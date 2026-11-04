"""Strange spaces behind the doors (not necessarily apartments). usage: python3 build_space.py <variant> <out.blend>
  Sorting - a post sorting hall that cannot fit into the block: walls of post office boxes 7 m high, tables, green lamps, letters
  Queue   - a polyclinic corridor: a queue of empty coats on the seats, facing a lit reception window
  Nested  - a room with the same room inside it at half size, and again, and again (wallpaper on the outside too)
  Stack   - the kitchens of all 14 floors stacked with the floors between them gone: ledges, doors, sinks and lamps hang on the walls
Reuses the furniture library of build_apartment.py."""
import sys, os, math, random
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from kit import *
from PIL import Image
VAR, OUT = sys.argv[-2], os.path.abspath(sys.argv[-1])
R = random.Random(sum(map(ord, VAR))); T, TH = .15, .015
start(OUT, os.path.splitext(os.path.basename(OUT))[0])
_src = open(os.path.join(HERE, 'build_apartment.py')).read(); exec(_src[_src.index('def B(bm, x0'):_src.index('def furnish():')])

VD, VL, EN = tm('T_A_VeneerDark', (.8, .8)), tm('T_A_VeneerLight', (.8, .8)), tm('T_A_Enamel', (.6, .6))
METAL, CHROME, BLACK = flat('M_Metal_Dark', (.1, .09, .08), .5), flat('M_Chrome', (.6, .6, .58), .2), flat('M_Black', (.015, .015, .015))
BRASS = flat('M_Metal_Brass', (.45, .33, .12), .45); NIGHT = glow('M_Glass_Night', (.02, .03, .06), 1.0); FRAME = tm('T_Wood_Frame_M')
LC = (1, .78, .5); LAMPG = glow('M_Lamp_Glow', LC, 6.0); DEADG = flat('M_Lamp_DeadGlass', (.5, .48, .42), .4)
WIRE = flat('M_Wire', (.05, .05, .05)); VOID = flat('M_Void', (0, 0, 0), 1.0); OUTM = flat('M_Outer', (.05, .05, .05))
LIGHTS, IGN = [], []

# ---------------------------------------------------------------- shared pieces
def shell(name, hi, cuts, matfn, mats, planes=(), col='Shell'):
    """box room (0,0,0)-hi with walls T thick, floor and ceiling; cuts = [(lo, hi)] boxes; matfn(centre, normal) -> material index"""
    bm = bmesh.new(); wbox(bm, (-T, -T, -.2), (hi[0] + T, hi[1] + T, hi[2] + .2)); o = make(name, bm, col, mats)
    cs = []
    for a, b in [((0, 0, 0), hi)] + list(cuts): c = bmesh.new(); wbox(c, a, b); cs.append(c)
    boolean_cut(o, cs); bm = bmesh.new(); bm.from_mesh(o.data)
    if planes:
        bisect(bm, planes); bmesh.ops.dissolve_degenerate(bm, dist=1e-5, edges=bm.edges[:]); bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=1e-5)
    for fc in bm.faces: fc.material_index = matfn(fc.calc_center_median(), fc.normal)
    bmesh.ops.triangulate(bm, faces=[fc for fc in bm.faces if len(fc.verts) > 4], ngon_method='EAR_CLIP')
    bm.to_mesh(o.data); bm.free(); return o
def outside(c, hi, e=1e-3): return c.x < -T + e or c.x > hi[0] + T - e or c.y < -T + e or c.y > hi[1] + T - e or c.z < -.2 + e or c.z > hi[2] + .2 - e
def casing(bm, wf, u0, u1, h, a=.065, d=.012, w0=0.0, mi=0, z0=0.0):
    prism(bm, wf, [(u0 - a, z0), (u0, z0), (u0, z0 + h), (u1, z0 + h), (u1, z0), (u1 + a, z0), (u1 + a, z0 + h + a), (u0 - a, z0 + h + a)], w0, w0 + d, mi)
def door(name, wf, u, wd=.8, h=2.0, tex=None, cell=(.5, 0, 1, 1), z0=0.0, col='Doors'):
    f = F(wf); u0, u1 = u - wd / 2, u + wd / 2
    bm = bmesh.new(); casing(bm, wf, u0, u1, h, z0=z0); make(name + '_Frame', bm, col, [FRAME], origin=f(u, z0, 0))
    la, lb, za, zb = u0 + .004, u1 - .004, z0 + TH + .004, z0 + h - .004; w0, w1 = -T / 2 - .02, -T / 2 + .02
    bm = bmesh.new(); caps = prism(bm, wf, [(la, za), (lb, za), (lb, zb), (la, zb)], w0, w1, 0)
    for fc in bm.faces:
        if fc not in caps: fc.material_index = 1
    for c in caps: set_uv(bm, c, wf, la, lb, za, zb, cell)
    hx = lb - .07; lbox(bm, wf, hx - .1, hx + .01, z0 + .97, z0 + .995, w1 + .02, w1 + .032, 2); lbox(bm, wf, hx - .008, hx + .008, z0 + .97, z0 + .995, w1, w1 + .02, 2)
    o = make(name, bm, col, [tex or xm('T_A_Doors'), flat('M_Door_Edge', (.25, .2, .14)), BRASS], origin=f(la, za, (w0 + w1) / 2)); IGN.append(o.name); return o
def window(name, wf, uc, ww=1.2, z0=.85, z1=2.25, glass=None, col='Windows'):
    f = F(wf); a0, a1 = uc - ww / 2, uc + ww / 2; wa, wb = -T / 2 - .03, -T / 2 + .03; bm = bmesh.new()
    for a in ((a0, a0 + .06, z0, z1), (a1 - .06, a1, z0, z1), (a0 + .0605, a1 - .0605, z1 - .06, z1), (a0 + .0605, a1 - .0605, z0, z0 + .09), (uc - .03, uc + .03, z0 + .0905, z1 - .0605)):
        lbox(bm, wf, a[0], a[1], a[2], a[3], wa, wb, 0)
    if glass is not None:
        for a, b in ((a0 + .06, uc - .03), (uc + .03, a1 - .06)): lbox(bm, wf, a, b, z0 + .09, z1 - .06, -T / 2 - .005, -T / 2 + .005, 1)
    lbox(bm, wf, a0 - .06, a1 + .06, z0 - .03, z0 + .004, 0, .07, 0)
    make(name, bm, col, [FRAME, glass or FRAME], origin=f(uc, z0, 0))
def radiator(name, wf, uc, ww=1.2, z0=0.0, col='Windows'):
    f = F(wf); bm = bmesh.new()
    for k in range(int(ww / .1)):
        a = uc - ww / 2 + .1 + k * .09
        if a + .06 > uc + ww / 2 - .1: break
        prism(bm, wf, [(a, z0 + .14), (a + .06, z0 + .14), (a + .065, z0 + .2), (a + .065, z0 + .6), (a + .06, z0 + .66), (a, z0 + .66), (a - .005, z0 + .6), (a - .005, z0 + .2)], .06, .15)
    for z in (.2, .6): cyl(bm, f(uc - ww / 2, z0 + z, .105), f(uc + ww / 2 - .08, z0 + z, .105), .02, 8)
    for a in (uc - ww / 2 + .02, uc + ww / 2 - .14): lbox(bm, wf, a, a + .03, z0 + .58, z0 + .62, 0, .06)
    make(name, bm, col, [tm('T_Radiator')], origin=f(uc, z0, 0))
