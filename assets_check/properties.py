import bpy
import json
import os


from .presets import (
    BUILTIN_PRESETS, apply_preset_data, collect_preset_data,
    default_preset_all_enabled, load_presets, save_presets, sync_preset_collection,
    update_active_preset_index, sync_preferences_to_scene_props,
)


def naming_standard_property():
    return bpy.props.EnumProperty(
        name="命名规范",
        items=[("PROJECT", "项目资产（MI_）", "物体 SM_物体名，材质 MI_材质名，贴图 T_；名称支持多样符号，但不能出现 .001 等重复后缀")],
        default="PROJECT",
    )


class ASSETSCHECKNEXT_ResultItem(bpy.types.PropertyGroup):
    object_name: bpy.props.StringProperty(name="Object")
    check_id: bpy.props.StringProperty(name="Check")
    status: bpy.props.StringProperty(name="Status")
    message: bpy.props.StringProperty(name="Message")
    display_value: bpy.props.StringProperty(name="Display Value", default="")


class ASSETSCHECKNEXT_PresetItem(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty(name="Preset Name")
    export_enabled: bpy.props.BoolProperty(default=True)


class AssetsCheckUIState(bpy.types.PropertyGroup):
    show_config: bpy.props.BoolProperty(name="显示配置区", default=False)
    search_query: bpy.props.StringProperty(name="搜索", default="")
    sort_col: bpy.props.IntProperty(name="排序列", default=0, min=0)
    sort_reverse: bpy.props.BoolProperty(name="降序", default=False)


class ASSETSCHECKNEXT_AddonPreferences(bpy.types.AddonPreferences):
    bl_idname = __package__

    naming_standard: naming_standard_property()

    chk_ngon: bpy.props.BoolProperty(name="N多边面", default=True)
    chk_empty_material_slot: bpy.props.BoolProperty(name="空材质槽", default=True)
    chk_transform: bpy.props.BoolProperty(name="变换检查", default=True)
    chk_missing_textures: bpy.props.BoolProperty(name="贴图丢失", default=True)
    chk_uv_bounds: bpy.props.BoolProperty(name="UV越界检查", default=True)
    chk_uv_overlap: bpy.props.BoolProperty(name="UV重叠", default=True)
    chk_uv_name: bpy.props.BoolProperty(name="UV名称", default=True)
    chk_uv_layer_count: bpy.props.BoolProperty(name="UV数量", default=True)
    chk_vertex_color_count: bpy.props.BoolProperty(name="顶点色", default=True)
    chk_ignore_uv0: bpy.props.BoolProperty(name="豁免UV0(允许重叠/越界)", default=True)
    chk_non_manifold: bpy.props.BoolProperty(name="非流体边", default=True)
    chk_ignore_manifold_open: bpy.props.BoolProperty(name="豁免开放边界(面片)", default=True)
    chk_loose_geometry: bpy.props.BoolProperty(name="孤立/游离点边", default=True)
    chk_doubled_vertices: bpy.props.BoolProperty(name="重叠点", default=True)
    chk_poles: bpy.props.BoolProperty(name="极点(>6边)", default=True)
    chk_normal_direction: bpy.props.BoolProperty(name="法线方向", default=True)
    chk_nonplanar_faces: bpy.props.BoolProperty(name="不平整面", default=True)
    chk_self_intersection: bpy.props.BoolProperty(name="交叉边面", default=True)
    chk_zero_edges: bpy.props.BoolProperty(name="零边检查", default=True)
    chk_apply_scale: bpy.props.BoolProperty(name="缩放未应用", default=True)
    chk_transform_zero: bpy.props.BoolProperty(name="变换未归零", default=True)
    chk_pivot_position: bpy.props.BoolProperty(name="轴心点位置", default=True)
    chk_modifier: bpy.props.BoolProperty(name="包含修改器", default=True)
    chk_animation: bpy.props.BoolProperty(name="包含动画数据", default=True)
    chk_vertex_weight: bpy.props.BoolProperty(name="顶点重量/组检查", default=True)
    chk_ue_vertex_color_naming: bpy.props.BoolProperty(name="命名不合规", default=True)
    chk_object_data_name_match: bpy.props.BoolProperty(name="物体名与网格数据名不匹配", default=True)

    # 界面尺寸参数（像素）：控制检查矩阵列宽与弹窗宽度
    ui_name_width: bpy.props.IntProperty(
        name="名称列宽度", default=210, min=60, max=600,
        description="检查矩阵中物体名称列的宽度（像素）")
    ui_face_width: bpy.props.IntProperty(
        name="面数列宽度", default=55, min=30, max=300,
        description="检查矩阵中面数列的宽度（像素）")
    ui_check_width: bpy.props.IntProperty(
        name="检查列宽度", default=39, min=20, max=200,
        description="每个检查列的宽度（像素），所有检查列等宽")
    ui_popup_width: bpy.props.IntProperty(
        name="弹窗宽度", default=0, min=0, max=3000,
        description="审查弹窗总宽度（像素）；0 表示按上方列宽自动计算")

    def draw(self, context):
        from .ui import draw_support_preferences
        self.layout.label(text="检查与报告位于 3D 视图顶栏「检查」")
        size_box = self.layout.box()
        size_box.label(text="界面尺寸（像素）", icon="PREFERENCES")
        for prop_name in ("ui_name_width", "ui_face_width", "ui_check_width", "ui_popup_width"):
            size_box.prop(self, prop_name)
        draw_support_preferences(self.layout, context)


class ASSETSCHECKNEXT_Props(bpy.types.PropertyGroup):
    active_preset_index: bpy.props.IntProperty(
        name="Active Preset",
        default=0,
        update=update_active_preset_index,
    )
    presets_collection: bpy.props.CollectionProperty(type=ASSETSCHECKNEXT_PresetItem)
    show_custom_checks: bpy.props.BoolProperty(
        name="自定义检查",
        default=True,
    )

    # 检查项开关（先提供核心高频项）
    naming_standard: naming_standard_property()

    chk_ngon: bpy.props.BoolProperty(name="N多边面", default=True)
    chk_empty_material_slot: bpy.props.BoolProperty(name="空材质槽", default=True)
    chk_transform: bpy.props.BoolProperty(name="变换检查", default=True)
    chk_missing_textures: bpy.props.BoolProperty(name="贴图丢失", default=True)
    chk_uv_bounds: bpy.props.BoolProperty(name="UV越界", default=True)
    chk_uv_overlap: bpy.props.BoolProperty(name="UV重叠", default=True)
    chk_ignore_uv0: bpy.props.BoolProperty(name="豁免UV0(允许重叠/越界)", default=True)
    chk_non_manifold: bpy.props.BoolProperty(name="非流形边", default=True)
    chk_ignore_manifold_open: bpy.props.BoolProperty(name="豁免开放边界(面片)", default=True)
    chk_loose_geometry: bpy.props.BoolProperty(name="孤立/游离点边", default=True)
    chk_doubled_vertices: bpy.props.BoolProperty(name="重叠顶点", default=True)
    chk_poles: bpy.props.BoolProperty(name="极点星点", default=True)

    chk_normal_direction: bpy.props.BoolProperty(name="法线方向", default=True)
    chk_nonplanar_faces: bpy.props.BoolProperty(name="不平整面", default=True)
    chk_self_intersection: bpy.props.BoolProperty(name="交叉边面", default=True)
    chk_zero_edges: bpy.props.BoolProperty(name="零边检查", default=True)

    chk_uv_name: bpy.props.BoolProperty(name="UV名称", default=True)
    chk_uv_layer_count: bpy.props.BoolProperty(name="UV数量", default=True)
    chk_vertex_color_count: bpy.props.BoolProperty(name="顶点色", default=True)
    chk_ue_vertex_color_naming: bpy.props.BoolProperty(name="命名不合规", default=True)

    chk_apply_scale: bpy.props.BoolProperty(name="缩放未应用", default=True)
    chk_transform_zero: bpy.props.BoolProperty(name="变换未归零", default=True)
    chk_pivot_position: bpy.props.BoolProperty(name="轴心位置", default=True)
    chk_modifier: bpy.props.BoolProperty(name="包含修改器", default=True)
    chk_animation: bpy.props.BoolProperty(name="包含动画数据", default=True)
    chk_vertex_weight: bpy.props.BoolProperty(name="顶点重量组检查", default=True)
    chk_object_data_name_match: bpy.props.BoolProperty(name="物体名与网格数据名不匹配", default=True)

    total_items: bpy.props.IntProperty(name="Total", default=0)
    checked_object_count: bpy.props.IntProperty(name="Checked Objects", default=0)
    pass_count: bpy.props.IntProperty(name="Pass", default=0)
    warn_count: bpy.props.IntProperty(name="Warn", default=0)
    fail_count: bpy.props.IntProperty(name="Fail", default=0)
    last_run_at: bpy.props.StringProperty(name="Last Run", default="")
    results_json: bpy.props.StringProperty(name="Results JSON", default="")
    name_filter: bpy.props.StringProperty(name="名称过滤", default="")
    matrix_sort_key: bpy.props.StringProperty(name="矩阵排序列", default="name")
    matrix_sort_desc: bpy.props.BoolProperty(name="矩阵降序", default=False)
