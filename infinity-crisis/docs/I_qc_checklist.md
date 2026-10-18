# Deliverable I: Quality-Control Checklist

## A. Automated checks (run on every change)

`python3 tools/qc_shots.py`. Current result: **0 issues** across 11 sequences, 278 shots, 12:12, 112 dialogue lines.

| Check | What it guarantees |
|---|---|
| 13-field schema | Every shot has shot number, duration, camera, lens, movement, framing, action, lighting, environmental motion, VFX, sound, dialogue, transition |
| Frame accuracy | Every duration is a whole number of frames at 24 fps; IDs unique and ordered |
| Roster and locations | Every character, extra, force and location exists in the bible |
| Continuity path | Characters only appear in locations on their path, in order (no teleporting; no one in two cross-cut zones) |
| Exits | Nobody appears after leaving (e.g. heroes after the S10 evacuation) |
| Damage persistence | Damage never decreases within or across sequences |
| Props | Equipment changes are explicit events (shield thrown S10_150, recovered S11_060; Stormbreaker lost S09_140, recalled S09_205) |
| Dialogue lock | Every shot line matches the screenplay verbatim, same speaker, same order, same scene; speakers are in their shots |
| Scene coverage | Every screenplay scene has shots; every shot points at a real scene |

## B. Per-shot review (before a shot is approved)

- [ ] The intended characters are recognisable, and their design matches `data/characters.yaml`.
- [ ] The number of characters matches the shot list exactly (no extras, no duplicates).
- [ ] Costume, weapon and damage state match the continuity line for that shot in `docs/C_storyboard`.
- [ ] The shot does what its `action` field says, with a clear beginning, middle and end.
- [ ] Camera position, lens, move and framing match the shot list; no unmotivated shake, spin or zoom.
- [ ] Screen direction matches the sequence's staging rule (S5 zone directions; S9 Thanos left / heroes centre / platform right).
- [ ] Powers show their signature colour and shape (Deliverable D); silhouettes stay readable through FX.
- [ ] Movement has weight for its class (Deliverable E §3): contacts planted, no floating feet, no sliding.
- [ ] Anticipation, contact, follow-through, recovery and reaction are all present on every strike.
- [ ] Impacts affect the environment (dust, debris, light change) and the damage persists into later shots.
- [ ] Lighting and shadows are coherent with the shot's light sources; bloom doesn't wash out faces.
- [ ] Hands, faces and fingers have no malformations; no clipping through bodies or props.
- [ ] Duration equals the frame count in the EDL.

## C. Per-sequence review

- [ ] The sequence achieves its stated `purpose` (top of each storyboard file).
- [ ] The geography shot establishes the space before the action (S3_050, S5_040, S8_170, S9_020).
- [ ] No character is in two places at once; no prop disappears.
- [ ] The story progresses; every hero present has a meaningful contribution.
- [ ] The transition into the next sequence plays as designed (`transition` field).
- [ ] Sound effects match the visible action; designed silences are truly silent.
- [ ] Dialogue is intelligible over music and effects (dialogue-gated loudness checked).

## D. Whole-film review

- [ ] The opening establishes the threat (S1–S3).
- [ ] The middle develops the alliance (S4–S5) and the setback (S6), and the plan is clear (S7).
- [ ] The final battle pays off each hero's ability:
  - Flash: the strike
  - Spider-Man: the gears and the hold
  - Cap: the shield
  - Lantern: the bridge and the shields
  - Strange: the count and the seal
  - Cyborg: the pulse
  - Batman: the plan
  - Tony: the release
  - Trinity: buying time
  - Hulk: the gate
  - Panther: the breach
  - Aquaman: leading the breach
- [ ] Thanos is never beaten by repeated beams. He is beaten by the plan, and he has several dominant moments (S3, S5–S6, S9).
- [ ] The heroes believe they've won before learning Thanos anticipated them (end of S5).
- [ ] The ending resolves the immediate conflict at a visible cost and leaves a credible future danger (the spark; no body).
- [ ] Colour script and score progress as planned (Deliverables A and H).
- [ ] Technical deliverables pass spec (Deliverable H §5): resolution, frame rate, colour space, loudness, stems.
- [ ] Rights cleared before any public release (Marvel/Disney, DC/WBD).

## E. Prototype QC results (Sequence 1)

See [`F_prototype.md`](F_prototype.md#qc-of-the-prototype): durations match the shot list exactly, picture was reviewed across three contact-sheet iterations with the fixes listed there, and sound was verified by levels (not auditioned).
