from .common import build_bmesh


def run(obj, context):
    bm = build_bmesh(obj.data)
    try:
        tiny = sum(1 for e in bm.edges if e.calc_length() <= 1e-6)
        if tiny > 0:
            return {"check_id": "zero_edges", "status": "WARN", "message": f"检测到零边: {tiny}"}
        return {"check_id": "zero_edges", "status": "PASS", "message": "未检测到零边"}
    finally:
        bm.free()
