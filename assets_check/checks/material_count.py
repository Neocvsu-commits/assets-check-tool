def run(obj, context, props):
    count = len({slot.material.name for slot in obj.material_slots if slot.material})
    return {
        "check_id": "material_count",
        "status": "WARN",  # 信息项沿用WARN计数，但UI以数字展示
        "message": f"材质球数量: {count}",
        "display_value": str(count),
    }
