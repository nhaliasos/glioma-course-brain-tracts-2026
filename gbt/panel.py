"""The floating button panel, built from gbt/layout.py."""
import qt
import slicer

from . import layout


def build(D):
    for attr in ('gbt_panel', 'demo_panel'):
        try:
            getattr(slicer, attr).close()
        except Exception:
            pass
    width = int(D.cfg.get('panel_width', 240))
    w = qt.QWidget()                       # outer window: fixed width, never taller than the screen
    w.setWindowTitle('gbt2026')
    w.setWindowFlags(qt.Qt.Tool | qt.Qt.WindowStaysOnTopHint)
    w.setFixedWidth(width)
    inner = qt.QWidget()                   # all the buttons live here, inside a scroll area
    w.setStyleSheet('QPushButton{font-size:11px;min-height:22px;padding:0px 4px;} '
                    'QPushButton:checked{background:#2e7d32;color:white;} '
                    'QLabel{font-weight:bold;font-size:10px;color:#444;}')
    root = qt.QVBoxLayout(inner)
    root.setSpacing(2)
    root.setContentsMargins(4, 2, 4, 2)

    def run(action):
        def go():
            try:
                D.do(action)
            except Exception as e:
                print('gbt2026 button error (%s): %r' % (action, e))
        return go

    status = qt.QLabel('')
    status.setWordWrap(True)
    root.addWidget(status)
    D.listeners.append(lambda: status.setText(D.status()))
    status.setText(D.status())

    toggles = {}                     # tract key -> button, so the checked state follows D.on

    def sync():
        for key, btn in toggles.items():
            btn.setChecked(key in D.on)
    flags = {}                       # button -> function telling whether it is "on"

    def sync2():
        for btn, fn in flags.items():
            btn.setChecked(bool(fn()))
    D.listeners.append(sync)
    D.listeners.append(sync2)
    scene_btns = []

    def sync_scene():
        """The scene button shows the state: grey/red = not loaded, amber = loading, green = loaded."""
        for btn in scene_btns:
            if D.loading:
                btn.setText('Loading scene...')
                btn.setStyleSheet('background:#f9a825;color:black;')
            elif D.scene_loaded():
                btn.setText('Scene loaded  \u2713  (click to reload)')
                btn.setStyleSheet('background:#2e7d32;color:white;')
            else:
                btn.setText('Scene NOT loaded - click to load')
                btn.setStyleSheet('background:#c62828;color:white;')
    D.listeners.append(sync_scene)

    for title, per_row, buttons in layout.SECTIONS:
        if title:
            root.addWidget(qt.QLabel(title))
        grid = qt.QGridLayout()
        grid.setSpacing(2)
        for i, (label, action) in enumerate(buttons):
            b = qt.QPushButton(label)
            b.connect('clicked()', run(action))
            if action.startswith('tract:') and action != 'tract:clear':
                b.setCheckable(True)
                toggles[action.split(':', 1)[1]] = b
            if action.startswith('surface:'):
                b.setCheckable(True)
                flags[b] = (lambda k: (lambda: D.surface == k))(action.split(':', 1)[1])
            if action == 'reload':
                scene_btns.append(b)
            if action == 'toggle:t1':
                b.setCheckable(True)
                flags[b] = lambda: D.planes_on
            grid.addWidget(b, i // per_row, i % per_row)
        root.addLayout(grid)
    sync_scene()
    root.addStretch(1)
    scroll = qt.QScrollArea()
    scroll.setWidgetResizable(True)
    scroll.setFrameShape(qt.QFrame.NoFrame)
    scroll.setHorizontalScrollBarPolicy(qt.Qt.ScrollBarAlwaysOff)
    scroll.setWidget(inner)
    outer = qt.QVBoxLayout(w)
    outer.setContentsMargins(0, 0, 0, 0)
    outer.addWidget(scroll)
    avail = qt.QApplication.desktop().availableGeometry(slicer.util.mainWindow()).height()
    want = inner.sizeHint.height() + 4
    w.resize(width, max(200, min(want, avail - 60)))   # scrolls if the screen is too short
    w.show()
    qt.QApplication.processEvents()
    want = inner.sizeHint.height() + 4           # sizes are only final once the window is shown
    w.resize(width, max(200, min(want, avail - 60)))
    w.move(20, 20)
    return w


def _show(w):
    w.show()
    w.raise_()
    w.activateWindow()


def add_reopen(w):
    """If the panel is closed by accident, bring it back from the 'gbt2026' menu or with Ctrl+Shift+G."""
    mw = slicer.util.mainWindow()
    for attr in ('gbt_menu', 'gbt_shortcut'):          # clean up after a re-run
        old = getattr(slicer, attr, None)
        try:
            if attr == 'gbt_menu' and old is not None:
                mw.menuBar().removeAction(old.menuAction())
            if old is not None:
                old.deleteLater()
        except Exception:
            pass
    menu = mw.menuBar().addMenu('gbt2026')
    act = menu.addAction('Show panel  (Ctrl+Shift+G)')
    act.connect('triggered()', lambda: _show(w))
    sc = qt.QShortcut(qt.QKeySequence('Ctrl+Shift+G'), mw)
    sc.connect('activated()', lambda: _show(w))
    slicer.gbt_menu = menu
    slicer.gbt_shortcut = sc
