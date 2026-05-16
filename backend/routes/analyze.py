# ============================================================
# routes/analyze.py — AuthentIfy Backend
# Project: AuthentIfy — "Verify before you trust."
# Role   : Main API controller — receives a PDF upload, runs
#          the full 6-phase forensic analysis pipeline, and
#          returns a structured JSON verdict.
#
# This is the MOST IMPORTANT file in the project. It
# orchestrates all services in strict sequential order,
# handles errors per-phase (never lets one failure abort
# the pipeline), and guarantees cleanup of uploaded files.
#
# Endpoint: POST /analyze
# Input   : multipart/form-data with field "file" (PDF)
# Output  : JSON verdict with score, reasons, and breakdown
# ============================================================

from __future__ import annotations

import os
from datetime import datetime, timezone

from flask import Blueprint, jsonify, request

from config import Config
from utils import file_handler
from services import metadata_analyzer
from services import ela_analyzer
from services import ocr_extractor
from services import template_matcher
from services import anomaly_detector
from services import score_aggregator


# ── Blueprint Setup ──────────────────────────────────────────

analyze_bp = Blueprint("analyze_bp", __name__)


# ── Console Logging ──────────────────────────────────────────


def _log(message: str) -> None:
    """Print a timestamped log line to the console.

    Makes the demo terminal output visually informative.

    Args:
        message: Log message to print.
    """
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[AuthentIfy {ts}] {message}")


# ── Empty Result Factories ───────────────────────────────────
# Used when a phase fails — provides safe defaults so the
# pipeline can continue to score_aggregator.


def _empty_metadata() -> dict:
    """Return a safe empty metadata result."""
    return {
        "issues": [],
        "issue_count": 0,
        "raw_metadata": {},
        "font_data": {},
        "signature_data": {},
        "error": "Metadata analysis was skipped due to error.",
    }


def _empty_ela() -> dict:
    """Return a safe empty ELA/vision result."""
    return {
        "issues": [],
        "issue_count": 0,
        "page_count": 0,
        "page_image_paths": [],
        "per_page_ela": [],
        "per_page_noise": [],
        "error": "Vision analysis was skipped due to error.",
    }


def _empty_ocr() -> dict:
    """Return a safe empty OCR result."""
    return {
        "issues": [],
        "issue_count": 0,
        "total_text_length": 0,
        "mean_confidence": 0.0,
        "per_page_text": [],
        "per_page_length": [],
        "garble_ratio": 0.0,
        "error": "OCR analysis was skipped due to error.",
    }


def _empty_template() -> dict:
    """Return a safe empty template result."""
    return {
        "issues": [],
        "issue_count": 0,
        "matched": False,
        "template_id": None,
        "error": "Template matching was skipped due to error.",
    }


def _empty_anomaly() -> dict:
    """Return a safe empty anomaly result."""
    return {
        "is_anomaly": False,
        "confidence": 50.0,
        "issues": [],
        "error": "ML analysis was skipped due to error.",
    }


# ── Request Validation ───────────────────────────────────────


def _validate_upload():
    """Validate the incoming file upload request.

    Checks:
        1. A file is present in the request.
        2. The filename is not empty.
        3. The extension is .pdf.

    Returns:
        (file_object, None) on success.
        (None, (error_response, status_code)) on failure.
    """
    # Check 1: file field present
    if "file" not in request.files:
        return None, (
            jsonify({"error": "No file provided"}), 400
        )

    file_obj = request.files["file"]

    # Check 2: filename not empty
    if not file_obj.filename or file_obj.filename.strip() == "":
        return None, (
            jsonify({"error": "Empty filename"}), 400
        )

    # Check 3: extension is PDF
    if not file_handler.validate_extension(file_obj.filename):
        return None, (
            jsonify({"error": "Only PDF files are accepted"}),
            415,
        )

    return file_obj, None


# ── Serialization Helper ─────────────────────────────────────


