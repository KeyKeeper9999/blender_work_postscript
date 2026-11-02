"""Panel-block floor generator (headless Blender 5.2 / bpy).
usage: python3 build_level.py <layout> <style> <out.blend>
layouts: corridor, corner, ring      styles: blue, green
Geometry is generated from the layout data below; textures come from ../textures."""
import sys, os, math, bpy, bmesh
from collections import defaultdict
from mathutils import Vector, Matrix
HERE = os.path.dirname(os.path.abspath(__file__))
LEVELS = os.path.dirname(HERE); REPO = os.path.dirname(LEVELS)
sys.path.insert(0, os.path.join(REPO, '.claude/skills/blender-keytools'))
import keytools as kt
LAYOUT, STYLE, OUT = sys.argv[-3], sys.argv[-2], os.path.abspath(sys.argv[-1])
TEXD = os.path.join(LEVELS, 'textures') + '/'
H, T, TE, TH = 2.6, 0.18, 0.35, 0.02
DW, DH, LW, LH = 0.9, 2.05, 0.8, 2.0
WARN = []

# ============================================================== styles
STYLES = {
 'blue': dict(
    zones={'corr': ('T_Baseboard_Dark', 'T_Wall_PaintSkyBlue', 'T_Wall_PaintSkyBlueStripe', 'T_Wall_ConcretePainted'),
           'hall': ('T_Baseboard_Dark', 'T_Wall_PaintSkyBlue', 'T_Wall_PaintSkyBlueStripe', 'T_Wall_ConcretePainted'),
           'tamb_wood': ('T_Baseboard_Dark', 'T_Wall_Vagonka_M', 'T_Wood_Frame_M', 'T_Wall_Wallpaper2_M'),
           'tamb_bare': ('T_Baseboard_Dark', 'T_Wall_ConcreteStained', 'T_Baseboard_Dark', 'T_Wall_ConcretePainted')},
    peel='T_Wall_PaintBlueGreyPeeling', stain='T_Wall_ConcreteStained',
    floors={'corr': 'T_Floor_Concrete', 'hall': 'T_Floor_ConcreteWorn', 'tamb_wood': 'T_Floor_ConcreteLight', 'tamb_bare': 'T_Floor_ConcreteWorn'},
    ceil='T_Ceiling_Concrete', ceil_stain='T_Ceiling_ConcreteStained', beam='T_Beam_Concrete', ceil_stain_zones=('tamb_bare',),
    doors={'derm_a': 'T_Door_DermatinBrown_M', 'derm_b': 'T_Door_DermatinBlack_M', 'derm_c': 'T_Door_DermatinBlack_M',
           'steel_a': 'T_Door_SteelGrey_M', 'steel_b': 'T_Door_SteelBrown_M', 'wood_a': 'T_Door_WoodBeige_M',
           'wood_b': 'T_Door_WoodBlue_M', 'wood_c': 'T_Door_WoodBrown_M', 'stair': 'T_Door_StairWood_M'},
    frame='T_Wood_Frame_M', suffix='_M', light=(.92, .93, 1.0),
    plates={'w': ((190, 188, 180), (25, 25, 25)), 'b': ((150, 128, 90), (40, 30, 15)), 'k': ((30, 30, 30), (200, 200, 195)), 'u': ((70, 82, 105), (220, 220, 220))}),
 'green': dict(
    zones={'corr': ('T_Baseboard_Paint', 'T_Wall_PaintGreen', 'T_Wall_PaintGreenStripe', 'T_Whitewash'),
           'hall': ('T_Baseboard_Paint', 'T_Wall_PaintGreen', 'T_Wall_PaintGreenStripe', 'T_Whitewash'),
           'tamb_wood': ('T_Baseboard_Paint', 'T_Wall_Vagonka', 'T_Wood_Frame', 'T_Wall_Wallpaper'),
           'tamb_bare': ('T_Baseboard_Paint', 'T_Wall_PaintBlue', 'T_Wall_PaintBlueStripe', 'T_Plaster_Stained')},
    peel='T_Wall_PaintPeeling', stain='T_Plaster_Stained',
    floors={'corr': 'T_Floor_MetlakhHex', 'hall': 'T_Floor_Terrazzo', 'tamb_wood': 'T_Floor_Linoleum', 'tamb_bare': 'T_Floor_WornTiles'},
    ceil='T_Ceiling', ceil_stain='T_Plaster_Stained', beam='T_Whitewash', ceil_stain_zones=('tamb_bare', 'tamb_wood'),
    doors={'derm_a': 'T_Door_DermatinBrown', 'derm_b': 'T_Door_DermatinBlack', 'derm_c': 'T_Door_DermatinRed',
           'steel_a': 'T_Door_SteelGrey', 'steel_b': 'T_Door_SteelBrown', 'wood_a': 'T_Door_WoodBeige',
           'wood_b': 'T_Door_WoodBlue', 'wood_c': 'T_Door_WoodBrown', 'stair': 'T_Door_StairWood'},
    frame='T_Wood_Frame', suffix='', light=(1, .82, .6),
    plates={'w': ((214, 208, 190), (20, 20, 20)), 'b': ((176, 136, 64), (40, 28, 10)), 'k': ((28, 28, 28), (210, 205, 190)), 'u': ((42, 62, 120), (225, 225, 225))}),
}
S = STYLES[STYLE]

# ============================================================== layouts
def door_runs(runs, base, types, special=None, dup=None, mats=None):
    """runs: [(wall, [u, ...])] -> door list (num, wall, u, type, mat)"""
    out, i = [], 0
    for wf, us in runs:
        for u in us:
            t = (special or {}).get(i, types[i % len(types)])
            num = None if t == 'wrong' else str(base + i)
            mat = (mats or {}).get(i)
            out.append([num, wf, u, t, mat]); i += 1
    if dup:
        for a, b in dup: out[b][0] = out[a][0]
    return [tuple(d) for d in out]

def layout_corridor():
    S_, N_, HW, HE, HN, EW, EE = ('y', 0, 1), ('y', 2, -1), ('x', 18, 1), ('x', 24, -1), ('y', 7, -1), ('x', 0, 1), ('x', 42, -1)
    D = [('133', N_, 2.0, 'derm_a', 'Mat_Olive'), ('134', S_, 2.0, 'wood_a', None), ('135', N_, 5.6, 'derm_b', 'Mat_Rubber'),
         ('136', S_, 5.6, 'steel_b', None), ('137', N_, 10.0, 'derm_c', 'Mat_Blue'), ('138', S_, 9.6, 'wood_c', None),
         ('139', N_, 13.0, 'steel_a', None), ('140', S_, 12.6, 'boarded', None), (None, N_, 16.2, 'wrong', None),
         ('141', S_, 15.6, 'derm_a', 'Mat_Olive'), ('142', S_, 19.6, 'steel_b', None), ('143', S_, 22.4, 'sealed', None),
         ('144', N_, 26.0, 'derm_b', 'Mat_Rubber'), ('145', S_, 25.6, 'wood_b', None), ('146', N_, 29.0, 'steel_a', None),
         ('147', S_, 28.6, 'derm_c', 'Mat_Blue'), ('148', N_, 32.0, 'derm_a', None), ('144', S_, 31.6, 'wood_c', None),
         ('149', N_, 36.6, 'wood_b', None), ('150', S_, 36.6, 'steel_b', 'Mat_Rubber'), ('151', N_, 40.0, 'wood_a', None),
         ('152', S_, 40.0, 'derm_a', 'Mat_Olive')]
    return dict(
        rooms=[(0, 0, 42, 2), (18, 2, 24, 7)],
        floors=[('TambourW', (0, 0, 8, 2), 'tamb_wood'), ('Corridor', (8, 0, 34, 2), 'corr'),
                ('TambourE', (34, 0, 42, 2), 'tamb_bare'), ('Hall', (18, 2, 24, 7), 'hall')],
        doors=D, stair=(HW, 4.6), lifts=(HN, 19.6, 22.0),
        windows=[(EW, 1.0, True), (EE, 1.0, False)],
        partitions=[('TambourW', 'x', 8, 0, 2, 'wood', 'hi', 1), ('TambourE', 'x', 34, 0, 2, 'grille', 'hi', -1)],
        beams=[(b - .15, 0, b + .15, 2) for b in (6, 12, 18, 24, 30, 36)] + [(18.15, 1.9, 23.85, 2.1)],
        lamps=[(3, 1, 'bulb', N_), (9, 1, 'broken', N_), (15, 1, 'plafond', N_), (27, 1, 'flicker', N_),
               (33, 1, 'dead', N_), (39, 1, 'bulb_dead', N_), (21, 4.5, 'plafond', None)],
        runs=[(N_, .4, 17.6), (N_, 24.4, 41.6)],
        panels=[(N_, 11.5, 'ElectricPanel', 0), (N_, 27.5, 'ElectricPanel', 20), (S_, 21.0, 'ElectricPanel', 110), (N_, 38.3, 'Chute_Hatch', 0)],
        firecabs=[(S_, 14.1)], mailboxes=(HE, 3.4), chute=((23.45, 6.45, 24, 7), ('x', 23.45, -1), 6.725),
        patches=[((11.0, 1.5, 12.4, 2.5), 'low'), ((16.8, -.5, 18.0, .5), 'low'), ((30.0, 1.5, 31.2, 2.5), 'low'), ((29.6, -.5, 31.2, 2.5), 'up')],
        ceil_stains=[(29.6, 0, 31.2, 2)],
        phantom_mats=[(N_, 35.2)],
        props=[('chair', 19.6, 4.2, 6), ('wardrobe', S_, 3.8), ('sled', S_, 4.72), ('runner', (.6, .6, 7.7, 1.4)),
               ('rolled', 7.75, .2), ('boots', 5.575, 1.75, 0), ('boxes', S_, 38.1), ('bucket', 41.6, 1.6),
               ('bags', [(23.05, 6.62, .24), (22.62, 6.74, .2)]), ('envelopes', [(23.4, 3.0, 15), (23.05, 3.6, -30), (23.55, 3.95, 70)])],
        spawn=(18.7, 4.6, -90))

