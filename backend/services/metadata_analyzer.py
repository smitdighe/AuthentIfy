# ============================================================
# services/metadata_analyzer.py — AuthentIfy Backend
# Project: AuthentIfy — "Verify before you trust."
# Role   : Interprets raw PDF metadata, applies forensic
#          checks, and produces human-readable issue strings.
#
# This is a SERVICE file — it calls utility and forensics
# modules, applies thresholds from Config, and returns a
# structured result dict. It does NOT implement low-level
# algorithms.
#
# Calls  : utils.pdf_utils, forensics.font_inspector,
#           forensics.digital_signature
# Called  : routes/analyze.py
# Config : Config.SUSPICIOUS_PRODUCERS,
#          Config.SUSPICIOUS_CREATORS,
#          Config.DEDUCT_METADATA_ISSUE
# ============================================================

from __future__ import annotations

import datetime
import re

from config import Config
from utils import pdf_utils
from forensics import font_inspector
from forensics import digital_signature


# ── Date Parsing ──────────────────────────────────────────────


def _parse_pdf_date(date_str: str) -> datetime.datetime | None:
    """Parse a PDF date string into a datetime object.

    PDF dates follow the format:
        D:YYYYMMDDHHmmSSOHH'mm'
    where everything after YYYY is optional.

    Args:
        date_str: Raw PDF date string (e.g. "D:20230415120000+05'30'").

    Returns:
        datetime.datetime on success, None if unparseable or empty.
    """
    if not date_str or not date_str.strip():
        return None

    cleaned = date_str.strip()

    # Strip the leading "D:" prefix if present
    if cleaned.startswith("D:"):
        cleaned = cleaned[2:]

    # Remove apostrophes used in timezone offset (e.g. +05'30')
    cleaned = cleaned.replace("'", "")

    # Try progressively shorter format patterns
    formats = [
        "%Y%m%d%H%M%S%z",   # Full with timezone
        "%Y%m%d%H%M%S",     # Full without timezone
        "%Y%m%d%H%M",       # No seconds
        "%Y%m%d",           # Date only
        "%Y%m",             # Year + month
        "%Y",               # Year only
    ]

    for fmt in formats:
        try:
            return datetime.datetime.strptime(cleaned[:len(fmt) * 2], fmt)
        except (ValueError, IndexError):
            continue

    # Fallback: extract at least a year with regex
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


# ── Individual Metadata Checks ───────────────────────────────


def _check_missing_author(metadata: dict) -> str | None:
    """CHECK 1 — Flag if the author field is empty or absent.

    Genuine government documents always identify the issuing
    authority or individual in the author field.

    Args:
        metadata: Normalized PDF metadata dict.

    Returns:
        Issue string if author is missing, None otherwise.
    """
    author = metadata.get("author", "").strip()
    if not author:
        return (
            "Author field is missing — genuine documents "
            "always identify the issuer."
        )
    return None


def _check_missing_creation_date(metadata: dict) -> str | None:
    """CHECK 2 — Flag if the creation date is empty or absent.

    Official documents always record their generation timestamp.

    Args:
        metadata: Normalized PDF metadata dict.

    Returns:
        Issue string if creation date is missing, None otherwise.
    """
    creation_date = metadata.get("creationDate", "").strip()
    if not creation_date:
        return (
            "Creation date is absent — official documents "
            "always record when they were generated."
        )
    return None


def _check_date_logic(metadata: dict) -> str | None:
    """CHECK 3 — Flag if modification date precedes creation date.

    A document cannot be modified before it was created. This
    temporal impossibility is a strong indicator of metadata
    manipulation.

    Args:
        metadata: Normalized PDF metadata dict.

    Returns:
        Issue string if dates are logically impossible,
        None otherwise.
    """
    creation_str = metadata.get("creationDate", "").strip()
    mod_str = metadata.get("modDate", "").strip()

    if not creation_str or not mod_str:
        return None  # Cannot compare if either is missing

    creation_dt = _parse_pdf_date(creation_str)
    mod_dt = _parse_pdf_date(mod_str)

    if creation_dt is None or mod_dt is None:
        return None  # Cannot compare unparseable dates

    # Strip timezone info for safe comparison
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
    """CHECK 4 — Flag if the producer matches a suspicious tool.

    Genuine government PDFs are produced by enterprise-grade
    tools (Adobe Acrobat, Oracle, SAP). Consumer/online tools
    suggest the document was re-created or altered.

    Matching is case-insensitive substring.

    Args:
        metadata: Normalized PDF metadata dict.

    Returns:
        Issue string if producer is suspicious, None otherwise.
    """
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
    """CHECK 5 — Flag if the creator matches a suspicious tool.

    Similar to producer check, but targets the creator field
    which identifies the application that originally generated
    the document content.

    Matching is case-insensitive substring.

    Args:
        metadata: Normalized PDF metadata dict.

    Returns:
        Issue string if creator is suspicious, None otherwise.
    """
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
    """CHECK 6 — Flag if ALL key metadata fields are empty.

    When author, producer, creator, AND creationDate are all
    absent, the metadata has likely been deliberately stripped
    to hide provenance — a strong tampering indicator.

    Args:
        metadata: Normalized PDF metadata dict.

    Returns:
        Issue string if all metadata is stripped, None otherwise.
    """
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


