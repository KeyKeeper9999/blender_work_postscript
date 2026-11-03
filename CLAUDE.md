# Postscript art repo

Key (Bogdan) is a game design student. This repo holds Blender assets for **Postscript**,
his 2-week horror game for the Game a Week course. Answer in Russian; everything inside
the game and the files (object, material, collection names) in English.

## Stack
Blender 5.2, Unity 6.3 (URP, Input System), Cinemachine 3, FMOD 2.03. 1 Blender unit = 1 m.

## How to work
- New chat: read `PROJECT_STATUS.md` first (what exists, how to rebuild, open questions, Key's preferences)
  and keep it updated when you finish something.
- Before modeling for this game read `ART_DIRECTION.md` (PS1 target, palette, Soviet details, storytelling,
  sizes). The skill stays generic; project-specific rules live in that file.
- For any Blender task use the `blender-keytools` skill in `.claude/skills/` (read its
  SKILL.md first). If there are no Blender MCP tools, follow its "Headless mode" section.
- Keep it simple: build only what was asked, no extras "for later".
- Do not touch originals unless the task is to change them: save results as a new .blend
  or a new collection, never overwrite Key's file silently.
- When done: `kt.check_all`, one small preview render, then git commit + push. Report in
  2-3 lines: which file, what was made, anything left open.
- "How is it usually done" questions: search first, don't present guesses as facts.

## Blender quality rules
- Nothing floats unless intended, no z-fighting, no garbage faces inside.
- Objects are logically separate; pivots of moving parts (doors, drawers, windows, lids)
  on their rotation/movement axis.
- Applied scale, no negative scale, clean names.
- Unity-ready: real-world size, reasonable poly count for a first-person game,
  textures power of two, data maps Non-Color.

## Postscript (context)
- Existential SCP-like horror, no jump scares. Our reality slowly changing in strange ways.
- Setting: a post-Soviet panel apartment block (panelka) at night: stairwell, landings,
  several apartments, maybe roof/yard. Player is a postman delivering letters to tenants.
- Atmosphere: dread comes on its own, nothing is explained, long pauses on unimportant
  things, small light radius, sound tells more than the image, fog.
- Characters: a Flower (immortal until seen, then wilts), Mr. Nobody, a Trader with a
  triangle for a head, Greed (a huge red royal mantle with an eye and a crown of money).
- Planned: modular panelka kit (stair flight, landing with apartment doors, typical
  apartment), props that can morph (shape keys with identical topology for Unity).
- Visual tone: everyday Soviet details (tiles, paint on walls, mailboxes, radiators,
  wires), worn and slightly wrong.