def _make_serializable(result: dict) -> dict:
    """Strip non-JSON-serializable values from a result dict.

    Removes PIL Image objects, NumPy arrays, and any other
    types that json.dumps cannot handle. Replaces them with
    placeholder strings.

    Args:
        result: A service result dict.

    Returns:
        A copy safe for JSON serialization.
    """
    import numpy as np
    from PIL import Image

    clean = {}
    for key, value in result.items():
        if isinstance(value, Image.Image):
            clean[key] = "<PIL.Image>"
        elif isinstance(value, np.ndarray):
            clean[key] = "<numpy.ndarray>"
        elif isinstance(value, dict):
            clean[key] = _make_serializable(value)
        elif isinstance(value, list):
            clean[key] = [
                _make_serializable(v) if isinstance(v, dict)
                else (
                    "<non-serializable>"
                    if isinstance(v, (Image.Image, np.ndarray))
                    else v
                )
                for v in value
            ]
        else:
            clean[key] = value
    return clean


# ── Main Endpoint ────────────────────────────────────────────


@analyze_bp.route("/analyze", methods=["POST"])
def analyze():
    """POST /analyze — Full PDF forensic analysis pipeline.

    Accepts a PDF file via multipart/form-data, runs it through
    6 sequential analysis phases, and returns a JSON verdict
    with score, confidence, reasons, and detailed breakdown.

    Request:
        Content-Type: multipart/form-data
        Field: "file" — the PDF document to analyze.

    Returns:
        200: Full analysis report (JSON).
        400: Missing file or empty filename.
        413: File exceeds size limit.
        415: Non-PDF file type.
        500: Unrecoverable pipeline failure.
    """
    pdf_path = None
    report_id = None
    original_filename = None

    try:
        # ── REQUEST VALIDATION ───────────────────────────────
        file_obj, error = _validate_upload()
        if error is not None:
            return error

        original_filename = file_obj.filename

        # ── SAVE UPLOAD ──────────────────────────────────────
        _log(f"Received: {original_filename}")

        success, path_or_error, rid = file_handler.save_upload(
            file_obj, original_filename
        )

        if not success:
            return (
                jsonify({"error": path_or_error}), 500
            )

        pdf_path = path_or_error
        report_id = rid

        # ── FILE SIZE CHECK ──────────────────────────────────
        size_ok, size_msg = file_handler.validate_file_size(
            pdf_path
        )
        if not size_ok:
            return (
                jsonify({
                    "error": (
                        f"File too large. Maximum size is "
                        f"{Config.MAX_FILE_SIZE_MB} MB"
                    )
                }),
                413,
            )

        # Build processed directory path for this document
        processed_dir = os.path.join(
            Config.PROCESSED_FOLDER, report_id
        )

        timestamp = datetime.now(timezone.utc).isoformat()

        _log(f"Report ID: {report_id}")
        _log("Starting analysis pipeline...")

        # ════════════════════════════════════════════════════
        # PHASE 1 — Metadata Analysis
        # ════════════════════════════════════════════════════
        _log("Phase 1: Metadata analysis...")
        try:
            metadata_result = (
                metadata_analyzer.analyze_metadata(pdf_path)
            )
            _log(
                f"Phase 1: Done. Issues found: "
                f"{metadata_result.get('issue_count', 0)}"
            )
        except Exception as exc:
            _log(f"Phase 1: FAILED — {exc}")
            metadata_result = _empty_metadata()

        # ════════════════════════════════════════════════════
        # PHASE 2 — ELA + Noise Analysis (renders pages)
        # ════════════════════════════════════════════════════
        _log("Phase 2: ELA + noise analysis...")
        try:
            ela_result = ela_analyzer.analyze_vision(
                pdf_path, processed_dir
            )
            _log(
                f"Phase 2: Done. Pages: "
                f"{ela_result.get('page_count', 0)}, "
                f"Issues: {ela_result.get('issue_count', 0)}"
            )
        except Exception as exc:
            _log(f"Phase 2: FAILED — {exc}")
            ela_result = _empty_ela()

        # ════════════════════════════════════════════════════
        # PHASE 3 — OCR Extraction
        # ════════════════════════════════════════════════════
        _log("Phase 3: OCR text extraction...")
        try:
            ocr_result = ocr_extractor.analyze_ocr(
                pdf_path, processed_dir
            )
            _log(
                f"Phase 3: Done. Text length: "
                f"{ocr_result.get('total_text_length', 0)}, "
                f"Issues: {ocr_result.get('issue_count', 0)}"
            )
        except Exception as exc:
            _log(f"Phase 3: FAILED — {exc}")
            ocr_result = _empty_ocr()

        # ════════════════════════════════════════════════════
        # PHASE 4 — Template Matching
        # ════════════════════════════════════════════════════
        _log("Phase 4: Template matching...")
        try:
            templates_dir = Config.TEMPLATES_FOLDER
            template_result = template_matcher.match_template(
                ocr_result, metadata_result, templates_dir
            )
            _log(
                f"Phase 4: Done. Issues: "
                f"{template_result.get('issue_count', 0)}"
            )
        except Exception as exc:
            _log(f"Phase 4: FAILED — {exc}")
            template_result = _empty_template()

        # ════════════════════════════════════════════════════
        # PHASE 5 — ML Anomaly Detection
        # ════════════════════════════════════════════════════
        _log("Phase 5: ML anomaly detection...")
        try:
            anomaly_result = (
                anomaly_detector.run_anomaly_detection(
                    metadata_result,
                    ela_result,
                    ocr_result,
                    template_result,
                    Config.MODEL_PATH,
                )
            )
            is_anom = anomaly_result.get("is_anomaly", False)
            _log(
                f"Phase 5: Done. Anomaly: {is_anom}, "
                f"Confidence: "
                f"{anomaly_result.get('confidence', 0)}%"
            )
        except Exception as exc:
            _log(f"Phase 5: FAILED — {exc}")
            anomaly_result = _empty_anomaly()

        # ════════════════════════════════════════════════════
        # PHASE 6 — Score Aggregation
        # ════════════════════════════════════════════════════
        _log("Phase 6: Score aggregation...")
        try:
            verdict_result = score_aggregator.aggregate_scores(
                metadata_result,
                ela_result,
                ocr_result,
                template_result,
                anomaly_result,
            )
            _log(
                f"Phase 6: Done. Score: "
                f"{verdict_result.get('score', '?')}/100, "
                f"Verdict: {verdict_result.get('verdict', '?')}"
            )
        except Exception as exc:
            _log(f"Phase 6: FAILED — {exc}")
            return (
                jsonify({
                    "error": "Analysis failed",
                    "detail": str(exc),
                }),
                500,
            )

        # ════════════════════════════════════════════════════
        # BUILD FULL REPORT
        # ════════════════════════════════════════════════════
        full_report = {
            "report_id": report_id,
            "filename": original_filename,
            "timestamp": timestamp,
            "score": verdict_result["score"],
            "verdict": verdict_result["verdict"],
            "confidence": verdict_result["confidence"],
            "reasons": verdict_result["reasons"],
            "summary": verdict_result["summary"],
            "breakdown": verdict_result["breakdown"],
            "details": {
                "metadata": _make_serializable(
                    metadata_result
                ),
                "vision": _make_serializable(ela_result),
                "ocr": _make_serializable(ocr_result),
                "template": _make_serializable(
                    template_result
                ),
                "ml": _make_serializable(anomaly_result),
            },
        }

        # ── Save report to disk ──────────────────────────────
        _log("Saving report...")
        saved = file_handler.save_report(
            report_id, full_report
        )
        if saved:
            _log(f"Report saved: {report_id}.json")
        else:
            _log("WARNING: Report save failed.")

        _log(
            f"Pipeline complete. "
            f"Verdict: {verdict_result['verdict']} "
            f"({verdict_result['score']}/100)"
        )

        return jsonify(full_report), 200

    except Exception as exc:
        _log(f"CRITICAL: Unhandled error — {exc}")
        return (
            jsonify({
                "error": "Analysis failed",
                "detail": str(exc),
            }),
            500,
        )

    finally:
        # ── CLEANUP GUARANTEE ────────────────────────────────
        # Always delete the uploaded PDF after processing.
        # processed/ images are left for report viewing.
        if pdf_path and os.path.isfile(pdf_path):
            deleted = file_handler.delete_upload(pdf_path)
            if deleted:
                _log("Upload cleaned up.")
            else:
                _log("WARNING: Upload cleanup failed.")
