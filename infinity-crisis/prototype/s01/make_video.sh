#!/bin/sh
# Render Sequence 1 (picture + sound) and build both deliverables plus storyboard frames.
set -e
cd "$(dirname "$0")"
TMP=${TMPDIR:-/tmp}
python3 render.py --out "$TMP/s01_picture_16x9.mp4"
python3 audio.py "$TMP/s01_sound.wav"
python3 finish.py "$TMP/s01_picture_16x9.mp4" "$TMP/s01_sound.wav"
