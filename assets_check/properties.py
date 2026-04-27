import bpy
import json
import os


PRESET_EXCLUDED_KEYS = set()

# 与 AddonPreferences / ASSETSCHECKNEXT_Props 中 chk_* 保持一致；预设「默认预设」为全部开启
DEFAULT_CHK_PRESET_KEYS = (
    "chk_ngon",
    "chk_empty_material_slot",
    "chk_transform",
    "chk_missing_textures",
    "chk_uv_bounds",
    "chk_uv_overlap",
    "chk_uv_layer_count",
    "chk_vertex_color_count",
    "chk_ignore_uv0",
    "chk_non_manifold",
    "chk_ignore_manifold_open",
    "chk_loose_geometry",
    "chk_doubled_vertices",
    "chk_poles",
    "chk_normal_direction",
    "chk_nonplanar_faces",
    "chk_self_intersection",
    "chk_zero_edges",
    "chk_apply_scale",
    "chk_transform_zero",
    "chk_pivot_position",
    "chk_modifier",
    "chk_animation",
    "chk_vertex_weight",
    "chk_collision",
    "chk_ue_vertex_color_naming",
)


def default_preset_all_enabled():
    return {k: True for k in DEFAULT_CHK_PRESET_KEYS}


def _preset_file_path():
    return os.path.join(os.path.dirname(__file__), "assets_check_presets.json")


def load_presets():
    file_path = _preset_file_path()
    if os.path.exists(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict) and data:
                if data.get("默认预设") == {}:
                    data["默认预设"] = default_preset_all_enabled()
                return data
        except Exception:
            pass
    return {"默认预设": default_preset_all_enabled()}


def save_presets(data):
    try:
        with open(_preset_file_path(), "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception:
        pass


def collect_preset_data(props):
    out = {}
    for key in dir(props):
        if not key.startswith("chk_"):
            continue
        if key in PRESET_EXCLUDED_KEYS:
            continue
        try:
            value = getattr(props, key)
        except Exception:
            continue
        if isinstance(value, bool):
            out[key] = value
    return out


def apply_preset_data(props, data):
    for key, value in data.items():
        if not key.startswith("chk_") or key in PRESET_EXCLUDED_KEYS:
            continue
        if hasattr(props, key):
            try:
                setattr(props, key, bool(value))
            except Exception:
                pass


def sync_preset_collection(props):
    presets = load_presets()
    props.presets_collection.clear()
    for name in presets.keys():
        item = props.presets_collection.add()
        item.name = str(name)


def update_active_preset_index(self, context):
    try:
        presets = load_presets()
        idx = self.active_preset_index
        if 0 <= idx < len(self.presets_collection):
            name = self.presets_collection[idx].name
            if name in presets:
                addon = context.preferences.addons.get(__package__)
                if addon and addon.preferences:
                    apply_preset_data(addon.preferences, presets[name])
    except Exception:
        pass


def sync_preferences_to_scene_props(context, scene_props):
    addon = context.preferences.addons.get(__package__)
    if not addon or not addon.preferences:
        return
    prefs = addon.preferences
    for key in dir(scene_props):
        if not key.startswith("chk_"):
            continue
        if hasattr(prefs, key):
            try:
                setattr(scene_props, key, getattr(prefs, key))
            except Exception:
                pass


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
    show_config: bpy.props.BoolProperty(name="显示配置区", default=True)
    search_query: bpy.props.StringProperty(name="搜索", default="")
    sort_col: bpy.props.IntProperty(name="排序列", default=0, min=0)
    sort_reverse: bpy.props.BoolProperty(name="降序", default=False)


class ASSETSCHECKNEXT_AddonPreferences(bpy.types.AddonPreferences):
    bl_idname = __package__

    chk_ngon: bpy.props.BoolProperty(name="N多边面", default=True)
    chk_empty_material_slot: bpy.props.BoolProperty(name="空材质槽", default=True)
    chk_transform: bpy.props.BoolProperty(name="变换检查", default=True)
    chk_missing_textures: bpy.props.BoolProperty(name="贴图丢失", default=True)
    chk_uv_bounds: bpy.props.BoolProperty(name="UV越界检查", default=True)
    chk_uv_overlap: bpy.props.BoolProperty(name="UV重叠", default=True)
    chk_uv_layer_count: bpy.props.BoolProperty(name="UV数量信息", default=True)
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
    chk_collision: bpy.props.BoolProperty(name="UE简易碰撞检查", default=True)
    chk_ue_vertex_color_naming: bpy.props.BoolProperty(name="命名不合规", default=True)

    def draw(self, context):
        self.layout.label(text="资产审查助手：配置在 3D 视图顶栏「检查」中编辑")


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

    chk_uv_layer_count: bpy.props.BoolProperty(name="UV数量信息", default=True)
    chk_vertex_color_count: bpy.props.BoolProperty(name="顶点色", default=True)
    chk_ue_vertex_color_naming: bpy.props.BoolProperty(name="命名不合规", default=True)

    chk_apply_scale: bpy.props.BoolProperty(name="缩放未应用", default=True)
    chk_transform_zero: bpy.props.BoolProperty(name="变换未归零", default=True)
    chk_pivot_position: bpy.props.BoolProperty(name="轴心位置", default=True)
    chk_modifier: bpy.props.BoolProperty(name="包含修改器", default=True)
    chk_animation: bpy.props.BoolProperty(name="包含动画数据", default=True)
    chk_vertex_weight: bpy.props.BoolProperty(name="顶点重量组检查", default=True)
    chk_collision: bpy.props.BoolProperty(name="UE简易碰撞检查", default=True)

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
