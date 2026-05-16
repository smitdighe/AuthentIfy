# ============================================================
# utils/pdf_utils.py — AuthentIfy Backend
# Project: AuthentIfy — "Verify before you trust."
# Role   : Centralized PyMuPDF (fitz) operations for the
#          document forensics pipeline.
#
# This is a PURE utility module — no analysis logic, no
# scoring, no Flask routes. Only PDF open/render/extract
# operations live here.
#
# No other file should call fitz directly for basic PDF
# operations. Everything goes through these helpers.
#
# Consumers: services/metadata_analyzer.py,
#            services/ela_analyzer.py,
#            services/ocr_extractor.py,
#            forensics/font_inspector.py,
#            forensics/digital_signature.py
# ============================================================

from __future__ import annotations

import os

import fitz  # PyMuPDF — pip install PyMuPDF

from utils.image_utils import pixmap_to_pil, save_image


# ── PDF Open / Close ──────────────────────────────────────────


def open_pdf(pdf_path: str) -> fitz.Document | None:
    """Safely open a PDF file and return the fitz.Document.

    Checks that the file exists on disk before attempting to
    open. If the PDF is encrypted (password-protected), it is
    rejected — AuthentIfy cannot analyze locked documents.

    Args:
        pdf_path: Absolute or relative path to the PDF file.

    Returns:
        fitz.Document on success, None on any failure
        (missing file, encrypted, corrupt).
    """
    if not os.path.isfile(pdf_path):
        return None

    try:
        doc = fitz.open(pdf_path)

        # Reject password-protected PDFs — cannot analyze
        if doc.is_encrypted:
            doc.close()
            return None

        return doc

    except (fitz.FileDataError, RuntimeError, OSError):
        # FileDataError: corrupt or unreadable PDF
        # RuntimeError:  MuPDF internal failure
        # OSError:       filesystem-level failure
        return None


def close_pdf(doc: fitz.Document) -> None:
    """Safely close a fitz.Document. Never raises.

    Safe to call in finally blocks or cleanup routines.
    Silently handles None input and already-closed documents.

    Args:
        doc: A fitz.Document to close, or None.
    """
    try:
        if doc is not None:
            doc.close()
    except (RuntimeError, AttributeError):
        # RuntimeError:   document already closed
        # AttributeError: doc is not a valid Document object
        pass


# ── Page Count ────────────────────────────────────────────────


def get_page_count(doc: fitz.Document) -> int:
    """Return the number of pages in the document.

    Args:
        doc: An open fitz.Document.

    Returns:
        Page count as int. Returns 0 on error or None input.
    """
    try:
        if doc is None:
            return 0
        return doc.page_count
    except (RuntimeError, AttributeError):
        return 0


# ── Single-Page Rendering ────────────────────────────────────


def render_page(
    doc: fitz.Document,
    page_num: int,
    dpi: int = 200,
) -> fitz.Pixmap | None:
    """Render a single PDF page to a fitz.Pixmap at a given DPI.

    DPI-to-matrix calculation:
        PDF base resolution is 72 DPI. To render at a target DPI,
        we scale by (target_dpi / 72). For example:
            200 DPI → scale = 200/72 ≈ 2.78× magnification
        This scale is applied to both X and Y axes via fitz.Matrix.

    Args:
        doc:      An open fitz.Document.
        page_num: Zero-based page index.
        dpi:      Target render resolution (default 200).

    Returns:
        fitz.Pixmap (RGB) on success, None on failure.
    """
    try:
        if doc is None or page_num < 0:
            return None

        if page_num >= doc.page_count:
            return None

        # Scale factor: target DPI / PDF base DPI (72)
        scale = dpi / 72.0
        matrix = fitz.Matrix(scale, scale)

        page = doc.load_page(page_num)
        pixmap = page.get_pixmap(matrix=matrix, alpha=False)

        return pixmap

    except (RuntimeError, ValueError, IndexError):
        return None


# ── Render All Pages ──────────────────────────────────────────


