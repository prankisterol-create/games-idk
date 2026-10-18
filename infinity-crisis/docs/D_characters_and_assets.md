# Deliverable D: Character and Asset List

Canonical designs live in [`data/characters.yaml`](../data/characters.yaml). Every video prompt repeats those design blocks word for word. Locations are in [`data/locations.yaml`](../data/locations.yaml). The per-sequence state of every character (damage, location, power, knowledge) is in the generated [continuity sheet](D_continuity_sheet.md).

## 1. Characters (hero assets)

| Character | Height | Silhouette key | Model / texture notes | Rig needs | Power signature (light) |
|---|---|---|---|---|---|
| Thanos | 2.60 m | Huge shoulders, small head, one bright gauntlet | Subsurface skin with chin-ridge scarring; gunmetal armor with worn gold; 6 refractive Stones; **damage variant: cracked chest plate (S9–S10)** | Full facial (FACS, 120+ shapes) for close-ups; heavy-mass muscle and jiggle; armor plate collision | Deep purple; Stone colours |
| Iron Man | 1.98 m | Chest light, hand glows | Clear-coat red, brushed gold; **variants: clean, back-scorched (S3), half-scorched (S6–S10), nanotech shell, destroyed shell**; Tony face (helmet-off rig) | Mechanical faceplate; nanotech growth (procedural); hover IK | Warm repulsor, blue-white reactor |
| Captain America | 1.88 m | Round shield | Navy weave, leather; **shield scratch layers accumulate per sequence** | Shield constraint swap (hand / back / thrown / embedded) | None (reflections) |
| Thor | 1.98 m | Cape + axe head | Scaled armor; Stormbreaker; **variants: dented (S4+), scalp cut (S6+)** | Cloth cape; axe dynamics and return-flight constraint | White-blue lightning |
| Hulk | 2.40 m | Massive triangle | Thick SSS skin; **dust/scrape layers per sequence** | Muscle sim, heavy secondary; full face | None |
| Doctor Strange | 1.83 m | Collar + cloak | Robes; **cloak variants: clean, singed hem (S4+), torn (S10+)** | Cloak with an "intent" layer (animatable, not only simulated); finger rig | Orange mandalas |
| Spider-Man | 1.78 m | Slim, splayed | Raised web-line fabric; **mask variants: on, pushed up, torn knee** | Lens shutter rig (emotion); web-line rig | White web |
| Black Panther | 1.83 m | Feline mask | Micro-weave; emissive kinetic pattern driven by a "stored energy" attribute | Claws; pattern intensity attribute | Purple kinetic |
| Superman | 1.91 m | Cape + crest | Textured blue weave; **cape variants: whole, torn (S6+), torn half away (S9+)** | Heavy cape sim; heat-vision eye shader | Natural daylight; red-white heat vision |
| Batman | 1.88 m | Cowl ears + cape | Matte armor; lens glow | Cape (glide shapes); gadget props | Gadget light only |
| Wonder Woman | 1.83 m | Tiara, shield, sword | Hammered armor; **shield dented (S6+)** | Lasso (curve + dynamics); bracer spark FX locator | Gold lasso, bracer sparks |
| The Flash | 1.83 m | Lean runner | Textured red suit | Speed rig: route curve + "time-slice" offset per limb | Yellow-orange lightning |
| Green Lantern | 1.88 m | Ring forward | Suit with emissive accents | Constructs as rigged/procedural assets; brightness driven by `power` | Green constructs |
| Aquaman | 1.93 m | Trident, hair | Wet-surface layer always on | Hair sim (wet); underwater swim set | Water, trident glow |
| Cyborg | 1.98 m | Asymmetric head | Alloy, emissive seams, half human face | Arm reconfiguration states; eye shader | Blue data, red eye |
| Extras | — | — | Woman, Dr. Okafor, child and parent, pedestrians (crowd kit: 24 base bodies × 8 outfits, rain gear), responders, hospital staff, window workers, paramedic | Crowd rig (Blender geometry nodes or Golaem-style agents) | — |

## 2. Enemy forces and vehicles

