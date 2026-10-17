"""SEQUENCE 1 — STANDOFF & FIRST EXCHANGE (240 animation frames, 10.0 s @ 24 fps)

Beat: KAI opens with total commitment; SEN shows he only needs inches.
  1A   0- 65  wide establishing, slow dolly-in, both idle
  1B  66-101  CU KAI: neutral -> fists up (anticipation dip, elbows-first breakdown, overshoot, settle)
  1C 102-131  CU SEN: calm open-hand guard (on 2s)
  1D 132-203  wide: KAI coils and sprints (1s) into a straight right -> SEN leans back by inches;
              KAI turns the miss into a travelling 360 spinning backfist while SEN glides out
              and changes level under it; the over-rotation opens KAI's body -> SEN turns his
              back and drives a spinning back kick: impact, KAI skids 2 m on his feet
  1E 204-221  MCU KAI looks up from a three-point crouch, eye flares
  1F 222-239  wide: KAI rises into a lower, warier guard (he has learned something)

Spacing is derived from planted feet: every pinned foot position below is a
world coordinate and the hips are solved from it, so nothing slides unless the
script asks for a slide (SEN's glide, KAI's skid).
"""
from rig import KAI, SEN, solve
from poses import LIB, with_hand_on_ground
from engine import Track
from scene import Sequence
from author import P, swap, foot_on, ankle, hand, head_of, breathe, bounce, mix
from titles import name_card

K, S = LIB['KAI'], LIB['SEN']
VERBOSE = False


