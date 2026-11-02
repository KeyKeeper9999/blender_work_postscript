"""Apartments behind the corridor doors. usage: python3 build_apartment.py <variant> <out.blend>
variants: Lived (ordinary), Empty (stripped for renovation), Covered (everything under sheets, floor full of letters),
          Ceiling (the room's furniture hangs on the ceiling), Long (the hallway does not end)"""
import sys, os, math, random
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from kit import *
VAR, OUT = sys.argv[-2], os.path.abspath(sys.argv[-1])
R = random.Random(sum(map(ord, VAR))); T, TE, TH = .15, .3, .015
start(OUT, os.path.splitext(os.path.basename(OUT))[0])
LONG = VAR == 'Long'; HL = 14.0 if LONG else 3.4

# ---------------------------------------------------------------- plan
if LONG:
    ROOMS = {'Hall': (3.75, 0, 5.25, HL), 'Kitchen': (3.75, HL + .15, 7.0, HL + 2.6)}
    DOORS = [('Entrance', ('y', 0, 1), 4.5, .94, 2.07, 'entry')]
    for k in range(6):
        y = 1.6 + k * 2.1
        DOORS += [('Side_W%d' % k, ('x', 3.75, 1), y, .8, 2.0, 'blind'), ('Side_E%d' % k, ('x', 5.25, -1), y + .9, .8, 2.0, 'blind')]
    DOORS += [('Kitchen', ('y', HL, -1), 4.5, .8, 2.0, 'glass_open')]
    WINDOWS = [(('y', HL + 2.6, -1), 5.4, 1.2)]
else:
    ROOMS = {'Room': (0, 0, 3.6, 6.0), 'Hall': (3.75, 0, 5.25, 3.4), 'Bath': (5.4, 0, 7.0, 2.0), 'Pantry': (5.4, 2.15, 7.0, 3.4), 'Kitchen': (3.75, 3.55, 7.0, 6.0)}
    DOORS = [('Entrance', ('y', 0, 1), 4.5, .94, 2.07, 'entry'), ('Room', ('x', 3.75, 1), 2.4, .8, 2.0, 'glass'), ('Kitchen', ('y', 3.4, -1), 4.5, .8, 2.0, 'glass'),
             ('Bath', ('x', 5.25, -1), 1.0, .7, 2.0, 'plain'), ('Pantry', ('x', 5.25, -1), 2.8, .7, 2.0, 'plain')]
    WINDOWS = [(('x', 0, 1), 3.0, 1.5), (('y', 6.0, -1), 5.4, 1.2)]
EMPTY, COVER, CEIL = VAR == 'Empty', VAR == 'Covered', VAR == 'Ceiling'
FIN = {   # walls, floor
    'Room': ('T_AW_Stripped' if EMPTY else 'T_AW_Stripes' if COVER else 'T_AW_Damask', 'T_AF_Concrete' if EMPTY else 'T_AF_Parquet'),
    'Hall': ('T_AW_Stripped' if EMPTY else 'T_AW_Flowers', 'T_AF_Concrete' if EMPTY else 'T_AF_KitchenLino'),
    'Kitchen': ('T_AW_Kitchen_A', 'T_AF_KitchenLino'), 'Bath': ('T_AW_Bath_A', 'T_AF_BathTile'), 'Pantry': ('T_AW_Kitchen_A', 'T_AF_KitchenLino')}
RN = list(ROOMS); RR = [ROOMS[n] for n in RN]
def room_at(x, y):
    for n in RN:
        r = ROOMS[n]
        if r[0] - .01 <= x <= r[2] + .01 and r[1] - .01 <= y <= r[3] + .01: return n
    return RN[0]
WT = list(dict.fromkeys(FIN[n][0] for n in RN)); WMAT = [wm(t) for t in WT]
X0, Y0, X1, Y1 = min(r[0] for r in RR), min(r[1] for r in RR), max(r[2] for r in RR), max(r[3] for r in RR)
bm = bmesh.new(); wbox(bm, (X0 - TE, Y0 - TE, 0), (X1 + TE, Y1 + TE, H)); walls = make('Walls', bm, 'Shell', WMAT)
cuts = []
for r in RR: c = bmesh.new(); wbox(c, (r[0], r[1], -.5), (r[2], r[3], H + .5)); cuts.append(c)
for n, wf, u, wd, h, kind in DOORS:
    if kind != 'blind': cuts.append(cutter(wf, u - wd / 2, u + wd / 2, TH, h, .35))
for wf, uc, ww in WINDOWS: cuts.append(cutter(wf, uc - ww / 2, uc + ww / 2, .85, 2.25, TE + .5))
boolean_cut(walls, cuts)
bm = bmesh.new(); bm.from_mesh(walls.data)
bmesh.ops.dissolve_degenerate(bm, dist=1e-5, edges=bm.edges[:]); bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=1e-5)
bmesh.ops.delete(bm, geom=[f for f in bm.faces if (f.normal.z < -.99 and abs(f.calc_center_median().z) < 1e-4) or (f.normal.z > .99 and abs(f.calc_center_median().z - H) < 1e-4)], context='FACES')
for f in bm.faces:
    c = f.calc_center_median() + f.normal * .06; f.material_index = WT.index(FIN[room_at(c.x, c.y)][0])
