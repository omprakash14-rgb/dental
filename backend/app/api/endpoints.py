import os
import uuid
import logging
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status, Response, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import func, or_, desc, cast, Date

from app.db.database import get_db, engine
from app.db.models import Patient, DentalAnalysis, UploadedImage, DiseasePrediction, GeneratedReport, User
from app.core.auth import get_current_user, get_optional_current_user, require_roles, log_audit
from app.ai.model_loader import (
    get_dental_model,
    get_class_indices,
    get_model_status,
    load_dental_model,
    DEFAULT_ABSTENTION_THRESHOLD
)
from app.ai.image_preprocessing import validate_image_file, preprocess_dental_image
from app.ai.inference import run_inference, GRADCAM_DISCLOSURE
from app.ai.prediction_processor import process_three_views
from app.ai.report_generator import generate_screening_report, PRIMARY_SAFETY_NOTICE
from app.ai.pdf_generator import generate_screening_pdf
from .schemas import (
    PatientResponse,
    PatientCreate,
    PatientUpdate,
    ReportDetailResponse,
    HealthStatus,
    ModelStatusResponse,
    SingleImageAnalysisResponse,
    DashboardStats,
    AnalysisSummaryResponse
)

logger = logging.getLogger("dentalai.api")

router = APIRouter()

UPLOADS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "uploads")
os.makedirs(UPLOADS_DIR, exist_ok=True)

# -------------------------------------------------------------
# 1. Model Status & Health Endpoints
# -------------------------------------------------------------

