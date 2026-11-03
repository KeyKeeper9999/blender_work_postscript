# Environment art for a PS1-style horror game: what works, and Blender traps

Read once per chat before modeling environments or props (levels, streets, interiors, cars, furniture).
Part 1 is how to make it look good, part 2 is technique that broke before and how it was fixed.
Lessons come from building the Postscript levels (see PROJECT_STATUS.md in the repo root) and the sources at the end.

## 1. Looking good

### Geometry vs texture
- Model what makes the silhouette and catches light: car body with wheel arches and a sloped greenhouse,
  bumpers, round headlights, door casings with 2 steps, jamb lining, skirting and cap rails, ceiling beams,
  radiator sections, pipes with brackets, lamp fittings. Low-poly style still needs these shapes.
- Paint everything small into the texture: panel lines, handles on far objects, grilles, tufting, rivets,
  labels, numbers, cracks, drips. On a PS1 budget a texture can carry only so much: real lenses/glass
  read better as geometry (headlights) than as painted circles (Polycount threads below).
- Painted highlights: warm tones, not pure white. Glass = dark vertical gradient + 1-2 diagonal reflection
  streaks; broken glass = a few black shards.
- Doors, lifts and other hero props: one atlas per set (8 door leaves of 64x128 px in one 512x128 image),
  front and back faces get explicit UVs into their cell; edges use a plain dark material.

### Textures: photo grain + drawn shape
- Base = a real CC0 photo (only for grain and colour noise), everything with a shape is drawn on top:
  tile grids, wallpaper motifs, quilted dermatin diamonds, paint edges, numbers, stencils, stickers.
- Grade every photo to the theme palette: tint by luminance with low contrast (0.35-0.6). This is what makes
  textures from different sources look like one place. Muted themes: desaturate the props too.
  Too much contrast in the photo = noisy, speckled walls (seen on oil-paint walls at contrast 1.0).
- Walls: one texture per wall covers floor to ceiling (256x256 = 4 m x 2.6 m, UV u = along wall / 4 m,
  v = z / 2.6). Then the two-tone paint edge, the dark stripe, drips, chips showing older paint, scuffs at
  shoe/bag height and dust under the ceiling are hand-drawn and uneven, instead of geometry splits.
  Make it horizontally seamless (paint 32 px extra and cross-fade). Make 3 variants, pick per 4 m block.
- Wallpaper: strips 0.5 m wide with seams, small vertical misalignment per strip, sun-faded strips,
  dirt toward the floor. Motifs small (cell 16-32 px at 64 px/m) and low contrast, or they look cartoonish.
- Floors: draw tiles (grout lines, per-tile colour jitter, chipped corners, a few cracked or replaced tiles).
  Big surfaces (roads, lawns) get bigger textures so the repeat is less visible.

### Breaking the repeat (the biggest visual win)
- Several variants of the same material, chosen per block; never one tile over 40 m.
- Decals (alpha quads): asphalt patches, cracks, oil, manholes, leaves along curbs, moss/dry grass/mud blobs
  on lawns, trampled ground, trodden paths, puddles; indoors: water stains, scuffs, scribbles, cracks,
  mould, soot above lamps and burnt doors, worn traffic path, missing tiles, debris, flyers.
- Fake AO: dark alpha-gradient strips (~0.3 m) on the floor along every wall and on the ceiling along every
  corner. Cheap and it removes the "flat, dry" look of interiors more than anything else.
- Facades: rain streaks under sills, rust bleeding from drainpipe brackets, splash grime on the plinth.
- Large single texture beats many small ones where repetition is the problem; stochastic/random-rotation
  tricks do not work on regular patterns like tiles and bricks (Polycount, Unity forum threads below).
- Varied geometry and props on top of the worst areas (boxes, prams, plants, benches) also hide tiling.

### Puddles and wet
- Puddle = irregular alpha blob decal: dark water core + lighter wet rim, low roughness (~0.03). The
  reflection must be masked to the puddle shape, not to a rectangle (puddle devlog below).

### PS1 look (Voices of the Void / KLETKA direction)
- Texel density around 32 px/m reads as PS1; ~64-100 px/m already looks "too good".
  Our level textures are 64-107 px/m: Key is deciding whether to halve them (see PROJECT_STATUS.md).
- Colour: 15-bit (5 bits/channel) at least; 16 levels/channel for a cruder look.
- Most of the pixel look comes from the engine: low internal render resolution (e.g. 480x270 RenderTexture
  upscaled without filtering), Filter Mode = Point on every texture, optionally vertex snapping and
  affine texture warping in a PS1 shader. Keep text (door numbers, signs, plates) sharp enough to read.
- Blender previews with denoise hide pixelation; judge the style with render_preview.py mode ps1.

### Lighting and mood
- One point light per working fixture; emissive materials for windows, buttons, indicators; a few fixtures
  dead or broken; flickering ones named *_Flicker for a Unity script. Dark zones are fine, but leave a
  readable path (moonlit window, one lit lamp, an emergency light).
- Exterior night: sodium street lamps (orange spots), lit windows only ~20% with curtains/TV variants,
  distant blocks as dark boxes with sparse lit window quads, not an office-tower facade texture.

### Storytelling details (dread without jump scares)
- Small wrong things: a door painted over like the wall with no number, a repeated apartment number,
  a doormat in front of a blank wall, muddy footprints leading into the wrong door, a lone chair facing
  a covered mirror, furniture on the ceiling, a hallway that keeps going, letters covering a floor.
