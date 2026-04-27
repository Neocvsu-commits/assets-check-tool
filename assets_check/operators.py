



import csv
import json
import os

import bpy
from bpy_extras.io_utils import ExportHelper, ImportHelper

from .services import run_checks_and_store
from .properties import (
    collect_preset_data,
    default_preset_all_enabled,
    load_presets,
    save_presets,
    sync_preset_collection,
)


class ASSETSCHECKNEXT_OT_RunChecks(bpy.types.Operator):
    bl_idname = "assets_check_next.run_checks"
    bl_label = "开始检查"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        mesh_count, row_count = run_checks_and_store(context.scene, context)
        if mesh_count == 0:
            self.report({"WARNING"}, "未选中任何 MESH 对象")
            return {"CANCELLED"}
        self.report({"INFO"}, f"检查完成：{mesh_count} 个对象，{row_count} 条结果")
        return {"FINISHED"}


class ASSETSCHECKNEXT_OT_SelectAllChecked(bpy.types.Operator):
    bl_idname = "assets_check_next.select_all_checked"
    bl_label = "全选"
    bl_description = "选中本次检查涉及的所有对象"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        props = context.scene.assets_check_next_props
        if not props.results_json:
            self.report({"WARNING"}, "没有检查结果，请先执行检查")
            return {"CANCELLED"}
        data = json.loads(props.results_json)
        rows = data.get("rows", [])
        targets = sorted({r.get("object_name", "") for r in rows if r.get("object_name", "")})
        if not targets:
            self.report({"WARNING"}, "没有可选中的检查对象")
            return {"CANCELLED"}

        bpy.ops.object.select_all(action="DESELECT")
        active = None
        for name in targets:
            obj = bpy.data.objects.get(name)
            if obj:
                obj.select_set(True)
                if active is None:
                    active = obj
        if active:
            context.view_layer.objects.active = active
        self.report({"INFO"}, f"已选中 {len(targets)} 个检查对象")
        return {"FINISHED"}


class ASSETSCHECKNEXT_OT_SortMatrix(bpy.types.Operator):
    bl_idname = "assets_check_next.sort_matrix"
    bl_label = "矩阵排序"
    bl_description = "切换矩阵排序"
    bl_options = {"REGISTER", "UNDO"}

    sort_col: bpy.props.IntProperty(name="Sort Col", default=0, min=0)

    def execute(self, context):
        ui_state = context.scene.ac_ui_state
        if ui_state.sort_col == self.sort_col:
            ui_state.sort_reverse = not ui_state.sort_reverse
        else:
            ui_state.sort_col = self.sort_col
            ui_state.sort_reverse = False
        return {"FINISHED"}


class ASSETSCHECKNEXT_OT_OpenQuickFixMenu(bpy.types.Operator):
    bl_idname = "assets_check_next.open_quick_fix_menu"
    bl_label = "打开快速修复菜单"
    bl_description = "打开对应列的快速修复菜单"
    bl_options = {"REGISTER", "UNDO"}

    menu_id: bpy.props.StringProperty(name="Menu ID", default="")

    def execute(self, context):
        if not self.menu_id:
            return {"CANCELLED"}
        try:
            bpy.ops.wm.call_menu(name=self.menu_id)
        except Exception:
            return {"CANCELLED"}
        return {"FINISHED"}


class ASSETSCHECKNEXT_OT_PresetSave(bpy.types.Operator):
    bl_idname = "assets_check_next.preset_save"
    bl_label = "保存预设"
    bl_options = {"REGISTER", "UNDO"}

    preset_name: bpy.props.StringProperty(name="预设名称", default="我的预设")

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=320)

    def draw(self, context):
        self.layout.prop(self, "preset_name")

    def execute(self, context):
        props = context.scene.assets_check_next_props
        addon = context.preferences.addons.get(__package__)
        cfg = addon.preferences if addon else props
        name = self.preset_name.strip() or "未命名预设"
        data = load_presets()
        data[name] = collect_preset_data(cfg)
        save_presets(data)
        sync_preset_collection(props)
        for i, item in enumerate(props.presets_collection):
            if item.name == name:
                props.active_preset_index = i
                break
        self.report({"INFO"}, f"保存预设: {name}")
        return {"FINISHED"}


class ASSETSCHECKNEXT_OT_PresetRemoveActive(bpy.types.Operator):
    bl_idname = "assets_check_next.preset_remove_active"
    bl_label = "删除当前预设"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        props = context.scene.assets_check_next_props
        idx = props.active_preset_index
        if idx < 0 or idx >= len(props.presets_collection):
            self.report({"WARNING"}, "未选中预设")
            return {"CANCELLED"}

        name = props.presets_collection[idx].name
        data = load_presets()
        if name in data:
            del data[name]
        if not data:
            data = {"默认预设": default_preset_all_enabled()}
        save_presets(data)
        sync_preset_collection(props)
        props.active_preset_index = min(idx, max(0, len(props.presets_collection) - 1))
        self.report({"INFO"}, f"已删除预设: {name}")
        return {"FINISHED"}


class ASSETSCHECKNEXT_OT_PresetImport(bpy.types.Operator, ImportHelper):
    bl_idname = "assets_check_next.preset_import"
    bl_label = "导入预设"
    bl_options = {"REGISTER", "UNDO"}

    filename_ext = ".json"
    filter_glob: bpy.props.StringProperty(default="*.json", options={"HIDDEN"})

    def execute(self, context):
        props = context.scene.assets_check_next_props
        try:
            with open(self.filepath, "r", encoding="utf-8") as f:
                imported = json.load(f)
            if not isinstance(imported, dict):
                self.report({"WARNING"}, "预设文件格式不正确")
                return {"CANCELLED"}
        except Exception as e:
            self.report({"WARNING"}, f"导入失败: {e}")
            return {"CANCELLED"}

        data = load_presets()
        data.update(imported)
        save_presets(data)
        sync_preset_collection(props)
        self.report({"INFO"}, "导入预设成功")
        return {"FINISHED"}


class ASSETSCHECKNEXT_OT_PresetExport(bpy.types.Operator, ExportHelper):
    bl_idname = "assets_check_next.preset_export"
    bl_label = "导出预设"
    bl_options = {"REGISTER", "UNDO"}

    filename_ext = ".json"
    filter_glob: bpy.props.StringProperty(default="*.json", options={"HIDDEN"})

    def execute(self, context):
        props = context.scene.assets_check_next_props
        data = load_presets()
        export_data = {}
        for item in props.presets_collection:
            if item.export_enabled and item.name in data:
                export_data[item.name] = data[item.name]
        if not export_data:
            self.report({"WARNING"}, "未选择任何需要导出的预设")
            return {"CANCELLED"}
        try:
            with open(self.filepath, "w", encoding="utf-8") as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.report({"WARNING"}, f"导出失败: {e}")
            return {"CANCELLED"}
        self.report({"INFO"}, f"导出预设成功: {len(export_data)} 个")
        return {"FINISHED"}


