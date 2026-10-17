"""Key-pose library for DOOM vs SPIDER-MAN (same conventions as poses.py).

Every pose is authored facing RIGHT (face=+1) at x=0 and placed/mirrored with
author.P / stance_at. Grounded poses are constraints (hip height + planted feet,
legs solved with IK).

SPIDER-MAN -- small, fast, never square to the threat. Low wide stances, hands
open and ready (the web-shooter sign when he fires), knees always bent. He
moves in arcs and lines of web; every landing is a crouch.
DOOM -- tall, upright, chest out, chin level. Economy of motion: he barely
moves his feet and lets the gauntlets do the work. Palms open when casting,
fists otherwise.
"""
from heroes import SPIDER, DOOM
from poses import grounded, airborne, with_hand_on_ground

# ---------------------------------------------------------------- SPIDER-MAN
SP = {}
SP['neutral'] = grounded(SPIDER, 0.92, 0.10, -0.10, lean=2, head=0, an=8, en=16, af=-8, ef=18,
                         hn='open', hf='open')
SP['guard'] = grounded(SPIDER, 0.70, 0.38, -0.38, lean=24, bend=14, head=-14, pn=0.3, pf=0.6,
                       an=70, en=46, af=40, ef=74, hn='open', hf='open')
SP['guard_b'] = grounded(SPIDER, 0.74, 0.36, -0.36, lean=22, bend=12, head=-12, pn=0.4, pf=0.7,
                         an=66, en=52, af=36, ef=80, hn='open', hf='open')
SP['crouch3'] = with_hand_on_ground(SPIDER, grounded(SPIDER, 0.44, 0.36, -0.18, lean=52, bend=22, head=-34,
                                                     an=60, en=10, af=-110, ef=14, pn=0.3, pf=0.8,
                                                     hn='claw', hf='open'), 'n', 0.30)
SP['crouch_low'] = with_hand_on_ground(SPIDER, grounded(SPIDER, 0.40, 0.38, -0.20, lean=58, bend=26, head=-40,
                                                        an=60, en=10, af=-80, ef=40, pn=0.3, pf=0.8,
                                                        hn='claw', hf='open'), 'n', 0.32)
SP['thwip_n'] = grounded(SPIDER, 0.70, 0.36, -0.40, lean=16, bend=4, head=-6, pn=0.2, pf=0.5,
                         an=94, en=2, af=24, ef=96, hn='thwip', hf='open')
SP['thwip_f'] = grounded(SPIDER, 0.70, 0.36, -0.40, lean=18, bend=4, head=-6, pn=0.2, pf=0.5,
                         an=36, en=96, af=94, ef=2, hn='open', hf='thwip')
SP['thwip_both'] = grounded(SPIDER, 0.66, 0.40, -0.44, lean=20, bend=6, head=-8, pn=0.2, pf=0.5,
                            an=92, en=2, af=86, ef=6, hn='thwip', hf='thwip')
SP['yank'] = grounded(SPIDER, 0.66, 0.36, -0.50, lean=-26, bend=-10, head=-4, pn=0.0, pf=0.4,
                      an=56, en=104, af=46, ef=112, hn='fist', hf='fist')
# swinging on a line: the near hand holds the web overhead; rot is driven by the swing path
SP['swing'] = airborne(SPIDER, 1.5, lean=-4, bend=-8, head=-8, an=178, en=4, af=120, ef=40,
                       ln=24, kn=50, lf=8, kf=30, pn=0.7, pf=0.8, hn='fist', hf='open')
SP['swing_pump'] = airborne(SPIDER, 1.5, lean=6, bend=4, head=-14, an=176, en=6, af=150, ef=20,
                            ln=70, kn=30, lf=50, kf=60, pn=0.6, pf=0.7, hn='fist', hf='open')
SP['release'] = airborne(SPIDER, 1.5, lean=-18, bend=-18, head=-22, an=168, en=8, af=150, ef=18,
                         ln=-12, kn=24, lf=-30, kf=44, pn=0.9, pf=0.9, hn='open', hf='open')
SP['tuck'] = airborne(SPIDER, 1.3, lean=40, bend=30, head=30, an=62, en=110, af=48, ef=120,
                      ln=122, kn=140, lf=114, kf=136, pn=0.8, pf=0.8, hn='fist', hf='fist')
SP['open_out'] = airborne(SPIDER, 1.3, lean=10, bend=0, head=-6, an=120, en=20, af=-60, ef=30,
                          ln=40, kn=60, lf=-10, kf=40, pn=0.6, pf=0.8, hn='open', hf='open')
