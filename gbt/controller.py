"""Scene controller. Shows and hides the models that already live in the loaded Slicer scene."""
import os

import ctk
import slicer
import vtk  # noqa: F401  (kept: some scene operations rely on it being imported)


class Controller:
    TR = {'slf': ['SLF I', 'SLF II', 'SLF III'], 'slf1': ['SLF I'], 'slf2': ['SLF II'], 'slf3': ['SLF III'], 'arcuate': ['Arcuate'], 'ifof': ['IFOF'], 'ilf': ['ILF'],
          'optic': ['Optic radiation'], 'meyer': ["Meyer's loop"],
          'uf': ['Uncinate'], 'mdlf': ['MdLF'], 'ec': ['External capsule'], 'ic': ['Internal capsule'],
          'cr': ['Corona radiata (frontal)', 'Corona radiata (parietal)'], 'vof': ['VOF'],
          'cst': ['Corticospinal'], 'fstr': ['Frontostriatal']}
    SEQ = ['gyri', 'glass', 'angular', 'arcuate', 'ifof', 'ilf', 'slf', 'splenium', 'visual', 'lang', 'wow']
    # a model of this name must exist, otherwise the scene is not the expected one
    PROBE = 'FS glass left'

    def __init__(self, cfg=None):
        self.cfg = cfg or {}
        self.side = 'left'
        self.cur = None
        self.i = -1
        self.spinning = False
        self.planes_on = False
        self.loading = False         # True while the scene file is being read (drives the scene button colour)
        self.surface = None          # 'glass' | 'gyri' | 'inflated' | None, set by the surface buttons
        self.on = []                 # tract keys switched on with the tract buttons, in order
        self.listeners = []          # callables run after every change, e.g. the panel label

    # ---- housekeeping -------------------------------------------------
    def _notify(self):
        for fn in list(self.listeners):
            try:
                fn()
            except Exception as e:
                print('gbt2026 listener error:', repr(e))

    def models(self):
        return {n.GetName(): n for n in slicer.util.getNodesByClass('vtkMRMLModelNode')}

    def scene_loaded(self):
        return self.PROBE in self.models()

    def load_scene(self, path=None):
        path = path or self.cfg.get('scene_path')
        if self.scene_loaded():
            print('gbt2026: scene already loaded')
            return True
        if not path or not os.path.exists(path):
            print('gbt2026: scene file not found:', path)
            return False
        slicer.util.showStatusMessage('gbt2026: loading scene...', 3000)
        self.loading = True
        self._notify()                       # the scene button turns amber ("Loading...")
        slicer.app.processEvents()
        try:
            ok = slicer.util.loadScene(path)
        finally:
            self.loading = False
        print('gbt2026: scene', 'loaded' if ok else 'FAILED to load', path)
        self._notify()                       # ... and green when it is done
        return bool(ok)

    def reload_scene(self):
        """Recovery button: throw the scene away, load it again from the file, reset all button states."""
        path = self.cfg.get('scene_path')
        if not path or not os.path.exists(path):
            print('gbt2026: scene file not found:', path)
            return False
        self.spin(False)
        self.on, self.surface, self.cur, self.planes_on = [], None, None, False
        slicer.util.showStatusMessage('gbt2026: reloading scene...', 5000)
        slicer.mrmlScene.Clear(0)
        slicer.app.processEvents()
        return self.load_scene(path)

    def status(self):
        if not self.scene_loaded():
            return 'Scene not loaded'
        if self.on:
            return 'Tracts: %s (%s)' % (', '.join(self.on), self.side)
        return 'Showing: %s (%s)' % (self.cur or '-', self.side)

    # ---- name tables ---------------------------------------------------
    STRUCT = {'ventricles': 'Ventricles', 'bg': 'Basal ganglia', 'brainstem': 'Brainstem'}   # SPL atlas deep structures

    def names(self, key, side):
        if key in self.STRUCT:
            pre = self.STRUCT[key] + ':'
            return [n for n in self.models() if n.startswith(pre) and n.endswith(('(%s)' % side, '(mid)'))]
        if key == 'splenium':
            return ['Splenium (CC7)']
        if key == 'tapetum':
            return ['Tapetum (%s, derived)' % side]
        out = []
        for b in self.TR[key]:
            out.append(b + (' (clean)' if side == 'left' else ' (right)') if key.startswith('slf') else b + ' (%s)' % side)
        return out

    # ---- visibility ----------------------------------------------------
    def hide_all(self):
        for nm, n in self.models().items():
            if nm.startswith(('SLF', 'Arcuate', 'IFOF', 'ILF', 'Splen', 'FS ', 'Optic', "Meyer",
                               'Uncinate', 'MdLF', 'External capsule', 'Internal capsule', 'Corona radiata', 'VOF', 'Tapetum', 'Corticospinal', 'Frontostriatal')) and n.GetDisplayNode():
                n.GetDisplayNode().SetVisibility(False)
        for n in slicer.util.getNodesByClass('vtkMRMLFiberBundleNode'):
            for i in range(n.GetNumberOfDisplayNodes()):
                n.GetNthDisplayNode(i).SetVisibility(False)
        try:
            slicer.util.getNode('SPL cortex').GetDisplayNode().SetVisibility3D(False)
        except Exception:
            pass

    TRACT_PREFIXES = ('SLF', 'Arcuate', 'IFOF', 'ILF', 'Splen', 'Optic', "Meyer", 'Uncinate', 'MdLF',
                      'External capsule', 'Internal capsule', 'Corona radiata', 'VOF', 'Tapetum',
                      'Corticospinal', 'Frontostriatal',
                      'Ventricles', 'Basal ganglia', 'Brainstem')
    GROUPS = {'sagittal': ['ifof', 'ilf', 'optic']}      # composite buttons

    def hide_tracts(self):
        for nm, n in self.models().items():
            if nm.startswith(self.TRACT_PREFIXES) and n.GetDisplayNode():
                n.GetDisplayNode().SetVisibility(False)
        for n in slicer.util.getNodesByClass('vtkMRMLFiberBundleNode'):
            for i in range(n.GetNumberOfDisplayNodes()):
                n.GetNthDisplayNode(i).SetVisibility(False)

    def refresh_tracts(self):
        """Show exactly the tracts in self.on on the chosen hemisphere. Brain surfaces are left alone."""
        self.hide_tracts()
        for k in self.on:
            self.tracts(self.GROUPS.get(k, [k]))
        slicer.app.layoutManager().threeDWidget(0).threeDView().forceRender()
        self._notify()

    def toggle_tract(self, key):
        if not self.scene_loaded():
            print('gbt2026: scene not loaded - press "Load scene" first')
            return self._notify()
        if key in self.on:
            self.on.remove(key)
        else:
            self.on.append(key)
        self.refresh_tracts()

    def clear_tracts(self):
        self.on = []
        self.refresh_tracts()

    def vis(self, names, on=True):
        m = self.models()
        for nm in names:
            if nm in m:
                m[nm].GetDisplayNode().SetVisibility(on)

    def tracts(self, keys, side=None):
        side = side or self.side
        sides = ['left', 'right'] if side == 'both' else [side]
        for k in keys:
            for sd in sides:
                self.vis(self.names(k, sd))

    def surf(self, kind, side='both'):
        nm = {'glass': 'FS glass', 'gyri': 'FS cortex', 'inflated': 'FS inflated'}[kind]
        self.vis([nm + ' left', nm + ' right'] if side == 'both' else [nm + ' ' + side])

    def apply_surface(self):
        """Show the chosen brain surface on the chosen hemisphere(s)."""
        for nm, n in self.models().items():
            if nm.startswith('FS ') and n.GetDisplayNode():
                n.GetDisplayNode().SetVisibility(False)
        if self.surface:
            self.surf(self.surface, self.side)
        slicer.app.layoutManager().threeDWidget(0).threeDView().forceRender()

    def set_surface(self, kind):
        """Surface buttons: one brain surface at a time; pressing the active one switches it off."""
        if not self.scene_loaded():
            print('gbt2026: scene not loaded - press "Load scene" first')
            return self._notify()
        self.surface = None if self.surface == kind else kind
        self.apply_surface()
        self._notify()

    def planes(self, on):
        self.planes_on = on
        for n in slicer.util.getNodesByClass('vtkMRMLSliceNode'):
            n.SetSliceVisible(on)

    def frame(self, on):
        for n in slicer.util.getNodesByClass('vtkMRMLViewNode'):
            n.SetBoxVisible(on)
            n.SetAxisLabelsVisible(on)

    def look(self, d):
        a = {'left': ctk.ctkAxesWidget.Left, 'right': ctk.ctkAxesWidget.Right, 'front': ctk.ctkAxesWidget.Anterior,
             'back': ctk.ctkAxesWidget.Posterior, 'top': ctk.ctkAxesWidget.Superior,
             'bottom': ctk.ctkAxesWidget.Inferior}[d]
        v = slicer.app.layoutManager().threeDWidget(0).threeDView()
        v.lookFromViewAxis(a)
        v.resetFocalPoint()
        v.forceRender()

    def spin(self, on):
        self.spinning = on
        for n in slicer.util.getNodesByClass('vtkMRMLViewNode'):
            n.SetAnimationMode(n.Spin if on else n.Off)
            n.SetSpinDegrees(1.5)
            n.SetAnimationMs(30)

    def toggle_spin(self):
        self.spin(not self.spinning)

    T1 = 'SPL_MRI'      # single-subject T1 shown by the T1 button (the ORG population-mean T1 is not used)

    def toggle_planes(self):
        self.planes(not self.planes_on)

    def toggle_t1(self):
        """Show / hide the T1 slice planes in the 3D view (always the subject T1)."""
        on = not self.planes_on
        if on:
            try:
                vid = slicer.util.getNode(self.T1).GetID()
                for c in slicer.util.getNodesByClass('vtkMRMLSliceCompositeNode'):
                    c.SetBackgroundVolumeID(vid)
            except Exception as e:
                print('gbt2026: T1 volume not found:', repr(e))
        self.planes(on)
        self._notify()

    def layout(self, k):
        L = slicer.vtkMRMLLayoutNode
        slicer.app.layoutManager().setLayout(
            {'3d': L.SlicerLayoutOneUp3DView, '4': L.SlicerLayoutFourUpView,
             'conv': L.SlicerLayoutConventionalView}[k])

    def glass_opacity(self, v):
        m = self.models()
        for sd in ('left', 'right'):
            if 'FS glass ' + sd in m:
                m['FS glass ' + sd].GetDisplayNode().SetOpacity(v)

    def gyri_hl(self, on=True):
        sn = slicer.util.getNode('SPL cortex')
        seg = sn.GetSegmentation()
        d = sn.GetDisplayNode()
        for i in range(seg.GetNumberOfSegments()):
            nm = seg.GetNthSegment(i).GetName()
            d.SetSegmentVisibility(seg.GetNthSegmentID(i), on and nm.startswith(('supramarginal', 'angular')))
        d.SetVisibility(True)
        d.SetVisibility3D(on)
        d.SetOpacity3D(0.7)

    # ---- scenes ---------------------------------------------------------
    def scene(self, name, side=None):
        if not self.scene_loaded():
            print('gbt2026: scene not loaded - press "Load scene" first')
            self._notify()
            return
        if side:
            self.side = side
        self.cur = name
        self.on = []
        self.surface = None
        self.hide_all()
        self.planes(False)
        self.frame(False)
        self.spin(False)
        allt = ['slf', 'arcuate', 'ifof', 'ilf', 'splenium']
        if name == 'wow':
            self.surf('glass'); self.tracts(allt)
        elif name == 'glass':
            self.surf('glass')
        elif name == 'gyri':
            self.surf('gyri')
        elif name == 'inflated':
            self.surf('inflated')
        elif name == 'angular':
            self.surf('glass'); self.gyri_hl(True)
        elif name == 'lang':
            self.surf('glass'); self.tracts(['arcuate', 'ifof', 'ilf'])
        elif name == 'visual':
            self.surf('glass'); self.tracts(['optic', 'meyer'])
        elif name == 'tracts':
            self.tracts(allt)
        elif name == 'full':
            self.surf('glass'); self.tracts(allt + ['optic', 'meyer'], 'both'); self.planes(True)
        elif name == 'sagittal':
            # composite, not an anatomical atlas entity: IFOF + ILF + optic radiation
            self.surf('glass'); self.tracts(['ifof', 'ilf', 'optic'])
        elif name in self.TR or name in ('splenium', 'tapetum'):
            self.tracts([name])
        slicer.app.layoutManager().threeDWidget(0).threeDView().forceRender()
        self._notify()

    def setside(self, s):
        self.side = s
        if self.surface:
            self.apply_surface()
        if self.on:
            self.refresh_tracts()
        elif self.cur and not self.surface:
            self.scene(self.cur)
        else:
            self._notify()

    def next(self, step=1):
        self.i = (self.i + step) % len(self.SEQ)
        self.scene(self.SEQ[self.i])
        self.look('left')

    def back(self):
        self.next(-1)

    def reset(self):
        self.layout('conv')
        self.side = 'left'
        self.i = -1
        self.scene('wow')
        self.look('left')

    # ---- one entry point for every kind of control ---------------------
    def do(self, action):
        """Run an action word such as 'scene:wow', 'look:left' or 'flow:next' (see gbt/layout.py)."""
        kind, _, arg = action.partition(':')
        if kind == 'load':
            self.load_scene()
        elif kind == 'reload':
            self.reload_scene()
        elif kind == 'scene':
            self.scene(arg)
        elif kind == 'surface':
            self.set_surface(arg)
        elif kind == 'tract':
            self.clear_tracts() if arg == 'clear' else self.toggle_tract(arg)
        elif kind == 'side':
            self.setside(arg)
        elif kind == 'look':
            self.look(arg)
        elif kind == 'view' and arg == 'reset':
            self.look('left')            # straight side view, re-centred and re-zoomed
        elif kind == 'layout':
            self.layout(arg)
        elif kind == 'flow':
            {'next': self.next, 'back': self.back, 'reset': self.reset}[arg]()
        elif kind == 'toggle':
            {'spin': self.toggle_spin, 'planes': self.toggle_planes, 't1': self.toggle_t1}[arg]()
        else:
            raise ValueError('unknown action: %r' % action)


Demo = Controller   # old name, kept so existing code and voice/MCP commands keep working
