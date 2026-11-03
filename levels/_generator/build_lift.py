"""Lift cab interior: Soviet passenger lift, wood-grain laminate walls, 1.0 m two-speed telescopic doors.
usage: python3 build_lift.py <Normal|Trader> <out.blend>
Normal: 1.5 x 1.3 x 2.25 m inside (outer 1.6 x 1.4, the size of LiftA_Cab in the v2 floor shafts).
Trader: the same cab grown to 2.2 x 2.6 m, with a dark booth behind the back wall (Spawn_Trader).
  LiftCab_BackWall is one closed mesh with two shape keys (identical topology, Unity blend shapes):
    Crack - the middle panel swells and an H-shaped seam opens around it (booth light leaks through)
    Open  - the two halves roll back into soft lips above and below: a service window onto the booth
  Unity: animate Crack 0->100, then crossfade Crack 100->0 with Open 0->100 (action BackWall_Open shows it).
Local frame: x across the doors, +y into the cab, front outer face of the cab at y = 0, floor at z = 0."""
import sys, os, math
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from kit import *
import lift_spec as LS
VAR, OUT = sys.argv[-2], os.path.abspath(sys.argv[-1]); TR = VAR == 'Trader'
W, D = (2.2, 2.6) if TR else (1.5, 1.3)
HC, TW, DW, DH = 2.25, .05, .5, 2.05                 # inside height, wall thickness, half door width, door height
X1, Y0, Y1 = W / 2, TW, TW + D                        # inside: x in [-X1, X1], y in [Y0, Y1]
KH, KD, CH, CD = .1, .005, .03, .008                  # kick plate / cornice height and depth
start(OUT, os.path.splitext(os.path.basename(OUT))[0])

# ---------------------------------------------------------------- materials
WALL = [tm('T_LC_Wall_A', (1.28, 2.56)), tm('T_LC_Wall_B', (1.28, 2.56))]
FLOOR, CEIL, DOOR = tm('T_LC_Floor', (1.28, 1.28)), tm('T_LC_Ceiling', (.64, .64)), tm('T_LC_DoorMetal', (.64, 2.56))
OUTER = flat('M_LC_SteelOuter', (.07, .07, .068), .6); ALU = flat('M_LC_Alu', (.40, .40, .38), .35)
KICK = flat('M_LC_KickPlate', (.13, .125, .12), .45); CORE = flat('M_LC_Chipboard', (.16, .11, .07), .9)
PANEL, RULES, VENT, DEC = xm('T_LC_Panel_' + ('B' if TR else 'A')), xm('T_LC_Rules'), xm('T_LC_Vent'), dm('T_LC_Decals')
BTN = flat('M_LC_Button', (.025, .025, .024), .35); BURNT = flat('M_LC_ButtonBurnt', (.035, .022, .014), .9)
STOP = flat('M_LC_ButtonStop', (.42, .03, .02), .45); CALL = flat('M_LC_ButtonCall', (.5, .38, .07), .45)
GRIME, CSHAD = dm('T_ID_EdgeGrime'), dm('T_ID_CornerShadow')
def plafond_mat(lit):
    name = 'M_LC_Plafond' + ('' if lit else '_Dead')
    if name in ST['mats']: return ST['mats'][name]
    m = bpy.data.materials.new(name); nt = m.node_tree; b = nt.nodes.get('Principled BSDF'); b.inputs['Roughness'].default_value = .3
    im = bpy.data.images.get('T_LC_Plafond.png') or bpy.data.images.load(TEXD + 'T_LC_Plafond.png'); im.filepath = bpy.path.relpath(im.filepath)
    n = nt.nodes.new('ShaderNodeTexImage'); n.image = im; n.interpolation = 'Closest'
    if lit:
        nt.links.new(n.outputs['Color'], b.inputs['Base Color']); nt.links.new(n.outputs['Color'], b.inputs['Emission Color'])
        b.inputs['Emission Strength'].default_value = 2.5
    else:                                                  # dead lamp: the same shade, dark
        hs = nt.nodes.new('ShaderNodeHueSaturation'); hs.inputs['Value'].default_value = .3
        nt.links.new(n.outputs['Color'], hs.inputs['Color']); nt.links.new(hs.outputs['Color'], b.inputs['Base Color'])
    ST['mats'][name] = m; ST['MS'][name] = None; return m
