"""Preview renders of any .blend (headless). Cameras are temporary, nothing is saved into the file.
usage: python3 render_preview.py <file.blend> <out_prefix> "<shots>" [world_strength=.02] [exposure=1.0] [mode=preview|lowres]
shots: python list of ((cam x, y, z), (target x, y, z)), e.g. "[((4.5,.6,1.6),(4.5,5,1.3))]"
mode preview: Cycles 480x300, 40 samples, denoise (smooth, hides pixelation)
mode lowres:  320x200, no denoise, no pixel filter, then a nearest-neighbour 2x upscale (how a low-res pixel style looks in the engine)
Writes <out_prefix>_<i>.png. Read the PNGs to judge the result."""
import sys, bpy
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
path, out, shots = a[0], a[1], eval(a[2])
ws = float(a[3]) if len(a) > 3 else .02; ex = float(a[4]) if len(a) > 4 else 1.0; mode = a[5] if len(a) > 5 else 'preview'
bpy.ops.wm.open_mainfile(filepath=path)
sc = bpy.context.scene
w = bpy.data.worlds.new('preview_world'); sc.world = w; bg = w.node_tree.nodes['Background']
bg.inputs[0].default_value = (.3, .35, .5, 1); bg.inputs[1].default_value = ws
cd = bpy.data.cameras.new('preview_cam'); cd.lens = 18; cd.clip_end = 800
cam = bpy.data.objects.new('preview_cam', cd); sc.collection.objects.link(cam); sc.camera = cam
r = sc.render; r.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.view_settings.view_transform = 'Standard'; sc.view_settings.exposure = ex
if mode == 'lowres':
    sc.cycles.samples = 96; sc.cycles.use_denoising = False; r.resolution_x, r.resolution_y = 320, 200; r.filter_size = .01
else:
    sc.cycles.samples = 40; sc.cycles.use_denoising = True; r.resolution_x, r.resolution_y = 480, 300
for i, (loc, tgt) in enumerate(shots):
    cam.location = loc; cam.rotation_euler = (Vector(tgt) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    r.filepath = f'{out}_{i}.png'; bpy.ops.render.render(write_still=True)
    if mode == 'lowres':
        from PIL import Image
        im = Image.open(r.filepath); im.resize((im.width * 2, im.height * 2), Image.NEAREST).save(r.filepath)
print('rendered', len(shots))