bm.to_mesh(walls.data); bm.free()
for n in RN:
    x0, y0, x1, y1 = ROOMS[n]; bm = bmesh.new(); bm.faces.new([bm.verts.new(p) for p in ((x0, y0, 0), (x1, y0, 0), (x1, y1, 0), (x0, y1, 0))])
    make('Floor_' + n, bm, 'Shell', [tm(FIN[n][1], (1.2, 1.2) if n == 'Bath' else (2.4, 2.4))], recalc=False)
bm = bmesh.new()
for r in RR: bm.faces.new([bm.verts.new(p) for p in ((r[0], r[1], H), (r[0], r[3], H), (r[2], r[3], H), (r[2], r[1], H))])
make('Ceiling', bm, 'Shell', [tm('T_AC_Ceiling', (2, 2))], recalc=False)
SEGS = wall_segments(RR)

# ---------------------------------------------------------------- materials
VD, VL = tm('T_A_VeneerDark', (.8, .8)), tm('T_A_VeneerLight', (.8, .8)); EN = tm('T_A_Enamel', (.6, .6)); SHEET = tm('T_A_Sheet', (1.0, 1.0))
METAL, CHROME, BLACK = flat('M_Metal_Dark', (.1, .09, .08), .5), flat('M_Chrome', (.6, .6, .58), .2), flat('M_Black', (.015, .015, .015))
BRASS = flat('M_Metal_Brass', (.45, .33, .12), .45); MIRROR = flat('M_Mirror', (.55, .58, .6), .03); GLASS = flat('M_Glass_Clear', (.25, .3, .32), .05); NIGHT = glow('M_Glass_Night', (.02, .03, .06), 1.0)
LC = (1, .78, .5); LAMPG = glow('M_Lamp_Glow', LC, 6.0); DEADG = flat('M_Lamp_DeadGlass', (.5, .48, .42), .4)
LIGHTS = []; IGNX = []

# ---------------------------------------------------------------- doors and windows
def casing(bm, wf, u0, u1, h, a=.065, d=.012, w0=0.0, mi=0):
    prism(bm, wf, [(u0 - a, 0), (u0, 0), (u0, h), (u1, h), (u1, 0), (u1 + a, 0), (u1 + a, h + a), (u0 - a, h + a)], w0, w0 + d, mi)
for n, wf, u, wd, h, kind in DOORS:
    f = F(wf); u0, u1 = u - wd / 2, u + wd / 2; TW = TE if wf[1] in (X0, X1, Y0, Y1) else T
    bm = bmesh.new()
    if kind != 'blind':
        for a, b in ((u0, u0 + .03), (u1 - .03, u1)): lbox(bm, wf, a, b, TH, h, -TW - .002, -.004)
        lbox(bm, wf, u0 + .0305, u1 - .0305, h - .03, h - .0005, -TW - .002, -.004)
        casing(bm, wf, u0, u1, h); casing(bm, wf, u0, u1, h, w0=-TW - .016)
    else: casing(bm, wf, u0, u1, h)
    make(f'Door_{n}_Frame', bm, 'Doors', [tm('T_Wood_Frame_M')], origin=f(u, 0, 0))
    la, lb = u0 + .034, u1 - .034; cell = (0, 0, .5, 1) if kind in ('glass', 'glass_open') else (.5, 0, 1, 1)
    tex = xm('T_IDoors_Panel80') if kind == 'entry' else xm('T_A_Doors'); cell = (0, 0, 1 / 8, 1) if kind == 'entry' else cell
    bm = bmesh.new(); w0, w1 = (-.07, -.03) if kind != 'blind' else (.01, .05)
    caps = prism(bm, wf, [(la, TH + .005), (lb, TH + .005), (lb, h - .035), (la, h - .035)], w0, w1, 0)
    for fc in bm.faces:
        if fc not in caps: fc.material_index = 1
    for c in caps: set_uv(bm, c, wf, la, lb, TH + .005, h - .035, cell)
    hx = lb - .07; ww = w1
    lbox(bm, wf, hx - .018, hx + .018, .9, 1.08, ww, ww + .005, 2); lbox(bm, wf, hx - .12, hx + .01, .97, .995, ww + .02, ww + .032, 2); lbox(bm, wf, hx - .008, hx + .008, .97, .995, ww + .005, ww + .02, 2)
    if kind == 'entry': cyl(bm, f(u, 1.55, w1), f(u, 1.55, w1 + .014), .012, 8, 2)
    hinge = f(la, TH, (w0 + w1) / 2); ang = 0
    if kind == 'glass_open': ang = 70
    o = make(f'Door_{n}', bm, 'Doors', [tex, flat('M_Door_Edge', (.25, .2, .14)), BRASS], origin=hinge)
    if ang: o.rotation_euler = (0, 0, math.radians(ang) * (1 if wf[2] < 0 else -1))
    occupy(wf, u0 - .07, u1 + .07, 0, h + .07, 'Door_' + n)
    if kind != 'blind':
        b_ = (wf[0], round(wf[1] - wf[2] * TW, 4), -wf[2]); occupy(b_, u0 - .07, u1 + .07, 0, h + .07, 'Door_' + n)
