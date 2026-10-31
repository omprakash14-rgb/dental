import logging
from typing import Dict, Any, List

logger = logging.getLogger("dentalai.ai.prediction_processor")

MULTI_VIEW_DISCLAIMER = (
    "MULTI-VIEW NOTICE: This combined report provides an algorithmic compilation of independent single-image "
    "ResNet-50 model inferences across the three photographic views. The underlying model was trained on individual "
    "images and has NOT been independently validated as a cohesive multi-view diagnostic system. "
    "Clinicians must evaluate each view's visual findings independently."
)

def process_three_views(view_results: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    """
    Summarizes individual inferences across Front, Left, and Right dental photographs
    without pretending the model is an independently validated multi-view clinical diagnostic system.
    """
    views_present = list(view_results.keys())
    abstained_views = []
    per_view_findings = {}
    total_inference_time_ms = 0.0

    # Collect unique conditions detected as top-1 across views
    condition_summary: Dict[str, Dict[str, Any]] = {}

    for view_name, res in view_results.items():
        per_view_findings[view_name] = res
        total_inference_time_ms += res.get("inference_time_ms", 0.0)

        if res.get("is_abstaining", False):
            abstained_views.append(view_name)

        pred_class = res.get("predicted_class")
        score = res.get("model_output_score", 0.0)

        if pred_class:
            if pred_class not in condition_summary:
                condition_summary[pred_class] = {
                    "disease_key": pred_class,
                    "disease_name": res.get("predicted_name", pred_class),
                    "category": res.get("category", "General Oral"),
                    "affected_views": [view_name],
                    "scores_by_view": {view_name: score},
                    "peak_score": score,
                    "clinical_signs": res.get("clinical_signs", []),
                    "clinical_relevance": res.get("clinical_relevance", "")
                }
            else:
                entry = condition_summary[pred_class]
                entry["affected_views"].append(view_name)
                entry["scores_by_view"][view_name] = score
                if score > entry["peak_score"]:
                    entry["peak_score"] = score

    # Convert condition summary to sorted list
    conditions_list = list(condition_summary.values())
    conditions_list.sort(key=lambda x: x["peak_score"], reverse=True)

    # Compile descriptive overall status
    if len(abstained_views) == len(views_present) and len(views_present) > 0:
        overall_status = "Inconclusive / Low Model Confidence Across Views"
        triage_recommendation = "Full Clinical Examination Required"
        narrative = (
            "Model scores across all uploaded photographic angles fell below the configurable confidence threshold. "
            "No diagnostic inference could be reliably drawn from these photographs."
        )
    elif len(conditions_list) > 0:
        top_condition = conditions_list[0]
        detected_names = [c["disease_name"] for c in conditions_list]
        overall_status = f"Indications of {', '.join(detected_names)}"
        triage_recommendation = "Clinical Validation & Radiographic Review Advised"
        narrative = (
            f"Preliminary model feature activations indicate characteristics consistent with {top_condition['disease_name']} "
            f"on {', '.join(top_condition['affected_views'])} view(s). "
            f"Model output score peaked at {round(top_condition['peak_score'] * 100, 1)}%. "
            "Direct chairside tactile and radiographic inspection by a dentist is required."
        )
    else:
        overall_status = "No Salient Abnormalities Detected"
        triage_recommendation = "Routine Preventative Examination"
        narrative = "No primary conditions met the activation criteria within the photographic angles provided."

    return {
        "overall_status": overall_status,
        "triage_recommendation": triage_recommendation,
        "narrative": narrative,
        "views_evaluated": views_present,
        "abstained_views": abstained_views,
        "has_abstained_views": len(abstained_views) > 0,
        "total_inference_time_ms": round(total_inference_time_ms, 2),
        "conditions_detected": conditions_list,
        "per_view_findings": per_view_findings,
        "multi_view_notice": MULTI_VIEW_DISCLAIMER
    }
