"""Character prototypes (blockouts with painted materials). usage: python3 build_character.py <Flower|MrNobody|Trader|Greed> <out.blend>
Front = -y, feet at the origin, 1 unit = 1 m.
  Flower   - a houseplant as tall as a person, in a clay pot. Flower = one mesh with shape keys Droop and Wilt (it wilts once seen):
             Unity: Droop 0->100, then crossfade Droop 100->0 with Wilt 0->100 (action Flower_Wilt shows it)
  MrNobody - coat, trousers, shoes and a hat on nobody: no head, no hands, black inside. The hat floats where the head would be
  Trader   - a shop assistant in a blue work coat with black sleeve protectors, long hands resting on a counter at 0.92 m
             (the Lift_Cab_Trader booth), a triangle for a head (Trader_Head pivots at the neck)
  Greed    - a 3.3 m red royal mantle with an ermine cape, one big eye for a head (Greed_Eye pivots at its centre), a crown of money"""
import sys, os, math
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from kit import *
NAME, OUT = sys.argv[-2], os.path.abspath(sys.argv[-1])
start(OUT, os.path.splitext(os.path.basename(OUT))[0])
VOID = flat('M_Void', (0, 0, 0), 1.0); IGN = []; ANCH = []
def spow(v, p): return math.copysign(abs(v) ** p, v)
def ell_rings(spec, n=16, sq=.8):
    """[(z, cy, rx, ry)] -> rings of a rounded-rectangle-ish ellipse (sq < 1 squares the sides)"""
    return [[(rx * spow(math.cos(a), sq), cy + ry * spow(math.sin(a), .9), z) for a in [i / n * 2 * math.pi for i in range(n)]] for z, cy, rx, ry in spec]
def front_y(spec, z):
    for (za, ca, _, ra), (zb, cb, _, rb) in zip(spec, spec[1:]):
        if za <= z <= zb: t = (z - za) / (zb - za); return (ca + (cb - ca) * t) - (ra + (rb - ra) * t)
def shoes(bm, mi, x=.1):
    for s in (-1, 1): prism(bm, lambda p, q, a: (s * x + a, p, q), [(-.2, 0), (.1, 0), (.1, .09), (-.05, .09), (-.16, .07), (-.2, .04)], -.048, .048, mi)
def fedora(bm, z, mi_felt=0, mi_band=1):
    cyl(bm, (0, 0, z), (0, 0, z + .012), .19, 14, mi_felt); cyl(bm, (0, 0, z + .012), (0, 0, z + .14), .105, 12, mi_felt, r1=.09)
    cyl(bm, (0, 0, z + .02), (0, 0, z + .042), .107, 12, mi_band)

# ================================================================ Mr. Nobody
if NAME == 'MrNobody':
    COAT = [(.42, 0, .29, .2), (.62, 0, .26, .18), (.85, 0, .22, .155), (1.02, 0, .2, .14), (1.2, 0, .22, .145), (1.38, 0, .24, .15), (1.5, 0, .25, .14),
            (1.56, 0, .23, .13), (1.6, 0, .13, .11), (1.7, 0, .125, .11)]
    bm = bmesh.new(); cup(bm, ell_rings(COAT), .02, 0, 1, closed_first=False)
    for s in (-1, 1):
        cup(bm, path_rings([(s * .22, 0, 1.5), (s * .265, 0, 1.25), (s * .285, -.02, 1.05), (s * .29, -.04, .86)], [.07, .066, .061, .058], 10), .012, 0, 1)
        cyl(bm, (s * .1, 0, .075), (s * .1, 0, .8), .075, 10, 2)
    for z in (1.32, 1.12, .92): cyl(bm, (0, front_y(COAT, z) + .004, z), (0, front_y(COAT, z) - .006, z), .014, 8, 3)
    shoes(bm, 4)
    make('MrNobody_Body', bm, 'MrNobody', [tm('T_CH_Wool_Black', (.5, .5)), VOID, flat('M_Trousers', (.035, .035, .04), .8), flat('M_Button', (.02, .02, .02), .3),
                                          flat('M_Shoe', (.015, .015, .015), .3)])
    bm = bmesh.new(); fedora(bm, 0); o = make('MrNobody_Hat', bm, 'MrNobody', [flat('M_Felt', (.03, .03, .03), .9), flat('M_HatBand', (.01, .01, .01), .5)], loc=(0, 0, 1.93))
    IGN.append(o.name); ANCH = ['MrNobody_Body']

