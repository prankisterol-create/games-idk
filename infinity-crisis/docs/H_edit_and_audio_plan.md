# Deliverable H: Editing and Audio Plan

Frame-accurate timings for every shot are in [`output/edit/edl.csv`](../output/edit/edl.csv) and the CMX3600 [`INFINITY_CRISIS.edl`](../output/edit/INFINITY_CRISIS.edl) (picture start 01:00:00:00). The runtime table is in [`output/edit/runtime.md`](../output/edit/runtime.md).

## 1. Sequence order, pacing and transitions

| Seq | Duration | Avg shot | Pacing intent | Out-transition |
|---|---|---|---|---|
| 1 The Sky Breaks | 0:58 | 3.2 s | Slow and silent, accelerating into the inserts (1.5–2.5 s), long holds on Thanos | **Smash cut** on the impact into tinnitus |
| 2 The Avengers Respond | 0:58 | 2.9 s | Brisk cross-cutting, one clear action per hero | Cut on Thanos's descent |
| 3 The Titan Enters | 1:00 | 2.4 s | Ritual slowness (4.5 s tilt-up), then a four-second flurry, then counters at 1–2 s each | Cut on the sonic boom |
| 4 The Justice League Arrives | 1:06 | 2.4 s | Hero beats of 1.5–2 s, dialogue at a natural pace | Crane up into S5 |
| 5 First Combined Battle | 1:30 | 2.7 s | Cross-cut zones A–E on locked screen directions; false-victory swell; **hard cut to freeze** | Reverse playback into S6 |
| 6 Thanos Turns the Tide | 1:01 | 2.5 s | Each failure gets its own shot; realisation beats are held | **Fade to black** (12 frames) |
| 7 The Plan | 0:48 | 3.2 s | Dialogue-led; slow push on Steve | **Match cut** through the portal |
| 8 The War for Reality | 1:43 | 2.7 s | Wide/close alternation; four movements; **silence on the strike** | Cut on Thanos's launch |
| 9 Trinity vs. Thanos | 1:05 | 2.6 s | Lateral master, line never crossed until S09_210 | Deliberate reverse to the platform |
| 10 The Final Gambit | 1:05 | 2.3 s | The fastest cutting of the film, then 1.5–2 s beats around Tony's choice | **Cut to black + silence** |
| 11 The Aftermath | 0:55 | 2.6 s | Slow; faces; one long pull-back; titles on black | End |

Slow motion is limited to S3_090, S3_180, S5_260 and S8_330, and every one is a speed ramp back to real time. Shake is limited to impacts (8–10 frames).

## 2. Music (original score concept)

| Cue | Sequence | Content |
|---|---|---|
| 1M1 Stillness | 1 | Digital silence, 30 Hz pressure, distant solo choir, then the invasion: heartbeat, low drums, and the **Thanos motif** (low brass D–B♭–A, choir D minor), held under his lines |
| 2M1 First Response | 2 | Fast string ostinato + aggressive percussion; the **Avengers motif** (rising 4th–5th brass figure) |
| 3M1 The Titan | 3 | Thanos motif in full; combat percussion that drains to a single cello note on "He adapts"; a sting of hope on the second tear |
| 4M1 Dawn | 4 | The **Justice League horn call** (rising octave + 5th), held under strain at the hospital, then blooming; at the handclasp the two motifs **merge** (Avengers ostinato under the JL horn line) |
| 5M1 Alliance in Motion | 5 | Merged theme at tempo; each zone keeps its own instrument family (brass sky, strings street, low percussion waterfront, choir dimensional front, woodwind rescue); false-victory swell; **freeze cuts everything to one tone** |
| 6M1 Causality | 6 | Reversed orchestra, dread pulse, Thanos motif at full force, then low strings only |
| 7M1 The Count | 7 | Near silence, solo piano; the **tick motif** (a muted woodblock) appears with the hologram; a low string motif builds into determination |
| 8M1 The War for Reality | 8 | Full orchestra and choir over the tick as a metronome; **absolute silence for the strike**; then the merged theme |
| 9M1 Three Against the Titan | 9 | Percussion-led; each hero's motif on contact; Thanos motif climbing; strings swell under "We're buying time" |
| 10M1 The Gambit | 10 | Merged theme fighting the Thanos motif; **music falls away completely** at the collapse so the mechanism dominates; silence on the wave |
| 11M1 Same Responsibility | 11 | Solo strings, then a restrained hopeful resolution of the merged theme; one low Thanos-motif note under the spark; silence for titles |

All themes are original. Temp tracks must not use existing film scores.

## 3. Sound design layers

**Layer stack per major impact** (mirrors the VFX recipe):
1. contact transient
2. flash high-frequency crack
3. low-frequency shock (sub)
4. debris and glass
5. secondary collapse
6. delayed distant boom (distance-correct: 1 s per ~340 m)
7. settle ticks

**Character sonic identities** are listed in `data/characters.yaml` (`sonic_identity`): Cap's bell-like shield, Diana's bracer bell, Lantern's construct hum whose pitch drops with power, Panther's storing hum, Flash's crackle, Thanos's six-note Stone cluster and footstep sub, and Iron Man's rising repulsor whine.

**Designed silences:**
- S1 head
- S1_080 rain freeze
- S1_180 flash-to-boom
- S5 freeze (single tone)
- S8_330–340 strike (no tick)
- S10_190 collapse (high-pass to nothing)
- S10_280 wave
- S11 head and titles

**Dialogue intelligibility:**
- Dialogue is centre-channel, never masked: music ducks 6–9 dB under lines, and effects are high-passed under Thanos.
- Every Thanos line sits on near-silence by design.

## 4. Mix and loudness targets

| Deliverable | Target |
|---|---|
| Theatrical / DCP | 7.1.4 (Atmos objects for ships, Flash, constructs, debris); reference level 85 dB SPL; dialnorm-free |
| Streaming | −27 LKFS integrated dialogue-gated (Netflix-style), true peak −2 dBTP; 5.1 and stereo |
| Web (YouTube) | −14 LUFS integrated, true peak −1 dBTP, stereo |
| Stems | DX, MX, FX (+ M&E) at 48 kHz / 24-bit |

## 5. Export settings

| Master | Spec |
|---|---|
| Picture master | ProRes 4444 XQ (or 16-bit EXR sequence) 4096 × 1716, 24 fps, ACES AP0 |
| DCP | JPEG2000, 2K scope 2048 × 858 or 4K 4096 × 1716, XYZ, 250 Mb/s |
| UHD scope | HEVC Main10, 3840 × 1608, PQ (HDR10) and Rec.709 SDR trims, 40–60 Mb/s |
| 16:9 | 3840 × 2160 open-gate extraction (story protected inside 2.39 centre), HEVC/H.264 |
| Web | H.264 High, 1920 × 1080 (16:9) and 1920 × 804 (scope), CRF 18–20, AAC 320 kb/s |

## 6. Conform workflow

1. Edit to the EDL with prototype or previs clips named by shot ID (`S05_140.mov`).
2. As shots finish (or as video-generation takes are approved), drop them in under the same names. The EDL relinks without re-cutting.
3. Lock picture, then sound and music to the locked EDL, then grade, then masters.
