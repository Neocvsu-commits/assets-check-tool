def run(obj, context, props):
    uv_layers = obj.data.uv_layers
    if not uv_layers:
        return {
            "check_id": "uv_name",
            "status": "WARN",  # 信息项沿用WARN计数，但UI以文本展示
            "message": "无UV层",
            "display_value": "",
        }
    names = ", ".join(layer.name for layer in uv_layers)
    return {
        "check_id": "uv_name",
        "status": "WARN",  # 信息项沿用WARN计数，但UI以文本展示
        "message": f"UV层名称: {names}",
        "display_value": names,
    }
