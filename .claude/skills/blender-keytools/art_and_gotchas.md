# Modeling environments and props: what makes them look good, and Blender traps

Read once per chat before modeling environments or props (levels, streets, interiors, vehicles, furniture).
Style-neutral: the project decides the target look (its own art-direction doc, if the repo has one, wins over
the defaults here). Part 1 is craft, part 2 is technique that broke before and how it was fixed.

## 1. Craft

### Decide the style numbers first
- Texel density (texture pixels per metre) sets the look more than anything; pick it once per project and keep
  it consistent across assets. Rough guide: retro/PS1 ~16-32 px/m, stylized ~64-128 px/m, realistic commonly
  512-1024 px/m. Mixed densities in one view look wrong immediately.
- Colour budget (full colour, or 15-bit / posterized for retro) and filtering (Point for pixel art styles,
  trilinear/anisotropic for realistic) are part of the same decision.
- Use real-world sizes (1 unit = 1 m). Games often exaggerate a few for readability or camera comfort
  (wider doors, lifts, corridors); do that on purpose and note it.

### Geometry vs texture
- Model what makes the silhouette and catches light: wheel arches and a sloped greenhouse on a car, bumpers,
  round lamps, door casings with steps, jamb lining, skirting and rails, beams, radiator sections, pipes with
  brackets, light fittings. Even a low budget needs these shapes.
- Paint (or bake, for realistic work) the small things: panel lines, handles on distant objects, grilles,
  rivets, labels, numbers, cracks, drips. A texture can carry only so much: lenses and glass usually read better
  as geometry than as painted circles.
- Painted highlights look better warm than pure white. Simple glass: dark vertical gradient + 1-2 diagonal
  reflection streaks.
- Hero prop sets (doors, lift leaves, cabinet fronts): one atlas per set with explicit UVs per cell; edges and
  backs get a plain material.

### Textures from photo grain + drawn shape
- A real photo (CC0 scan) gives grain and colour noise; anything with a defined shape is drawn or modelled on
  top: tile grids, wallpaper motifs, quilting, paint edges, seams, numbers, stickers. Photos alone look like
  wallpaper; drawn alone looks flat.
- Grade every photo to the project palette (tint by luminance, contrast ~0.35-0.6) so assets from different
  sources read as one place. High-contrast photos make walls noisy and speckled.
- Walls: one texture can cover floor to ceiling (u = along the wall / tile length, v = z / ceiling height). Then
  paint edges, stripes, drips, chips, scuffs at shoe/bag height and dust near the ceiling are drawn and uneven
  instead of being geometry splits. Make it horizontally seamless (paint an overlap and cross-fade), make a few
  variants and pick one per block of wall.
- Wallpaper: strips with seams, slight misalignment per strip, uneven fading, dirt toward the floor. Keep
  motifs small and low-contrast for their real size, or they look cartoonish.
- Floors: draw tiles with grout, per-tile colour jitter, chipped corners, a few cracked or replaced tiles.
  Big surfaces get bigger textures so the repeat is less visible.

### Breaking the repeat (the biggest visual win)
- Variants of the same material picked per block; never one tile repeated over tens of metres unbroken.
- Decals (alpha quads) on top: patches, cracks, stains, oil, manholes, leaves, moss/dirt blobs, trodden paths,
  puddles; indoors water stains, scuffs, scribbles, mould, soot over lamps, worn traffic paths, missing tiles.
- Fake AO strips: dark alpha-gradient strips (~0.3 m) on the floor along walls and on the ceiling along corners.
  Cheap, and it removes the flat look of interiors more than anything else (realistic projects: baked AO /
  lightmaps do the same job).
- Facades: streaks under sills, rust bleeding from brackets, splash grime on the plinth.
- One large texture beats many small ones where repetition is the problem; stochastic/random-rotation tiling
  does not work on regular patterns like tiles and bricks.
- Props and varied geometry on top of the worst areas also hide tiling.

### Wet surfaces
- Puddle = irregular alpha blob decal: dark water core + lighter wet rim, low roughness. A reflection must be
  masked to the puddle shape, not to its rectangle.

### Lighting
- One light per working fixture, emissive materials for windows, screens, buttons, indicators. Name lights that
  should animate in the engine (e.g. *_Flicker) so a script can find them. Leave a readable path through dark
  areas.

