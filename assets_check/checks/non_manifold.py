from .common import build_bmesh


def run(obj, context, props):
    bm = build_bmesh(obj.data)
    try:
        ignore_open = getattr(props, "chk_ignore_manifold_open", False)
        has_bad = False
        for e in bm.edges:
            if not e.is_manifold:
                if ignore_open and len(e.link_faces) <= 1:
                    continue
                has_bad = True
                break
        if has_bad:
            return {"check_id": "non_manifold", "status": "WARN", "message": "检测到非流形边"}
        return {"check_id": "non_manifold", "status": "PASS", "message": "未检测到非流形边"}
    finally:
        bm.free()
