import os, re, subprocess
from PIL import Image, ImageDraw, ImageFont, ImageEnhance
C='/tmp/claude-0/prev'; O='/home/user/blender_work_postscript/levels/textures'
os.makedirs(O, exist_ok=True)
for f in os.listdir(O): os.remove(os.path.join(O,f))
lines=open('/tmp/claude-0/papy.txt').read().split('\n')
PACK={'am':'ambientcg','po':'polyhaven','sh':'sharetextures','cg':'cgbookcase'}
def src(key):
    p=f'{C}/{key}.png'
    if os.path.exists(p): return p
    pk,name=key.split('__'); cands=[l for l in lines if l.startswith(f'packs/{PACK[pk]}-textures/textures/{name}/') and l.endswith('_preview.png')]
    col=[l for l in cands if re.search(r'(?i)(color|albedo|diffuse|diff|basecolor|col)[^/]*_preview', l)] or cands
    subprocess.run(['curl','-sS','--retry','3','-o',p,'https://raw.githubusercontent.com/Papyszoo/CC0-Public-Domain-Textures/main/'+col[0]],check=True)
    return p
def q15(im): return im.point(lambda v: (v>>3)<<3 | (v>>5))
NAMES={'am':'ambientCG','po':'Poly Haven','sh':'ShareTextures','cg':'cgbookcase'}
T={ # out name: (key, size, rotate, brightness)
 'T_Floor_MetlakhHex':('am__Tiles065',128,0,1), 'T_Floor_Terrazzo':('am__Terrazzo005',128,0,1),
 'T_Floor_Linoleum':('po__old_linoleum_flooring_01',128,0,1), 'T_Floor_WornTiles':('am__Tiles094',128,0,1),
 'T_Wall_PaintGreen':('am__PaintedPlaster003',128,0,1), 'T_Wall_PaintGreenStripe':('am__PaintedPlaster003',64,0,.45),
 'T_Wall_PaintPeeling':('am__PaintedPlaster009',128,0,1), 'T_Wall_PaintBlue':('am__PaintedPlaster008',128,0,1),
 'T_Wall_PaintBlueStripe':('am__PaintedPlaster008',64,0,.45), 'T_Wall_Vagonka':('am__WoodSiding009',128,90,1),
 'T_Wall_Wallpaper':('sh__wallpaper-6',128,0,1), 'T_Whitewash':('am__Plaster001',128,0,1),
 'T_Plaster_Stained':('am__PaintedPlaster016',128,0,1), 'T_Ceiling':('am__Plaster002',64,0,1),
 'T_Baseboard_Paint':('am__PaintedWood008C',64,0,.8), 'T_Wood_Frame':('am__PaintedWood009C',64,0,1),
 'T_Door_DermatinBrown':('am__Leather034B',64,0,1), 'T_Door_DermatinBlack':('am__Leather010',64,0,1),
 'T_Door_DermatinRed':('am__Leather011',64,0,1), 'T_Door_WoodBrown':('am__PaintedWood006A',64,0,1),
 'T_Door_WoodBeige':('am__PaintedWood007C',64,0,1), 'T_Door_WoodBlue':('am__PaintedWood008B',64,0,1),
 'T_Door_SteelBrown':('am__Metal018',64,0,1), 'T_Door_SteelGrey':('am__Metal040',64,0,1),
 'T_Door_StairWood':('am__PaintedWood008C',64,0,1), 'T_Planks':('am__Planks006',64,0,1),
 'T_Partition_Wood':('am__PaintedWood006C',64,0,1), 'T_Partition_Door':('am__PaintedWood009B',64,0,1),
 'T_Metal_Grille':('am__Metal013',64,0,1), 'T_LiftDoor_Metal':('cg__PaintedMetal01',64,0,1),
 'T_LiftCab_Wood':('am__Wood030',64,0,1), 'T_LiftCab_Floor':('am__Rubber004',64,0,1),
 'T_Shaft_Concrete':('am__Concrete032',64,0,.7), 'T_Concrete':('am__Concrete015',64,0,1),
 'T_ElectricPanel':('am__PaintedMetal006',64,0,1), 'T_Radiator':('am__PaintedMetal012',64,0,1),
 'T_Mailbox':('am__PaintedMetal007',64,0,1), 'T_FireCabinet':('am__PaintedMetal004',64,0,1),
 'T_Chute_Hatch':('am__PaintedMetal013',64,0,1), 'T_Furniture_Wood':('am__Wood036',64,0,1),
 'T_Chair_Wood':('am__Wood020',64,0,1), 'T_Sled_Wood':('am__PaintedWood003',64,0,1),
 'T_Cardboard':('am__Cardboard002',64,0,1), 'T_Plastic_Bag':('am__Plastic006',64,0,1),
 'T_Paper':('am__Paper001',64,0,1), 'T_Envelope':('am__Paper003',64,0,1),
 'T_Carpet_Runner':('am__Carpet013',64,0,1), 'T_Carpet_Rolled':('am__Carpet015',64,0,1),
 'T_Mat_Olive':('am__Carpet011',64,0,1), 'T_Mat_Blue':('am__Carpet012',64,0,1), 'T_Mat_Rubber':('am__Rubber001',64,0,1),
 'T_Boots':('am__Leather015',64,0,1), 'T_Bucket':('am__Metal024',64,0,1),
}
rows=[]
for n,(k,s,rot,br) in T.items():
    im=Image.open(src(k)).convert('RGB')
    if rot: im=im.transpose(Image.Transpose.ROTATE_90)
    w,h=im.size; im=im.resize((s,s) if w==h else ((s*w)//max(w,h),(s*h)//max(w,h)),Image.BOX)
    if br!=1: im=ImageEnhance.Brightness(im).enhance(br)
    q15(im).save(f'{O}/{n}.png')
    pk,name=k.split('__'); rows.append(f'| {n}.png | {s} | {NAMES[pk]} {name}'+(' (rotated 90)' if rot else '')+(' (darkened)' if br!=1 else '')+' |')
B='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
# floor number stencil
im=Image.new('RGBA',(32,32),(0,0,0,0)); d=ImageDraw.Draw(im)
d.text((16,17),'7',font=ImageFont.truetype(B,30),fill=(48,38,34,235),anchor='mm'); im.save(f'{O}/T_FloorNumber_7.png')
rows.append('| T_FloorNumber_7.png | 32 | drawn: stencil digit |')
# apartment number plates atlas: 8x8 cells of 32x16
PLATES=open('/tmp/claude-0/tools/plates.txt').read().split()
STY={'w':((214,208,190),(20,20,20)),'b':((176,136,64),(40,28,10)),'k':((28,28,28),(210,205,190)),'u':((42,62,120),(225,225,225))}
im=Image.new('RGB',(256,128),(0,0,0)); d=ImageDraw.Draw(im); f=ImageFont.truetype(B,12)
for i,p in enumerate(PLATES):
    num,st=p.split(':'); bg,fg=STY[st]; x,y=(i%8)*32,(i//8)*16
    d.rectangle((x,y,x+31,y+15),fill=bg); d.rectangle((x,y,x+31,y+15),outline=tuple(int(c*.6) for c in bg))
    d.text((x+16,y+8),num,font=f,fill=fg,anchor='mm')
im.save(f'{O}/T_NumberPlates.png'); rows.append('| T_NumberPlates.png | 256x128 | drawn: apartment number plates atlas |')
# "out of order" note on real paper
p=Image.open(src('am__Paper001')).convert('RGB').resize((64,64),Image.BOX); d=ImageDraw.Draw(p); f=ImageFont.truetype(B,10)
d.text((32,24),'ЛИФТ НЕ',font=f,fill=(30,30,40),anchor='mm'); d.text((32,38),'РАБОТАЕТ',font=f,fill=(30,30,40),anchor='mm')
q15(p).save(f'{O}/T_Sign_LiftBroken.png'); rows.append('| T_Sign_LiftBroken.png | 64 | ambientCG Paper001 + drawn text |')
hdr=['# Texture sources','','Bases are CC0 (ambientCG, Poly Haven, ShareTextures, cgbookcase), taken from the 256 px colour previews in',
 'github.com/Papyszoo/CC0-Public-Domain-Textures, box-downscaled and cut to 15-bit colour (PS1 look).',
 'Drawn by hand only where no source fits (digits, number plates, the lift note).','',
 'Unity: Filter Mode = Point, Compression = None, Generate Mip Maps off (or on, for less shimmer at distance).','',
 '| File | Size | Source |','|---|---|---|']
open(f'{O}/SOURCES.md','w').write('\n'.join(hdr+rows)+'\n'); print('textures:',len(os.listdir(O))-1)
