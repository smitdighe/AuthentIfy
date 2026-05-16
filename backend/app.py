# ============================================================
# app.py — AuthentIfy Backend
# Project: AuthentIfy — "Verify before you trust."
# Role   : Application entry point — creates the Flask app,
#          registers all blueprints, ensures required
#          directories exist, and starts the dev server.
#
# This file contains NO business logic. It only wires
# components together and boots the server.
# ============================================================

from flask import Flask
from flask_cors import CORS

from config import Config
from utils.file_handler import ensure_directory

from routes.analyze import analyze_bp
from routes.report import report_bp
from routes.health import health_bp

import numpy as np
from flask.json.provider import DefaultJSONProvider

class CustomJSONProvider(DefaultJSONProvider):
    def default(self, obj):
        if isinstance(obj, np.bool_):
            return bool(obj)
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return super().default(obj)

# ── App Factory ──────────────────────────────────────────────


def create_app() -> Flask:
    """Create and configure the Flask application.

    Steps:
        1. Create Flask instance.
        2. Set secret key and max content length.
        3. Enable CORS (all origins — hackathon mode).
        4. Register all route blueprints.
        5. Ensure required directories exist on disk.

    Returns:
        Configured Flask application instance.
    """
    app = Flask(__name__)
    app.json_provider_class = CustomJSONProvider 
    app.json = CustomJSONProvider(app)
    # Secret key for session signing — change for production
    app.secret_key = "authentify-hackathon-2026"

    # Reject uploads larger than the configured limit
    app.config["MAX_CONTENT_LENGTH"] = Config.MAX_FILE_SIZE_BYTES

    # ── CORS ─────────────────────────────────────────────────
    # Allow all origins for hackathon demo convenience
    CORS(app)

    # ── Register Blueprints ──────────────────────────────────
    app.register_blueprint(analyze_bp)
    app.register_blueprint(report_bp)
    app.register_blueprint(health_bp)

    # ── Ensure Required Directories ──────────────────────────
    _ensure_directories()

    return app


# ── Directory Bootstrap ──────────────────────────────────────


def _ensure_directories() -> None:
    """Create all required directories if they don't exist.

    Uses file_handler.ensure_directory() for safe creation
    with os.makedirs(exist_ok=True).
    """
    dirs = [
        ("Upload folder   ", Config.UPLOAD_FOLDER),
        ("Processed folder", Config.PROCESSED_FOLDER),
        ("Models folder   ", Config.MODEL_FOLDER),
        ("Reports folder  ", Config.REPORTS_FOLDER),
        ("Templates folder", Config.TEMPLATES_FOLDER),
    ]

    for label, path in dirs:
        ensure_directory(path)
        print(f"  [+] {label}: {path}")


# ── Startup Banner ───────────────────────────────────────────


def _print_banner() -> None:
    """Print the AuthentIfy startup banner to the console."""
    print()
    print("  +======================================+")
    print("  |   AuthentIfy - Verify before trust    |")
    print(
        f"  |   Backend running on port {Config.PORT}"
        f"{'':>{8 - len(str(Config.PORT))}}|"
    )
    print("  +======================================+")
    print()


# ── Entry Point ──────────────────────────────────────────────


if __name__ == "__main__":
    _print_banner()

    app = create_app()

    print()
    print("  [+] All systems ready. Awaiting documents.")
    print()

    app.run(
        host=Config.HOST,
        port=Config.PORT,
        debug=Config.DEBUG,
    )