def layout_corner():
    AS, AN, AE = ('y', 0, 1), ('y', 2, -1), ('x', 0, 1)
    HE_, HW_ = ('x', 30, -1), ('x', 24, 1)
    BW, BE, BN = ('x', 26, 1), ('x', 28, -1), ('y', 28, -1)
    types = ['derm_a', 'steel_a', 'wood_a', 'derm_b', 'steel_b', 'wood_b', 'derm_a', 'wood_c', 'steel_a', 'derm_b', 'wood_a', 'steel_b']
    D = door_runs([(AS, [2.2, 7.8, 11.2, 14.6, 18.0, 21.4]), (AN, [2.2, 4.6, 8.4, 11.8, 15.2, 18.6, 22.0]),
                   (BW, [8.0, 11.4, 14.8, 18.2, 23.6]), (BE, [7.4, 9.6, 13.0, 16.4, 19.8, 23.6, 26.4])], 61, types,
                  special={4: 'boarded', 16: 'wrong', 21: 'sealed'}, dup=[(9, 19)],
                  mats={0: 'Mat_Rubber', 3: 'Mat_Olive', 8: 'Mat_Blue', 12: 'Mat_Olive', 14: 'Mat_Rubber', 23: 'Mat_Olive', 24: 'Mat_Blue'})
    return dict(
        rooms=[(0, 0, 24, 2), (24, 0, 30, 6), (26, 6, 28, 28)],
        floors=[('TambourA', (0, 0, 6, 2), 'tamb_bare'), ('CorridorA', (6, 0, 24, 2), 'corr'), ('Hall', (24, 0, 30, 6), 'hall'),
                ('CorridorB', (26, 6, 28, 22), 'corr'), ('TambourB', (26, 22, 28, 28), 'tamb_wood')],
        doors=D, stair=(AS, 27.0), lifts=(HE_, 2.2, 4.6),
        windows=[(AE, 1.0, False), (BN, 27.0, True)],
        partitions=[('TambourA', 'x', 6, 0, 2, 'grille', 'hi', 1), ('TambourB', 'y', 22, 26, 28, 'wood', 'hi', -1)],
        beams=[(b - .15, 0, b + .15, 2) for b in (12, 18, 24)] + [(26, b - .15, 28, b + .15) for b in (6, 12, 18, 24)],
        lamps=[(3, 1, 'bulb_dead', AN), (9, 1, 'plafond', AN), (15, 1, 'broken', AN), (21, 1, 'flicker', AN), (27, 3, 'plafond', None),
               (27, 9, 'plafond', BW), (27, 15, 'dead', BW), (27, 20, 'plafond', BW), (27, 26, 'bulb', BW)],
        runs=[(AN, .4, 23.6), (BW, 6.4, 27.6)],
        panels=[(AN, 13.45, 'ElectricPanel', 0), (BW, 9.65, 'Chute_Hatch', 20), (BE, 17.3, 'ElectricPanel', 110)],
        firecabs=[(AS, 12.85), (BW, 16.5)], mailboxes=(HW_, 3.6), chute=((24, 5.45, 24.55, 6), ('x', 24.55, 1), 5.725),
        patches=[((12.9, 1.5, 14.0, 2.5), 'low'), ((25.5, 13.6, 26.5, 14.6), 'low'), ((26, 14.0, 28, 16.5), 'up'), ((8.5, -.5, 10.0, .5), 'low')],
        ceil_stains=[(15.5, 0, 17.5, 2), (26, 13, 28, 16)],
        phantom_mats=[(BE, 21.0)],
        props=[('chair', 28.0, 3.4, -84), ('boxes', AS, 4.3), ('sled', AS, 5.4), ('bucket', 5.3, 1.55), ('stool', .75, 1.1, 10),
               ('runner', (26.6, 22.4, 27.4, 27.5)), ('wardrobe', BW, 25.6), ('rolled', 26.25, 22.35), ('boots', 27.72, 23.6, 90),
               ('bags', [(24.85, 5.62, .22), (25.3, 5.75, .17)]), ('envelopes', [(24.6, 3.2, 20), (25.0, 3.9, -35), (24.45, 4.4, 80)])],
        spawn=(27.0, .7, 0))

def layout_ring():
    S_out, S_core, N_out, N_core = ('y', 0, 1), ('y', 2, -1), ('y', 16, -1), ('y', 14, 1)
    W_out, W_core, E_out, E_core = ('x', 0, 1), ('x', 2, -1), ('x', 20, -1), ('x', 18, 1)
    H_S, H_W, H_E = ('y', 10, 1), ('x', 7, 1), ('x', 13, -1)
    types = ['steel_a', 'derm_a', 'wood_b', 'derm_b', 'steel_b', 'wood_a', 'derm_a', 'steel_a', 'wood_c', 'derm_b']
    D = door_runs([(N_out, [2.6, 6.0, 9.4, 12.8, 16.2]), (N_core, [4.5, 15.5]), (E_out, [3.0, 6.6, 9.4, 12.6]),
                   (E_core, [3.3, 8.0, 12.7]), (S_core, [15.0, 11.5, 8.0, 4.5]), (W_core, [4.5, 11.5]), (W_out, [4.0, 11.0])], 205, types,
                  special={10: 'boarded', 19: 'wrong', 14: 'sealed'}, dup=[(0, 2)],
                  mats={1: 'Mat_Olive', 5: 'Mat_Rubber', 9: 'Mat_Blue', 13: 'Mat_Olive', 17: 'Mat_Rubber', 21: 'Mat_Olive'})
    return dict(
        rooms=[(0, 0, 20, 2), (0, 14, 20, 16), (0, 2, 2, 14), (18, 2, 20, 14), (7, 10, 13, 14)],
        floors=[('South', (0, 0, 20, 2), 'corr'), ('North', (0, 14, 20, 16), 'corr'), ('WestA', (0, 2, 2, 8), 'tamb_bare'),
                ('WestB', (0, 8, 2, 14), 'corr'), ('EastA', (18, 2, 20, 5), 'corr'), ('TambourE', (18, 5, 20, 11), 'tamb_wood'),
                ('EastB', (18, 11, 20, 14), 'corr'), ('Hall', (7, 10, 13, 14), 'hall')],
        doors=D, stair=(H_W, 12.0), lifts=(H_S, 8.6, 11.0),
        windows=[(S_out, 3.0, False), (S_out, 10.0, True), (S_out, 17.0, False)],
        partitions=[('TambourE_S', 'y', 5, 18, 20, 'wood', 'hi', -1), ('TambourE_N', 'y', 11, 18, 20, 'wood', 'lo', 1),
                    ('GrilleW', 'y', 8, 0, 2, 'grille', 'lo', 1)],
        beams=[(b - .15, 0, b + .15, 2) for b in (4.2, 10.0, 15.4)] + [(6.85, 14, 7.15, 16), (12.85, 14, 13.15, 16), (7.15, 13.9, 12.85, 14.1)]
              + [(0, b - .15, 2, b + .15) for b in (4.0, 11.5)],
        lamps=[(6.2, 1, 'plafond', S_core), (13.3, 1, 'dead', S_core), (17.5, 1, 'flicker', S_core),
               (3.5, 15, 'plafond', N_out), (10, 15, 'plafond', N_out), (16.5, 15, 'broken', N_out),
               (1, 5.5, 'bulb_dead', W_out), (1, 10.0, 'plafond', W_out),
               (19, 3.4, 'dead', E_out), (19, 8.0, 'bulb', E_out), (19, 12.8, 'plafond', E_out), (10, 12.2, 'plafond', None)],
        runs=[(S_core, 2.4, 17.6), (N_out, .4, 19.6), (W_out, .4, 15.6), (E_out, .4, 15.6)],
        panels=[(S_core, 6.2, 'ElectricPanel', 0), (N_out, 7.7, 'ElectricPanel', 20), (E_core, 10.0, 'ElectricPanel', 110), (S_out, 13.5, 'Chute_Hatch', 0)],
        firecabs=[(S_out, 6.5), (W_out, 12.8)], mailboxes=(H_E, 12.0), chute=((12.45, 10, 13, 10.55), ('y', 10.55, 1), 12.725),
        patches=[((5.5, 1.5, 7.0, 2.5), 'low'), ((-.5, 9.0, .5, 10.5), 'low'), ((14.0, 13.5, 16.5, 16.5), 'up'), ((19.5, 2.0, 20.5, 4.0), 'low')],
        ceil_stains=[(13, 14, 17, 16), (0, 9, 2, 11)],
        phantom_mats=[(S_core, 13.3)],
        props=[('chair', 9.8, 12.7, 180), ('stool', 10.0, .55, 0), ('runner', (18.6, 5.3, 19.4, 10.7)), ('wardrobe', E_core, 6.2),
               ('sled', E_out, 7.9), ('rolled', 19.8, 10.7), ('boots', 19.72, 9.4, 90), ('boxes', W_out, 6.0), ('bucket', 1.6, 7.35),
               ('bags', [(12.2, 10.85, .2)]), ('envelopes', [(12.6, 11.8, 20), (12.2, 12.5, -40), (12.65, 12.9, 75)])],
        spawn=(7.7, 12.0, -90))

