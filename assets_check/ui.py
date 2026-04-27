import bpy
from . import properties as props_store
from .icon_manager import get_icon_id


CHECK_LABELS = {
    "ngon": "N多边面",
    "empty_material_slot": "空材质槽",
    "transform": "变换检查",
    "missing_textures": "贴图丢失",
    "uv_bounds": "UV越界",
    "uv_overlap": "UV重叠",
    "non_manifold": "非流形边",
    "loose_geometry": "游离点边",
    "doubled_vertices": "重叠顶点",
    "poles": "极点星点",
    "normal_direction": "法线方向",
    "nonplanar_faces": "不平整面",
    "self_intersection": "交叉边面",
    "zero_edges": "零边检查",
    "uv_layer_count": "UV数量",
    "vertex_color_count": "顶点色数",
    "ue_vertex_color_naming": "命名规范检查",
    "apply_scale": "应用缩放",
    "transform_zero": "变换归零",
    "pivot_position": "轴心位置",
    "modifier": "修改器",
    "animation": "动画检查",
    "vertex_weight": "顶点权重",
    "collision": "碰撞检查",
}

CHECK_LABELS_MATRIX = {
    "ngon": "N多边",
    "empty_material_slot": "空材",
    "transform": "变换",
    "missing_textures": "贴图",
    "uv_bounds": "UV越",
    "uv_overlap": "UV叠",
    "non_manifold": "非流",
    "loose_geometry": "游离",
    "doubled_vertices": "重顶",
    "poles": "极点",
    "normal_direction": "法线",
    "nonplanar_faces": "不平",
    "self_intersection": "交叉",
    "zero_edges": "零边",
    "uv_layer_count": "UV数",
    "vertex_color_count": "顶色",
    "ue_vertex_color_naming": "命名",
    "apply_scale": "应缩",
    "transform_zero": "变归",
    "pivot_position": "轴心",
    "modifier": "修改",
    "animation": "动画",
    "vertex_weight": "权重",
    "collision": "碰撞",
}

CHECK_LABELS_MATRIX_2LINE = {
    "ngon": ("N多", "边面"),
    "empty_material_slot": ("空材", "质槽"),
    "transform": ("变换", "检查"),
    "missing_textures": ("贴图", "丢失"),
    "uv_bounds": ("UV", "越界"),
    "uv_overlap": ("UV", "重叠"),
    "uv_layer_count": ("UV", "数"),
    "vertex_color_count": ("顶点", "色数"),
    "non_manifold": ("非流", "形边"),
    "loose_geometry": ("游离", "点边"),
    "doubled_vertices": ("重叠", "顶点"),
    "poles": ("极点", "星点"),
    "normal_direction": ("法线", "方向"),
    "nonplanar_faces": ("不平", "整面"),
    "self_intersection": ("交叉", "边面"),
    "zero_edges": ("零边", "检查"),
    "ue_vertex_color_naming": ("命名", "规范"),
    "apply_scale": ("应用", "缩放"),
    "transform_zero": ("变换", "归零"),
    "pivot_position": ("轴心", "位置"),
    "modifier": ("修改", "器"),
    "animation": ("动画", "检查"),
    "vertex_weight": ("顶点", "权重"),
    "collision": ("碰撞", "检查"),
}


def _enabled_check_ids(cfg):
    order = []
    # 与旧版矩阵顺序对齐，优先保证使用习惯
    mapping = [
        ("chk_empty_material_slot", "empty_material_slot"),
        ("chk_missing_textures", "missing_textures"),
        ("chk_uv_bounds", "uv_bounds"),
        ("chk_uv_overlap", "uv_overlap"),
        ("chk_uv_layer_count", "uv_layer_count"),
        ("chk_vertex_color_count", "vertex_color_count"),
        ("chk_ngon", "ngon"),
        ("chk_non_manifold", "non_manifold"),
        ("chk_loose_geometry", "loose_geometry"),
        ("chk_doubled_vertices", "doubled_vertices"),
        ("chk_poles", "poles"),
        ("chk_normal_direction", "normal_direction"),
        ("chk_nonplanar_faces", "nonplanar_faces"),
        ("chk_zero_edges", "zero_edges"),
        ("chk_self_intersection", "self_intersection"),
        ("chk_apply_scale", "apply_scale"),
        ("chk_transform_zero", "transform_zero"),
        ("chk_pivot_position", "pivot_position"),
        ("chk_modifier", "modifier"),
        ("chk_animation", "animation"),
        ("chk_vertex_weight", "vertex_weight"),
        ("chk_collision", "collision"),
        ("chk_ue_vertex_color_naming", "ue_vertex_color_naming"),
    ]
    for prop_name, check_id in mapping:
        if getattr(cfg, prop_name, False):
            order.append(check_id)
    return order


