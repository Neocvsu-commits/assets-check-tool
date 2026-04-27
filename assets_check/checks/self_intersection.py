import bmesh
from mathutils.bvhtree import BVHTree


def run(obj, context):
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bm.verts.ensure_lookup_table()
    bm.faces.ensure_lookup_table()
    try:
        if len(bm.faces) < 2:
            return {"check_id": "self_intersection", "status": "PASS", "message": "面数过少，无交叉风险"}

        tree = BVHTree.FromBMesh(bm, epsilon=0.0)
        overlaps = tree.overlap(tree)
        hit = 0
        for a, b in overlaps:
            if a == b:
                continue
            fa = bm.faces[a]
            fb = bm.faces[b]
            if set(v.index for v in fa.verts) & set(v.index for v in fb.verts):
                continue
            hit += 1

        if hit > 0:
            return {"check_id": "self_intersection", "status": "WARN", "message": f"检测到交叉边面: {hit}"}
        return {"check_id": "self_intersection", "status": "PASS", "message": "未检测到交叉边面"}
    except Exception:
        return {"check_id": "self_intersection", "status": "WARN", "message": "交叉边面检查失败，建议手动复核"}
    finally:
        bm.free()
