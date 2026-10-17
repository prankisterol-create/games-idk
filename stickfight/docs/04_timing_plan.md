# 04 — Timed Animation Plan

*Generated from the animation tracks by `src/tools/timing_doc.py`. Do not hand-edit the tables; edit the sequence scripts and regenerate.*

## Frame-rate decisions

- **Playback:** 24 fps (film standard; the reference is also 24 fps).
- **Drawing rate:** varies by shot type, chosen per range in the scripts:
  - **On 1s (24 drawings/s):** all fast action (sprints, strikes, spins, flips, impacts).
  - **On 2s (12 drawings/s):** idles, breathing, KAI's stalking shuffle, SEN's slow guard raise, lowering the hand, the walk-off. Ranges are listed per sequence below.
- **Camera, FX, hair and headband secondary motion:** always on 1s, even over drawings held on 2s (as observed in the reference close-ups).
- **Hit-stop:** extra render frames inserted *after* a contact drawing. The drawing holds while sparks, rings, shake and hair keep moving. Authored in animation frames, so choreography timing and impact emphasis are edited independently.
- **Spacing curves** (`ease` per key, meaning the spacing *from that key to the next*):

| Curve | Meaning |
|---|---|
| `lin` | Even spacing (constant speed). Used inside sprint cycles and ballistic travel. |
| `acc` | Spacing widens: slow out of the key, arriving fast. Used for anticipations. |
| `dec` | Spacing narrows: explosive departure, cushioned arrival. Used on most extremes. |
| `whip` | Very explosive start, long settle. Used for reactions and evasions. |
| `smooth` | Slow out and slow in. Used for settles and idles. |
| `hold` | Hold the drawing, then pop. Used across cuts. |

Measured per-frame travel of the striking limb for the signature actions is in `output/timing/spacing.txt`, and drawn as spacing charts in `output/timing/timing_*.png`.


## SEQUENCE 1 — STANDOFF & FIRST EXCHANGE (240 animation frames, 10.0 s @ 24 fps)

- **Length:** 240 animation frames + 6 hit-stop frames = 246 rendered frames (10.25 s), starting at film time 0.00 s.
- **Hit-stops** (anim frame, +extra frames): 164 (+2), 179 (+4).
- **Impact frames:** none.
- **Camera cuts** at anim frames: 66, 102, 132, 204, 222.

### KAI

- **On 2s:** 0-63.
- **Smear frames:** 162-164 af, 173-173 af, 174-175 af.

| Anim frame | Film time (s) | Drawing | Spacing to next | Locks |
|---:|---:|---|---|---|
| 66 | 2.75 | CU idle | smooth | foot:n foot:f |
| 80 | 3.33 | antic: shoulders drop | acc |  |
| 82 | 3.42 | breakdown: elbows fold first | lin |  |
| 85 | 3.54 | fists up (overshoot) | dec |  |
| 89 | 3.71 | settle | smooth |  |
| 132 | 5.50 | wide: guard | smooth | foot:n foot:f |
| 140 | 5.83 | antic: coil | smooth | foot:n foot:f |
| 145 | 6.04 | launch (compressed) | acc | foot:n foot:f |
| 147 | 6.12 | push-off | lin | foot:f |
| 149 | 6.21 | flight | lin |  |
| 151 | 6.29 | contact | lin | foot:n |
| 162 | 6.75 | cross breakdown (smear) | lin | foot:n |
| 164 | 6.83 | cross EXTREME: near miss | dec | foot:n |
| 167 | 7.04 | over-extended | smooth | foot:n |
| 168 | 7.08 | spin: back to camera | lin |  |
| 170 | 7.17 | spin: back to SEN | lin |  |
| 171 | 7.21 | spin: facing camera | lin |  |
| 173 | 7.29 | backfist EXTREME: over SEN | dec |  |
| 176 | 7.42 | over-rotation: body open | smooth |  |
| 179 | 7.54 | CONTACT | lin |  |
| 180 | 7.75 | C-fold around the kick, lifted | dec |  |
| 186 | 8.00 | lands, fights the slide | smooth |  |
| 198 | 8.50 | skid stops: three-point crouch | smooth |  |
| 212 | 9.08 | looks up | dec | foot:n foot:f hand:n |
| 232 | 9.92 | rises: lower, warier guard | smooth |  |

### SEN

- **On 2s:** 0-99, 108-121, 132-159, 192-239.
- **Smear frames:** 178-179 lf.

