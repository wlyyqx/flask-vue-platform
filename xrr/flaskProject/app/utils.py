from functools import wraps
from flask import jsonify, g
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from .models import User


def ok(data=None, msg="success"):
    return jsonify({"code": 0, "msg": msg, "data": data})


def fail(msg="error", http_status=400):
    return jsonify({"code": 1, "msg": msg, "data": None}), http_status


def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        uid = int(get_jwt_identity())
        user = User.query.get(uid)
        if not user or not user.is_active:
            return fail("用户无效", 401)
        g.user = user
        return fn(*args, **kwargs)
    return wrapper