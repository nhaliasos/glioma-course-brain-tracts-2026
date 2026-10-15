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
    w.setStyleSheet('QPushButton{font-size:11px;min-height:22px;padding:0px 4px;} '
                    'QPushButton:checked{background:#2e7d32;color:white;} '
                    'QLabel{font-weight:bold;font-size:10px;color:#444;}')

    def run(action):
        def go():
            try:
                D.do(action)
            except Exception as e:
                print('gbt2026 button error (%s): %r' % (action, e))
        return go

    status = qt.QLabel('')
    status.setWordWrap(True)
    D.listeners.append(lambda: status.setText(D.status()))
    status.setText(D.status())

    toggles = {}                     # tract key -> button, so the checked state follows D.on
    flags = {}                       # button -> function telling whether it is "on"
    sliders = {}                     # opacity group -> slider
    style_sliders = {}               # 'density' | 'thickness' -> (slider, label)
    scene_btns = []

    def sync():
        for key, btn in toggles.items():
            btn.setChecked(key in D.on)
        for btn, fn in flags.items():
            btn.setChecked(bool(fn()))
        for key, (sl, lab) in style_sliders.items():
            v = D.density if key == 'density' else D.radius
            sl.blockSignals(True)
            sl.setValue(int(round(v * 100)))
            sl.blockSignals(False)
            lab.setText(('%d%%' % int(round(v * 100))) if key == 'density' else ('%.2f mm' % v))
        for grp, (sl, lab) in sliders.items():
            v = D.get_opacity(grp, sl.value / 100.0)
            sl.blockSignals(True)
            sl.setValue(int(round(v * 100)))
            sl.blockSignals(False)
            lab.setText('%d%%' % int(round(v * 100)))

    def sync_scene():
        """The scene button shows the state: red = not loaded, amber = loading, green = loaded."""
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
    D.listeners.append(sync)
    D.listeners.append(sync_scene)

    def add_sections(root, sections):
        for title, per_row, items in sections:
            if title:
                root.addWidget(qt.QLabel(title))
            if per_row == 'style':
                for label, key, lo, hi in items:
                    row = qt.QHBoxLayout()
                    name = qt.QLabel(label)
                    name.setFixedWidth(62)
                    sl = qt.QSlider(qt.Qt.Horizontal)
                    sl.setRange(lo, hi)
                    sl.setTracking(False)              # rebuild the tubes only when the slider is released
                    val = qt.QLabel('')
                    val.setFixedWidth(46)

                    def shown(v, k=key, lab=val):
                        lab.setText(('%d%%' % v) if k == 'density' else ('%.2f mm' % (v / 100.0)))

                    def released(v, k=key):
                        D.do('style:%s:%.2f' % (k, v / 100.0))
                    sl.connect('sliderMoved(int)', shown)
                    sl.connect('valueChanged(int)', released)
                    style_sliders[key] = (sl, val)
                    row.addWidget(name)
                    row.addWidget(sl)
                    row.addWidget(val)
                    root.addLayout(row)
                continue
            if per_row == 'sliders':
                for label, grp, lo, hi in items:
                    row = qt.QHBoxLayout()
                    name = qt.QLabel(label)
                    name.setFixedWidth(70)
                    sl = qt.QSlider(qt.Qt.Horizontal)
                    sl.setRange(int(lo * 100), int(hi * 100))
                    val = qt.QLabel('')
                    val.setFixedWidth(34)
                    def moved(v, g=grp, lab=val):
                        lab.setText('%d%%' % v)                  # show the number while dragging
                        D.do('opacity:%s:%.2f' % (g, v / 100.0))
                    sl.connect('valueChanged(int)', moved)
                    sliders[grp] = (sl, val)
                    row.addWidget(name)
                    row.addWidget(sl)
                    row.addWidget(val)
                    root.addLayout(row)
                continue
            grid = qt.QGridLayout()
            grid.setSpacing(2)
            for i, (label, action) in enumerate(items):
                b = qt.QPushButton(label)
                b.connect('clicked()', run(action))
                if action.startswith('tract:') and action != 'tract:clear':
                    b.setCheckable(True)
                    toggles[action.split(':', 1)[1]] = b
                if action.startswith('surface:'):
                    b.setCheckable(True)
                    flags[b] = (lambda k: (lambda: D.surface == k))(action.split(':', 1)[1])
                if action.startswith('side:'):
                    b.setCheckable(True)
                    flags[b] = (lambda k: (lambda: D.side == k))(action.split(':', 1)[1])
                if action == 'reload':
                    scene_btns.append(b)
                if action == 'toggle:t1':
                    b.setCheckable(True)
                    flags[b] = lambda: D.planes_on
                if action == 'toggle:spin':
                    b.setCheckable(True)
                    flags[b] = lambda: D.spinning
                grid.addWidget(b, i // per_row, i % per_row)
            root.addLayout(grid)

    outer = qt.QVBoxLayout(w)
    outer.setSpacing(2)
    outer.setContentsMargins(4, 2, 4, 2)
    add_sections(outer, layout.HEADER)
    outer.insertWidget(0, status)
    tabs = qt.QTabWidget()
    pages = []
    for name, sections in layout.TABS:
        inner = qt.QWidget()
        col = qt.QVBoxLayout(inner)
        col.setSpacing(2)
        col.setContentsMargins(2, 2, 2, 2)
        add_sections(col, sections)
        col.addStretch(1)
        scroll = qt.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(qt.QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(qt.Qt.ScrollBarAlwaysOff)
        scroll.setWidget(inner)
        tabs.addTab(scroll, name)
        pages.append(inner)
    outer.addWidget(tabs)
    add_sections(outer, layout.FOOTER)
    sync()
    sync_scene()
    avail = qt.QApplication.desktop().availableGeometry(slicer.util.mainWindow()).height()
    w.show()
    qt.QApplication.processEvents()                    # sizes are only final once the window is shown
    head = w.sizeHint.height() - tabs.sizeHint.height()
    want = head + max(p.sizeHint.height() for p in pages) + 40
    w.resize(width, max(200, min(want, avail - 60)))   # the tab scrolls if the screen is too short
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