| Anim frame | Film time (s) | Drawing | Spacing to next | Locks |
|---:|---:|---|---|---|
| 115 | 4.79 | breakdown: forearm rises first | smooth |  |
| 122 | 5.08 | open-hand guard | smooth |  |
| 161 | 6.71 | reads the cross late | whip | foot:n |
| 164 | 6.83 | lean back: misses by inches | dec | foot:n |
| 167 | 7.04 | glides out | dec |  |
| 173 | 7.29 | level change: arm passes over | dec | foot:n foot:f |
| 175 | 7.38 | turn (facing camera) | lin |  |
| 177 | 7.46 | chamber | acc |  |
| 179 | 7.54 | back kick CONTACT | dec |  |
| 184 | 7.92 | recoil | smooth |  |
| 190 | 8.17 | guard reset | dec | foot:n foot:f |

## SEQUENCE 2 — ADAPTATION (anim frames 0-167, ~7 s)

- **Length:** 168 animation frames + 7 hit-stop frames = 175 rendered frames (7.29 s), starting at film time 10.25 s.
- **Hit-stops** (anim frame, +extra frames): 52 (+3), 68 (+1), 76 (+1), 94 (+2).
- **Impact frames:** 52 (white).
- **Camera cuts** at anim frames: 124, 146.

### KAI

- **On 2s:** 2-43, 124-167.
- **Smear frames:** 51-52 lf, 67-67 an, 75-75 an, 80-82 af.

| Anim frame | Film time (s) | Drawing | Spacing to next | Locks |
|---:|---:|---|---|---|
| 0 | 10.25 | stalk | smooth | foot:n foot:f |
| 46 | 12.17 | feint: S1 coil + step in | acc | foot:f |
| 50 | 12.33 | hold: SEN bites | smooth | foot:n foot:f |
| 51 | 12.38 | low kick | lin | foot:n |
| 52 | 12.42 | CONTACT shin on shin | dec | foot:n |
| 55 | 12.67 | rebound | smooth | foot:n |
| 68 | 13.21 | step-jab 1 (parried) | dec | foot:n foot:f |
| 76 | 13.58 | step-jab 2 (parried) | dec | foot:n foot:f |
| 78 | 13.71 | cross coil | acc | foot:n foot:f |
| 82 | 13.88 | cross: caught and redirected | dec | foot:n |
| 85 | 14.00 | pulled past | dec |  |
| 88 | 14.12 | staggers forward a step | smooth | foot:n |
| 91 | 14.25 | tries to turn | smooth |  |
| 94 | 14.38 | CONTACT (back) | lin |  |
| 97 | 14.58 | stumbles | dec |  |
| 110 | 15.12 | catches himself | dec | foot:n foot:f |
| 117 | 15.42 | turns | smooth | foot:n foot:f |

### SEN

- **On 2s:** 0-17, 32-45, 120-167.
- **Smear frames:** 93-94 an+af.

| Anim frame | Film time (s) | Drawing | Spacing to next | Locks |
|---:|---:|---|---|---|
| 30 | 11.50 | meets him | smooth | foot:n foot:f |
| 49 | 12.29 | sways back (conditioned) | dec | foot:n foot:f |
| 52 | 12.42 | check: shin up | dec | foot:f |
| 54 | 12.62 | hop back | dec |  |
| 62 | 12.96 | lands | dec | foot:n foot:f |
| 68 | 13.21 | parry (lead hand) | whip |  |
| 76 | 13.58 | parry (rear hand) | whip |  |
| 80 | 13.79 | redirect: hand on the wrist, under the arm | whip |  |
| 86 | 14.04 | passes behind | lin |  |
| 94 | 14.38 | palm strike to the back | dec | foot:n foot:f |
| 100 | 14.71 | follow-through | smooth | foot:n foot:f |
| 106 | 14.96 | resets | smooth |  |
| 110 | 15.12 | shakes out the hand | smooth |  |

## SEQUENCE 3 — ESCALATION: AIR & GROUND (anim frames 0-123, ~5.5 s)

- **Length:** 124 animation frames + 7 hit-stop frames = 131 rendered frames (5.46 s), starting at film time 17.54 s.
- **Hit-stops** (anim frame, +extra frames): 28 (+4), 56 (+3).
- **Impact frames:** 28 (dark), 56 (white).
- **Camera cuts** at anim frames: 14, 26.

### KAI

- **On 2s:** 80-123.
- **Smear frames:** 12-13 an+af, 25-28 ln, 55-56 af, 68-70 ln.

