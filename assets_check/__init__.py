bl_info = {
    "name": "资产审查助手",
    "author": "Neo",
    "version": (2, 1, 6),
    "blender": (4, 2, 0),
    "location": "3D 视图 > 顶栏「检查」",
    "description": "资产网格与数据检查、快速修复与报告导出（正式版）",
    "category": "3D View",
}

import bpy
import os

if "bpy" in locals():
    import importlib
    if "icon_manager" in locals():
        importlib.reload(icon_manager)
    if "update_checker" in locals():
        importlib.reload(update_checker)
    if "properties" in locals():
        importlib.reload(properties)
    if "checks" in locals():
        importlib.reload(checks)
    if "services" in locals():
        importlib.reload(services)
    if "operators" in locals():
        importlib.reload(operators)
    if "ui" in locals():
        importlib.reload(ui)

from . import icon_manager
from . import update_checker
from . import properties
from . import checks
from . import services
from . import operators
from . import ui


CLASSES = (
    properties.ASSETSCHECKNEXT_AddonPreferences,
    properties.AssetsCheckUIState,
    properties.ASSETSCHECKNEXT_ResultItem,
    properties.ASSETSCHECKNEXT_PresetItem,
    properties.ASSETSCHECKNEXT_Props,
    operators.ASSETSCHECKNEXT_OT_PresetSave,
    operators.ASSETSCHECKNEXT_OT_PresetQuickSave,
    operators.ASSETSCHECKNEXT_OT_PresetResetDefault,
    operators.ASSETSCHECKNEXT_OT_PresetRemoveActive,
    operators.ASSETSCHECKNEXT_OT_PresetImport,
    operators.ASSETSCHECKNEXT_OT_PresetExportDialog,
    operators.ASSETSCHECKNEXT_OT_PresetExport,
    operators.ASSETSCHECKNEXT_OT_HeaderTooltip,
    operators.ASSETSCHECKNEXT_OT_QuickFixStub,
    operators.ASSETSCHECKNEXT_OT_QuickFixAction,
    operators.ASSETSCHECKNEXT_OT_MergeDuplicateMaterials,
    operators.ASSETSCHECKNEXT_OT_LocateUVOutOfBounds,
    operators.ASSETSCHECKNEXT_OT_LocateUVOverlap,
    operators.ASSETSCHECKNEXT_OT_RenameVertexColorUE,
    operators.ASSETSCHECKNEXT_OT_TriangulateNgon,
    operators.ASSETSCHECKNEXT_OT_FillHoles,
    operators.ASSETSCHECKNEXT_OT_SeparateNonManifold,
    operators.ASSETSCHECKNEXT_OT_LocateLoose,
    operators.ASSETSCHECKNEXT_OT_DeleteLoose,
    operators.ASSETSCHECKNEXT_OT_MergeDoubles,
    operators.ASSETSCHECKNEXT_OT_LocateDoubles,
    operators.ASSETSCHECKNEXT_OT_LocatePoles,
    operators.ASSETSCHECKNEXT_OT_SelectFlippedNormal,
    operators.ASSETSCHECKNEXT_OT_ApplyScale,
    operators.ASSETSCHECKNEXT_OT_ApplyAllTransforms,
    operators.ASSETSCHECKNEXT_OT_ZeroTransform,
    operators.ASSETSCHECKNEXT_OT_ApplyRotationOnly,
    operators.ASSETSCHECKNEXT_OT_OriginToBottom,
    operators.ASSETSCHECKNEXT_OT_OriginToGeometry,
    operators.ASSETSCHECKNEXT_OT_OriginToWorld,
    operators.ASSETSCHECKNEXT_OT_ApplyAllModifiers,
    operators.ASSETSCHECKNEXT_OT_ClearVertexGroups,
    operators.ASSETSCHECKNEXT_OT_SelectCollision,
    operators.ASSETSCHECKNEXT_OT_GenerateConvexCollision,
    operators.ASSETSCHECKNEXT_MT_QF_EmptyMaterial,
    operators.ASSETSCHECKNEXT_MT_QF_MissingTextures,
    operators.ASSETSCHECKNEXT_MT_QF_UVBounds,
    operators.ASSETSCHECKNEXT_MT_QF_UVOverlap,
    operators.ASSETSCHECKNEXT_MT_QF_Ngon,
    operators.ASSETSCHECKNEXT_MT_QF_NonManifold,
    operators.ASSETSCHECKNEXT_MT_QF_LooseGeometry,
    operators.ASSETSCHECKNEXT_MT_QF_DoubledVertices,
    operators.ASSETSCHECKNEXT_MT_QF_NamingPrefix,
    operators.ASSETSCHECKNEXT_MT_QF_Poles,
    operators.ASSETSCHECKNEXT_MT_QF_NormalDirection,
    operators.ASSETSCHECKNEXT_MT_QF_ApplyScale,
    operators.ASSETSCHECKNEXT_MT_QF_TransformZero,
    operators.ASSETSCHECKNEXT_MT_QF_PivotPosition,
    operators.ASSETSCHECKNEXT_MT_QF_Modifier,
    operators.ASSETSCHECKNEXT_MT_QF_VertexWeight,
    operators.ASSETSCHECKNEXT_MT_QF_Collision,
    operators.ASSETSCHECKNEXT_MT_QF_VertexColor,
    operators.ASSETSCHECKNEXT_OT_LocateNonplanar,
    operators.ASSETSCHECKNEXT_OT_LocateZeroEdges,
    operators.ASSETSCHECKNEXT_OT_LocateSelfIntersection,
    operators.ASSETSCHECKNEXT_MT_QF_NonplanarFaces,
    operators.ASSETSCHECKNEXT_MT_QF_ZeroEdges,
    operators.ASSETSCHECKNEXT_MT_QF_SelfIntersection,
    operators.ASSETSCHECKNEXT_OT_RunChecks,
    operators.ASSETSCHECKNEXT_OT_SelectAllChecked,
    operators.ASSETSCHECKNEXT_OT_SortMatrix,
    operators.ASSETSCHECKNEXT_OT_OpenQuickFixMenu,
    operators.ASSETSCHECKNEXT_OT_ClearResults,
    operators.ASSETSCHECKNEXT_OT_AutoFixBasic,
    operators.ASSETSCHECKNEXT_OT_SelectResultObject,
    operators.ASSETSCHECKNEXT_OT_ExportReport,
    operators.ASSETSCHECKNEXT_OT_OpenPopup,
    operators.ASSETSCHECKNEXT_OT_SelectAllMeshes,
    operators.ASSETSCHECKNEXT_OT_SelectByResult,
    operators.ASSETSCHECKNEXT_OT_CheckUpdate,
    operators.ASSETSCHECKNEXT_OT_InstallUpdate,
    operators.ASSETSCHECKNEXT_OT_FixObjectDataName,
    operators.ASSETSCHECKNEXT_MT_QF_ObjectDataNameMatch,
    ui.ASSETSCHECKNEXT_UL_PresetList,
)


