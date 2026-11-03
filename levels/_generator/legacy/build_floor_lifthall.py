import sys, math, bpy, bmesh
from mathutils import Vector, Matrix, Euler
REPO = '/home/user/blender_work_postscript'
sys.path.insert(0, REPO + '/.claude/skills/blender-keytools')
import keytools as kt
OUT = REPO + '/levels/Floor_LiftHall.blend'
TEXD = REPO + '/levels/textures/'

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
bpy.ops.wm.save_as_mainfile(filepath=OUT)

H, T, TE, TH = 2.6, 0.18, 0.35, 0.02          # ceiling, inner wall, end (outer) wall, threshold
CX, CY = 42.0, 2.0                             # corridor length / width
HX0, HX1, HY = 18.0, 24.0, 7.0                 # lift hall
Y0 = HY + T                                    # back face of the lift wall
root = bpy.data.collections.new('Floor_LiftHall'); sc.collection.children.link(root)
_cols = {}
def col(n):
    if n not in _cols:
        c = bpy.data.collections.new(n); root.children.link(c); _cols[n] = c
    return _cols[n]

# ---------------------------------------------------------------- materials
_mats, MS = {}, {}   # MS: material -> (m per tile u, v) for box UV, None = explicit UV
def mat(name, tex=None, color=(.5, .5, .5), emit=None, alpha=False, rough=1.0, tile=None, explicit=False):
    if name in _mats: return _mats[name]
    m = bpy.data.materials.new(name); nt = m.node_tree; b = nt.nodes.get('Principled BSDF')
    b.inputs['Roughness'].default_value = rough
    b.inputs['Specular IOR Level'].default_value = 0.1 if rough > .5 else 0.5
    b.inputs['Base Color'].default_value = (*color, 1)
    MS[name] = tile or (1.0, 1.0)
    if tex:
        im = bpy.data.images.get(tex + '.png') or bpy.data.images.load(TEXD + tex + '.png')
        im.filepath = bpy.path.relpath(im.filepath)
        n = nt.nodes.new('ShaderNodeTexImage'); n.image = im; n.interpolation = 'Closest'; n.location = (-400, 200)
        nt.links.new(n.outputs['Color'], b.inputs['Base Color'])
        if alpha: nt.links.new(n.outputs['Alpha'], b.inputs['Alpha'])
        w, h = im.size
        MS[name] = tile or (w / 64.0, h / 64.0)
    if explicit: MS[name] = None
    if emit:
        b.inputs['Emission Color'].default_value = (*emit[0], 1); b.inputs['Emission Strength'].default_value = emit[1]
    _mats[name] = m; return m
def tm(tex, tile=None):          # textured material named after its texture
    return mat('M_' + tex[2:], tex, tile=tile)

M = dict(
    handle=mat('M_Metal_Dark', color=(.10, .09, .08), rough=.6),
    brass=mat('M_Metal_Brass', color=(.45, .33, .12), rough=.5),
    plate=mat('M_NumberPlates', 'T_NumberPlates', explicit=True),
    number=mat('M_Decal_FloorNumber', 'T_FloorNumber_7', alpha=True, explicit=True),
    sign=mat('M_Sign_LiftBroken', 'T_Sign_LiftBroken', explicit=True),
    lamp=mat('M_Lamp_Glow', color=(1, .92, .75), emit=((1, .85, .6), 6.0)),
    deadglass=mat('M_Lamp_DeadGlass', color=(.55, .52, .46), rough=.4),
    plastic=mat('M_Plastic_Dark', color=(.05, .05, .05), rough=.7),
    wire=mat('M_Wire', color=(.07, .07, .07), rough=.8),
    btn=mat('M_Button_Red', color=(.8, .05, .03), emit=((1, .08, .03), 3.0)),
    btn_dead=mat('M_Button_Dead', color=(.25, .04, .03), rough=.6),
    btn_cream=mat('M_Plastic_Cream', color=(.75, .70, .58), rough=.6),
    btn_burnt=mat('M_Plastic_Burnt', color=(.03, .025, .02), rough=.9),
    cablight=mat('M_LiftCab_Light', color=(1, .95, .85), emit=((1, .93, .8), 4.0)),
    night=mat('M_Glass_Night', color=(.01, .015, .03), emit=((.02, .03, .06), 1.0), rough=.1),
    wired=mat('M_Glass_Wired', color=(.05, .07, .06), rough=.25),
    jar=mat('M_Glass_Jar', color=(.35, .42, .38), rough=.2),
    pot=mat('M_Clay_Pot', color=(.42, .18, .09)),
    stem=mat('M_Plant_Dead', color=(.18, .14, .08)),
    steel=mat('M_Metal_Grey', color=(.3, .3, .3), rough=.5),
)
W = {k: tm('T_' + k) for k in (
    'Wall_PaintGreen', 'Wall_PaintGreenStripe', 'Wall_PaintPeeling', 'Wall_PaintBlue', 'Wall_PaintBlueStripe',
    'Wall_Vagonka', 'Wall_Wallpaper', 'Whitewash', 'Plaster_Stained', 'Baseboard_Paint', 'Wood_Frame', 'Ceiling')}
FL = dict(hex=tm('T_Floor_MetlakhHex', tile=(1.6, 1.6)), terrazzo=tm('T_Floor_Terrazzo'),
          lino=tm('T_Floor_Linoleum', tile=(1.5, 1.5)), worn=tm('T_Floor_WornTiles'))
DM = {k: tm('T_Door_' + k) for k in ('DermatinBrown', 'DermatinBlack', 'DermatinRed', 'WoodBrown', 'WoodBeige',
                                    'WoodBlue', 'SteelBrown', 'SteelGrey', 'StairWood')}
P = {k: tm('T_' + k) for k in ('Planks', 'Partition_Wood', 'Partition_Door', 'Metal_Grille', 'LiftDoor_Metal',
                               'LiftCab_Wood', 'LiftCab_Floor', 'Shaft_Concrete', 'ElectricPanel', 'Radiator',
                               'Mailbox', 'FireCabinet', 'Chute_Hatch', 'Furniture_Wood', 'Chair_Wood', 'Sled_Wood',
                               'Cardboard', 'Plastic_Bag', 'Paper', 'Envelope', 'Carpet_Runner', 'Carpet_Rolled',
                               'Mat_Olive', 'Mat_Blue', 'Mat_Rubber', 'Boots', 'Bucket')}

