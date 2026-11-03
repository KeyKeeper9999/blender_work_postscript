"""Painted textures for the v2 corridors and the apartments.
Real CC0 photos (ambientCG / Poly Haven / cgbookcase previews) give the grain; colour, wear and
everything with a shape (paint edges, tiles, doors, wallpaper, carpets, labels) is drawn here.
Walls are painted floor-to-ceiling: one 256x256 texture = 4 m of wall x 2.6 m height.
usage: python3 paint_interior.py [corridor] [apartment]"""
import os, sys, math, random
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import paint_textures as PT
OUT, FONT = PT.OUT, PT.FONT
FONTR = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
ROWS = []
WW, WH, OV = 256, 256, 32

# ------------------------------------------------------------------ basics
def A(im): return np.asarray(im.convert('RGB')).astype(float)
def I(a): return Image.fromarray(np.clip(a, 0, 255).astype('uint8'))
def save(a, name, note):
    im = a if isinstance(a, Image.Image) else I(a)
    PT.q15(im).save(os.path.join(OUT, name + '.png')); ROWS.append(f'| {name}.png | {im.size[0]}x{im.size[1]} | {note} |')
def saveA(rgb, alpha, name, note): save(PT.rgba(rgb, alpha), name, note)
def photo(key, w, h, cell=128): return A(PT.tile(PT.src(key).resize((cell, cell), Image.BOX), w, h))
def tint(a, rgb, amt=1.0, contrast=1.0):
    lum = a.mean(axis=2, keepdims=True); m = lum.mean() + 1e-6
    t = ((lum / m - 1) * contrast + 1) * np.array(rgb, float)
    return a * (1 - amt) + t * amt
def nz(w, h, cell, seed): return PT.noise(w, h, cell, seed)
def col_noise(w, step, seed):
    r = np.random.RandomState(seed); k = w // step + 2; v = r.rand(k)
    return np.interp(np.arange(w) / step, np.arange(k), v)
def seam(a, w=WW, o=OV):
    t = np.linspace(0, 1, o)[None, :, None]; out = a[:, :w].copy()
    out[:, :o] = a[:, w:w + o] * (1 - t) + a[:, :o] * t; return out
def mimg(m): return Image.fromarray((np.clip(m, 0, 1) * 255).astype('uint8'))
def dilate(m, k=3): return np.asarray(mimg(m).filter(ImageFilter.MaxFilter(k))).astype(float) / 255
def blur(m, r): return np.asarray(mimg(m).filter(ImageFilter.GaussianBlur(r))).astype(float) / 255
def zpx(z): return WH * (1 - z / 2.6)
def scribble(d, x0, x1, y, R, col, step=(2, 6)):
    x = x0
    while x < x1 - 2:
        w = R.randint(*step); d.line([(x, y), (min(x + w, x1), y + R.choice((0, 0, 1)))], fill=col); x += w + R.randint(1, 3)

# ------------------------------------------------------------------ walls
def compose_wall(lower, upper, edge_z, seed, band=None, band_w=3.0, wobble=1.2, drips=5, chips=0.0, under=None,
                 plinth=None, plinth_z=.1, scuffs=.5, dust=.5, peel=0.0, deep=None, grime=.15):
    """lower/upper: (WH, WW+OV, 3) fills. Returns seamless (WH, WW, 3)."""
    W, H = WW + OV, WH; R = random.Random(seed); yy = np.arange(H)[:, None].astype(float)
    wob = (col_noise(W, 9, seed) - .5) * 2 * wobble + (col_noise(W, 3, seed + 1) - .5) * .8
    wob[WW:] = wob[:OV]
    edge = zpx(edge_z) + wob
    low = yy > edge[None, :]
    out = np.where(low[..., None], lower, upper)
    if band is not None:
        top = edge - band_w + (col_noise(W, 5, seed + 2) - .5) * 1.2
        m = (yy > top[None, :]) & ~low; out[m] = tint(lower, band)[m]
    for k in range(drips):                                   # paint runs below the edge
        x = R.randrange(WW); L = R.uniform(4, 20); y0 = int(edge[x]) + 1
        for y in range(y0, min(H, int(y0 + L))):
            f = .82 + .18 * (y - y0) / L
            for xx in (x, x + WW) if x < OV else (x,): out[y, xx] *= f
    if peel > 0 and under is not None:                       # big peeled areas show the older paint
        n = nz(W, H, 22, seed + 3) * .7 + nz(W, H, 5, seed + 4) * .3; n[:, WW:] = n[:, :OV]
        m = (n > 1 - peel) & low; rim = (dilate(m.astype(float), 3) > .5) & ~m
        out[m] = under[m]; out[rim] *= .55
        if deep is not None:
            m2 = m & (nz(W, H, 9, seed + 5) > .62); out[m2] = deep[m2]
            out[(dilate(m2.astype(float), 3) > .5) & ~m2 & m] *= .7
    if chips > 0 and under is not None:                      # small chips
        n = nz(W, H, 3, seed + 6); n[:, WW:] = n[:, :OV]
        m = (n > 1 - chips * .035) & low & (yy > edge[None, :] + 3)
        rim = (dilate(m.astype(float), 3) > .5) & ~m
        out[m] = (deep if deep is not None and R.random() < .3 else under)[m]; out[rim] *= .7
    if plinth is not None:
        pz = zpx(plinth_z) + wob * .4; m = yy > pz[None, :]; out[m] = tint(lower, plinth)[m]
    sc = Image.new('L', (W, H), 0); d = ImageDraw.Draw(sc)       # shoe and bag scuffs
    for k in range(int(28 * scuffs)):
        x = R.uniform(0, WW); y = R.uniform(zpx(.75), zpx(.08)); w = R.uniform(6, 34); h = R.uniform(1.5, 4)
        for xo in (0, WW) if x < OV else (0,): d.ellipse([x + xo - w / 2, y - h / 2, x + xo + w / 2, y + h / 2], fill=int(R.uniform(60, 160)))
    s = blur(np.asarray(sc).astype(float) / 255, 1.5); out *= (1 - .45 * s)[..., None]
    g = np.clip((yy - zpx(.6)) / (H - zpx(.6)), 0, 1); out *= (1 - grime * g)[..., None]
    t = np.clip(1 - yy / 16, 0, 1); out *= (1 - dust * .3 * t)[..., None]
    return seam(out)

def paint_fill(key, rgb, cell=128, contrast=1.0, streaks=.1, seed=0):
    a = tint(photo(key, WW + OV, WH, cell), rgb, contrast=contrast)
    if streaks: a *= (1 - streaks / 2 + streaks * col_noise(WW + OV, 4, seed))[None, :, None]
    a[:, WW:] = a[:, :OV]; return a

def wall_variants(name, n, **kw):
    for i in range(n):
        f = kw.copy(); s = f.pop('seed', 0) + 17 * i
        lower, upper = f.pop('lower')(s), f.pop('upper')(s)
        under = f.pop('under', None); deep = f.pop('deep', None)
        save(compose_wall(lower, upper, seed=s, under=under(s) if under else None, deep=deep(s) if deep else None, **f),
             f'{name}_{"ABC"[i]}', 'painted wall 4 m x 2.6 m: CC0 plaster/paint photo grain + drawn edge, drips, chips, scuffs')

# ------------------------------------------------------------------ wallpaper
def wrap(fn, x, y, w, h):
    for dx in (-w, 0, w):
        for dy in (-h, 0, h): fn(x + dx, y + dy)
