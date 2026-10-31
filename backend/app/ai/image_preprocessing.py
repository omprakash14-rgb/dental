import io
import logging
from typing import Tuple, Dict, Any
import numpy as np
from PIL import Image
import cv2
from tensorflow.keras.applications.resnet50 import preprocess_input

logger = logging.getLogger("dentalai.ai.preprocessing")

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
MIN_IMAGE_DIMENSION = 150
MAX_IMAGE_DIMENSION = 8192
MAX_FILE_SIZE_BYTES = 25 * 1024 * 1024  # 25 MB
MIN_FILE_SIZE_BYTES = 1024  # 1 KB

def validate_image_file(file_bytes: bytes, filename: str) -> Dict[str, Any]:
    """
    Validates file format, size, dimensions, and visual clarity of uploaded dental photographs.
    Raises ValueError with specific explanation if validation fails.
    """
    # 1. Size checks
    size_bytes = len(file_bytes)
    if size_bytes < MIN_FILE_SIZE_BYTES:
        raise ValueError(f"Uploaded file '{filename}' is too small ({size_bytes} bytes). Corrupted or empty image.")
    if size_bytes > MAX_FILE_SIZE_BYTES:
        raise ValueError(f"Uploaded file '{filename}' exceeds maximum allowed size of 25MB.")

    # 2. Extension check
    ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError(
            f"Unsupported file format '{ext}' for '{filename}'. Supported formats: JPG, JPEG, PNG, WebP."
        )

    # 3. Pillow integrity check
    try:
        img_buffer = io.BytesIO(file_bytes)
        img = Image.open(img_buffer)
        img.verify()
    except Exception as e:
        raise ValueError(f"Invalid or corrupted image file '{filename}': {str(e)}")

    # 4. Dimension checks
    img_buffer.seek(0)
    img = Image.open(img_buffer)
    width, height = img.size

    if width < MIN_IMAGE_DIMENSION or height < MIN_IMAGE_DIMENSION:
        raise ValueError(
            f"Image resolution {width}x{height} for '{filename}' is below minimum required quality ({MIN_IMAGE_DIMENSION}x{MIN_IMAGE_DIMENSION}px)."
        )
    if width > MAX_IMAGE_DIMENSION or height > MAX_IMAGE_DIMENSION:
        raise ValueError(
            f"Image dimensions {width}x{height} for '{filename}' exceed maximum allowed limit of {MAX_IMAGE_DIMENSION}px."
        )

    # 5. Image quality / blur estimation (Laplacian variance)
    np_img = np.array(img.convert('RGB'))
    gray = cv2.cvtColor(np_img, cv2.COLOR_RGB2GRAY)
    laplacian_var = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    is_sharp = laplacian_var > 30.0

    return {
        "filename": filename,
        "format": (img.format or ext.replace(".", "")).upper(),
        "width": width,
        "height": height,
        "size_bytes": size_bytes,
        "clarity_score": round(laplacian_var, 2),
        "is_sharp": is_sharp
    }

def preprocess_dental_image(file_bytes: bytes) -> Tuple[np.ndarray, Image.Image, Dict[str, Any]]:
    """
    Prepares intraoral image for ResNet-50 inference matching the original training configuration:
    - Normalizes color channels to RGB.
    - Resizes to standard model dimension (224, 224) using bilinear interpolation.
    - Applies official ResNet50 preprocess_input (Caffe-style BGR channel reversal and mean centering:
      [103.939, 116.779, 123.68]).
    - Returns:
      - 4D tensor batch: shape (1, 224, 224, 3), float32
      - Original PIL image (for side-by-side rendering & Grad-CAM overlay)
      - Quality metadata
    """
    img = Image.open(io.BytesIO(file_bytes)).convert("RGB")
    width, height = img.size

    # Target 224x224 RGB
    resized_img = img.resize((224, 224), Image.Resampling.BILINEAR)
    img_array = np.array(resized_img, dtype=np.float32)

    # Expand batch dimension before preprocess_input: (1, 224, 224, 3)
    batch_img = np.expand_dims(img_array, axis=0)

    # Official ResNet50 caffe preprocessing: BGR conversion + mean subtraction
    tensor = preprocess_input(batch_img)

    quality_info = {
        "original_width": width,
        "original_height": height,
        "aspect_ratio": round(width / max(height, 1), 2)
    }

    return tensor, img, quality_info
