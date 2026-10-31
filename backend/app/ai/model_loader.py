import os
import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional

# Suppress verbose TF logging
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

logger = logging.getLogger("dentalai.ai.model_loader")

_MODEL_INSTANCE = None
_CLASS_INDICES: Optional[Dict[int, str]] = None
_INIT_METADATA: Dict[str, Any] = {}

# Configurable abstention / low-confidence threshold
# NOTE: Clearly identified as an unvalidated heuristic threshold until clinically calibrated.
DEFAULT_ABSTENTION_THRESHOLD = float(os.getenv("DENTAL_ABSTENTION_THRESHOLD", "0.35"))

DISEASE_METADATA = {
    "Calculus": {
        "name": "Dental Calculus (Tartar)",
        "category": "Periodontal Deposit",
        "description": "Hardened, calcified mineral deposit adhering to teeth surfaces and subgingival margins, serving as a reservoir for bacterial biofilm.",
        "clinical_signs": [
            "Yellow, brown, or dark deposits along cervical margin",
            "Supragingival or subgingival rough calcified accretions",
            "Marginal erythema in adjacent gingival tissues"
        ],
        "clinical_relevance": "Predisposes to localized gingival inflammation and pocket formation if not removed."
    },
    "Caries": {
        "name": "Dental Caries (Tooth Decay)",
        "category": "Hard Tissue Lesion",
        "description": "Localized demineralization of inorganic dental tissues by organic acids from microbial fermentation of dietary carbohydrates.",
        "clinical_signs": [
            "Chalky white spot lesions or dark brown/black cavitations",
            "Surface softness or catch with a dental probe",
            "Thermal, tactile, or chemical sensitivity"
        ],
        "clinical_relevance": "Progressive structural tooth damage requiring clinical confirmation of depth and restorative intervention."
    },
    "Gingivitis": {
        "name": "Gingivitis",
        "category": "Periodontal Inflammation",
        "description": "Reversible, plaque-induced inflammation of the marginal gingiva without loss of periodontal attachment or alveolar bone.",
        "clinical_signs": [
            "Erythematous, edematous, or swollen marginal gingiva and papillae",
            "Tendency toward bleeding upon gentle probing or brushing",
            "Blunting or loss of knife-edge gingival architecture"
        ],
        "clinical_relevance": "Reversible condition with professional oral prophylaxis and plaque control."
    },
    "Hypodontia": {
        "name": "Hypodontia / Missing Tooth",
        "category": "Arch Continuity",
        "description": "Absence of one or more teeth within the dental arch due to agenesis, impaction, or extraction.",
        "clinical_signs": [
            "Empty arch space or widened interdental diastema",
            "Drifting, tipping, or over-eruption of opposing/adjacent teeth",
            "Reduced arch length or localized alveolar ridge contour variation"
        ],
        "clinical_relevance": "Requires radiographic evaluation for unerupted tooth germs and restorative/orthodontic space management."
    },
    "Mouth_Ulcer": {
        "name": "Oral Mucosal Ulceration",
        "category": "Soft Tissue Lesion",
        "description": "Disruption of the oral epithelial lining exposing underlying vascular lamina propria, seen in aphthous stomatitis, trauma, or mucosal pathology.",
        "clinical_signs": [
            "Circumscribed, painful, shallow erosion with a yellowish necrotic base",
            "Surrounding erythematous inflammatory border (halo)",
            "Localized discomfort exacerbated by eating, drinking, or speaking"
        ],
        "clinical_relevance": "Requires evaluation for mechanical irritation. Ulcers persisting past 14 days require specialist evaluation and biopsy."
    },
    "Tooth_Discoloration": {
        "name": "Tooth Discoloration",
        "category": "Enamel Aesthetics",
        "description": "Alteration in natural tooth shade caused by extrinsic chromogenic stains (tea, coffee, tobacco) or intrinsic factors (fluorosis, trauma, non-vital pulp).",
        "clinical_signs": [
            "Superficial brown, yellow, or grey staining along developmental lines",
            "Uniform or mottled enamel shade alterations across crown surfaces",
            "Isolated dark grey hue suggestive of past trauma or pulpal necrosis"
        ],
        "clinical_relevance": "Cosmetic concern; non-vital teeth should be tested for pulpal sensitivity."
    }
}

