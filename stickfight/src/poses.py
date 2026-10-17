"""Key-pose library.

Every pose is authored facing RIGHT (face=+1) at x=0 and mirrored by `at()`.
Grounded poses are authored as constraints (hip height + where each foot is
planted) and the legs are solved with IK, so stances never float or sink.
`near` limbs are on the camera side (KAI's lead side when he faces right).
"""
from rig import KAI, SEN, pose, plant_leg, plant_hand, ground_y


def grounded(build, hip_y, foot_n, foot_f, **kw):
    """hip at height hip_y; feet planted at hip-relative x offsets (face=+1)."""
    p = pose(**kw)
    p['x'], p['y'], p['face'] = 0.0, hip_y, 1
    if foot_n is not None:
        p = plant_leg(build, p, 'n', (foot_n, build.w_ankle * 0.5))
    if foot_f is not None:
        p = plant_leg(build, p, 'f', (foot_f, build.w_ankle * 0.5))
    return p


def airborne(build, y, **kw):
    p = pose(**kw)
    p['x'], p['y'], p['face'] = 0.0, y, 1
    return p


def at(p, x, face=1, y=None, dy=0.0):
    """Place a library pose in the world."""
    q = dict(p)
    q['x'] = x
    q['face'] = face
    if y is not None:
        q['y'] = y
    q['y'] = (q['y'] if q['y'] is not None else 0.0) + dy
    return q


def with_hand_on_ground(build, p, side, dx):
    return plant_hand(build, p, side, (p['x'] + dx, build.fist_r * 0.6))


# ---------------------------------------------------------------- KAI -----
# Power striker. Square, heavy, chin tucked, elbows in. Everything he throws
# travels in straight lines and his whole body goes with it.
K = {}
K['neutral'] = grounded(KAI, 0.90, 0.10, -0.10, lean=2, head=4, an=6, en=14, af=-6, ef=16,
                        hn='fist', hf='fist')
K['guard'] = grounded(KAI, 0.80, 0.24, -0.40, lean=12, bend=10, head=10,
                      an=52, en=98, af=30, ef=142)
K['guard_low'] = grounded(KAI, 0.70, 0.30, -0.50, lean=22, bend=14, head=14,
                          an=60, en=92, af=36, ef=136)
# straight right (rear hand = far arm) -----------------------------------
K['cross_antic'] = grounded(KAI, 0.74, 0.30, -0.52, lean=-4, bend=6, head=14,
                            an=80, en=30, af=-38, ef=128)            # coil back, lead arm measures
K['cross_break'] = grounded(KAI, 0.78, 0.50, -0.62, lean=20, bend=4, head=4,
                            an=34, en=120, af=88, ef=40, saf=1.2)    # smear: arm stretched mid-flight
K['cross_ext'] = grounded(KAI, 0.78, 0.45, -0.82, lean=30, bend=-4, head=0,
                          an=14, en=150, af=113, ef=2, saf=1.06)     # full commitment, line of action
K['cross_over'] = grounded(KAI, 0.74, 0.46, -0.86, lean=38, bend=2, head=2,
                           an=8, en=150, af=118, ef=8)              # overextended (missed)
# lead uppercut (near arm) ------------------------------------------------
K['upper_antic'] = grounded(KAI, 0.62, 0.36, -0.40, lean=30, bend=22, head=20,
                            an=-10, en=110, af=40, ef=140)
K['upper_ext'] = grounded(KAI, 0.92, 0.26, -0.30, lean=-6, bend=-10, head=-6,
                          an=168, en=12, af=20, ef=140, pf=0.8)
# axe kick (near leg) -----------------------------------------------------
K['axe_antic'] = grounded(KAI, 0.84, 0.10, -0.12, lean=-8, bend=6, head=6,
                          an=60, en=80, af=-40, ef=60)
K['axe_up'] = grounded(KAI, 0.90, None, -0.06, lean=-22, bend=-6, head=-4,
                       an=100, en=20, af=-70, ef=20, ln=176, kn=4, pn=0.2)
