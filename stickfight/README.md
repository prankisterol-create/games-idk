# FURNACE & TIDE: an original 2D stick-fight animation

A 37.5-second, 899-frame, 24 fps stick-figure duel with a synthesised soundtrack. It is drawn frame by frame from authored key poses with a vector renderer, and was built after studying the uploaded Combat Gods–style reference video.

▶ **Watch:** [`output/preview/furnace_and_tide_1080p.mp4`](output/preview/furnace_and_tide_1080p.mp4) (1920×1080, H.264 + AAC).

> **Second film: DOOM vs SPIDER-MAN.** A 42-second night-rooftop fight built on the same engine, with costumed characters, powers, a water-tower set piece and a synthesised score.
> ▶ [`output/doom_vs_spiderman/preview/doom_vs_spiderman_1080p.mp4`](output/doom_vs_spiderman/preview/doom_vs_spiderman_1080p.mp4) · notes: [`docs/06_doom_vs_spiderman.md`](docs/06_doom_vs_spiderman.md) · see [below](#second-film-doom-vs-spider-man).

## Deliverables

| # | Deliverable | Where |
|---|---|---|
| 1 | Reference analysis (measured cut and flash statistics, technique notes) | [`docs/01_reference_analysis.md`](docs/01_reference_analysis.md) |
| 2 | Character model sheets (PNG + editable SVG) and character bible | [`output/modelsheets/`](output/modelsheets), [`docs/02_character_bible.md`](docs/02_character_bible.md) |
| 3 | Full storyboard: choreography with cause → effect per beat, plus 44 panels rendered from the real animation | [`docs/03_storyboard.md`](docs/03_storyboard.md), [`output/storyboard/`](output/storyboard) |
| 4 | Timed animation plan (keys, spacing, hit-stops, on 1s/2s ranges) and spacing charts | [`docs/04_timing_plan.md`](docs/04_timing_plan.md), [`output/timing/`](output/timing) |
| 5 | Animated frame sequences: every rendered frame, numbered, on contact sheets, plus a per-frame timeline log | [`output/sheets/`](output/sheets), [`output/timeline.csv`](output/timeline.csv) |
| 6 | Rendered video with sound | [`output/preview/`](output/preview) |
| 7 | Editable sources: pose library, sequence scripts, SVG drawings of every storyboard frame | [`src/`](src), [`output/storyboard/svg/`](output/storyboard/svg) |
| 8 | Tools to regenerate everything | [`src/`](src), see below |
| 9 | This file: structure and instructions | |
| 10 | Quality-control report and remaining limitations | [`docs/05_qc_report.md`](docs/05_qc_report.md) |

## File structure

```
stickfight/
  docs/        01-05 production documents
  output/
    preview/       final video (with audio)
    modelsheets/   KAI / SEN model sheets (.png + .svg)
    storyboard/    storyboard_N.jpg pages, panels/*.jpg, svg/*.svg (vector source frames)
    timing/        spacing charts timing_NN.png + spacing.txt
    sheets/        every rendered frame as numbered thumbnails (sheet_NN.jpg, 48 frames each)
    timeline.csv   per rendered frame: time, sequence, anim frame, hit-stop, positions, camera, shot notes
  src/
    rig.py         character builds, kinematics (FK + 2-bone IK), drawing
    poses.py       key-pose library (every drawing on the model sheets)
    engine.py      keyframe tracks: spacing curves, foot/hand pins, floor constraint, overlap lags,
                   on-2s ranges, root paths (ballistic arcs), hit-stop map, camera keys, hair physics
    fx.py          smears, sparks, dust, rings, debris, cracks, embers, glints, afterimages
    scene.py       sequence container + renderer (parallax background, camera, impact frames, post)
    author.py      authoring helpers (foot-driven placement, stances, shuffles, idles)
    titles.py      name and title cards
    seq01.py ...   the four sequences (choreography scripts with geometry checks)
    film.py        renders video / contact sheets / PNG frames / storyboard + SVG
    audio.py       procedural sound effects and score, cue-locked to the picture
    modelsheet.py  model sheets;  timing.py  spacing charts
    tools/         ref_stats.py (reference statistics), qc_scan.py (automated QC), timing_doc.py
```

## Regenerating

Requirements: Python 3.10+, ffmpeg, and `pip install pycairo numpy pillow scipy`.

```bash
cd stickfight/src
python3 modelsheet.py ../output/modelsheets                 # model sheets
python3 timing.py ../output/timing                          # spacing charts
python3 tools/qc_scan.py                                    # automated QC (expects "0 issues")
python3 tools/timing_doc.py ../docs/04_timing_plan.md       # timing plan tables
# picture (+ contact sheets, storyboard/SVG, timeline); ~4 min at 1080p
python3 film.py --all --res 1920x1080 --out /tmp/video.mp4 \
    --sheets ../output/sheets --storyboard ../output/storyboard --log ../output/timeline.csv
python3 audio.py /tmp/sound.wav                             # soundtrack
ffmpeg -i /tmp/video.mp4 -i /tmp/sound.wav -c:v copy -c:a aac -b:a 192k -shortest \
    ../output/preview/furnace_and_tide_1080p.mp4
```

Useful variants:
- `python3 film.py --seq s2 --out /tmp/s2.mp4 --debug`: one sequence with frame numbers burned in.
- `--range 160:185 --png /tmp/frames`: dump full-resolution PNGs of a frame range.
- `--res 3840x2160`: any resolution. Everything is vector until the final raster.

## Editing the animation

- **Change a drawing:** edit its parameters in `poses.py` (angles in degrees; see the conventions at the top of `rig.py`). Check it on the model sheet with `python3 modelsheet.py`.
- **Change timing or spacing:** each `track.key(frame, pose, ease=..., lock=...)` in a `seqNN.py` is one key drawing. Move frames, change `ease`, add a breakdown key, add `track.smear(...)`, `track.lag(...)` or `track.on_twos(...)`, or change `seq.hitstop(...)`.
- **Choreography geometry** (distances, contact points) is solved in each script. Run `python3 seq01.py` (or 02/03/04) to print the measured gaps and contact positions.
- **Vector drawings:** the SVGs in `output/storyboard/svg/` and `output/modelsheets/` open in Inkscape, Illustrator, Affinity, or a browser.

## Second film: DOOM vs SPIDER-MAN

A non-commercial fan animation on the same engine: [`docs/06_doom_vs_spiderman.md`](docs/06_doom_vs_spiderman.md) has the story beats, techniques, timing, sound and QC.

| What | Where |
|---|---|
| Video with sound (1920×1080) | [`output/doom_vs_spiderman/preview/`](output/doom_vs_spiderman/preview) |
| Model sheets (PNG + SVG) | [`output/doom_vs_spiderman/modelsheets/`](output/doom_vs_spiderman/modelsheets) |
| Storyboard rendered from the animation (pages, panels, SVG frames) | [`output/doom_vs_spiderman/storyboard/`](output/doom_vs_spiderman/storyboard) |
| Every rendered frame on contact sheets, plus the per-frame timeline | [`output/doom_vs_spiderman/sheets/`](output/doom_vs_spiderman/sheets), [`output/doom_vs_spiderman/timeline.csv`](output/doom_vs_spiderman/timeline.csv) |
| Sources | `src/heroes.py` (costumed builds), `src/heroposes.py`, `src/rooftop.py` (stage), `src/powers.py` (effects), `src/dv01.py`–`dv04.py` (sequences), `src/dv_audio.py`, `src/dv_modelsheet.py`, `src/dv_storyboard.py` |

```bash
cd stickfight/src
python3 dv_modelsheet.py ../output/doom_vs_spiderman/modelsheets
python3 tools/qc_scan.py --film doom                     # expects "0 issues"
python3 film.py --film doom --all --res 1920x1080 --out /tmp/dv_video.mp4 \
    --sheets ../output/doom_vs_spiderman/sheets --storyboard ../output/doom_vs_spiderman/storyboard \
    --log ../output/doom_vs_spiderman/timeline.csv
python3 dv_audio.py /tmp/dv_sound.wav
ffmpeg -i /tmp/dv_video.mp4 -i /tmp/dv_sound.wav -c:v copy -c:a aac -b:a 192k -shortest \
    ../output/doom_vs_spiderman/preview/doom_vs_spiderman_1080p.mp4
```

The engine changes the second film needed (costume painters, stages, overlays, FX items, dict paths) are opt-in hooks; FURNACE & TIDE renders as before.