L = {'corridor': layout_corridor, 'corner': layout_corner, 'ring': layout_ring}[LAYOUT]()

# ============================================================== scene + materials
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
bpy.ops.wm.save_as_mainfile(filepath=OUT)
ROOTNAME = os.path.splitext(os.path.basename(OUT))[0]
root = bpy.data.collections.new(ROOTNAME); sc.collection.children.link(root)
_cols = {}
def col(n):
    if n not in _cols:
        c = bpy.data.collections.new(n); root.children.link(c); _cols[n] = c
    return _cols[n]

# number plate atlas for this layout
from PIL import Image, ImageDraw, ImageFont
nums = []
for d in L['doors']:
    if d[0] and d[0] not in nums: nums.append(d[0])
PLATE_IDX = {n: i for i, n in enumerate(nums)}
atlas = Image.new('RGB', (256, 128)); dr = ImageDraw.Draw(atlas)
fnt = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 12)
for i, n in enumerate(nums):
    bg, fg = S['plates']['wbku'[i % 4]]; x, y = (i % 8) * 32, (i // 8) * 16
    dr.rectangle((x, y, x + 31, y + 15), fill=bg); dr.rectangle((x, y, x + 31, y + 15), outline=tuple(int(c * .6) for c in bg))
    dr.text((x + 16, y + 8), n, font=fnt, fill=fg, anchor='mm')
PLATE_TEX = 'T_NumberPlates_%s' % ROOTNAME
atlas.save(TEXD + PLATE_TEX + '.png')
def plate_cell(n):
    i = PLATE_IDX[n]; cx, cy = i % 8, i // 8
    return (cx / 8, 1 - (cy + 1) / 8, (cx + 1) / 8, 1 - cy / 8)

_mats, MS = {}, {}
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
        w, h = im.size; MS[name] = tile or (w / 64.0, h / 64.0)
    if explicit: MS[name] = None
    if emit:
        b.inputs['Emission Color'].default_value = (*emit[0], 1); b.inputs['Emission Strength'].default_value = emit[1]
    _mats[name] = m; return m
def tm(tex, tile=None): return mat('M_' + tex[2:], tex, tile=tile)
def pm(name):   # prop texture in the current style (muted copy when it exists)
    base = 'T_' + name; m = base + S['suffix']
    return tm(m if os.path.exists(TEXD + m + '.png') else base)

LC = S['light']
M = dict(
    handle=mat('M_Metal_Dark', color=(.10, .09, .08), rough=.6), brass=mat('M_Metal_Brass', color=(.45, .33, .12), rough=.5),
    plate=mat('M_NumberPlates', PLATE_TEX, explicit=True),
    number=mat('M_Decal_FloorNumber', 'T_FloorNumber_7', alpha=True, explicit=True),
    sign=mat('M_Sign_LiftBroken', 'T_Sign_LiftBroken', explicit=True),
    lamp=mat('M_Lamp_Glow', color=LC, emit=(LC, 6.0)), deadglass=mat('M_Lamp_DeadGlass', color=(.55, .52, .46), rough=.4),
    plastic=mat('M_Plastic_Dark', color=(.05, .05, .05), rough=.7), wire=mat('M_Wire', color=(.07, .07, .07), rough=.8),
    btn=mat('M_Button_Red', color=(.8, .05, .03), emit=((1, .08, .03), 3.0)), btn_dead=mat('M_Button_Dead', color=(.25, .04, .03), rough=.6),
    btn_cream=mat('M_Plastic_Cream', color=(.75, .70, .58), rough=.6), btn_burnt=mat('M_Plastic_Burnt', color=(.03, .025, .02), rough=.9),
    cablight=mat('M_LiftCab_Light', color=(1, .95, .85), emit=((1, .93, .8), 4.0)),
    night=mat('M_Glass_Night', color=(.01, .015, .03), emit=((.02, .03, .06), 1.0), rough=.1),
    wired=mat('M_Glass_Wired', color=(.05, .07, .06), rough=.25), jar=mat('M_Glass_Jar', color=(.35, .42, .38), rough=.2),
    pot=mat('M_Clay_Pot', color=(.42, .18, .09)), stem=mat('M_Plant_Dead', color=(.18, .14, .08)), steel=mat('M_Metal_Grey', color=(.3, .3, .3), rough=.5),
)

# ============================================================== geometry helpers
def F(wf):
    if callable(wf): return wf
    a, c, s = wf
    return (lambda u, z, w: (u, c + s * w, z)) if a == 'y' else (lambda u, z, w: (c + s * w, u, z))
def nrm(wf): a, c, s = wf; return Vector((0, s, 0)) if a == 'y' else Vector((s, 0, 0))
def mirrored(f):
    o = Vector(f(0, 0, 0)); ud = Vector(f(1, 0, 0)) - o; n = Vector(f(0, 0, 1)) - o
    return ud.dot((-n).cross(Vector((0, 0, 1)))) < 0
OCC = defaultdict(list)
def occupy(wf, u0, u1, z0, z1, name):
    for a0, a1, b0, b1, n in OCC[wf]:
        if u0 < a1 - 1e-4 and a0 < u1 - 1e-4 and z0 < b1 - 1e-4 and b0 < z1 - 1e-4: WARN.append(f'overlap on {wf}: {name} x {n}')
    OCC[wf].append((u0, u1, z0, z1, name))
def prism(bm, f, pts, a0, a1, mi=0):
    f = F(f); a = [bm.verts.new(f(p, q, a0)) for p, q in pts]; b = [bm.verts.new(f(p, q, a1)) for p, q in pts]
    n = len(pts); caps = [bm.faces.new(a), bm.faces.new(b[::-1])]
    sides = [bm.faces.new((a[i], a[(i + 1) % n], b[(i + 1) % n], b[i])) for i in range(n)]
    for x in caps + sides: x.material_index = mi
    if n > 4:
        for x in caps: x.normal_update()
        bmesh.ops.triangulate(bm, faces=caps, ngon_method='EAR_CLIP')
    return caps
def lbox(bm, f, u0, u1, z0, z1, w0, w1, mi=0): return prism(bm, f, [(u0, z0), (u1, z0), (u1, z1), (u0, z1)], w0, w1, mi)[1]
def wbox(bm, lo, hi, mi=0): return lbox(bm, lambda u, z, w: (u, w, z), lo[0], hi[0], lo[2], hi[2], lo[1], hi[1], mi)
def fbox(bm, f, a, b, mi=0):   # box between two points given in wall coords (u,z,w)
    p, q = Vector(F(f)(*a)), Vector(F(f)(*b))
    return wbox(bm, [min(p[i], q[i]) for i in range(3)], [max(p[i], q[i]) for i in range(3)], mi)
def hexa(bm, fp, r0, r1, r2, mi=0):
    vs = [bm.verts.new(fp(a, b, c)) for c in r2 for b in r1 for a in r0]
    idx = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]
    for q in idx: bm.faces.new([vs[i] for i in q]).material_index = mi
