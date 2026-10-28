from flask import Blueprint, request, g
from sqlalchemy import or_, func
from ..extensions import db
from ..models import TestCase, CaseVersion, Tag, CaseExecution
from ..utils import ok, fail, login_required

bp = Blueprint("testcase", __name__, url_prefix="/api/projects/<int:pid>/cases")


def _gen_case_no(project_id):
    count = TestCase.query.filter_by(project_id=project_id).count()
    return f"TC-{count + 1:05d}"


@bp.get("")
@login_required
def list_cases(pid):
    page = int(request.args.get("page", 1))
    size = min(int(request.args.get("size", 20)), 200)
    kw = request.args.get("keyword", "").strip()
    module_id = request.args.get("module_id")
    status = request.args.get("status")
    priority = request.args.get("priority")

    q = TestCase.query.filter_by(project_id=pid)
    if kw:
        q = q.filter(or_(TestCase.title.like(f"%{kw}%"),
                         TestCase.case_no.like(f"%{kw}%")))
    if module_id:
        q = q.filter_by(module_id=module_id)
    if status:
        q = q.filter_by(status=status)
    if priority:
        q = q.filter_by(priority=priority)

    total = q.count()
    items = q.order_by(TestCase.id.desc()).offset((page - 1) * size).limit(size).all()
    return ok({"total": total, "page": page, "size": size,
               "items": [c.to_dict() for c in items]})


@bp.post("")
@login_required
def create_case(pid):
    d = request.get_json() or {}
    if not d.get("title"):
        return fail("title 必填")
    case = TestCase(
        project_id=pid,
        module_id=d.get("module_id"),
        case_no=_gen_case_no(pid),
        title=d["title"],
        precondition=d.get("precondition", ""),
        steps=d.get("steps", []),
        priority=d.get("priority", 2),
        case_type=d.get("case_type", "functional"),
        status=d.get("status", 1),
        creator_id=g.user.id,
    )
    for tag_name in d.get("tags", []):
        tag = Tag.query.filter_by(project_id=pid, name=tag_name).first()
        if not tag:
            tag = Tag(project_id=pid, name=tag_name)
            db.session.add(tag)
        case.tags.append(tag)
    db.session.add(case)
    db.session.flush()
    db.session.add(CaseVersion(
        case_id=case.id, version=1,
        snapshot={"title": case.title, "steps": case.steps, "priority": case.priority},
        change_log="创建", operator_id=g.user.id))
    db.session.commit()
    return ok(case.to_dict(detail=True))


@bp.get("/<int:cid>")
@login_required
def get_case(pid, cid):
    c = TestCase.query.filter_by(id=cid, project_id=pid).first()
    if not c:
        return fail("用例不存在", 404)
    return ok(c.to_dict(detail=True))


@bp.put("/<int:cid>")
@login_required
def update_case(pid, cid):
    d = request.get_json() or {}
    c = TestCase.query.filter_by(id=cid, project_id=pid).first()
    if not c:
        return fail("用例不存在", 404)
    for f in ("title", "precondition", "steps", "priority",
              "case_type", "module_id", "status"):
        if f in d:
            setattr(c, f, d[f])
    c.current_version += 1
    db.session.add(CaseVersion(
        case_id=c.id, version=c.current_version,
        snapshot={"title": c.title, "steps": c.steps, "priority": c.priority},
        change_log=d.get("change_log", "编辑"), operator_id=g.user.id))
    db.session.commit()
    return ok(c.to_dict(detail=True))


@bp.delete("/<int:cid>")
@login_required
def delete_case(pid, cid):
    c = TestCase.query.filter_by(id=cid, project_id=pid).first()
    if not c:
        return fail("用例不存在", 404)
    db.session.delete(c)
    db.session.commit()
    return ok()


@bp.get("/<int:cid>/versions")
@login_required
def versions(pid, cid):
    rows = CaseVersion.query.filter_by(case_id=cid)\
        .order_by(CaseVersion.version.desc()).all()
    return ok([r.to_dict() for r in rows])


@bp.get("/stats/overview")
@login_required
def stats_overview(pid):
    total = TestCase.query.filter_by(project_id=pid).count()
    prio = dict(db.session.query(TestCase.priority, func.count(TestCase.id))
                .filter_by(project_id=pid).group_by(TestCase.priority).all())
    exec_rows = (db.session.query(CaseExecution.result, func.count(CaseExecution.id))
                 .join(TestCase, TestCase.id == CaseExecution.case_id)
                 .filter(TestCase.project_id == pid)
                 .group_by(CaseExecution.result).all())
    exec_stat = {1: 0, 2: 0, 3: 0, 4: 0}
    for r, c in exec_rows:
        exec_stat[r] = c
    return ok({"total_cases": total, "priority_dist": prio, "execution_dist": exec_stat})