def run(obj, context):
    count = len(obj.modifiers)
    if count > 0:
        return {"check_id": "modifier", "status": "WARN", "message": f"存在未处理修改器: {count}"}
    return {"check_id": "modifier", "status": "PASS", "message": "无修改器"}