# ---------------------------------------------------------------- geometry helpers
WALL = {
    'S': lambda u, z, w: (u, w, z),        'N': lambda u, z, w: (u, CY - w, z),
    'HW': lambda u, z, w: (HX0 + w, u, z), 'HE': lambda u, z, w: (HX1 - w, u, z),
    'HN': lambda u, z, w: (u, HY - w, z),  'EW': lambda u, z, w: (w, u, z),
    'EE': lambda u, z, w: (CX - w, u, z),
}
THICK = dict(S=T, N=T, HW=T, HE=T, HN=T, EW=TE, EE=TE)
def F(wall): return WALL[wall] if isinstance(wall, str) else wall
def mirrored(f):
    o = Vector(f(0, 0, 0)); ud = Vector(f(1, 0, 0)) - o; n = Vector(f(0, 0, 1)) - o
    return ud.dot((-n).cross(Vector((0, 0, 1)))) < 0

def prism(bm, f, pts, a0, a1, mi=0):
    f = F(f); a = [bm.verts.new(f(p, q, a0)) for p, q in pts]; b = [bm.verts.new(f(p, q, a1)) for p, q in pts]
    n = len(pts); caps = [bm.faces.new(a), bm.faces.new(b[::-1])]
    sides = [bm.faces.new((a[i], a[(i + 1) % n], b[(i + 1) % n], b[i])) for i in range(n)]
    for x in caps + sides: x.material_index = mi
    if n > 4:
        for x in caps: x.normal_update()
        bmesh.ops.triangulate(bm, faces=caps, ngon_method='EAR_CLIP')
    return caps
def lbox(bm, f, u0, u1, z0, z1, w0, w1, mi=0):
    return prism(bm, f, [(u0, z0), (u1, z0), (u1, z1), (u0, z1)], w0, w1, mi)[1]
def wbox(bm, lo, hi, mi=0):
    return lbox(bm, lambda u, z, w: (u, w, z), lo[0], hi[0], lo[2], hi[2], lo[1], hi[1], mi)
def cyl(bm, p0, p1, r, seg=8, mi=0, r1=None):
    p0, p1 = Vector(p0), Vector(p1); d = p1 - p0
    res = bmesh.ops.create_cone(bm, cap_ends=True, segments=seg, radius1=r, radius2=r if r1 is None else r1, depth=d.length)
    rot = Vector((0, 0, 1)).rotation_difference(d.normalized()).to_matrix().to_4x4()
    mtx = Matrix.Translation((p0 + p1) / 2) @ rot
    for v in res['verts']: v.co = mtx @ v.co
    for x in {x for v in res['verts'] for x in v.link_faces}: x.material_index = mi
def sphere(bm, c, r, sz=1.0, mi=0, u=8, v=5):
    res = bmesh.ops.create_uvsphere(bm, u_segments=u, v_segments=v, radius=r)
    for x in res['verts']: x.co = Vector((c[0] + x.co.x, c[1] + x.co.y, c[2] + x.co.z * sz))
    for x in {x for v_ in res['verts'] for x in v_.link_faces}: x.material_index = mi
def set_uv(bm, face, f, u0, u1, z0, z1, cell=(0, 0, 1, 1)):
    f = F(f); o = Vector(f(0, 0, 0)); ud = Vector(f(1, 0, 0)) - o; flip = mirrored(f)
    uvl = bm.loops.layers.uv.get('UVMap') or bm.loops.layers.uv.new('UVMap')
    for lp in face.loops:
        co = lp.vert.co; s = ((co - o).dot(ud) - u0) / (u1 - u0); t = (co.z - z0) / (z1 - z0)
        if flip: s = 1 - s
        lp[uvl].uv = (cell[0] + s * (cell[2] - cell[0]), cell[1] + t * (cell[3] - cell[1]))

def fix_normals(bm):
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    seen = set()
    for f0 in bm.faces:
        if f0.index in seen: continue
        isl, stack = [], [f0]; seen.add(f0.index)
        while stack:
            f = stack.pop(); isl.append(f)
            for e in f.edges:
                for g in e.link_faces:
                    if g.index not in seen: seen.add(g.index); stack.append(g)
        if any(len(e.link_faces) != 2 for f in isl for e in f.edges): continue
        c = sum((v.co for f in isl for v in f.verts), Vector()) / sum(len(f.verts) for f in isl)
        vol = 0.0
        for f in isl:
            v0 = f.verts[0].co - c
            for i in range(1, len(f.verts) - 1): vol += v0.dot((f.verts[i].co - c).cross(f.verts[i + 1].co - c))
        if vol < 0: bmesh.ops.reverse_faces(bm, faces=isl)

def make(name, bm, cname, mats, origin=None, loc=None, rot=None, recalc=True):
    if origin is not None:
        origin = Vector(origin)
        for v in bm.verts: v.co -= origin
    bm.faces.index_update()
    if recalc: fix_normals(bm)
    if not bm.loops.layers.uv.get('UVMap'): bm.loops.layers.uv.new('UVMap')
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    for m in mats: me.materials.append(m)
    o = bpy.data.objects.new(name, me)
    o.location = origin if origin is not None else (loc or (0, 0, 0))
    if rot: o.rotation_euler = rot
    col(cname).objects.link(o); return o

def boolean_cut(o, cutters):
    tmp = bpy.data.collections.new('_cut'); sc.collection.children.link(tmp)
    for i, bm in enumerate(cutters):
        me = bpy.data.meshes.new('_c'); bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:]); bm.to_mesh(me); bm.free()
        tmp.objects.link(bpy.data.objects.new('_c%d' % i, me))
    md = o.modifiers.new('cut', 'BOOLEAN'); md.operation = 'DIFFERENCE'
    md.operand_type = 'COLLECTION'; md.collection = tmp; md.solver = 'EXACT'
    me = bpy.data.meshes.new_from_object(o.evaluated_get(bpy.context.evaluated_depsgraph_get()))
    old = o.data; o.modifiers.remove(md); o.data = me; me.name = o.name
    if not me.materials:
        for m in old.materials: me.materials.append(m)
    bpy.data.meshes.remove(old)
    for x in list(tmp.objects): bpy.data.meshes.remove(x.data)
    bpy.data.collections.remove(tmp)
