from __future__ import annotations
from datetime import datetime, timezone
from flask import Blueprint, jsonify

health_bp = Blueprint("health_bp", __name__, url_prefix="/health")

@health_bp.route("/", methods=["GET"])
def health_check():
    
    return jsonify({
        "status": "ok",
        "service": "AuthentIfy",
        "version": "1.0.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }), 200