| Asset | Scale | Notes |
|---|---|---|
| Hollows | 2.1 m | Blank faceplate, violet visor slit; unison locomotion library (walk, fire, kneel, retreat); crowd of 2,000 instances |
| Crawler | 9 m | Six-legged tank; procedural gait |
| Leviathan | 60 m | Crab-cathedral walker; **adaptive armor** blendshape/procedural scale growth; open cooling intake; water interaction |
| Monolith cruiser | 400 m | Black slab; damage variant (S4 crippled) |
| Carrier | 250 m | Exposed stern engine bank (S5 target) |
| Gunships | 30 m | Standard and **mirror-hull** (S8) variants |
| Silent Throne | ~20 km | Flagship; observation prow set (hero-scale set for S1_150–160) |
| Ascendant Guard | 3 m | Gunmetal and gold (echoes Thanos), glaives, shoulder cannons |

## 3. Environments

| Environment | Build | Damage states |
|---|---|---|
| Earth from orbit | Procedural planet: land/ocean, city lights, 3 cloud layers, atmosphere shader | — |
| New York (night, rain) | Procedural city blocks + 12 hero buildings; river and harbor; rain system | **Intact (S1) > first strike (S2) > Crossing destroyed (S3–S6) > sky fractured (S6)** |
| The Crossing | Hero set: four-avenue intersection | Damage is cumulative per sequence; craters from S3 stay through S6 |
| Mercy General roof | Hero set | Downdraft and debris |
| Brooklyn waterfront + refinery | Set + destruction rig | Refinery collapse (S5) |
| Stark bunker, sublevel 9 | Interior set | Leaks, dead screens |
| Eternity Engine / Oruun | Procedural rings (1,000 km), core sphere, Crown spire, Root gate and crystal, gear passage, time-fragment corridor, Heart chamber, causeway, platform | **Active > storm-lit > anchors dark > collapse > wreckage (S11)** |
| Wreckage field | Kitbash of Engine fragments on Oruun's surface | — |

## 4. Props and weapons (continuity-tracked)

Cap's shield (hand, back, thrown, embedded in the node at S10_160, recovered at S11_060). Stormbreaker (flung into the void at S09_140, recalled at S09_205). Diana's sword, shield (dented from S06_090) and lasso. Aquaman's trident. Batman's scanner gauntlet and holo projector. Strange's sling ring. Lantern's ring (power level drives construct brightness). Thanos's gauntlet. Tony's nanotech shell (S10–S11). Window-washing platform, hospital beds, buses (barricade), water tower, taxis.

## 5. Lighting setups (reusable rigs)

| Rig | Use |
|---|---|
| `LGT_NYC_rain_night` | Sodium street, window emission, rain backlight |
| `LGT_rupture_violet` | Animated colour-temperature shift from sodium to violet (S1_060 onward) |
| `LGT_fire_practicals` | Flicker library for burning wreckage |
| `LGT_superman_daylight` | A "sun" that follows Superman (soft warm key + blue-white rim), even at night |
| `LGT_power_<hero>` | Light emitters attached to each power FX, so effects light the set |
| `LGT_bunker_emergency` | Red emergency light, holo blue |
| `LGT_engine_core` | Violet-white core, cold starlight, team beacons |
| `LGT_collapse_mono` | Desaturating ramp for S10_190 |
| `LGT_wreckage_earthglow` | Starlight + Earth-blue rim (S11) |

## 6. Effects library

Rain (with **time-freeze** and **reverse** modes), rupture and hex-lattice sky, cloud vortex, sky shatter, portals (sling ring and Space Stone pinhole), repulsor/lightning/heat-vision/construct/kinetic/lasso/speed-trail FX, layered impacts (contact > flash > shockwave > dust > secondary collapse > light change > settle), water (harbor, Leviathan cascade, underwater discharge), destruction (RBD buildings, refinery, ring segments), the Engine collapse (non-Euclidean stretch, star fold, white-violet wave), glowing dust, and the final spark.

## 7. Sound identity per character

See `sonic_identity` in `data/characters.yaml`, for example Cap's bell-like shield ring, Diana's bracer bell, Lantern's construct hum (its pitch falls with power), Panther's storing hum, Thanos's six-note Stone cluster, and Flash's crackle.
