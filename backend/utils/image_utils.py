from __future__ import annotations

import os

import cv2
import numpy as np
from PIL import Image

def pixmap_to_pil(pixmap) -> Image.Image | None:
    
    try:
        samples = pixmap.n

        if samples == 4:
            img = Image.frombytes(
                "RGBA",
                (pixmap.width, pixmap.height),
                pixmap.samples,
            )
            background = Image.new("RGB", img.size, (255, 255, 255))
            background.paste(img, mask=img.split()[3])
            return background

        if samples == 3:
            return Image.frombytes(
                "RGB",
                (pixmap.width, pixmap.height),
                pixmap.samples,
            )
        return None
    except (ValueError, AttributeError, RuntimeError):
        return None


def pixmap_to_numpy(pixmap) -> np.ndarray | None:

    pil_img = pixmap_to_pil(pixmap)
    if pil_img is None:
        return None
    return pil_to_numpy(pil_img)

def pil_to_numpy(image: Image.Image) -> np.ndarray | None:

    try:
        if image is None:
            return None
        if image.mode != "RGB":
            image = image.convert("RGB")
        rgb_array = np.array(image, dtype=np.uint8)
        bgr_array = cv2.cvtColor(rgb_array, cv2.COLOR_RGB2BGR)
        return bgr_array
    except (ValueError, TypeError, cv2.error):
        return None


def numpy_to_pil(array: np.ndarray) -> Image.Image | None:

    try:
        if array is None or array.size == 0:
            return None
        rgb_array = cv2.cvtColor(array, cv2.COLOR_BGR2RGB)
        return Image.fromarray(rgb_array)
    except (ValueError, TypeError, cv2.error):
        return None

def save_image(image: Image.Image, path: str) -> bool:

    try:
        parent_dir = os.path.dirname(path)
        if parent_dir:
            os.makedirs(parent_dir, exist_ok=True)
        image.save(path)
        return True
    except (OSError, ValueError, AttributeError):
        return False

def load_image_pil(path: str) -> Image.Image | None:

    if not os.path.isfile(path):
        return None
    try:
        img = Image.open(path)
        img.load()
        if img.mode != "RGB":
            img = img.convert("RGB")
        return img
    except (OSError, ValueError, SyntaxError):
        return None

def load_image_numpy(path: str) -> np.ndarray | None:
    
    if not os.path.isfile(path):
        return None
    try:
        img = cv2.imread(path, cv2.IMREAD_COLOR)
        if img is None or img.size == 0:
            return None
        return img
    except cv2.error:
        return None

def to_grayscale(image: np.ndarray) -> np.ndarray | None:

    try:
        if image is None or image.size == 0:
            return None
        if len(image.shape) == 2:
            return image
        return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    except (cv2.error, ValueError):
        return None

def resize_to_width(
    image: Image.Image, target_width: int
) -> Image.Image | None:

    try:
        if target_width <= 0:
            return None
        original_width, original_height = image.size
        if original_width <= 0 or original_height <= 0:
            return None
        ratio = target_width / original_width
        target_height = int(original_height * ratio)
        if target_height <= 0:
            return None
        return image.resize(
            (target_width, target_height),
            Image.LANCZOS,
        )
        
    except (ValueError, TypeError, AttributeError):
        return None