def _status_icon(status: str) -> str:
    if status == "PASS":
        return "CHECKMARK"
    if status == "FAIL":
        return "ERROR"
    return "INFO"


def _status_color(status: str):
    if status == "PASS":
        return (0.3, 0.7, 0.3, 1.0)
    if status == "FAIL":
        return (0.8, 0.2, 0.2, 1.0)
    return (0.8, 0.8, 0.2, 1.0)


def _draw_center_label(layout, text, *, translate=True):
    row = layout.row(align=True)
    row.alignment = "CENTER"
    row.label(text=text, translate=translate)


def _draw_status_dot(layout, status: str):
    row = layout.row(align=True)
    row.alignment = "CENTER"
    row.template_node_socket(color=_status_color(status))


def _draw_center_two_line_label(layout, line1: str, line2: str):
    col = layout.column(align=True)
    col.scale_y = 0.82
    top = col.row(align=True)
    top.alignment = "CENTER"
    top.label(text=line1)
    bottom = col.row(align=True)
    bottom.alignment = "CENTER"
    bottom.label(text=line2)


def _build_result_matrix(results):
    matrix = {}
    for item in results:
        matrix.setdefault(item.object_name, {})
        matrix[item.object_name][item.check_id] = {
            "status": item.status,
            "display_value": item.display_value,
        }
    return matrix


def _iter_matrix_rows(context, ui_state, result_matrix, check_ids):
    rows = []
    name_filter = (ui_state.search_query or "").strip().lower()
    for obj_name, checks in result_matrix.items():
        if name_filter and name_filter not in obj_name.lower():
            continue
        obj = bpy.data.objects.get(obj_name)
        if obj and obj.type == "MESH" and obj.data:
            obj.data.calc_loop_triangles()
            face_count = len(obj.data.loop_triangles)
        else:
            face_count = 0
        rows.append((obj_name, face_count, checks))

    sort_col = int(ui_state.sort_col)
    reverse = bool(ui_state.sort_reverse)
    if sort_col == 1:
        rows.sort(key=lambda x: x[1], reverse=reverse)
    elif sort_col >= 2 and (sort_col - 2) < len(check_ids):
        cid = check_ids[sort_col - 2]

        def _sort_val(row):
            checks = row[2]
            cell_data = checks.get(cid, {})
            if isinstance(cell_data, dict) and cell_data.get("display_value", "") != "":
                try:
                    return float(cell_data.get("display_value", "0"))
                except Exception:
                    return 0.0
            status = cell_data.get("status", "WARN") if isinstance(cell_data, dict) else "WARN"
            order = {"PASS": 0, "WARN": 1, "FAIL": 2}
            return order.get(status, 1)

        rows.sort(key=_sort_val, reverse=reverse)
    else:
        rows.sort(key=lambda x: x[0].lower(), reverse=reverse)
    return rows


def _display_object_name(raw_name: str) -> str:
    """
    统一对象显示名称：
    - 对 UI 输出使用原始名称（不翻译）
    """
    return raw_name or ""


