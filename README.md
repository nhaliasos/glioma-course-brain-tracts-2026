# glioma-course-brain-tracts-2026 (gbt2026)

Live 3D Slicer demos of brain tracts for the 2026 glioma course, driven by an
AI assistant through MCP. One shared engine, one small deck file per presenter.

## Layout

| Folder | Purpose |
|---|---|
| `gbt/` | The engine (code only) |
| `presentations/<presenter>/deck.yaml` | Scenes, tracts and voice phrases for one presenter |
| `data/` | Downloaded atlases and tracts. **Not tracked by Git.** Only `data/manifest.yaml` is |
| `scripts/` | `fetch_data`, `install`, `doctor` |
| `docs/` | Manual setup steps |

## Adding your own presentation

1. Copy `presentations/nik/` to `presentations/<your-name>/`.
2. Edit `deck.yaml`: tracts, scenes, flow, caveats. `python scripts/doctor.py` checks it against the panel buttons.
3. Open a pull request.

Do not commit patient data or large imaging files. Keep them local.

## Status

Work in progress: the engine and scripts are being written.

## Licence

MIT. Atlas and tract data keep their own licences; see `data/manifest.yaml`.
