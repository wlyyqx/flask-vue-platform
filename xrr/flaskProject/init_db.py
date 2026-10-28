from app import create_app
from app.extensions import db
from app.models import User

app = create_app()

with app.app_context():
    db.create_all()
    if not User.query.filter_by(username="admin").first():
        u = User(username="admin", real_name="管理员", role="admin")
        u.set_password("admin123")
        db.session.add(u)
        db.session.commit()
        print("✅ 已创建管理员: admin / admin123")
    else:
        print("ℹ️  管理员已存在")