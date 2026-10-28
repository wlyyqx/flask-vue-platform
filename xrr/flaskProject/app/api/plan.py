from datetime import datetime
from flask import Blueprint, request, g
from ..extensions import db
from ..models import TestPlan
from ..utils import ok, fail, login_required

bp = Blueprint("plan", __name__, url_prefix="/api/projects/<int:pid>/plans")


@bp.get("")
@login_required
def list_plans(pid):
    items = TestPlan.query.filter_by(project_id=pid).order_by(TestPlan.id.desc()).all()
    return ok([p.to_dict() for p in items])


@bp.post("")
@login_required
def create_plan(pid):
    d = request.get_json() or {}
    if not d.get("name"):
        return fail("name 必填")
    start = datetime.strptime(d["start_date"], "%Y-%m-%d").date() if d.get("start_date") else None
    end = datetime.strptime(d["end_date"], "%Y-%m-%d").date() if d.get("end_date") else None
    p = TestPlan(project_id=pid, name=d["name"], description=d.get("description", ""),
                 start_date=start, end_date=end, creator_id=g.user.id)
    db.session.add(p)
    db.session.commit()
    return ok(p.to_dict())


@bp.delete("/<int:plan_id>")
@login_required
def delete_plan(pid, plan_id):
    p = TestPlan.query.filter_by(id=plan_id, project_id=pid).first()
    if not p:
        return fail("计划不存在", 404)
    db.session.delete(p)
    db.session.commit()
    return ok()