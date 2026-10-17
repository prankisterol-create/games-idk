"""SEQUENCE 3 — ESCALATION: AIR & GROUND (anim frames 0-123, ~5.5 s)

  3A   0- 27  KAI: two-stride run-up and a huge leap. Telephoto low angle: he crosses the moon at
              the apex (hang time), leg raised for an axe kick.
  3B  28- 43  SEN rolls backward out from under it; the heel splits the ground (FIRST DARK IMPACT
              FRAME, crack decals, debris, flat ground ring, heavy shake).
  3C  44- 63  SEN pops up and sweeps KAI's standing leg -> KAI (who has learned) hops it and drops a
              hammer fist from the air -> SEN can only X-block (FLASH FRAME), driven to one knee.
  3D  64-123  KAI's rising knee -> SEN escapes with a back flip; distance. Both breathing hard;
              KAI's embers at full heat; SEN's eyes flare: the tide is rising.
"""
from rig import KAI, SEN, solve
from poses import LIB, with_hand_on_ground
from engine import Track, arc
from scene import Sequence, H0, YC
from author import P, swap, foot_on, ankle, hand, head_of, breathe, bounce, mix, stance_at, lifted

K, S = LIB['KAI'], LIB['SEN']


def with_hands(p):
    q = with_hand_on_ground(SEN, p, 'n', 0.35)
    return with_hand_on_ground(SEN, q, 'f', 0.12)


def moon_behind(cam, pt):
    """moon_x / moon_dy that put the moon's centre at a world point's screen position."""
    z = H0 / cam['h']
    s1 = 1.0 / cam['h']
    s0 = (1.0 / H0) * z ** 0.015
    mx = s1 * (pt[0] - cam['cx']) / s0 + 0.015 * cam['cx']
    mdy = s1 * (pt[1] - cam['cy']) / s0 + 0.015 * cam['cy'] - 0.015 * YC
    return mx, mdy


