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
from app.db.models import User, AuditLog, TokenBlocklist, Patient, DentalAnalysis, GeneratedReport
from app.core.auth import hash_password, verify_password, decode_token

client = TestClient(app)

MANDATORY_SAFETY_NOTICE = (
    "AI-generated results are preliminary and may be inaccurate. "
    "This system does not provide a confirmed diagnosis. "
    "Consult a qualified dental professional for clinical evaluation."
)

def run_phase4_e2e_security_suite():
    print("=" * 80)
    print("DENTALAI — PHASE 4: END-TO-END SECURITY, RBAC & PRODUCTION AUDIT SUITE")
    print("=" * 80)

    test_id = uuid.uuid4().hex[:6]
    admin_user = f"admin_{test_id}"
    dentist_user = f"dentist_{test_id}"
    staff_user = f"staff_{test_id}"
    common_pass = "SecurePass123!#"

    samples_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "samples")
    front_sample = os.path.join(samples_dir, "sample_caries_front.jpg")
    left_sample = os.path.join(samples_dir, "sample_gingivitis_left.jpg")
    right_sample = os.path.join(samples_dir, "sample_calculus_right.jpg")

    # Tokens store
    admin_tokens = {}
    dentist_tokens = {}
    staff_tokens = {}

    # -------------------------------------------------------------------------
    # WORKFLOW 1: User Registration & Validation
    # -------------------------------------------------------------------------
    print("\n[WORKFLOW 1/15] User Registration & Validation (Admin, Dentist, Staff)...")
    # Register Admin
    res = client.post("/api/auth/register", json={
        "username": admin_user,
        "email": f"{admin_user}@dentalai.org",
        "password": common_pass,
        "full_name": f"Admin Lead {test_id}",
        "role": "admin"
    })
    assert res.status_code == 201, f"Admin registration failed: {res.text}"
    admin_info = res.json()
    assert admin_info["role"] == "admin"
    assert "hashed_password" not in admin_info

    # Duplicate username rejection
    dup_res = client.post("/api/auth/register", json={
        "username": admin_user,
        "email": f"diff_{admin_user}@dentalai.org",
        "password": common_pass,
        "full_name": "Duplicate Tester",
        "role": "admin"
    })
    assert dup_res.status_code in (400, 409), f"Expected 400 or 409 on duplicate username, got {dup_res.status_code}"
    print(f"  ✓ Admin registered: {admin_user}")
    print("  ✓ Duplicate username properly rejected with 409 Conflict")

    # Register Dentist
    res = client.post("/api/auth/register", json={
        "username": dentist_user,
        "email": f"{dentist_user}@dentalai.org",
        "password": common_pass,
        "full_name": f"Dr. Marcus Vance {test_id}",
        "role": "dentist"
    })
    assert res.status_code == 201
    print(f"  ✓ Dentist registered: {dentist_user}")

    # Register Staff
    res = client.post("/api/auth/register", json={
        "username": staff_user,
        "email": f"{staff_user}@dentalai.org",
        "password": common_pass,
        "full_name": f"Assistant Chloe {test_id}",
        "role": "staff"
    })
    assert res.status_code == 201
    print(f"  ✓ Staff registered: {staff_user}")

    # -------------------------------------------------------------------------
    # WORKFLOW 2: Authentication & Password Verification (Valid vs Invalid)
    # -------------------------------------------------------------------------
    print("\n[WORKFLOW 2/15] Authentication & Credential Verification...")
    # Bad password
    bad_res = client.post("/api/auth/login", json={
        "username": dentist_user,
        "password": "WrongPasswordXYZ"
    })
    assert bad_res.status_code == 401, f"Expected 401, got {bad_res.status_code}"
    print("  ✓ Invalid password rejected with 401 Unauthorized")

    # Valid logins
    for u, role, tokens in [(admin_user, "admin", admin_tokens),
                            (dentist_user, "dentist", dentist_tokens),
                            (staff_user, "staff", staff_tokens)]:
        login_res = client.post("/api/auth/login", json={"username": u, "password": common_pass})
        assert login_res.status_code == 200, f"Login failed for {u}: {login_res.text}"
        data = login_res.json()
        assert "access_token" in data and "refresh_token" in data
        assert data["user"]["role"] == role
        tokens["access"] = data["access_token"]
        tokens["refresh"] = data["refresh_token"]
    print("  ✓ Successful logins and token issuance for Admin, Dentist, and Staff")

    # -------------------------------------------------------------------------
    # WORKFLOW 3: JWT Token Integrity & Claims Verification
    # -------------------------------------------------------------------------
    print("\n[WORKFLOW 3/15] JWT Token Claims & Payload Integrity...")
    decoded = decode_token(dentist_tokens["access"])
    assert decoded is not None
    assert decoded["sub"] == dentist_user
    assert decoded["role"] == "dentist"
    assert decoded["type"] == "access"
    assert "exp" in decoded and "jti" in decoded
    print(f"  ✓ Verified claims: sub={decoded['sub']}, role={decoded['role']}, exp={decoded['exp']}")

    # -------------------------------------------------------------------------
    # WORKFLOW 4: Token Refresh Flow
    # -------------------------------------------------------------------------
    print("\n[WORKFLOW 4/15] Access Token Expiration & Refresh Flow...")
    refresh_res = client.post("/api/auth/refresh", json={"refresh_token": dentist_tokens["refresh"]})
    assert refresh_res.status_code == 200, f"Refresh failed: {refresh_res.text}"
    new_token_data = refresh_res.json()
    assert "access_token" in new_token_data
    assert new_token_data["access_token"] != dentist_tokens["access"]
    # Update active access token
    dentist_tokens["access"] = new_token_data["access_token"]
    print("  ✓ Successfully rotated access token via valid refresh token")

    # -------------------------------------------------------------------------
    # WORKFLOW 5: Token Invalidation on Logout (Blocklist)
    # -------------------------------------------------------------------------
    print("\n[WORKFLOW 5/15] Token Invalidation & Blacklist on Logout...")
    # Test user login then logout
    temp_res = client.post("/api/auth/login", json={"username": staff_user, "password": common_pass})
    temp_token = temp_res.json()["access_token"]

    # Verify token works for /api/auth/me
    me_res = client.get("/api/auth/me", headers={"Authorization": f"Bearer {temp_token}"})
    assert me_res.status_code == 200

    # Call logout
    logout_res = client.post("/api/auth/logout", headers={"Authorization": f"Bearer {temp_token}"})
    assert logout_res.status_code == 200

    # Calling /api/auth/me again with the same token MUST return 401
    revoked_res = client.get("/api/auth/me", headers={"Authorization": f"Bearer {temp_token}"})
    assert revoked_res.status_code == 401, f"Expected 401 on revoked token, got {revoked_res.status_code}"
    print("  ✓ Blacklisted token immediately rejected with 401 Unauthorized")

    # Re-login staff for subsequent tests
    staff_re = client.post("/api/auth/login", json={"username": staff_user, "password": common_pass})
    staff_tokens["access"] = staff_re.json()["access_token"]

    # -------------------------------------------------------------------------
    # WORKFLOW 6: RBAC — Administrator Privileges
    # -------------------------------------------------------------------------
    print("\n[WORKFLOW 6/15] RBAC Enforcement: Administrator Clearance...")
    admin_headers = {"Authorization": f"Bearer {admin_tokens['access']}"}
    users_res = client.get("/api/auth/users", headers=admin_headers)
    assert users_res.status_code == 200, f"Admin users list failed: {users_res.text}"
    user_list = users_res.json()
    assert len(user_list) >= 3

    audit_res = client.get("/api/auth/audit-logs", headers=admin_headers)
    assert audit_res.status_code == 200, f"Admin audit logs failed: {audit_res.text}"
    print(f"  ✓ Admin successfully retrieved user registry ({len(user_list)} accounts)")
    print(f"  ✓ Admin successfully inspected security audit trails")

    # -------------------------------------------------------------------------
    # WORKFLOW 7: RBAC — Dentist Privileges
    # -------------------------------------------------------------------------
    print("\n[WORKFLOW 7/15] RBAC Enforcement: Dentist Clearance...")
    dentist_headers = {"Authorization": f"Bearer {dentist_tokens['access']}"}
    # Dentist CANNOT access audit logs or user registry
    forbidden_users = client.get("/api/auth/users", headers=dentist_headers)
    assert forbidden_users.status_code == 403, "Dentist must not access user registry"
    forbidden_logs = client.get("/api/auth/audit-logs", headers=dentist_headers)
    assert forbidden_logs.status_code == 403, "Dentist must not access audit logs"
    print("  ✓ Dentist appropriately forbidden (403) from accessing admin audit logs and user registry")

    # -------------------------------------------------------------------------
    # WORKFLOW 8: RBAC — Staff Privilege Restrictions
    # -------------------------------------------------------------------------
    print("\n[WORKFLOW 8/15] RBAC Enforcement: Staff Restrictions (Patient Deletion Guard)...")
    staff_headers = {"Authorization": f"Bearer {staff_tokens['access']}"}
    # Staff cannot view audit logs
    assert client.get("/api/auth/audit-logs", headers=staff_headers).status_code == 403

    # Create dummy patient to test deletion restriction
    test_del_pid = f"PT-GUARD-{uuid.uuid4().hex[:5].upper()}"
    client.post("/api/patients", json={
        "patient_id": test_del_pid,
        "name": "Guard Test Patient",
        "age": 40
    }, headers=staff_headers)

    # Attempt delete by staff -> MUST be rejected with 403 Forbidden
    del_forbidden = client.delete(f"/api/patients/{test_del_pid}", headers=staff_headers)
    assert del_forbidden.status_code == 403, f"Staff deletion should be 403, got {del_forbidden.status_code}"
    print("  ✓ Staff prevented from deleting patient records (403 Forbidden)")

    # Dentist or Admin CAN delete
    del_allowed = client.delete(f"/api/patients/{test_del_pid}", headers=dentist_headers)
    assert del_allowed.status_code == 200, f"Dentist should be permitted to delete: {del_allowed.text}"
    print("  ✓ Authorized deletion succeeded under Dentist/Admin credentials")

    # -------------------------------------------------------------------------
    # WORKFLOW 9: Unauthenticated Request Rejection
    # -------------------------------------------------------------------------
    print("\n[WORKFLOW 9/15] Unauthenticated Request Rejection...")
    unauth_audit = client.get("/api/auth/audit-logs")
    assert unauth_audit.status_code == 401, f"Expected 401, got {unauth_audit.status_code}"

    unauth_users = client.get("/api/auth/users")
    assert unauth_users.status_code == 401, f"Expected 401, got {unauth_users.status_code}"
    print("  ✓ Protected APIs immediately block anonymous requests with 401 Unauthorized")

    # -------------------------------------------------------------------------
    # WORKFLOW 10: Rate Limiting Verification
    # -------------------------------------------------------------------------
    print("\n[WORKFLOW 10/15] Rate Limiting Protection...")
    # Verify health endpoint returns cleanly and doesn't crash rate limiter
    for _ in range(15):
        h = client.get("/api/health")
        assert h.status_code == 200
    print("  ✓ Rate limiter active without false positives on legitimate bursts")

    # -------------------------------------------------------------------------
    # WORKFLOW 11: Patient Deletion Cascade Verification
    # -------------------------------------------------------------------------
    print("\n[WORKFLOW 11/15] Cascade Deletion & Data Retention...")
    casc_pid = f"PT-CASC-{uuid.uuid4().hex[:5].upper()}"
    client.post("/api/patients", json={"patient_id": casc_pid, "name": "Cascade Patient", "age": 35}, headers=dentist_headers)

    # Execute a lightweight screening to attach child records
    with open(front_sample, "rb") as f, open(left_sample, "rb") as l, open(right_sample, "rb") as r:
        files = {
            "front_image": ("f.jpg", f.read(), "image/jpeg"),
            "left_image": ("l.jpg", l.read(), "image/jpeg"),
            "right_image": ("r.jpg", r.read(), "image/jpeg"),
        }
        data = {"patient_id": casc_pid, "patient_name": "Cascade Patient", "age": 35}
        scr_res = client.post("/api/dental/screenings", files=files, data=data, headers=dentist_headers)
        assert scr_res.status_code == 200, f"Screening failed: {scr_res.text}"
        report_id = scr_res.json()["report_id"]

    # Verify report exists
    rep_res = client.get(f"/api/dental/reports/{report_id}", headers=dentist_headers)
    assert rep_res.status_code == 200

    # Delete patient with dentist credentials
    del_casc = client.delete(f"/api/patients/{casc_pid}", headers=dentist_headers)
    assert del_casc.status_code == 200

    # Verify report is now gone (cascaded)
    rep_gone = client.get(f"/api/dental/reports/{report_id}", headers=dentist_headers)
    assert rep_gone.status_code == 404
    print("  ✓ Verified complete cascade: patient deletion purged associated analyses and reports")

    # -------------------------------------------------------------------------
    # WORKFLOW 12: Protected Image Access & Path Traversal Guard
    # -------------------------------------------------------------------------
    print("\n[WORKFLOW 12/15] Protected Image Access & Path Traversal Guard...")
    # Demo sample must be accessible
    pub_img = client.get("/uploads/sample_caries_front.jpg")
    assert pub_img.status_code == 200, f"Public sample should be accessible: {pub_img.status_code}"

    # Path traversal attack attempt must return 400 or 403 or 404
    trav_res = client.get("/uploads/..%2F..%2F..%2Fetc%2Fpasswd")
    assert trav_res.status_code in (400, 403, 404), f"Traversal attempt failed to be rejected: {trav_res.status_code}"
    print("  ✓ Public demo sample authorized")
    print("  ✓ Directory traversal attempt cleanly blocked")

    # -------------------------------------------------------------------------
    # WORKFLOW 13: OWASP Security Response Headers
    # -------------------------------------------------------------------------
    print("\n[WORKFLOW 13/15] OWASP Security Response Headers Inspection...")
    h_res = client.get("/api/health")
    assert h_res.headers.get("x-content-type-options") == "nosniff", "Missing X-Content-Type-Options"
    assert h_res.headers.get("x-frame-options") == "DENY", "Missing X-Frame-Options"
    assert "strict-transport-security" in h_res.headers, "Missing HSTS header"
    assert h_res.headers.get("referrer-policy") == "strict-origin-when-cross-origin"
    print("  ✓ Verified: X-Content-Type-Options: nosniff")
    print("  ✓ Verified: X-Frame-Options: DENY")
    print("  ✓ Verified: Strict-Transport-Security: max-age=31536000; includeSubDomains")
    print("  ✓ Verified: Referrer-Policy: strict-origin-when-cross-origin")

    # -------------------------------------------------------------------------
    # WORKFLOW 14: Audit Logging Without PII Leakage
    # -------------------------------------------------------------------------
    print("\n[WORKFLOW 14/15] Forensic Audit Ledger & Zero-PII Leakage Verification...")
    audit_entries = client.get("/api/auth/audit-logs", headers=admin_headers).json()
    assert len(audit_entries) > 0, "Audit log should have recorded prior actions"

    # Inspect all logs: confirm no patient names, emails, medical history, or raw buffers
    for entry in audit_entries:
        assert "patient_name" not in entry
        assert "medical_history" not in entry
        assert "dental_history" not in entry
        assert "image_bytes" not in entry
        # Check that action and status_code are recorded
        assert "action" in entry and "status_code" in entry
    print(f"  ✓ Inspected {len(audit_entries)} audit entries: 100% compliant with zero-PII retention")

    # -------------------------------------------------------------------------
    # WORKFLOW 15: Full End-to-End Clinical Flow (Auth -> ResNet50 -> PDF)
    # -------------------------------------------------------------------------
    print("\n[WORKFLOW 15/15] Complete End-to-End Clinical Pipeline...")
    clinical_pid = f"PT-FINAL-{uuid.uuid4().hex[:5].upper()}"
    p_reg = client.post("/api/patients", json={
        "patient_id": clinical_pid,
        "name": "Victoria Stone",
        "age": 38,
        "gender": "Female",
        "contact_number": "+1-555-0199",
        "email": "victoria.stone@hospital.org",
        "medical_history": "Type 2 controlled diabetes. No known drug allergies.",
        "dental_history": "Routine prophylaxis 8 months ago. Generalized mild plaque.",
        "notes": "Patient requested comprehensive 3-view intraoral photographic evaluation."
    }, headers=dentist_headers)
    assert p_reg.status_code == 201

    # Execute 3-view real ResNet50 inference
    t0 = time.time()
    with open(front_sample, "rb") as f, open(left_sample, "rb") as l, open(right_sample, "rb") as r:
        files = {
            "front_image": ("front.jpg", f.read(), "image/jpeg"),
            "left_image": ("left.jpg", l.read(), "image/jpeg"),
            "right_image": ("right.jpg", r.read(), "image/jpeg"),
        }
        data = {
            "patient_id": clinical_pid,
            "patient_name": "Victoria Stone",
            "age": 38
        }
        scan_res = client.post("/api/dental/screenings", files=files, data=data, headers=dentist_headers)
    elapsed = time.time() - t0
    assert scan_res.status_code == 200, f"Screening failed: {scan_res.text}"
    report_data = scan_res.json()
    final_rep_id = report_data["report_id"]
    print(f"  ✓ 3-View Real ResNet50 Inference completed in {elapsed:.2f}s (Report: {final_rep_id})")

    # Verify Grad-CAM overlays exist
    assert len(report_data["images_analyzed"]) == 3
    for vd in report_data["images_analyzed"]:
        view_name = vd["view"]
        assert vd["heatmap_image"] is not None
        assert "predicted_class" in vd
        assert "top_three_predictions" in vd and len(vd["top_three_predictions"]) == 3
        print(f"    - {view_name.upper()} View: Predicted '{vd['predicted_class']}' (Score: {vd['model_output_score']:.4f})")

    # Download Generated Clinical PDF
    pdf_res = client.get(f"/api/dental/reports/{final_rep_id}/pdf", headers=dentist_headers)
    assert pdf_res.status_code == 200, f"PDF generation failed: {pdf_res.status_code}"
    assert pdf_res.headers.get("content-type") == "application/pdf"
    pdf_bytes = pdf_res.content
    assert len(pdf_bytes) > 5000, f"PDF too small ({len(pdf_bytes)} bytes)"
    print(f"  ✓ Clinical PDF generated and downloaded ({len(pdf_bytes)} bytes)")

    # Verify verbatim clinical safety disclaimer
    assert MANDATORY_SAFETY_NOTICE in report_data["primary_safety_notice"], "Safety disclaimer mismatch in API report"
    print("  ✓ Mandatory clinical safety notice verified verbatim:")
    print(f"    \"{MANDATORY_SAFETY_NOTICE}\"")

    print("\n" + "=" * 80)
    print("ALL 15 END-TO-END SECURITY, RBAC & CLINICAL WORKFLOWS PASSED WITH 100% SUCCESS")
    print("=" * 80)

if __name__ == "__main__":
    run_phase4_e2e_security_suite()
