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
    "uv_name": "UV名称",
    "uv_layer_count": "UV数量",
    "vertex_color_count": "顶点色数",
    "ue_vertex_color_naming": "命名规范检查",
    "apply_scale": "应用缩放",
    "transform_zero": "变换归零",
    "pivot_position": "轴心位置",
    "modifier": "修改器",
    "animation": "动画检查",
    "vertex_weight": "顶点权重",
    "object_data_name_match": "物体名与数据名不匹配",
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
    "uv_name": "UV名",
    "uv_layer_count": "UV数",
    "vertex_color_count": "顶色",
    "ue_vertex_color_naming": "命名",
    "apply_scale": "应缩",
    "transform_zero": "变归",
    "pivot_position": "轴心",
    "modifier": "修改",
    "animation": "动画",
    "vertex_weight": "权重",
    "object_data_name_match": "名数",
}

CHECK_LABELS_MATRIX_2LINE = {
    "ngon": ("N多", "边面"),
    "empty_material_slot": ("空材", "质槽"),
    "transform": ("变换", "检查"),
    "missing_textures": ("贴图", "丢失"),
    "uv_bounds": ("UV", "越界"),
    "uv_overlap": ("UV", "重叠"),
    "uv_name": ("UV", "名称"),
    "uv_layer_count": ("UV", "数量"),
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
    "object_data_name_match": ("名数", "匹配"),
}


