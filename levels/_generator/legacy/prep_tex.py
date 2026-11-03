import os
from PIL import Image, ImageDraw, ImageFont, ImageEnhance
C='/tmp/claude-0/prev'; O='/home/user/blender_work_postscript/levels/textures'
def q15(im):  # PS1-style 15-bit colour (5 bits per channel)
    return im.point(lambda v: (v>>3)<<3 | (v>>5))
T={ # name: (cache key, size, source credit)
 'T_Floor_MetlakhHex':('am__Tiles065',128,'ambientCG Tiles065'),
 'T_Wall_PaintGreen':('am__PaintedPlaster003',128,'ambientCG PaintedPlaster003'),
 'T_Whitewash':('am__Plaster001',128,'ambientCG Plaster001'),
 'T_Ceiling':('am__Plaster002',64,'ambientCG Plaster002'),
 'T_LiftDoor_Metal':('cg__PaintedMetal01',64,'cgbookcase PaintedMetal01'),
 'T_Shchitok_Metal':('am__PaintedMetal006',64,'ambientCG PaintedMetal006'),
 'T_Door_DermatinBrown':('am__Leather034B',64,'ambientCG Leather034B'),
 'T_Door_DermatinBlack':('am__Leather010',64,'ambientCG Leather010'),
 'T_Wood_Frame':('am__PaintedWood009C',64,'ambientCG PaintedWood009C'),
 'T_Door_StairWood':('am__PaintedWood008C',64,'ambientCG PaintedWood008C'),
 'T_LiftCab_Wood':('am__Wood030',64,'ambientCG Wood030'),
 'T_Concrete':('am__Concrete015',64,'ambientCG Concrete015'),
}
lines=['# Texture sources','','All bases are CC0 (ambientCG, cgbookcase), taken from the 256 px colour previews in',
 'github.com/Papyszoo/CC0-Public-Domain-Textures, box-downscaled and cut to 15-bit colour (PS1 look).',
 'Unity: Filter Mode = Point, Compression = None.','','| File | Size | Source |','|---|---|---|']
for n,(k,s,src) in T.items():
    p=f'{C}/{k}.png'
    if not os.path.exists(p):
        pk,f=k.split('__'); raise SystemExit('missing '+p)
    im=Image.open(p).convert('RGB').resize((s,s),Image.BOX); q15(im).save(f'{O}/{n}.png')
    lines.append(f'| {n}.png | {s} | {src} |')
# stripe between paint and whitewash: same green paint, darker
g=Image.open(f'{C}/am__PaintedPlaster003.png').convert('RGB').resize((64,64),Image.BOX)
q15(ImageEnhance.Brightness(g).enhance(0.45)).save(f'{O}/T_Wall_PaintStripe.png')
lines.append('| T_Wall_PaintStripe.png | 64 | ambientCG PaintedPlaster003, darkened |')
# stencilled floor number (drawn: no source texture for this)
im=Image.new('RGBA',(32,32),(0,0,0,0)); d=ImageDraw.Draw(im)
f=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',30)
d.text((16,17),'7',font=f,fill=(48,38,34,235),anchor='mm'); im.save(f'{O}/T_FloorNumber_7.png')
lines.append('| T_FloorNumber_7.png | 32 | drawn (DejaVu Sans Bold), stencil paint |')
open(f'{O}/SOURCES.md','w').write('\n'.join(lines)+'\n'); print('ok', len(os.listdir(O)))
