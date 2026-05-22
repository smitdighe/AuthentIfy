import functools

from flask import jsonify
from flask_jwt_extended import (
    get_jwt_identity,
    jwt_required,
    verify_jwt_in_request,
)

from db_models.user import User

def get_current_user():

    try:
        user_id = get_jwt_identity()
        if user_id is None:
            return None
        return User.query.get(int(user_id))
    except Exception:
        return None


def jwt_required_with_user(fn):
    
    @functools.wraps(fn)
    @jwt_required()
    def wrapper(*args, **kwargs):
        user = get_current_user()

        if user is None:
            return (
                jsonify({"error": "User account not found"}),
                401,
            )

        if not user.is_active:
            return (
                jsonify({"error": "Account is deactivated"}),
                403,
            )

        return fn(user, *args, **kwargs)
    
    return wrapper


def optional_jwt_user(fn):
    
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        current_user = None

        try:
            verify_jwt_in_request(optional=True)
            identity = get_jwt_identity()
            if identity is not None:
                user = User.query.get(int(identity))
                if user and user.is_active:
                    current_user = user
        except Exception:            
            current_user = None

        return fn(current_user, *args, **kwargs)

    return wrapper
