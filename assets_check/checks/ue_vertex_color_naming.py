import re


def run(obj, context, props):
    pattern = re.compile(r'^[a-zA-Z0-9_]+$')

    project = getattr(props, "naming_standard", "ASSET") == "PROJECT"
    if not (pattern.fullmatch(obj.name) and (project or (obj.name.startswith("SM_") and len(obj.name) > 3))):
        return {"check_id": "ue_vertex_color_naming", "status": "FAIL", "message": "物体命名不合规"}

    for mat_slot in obj.material_slots:
        mat = mat_slot.material
        if mat:
            prefix = "MI_" if project else "M_"
            if not (pattern.fullmatch(mat.name) and mat.name.startswith(prefix) and len(mat.name) > len(prefix)):
                return {"check_id": "ue_vertex_color_naming", "status": "FAIL", "message": f"材质命名不合规，应为 {prefix}<材质名>"}
            if mat.use_nodes and mat.node_tree:
                for node in mat.node_tree.nodes:
                    if node.type == "TEX_IMAGE" and node.image:
                        img_name = node.image.name.rsplit(".", 1)[0]
                        if not (pattern.match(img_name) and img_name.startswith("T_")):
                            return {"check_id": "ue_vertex_color_naming", "status": "FAIL", "message": "贴图命名不合规"}

    return {"check_id": "ue_vertex_color_naming", "status": "PASS", "message": "命名规范检查通过"}
