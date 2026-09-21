def _out_of_bounds(uv_layer):
    for uv_loop in uv_layer.data:
        u, v = uv_loop.uv.x, uv_loop.uv.y
        if u < 0.0 or u > 1.0 or v < 0.0 or v > 1.0:
            return True
    return False


def run(obj, context, props):
    uv_layers = obj.data.uv_layers
    if not uv_layers:
        return {"check_id": "uv_bounds", "status": "PASS", "message": "无UV层，跳过"}

    if props.chk_ignore_uv0:
        # UV1+ 不在豁免范围，仍按正式标准判定
        if len(uv_layers) > 1 and _out_of_bounds(uv_layers[1]):
            return {"check_id": "uv_bounds", "status": "FAIL", "message": "UV1存在越界（超出0-1）"}
        if _out_of_bounds(uv_layers[0]):
            return {"check_id": "uv_bounds", "status": "WARN", "message": "UV0存在越界（已豁免，仅提示）"}
        return {"check_id": "uv_bounds", "status": "PASS", "message": "UV范围正常"}

    uv_layer = uv_layers[uv_layers.active_index]
    if uv_layer and _out_of_bounds(uv_layer):
        return {"check_id": "uv_bounds", "status": "FAIL", "message": "存在UV越界（超出0-1）"}
    return {"check_id": "uv_bounds", "status": "PASS", "message": "UV范围正常"}
