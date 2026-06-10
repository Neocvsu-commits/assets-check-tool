def run(obj, context, props, *, colliders=None):
    if obj.rigid_body:
        return {"check_id": "collision", "status": "PASS", "message": "已配置刚体碰撞"}

    if colliders is None:
        prefixes = ("UCX_", "UBX_", "UCP_", "USP_")
        colliders = [
            o for o in context.scene.objects
            if o.type == "MESH" and o.name.startswith(prefixes)
        ]

    base_name_raw = obj.name.replace("SM_", "")
    dense_col = False
    has_col = False

    for col_obj in colliders:
        col_base = col_obj.name.split("_", 1)[1] if "_" in col_obj.name else ""
        if not col_base:
            continue
        if obj.name.startswith(col_base) or col_base.startswith(base_name_raw):
            has_col = True
            if len(col_obj.data.polygons) > 64:
                dense_col = True
                break

    if dense_col:
        return {"check_id": "collision", "status": "FAIL", "message": "碰撞体面数超过64"}
    return {"check_id": "collision", "status": "PASS", "message": "碰撞检查通过"}
