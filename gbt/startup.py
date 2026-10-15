"""Entry point: called from ~/.slicerrc.py (written by scripts/install.py) when Slicer starts."""
import slicer

from . import config, controller, panel


def start(repo_root):
    cfg = config.load(repo_root)
    if not cfg['enabled']:
        print('gbt2026: disabled in gbt.local.yaml (enabled: false) - not loading the panel')
        return None
    D = controller.Controller(cfg)
    slicer.gbt = D
    slicer.demo = D            # compatibility alias: existing voice/MCP commands call slicer.demo
    w = panel.build(D)
    slicer.gbt_panel = w
    slicer.demo_panel = w
    try:
        panel.add_reopen(w)
    except Exception as e:      # never let the extra menu stop the panel itself
        print('gbt2026: could not add the reopen menu:', repr(e))
    if cfg['autoload_scene'] and not D.scene_loaded():
        # a moment after startup, so Slicer's window is up and the panel is visible while the scene loads
        import qt
        qt.QTimer.singleShot(1500, lambda: None if D.scene_loaded() else D.load_scene())
    return D
