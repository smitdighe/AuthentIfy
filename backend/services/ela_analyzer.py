from __future__ import annotations

import cv2
import numpy as np

from config import Config
from utils import pdf_utils
from utils import image_utils
from forensics import ela
from forensics import noise_analysis

_ELA_SUSPICIOUS_RATIO = 0.15
_ELA_MAX_ERROR_SPIKE = 80.0

def _analyze_page_ela(
    image_path: str,
    page_num: int,
) -> tuple[dict | None, list[str]]:
    
    issues: list[str] = []

    pil_image = image_utils.load_image_pil(image_path)
    if pil_image is None:
        print(
            f"[ELA] Page {page_num}: "
            f"Failed to load image as PIL — skipping ELA."
        )
        return None, issues

    ela_result = ela.run_ela(pil_image)
    if ela_result is None:
        print(
            f"[ELA] Page {page_num}: "
            f"ELA computation failed — skipping."
        )
        return None, issues

    ratio = ela_result.get("suspicious_ratio", 0.0)
    if ratio > _ELA_SUSPICIOUS_RATIO:
        pct = round(ratio * 100, 1)
        issues.append(
            f"Page {page_num}: ELA detected {pct}% suspicious "
            f"regions, suggesting content may have been "
            f"altered."
        )
        
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
    
    issues: list[str] = []

    np_image = image_utils.load_image_numpy(image_path)
    if np_image is None:
        print(
            f"[Noise] Page {page_num}: "
            f"Failed to load image as NumPy — skipping."
        )
        return None, issues

    noise_result = noise_analysis.analyze_noise(np_image)
    if noise_result is None:
        print(
            f"[Noise] Page {page_num}: "
            f"Noise analysis failed — skipping."
        )
        return None, issues

    lap_var = noise_result.get("laplacian_variance", 999.0)
    if lap_var < Config.BLUR_THRESHOLD:
        issues.append(
            f"Page {page_num}: Abnormal blurring detected, "
            f"which may indicate content obscuring."
        )

    regional_var = noise_result.get("regional_variance", 0.0)
    if regional_var > Config.NOISE_VARIANCE_THRESHOLD:
        issues.append(
            f"Page {page_num}: Noise pattern inconsistency "
            f"detected, suggesting composite content."
        )

    mean_intensity = noise_result.get("mean_intensity", 255.0)
    if mean_intensity < Config.DARK_REGION_THRESHOLD:
        issues.append(
            f"Page {page_num}: Unusually dark regions "
            f"detected, possibly redacted or ink-covered "
            f"areas."
        )

    return noise_result, issues

def _compare_all_pages(
    noise_results: list[dict],
) -> list[str]:
    
    valid_results = [r for r in noise_results if r is not None]

    if len(valid_results) < 2:
        return []

    try:
        comparison = noise_analysis.compare_pages(valid_results)
        if comparison.get("is_suspicious", False):
            return comparison.get("issues", [])
        return []

    except Exception as exc:
        print(f"[Vision] Cross-page comparison failed: {exc}")
        return []

def analyze_vision(pdf_path: str, processed_dir: str) -> dict:
    
    try:
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

        for idx, image_path in enumerate(page_paths):
            page_num = idx + 1

            ela_result, ela_issues = _analyze_page_ela(
                image_path, page_num
            )
            per_page_ela.append(ela_result)
            all_issues.extend(ela_issues)

            noise_result, noise_issues = _analyze_page_noise(
                image_path, page_num
            )
            per_page_noise.append(noise_result)
            all_issues.extend(noise_issues)

        cross_page_issues = _compare_all_pages(per_page_noise)
        all_issues.extend(cross_page_issues)

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
