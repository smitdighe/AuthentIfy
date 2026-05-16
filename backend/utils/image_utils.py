# ============================================================
# utils/image_utils.py — AuthentIfy Backend
# Project: AuthentIfy — "Verify before you trust."
# Role   : Centralized image conversion and preprocessing
#          utilities for the document forensics pipeline.
#
# This is a PURE utility module — no analysis logic, no
# scoring, no Flask routes. Only image format conversions
# and preprocessing operations.
#
# Consumers: forensics/ela.py, forensics/noise_analysis.py,
#            services/ela_analyzer.py, services/ocr_extractor.py
#
# KEY CONVENTION:
#   - OpenCV  uses BGR channel order
#   - Pillow  uses RGB channel order
#   - PyMuPDF uses RGB channel order (or RGBA)
#   Every conversion between libraries MUST swap channels.
# ============================================================

from __future__ import annotations

import os

import cv2
import numpy as np
from PIL import Image


# ── PyMuPDF Pixmap Conversions ────────────────────────────────


def pixmap_to_pil(pixmap) -> Image.Image | None:
    """Convert a PyMuPDF fitz.Pixmap to a PIL Image (RGB).

    Handles both RGB (n=3) and RGBA (n=4) pixmaps.
    RGBA pixmaps are composited onto a white background
    before conversion.

    Args:
        pixmap: A fitz.Pixmap object from PyMuPDF page rendering.

    Returns:
        PIL Image in RGB mode, or None on failure.
    """
    try:
        # Extract raw pixel bytes and dimensions from the pixmap
        samples = pixmap.n  # Number of color channels

        if samples == 4:
            # RGBA — create PIL image then composite onto white
            img = Image.frombytes(
                "RGBA",
                (pixmap.width, pixmap.height),
                pixmap.samples,
            )
            # Flatten alpha onto white background
            background = Image.new("RGB", img.size, (255, 255, 255))
            background.paste(img, mask=img.split()[3])
            return background

        if samples == 3:
            # RGB — direct conversion, no channel swap needed
            # (PyMuPDF and Pillow both use RGB order)
            return Image.frombytes(
                "RGB",
                (pixmap.width, pixmap.height),
                pixmap.samples,
            )

        # Unexpected channel count (e.g., grayscale pixmap)
        return None

    except (ValueError, AttributeError, RuntimeError):
        return None


def pixmap_to_numpy(pixmap) -> np.ndarray | None:
    """Convert a PyMuPDF fitz.Pixmap to a NumPy array (BGR).

    First converts to PIL (RGB), then swaps to BGR because
    OpenCV expects BGR channel order for all its operations.

    Args:
        pixmap: A fitz.Pixmap object from PyMuPDF page rendering.

    Returns:
        NumPy ndarray in BGR format (uint8), or None on failure.
    """
    pil_img = pixmap_to_pil(pixmap)
    if pil_img is None:
        return None

    return pil_to_numpy(pil_img)


# ── PIL ↔ NumPy Conversions ──────────────────────────────────


def pil_to_numpy(image: Image.Image) -> np.ndarray | None:
    """Convert a PIL Image (RGB) to a NumPy array (BGR).

    Channel swap is required because:
      - Pillow stores pixels as R, G, B
      - OpenCV expects pixels as B, G, R
    Without this swap, reds appear blue and vice versa.

    Args:
        image: PIL Image in RGB mode.

    Returns:
        NumPy ndarray in BGR format (uint8), or None on failure.
    """
    try:
        if image is None:
            return None

        # Ensure the image is in RGB mode before conversion
        if image.mode != "RGB":
            image = image.convert("RGB")

        rgb_array = np.array(image, dtype=np.uint8)

        # Swap R↔B channels: RGB → BGR for OpenCV compatibility
        bgr_array = cv2.cvtColor(rgb_array, cv2.COLOR_RGB2BGR)
        return bgr_array

    except (ValueError, TypeError, cv2.error):
        return None


