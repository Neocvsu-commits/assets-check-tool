"""Two report views of the same check-time snapshot."""
import csv
import json
import os


MODEL_COLUMNS = [
    '序号', '模型名称', '模型面数（三角面）', '材质球数量',
    '贴图类型（四方连续/PBR烘焙贴图）', '预计完成时间', '实际提交时间',
    '提交方式（svn文件夹/直接导入项目文件）', '是否有动画', '备注（问题说明/特殊说明）',
]


def model_snapshot(obj):
    obj.update_from_editmode()
    mesh = obj.data
    mesh.calc_loop_triangles()
    material_names = sorted({slot.material.name for slot in obj.material_slots if slot.material})
    animation_blocks = [obj, mesh, mesh.shape_keys]
    # Parent animation also affects rigid parts such as doors.
    parent = obj.parent
    while parent:
        animation_blocks.append(parent)
        parent = parent.parent
    has_animation = any(
        getattr(block, 'animation_data', None) and (
            block.animation_data.action or block.animation_data.nla_tracks or block.animation_data.drivers
        ) for block in animation_blocks if block
    )
    return {
        'object_name': obj.name, 'triangle_count': len(mesh.loop_triangles),
        'polygon_count': len(mesh.polygons), 'material_count': len(material_names),
        'material_names': material_names, 'has_animation': bool(has_animation),
        'texture_type': str(obj.get('delivery_texture_type', '')),
        'expected_completion': str(obj.get('delivery_expected_completion', '')),
        'actual_submission': str(obj.get('delivery_actual_submission', '')),
        'submission_method': str(obj.get('delivery_submission_method', '')),
        'remarks': str(obj.get('delivery_remarks', '')),
    }


def build_model_rows(snapshot, defaults):
    models = snapshot.get('models')
    if not models:
        raise ValueError('旧检查结果没有模型信息快照，请重新执行检查后导出模型报告')
    checks = snapshot.get('rows', [])
    result = []
    for index, model in enumerate(models, 1):
        name = model['object_name']
        object_checks = [row for row in checks if row.get('object_name') == name and row.get('check_id') != 'collision']
        issues = [f"{row['status']}: {row.get('message', '')}" for row in object_checks if row.get('status') != 'PASS']
        notes = [model.get('remarks', ''), defaults.get('remarks', '')]
        notes.extend(issues)
        notes.append(f"已执行 {len(object_checks)} 项自查；L3还原度、尺寸及UE效果需人工验收")
        result.append([
            index, name, model['triangle_count'], model['material_count'],
            model.get('texture_type') or defaults.get('texture_type') or '待填写',
            model.get('expected_completion') or defaults.get('expected_completion', ''),
            model.get('actual_submission') or defaults.get('actual_submission', ''),
            model.get('submission_method') or defaults.get('submission_method', ''),
            '是' if model['has_animation'] else '否',
            '；'.join(note for note in notes if note),
        ])
    return result


def write_twin_report(filepath, snapshot):
    columns = ['Object', 'Check', 'Status', 'Message', 'DisplayValue']
    keys = ['object_name', 'check_id', 'status', 'message', 'display_value']
    rows = [{key: row.get(key, '') for key in keys} for row in snapshot.get('rows', []) if row.get('check_id') != 'collision']
    if not rows:
        raise ValueError('没有可导出的检查结果，请先执行检查')
    with open(filepath, 'w', encoding='utf-8-sig', newline='') as stream:
        writer = csv.writer(stream)
        writer.writerow(columns)
        writer.writerows([[row[key] for key in keys] for row in rows])
    payload = {**snapshot, 'report_type': 'twin', 'export_columns': columns, 'rows': rows}
    _write_json(filepath, payload)


def write_model_report(filepath, snapshot, defaults):
    rows = build_model_rows(snapshot, defaults)
    metadata = {
        '项目名称': defaults.get('project_name', ''),
        '项目质量及制作周期': defaults.get('project_quality', ''),
        '项目负责人': defaults.get('project_owner', ''),
        '主要模型数量（本报告网格数）': len(rows),
        '检查时间': snapshot.get('checked_at', ''),
        '检查预设': snapshot.get('preset_name', ''),
    }
    with open(filepath, 'w', encoding='utf-8-sig', newline='') as stream:
        writer = csv.writer(stream)
        writer.writerows(metadata.items())
        writer.writerow([])
        writer.writerow(MODEL_COLUMNS)
        writer.writerows(rows)
    _write_json(filepath, {
        'report_type': 'model', 'metadata': metadata, 'export_columns': MODEL_COLUMNS,
        'rows': [dict(zip(MODEL_COLUMNS, row)) for row in rows],
        'models': snapshot['models'],
        'note': '按检查时的网格逐行统计，非FBX导出后验收；一项资产的多个部件会分行列出。',
    })


def _write_json(filepath, data):
    with open(os.path.splitext(filepath)[0] + '.json', 'w', encoding='utf-8') as stream:
        json.dump(data, stream, ensure_ascii=False, indent=2)