def build():
    seq = Sequence('S3', 124, wind=-0.6)
    k = Track(KAI)
    s = Track(SEN)

    # ------------------------------------------------ start (continuity from S2)
    KF, KR = 5.96, 6.61          # KAI facing left: front foot at smaller x
    SF, SR = 4.05, 3.43          # SEN facing right
    kg = stance_at(KAI, K['guard'], KF, KR, -1)
    sg = stance_at(SEN, S['guard'], SF, SR, 1)

    # ================================================================ 3A run-up and leap
    k.key(0, kg, lock='nf', label='guard')
    launch = stance_at(KAI, K['launch'], KF - 0.05, KR, -1, frac=0.5)
    k.key(3, launch, lock='nf', ease='acc', label='antic')
    push1 = foot_on(KAI, P(swap(K['run_push']), 0, -1), 'f', KR)
    fl1 = P(swap(K['run_flight']), push1['x'] - 0.5, -1)
    con1 = P(K['run_contact'], fl1['x'] - 0.42, -1)
    pin1 = ankle(KAI, con1, 'n')[0]
    tko = foot_on(KAI, P(swap(K['takeoff']), 0, -1), 'n', pin1 - 0.05)
    k.key(5, push1, lock='f', ease='lin', label='push-off')
    k.key(7, fl1, ease='lin')
    k.key(9, con1, lock='n', ease='lin', label='plant')
    k.key(11, P(K['launch'], pin1 + 0.25, -1, dy=0.04), ease='lin', label='gather')
    k.key(13, tko, ease='lin', label='TAKE-OFF')
    k.smear(12, 14, ['an', 'af'], 0.6)
    # axe heel lands where SEN's head was
    target_x = SF + 0.05
    imp = P(K['axe_impact'], 0, -1)
    heel_dx = ankle(KAI, imp, 'n')[0] - imp['x']
    imp = P(K['axe_impact'], target_x - heel_dx, -1)
    path = arc(13, 28, (tko['x'], tko['y']), (imp['x'], imp['y']), height=1.25, hang=2.6)
    k.path(14, 27, path)
    k.key(16, P(K['air_rise'], 0, -1), ease='dec', label='rising, knee up')
    k.key(19, P(K['axe_air'], 0, -1, ln=160, lean=-16), ease='dec', label='leg up (apex)')
    k.key(23, P(K['axe_air'], 0, -1, ln=186, lean=-30, head=-12), ease='smooth', label='hang time')
    k.key(26, P(K['axe_drop'], 0, -1), ease='acc', label='DROP')
    k.key(28, imp, ease='dec', lock='nf', label='HEEL IMPACT')
    k.smear(25, 29, ['ln'], 1.0)

    # ================================================================ SEN: backward roll out
    bounce(s, 0, 12, sg, stance_at(SEN, S['bounce'], SF, SR, 1), period=12)
    s.key(12, sg, lock='nf')
    s.key(15, stance_at(SEN, S['flip_antic'], SF - 0.1, SR - 0.05, 1, frac=0.4), lock='nf', ease='whip',
          label='sees the leap: drops')
    rs = P(S['roll_sit'], SR - 0.25, 1)
    s.key(18, rs, ease='dec', label='sits back into the roll')
    s.key(20, P(S['roll_tuck'], SR - 0.55, 1, rot=-100, dy=0.05), ease='lin')
    s.key(22, P(S['roll_tuck'], SR - 0.85, 1, rot=-200, dy=0.12), ease='lin')
    s.key(24, P(S['roll_tuck'], SR - 1.1, 1, rot=-290, dy=0.06), ease='lin')
    sland = stance_at(SEN, S['crouch3'], SR - 1.05, SR - 1.6, 1)
    s.key(27, sland, lock='nf', ease='dec', label='out of the roll, crouched')

    # ================================================================ 3B impact aftermath
    k.key(32, P(imp, imp['x'], -1, dy=-0.02), lock='nf', ease='dec')
    rec = stance_at(KAI, K['guard_low'], ankle(KAI, imp, 'n')[0] - 0.05, ankle(KAI, imp, 'f')[0] - 0.1, -1)
    k.key(40, P(imp, imp['x'], -1, dy=0.02, ln=60, kn=40), ease='smooth', lock='f')
    k.key(46, rec, lock='nf', ease='smooth', label='pulls the heel out')
    s.key(34, P(sland, sland['x'], 1, dy=0.01, head=-30), lock='nf', ease='smooth')
    s.key(42, sland, lock='nf', ease='smooth')

    # ================================================================ 3C sweep -> hop -> hammer -> X-block
    kF, kR = ankle(KAI, rec, 'n')[0], ankle(KAI, rec, 'f')[0]
    sw = P(S['sweep_fwd'], 0, 1)
    sw_dx = ankle(SEN, sw, 'n')[0] - sw['x']
    sweep = P(S['sweep_fwd'], kF - sw_dx + 0.12, 1)
    sdash = P(S['dash_a'], (sland['x'] + sweep['x']) / 2, 1, dy=-0.25)
    s.key(44, sland, lock='nf', ease='acc')
    s.key(47, sdash, ease='lin', label='low dash')
    s.key(49, with_hands(stance_at(SEN, S['sweep_wind'], sweep['x'] + 0.05, sweep['x'] - 0.45, 1)), ease='lin',
          label='sweep wind: hands down')
    s.key(51, sweep, ease='dec', lock='f', label='SWEEP (passes under)')
    s.smear(50, 52, ['ln'])
    # KAI reads it and hops; hammer fist from the air
    k.key(48, rec, lock='nf', ease='acc')
    k.key(49, stance_at(KAI, K['launch'], kF, kR, -1, frac=0.5), lock='nf', ease='lin', label='reads the sweep')
    hop_x = rec['x'] - 0.15
    k.path(50, 57, arc(50, 57, (rec['x'] - 0.05, 0.62), (hop_x - 0.1, 0.78), height=0.6, hang=2.0))
    k.key(51, P(K['hop_tuck'], 0, -1), ease='dec', label='hops it')
    k.key(53, P(K['hammer_up'], 0, -1), ease='smooth', label='hammer wind-up')
    k.key(56, P(K['hammer_down'], 0, -1), ease='acc', label='HAMMER (blocked)')
    k.smear(55, 57, ['af'])
    # SEN rises into the X-block under the fist
    J56 = solve(KAI, k.eval(56))
    fist = J56.hand_f
    xb = P(S['xblock'], 0, 1)
    wrist = solve(SEN, xb).hand_n
    xblock = P(S['xblock'], fist[0] - (wrist[0] - xb['x']) + 0.02, 1)
    s.key(53, P(S['sweep_fwd'], sweep['x'], 1, ln=60, kn=80, an=40, en=90, af=20, ef=100), ease='dec',
          label='sees it coming')
    s.key(56, xblock, ease='dec', lock='nf', label='X-BLOCK')
    s.key(58, P(xblock, xblock['x'] - 0.25, 1, dy=-0.06, head=24, bend=22), ease='dec', label='driven down')
    s.key(64, P(xblock, xblock['x'] - 0.7, 1, dy=-0.02, an=120, en=80, af=110, ef=90), ease='dec',
          label='slides back on one knee')
    kland = stance_at(KAI, K['guard_low'], hop_x - 0.35, hop_x + 0.25, -1)
    k.key(58, P(K['hammer_down'], hop_x - 0.1, -1, dy=-0.22, ln=40, kn=40, lf=-20, kf=40), ease='lin')
    k.key(60, kland, lock='nf', ease='dec', label='lands, presses')

    # ================================================================ 3D knee -> back flip -> distance
    sx_k = xblock['x'] - 0.7
    s.key(66, stance_at(SEN, S['flip_antic'], sx_k + 0.25, sx_k - 0.2, 1, frac=0.5), lock='nf', ease='smooth',
          label='flip antic')
    fl = P(S['flip_launch'], sx_k - 0.15, 1, dy=-0.15)
    s.key(69, fl, ease='dec', label='springs back (arched)')
    land_x = sx_k - 1.9
    s.path(69, 82, arc(69, 82, (fl['x'], fl['y']), (land_x, 0.55), height=0.9, hang=2.2))
    s.key(72, P(S['flip_tuck'], 0, 1, rot=-120), ease='lin')
    s.key(75, P(S['flip_tuck'], 0, 1, rot=-220), ease='lin')
    s.key(78, P(S['flip_tuck'], 0, 1, rot=-300, ln=60, kn=60, lf=50, kf=70), ease='lin')
    s.key(80, P(S['land'], 0, 1, rot=-350, dy=0.1), ease='lin')
    sl2 = stance_at(SEN, S['land'], land_x + 0.36, land_x - 0.4, 1)
    s.key(82, sl2, ease='dec', lock='nf', label='lands, far away')
    sg2 = stance_at(SEN, S['guard'], land_x + 0.2, land_x - 0.36, 1, dy=-0.06, lean=14, bend=10)
    s.key(90, sg2, ease='smooth', lock='nf')
    # KAI's knee comes up into the space SEN just left
    kn_x = kland['x'] - 0.5
    k.key(66, stance_at(KAI, K['guard'], hop_x - 0.55, hop_x + 0.2, -1, frac=0.6), lock='f', ease='smooth')
    kneeP = foot_on(KAI, P(K['knee_up'], 0, -1), 'f', hop_x + 0.0)
    k.key(70, kneeP, lock='f', ease='dec', label='rising knee: misses')
    k.smear(68, 71, ['ln'], 0.8)
    kg2 = stance_at(KAI, K['guard'], ankle(KAI, kneeP, 'f')[0] - 0.62, ankle(KAI, kneeP, 'f')[0], -1)
    k.key(76, kg2, ease='smooth', lock='nf')
    breathe(k, 80, 124, kg2, amp=0.035, period=14, arm=5.0)
    breathe(s, 92, 124, sg2, amp=0.03, period=16, arm=3.0)
    k.key(123, kg2, lock='nf')
    s.key(123, sg2, lock='nf')

    seq.add(k, z=1)
    seq.add(s, z=0)

    # ================================================================ camera
    c = seq.cam
    c.key(0, cx=5.0, cy=1.1, h=4.6, fw=0.5, ease='smooth')
    c.key(13, cx=4.9, cy=1.2, h=5.0, fw=0.5)
    # telephoto low angle: KAI crosses a huge moon at the apex (frames 14-25)
    apex_f = 21
    Ja = solve(KAI, k.eval(apex_f))
    # tilt up so the horizon sits low; the fighters' ground line just under it
    mc = dict(cx=Ja.hip[0] + 0.1, cy=-0.3, h=4.2, tilt=0.45)
    mx, mdy = moon_behind(mc, (Ja.hip[0] - 0.05, Ja.hip[1] + 0.15))
    c.key(14, cut=True, ease='lin', moon_r=1.45, moon_x=mx, moon_dy=mdy, **mc)
    c.key(25, ease='lin', moon_r=1.45, moon_x=mx, moon_dy=mdy, cx=mc['cx'] - 0.1, cy=-0.32, h=4.1, tilt=0.45)
    c.key(26, cut=True, cx=(imp['x'] + sland['x']) / 2 + 0.2, cy=1.0, h=4.4, ease='dec')
    c.key(44, cx=(imp['x'] + sland['x']) / 2, cy=1.0, h=4.2, fw=0.3, ease='smooth')
    c.key(64, cy=1.0, h=4.0, fw=0.6, ease='smooth')
    c.key(84, cx=2.42, cy=1.1, h=5.2, fw=0.0, ease='smooth')
    c.key(123, cx=2.42, cy=1.1, h=4.7, fw=0.0)

    # ================================================================ fx / sound
    def motes(fx, sc, rf, a):
        if a % 3 == 0:
            fx.dust(fx.rnd.uniform(-1, 9), fx.rnd.uniform(0.05, 1.4), n=1, dirx=-1, speed=1.2, size=0.03,
                    life=(30, 50), up=0.05, alpha=0.35)
    seq.emit(0, 124, motes)
    seq.at(5, lambda fx, sc, rf: fx.dust(KR, n=8, dirx=1, speed=2.3, size=0.18, alpha=0.55))
    seq.at(13, lambda fx, sc, rf: fx.dust(pin1, n=12, dirx=1, speed=2.8, size=0.2, alpha=0.6))
    seq.sfx(5, 'dash')
    seq.sfx(13, 'jump')
    seq.sfx(26, 'whoosh_big')

    heel = ankle(KAI, imp, 'n')
    seq.impact(28, heel[0], 0.08, dirx=0, diry=1, power=1.6, stop=4, style='dark', ring=False, sound='slam')

    def quake(fx, sc, rf):
        fx.ring(heel[0], 0.02, 0.1, 2.6, life=12, w=0.08, squash=0.18, col=(0.95, 0.88, 0.8))
        fx.ring(heel[0], 0.02, 0.1, 1.6, life=9, w=0.05, squash=0.18)
        fx.crack(heel[0], n=9, length=1.5)
        fx.debris(heel[0], n=18, speed=3.5, up=5.5)
        fx.dust(heel[0], n=10, dirx=-1, speed=3.4, size=0.24, alpha=0.7, life=(12, 22), up=0.9)
        fx.dust(heel[0], n=10, dirx=1, speed=3.4, size=0.24, alpha=0.7, life=(12, 22), up=0.9)
    seq.at(28, quake)
    seq.at(19, lambda fx, sc, rf: fx.dust(SR - 0.25, n=5, dirx=-1, speed=1.4, size=0.13, alpha=0.45))
    seq.at(27, lambda fx, sc, rf: fx.dust(SR - 1.3, n=6, dirx=-1, speed=1.6, size=0.14, alpha=0.5))
    seq.at(51, lambda fx, sc, rf: fx.dust(ankle(SEN, sweep, 'n')[0], n=8, dirx=1, speed=2.6, size=0.15, alpha=0.55))
    seq.sfx(47, 'dash')
    seq.sfx(50, 'whoosh')
    seq.impact(56, fist[0], fist[1] - 0.02, dirx=0, diry=-1, power=1.1, stop=3, style='white', sound='hit_block')

    def kneel_skid(fx, sc, rf, a):
        p = s.eval(a)
        fx.dust(ankle(SEN, p, 'f')[0], n=2, dirx=-1, speed=1.8, size=0.12, alpha=0.5, life=(10, 18))
    seq.emit(57, 64, kneel_skid)
    seq.sfx(57, 'skid')
    seq.sfx(68, 'whoosh')
    seq.at(69, lambda fx, sc, rf: fx.dust(sx_k, n=8, dirx=-1, speed=2.0, size=0.15, alpha=0.5))
    seq.at(82, lambda fx, sc, rf: fx.dust(land_x, n=8, dirx=-1, speed=1.6, size=0.15, alpha=0.5))
    seq.sfx(82, 'land')

    def embers(fx, sc, rf, a):
        fx.embers(solve(KAI, k.eval(a)), n=2, heat=1.1)
    seq.emit(0, 124, embers)
    seq.glow['KAI'] = lambda a: 1.8
    seq.glow['SEN'] = lambda a: 1.0 + 0.9 * max(0.0, min(1.0, (a - 96) / 16.0))

    def sen_flare(fx, sc, rf):
        from rig import eye_point
        e, _, _ = eye_point(solve(SEN, s.eval(104)))
        fx.glint(e[0], e[1], size=0.2, life=9, col=(0.7, 1.0, 1.0))
    seq.at(104, sen_flare)
    seq.sfx(104, 'glint')

    for f_, t_ in [(0, '3A run-up'), (14, '3A moon shot'), (26, '3B impact'), (44, '3C sweep'),
                   (56, '3C hammer/X-block'), (64, '3D knee/flip'), (84, '3D distance')]:
        seq.note(f_, t_)
    seq.geometry = dict(heel_x=heel[0], sen_roll_end=sland['x'], sweep_toe=ankle(SEN, sweep, 'n')[0],
                        kai_front_at_sweep=kF, fist_x=fist[0], fist_y=fist[1], flip_land=land_x)
    return seq


if __name__ == '__main__':
    for kk, v in build().geometry.items():
        print(f'{kk:22s} {v:7.2f}')