def xy_uv(bm, mi, x0, x1, y0, y1):
    """explicit UV by top view for faces of material mi (ceiling plates seen from below)"""
    uvl = bm.loops.layers.uv.get('UVMap') or bm.loops.layers.uv.new('UVMap')
    for fc in bm.faces:
        if fc.material_index != mi: continue
        for lp in fc.loops: lp[uvl].uv = ((lp.vert.co.x - x0) / (x1 - x0), (lp.vert.co.y - y0) / (y1 - y0))
XYZ = lambda p, q, a: (p, q, a)
FRONT, BACK, LEFT, RIGHT = ('y', Y0, 1), ('y', Y1, -1), ('x', X1, -1), ('x', -X1, 1)   # LEFT/RIGHT as seen facing the doors

# ---------------------------------------------------------------- shell: steel box, laminate inside
bm = bmesh.new(); wbox(bm, (-X1 - TW, 0, -.05), (X1 + TW, Y1 + TW, HC + .05)); shell = make('LiftCab_Shell', bm, 'Cab', WALL + [FLOOR, CEIL, OUTER, ALU])
cs = []
for lo, hi in [((-X1, Y0, 0), (X1, Y1, HC)), ((-DW, -.2, 0), (DW, Y0 + .02, DH))] + ([((-X1, Y1 - .02, 0), (X1, Y1 + TW + .2, HC))] if TR else []):
    c = bmesh.new(); wbox(c, lo, hi); cs.append(c)
boolean_cut(shell, cs)
bm = bmesh.new(); bm.from_mesh(shell.data); e = 1e-3
for fc in bm.faces:
    c, n = fc.calc_center_median(), fc.normal
    inner = -X1 - e < c.x < X1 + e and Y0 - e < c.y < Y1 + (TW / 2 if TR else 0) + e and -e < c.z < HC + e
    if abs(n.y) < .5 and abs(c.x) < DW + e and -e < c.y < Y0 + e and c.z < DH + e: fc.material_index = 5   # door reveal + threshold
    elif not inner: fc.material_index = 4
    elif n.z > .9: fc.material_index = 2
    elif n.z < -.9: fc.material_index = 3
    else: fc.material_index = 1 if (n.y < -.9 and abs(c.y - Y1) < e) else 0
bmesh.ops.triangulate(bm, faces=[fc for fc in bm.faces if len(fc.verts) > 4], ngon_method='EAR_CLIP')   # ring ngons: keep check points on the frame
bm.to_mesh(shell.data); bm.free()

# ---------------------------------------------------------------- trims: kick plates, corner angles, cornice, joint strips, door casing
bm = bmesh.new()
wbox(bm, (-X1, Y1 - KD, 0), (X1, Y1, KH), 1); wbox(bm, (-X1, Y1 - CD, HC - CH), (X1, Y1, HC), 0); wbox(bm, (-X1, Y0, HC - CH), (X1, Y0 + CD, HC), 0)
for s in (-1, 1):
    x0, x1 = sorted((s * X1, s * (X1 - KD))); wbox(bm, (x0, Y0 + KD + .0005, 0), (x1, Y1 - KD - .0005, KH), 1)
    x0, x1 = sorted((s * X1, s * (X1 - CD))); wbox(bm, (x0, Y0 + CD + .0005, HC - CH), (x1, Y1 - CD - .0005, HC), 0)
    u0, u1 = sorted((s * X1, s * (DW + .045))); wbox(bm, (u0, Y0, 0), (u1, Y0 + KD, KH), 1)
