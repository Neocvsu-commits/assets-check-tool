import re


def run(obj, context, props=None):
    pattern = re.compile(r'^[a-zA-Z0-9_]+$')

    if not (pattern.match(obj.name) and obj.name.startswith("SM_")):
        return {"check_id": "ue_vertex_color_naming", "status": "FAIL", "message": "物体命名不合规"}

    for mat_slot in obj.material_slots:
        mat = mat_slot.material
        if mat:
            if not (pattern.match(mat.name) and mat.name.startswith("M_")):
                return {"check_id": "ue_vertex_color_naming", "status": "FAIL", "message": "材质命名不合规"}
            if mat.use_nodes and mat.node_tree:
                for node in mat.node_tree.nodes:
                    if node.type == "TEX_IMAGE" and node.image:
                        img_name = node.image.name.rsplit(".", 1)[0]
                        if not (pattern.match(img_name) and img_name.startswith("T_")):
                            return {"check_id": "ue_vertex_color_naming", "status": "FAIL", "message": "贴图命名不合规"}

    return {"check_id": "ue_vertex_color_naming", "status": "PASS", "message": "命名规范检查通过"}
