"""The button panel layout. Edit this file to add, remove or reorder buttons.

Each section is:  (title, buttons_per_row, [(button label, action), ...])

Actions (the same words a keyboard shortcut or a voice command will use later):
    load                          load the scene file
    scene:<name>                  gyri, glass, inflated, angular, slf, arcuate, ifof, ilf, splenium,
                                  optic, meyer, visual, lang, tracts, wow, full
    side:<left|right|both>        which hemisphere the tracts are shown on
    look:<left|right|top|front|back|bottom>   camera direction
    layout:<3d|4|conv>            Slicer window layout
    flow:<next|back|reset>        step through the talk / return to the start
    toggle:<spin|planes>          rotate the brain / show the T1 slice planes
"""

SECTIONS = [
    ("SCENE FILE", 1, [("Load scene", "load")]),
]
