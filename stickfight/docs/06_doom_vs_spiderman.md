# DOOM vs SPIDER-MAN: production notes

A 42-second (1,011 rendered frames, 24 fps) 2D fight on a night rooftop above the city, made with the FURNACE & TIDE engine. It is a non-commercial fan piece: the characters are drawn from scratch in the engine's vector style and use no logos or official artwork.

▶ **Watch:** [`output/doom_vs_spiderman/preview/doom_vs_spiderman_1080p.mp4`](../output/doom_vs_spiderman/preview/doom_vs_spiderman_1080p.mp4)

## The fight, as cause and effect

Spider-Man wins with his head rather than his fists. Every beat sets up a later one.

| Seq | Frames | Beat | Why it happens / what it sets up |
|---|---|---|---|
| **D1 Arrival** | 0–239 | Doom crane-drops out of the sky on rocket boots past the moon and lands in a three-point crouch that cracks the roof. CU: his eye slits flare. A web line snaps onto the water-tower finial; Spider-Man swings in under the tank, front-flips over Doom's head with a half twist and lands behind him. | Establishes the **water tower** in the fighters' plane and Doom's power. |
| **D2 First exchange** | 0–189 | Doom fires a bolt at the crouching Spider-Man. Spider-sense: he is already airborne when the roof explodes. Web balls splat on Doom's **hex force field**. Doom drops the field to charge a bigger bolt overhead, and that is the opening: two web lines to the chest, a yank, a feet-first **dropkick** (impact frames). The impact flings Doom's arm back and the charged bolt goes off wild **into the tank**. | The holed tank gushes. The **pool spreads under Doom's feet** for the rest of the film. Webbing that sticks is planted (the splats on the field, on his chest). |
| **D3 The gauntlet** | 0–193 | Doom doesn't chase. He fires a barrage, and Spider-Man walks into it: lean back, hop (the roof blows up behind him), knee slide. Flying kick, blocked. Jab, parried. Cross, parried. The third punch is **caught**: the gauntlet discharges into him (dark impact frames), then Doom hurls him across the roof. | Shows that **the gauntlets discharge electricity**, and that Doom fights standing in the water. |
| **D4 Backfire** | 0–359 | Doom raises both gauntlets for the finisher. INSERT: his steel boots are in the water. CU: the lenses narrow. Thwip-thwip: **both palms plugged with webbing**. Doom fires anyway; the energy glows through the web, crawls back up his arms, and **backfires through the armour into the water**. The whole pool lights up. Doom goes down on one knee, smoking, then leaves on coughing rocket boots across the moon. Spider-Man waves him off, zips to the tower and perches on the finial against the moon. Title. | Pays off the leak (D2), the discharge (D3) and the webs that stick (D2). |

The full panel-by-panel storyboard is rendered from the real animation in [`output/doom_vs_spiderman/storyboard/`](../output/doom_vs_spiderman/storyboard).

## Characters

Model sheets (PNG plus editable SVG): [`output/doom_vs_spiderman/modelsheets/`](../output/doom_vs_spiderman/modelsheets).

- **Spider-Man** (1.71 m): small, fast, never square to the threat. Low wide stances, knees always bent, hands open, and the web-shooter sign (index and little finger out) when he fires. Red/blue split with webbing drawn on every red panel. The head is a sphere-mapped mask with angled white lenses whose openness is animated (they narrow on the "idea" beat).
- **Doctor Doom** (1.88 m): tall, upright, chin level, barely moves his feet. Steel armour, green tunic and skirt panels, belt with gold clasps, a hood, and a floor-length cape simulated by the engine's Verlet chain. The steel mask has glowing eye slits whose intensity is animated (flare, overload, gutter, relight).

## What was added to the engine

All engine changes are opt-in hooks. FURNACE & TIDE renders exactly as before, and `tools/qc_scan.py` still reports 0 issues for it.

- `rig.Build` gained optional `painter`, `anchor` and `chains` fields. A painter dresses the solved joints in every style ('normal', plus 'flat' and 'silhouette' for afterimages and impact frames).
- `scene.Sequence` gained `stage` (a pluggable background/foreground set with its own shadow drawing) and `overlay(f0, f1, fn, layer)`. Overlays are world-space drawings driven by the *animation* frame, so a bolt or web line meets its target on an exact frame and freezes with the characters during hit-stops. Energy crackle uses the render frame, so it keeps flickering through a freeze.
- `fx.FX` gained self-contained items (`fx.add(item)`); `fx.dust` takes a colour.
- `engine.Track.path` may return a dict, so a path can also drive rotation (the pendulum swing, the web-zip).
- `film.py --film doom` and `tools/qc_scan.py --film doom` select the film.

