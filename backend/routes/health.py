# ============================================================
# routes/health.py — AuthentIfy Backend
# Project: AuthentIfy — "Verify before you trust."
# Role   : Liveness probe — confirms the Flask server is up.
# ============================================================

from __future__ import annotations

from datetime import datetime, timezone

from flask import Blueprint, jsonify


health_bp = Blueprint("health_bp", __name__, url_prefix="/health")


@health_bp.route("/", methods=["GET"])
def health_check():
    """GET /health — Service liveness check.

    Returns a minimal JSON payload confirming the API is
    reachable and responding. Used by uptime monitors,
    load balancers, and quick sanity checks during demos.

    Returns:
        200 always.
    """
    return jsonify({
        "status": "ok",
        "service": "AuthentIfy",
        "version": "1.0.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }), 200
