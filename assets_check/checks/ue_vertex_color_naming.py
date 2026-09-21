import re

# Blender 重名自动后缀，如 Wall.001 / MI_Wood.002
_DUP_SUFFIX = re.compile(r'\.\d+$')
# 支持命名多样性：字母、数字、下划线、横杠、点、正反斜杠（前缀规则单独校验）
_NAME = re.compile(r'^[A-Za-z0-9_\-./\\]+$')
_IMAGE_EXT = re.compile(r'\.(png|jpe?g|tga|exr|tiff?|bmp|psd|hdr)$', re.IGNORECASE)


def _dup_suffix(name):
    return _DUP_SUFFIX.search(name) is not None


def _fail(message):
    return {"check_id": "ue_vertex_color_naming", "status": "FAIL", "message": message}


def run(obj, context, props):
    warnings = []

    if _dup_suffix(obj.name):
        warnings.append(f"物体名带 .001 之类的重复后缀：{obj.name}")
    if not obj.name.startswith("SM_"):
        return _fail(f"物体命名不合规，应以 SM_ 开头：{obj.name}")
    if not _NAME.fullmatch(obj.name):
        warnings.append(f"物体名含非支持字符：{obj.name}")

    for mat_slot in obj.material_slots:
        mat = mat_slot.material
        if not mat:
            continue
        if _dup_suffix(mat.name):
            warnings.append(f"材质名带 .001 之类的重复后缀：{mat.name}")
        # SOP 1.4 / 1.6: all delivery materials use MI_, regardless of preset.
        if not mat.name.startswith("MI_"):
            return _fail(f"材质命名不合规，应为 MI_<材质名>：{mat.name}")
        if not _NAME.fullmatch(mat.name):
            warnings.append(f"材质名含非支持字符：{mat.name}")
        if mat.use_nodes and mat.node_tree:
            for node in mat.node_tree.nodes:
                if node.type == "TEX_IMAGE" and node.image:
                    img_name = node.image.name
                    stem = _IMAGE_EXT.sub("", img_name)
                    if _dup_suffix(img_name) or _dup_suffix(stem):
                        warnings.append(f"贴图名带 .001 之类的重复后缀：{img_name}")
                    if not stem.startswith("T_"):
                        return _fail(f"贴图命名不合规，应为 T_<名称>：{img_name}")
                    if not _NAME.fullmatch(stem):
                        warnings.append(f"贴图名含非支持字符：{img_name}")

    if warnings:
        return {"check_id": "ue_vertex_color_naming", "status": "WARN", "message": "；".join(warnings)}
    return {"check_id": "ue_vertex_color_naming", "status": "PASS", "message": "命名规范检查通过"}
