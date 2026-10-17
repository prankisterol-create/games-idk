# 05 — Quality-Control Report

## How the animation was reviewed (and what that means)

- **What I inspected:** every rendered frame, as numbered contact sheets (8×6 thumbnails per page, at every iteration), plus full-resolution stills of every key exchange (contacts, near misses, impacts, spins, close-ups).
- **What I did not do:** I cannot watch video in real time. Judgements about *motion* come from frame-by-frame sequences and from **measured spacing** (per-frame travel of the striking limb; `output/timing/spacing.txt`), not from real-time playback.
- **Audio:** the soundtrack was **not auditioned by ear**. It was verified numerically only:
  - It is generated from the same hit-stop frame map as the picture, so cues land on their contact frames.
  - Duration matches the picture (37.46 s).
  - Peak −1 dBFS, with loudness peaks at the impacts.
- **Automated checks** run on every animation frame by `src/tools/qc_scan.py`:
  - Feet, toes, hands and head never below the ground.
  - Thigh and shin length within limits (consistency).
  - No root jump over 0.6 m in one frame (teleports).
  - The two torsos never interpenetrate.
- **Final result:** 0 issues over 868 animation frames.

## Iteration log: what each review found, and the fix

### Pass 1: Sequence 1, first render

1. **Spacing failure (critical).** KAI's sprint carried him *through* SEN. The spin overlapped him completely, and the backfist ended up swinging away from SEN, so the cause-and-effect chain broke.
   *Fix:* rebuilt the exchange on a spacing budget. Everything is solved from KAI's planted lead foot, and `seq01.py` prints the geometry: hip gaps of 0.98 m (backfist) and 1.12 m (kick).
2. **The "head" cross was a body shot.** Fist height was 1.10 m against a head at 1.3–1.4 m.
   *Fix:* raised the cross to chin height. Had SEN stayed in guard, the fist would have landed 22 cm into his head; his sway makes it miss by about 20 cm.
3. **Impact package oversized.** The ring grew to 1.7 m and a beige flash washed the whole frame.
   *Fix:* scaled it to the hit (ring 0.4–0.9 m), made screen flashes rare and light, and shortened burst spikes.
4. **Smears read as a fan of separate limbs.**
   *Fix:* swept copies are interpolated in joint space, composited behind the opaque drawing, and their density scales with distance travelled.
5. **Arms passed through a straight "punch" in-between when raising guards.**
   *Fix:* added elbows-first breakdown drawings (KAI 82, SEN 115).
6. **KAI's reaction to the kick read as standing upright.**
   *Fix:* new C-fold drawing (hips driven back, head, arms and feet trailing), plus a "fights the slide" skid drawing.
7. **Name cards overlapped the characters.**
   *Fix:* each card moved into its character's lead room.

### Pass 2: Sequence 2

1. A near-90° low-kick sweep produced visible rake lines.
   *Fix:* adaptive smear density.
2. SEN passing behind KAI was unreadable.
   *Fix:* atmospheric depth tint while behind, plus z-order.
3. KAI froze in the lunge for 12 frames while supposedly being "pulled".
   *Fix:* stagger, attempted turn, then the hit.

### Pass 3: Sequence 3

1. The moon was half-hidden by the ground in the low-angle shot. A crane can't look up at an infinitely distant horizon.
   *Fix:* added a true camera **tilt**, and a per-shot telephoto moon solved to sit behind KAI's apex.
2. **Bug:** KAI jumped to x = 0 for one frame after a root path ended.
   *Fix:* corrected the key, and added automated teleport detection.
3. SEN's sweep wind-up floated with a leg sunk into the ground.
   *Fix:* a proper hands-down grounded drawing.
4. **Bug:** black blobs appeared on a flash frame. Dust was filled after `cairo.restore()`, which also restores the *source colour*.
   *Fix:* corrected the fill order.

### Pass 4: Sequence 4

1. The two-stride clash run overshot the gap.
   *Fix:* one stride each, solved numerically.
2. The finish geometry would have floated KAI 0.5 m to meet SEN's palm.
   *Fix:* kept KAI at natural height and searched SEN's arm angle and crouch. The palm meets the chin, and the fist clears SEN's head by 14 cm.
3. KAI decelerated into the final punch (0.25 → 0.07 m/frame).
   *Fix:* retimed so the charge accelerates 0.03 → 0.31 m/frame into the cross.
