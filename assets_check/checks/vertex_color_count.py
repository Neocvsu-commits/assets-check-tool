def run(obj, context, props):
    count = len(getattr(obj.data, "color_attributes", []))
    return {
        "check_id": "vertex_color_count",
        "status": "WARN",  # 信息项沿用WARN计数，但UI以数字展示
        "message": f"顶点色数量信息: {count}",
        "display_value": str(count),
    }
