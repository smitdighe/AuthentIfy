from __future__ import annotations

import json
import os

def _load_templates(templates_dir: str) -> list[dict]:
    
    templates: list[dict] = []

    if not templates_dir or not os.path.isdir(templates_dir):
        return templates

    for filename in sorted(os.listdir(templates_dir)):
        if not filename.lower().endswith(".json"):
            continue
        filepath = os.path.join(templates_dir, filename)
        try:
            with open(filepath, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            if (
                isinstance(data, dict)
                and "doc_type" in data
                and "keywords" in data
            ):
                templates.append(data)
        except (json.JSONDecodeError, OSError):
            continue
    return templates

def _extract_ocr_text(ocr_result: dict) -> str:
    
    if not ocr_result or not isinstance(ocr_result, dict):
        return ""
    per_page = ocr_result.get("per_page_text", [])
    if isinstance(per_page, list):
        return " ".join(str(page) for page in per_page)
    return ""

def _count_keyword_matches(
    text_lower: str,
    keywords: list[str],
) -> tuple[list[str], list[str]]:
   
    found: list[str] = []
    missing: list[str] = []

    for kw in keywords:
        if kw.lower() in text_lower:
            found.append(kw)
        else:
            missing.append(kw)
    return found, missing

def detect_doc_type(
    ocr_text: str,
    templates_dir: str,
) -> str | None:
    
    if not ocr_text or not ocr_text.strip():
        return None
    templates = _load_templates(templates_dir)
    
    if not templates:
        return None
    
    text_lower = ocr_text.lower()
    best_type: str | None = None
    best_ratio: float = 0.0
    min_match_ratio = 0.5

    for template in templates:
        keywords_section = template.get("keywords", {})
        required = keywords_section.get("required", [])

        if not required:
            continue

        found, _ = _count_keyword_matches(text_lower, required)
        ratio = len(found) / len(required)

        if ratio >= min_match_ratio and ratio > best_ratio:
            best_ratio = ratio
            best_type = template.get("doc_type")

    return best_type

def _check_metadata_hints(
    template: dict,
    metadata_result: dict,
) -> list[str]:
    
    issues: list[str] = []

    hints = template.get("metadata_hints", {})
    suspicious_if_missing = hints.get(
        "suspicious_if_missing", []
    )

    if not suspicious_if_missing:
        return issues

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

def match_template(
    ocr_result: dict,
    metadata_result: dict,
    templates_dir: str,
) -> dict:
    
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
        ocr_text = _extract_ocr_text(ocr_result)

        if not ocr_text.strip():
            neutral["error"] = (
                "No OCR text available for template matching."
            )
            return neutral

        doc_type = detect_doc_type(ocr_text, templates_dir)

        if doc_type is None:
            return neutral

        templates = _load_templates(templates_dir)
        matched_template = None

        for tmpl in templates:
            if tmpl.get("doc_type") == doc_type:
                matched_template = tmpl
                break

        if matched_template is None:
            return neutral

        text_lower = ocr_text.lower()
        keywords_section = matched_template.get("keywords", {})
        required_keywords = keywords_section.get("required", [])

        found, missing = _count_keyword_matches(
            text_lower, required_keywords
        )

        issues: list[str] = []

        for kw in missing:
            issues.append(
                f"Expected keyword '{kw}' not found in "
                f"document — required for {doc_type} "
                f"documents."
            )

        meta_issues = _check_metadata_hints(
            matched_template, metadata_result
        )
        issues.extend(meta_issues)
        
        if required_keywords:
            confidence = len(found) / len(required_keywords)
        else:
            confidence = 1.0

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