for i, (wf, uc, ww) in enumerate(WINDOWS):
    f = F(wf); a0, a1 = uc - ww / 2, uc + ww / 2; bm = bmesh.new()
    for a in ((a0, a0 + .06, .85, 2.25), (a1 - .06, a1, .85, 2.25), (a0 + .0605, a1 - .0605, 2.19, 2.25), (a0 + .0605, a1 - .0605, .85, .94), (uc - .03, uc + .03, .9405, 2.1895)):
        lbox(bm, wf, a[0], a[1], a[2], a[3], -.21, -.15, 0)
    gm = 2 if (COVER or EMPTY) else 1
    for a in ((a0 + .06, uc - .03, .94, 2.19), (uc + .03, a1 - .06, .94, 2.19)):
        fs = lbox(bm, wf, a[0], a[1], a[2], a[3], -.185, -.175, gm); set_uv(bm, fs, wf, a[0], a[1], a[2], a[3])
    prism(bm, lambda p, q, a: f(p, a, q), [(a0 + .001, -.15), (a1 - .001, -.15), (a1, 0), (a1 + .06, 0), (a1 + .06, .08), (a0 - .06, .08), (a0 - .06, 0), (a0, 0)], .85, .88, 0)
    make('Window_%d' % (i + 1), bm, 'Windows', [tm('T_Wood_Frame_M'), NIGHT, xm('T_A_Newspaper')], origin=f(uc, .85, 0))
    bm = bmesh.new()
    for k in range(int(ww / .1)):
        a = uc - ww / 2 + .1 + k * .09
        if a + .06 > uc + ww / 2 - .1: break
        prism(bm, wf, [(a, .14), (a + .06, .14), (a + .065, .2), (a + .065, .6), (a + .06, .66), (a, .66), (a - .005, .6), (a - .005, .2)], .06, .15)
    for z in (.2, .6): cyl(bm, f(uc - ww / 2, z, .105), f(uc + ww / 2 - .08, z, .105), .02, 8)
    for a in (uc - ww / 2 + .02, uc + ww / 2 - .14): lbox(bm, wf, a, a + .03, .58, .62, 0, .06)
    make('Radiator_%d' % (i + 1), bm, 'Windows', [tm('T_Radiator')], origin=f(uc, 0, 0)); occupy(wf, a0 - .1, a1 + .1, 0, 2.3, 'Window_%d' % i)
    LIGHTS.append(('Light_Window_%d' % (i + 1), f(uc, 1.6, .5), 2.5, (.45, .55, 1.0)))
    if not EMPTY:                                        # curtains + tulle on a rod
        bm = bmesh.new(); rz = 2.42; cyl(bm, f(a0 - .35, rz, .1), f(a1 + .35, rz, .1), .012, 6, 0)
        for a in (a0 - .3, a1 + .3): lbox(bm, wf, a - .01, a + .01, rz - .01, rz + .01, 0, .095, 0)
        make('CurtainRod_%d' % (i + 1), bm, 'Windows', [CHROME]); bm = bmesh.new()
        for s_, (p0, p1) in ((0, (a0 - .33, a0 + .12)), (1, (a1 - .12, a1 + .33))):
            n_ = 6; pts = []
            for k in range(n_ + 1):
                uu = p0 + (p1 - p0) * k / n_; ww_ = .12 + (.035 if k % 2 else 0); pts.append((uu, ww_))
            for k in range(n_):
                (ua_, wa), (ub_, wb) = pts[k], pts[k + 1]; fc = quad(bm, [f(ua_, .05, wa), f(ub_, .05, wb), f(ub_, rz, wb), f(ua_, rz, wa)], 1)
                set_uv(bm, fc, wf, ua_, ub_, .05, rz, (k / n_, 0, (k + 1) / n_, 1))
                fc2 = quad(bm, [f(ub_, .05, wb + .004), f(ua_, .05, wa + .004), f(ua_, rz, wa + .004), f(ub_, rz, wb + .004)], 1); set_uv(bm, fc2, wf, ub_, ua_, .05, rz, ((k + 1) / n_, 0, k / n_, 1))
        if not COVER:
            fc = quad(bm, [f(a0 + .1, .9, .08), f(a1 - .1, .9, .08), f(a1 - .1, rz, .08), f(a0 + .1, rz, .08)], 2); set_uv(bm, fc, wf, a0 + .1, a1 - .1, .9, rz, (0, 0, (ww - .2) / .6, (rz - .9) / .6))
        bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=1e-5)
        make('Curtains_%d' % (i + 1), bm, 'Windows', [CHROME, xm('T_A_Curtain'), dm('T_A_Tulle')], recalc=False); IGNX.append('Curtains_%d' % (i + 1))

# ---------------------------------------------------------------- furniture (local: front faces -y, back against +y)
PIECES = []          # (name, builder, mats, loc, rot, room, coverable)
def place(name, fn, mats, wf=None, u=None, x=None, y=None, rot=0, room=None, cover=True, w=None, oh=2.3):
    if wf is not None:
        n = nrm(wf); p = F(wf)(u, 0, 0); rot = math.degrees(math.atan2(n.x, -n.y)); x, y = p[0], p[1]
        if w: occupy(wf, u - w / 2, u + w / 2, 0, oh, name)
    PIECES.append((name, fn, mats, (x, y), rot, room or room_at(x + .01, y + .01), cover))
