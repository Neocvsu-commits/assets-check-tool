import bmesh


def run(obj, context):
    me = obj.data
    if me.has_custom_normals:
        return {"check_id": "normal_direction", "status": "PASS", "message": "使用自定义法线，跳过"}

    bm = bmesh.new()
    try:
        bm.from_mesh(me)
        if not bm.faces:
            return {"check_id": "normal_direction", "status": "WARN", "message": "无面数据，跳过"}

        bm.faces.ensure_lookup_table()
        original_normals = [f.normal.copy() for f in bm.faces]
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)

        flipped_count = 0
        for i, f in enumerate(bm.faces):
            if original_normals[i].dot(f.normal) < 0.0:
                flipped_count += 1

        if flipped_count > 0:
            return {"check_id": "normal_direction", "status": "FAIL", "message": f"检测到 {flipped_count} 个反向法线面"}
        return {"check_id": "normal_direction", "status": "PASS", "message": "法线方向正常"}
    finally:
        bm.free()
