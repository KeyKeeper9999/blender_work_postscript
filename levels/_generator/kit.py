"""Shared building kit for the v2 interiors (corridors + apartments). Headless Blender 5.2 / bpy.
Wall frames: wf = (axis, c, s): the wall plane is axis=c ('y': y=c, u runs along x), s = +1/-1 points into the room.
F(wf)(u, z, w) -> world point, w = distance into the room."""
import os, sys, math, random, bpy, bmesh
from collections import defaultdict
from mathutils import Vector, Matrix
HERE = os.path.dirname(os.path.abspath(__file__)); LEVELS = os.path.dirname(HERE); REPO = os.path.dirname(LEVELS)
sys.path.insert(0, os.path.join(REPO, '.claude/skills/blender-keytools'))
import keytools as kt
TEXD = os.path.join(LEVELS, 'textures') + '/'
H = 2.6
ST = dict(root=None, cols={}, mats={}, MS={}, warn=[], occ=defaultdict(list), out=None)

def start(out, rootname):
    bpy.ops.wm.read_factory_settings(use_empty=True); ST['out'] = out
    bpy.ops.wm.save_as_mainfile(filepath=out)
    r = bpy.data.collections.new(rootname); bpy.context.scene.collection.children.link(r); ST['root'] = r
def col(n):
    if n not in ST['cols']:
        c = bpy.data.collections.new(n); ST['root'].children.link(c); ST['cols'][n] = c
    return ST['cols'][n]

# ---------------------------------------------------------------- materials
def mat(name, tex=None, color=(.5, .5, .5), emit=None, alpha=False, rough=1.0, mode='box', tile=None):
    """mode: 'box' (world box UV, tile=(m,m)), 'wall' (u along wall / 4 m, v = z / 2.6), 'explicit' (UVs set by hand)"""
    if name in ST['mats']: return ST['mats'][name]
    m = bpy.data.materials.new(name); nt = m.node_tree; b = nt.nodes.get('Principled BSDF')
    b.inputs['Roughness'].default_value = rough; b.inputs['Specular IOR Level'].default_value = .1 if rough > .5 else .5
    b.inputs['Base Color'].default_value = (*color, 1)
    ms = ('box', 1.0, 1.0)
    if tex:
        im = bpy.data.images.get(tex + '.png') or bpy.data.images.load(TEXD + tex + '.png'); im.filepath = bpy.path.relpath(im.filepath)
        n = nt.nodes.new('ShaderNodeTexImage'); n.image = im; n.interpolation = 'Closest'; n.location = (-400, 200)
        nt.links.new(n.outputs['Color'], b.inputs['Base Color'])
        if alpha: nt.links.new(n.outputs['Alpha'], b.inputs['Alpha'])
        w, h = im.size; ms = ('box', *(tile or (w / 64.0, h / 64.0)))
    if mode == 'wall': ms = ('wall',)
    if mode == 'explicit': ms = None
    if emit: b.inputs['Emission Color'].default_value = (*emit[0], 1); b.inputs['Emission Strength'].default_value = emit[1]
    ST['MS'][name] = ms; ST['mats'][name] = m; return m
def tm(tex, tile=None): return mat('M_' + tex[2:], tex, tile=tile)
def wm(tex): return mat('M_' + tex[2:], tex, mode='wall')
def xm(tex, alpha=False, rough=1.0): return mat('M_' + tex[2:], tex, mode='explicit', alpha=alpha, rough=rough)
def dm(tex, rough=1.0): return mat('M_' + tex[2:], tex, mode='explicit', alpha=True, rough=rough)
def glow(name, c, s): return mat(name, color=c, emit=(c, s), rough=.3)
def flat(name, c, rough=.8): return mat(name, color=c, rough=rough)

# ---------------------------------------------------------------- geometry
def F(wf):
    if callable(wf): return wf
    a, c, s = wf
    return (lambda u, z, w: (u, c + s * w, z)) if a == 'y' else (lambda u, z, w: (c + s * w, u, z))
def nrm(wf): a, c, s = wf; return Vector((0, s, 0)) if a == 'y' else Vector((s, 0, 0))
def mirrored(f):
    o = Vector(f(0, 0, 0)); ud = Vector(f(1, 0, 0)) - o; n = Vector(f(0, 0, 1)) - o
    return ud.dot((-n).cross(Vector((0, 0, 1)))) < 0
def occupy(wf, u0, u1, z0, z1, name):
    for a0, a1, b0, b1, n in ST['occ'][wf]:
        if u0 < a1 - 1e-4 and a0 < u1 - 1e-4 and z0 < b1 - 1e-4 and b0 < z1 - 1e-4: ST['warn'].append(f'overlap on {wf}: {name} x {n}')
    ST['occ'][wf].append((u0, u1, z0, z1, name))
