import bpy
import os


def run(obj, context):
    missing = []
    for slot in obj.material_slots:
        mat = slot.material
        if not (mat and mat.use_nodes and mat.node_tree):
            continue
        for node in mat.node_tree.nodes:
            if node.type != "TEX_IMAGE" or not node.image:
                continue
            img = node.image
            if getattr(img, "source", "") in {"GENERATED", "VIEWER"}:
                continue
            if getattr(img, "packed_file", None):
                continue
            abs_path = bpy.path.abspath(img.filepath)
            if abs_path and (not os.path.exists(abs_path)):
                missing.append(img.name)
    if missing:
        return {"check_id": "missing_textures", "status": "FAIL", "message": f"丢失贴图: {len(set(missing))} 个"}
    return {"check_id": "missing_textures", "status": "PASS", "message": "贴图路径正常"}
