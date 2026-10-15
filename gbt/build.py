"""Scene-building helpers (run inside 3D Slicer, not needed at presentation time).

They add new tract models to the scene in the same style as the existing ones:
six-sided tubes, radius 0.4 mm, a solid colour, hidden until a scene shows them.
Source tracts are the ORG atlas clusters (.vtk inside each T_*.mrb) or HCP1065 streamlines.
"""
import os
import zipfile

import numpy as np
import slicer
import vtk
from vtk.util.numpy_support import vtk_to_numpy

TUBE_RADIUS = 0.4
TUBE_SIDES = 6


def read_org_streamlines(mrb_path):
    """All streamlines of one ORG tract file (T_*.mrb) as a list of (n,3) arrays, scene RAS mm."""
    streams = []
    tmp = os.path.join(slicer.app.temporaryPath, 'gbt_cluster.vtk')
    with zipfile.ZipFile(mrb_path) as z:
        for name in sorted(z.namelist()):
            if '/Data/' in name and name.endswith('.vtk'):
                with open(tmp, 'wb') as f:
                    f.write(z.read(name))
                r = vtk.vtkPolyDataReader()
                r.SetFileName(tmp)
                r.Update()
                streams += polydata_streamlines(r.GetOutput())
    return streams


def polydata_streamlines(pd):
    lines = pd.GetLines()
    off = vtk_to_numpy(lines.GetOffsetsArray())
    con = vtk_to_numpy(lines.GetConnectivityArray())
    pts = vtk_to_numpy(pd.GetPoints().GetData()).astype(float)
    return [pts[con[off[i]:off[i + 1]]] for i in range(len(off) - 1)]


def split_sides(streams, min_abs_x=3.0):
    """Left/right by the sign of each streamline's mean x. Streamlines hugging the midline are dropped."""
    left, right = [], []
    for s in streams:
        mx = s[:, 0].mean()
        if mx <= -min_abs_x:
            left.append(s)
        elif mx >= min_abs_x:
            right.append(s)
    return left, right


def sample(streams, n, seed=0):
    if len(streams) <= n:
        return list(streams)
    idx = np.random.RandomState(seed).choice(len(streams), n, replace=False)
    return [streams[i] for i in sorted(idx)]


def streams_to_polydata(streams):
    pts = vtk.vtkPoints()
    cells = vtk.vtkCellArray()
    k = 0
    for s in streams:
        cells.InsertNextCell(len(s))
        for p in s:
            pts.InsertNextPoint(float(p[0]), float(p[1]), float(p[2]))
            cells.InsertCellPoint(k)
            k += 1
    pd = vtk.vtkPolyData()
    pd.SetPoints(pts)
    pd.SetLines(cells)
    return pd


def add_tube_model(name, streams, color, opacity=0.15):
    """Replace/add a hidden tube model called `name` built from streamlines."""
    try:
        slicer.mrmlScene.RemoveNode(slicer.util.getNode(name))
    except Exception:
        pass
    tube = vtk.vtkTubeFilter()
    tube.SetInputData(streams_to_polydata(streams))
    tube.SetRadius(TUBE_RADIUS)
    tube.SetNumberOfSides(TUBE_SIDES)
    tube.CappingOff()
    tube.Update()
    out = vtk.vtkPolyData()
    out.DeepCopy(tube.GetOutput())
    node = slicer.modules.models.logic().AddModel(out)
    node.SetName(name)
    d = node.GetDisplayNode()
    d.SetColor(*color)
    d.SetOpacity(opacity)
    d.SetAmbient(0.3)
    d.SetDiffuse(0.75)
    d.SetSpecular(0.35)
    d.SetScalarVisibility(False)
    d.SetVisibility(False)
    d.SetSliceIntersectionVisibility(False)
    return node


def add_org_tract(mrb_path, label, color, per_side=150, opacity=0.15):
    """Build '<label> (left)' and '<label> (right)' from one ORG tract file. Returns a summary."""
    streams = read_org_streamlines(mrb_path)
    left, right = split_sides(streams)
    summary = {'file': os.path.basename(mrb_path), 'streamlines': len(streams), 'left': len(left), 'right': len(right)}
    for side, group in (('left', left), ('right', right)):
        if group:
            add_tube_model('%s (%s)' % (label, side), sample(group, per_side), color, opacity)
    return summary


# ---- SPL atlas deep structures ------------------------------------------------------
SPL_MODELS = r'data\SPL_Atlas\extracted\spl_pnl_brain_atlas_2007\03-models'
SPL_GROUPS = {
    'Ventricles': [('lateral_ventricle_L', 'left', (0.3, 0.5, 1.0)), ('lateral_ventricle_R', 'right', (0.3, 0.5, 1.0)),
                   ('third_ventricle', 'mid', (0.3, 0.5, 1.0)), ('fourth_ventricle', 'mid', (0.3, 0.5, 1.0))],
    'Basal ganglia': [('caudate_nucleus_L', 'left', (0.95, 0.6, 0.2)), ('caudate_nucleus_R', 'right', (0.95, 0.6, 0.2)),
                      ('putamen_L', 'left', (0.85, 0.3, 0.5)), ('putamen_R', 'right', (0.85, 0.3, 0.5)),
                      ('globus_pallidus_L', 'left', (0.2, 0.75, 0.6)), ('globus_pallidus_R', 'right', (0.2, 0.75, 0.6))],
    'Brainstem': [('midbrain', 'mid', (0.8, 0.7, 0.55)), ('pons', 'mid', (0.75, 0.65, 0.5)),
                  ('medulla_oblongata', 'mid', (0.7, 0.6, 0.45))],
}


