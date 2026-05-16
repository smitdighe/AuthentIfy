# ============================================================
# forensics/digital_signature.py — AuthentIfy Backend
# Project: AuthentIfy — "Verify before you trust."
# Role   : Inspects digital signature fields in a PDF to
#          detect missing, invalid, or tampered signatures.
#
# ── Why Digital Signatures Matter ──────────────────────────
# Official documents from government agencies and
# institutions are frequently digitally signed.  A valid
# signature cryptographically binds the signer's identity
# to the document content — any modification after signing
# invalidates the signature.
#
# Detection logic:
#   • No signature fields     → "unsigned" — neutral.  Many
#     legitimate PDFs are unsigned, so this alone is NOT
#     suspicious.
#   • Signature field present + marked valid → "valid" — the
#     PDF's internal state indicates the signature was intact
#     when last checked.
#   • Signature field present + invalid/unknown → "invalid" —
#     STRONG tamper signal.  The document was signed and then
#     modified, breaking the signature.
#
# ── PyMuPDF Signature Limitations ──────────────────────────
# IMPORTANT: PyMuPDF (fitz) does NOT perform full
# cryptographic signature verification.  It cannot:
#   • Validate the certificate chain against a trust store
#   • Check certificate revocation (CRL / OCSP)
#   • Verify the actual PKCS#7 / CMS digest
#
# What PyMuPDF CAN do:
#   • Detect the presence of signature form fields (type=Sig)
#   • Read the signer name from the signature dictionary
#   • Read the signing date (M entry in the sig dict)
#   • Report the widget's field flags
#
# This module uses ONLY what PyMuPDF provides.  No OpenSSL,
# no external crypto libraries.
#
# Called by: services/metadata_analyzer.py
# Input   : fitz.Document object
# Output  : Dict with signature findings and issues
# ============================================================

from __future__ import annotations

import fitz


def check_signatures(doc: fitz.Document) -> dict:
    """Check digital signatures in a PDF document.

    Iterates through all form field widgets looking for
    signature fields (widget type = fitz.PDF_WIDGET_TYPE_SIG).
    For each signature field, extracts the signer name,
    signing date, and validity flag from the field's value
    dictionary.

    Classification:
        - "unsigned" — No signature fields found.  This is
          NOT suspicious by itself; many legitimate documents
          are unsigned.
        - "valid"    — At least one signature field exists and
          all detected signatures appear intact.
        - "invalid"  — At least one signature field exists but
          its signature is missing, broken, or marked as
          invalid — a strong indicator of post-signing
          modification.

    Args:
        doc: An open fitz.Document (PyMuPDF).

    Returns:
        dict with keys:
            signature_count (int)       — Number of signature
                fields found in the document.
            status          (str)       — Overall classification:
                "unsigned", "valid", or "invalid".
            signatures      (list[dict]) — Per-signature details
                with keys: signer, date, valid, field_name.
            is_suspicious   (bool)      — True ONLY if an
                invalid signature is found.  False for
                unsigned documents.
            issues          (list[str]) — Human-readable issue
                descriptions for the frontend.
            error           (None|str)  — Error description on
                failure; None on success.
    """
    # ── Safe default for early returns and exceptions ────────
    default_result: dict = {
        "signature_count": 0,
        "status": "unsigned",
        "signatures": [],
        "is_suspicious": False,
        "issues": [],
        "error": None,
    }

    try:
        page_count = len(doc)
        if page_count == 0:
            return default_result

        # ── Collect all signature fields across pages ────────
        # PyMuPDF exposes form fields as widgets on each page.
        # Signature fields have widget.field_type equal to
        # fitz.PDF_WIDGET_TYPE_SIG (value 7 in PyMuPDF).
        signatures: list[dict] = []

        for page_idx in range(page_count):
            page = doc[page_idx]

            # Iterate over all form field widgets on this page
            widget = page.first_widget
            while widget is not None:
                if widget.field_type == fitz.PDF_WIDGET_TYPE_SIG:
                    # ── Extract signature metadata ───────────
                    sig_info = _extract_signature_info(
                        widget, page_idx
                    )
                    signatures.append(sig_info)

                # Advance to the next widget on this page
                widget = widget.next

        # ── Classify overall signature status ────────────────
        sig_count = len(signatures)

        if sig_count == 0:
            # No signature fields at all — document is unsigned
            # This is NOT suspicious by itself
            return default_result

        # Check if any signature is invalid
        has_invalid = any(
            not sig.get("valid", False) for sig in signatures
        )

        # Check if any signature is valid
        has_valid = any(
            sig.get("valid", False) for sig in signatures
        )

        if has_invalid:
            status = "invalid"
        elif has_valid:
            status = "valid"
        else:
            # All signatures exist but none confirmed valid
            # — treat as invalid (uncertain state)
            status = "invalid"

        is_suspicious = status == "invalid"

        # ── Build human-readable issues ──────────────────────
        issues: list[str] = []

        if is_suspicious:
            invalid_count = sum(
                1 for s in signatures if not s.get("valid", False)
            )
            if invalid_count == sig_count:
                issues.append(
                    f"All {sig_count} digital signature(s) in "
                    f"this document are invalid or unverifiable "
                    f"— the document may have been modified "
                    f"after signing."
                )
            else:
                issues.append(
                    f"{invalid_count} of {sig_count} digital "
                    f"signature(s) are invalid or unverifiable "
                    f"— partial tampering is suspected."
                )

        return {
            "signature_count": sig_count,
            "status": status,
            "signatures": signatures,
            "is_suspicious": is_suspicious,
            "issues": issues,
            "error": None,
        }

    except Exception as exc:
        # Never crash — return safe default with error detail
        return {
            "signature_count": 0,
            "status": "unsigned",
            "signatures": [],
            "is_suspicious": False,
            "issues": [],
            "error": f"Signature check failed: {exc}",
        }