def B(bm, x0, y0, z0, x1, y1, z1, mi=0): wbox(bm, (x0, y0, z0), (x1, y1, z1), mi)
def front(bm, x0, x1, z0, z1, y, mi, uvr=(0, 0, 1, 1)): uvquad(bm, [(x0, y, z0), (x1, y, z0), (x1, y, z1), (x0, y, z1)], mi, uvr)
def stenka(bm):
    B(bm, -1.5, -.45, .04, -.6005, 0, 2.2, 0); B(bm, -.6, -.45, .04, .6, 0, 2.2, 0); B(bm, .6005, -.45, .04, 1.5, 0, 2.2, 0); B(bm, -1.5, -.42, 0, 1.5, -.03, .04, 3)
    front(bm, -.56, .56, .95, 2.15, -.452, 1); front(bm, .64, 1.46, 1.2, 2.15, -.452, 2)
    for x0, x1 in ((-1.46, -1.06), (-1.04, -.64)): B(bm, x0, -.46, .1, x1, -.45, 2.15, 0)
    for z in (.1, .5): B(bm, -.56, -.46, z, .56, -.45, z + .38, 0)
    B(bm, .64, -.46, .1, 1.46, -.45, 1.15, 0)
    for x in (-1.08, -1.02, .02, 1.0): B(bm, x, -.48, 1.0, x + .015, -.46, 1.15, 4)
def sofa(bm):
    B(bm, -.84, -.85, .1, .84, -.05, .42, 0); B(bm, -.8395, -.25, .4205, .8395, 0, .9, 0)
    for s in (-1, 1): B(bm, s * 1.0 - (.1595 if s > 0 else 0), -.85, .1, s * 1.0 + (.1595 if s < 0 else 0), -.05, .62, 0)
    for k in range(2): B(bm, -.84 + k * .84, -.83, .42, -.84 + k * .84 + .82, -.27, .52, 0)
    for s in (-1, 1): B(bm, s * .9 - .03, -.8, 0, s * .9 + .03, -.1, .1, 1)
def table(bm, w=1.0, d=.6, h=.5, legs=.04):
    B(bm, -w / 2, -d / 2, h - .04, w / 2, d / 2, h, 0)
    for sx in (-1, 1):
        for sy in (-1, 1): B(bm, sx * (w / 2 - .06) - legs / 2, sy * (d / 2 - .06) - legs / 2, 0, sx * (w / 2 - .06) + legs / 2, sy * (d / 2 - .06) + legs / 2, h - .04, 0)
def tv(bm):
    B(bm, -.45, -.4, 0, .45, 0, .55, 0); B(bm, -.32, -.42, .58, .32, -.02, 1.08, 1); front(bm, -.32, .32, .58, 1.08, -.422, 2)
    cyl(bm, (-.1, -.2, 1.08), (-.25, -.2, 1.45), .004, 4, 3); cyl(bm, (.1, -.2, 1.08), (.25, -.2, 1.45), .004, 4, 3)
def armchair(bm):
    B(bm, -.42, -.75, .1, .42, -.05, .42, 0); B(bm, -.42, -.24, .4205, .42, -.05, .95, 0)
    for s in (-1, 1): B(bm, s * .4195 - (.12 if s > 0 else 0), -.75, .4205, s * .4195 + (.12 if s < 0 else 0), -.2395, .62, 0)
    for sx in (-1, 1):
        for sy in (-1, 1): B(bm, sx * .35 - .025, -.4 + sy * .3 - .025, 0, sx * .35 + .025, -.4 + sy * .3 + .025, .1, 1)
def chandelier(bm):
    cyl(bm, (0, 0, H - .02), (0, 0, H), .06, 8, 0); cyl(bm, (0, 0, H - .4), (0, 0, H - .02), .008, 4, 0)
    for k in range(3):
        a = k * 2 * math.pi / 3; p = Vector((.28 * math.cos(a), .28 * math.sin(a), H - .5))
        cyl(bm, (0, 0, H - .42), tuple(p + Vector((0, 0, .04))), .008, 4, 0); cyl(bm, tuple(p), tuple(p + Vector((0, 0, .14))), .1, 8, 1, r1=.05)
def clock(bm): cyl(bm, (0, 0, 0), (0, -.03, 0), .14, 12, 0); f = quad(bm, [(-.12, -.032, -.12), (.12, -.032, -.12), (.12, -.032, .12), (-.12, -.032, .12)], 1)
def picture(bm, w=.6, h=.5, mi=1):
    B(bm, -w / 2, -.025, 0, w / 2, 0, h, 0); front(bm, -w / 2 + .02, w / 2 - .02, .02, h - .02, -.027, mi)
def coatrack(bm):
    B(bm, -.45, -.03, 1.6, .45, 0, 1.75, 0); B(bm, -.47, -.3, 1.85, .47, 0, 1.88, 0)
    for k, c in enumerate((1, 2, 1)):
        x = -.3 + k * .3; B(bm, x - .14, -.24 + k * .015, .85 + k * .03, x + .14, -.04 - k * .005, 1.7, c)
    B(bm, -.45, -.32, 0, .45, -.02, .4, 0)
    for k in range(3): B(bm, -.4 + k * .3, -.3, .4, -.4 + k * .3 + .1, -.06, .5, 3)
def mirror_w(bm, w=.5, h=.8): B(bm, -w / 2, -.02, 0, w / 2, 0, h, 0); front(bm, -w / 2 + .03, w / 2 - .03, .03, h - .03, -.022, 1)
def fridge(bm): B(bm, -.3, -.6, .03, .3, 0, 1.5, 0); front(bm, -.3, .3, .03, 1.5, -.602, 1); B(bm, -.29, -.58, 0, .29, -.02, .03, 2)
def stove(bm):
    B(bm, -.25, -.6, 0, .25, 0, .85, 0); front(bm, -.25, .25, .05, .85, -.602, 1); B(bm, -.25, -.06, .8505, .25, 0, 1.1, 0)
    for sx in (-.12, .12):
        for sy in (-.42, -.2): cyl(bm, (sx, sy, .85), (sx, sy, .87), .07, 8, 2)
    cyl(bm, (.12, -.42, .87), (.12, -.42, 1.0), .09, 10, 3, r1=.07); cyl(bm, (-.12, -.2, .87), (-.12, -.2, .97), .1, 10, 2)
