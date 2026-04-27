def run(obj, context):
    has_armature = any(m.type == "ARMATURE" for m in obj.modifiers)
    has_armature_parent = (
        getattr(obj, "parent", None) is not None
        and getattr(obj.parent, "type", None) == "ARMATURE"
    )

    if has_armature or has_armature_parent:
        has_weights = any(len(v.groups) > 0 for v in obj.data.vertices)
        if has_weights:
            return {"check_id": "vertex_weight", "status": "PASS", "message": "顶点权重存在"}
        return {"check_id": "vertex_weight", "status": "FAIL", "message": "骨骼模型缺少顶点权重"}

    if len(obj.vertex_groups) > 0:
        return {"check_id": "vertex_weight", "status": "FAIL", "message": "静态网格携带多余顶点组"}
    return {"check_id": "vertex_weight", "status": "PASS", "message": "无多余顶点组"}
