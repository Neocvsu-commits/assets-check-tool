def run(obj, context, props):
    count = len(obj.data.uv_layers)
    return {
        "check_id": "uv_layer_count",
        "status": "WARN",  # 信息项沿用WARN计数，但UI以数字展示
        "message": f"UV数量信息: {count}",
        "display_value": str(count),
    }
