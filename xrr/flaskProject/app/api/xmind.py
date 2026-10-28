import io
import re
import json
import zipfile
from xml.etree import ElementTree as ET

from flask import Blueprint, request, g
from ..extensions import db
from ..models import TestCase, CaseVersion, Tag, Module
from ..utils import ok, fail, login_required

bp = Blueprint("xmind", __name__, url_prefix="/api/projects/<int:pid>/cases")

# XMind 内建优先级 marker -> 我们系统的 1/2/3/4
MARKER_PRIORITY = {
    "priority-1": 1, "priority-2": 2, "priority-3": 3,
    "priority-4": 4, "priority-5": 4, "priority-6": 4, "priority-7": 4,
}

# 标题里带 [P0]/P1/【P2】等前缀的也能识别
TITLE_PRIO_RE = re.compile(r"^\s*[\[【]?\s*[Pp](\d)\s*[\]】]?\s*[:：\-—]?\s*(.*)$")


def _split_prio_from_title(title: str):
    m = TITLE_PRIO_RE.match(title or "")
    if not m:
        return None, title
    p = int(m.group(1))
    if p in (0, 1, 2, 3):
        return p + 1, m.group(2).strip()
    return None, title


# ---------- 解析（统一成 {title, markers, children}） ----------

def _node_json(node):
    """新版 content.json 的节点"""
    title = node.get("title", "") or ""
    markers = [m.get("markerId") for m in (node.get("markers") or []) if m.get("markerId")]
    children = []
    ch = node.get("children") or {}
    for c in (ch.get("attached") or []):
        children.append(_node_json(c))
    return {"title": title, "markers": markers, "children": children}


def _tag(el):
    return el.tag.split("}")[-1]


def _node_xml(node):
    """老版 content.xml 的节点（跨命名空间）"""
    title = ""
    for child in node:
        if _tag(child) == "title":
            title = child.text or ""
            break
    markers = []
    for el in node.iter():
        if _tag(el) == "marker":
            # 兼容不同命名空间写法
            mid = (el.get("marker-id") or el.get("markerId")
                   or next((v for k, v in el.attrib.items() if k.endswith("marker-id")), None))
            if mid:
                markers.append(mid)
    children = []
    for ch in node:
        if _tag(ch) != "children":
            continue
        for topics in ch:
            if _tag(topics) != "topics":
                continue
            for topic in topics:
                if _tag(topic) == "topic":
                    children.append(_node_xml(topic))
    return {"title": title, "markers": markers, "children": children}


def _load_xmind(file_stream):
    """读取 .xmind，返回 [{title, markers, children}, ...]（每个 sheet 一个根）"""
    roots = []
    with zipfile.ZipFile(file_stream) as zf:
        names = zf.namelist()

        if "content.json" in names:
            data = json.loads(zf.read("content.json").decode("utf-8"))
            # content.json 结构： [ {sheet}, {sheet}, ... ]
            for sheet in data:
                root = sheet.get("rootTopic")
                if root:
                    roots.append(_node_json(root))
        elif "content.xml" in names:
            xml_bytes = zf.read("content.xml")
            root_el = ET.fromstring(xml_bytes)
            for sheet in root_el:
                if _tag(sheet) != "sheet":
                    continue
                for child in sheet:
                    if _tag(child) == "topic":
                        roots.append(_node_xml(child))
                        break
        else:
            raise ValueError("不是合法的 XMind 文件（缺少 content.json / content.xml）")
    return roots


# ---------- 脑图 -> 用例列表 ----------

