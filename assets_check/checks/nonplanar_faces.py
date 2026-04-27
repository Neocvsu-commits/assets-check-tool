from .common import build_bmesh


def run(obj, context):
    bm = build_bmesh(obj.data)
    try:
        bad = 0
        threshold = 1e-4
        for f in bm.faces:
            if len(f.verts) <= 3:
                continue
            p0 = f.verts[0].co
            normal = f.normal
            for v in f.verts[1:]:
                if abs((v.co - p0).dot(normal)) > threshold:
                    bad += 1
                    break
        if bad > 0:
            return {"check_id": "nonplanar_faces", "status": "WARN", "message": f"检测到不平整面: {bad}"}
        return {"check_id": "nonplanar_faces", "status": "PASS", "message": "未检测到不平整面"}
    finally:
        bm.free()
