"""Hand-painted (procedural) textures for the street: cars, wheels, plates, decals.
Bases are real CC0 photos (ambientCG / Poly Haven previews) where a material exists;
details (panel lines, handles, glass, plates, cracks, streaks) are drawn.
usage: python3 paint_textures.py  -> writes into ../textures"""
import os, sys, math, random, subprocess, re
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageEnhance
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import car_spec as C
OUT = os.path.join(os.path.dirname(HERE), 'textures')
CACHE = '/tmp/claude-0/prev'
FONT = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
LIST = '/tmp/claude-0/papy.txt'
PACK = {'am': 'ambientcg', 'po': 'polyhaven', 'sh': 'sharetextures', 'cg': 'cgbookcase'}
ROWS = []

def src(key):
    """256 px colour preview of a CC0 texture (downloaded once from the Papyszoo mirror)"""
    os.makedirs(CACHE, exist_ok=True); p = f'{CACHE}/{key}.png'
    if not os.path.exists(p):
        pk, name = key.split('__'); lines = open(LIST).read().split('\n')
        c = [l for l in lines if l.startswith(f'packs/{PACK[pk]}-textures/textures/{name}/') and l.endswith('_preview.png')]
        col = [l for l in c if re.search(r'(?i)(color|albedo|diffuse|diff|basecolor|col)[^/]*_preview', l)] or c
        subprocess.run(['curl', '-sS', '--retry', '3', '-o', p, 'https://raw.githubusercontent.com/Papyszoo/CC0-Public-Domain-Textures/main/' + col[0]], check=True)
    return Image.open(p).convert('RGB')
def q15(im):
    if im.mode == 'RGBA':
        r, g, b, a = im.split(); rgb = Image.merge('RGB', (r, g, b)).point(lambda v: (v >> 3) << 3 | (v >> 5)); return Image.merge('RGBA', (*rgb.split(), a))
    return im.point(lambda v: (v >> 3) << 3 | (v >> 5))
def save(im, name, note):
    q15(im).save(os.path.join(OUT, name + '.png')); ROWS.append(f'| {name}.png | {im.size[0]}x{im.size[1]} | {note} |')
