"""Scene controller. Shows and hides the models that already live in the loaded Slicer scene."""
import os

import ctk
import slicer
import vtk  # noqa: F401  (kept: some scene operations rely on it being imported)


class Controller:
    TR = {'slf': ['SLF I', 'SLF II', 'SLF III'], 'arcuate': ['Arcuate'], 'ifof': ['IFOF'], 'ilf': ['ILF'],
          'optic': ['Optic radiation'], 'meyer': ["Meyer's loop"]}
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
        slicer.app.processEvents()
        ok = slicer.util.loadScene(path)
        print('gbt2026: scene', 'loaded' if ok else 'FAILED to load', path)
        self._notify()
        return bool(ok)

    def status(self):
        if not self.scene_loaded():
            return 'Scene not loaded'
        return 'Showing: %s (%s)' % (self.cur or '-', self.side)

    # ---- name tables ---------------------------------------------------
    def names(self, key, side):
        if key == 'splenium':
            return ['Splenium (CC7)']
        out = []
        for b in self.TR[key]:
            out.append(b + (' (clean)' if side == 'left' else ' (right)') if key == 'slf' else b + ' (%s)' % side)
        return out

    # ---- visibility ----------------------------------------------------
    def hide_all(self):
        for nm, n in self.models().items():
            if nm.startswith(('SLF', 'Arcuate', 'IFOF', 'ILF', 'Splen', 'FS ', 'Optic', "Meyer")) and n.GetDisplayNode():
                n.GetDisplayNode().SetVisibility(False)
        for n in slicer.util.getNodesByClass('vtkMRMLFiberBundleNode'):
            for i in range(n.GetNumberOfDisplayNodes()):
                n.GetNthDisplayNode(i).SetVisibility(False)
        try:
            slicer.util.getNode('SPL cortex').GetDisplayNode().SetVisibility3D(False)
        except Exception:
            pass

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
                if k == 'splenium' and sd == 'right':
                    continue
                self.vis(self.names(k, sd))

    def surf(self, kind):
        nm = {'glass': 'FS glass', 'gyri': 'FS cortex', 'inflated': 'FS inflated'}[kind]
        self.vis([nm + ' left', nm + ' right'])

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

    def toggle_planes(self):
        self.planes(not self.planes_on)

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
        elif name in self.TR or name == 'splenium':
            self.tracts([name])
        slicer.app.layoutManager().threeDWidget(0).threeDView().forceRender()
        self._notify()

    def setside(self, s):
        self.side = s
        if self.cur:
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


Demo = Controller   # old name, kept so existing code and voice/MCP commands keep working
