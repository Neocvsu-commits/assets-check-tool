import json
from datetime import datetime

from .checks import run_checks_for_object
from .properties import sync_preferences_to_scene_props


def run_checks_and_store(scene, context):
    props = scene.assets_check_next_props
    sync_preferences_to_scene_props(context, props)
    results = scene.assets_check_next_results
    results.clear()

    mesh_objects = [obj for obj in context.selected_objects if obj.type == "MESH"]
    all_rows = []
    pass_count = 0
    warn_count = 0
    fail_count = 0

    for obj in mesh_objects:
        checks = run_checks_for_object(obj, context, props)
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
    props.results_json = json.dumps({"rows": all_rows}, ensure_ascii=False)

    return len(mesh_objects), len(all_rows)