def noise(w, h, cells, seed, blur=0):
    r = np.random.RandomState(seed); a = r.rand(max(2, h // cells), max(2, w // cells))
    im = Image.fromarray((a * 255).astype('uint8')).resize((w, h), Image.BICUBIC)
    if blur: im = im.filter(ImageFilter.GaussianBlur(blur))
    return np.asarray(im).astype(float) / 255.0
def tile(img, w, h):
    out = Image.new('RGB', (w, h))
    for y in range(0, h, img.height):
        for x in range(0, w, img.width): out.paste(img, (x, y))
    return out

# ================================================================== cars
CARS = {   # name: (kind, paint rgb, rust 0..1, dirt 0..1, extras)
    'Sedan_White':  ('sedan', (196, 190, 168), .25, .55, {'leaves': True}),
    'Sedan_Blue':   ('sedan', (88, 116, 140), .35, .5, {'crack': True}),
    'Sedan_Cherry': ('sedan', (112, 38, 36), .3, .45, {'leaves': True}),
    'Wagon_Olive':  ('wagon', (92, 98, 70), .45, .6, {}),
    'Sedan_Wreck':  ('sedan', (140, 132, 112), 1.0, .9, {'wreck': True}),
}
def poly(d, pts, fill=None, outline=None, width=1):
    d.polygon([tuple(map(float, p)) for p in pts], fill=fill, outline=outline, width=width) if width == 1 else (d.polygon([tuple(map(float, p)) for p in pts], fill=fill), d.line([tuple(map(float, p)) for p in pts + pts[:1]], fill=outline, width=width))
def car_texture(name, kind, paint, rust, dirt, ex):
    rnd = random.Random(sum(map(ord, name))); S = 256
    base = np.ones((S, S, 3)) * np.array(paint, float)
    base *= (1 + (noise(S, S, 32, 1) - .5) * .16)[..., None]; base *= (1 + (noise(S, S, 2, 2) - .5) * .05)[..., None]
    rowz = np.arange(S)[:, None]
    shade = np.ones((S, S))
    shade[:96] *= (1.06 - (rowz[:96] / 96.0) * .2)                                     # side: lighter at the shoulder
    shade[96:176] *= 1.1                                                                # top catches the sky
    base *= shade[..., None]
    im = Image.fromarray(np.clip(base, 0, 255).astype('uint8')); d = ImageDraw.Draw(im, 'RGBA')
    dark = tuple(int(c * .35) for c in paint)
    G = C.greenhouse(kind)
    # ---------------- side region
    bfx, bfz = G['bf']; brx, brz = G['br']; tf, tr, roof = G['tf'], G['tr'], G['roof']
    ax = lambda z: bfx + (z - bfz) * (tf - bfx) / (roof - bfz)                        # A-pillar line x(z)
    rx = lambda z: brx + (z - brz) * (tr - brx) / (roof - brz)                        # rear pillar line x(z)
    z0, z1 = max(bfz, brz) + .05, roof - .06
    bp0, bp1 = C.B_PILLAR
    wins = [[(ax(z0) - .07, z0), (bp0 + .03, z0), (bp1 + .03, z1), (ax(z1) - .05, z1)]]
    if kind == 'wagon':
        wins += [[(bp0 - .07, z0), (-1.05, z0), (-1.05, z1), (bp1 - .07, z1)], [(-1.13, z0), (rx(z0) + .08, z0), (rx(z1) + .08, z1), (-1.13, z1)]]
    else:
        wins += [[(bp0 - .07, z0), (rx(z0) + .14, z0), (rx(z1) + .1, z1), (bp1 - .07, z1)]]
    gh = [C.px_side(bfx, bfz), C.px_side(tf, roof), C.px_side(tr, roof), C.px_side(brx, brz)]
    poly(d, gh, fill=tuple(int(c * .92) for c in paint))
    def glass(pts_px, top_v, bot_v, broken=False):
        xs = [p[0] for p in pts_px]; ys = [p[1] for p in pts_px]
        g = Image.new('RGBA', im.size, (0, 0, 0, 0)); gd = ImageDraw.Draw(g)
        for yy in range(int(min(ys)), int(max(ys)) + 1):
            t = (yy - min(ys)) / max(1, max(ys) - min(ys)); c = tuple(int(top_v[i] + (bot_v[i] - top_v[i]) * t) for i in range(3))
            gd.line([(min(xs), yy), (max(xs), yy)], fill=c + (255,))
        mask = Image.new('L', im.size, 0); ImageDraw.Draw(mask).polygon([tuple(p) for p in pts_px], fill=255)
        refl = Image.new('RGBA', im.size, (0, 0, 0, 0)); rd = ImageDraw.Draw(refl)
        cx = (min(xs) + max(xs)) / 2
        rd.polygon([(cx - 6, min(ys)), (cx + 2, min(ys)), (cx - 10, max(ys)), (cx - 18, max(ys))], fill=(150, 160, 175, 70))
        rd.polygon([(cx + 6, min(ys)), (cx + 9, min(ys)), (cx - 3, max(ys)), (cx - 6, max(ys))], fill=(150, 160, 175, 40))
        g.alpha_composite(refl)
        if broken:
            gd2 = ImageDraw.Draw(g)
            for k in range(14): gd2.point((rnd.uniform(min(xs), max(xs)), rnd.uniform(min(ys), max(ys))), fill=(4, 4, 6, 255))
            gd2.polygon([(cx - 4, min(ys) + 2), (cx + 6, (min(ys) + max(ys)) / 2), (cx - 2, max(ys) - 1), (cx - 9, (min(ys) + max(ys)) / 2)], fill=(3, 3, 4, 255))
        im.paste(g, (0, 0), Image.composite(g.split()[3], Image.new('L', im.size, 0), mask))
        d.line([tuple(p) for p in pts_px] + [tuple(pts_px[0])], fill=(14, 14, 14, 255), width=1)
    for w in wins: glass([C.px_side(*p) for p in w], (22, 26, 34), (48, 56, 66), ex.get('wreck') and rnd.random() < .6)
    # door lines, molding, handles
    sl = lambda x0, z0_, x1, z1_, c, wdt=1: d.line([C.px_side(x0, z0_), C.px_side(x1, z1_)], fill=c, width=wdt)
    seam = dark + (220,)
    for x in (C.DOORS['front_door'][0], C.DOORS['front_door'][1], C.DOORS['rear_door'][1]): sl(x, .88, x, .31, seam)
    sl(C.DOORS['front_door'][0], .31, C.DOORS['rear_door'][1], .31, seam)
    sl(1.95, .70, -1.95, .70, (205, 205, 200, 230)); sl(1.95, .685, -1.95, .685, (60, 60, 60, 120))
    for x0 in (-.10, -.76):
        d.rectangle([C.px_side(x0 + .1, .845), C.px_side(x0, .82)], fill=(200, 200, 195, 255)); d.point(C.px_side(x0 + .07, .80), fill=(10, 10, 10, 255))
    d.rectangle([C.px_side(1.68, .755), C.px_side(1.62, .725)], fill=(230, 140, 40, 255))
    fx, fz = C.px_side(-1.55, .78); d.ellipse([fx - 3, fz - 2, fx + 3, fz + 2], outline=seam, fill=tuple(int(c * .9) for c in paint) + (255,))
    # ---------------- top region
    tl = lambda x0, y0, x1, y1, c, wdt=1: d.line([C.px_top(x0, y0), C.px_top(x1, y1)], fill=c, width=wdt)
    for y in (-.70, .70): tl(.69, y, 2.0, y, seam)
    tl(.69, -.70, .69, .70, seam); tl(2.0, -.70, 2.0, .70, seam)
    if kind == 'sedan':
        for y in (-.70, .70): tl(-.97, y, -1.96, y, seam)
        tl(-.97, -.70, -.97, .70, seam); tl(-1.96, -.70, -1.96, .70, seam)
    bw, tw = G['bw'], G['tw']
    ws = [C.px_top(bfx - .04, -bw + .07), C.px_top(bfx - .04, bw - .07), C.px_top(tf + .05, tw - .06), C.px_top(tf + .05, -tw + .06)]
    glass(ws, (38, 44, 54), (70, 80, 92), ex.get('wreck'))
    if kind == 'sedan':
        rw = [C.px_top(tr - .05, -tw + .06), C.px_top(tr - .05, tw - .06), C.px_top(brx + .05, bw - .08), C.px_top(brx + .05, -bw + .08)]
        glass(rw, (60, 70, 82), (30, 34, 42), ex.get('wreck'))
    for y in (-tw + .01, tw - .01): tl(tf, y, tr, y, (40, 40, 40, 150))                 # rain gutters
    if ex.get('crack'):
        cx, cy = C.px_top(.45, .25)
        for k in range(7):
            a = rnd.uniform(0, 2 * math.pi); L = rnd.uniform(6, 16); d.line([(cx, cy), (cx + math.cos(a) * L, cy + math.sin(a) * L * .6)], fill=(200, 205, 210, 170))
    if ex.get('leaves') or ex.get('wreck'):
        for k in range(60 if ex.get('wreck') else 35):
            x, y = rnd.uniform(-1.9, 1.9), rnd.uniform(-.78, .78)
            px, py = C.px_top(x, y); c = rnd.choice([(150, 90, 30), (170, 120, 40), (110, 70, 30), (90, 60, 25)])
            d.rectangle([px, py, px + rnd.randint(1, 2), py + 1], fill=c + (255,))
    # ---------------- front region
    fr = lambda y0, z0_, y1, z1_: [C.px_front(y0, z1_), C.px_front(y1, z0_)]
    d.rectangle(fr(-.36, .55, .36, .77), fill=(20, 20, 20, 255))
    for z in (.59, .64, .69, .74): d.line([C.px_front(-.35, z), C.px_front(.35, z)], fill=(150, 150, 150, 255))
    d.rectangle(fr(-.37, .545, .37, .775), outline=(185, 185, 180, 255))
    for (yy, zz) in C.HEADLIGHTS:
        for s in (-1, 1):
            cx, cy = C.px_front(s * yy, zz); d.ellipse([cx - 6, cy - 5, cx + 6, cy + 5], fill=(30, 30, 30, 255), outline=(170, 170, 165, 255))
    for s in (-1, 1): d.rectangle(fr(s * .55 if s > 0 else -.75, .45, s * .75 if s > 0 else -.55, .50), fill=(225, 140, 45, 255))
    d.rectangle(fr(-.8, .27, .8, .35), fill=tuple(int(c * .5) for c in paint) + (255,))
    # ---------------- back region
    bk = lambda y0, z0_, y1, z1_: [C.px_back(y1, z1_), C.px_back(y0, z0_)]
    d.line([C.px_back(-.75, .84), C.px_back(.75, .84)], fill=seam)
    for s in (-1, 1):
        a, b_ = (C.TAIL[0], C.TAIL[1]) if s > 0 else (-C.TAIL[1], -C.TAIL[0])
        d.rectangle(bk(a, C.TAIL[2], b_, C.TAIL[3]), fill=(120, 18, 14, 255), outline=(170, 170, 165, 255))
    d.rectangle(bk(-.3, .43, .3, .57), fill=tuple(int(c * .6) for c in paint) + (255,))
    if kind == 'wagon':
        glass([C.px_back(-.58, 1.36), C.px_back(.58, 1.36), C.px_back(.6, .96), C.px_back(-.6, .96)], (26, 30, 38), (56, 64, 74), False)
        for y in (-.64, .64): d.line([C.px_back(y, .45), C.px_back(y, 1.4)], fill=seam)
    # ---------------- rust + dirt (real rust photo through noise masks)
    rust_img = tile(src('am__Rust004').resize((128, 128), Image.BOX), S, S)
    m = np.zeros((S, S))
    yy, xx = np.mgrid[0:S, 0:S]
    side = (yy < 96).astype(float); sx, sz = 256 / 4.2, 96 / 1.30           # px per metre on the side projection
    for axx in (C.AX_F, C.AX_R):                                             # rust eats the arch lips first
        cx, cy = C.px_side(axx, .29)
        dist = np.sqrt(((xx - cx) / sx) ** 2 + ((yy - cy) / sz) ** 2)        # metres from the wheel centre
        lip = np.clip(1 - np.abs(dist - C.ARCH_R - .03) / (.03 + .07 * rust), 0, 1)
        m += lip * side * np.clip((yy - (cy - .25 * sz)) / (.15 * sz), .25, 1)   # mostly the lower half of the lip
    m += np.clip((yy - 84) / 8.0, 0, 1) * side                               # sills
    m *= noise(S, S, 5, 7) > (.58 - rust * .3)
    m += (noise(S, S, 4, 8) > (.955 - rust * .05)) * (.4 + .6 * side)       # a few small blisters
    if rust > .8: m += (noise(S, S, 14, 9) > .72) * side * np.clip((yy - 40) / 30.0, 0, 1)   # wreck: big patches low on the body
    m = np.clip(m, 0, 1)
    mb = np.asarray(Image.fromarray((m * 255).astype('uint8')).filter(ImageFilter.GaussianBlur(1.3))).astype(float) / 255
    edge = np.clip(mb - m, 0, 1) * 1.6                                       # dark bubbling ring around each patch
    arr = np.asarray(im).astype(float); ra = np.asarray(rust_img).astype(float)
    arr = arr * (1 - edge[..., None] * .45)
    arr = arr * (1 - m[..., None] * .9) + ra * (m[..., None] * .9)
    dg = np.clip((yy - 70) / 26.0, 0, 1) * (yy < 96) * dirt * (.6 + .4 * noise(S, S, 4, 11))
    arr = arr * (1 - dg[..., None] * .55) + np.array([62, 50, 36]) * dg[..., None] * .55
    arr[248:, 248:] = 0
    im = Image.fromarray(np.clip(arr, 0, 255).astype('uint8'))
    save(im, 'T_Car_' + name, f'drawn car atlas ({kind}): paint + panel lines/glass/lights drawn, rust from ambientCG Rust004')

def wheel_texture():
    W_, H_ = 128, 64; im = Image.new('RGB', (W_, H_), (18, 18, 18))
    tread = src('am__Rubber004').resize((64, 64), Image.BOX); tread = ImageEnhance.Brightness(tread).enhance(.55); im.paste(tread, (0, 0))
    d = ImageDraw.Draw(im)
    for y in range(0, 64, 6): d.line([(4, y), (14, y + 3), (24, y)], fill=(8, 8, 8)); d.line([(40, y), (50, y + 3), (60, y)], fill=(8, 8, 8))
    for x in (30, 34): d.line([(x, 0), (x, 63)], fill=(10, 10, 10))
    cx, cy = 96, 32
    d.ellipse([cx - 31, cy - 31, cx + 31, cy + 31], fill=(26, 26, 26)); d.ellipse([cx - 27, cy - 27, cx + 27, cy + 27], outline=(38, 38, 38))
    rim = src('am__Metal009').resize((64, 64), Image.BOX); mask = Image.new('L', (64, 64), 0); ImageDraw.Draw(mask).ellipse([12, 12, 52, 52], fill=255)
    im.paste(ImageEnhance.Brightness(rim).enhance(.8), (64, 0), mask)
    d.ellipse([cx - 13, cy - 13, cx + 13, cy + 13], fill=(170, 170, 168), outline=(90, 90, 90)); d.ellipse([cx - 6, cy - 6, cx + 6, cy + 6], fill=(205, 205, 200))
    d.arc([cx - 11, cy - 11, cx + 11, cy + 11], 200, 260, fill=(240, 240, 235));
    for a in range(4): r = math.radians(a * 90 + 45); d.point((cx + 9 * math.cos(r), cy + 9 * math.sin(r)), fill=(60, 60, 60))
    save(im, 'T_Car_Wheel', 'drawn wheel: tread from ambientCG Rubber004, rim from Metal009, hubcap drawn')

PLATES = ['а 4713 ЛГ', 'м 0961 ЛД', 'к 2208 ЛГ', 'о 5537 ЛЕ']
def plates_texture():
    im = Image.new('RGB', (128, 64), (20, 20, 20)); d = ImageDraw.Draw(im); f = ImageFont.truetype(FONT, 10)
    for i, t in enumerate(PLATES):
        x, y = (i % 2) * 64, (i // 2) * 16
        d.rectangle([x, y, x + 63, y + 15], fill=(214, 212, 200)); d.rectangle([x + 1, y + 1, x + 62, y + 14], outline=(30, 30, 30))
        d.text((x + 32, y + 8), t, font=f, fill=(20, 20, 20), anchor='mm')
    im = Image.fromarray(np.clip(np.asarray(im).astype(float) * (1 - (noise(128, 64, 3, 5) * .25)[..., None]), 0, 255).astype('uint8'))
    save(im, 'T_Car_Plates', 'drawn licence plates (fictional numbers)')


# ================================================================== decals (RGBA, transparent edges)
def blob_mask(w, h, seed, soft=6, rough=.35, shape=None):
    """irregular blob alpha 0..1: noisy radius, soft edge"""
    yy, xx = np.mgrid[0:h, 0:w]; cx, cy = w / 2, h / 2
    ang = np.arctan2(yy - cy, xx - cx); r = np.random.RandomState(seed)
    rad = np.ones_like(ang)
    for k in range(2, 7): rad += r.uniform(-rough, rough) / k * np.cos(k * ang + r.uniform(0, 6.28))
    if shape is not None: rad = shape
    d = np.sqrt(((xx - cx) / (w / 2 * .82)) ** 2 + ((yy - cy) / (h / 2 * .82)) ** 2) / rad
    a = np.clip((1 - d) * (min(w, h) / 2 / soft), 0, 1)
    return a * (.75 + .25 * noise(w, h, 3, seed + 1))
def rgba(rgb, a): arr = np.dstack([np.asarray(rgb).astype(float), np.clip(a, 0, 1) * 255]); return Image.fromarray(arr.astype('uint8'), 'RGBA')
def decals():
    # puddles: dark water, wet rim, ragged edge
    for i, sd in enumerate((21, 22)):
        a = blob_mask(128, 128, sd, soft=10); core = np.clip((a - .45) * 3, 0, 1)
        col = np.zeros((128, 128, 3)) + np.array([30, 33, 38]); col = col * (1 - core[..., None]) + np.array([12, 14, 18]) * core[..., None]
        col *= (.9 + .2 * noise(128, 128, 8, sd))[..., None]
        save(rgba(col, np.clip(a * 1.25, 0, .97)), 'T_Decal_Puddle_%d' % (i + 1), 'drawn puddle decal (water + wet rim, alpha edges)')
    # cracks: branching dark lines
    im = Image.new('RGBA', (256, 256), (0, 0, 0, 0)); d = ImageDraw.Draw(im); r = random.Random(5)
    def crack(x, y, a, L, w, depth):
        for k in range(int(L)):
            a += r.uniform(-.35, .35); nx, ny = x + math.cos(a) * 3, y + math.sin(a) * 3
            d.line([(x, y), (nx, ny)], fill=(14, 13, 12, 210), width=w); x, y = nx, ny
            if depth < 2 and r.random() < .07: crack(x, y, a + r.choice((-1, 1)) * r.uniform(.5, 1.1), L * .45, max(1, w - 1), depth + 1)
    for k in range(5): crack(r.uniform(20, 236), r.uniform(20, 236), r.uniform(0, 6.28), r.uniform(25, 60), 2, 0)
    save(im, 'T_Decal_Cracks', 'drawn asphalt cracks')
    # oil / dark stains
    a = blob_mask(64, 64, 31, soft=14, rough=.5); col = np.zeros((64, 64, 3)) + np.array([16, 14, 12])
    save(rgba(col, a * .75), 'T_Decal_OilStain', 'drawn oil stain')
    # leaves: real photo of leaves on black -> alpha from luminance
    for name, key in (('T_Decal_Leaves', 'am__ScatteredLeaves006'), ('T_Decal_LeafPile', 'am__ScatteredLeaves004')):
        im = src(key).resize((128, 128), Image.BOX); arr = np.asarray(im).astype(float)
        lum = arr.mean(axis=2); a = np.clip((lum - 18) / 30.0, 0, 1)
        if 'Pile' not in name: a *= blob_mask(128, 128, 81, soft=24, rough=.3)
        arr = arr * np.array([.95, .85, .7]); save(rgba(arr, a), name, f'ambientCG {key[4:]}, alpha from luminance')
    # asphalt patch: newer darker asphalt, jagged rectangle
    base = src('am__Asphalt026A').resize((128, 128), Image.BOX); base = ImageEnhance.Brightness(base).enhance(.8)
    yy, xx = np.mgrid[0:128, 0:128]; e = np.minimum(np.minimum(xx, 127 - xx), np.minimum(yy, 127 - yy)).astype(float)
    a = np.clip((e - 3 + (noise(128, 128, 4, 41) - .5) * 8) / 2.0, 0, 1)
    save(rgba(base, a), 'T_Decal_AsphaltPatch', 'ambientCG Asphalt026A, jagged alpha edge')
    # ground blend patches (big, soft): moss/grass, dry grass + dirt, rotten leaves, mud
    for name, key, sat, br in (('T_Decal_GroundMoss', 'am__Ground037', .5, .6), ('T_Decal_GroundDryGrass', 'am__Ground068', .65, .75),
                               ('T_Decal_GroundLeaves', 'po__dry_decay_leaves', .7, .8), ('T_Decal_GroundMud', 'po__brown_mud_02', .7, .85)):
        im = ImageEnhance.Brightness(ImageEnhance.Color(src(key).resize((128, 128), Image.BOX)).enhance(sat)).enhance(br)
        save(rgba(im, blob_mask(128, 128, sum(map(ord, name)), soft=22, rough=.45)), name, f'{key.split("__")[0]=="am" and "ambientCG" or "Poly Haven"} {key[4:]}, blob alpha')
    # big trampled mud area (playground): tiled mud photo + soft blob edge
    mud4 = tile(ImageEnhance.Brightness(ImageEnhance.Color(src('am__Ground048').resize((64, 64), Image.BOX)).enhance(.7)).enhance(.8), 256, 256)
    save(rgba(mud4, blob_mask(256, 256, 91, soft=30, rough=.18) * 1.15), 'T_Decal_MudArea', 'ambientCG Ground048 tiled 4x, soft blob alpha')
    # trodden path strip: tiles along v, alpha fades across u
    mud = ImageEnhance.Color(src('am__Ground048').resize((64, 128), Image.BOX)).enhance(.7); mud = ImageEnhance.Brightness(mud).enhance(.85)
    u = np.abs(np.arange(64) - 31.5) / 32.0; a = np.clip((1 - u) * 2.2 - .2, 0, 1)[None, :] * np.ones((128, 1))
    a *= (.7 + .3 * noise(64, 128, 3, 51)); save(rgba(mud, a), 'T_Decal_TrodPath', 'ambientCG Ground048, alpha fades to the sides')
    # rain streaks under sills/slabs, rust streaks, plinth grime
    for name, colr, seed, cnt in (('T_Decal_RainStreaks', (26, 26, 25), 61, 13), ('T_Decal_RustStreaks', (105, 52, 22), 62, 6)):
        r = random.Random(seed); a = np.zeros((128, 64))
        for k in range(cnt):
            x = r.uniform(4, 60); w = r.uniform(1.5, 4.5); L = r.uniform(.45, 1.0); st = r.uniform(.4, 1.0)
            xs = np.arange(64); prof = np.clip(1 - np.abs(xs - x) / w, 0, 1)
            fade = np.clip(1 - np.arange(128) / (128 * L), 0, 1) ** 1.3
            a += st * fade[:, None] * prof[None, :]
        a = np.clip(a, 0, 1) * (.7 + .3 * noise(64, 128, 2, seed)); col = np.zeros((128, 64, 3)) + np.array(colr)
        save(rgba(col, np.clip(a * 1.1, 0, .92)), name, 'drawn ' + ('rain' if 'Rain' in name else 'rust') + ' streaks')
    g = np.clip(1 - np.arange(64) / 64.0, 0, 1)[:, None] ** 1.6 * np.ones((1, 128)); g = g[::-1]
    g *= (.6 + .4 * noise(128, 64, 6, 71)); col = np.zeros((64, 128, 3)) + np.array([45, 38, 30])
    save(rgba(col, g * .8), 'T_Decal_PlinthGrime', 'drawn splash grime gradient')
    # manhole covers (cgbookcase, round, on black)
    for name, key in (('T_Decal_Manhole_1', 'cg__ManholeCover10'), ('T_Decal_Manhole_2', 'cg__ManholeCover06')):
        im = ImageEnhance.Color(src(key).resize((64, 64), Image.BOX)).enhance(.6); yy, xx = np.mgrid[0:64, 0:64]
        a = (np.sqrt((xx - 31.5) ** 2 + (yy - 31.5) ** 2) < 30.5).astype(float); save(rgba(im, a), name, f'cgbookcase {key[4:]}, round cut')
    # bigger tiles for large surfaces (256 px = 4 m, half the visible repetition)
    for name, key, sat, br in (('T_Ext_Road', 'am__Asphalt025A', .6, 1), ('T_Ext_Sidewalk', 'am__Asphalt021', .6, 1), ('T_Ext_Lawn', 'po__brown_mud_leaves_01', .75, 1)):
        im = ImageEnhance.Color(src(key)).enhance(sat); save(im, name, f'{key[4:]} at full 256 px, saturation x{sat}')

# ================================================================== props
def scribble(d, x0, y0, x1, y, r, col=(40, 40, 50, 255)):
    x = x0
    while x < x1 - 2:
        w = r.randint(2, 6); d.line([(x, y), (min(x + w, x1), y)], fill=col); x += w + r.randint(1, 3)
def props():
    r = random.Random(3)
    paper = src('am__Paper001').resize((64, 64), Image.BOX)
    # notices atlas 128x64: [A4 notice | tear-off phone notice]
    im = Image.new('RGB', (128, 64), (200, 200, 195)); im.paste(paper, (0, 0)); im.paste(paper, (64, 0)); d = ImageDraw.Draw(im)
    f = ImageFont.truetype(FONT, 7)
    d.text((32, 6), 'ВНИМАНИЕ', font=f, fill=(150, 20, 20), anchor='mm')
    for y in range(13, 60, 4): scribble(d, 5, 0, 59, y, r)
    d.text((96, 6), 'ПРОДАМ', font=f, fill=(30, 30, 60), anchor='mm')
    for y in range(13, 34, 4): scribble(d, 69, 0, 123, y, r)
    for k in range(8):
        x = 66 + k * 7.5; d.line([(x, 38), (x, 63)], fill=(150, 150, 140)); 
        if k in (2, 5): d.rectangle([x + 1, 38, x + 6, 63], fill=(70, 72, 70))           # strips already torn off
        else:
            for yy in range(41, 62, 3): d.point((x + 3 + r.randint(-1, 1), yy), fill=(40, 40, 60))
    a = np.asarray(im).astype(float) * (.85 + .15 * noise(128, 64, 4, 3))[..., None]
    save(Image.fromarray(np.clip(a, 0, 255).astype('uint8')), 'T_Prop_Notices', 'ambientCG Paper001 + drawn notices (scribbled text, tear-off phone strips)')
    # entrance door 64x128: painted steel, frame, rivets, scratches, stickers, code lock
    base = ImageEnhance.Color(src('am__PaintedMetal013').resize((64, 128), Image.BOX)).enhance(.5)
    tint = np.asarray(base).astype(float) * np.array([.62, .5, .42]); im = Image.fromarray(np.clip(tint, 0, 255).astype('uint8')); d = ImageDraw.Draw(im, 'RGBA')
    d.rectangle([2, 2, 61, 125], outline=(30, 24, 20, 255)); d.rectangle([5, 5, 58, 122], outline=(120, 100, 85, 120))
    for y in (8, 64, 119):
        for x in (8, 55): d.point((x, y), fill=(25, 20, 18, 255))
    d.rectangle([46, 58, 56, 74], fill=(150, 150, 145, 255)); d.rectangle([48, 60, 54, 66], fill=(40, 40, 40, 255))
    for yy in range(67, 73, 2):
        for xx in range(48, 55, 3): d.point((xx, yy), fill=(20, 20, 20, 255))
    for k in range(25):
        x, y = r.uniform(4, 60), r.uniform(10, 120); d.line([(x, y), (x + r.uniform(-6, 6), y + r.uniform(-2, 2))], fill=(170, 160, 150, 90))
    for (x, y, c) in ((12, 40, (220, 220, 210)), (20, 90, (230, 200, 60)), (30, 30, (210, 215, 225))):
        d.rectangle([x, y, x + 9, y + 6], fill=c + (230,)); scribble(d, x + 1, 0, x + 8, y + 3, r, (60, 60, 60, 255))
    save(im, 'T_Prop_EntranceDoor', 'ambientCG PaintedMetal013 tinted + drawn frame, rivets, code lock, scratches, stickers')
    # trash container side 128x64: green paint, rust, stencil
    base = ImageEnhance.Color(src('am__PaintedMetal006').resize((128, 64), Image.BOX)).enhance(.55); im = base.copy(); d = ImageDraw.Draw(im, 'RGBA')
    f2 = ImageFont.truetype(FONT, 11); d.text((64, 30), 'ЖЭК-7', font=f2, fill=(225, 225, 215, 210), anchor='mm')
    for y in (8, 52): d.line([(0, y), (127, y)], fill=(20, 30, 22, 160), width=2)
    save(im, 'T_Prop_Container', 'ambientCG PaintedMetal006 + drawn stencil and ribs')
    # garage door leaves 128x128 = 4 variants of 64x64 (one leaf each): paint photo + frame, ribs, number
    keys = [('am__PaintedMetal007', (1, 1, 1)), ('am__PaintedMetal006', (1, 1, 1)), ('am__PaintedMetal013', (.75, .62, .5)), ('cg__PaintedMetal01', (.9, .9, .85))]
    im = Image.new('RGB', (128, 128)); d = ImageDraw.Draw(im, 'RGBA'); f3 = ImageFont.truetype(FONT, 12)
    for i, (k, t) in enumerate(keys):
        x0, y0 = (i % 2) * 64, (i // 2) * 64
        b = ImageEnhance.Color(src(k).resize((64, 64), Image.BOX)).enhance(.5); b = Image.fromarray(np.clip(np.asarray(b).astype(float) * np.array(t), 0, 255).astype('uint8'))
        im.paste(b, (x0, y0)); d.rectangle([x0, y0, x0 + 63, y0 + 63], outline=(25, 22, 20, 255), width=2)
        for xx in range(x0 + 10, x0 + 60, 12): d.line([(xx, y0 + 3), (xx, y0 + 60)], fill=(0, 0, 0, 50))
        d.text((x0 + 32, y0 + 18), str(r.randint(11, 64)), font=f3, fill=(235, 235, 225, 200), anchor='mm')
        for k2 in range(5):
            xx = r.uniform(x0 + 4, x0 + 60); d.line([(xx, y0 + 2), (xx + r.uniform(-1, 1), y0 + r.uniform(15, 50))], fill=(110, 55, 25, 120), width=1)
    save(im, 'T_Prop_GarageDoors', 'ambientCG/cgbookcase painted metal + drawn frames, ribs, numbers, rust drips')
    # twig card: bare branch silhouettes with alpha
    im = Image.new('RGBA', (128, 128), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    def twig(x, y, a, L, w, dep):
        for k in range(int(L)):
            a += r.uniform(-.25, .25); nx, ny = x + math.cos(a) * 2.2, y - math.sin(a) * 2.2
            d.line([(x, y), (nx, ny)], fill=(48, 40, 34, 255), width=max(1, int(w))); x, y = nx, ny; w *= .985
            if dep < 4 and r.random() < .12: twig(x, y, a + r.choice((-1, 1)) * r.uniform(.4, .9), L * .55, w * .7, dep + 1)
    twig(64, 127, math.pi / 2, 50, 3, 0)
    save(im, 'T_Prop_Twigs', 'drawn branching twigs (alpha card)')
    # decorative fence: bars with arches, green paint, alpha
    im = Image.new('RGBA', (64, 32), (0, 0, 0, 0)); d = ImageDraw.Draw(im); g = (52, 82, 58, 255)
    d.rectangle([0, 2, 63, 4], fill=g); d.rectangle([0, 27, 63, 29], fill=g)
    for x in range(4, 64, 8): d.line([(x, 4), (x, 27)], fill=g, width=2)
    for x in range(0, 64, 16): d.arc([x, 6, x + 16, 22], 180, 360, fill=g, width=2)
    save(im, 'T_Prop_Fence', 'drawn decorative fence pattern (alpha)')

if __name__ == '__main__':
    which = sys.argv[1:] or ['cars']
    if 'cars' in which:
        for n, (k, p, r, dd, ex) in CARS.items(): car_texture(n, k, p, r, dd, ex)
        wheel_texture(); plates_texture()
    if 'decals' in which: decals()
    if 'props' in which: props()
    md = os.path.join(OUT, 'SOURCES.md'); s = open(md).read()
    s = '\n'.join(l for l in s.split('\n') if not any(l.startswith('| ' + r.split('|')[1].strip() + ' ') for r in ROWS)).rstrip('\n')
    open(md, 'w').write(s + '\n' + '\n'.join(ROWS) + '\n'); print('painted', len(ROWS))
