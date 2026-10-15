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
    w = qt.QWidget()
    w.setWindowTitle('gbt2026')
    w.setWindowFlags(qt.Qt.Tool | qt.Qt.WindowStaysOnTopHint)
    w.setFixedWidth(width)
    w.setStyleSheet('QPushButton{font-size:12px;min-height:28px;padding:1px 6px;} '
                    'QPushButton:checked{background:#2e7d32;color:white;} '
                    'QLabel{font-weight:bold;font-size:11px;color:#444;}')
    root = qt.QVBoxLayout(w)
    root.setSpacing(3)

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
    D.listeners.append(sync)

    for title, per_row, buttons in layout.SECTIONS:
        if title:
            root.addWidget(qt.QLabel(title))
        grid = qt.QGridLayout()
        grid.setSpacing(3)
        for i, (label, action) in enumerate(buttons):
            b = qt.QPushButton(label)
            b.connect('clicked()', run(action))
            if action.startswith('tract:') and action != 'tract:clear':
                b.setCheckable(True)
                toggles[action.split(':', 1)[1]] = b
            grid.addWidget(b, i // per_row, i % per_row)
        root.addLayout(grid)
    root.addStretch(1)
    w.show()
    w.move(40, 120)
    w.adjustSize()
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
