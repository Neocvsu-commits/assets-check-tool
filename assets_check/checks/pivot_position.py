from mathutils import Vector
import math


def _bbox_bottom_z(obj):
    """包围盒底部 Z 值（局部空间）."""
    return min(v[2] for v in obj.bound_box)


def _vertex_bottom_z(obj):
    """从顶点坐标计算底部 Z 值（局部空间，单趟遍历）."""
    min_z = math.inf
    for v in obj.data.vertices:
        if v.co.z < min_z:
            min_z = v.co.z
    return min_z


def run(obj, context, props):
    """检查轴心是否在几何底部 & 物体是否在世界原点.

    两轮判断：
    1. 包围盒底部 Z — 快速
    2. 顶点底部 Z — 回退，覆盖模型有特殊延伸的情况
    """

    world_loc = obj.matrix_world.translation
    dist_to_world = world_loc.length

    issues = []

    if obj.type == 'MESH' and obj.data.vertices:
        bottom_z = _bbox_bottom_z(obj)
        if abs(bottom_z) > 1e-3:
            # 包围盒不通过 → 顶点二轮
            bottom_z = _vertex_bottom_z(obj)
            if abs(bottom_z) > 1e-3:
                issues.append("轴心偏离底部")
    else:
        bottom_z = _bbox_bottom_z(obj)
        if abs(bottom_z) > 1e-3:
            issues.append("轴心偏离底部")

    if dist_to_world > 1e-3:
        issues.append("物体不在世界原点")

    if issues:
        return {"check_id": "pivot_position", "status": "FAIL", "message": " / ".join(issues)}
    return {"check_id": "pivot_position", "status": "PASS", "message": "轴心位于底部且在世界原点"}