@router.get("/dental/model-status", response_model=ModelStatusResponse, summary="Inspect ResNet-50 Pretrained Model Status")
def get_dental_model_status():
    """
    Returns verified architectural inspection metadata for the pretrained ResNet-50 model,
    including layer layout, input/output tensor shapes, parameter counts, weights file verification,
    and class-to-index mapping.
    """
    status_info = get_model_status()
    meta = status_info.get("metadata", {})
    class_indices = get_class_indices()

    return {
        "is_loaded": status_info["is_loaded"],
        "file_exists": status_info["file_exists"],
        "model_path": status_info["model_path"],
        "architecture": meta.get("architecture", "ResNet-50 Transfer Learning Classifier"),
        "input_shape": meta.get("input_shape", [None, 224, 224, 3]),
        "output_shape": meta.get("output_shape", [None, 6]),
        "num_classes": len(class_indices),
        "classes": list(class_indices.values()),
        "class_mapping": class_indices,
        "gradcam_layer": meta.get("gradcam_layer", "conv5_block3_out"),
        "abstention_threshold": meta.get("abstention_threshold", DEFAULT_ABSTENTION_THRESHOLD),
        "model_size_mb": meta.get("model_size_mb", 98.2),
        "primary_safety_notice": PRIMARY_SAFETY_NOTICE,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

@router.get("/health", response_model=HealthStatus, summary="System Health & AI Readiness")
def check_health(db: Session = Depends(get_db)):
    """Health check validating AI model memory residency, DB connection, and supported classes."""
    model_loaded = False
    supported_classes = []
    try:
        model = get_dental_model()
        model_loaded = model is not None
        class_indices = get_class_indices()
        supported_classes = list(class_indices.values())
    except Exception as e:
        logger.error("Health check AI model query failed: %s", e)

    db_status = "connected"
    try:
        db.execute(func.now())
    except Exception as e:
        logger.error("Health check DB query failed: %s", e)
        db_status = f"unhealthy: {str(e)}"

    db_type = "PostgreSQL" if "postgresql" in str(engine.url) else "SQLite"

    return {
        "status": "operational" if model_loaded and db_status == "connected" else "degraded",
        "ai_model_loaded": model_loaded,
        "database_status": db_status,
        "database_type": db_type,
        "supported_classes": supported_classes,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

# -------------------------------------------------------------
# 2. Single-View Image Inference
# -------------------------------------------------------------

@router.post("/dental/analyze", response_model=SingleImageAnalysisResponse, summary="Analyze Single Intraoral Dental Photograph")
async def analyze_single_dental_image(
    image: UploadFile = File(..., description="Single intraoral photograph (JPG, JPEG, PNG, WebP)"),
    view_name: Optional[str] = Form("front", description="Arch view: 'front', 'left', or 'right'"),
    abstention_threshold: Optional[float] = Form(DEFAULT_ABSTENTION_THRESHOLD)
):
    """
    Performs verified ResNet-50 inference on a single intraoral dental photograph:
    - Validates file format, resolution (>= 150x150), and image clarity.
    - Applies standard Caffe ResNet50 preprocessing (RGB->BGR + mean centering [103.939, 116.779, 123.68]).
    - Runs model feed-forward and measures exact inference latency.
    - Computes authentic Grad-CAM heatmap on conv5_block3_out without artificial bounding boxes.
    - Returns predicted class, raw softmax score distribution, top-three rankings, and side-by-side visualization files.
    """
    if not image.filename:
        raise HTTPException(status_code=400, detail="No image file provided.")

    try:
        content = await image.read()
        val_meta = validate_image_file(content, image.filename)
    except ValueError as val_err:
        raise HTTPException(status_code=422, detail=str(val_err))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read image file: {str(e)}")

    tensor, orig_pil, _ = preprocess_dental_image(content)

    clean_view = (view_name or "front").lower()
    inf_res = run_inference(
        tensor=tensor,
        orig_img=orig_pil,
        view_name=clean_view,
        output_dir=UPLOADS_DIR,
        abstention_threshold=abstention_threshold or DEFAULT_ABSTENTION_THRESHOLD
    )

    return {
        **inf_res,
        "primary_safety_notice": PRIMARY_SAFETY_NOTICE
    }

# -------------------------------------------------------------
# 3. Three-View Multi-Angle Analysis
# -------------------------------------------------------------

async def _process_multi_view_submission(
    patient_name: str,
    patient_id: str,
    age: Optional[int],
    gender: Optional[str],
    notes: Optional[str],
    front_image: UploadFile,
    left_image: UploadFile,
    right_image: UploadFile,
    db: Session
) -> Dict[str, Any]:
    upload_map = {
        "front": front_image,
        "left": left_image,
        "right": right_image
    }

    # 1. Read and validate all 3 images
    validated_files = {}
    for view_key, file_obj in upload_map.items():
        if not file_obj or not file_obj.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Missing file for {view_key.capitalize()} View. All three views (Front, Left, Right) are required."
            )
        try:
            content = await file_obj.read()
            val_meta = validate_image_file(content, file_obj.filename)
            validated_files[view_key] = {
                "bytes": content,
                "meta": val_meta,
                "orig_filename": file_obj.filename
            }
        except ValueError as val_err:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Validation error on {view_key} view image: {str(val_err)}"
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to read image for {view_key} view: {str(e)}"
            )

    # 2. Run inference on each view
    view_results = {}
    stored_images_meta = {}

    for view_key, file_info in validated_files.items():
        tensor, orig_pil, q_info = preprocess_dental_image(file_info["bytes"])

        # Save raw uploaded photograph
        raw_uuid = uuid.uuid4().hex[:10]
        ext = os.path.splitext(file_info["orig_filename"])[1].lower() or ".jpg"
        stored_raw_name = f"{view_key}_{raw_uuid}{ext}"
        stored_raw_path = os.path.join(UPLOADS_DIR, stored_raw_name)
        with open(stored_raw_path, "wb") as f_out:
            f_out.write(file_info["bytes"])

        # Run model inference + Grad-CAM generation
        inf_result = run_inference(
            tensor=tensor,
            orig_img=orig_pil,
            view_name=view_key,
            output_dir=UPLOADS_DIR
        )

        view_results[view_key] = inf_result
        stored_images_meta[view_key] = {
            "original_filename": file_info["orig_filename"],
            "stored_filename": stored_raw_name,
            "annotated_filename": inf_result.get("original_image"),
            "heatmap_filename": inf_result.get("heatmap_image"),
            "width": file_info["meta"]["width"],
            "height": file_info["meta"]["height"],
            "clarity_score": file_info["meta"]["clarity_score"],
            "is_inconclusive": inf_result.get("is_abstaining", False),
            "bounding_boxes": []  # Not generating fake boxes
        }

    # 3. Aggregate findings across 3 photographic views
    consolidated = process_three_views(view_results)

    # 4. Find or create patient record
    try:
        existing_patient = db.query(Patient).filter(Patient.patient_id == patient_id.strip()).first()
        if not existing_patient:
            patient = Patient(
                patient_id=patient_id.strip(),
                name=patient_name.strip(),
                age=age,
                gender=gender,
                notes=notes
            )
            db.add(patient)
            db.flush()
        else:
            patient = existing_patient
            patient.name = patient_name.strip()
            if age is not None:
                patient.age = age
            if gender:
                patient.gender = gender
            if notes:
                patient.notes = notes

        patient_info = {
            "name": patient.name,
            "patient_id": patient.patient_id,
            "age": patient.age,
            "date_of_birth": patient.date_of_birth,
            "gender": patient.gender or "Not Specified",
            "contact_number": patient.contact_number,
            "email": patient.email,
            "medical_history": patient.medical_history,
            "dental_history": patient.dental_history,
            "notes": patient.notes or ""
        }
        report_dict = generate_screening_report(patient_info, consolidated)

        # 5. Create DentalAnalysis record
        analysis = DentalAnalysis(
            patient_id=patient.id,
            overall_status=consolidated["overall_status"],
            urgency_level=consolidated["triage_recommendation"],
            summary=consolidated["narrative"],
            inconclusive_views=consolidated["abstained_views"]
        )
        db.add(analysis)
        db.flush()

        # Add UploadedImage records
        for v_name, img_m in stored_images_meta.items():
            db_img = UploadedImage(
                analysis_id=analysis.id,
                view_name=v_name,
                original_filename=img_m["original_filename"],
                stored_filename=img_m["stored_filename"],
                annotated_filename=img_m["annotated_filename"],
                heatmap_filename=img_m["heatmap_filename"],
                width=img_m["width"],
                height=img_m["height"],
                clarity_score=img_m["clarity_score"],
                is_inconclusive=img_m["is_inconclusive"],
                bounding_boxes=img_m["bounding_boxes"]
            )
            db.add(db_img)

        # Add DiseasePrediction records
        for cond in consolidated["conditions_detected"]:
            pred = DiseasePrediction(
                analysis_id=analysis.id,
                disease_key=cond["disease_key"],
                disease_name=cond["disease_name"],
                category=cond.get("category"),
                severity="Moderate",
                peak_confidence=cond["peak_score"],
                calibrated_confidence=cond["peak_score"],
                affected_views=cond["affected_views"],
                clinical_signs=cond.get("clinical_signs", []),
                recommendations=[cond.get("clinical_relevance", "")]
            )
            db.add(pred)

        # Add GeneratedReport record
        gen_report = GeneratedReport(
            report_id=report_dict["report_id"],
            analysis_id=analysis.id,
            patient_id=patient.id,
            report_data=report_dict
        )
        db.add(gen_report)

        db.commit()
        log_audit(db, action="SCREENING_EXECUTE", resource_type="screening", resource_id=report_dict["report_id"], status_code=200)
        logger.info("Successfully analyzed and persisted Report %s for Patient %s", report_dict["report_id"], patient_id)

    except Exception as db_err:
        db.rollback()
        logger.error("Failed to commit analysis to database: %s", db_err, exc_info=True)

    return report_dict

