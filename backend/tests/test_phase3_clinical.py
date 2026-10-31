import os
import sys
import time
import io
import json
import uuid

# Add backend directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from app.main import app
from app.db.database import SessionLocal, engine
from app.db.models import Patient, DentalAnalysis, UploadedImage, DiseasePrediction, GeneratedReport
from app.ai.pdf_generator import generate_screening_pdf, PRIMARY_SAFETY_NOTICE, MULTI_VIEW_NOTICE

client = TestClient(app)

def run_phase3_clinical_tests():
    print("=" * 70)
    print("DENTALAI — PHASE 3: PATIENT MANAGEMENT, REPORTS & PDF TEST SUITE")
    print("=" * 70)

    samples_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "samples")
    front_sample = os.path.join(samples_dir, "sample_caries_front.jpg")
    left_sample = os.path.join(samples_dir, "sample_gingivitis_left.jpg")
    right_sample = os.path.join(samples_dir, "sample_calculus_right.jpg")
    uploads_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "uploads")

    test_uid = uuid.uuid4().hex[:6].upper()
    test_pid = f"PT-TEST-{test_uid}"
    test_name = f"Elena Rostova {test_uid}"

    # -------------------------------------------------------------
    # Test 1: Patient Registration
    # -------------------------------------------------------------
    print("\n[TEST 1/12] Registering New Patient with Complete Clinical Profile...")
    reg_payload = {
        "patient_id": test_pid,
        "name": test_name,
        "age": 29,
        "date_of_birth": "1997-04-12",
        "gender": "Female",
        "contact_number": "+1-555-8821",
        "email": f"elena.{test_uid.lower()}@example.org",
        "medical_history": "Penicillin hypersensitivity. No cardiovascular abnormalities.",
        "dental_history": "Composite restoration on tooth #19 (2023). Mild marginal gingival erythema.",
        "notes": "Patient reports hypersensitivity on left lower quadrant during mastication."
    }
    res = client.post("/api/patients", json=reg_payload)
    assert res.status_code == 201, f"Expected 201, got {res.status_code}: {res.text}"
    p_data = res.json()
    assert p_data["patient_id"] == test_pid
    assert p_data["name"] == test_name
    assert p_data["contact_number"] == "+1-555-8821"
    assert p_data["analyses_count"] == 0
    print(f"  ✓ Patient successfully registered: {test_name} ({test_pid})")

    # -------------------------------------------------------------
    # Test 2: Patient Update
    # -------------------------------------------------------------
    print("\n[TEST 2/12] Updating Patient Anamnesis and Information...")
    update_payload = {
        "notes": "Patient reports hypersensitivity on left lower quadrant. Scheduled for follow-up scaling.",
        "medical_history": "Penicillin hypersensitivity. Verified up-to-date tetanus vaccination."
    }
    up_res = client.put(f"/api/patients/{test_pid}", json=update_payload)
    assert up_res.status_code == 200, f"Expected 200, got {up_res.status_code}: {up_res.text}"
    up_data = up_res.json()
    assert "tetanus" in up_data["medical_history"]
    assert "follow-up scaling" in up_data["notes"]
    print(f"  ✓ Patient profile updated successfully.")

    # -------------------------------------------------------------
    # Test 3: Patient Search
    # -------------------------------------------------------------
    print("\n[TEST 3/12] Searching Patients by Name and ID...")
    search_res = client.get(f"/api/patients?search={test_uid}")
    assert search_res.status_code == 200
    search_list = search_res.json()
    assert len(search_list) >= 1
    found = any(p["patient_id"] == test_pid for p in search_list)
    assert found, "Created patient should be found in search results"
    print(f"  ✓ Patient search verified: found {len(search_list)} record(s) matching '{test_uid}'")

    # -------------------------------------------------------------
    # Test 4: Patient Record Retrieval
    # -------------------------------------------------------------
    print("\n[TEST 4/12] Retrieving Complete Patient Record & Scan History...")
    get_res = client.get(f"/api/patients/{test_pid}")
    assert get_res.status_code == 200, f"Expected 200, got {get_res.status_code}"
    rec_data = get_res.json()
    assert rec_data["patient"]["patient_id"] == test_pid
    assert rec_data["patient"]["name"] == test_name
    assert rec_data["scans_count"] == 0
    assert rec_data["history"] == []
    print(f"  ✓ Retrieved patient details and baseline 0 scans.")

    # -------------------------------------------------------------
    # Test 5: Three-View Screening Workflow
    # -------------------------------------------------------------
    print("\n[TEST 5/12] Executing 3-View Photographic Screening Workflow...")
    t0 = time.perf_counter()
    with open(front_sample, "rb") as f_front, \
         open(left_sample, "rb") as f_left, \
         open(right_sample, "rb") as f_right:
        screen_res = client.post(
            "/api/dental/screenings",
            data={
                "patient_name": test_name,
                "patient_id": test_pid,
                "age": 29,
                "gender": "Female",
                "notes": "Preliminary pre-screening scan"
            },
            files={
                "front_image": ("front.jpg", f_front, "image/jpeg"),
                "left_image": ("left.jpg", f_left, "image/jpeg"),
                "right_image": ("right.jpg", f_right, "image/jpeg"),
            }
        )
    screen_time = round((time.perf_counter() - t0) * 1000, 2)
    assert screen_res.status_code == 200, f"Expected 200, got {screen_res.status_code}: {screen_res.text}"
    report_data = screen_res.json()
    report_id = report_data["report_id"]
    assert report_id.startswith("RPT-")
    assert len(report_data["images_analyzed"]) == 3
    assert report_data["patient"]["patient_id"] == test_pid
    assert report_data["primary_safety_notice"] == PRIMARY_SAFETY_NOTICE
    print(f"  ✓ Screening completed in {screen_time}ms. Report ID: {report_id}")
    print(f"  ✓ Overall finding: {report_data['screening_summary']['overall_status']}")
    print(f"  ✓ Triage priority: {report_data['screening_summary']['triage_recommendation']}")

    # -------------------------------------------------------------
    # Test 6: Database Persistence Verification
    # -------------------------------------------------------------
    print("\n[TEST 6/12] Verifying PostgreSQL Relational Persistence...")
    db = SessionLocal()
    try:
        db_patient = db.query(Patient).filter(Patient.patient_id == test_pid).first()
        assert db_patient is not None, "Patient must exist in DB"
        analyses = db.query(DentalAnalysis).filter(DentalAnalysis.patient_id == db_patient.id).all()
        assert len(analyses) == 1, "Must have exactly 1 analysis recorded"
        db_analysis = analyses[0]
        images = db.query(UploadedImage).filter(UploadedImage.analysis_id == db_analysis.id).all()
        assert len(images) == 3, f"Must have 3 images recorded, found {len(images)}"
        db_report = db.query(GeneratedReport).filter(GeneratedReport.analysis_id == db_analysis.id).first()
        assert db_report is not None, "GeneratedReport must exist in DB"
        assert db_report.report_id == report_id
        print(f"  ✓ Verified PostgreSQL records:")
        print(f"     • Patient: {db_patient.name} (ID: {db_patient.id})")
        print(f"     • DentalAnalysis: {db_analysis.analysis_id}")
        print(f"     • UploadedImage rows: {[img.view_name for img in images]}")
        print(f"     • GeneratedReport: {db_report.report_id}")
    finally:
        db.close()

    # -------------------------------------------------------------
    # Test 7: Historical Screening Retrieval
    # -------------------------------------------------------------
    print("\n[TEST 7/12] Retrieving Historical Screenings Without AI Inference...")
    t_hist = time.perf_counter()
    hist_res = client.get(f"/api/patients/{test_pid}/screenings")
    hist_latency = round((time.perf_counter() - t_hist) * 1000, 2)
    assert hist_res.status_code == 200
    hist_data = hist_res.json()
    assert len(hist_data) == 1
    assert hist_data[0]["report_id"] == report_id
    assert hist_latency < 50.0, f"DB lookup must be instantaneous (<50ms), took {hist_latency}ms"
    print(f"  ✓ Historical record retrieved from PostgreSQL in {hist_latency}ms (no AI re-run).")

    # -------------------------------------------------------------
    # Test 8: PDF Report Generation
    # -------------------------------------------------------------
    print("\n[TEST 8/12] Generating A4 Clinical PDF Report via ReportLab...")
    t_pdf = time.perf_counter()
    pdf_bytes = generate_screening_pdf(report_data, uploads_dir)
    pdf_latency = round((time.perf_counter() - t_pdf) * 1000, 2)
    assert len(pdf_bytes) > 50000, f"Expected substantive PDF bytes, got {len(pdf_bytes)}"
    assert pdf_bytes.startswith(b"%PDF"), "Output buffer must start with %PDF magic number"
    print(f"  ✓ Generated clinical PDF ({len(pdf_bytes)} bytes) in {pdf_latency}ms.")

    # -------------------------------------------------------------
    # Test 9: PDF Download Endpoint
    # -------------------------------------------------------------
    print("\n[TEST 9/12] Testing HTTP PDF Download Endpoint...")
    dl_res = client.get(f"/api/dental/reports/{report_id}/pdf")
    assert dl_res.status_code == 200, f"Expected 200, got {dl_res.status_code}"
    assert dl_res.headers["content-type"] == "application/pdf"
    assert f'filename="DentalAI_Report_{report_id}.pdf"' in dl_res.headers.get("content-disposition", "")
    assert dl_res.headers.get("x-report-id") == report_id
    assert len(dl_res.content) == len(pdf_bytes)
    print(f"  ✓ PDF HTTP download verified: 200 OK, Content-Type: application/pdf")

    # -------------------------------------------------------------
    # Test 10: Dashboard Analytics
    # -------------------------------------------------------------
    print("\n[TEST 10/12] Inspecting Real Dashboard Analytics & Timeline Trends...")
    stats_res = client.get("/api/dental/stats")
    assert stats_res.status_code == 200
    stats = stats_res.json()
    assert stats["total_patients"] >= 1
    assert stats["total_scans"] >= 1
    assert "completed_scans" in stats
    assert "inconclusive_scans" in stats
    assert len(stats["scans_over_time"]) >= 1
    assert "Gingivitis" in stats["disease_distribution"]
    print(f"  ✓ Dashboard metrics verified from PostgreSQL:")
    print(f"     • Total Patients: {stats['total_patients']}")
    print(f"     • Total Scans: {stats['total_scans']}")
    print(f"     • Completed Scans: {stats['completed_scans']}")
    print(f"     • Inconclusive Views: {stats['inconclusive_scans']}")
    print(f"     • Scans Over Time entries: {len(stats['scans_over_time'])}")

    # -------------------------------------------------------------
    # Test 11: Unauthorized / Non-existent Record Access
    # -------------------------------------------------------------
    print("\n[TEST 11/12] Testing Non-Existent Record Guard & Error Handling...")
    err_pat = client.get("/api/patients/NON-EXISTENT-ID-9999")
    assert err_pat.status_code == 404, f"Expected 404, got {err_pat.status_code}"
    err_rep = client.get("/api/dental/reports/RPT-NOT-FOUND-999/pdf")
    assert err_rep.status_code == 404, f"Expected 404, got {err_rep.status_code}"
    print(f"  ✓ Non-existent patient & report access returned 404 Not Found.")

    # -------------------------------------------------------------
    # Test 12: Invalid Input & Image Validation
    # -------------------------------------------------------------
    print("\n[TEST 12/12] Testing Invalid Input and Image Handling...")
    # Missing left & right views
    with open(front_sample, "rb") as f_front:
        bad_req = client.post(
            "/api/dental/screenings",
            data={"patient_name": "Test", "patient_id": "PT-ERR"},
            files={"front_image": ("front.jpg", f_front, "image/jpeg")}
        )
    assert bad_req.status_code in [400, 422], f"Expected 400/422 on missing views, got {bad_req.status_code}"

    # Duplicate patient registration attempt
    dup_res = client.post("/api/patients", json=reg_payload)
    assert dup_res.status_code == 409, f"Expected 409 on duplicate patient registration, got {dup_res.status_code}"
    print(f"  ✓ Missing views and duplicate patient IDs properly rejected.")

    # Cleanup test patient to maintain clean database state
    del_res = client.delete(f"/api/patients/{test_pid}")
    assert del_res.status_code == 200
    print(f"  ✓ Safely deleted test patient '{test_pid}' and cascaded DB records.")

    print("\n" + "=" * 70)
    print("ALL 12 PHASE 3 TESTS COMPLETED SUCCESSFULLY WITH 100% PASS RATE!")
    print("=" * 70)

if __name__ == "__main__":
    run_phase3_clinical_tests()