def pendant(name, x, y, ztop, zb, lit, shade=None, energy=30, col='Lamps', flicker=False):
    bm = bmesh.new(); cyl(bm, (x, y, zb + .14), (x, y, ztop), .004, 4, 0); cyl(bm, (x, y, zb), (x, y, zb + .15), .17, 10, 3, r1=.05)
    sphere(bm, (x, y, zb - .012), .035, 1, 1 if lit else 2, 6, 4)
    make(name, bm, col, [WIRE, LAMPG, DEADG, shade or flat('M_Shade', (.55, .4, .25), .6)])
    if lit: LIGHTS.append(('Light_' + name + ('_Flicker' if flicker else ''), (x, y, zb - .15), energy, LC))
def ao(segs, h, floor=True, ceil=True, z0=0.0):
    bm = bmesh.new(); uvl = bm.loops.layers.uv.new('UVMap')
    for wf, a, b in segs:
        f = F(wf); lay = .0015 if wf[0] == 'y' else .0025; n_ = nrm(wf); ud = Vector(f(1, 0, 0)) - Vector(f(0, 0, 0))
        for z, mi, d, down, on in ((z0 + lay + .0005, 0, .28, False, floor), (h - lay, 1, .3, True, ceil)):
            if not on: continue
            p0 = Vector(f(a, 0, 0)); fc = quad(bm, [(p[0], p[1], z) for p in (f(a, 0, 0), f(b, 0, 0), f(b, 0, d), f(a, 0, d))], mi); fc.normal_update()
            if (fc.normal.z < 0) != down: fc.normal_flip()
            for lp in fc.loops:
                q = Vector(lp.vert.co) - p0; q.z = 0; lp[uvl].uv = (q.dot(ud) / 2.0, q.dot(n_) / d)
    make('Decal_AO', bm, 'Decals', [dm('T_ID_EdgeGrime'), dm('T_ID_CornerShadow')], recalc=False)
def scatter_letters(name, n, pick, z0=.004, tilt=6, size=(.16, .08), dz=.05):
    """envelopes on the floor: pick() -> (x, y) or None"""
    bm = bmesh.new(); uvl = bm.loops.layers.uv.new('UVMap'); placed = []; k = tries = 0; sx, sy = size
    while k < n and tries < 30000:
        tries += 1; p = pick()
        if p is None: continue
        x, y = p; a = math.radians(R.uniform(0, 360)); tx, ty = math.radians(R.uniform(-tilt, tilt)), math.radians(R.uniform(-tilt, tilt)); z = z0 + R.random() * dz
        M = Matrix.Translation((x, y, z)) @ Matrix.Rotation(a, 4, 'Z') @ Matrix.Rotation(tx, 4, 'X') @ Matrix.Rotation(ty, 4, 'Y')
        cs = [M @ Vector((p_, q_, 0)) for p_, q_ in ((-sx / 2, -sy / 2), (sx / 2, -sy / 2), (sx / 2, sy / 2), (-sx / 2, sy / 2))]
        if min(c.z for c in cs) < z0 - .002: continue
        rr = math.hypot(sx, sy) / 2
        if any(math.hypot(x - px, y - py) < rr + pr and abs(z - pz) < .004 for px, py, pr, pz in placed): continue
        placed.append((x, y, rr, z)); fc = quad(bm, [tuple(c) for c in cs], 0)
        for lp, uv in zip(fc.loops, ((0, 0), (1, 0), (1, 1), (0, 1))): lp[uvl].uv = uv
        k += 1
    make(name, bm, 'Props', [xm('T_A_Envelope')], recalc=False); IGN.append(name)
def glowtex(name, tex, strength):
    if name in ST['mats']: return ST['mats'][name]
    m = xm(tex); m = m.copy(); m.name = name; nt = m.node_tree; b = nt.nodes.get('Principled BSDF')
    n = [x for x in nt.nodes if x.type == 'TEX_IMAGE'][0]; nt.links.new(n.outputs['Color'], b.inputs['Emission Color']); b.inputs['Emission Strength'].default_value = strength
    ST['mats'][name] = m; ST['MS'][name] = None; return m
def put(name, fn, mats, x, y, rot=0, z=0.0, col='Props'):
    bm = bmesh.new(); fn(bm); return make(name, bm, col, mats, loc=(x, y, z), rot=(0, 0, math.radians(rot)))
