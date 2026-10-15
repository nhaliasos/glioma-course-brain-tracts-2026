"""The button panel layout. Edit this file to add, remove or reorder buttons.

The panel has a header (scene state + hemisphere), tabs, and a footer (camera) that are always visible.
Each section is:  (title, buttons_per_row, [(button label, action), ...])
A section with buttons_per_row == "style" holds the density / thickness sliders: [(label, "density"|"thickness", min, max), ...]
(density is in %, thickness in 1/100 mm; they rebuild all tracts when released).
A section with buttons_per_row == "sliders" holds sliders instead:  [(label, group, min, max), ...]
    group: tracts | surface | deep  -> opacity of that set of models (the same words work as opacity:<group>:<0-1>)

Actions (the same words a keyboard shortcut or a voice command will use later):
    load                          load the scene file (it also loads by itself at startup)
    reload                        recovery: clear everything and load the scene file again
    tract:<name>                  toggle a tract on/off (adds to what is shown); tract:clear removes all
    scene:<name>                  gyri, glass, inflated, angular, slf, arcuate, ifof, ilf, splenium, tapetum,
                                  uf, mdlf, vof, ec, ic, cr, cst, fstr, sagittal, optic, meyer, visual, lang, tracts, wow, full
    side:<left|right|both>        which hemisphere the tracts are shown on
    surface:<gyri|inflated|glass> brain surface on/off (one at a time)
    style:density:<0.05-1>        fraction of streamlines drawn;  style:thickness:<mm>  tube radius;  style:reset
    opacity:<tracts|surface|deep>:<0-1>   set the opacity of a set of models
    view:reset                    back to a straight side view, centred
    look:<left|right|top|front|back|bottom>   camera direction
    layout:<3d|4|conv>            Slicer window layout
    flow:<next|back|reset>        step through the talk / return to the start
    toggle:<spin|planes|t1>          rotate the brain / show the T1 slice planes
"""

HEADER = [
    ("", 1, [("Reload scene", "reload")]),
    ("HEMISPHERE", 3, [("Left", "side:left"), ("Right", "side:right"), ("Both", "side:both")]),
]

FOOTER = [          # always visible, below the tabs
    ("CAMERA", 3, [("Left", "look:left"), ("Right", "look:right"), ("Top", "look:top"),
                   ("Front", "look:front"), ("Back", "look:back"), ("Bottom", "look:bottom")]),
    ("", 2, [("Spin", "toggle:spin"), ("Reset 3D view", "view:reset")]),
]

TABS = [
    ("Tracts", [
        ("ASSOCIATION", 2, [
            ("Arcuate", "tract:arcuate"), ("IFOF", "tract:ifof"),
            ("ILF", "tract:ilf"), ("Uncinate", "tract:uf"),
            ("MdLF", "tract:mdlf"),
            ("VOF", "tract:vof"), ("External capsule", "tract:ec"),
        ]),
        ("SLF", 3, [("SLF I", "tract:slf1"), ("SLF II", "tract:slf2"), ("SLF III", "tract:slf3")]),
        ("PROJECTION", 2, [
            ("Corticospinal", "tract:cst"), ("Frontostriatal", "tract:fstr"),
            ("Internal capsule", "tract:ic"), ("Corona radiata", "tract:cr"),
        ]),
        ("COMMISSURAL", 2, [("Splenium", "tract:splenium"), ("Tapetum", "tract:tapetum")]),
        ("VISUAL", 2, [("Optic radiation", "tract:optic"), ("Meyer's loop", "tract:meyer")]),
        ("SAGITTAL", 1, [("Sagittal stratum", "tract:sagittal")]),
        ("", 1, [("Clear all tracts", "tract:clear")]),
        ("OPACITY", "sliders", [("Tracts", "tracts", 0.05, 1.0)]),
    ]),
    ("Style", [
        ("TRACT DRAWING", "style", [("Density", "density", 5, 100), ("Thickness", "thickness", 5, 150)]),
        ("", 1, [("Reset style", "style:reset")]),
    ]),
    ("Brain", [
        ("DEEP STRUCTURES", 3, [("Ventricles", "tract:ventricles"), ("Basal ganglia", "tract:bg"),
                                ("Brainstem", "tract:brainstem")]),
        ("SURFACE", 1, [("Gyri and sulci", "surface:gyri"), ("Inflated", "surface:inflated"),
                        ("Glass brain", "surface:glass")]),
        ("T1", 1, [("T1 slices", "toggle:t1")]),
        ("OPACITY", "sliders", [("Surface", "surface", 0.05, 1.0), ("Deep struct.", "deep", 0.1, 1.0)]),
    ]),
]
