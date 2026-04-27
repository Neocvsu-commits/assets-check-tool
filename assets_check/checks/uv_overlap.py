import bpy


def run(obj, context, props):
    if not obj.data.uv_layers:
        return {"check_id": "uv_overlap", "status": "PASS", "message": "无UV层，跳过"}

    view_layer = context.view_layer
    prev_active = view_layer.objects.active
    prev_selected = list(context.selected_objects)
    prev_mode = context.mode
    prev_uv_index = obj.data.uv_layers.active_index

    try:
        if context.mode != "OBJECT":
            bpy.ops.object.mode_set(mode="OBJECT")
        bpy.ops.object.select_all(action="DESELECT")
        obj.select_set(True)
        view_layer.objects.active = obj

        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_all(action="SELECT")
        if props.chk_ignore_uv0 and len(obj.data.uv_layers) > 1:
            obj.data.uv_layers.active_index = 1
        bpy.ops.uv.select_overlap(extend=False)
        bpy.ops.object.mode_set(mode="OBJECT")

        uv_layer = obj.data.uv_layers.active
        has_overlap = any(loop.select for loop in uv_layer.data)
        if has_overlap:
            return {"check_id": "uv_overlap", "status": "FAIL", "message": "检测到UV重叠"}
        return {"check_id": "uv_overlap", "status": "PASS", "message": "未检测到UV重叠"}
    except Exception:
        return {"check_id": "uv_overlap", "status": "WARN", "message": "UV重叠检查执行失败，建议手动复核"}
    finally:
        try:
            bpy.ops.object.select_all(action="DESELECT")
            for o in prev_selected:
                if o and o.name in bpy.data.objects:
                    o.select_set(True)
            if prev_active and prev_active.name in bpy.data.objects:
                view_layer.objects.active = prev_active
            if prev_mode == "EDIT_MESH":
                bpy.ops.object.mode_set(mode="EDIT")
            elif prev_mode == "OBJECT":
                bpy.ops.object.mode_set(mode="OBJECT")
            if obj and obj.name in bpy.data.objects and obj.data.uv_layers:
                obj.data.uv_layers.active_index = prev_uv_index
        except Exception:
            pass
