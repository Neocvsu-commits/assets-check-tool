import os
import bpy

_icons = None


def load_icons():
    global _icons
    _icons = bpy.utils.previews.new()
    icons_dir = os.path.join(os.path.dirname(__file__), "icons")
    for name in ("timer-outline.png", "search-outline.png", "location-pin.png",
                 "caret-up-outline.png", "caret-down-outline.png", "presentation.png"):
        if name not in _icons:
            path = os.path.join(icons_dir, name)
            if os.path.exists(path):
                _icons.load(name, path, "IMAGE")


def unload_icons():
    global _icons
    if _icons:
        bpy.utils.previews.remove(_icons)
        _icons = None


def get_icon_id(name):
    if _icons and name in _icons:
        return _icons[name].icon_id
    return 0