def numpy_to_pil(array: np.ndarray) -> Image.Image | None:
    """Convert a NumPy array (BGR) to a PIL Image (RGB).

    Channel swap is required because:
      - OpenCV stores pixels as B, G, R
      - Pillow expects pixels as R, G, B
    Without this swap, colors render incorrectly.

    Args:
        array: NumPy ndarray in BGR format (uint8).

    Returns:
        PIL Image in RGB mode, or None on failure.
    """
    try:
        if array is None or array.size == 0:
            return None

        # Swap B↔R channels: BGR → RGB for Pillow compatibility
        rgb_array = cv2.cvtColor(array, cv2.COLOR_BGR2RGB)
        return Image.fromarray(rgb_array)

    except (ValueError, TypeError, cv2.error):
        return None


# ── Disk I/O ──────────────────────────────────────────────────


def save_image(image: Image.Image, path: str) -> bool:
    """Save a PIL Image to disk at the given path.

    Creates parent directories if they do not exist.
    File format is inferred from the path extension.

    Args:
        image: PIL Image to save.
        path:  Destination file path (e.g., "processed/page_0.png").

    Returns:
        True on success, False on failure.
    """
    try:
        parent_dir = os.path.dirname(path)
        if parent_dir:
            os.makedirs(parent_dir, exist_ok=True)

        image.save(path)
        return True

    except (OSError, ValueError, AttributeError):
        return False


def load_image_pil(path: str) -> Image.Image | None:
    """Load an image from disk as a PIL Image in RGB mode.

    Args:
        path: File path to the image.

    Returns:
        PIL Image in RGB mode, or None if the file is missing
        or corrupt.
    """
    if not os.path.isfile(path):
        return None

    try:
        img = Image.open(path)
        img.load()  # Force full read to catch truncated files

        # Normalize to RGB — handles grayscale, RGBA, palette, etc.
        if img.mode != "RGB":
            img = img.convert("RGB")

        return img

    except (OSError, ValueError, SyntaxError):
        # SyntaxError: Pillow raises this on severely corrupt files
        return None


def load_image_numpy(path: str) -> np.ndarray | None:
    """Load an image from disk as an OpenCV BGR NumPy array.

    Uses cv2.imread which natively loads in BGR order.

    Args:
        path: File path to the image.

    Returns:
        NumPy ndarray in BGR format (uint8), or None on failure.
    """
    if not os.path.isfile(path):
        return None

    try:
        # cv2.IMREAD_COLOR forces 3-channel BGR output
        img = cv2.imread(path, cv2.IMREAD_COLOR)
        if img is None or img.size == 0:
            return None
        return img

    except cv2.error:
        return None


# ── Preprocessing ─────────────────────────────────────────────


def to_grayscale(image: np.ndarray) -> np.ndarray | None:
    """Convert a BGR NumPy array to single-channel grayscale.

    Uses OpenCV's luminosity-weighted conversion:
      gray = 0.114*B + 0.587*G + 0.299*R

    Args:
        image: NumPy ndarray in BGR format.

    Returns:
        Single-channel grayscale ndarray, or None on failure.
    """
    try:
        if image is None or image.size == 0:
            return None

        # Already grayscale — return as-is
        if len(image.shape) == 2:
            return image

        return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    except (cv2.error, ValueError):
        return None


def resize_to_width(
    image: Image.Image, target_width: int
) -> Image.Image | None:
    """Resize a PIL Image to a target width, preserving aspect ratio.

    Useful for normalizing scanned pages to a consistent width
    before forensic comparison.

    Args:
        image:        PIL Image to resize.
        target_width: Desired width in pixels (must be > 0).

    Returns:
        Resized PIL Image, or None on failure or invalid input.
    """
    try:
        if target_width <= 0:
            return None

        original_width, original_height = image.size

        if original_width <= 0 or original_height <= 0:
            return None

        # Calculate new height to preserve aspect ratio
        ratio = target_width / original_width
        target_height = int(original_height * ratio)

        if target_height <= 0:
            return None  # Edge case: extreme downscale

        return image.resize(
            (target_width, target_height),
            Image.LANCZOS,  # High-quality downsampling filter
        )

    except (ValueError, TypeError, AttributeError):
        return None