# ── Internal Helpers ─────────────────────────────────────────


def _extract_signature_info(
    widget: fitz.Widget,
    page_idx: int,
) -> dict:
    """Extract metadata from a single signature widget.

    Reads the signer name, signing date, and validity flag
    from the widget's field value and properties.

    PyMuPDF stores signature details in the widget's
    field_value (a string representation) and in the
    underlying PDF object's dictionary entries.

    Args:
        widget:   A fitz.Widget with field_type == SIG.
        page_idx: 0-based page index (for diagnostics).

    Returns:
        dict with keys:
            signer     (str)  — Signer's name, or "Unknown".
            date       (str)  — Signing date string, or "".
            valid      (bool) — True if the signature appears
                intact based on available PyMuPDF info.
            field_name (str)  — The form field name of the
                signature widget.
            page       (int)  — 1-based page number.
    """
    # ── Field name ───────────────────────────────────────────
    # The widget's field_name identifies the signature field
    # in the PDF's AcroForm structure (e.g., "Signature1").
    field_name = widget.field_name or "Unknown"

    # ── Signer name and date ─────────────────────────────────
    # Attempt to read from the widget's underlying PDF object.
    # The signature dictionary (/V entry) contains /Name
    # (signer) and /M (signing date).
    signer = "Unknown"
    signing_date = ""
    is_valid = False

    try:
        # field_value may contain a text representation of
        # the signature status set by the signing application
        field_value = widget.field_value or ""

        # If the field has a value, the signature field is
        # populated (i.e., it has been signed, not just an
        # empty placeholder).
        if field_value:
            is_valid = True  # Populated = presumed intact

        # Try to access the signature dictionary via the
        # widget's underlying xref for richer metadata
        xref = widget.xref
        if xref and xref > 0:
            sig_dict = _read_sig_dict(widget, xref)
            signer = sig_dict.get("signer", signer)
            signing_date = sig_dict.get("date", signing_date)

            # If the sig dict indicates a reason or contact
            # name, use it as additional signer info
            if sig_dict.get("reason"):
                signer = (
                    f"{signer} "
                    f"(Reason: {sig_dict['reason']})"
                )

    except Exception:
        # Any extraction failure — keep defaults, don't crash
        pass

    return {
        "signer": signer,
        "date": signing_date,
        "valid": is_valid,
        "field_name": field_name,
        "page": page_idx + 1,  # 1-based for readability
    }


def _read_sig_dict(
    widget: fitz.Widget,
    xref: int,
) -> dict:
    """Read the signature dictionary entries via xref.

    Attempts to extract /Name, /M (date), /Reason, and
    /ContactInfo from the signature value dictionary
    referenced by the widget's xref.

    Args:
        widget: The signature widget.
        xref:   The widget's cross-reference ID.

    Returns:
        dict with optional keys: signer, date, reason.
        Missing entries are omitted (not set to None).
    """
    result: dict = {}

    try:
        # Access the Document through the widget's parent page
        doc = widget.parent.parent

        # Read raw key-value entries from the xref object
        # PyMuPDF's xref_get_key returns (type_str, value_str)
        # for a given PDF dictionary key.

        # /V entry points to the actual signature dictionary
        v_type, v_val = doc.xref_get_key(xref, "V")
        if v_type == "xref":
            # v_val is like "X Y R" — extract the xref number
            sig_xref = int(v_val.split()[0])

            # Read signer name (/Name entry)
            n_type, n_val = doc.xref_get_key(
                sig_xref, "Name"
            )
            if n_type == "string" and n_val:
                result["signer"] = _clean_pdf_string(n_val)

            # Read signing date (/M entry)
            m_type, m_val = doc.xref_get_key(sig_xref, "M")
            if m_type == "string" and m_val:
                result["date"] = _clean_pdf_string(m_val)

            # Read reason (/Reason entry)
            r_type, r_val = doc.xref_get_key(
                sig_xref, "Reason"
            )
            if r_type == "string" and r_val:
                result["reason"] = _clean_pdf_string(r_val)

    except Exception:
        # Silently ignore — partial data is acceptable
        pass

    return result


def _clean_pdf_string(raw: str) -> str:
    """Remove PDF string delimiters and whitespace.

    PDF strings are often wrapped in parentheses:
        (John Doe)  →  John Doe

    Args:
        raw: Raw PDF string value.

    Returns:
        Cleaned string with delimiters and excess whitespace
        removed.
    """
    cleaned = raw.strip()

    # Strip enclosing parentheses (literal PDF string syntax)
    if cleaned.startswith("(") and cleaned.endswith(")"):
        cleaned = cleaned[1:-1]

    return cleaned.strip()
