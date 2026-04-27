def run(obj, context):
    loc = obj.location
    rot = obj.rotation_euler
    scale = obj.scale
    has_loc = abs(loc.x) > 0.001 or abs(loc.y) > 0.001 or abs(loc.z) > 0.001
    has_rot = abs(rot.x) > 0.001 or abs(rot.y) > 0.001 or abs(rot.z) > 0.001
    has_scale = abs(scale.x - 1.0) > 0.001 or abs(scale.y - 1.0) > 0.001 or abs(scale.z - 1.0) > 0.001
    if has_loc or has_rot or has_scale:
        return {"check_id": "transform", "status": "WARN", "message": "存在未应用的位移/旋转/缩放"}
    return {"check_id": "transform", "status": "PASS", "message": "Transform 已归零/应用"}
