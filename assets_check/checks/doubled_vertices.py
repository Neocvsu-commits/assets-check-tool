import bmesh as _bmesh
from .common import build_bmesh


def run(obj, context):
    bm = build_bmesh(obj.data)
    try:
        v_count = len(bm.verts)
        _bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0001)
        has_double = len(bm.verts) < v_count
        if has_double:
            removed = v_count - len(bm.verts)
            return {"check_id": "doubled_vertices", "status": "WARN", "message": f"检测到重叠顶点: {removed}"}
        return {"check_id": "doubled_vertices", "status": "PASS", "message": "未检测到重叠顶点"}
    finally:
        bm.free()