def cutter(wall, u0, u1, z0, z1):
    bm = bmesh.new(); lbox(bm, wall, u0, u1, z0, z1, -THICK[wall] - 0.2, 0.2); return bm
def bisect(bm, planes):
    for co, no in planes:
        bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=co, plane_no=no)

# ---------------------------------------------------------------- layout data
PLATES = open('/tmp/claude-0/tools/plates.txt').read().split()
PLATE_IDX = {}
for i, p in enumerate(PLATES): PLATE_IDX.setdefault(p.split(':')[0], i)
def plate_cell(num):
    i = PLATE_IDX[num]; cx, cy = i % 8, i // 8
    return (cx / 8, 1 - (cy + 1) / 8, (cx + 1) / 8, 1 - cy / 8)
# (number, wall, centre, type, doormat)
DOORS = [
    ('133', 'N', 2.0, 'DermatinBrown', 'Mat_Olive'), ('134', 'S', 2.0, 'WoodBeige', None),
    ('135', 'N', 5.6, 'DermatinBlack', 'Mat_Rubber'), ('136', 'S', 5.6, 'SteelBrown', None),
    ('137', 'N', 10.0, 'DermatinRed', 'Mat_Blue'), ('138', 'S', 9.6, 'WoodBrown', None),
    ('139', 'N', 13.0, 'SteelGrey', None), ('140', 'S', 12.6, 'boarded', None),
    (None, 'N', 16.2, 'wrong', None), ('141', 'S', 15.6, 'DermatinBrown', 'Mat_Olive'),
    ('142', 'S', 19.6, 'SteelBrown', None), ('143', 'S', 22.4, 'sealed', None),
    ('144', 'N', 26.0, 'DermatinBlack', 'Mat_Rubber'), ('145', 'S', 25.6, 'WoodBlue', None),
    ('146', 'N', 29.0, 'SteelGrey', None), ('147', 'S', 28.6, 'DermatinRed', 'Mat_Blue'),
    ('148', 'N', 32.0, 'DermatinBrown', None), ('144', 'S', 31.6, 'WoodBrown', None),   # the number repeats
    ('149', 'N', 36.6, 'WoodBlue', None), ('150', 'S', 36.6, 'SteelBrown', 'Mat_Rubber'),
    ('151', 'N', 40.0, 'WoodBeige', None), ('152', 'S', 40.0, 'DermatinBrown', 'Mat_Olive'),
]
DW, DH = 0.9, 2.05
def dsize(t): return (0.7, 2.25) if t == 'wrong' else (DW, DH)
STAIR = ('HW', 4.6, 1.2, 2.1)
LIFTS = [('A', 19.6), ('B', 22.0)]; LW, LH = 0.8, 2.0
WINDOWS = [('W', 'EW'), ('E', 'EE')]; WU0, WU1, WZ0, WZ1 = 0.4, 1.6, 0.9, 2.2
BEAMS = [6, 12, 18, 24, 30, 36]
LAMPS = [(3, 'bulb'), (9, 'broken'), (15, 'plafond'), (27, 'plafond_flicker'), (33, 'dead'), (39, 'bulb_dead')]
PANELS = [('N', 11.5, 'ElectricPanel', 0), ('N', 27.5, 'ElectricPanel', -20), ('S', 21.0, 'ElectricPanel', 110),
          ('N', 38.3, 'Chute_Hatch', 0)]
PATCH_LOW = [(11.0, 12.4, 'N'), (16.8, 18.0, 'S'), (30.0, 31.2, 'N')]
PATCH_UP = [(29.6, 31.2)]

# ---------------------------------------------------------------- shell: walls
bm = bmesh.new(); wbox(bm, (-TE, -T, 0), (CX + TE, HY + T, H))
WMAT = list(W.values())[:-1]                                     # all wall mats except ceiling
walls = make('Walls', bm, 'Shell', WMAT)
cuts = []
c = bmesh.new(); wbox(c, (0, 0, -.5), (CX, CY, H + .5)); cuts.append(c)
c = bmesh.new(); wbox(c, (HX0, CY - .05, -.5), (HX1, HY, H + .5)); cuts.append(c)
for num, wl, u, t, _ in DOORS:
    wd, h = dsize(t); cuts.append(cutter(wl, u - wd / 2, u + wd / 2, TH, h))
wl, u, wd, h = STAIR; cuts.append(cutter(wl, u - wd / 2, u + wd / 2, TH, h))
for _, u in LIFTS: cuts.append(cutter('HN', u - LW / 2, u + LW / 2, TH, LH))
for _, wl in WINDOWS: cuts.append(cutter(wl, WU0, WU1, WZ0, WZ1))
boolean_cut(walls, cuts)
bm = bmesh.new(); bm.from_mesh(walls.data)
xs = sorted({8, 34} | {a for p in PATCH_LOW for a in p[:2]} | {a for p in PATCH_UP for a in p})
bisect(bm, [((0, 0, z), (0, 0, 1)) for z in (0.1, 1.5, 1.53)] + [((x, 0, 0), (1, 0, 0)) for x in xs])
IDX = {m.name: i for i, m in enumerate(WMAT)}
def wall_mat(c):
    x, y, z = c
    zone = 'tw' if x < 8 else 'te' if x > 34 else ('hall' if (y > CY + 1e-3 and HX0 - .01 <= x <= HX1 + .01) else 'corr')
    band = 'base' if z < .1 else 'low' if z < 1.5 else 'stripe' if z < 1.53 else 'up'
    if band == 'base': return 'M_Baseboard_Paint'
    if zone == 'tw': return {'low': 'M_Wall_Vagonka', 'stripe': 'M_Wood_Frame', 'up': 'M_Wall_Wallpaper'}[band]
    if zone == 'te': return {'low': 'M_Wall_PaintBlue', 'stripe': 'M_Wall_PaintBlueStripe', 'up': 'M_Plaster_Stained'}[band]
    if zone == 'corr':
        side = 'N' if y > 1.0 else 'S'
        if band == 'low' and any(a < x < b and s == side for a, b, s in PATCH_LOW): return 'M_Wall_PaintPeeling'
        if band == 'up' and any(a < x < b for a, b in PATCH_UP): return 'M_Plaster_Stained'
    return {'low': 'M_Wall_PaintGreen', 'stripe': 'M_Wall_PaintGreenStripe', 'up': 'M_Whitewash'}[band]