@router.post("/dental/analyze-multiple", response_model=ReportDetailResponse, summary="Analyze Three Views (Front, Left, Right)")
async def analyze_multiple_endpoint(
    patient_name: str = Form(..., min_length=1, max_length=255),
    patient_id: str = Form(..., min_length=1, max_length=64),
    age: Optional[int] = Form(None),
    gender: Optional[str] = Form("Not Specified"),
    notes: Optional[str] = Form(""),
    front_image: UploadFile = File(..., description="Anterior Front View"),
    left_image: UploadFile = File(..., description="Left Lateral / Buccal View"),
    right_image: UploadFile = File(..., description="Right Lateral / Buccal View"),
    db: Session = Depends(get_db)
):
    return await _process_multi_view_submission(
        patient_name=patient_name,
        patient_id=patient_id,
        age=age,
        gender=gender,
        notes=notes,
        front_image=front_image,
        left_image=left_image,
        right_image=right_image,
        db=db
    )

@router.post("/analyze", response_model=ReportDetailResponse, summary="Analyze Three Views (Backwards Compatibility Alias)")
async def analyze_alias_endpoint(
    patient_name: str = Form(..., min_length=1, max_length=255),
    patient_id: str = Form(..., min_length=1, max_length=64),
    age: Optional[int] = Form(None),
    gender: Optional[str] = Form("Not Specified"),
    notes: Optional[str] = Form(""),
    front_image: UploadFile = File(...),
    left_image: UploadFile = File(...),
    right_image: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    return await _process_multi_view_submission(
        patient_name=patient_name,
        patient_id=patient_id,
        age=age,
        gender=gender,
        notes=notes,
        front_image=front_image,
        left_image=left_image,
        right_image=right_image,
        db=db
    )

# -------------------------------------------------------------
# 4. Reports, Patients, and Dashboard Records
# -------------------------------------------------------------

def _fetch_report(report_id: str, db: Session):
    report_record = db.query(GeneratedReport).filter(GeneratedReport.report_id == report_id).first()
    if not report_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report with ID '{report_id}' was not found."
        )
    return report_record.report_data

