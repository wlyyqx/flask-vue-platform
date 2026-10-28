from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from .extensions import db


class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    real_name = db.Column(db.String(50))
    email = db.Column(db.String(100))
    role = db.Column(db.String(20), default="user")
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, raw):
        self.password = generate_password_hash(raw)

    def check_password(self, raw):
        return check_password_hash(self.password, raw)

    def to_dict(self):
        return {
            "id": self.id, "username": self.username,
            "real_name": self.real_name, "email": self.email,
            "role": self.role, "is_active": self.is_active,
        }


class Project(db.Model):
    __tablename__ = "projects"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.Text)
    owner_id = db.Column(db.Integer, nullable=False)
    status = db.Column(db.Integer, default=1)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id, "name": self.name, "code": self.code,
            "description": self.description, "owner_id": self.owner_id,
            "status": self.status,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        }


class Module(db.Model):
    __tablename__ = "modules"
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, nullable=False, index=True)
    parent_id = db.Column(db.Integer, default=0)
    name = db.Column(db.String(100), nullable=False)
    sort = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {"id": self.id, "project_id": self.project_id,
                "parent_id": self.parent_id, "name": self.name, "sort": self.sort}


case_tag = db.Table(
    "case_tag",
    db.Column("case_id", db.Integer, db.ForeignKey("test_cases.id"), primary_key=True),
    db.Column("tag_id", db.Integer, db.ForeignKey("tags.id"), primary_key=True),
)


class Tag(db.Model):
    __tablename__ = "tags"
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, nullable=False)
    name = db.Column(db.String(50), nullable=False)
    color = db.Column(db.String(20), default="#409EFF")


class TestCase(db.Model):
    __tablename__ = "test_cases"
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, nullable=False, index=True)
    module_id = db.Column(db.Integer)
    case_no = db.Column(db.String(50), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    precondition = db.Column(db.Text)
    steps = db.Column(db.JSON)
    priority = db.Column(db.Integer, default=2)
    case_type = db.Column(db.String(20), default="functional")
    status = db.Column(db.Integer, default=1)
    current_version = db.Column(db.Integer, default=1)
    creator_id = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    tags = db.relationship("Tag", secondary=case_tag, lazy="selectin")

    def to_dict(self, detail=False):
        d = {
            "id": self.id, "project_id": self.project_id,
            "module_id": self.module_id, "case_no": self.case_no,
            "title": self.title, "priority": self.priority,
            "case_type": self.case_type, "status": self.status,
            "current_version": self.current_version,
            "tags": [{"id": t.id, "name": t.name, "color": t.color} for t in self.tags],
            "updated_at": self.updated_at.strftime("%Y-%m-%d %H:%M:%S") if self.updated_at else "",
        }
        if detail:
            d["precondition"] = self.precondition
            d["steps"] = self.steps or []
            d["created_at"] = self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else ""
        return d


class CaseVersion(db.Model):
    __tablename__ = "case_versions"
    id = db.Column(db.Integer, primary_key=True)
    case_id = db.Column(db.Integer, nullable=False, index=True)
    version = db.Column(db.Integer, nullable=False)
    snapshot = db.Column(db.JSON, nullable=False)
    change_log = db.Column(db.String(255))
    operator_id = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {"id": self.id, "case_id": self.case_id, "version": self.version,
                "snapshot": self.snapshot, "change_log": self.change_log,
                "operator_id": self.operator_id,
                "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S")}


class TestPlan(db.Model):
    __tablename__ = "test_plans"
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    status = db.Column(db.Integer, default=1)
    creator_id = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id, "project_id": self.project_id, "name": self.name,
            "description": self.description,
            "start_date": self.start_date.strftime("%Y-%m-%d") if self.start_date else None,
            "end_date": self.end_date.strftime("%Y-%m-%d") if self.end_date else None,
            "status": self.status, "creator_id": self.creator_id,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        }


class CaseExecution(db.Model):
    __tablename__ = "case_executions"
    id = db.Column(db.Integer, primary_key=True)
    plan_id = db.Column(db.Integer, nullable=False, index=True)
    case_id = db.Column(db.Integer, nullable=False)
    executor_id = db.Column(db.Integer, nullable=False)
    result = db.Column(db.Integer, nullable=False)  # 1通过 2失败 3阻塞 4跳过
    comment = db.Column(db.Text)
    duration_ms = db.Column(db.Integer, default=0)
    executed_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id, "plan_id": self.plan_id, "case_id": self.case_id,
            "executor_id": self.executor_id, "result": self.result,
            "comment": self.comment, "duration_ms": self.duration_ms,
            "executed_at": self.executed_at.strftime("%Y-%m-%d %H:%M:%S"),
        }


class Review(db.Model):
    __tablename__ = "reviews"
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, nullable=False, index=True)
    title = db.Column(db.String(200), nullable=False)
    case_ids = db.Column(db.JSON)         # [1, 2, 3]
    reviewer_ids = db.Column(db.JSON)     # [1, 2]
    status = db.Column(db.Integer, default=1)  # 1待评审 2评审中 3已完成 4取消
    creator_id = db.Column(db.Integer, nullable=False)
    deadline = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id, "project_id": self.project_id, "title": self.title,
            "case_ids": self.case_ids or [], "reviewer_ids": self.reviewer_ids or [],
            "status": self.status, "creator_id": self.creator_id,
            "deadline": self.deadline.strftime("%Y-%m-%d %H:%M:%S") if self.deadline else None,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        }


class ReviewComment(db.Model):
    __tablename__ = "review_comments"
    id = db.Column(db.Integer, primary_key=True)
    review_id = db.Column(db.Integer, nullable=False, index=True)
    case_id = db.Column(db.Integer, nullable=False)
    user_id = db.Column(db.Integer, nullable=False)
    result = db.Column(db.Integer, nullable=False)   # 1通过 2拒绝 3建议
    content = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id, "review_id": self.review_id, "case_id": self.case_id,
            "user_id": self.user_id, "result": self.result, "content": self.content,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        }


class Defect(db.Model):
    __tablename__ = "defects"
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, nullable=False, index=True)
    case_id = db.Column(db.Integer)
    execution_id = db.Column(db.Integer)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    severity = db.Column(db.Integer, default=2)   # 1致命 2严重 3一般 4轻微
    status = db.Column(db.Integer, default=1)     # 1新建 2处理中 3已解决 4关闭
    assignee_id = db.Column(db.Integer)
    creator_id = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id, "project_id": self.project_id,
            "case_id": self.case_id, "execution_id": self.execution_id,
            "title": self.title, "description": self.description,
            "severity": self.severity, "status": self.status,
            "assignee_id": self.assignee_id, "creator_id": self.creator_id,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            "updated_at": self.updated_at.strftime("%Y-%m-%d %H:%M:%S") if self.updated_at else "",
        }


class Attachment(db.Model):
    __tablename__ = "attachments"
    id = db.Column(db.Integer, primary_key=True)
    biz_type = db.Column(db.String(30), nullable=False)   # case/execution/defect
    biz_id = db.Column(db.Integer, nullable=False, index=True)
    file_name = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    file_size = db.Column(db.Integer, default=0)
    uploader_id = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id, "biz_type": self.biz_type, "biz_id": self.biz_id,
            "file_name": self.file_name, "file_size": self.file_size,
            "url": f"/api/files/{self.id}",
            "uploader_id": self.uploader_id,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        }