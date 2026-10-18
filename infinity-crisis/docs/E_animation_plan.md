# Deliverable E: Animation Production Plan

## 1. Pipeline order per sequence

1. **Previs.** Built from `data/shots`. The Sequence 1 prototype in `prototype/s01` is the template: timing, camera and lighting intent, temp sound.
2. **Layout.** `prototype/blender/build_layout.py` creates one Blender scene per sequence, with a camera per shot at the specified focal length and markers at the exact frame ranges. Layout artists place the set and characters, block the camera move, and lock the edit length.
3. **Blocking** (stepped keys). Story poses, contacts and screen direction. It's reviewed in the cut against the QC checklist.
4. **Spline and polish.** Arcs, spacing, overlap, faces and fingers.
5. **Technical animation.** Cloth (capes, cloak), hair (Aquaman, Thor, Diana), muscle (Hulk, Thanos), armor collision.
6. **FX, lighting, comp.**

## 2. Reusable action library (Blender Actions / NLA strips)

| Category | Actions |
|---|---|
| Locomotion | walk/run per weight class, sprint, skid stop, three-point landing, heavy landing (crater), soft landing, take-off, hover idle, flight cruise/bank/brake |
| Attacks | per hero: 3 signature strikes + 1 finisher (Cap shield throw/catch, Thor axe overhead/recall, Diana sword high/low/shield bash/lasso, Superman jab-cross-hook/heat vision, Hulk haymaker/stomp/grab-and-heave, Panther absorb/release, Strange cast/shield/portal, Lantern construct throw, Spidey web-zip/web-net/swing, Flash route-run, Aquaman trident spin/drive, Iron Man repulsor/unibeam/missile) |
| Reactions | hit light / heavy, thrown (ballistic), skid recovery, rise from rubble (tired and fresh variants), block flinch |
| Idles | fresh, wary, exhausted, injured (per character; they degrade with the continuity sheet's `power` value) |
| Thanos | stillness hold, read (eyes only), decisive counter set: redirect, pinhole portal, sway-and-elbow, catch, pulse, lens deflection, absorb-and-return, throat slam. **Never reused within the film.** |

## 3. Movement rules by weight class

| Class | Characters | Accel. | Ground contact | Landing response | Notes |
|---|---|---|---|---|---|
| Titan | Thanos | Very slow | 4–6 frames per step | Crater + shockwave, 0 frames of recovery (he doesn't bounce) | Stillness is his rhythm; one decisive counter |
| Heavy | Hulk, Leviathan | Slow wind-up, explosive | 6–8 frames | Crater, 6–10 frames of recovery | Hang time on leaps; floor shakes |
| Power | Superman, Thor, Diana, Aquaman, Cyborg | Fast | 3–4 frames | Dust ring, 3–4 frames of recovery | Superman pulls punches unless the story says otherwise |
| Agile | Cap, Panther, Batman, Spider-Man | Very fast | 2–3 frames | Roll or crouch, 2 frames of recovery | Momentum carried through turns |
| Speed | Flash | Instant (readable) | Time-sliced | Skid | Route always visible as lightning; never pops |
| Flight | Iron Man, Lantern, Strange | Thrust-driven | n/a | Repulsor/construct braking | Banking with the whole body |

Every action shows **anticipation > contact > follow-through > recovery > reaction**. Hit-stops: 2–4 frames on heavy contacts. Slow motion is used only where the storyboard marks it (S3_090, S3_180, S5_260, S8_330).

## 4. Choreography method

1. **Fight script** per exchange, written as cause > effect (in the shot list `action` fields).
2. **Stunt-vis:** motion-capture stunt performers on a marked floor matching set geometry (the Crossing, the causeway). Thanos and Hulk are captured with performers on stilts/weighted suits, then retargeted with the mass curves above.
3. **Spatial lock:** a top-down map per set piece; screen direction is fixed (see `staging` in S9).
4. **Every counter differs** (the brief requires this). S3 and S9 counters are catalogued in section 2.
5. **Contact accuracy:** IK pins for blocks and grapples, contact-point locators checked frame by frame. QC: no interpenetration of more than 1 cm.

## 5. Simulations

| Sim | Tool | Notes |
|---|---|---|
| Capes, cloak, robes | Blender cloth / Houdini Vellum | Pre-roll 48 frames; cloak has an animator-controlled "intent" layer |
| Hair | Blender hair curves + physics | Wet-hair preset for Aquaman |
| Rain incl. freeze and reverse | Particles with time-remap attribute | One cache, played forward, frozen or reversed per shot |
| Water | FLIP (Mantaflow/Houdini) | Leviathan rise, splashes, underwater discharge |
| Destruction | RBD with constraints | Buildings, refinery, Engine rings; damage persists (cache states saved per sequence) |
| Smoke / dust | Volumes | Layered impact recipe (see Deliverable D section 6) |
| Crowds | Geometry-node agents | Hollows in unison; civilians with varied cycles |

## 6. Transitions between sequences

Every sequence boundary is designed in the shot list (`transition` field). Examples: the S1 > S2 smash cut on tinnitus; the S6 > S7 fade on low strings; the S7 > S8 match cut through the portal; the S10 > S11 cut to black in absolute silence. Character states carry exactly across boundaries (continuity sheet).

## 7. Team and schedule (indicative)

| Department | Crew | Weeks |
|---|---|---|
| Art and design | 4 | 1–10 |
| Modeling, texturing, lookdev | 8 | 4–20 |
| Rigging / CFX | 4 | 8–24 |
| Layout / previs | 3 | 2–14 |
| Animation | 10 | 12–34 |
| FX | 5 | 16–38 |
| Lighting / render / comp | 6 | 20–42 |
| Editorial, sound, music | 4 | 2–44 |

Render budget: about 17,600 frames × 2–4 render layers. At about 1.5 node-hours per frame at 4K open gate, that's about 60k node-hours (Cycles, GPU farm).
