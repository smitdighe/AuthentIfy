from __future__ import annotations

import os
import re

from config import Config
from utils import image_utils
from utils import pdf_utils

_TESSERACT_AVAILABLE = False

try:
    import pytesseract

    pytesseract.get_tesseract_version()
    _TESSERACT_AVAILABLE = True
    
except (ImportError, Exception):
    pytesseract = None
    
def _extract_text_and_confidence(
    image_path: str,
) -> tuple[str, float]:
    
    if not _TESSERACT_AVAILABLE or pytesseract is None:
        return "", 0.0

    pil_image = image_utils.load_image_pil(image_path)
    if pil_image is None:
        return "", 0.0

    try:
        data = pytesseract.image_to_data(
            pil_image, output_type=pytesseract.Output.DICT
        )

        confidences = data.get("conf", [])
        texts = data.get("text", [])

        valid_confs: list[float] = []
        extracted_words: list[str] = []

        for conf, text in zip(confidences, texts):
            conf_val = int(conf)
            word = str(text).strip()

            if conf_val > -1 and word:
                valid_confs.append(float(conf_val))
                extracted_words.append(word)

        full_text = " ".join(extracted_words)

        mean_conf = (
            sum(valid_confs) / len(valid_confs)
            if valid_confs
            else 0.0
        )

        return full_text, round(mean_conf, 2)

    except Exception as exc:
        print(
            f"[OCR] Tesseract failed on '{image_path}': {exc}"
        )
        return "", 0.0

def _check_low_confidence(
    mean_confidence: float,
) -> str | None:
    
    if mean_confidence < Config.MIN_OCR_CONFIDENCE:
        pct = round(mean_confidence, 1)
        return (
            f"OCR confidence is {pct}% — text may be "
            f"image-embedded or heavily distorted."
        )
    return None

def _check_sparse_text(
    total_length: int,
    page_count: int,
) -> str | None:
    
    if total_length < Config.MIN_TEXT_LENGTH:
        return (
            f"Total extracted text ({total_length} chars) is "
            f"unusually sparse for a {page_count}-page "
            f"document."
        )
    return None

def _check_garbled_text(full_text: str) -> tuple[float, str | None]:
    
    if not full_text:
        return 0.0, None

    total_chars = len(full_text)
    garble_count = sum(
        1 for ch in full_text
        if not ch.isalnum() and not ch.isspace()
    )

    ratio = round(garble_count / total_chars, 4)

    if ratio > Config.GARBLE_RATIO_THRESHOLD:
        return ratio, (
            "High ratio of unrecognizable characters "
            "detected — text may be artificially generated "
            "or corrupted."
        )

    return ratio, None

def _check_page_density(
    per_page_lengths: list[int],
) -> list[str]:
    
    issues: list[str] = []

    if len(per_page_lengths) < 2:
        return issues
    max_page_len = max(per_page_lengths)

    if max_page_len < Config.MIN_TEXT_LENGTH:
        return issues

    for idx, length in enumerate(per_page_lengths):
        if length == 0:
            page_num = idx + 1
            issues.append(
                f"Page {page_num} contains no extractable "
                f"text while other pages do — suggests "
                f"image-only insertion."
            )

    return issues

def _get_page_images(
    pdf_path: str,
    processed_dir: str,
) -> list[str]:
    
    if os.path.isdir(processed_dir):
        existing = sorted(
            os.path.join(processed_dir, f)
            for f in os.listdir(processed_dir)
            if f.lower().endswith((".png", ".jpg", ".jpeg"))
        )
        if existing:
            return existing

    try:
        rendered = pdf_utils.render_all_pages(
            pdf_path, processed_dir
        )
        return rendered
    except Exception as exc:
        print(f"[OCR] Fallback page render failed: {exc}")
        return []
    
def analyze_ocr(
    pdf_path: str,
    processed_dir: str,
) -> dict:
    
    try:
        issues: list[str] = []
        
        if not _TESSERACT_AVAILABLE:
            issues.append(
                "OCR engine (Tesseract) not found — "
                "text analysis skipped."
            )
            return {
                "issues": issues,
                "issue_count": len(issues),
                "total_text_length": 0,
                "mean_confidence": 0.0,
                "per_page_text": [],
                "per_page_length": [],
                "garble_ratio": 0.0,
                "error": None,
            }

        page_paths = _get_page_images(pdf_path, processed_dir)

        if not page_paths:
            return {
                "issues": [],
                "issue_count": 0,
                "total_text_length": 0,
                "mean_confidence": 0.0,
                "per_page_text": [],
                "per_page_length": [],
                "garble_ratio": 0.0,
                "error": (
                    f"No page images found in "
                    f"'{processed_dir}' and rendering "
                    f"failed for '{pdf_path}'."
                ),
            }

        per_page_text: list[str] = []
        per_page_length: list[int] = []
        all_confidences: list[float] = []

        for idx, image_path in enumerate(page_paths):
            page_num = idx + 1

            text, confidence = _extract_text_and_confidence(
                image_path
            )

            per_page_text.append(text)
            per_page_length.append(len(text))

            if confidence > 0.0:
                all_confidences.append(confidence)

        full_text = " ".join(per_page_text)
        total_length = sum(per_page_length)
        page_count = len(page_paths)

        mean_confidence = (
            round(
                sum(all_confidences) / len(all_confidences), 2
            )
            if all_confidences
            else 0.0
        )

        conf_issue = _check_low_confidence(mean_confidence)
        if conf_issue is not None:
            issues.append(conf_issue)

        sparse_issue = _check_sparse_text(
            total_length, page_count
        )
        if sparse_issue is not None:
            issues.append(sparse_issue)

        garble_ratio, garble_issue = _check_garbled_text(
            full_text
        )
        if garble_issue is not None:
            issues.append(garble_issue)

        density_issues = _check_page_density(per_page_length)
        issues.extend(density_issues)

        return {
            "issues": issues,
            "issue_count": len(issues),
            "total_text_length": total_length,
            "mean_confidence": mean_confidence,
            "per_page_text": per_page_text,
            "per_page_length": per_page_length,
            "garble_ratio": garble_ratio,
            "error": None,
        }

    except Exception as exc:
        print(f"[OCR] Total analysis failure: {exc}")
        return {
            "issues": [],
            "issue_count": 0,
            "total_text_length": 0,
            "mean_confidence": 0.0,
            "per_page_text": [],
            "per_page_length": [],
            "garble_ratio": 0.0,
            "error": f"OCR analysis failed: {exc}",
        }
