# Postscript art repo: project status

Read this at the start of every new chat (then ART_DIRECTION.md before modeling). Last updated: 2026-11-03.
Key works from claude.ai cloud sessions (no Blender UI here): everything is built headless with bpy
from generator scripts and pushed to `main` so Key can `git pull` and open the .blend files.

## Workflow (agreed with Key)
- Answer in Russian, names in files in English (CLAUDE.md).
- Push results to `main` (Key asked for it): commit on the session branch, then
  `git push origin <session-branch>:main` (fast-forward; check `git merge-base --is-ancestor origin/main HEAD` first).
- Before saying "done": `kt.check_all` must print ALL OK, then preview renders, then commit + push.
- First thing in a new cloud session: `bash levels/_generator/setup_headless.sh` (installs bpy 5.2, texture list).
- Art direction: PS1-style horror like Voices of the Void / KLETKA, night, late autumn (no snow),
  dread without jump scares, everyday Soviet panel-block details, small wrong things.
- Art direction for this game (PS1 target, palette, Soviet details, storytelling, sizes): `ART_DIRECTION.md`.
  Generic craft and Blender traps (any project): `.claude/skills/blender-keytools/art_and_gotchas.md`.

## What exists (levels/)
| File | What it is | Rebuild |
|---|---|---|
| Street_Night.blend | Night yard: 9-storey panel block (3 entrances, lit one at x=22.5), 5-storey khrushchevka, road, sodium lamps, playground, trash area, garages (one open), 4 modelled cars + wreck on bricks, trees, decals, distant blocks, Panels2 lods as background. Spawn_Player at the garages, Exit_Entrance at the lit door. ~72k tris | `build_street.py <out>` |
| Floor_Ochre_Landing.blend | v2: landing layout (lift hall + side corridor + tambour), ochre oil paint, metlakh checker, caged bulbs, pipes, pram | `build_floor_v2.py landing Ochre <out>` |
| Floor_Mint_Ring.blend | v2: ring corridor around the lift core, hospital mint, terrazzo, fluorescent tubes, benches, plants | `build_floor_v2.py ring Mint <out>` |
| Floor_Panel80_Corner.blend | v2: L-shaped floor, 80s chipboard wainscot + wallpaper, parquet-print linoleum, globe lamps | `build_floor_v2.py corner Panel80 <out>` |
| Floor_Decay_Corridor.blend | v2: 42 m corridor, peeling paint, concrete, debris, leaks with buckets, mould, emergency light | `build_floor_v2.py corridor Decay <out>` |
| Apt_Lived.blend | 1-room flat (hall, room, kitchen, bath, pantry), fully furnished Soviet interior | `build_apartment.py Lived <out>` |
| Apt_Empty.blend | same flat stripped for renovation: torn wallpaper over newspaper, ladder, paint cans | `build_apartment.py Empty <out>` |
| Apt_Covered.blend | anomaly: everything under sheets, mirror covered, windows papered, one chair, ~340 letters on the floor | `build_apartment.py Covered <out>` |
| Apt_Ceiling.blend | anomaly: the room's furniture hangs from the ceiling, chandelier on the floor | `build_apartment.py Ceiling <out>` |
| Apt_Long.blend | anomaly: 14 m hallway, identical doors/racks/mirrors, lit kitchen at the end | `build_apartment.py Long <out>` |
| Floor_Corridor_Blue / Corner_Blue / Ring_Blue.blend | v1 floors, blue/concrete style (older, flatter look) | `build_level.py <corridor/corner/ring> blue <out>` |
| Floor_LiftHall.blend | v1 green corridor (oldest). Generator kept only as reference in `_generator/legacy/` | not maintained |
| ../Panels1.blend, ../Panels2.blend | Key's downloaded reference models (exteriors only). Panels2 lods are reused in Street_Night | do not modify |

All floors: lift A works (Exit_LiftA marker), lift B is broken (doors ajar, empty shaft, sign), stair door
locked, Spawn_Player marker, a "wrong" door painted like the wall in some layouts, muddy footprints
leading to it, lights in collection `Lights` (names *_Flicker = flicker in Unity).
v2 lift doors are 1.0 m wide (Key found 0.8 m too narrow).