def cyl(bm, p0, p1, r, seg=8, mi=0, r1=None):
    p0, p1 = Vector(p0), Vector(p1); d = p1 - p0
    res = bmesh.ops.create_cone(bm, cap_ends=True, segments=seg, radius1=r, radius2=r if r1 is None else r1, depth=d.length)
    mtx = Matrix.Translation((p0 + p1) / 2) @ Vector((0, 0, 1)).rotation_difference(d.normalized()).to_matrix().to_4x4()
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
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:]); bm.faces.index_update(); seen = set()
    for f0 in bm.faces:
        if f0.index in seen: continue
        isl, stack = [], [f0]; seen.add(f0.index)
        while stack:
            f = stack.pop(); isl.append(f)
            for e in f.edges:
                for g in e.link_faces:
                    if g.index not in seen: seen.add(g.index); stack.append(g)
        if any(len(e.link_faces) != 2 for f in isl for e in f.edges): continue
        c = sum((v.co for f in isl for v in f.verts), Vector()) / sum(len(f.verts) for f in isl); vol = 0.0
        for f in isl:
            v0 = f.verts[0].co - c
            for i in range(1, len(f.verts) - 1): vol += v0.dot((f.verts[i].co - c).cross(f.verts[i + 1].co - c))
        if vol < 0: bmesh.ops.reverse_faces(bm, faces=isl)
def make(name, bm, cname, mats, origin=None, loc=None, rot=None, recalc=True):
    if origin is not None:
        origin = Vector(origin)
        for v in bm.verts: v.co -= origin
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
    md = o.modifiers.new('cut', 'BOOLEAN'); md.operation = 'DIFFERENCE'; md.operand_type = 'COLLECTION'; md.collection = tmp; md.solver = 'EXACT'
    me = bpy.data.meshes.new_from_object(o.evaluated_get(bpy.context.evaluated_depsgraph_get()))
    old = o.data; o.modifiers.remove(md); o.data = me; me.name = o.name
    if not me.materials:
        for m in old.materials: me.materials.append(m)
    bpy.data.meshes.remove(old)
    for x in list(tmp.objects): bpy.data.meshes.remove(x.data)
    bpy.data.collections.remove(tmp)
def bisect(bm, planes):
    for co, no in planes: bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=co, plane_no=no)
def cutter_l(wf, u0, u1, z0, z1, depth):
    bm = bmesh.new(); lbox(bm, wf, u0, u1, z0, z1, -depth, .2); return bm
def ang_into_room(wf, ang):
    """rotation about Z for something hinged at its low-u edge, opening into the room by |ang| degrees"""
    if not ang: return 0.0
    d0 = Vector(F(wf)(1, 0, 0)) - Vector(F(wf)(0, 0, 0)); n = nrm(wf)
    for a in (abs(ang), -abs(ang)):
        if (Matrix.Rotation(math.radians(a), 3, 'Z') @ d0).dot(n) > 0: return math.radians(a)

# ============================================================== zones
ZONES = [(z, r) for _, r, z in L['floors']]
def zone_at(x, y):
    for tol in (.002, .45):
        for z, r in ZONES:
            if r[0] - tol <= x <= r[2] + tol and r[1] - tol <= y <= r[3] + tol: return z
    return 'corr'
def in_rect(x, y, r, tol=0.0): return r[0] - tol < x < r[2] + tol and r[1] - tol < y < r[3] + tol

# ============================================================== shell
rooms = L['rooms']
X0 = min(r[0] for r in rooms); Y0_ = min(r[1] for r in rooms); X1 = max(r[2] for r in rooms); Y1 = max(r[3] for r in rooms)
WMAT_T = sorted({t for z in S['zones'].values() for t in z} | {S['peel'], S['stain']})
WMAT = [tm(t) for t in WMAT_T]; WIDX = {t: i for i, t in enumerate(WMAT_T)}
bm = bmesh.new(); wbox(bm, (X0 - TE, Y0_ - TE, 0), (X1 + TE, Y1 + TE, H))
walls = make('Walls', bm, 'Shell', WMAT)
cuts = []
def ext(r):   # extend a room into a neighbour it opens onto, so cutters overlap instead of touching
    x0, y0, x1, y1 = r; e = .03
    for q in rooms:
        if q is r: continue
        if abs(q[3] - y0) < 1e-6 and q[0] - 1e-6 <= x0 and x1 <= q[2] + 1e-6: y0 -= e
        if abs(q[1] - y1) < 1e-6 and q[0] - 1e-6 <= x0 and x1 <= q[2] + 1e-6: y1 += e
        if abs(q[2] - x0) < 1e-6 and q[1] - 1e-6 <= y0 and y1 <= q[3] + 1e-6: x0 -= e
        if abs(q[0] - x1) < 1e-6 and q[1] - 1e-6 <= y0 and y1 <= q[3] + 1e-6: x1 += e
    return x0, y0, x1, y1
for r in rooms:
    x0, y0, x1, y1 = ext(r); c = bmesh.new(); wbox(c, (x0, y0, -.5), (x1, y1, H + .5)); cuts.append(c)
def dsize(t): return (0.7, 2.25) if t == 'wrong' else (DW, DH)
for num, wf, u, t, _ in L['doors']:
    wd, h = dsize(t); cuts.append(cutter_l(wf, u - wd / 2, u + wd / 2, TH, h, .3))
swf, su = L['stair']; cuts.append(cutter_l(swf, su - .6, su + .6, TH, 2.1, .3))
lwf, ua, ub = L['lifts']
for u in (ua, ub):
    cuts.append(cutter_l(lwf, u - LW / 2, u + LW / 2, TH, LH, T + .2))
    c = bmesh.new(); fbox(c, lwf, (u - .6, -.5, -T), (u + .6, H + .5, -T - 1.6)); cuts.append(c)
for wf, uc, _ in L['windows']: cuts.append(cutter_l(wf, uc - .6, uc + .6, .9, 2.2, TE + .5))
boolean_cut(walls, cuts)
bm = bmesh.new(); bm.from_mesh(walls.data)
RX = {v for r in rooms for v in (r[0], r[2])}; RY = {v for r in rooms for v in (r[1], r[3])}   # wall planes: never bisect along them
xs = sorted(({v for _, r, _ in L['floors'] for v in (r[0], r[2])} | {v for r, _ in L['patches'] for v in (r[0], r[2])}) - RX)
ys = sorted(({v for _, r, _ in L['floors'] for v in (r[1], r[3])} | {v for r, _ in L['patches'] for v in (r[1], r[3])}) - RY)
bisect(bm, [((0, 0, z), (0, 0, 1)) for z in (.1, 1.5, 1.53)] + [((x, 0, 0), (1, 0, 0)) for x in xs] + [((0, y, 0), (0, 1, 0)) for y in ys])
def wall_tex(c):
    x, y, z = c; zone = zone_at(x, y); base, low, stripe, up = S['zones'][zone]
    if z < .1: return base
    if z < 1.5:
        if zone in ('corr', 'hall') and any(in_rect(x, y, r) and b == 'low' for r, b in L['patches']): return S['peel']
        return low
    if z < 1.53: return stripe
    if any(in_rect(x, y, r) and b == 'up' for r, b in L['patches']): return S['stain']
    return up
bmesh.ops.dissolve_degenerate(bm, dist=1e-5, edges=bm.edges[:])
bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=1e-5)
hidden = [fc for fc in bm.faces if (fc.normal.z < -.99 and abs(fc.calc_center_median().z) < 1e-4) or (fc.normal.z > .99 and abs(fc.calc_center_median().z - H) < 1e-4)]
bmesh.ops.delete(bm, geom=hidden, context='FACES')        # under the floor / above the ceiling: never seen
for fc in bm.faces: fc.material_index = WIDX[wall_tex(fc.calc_center_median())]
bm.to_mesh(walls.data); bm.free()

for name, (x0, y0, x1, y1), z in L['floors']:
    bm = bmesh.new(); bm.faces.new([bm.verts.new(p) for p in ((x0, y0, 0), (x1, y0, 0), (x1, y1, 0), (x0, y1, 0))])
    tile = (1.6, 1.6) if S['floors'][z] == 'T_Floor_MetlakhHex' else None
    make('Floor_' + name, bm, 'Shell', [tm(S['floors'][z], tile)], recalc=False)
bm = bmesh.new()
for name, (x0, y0, x1, y1), z in L['floors']:
    bm.faces.new([bm.verts.new(p) for p in ((x0, y0, H), (x0, y1, H), (x1, y1, H), (x1, y0, H))])
bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=1e-5)
bisect(bm, [((r[0], 0, 0), (1, 0, 0)) for r in L['ceil_stains']] + [((r[2], 0, 0), (1, 0, 0)) for r in L['ceil_stains']]
       + [((0, r[1], 0), (0, 1, 0)) for r in L['ceil_stains']] + [((0, r[3], 0), (0, 1, 0)) for r in L['ceil_stains']])
