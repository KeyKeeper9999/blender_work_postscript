"""Night yard in front of the panel block (headless Blender 5.2 / bpy).
usage: python3 build_street.py <out.blend>
Reuses the geometry helpers of build_level.py. Late autumn, no snow."""
import sys, os, math, random, bpy, bmesh
from collections import defaultdict
from mathutils import Vector, Matrix
HERE = os.path.dirname(os.path.abspath(__file__)); LEVELS = os.path.dirname(HERE); REPO = os.path.dirname(LEVELS)
sys.path.insert(0, os.path.join(REPO, '.claude/skills/blender-keytools'))
import keytools as kt
OUT = os.path.abspath(sys.argv[-1]); TEXD = os.path.join(LEVELS, 'textures') + '/'
WARN = []; OCC = defaultdict(list); S = {'suffix': '_M'}
bpy.ops.wm.read_factory_settings(use_empty=True); sc = bpy.context.scene
bpy.ops.wm.save_as_mainfile(filepath=OUT)
root = bpy.data.collections.new('Street_Night'); sc.collection.children.link(root)
_cols = {}
def col(n):
    if n not in _cols:
        c = bpy.data.collections.new(n); root.children.link(c); _cols[n] = c
    return _cols[n]
_src = open(os.path.join(HERE, 'build_level.py')).read()
exec(_src[_src.index('_mats, MS = {}, {}'):_src.index("LC = S['light']")])
exec(_src[_src.index('# ============================================================== geometry helpers'):_src.index('# ============================================================== zones')])
H = 2.6
R = random.Random(7)

def quad(bm, pts, mi=0):
    f = bm.faces.new([bm.verts.new(p) for p in pts]); f.material_index = mi; return f
def tf(org, rot):
    m = Matrix.Rotation(math.radians(rot), 3, 'Z')
    return lambda p: tuple(m @ Vector(p) + Vector((org[0], org[1], 0)))

# ---------------------------------------------------------------- materials
E = {k: tm('T_Ext_' + k) for k in ('Panel_A', 'Panel_B', 'Panel_C', 'Seam', 'Plinth', 'Road', 'Sidewalk', 'Curb', 'Lawn',
                                   'Sand', 'BarkPoplar', 'BarkBirch', 'GarageWall', 'GarageDoor', 'BrickRed',
                                   'Rust', 'PaintOrange', 'PaintBlue', 'PaintRed',
                                   'Pole', 'Roof', 'BgPanels')}
def glow(name, c, s): return mat(name, color=c, emit=(c, s), rough=.3)
PROP = dict(door=mat('M_Prop_EntranceDoor', 'T_Prop_EntranceDoor', explicit=True), notices=mat('M_Prop_Notices', 'T_Prop_Notices', explicit=True),
            container=mat('M_Prop_Container', 'T_Prop_Container', explicit=True), garage=mat('M_Prop_GarageDoors', 'T_Prop_GarageDoors', explicit=True),
            twigs=mat('M_Prop_Twigs', 'T_Prop_Twigs', alpha=True, explicit=True), fence=mat('M_Prop_Fence', 'T_Prop_Fence', alpha=True, explicit=True),
            leafcard=mat('M_Prop_LeafCard', 'T_Decal_Leaves', alpha=True, explicit=True))
def uvquad(bm, pts, mi, uvr=(0, 0, 1, 1)):
    f = quad(bm, pts, mi); uvl_ = bm.loops.layers.uv.get('UVMap') or bm.loops.layers.uv.new('UVMap')
    for l, uv_ in zip(f.loops, ((uvr[0], uvr[1]), (uvr[2], uvr[1]), (uvr[2], uvr[3]), (uvr[0], uvr[3]))): l[uvl_].uv = uv_
    return f
def DMAT(tex, rough=1.0): return mat('M_' + tex[2:], tex, alpha=True, explicit=True, rough=rough)
def tglow(name, tex, s):
    m = tm(tex); nt = m.node_tree; b = nt.nodes.get('Principled BSDF'); img = [n for n in nt.nodes if n.type == 'TEX_IMAGE'][0]
    nt.links.new(img.outputs['Color'], b.inputs['Emission Color']); b.inputs['Emission Strength'].default_value = s
    return m
G = dict(dark=mat('M_Ext_GlassDark', color=(.02, .025, .035), rough=.12), warm=glow('M_Ext_GlassWarm', (1, .72, .38), 2.2),
         tv=glow('M_Ext_GlassTV', (.35, .5, 1), 1.4), dim=glow('M_Ext_GlassDim', (.9, .7, .45), .5),
         stair=glow('M_Ext_GlassStair', (.75, .85, .7), .8), vent=mat('M_Ext_VentDark', color=(.01, .01, .01)))
CURT = [tglow('T_Ext_Curtain_%d' % i, 'T_Ext_Curtain_%d' % i, 1.6) for i in (1, 2, 3, 4)]
M2 = dict(handle=mat('M_Metal_Dark', color=(.10, .09, .08), rough=.6), steel=mat('M_Metal_Grey', color=(.3, .3, .3), rough=.5),
          wire=mat('M_Wire', color=(.05, .05, .05), rough=.8), plastic=mat('M_Plastic_Dark', color=(.05, .05, .05), rough=.7),
          cream=mat('M_Plastic_Cream', color=(.75, .70, .58), rough=.6), bulb=glow('M_Ext_BulbWarm', (1, .8, .5), 8.0),
          bulb_dead=mat('M_Lamp_DeadGlass', color=(.55, .52, .46), rough=.4), sodium=glow('M_Ext_Sodium', (1, .55, .2), 9.0),
          sodium_dead=mat('M_Ext_SodiumDead', color=(.25, .2, .15), rough=.3), tire=pm('LiftCab_Floor'), glass=mat('M_Ext_CarGlass', color=(.02, .02, .025), rough=.1),
          headl=mat('M_Ext_CarLamp', color=(.6, .6, .55), rough=.2), moon=glow('M_Ext_Moon', (.75, .8, .9), 3.0),
          tirepaint=mat('M_Ext_TirePaintWhite', color=(.55, .55, .52)), tirepaint2=mat('M_Ext_TirePaintBlue', color=(.2, .3, .45)),
          number=mat('M_Ext_HouseNumber', 'T_Ext_HouseNumber', explicit=True), bignum=mat('M_Decal_FloorNumber', 'T_FloorNumber_7', alpha=True, explicit=True))
LIGHTS = []
def light(n, kind, loc, e, c, rot=None, size=None):
    d = bpy.data.lights.new(n, kind); d.energy = e; d.color = c; d.shadow_soft_size = .05
    if kind == 'SPOT': d.spot_size = math.radians(size or 120); d.spot_blend = .6
    o = bpy.data.objects.new(n, d); o.location = loc
    if rot: o.rotation_euler = rot
    col('Lights').objects.link(o)

