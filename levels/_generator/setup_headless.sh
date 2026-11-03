#!/usr/bin/env bash
# One-time setup of a cloud session for this repo: bpy (generic installer from the blender-keytools skill)
# + the CC0 texture file list used by the painter scripts.
set -e
HERE="$(dirname "$(readlink -f "$0")")"
bash "$HERE/../../.claude/skills/blender-keytools/tools/install_bpy.sh" 5.2.3
python3 -c "import sys; sys.path.insert(0, '$(dirname "$(readlink -f "$0")")'); import paint_textures as PT; PT.ensure_list(); print('CC0 texture list ready')"