SP['land'] = grounded(SPIDER, 0.50, 0.38, -0.26, lean=34, bend=24, head=-14, pn=0.2, pf=0.7,
                      an=80, en=30, af=-60, ef=40, hn='open', hf='open')
SP['leap'] = airborne(SPIDER, 1.25, lean=14, bend=-6, head=-14, an=160, en=10, af=140, ef=20,
                      ln=-6, kn=6, lf=-24, kf=20, pn=1, pf=1, hn='open', hf='open')
SP['hop_tuck'] = airborne(SPIDER, 1.6, lean=20, bend=18, head=-6, an=80, en=80, af=40, ef=110,
                          ln=118, kn=150, lf=96, kf=140, pn=0.8, pf=0.8, hn='open', hf='open')
SP['duck'] = grounded(SPIDER, 0.46, 0.40, -0.30, lean=58, bend=26, head=-30, pn=0.3, pf=0.7,
                      an=50, en=50, af=10, ef=70, hn='open', hf='open')
SP['lean_back'] = grounded(SPIDER, 0.66, 0.42, -0.30, lean=-42, bend=-24, head=-20, pn=0.0, pf=0.4,
                           an=40, en=90, af=-90, ef=20, hn='open', hf='open')
# feet-first web-yank dropkick
SP['dropkick'] = airborne(SPIDER, 1.2, lean=-62, bend=-6, head=24, an=60, en=90, af=50, ef=100,
                          ln=92, kn=10, lf=84, kf=16, pn=0.3, pf=0.3, hn='fist', hf='fist')
SP['dropkick_ext'] = airborne(SPIDER, 1.2, lean=-70, bend=-10, head=30, an=40, en=80, af=30, ef=90,
                              ln=98, kn=0, lf=94, kf=2, pn=0.1, pf=0.1, sln=1.04, slf=1.04,
                              hn='open', hf='open')
SP['chamber'] = airborne(SPIDER, 1.2, lean=-56, bend=10, head=26, an=70, en=90, af=60, ef=100,
                         ln=120, kn=110, lf=116, kf=118, pn=0.5, pf=0.5, hn='fist', hf='fist')
SP['jab_n'] = grounded(SPIDER, 0.78, 0.38, -0.42, lean=22, bend=4, head=-2, pn=0.2, pf=0.6,
                       an=96, en=2, af=40, ef=128, san=1.04, hn='fist', hf='fist')
SP['jab_f'] = grounded(SPIDER, 0.76, 0.42, -0.50, lean=28, bend=0, head=0, pn=0.2, pf=0.8,
                       an=36, en=118, af=100, ef=2, saf=1.05, hn='fist', hf='fist')
SP['fight'] = grounded(SPIDER, 0.74, 0.34, -0.40, lean=16, bend=8, head=-4, pn=0.3, pf=0.6,
                       an=56, en=100, af=40, ef=124, hn='fist', hf='fist')
SP['flykick'] = airborne(SPIDER, 1.35, lean=-34, bend=-4, head=12, an=70, en=90, af=-30, ef=60,
                         ln=102, kn=2, lf=24, kf=124, pn=0.2, pf=0.6, hn='fist', hf='open')
SP['grabbed'] = grounded(SPIDER, 0.76, 0.40, -0.36, lean=10, bend=-6, head=-10, pn=0.2, pf=0.5,
                         an=96, en=0, af=-30, ef=60, hn='fist', hf='open')
SP['shock_a'] = grounded(SPIDER, 0.84, 0.30, -0.30, lean=-20, bend=-26, head=-36, pn=0.9, pf=0.9,
                         an=100, en=0, af=-120, ef=20, hn='fist', hf='open')
SP['shock_b'] = grounded(SPIDER, 0.80, 0.34, -0.26, lean=-12, bend=-16, head=-24, pn=0.6, pf=0.7,
                         an=98, en=4, af=-80, ef=50, hn='fist', hf='claw')
SP['thrown'] = airborne(SPIDER, 1.4, lean=-20, bend=-18, head=-30, an=150, en=30, af=120, ef=40,
                        ln=30, kn=50, lf=-10, kf=60, pn=0.7, pf=0.7, hn='open', hf='open')
SP['roll'] = airborne(SPIDER, 0.45, lean=34, bend=40, head=34, an=70, en=120, af=50, ef=120,
                      ln=130, kn=150, lf=120, kf=150, pn=0.8, pf=0.8, hn='open', hf='open')
SP['skid'] = with_hand_on_ground(SPIDER, grounded(SPIDER, 0.44, 0.50, -0.40, lean=48, bend=22, head=-20,
                                                  an=60, en=10, af=-70, ef=40, pf=0.6,
                                                  hn='claw', hf='open'), 'n', 0.36)