bmesh.ops.dissolve_degenerate(bm, dist=1e-5, edges=bm.edges[:]); bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=1e-5)
for fc in bm.faces:
    c = fc.calc_center_median()
    fc.material_index = 1 if (any(in_rect(c.x, c.y, r) for r in L['ceil_stains']) or zone_at(c.x, c.y) in S['ceil_stain_zones']) else 0
make('Ceiling', bm, 'Shell', [tm(S['ceil']), tm(S['ceil_stain'])], recalc=False)
bm = bmesh.new()
for x0, y0, x1, y1 in L['beams']: wbox(bm, (x0, y0, 2.32), (x1, y1, H))
make('Ceiling_Beams', bm, 'Shell', [tm(S['beam'])])

# ============================================================== doors
def frame(bm, wf, u0, u1, h, a=0.07, d=0.015, mi=0):
    prism(bm, wf, [(u0 - a, 0), (u0, 0), (u0, h), (u1, h), (u1, 0), (u1 + a, 0), (u1 + a, h + a), (u0 - a, h + a)], 0, d, mi)
seen_names = set()
for num, wf, u, t, matname in L['doors']:
    f = F(wf); wd, h = dsize(t); u0, u1 = u - wd / 2, u + wd / 2
    tag = num or 'X'
    while 'Door_' + tag in seen_names: tag += '_B'
    seen_names.add('Door_' + tag)
    zone = zone_at(*Vector(f(u, 1, .3))[:2])
    if t == 'wrong': leaftex = S['zones'][zone][1]
    elif t in ('boarded', 'sealed'): leaftex = S['doors']['wood_c']
    else: leaftex = S['doors'][t]
    mats = [tm(leaftex), M['handle'], M['plate'], M['brass'], pm('Paper'), tm(S['zones'][zone][3])]
    bm = bmesh.new(); lbox(bm, wf, u0 + .004, u1 - .004, TH, h - .004, -.11, -.07, 0)
    if t == 'wrong':
        bisect(bm, [((0, 0, 1.5), (0, 0, 1))])
        for fc in bm.faces: fc.material_index = 0 if fc.calc_center_median().z < 1.5 else 5
        occupy(wf, u0, u1, 0, h, 'Door_' + tag)
    else:
        steel, wood = t.startswith('steel'), t.startswith('wood') or t in ('sealed', 'boarded')
        if t != 'boarded':
            if wood: cyl(bm, f(u1 - .08, 1.0, -.07), f(u1 - .08, 1.0, -.03), .025, 8, 3)
            else: lbox(bm, wf, u1 - .17, u1 - .05, .98, 1.01, -.07, -.02, 1)
            if t != 'sealed': lbox(bm, wf, u1 - .10, u1 - .07, 1.12, 1.17, -.07, -.066, 1)
            if steel: lbox(bm, wf, u1 - .10, u1 - .07, .80, .85, -.07, -.066, 1)
            cyl(bm, f(u, 1.55, -.07), f(u, 1.55, -.055), .012, 6, 1)
        pf = lbox(bm, wf, u - .06, u + .06, 1.72, 1.78, -.07, -.066, 2); set_uv(bm, pf, wf, u - .06, u + .06, 1.72, 1.78, plate_cell(num))
        if t == 'sealed': lbox(bm, wf, u1 - .26, u1 - .02, 1.06, 1.13, -.07, -.068, 4)
        occupy(wf, u0 - .2, u1 + .07, 0, h + .07, 'Door_' + tag)
    make('Door_' + tag, bm, 'Doors', mats, origin=f(u0 + .004, TH, -.09))
    if t == 'wrong': continue
    bm = bmesh.new(); frame(bm, wf, u0, u1, h)
    if t == 'boarded':
        for zc in (.55, 1.15, 1.8): lbox(bm, wf, u0 - .07, u1 + .07, zc - .06, zc + .06, .015, .035, 1)
    make('Door_%s_Frame' % tag, bm, 'Doors', [tm(S['frame']), pm('Planks')], origin=f(u, 0, 0))
    bm = bmesh.new(); ub_ = u0 - .15
    lbox(bm, wf, ub_ - .035, ub_ + .035, 1.42, 1.52, 0, .025, 0); cyl(bm, f(ub_, 1.47, .025), f(ub_, 1.47, .032), .01, 6, 1)
    make('Door_%s_Bell' % tag, bm, 'Doors', [M['btn_cream'], M['plastic']], origin=f(ub_, 1.42, 0))
    if matname:
        bm = bmesh.new(); lbox(bm, wf, u - .3, u + .3, 0, .012, .05, .45)
        make('Door_%s_Mat' % tag, bm, 'Props', [pm(matname)], origin=f(u, 0, .25))
for i, (wf, u) in enumerate(L['phantom_mats']):
    bm = bmesh.new(); lbox(bm, wf, u - .3, u + .3, 0, .012, .05, .45)
    make('Doormat_NoDoor' + ('_%d' % i if i else ''), bm, 'Props', [pm('Mat_Olive')], origin=F(wf)(u, 0, .25))
# stair door
f = F(swf); u0, u1 = su - .6, su + .6
for side, (a0, a1, hinge) in (('L', (u0 + .004, su - .002, u0 + .004)), ('R', (su + .002, u1 - .004, u1 - .004))):
    bm = bmesh.new(); lbox(bm, swf, a0, a1, TH, 2.1 - .004, -.11, -.07, 0); lbox(bm, swf, a0 + .1, a1 - .1, 1.15, 1.95, -.07, -.066, 1)
    if side == 'R': lbox(bm, swf, a0 + .05, a0 + .17, .98, 1.01, -.07, -.02, 2)
    make('Door_Stair_' + side, bm, 'Doors', [tm(S['doors']['stair']), M['wired'], M['handle']], origin=f(hinge, TH, -.09))
bm = bmesh.new(); frame(bm, swf, u0, u1, 2.1, a=.08); make('Door_Stair_Frame', bm, 'Doors', [tm(S['frame'])], origin=f(su, 0, 0))
occupy(swf, u0 - .08, u1 + .08, 0, 2.18, 'Door_Stair')

# ============================================================== lifts
f = F(lwf)
for name, u in (('A', ua), ('B', ub)):
    u0, u1 = u - LW / 2, u + LW / 2; broken = name == 'B'
    lm = pm('Metal_Grille') if broken else pm('LiftDoor_Metal')
    bm = bmesh.new(); frame(bm, lwf, u0, u1, LH, a=.1, d=.04); make('Lift%s_Frame' % name, bm, 'Lift', [lm], origin=f(u, 0, 0))
    occupy(lwf, u0 - .1, u1 + .1, 0, LH + .1, 'Lift' + name)
    gap = .03 if broken else .001; sh = .026 if broken else 0
    for side, (a0, a1) in (('L', (u0 + .004 - sh, u - gap)), ('R', (u + gap, u1 - .004 + sh))):
        bm = bmesh.new(); lbox(bm, lwf, a0, a1, TH, LH - .004, -.10, -.07)
        make('Lift%s_Door_%s' % (name, side), bm, 'Lift', [lm], origin=f((a0 + a1) / 2, TH, -.085))
    bu = u1 + .3
    bm = bmesh.new(); lbox(bm, lwf, bu - .04, bu + .04, 1.12, 1.26, 0, .02, 0); lbox(bm, lwf, bu - .015, bu + .015, 1.17, 1.20, .02, .03, 1)
    make('Lift%s_CallButton' % name, bm, 'Lift', [M['handle'], M['btn_dead'] if broken else M['btn']], origin=f(bu, 1.12, 0))
    occupy(lwf, bu - .04, bu + .04, 1.12, 1.26, 'Lift%s_Button' % name)
    if not broken:
        bm = bmesh.new(); fbox(bm, lwf, (u - .6, -.05, -T), (u + .6, 2.25, -T - 1.1))
        cab = make('LiftA_Cab', bm, 'Lift', [pm('LiftCab_Wood'), pm('LiftCab_Floor'), pm('LiftDoor_Metal')], origin=f(u, 0, -T))
        c1 = bmesh.new(); fbox(c1, lwf, (u - .55, 0, -T - .05), (u + .55, 2.2, -T - 1.05))
        c2 = bmesh.new(); fbox(c2, lwf, (u - .4, 0, -T + .1), (u + .4, LH, -T - .2)); boolean_cut(cab, [c1, c2])
        bm = bmesh.new(); bm.from_mesh(cab.data)
        for fc in bm.faces:
            nz, zc = fc.normal.z, fc.calc_center_median().z
            fc.material_index = 1 if (nz > .9 and abs(zc) < .01) else (2 if (nz < -.9 and abs(zc - 2.2) < .01) else 0)
        bm.to_mesh(cab.data); bm.free()
        bm = bmesh.new(); fbox(bm, lwf, (u - .15, 2.18, -T - .4), (u + .15, 2.2, -T - .7))
        make('LiftA_CabLight', bm, 'Lift', [M['cablight']], origin=f(u, 2.2, -T - .55))
        bm = bmesh.new(); fbox(bm, lwf, (u + .53, .95, -T - .15), (u + .55, 1.5, -T - .35), 0)
        for i in range(5):
            for j in range(2):
                z = 1.0 + i * .09; w = -T - .2 - j * .07
                fbox(bm, lwf, (u + .52, z, w), (u + .53, z + .05, w - .035), 2 if (i, j) == (3, 1) else 1)
        make('LiftA_CabPanel', bm, 'Lift', [M['steel'], M['btn_cream'], M['btn_burnt']], origin=f(u + .55, .95, -T - .25))
        LIGHTS_EXTRA = [('Light_LiftA_Cab', f(u, 2.05, -T - .55), 12, (1, .93, .8)), ('Light_LiftA_Button', f(bu, 1.19, .08), .3, (1, .1, .05))]
    else:
        bm = bmesh.new(); fbox(bm, lwf, (u - .6, -2.5, -T), (u + .6, H + 1, -T - 1.5))
        shf = make('LiftB_Shaft', bm, 'Lift', [pm('Shaft_Concrete')], origin=f(u, 0, -T))
        c1 = bmesh.new(); fbox(c1, lwf, (u - .55, -2.45, -T + .01), (u + .55, H + .95, -T - 1.45)); boolean_cut(shf, [c1])
        bm = bmesh.new()
        for du in (-.2, 0, .2): cyl(bm, f(u + du, -2.45, -T - .8), f(u + du, H + .95, -T - .8), .012, 6)
        make('LiftB_Cables', bm, 'Lift', [M['wire']], origin=f(u, -2.45, -T - .8))
        bm = bmesh.new(); fs = lbox(bm, lwf, bu + .12, bu + .4, 1.40, 1.68, 0, .002); set_uv(bm, fs, lwf, bu + .12, bu + .4, 1.40, 1.68)
        make('LiftB_Sign', bm, 'Lift', [M['sign']], origin=f(bu + .26, 1.4, 0)); occupy(lwf, bu + .12, bu + .4, 1.4, 1.68, 'LiftB_Sign')