for cx, cy, sx, sy in ((-X1, Y1, 1, -1), (X1, Y1, -1, -1), (-X1, Y0, 1, 1), (X1, Y0, -1, 1)):
    L_, t_ = .022, .005
    prism(bm, XYZ, [(cx, cy), (cx + sx * L_, cy), (cx + sx * L_, cy + sy * t_), (cx + sx * t_, cy + sy * t_), (cx + sx * t_, cy + sy * L_), (cx, cy + sy * L_)], KH + .0005, HC - CH - .0005, 0)
STRIPS = [(BACK, x) for x in ((-.47, .47) if TR else (-.25, .25))] + [(wf, Y0 + D * k / (3 if TR else 2)) for wf in (LEFT, RIGHT) for k in ((1, 2) if TR else (1,))]
for wf, u in STRIPS:
    lbox(bm, wf, u - .012, u + .012, KH, HC - CH, 0, .004, 0); occupy(wf, u - .012, u + .012, KH, HC - CH, 'Strip')
u0, u1, a_, h_ = -DW + .005, DW - .005, .04, DH - .005
prism(bm, FRONT, [(u0 - a_, 0), (u0, 0), (u0, h_), (u1, h_), (u1, 0), (u1 + a_, 0), (u1 + a_, h_ + a_), (u0 - a_, h_ + a_)], 0, .004, 0)
occupy(FRONT, u0 - a_, u1 + a_, 0, h_ + a_, 'Casing')
make('LiftCab_Trims', bm, 'Cab', [ALU, KICK])

# ---------------------------------------------------------------- button plate (layout in lift_spec.py), rules plate
pu1 = -(DW + .06); pu0 = pu1 - LS.PANEL_W; pz0 = .92; pz1 = pz0 + LS.PANEL_H
bm = bmesh.new(); fr = lbox(bm, FRONT, pu0, pu1, pz0, pz1, 0, .006, 0); fr.material_index = 1; set_uv(bm, fr, FRONT, pu0, pu1, pz0, pz1)
for k, rn in enumerate(LS.rows(VAR)):
    z = pz1 - (LS.ROW0 + k * LS.PITCH) / LS.PANEL_PX[1] * LS.PANEL_H; x = pu1 - LS.BTN_X / LS.PANEL_PX[0] * LS.PANEL_W
    burnt = rn in LS.BURNT; sc_ = .82 if burnt else 1.0; mi = 3 if burnt else {'stop': 4, 'call': 5}.get(rn, 2)
    lbox(bm, FRONT, x - LS.BTN_W / 2 * sc_, x + LS.BTN_W / 2 * sc_, z - LS.BTN_H / 2 * sc_, z + LS.BTN_H / 2 * sc_, .006, .0095 if burnt else .013, mi)
make('LiftCab_ButtonPanel', bm, 'Cab', [ALU, PANEL, BTN, BURNT, STOP, CALL], origin=((pu0 + pu1) / 2, Y0, pz0)); occupy(FRONT, pu0, pu1, pz0, pz1, 'ButtonPanel')
ru = Y0 + (.5 if TR else .42); rz = 1.25; rw, rh = .1, .4                          # rules plate 0.2 x 0.4 m
bm = bmesh.new(); fr = lbox(bm, LEFT, ru - rw, ru + rw, rz, rz + rh, 0, .003, 0); fr.material_index = 1; set_uv(bm, fr, LEFT, ru - rw, ru + rw, rz, rz + rh)
make('LiftCab_RulesPlate', bm, 'Cab', [ALU, RULES], origin=(X1, ru, rz)); occupy(LEFT, ru - rw, ru + rw, rz, rz + rh, 'Rules')

# ---------------------------------------------------------------- ceiling: plafonds, vent
LIGHTS = []
for name, yc, lit in [('LiftCab_Plafond', .7 if TR else .62, True)] + ([('LiftCab_Plafond_Dead', 1.95, False)] if TR else []):
    hx, hy = .25, .13; bm = bmesh.new()
    wbox(bm, (-hx - .012, yc - hy - .012, HC - .012), (hx + .012, yc + hy + .012, HC), 0); wbox(bm, (-hx, yc - hy, HC - .05), (hx, yc + hy, HC - .012), 1)
    xy_uv(bm, 1, -hx, hx, yc - hy, yc + hy); make(name, bm, 'Cab', [ALU, plafond_mat(lit)], origin=(0, yc, HC))
    if lit: LIGHTS.append(('Light_LiftCab_Flicker' if TR else 'Light_LiftCab', (0, yc, HC - .14), 9, (1, .9, .74)))
