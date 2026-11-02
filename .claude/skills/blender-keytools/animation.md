# Animation reference (read once per chat before planning or changing animation)

Based on the 12 principles from Thomas & Johnston "The Illusion of Life" and common
keyframe practice (Williams "The Animator's Survival Kit"), rewritten as working rules
for bone animation in Blender -> Unity. Frame numbers assume 24 fps; check `anim_report`
for the real fps and scale timings (30 fps: x1.25).

## Workflow
1. Copy first: `dup_action(rig)` unless Key asks to edit the original.
2. Plan in text before keying: a short table `frame | pose | intent` (key poses, then
   breakdowns). Show it to Key if the motion is new or ambiguous.
3. Block key poses in CONSTANT (`set_interp(..., "CONSTANT")`), check with `pose_at`
   or one `contact_sheet` (UI only).
4. Switch to BEZIER, add breakdowns, fix spacing and arcs. Contacts / sharp direction
   changes: VECTOR handles. Apex, slow parts: AUTO_CLAMPED.
5. Verify without screenshots: `motion()` (arc = turn angles change smoothly, no zigzag;
   spacing = v ramps up/down where intended), `anim_check()` (flips, jumps, feet in floor).
6. Final look: one contact sheet or viewport screenshot.

## The 12 principles as rules
1. **Squash & stretch** - shape reacts to force, volume stays the same (`squash_stretch`:
   one axis x f, the others / sqrt f). Squash on impact (perpendicular to the surface),
   stretch along the motion on the fastest frames, normal shape at slow parts (apex).
   Amount = material: rubber ball ~0.6-0.75 squash, wood/stone almost none.
2. **Anticipation** - a small opposite move before the action (crouch before jump, wind-up
   before throw). Bigger/heavier action -> longer anticipation. Quick: 2-4 f, big: 6-12 f.
   Removing it makes motion feel sudden or mechanical.
3. **Staging** - one clear action at a time, readable silhouette from the game camera.
4. **Pose to pose / straight ahead** - keyframing = pose to pose. Chaotic secondary parts
   (hair, cloth, tentacles) work better straight ahead or simulated.
5. **Follow-through & overlap** - parts don't stop together. The main mass leads, attached
   parts (head, arms, tail, hair, antenna) arrive 1-3 frames later and overshoot a bit.
   In keys: offset child bones along the chain (`move_keys(rig, offset=1..3, bones=child)`),
   bigger offset further down the chain.
6. **Slow in / slow out** - more frames near extremes, fewer in the middle. Exceptions:
   falling accelerates until impact (no ease into the ground), machines can be linear,
   impacts are sudden.
7. **Arcs** - living things move along arcs. Rotate from joints instead of translating;
   if a translated path goes straight between keys, add a breakdown key off the line.
   Check the tip of the chain (`motion(rig, bone, point="tail")`).
8. **Secondary action** - small supporting motion (breath, blink, finger curl) that never
   competes with the main action.
9. **Timing** - frame count = weight and mood. Same distance in fewer frames = lighter,
   faster, more energetic.
10. **Exaggeration** - push key poses past realistic, consistently across the shot.
11. **Solid drawing** (3D: weight and balance) - center of mass over the support, no
    "twins": after a mirrored copy (`copy_keys(mirror=True)`) offset one side 1-2 frames
    and vary amplitude.
12. **Appeal** - clear, readable, interesting poses; avoid stiff symmetric ones.

## Physics timing (exact, g = 9.81)
Fall time t = sqrt(2h/g). At 24 fps:
| height | fall | frames |
|---|---|---|
| 0.25 m | 0.23 s | ~5.5 |
| 0.5 m | 0.32 s | ~7.7 |
| 1 m | 0.45 s | ~10.8 |
| 2 m | 0.64 s | ~15.3 |
Airtime of a jump with apex h = 2t. Bounce n+1 with height ratio r: time scales by sqrt(r).

## Recipes
**Bouncing ball** - Z: contacts with VECTOR handles (sharp V), apex AUTO_CLAMPED (round).
X: near-constant speed (LINEAR), slowing slightly per bounce. Each bounce lower
(rubber ~0.5-0.7 of previous height) and shorter (sqrt of that). Squash 1-2 frames at
contact with the bottom touching the floor (pivot at the bottom or lower the center),
stretch on the frames just before and after contact, round at the apex.

**Character jump** - anticipation crouch (hips down, arms back) -> push-off (extended,
stretch, 1-2 f) -> air: root on a parabola, horizontal speed constant, ease only at the
apex, legs tuck, arms/spine/head overlap -> landing contact -> absorb (compress 2-4 f,
often deeper than the anticipation) -> settle with a small overshoot. Feet stay planted
until push-off and from contact (`anim_check(ground=..., feet=[...])`).

**Walk** - per step: contact, down (weight lowest), passing, up (highest), next contact.
Normal walk ~12 f per step (24 per cycle), brisk ~8-10, run 6-8 with a flight phase.
Hips bob twice per cycle and shift over the supporting leg; arms swing opposite to legs,
lagging 1-2 f. Loop with `cycle(rig, end=<last frame>)` so first = last.

**Settle / overshoot** - pass the final pose and come back in 1-3 decreasing waves.
BACK/ELASTIC interpolation works for cartoony or mechanical cases.

**Weight** - heavy: long anticipation, slow start, abrupt stop with a small shake, little
squash. Light: quick, floaty, flutter, long follow-through.

**Moving hold** - a character never freezes completely: drift a few percent during holds.

**Unsettling motion (horror)** - break the rules on purpose: no anticipation, linear
constant speed, a hold that is too long with no breathing, overlap in the wrong order
(tip leads the root), a joint snapping on one frame.

## Blender -> Unity notes
- Unity inherits scale fully. For squash/stretch put the scale on a bone without children
  or keep children at Inherit Scale = Full, otherwise Blender and Unity look different.
- Constraints / IK do not export: `bake_anim` to a new action first.
- Each action becomes a clip: `export_fbx(sel, path, anim=True)` (all actions + NLA strips).
- In place vs root motion: decide with Key; for root motion animate the root bone forward.
- Quaternion bones avoid gimbal problems; `anim_check` finds sign flips.