def is_free(wf, u0, u1, z0, z1):
    return not any(u0 < a1 and a0 < u1 and z0 < b1 and b0 < z1 for a0, a1, b0, b1, n in ST['occ'][wf])
def prism(bm, f, pts, a0, a1, mi=0):
    f = F(f); a = [bm.verts.new(f(p, q, a0)) for p, q in pts]; b = [bm.verts.new(f(p, q, a1)) for p, q in pts]
    n = len(pts); caps = [bm.faces.new(a), bm.faces.new(b[::-1])]
    sides = [bm.faces.new((a[i], a[(i + 1) % n], b[(i + 1) % n], b[i])) for i in range(n)]
    for x in caps + sides: x.material_index = mi
    if n > 4:
        for x in caps: x.normal_update()
        bmesh.ops.triangulate(bm, faces=caps, ngon_method='EAR_CLIP')
    return caps
def lbox(bm, f, u0, u1, z0, z1, w0, w1, mi=0): return prism(bm, f, [(u0, z0), (u1, z0), (u1, z1), (u0, z1)], w0, w1, mi)[1]
def wbox(bm, lo, hi, mi=0): return lbox(bm, lambda u, z, w: (u, w, z), lo[0], hi[0], lo[2], hi[2], lo[1], hi[1], mi)
def fbox(bm, f, a, b, mi=0):
    p, q = Vector(F(f)(*a)), Vector(F(f)(*b))
    return wbox(bm, [min(p[i], q[i]) for i in range(3)], [max(p[i], q[i]) for i in range(3)], mi)
def hexa(bm, fp, r0, r1, r2, mi=0):
    vs = [bm.verts.new(fp(a, b, c)) for c in r2 for b in r1 for a in r0]
    for q in ((0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)):
        bm.faces.new([vs[i] for i in q]).material_index = mi
def cyl(bm, p0, p1, r, seg=8, mi=0, r1=None):
    p0, p1 = Vector(p0), Vector(p1); d = p1 - p0
    res = bmesh.ops.create_cone(bm, cap_ends=True, segments=seg, radius1=r, radius2=r if r1 is None else r1, depth=d.length)
    mtx = Matrix.Translation((p0 + p1) / 2) @ Vector((0, 0, 1)).rotation_difference(d.normalized()).to_matrix().to_4x4()
    for v in res['verts']: v.co = mtx @ v.co
    fs = {x for v in res['verts'] for x in v.link_faces}
    for x in fs: x.material_index = mi
    return fs
def sphere(bm, c, r, sz=1.0, mi=0, u=8, v=5, sx=1.0, sy=1.0):
    res = bmesh.ops.create_uvsphere(bm, u_segments=u, v_segments=v, radius=r)
    for x in res['verts']: x.co = Vector((c[0] + x.co.x * sx, c[1] + x.co.y * sy, c[2] + x.co.z * sz))
    for x in {x for v_ in res['verts'] for x in v_.link_faces}: x.material_index = mi
def quad(bm, pts, mi=0):
    f = bm.faces.new([bm.verts.new(p) for p in pts]); f.material_index = mi; return f
def uvquad(bm, pts, mi, uvr=(0, 0, 1, 1)):
    f = quad(bm, pts, mi); uvl = bm.loops.layers.uv.get('UVMap') or bm.loops.layers.uv.new('UVMap')
    for l, uv in zip(f.loops, ((uvr[0], uvr[1]), (uvr[2], uvr[1]), (uvr[2], uvr[3]), (uvr[0], uvr[3]))): l[uvl].uv = uv
    return f
def set_uv(bm, face, f, u0, u1, z0, z1, cell=(0, 0, 1, 1)):
    f = F(f); o = Vector(f(0, 0, 0)); ud = Vector(f(1, 0, 0)) - o; flip = mirrored(f)
    uvl = bm.loops.layers.uv.get('UVMap') or bm.loops.layers.uv.new('UVMap')
    for lp in face.loops:
        co = lp.vert.co; s = ((co - o).dot(ud) - u0) / (u1 - u0); t = (co.z - z0) / (z1 - z0)
        if flip: s = 1 - s
        lp[uvl].uv = (cell[0] + s * (cell[2] - cell[0]), cell[1] + t * (cell[3] - cell[1]))
