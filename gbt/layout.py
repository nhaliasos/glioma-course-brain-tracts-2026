"""The button panel layout. Edit this file to add, remove or reorder buttons.

Each section is:  (title, buttons_per_row, [(button label, action), ...])

Actions (the same words a keyboard shortcut or a voice command will use later):
    load                          load the scene file (it also loads by itself at startup)
    reload                        recovery: clear everything and load the scene file again
    tract:<name>                  toggle a tract on/off (adds to what is shown); tract:clear removes all
    scene:<name>                  gyri, glass, inflated, angular, slf, arcuate, ifof, ilf, splenium, tapetum,
                                  uf, mdlf, vof, ec, ic, cr, cst, fstr, sagittal, optic, meyer, visual, lang, tracts, wow, full
    side:<left|right|both>        which hemisphere the tracts are shown on
    surface:<gyri|inflated|glass> brain surface on/off (one at a time)
    view:reset                    back to a straight side view, centred
    look:<left|right|top|front|back|bottom>   camera direction
    layout:<3d|4|conv>            Slicer window layout
    flow:<next|back|reset>        step through the talk / return to the start
    toggle:<spin|planes|t1>          rotate the brain / show the T1 slice planes
"""

SECTIONS = [
    ("SCENE FILE", 1, [("Reload scene", "reload")]),
    ("HEMISPHERE", 3, [("Left", "side:left"), ("Right", "side:right"), ("Both", "side:both")]),
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
    ("DEEP STRUCTURES", 3, [("Ventricles", "tract:ventricles"), ("Basal ganglia", "tract:bg"), ("Brainstem", "tract:brainstem")]),
    ("SURFACE", 1, [("Gyri and sulci", "surface:gyri"), ("Inflated", "surface:inflated"), ("Glass brain", "surface:glass")]),
    ("BRAIN", 2, [("T1 slices", "toggle:t1"), ("Reset 3D view", "view:reset")]),
]