@router.get("/dental/reports/{report_id}", response_model=ReportDetailResponse, summary="Retrieve Screening Report by ID")
def get_dental_report(report_id: str, db: Session = Depends(get_db)):
    return _fetch_report(report_id, db)

@router.get("/reports/{report_id}", response_model=ReportDetailResponse, summary="Retrieve Report (Alias)")
def get_report_alias(report_id: str, db: Session = Depends(get_db)):
    return _fetch_report(report_id, db)

# -------------------------------------------------------------
# 4. Patient Management Endpoints (CRUD + Search)
# -------------------------------------------------------------

def _serialize_patient(p: Patient, analyses_count: int) -> PatientResponse:
    return PatientResponse(
        id=p.id,
        patient_id=p.patient_id,
        name=p.name,
        age=p.age,
        date_of_birth=p.date_of_birth,
        gender=p.gender,
        contact_number=p.contact_number,
        email=p.email,
        medical_history=p.medical_history,
        dental_history=p.dental_history,
        notes=p.notes,
        created_at=p.created_at,
        updated_at=p.updated_at,
        analyses_count=analyses_count
    )

def _query_patients(search: Optional[str], skip: int, limit: int, db: Session) -> List[PatientResponse]:
    query = db.query(Patient)
    if search and search.strip():
        term = f"%{search.strip()}%"
        query = query.filter(
            or_(
                Patient.name.ilike(term),
                Patient.patient_id.ilike(term),
                Patient.email.ilike(term),
                Patient.contact_number.ilike(term)
            )
        )
    patients = query.order_by(Patient.updated_at.desc()).offset(skip).limit(limit).all()
    results = []
    for p in patients:
        count = db.query(func.count(DentalAnalysis.id)).filter(DentalAnalysis.patient_id == p.id).scalar() or 0
        results.append(_serialize_patient(p, count))
    return results

@router.get("/dental/patients", response_model=List[PatientResponse], summary="List & Search Patients")
def list_dental_patients(
    search: Optional[str] = Query(None, description="Search by name, ID, email, or contact"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db)
):
    return _query_patients(search, skip, limit, db)