class ASSETSCHECKNEXT_OT_PresetExportDialog(bpy.types.Operator):
    bl_idname = "assets_check_next.preset_export_dialog"
    bl_label = "选择要导出的预设"
    bl_options = {"REGISTER", "UNDO"}

    def invoke(self, context, event):
        props = context.scene.assets_check_next_props
        sync_preset_collection(props)
        return context.window_manager.invoke_props_dialog(self, width=320)

    def draw(self, context):
        layout = self.layout
        props = context.scene.assets_check_next_props
        layout.label(text="勾选需要导出的预设:")
        box = layout.box()
        for item in props.presets_collection:
            box.prop(item, "export_enabled", text=item.name)

    def execute(self, context):
        bpy.ops.assets_check_next.preset_export("INVOKE_DEFAULT")
        return {"FINISHED"}


class ASSETSCHECKNEXT_OT_HeaderTooltip(bpy.types.Operator):
    bl_idname = "assets_check_next.header_tooltip"
    bl_label = ""
    bl_description = ""
    col_name: bpy.props.StringProperty()

    @classmethod
    def description(cls, context, properties):
        tt_dict = {
            "名称": "物体的名称",
            "面数": "物体的三角面总数量",
            "空材-质槽": "检测：是否存在没有赋予材质的空材质槽",
            "贴图-丢失": "检测：材质节点中引用的贴图文件是否在本地丢失",
            "UV-越界": "检测：UV是否超出了标准(0,1)区间（此项不适用于UDIM流程）",
            "UV-重叠": "检测：UV岛屿之间是否存在相互重叠",
            "UV-数": "信息：显示当前模型包含的UV通道数量（此项按黄色信息提示展示）",
            "顶点-色数": "检测：模型是否包含顶点颜色层(Color Attributes)",
            "N多-边面": "检测：是否存在由5条或更多边组成的多边形面",
            "非流-形边": "检测：是否存在破洞、游离边、或超过两个面共享的非流形几何",
            "游离-点边": "检测：是否存在没有连接到面的孤立顶点或边",
            "重叠-顶点": "检测：是否存在空间位置极度接近但未合并的重叠顶点",
            "极点-星点": "检测：是否存在汇聚了超过6条边的顶点（普通四转三网格通常为6边。圆柱体的扇形封口极点通常超过30边）",
            "法线-方向": "检测：是否存在面法线朝向网格内部的情况",
            "不平-整面": "检测：是否存在严重凹陷、折叠变形的非平面多边形",
            "零边-检查": "检测：是否存在长度极短、面积近乎为零的废弃几何面/边",
            "交叉-边面": "检测：网格自身面与面之间是否存在相互穿插（此项在大网格上计算极慢！）",
            "应用-缩放": "检测：物体的缩放比例(Scale)是否已经应用归为(1,1,1)",
            "变换-归零": "检测：物体的世界坐标系位置(Location)及旋转(Rotation)是否都已经归零",
            "轴心-位置": "【轴心位置检查】：1 检查物体轴心(原点)是否位于模型底部正中心。 2 检查物体坐标是否位于世界原点(0,0,0)",
            "修改-器": "检测：物体是否仍携带有未应用(Apply)的修改器堆栈",
            "动画-检查": "检测：物体是否携带有动画时间轴的关键帧数据",
            "顶点-权重": "检测：静态网格体是否错误绑定了多余的顶点组(Vertex Groups)",
            "碰撞-检查": "检测：场景中是否存在与该物体绑定的UCX/UBX等UE专属简易碰撞体，且面数是否超标(>64面)",
            "命名-规范": "检测：物体需以SM_开头，材质需以M_开头，贴图需以T_开头，且仅包含英文字母、数字和下划线",
        }
        return tt_dict.get(properties.col_name, properties.col_name)

    def execute(self, context):
        return {"FINISHED"}


class ASSETSCHECKNEXT_OT_QuickFixStub(bpy.types.Operator):
    bl_idname = "assets_check_next.quick_fix_stub"
    bl_label = "功能待迁移"
    bl_description = "旧版功能待迁移到结构化版本"
    bl_options = {"REGISTER", "UNDO"}

    message: bpy.props.StringProperty(name="提示", default="该功能正在迁移中")

    def execute(self, context):
        self.report({"INFO"}, self.message or "该功能正在迁移中")
        return {"FINISHED"}


class ASSETSCHECKNEXT_OT_QuickFixAction(bpy.types.Operator):
    bl_idname = "assets_check_next.quick_fix_action"
    bl_label = "快速修复"
    bl_options = {"REGISTER", "UNDO"}

    action: bpy.props.EnumProperty(
        name="Action",
        items=[
            ("REMOVE_EMPTY_MATERIAL_SLOTS", "清理空材质槽", ""),
            ("DELETE_LOOSE_GEOMETRY", "删除游离点边", ""),
            ("MERGE_DOUBLES", "合并重叠顶点", ""),
            ("AUTOFILL_NAMING_PREFIX", "缺失前缀一键补全", ""),
        ],
        default="REMOVE_EMPTY_MATERIAL_SLOTS",
    )

    def execute(self, context):
        mesh_objects = [obj for obj in context.selected_objects if obj.type == "MESH"]
        if not mesh_objects:
            self.report({"WARNING"}, "未选中任何 MESH 对象")
            return {"CANCELLED"}

        prev_active = context.view_layer.objects.active
        prev_selected = list(context.selected_objects)
        prev_mode = context.mode
        processed = 0

        try:
            if context.mode != "OBJECT":
                bpy.ops.object.mode_set(mode="OBJECT")
            for obj in mesh_objects:
                try:
                    bpy.ops.object.select_all(action="DESELECT")
                    obj.select_set(True)
                    context.view_layer.objects.active = obj
                    if self.action == "REMOVE_EMPTY_MATERIAL_SLOTS":
                        bpy.ops.object.material_slot_remove_unused()
                    elif self.action == "DELETE_LOOSE_GEOMETRY":
                        bpy.ops.object.mode_set(mode="EDIT")
                        bpy.ops.mesh.select_all(action="SELECT")
                        bpy.ops.mesh.delete_loose(use_verts=True, use_edges=True, use_faces=False)
                        bpy.ops.object.mode_set(mode="OBJECT")
                    elif self.action == "MERGE_DOUBLES":
                        bpy.ops.object.mode_set(mode="EDIT")
                        bpy.ops.mesh.select_all(action="SELECT")
                        bpy.ops.mesh.remove_doubles(threshold=0.0001)
                        bpy.ops.object.mode_set(mode="OBJECT")
                    elif self.action == "AUTOFILL_NAMING_PREFIX":
                        if not obj.name.startswith("SM_"):
                            obj.name = f"SM_{obj.name}"
                        for slot in obj.material_slots:
                            mat = slot.material
                            if mat and not mat.name.startswith("M_"):
                                mat.name = f"M_{mat.name}"
                            if not mat or not mat.use_nodes or not mat.node_tree:
                                continue
                            for node in mat.node_tree.nodes:
                                if node.type != "TEX_IMAGE":
                                    continue
                                img = node.image
                                if img and not img.name.startswith("T_"):
                                    img.name = f"T_{img.name}"
                    processed += 1
                except Exception:
                    continue
        finally:
            try:
                bpy.ops.object.select_all(action="DESELECT")
                for o in prev_selected:
                    if o and o.name in bpy.data.objects:
                        o.select_set(True)
                if prev_active and prev_active.name in bpy.data.objects:
                    context.view_layer.objects.active = prev_active
                if prev_mode == "EDIT_MESH":
                    bpy.ops.object.mode_set(mode="EDIT")
                elif prev_mode == "OBJECT":
                    bpy.ops.object.mode_set(mode="OBJECT")
            except Exception:
                pass

        self.report({"INFO"}, f"快速修复完成：处理 {processed} 个对象")
        return {"FINISHED"}


