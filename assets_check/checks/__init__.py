from .ngon import run as run_ngon
from .empty_material_slot import run as run_empty_material_slot
from .transform import run as run_transform
from .missing_textures import run as run_missing_textures
from .uv_bounds import run as run_uv_bounds
from .uv_overlap import run as run_uv_overlap
from .non_manifold import run as run_non_manifold
from .loose_geometry import run as run_loose_geometry
from .doubled_vertices import run as run_doubled_vertices
from .poles import run as run_poles
from .normal_direction import run as run_normal_direction
from .nonplanar_faces import run as run_nonplanar_faces
from .self_intersection import run as run_self_intersection
from .zero_edges import run as run_zero_edges
from .uv_layer_count import run as run_uv_layer_count
from .vertex_color_count import run as run_vertex_color_count
from .ue_vertex_color_naming import run as run_ue_vertex_color_naming
from .apply_scale import run as run_apply_scale
from .transform_zero import run as run_transform_zero
from .pivot_position import run as run_pivot_position
from .modifier import run as run_modifier
from .animation import run as run_animation
from .vertex_weight import run as run_vertex_weight
from .collision import run as run_collision


def _call_check(fn, obj, context, props):
    """
    兼容旧版/新版检查函数签名：
    - 旧版: run(obj, context)
    - 新版: run(obj, context, props)
    """
    try:
        return fn(obj, context, props)
    except TypeError:
        return fn(obj, context)


def run_checks_for_object(obj, context, props):
    rows = []
    # 基础项
    if props.chk_ngon:
        rows.append(_call_check(run_ngon, obj, context, props))
    if props.chk_empty_material_slot:
        rows.append(_call_check(run_empty_material_slot, obj, context, props))
    if props.chk_transform:
        rows.append(_call_check(run_transform, obj, context, props))
    if props.chk_missing_textures:
        rows.append(_call_check(run_missing_textures, obj, context, props))
    if props.chk_uv_bounds:
        rows.append(_call_check(run_uv_bounds, obj, context, props))
    if props.chk_uv_overlap:
        rows.append(_call_check(run_uv_overlap, obj, context, props))

    # A: 拓扑包
    if props.chk_non_manifold:
        rows.append(_call_check(run_non_manifold, obj, context, props))
    if props.chk_loose_geometry:
        rows.append(_call_check(run_loose_geometry, obj, context, props))
    if props.chk_doubled_vertices:
        rows.append(_call_check(run_doubled_vertices, obj, context, props))
    if props.chk_poles:
        rows.append(_call_check(run_poles, obj, context, props))

    # B: 法线/几何包
    if props.chk_normal_direction:
        rows.append(_call_check(run_normal_direction, obj, context, props))
    if props.chk_nonplanar_faces:
        rows.append(_call_check(run_nonplanar_faces, obj, context, props))
    if props.chk_self_intersection:
        rows.append(_call_check(run_self_intersection, obj, context, props))
    if props.chk_zero_edges:
        rows.append(_call_check(run_zero_edges, obj, context, props))

    # C: UV/顶点色包
    if props.chk_uv_layer_count:
        rows.append(_call_check(run_uv_layer_count, obj, context, props))
    if props.chk_vertex_color_count:
        rows.append(_call_check(run_vertex_color_count, obj, context, props))
    if props.chk_ue_vertex_color_naming:
        rows.append(_call_check(run_ue_vertex_color_naming, obj, context, props))

    # D: 物体数据包
    if props.chk_apply_scale:
        rows.append(_call_check(run_apply_scale, obj, context, props))
    if props.chk_transform_zero:
        rows.append(_call_check(run_transform_zero, obj, context, props))
    if props.chk_pivot_position:
        rows.append(_call_check(run_pivot_position, obj, context, props))
    if props.chk_modifier:
        rows.append(_call_check(run_modifier, obj, context, props))
    if props.chk_animation:
        rows.append(_call_check(run_animation, obj, context, props))
    if props.chk_vertex_weight:
        rows.append(_call_check(run_vertex_weight, obj, context, props))
    if props.chk_collision:
        rows.append(_call_check(run_collision, obj, context, props))
    return rows
