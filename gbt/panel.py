"""The floating button panel. Same buttons as before, plus a scene status line and a Load scene button."""
import qt
import slicer


def build(D):
    for attr in ('gbt_panel', 'demo_panel'):
        try:
            getattr(slicer, attr).close()
        except Exception:
            pass
    w = qt.QWidget()
    w.setWindowTitle('gbt2026')
    w.setWindowFlags(qt.Qt.Tool | qt.Qt.WindowStaysOnTopHint)
    w.setStyleSheet('QPushButton{font-size:14px;min-height:34px;padding:2px 10px;} '
                    'QLabel{font-weight:bold;font-size:12px;color:#444;}')
    root = qt.QVBoxLayout(w)

    def safe(fn):
        def run():
            try:
                fn()
            except Exception as e:
                print('gbt2026 button error:', repr(e))
        return run

    def row(title, items):
        root.addWidget(qt.QLabel(title))
        h = qt.QHBoxLayout()
        for label, fn in items:
            b = qt.QPushButton(label)
            b.connect('clicked()', safe(fn))
            h.addWidget(b)
        root.addLayout(h)

    status = qt.QLabel('')
    root.addWidget(status)
    D.listeners.append(lambda: status.setText(D.status()))
    status.setText(D.status())
    row('SCENE FILE', [('Load scene', D.load_scene)])

    S = lambda n: (lambda: D.scene(n))
    row('HEMISPHERE', [('Left', lambda: D.setside('left')), ('Right', lambda: D.setside('right')),
                       ('Both', lambda: D.setside('both'))])
    row('CORTEX', [('Gyri', S('gyri')), ('Glass', S('glass')), ('Inflated', S('inflated')),
                   ('Angular + SMG', S('angular'))])
    row('TRACTS', [('SLF', S('slf')), ('Arcuate', S('arcuate')), ('IFOF', S('ifof')), ('ILF', S('ilf')),
                   ('Splenium', S('splenium'))])
    row('VISUAL', [('Optic radiation', S('optic')), ("Meyer's loop", S('meyer')), ('Visual pathway', S('visual'))])
    row('COMBINED', [('Language', S('lang')), ('All tracts', S('tracts')), ('WOW', S('wow')), ('Full', S('full'))])
    row('VIEW', [('Left', lambda: D.look('left')), ('Right', lambda: D.look('right')),
                 ('Top', lambda: D.look('top')), ('Front', lambda: D.look('front')),
                 ('Back', lambda: D.look('back')), ('Spin', D.toggle_spin), ('T1 planes', D.toggle_planes)])
    row('LAYOUT', [('3D only', lambda: D.layout('3d')), ('4 views', lambda: D.layout('4')),
                   ('Conventional', lambda: D.layout('conv'))])
    row('FLOW', [('Back', D.back), ('Next', D.next), ('Reset', D.reset)])
    root.addWidget(qt.QLabel('GLASS OPACITY'))
    sl = qt.QSlider(qt.Qt.Horizontal)
    sl.setRange(5, 80)
    sl.setValue(32)
    sl.connect('valueChanged(int)', lambda v: D.glass_opacity(v / 100.0))
    root.addWidget(sl)
    w.show()
    w.move(40, 120)
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
