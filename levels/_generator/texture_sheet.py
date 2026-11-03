"""Contact sheet of CC0 texture previews to pick bases from.
usage: python3 texture_sheet.py out.png <cell px> <regex> [regex...]
keys look like am:Tiles065 (am ambientCG, po Poly Haven, sh ShareTextures, cg cgbookcase); downloaded previews are cached
and the same keys work in paint_*.py as 'am__Tiles065'."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import paint_textures as PT; PT.ensure_list()
# usage: sheet.py out.png cell regex [regex...]  -> contact sheet of color previews whose folder matches
import sys, re, os, subprocess, concurrent.futures as cf
from PIL import Image, ImageDraw
out, cell = sys.argv[1], int(sys.argv[2]); pats=[re.compile(p) for p in sys.argv[3:]]
lines=open('/tmp/claude-0/papy.txt').read().split('\n')
pick={}
for l in lines:
    m=re.match(r'packs/([a-z]+)-textures/textures/([^/]+)/(.+_preview\.png)$', l)
    if not m: continue
    pack,folder,fn=m.groups()
    key=f"{pack[:2]}:{folder}"
    if not any(p.search(key) for p in pats): continue
    if re.search(r'(?i)(color|albedo|diffuse|diff|basecolor|col)[^/]*_preview', fn) or key not in pick:
        if key in pick and not re.search(r'(?i)(color|albedo|diffuse|diff|basecolor|col)', fn): continue
        pick[key]=l
cache='/tmp/claude-0/prev'; os.makedirs(cache, exist_ok=True)
def get(k):
    p=os.path.join(cache, k.replace(':','__')+'.png')
    if not os.path.exists(p):
        subprocess.run(['curl','-sS','--retry','3','-o',p,'https://raw.githubusercontent.com/Papyszoo/CC0-Public-Domain-Textures/main/'+pick[k]])
    return k,p
keys=sorted(pick)
with cf.ThreadPoolExecutor(16) as ex: res=list(ex.map(get, keys))
cols=min(10,len(res)); rows=(len(res)+cols-1)//cols
S=Image.new('RGB',(cols*cell, rows*(cell+12)),(30,30,30)); d=ImageDraw.Draw(S)
for i,(k,p) in enumerate(res):
    try: im=Image.open(p).convert('RGB').resize((cell,cell))
    except Exception: continue
    x,y=(i%cols)*cell,(i//cols)*(cell+12); S.paste(im,(x,y+12)); d.text((x+2,y),k.split(':',1)[1][:22],fill=(255,255,0))
S.save(out); print(len(res),'tiles ->',out, S.size)