def build():
    seq = Sequence('S1', 240, wind=lambda a: -0.5 + (1.8 if 164 <= a < 169 else 0.0))
    k = Track(KAI)
    s = Track(SEN)
    KX = -2.9

    # ================================================================ KAI dash
    kneu = P(K['neutral'], KX, 1)
    kg = P(K['guard'], KX, 1)
    launch = P(K['launch'], KX + 0.12, 1)
    far_pin = ankle(KAI, kg, 'f')[0]
    push1 = foot_on(KAI, P(swap(K['run_push']), 0, 1), 'f', far_pin)
    fl1 = P(swap(K['run_flight']), push1['x'] + 0.55, 1)
    con1 = P(K['run_contact'], fl1['x'] + 0.45, 1)
    near_pin1 = ankle(KAI, con1, 'n')[0]
    push2 = foot_on(KAI, P(K['run_push'], 0, 1), 'n', near_pin1)
    fl2 = P(K['run_flight'], push2['x'] + 0.62, 1)
    con2 = P(swap(K['run_contact']), fl2['x'] + 0.5, 1)
    far_pin2 = ankle(KAI, con2, 'f')[0]
    push3 = foot_on(KAI, P(swap(K['run_push']), 0, 1), 'f', far_pin2)
    fl3 = P(swap(K['run_flight']), push3['x'] + 0.6, 1)
    cbreak = P(K['cross_break'], fl3['x'] + 0.42, 1, dy=0.02)
    L = ankle(KAI, cbreak, 'n')[0]                     # KAI's lead (left) foot: the pivot for everything
    cext = foot_on(KAI, P(K['cross_ext'], 0, 1), 'n', L)
    cover = foot_on(KAI, P(K['cross_over'], 0, 1), 'n', L)
    fist = hand(KAI, cext, 'f')

    # ================================================================ SEN placement
    # SEN's front foot stays 8 cm clear of KAI's lead foot; the sway-back does the rest
    slip0 = P(S['slip_back'], 0, -1)
    SX = (L + 0.08) - ankle(SEN, slip0, 'n')[0]
    sslip = P(S['slip_back'], SX, -1)
    sg = foot_on(SEN, P(S['guard'], 0, -1), 'n', ankle(SEN, sslip, 'n')[0])
    SG = sg['x']
    sneu = P(S['neutral'], SG, -1)
    sb = P(S['bounce'], SG, -1)
    miss = head_of(SEN, sslip)[0] - SEN.head_r - fist[0]

    # ================================================================ 1A / 1B KAI idle -> fists up
    breathe(k, 0, 64, kneu, period=40)
    k.key(65, kneu, ease='hold', lock='nf')
    cu = dict(yaw=28)
    k.key(66, P(K['neutral'], KX, 1, **cu), lock='nf', label='CU idle')
    k.key(76, P(K['neutral'], KX, 1, dy=0.012, **cu), lock='nf')
    k.key(80, P(K['neutral'], KX, 1, dy=-0.035, head=16, an=-2, en=30, af=-12, ef=34, **cu), ease='acc',
          label='antic: shoulders drop')
    k.key(82, P(K['neutral'], KX, 1, dy=-0.02, head=10, an=8, en=120, af=-2, ef=128, **cu), ease='lin',
          label='breakdown: elbows fold first')
    k.key(85, P(K['guard'], KX, 1, an=62, en=104, af=36, ef=150, head=4, **cu), ease='dec',
          label='fists up (overshoot)')
    k.key(89, P(K['guard'], KX, 1, **cu), ease='smooth', label='settle')
    k.key(96, P(K['guard'], KX, 1, dy=0.01, **cu))
    k.key(101, P(K['guard'], KX, 1, **cu), ease='hold')
    k.lag(80, 92, 'head', 1)

    # ================================================================ 1D dash + straight right
    k.key(132, kg, lock='nf', label='wide: guard')
    k.key(136, P(K['guard'], KX, 1, dy=0.01), lock='nf')
    k.key(140, kg, ease='smooth', lock='nf', label='antic: coil')
    k.key(145, launch, ease='acc', lock='nf', label='launch (compressed)')
    k.key(147, push1, ease='lin', lock='f', label='push-off')
    k.key(149, fl1, ease='lin', label='flight')
    k.key(151, con1, ease='lin', lock='n', label='contact')
    k.key(153, push2, ease='lin', lock='n')
    k.key(155, fl2, ease='lin')
    k.key(157, con2, ease='lin', lock='f')
    k.key(159, push3, ease='lin', lock='f')
    k.key(161, fl3, ease='lin')
    k.key(162, cbreak, ease='lin', lock='n', label='cross breakdown (smear)')
    k.key(164, cext, ease='dec', lock='n', label='cross EXTREME: near miss')
    k.key(167, cover, ease='smooth', lock='n', label='over-extended')
    k.smear(162, 165, ['af'])
    k.lag(147, 162, 'head', 1)

    # ================================================================ travelling 360 spinning backfist
    spin1 = foot_on(KAI, P(K['spin_a'], 0, 1, yaw=-55), 'n', L)
    spin2 = foot_on(KAI, P(K['spin_back'], 0, -1, yaw=-55), 'f', L)
    spin3 = foot_on(KAI, P(K['spin_back'], 0, -1, yaw=0), 'f', L)
    spin4 = foot_on(KAI, P(K['spin_front'], 0, -1, yaw=60), 'f', L)
    bwind = foot_on(KAI, P(K['bf_wind'], 0, 1, yaw=50), 'n', L)
    bext = foot_on(KAI, P(K['bf_ext'], 0, 1), 'n', L)
    bfol = foot_on(KAI, P(K['bf_follow'], 0, 1), 'n', L + 0.03)
    k.key(168, spin1, ease='lin', label='spin: back to camera')
    k.key(169, spin2, ease='lin')
    k.key(170, spin3, ease='lin', label='spin: back to SEN')
    k.key(171, spin4, ease='lin', label='spin: facing camera')
    k.key(172, bwind, ease='lin')
    k.key(173, bext, ease='dec', label='backfist EXTREME: over SEN')
    k.key(176, bfol, ease='smooth', label='over-rotation: body open')
    k.smear(173, 174, ['af'])
    k.smear(174, 176, ['af'], 0.6)
    bfol2 = P(bfol, bfol['x'] + 0.02, 1, af=112, lean=24)
    k.key(178, bfol2, ease='lin')

    # ================================================================ SEN
    breathe(s, 0, 100, sneu, period=44)
    scu = dict(yaw=28)
    s.key(101, sneu, ease='hold', lock='nf')
    s.key(102, P(S['neutral'], SG, -1, **scu), lock='nf')
    s.key(108, P(S['neutral'], SG, -1, head=6, **scu), ease='smooth', lock='nf')
    s.key(115, P(S['neutral'], SG, -1, head=2, an=14, en=118, af=-2, ef=60, **scu), ease='smooth',
          label='breakdown: forearm rises first')
    s.key(122, P(S['guard'], SG, -1, head=-2, **scu), ease='smooth', label='open-hand guard')
    s.on_twos(108, 122)
    s.key(131, P(S['guard'], SG, -1, **scu), ease='hold')
    bounce(s, 132, 160, sg, sb, period=12)
    s.key(160, sg, ease='smooth', lock='n')
    s.key(161, sg, ease='whip', lock='n', label='reads the cross late')
    s.key(164, sslip, ease='dec', lock='n', label='lean back: misses by inches')
    s.key(165, P(S['slip_back'], SX, -1, lean=-18), ease='smooth', lock='n')
    s.lag(161, 166, 'head', 1)
    # glide out (a deliberate slide), then drop under the backfist
    k_hip_173 = bext['x']
    X2 = k_hip_173 + 0.98
    s.key(167, P(S['glide'], SX + 0.45, -1), ease='dec', label='glides out')
    s.key(170, P(S['glide'], X2, -1, dy=-0.04), ease='dec')
    sduck = P(S['duck'], X2, -1)
    s.key(173, sduck, ease='dec', lock='nf', label='level change: arm passes over')
    s.key(174, P(S['duck'], X2, -1, dy=-0.02), ease='lin', lock='nf')
    # turn the back to KAI, chamber, kick
    target = solve(KAI, bfol2)
    tx, ty = target.hip[0] + 0.12, target.hip[1] + 0.32
    kick0 = P(S['backkick_ext'], 0, 1)
    toe_dx = ankle(SEN, kick0, 'f')[0]
    kick_x = tx - toe_dx + 0.04
    t1 = mix(sduck, P(S['backkick_chamber'], X2, -1), 0.45, yaw=60, face=-1, x=X2 + 0.16, lean=20)
    t2 = P(S['backkick_chamber'], (X2 + kick_x) / 2 + 0.05, 1, yaw=60, ln=40, kn=80)
    chamber = P(S['backkick_chamber'], kick_x + 0.06, 1)
    kick = P(S['backkick_ext'], kick_x, 1)
    s.key(175, t1, ease='lin', label='turn (facing camera)')
    s.key(176, t2, ease='lin')
    s.key(177, chamber, ease='acc', label='chamber')
    s.key(179, kick, ease='dec', label='back kick CONTACT')
    s.smear(178, 180, ['lf'])
    s.key(184, P(S['backkick_chamber'], kick_x + 0.06, 1), ease='smooth', label='recoil')
    s.key(186, P(S['backkick_chamber'], kick_x + 0.1, 1, yaw=60), ease='lin')
    s.key(187, P(S['guard'], kick_x + 0.12, -1, yaw=60, dy=0.05), ease='lin')
    s.key(190, P(S['guard'], kick_x + 0.14, -1), ease='dec', lock='nf', label='guard reset')
    sg2 = P(S['guard'], kick_x + 0.14, -1)
    bounce(s, 192, 240, sg2, P(S['bounce'], kick_x + 0.14, -1), period=12)

    # ================================================================ KAI knocked back
    hx = bfol2['x']
    k.key(179, bfol2, ease='lin', label='CONTACT')
    k.key(180, P(K['hit_gut'], hx - 0.30, 1, dy=0.02), ease='dec', label='C-fold around the kick, lifted')
    k.key(183, P(K['hit_gut'], hx - 0.85, 1, dy=-0.06, bend=40), ease='dec', xease='lin')
    k.key(186, P(K['skid_fight'], hx - 1.35, 1), ease='smooth', xease='dec', label='lands, fights the slide')
    k.key(191, P(K['skid'], hx - 1.85, 1), ease='smooth', xease='dec')
    skid_end = with_hand_on_ground(KAI, P(K['skid'], hx - 2.15, 1, head=-2), 'n', 0.42)
    k.key(198, skid_end, ease='smooth', xease=('dec', 3), label='skid stops: three-point crouch')
    k.lag(181, 198, 'arms', 2)
    k.lag(180, 196, 'head', 1)
    k.key(206, skid_end, ease='smooth', lock='nf', hands='n')
    look = P(skid_end, skid_end['x'], 1, head=-16, yaw=20)
    k.key(212, look, ease='dec', lock='nf', hands='n', label='looks up')
    k.key(221, P(look, look['x'], 1, dy=0.008), ease='hold', lock='nf', hands='n')
    kgl = P(K['guard'], skid_end['x'] + 0.12, 1, dy=-0.05, lean=18, bend=14, head=12)
    k.key(222, P(skid_end, skid_end['x'], 1, head=-14), lock='nf')
    k.key(225, P(skid_end, skid_end['x'], 1, head=-14, dy=-0.03), ease='smooth', lock='nf')
    k.key(232, kgl, ease='smooth', label='rises: lower, warier guard')
    k.key(239, P(kgl, kgl['x'], 1, dy=0.01), ease='smooth')
    k.lag(225, 236, 'arms', 2)

    seq.add(k, z=0)
    seq.add(s, z=1)
    seq.zorder(167, ['SEN', 'KAI'])
    seq.zorder(174, ['KAI', 'SEN'])

    # ================================================================ camera
    c = seq.cam
    c.key(0, cx=0.0, cy=1.25, h=6.4, ease='lin')
    c.key(65, cx=0.0, cy=1.2, h=5.9)
    kh = head_of(KAI, P(K['guard'], KX, 1, yaw=28))
    c.key(66, cut=True, cx=kh[0] + 0.32, cy=kh[1] - 0.14, h=1.35, ease='lin')
    c.key(101, cx=kh[0] + 0.3, cy=kh[1] - 0.12, h=1.22)
    sh = head_of(SEN, P(S['guard'], SG, -1, yaw=28))
    c.key(102, cut=True, cx=sh[0] - 0.32, cy=sh[1] - 0.14, h=1.35, ease='lin')
    c.key(131, cx=sh[0] - 0.3, cy=sh[1] - 0.12, h=1.22)
    mid0 = (KX + SG) / 2
    c.key(132, cut=True, cx=mid0, cy=1.1, h=5.6, ease='smooth')
    c.key(140, cx=mid0, cy=1.1, h=5.5, ease='acc')
    c.key(160, cx=mid0 + 0.3, cy=1.0, h=4.3, fw=0.65, ox=0.15, ease='smooth')
    c.key(179, cy=1.0, h=3.9, fw=0.65, ox=0.2, ease='dec')
    c.key(198, cy=1.05, h=5.2, fw=0.55, ox=0.0, ease='smooth')
    c.key(203, cy=1.05, h=5.25)
    ch = head_of(KAI, look)
    c.key(204, cut=True, cx=ch[0] + 0.3, cy=ch[1] - 0.02, h=1.15, ease='lin')
    c.key(221, cx=ch[0] + 0.28, cy=ch[1] - 0.01, h=1.0)
    mid1 = (skid_end['x'] + kick_x) / 2
    c.key(222, cut=True, cx=mid1, cy=1.1, h=5.2, ease='lin')
    c.key(239, cx=mid1, cy=1.1, h=4.9)

    # ================================================================ fx / sound
    seq.fade(0, 20, 1.0, 0.0)
    seq.cards.append((86, 101, name_card('KAI', 'THE FURNACE', KAI.near, 'right')))
    seq.cards.append((110, 131, name_card('SEN', 'THE TIDE', SEN.near, 'left')))

    def motes(fx, sc, rf, a):
        if a % 3 == 0:
            fx.dust(fx.rnd.uniform(-6, 6), fx.rnd.uniform(0.05, 1.4), n=1, dirx=-1, speed=1.2, size=0.03,
                    life=(30, 50), up=0.05, alpha=0.35)
    seq.emit(0, 240, motes)
    seq.at(146, lambda fx, sc, rf: fx.dust(far_pin, n=10, dirx=-1, speed=2.5, size=0.2, alpha=0.6))
    for f_, x_ in ((151, near_pin1), (157, far_pin2), (162, L)):
        seq.at(f_, lambda fx, sc, rf, x_=x_: fx.dust(x_, n=5, dirx=-1, speed=1.8, size=0.14, alpha=0.5))
    seq.emit(149, 162, lambda fx, sc, rf, a: fx.speedlines(k.eval(a)['x'], 1.1, 1, n=2, length=1.6, spread=0.6))

    def near_miss(fx, sc, rf):
        fx.streak(fist[0] + 0.7, fist[1], length=1.1, life=5, col=(1, 0.95, 0.85), w=0.022)
        fx.dust(SX + 0.2, n=4, dirx=1, speed=1.5, size=0.12, alpha=0.4)
    seq.at(164, near_miss)
    seq.hitstop(164, 2)
    seq.emit(168, 172, lambda fx, sc, rf, a: fx.dust(s.eval(a)['x'] - 0.1, n=2, dirx=1, speed=1.4, size=0.1,
                                                      alpha=0.45, life=(10, 18)))
    seq.at(173, lambda fx, sc, rf: fx.streak(hand(KAI, bext, 'f')[0] - 0.2, hand(KAI, bext, 'f')[1],
                                             length=0.9, life=4, w=0.018))
    seq.sfx(146, 'dash')
    seq.sfx(162, 'whoosh_big')
    seq.sfx(169, 'whoosh')
    seq.sfx(172, 'whoosh')
    seq.sfx(177, 'whoosh')

    kick_pt = ankle(SEN, kick, 'f')
    seq.impact(179, kick_pt[0] - 0.04, kick_pt[1] + 0.02, dirx=-1, diry=0.15, power=1.0, stop=4)
    seq.at(179, lambda fx, sc, rf: fx.flash_screen(0.18, (1, 0.92, 0.85)))

    def skid(fx, sc, rf, a):
        p = k.eval(a)
        fx.dust(ankle(KAI, p, 'n')[0], n=2, dirx=-1, speed=2.2, size=0.13, alpha=0.5, life=(10, 20))
        fx.dust(ankle(KAI, p, 'f')[0], n=1, dirx=-1, speed=1.6, size=0.11, alpha=0.4, life=(10, 18))
    seq.emit(183, 197, skid)
    seq.sfx(183, 'skid')

    def marks(fx, sc, rf):
        p0 = P(K['skid'], hx - 1.5, 1)
        fx.skidmark(ankle(KAI, skid_end, 'n')[0], ankle(KAI, p0, 'n')[0] + 0.3)
        fx.skidmark(ankle(KAI, skid_end, 'f')[0], ankle(KAI, p0, 'f')[0] + 0.3, w=0.028)
    seq.at(197, marks)

    def eye_flare(fx, sc, rf):
        from rig import eye_point
        e, _, _ = eye_point(solve(KAI, k.eval(213)))
        fx.glint(e[0], e[1], size=0.16, life=8, col=(1, 0.9, 0.7))
    seq.at(213, eye_flare)
    seq.sfx(213, 'glint')

    for f_, t_ in [(0, '1A wide establishing'), (66, '1B CU KAI'), (102, '1C CU SEN'), (132, '1D wide exchange'),
                   (204, '1E MCU KAI'), (222, '1F wide reset')]:
        seq.note(f_, t_)
    seq.geometry = dict(lead_foot=L, sen_front_gap=0.08, miss_cm=miss * 100,
                        hip_gap_backfist=X2 - bext['x'], hip_gap_kick=kick_x - hx,
                        sen_head_y_duck=head_of(SEN, sduck)[1], kai_fist_y_backfist=hand(KAI, bext, 'f')[1])
    seq.state = dict(kai=k.eval(239), sen=s.eval(239))
    return seq


if __name__ == '__main__':
    for kk, v in build().geometry.items():
        print(f'{kk:22s} {v:7.2f}')
