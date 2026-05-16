# ============================================================
# forensics/noise_analysis.py — AuthentIfy Backend
# Project: AuthentIfy — "Verify before you trust."
# Role   : Noise pattern analysis algorithms for detecting
#          inconsistencies in document page images.
#
# ── Theory of Operation ────────────────────────────────────
# Every image source (camera sensor, scanner CCD, PDF
# renderer) imprints a characteristic noise fingerprint on
# the pixel data.  When a document page is genuine, the
# noise level is uniform across the entire image because
# every pixel passed through the same capture/render
# pipeline.
#
# When content is pasted, spliced, or digitally inserted:
#   • The inserted region carries noise from a DIFFERENT
#     source (different sensor, different JPEG quality,
#     different renderer).
#   • The boundary between original and pasted content
#     shows a sharp discontinuity in local noise statistics.
#
# Detection approach implemented here:
#   1. Convert the BGR page image to single-channel grayscale.
#   2. Apply Gaussian blur to produce a "clean" base image
#      (this removes high-frequency noise while preserving
#      structure).
#   3. Subtract the blurred base from the original grayscale
#      to isolate the noise residual — the high-frequency
#      component that is normally invisible to the eye.
#   4. Divide the noise residual into a grid of rectangular
#      regions and compute per-region statistics (mean, std).
#   5. Compute the variance of per-region means.  If the
#      variance is high, different parts of the page have
#      different noise levels — a strong indicator of
#      compositing or tampering.
#   6. Also compute the Laplacian variance of the full image
#      as a general sharpness/blur quality check.
#
# This is a PURE ALGORITHM FILE — no Flask, no Config, no
# file I/O, no scoring.
#
# Called by: services/ela_analyzer.py
# Input   : NumPy array (BGR, uint8) — one rendered page
# Output  : Structured dict with noise metrics
# ============================================================

from __future__ import annotations

import cv2
import numpy as np


# ── Regional Variance Threshold ─────────────────────────────
# If the variance of per-region noise means exceeds this
# value, the page is flagged as having inconsistent noise
# patterns — a hallmark of composited or spliced content.
# Empirically tuned for 300-DPI scanned/rendered documents.
_INCONSISTENCY_THRESHOLD = 25.0

# ── Cross-Page Outlier Z-Score ──────────────────────────────
# When comparing Laplacian variances across pages, any page
# whose value deviates more than this many standard deviations
# from the group mean is flagged as an outlier.
_OUTLIER_Z_THRESHOLD = 2.0


def analyze_noise(
    image: np.ndarray,
    blur_kernel: int = 3,
    grid_rows: int = 4,
    grid_cols: int = 4,
) -> dict | None:
    """Analyze noise patterns in a single page image.

    Extracts the noise residual (high-frequency component) by
    subtracting a Gaussian-blurred copy from the grayscale
    original, then measures how uniformly that noise is
    distributed across a grid of sub-regions.

    A genuine document — produced by a single source — will
    have nearly uniform noise everywhere.  A tampered document
    — with pasted or inserted content — will show regions
    whose noise statistics differ markedly from the rest.

    Args:
        image:       NumPy ndarray in BGR format (uint8).
        blur_kernel: Size of the Gaussian kernel (must be odd).
                     Larger values extract coarser noise.
        grid_rows:   Number of horizontal slices for regional
                     analysis.
        grid_cols:   Number of vertical slices for regional
                     analysis.

    Returns:
        dict with keys:
            noise_mean         (float)  — Overall mean of the
                noise residual across the entire image.
            noise_std          (float)  — Overall standard
                deviation of the noise residual.
            regional_variance  (float)  — Variance of the
                per-region noise means.  High values indicate
                composited content from different sources.
            laplacian_variance (float)  — Variance of the
                Laplacian operator output; a sharpness/blur
                quality indicator.
            region_grid        (list[list[float]]) — 2-D grid
                of per-region mean noise values
                (grid_rows × grid_cols).
            mean_intensity     (float)  — Average pixel
                brightness of the grayscale image (0–255).
            is_inconsistent    (bool)   — True if
                regional_variance exceeds the internal
                inconsistency threshold.
            error              (None|str) — Error description
                on partial failure; None on success.

        Returns None only on total unrecoverable failure
        (e.g., empty or None input).
    """
    try:
        # ── Guard: reject empty / None input ─────────────────
        if image is None or image.size == 0:
            return None

        # ── Ensure blur_kernel is a positive odd integer ─────
        # Gaussian blur requires an odd kernel size.  If the
        # caller passes an even number, bump it up by one.
        assert isinstance(blur_kernel, int), (
            f"blur_kernel must be int, got {type(blur_kernel)}"
        )
        if blur_kernel < 1:
            blur_kernel = 3  # fallback to default
        if blur_kernel % 2 == 0:
            blur_kernel += 1  # auto-correct even → odd

        # ── Step 1: Convert BGR → Grayscale ──────────────────
        # All noise analysis operates on single-channel data
        # to avoid color-channel correlation artifacts.
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()

        # ── Step 2: Gaussian blur to isolate the base ────────
        # The blurred image approximates the "ideal" noise-free
        # content — text, lines, and fills without sensor noise.
        blurred = cv2.GaussianBlur(
            gray,
            (blur_kernel, blur_kernel),
            0,
        )

        # ── Step 3: Compute noise residual ───────────────────
        # Subtract the clean base from the original.  The
        # difference is the high-frequency noise component.
        # Using float32 to preserve negative values and
        # fractional precision.
        noise_residual = (
            gray.astype(np.float32) - blurred.astype(np.float32)
        )

        # ── Step 4: Overall noise statistics ─────────────────
        # Global mean and std dev of the residual give a
        # single-number summary of how noisy the page is.
        overall_mean = float(np.mean(noise_residual))
        overall_std = float(np.std(noise_residual))

        # ── Step 5: Per-region analysis ──────────────────────
        # Divide the residual into a grid and compute local
        # mean noise in each cell.  If the image is too small
        # for the requested grid, fall back to 1×1.
        height, width = noise_residual.shape[:2]
        eff_rows = min(grid_rows, height)
        eff_cols = min(grid_cols, width)

        cell_h = height // eff_rows
        cell_w = width // eff_cols

        region_means: list[list[float]] = []
        flat_means: list[float] = []

        for r in range(eff_rows):
            row_means: list[float] = []
            for c in range(eff_cols):
                # Slice out the sub-region
                y_start = r * cell_h
                y_end = (
                    y_start + cell_h
                    if r < eff_rows - 1
                    else height  # last row absorbs remainder
                )
                x_start = c * cell_w
                x_end = (
                    x_start + cell_w
                    if c < eff_cols - 1
                    else width  # last col absorbs remainder
                )

                cell = noise_residual[y_start:y_end, x_start:x_end]

                # Per-region mean of the absolute noise residual
                cell_mean = float(np.mean(np.abs(cell)))
                row_means.append(round(cell_mean, 4))
                flat_means.append(cell_mean)

            region_means.append(row_means)

        # ── Step 6: Regional variance ────────────────────────
        # Variance of the per-region means.  A high value means
        # different parts of the page have different noise
        # characteristics — the hallmark of compositing.
        regional_var = (
            float(np.var(flat_means)) if flat_means else 0.0
        )

        # ── Step 7: Laplacian variance (sharpness check) ─────
        # The Laplacian operator highlights edges and texture.
        # A sharp, well-focused document scores high variance;
        # a blurry or defocused page scores low.
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        laplacian_var = float(np.var(laplacian))

        # ── Step 8: Mean intensity (dark region check) ───────
        # Average brightness of the grayscale image.  Very low
        # values indicate large dark/redacted/ink-covered areas.
        mean_intensity = float(np.mean(gray))

        # ── Step 9: Inconsistency flag ───────────────────────
        # Binary flag for downstream consumers that don't want
        # to re-implement threshold logic.
        is_inconsistent = regional_var > _INCONSISTENCY_THRESHOLD

        return {
            "noise_mean": round(overall_mean, 4),
            "noise_std": round(overall_std, 4),
            "regional_variance": round(regional_var, 4),
            "laplacian_variance": round(laplacian_var, 4),
            "region_grid": region_means,
            "mean_intensity": round(mean_intensity, 4),
            "is_inconsistent": is_inconsistent,
            "error": None,
        }

    except Exception:
        # Total failure — return None so callers can skip
        return None


