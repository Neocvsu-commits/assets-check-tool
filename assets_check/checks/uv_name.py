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
    if len(uv_layers) > 1:
        # 多套UV列内显示首层名加省略标记，完整列表见悬浮提示
        display = uv_layers[0].name + ".."
    else:
        display = uv_layers[0].name
    return {
        "check_id": "uv_name",
        "status": "WARN",  # 信息项沿用WARN计数，但UI以文本展示
        "message": names,  # 完整层名列表，供单元格悬浮提示
        "display_value": display,
    }