K['axe_impact'] = grounded(KAI, 0.66, 0.78, -0.30, lean=24, bend=18, head=18,
                           an=40, en=60, af=-30, ef=70, pn=0.0)
# spinning backfist (far arm swings out flat) -----------------------------
K['backfist_ext'] = grounded(KAI, 0.82, 0.10, -0.40, lean=8, bend=0, head=0,
                             an=40, en=130, af=96, ef=6)
# dash / sprint -----------------------------------------------------------
K['dash_a'] = airborne(KAI, 0.78, lean=46, bend=10, head=-14, an=-50, en=70, af=70, ef=90,
                       ln=70, kn=95, lf=-60, kf=40, pn=0.6, pf=0.9)
K['dash_b'] = airborne(KAI, 0.82, lean=44, bend=10, head=-14, an=70, en=90, af=-50, ef=70,
                       ln=-60, kn=40, lf=70, kf=95, pn=0.9, pf=0.6)
K['launch'] = grounded(KAI, 0.56, 0.30, -0.36, lean=52, bend=18, head=-16,
                       an=-60, en=40, af=40, ef=110)
# sprint cycle (contact / push / flight; the other stride is swap()) ------
K['run_contact'] = grounded(KAI, 0.80, 0.14, None, lean=38, bend=8, head=-12,
                            an=-45, en=85, af=55, ef=95, lf=-60, kf=115, pf=0.7)
K['run_push'] = grounded(KAI, 0.84, -0.60, None, lean=44, bend=8, head=-14,
                         an=60, en=95, af=-50, ef=70, lf=80, kf=105, pf=0.5)
K['run_flight'] = airborne(KAI, 0.96, lean=40, bend=8, head=-12, an=30, en=95, af=-30, ef=80,
                           ln=-55, kn=80, lf=55, kf=45, pn=0.8, pf=0.3)
# spinning backfist -------------------------------------------------------
K['spin_mid'] = grounded(KAI, 0.80, 0.06, -0.32, lean=16, bend=12, head=8,
                         an=30, en=125, af=50, ef=120)
K['backfist_wind'] = grounded(KAI, 0.80, 0.10, -0.36, lean=6, bend=6, head=0,
                              an=34, en=128, af=-70, ef=30)
K['backfist_follow'] = grounded(KAI, 0.76, 0.14, -0.42, lean=22, bend=8, head=4,
                                an=20, en=120, af=118, ef=14)
# 360 spin that travels forward, pivoting on the LEFT foot
# (left foot = near when facing right, far when facing left)
K['spin_a'] = grounded(KAI, 0.80, 0.10, None, lean=14, bend=10, head=6,
                       an=20, en=130, af=20, ef=130, lf=-20, kf=70, pf=0.6)
K['spin_back'] = grounded(KAI, 0.80, -0.12, 0.22, lean=16, bend=12, head=8,
                          an=60, en=110, af=30, ef=125)
K['spin_front'] = grounded(KAI, 0.82, None, 0.28, lean=10, bend=8, head=4,
                           an=-40, en=60, af=30, ef=120, ln=40, kn=80, pn=0.5)
K['bf_wind'] = grounded(KAI, 0.80, -0.35, 0.30, lean=6, bend=6, head=0,
                        an=34, en=128, af=-70, ef=30)
K['bf_ext'] = grounded(KAI, 0.80, -0.42, 0.32, lean=8, bend=0, head=0,
                       an=40, en=130, af=96, ef=6)
K['bf_follow'] = grounded(KAI, 0.76, -0.46, 0.36, lean=22, bend=8, head=4,
                          an=20, en=120, af=118, ef=14)
# stalking / low kick / jab / stumble (sequence 2) --------------------------
K['stalk'] = grounded(KAI, 0.74, 0.26, -0.38, lean=18, bend=14, head=12,
                      an=56, en=100, af=34, ef=144)