for fc in bm.faces: fc.material_index = IDX[wall_mat(fc.calc_center_median())]
bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=1e-5)
bm.to_mesh(walls.data); bm.free()

# floors and ceiling
for name, (x0, y0, x1, y1), m in (('Floor_TambourW', (0, 0, 8, CY), FL['lino']), ('Floor_Corridor', (8, 0, 34, CY), FL['hex']),
                                  ('Floor_TambourE', (34, 0, CX, CY), FL['worn']), ('Floor_Hall', (HX0, CY, HX1, HY), FL['terrazzo'])):
    bm = bmesh.new(); bm.faces.new([bm.verts.new(p) for p in ((x0, y0, 0), (x1, y0, 0), (x1, y1, 0), (x0, y1, 0))])
    make(name, bm, 'Shell', [m], recalc=False)
CL = [(0, 0), (CX, 0), (CX, CY), (HX1, CY), (HX1, HY), (HX0, HY), (HX0, CY), (0, CY)]
bm = bmesh.new(); bm.faces.new([bm.verts.new((x, y, H)) for x, y in CL][::-1])
bisect(bm, [((x, 0, 0), (1, 0, 0)) for x in (8, 34, 29.6, 31.2)])
for fc in bm.faces:
    x = fc.calc_center_median().x; fc.material_index = 1 if (x < 8 or x > 34 or 29.6 < x < 31.2) else 0
make('Ceiling', bm, 'Shell', [W['Ceiling'], W['Plaster_Stained']], recalc=False)
bm = bmesh.new()
for b in BEAMS: wbox(bm, (b - .15, 0, 2.32), (b + .15, CY, H))
wbox(bm, (HX0 + .15, CY - .1, 2.32), (HX1 - .15, CY + .1, H))
make('Ceiling_Beams', bm, 'Shell', [W['Whitewash']])

# ---------------------------------------------------------------- apartment doors
def frame(bm, wl, u0, u1, h, a=0.07, d=0.015, mi=0):
    prism(bm, wl, [(u0 - a, 0), (u0, 0), (u0, h), (u1, h), (u1, 0), (u1 + a, 0), (u1 + a, h + a), (u0 - a, h + a)], 0, d, mi)
for num, wl, u, t, matname in DOORS:
    f = WALL[wl]; wd, h = dsize(t); u0, u1 = u - wd / 2, u + wd / 2
    tag = num if num else 'X'
    leafmat = {'boarded': DM['WoodBrown'], 'sealed': DM['WoodBrown'], 'wrong': W['Wall_PaintGreen']}.get(t) or DM[t]
    mats = [leafmat, M['handle'], M['plate'], M['brass'], P['Paper'], W['Whitewash']]
    bm = bmesh.new()
    lbox(bm, wl, u0 + .004, u1 - .004, TH, h - .004, -.11, -.07, 0)
    if t == 'wrong':     # painted over like the wall: green below the stripe, whitewash above
        bisect(bm, [((0, 0, 1.5), (0, 0, 1))])
        for fc in bm.faces: fc.material_index = 0 if fc.calc_center_median().z < 1.5 else 5
    else:
        steel, wood = t.startswith('Steel'), t.startswith('Wood') or t in ('sealed', 'boarded')
        if t != 'boarded':
            if wood: cyl(bm, f(u1 - .08, 1.0, -.07), f(u1 - .08, 1.0, -.03), .025, 8, 3)
            else: lbox(bm, wl, u1 - .17, u1 - .05, .98, 1.01, -.07, -.02, 1)
            if t != 'sealed': lbox(bm, wl, u1 - .10, u1 - .07, 1.12, 1.17, -.07, -.066, 1)
            if steel: lbox(bm, wl, u1 - .10, u1 - .07, .80, .85, -.07, -.066, 1)
            cyl(bm, f((u0 + u1) / 2, 1.55, -.07), f((u0 + u1) / 2, 1.55, -.055), .012, 6, 1)
        pf = lbox(bm, wl, (u0 + u1) / 2 - .06, (u0 + u1) / 2 + .06, 1.72, 1.78, -.07, -.066, 2)
        set_uv(bm, pf, wl, (u0 + u1) / 2 - .06, (u0 + u1) / 2 + .06, 1.72, 1.78, plate_cell(num))
        if t == 'sealed': lbox(bm, wl, u1 - .26, u1 - .02, 1.06, 1.13, -.07, -.068, 4)
    make('Door_%s' % tag + ('_B' if num == '144' and wl == 'S' else ''), bm, 'Doors', mats, origin=f(u0 + .004, TH, -.09))
    if t == 'wrong': continue
    bm = bmesh.new(); frame(bm, wl, u0, u1, h)
    if t == 'boarded':
        for zc in (.55, 1.15, 1.8): lbox(bm, wl, u0 - .07, u1 + .07, zc - .06, zc + .06, .015, .035, 1)
    nm = 'Door_%s_Frame' % tag + ('_B' if num == '144' and wl == 'S' else '')
    make(nm, bm, 'Doors', [W['Wood_Frame'], P['Planks']], origin=f(u, 0, 0))
    bm = bmesh.new(); ub = u0 - .15                                   # doorbell
    lbox(bm, wl, ub - .035, ub + .035, 1.42, 1.52, 0, .025, 0); cyl(bm, f(ub, 1.47, .025), f(ub, 1.47, .032), .01, 6, 1)
    make(nm.replace('_Frame', '_Bell'), bm, 'Doors', [M['btn_cream'], M['plastic']], origin=f(ub, 1.42, 0))
    if matname:
        bm = bmesh.new(); lbox(bm, wl, u - .3, u + .3, 0, .012, .05, .45)
        make(nm.replace('_Frame', '_Mat'), bm, 'Props', [P[matname]], origin=f(u, 0, .25))
bm = bmesh.new(); lbox(bm, 'N', 34.9, 35.5, 0, .012, .05, .45)       # a doormat in front of a blank wall
make('Doormat_NoDoor', bm, 'Props', [P['Mat_Olive']], origin=WALL['N'](35.2, 0, .25))