def render_all_pages(
    pdf_path: str,
    output_dir: str,
    dpi: int = 200,
) -> list[str]:
    """Open a PDF, render every page as PNG, save to output_dir.

    Filename format: page_000.png, page_001.png, ...
    Pages that fail to render are skipped — the remaining
    pages are still processed.

    Args:
        pdf_path:   Path to the PDF file.
        output_dir: Directory to save rendered page images.
        dpi:        Target render resolution (default 200).

    Returns:
        List of saved file paths (may be shorter than page count
        if some pages failed). Empty list on total failure.
    """
    saved_paths: list[str] = []
    doc = open_pdf(pdf_path)

    if doc is None:
        return saved_paths

    try:
        # Ensure the output directory exists
        os.makedirs(output_dir, exist_ok=True)

        for page_num in range(doc.page_count):
            pixmap = render_page(doc, page_num, dpi)

            if pixmap is None:
                continue  # Skip failed pages, keep going

            pil_img = pixmap_to_pil(pixmap)

            if pil_img is None:
                continue

            # Zero-padded filename: page_000.png, page_001.png, ...
            filename = f"page_{page_num:03d}.png"
            save_path = os.path.join(output_dir, filename)

            if save_image(pil_img, save_path):
                saved_paths.append(save_path)

    finally:
        close_pdf(doc)

    return saved_paths


# ── Metadata Extraction ──────────────────────────────────────


def extract_metadata(doc: fitz.Document) -> dict:
    """Extract the raw metadata dictionary from a PDF document.

    PyMuPDF's doc.metadata may contain None values for missing
    fields. This function normalizes all None values to empty
    strings so downstream code can safely use string methods.

    Standard metadata keys returned by PyMuPDF:
        producer, creator, title, author, subject, keywords,
        creationDate, modDate, format, encryption

    Args:
        doc: An open fitz.Document.

    Returns:
        dict with string values. Never returns None.
        Returns empty dict on error.
    """
    try:
        if doc is None:
            return {}

        raw_meta = doc.metadata

        if raw_meta is None:
            return {}

        # Normalize None values → empty strings
        return {
            key: (value if value is not None else "")
            for key, value in raw_meta.items()
        }

    except (RuntimeError, AttributeError):
        return {}


# ── Font Extraction ───────────────────────────────────────────


def extract_fonts(doc: fitz.Document) -> list[dict]:
    """Extract font information from every page in the document.

    Iterates through all pages and collects each font's name,
    encoding flags, and the page it appears on. Useful for
    detecting inconsistent fonts that suggest splicing.

    Args:
        doc: An open fitz.Document.

    Returns:
        List of dicts, each containing:
            {"name": str, "flags": int, "page": int}
        Returns empty list on error.
    """
    fonts: list[dict] = []

    try:
        if doc is None:
            return fonts

        for page_num in range(doc.page_count):
            page = doc.load_page(page_num)

            # get_fonts() returns list of tuples:
            # (xref, ext, type, basefont, name, encoding, ...)
            for font_tuple in page.get_fonts():
                font_entry = {
                    "name": font_tuple[3] if len(font_tuple) > 3 else "",
                    "flags": font_tuple[0] if len(font_tuple) > 0 else 0,
                    "page": page_num,
                }
                fonts.append(font_entry)

    except (RuntimeError, IndexError, AttributeError):
        pass

    return fonts


# ── Annotation Extraction ────────────────────────────────────


def extract_annotations(doc: fitz.Document) -> list[dict]:
    """Extract all annotations from every page in the document.

    Annotations can indicate editing activity — stamps, sticky
    notes, redactions, and highlight overlays are common signs
    of post-creation modification.

    Args:
        doc: An open fitz.Document.

    Returns:
        List of dicts, each containing:
            {"type": str, "page": int, "rect": list[float]}
        Returns empty list on error.
    """
    annotations: list[dict] = []

    try:
        if doc is None:
            return annotations

        for page_num in range(doc.page_count):
            page = doc.load_page(page_num)

            for annot in page.annots() or []:
                annot_entry = {
                    "type": annot.type[1] if annot.type else "Unknown",
                    "page": page_num,
                    "rect": list(annot.rect),
                }
                annotations.append(annot_entry)

    except (RuntimeError, AttributeError):
        pass

    return annotations


# ── Encryption Check ──────────────────────────────────────────


def is_encrypted(pdf_path: str) -> bool:
    """Check whether a PDF file is password-protected.

    Opens the file just long enough to read the encryption flag,
    then immediately closes it. Does NOT attempt to decrypt.

    Args:
        pdf_path: Path to the PDF file.

    Returns:
        True if the PDF is encrypted (password-required).
        False if unencrypted, missing, or unreadable.
    """
    if not os.path.isfile(pdf_path):
        return False

    doc = None
    try:
        doc = fitz.open(pdf_path)
        return doc.is_encrypted

    except (fitz.FileDataError, RuntimeError, OSError):
        return False

    finally:
        if doc is not None:
            try:
                doc.close()
            except RuntimeError:
                pass