K['lk_chamber'] = grounded(KAI, 0.82, 0.08, None, lean=-4, bend=4, head=8,
                           an=70, en=74, af=-26, ef=96, lf=24, kf=66, pf=0.6)
K['lk_ext'] = grounded(KAI, 0.84, 0.06, None, lean=-18, bend=0, head=12,
                       an=84, en=58, af=-62, ef=60, lf=62, kf=4, pf=0.3)
K['jab_antic'] = grounded(KAI, 0.74, 0.30, -0.40, lean=16, bend=12, head=12,
                          an=44, en=112, af=34, ef=144)
K['jab_ext'] = grounded(KAI, 0.76, 0.36, -0.42, lean=24, bend=4, head=8,
                        an=99, en=3, af=36, ef=146, san=1.04)
K['stumble_a'] = airborne(KAI, 0.84, lean=56, bend=10, head=-22, an=100, en=40, af=-56, ef=30,
                          ln=52, kn=70, lf=-36, kf=60, pn=0.4, pf=0.8)
K['stumble_b'] = grounded(KAI, 0.70, 0.42, -0.34, lean=50, bend=16, head=-12,
                          an=84, en=34, af=124, ef=34)
K['catch'] = grounded(KAI, 0.58, 0.52, -0.34, lean=56, bend=24, head=-8,
                      an=80, en=10, af=40, ef=110)
# leaping axe kick / hop / hammer fist / knee (sequence 3) -----------------
K['takeoff'] = grounded(KAI, 0.92, None, -0.30, lean=24, bend=-4, head=-10,
                        an=150, en=40, af=120, ef=50, ln=95, kn=110, pn=0.6, pf=0.9)
K['air_rise'] = airborne(KAI, 1.6, lean=6, bend=6, head=-4, an=150, en=50, af=110, ef=70,
                         ln=110, kn=130, lf=-30, kf=90, pn=0.6, pf=0.9)
K['axe_air'] = airborne(KAI, 2.0, lean=-26, bend=-6, head=-8, an=100, en=20, af=-80, ef=30,
                        ln=178, kn=2, lf=10, kf=110, pn=0.2, pf=0.8)
K['axe_drop'] = airborne(KAI, 1.5, lean=20, bend=14, head=10, an=60, en=50, af=-40, ef=60,
                         ln=80, kn=4, lf=-20, kf=60, pn=0.0, pf=0.7)
K['hop_tuck'] = airborne(KAI, 1.15, lean=14, bend=10, head=4, an=60, en=100, af=40, ef=120,
                         ln=95, kn=125, lf=70, kf=130, pn=0.6, pf=0.6)
K['hammer_up'] = airborne(KAI, 1.2, lean=-8, bend=-6, head=-6, an=60, en=90, af=200, ef=30,
                          ln=80, kn=110, lf=30, kf=100, pn=0.5, pf=0.5)
K['hammer_down'] = airborne(KAI, 1.05, lean=34, bend=18, head=20, an=30, en=100, af=95, ef=12,
                            ln=50, kn=70, lf=-10, kf=80, pn=0.4, pf=0.5)
K['knee_up'] = grounded(KAI, 0.98, None, -0.20, lean=-14, bend=-8, head=6, pf=0.9,
                        an=40, en=40, af=20, ef=50, ln=118, kn=140, pn=0.8)
# reactions ---------------------------------------------------------------
K['hit_body'] = grounded(KAI, 0.72, 0.28, -0.24, lean=-6, bend=32, head=30,
                         an=20, en=110, af=-20, ef=90)
K['hit_chin'] = airborne(KAI, 1.02, lean=-30, bend=-14, head=-18, an=150, en=20, af=120, ef=40,
                         ln=30, kn=40, lf=-10, kf=30, pn=0.9, pf=0.9)
K['launched'] = airborne(KAI, 1.0, rot=-72, lean=-10, bend=-10, head=-30, an=160, en=20, af=140,
                         ef=40, ln=40, kn=30, lf=10, kf=50, pn=1, pf=1)
