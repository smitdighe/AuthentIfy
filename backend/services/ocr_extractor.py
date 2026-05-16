# ============================================================
# services/ocr_extractor.py — AuthentIfy Backend
# Project: AuthentIfy — "Verify before you trust."
# Role   : Runs OCR on rendered PDF page images, analyzes
#          text quality, and produces human-readable issues.
#
# This is a SERVICE file — it reads pre-rendered page images
# from processed/, delegates OCR to pytesseract, interprets
# results against Config thresholds, and returns structured
# findings.
#
# IMPORTANT: Page images are already saved to processed/ by
# ela_analyzer.py. This service reads from there. If images
# don't exist, it falls back to rendering via pdf_utils.
#
# Calls  : utils.image_utils, utils.pdf_utils
# Called  : routes/analyze.py
# Config : Config.MIN_TEXT_LENGTH, Config.MIN_OCR_CONFIDENCE,
#          Config.GARBLE_RATIO_THRESHOLD
# ============================================================

from __future__ import annotations

import os
import re

from config import Config
from utils import image_utils
from utils import pdf_utils


# ── Tesseract Availability Check ─────────────────────────────
# Tesseract may not be installed on every machine. We attempt
# the import once at module level and set a flag so individual
# functions can degrade gracefully without repeated try/except.

_TESSERACT_AVAILABLE = False

try:
    import pytesseract

    # Probe for the binary — raises if not found
    pytesseract.get_tesseract_version()
    _TESSERACT_AVAILABLE = True
except (ImportError, Exception):
    # ImportError: pytesseract package not installed
    # Exception: catches TesseractNotFoundError and any
    #            other startup failure
    pytesseract = None  # type: ignore[assignment]


# ── OCR Extraction Helpers ───────────────────────────────────


def _extract_text_and_confidence(
    image_path: str,
) -> tuple[str, float]:
    """Run Tesseract OCR on a single page image.

    Uses pytesseract.image_to_data() to obtain per-word
    confidence scores, then computes mean confidence across
    all recognized words.

    Args:
        image_path: Path to the rendered page image (PNG).

    Returns:
        Tuple of (extracted_text, mean_confidence).
        On failure returns ("", 0.0).
    """
    if not _TESSERACT_AVAILABLE or pytesseract is None:
        return "", 0.0

    pil_image = image_utils.load_image_pil(image_path)
    if pil_image is None:
        return "", 0.0

    try:
        # image_to_data returns a TSV string with columns:
        # level, page_num, block_num, par_num, line_num,
        # word_num, left, top, width, height, conf, text
        data = pytesseract.image_to_data(
            pil_image, output_type=pytesseract.Output.DICT
        )

        confidences = data.get("conf", [])
        texts = data.get("text", [])

        # Collect valid words and their confidences
        # conf == -1 means Tesseract could not determine
        # confidence (e.g., whitespace, empty blocks)
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


# ── Individual OCR Checks ────────────────────────────────────


def _check_low_confidence(
    mean_confidence: float,
) -> str | None:
    """CHECK 1 — Flag if mean OCR confidence is below threshold.

    Low confidence indicates the text is image-embedded,
    heavily distorted, or uses non-standard fonts that
    Tesseract cannot reliably decode.

    Args:
        mean_confidence: Mean per-word confidence (0–100).

    Returns:
        Issue string if confidence is low, None otherwise.
    """
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
    """CHECK 2 — Flag if total extracted text is unusually sparse.

    Genuine multi-page documents contain substantial text.
    Very short text across many pages suggests the content
    is primarily image-based or has been stripped.

    Args:
        total_length: Total character count across all pages.
        page_count:   Number of pages analyzed.

    Returns:
        Issue string if text is sparse, None otherwise.
    """
    if total_length < Config.MIN_TEXT_LENGTH:
        return (
            f"Total extracted text ({total_length} chars) is "
            f"unusually sparse for a {page_count}-page "
            f"document."
        )
    return None


