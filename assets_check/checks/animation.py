def run(obj, context):
    ad = obj.animation_data
    has_anim = bool(ad and (ad.action or ad.nla_tracks))
    if has_anim:
        return {"check_id": "animation", "status": "WARN", "message": "检测到动画数据"}
    return {"check_id": "animation", "status": "PASS", "message": "无动画数据"}