class ASSETSCHECKNEXT_MT_QF_EmptyMaterial(bpy.types.Menu):
    bl_idname = "ASSETSCHECKNEXT_MT_QF_EmptyMaterial"
    bl_label = "空材质槽修复"

    def draw(self, context):
        layout = self.layout
        op = layout.operator("assets_check_next.quick_fix_action", text="清理空材质槽")
        op.action = "REMOVE_EMPTY_MATERIAL_SLOTS"
        layout.operator("assets_check_next.merge_duplicate_materials", text="合并重复材质槽")


class ASSETSCHECKNEXT_MT_QF_MissingTextures(bpy.types.Menu):
    bl_idname = "ASSETSCHECKNEXT_MT_QF_MissingTextures"
    bl_label = "贴图丢失处理"

    def draw(self, context):
        self.layout.label(text="请在材质节点中检查丢失贴图路径", icon="INFO")


class ASSETSCHECKNEXT_MT_QF_UVBounds(bpy.types.Menu):
    bl_idname = "ASSETSCHECKNEXT_MT_QF_UVBounds"
    bl_label = "UV越界处理"

    def draw(self, context):
        self.layout.operator("assets_check_next.locate_uv_oob", text="定位越界UV")


class ASSETSCHECKNEXT_MT_QF_UVOverlap(bpy.types.Menu):
    bl_idname = "ASSETSCHECKNEXT_MT_QF_UVOverlap"
    bl_label = "UV重叠处理"

    def draw(self, context):
        self.layout.operator("assets_check_next.locate_uv_overlap", text="定位重叠UV")


class ASSETSCHECKNEXT_MT_QF_Ngon(bpy.types.Menu):
    bl_idname = "ASSETSCHECKNEXT_MT_QF_Ngon"
    bl_label = "N多边面处理"

    def draw(self, context):
        self.layout.operator("assets_check_next.triangulate_ngon", text="纯三角化N-gon")


class ASSETSCHECKNEXT_MT_QF_NonManifold(bpy.types.Menu):
    bl_idname = "ASSETSCHECKNEXT_MT_QF_NonManifold"
    bl_label = "非流形边处理"

    def draw(self, context):
        self.layout.operator("assets_check_next.fill_holes", text="自动填洞")
        self.layout.operator("assets_check_next.separate_nonmanifold", text="分离非流形几何")


class ASSETSCHECKNEXT_MT_QF_LooseGeometry(bpy.types.Menu):
    bl_idname = "ASSETSCHECKNEXT_MT_QF_LooseGeometry"
    bl_label = "游离点边处理"

    def draw(self, context):
        self.layout.operator("assets_check_next.locate_loose", text="定位游离几何")
        self.layout.operator("assets_check_next.delete_loose", text="删除游离点边")


class ASSETSCHECKNEXT_MT_QF_DoubledVertices(bpy.types.Menu):
    bl_idname = "ASSETSCHECKNEXT_MT_QF_DoubledVertices"
    bl_label = "重叠顶点处理"

    def draw(self, context):
        self.layout.operator("assets_check_next.locate_doubles", text="定位重叠顶点")
        self.layout.operator("assets_check_next.merge_doubles", text="合并重叠顶点")


class ASSETSCHECKNEXT_MT_QF_NamingPrefix(bpy.types.Menu):
    bl_idname = "ASSETSCHECKNEXT_MT_QF_NamingPrefix"
    bl_label = "命名规范处理"

    def draw(self, context):
        op = self.layout.operator("assets_check_next.quick_fix_action", text="缺失前缀一键补全")
        op.action = "AUTOFILL_NAMING_PREFIX"

class ASSETSCHECKNEXT_OT_ClearResults(bpy.types.Operator):
    bl_idname = "assets_check_next.clear_results"
    bl_label = "清空结果"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        scene = context.scene
        scene.assets_check_next_results.clear()
        props = scene.assets_check_next_props
        props.total_items = 0
        props.checked_object_count = 0
        props.pass_count = 0
        props.warn_count = 0
        props.fail_count = 0
        props.results_json = ""
        self.report({"INFO"}, "已清空检查结果")
        return {"FINISHED"}


class ASSETSCHECKNEXT_OT_AutoFixBasic(bpy.types.Operator):
    bl_idname = "assets_check_next.auto_fix_basic"
    bl_label = "一键修复"
    bl_description = "修复无争议项（空材质槽、游离几何、合并重叠顶点、应用Transform、应用修改器、清除顶点组），完成后自动重新检查"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        mesh_objects = [obj for obj in context.selected_objects if obj.type == "MESH"]
        if not mesh_objects:
            self.report({"WARNING"}, "未选中任何 MESH 对象")
            return {"CANCELLED"}

        fixed_mat = 0
        fixed_transform = 0
        fixed_loose = 0
        fixed_doubles = 0
        fixed_modifiers = 0
        fixed_vgroups = 0

        prev_active = context.view_layer.objects.active
        prev_selected = list(context.selected_objects)
        prev_mode = context.mode

        try:
            if context.mode != "OBJECT":
                bpy.ops.object.mode_set(mode="OBJECT")

            for obj in mesh_objects:
                try:
                    bpy.ops.object.select_all(action="DESELECT")
                    obj.select_set(True)
                    context.view_layer.objects.active = obj

                    before = len(obj.material_slots)
                    bpy.ops.object.material_slot_remove_unused()
                    after = len(obj.material_slots)
                    if after < before:
                        fixed_mat += (before - after)

                    bpy.ops.object.mode_set(mode="EDIT")
                    bpy.ops.mesh.select_all(action="SELECT")
                    bpy.ops.mesh.delete_loose(use_verts=True, use_edges=True, use_faces=False)
                    bpy.ops.mesh.remove_doubles(threshold=0.0001)
                    bpy.ops.object.mode_set(mode="OBJECT")
                    fixed_loose += 1
                    fixed_doubles += 1

                    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
                    fixed_transform += 1

                    for mod in list(obj.modifiers):
                        try:
                            bpy.ops.object.modifier_apply(modifier=mod.name)
                            fixed_modifiers += 1
                        except Exception:
                            pass

                    if not any(m.type == "ARMATURE" for m in obj.modifiers):
                        if len(obj.vertex_groups) > 0:
                            obj.vertex_groups.clear()
                            fixed_vgroups += 1
                except Exception:
                    continue
                finally:
                    try:
                        if context.mode != "OBJECT":
                            bpy.ops.object.mode_set(mode="OBJECT")
                    except Exception:
                        pass

            run_checks_and_store(context.scene, context)
        finally:
            try:
                bpy.ops.object.select_all(action="DESELECT")
                for o in prev_selected:
                    if o and o.name in bpy.data.objects:
                        o.select_set(True)
                if prev_active and prev_active.name in bpy.data.objects:
                    context.view_layer.objects.active = prev_active
                if prev_mode == "EDIT_MESH":
                    bpy.ops.object.mode_set(mode="EDIT")
                elif prev_mode == "OBJECT":
                    bpy.ops.object.mode_set(mode="OBJECT")
            except Exception:
                pass

        parts = [
            f"空材质槽 {fixed_mat}",
            f"游离几何 {fixed_loose}",
            f"重叠顶点 {fixed_doubles}",
            f"Transform {fixed_transform}",
            f"修改器 {fixed_modifiers}",
            f"顶点组 {fixed_vgroups}",
        ]
        self.report({"INFO"}, f"一键修复完成：{'，'.join(parts)}")
        return {"FINISHED"}