def wall_decal(bm, wf, u0, u1, z0, z1, w, mi, cell=(0, 0, 1, 1)):
    f = F(wf); fc = quad(bm, [f(u0, z0, w), f(u1, z0, w), f(u1, z1, w), f(u0, z1, w)], mi)
    fc.normal_update()
    if fc.normal.dot(nrm(wf)) < 0: fc.normal_flip()
    set_uv(bm, fc, wf, u0, u1, z0, z1, cell); return fc
def floor_decal(bm, x, y, z, sx, sy, rot, mi, uvr=(0, 0, 1, 1), down=False):
    c, s = math.cos(math.radians(rot)), math.sin(math.radians(rot)); uvl = bm.loops.layers.uv.get('UVMap') or bm.loops.layers.uv.new('UVMap')
    cs = [(-sx / 2, -sy / 2), (sx / 2, -sy / 2), (sx / 2, sy / 2), (-sx / 2, sy / 2)]; uvs = [(uvr[0], uvr[1]), (uvr[2], uvr[1]), (uvr[2], uvr[3]), (uvr[0], uvr[3])]
    if down: cs, uvs = cs[::-1], uvs[::-1]
    f = quad(bm, [(x + a * c - b * s, y + a * s + b * c, z) for a, b in cs], mi)
    for l, uv in zip(f.loops, uvs): l[uvl].uv = uv
    return f
def fix_normals(bm):
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:]); bm.faces.index_update(); seen = set()
    for f0 in bm.faces:
        if f0.index in seen: continue
        isl, stack = [], [f0]; seen.add(f0.index)
        while stack:
            f = stack.pop(); isl.append(f)
            for e in f.edges:
                for g in e.link_faces:
                    if g.index not in seen: seen.add(g.index); stack.append(g)
        if any(len(e.link_faces) != 2 for f in isl for e in f.edges): continue
        c = sum((v.co for f in isl for v in f.verts), Vector()) / sum(len(f.verts) for f in isl); vol = 0.0
        for f in isl:
            v0 = f.verts[0].co - c
            for i in range(1, len(f.verts) - 1): vol += v0.dot((f.verts[i].co - c).cross(f.verts[i + 1].co - c))
        if vol < 0: bmesh.ops.reverse_faces(bm, faces=isl)
def make(name, bm, cname, mats, origin=None, loc=None, rot=None, recalc=True):
    if origin is not None:
        origin = Vector(origin)
        for v in bm.verts: v.co -= origin
    if recalc: fix_normals(bm)
    if not bm.loops.layers.uv.get('UVMap'): bm.loops.layers.uv.new('UVMap')
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    for m in mats: me.materials.append(m)
    o = bpy.data.objects.new(name, me)
    o.location = origin if origin is not None else (loc or (0, 0, 0))
    if rot: o.rotation_euler = rot
    col(cname).objects.link(o); return o
def boolean_cut(o, cutters):
    sc = bpy.context.scene; tmp = bpy.data.collections.new('_cut'); sc.collection.children.link(tmp)
    for i, bm in enumerate(cutters):
        me = bpy.data.meshes.new('_c'); bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:]); bm.to_mesh(me); bm.free()
        tmp.objects.link(bpy.data.objects.new('_c%d' % i, me))
    md = o.modifiers.new('cut', 'BOOLEAN'); md.operation = 'DIFFERENCE'; md.operand_type = 'COLLECTION'; md.collection = tmp; md.solver = 'EXACT'
    me = bpy.data.meshes.new_from_object(o.evaluated_get(bpy.context.evaluated_depsgraph_get()))
    old = o.data; o.modifiers.remove(md); o.data = me; me.name = o.name
    if not me.materials:
        for m in old.materials: me.materials.append(m)
    nones = [i for i, m in enumerate(me.materials) if m is None]
    for pl in me.polygons:
        if pl.material_index in nones: pl.material_index = 0
    for i in sorted(nones, reverse=True): me.materials.pop(index=i)
    bpy.data.meshes.remove(old)
    for x in list(tmp.objects): bpy.data.meshes.remove(x.data)
    bpy.data.collections.remove(tmp)
def bisect(bm, planes):
    for co, no in planes: bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=co, plane_no=no)
def cutter(wf, u0, u1, z0, z1, depth):
    bm = bmesh.new(); lbox(bm, wf, u0, u1, z0, z1, -depth, .2); return bm
def rot_into(wf, ang, hinge_low=True):
    """z-rotation for a leaf hinged at its low-u edge (or high-u edge) that opens into the room by |ang| degrees"""
    if not ang: return 0.0
    d0 = (Vector(F(wf)(1, 0, 0)) - Vector(F(wf)(0, 0, 0))) * (1 if hinge_low else -1); n = nrm(wf)
    for a in (abs(ang), -abs(ang)):
        if (Matrix.Rotation(math.radians(a), 3, 'Z') @ d0).dot(n) > 0: return math.radians(a)

