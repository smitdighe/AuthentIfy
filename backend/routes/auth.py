import re

from flask import Blueprint, jsonify, request
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    get_jwt_identity,
    jwt_required,
)
from database import db
from db_models import User
from middleware.auth_middleware import jwt_required_with_user

auth_bp = Blueprint("auth_bp", __name__, url_prefix="/auth")

_EMAIL_RE = re.compile(
    r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
)

@auth_bp.route("/register", methods=["POST"])
def register():

    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body must be JSON"}), 400

    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    full_name = (data.get("full_name") or "").strip() or None

    if not email:
        return jsonify({"error": "Email is required"}), 400

    if not _EMAIL_RE.match(email):
        return jsonify({"error": "Invalid email format"}), 400

    if not password or len(password) < 8:
        return (
            jsonify({
                "error": "Password must be at least 8 characters"
            }),
            400,
        )
        
    if User.query.filter_by(email=email).first():
        return (
            jsonify({"error": "Email already registered"}),
            409,
        )

    try:
        user = User(email=email, full_name=full_name)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
    except Exception as exc:
        db.session.rollback()
        return (
            jsonify({"error": f"Registration failed: {exc}"}),
            500,
        )

    access_token = create_access_token(identity=str(user.id))
    refresh_token = create_refresh_token(identity=str(user.id))

    print(f"[✓] New registration: {user.email} (id={user.id})")

    return (
        jsonify({
            "message": "Account created successfully",
            "user": user.to_dict(),
            "access_token": access_token,
            "refresh_token": refresh_token,
        }),
        201,
    )

@auth_bp.route("/login", methods=["POST"])
def login():

    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body must be JSON"}), 400

    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not email or not password:
        return (
            jsonify({"error": "Email and password are required"}),
            400,
        )

    _INVALID = {"error": "Invalid email or password"}

    user = User.query.filter_by(email=email).first()
    if user is None:
        return jsonify(_INVALID), 401

    if not user.check_password(password):
        return jsonify(_INVALID), 401

    if not user.is_active:
        return (
            jsonify({"error": "Account is deactivated"}),
            403,
        )

    access_token = create_access_token(identity=str(user.id))
    refresh_token = create_refresh_token(identity=str(user.id))

    print(f"[✓] Login: {user.email} (id={user.id})")

    return (
        jsonify({
            "message": "Login successful",
            "user": user.to_dict(),
            "access_token": access_token,
            "refresh_token": refresh_token,
        }),
        200,
    )

@auth_bp.route("/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh():

    identity = get_jwt_identity()
    access_token = create_access_token(identity=identity)

    return (
        jsonify({"access_token": access_token}),
        200,
    )

@auth_bp.route("/logout", methods=["POST"])
@jwt_required()
def logout():

    identity = get_jwt_identity()
    print(f"[✓] Logout: user_id={identity}")

    return (
        jsonify({"message": "Logged out successfully"}),
        200,
    )

@auth_bp.route("/me", methods=["GET"])
@jwt_required_with_user
def me(current_user):

    return jsonify(current_user.to_dict()), 200
