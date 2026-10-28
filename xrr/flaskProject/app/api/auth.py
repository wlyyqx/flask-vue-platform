from flask import Blueprint, request, g
from flask_jwt_extended import create_access_token
from ..models import User
from ..utils import ok, fail, login_required

bp = Blueprint("auth", __name__, url_prefix="/api/auth")


@bp.post("/login")
def login():
    d = request.get_json() or {}
    user = User.query.filter_by(username=d.get("username")).first()
    if not user or not user.check_password(d.get("password", "")):
        return fail("用户名或密码错误", 401)
    if not user.is_active:
        return fail("账号已禁用", 403)
    token = create_access_token(identity=str(user.id))
    return ok({"access_token": token, "user": user.to_dict()})


@bp.get("/me")
@login_required
def me():
    return ok(g.user.to_dict())