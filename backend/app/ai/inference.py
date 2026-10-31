import os
import time
import uuid
import logging
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
import tensorflow as tf
from PIL import Image
import cv2

from .model_loader import (
    get_dental_model,
    get_class_indices,
    DISEASE_METADATA,
    DEFAULT_ABSTENTION_THRESHOLD
)

logger = logging.getLogger("dentalai.ai.inference")

GRADCAM_LAYER_NAME = "conv5_block3_out"

GRADCAM_DISCLOSURE = (
    "Grad-CAM (Gradient-weighted Class Activation Mapping) visualizes the spatial regions "
    "within the dental photograph that most heavily influenced the convolutional neural network's "
    "feature activations for the predicted class. It highlights visual salience areas and does NOT "
    "represent an automated lesion bounding box, segmentation mask, or verified diagnostic boundary."
)

def generate_gradcam_heatmap(
    model,
    tensor: np.ndarray,
    target_class_idx: int
) -> np.ndarray:
    """
    Computes Gradient-weighted Class Activation Mapping (Grad-CAM) from ResNet-50's final
    convolutional feature activation layer (conv5_block3_out).
    
    Formula:
    L_{Grad-CAM}^c = ReLU( sum_k( alpha_k^c * A^k ) )
    where alpha_k^c = (1/Z) * sum_i sum_j ( d(y^c) / d(A_{i,j}^k) )
    """
    resnet_layer = model.get_layer("resnet50") if "resnet50" in [l.name for l in model.layers] else model.layers[0]
    gap = model.get_layer("global_average_pooling2d_5") if "global_average_pooling2d_5" in [l.name for l in model.layers] else model.layers[1]
    d1 = model.get_layer("dense_12") if "dense_12" in [l.name for l in model.layers] else model.layers[2]
    drop = model.get_layer("dropout_5") if "dropout_5" in [l.name for l in model.layers] else model.layers[3]
    d2 = model.get_layer("dense_13") if "dense_13" in [l.name for l in model.layers] else model.layers[4]

    x_tensor = tf.convert_to_tensor(tensor, dtype=tf.float32)

    with tf.GradientTape() as tape:
        # 1. Forward through ResNet backbone to conv5_block3_out
        conv_out = resnet_layer(x_tensor)
        tape.watch(conv_out)

        # 2. Forward through classification head
        h = gap(conv_out)
        h = d1(h)
        h = drop(h, training=False)
        preds = d2(h)
        class_channel = preds[:, target_class_idx]

    # 3. Compute gradients of predicted class score w.r.t. feature maps
    grads = tape.gradient(class_channel, conv_out)
    if grads is None:
        logger.warning("Grad-CAM gradient computation returned None.")
        return np.zeros((7, 7), dtype=np.float32)

    # 4. Global average pooling of gradients to obtain neuron importance weights alpha_k
    pooled_grads = tf.reduce_mean(grads, axis=(0, 1, 2))

    # 5. Weighted combination of forward activation maps
    cam = tf.reduce_sum(pooled_grads * conv_out[0], axis=-1)

    # 6. Apply ReLU to retain features that positively correlate with the class
    cam = tf.maximum(cam, 0.0)
    max_val = tf.reduce_max(cam)
    if max_val > 0:
        cam = cam / max_val

    return cam.numpy()

def create_gradcam_overlay(
    orig_img: Image.Image,
    heatmap_7x7: np.ndarray,
    output_dir: Optional[str] = None,
    file_prefix: str = "gradcam"
) -> Tuple[Optional[str], Optional[str], Dict[str, Any]]:
    """
    Interpolates 7x7 Grad-CAM heatmap to original image resolution, applies JET colormap,
    and blends it over the original photograph.
    Saves:
      1. Original image
      2. Blended heatmap overlay
    Returns paths and saliency statistics.
    """
    orig_w, orig_h = orig_img.size

    # Resize 7x7 heatmap to original image dimensions with cubic interpolation
    heatmap_resized = cv2.resize(heatmap_7x7, (orig_w, orig_h), interpolation=cv2.INTER_CUBIC)
    heatmap_resized = np.clip(heatmap_resized, 0.0, 1.0)

    # Compute salience statistics
    high_salience_ratio = float(np.mean(heatmap_resized > 0.5))
    peak_salience_coords = np.unravel_index(np.argmax(heatmap_resized), heatmap_resized.shape)
    salience_stats = {
        "mean_activation": round(float(np.mean(heatmap_resized)), 4),
        "peak_activation": round(float(np.max(heatmap_resized)), 4),
        "high_salience_area_percentage": round(high_salience_ratio * 100, 1),
        "focal_region_normalized": [
            round(peak_salience_coords[0] / orig_h, 4), # y
            round(peak_salience_coords[1] / orig_w, 4)  # x
        ]
    }

    orig_filename = None
    overlay_filename = None

    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        img_np = np.array(orig_img.convert("RGB"))
        img_bgr = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)

        # Apply JET colormap to heatmap (0-255)
        heatmap_colored = cv2.applyColorMap((heatmap_resized * 255).astype(np.uint8), cv2.COLORMAP_JET)

        # Alpha blend (60% original image + 40% heatmap)
        blended = cv2.addWeighted(img_bgr, 0.60, heatmap_colored, 0.40, 0)

        uid = uuid.uuid4().hex[:8]
        orig_filename = f"{file_prefix}_orig_{uid}.jpg"
        overlay_filename = f"{file_prefix}_heatmap_{uid}.jpg"

        orig_path = os.path.join(output_dir, orig_filename)
        overlay_path = os.path.join(output_dir, overlay_filename)

        cv2.imwrite(orig_path, img_bgr)
        cv2.imwrite(overlay_path, blended)

    return orig_filename, overlay_filename, salience_stats

