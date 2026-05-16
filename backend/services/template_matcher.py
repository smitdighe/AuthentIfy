# ============================================================
# services/template_matcher.py — AuthentIfy Backend
# Project: AuthentIfy — "Verify before you trust."
# Role   : Compares extracted document data against known
#          authentic document templates (Aadhaar, PAN,
#          marksheets) to verify structural integrity.
#
# ── Approach ───────────────────────────────────────────────
# This module uses KEYWORD-BASED MATCHING only — no ML, no
# image computer vision.  It loads JSON template definitions
# from the templates/ directory, matches extracted OCR text
# against each template's required and optional keywords, and
# flags missing keywords as issues.
#
# This approach is:
#   • Fast   — simple string containment checks
#   • Explainable — every flag traces to a specific keyword
#   • Reliable — no model drift, no training data needed
#
# Template JSON schema (each file in templates/):
#   {
#     "doc_type": "aadhaar",
#     "expected_fields": ["name", "dob", ...],
#     "keywords": {
#       "required": ["UIDAI", "Unique Identification"],
#       "optional": ["Government of India", "आधार"]
#     },
#     "layout_regions": { ... },
#     "font_hints": {
#       "flag_if_found": ["Courier", "Comic Sans"]
#     },
#     "metadata_hints": {
#       "suspicious_if_missing": ["creationDate"]
#     }
#   }
#
# Called by: routes/analyze.py (Phase 4)
# Inputs  : OCR result dict, metadata result dict,
#            path to templates/ folder
# Config  : Config.TEMPLATES_FOLDER (passed as arg)
# ============================================================

from __future__ import annotations

import json
import os


# ── Template Loading ─────────────────────────────────────────


def _load_templates(templates_dir: str) -> list[dict]:
    """Load all template JSON files from the templates directory.

    Scans the directory for files ending in .json, parses each
    one, and returns a list of valid template dicts.  Silently
    skips files that fail to parse.

    Args:
        templates_dir: Absolute or relative path to the folder
            containing template JSON files.

    Returns:
        List of parsed template dicts.  Empty list if the
        directory is missing, empty, or contains no valid JSON.
    """
    templates: list[dict] = []

    # Guard: directory must exist
    if not templates_dir or not os.path.isdir(templates_dir):
        return templates

    for filename in sorted(os.listdir(templates_dir)):
        if not filename.lower().endswith(".json"):
            continue

        filepath = os.path.join(templates_dir, filename)

        try:
            with open(filepath, "r", encoding="utf-8") as fh:
                data = json.load(fh)

            # Minimal validation: must have doc_type and keywords
            if (
                isinstance(data, dict)
                and "doc_type" in data
                and "keywords" in data
            ):
                templates.append(data)

        except (json.JSONDecodeError, OSError):
            # Skip malformed or unreadable files
            continue

    return templates


# ── Text Extraction from OCR Result ──────────────────────────


def _extract_ocr_text(ocr_result: dict) -> str:
    """Extract the combined OCR text from an ocr_result dict.

    The OCR result (from services/ocr_extractor.py) stores
    per-page text in the "per_page_text" key as a list of
    strings.  This helper joins them into a single string
    for keyword matching.

    Args:
        ocr_result: Dict returned by ocr_extractor.analyze_ocr().

    Returns:
        Combined text string, or empty string on failure.
    """
    if not ocr_result or not isinstance(ocr_result, dict):
        return ""

    per_page = ocr_result.get("per_page_text", [])

    if isinstance(per_page, list):
        return " ".join(str(page) for page in per_page)

    return ""


# ── Keyword Matching ─────────────────────────────────────────


def _count_keyword_matches(
    text_lower: str,
    keywords: list[str],
) -> tuple[list[str], list[str]]:
    """Check which keywords appear in the text.

    Performs case-insensitive substring matching.

    Args:
        text_lower: The OCR text, already lowercased.
        keywords:   List of keyword strings to search for.

    Returns:
        Tuple of (found_keywords, missing_keywords).
    """
    found: list[str] = []
    missing: list[str] = []

    for kw in keywords:
        if kw.lower() in text_lower:
            found.append(kw)
        else:
            missing.append(kw)

    return found, missing


# ── Document Type Detection ──────────────────────────────────


def detect_doc_type(
    ocr_text: str,
    templates_dir: str,
) -> str | None:
    """Detect the document type by matching OCR text to templates.

    Loads all template JSON files from templates_dir and checks
    how many of each template's required keywords appear in the
    OCR text.  Returns the doc_type of the best-matching
    template, or None if no template matches sufficiently.

    A template is considered a match if at least 50% of its
    required keywords are found in the text.  Among matches,
    the template with the highest match ratio wins.

    Args:
        ocr_text:      Combined OCR text from all pages.
        templates_dir: Path to the templates/ directory.

    Returns:
        doc_type string (e.g., "aadhaar", "pan") of the
        best-matching template, or None if no match.
    """
    if not ocr_text or not ocr_text.strip():
        return None

    templates = _load_templates(templates_dir)
    if not templates:
        return None

    text_lower = ocr_text.lower()

    best_type: str | None = None
    best_ratio: float = 0.0

    # Minimum match ratio to consider a template as matching
    min_match_ratio = 0.5

    for template in templates:
        keywords_section = template.get("keywords", {})
        required = keywords_section.get("required", [])

        if not required:
            continue

        # Count how many required keywords appear in text
        found, _ = _count_keyword_matches(text_lower, required)

        ratio = len(found) / len(required)

        # Must meet minimum threshold and beat current best
        if ratio >= min_match_ratio and ratio > best_ratio:
            best_ratio = ratio
            best_type = template.get("doc_type")

    return best_type


