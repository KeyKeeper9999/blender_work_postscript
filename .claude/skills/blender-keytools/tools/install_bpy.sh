#!/usr/bin/env bash
# Install Blender as a Python module (bpy) in a headless/cloud session.
# pip downloads the ~400 MB wheel very slowly through some proxies; 16 parallel ranged curl requests take ~2 min.
# usage: bash install_bpy.sh [version]   (default 5.2.3; needs the matching Python, 3.13 for bpy 5.2)
set -e
BPY_VERSION=${1:-${BPY_VERSION:-5.2.3}}
if python3 -c "import bpy" 2>/dev/null; then echo "bpy already installed: $(python3 -c 'import bpy; print(bpy.app.version_string)')"; else
  VER=$BPY_VERSION
  URL=$(curl -sS "https://pypi.org/pypi/bpy/$VER/json" | python3 -c "import json,sys; print([f['url'] for f in json.load(sys.stdin)['urls'] if 'manylinux' in f['filename'] and 'x86_64' in f['filename']][0])")
  D=/tmp/claude-0/whl; mkdir -p $D; cd $D; rm -f part*
  S=$(curl -sSI "$URL" | awk 'tolower($1)=="content-length:"{print $2+0}' | tail -1); N=16; P=$(( (S + N - 1) / N ))
  get() { i=$1; f=part$(printf %02d $i); a=$((i * P)); b=$((a + P - 1)); [ $b -ge $S ] && b=$((S - 1)); need=$((b - a + 1))
    for t in 1 2 3 4 5 6; do have=$(stat -c%s $f 2>/dev/null || echo 0); [ $have -ge $need ] && return; curl -sS -r $((a + have))-$b "$URL" >> $f; done; }
  for i in $(seq 0 $((N - 1))); do get $i & done; wait
  W=$(basename "$URL"); cat part* > "$W"; rm part*
  python3 -c "import zipfile,sys; zipfile.ZipFile(sys.argv[1]).testzip() or print('wheel ok')" "$W"
  pip install --break-system-packages -q "./$W"; rm -f "$W"
  python3 -c "import bpy; print('bpy', bpy.app.version_string)"
fi