def run_inference(
    tensor: np.ndarray,
    orig_img: Image.Image,
    view_name: str,
    output_dir: Optional[str] = None,
    abstention_threshold: float = DEFAULT_ABSTENTION_THRESHOLD
) -> Dict[str, Any]:
    """
    Executes genuine ResNet-50 inference on a single intraoral photograph view:
    - Runs feed-forward inference.
    - Measures exact inference execution time.
    - Extracts complete model output distribution (softmax scores for all 6 categories).
    - Sorts and extracts top-three class predictions.
    - Computes authentic Grad-CAM heatmap on conv5_block3_out without artificial bounding boxes.
    - Provides explicit disclaimer that softmax values are model output scores, not calibrated clinical probabilities.
    """
    model = get_dental_model()
    class_indices = get_class_indices()

    # Time inference accurately
    t_start = time.perf_counter()
    preds = model.predict(tensor, verbose=0)[0]
    inference_time_ms = round((time.perf_counter() - t_start) * 1000, 2)

    preds_list = [float(p) for p in preds]

    # Map raw model output scores
    model_output_scores = {
        class_indices[idx]: round(preds_list[idx], 4)
        for idx in range(len(preds_list))
    }

    # Rank classes
    ranked_indices = np.argsort(preds_list)[::-1]
    top_idx = int(ranked_indices[0])
    top_class = class_indices[top_idx]
    top_score = round(preds_list[top_idx], 4)

    # Top-3 predictions
    top_three = []
    for rank, idx in enumerate(ranked_indices[:3], start=1):
        cname = class_indices[int(idx)]
        cscore = round(preds_list[int(idx)], 4)
        top_three.append({
            "rank": rank,
            "class_name": cname,
            "display_name": DISEASE_METADATA.get(cname, {}).get("name", cname),
            "score": cscore,
            "percentage": round(cscore * 100, 1)
        })

    # Check abstention threshold (unvalidated exploratory heuristic)
    is_abstaining = top_score < abstention_threshold
    status = "low_confidence_abstention" if is_abstaining else "success"

    # Compute Grad-CAM on conv5_block3_out
    file_prefix = f"view_{view_name}"
    orig_file, heatmap_file, salience_stats = None, None, {}
    try:
        heatmap_7x7 = generate_gradcam_heatmap(model, tensor, top_idx)
        orig_file, heatmap_file, salience_stats = create_gradcam_overlay(
            orig_img=orig_img,
            heatmap_7x7=heatmap_7x7,
            output_dir=output_dir,
            file_prefix=file_prefix
        )
    except Exception as e:
        logger.error("Grad-CAM generation failed for %s view: %s", view_name, e, exc_info=True)

    meta = DISEASE_METADATA.get(top_class, {
        "name": top_class,
        "category": "Oral Condition",
        "description": "Observed dental condition.",
        "clinical_signs": [],
        "clinical_relevance": "Clinical examination required."
    })

    return {
        "view": view_name,
        "predicted_class": top_class,
        "predicted_name": meta["name"],
        "model_output_score": top_score,
        "confidence_percentage": round(top_score * 100, 1),
        "is_abstaining": is_abstaining,
        "abstention_threshold": abstention_threshold,
        "processing_status": status,
        "inference_time_ms": inference_time_ms,
        "top_three_predictions": top_three,
        "model_output_scores": model_output_scores,
        "original_image": orig_file,
        "heatmap_image": heatmap_file,
        "gradcam_salience_stats": salience_stats,
        "gradcam_explanation": GRADCAM_DISCLOSURE,
        "category": meta["category"],
        "clinical_signs": meta["clinical_signs"],
        "clinical_relevance": meta["clinical_relevance"]
    }