def draw_assets_check_next_content(layout, context):
    scene = context.scene
    props = scene.assets_check_next_props
    ui_state = scene.ac_ui_state
    addon = context.preferences.addons.get(__package__)
    cfg = addon.preferences if addon else props
    results = scene.assets_check_next_results

    checks_box = layout.box()
    header_row = checks_box.row(align=True)
    header_row.prop(ui_state, "show_config", text="", icon="TRIA_DOWN" if ui_state.show_config else "TRIA_RIGHT", emboss=False)
    header_row.label(text="自定义检查")
    if ui_state.show_config:
        if len(props.presets_collection) == 0:
            try:
                props_store.sync_preset_collection(props)
            except Exception:
                pass

        box_presets = checks_box.box()
        row_preset = box_presets.row(align=True)
        row_preset.scale_y = 1.2
        row_preset.template_list(
            "ASSETSCHECKNEXT_UL_PresetList",
            "",
            props,
            "presets_collection",
            props,
            "active_preset_index",
            rows=3,
        )
        col_preset_ops = row_preset.column(align=True)
        col_preset_ops.operator("assets_check_next.preset_save", text="", icon="ADD")
        col_preset_ops.operator("assets_check_next.preset_remove_active", text="", icon="X")
        row_io = box_presets.row(align=True)
        row_io.operator("assets_check_next.preset_import", text="导入预设", icon="IMPORT")
        row_io.operator("assets_check_next.preset_export_dialog", text="导出预设", icon="EXPORT")

        mat_box = checks_box.box()
        mat_box.label(text="材质与贴图 (Materials)", icon="MATERIAL")
        mat_flow = mat_box.column_flow(columns=2, align=True)
        mat_flow.prop(cfg, "chk_empty_material_slot")
        mat_flow.prop(cfg, "chk_missing_textures")

        uv_box = checks_box.box()
        uv_box.label(text="UV与颜色 (UVs & Colors)", icon="UV")
        uv_flow = uv_box.column_flow(columns=2, align=True)
        uv_flow.prop(cfg, "chk_uv_bounds")
        uv_flow.prop(cfg, "chk_uv_overlap")
        uv_flow.prop(cfg, "chk_uv_layer_count")
        uv_flow.prop(cfg, "chk_vertex_color_count")
        uv_flow.prop(cfg, "chk_ignore_uv0")

        topo_box = checks_box.box()
        topo_box.label(text="拓扑与几何 (Topology & Geometry)", icon="MESH_DATA")
        topo_flow = topo_box.column_flow(columns=2, align=True)
        topo_flow.prop(cfg, "chk_ngon")
        topo_flow.prop(cfg, "chk_non_manifold")
        topo_flow.prop(cfg, "chk_ignore_manifold_open")
        topo_flow.prop(cfg, "chk_loose_geometry")
        topo_flow.prop(cfg, "chk_doubled_vertices")
        topo_flow.prop(cfg, "chk_poles")
        topo_flow.prop(cfg, "chk_normal_direction")
        topo_flow.prop(cfg, "chk_nonplanar_faces")
        topo_flow.prop(cfg, "chk_zero_edges")
        topo_flow.prop(cfg, "chk_self_intersection")

        obj_box = checks_box.box()
        obj_box.label(text="物体与数据 (Object & Data)", icon="OBJECT_DATA")
        obj_flow = obj_box.column_flow(columns=2, align=True)
        obj_flow.prop(cfg, "chk_apply_scale")
        obj_flow.prop(cfg, "chk_transform_zero")
        obj_flow.prop(cfg, "chk_pivot_position")
        obj_flow.prop(cfg, "chk_modifier")
        obj_flow.prop(cfg, "chk_animation")
        obj_flow.prop(cfg, "chk_vertex_weight")
        obj_flow.prop(cfg, "chk_collision")

        naming_box = checks_box.box()
        naming_box.label(text="命名规范 (Naming)", icon="SYNTAX_OFF")
        naming_box.prop(cfg, "chk_ue_vertex_color_naming")

    btn_col = layout.column(align=False)
    btn_col.scale_y = 1.5
    btn_row = btn_col.row(align=True)
    btn_row.operator("assets_check_next.run_checks", text="开始检查", icon_value=get_icon_id("timer-outline.png"))
    btn_row.operator("assets_check_next.auto_fix_basic", text="一键修复", icon="TOOL_SETTINGS")
    export_row = btn_col.row(align=True)
    export_row.operator("assets_check_next.export_report", text="导出报告 (CSV、JSON)", icon="EXPORT")

    layout.separator(factor=1.0)
    info_split = layout.split(factor=0.30, align=True)
    info_col = info_split.column(align=True)
    selected_mesh_count = len([o for o in context.selected_objects if o.type == "MESH"])
    info_col.label(text=f"选中的物体数量: {selected_mesh_count}")
    info_bottom = info_col.split(factor=0.70, align=True)
    info_bottom.label(text=f"检查的物体数量: {props.checked_object_count}")
    info_bottom.operator("assets_check_next.select_all_checked", text="全选")
    search_split = info_split.split(factor=0.01, align=True)
    search_split.separator(factor=1.0)
    search_col = search_split.column(align=True)
    search_col.separator(factor=4.0)
    search_col.prop(ui_state, "search_query", text="", icon_value=get_icon_id("search-outline.png"))
    layout.separator(factor=1.0)

    # 外层不再使用 box，避免表格外围多一圈边框
    matrix_box = layout.column(align=True)
    check_ids = _enabled_check_ids(cfg)
    result_matrix = _build_result_matrix(results)
    if not result_matrix:
        matrix_box.label(text="暂无结果")
    else:
        matrix_rows = _iter_matrix_rows(context, ui_state, result_matrix, check_ids)
        if not matrix_rows:
            matrix_box.label(text="筛选后无结果")
            return

        # 与 v1 同构：左侧信息区固定比例，名称/面数内部再按 70/30 划分
        left_factor = 0.24
        name_factor = 0.72
        table_col = matrix_box.column(align=True)

        menu_map = {
            "empty_material_slot": "ASSETSCHECKNEXT_MT_QF_EmptyMaterial",
            "missing_textures": "ASSETSCHECKNEXT_MT_QF_MissingTextures",
            "uv_bounds": "ASSETSCHECKNEXT_MT_QF_UVBounds",
            "uv_overlap": "ASSETSCHECKNEXT_MT_QF_UVOverlap",
            "vertex_color_count": "ASSETSCHECKNEXT_MT_QF_VertexColor",
            "ngon": "ASSETSCHECKNEXT_MT_QF_Ngon",
            "non_manifold": "ASSETSCHECKNEXT_MT_QF_NonManifold",
            "loose_geometry": "ASSETSCHECKNEXT_MT_QF_LooseGeometry",
            "doubled_vertices": "ASSETSCHECKNEXT_MT_QF_DoubledVertices",
            "poles": "ASSETSCHECKNEXT_MT_QF_Poles",
            "normal_direction": "ASSETSCHECKNEXT_MT_QF_NormalDirection",
            "nonplanar_faces": "ASSETSCHECKNEXT_MT_QF_NonplanarFaces",
            "zero_edges": "ASSETSCHECKNEXT_MT_QF_ZeroEdges",
            "self_intersection": "ASSETSCHECKNEXT_MT_QF_SelfIntersection",
            "apply_scale": "ASSETSCHECKNEXT_MT_QF_ApplyScale",
            "transform_zero": "ASSETSCHECKNEXT_MT_QF_TransformZero",
            "pivot_position": "ASSETSCHECKNEXT_MT_QF_PivotPosition",
            "modifier": "ASSETSCHECKNEXT_MT_QF_Modifier",
            "vertex_weight": "ASSETSCHECKNEXT_MT_QF_VertexWeight",
            "collision": "ASSETSCHECKNEXT_MT_QF_Collision",
            "ue_vertex_color_naming": "ASSETSCHECKNEXT_MT_QF_NamingPrefix",
        }

        # 第一横条：左侧名称/面数表头 + 右侧每列（菜单+两行文字纵向叠放）
        header_split = table_col.split(factor=left_factor, align=True)

        header_left = header_split.split(factor=name_factor, align=True)
        name_hdr_col = header_left.column(align=True)
        name_hdr_box = name_hdr_col.box()
        name_hdr_box.scale_y = 1.6
        op = name_hdr_box.operator("assets_check_next.header_tooltip", text="名称", emboss=False)
        op.col_name = "名称"
        face_hdr_col = header_left.column(align=True)
        face_hdr_box = face_hdr_col.box()
        face_hdr_box.scale_y = 1.6
        op = face_hdr_box.operator("assets_check_next.header_tooltip", text="面数", emboss=False)
        op.col_name = "面数"

        header_right = header_split.row(align=True)
        for cid in check_ids:
            col = header_right.column(align=True)
            menu_id = menu_map.get(cid)
            if menu_id:
                col.menu(menu_id, text="", icon_value=0)
            else:
                col.label(text=" ", icon_value=0)
            hbox = col.box()
            short = CHECK_LABELS_MATRIX_2LINE.get(cid)
            if short:
                key = f"{short[0]}-{short[1]}"
                text_col = hbox.column(align=True)
                text_col.scale_y = 0.8
                op1 = text_col.operator("assets_check_next.header_tooltip", text=short[0], emboss=False)
                op1.col_name = key
                op2 = text_col.operator("assets_check_next.header_tooltip", text=short[1], emboss=False)
                op2.col_name = key
            else:
                hbox.label(text=CHECK_LABELS_MATRIX.get(cid, cid))

        # 第二横条：排序箭头
        sort_split = table_col.split(factor=left_factor, align=True)

        sort_left = sort_split.split(factor=name_factor, align=True)
        sort_name_box = sort_left.box()
        sort_name_box.operator(
            "assets_check_next.sort_matrix", text="",
            icon_value=get_icon_id("caret-down-outline.png") if (ui_state.sort_col == 0 and not ui_state.sort_reverse) else (get_icon_id("caret-up-outline.png") if ui_state.sort_col == 0 else 0),
            emboss=False,
        ).sort_col = 0
        sort_face_box = sort_left.box()
        sort_face_box.operator(
            "assets_check_next.sort_matrix", text="",
            icon_value=get_icon_id("caret-down-outline.png") if (ui_state.sort_col == 1 and not ui_state.sort_reverse) else (get_icon_id("caret-up-outline.png") if ui_state.sort_col == 1 else 0),
            emboss=False,
        ).sort_col = 1

        sort_right = sort_split.row(align=True)
        for idx, cid in enumerate(check_ids):
            sbox = sort_right.box()
            sbox.operator(
                "assets_check_next.sort_matrix", text=" ",
                icon_value=get_icon_id("caret-down-outline.png") if (ui_state.sort_col == idx + 2 and not ui_state.sort_reverse) else (get_icon_id("caret-up-outline.png") if ui_state.sort_col == idx + 2 else 0),
                emboss=False,
            ).sort_col = idx + 2

        # 数据行
        for obj_name, face_count, checks in matrix_rows:
            data_split = table_col.split(factor=left_factor, align=True)

            data_left = data_split.split(factor=name_factor, align=True)
            data_name_box = data_left.box()
            name_row = data_name_box.row(align=True)
            active_obj = context.view_layer.objects.active
            is_active = active_obj and active_obj.name == obj_name
            op_pin = name_row.operator("assets_check_next.select_result_object", text="", icon_value=get_icon_id("location-pin.png"), emboss=is_active)
            op_pin.object_name = obj_name
            name_row.label(text=_display_object_name(obj_name), translate=False)
            data_face_box = data_left.box()
            data_face_box.label(text=str(face_count))

            data_right = data_split.row(align=True)
            for cid in check_ids:
                cell_data = checks.get(cid, {})
                cell = data_right.box()
                display_value = ""
                if isinstance(cell_data, dict):
                    display_value = str(cell_data.get("display_value", ""))

                if display_value != "":
                    cell.label(text=display_value)
                elif cid in {"uv_layer_count", "vertex_color_count"}:
                    cell.label(text="0")
                else:
                    status = cell_data.get("status", "WARN") if isinstance(cell_data, dict) else "WARN"
                    col_dot = cell.column(align=True)
                    col_dot.template_node_socket(color=_status_color(status))
                    spacer = col_dot.column(align=True)
                    spacer.scale_y = 1e-9
                    spacer.label(text="")


class ASSETSCHECK_PT_main_panel(bpy.types.Panel):
    bl_label = "资产审查助手"
    bl_idname = "ASSETSCHECK_PT_main_panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Assets_Check"

    def draw(self, context):
        draw_assets_check_next_content(self.layout, context)


class ASSETSCHECKNEXT_UL_PresetList(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        row = layout.row(align=True)
        row.label(text=item.name, icon="PRESET")
