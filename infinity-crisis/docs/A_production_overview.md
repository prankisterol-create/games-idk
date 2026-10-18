# Deliverable A: Production Overview

**INFINITY CRISIS: AVENGERS & JUSTICE LEAGUE VS. THANOS**
A 12-minute theatrical-style CGI short film. Non-commercial fan production concept.

## Logline

Thanos uses an ancient multiversal machine, the Eternity Engine, to pin two realities into one and erase free will. The Avengers and the Justice League don't trust each other, but they have to beat him with a plan he can't predict, because he can see every attack coming.

## Story in one paragraph

A violet rupture opens over New York and Thanos's fleet pours through. Earth is the *hinge*, the one world that exists in both the Marvel and DC realities, and the last anchor the Engine needs. The Avengers hold for one round, then Thanos beats them one by one, each in a different way. Superman arrives through a second tear with the Justice League. The two teams join forces and appear to win a huge city battle, until Thanos freezes time. He reveals that every blow they landed fed the Engine (Tony's realization) and that he has been editing their perception of cause and effect (Batman's realization). Beaten and hiding underground, the heroes build a plan around three anchors (Crown, Root, Heart). The anchors must go dark in one order inside a half-second window. Strange runs the plan on a shared count that Thanos cannot read, so the heroes act on the clock instead of reacting to what they see. On the Engine, the plan works. Superman, Thor and Wonder Woman lose their fight with Thanos but buy the time the shutdown needs. When Thanos pours the Stones into the failing machine, Batman and Tony force him to choose between the Engine and the fight. Cap's shield hits the last control point, and Tony stays to trigger the release by hand. The heroes wake in the wreckage, and Tony is alive inside his nanotech shell. A single purple spark flickers in the debris.

**Theme.** Order imposed (Thanos's single reality) against order chosen (strangers trusting each other). Thanos wins every exchange he can predict. He loses only to a plan made of free choices.

## Key creative decisions and assumptions

| Decision | Choice and reason |
|---|---|
| Runtime | **12:12** (17,568 frames). The brief's sequence ranges add up to at least 12:15, so each sequence sits near the low end of its range. Sequence 1 gets its full 58 s as the polished opening. Sequence 8 (1:44) and Sequence 9 (1:05) run under the brief's ranges to protect the total; an extended cut could add about 50 s of fleet combat to S8 and two exchanges to S9. |
| Roster | Brief roster plus **Cyborg** (analysis, carrier pulse). Captain Marvel, Scarlet Witch, Ant-Man, Wasp, Hawkeye, Black Widow, Martian Manhunter and Supergirl are left out to avoid overcrowding; the brief allows this. |
| Setting | New York is the coastal city. Aquaman's war machine comes out of the harbor, and the ferries give Green Lantern a fleet to shield. |
| Why Thanos doesn't just snap | The Stones govern one universe. The Engine extends them across realities, and syncing it uses most of their power. He fights physically and has to *choose* when the Engine fails. |
| Why direct attacks fail | Every strike feeds the Engine, and Thanos edits the heroes' perception of cause and effect. The win comes from a pre-timed plan (the count), with no last-minute power-up. |
| False victory | End of S5: heroes believe they've won, and Thanos freezes the battlefield. ("Thank you.") |
| Ending | Costly but survivable. Tony survives inside the nanotech shell set up in S10_080. The Flash can't run, Lantern's ring is dark and Strange is spent. There is no sign of Thanos's body, and a spark remains. |
| Original elements | Eternity Engine, Oruun, the Hollows, the Leviathan, Monolith cruisers, the Silent Throne, the Ascendant Guard, all dialogue and all music. No copied lines or score. |
| Rights | Characters belong to Marvel/Disney and DC/Warner Bros. Discovery. This is a fan concept; any public release needs licensing. |

## Visual approach

- **Look:** premium stylised-realist CGI, physically based materials, volumetric atmosphere, anamorphic lens language (oval bokeh, restrained flares), filmic tone mapping.
- **Colour script:** S1 sodium-orange and blue night turns violet. S2–S6 are fire against violet, with green and blue hero accents. S7 is red emergency light against blue hologram. S8–S10 are a cold void with violet-white core light and each team's colour as a beacon. S10's collapse drains to monochrome. S11 is starlight and Earth blue.
- **Power signatures:** each hero has a distinct colour and shape language (Deliverable D), so a frame reads even in silhouette.
- **Readability rules:** fights are staged laterally with locked screen direction (S9 has a formal rule). Every set piece opens with a geography shot (S3_050, S5_040, S8_170, S9_020).

## Technical specification

| Item | Spec |
|---|---|
| Frame rate | 24 fps (23.976 for broadcast deliverables) |
| Master | 4096 × 1716 (DCI 4K scope, 2.39:1), rendered **open gate 4096 × 2304** so the 16:9 version extracts without reframing |
| Deliverables | DCP 2K/4K scope; UHD 3840 × 1608 scope; UHD 3840 × 2160 16:9 (open-gate extraction); 1920 × 1080 web |
| Colour | ACES (ACEScg working, ACEScct grading); Rec.709 SDR and P3-D65 PQ HDR10 trims |
| Audio | 5.1 and 7.1.4 (Atmos-ready objects) plus stereo downmix; dialogue, music and effects stems |
| Composition | All story-critical action protected inside 2.39:1; 16:9 adds headroom only |

## Production method

**Pipeline:** Blender (assets, layout, animation, Mantaflow and particle FX, Cycles rendering) with USD interchange. Houdini is optional for the S8/S10 destruction and the Leviathan water. Unreal Engine is optional for virtual-camera layout of the large S8 environment. DaVinci Resolve handles conform and grade; a DAW (Reaper or Pro Tools) handles the mix.

**Phases:**
1. Development (this package)
2. Previs, using the prototype pipeline in `prototype/` per sequence
3. Asset build
4. Layout from `data/shots` (cameras are generated from the shot list, see `prototype/blender/`)
5. Animation
6. FX and simulation
7. Lighting and render
8. Compositing
9. Editorial
10. Sound and music
11. Picture finishing (grade and conform)

**Schedule and crew:** about 9–11 months with a core team of about 35. Breakdown in Deliverable E.

## Capability audit: what was made here, and what wasn't

| Made in this environment (finished) | Still needs a production pipeline |
|---|---|
| Complete screenplay (`docs/B_screenplay.fountain` + PDF) | Final CG character models, rigs and textures |
| Storyboard: 278 shots, all 13 fields (`docs/C_storyboard/`) | Character animation for 12 minutes |
| Character bible, asset list and continuity sheet (D) | Final FX simulations and renders |
| Animation production plan (E) | Voice cast and recorded dialogue |
| **Rendered prototype of Sequence 1** with synthesised sound (F), 2.39:1 and 16:9 | Orchestral score recording |
| Blender layout builder: scenes, cameras and markers from the shot list (F) | Final mix and grade |
| 278 video-generation prompts (G), EDL, runtime | |
| Edit and audio plan (H), QC checklist plus automated QC (I) | |

**No final film exists.** The only rendered video is the **Sequence 1 prototype**. It is a procedural 2D previs: stylised, with captions in place of recorded dialogue and synthesised temp sound. It shows timing, composition, lighting intent and sound design, not final CGI quality.
