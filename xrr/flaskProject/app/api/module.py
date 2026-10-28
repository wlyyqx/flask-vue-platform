from flask import Blueprint, request
from ..extensions import db
from ..models import Module
from ..utils import ok, fail, login_required

bp = Blueprint("module", __name__, url_prefix="/api/projects/<int:pid>/modules")


@bp.get("")
@login_required
def list_modules(pid):
    items = Module.query.filter_by(project_id=pid).order_by(Module.sort).all()
    return ok([m.to_dict() for m in items])


@bp.post("")
@login_required
def create_module(pid):
    d = request.get_json() or {}
    if not d.get("name"):
        return fail("name 必填")
    m = Module(project_id=pid, parent_id=d.get("parent_id", 0),
               name=d["name"], sort=d.get("sort", 0))
    db.session.add(m)
    db.session.commit()
    return ok(m.to_dict())


@bp.delete("/<int:mid>")
@login_required
def delete_module(pid, mid):
    m = Module.query.filter_by(id=mid, project_id=pid).first()
    if not m:
        return fail("模块不存在", 404)
    db.session.delete(m)
    db.session.commit()
    return ok()