def _draw_topbar_entry(self, context):
    self.layout.operator("assets_check_next.open_popup", text="检查", icon_value=icon_manager.get_icon_id("presentation.png"))


def register():
    global _register_handlers
    _register_handlers = []
    icon_manager.load_icons()
    for cls in CLASSES:
        bpy.utils.register_class(cls)
    bpy.types.Scene.assets_check_next_props = bpy.props.PointerProperty(type=properties.ASSETSCHECKNEXT_Props)
    bpy.types.Scene.assets_check_next_results = bpy.props.CollectionProperty(type=properties.ASSETSCHECKNEXT_ResultItem)
    bpy.types.Scene.ac_ui_state = bpy.props.PointerProperty(type=properties.AssetsCheckUIState)
    bpy.types.TOPBAR_MT_editor_menus.append(_draw_topbar_entry)

    # 后台检查更新
    try:
        from .update_checker import check_for_updates
        check_for_updates(
            owner="Neocvsu-commits",
            repo="assets-check-tool",
            current_version=bl_info["version"],
            plugin_dir=os.path.dirname(__file__),
        )
    except Exception:
        pass

    # 预设同步：不能在 register() 里直接操作 scene，用 load_post 延迟
    def _delayed_sync_presets(_dummy):
        try:
            props = bpy.context.scene.assets_check_next_props
            properties.sync_preset_collection(props)
        except Exception as e:
            print(f"[AssetsCheck] 延迟预设同步失败: {e}")
        return None
    bpy.app.handlers.load_post.append(_delayed_sync_presets)
    _register_handlers.append(("load_post", _delayed_sync_presets))


def unregister():
    global _icons, _register_handlers
    # 清理 load_post handler
    for handler_type, handler in _register_handlers:
        handler_list = getattr(bpy.app.handlers, handler_type, None)
        if handler_list is not None and handler in handler_list:
            handler_list.remove(handler)
    _register_handlers = []
    try:
        bpy.types.TOPBAR_MT_editor_menus.remove(_draw_topbar_entry)
    except Exception:
        pass
    if hasattr(bpy.types.Scene, "assets_check_next_results"):
        del bpy.types.Scene.assets_check_next_results
    if hasattr(bpy.types.Scene, "ac_ui_state"):
        del bpy.types.Scene.ac_ui_state
    if hasattr(bpy.types.Scene, "assets_check_next_props"):
        del bpy.types.Scene.assets_check_next_props
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)
    icon_manager.unload_icons()


if __name__ == "__main__":
    register()