# stair door (locked double door with wired glass)
wl, u, wd, h = STAIR; f = WALL[wl]; u0, u1 = u - wd / 2, u + wd / 2
for side, (a0, a1, hinge) in (('L', (u0 + .004, u - .002, u0 + .004)), ('R', (u + .002, u1 - .004, u1 - .004))):
    bm = bmesh.new(); lbox(bm, wl, a0, a1, TH, h - .004, -.11, -.07, 0)
    lbox(bm, wl, a0 + .1, a1 - .1, 1.15, 1.95, -.07, -.066, 1)
    if side == 'R': lbox(bm, wl, a0 + .05, a0 + .17, .98, 1.01, -.07, -.02, 2)
    make('Door_Stair_' + side, bm, 'Doors', [DM['StairWood'], M['wired'], M['handle']], origin=f(hinge, TH, -.09))
bm = bmesh.new(); frame(bm, wl, u0, u1, h, a=.08); make('Door_Stair_Frame', bm, 'Doors', [W['Wood_Frame']], origin=f(u, 0, 0))

# ---------------------------------------------------------------- lifts
f = WALL['HN']
for name, u in LIFTS:
    u0, u1 = u - LW / 2, u + LW / 2; broken = name == 'B'
    bm = bmesh.new(); frame(bm, 'HN', u0, u1, LH, a=.1, d=.04)
    make('Lift%s_Frame' % name, bm, 'Lift', [P['Metal_Grille'] if broken else P['LiftDoor_Metal']], origin=f(u, 0, 0))
    gap = .03 if broken else .001
    for side, (a0, a1) in (('L', (u0 + .004 - (.026 if broken else 0), u - gap)), ('R', (u + gap, u1 - .004 + (.026 if broken else 0)))):
        bm = bmesh.new(); lbox(bm, 'HN', a0, a1, TH, LH - .004, -.10, -.07)
        make('Lift%s_Door_%s' % (name, side), bm, 'Lift', [P['Metal_Grille'] if broken else P['LiftDoor_Metal']],
             origin=f((a0 + a1) / 2, TH, -.085))
    bu = u1 + .3
    bm = bmesh.new(); lbox(bm, 'HN', bu - .04, bu + .04, 1.12, 1.26, 0, .02, 0); lbox(bm, 'HN', bu - .015, bu + .015, 1.17, 1.20, .02, .03, 1)
    make('Lift%s_CallButton' % name, bm, 'Lift', [M['handle'], M['btn_dead'] if broken else M['btn']], origin=f(bu, 1.12, 0))
# lift A cab
bm = bmesh.new(); wbox(bm, (19.0, Y0, -.05), (20.2, Y0 + 1.1, 2.25))
cab = make('LiftA_Cab', bm, 'Lift', [P['LiftCab_Wood'], P['LiftCab_Floor'], P['LiftDoor_Metal']], origin=(19.6, Y0, 0))
c1 = bmesh.new(); wbox(c1, (19.05, Y0 + .05, 0), (20.15, Y0 + 1.05, 2.2))
c2 = bmesh.new(); wbox(c2, (19.2, Y0 - .1, 0), (20.0, Y0 + .2, LH)); boolean_cut(cab, [c1, c2])
bm = bmesh.new(); bm.from_mesh(cab.data)
for fc in bm.faces:
    nz, zc = fc.normal.z, fc.calc_center_median().z
    fc.material_index = 1 if (nz > .9 and abs(zc) < .01) else (2 if (nz < -.9 and abs(zc - 2.2) < .01) else 0)
bm.to_mesh(cab.data); bm.free()
bm = bmesh.new(); wbox(bm, (19.45, Y0 + .4, 2.18), (19.75, Y0 + .7, 2.2)); make('LiftA_CabLight', bm, 'Lift', [M['cablight']], origin=(19.6, Y0 + .55, 2.2))
bm = bmesh.new(); wbox(bm, (20.13, Y0 + .15, .95), (20.15, Y0 + .35, 1.5), 0)
for i in range(5):
    for j in range(2):
        z = 1.0 + i * .09; y = Y0 + .2 + j * .07
        wbox(bm, (20.12, y, z), (20.13, y + .035, z + .05), 2 if (i, j) == (3, 1) else 1)
make('LiftA_CabPanel', bm, 'Lift', [M['steel'], M['btn_cream'], M['btn_burnt']], origin=(20.15, Y0 + .25, .95))
# lift B: doors ajar, empty shaft behind
bm = bmesh.new(); wbox(bm, (21.4, Y0, -2.5), (22.6, Y0 + 1.5, H + 1.0))
sh = make('LiftB_Shaft', bm, 'Lift', [P['Shaft_Concrete']], origin=(22.0, Y0, 0))
c1 = bmesh.new(); wbox(c1, (21.45, Y0 - .01, -2.45), (22.55, Y0 + 1.45, H + .95)); boolean_cut(sh, [c1])
bm = bmesh.new()
for x in (21.8, 22.0, 22.2): cyl(bm, (x, Y0 + .8, -2.45), (x, Y0 + .8, H + .95), .012, 6)
make('LiftB_Cables', bm, 'Lift', [M['wire']], origin=(22.0, Y0 + .8, -2.45))
bm = bmesh.new(); fs = lbox(bm, 'HN', 22.82, 23.1, 1.40, 1.68, 0, .002); set_uv(bm, fs, 'HN', 22.82, 23.1, 1.40, 1.68)
make('LiftB_Sign', bm, 'Lift', [M['sign']], origin=f(22.96, 1.4, 0))
bm = bmesh.new(); fs = lbox(bm, 'HN', 20.6, 21.0, 1.62, 2.02, 0, .002); set_uv(bm, fs, 'HN', 20.6, 21.0, 1.62, 2.02)
make('Decal_FloorNumber', bm, 'Props', [M['number']], origin=f(20.8, 1.62, 0))