def compare_pages(page_results: list[dict]) -> dict:
    """Compare noise profiles across multiple document pages.

    A genuine multi-page document (e.g., a scanned report)
    should have consistent scan/render characteristics across
    all pages — similar sharpness, similar noise level, similar
    Laplacian variance.

    This function compares the Laplacian variance values
    across pages and flags any page whose value deviates
    significantly from the group mean, which would suggest
    that page was captured or generated separately.

    Args:
        page_results: List of dicts returned by
            analyze_noise(), one per page.  None entries
            and dicts with missing keys are silently skipped.

    Returns:
        dict with keys:
            cross_page_variance (float)    — Variance of
                Laplacian values across all valid pages.
            outlier_pages       (list[int]) — 0-based page
                indices whose Laplacian variance deviates
                more than 2σ from the group mean.
            is_suspicious       (bool)     — True if any
                outlier pages were found.
            issues              (list[str]) — Human-readable
                issue descriptions (for backward compat with
                the calling service).
    """
    # ── Default "nothing to compare" response ────────────────
    default = {
        "cross_page_variance": 0.0,
        "outlier_pages": [],
        "is_suspicious": False,
        "issues": [],
    }

    try:
        # Need at least 2 valid results to compare
        if len(page_results) < 2:
            return default

        # ── Collect Laplacian variances from each page ───────
        # Build parallel lists of (index, value) so we can
        # trace outliers back to their page number.
        indexed_values: list[tuple[int, float]] = []
        for idx, result in enumerate(page_results):
            if result is None:
                continue
            val = result.get("laplacian_variance")
            if val is not None:
                indexed_values.append((idx, float(val)))

        if len(indexed_values) < 2:
            return default

        # ── Compute group statistics ─────────────────────────
        values = np.array(
            [v for _, v in indexed_values], dtype=np.float64
        )
        group_mean = float(np.mean(values))
        group_std = float(np.std(values))
        cross_page_var = float(np.var(values))

        # ── Identify outlier pages ───────────────────────────
        # A page is an outlier if its Laplacian variance is
        # more than _OUTLIER_Z_THRESHOLD standard deviations
        # from the group mean.  Guard against zero std (all
        # pages identical → no outliers).
        outlier_pages: list[int] = []

        if group_std > 0:
            for page_idx, val in indexed_values:
                z_score = abs(val - group_mean) / group_std
                if z_score > _OUTLIER_Z_THRESHOLD:
                    outlier_pages.append(page_idx)

        is_suspicious = len(outlier_pages) > 0

        # ── Build human-readable issues list ─────────────────
        issues: list[str] = []
        if is_suspicious:
            page_nums = ", ".join(
                str(p + 1) for p in outlier_pages
            )  # Convert to 1-based for readability
            issues.append(
                f"Significant visual inconsistency across "
                f"pages suggests pages from different sources. "
                f"Outlier page(s): {page_nums}."
            )

        return {
            "cross_page_variance": round(cross_page_var, 4),
            "outlier_pages": outlier_pages,
            "is_suspicious": is_suspicious,
            "issues": issues,
        }

    except Exception:
        return default