class ASSETSCHECKNEXT_OT_SelectResultObject(bpy.types.Operator):
    bl_idname = "assets_check_next.select_result_object"
    bl_label = "选中对象"
    bl_description = "在场景中定位并选中该对象"
    bl_options = {"REGISTER", "UNDO"}

    object_name: bpy.props.StringProperty(name="Object Name", default="")

    def execute(self, context):
        obj = bpy.data.objects.get(self.object_name)
        if not obj:
            self.report({"WARNING"}, f"对象不存在: {self.object_name}")
            return {"CANCELLED"}
        bpy.ops.object.select_all(action="DESELECT")
        obj.select_set(True)
        context.view_layer.objects.active = obj
        return {"FINISHED"}


class ASSETSCHECKNEXT_OT_ExportReport(bpy.types.Operator, ExportHelper):
    bl_idname = "assets_check_next.export_report"
    bl_label = "导出报告 (CSV、JSON)"
    filename_ext = ".csv"
    filter_glob: bpy.props.StringProperty(default="*.csv", options={"HIDDEN"})

    def execute(self, context):
        props = context.scene.assets_check_next_props
        if not props.results_json:
            self.report({"WARNING"}, "没有可导出的检查结果，请先执行检查")
            return {"CANCELLED"}

        data = json.loads(props.results_json)
        rows = data.get("rows", [])
        if not rows:
            self.report({"WARNING"}, "结果为空")
            return {"CANCELLED"}

        # 与 CSV 列顺序、字段一一对应（含 display_value，与界面矩阵「数值」列一致）
        export_columns = ["Object", "Check", "Status", "Message", "DisplayValue"]
        norm_rows = [
            {
                "object_name": r.get("object_name", ""),
                "check_id": r.get("check_id", ""),
                "status": r.get("status", ""),
                "message": r.get("message", ""),
                "display_value": r.get("display_value", ""),
            }
            for r in rows
        ]

        with open(self.filepath, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(export_columns)
            for r in norm_rows:
                writer.writerow(
                    [
                        r["object_name"],
                        r["check_id"],
                        r["status"],
                        r["message"],
                        r["display_value"],
                    ]
                )

        json_path = os.path.splitext(self.filepath)[0] + ".json"
        with open(json_path, "w", encoding="utf-8") as jf:
            json.dump(
                {"export_columns": export_columns, "rows": norm_rows},
                jf,
                ensure_ascii=False,
                indent=2,
            )

        self.report({"INFO"}, f"导出完成：{self.filepath} / {json_path}")
        return {"FINISHED"}


class ASSETSCHECKNEXT_OT_OpenPopup(bpy.types.Operator):
    bl_idname = "assets_check_next.open_popup"
    bl_label = "资产审查助手"
    bl_description = "打开资产审查弹窗"
    bl_options = {"REGISTER", "UNDO"}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=1200)

    def execute(self, context):
        return {"FINISHED"}

    def draw(self, context):
        from .ui import draw_assets_check_next_content

        draw_assets_check_next_content(self.layout, context)


class ASSETSCHECKNEXT_OT_SelectAllMeshes(bpy.types.Operator):
    bl_idname = "assets_check_next.select_all_meshes"
    bl_label = "全选MESH"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        bpy.ops.object.select_all(action="DESELECT")
        count = 0
        for obj in context.scene.objects:
            if obj.type == "MESH":
                obj.select_set(True)
                count += 1
        self.report({"INFO"}, f"已选中 {count} 个 MESH")
        return {"FINISHED"}


class ASSETSCHECKNEXT_OT_SelectByResult(bpy.types.Operator):
    bl_idname = "assets_check_next.select_by_result"
    bl_label = "按结果选择对象"
    bl_options = {"REGISTER", "UNDO"}

    mode: bpy.props.EnumProperty(
        name="模式",
        items=[
            ("FAIL", "仅FAIL", "选择至少有一项FAIL的对象"),
            ("WARN_FAIL", "WARN/FAIL", "选择至少有一项WARN或FAIL的对象"),
        ],
        default="FAIL",
    )

    def execute(self, context):
        props = context.scene.assets_check_next_props
        if not props.results_json:
            self.report({"WARNING"}, "没有检查结果，请先执行检查")
            return {"CANCELLED"}

        data = json.loads(props.results_json)
        rows = data.get("rows", [])
        targets = set()
        for row in rows:
            status = row.get("status", "")
            obj_name = row.get("object_name", "")
            if self.mode == "FAIL" and status == "FAIL":
                targets.add(obj_name)
            if self.mode == "WARN_FAIL" and status in {"WARN", "FAIL"}:
                targets.add(obj_name)

        bpy.ops.object.select_all(action="DESELECT")
        for name in targets:
            obj = bpy.data.objects.get(name)
            if obj:
                obj.select_set(True)

        self.report({"INFO"}, f"已按结果选中 {len(targets)} 个对象")
        return {"FINISHED"}


# ============================================================
# 快速修复 Operator（从 v1 完整迁移）
# ============================================================

class ASSETSCHECKNEXT_OT_MergeDuplicateMaterials(bpy.types.Operator):
    bl_idname = "assets_check_next.merge_duplicate_materials"
    bl_label = "合并重复材质槽"
    bl_description = "合并引用同一材质的重复材质槽"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return context.selected_objects and context.mode == "OBJECT"

    def execute(self, context):
        merged_count = 0
        for obj in context.selected_objects:
            if obj.type != "MESH":
                continue
            mat_map = {}
            for i, slot in enumerate(obj.material_slots):
                if slot.material is None:
                    continue
                mat_name = slot.material.name
                if mat_name not in mat_map:
                    mat_map[mat_name] = i
                else:
                    target_idx = mat_map[mat_name]
                    for poly in obj.data.polygons:
                        if poly.material_index == i:
                            poly.material_index = target_idx
                    merged_count += 1
            for i in range(len(obj.material_slots) - 1, -1, -1):
                mat = obj.material_slots[i].material
                if mat and i != mat_map.get(mat.name, i):
                    obj.active_material_index = i
                    bpy.ops.object.material_slot_remove({"object": obj})
        self.report({"INFO"}, f"合并了 {merged_count} 个重复材质槽")
        return {"FINISHED"}


