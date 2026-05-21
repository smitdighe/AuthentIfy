from __future__ import annotations

import datetime
import re

from config import Config
from utils import pdf_utils
from forensics import font_inspector
from forensics import digital_signature

def _parse_pdf_date(date_str: str) -> datetime.datetime | None:
    
    if not date_str or not date_str.strip():
        return None

    cleaned = date_str.strip()

    if cleaned.startswith("D:"):
        cleaned = cleaned[2:]

    cleaned = cleaned.replace("'", "")

    formats = [
        "%Y%m%d%H%M%S%z",
        "%Y%m%d%H%M%S",
        "%Y%m%d%H%M",
        "%Y%m%d",
        "%Y%m",
        "%Y",
    ]

    for fmt in formats:
        try:
            return datetime.datetime.strptime(cleaned[:len(fmt) * 2], fmt)
        except (ValueError, IndexError):
            continue

    match = re.match(r"(\d{4})(\d{2})?(\d{2})?", cleaned)
    if match:
        try:
            year = int(match.group(1))
            month = int(match.group(2)) if match.group(2) else 1
            day = int(match.group(3)) if match.group(3) else 1
            return datetime.datetime(year, month, day)
        except (ValueError, OverflowError):
            return None

    return None

def _check_missing_author(metadata: dict) -> str | None:
    
    author = metadata.get("author", "").strip()
    if not author:
        return (
            "Author field is missing — genuine documents "
            "always identify the issuer."
        )
    return None

def _check_missing_creation_date(metadata: dict) -> str | None:
    
    creation_date = metadata.get("creationDate", "").strip()
    if not creation_date:
        return (
            "Creation date is absent — official documents "
            "always record when they were generated."
        )
    return None

def _check_date_logic(metadata: dict) -> str | None:
    
    creation_str = metadata.get("creationDate", "").strip()
    mod_str = metadata.get("modDate", "").strip()

    if not creation_str or not mod_str:
        return None

    creation_dt = _parse_pdf_date(creation_str)
    mod_dt = _parse_pdf_date(mod_str)

    if creation_dt is None or mod_dt is None:
        return None

    creation_naive = creation_dt.replace(tzinfo=None)
    mod_naive = mod_dt.replace(tzinfo=None)

    if mod_naive < creation_naive:
        return (
            "Modification date precedes creation date — "
            "this is a logical impossibility indicating "
            "tampering."
        )

    return None

def _check_suspicious_producer(metadata: dict) -> str | None:
    
    producer = metadata.get("producer", "").strip()
    if not producer:
        return None

    producer_lower = producer.lower()

    for suspicious in Config.SUSPICIOUS_PRODUCERS:
        if suspicious.lower() in producer_lower:
            return (
                f"Document was produced by '{producer}' — "
                f"a tool not used by official issuers."
            )

    return None

def _check_suspicious_creator(metadata: dict) -> str | None:
    
    creator = metadata.get("creator", "").strip()
    if not creator:
        return None

    creator_lower = creator.lower()

    for suspicious in Config.SUSPICIOUS_CREATORS:
        if suspicious.lower() in creator_lower:
            return (
                f"Document creator tool '{creator}' is not "
                f"associated with government document "
                f"generation."
            )

    return None

def _check_stripped_metadata(metadata: dict) -> str | None:
    
    author = metadata.get("author", "").strip()
    producer = metadata.get("producer", "").strip()
    creator = metadata.get("creator", "").strip()
    creation_date = metadata.get("creationDate", "").strip()

    if not author and not producer and not creator and not creation_date:
        return (
            "All metadata has been stripped — this is a "
            "strong indicator of deliberate tampering."
        )

    return None

def _run_font_inspection(doc) -> dict:
    
    try:
        return font_inspector.inspect_fonts(doc)
    except Exception:
        return {"issues": [], "fonts": []}

def _run_signature_check(doc) -> dict:
    
    try:
        return digital_signature.check_signatures(doc)
    except Exception:
        return {
            "is_suspicious": False,
            "issues": [],
            "signatures": [],
        }

def analyze_metadata(pdf_path: str) -> dict:
    doc = None
    try:
        doc = pdf_utils.open_pdf(pdf_path)

        if doc is None:
            return {
                "issues": [],
                "issue_count": 0,
                "raw_metadata": {},
                "font_data": {},
                "signature_data": {},
                "error": (
                    f"Failed to open PDF: '{pdf_path}'. "
                    f"File may be missing, corrupt, or encrypted."
                ),
            }

        metadata = pdf_utils.extract_metadata(doc)
        issues: list[str] = []

        metadata_checks = [
            _check_missing_author,
            _check_missing_creation_date,
            _check_date_logic,
            _check_suspicious_producer,
            _check_suspicious_creator,
            _check_stripped_metadata,
        ]

        for check_fn in metadata_checks:
            issue = check_fn(metadata)
            if issue is not None:
                issues.append(issue)

        font_data = _run_font_inspection(doc)
        font_issues = font_data.get("issues", [])
        issues.extend(font_issues)
        signature_data = _run_signature_check(doc)

        if signature_data.get("is_suspicious", False):
            sig_issues = signature_data.get("issues", [])
            issues.extend(sig_issues)

        return {
            "issues": issues,
            "issue_count": len(issues),
            "raw_metadata": metadata,
            "font_data": font_data,
            "signature_data": signature_data,
            "error": None,
        }

    except Exception as exc:
        return {
            "issues": [],
            "issue_count": 0,
            "raw_metadata": {},
            "font_data": {},
            "signature_data": {},
            "error": f"Metadata analysis failed: {exc}",
        }

    finally:
        pdf_utils.close_pdf(doc)
