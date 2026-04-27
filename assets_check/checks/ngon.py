def run(obj, context):
    has_ngon = any(poly.loop_total > 4 for poly in obj.data.polygons)
    if has_ngon:
        return {"check_id": "ngon", "status": "WARN", "message": "存在 N-gon（大于4边面）"}
    return {"check_id": "ngon", "status": "PASS", "message": "未发现 N-gon"}