def pattern(kind, base, ink, ink2, seed, w=WW, h=WH):
    im = Image.new('RGB', (w, h), base); d = ImageDraw.Draw(im); R = random.Random(seed)
    if kind == 'damask':
        def m(x, y):
            d.polygon([(x, y - 22), (x + 11, y), (x, y + 22), (x - 11, y)], outline=ink)
            d.polygon([(x, y - 9), (x + 5, y), (x, y + 9), (x - 5, y)], fill=ink2)
            for s in (-1, 1): d.arc([x + s * 9 - 5, y - 18, x + s * 9 + 5, y - 6], 0, 360, fill=ink)
            d.line([(x, y - 30), (x, y - 25)], fill=ink); d.line([(x, y + 25), (x, y + 30)], fill=ink)
        for j in range(h // 64):
            for i in range(w // 32): wrap(m, i * 32 + 16 + (16 if j % 2 else 0), j * 64 + 32, w, h)
    elif kind == 'flowers':
        def m(x, y):
            for k in range(5):
                a = k * 2 * math.pi / 5 + .3; d.point((x + 1.6 * math.cos(a), y + 1.6 * math.sin(a)), fill=ink)
            d.point((x, y), fill=ink2); d.line([(x + 2, y + 3), (x + 4, y + 7)], fill=ink2)
        for j in range(h // 32):
            for i in range(w // 16): wrap(m, i * 16 + 8 + (8 if j % 2 else 0), j * 32 + 16, w, h)
    elif kind == 'stripes':
        for x in range(0, w, 16):
            d.rectangle([x, 0, x + 4, h], fill=ink); d.line([(x + 9, 0), (x + 9, h)], fill=ink2)
            for y in range(6, h, 16): d.point((x + 12, y), fill=ink)
    elif kind == 'geo':
        def m(x, y):
            d.ellipse([x - 10, y - 10, x + 10, y + 10], outline=ink, width=2); d.ellipse([x - 4, y - 4, x + 4, y + 4], fill=ink2)
        for j in range(h // 32):
            for i in range(w // 32): wrap(m, i * 32 + 16 + (16 if j % 2 else 0), j * 32 + 16, w, h)
            d.line([(0, j * 32), (w, j * 32)], fill=ink2)
    elif kind == 'sprigs':
        def m(x, y):
            d.line([(x - 1, y + 3), (x + 1, y - 3)], fill=ink); d.point((x + 2, y - 1), fill=ink2); d.point((x - 2, y + 1), fill=ink2)
        for j in range(h // 16):
            for i in range(w // 16): wrap(m, i * 16 + 8 + (8 if j % 2 else 0), j * 16 + 8, w, h)
        for x in range(0, w, 32): d.line([(x + 16, 0), (x + 16, h)], fill=tuple(int(c * .96) for c in base))
    return A(im)

def paper_wall(name, kind, base, ink, ink2, seed, stripped=0.0, fade=.5, dirt=.5, note='wallpaper'):
    W, H = WW + OV, WH; R = random.Random(seed); yy = np.arange(H)[:, None].astype(float)
    pat = pattern(kind, base, ink, ink2, seed); pat = np.concatenate([pat, pat[:, :OV]], axis=1)
    g = photo('am__Paper001', W, H, 64); out = pat * (.86 + .14 * g.mean(2, keepdims=True) / g.mean())
    sh = [R.randint(-4, 4) for _ in range(8)]; br = [R.uniform(.94, 1.05) for _ in range(8)]
    for s in range(W // 32):
        x0, x1 = s * 32, min(W, s * 32 + 32); out[:, x0:x1] = np.roll(out[:, x0:x1], sh[s % 8], axis=0) * br[s % 8]
        out[:, x0] *= 1.07
        if s % 8 in (2, 5): out[int(zpx(2.6)):int(zpx(1.9)), x0:x1] *= 1 + fade * .12      # sun-faded strips
    out *= (1 - dirt * .25 * np.clip((yy - zpx(.5)) / (H - zpx(.5)), 0, 1))[..., None]
    out *= (1 - .25 * np.clip(1 - yy / 10, 0, 1))[..., None]
    if stripped > 0:
        n = nz(W, H, 26, seed + 9) * .7 + nz(W, H, 6, seed + 8) * .3; n[:, WW:] = n[:, :OV]
        m = n > 1 - stripped; rim = (dilate(m.astype(float), 3) > .5) & ~m
        news = newspaper_fill(W, H, seed); conc = tint(photo('am__Concrete034', W, H, 128), (150, 148, 140))
        under = np.where((nz(W, H, 12, seed + 7) > .55)[..., None], conc, news)
        out[m] = under[m]; out[rim] = out[rim] * .55 + np.array([196, 188, 160]) * .45
    save(seam(out), name, f'drawn {note} ({kind}) on ambientCG Paper001 grain, strips, fading, dirt')

def newspaper_fill(W, H, seed):
    R = random.Random(seed); im = Image.fromarray(np.clip(tint(photo('am__Paper001', W, H, 64), (196, 190, 172)), 0, 255).astype('uint8'))
    d = ImageDraw.Draw(im)
    for c in range(0, W, 22):
        for y in range(2, H, 3):
            if R.random() < .08: d.rectangle([c + 2, y, c + 19, y + R.randint(6, 14)], fill=(110, 108, 104)); continue
            scribble(d, c + 2, c + 20, y, R, (70, 70, 72), (2, 5))
    return A(im)

# ------------------------------------------------------------------ floors and ceilings
def tile_floor(name, cols, tp, seed, grain='am__Concrete015', grout=(70, 66, 60), pattern='checker', chip=.04, crack=.03, odd=None,
               size=256, note='drawn tiles'):
    R = random.Random(seed); g = photo(grain, size, size, 64); lum = g.mean(2, keepdims=True) / g.mean()
    out = np.zeros((size, size, 3)); n = size // tp
    for ty in range(n):
        for tx in range(n):
            if pattern == 'checker': c = cols[(tx + ty) % len(cols)]
            elif pattern == 'border': c = cols[1] if (tx % 8 in (0, 7) or ty % 8 in (0, 7)) else cols[0]
            else: c = cols[0]
            if odd and R.random() < .02: c = odd
            sl = np.s_[ty * tp:(ty + 1) * tp, tx * tp:(tx + 1) * tp]
            out[sl] = lum[sl] * np.array(c) * R.uniform(.9, 1.07)
    im = I(out); d = ImageDraw.Draw(im)
    for k in range(n * n):
        tx, ty = k % n, k // n; x0, y0 = tx * tp, ty * tp
        if R.random() < chip:
            cx, cy = R.choice([(x0, y0), (x0 + tp, y0), (x0, y0 + tp), (x0 + tp, y0 + tp)]); s = R.uniform(2, tp * .45)
            d.polygon([(cx, cy), (cx + (s if cx == x0 else -s), cy), (cx, cy + (s if cy == y0 else -s))], fill=tuple(int(v * .8) for v in grout))
        if R.random() < crack: d.line([(x0 + R.uniform(0, tp), y0), (x0 + R.uniform(0, tp), y0 + tp)], fill=tuple(int(v * .6) for v in grout))
    for v in range(0, size, tp): d.line([(v, 0), (v, size)], fill=grout); d.line([(0, v), (size, v)], fill=grout)
    a = A(im) * (.85 + .3 * nz(size, size, 24, seed))[..., None]
    save(a, name, note + f' ({tp}px tiles) on ambientCG {grain[4:]} grain')

def photo_floor(name, key, rgb, seed, contrast=1.0, strips=None, size=256, note=''):
    a = tint(photo(key, size, size, size // 2 if 'WoodFloor' not in key else size), rgb, contrast=contrast)
    a *= (.88 + .24 * nz(size, size, 32, seed))[..., None]
    if strips:
        for v in (0, size // 2): a[v:v + 2, :] = strips; a[:, v:v + 2] = strips
    save(a, name, note or f'{key.split("__")[1]} graded')

# ------------------------------------------------------------------ doors
def leaf_base(key, color, contrast=.7): return tint(photo(key, 64, 128, 64), color, contrast=contrast)
def wear(a, seed, handle=True, kick=.6, scratch=10):
    R = random.Random(seed); im = I(a); d = ImageDraw.Draw(im, 'RGBA')
    if handle: d.ellipse([46, 56, 62, 74], fill=(255, 240, 220, 14))
    for k in range(int(scratch)):
        x, y = R.uniform(4, 60), R.uniform(80, 124); d.line([(x, y), (x + R.uniform(-5, 5), y + R.uniform(-2, 2))], fill=(230, 220, 200, 70))
    d.rectangle([2, 112, 61, 126], fill=(30, 25, 20, int(60 * kick)))
    return A(im)
def leaf_quilt(color, seed, torn=False):
    a = leaf_base('am__Leather010', color, .5); yy, xx = np.mgrid[0:128, 0:64].astype(float)
    u = (xx - 6) / 17.3 + (yy - 6) / 23.2; v = (xx - 6) / 17.3 - (yy - 6) / 23.2
    du, dv = np.abs(u - np.round(u)), np.abs(v - np.round(v)); puff = np.minimum(du, dv) * 2
    field = (xx >= 6) & (xx < 58) & (yy >= 6) & (yy < 122)
    a[field] *= (.5 + .7 * np.sqrt(puff[field]))[..., None]
    welt = ~field & (xx >= 2) & (xx < 62) & (yy >= 2) & (yy < 126); a[welt] *= 1.12
    a[field & (du < .07) & (dv < .07)] = (196, 168, 96)
    for x in range(4, 62, 6): a[3, x] = a[124, x] = (180, 150, 85)
    for y in range(4, 126, 6): a[y, 3] = a[y, 60] = (180, 150, 85)
    if torn:
        im = I(a); d = ImageDraw.Draw(im); d.polygon([(14, 84), (30, 80), (34, 96), (22, 104), (12, 98)], fill=(200, 176, 92))
        d.line([(14, 84), (30, 80), (34, 96), (22, 104), (12, 98), (14, 84)], fill=(30, 20, 15)); a = A(im)
    return wear(a, seed)
def leaf_panel(color, under, seed):
    a = leaf_base('am__PaintedPlaster003', color, .6); im = I(a); d = ImageDraw.Draw(im, 'RGBA')
    for (x0, y0, x1, y1) in ((9, 9, 55, 60), (9, 68, 55, 119)):
        d.line([(x0, y1), (x0, y0), (x1, y0)], fill=(255, 255, 255, 60), width=2); d.line([(x0, y1), (x1, y1), (x1, y0)], fill=(0, 0, 0, 80), width=2)
        d.rectangle([x0 + 4, y0 + 4, x1 - 4, y1 - 4], outline=(0, 0, 0, 40))
    a = A(im); n = nz(64, 128, 3, seed); m = n > .96; a[m] = np.array(under) * (.8 + .3 * nz(64, 128, 2, seed + 1)[m][..., None])
    return wear(a, seed)
def leaf_veneer(color, seed):
    w = PT.src('am__Wood030').resize((64, 64), Image.BOX).transpose(Image.Transpose.ROTATE_90)
    a = tint(A(PT.tile(w, 64, 128)), color, contrast=1.1); a *= (1.08 - .16 * np.linspace(0, 1, 64))[None, :, None]
    m = (nz(64, 128, 4, seed) > .7) & (np.arange(128)[:, None] > 100); a[m] *= 1.25
    return wear(a, seed)
def leaf_steel(color, seed):
    a = leaf_base('am__PaintedMetal013', color, .8); im = I(a); d = ImageDraw.Draw(im, 'RGBA')
    d.rectangle([1, 1, 62, 126], outline=(0, 0, 0, 120), width=2)
    for x in (6, 57):
        for y in range(8, 124, 14): d.point((x, y), fill=(20, 20, 20, 255))
    a = A(im); yy = np.arange(128)[:, None]
    rust = (nz(64, 128, 2, seed) > .6) & (yy > 110); a[rust] = a[rust] * .4 + np.array([110, 55, 25]) * .6
    return wear(a, seed, kick=.9, scratch=18)
def leaf_burnt(seed):
    a = leaf_base('am__Leather010', (40, 34, 30), .5); n = nz(64, 128, 6, seed)
    a *= (.35 + .65 * np.clip(np.arange(128)[:, None] / 128 + n * .3, 0, 1))[..., None]
    m = nz(64, 128, 3, seed + 1) > .93; a[m] = (150, 130, 70)                     # foam bursting through
    return a
def leaf_lift(color, seed, slit=False, side=0):
    a = leaf_base('cg__PaintedMetal01', color, .6); im = I(a); d = ImageDraw.Draw(im, 'RGBA'); R = random.Random(seed)
    for k in range(5):
        x = R.uniform(8, 50); y = R.uniform(50, 90)
        pts = [(x + i * 2.5, y + R.uniform(-4, 4)) for i in range(R.randint(4, 8))]; d.line(pts, fill=(230, 230, 225, 110))
    if slit: d.rectangle([28, 34, 36, 70], fill=(10, 10, 12, 255)); d.rectangle([27, 33, 37, 71], outline=(150, 150, 145, 255))
    ex = 61 if side == 0 else 0; d.rectangle([ex, 0, ex + 2, 127], fill=(20, 20, 20, 255))
    d.rectangle([0, 116, 63, 127], fill=(40, 34, 28, 90))
    return A(im)
def door_atlas(name, leaves, note):
    at = np.zeros((128, 64 * len(leaves), 3))
    for i, a in enumerate(leaves): at[:, i * 64:(i + 1) * 64] = a
    save(at, name, note)

# ------------------------------------------------------------------ corridor props
def props_corridor():
    R = random.Random(11)
    # mailbox block 4 x 3 little doors
    a = tint(photo('am__PaintedMetal007', 128, 64, 64), (92, 108, 120), contrast=.6); im = I(a); d = ImageDraw.Draw(im, 'RGBA'); f = ImageFont.truetype(FONT, 7)
    for j in range(3):
        for i in range(4):
            x0, y0 = i * 32, j * 21
            d.rectangle([x0 + 1, y0 + 1, x0 + 30, y0 + 20], outline=(30, 34, 38, 255)); d.rectangle([x0 + 6, y0 + 3, x0 + 25, y0 + 5], fill=(12, 12, 14, 255))
            d.text((x0 + 8, y0 + 13), str(130 + j * 4 + i), font=f, fill=(225, 225, 220, 220), anchor='mm'); d.point((x0 + 25, y0 + 13), fill=(10, 10, 10, 255))
            if (i, j) in ((1, 0), (3, 2), (0, 1)):
                d.rectangle([x0 + 7, y0 + 1, x0 + 22, y0 + 4], fill=(225, 220, 205, 255)); d.line([(x0 + 9, y0 + 2), (x0 + 19, y0 + 2)], fill=(150, 60, 60, 255))
            if (i, j) == (2, 1): d.rectangle([x0 + 2, y0 + 2, x0 + 29, y0 + 19], fill=(8, 8, 10, 255)); d.rectangle([x0 + 8, y0 + 12, x0 + 22, y0 + 18], fill=(220, 215, 200, 255))
    save(A(im), 'T_IP_Mailbox', 'ambientCG PaintedMetal007 + drawn little doors, numbers, slots, letters sticking out')
    # electrical shield
    a = tint(photo('am__PaintedMetal006', 64, 128, 64), (128, 132, 128), contrast=.6); im = I(a); d = ImageDraw.Draw(im, 'RGBA')
    d.rectangle([1, 1, 62, 126], outline=(40, 40, 40, 255), width=2)
    d.polygon([(32, 18), (46, 42), (18, 42)], fill=(230, 196, 40, 255), outline=(20, 20, 20, 255)); d.line([(33, 24), (29, 33), (35, 33), (31, 40)], fill=(10, 10, 10, 255), width=2)
    d.text((32, 54), 'ЩЭ-7', font=ImageFont.truetype(FONT, 9), fill=(235, 235, 230, 230), anchor='mm')
    d.rectangle([52, 60, 58, 70], fill=(60, 60, 60, 255)); scribble(d, 10, 44, 92, R, (40, 40, 80, 255)); scribble(d, 10, 36, 96, R, (40, 40, 80, 255))
    a = A(im); m = (nz(64, 128, 2, 4) > .62) & (np.arange(128)[:, None] > 108); a[m] = a[m] * .4 + np.array([110, 55, 25]) * .6
    save(a, 'T_IP_Shield', 'ambientCG PaintedMetal006 + drawn warning sign, stencil, lock, scribbles, rust')
    # fire hose cabinet
    a = tint(photo('am__PaintedMetal004', 64, 64, 64), (150, 36, 30), contrast=.6); im = I(a); d = ImageDraw.Draw(im, 'RGBA')
    d.rectangle([8, 8, 56, 40], fill=(14, 12, 12, 255)); d.ellipse([16, 12, 48, 38], outline=(170, 150, 120, 255), width=3); d.ellipse([26, 20, 38, 30], outline=(170, 150, 120, 255), width=2)
    d.rectangle([7, 7, 57, 41], outline=(200, 200, 195, 255)); d.text((32, 52), 'ПК', font=ImageFont.truetype(FONT, 10), fill=(240, 240, 235, 255), anchor='mm')
    save(A(im), 'T_IP_FireCab', 'ambientCG PaintedMetal004 + drawn window, hose, label')
    # doormats: rag rug and rubber
    im = Image.new('RGB', (64, 32), (90, 70, 60)); d = ImageDraw.Draw(im); cols = [(150, 60, 50), (60, 80, 120), (170, 150, 90), (80, 110, 70), (120, 100, 140)]
    for k in range(10): d.ellipse([2 + k * 1.5, 2 + k * .7, 61 - k * 1.5, 29 - k * .7], outline=cols[k % 5], width=1)
    a = A(im) * (.75 + .3 * nz(64, 32, 2, 3))[..., None]; save(a, 'T_IP_MatRag', 'drawn braided rag rug')
    a = tint(photo('am__Rubber004', 64, 32, 64), (40, 40, 40), contrast=.5); im = I(a); d = ImageDraw.Draw(im)
    for y in range(4, 30, 6):
        for x in range(4, 62, 6): d.rectangle([x, y, x + 2, y + 2], fill=(8, 8, 8))
    save(A(im), 'T_IP_MatRubber', 'ambientCG Rubber004 + drawn holes')
    im = Image.new('RGBA', (64, 64), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    for k in range(16):
        ang = R.uniform(0, 2 * math.pi); r0 = R.uniform(4, 22); x, y = 32 + math.cos(ang) * r0, 34 + math.sin(ang) * r0 * .8
        L, W_ = R.uniform(7, 11), R.uniform(3, 5); c, s_ = math.cos(ang), math.sin(ang)
        pts = [(x + c * t * L - s_ * W_ * math.sin(t * math.pi), y + s_ * t * L + c * W_ * math.sin(t * math.pi)) for t in [i / 6 for i in range(7)]]
        pts += [(x + c * t * L + s_ * W_ * math.sin(t * math.pi), y + s_ * t * L - c * W_ * math.sin(t * math.pi)) for t in [i / 6 for i in range(6, -1, -1)]]
        g = R.randint(0, 30); d.polygon(pts, fill=(34 + g, 70 + g, 30 + g // 2, 255)); d.line([(x, y), (x + c * L, y + s_ * L)], fill=(80 + g, 120 + g, 60, 255))
    save(im, 'T_IP_Leaves', 'drawn rubber-plant leaves (alpha card)')

# ------------------------------------------------------------------ decals
def decals_interior():
    R = random.Random(5)
    yy, xx = np.mgrid[0:64, 0:64].astype(float)
    g = np.clip(1 - yy / 64, 0, 1) ** 1.8 * (.7 + .3 * nz(64, 64, 4, 1)); g = g[::-1]          # strong at v=0 (the wall)
    saveA(np.zeros((64, 64, 3)) + (38, 32, 26), g * .85, 'T_ID_EdgeGrime', 'drawn dirt gradient along the skirting (fake AO)')
    saveA(np.zeros((64, 64, 3)) + (30, 30, 30), g * .6, 'T_ID_CornerShadow', 'drawn ceiling-corner shadow gradient (fake AO)')
    a = PT.blob_mask(128, 128, 3, soft=8, rough=.4); rim = np.clip(1 - np.abs(a - .55) * 5, 0, 1)
    col = np.zeros((128, 128, 3)) + (150, 120, 70); col = col * (1 - rim[..., None] * .5)
    saveA(col, np.clip(a * .55 + rim * .35, 0, 1), 'T_ID_WaterStain', 'drawn water leak stain with tide-mark rims')
    sc = Image.new('L', (128, 64), 0); d = ImageDraw.Draw(sc)
    for k in range(26): x, y = R.uniform(10, 118), R.uniform(10, 54); w = R.uniform(8, 40); d.ellipse([x - w / 2, y - 2, x + w / 2, y + 2], fill=R.randint(80, 200))
    saveA(np.zeros((64, 128, 3)) + (30, 28, 26), blur(np.asarray(sc) / 255.0, 1.2) * .8, 'T_ID_Scuffs', 'drawn shoe and bag scuffs')
    im = Image.new('RGBA', (128, 128), (0, 0, 0, 0)); d = ImageDraw.Draw(im); f = ImageFont.truetype(FONT, 11); pen = (40, 44, 90, 200)
    d.text((8, 8), 'ЗДЕСЬ БЫЛ', font=f, fill=pen); d.line([(6, 22), (80, 24)], fill=pen)
    d.text((70, 40), '7', font=ImageFont.truetype(FONT, 22), fill=(120, 30, 30, 170))
    d.rectangle([10, 60, 30, 76], outline=(60, 60, 60, 190)); d.polygon([(8, 61), (20, 52), (32, 61)], outline=(60, 60, 60, 190)); d.ellipse([40, 54, 50, 64], outline=(150, 110, 30, 190))
    d.text((10, 92), '2-14-07', font=ImageFont.truetype(FONT, 9), fill=pen); scribble(d, 60, 120, 100, R, pen); scribble(d, 60, 110, 106, R, pen)
    for k in range(6): x = 70 + k * 8; d.line([(x, 70), (x + 4, 84)], fill=(20, 20, 20, 160))
    save(im, 'T_ID_Scribbles', 'drawn pen scribbles, kids drawing, phone number, tally marks')
    a = PT.blob_mask(64, 128, 7, soft=20, rough=.15) * (.5 + .5 * nz(64, 128, 3, 2))
    saveA(np.zeros((128, 64, 3)) + (34, 28, 22), a * .55, 'T_ID_PathWear', 'drawn worn traffic path')
    m = np.zeros((128, 128)); out = np.zeros((128, 128, 3)) + (120, 118, 112)
    for ty in range(8):
        for tx in range(8):
            if math.hypot(tx - 3.5, ty - 3.5) + R.uniform(-1, 1) < 3: m[ty * 16 + 1:ty * 16 + 15, tx * 16 + 1:tx * 16 + 15] = 1
    out *= (.75 + .4 * nz(128, 128, 4, 9))[..., None]; saveA(out, m, 'T_ID_MissingTiles', 'drawn cement bed where floor tiles fell out')
    im = Image.new('RGBA', (64, 128), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    for k in range(6):
        x = 20 if k % 2 else 40; y = 118 - k * 21
        d.ellipse([x - 6, y - 9, x + 6, y + 2], fill=(40, 30, 22, 150)); d.ellipse([x - 5, y + 4, x + 5, y + 11], fill=(40, 30, 22, 150))
    save(im, 'T_ID_Footprints', 'drawn muddy shoe prints')
    a = PT.blob_mask(128, 128, 13, soft=14, rough=.5) * (nz(128, 128, 3, 4) > .45)
    saveA(np.zeros((128, 128, 3)) + (24, 34, 24), blur(a, 1) * .85, 'T_ID_Mold', 'drawn black mould')
    rr = np.sqrt((xx - 32) ** 2 + ((yy - 40) * 1.3) ** 2) / 32
    saveA(np.zeros((64, 64, 3)) + (20, 18, 16), np.clip(1 - rr, 0, 1) ** 1.5 * .8, 'T_ID_Soot', 'drawn soot above a lamp / burn')
    im = Image.new('RGBA', (128, 128), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    for k in range(70):
        x, y, s = R.gauss(64, 22), R.gauss(64, 22), R.uniform(1, 5); c = R.choice([(170, 165, 150), (140, 136, 128), (90, 86, 80)])
        d.polygon([(x, y), (x + s, y + R.uniform(-1, 1)), (x + s * .6, y + s * .8)], fill=c + (255,))
    dust = PT.blob_mask(128, 128, 21, soft=30, rough=.3) * .5; ar = np.asarray(im).astype(float); ar[..., 3] = np.maximum(ar[..., 3], dust * 255)
    ar[..., :3] = np.where(ar[..., 3:4] > 0, np.where(ar[..., :3] > 0, ar[..., :3], 150), 0)
    save(Image.fromarray(ar.astype('uint8'), 'RGBA'), 'T_ID_Debris', 'drawn fallen plaster chunks and dust')
    im = Image.new('RGBA', (128, 128), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    for k in range(9):
        x, y, a_ = R.uniform(20, 108), R.uniform(20, 108), R.uniform(0, math.pi)
        c, s = math.cos(a_), math.sin(a_); w, h = 14, 10
        pts = [(x + c * dx - s * dy, y + s * dx + c * dy) for dx, dy in ((-w, -h), (w, -h), (w, h), (-w, h))]
        d.polygon(pts, fill=R.choice([(220, 215, 200, 255), (230, 200, 120, 255), (200, 210, 225, 255)]))
        d.line([pts[0], pts[1]], fill=(120, 40, 40, 255))
    save(im, 'T_ID_Flyers', 'drawn trampled flyers')
    im = Image.new('RGBA', (128, 128), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    def cr(x, y, a_, L, dep):
        for k in range(int(L)):
            a_ += R.uniform(-.4, .4); nx, ny = x + math.cos(a_) * 2.5, y + math.sin(a_) * 2.5; d.line([(x, y), (nx, ny)], fill=(40, 36, 32, 200)); x, y = nx, ny
            if dep < 2 and R.random() < .08: cr(x, y, a_ + R.choice((-1, 1)), L * .4, dep + 1)
    cr(4, 64, 0, 52, 0); save(im, 'T_ID_Crack', 'drawn plaster crack')

# ------------------------------------------------------------------ corridor themes
THEMES = {
    'Ochre': dict(lower=(150, 100, 48), band=(64, 40, 22), upper=(214, 200, 166), under=(96, 120, 90), plinth=(70, 44, 26), edge=1.55,
                  floor=('tiles', [(150, 66, 44), (206, 186, 146)], 16), ceil=(206, 196, 168),
                  doors=[('quilt', (92, 52, 30)), ('quilt', (36, 30, 28)), ('quilt', (104, 30, 28)), ('panel', (196, 186, 160)), ('veneer', (150, 100, 60)),
                         ('steel', (100, 64, 44)), ('quilt', (60, 70, 50), True), ('burnt',)], lift=(150, 140, 120)),
    'Mint':  dict(lower=(126, 170, 150), band=(52, 86, 76), upper=(216, 216, 200), under=(170, 160, 120), plinth=(62, 90, 82), edge=1.6,
                  floor=('terrazzo', (176, 172, 160)), ceil=(212, 214, 206),
                  doors=[('panel', (200, 204, 192)), ('panel', (150, 176, 172)), ('steel', (120, 128, 126)), ('quilt', (36, 30, 28)), ('veneer', (170, 130, 80)),
                         ('quilt', (92, 52, 30)), ('panel', (186, 170, 140)), ('steel', (100, 64, 44))], lift=(180, 186, 176)),
    'Panel80': dict(ceil=(214, 208, 192), floor=('parquetprint', (130, 82, 48)),
                  doors=[('veneer', (150, 96, 56)), ('veneer', (110, 70, 40)), ('quilt', (92, 52, 30)), ('quilt', (36, 30, 28)), ('steel', (100, 64, 44)),
                         ('panel', (190, 176, 150)), ('veneer', (176, 130, 80)), ('quilt', (104, 30, 28))], lift=(130, 100, 70)),
    'Decay': dict(lower=(96, 116, 132), band=(48, 58, 70), upper=(150, 150, 142), under=(90, 112, 80), deep=(128, 126, 118), plinth=(50, 56, 60), edge=1.5,
                  floor=('concrete', (122, 120, 112)), ceil=(128, 126, 118),
                  doors=[('steel', (90, 86, 80)), ('quilt', (50, 40, 34), True), ('panel', (130, 140, 140)), ('burnt',), ('quilt', (36, 30, 28)),
                         ('steel', (100, 64, 44)), ('panel', (120, 110, 90)), ('veneer', (110, 80, 50))], lift=(110, 112, 110)),
}
def leaf(spec, seed):
    k = spec[0]
    if k == 'quilt': return leaf_quilt(spec[1], seed, torn=len(spec) > 2)
    if k == 'panel': return leaf_panel(spec[1], (110, 90, 70), seed)
    if k == 'veneer': return leaf_veneer(spec[1], seed)
    if k == 'steel': return leaf_steel(spec[1], seed)
    return leaf_burnt(seed)
def corridors():
    for t, P in THEMES.items():
        s0 = sum(map(ord, t))
        if t == 'Panel80':
            def lower(s):          # lacquered chipboard wainscot, vertical joints every 0.6 m, cap at 1.0 m
                w = PT.src('am__Wood030').resize((64, 64), Image.BOX).transpose(Image.Transpose.ROTATE_90)
                a = tint(A(PT.tile(w, WW + OV, WH)), (112, 70, 40), contrast=1.1); a *= (.9 + .2 * col_noise(WW + OV, 6, s))[None, :, None]
                for x in range(0, WW + OV, 32): a[:, x:x + 1] *= .45; a[:, x + 1:x + 2] *= 1.15
                return a
            def upper(s): return np.concatenate([pattern('sprigs', (196, 178, 140), (150, 120, 80), (120, 140, 90), s) * .97, pattern('sprigs', (196, 178, 140), (150, 120, 80), (120, 140, 90), s)[:, :OV]], 1)
            wall_variants(f'T_IW_{t}', 3, lower=lower, upper=upper, edge_z=1.0, seed=s0, band=None, wobble=0, drips=0, scuffs=.7, dust=.4)
        else:
            lk = 'am__Plaster001' if t != 'Decay' else 'am__PaintedPlaster009'
            wall_variants(f'T_IW_{t}', 3, lower=lambda s, P=P, lk=lk: paint_fill(lk, P['lower'], seed=s, contrast=.35 if t != 'Decay' else .6),
                          upper=lambda s, P=P: paint_fill('am__Plaster001' if t != 'Decay' else 'am__PaintedPlaster016', P['upper'], streaks=0, seed=s, contrast=.6 if t != 'Decay' else .28),
                          under=lambda s, P=P: paint_fill('am__PaintedPlaster008', P['under'], seed=s + 1),
                          deep=(lambda s, P=P: paint_fill('am__Concrete034', P['deep'], seed=s + 2)) if 'deep' in P else None,
                          edge_z=P['edge'], seed=s0, band=P['band'], plinth=P['plinth'], chips={'Ochre': .7, 'Mint': .3}.get(t, 2.0),
                          peel=.38 if t == 'Decay' else 0.0, drips=6, scuffs=.6 if t != 'Decay' else .9, dust=.5 if t != 'Decay' else 1.0,
                          grime=.15 if t != 'Decay' else .35)
        fk = P['floor']
        if fk[0] == 'tiles': tile_floor(f'T_IF_{t}', fk[1], fk[2], s0, grain='am__Concrete015', grout=(96, 80, 64), note='drawn metlakh checker tiles')
        elif fk[0] == 'terrazzo': photo_floor(f'T_IF_{t}', 'am__Terrazzo005', fk[1], s0, contrast=.45, strips=(150, 120, 60), note='ambientCG Terrazzo005 graded + drawn brass dividers')
        elif fk[0] == 'parquetprint': photo_floor(f'T_IF_{t}', 'am__WoodFloor019', fk[1], s0, contrast=.7, note='ambientCG WoodFloor019 graded flat (printed linoleum)')
        else:
            a = tint(photo('po__concrete_floor_02', 256, 256, 128), fk[1]); a *= (.8 + .4 * nz(256, 256, 40, s0))[..., None]
            save(a, f'T_IF_{t}', 'Poly Haven concrete_floor_02 graded, large-scale stains')
        a = tint(photo('am__Plaster002', 128, 128, 128), P['ceil']) * (.9 + .2 * nz(128, 128, 20, s0))[..., None]
        if t == 'Decay': a *= (1 - .35 * (nz(128, 128, 16, s0 + 1) > .62))[..., None]
        save(a, f'T_IC_{t}', 'ambientCG Plaster002 graded')
        door_atlas(f'T_IDoors_{t}', [leaf(sp, s0 + i) for i, sp in enumerate(P['doors'])], f'drawn door leaves for {t}: CC0 leather/paint/wood grain + quilting, panels, rivets, wear')
        door_atlas(f'T_ILift_{t}', [leaf_lift(P['lift'], s0, slit=True, side=0), leaf_lift(P['lift'], s0 + 1, side=1)], 'cgbookcase PaintedMetal01 + drawn scratched tags, rubber edge, kick marks')
    props_corridor(); decals_interior()

# ------------------------------------------------------------------ apartment
def carpet(name, w, h, bg, c1, c2, c3, seed, note):
    R = random.Random(seed); im = Image.new('RGB', (w, h), bg); d = ImageDraw.Draw(im)
    q = Image.new('RGB', (w // 2, h // 2), bg); dq = ImageDraw.Draw(q); qw, qh = w // 2, h // 2
    dq.rectangle([0, 0, qw, qh], outline=c1, width=6); dq.rectangle([7, 7, qw, qh], outline=c3, width=1)
    for x in range(10, qw, 8): dq.polygon([(x, 2), (x + 3, 0), (x + 6, 2), (x + 3, 5)], fill=c2)
    for y in range(10, qh, 8): dq.polygon([(2, y), (0, y + 3), (2, y + 6), (5, y + 3)], fill=c2)
    for k, r in enumerate((qw * .55, qw * .42, qw * .28, qw * .14)):
        dq.polygon([(qw, qh - r * 1.6), (qw - r, qh), (qw, qh + r)], fill=(c1, c3, c2, bg)[k % 4])
    dq.polygon([(12, 12), (30, 12), (12, 30)], fill=c1); dq.polygon([(14, 14), (24, 14), (14, 24)], fill=c2)
    for k in range(10):
        x, y = R.uniform(14, qw - 18), R.uniform(14, qh - 18)
        if math.hypot((x - qw) / qw, (y - qh) / qh) > .65: dq.rectangle([x - 2, y - 2, x + 2, y + 2], fill=R.choice((c2, c3)))
    im.paste(q, (0, 0)); im.paste(q.transpose(Image.Transpose.FLIP_LEFT_RIGHT), (qw, 0))
    im.paste(q.transpose(Image.Transpose.FLIP_TOP_BOTTOM), (0, qh)); im.paste(q.transpose(Image.Transpose.ROTATE_180), (qw, qh))
    g = photo('am__Fabric026', w, h, 32); a = A(im) * (.8 + .2 * g.mean(2, keepdims=True) / g.mean()) * (.92 + .16 * nz(w, h, 6, seed))[..., None]
    save(a, name, note)

def apartment():
    R = random.Random(21)
    # walls
    paper_wall('T_AW_Damask', 'damask', (176, 168, 128), (130, 116, 76), (150, 90, 60), 31, note='wallpaper')
    paper_wall('T_AW_Flowers', 'flowers', (186, 176, 150), (150, 96, 80), (110, 120, 86), 32, note='wallpaper')
    paper_wall('T_AW_Stripes', 'stripes', (170, 176, 170), (140, 150, 150), (120, 100, 90), 33, note='wallpaper')
    paper_wall('T_AW_Geo', 'geo', (190, 170, 120), (160, 110, 50), (110, 70, 40), 34, note='wallpaper')
    paper_wall('T_AW_Stripped', 'damask', (150, 150, 120), (110, 104, 74), (130, 80, 60), 35, stripped=.45, dirt=.9, note='torn wallpaper over newspaper and concrete')
    wall_variants('T_AW_Kitchen', 1, lower=lambda s: paint_fill('am__Plaster001', (196, 180, 120), seed=s, contrast=.35), upper=lambda s: paint_fill('am__Plaster001', (216, 212, 196), streaks=0, seed=s),
                  under=lambda s: paint_fill('am__PaintedPlaster008', (140, 170, 160), seed=s), edge_z=1.5, seed=36, band=(120, 100, 60), plinth=(110, 90, 60), chips=.6, scuffs=.3)
    def tiles(s):
        a = tint(photo('am__Plaster001', WW + OV, WH, 64), (186, 206, 210), contrast=.4); xx = np.arange(WW + OV)[None, :]; yy = np.arange(WH)[:, None]
        tw, th = WW / 26, 14.8; g = ((xx % tw) < 1) | ((yy % th) < 1); a[np.broadcast_to(g, a.shape[:2])] = (120, 128, 128)
        a *= (.92 + .12 * nz(WW + OV, WH, 10, s))[..., None]; a[:, WW:] = a[:, :OV]; return a
    wall_variants('T_AW_Bath', 1, lower=tiles, upper=lambda s: paint_fill('am__Plaster001', (200, 206, 196), streaks=0, seed=s), edge_z=1.6, seed=37,
                  band=(150, 160, 160), band_w=2, wobble=0, drips=0, scuffs=.1, dust=.6)
    # floors
    photo_floor('T_AF_Parquet', 'am__WoodFloor034', (150, 100, 58), 41, contrast=.9, note='ambientCG WoodFloor034 herringbone graded')
    tile_floor('T_AF_KitchenLino', [(150, 140, 120), (110, 70, 50)], 16, 42, grain='po__linoleum_brown', grout=(90, 80, 70), chip=0, crack=0, note='drawn checker linoleum print')
    tile_floor('T_AF_BathTile', [(196, 192, 182), (172, 166, 154)], 8, 43, pattern='checker', grout=(110, 104, 96), note='drawn small bathroom floor tiles')
    a = tint(photo('am__Concrete020', 256, 256, 128), (130, 126, 118)); save(a * (.85 + .3 * nz(256, 256, 40, 44))[..., None], 'T_AF_Concrete', 'ambientCG Concrete020 graded')
    save(tint(photo('am__Plaster002', 128, 128, 128), (214, 210, 196)) * (.92 + .16 * nz(128, 128, 24, 45))[..., None], 'T_AC_Ceiling', 'ambientCG Plaster002 graded')
    # furniture materials
    for n, k, c, ct in (('T_A_VeneerDark', 'am__Wood030', (92, 54, 30), 1.2), ('T_A_VeneerLight', 'am__Wood030', (170, 126, 80), 1.0),
                        ('T_A_Sofa', 'am__Fabric026', (120, 40, 36), 1.0), ('T_A_Armchair', 'am__Fabric025', (110, 96, 60), 1.0),
                        ('T_A_Enamel', 'am__Plaster001', (226, 224, 214), .3), ('T_A_Sheet', 'am__Fabric019', (210, 210, 204), .8)):
        a = tint(photo(k, 64, 64, 64), c, contrast=ct)
        if n == 'T_A_Enamel': a[nz(64, 64, 2, 5) > .93] = (40, 36, 30)
        if n == 'T_A_Sheet':
            yy, xx = np.mgrid[0:64, 0:64]; a *= (.9 + .12 * np.sin(xx / 5 + 2 * np.sin(yy / 13)))[..., None]
        save(a, n, f'{k[4:]} graded')
    carpet('T_A_Carpet', 128, 256, (122, 26, 28), (28, 34, 70), (210, 180, 110), (220, 210, 190), 51, 'drawn ornamental wall carpet, ambientCG Fabric026 weave')
    carpet('T_A_Rug', 128, 128, (110, 70, 44), (60, 30, 24), (200, 170, 110), (180, 150, 120), 52, 'drawn floor rug, ambientCG Fabric026 weave')
    # curtains, tulle
    yy, xx = np.mgrid[0:128, 0:64].astype(float); a = np.zeros((128, 64, 3)) + (150, 96, 46)
    im = I(a); d = ImageDraw.Draw(im)
    for j in range(0, 128, 32):
        for i in range(0, 64, 32): x, y = i + 16 + (16 if (j // 32) % 2 else 0), j + 16; d.ellipse([x - 9, y - 9, x + 9, y + 9], outline=(200, 150, 70), width=3); d.ellipse([x - 3, y - 3, x + 3, y + 3], fill=(90, 50, 24))
    a = A(im) * (.72 + .3 * (.5 + .5 * np.sin(xx / 3.5)))[..., None]; save(a, 'T_A_Curtain', 'drawn 70s curtain with fold shading')
    im = Image.new('RGBA', (64, 64), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    for v in range(0, 64, 4): d.line([(v, 0), (v, 63)], fill=(235, 235, 230, 90)); d.line([(0, v), (63, v)], fill=(235, 235, 230, 90))
    for (x, y) in ((16, 16), (48, 48)): d.ellipse([x - 9, y - 9, x + 9, y + 9], outline=(240, 240, 235, 200), width=2); d.ellipse([x - 3, y - 3, x + 3, y + 3], fill=(240, 240, 235, 200))
    save(im, 'T_A_Tulle', 'drawn lace tulle (alpha)')
    news = newspaper_fill(128, 128, 61); im = I(news); d = ImageDraw.Draw(im); d.rectangle([0, 0, 127, 16], fill=(200, 194, 176))
    d.text((64, 9), 'ВЕЧЕРНИЙ ГОРОД', font=ImageFont.truetype(FONT, 10), fill=(30, 30, 30), anchor='mm'); save(A(im), 'T_A_Newspaper', 'drawn fictional newspaper on ambientCG Paper001')
    im = Image.new('RGB', (64, 32), (226, 220, 200)); d = ImageDraw.Draw(im)
    d.rectangle([48, 3, 60, 14], fill=(170, 50, 40)); [d.point((x, 2), fill=(226, 220, 200)) for x in range(48, 61, 2)]
    d.ellipse([38, 4, 52, 16], outline=(60, 60, 90)); scribble(d, 6, 40, 18, R, (40, 40, 90)); scribble(d, 6, 46, 22, R, (40, 40, 90)); scribble(d, 6, 30, 26, R, (40, 40, 90))
    d.rectangle([4, 4, 10, 10], outline=(150, 40, 40)); save(A(im), 'T_A_Envelope', 'drawn envelope with stamp and postmark')
    # fronts
    im = Image.new('RGB', (64, 128), (16, 14, 12)); d = ImageDraw.Draw(im)
    for y in (42, 84): d.line([(2, y), (61, y)], fill=(120, 110, 90), width=2)
    for k in range(5): d.ellipse([4 + k * 11, 10, 14 + k * 11, 38], fill=(220, 216, 206), outline=(40, 70, 140))
    for k in range(7): x = 6 + k * 8; d.polygon([(x, 80), (x + 5, 80), (x + 4, 60), (x + 1, 60)], fill=(170, 190, 200)); d.line([(x + 1, 62), (x + 1, 78)], fill=(240, 245, 250))
    for k in range(3): d.rectangle([8 + k * 18, 96, 22 + k * 18, 124], fill=(150 - k * 30, 60 + k * 20, 40), outline=(220, 200, 120))
    a = A(im); a[:, 20:24] = a[:, 20:24] * .5 + 110; a[:, 40:42] = a[:, 40:42] * .6 + 80; save(a, 'T_A_StenkaGlass', 'drawn display cabinet: plates, crystal, boxes behind glass')
    im = Image.new('RGB', (64, 64), (60, 40, 28)); d = ImageDraw.Draw(im)
    for row in range(3):
        x = 0
        while x < 64:
            w = R.randint(3, 7); c = R.choice([(120, 30, 30), (40, 60, 100), (150, 130, 80), (60, 90, 60), (180, 170, 150), (90, 60, 40)])
            top = row * 21 + R.randint(2, 6); d.rectangle([x, top, x + w - 1, row * 21 + 20], fill=c); d.line([(x + w // 2, top + 3), (x + w // 2, top + 9)], fill=(220, 200, 150)); x += w
    save(A(im), 'T_A_Books', 'drawn book spines')
    im = Image.new('RGB', (64, 64), (70, 46, 30)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([4, 6, 46, 50], 6, fill=(30, 36, 34)); d.polygon([(10, 12), (20, 12), (12, 40)], fill=(60, 70, 68))
    for y in (14, 26, 38): d.ellipse([50, y, 58, y + 8], fill=(190, 180, 160)); d.line([(54, y + 1), (54, y + 4)], fill=(30, 30, 30))
    d.rectangle([4, 54, 46, 58], fill=(160, 150, 130)); save(A(im) * (.9 + .2 * nz(64, 64, 8, 3))[..., None], 'T_A_TV', 'drawn CRT TV front')
    a = tint(photo('am__Plaster001', 64, 64, 64), (226, 224, 214), contrast=.3); im = I(a); d = ImageDraw.Draw(im)
    for x in (10, 24, 38, 52): d.ellipse([x - 4, 4, x + 4, 12], fill=(30, 30, 30))
    d.rectangle([6, 20, 58, 60], outline=(120, 120, 120)); d.rectangle([14, 30, 50, 52], fill=(20, 18, 16)); d.rectangle([10, 22, 54, 25], fill=(170, 170, 165))
    save(A(im), 'T_A_Stove', 'drawn gas stove front on ambientCG Plaster001')
    a = tint(photo('am__Plaster001', 64, 128, 64), (230, 228, 220), contrast=.3); a[100:] *= .95; im = I(a); d = ImageDraw.Draw(im)
    d.rectangle([2, 40, 7, 90], fill=(190, 190, 186)); d.line([(2, 40), (2, 90)], fill=(250, 250, 250)); d.rectangle([20, 10, 44, 16], fill=(180, 180, 175)); d.line([(0, 34), (63, 34)], fill=(160, 160, 155))
    for (x, y, c) in ((30, 50, (200, 40, 40)), (40, 62, (40, 120, 200)), (34, 70, (230, 200, 60))): d.rectangle([x, y, x + 3, y + 3], fill=c)
    d.rectangle([24, 76, 44, 90], fill=(240, 236, 210)); scribble(d, 26, 42, 80, R, (60, 60, 120)); save(A(im), 'T_A_Fridge', 'drawn fridge front with magnets and a note')
    im = Image.new('RGB', (64, 64), (220, 214, 200)); d = ImageDraw.Draw(im)
    for y in range(0, 64, 8):
        for x in range(0, 64, 8):
            if (x + y) // 8 % 2: d.rectangle([x, y, x + 7, y + 7], fill=(170, 50, 50))
    for (x, y) in ((12, 12), (44, 36)): d.ellipse([x - 4, y - 4, x + 4, y + 4], fill=(230, 160, 40)); d.line([(x, y - 4), (x + 2, y - 7)], fill=(60, 120, 40))
    save(A(im) * (.9 + .15 * nz(64, 64, 6, 7))[..., None], 'T_A_Oilcloth', 'drawn oilcloth')
    im = Image.new('RGB', (64, 64), (170, 130, 50)); d = ImageDraw.Draw(im)
    for y in range(6, 36): d.line([(6, y), (57, y)], fill=(int(220 - y * 2), int(150 - y), int(90 + y)))
    d.rectangle([6, 36, 57, 57], fill=(90, 110, 50)); d.polygon([(6, 36), (30, 30), (57, 36)], fill=(70, 80, 60))
    for x in (16, 22, 44): d.rectangle([x, 20, x + 2, 52], fill=(230, 226, 214)); d.point((x + 1, 30), fill=(20, 20, 20)); d.point((x, 40), fill=(20, 20, 20))
    d.rectangle([3, 3, 60, 60], outline=(120, 90, 30), width=3); save(A(im), 'T_A_Painting', 'drawn framed landscape painting')
    im = Image.new('RGB', (32, 32), (60, 40, 26)); d = ImageDraw.Draw(im); d.ellipse([2, 2, 29, 29], fill=(230, 226, 214))
    for k in range(12): a_ = k * math.pi / 6; d.point((16 + 11 * math.cos(a_), 16 + 11 * math.sin(a_)), fill=(20, 20, 20))
    d.line([(16, 16), (22, 12)], fill=(10, 10, 10)); d.line([(16, 16), (15, 6)], fill=(10, 10, 10)); save(A(im), 'T_A_Clock', 'drawn wall clock')
    im = Image.new('RGB', (64, 32), (226, 220, 206)); d = ImageDraw.Draw(im)
    for r in range(4):
        for c in range(7): d.rectangle([2 + c * 9, 4 + r * 7, 8 + c * 9, 9 + r * 7], outline=(90, 90, 90))
    d.rectangle([2 + 3 * 9, 4 + 2 * 7, 8 + 3 * 9, 9 + 2 * 7], fill=(190, 40, 40)); save(A(im), 'T_A_Calendar', 'drawn calendar grid (one day circled)')
    leaves = []
    a = leaf_base('am__PaintedPlaster003', (222, 216, 196), .4); im = I(a); d = ImageDraw.Draw(im)
    d.rectangle([12, 10, 52, 66], fill=(190, 200, 205)); [d.line([(x, 10), (x, 66)], fill=(220, 228, 232)) for x in range(12, 53, 3)]
    d.rectangle([11, 9, 53, 67], outline=(170, 160, 140), width=2); d.rectangle([12, 76, 52, 118], outline=(190, 182, 160), width=2)
    leaves.append(wear(A(im), 1)); a = leaf_base('am__PaintedPlaster003', (214, 206, 182), .4); leaves.append(wear(a, 2))
    door_atlas('T_A_Doors', leaves, 'drawn interior doors: frosted glass panel door and flush door')
    im = Image.new('RGB', (64, 32), (240, 240, 236)); a = A(im); xx = np.arange(64)[None, :]; yy = np.arange(32)[:, None]
    g = ((xx % 8) < 1) | ((yy % 8) < 1); a[np.broadcast_to(g, (32, 64))] = (140, 140, 136); a *= (.9 + .2 * nz(64, 32, 6, 9))[..., None]
    a[nz(64, 32, 4, 10) > .8] *= .8; save(a, 'T_A_Backsplash', 'drawn white kitchen tiles with grease')

# ------------------------------------------------------------------ lift cab (build_lift.py)
def pnz(w, h, cell, seed):
    """smooth noise that tiles (for box-mapped textures)"""
    a = np.random.RandomState(seed).rand(max(2, h // cell), max(2, w // cell))
    im = Image.fromarray((np.tile(a, (3, 3)) * 255).astype('uint8')).resize((w * 3, h * 3), Image.BICUBIC)
    return np.asarray(im).astype(float)[h:2 * h, w:2 * w] / 255
def lift():
    import lift_spec as LS
    FS = lambda s: ImageFont.truetype(FONT, s); FR = lambda s: ImageFont.truetype(FONTR, s)
    def wrapped(W, fn):
        for dx in (-W, 0, W): fn(dx)
    zp = lambda z: 256 * (1 - z / 2.56)                      # 256 px = 2.56 m from the floor
    PALE = (226, 202, 162)
    # walls: brown wood-grain laminate over the steel cab, 128 x 256 = 1.28 m x 2.56 m (box UV from the floor)
    grain = PT.src('am__Wood026').transpose(Image.ROTATE_90).resize((128, 128), Image.BOX)
    for tag, seed, words in (('A', 1, ['ВИТЯ', '1987']), ('B', 2, ['КОЛЯ', '86'])):
        r = random.Random(seed); a = tint(A(PT.tile(grain, 128, 256)), (102, 68, 42), contrast=.5)
        z = 2.56 * (1 - np.arange(256)[:, None] / 256.0)
        a *= (1 + .05 * np.sin(np.arange(128) / 128 * 2 * math.pi * 3 + seed))[None, :, None] * (.94 + .12 * pnz(128, 256, 16, seed))[..., None]
        a *= (1 - .2 * np.clip((z - 1.95) / .3, 0, 1))[..., None]                 # dust under the ceiling
        a *= (1 - .14 * np.clip((.5 - z) / .4, 0, 1))[..., None]                  # shoe grime above the kick plate
        a *= (1 - .06 * np.exp(-((z - 1.25) / .25) ** 2))[..., None]              # greasy band at hand height
        im = I(a); d = ImageDraw.Draw(im, 'RGBA')
        for k in range(30):                                                      # key scratches show the pale core
            x, y = r.uniform(0, 128), zp(r.uniform(.55, 1.95)); L = r.uniform(3, 20); ang = r.uniform(-.6, .6) + (math.pi / 2 if r.random() < .3 else 0)
            col = (*PALE, r.randint(30, 75))
            wrapped(128, lambda dx: d.line([(x + dx, y), (x + dx + L * math.cos(ang), y + L * math.sin(ang))], fill=col))
        for w_, (x, zz) in zip(words, ((10, 1.62), (74, 1.08))):                    # scratched words
            y = zp(zz)
            for i, ch in enumerate(w_):
                p = (x + i * 7 + r.uniform(-1, 1), y + r.uniform(-1.5, 1.5))
                wrapped(128, lambda dx: d.text((p[0] + dx, p[1]), ch, font=FR(8), fill=(*PALE, 85)))
        for k in range(2):                                                       # lighter burns: melted blisters
            x, y = r.uniform(8, 120), zp(r.uniform(1.0, 1.6))
            d.ellipse([x - 3, y - 2, x + 3, y + 3], fill=(30, 18, 10, 230)); d.ellipse([x - 1, y, x + 1, y + 1], fill=(96, 64, 36, 255))
        save(A(im), f'T_LC_Wall_{tag}', 'ambientCG Wood026 (rotated) graded + drawn key scratches, scratched words, lighter burns, grime')
    # floor: brown linoleum with cigarette burns, 128 px = 1.28 m (tiles)
    a = tint(photo('am__Rubber004', 128, 128, 128), (84, 70, 56), contrast=.4) * (.88 + .24 * pnz(128, 128, 16, 3))[..., None]
    im = I(a); d = ImageDraw.Draw(im, 'RGBA'); r = random.Random(4)
    for k in range(9):
        x, y = r.uniform(0, 128), r.uniform(0, 128)
        wrapped(128, lambda dx: (d.ellipse([x + dx - 4, y - 3, x + dx + 4, y + 3], fill=(44, 30, 18, 110)), d.ellipse([x + dx - 2, y - 1, x + dx + 2, y + 1], fill=(12, 9, 6, 235))))
    for k in range(3):
        x, y = r.uniform(0, 128), r.uniform(0, 128); wrapped(128, lambda dx: d.ellipse([x + dx - 3, y - 3, x + dx + 3, y + 2], fill=(46, 44, 42, 220)))
    for k in range(14):
        x, y = r.uniform(0, 128), r.uniform(0, 128); L = r.uniform(6, 24); ang = r.uniform(0, math.pi)
        wrapped(128, lambda dx: d.line([(x + dx, y), (x + dx + L * math.cos(ang), y + L * math.sin(ang))], fill=(130, 112, 90, 70)))
    save(A(im), 'T_LC_Floor', 'ambientCG Rubber004 graded to brown linoleum + drawn cigarette burns, gum, scratches')
    # ceiling: painted steel, rust stains, 64 px = 0.64 m
    a = tint(photo('am__PaintedMetal006', 64, 64, 64), (172, 168, 150), contrast=.4) * (.94 + .1 * pnz(64, 64, 8, 6))[..., None]
    save(a, 'T_LC_Ceiling', 'ambientCG PaintedMetal006 graded off-white (old rust patches stay as stains)')
    # plafond: frosted plexiglass with the bulb behind it and dead flies, used as emission
    yy, xx = np.mgrid[0:32, 0:64].astype(float); rr = np.hypot((xx - 30) / 32, (yy - 15) / 17)
    a = np.zeros((32, 64, 3)) + np.array([255, 236, 200]) * (1 - .5 * np.clip(rr, 0, 1) ** 1.3)[..., None]
    a *= (.93 + .1 * nz(64, 32, 4, 5))[..., None]; im = I(a); d = ImageDraw.Draw(im, 'RGBA'); r = random.Random(8)
    d.ellipse([22, 8, 38, 22], fill=(150, 104, 56, 46))
    for k in range(11):
        x, y = r.uniform(44, 61), r.uniform(18, 29)
        d.ellipse([x, y, x + 2, y + 1], fill=(28, 22, 16, 235)); d.point([(x - 1, y + 2), (x + 3, y + 2)], fill=(40, 34, 26, 200))
    d.rectangle([0, 0, 63, 31], outline=(130, 110, 86, 170)); d.rectangle([1, 1, 62, 30], outline=(170, 150, 120, 90))
    save(A(im), 'T_LC_Plafond', 'drawn frosted plexiglass shade: bulb glow, scorch, dead flies collected in one corner')
    # button plate (layout in lift_spec.py): A = normal cab, B = Trader cab (extra triangle button)
    for var, tag in (('Normal', 'A'), ('Trader', 'B')):
        r = random.Random(9); a = tint(photo('am__Metal009', 64, 256, 64), (150, 150, 146), contrast=.5)
        im = I(a); d = ImageDraw.Draw(im, 'RGBA'); LX, BX = LS.LABEL_X, LS.BTN_X; ink = (24, 24, 24, 255)
        d.rectangle([0, 0, 63, 255], outline=(60, 60, 58, 255)); d.rectangle([1, 1, 62, 254], outline=(205, 205, 200, 110))
        for sx, sy in ((5, 5), (58, 5), (5, 250), (58, 250)):
            d.ellipse([sx - 2, sy - 2, sx + 2, sy + 2], fill=(112, 112, 108, 255), outline=(50, 50, 48, 255)); d.line([(sx - 1, sy + 1), (sx + 1, sy - 1)], fill=(36, 36, 36, 255))
        for i in range(6):                                                      # intercom grille
            for j in range(3): d.ellipse([18 + i * 5, 11 + j * 5, 20 + i * 5, 13 + j * 5], fill=(16, 16, 16, 255))
        d.text((32, 35), 'ЛИФТ', font=FS(8), fill=ink, anchor='mm'); d.text((32, 45), '320 кг  4 чел', font=FR(6), fill=(40, 40, 40, 255), anchor='mm')
        for k, rn in enumerate(LS.rows(var)):
            y = LS.ROW0 + k * LS.PITCH
            d.rectangle([BX - 9, y - 7, BX + 9, y + 7], fill=(36, 36, 34, 255), outline=(196, 196, 190, 255))
            if rn.isdigit(): d.text((LX, y), rn, font=FS(10), fill=ink, anchor='mm')
            elif rn == 'stop': d.text((LX, y), 'СТОП', font=FS(6), fill=(170, 20, 16, 255), anchor='mm')
            elif rn == 'call':
                d.pieslice([LX - 4, y - 5, LX + 4, y + 4], 180, 360, fill=ink); d.rectangle([LX - 4, y - 1, LX + 4, y + 1], fill=ink)
                d.rectangle([LX - 6, y + 1, LX + 6, y + 2], fill=ink); d.ellipse([LX - 1, y + 3, LX + 1, y + 5], fill=ink)
            elif rn == 'tri': d.polygon([(LX, y - 5), (LX + 5, y + 4), (LX - 5, y + 4)], outline=ink)
            if rn in LS.BURNT:                                                  # soot rising from a melted button
                for rr_ in range(14, 5, -2): d.ellipse([BX - rr_ * .8, y - 2 - rr_ * .9, BX + rr_ * .8, y + rr_ * .5], fill=(12, 10, 8, 34))
        for k in range(26):
            x, y = r.uniform(4, 60), r.uniform(50, 250); L = r.uniform(3, 12); ang = r.uniform(-.8, .8)
            d.line([(x, y), (x + L * math.cos(ang), y + L * math.sin(ang))], fill=(235, 235, 230, 90))
        scribble(d, 8, 30, 52, r, (34, 36, 80, 200)); scribble(d, 44, 58, 230, r, (34, 36, 80, 200))
        save(A(im), f'T_LC_Panel_{tag}', 'ambientCG Metal009 graded + drawn engraved digits, button recesses, intercom grille, soot, scratches' + (', triangle button' if tag == 'B' else ''))
    # rules plate, 64 x 128 = 0.2 m x 0.4 m
    a = tint(photo('am__Paper001', 64, 128, 64), (206, 194, 160), contrast=.4) * (1 - .14 * (np.arange(128)[:, None] / 128))[..., None]
    im = I(a); d = ImageDraw.Draw(im, 'RGBA'); r = random.Random(10); ink = (40, 34, 26, 255); red = (150, 28, 22, 255)
    d.rectangle([0, 0, 63, 127], outline=(70, 60, 44, 255)); d.rectangle([3, 3, 60, 124], outline=(150, 28, 22, 170))
    d.text((32, 11), 'ПРАВИЛА', font=FS(8), fill=red, anchor='mm'); d.text((32, 20), 'пользования лифтом', font=FR(5), fill=ink, anchor='mm')
    for i in range(10):
        y = 28 + i * 7; d.text((6, y - 1), f'{i + 1}.', font=FR(5), fill=ink); scribble(d, 14, 57 - (i % 3) * 7, y + 2, r, (74, 66, 54, 255), step=(2, 5))
    d.ellipse([6, 103, 19, 116], outline=red, width=2); d.line([(8, 109), (17, 109)], fill=(70, 60, 50, 255), width=2); d.line([(8, 105), (17, 114)], fill=red, width=2)
    d.text((40, 105), 'Диспетчер', font=FR(5), fill=ink, anchor='mm'); d.text((40, 114), '2-14-07', font=FS(6), fill=ink, anchor='mm')
    for sx, sy in ((2, 2), (61, 2), (2, 125), (61, 125)): d.point((sx, sy), fill=(40, 40, 40, 255))
    for k in range(10):
        x, y = r.uniform(4, 60), r.uniform(24, 124); d.line([(x, y), (x + r.uniform(-8, 8), y + r.uniform(-3, 3))], fill=(250, 246, 236, 120))
    save(A(im), 'T_LC_Rules', 'ambientCG Paper001 graded + drawn "lift rules" plate, no-smoking sign, dispatcher phone, scratches')
    # door panels (cab side): painted steel, 64 x 256 = 0.64 m x 2.56 m from the floor (box UV)
    a = tint(photo('cg__PaintedMetal01', 64, 256, 64), (138, 136, 122), contrast=.55); z = 2.56 * (1 - np.arange(256)[:, None] / 256.0)
    a *= (1 - .25 * np.clip((.4 - z) / .35, 0, 1))[..., None] * (.95 + .1 * pnz(64, 256, 16, 12))[..., None]
    im = I(a); d = ImageDraw.Draw(im, 'RGBA'); r = random.Random(12)
    for k in range(30):
        x, y = r.uniform(0, 64), zp(r.uniform(.5, 1.9)); L = r.uniform(3, 14); ang = r.uniform(-.5, .5)
        wrapped(64, lambda dx: d.line([(x + dx, y), (x + dx + L * math.cos(ang), y + L * math.sin(ang))], fill=(224, 222, 210, 100)))
    for k in range(7):
        x, y = r.uniform(0, 64), zp(r.uniform(.06, .3)); wrapped(64, lambda dx: d.ellipse([x + dx - 5, y - 2, x + dx + 5, y + 2], fill=(30, 28, 24, 90)))
    x, y = r.uniform(10, 40), zp(1.35); scribble(d, x, x + 20, y, r, (24, 24, 30, 200)); scribble(d, x + 3, x + 16, y + 4, r, (24, 24, 30, 200))
    save(A(im), 'T_LC_DoorMetal', 'cgbookcase PaintedMetal01 graded + drawn scratches, kick marks, marker scribble')
    # ceiling vent: aluminium plate with figured cut-outs
    a = tint(photo('am__Metal009', 64, 32, 64), (160, 160, 156), contrast=.4); im = I(a); d = ImageDraw.Draw(im)
    for i in range(7):
        for j in range(2): cx, cy = 8 + i * 8, 10 + j * 12; d.polygon([(cx, cy - 4), (cx + 3, cy), (cx, cy + 4), (cx - 3, cy)], fill=(14, 14, 14))
    d.rectangle([0, 0, 63, 31], outline=(70, 70, 68)); a = A(im) * (.85 + .15 * nz(64, 32, 4, 13))[..., None]
    save(a, 'T_LC_Vent', 'ambientCG Metal009 graded + drawn figured vent cut-outs, dust')
    # decal atlas 2 x 2: marker tag | scratched heart / cigarette burns | advert sticker with tear-off strips
    im = Image.new('RGBA', (128, 128), (0, 0, 0, 0)); d = ImageDraw.Draw(im); r = random.Random(14); blue = (30, 34, 84, 215)
    d.text((32, 20), 'ЛЁХА', font=FS(13), fill=blue, anchor='mm'); d.line([(6, 32), (58, 29)], fill=blue, width=2)
    d.line([(16, 46), (44, 44)], fill=blue, width=2); d.polygon([(44, 39), (54, 44), (44, 49)], fill=blue)
    hp = [(96 + 16 * math.sin(t) ** 3, 30 - (13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t))) for t in [i / 24 * 2 * math.pi for i in range(25)]]
    d.line(hp, fill=(*PALE, 180)); d.line([(p[0] + .7, p[1] + .5) for p in hp], fill=(*PALE, 90)); d.text((96, 30), 'С+Т', font=FR(9), fill=(*PALE, 180), anchor='mm')
    d.line([(78, 52), (114, 50)], fill=(*PALE, 150))
    for k in range(7):
        x, y = r.uniform(10, 54), r.uniform(74, 118)
        d.ellipse([x - 4, y - 3, x + 4, y + 3], fill=(48, 32, 18, 120)); d.ellipse([x - 2, y - 1, x + 2, y + 1], fill=(10, 8, 6, 235))
    d.rectangle([70, 68, 122, 110], fill=(226, 222, 206, 255)); d.text((96, 78), 'ЗАМКИ', font=FS(8), fill=(30, 30, 30, 255), anchor='mm')
    d.text((96, 90), 'вскрытие', font=FR(6), fill=(30, 30, 30, 255), anchor='mm'); d.text((96, 100), '2-14-07', font=FS(6), fill=(150, 30, 24, 255), anchor='mm')
    for i in range(6):
        x = 71 + i * 8.5
        if i not in (1, 4): d.rectangle([x, 111, x + 7, 124], fill=(226, 222, 206, 255)); d.line([(x + 3.5, 113), (x + 3.5, 122)], fill=(40, 40, 40, 255))
    save(im, 'T_LC_Decals', 'drawn decal atlas: marker tag, scratched heart, cigarette burns, advert sticker with tear-off strips')

def finish():
    md = os.path.join(OUT, 'SOURCES.md'); s = open(md).read(); names = {r.split('|')[1].strip() for r in ROWS}
    s = '\n'.join(l for l in s.split('\n') if not (l.startswith('| ') and l.split('|')[1].strip() in names)).rstrip('\n')
    open(md, 'w').write(s + '\n' + '\n'.join(ROWS) + '\n'); print('painted', len(ROWS))

if __name__ == '__main__':
    which = sys.argv[1:] or ['corridor', 'apartment', 'lift']
    if 'corridor' in which: corridors()
    if 'apartment' in which: apartment()
    if 'lift' in which: lift()
    finish()
