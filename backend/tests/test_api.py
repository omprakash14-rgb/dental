import os
import sys

# Ensure backend root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_api():
    print("==================================================")
    print("PHASE 4 TEST: Testing DentalAI FastAPI Endpoints")
    print("==================================================")

    # 1. Test Health Endpoint
    print("\n[1/6] Testing GET /api/health...")
    res = client.get("/api/health")
    assert res.status_code == 200, f"Health check failed: {res.text}"
    health_data = res.json()
    print("  Health response:", health_data)
    assert health_data["ai_model_loaded"] is True
    assert health_data["database_status"] == "connected"

    # 2. Test Multi-Image Analysis Endpoint (POST /api/analyze)
    print("\n[2/6] Testing POST /api/analyze with 3 intraoral photos...")
    samples_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "samples")
    front_path = os.path.join(samples_dir, "sample_caries_front.jpg")
    left_path = os.path.join(samples_dir, "sample_gingivitis_left.jpg")
    right_path = os.path.join(samples_dir, "sample_calculus_right.jpg")

    with open(front_path, "rb") as f_front, open(left_path, "rb") as f_left, open(right_path, "rb") as f_right:
        files = {
            "front_image": ("front.jpg", f_front, "image/jpeg"),
            "left_image": ("left.jpg", f_left, "image/jpeg"),
            "right_image": ("right.jpg", f_right, "image/jpeg"),
        }
        data = {
            "patient_name": "Eleanor Vance",
            "patient_id": "PT-EV-8841",
            "age": "29",
            "gender": "Female",
            "notes": "Sensitivity to thermal changes, routine pre-screening."
        }
        analyze_res = client.post("/api/analyze", data=data, files=files)

    assert analyze_res.status_code == 200, f"Analysis failed: {analyze_res.text}"
    report = analyze_res.json()
    report_id = report["report_id"]
    print("  Analysis completed successfully!")
    print(f"  Report ID: {report_id}")
    print(f"  Overall Status: {report['screening_summary']['overall_status']}")
    print(f"  Urgency: {report['screening_summary']['urgency_level']}")
    print(f"  Detected Conditions: {len(report['detected_conditions'])}")
    for d in report['detected_conditions']:
        print(f"    - {d['disease_name']}: {d['confidence_percentage']}% on {d['affected_views']}")

    # 3. Test Fetching Report by ID
    print(f"\n[3/6] Testing GET /api/reports/{report_id}...")
    rep_res = client.get(f"/api/reports/{report_id}")
    assert rep_res.status_code == 200
    fetched_rep = rep_res.json()
    assert fetched_rep["report_id"] == report_id
    print("  Report fetched successfully by ID.")

    # 4. Test Listing Patients
    print("\n[4/6] Testing GET /api/patients...")
    patients_res = client.get("/api/patients")
    assert patients_res.status_code == 200
    patients = patients_res.json()
    print(f"  Total registered patients: {len(patients)}")
    assert any(p["patient_id"] == "PT-EV-8841" for p in patients)

    # 5. Test Patient History
    print("\n[5/6] Testing GET /api/patients/PT-EV-8841...")
    pat_res = client.get("/api/patients/PT-EV-8841")
    assert pat_res.status_code == 200
    pat_history = pat_res.json()
    print(f"  Patient: {pat_history['patient']['name']}")
    print(f"  Scans in history: {pat_history['scans_count']}")

    # 6. Test Dashboard Stats
    print("\n[6/6] Testing GET /api/stats...")
    stats_res = client.get("/api/stats")
    assert stats_res.status_code == 200
    stats = stats_res.json()
    print(f"  Dashboard Stats: Total Patients={stats['total_patients']}, Total Scans={stats['total_scans']}")
    print("  Disease distribution:", stats["disease_distribution"])

    print("\n==================================================")
    print("ALL API ENDPOINT TESTS PASSED WITH 100% SUCCESS!")
    print("==================================================")

if __name__ == "__main__":
    test_api()