def sink(bm):
    B(bm, -.4, -.6, 0, .4, 0, .82, 0); B(bm, -.42, -.62, .82, .42, 0, .86, 1); B(bm, -.25, -.48, .78, .25, -.12, .862, 2)
    cyl(bm, (0, -.06, .86), (0, -.06, 1.06), .012, 6, 3); cyl(bm, (0, -.06, 1.06), (0, -.22, 1.02), .012, 6, 3)
    for k in range(2): B(bm, -.39 + k * .39, -.61, .05, -.39 + k * .39 + .38, -.6, .78, 0)
def cabinet_wall(bm, w=1.3): B(bm, -w / 2, -.32, 0, w / 2, 0, .65, 0); [B(bm, -w / 2 + .02 + k * w / 3, -.33, .03, -w / 2 + (k + 1) * w / 3 - .01, -.32, .62, 0) for k in range(3)]
def kitchen_table(bm):
    table(bm, .9, .6, .75); uvquad(bm, [(-.45, -.3, .7515), (.45, -.3, .7515), (.45, .3, .7515), (-.45, .3, .7515)], 1)
def stool(bm): B(bm, -.16, -.16, .42, .16, .16, .45); [B(bm, sx * .12 - .015, sy * .12 - .015, 0, sx * .12 + .015, sy * .12 + .015, .42) for sx in (-1, 1) for sy in (-1, 1)]
def chair(bm):
    for sx in (-1, 1):
        for sy in (-1, 1): B(bm, sx * .19 - .017, sy * .18 - .017, 0, sx * .19 + .017, sy * .18 + .017, .44)
    B(bm, -.215, -.205, .44, .215, .205, .47)
    for sx in (-1, 1): B(bm, sx * .19 - .017, .166, .47, sx * .19 + .017, .2, .95)
    for z in (.62, .78): B(bm, -.172, .17, z, .172, .2, z + .1)
def tub(bm):
    B(bm, -.35, -.75, 0, .35, .75, .55, 0); B(bm, -.36, -.76, .55, .36, .76, .58, 0)
def toilet(bm):
    cyl(bm, (0, -.25, 0), (0, -.25, .38), .17, 10, 0, r1=.2); B(bm, -.2, -.48, .38, .2, -.05, .41, 1); B(bm, -.2, -.2, .7, .2, 0, 1.05, 0); cyl(bm, (0, -.12, .4), (0, -.12, .7), .03, 6, 0)
