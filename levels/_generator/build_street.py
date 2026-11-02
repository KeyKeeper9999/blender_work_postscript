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
E = {k: tm('T_Ext_' + k) for k in ('Panel_A', 'Panel_B', 'Panel_C', 'Seam', 'Plinth', 'Road', 'Sidewalk', 'Curb', 'Lawn', 'Mud',
                                   'LeafClump', 'Sand', 'BarkPoplar', 'BarkBirch', 'GarageWall', 'GarageDoor', 'BrickRed',
                                   'Rust', 'PaintOrange', 'PaintBlue', 'PaintRed', 'CarPaintA',
                                   'CarPaintB', 'Pole', 'Roof', 'BgPanels')}
def glow(name, c, s): return mat(name, color=c, emit=(c, s), rough=.3)
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
    fac, frames, glass, bars, extra = bmesh.new(), bmesh.new(), bmesh.new(), bmesh.new(), bmesh.new()
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
    # drainpipes on seams
    bm_ = bmesh.new()
    for k in sorted({0, nb // 3, 2 * nb // 3, nb}):
        x = k * 3.0 + (.25 if k == 0 else -.25 if k == nb else 0); y = -.14; off = 0 if k in (0, nb) else -.0125
        cyl(bm_, P(x, y, .35), P(x, y, ztop - .1), .06, 8, 0); wbox(bm_, *[[min(a, b) for a, b in zip(P(x - .12, y - .1, ztop - .1), P(x + .12, off, ztop + .05))], [max(a, b) for a, b in zip(P(x - .12, y - .1, ztop - .1), P(x + .12, off, ztop + .05))]], 0)
        cyl(bm_, P(x, y, .41), P(x, y - .35, .12), .06, 8, 0)
        for z in range(2, int(ztop) - 1, 3):
            p, q = P(x - .03, -.08, z), P(x + .03, off, z + .04); wbox(bm_, [min(a, b) for a, b in zip(p, q)], [max(a, b) for a, b in zip(p, q)], 0)
    make(name + '_Drainpipes', bm_, name, [pm('Bucket')])
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
        lbox(bm_, dw_, cx - .546, cx + .546, .45, 2.496, 0, .04, 0)
        lbox(bm_, dw_, cx + .36, cx + .48, 1.18, 1.21, .04, .09, 1); lbox(bm_, dw_, cx + .38, cx + .42, 1.3, 1.36, .04, .045, 1)
        for (a, b, z0, z1) in ((-.4, -.12, 1.5, 1.85), (-.05, .2, 1.62, 1.9), (-.3, -.02, 1.0, 1.3)): lbox(bm_, dw_, cx + a, cx + b, z0, z1, .04, .042, 2)
        make(nm + '_Door', bm_, name, [pm('Door_SteelBrown') if k % 2 == 0 else pm('Mailbox'), M2['handle'], pm('Paper')], origin=dw_(cx - .546, .45, .02))
        bm_ = bmesh.new()
        lbox(bm_, bw, cx + .72, cx + .9, 1.42, 1.78, 0, .035, 0)
        for r_ in range(4):
            for c_ in range(3): lbox(bm_, bw, cx + .74 + c_ * .05, cx + .78 + c_ * .05, 1.46 + r_ * .05, 1.5 + r_ * .05, .035, .04, 1)
        lbox(bm_, bw, cx + .75, cx + .87, 1.68, 1.74, .035, .038, 2)
        for (a, b, z0, z1) in ((-1.25, -.75, 1.2, 1.9), (.95, 1.3, 1.5, 1.95)): lbox(bm_, bw, cx + a, cx + b, z0, z1, 0, .002, 3)
        make(nm + '_Intercom_Notices', bm_, name, [M2['steel'], M2['cream'], M2['plastic'], pm('Paper')])
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
EW_ = lambda u, z, w: (45 + w, u, z)       # east end wall of A, seen from the yard
bm = bmesh.new(); fs = lbox(bm, EW_, 4.75, 7.25, 17.85, 20.35, 0, .004); set_uv(bm, fs, EW_, 4.75, 7.25, 17.85, 20.35)
make('BuildingA_EndNumber', bm, 'BuildingA', [M2['bignum']], origin=(45, 6, 17.85))

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
slab('Mud_Playground', 8, -31, 22, -16, E['Mud'], -.045)
slab('TrashArea_Slab', 38, -20, 44, -14, pm('Concrete'))
for i, (x, y, rx, ry, pz_) in enumerate(((16, -9.0, 1.6, .9, .002), (27.5, -10.6, 1.1, .7, .002), (7.5, -8.0, .9, .6, .002), (2.0, -27.5, .8, .6, .002), (14.5, -23.5, 1.3, .9, -.042), (40, -5.0, .8, .5, .002))):
    bm = bmesh.new(); res = bmesh.ops.create_circle(bm, cap_ends=True, segments=10, radius=1)
    for v in res['verts']: v.co = Vector((x + v.co.x * rx, y + v.co.y * ry, pz_))
    make('Puddle_%02d' % (i + 1), bm, 'Street', [mat('M_Ext_Puddle', color=(.015, .018, .022), rough=.02)], recalc=False)

# ================================================================ palisade fences, tires, benches, urn
bm = bmesh.new(); fm = pm('ElectricPanel')
segs = [(.2, 6.0), (9.0, 21.0), (24.0, 36.0), (39.0, 44.8)]
for a, b in segs:
    n = max(1, int((b - a) / 1.5))
    for k in range(n + 1): x = a + k * (b - a) / n; wbox(bm, (x - .025, -3.95, -.05), (x + .025, -3.9, .7))
    for z in (.25, .62): wbox(bm, (a, -3.945, z), (b, -3.905, z + .03))
    for x in (a, b):
        for k in range(3): y = -3.9 + k * .95; wbox(bm, (x - .025, y, -.05), (x + .025, y + .05, .7)) if k else None
        for z in (.25, .62): wbox(bm, (x - .02, -3.9, z), (x + .02, -1.0, z + .03))
make('Palisade_Fence', bm, 'Street', [fm])
bm = bmesh.new()
for i, (x, y, pm_) in enumerate(((19.6, -2.6, 0), (20.5, -1.9, 1), (25.3, -2.3, 0), (26.2, -3.0, 1))):
    t = bmesh.ops.create_cone(bm, cap_ends=False, segments=10, radius1=.32, radius2=.32, depth=.22)
    for v in t['verts']: v.co += Vector((x, y, .06))
    for f in {f for v in t['verts'] for f in v.link_faces}: f.material_index = pm_
make('Tire_Planters', bm, 'Street', [M2['tirepaint'], M2['tirepaint2']], recalc=False)
def bench(name, x, y, rot, z0=-.04):
    bm = bmesh.new()
    for lx in (-.7, .7): wbox(bm, (lx - .1, -.18, z0), (lx + .1, .18, .4))
    for k in range(3): wbox(bm, (-.9, -.2 + k * .14, .4), (.9, -.2 + k * .14 + .11, .44))
    make(name, bm, 'Street', [pm('Concrete'), pm('Partition_Door')], loc=(x, y, 0), rot=(0, 0, math.radians(rot)))
bench('Bench_EntranceA2', 19.9, -4.6, 0); bench('Bench_Playground', 8.6, -23.5, 90, -.048); bench('Bench_EntranceB1', -3.4, -36.0, 90)
bm = bmesh.new(); cyl(bm, (24.2, -4.6, -.04), (24.2, -4.6, .6), .22, 8, 0, r1=.26); make('Urn_EntranceA2', bm, 'Street', [pm('Concrete')])

# ================================================================ trees
def tree(name, x, y, h, kind, clumps, seed):
    r = random.Random(seed); bm = bmesh.new(); bark = 0
    lean = Vector((r.uniform(-.3, .3), r.uniform(-.3, .3), 0))
    top = Vector((x, y, h)) + lean * h * .1
    cyl(bm, (x, y, -.06), top, .22 if kind == 'poplar' else .14, 6, bark, r1=.07)
    tips = []
    for k in range(r.randint(5, 7)):
        t = r.uniform(.35, .85); base = Vector((x, y, -.06)).lerp(top, t)
        az = r.uniform(0, 2 * math.pi); el = math.radians(r.uniform(35, 70) if kind == 'poplar' else r.uniform(15, 45))
        L = h * r.uniform(.25, .4) * (1 - t * .4); d = Vector((math.cos(az) * math.cos(el), math.sin(az) * math.cos(el), math.sin(el)))
        tip = base + d * L; cyl(bm, base, tip, .08 * (1 - t * .6), 5, bark, r1=.015)
        for s in range(2):
            a2 = az + r.uniform(-.8, .8); e2 = el + r.uniform(-.3, .4); d2 = Vector((math.cos(a2) * math.cos(e2), math.sin(a2) * math.cos(e2), math.sin(e2)))
            b2 = base.lerp(tip, r.uniform(.4, .8)); t2 = b2 + d2 * L * .5; cyl(bm, b2, t2, .03, 4, bark, r1=.008); tips.append(t2)
    for k in range(clumps):
        c = r.choice(tips); sphere(bm, c, r.uniform(.5, .9), .7, 1, 6, 4)
    make(name, bm, 'Trees', [E['BarkPoplar'] if kind == 'poplar' else E['BarkBirch'], E['LeafClump']])
for i, (x, y, h, k, c) in enumerate(((6, -14.5, 13, 'poplar', 2), (25, -14.6, 14, 'poplar', 0), (34, -30, 12, 'poplar', 3), (46.5, -22, 13, 'poplar', 1),
                                     (5.5, -32, 11, 'poplar', 0), (28, -33, 12, 'poplar', 2), (4.5, -2.5, 8, 'birch', 1), (13.5, -2.6, 9, 'birch', 0),
                                     (31, -2.4, 8.5, 'birch', 2), (42, -2.5, 7.5, 'birch', 0), (-2, -20, 10, 'birch', 1), (-1.5, -44, 12, 'poplar', 0))):
    tree('Tree_%02d' % (i + 1), x, y, h, k, c, 100 + i + (50 if i == 8 else 0))

# ================================================================ street lamps + wires
POLES = [(4, -5.7, 'dead'), (20, -5.7, 'lit'), (36, -5.7, 'flicker'), (52, -5.7, 'lit')]
bm = bmesh.new(); heads = bmesh.new(); hm = []
for i, (x, y, st) in enumerate(POLES):
    cyl(bm, (x, y, -.06), (x, y, 8.6), .13, 4, 0, r1=.08)
    wbox(bm, (x - .03, y - .45, 8.3), (x + .03, y + .45, 8.36), 1)
    cyl(bm, (x, y, 7.6), (x, y - 1.7, 7.95), .035, 6, 1)
    wbox(heads, (x - .14, y - 2.15, 7.86), (x + .14, y - 1.55, 8.04), 0); wbox(heads, (x - .1, y - 2.1, 7.84), (x + .1, y - 1.6, 7.86), 1 if st != 'dead' else 2)
    if st != 'dead': light('Light_StreetLamp_%d' % (i + 1) + ('_Flicker' if st == 'flicker' else ''), 'SPOT', (x, y - 1.85, 7.8), 900 if st == 'lit' else 500, (1, .55, .2), size=125)
x, y = 9.5, -25.0
cyl(bm, (x, y, -.06), (x, y, 7.0), .12, 4, 0, r1=.08); cyl(bm, (x, y, 6.2), (x + 1.4, y, 6.5), .035, 6, 1)
wbox(heads, (x + 1.3, y - .14, 6.41), (x + 1.9, y + .14, 6.59), 0); wbox(heads, (x + 1.35, y - .1, 6.39), (x + 1.85, y + .1, 6.41), 1)
light('Light_YardLamp', 'SPOT', (x + 1.6, y, 6.35), 500, (1, .6, .25), size=130)
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
    for dy in (-.85, .85): cyl(bm, (x, -20 + dy, -.048), (x, -20, 2.45), .04, 6, 0)
cyl(bm, (10.9, -20, 2.42), (13.5, -20, 2.42), .045, 6, 0)
for sx in (11.75, 12.65):
    for dy in (-.2, .2): cyl(bm, (sx, -20 + dy, 2.38), (sx, -20 + dy, .5), .006, 4, 1)
    wbox(bm, (sx - .25, -20.24, .45), (sx + .25, -19.76, .5), 2)
make('Swing', bm, 'Playground', [E['PaintBlue'], M2['steel'], pm('Partition_Door')])
bm = bmesh.new()
for a in ((16, -27, 18, -26.9), (16, -25.1, 18, -25), (16.001, -26.92, 16.1, -25.08), (17.9, -26.92, 17.999, -25.08)): wbox(bm, (a[0], a[1], -.048), (a[2], a[3], .28), 0)
wbox(bm, (16.105, -26.895, -.047), (17.895, -25.105, .14), 1); make('Sandbox', bm, 'Playground', [pm('Partition_Wood'), E['Sand']])
bm = bmesh.new(); sx, sy = 19.5, -19.0
for dx in (-.3, .3): cyl(bm, (sx + dx, sy + .6, -.048), (sx + dx, sy, 1.55), .03, 6, 0)
for k in range(5): z = .3 + k * .27; cyl(bm, (sx - .3, sy + .6 - z * .4, z), (sx + .3, sy + .6 - z * .4, z), .018, 6, 0)
wbox(bm, (sx - .35, sy - .5, 1.45), (sx + .35, sy, 1.53), 0)
for dx in (-.33, .33): cyl(bm, (sx + dx, sy - .5, -.048), (sx + dx, sy - .5, 1.45), .03, 6, 0)
hexa(bm, lambda a, t, n: (sx + a, sy - .5 - t * 2.6, 1.45 - t * 1.4 + n), (-.3, .3), (0, 1), (0, .03), 1)
make('Slide', bm, 'Playground', [E['PaintRed'], E['Rust']])
bm = bmesh.new()
for x in (9.6, 11.2): cyl(bm, (x, -28, -.048), (x, -28, 2.2), .04, 6, 0)
cyl(bm, (9.55, -28, 2.1), (11.25, -28, 2.1), .02, 6, 0); make('PullUpBar', bm, 'Playground', [E['PaintOrange']])

# ================================================================ trash area
bm = bmesh.new()
wbox(bm, (38, -20, 0), (44, -19.75, 1.6)); wbox(bm, (38.001, -19.76, .001), (38.25, -15, 1.599)); wbox(bm, (43.75, -19.76, .001), (43.999, -15, 1.599))
make('TrashArea_Walls', bm, 'Street', [E['BrickRed']])
for i, x in enumerate((38.5, 40.3, 42.1)):
    bm = bmesh.new(); wbox(bm, (x, -19.65, 0), (x + 1.4, -18.6, 1.05), 0)
    if i == 1: hexa(bm, lambda a, t, n: (x + a, -19.65 - n * .1 + t * .2, 1.05 + t * .9 + n), (.005, 1.395), (0, 1), (0, .03), 0)
    else: wbox(bm, (x - .02, -19.67, 1.05), (x + 1.42, -18.58, 1.08), 0)
    make('TrashContainer_%d' % (i + 1), bm, 'Street', [pm('ElectricPanel'), M2['steel']])
for i, (x, y, r) in enumerate(((39.0, -17.8, .3), (39.6, -17.4, .25), (41.9, -17.9, .28), (42.3, -16.2, .22), (38.7, -15.8, .26))):
    bm = bmesh.new(); sphere(bm, (0, 0, r * .75), r, .75, 0, 8, 6); make('GarbageBag_%02d' % (i + 1), bm, 'Street', [pm('Plastic_Bag')], loc=(x, y, 0))
bm = bmesh.new(); hexa(bm, lambda a, t, n: (43.75 - n - (1 - t / 1.9) * .35, -17.6 + a, t), (0, .9), (0, 1.9), (0, .15), 0)
make('Mattress', bm, 'Street', [pm('Carpet_Rolled')])

# ================================================================ garages
bm = bmesh.new(); doors = bmesh.new(); DC = [6, 7, 3, 1, 4, 6, 3, 7]
for g in range(8):
    x0 = 20 + g * 3.0; x1 = x0 + 3.0
    if g == 2: continue
    hexa(bm, lambda a, b, c: (x0 + .02 + a * 2.96, -44 + b * 6, c * (2.5 - b * .2) if c else 0), (0, 1), (0, 1), (0, 1), 0)
    for a, b in ((x0 + .15, x0 + 1.5), (x0 + 1.5, x1 - .15)): wbox(doors, (a + .005, -38.0, .05), (b - .005, -37.97, 2.25), DC[g])
    wbox(doors, (x0 + 1.42, -37.97, 1.0), (x0 + 1.58, -37.94, 1.3), 2)
make('Garages', bm, 'Garages', [E['GarageWall']]); make('Garage_Doors', doors, 'Garages',
     [E['GarageDoor'], E['Rust'], M2['handle'], pm('Mailbox'), pm('ElectricPanel'), pm('Door_SteelBrown'), E['GarageDoor'], E['Rust']])
x0 = 26.0; bm = bmesh.new()
hexa(bm, lambda a, b, c: (x0 + .02 + a * 2.96, -44 + b * 6, c * (2.5 - b * .2) if c else 0), (0, 1), (0, 1), (0, 1), 0)
og = make('Garage_Open', bm, 'Garages', [E['GarageWall']], origin=(x0 + 1.5, -41, 0))
c1 = bmesh.new(); wbox(c1, (x0 + .1, -43.9, .0), (x0 + 2.9, -38.1, 2.2)); c2 = bmesh.new(); wbox(c2, (x0 + .15, -38.5, .0), (x0 + 2.85, -37.5, 2.25)); boolean_cut(og, [c1, c2])
for side, (a, b, hx, ang) in (('L', (x0 + .15, x0 + 1.5, x0 + .15, 100)), ('R', (x0 + 1.5, x0 + 2.85, x0 + 2.85, -100))):
    bm = bmesh.new(); wbox(bm, (a + .005, -38.0, .05), (b - .005, -37.97, 2.25)); make('Garage_Open_Door' + side, bm, 'Garages', [pm('Door_SteelBrown')], origin=(hx, -37.985, .05), rot=(0, 0, math.radians(ang)))
bm = bmesh.new(); bulb_c = (x0 + 1.5, -41, 2.2)
cyl(bm, (bulb_c[0], bulb_c[1], 1.75), (bulb_c[0], bulb_c[1], 2.2), .004, 4, 0); sphere(bm, (bulb_c[0], bulb_c[1], 1.71), .04, 1, 1, 6, 4)
wbox(bm, (x0 + .2, -43.8, 0), (x0 + 1.6, -43.2, .9), 2); wbox(bm, (x0 + .18, -43.82, .9), (x0 + 1.62, -43.18, .95), 2)
for k in range(3): cyl(bm, (x0 + 2.4, -43.3, k * .2), (x0 + 2.4, -43.3, k * .2 + .19), .32, 10, 3)
make('Garage_Open_Interior', bm, 'Garages', [M2['wire'], M2['bulb'], pm('Furniture_Wood'), M2['tire']])
light('Light_Garage_Bulb', 'POINT', (bulb_c[0], bulb_c[1], 1.6), 30, (1, .75, .45))

# ================================================================ cars
def car(name, x, y, rot, paint, wheels=True):
    bm = bmesh.new(); h0 = .32 if wheels else .5
    wbox(bm, (-2.05, -.8, h0), (2.05, .8, h0 + .52), 0)
    hexa(bm, lambda a, b, c: ((-.95 + a * 1.85) + (b - .5) * (.0) - (c * (.3 if a else -.25)), -.74 + b * 1.48, h0 + .52 + c * .5), (0, 1), (0, 1), (0, 1), 1)
    wbox(bm, (2.05, -.7, h0 + .3), (2.07, -.45, h0 + .42), 3); wbox(bm, (2.05, .45, h0 + .3), (2.07, .7, h0 + .42), 3)
    wbox(bm, (-2.1, -.82, h0 + .08), (2.1, .82, h0 + .14), 4)
    if wheels:
        for wx in (-1.3, 1.3):
            for s in (-1, 1): cyl(bm, (wx, s * .7, .3), (wx, s * .88, .3), .3, 10, 2)
    else:
        for wx in (-1.3, 1.3):
            for s in (-1, 1): wbox(bm, (wx - .15, s * .6 - .12, -.05), (wx + .15, s * .6 + .12, .5), 5)
    make(name, bm, 'Cars', [paint, M2['glass'], M2['tire'], M2['headl'], M2['handle'], E['BrickRed']], loc=(x, y, 0), rot=(0, 0, math.radians(rot)))
car('Car_01', 13.0, -7.15, 0, E['CarPaintA']); car('Car_02', 31.5, -7.15, 180, E['CarPaintB']); car('Car_OnBricks', 46.5, -31, 70, E['Rust'], wheels=False)

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
IGN = [o.name for o in meshes if o.name.startswith(('Puddle', 'Bg_', 'Moon', 'Garage_Open_Door')) or o.name.endswith(('HouseNumber', 'EndNumber'))]   # open garage leaves hang on hinges
print(kt.check_all([o.name for o in meshes], ground=-.05, anchors=['Ground', 'BuildingA_Facade', 'BuildingB_Facade', 'Road', 'Sidewalk_A'], ignore=IGN))
print('WARN', WARN or 'none')
print('tris', sum(len(p.vertices) - 2 for o in meshes for p in o.data.polygons), 'objects', len(meshes))
bpy.ops.wm.save_as_mainfile(filepath=OUT, relative_remap=True)
print('saved', OUT)