dm = (ua + ub) / 2
bm = bmesh.new(); fs = lbox(bm, lwf, dm - .2, dm + .2, 1.62, 2.02, 0, .002); set_uv(bm, fs, lwf, dm - .2, dm + .2, 1.62, 2.02)
make('Decal_FloorNumber', bm, 'Props', [M['number']], origin=f(dm, 1.62, 0)); occupy(lwf, dm - .2, dm + .2, 1.62, 2.02, 'FloorNumber')

# ============================================================== windows + radiators
for wi, (wf, uc, jars) in enumerate(L['windows']):
    f = F(wf); a0, a1 = uc - .6, uc + .6; bm = bmesh.new(); nm = 'Window_%d' % (wi + 1)
    for a in ((a0, a0 + .06, .9, 2.2), (a1 - .06, a1, .9, 2.2), (a0 + .0605, a1 - .0605, 2.14, 2.2),
              (a0 + .0605, a1 - .0605, .9, .99), (uc - .03, uc + .03, .99, 2.14), (a0 + .0605, uc - .03, 1.72, 1.78)):
        lbox(bm, wf, a[0], a[1], a[2], a[3], -.245, -.185, 0)
    for a in ((a0 + .06, uc - .03, .99, 1.72), (a0 + .06, uc - .03, 1.78, 2.14), (uc + .03, a1 - .06, .99, 2.14)):
        lbox(bm, wf, a[0], a[1], a[2], a[3], -.215, -.205, 1)
    prism(bm, lambda p, q, a: f(p, a, q), [(a0, -.18), (a1, -.18), (a1, 0), (a1 + .07, 0), (a1 + .07, .07), (a0 - .07, .07), (a0 - .07, 0), (a0, 0)], .9, .93, 0)
    make(nm, bm, 'Windows', [tm(S['frame']), M['night']], origin=f(uc, .9, 0))
    bm = bmesh.new()
    for i in range(9):
        a = uc - .405 + i * .09; lbox(bm, wf, a, a + .06, .12, .72, .06, .16)
    for z in (.2, .64): cyl(bm, f(uc - .7, z, .11), f(uc + .405, z, .11), .025, 8)
    for a in (uc - .3, uc + .3): lbox(bm, wf, a, a + .04, .66, .70, 0, .06)
    cyl(bm, f(uc - .7, 0, .11), f(uc - .7, H, .11), .025, 8)
    make(nm.replace('Window', 'Radiator'), bm, 'Windows', [pm('Radiator')], origin=f(uc, 0, 0))
    occupy(wf, uc - .75, uc + .67, 0, H, nm)
    if jars:
        bm = bmesh.new()
        for du, r, hh in ((-.4, .05, .14), (-.26, .045, .12), (-.14, .05, .16)): cyl(bm, f(uc + du, .93, -.08), f(uc + du, .93 + hh, -.08), r, 8, 0)
        cyl(bm, f(uc + .35, .93, -.08), f(uc + .35, 1.04, -.08), .07, 8, 1, r1=.08)
        for du, dw, top in ((-.02, .01, 1.25), (.02, -.01, 1.2), (0, .02, 1.3)):
            lbox(bm, wf, uc + .35 + du - .004, uc + .35 + du + .004, 1.0, top, -.08 + dw - .004, -.08 + dw + .004, 2)
        make('Sill_Jars_Plant', bm, 'Props', [M['jar'], M['pot'], M['stem']], origin=f(uc, .93, -.08))
    LIGHTS_EXTRA.append(('Light_' + nm, f(uc, 1.6, .5), 3, (.45, .55, 1.0)))

# ============================================================== tambour partitions
for name, ax, c, s0, s1, kind, side, swing in L['partitions']:
    pf = (lambda c: (lambda u, z, w: (c + w, u, z)))(c) if ax == 'x' else (lambda c: (lambda u, z, w: (u, c + w, z)))(c)
    side_walls = [(('y', s0, 1), ('y', s1, -1)), (('x', s0, 1), ('x', s1, -1))][ax == 'y']
    for sw in side_walls: occupy(sw, c - .06, c + .06, 0, H, name)
    gap = .04 if kind == 'grille' else .1
    if side == 'hi': oa, ob, sgn = s1 - 1.0, s1 - gap, -1
    else: oa, ob, sgn = s0 + gap, s0 + 1.0, 1
    hinge = ob - .004 if side == 'hi' else oa + .004
    nvec = Vector(pf(0, 0, 1)) - Vector(pf(0, 0, 0)); d0 = (Vector(pf(1, 0, 0)) - Vector(pf(0, 0, 0))) * sgn
    rz = 0.0
    for a in (78, -78) if kind == 'wood' else (55, -55):
        if (Matrix.Rotation(math.radians(a), 3, 'Z') @ d0).dot(nvec * swing) > 0: rz = math.radians(a); break
    if kind == 'wood':
        bm = bmesh.new(); prism(bm, pf, [(s0, 0), (oa, 0), (oa, 2.05), (ob, 2.05), (ob, 0), (s1, 0), (s1, H), (s0, H)], -.05, .05)
        make(name + '_Partition', bm, 'Tambours', [pm('Partition_Wood')], origin=pf((s0 + s1) / 2, 0, 0))
        bm = bmesh.new(); la, lb = oa + .004, ob - .004; lbox(bm, pf, la, lb, 0, 2.046, -.02, .02, 0)
        for s in (1, -1): lbox(bm, pf, la + .15, lb - .15, 1.2, 1.9, s * .02, s * .024, 1)
        hu = la + .06 if side == 'hi' else lb - .18
        lbox(bm, pf, hu, hu + .12, .98, 1.01, .02, .06, 2)
        make(name + '_Door', bm, 'Tambours', [pm('Partition_Door'), M['wired'], M['handle']], origin=pf(hinge, 0, 0), rot=(0, 0, rz))
    else:
        g0, g1 = (s0, oa) if side == 'hi' else (ob, s1)       # fixed grille part
        bm = bmesh.new()
        for a in ((s0, s0 + .04), (oa - .04, oa) if side == 'hi' else (ob, ob + .04), (s1 - .04, s1)): lbox(bm, pf, a[0], a[1], 0, H, -.02, .02)
        fa, fb = (s0 + .0405, oa - .0405) if side == 'hi' else (ob + .0405, s1 - .0405)
        da, db = (oa + .0005, s1 - .0405) if side == 'hi' else (s0 + .0405, ob - .0005)
        lbox(bm, pf, fa, fb, 0, .04, -.02, .02); lbox(bm, pf, fa, fb, 2.05, 2.09, -.02, .02); lbox(bm, pf, da, db, 2.05, 2.09, -.02, .02)
        lbox(bm, pf, fa, fb, H - .04, H, -.02, .02); lbox(bm, pf, da, db, H - .04, H, -.02, .02)
        n = int((fb - fa) / .12)
        for i in range(n): uu = fa + (i + .5) * (fb - fa) / n; lbox(bm, pf, uu - .008, uu + .008, .04, 2.05, -.008, .008)
        for a, b in ((fa, fb), (da, db)):
            n = int((b - a) / .12)
            for i in range(n): uu = a + (i + .5) * (b - a) / n; lbox(bm, pf, uu - .008, uu + .008, 2.09, H - .04, -.008, .008)
        make(name + '_Grille', bm, 'Tambours', [pm('Metal_Grille')], origin=pf((s0 + s1) / 2, 0, 0))
        la, lb = oa + .004, ob - .004; bm = bmesh.new()
        lbox(bm, pf, la, la + .03, 0, 2.045, -.015, .015); lbox(bm, pf, lb - .03, lb, 0, 2.045, -.015, .015)
        lbox(bm, pf, la + .0305, lb - .0305, 0, .03, -.015, .015); lbox(bm, pf, la + .0305, lb - .0305, 2.015, 2.045, -.015, .015)
        for i in range(6): uu = la + .03 + (i + 1) * (lb - la - .06) / 7; lbox(bm, pf, uu - .008, uu + .008, .03, 2.015, -.008, .008)
        lk = la + .03 if side == 'hi' else lb - .106
        lbox(bm, pf, lk, lk + .076, .95, 1.1, -.03, .03, 1)
        make(name + '_GrilleDoor', bm, 'Tambours', [pm('Metal_Grille'), M['handle']], origin=pf(hinge, 0, 0), rot=(0, 0, rz))

