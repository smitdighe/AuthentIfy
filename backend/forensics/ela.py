# ============================================================
# forensics/ela.py — AuthentIfy Backend
# Project: AuthentIfy — "Verify before you trust."
# Role   : Pure Error Level Analysis (ELA) algorithm.
#
# This is a PURE ALGORITHM FILE — no Flask, no Config, no
# file I/O, no scoring. Only computation. All parameters
# are passed in, nothing is hardcoded.
#
# Called by: services/ela_analyzer.py
# Input   : PIL Image object (one rendered page of a PDF)
# Output  : Structured dict with ELA metrics + ELA image
# ============================================================

from __future__ import annotations

import io

import numpy as np
from PIL import Image, ImageChops


# ── Main ELA Entry Point ─────────────────────────────────────


def run_ela(
    image: Image.Image,
    quality: int = 90,
    scale: int = 15,
    block_size: int = 8,
    error_threshold: float = 25.0,
) -> dict | None:
    """Perform Error Level Analysis on a single image.

    Error Level Analysis (ELA) detects image manipulation by
    exploiting JPEG compression artifacts:

        1. A JPEG image is re-saved at a known quality level.
        2. The absolute pixel difference between the original
           and the re-saved version is computed.
        3. In an unmodified image, this difference (the "error
           level") is roughly uniform — every region has been
           through the same number of compression cycles.
        4. In a tampered image, edited regions were compressed
           a different number of times, producing error levels
           that DIFFER from the surrounding untouched areas.
        5. The difference image is amplified by a scale factor
           so anomalies become visible to the human eye.
        6. The image is divided into a grid of blocks, and
           blocks with abnormally high mean error are flagged.

    Args:
        image:
            PIL Image object (RGB preferred). Grayscale and
            RGBA inputs are automatically converted to RGB.
        quality:
            JPEG re-save quality (1–95). Default 90 provides
            a good balance — high enough to preserve detail,
            low enough to generate measurable error levels.
        scale:
            Amplification factor applied to the raw difference
            image. Default 15 makes subtle anomalies visible
            without saturating genuine regions.
        block_size:
            Side length (in pixels) of the grid blocks used
            for regional analysis. Default 8 matches the JPEG
            DCT block size, making analysis aligned with the
            compression grid.
        error_threshold:
            Mean intensity threshold (0–255) above which a
            block is flagged as suspicious. Default 25.0 is
            calibrated against typical document images — high
            enough to avoid false positives on text edges,
            low enough to catch genuine splicing artifacts.

    Returns:
        dict with keys:
            ela_image         (PIL.Image.Image) — Scaled ELA
            mean_error        (float) — Overall average error
            max_error         (float) — Peak error anywhere
            suspicious_blocks (int)   — High-error block count
            total_blocks      (int)   — Total blocks analyzed
            suspicious_ratio  (float) — suspicious / total
            error             (None|str) — Error on partial fail
        Returns None only on total unrecoverable failure.
    """
    try:
        # ── Validate input ───────────────────────────────────
        if image is None:
            return None

        # ── Normalize to RGB ─────────────────────────────────
        working = _normalize_to_rgb(image)

        # ── STEP 1: Re-save as JPEG at known quality ─────────
        resaved = _resave_jpeg(working, quality)
        if resaved is None:
            return None  # JPEG re-save failed — unrecoverable

        # ── STEP 2: Compute absolute pixel difference ────────
        # |original - resaved| gives the raw error levels
        diff_image = ImageChops.difference(working, resaved)

        # ── STEP 3: Convert to NumPy for numerical analysis ──
        diff_array = np.array(diff_image, dtype=np.float64)

        # ── STEP 4: Compute global ELA metrics ───────────────
        # Mean error: average intensity across all pixels/channels
        mean_error = float(np.mean(diff_array))

        # Max error: single highest pixel-channel value
        max_error = float(np.max(diff_array))

        # ── STEP 5: Scale difference for visibility ──────────
        # Amplify and clamp to [0, 255] for display
        scaled_array = np.clip(
            diff_array * scale, 0, 255
        ).astype(np.uint8)

        ela_image = Image.fromarray(scaled_array, mode="RGB")

        # ── STEP 6: Regional block analysis ──────────────────
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
        # Total failure — return None per contract
        return None


