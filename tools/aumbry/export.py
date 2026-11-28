"""Export the render meshes cached in a .3dm to a compact binary + JSON index for three.js."""
import json, struct, sys
import numpy as np, rhino3dm as r
src, out = sys.argv[1], sys.argv[2]
m = r.File3dm.Read(src)
groups = {}
for o in m.Objects:
    g = o.Geometry; a = o.Attributes
    layer = m.Layers[a.LayerIndex].Name
    meshes = []
    if isinstance(g, r.Extrusion):
        meshes = [g.GetMesh(r.MeshType.Any)]
    else:
        meshes = [f.GetMesh(r.MeshType.Any) for f in g.Faces]
    bb = g.GetBoundingBox(); ext = [bb.Max.X-bb.Min.X, bb.Max.Y-bb.Min.Y, bb.Max.Z-bb.Min.Z]
    grain = int(np.argmax(ext))
    for me in meshes:
        if me is None: continue
        me.Normals.ComputeNormals() if len(me.Normals) == 0 else None
        V = np.array([[p.X, p.Y, p.Z] for p in me.Vertices], np.float32)
        N = np.array([[n.X, n.Y, n.Z] for n in me.Normals], np.float32)
        # planar UVs in mm per face orientation, u along the part's grain (its longest side)
        dom = np.abs(N).argmax(1)
        T = np.zeros((len(V), 2), np.float32)
        for i in range(len(V)):
            ax = [a for a in range(3) if a != dom[i]]
            if grain in ax: u = grain; w = ax[0] if ax[1] == grain else ax[1]
            else: u, w = ax
            T[i] = (V[i, u], V[i, w])
        F = []
        for i in range(len(me.Faces)):
            f = me.Faces[i]
            F.append((f[0], f[1], f[2]))
            if f[2] != f[3]: F.append((f[0], f[2], f[3]))
        F = np.array(F, np.uint32)
        gr = groups.setdefault(layer, {'V': [], 'N': [], 'T': [], 'F': [], 'n': 0})
        gr['V'].append(V); gr['N'].append(N); gr['T'].append(T); gr['F'].append(F + gr['n']); gr['n'] += len(V)
index = {}; blob = bytearray()
for k, gr in groups.items():
    ent = {}
    for key in 'VNTF':
        arr = np.concatenate(gr[key]); arr = arr.astype(np.uint32 if key == 'F' else np.float32)
        ent[key] = [len(blob), arr.size]; blob += arr.tobytes()
    index[k] = ent
    print(k, gr['n'], 'verts', sum(len(f) for f in gr['F']), 'tris')
open(out + '.bin', 'wb').write(blob)
json.dump(index, open(out + '.json', 'w'))
