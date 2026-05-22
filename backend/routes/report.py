from __future__ import annotations
import re

from flask import Blueprint, jsonify, request
from database import db
from db_models import Report
from middleware.auth_middleware import jwt_required_with_user
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

@report_bp.route("/history", methods=["GET"])
@jwt_required_with_user
def get_history(current_user):
 
    page = request.args.get("page", 1, type=int)
    limit = request.args.get("limit", 10, type=int)
    limit = min(max(limit, 1), 50)  # Clamp to 1–50
    page = max(page, 1)

    pagination = (
        Report.query
        .filter_by(user_id=current_user.id)
        .order_by(Report.created_at.desc())
        .paginate(
            page=page,
            per_page=limit,
            error_out=False,
        )
    )

    return (
        jsonify({
            "reports": [
                r.to_dict() for r in pagination.items
            ],
            "total": pagination.total,
            "page": pagination.page,
            "pages": pagination.pages,
            "has_next": pagination.has_next,
            "has_prev": pagination.has_prev,
        }),
        200,
    )

@report_bp.route(
    "/history/<report_uuid>", methods=["DELETE"]
)
@jwt_required_with_user
def delete_report(current_user, report_uuid: str):
 
    report = Report.query.filter_by(
        report_uuid=report_uuid
    ).first()

    if report is None:
        return (
            jsonify({"error": "Report not found"}),
            404,
        )

    if report.user_id != current_user.id:
        return (
            jsonify({
                "error": "Not authorized to delete "
                "this report"
            }),
            403,
        )

    try:
        db.session.delete(report)
        current_user.total_reports = max(
            current_user.total_reports - 1, 0
        )
        db.session.commit()
    except Exception as exc:
        db.session.rollback()
        return (
            jsonify({
                "error": f"Delete failed: {exc}"
            }),
            500,
        )

    return (
        jsonify({"message": "Report deleted"}),
        200,
    )

@report_bp.route("/stats", methods=["GET"])
@jwt_required_with_user
def get_stats(current_user):
 
    reports = Report.query.filter_by(
        user_id=current_user.id
    ).all()

    total = len(reports)
    genuine = sum(
        1 for r in reports if r.verdict == "Genuine"
    )
    suspicious = sum(
        1 for r in reports if r.verdict == "Suspicious"
    )
    tampered = sum(
        1 for r in reports if r.verdict == "Tampered"
    )
    avg_score = (
        round(sum(r.score for r in reports) / total, 1)
        if total > 0
        else 0.0
    )

    return (
        jsonify({
            "total_reports": total,
            "genuine_count": genuine,
            "suspicious_count": suspicious,
            "tampered_count": tampered,
            "average_score": avg_score,
        }),
        200,
    )