# ================================================================ panel building
def building(name, org, rot, types, nf, fh, pz, ents, depth=12.0, roofrooms=True, seed=1):
    """facade along local +x at y=0, facing -y. types: per 3 m bay 'win' | 'balc' | 'ent'. ents: state per entrance"""
    rnd = random.Random(seed); T_ = tf(org, rot); nb = len(types); Wd = nb * 3.0; top = pz + nf * fh; ztop = top + .7
    P = lambda x, y, z: T_((x, y, z))
    pmat = [E['Plinth'], E['Panel_A'], E['Panel_B'], E['Panel_C'], E['Seam']]
    fac, frames, glass, bars, extra, dec = bmesh.new(), bmesh.new(), bmesh.new(), bmesh.new(), bmesh.new(), bmesh.new()
    duv = dec.loops.layers.uv.new('UVMap')
    def wdec(u0, u1, z0, z1, w, mi, uvr=(0, 0, 1, 1), fn=None):
        fn = fn or (lambda u, z: P(u, -w, z)); f = quad(dec, [fn(u0, z0), fn(u1, z0), fn(u1, z1), fn(u0, z1)], mi)
        for l, uv_ in zip(f.loops, ((uvr[0], uvr[1]), (uvr[2], uvr[1]), (uvr[2], uvr[3]), (uvr[0], uvr[3]))): l[duv].uv = uv_
    gm = [G['dark'], G['warm'], G['tv'], G['dim'], G['stair'], G['vent']] + CURT + [tm('T_Wood_Frame_M'), pm('Door_SteelBrown')]
    GI = {k: i for i, k in enumerate(['dark', 'warm', 'tv', 'dim', 'stair', 'vent', 'c1', 'c2', 'c3', 'c4', 'panel', 'door'])}
    def gstate(kind):
        r = rnd.random()
        if kind == 'stairwin': return 'stair' if r < .5 else ('dim' if r < .6 else 'dark')
        if r < .11: return 'warm'
        if r < .17: return 'c%d' % rnd.randint(1, 4)
        if r < .2: return 'tv'
        if r < .22: return 'dim'
        return 'dark'
    def seams(b):
        if types[b] == 'ent': return [pz + fh * (i + .5) for i in range(1, nf)]
        return [pz + fh * i for i in range(1, nf)]
    ent_i = 0; entrances = []
    for b, t in enumerate(types):
        bx, cx = b * 3.0, b * 3.0 + 1.5; ops = []
        for i in range(nf):
            fz = pz + fh * i
            if t == 'win' or (t == 'balc' and i == 0): ops.append((cx - .75, cx + .75, fz + .85, fz + 2.3, 'window', i))
            elif t == 'balc':
                ops.append((cx - 1.025, cx - .275, fz + .05, fz + 2.2, 'bdoor', i)); ops.append((cx - .15, cx + 1.05, fz + .85, fz + 2.3, 'window', i))
        if t == 'ent':
            ops.append((cx - .55, cx + .55, .45, 2.5, 'entrance', 0))
            for i in range(nf - 1):
                zb = pz + fh * (i + .5) + 1.0; ops.append((cx - .6, cx + .6, zb, zb + 1.2, 'stairwin', i))
            entrances.append((cx, ents[ent_i])); ent_i += 1
        else: ops.append((cx - .2, cx + .2, .22, .47, 'vent', 0))
        sz = seams(b)
        xs = sorted({bx, bx + 3.0} | {v for o in ops for v in o[:2]})
        zs = sorted({-.1, pz, top, ztop} | set(sz) | {v for o in ops for v in o[2:4]})
        rows = [pz] + sz + [top]; pal = [rnd.randint(1, 3) for _ in rows]
        for xi in range(len(xs) - 1):
            for zi in range(len(zs) - 1):
                x0, x1, z0, z1 = xs[xi], xs[xi + 1], zs[zi], zs[zi + 1]; xc, zc = (x0 + x1) / 2, (z0 + z1) / 2
                if any(o[0] <= xc <= o[1] and o[2] <= zc <= o[3] for o in ops): continue
                if zc < pz: mi = 0
                elif zc > top: mi = 1
                else: mi = pal[max(k for k, r in enumerate(rows) if r <= zc)]
                quad(fac, [P(x0, 0, z0), P(x1, 0, z0), P(x1, 0, z1), P(x0, 0, z1)], mi)
        for x0, x1, z0, z1, kind, i in ops:          # reveals + fillers
            d = .15 if kind == 'vent' else .18
            mi = 0 if z0 < pz and kind in ('vent', 'entrance') else pal[max(k for k, r in enumerate(rows) if r <= (z0 + z1) / 2)] if pz <= (z0 + z1) / 2 <= top else 1
            quad(fac, [P(x0, 0, z0), P(x0, d, z0), P(x0, d, z1), P(x0, 0, z1)], mi); quad(fac, [P(x1, d, z0), P(x1, 0, z0), P(x1, 0, z1), P(x1, d, z1)], mi)
            quad(fac, [P(x0, 0, z0), P(x1, 0, z0), P(x1, d, z0), P(x0, d, z0)], mi); quad(fac, [P(x0, d, z1), P(x1, d, z1), P(x1, 0, z1), P(x0, 0, z1)], mi)
            if kind == 'vent': quad(glass, [P(x0, d, z0), P(x1, d, z0), P(x1, d, z1), P(x0, d, z1)], GI['vent']); continue
            if kind == 'entrance': continue
            st = gstate(kind); wf = lambda u, z, w: P(u, .08 - w, z)        # frame wall-coords: w toward the street
            for a in ((x0, x0 + .06, z0, z1), (x1 - .06, x1, z0, z1), (x0 + .0605, x1 - .0605, z1 - .06, z1), (x0 + .0605, x1 - .0605, z0, z0 + .06)):
                lbox(frames, wf, a[0], a[1], a[2], a[3], -.06, 0, 0)
            if x1 - x0 > 1.3: lbox(frames, wf, (x0 + x1) / 2 - .03, (x0 + x1) / 2 + .03, z0 + .06, z1 - .06, -.06, 0, 0)
            if kind == 'bdoor':
                lbox(frames, wf, x0 + .0605, x1 - .0605, z0 + .9, z0 + .96, -.06, 0, 0)
                quad(glass, [P(x0, .11, z0), P(x1, .11, z0), P(x1, .11, z0 + .93), P(x0, .11, z0 + .93)], GI['panel'])
                quad(glass, [P(x0, .11, z0 + .93), P(x1, .11, z0 + .93), P(x1, .11, z1), P(x0, .11, z1)], GI[st])
            else:
                quad(glass, [P(x0, .11, z0), P(x1, .11, z0), P(x1, .11, z1), P(x0, .11, z1)], GI[st])
                if kind == 'window': lbox(extra, lambda u, z, w: P(u, -w, z), x0 - .03, x1 + .03, z0 - .03, z0, 0, .06, 2)      # tin sill
                if kind == 'window' and i > 0 and rnd.random() < .4:                                                       # rain streaks under the sill
                    L = rnd.uniform(.8, 2.0); wdec(x0 + .05, x1 - .05, z0 - .05 - L, z0 - .05, .004, 0, (0, 0, rnd.choice((1, -1)) * (x1 - x0) / 1.4, 1))
            if kind == 'window' and i == 0:                                                                                     # bars, ground floor
                bw = lambda u, z, w: P(u, -w, z)
                for a in ((x0 - .05, x1 + .05, z0 - .05, z0 - .02), (x0 - .05, x1 + .05, z1 + .02, z1 + .05), (x0 - .05, x1 + .05, (z0 + z1) / 2 - .015, (z0 + z1) / 2 + .015)):
                    lbox(bars, bw, a[0], a[1], a[2], a[3], .07, .085)
                n = int((x1 - x0 + .1) / .15)
                for k in range(n + 1):
                    u = x0 - .05 + .015 + k * (x1 - x0 + .1 - .03) / n; lbox(bars, bw, u - .008, u + .008, z0 - .02, z1 + .02, .072, .083)
                for u in (x0 - .04, x1 + .015):
                    for z in (z0 - .046, z1 + .025): lbox(bars, bw, u, u + .025, z, z + .011 if z < z0 else z + .02, 0, .07)
        if t == 'balc':
            for i in range(1, nf):
                fz = pz + fh * i; x0, x1 = bx + .1, bx + 2.9; bm_ = extra; pt = rnd.choice([1, 3, 6, 7]); glazed = rnd.random() < .35
                lbox(bm_, lambda u, z, w: P(u, -w, z), x0, x1, fz - .15, fz, 0, 1.1, 1)
                lbox(bm_, lambda u, z, w: P(u, -w, z), x0, x1, fz - .01, fz + 1.0, 1.04, 1.1, pt)
                for a in (x0 + .001, x1 - .061): lbox(bm_, lambda u, z, w: P(u, -w, z), a, a + .06, fz - .01, fz + .99, 0, 1.045, pt)
                if glazed:
                    for k in range(5):
                        u = x0 + k * (x1 - x0 - .05) / 4; lbox(frames, lambda u_, z, w: P(u_, -w, z), u, u + .05, fz + 1.0, fz + fh - .2, 1.04, 1.1, 0)
                    lbox(frames, lambda u_, z, w: P(u_, -w, z), x0 - .005, x1 + .005, fz + fh - .2, fz + fh - .15, 1.035, 1.105, 0)
                    quad(glass, [P(x0, -1.07, fz + 1.0), P(x1, -1.07, fz + 1.0), P(x1, -1.07, fz + fh - .2), P(x0, -1.07, fz + fh - .2)], GI[gstate('window')])
                elif rnd.random() < .3:
                    lbox(bm_, lambda u, z, w: P(u, -w, z), x0 + .3, x0 + .8, fz, fz + .45, .55, 1.0, 5)
        # seams
        for z in [pz] + sz:
            if (t == 'ent' and z < 3.0) or (t == 'balc' and z > pz + .1): continue
            lbox(extra, lambda u, z_, w: P(u, -w, z_), bx + .021, bx + 2.979, z - .015, z + .015, 0, .012, 0)
        lbox(extra, lambda u, z, w: P(u, -w, z), bx - .02, bx + .02, pz, ztop, 0, .012, 0)
    lbox(extra, lambda u, z, w: P(u, -w, z), Wd - .02, Wd + .02, pz, ztop, 0, .012, 0)
    # ends, back, roof (single-sided)
    quad(fac, [P(0, depth, -.1), P(0, 0, -.1), P(0, 0, ztop), P(0, depth, ztop)], 1); quad(fac, [P(Wd, 0, -.1), P(Wd, depth, -.1), P(Wd, depth, ztop), P(Wd, 0, ztop)], 2)
    quad(fac, [P(Wd, depth, -.1), P(0, depth, -.1), P(0, depth, ztop), P(Wd, depth, ztop)], 3); quad(fac, [P(0, 0, top), P(Wd, 0, top), P(Wd, depth, top), P(0, depth, top)], 4)
    for i in range(1, nf + 1):
        z = pz + fh * i
        lbox(extra, lambda u, z_, w: P(-w, u, z_), .02, depth - .02, z - .015, z + .015, 0, .012, 0)
        lbox(extra, lambda u, z_, w: P(Wd + w, u, z_), .02, depth - .02, z - .015, z + .015, 0, .012, 0)
    for b_ in (fac, glass): bmesh.ops.remove_doubles(b_, verts=b_.verts[:], dist=1e-4)
    o = make(name + '_Facade', fac, name, pmat[:4] + [E['Roof']], recalc=False)
    make(name + '_WindowFrames', frames, name, [tm('T_Wood_Frame_M')])
    make(name + '_Glass', glass, name, gm, recalc=False)
    make(name + '_Bars', bars, name, [M2['handle']])
    make(name + '_Details', extra, name, [E['Seam'], E['Panel_C'], M2['steel'], E['GarageDoor'], E['Rust'], pm('Cardboard'), pm('Mailbox'), pm('ElectricPanel')])
    for b, t in enumerate(types):                                                                                  # splash grime on the plinth
        if t != 'ent': wdec(b * 3.0 + .02, b * 3.0 + 2.98, -.1, 1.1, .005, 2, (0, 0, 1.5, 1))
    wdec(.02, depth - .02, -.1, 1.1, 0, 2, (0, 0, depth / 2, 1), fn=lambda u, z: P(-.005, depth - u, z))
    wdec(.02, depth - .02, -.1, 1.1, 0, 2, (0, 0, depth / 2, 1), fn=lambda u, z: P(Wd + .005, u, z))
    # drainpipes on seams
    bm_ = bmesh.new()
    for k in sorted({0, nb // 3, 2 * nb // 3, nb}):
        x = k * 3.0 + (.25 if k == 0 else -.25 if k == nb else 0); y = -.14; off = 0 if k in (0, nb) else -.0125
        cyl(bm_, P(x, y, .35), P(x, y, ztop - .1), .06, 8, 0); wbox(bm_, *[[min(a, b) for a, b in zip(P(x - .12, y - .1, ztop - .1), P(x + .12, off, ztop + .05))], [max(a, b) for a, b in zip(P(x - .12, y - .1, ztop - .1), P(x + .12, off, ztop + .05))]], 0)
        cyl(bm_, P(x, y, .41), P(x, y - .35, .12), .06, 8, 0)
        for z in range(2, int(ztop) - 1, 3):
            p, q = P(x - .03, -.08, z), P(x + .03, off, z + .04); wbox(bm_, [min(a, b) for a, b in zip(p, q)], [max(a, b) for a, b in zip(p, q)], 0)
            if rnd.random() < .6: wdec(x - .09, x + .09, z - rnd.uniform(.4, 1.0), z, -off + .002 + (0 if off else .002), 1, (0, 0, .4, 1))   # rust bleeding from the bracket
    make(name + '_Drainpipes', bm_, name, [pm('Bucket')])
    make(name + '_Decals', dec, name, [DMAT('T_Decal_RainStreaks'), DMAT('T_Decal_RustStreaks'), DMAT('T_Decal_PlinthGrime')], recalc=False)
    if roofrooms:
        bm_ = bmesh.new()
        for cx, _ in entrances:
            p, q = P(cx - 1.5, 4, top), P(cx + 1.5, 8.5, top + 2.6); wbox(bm_, [min(a, b) for a, b in zip(p, q)], [max(a, b) for a, b in zip(p, q)], 0)
        for x in (5.0, Wd * .55, Wd - 4):
            cyl(bm_, P(x, 6, top), P(x, 6, top + 4.5), .03, 5, 1)
            for z in (top + 3.0, top + 3.6, top + 4.2): cyl(bm_, P(x - .6, 6, z), P(x + .6, 6, z), .012, 4, 1)
        make(name + '_Roof', bm_, name, [E['Panel_B'], M2['steel']])
    # entrances
    for k, (cx, state) in enumerate(entrances):
        nm = '%s_Entrance%d' % (name, k + 1); bm_ = bmesh.new(); bw = lambda u, z, w: P(u, -w, z)
        lbox(bm_, bw, cx - 1.1, cx + 1.1, 0, .45, 0, .9, 0); lbox(bm_, bw, cx - 1.099, cx + 1.099, .001, .30, .89, 1.2, 0); lbox(bm_, bw, cx - 1.098, cx + 1.098, .002, .15, 1.19, 1.5, 0)
        lbox(bm_, bw, cx - 1.4, cx + 1.4, 2.7, 2.85, 0, 1.6, 1)
        for u in (cx - 1.29, cx + 1.21): lbox(bm_, bw, u, u + .08, 0, 2.7, 1.42, 1.5, 2)
        make(nm + '_Steps_Canopy', bm_, name, [pm('Concrete'), E['Plinth'], M2['steel']])
        bm_ = bmesh.new(); dw_ = lambda u, z, w: P(u, .14 - w, z)
        fs_ = lbox(bm_, dw_, cx - .546, cx + .546, .45, 2.496, 0, .04, 0); set_uv(bm_, fs_, dw_, cx - .546, cx + .546, .45, 2.496)
        lbox(bm_, dw_, cx + .36, cx + .48, 1.18, 1.21, .04, .09, 1); lbox(bm_, dw_, cx - .52, cx - .46, 1.1, 1.3, .04, .05, 1)
        make(nm + '_Door', bm_, name, [PROP['door'], M2['handle']], origin=dw_(cx - .546, .45, .02))
        bm_ = bmesh.new()
        lbox(bm_, bw, cx + .72, cx + .9, 1.42, 1.78, 0, .035, 0)
        for r_ in range(4):
            for c_ in range(3): lbox(bm_, bw, cx + .74 + c_ * .05, cx + .78 + c_ * .05, 1.46 + r_ * .05, 1.5 + r_ * .05, .035, .04, 1)
        lbox(bm_, bw, cx + .75, cx + .87, 1.68, 1.74, .035, .038, 2)
        for (a, b, z0, z1, cell) in ((-1.25, -.85, 1.25, 1.83, (0, 0, .5, 1)), (.95, 1.29, 1.45, 1.95, (.5, 0, 1, 1))):
            fs_ = lbox(bm_, bw, cx + a, cx + b, z0, z1, 0, .002, 3); set_uv(bm_, fs_, bw, cx + a, cx + b, z0, z1, cell)
        make(nm + '_Intercom_Notices', bm_, name, [M2['steel'], M2['cream'], M2['plastic'], PROP['notices']])
        bm_ = bmesh.new(); hc = P(cx, -.45, 2.7)
        cyl(bm_, (hc[0], hc[1], 2.62), (hc[0], hc[1], 2.7), .08, 8, 0); sphere(bm_, (hc[0], hc[1], 2.58), .05, 1, 1, 6, 4)
        for a in range(4):
            ang = a * math.pi / 2; cyl(bm_, (hc[0] + .07 * math.cos(ang), hc[1] + .07 * math.sin(ang), 2.48), (hc[0] + .07 * math.cos(ang), hc[1] + .07 * math.sin(ang), 2.62), .006, 4, 0)
        make(nm + '_Lamp' + {'lit': '', 'dead': '_Dead', 'flicker': '_Flicker'}[state], bm_, name, [M2['handle'], M2['bulb_dead'] if state == 'dead' else M2['bulb']], origin=hc)
        if state != 'dead': light('Light_' + nm, 'POINT', (hc[0], hc[1], 2.45), 45 if state == 'lit' else 25, (1, .78, .5))
        if k == 1 or len(entrances) == 1:
            bm_ = bmesh.new(); fs = lbox(bm_, bw, cx - 1.35, cx - .95, 2.25, 2.45, 0, .004); set_uv(bm_, fs, bw, cx - 1.35, cx - .95, 2.25, 2.45)
            make(nm + '_HouseNumber', bm_, name, [M2['number']], origin=P(cx - 1.15, 0, 2.25))
    return T_, P, Wd, entrances

TA, PA, WA, ENTA = building('BuildingA', (0, 0), 0, ['win', 'balc', 'ent', 'win', 'balc', 'win', 'balc', 'ent', 'balc', 'win', 'balc', 'win', 'ent', 'balc', 'win'],
                            9, 2.8, .9, ['dead', 'lit', 'flicker'], seed=3)
TB, PB, WB, ENTB = building('BuildingB', (-6, -50), 90, ['win', 'balc', 'win', 'ent', 'win', 'balc', 'balc', 'win', 'ent', 'win', 'balc', 'win'],
                            5, 2.7, .6, ['lit', 'dead'], roofrooms=False, seed=11)
EW_ = lambda u, z, w: (45 + w, u, z)       # east end wall of A, seen from the yard (single quad: alpha decal)
bm = bmesh.new(); fs = quad(bm, [EW_(4.75, 17.85, .004), EW_(7.25, 17.85, .004), EW_(7.25, 20.35, .004), EW_(4.75, 20.35, .004)], 0); fs.normal_update()
if fs.normal.x < 0: fs.normal_flip()
set_uv(bm, fs, EW_, 4.75, 7.25, 17.85, 20.35)
make('BuildingA_EndNumber', bm, 'BuildingA', [M2['bignum']], origin=(45, 6, 17.85), recalc=False)

# ================================================================ ground, road, sidewalks
bm = bmesh.new(); wbox(bm, (-70, -120, -.1), (120, 40, -.05)); make('Ground', bm, 'Street', [E['Lawn']])
def slab(name, x0, y0, x1, y1, m, z1=0.0, z0=-.05):
    bm = bmesh.new(); wbox(bm, (x0, y0, z0), (x1, y1, z1)); return make(name, bm, 'Street', [m], origin=((x0 + x1) / 2, (y0 + y1) / 2, z0))
slab('Apron_A', -.6, -1.0, 45.6, 0, pm('Concrete')); slab('Sidewalk_A', -25, -6.0, 75, -4.0, E['Sidewalk'])
slab('Curb_1', -25, -6.15, 75, -6.0, E['Curb'], .12); slab('Road', -30, -12.0, 80, -6.15, E['Road']); slab('Curb_2', -30, -12.15, 80, -12.0, E['Curb'], .12)
for i, (cx, _) in enumerate(ENTA): slab('Path_EntranceA%d' % (i + 1), cx - 1.4, -4.0, cx + 1.4, -1.0, E['Sidewalk'])
slab('Path_Yard', 1.0, -40, 3.0, -12.15, E['Sidewalk']); slab('Path_Garages', 3.0, -38.2, 45, -36.6, E['Sidewalk'])
slab('Apron_B', -6.0, -50, -5.0, -14, pm('Concrete')); slab('Sidewalk_B', -5.0, -50, -3.0, -12.15, E['Sidewalk'])
for i, (cx, _) in enumerate(ENTB): slab('Path_EntranceB%d' % (i + 1), -3.0, -50 + cx - 1.4, 1.0, -50 + cx + 1.4, E['Sidewalk'])
slab('TrashArea_Slab', 38, -20, 44, -14, pm('Concrete'))

# ================================================================ ground decals: break the tiling
DR = random.Random(77)
def dq(bm, uvl, x, y, z, sx, sy, rot, mi, uvr=(0, 0, 1, 1)):
    c, s_ = math.cos(math.radians(rot)), math.sin(math.radians(rot)); pts = []
    for (a, b), uv_ in zip(((-sx / 2, -sy / 2), (sx / 2, -sy / 2), (sx / 2, sy / 2), (-sx / 2, sy / 2)), ((uvr[0], uvr[1]), (uvr[2], uvr[1]), (uvr[2], uvr[3]), (uvr[0], uvr[3]))):
        pts.append(((x + a * c - b * s_, y + a * s_ + b * c, z), uv_))
    f = quad(bm, [p for p, _ in pts], mi)
    for l, (_, uv_) in zip(f.loops, pts): l[uvl].uv = uv_
ASPH = [(-28, -11.8, 78, -6.4), (-23, -5.9, 73, -4.1)]                      # road, sidewalk A
LAWN_BLOCK = [(8, -31, 22, -16), (38, -20, 44, -14), (1, -40, 3, -12), (-6, -50, 1, -12), (19, -44.5, 45, -36.5), (0, -1, 45, 0)]
def free_lawn(x, y, r):
    if not (-2 < x < 50 and -36 < y < -12.5 or -20 < x < 60 and -1 < y < 0): return False
    return not any(a - r < x < c + r and b - r < y < d + r for a, b, c, d in LAWN_BLOCK)
# --- asphalt layers 2 mm apart: patches, cracks, oil, manholes, leaves, puddles; no overlaps inside a layer
bm = bmesh.new(); uvl = bm.loops.layers.uv.new('UVMap'); LAY = defaultdict(list)
def put(layer, z, x, y, sx, sy, rot, mi, uvr=(0, 0, 1, 1)):
    r = math.hypot(sx, sy) / 2
    if any(math.hypot(x - a, y - b) < r + c for a, b, c in LAY[layer]): return False
    LAY[layer].append((x, y, r)); dq(bm, uvl, x, y, z, sx, sy, rot, mi, uvr); return True
def scatter(layer, z, n, area, smin, smax, mi, flat=1.0, rot=(0, 360), uvf=None):
    k = t = 0
    while k < n and t < 600:
        t += 1; sx = DR.uniform(smin, smax); sy = min(sx * DR.uniform(flat, 1.0), area[3] - area[1] - .1)
        x, y = DR.uniform(area[0] + sx / 2, area[2] - sx / 2), DR.uniform(area[1] + sy / 2, area[3] - sy / 2)
        if put(layer, z, x, y, sx, sy, DR.uniform(*rot), mi, uvf() if uvf else (0, 0, 1, 1)): k += 1
scatter('patch', .002, 12, ASPH[0], 1.0, 3.2, 0, .5, (-6, 6)); scatter('patch', .002, 4, ASPH[1], .8, 1.6, 0, .6, (-6, 6))
flip = lambda: (0, 0, DR.choice((1, -1)), 1)
scatter('crack', .004, 13, ASPH[0], 1.8, 3.4, 1, .9, uvf=flip); scatter('crack', .004, 6, ASPH[1], 1.4, 1.8, 1, uvf=flip); scatter('crack', .004, 3, (1.05, -39, 2.95, -13), 1.4, 1.8, 1, uvf=flip)
for (x, y) in ((13.4, -7.0), (12.2, -7.3), (31.0, -7.1), (56.5, -7.2), (6.8, -11.0), (24.0, -37.4), (35.5, -37.5), (21.5, -37.2)):
    put('oil', .006, x + DR.uniform(-.3, .3), y + DR.uniform(-.2, .2), DR.uniform(.6, 1.2), DR.uniform(.5, .9), DR.uniform(0, 360), 2)
for (x, y, k) in ((20.5, -9.0, 3), (48.0, -8.4, 4), (33.0, -5.0, 3)): put('manhole', .008, x, y, .66, .66, DR.uniform(0, 90), k)
for edge in (-6.45, -11.75):
    x = -26.0
    while x < 76:
        x += DR.uniform(1.0, 3.0)
        if DR.random() < .7: put('leaves', .010, x, edge + DR.uniform(-.08, .08), DR.uniform(.8, 1.6), DR.uniform(.4, .6), DR.uniform(-8, 8), 5, (0, 0, DR.uniform(1, 2), 1))
for (x, y) in ((2.0, -21), (1.8, -33), (6, -37.3), (15, -37.5), (24.5, -4.6), (18, -5.2), (0.5, -5.0), (-4.0, -30)): put('leaves', .010, x, y, DR.uniform(.9, 1.4), DR.uniform(.7, 1.1), DR.uniform(0, 360), 5)
PUD = [(16, -9.0, 2.6, 1.5, 0), (27.5, -10.6, 1.8, 1.1, 1), (7.5, -8.3, 1.5, 1.0, 0), (44, -9.6, 2.2, 1.3, 1), (61, -10.4, 2.0, 1.2, 0), (-8, -9.0, 2.4, 1.3, 1),
       (40, -5.0, 1.2, .8, 0), (12, -4.7, 1.0, .7, 1), (2.0, -27.5, 1.3, .9, 0), (2.1, -17.0, 1.0, .7, 1), (30, -37.4, 2.2, 1.2, 0), (41, -15.6, 1.3, .9, 1), (-4, -20, 1.2, .9, 0)]
for (x, y, sx, sy, k) in PUD: put('puddle', .012, x, y, sx, sy, DR.uniform(-20, 20), 6 + k)
make('Decal_Asphalt', bm, 'Decals', [DMAT('T_Decal_AsphaltPatch'), DMAT('T_Decal_Cracks'), DMAT('T_Decal_OilStain'), DMAT('T_Decal_Manhole_1', .4), DMAT('T_Decal_Manhole_2', .4),
                                     DMAT('T_Decal_Leaves'), DMAT('T_Decal_Puddle_1', .03), DMAT('T_Decal_Puddle_2', .03)], recalc=False)
# --- ground: blend patches -.048, trodden paths -.044, leaves -.043, puddles -.040
bm = bmesh.new(); uvl = bm.loops.layers.uv.new('UVMap'); placed = []
tries = 0
while len(placed) < 34 and tries < 4000:
    tries += 1; x, y = DR.uniform(-2, 50), DR.uniform(-36, -12.8); r = DR.uniform(1.2, 3.2)
    if not free_lawn(x, y, r * .6) or any(math.hypot(x - a, y - b) < r * 1.42 + c for a, b, c in placed): continue
    placed.append((x, y, r * 1.42)); dq(bm, uvl, x, y, -.048, r * 2, r * 2 * DR.uniform(.7, 1.0), DR.uniform(0, 360), DR.randint(0, 3))
for (x, y, r) in ((4.5, -2.4, 1.2), (13.5, -2.6, 1.0), (31, -2.4, 1.1), (42, -2.6, 1.0), (17.5, -2.4, 1.1), (36, -2.5, 1.0)): dq(bm, uvl, x, y, -.048, r * 2, 2.5, DR.uniform(0, 30), DR.choice((2, 3)))
def trod(pts, w=.9):
    v = 0.0; seg = 0
    for (ax_, ay), (bx_, by) in zip(pts, pts[1:]):
        L = math.hypot(bx_ - ax_, by - ay); nx, ny = -(by - ay) / L * w / 2, (bx_ - ax_) / L * w / 2
        zz = -.046 + .0012 * seg; seg += 1
        f = quad(bm, [(ax_ - nx, ay - ny, zz), (ax_ + nx, ay + ny, zz), (bx_ + nx, by + ny, zz), (bx_ - nx, by - ny, zz)], 4)
        for l, uv_ in zip(f.loops, ((0, v), (1, v), (1, v + L / 2.5), (0, v + L / 2.5))): l[uvl].uv = uv_
        v += L / 2.5
dq(bm, uvl, 15, -23.5, -.047, 17, 18, 4, 7)                                    # trampled playground ground
trod([(3.0, -33.5), (7, -34.6), (12, -35.6), (18.5, -36.5)]); trod([(1.0, -24.5), (4.0, -23.4), (8.0, -22.6)])
trod([(23.5, -12.3), (28, -13.4), (33, -14.6), (37.8, -16.5)]); trod([(22, -31), (26, -33.5), (29, -36.4)], .7)
for (x, y) in ((6, -14.5), (25, -14.6), (34, -30), (46.5, -22), (5.5, -32), (28, -33), (-2, -20), (-1.5, -44)):
    dq(bm, uvl, x + DR.uniform(-.5, .5), y + DR.uniform(-.5, .5), -.040, DR.uniform(2.5, 3.6), DR.uniform(2.5, 3.6), DR.uniform(0, 360), 5)
for (x, y, sx, sy) in ((14.5, -23.5, 1.8, 1.2), (19, -28.2, 1.3, .9), (27, -24, 1.6, 1.0), (9.5, -14.2, 1.4, 1.0)): dq(bm, uvl, x, y, -.038, sx, sy, DR.uniform(0, 360), 6)
make('Decal_Ground', bm, 'Decals', [DMAT('T_Decal_GroundMoss'), DMAT('T_Decal_GroundDryGrass'), DMAT('T_Decal_GroundLeaves'), DMAT('T_Decal_GroundMud'),
                                    DMAT('T_Decal_TrodPath'), DMAT('T_Decal_LeafPile'), DMAT('T_Decal_Puddle_1', .03), DMAT('T_Decal_MudArea')], recalc=False)
# ================================================================ palisade fences, tires, benches, urn
bm = bmesh.new(); posts = bmesh.new(); POSTS = set(); fm = pm('ElectricPanel'); segs = [(.2, 6.0), (9.0, 21.0), (24.0, 36.0), (39.0, 44.8)]
def fence_run(p0, p1):
    L = math.dist(p0, p1); n = max(1, round(L / 2.0)); d = ((p1[0] - p0[0]) / L, (p1[1] - p0[1]) / L); nx, ny = -d[1] * .002, d[0] * .002
    for k in range(n + 1):
        x, y = p0[0] + d[0] * L * k / n, p0[1] + d[1] * L * k / n
        if (round(x, 2), round(y, 2)) in POSTS: continue
        POSTS.add((round(x, 2), round(y, 2))); wbox(posts, (x - .03, y - .03, -.06), (x + .03, y + .03, .78), 0)
    for k in range(n):
        a0 = (p0[0] + d[0] * (L * k / n + .03), p0[1] + d[1] * (L * k / n + .03)); a1 = (p0[0] + d[0] * (L * (k + 1) / n - .03), p0[1] + d[1] * (L * (k + 1) / n - .03))
        tl = math.dist(a0, a1) / 1.4
        uvquad(bm, [(a0[0] + nx, a0[1] + ny, .02), (a1[0] + nx, a1[1] + ny, .02), (a1[0] + nx, a1[1] + ny, .72), (a0[0] + nx, a0[1] + ny, .72)], 1, (0, 0, tl, 1))
        uvquad(bm, [(a1[0] - nx, a1[1] - ny, .02), (a0[0] - nx, a0[1] - ny, .02), (a0[0] - nx, a0[1] - ny, .72), (a1[0] - nx, a1[1] - ny, .72)], 1, (tl, 0, 0, 1))
for a, b in segs: fence_run((a, -3.92), (b, -3.92)); fence_run((a, -3.92), (a, -1.05)); fence_run((b, -3.92), (b, -1.05))
make('Palisade_FencePanels', bm, 'Street', [fm, PROP['fence']], recalc=False); make('Palisade_FencePosts', posts, 'Street', [fm])
bm = bmesh.new()
for i, (x, y, pm_) in enumerate(((19.6, -2.6, 0), (20.5, -1.9, 1), (25.3, -2.3, 0), (26.2, -3.0, 1))):
    t = bmesh.ops.create_cone(bm, cap_ends=False, segments=10, radius1=.32, radius2=.32, depth=.22)
    for v in t['verts']: v.co += Vector((x, y, .06))
    for f in {f for v in t['verts'] for f in v.link_faces}: f.material_index = pm_
make('Tire_Planters', bm, 'Street', [M2['tirepaint'], M2['tirepaint2']], recalc=False)
def bench(name, x, y, rot, z0=-.04):
    bm = bmesh.new(); O = [(0, 0), (.08, 0), (.12, .38), (.42, .38), (.46, 0), (.54, 0), (.50, .42), (.62, .86), (.555, .875), (.45, .47), (.05, .47)]
    for sx in (-.78, .73): prism(bm, lambda u, z, w: (sx + w, u - .3, z + (z0 if z < .01 else 0)), O, 0, .05, 0)
    for k in range(4): wbox(bm, (-.92, -.27 + k * .105, .47), (.92, -.27 + k * .105 + .085, .505), 1)
    for k in range(3):
        t0, t1 = .18 + k * .28, .18 + k * .28 + .2
        p0 = (.46 + (.56 - .46) * t0, .50 + (.84 - .50) * t0); p1 = (.46 + (.56 - .46) * t1, .50 + (.84 - .50) * t1)
        hexa(bm, lambda a_, t, n: (a_, p0[0] + (p1[0] - p0[0]) * t - .3 + n - .045, p0[1] + (p1[1] - p0[1]) * t - n * .3), (-.92, .92), (0, 1), (0, .03), 1)
    make(name, bm, 'Street', [M2['handle'], pm('Partition_Door')], loc=(x, y, 0), rot=(0, 0, math.radians(rot)))
bench('Bench_EntranceA2', 19.9, -4.6, 0); bench('Bench_Playground', 8.6, -23.5, 90, -.052); bench('Bench_EntranceB1', -3.4, -36.0, 90)
bm = bmesh.new(); cyl(bm, (24.2, -4.6, -.04), (24.2, -4.6, .6), .22, 8, 0, r1=.26); make('Urn_EntranceA2', bm, 'Street', [pm('Concrete')])

# ================================================================ trees
def tree(name, x, y, h, kind, clumps, seed):
    r = random.Random(seed); bm = bmesh.new(); bark = 0
    lean = Vector((r.uniform(-.3, .3), r.uniform(-.3, .3), 0)); top = Vector((x, y, h)) + lean * h * .1
    cyl(bm, (x, y, -.06), top, .22 if kind == 'poplar' else .14, 6, bark, r1=.07)
    tips = []
    def card(p, d, size, mi, uvr=(0, 0, 1, 1)):
        d = d.normalized(); side = d.cross(Vector((0, 0, 1)))
        if side.length < .1: side = Vector((1, 0, 0))
        side.normalize()
        for sd in (side, d.cross(side).normalized()):
            a0, a1 = p - sd * size / 2, p + sd * size / 2
            uvquad(bm, [tuple(a0), tuple(a1), tuple(a1 + d * size), tuple(a0 + d * size)], mi, uvr)
    for k in range(r.randint(6, 8)):
        t = r.uniform(.3, .88); base = Vector((x, y, -.06)).lerp(top, t)
        az = r.uniform(0, 2 * math.pi); el = math.radians(r.uniform(35, 70) if kind == 'poplar' else r.uniform(15, 50))
        L = h * r.uniform(.25, .42) * (1 - t * .4); d = Vector((math.cos(az) * math.cos(el), math.sin(az) * math.cos(el), math.sin(el)))
        tip = base + d * L; cyl(bm, base, tip, .08 * (1 - t * .6), 5, bark, r1=.015); card(tip - d * .2, d, r.uniform(1.2, 1.9), 1)
        for s_ in range(3):
            a2 = az + r.uniform(-.9, .9); e2 = el + r.uniform(-.3, .5); d2 = Vector((math.cos(a2) * math.cos(e2), math.sin(a2) * math.cos(e2), math.sin(e2)))
            b2 = base.lerp(tip, r.uniform(.35, .85)); t2 = b2 + d2 * L * .45; cyl(bm, b2, t2, .03, 4, bark, r1=.008); tips.append((t2, d2))
            card(t2 - d2 * .15, d2, r.uniform(.9, 1.5), 1)
    card(top - Vector((0, 0, .4)), Vector((0, 0, 1)), 1.6, 1)
    for k in range(clumps):
        c, dd = r.choice(tips)
        for j in range(3): card(c + Vector((r.uniform(-.3, .3), r.uniform(-.3, .3), -.4)), Vector((r.uniform(-1, 1), r.uniform(-1, 1), 1.2)), r.uniform(.9, 1.4), 2)
    make(name, bm, 'Trees', [E['BarkPoplar'] if kind == 'poplar' else E['BarkBirch'], PROP['twigs'], PROP['leafcard']], recalc=False)
for i, (x, y, h, k, c) in enumerate(((6, -14.5, 13, 'poplar', 2), (25, -14.6, 14, 'poplar', 0), (34, -30, 12, 'poplar', 3), (46.5, -22, 13, 'poplar', 1),
                                     (5.5, -32, 11, 'poplar', 0), (28, -33, 12, 'poplar', 2), (4.5, -2.5, 8, 'birch', 1), (13.5, -2.6, 9, 'birch', 0),
                                     (31, -2.4, 8.5, 'birch', 2), (42, -2.5, 7.5, 'birch', 0), (-2, -20, 10, 'birch', 1), (-1.5, -44, 12, 'poplar', 0))):
    tree('Tree_%02d' % (i + 1), x, y, h, k, c, 100 + i + (50 if i == 8 else 0) + (20 if i == 3 else 0))

# ================================================================ street lamps + wires
POLES = [(4, -5.7, 'dead'), (20, -5.7, 'lit'), (36, -5.7, 'flicker'), (52, -5.7, 'lit')]
def cobra(bm, p, d, lit):
    """classic Soviet street luminaire: lofted 'cobra' housing with a glass bowl underneath"""
    side = Vector((-d.y, d.x, 0)); st = [(0, .05, .05, -.03), (.16, .14, .10, -.06), (.42, .16, .09, -.07), (.66, .08, .04, -.03)]
    rings = [[bm.verts.new(p + d * t + side * sw * w + Vector((0, 0, z))) for sw, z in ((-1, zt), (1, zt), (1, zb), (-1, zb))] for t, w, zt, zb in st]
    for a, b in zip(rings, rings[1:]):
        for i in range(4): bm.faces.new((a[i], a[(i + 1) % 4], b[(i + 1) % 4], b[i])).material_index = 0
    bm.faces.new(rings[0][::-1]).material_index = 0; bm.faces.new(rings[-1]).material_index = 0
    hexa(bm, lambda a_, t, n: tuple(p + d * (.14 + t * .3) + side * a_ * (.11 - .03 * abs(t - .5)) + Vector((0, 0, -.06 - n))), (-1, 1), (0, 1), (-.005, .04), 1 if lit else 2)
bm = bmesh.new(); heads = bmesh.new(); hm = []
for i, (x, y, st) in enumerate(POLES):
    cyl(bm, (x, y, -.06), (x, y, 8.6), .13, 4, 0, r1=.08)
    wbox(bm, (x - .03, y - .45, 8.3), (x + .03, y + .45, 8.36), 1)
    cyl(bm, (x, y, 7.55), (x, y - .55, 7.98), .035, 6, 1); cyl(bm, (x, y - .52, 7.97), (x, y - 1.45, 8.08), .035, 6, 1)
    cobra(heads, Vector((x, y - 1.42, 8.08)), Vector((0, -1, 0)), st != 'dead')
    if st != 'dead': light('Light_StreetLamp_%d' % (i + 1) + ('_Flicker' if st == 'flicker' else ''), 'SPOT', (x, y - 1.82, 7.95), 900 if st == 'lit' else 500, (1, .55, .2), size=125)
x, y = 9.5, -25.0
cyl(bm, (x, y, -.06), (x, y, 7.0), .12, 4, 0, r1=.08); cyl(bm, (x, y, 6.15), (x + .5, y, 6.5), .035, 6, 1); cyl(bm, (x + .48, y, 6.49), (x + 1.3, y, 6.58), .035, 6, 1)
cobra(heads, Vector((x + 1.27, y, 6.58)), Vector((1, 0, 0)), True)
light('Light_YardLamp', 'SPOT', (x + 1.67, y, 6.45), 500, (1, .6, .25), size=130)
make('StreetLamp_Poles', bm, 'Lamps', [E['Pole'], M2['steel']]); make('StreetLamp_Heads', heads, 'Lamps', [M2['steel'], M2['sodium'], M2['sodium_dead']])
bm = bmesh.new()
for dy in (-.42, .42):
    pts = [(-22, -5.7)] + [(p[0], p[1]) for p in POLES] + [(70, -5.7)]
    for a, b in zip(pts, pts[1:]):
        n = 8; prev = None
        for k in range(n + 1):
            t = k / n; px = a[0] + (b[0] - a[0]) * t; pz = 8.36 - .7 * 4 * t * (1 - t)
            cur = (px, a[1] + dy, pz)
            if prev:
                dd = (Vector(cur) - Vector(prev)).normalized() * .004; cyl(bm, Vector(prev) - dd, Vector(cur) + dd, .01, 4, 0)
            prev = cur
make('Power_Wires', bm, 'Lamps', [M2['wire']])

# ================================================================ playground
bm = bmesh.new()
for x in (11.0, 13.4):
    for dy in (-.85, .85): cyl(bm, (x, -20 + dy, -.052), (x, -20, 2.45), .04, 6, 0)
cyl(bm, (10.9, -20, 2.42), (13.5, -20, 2.42), .045, 6, 0)
for sx in (11.75, 12.65):
    for dy in (-.2, .2): cyl(bm, (sx, -20 + dy, 2.38), (sx, -20 + dy, .5), .006, 4, 1)
    wbox(bm, (sx - .25, -20.24, .45), (sx + .25, -19.76, .5), 2)
make('Swing', bm, 'Playground', [E['PaintBlue'], M2['steel'], pm('Partition_Door')])
bm = bmesh.new()
for a in ((16, -27, 18, -26.9), (16, -25.1, 18, -25), (16.001, -26.92, 16.1, -25.08), (17.9, -26.92, 17.999, -25.08)): wbox(bm, (a[0], a[1], -.052), (a[2], a[3], .28), 0)
wbox(bm, (16.105, -26.895, -.051), (17.895, -25.105, .14), 1); make('Sandbox', bm, 'Playground', [pm('Partition_Wood'), E['Sand']])
bm = bmesh.new(); sx, sy = 19.5, -19.0
for dx in (-.3, .3): cyl(bm, (sx + dx, sy + .6, -.052), (sx + dx, sy, 1.55), .03, 6, 0)
for k in range(5): z = .3 + k * .27; cyl(bm, (sx - .3, sy + .6 - z * .4, z), (sx + .3, sy + .6 - z * .4, z), .018, 6, 0)
wbox(bm, (sx - .35, sy - .5, 1.45), (sx + .35, sy, 1.53), 0)
for dx in (-.33, .33): cyl(bm, (sx + dx, sy - .5, -.052), (sx + dx, sy - .5, 1.45), .03, 6, 0)
hexa(bm, lambda a, t, n: (sx + a, sy - .5 - t * 2.6, 1.45 - t * 1.4 + n), (-.3, .3), (0, 1), (0, .03), 1)
make('Slide', bm, 'Playground', [E['PaintRed'], E['Rust']])
bm = bmesh.new()
for x in (9.6, 11.2): cyl(bm, (x, -28, -.052), (x, -28, 2.2), .04, 6, 0)
cyl(bm, (9.55, -28, 2.1), (11.25, -28, 2.1), .02, 6, 0); make('PullUpBar', bm, 'Playground', [E['PaintOrange']])

# ================================================================ trash area
bm = bmesh.new()
wbox(bm, (38, -20, 0), (44, -19.75, 1.6)); wbox(bm, (38.001, -19.76, .001), (38.25, -15, 1.599)); wbox(bm, (43.75, -19.76, .001), (43.999, -15, 1.599))
make('TrashArea_Walls', bm, 'Street', [E['BrickRed']])
def container(name, x, y, lid_open):
    bm = bmesh.new(); uvl_ = bm.loops.layers.uv.new('UVMap')
    lo, hi = (.62, .42, .13), (.71, .52, 1.12)
    taper = lambda a_, b_, c_, k=0: (x + a_ * (lo[0] + (hi[0] - lo[0]) * c_ + k), y + b_ * (lo[1] + (hi[1] - lo[1]) * c_ + k), lo[2] + (hi[2] - lo[2]) * c_)
    hexa(bm, lambda a_, b_, c_: taper(a_, b_, c_), (-1, 1), (-1, 1), (0, 1), 0)
    for zc in (.45, .85):
        c0, c1 = (zc - lo[2]) / (hi[2] - lo[2]), (zc + .06 - lo[2]) / (hi[2] - lo[2])
        hexa(bm, lambda a_, b_, c_: taper(a_, b_, c0 + (c1 - c0) * c_, .015), (-1, 1), (-1, 1), (0, 1), 1)
    for sx in (-.45, .45): wbox(bm, (x + sx - .05, y - .4, -.002), (x + sx + .05, y + .4, .135), 1)
    for sx in (-1, 1): cyl(bm, (x + sx * .70, y, .95), (x + sx * .80, y, .95), .035, 6, 1)
    for k, sx in enumerate((-1, 1)):
        if lid_open and k == 1: hexa(bm, lambda a_, b_, c_: (x + .003 + a_ * .7, y + .52 + c_ * .03, 1.12 + (b_ + 1) / 2 * 1.0), (0, 1), (-1, 1), (0, 1), 2)
        else: wbox(bm, (x + (-.715 if sx < 0 else .003), y - .53, 1.12), (x + (-.003 if sx < 0 else .715), y + .53, 1.15), 2)
    bm.faces.index_update(); fix_normals(bm)
    for f in bm.faces:
        n_ = f.normal
        for l in f.loops:
            co = l.vert.co
            l[uvl_].uv = (((x - co.x) / 1.42 * (1 if n_.y > 0 else -1) + .5), (co.z - .1) / 1.05) if abs(n_.y) > .7 else ((co.y - y + co.x - x) / 1.4 + .3, co.z / 1.4 * .3 + .1)
    make(name, bm, 'Street', [PROP['container'], M2['handle'], pm('ElectricPanel')], recalc=True)
for i, x in enumerate((38.85, 40.95, 43.0)): container('TrashContainer_%d' % (i + 1), x if i < 2 else 42.95, -19.1, i == 1)
for i, (x, y, r) in enumerate(((39.0, -17.8, .3), (39.6, -17.4, .25), (41.9, -17.9, .28), (42.3, -16.2, .22), (38.7, -15.8, .26))):
    bm = bmesh.new(); sphere(bm, (0, 0, r * .75), r, .75, 0, 8, 6); make('GarbageBag_%02d' % (i + 1), bm, 'Street', [pm('Plastic_Bag')], loc=(x, y, 0))
bm = bmesh.new(); hexa(bm, lambda a, t, n: (43.75 - n - (1 - t / 1.9) * .35, -17.6 + a, t), (0, .9), (0, 1.9), (0, .15), 0)
make('Mattress', bm, 'Street', [pm('Carpet_Rolled')])

# ================================================================ garages
bm = bmesh.new(); doors = bmesh.new(); duv = doors.loops.layers.uv.new('UVMap'); roof = bmesh.new()
def garage_front(x0, x1, g, closed=True):
    gc = (x0 + x1) / 2; cu, cv = (g % 2) * .5, 1 - (g // 2 % 2 + 1) * .5
    for a_, b_ in ((x0 + .1, x0 + .16), (x1 - .16, x1 - .1)): wbox(doors, (a_, -38.0, 0), (b_, -37.96, 2.31), 1)
    wbox(doors, (x0 + .161, -38.0, 2.25), (x1 - .161, -37.96, 2.309), 1)
    if not closed: return
    for k, (a_, b_) in enumerate(((x0 + .16, gc - .005), (gc + .005, x1 - .16))):
        fs_ = wbox(doors, (a_, -37.99, .05), (b_, -37.95, 2.25), 0)
        for l in fs_.loops:
            co = l.vert.co; l[duv].uv = (cu + (b_ - co.x) / (b_ - a_) * .5, cv + (co.z - .05) / 2.2 * .5)
        for rx in (.25, .5, .75): xx = a_ + (b_ - a_) * rx; wbox(doors, (xx - .015, -37.95, .12), (xx + .015, -37.935, 2.18), 1)
    for hx in (x0 + .175, x1 - .175):
        for hz in (.35, 1.15, 1.95): cyl(doors, (hx, -37.94, hz), (hx, -37.94, hz + .12), .022, 6, 1)
    wbox(doors, (gc - .07, -37.95, 1.06), (gc + .07, -37.92, 1.14), 1); wbox(doors, (gc - .035, -37.94, .95), (gc + .035, -37.91, 1.06), 2)
for g in range(8):
    x0 = 20 + g * 3.0; x1 = x0 + 3.0
    hexa(roof, lambda a_, b_, c_: (x0 + .01 + a_ * 2.98, -44.12 + b_ * 6.27, (2.5 - b_ * .2) + (2.5 - b_ * .2 - 2.3) * 0 + c_ * .06 - .001), (0, 1), (0, 1), (0, 1), 0)
    if g == 2: garage_front(x0, x1, g, closed=False); continue
    hexa(bm, lambda a, b, c: (x0 + .02 + a * 2.96, -44 + b * 6, c * (2.5 - b * .2) if c else 0), (0, 1), (0, 1), (0, 1), 0)
    garage_front(x0, x1, g)
make('Garages', bm, 'Garages', [E['GarageWall']]); make('Garage_Doors', doors, 'Garages', [PROP['garage'], M2['handle'], E['Rust']])
make('Garage_Roofs', roof, 'Garages', [E['Roof']])
x0 = 26.0; bm = bmesh.new()
hexa(bm, lambda a, b, c: (x0 + .02 + a * 2.96, -44 + b * 6, c * (2.5 - b * .2) if c else 0), (0, 1), (0, 1), (0, 1), 0)
og = make('Garage_Open', bm, 'Garages', [E['GarageWall']], origin=(x0 + 1.5, -41, 0))
c1 = bmesh.new(); wbox(c1, (x0 + .1, -43.9, .0), (x0 + 2.9, -38.1, 2.2)); c2 = bmesh.new(); wbox(c2, (x0 + .15, -38.5, .0), (x0 + 2.85, -37.5, 2.25)); boolean_cut(og, [c1, c2])
for side, ang in (('L', 100), ('R', -100)):
    bm = bmesh.new(); a, b = (x0 + .16, x0 + 1.495) if side == 'L' else (x0 + 1.505, x0 + 2.84); fs_ = wbox(bm, (a, -37.99, .05), (b, -37.95, 2.25)); u_ = bm.loops.layers.uv.new('UVMap')
    for l in fs_.loops: co = l.vert.co; l[u_].uv = ((b - co.x) / (b - a) * .5 + .5, .5 + (co.z - .05) / 2.2 * .5)
    for rx in (.25, .5, .75): xx = a + (b - a) * rx; wbox(bm, (xx - .015, -37.95, .12), (xx + .015, -37.935, 2.18), 1)
    make('Garage_Open_Door' + side, bm, 'Garages', [PROP['garage'], M2['handle']], origin=((a if side == 'L' else b), -37.97, .05), rot=(0, 0, math.radians(ang)))
bm = bmesh.new(); bulb_c = (x0 + 1.5, -41, 2.2)
cyl(bm, (bulb_c[0], bulb_c[1], 1.75), (bulb_c[0], bulb_c[1], 2.2), .004, 4, 0); sphere(bm, (bulb_c[0], bulb_c[1], 1.71), .04, 1, 1, 6, 4)
wbox(bm, (x0 + .2, -43.8, 0), (x0 + 1.6, -43.2, .9), 2); wbox(bm, (x0 + .18, -43.82, .9), (x0 + 1.62, -43.18, .95), 2)
for k in range(3): cyl(bm, (x0 + 2.4, -43.3, k * .2), (x0 + 2.4, -43.3, k * .2 + .19), .32, 10, 3)
make('Garage_Open_Interior', bm, 'Garages', [M2['wire'], M2['bulb'], pm('Furniture_Wood'), M2['tire']])
light('Light_Garage_Bulb', 'POINT', (bulb_c[0], bulb_c[1], 1.6), 30, (1, .75, .45))

# ================================================================ cars
sys.path.insert(0, HERE); import car_spec as CS
CM = dict(chrome=mat('M_Car_Chrome', color=(.72, .72, .70), rough=.25), lamp=mat('M_Car_LampGlass', color=(.86, .86, .80), rough=.08),
          red=mat('M_Car_TailRed', color=(.5, .03, .02), rough=.15), amber=mat('M_Car_Amber', color=(.85, .38, .05), rough=.15),
          black=mat('M_Car_Black', color=(.025, .025, .025), rough=.6), wheel=mat('M_Car_Wheel', 'T_Car_Wheel', explicit=True),
          plate=mat('M_Car_Plates', 'T_Car_Plates', explicit=True))
def car(name, tex, kind, x, y, rot, wheels=True, plate=0):
    bm = bmesh.new(); uvl = bm.loops.layers.uv.new('UVMap')
    P = CS.profile(kind); n = len(P); k0 = P.index((-1.50, CS.SILL)) + 1; ARCH = set(range(k0, k0 + 14))
    ys = [-CS.HW, -CS.HW + .07, CS.HW - .07, CS.HW]
    def lp(li, px, pz):
        if li in (1, 2):
            if abs(px) > 1.9: px -= math.copysign(.05, px)
            if pz > .7: pz += .025
        return (px, ys[li], pz)
    V = [[bm.verts.new(lp(li, *P[i])) for i in range(n)] for li in range(4)]
    caps = [bm.faces.new(V[0]), bm.faces.new(V[3][::-1])]
    well = []
    for li in range(3):
        for i in range(n):
            f = bm.faces.new((V[li][i], V[li][(i + 1) % n], V[li + 1][(i + 1) % n], V[li + 1][i]))
            if i in ARCH and (i + 1) % n in ARCH: well.append(f)
    G = CS.greenhouse(kind); (bfx, bfz), (brx, brz) = G['bf'], G['br']; bw, tw, tf, tr, rf = G['bw'], G['tw'], G['tf'], G['tr'], G['roof']
    vb = [bm.verts.new(p) for p in ((bfx, -bw, bfz), (brx, -bw, brz), (brx, bw, brz), (bfx, bw, bfz))]
    vt = [bm.verts.new(p) for p in ((tf, -tw, rf), (tr, -tw, rf), (tr, tw, rf), (tf, tw, rf))]
    for q in ((vb[0], vb[1], vb[2], vb[3]), (vt[0], vt[1], vt[2], vt[3]), (vb[0], vb[1], vt[1], vt[0]), (vb[3], vb[2], vt[2], vt[3]), (vb[0], vt[0], vt[3], vb[3]), (vb[1], vb[2], vt[2], vt[1])):
        bm.faces.new(q)
    for c in caps: c.normal_update()
    bmesh.ops.triangulate(bm, faces=caps, ngon_method='EAR_CLIP')
    bm.faces.index_update(); fix_normals(bm)
    wellset = set(well)
    for f in bm.faces:
        nn = f.normal
        for lp_ in f.loops:
            co = lp_.vert.co
            if f in wellset or (abs(nn.z) >= max(abs(nn.x), abs(nn.y)) and nn.z < 0): px = CS.DARK_PX
            elif abs(nn.y) >= max(abs(nn.x), abs(nn.z)): px = CS.px_side(co.x, co.z)
            elif abs(nn.z) >= abs(nn.x): px = CS.px_top(co.x, co.y)
            elif nn.x > 0: px = CS.px_front(co.y, co.z)
            else: px = CS.px_back(co.y, co.z)
            lp_[uvl].uv = CS.uv(px)
    # ---- details: 1 chrome, 2 lamp glass, 3 red, 4 amber, 5 black, 6 wheel, 7 plate, 8 brick
    def piece(fn, mi):
        before = set(bm.faces); fn(); new = [f for f in bm.faces if f not in before]
        for f in new: f.material_index = mi
        return new
    for (yy, zz) in CS.HEADLIGHTS:
        for s in (-1, 1):
            fs = piece(lambda: cyl(bm, (1.975, s * yy, zz), (2.03, s * yy, zz), .085, 10), 1)
            for f in fs:
                if len(f.verts) > 4 and f.calc_center_median().x > 2.0: f.material_index = 2
    for s in (-1, 1):
        a, b = (CS.TAIL[0], CS.TAIL[1])
        piece(lambda: wbox(bm, (-2.02, min(s * .58, s * b), CS.TAIL[2]), (-1.99, max(s * .58, s * b), CS.TAIL[3])), 3)
        piece(lambda: wbox(bm, (-2.02, min(s * a, s * .57), CS.TAIL[2]), (-1.99, max(s * a, s * .57), CS.TAIL[3])), 4)
        piece(lambda: wbox(bm, (1.99, min(s * .55, s * .75), .49), (2.02, max(s * .55, s * .75), .53)), 4)
        piece(lambda: wbox(bm, (.62, min(s * .81, s * .88), .93), (.66, max(s * .81, s * .88), .95)), 5)
        piece(lambda: wbox(bm, (.60, min(s * .875, s * .97), .93), (.72, max(s * .875, s * .97), 1.03)), 1)
        for hx in (-.10, -.76): piece(lambda: wbox(bm, (hx, min(s * .81, s * .83), .82), (hx + .1, max(s * .81, s * .83), .845)), 1)
        piece(lambda: wbox(bm, (.64, min(s * .06, s * .56), .915), (.66, max(s * .06, s * .56), .93)), 5)
    piece(lambda: wbox(bm, (2.0, -.80, .40), (2.07, .80, .48)), 1); piece(lambda: wbox(bm, (-2.07, -.80, .38), (-2.0, .80, .46)), 1)
    piece(lambda: cyl(bm, (1.45, .74, .86), (1.30, .74, 1.55), .004, 4), 5); piece(lambda: cyl(bm, (-1.95, -.45, .27), (-2.12, -.45, .27), .03, 6), 5)
    if plate is not None:
        cu, cv = (plate % 2) * .5, 1 - (plate // 2 + 1) * .25
        for fx, x0, x1, z0, z1 in ((1, 2.07, 2.08, .375, .485), (-1, -2.012, -2.0, .45, .56)):
            fs = piece(lambda: wbox(bm, (x0, -.26, z0), (x1, .26, z1)), 7)
            for f in fs:
                for lp_ in f.loops:
                    co = lp_.vert.co; s_ = (co.y + .26) / .52 if fx > 0 else (.26 - co.y) / .52; t = (co.z - z0) / (z1 - z0)
                    lp_[uvl].uv = (cu + s_ * .5, cv + t * .25)
    if wheels:
        for axx in (CS.AX_F, CS.AX_R):
            for s in (-1, 1):
                fs = piece(lambda: cyl(bm, (axx, s * .58, .29), (axx, s * .75, .29), .29, 12), 6)
                for f in fs:
                    cap = len(f.verts) > 4
                    angs = [math.atan2(l.vert.co.z - .29, l.vert.co.x - axx) % (2 * math.pi) for l in f.loops]
                    if not cap and max(angs) - min(angs) > math.pi: angs = [a + 2 * math.pi if a < math.pi else a for a in angs]
                    for l, a in zip(f.loops, angs):
                        co = l.vert.co
                        if cap: l[uvl].uv = (.5 + .5 * (.5 + (co.x - axx) / .6), .5 + (co.z - .29) / .6)
                        else: l[uvl].uv = (.5 * a / (4 * math.pi) * 2, (abs(co.y) - .58) / .17)
    else:
        for bx in (1.85, .75, -.55, -1.85):
            for s in (-1, 1):
                for k in range(4): piece(lambda: wbox(bm, (bx - .125 + (k % 2) * .01, s * .6 - .06, -.055 + k * .079), (bx + .125 + (k % 2) * .01, s * .6 + .06, -.055 + (k + 1) * .079)), 8)
    return make(name, bm, 'Cars', [tm(tex) if False else mat('M_' + tex[2:], tex, explicit=True), CM['chrome'], CM['lamp'], CM['red'], CM['amber'], CM['black'], CM['wheel'], CM['plate'], E['BrickRed']],
                loc=(x, y, 0), rot=(0, 0, math.radians(rot)))
car('Car_Sedan_White', 'T_Car_Sedan_White', 'sedan', 13.0, -7.15, 0, plate=0)
car('Car_Sedan_Blue', 'T_Car_Sedan_Blue', 'sedan', 31.5, -7.15, 180, plate=1)
car('Car_Sedan_Cherry', 'T_Car_Sedan_Cherry', 'sedan', 56.0, -7.2, 2, plate=2)
car('Car_Wagon_Olive', 'T_Car_Wagon_Olive', 'wagon', 6.5, -11.05, 181, plate=3)
car('Car_Wreck', 'T_Car_Sedan_Wreck', 'sedan', 46.5, -31, 70, wheels=False, plate=None)

# ================================================================ background
lib = os.path.join(REPO, 'Panels2.blend')
with bpy.data.libraries.load(lib, link=False) as (src, dst): dst.objects = [n for n in src.objects if n.startswith('lod')]
for o in dst.objects:
    o.data = o.data.copy(); o.data.transform(Matrix.LocRotScale(o.location, o.rotation_euler, o.scale))
    o.location, o.rotation_euler, o.scale = (0, 0, 0), (0, 0, 0), (1, 1, 1)
    o.data.transform(Matrix.Translation((80, -45, 0))); o.data.materials.clear(); o.data.materials.append(E['BgPanels'])
    o.name = 'Bg_' + o.name; col('Background').objects.link(o)
for m in [m for m in bpy.data.materials if m.name.startswith('lod')]: bpy.data.materials.remove(m)       # keep only our 256 px copy
for im in [i for i in bpy.data.images if i.name.startswith('lod')]: bpy.data.images.remove(im)
def far_block(name, x0, y0, x1, y1, floors, seed):
    """distant panel block: dark body + only the lit windows as thin boxes"""
    r = random.Random(seed); hgt = .9 + floors * 2.8 + .7
    bm = bmesh.new(); wbox(bm, (x0, y0, -.05), (x1, y1, hgt)); make(name, bm, 'Background', [E['Plinth']])
    bm = bmesh.new()
    sides = [(lambda u, z, w: (u, y0 - w, z), x0, x1), (lambda u, z, w: (u, y1 + w, z), x0, x1),
             (lambda u, z, w: (x0 - w, u, z), y0, y1), (lambda u, z, w: (x1 + w, u, z), y0, y1)]
    for f, a, b in sides:
        for fl in range(floors):
            z = .9 + fl * 2.8 + .85
            for k in range(int((b - a) / 1.5)):
                if r.random() < .14:
                    u = a + .15 + k * 1.5; lbox(bm, f, u, u + 1.2, z, z + 1.4, 0, .02, r.choice((0, 0, 0, 1, 2, 3, 4)))
    make(name + '_Windows', bm, 'Background', [G['warm'], G['tv'], CURT[0], CURT[2], G['dim']])
for i, (x0, y0, x1, y1, fl) in enumerate(((-60, -100, -20, -88, 14), (90, -70, 128, -58, 12), (-40, -150, 30, -136, 16), (40, -125, 95, -113, 9),
                                         (72, 22, 112, 34, 12), (-62, 24, -26, 36, 9))):
    far_block('Bg_Block_%d' % (i + 1), x0, y0, x1, y1, fl, 300 + i)
bm = bmesh.new(); res = bmesh.ops.create_circle(bm, cap_ends=True, segments=16, radius=7)
mx = Matrix.Translation((-110, -280, 95)) @ Matrix.Rotation(math.radians(-80), 4, 'X')
for v in res['verts']: v.co = mx @ v.co
make('Moon', bm, 'Background', [M2['moon']], recalc=False)
d = bpy.data.lights.new('Light_Moon', 'SUN'); d.energy = .05; d.color = (.6, .7, 1.0); o = bpy.data.objects.new('Light_Moon', d)
o.rotation_euler = (math.radians(55), 0, math.radians(-30)); col('Lights').objects.link(o)
for n, loc, r in (('Spawn_Player', (2, -38.6, 0), 0), ('Exit_Entrance', (22.5, -.3, .45), 0)):
    e = bpy.data.objects.new(n, None); e.empty_display_type = 'ARROWS'; e.location = loc; e.rotation_euler = (0, 0, math.radians(r)); col('Markers').objects.link(e)

# ================================================================ UV, checks, save
bpy.context.view_layer.update()
def uv_mat(o):
    mw = o.matrix_world; nm_ = mw.to_3x3().inverted_safe().transposed()
    bm = bmesh.new(); bm.from_mesh(o.data); uvl = bm.loops.layers.uv.get('UVMap') or bm.loops.layers.uv.new('UVMap')
    for fc in bm.faces:
        s = MS.get(o.data.materials[fc.material_index].name, (1, 1))
        if s is None: continue
        n = (nm_ @ fc.normal).normalized(); ax = max(range(3), key=lambda i: abs(n[i])); sg = 1 if n[ax] >= 0 else -1
        for lp in fc.loops:
            c = mw @ lp.vert.co
            u, v = (sg * c.y, c.z) if ax == 0 else ((-sg * c.x, c.z) if ax == 1 else (c.x, sg * c.y))
            lp[uvl].uv = (u / s[0], v / s[1])
    bm.to_mesh(o.data); bm.free()
meshes = [o for o in root.all_objects if o.type == 'MESH']
for o in meshes:
    if not o.name.startswith('Bg_lod'): uv_mat(o)
IGN = [o.name for o in meshes if o.name.startswith(('Decal_', 'Bg_', 'Moon', 'Garage_Open_Door')) or o.name.endswith('_Decals') or o.name.endswith(('HouseNumber', 'EndNumber'))]   # open garage leaves hang on hinges
print(kt.check_all([o.name for o in meshes], ground=-.05, anchors=['Ground', 'BuildingA_Facade', 'BuildingB_Facade', 'Road', 'Sidewalk_A'], ignore=IGN))
print('WARN', WARN or 'none')
print('tris', sum(len(p.vertices) - 2 for o in meshes for p in o.data.polygons), 'objects', len(meshes))
bpy.ops.wm.save_as_mainfile(filepath=OUT, relative_remap=True)
print('saved', OUT)
