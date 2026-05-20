from __future__ import annotations

import fitz  
_DEFAULT_SUSPICIOUS_FONTS: list[str] = [
    "courier",
    "comic sans",
    "wingdings",
    "zapfdingbats",
    "symbol",
    "webdings",
    "impact",
]

_MAX_FONTS_PER_PAGE = 4


def inspect_fonts(
    doc: fitz.Document,
    suspicious_font_names: list[str] | None = None,
) -> dict:
    
    if suspicious_font_names is None:
        suspicious_font_names = _DEFAULT_SUSPICIOUS_FONTS

    default_result: dict = {
        "fonts_found": [],
        "fonts_per_page": [],
        "suspicious_fonts": [],
        "non_embedded_fonts": [],
        "cross_page_inconsistency": False,
        "issues": [],
        "error": None,
    }

    try:
        page_count = len(doc)
        if page_count == 0:
            default_result["error"] = "Document has no pages."
            return default_result

        all_font_names: set[str] = set()
        fonts_per_page: list[int] = []
        per_page_font_sets: list[set[str]] = []
        non_embedded: set[str] = set()

        for page_idx in range(page_count):
            page = doc[page_idx]

            page_fonts = page.get_fonts(full=True)

            page_font_names: set[str] = set()

            for font_entry in page_fonts:
                
                basefont = (
                    font_entry[3]
                    if len(font_entry) > 3 and font_entry[3]
                    else ""
                )
                name = (
                    font_entry[4]
                    if len(font_entry) > 4 and font_entry[4]
                    else ""
                )

                font_label = basefont or name or "Unknown"

                if "+" in font_label:
                    font_label = font_label.split("+", 1)[1]

                page_font_names.add(font_label)
                all_font_names.add(font_label)
                
                font_type = (
                    font_entry[2]
                    if len(font_entry) > 2 and font_entry[2]
                    else ""
                )
                xref = (
                    font_entry[0]
                    if len(font_entry) > 0
                    else 0
                )

                encoding = (
                    font_entry[5]
                    if len(font_entry) > 5 and font_entry[5]
                    else ""
                )

                if (
                    not encoding
                    and font_type != "Type3"
                    and xref == 0
                ):
                    non_embedded.add(font_label)

            fonts_per_page.append(len(page_font_names))
            per_page_font_sets.append(page_font_names)

        sorted_fonts = sorted(all_font_names)
        sorted_non_embedded = sorted(non_embedded)

        issues: list[str] = []

        for page_idx, count in enumerate(fonts_per_page):
            if count > _MAX_FONTS_PER_PAGE:
                issues.append(
                    f"Page {page_idx + 1} uses {count} "
                    f"distinct fonts — genuine documents "
                    f"rarely exceed {_MAX_FONTS_PER_PAGE}."
                )

        matched_suspicious: list[str] = []

        for font_name in sorted_fonts:
            font_lower = font_name.lower()
            for suspect in suspicious_font_names:
                if suspect.lower() in font_lower:
                    matched_suspicious.append(font_name)
                    break

        if matched_suspicious:
            names_str = ", ".join(matched_suspicious)
            issues.append(
                f"Suspicious font(s) detected: {names_str}. "
                f"These are not typically found in official "
                f"government or institutional documents."
            )

        if sorted_non_embedded:
            names_str = ", ".join(sorted_non_embedded)
            issues.append(
                f"Non-embedded font(s) found: {names_str}. "
                f"Official documents typically embed all "
                f"fonts to ensure consistent rendering."
            )

        cross_page_flag = _check_cross_page_inconsistency(
            per_page_font_sets
        )

        if cross_page_flag:
            issues.append(
                "Font usage varies significantly between "
                "pages — this may indicate pages were "
                "sourced from different documents."
            )

        return {
            "fonts_found": sorted_fonts,
            "fonts_per_page": fonts_per_page,
            "suspicious_fonts": matched_suspicious,
            "non_embedded_fonts": sorted_non_embedded,
            "cross_page_inconsistency": cross_page_flag,
            "issues": issues,
            "error": None,
        }

    except Exception as exc:
        return {
            "fonts_found": [],
            "fonts_per_page": [],
            "suspicious_fonts": [],
            "non_embedded_fonts": [],
            "cross_page_inconsistency": False,
            "issues": [],
            "error": f"Font inspection failed: {exc}",
        }

def _check_cross_page_inconsistency(
    per_page_font_sets: list[set[str]],
) -> bool:
    
    if len(per_page_font_sets) < 2:
        return False

    for i in range(len(per_page_font_sets) - 1):
        current_page = per_page_font_sets[i]
        next_page = per_page_font_sets[i + 1]
        new_fonts = next_page - current_page

        if len(new_fonts) > 2:
            return True

    all_fonts = set()
    total_per_page = 0

    for page_set in per_page_font_sets:
        all_fonts.update(page_set)
        total_per_page += len(page_set)

    avg_per_page = total_per_page / len(per_page_font_sets)

    if len(all_fonts) > avg_per_page * 2 and len(all_fonts) >= 4:
        return True

    return False