def washbasin(bm): cyl(bm, (0, -.25, 0), (0, -.25, .7), .08, 8, 0); B(bm, -.28, -.45, .7, .28, 0, .85, 0); cyl(bm, (0, -.05, .85), (0, -.15, .92), .01, 6, 1)
def shelves(bm):
    for x0 in (-.5, .48): B(bm, x0, -.35, 0, x0 + .02, 0, 2.0, 0)
    for z in (.3, .8, 1.3, 1.8): B(bm, -.48, -.35, z, .48, 0, z + .02, 0)
    for k in range(9):
        z = (.32, .82, 1.32)[k % 3]; x = -.4 + (k // 3) * .3; cyl(bm, (x, -.18, z), (x, -.18, z + .16), .05, 8, 1)
    B(bm, -.4, -.32, 1.82, .1, -.02, 2.0, 2)
def ladder(bm):
    for sx in (-1, 1):
        cyl(bm, (sx * .22, -.45, 0), (sx * .18, 0, 1.6), .02, 4, 0); cyl(bm, (sx * .22, .45, 0), (sx * .18, .02, 1.58), .02, 4, 0)
    for k in range(4): z = .35 + k * .35; t = z / 1.6; B(bm, -.2, -.45 + t * .45 - .04, z, .2, -.45 + t * .45 + .04, z + .025, 0)
def paintcans(bm):
    for k, (x, y) in enumerate(((0, 0), (.3, .05), (.12, .32))): cyl(bm, (x, y, 0), (x, y, .28), .12, 10, k % 2)
    for k in range(3): cyl(bm, (.55, -.25 + k * .15, .06), (1.05, -.25 + k * .15, .06), .06, 8, 2)

def furnish():
    if LONG:
        def spot(wf, u, w):
            for du in [0] + [s_ * .1 * i for i in range(1, 15) for s_ in (1, -1)]:
                if is_free(wf, u + du - w / 2 - .02, u + du + w / 2 + .02, 0, 2.3): return u + du
        for k in range(4):
            y = .6 + k * 3.3; ue = spot(('x', 5.25, -1), y, 1.0); uw = spot(('x', 3.75, 1), y + .55, .55)
            if ue is not None: place('CoatRack_%d' % k, coatrack, [VD, tm('T_A_Sofa', (.5, .5)), tm('T_A_Armchair', (.5, .5)), tm('T_Boots')], wf=('x', 5.25, -1), u=ue, w=.95)
            if uw is not None: place('HallMirror_%d' % k, mirror_w, [VD, MIRROR], wf=('x', 3.75, 1), u=uw, w=.5)
        return
    if not EMPTY:
        place('Stenka', stenka, [VD, xm('T_A_StenkaGlass'), xm('T_A_Books'), BLACK, flat('M_Metal_Brass', (.45, .33, .12), .45)], wf=('y', 6.0, -1), u=1.8, w=3.0)
        place('Sofa', sofa, [tm('T_A_Sofa', (.6, .6)), VD], wf=('y', 0, 1), u=1.6, w=2.0, oh=.92)
        place('TV', tv, [VD, tm('T_A_VeneerDark', (.5, .5)), xm('T_A_TV'), METAL], wf=('x', 3.6, -1), u=4.4, w=.9, oh=1.5)
        place('Armchair', armchair, [tm('T_A_Armchair', (.6, .6)), VD], x=1.0, y=4.6, rot=-110)
        place('CoffeeTable', lambda bm: table(bm, 1.0, .55, .45), [VL], x=1.6, y=1.6, rot=0)
        place('Chandelier', chandelier, [CHROME, LAMPG], x=1.8, y=3.0, cover=False)
        place('FridgeK', fridge, [EN, xm('T_A_Fridge'), BLACK], wf=('x', 7.0, -1), u=4.15, w=.6)
        place('Stove', stove, [EN, xm('T_A_Stove'), BLACK, flat('M_Kettle', (.6, .2, .15), .3)], wf=('x', 7.0, -1), u=4.75, w=.5)
        place('Sink', sink, [VL, flat('M_Worktop', (.55, .5, .42), .6), CHROME, CHROME], wf=('x', 7.0, -1), u=5.45, w=.8)
        place('KitchenTable', kitchen_table, [VL, xm('T_A_Oilcloth')], x=4.45, y=5.35, rot=90)
        for k, (x, y) in enumerate(((4.45, 4.75), (4.95, 5.35))): place('Stool_%d' % k, stool, [VL], x=x, y=y)
        place('CoatRack', coatrack, [VD, tm('T_A_Sofa', (.5, .5)), tm('T_A_Armchair', (.5, .5)), tm('T_Boots')], wf=('x', 3.75, 1), u=1.0, w=.95)
        place('HallMirror', mirror_w, [VD, MIRROR], wf=('x', 5.25, -1), u=1.9, w=.5)
        place('Pantry_Shelves', shelves, [tm('T_Planks'), flat('M_Glass_Jar', (.35, .42, .38), .2), tm('T_Cardboard')], wf=('y', 3.4, -1), u=6.2, w=1.0, cover=False)
    else:
        place('Ladder', ladder, [tm('T_A_VeneerLight')], x=1.8, y=3.0, rot=25, cover=False)
        place('PaintCans', paintcans, [flat('M_Can', (.55, .55, .5), .4), flat('M_Can2', (.5, .2, .15), .5), tm('T_A_Newspaper', (.5, .5))], x=.6, y=5.3, rot=10, cover=False)
        place('Stove', stove, [EN, xm('T_A_Stove'), BLACK, flat('M_Kettle', (.6, .2, .15), .3)], wf=('x', 7.0, -1), u=4.75, w=.5, cover=False)
        place('Sink', sink, [VL, flat('M_Worktop', (.55, .5, .42), .6), CHROME, CHROME], wf=('x', 7.0, -1), u=5.45, w=.8, cover=False)
    place('Tub', tub, [EN], x=6.6, y=1.0, rot=0, cover=False)
    place('Toilet', toilet, [EN, VL], wf=('y', 0, 1), u=5.78, w=.45, cover=False, oh=1.1)
    place('Washbasin', washbasin, [EN, CHROME], wf=('y', 2.0, -1), u=5.85, w=.6, cover=False, oh=1.0)
furnish()
if COVER: place('LoneChair', chair, [VL], x=1.8, y=3.4, rot=180, cover=False)

def mirror_z(o):
    me = o.data; me.transform(Matrix.Translation((0, 0, H)) @ Matrix.Scale(-1, 4, (0, 0, 1)))
    bm = bmesh.new(); bm.from_mesh(me); bmesh.ops.reverse_faces(bm, faces=bm.faces[:]); bm.to_mesh(me); bm.free()
for name, fn, mats, (x, y), rot, room, cov in PIECES:
    bm = bmesh.new(); fn(bm)
    if COVER and cov:
        xs = [v.co.x for v in bm.verts]; ys = [v.co.y for v in bm.verts]; zs = [v.co.z for v in bm.verts]; bm.free(); bm = bmesh.new()
        a0, a1, b0, b1, top = min(xs) - .006, max(xs) + .006, min(ys) - .03, max(ys) + .03, max(zs) + .03
        fl = .09 if min(zs) < .05 else 0.0; zb = 0 if min(zs) < .05 else min(zs) - .05
        hexa(bm, lambda a, b, c: (a + (fl * (1 if a > 0 else -1) if c == 0 else 0), b + (fl * (1 if b > 0 else -1) if c == 0 else 0) if b < max(ys) else b, c), (a0, a1), (b0, min(b1, -.002) if max(ys) > -.01 else b1), (zb, top), 0)
        for fc in bm.faces: fc.normal_update()
        bmesh.ops.delete(bm, geom=[fc for fc in bm.faces if all(v.co.z < zb + .001 for v in fc.verts)], context='FACES')       # open-bottom drape
        mats = [SHEET]
    o = make(name, bm, room, mats, loc=(x, y, 0), rot=(0, 0, math.radians(rot)))
    if CEIL and room == 'Room' and name != 'Chandelier': mirror_z(o)
    if CEIL and name == 'Chandelier': mirror_z(o)
# wall carpet / clock / picture / calendar
if not LONG and not EMPTY:
    bm = bmesh.new(); f = quad(bm, [(.6, .0015, .95), (2.6, .0015, .95), (2.6, .0015, 2.35), (.6, .0015, 2.35)], 0)
    uvl = bm.loops.layers.uv.new('UVMap')
    for l, uv in zip(f.loops, ((1, 0), (1, 1), (0, 1), (0, 0))): l[uvl].uv = uv
    f.normal_update()
    if f.normal.y < 0: f.normal_flip()
    o = make('WallCarpet', bm, 'Room', [SHEET if COVER else xm('T_A_Carpet')], recalc=False); occupy(('y', 0, 1), .6, 2.6, .95, 2.35, 'WallCarpet')
    if CEIL:
        o.data.transform(Matrix.Translation((0, 0, 3.3)) @ Matrix.Scale(-1, 4, (0, 0, 1)))
    for n_, fn, mats, wf, u, z in (('Clock', clock, [VD, xm('T_A_Clock')], ('x', 0, 1), 1.4, 1.95), ('Painting', lambda bm: picture(bm, .6, .5), [tm('T_A_VeneerDark'), xm('T_A_Painting')], ('x', 3.6, -1), 4.4, 1.65),
                                   ('Calendar', lambda bm: picture(bm, .32, .45), [flat('M_Paper', (.85, .83, .78)), xm('T_A_Calendar')], ('x', 3.75, 1), 4.8, 1.4)):
        bm = bmesh.new(); fn(bm); n = nrm(wf); p = F(wf)(u, 0, 0)
        o = make(n_, bm, room_at(p[0] + n.x * .1, p[1] + n.y * .1), [SHEET, SHEET] if (COVER and n_ != 'Calendar') else mats, loc=(p[0], p[1], z), rot=(0, 0, math.atan2(n.x, -n.y)))
        if CEIL and o.users_collection[0].name == 'Room': mirror_z(o); o.location.z = 0; o.data.transform(Matrix.Translation((0, 0, -z)))
        occupy(wf, u - .32, u + .32, z, z + .5, n_)
# ---------------------------------------------------------------- skirting boards
bm = bmesh.new()
for wf, a, b in SEGS:
    rm = room_at(*F(wf)((a + b) / 2, 0, .1)[:2])
    if rm == 'Bath': continue
    ins = .02 if wf[0] == 'x' else .001
    for x0, x1 in free_spans(wf, a + ins, b - ins, 0, .07, pad=.002): lbox(bm, wf, x0, x1, .0005, .07, 0, .016)
make('Skirting', bm, 'Shell', [VD])

# ---------------------------------------------------------------- floor clutter: letters / newspapers
if COVER or EMPTY:
    bm = bmesh.new(); uvl = bm.loops.layers.uv.new('UVMap'); n = 340 if COVER else 26; k = 0; placed = []; tries = 0
    while k < n and tries < 20000:
        tries += 1
        rn = R.choice(['Room', 'Room', 'Hall'] if COVER else ['Room', 'Hall']); r = ROOMS[rn]; x, y = R.uniform(r[0] + .2, r[2] - .2), R.uniform(r[1] + .2, r[3] - .2)
        sx, sy = (.16, .08) if COVER else (.6, .42); a = math.radians(R.uniform(0, 360)); tx, ty = (math.radians(R.uniform(-5, 5)), math.radians(R.uniform(-5, 5))) if COVER else (0, 0)
        z0 = .016 + R.random() * (.06 if COVER else .03); M = Matrix.Translation((x, y, z0)) @ Matrix.Rotation(a, 4, 'Z') @ Matrix.Rotation(tx, 4, 'X') @ Matrix.Rotation(ty, 4, 'Y')
        cs = [M @ Vector((p, q, 0)) for p, q in ((-sx / 2, -sy / 2), (sx / 2, -sy / 2), (sx / 2, sy / 2), (-sx / 2, sy / 2))]
        if min(c.z for c in cs) < .012: continue
        rr = math.hypot(sx, sy) / 2
        if any(math.hypot(x - px, y - py) < rr + pr and abs(z0 - pz) < (.004 if COVER else .008) for px, py, pr, pz in placed): continue
        placed.append((x, y, rr, z0))
        f = quad(bm, [tuple(c) for c in cs], 0)
        for l, uv in zip(f.loops, ((0, 0), (1, 0), (1, 1), (0, 1))): l[uvl].uv = uv
        k += 1
    make('Decal_Letters' if COVER else 'Decal_Newspapers', bm, 'Props', [xm('T_A_Envelope' if COVER else 'T_A_Newspaper')], recalc=False)

# ---------------------------------------------------------------- decals: AO strips, stains, backsplash, scuffs
FD, CD, WD = bmesh.new(), bmesh.new(), bmesh.new(); DT = ['T_ID_EdgeGrime', 'T_ID_CornerShadow', 'T_ID_WaterStain', 'T_A_Backsplash', 'T_ID_Scuffs', 'T_ID_Mold', 'T_ID_Crack', 'T_ID_Debris']
DI = {t: i for i, t in enumerate(DT)}
for wf, a, b in SEGS:
    f = F(wf); z = .0015 if wf[0] == 'y' else .0025
    for bm_, zz, tex, d in ((FD, z + .0005, 'T_ID_EdgeGrime', .28), (CD, H - z, 'T_ID_CornerShadow', .3)):
        p0 = f(a, 0, 0); pts = [(p[0], p[1], zz) for p in (f(a, 0, 0), f(b, 0, 0), f(b, 0, d), f(a, 0, d))]
        fc = quad(bm_, pts, DI[tex]); fc.normal_update()
        if (fc.normal.z < 0) != (bm_ is CD): fc.normal_flip()
        uvl = bm_.loops.layers.uv.get('UVMap') or bm_.loops.layers.uv.new('UVMap')
        for l in fc.loops:
            co = Vector(l.vert.co); l[uvl].uv = ((co - Vector((p0[0], p0[1], zz))).dot(Vector(f(1, 0, 0)) - Vector(f(0, 0, 0))) / 2.0, (co - Vector((p0[0], p0[1], zz))).dot(nrm(wf)) / d)
for k in range(4 if not EMPTY else 9):
    rn = R.choice(RN); r = ROOMS[rn]; x, y = R.uniform(r[0] + .5, r[2] - .5), R.uniform(r[1] + .5, r[3] - .5)
    floor_decal(CD, x, y, H - .006 - k * .0012, R.uniform(.8, 1.4), R.uniform(.8, 1.4), R.uniform(0, 360), DI['T_ID_WaterStain'], down=True)
if not LONG:
    for u, z0, z1 in ((4.75, .86, 1.45), (5.4, .87, 1.45)): wall_decal(WD, ('x', 7.0, -1), u - .3 if u == 4.75 else u - .42, u + .3 if u == 4.75 else u + .42, z0 + .2 if u == 4.75 else z0, z1, .003, DI['T_A_Backsplash'], (0, 0, 1.5, 1.5))
for wf, a, b in SEGS:
    if R.random() < .45 and b - a > 1.4:
        u = R.uniform(a + .6, b - .6)
        if is_free(wf, u - .5, u + .5, .1, .5): wall_decal(WD, wf, u - .5, u + .5, .1, .5, .003, DI['T_ID_Scuffs'])
    if (EMPTY or COVER) and R.random() < .3 and b - a > 1.4:
        u = R.uniform(a + .6, b - .6)
        if is_free(wf, u - .5, u + .5, 1.6, 2.5): wall_decal(WD, wf, u - .5, u + .5, 1.6, 2.5, .005, DI['T_ID_Crack'])
if EMPTY:
    for k in range(5):
        r = ROOMS[R.choice(['Room', 'Hall'])]; floor_decal(FD, R.uniform(r[0] + .5, r[2] - .5), R.uniform(r[1] + .5, r[3] - .5), .004 + k * .0012, 1.0, 1.0, R.uniform(0, 360), DI['T_ID_Debris'])
DM_ = [dm(t) for t in DT]
make('Decal_Floor', FD, 'Decals', DM_, recalc=False); make('Decal_Ceiling', CD, 'Decals', DM_, recalc=False); make('Decal_Walls', WD, 'Decals', DM_, recalc=False)

# ---------------------------------------------------------------- lamps + lights
def lampshade(name, x, y, lit, kind='shade'):
    bm = bmesh.new()
    if kind == 'shade': cyl(bm, (x, y, H - .3), (x, y, H), .005, 4, 0); cyl(bm, (x, y, H - .45), (x, y, H - .3), .16, 10, 0, r1=.05); sphere(bm, (x, y, H - .4), .035, 1, 1 if lit else 2, 6, 4)
    elif kind == 'plafond': cyl(bm, (x, y, H - .08), (x, y, H), .17, 10, 1 if lit else 2)
    else: cyl(bm, (x, y, H - .35), (x, y, H), .005, 4, 0); cyl(bm, (x, y, H - .42), (x, y, H - .35), .02, 6, 0); sphere(bm, (x, y, H - .452), .035, 1, 1 if lit else 2, 6, 4)
    make(name, bm, 'Lamps', [flat('M_Shade', (.55, .4, .25), .6), LAMPG, DEADG])
    if lit: LIGHTS.append(('Light_' + name, (x, y, H - .55), 30 if kind != 'bulb' else 22, LC))
if LONG:
    for k in range(5): lampshade('Lamp_Hall_%d' % k, 4.5, 1.4 + k * 3.0, k in (0, 3), 'shade')
    lampshade('Lamp_Kitchen', 5.4, HL + 1.4, True, 'plafond')
else:
    lit_all = not (COVER or EMPTY)
    if CEIL: LIGHTS.append(('Light_Chandelier_Floor', (1.8, 3.0, .6), 40, LC))
    elif lit_all: LIGHTS.append(('Light_Chandelier', (1.8, 3.0, H - .6), 45, LC))
    if EMPTY or COVER: lampshade('Lamp_Room_Bulb', 1.8, 3.6, True, 'bulb')
    lampshade('Lamp_Hall', 4.5, 1.7, lit_all or COVER, 'shade'); lampshade('Lamp_Kitchen', 5.4, 4.8, lit_all, 'plafond')
    lampshade('Lamp_Bath', 6.2, 1.0, False, 'plafond'); lampshade('Lamp_Pantry', 6.2, 2.8, False, 'bulb')
for n, loc, e, c in LIGHTS: light(n, loc, e, c)
marker('Spawn_Player', (4.5, .7, 0), 90); marker('Exit_Entrance', (4.5, .2, 0), -90)
finish(anchors=['Ceiling', 'Walls', 'Skirting'], ignore=[o.name for o in ST['root'].all_objects if o.name.startswith('Door_') and not o.name.endswith('_Frame')]
       + (['Chandelier'] if CEIL else []) + IGNX + ['WallCarpet', 'Decal_Letters', 'Decal_Newspapers'])
