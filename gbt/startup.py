"""Entry point: called from ~/.slicerrc.py (written by scripts/install.py) when Slicer starts."""
import slicer

from . import config, controller, panel


def start(repo_root):
    cfg = config.load(repo_root)
    D = controller.Controller(cfg)
    slicer.gbt = D
    slicer.demo = D            # compatibility alias: existing voice/MCP commands call slicer.demo
    w = panel.build(D)
    slicer.gbt_panel = w
    slicer.demo_panel = w
    if cfg['autoload_scene'] and not D.scene_loaded():
        D.load_scene()
    return D