# ============================================================== wall items
IGN = ['Decal_FloorNumber', 'LiftB_Sign', 'Notices']
for wf, u, tex, ang in L['panels']:
    f = F(wf); bm = bmesh.new(); lbox(bm, wf, u - .3, u + .3, 1.1, 2.0, 0, .14)
    if ang > 45:
        for a in (u - .22, u + .04):
            lbox(bm, wf, a, a + .16, 1.45, 1.70, .14, .20, 1); lbox(bm, wf, a + .03, a + .13, 1.58, 1.64, .20, .203, 2)
    nm = 'ElectricPanel_%d' % len([o for o in bpy.data.objects if o.name.startswith('ElectricPanel_') and not o.name.endswith('Door')])
    make(nm, bm, 'Props', [pm(tex), M['plastic'], M['btn_cream']], origin=f(u, 1.1, 0))
    bm = bmesh.new(); lbox(bm, wf, u - .3, u + .3, 1.1, 2.0, .14, .152)
    make(nm + '_Door', bm, 'Props', [pm(tex)], origin=f(u - .3, 1.1, .146), rot=(0, 0, ang_into_room(wf, ang)))
    if ang > 45: IGN.append(nm + '_Door')
    occupy(wf, u - .3, u + .3, 1.1, 2.0, nm)
for i, (wf, u) in enumerate(L['firecabs']):
    f = F(wf); bm = bmesh.new()
    lbox(bm, wf, u - .325, u + .325, .85, 1.7, 0, .21, 0); lbox(bm, wf, u - .32, u + .32, .855, 1.695, .21, .222, 0)
    lbox(bm, wf, u - .2, u + .2, 1.25, 1.6, .222, .225, 1); lbox(bm, wf, u + .26, u + .29, 1.2, 1.3, .222, .245, 2)
    make('FireCabinet_%d' % (i + 1), bm, 'Props', [pm('FireCabinet'), M['wired'], M['handle']], origin=f(u, .85, 0))
    occupy(wf, u - .325, u + .325, .85, 1.7, 'FireCabinet')
(cx0, cy0, cx1, cy1), hwf, hu = L['chute']
bm = bmesh.new(); wbox(bm, (cx0, cy0, 0), (cx1, cy1, H)); bisect(bm, [((0, 0, z), (0, 0, 1)) for z in (.1, 1.5, 1.53)])
zt = S['zones']['hall']
for fc in bm.faces:
    z = fc.calc_center_median().z; fc.material_index = 0 if z < .1 else 1 if z < 1.5 else 2 if z < 1.53 else 3
make('TrashChute', bm, 'Props', [tm(t) for t in zt], origin=((cx0 + cx1) / 2, (cy0 + cy1) / 2, 0))
bm = bmesh.new(); lbox(bm, hwf, hu - .205, hu + .205, .75, 1.15, 0, .07, 0); lbox(bm, hwf, hu - .065, hu + .065, 1.08, 1.11, .07, .1, 1)
make('TrashChute_Hatch', bm, 'Props', [pm('Chute_Hatch'), M['handle']], origin=F(hwf)(hu, .75, 0))
mwf, mu = L['mailboxes']; f = F(mwf); bm = bmesh.new(); lbox(bm, mwf, mu - .45, mu + .45, .9, 1.6, 0, .2, 0)
cw, ch = .86 / 3, .66 / 4
for i in range(3):
    for j in range(4):
        a, z = mu - .43 + i * cw, .92 + j * ch
        lbox(bm, mwf, a + .008, a + cw - .008, z + .008, z + ch - .008, .2, .212, 0)
        lbox(bm, mwf, a + cw / 2 - .06, a + cw / 2 + .06, z + ch - .045, z + ch - .033, .212, .214, 1)
make('Mailboxes', bm, 'Props', [pm('Mailbox'), M['plastic']], origin=f(mu, .9, 0))
bm = bmesh.new()
for a in ((-.4, -.19, 1.68, 1.98), (-.1, .1, 1.72, 1.95), (.18, .4, 1.66, 1.86)): lbox(bm, mwf, mu + a[0], mu + a[1], a[2], a[3], 0, .002)
make('Notices', bm, 'Props', [pm('Paper')], origin=f(mu, 1.66, 0)); occupy(mwf, mu - .45, mu + .45, .9, 1.98, 'Mailboxes')

# ============================================================== lamps, wires, lights
LR = {'plafond': .165, 'flicker': .165, 'dead': .165, 'broken': .105, 'bulb': .0055, 'bulb_dead': .0055}
lights = []
def bulb(bm, x, y, mi):
    cyl(bm, (x, y, H - .35), (x, y, H), .005, 4, 0); cyl(bm, (x, y, H - .42), (x, y, H - .35), .02, 6, 0)
    sphere(bm, (x, y, H - .452), .035, 1, mi, 6, 4)
wires = bmesh.new()
for wf, u0, u1 in L['runs']:          # main cable, interrupted where a tambour partition meets the wall
    cutsu = sorted(c for _, ax, c, s0, s1, *_ in L['partitions'] if wf in ((('y', s0, 1), ('y', s1, -1)), (('x', s0, 1), ('x', s1, -1)))[ax == 'y'] and u0 < c < u1)
    pts = [u0] + [v for c in cutsu for v in (c - .06, c + .06)] + [u1]
    for i in range(0, len(pts), 2): lbox(wires, wf, pts[i], pts[i + 1], 2.24, 2.26, 0, .02)
def on_run(wf, u): return any(r[0] == wf and r[1] <= u <= r[2] for r in L['runs'])
for i, (x, y, kind, wwf) in enumerate(L['lamps']):
    bm = bmesh.new()
    if kind in ('plafond', 'flicker'): cyl(bm, (x, y, H - .07), (x, y, H), .16, 8, 1)
    elif kind == 'dead': cyl(bm, (x, y, H - .07), (x, y, H), .16, 8, 2)
    elif kind == 'broken': cyl(bm, (x, y, H - .025), (x, y, H), .1, 8, 0); cyl(bm, (x, y, H - .08), (x, y, H - .025), .02, 6, 0)
    elif kind == 'bulb': bulb(bm, x, y, 1)
    else: bulb(bm, x, y, 2)
    nm = 'Lamp_%02d' % (i + 1) + {'flicker': '_Flicker', 'dead': '_Dead', 'broken': '_Dead', 'bulb_dead': '_Dead'}.get(kind, '')
    make(nm, bm, 'Lamps', [M['plastic'], M['lamp'], M['deadglass']], origin=(x, y, H))
    if kind in ('plafond', 'flicker', 'bulb'):
        lights.append((nm.replace('Lamp', 'Light'), (x, y, H - (.5 if kind == 'bulb' else .15)), 22 if kind == 'bulb' else 40, LC))
    if wwf:
        a, c, s = wwf; ul = x if a == 'y' else y; d = abs((y if a == 'y' else x) - c)
        if not on_run(wwf, ul): WARN.append(f'lamp {nm} not on a wire run')
        lbox(wires, wwf, ul - .01, ul + .01, 2.26, H, 0, .02); lbox(wires, wwf, ul - .008, ul + .008, H - .02, H, .02, d - LR[kind])
