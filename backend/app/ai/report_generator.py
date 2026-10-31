import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional

PRIMARY_SAFETY_NOTICE = (
    "AI-generated results are preliminary and may be inaccurate. This system does not provide a confirmed diagnosis. "
    "Consult a qualified dental professional for clinical evaluation."
)

CLINICAL_DISCLAIMER = (
    "IMPORTANT CLINICAL & EDUCATIONAL PROTOCOL: DentalAI is an AI-assisted educational screening prototype "
    "designed to aid registered dental practitioners in preliminary photographic review. "
    "This system DOES NOT formulate a confirmed diagnosis, surgical treatment plan, or pharmaceutical prescription. "
    "All model outputs, category scores, and Grad-CAM salience overlays must be evaluated and confirmed "
    "by a licensed dentist through chairside examination, periodontal probing, and diagnostic radiographs."
)

def generate_screening_report(
    patient_info: Dict[str, Any],
    multi_view_results: Dict[str, Any],
    report_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Constructs a structured screening report object incorporating verified ResNet-50 outputs,
    Grad-CAM salience visualizations, per-view breakdowns, and mandatory safety notices.
    """
    if not report_id:
        report_id = f"RPT-{uuid.uuid4().hex[:8].upper()}"

    now = datetime.now(timezone.utc)
    scan_date_iso = now.isoformat()
    scan_date_formatted = now.strftime("%B %d, %Y at %I:%M %p UTC")

    per_view = multi_view_results.get("per_view_findings", {})
    images_analyzed = []

    for view_key in ["front", "left", "right"]:
        if view_key in per_view:
            v_data = per_view[view_key]
            images_analyzed.append({
                "view": view_key,
                "label": f"{view_key.capitalize()} View",
                "predicted_class": v_data.get("predicted_name", v_data.get("predicted_class")),
                "model_output_score": v_data.get("model_output_score", 0.0),
                "confidence_percentage": v_data.get("confidence_percentage", 0.0),
                "is_abstaining": v_data.get("is_abstaining", False),
                "processing_status": v_data.get("processing_status", "success"),
                "inference_time_ms": v_data.get("inference_time_ms", 0.0),
                "top_three_predictions": v_data.get("top_three_predictions", []),
                "model_output_scores": v_data.get("model_output_scores", {}),
                "original_image": v_data.get("original_image"),
                "heatmap_image": v_data.get("heatmap_image"),
                "gradcam_salience_stats": v_data.get("gradcam_salience_stats", {}),
                "gradcam_explanation": v_data.get("gradcam_explanation")
            })

    # Educational clinical next steps (procedural evaluation, no prescriptions or treatment plans)
    examination_steps = [
        "Perform comprehensive visual-tactile inspection of tooth crowns and cervical margins using dental explorer and mirror.",
        "Record periodontal probing depths (6-point charting) and bleeding on probing (BOP) across all quadrants.",
        "Acquire diagnostic intraoral bitewing or periapical radiographs to examine interproximal contact zones and alveolar crest levels.",
        "Correlate patient-reported symptoms (thermal sensitivity, masticatory pain) with chairside clinical findings."
    ]

    return {
        "report_id": report_id,
        "scan_date": scan_date_formatted,
        "scan_date_iso": scan_date_iso,
        "total_inference_time_ms": multi_view_results.get("total_inference_time_ms", 0.0),
        "patient": {
            "name": patient_info.get("name", "Unknown Patient"),
            "patient_id": patient_info.get("patient_id", "N/A"),
            "age": patient_info.get("age"),
            "date_of_birth": patient_info.get("date_of_birth"),
            "gender": patient_info.get("gender", "Not Specified"),
            "contact_number": patient_info.get("contact_number"),
            "email": patient_info.get("email"),
            "medical_history": patient_info.get("medical_history"),
            "dental_history": patient_info.get("dental_history"),
            "notes": patient_info.get("notes", "")
        },
        "screening_summary": {
            "overall_status": multi_view_results.get("overall_status", "Evaluation Complete"),
            "triage_recommendation": multi_view_results.get("triage_recommendation", "Clinical Review Required"),
            "narrative": multi_view_results.get("narrative", ""),
            "abstained_views": multi_view_results.get("abstained_views", []),
            "has_abstained_views": multi_view_results.get("has_abstained_views", False),
            "multi_view_notice": multi_view_results.get("multi_view_notice", "")
        },
        "conditions_detected": multi_view_results.get("conditions_detected", []),
        "images_analyzed": images_analyzed,
        "recommended_examination_steps": examination_steps,
        "primary_safety_notice": PRIMARY_SAFETY_NOTICE,
        "disclaimer": CLINICAL_DISCLAIMER
    }