# ---------------------------------------------------------------- windows + radiators
for name, wl in WINDOWS:
    f = WALL[wl]; bm = bmesh.new()
    for a in ((WU0, WU0 + .06, .9, WZ1), (WU1 - .06, WU1, .9, WZ1), (WU0 + .0605, WU1 - .0605, WZ1 - .06, WZ1),
              (WU0 + .0605, WU1 - .0605, .9, .99), (.97, 1.03, .99, WZ1 - .06), (WU0 + .0605, .97, 1.72, 1.78)):
        lbox(bm, wl, a[0], a[1], a[2], a[3], -.245, -.185, 0)
    for a in ((WU0 + .06, .97, .99, 1.72), (WU0 + .06, .97, 1.78, WZ1 - .06), (1.03, WU1 - .06, .99, WZ1 - .06)):
        lbox(bm, wl, a[0], a[1], a[2], a[3], -.215, -.205, 1)
    prism(bm, lambda p, q, a: f(p, a, q), [(.4, -.18), (1.6, -.18), (1.6, 0), (1.67, 0), (1.67, .07), (.33, .07), (.33, 0), (.4, 0)], .9, .93, 0)
    make('Window_' + name, bm, 'Windows', [W['Wood_Frame'], M['night']], origin=f(1.0, .9, 0))
    bm = bmesh.new()
    for i in range(9):
        a = .595 + i * .09; lbox(bm, wl, a, a + .06, .12, .72, .06, .16)
    for z in (.2, .64): cyl(bm, f(.3, z, .11), f(1.405, z, .11), .025, 8)
    for a in (.7, 1.3): lbox(bm, wl, a, a + .04, .66, .70, 0, .06)
    cyl(bm, f(.3, 0, .11), f(.3, H, .11), .025, 8)
    make('Radiator_' + name, bm, 'Windows', [P['Radiator']], origin=f(1.0, 0, 0))
f = WALL['EW']; bm = bmesh.new()                                            # stuff on the west sill
for uu, r, hh in ((.6, .05, .14), (.74, .045, .12), (.86, .05, .16)): cyl(bm, f(uu, .93, -.08), f(uu, .93 + hh, -.08), r, 8, 0)
cyl(bm, f(1.35, .93, -.08), f(1.35, 1.04, -.08), .07, 8, 1, r1=.08)
for du, dw, top in ((-.02, .01, 1.25), (.02, -.01, 1.2), (0, .02, 1.3)):
    lbox(bm, 'EW', 1.35 + du - .004, 1.35 + du + .004, 1.0, top, -.08 + dw - .004, -.08 + dw + .004, 2)
make('Sill_Jars_Plant', bm, 'Props', [M['jar'], M['pot'], M['stem']], origin=f(1.0, .93, -.08))

# ---------------------------------------------------------------- tambour partitions
fx = lambda u, z, w: (8.0 + w, u, z)
bm = bmesh.new(); prism(bm, fx, [(0, 0), (1.0, 0), (1.0, 2.05), (1.9, 2.05), (1.9, 0), (CY, 0), (CY, H), (0, H)], -.05, .05)
make('TambourW_Partition', bm, 'Tambours', [P['Partition_Wood']], origin=(8.0, 1.0, 0))
bm = bmesh.new(); lbox(bm, fx, 1.004, 1.896, 0, 2.046, -.02, .02, 0)
for s in (1, -1): lbox(bm, fx, 1.15, 1.75, 1.2, 1.9, s * .02, s * .024, 1)
lbox(bm, fx, 1.06, 1.18, .98, 1.01, .02, .06, 2)
make('TambourW_Door', bm, 'Tambours', [P['Partition_Door'], M['wired'], M['handle']], origin=(8.0, 1.896, 0), rot=(0, 0, math.radians(80)))
fx = lambda u, z, w: (34.0 + w, u, z)
bm = bmesh.new()
for a in ((0, .04), (.96, 1.0), (1.96, 2.0)): lbox(bm, fx, a[0], a[1], 0, H, -.02, .02)
lbox(bm, fx, .0405, .9595, 0, .04, -.02, .02); lbox(bm, fx, .0405, .9595, 2.05, 2.09, -.02, .02)
lbox(bm, fx, 1.0005, 1.9595, 2.05, 2.09, -.02, .02); lbox(bm, fx, .0405, .9595, H - .04, H, -.02, .02); lbox(bm, fx, 1.0005, 1.9595, H - .04, H, -.02, .02)
for i in range(7): uu = .12 + i * .12; lbox(bm, fx, uu - .008, uu + .008, .04, 2.05, -.008, .008)
for i in range(16):
    uu = .12 + i * .12
    if abs(uu - .98) > .03: lbox(bm, fx, uu - .008, uu + .008, 2.09, H - .04, -.008, .008)
make('TambourE_Grille', bm, 'Tambours', [P['Metal_Grille']], origin=(34.0, 1.0, 0))
bm = bmesh.new()
lbox(bm, fx, 1.004, 1.034, 0, 2.045, -.015, .015); lbox(bm, fx, 1.926, 1.956, 0, 2.045, -.015, .015)
lbox(bm, fx, 1.0345, 1.9255, 0, .03, -.015, .015); lbox(bm, fx, 1.0345, 1.9255, 2.015, 2.045, -.015, .015)
for i in range(6): uu = 1.034 + (i + 1) * (.892 / 7); lbox(bm, fx, uu - .008, uu + .008, .03, 2.015, -.008, .008)
lbox(bm, fx, 1.034, 1.11, .95, 1.1, -.03, .03, 1)
make('TambourE_GrilleDoor', bm, 'Tambours', [P['Metal_Grille'], M['handle']], origin=(34.0, 1.956, 0), rot=(0, 0, math.radians(-55)))

# ---------------------------------------------------------------- electrical panels, fire cabinet, chute, mailboxes
for wl, u, tex, ang in PANELS:
    f = WALL[wl]; bm = bmesh.new(); lbox(bm, wl, u - .3, u + .3, 1.1, 2.0, 0, .14)
    meters = ang > 45
    if meters:
        for a in (u - .22, u + .04):
            lbox(bm, wl, a, a + .16, 1.45, 1.70, .14, .20, 1); lbox(bm, wl, a + .03, a + .13, 1.58, 1.64, .20, .203, 2)
    nm = 'ElectricPanel_%s_%d' % (wl, int(u * 10))
    make(nm, bm, 'Props', [P[tex], M['plastic'], M['btn_cream']], origin=f(u, 1.1, 0))
    bm = bmesh.new(); lbox(bm, wl, u - .3, u + .3, 1.1, 2.0, .14, .152)
    hinge = Vector(f(u - .3, 1.1, .146)); o = make(nm + '_Door', bm, 'Props', [P[tex]], origin=hinge)
    o.rotation_euler = (0, 0, math.radians(ang))
