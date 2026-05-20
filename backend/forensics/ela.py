from __future__ import annotations

import io

import numpy as np
from PIL import Image, ImageChops

def run_ela(
    image: Image.Image,
    quality: int = 90,
    scale: int = 15,
    block_size: int = 8,
    error_threshold: float = 25.0,
) -> dict | None:
    
    try:
        if image is None:
            return None

        working = _normalize_to_rgb(image)

        resaved = _resave_jpeg(working, quality)
        if resaved is None:
            return None  
        
        diff_image = ImageChops.difference(working, resaved)
        diff_array = np.array(diff_image, dtype=np.float64)
        mean_error = float(np.mean(diff_array))
        max_error = float(np.max(diff_array))

        scaled_array = np.clip(
            diff_array * scale, 0, 255
        ).astype(np.uint8)

        ela_image = Image.fromarray(scaled_array, mode="RGB")
        
        block_result = _analyze_blocks(
            diff_array, block_size, error_threshold
        )

        return {
            "ela_image": ela_image,
            "mean_error": round(mean_error, 4),
            "max_error": round(max_error, 4),
            "suspicious_blocks": block_result["suspicious"],
            "total_blocks": block_result["total"],
            "suspicious_ratio": block_result["ratio"],
            "error": None,
        }

    except Exception as exc:
        return None

def ela_to_numpy(ela_result: dict) -> np.ndarray | None:

    try:
        if ela_result is None:
            return None

        ela_image = ela_result.get("ela_image")
        if ela_image is None:
            return None

        return np.array(ela_image, dtype=np.uint8)

    except (TypeError, AttributeError, ValueError):
        return None

def _normalize_to_rgb(image: Image.Image) -> Image.Image:
    
    if image.mode == "RGB":
        return image

    if image.mode == "RGBA":
        background = Image.new("RGB", image.size, (255, 255, 255))
        background.paste(image, mask=image.split()[3])  
    return image.convert("RGB")


def _resave_jpeg(
    image: Image.Image,
    quality: int,
) -> Image.Image | None:
    
    try:
        buffer = io.BytesIO()

        image.save(buffer, format="JPEG", quality=quality)
        buffer.seek(0)

        resaved = Image.open(buffer)
        resaved.load() 

        return resaved.convert("RGB")

    except (OSError, ValueError, IOError):
        return None


def _analyze_blocks(
    diff_array: np.ndarray,
    block_size: int,
    threshold: float,
) -> dict:
    
    height, width = diff_array.shape[:2]

    if height < block_size or width < block_size:
        return {"suspicious": 0, "total": 0, "ratio": 0.0}

    rows = height // block_size
    cols = width // block_size

    total_blocks = rows * cols
    suspicious_count = 0

    for r in range(rows):
        for c in range(cols):
            y_start = r * block_size
            y_end = y_start + block_size
            x_start = c * block_size
            x_end = x_start + block_size

            block = diff_array[y_start:y_end, x_start:x_end]
            block_mean = float(np.mean(block))

            if block_mean > threshold:
                suspicious_count += 1

    ratio = (
        round(suspicious_count / total_blocks, 4)
        if total_blocks > 0
        else 0.0
    )

    return {
        "suspicious": suspicious_count,
        "total": total_blocks,
        "ratio": ratio,
    }
