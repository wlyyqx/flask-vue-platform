from flask import Blueprint, request, g
from ..extensions import db
from ..models import Project
from ..utils import ok, fail, login_required

bp = Blueprint("project", __name__, url_prefix="/api/projects")


@bp.get("")
@login_required
def list_projects():
    items = Project.query.order_by(Project.id.desc()).all()
    return ok([p.to_dict() for p in items])


@bp.post("")
@login_required
def create_project():
    d = request.get_json() or {}
    if not d.get("name") or not d.get("code"):
        return fail("name 和 code 必填")
    if Project.query.filter_by(code=d["code"]).first():
        return fail("项目编码已存在")
    p = Project(name=d["name"], code=d["code"],
                description=d.get("description", ""), owner_id=g.user.id)
    db.session.add(p)
    db.session.commit()
    return ok(p.to_dict())


@bp.get("/<int:pid>")
@login_required
def get_project(pid):
    p = Project.query.get(pid)
    if not p:
        return fail("项目不存在", 404)
    return ok(p.to_dict())


@bp.put("/<int:pid>")
@login_required
def update_project(pid):
    p = Project.query.get(pid)
    if not p:
        return fail("项目不存在", 404)
    d = request.get_json() or {}
    for f in ("name", "description", "status"):
        if f in d:
            setattr(p, f, d[f])
    db.session.commit()
    return ok(p.to_dict())


@bp.delete("/<int:pid>")
@login_required
def delete_project(pid):
    p = Project.query.get(pid)
    if not p:
        return fail("项目不存在", 404)
    db.session.delete(p)
    db.session.commit()
    return ok()