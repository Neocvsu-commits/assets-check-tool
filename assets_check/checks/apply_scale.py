from .common import is_close


def run(obj, context):
    s = obj.scale
    ok = is_close(s.x, 1.0) and is_close(s.y, 1.0) and is_close(s.z, 1.0)
    if ok:
        return {"check_id": "apply_scale", "status": "PASS", "message": "缩放已应用"}
    return {"check_id": "apply_scale", "status": "FAIL", "message": "缩放未应用"}
