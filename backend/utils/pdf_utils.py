from __future__ import annotations

import os
import fitz  # PyMuPDF — pip install PyMuPDF

from utils.image_utils import pixmap_to_pil, save_image

def open_pdf(pdf_path: str) -> fitz.Document | None:
    
    if not os.path.isfile(pdf_path):
        return None

    try:
        doc = fitz.open(pdf_path)
        if doc.is_encrypted:
            doc.close()
            return None
        return doc

    except (fitz.FileDataError, RuntimeError, OSError):
        return None

def close_pdf(doc: fitz.Document) -> None:

    try:
        if doc is not None:
            doc.close()
    except (RuntimeError, AttributeError):
        pass

def get_page_count(doc: fitz.Document) -> int:

    try:
        if doc is None:
            return 0
        return doc.page_count
    except (RuntimeError, AttributeError):
        return 0

def render_page(
    doc: fitz.Document,
    page_num: int,
    dpi: int = 200,
) -> fitz.Pixmap | None:

    try:
        if doc is None or page_num < 0:
            return None
        if page_num >= doc.page_count:
            return None
        scale = dpi / 72.0
        matrix = fitz.Matrix(scale, scale)
        page = doc.load_page(page_num)
        pixmap = page.get_pixmap(matrix=matrix, alpha=False)
        return pixmap
    except (RuntimeError, ValueError, IndexError):
        return None

def render_all_pages(
    pdf_path: str,
    output_dir: str,
    dpi: int = 200,
) -> list[str]:

    saved_paths: list[str] = []
    doc = open_pdf(pdf_path)

    if doc is None:
        return saved_paths
    try:
        os.makedirs(output_dir, exist_ok=True)
        for page_num in range(doc.page_count):
            pixmap = render_page(doc, page_num, dpi)
            if pixmap is None:
                continue
            pil_img = pixmap_to_pil(pixmap)
            if pil_img is None:
                continue
            filename = f"page_{page_num:03d}.png"
            save_path = os.path.join(output_dir, filename)
            if save_image(pil_img, save_path):
                saved_paths.append(save_path)
    finally:
        close_pdf(doc)
    return saved_paths

def extract_metadata(doc: fitz.Document) -> dict:

    try:
        if doc is None:
            return {}
        raw_meta = doc.metadata
        if raw_meta is None:
            return {}
        return {
            key: (value if value is not None else "")
            for key, value in raw_meta.items()
        }
    except (RuntimeError, AttributeError):
        return {}

def extract_fonts(doc: fitz.Document) -> list[dict]:

    fonts: list[dict] = []
    try:
        if doc is None:
            return fonts
        for page_num in range(doc.page_count):
            page = doc.load_page(page_num)
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

def extract_annotations(doc: fitz.Document) -> list[dict]:

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

def is_encrypted(pdf_path: str) -> bool:

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
