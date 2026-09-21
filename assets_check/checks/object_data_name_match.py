import re

_DUP_SUFFIX = re.compile(r'\.\d+$')


def run(obj, context, props):
    if obj.type != 'MESH':
        return {"check_id": "object_data_name_match", "status": "PASS", "message": "非网格对象，跳过"}

    obj_name = obj.name
    data_name = obj.data.name

    if obj_name == data_name:
        return {"check_id": "object_data_name_match", "status": "PASS", "message": "物体名与网格数据名一致"}
    # 复制物体时 Blender 会加 .001 等后缀；忽略重复后缀后核心名一致视为匹配
    if _DUP_SUFFIX.sub("", obj_name) == _DUP_SUFFIX.sub("", data_name):
        return {"check_id": "object_data_name_match", "status": "PASS", "message": "忽略重复后缀后名称一致"}
    return {"check_id": "object_data_name_match", "status": "FAIL", "message": f"物体名 '{obj_name}' 与网格数据名 '{data_name}' 不匹配"}