# ================================================================ Trader
if NAME == 'Trader':
    HALAT = [(.5, 0, .25, .17), (.75, 0, .22, .15), (1.0, 0, .19, .13), (1.2, 0, .2, .135), (1.38, 0, .22, .14), (1.5, 0, .225, .13), (1.56, 0, .2, .12), (1.6, 0, .09, .08), (1.64, 0, .085, .075)]
    bm = bmesh.new(); cup(bm, ell_rings(HALAT), .018, 0, 1, closed_first=False)
    cyl(bm, (0, 0, 1.56), (0, 0, 1.72), .045, 10, 2)                                   # neck
    for s in (-1, 1):
        S_, E_, W_ = Vector((s * .215, 0, 1.47)), Vector((s * .26, -.12, 1.12)), Vector((s * .2, -.42, .94))
        cuff = E_ + (W_ - E_) * .82
        cup(bm, path_rings([tuple(S_), tuple(S_ + (E_ - S_) * .5), tuple(E_), tuple(E_ + (W_ - E_) * .5), tuple(cuff)], [.058, .056, .054, .05, .047], 10), .01, 0, 1)
        cyl(bm, tuple(E_ + (W_ - E_) * .22), tuple(E_ + (W_ - E_) * .78), .056, 10, 4)                    # black sleeve protectors
        cyl(bm, tuple(E_ + (W_ - E_) * .7), (s * .2, -.43, .935), .026, 8, 2)                              # wrist
        B_ = lambda x0, y0, z0, x1, y1, z1: wbox(bm, (min(x0, x1), min(y0, y1), z0), (max(x0, x1), max(y0, y1), z1), 2)
        B_(s * .2 - .042, -.42, .92, s * .2 + .042, -.51, .945)                                             # palm on the counter
        for k in range(4):
            fx = s * .2 - .0315 + k * .021; ln = (.13, .145, .14, .115)[k if s > 0 else 3 - k]
            B_(fx - .0075, -.5105, .92, fx + .0075, -.51 - ln, .936)                                         # long fingers
        B_(s * .2 - s * .05, -.44, .922, s * .2 - s * .036, -.53, .934)                                       # thumb
        cyl(bm, (s * .09, 0, .075), (s * .09, 0, .85), .068, 10, 3)
    for z in (1.4, 1.2, 1.0, .8): cyl(bm, (0, front_y(HALAT, z) + .004, z), (0, front_y(HALAT, z) - .006, z), .012, 8, 5)
    wbox(bm, (.07, front_y(HALAT, 1.38) - .006, 1.37), (.15, front_y(HALAT, 1.38) + .01, 1.395), 5)          # name badge, blank
    shoes(bm, 6, .09)
    make('Trader_Body', bm, 'Trader', [tm('T_CH_Halat', (.5, .5)), VOID, flat('M_Skin_Grey', (.56, .53, .49), .7), flat('M_Trousers', (.05, .05, .055), .8),
                                      flat('M_SleeveProtector', (.015, .015, .02), .35), flat('M_Button_White', (.8, .8, .76), .4), flat('M_Shoe', (.02, .015, .012), .35)])
    bm = bmesh.new(); prism(bm, lambda p, q, a: (p, a, q), [(-.16, 0), (.16, 0), (0, .34)], -.03, .03, 0)
    make('Trader_Head', bm, 'Trader', [flat('M_Triangle', (.86, .84, .78), .9)], loc=(0, 0, 1.72))
    ANCH = ['Trader_Body']