@router.get("/patients", response_model=List[PatientResponse], summary="List & Search Patients (Alias)")
def list_patients_alias(
    search: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db)
):
    return _query_patients(search, skip, limit, db)

def _create_patient(patient_in: PatientCreate, db: Session) -> PatientResponse:
    clean_pid = patient_in.patient_id.strip()
    clean_name = patient_in.name.strip()
    if not clean_pid or not clean_name:
        raise HTTPException(status_code=400, detail="Patient Name and Unique Patient ID are required.")
    
    existing = db.query(Patient).filter(Patient.patient_id == clean_pid).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Patient with ID '{clean_pid}' is already registered."
        )
    
    new_patient = Patient(
        patient_id=clean_pid,
        name=clean_name,
        age=patient_in.age,
        date_of_birth=patient_in.date_of_birth.strip() if patient_in.date_of_birth else None,
        gender=patient_in.gender or "Not Specified",
        contact_number=patient_in.contact_number.strip() if patient_in.contact_number else None,
        email=patient_in.email.strip() if patient_in.email else None,
        medical_history=patient_in.medical_history.strip() if patient_in.medical_history else None,
        dental_history=patient_in.dental_history.strip() if patient_in.dental_history else None,
        notes=patient_in.notes.strip() if patient_in.notes else None
    )
    db.add(new_patient)
    db.commit()
    db.refresh(new_patient)
    logger.info("Successfully registered new Patient %s (%s)", clean_pid, clean_name)
    return _serialize_patient(new_patient, 0)

@router.post("/dental/patients", response_model=PatientResponse, status_code=status.HTTP_201_CREATED, summary="Register New Patient")
def create_dental_patient(patient_in: PatientCreate, db: Session = Depends(get_db)):
    return _create_patient(patient_in, db)

@router.post("/patients", response_model=PatientResponse, status_code=status.HTTP_201_CREATED, summary="Register Patient (Alias)")
def create_patient_alias(patient_in: PatientCreate, db: Session = Depends(get_db)):
    return _create_patient(patient_in, db)

def _find_patient_by_identifier(identifier: str, db: Session) -> Patient:
    patient = db.query(Patient).filter(Patient.patient_id == identifier).first()
    if not patient and identifier.isdigit():
        patient = db.query(Patient).filter(Patient.id == int(identifier)).first()
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Patient with identifier '{identifier}' was not found."
        )
    return patient

def _get_patient_details_and_scans(identifier: str, db: Session):
    patient = _find_patient_by_identifier(identifier, db)
    analyses = (
        db.query(DentalAnalysis)
        .filter(DentalAnalysis.patient_id == patient.id)
        .order_by(DentalAnalysis.created_at.desc())
        .all()
    )
    history = []
    for a in analyses:
        report_record = db.query(GeneratedReport).filter(GeneratedReport.analysis_id == a.id).first()
        preds = db.query(DiseasePrediction).filter(DiseasePrediction.analysis_id == a.id).all()
        history.append({
            "analysis_id": a.analysis_id,
            "report_id": report_record.report_id if report_record else None,
            "overall_status": a.overall_status,
            "urgency_level": a.urgency_level,
            "summary": a.summary,
            "created_at": a.created_at,
            "inconclusive_views": a.inconclusive_views or [],
            "findings": [
                {
                    "disease_name": p.disease_name,
                    "severity": p.severity,
                    "confidence_percentage": round(p.peak_confidence * 100, 1),
                    "affected_views": p.affected_views
                }
                for p in preds
            ]
        })
    return {
        "patient": _serialize_patient(patient, len(history)),
        "scans_count": len(history),
        "history": history
    }

@router.get("/dental/patients/{patient_id}", summary="Get Patient Details & History")
def get_dental_patient_history(patient_id: str, db: Session = Depends(get_db)):
    return _get_patient_details_and_scans(patient_id, db)

