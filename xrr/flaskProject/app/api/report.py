from flask import Blueprint
from sqlalchemy import func
from ..extensions import db
from ..models import TestCase, CaseExecution, Defect
from ..utils import ok, login_required

bp = Blueprint("report", __name__, url_prefix="/api/projects/<int:pid>/reports")


@bp.get("/overview")
@login_required
def overview(pid):
    total_cases = TestCase.query.filter_by(project_id=pid).count()

    prio_rows = (db.session.query(TestCase.priority, func.count(TestCase.id))
                 .filter_by(project_id=pid).group_by(TestCase.priority).all())
    prio_dist = {f"P{p-1}": c for p, c in prio_rows}

    exec_rows = (db.session.query(CaseExecution.result, func.count(CaseExecution.id))
                 .join(TestCase, TestCase.id == CaseExecution.case_id)
                 .filter(TestCase.project_id == pid)
                 .group_by(CaseExecution.result).all())
    label_map = {1: "通过", 2: "失败", 3: "阻塞", 4: "跳过"}
    exec_dist = {label_map.get(r, str(r)): c for r, c in exec_rows}

    defect_rows = (db.session.query(Defect.severity, func.count(Defect.id))
                   .filter_by(project_id=pid).group_by(Defect.severity).all())
    sev_map = {1: "致命", 2: "严重", 3: "一般", 4: "轻微"}
    defect_dist = {sev_map.get(s, str(s)): c for s, c in defect_rows}

    total_exec = sum(exec_dist.values())
    passed = exec_dist.get("通过", 0)

    return ok({
        "total_cases": total_cases,
        "total_defects": sum(defect_dist.values()),
        "pass_rate": round(passed / total_exec * 100, 2) if total_exec else 0,
        "priority_dist": prio_dist,
        "execution_dist": exec_dist,
        "defect_dist": defect_dist,
    })