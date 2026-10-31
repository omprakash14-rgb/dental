"""
DentalAI - AI Pipeline Module
Provides model loading, preprocessing, inference, prediction processing, and clinical screening reports.
"""
from .model_loader import (
    get_dental_model,
    get_class_indices,
    get_model_status,
    load_dental_model,
    DISEASE_METADATA,
    DEFAULT_ABSTENTION_THRESHOLD
)
from .image_preprocessing import preprocess_dental_image, validate_image_file
from .inference import (
    run_inference,
    generate_gradcam_heatmap,
    create_gradcam_overlay,
    GRADCAM_LAYER_NAME,
    GRADCAM_DISCLOSURE
)
from .prediction_processor import process_three_views
from .report_generator import generate_screening_report, PRIMARY_SAFETY_NOTICE, CLINICAL_DISCLAIMER

__all__ = [
    "get_dental_model",
    "get_class_indices",
    "get_model_status",
    "load_dental_model",
    "DISEASE_METADATA",
    "DEFAULT_ABSTENTION_THRESHOLD",
    "preprocess_dental_image",
    "validate_image_file",
    "run_inference",
    "generate_gradcam_heatmap",
    "create_gradcam_overlay",
    "GRADCAM_LAYER_NAME",
    "GRADCAM_DISCLOSURE",
    "process_three_views",
    "generate_screening_report",
    "PRIMARY_SAFETY_NOTICE",
    "CLINICAL_DISCLAIMER"
]
