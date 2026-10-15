"""The button panel layout. Edit this file to add, remove or reorder buttons.

Each section is:  (title, buttons_per_row, [(button label, action), ...])

Actions (the same words a keyboard shortcut or a voice command will use later):
    load                          load the scene file
    tract:<name>                  toggle a tract on/off (adds to what is shown); tract:clear removes all
    scene:<name>                  gyri, glass, inflated, angular, slf, arcuate, ifof, ilf, splenium, tapetum,
                                  uf, mdlf, vof, ec, ic, cr, cst, fstr, sagittal, optic, meyer, visual, lang, tracts, wow, full
    side:<left|right|both>        which hemisphere the tracts are shown on
    look:<left|right|top|front|back|bottom>   camera direction
    layout:<3d|4|conv>            Slicer window layout
    flow:<next|back|reset>        step through the talk / return to the start
    toggle:<spin|planes>          rotate the brain / show the T1 slice planes
"""

SECTIONS = [
    ("SCENE FILE", 1, [("Load scene", "load")]),
    ("HEMISPHERE", 3, [("Left", "side:left"), ("Right", "side:right"), ("Both", "side:both")]),
    ("ASSOCIATION", 2, [
        ("Arcuate", "tract:arcuate"), ("SLF I-III", "tract:slf"),
        ("IFOF", "tract:ifof"), ("ILF", "tract:ilf"),
        ("Uncinate", "tract:uf"), ("MdLF", "tract:mdlf"),
        ("VOF", "tract:vof"), ("External capsule", "tract:ec"),
    ]),
    ("PROJECTION", 2, [
        ("Corticospinal", "tract:cst"), ("Frontostriatal", "tract:fstr"),
        ("Internal capsule", "tract:ic"), ("Corona radiata", "tract:cr"),
    ]),
    ("COMMISSURAL", 2, [("Splenium", "tract:splenium"), ("Tapetum (derived)", "tract:tapetum")]),
    ("VISUAL", 2, [
        ("Optic radiation", "tract:optic"), ("Meyer's loop", "tract:meyer"),
        ("Sagittal stratum (composite)", "tract:sagittal"),
    ]),
    ("", 1, [("Clear all tracts", "tract:clear")]),
]
