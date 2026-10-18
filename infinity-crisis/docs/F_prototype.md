# Deliverable F: Technical Prototype

## What exists

| Item | File | Status |
|---|---|---|
| **Sequence 1 "The Sky Breaks", 2.39:1 scope master** | `output/s01_prototype/infinity_crisis_s01_scope_1920x804.mp4` | Rendered, 58.0 s, 24 fps, H.264 + AAC |
| Sequence 1, 16:9 open-gate version | `output/s01_prototype/infinity_crisis_s01_16x9_1920x1080.mp4` | Rendered (same picture, open gate) |
| Storyboard frames from the prototype (2 per shot) | `output/s01_prototype/storyboard/` + `contact_sheet.jpg` | Rendered |
| Temp soundtrack (synthesised, cue-locked) | `prototype/s01/audio.py` | Generated into both videos |
| Renderer | `prototype/s01/render.py` | Reads shot order and durations from `data/shots/s01.yaml` |
| Blender layout builder | `prototype/blender/build_layout.py` | Verified with Blender 5.2 (bpy): 11 scenes, 278 cameras with lenses and timeline markers, collections per the brief, the Eternity Engine asset, labelled proxy figures |

## What it is and isn't

This is a **procedural 2D previs**, not the final CGI.

- **Shows:** the opening's timing, shot order, composition, camera moves, colour script, lighting intent and sound design, frame-accurate to the storyboard.
- **Characters:** drawn as stylised silhouettes and profiles (the woman, Dr. Okafor, the hands, Thanos).
- **Dialogue:** Thanos's two lines appear as **captions**. No voice was recorded or synthesised.
- **Labelling:** every frame carries a small `S01 PREVIS PROTOTYPE <shot>` label inside the scope safe area.

## How it was built

1. `render.py` has one function per shot (`S01_010` ... `S01_180`). Each draws its frame from vector shapes (pycairo) and per-pixel numpy layers:
   - spectral-noise clouds and a procedural Earth with the real US East Coast and city-light hubs
   - parallax skyline layers and a river reflection
   - a one-point-perspective street
   - the rupture ring with a propagating hex lattice and a swirl cloud vortex
   - rain with **freeze** and **reverse** modes (S01_080)
   - a ship swarm, the Silent Throne, and Thanos from behind and in profile
2. A post stage applies a filmic tone curve, vignette, clumped grain, captions and the prototype label.
3. Frames render in parallel and pipe into ffmpeg. The 16:9 picture is rendered open gate; the scope master is its centre 1920 × 804 extraction, so both deliverables come from one render.
4. `audio.py` synthesises every cue at the shot-list times:
   - digital silence for 2.5 s, 30 Hz pressure, the distant choir, wind, rain and city
   - the shimmer at the point of light, the sub swell and glass hum, three car alarms, the crack
   - local silence during the rain freeze, birds, the jet, the observatory beeps, the heartbeat
   - drums, engine drones, the Thanos motif on low brass (D–B♭–A) over a D-minor choir, wind on the prow
   - the riser, **silence on the flash and the boom 14 frames later**

## Regenerate

```bash
pip install pycairo numpy scipy pillow pyyaml      # plus ffmpeg
cd prototype/s01
./make_video.sh                  # renders, builds audio, muxes both versions (~15 min at 1080p, 4 cores)
python3 render.py --scale 0.5 --png /tmp/frames --shots S01_060   # quick look at one shot
pip install bpy && python3 ../blender/build_layout.py --out layout.blend
```

## QC of the prototype

- **Shot list:** 18 shots, 1,392 frames, durations identical to `data/shots/s01.yaml` (the renderer reads them).
- **Picture:** every shot was reviewed on contact sheets across three iterations. Fixed along the way:
  - The Earth showed a half-lit day side and a straight-line coast; it now has a night side, a dawn rim and real geography.
  - The cloud deck hid the city.
  - The skyline was too tall.
  - The canyon walls hid the rupture.
  - The woman's head read as bald, and the scientist's outline was ghost-like.
  - Thanos's rim light ran around the whole silhouette.
- **Sound:** checked by level, not by ear:
  - 0–2.5 s digital silence; the freeze section about 10 dB under the surrounding bed
  - true silence between the flash (57.25 s) and the boom (57.83 s)
  - peak −1 dBFS
  - the mix has not been auditioned.
- **Known limits:**
  - stylised figures; no lip-sync
  - captions instead of voice
  - the street shot is graphic rather than photoreal
  - camera moves are 2D approximations of the specified 3D moves (push, tilt, truck)