SP['kneel'] = grounded(SPIDER, 0.50, 0.30, None, lean=26, bend=24, head=26, pn=0.2,
                       an=30, en=60, af=-6, ef=40, lf=-4, kf=92, pf=1.0, hn='open', hf='open')
SP['kneel_shake'] = grounded(SPIDER, 0.50, 0.30, None, lean=30, bend=26, head=34, pn=0.2,
                             an=70, en=120, af=-6, ef=40, lf=-4, kf=92, pf=1.0, hn='open', hf='open')
SP['beckon'] = grounded(SPIDER, 0.84, 0.30, -0.26, lean=4, bend=2, head=4, pn=0.1, pf=0.4,
                        an=70, en=40, af=-14, ef=60, hn='open', hf='open')
SP['wave'] = grounded(SPIDER, 0.88, 0.22, -0.18, lean=-2, bend=-2, head=-6, pn=0.1, pf=0.3,
                      an=158, en=24, af=-10, ef=30, hn='open', hf='open')
SP['zip'] = airborne(SPIDER, 1.5, lean=6, bend=-6, head=-20, an=172, en=4, af=170, ef=6,
                     ln=-4, kn=20, lf=-14, kf=40, pn=1, pf=1, hn='fist', hf='fist')
SP['slide'] = grounded(SPIDER, 0.42, 0.40, None, lean=-52, bend=-12, head=-6, pn=0.4,
                       an=30, en=70, af=-50, ef=40, lf=-6, kf=96, pf=1.0, hn='open', hf='open')
SP['cover'] = grounded(SPIDER, 0.74, 0.30, -0.38, lean=-12, bend=-6, head=12, pn=0.2, pf=0.5,
                       an=96, en=128, af=-30, ef=60, hn='open', hf='open')
SP['thwip_up'] = grounded(SPIDER, 0.82, 0.30, -0.30, lean=-6, bend=-4, head=-30, pn=0.2, pf=0.5,
                          an=146, en=0, af=-20, ef=40, hn='thwip', hf='open')
SP['perch'] = grounded(SPIDER, 0.40, 0.10, -0.10, lean=46, bend=28, head=-26, pn=0.6, pf=0.6,
                       an=24, en=40, af=14, ef=50, hn='claw', hf='claw')

# ---------------------------------------------------------------- DOOM
DM = {}
DM['stand'] = grounded(DOOM, 1.0, 0.14, -0.14, lean=-3, bend=-4, head=-2, an=8, en=12, af=-8, ef=14)
DM['stand_wide'] = grounded(DOOM, 0.97, 0.26, -0.26, lean=-2, bend=-4, head=0, an=14, en=18, af=-10, ef=20)
DM['hover'] = airborne(DOOM, 2.0, lean=-2, bend=-2, head=8, an=26, en=22, af=-18, ef=26,
                       ln=6, kn=10, lf=-4, kf=14, pn=0.9, pf=0.9, hn='open', hf='open')
DM['brake'] = airborne(DOOM, 2.0, lean=-8, bend=-6, head=4, an=50, en=30, af=-40, ef=36,
                       ln=24, kn=46, lf=0, kf=30, pn=0.5, pf=0.6, hn='open', hf='open')
DM['land'] = with_hand_on_ground(DOOM, grounded(DOOM, 0.54, 0.44, None, lean=34, bend=18, head=-18,
                                                an=60, en=10, af=-50, ef=40, lf=-2, kf=94, pf=1.0,
                                                hn='fist', hf='fist'), 'n', 0.42)
DM['rise'] = grounded(DOOM, 0.80, 0.34, -0.26, lean=16, bend=10, head=6, an=20, en=30, af=-20, ef=30)
DM['cast_antic'] = grounded(DOOM, 0.94, 0.30, -0.32, lean=-8, bend=-4, head=4,
                            an=-24, en=128, af=24, ef=40, hn='open', hf='fist')
DM['cast'] = grounded(DOOM, 0.92, 0.36, -0.38, lean=8, bend=0, head=0,
                      an=92, en=0, af=-30, ef=46, san=1.03, hn='open', hf='fist')
DM['cast_high'] = grounded(DOOM, 0.94, 0.30, -0.34, lean=-4, bend=-4, head=-8,
                           an=128, en=0, af=-30, ef=40, hn='open', hf='fist')
DM['shield'] = grounded(DOOM, 0.92, 0.30, -0.34, lean=-6, bend=-2, head=6,
                        an=74, en=46, af=62, ef=58, hn='open', hf='open')
DM['charge_up'] = grounded(DOOM, 0.94, 0.30, -0.34, lean=-10, bend=-8, head=-10,
                           an=150, en=20, af=140, ef=30, hn='open', hf='open')