# ── Font & Signature Delegation ──────────────────────────────


def _run_font_inspection(doc) -> dict:
    """CHECK 7 — Delegate font anomaly detection to font_inspector.

    Calls forensics.font_inspector.inspect_fonts() and returns
    its raw result. Any issues found are folded into the main
    issues list by the caller.

    Args:
        doc: An open fitz.Document.

    Returns:
        dict with keys "issues" (list[str]) and any raw font data.
        Returns safe default on error.
    """
    try:
        return font_inspector.inspect_fonts(doc)
    except Exception:
        return {"issues": [], "fonts": []}


def _run_signature_check(doc) -> dict:
    """CHECK 8 — Delegate digital signature verification.

    Calls forensics.digital_signature.check_signatures() and
    returns its raw result. If is_suspicious is True, the
    issues are folded into the main issues list by the caller.

    Args:
        doc: An open fitz.Document.

    Returns:
        dict with keys "is_suspicious" (bool), "issues" (list[str]),
        and any raw signature data. Returns safe default on error.
    """
    try:
        return digital_signature.check_signatures(doc)
    except Exception:
        return {
            "is_suspicious": False,
            "issues": [],
            "signatures": [],
        }


# ── Main Analysis Entry Point ────────────────────────────────


def analyze_metadata(pdf_path: str) -> dict:
    """Perform comprehensive metadata forensic analysis on a PDF.

    Orchestrates all metadata checks, font inspection, and
    digital signature verification into a single result dict.

    Processing steps:
        1. Open PDF safely via pdf_utils.open_pdf()
        2. Extract metadata via pdf_utils.extract_metadata()
        3. Run all 6 metadata checks (author, dates, producer,
           creator, stripped metadata)
        4. Run font_inspector, fold in its issues
        5. Run digital_signature check, fold in its issues
        6. Close PDF via pdf_utils.close_pdf() (always, via finally)
        7. Build and return result dict

    Args:
        pdf_path: Absolute or relative path to the PDF file.

    Returns:
        dict with keys:
            issues         (list[str])  — Human-readable issues
            issue_count    (int)        — len(issues)
            raw_metadata   (dict)       — Raw metadata for transparency
            font_data      (dict)       — Raw font_inspector output
            signature_data (dict)       — Raw digital_signature output
            error          (None|str)   — Error string on total failure
    """
    doc = None

    try:
        # ── STEP 1: Open PDF ─────────────────────────────────
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

        # ── STEP 2: Extract metadata ────────────────────────
        metadata = pdf_utils.extract_metadata(doc)

        # ── STEP 3: Run all 6 metadata checks ───────────────
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

        # ── STEP 4: Run font inspection ─────────────────────
        font_data = _run_font_inspection(doc)
        font_issues = font_data.get("issues", [])
        issues.extend(font_issues)

        # ── STEP 5: Run digital signature check ─────────────
        signature_data = _run_signature_check(doc)

        if signature_data.get("is_suspicious", False):
            sig_issues = signature_data.get("issues", [])
            issues.extend(sig_issues)

        # ── STEP 7: Build result ────────────────────────────
        return {
            "issues": issues,
            "issue_count": len(issues),
            "raw_metadata": metadata,
            "font_data": font_data,
            "signature_data": signature_data,
            "error": None,
        }

    except Exception as exc:
        # Total failure — return error, never crash
        return {
            "issues": [],
            "issue_count": 0,
            "raw_metadata": {},
            "font_data": {},
            "signature_data": {},
            "error": f"Metadata analysis failed: {exc}",
        }

    finally:
        # ── STEP 6: Always close the PDF ────────────────────
        pdf_utils.close_pdf(doc)