def wall_rot(wf): n = nrm(wf); return math.degrees(math.atan2(n.x, -n.y))
# ================================================================ Sorting: the post hall
if VAR == 'Sorting':
    XA, YA, HS = 10.0, 26.0, 7.0; HI = (XA, YA, HS); DX = 5.0
    MB, CON = tm('T_SP_Mailboxes', (1.6, 1.6)), tm('T_Concrete')
    def mf(c, n):
        if abs(c.x - DX) < .5 and c.y < 1e-3 and c.z < 2.1: return 1
        if outside(c, HI): return 4
        if n.z > .9: return 2
        if n.z < -.9: return 3
        return 1 if c.y < .5 else 0
    shell('Walls', HI, [((DX - .47, -.5, TH), (DX + .47, .3, 2.07))], mf, [MB, CON, tm('T_Floor_ConcreteWorn', (2.4, 2.4)), tm('T_Ceiling_Concrete', (3, 3)), OUTM])
    bm = bmesh.new(); PIL_ = [(('x', 0, 1), 3.25 * k) for k in range(1, 8)] + [(('x', XA, -1), 3.25 * k) for k in range(1, 8)] + [(('y', YA, -1), x) for x in (10 / 3, 20 / 3)]
    for wf, u in PIL_: lbox(bm, wf, u - .2, u + .2, 0, HS, 0, .12, 0)
    for wf, a, b in ((('x', 0, 1), 0, YA), (('x', XA, -1), 0, YA), (('y', YA, -1), 0, XA)):            # wooden ledges between the pilasters
        cuts_ = sorted(u for w_, u in PIL_ if w_ == wf); pts = [a] + [v for u in cuts_ for v in (u - .2, u + .2)] + [b]
        for z in (1.6, 3.2, 4.8, 6.4):
            for i in range(0, len(pts), 2):
                u0, u1 = pts[i] + (.0005 if i else .06), pts[i + 1] - (.0005 if i + 2 < len(pts) else .06)
                lbox(bm, wf, u0, u1, z - .03, z, 0, .05, 1)
    make('Wall_Relief', bm, 'Shell', [CON, VD])
    yl = 9.6; bm = bmesh.new()                                                     # rolling ladder on a rail
    cyl(bm, (.2, 1.0, 6.62), (.2, YA - 1.0, 6.62), .02, 8, 1)
    for k in range(1, 8): lbox(bm, ('x', 0, 1), 3.25 * k - .02, 3.25 * k + .02, 6.6, 6.64, .12, .19, 1)
    for s in (-1, 1): cyl(bm, (.85, yl + s * .24, 0), (.2, yl + s * .24, 6.6), .025, 6, 0)
    for k in range(1, 21):
        z = k * .31; x = .85 - .65 * z / 6.6; B(bm, x - .02, yl - .24, z, x + .02, yl + .24, z + .03, 0)
    make('Rolling_Ladder', bm, 'Props', [VD, METAL])
    TABLES = [(x, y) for y in (4.5, 9.0, 13.5, 18.0, 22.5) for x in (3.2, 6.8)]; GREEN = flat('M_Shade_Green', (.06, .2, .1), .45)
    def rack(bm):
        B(bm, -.6, -.15, 0, .6, .15, .02, 0); B(bm, -.6, .13, .0205, .6, .15, .5, 0)
        for k in range(7): x = -.6 + k * .2; B(bm, x - .006, -.15, .0205, x + .006, .1295, .5, 0)
        for k in range(1, 4):
            for i in range(6): B(bm, -.6 + i * .2 + .0065, -.15, k * .12, -.6 + (i + 1) * .2 - .0065, .1295, k * .12 + .01, 0)
    for i, (x, y) in enumerate(TABLES):
        put(f'Table_{i}', lambda bm: table(bm, 1.0, 2.6, .85, .05), [VD], x, y)
        if i in (0, 3, 4, 7, 9): put(f'Rack_{i}', rack, [VL], x + (.3 if x > DX else -.3), y, rot=90 if x > DX else -90, z=.85)
        pendant(f'Lamp_{i}', x, y, HS, 1.8, i in (1, 6, 8), GREEN, 40)
        bm = bmesh.new(); uvl = bm.loops.layers.uv.new('UVMap')
        for k in range(R.randint(5, 12)):
            px, py = x + R.uniform(-.38, .38) * (.4 if i in (0, 3, 4, 7, 9) else 1), y + R.uniform(-1.1, 1.1); a = math.radians(R.uniform(0, 360)); z = .8515 + k * .0015
            fc = quad(bm, [(px + p * math.cos(a) - q * math.sin(a), py + p * math.sin(a) + q * math.cos(a), z) for p, q in ((-.08, -.04), (.08, -.04), (.08, .04), (-.08, .04))], 0)
            for lp, uv in zip(fc.loops, ((0, 0), (1, 0), (1, 1), (0, 1))): lp[uvl].uv = uv
        make(f'Decal_TableLetters_{i}', bm, 'Props', [xm('T_A_Envelope')], recalc=False)
    put('Chair', chair, [VL], 3.95, 9.4, rot=-75)
    SACK = tm('T_SP_Sack', (.6, .6))
    for i, (x, y) in enumerate(((1.3, 3.0), (1.1, 15.2), (8.8, 6.3), (9.0, 20.4), (5.0, 11.2), (4.8, 16.0), (5.3, 24.4), (8.6, 12.0), (1.4, 23.5))):
        def sack(bm, s=R.uniform(.8, 1.15)):
            sphere(bm, (0, 0, .24 * s), .3 * s, .8, 0, 10, 6, 1.0, .78); cyl(bm, (0, 0, .4 * s), (0, 0, .58 * s), .07 * s, 8, 0, r1=.05 * s); cyl(bm, (0, 0, .5 * s), (0, 0, .53 * s), .062 * s, 8, 1)
        put(f'MailSack_{i}', sack, [SACK, WIRE], x, y, rot=R.uniform(0, 360))
    def pick():
        x, y = R.uniform(.5, XA - .5), R.uniform(1.6, YA - .4)
        if any(abs(x - tx) < .56 and abs(y - ty) < 1.36 for tx, ty in TABLES) or (x < 1.0 and abs(y - yl) < .4): return None
        if R.random() > .25 + .75 * y / YA: return None                           # more letters the further you go
        return x, y
    scatter_letters('Decal_FloorLetters', 380, pick, tilt=3, dz=.014)
    door('Door_Entrance', ('y', 0, 1), DX, .94, 2.07, xm('T_IDoors_Panel80'), (0, 0, 1 / 8, 1))
    ao(wall_segments([(0, 0, XA, YA)]), HS, ceil=False)
    marker('Spawn_Player', (DX, 1.3, 0), 90); marker('Exit_Entrance', (DX, .3, 0), -90); ANCH = ['Walls', 'Wall_Relief']