def _flatten(roots):
    """
    层级约定：
      L1 = 模块
      L2 = 用例标题
      L3 = 步骤
      L4 = 预期
    也兼容：
      - L3 是叶子，且标题含 || 或 → 时自动拆分
      - 若 L2 无子节点，则 steps 为空
    """
    cases = []
    for root in roots:
        for l1 in root["children"]:
            module_name = (l1["title"] or "").strip() or "未分类"
            # 兼容：L1 直接是用例（没有 L2）
            l2_list = l1["children"] if l1["children"] else [l1]
            for l2 in l2_list:
                steps = []
                for l3 in l2["children"]:
                    if l3["children"]:
                        for l4 in l3["children"]:
                            steps.append({
                                "step": (l3["title"] or "").strip(),
                                "expect": (l4["title"] or "").strip(),
                            })
                    else:
                        t = (l3["title"] or "").strip()
                        if "||" in t:
                            s, e = t.split("||", 1)
                            steps.append({"step": s.strip(), "expect": e.strip()})
                        elif "→" in t:
                            s, e = t.split("→", 1)
                            steps.append({"step": s.strip(), "expect": e.strip()})
                        elif "->" in t:
                            s, e = t.split("->", 1)
                            steps.append({"step": s.strip(), "expect": e.strip()})
                        else:
                            steps.append({"step": t, "expect": ""})

                # 优先级：marker 优先，其次标题里的 [P0]
                prio = None
                for mk in l2["markers"]:
                    if mk in MARKER_PRIORITY:
                        prio = MARKER_PRIORITY[mk]
                        break
                title = l2["title"] or ""
                p_from_title, clean_title = _split_prio_from_title(title)
                if p_from_title:
                    prio = p_from_title
                    title = clean_title

                # 标签：标题以 #tag1 #tag2 结尾的也提取一下
                tags = re.findall(r"#([^\s#]+)", title)
                title = re.sub(r"#[^\s#]+", "", title).strip()

                if not title:
                    continue

                cases.append({
                    "module": module_name,
                    "title": title,
                    "priority": prio or 2,
                    "steps": steps,
                    "tags": tags,
                    "case_type": "functional",
                })
    return cases


# ---------- 接口 ----------

@bp.post("/import-xmind")
@login_required
def import_xmind(pid):
    f = request.files.get("file")
    if not f:
        return fail("请上传 .xmind 文件")

    try:
        roots = _load_xmind(io.BytesIO(f.read()))
    except zipfile.BadZipFile:
        return fail("文件不是合法的 .xmind（zip）格式")
    except Exception as e:
        return fail(f"XMind 解析失败: {e}")

    try:
        cases_data = _flatten(roots)
    except Exception as e:
        return fail(f"XMind 结构解析失败: {e}")

    if not cases_data:
        return fail("未从 XMind 中解析出任何用例（请检查层级结构）")

    # 建模块缓存
    module_cache = {}
    modules_created = 0

    def ensure_module(name):
        nonlocal modules_created
        if name in module_cache:
            return module_cache[name]
        m = Module.query.filter_by(project_id=pid, name=name, parent_id=0).first()
        if not m:
            m = Module(project_id=pid, name=name, parent_id=0)
            db.session.add(m)
            db.session.flush()
            modules_created += 1
        module_cache[name] = m
        return m

    base_count = TestCase.query.filter_by(project_id=pid).count()
    success, errors = 0, []

    for idx, item in enumerate(cases_data):
        try:
            module = ensure_module(item["module"])
            base_count += 1
            case = TestCase(
                project_id=pid,
                module_id=module.id,
                case_no=f"TC-{base_count:05d}",
                title=item["title"],
                precondition="",
                steps=item["steps"],
                priority=item["priority"],
                case_type=item["case_type"],
                creator_id=g.user.id,
            )
            for tag_name in item["tags"]:
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
                change_log="XMind 导入", operator_id=g.user.id))
            success += 1
        except Exception as e:
            errors.append(f"第 {idx + 1} 条 [{item.get('title')}]: {e}")

    db.session.commit()
    return ok({
        "success": success,
        "modules_created": modules_created,
        "errors": errors,
    })


@bp.get("/import-xmind/template-tips")
@login_required
def xmind_tips(pid):
    """给前端提示用的层级说明"""
    return ok({
        "levels": [
            "Level 1（根的直接子节点）= 模块名",
            "Level 2 = 用例标题（可加 [P0]/[P1] 前缀或 XMind 优先级图标）",
            "Level 3 = 步骤",
            "Level 4 = 预期结果",
        ],
        "compat": [
            "用例节点若无子节点，则 steps 为空",
            "步骤节点若是叶子且标题含 '||' 或 '→' 或 '->'，会自动拆分 步骤/预期",
            "标题里的 #标签 会被提取成标签",
        ],
    })