# ================================================================ Greed
if NAME == 'Greed':
    VEL, ERM, GOLD = tm('T_CH_Velvet', (.6, .6)), tm('T_CH_Ermine', (.22, .22)), flat('M_Gold', (.6, .42, .1), .3)
    MZ = [(0, 1.05, .09, 22), (.15, 1.03, .088, 21), (.4, 1.0, .085, 18), (.9, .92, .07, 13), (1.4, .82, .05, 8), (1.9, .7, .03, 4), (2.25, .58, .015, 2), (2.4, .44, 0, 1.5)]
    NA, TH_ = 44, .03; bm = bmesh.new()
    def arc(z, R_, A_, gap, d=0.0):
        a0, a1 = math.radians(-90 + gap), math.radians(270 - gap)
        return [((R_ - d) * (1 + A_ * math.sin(9 * a)) * math.cos(a), (R_ - d) * (1 + A_ * math.sin(9 * a)) * math.sin(a), z + (d if z == 0 else 0)) for a in [a0 + (a1 - a0) * i / NA for i in range(NA + 1)]]
    O_ = [[bm.verts.new(p) for p in arc(*m)] for m in MZ]; I_ = [[bm.verts.new(p) for p in arc(*m, d=TH_)] for m in MZ]
    for j in range(len(MZ) - 1):
        for i in range(NA):
            erm = j == 0 or i < 2 or i >= NA - 2
            bm.faces.new((O_[j][i], O_[j][i + 1], O_[j + 1][i + 1], O_[j + 1][i])).material_index = 1 if erm else 0
            bm.faces.new((I_[j + 1][i], I_[j + 1][i + 1], I_[j][i + 1], I_[j][i])).material_index = 2
        bm.faces.new((O_[j][0], O_[j + 1][0], I_[j + 1][0], I_[j][0])).material_index = 1
        bm.faces.new((O_[j + 1][NA], O_[j][NA], I_[j][NA], I_[j + 1][NA])).material_index = 1
    for i in range(NA):
        bm.faces.new((I_[0][i], I_[0][i + 1], O_[0][i + 1], O_[0][i])).material_index = 1
        L_ = len(MZ) - 1; bm.faces.new((O_[L_][i], O_[L_][i + 1], I_[L_][i + 1], I_[L_][i])).material_index = 0
    cape = [[(R_ * (1 + .03 * math.sin(7 * a)) * math.cos(a), R_ * (1 + .03 * math.sin(7 * a)) * math.sin(a), z) for a in [k / 32 * 2 * math.pi for k in range(32)]]
            for z, R_ in ((2.12, .7), (2.3, .6), (2.47, .45), (2.58, .34), (2.63, .3))]
    cup(bm, cape, .03, 1, 2, closed_first=False)
    make('Greed_Mantle', bm, 'Greed', [VEL, ERM, VOID], recalc=False)
    bm = bmesh.new(); res = bmesh.ops.create_uvsphere(bm, u_segments=16, v_segments=10, radius=.27); uvl = bm.loops.layers.uv.new('UVMap')
    for fc in bm.faces:
        for lp in fc.loops: lp[uvl].uv = (.5 + lp.vert.co.x / .54, .5 + lp.vert.co.z / .54)
    o = make('Greed_Eye', bm, 'Greed', [xm('T_CH_Eye', rough=.15)], loc=(0, 0, 2.75)); IGN.append(o.name)
    bm = bmesh.new(); zc = 3.06; band = [[(.19 * math.cos(a), .19 * math.sin(a), z) for a in [k / 24 * 2 * math.pi for k in range(24)]] for z in (zc, zc + .08)]
    cup(bm, band, .015, 0, 0, closed_first=False); uvl = bm.loops.layers.uv.get('UVMap') or bm.loops.layers.uv.new('UVMap')
    for k in range(9):
        a = k / 9 * 2 * math.pi; c, s_ = math.cos(a), math.sin(a); cell = ((k % 2) * .5, (k // 2 % 2) * .5); tilt = math.radians(14)
        M = Matrix.Translation((.2 * c, .2 * s_, zc + .06)) @ Matrix.Rotation(a + math.pi / 2, 4, 'Z') @ Matrix.Rotation(tilt, 4, 'X')
        vs = [bm.verts.new(M @ Vector(p)) for p in ((-.04, -.001, 0), (.04, -.001, 0), (.04, -.001, .17), (-.04, -.001, .17), (-.04, .001, 0), (.04, .001, 0), (.04, .001, .17), (-.04, .001, .17))]
        for q, uvs in (((0, 1, 2, 3), ((0, 0), (1, 0), (1, 1), (0, 1))), ((5, 4, 7, 6), ((1, 0), (0, 0), (0, 1), (1, 1)))):
            fc = bm.faces.new([vs[i] for i in q]); fc.material_index = 1
            for lp, (u, v) in zip(fc.loops, uvs): lp[uvl].uv = (cell[0] + u * .5, cell[1] + v * .5)
        for q in ((1, 5, 6, 2), (4, 0, 3, 7), (3, 2, 6, 7), (4, 5, 1, 0)): bm.faces.new([vs[i] for i in q]).material_index = 0
        a2 = a + math.pi / 9; cyl(bm, (.19 * math.cos(a2), .19 * math.sin(a2), zc + .08), (.19 * math.cos(a2), .19 * math.sin(a2), zc + .08 + .006 * (3 + k % 4)), .024, 10, 0)
    o = make('Greed_Crown', bm, 'Greed', [GOLD, xm('T_CH_Money')]); IGN.append(o.name)
    ANCH = ['Greed_Mantle']

# ================================================================ Flower
if NAME == 'Flower':
    L, Z0, NSR, SEG = 1.42, .17, 26, 6
    STATES = {'Basis': dict(lean=-5, bend=6, head=18, pe=28, curl=0, shrink=1.0, leaf=0),
              'Droop': dict(lean=-5, bend=55, head=30, pe=-12, curl=20, shrink=.95, leaf=22),
              'Wilt':  dict(lean=-5, bend=150, head=45, pe=-75, curl=60, shrink=.75, leaf=65)}
    LEAVES = [(.18, 60), (.34, 200), (.52, 320), (.7, 110)]
    def geo(P):
        V, Fc, M_, U = [], [], [], []
        N = 600; ds = L / N; th = lambda s: math.radians(P['lean']) * (s / L) + math.radians(P['bend']) * (s / L) ** 2.2
        cl = [Vector((0, 0, Z0))]
        for i in range(N): t = th((i + .5) * ds); cl.append(cl[-1] + Vector((0, -math.sin(t), math.cos(t))) * ds)
        def frame(s): i = min(N, max(0, int(round(s / ds)))); return cl[i], Matrix.Rotation(th(i * ds), 3, 'X')
        def face(idx, mi, uv=None): Fc.append(idx); M_.append(mi); U.append(uv)
        base = len(V)                                                                   # stem
        for r_ in range(NSR + 1):
            s = L * r_ / NSR; c, Rm = frame(s); rad = .018 - .007 * s / L
            for k in range(SEG): a = 2 * math.pi * k / SEG; V.append(c + Rm @ Vector((rad * math.cos(a), rad * math.sin(a), 0)))
        for r_ in range(NSR):
            for k in range(SEG): a0, a1 = base + r_ * SEG + k, base + r_ * SEG + (k + 1) % SEG; face((a0, a1, a1 + SEG, a0 + SEG), 0)
        face(tuple(base + k for k in range(SEG))[::-1], 0); face(tuple(base + NSR * SEG + k for k in range(SEG)), 0)
        def blade(origin, Rm, d, up, length, width, beta0, droop, nl, nw, mi, curl=0.0, cup_=.25):
            """two-layer leaf / petal: centre line rises at beta0 and bends down by droop along its length"""
            side = up.cross(d).normalized(); pts = [Vector(origin)]; b0 = len(V)
            for i in range(1, nl + 1):
                t = i / nl; b = math.radians(beta0 - droop * t - curl * t * t); pts.append(pts[-1] + (Rm @ (d * math.cos(b) + up * math.sin(b))) * (length / nl))
            for layer in (1, -1):
                for i in range(nl + 1):
                    t = i / nl; w = max(width * .15, width * math.sin(math.pi * min(t, .97)) ** .6) if i < nl else width * .1
                    tng = (pts[min(i + 1, nl)] - pts[max(i - 1, 0)]).normalized(); sd = Rm @ side; nb = tng.cross(sd).normalized()
                    for j in (-1, 0, 1):
                        V.append(pts[i] + sd * (w / 2 * j) + nb * (.0012 * layer + cup_ * w * (1 - abs(j)) * .25))
            for layer in (0, 1):
                o = b0 + layer * (nl + 1) * 3
                for i in range(nl):
                    for j in range(2):
                        q = (o + i * 3 + j, o + i * 3 + j + 1, o + (i + 1) * 3 + j + 1, o + (i + 1) * 3 + j)
                        uv = ((j / 2, i / nl), ((j + 1) / 2, i / nl), ((j + 1) / 2, (i + 1) / nl), (j / 2, (i + 1) / nl))
                        if not layer: q, uv = q[::-1], uv[::-1]
                        face(q, mi, uv)
            o0, o1 = b0, b0 + (nl + 1) * 3                                           # rims join the two layers
            A = lambda i, j: o0 + i * 3 + j; Bv = lambda i, j: o1 + i * 3 + j
            for i in range(nl):
                face((A(i + 1, 0), A(i, 0), Bv(i, 0), Bv(i + 1, 0)), mi, ((0, 0),) * 4); face((A(i, 2), A(i + 1, 2), Bv(i + 1, 2), Bv(i, 2)), mi, ((1, 0),) * 4)
            face((A(nl, 2), A(nl, 1), A(nl, 0), Bv(nl, 0), Bv(nl, 1), Bv(nl, 2)), mi, ((.5, 1),) * 6)
        for k, (sf, az) in enumerate(LEAVES):                                           # leaves
            c, Rm = frame(sf * L); d = Vector((math.cos(math.radians(az)), math.sin(math.radians(az)), 0))
            blade(c + Rm @ (d * .015), Rm, d, Vector((0, 0, 1)), .34, .09, 38 - P['leaf'] * .3, 30 + P['leaf'], 5, 2, 1, curl=P['leaf'] * .3)
        c, Rm = frame(L); Hm = Rm @ Matrix.Rotation(math.radians(P['head']), 3, 'X')           # head
        b0 = len(V)
        for zc, rr in ((-.06, .015), (-.015, .062), (0, .07), (.034, .07)):
            for k in range(10): a = 2 * math.pi * k / 10; V.append(c + Hm @ Vector((rr * math.cos(a), rr * math.sin(a), zc)))
        for r_ in range(3):
            for k in range(10): a0, a1 = b0 + r_ * 10 + k, b0 + r_ * 10 + (k + 1) % 10; face((a0, a1, a1 + 10, a0 + 10), 0)
        face(tuple(b0 + k for k in range(10))[::-1], 0)
        face(tuple(b0 + 30 + k for k in range(10)), 3, tuple((.5 + .5 * math.cos(2 * math.pi * k / 10), .5 + .5 * math.sin(2 * math.pi * k / 10)) for k in range(10)))
        for k in range(13):                                                             # petals
            a = 2 * math.pi * k / 13; d = Vector((math.cos(a), math.sin(a), 0))
            blade(c + Hm @ (d * .064 + Vector((0, 0, .024))), Hm, d, Vector((0, 0, 1)), .22 * P['shrink'], .075 * (P['shrink'] ** 2), P['pe'], 10 + P['curl'] * .5, 5, 2, 2, curl=P['curl'], cup_=.4)
        return V, Fc, M_, U
    V, Fc, M_, U = geo(STATES['Basis']); bm = bmesh.new(); vs = [bm.verts.new(v) for v in V]; uvl = bm.loops.layers.uv.new('UVMap')
    for idx, mi, uv in zip(Fc, M_, U):
        fc = bm.faces.new([vs[i] for i in idx]); fc.material_index = mi
        if uv:
            for lp, t in zip(fc.loops, uv): lp[uvl].uv = t
    fl = make('Flower', bm, 'Flower', [flat('M_Stem', (.12, .2, .07), .7), xm('T_CH_Leaf'), xm('T_CH_Petal'), xm('T_CH_FlowerDisk')], recalc=False)
    fl.shape_key_add(name='Basis', from_mix=False)
    for nm in ('Droop', 'Wilt'):
        kb = fl.shape_key_add(name=nm, from_mix=False); P_ = geo(STATES[nm])[0]
        for i, p in enumerate(P_): kb.data[i].co = p
    kb = fl.data.shape_keys.key_blocks
    for nm_, keys in (('Droop', ((1, 0), (20, 1), (60, 0))), ('Wilt', ((1, 0), (20, 0), (60, 1)))):
        for fr_, v in keys: kb[nm_].value = v; kb[nm_].keyframe_insert('value', frame=fr_)
    fl.data.shape_keys.animation_data.action.name = 'Flower_Wilt'; sc = bpy.context.scene; sc.frame_start, sc.frame_end = 1, 72; sc.render.fps = 24; sc.frame_set(1)
    bm = bmesh.new(); pot = [[(r * math.cos(a), r * math.sin(a), z) for a in [k / 16 * 2 * math.pi for k in range(16)]] for z, r in ((0, .1), (.17, .125), (.2, .132), (.215, .14))]
    cup(bm, pot, .012, 0, 0); cyl(bm, (0, 0, .15), (0, 0, .17), .118, 16, 1)
    make('Flower_Pot', bm, 'Flower', [flat('M_Terracotta', (.42, .18, .09), .9), flat('M_Soil', (.05, .035, .025), 1.0)])
    ANCH = ['Flower_Pot']

finish(anchors=ANCH, ignore=IGN)
