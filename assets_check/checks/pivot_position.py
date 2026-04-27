from mathutils import Vector


def run(obj, context):
    bbox = obj.bound_box
    min_x = min(v[0] for v in bbox)
    max_x = max(v[0] for v in bbox)
    min_y = min(v[1] for v in bbox)
    max_y = max(v[1] for v in bbox)
    min_z = min(v[2] for v in bbox)

    bottom_center_local = Vector(((min_x + max_x) / 2, (min_y + max_y) / 2, min_z))
    dist_to_bottom = bottom_center_local.length

    world_loc = obj.matrix_world.translation
    dist_to_world = world_loc.length

    issues = []
    if dist_to_bottom > 1e-3:
        issues.append("轴心偏离底部中心")
    if dist_to_world > 1e-3:
        issues.append("物体不在世界原点")

    if issues:
        return {"check_id": "pivot_position", "status": "FAIL", "message": " / ".join(issues)}
    return {"check_id": "pivot_position", "status": "PASS", "message": "轴心位于底部中心且在世界原点"}
