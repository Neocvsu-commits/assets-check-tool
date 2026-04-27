bl_info = {
    "name": "资产审查助手",
    "author": "Neo",
    "version": (2, 0, 0),
    "blender": (4, 2, 0),
    "location": "3D 视图 > 顶栏「检查」",
    "description": "资产网格与数据检查、快速修复与报告导出（正式版）",
    "category": "3D View",
}

import bpy

if "bpy" in locals():
    import importlib
    if "icon_manager" in locals():
        importlib.reload(icon_manager)
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
    ui.ASSETSCHECKNEXT_UL_PresetList,
)


def _draw_topbar_entry(self, context):
    self.layout.operator("assets_check_next.open_popup", text="检查", icon_value=icon_manager.get_icon_id("presentation.png"))


def register():
    icon_manager.load_icons()
    for cls in CLASSES:
        bpy.utils.register_class(cls)
    bpy.types.Scene.assets_check_next_props = bpy.props.PointerProperty(type=properties.ASSETSCHECKNEXT_Props)
    bpy.types.Scene.assets_check_next_results = bpy.props.CollectionProperty(type=properties.ASSETSCHECKNEXT_ResultItem)
    bpy.types.Scene.ac_ui_state = bpy.props.PointerProperty(type=properties.AssetsCheckUIState)
    try:
        properties.sync_preset_collection(bpy.context.scene.assets_check_next_props)
    except Exception:
        pass
    bpy.types.TOPBAR_MT_editor_menus.append(_draw_topbar_entry)


def unregister():
    global _icons
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