class ASSETSCHECKNEXT_OT_LocateUVOutOfBounds(bpy.types.Operator):
    bl_idname = "assets_check_next.locate_uv_oob"
    bl_label = "定位越界UV"
    bl_description = "进入编辑模式选中超出0-1范围的UV"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return context.active_object and context.active_object.type == "MESH"

    def execute(self, context):
        obj = context.active_object
        bpy.ops.object.mode_set(mode="EDIT", toggle=False)
        bpy.ops.mesh.select_all(action="DESELECT")
        bpy.ops.object.mode_set(mode="OBJECT", toggle=False)
        mesh = obj.data
        if not mesh.uv_layers:
            self.report({"WARNING"}, "物体没有UV层")
            return {"CANCELLED"}
        uv_layer = mesh.uv_layers.active.data
        selected_count = 0
        for poly in mesh.polygons:
            oob = False
            for li in poly.loop_indices:
                uv = uv_layer[li].uv
                if uv.x < 0 or uv.y < 0 or uv.x > 1 or uv.y > 1:
                    oob = True
                    break
            if oob:
                poly.select = True
                selected_count += 1
        bpy.ops.object.mode_set(mode="EDIT", toggle=False)
        self.report({"INFO"}, f"定位到 {selected_count} 个越界面")
        return {"FINISHED"}


class ASSETSCHECKNEXT_OT_LocateUVOverlap(bpy.types.Operator):
    bl_idname = "assets_check_next.locate_uv_overlap"
    bl_label = "定位重叠UV"
    bl_description = "进入编辑模式高亮重叠的UV岛"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return context.active_object and context.active_object.type == "MESH"

    def execute(self, context):
        obj = context.active_object
        bpy.context.view_layer.objects.active = obj
        bpy.context.scene.tool_settings.use_uv_select_sync = False
        mat_slots = len(obj.material_slots)
        if mat_slots > 1:
            overlapping_loops = set()
            for m_idx in range(mat_slots):
                bpy.ops.object.mode_set(mode="OBJECT", toggle=False)
                obj.active_material_index = m_idx
                bpy.ops.object.mode_set(mode="EDIT", toggle=False)
                bpy.ops.mesh.select_all(action="DESELECT")
                bpy.ops.object.material_slot_select()
                bpy.ops.uv.select_overlap(extend=False)
                bpy.ops.object.mode_set(mode="OBJECT", toggle=False)
                for i, loop in enumerate(obj.data.uv_layers.active.data):
                    if loop.select:
                        overlapping_loops.add(i)
            bpy.ops.object.mode_set(mode="EDIT", toggle=False)
            bpy.ops.mesh.select_all(action="SELECT")
            bpy.ops.uv.select_all(action="DESELECT")
            bpy.ops.object.mode_set(mode="OBJECT", toggle=False)
            for idx in overlapping_loops:
                obj.data.uv_layers.active.data[idx].select = True
            bpy.ops.object.mode_set(mode="EDIT", toggle=False)
        else:
            bpy.ops.object.mode_set(mode="EDIT", toggle=False)
            bpy.ops.mesh.select_all(action="SELECT")
            bpy.ops.uv.select_overlap(extend=False)
        self.report({"INFO"}, "已定位重叠UV")
        return {"FINISHED"}


class ASSETSCHECKNEXT_OT_RenameVertexColorUE(bpy.types.Operator):
    bl_idname = "assets_check_next.rename_vc_ue"
    bl_label = "UE标准重命名"
    bl_description = "按UE规范重命名顶点色通道"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return context.selected_objects

    def execute(self, context):
        ue_names = ["Color", "AO", "VertexColor2", "VertexColor3"]
        for obj in context.selected_objects:
            if obj.type != "MESH":
                continue
            for i, attr in enumerate(obj.data.color_attributes):
                if i < len(ue_names):
                    attr.name = ue_names[i]
                else:
                    attr.name = f"VertexColor{i}"
        self.report({"INFO"}, "UE标准顶点色重命名完成")
        return {"FINISHED"}


class ASSETSCHECKNEXT_OT_TriangulateNgon(bpy.types.Operator):
    bl_idname = "assets_check_next.triangulate_ngon"
    bl_label = "纯三角化N-gon"
    bl_description = "仅三角化所有N-gon面"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return context.active_object and context.active_object.type == "MESH"

    def execute(self, context):
        bpy.ops.object.mode_set(mode="EDIT", toggle=False)
        bpy.ops.mesh.select_all(action="DESELECT")
        bpy.ops.mesh.select_face_by_sides(number=4, type="GREATER", extend=False)
        bpy.ops.mesh.quads_convert_to_tris()
        bpy.ops.object.mode_set(mode="OBJECT", toggle=False)
        self.report({"INFO"}, "N-gon三角化完成")
        return {"FINISHED"}


class ASSETSCHECKNEXT_OT_FillHoles(bpy.types.Operator):
    bl_idname = "assets_check_next.fill_holes"
    bl_label = "自动填洞"
    bl_description = "对非流形开放边界执行填充"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return context.active_object and context.active_object.type == "MESH"

    def execute(self, context):
        bpy.ops.object.mode_set(mode="EDIT", toggle=False)
        bpy.ops.mesh.select_all(action="DESELECT")
        bpy.ops.mesh.select_non_manifold(extend=False, use_wire=False, use_boundary=True, use_multi_face=False, use_non_contiguous=False, use_verts=False)
        bpy.ops.mesh.fill()
        bpy.ops.object.mode_set(mode="OBJECT", toggle=False)
        self.report({"INFO"}, "自动填洞完成")
        return {"FINISHED"}


class ASSETSCHECKNEXT_OT_SeparateNonManifold(bpy.types.Operator):
    bl_idname = "assets_check_next.separate_nonmanifold"
    bl_label = "分离非流形几何"
    bl_description = "将非流形部分分离为独立物体"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return context.active_object and context.active_object.type == "MESH"

    def execute(self, context):
        bpy.ops.object.mode_set(mode="EDIT", toggle=False)
        bpy.ops.mesh.select_all(action="DESELECT")
        bpy.ops.mesh.select_non_manifold(extend=False, use_wire=True, use_boundary=True, use_multi_face=True, use_non_contiguous=True, use_verts=True)
        try:
            bpy.ops.mesh.separate(type="SELECTED")
            self.report({"INFO"}, "非流形几何已分离")
        except Exception:
            self.report({"WARNING"}, "没有可分离的非流形几何")
        bpy.ops.object.mode_set(mode="OBJECT", toggle=False)
        return {"FINISHED"}


class ASSETSCHECKNEXT_OT_LocateLoose(bpy.types.Operator):
    bl_idname = "assets_check_next.locate_loose"
    bl_label = "定位游离几何"
    bl_description = "进入编辑模式选中游离点和边"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return context.active_object and context.active_object.type == "MESH"

    def execute(self, context):
        bpy.ops.object.mode_set(mode="EDIT", toggle=False)
        bpy.ops.mesh.select_all(action="DESELECT")
        bpy.ops.mesh.select_loose()
        self.report({"INFO"}, "已定位游离几何")
        return {"FINISHED"}


class ASSETSCHECKNEXT_OT_DeleteLoose(bpy.types.Operator):
    bl_idname = "assets_check_next.delete_loose"
    bl_label = "删除游离点边"
    bl_description = "自动清除所有游离顶点和边"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return context.selected_objects

    def execute(self, context):
        deleted_count = 0
        for obj in context.selected_objects:
            if obj.type != "MESH":
                continue
            bpy.context.view_layer.objects.active = obj
            bpy.ops.object.mode_set(mode="EDIT", toggle=False)
            bpy.ops.mesh.select_all(action="DESELECT")
            bpy.ops.mesh.select_loose()
            bpy.ops.mesh.delete(type="VERT")
            bpy.ops.object.mode_set(mode="OBJECT", toggle=False)
            deleted_count += 1
        self.report({"INFO"}, f"已清除 {deleted_count} 个物体的游离几何")
        return {"FINISHED"}


