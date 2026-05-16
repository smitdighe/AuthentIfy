# ============================================================
# services/ela_analyzer.py — AuthentIfy Backend
# Project: AuthentIfy — "Verify before you trust."
# Role   : Orchestrates visual forensic analysis on every page
#          of a PDF — runs ELA and noise algorithms, interprets
#          results against Config thresholds, and produces
#          human-readable issues.
#
# This is a SERVICE file — it renders pages, delegates to
# algorithm modules, and interprets raw numbers into verdicts.
# It does NOT implement algorithms.
#
# Calls  : utils.pdf_utils, utils.image_utils,
#           forensics.ela, forensics.noise_analysis
# Called  : routes/analyze.py
# Config : Config.BLUR_THRESHOLD,
#          Config.NOISE_VARIANCE_THRESHOLD,
#          Config.DARK_REGION_THRESHOLD
# ============================================================

from __future__ import annotations

import cv2
import numpy as np

from config import Config
from utils import pdf_utils
from utils import image_utils
from forensics import ela
from forensics import noise_analysis


# ── Interpretation Thresholds ────────────────────────────────
# ELA-specific thresholds (not in Config because they are
# internal to this service's interpretation logic).

_ELA_SUSPICIOUS_RATIO = 0.15   # >15% blocks flagged → issue
_ELA_MAX_ERROR_SPIKE = 80.0    # Peak error above this → issue


# ── Per-Page Analysis Helpers ────────────────────────────────


def _analyze_page_ela(
    image_path: str,
    page_num: int,
) -> tuple[dict | None, list[str]]:
    """Run ELA on a single page and interpret the result.

    Loads the page image as PIL, runs forensics/ela.run_ela(),
    and flags issues based on suspicious_ratio and max_error.

    Args:
        image_path: Path to the rendered page image (PNG).
        page_num:   1-based page number for issue messages.

    Returns:
        Tuple of (ela_result dict or None, list of issue strings).
    """
    issues: list[str] = []

    # Load as PIL for ELA (ELA works on PIL images)
    pil_image = image_utils.load_image_pil(image_path)
    if pil_image is None:
        print(
            f"[ELA] Page {page_num}: "
            f"Failed to load image as PIL — skipping ELA."
        )
        return None, issues

    # Run the ELA algorithm
    ela_result = ela.run_ela(pil_image)
    if ela_result is None:
        print(
            f"[ELA] Page {page_num}: "
            f"ELA computation failed — skipping."
        )
        return None, issues

    # ── Interpret: suspicious block ratio ────────────────────
    ratio = ela_result.get("suspicious_ratio", 0.0)
    if ratio > _ELA_SUSPICIOUS_RATIO:
        pct = round(ratio * 100, 1)
        issues.append(
            f"Page {page_num}: ELA detected {pct}% suspicious "
            f"regions, suggesting content may have been "
            f"altered."
        )

    # ── Interpret: extreme error spike ───────────────────────
    max_err = ela_result.get("max_error", 0.0)
    if max_err > _ELA_MAX_ERROR_SPIKE:
        issues.append(
            f"Page {page_num}: ELA detected an extreme "
            f"error spike (max={round(max_err, 1)}), "
            f"indicating localized tampering."
        )

    return ela_result, issues


def _analyze_page_noise(
    image_path: str,
    page_num: int,
) -> tuple[dict | None, list[str]]:
    """Run noise analysis on a single page and interpret results.

    Loads the page image as NumPy (BGR), runs noise analysis,
    and flags issues for blur, noise inconsistency, and dark
    regions.

    Args:
        image_path: Path to the rendered page image (PNG).
        page_num:   1-based page number for issue messages.

    Returns:
        Tuple of (noise_result dict or None, list of issue strings).
    """
    issues: list[str] = []

    # Load as NumPy BGR for OpenCV-based analysis
    np_image = image_utils.load_image_numpy(image_path)
    if np_image is None:
        print(
            f"[Noise] Page {page_num}: "
            f"Failed to load image as NumPy — skipping."
        )
        return None, issues

    # Run noise analysis algorithm
    noise_result = noise_analysis.analyze_noise(np_image)
    if noise_result is None:
        print(
            f"[Noise] Page {page_num}: "
            f"Noise analysis failed — skipping."
        )
        return None, issues

    # ── Interpret: blur detection ────────────────────────────
    # Low Laplacian variance = blurry image (sharp docs > 300)
    lap_var = noise_result.get("laplacian_variance", 999.0)
    if lap_var < Config.BLUR_THRESHOLD:
        issues.append(
            f"Page {page_num}: Abnormal blurring detected, "
            f"which may indicate content obscuring."
        )

    # ── Interpret: noise inconsistency ───────────────────────
    # High regional variance = different noise patterns mixed
    regional_var = noise_result.get("regional_variance", 0.0)
    if regional_var > Config.NOISE_VARIANCE_THRESHOLD:
        issues.append(
            f"Page {page_num}: Noise pattern inconsistency "
            f"detected, suggesting composite content."
        )

    # ── Interpret: dark regions ──────────────────────────────
    # Very low mean intensity = large dark/redacted areas
    mean_intensity = noise_result.get("mean_intensity", 255.0)
    if mean_intensity < Config.DARK_REGION_THRESHOLD:
        issues.append(
            f"Page {page_num}: Unusually dark regions "
            f"detected, possibly redacted or ink-covered "
            f"areas."
        )

    return noise_result, issues