DM['charge_fwd'] = grounded(DOOM, 0.90, 0.40, -0.42, lean=6, bend=0, head=0,
                            an=90, en=2, af=84, ef=8, hn='open', hf='open')
DM['hit_chest'] = airborne(DOOM, 1.05, lean=-30, bend=-22, head=-26, an=150, en=12, af=-50, ef=30,
                           ln=22, kn=14, lf=-12, kf=30, pn=0.6, pf=0.6, hn='open', hf='fist')
DM['skid'] = grounded(DOOM, 0.80, 0.52, -0.46, lean=22, bend=12, head=10,
                      an=40, en=60, af=-30, ef=50, hn='fist', hf='fist')
DM['block'] = grounded(DOOM, 0.94, 0.30, -0.34, lean=-2, bend=-2, head=10,
                       an=60, en=112, af=-10, ef=40, hn='fist', hf='fist')
DM['parry'] = grounded(DOOM, 0.94, 0.30, -0.34, lean=-6, bend=-4, head=4,
                       an=110, en=50, af=-10, ef=40, hn='fist', hf='fist')
DM['grab'] = grounded(DOOM, 0.92, 0.34, -0.36, lean=6, bend=0, head=2,
                      an=88, en=6, af=-20, ef=40, hn='claw', hf='fist')
DM['hold'] = grounded(DOOM, 0.98, 0.30, -0.32, lean=-6, bend=-6, head=-4,
                      an=96, en=4, af=-30, ef=40, hn='fist', hf='fist')
DM['throw_wind'] = grounded(DOOM, 0.88, 0.36, -0.40, lean=-14, bend=-6, head=-6,
                            an=40, en=40, af=-40, ef=30, hn='fist', hf='fist')
DM['throw'] = grounded(DOOM, 0.92, 0.48, -0.44, lean=24, bend=4, head=0, pf=0.6,
                       an=124, en=0, af=-50, ef=30, hn='open', hf='fist')
DM['rip'] = grounded(DOOM, 0.98, 0.20, -0.20, lean=8, bend=10, head=24,
                     an=22, en=124, af=-6, ef=30, hn='claw', hf='fist')
DM['fling'] = grounded(DOOM, 0.98, 0.20, -0.20, lean=-4, bend=-4, head=4,
                       an=-30, en=30, af=-6, ef=30, hn='open', hf='fist')
DM['backfire'] = airborne(DOOM, 1.0, lean=-28, bend=-26, head=-36, an=160, en=10, af=150, ef=20,
                          ln=20, kn=24, lf=-14, kf=30, pn=0.5, pf=0.5, hn='open', hf='open')
DM['convulse_a'] = grounded(DOOM, 0.90, 0.30, -0.34, lean=-14, bend=-20, head=-26,
                            an=120, en=30, af=110, ef=40, hn='claw', hf='claw')
DM['convulse_b'] = grounded(DOOM, 0.86, 0.34, -0.30, lean=-4, bend=-8, head=-8,
                            an=96, en=60, af=88, ef=70, hn='claw', hf='claw')
DM['kneel'] = with_hand_on_ground(DOOM, grounded(DOOM, 0.54, 0.40, None, lean=30, bend=26, head=20,
                                                 an=50, en=10, af=-10, ef=30, lf=-4, kf=92, pf=1.0,
                                                 hn='open', hf='fist'), 'n', 0.40)
DM['kneel_look'] = with_hand_on_ground(DOOM, grounded(DOOM, 0.56, 0.40, None, lean=22, bend=14, head=-12,
                                                      an=50, en=10, af=-10, ef=30, lf=-4, kf=92, pf=1.0,
                                                      hn='open', hf='fist'), 'n', 0.40)
DM['takeoff'] = grounded(DOOM, 0.76, 0.24, -0.24, lean=10, bend=8, head=-10, an=-20, en=20, af=-30, ef=20,
                         hn='open', hf='open')
DM['fly'] = airborne(DOOM, 2.0, lean=-10, bend=-6, head=-14, an=-10, en=14, af=-24, ef=18,
                     ln=-6, kn=8, lf=-14, kf=14, pn=1.0, pf=1.0, hn='fist', hf='fist')
DM['slump'] = grounded(DOOM, 0.80, 0.30, -0.34, lean=24, bend=24, head=30,
                       an=4, en=20, af=-6, ef=24, hn='open', hf='open')
DM['point'] = grounded(DOOM, 0.98, 0.24, -0.24, lean=-4, bend=-4, head=-4,
                       an=88, en=4, af=-10, ef=20, hn='blade', hf='fist')

LIB2 = {'SPIDER': SP, 'DOOM': DM}