4. The launch travelled at a constant 0.13 m/frame and looked floaty.
   *Fix:* eased the arc. It now snaps 0.85 m off the hit, decelerates through the apex, and drops into the landing.
5. The camera panned with SEN's walk-off, so he appeared to walk in place.
   *Fix:* held the camera so he walks out of frame.
6. KAI's head-lift beat was invisible in the wide shot.
   *Fix:* new low close-up with the moon above him. SEN's follow-through hold was also shortened by 14 frames.

### Delivery encode

The first 1080p master was 197 MB: per-pixel film grain changing every frame defeats compression.
*Fix:* grain reduced to ±2 levels and clumped 2×2, encoded with x264 CRF 20 / preset slow. The film keeps its texture at a fraction of the size.

### Whole-film continuity

1. 5–11 cm pops at sequence boundaries, plus one camera jump cut (S3 → S4).
   *Fix:* exact handoff. Each sequence starts on the previous sequence's last drawing, and hair physics state carries across. Framing matched at the boundary.
2. Automated QC count went 692 → 121 → 2 → 0.
   - The 692 were mostly pointed toes on planted feet sinking into the floor.
   - The rest were slides, lowered drawings, and rotated rolls.

   *Fix:* toe clamp in the rig, plus an engine-level floor constraint (lift a sinking body; IK feet and hands back onto the floor).

## Evaluation against the brief's checklist

| # | Criterion | Status | Evidence / notes |
|---|---|---|---|
| 1 | Character consistency | ✅ | Fixed builds and line weights; limb lengths verified every frame; stretch only in deliberate smear drawings |
| 2 | Pose clarity | ✅ (mostly) | Contact frames checked at full res; overlap remains at clinch range (final palm, pass-behind), separated by colour, depth tint and z-order |
| 3 | Choreography logic | ✅ | Every exchange is cause → effect (`03_storyboard.md`); distances are solved, not eyeballed |
| 4 | Timing & spacing | ✅ | Explicit spacing per key; measured travel shows acceleration into strikes and hang at apexes (`spacing.txt`) |
| 5 | Smooth transitions | ✅ | Exact sequence handoffs; breakdowns on arcs; pinned feet |
| 6 | Readability of fast moves | ✅ | Wide profile staging, smears behind opaque drawings, 1–2 frame holds on near misses |
| 7 | Impact-pose strength | ✅ | Contact drawings plus hit-stop; flash and silhouette frames escalate S2 → S4 |
| 8 | Full-body coordination | ✅ | Strikes lead with the hips and torso (lean 20–40°), counter-rotation on kicks, arms on overlap lags |
| 9 | Visual continuity | ✅ | Automated continuity scan; exact boundary handoff |
| 10 | Camera composition | ✅ | Lead room, motivated push-ins and pull-outs, tilt for the moon shot, held camera for the ending; shake only on impacts |
| 11 | Unwanted artifacts | ✅ | Ground penetration, teleports and fill bugs found and fixed; QC reports 0 issues |
| 12 | Animated vs. mechanically moved | ✅ (see limits) | Key drawings, breakdowns, anticipation, overlap, secondary hair motion, squash poses; slow moves are interpolated between keys (below) |

## Remaining limitations (honest)

1. **No real-time viewing by me.** Motion was judged from frame sequences and measurements. Please watch it and send notes; the scripts make changes cheap.
2. **Audio not heard.** Synthesised effects and score are cue-accurate, but the mix may need taste adjustments (`audio.py` has one gain per effect).
3. **Slow moves are machine in-betweened.** Fast action uses keys every 1–3 frames, but idles, rises and the walk interpolate in joint space between keys 4–14 frames apart. They're smooth, but more even than hand-drawn in-betweens.
4. **Profile-first rig.** 3/4 and front views come from a lateral-offset `yaw` approximation (no true 3D limb rotation). They hold up in turns and close-ups but would not support long 3/4 action.
5. **Hair and headband tails** are simulated but do not collide with the body, so they can pass over the head or torso on extreme poses.
6. **Clinch-range overlap.** In 2D profile, the final palm strike and SEN's pass-behind necessarily overlap the two silhouettes for a few frames.
7. **2.5D camera.** Parallax is layered depth factors, not a perspective camera.
8. **Wide shots are small on phones.** Extreme wide shots put the figures at about 170 px tall at 1080p, faithful to the reference's wide shots but small on a phone.
9. **Length.** 37.5 s, chosen deliberately: quality over length, per the brief.
