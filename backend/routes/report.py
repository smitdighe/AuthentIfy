from __future__ import annotations

import re

from flask import Blueprint, jsonify
from utils import file_handler

report_bp = Blueprint(
    "report_bp", __name__, url_prefix="/report"
)

_UUID_PATTERN = re.compile(
    r"^[0-9a-fA-F]{32}$"
    r"|"
    r"^[0-9a-fA-F]{8}"
    r"-[0-9a-fA-F]{4}"
    r"-[0-9a-fA-F]{4}"
    r"-[0-9a-fA-F]{4}"
    r"-[0-9a-fA-F]{12}$"
)

def _is_valid_report_id(report_id: str) -> bool:
    
    if not report_id or not isinstance(report_id, str):
        return False

    return _UUID_PATTERN.match(report_id) is not None

@report_bp.route("/<report_id>", methods=["GET"])
def get_report(report_id: str):
    
    if not _is_valid_report_id(report_id):
        return (
            jsonify({
                "error": "Invalid report ID format",
            }),
            400,
        )

    try:
        found, report_data = file_handler.load_report(
            report_id
        )
    except Exception:
        return (
            jsonify({
                "error": "Report retrieval failed",
                "report_id": report_id,
            }),
            500,
        )

    if not found:
        return (
            jsonify({
                "error": "Report not found",
                "report_id": report_id,
            }),
            404,
        )

    return jsonify(report_data), 200
