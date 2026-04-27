import bmesh


def build_bmesh(mesh):
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bm.verts.ensure_lookup_table()
    bm.edges.ensure_lookup_table()
    bm.faces.ensure_lookup_table()
    return bm


def is_close(a, b, eps=1e-4):
    return abs(a - b) <= eps
