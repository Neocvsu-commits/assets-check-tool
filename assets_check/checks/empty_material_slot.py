def run(obj, context):
    has_empty = any(slot.material is None for slot in obj.material_slots)
    if has_empty:
        return {"check_id": "empty_material_slot", "status": "FAIL", "message": "存在空材质槽"}
    return {"check_id": "empty_material_slot", "status": "PASS", "message": "材质槽正常"}