@router.get("/patients/{patient_id}", summary="Get Patient Details & History (Alias)")
def get_patient_history_alias(patient_id: str, db: Session = Depends(get_db)):
    return _get_patient_details_and_scans(patient_id, db)

def _update_patient(identifier: str, patient_up: PatientUpdate, db: Session) -> PatientResponse:
    patient = _find_patient_by_identifier(identifier, db)
    if patient_up.name is not None:
        patient.name = patient_up.name.strip()
    if patient_up.age is not None:
        patient.age = patient_up.age
    if patient_up.date_of_birth is not None:
        patient.date_of_birth = patient_up.date_of_birth.strip() if patient_up.date_of_birth else None
    if patient_up.gender is not None:
        patient.gender = patient_up.gender
    if patient_up.contact_number is not None:
        patient.contact_number = patient_up.contact_number.strip() if patient_up.contact_number else None
    if patient_up.email is not None:
        patient.email = patient_up.email.strip() if patient_up.email else None
    if patient_up.medical_history is not None:
        patient.medical_history = patient_up.medical_history.strip() if patient_up.medical_history else None
    if patient_up.dental_history is not None:
        patient.dental_history = patient_up.dental_history.strip() if patient_up.dental_history else None
    if patient_up.notes is not None:
        patient.notes = patient_up.notes.strip() if patient_up.notes else None

    db.commit()
    db.refresh(patient)
    count = db.query(func.count(DentalAnalysis.id)).filter(DentalAnalysis.patient_id == patient.id).scalar() or 0
    logger.info("Updated patient record %s", patient.patient_id)
    return _serialize_patient(patient, count)

@router.put("/dental/patients/{patient_id}", response_model=PatientResponse, summary="Update Patient Information")
def update_dental_patient(patient_id: str, patient_up: PatientUpdate, db: Session = Depends(get_db)):
    return _update_patient(patient_id, patient_up, db)

@router.put("/patients/{patient_id}", response_model=PatientResponse, summary="Update Patient Information (Alias)")
def update_patient_alias(patient_id: str, patient_up: PatientUpdate, db: Session = Depends(get_db)):
    return _update_patient(patient_id, patient_up, db)

def _delete_patient(identifier: str, current_user: Optional[User], db: Session):
    if current_user and current_user.role == "staff":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Staff role lacks authorization to delete clinical records. Administrator or Clinician role required."
        )
    patient = _find_patient_by_identifier(identifier, db)
    pid = patient.patient_id
    pname = patient.name
    db.delete(patient)
    db.commit()
    log_audit(db, action="PATIENT_DELETE", user=current_user, resource_type="patient", resource_id=pid, status_code=200)
    logger.info("Deleted patient %s (%s) and safely cascaded associated analyses and reports.", pid, pname)
    return {
        "status": "success",
        "message": f"Patient '{pname}' ({pid}) and all associated screening records have been safely deleted.",
        "patient_id": pid
    }

@router.delete("/dental/patients/{patient_id}", summary="Delete Patient Record")
def delete_dental_patient(
    patient_id: str,
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: Session = Depends(get_db)
):
    return _delete_patient(patient_id, current_user, db)

@router.delete("/patients/{patient_id}", summary="Delete Patient Record (Alias)")
def delete_patient_alias(
    patient_id: str,
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: Session = Depends(get_db)
):
    return _delete_patient(patient_id, current_user, db)

# -------------------------------------------------------------
# 5. Screening Sessions & History Endpoints
# -------------------------------------------------------------