def _enabled_check_ids(cfg):
    order = []
    # 与旧版矩阵顺序对齐，优先保证使用习惯
    mapping = [
        ("chk_empty_material_slot", "empty_material_slot"),
        ("chk_missing_textures", "missing_textures"),
        ("chk_transform", "transform"),
        ("chk_uv_bounds", "uv_bounds"),
        ("chk_uv_overlap", "uv_overlap"),
        ("chk_uv_name", "uv_name"),
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
        ("chk_ue_vertex_color_naming", "ue_vertex_color_naming"),
        ("chk_object_data_name_match", "object_data_name_match"),
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


# 信息列超过阈值时加黄色提示点：UV多层、顶点色数
_INFO_LIMITS = {"uv_layer_count": 1, "vertex_color_count": 1}


def _matrix_layout_metrics(context, check_ids):
    """矩阵布局度量：返回 (弹窗宽度, left_factor, name_factor)，均由偏好设置尺寸参数计算."""
    addon = context.preferences.addons.get(__package__)
    prefs = addon.preferences if addon else None
    name_w = int(getattr(prefs, "ui_name_width", 210) or 210)
    face_w = int(getattr(prefs, "ui_face_width", 55) or 55)
    check_w = int(getattr(prefs, "ui_check_width", 39) or 39)
    override = int(getattr(prefs, "ui_popup_width", 0) or 0)
    auto_w = 40 + name_w + face_w + len(check_ids) * check_w
    popup_w = override if override > 0 else auto_w
    body_w = max(popup_w - 40, name_w + face_w + 10)
    left_factor = min(max((name_w + face_w) / float(body_w), 0.05), 0.7)
    name_factor = name_w / float(name_w + face_w)
    return popup_w, left_factor, name_factor


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
            "message": item.message,
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


def _draw_update_banner(layout):
    """Always show the installed version and the update entry in the working UI."""
    from . import bl_info
    from .update_checker import get_update_info, get_check_status

    row = layout.row(align=True)
    row.alignment = "LEFT"
    row.label(text="v" + ".".join(map(str, bl_info["version"])), icon="INFO")
    row.operator("assets_check_next.check_update", text="检查更新", icon="FILE_REFRESH")
    status = get_check_status("Neocvsu-commits", "assets-check-tool")
    state = status.get("status", "pending")
    if state == "checking":
        row.label(text="检查中…", icon="SORTTIME")
    elif state == "no_update":
        row.label(text="已是最新版", icon="CHECKMARK")
    elif state == "error":
        layout.label(text="更新检查失败，请重试", icon="ERROR")
    elif state == "no_release":
        row.label(text="暂无发布版本", icon="INFO")

    info = get_update_info("Neocvsu-commits", "assets-check-tool")
    if info:
        update_row = layout.row(align=True)
        update_row.alert = True
        update_row.label(text=f"可更新至 v{info['latest_version']}", icon="IMPORT")
        update_row.operator("assets_check_next.install_update", text="一键更新", icon="IMPORT")
        update_row.operator("wm.url_open", text="更新说明", icon="URL").url = info["html_url"]



def draw_assets_check_next_content(layout, context):
    """绘制完整的资产检查面板内容，供弹窗/Panel 共用。"""
    _draw_update_banner(layout)
    scene = context.scene
    props = scene.assets_check_next_props
    ui_state = scene.ac_ui_state
    addon = context.preferences.addons.get(__package__)
    cfg = addon.preferences if addon else props
    results = scene.assets_check_next_results

    box_presets = layout.box()
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
    col_preset_ops.operator("assets_check_next.preset_move_up", text="", icon="TRIA_UP")
    col_preset_ops.operator("assets_check_next.preset_move_down", text="", icon="TRIA_DOWN")
    col_preset_ops.operator("assets_check_next.preset_remove_active", text="", icon="X")

    checks_box = layout.box()
    header_row = checks_box.row(align=True)
    header_row.prop(ui_state, "show_config", text="", icon="TRIA_DOWN" if ui_state.show_config else "TRIA_RIGHT", emboss=False)
    header_row.label(text="自定义检查")
    if ui_state.show_config:
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
        uv_flow.prop(cfg, "chk_uv_name")
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
        obj_flow.prop(cfg, "chk_object_data_name_match")

        naming_box = checks_box.box()
        naming_box.label(text="命名规范 (Naming)", icon="SYNTAX_OFF")
        naming_box.prop(cfg, "chk_ue_vertex_color_naming")

    btn_col = layout.column(align=False)
    btn_col.scale_y = 1.2
    btn_row = btn_col.row(align=True)
    # 高频操作使用蓝色高亮（按下态）突出；报告导出为常规样式
    btn_row.operator("assets_check_next.run_checks", text="开始检查", icon_value=get_icon_id("timer-outline.png"), depress=True)
    btn_row.operator("assets_check_next.auto_fix_basic", text="一键修复", icon="TOOL_SETTINGS", depress=True)
    btn_row.operator("assets_check_next.export_report", text="资产库模型报告", icon="EXPORT")
    btn_row.operator("assets_check_next.export_model_report", text="模型报告（地编）", icon="EXPORT")

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

        # 列宽由偏好设置的尺寸参数计算（名称/面数/检查列），弹窗宽度同源
        _, left_factor, name_factor = _matrix_layout_metrics(context, check_ids)
        table_col = matrix_box.column(align=True)

        menu_map = {
            "empty_material_slot": "ASSETSCHECKNEXT_MT_QF_EmptyMaterial",
            "missing_textures": "ASSETSCHECKNEXT_MT_QF_MissingTextures",
            "uv_bounds": "ASSETSCHECKNEXT_MT_QF_UVBounds",
            "uv_overlap": "ASSETSCHECKNEXT_MT_QF_UVOverlap",
            "uv_name": "ASSETSCHECKNEXT_MT_QF_UVName",
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
            "ue_vertex_color_naming": "ASSETSCHECKNEXT_MT_QF_NamingPrefix",
            "object_data_name_match": "ASSETSCHECKNEXT_MT_QF_ObjectDataNameMatch",
        }

        # Every column uses the same menu row and the same two title rows.
        menu_split = table_col.split(factor=left_factor, align=True)
        menu_left = menu_split.split(factor=name_factor, align=True)
        menu_left.label(text=" ")
        menu_left.label(text=" ")
        menu_right = menu_split.row(align=True)
        for cid in check_ids:
            menu_id = menu_map.get(cid)
            if menu_id:
                menu_right.menu(menu_id, text="", icon_value=0)
            else:
                menu_right.label(text=" ")

        header_split = table_col.split(factor=left_factor, align=True)
        header_left = header_split.split(factor=name_factor, align=True)

        def title_cell(parent, first, second, tooltip):
            cell = parent.box().column(align=True)
            cell.alignment = "CENTER"
            cell.scale_y = 0.8
            for label in (first, second):
                # 关闭翻译：界面词典会把 UV 等词条译成冗长名称（如 UV纹理坐标）
                op = cell.operator("assets_check_next.header_tooltip", text=label or " ", emboss=False, translate=False)
                op.col_name = tooltip

        title_cell(header_left, "名称", "", "名称")
        title_cell(header_left, "面数", "", "面数")
        header_right = header_split.row(align=True)
        for cid in check_ids:
            first, second = CHECK_LABELS_MATRIX_2LINE.get(cid, (CHECK_LABELS_MATRIX.get(cid, cid), ""))
            title_cell(header_right, first, second, f"{first}-{second}")

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
            name_row.alignment = "CENTER"
            active_obj = context.view_layer.objects.active
            is_active = active_obj and active_obj.name == obj_name
            op_pin = name_row.operator("assets_check_next.select_result_object", text="", icon_value=get_icon_id("location-pin.png"), emboss=is_active)
            op_pin.object_name = obj_name
            name_row.label(text=_display_object_name(obj_name), translate=False)
            data_face_box = data_left.box()
            data_face_box.alignment = "CENTER"
            data_face_box.label(text=str(face_count))

            data_right = data_split.row(align=True)
            for cid in check_ids:
                cell_data = checks.get(cid, {})
                cell = data_right.box()
                display_value = ""
                if isinstance(cell_data, dict):
                    display_value = str(cell_data.get("display_value", ""))

                if display_value != "":
                    row = cell.row(align=True)
                    row.alignment = "CENTER"
                    if cid == "uv_name":
                        op = row.operator(
                            "assets_check_next.cell_tooltip",
                            text=display_value, emboss=False, translate=False,
                        )
                        # 缩写与完整列表不同（多套UV）时，悬浮第二行显示全部层名
                        full = str(cell_data.get("message", ""))
                        op.tooltip = full if full != display_value else ""
                    else:
                        row.label(text=display_value, translate=False)
                    info_limit = _INFO_LIMITS.get(cid)
                    if info_limit is not None:
                        try:
                            if int(display_value) > info_limit:
                                row.template_node_socket(color=(0.8, 0.8, 0.2, 1.0))
                        except ValueError:
                            pass
                elif cid in {"uv_layer_count", "vertex_color_count"}:
                    cell.label(text="0")
                else:
                    status = cell_data.get("status", "WARN") if isinstance(cell_data, dict) else "WARN"
                    col_dot = cell.column(align=True)
                    col_dot.alignment = "CENTER"
                    col_dot.template_node_socket(color=_status_color(status))
                    spacer = col_dot.column(align=True)
                    spacer.scale_y = 1e-9
                    spacer.label(text="")



class ASSETSCHECK_PT_main_panel(bpy.types.Panel):
    bl_label = "资产审查"
    bl_idname = "ASSETSCHECK_PT_main_panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Assets_Check"

    def draw(self, context):
        draw_assets_check_next_content(self.layout, context)


class ASSETSCHECKNEXT_UL_PresetList(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        row = layout.row(align=True)
        row.label(text=item.name, icon="LOCKED" if item.name in props_store.BUILTIN_PRESETS else "PRESET")


def draw_support_preferences(layout, context):
    _draw_update_banner(layout)
    layout.separator()
    feedback_box = layout.box()
    feedback_box.label(text="反馈 & 支持", icon="HELP")
    fb_row = feedback_box.row(align=True)
    fb_row.operator(
        "wm.url_open",
        text="Bug / 功能建议",
        icon="GHOST_ENABLED",
    ).url = "https://github.com/Neocvsu-commits/assets-check-tool/issues/new"
    fb_row.operator(
        "wm.url_open",
        text="匿名反馈",
        icon="COMMUNITY",
    ).url = "https://docs.qq.com/form/page/DTkNKUE9RcUpOemRr"
    fb_row2 = feedback_box.row()
    fb_row2.operator(
        "wm.url_open",
        text="⭐ 作者主页（了解更多工具）",
        icon="URL",
    ).url = "https://github.com/Neocvsu-commits"

    box = layout.box()
    box.label(text="个人预设迁移", icon="PRESET")
    box.label(text="默认预设随插件安装；个人预设保存在 Blender 用户配置目录。")
    box.label(text="换电脑时先导出个人预设，在新电脑导入。")
    row = box.row(align=True)
    row.operator("assets_check_next.preset_import", text="导入预设", icon="IMPORT")
    row.operator("assets_check_next.preset_export_dialog", text="导出预设", icon="EXPORT")
