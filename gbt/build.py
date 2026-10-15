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


def add_tube_model(name, streams, color, opacity=1.0):
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


def add_org_tract(mrb_path, label, color, per_side=150, opacity=1.0):
    """Build '<label> (left)' and '<label> (right)' from one ORG tract file. Returns a summary."""
    streams = read_org_streamlines(mrb_path)
    left, right = split_sides(streams)
    summary = {'file': os.path.basename(mrb_path), 'streamlines': len(streams), 'left': len(left), 'right': len(right)}
    for side, group in (('left', left), ('right', right)):
        if group:
            add_tube_model('%s (%s)' % (label, side), sample(group, per_side), color, opacity)
    return summary
