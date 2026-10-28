from flask import Blueprint, request, g
from sqlalchemy import func
from ..extensions import db
from ..models import TestPlan, CaseExecution
from ..utils import ok, fail, login_required

bp = Blueprint("execution", __name__, url_prefix="/api/projects/<int:pid>")


@bp.post("/plans/<int:plan_id>/executions")
@login_required
def execute(pid, plan_id):
    d = request.get_json() or {}
    if d.get("result") not in (1, 2, 3, 4):
        return fail("result 非法（1通过 2失败 3阻塞 4跳过）")
    plan = TestPlan.query.filter_by(id=plan_id, project_id=pid).first()
    if not plan:
        return fail("计划不存在", 404)
    ex = CaseExecution(plan_id=plan_id, case_id=d["case_id"], executor_id=g.user.id,
                       result=d["result"], comment=d.get("comment", ""),
                       duration_ms=d.get("duration_ms", 0))
    db.session.add(ex)
    db.session.commit()
    return ok(ex.to_dict())


@bp.get("/plans/<int:plan_id>/report")
@login_required
def plan_report(pid, plan_id):
    rows = (db.session.query(CaseExecution.result, func.count(CaseExecution.id))
            .filter_by(plan_id=plan_id)
            .group_by(CaseExecution.result).all())
    stat = {1: 0, 2: 0, 3: 0, 4: 0}
    for r, c in rows:
        stat[r] = c
    total = sum(stat.values())
    passed = stat[1]
    return ok({
        "total": total, "passed": passed, "failed": stat[2],
        "blocked": stat[3], "skipped": stat[4],
        "pass_rate": round(passed / total * 100, 2) if total else 0,
    })