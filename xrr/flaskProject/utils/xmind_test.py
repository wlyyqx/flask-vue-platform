# make_test_xmind.py —— 生成一个用于测试的 .xmind
import zipfile, json

content = [{
    "id": "sheet-1",
    "class": "sheet",
    "title": "Sheet 1",
    "rootTopic": {
        "id": "root",
        "class": "topic",
        "title": "电商平台用例",
        "children": {
            "attached": [
                {
                    "id": "m1", "title": "登录模块",
                    "children": {"attached": [
                        {
                            "id": "c1", "title": "登录成功",
                            "markers": [{"markerId": "priority-1"}],
                            "children": {"attached": [
                                {"id": "s1", "title": "打开登录页",
                                 "children": {"attached": [{"id": "e1", "title": "展示登录框"}]}},
                                {"id": "s2", "title": "输入正确账密",
                                 "children": {"attached": [{"id": "e2", "title": "跳转首页"}]}},
                            ]},
                        },
                        {
                            "id": "c2", "title": "[P2] 登录失败 #回归",
                            "children": {"attached": [
                                {"id": "s3", "title": "输入错误密码||提示密码错误"},
                            ]},
                        },
                    ]},
                },
                {
                    "id": "m2", "title": "注册模块",
                    "children": {"attached": [
                        {"id": "c3", "title": "邮箱注册成功", "markers": [{"markerId": "priority-2"}]}
                    ]},
                },
            ]
        },
    },
}]

with zipfile.ZipFile("test.xmind", "w", zipfile.ZIP_DEFLATED) as zf:
    zf.writestr("content.json", json.dumps(content, ensure_ascii=False))
    # 补一个空的 manifest.json（不是必须，但更像真实 xmind）
    zf.writestr("metadata.json", json.dumps({"creator": {"name": "test"}}))

print("已生成 test.xmind")