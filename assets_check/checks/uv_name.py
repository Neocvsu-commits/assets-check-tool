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
        # 多套UV显示编号避免名称过长截断；完整层名见单元格悬浮提示
        display = ", ".join(f"UV{i}" for i in range(len(uv_layers)))
    else:
        display = uv_layers[0].name
    return {
        "check_id": "uv_name",
        "status": "WARN",  # 信息项沿用WARN计数，但UI以文本展示
        "message": names,  # 完整层名，供单元格悬浮提示
        "display_value": display,
    }
