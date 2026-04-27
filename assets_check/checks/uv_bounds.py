def run(obj, context, props):
    uv_layers = obj.data.uv_layers
    if not uv_layers:
        return {"check_id": "uv_bounds", "status": "PASS", "message": "无UV层，跳过"}

    layer_index = uv_layers.active_index
    if props.chk_ignore_uv0 and len(uv_layers) > 1:
        layer_index = 1
    uv_layer = uv_layers[layer_index]
    if not uv_layer:
        return {"check_id": "uv_bounds", "status": "PASS", "message": "无UV层，跳过"}

    for uv_loop in uv_layer.data:
        u, v = uv_loop.uv.x, uv_loop.uv.y
        if u < 0.0 or u > 1.0 or v < 0.0 or v > 1.0:
            return {"check_id": "uv_bounds", "status": "FAIL", "message": "存在UV越界（超出0-1）"}
    return {"check_id": "uv_bounds", "status": "PASS", "message": "UV范围正常"}