@router.post("/dental/screenings", response_model=ReportDetailResponse, summary="Initiate New 3-View Screening Session")
async def create_dental_screening(
    patient_name: str = Form(..., min_length=1, max_length=255),
    patient_id: str = Form(..., min_length=1, max_length=64),
    age: Optional[int] = Form(None),
    gender: Optional[str] = Form("Not Specified"),
    notes: Optional[str] = Form(""),
    front_image: UploadFile = File(...),
    left_image: UploadFile = File(...),
    right_image: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    return await _process_multi_view_submission(
        patient_name=patient_name,
        patient_id=patient_id,
        age=age,
        gender=gender,
        notes=notes,
        front_image=front_image,
        left_image=left_image,
        right_image=right_image,
        db=db
    )

@router.get("/dental/screenings", summary="List All Screening Sessions")
def list_dental_screenings(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    analyses = db.query(DentalAnalysis).order_by(DentalAnalysis.created_at.desc()).offset(skip).limit(limit).all()
    results = []
    for a in analyses:
        p = a.patient
        rep = a.report
        results.append({
            "analysis_id": a.analysis_id,
            "report_id": rep.report_id if rep else None,
            "patient_id": p.patient_id if p else "N/A",
            "patient_name": p.name if p else "Unknown",
            "overall_status": a.overall_status,
            "urgency_level": a.urgency_level,
            "inconclusive_views": a.inconclusive_views or [],
            "created_at": a.created_at
        })
    return results

@router.get("/dental/screenings/{screening_id}", response_model=ReportDetailResponse, summary="Retrieve Screening Session by ID")
def get_dental_screening_by_id(screening_id: str, db: Session = Depends(get_db)):
    report_record = db.query(GeneratedReport).filter(
        or_(
            GeneratedReport.report_id == screening_id,
            GeneratedReport.analysis_id == db.query(DentalAnalysis.id).filter(DentalAnalysis.analysis_id == screening_id).scalar_subquery()
        )
    ).first()
    if not report_record:
        raise HTTPException(status_code=404, detail=f"Screening '{screening_id}' not found.")
    return report_record.report_data

@router.get("/patients/{patient_id}/screenings", summary="List Screenings for Specific Patient")
def get_patient_screenings(patient_id: str, db: Session = Depends(get_db)):
    patient = _find_patient_by_identifier(patient_id, db)
    analyses = db.query(DentalAnalysis).filter(DentalAnalysis.patient_id == patient.id).order_by(DentalAnalysis.created_at.desc()).all()
    results = []
    for a in analyses:
        rep = a.report
        results.append({
            "analysis_id": a.analysis_id,
            "report_id": rep.report_id if rep else None,
            "overall_status": a.overall_status,
            "urgency_level": a.urgency_level,
            "inconclusive_views": a.inconclusive_views or [],
            "created_at": a.created_at
        })
    return results

# -------------------------------------------------------------
# 6. PDF Generation & Download Endpoints
# -------------------------------------------------------------

def _generate_report_pdf_response(report_id: str, current_user: Optional[User], db: Session) -> Response:
    report_data = _fetch_report(report_id, db)
    try:
        pdf_bytes = generate_screening_pdf(report_data, UPLOADS_DIR)
        log_audit(db, action="PDF_DOWNLOAD", user=current_user, resource_type="report", resource_id=report_id, status_code=200)
    except Exception as e:
        logger.error("PDF generation failed for report %s: %s", report_id, e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate PDF for report '{report_id}': {str(e)}"
        )
    filename = f"DentalAI_Report_{report_id}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "X-Report-ID": report_id
        }
    )

@router.get("/dental/reports/{report_id}/pdf", summary="Download Screening Report PDF")
def download_dental_report_pdf(
    report_id: str,
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: Session = Depends(get_db)
):
    return _generate_report_pdf_response(report_id, current_user, db)

@router.get("/reports/{report_id}/pdf", summary="Download Screening Report PDF (Alias)")
def download_report_pdf_alias(
    report_id: str,
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: Session = Depends(get_db)
):
    return _generate_report_pdf_response(report_id, current_user, db)