class ASSETSCHECKNEXT_OT_MergeDoubles(bpy.types.Operator):
    bl_idname = "assets_check_next.merge_doubles"
    bl_label = "合并重叠顶点"
    bl_description = "按距离合并重叠顶点 (阈值 0.0001)"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return context.selected_objects

    def execute(self, context):
        for obj in context.selected_objects:
            if obj.type != "MESH":
                continue
            bpy.context.view_layer.objects.active = obj
            bpy.ops.object.mode_set(mode="EDIT", toggle=False)
            bpy.ops.mesh.select_all(action="SELECT")
            bpy.ops.mesh.remove_doubles(threshold=0.0001)
            bpy.ops.object.mode_set(mode="OBJECT", toggle=False)
        self.report({"INFO"}, "重叠顶点合并完成")
        return {"FINISHED"}


class ASSETSCHECKNEXT_OT_LocateDoubles(bpy.types.Operator):
    bl_idname = "assets_check_next.locate_doubles"
    bl_label = "定位重叠顶点"
    bl_description = "进入编辑模式选中可合并的重叠顶点"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return context.active_object and context.active_object.type == "MESH"

    def execute(self, context):
        import bmesh
        from mathutils import kdtree

        obj = context.active_object
        bm = bmesh.new()
        bm.from_mesh(obj.data)
        size = len(bm.verts)
        kd = kdtree.KDTree(size)
        for i, v in enumerate(bm.verts):
            kd.insert(v.co, i)
        kd.balance()
        doubles_verts = set()
        for i, v in enumerate(bm.verts):
            for (co, index, dist) in kd.find_range(v.co, 0.0001):
                if index != i:
                    doubles_verts.add(i)
                    doubles_verts.add(index)
        bm.free()
        bpy.ops.object.mode_set(mode="EDIT", toggle=False)
        bpy.ops.mesh.select_mode(type="VERT", action="ENABLE")
        bpy.ops.mesh.select_all(action="DESELECT")
        bpy.ops.object.mode_set(mode="OBJECT", toggle=False)
        for vi in doubles_verts:
            obj.data.vertices[vi].select = True
        bpy.ops.object.mode_set(mode="EDIT", toggle=False)
        self.report({"INFO"}, f"定位到 {len(doubles_verts)} 个重叠顶点")
        return {"FINISHED"}


class ASSETSCHECKNEXT_OT_LocatePoles(bpy.types.Operator):
    bl_idname = "assets_check_next.locate_poles"
    bl_label = "定位极点"
    bl_description = "进入编辑模式选中汇聚超过6条边的顶点"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return context.active_object and context.active_object.type == "MESH"

    def execute(self, context):
        import bmesh

        obj = context.active_object
        bm = bmesh.new()
        bm.from_mesh(obj.data)
        pole_indices = [v.index for v in bm.verts if len(v.link_edges) > 6]
        bm.free()
        bpy.ops.object.mode_set(mode="EDIT", toggle=False)
        bpy.ops.mesh.select_mode(type="VERT", action="ENABLE")
        bpy.ops.mesh.select_all(action="DESELECT")
        bpy.ops.object.mode_set(mode="OBJECT", toggle=False)
        for vi in pole_indices:
            obj.data.vertices[vi].select = True
        bpy.ops.object.mode_set(mode="EDIT", toggle=False)
        self.report({"INFO"}, f"定位到 {len(pole_indices)} 个极点")
        return {"FINISHED"}


class ASSETSCHECKNEXT_OT_SelectFlippedNormal(bpy.types.Operator):
    bl_idname = "assets_check_next.select_flipped_normal"
    bl_label = "定位反转法线"
    bl_description = "进入编辑模式选中法线朝内的面"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return context.active_object and context.active_object.type == "MESH"

    def execute(self, context):
        import bmesh

        obj = context.active_object
        bpy.ops.object.mode_set(mode="OBJECT", toggle=False)
        me = obj.data
        if me.has_custom_normals:
            self.report({"INFO"}, "使用自定义法线，跳过检测")
            return {"FINISHED"}
        bm = bmesh.new()
        bm.from_mesh(me)
        bm.faces.ensure_lookup_table()
        original_normals = [f.normal.copy() for f in bm.faces]
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        flipped_indices = []
        for i, f in enumerate(bm.faces):
            if original_normals[i].dot(f.normal) < 0.0:
                flipped_indices.append(i)
        bm.free()
        bpy.ops.object.mode_set(mode="EDIT", toggle=False)
        bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type="FACE", action="ENABLE")
        bpy.ops.mesh.select_all(action="DESELECT")
        bpy.ops.object.mode_set(mode="OBJECT", toggle=False)
        for idx in flipped_indices:
            obj.data.polygons[idx].select = True
        bpy.ops.object.mode_set(mode="EDIT", toggle=False)
        self.report({"INFO"}, f"定位到 {len(flipped_indices)} 个反转法线面")
        return {"FINISHED"}


class ASSETSCHECKNEXT_OT_ApplyScale(bpy.types.Operator):
    bl_idname = "assets_check_next.apply_scale"
    bl_label = "应用缩放"
    bl_description = "对选中物体应用缩放"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return context.selected_objects and context.mode == "OBJECT"

    def execute(self, context):
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        self.report({"INFO"}, "缩放应用完成")
        return {"FINISHED"}


class ASSETSCHECKNEXT_OT_ApplyAllTransforms(bpy.types.Operator):
    bl_idname = "assets_check_next.apply_all_transforms"
    bl_label = "应用全部变换"
    bl_description = "同时应用位置、旋转和缩放"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return context.selected_objects and context.mode == "OBJECT"

    def execute(self, context):
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
        self.report({"INFO"}, "全部变换应用完成")
        return {"FINISHED"}


class ASSETSCHECKNEXT_OT_ZeroTransform(bpy.types.Operator):
    bl_idname = "assets_check_next.zero_transform"
    bl_label = "完全归零Transform"
    bl_description = "将位置归零到世界原点并重置旋转"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return context.selected_objects and context.mode == "OBJECT"

    def execute(self, context):
        for obj in context.selected_objects:
            obj.location = (0.0, 0.0, 0.0)
            obj.rotation_euler = (0.0, 0.0, 0.0)
        self.report({"INFO"}, "Transform归零完成")
        return {"FINISHED"}


class ASSETSCHECKNEXT_OT_ApplyRotationOnly(bpy.types.Operator):
    bl_idname = "assets_check_next.apply_rotation_only"
    bl_label = "仅应用旋转"
    bl_description = "仅应用旋转，保留位置和缩放"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return context.selected_objects and context.mode == "OBJECT"

    def execute(self, context):
        bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)
        self.report({"INFO"}, "旋转应用完成")
        return {"FINISHED"}


