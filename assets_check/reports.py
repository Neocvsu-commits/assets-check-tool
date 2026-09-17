"""Two report views of the same check-time snapshot."""
import csv
import json
import os
import re


MODEL_COLUMNS = [
    '序号', '验收项目', '规范要求', '验收结果（合格/不合格）', '备注（不合格说明）',
]
SOP_REQUIREMENTS = [
    ('拓扑结构', '模型面都三角化导出，确保没有面重叠、软硬边问题、废点、孤立点、五边及以上面、反面问题'),
    ('模型尺寸', '建模时尽量尺寸为10的倍数（单位：cm）'),
    ('模型文件命名前缀', '以SM_开头，采用英文、拼音或缩写'),
    ('uv拆分', '是否有明显拉伸和尺寸不统一问题'),
    ('纹理质量', '命名是否正确   T_材质球名称_D   T_材质球名称_N   T_材质球名称_ORM\n是否为标准尺寸   512*512\n1024*1024\n……'),
    ('材质球数量', '同一模型不超过20个'),
    ('模型摆放', '放置在世界位置中心附近'),
]


def model_snapshot(obj, scene=None):
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
    if scene is None:
        import bpy
        scene = bpy.context.scene
    cm_per_unit = scene.unit_settings.scale_length * 100.0
    points = [obj.matrix_world @ vertex.co for vertex in mesh.vertices]
    bounds = [[min(point[i] for point in points), max(point[i] for point in points)] for i in range(3)] if points else [[0, 0]] * 3
    images = {}
    for slot in obj.material_slots:
        mat = slot.material
        if mat and mat.use_nodes and mat.node_tree:
            for node in mat.node_tree.nodes:
                if node.type == 'TEX_IMAGE' and node.image:
                    image = node.image
                    images[image.name] = {'name': image.name, 'size': list(image.size), 'filepath': image.filepath}
    return {
        'snapshot_version': 2,
        'object_name': obj.name, 'triangle_count': len(mesh.loop_triangles),
        'polygon_count': len(mesh.polygons), 'material_count': len(material_names),
        'material_names': material_names, 'has_animation': bool(has_animation),
        'non_triangle_faces': sum(len(face.vertices) != 3 for face in mesh.polygons),
        'uv_layer_count': len(mesh.uv_layers),
        'dimensions_cm': [(high - low) * cm_per_unit for low, high in bounds],
        'origin_cm': [v * cm_per_unit for v in obj.matrix_world.translation],
        'world_bounds_cm': [[v * cm_per_unit for v in pair] for pair in bounds],
        'textures': list(images.values()),
        'delivery_filename': str(obj.get('delivery_filename', obj.get('delivery_file_name', ''))),
        'remarks': str(obj.get('delivery_remarks', '')),
    }


