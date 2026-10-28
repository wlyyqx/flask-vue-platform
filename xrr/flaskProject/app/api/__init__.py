from . import auth, project, module, testcase, plan, execution
from . import review, defect, file, excel, report, xmind


def register_blueprints(app):
    for m in (auth, project, module, testcase, plan, execution,
              review, defect, file, excel, report, xmind):
        app.register_blueprint(m.bp)