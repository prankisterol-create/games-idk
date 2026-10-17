# 02 — Character Bible & Construction Rules

Model sheets (PNG plus editable SVG) are in `output/modelsheets/`. Each sheet shows front, 3/4 and side views on a head-unit grid, the construction skeleton, and every key pose used in the film. Numbers below are the real values in `src/rig.py` (metres; standing height in the "Height" row).

## The cast

| | **KAI — "The Furnace"** | **SEN — "The Tide"** |
|---|---|---|
| Role | Power striker | Evasive counter-fighter |
| Height | 1.72 m = 6.5 heads | 1.79 m = 7.7 heads |
| Head radius | 0.132 (big head: younger, blunter) | 0.116 (small head: long, elegant) |
| Thigh / shin | 0.46 / 0.45 | 0.51 / 0.51 (long legs, long reach for kicks) |
| Torso (hip→neck base) | 0.50 | 0.52 |
| Upper arm / forearm | 0.31 / 0.30 | 0.34 / 0.33 |
| Line weight: chest → hip | 0.165 → 0.115 (heavy V taper) | 0.125 → 0.085 (slim) |
| Arm taper | 0.092 → 0.066 | 0.068 → 0.050 |
| Leg taper | 0.105 → 0.070 | 0.080 → 0.054 |
| Hands | Round fists (r 0.052), always closed | Open palms bent back at the wrist; straight "blade" hands when running |
| Body colour (near / far side) | `#F06A2C` ember orange / `#A9431C` | `#3CC8CB` teal / `#1F7F8C` |
| Identifier | Off-white headband with two simulated tails | Long simulated ponytail (far-side colour) |
| Eyes | White-hot slit, amber glow; glow rises with "heat" (embers) through the film | Pale slit, ice-cyan glow; closes before the final exchange, then flares |
| Signature FX | Embers lifting off the body, intensifying S2→S4 | None of his own; he uses the opponent's force |

## Construction conventions (both characters)

1. **Solid filled shapes, no outlines.** Every body part is a tapered capsule (two circles joined by tangent edges) in a flat colour. Torso is a tapered quadratic-Bézier stroke that can hunch (`bend` > 0) or arch (`bend` < 0).
2. **Two-tone depth:** far-side arm and leg use the darker body colour and are drawn behind the torso; near-side limbs are drawn last. This keeps crossed limbs readable without outlines (adopted from the reference).
3. **Fixed bone lengths.** Every joint position comes from forward kinematics with constant lengths. Limbs may only stretch through the explicit `san/saf/sln/slf` parameters, used for smear drawings (≤ 1.2×) and IK reach (≤ 1.08×). QC verifies thigh and shin lengths on every frame.
4. **Arms attach at one shoulder point** (90% up the spine) in profile. When the figure turns (`yaw`), shoulders and hips spread laterally to give real 3/4 and front views.
5. **Head:** circle on a short neck that continues the spine tangent; `head` nods it. Eyes sit on the forward side and follow head rotation; at `yaw` ≠ 0 both eyes show; at negative yaw (back to camera) none.
6. **Feet:** a short foot segment that is flat on the ground when planted, points with `pn/pf`, and is never drawn through the floor.
7. **Line weight is in world units**, so it scales with the camera like the drawing itself and stays consistent between wide shots and close-ups.

## Pose & movement conventions

| Convention | KAI | SEN |
|---|---|---|
| Neutral | Feet shoulder-width, chin slightly down, fists loose | Tall and relaxed, open hands, slight back lean |
| Guard | Low, square, elbows in, rear fist at the jaw, torso leaning 12–18° in | Bladed and light, lead hand open and forward, heels up |
| Line of action | Straight diagonals: rear foot → hip → fist | Curves and arcs: sways, glides, spins, flips |
| Typical anticipation | Visible coil (4–5 frames) on big moves | Almost none: he moves late and fast (`whip` spacing) |
| Strikes | Cross, backfist, low kick, axe kick, hammer fist, knee | Back kick, sweep, palm strikes, parries, redirects |
| Limitations (respected in animation) | Never fully upright mid-fight; no flips; turns are full 360° drawn through back and front views | Never meets force head-on until the climax; never punches with a fist |

## Reusable representation (and how it stays flexible)

Poses are parameter sets (joint angles, root position, `rot` whole-body rotation, `yaw` turn, `bend`, `sq` squash, per-limb stretch, hand shapes), authored as named drawings in `src/poses.py`. The rig never limits a pose:
- **Grounded poses** are authored as constraints (hip height plus world foot positions, solved with 2-bone IK), so stances can be anything.
- **Extremes and smears** use stretch, `rot` (flips, horizontal knockbacks, lying down) and per-frame overrides.
- **In-betweens** are interpolated in joint-angle space (arcs, not straight lines). Keys, breakdowns, smear frames and holds are placed by hand in the sequence scripts, and the floor constraint plus foot and hand pins prevent sliding and sinking.