def _check_garbled_text(full_text: str) -> tuple[float, str | None]:
    """CHECK 3 — Flag if text has a high ratio of garbled characters.

    Computes the ratio of non-alphanumeric, non-whitespace
    characters to total characters. A high ratio indicates
    artificially generated text, font encoding corruption,
    or deliberate obfuscation.

    Args:
        full_text: Concatenated OCR text from all pages.

    Returns:
        Tuple of (garble_ratio, issue_string_or_None).
    """
    if not full_text:
        return 0.0, None

    total_chars = len(full_text)

    # Count characters that are NOT alphanumeric and NOT space
    # These are the "garble" characters (symbols, control chars)
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
    """CHECK 4 — Flag pages with zero text among text-rich pages.

    If some pages have substantial text content but one or
    more pages have zero extractable text, those empty pages
    may be image-only insertions spliced into the document.

    Args:
        per_page_lengths: List of text character counts per page.

    Returns:
        List of issue strings (one per flagged page).
    """
    issues: list[str] = []

    if len(per_page_lengths) < 2:
        return issues  # Need multiple pages to compare

    # Determine if other pages have significant text
    # "Significant" = at least MIN_TEXT_LENGTH on any page
    max_page_len = max(per_page_lengths)

    if max_page_len < Config.MIN_TEXT_LENGTH:
        return issues  # All pages sparse — not a density issue

    for idx, length in enumerate(per_page_lengths):
        if length == 0:
            page_num = idx + 1  # 1-based
            issues.append(
                f"Page {page_num} contains no extractable "
                f"text while other pages do — suggests "
                f"image-only insertion."
            )

    return issues


# ── Page Image Discovery ─────────────────────────────────────


def _get_page_images(
    pdf_path: str,
    processed_dir: str,
) -> list[str]:
    """Locate or render page images for OCR processing.

    First checks if rendered images already exist in
    processed_dir (saved by ela_analyzer.py). If not,
    falls back to rendering via pdf_utils.render_all_pages().

    Args:
        pdf_path:      Path to the source PDF file.
        processed_dir: Directory containing/expecting page PNGs.

    Returns:
        Sorted list of page image file paths. Empty on failure.
    """
    # ── Try to find existing rendered images ─────────────────
    if os.path.isdir(processed_dir):
        existing = sorted(
            os.path.join(processed_dir, f)
            for f in os.listdir(processed_dir)
            if f.lower().endswith((".png", ".jpg", ".jpeg"))
        )
        if existing:
            return existing

    # ── Fallback: render pages ourselves ─────────────────────
    try:
        rendered = pdf_utils.render_all_pages(
            pdf_path, processed_dir
        )
        return rendered
    except Exception as exc:
        print(f"[OCR] Fallback page render failed: {exc}")
        return []


# ── Main OCR Analysis Entry Point ────────────────────────────


def analyze_ocr(
    pdf_path: str,
    processed_dir: str,
) -> dict:
    """Perform OCR-based text analysis on a PDF document.

    Orchestrates the full OCR pipeline:

        1. Locate rendered page images in processed_dir
           (created by ela_analyzer.py), or render them
           via pdf_utils as a fallback.
        2. Run Tesseract OCR on each page image to extract
           text and per-word confidence scores.
        3. Run all 4 OCR checks:
           - Low confidence detection
           - Sparse text detection
           - Garbled text detection
           - Page density inconsistency detection
        4. Aggregate all issues into a single result dict.

    If Tesseract is not installed, a single issue is reported
    and partial results are returned — the service never crashes.

    Args:
        pdf_path:      Path to the source PDF file.
        processed_dir: Directory containing rendered page images.

    Returns:
        dict with keys:
            issues           (list[str])  — Human-readable issues.
            issue_count      (int)        — len(issues).
            total_text_length(int)        — Combined text length.
            mean_confidence  (float)      — Average OCR confidence.
            per_page_text    (list[str])  — Extracted text per page.
            per_page_length  (list[int])  — Text length per page.
            garble_ratio     (float)      — Non-alnum character ratio.
            error            (None|str)   — Error on total failure.
    """
    try:
        issues: list[str] = []

        # ── Check Tesseract availability ─────────────────────
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

        # ── STEP 1: Locate page images ───────────────────────
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

        # ── STEP 2: Run OCR on each page ─────────────────────
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

        # Aggregate metrics
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

        # ── STEP 3: Run all OCR checks ──────────────────────

        # CHECK 1 — Low OCR confidence
        conf_issue = _check_low_confidence(mean_confidence)
        if conf_issue is not None:
            issues.append(conf_issue)

        # CHECK 2 — Sparse text
        sparse_issue = _check_sparse_text(
            total_length, page_count
        )
        if sparse_issue is not None:
            issues.append(sparse_issue)

        # CHECK 3 — Garbled text
        garble_ratio, garble_issue = _check_garbled_text(
            full_text
        )
        if garble_issue is not None:
            issues.append(garble_issue)

        # CHECK 4 — Page density inconsistency
        density_issues = _check_page_density(per_page_length)
        issues.extend(density_issues)

        # ── STEP 4: Build and return result ──────────────────
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
        # Total failure — return error, never crash
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
