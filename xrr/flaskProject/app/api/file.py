import os
import uuid
from flask import Blueprint, request, g, current_app, send_file
from werkzeug.utils import secure_filename
from ..extensions import db
from ..models import Attachment
from ..utils import ok, fail, login_required

bp = Blueprint("file", __name__, url_prefix="/api/files")


def _upload_dir():
    d = current_app.config["UPLOAD_FOLDER"]
    os.makedirs(d, exist_ok=True)
    return d


@bp.post("/upload")
@login_required
def upload():
    f = request.files.get("file")
    biz_type = request.form.get("biz_type", "case")
    biz_id = request.form.get("biz_id", type=int)
    if not f or not biz_id:
        return fail("缺少 file 或 biz_id")

    filename = secure_filename(f.filename)
    ext = os.path.splitext(filename)[1]
    stored = f"{uuid.uuid4().hex}{ext}"
    path = os.path.join(_upload_dir(), stored)
    f.save(path)
    size = os.path.getsize(path)

    att = Attachment(biz_type=biz_type, biz_id=biz_id, file_name=filename,
                     file_path=stored, file_size=size, uploader_id=g.user.id)
    db.session.add(att)
    db.session.commit()
    return ok(att.to_dict())


@bp.get("")
@login_required
def list_files():
    biz_type = request.args.get("biz_type")
    biz_id = request.args.get("biz_id", type=int)
    q = Attachment.query
    if biz_type:
        q = q.filter_by(biz_type=biz_type)
    if biz_id:
        q = q.filter_by(biz_id=biz_id)
    return ok([a.to_dict() for a in q.order_by(Attachment.id.desc()).all()])


@bp.get("/<int:aid>")
def download(aid):
    att = Attachment.query.get(aid)
    if not att:
        return fail("文件不存在", 404)
    path = os.path.join(_upload_dir(), att.file_path)
    if not os.path.exists(path):
        return fail("文件已丢失", 404)
    return send_file(path, as_attachment=True, download_name=att.file_name)


@bp.delete("/<int:aid>")
@login_required
def delete_file(aid):
    att = Attachment.query.get(aid)
    if not att:
        return fail("文件不存在", 404)
    path = os.path.join(_upload_dir(), att.file_path)
    if os.path.exists(path):
        os.remove(path)
    db.session.delete(att)
    db.session.commit()
    return ok()