vx, vy = (.3, 1.3) if TR else (.25, .92)
bm = bmesh.new(); wbox(bm, (vx - .15, vy - .075, HC - .005), (vx + .15, vy + .075, HC), 0); xy_uv(bm, 0, vx - .15, vx + .15, vy - .075, vy + .075)
make('LiftCab_Vent', bm, 'Cab', [VENT], origin=(vx, vy, HC))

# ---------------------------------------------------------------- decals: fake AO strips, burns, marker tag, scratched heart, sticker
bm = bmesh.new(); uvl = bm.loops.layers.uv.new('UVMap')
for wf, a, b in ((FRONT, -X1, X1), (BACK, -X1, X1), (LEFT, Y0, Y1), (RIGHT, Y0, Y1)):
    f = F(wf); n_ = nrm(wf); ud = Vector(f(1, 0, 0)) - Vector(f(0, 0, 0)); lay = .0015 if wf[0] == 'y' else .0025
    for z, mi, w0, w1, down in ((lay, 1, KD + .001, .26, False), (HC - lay, 2, CD + .001, .26, True)):
        p0 = Vector(f(a, 0, 0)); pts = [(p[0], p[1], z) for p in (f(a, 0, w0), f(b, 0, w0), f(b, 0, w1), f(a, 0, w1))]
        fc = quad(bm, pts, mi); fc.normal_update()
        if (fc.normal.z < 0) != down: fc.normal_flip()
        for lp in fc.loops:
            co = Vector(lp.vert.co); co.z = 0; lp[uvl].uv = ((co - Vector((p0.x, p0.y, 0))).dot(ud) / 2.0, ((co - Vector((p0.x, p0.y, 0))).dot(n_) - w0) / (w1 - w0))
CELL = {'tag': (0, .5, .5, 1), 'heart': (.5, .5, 1, 1), 'burns': (0, 0, .5, .5), 'sticker': (.5, 0, 1, .5)}
bx_, by_ = (.3, 1.4) if TR else (.12, .72); floor_decal(bm, bx_, by_, .0035, .34, .34, 20, 0, CELL['burns'])
for wf, kind, u0, u1, z0, z1 in ((RIGHT, 'tag', *((1.3, 1.65) if TR else (.25, .6)), 1.2, 1.55), (BACK, 'heart', *((.66, .94) if TR else (.36, .64)), 1.32, 1.6),
                                 (FRONT, 'sticker', *((.62, .74) if TR else (.58, .70)), 1.4, 1.52)):
    wall_decal(bm, wf, u0, u1, z0, z1, .002, 0, CELL[kind]); occupy(wf, u0, u1, z0, z1, 'Decal_' + kind)
make('LiftCab_Decals', bm, 'Decals', [DEC, GRIME, CSHAD], recalc=False)

# ---------------------------------------------------------------- doors: two-speed centre-opening, outside the front wall
DOORS = []
for sd, sg in (('L', -1), ('R', 1)):
    for nm, a, b, y0, y1, mv in (('Fast', .0015, .2555, -.052, -.032, .5), ('Slow', .2455, .505, -.026, -.006, .25)):
        x0, x1 = sorted((sg * a, sg * b)); bm = bmesh.new(); wbox(bm, (x0, y0, .005), (x1, y1, DH + .005))
        o = make(f'LiftCab_Door_{sd}_{nm}', bm, 'Doors', [DOOR], origin=((x0 + x1) / 2, (y0 + y1) / 2, .005)); o['slide_x'] = sg * mv; DOORS.append(o.name)
