#!/usr/bin/env python3
"""gbt2026 doctor: is this machine ready for the demo?

Standard library only, so it runs on a fresh PC. Usage (from the repo folder):
    python scripts\\doctor.py
Exit code 0 = no failures, 1 = at least one FAIL.
"""
import glob
import os
import platform
import re
import shutil
import socket
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
results = []


def report(status, name, detail=""):
    results.append(status)
    print(f"[{status:<4}] {name}" + (f": {detail}" if detail else ""))


def run(cmd, timeout=15):
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return (out.stdout or out.stderr).strip()
    except Exception:
        return ""


def check_system():
    report("OK", "Operating system", f"{platform.system()} {platform.release()}")
    report("OK", "Python", sys.version.split()[0])
    free_gb = shutil.disk_usage(ROOT).free / 1e9
    report("OK" if free_gb >= 20 else "WARN", "Free disk space", f"{free_gb:.0f} GB (want 20+)")
    if "onedrive" in str(ROOT).lower():
        report("WARN", "Repo location", "inside OneDrive; move it to a plain folder such as C:\\gbt2026")
    else:
        report("OK", "Repo location", str(ROOT))
    if " " in str(ROOT):
        report("WARN", "Path contains spaces", "can break scripts; prefer a short path")


def check_gpu():
    if platform.system() != "Windows":
        return
    out = run(["powershell", "-NoProfile", "-Command",
               "(Get-CimInstance Win32_VideoController | Select-Object -ExpandProperty Name) -join '; '"])
    if out:
        report("OK", "Graphics", out)
        if "nvidia" not in out.lower() and "radeon" not in out.lower():
            report("WARN", "Graphics", "integrated only; test the 'wow' and 'full' scenes for speed")
    else:
        report("WARN", "Graphics", "could not read the graphics adapter")


def find_slicer():
    candidates = []
    if platform.system() == "Windows":
        for base in (os.environ.get("LOCALAPPDATA", ""), os.environ.get("ProgramFiles", "")):
            if base:
                candidates += glob.glob(os.path.join(base, "slicer.org", "Slicer *", "Slicer.exe"))
                candidates += glob.glob(os.path.join(base, "Slicer *", "Slicer.exe"))
    else:
        found = shutil.which("Slicer")
        if found:
            candidates.append(found)
    return sorted(candidates)


def check_slicer():
    found = find_slicer()
    if not found:
        report("FAIL", "3D Slicer", "not found in the usual install folders")
        return
    for exe in found:
        m = re.search(r"Slicer (\d+\.\d+(?:\.\d+)?)", exe)
        report("OK", "3D Slicer", f"{exe}" + (f" (version {m.group(1)})" if m else ""))
    if len(found) > 1:
        report("WARN", "3D Slicer", "several versions installed; make sure you launch the one you rehearsed with")


def check_git():
    out = run(["git", "--version"])
    if not out:
        report("FAIL", "Git", "not installed")
        return
    report("OK", "Git", out)
    if (ROOT / ".git").exists():
        head = run(["git", "-C", str(ROOT), "log", "-1", "--format=%h %s"])
        dirty = run(["git", "-C", str(ROOT), "status", "--porcelain"])
        report("OK", "Repo", head)
        report("OK" if not dirty else "WARN", "Working tree",
               "clean" if not dirty else "uncommitted changes")
    else:
        report("WARN", "Repo", "not a Git clone (fine for an offline copy)")


def check_deck():
    decks = sorted((ROOT / "presentations").glob("*/deck.yaml"))
    if not decks:
        report("FAIL", "Decks", "no presentations/*/deck.yaml found")
        return
    report("OK", "Decks", ", ".join(d.parent.name for d in decks))
    try:
        import yaml  # optional
    except ImportError:
        report("WARN", "Deck syntax", "PyYAML not installed; skipped (pip install pyyaml)")
        return
    for d in decks:
        try:
            doc = yaml.safe_load(d.read_text(encoding="utf-8"))
            layers = set(doc.get("layers", {}))
            names = {s["name"] for s in doc.get("scenes", [])}
            bad = [n for s in doc.get("scenes", []) for n in s.get("layers", []) if n not in layers]
            bad += [f for f in doc.get("flow", []) if f not in names]
            report("OK" if not bad else "FAIL", f"Deck {d.parent.name}",
                   "consistent" if not bad else f"unknown references: {sorted(set(bad))}")
        except Exception as e:
            report("FAIL", f"Deck {d.parent.name}", str(e))


def check_data():
    manifest = ROOT / "data" / "manifest.yaml"
    if not manifest.exists():
        report("FAIL", "Manifest", "data/manifest.yaml missing")
        return
    ds, cur = {}, None
    for line in manifest.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^  (\w+):\s*$", line)
        if m:
            cur = m.group(1)
            continue
        m = re.match(r"^    path:\s*(\S+)", line)
        if m and cur:
            ds[cur] = m.group(1)
    for name, rel in ds.items():
        p = ROOT / "data" / rel
        if p.is_dir() and any(p.iterdir()):
            size = sum(f.stat().st_size for f in p.rglob("*") if f.is_file()) / 1e6
            report("OK", f"Data {name}", f"{size:.0f} MB")
        else:
            report("FAIL", f"Data {name}", f"missing or empty: data/{rel}")


def check_network():
    for host in ("github.com", "api.anthropic.com"):
        try:
            socket.create_connection((host, 443), timeout=4).close()
            report("OK", f"Network {host}", "reachable")
        except OSError:
            report("WARN", f"Network {host}", "unreachable (offline fallback: panel works without Claude)")


if __name__ == "__main__":
    print(f"gbt2026 doctor - {ROOT}\n")
    for fn in (check_system, check_gpu, check_slicer, check_git, check_deck, check_data, check_network):
        fn()
    fails, warns = results.count("FAIL"), results.count("WARN")
    print(f"\n{fails} fail, {warns} warn")
    sys.exit(1 if fails else 0)