def add_spl_structures(repo_root, opacity=0.6):
    """Load SPL atlas deep structures as hidden models named '<Group>: <structure> (left|right|mid)'.

    The SPL .vtk files are in RAS; Slicer reads .vtk as LPS, so x and y are negated after loading.
    They are parented to SPL_to_ORG_affine like the SPL MRI and the SPL cortex segmentation.
    """
    tf = slicer.util.getNode('SPL_to_ORG_affine')
    made = []
    for group, items in SPL_GROUPS.items():
        for fname, side, color in items:
            base = fname[:-2] if fname.endswith(('_L', '_R')) else fname
            name = '%s: %s (%s)' % (group, base, side)
            try:
                slicer.mrmlScene.RemoveNode(slicer.util.getNode(name))
            except Exception:
                pass
            node = slicer.util.loadModel(os.path.join(repo_root, SPL_MODELS, fname + '.vtk'))
            node.SetName(name)
            pts = node.GetPolyData().GetPoints()
            for i in range(pts.GetNumberOfPoints()):
                x, y, z = pts.GetPoint(i)
                pts.SetPoint(i, -x, -y, z)
            pts.Modified()
            node.GetPolyData().GetPointData().SetNormals(None)
            node.GetPolyData().Modified()
            node.SetAndObserveTransformNodeID(tf.GetID())
            d = node.GetDisplayNode()
            d.SetColor(*color)
            d.SetOpacity(opacity)
            d.SetAmbient(0.3)
            d.SetDiffuse(0.75)
            d.SetSpecular(0.35)
            d.SetScalarVisibility(False)
            d.SetSliceIntersectionVisibility(False)
            d.SetVisibility(False)
            made.append(name)
    return made


def fit_freesurfer(scale=1.076, shift=(-0.1, 0.8, 0.2)):
    """Parent all 'FS ...' surface models to a scaling transform 'FS_to_ORG_fit'.

    The fsaverage pial surface is about 7.6 % smaller than the ORG population-mean brain; matching the
    brain extent of the ORG T1 (x -65..66, y -104..71, top z 70 mm) gives a uniform scale of 1.076.
    """
    try:
        slicer.mrmlScene.RemoveNode(slicer.util.getNode('FS_to_ORG_fit'))
    except Exception:
        pass
    tf = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLLinearTransformNode', 'FS_to_ORG_fit')
    m = vtk.vtkMatrix4x4()
    for i in range(3):
        m.SetElement(i, i, scale)
        m.SetElement(i, 3, shift[i])
    tf.SetMatrixTransformToParent(m)
    for n in slicer.util.getNodesByClass('vtkMRMLModelNode'):
        if n.GetName().startswith('FS '):
            n.SetAndObserveTransformNodeID(tf.GetID())
    return tf


# Tract colours: the first group are the long-standing course colours, the rest were chosen to be
# clearly different from them and from each other (all models of a tract share its colour, left and right).
TRACT_COLORS = {
    'Arcuate': (1.0, 0.55, 0.0), 'IFOF': (0.0, 0.85, 0.85), 'ILF': (1.0, 0.9, 0.1),
    'Splenium': (1.0, 0.15, 0.15), 'Optic radiation': (0.6, 1.0, 0.2), "Meyer's loop": (1.0, 0.45, 0.65),
    'SLF I': (0.15, 0.8, 0.15), 'SLF II': (0.1, 0.1, 0.95), 'SLF III': (0.9, 0.3, 0.9),
    'Uncinate': (0.55, 0.25, 0.85), 'MdLF': (0.6, 0.38, 0.18), 'VOF': (1.0, 0.6, 0.55),
    'External capsule': (0.0, 0.55, 0.45), 'Corticospinal': (0.95, 0.95, 0.95),
    'Frontostriatal': (0.55, 0.05, 0.2), 'Internal capsule': (0.6, 0.6, 0.68),
    'Corona radiata': (0.45, 0.75, 1.0), 'Tapetum': (0.5, 0.5, 0.0),
}