- Everyday Soviet clutter makes the normal believable first: prams, sleds, boots on a rag rug, boxes,
  rolled carpets, notices with tear-off phone strips, mailboxes with letters sticking out.

### Real sizes used (1 unit = 1 m)
- Ceiling 2.6; corridor 2 wide; apartment door opening 0.94 x 2.07; interior door 0.8 x 2.0; two-tone
  paint edge 1.5-1.6; skirting 0.07-0.08; wainscot cap 1.0; window sill 0.85-0.9.
- Soviet passenger lifts (320-500 kg) had ~0.7 m door openings (dnaop.com); in game 1.0 m reads better.
- Panel block: 2.8 m storey, 3 m bays, 9 storeys; khrushchevka 5 storeys 2.7 m.

## 2. Technique that broke (headless bpy 5.2 + bmesh)

### kt.check_all
- check_zfight flags coplanar overlapping same-facing faces even on objects passed in `ignore`
  (ignore only affects the floating check). Decals: put each kind on its own layer 2 mm apart and never
  overlap two quads of the same layer; flat stacks of quads need >= 4 mm between levels; tilted quads
  (letters on a floor) with random tilt are fine.
- Adjacent boxes that share corner vertices -> "double verts": end one of them 0.5 mm short.
- Trims meeting in a corner overlap: let walls along one axis stop 27 mm short at both ends.
- Thin parts flush with a wall (jamb lining, casing back) closer than ~4 mm to the wall plane get flagged.
- Wire/plate touching a beam or lamp top at the ceiling plane: stop 1.5 mm below it.
- Door leaves hang on hinges with gaps: put them in `ignore` (floating), not touching the frame.

### bmesh
- Concave ngon caps: triangulate with ngon_method='EAR_CLIP' after normal_update.
- create_cone along a direction: rotation_difference((0,0,1), dir), not to_track_quat (gave flipped caps).
- recalc_face_normals is unreliable on many small islands: orient each closed island by signed volume.
- Quads built one by one have separate verts: remove_doubles before make, or the check reports doubles.
- Explicit-UV faces (decals, fronts) on a box: recalc can flip them; build them as separate quads and check
  normal against the wall normal.

### Alpha decals
- A decal must be a single quad. A thin box with an alpha texture rendered a grey square (seen on the
  floor number and the end-wall house number).
- Material: Image Texture (Closest) Color -> Base Color, Alpha -> Alpha. In Unity they need Alpha
  Clipping or Transparent.

### Booleans and walls
- Wall shell = one box minus room boxes (rooms extended 3 cm into neighbours they open onto) minus door,
  window and shaft cutters; EXACT solver.
- EXACT boolean adds an empty (None) material slot from the cutters: strip it (kit.boolean_cut does).
- The same material twice in a mesh's list breaks slots: build a unique list and index by texture.
- Bisecting walls on planes that coincide with wall surfaces makes zero-area faces: skip planes on room
  boundaries; delete the hidden top/bottom faces of the shell.
- Material by face: point = face centre + normal * 6 cm, then find the room.

### Files, imports, environment
- Never name a script inspect.py (or any stdlib name): bpy then crashes with "InitGoogleLogging twice".
- Appending objects from another .blend (libraries.load): bake LocRotScale into the mesh data yourself,
  and remove the appended images/materials you replace, or 2048 px packed textures end up in the file.
- GitHub: 100 MB per file via git, 25 MB via the web upload. Keep .blend files small: textures as external
  PNGs in levels/textures (relative paths), nothing packed.
- Cloud sessions: blender.org, ambientcg.com, polyhaven.com are blocked; pypi and GitHub work. CC0 textures
  come from the 256 px previews of github.com/Papyszoo/CC0-Public-Domain-Textures (blobless clone for the
  file list). bpy via pip is very slow: setup_headless.sh downloads the wheel in 16 parallel ranges.
- Preview renders: Cycles CPU, Standard view transform, low world strength, 480x300, 40 samples + denoise;
  then Read the PNG. A render takes 10-60 s.

## Sources
- Polycount, headlights as geometry vs texture: https://polycount.com/discussion/comment/1037078
- Polycount, painted warm highlights on glass: https://polycount.com/discussion/comment/1036736
- Polycount, breaking tiling (bigger single texture, variants, decals, geometry): https://polycount.com/discussion/comment/2704129
- Polycount, vertex colour and decals against tiling: https://polycount.com/discussion/comment/2516644
- Unity forum, Repetitionless (stochastic tiling, limits on regular patterns): https://discussions.unity.com/t/repetitionless-texture-tiling-remover/1705964
- Puddle reflection masking devlog: https://everythings-a-nail.mataroa.blog/blog/report-from-the-pits-puddles
- PS1 rendering (affine mapping, vertex snapping, low-res textures): https://pikuma.com/blog/how-to-make-ps1-graphics
- Lift door openings 700 mm for 320-500 kg: https://dnaop.com/html/41723_2.html ; min height 1960 mm: https://dnaop.com/html/56686_5.html
- Two-tone Soviet stairwell paint: https://www.obozrevatel.com/novosti-obschestvo/pochemu-v-sssr-podezdyi-krasili-do-polovinyi-otkuda-vzyalas-lyubov-k-sinemu-i-zelenomu-tsvetu/amp.htm