# ── Cross-Page Comparison ────────────────────────────────────


def _compare_all_pages(
    noise_results: list[dict],
) -> list[str]:
    """Compare noise profiles across all pages for consistency.

    Delegates to noise_analysis.compare_pages() and returns
    any issues found.

    Args:
        noise_results: List of noise result dicts, one per page.

    Returns:
        List of issue strings (empty if pages are consistent).
    """
    # Filter out None results from failed pages
    valid_results = [r for r in noise_results if r is not None]

    if len(valid_results) < 2:
        return []  # Need at least 2 pages to compare

    try:
        comparison = noise_analysis.compare_pages(valid_results)

        if comparison.get("is_suspicious", False):
            return comparison.get("issues", [])

        return []

    except Exception as exc:
        print(f"[Vision] Cross-page comparison failed: {exc}")
        return []


# ── Main Vision Analysis Entry Point ─────────────────────────


def analyze_vision(pdf_path: str, processed_dir: str) -> dict:
    """Perform comprehensive visual forensic analysis on a PDF.

    Orchestrates the full vision analysis pipeline:

        1. Render all PDF pages as PNG images to processed_dir
           via pdf_utils.render_all_pages().
        2. For each rendered page image:
           a. Load as PIL → run ELA (forensics/ela.py)
           b. Load as NumPy → run noise analysis
              (forensics/noise_analysis.py)
           c. Check blur (Laplacian variance vs threshold)
           d. Check dark regions (mean intensity vs threshold)
           e. Interpret all results into human-readable issues
        3. Compare noise profiles across all pages for
           consistency (forensics/noise_analysis.compare_pages)
        4. Aggregate all issues into a single result dict.

    If a single page fails analysis, it is skipped and the
    remaining pages are still processed. Only a total failure
    (e.g., PDF cannot be opened) returns an error.

    Args:
        pdf_path:      Path to the PDF file to analyze.
        processed_dir: Directory to store rendered page images.

    Returns:
        dict with keys:
            issues           (list[str])  — All human-readable
                issues found across all pages.
            issue_count      (int)        — len(issues).
            page_count       (int)        — Number of pages
                successfully rendered.
            page_image_paths (list[str])  — Paths to rendered
                page images on disk.
            per_page_ela     (list[dict]) — Raw ELA results
                per page (None entries for failed pages).
            per_page_noise   (list[dict]) — Raw noise results
                per page (None entries for failed pages).
            error            (None|str)   — Error string on
                total failure, None on success.
    """
    try:
        # ── STEP 1: Render all pages ─────────────────────────
        page_paths = pdf_utils.render_all_pages(
            pdf_path, processed_dir
        )

        if not page_paths:
            return {
                "issues": [],
                "issue_count": 0,
                "page_count": 0,
                "page_image_paths": [],
                "per_page_ela": [],
                "per_page_noise": [],
                "error": (
                    f"Failed to render any pages from "
                    f"'{pdf_path}'. File may be missing, "
                    f"corrupt, or encrypted."
                ),
            }

        page_count = len(page_paths)
        all_issues: list[str] = []
        per_page_ela: list[dict | None] = []
        per_page_noise: list[dict | None] = []

        # ── STEP 2: Analyze each page ────────────────────────
        for idx, image_path in enumerate(page_paths):
            # 1-based page number for human-readable messages
            page_num = idx + 1

            # ── 2a/2b: ELA analysis ──────────────────────────
            ela_result, ela_issues = _analyze_page_ela(
                image_path, page_num
            )
            per_page_ela.append(ela_result)
            all_issues.extend(ela_issues)

            # ── 2c/2d: Noise, blur, dark region analysis ─────
            noise_result, noise_issues = _analyze_page_noise(
                image_path, page_num
            )
            per_page_noise.append(noise_result)
            all_issues.extend(noise_issues)

        # ── STEP 3: Cross-page comparison ────────────────────
        cross_page_issues = _compare_all_pages(per_page_noise)
        all_issues.extend(cross_page_issues)

        # ── STEP 4: Build and return result ──────────────────
        return {
            "issues": all_issues,
            "issue_count": len(all_issues),
            "page_count": page_count,
            "page_image_paths": page_paths,
            "per_page_ela": per_page_ela,
            "per_page_noise": per_page_noise,
            "error": None,
        }

    except Exception as exc:
        # Total failure — return error, never crash
        print(f"[Vision] Total analysis failure: {exc}")
        return {
            "issues": [],
            "issue_count": 0,
            "page_count": 0,
            "page_image_paths": [],
            "per_page_ela": [],
            "per_page_noise": [],
            "error": f"Vision analysis failed: {exc}",
        }
