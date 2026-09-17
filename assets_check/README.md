# 资产审查助手 v3.1.0

本版内置「项目资产要求」「资产导出要求」「全部检查」；个人预设独立保存于 Blender 用户配置目录，可导入/导出迁移。内置预设始终保留。

报告按钮分为「Twin 用模型报告」（完整检查明细）和「模型报告（地编）」（SOP 提交对接表），均输出 CSV/JSON。模型报告基于检查时的源网格快照，每个网格一行；修改后请重新检查。UE 简易碰撞检查已从界面、执行入口及报告中移除。

反馈、支持和更新入口位于插件偏好设置。

这是 `Assets_Check` 的并行重构版本，当前已完成检查内核 A/B/C/D 四组能力接入，并保持旧版风格 UI。

## 当前能力

- 选中对象检查（仅 MESH）：
  - 基础：`ngon`、`empty_material_slot`、`transform`、`missing_textures`、`uv_bounds`、`uv_overlap`
  - A 拓扑包：`non_manifold`、`loose_geometry`、`doubled_vertices`、`poles`
  - B 法线/几何包：`normal_direction`、`nonplanar_faces`、`self_intersection`、`zero_edges`
  - C UV/顶点色包：`uv_layer_count`、`vertex_color_count`、`ue_vertex_color_naming`
  - D 物体数据包：`apply_scale`、`transform_zero`、`pivot_position`、`modifier`、`animation`、`vertex_weight`
- 一键修复（无争议项）：清理空材质槽、清理游离几何、应用 Transform
- 结果汇总（PASS/WARN/FAIL）
- 导出报告（CSV + JSON）

## 目录

- `__init__.py`：入口与注册
- `properties.py`：状态与结果结构
- `presets.py`：固定内置预设及个人预设存储
- `reports.py`：检查快照与两类报告输出
- `checks/`：检查项目录（每个检查一个文件）
- `services.py`：执行编排与结果落盘前缓存
- `operators.py`：检查/清空/导出
- `ui.py`：简版面板

## 设计原则

- 不改旧插件，双轨并行。
- 先重构内核，再逐步迁移旧版 UI 能力。