class ASSETSCHECKNEXT_OT_OriginToBottom(bpy.types.Operator):
    bl_idname = "assets_check_next.origin_to_bottom"
    bl_label = "原点→底部中心"
    bl_description = "设置原点到包围盒底面中心"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return context.selected_objects and context.mode == "OBJECT"

    def execute(self, context):
        import mathutils

        for obj in context.selected_objects:
            if obj.type != "MESH":
                continue
            bbox = obj.bound_box
            min_x = min(v[0] for v in bbox)
            max_x = max(v[0] for v in bbox)
            min_y = min(v[1] for v in bbox)
            max_y = max(v[1] for v in bbox)
            min_z = min(v[2] for v in bbox)
            bottom_center_local = mathutils.Vector(((min_x + max_x) / 2, (min_y + max_y) / 2, min_z))
            bottom_world = obj.matrix_world @ bottom_center_local
            obj.location = bottom_world
            for v in obj.data.vertices:
                v.co -= bottom_center_local
        self.report({"INFO"}, "原点已设置到底部中心")
        return {"FINISHED"}


class ASSETSCHECKNEXT_OT_OriginToGeometry(bpy.types.Operator):
    bl_idname = "assets_check_next.origin_to_geometry"
    bl_label = "原点→几何中心"
    bl_description = "设置原点到几何体中心"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return context.selected_objects and context.mode == "OBJECT"

    def execute(self, context):
        bpy.ops.object.origin_set(type="ORIGIN_GEOMETRY", center="MEDIAN")
        self.report({"INFO"}, "原点已设置到几何中心")
        return {"FINISHED"}


class ASSETSCHECKNEXT_OT_OriginToWorld(bpy.types.Operator):
    bl_idname = "assets_check_next.origin_to_world"
    bl_label = "原点→世界原点"
    bl_description = "将物体移到世界原点且原点设在底部中心"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return context.selected_objects and context.mode == "OBJECT"

    def execute(self, context):
        import mathutils

        for obj in context.selected_objects:
            if obj.type != "MESH":
                continue
            bbox = obj.bound_box
            min_x = min(v[0] for v in bbox)
            max_x = max(v[0] for v in bbox)
            min_y = min(v[1] for v in bbox)
            max_y = max(v[1] for v in bbox)
            min_z = min(v[2] for v in bbox)
            bottom_center_local = mathutils.Vector(((min_x + max_x) / 2, (min_y + max_y) / 2, min_z))
            for v in obj.data.vertices:
                v.co -= bottom_center_local
            obj.location = (0.0, 0.0, 0.0)
        self.report({"INFO"}, "物体已移至世界原点，原点在底部中心")
        return {"FINISHED"}


class ASSETSCHECKNEXT_OT_ApplyAllModifiers(bpy.types.Operator):
    bl_idname = "assets_check_next.apply_all_modifiers"
    bl_label = "应用全部修改器"
    bl_description = "逐个应用所有修改器"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return context.selected_objects and context.mode == "OBJECT"

    def execute(self, context):
        applied_count = 0
        for obj in context.selected_objects:
            if obj.type != "MESH":
                continue
            bpy.context.view_layer.objects.active = obj
            for mod in list(obj.modifiers):
                try:
                    bpy.ops.object.modifier_apply(modifier=mod.name)
                    applied_count += 1
                except Exception as e:
                    self.report({"WARNING"}, f"无法应用修改器 {mod.name}: {e}")
        self.report({"INFO"}, f"已应用 {applied_count} 个修改器")
        return {"FINISHED"}


class ASSETSCHECKNEXT_OT_ClearVertexGroups(bpy.types.Operator):
    bl_idname = "assets_check_next.clear_vertex_groups"
    bl_label = "清除全部顶点组"
    bl_description = "删除静态网格上的所有顶点组"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return context.selected_objects and context.mode == "OBJECT"

    def execute(self, context):
        cleared_count = 0
        for obj in context.selected_objects:
            if obj.type != "MESH":
                continue
            obj.vertex_groups.clear()
            cleared_count += 1
        self.report({"INFO"}, f"已清除 {cleared_count} 个物体的顶点组")
        return {"FINISHED"}


class ASSETSCHECKNEXT_OT_SelectCollision(bpy.types.Operator):
    bl_idname = "assets_check_next.select_collision"
    bl_label = "选中关联碰撞体"
    bl_description = "选中与当前物体关联的UCX_/UBX_等碰撞体"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return context.active_object and context.mode == "OBJECT"

    def execute(self, context):
        active = context.active_object
        found = 0
        prefixes = ("UCX_", "UBX_", "UCP_", "USP_")
        for scene_obj in context.scene.objects:
            if scene_obj.type == "MESH" and scene_obj.name.startswith(prefixes):
                base_name = scene_obj.name.split("_", 1)[1] if "_" in scene_obj.name else ""
                if base_name and (active.name.startswith(base_name) or base_name.startswith(active.name.replace("SM_", ""))):
                    scene_obj.select_set(True)
                    found += 1
        if found:
            self.report({"INFO"}, f"选中了 {found} 个关联碰撞体")
        else:
            self.report({"WARNING"}, "未找到关联碰撞体")
        return {"FINISHED"}


class ASSETSCHECKNEXT_OT_GenerateConvexCollision(bpy.types.Operator):
    bl_idname = "assets_check_next.generate_convex_collision"
    bl_label = "自动生成凸包碰撞"
    bl_description = "基于当前模型生成Convex Hull碰撞体并命名为UCX_"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return context.active_object and context.active_object.type == "MESH" and context.mode == "OBJECT"

    def execute(self, context):
        import bmesh

        active = context.active_object
        bm = bmesh.new()
        bm.from_mesh(active.data)
        result = bmesh.ops.convex_hull(bm, input=bm.verts)
        interior_geom = result.get("geom_interior", [])
        unused_geom = result.get("geom_unused", [])
        geom_to_delete = set()
        for g in interior_geom + unused_geom:
            if isinstance(g, (bmesh.types.BMVert, bmesh.types.BMEdge, bmesh.types.BMFace)):
                geom_to_delete.add(g)
        if geom_to_delete:
            bmesh.ops.delete(bm, geom=list(geom_to_delete), context="TAGGED")
        collision_mesh = bpy.data.meshes.new(f"UCX_{active.name}_mesh")
        bm.to_mesh(collision_mesh)
        bm.free()
        collision_obj = bpy.data.objects.new(f"UCX_{active.name}", collision_mesh)
        context.collection.objects.link(collision_obj)
        collision_obj.matrix_world = active.matrix_world.copy()
        collision_obj.display_type = "WIRE"
        face_count = len(collision_mesh.polygons)
        self.report({"INFO"}, f"生成碰撞体 UCX_{active.name} (面数: {face_count})")
        return {"FINISHED"}


# ============================================================
# 快速修复菜单（补齐全部列）
# ============================================================

class ASSETSCHECKNEXT_MT_QF_Poles(bpy.types.Menu):
    bl_idname = "ASSETSCHECKNEXT_MT_QF_Poles"
    bl_label = "极点处理"

    def draw(self, context):
        self.layout.operator("assets_check_next.locate_poles", text="定位极点")


class ASSETSCHECKNEXT_MT_QF_NormalDirection(bpy.types.Menu):
    bl_idname = "ASSETSCHECKNEXT_MT_QF_NormalDirection"
    bl_label = "法线处理"

    def draw(self, context):
        self.layout.operator("assets_check_next.select_flipped_normal", text="定位反转法线")


