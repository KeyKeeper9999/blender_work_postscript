"""v2 corridors: themed, hand-painted, decaled.
usage: python3 build_floor_v2.py <layout> <theme> <out.blend>
layouts: corridor, corner, ring (from build_level.py), landing     themes: Ochre, Mint, Panel80, Decay"""
import sys, os, math, random
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from kit import *
LAYOUT, THEME, OUT = sys.argv[-3], sys.argv[-2], os.path.abspath(sys.argv[-1])
_src = open(os.path.join(HERE, 'build_level.py')).read()
exec(_src[_src.index('def door_runs'):_src.index("L = {'corridor'")])
T, TE, TH = .18, .35, .02

def layout_landing():
    S_, N_, W_, E_ = ('y', 0, 1), ('y', 5, -1), ('x', 0, 1), ('x', 9, -1)
    SN, SS, TE_ = ('y', 3.5, -1), ('y', 1.5, 1), ('x', 16, -1)
    D = [('161', S_, 1.6, 'derm_a', 'Mat_Rubber'), ('162', W_, 2.5, 'steel_a', None), ('163', S_, 7.4, 'derm_b', 'Mat_Olive'),
         ('164', SN, 10.6, 'wood_a', None), ('165', SS, 11.4, 'steel_b', 'Mat_Rubber'), ('166', SN, 12.2, 'derm_c', None),
         ('167', ('y', 3.5, -1), 14.6, 'wood_c', 'Mat_Olive'), ('168', ('y', 1.5, 1), 14.6, 'derm_a', None)]
    return dict(
        rooms=[(0, 0, 9, 5), (9, 1.5, 16, 3.5)],
        floors=[('Hall', (0, 0, 9, 5), 'hall'), ('Side', (9, 1.5, 13, 3.5), 'corr'), ('Tambour', (13, 1.5, 16, 3.5), 'tamb_wood')],
        doors=D, stair=(S_, 4.5), lifts=(N_, 3.3, 5.7), windows=[(TE_, 2.5, True)],
        partitions=[('Tambour', 'x', 13, 1.5, 3.5, 'wood', 'hi', 1)],
        beams=[(4.35, 0, 4.65, 5), (11.0, 1.5, 11.3, 3.5)],
        lamps=[(2.2, 2.5, 'plafond', None), (6.8, 2.5, 'flicker', None), (10.4, 2.5, 'bulb', SN), (14.6, 2.5, 'bulb_dead', SN)],
        runs=[(N_, .4, 8.6), (SN, 9.2, 15.6)],
        panels=[(N_, 1.3, 'ElectricPanel', 0), (SS, 12.6, 'ElectricPanel', 110)],
        firecabs=[(W_, 4.2)], mailboxes=(E_, 4.25), chute=((8.45, 0, 9, .55), ('x', 8.45, -1), .275),
        patches=[], ceil_stains=[(6, 0, 9, 2)], phantom_mats=[(W_, 1.0)],
        props=[('bags', [(8.15, .85, .22)]), ('envelopes', [(8.5, 3.9, 20), (8.2, 4.4, -30), (7.9, 3.6, 70)]),
               ('boots', 15.4, 3.2, 180), ('rolled', 15.75, 1.75)],
        spawn=(4.5, .8, 90))

L = {'corridor': layout_corridor, 'corner': layout_corner, 'ring': layout_ring, 'landing': layout_landing}[LAYOUT]()
THEMES = {
    'Ochre': dict(cells=dict(derm_a=0, derm_b=1, derm_c=2, steel_a=5, steel_b=5, wood_a=3, wood_b=4, wood_c=6, boarded=4, sealed=7), stair=3,
                  lamp='cage', lc=(1, .7, .4), le=38, tamb_wood='T_AW_Geo', tamb_floor='T_AF_KitchenLino', pipes=True, frame='T_A_VeneerDark',
                  plates=[((214, 200, 160), (40, 30, 20)), ((180, 140, 60), (30, 20, 10)), ((40, 36, 30), (220, 210, 180))], extras=['stroller', 'stroller', 'boxes2', 'bench']),
    'Mint': dict(cells=dict(derm_a=5, derm_b=3, derm_c=6, steel_a=2, steel_b=7, wood_a=0, wood_b=1, wood_c=4, boarded=4, sealed=6), stair=1,
                 lamp='tube', lc=(.82, .94, 1.0), le=45, tamb_wood='T_AW_Stripes', tamb_floor='T_AF_BathTile', pipes=False, frame='T_Wood_Frame_M',
                 plates=[((228, 228, 222), (30, 50, 60)), ((60, 90, 110), (230, 230, 225)), ((200, 196, 180), (60, 30, 30))], extras=['bench', 'bench', 'plant', 'plant', 'board']),
    'Panel80': dict(cells=dict(derm_a=2, derm_b=3, derm_c=7, steel_a=4, steel_b=4, wood_a=0, wood_b=6, wood_c=1, boarded=1, sealed=5), stair=5,
                    lamp='globe', lc=(1, .8, .55), le=36, tamb_wood='T_AW_Flowers', tamb_floor='T_AF_Parquet', pipes=False, frame='T_A_VeneerDark', wainscot=True,
                    plates=[((176, 140, 70), (30, 20, 10)), ((220, 214, 196), (40, 30, 20)), ((30, 30, 30), (210, 180, 90))], extras=['plant', 'plant', 'plant', 'painting', 'painting', 'mirror']),
    'Decay': dict(cells=dict(derm_a=1, derm_b=4, derm_c=1, steel_a=0, steel_b=5, wood_a=2, wood_b=6, wood_c=7, boarded=7, sealed=3), stair=2,
                  lamp='bulb', lc=(1, .7, .42), le=26, tamb_wood='T_AW_Stripped', tamb_floor='T_AF_Concrete', pipes=True, frame='T_Wood_Frame_M', dead=.25,
                  plates=[((150, 146, 136), (30, 30, 30)), ((90, 70, 40), (200, 190, 160))], extras=['armchair', 'mattress', 'boxes2', 'bucket2', 'bucket2', 'boards']),
}
TH_ = THEMES[THEME]; R = random.Random(sum(map(ord, LAYOUT + THEME)))
start(OUT, os.path.splitext(os.path.basename(OUT))[0])

# ---------------------------------------------------------------- zones, materials
ZONES = [(z, r) for _, r, z in L['floors']]
def zone_at(x, y):
    for tol in (.002, .45):
        for z, r in ZONES:
            if r[0] - tol <= x <= r[2] + tol and r[1] - tol <= y <= r[3] + tol: return z
    return 'corr'
WALLT = [f'T_IW_{THEME}_{c}' for c in 'ABC'] + [TH_['tamb_wood']]
WM = [wm(t) for t in WALLT]
FLOOR = {z: tm(f'T_IF_{THEME}', (2.4, 2.4)) for z in ('corr', 'hall', 'tamb_bare')}; FLOOR['tamb_wood'] = tm(TH_['tamb_floor'], (2.4, 2.4))
CEIL = tm(f'T_IC_{THEME}', (2.0, 2.0)); DOORS = xm(f'T_IDoors_{THEME}'); LIFT = xm(f'T_ILift_{THEME}')
FRAME = tm(TH_['frame']); METAL = flat('M_Metal_Dark', (.10, .09, .08), .5); BRASS = flat('M_Metal_Brass', (.45, .33, .12), .45)
STEEL = flat('M_Metal_Grey', (.32, .32, .31), .45); WIRE = flat('M_Wire', (.05, .05, .05)); BLACK = flat('M_Black', (.012, .012, .012))
CREAM = flat('M_Plastic_Cream', (.75, .70, .58), .6); WIRED = flat('M_Glass_Wired', (.05, .07, .06), .25); NIGHT = glow('M_Glass_Night', (.02, .03, .06), 1.0)
LC = TH_['lc']; LAMPG = glow('M_Lamp_Glow', LC, 6.0); DEADG = flat('M_Lamp_DeadGlass', (.5, .48, .42), .4)
def wall_variant(x, y): return (int(math.floor(x / 4)) * 7 + int(math.floor(y / 4)) * 13) % 3

# ---------------------------------------------------------------- plates atlas
from PIL import Image, ImageDraw, ImageFont
nums = []
for d in L['doors']:
    if d[0] and d[0] not in nums: nums.append(d[0])
