"""Built-in presets ship with the add-on; personal presets live in user config."""
import json
import os

import bpy


CHECK_KEYS = (
    'chk_ngon', 'chk_empty_material_slot', 'chk_transform', 'chk_missing_textures',
    'chk_uv_bounds', 'chk_uv_overlap', 'chk_uv_name', 'chk_uv_layer_count', 'chk_vertex_color_count',
    'chk_ignore_uv0', 'chk_non_manifold', 'chk_ignore_manifold_open',
    'chk_loose_geometry', 'chk_doubled_vertices', 'chk_poles', 'chk_normal_direction',
    'chk_nonplanar_faces', 'chk_self_intersection', 'chk_zero_edges', 'chk_apply_scale',
    'chk_transform_zero', 'chk_pivot_position', 'chk_modifier', 'chk_animation',
    'chk_vertex_weight', 'chk_ue_vertex_color_naming', 'chk_object_data_name_match',
)
PRESET_KEYS = (*CHECK_KEYS, 'naming_standard')
ALL_CHECKS = {**dict.fromkeys(CHECK_KEYS, True), 'naming_standard': 'PROJECT'}
BUILTIN_PRESETS = {
    '项目模型': {
        **ALL_CHECKS, 'naming_standard': 'PROJECT',
        'chk_uv_bounds': False, 'chk_uv_overlap': False,
        'chk_transform': False, 'chk_transform_zero': False, 'chk_pivot_position': False,
        'chk_object_data_name_match': False, 'chk_poles': False,
    },
    '资产库模型（独立贴图）': {**ALL_CHECKS, 'chk_ignore_uv0': False},
    '资产库模型（四方贴图）': dict(ALL_CHECKS),
}


def default_preset_all_enabled():
    return dict(ALL_CHECKS)


def _preset_file_path():
    folder = bpy.utils.user_resource('CONFIG', path='assets_check', create=True)
    if not folder:
        raise OSError('无法访问 Blender 用户配置目录')
    return os.path.join(folder, 'presets.json')


def validate_presets(data):
    if not isinstance(data, dict):
        raise ValueError('预设文件必须是名称与配置的 JSON 对象')
    clean = {}
    for name, cfg in data.items():
        if not isinstance(name, str) or not name.strip() or not isinstance(cfg, dict):
            raise ValueError('预设名称或配置格式不正确')
        values = {}
        for key in CHECK_KEYS:
            if key in cfg:
                if type(cfg[key]) is not bool:
                    raise ValueError(f'{name}: {key} 必须是布尔值')
                values[key] = cfg[key]
        standard = cfg.get('naming_standard', 'PROJECT')
        if standard not in {'PROJECT', 'ASSET'}:
            raise ValueError(f'{name}: 命名规范无效')
        # 旧的 ASSET（资产导出）模式已并入项目模式
        values['naming_standard'] = 'PROJECT'
        clean[name.strip()] = {**ALL_CHECKS, **values}
    return clean


def personal_presets(data):
    """Keep built-ins immutable, preserving older overrides under a distinct name."""
    result = {}
    for name, cfg in validate_presets(data).items():
        if name in BUILTIN_PRESETS:
            if cfg == BUILTIN_PRESETS[name]:
                continue
            name += '（自定义）'
        target = name
        i = 2
        while target in result:
            target = f'{name} {i}'
            i += 1
        result[target] = cfg
    return result


def save_presets(data):
    path = _preset_file_path()
    temporary = path + '.tmp'
    with open(temporary, 'w', encoding='utf-8') as stream:
        json.dump(personal_presets(data), stream, ensure_ascii=False, indent=2)
    os.replace(temporary, path)


def load_presets():
    path = _preset_file_path()
    legacy = os.path.join(os.path.dirname(__file__), 'assets_check_presets.json')
    source = path if os.path.exists(path) else legacy
    personal = {}
    if os.path.exists(source):
        try:
            with open(source, encoding='utf-8') as stream:
                personal = personal_presets(json.load(stream))
            if source == legacy and personal:
                save_presets(personal)
        except (OSError, ValueError) as exc:
            # Preserve the damaged file and keep the shipped defaults usable.
            print(f'[AssetsCheck] 预设加载失败，已保留原文件 {source}: {exc}')
    return {**{name: dict(cfg) for name, cfg in BUILTIN_PRESETS.items()}, **personal}


def collect_preset_data(props):
    return {key: getattr(props, key) for key in PRESET_KEYS if hasattr(props, key)}


def apply_preset_data(props, data):
    for key in PRESET_KEYS:
        if key in data and hasattr(props, key):
            setattr(props, key, data[key])


def sync_preset_collection(props):
    index = props.active_preset_index
    selected = props.presets_collection[index].name if 0 <= index < len(props.presets_collection) else ''
    names = list(load_presets())
    props.presets_collection.clear()
    for name in names:
        props.presets_collection.add().name = name
    props.active_preset_index = names.index(selected) if selected in names else 0


def update_active_preset_index(self, context):
    index = self.active_preset_index
    if 0 <= index < len(self.presets_collection):
        cfg = load_presets().get(self.presets_collection[index].name)
        if cfg:
            apply_preset_data(self, cfg)
            addon = context.preferences.addons.get(__package__)
            if addon:
                apply_preset_data(addon.preferences, cfg)


def sync_preferences_to_scene_props(context, scene_props):
    addon = context.preferences.addons.get(__package__)
    if addon:
        apply_preset_data(scene_props, collect_preset_data(addon.preferences))
