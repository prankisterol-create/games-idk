"""SEQUENCE 2 — ADAPTATION (anim frames 0-167, ~7 s)

  2A   0- 43  KAI stalks in with step-drag shuffles (on 2s, feet pinned); SEN steps in to meet him
  2B  44- 63  feint: KAI repeats S1's cross coil -> SEN sways back (conditioned) -> no punch:
              rear-leg low kick -> SEN checks shin-to-shin (FIRST FLASH FRAME) -> off balance, hops back
  2C  64-109  press: step-jab, step-jab (parried), cross -> SEN redirects the arm, ducks under and
              passes BEHIND KAI, palm strike to his back; KAI stumbles 1.6 m and catches himself.
              The fighters have swapped sides.
  2D 110-167  KAI turns and re-squares, breathing hard; embers start lifting off him (MCU), SEN resets.
"""
from rig import KAI, SEN, solve
from poses import LIB, with_hand_on_ground
from engine import Track
from scene import Sequence
from author import P, foot_on, ankle, hand, head_of, breathe, bounce, mix, stance_at, lifted

K, S = LIB['KAI'], LIB['SEN']


def shuffle(track, f, F, R, d, base, lift=0.1, face=1):
    """Step-drag: front foot steps d, then the rear foot drags up d. 12 frames."""
    b = track.b
    s0 = stance_at(b, base, F, R, face)
    mid1 = lifted(b, stance_at(b, base, F, R, face, frac=0.62), 'n', F + d * face * 0.55, lift)
    wide = stance_at(b, base, F + d * face, R, face, frac=0.6)
    mid2 = lifted(b, stance_at(b, base, F + d * face, R, face, frac=0.66), 'f', R + d * face * 0.5, lift * 0.6)
    s1 = stance_at(b, base, F + d * face, R + d * face, face)
    track.key(f, s0, lock='nf')
    track.key(f + 3, mid1, lock='f', ease='smooth')
    track.key(f + 6, wide, lock='nf', ease='smooth')
    track.key(f + 9, mid2, lock='n', ease='smooth')
    track.key(f + 12, s1, lock='nf', ease='smooth')
    return F + d * face, R + d * face


