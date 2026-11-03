import os
from PIL import Image, ImageEnhance, ImageDraw, ImageFont
src_code=open('/tmp/claude-0/tools/prep_tex2.py').read()
exec(src_code[:src_code.index('T={')].replace("for f in os.listdir(O): os.remove(os.path.join(O,f))",""))
NEW={ # name: (key, size, saturation, brightness)
 'T_Ext_Panel_A':('am__Concrete034',128,.5,1), 'T_Ext_Panel_B':('am__Concrete013',128,.5,1), 'T_Ext_Panel_C':('am__Concrete016',128,.5,1.15),
 'T_Ext_Seam':('am__Concrete031',64,.5,.4), 'T_Ext_Plinth':('am__Concrete032',128,.5,1), 'T_Ext_Road':('am__Asphalt025A',128,.6,1),
 'T_Ext_Sidewalk':('am__Asphalt021',128,.6,1), 'T_Ext_Curb':('am__Concrete015',64,.5,1.1), 'T_Ext_Lawn':('po__brown_mud_leaves_01',128,.75,1),
 'T_Ext_Mud':('am__Ground048',128,.7,1), 'T_Ext_LeafClump':('po__forest_leaves_03',64,.7,1), 'T_Ext_Sand':('am__Ground033',64,.6,.9),
 'T_Ext_BarkPoplar':('am__Bark001',64,.6,1), 'T_Ext_BarkBirch':('am__Bark009',64,.6,1), 'T_Ext_GarageWall':('am__CorrugatedSteel007B',128,.55,1),
 'T_Ext_GarageDoor':('am__CorrugatedSteel005',64,.6,1), 'T_Ext_BrickWhite':('am__Bricks024',128,.6,1), 'T_Ext_BrickRed':('am__Bricks025',64,.55,1),
 'T_Ext_NightFacade':('am__Facade010',128,.7,1), 'T_Ext_NightFacade2':('am__Facade011',128,.7,1),
 'T_Ext_Curtain_1':('am__Fabric008',64,.8,1), 'T_Ext_Curtain_2':('am__Fabric009',64,.8,1), 'T_Ext_Curtain_3':('am__Fabric035',64,.7,1),
 'T_Ext_Curtain_4':('am__Fabric017',64,.7,1), 'T_Ext_Rust':('am__Rust004',64,.6,1), 'T_Ext_PaintOrange':('am__PaintedMetal008',64,.5,1),
 'T_Ext_PaintBlue':('am__PaintedMetal007',64,.5,1), 'T_Ext_PaintRed':('am__PaintedMetal004',64,.45,.9), 
 'T_Ext_CarPaintB':('am__PaintedMetal010',64,.4,.85), 'T_Ext_Pole':('am__Concrete015',64,.4,1.15), 'T_Ext_Roof':('am__Asphalt026A',64,.5,1),
}
rows=[]
for n,(k,s,sat,br) in NEW.items():
    im=Image.open(src(k)).convert('RGB').resize((s,s),Image.BOX)
    im=ImageEnhance.Color(im).enhance(sat)
    if br!=1: im=ImageEnhance.Brightness(im).enhance(br)
    q15(im).save(f'{O}/{n}.png'); pk,name=k.split('__')
    rows.append(f'| {n}.png | {s} | {NAMES[pk]} {name}, saturation x{sat}'+(f', brightness x{br}' if br!=1 else '')+' |')
# house number plate (drawn: blue enamel, white digit)
B='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
im=Image.new('RGB',(64,32),(38,58,110)); d=ImageDraw.Draw(im); d.rectangle((0,0,63,31),outline=(200,200,200)); d.rectangle((2,2,61,29),outline=(200,200,200))
d.text((32,16),'7',font=ImageFont.truetype(B,22),fill=(235,235,235),anchor='mm'); im.save(f'{O}/T_Ext_HouseNumber.png')
rows.append('| T_Ext_HouseNumber.png | 64x32 | drawn: house number plate |')
s=open(f'{O}/SOURCES.md').read().rstrip('\n')+'\n'+'\n'.join(rows)+'\n'; open(f'{O}/SOURCES.md','w').write(s); print('added',len(rows))