class ASSETSCHECKNEXT_MT_QF_ApplyScale(bpy.types.Menu):
    bl_idname = "ASSETSCHECKNEXT_MT_QF_ApplyScale"
    bl_label = "缩放处理"

    def draw(self, context):
        self.layout.operator("assets_check_next.apply_scale", text="应用缩放")
        self.layout.operator("assets_check_next.apply_all_transforms", text="应用全部变换")


class ASSETSCHECKNEXT_MT_QF_TransformZero(bpy.types.Menu):
    bl_idname = "ASSETSCHECKNEXT_MT_QF_TransformZero"
    bl_label = "变换归零处理"

    def draw(self, context):
        self.layout.operator("assets_check_next.zero_transform", text="完全归零Transform")
        self.layout.operator("assets_check_next.apply_rotation_only", text="仅应用旋转")


class ASSETSCHECKNEXT_MT_QF_PivotPosition(bpy.types.Menu):
    bl_idname = "ASSETSCHECKNEXT_MT_QF_PivotPosition"
    bl_label = "轴心位置处理"

    def draw(self, context):
        self.layout.operator("assets_check_next.origin_to_bottom", text="原点→底部中心")
        self.layout.operator("assets_check_next.origin_to_geometry", text="原点→几何中心")
        self.layout.operator("assets_check_next.origin_to_world", text="原点→世界原点")


class ASSETSCHECKNEXT_MT_QF_Modifier(bpy.types.Menu):
    bl_idname = "ASSETSCHECKNEXT_MT_QF_Modifier"
    bl_label = "修改器处理"

    def draw(self, context):
        self.layout.operator("assets_check_next.apply_all_modifiers", text="应用全部修改器")


class ASSETSCHECKNEXT_MT_QF_VertexWeight(bpy.types.Menu):
    bl_idname = "ASSETSCHECKNEXT_MT_QF_VertexWeight"
    bl_label = "顶点权重处理"

    def draw(self, context):
        self.layout.operator("assets_check_next.clear_vertex_groups", text="清除全部顶点组")


class ASSETSCHECKNEXT_MT_QF_Collision(bpy.types.Menu):
    bl_idname = "ASSETSCHECKNEXT_MT_QF_Collision"
    bl_label = "碰撞处理"

    def draw(self, context):
        self.layout.operator("assets_check_next.select_collision", text="选中关联碰撞体")
        self.layout.operator("assets_check_next.generate_convex_collision", text="自动生成凸包碰撞")


class ASSETSCHECKNEXT_MT_QF_VertexColor(bpy.types.Menu):
    bl_idname = "ASSETSCHECKNEXT_MT_QF_VertexColor"
    bl_label = "顶点色处理"

    def draw(self, context):
        self.layout.operator("assets_check_next.rename_vc_ue", text="UE标准重命名")


class ASSETSCHECKNEXT_OT_LocateNonplanar(bpy.types.Operator):
    bl_idname = "assets_check_next.locate_nonplanar"
    bl_label = "定位不平整面"
    bl_description = "进入编辑模式选中严重凹陷变形的非平面多边形"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return context.active_object and context.active_object.type == "MESH"

    def execute(self, context):
        import bmesh

        obj = context.active_object
        bm = bmesh.new()
        bm.from_mesh(obj.data)
        bm.faces.ensure_lookup_table()
        nonplanar_indices = []
        for f in bm.faces:
            if len(f.verts) < 4:
                continue
            normal = f.normal
            center = f.calc_center_median()
            max_dist = 0.0
            for v in f.verts:
                d = abs((v.co - center).dot(normal))
                if d > max_dist:
                    max_dist = d
            if max_dist > 0.01:
                nonplanar_indices.append(f.index)
        bm.free()
        bpy.ops.object.mode_set(mode="EDIT", toggle=False)
        bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type="FACE", action="ENABLE")
        bpy.ops.mesh.select_all(action="DESELECT")
        bpy.ops.object.mode_set(mode="OBJECT", toggle=False)
        for idx in nonplanar_indices:
            obj.data.polygons[idx].select = True
        bpy.ops.object.mode_set(mode="EDIT", toggle=False)
        self.report({"INFO"}, f"定位到 {len(nonplanar_indices)} 个不平整面")
        return {"FINISHED"}


class ASSETSCHECKNEXT_OT_LocateZeroEdges(bpy.types.Operator):
    bl_idname = "assets_check_next.locate_zero_edges"
    bl_label = "定位零边"
    bl_description = "进入编辑模式选中长度极短的废弃边"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return context.active_object and context.active_object.type == "MESH"

    def execute(self, context):
        import bmesh

        obj = context.active_object
        bm = bmesh.new()
        bm.from_mesh(obj.data)
        zero_vert_indices = set()
        for e in bm.edges:
            if e.calc_length() < 1e-6:
                zero_vert_indices.add(e.verts[0].index)
                zero_vert_indices.add(e.verts[1].index)
        bm.free()
        bpy.ops.object.mode_set(mode="EDIT", toggle=False)
        bpy.ops.mesh.select_mode(type="VERT", action="ENABLE")
        bpy.ops.mesh.select_all(action="DESELECT")
        bpy.ops.object.mode_set(mode="OBJECT", toggle=False)
        for vi in zero_vert_indices:
            obj.data.vertices[vi].select = True
        bpy.ops.object.mode_set(mode="EDIT", toggle=False)
        self.report({"INFO"}, f"定位到 {len(zero_vert_indices)} 个零边相关顶点")
        return {"FINISHED"}


class ASSETSCHECKNEXT_OT_LocateSelfIntersection(bpy.types.Operator):
    bl_idname = "assets_check_next.locate_self_intersection"
    bl_label = "定位交叉面"
    bl_description = "进入编辑模式选中自交叉面（大网格可能较慢）"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return context.active_object and context.active_object.type == "MESH"

    def execute(self, context):
        bpy.ops.object.mode_set(mode="EDIT", toggle=False)
        bpy.ops.mesh.select_all(action="SELECT")
        # Blender 4.x：mode 仅支持 SELECT（自相交）/ SELECT_UNSELECT；SELF 已移除
        bpy.ops.mesh.intersect(
            mode="SELECT",
            separate_mode="NONE",
            threshold=0.0001,
            solver="EXACT",
        )
        self.report({"INFO"}, "已执行自交叉检测，选中区域为交叉相关几何")
        return {"FINISHED"}


class ASSETSCHECKNEXT_MT_QF_NonplanarFaces(bpy.types.Menu):
    bl_idname = "ASSETSCHECKNEXT_MT_QF_NonplanarFaces"
    bl_label = "不平整面处理"

    def draw(self, context):
        self.layout.operator("assets_check_next.locate_nonplanar", text="定位不平整面")


class ASSETSCHECKNEXT_MT_QF_ZeroEdges(bpy.types.Menu):
    bl_idname = "ASSETSCHECKNEXT_MT_QF_ZeroEdges"
    bl_label = "零边处理"

    def draw(self, context):
        self.layout.operator("assets_check_next.locate_zero_edges", text="定位零边")


class ASSETSCHECKNEXT_MT_QF_SelfIntersection(bpy.types.Menu):
    bl_idname = "ASSETSCHECKNEXT_MT_QF_SelfIntersection"
    bl_label = "交叉面处理"

    def draw(self, context):
        self.layout.operator("assets_check_next.locate_self_intersection", text="定位交叉面")