# ================================================================ Queue: empty coats waiting
if VAR == 'Queue':
    XA, YA = 2.8, 30.0; HI = (XA, YA, H); DOORS_Y = [3.0, 7.2, 11.4, 15.6, 19.8, 24.0]
    WMQ = [wm(f'T_IW_Mint_{c}') for c in 'ABC']
    def mf(c, n):
        if outside(c, HI): return 5
        if n.z > .9: return 3
        if n.z < -.9: return 4
        return int((c.y - .01 * n.y) // 4) % 3
    cuts = [((1.4 - .47, -.5, TH), (1.4 + .47, .3, 2.07)), ((.8, YA - .3, 1.0), (2.0, YA + .5, 1.7))] + [((XA - .3, y - .4, TH), (XA + .5, y + .4, 2.0)) for y in DOORS_Y]
    shell('Walls', HI, cuts, mf, WMQ + [tm('T_IF_Mint', (2.4, 2.4)), tm('T_IC_Mint', (2.0, 2.0)), OUTM], planes=[((0, 4.0 * k, 0), (0, 1, 0)) for k in range(1, 8)])
    door('Door_Entrance', ('y', 0, 1), 1.4, .94, 2.07, xm('T_A_Doors'), (0, 0, .5, 1))
    SIG = xm('T_SP_Signs'); bm = bmesh.new()
    for i, y in enumerate(DOORS_Y):
        door(f'Door_Office_{i}', ('x', XA, -1), y, .8, 2.0, xm('T_A_Doors'), (0, 0, .5, 1) if i % 2 else (.5, 0, 1, 1)); occupy(('x', XA, -1), y - .47, y + .47, 0, 2.07, 'Door')
        wall_decal(bm, ('x', XA, -1), y + .52, y + .7, 1.45, 1.51, .003, 0, (0, 0, .5, 20 / 64))
    wall_decal(bm, ('x', 0, 1), 10.1, 11.0, 1.62, 1.8, .003, 0, (0, 22 / 64, 1, 42 / 64)); wall_decal(bm, ('y', YA, -1), .9, 1.9, 1.86, 2.08, .003, 0, (0, 44 / 64, 1, 1))
    make('Decal_Signs', bm, 'Props', [SIG], recalc=False)
    bm = bmesh.new(); lbox(bm, ('y', YA, -1), .8, 2.0, 1.0, 1.7, -.085, -.075, 0); lbox(bm, ('y', YA, -1), .7, 2.1, .97, 1.0, 0, .25, 1)
    make('Reception_Window', bm, 'Props', [glow('M_Glass_Frosted', (.72, .78, .76), 1.4), VL])
    bm = bmesh.new(); fr = lbox(bm, ('y', YA, -1), 2.2, 2.5, 1.74, 1.9, 0, .05, 0); fr.material_index = 1; set_uv(bm, fr, ('y', YA, -1), 2.2, 2.5, 1.74, 1.9, (.5, 0, 1, 20 / 64))
    make('Queue_Display', bm, 'Props', [BLACK, glowtex('M_SP_Signs_Glow', 'T_SP_Signs', 2.0)])
    LIGHTS.append(('Light_Reception', (1.4, YA - .4, 1.4), 12, (.85, .95, 1)))
    TUBE, TDEAD, HOUS = glow('M_Tube_Glow', (.82, .94, 1), 5.0), flat('M_Tube_Dead', (.6, .62, .6), .4), flat('M_Lamp_Housing', (.7, .7, .66), .5)
    for k in range(10):
        y = 1.5 + 3 * k; lit = k not in (2, 5, 7, 9); bm = bmesh.new(); B(bm, 1.34, y - .62, H - .05, 1.46, y + .62, H, 0); cyl(bm, (1.4, y - .58, H - .064), (1.4, y + .58, H - .064), .015, 6, 1 if lit else 2)
        make(f'Lamp_Tube_{k}', bm, 'Lamps', [HOUS, TUBE, TDEAD])
        if lit: LIGHTS.append((f'Light_Tube_{k}' + ('_Flicker' if k == 4 else ''), (1.4, y, H - .25), 18, (.82, .94, 1)))
    def seat_block(bm):
        for sx in (-1.18, 1.18):
            B(bm, sx - .015, -.2, .38, sx + .015, .2, .40, 1)
            for sy in (-.18, .18): cyl(bm, (sx, sy, 0), (sx, sy, .38), .015, 6, 1)
        B(bm, -1.19, -.03, .40, 1.19, .03, .43, 1)
        for k in range(4): x = -.9 + .6 * k; B(bm, x - .25, -.2, .43, x + .25, .2, .46, 0); B(bm, x - .24, .2005, .435, x + .24, .23, .88, 0)
    WOOL = [tm(f'T_SP_Wool_{c}', (.5, .5)) for c in ('Grey', 'Brown', 'Navy')]; FUR = tm('T_SP_Fur', (.3, .3)); FELT = flat('M_Felt', (.07, .065, .06), .9)
    LEATHER = flat('M_Leather', (.06, .04, .03), .45); BAG = flat('M_Bag', (.25, .1, .06), .5)
    def coat(bm):
        rings = [[(rx * math.copysign(abs(math.cos(a)) ** .8, math.cos(a)), cy + ry * math.copysign(abs(math.sin(a)) ** .9, math.sin(a)), z) for a in [i / 14 * 2 * math.pi for i in range(14)]]
                 for z, cy, rx, ry in ((.5, -.01, .18, .13), (.64, .0, .165, .115), (.8, .01, .19, .115), (.96, .02, .215, .11), (1.05, .03, .2, .1), (1.1, .03, .1, .085), (1.19, .035, .105, .09))]
        cup(bm, rings, .015)                                                       # torso: nobody inside, the collar is open
        for s in (-1, 1):
            cup(bm, path_rings([(s * .085, .02, .53), (s * .095, -.2, .54), (s * .1, -.43, .53)], [.085, .08, .075], 8), .01, closed_first=True)   # thighs
            cup(bm, path_rings([(s * .19, .02, .99), (s * .215, .02, .85), (s * .215, -.01, .7), (s * .17, -.2, .62), (s * .13, -.36, .61)], [.055, .057, .054, .05, .047], 8), .01)
        prism(bm, lambda p, q, a: (a, p, q), [(-.44, .53), (-.5, .45), (-.47, .2), (-.43, .2), (-.45, .44), (-.4, .52)], -.16, .16, 0)                      # the coat skirt hanging over the knees
    def shoes(bm):
        for s in (-1, 1): prism(bm, lambda p, q, a: (s * .1 + a, p, q), [(-.47, 0), (-.2, 0), (-.2, .09), (-.33, .09), (-.43, .07), (-.47, .04)], -.045, .045, 0)
    def ushanka(bm): cyl(bm, (0, 0, 0), (0, 0, .1), .115, 10, 0, r1=.1); [B(bm, s * .1 - .02, -.06, -.07, s * .1 + .02, .06, .03, 0) for s in (-1, 1)]
    def fedora(bm): cyl(bm, (0, 0, 0), (0, 0, .012), .17, 12, 0); cyl(bm, (0, 0, .012), (0, 0, .13), .1, 10, 0, r1=.085); cyl(bm, (0, 0, .02), (0, 0, .042), .102, 10, 1)
    def handbag(bm): B(bm, -.13, -.05, 0, .13, .05, .18, 0); cyl(bm, (-.08, 0, .18), (.005, 0, .265), .007, 4, 0); cyl(bm, (-.005, 0, .265), (.08, 0, .18), .007, 4, 0)
    SB = [2.4, 5.8, 9.2, 12.6, 16.0, 19.4, 22.8, 26.2]; wf0 = ('x', 0, 1); rq = wall_rot(wf0)
    for b, u in enumerate(SB):
        bx, by = F(wf0)(u, 0, 0)[:2]; bx += .25; put(f'Seats_{b}', seat_block, [VL, METAL], bx, by, rot=rq, col='Seats')
        for k in range(4):
            sx_ = -.9 + .6 * k; ca, sa = math.cos(math.radians(rq)), math.sin(math.radians(rq)); px, py = bx + sx_ * ca, by + sx_ * sa
            q = R.random()
            if q < .2:                                                            # empty seat: a bag or a hat left on it
                if q < .1: put(f'Bag_{b}_{k}', handbag, [BAG], px, py, rot=rq + R.uniform(-20, 20), z=.46)
                continue
            put(f'Coat_{b}_{k}', coat, [R.choice(WOOL), VOID], px, py, rot=rq + R.uniform(-2, 2), col='Coats')
            put(f'Shoes_{b}_{k}', shoes, [LEATHER], px, py, rot=rq + R.uniform(-8, 8), col='Coats')
            h = R.random(); hat, hm = (ushanka, [FUR]) if R.random() < .5 else (fedora, [FELT, BLACK])
            if h < .12:
                o = put(f'Hat_{b}_{k}', hat, hm, px - .03 * sa, py + .03 * ca, rot=rq, z=1.4, col='Coats'); IGN.append(o.name)   # worn by nobody
            elif h < .4:
                lx, ly = px + .26 * sa, py - .26 * ca; put(f'Hat_{b}_{k}', hat, hm, lx, ly, rot=rq + R.uniform(-30, 30), z=.612, col='Coats')
    ao(wall_segments([(0, 0, XA, YA)]), H)
    marker('Spawn_Player', (1.4, .9, 0), 90); marker('Exit_Entrance', (1.4, .3, 0), -90); ANCH = ['Walls', 'Seats_0']

# ================================================================ Stack: the kitchens of all floors, no floors between them
if VAR == 'Stack':
    XA, YA, LH, NL = 2.8, 3.4, 2.8, 14; HT = LH * NL; HI = (XA, YA, HT)
    WT = ['T_AW_Kitchen_A', 'T_AW_Flowers', 'T_AW_Geo', 'T_AW_Stripes', 'T_AW_Damask', 'T_IW_Ochre_C', 'T_AW_Stripped', 'T_IW_Mint_B']
    LV = ['T_AW_Kitchen_A'] + [R.choice(WT) for k in range(NL - 1)]; WU = list(dict.fromkeys(LV)); WMS = [mat(f'M_{t[2:]}_Stack', t, tile=(4.0, LH)) for t in WU]
    def mf(c, n):
        if outside(c, HI): return len(WU) + 2
        if n.z > .9 and c.z < .01: return len(WU)
        if n.z < -.9 and c.z > HT - .01: return len(WU) + 1
        return WU.index(LV[min(NL - 1, max(0, int((c.z - 1e-3) // LH)))])
    cuts = []
    for k in range(NL):
        z = k * LH; cuts += [((.2, -.5, z + TH), (1.0, .3, z + 2.0)), ((XA - .3, 1.1, z + .85), (XA + .5, 2.3, z + 2.25))]
    shell('Walls', HI, cuts, mf, WMS + [tm('T_AF_KitchenLino', (2.4, 2.4)), tm('T_AC_Ceiling', (2, 2)), OUTM], planes=[((0, 0, k * LH), (0, 0, 1)) for k in range(1, NL)])
    bm = bmesh.new(); LINO = [tm('T_AF_KitchenLino', (2.4, 2.4)), tm('T_AF_Parquet', (2.4, 2.4)), tm('T_AF_Concrete', (2.4, 2.4))]
    for k in range(1, NL):
        z1 = k * LH; z0 = z1 - .2; d = .07; top = R.randrange(3)
        boxes = [((0, 0, z0), (XA, d, z1)), ((0, YA - d, z0), (XA, YA, z1)), ((0, d + .0005, z0), (d, YA - d - .0005, z1)), ((XA - d, d + .0005, z0), (XA, YA - d - .0005, z1))]
        for lo, hi in boxes: wbox(bm, lo, hi, 3)
        for fc in bm.faces:
            fc.normal_update()
            if fc.material_index == 3 and fc.normal.z > .9 and abs(fc.calc_center_median().z - z1) < 1e-4: fc.material_index = top
    make('Ledges', bm, 'Shell', LINO + [tm('T_Concrete')])
    bm = bmesh.new(); GAS = flat('M_GasPipe_Yellow', (.55, .42, .08), .5); cyl(bm, (.05, .12, 0), (.05, .12, HT), .016, 8, 0)
    for k in range(NL): cyl(bm, (.05, .12, k * LH + 1.2), (.11, .12, k * LH + 1.2), .009, 6, 0); B(bm, .1, .1, k * LH + 1.17, .14, .14, k * LH + 1.23, 1)
    make('Gas_Riser', bm, 'Props', [GAS, METAL])
    def wall_sink(bm):
        B(bm, -.25, -.4, .68, .25, 0, .86, 0); B(bm, -.2, -.34, .8, .2, -.06, .862, 2)
        for s in (-1, 1): B(bm, s * .2 - .015, -.3, .62, s * .2 + .015, 0, .68, 1)
        cyl(bm, (0, -.03, .86), (0, -.03, 1.02), .01, 6, 3); cyl(bm, (0, -.03, 1.02), (0, -.17, .98), .01, 6, 3)
    def jar_shelf(bm):
        B(bm, -.4, -.2, 0, .4, 0, .02, 0)
        for k in range(5): x = -.32 + k * .16; cyl(bm, (x, -.1, .02), (x, -.1, .17 + .03 * (k % 2)), .05, 8, 1)
    WD = bmesh.new(); BS = dm('T_A_Backsplash'); wx = ('x', 0, 1); rw = wall_rot(wx)
    GRID = [(round(.8 + .4 * i, 2), round(1.1 + .4 * j, 2)) for i in range(4) for j in range(4)]; R.shuffle(GRID); GRID.remove((1.6, 1.9)); GRID.insert(0, (1.6, 1.9))
    for k in range(NL):
        z = k * LH
        window(f'Window_L{k}', ('x', XA, -1), 1.7, 1.2, z + .85, z + 2.25, NIGHT); radiator(f'Radiator_L{k}', ('x', XA, -1), 1.7, 1.2, z)
        door(f'Door_L{k}', ('y', 0, 1), .6, .8, 2.0, xm('T_A_Doors'), (0, 0, .5, 1), z0=z)
        wall_decal(WD, wx, 1.25, 2.05, z + .86, z + 1.45, .003, 0, (0, 0, 1.5, 1.5))
        if k:
            put(f'Sink_L{k}', wall_sink, [EN, METAL, flat('M_Sink_Inside', (.4, .4, .38), .4), CHROME], .0, 1.65, rot=rw, z=z)
            if R.random() < .7: put(f'WallCabinet_L{k}', lambda bm: cabinet_wall(bm, 1.1), [VL], .0, 2.35, rot=rw, z=z + 1.55)
            if R.random() < .35: put(f'Shelf_L{k}', jar_shelf, [VD, flat('M_Glass_Jar', (.35, .42, .38), .2)], 1.3, YA, rot=0, z=z + 1.7)
            if R.random() < .3: put(f'Clock_L{k}', clock, [VD, xm('T_A_Clock')], 2.25, YA, rot=0, z=z + 1.95)
        gx, gy = GRID[k]; pendant(f'Lamp_L{k}', gx, gy, HT, z + 2.1, k in (0, 4, 9, 13), energy=30 if k == 0 else 45)
        if k in (2, 6, 10): LIGHTS.append((f'Light_Window_L{k}', (XA - .3, 1.7, z + 1.6), 4, (1, .55, .2)))
    make('Decal_Backsplash', WD, 'Decals', [BS], recalc=False)
    put('Fridge', fridge, [EN, xm('T_A_Fridge'), BLACK], 0, 2.95, rot=rw); put('Stove', stove, [EN, xm('T_A_Stove'), BLACK, flat('M_Kettle', (.6, .2, .15), .3)], 0, 2.3, rot=rw)
    put('Sink_L0', sink, [VL, flat('M_Worktop', (.55, .5, .42), .6), CHROME, CHROME], 0, 1.65, rot=rw); put('WallCabinet_L0', lambda bm: cabinet_wall(bm, 1.1), [VL], 0, 1.95, rot=rw, z=1.55)
    put('KitchenTable', kitchen_table, [VL, xm('T_A_Oilcloth')], 2.2, 2.75, rot=90)
    for i, (x, y) in enumerate(((1.65, 2.75), (2.2, 2.1))): put(f'Stool_{i}', stool, [VL], x, y)
    ao(wall_segments([(0, 0, XA, YA)]), H, ceil=False)
    marker('Spawn_Player', (1.4, .9, 0), 90); marker('Exit_Door', (.6, .3, 0), -90); ANCH = ['Walls', 'Ledges']

# ================================================================ Nested: the room inside the room inside the room
if VAR == 'Nested':
    RW, RD, SC = 5.2, 4.4, .5
    MODES = {}
    def NM(tex, mode=None):
        m = mat('M_' + tex[2:] + '_N', tex, mode='explicit')
        if mode is None: w, h = Image.open(TEXD + tex + '.png').size; mode = ('box', w / 64, h / 64)
        MODES[m.name] = mode; return m
    def local_uv(bm, mats):
        uvl = bm.loops.layers.uv.get('UVMap') or bm.loops.layers.uv.new('UVMap')
        for fc in bm.faces:
            s = MODES.get(mats[fc.material_index].name) if mats else None
            if s is None: continue
            n = fc.normal; ax = max(range(3), key=lambda i: abs(n[i])); sg = 1 if n[ax] >= 0 else -1
            for lp in fc.loops:
                c = lp.vert.co; u, v = (sg * c.y, c.z) if ax == 0 else ((-sg * c.x, c.z) if ax == 1 else (c.x, sg * c.y))
                lp[uvl].uv = ((u / 4.0, v / H if ax != 2 else v / 4.0) if s[0] == 'wall' else (u / s[1], v / s[2]))
    WALLP, FLOORP, CEILP = NM('T_AW_Damask', ('wall',)), NM('T_AF_Parquet', ('box', 2.4, 2.4)), NM('T_AC_Ceiling', ('box', 2, 2))
    VDN, SOFA, ARM, FRN, RADN = NM('T_A_VeneerDark', ('box', .8, .8)), NM('T_A_Sofa', ('box', .6, .6)), NM('T_A_Armchair', ('box', .6, .6)), NM('T_Wood_Frame_M'), NM('T_Radiator')
    WARMG = glow('M_Window_Warm', (1, .72, .4), 3.0)
    def emit(name, bm, col, mats, s, O, at=(0, 0, 0), rot=0, recalc=True):
        if recalc: fix_normals(bm)
        local_uv(bm, mats); M = Matrix.Translation(Vector(at)) @ Matrix.Rotation(math.radians(rot), 4, 'Z')
        for v in bm.verts: v.co = Vector(O) + s * (M @ v.co)
        return make(name, bm, col, mats, origin=Vector(O) + s * Vector(at), recalc=False)
    def stenka_s(bm, s):                                                        # wall unit with offsets that survive the scale
        o = max(.002, .003 / s); B(bm, -1.5, -.45, .04, 1.5, 0, 2.2, 0); B(bm, -1.5, -.42, 0, 1.5, -.03, .04, 3)
        front(bm, -.56, .56, .95, 2.15, -.45 - o, 1); front(bm, .64, 1.46, 1.2, 2.15, -.45 - o, 2)
    def nested(L, O):
        s = SC ** L; tg = f'_L{L}'; col = f'Room{tg}'; last = L == 3
        bm = bmesh.new(); wbox(bm, (-T, -T, -.15), (RW + T, RD + T, H + .15)); tmp = make('_tmp', bm, col, [WALLP])
        cs = []
        for a, b in (((0, 0, 0), (RW, RD, H)), ((.6, -.5, TH), (1.4, .3, 2.0)), ((RW - .3, 1.6, .85), (RW + .5, 2.8, 2.25))):
            c = bmesh.new(); wbox(c, a, b); cs.append(c)
        boolean_cut(tmp, cs); bm = bmesh.new(); bm.from_mesh(tmp.data); bpy.data.meshes.remove(tmp.data)
        for fc in bm.faces:
            c, n = fc.calc_center_median(), fc.normal; e = 1e-3; ins = -e < c.x < RW + e and -e < c.y < RD + e and -e < c.z < H + e
            out_ = c.x < -T + e or c.x > RW + T - e or c.y < -T + e or c.y > RD + T - e or c.z < -.15 + e or c.z > H + .15 - e
            if ins and abs(n.z) > .9: fc.material_index = 1 if n.z > 0 else 2
            elif out_: fc.material_index = 2 if n.z > .9 else (0 if L else 3)          # outside of a nested box: wallpaper, roof: ceiling paint
            else: fc.material_index = 0
        bmesh.ops.triangulate(bm, faces=[fc for fc in bm.faces if len(fc.verts) > 4], ngon_method='EAR_CLIP')
        emit('Shell' + tg, bm, col, [WALLP, FLOORP, CEILP, OUTM], s, O, recalc=False)
        g = max(.0005, .0002 / s); bm = bmesh.new(); casing(bm, ('y', 0, 1), .6, 1.4, 2.0, d=max(.012, .005 / s)); emit('Door_Frame' + tg, bm, col, [FRN], s, O)
        bm = bmesh.new(); caps = prism(bm, ('y', 0, 1), [(.604, TH + .004), (1.396, TH + .004), (1.396, 1.996), (.604, 1.996)], -T / 2 - .02, -T / 2 + .02, 0)
        for fc in bm.faces:
            if fc not in caps: fc.material_index = 1
        for c in caps: set_uv(bm, c, ('y', 0, 1), .604, 1.396, TH + .004, 1.996, (.5, 0, 1, 1))
        if L < 2: lbox(bm, ('y', 0, 1), 1.22, 1.33, .97, .995, -T / 2 + .04, -T / 2 + .052, 2); lbox(bm, ('y', 0, 1), 1.317, 1.333, .97, .995, -T / 2 + .02, -T / 2 + .04, 2)
        IGN.append(emit('Door' + tg, bm, col, [xm('T_A_Doors'), flat('M_Door_Edge', (.25, .2, .14)), BRASS], s, O).name)
        wfw = ('x', RW, -1); fw = F(wfw); a0, a1 = 1.6, 2.8; bm = bmesh.new()
        for a in ((a0, a0 + .06, .85, 2.25), (a1 - .06, a1, .85, 2.25), (a0 + .06 + g, a1 - .06 - g, 2.19, 2.25), (a0 + .06 + g, a1 - .06 - g, .85, .94), (2.17, 2.23, .94 + g, 2.19 - g)):
            lbox(bm, wfw, a[0], a[1], a[2], a[3], -T / 2 - .03, -T / 2 + .03, 0)
        if L == 0 or last:
            for a, b in ((a0 + .06, 2.17), (2.23, a1 - .06)): lbox(bm, wfw, a, b, .94, 2.19, -T / 2 - .005, -T / 2 + .005, 1)
        lbox(bm, wfw, a0 - .06, a1 + .06, .82, .854, 0, .07, 0)
        emit('Window' + tg, bm, col, [FRN, WARMG if last else NIGHT], s, O)
        if last: return
        bm = bmesh.new()
        for k in range(10):
            a = 1.7 + k * .09; prism(bm, wfw, [(a, .14), (a + .06, .14), (a + .065, .2), (a + .065, .6), (a + .06, .66), (a, .66), (a - .005, .6), (a - .005, .2)], .06, .15)
        for z in (.2, .6): cyl(bm, fw(1.6, z, .105), fw(2.72, z, .105), .02, 8)
        for a in (1.62, 2.66): lbox(bm, wfw, a, a + .03, .58, .62, 0, .06)
        emit('Radiator' + tg, bm, col, [RADN], s, O)
        sk = bmesh.new()
        for wf, a, b in ((('y', 0, 1), .02, .6 - .066), (('y', 0, 1), 1.4 + .066, RW - .02), (('y', RD, -1), .02, 1.098), (('y', RD, -1), 4.102, RW - .02), (('x', 0, 1), .0005, RD - .0005), (('x', RW, -1), .0005, RD - .0005)):
            lbox(sk, wf, a, b, .0005, .07, 0, .016)
        emit('Skirting' + tg, sk, col, [VDN], s, O)
        for nm, fn, mats, at, rot in (('Sofa', sofa, [SOFA, VDN], (0, 2.2, 0), 90), ('Stenka', stenka if L == 0 else (lambda bm: stenka_s(bm, s)), [VDN, xm('T_A_StenkaGlass'), xm('T_A_Books'), BLACK, BRASS], (2.6, RD, 0), 0),
                                      ('Armchair', armchair, [ARM, VDN], (4.65, .62, 0), -165), ('Chandelier', chandelier, [CHROME, LAMPG], (2.6, 2.2, 0), 0),
                                      ('Clock', clock, [VDN, xm('T_A_Clock')], (3.5, 0, 1.9), 180)):
            bm = bmesh.new(); fn(bm); emit(nm + tg, bm, col, mats, s, O, at, rot)
        bm = bmesh.new(); uvl = bm.loops.layers.uv.new('UVMap'); fc = quad(bm, [(.0015 / s, 1.2, .95), (.0015 / s, 3.2, .95), (.0015 / s, 3.2, 2.35), (.0015 / s, 1.2, 2.35)], 0)
        for lp, uv in zip(fc.loops, ((1, 0), (0, 0), (0, 1), (1, 1))): lp[uvl].uv = uv
        fc.normal_update()
        if fc.normal.x < 0: fc.normal_flip()
        IGN.append(emit('WallCarpet' + tg, bm, col, [xm('T_A_Carpet')], s, O, recalc=False).name)
        cx0, cy0 = (RW - RW * SC) / 2, (RD - RD * SC) / 2; bm = bmesh.new(); floor_decal(bm, RW / 2, RD / 2, .003 / s, RW * SC + .9, RD * SC + .7, 0, 0)
        IGN.append(emit('Rug' + tg, bm, col, [xm('T_A_Rug')], s, O, recalc=False).name)
        cl = Vector(O) + s * Vector((2.6, 2.2, H - .6)); LIGHTS.append(('Light_Chandelier' + tg, tuple(cl), 45 * s * s, LC))
        nested(L + 1, Vector(O) + s * Vector((cx0, cy0, 0)) + Vector((0, 0, .15 * s * SC)))
    nested(0, Vector((0, 0, 0)))
    marker('Spawn_Player', (1.0, .8, 0), 90); ANCH = ['Shell_L0']

# ================================================================ Dunes: not a room at all
if VAR == 'Dunes':
    SZ, NG = 110.0, 70; ST_ = SZ / NG
    def hgt(x, y):
        u, v = x * .8 + y * .6, -x * .6 + y * .8
        h = .9 * math.sin(.16 * u + .9 * math.sin(.06 * v)) + .45 * math.sin(.37 * u + 1.3 + .4 * math.sin(.11 * v)) * math.cos(.21 * v) + .25 * math.sin(.9 * u + .5 * v) + .6 * math.sin(.045 * v + 2.0)
        return 1.8 * h * (.04 + .96 * min(1.0, max(0.0, (math.hypot(x, y) - 6.0) / 12.0)))    # flatter where you come in
    HG = [[hgt(-SZ / 2 + i * ST_, -SZ / 2 + j * ST_) for j in range(NG + 1)] for i in range(NG + 1)]
    def surf(x, y):
        fx, fy = (x + SZ / 2) / ST_, (y + SZ / 2) / ST_; i, j = min(NG - 1, int(fx)), min(NG - 1, int(fy)); u, v = fx - i, fy - j
        h00, h10, h11, h01 = HG[i][j], HG[i + 1][j], HG[i + 1][j + 1], HG[i][j + 1]
        return h00 + u * (h10 - h00) + v * (h11 - h10) if u >= v else h00 + v * (h01 - h00) + u * (h11 - h01)
    bm = bmesh.new(); VG = [[bm.verts.new((-SZ / 2 + i * ST_, -SZ / 2 + j * ST_, HG[i][j])) for j in range(NG + 1)] for i in range(NG + 1)]
    for i in range(NG):
        for j in range(NG): bm.faces.new((VG[i][j], VG[i + 1][j], VG[i + 1][j + 1])); bm.faces.new((VG[i][j], VG[i + 1][j + 1], VG[i][j + 1]))
    make('Dunes', bm, 'Ground', [tm('T_SP_LetterDune', (1.6, 1.6))], recalc=False)
    PX, PY = 2.2, 4.5                                                              # the postbox under the only street lamp
    bm = bmesh.new(); cyl(bm, (PX, PY, surf(PX, PY) - .3), (PX, PY, 1.1 + surf(PX, PY)), .035, 8, 1); z0 = surf(PX, PY) + 1.05
    fr = wbox(bm, (PX - .18, PY - .11, z0), (PX + .18, PY + .11, z0 + .47), 1)
    for f in bm.faces: f.normal_update()
    ff = [f for f in bm.faces if f.calc_center_median().y < PY - .109 and abs(f.normal.y) > .9 and f.calc_center_median().z > z0]
    for f in ff: f.material_index = 0; set_uv(bm, f, ('y', PY - .11, -1), PX - .18, PX + .18, z0, z0 + .47)
    prism(bm, lambda p, q, a: (a, p, q), [(PY - .13, z0 + .47), (PY + .13, z0 + .47), (PY + .13, z0 + .5), (PY, z0 + .54), (PY - .13, z0 + .5)], PX - .2, PX + .2, 1)
    make('Postbox', bm, 'Props', [xm('T_SP_Postbox'), flat('M_Postbox_Blue', (.05, .09, .2), .5)])
    bm = bmesh.new(); uvl = bm.loops.layers.uv.new('UVMap')
    for k in range(5):                                                             # letters stuck in the slot
        x = PX - .14 + k * .07; a = math.radians(R.uniform(-25, 25)); zs = z0 + .4
        fc = quad(bm, [(x - .03, PY - .1, zs), (x + .03, PY - .1, zs), (x + .03 + .05 * math.sin(a), PY - .1 - .1, zs + .03), (x - .03 + .05 * math.sin(a), PY - .1 - .1, zs + .03)], 0)
        for lp, uv in zip(fc.loops, ((0, 0), (1, 0), (1, 1), (0, 1))): lp[uvl].uv = uv
    make('Decal_SlotLetters', bm, 'Props', [xm('T_A_Envelope')], recalc=False)
    LX_, LY_ = PX + 1.0, PY + .9; bm = bmesh.new(); zb = surf(LX_, LY_) - .3
    cyl(bm, (LX_, LY_, zb), (LX_, LY_, zb + 6.8), .1, 8, 0, r1=.07); cyl(bm, (LX_, LY_, zb + 6.6), (PX + .2, PY + .2, zb + 6.7), .03, 6, 0)
    wbox(bm, (PX + .02, PY + .05, zb + 6.55), (PX + .45, PY + .35, zb + 6.72), 0); wbox(bm, (PX + .05, PY + .08, zb + 6.53), (PX + .42, PY + .32, zb + 6.5505), 1)
    make('Street_Lamp', bm, 'Props', [tm('T_Ext_Pole'), glow('M_Sodium_Glow', (1, .6, .25), 8.0)]); LIGHTS.append(('Light_Street', (PX + .23, PY + .2, zb + 6.3), 500, (1, .55, .2)))
    bm = bmesh.new(); POLES = []                                                   # telegraph poles to the horizon, some leaning
    for k in range(9):
        x = -52 + 13 * k; y = 14 + .1 * x; zb = surf(x, y) - .4; lean = math.radians(R.choice((0, 0, 3, 6, 11)) * R.choice((-1, 1)))
        top = Vector((x + 7.2 * math.sin(lean), y, zb + 7.2 * math.cos(lean))); cyl(bm, (x, y, zb), tuple(top), .12, 8, 0, r1=.1)
        ax = Vector((1, .1, 0)).normalized(); side = Vector((-ax.y, ax.x, 0)); ca = Vector((x, y, zb)).lerp(top, (7.2 - .45) / 7.2)
        a_, b_ = ca - side * .7, ca + side * .7; cyl(bm, tuple(a_), tuple(b_), .06, 4, 0)
        ins = [tuple(p + Vector((0, 0, .04))) for p in (ca - side * .6, ca + side * .6)]
        for p in ins: cyl(bm, p, (p[0], p[1], p[2] + .12), .03, 6, 1)
        POLES.append([Vector(p) + Vector((0, 0, .1)) for p in ins])
    for A_, B2 in zip(POLES, POLES[1:]):
        for w in range(2):
            pts = [A_[w].lerp(B2[w], .002 + .996 * t / 10) - Vector((0, 0, .7 * math.sin(math.pi * t / 10))) for t in range(11)]
            rg = [[bm.verts.new(v) for v in ring] for ring in path_rings([tuple(p) for p in pts], [.008] * len(pts), 4)]
            for ra, rb in zip(rg, rg[1:]):
                for q in range(4): bm.faces.new((ra[q], ra[(q + 1) % 4], rb[(q + 1) % 4], rb[q])).material_index = 2
            bm.faces.new(rg[0][::-1]).material_index = 2; bm.faces.new(rg[-1]).material_index = 2
    make('Telegraph_Poles', bm, 'Props', [flat('M_Pole_Wood', (.15, .11, .075), .9), flat('M_Insulator', (.5, .52, .48), .3), WIRE])
    bm = bmesh.new(); zd = surf(0, 0)                                              # the door you came through, standing alone
    for x0, x1 in ((-.54, -.47), (.47, .54)): wbox(bm, (x0, -.075, zd - .3), (x1, .075, zd + 2.07), 0)
    wbox(bm, (-.54, -.075, zd + 2.0705), (.54, .075, zd + 2.14), 0); make('Door_Frame', bm, 'Doors', [FRAME])
    bm = bmesh.new(); caps = prism(bm, lambda p, q, a: (p, a, q), [(0, .02), (.932, .02), (.932, 2.05), (0, 2.05)], -.0225, .0225, 0)
    for fc in bm.faces:
        if fc not in caps: fc.material_index = 1
    uvl = bm.loops.layers.uv.get('UVMap') or bm.loops.layers.uv.new('UVMap')
    for c in caps:
        for lp in c.loops: lp[uvl].uv = (lp.vert.co.x / .932 / 8, (lp.vert.co.z - .02) / 2.03)
    lbox(bm, lambda u, z, w: (u, w, z), .8, .84, .95, 1.1, -.065, -.0225, 2)
    o = make('Door', bm, 'Doors', [xm('T_IDoors_Panel80'), flat('M_Door_Edge', (.25, .2, .14)), BRASS], loc=(-.466, 0, zd), rot=(0, 0, math.radians(-35))); IGN.append(o.name)
    bm = bmesh.new(); uvl = bm.loops.layers.uv.new('UVMap'); fc = quad(bm, [(-.4, .25, surf(-.4, .25) + .006), (.4, .25, surf(.4, .25) + .006), (.4, .75, surf(.4, .75) + .006), (-.4, .75, surf(-.4, .75) + .006)], 0)
    for lp, uv in zip(fc.loops, ((0, 0), (1, 0), (1, 1), (0, 1))): lp[uvl].uv = uv
    make('Decal_Doormat', bm, 'Props', [xm('T_IP_MatRag')], recalc=False)
    bm = bmesh.new(); uvl = bm.loops.layers.uv.new('UVMap'); placed = []; k = tries = 0            # loose letters on top of the dunes
    while k < 520 and tries < 40000:
        tries += 1; rr = 18 * math.sqrt(R.random()); t = R.uniform(0, 2 * math.pi); x, y = rr * math.cos(t), rr * math.sin(t)
        if R.random() < .35: x, y = PX + R.gauss(0, .5), PY + R.gauss(0, .5)                     # a drift below the postbox
        if abs(x) < .6 and abs(y) < .8: continue
        lay = k % 3; a = R.uniform(0, 2 * math.pi)
        if any(math.hypot(x - px, y - py) < .2 and pl == lay for px, py, pl in placed): continue
        placed.append((x, y, lay)); cs = [(x + p * math.cos(a) - q * math.sin(a), y + p * math.sin(a) + q * math.cos(a)) for p, q in ((-.08, -.04), (.08, -.04), (.08, .04), (-.08, .04))]
        fc = quad(bm, [(cx, cy, surf(cx, cy) + .008 + lay * .005) for cx, cy in cs], 0)
        for lp, uv in zip(fc.loops, ((0, 0), (1, 0), (1, 1), (0, 1))): lp[uvl].uv = uv
        k += 1
    make('Decal_Letters', bm, 'Props', [xm('T_A_Envelope')], recalc=False)
    for i, (p, tex) in enumerate((((34, 72, 9), 'T_Ext_Curtain_1'), ((-46, 58, 15), 'T_Ext_Curtain_3'))):   # windows lit in the sky, no building
        bm = bmesh.new(); uvl = bm.loops.layers.uv.new('UVMap'); fc = quad(bm, [(-.6, 0, 0), (.6, 0, 0), (.6, 0, 1.4), (-.6, 0, 1.4)], 0)
        for lp, uv in zip(fc.loops, ((0, 0), (1, 0), (1, 1), (0, 1))): lp[uvl].uv = uv
        for a in ((-.66, -.6), (.6, .66)): wbox(bm, (a[0], -.06, -.06), (a[1], -.002, 1.46), 1)
        for z0_, z1_ in ((-.06, 0), (1.4, 1.46)): wbox(bm, (-.5995, -.06, z0_), (.5995, -.002, z1_), 1)
        wbox(bm, (-.025, -.05, .0005), (.025, -.002, 1.3995), 1)
        o = make(f'Window_Sky_{i}', bm, 'Props', [glowtex(f'M_{tex[2:]}_Glow', tex, 2.5), flat('M_Frame_Dark', (.04, .035, .03), .8)], loc=p, rot=(0, 0, math.atan2(-p[0], p[1]))); IGN.append(o.name)
    marker('Spawn_Player', (0, .9, surf(0, .9)), 90); marker('Exit_Door', (0, -.3, surf(0, -.3)), -90); ANCH = ['Dunes']

for n_, loc, e, c in LIGHTS: light(n_, loc, e, c)
finish(anchors=ANCH, ignore=IGN)
