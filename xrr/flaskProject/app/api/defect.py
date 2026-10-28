from flask import Blueprint, request, g
from ..extensions import db
from ..models import Defect
from ..utils import ok, fail, login_required

bp = Blueprint("defect", __name__, url_prefix="/api/projects/<int:pid>/defects")


@bp.get("")
@login_required
def list_defects(pid):
    status = request.args.get("status")
    severity = request.args.get("severity")
    q = Defect.query.filter_by(project_id=pid)
    if status:
        q = q.filter_by(status=status)
    if severity:
        q = q.filter_by(severity=severity)
    items = q.order_by(Defect.id.desc()).all()
    return ok([x.to_dict() for x in items])


@bp.post("")
@login_required
def create_defect(pid):
    d = request.get_json() or {}
    if not d.get("title"):
        return fail("title 必填")
    x = Defect(
        project_id=pid, title=d["title"], description=d.get("description", ""),
        case_id=d.get("case_id"), execution_id=d.get("execution_id"),
        severity=d.get("severity", 2), status=d.get("status", 1),
        assignee_id=d.get("assignee_id"), creator_id=g.user.id,
    )
    db.session.add(x)
    db.session.commit()
    return ok(x.to_dict())


@bp.put("/<int:did>")
@login_required
def update_defect(pid, did):
    x = Defect.query.filter_by(id=did, project_id=pid).first()
    if not x:
        return fail("缺陷不存在", 404)
    d = request.get_json() or {}
    for f in ("title", "description", "severity", "status", "assignee_id"):
        if f in d:
            setattr(x, f, d[f])
    db.session.commit()
    return ok(x.to_dict())


@bp.delete("/<int:did>")
@login_required
def delete_defect(pid, did):
    x = Defect.query.filter_by(id=did, project_id=pid).first()
    if not x:
        return fail("缺陷不存在", 404)
    db.session.delete(x)
    db.session.commit()
    return ok()