f = WALL['S']; bm = bmesh.new()
lbox(bm, 'S', 13.775, 14.425, .85, 1.7, 0, .21, 0); lbox(bm, 'S', 13.78, 14.42, .855, 1.695, .21, .222, 0)
lbox(bm, 'S', 13.9, 14.3, 1.25, 1.6, .222, .225, 1); lbox(bm, 'S', 14.36, 14.39, 1.2, 1.3, .222, .245, 2)
make('FireCabinet', bm, 'Props', [P['FireCabinet'], M['wired'], M['handle']], origin=f(14.1, .85, 0))
bm = bmesh.new(); wbox(bm, (23.45, 6.45, 0), (HX1, HY, H))
bisect(bm, [((0, 0, z), (0, 0, 1)) for z in (.1, 1.5, 1.53)])
for fc in bm.faces:
    z = fc.calc_center_median().z; fc.material_index = 0 if z < .1 else 1 if z < 1.5 else 2 if z < 1.53 else 3
make('TrashChute', bm, 'Props', [W['Baseboard_Paint'], W['Wall_PaintGreen'], W['Wall_PaintGreenStripe'], W['Whitewash']], origin=(23.725, 6.725, 0))
bm = bmesh.new(); wbox(bm, (23.38, 6.52, .75), (23.45, 6.93, 1.15), 0); wbox(bm, (23.35, 6.66, 1.08), (23.38, 6.79, 1.11), 1)
make('TrashChute_Hatch', bm, 'Props', [P['Chute_Hatch'], M['handle']], origin=(23.45, 6.725, .75))
f = WALL['HE']; bm = bmesh.new(); lbox(bm, 'HE', 2.95, 3.85, .9, 1.6, 0, .2, 0)
cw, ch = .86 / 3, .66 / 4
for i in range(3):
    for j in range(4):
        a, z = 2.97 + i * cw, .92 + j * ch
        lbox(bm, 'HE', a + .008, a + cw - .008, z + .008, z + ch - .008, .2, .212, 0)
        lbox(bm, 'HE', a + cw / 2 - .06, a + cw / 2 + .06, z + ch - .045, z + ch - .033, .212, .214, 1)
make('Mailboxes', bm, 'Props', [P['Mailbox'], M['plastic']], origin=f(3.4, .9, 0))
bm = bmesh.new()
for a in ((3.0, 3.21, 1.68, 1.98), (3.3, 3.5, 1.72, 1.95), (3.58, 3.8, 1.66, 1.86)): lbox(bm, 'HE', a[0], a[1], a[2], a[3], 0, .002)
make('Notices', bm, 'Props', [P['Paper']], origin=f(3.4, 1.66, 0))
for i, (x, y, r) in enumerate(((23.4, 3.0, 15), (23.05, 3.6, -30), (23.55, 3.95, 70))):
    bm = bmesh.new(); wbox(bm, (-.08, -.055, 0), (.08, .055, .003))
    make('Envelope_%02d' % (i + 1), bm, 'Props', [P['Envelope']], loc=(x, y, 0), rot=(0, 0, math.radians(r)))

# ---------------------------------------------------------------- lamps, wires, lights
lights = []
def bulb(bm, x, y, mi_glass):
    cyl(bm, (x, y, H - .35), (x, y, H), .005, 4, 0); cyl(bm, (x, y, H - .42), (x, y, H - .35), .02, 6, 0)
    sphere(bm, (x, y, H - .452), .035, 1, mi_glass, 6, 4)
for x, kind in LAMPS + [(21, 'hall')]:
    y = 4.5 if kind == 'hall' else 1.0; bm = bmesh.new()
    if kind in ('plafond', 'plafond_flicker', 'hall'): cyl(bm, (x, y, H - .07), (x, y, H), .16, 8, 1)
    elif kind == 'dead': cyl(bm, (x, y, H - .07), (x, y, H), .16, 8, 2)
    elif kind == 'broken': cyl(bm, (x, y, H - .025), (x, y, H), .1, 8, 0); cyl(bm, (x, y, H - .08), (x, y, H - .025), .02, 6, 0)
    elif kind == 'bulb': bulb(bm, x, y, 1)
    elif kind == 'bulb_dead': bulb(bm, x, y, 2)
    nm = 'Lamp_%s_%d' % ({'hall': 'Hall'}.get(kind, 'Corridor'), x) + ('_Flicker' if kind == 'plafond_flicker' else '') + \
         ('_Dead' if kind in ('dead', 'bulb_dead', 'broken') else '')
    make(nm, bm, 'Lamps', [M['plastic'], M['lamp'], M['deadglass']], origin=(x, y, H))
    if kind in ('plafond', 'plafond_flicker', 'hall', 'bulb'):
        lights.append((nm.replace('Lamp', 'Light'), (x, y, H - (.5 if kind == 'bulb' else .15)), 22 if kind == 'bulb' else 40, (1, .82, .6)))
bm = bmesh.new(); taps = sorted([(x, 'lamp') for x, _ in LAMPS] + [(u, 'panel') for wl, u, _, _ in PANELS if wl == 'N'])
for x0, x1 in ((0.4, HX0 - .4), (HX1 + .4, CX - .4)):
    wbox(bm, (x0, CY - .02, 2.24), (x1, CY, 2.26))
for t, kind in taps:
    if kind == 'lamp':
        wbox(bm, (t - .01, CY - .02, 2.26), (t + .01, CY, H))
        wbox(bm, (t - .008, {9: 1.105, 15: 1.165, 27: 1.165, 33: 1.165}.get(t, 1.0055), H - .02), (t + .008, CY - .02, H))
    else: wbox(bm, (t - .01, CY - .02, 2.0), (t + .01, CY, 2.24))
wbox(bm, (20.99, 0, 2.0), (21.01, .02, H))      # S panel feed up to the ceiling
make('Wires', bm, 'Lamps', [M['wire']], origin=(21, 1.0, H))
lights += [('Light_LiftA_Cab', (19.6, Y0 + .55, 2.05), 12, (1, .93, .8)), ('Light_LiftA_Button', (20.3, HY - .08, 1.19), .3, (1, .1, .05)),
           ('Light_Window_W', (.5, 1.0, 1.6), 3, (.45, .55, 1.0)), ('Light_Window_E', (CX - .5, 1.0, 1.6), 3, (.45, .55, 1.0))]
for n, loc, e, c in lights:
    d = bpy.data.lights.new(n, 'POINT'); d.energy = e; d.color = c; d.shadow_soft_size = .05
    o = bpy.data.objects.new(n, d); o.location = loc; col('Lights').objects.link(o)
