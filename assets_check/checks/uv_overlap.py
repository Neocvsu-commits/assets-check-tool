_GRID = 64  # cells per UV unit — 平衡精度与速度
_EPS = 1e-10


def _segments_intersect(a1, a2, b1, b2):
    """两线段是否在 2D 空间相交（含端点共线）."""
    def _cross(u, v):
        return u.x * v.y - u.y * v.x

    d1 = _cross(b2 - b1, a1 - b1)
    d2 = _cross(b2 - b1, a2 - b1)
    d3 = _cross(a2 - a1, b1 - a1)
    d4 = _cross(a2 - a1, b2 - a1)

    if ((d1 > _EPS and d2 < -_EPS) or (d1 < -_EPS and d2 > _EPS)) and \
       ((d3 > _EPS and d4 < -_EPS) or (d3 < -_EPS and d4 > _EPS)):
        return True

    # 共线退化情况
    def _on_seg(p, q, r):
        return (min(p.x, q.x) - _EPS <= r.x <= max(p.x, q.x) + _EPS and
                min(p.y, q.y) - _EPS <= r.y <= max(p.y, q.y) + _EPS)

    if abs(d1) <= _EPS and _on_seg(b1, b2, a1): return True
    if abs(d2) <= _EPS and _on_seg(b1, b2, a2): return True
    if abs(d3) <= _EPS and _on_seg(a1, a2, b1): return True
    if abs(d4) <= _EPS and _on_seg(a1, a2, b2): return True
    return False


def _point_in_triangle(p, tri):
    """点 p 是否在三角形 tri 内部（重心坐标法）."""
    v0, v1, v2 = tri
    d00 = (v1.x - v0.x) * (v1.x - v0.x) + (v1.y - v0.y) * (v1.y - v0.y)
    if d00 < _EPS:
        d00 = 1.0
    d01 = (v1.x - v0.x) * (v2.x - v0.x) + (v1.y - v0.y) * (v2.y - v0.y)
    d11 = (v2.x - v0.x) * (v2.x - v0.x) + (v2.y - v0.y) * (v2.y - v0.y)
    d20 = (p.x - v0.x) * (v1.x - v0.x) + (p.y - v0.y) * (v1.y - v0.y)
    d21 = (p.x - v0.x) * (v2.x - v0.x) + (p.y - v0.y) * (v2.y - v0.y)
    denom = d00 * d11 - d01 * d01
    if abs(denom) < _EPS:
        denom = 1.0
    v = (d11 * d20 - d01 * d21) / denom
    w = (d00 * d21 - d01 * d20) / denom
    u = 1.0 - v - w
    return u >= -_EPS and v >= -_EPS and w >= -_EPS


def _triangles_overlap(t1, t2):
    """两个 UV 三角形是否重叠."""
    # 边-边相交
    for i in range(3):
        a1, a2 = t1[i], t1[(i + 1) % 3]
        for j in range(3):
            b1, b2 = t2[j], t2[(j + 1) % 3]
            if _segments_intersect(a1, a2, b1, b2):
                return True
    # 包含关系
    if _point_in_triangle(t1[0], t2): return True
    if _point_in_triangle(t2[0], t1): return True
    return False


def run(obj, context, props):
    if not obj.data.uv_layers:
        return {"check_id": "uv_overlap", "status": "PASS", "message": "无UV层，跳过"}

    uv_layers = obj.data.uv_layers
    layer_index = 0
    if props.chk_ignore_uv0 and len(uv_layers) > 1:
        layer_index = 1
    uv_data = uv_layers[layer_index].data

    # 确保有预计算的三角剖分
    obj.data.calc_loop_triangles()
    loop_tris = obj.data.loop_triangles

    # 构建三角形数据（直接索引 uv_data，省去中间对象）
    triangles = []
    for tri in loop_tris:
        uvs = tuple(uv_data[li].uv.copy() for li in tri.loops)
        vert_set = frozenset(obj.data.loops[li].vertex_index for li in tri.loops)
        triangles.append((tri.polygon_index, vert_set, uvs))

    if len(triangles) < 2:
        return {"check_id": "uv_overlap", "status": "PASS", "message": "未检测到UV重叠"}

    # 空间哈希网格
    grid = {}
    for idx, (face_idx, vert_set, uvs) in enumerate(triangles):
        min_x = min(v.x for v in uvs)
        max_x = max(v.x for v in uvs)
        min_y = min(v.y for v in uvs)
        max_y = max(v.y for v in uvs)

        cx1 = max(0, int(min_x * _GRID))
        cy1 = max(0, int(min_y * _GRID))
        cx2 = min(_GRID - 1, int(max_x * _GRID))
        cy2 = min(_GRID - 1, int(max_y * _GRID))

        for cx in range(cx1, cx2 + 1):
            for cy in range(cy1, cy2 + 1):
                grid.setdefault((cx, cy), []).append(idx)

    # 去重检查
    checked = set()
    for idx, (face_idx, vert_set, uvs) in enumerate(triangles):
        # 查该三角形覆盖的所有网格单元中的候选（与插入逻辑一致）
        min_x = min(v.x for v in uvs)
        max_x = max(v.x for v in uvs)
        min_y = min(v.y for v in uvs)
        max_y = max(v.y for v in uvs)

        cx1 = max(0, int(min_x * _GRID))
        cy1 = max(0, int(min_y * _GRID))
        cx2 = min(_GRID - 1, int(max_x * _GRID))
        cy2 = min(_GRID - 1, int(max_y * _GRID))

        seen_candidates = set()
        for cx in range(cx1, cx2 + 1):
            for cy in range(cy1, cy2 + 1):
                for c in grid.get((cx, cy), ()):
                    seen_candidates.add(c)

        for other_idx in seen_candidates:
            if other_idx <= idx:
                continue
            pair = (idx, other_idx)
            if pair in checked:
                continue
            checked.add(pair)

            o_face_idx, o_vert_set, o_uvs = triangles[other_idx]

            # 同一面 → 跳过
            if face_idx == o_face_idx:
                continue
            # 共享 3D 顶点 → 相邻面，UV 共享边是正常的
            if vert_set & o_vert_set:
                continue
            # 快速 AABB 剔除
            if (max(v.x for v in uvs) < min(v.x for v in o_uvs) or
                min(v.x for v in uvs) > max(v.x for v in o_uvs) or
                max(v.y for v in uvs) < min(v.y for v in o_uvs) or
                min(v.y for v in uvs) > max(v.y for v in o_uvs)):
                continue

            if _triangles_overlap(uvs, o_uvs):
                return {"check_id": "uv_overlap", "status": "FAIL", "message": "检测到UV重叠"}

    return {"check_id": "uv_overlap", "status": "PASS", "message": "未检测到UV重叠"}