bm = bmesh.new(); wbox(bm, (-X1 - TW, -.06, DH + .01), (X1 + TW, 0, HC + .05), 0); wbox(bm, (-X1 - TW, -.07, -.03), (X1 + TW, 0, 0), 1)
make('LiftCab_DoorTrack', bm, 'Doors', [OUTER, ALU])

# ---------------------------------------------------------------- Trader: morphing back wall + booth
if TR:
    XW, Z0, Z1, G, NL, NC = .45, .95, 1.75, .0005, 10, 12        # window half width, bottom, top, half seam width, rows per lid, columns
    ZC = (Z0 + Z1) / 2; YF, YB = Y1, Y1 + TW; YM = (YF + YB) / 2
    X = [-X1, -XW - G] + [-XW + G + 2 * (XW - G) * k / NC for k in range(NC + 1)] + [XW + G, X1]
    Z = [0, Z0 - .12, Z0 - .05] + [Z0 + (ZC - G - Z0) * k / NL for k in range(NL + 1)] + [ZC + G + (Z1 - ZC - G) * k / NL for k in range(NL + 1)] + [Z1 + .05, Z1 + .12, HC]
    iL, iR, jS, jz0, jz1 = 1, NC + 2, 3 + NL, 3, 4 + 2 * NL
    def cut(i, j): return (i in (iL, iR) and jz0 <= j < jz1) or (j == jS and iL < i < iR)
    bm = bmesh.new(); INFO, VS = [], ({}, {})
    def vert(i, j, side):
        if (i, j) not in VS[side]: VS[side][(i, j)] = bm.verts.new((X[i], (YF, YB)[side], Z[j])); INFO.append((i, j, side))
        return VS[side][(i, j)]
    cells = [(i, j) for i in range(len(X) - 1) for j in range(len(Z) - 1) if not cut(i, j)]; cset = set(cells)
    for i, j in cells:
        bm.faces.new([vert(i, j, 0), vert(i + 1, j, 0), vert(i + 1, j + 1, 0), vert(i, j + 1, 0)]).material_index = 0
        bm.faces.new([vert(i, j + 1, 1), vert(i + 1, j + 1, 1), vert(i + 1, j, 1), vert(i, j, 1)]).material_index = 1
    for i, j in cells:                                               # seam walls and rim along every boundary edge
        for a, b, nb in (((i, j), (i + 1, j), (i, j - 1)), ((i + 1, j), (i + 1, j + 1), (i + 1, j)), ((i + 1, j + 1), (i, j + 1), (i, j + 1)), ((i, j + 1), (i, j), (i - 1, j))):
            if nb not in cset: bm.faces.new([vert(*b, 0), vert(*a, 0), vert(*a, 1), vert(*b, 1)]).material_index = 2
    BW_, BF_, BC_ = wm('T_IW_Ochre_A'), tm('T_AF_Concrete', (2.4, 2.4)), tm('T_IC_Ochre', (2.0, 2.0))
    bw = make('LiftCab_BackWall', bm, 'Cab', [WALL[1], BW_, CORE], origin=(0, YF, 0))

    def morph(i, j, side):
        """(Crack, Open) positions of one vertex"""
        x, z = X[i], Z[j]; y = (YF, YB)[side]; out = -1 if side == 0 else 1          # out: away from the wall core
        if not 2 <= i <= NC + 2: return (x, y, z), (x, y, z)
        s = max(0.0, 1 - (x / XW) ** 2); P = .012 * s                                # swelling, strongest in the middle
        if z > Z1 + 1e-6 or z < Z0 - 1e-6:                                           # rows around the window puff a little
            k = {.05: .45}.get(round(min(abs(z - Z1), abs(z - Z0)), 2), 0.0)
            return (x, y, z), (x, y + out * P * k, z)
        top = z > ZC
        if top: t = (Z1 - z) / (Z1 - ZC - G); zh, L, bf, bb, dz = Z1, .085 * (.85 + .15 * s), .03 + .015 * s, .016, -1
        else:   t = (z - Z0) / (ZC - G - Z0); zh, L, bf, bb, dz = Z0, .065 * (.85 + .15 * s), .05 + .03 * s, .014, 1
        nx = min(1.0, t * 4)
        bulge = .016 * s * math.sin(math.pi * (z - Z0) / (Z1 - Z0))
        crack = (x * (1 - .009 * nx), y - bulge, z - dz * .006 * t)
        y0 = y + out * P; ps = math.pi * t; h = (1 - math.cos(ps)) / 2                  # lip profile: out, round, back to the core
        yo = y0 + out * (bf if side == 0 else bb) * math.sin(ps) + (YM + out * .002 - y0) * h
        return crack, (x * (1 - .012 * nx), yo, zh + dz * L * h)
    bw.shape_key_add(name='Basis', from_mix=False); kc = bw.shape_key_add(name='Crack', from_mix=False); ko = bw.shape_key_add(name='Open', from_mix=False)
    org = Vector((0, YF, 0))
    for idx, (i, j, side) in enumerate(INFO):
        c_, o_ = morph(i, j, side); kc.data[idx].co = Vector(c_) - org; ko.data[idx].co = Vector(o_) - org
    kb = bw.data.shape_keys.key_blocks
    for nm_, keys in (('Crack', ((1, 0), (72, 1), (96, 1), (144, 0))), ('Open', ((1, 0), (96, 0), (144, 1)))):
        for fr_, v in keys: kb[nm_].value = v; kb[nm_].keyframe_insert('value', frame=fr_)
    bw.data.shape_keys.animation_data.action.name = 'BackWall_Open'
    sc = bpy.context.scene; sc.frame_start, sc.frame_end = 1, 150; sc.render.fps = 24; sc.frame_set(1)
    for x_ in (-XW, XW): occupy(BACK, x_ - .001, x_ + .001, Z0, Z1, 'Window')

    BY0, BY1, BX = YB, YB + 1.3, .9                                                   # booth behind the window
    bm = bmesh.new(); wbox(bm, (-BX - .1, BY0, -.05), (BX + .1, BY1 + .1, HC + .05)); booth = make('Booth_Shell', bm, 'Booth', [BW_, BF_, BC_, OUTER])
    c = bmesh.new(); wbox(c, (-BX, BY0 - .1, 0), (BX, BY1, HC)); boolean_cut(booth, [c])
    bm = bmesh.new(); bm.from_mesh(booth.data)
    for fc in bm.faces:
        c, n = fc.calc_center_median(), fc.normal; inner = abs(c.x) < BX + e and BY0 - e < c.y < BY1 + e and -e < c.z < HC + e
        fc.material_index = 3 if not inner else (1 if n.z > .9 else (2 if n.z < -.9 else 0))
    bm.to_mesh(booth.data); bm.free()
    bm = bmesh.new(); wbox(bm, (-.62, BY0 + .01, .88), (.62, BY0 + .43, .92)); wbox(bm, (-.58, BY0 + .03, 0), (.58, BY0 + .39, .88))
    make('Booth_Counter', bm, 'Booth', [tm('T_A_VeneerDark')])
    lx, ly = .32, BY0 + .45; bm = bmesh.new()
    cyl(bm, (lx, ly, HC), (lx, ly, 1.68), .004, 6, 0); cyl(bm, (lx, ly, 1.68), (lx, ly, 1.63), .018, 8, 1); sphere(bm, (lx, ly, 1.60), .032, mi=2)
    make('Booth_Bulb', bm, 'Booth', [flat('M_Wire', (.05, .05, .05)), flat('M_Metal_Dark', (.10, .09, .08), .5), glow('M_Booth_Bulb', (1, .7, .4), 3.0)], origin=(lx, ly, 1.6))
    LIGHTS.append(('Light_Booth', (lx, ly, 1.5), 4, (1, .62, .32)))
    marker('Spawn_Trader', (0, BY0 + .85, 0), -90)

for n_, p, en, c in LIGHTS: light(n_, p, en, c)
marker('Spawn_Player', (0, Y0 + D * .55, 0), -90)
finish(anchors=['LiftCab_Shell', 'Booth_Shell'], ignore=DOORS)
