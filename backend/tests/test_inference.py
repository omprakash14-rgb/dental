import os
import sys

# Ensure backend root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
from app.ai.model_loader import get_dental_model, get_class_indices
from app.ai.image_preprocessing import validate_image_file, preprocess_dental_image
from app.ai.inference import run_inference
from app.ai.prediction_processor import process_three_views
from app.ai.report_generator import generate_screening_report

def main():
    print("==================================================")
    print("PHASE 3 TEST: Testing DentalAI Inference Pipeline")
    print("==================================================")

    # 1. Test Model Loading
    print("\n[1/5] Loading Dental ResNet-50 Model...")
    model = get_dental_model()
    class_indices = get_class_indices()
    print(f"Model successfully loaded. Supported classes: {list(class_indices.values())}")

    # 2. Test Image Validation & Preprocessing on 3 Views
    samples_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "samples")
    uploads_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "uploads")
    os.makedirs(uploads_dir, exist_ok=True)

    views = {
        "front": os.path.join(samples_dir, "sample_caries_front.jpg"),
        "left": os.path.join(samples_dir, "sample_gingivitis_left.jpg"),
        "right": os.path.join(samples_dir, "sample_calculus_right.jpg"),
    }

    view_results = {}

    for v_name, f_path in views.items():
        print(f"\n[2/5] Testing validation & inference for {v_name.upper()} view ({os.path.basename(f_path)})...")
        with open(f_path, "rb") as f:
            f_bytes = f.read()

        val_res = validate_image_file(f_bytes, os.path.basename(f_path))
        print(f"  Validation passed: format={val_res['format']}, res={val_res['width']}x{val_res['height']}, clarity={val_res['clarity_score']}")

        tensor, orig_img, q_info = preprocess_dental_image(f_bytes)
        print(f"  Preprocessed tensor shape: {tensor.shape}")

        # Run inference
        inf_res = run_inference(
            tensor=tensor,
            orig_img=orig_img,
            view_name=v_name,
            output_dir=uploads_dir
        )
        print(f"  Prediction: {inf_res['predicted_name']} ({inf_res['confidence_percentage']}%)")
        print(f"  Inconclusive: {inf_res['is_inconclusive']}")
        print(f"  Bounding boxes found: {len(inf_res['bounding_boxes'])}")
        if inf_res['annotated_image']:
            print(f"  Annotated visualization: {inf_res['annotated_image']}")

        view_results[v_name] = inf_res

    # 3. Test Multi-View Consolidation
    print("\n[3/5] Consolidating findings across all 3 views...")
    consolidated = process_three_views(view_results)
    print(f"  Overall Status: {consolidated['overall_status']}")
    print(f"  Urgency Level: {consolidated['urgency_level']}")
    print(f"  Summary: {consolidated['summary']}")
    print(f"  Combined Distinct Diseases: {len(consolidated['combined_diseases'])}")
    for d in consolidated['combined_diseases']:
        print(f"    - {d['disease_name']} ({d['severity']}): {d['confidence_percentage']}% across views: {d['affected_views']}")

    # 4. Test Report Generation
    print("\n[4/5] Generating Clinical Screening Report...")
    patient = {
        "name": "Jane Doe",
        "patient_id": "PT-2026-9042",
        "age": 34,
        "gender": "Female",
        "notes": "Patient reports mild sensitivity in upper right quadrant during mastication."
    }
    report = generate_screening_report(patient, consolidated)
    print(f"  Report ID: {report['report_id']}")
    print(f"  Scan Date: {report['scan_date']}")
    print(f"  Disclaimer Included: {len(report['disclaimer']) > 0}")
    print(f"  Recommendations Count: {len(report['clinical_recommendations'])}")

    print("\n[5/5] Pipeline test completed with 100% success!")
    print("==================================================")

if __name__ == "__main__":
    main()

