from .common import build_bmesh


def run(obj, context, props, *, bm=None):
    _own = bm is None
    if _own:
        bm = build_bmesh(obj.data)
    try:
        poles = sum(1 for v in bm.verts if len(v.link_edges) > 6)
        if poles > 0:
            return {"check_id": "poles", "status": "WARN", "message": f"检测到极点星点: {poles}"}
        return {"check_id": "poles", "status": "PASS", "message": "未检测到极点星点"}
    finally:
        if _own:
            bm.free()