| Anim frame | Film time (s) | Drawing | Spacing to next | Locks |
|---:|---:|---|---|---|
| 0 | 17.54 | guard | smooth | foot:n foot:f |
| 3 | 17.67 | antic | acc | foot:n foot:f |
| 5 | 17.75 | push-off | lin | foot:f |
| 9 | 17.92 | plant | lin | foot:n |
| 11 | 18.00 | gather | lin |  |
| 13 | 18.08 | TAKE-OFF | lin |  |
| 16 | 18.21 | rising, knee up | dec |  |
| 19 | 18.33 | leg up (apex) | dec |  |
| 23 | 18.50 | hang time | smooth |  |
| 26 | 18.62 | DROP | acc |  |
| 28 | 18.71 | HEEL IMPACT | dec | foot:n foot:f |
| 46 | 19.62 | pulls the heel out | smooth | foot:n foot:f |
| 49 | 19.75 | reads the sweep | lin | foot:n foot:f |
| 51 | 19.83 | hops it | dec |  |
| 53 | 19.92 | hammer wind-up | smooth |  |
| 56 | 20.04 | HAMMER (blocked) | acc |  |
| 60 | 20.33 | lands, presses | dec | foot:n foot:f |
| 70 | 20.75 | rising knee: misses | dec | foot:f |

### SEN

- **On 2s:** 0-11, 92-123.
- **Smear frames:** 50-51 ln.

| Anim frame | Film time (s) | Drawing | Spacing to next | Locks |
|---:|---:|---|---|---|
| 15 | 18.17 | sees the leap: drops | whip | foot:n foot:f |
| 18 | 18.29 | sits back into the roll | dec |  |
| 27 | 18.67 | out of the roll, crouched | dec | foot:n foot:f |
| 47 | 19.67 | low dash | lin |  |
| 49 | 19.75 | sweep wind: hands down | lin |  |
| 51 | 19.83 | SWEEP (passes under) | dec | foot:f |
| 53 | 19.92 | sees it coming | dec |  |
| 56 | 20.04 | X-BLOCK | dec | foot:n foot:f |
| 58 | 20.25 | driven down | dec |  |
| 64 | 20.50 | slides back on one knee | dec |  |
| 66 | 20.58 | flip antic | smooth | foot:n foot:f |
| 69 | 20.71 | springs back (arched) | dec |  |
| 82 | 21.25 | lands, far away | dec | foot:n foot:f |

## SEQUENCE 4 — CLASH & RESOLUTION (anim frames 0-335, ~14 s)

- **Length:** 336 animation frames + 11 hit-stop frames = 347 rendered frames (14.46 s), starting at film time 23.00 s.
- **Hit-stops** (anim frame, +extra frames): 26 (+5), 118 (+6).
- **Impact frames:** 26 (focus+dark), 118 (white+dark).
- **Camera cuts** at anim frames: 60, 76, 92, 199, 227.

### KAI

- **On 2s:** 0-7, 44-91, 202-225.
- **Smear frames:** 25-26 af, 116-118 af.

| Anim frame | Film time (s) | Drawing | Spacing to next | Locks |
|---:|---:|---|---|---|
| 14 | 23.58 | coil | lin | foot:n foot:f |
| 26 | 24.08 | CLASH (fist) | dec |  |
| 28 | 24.38 | thrown back | dec |  |
| 42 | 24.96 | skid stops | smooth | foot:n foot:f |
| 76 | 26.38 | CU KAI | smooth | foot:n foot:f |
| 90 | 26.96 | sinks into the crouch | acc | foot:n foot:f |
| 99 | 27.33 | LAST CHARGE | acc | foot:n foot:f |
| 118 | 28.12 | straight right: passes over his shoulder | dec |  |
| 119 | 28.42 | launched | dec |  |
| 140 | 29.29 | lands on his back | dec |  |
| 144 | 29.46 | bounce | smooth |  |
| 160 | 30.12 | slides to rest | dec |  |
| 210 | 32.21 | lifts his head toward SEN | smooth |  |
| 225 | 32.83 | lets it fall | acc |  |

### SEN

- **On 2s:** 0-7, 44-59, 162-183, 254-335.
- **Smear frames:** 25-26 an, 117-118 an.

| Anim frame | Film time (s) | Drawing | Spacing to next | Locks |
|---:|---:|---|---|---|
| 14 | 23.58 | coil | lin | foot:n foot:f |
| 26 | 24.08 | CLASH (palm) | dec |  |
| 42 | 24.96 | skid stops | smooth | foot:n foot:f |
| 60 | 25.71 | CU: eyes close | smooth | foot:n foot:f |
| 74 | 26.29 | eyes open | smooth | foot:n foot:f |
| 100 | 27.38 | low, still guard: waits | smooth | foot:n foot:f |
| 114 | 27.96 | steps IN, under the line | dec | foot:n foot:f |
| 118 | 28.12 | RISING PALM: chin | dec | foot:n foot:f |
| 132 | 28.96 | holds the follow-through | smooth | foot:n foot:f |
| 184 | 31.12 | lowers his hand | smooth | foot:n foot:f |
| 232 | 33.12 | bows | smooth | foot:n foot:f |
| 247 | 33.75 | turns away | lin | foot:n foot:f |

**Total running time:** 899 frames = 37.46 s.