# ---- Tapetum (derived) --------------------------------------------------------------
def tapetum_segments(streams, vent_pts, dmin=1.5, dmax=7.0, minlen=8):
    """Parts of splenial streamlines that run in a thin shell lateral to a lateral ventricle.

    The tapetum is the sheet of splenium fibres lying against the ependyma on the roof and lateral
    wall of the atrium and the occipital/temporal horns. A streamline point is kept when it is
    outside the ventricle (>= dmin mm from the nearest ventricle vertex), within dmax mm of it, and
    not medial to that vertex (|x| >= |x_vertex| - 1). Consecutive kept points (no jump > 5 mm)
    form segments; short ones (< minlen points) are dropped.
    """
    from scipy.spatial import cKDTree
    tree = cKDTree(vent_pts)
    segs = []
    for s in streams:
        d, i = tree.query(s)
        ok = (d >= dmin) & (d <= dmax) & (np.abs(s[:, 0]) >= np.abs(vent_pts[i, 0]) - 1.0)
        cur = []
        for k in range(len(s)):
            if ok[k] and (not cur or np.linalg.norm(s[k] - s[k - 1]) < 5):
                cur.append(k)
            else:
                if len(cur) >= minlen:
                    segs.append(s[cur])
                cur = [k] if ok[k] else []
        if len(cur) >= minlen:
            segs.append(s[cur])
    return segs


def _world_points(node):
    pts = vtk_to_numpy(node.GetPolyData().GetPoints().GetData()).astype(float)
    tn = node.GetParentTransformNode()
    if tn is None:
        return pts
    g = vtk.vtkGeneralTransform()
    tn.GetTransformToWorld(g)
    return np.array([g.TransformPoint(p) for p in pts])


def add_tapetum(mrb_dir, per_side=250, color=(0.5, 0.5, 0.0), opacity=0.15):
    """Build 'Tapetum (left, derived)' / '(right, derived)' from ORG T_CC6+T_CC7 and the SPL
    lateral ventricle models (they must already be in the scene). Returns segment counts."""
    streams = []
    for t in ('T_CC6', 'T_CC7'):
        streams += read_org_streamlines(os.path.join(mrb_dir, t + '.mrb'))
    left, right = split_sides(streams)
    summary = {}
    for side, group in (('left', left), ('right', right)):
        vent = _world_points(slicer.util.getNode('Ventricles: lateral_ventricle (%s)' % side))
        segs = tapetum_segments(group, vent)
        summary[side] = len(segs)
        add_tube_model('Tapetum (%s, derived)' % side, sample(segs, per_side), color, opacity)
    return summary


# ---- Internal capsule parts (derived) -----------------------------------------------
IC_PARTS = {      # name: colour
    'anterior limb': (1.0, 0.25, 0.25), 'genu': (1.0, 0.8, 0.0), 'posterior limb': (0.25, 0.8, 0.25),
    'retrolenticular': (0.25, 0.5, 1.0), 'sublenticular': (0.8, 0.3, 0.9),
}
IC_POOL = ['T_PLIC', 'T_CST', 'T_CR-F', 'T_CR-P', 'T_TF', 'T_TP', 'T_TO']


def ic_classify(streams, lentiform_pts, dmax=6.0):
    """Assign whole projection streamlines to a part of the internal capsule.

    Not an atlas label: each streamline is placed by where it passes closest to the lentiform
    nucleus (putamen + globus pallidus). Streamlines that never come within dmax mm, or pass lateral
    to it, are dropped. Rules on that point (scene mm): z < -6 and -30 < y <= 2 sublenticular;
    y <= -22 retrolenticular; y <= 0 posterior limb; y <= 8 genu; otherwise anterior limb.
    """
    from scipy.spatial import cKDTree
    tree = cKDTree(lentiform_pts)
    parts = {k: [] for k in IC_PARTS}
    for s in streams:
        d, i = tree.query(s)
        k = int(np.argmin(d))
        if d[k] > dmax:
            continue
        p, v = s[k], lentiform_pts[i[k]]
        if abs(p[0]) > abs(v[0]) + 1.0:
            continue
        y, z = p[1], p[2]
        if z < -6 and -30 < y <= 2:
            nm = 'sublenticular'
        elif y <= -22:
            nm = 'retrolenticular'
        elif y <= 0:
            nm = 'posterior limb'
        elif y <= 8:
            nm = 'genu'
        else:
            nm = 'anterior limb'
        parts[nm].append(s)
    return parts


def add_internal_capsule(mrb_dir, per_side=80, opacity=0.15):
    """Build 'Internal capsule - <part> (left|right)' models. Needs the SPL basal ganglia in the scene."""
    streams = []
    for t in IC_POOL:
        streams += read_org_streamlines(os.path.join(mrb_dir, t + '.mrb'))
    left, right = split_sides(streams)
    summary = {}
    for side, group in (('left', left), ('right', right)):
        len_pts = np.vstack([_world_points(slicer.util.getNode('Basal ganglia: %s (%s)' % (k, side)))
                             for k in ('putamen', 'globus_pallidus')])
        parts = ic_classify(group, len_pts)
        for nm, segs in parts.items():
            summary['%s %s' % (nm, side)] = len(segs)
            if segs:
                add_tube_model('Internal capsule - %s (%s)' % (nm, side), sample(segs, per_side), IC_PARTS[nm], opacity)
    return summary
