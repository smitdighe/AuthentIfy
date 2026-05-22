from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from config import Config
from database import init_db
from utils.file_handler import ensure_directory
from routes.analyze import analyze_bp
from routes.auth import auth_bp
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

def create_app() -> Flask:

    app = Flask(__name__)
    app.json_provider_class = CustomJSONProvider 
    app.json = CustomJSONProvider(app)
    app.secret_key = "authentify-hackathon-2026"

    app.config["MAX_CONTENT_LENGTH"] = Config.MAX_FILE_SIZE_BYTES

    CORS(app)

    app.config["JWT_SECRET_KEY"] = (
        Config.JWT_SECRET_KEY
    )
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = (
        Config.JWT_ACCESS_TOKEN_EXPIRES
    )
    app.config["JWT_REFRESH_TOKEN_EXPIRES"] = (
        Config.JWT_REFRESH_TOKEN_EXPIRES
    )
    app.config["JWT_TOKEN_LOCATION"] = (
        Config.JWT_TOKEN_LOCATION
    )
    app.config["JWT_HEADER_NAME"] = (
        Config.JWT_HEADER_NAME
    )
    app.config["JWT_HEADER_TYPE"] = (
        Config.JWT_HEADER_TYPE
    )
    jwt = JWTManager(app)
    
    app.config["SQLALCHEMY_DATABASE_URI"] = (
        Config.SQLALCHEMY_DATABASE_URI
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = (
        Config.SQLALCHEMY_TRACK_MODIFICATIONS
    )
    init_db(app)

    app.register_blueprint(analyze_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(report_bp)
    app.register_blueprint(health_bp)

    _ensure_directories()
    return app

def _ensure_directories() -> None:

    dirs = [
        ("Upload folder   ", Config.UPLOAD_FOLDER),
        ("Processed folder", Config.PROCESSED_FOLDER),
        ("Models folder   ", Config.MODEL_FOLDER),
        ("Reports folder  ", Config.REPORTS_FOLDER),
        ("Templates folder", Config.TEMPLATES_FOLDER),
        ("Database folder ", Config.DATABASE_DIR),
    ]

    for label, path in dirs:
        ensure_directory(path)
        print(f"  [+] {label}: {path}")

def _print_banner() -> None:
    
    print()
    print("  +======================================+")
    print("  |   AuthentIfy - Verify before trust    |")
    print(
        f"  |   Backend running on port {Config.PORT}"
        f"{'':>{8 - len(str(Config.PORT))}}|"
    )
    print("  +======================================+")
    print()


if __name__ == "__main__":
    _print_banner()

    app = create_app()

    print()
    print(
        "  [\u2713] Authentication : JWT enabled"
    )
    print(
        f"  [\u2713] Database       : SQLite at "
        f"{Config.DATABASE_PATH}"
    )
    print("  [+] All systems ready. Awaiting documents.")
    print()

    app.run(
        host=Config.HOST,
        port=Config.PORT,
        debug=Config.DEBUG,
    )
