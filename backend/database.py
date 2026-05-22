import os
import sys

from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt

db = SQLAlchemy()
bcrypt = Bcrypt()

def init_db(app):
    
    try:
        db.init_app(app)
        bcrypt.init_app(app)
        db_dir = app.config.get("DATABASE_DIR")
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)
        with app.app_context():
            db.create_all()
        db_path = app.config.get("DATABASE_PATH", "unknown")
        print(f"[✓] Database initialized at {db_path}")

    except Exception as exc:
        print(
            f"[✗] Database initialization failed: {exc}",
            file=sys.stderr,
        )
        raise
