"""Tiny reader for gbt.local.yaml (plain 'key: value' lines, no PyYAML needed inside Slicer)."""
import os
import re

DEFAULTS = {
    "enabled": "true",                          # false = Slicer starts normally, no gbt2026 panel
    "scene": "data/scenes/gbt2026_scene.mrb",   # relative to the repo root, or an absolute path
    "panel_width": "240",                       # width of the button panel in pixels
    "autoload_scene": "false",                  # true = load the scene when Slicer starts
}


def load(repo_root):
    cfg = dict(DEFAULTS)
    path = os.path.join(repo_root, "gbt.local.yaml")
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            for line in f:
                m = re.match(r"^\s*([A-Za-z_]+)\s*:\s*([^#]*?)\s*(#.*)?$", line)
                if m and m.group(2):
                    cfg[m.group(1)] = m.group(2).strip("\"'")
    scene = cfg["scene"]
    if not os.path.isabs(scene):
        scene = os.path.join(repo_root, scene)
    cfg["scene_path"] = os.path.normpath(scene)
    cfg["enabled"] = str(cfg["enabled"]).lower() in ("1", "true", "yes", "on")
    cfg["autoload_scene"] = str(cfg["autoload_scene"]).lower() in ("1", "true", "yes", "on")
    try:
        cfg["panel_width"] = int(cfg["panel_width"])
    except ValueError:
        cfg["panel_width"] = 240
    cfg["repo_root"] = repo_root
    return cfg