def build_model_reports(snapshot, defaults):
    models = snapshot.get('models')
    if not models:
        raise ValueError('没有模型信息快照，请执行检查后导出模型报告')
    if any(model.get('snapshot_version') != 2 for model in models):
        raise ValueError('旧版检查结果缺少七项自查所需数据，请重新检查后导出')
    checks = snapshot.get('rows', [])
    result = []
    for model in models:
        name = model['object_name']
        object_checks = [row for row in checks if row.get('object_name') == name and row.get('check_id') != 'collision']
        by_id = {row['check_id']: row for row in object_checks}
        rows = []

        def add(index, status, notes):
            title, requirement = SOP_REQUIREMENTS[index - 1]
            rows.append([index, title, requirement, status, '；'.join(notes)])

        topology = ['ngon', 'loose_geometry', 'doubled_vertices', 'normal_direction', 'zero_edges', 'self_intersection']
        problems = [by_id[key]['message'] for key in topology if key in by_id and by_id[key]['status'] == 'FAIL']
        if model['non_triangle_faces']:
            problems.insert(0, f"源网格有 {model['non_triangle_faces']} 个非三角面，交付前需三角化并复核")
        missing = [key for key in topology if key not in by_id]
        note = problems + [f"源网格 {model['polygon_count']} 面，三角化后 {model['triangle_count']} 面"]
        if missing:
            note.append('部分拓扑检查未执行')
        note.append('软硬边、面重叠及反面需人工/UE复核；本报告未回读最终FBX')
        add(1, '不合格' if problems else '', note)

        dimensions = model['dimensions_cm']
        aligned = all(abs(value - round(value / 10) * 10) <= 0.01 for value in dimensions)
        add(2, '', [f"世界尺寸 X/Y/Z：{' / '.join(f'{v:.3f}' for v in dimensions)} cm",
                    '尺寸接近10 cm倍数' if aligned else '尺寸未全部接近10 cm倍数（SOP为建议项）',
                    '待人工对照CAD/实际尺寸确认，未自动缩放'])

        filename = model.get('delivery_filename') or defaults.get('delivery_filename', '')
        basename = filename.replace('\\', '/').rsplit('/', 1)[-1].strip()
        if basename:
            valid = bool(re.fullmatch(r'SM_[A-Za-z0-9_]+\.fbx', basename, re.IGNORECASE)) and basename.startswith('SM_')
            add(3, '合格' if valid else '不合格', [f'交付文件名：{basename}', '按填写的文件名检查，不以部件名代替文件名'])
        else:
            add(3, '', ['未填写交付FBX文件名，待确认；不能用Blender物体名推断'])

        if not model['uv_layer_count']:
            add(4, '不合格', ['没有UV层'])
        else:
            add(4, '', [f"UV层数：{model['uv_layer_count']}", '拉伸和纹理尺寸一致性待人工确认；UV不越界不代表无拉伸'])

        texture_problems = []
        texture_notes = []
        for texture in model['textures']:
            texture_name = os.path.splitext(texture['name'])[0]
            if not re.fullmatch(r'T_[A-Za-z0-9_]+_(D|N|R|M|ORM)', texture_name):
                texture_problems.append(f"贴图名称不符合T_名称_通道规范：{texture['name']}")
            width, height = texture['size']
            texture_notes.append(f"{texture['name']}：{width}×{height}")
            if width <= 0 or height <= 0:
                texture_problems.append(f"贴图尺寸不可读取：{texture['name']}")
            elif width != height or width & (width - 1):
                texture_problems.append(f"贴图不是标准的2次幂方形尺寸：{texture['name']}")
        if by_id.get('missing_textures', {}).get('status') == 'FAIL':
            texture_problems.append(by_id['missing_textures']['message'])
        invalid_materials = [mat for mat in model['material_names'] if not re.fullmatch(r'MI_[A-Za-z0-9_]+', mat)]
        if invalid_materials:
            texture_problems.append('SOP 1.4/1.6 材质名应为MI_：' + '、'.join(invalid_materials))
        if not model['textures']:
            texture_notes.append('源模型未关联贴图；FBX允许纯色占位材质，请核对独立贴图或复用UE材质')
        texture_notes.append('贴图与材质对应关系、Normal DirectX及ORM通道内容待人工复核')
        add(5, '不合格' if texture_problems else '', texture_problems + texture_notes)

        count = model['material_count']
        add(6, '合格' if count <= 20 else '不合格', [f'有效材质球数量：{count}',
                                                    '、'.join(model['material_names']) or '无材质球'])
        add(7, '', [f"物体世界原点 X/Y/Z：{' / '.join(f'{v:.3f}' for v in model['origin_cm'])} cm",
                    '待人工确认摆放：地块按SOP 1.7保留项目/CAD坐标；可复用件或动画备用件核对世界中心及功能轴心'])
        result.append({'model_name': name, 'rows': rows,
                       'remarks': '；'.join(v for v in (model.get('remarks'), defaults.get('remarks')) if v)})
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
    reports = build_model_reports(snapshot, defaults)
    metadata = {
        '项目名称': defaults.get('project_name', ''),
        '检查时间': snapshot.get('checked_at', ''),
    }
    with open(filepath, 'w', encoding='utf-8-sig', newline='') as stream:
        writer = csv.writer(stream)
        writer.writerow(['模型报告（地编）— 文件命名规范验收自查表'])
        writer.writerows(metadata.items())
        writer.writerow(['填写说明', '验收结果为空的项目需人工确认后填写合格/不合格；统计基于检查时源网格。'])
        for report in reports:
            writer.writerow([])
            writer.writerow(['模型名称', report['model_name']])
            if report['remarks']:
                writer.writerow(['补充说明', report['remarks']])
            writer.writerow(MODEL_COLUMNS)
            writer.writerows(report['rows'])
    _write_json(filepath, {
        'report_type': 'sop_acceptance', 'schema_version': 2,
        'metadata': metadata, 'export_columns': MODEL_COLUMNS,
        'reports': [{**report, 'rows': [dict(zip(MODEL_COLUMNS, row)) for row in report['rows']]} for report in reports],
        'models': snapshot['models'],
        'note': '每个已检查网格输出SOP第2.1节的七项验收自查表，空白结果待人工确认，不代表合格。',
    })


def _write_json(filepath, data):
    with open(os.path.splitext(filepath)[0] + '.json', 'w', encoding='utf-8') as stream:
        json.dump(data, stream, ensure_ascii=False, indent=2)
