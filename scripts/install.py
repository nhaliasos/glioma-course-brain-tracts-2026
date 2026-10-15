#!/usr/bin/env python3
"""Install the gbt2026 startup hook for 3D Slicer (standard library only).

Slicer runs ~/.slicerrc.py at every start. This script writes a small stub there
that loads the engine from this repo, after backing up whatever was there before.

    python scripts/install.py              install (or refresh) the hook
    python scripts/install.py --dry-run    show what would happen, change nothing
    python scripts/install.py --uninstall  put the previous .slicerrc.py back

Options for unusual cases: --home PATH (where .slicerrc.py lives) and
--repo-path TEXT (the repo path to write into the stub, as Slicer's machine sees it).
"""
import argparse
import shutil
import sys
import time
from pathlib import Path

MARKER = "# gbt2026 startup (managed by scripts/install.py)"
BACKUP = ".slicerrc.py.pre-gbt2026.bak"

STUB = MARKER + """
import sys
_GBT_REPO = %r
try:
    if _GBT_REPO not in sys.path:
        sys.path.insert(0, _GBT_REPO)
    import gbt.startup as _gbt_startup
    _gbt_startup.start(_GBT_REPO)
except Exception as _e:
    print('gbt2026 failed to load:', _e)
"""

LOCAL_CONFIG = """# gbt.local.yaml - settings for THIS machine (not tracked by Git)
scene: data/scenes/gbt2026_scene.mrb   # relative to the repo, or a full path
autoload_scene: false                  # true = load the scene automatically when Slicer starts
"""


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--uninstall", action="store_true")
    ap.add_argument("--home", default=None)
    ap.add_argument("--repo-path", default=None)
    a = ap.parse_args()

    repo = Path(__file__).resolve().parent.parent
    home = Path(a.home) if a.home else Path.home()
    rc = home / ".slicerrc.py"
    bak = home / BACKUP
    current = rc.read_text(encoding="utf-8") if rc.exists() else None
    say = (lambda s: print(("[dry-run] " if a.dry_run else "") + s))

    if a.uninstall:
        if bak.exists():
            say(f"restoring {bak.name} -> {rc}")
            if not a.dry_run:
                shutil.copy2(bak, rc)
        elif current and MARKER in current:
            say(f"no backup found; removing the gbt2026 stub {rc}")
            if not a.dry_run:
                rc.unlink()
        else:
            say("nothing to uninstall")
        return 0

    stub = STUB % (a.repo_path or str(repo))
    if current is not None and MARKER not in current:
        target = bak if not bak.exists() else home / f"{BACKUP}.{time.strftime('%Y%m%d-%H%M%S')}"
        say(f"backing up existing {rc.name} -> {target.name}")
        if not a.dry_run:
            shutil.copy2(rc, target)
    elif current == stub:
        say(f"{rc} is already up to date")
    say(f"writing {rc}")
    if not a.dry_run:
        rc.write_text(stub, encoding="utf-8")

    local = repo / "gbt.local.yaml"
    if not local.exists():
        say(f"creating {local.name} with defaults")
        if not a.dry_run:
            local.write_text(LOCAL_CONFIG, encoding="utf-8")
    print("\nDone. Restart Slicer (or run the stub once) to load the gbt2026 panel.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