K['hit_gut'] = airborne(KAI, 0.98, lean=34, bend=48, head=34, an=78, en=24, af=58, ef=40,
                        ln=44, kn=36, lf=22, kf=52, pn=0.7, pf=0.7)      # C-fold: hips lead backwards
K['skid_fight'] = grounded(KAI, 0.62, 0.62, -0.20, lean=40, bend=26, head=6,
                           an=66, en=60, af=30, ef=90, pn=0.0)           # leaning into the slide
K['skid'] = grounded(KAI, 0.52, 0.50, -0.42, lean=34, bend=22, head=-6,
                     an=40, en=100, af=-10, ef=60)
K['kneel'] = grounded(KAI, 0.46, 0.38, None, lean=24, bend=26, head=30,
                      an=26, en=60, af=-6, ef=40, lf=-60, kf=150)


# ---------------------------------------------------------------- SEN -----
# Evasive counter-fighter. Tall and loose, open hands, weight on the balls of
# the feet. Moves in arcs, changes level, turns defence into the next attack.
S = {}
S['neutral'] = grounded(SEN, 0.97, 0.08, -0.08, lean=-2, head=0, an=4, en=10, af=-4, ef=12,
                        hn='open', hf='open')
S['guard'] = grounded(SEN, 0.88, 0.20, -0.34, lean=6, bend=4, head=4, pn=0.25, pf=0.4,
                      an=58, en=72, af=24, ef=104, hn='open', hf='open')
S['bounce'] = grounded(SEN, 0.92, 0.18, -0.30, lean=4, bend=2, head=2, pn=0.5, pf=0.6,
                       an=55, en=76, af=22, ef=108, hn='open', hf='open')
# lean-back slip ------------------------------------------------------------
S['slip_back'] = grounded(SEN, 0.80, 0.30, -0.24, lean=-20, bend=-14, head=-14,
                          an=30, en=90, af=-80, ef=20, hn='open', hf='open')
# level change ---------------------------------------------------------------
S['duck'] = grounded(SEN, 0.50, 0.30, -0.45, lean=42, bend=24, head=-26,
                     an=40, en=110, af=10, ef=120, hn='open', hf='open')
# rising palm (finisher) ------------------------------------------------------
S['palm_antic'] = grounded(SEN, 0.52, 0.46, -0.36, lean=40, bend=20, head=-20,
                           an=-20, en=40, af=20, ef=120, hn='open', hf='blade')
S['palm_ext'] = grounded(SEN, 0.98, 0.30, -0.52, lean=14, bend=-12, head=-16, pf=0.9,
                         an=166, en=8, af=-30, ef=40, hn='open', hf='open')
# spinning back kick (SEN faces away; far leg drives back toward the target) --
S['backkick_chamber'] = grounded(SEN, 0.80, 0.10, None, lean=40, bend=10, head=-50,
                                 an=50, en=90, af=-20, ef=60, lf=-50, kf=120, pf=0.3,
                                 hn='open', hf='open')
S['backkick_ext'] = grounded(SEN, 0.84, 0.06, None, lean=62, bend=2, head=-56,
                             an=60, en=60, af=-10, ef=50, lf=-108, kf=2, pf=0.0,
                             hn='open', hf='open')
# low sweep -------------------------------------------------------------------
S['sweep'] = grounded(SEN, 0.40, 0.30, None, lean=30, bend=20, head=-10,
                      an=60, en=40, af=-10, ef=20, lf=-96, kf=0, pf=0.8,
                      hn='open', hf='open')
# parry ---------------------------------------------------------------------
S['parry'] = grounded(SEN, 0.84, 0.30, -0.36, lean=-4, bend=6, head=0,
                      an=110, en=40, af=40, ef=110, hn='open', hf='open')
# check (shin block) ---------------------------------------------------------
S['check'] = grounded(SEN, 0.92, None, -0.10, lean=-6, bend=12, head=8,
                      an=70, en=90, af=30, ef=120, ln=70, kn=100, pn=0.2, hn='open', hf='open')
