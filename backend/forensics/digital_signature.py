from __future__ import annotations

import fitz

def check_signatures(doc: fitz.Document) -> dict:
    
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

        signatures: list[dict] = []

        for page_idx in range(page_count):
            page = doc[page_idx]

            widget = page.first_widget
            while widget is not None:
                if widget.field_type == fitz.PDF_WIDGET_TYPE_SIG:
                    sig_info = _extract_signature_info(
                        widget, page_idx
                    )
                    signatures.append(sig_info)

                widget = widget.next

        sig_count = len(signatures)

        if sig_count == 0:
            return default_result

        has_invalid = any(
            not sig.get("valid", False) for sig in signatures
        )

        has_valid = any(
            sig.get("valid", False) for sig in signatures
        )

        if has_invalid:
            status = "invalid"
        elif has_valid:
            status = "valid"
        else:
            status = "invalid"

        is_suspicious = status == "invalid"

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
        return {
            "signature_count": 0,
            "status": "unsigned",
            "signatures": [],
            "is_suspicious": False,
            "issues": [],
            "error": f"Signature check failed: {exc}",
        }


def _extract_signature_info(
    widget: fitz.Widget,
    page_idx: int,
) -> dict:
    
    field_name = widget.field_name or "Unknown"

    signer = "Unknown"
    signing_date = ""
    is_valid = False

    try:
        field_value = widget.field_value or ""

        if field_value:
            is_valid = True  
            
        xref = widget.xref
        if xref and xref > 0:
            sig_dict = _read_sig_dict(widget, xref)
            signer = sig_dict.get("signer", signer)
            signing_date = sig_dict.get("date", signing_date)

            if sig_dict.get("reason"):
                signer = (
                    f"{signer} "
                    f"(Reason: {sig_dict['reason']})"
                )

    except Exception:
        pass

    return {
        "signer": signer,
        "date": signing_date,
        "valid": is_valid,
        "field_name": field_name,
        "page": page_idx + 1,  
    }


def _read_sig_dict(
    widget: fitz.Widget,
    xref: int,
) -> dict:
    
    result: dict = {}

    try:
        doc = widget.parent.parent
        v_type, v_val = doc.xref_get_key(xref, "V")
        if v_type == "xref":
            sig_xref = int(v_val.split()[0])

            n_type, n_val = doc.xref_get_key(
                sig_xref, "Name"
            )
            if n_type == "string" and n_val:
                result["signer"] = _clean_pdf_string(n_val)

            m_type, m_val = doc.xref_get_key(sig_xref, "M")
            if m_type == "string" and m_val:
                result["date"] = _clean_pdf_string(m_val)

            r_type, r_val = doc.xref_get_key(
                sig_xref, "Reason"
            )
            if r_type == "string" and r_val:
                result["reason"] = _clean_pdf_string(r_val)

    except Exception:
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
    
    if cleaned.startswith("(") and cleaned.endswith(")"):
        cleaned = cleaned[1:-1]

    return cleaned.strip()