def build():
    seq = Sequence('S2', 168, wind=-0.5)
    k = Track(KAI)
    s = Track(SEN)

    # ------------------------------------------------ geometry first: solve the low kick
    # SEN checks with his front shin raised; his rear foot is planted at SR.
    SR = 4.15
    check = foot_on(SEN, P(S['check'], 0, -1), 'f', SR)
    Jc = solve(SEN, check)
    shin = ((Jc.knee_n[0] + Jc.ankle_n[0]) / 2, (Jc.knee_n[1] + Jc.ankle_n[1]) / 2)
    lk = P(K['lk_ext'], 0, 1)
    Jk = solve(KAI, lk)
    toe_dx = Jk.ankle_f[0] - Jk.hip[0]
    lk_ext = P(K['lk_ext'], shin[0] - toe_dx - 0.02, 1)
    SUP = ankle(KAI, lk_ext, 'n')[0]                 # KAI's support foot during the kick
    # SEN's ready stance before the kick: rear foot SR, front foot 0.55 ahead (toward KAI)
    SF = SR - 0.55

    # ================================================================ KAI 2A stalk
    base = K['stalk']
    F, R = 1.10, 0.46
    k.key(0, stance_at(KAI, base, F, R), lock='nf', label='stalk')
    for f0 in (2, 16, 30):
        F, R = shuffle(k, f0, F, R, 0.40, base)
    k.on_twos(2, 44)
    # 2B feint: the S1 coil, with a lunging step that sets up the kick
    feintF = SUP
    feintR = R + (feintF - F) * 0.45
    feint = stance_at(KAI, K['cross_antic'], feintF, feintR, frac=0.42)
    k.key(44, stance_at(KAI, base, F, R), lock='nf')
    k.key(46, lifted(KAI, stance_at(KAI, K['cross_antic'], F, R, frac=0.6), 'n', (F + feintF) / 2, 0.1),
          lock='f', ease='acc', label='feint: S1 coil + step in')
    k.key(48, feint, lock='nf', ease='dec')
    k.key(50, P(feint, feint['x'], 1, dy=-0.01), lock='nf', ease='smooth', label='hold: SEN bites')
    lkc = foot_on(KAI, P(K['lk_chamber'], 0, 1), 'n', SUP)
    k.key(51, lkc, lock='n', ease='lin', label='low kick')
    k.key(52, lk_ext, lock='n', ease='dec', label='CONTACT shin on shin')
    k.smear(51, 53, ['lf'])
    k.key(55, foot_on(KAI, P(K['lk_chamber'], 0, 1, lf=10, kf=80), 'n', SUP), lock='n', ease='smooth',
          label='rebound')
    k.key(59, stance_at(KAI, base, SUP, SUP - 0.62), lock='nf', ease='dec')

    # ================================================================ SEN 2A/2B
    sg_base = S['guard']
    s.key(0, P(S['bounce'], 4.16, -1), lock='nf')
    bounce(s, 0, 18, P(S['guard'], 4.16, -1), P(S['bounce'], 4.16, -1), period=12)
    # one calm step toward KAI (meets him)
    sg0 = P(S['guard'], 4.16, -1)
    F0, R0 = ankle(SEN, sg0, 'n')[0], ankle(SEN, sg0, 'f')[0]
    s.key(18, stance_at(SEN, sg_base, F0, R0, -1), lock='nf')
    s.key(21, lifted(SEN, stance_at(SEN, sg_base, F0, R0, -1, frac=0.6), 'n', (F0 + SF) / 2, 0.08), lock='f')
    s.key(24, stance_at(SEN, sg_base, SF, R0, -1, frac=0.6), lock='nf')
    s.key(27, lifted(SEN, stance_at(SEN, sg_base, SF, R0, -1, frac=0.66), 'f', (R0 + SR) / 2, 0.06), lock='n')
    sready = stance_at(SEN, sg_base, SF, SR, -1)
    s.key(30, sready, lock='nf', label='meets him')
    bounce(s, 32, 46, sready, stance_at(SEN, S['bounce'], SF, SR, -1), period=12)
    sslip = stance_at(SEN, S['slip_back'], SF, SR, -1, frac=0.25)
    s.key(46, sready, lock='nf', ease='whip')
    s.key(49, sslip, lock='nf', ease='dec', label='sways back (conditioned)')
    s.key(50, sslip, lock='nf', ease='whip')
    s.key(52, check, lock='f', ease='dec', label='check: shin up')
    # knocked off balance: two hops back on the rear leg
    s.key(54, P(S['hop'], check['x'] + 0.25, -1, dy=0.02), ease='dec', jump=0.12, label='hop back')
    s.key(57, foot_on(SEN, P(S['hop'], 0, -1, lf=-4, kf=20, dy=-0.12), 'f', SR + 0.42), ease='lin')
    s.key(59, P(S['hop'], check['x'] + 0.62, -1, an=120, af=-70), ease='dec', jump=0.08)
    s.key(62, stance_at(SEN, sg_base, SR + 0.15, SR + 0.72, -1), lock='nf', ease='dec', label='lands')

    # ================================================================ 2C press: step-jab, step-jab, cross
    SF2, SR2 = SR + 0.15, SR + 0.72
    sg2 = stance_at(SEN, sg_base, SF2, SR2, -1)
    face2 = head_of(SEN, sg2)
    jab0 = P(K['jab_ext'], 0, 1)
    reach = hand(KAI, jab0, 'n')[0] - jab0['x']
    # jab 1 lands on SEN's parrying hand ~0.22 m in front of his face
    j1x = face2[0] - 0.22 - reach
    j1 = P(K['jab_ext'], j1x, 1)
    j1F, j1R = ankle(KAI, j1, 'n')[0], ankle(KAI, j1, 'f')[0]
    k.key(64, stance_at(KAI, base, SUP, SUP - 0.62), lock='nf')
    k.key(66, lifted(KAI, stance_at(KAI, K['jab_antic'], SUP, SUP - 0.62, frac=0.62), 'n',
                     (SUP + j1F) / 2, 0.08), lock='f', ease='acc')
    k.key(68, stance_at(KAI, K['jab_ext'], j1F, SUP - 0.62, frac=0.62), lock='nf', ease='dec',
          label='step-jab 1 (parried)')
    k.smear(67, 68, ['an'], 0.7)
    jr1 = stance_at(KAI, base, j1F, j1F - 0.64)
    k.key(71, jr1, lock='n', ease='smooth')
    # SEN parries and gives a step each time
    s.key(64, sg2, lock='nf')
    s.key(68, stance_at(SEN, S['parry_n'], SF2 + 0.12, SR2 + 0.1, -1), ease='whip', label='parry (lead hand)')
    sg3 = stance_at(SEN, sg_base, SF2 + 0.3, SR2 + 0.3, -1)
    s.key(72, sg3, lock='nf', ease='smooth')
    face3 = head_of(SEN, sg3)
    j2x = face3[0] - 0.22 - reach
    j2 = P(K['jab_ext'], j2x, 1)
    j2F = ankle(KAI, j2, 'n')[0]
    k.key(72, jr1, lock='nf')
    k.key(74, lifted(KAI, stance_at(KAI, K['jab_antic'], j1F, j1F - 0.64, frac=0.62), 'n', (j1F + j2F) / 2, 0.08),
          lock='f', ease='acc')
    k.key(76, stance_at(KAI, K['jab_ext'], j2F, j1F - 0.64, frac=0.62), lock='nf', ease='dec',
          label='step-jab 2 (parried)')
    k.smear(75, 76, ['an'], 0.7)
    s.key(76, stance_at(SEN, S['parry_f'], SF2 + 0.42, SR2 + 0.4, -1), ease='whip', label='parry (rear hand)')
    # the cross: SEN stops parrying and goes under it
    coil = stance_at(KAI, K['cross_antic'], j2F, j2F - 0.68, frac=0.4)
    k.key(78, coil, lock='nf', ease='acc', label='cross coil')
    cb = stance_at(KAI, K['cross_break'], j2F + 0.12, j2F - 0.68, frac=0.6)
    k.key(80, cb, lock='f', ease='lin')
    ce = stance_at(KAI, K['cross_ext'], j2F + 0.3, j2F - 0.6, frac=0.66)
    k.key(82, ce, lock='n', ease='dec', label='cross: caught and redirected')
    k.smear(80, 83, ['af'])
    # pulled past: SEN's redirect drags him forward
    co = P(K['cross_over'], ce['x'] + 0.25, 1, lean=46, af=124)
    k.key(85, foot_on(KAI, co, 'n', ankle(KAI, ce, 'n')[0] + 0.1), ease='dec', label='pulled past')
    st1 = P(K['stumble_a'], co['x'] + 0.9, 1)
    # SEN goes under and behind
    sred = stance_at(SEN, S['redirect'], j2F + 0.62, SR2 + 0.2, -1, frac=0.5)
    s.key(80, sred, ease='whip', label='redirect: hand on the wrist, under the arm')
    s.key(83, P(S['duck'], ce['x'] + 0.55, -1, an=140, en=10), ease='smooth')
    s.key(86, P(S['duck'], ce['x'] - 0.1, -1, yaw=60), ease='lin', label='passes behind')
    s.key(88, P(S['duck'], ce['x'] - 0.55, 1, yaw=60), ease='lin')
    behind_x = co['x'] - 0.25
    spush0 = P(S['palm_push'], 0, 1)
    pdx = hand(SEN, spush0, 'n')[0] - spush0['x']
    kback = solve(KAI, P(co, co['x'] + 0.34, 1, lean=34, bend=-16, head=-22))
    push_x = kback.hip[0] - 0.12 - pdx
    s.key(90, stance_at(SEN, sg_base, push_x + 0.15, push_x - 0.35, 1), lock='nf', ease='dec')
    s.key(92, stance_at(SEN, S['palm_antic'], push_x + 0.2, push_x - 0.35, 1, frac=0.3), lock='f', ease='acc')
    spush = stance_at(SEN, S['palm_push'], push_x + 0.42, push_x - 0.35, 1, frac=0.5)
    s.key(94, spush, lock='nf', ease='dec', label='palm strike to the back')
    s.smear(93, 95, ['an', 'af'], 0.7)
    s.key(100, P(spush, spush['x'], 1, dy=0.01, an=82, af=76), lock='nf', ease='smooth', label='follow-through')
    k.key(88, stance_at(KAI, K['stumble_b'], ankle(KAI, ce, 'n')[0] + 0.62, ankle(KAI, ce, 'n')[0] + 0.05,
                        frac=0.5, af=120, lean=44), lock='n', ease='smooth', label='staggers forward a step')
    k.key(91, P(co, co['x'] + 0.3, 1, lean=30, bend=4, af=90, ef=40, an=40, en=110), ease='smooth',
          label='tries to turn')
    k.key(94, P(co, co['x'] + 0.34, 1, lean=34, bend=-16, head=-22, af=100, ef=30), ease='lin',
          label='CONTACT (back)')
    k.key(97, st1, ease='dec', label='stumbles')
    sb_ = stance_at(KAI, K['stumble_b'], st1['x'] + 0.55, st1['x'] - 0.1, frac=0.5)
    k.key(101, sb_, lock='n', ease='smooth')
    k.key(104, P(K['stumble_a'], sb_['x'] + 0.55, 1, lean=46), ease='smooth')
    catch = with_hand_on_ground(KAI, stance_at(KAI, K['catch'], sb_['x'] + 1.1, sb_['x'] + 0.4, frac=0.5), 'n', 0.5)
    k.key(110, catch, lock='nf', ease='dec', label='catches himself')
    k.lag(95, 112, 'arms', 2)
    k.lag(95, 112, 'head', 1)
    k.key(114, catch, lock='nf', hands='n', ease='smooth')

    # ================================================================ 2D turn and re-square
    cx_ = catch['x']
    kf_ = ankle(KAI, catch, 'n')[0]
    kr_ = ankle(KAI, catch, 'f')[0]
    k.key(117, stance_at(KAI, base, kf_, kr_, 1, dy=0.04, yaw=40), lock='nf', ease='smooth', label='turns')
    k.key(120, stance_at(KAI, base, kr_ + 0.1, kf_, -1, yaw=50, front='n'), ease='smooth')
    kg2 = stance_at(KAI, K['guard'], kr_ + 0.1, kf_ + 0.05, -1, dy=0.0)
    k.key(124, kg2, lock='nf', ease='dec', label='re-squared, breathing hard')
    breathe(k, 124, 168, kg2, amp=0.03, period=16, arm=4.0)
    k.key(167, P(kg2, kg2['x'], -1), lock='nf')
    sg4 = stance_at(SEN, sg_base, spush['x'] + 0.3, spush['x'] - 0.32, 1)
    s.key(106, sg4, ease='smooth', label='resets')
    s.key(110, P(sg4, sg4['x'], 1, an=40, en=70), ease='smooth', label='shakes out the hand')
    s.key(112, P(sg4, sg4['x'], 1, an=30, en=110), ease='smooth')
    s.key(114, P(sg4, sg4['x'], 1, an=42, en=64), ease='smooth')
    s.key(118, sg4, ease='smooth', lock='nf')
    bounce(s, 120, 168, sg4, stance_at(SEN, S['bounce'], spush['x'] + 0.3, spush['x'] - 0.32, 1), period=12)

    seq.add(k, z=1)
    seq.add(s, z=0)
    seq.zorder(46, ['KAI', 'SEN'])
    seq.zorder(80, ['SEN', 'KAI'])       # SEN passes behind
    seq.zorder(92, ['KAI', 'SEN'])
    seq.depth.append((80, 92, 'SEN', 0.35))

    # ================================================================ camera
    c = seq.cam
    c.key(0, cx=2.4, cy=1.1, h=4.9, fw=0.0, ease='smooth')
    c.key(40, cx=2.9, cy=1.05, h=4.3, fw=0.5, ox=0.1, ease='smooth')
    c.key(52, cy=1.0, h=4.0, fw=0.6, ox=0.15, ease='smooth')
    c.key(80, cy=1.05, h=4.2, fw=0.7, ox=0.0, ease='smooth')
    c.key(110, cy=1.1, h=4.8, fw=0.6, ox=0.0, ease='smooth')
    c.key(123, cy=1.1, h=4.8, fw=0.6)
    kh = head_of(KAI, P(kg2, kg2['x'], -1, yaw=30))
    c.key(124, cut=True, cx=kh[0] - 0.3, cy=kh[1] - 0.12, h=1.3, ease='lin')
    c.key(145, cx=kh[0] - 0.28, cy=kh[1] - 0.1, h=1.15)
    c.key(146, cut=True, cx=(kg2['x'] + sg4['x']) / 2, cy=1.1, h=4.9, ease='lin')
    c.key(167, cx=(kg2['x'] + sg4['x']) / 2, cy=1.1, h=4.7)
    # the MCU is shot 3/4 toward camera
    for f_ in range(124, 146):
        pass

    # ================================================================ fx / sound
    def motes(fx, sc, rf, a):
        if a % 3 == 0:
            fx.dust(fx.rnd.uniform(-4, 9), fx.rnd.uniform(0.05, 1.4), n=1, dirx=-1, speed=1.2, size=0.03,
                    life=(30, 50), up=0.05, alpha=0.35)
    seq.emit(0, 168, motes)
    seq.impact(52, shin[0], shin[1], dirx=1, diry=0.2, power=0.8, stop=3, style='white', sound='hit_shin')
    seq.at(53, lambda fx, sc, rf: fx.dust(SR, n=6, dirx=1, speed=2.0, size=0.14, alpha=0.5))
    for f_, kk in ((68, 'n'), (76, 'f')):
        def parry(fx, sc, rf, kk=kk, f_=f_):
            p = s.eval(f_)
            x, y = hand(SEN, p, kk)
            fx.sparks(x, y, 0, 1, n=6, speed=4, spread=0.6, life=(3, 6))
            fx.ring(x, y, 0.02, 0.25, life=4, w=0.02)
            sc.shake.add(rf, 0.02, frames=3, dx=1, dy=0, seed=f_)
        seq.at(f_, parry)
        seq.sfx(f_, 'parry')
    seq.hitstop(68, 1)
    seq.hitstop(76, 1)
    seq.sfx(51, 'whoosh')
    seq.sfx(80, 'whoosh_big')
    seq.sfx(86, 'whoosh')
    pp = hand(SEN, spush, 'n')
    seq.impact(94, pp[0] + 0.05, pp[1], dirx=1, diry=0.0, power=0.55, stop=2, sound='hit')
    for f_ in (101, 110):
        seq.at(f_, lambda fx, sc, rf, f_=f_: fx.dust(ankle(KAI, k.eval(f_), 'n')[0], n=4, dirx=1, speed=1.5,
                                                    size=0.12, alpha=0.45))
    seq.sfx(101, 'step')
    seq.sfx(110, 'step')

    def embers(fx, sc, rf, a):
        heat = min(1.0, (a - 98) / 60.0)
        n = 1 if (a % max(1, int(3 - 2 * heat)) == 0) else 0
        if n:
            fx.embers(solve(KAI, k.eval(a)), n=1 + int(heat * 1.5), heat=0.6 + 0.6 * heat)
    seq.emit(98, 168, embers)
    seq.glow['KAI'] = lambda a: 1.0 + 0.8 * max(0.0, min(1.0, (a - 110) / 40.0))
    seq.sfx(130, 'breath')

    for f_, t_ in [(0, '2A stalk'), (44, '2B feint'), (52, '2B check'), (64, '2C press'), (82, '2C redirect'),
                   (94, '2C palm'), (110, '2D reset'), (124, '2D MCU KAI'), (146, '2D wide')]:
        seq.note(f_, t_)
    seq.geometry = dict(kick_support_foot=SUP, shin_x=shin[0], shin_y=shin[1], kai_front_at_feint=feintF,
                        sen_front=SF, jab1_hip=j1x, kai_back_x=kback.hip[0], sen_push_x=push_x)
    return seq


if __name__ == '__main__':
    for kk, v in build().geometry.items():
        print(f'{kk:22s} {v:7.2f}')
