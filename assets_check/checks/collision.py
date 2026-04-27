def run(obj, context):
    if obj.rigid_body:
        return {"check_id": "collision", "status": "PASS", "message": "已配置刚体碰撞"}

    prefixes = ("UCX_", "UBX_", "UCP_", "USP_")
    base_name_raw = obj.name.replace("SM_", "")
    dense_col = False
    has_col = False

    for scene_obj in context.scene.objects:
        if scene_obj.type != "MESH" or not scene_obj.name.startswith(prefixes):
            continue
        col_base = scene_obj.name.split("_", 1)[1] if "_" in scene_obj.name else ""
        if not col_base:
            continue
        if obj.name.startswith(col_base) or col_base.startswith(base_name_raw):
            has_col = True
            if len(scene_obj.data.polygons) > 64:
                dense_col = True
                break

    if dense_col:
        return {"check_id": "collision", "status": "FAIL", "message": "碰撞体面数超过64"}
    return {"check_id": "collision", "status": "PASS", "message": "碰撞检查通过"}
