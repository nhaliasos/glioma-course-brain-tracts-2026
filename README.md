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

## What it does

A thin panel inside 3D Slicer (menu `gbt2026`, or Ctrl+Shift+G) drives the scene through one
command bus, `Controller.do("action")`. Buttons, keyboard, voice and Claude all use the same actions.

- **Header:** Reload scene (red / amber / green for the load state) and the Left / Right / Both hemisphere buttons.
- **Tracts tab:** each button toggles a tract on or off and they add up. Tracts are drawn left and right
  with a distinct colour each, opacity 0.15, and never switch the glass brain on.
  Association (arcuate, IFOF, ILF, uncinate, MdLF, VOF, external capsule), SLF I / II / III,
  projection (corticospinal, frontostriatal, corona radiata), internal capsule (anterior limb, genu,
  posterior limb, retrolenticular, sublenticular, all parts), commissural (splenium, tapetum),
  visual (optic radiation, Meyer's loop), sagittal stratum, and an opacity slider.
- **Style tab:** density and thickness of all tracts.
- **Brain tab:** gyri / sulci atlas, inflated and glass surfaces (follow the hemisphere buttons),
  ventricles, basal ganglia, brainstem, subject T1 slices, opacity sliders.
- **Footer:** camera views, Spin, Reset 3D view.
- Slicer's Web Server starts automatically, so Claude can drive the scene over MCP (set `webserver: false`
  in `gbt.local.yaml` on untrusted networks).

## Data sources

| Content | Source |
|---|---|
| Most tracts, T1 space | ORG atlas (clusters in the `T_*.mrb` files) |
| Optic radiation, VOF | HCP1065 atlas, moved to the ORG brain by the ICBM-to-ORG transform |
| Meyer's loop | CONSULT probability maps (generated fibres, not measured) |
| Gyri / sulci, ventricles, basal ganglia, brainstem, subject T1 | SPL brain atlas |
| Glass, inflated surfaces | FreeSurfer fsaverage, fitted to the ORG T1 (x1.076) |

## Derived tracts (not atlas labels)

- **Tapetum:** the parts of the ORG splenium fibres (CC6 / CC7) that lie in a thin shell lateral to the
  lateral ventricles (`gbt/build.py: add_tapetum`).
- **Internal capsule parts:** ORG projection fibres assigned to a part by where they pass the lentiform
  nucleus (`add_internal_capsule`). The atlas has no separate labels for these. The sublenticular part is
  thin and the auditory radiation is not available.

## Known limits

- The temporal horns of the ventricles are not resolved in the SPL atlas or in the fsaverage template.
- The optic radiation is one bundle; a separate dorsal bundle is not distinguishable.
- No subthalamic nucleus yet (not in the SPL atlas; needs a DBS atlas such as the Lead-DBS collection).
- The scene file `data/scenes/gbt2026_scene.mrb` is not in Git. Keep your own backup.
- Per-machine settings live in `gbt.local.yaml` (not tracked): `enabled`, `scene`, `webserver`, `autoload_scene`, `panel_width`.

## Status

Working for the 23 Oct 2026 talk. Open items: STN, VOF check against references, keyboard and voice
shortcuts, rebuild-from-atlases script, dress rehearsal.

## Licence

MIT. Atlas and tract data keep their own licences; see `data/manifest.yaml`.
