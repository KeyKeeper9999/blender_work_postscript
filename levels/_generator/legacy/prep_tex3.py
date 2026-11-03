# blue/concrete style textures + muted copies of the existing set (existing files are kept)
import os, sys
sys.path.insert(0, '/tmp/claude-0/tools')
from PIL import Image, ImageEnhance
O='/home/user/blender_work_postscript/levels/textures'
exec(open('/tmp/claude-0/tools/prep_tex2.py').read().split("rows=[]")[0].split("for f in os.listdir(O)")[0])  # src(), q15(), NAMES
src_code=open('/tmp/claude-0/tools/prep_tex2.py').read()
exec(src_code[src_code.index('lines=open'):src_code.index('T={')])
NEW={ # name: (key, size, saturation, brightness)
 'T_Wall_PaintSkyBlue':('po__blue_plaster_weathered',128,.85,1), 'T_Wall_PaintSkyBlueStripe':('po__blue_plaster_weathered',64,.8,.5),
 'T_Wall_PaintBlueGreyPeeling':('am__PaintedPlaster008',128,.6,1.05), 'T_Wall_ConcretePainted':('am__Concrete034',128,.5,1),
 'T_Wall_ConcreteStained':('am__PaintedPlaster015',128,.5,1), 'T_Baseboard_Dark':('am__Concrete031',64,.5,.6),
 'T_Floor_Concrete':('am__Concrete020',128,.6,1), 'T_Floor_ConcreteWorn':('po__concrete_floor_02',128,.5,1),
 'T_Floor_ConcreteLight':('am__Concrete036',128,.5,1), 'T_Ceiling_Concrete':('am__Concrete034',128,.4,1.05),
 'T_Ceiling_ConcreteStained':('am__Concrete019',128,.4,1), 'T_Beam_Concrete':('am__Concrete015',64,.5,1.1),
 'T_Wall_Wallpaper2_M':('sh__wallpaper-20',128,.5,.95),
}
rows=[]
for n,(k,s,sat,br) in NEW.items():
    im=Image.open(src(k)).convert('RGB').resize((s,s),Image.BOX)
    im=ImageEnhance.Color(im).enhance(sat)
    if br!=1: im=ImageEnhance.Brightness(im).enhance(br)
    q15(im).save(f'{O}/{n}.png'); pk,name=k.split('__')
    rows.append(f'| {n}.png | {s} | {NAMES[pk]} {name}, saturation x{sat}'+(f', brightness x{br}' if br!=1 else '')+' |')
MUTE=['Door_DermatinBrown','Door_DermatinBlack','Door_WoodBeige','Door_WoodBlue','Door_WoodBrown','Door_SteelBrown','Door_SteelGrey',
 'Door_StairWood','Wood_Frame','Partition_Wood','Partition_Door','Metal_Grille','Mailbox','FireCabinet','ElectricPanel','Chute_Hatch',
 'Radiator','Furniture_Wood','Chair_Wood','Sled_Wood','Cardboard','Carpet_Runner','Carpet_Rolled','Mat_Olive','Mat_Blue','Wall_Vagonka',
 'LiftCab_Wood','Bucket']
for n in MUTE:
    im=Image.open(f'{O}/T_{n}.png').convert('RGB'); im=ImageEnhance.Color(im).enhance(.45 if n!='FireCabinet' else .6)
    q15(ImageEnhance.Brightness(im).enhance(.95)).save(f'{O}/T_{n}_M.png'); rows.append(f'| T_{n}_M.png | {im.size[0]} | T_{n}.png desaturated (blue/concrete style) |')
s=open(f'{O}/SOURCES.md').read().rstrip('\n')+'\n'+'\n'.join(rows)+'\n'
open(f'{O}/SOURCES.md','w').write(s); print('added', len(rows))
