from .common import is_close


def run(obj, context):
    l = obj.location
    r = obj.rotation_euler
    has_loc = not (is_close(l.x, 0.0) and is_close(l.y, 0.0) and is_close(l.z, 0.0))
    has_rot = not (is_close(r.x, 0.0) and is_close(r.y, 0.0) and is_close(r.z, 0.0))
    if has_loc or has_rot:
        return {"check_id": "transform_zero", "status": "FAIL", "message": "变换未归零（位移/旋转）"}
    return {"check_id": "transform_zero", "status": "PASS", "message": "变换归零正常"}