### Previews
- Smooth previews (denoise, high resolution) hide pixelation and noise; for a low-res target, also render small
  without denoise and upscale with nearest-neighbour to judge the real look (tools/render_preview.py mode lowres).

## 2. Technique that broke (headless bpy 5.x + bmesh)

### kt.check_all
- check_zfight flags coplanar overlapping same-facing faces even on objects passed in `ignore` (ignore only
  affects the floating check). Decals: give each kind its own layer 2 mm apart and never overlap two quads of
  the same layer; flat stacks need >= 4 mm between levels; randomly tilted quads are fine.
- Adjacent boxes that share corner vertices -> "double verts": end one of them 0.5 mm short.
- Trims meeting in a corner overlap: let the trims of one axis stop short by their depth at both ends.
- Thin parts flush with a wall (jamb lining, casing back) closer than ~4 mm to the wall plane get flagged.
- Wires or plates touching a beam or lamp top at the ceiling plane: stop 1.5 mm below it.
- Hinged leaves with clearance gaps: put them in `ignore` (floating), do not glue them to the frame.

### bmesh
- Concave ngon caps: triangulate with ngon_method='EAR_CLIP' after normal_update.
- create_cone along a direction: rotation_difference((0,0,1), dir), not to_track_quat (gave flipped caps).
- recalc_face_normals is unreliable on many small islands: orient each closed island by signed volume.
- Quads built one by one have separate verts: remove_doubles before making the mesh, or the check reports doubles.
- Explicit-UV faces (decals, fronts) can be flipped by normal recalculation: build them as separate quads and
  check the normal against the surface normal.

### Alpha decals
- A decal must be a single quad. A thin box with an alpha texture rendered as a grey square.
- Material: Image Texture Color -> Base Color, Alpha -> Alpha. In Unity they need Alpha Clipping or Transparent.

### Booleans and walls
- Wall shell = one box minus room boxes (rooms extended a few cm into neighbours they open onto) minus door,
  window and shaft cutters; EXACT solver.
- EXACT boolean adds an empty (None) material slot from the cutters: strip it before indexing materials.
- The same material twice in a mesh's material list breaks slots: build a unique list and index into it.
- Bisecting walls on planes that coincide with wall surfaces makes zero-area faces: skip planes on room
  boundaries; delete hidden top/bottom faces of the shell.
- Material by face: test point = face centre + normal * 6 cm, then find which room it is in.

### Files, imports, environment
- Never name a script after a stdlib module (inspect.py): bpy then crashes with "InitGoogleLogging twice".
- Appending objects from another .blend (libraries.load): bake LocRotScale into the mesh data yourself, and
  remove appended images/materials you replace, or large packed textures end up in the file.
- GitHub: 100 MB per file via git, 25 MB via web upload. Keep .blend files small: textures as external files
  with relative paths, nothing packed (unless the project wants packed files).
- Cloud sessions: blender.org, ambientcg.com, polyhaven.com may be blocked while PyPI and GitHub work.
  bpy via pip is very slow through the proxy: tools/install_bpy.sh downloads the wheel in 16 parallel ranges
  (~2 min). CC0 textures can come from github.com/Papyszoo/CC0-Public-Domain-Textures (256 px previews only:
  enough for low-res styles; realistic work needs full-res sets from the user).
- Preview renders: Cycles CPU, Standard view transform, low world strength, 480x300, 40 samples + denoise,
  then Read the PNG (tools/render_preview.py). A render takes 10-60 s.

## Sources
- Polycount, headlights as geometry vs texture: https://polycount.com/discussion/comment/1037078
- Polycount, painted warm highlights on glass: https://polycount.com/discussion/comment/1036736
- Polycount, breaking tiling (bigger texture, variants, decals, geometry): https://polycount.com/discussion/comment/2704129
- Polycount, vertex colour and decals against tiling: https://polycount.com/discussion/comment/2516644
- Unity forum, Repetitionless (stochastic tiling and its limits): https://discussions.unity.com/t/repetitionless-texture-tiling-remover/1705964
- Puddle reflection masking devlog: https://everythings-a-nail.mataroa.blog/blog/report-from-the-pits-puddles
