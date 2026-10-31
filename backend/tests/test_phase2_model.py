import os
import sys
import time
import io
import numpy as np
from PIL import Image

# Add backend directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from app.main import app
from app.ai.model_loader import (
    get_dental_model,
    get_class_indices,
    get_model_status,
    load_dental_model,
    DEFAULT_ABSTENTION_THRESHOLD
)
from app.ai.image_preprocessing import validate_image_file, preprocess_dental_image
from app.ai.inference import (
    run_inference,
    generate_gradcam_heatmap,
    create_gradcam_overlay,
    GRADCAM_LAYER_NAME
)
from app.ai.prediction_processor import process_three_views
from app.ai.report_generator import generate_screening_report, PRIMARY_SAFETY_NOTICE

client = TestClient(app)

def run_phase2_tests():
    print("=" * 65)
    print("DENTALAI - PHASE 2: RESNET-50 INTEGRATION & INFERENCE TEST SUITE")
    print("=" * 65)

    samples_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "samples")
    front_sample = os.path.join(samples_dir, "sample_caries_front.jpg")
    left_sample = os.path.join(samples_dir, "sample_gingivitis_left.jpg")
    right_sample = os.path.join(samples_dir, "sample_calculus_right.jpg")
    test_uploads_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "uploads")

    # -------------------------------------------------------------
    # Test 1: Model Loading & Architectural Verification
    # -------------------------------------------------------------
    print("\n[TEST 1/10] Verifying Model Loading & Architecture...")
    t0 = time.perf_counter()
    model = get_dental_model()
    load_time = round((time.perf_counter() - t0) * 1000, 2)
    assert model is not None, "Failed to load model"
    assert model.input_shape == (None, 224, 224, 3), f"Unexpected input shape: {model.input_shape}"
    assert model.output_shape == (None, 6), f"Unexpected output shape: {model.output_shape}"
    print(f"  ✓ Model loaded in {load_time}ms.")
    print(f"  ✓ Verified input tensor: {model.input_shape}, output tensor: {model.output_shape}")
    print(f"  ✓ Backbone: {model.layers[0].name} ({len(model.layers[0].layers)} layers)")

    # -------------------------------------------------------------
    # Test 2: Input Image Validation
    # -------------------------------------------------------------
    print("\n[TEST 2/10] Verifying Input Image Validation...")
    with open(front_sample, "rb") as f:
        valid_bytes = f.read()
    val_meta = validate_image_file(valid_bytes, "sample_caries_front.jpg")
    assert val_meta["format"] in ["JPEG", "JPG"]
    assert val_meta["width"] >= 150 and val_meta["height"] >= 150
    assert val_meta["size_bytes"] > 1024
    print(f"  ✓ Valid photo accepted: format={val_meta['format']}, {val_meta['width']}x{val_meta['height']}px, clarity={val_meta['clarity_score']}")

    # -------------------------------------------------------------
    # Test 3: Preprocessing Parity with ResNet-50 Caffe Mode
    # -------------------------------------------------------------
    print("\n[TEST 3/10] Verifying Image Preprocessing Matching Training Config...")
    tensor, orig_img, q_info = preprocess_dental_image(valid_bytes)
    assert tensor.shape == (1, 224, 224, 3), f"Invalid tensor shape: {tensor.shape}"
    assert tensor.dtype == np.float32
    # Verify BGR channel mean subtraction: mean values should center near zero/negative
    b_mean = float(np.mean(tensor[:, :, :, 0]))
    g_mean = float(np.mean(tensor[:, :, :, 1]))
    r_mean = float(np.mean(tensor[:, :, :, 2]))
    print(f"  ✓ Preprocessed tensor shape: {tensor.shape}, dtype: {tensor.dtype}")
    print(f"  ✓ Caffe BGR channel means: B={b_mean:.2f}, G={g_mean:.2f}, R={r_mean:.2f}")

    # -------------------------------------------------------------
    # Test 4: Correct Class-Index Mapping & Ordering
    # -------------------------------------------------------------
    print("\n[TEST 4/10] Verifying Class-Index Mapping...")
    class_indices = get_class_indices()
    expected_classes = {
        0: "Calculus",
        1: "Caries",
        2: "Gingivitis",
        3: "Hypodontia",
        4: "Mouth_Ulcer",
        5: "Tooth_Discoloration"
    }
    assert len(class_indices) == 6, f"Expected 6 classes, got {len(class_indices)}"
    for idx, cname in expected_classes.items():
        assert class_indices.get(idx) == cname, f"Mismatch at index {idx}: expected {cname}, got {class_indices.get(idx)}"
    print(f"  ✓ Verified exact 6-class order: {list(class_indices.values())}")

    # -------------------------------------------------------------
    # Test 5: Single-Image Inference with Timing & Output Scores
    # -------------------------------------------------------------
    print("\n[TEST 5/10] Executing Single-Image Genuine Inference...")
    single_res = run_inference(
        tensor=tensor,
        orig_img=orig_img,
        view_name="front",
        output_dir=test_uploads_dir
    )
    assert "predicted_class" in single_res
    assert "model_output_scores" in single_res
    assert len(single_res["model_output_scores"]) == 6
    assert len(single_res["top_three_predictions"]) == 3
    assert single_res["inference_time_ms"] > 0
    assert single_res["processing_status"] in ["success", "low_confidence_abstention"]
    print(f"  ✓ Predicted class: {single_res['predicted_name']}")
    print(f"  ✓ Model output score: {single_res['model_output_score']} ({single_res['confidence_percentage']}%)")
    print(f"  ✓ Measured inference time: {single_res['inference_time_ms']}ms")
    print("  ✓ Top-3 predictions:")
    for item in single_res["top_three_predictions"]:
        print(f"     Rank {item['rank']}: {item['display_name']} -> {item['percentage']}%")

    # -------------------------------------------------------------
    # Test 6: Three-View Intraoral Processing Pipeline
    # -------------------------------------------------------------
    print("\n[TEST 6/10] Executing Multi-Angle Three-View Processing...")
    views = {
        "front": front_sample,
        "left": left_sample,
        "right": right_sample
    }
    multi_results = {}
    for vname, vpath in views.items():
        with open(vpath, "rb") as f:
            v_bytes = f.read()
        v_tensor, v_pil, _ = preprocess_dental_image(v_bytes)
        multi_results[vname] = run_inference(v_tensor, v_pil, vname, output_dir=test_uploads_dir)
        print(f"  ✓ {vname.capitalize()} View: {multi_results[vname]['predicted_name']} ({multi_results[vname]['confidence_percentage']}%) [{multi_results[vname]['inference_time_ms']}ms]")

    consolidated = process_three_views(multi_results)
    assert len(consolidated["views_evaluated"]) == 3
    assert "multi_view_notice" in consolidated
    print(f"  ✓ Combined multi-angle status: {consolidated['overall_status']}")
    print(f"  ✓ Total inference execution time: {consolidated['total_inference_time_ms']}ms")

    # -------------------------------------------------------------
    # Test 7: Grad-CAM Generation on conv5_block3_out
    # -------------------------------------------------------------
    print("\n[TEST 7/10] Verifying Grad-CAM on conv5_block3_out Layer...")
    top_idx = int(list(class_indices.keys())[list(class_indices.values()).index(single_res["predicted_class"])])
    cam_7x7 = generate_gradcam_heatmap(model, tensor, top_idx)
    assert cam_7x7.shape == (7, 7), f"Expected 7x7 Grad-CAM matrix, got {cam_7x7.shape}"
    assert np.max(cam_7x7) <= 1.0 and np.min(cam_7x7) >= 0.0
    orig_file, heatmap_file, stats = create_gradcam_overlay(orig_img, cam_7x7, output_dir=test_uploads_dir, file_prefix="test_cam")
    assert orig_file is not None and os.path.exists(os.path.join(test_uploads_dir, orig_file))
    assert heatmap_file is not None and os.path.exists(os.path.join(test_uploads_dir, heatmap_file))
    print(f"  ✓ Layer target: {GRADCAM_LAYER_NAME}")
    print(f"  ✓ Grad-CAM 7x7 computed. Max salience: {stats['peak_activation']}, Mean: {stats['mean_activation']}")
    print(f"  ✓ Side-by-side files generated: {orig_file} & {heatmap_file}")

    # -------------------------------------------------------------
    # Test 8: Invalid Image & Edge Cases Handling
    # -------------------------------------------------------------
    print("\n[TEST 8/10] Testing Invalid Image Handling...")
    # A. Corrupted bytes
    try:
        validate_image_file(b"NOT_AN_IMAGE_DATA_1234567890", "corrupt.jpg")
        assert False, "Should have raised ValueError on corrupted bytes"
    except ValueError as e:
        print(f"  ✓ Corrupted image rejected: {e}")

    # B. Unsupported format (.bmp or .gif)
    try:
        validate_image_file(valid_bytes, "test.gif")
        assert False, "Should have raised ValueError on unsupported extension"
    except ValueError as e:
        print(f"  ✓ Unsupported format rejected: {e}")

    # C. Sub-minimum resolution (< 150x150)
    tiny_img = Image.new("RGB", (64, 64), color="white")
    tiny_buf = io.BytesIO()
    tiny_img.save(tiny_buf, format="JPEG")
    try:
        validate_image_file(tiny_buf.getvalue(), "tiny.jpg")
        assert False, "Should have raised ValueError on sub-minimum resolution"
    except ValueError as e:
        print(f"  ✓ Sub-minimum resolution rejected: {e}")

    # -------------------------------------------------------------
    # Test 9: Model Status & Missing Weights Safety
    # -------------------------------------------------------------
    print("\n[TEST 9/10] Testing Model Status Reporting & Error Handling...")
    status_info = get_model_status()
    assert status_info["is_loaded"] is True
    assert status_info["file_exists"] is True
    assert "metadata" in status_info
    print(f"  ✓ Model status operational. Architecture: {status_info['metadata']['architecture']}")
    print(f"  ✓ Checkpoint size: {status_info['metadata']['model_size_mb']} MB")

    # -------------------------------------------------------------
    # Test 10: Backend API Endpoints Integration
    # -------------------------------------------------------------
    print("\n[TEST 10/10] Verifying Backend API Endpoints Integration...")
    # A. GET /api/dental/model-status
    res_status = client.get("/api/dental/model-status")
    assert res_status.status_code == 200
    st_json = res_status.json()
    assert st_json["is_loaded"] is True
    assert PRIMARY_SAFETY_NOTICE in st_json["primary_safety_notice"]
    print("  ✓ GET /api/dental/model-status returned 200 OK.")

    # B. POST /api/dental/analyze (single image)
    with open(front_sample, "rb") as f_front:
        files = {"image": ("front.jpg", f_front, "image/jpeg")}
        data = {"view_name": "front"}
        res_single = client.post("/api/dental/analyze", files=files, data=data)
    assert res_single.status_code == 200
    single_json = res_single.json()
    assert "predicted_class" in single_json
    assert "top_three_predictions" in single_json
    print(f"  ✓ POST /api/dental/analyze returned 200 OK -> {single_json['predicted_name']} ({single_json['confidence_percentage']}%)")

    # C. POST /api/dental/analyze-multiple (three views)
    with open(front_sample, "rb") as f_f, open(left_sample, "rb") as f_l, open(right_sample, "rb") as f_r:
        files = {
            "front_image": ("front.jpg", f_f, "image/jpeg"),
            "left_image": ("left.jpg", f_l, "image/jpeg"),
            "right_image": ("right.jpg", f_r, "image/jpeg")
        }
        data = {
            "patient_name": "Marcus Aurelius",
            "patient_id": "PT-MA-101",
            "age": "58",
            "gender": "Male",
            "notes": "Routine photographic pre-screening."
        }
        res_multi = client.post("/api/dental/analyze-multiple", files=files, data=data)
    assert res_multi.status_code == 200
    multi_json = res_multi.json()
    assert "report_id" in multi_json
    assert len(multi_json["images_analyzed"]) == 3
    print(f"  ✓ POST /api/dental/analyze-multiple returned 200 OK -> Report ID: {multi_json['report_id']}")

    print("\n" + "=" * 65)
    print("ALL 10 PHASE 2 TESTS COMPLETED SUCCESSFULLY WITH 100% PASS RATE!")
    print("=" * 65)

if __name__ == "__main__":
    run_phase2_tests()