@router.get("/dental/images/{filename}", summary="Secure Intraoral Image Access")
def get_secure_dental_image(
    filename: str,
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    clean_filename = os.path.basename(filename)
    safe_path = os.path.abspath(os.path.join(UPLOADS_DIR, clean_filename))
    if not safe_path.startswith(os.path.abspath(UPLOADS_DIR)):
        raise HTTPException(status_code=403, detail="Invalid file path.")
    if not os.path.exists(safe_path):
        raise HTTPException(status_code=404, detail="Requested image not found.")
    return FileResponse(safe_path)

# -------------------------------------------------------------
# 7. Dashboard Metrics & Analytics
# -------------------------------------------------------------

def _fetch_dashboard_stats(db: Session):
    total_patients = db.query(func.count(Patient.id)).scalar() or 0
    total_scans = db.query(func.count(DentalAnalysis.id)).scalar() or 0

    # Inconclusive scans: where inconclusive_views != '[]'
    try:
        if "postgresql" in str(engine.url):
            inconclusive_count = (
                db.query(func.count(DentalAnalysis.id))
                .filter(DentalAnalysis.inconclusive_views.isnot(None))
                .filter(func.json_array_length(DentalAnalysis.inconclusive_views) > 0)
                .scalar()
            ) or 0
        else:
            inconclusive_count = 0
    except Exception:
        inconclusive_count = 0

    completed_count = max(0, total_scans - inconclusive_count)

    disease_counts = (
        db.query(DiseasePrediction.disease_name, func.count(DiseasePrediction.id))
        .group_by(DiseasePrediction.disease_name)
        .all()
    )
    disease_dist = {name: count for name, count in disease_counts}

    for c in ["Dental Calculus (Tartar)", "Dental Caries (Tooth Decay)", "Gingivitis", "Hypodontia / Missing Tooth", "Oral Mucosal Ulceration", "Tooth Discoloration"]:
        if c not in disease_dist:
            disease_dist[c] = 0

    urgency_counts = (
        db.query(DentalAnalysis.urgency_level, func.count(DentalAnalysis.id))
        .group_by(DentalAnalysis.urgency_level)
        .all()
    )
    urgency_dist = {u: count for u, count in urgency_counts}

    # Chronological scans over time (grouped by date)
    date_col = cast(DentalAnalysis.created_at, Date)
    timeline_rows = (
        db.query(date_col.label("scan_date"), func.count(DentalAnalysis.id).label("count"))
        .group_by(date_col)
        .order_by(date_col.asc())
        .limit(30)
        .all()
    )
    scans_over_time = [
        {"date": row.scan_date.strftime("%b %d, %Y") if hasattr(row.scan_date, "strftime") else str(row.scan_date), "scans": row.count}
        for row in timeline_rows
    ]

    recent = (
        db.query(DentalAnalysis)
        .order_by(DentalAnalysis.created_at.desc())
        .limit(8)
        .all()
    )

    recent_list = []
    for a in recent:
        p = a.patient
        rep = a.report
        pred_count = db.query(func.count(DiseasePrediction.id)).filter(DiseasePrediction.analysis_id == a.id).scalar() or 0
        recent_list.append(
            AnalysisSummaryResponse(
                analysis_id=a.analysis_id,
                report_id=rep.report_id if rep else "N/A",
                patient_id=p.patient_id if p else "Unknown",
                patient_name=p.name if p else "Anonymous",
                overall_status=a.overall_status,
                urgency_level=a.urgency_level,
                created_at=a.created_at,
                findings_count=pred_count
            )
        )

    return {
        "total_patients": total_patients,
        "total_scans": total_scans,
        "completed_scans": completed_count,
        "inconclusive_scans": inconclusive_count,
        "disease_distribution": disease_dist,
        "urgency_distribution": urgency_dist,
        "scans_over_time": scans_over_time,
        "recent_analyses": recent_list
    }

@router.get("/dental/stats", response_model=DashboardStats, summary="Clinical Dashboard Metrics")
def get_dental_stats(db: Session = Depends(get_db)):
    return _fetch_dashboard_stats(db)

@router.get("/stats", response_model=DashboardStats, summary="Dashboard Stats (Alias)")
def get_stats_alias(db: Session = Depends(get_db)):
    return _fetch_dashboard_stats(db)