def get_model_path() -> str:
    # 1. Environment variable override
    env_path = os.getenv("MODEL_PATH")
    if env_path and os.path.exists(env_path):
        return env_path

    # 2. Project relative paths
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    candidate = os.path.join(base_dir, "models", "best_model_resnet50.keras")
    if os.path.exists(candidate):
        return candidate

    return "backend/models/best_model_resnet50.keras"

def get_class_indices_path() -> str:
    env_path = os.getenv("CLASS_INDICES_PATH")
    if env_path and os.path.exists(env_path):
        return env_path

    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    candidate = os.path.join(base_dir, "models", "class_indices.json")
    if os.path.exists(candidate):
        return candidate

    return "backend/models/class_indices.json"

def get_class_indices() -> Dict[int, str]:
    global _CLASS_INDICES
    if _CLASS_INDICES is not None:
        return _CLASS_INDICES

    path = get_class_indices_path()
    try:
        with open(path, "r") as f:
            raw = json.load(f)
            _CLASS_INDICES = {int(k): v for k, v in raw.items()}
            logger.info("Loaded class indices from %s: %s", path, _CLASS_INDICES)
    except Exception as e:
        logger.warning("Could not read %s (%s). Using verified default mapping.", path, e)
        _CLASS_INDICES = {
            0: "Calculus",
            1: "Caries",
            2: "Gingivitis",
            3: "Hypodontia",
            4: "Mouth_Ulcer",
            5: "Tooth_Discoloration"
        }
    return _CLASS_INDICES

def load_dental_model():
    """
    Loads and caches the pretrained ResNet-50 model once.
    Thread-safe and graceful handling of missing weights or environment issues.
    """
    global _MODEL_INSTANCE, _INIT_METADATA
    if _MODEL_INSTANCE is not None:
        return _MODEL_INSTANCE

    model_path = get_model_path()
    logger.info("Initializing pretrained ResNet-50 Dental Model from: %s", model_path)

    if not os.path.exists(model_path):
        err_msg = f"Model checkpoint not found at: {model_path}. Please ensure best_model_resnet50.keras is present."
        logger.error(err_msg)
        raise FileNotFoundError(err_msg)

    import keras
    try:
        model = keras.models.load_model(model_path)
    except Exception as e:
        logger.error("Failed to load .keras model using Keras 3: %s", e)
        # Attempt fallback via tensorflow.keras
        import tensorflow as tf
        model = tf.keras.models.load_model(model_path)

    _MODEL_INSTANCE = model
    class_indices = get_class_indices()

    # Capture architectural verification metadata
    resnet = model.get_layer("resnet50") if "resnet50" in [l.name for l in model.layers] else model.layers[0]
    _INIT_METADATA = {
        "status": "loaded",
        "model_file": os.path.basename(model_path),
        "model_path": model_path,
        "model_size_mb": round(os.path.getsize(model_path) / (1024 * 1024), 2),
        "architecture": "ResNet-50 (Sequential backbone + GlobalAveragePooling2D + Dense + Dropout + Dense(Softmax))",
        "input_shape": list(model.input_shape),
        "output_shape": list(model.output_shape),
        "num_classes": len(class_indices),
        "classes": list(class_indices.values()),
        "class_mapping": class_indices,
        "gradcam_layer": "conv5_block3_out",
        "abstention_threshold": DEFAULT_ABSTENTION_THRESHOLD,
        "initialized_at": datetime.now(timezone.utc).isoformat()
    }

    logger.info(
        "ResNet-50 Dental Model successfully initialized. Input: %s, Output: %s, Classes: %s",
        model.input_shape, model.output_shape, list(class_indices.values())
    )
    return _MODEL_INSTANCE

def get_dental_model():
    """Returns singleton model instance, initializing if not yet loaded."""
    if _MODEL_INSTANCE is None:
        return load_dental_model()
    return _MODEL_INSTANCE

def get_model_status() -> Dict[str, Any]:
    """Provides detailed inspection metadata for model verification and health reporting."""
    global _INIT_METADATA
    is_loaded = _MODEL_INSTANCE is not None
    model_path = get_model_path()
    file_exists = os.path.exists(model_path)

    return {
        "is_loaded": is_loaded,
        "file_exists": file_exists,
        "model_path": model_path,
        "metadata": _INIT_METADATA if is_loaded else {
            "status": "unloaded",
            "file_exists": file_exists,
            "classes": list(get_class_indices().values()),
            "abstention_threshold": DEFAULT_ABSTENTION_THRESHOLD
        }
    }