New modules: `heroes.py` (builds and painters), `heroposes.py` (pose library), `rooftop.py` (stage), `powers.py` (bolts, charge orbs, lightning, force field, webs and splats, rocket jets, water stream and puddle, spider-sense, smoke, fireballs, scorch marks), `dv01.py`–`dv04.py` (the four sequences, with geometry printouts), `dv_storyboard.py`, `dv_modelsheet.py` and `dv_audio.py`.

### Drawing techniques worth knowing

- **Two-tone limbs** are capsules clipped and cut square across the limb (`heroes.band`), so a glove or boot edge stays crisp at any angle.
- **Torso panels** (Spider-Man's red chest and front panel, Doom's belt) are regions in (along-spine, across-spine) coordinates mapped onto the solved, curved spine.
- **Masks** are decals on a unit sphere, projected with a fixed 32–36° "cheat" toward camera that fades out as the body itself turns to face the camera. The face reads in profile, and lenses, slits and web lines foreshorten correctly in 3/4 view.
- **Set-piece continuity across sequences:** the holed tank, the stream, the growing pool (`dv02.puddle_half`), scorch marks and fallen webbing are re-created in later sequences from the previous sequence's recorded `state`.

## Timing

| Seq | Anim frames | Rendered | Hit-stops (frame: extra frames) | Impact frames | Camera cuts |
|---|---|---|---|---|---|
| D1 | 240 | 243 (10.1 s) | 58:3 (landing) | none | 97, 129, 182, 216 |
| D2 | 190 | 197 (8.2 s) | 25:2 (blast), 82:5 (dropkick) | 82: focus, white | 122, 159 |
| D3 | 194 | 205 (8.5 s) | 50:3, 59:2, 64:2 (blocks), 75:4 (shock) | 50: white; 75: dark ×2 | 140, 169 |
| D4 | 360 | 366 (15.3 s) | 86:6 (backfire) | 86: white, dark, white | 20, 34, 44, 58, 140, 177, 305 |

Action runs on 1s, held beats on 2s, as in FURNACE & TIDE. The per-rendered-frame log, with positions, camera and shot notes, is [`output/doom_vs_spiderman/timeline.csv`](../output/doom_vs_spiderman/timeline.csv). Every frame is on the contact sheets in [`output/doom_vs_spiderman/sheets/`](../output/doom_vs_spiderman/sheets).

## Sound

Everything is synthesised by `dv_audio.py`, building on `audio.py`, and is cue-locked to the rendered frames through each sequence's hit-stop map.

- **84 cued effects**, from about 30 synthesised sounds: web thwips, spider-sense shimmer, charge whines, bolts, blasts, force-field rise/ping/fall, struck-metal clanks, electric crackle, web splats, rocket roar (steady and sputtering), water gush, splashes and steam.
- **Ambience:** wind, a low city hum, two distant sirens, and the running leak from the moment the tank is holed.
- **Score:**
  - Doom's motif: low brass, D–F–E–D.
  - Spider-Man's motif: a plucked F-major arpeggio and a rising hero line.
  - A 132 bpm bass ostinato under the fighting, whose level follows the action.
  - A tritone stab on the shock.
  - A riser into the backfire that cuts to silence on impact.
  - The hero line in full over the final perch and the title.

## QC

`python3 tools/qc_scan.py --film doom` checks every animation frame for ground penetration, limb-length drift, root teleports and torso overlap. It reports **0 issues**.

Deliberately fast travel (the rocket descent and exit, the bottom of the swing, the throw, the web-zip) is declared per sequence in `seq.fast`. Hidden actors are skipped. While building the film, the scan caught two real bugs: a 1.4 m pop out of the knee slide (D3) and a one-frame return to the origin after Doom flies off (D4). Both are fixed.

## Known limitations

- The soundtrack was checked by loudness curve and spectrogram, not by ear.
- Capes are a single Verlet chain drawn as a ribbon. In fast backward slides the cape can trail ahead of Doom like a scarf. That is physically motivated, but less elegant than a hand-keyed cape.
- Spider-Man's lens openness, Doom's eye glow and all effects are 2D; there is no lighting from the energy onto the characters beyond glows and the puddle reflection.
- Only the near hand changes shape on close-ups; fingers are not individually animated.

## Regenerating

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

Useful variants: `python3 film.py --film doom --seq d2 --out /tmp/d2.mp4 --debug` renders one sequence with frame numbers burned in. `python3 dv02.py` (or 01/03/04) prints a sequence's solved geometry (contact points, gaps, where the leak lands).
