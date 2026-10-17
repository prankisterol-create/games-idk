# 01 — Reference Motion Analysis

**Source:** uploaded file `videoplayback.mp4` (Combat Gods–style stick fight), 640×360, 24 fps, 8:00.05, 11,520 frames.
**Method:** frames extracted with ffmpeg and examined as contact sheets: a 4-second overview of the whole film, plus every frame of six windows (1:08–1:18.4, 1:19.6–1:21.1, 3:19.9–3:21.4). Cut timing and impact-frame statistics were measured by computing mean absolute luminance difference between consecutive frames at 160×90 over the whole video (script: `src/tools/ref_stats.py`, kept for reproducibility).

Every statement is tagged:
- **[OBS]** seen directly in extracted frames
- **[MEAS]** computed from frame data
- **[EST]** inferred or estimated, not verified frame by frame

No reference frames are stored in this repository. The new film reuses principles only, not characters, designs, or choreography.

---

## 1. Structure of the reference (chronological)

| Time | Content | Notes |
|---|---|---|
| 0:00–0:24 | Merch cards, seizure warning, black | Not animation. Ignored. |
| 0:28–0:44 | Character title cards (gold "Shinji", maroon "Jun"), giant-scale close-ups, glowing eyes | [OBS] Each fighter is introduced in close-up before any wide shot. Scale contrast is used from the first second. |
| 0:48–1:08 | Walk-on in an extreme wide shot, then a close-up run cycle | [OBS] The close-up run of Jun is a 12-frame cycle: 6 drawings held 2 frames each, while the camera drifts on 1s. |
| 1:08–1:13 | Gold sprint with continuous push-in to an extreme close-up of the eyes, then a dark wipe to an overhead shot of both charging | [OBS] The camera follows a single motivated arc: from wide, to tight, to a reveal of the geography. |
| 1:13–1:20 | First clash in a long wide shot | [OBS] Clash flash with a spherical ring, then both are knocked apart, skid into low hand-on-ground stances, and relaunch. Level change: one fighter drops flat as the other leaps over. Cartwheel kick, clinch, horizontal knockback, tumble recovery. |
| 1:20–2:30 | Exchanges intercut with large close-ups (block, over-shoulder punch) | [OBS] Close-ups are reserved for key beats such as blocks, stare-downs, and power-ups. |
| 2:28–2:50 | Power-up auras, ground shockwave, dome explosion | [OBS] Big FX moments are separated by calm wide shots. |
| 2:56–3:20 | Crowd of maroon clones | [OBS] Escalation by stakes, not only by speed. |
| 3:20–4:40 | Weapon fights; densest impact frames | [MEAS] The highest flash density of the film. |
| 4:40–5:40 | Resolution: x-ray finisher, long held close-ups, figure lying still | [MEAS] Flash rate drops sharply. Long holds dominate. |
| 6:00–8:00 | Credits, including "rough → clean-up" comparisons | [OBS] The artist roughs poses as single-line skeletons, then cleans up into filled tapered shapes. We follow the same split: pose-first skeleton, filled shapes at render time. |

## 2. Measured rhythm

- **Cuts [MEAS]:** 105 true cuts between 1:00 and 5:40. Median shot is 1.10 s and mean is 2.44 s; the 25th percentile is 0.33 s and the 75th is 2.80 s. 33 shots are under 0.5 s and 16 are over 4 s. Long uncut wide-shot exchanges alternate with rapid insert cuts.
- **Single-frame inserts [MEAS]:** 191 one-frame inserts (a cut in and a cut out on consecutive frames). 63 are darker than both neighbours and 85 are brighter: black/maroon silhouette impact frames and white flashes.
- **Escalation curve [MEAS]:** flash frames per 20 s window:
  - 1:00–1:20: 1
  - 1:20–2:20: 5–6
  - 2:20–3:00: 13
  - 3:20–4:00: 25–26
  - 4:20–4:40: 43 (peak)
  - 5:20–5:40: 5

  Intensity is built deliberately and then released.
- **Animation rate [MEAS + OBS]:** about 22 of every 24 frames differ from the previous frame during the fight. Frame-by-frame inspection shows this is partly camera motion. In the close-up run, the character is on 2s while the camera moves on 1s. Wide-shot dashes and strikes, by contrast, change drawing every frame (1s).

  **Conclusion:** fast action on 1s, cycles and close-ups often on 2s, camera and FX always on 1s.

## 3. Technique notes

### Pose clarity and silhouette
- [OBS] Figures are solid fills with no outline. Two saturated hues (gold, maroon) sit on a desaturated brown-grey ground with a dark slate sky. Hue contrast alone separates the fighters.
- [OBS] Fights are staged almost entirely in profile on a single horizontal line. Even during clinches, every limb reads against the background.
- [OBS] **Two-tone depth:** the far arm and far leg are a darker shade of the body colour. Overlapping limbs stay readable without outlines. *(Adopted.)*