sp = bpy.data.objects.new('Spawn_Player', None); sp.empty_display_type = 'ARROWS'; sp.location = (18.7, 4.6, 0)
sp.rotation_euler = (0, 0, math.radians(-90)); col('Markers').objects.link(sp)

# ---------------------------------------------------------------- props / clutter
bm = bmesh.new()                                                   # chair facing lift A
for sx in (-1, 1):
    for sy in (-1, 1): wbox(bm, (sx * .21 - (.035 if sx > 0 else 0), sy * .2 - (.035 if sy > 0 else 0), 0), (sx * .21 + (.035 if sx < 0 else 0), sy * .2 + (.035 if sy < 0 else 0), .43))
wbox(bm, (-.215, -.205, .43), (.215, .205, .46))
for sx in (-1, 1): wbox(bm, (sx * .21 - (.035 if sx > 0 else 0), -.2, .46), (sx * .21 + (.035 if sx < 0 else 0), -.165, .92))
wbox(bm, (-.175, -.2, .7), (.175, -.18, .88))
make('Chair', bm, 'Props', [P['Chair_Wood']], loc=(19.6, 4.2, 0), rot=(0, 0, math.radians(6)))
bm = bmesh.new()                                                   # wardrobe in the west tambour
wbox(bm, (3.3, 0, .06), (4.3, .5, 1.9)); wbox(bm, (3.28, 0, 1.9), (4.32, .53, 1.95))
for x in (3.3, 4.25):
    for y in (0, .45): wbox(bm, (x + .005, y + .005, 0), (x + .045, y + .045, .06))
for a, b in ((3.32, 3.795), (3.805, 4.28)): wbox(bm, (a, .5, .1), (b, .512, 1.86))
for a in (3.77, 3.815): wbox(bm, (a, .512, .95), (a + .015, .53, 1.1), 1)
make('Wardrobe', bm, 'Props', [P['Furniture_Wood'], M['brass']], origin=(3.8, .25, 0))
bm = bmesh.new()                                                   # sled leaning on the wall
for sx in (-1, 1): wbox(bm, (sx * .16 - .01, 0, 0), (sx * .16 + .01, .8, .05), 1)
for yy in (.1, .3, .5, .7): wbox(bm, (-.17, yy - .03, .05), (.17, yy + .03, .07), 0)
make('Sled', bm, 'Props', [P['Sled_Wood'], M['steel']], loc=(4.72, .28, .012), rot=(math.radians(105), 0, 0))
bm = bmesh.new(); wbox(bm, (.6, .6, 0), (7.7, 1.4, .008)); make('Carpet_Runner', bm, 'Props', [P['Carpet_Runner']], origin=(4.15, 1.0, 0))
bm = bmesh.new(); cyl(bm, (7.75, .2, 0), (7.75, .2, 1.5), .12, 8); make('Carpet_Rolled', bm, 'Props', [P['Carpet_Rolled']], origin=(7.75, .2, 0))
bm = bmesh.new()
for x in (5.47, 5.68):
    wbox(bm, (x - .05, 1.62, .012), (x + .05, 1.89, .112)); wbox(bm, (x - .045, 1.775, .112), (x + .045, 1.885, .38))
make('Boots', bm, 'Props', [P['Boots']], origin=(5.575, 1.75, .012))
bm = bmesh.new()                                                   # boxes in the east tambour
wbox(bm, (37.6, .02, 0), (38.1, .42, .35)); wbox(bm, (38.12, .02, 0), (38.57, .42, .3)); make('Boxes_01', bm, 'Props', [P['Cardboard']], origin=(38.08, .22, 0))
bm = bmesh.new(); wbox(bm, (-.2, -.17, 0), (.2, .17, .28)); make('Boxes_02', bm, 'Props', [P['Cardboard']], loc=(37.85, .23, .35), rot=(0, 0, math.radians(9)))
bm = bmesh.new(); cyl(bm, (41.6, 1.6, 0), (41.6, 1.6, .28), .12, 8, 0, r1=.15); make('Bucket', bm, 'Props', [P['Bucket']], origin=(41.6, 1.6, 0))
for i, (x, y, r) in enumerate(((23.05, 6.62, .24), (22.62, 6.74, .2))):
    bm = bmesh.new(); sphere(bm, (0, 0, r * .75), r, .75, 0, 8, 6); cyl(bm, (0, 0, r * 1.45), (0, 0, r * 1.62), .04, 6, 0, r1=.01)
    make('GarbageBag_%02d' % (i + 1), bm, 'Props', [P['Plastic_Bag']], loc=(x, y, 0))

# ---------------------------------------------------------------- UV, checks, save
bpy.context.view_layer.update()
def uv_mat(o):
    mw = o.matrix_world; nm = mw.to_3x3().inverted_safe().transposed()
    bm = bmesh.new(); bm.from_mesh(o.data); uvl = bm.loops.layers.uv.get('UVMap') or bm.loops.layers.uv.new('UVMap')
    for fc in bm.faces:
        s = MS[o.data.materials[fc.material_index].name]
        if s is None: continue
        n = (nm @ fc.normal).normalized(); ax = max(range(3), key=lambda i: abs(n[i])); sg = 1 if n[ax] >= 0 else -1
        for lp in fc.loops:
            c = mw @ lp.vert.co
            u, v = (sg * c.y, c.z) if ax == 0 else ((-sg * c.x, c.z) if ax == 1 else (c.x, sg * c.y))
            lp[uvl].uv = (u / s[0], v / s[1])
    bm.to_mesh(o.data); bm.free()
for o in root.all_objects:
    if o.type == 'MESH': uv_mat(o)
meshes = [o for o in root.all_objects if o.type == 'MESH']
print(kt.check_all([o.name for o in meshes], ground=0, anchors=['Ceiling', 'Walls', 'Ceiling_Beams', 'LiftB_Shaft'],
                   ignore=['Decal_FloorNumber', 'LiftB_Sign', 'Notices', 'ElectricPanel_S_210_Door']))
print('tris', sum(len(p.vertices) - 2 for o in meshes for p in o.data.polygons), 'objects', len(meshes),
      'materials', len(bpy.data.materials), 'images', len(bpy.data.images))
bpy.ops.wm.save_as_mainfile(filepath=OUT, relative_remap=True)
print('saved', OUT)