# ── NumPy Conversion Convenience ─────────────────────────────


def ela_to_numpy(ela_result: dict) -> np.ndarray | None:
    """Extract the ELA image from a result dict as a NumPy array.

    Convenience function for downstream modules (e.g.,
    noise_analysis.py) that require NumPy/OpenCV input.

    Args:
        ela_result: dict returned by run_ela().

    Returns:
        np.ndarray (H×W×3, uint8) on success, None on failure.
    """
    try:
        if ela_result is None:
            return None

        ela_image = ela_result.get("ela_image")
        if ela_image is None:
            return None

        return np.array(ela_image, dtype=np.uint8)

    except (TypeError, AttributeError, ValueError):
        return None


# ── Internal Helpers ─────────────────────────────────────────


def _normalize_to_rgb(image: Image.Image) -> Image.Image:
    """Convert any PIL Image mode to RGB.

    Handles:
        - RGBA: strips alpha channel
        - L (grayscale): converts to 3-channel RGB
        - LA: strips alpha, then converts
        - P (palette): converts to RGB
        - Already RGB: returned as-is

    Args:
        image: PIL Image in any mode.

    Returns:
        PIL Image in RGB mode.
    """
    if image.mode == "RGB":
        return image

    if image.mode == "RGBA":
        # Create white background, paste image onto it
        background = Image.new("RGB", image.size, (255, 255, 255))
        background.paste(image, mask=image.split()[3])  # alpha mask
        return background

    # Covers L, LA, P, CMYK, and any other mode
    return image.convert("RGB")


def _resave_jpeg(
    image: Image.Image,
    quality: int,
) -> Image.Image | None:
    """Re-save a PIL Image as JPEG in memory and reload it.

    Uses io.BytesIO to avoid any disk I/O. The re-saved image
    goes through a full JPEG encode/decode cycle, introducing
    the compression artifacts that ELA relies on.

    Args:
        image:   PIL Image in RGB mode.
        quality: JPEG compression quality (1–95).

    Returns:
        Re-saved PIL Image (RGB) on success, None on failure.
    """
    try:
        buffer = io.BytesIO()

        # Encode: PIL → JPEG bytes in memory
        image.save(buffer, format="JPEG", quality=quality)

        # Rewind buffer to the start for reading
        buffer.seek(0)

        # Decode: JPEG bytes → PIL Image
        resaved = Image.open(buffer)
        resaved.load()  # Force full decode before buffer closes

        return resaved.convert("RGB")

    except (OSError, ValueError, IOError):
        return None


def _analyze_blocks(
    diff_array: np.ndarray,
    block_size: int,
    threshold: float,
) -> dict:
    """Divide the ELA difference array into a grid and flag blocks.

    Each block's mean intensity across all channels is computed.
    Blocks with mean intensity above the threshold are flagged
    as suspicious — they indicate regions where error levels
    deviate from the surrounding image, suggesting manipulation.

    Args:
        diff_array:  Raw ELA difference (H×W×3, float64).
        block_size:  Side length of each grid block in pixels.
        threshold:   Mean intensity above this → suspicious.

    Returns:
        dict with keys:
            suspicious (int)   — Number of flagged blocks
            total      (int)   — Total blocks analyzed
            ratio      (float) — suspicious / total (0.0–1.0)
    """
    height, width = diff_array.shape[:2]

    # Guard: image too small for even a single block
    if height < block_size or width < block_size:
        return {"suspicious": 0, "total": 0, "ratio": 0.0}

    # Number of full blocks along each axis
    rows = height // block_size
    cols = width // block_size

    total_blocks = rows * cols
    suspicious_count = 0

    for r in range(rows):
        for c in range(cols):
            # Extract the block region
            y_start = r * block_size
            y_end = y_start + block_size
            x_start = c * block_size
            x_end = x_start + block_size

            block = diff_array[y_start:y_end, x_start:x_end]

            # Mean intensity across all pixels and channels
            block_mean = float(np.mean(block))

            if block_mean > threshold:
                suspicious_count += 1

    # Compute ratio (guard against division by zero)
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