### Proportions and line quality
- [OBS] Heads are large circles (about 1/6 to 1/7 of body height). Torsos taper from shoulder to hip, and limbs taper toward hands and feet. Limbs are thick (about 0.4 × head diameter). Lengths stay constant through motion except in deliberate smear drawings.
- [OBS] Glowing slit eyes (cyan on gold, white on maroon) are the only face detail. They carry all the expression and appear in close-ups as light sources.

### Anticipation and acceleration
- [OBS] The sprint start (1:10.5) has a 2–3 frame compression (deep crouch, torso near horizontal) before the first stride. Strides then lengthen every frame: spacing widens, not timing.
- [OBS] Many strikes have **no visible anticipation** in the wide shot. The previous action is the anticipation (skid, then relaunch). Anticipation is spent on the *big* moves only.

### Fast action vs. held poses
- [OBS] Exchanges run in bursts of about 0.5–1.0 s, followed by short neutral resets of about 6–8 frames (1:16.9, frames 21–26) where both fighters square up. These resets make the next burst readable.
- [EST] Impact holds of 2–4 frames on the contact pose before the knockback.

### Spacing
- [OBS] Dashes cover roughly 1/3 of the screen in 3 frames, and the slide to a stop decelerates over about 8–10 frames. Very uneven spacing gives the "snap".
- [OBS] Knockback victims travel with the body rigid and horizontal (1:16.6), then tumble, and only then settle.

### Torso rotation and full-body coordination
- [OBS] Punches are thrown with the torso leaning 30–45° into the strike and the rear leg extended as a straight line through the fist. The whole silhouette is one diagonal "line of action".
- [OBS] Kicks pivot the torso *away* to counterbalance: the torso goes almost horizontal for high kicks.

### Direction changes and evasion
- [OBS] Evasion is mostly **level change** (dropping flat, sliding under), leaning back out of range, or cartwheel/handspring off the line. Direction changes happen through a compressed crouch on the ground, with a hand often touching down.

### Follow-through and recovery
- [OBS] After big swings, the attacker rotates past the target (spin kick, 1:17.5) before resetting. Victims tumble, roll, and recover into a three-point crouch.

### Impact frames
- [OBS] Fist-to-fist clash (1:20.2) gives one frame with the screen darkened, a bright ring at the contact point, and a horizontal flare streak. It is followed by 3–5 frames of an expanding, fading shockwave ring, and both fighters slide apart.
- [OBS] Heavy hits (3:20.4) get one frame where the background turns deep maroon and the figures become black silhouettes. These are used 1 frame at a time, never held.

### Smears and trails
- [OBS] Spinning legs leave a soft, partially transparent smear in the limb's own colour, filling the arc swept in one frame (1:17.4–1:17.5).
- [OBS] Dashing gets tinted afterimages (cyan ghosts behind gold, 3:20.6) and stylised white dust puffs along the ground during skids.
- [OBS] Trails are always *behind* the readable drawing. The current pose is fully opaque on top.

### Camera
- [OBS] There are four main camera modes:
  1. Locked wide shot for exchanges (most choreography).
  2. Tracking pans that follow a dash.
  3. Continuous push-in for build-up.
  4. Extreme close-ups for emotional beats.
- [OBS] Camera shake appears only at impacts. During exchanges, the frame is calm.
- [EST] There is a slight push-in during long exchanges (about 5–10% over several seconds).

### Choreography readability
- [OBS] Each burst has one clear "question": who commits? The commitment is punished, and the punishment causes the next spacing change (knockback). Distance is constantly reset, so the audience can track position.

## 4. What the new film adopts

1. Solid filled tapered figures with **two-tone depth** (darker far limbs), large circular heads, and glowing slit eyes.
2. A saturated, complementary pair of fighter colours on a desaturated environment.
3. Profile staging on one ground line, with a locked wide shot for exchanges and close-ups only for beats.
4. Fast action on **1s**, cycles and settles on **2s**, camera and FX always on **1s**.
5. Bursts of 0.5–1.0 s separated by short reset holds.
6. Anticipation only on the big moves. The previous action serves as anticipation for small ones.
7. Impact language:
   - 2–4 frame hit-stop
   - one flash or silhouette frame
   - expanding ring plus sparks
   - directional camera shake of 4–8 frames
   - escalating in frequency toward the climax
8. Smears as swept-arc fills behind the opaque limb, afterimages for one character's dashes, and dust puffs on skids and landings.
9. Escalation curve: few flashes early, the densest cluster at the climax, then a quiet held resolution.

## 5. What the new film will deliberately *not* copy
- The characters, names, palette (gold and maroon), beach setting, merch and title cards, power-ups, clones, weapons, gore, and specific move sequences.
- Our fight is unarmed and grounded, a style contrast between a power striker and an evasive counter-fighter (see `03_storyboard.md`).
