import json
from datetime import datetime

import bpy

from .checks import run_checks_for_object
from .properties import sync_preferences_to_scene_props
from .reports import model_snapshot
from .presets import collect_preset_data


_AUTO_CHECK_DELAY = 0.3


def schedule_auto_check():
    """切换检查项后去抖延迟执行自动检查：短时间内多次改动合并为一次."""
    try:
        bpy.app.timers.unregister(_auto_check_timer)
    except ValueError:
        pass
    bpy.app.timers.register(_auto_check_timer, first_interval=_AUTO_CHECK_DELAY)


def run_auto_check_now():
    """立即（下一帧）执行自动检查：取消等待中的去抖 timer，预设切换等场景使用."""
    try:
        bpy.app.timers.unregister(_auto_check_timer)
    except ValueError:
        pass
    bpy.app.timers.register(_auto_check_timer, first_interval=0.0)


def _auto_check_timer():
    context = bpy.context
    if context and context.scene and context.selected_objects:
        run_checks_and_store(context.scene, context)
    return None


def run_checks_and_store(scene, context):
    props = scene.assets_check_next_props
    sync_preferences_to_scene_props(context, props)
    results = scene.assets_check_next_results
    results.clear()
    props.results_json = ""

    mesh_objects = [obj for obj in context.selected_objects if obj.type == "MESH"]
    all_rows = []
    pass_count = 0
    warn_count = 0
    fail_count = 0

    models = []

    for obj in mesh_objects:
        obj.update_from_editmode()
        checks = run_checks_for_object(obj, context, props)
        models.append(model_snapshot(obj, scene))
        for row in checks:
            item = results.add()
            item.object_name = obj.name
            item.check_id = row["check_id"]
            item.status = row["status"]
            item.message = row["message"]
            item.display_value = row.get("display_value", "")
            all_rows.append(
                {
                    "object_name": obj.name,
                    "check_id": row["check_id"],
                    "status": row["status"],
                    "message": row["message"],
                    "display_value": row.get("display_value", ""),
                }
            )
            if row["status"] == "PASS":
                pass_count += 1
            elif row["status"] == "WARN":
                warn_count += 1
            elif row["status"] == "FAIL":
                fail_count += 1

    props.total_items = len(all_rows)
    props.checked_object_count = len(mesh_objects)
    props.pass_count = pass_count
    props.warn_count = warn_count
    props.fail_count = fail_count
    props.last_run_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    index = props.active_preset_index
    preset_name = props.presets_collection[index].name if 0 <= index < len(props.presets_collection) else "自定义检查"
    props.results_json = json.dumps({
        "rows": all_rows, "models": models, "checked_at": props.last_run_at,
        "preset_name": preset_name, "check_config": collect_preset_data(props),
    }, ensure_ascii=False)

    return len(mesh_objects), len(all_rows)