# ---------------------------------------------------------------- rooms -> wall segments
def wall_segments(rooms):
    """inner wall runs of a union of rectangles: [(wf, u0, u1)]"""
    segs = []
    for r in rooms:
        x0, y0, x1, y1 = r
        for wf, a, b, line, other in ((('y', y0, 1), x0, x1, y0, 3), (('y', y1, -1), x0, x1, y1, 1), (('x', x0, 1), y0, y1, x0, 2), (('x', x1, -1), y0, y1, x1, 0)):
            cuts = []
            for q in rooms:
                if q is r or abs(q[other] - line) > 1e-6: continue
                lo, hi = (q[0], q[2]) if wf[0] == 'y' else (q[1], q[3])
                if min(b, hi) > max(a, lo): cuts.append((max(a, lo), min(b, hi)))
            pts = [a]
            for c0, c1 in sorted(cuts): pts += [c0, c1]
            pts.append(b)
            for i in range(0, len(pts), 2):
                if pts[i + 1] - pts[i] > .05: segs.append((wf, pts[i], pts[i + 1]))
    segs.sort(key=lambda s: (s[0], s[1])); out = []
    for sg in segs:                                       # merge collinear runs that touch
        if out and out[-1][0] == sg[0] and abs(out[-1][2] - sg[1]) < 1e-6: out[-1] = (sg[0], out[-1][1], sg[2])
        else: out.append(sg)
    return out
def free_spans(wf, a, b, z0, z1, pad=0.0):
    occ = sorted((max(a, a0 - pad), min(b, a1 + pad)) for a0, a1, b0, b1, n in ST['occ'][wf] if b0 < z1 and z0 < b1 and a1 + pad > a and a0 - pad < b)
    out, cur = [], a
    for o0, o1 in occ:
        if o0 > cur: out.append((cur, o0))
        cur = max(cur, o1)
    if b > cur: out.append((cur, b))
    return [(x, y) for x, y in out if y - x > .05]

# ---------------------------------------------------------------- lights, markers, finishing
def light(n, loc, e, c, kind='POINT', size=.05):
    d = bpy.data.lights.new(n, kind); d.energy = e; d.color = c; d.shadow_soft_size = size
    o = bpy.data.objects.new(n, d); o.location = loc; col('Lights').objects.link(o); return o
def marker(n, loc, rz=0):
    e = bpy.data.objects.new(n, None); e.empty_display_type = 'ARROWS'; e.location = loc; e.rotation_euler = (0, 0, math.radians(rz)); col('Markers').objects.link(e)
def uv_world(o, wall_len=4.0):
    mw = o.matrix_world; nm = mw.to_3x3().inverted_safe().transposed()
    bm = bmesh.new(); bm.from_mesh(o.data); uvl = bm.loops.layers.uv.get('UVMap') or bm.loops.layers.uv.new('UVMap')
    for fc in bm.faces:
        s = ST['MS'].get(o.data.materials[fc.material_index].name, ('box', 1, 1)) if o.data.materials else ('box', 1, 1)
        if s is None: continue
        n = (nm @ fc.normal).normalized(); ax = max(range(3), key=lambda i: abs(n[i])); sg = 1 if n[ax] >= 0 else -1
        for lp in fc.loops:
            c = mw @ lp.vert.co
            u, v = (sg * c.y, c.z) if ax == 0 else ((-sg * c.x, c.z) if ax == 1 else (c.x, sg * c.y))
            if s[0] == 'wall': lp[uvl].uv = (u / wall_len, v / H if ax != 2 else v / wall_len)
            else: lp[uvl].uv = (u / s[1], v / s[2])
    bm.to_mesh(o.data); bm.free()
def finish(anchors=(), ignore=(), ground=0.0):
    root = ST['root']; bpy.context.view_layer.update()
    meshes = [o for o in root.all_objects if o.type == 'MESH']
    for o in meshes: uv_world(o)
    ign = [o.name for o in meshes if o.name.startswith('Decal_') or o.name.endswith('_Decals')] + list(ignore)
    print(kt.check_all([o.name for o in meshes], ground=ground, anchors=list(anchors), ignore=ign))
    print('WARN', ST['warn'] or 'none')
    print('tris', sum(len(p.vertices) - 2 for o in meshes for p in o.data.polygons), 'objects', len(meshes))
    bpy.ops.wm.save_as_mainfile(filepath=ST['out'], relative_remap=True); print('saved', ST['out'])
