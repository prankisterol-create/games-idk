# INFINITY CRISIS: Avengers & Justice League vs. Thanos

A complete production package for a 12-minute (12:12) theatrical-style CGI crossover short, plus a **rendered prototype of the opening sequence** with sound. This is a non-commercial fan concept; the characters belong to Marvel/Disney and DC/Warner Bros. Discovery.

▶ **Watch the Sequence 1 prototype:** [`output/s01_prototype/infinity_crisis_s01_scope_1920x804.mp4`](output/s01_prototype/infinity_crisis_s01_scope_1920x804.mp4) (2.39:1), or the [16:9 version](output/s01_prototype/infinity_crisis_s01_16x9_1920x1080.mp4).

> The prototype is a **procedural 2D previs** of "The Sky Breaks" (58 s). It has stylised figures, captions in place of recorded dialogue, and a synthesised temp score. No final CGI film exists. See [Deliverable F](docs/F_prototype.md).

## Deliverables (in the brief's order)

| | Deliverable | Where |
|---|---|---|
| A | Production overview: story, runtime, tone, visuals, specs, method, assumptions, capability audit | [`docs/A_production_overview.md`](docs/A_production_overview.md) |
| B | Complete screenplay (Fountain source + formatted 32-page PDF) | [`docs/B_screenplay.fountain`](docs/B_screenplay.fountain), [`docs/B_screenplay.pdf`](docs/B_screenplay.pdf) |
| C | Detailed storyboard: **278 shots**, all 13 fields per shot, timecodes, per-shot continuity | [`docs/C_storyboard/`](docs/C_storyboard/README.md) |
| D | Character and asset list; character continuity sheet | [`docs/D_characters_and_assets.md`](docs/D_characters_and_assets.md), [`docs/D_continuity_sheet.md`](docs/D_continuity_sheet.md) |
| E | Animation production plan | [`docs/E_animation_plan.md`](docs/E_animation_plan.md) |
| F | Technical prototype: Sequence 1 render + sound; Blender layout builder | [`docs/F_prototype.md`](docs/F_prototype.md), [`output/s01_prototype/`](output/s01_prototype), [`prototype/`](prototype) |
| G | Video-generation prompts: one self-contained prompt per shot (278) | [`docs/G_video_prompts/`](docs/G_video_prompts/README.md), [`output/edit/prompts.jsonl`](output/edit/prompts.jsonl) |
| H | Editing and audio plan, EDL, runtime | [`docs/H_edit_and_audio_plan.md`](docs/H_edit_and_audio_plan.md), [`output/edit/`](output/edit) |
| I | Quality-control checklist + automated QC | [`docs/I_qc_checklist.md`](docs/I_qc_checklist.md), [`tools/qc_shots.py`](tools/qc_shots.py) |

## The film at a glance

| # | Sequence | Time | Shots |
|---|---|---|---|
| 1 | The Sky Breaks | 0:58 | 18 |
| 2 | The Avengers Respond | 0:58 | 20 |
| 3 | The Titan Enters the War | 1:00 | 25 |
| 4 | The Justice League Arrives | 1:06 | 28 |
| 5 | The First Great Combined Battle | 1:30 | 34 |
| 6 | Thanos Turns the Tide | 1:01 | 25 |
| 7 | The Plan | 0:48 | 15 |
| 8 | The War for Reality | 1:43 | 39 |
| 9 | Superman, Thor & Wonder Woman vs. Thanos | 1:05 | 25 |
| 10 | The Final Gambit | 1:05 | 28 |
| 11 | The Aftermath | 0:55 | 21 |
| | **Total** | **12:12** | **278** |

## How it fits together

All shot data lives in YAML; every document, prompt, EDL and the prototype's timing are generated from it, so nothing drifts.

```
data/
  shots/s01..s11.yaml   every shot: the 13 fields + location, characters, scene
  characters.yaml       design bible (canonical design text used in every prompt), forces, environments
  continuity.yaml       per-sequence character state + shot-level events (damage, props, exits)
  locations.yaml        location descriptions
tools/
  qc_shots.py           automated QC (schema, continuity, dialogue vs screenplay, scenes)  -> "0 issues"
  build_docs.py         storyboard, continuity sheet, prompts, EDL, runtime
  fountain_pdf.py       screenplay PDF
  common.py             loaders, timeline, Fountain parser
prototype/
  s01/render.py         Sequence 1 renderer (one function per shot)
  s01/audio.py          synthesised, cue-locked soundtrack
  s01/finish.py         mux 16:9 + scope, storyboard frames, contact sheet
  s01/make_video.sh     all of the above
  blender/build_layout.py  Blender scenes / cameras / markers / Engine asset from the shot list
docs/                   deliverables A-I (C, D-sheet and G are generated)
output/                 prototype videos and frames; edit files
```

## Regenerate

```bash
pip install pycairo numpy scipy pillow pyyaml        # + ffmpeg; `pip install bpy` for the Blender builder
python3 tools/qc_shots.py                            # expect "0 issues"
python3 tools/build_docs.py                          # storyboard, continuity sheet, prompts, EDL
python3 tools/fountain_pdf.py                        # screenplay PDF
sh prototype/s01/make_video.sh                       # Sequence 1 prototype (~15 min at 1080p on 4 cores)
python3 prototype/blender/build_layout.py --out layout.blend
```

**To change the film,** edit the YAML (or the screenplay), run `qc_shots.py`, then `build_docs.py`. The QC will refuse dialogue that no longer matches the screenplay, characters that jump between locations, damage that disappears, and props that vanish.