# ── Metadata Hint Checking ───────────────────────────────────


def _check_metadata_hints(
    template: dict,
    metadata_result: dict,
) -> list[str]:
    """Check metadata hints defined in the template.

    Templates can specify metadata fields that should be
    present (e.g., "creationDate").  If the field is missing
    or empty in the raw metadata, an issue is raised.

    Args:
        template:        The matched template dict.
        metadata_result: Dict from metadata_analyzer.

    Returns:
        List of issue strings for missing metadata fields.
    """
    issues: list[str] = []

    hints = template.get("metadata_hints", {})
    suspicious_if_missing = hints.get(
        "suspicious_if_missing", []
    )

    if not suspicious_if_missing:
        return issues

    # Extract raw metadata from the metadata result
    raw_meta = metadata_result.get("raw_metadata", {})

    for field in suspicious_if_missing:
        value = raw_meta.get(field, "")
        if not value or not str(value).strip():
            issues.append(
                f"Expected metadata field '{field}' is "
                f"missing or empty — unusual for this "
                f"document type."
            )

    return issues


# ── Main Template Matching ───────────────────────────────────


def match_template(
    ocr_result: dict,
    metadata_result: dict,
    templates_dir: str,
) -> dict:
    """Compare document data against known authentic templates.

    Orchestrates the full template matching pipeline:
        1. Extract OCR text from the ocr_result dict.
        2. Detect document type by matching keywords.
        3. If no template matches, return neutral result.
        4. If a template matches, verify all required keywords
           are present and check metadata hints.
        5. Flag each missing required keyword as an issue.
        6. Compute a confidence ratio (found / total required).

    Args:
        ocr_result:      dict from services/ocr_extractor.py
                         (contains per_page_text, etc.).
        metadata_result: dict from services/metadata_analyzer.py
                         (contains raw_metadata, etc.).
        templates_dir:   Path to the folder containing template
                         JSON files.

    Returns:
        dict with keys:
            doc_type                 (str|None)  — Detected
                document type, or None / "unknown".
            matched                  (bool)      — True if a
                template was successfully matched.
            required_keywords_found  (list[str]) — Required
                keywords present in the OCR text.
            required_keywords_missing(list[str]) — Required
                keywords absent from the OCR text.
            issues                   (list[str]) — Human-
                readable issue descriptions.
            issue_count              (int)       — len(issues).
            confidence               (float)     — Ratio of
                required keywords found (0.0–1.0).
            error                    (None|str)  — Error on
                failure; None on success.
    """
    # ── Safe default for early returns ───────────────────────
    neutral: dict = {
        "doc_type": "unknown",
        "matched": False,
        "required_keywords_found": [],
        "required_keywords_missing": [],
        "issues": [],
        "issue_count": 0,
        "confidence": 0.0,
        "error": None,
    }

    try:
        # ── Step 1: Extract OCR text ─────────────────────────
        ocr_text = _extract_ocr_text(ocr_result)

        if not ocr_text.strip():
            # No text to match against — return neutral
            neutral["error"] = (
                "No OCR text available for template matching."
            )
            return neutral

        # ── Step 2: Detect document type ─────────────────────
        doc_type = detect_doc_type(ocr_text, templates_dir)

        if doc_type is None:
            # No template matched — return neutral (not an error)
            return neutral

        # ── Step 3: Load matched template for full analysis ──
        templates = _load_templates(templates_dir)
        matched_template = None

        for tmpl in templates:
            if tmpl.get("doc_type") == doc_type:
                matched_template = tmpl
                break

        if matched_template is None:
            # Should not happen, but guard defensively
            return neutral

        # ── Step 4: Verify all required keywords ─────────────
        text_lower = ocr_text.lower()
        keywords_section = matched_template.get("keywords", {})
        required_keywords = keywords_section.get("required", [])

        found, missing = _count_keyword_matches(
            text_lower, required_keywords
        )

        # ── Step 5: Build issues list ────────────────────────
        issues: list[str] = []

        # Flag each missing required keyword
        for kw in missing:
            issues.append(
                f"Expected keyword '{kw}' not found in "
                f"document — required for {doc_type} "
                f"documents."
            )

        # ── Step 6: Check metadata hints ─────────────────────
        meta_issues = _check_metadata_hints(
            matched_template, metadata_result
        )
        issues.extend(meta_issues)

        # ── Step 7: Compute confidence ───────────────────────
        # Confidence = ratio of required keywords found.
        # 1.0 = all present, 0.0 = none present.
        if required_keywords:
            confidence = len(found) / len(required_keywords)
        else:
            confidence = 1.0  # No requirements = full match

        return {
            "doc_type": doc_type,
            "matched": True,
            "required_keywords_found": found,
            "required_keywords_missing": missing,
            "issues": issues,
            "issue_count": len(issues),
            "confidence": round(confidence, 4),
            "error": None,
        }

    except Exception as exc:
        # Never crash — return safe default with error detail
        return {
            "doc_type": "unknown",
            "matched": False,
            "required_keywords_found": [],
            "required_keywords_missing": [],
            "issues": [],
            "issue_count": 0,
            "confidence": 0.0,
            "error": f"Template matching failed: {exc}",
        }