# backward glide (the tide going out) -------------------------------------------
S['glide'] = grounded(SEN, 0.72, 0.34, -0.44, lean=12, bend=10, head=2, pn=0.2,
                      an=70, en=64, af=6, ef=112, hn='open', hf='open')
# sequence 2 defence --------------------------------------------------------------
S['hop'] = airborne(SEN, 1.02, lean=-14, bend=-6, head=-10, an=150, en=30, af=-100, ef=30,
                    ln=64, kn=96, lf=-8, kf=34, pn=0.3, pf=0.7, hn='open', hf='open')
S['parry_n'] = grounded(SEN, 0.86, 0.22, -0.36, lean=-8, bend=4, head=-4,
                        an=114, en=36, af=30, ef=110, hn='open', hf='open')
S['parry_f'] = grounded(SEN, 0.86, 0.22, -0.36, lean=-8, bend=4, head=-4,
                        an=58, en=84, af=110, ef=36, hn='open', hf='open')
S['redirect'] = grounded(SEN, 0.62, 0.40, -0.32, lean=40, bend=20, head=-18,
                         an=132, en=18, af=18, ef=100, hn='open', hf='open')
S['palm_push'] = grounded(SEN, 0.80, 0.40, -0.52, lean=22, bend=-4, head=0,
                          an=86, en=10, af=80, ef=20, hn='open', hf='open')
# sequence 3 evasions -------------------------------------------------------------
S['roll_sit'] = grounded(SEN, 0.32, 0.50, 0.20, lean=-20, bend=30, head=30,
                         an=60, en=90, af=40, ef=100, hn='open', hf='open')
S['roll_tuck'] = airborne(SEN, 0.40, lean=30, bend=40, head=34, an=70, en=120, af=50, ef=120,
                          ln=130, kn=150, lf=120, kf=150, pn=0.8, pf=0.8, hn='open', hf='open')
S['sweep_fwd'] = grounded(SEN, 0.36, None, -0.10, lean=-10, bend=14, head=0,
                          an=-60, en=20, af=-80, ef=10, ln=86, kn=0, pn=0.8, hn='open', hf='open')
S['sweep_wind'] = grounded(SEN, 0.40, 0.30, -0.30, lean=30, bend=24, head=-12,
                           an=40, en=20, af=-20, ef=30, hn='open', hf='open')
S['xblock'] = grounded(SEN, 0.48, 0.46, None, lean=10, bend=14, head=14,
                       an=158, en=58, af=166, ef=48, lf=-70, kf=140, hn='fist', hf='fist')
S['flip_antic'] = grounded(SEN, 0.58, 0.20, -0.20, lean=34, bend=20, head=-6,
                           an=-60, en=20, af=-70, ef=20, hn='open', hf='open')
S['flip_launch'] = airborne(SEN, 1.25, lean=-40, bend=-24, head=-30, an=190, en=10, af=180, ef=20,
                            ln=0, kn=10, lf=-6, kf=8, pn=1, pf=1, hn='open', hf='open')
# landing / recovery ---------------------------------------------------------
S['land'] = grounded(SEN, 0.50, 0.36, -0.40, lean=34, bend=24, head=-10,
                     an=80, en=30, af=-60, ef=40, hn='open', hf='open')
S['crouch3'] = grounded(SEN, 0.46, 0.44, -0.46, lean=44, bend=20, head=-24,
                        an=30, en=10, af=-30, ef=60, hn='open', hf='open')
S['dash_a'] = airborne(SEN, 0.84, lean=40, bend=6, head=-20, an=-70, en=20, af=-60, ef=20,
                       ln=76, kn=96, lf=-58, kf=40, pn=0.6, pf=0.9, hn='blade', hf='blade')
S['flip_tuck'] = airborne(SEN, 1.3, rot=-180, lean=40, bend=30, head=30, an=60, en=110, af=40, ef=120,
                          ln=120, kn=140, lf=110, kf=130, pn=0.8, pf=0.8, hn='open', hf='open')

LIB = {'KAI': K, 'SEN': S}
