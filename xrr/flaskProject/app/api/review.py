from datetime import datetime
from flask import Blueprint, request, g
from ..extensions import db
from ..models import Review, ReviewComment, TestCase
from ..utils import ok, fail, login_required

bp = Blueprint("review", __name__, url_prefix="/api/projects/<int:pid>/reviews")


@bp.get("")
@login_required
def list_reviews(pid):
    items = Review.query.filter_by(project_id=pid).order_by(Review.id.desc()).all()
    return ok([r.to_dict() for r in items])


@bp.post("")
@login_required
def create_review(pid):
    d = request.get_json() or {}
    if not d.get("title"):
        return fail("title 必填")
    deadline = None
    if d.get("deadline"):
        deadline = datetime.strptime(d["deadline"], "%Y-%m-%d %H:%M:%S")
    r = Review(
        project_id=pid, title=d["title"],
        case_ids=d.get("case_ids", []), reviewer_ids=d.get("reviewer_ids", []),
        creator_id=g.user.id, deadline=deadline,
    )
    db.session.add(r)
    db.session.commit()
    return ok(r.to_dict())


@bp.get("/<int:rid>")
@login_required
def get_review(pid, rid):
    r = Review.query.filter_by(id=rid, project_id=pid).first()
    if not r:
        return fail("评审不存在", 404)
    # 关联用例信息
    cases = TestCase.query.filter(TestCase.id.in_(r.case_ids or [])).all()
    comments = ReviewComment.query.filter_by(review_id=rid).order_by(ReviewComment.id.desc()).all()
    return ok({
        **r.to_dict(),
        "cases": [{"id": c.id, "case_no": c.case_no, "title": c.title} for c in cases],
        "comments": [c.to_dict() for c in comments],
    })


@bp.post("/<int:rid>/comments")
@login_required
def add_comment(pid, rid):
    d = request.get_json() or {}
    if d.get("result") not in (1, 2, 3):
        return fail("result 非法（1通过 2拒绝 3建议）")
    r = Review.query.filter_by(id=rid, project_id=pid).first()
    if not r:
        return fail("评审不存在", 404)
    c = ReviewComment(review_id=rid, case_id=d["case_id"],
                      user_id=g.user.id, result=d["result"],
                      content=d.get("content", ""))
    db.session.add(c)
    # 首次有人评审，状态置为"评审中"
    if r.status == 1:
        r.status = 2
    db.session.commit()
    return ok(c.to_dict())


@bp.put("/<int:rid>/status")
@login_required
def update_status(pid, rid):
    d = request.get_json() or {}
    if d.get("status") not in (1, 2, 3, 4):
        return fail("status 非法")
    r = Review.query.filter_by(id=rid, project_id=pid).first()
    if not r:
        return fail("评审不存在", 404)
    r.status = d["status"]
    db.session.commit()
    return ok(r.to_dict())


@bp.delete("/<int:rid>")
@login_required
def delete_review(pid, rid):
    r = Review.query.filter_by(id=rid, project_id=pid).first()
    if not r:
        return fail("评审不存在", 404)
    ReviewComment.query.filter_by(review_id=rid).delete()
    db.session.delete(r)
    db.session.commit()
    return ok()