for wf, u, _, _ in L['panels']:
    if on_run(wf, u): lbox(wires, wf, u - .01, u + .01, 2.0, 2.24, 0, .02)
    else: lbox(wires, wf, u - .01, u + .01, 2.0, H, 0, .02)
make('Wires', wires, 'Lamps', [M['wire']], origin=(0, 0, H))
for n, loc, e, c in lights + LIGHTS_EXTRA:
    d = bpy.data.lights.new(n, 'POINT'); d.energy = e; d.color = c; d.shadow_soft_size = .05
    o = bpy.data.objects.new(n, d); o.location = loc; col('Lights').objects.link(o)
sx, sy, sr = L['spawn']; sp = bpy.data.objects.new('Spawn_Player', None); sp.empty_display_type = 'ARROWS'
sp.location = (sx, sy, 0); sp.rotation_euler = (0, 0, math.radians(sr)); col('Markers').objects.link(sp)

# ============================================================== props
def wall_of(wf): return wf
for p in L['props']:
    k = p[0]
    if k == 'chair':
        _, x, y, r = p; bm = bmesh.new()
        for sx_ in (-1, 1):
            for sy_ in (-1, 1): wbox(bm, (sx_ * .21 - (.035 if sx_ > 0 else 0), sy_ * .2 - (.035 if sy_ > 0 else 0), 0), (sx_ * .21 + (.035 if sx_ < 0 else 0), sy_ * .2 + (.035 if sy_ < 0 else 0), .43))
        wbox(bm, (-.215, -.205, .43), (.215, .205, .46))
        for sx_ in (-1, 1): wbox(bm, (sx_ * .21 - (.035 if sx_ > 0 else 0), -.2, .46), (sx_ * .21 + (.035 if sx_ < 0 else 0), -.165, .92))
        wbox(bm, (-.175, -.2, .7), (.175, -.18, .88))
        make('Chair', bm, 'Props', [pm('Chair_Wood')], loc=(x, y, 0), rot=(0, 0, math.radians(r)))
    elif k == 'stool':
        _, x, y, r = p; bm = bmesh.new()
        for sx_ in (-1, 1):
            for sy_ in (-1, 1): wbox(bm, (sx_ * .14 - (.03 if sx_ > 0 else 0), sy_ * .14 - (.03 if sy_ > 0 else 0), 0), (sx_ * .14 + (.03 if sx_ < 0 else 0), sy_ * .14 + (.03 if sy_ < 0 else 0), .42))
        wbox(bm, (-.165, -.165, .42), (.165, .165, .45))
        make('Stool', bm, 'Props', [pm('Chair_Wood')], loc=(x, y, 0), rot=(0, 0, math.radians(r)))
    elif k == 'wardrobe':
        _, wf, u = p; f = F(wf); bm = bmesh.new()
        lbox(bm, wf, u - .5, u + .5, .06, 1.9, 0, .5); lbox(bm, wf, u - .52, u + .52, 1.9, 1.95, 0, .53)
        for a in (u - .495, u + .455):
            for w in (.005, .455): lbox(bm, wf, a, a + .04, 0, .06, w, w + .04)
        for a, b in ((u - .48, u - .005), (u + .005, u + .48)): lbox(bm, wf, a, b, .1, 1.86, .5, .512)
        for a in (u - .03, u + .015): lbox(bm, wf, a, a + .015, .95, 1.1, .512, .53, 1)
        make('Wardrobe', bm, 'Props', [pm('Furniture_Wood'), M['brass']], origin=f(u, 0, .25)); occupy(wf, u - .52, u + .52, 0, 1.95, 'Wardrobe')
    elif k == 'sled':
        _, wf, u = p; f = F(wf); A = math.radians(75); w0 = .8 * math.cos(A) + .002
        fp = lambda a, t, n: f(u + a, t * math.sin(A) + n * math.cos(A), w0 - t * math.cos(A) + n * math.sin(A))
        bm = bmesh.new()
        for s_ in (-1, 1): hexa(bm, fp, (s_ * .16 - .01, s_ * .16 + .01), (0, .8), (0, .05), 1)
        for t in (.1, .3, .5, .7): hexa(bm, fp, (-.17, .17), (t - .03, t + .03), (.05, .07), 0)
        make('Sled', bm, 'Props', [pm('Sled_Wood'), M['steel']], origin=f(u, 0, w0)); occupy(wf, u - .17, u + .17, 0, .8, 'Sled')
    elif k == 'runner':
        _, (x0, y0, x1, y1) = p; bm = bmesh.new(); wbox(bm, (x0, y0, 0), (x1, y1, .008))
        make('Carpet_Runner', bm, 'Props', [pm('Carpet_Runner')], origin=((x0 + x1) / 2, (y0 + y1) / 2, 0))
    elif k == 'rolled':
        _, x, y = p; bm = bmesh.new(); cyl(bm, (x, y, 0), (x, y, 1.5), .12, 8)
        make('Carpet_Rolled', bm, 'Props', [pm('Carpet_Rolled')], origin=(x, y, 0))
    elif k == 'boots':
        _, x, y, r = p; bm = bmesh.new()
        for bx in (-.105, .105):
            wbox(bm, (bx - .05, -.13, .012), (bx + .05, .14, .112)); wbox(bm, (bx - .045, .025, .112), (bx + .045, .135, .38))
        make('Boots', bm, 'Props', [pm('Boots')], loc=(x, y, 0), rot=(0, 0, math.radians(r)))
    elif k == 'boxes':
        _, wf, u = p; f = F(wf); bm = bmesh.new()
        lbox(bm, wf, u - .48, u + .02, 0, .35, .02, .42); lbox(bm, wf, u + .04, u + .49, 0, .3, .02, .42); lbox(bm, wf, u - .38, u - .02, .35, .63, .06, .38)
        make('Boxes', bm, 'Props', [pm('Cardboard')], origin=f(u, 0, .2)); occupy(wf, u - .48, u + .49, 0, .63, 'Boxes')
    elif k == 'bucket':
        _, x, y = p; bm = bmesh.new(); cyl(bm, (x, y, 0), (x, y, .28), .12, 8, 0, r1=.15)
        make('Bucket', bm, 'Props', [pm('Bucket')], origin=(x, y, 0))
    elif k == 'bags':
        for i, (x, y, r) in enumerate(p[1]):
            bm = bmesh.new(); sphere(bm, (0, 0, r * .75), r, .75, 0, 8, 6); cyl(bm, (0, 0, r * 1.45), (0, 0, r * 1.62), .04, 6, 0, r1=.01)
            make('GarbageBag_%02d' % (i + 1), bm, 'Props', [pm('Plastic_Bag')], loc=(x, y, 0))
    elif k == 'envelopes':
        for i, (x, y, r) in enumerate(p[1]):
            bm = bmesh.new(); wbox(bm, (-.08, -.055, 0), (.08, .055, .003))
            make('Envelope_%02d' % (i + 1), bm, 'Props', [pm('Envelope')], loc=(x, y, 0), rot=(0, 0, math.radians(r)))

# ============================================================== UV, checks, save
bpy.context.view_layer.update()
def uv_mat(o):
    mw = o.matrix_world; nm_ = mw.to_3x3().inverted_safe().transposed()
    bm = bmesh.new(); bm.from_mesh(o.data); uvl = bm.loops.layers.uv.get('UVMap') or bm.loops.layers.uv.new('UVMap')
    for fc in bm.faces:
        s = MS[o.data.materials[fc.material_index].name]
        if s is None: continue
        n = (nm_ @ fc.normal).normalized(); ax = max(range(3), key=lambda i: abs(n[i])); sg = 1 if n[ax] >= 0 else -1
        for lp in fc.loops:
            c = mw @ lp.vert.co
            u, v = (sg * c.y, c.z) if ax == 0 else ((-sg * c.x, c.z) if ax == 1 else (c.x, sg * c.y))
            lp[uvl].uv = (u / s[0], v / s[1])
    bm.to_mesh(o.data); bm.free()
meshes = [o for o in root.all_objects if o.type == 'MESH']
for o in meshes: uv_mat(o)
print(kt.check_all([o.name for o in meshes], ground=0, anchors=['Ceiling', 'Walls', 'Ceiling_Beams', 'LiftB_Shaft'], ignore=IGN))
print('WARN', WARN if WARN else 'none')
print('tris', sum(len(p.vertices) - 2 for o in meshes for p in o.data.polygons), 'objects', len(meshes), 'doors', len(L['doors']))
bpy.ops.wm.save_as_mainfile(filepath=OUT, relative_remap=True)
print('saved', OUT)