PIDX = {n: i for i, n in enumerate(nums)}; atlas = Image.new('RGB', (256, 128)); dr = ImageDraw.Draw(atlas)
fnt = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 12)
for i, n in enumerate(nums):
    bg, fg = TH_['plates'][i % len(TH_['plates'])]; x, y = (i % 8) * 32, (i // 8) * 16
    dr.rectangle((x, y, x + 31, y + 15), fill=bg); dr.rectangle((x, y, x + 31, y + 15), outline=tuple(int(c * .55) for c in bg)); dr.text((x + 16, y + 8), n, font=fnt, fill=fg, anchor='mm')
PLATE_TEX = 'T_NumberPlates_' + ST['root'].name; atlas.save(TEXD + PLATE_TEX + '.png'); PLATES = xm(PLATE_TEX)
def plate_cell(n): i = PIDX[n]; cx, cy = i % 8, i // 8; return (cx / 8, 1 - (cy + 1) / 8, (cx + 1) / 8, 1 - cy / 8)

# ---------------------------------------------------------------- shell
rooms = L['rooms']; X0 = min(r[0] for r in rooms); Y0 = min(r[1] for r in rooms); X1 = max(r[2] for r in rooms); Y1 = max(r[3] for r in rooms)
bm = bmesh.new(); wbox(bm, (X0 - TE, Y0 - TE, 0), (X1 + TE, Y1 + TE, H)); walls = make('Walls', bm, 'Shell', WM)
def ext(r):
    x0, y0, x1, y1 = r; e = .03
    for q in rooms:
        if q is r: continue
        if abs(q[3] - y0) < 1e-6 and q[0] - 1e-6 <= x0 and x1 <= q[2] + 1e-6: y0 -= e
        if abs(q[1] - y1) < 1e-6 and q[0] - 1e-6 <= x0 and x1 <= q[2] + 1e-6: y1 += e
        if abs(q[2] - x0) < 1e-6 and q[1] - 1e-6 <= y0 and y1 <= q[3] + 1e-6: x0 -= e
        if abs(q[0] - x1) < 1e-6 and q[1] - 1e-6 <= y0 and y1 <= q[3] + 1e-6: x1 += e
    return x0, y0, x1, y1
cuts = []
for r in rooms:
    x0, y0, x1, y1 = ext(r); c = bmesh.new(); wbox(c, (x0, y0, -.5), (x1, y1, H + .5)); cuts.append(c)
def dsize(t): return (.7, 2.25) if t == 'wrong' else (.94, 2.07)
for num, wf, u, t, _ in L['doors']:
    wd, h = dsize(t); cuts.append(cutter(wf, u - wd / 2, u + wd / 2, TH, h, .3))
swf, su = L['stair']; cuts.append(cutter(swf, su - .62, su + .62, TH, 2.12, .3))
lwf, ua, ub = L['lifts']; LHW = .5        # 1.0 m lift doors
for u in (ua, ub):
    cuts.append(cutter(lwf, u - LHW, u + LHW, TH, 2.05, T + .2)); c = bmesh.new(); fbox(c, lwf, (u - .82, -.5, -T), (u + .82, H + .5, -T - 1.8)); cuts.append(c)
for wf, uc, _ in L['windows']: cuts.append(cutter(wf, uc - .6, uc + .6, .9, 2.2, TE + .5))
boolean_cut(walls, cuts)
bm = bmesh.new(); bm.from_mesh(walls.data)
RX = {v for r in rooms for v in (r[0], r[2])}; RY = {v for r in rooms for v in (r[1], r[3])}
xs = sorted(({v for _, r, _ in L['floors'] for v in (r[0], r[2])} | {4.0 * k for k in range(int(X0 // 4), int(X1 // 4) + 2)}) - RX)
ys = sorted(({v for _, r, _ in L['floors'] for v in (r[1], r[3])} | {4.0 * k for k in range(int(Y0 // 4), int(Y1 // 4) + 2)}) - RY)
xs = [v for v in xs if all(abs(v - q) > .01 for q in RX)]; ys = [v for v in ys if all(abs(v - q) > .01 for q in RY)]
bisect(bm, [((x, 0, 0), (1, 0, 0)) for x in xs] + [((0, y, 0), (0, 1, 0)) for y in ys])
bmesh.ops.dissolve_degenerate(bm, dist=1e-5, edges=bm.edges[:]); bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=1e-5)
hidden = [f for f in bm.faces if (f.normal.z < -.99 and abs(f.calc_center_median().z) < 1e-4) or (f.normal.z > .99 and abs(f.calc_center_median().z - H) < 1e-4)]
bmesh.ops.delete(bm, geom=hidden, context='FACES')
for f in bm.faces:
    c = f.calc_center_median(); f.material_index = 3 if zone_at(c.x, c.y) == 'tamb_wood' else wall_variant(c.x - .01 * f.normal.x, c.y - .01 * f.normal.y)
bm.to_mesh(walls.data); bm.free()
for name, (x0, y0, x1, y1), z in L['floors']:
    bm = bmesh.new(); bm.faces.new([bm.verts.new(p) for p in ((x0, y0, 0), (x1, y0, 0), (x1, y1, 0), (x0, y1, 0))]); make('Floor_' + name, bm, 'Shell', [FLOOR[z]], recalc=False)
bm = bmesh.new()
for name, (x0, y0, x1, y1), z in L['floors']: bm.faces.new([bm.verts.new(p) for p in ((x0, y0, H), (x0, y1, H), (x1, y1, H), (x1, y0, H))])
bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=1e-5); make('Ceiling', bm, 'Shell', [CEIL], recalc=False)
bm = bmesh.new()
for x0, y0, x1, y1 in L['beams']: wbox(bm, (x0, y0, 2.32), (x1, y1, H))
make('Ceiling_Beams', bm, 'Shell', [CEIL])
SEGS = wall_segments(rooms)
# ---------------------------------------------------------------- doors
def casing(bm, wf, u0, u1, h, a=.07, d=.012, mi=0, w0=0.0):
    prism(bm, wf, [(u0 - a, 0), (u0, 0), (u0, h), (u1, h), (u1, 0), (u1 + a, 0), (u1 + a, h + a), (u0 - a, h + a)], w0, w0 + d, mi)
def leaf_uv(bm, caps, wf, a, b, z0, z1, cell):
    for c in caps: set_uv(bm, c, wf, a, b, z0, z1, cell)
names = set(); MATS_POS = []
for idx, (num, wf, u, t, matname) in enumerate(L['doors']):
    f = F(wf); wd, h = dsize(t); u0, u1 = u - wd / 2, u + wd / 2; tag = num or 'X'
    while 'Door_' + tag in names: tag += '_B'
    names.add('Door_' + tag)
    if t == 'wrong':                                       # a door painted over like the wall: no frame, no handle, no number
        bm = bmesh.new(); lbox(bm, wf, u0 + .004, u1 - .004, TH, h - .004, -.11, -.07)
        mid = f(u, 1, .2); make('Door_' + tag, bm, 'Doors', [WM[wall_variant(mid[0] - .3 * nrm(wf).x, mid[1] - .3 * nrm(wf).y)]], origin=f(u0 + .004, TH, -.09))
        occupy(wf, u0, u1, 0, h, 'Door_' + tag); continue
    cell_i = TH_['cells'][t]; cell = (cell_i / 8, 0, (cell_i + 1) / 8, 1)
    bm = bmesh.new()
    for a, b in ((u0, u0 + .035), (u1 - .035, u1)): lbox(bm, wf, a, b, TH, h, -T, -.004)
    lbox(bm, wf, u0 + .0355, u1 - .0355, h - .035, h - .0005, -T, -.004)
    casing(bm, wf, u0, u1, h); casing(bm, wf, u0 + .018, u1 - .018, h - .018, a=.034, d=.01, w0=.012)
    if t == 'boarded':
        for zc in (.5, 1.1, 1.7): lbox(bm, wf, u0 - .09, u1 + .09, zc - .07, zc + .07, .022, .044, 1)
        lbox(bm, wf, u0 - .05, u1 + .05, .2, .34, .044, .066, 1)
    make(f'Door_{tag}_Frame', bm, 'Doors', [FRAME, tm('T_Planks')], origin=f(u, 0, 0))
    la, lb = u0 + .04, u1 - .04
    bm = bmesh.new(); caps = prism(bm, wf, [(la, TH + .005), (lb, TH + .005), (lb, h - .04), (la, h - .04)], -.11, -.07, 0)
    for fc in bm.faces:
        if fc not in caps: fc.material_index = 1
    leaf_uv(bm, caps, wf, la, lb, TH + .005, h - .04, cell)
    steel = t.startswith('steel')
    if t != 'boarded':
        hx = lb - .08
        lbox(bm, wf, hx - .02, hx + .02, .93, 1.13, -.07, -.064, 2); lbox(bm, wf, hx - .012, hx + .012, 1.01, 1.035, -.064, -.045, 2)
        lbox(bm, wf, hx - .14, hx + .013, 1.0095, 1.0355, -.045, -.032, 2)
        cyl(bm, f(hx, .86, -.07), f(hx, .86, -.06), .016, 8, 2 if not steel else 4)
        if steel: lbox(bm, wf, hx - .02, hx + .02, 1.22, 1.3, -.07, -.064, 2)
        cyl(bm, f(u, 1.55, -.07), f(u, 1.55, -.056), .012, 8, 2)
    pf = lbox(bm, wf, u - .06, u + .06, 1.72, 1.78, -.07, -.066, 3); set_uv(bm, pf, wf, u - .06, u + .06, 1.72, 1.78, plate_cell(num))
    if t == 'sealed':
        fs = lbox(bm, wf, la + .02, la + .32, 1.36, 1.44, -.07, -.068, 5); set_uv(bm, fs, wf, la + .02, la + .32, 1.36, 1.44, (0, .5, 1, .7))
    make('Door_' + tag, bm, 'Doors', [DOORS, flat('M_Door_Edge', (.08, .06, .05)), METAL, PLATES, BRASS, xm('T_A_Newspaper')], origin=f(la, TH, -.09))
    bm = bmesh.new(); ub_ = u0 - .16
    lbox(bm, wf, ub_ - .035, ub_ + .035, 1.42, 1.52, 0, .025, 0); cyl(bm, f(ub_, 1.47, .025), f(ub_, 1.47, .032), .01, 6, 1)
    q_ = F(wf)(ub_, 0, .05); top_ = 2.3195 if any(x0 - .01 < q_[0] < x1 + .01 and y0 - .01 < q_[1] < y1 + .01 for x0, y0, x1, y1 in L['beams']) else H - .0015
    lbox(bm, wf, ub_ - .004, ub_ + .004, 1.52, top_, 0, .006, 2)
    make(f'Door_{tag}_Bell', bm, 'Doors', [CREAM, BLACK, WIRE], origin=f(ub_, 1.42, 0))
    occupy(wf, u0 - .2, u1 + .07, 0, H, 'Door_' + tag)
    if matname:
        bm = bmesh.new(); lbox(bm, wf, u - .32, u + .32, 0, .012, .05, .48)
        MATS_POS.append(F(wf)(u, 0, .27)); make(f'Door_{tag}_Mat', bm, 'Props', [tm('T_IP_MatRag' if idx % 2 else 'T_IP_MatRubber', (.64, .43))], origin=f(u, 0, .27))
for i, (wf, u) in enumerate(L['phantom_mats']):
    bm = bmesh.new(); lbox(bm, wf, u - .32, u + .32, 0, .012, .05, .48); make('Doormat_NoDoor_%d' % i, bm, 'Props', [tm('T_IP_MatRag', (.64, .43))], origin=F(wf)(u, 0, .27))
# stair double door
f = F(swf); u0, u1 = su - .62, su + .62; sc_ = TH_['stair']; scell = (sc_ / 8, 0, (sc_ + 1) / 8, 1)
for side, (a, b, hinge) in (('L', (u0 + .004, su - .002, u0 + .004)), ('R', (su + .002, u1 - .004, u1 - .004))):
    bm = bmesh.new(); caps = prism(bm, swf, [(a, TH), (b, TH), (b, 2.1), (a, 2.1)], -.11, -.07, 0)
    for fc in bm.faces:
        if fc not in caps: fc.material_index = 1
    leaf_uv(bm, caps, swf, a, b, TH, 2.1, scell)
    lbox(bm, swf, a + .1, b - .1, 1.15, 1.95, -.07, -.066, 2); lbox(bm, swf, a + .1, b - .1, 1.15, 1.95, -.114, -.11, 2)
    if side == 'R': lbox(bm, swf, a + .05, a + .17, .98, 1.01, -.066, -.03, 3)
    make('Door_Stair_' + side, bm, 'Doors', [DOORS, flat('M_Door_Edge', (.08, .06, .05)), WIRED, METAL], origin=f(hinge, TH, -.09))
bm = bmesh.new(); casing(bm, swf, u0, u1, 2.12, a=.08); make('Door_Stair_Frame', bm, 'Doors', [FRAME], origin=f(su, 0, 0))
occupy(swf, u0 - .08, u1 + .08, 0, 2.2, 'Door_Stair')

# ---------------------------------------------------------------- lifts
f = F(lwf); LIGHTS = []
for name, u in (('A', ua), ('B', ub)):
    u0, u1 = u - LHW, u + LHW; broken = name == 'B'
    bm = bmesh.new(); casing(bm, lwf, u0, u1, 2.05, a=.12, d=.045); lbox(bm, lwf, u0 - .12, u1 + .12, 2.171, 2.35, 0, .03)
    make('Lift%s_Portal' % name, bm, 'Lift', [tm('T_LiftDoor_Metal')], origin=f(u, 0, 0)); occupy(lwf, u0 - .12, u1 + .12, 0, 2.35, 'Lift' + name)
    gap = .035 if broken else .001
    for side, (a, b, cell) in (('L', (u0 + .004, u - gap, (0, 0, .5, 1))), ('R', (u + gap, u1 - .004, (.5, 0, 1, 1)))):
        bm = bmesh.new(); caps = prism(bm, lwf, [(a, TH), (b, TH), (b, 2.046), (a, 2.046)], -.10, -.07, 0); leaf_uv(bm, caps, lwf, a, b, TH, 2.046, cell)
        make('Lift%s_Door_%s' % (name, side), bm, 'Lift', [LIFT], origin=f((a + b) / 2, TH, -.085))
    bu = u1 + .32
    bm = bmesh.new(); lbox(bm, lwf, bu - .045, bu + .045, 1.1, 1.28, 0, .022, 0); cyl(bm, f(bu, 1.17, .022), f(bu, 1.17, .032), .016, 8, 1)
    lbox(bm, lwf, bu - .02, bu + .02, 1.22, 1.25, .022, .025, 2)
    make('Lift%s_CallButton' % name, bm, 'Lift', [STEEL, flat('M_Button_Dead', (.25, .04, .03), .5) if broken else glow('M_Button_Red', (1, .08, .03), 3.0), glow('M_Lift_Arrow', (1, .55, .1), 2.0) if not broken else BLACK],
         origin=f(bu, 1.1, 0)); occupy(lwf, bu - .045, bu + .045, 1.1, 1.28, 'Lift%s_Button' % name)
    if not broken:
        bm = bmesh.new(); fbox(bm, lwf, (u - .8, -.05, -T), (u + .8, 2.3, -T - 1.4)); cab = make('LiftA_Cab', bm, 'Lift', [tm('T_A_VeneerLight'), tm('T_LiftCab_Floor'), STEEL], origin=f(u, 0, -T))
        c1 = bmesh.new(); fbox(c1, lwf, (u - .75, 0, -T - .05), (u + .75, 2.25, -T - 1.35)); c2 = bmesh.new(); fbox(c2, lwf, (u - LHW, 0, -T + .1), (u + LHW, 2.05, -T - .2)); boolean_cut(cab, [c1, c2])
        bm = bmesh.new(); bm.from_mesh(cab.data)
        for fc in bm.faces:
            nz_, zc = fc.normal.z, fc.calc_center_median().z
            fc.material_index = 1 if (nz_ > .9 and abs(zc) < .01) else (2 if (nz_ < -.9 and abs(zc - 2.25) < .01) else 0)
        bm.to_mesh(cab.data); bm.free()
        bm = bmesh.new(); fbox(bm, lwf, (u - .25, 2.23, -T - .5), (u + .25, 2.25, -T - .9)); make('LiftA_CabLight', bm, 'Lift', [glow('M_LiftCab_Light', (1, .95, .85), 4.0)], origin=f(u, 2.25, -T - .7))
        bm = bmesh.new(); fbox(bm, lwf, (u + .73, .95, -T - .15), (u + .75, 1.5, -T - .35), 0)
        for i in range(5):
            for j in range(2): z = 1.0 + i * .09; w = -T - .2 - j * .07; fbox(bm, lwf, (u + .72, z, w), (u + .73, z + .05, w - .035), 2 if (i, j) == (3, 1) else 1)
        make('LiftA_CabPanel', bm, 'Lift', [STEEL, CREAM, BLACK], origin=f(u + .75, .95, -T - .25))
        LIGHTS += [('Light_LiftA_Cab', f(u, 2.05, -T - .7), 14, (1, .93, .8)), ('Light_LiftA_Button', f(bu, 1.19, .08), .3, (1, .1, .05))]
        bm = bmesh.new(); lbox(bm, lwf, u - .12, u + .12, 2.38, 2.5, 0, .04, 0); lbox(bm, lwf, u - .05, u + .05, 2.41, 2.47, .04, .042, 1)
        make('LiftA_Indicator', bm, 'Lift', [STEEL, glow('M_Lift_Arrow', (1, .55, .1), 2.0)], origin=f(u, 2.38, 0)); occupy(lwf, u - .12, u + .12, 2.38, 2.5, 'Indicator')
    else:
        bm = bmesh.new(); fbox(bm, lwf, (u - .8, -2.5, -T), (u + .8, H + 1, -T - 1.7)); sh = make('LiftB_Shaft', bm, 'Lift', [tm('T_Shaft_Concrete')], origin=f(u, 0, -T))
        c1 = bmesh.new(); fbox(c1, lwf, (u - .75, -2.45, -T + .01), (u + .75, H + .95, -T - 1.65)); boolean_cut(sh, [c1])
        bm = bmesh.new()
        for du in (-.3, 0, .3): cyl(bm, f(u + du, -2.45, -T - .9), f(u + du, H + .95, -T - .9), .012, 6)
        make('LiftB_Cables', bm, 'Lift', [WIRE], origin=f(u, -2.45, -T - .9))
        bm = bmesh.new(); fs = lbox(bm, lwf, bu + .1, bu + .38, 1.40, 1.68, 0, .002); set_uv(bm, fs, lwf, bu + .1, bu + .38, 1.40, 1.68)
        make('LiftB_Sign', bm, 'Lift', [xm('T_Sign_LiftBroken')], origin=f(bu + .24, 1.4, 0)); occupy(lwf, bu + .1, bu + .38, 1.4, 1.68, 'LiftB_Sign')
dmx = (ua + ub) / 2
bm = bmesh.new(); wall_decal(bm, lwf, dmx - .2, dmx + .2, 1.62, 2.02, .002, 0)
make('Decal_FloorNumber', bm, 'Props', [dm('T_FloorNumber_7')], origin=f(dmx, 1.62, 0), recalc=False); occupy(lwf, dmx - .2, dmx + .2, 1.62, 2.02, 'FloorNumber')

# ---------------------------------------------------------------- windows, radiators, partitions
for wi, (wf, uc, jars) in enumerate(L['windows']):
    f = F(wf); a0, a1 = uc - .6, uc + .6; bm = bmesh.new(); nm = 'Window_%d' % (wi + 1)
    for a in ((a0, a0 + .06, .9, 2.2), (a1 - .06, a1, .9, 2.2), (a0 + .0605, a1 - .0605, 2.14, 2.2), (a0 + .0605, a1 - .0605, .9, .99), (uc - .03, uc + .03, .99, 2.14), (a0 + .0605, uc - .03, 1.72, 1.78)):
        lbox(bm, wf, a[0], a[1], a[2], a[3], -.245, -.185, 0)
    for a in ((a0 + .06, uc - .03, .99, 1.72), (a0 + .06, uc - .03, 1.78, 2.14), (uc + .03, a1 - .06, .99, 2.14)): lbox(bm, wf, a[0], a[1], a[2], a[3], -.215, -.205, 1)
    prism(bm, lambda p, q, a: f(p, a, q), [(a0, -.18), (a1, -.18), (a1, 0), (a1 + .07, 0), (a1 + .07, .07), (a0 - .07, .07), (a0 - .07, 0), (a0, 0)], .9, .93, 0)
    make(nm, bm, 'Windows', [tm('T_Wood_Frame_M'), NIGHT], origin=f(uc, .9, 0))
    bm = bmesh.new()
    for i in range(9):
        a = uc - .405 + i * .09; prism(bm, wf, [(a, .14), (a + .06, .14), (a + .065, .2), (a + .065, .64), (a + .06, .7), (a, .7), (a - .005, .64), (a - .005, .2)], .06, .16)
    for z in (.2, .64): cyl(bm, f(uc - .7, z, .11), f(uc + .405, z, .11), .025, 8)
    for a in (uc - .3, uc + .3): lbox(bm, wf, a, a + .04, .66, .70, 0, .06)
    cyl(bm, f(uc - .7, 0, .11), f(uc - .7, H, .11), .025, 8); cyl(bm, f(uc - .7, .38, .11), f(uc - .7, .38, .16), .04, 8)
    make(nm.replace('Window', 'Radiator'), bm, 'Windows', [tm('T_Radiator')], origin=f(uc, 0, 0)); occupy(wf, uc - .75, uc + .67, 0, H, nm)
    if jars:
        bm = bmesh.new()
        for du, r, hh in ((-.4, .05, .14), (-.26, .045, .12), (-.14, .05, .16)): cyl(bm, f(uc + du, .93, -.08), f(uc + du, .93 + hh, -.08), r, 8, 0)
        cyl(bm, f(uc + .35, .93, -.08), f(uc + .35, 1.06, -.08), .07, 8, 1, r1=.085)
        make('Sill_Jars_Plant', bm, 'Props', [flat('M_Glass_Jar', (.35, .42, .38), .2), flat('M_Clay_Pot', (.42, .18, .09))], origin=f(uc, .93, -.08))
        bm = bmesh.new(); p = Vector(f(uc + .35, 1.06, -.08))
        for k in range(3):
            ang = k * 2.1; d_ = Vector((math.cos(ang), math.sin(ang), 1.6)).normalized(); s_ = d_.cross(Vector((0, 0, 1))).normalized()
            uvquad(bm, [tuple(p - s_ * .14), tuple(p + s_ * .14), tuple(p + s_ * .14 + d_ * .3), tuple(p - s_ * .14 + d_ * .3)], 0)
        make('Sill_Plant_Leaves', bm, 'Props', [dm('T_IP_Leaves')], recalc=False)
    LIGHTS.append(('Light_' + nm, f(uc, 1.6, .5), 3, (.45, .55, 1.0)))
for name, ax, c, s0, s1, kind, side, swing in L['partitions']:
    pf = (lambda c: (lambda u, z, w: (c + w, u, z)))(c) if ax == 'x' else (lambda c: (lambda u, z, w: (u, c + w, z)))(c)
    for sw in [(('y', s0, 1), ('y', s1, -1)), (('x', s0, 1), ('x', s1, -1))][ax == 'y']: occupy(sw, c - .06, c + .06, 0, H, name)
    gap = .04 if kind == 'grille' else .1
    oa, ob = (s1 - 1.0, s1 - gap) if side == 'hi' else (s0 + gap, s0 + 1.0); hinge = ob - .004 if side == 'hi' else oa + .004; sgn = -1 if side == 'hi' else 1
    nvec = Vector(pf(0, 0, 1)) - Vector(pf(0, 0, 0)); d0 = (Vector(pf(1, 0, 0)) - Vector(pf(0, 0, 0))) * sgn; rz = 0.0
    for a in ((78, -78) if kind == 'wood' else (55, -55)):
        if (Matrix.Rotation(math.radians(a), 3, 'Z') @ d0).dot(nvec * swing) > 0: rz = math.radians(a); break
    if kind == 'wood':
        bm = bmesh.new(); prism(bm, pf, [(s0, 0), (oa, 0), (oa, 2.05), (ob, 2.05), (ob, 0), (s1, 0), (s1, H), (s0, H)], -.05, .05)
        make(name + '_Partition', bm, 'Tambours', [tm('T_Partition_Wood')], origin=pf((s0 + s1) / 2, 0, 0))
        bm = bmesh.new(); la, lb = oa + .004, ob - .004; lbox(bm, pf, la, lb, 0, 2.046, -.02, .02, 0)
        for s_ in (1, -1): lbox(bm, pf, la + .15, lb - .15, 1.2, 1.9, s_ * .02, s_ * .024, 1)
        hu = la + .06 if side == 'hi' else lb - .18; lbox(bm, pf, hu, hu + .12, .98, 1.01, .02, .06, 2)
        make(name + '_Door', bm, 'Tambours', [tm('T_Partition_Door'), WIRED, METAL], origin=pf(hinge, 0, 0), rot=(0, 0, rz))
    else:
        bm = bmesh.new(); fa, fb = (s0 + .0405, oa - .0405) if side == 'hi' else (ob + .0405, s1 - .0405); da, db = (oa + .0005, s1 - .0405) if side == 'hi' else (s0 + .0405, ob - .0005)
        for a in ((s0, s0 + .04), (oa - .04, oa) if side == 'hi' else (ob, ob + .04), (s1 - .04, s1)): lbox(bm, pf, a[0], a[1], 0, H, -.02, .02)
        lbox(bm, pf, fa, fb, 0, .04, -.02, .02); lbox(bm, pf, fa, fb, 2.05, 2.09, -.02, .02); lbox(bm, pf, da, db, 2.05, 2.09, -.02, .02)
        lbox(bm, pf, fa, fb, H - .04, H, -.02, .02); lbox(bm, pf, da, db, H - .04, H, -.02, .02)
        n = int((fb - fa) / .12)
        for i in range(n): uu = fa + (i + .5) * (fb - fa) / n; lbox(bm, pf, uu - .008, uu + .008, .04, 2.05, -.008, .008)
        for a, b in ((fa, fb), (da, db)):
            n = int((b - a) / .12)
            for i in range(n): uu = a + (i + .5) * (b - a) / n; lbox(bm, pf, uu - .008, uu + .008, 2.09, H - .04, -.008, .008)
        make(name + '_Grille', bm, 'Tambours', [tm('T_Metal_Grille')], origin=pf((s0 + s1) / 2, 0, 0))
        la, lb = oa + .004, ob - .004; bm = bmesh.new()
        lbox(bm, pf, la, la + .03, 0, 2.045, -.015, .015); lbox(bm, pf, lb - .03, lb, 0, 2.045, -.015, .015)
        lbox(bm, pf, la + .0305, lb - .0305, 0, .03, -.015, .015); lbox(bm, pf, la + .0305, lb - .0305, 2.015, 2.045, -.015, .015)
        for i in range(6): uu = la + .03 + (i + 1) * (lb - la - .06) / 7; lbox(bm, pf, uu - .008, uu + .008, .03, 2.015, -.008, .008)
        lk = la + .03 if side == 'hi' else lb - .106; lbox(bm, pf, lk, lk + .076, .95, 1.1, -.03, .03, 1)
        make(name + '_GrilleDoor', bm, 'Tambours', [tm('T_Metal_Grille'), METAL], origin=pf(hinge, 0, 0), rot=(0, 0, rz))

# ---------------------------------------------------------------- wall items
IGN = ['Decal_FloorNumber', 'LiftB_Sign']
for i, (wf, u, tex, ang) in enumerate(L['panels']):
    f = F(wf); bm = bmesh.new(); lbox(bm, wf, u - .3, u + .3, 1.1, 2.0, 0, .14, 0)
    if ang > 45:
        for a in (u - .22, u + .04): lbox(bm, wf, a, a + .16, 1.45, 1.70, .14, .20, 1); lbox(bm, wf, a + .03, a + .13, 1.58, 1.64, .20, .203, 2)
        for k in range(4): lbox(bm, wf, u - .2 + k * .1, u - .17 + k * .1, 1.18, 1.3, .14, .17, 3)
    for k in range(3): lbox(bm, wf, u - .12 + k * .09, u - .1 + k * .09, 2.0, H, .03, .05, 3)
    make('ElectricPanel_%d' % i, bm, 'Props', [tm('T_ElectricPanel_M'), BLACK, CREAM, WIRE], origin=f(u, 1.1, 0))
    bm = bmesh.new(); caps = prism(bm, wf, [(u - .3, 1.1), (u + .3, 1.1), (u + .3, 2.0), (u - .3, 2.0)], .14, .152, 1); set_uv(bm, caps[1], wf, u - .3, u + .3, 1.1, 2.0, (0, 0, 1, 1))
    caps[1].material_index = 0
    o = make('ElectricPanel_%d_Door' % i, bm, 'Props', [xm('T_IP_Shield'), tm('T_ElectricPanel_M')], origin=f(u - .3, 1.1, .146)); o.rotation_euler = (0, 0, rot_into(wf, ang))
    if ang > 45: IGN.append(o.name)
    occupy(wf, u - .3, u + .3, 1.1, H, 'ElectricPanel_%d' % i)
for i, (wf, u) in enumerate(L['firecabs']):
    f = F(wf); bm = bmesh.new(); lbox(bm, wf, u - .3, u + .3, .9, 1.5, 0, .2, 1); fs = lbox(bm, wf, u - .295, u + .295, .905, 1.495, .2, .212, 0); set_uv(bm, fs, wf, u - .295, u + .295, .905, 1.495)
    lbox(bm, wf, u + .2, u + .23, 1.15, 1.25, .212, .232, 2)
    make('FireCabinet_%d' % (i + 1), bm, 'Props', [xm('T_IP_FireCab'), tm('T_FireCabinet'), METAL], origin=f(u, .9, 0)); occupy(wf, u - .3, u + .3, .9, 1.5, 'FireCabinet')
(cx0, cy0, cx1, cy1), hwf, hu = L['chute']
bm = bmesh.new(); wbox(bm, (cx0, cy0, 0), (cx1, cy1, H)); make('TrashChute', bm, 'Props', [WM[0]], origin=((cx0 + cx1) / 2, (cy0 + cy1) / 2, 0))
for wf, a, b in SEGS:
    ax, c, sg = wf
    if ax == 'y' and abs(c - (cy0 if sg > 0 else cy1)) < 1e-6 and a < cx1 and cx0 < b: occupy(wf, cx0, cx1, 0, H, 'TrashChute')
    if ax == 'x' and abs(c - (cx0 if sg > 0 else cx1)) < 1e-6 and a < cy1 and cy0 < b: occupy(wf, cy0, cy1, 0, H, 'TrashChute')
bm = bmesh.new(); lbox(bm, hwf, hu - .205, hu + .205, .75, 1.15, 0, .07, 0); lbox(bm, hwf, hu - .065, hu + .065, 1.08, 1.11, .07, .1, 1)
make('TrashChute_Hatch', bm, 'Props', [tm('T_Chute_Hatch'), METAL], origin=F(hwf)(hu, .75, 0))
mwf, mu = L['mailboxes']; f = F(mwf); bm = bmesh.new(); lbox(bm, mwf, mu - .45, mu + .45, .9, 1.6, 0, .2, 1)
fs = lbox(bm, mwf, mu - .44, mu + .44, .91, 1.59, .2, .21, 0); set_uv(bm, fs, mwf, mu - .44, mu + .44, .91, 1.59)
make('Mailboxes', bm, 'Props', [xm('T_IP_Mailbox'), tm('T_Mailbox')], origin=f(mu, .9, 0))
bm = bmesh.new()
for a, cell in (((-.42, -.2, 1.66, 2.0), (0, 0, .5, 1)), ((.15, .43, 1.7, 2.06), (.5, 0, 1, 1))):
    fs = lbox(bm, mwf, mu + a[0], mu + a[1], a[2], a[3], 0, .002); set_uv(bm, fs, mwf, mu + a[0], mu + a[1], a[2], a[3], cell)
make('Notices', bm, 'Props', [xm('T_Prop_Notices')], origin=f(mu, 1.66, 0)); occupy(mwf, mu - .45, mu + .45, .9, 2.06, 'Mailboxes'); IGN.append('Notices')

# ---------------------------------------------------------------- lamps, wires, pipes
dead_rate = TH_.get('dead', 0)
wires = bmesh.new(); LR = {'cage': .09, 'tube': .07, 'globe': .07, 'bulb': .0055, 'plafond': .165}
def on_run(wf, u): return any(r[0] == wf and r[1] <= u <= r[2] for r in L['runs'])
for wf, u0, u1 in L['runs']:
    gaps = sorted((a0 - .02, a1 + .02) for a0, a1, b0, b1, n in ST['occ'][wf] if b0 <= 2.27 and b1 >= 2.23 and a1 > u0 and a0 < u1)
    pts = [u0]
    for g0, g1 in gaps:
        if g0 > pts[-1]: pts += [g0, g1]
        else: pts[-1] = max(pts[-1], g1) if len(pts) % 2 == 0 else pts[-1]
    pts.append(u1); spans = [(pts[i], pts[i + 1]) for i in range(0, len(pts) - 1, 2) if pts[i + 1] - pts[i] > .05]
    for a, b in spans:
        if any(a < g1 and g0 < b for g0, g1 in gaps): continue
        lbox(wires, wf, a, b, 2.24, 2.26, 0, .02)
        k = a + .3
        while k < b - .1:
            lbox(wires, wf, k - .01, k + .01, 2.235, 2.265, .02, .026); k += .6
ceil_items = []
for i, (x, y, kind, wwf) in enumerate(L['lamps']):
    lit = kind in ('plafond', 'flicker', 'bulb') and not (dead_rate and R.random() < dead_rate and kind != 'flicker')
    fx = 'bulb' if kind in ('bulb', 'bulb_dead') else TH_['lamp']; broken = kind == 'broken'
    bm = bmesh.new(); gm = 1 if lit else 2
    if fx == 'cage':
        cyl(bm, (x, y, H - .03), (x, y, H), .07, 8, 0); sphere(bm, (x, y, H - .12), .06, 1.2, gm, 8, 5)
        for k in range(4):
            a = k * math.pi / 2; cyl(bm, (x + .08 * math.cos(a), y + .08 * math.sin(a), H - .03), (x + .08 * math.cos(a), y + .08 * math.sin(a), H - .21), .005, 4, 0)
        cyl(bm, (x, y, H - .215), (x, y, H - .2), .085, 8, 0)
    elif fx == 'tube':
        wbox(bm, (x - .62, y - .07, H - .06), (x + .62, y + .07, H), 0)
        if not broken: wbox(bm, (x - .6, y - .055, H - .07), (x + .6, y + .055, H - .06), gm)
        else: wbox(bm, (x - .6, y - .055, H - .07), (x - .1, y + .055, H - .06), 2)
    elif fx == 'globe':
        cyl(bm, (x, y, H - .04), (x, y, H), .09, 8, 0); sphere(bm, (x, y, H - .17), .14, 1.0, gm if not broken else 2, 10, 6)
    elif fx == 'bulb':
        cyl(bm, (x, y, H - .35), (x, y, H), .005, 4, 0); cyl(bm, (x, y, H - .42), (x, y, H - .35), .02, 6, 0); sphere(bm, (x, y, H - .452), .035, 1, gm, 6, 4)
    nm = 'Lamp_%02d' % (i + 1) + ('_Flicker' if kind == 'flicker' else '') + ('' if lit else '_Dead')
    make(nm, bm, 'Lamps', [METAL, LAMPG, DEADG], origin=(x, y, H)); ceil_items.append((x, y, .8 if fx == 'tube' else .4))
    if lit: LIGHTS.append((nm.replace('Lamp', 'Light'), (x, y, H - (.5 if fx == 'bulb' else .3)), TH_['le'] * (.6 if fx == 'bulb' else 1), LC))
    if wwf:
        a, c, s = wwf; ul = x if a == 'y' else y; dd = abs((y if a == 'y' else x) - c)
        if not on_run(wwf, ul): ST['warn'].append(f'lamp {nm} not on a run')
        lbox(wires, wwf, ul - .01, ul + .01, 2.26, H, 0, .02); lbox(wires, wwf, ul - .008, ul + .008, H - .021, H - .0015, .02, dd - (LR.get(fx, .1) if fx != 'tube' else .07))
for wf, u, _, _ in L['panels']:
    if on_run(wf, u): pass
make('Wires', wires, 'Lamps', [WIRE], origin=(0, 0, H))
if THEME == 'Decay':
    x, y = (su, .15) if swf[0] == 'y' else (.15, su); p = Vector(F(swf)(su, 2.3, .03)); bm = bmesh.new()
    lbox(bm, swf, su - .15, su + .15, 2.25, 2.35, 0, .06, 0); lbox(bm, swf, su - .13, su + .13, 2.27, 2.33, .06, .065, 1)
    make('Lamp_Emergency', bm, 'Lamps', [METAL, glow('M_Lamp_Red', (1, .1, .05), 4.0)], origin=F(swf)(su, 2.25, 0)); occupy(swf, su - .15, su + .15, 2.25, 2.35, 'Emergency')
    LIGHTS.append(('Light_Emergency', tuple(p), 8, (1, .12, .06)))
if TH_['pipes']:
    bm = bmesh.new(); wf, u0, u1 = max(L['runs'], key=lambda r: r[2] - r[1]); f = F(wf)
    for z, r in ((2.42, .03), (2.5, .022)): cyl(bm, f(u0, z, .07), f(u1, z, .07), r, 8, 0)
    k = u0 + .4
    while k < u1:
        q = F(wf)(k, 0, .05)
        if not any(x0 - .05 < q[0] < x1 + .05 and y0 - .05 < q[1] < y1 + .05 for x0, y0, x1, y1 in L['beams']): lbox(bm, wf, k - .02, k + .02, 2.38, 2.54, 0, .1, 1)
        k += 1.6
    vu = (u0 + u1) / 2; cyl(bm, f(vu, 2.42, .07), f(vu, 2.42, .16), .012, 6, 1); cyl(bm, f(vu, 2.42, .16), f(vu, 2.42, .17), .06, 8, 2)
    make('Pipes', bm, 'Lamps', [tm('T_Radiator'), METAL, flat('M_Valve_Red', (.4, .05, .04), .6)])

# ---------------------------------------------------------------- props
FLOOR_OCC = []
def floor_free(x, y, r): return all(math.hypot(x - a, y - b) > r + c for a, b, c in FLOOR_OCC)
def chair(n, x, y, r, tex='T_A_VeneerLight'):
    bm = bmesh.new()
    for sx in (-1, 1):
        for sy in (-1, 1): wbox(bm, (sx * .19 - .017, sy * .18 - .017, 0), (sx * .19 + .017, sy * .18 + .017, .44))
    wbox(bm, (-.215, -.205, .44), (.215, .205, .47))
    for sx in (-1, 1): wbox(bm, (sx * .19 - .017, -.2, .47), (sx * .19 + .017, -.166, .95))
    for z in (.62, .78): wbox(bm, (-.172, -.2, z), (.172, -.17, z + .1))
    for sy in (-1, 1): wbox(bm, (-.172, sy * .18 - .01, .12), (.172, sy * .18 + .01, .14))
    make(n, bm, 'Props', [tm(tex)], loc=(x, y, 0), rot=(0, 0, math.radians(r))); FLOOR_OCC.append((x, y, .35))
def wall_prop(n, wf, u, kind):
    f = F(wf); bm = bmesh.new()
    if kind == 'wardrobe':
        lbox(bm, wf, u - .5, u + .5, .06, 1.9, 0, .5); lbox(bm, wf, u - .52, u + .52, 1.9, 1.95, 0, .53)
        for a in (u - .49, u + .45):
            for w in (.01, .45): lbox(bm, wf, a, a + .04, 0, .06, w, w + .04)
        for a, b in ((u - .48, u - .005), (u + .005, u + .48)): lbox(bm, wf, a, b, .1, 1.86, .5, .512)
        for a in (u - .03, u + .015): lbox(bm, wf, a, a + .015, .95, 1.1, .512, .53, 1)
        make(n, bm, 'Props', [tm('T_A_VeneerDark'), BRASS], origin=f(u, 0, .25)); occupy(wf, u - .52, u + .52, 0, 1.95, n)
    elif kind == 'stroller':
        lbox(bm, wf, u - .4, u + .4, .35, .75, .12, .58, 0); prism(bm, wf, [(u - .399, .75), (u - .1, .75), (u - .15, .95), (u - .35, .98)], .121, .579, 0)
        for du in (-.32, .32):
            for w in (.1, .6): cyl(bm, f(u + du, .15, w - .02), f(u + du, .15, w + .02), .15, 10, 1)
        cyl(bm, f(u + .4, .7, .14), f(u + .62, 1.0, .14), .012, 6, 2); cyl(bm, f(u + .4, .7, .56), f(u + .62, 1.0, .56), .012, 6, 2); cyl(bm, f(u + .62, 1.0, .12), f(u + .62, 1.0, .58), .018, 6, 2)
        for du in (-.32, .32): cyl(bm, f(u + du, .15, .1), f(u + du, .15, .6), .01, 6, 2)
        make(n, bm, 'Props', [tm('T_A_Sofa'), BLACK, STEEL], origin=f(u, 0, .35)); occupy(wf, u - .42, u + .65, 0, 1.0, n)
    elif kind == 'bench':
        lbox(bm, wf, u - .7, u + .7, .42, .46, .05, .4, 0)
        for du in (-.6, .6): lbox(bm, wf, u + du - .03, u + du + .03, 0, .42, .07, .38, 1)
        lbox(bm, wf, u - .7, u + .7, .6, .78, .0, .03, 0)
        make(n, bm, 'Props', [tm('T_A_VeneerLight'), METAL], origin=f(u, 0, .2)); occupy(wf, u - .7, u + .7, 0, .8, n)
    elif kind == 'boxes2':
        lbox(bm, wf, u - .45, u + .05, 0, .38, .02, .44, 0); lbox(bm, wf, u + .07, u + .45, 0, .3, .02, .4, 0); lbox(bm, wf, u - .38, u - .02, .38, .64, .06, .36, 0)
        make(n, bm, 'Props', [tm('T_Cardboard')], origin=f(u, 0, .2)); occupy(wf, u - .45, u + .45, 0, .64, n)
    elif kind == 'mattress':
        A_ = math.radians(78); w0 = 1.9 * math.cos(A_) + .002
        hexa(bm, lambda a, t, nn: f(u + a, t * math.sin(A_) + nn * math.cos(A_), w0 - t * math.cos(A_) + nn * math.sin(A_)), (-.45, .45), (0, 1.9), (0, .16), 0)
        make(n, bm, 'Props', [tm('T_A_Sheet')], origin=f(u, 0, w0)); occupy(wf, u - .45, u + .45, 0, 1.9, n)
    elif kind == 'boards':
        for k in range(4):
            A_ = math.radians(80 - k * 2); du = -.3 + k * .18; w0 = 2.0 * math.cos(A_) + .002 + k * .001
            hexa(bm, lambda a, t, nn, du=du, A_=A_, w0=w0: f(u + du + a, t * math.sin(A_) + nn * math.cos(A_), w0 - t * math.cos(A_) + nn * math.sin(A_)), (0, .14), (0, 2.0), (0, .025), 0)
        make(n, bm, 'Props', [tm('T_Planks')], origin=f(u, 0, .2)); occupy(wf, u - .32, u + .32, 0, 2.0, n)
    elif kind in ('painting', 'mirror', 'board'):
        w_, h_ = {'painting': (.5, .5), 'mirror': (.5, .8), 'board': (.9, .6)}[kind]; z0 = 1.35
        lbox(bm, wf, u - w_ / 2, u + w_ / 2, z0, z0 + h_, 0, .02, 1); fs = lbox(bm, wf, u - w_ / 2 + .03, u + w_ / 2 - .03, z0 + .03, z0 + h_ - .03, .02, .024, 0)
        set_uv(bm, fs, wf, u - w_ / 2 + .03, u + w_ / 2 - .03, z0 + .03, z0 + h_ - .03)
        tex = {'painting': xm('T_A_Painting'), 'mirror': flat('M_Mirror', (.55, .58, .6), .05), 'board': xm('T_Prop_Notices')}[kind]
        make(n, bm, 'Props', [tex, tm('T_A_VeneerDark')], origin=f(u, z0, 0)); occupy(wf, u - w_ / 2, u + w_ / 2, z0, z0 + h_, n)
    return True
def floor_prop(n, x, y, kind, r=0):
    bm = bmesh.new()
    if kind == 'plant':
        cyl(bm, (x, y, 0), (x, y, .3), .13, 8, 0, r1=.16); cyl(bm, (x, y, .28), (x, y, .9), .012, 5, 1)
        make(n + '_Pot', bm, 'Props', [flat('M_Clay_Pot', (.42, .18, .09)), flat('M_Plant_Stem', (.2, .16, .08))]); bm = bmesh.new()
        for k in range(5):
            ang = k * 1.3 + r; zc = .5 + k * .1; p = Vector((x, y, zc)); d_ = Vector((math.cos(ang), math.sin(ang), 1.2)).normalized(); s_ = d_.cross(Vector((0, 0, 1))).normalized()
            uvquad(bm, [tuple(p - s_ * .2), tuple(p + s_ * .2), tuple(p + s_ * .2 + d_ * .42), tuple(p - s_ * .2 + d_ * .42)], 0)
        make(n + '_Leaves', bm, 'Props', [dm('T_IP_Leaves')], recalc=False); FLOOR_OCC.append((x, y, .3))
    elif kind == 'armchair':
        wbox(bm, (-.42, -.4, .08), (.42, .4, .42), 0); wbox(bm, (-.42, -.4, .4205), (.42, -.22, .95), 0)
        for sx in (-1, 1): wbox(bm, (sx * .4195 - (.13 if sx > 0 else 0), -.2195, .4205), (sx * .4195 + (.13 if sx < 0 else 0), .3995, .62), 0)
        for sx in (-1, 1):
            for sy in (-1, 1): wbox(bm, (sx * .36 - .025, sy * .34 - .025, 0), (sx * .36 + .025, sy * .34 + .025, .08), 1)
        make(n, bm, 'Props', [tm('T_A_Armchair'), tm('T_A_VeneerDark')], loc=(x, y, 0), rot=(0, 0, math.radians(r))); FLOOR_OCC.append((x, y, .6))
    elif kind == 'bucket2':
        cyl(bm, (x, y, 0), (x, y, .3), .13, 10, 0, r1=.16); make(n, bm, 'Props', [tm('T_Bucket')]); FLOOR_OCC.append((x, y, .2))
for p in L['props']:
    k = p[0]
    if k in ('chair', 'stool'): chair(k.capitalize(), p[1], p[2], p[3])
    elif k in ('wardrobe', 'sled', 'boxes'):
        kind = {'sled': 'boards', 'boxes': 'boxes2'}.get(k, k); w_ = {'wardrobe': 1.04, 'boards': .64, 'boxes2': .9}[kind]
        for du in [0] + [s_ * .15 * i for i in range(1, 12) for s_ in (1, -1)]:
            if is_free(p[1], p[2] + du - w_ / 2, p[2] + du + w_ / 2, 0, 2.0): wall_prop(k.capitalize(), p[1], p[2] + du, kind); break
    elif k == 'runner':
        x0, y0, x1, y1 = p[1]; bm = bmesh.new(); L_ = max(x1 - x0, y1 - y0)
        f_ = floor_decal(bm, (x0 + x1) / 2, (y0 + y1) / 2, .006, x1 - x0, y1 - y0, 0, 0, (0, 0, (x1 - x0) / .9 if x1 - x0 > y1 - y0 else 1, (y1 - y0) / .9 if y1 - y0 >= x1 - x0 else 1))
        make('Carpet_Runner', bm, 'Props', [xm('T_A_Rug')], recalc=False); IGN.append('Carpet_Runner')
    elif k == 'rolled':
        bm = bmesh.new(); cyl(bm, (p[1], p[2], 0), (p[1], p[2], 1.5), .12, 8); make('Carpet_Rolled', bm, 'Props', [tm('T_A_Carpet')], origin=(p[1], p[2], 0)); FLOOR_OCC.append((p[1], p[2], .15))
    elif k == 'boots':
        bm = bmesh.new()
        for bx in (-.105, .105): wbox(bm, (bx - .05, -.13, 0), (bx + .05, .14, .1)); wbox(bm, (bx - .045, .025, .1), (bx + .045, .135, .38))
        zb = .012 if any(math.hypot(p[1] - m[0], p[2] - m[1]) < .6 for m in MATS_POS) else 0
        make('Boots', bm, 'Props', [tm('T_Boots')], loc=(p[1], p[2], zb), rot=(0, 0, math.radians(p[3]))); FLOOR_OCC.append((p[1], p[2], .25))
    elif k == 'bucket': floor_prop('Bucket', p[1], p[2], 'bucket2')
    elif k == 'bags':
        for i, (x, y, r) in enumerate(p[1]):
            bm = bmesh.new(); sphere(bm, (0, 0, r * .75), r, .75, 0, 8, 6); cyl(bm, (0, 0, r * 1.45), (0, 0, r * 1.62), .04, 6, 0, r1=.01)
            make('GarbageBag_%02d' % (i + 1), bm, 'Props', [tm('T_Plastic_Bag')], loc=(x, y, 0)); FLOOR_OCC.append((x, y, r))
    elif k == 'envelopes':
        bm = bmesh.new()
        for i, (x, y, r) in enumerate(p[1]): floor_decal(bm, x, y, .016 + i * .001, .16, .08, r, 0)
        make('Envelopes', bm, 'Props', [xm('T_A_Envelope')], recalc=False); IGN.append('Envelopes')
# theme extras on free wall spots
def free_spot(width, zones=('corr', 'hall'), depth=.6):
    cands = []
    for wf, a, b in SEGS:
        u = a + .4 + width / 2
        while u < b - .4 - width / 2:
            p = F(wf)(u, 0, depth / 2)
            if zone_at(p[0], p[1]) in zones and is_free(wf, u - width / 2 - .15, u + width / 2 + .15, 0, 1.2) and floor_free(p[0], p[1], depth):
                cands.append((wf, u, p))
            u += .3
    return R.choice(cands) if cands else None
for i, ex in enumerate(TH_['extras']):
    if ex in ('plant', 'armchair', 'bucket2'):
        s = free_spot(.6, depth=.7)
        if s: wf, u, p = s; q = F(wf)(u, 0, .45); floor_prop('%s_%d' % (ex.capitalize(), i), q[0], q[1], ex, R.uniform(0, 6)); occupy(wf, u - .3, u + .3, 0, 1.0, ex)
    else:
        w_ = {'stroller': 1.1, 'bench': 1.4, 'boxes2': .9, 'mattress': .9, 'boards': .7, 'painting': .5, 'mirror': .5, 'board': .9}[ex]
        s = free_spot(w_)
        if s:
            wf, u, p = s
            if ex in ('painting', 'mirror', 'board') and not is_free(wf, u - w_ / 2, u + w_ / 2, 1.3, 2.2): continue
            wall_prop('%s_%d' % (ex.capitalize(), i), wf, u, ex); FLOOR_OCC.append((p[0], p[1], w_ / 2))

# ---------------------------------------------------------------- decals
FD = bmesh.new(); CD = bmesh.new(); WD = bmesh.new(); LAY = defaultdict(list)
DMATS = ['T_ID_EdgeGrime', 'T_ID_PathWear', 'T_ID_WaterStain', 'T_ID_MissingTiles', 'T_ID_Debris', 'T_ID_Flyers', 'T_ID_Footprints', 'T_Decal_Puddle_1', 'T_ID_Mold', 'T_ID_Soot',
         'T_ID_CornerShadow', 'T_ID_Scuffs', 'T_ID_Scribbles', 'T_ID_Crack', 'T_Decal_Cracks']
DI = {n: i for i, n in enumerate(DMATS)}
def fput(layer, z, x, y, sx, sy, rot, tex, uvr=(0, 0, 1, 1), bm=None, down=False):
    r = math.hypot(sx, sy) / 2
    if any(math.hypot(x - a, y - b) < r + c for a, b, c in LAY[layer]): return False
    LAY[layer].append((x, y, r)); floor_decal(bm or FD, x, y, z, sx, sy, rot, DI[tex], uvr, down); return True
def inside_floor(x, y, m=.2): return any(r[0] + m < x < r[2] - m and r[1] + m < y < r[3] - m for _, r, _ in L['floors'])
for k, (wf, a, b) in enumerate(SEGS):                          # skirting grime + ceiling corner shadow
    f = F(wf); horiz = wf[0] == 'y'; z = .0015 if horiz else .0025
    for bm_, zz, tex, d in ((FD, z, 'T_ID_EdgeGrime', .32), (CD, H - z, 'T_ID_CornerShadow', .3)):
        p0, p1, p2, p3 = f(a, 0, 0), f(b, 0, 0), f(b, 0, d), f(a, 0, d)
        pts = [(p[0], p[1], zz) for p in (p0, p1, p2, p3)]; fc = quad(bm_, pts, DI[tex]); fc.normal_update()
        if (fc.normal.z < 0) != (bm_ is CD): fc.normal_flip(); pts = [pts[0], pts[3], pts[2], pts[1]]
        uvl = bm_.loops.layers.uv.get('UVMap') or bm_.loops.layers.uv.new('UVMap')
        for l in fc.loops:
            co = l.vert.co; s_ = (Vector(co) - Vector((p0[0], p0[1], zz))).dot(Vector(f(1, 0, 0)) - Vector(f(0, 0, 0))); t_ = (Vector(co) - Vector((p0[0], p0[1], zz))).dot(nrm(wf))
            l[uvl].uv = (s_ / 2.0, t_ / d)
for name, (x0, y0, x1, y1), z in L['floors']:                 # worn traffic path down the middle
    if z not in ('corr', 'hall') or THEME == 'Panel80': continue
    along_x = (x1 - x0) >= (y1 - y0); L_ = (x1 - x0) if along_x else (y1 - y0); n = max(1, int(L_ / 3.5)); seg = L_ / n
    for i in range(n):
        cx = x0 + (i + .5) * seg if along_x else (x0 + x1) / 2; cy = (y0 + y1) / 2 if along_x else y0 + (i + .5) * seg
        fl = R.choice((1, -1)); fput('path%d' % (i % 2), .004 + (i % 2) * .001, cx, cy, seg + .2 if along_x else 1.1, 1.1 if along_x else seg + .2, 0, 'T_ID_PathWear',
                                     (0, 0, 1, fl) if not along_x else (0, 0, fl, 1))
tiled = THEME in ('Ochre',)
for k in range(60):
    x, y = R.uniform(X0, X1), R.uniform(Y0, Y1)
    if not inside_floor(x, y, .5): continue
    roll = R.random()
    if tiled and roll < .25: fput('tiles', .006, x, y, R.uniform(.7, 1.2), R.uniform(.7, 1.2), R.choice((0, 90)), 'T_ID_MissingTiles')
    elif THEME == 'Decay' and roll < .45: fput('debris', .008, x, y, R.uniform(.8, 1.6), R.uniform(.8, 1.6), R.uniform(0, 360), 'T_ID_Debris')
    elif roll < .55 and THEME in ('Mint', 'Decay', 'Ochre'): fput('cracks', .007, x, y, R.uniform(1.2, 2.2), R.uniform(1.2, 2.2), R.uniform(0, 360), 'T_Decal_Cracks')
x, y = (F(mwf)(mu, 0, .6)[0], F(mwf)(mu, 0, .6)[1]); fput('flyers', .009, x, y, 1.0, 1.0, R.uniform(0, 90), 'T_ID_Flyers')
for k in range(3 if THEME == 'Decay' else 1):
    for t_ in range(40):
        x, y = R.uniform(X0, X1), R.uniform(Y0, Y1)
        if inside_floor(x, y, .6) and floor_free(x, y, .8) and fput('puddle', .010, x, y, R.uniform(1.0, 1.6), R.uniform(.7, 1.0), R.uniform(0, 180), 'T_Decal_Puddle_1'):
            fput('stain', H - .006, x, y, 1.4, 1.4, R.uniform(0, 360), 'T_ID_WaterStain', bm=CD, down=True)
            if THEME == 'Decay': floor_prop('Bucket_Leak_%d' % k, x + .2, y, 'bucket2')
            break
for (x0, y0, x1, y1) in L['ceil_stains']: fput('stain', H - .006, (x0 + x1) / 2, (y0 + y1) / 2, min(1.8, x1 - x0), min(1.8, y1 - y0), R.uniform(0, 360), 'T_ID_WaterStain', bm=CD, down=True)
for k in range(5 if THEME != 'Decay' else 12):
    x, y = R.uniform(X0, X1), R.uniform(Y0, Y1)
    if inside_floor(x, y, .6): fput('stain', H - .006, x, y, R.uniform(.9, 1.6), R.uniform(.9, 1.6), R.uniform(0, 360), 'T_ID_WaterStain', bm=CD, down=True)
for x, y, r in ceil_items:
    if TH_['lamp'] in ('cage', 'globe') or THEME == 'Decay': fput('soot', H - .004, x, y, r * 2.4, r * 2.4, 0, 'T_ID_Soot', bm=CD, down=True)
for k in range(8):
    x, y = R.uniform(X0, X1), R.uniform(Y0, Y1)
    if inside_floor(x, y, .5): fput('ccrack', H - .008, x, y, R.uniform(1.0, 2.0), R.uniform(1.0, 2.0), R.uniform(0, 360), 'T_ID_Crack', bm=CD, down=True)
wrong = [d for d in L['doors'] if d[3] == 'wrong']                # muddy prints that lead from the lift to the door that should not be there
if wrong:
    num, wf, u, t, _ = wrong[0]; dst = Vector(F(wf)(u, 0, .45)); src_ = Vector(F(lwf)(ua, 0, 1.0)); pts = [src_]
    cor = [r for _, r, z in L['floors'] if r[0] - .01 <= dst.x <= r[2] + .01 and r[1] - .01 <= dst.y <= r[3] + .01][0]
    if wf[0] == 'y': mid = Vector((src_.x, (cor[1] + cor[3]) / 2, 0)); pts += [mid, Vector((dst.x, mid.y, 0)), dst]
    else: mid = Vector(((cor[0] + cor[2]) / 2, src_.y, 0)); pts += [mid, Vector((mid.x, dst.y, 0)), dst]
    k = 0
    for a, b in zip(pts, pts[1:]):
        d_ = b - a; d_.z = 0; Ln = d_.length
        if Ln < .1: continue
        ang = math.degrees(math.atan2(d_.y, d_.x)) - 90; n = int(Ln / .95)
        for i in range(n):
            c = a + d_ * ((i + .5) / n); floor_decal(FD, c.x, c.y, .012 + (k % 2) * .001, .5, .95, ang, DI['T_ID_Footprints']); k += 1
wl = defaultdict(list)                                          # wall decals: scuffs, scribbles, stains, cracks, mould
def wput(layer, wf, u0, u1, z0, z1, w, tex, cell=(0, 0, 1, 1)):
    if not is_free(wf, u0 - .05, u1 + .05, z0, z1): return False
    if any(u0 < b and a < u1 and z0 < d and c < z1 for a, b, c, d in wl[(layer, wf)]): return False
    wl[(layer, wf)].append((u0, u1, z0, z1)); wall_decal(WD, wf, u0, u1, z0, z1, w, DI[tex], cell); return True
for wf, a, b in SEGS:
    L_ = b - a; p = F(wf)((a + b) / 2, 1, .3); zn = zone_at(p[0], p[1])
    for k in range(int(L_ / 2.5) + 1):
        u = R.uniform(a + .3, b - .3); w_ = R.uniform(.8, 1.6)
        if u - w_ / 2 > a and u + w_ / 2 < b: wput('scuff', wf, u - w_ / 2, u + w_ / 2, .12, .52, .002, 'T_ID_Scuffs', (0, 0, R.choice((1, -1)), 1))
    if zn == 'hall' or R.random() < .25:
        u = R.uniform(a + .5, b - .5); wput('scrib', wf, u - .35, u + .35, .95, 1.65, .004, 'T_ID_Scribbles')
    if R.random() < .5:
        u = R.uniform(a + .6, b - .6); wput('stain', wf, u - .5, u + .5, 1.75, 2.55, .006, 'T_ID_WaterStain', (0, .5, 1, 1))
    if R.random() < .35:
        u = R.uniform(a + .5, b - .5); wput('crack', wf, u - .6, u + .6, 1.6, 2.4, .008, 'T_ID_Crack')
    if THEME == 'Decay' or zn == 'tamb_bare':
        for u in (a + .45, b - .45):
            if R.random() < .6: wput('mold', wf, u - .45, u + .45, 0, .9, .01, 'T_ID_Mold', (0, 0, 1, .7))
burnt = [d for d in L['doors'] if TH_['cells'].get(d[3]) is not None and TH_['cells'][d[3]] in ([7] if THEME == 'Ochre' else [3] if THEME == 'Decay' else [])]
for num, wf, u, t, _ in burnt: wall_decal(WD, wf, u - .7, u + .7, 2.15, 2.58, .004, DI['T_ID_Soot'], (0, .5, 1, 1))
DM_ = [dm(t) for t in DMATS]
make('Decal_Floor', FD, 'Decals', DM_, recalc=False); make('Decal_Ceiling', CD, 'Decals', DM_, recalc=False); make('Decal_Walls', WD, 'Decals', DM_, recalc=False)

if TH_.get('wainscot'):                                   # skirting + cap rail (1.0 m) in the 80s theme, broken around everything on the wall
    bm = bmesh.new()
    for wf, a, b in SEGS:
        mid = F(wf)((a + b) / 2, 1, .2)
        if zone_at(mid[0], mid[1]) == 'tamb_wood': continue
        for z0, z1, d in ((0, .08, .018), (.98, 1.02, .025)):
            ins = .027 if wf[0] == 'x' else .001
            for x0, x1 in free_spans(wf, a + ins, b - ins, z0, z1, pad=.003): lbox(bm, wf, x0, x1, z0 + (.0005 if z0 == 0 else 0), z1, 0, d)
    make('Wainscot_Trim', bm, 'Shell', [tm('T_A_VeneerDark')])

# ---------------------------------------------------------------- lights, markers, save
for n, loc, e, c in LIGHTS: light(n, loc, e, c)
sx, sy, sr = L['spawn']; marker('Spawn_Player', (sx, sy, 0), sr); marker('Exit_LiftA', F(lwf)(ua, 0, .5))
IGN += [o.name for o in ST['root'].all_objects if o.name.startswith('Door_') and not o.name.endswith(('_Frame', '_Bell', '_Mat'))]   # leaves hang on hinges
finish(anchors=['Ceiling', 'Walls', 'Ceiling_Beams', 'LiftB_Shaft', 'Pipes'], ignore=IGN)