## Generators (levels/_generator/)
- `kit.py`: shared helpers for v2 interiors: materials (box / wall / explicit UV modes), prisms/boxes/cylinders,
  wall frames `wf=(axis, c, sign)`, boolean cuts, wall occupancy (no overlaps), wall segments, decals,
  `finish()` = UV + kt.check_all + save.
- `build_floor_v2.py`: corridor themes (THEMES dict: door atlas cells, lamp type, light colour, extras) x layouts
  (`layout_landing` here; corridor/corner/ring come from build_level.py).
- `build_apartment.py`: apartment plan + furniture library + variants.
- `build_street.py` (+ `car_spec.py`): the street. Reuses build_level.py helpers via exec.
- `build_level.py`: v1 floors (styles blue/green) and the layout data reused by v2.
- `paint_textures.py`: street cars, wheels, plates, outdoor decals, props (`python3 paint_textures.py cars decals props`).
- `paint_interior.py`: v2 corridor walls/floors/ceilings/doors/lifts/props/decals and all apartment textures
  (`python3 paint_interior.py corridor apartment`). Textures are linked by relative path, so repainting
  updates the .blend files without rebuilding.
- `texture_sheet.py`: contact sheet of CC0 bases. Preview renders: `.claude/skills/blender-keytools/tools/render_preview.py`
  (mode preview or lowres); bpy installer: `.claude/skills/blender-keytools/tools/install_bpy.sh` (called by setup_headless.sh).
- `legacy/`: one-off texture prep scripts of the v1 textures (T_Wall_*, T_Ext_*, ...) and the Floor_LiftHall builder.
- Rebuild everything: run each builder with the output path `levels/<File>.blend` (absolute path), from any dir.

## Textures (levels/textures/, 244 PNG)
- Every file has a row in `SOURCES.md` (CC0 base + what was drawn). Keep that up to date.
- Prefixes: `T_IW_/T_IF_/T_IC_<Theme>` corridor wall/floor/ceiling, `T_IDoors_/T_ILift_<Theme>` door atlases,
  `T_IP_` corridor props, `T_ID_` interior decals, `T_AW_/T_AF_/T_AC_/T_A_` apartment, `T_Ext_` street,
  `T_Car_` cars, `T_Decal_` outdoor decals, `T_Prop_` street props, `T_NumberPlates_<File>` per-floor plates.
- Size 64-256 px, 15-bit colour, Closest filtering. Bases: 256 px previews from
  github.com/Papyszoo/CC0-Public-Domain-Textures (ambientCG, Poly Haven, cgbookcase, ShareTextures).

## Unity notes (for Key)
- Textures: Filter Mode Point, Compression None. Alpha decals, tulle, leaves need Alpha Clipping or Transparent.
- PS1 look comes mostly from a low internal render resolution + point filtering (+ optional PS1 vertex shader).
- Not done yet: FBX export (kt.export_fbx exists), colliders, apartment/corridor connection is a scene change.

## Open questions / next steps
- Waiting for Key: halve the level textures (32-50 px/m, 16 colour levels, keep text sharp) for a cruder PS1 look,
  or leave it to Unity Max Size. Comparison shown in chat (preview vs ps1 render vs halved textures).
- Ideas not built yet: entrance vestibule + stair flights between the street and a floor, the Flower /
  Mr. Nobody / Trader / Greed characters, morphing props with shape keys, more apartment anomalies,
  bringing v1 floors up to the v2 look.
- Floor_Decay_Corridor lift hall is almost dark (only emergency light): intended, may need a flashlight.

## History (2026-11-02 .. 03)
1. Checked Key's Panels1/2.blend (exteriors only, no interiors). Installed bpy headless.
2. Floor_LiftHall (v1, green), then rebuilt bigger (42 m corridor, 22 doors, anomalies).
3. Blue/concrete style + 3 layouts (corridor, corner, ring) via build_level.py.
4. Street_Night, then upgraded: modelled cars with painted atlases, alpha puddles, decals against tiling, better props.
5. v2 interiors from scratch: kit.py, 4 themed floors, 5 apartments, painted floor-to-ceiling walls, fake AO.
6. Lifts widened to 1.0 m. Skill got a generic art_and_gotchas.md + tools; Postscript rules in ART_DIRECTION.md; this status file.
