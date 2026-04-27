from .common import build_bmesh


def run(obj, context):
    bm = build_bmesh(obj.data)
    try:
        has_loose = False
        for v in bm.verts:
            if len(v.link_edges) == 0:
                has_loose = True
                break
        if not has_loose:
            for e in bm.edges:
                if len(e.link_faces) == 0:
                    has_loose = True
                    break
        if has_loose:
            return {"check_id": "loose_geometry", "status": "WARN", "message": "检测到游离几何"}
        return {"check_id": "loose_geometry", "status": "PASS", "message": "未检测到游离几何"}
    finally:
        bm.free()
