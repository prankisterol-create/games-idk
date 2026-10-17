"""DOOM vs SPIDER-MAN -- SEQUENCE 3: THE GAUNTLET (194 animation frames, ~8.5 s)

  3A   0- 46  DOOM does not chase: he fires a barrage, left palm, right palm, left. SPIDER-MAN
              walks *into* it -- leans back under the first bolt, hops the second (it blows up the
              roof behind him), knee-slides under the third -- and closes the distance.
  3B  47- 71  Out of the slide into a flying kick: blocked on the gauntlet (flash frame). Jab:
              parried. Cross: parried. The third punch is CAUGHT.
  3C  72- 99  DOOM's gauntlet discharges into him (dark impact frames, 4-frame hit-stop):
              SPIDER-MAN convulses inside a cage of arcs.
  3D 100-131  DOOM hauls him up and hurls him across the roof: tumble, roll, skid to his knees.
  3E 132-193  MCU SPIDER-MAN, smoking, shakes his head. DOOM points at him: the verdict. DOOM is
              standing in the spreading pool from the tank (it matters later).
"""
import math
import random

from heroes import SPIDER, DOOM
from heroposes import LIB2
from engine import Track, arc
from scene import Sequence
from author import P, foot_on, ankle, hand, head_of, breathe, stance_at, mix, swap
from rooftop import Rooftop
from rig import solve, plant_hand
import powers as pw
import dv02
from dv02 import HOLE, LEAK_F, add_water, aim

SP, DM = LIB2['SPIDER'], LIB2['DOOM']
N = 194


def persistent(seq, prev, n):
    """Marks left by earlier sequences: scorches, fallen webbing."""
    for x in prev['scorches']:
        seq.overlay(0, n, pw.scorch(x, -999, w=0.85), layer='back')
    for i, p in enumerate(prev['splats']):
        seq.overlay(0, n, pw.splat_at(p, -999, 10 ** 6, r=0.1, seed=4 + i), layer='back')


def build():
    random.seed(303)
    st2 = dv02.build().state
    prev = dict(scorches=[st2['scorch_x']], splats=st2['roof_splats'] + [st2['torn']])
    seq = Sequence('D3', N, wind=-0.5)
    seq.stage = Rooftop(hole=(-10 ** 6, HOLE[0], HOLE[1]))
    since0 = 190 - LEAK_F
    add_water(seq, since0, N)
    persistent(seq, prev, N)
    d = Track(DOOM)
    s = Track(SPIDER)
    S0, D0 = st2['spider'], st2['doom']
    SF, SR = ankle(SPIDER, S0, 'n')[0], ankle(SPIDER, S0, 'f')[0]
    DF, DR = ankle(DOOM, D0, 'n')[0], ankle(DOOM, D0, 'f')[0]
    sg = stance_at(SPIDER, SP['guard'], SF, SR, 1)

    # ================================================================ 3A barrage
    s.key(0, sg, lock='nf')
    s.key(9, P(sg, sg['x'], 1, dy=0.012, head=-18), ease='smooth', lock='nf')
    head_y = head_of(SPIDER, sg)[1]
    lb = stance_at(SPIDER, SP['lean_back'], SF, SR, 1)
    s.key(11, sg, ease='whip', lock='nf')
    s.key(13, lb, ease='dec', lock='nf', label='leans back under bolt 1')
    s.key(17, P(lb, lb['x'], 1, dy=-0.01), ease='smooth', lock='nf')
    s.key(20, sg, ease='smooth', lock='nf')
    santic = stance_at(SPIDER, SP['duck'], SF, SR, 1)
    s.key(22, santic, ease='acc', lock='nf', label='drops...')
    hop0 = P(SP['hop_tuck'], sg['x'] + 0.2, 1)
    hop0['y'] = 0.95
    land2 = stance_at(SPIDER, SP['land'], SF + 1.25, SR + 1.25, 1)
    s.path(24, 31, arc(24, 31, (hop0['x'], hop0['y']), (land2['x'], land2['y']), height=0.95, hang=2.2))
    s.key(24, hop0, ease='dec', label='...hops bolt 2')
    s.key(28, P(SP['hop_tuck'], 0, 1, lean=30), ease='smooth')
    s.key(31, land2, ease='dec', lock='nf')
    s.smear(23, 25, ['ln', 'lf'], 0.5)
    # two running strides into the knee slide
    r1 = foot_on(SPIDER, P(SP['jab_f'], 0, 1, an=-40, en=90, af=40, ef=90, hn='open', hf='open', lean=34), 'f',
                 ankle(SPIDER, land2, 'f')[0])
    s.key(33, r1, ease='lin', lock='f', label='runs in')
    sl0 = P(SP['slide'], r1['x'] + 0.55, 1)
    sl1 = P(SP['slide'], sl0['x'] + 1.4, 1)
    s.key(35, sl0, ease='lin', label='KNEE SLIDE under bolt 3')
    s.key(42, sl1, ease='dec', xease=('dec', 2.0))
    s.lag(33, 42, 'head', 1)

    # DOOM: left, right, left
    dant = stance_at(DOOM, DM['cast_antic'], DF, DR, -1)
    dantf = stance_at(DOOM, swap(DM['cast_antic']), DF, DR, -1)
    tA = (sg['x'] - 3.0, head_y + 0.05)
    castA = aim(DOOM, stance_at(DOOM, DM['cast'], DF, DR, -1), 'n', (sg['x'], head_y))
    tB = (SR - 0.7, 0.05)
    castB = aim(DOOM, stance_at(DOOM, swap(DM['cast']), DF, DR, -1), 'f', tB)
    J33 = solve(SPIDER, s.eval(36))
    tC_mid = (J33.hip[0], J33.head[1] + DOOM.head_r * 0 + 0.22)
    castC = aim(DOOM, stance_at(DOOM, DM['cast'], DF, DR, -1), 'n', tC_mid)
    d.key(0, D0, lock='nf')
    d.key(4, dant, ease='acc', lock='nf', label='left palm')
    d.key(9, mix(dant, castA, 0.5), ease='lin', lock='nf')
    d.key(10, castA, ease='dec', lock='nf', label='BOLT 1')
    d.key(14, P(castA, castA['x'], -1, an=castA['an'] + 16, en=12), ease='smooth', lock='nf')
    d.key(18, dantf, ease='acc', lock='nf', label='right palm')
    d.key(21, mix(dantf, castB, 0.5), ease='lin', lock='nf')
    d.key(22, castB, ease='dec', lock='nf', label='BOLT 2 (low)')
    d.key(26, P(castB, castB['x'], -1, af=castB['af'] + 16, ef=12), ease='smooth', lock='nf')
    d.key(30, dant, ease='acc', lock='nf', label='left palm')
    d.key(33, mix(dant, castC, 0.5), ease='lin', lock='nf')
    d.key(34, castC, ease='dec', lock='nf', label='BOLT 3')
    d.smear(9, 11, ['an'], 0.6)
    d.smear(21, 23, ['af'], 0.6)
    d.smear(33, 35, ['an'], 0.6)
    pA = pw.hand_tip(solve(DOOM, castA), 'n', 0.12)
    pB = pw.hand_tip(solve(DOOM, castB), 'f', 0.12)
    pC = pw.hand_tip(solve(DOOM, castC), 'n', 0.12)

    def extend(p0, p1, x_end):
        t = (x_end - p0[0]) / (p1[0] - p0[0])
        return (x_end, p0[1] + (p1[1] - p0[1]) * t)
    endA = extend(pA, (sg['x'], head_y), -9.0)
    endC = extend(pC, tC_mid, -9.0)
    vA = math.dist(pA, endA) / 11.0
    seq.overlay(10, 22, pw.bolt(pA, endA, 10, 21))
    seq.overlay(22, 28, pw.bolt(pB, tB, 22, 27))
    seq.overlay(34, 46, pw.bolt(pC, endC, 34, 45))
    for f0_, side in ((4, 'n'), (18, 'f'), (30, 'n')):
        seq.overlay(f0_, f0_ + 6, pw.charge('DOOM', side, lambda a, f0_=f0_: 0.06 * min(1.0, (a - f0_ + 1) / 4.0)))

    def blastB(fx, sc, rf):
        pw.explosion(fx, tB[0], 0.18, power=1.1, seed=27)
        fx.debris(tB[0], n=12, speed=3.0, up=4.5)
        fx.dust(tB[0], n=7, dirx=-1, speed=3.0, size=0.2, alpha=0.5, up=0.7, col=pw.GRIT)
        fx.crack(tB[0], n=7, length=1.0)
        sc.shake.add(rf, 0.07, frames=8, dx=0.2, dy=1.0, seed=27)
        fx.flash_screen(0.18, (0.6, 1.0, 0.65))
    seq.at(27, blastB)
    seq.overlay(27, N, pw.scorch(tB[0], 27, w=0.8, seed=6), layer='back')
    seq.overlay(2, 40, pw.spider_sense('SPIDER', lambda a: 0.9 if a < 37 else max(0.0, (40 - a) / 3.0)), layer='top')

    # ================================================================ 3B flying kick -> blocked
    dblock = stance_at(DOOM, DM['block'], DF, DR, -1)
    Jb = solve(DOOM, dblock)
    fore = ((Jb.elbow_n[0] + Jb.hand_n[0]) / 2, (Jb.elbow_n[1] + Jb.hand_n[1]) / 2 + 0.05)
    fk = P(SP['flykick'], 0, 1)
    Jfk = solve(SPIDER, fk)
    toe_dx, toe_dy = Jfk.toe_n[0] - fk['x'], Jfk.toe_n[1] - fk['y']
    kickp = P(SP['flykick'], fore[0] - 0.03 - toe_dx, 1)
    kickp['y'] = fore[1] - toe_dy
    s.path(44, 50, arc(44, 50, (sl1['x'] + 0.1, sl1['y'] + 0.2), (kickp['x'], kickp['y']), height=0.35, hang=1.6))
    s.key(44, P(SP['land'], sl1['x'] + 0.1, 1) | dict(y=sl1['y'] + 0.2), ease='dec', label='springs out of the slide')
    s.key(47, P(SP['chamber'], 0, 1, lean=-20, rot=0), ease='smooth')
    s.key(50, kickp, ease='dec', label='FLYING KICK: blocked')
    s.smear(48, 51, ['ln'], 0.9)
    d.key(42, P(DM['stand_wide'], castC['x'], -1), ease='smooth', lock='nf')
    d.key(47, dblock, ease='dec', lock='nf', label='forearm block')
    d.key(52, P(dblock, dblock['x'], -1, dy=-0.03, lean=-6, head=14), ease='dec', lock='nf')
    # rebound, land in a fighting stance at punching range
    fx_ = 2.62
    sfight = stance_at(SPIDER, SP['fight'], fx_ + 0.3, fx_ - 0.36, 1)
    s.path(51, 56, arc(51, 56, (kickp['x'] - 0.05, kickp['y']), (sfight['x'], sfight['y']), height=0.25, hang=1.6))
    s.key(51, P(SP['flykick'], 0, 1, ln=80, kn=50), ease='dec')
    s.key(56, sfight, ease='dec', lock='nf', label='lands at punching range')
    SF2, SR2 = ankle(SPIDER, sfight, 'n')[0], ankle(SPIDER, sfight, 'f')[0]

    def punch(name, f, side):
        q = stance_at(SPIDER, SP[name], SF2, SR2, 1)
        return q, (hand(SPIDER, q, side))
    j1, f1 = punch('jab_n', 59, 'n')
    j2, f2 = punch('jab_f', 64, 'f')
    j3, f3 = punch('jab_n', 70, 'n')
    j3 = P(j3, j3['x'], 1, lean=30, an=98)
    f3 = hand(SPIDER, j3, 'n')
    s.key(57, sfight, lock='nf', ease='acc')
    s.key(59, j1, lock='nf', ease='dec', label='jab: parried')
    s.key(62, sfight, lock='nf', ease='smooth')
    s.key(64, j2, lock='nf', ease='dec', label='cross: parried')
    s.key(67, sfight, lock='nf', ease='smooth')
    s.key(68, P(sfight, sfight['x'], 1, dy=-0.02, an=40, en=120), lock='nf', ease='acc')
    s.key(70, j3, lock='nf', ease='dec', label='straight: CAUGHT')
    s.smear(58, 60, ['an'], 0.6)
    s.smear(63, 65, ['af'], 0.6)
    s.smear(69, 71, ['an'], 0.6)
    pb1 = plant_hand(DOOM, stance_at(DOOM, DM['parry'], DF, DR, -1), 'n', (f1[0] + 0.1, f1[1] + 0.06))
    pb2 = plant_hand(DOOM, stance_at(DOOM, DM['parry'], DF, DR, -1, head=0), 'n', (f2[0] + 0.12, f2[1] + 0.1))
    grab = plant_hand(DOOM, stance_at(DOOM, DM['grab'], DF, DR, -1), 'n', (f3[0] + 0.06, f3[1]))
    d.key(57, dblock, lock='nf')
    d.key(59, pb1, lock='nf', ease='dec')
    d.key(62, dblock, lock='nf', ease='smooth')
    d.key(64, pb2, lock='nf', ease='dec')
    d.key(67, dblock, lock='nf', ease='smooth')
    d.key(70, grab, lock='nf', ease='dec', label='CATCHES the fist')
    for f_, pt in ((59, f1), (64, f2)):
        seq.impact(f_, pt[0] + 0.05, pt[1] + 0.04, dirx=-1, diry=0.4, power=0.6, stop=2, sound='clank', ring=False)
    seq.impact(50, fore[0], fore[1], dirx=-1, diry=0.3, power=1.0, stop=3, style='white', sound='clank_big')

    # ================================================================ 3C the shock
    G = (f3[0] + 0.04, f3[1] + 0.06)
    hold = plant_hand(DOOM, stance_at(DOOM, DM['hold'], DF, DR, -1), 'n', (G[0] + 0.02, G[1]))
    d.key(73, hold, lock='nf', ease='dec', label='the gauntlet discharges')
    d.key(98, P(hold, hold['x'], -1, dy=0.01), lock='nf', ease='smooth')
    gr = plant_hand(SPIDER, stance_at(SPIDER, SP['grabbed'], SF2, SR2, 1), 'n', G)
    s.key(73, gr, lock='nf', ease='dec')
    R = random.Random(7)
    for k, f in enumerate(range(75, 99, 2)):
        base = SP['shock_a'] if k % 2 == 0 else SP['shock_b']
        q = stance_at(SPIDER, base, SF2 + R.uniform(-0.02, 0.02), SR2, 1, dy=R.uniform(-0.02, 0.03))
        s.key(f, plant_hand(SPIDER, q, 'n', (G[0] + R.uniform(-0.015, 0.015), G[1] + R.uniform(-0.015, 0.015))),
              lock='nf', ease='hold' if k else 'dec', label='convulses' if k == 0 else None)
    seq.impact(75, G[0], G[1], dirx=-1, diry=0.2, power=1.4, stop=4, style=['dark', 'dark'], sound='zap_big',
               ring=False, sparks=False)
    shock_k = lambda a: 0.0 if a < 74 else (1.5 if a < 92 else max(0.0, 1.5 - (a - 92) * 0.12))
    seq.overlay(73, 104, pw.electrify('SPIDER', shock_k, seed=3, n=6), layer='front')
    seq.overlay(73, 104, pw.arc_between(lambda sc, a: pw.hand_tip(sc.actors['DOOM'].J, 'n', 0.0),
                                        lambda sc, a: sc.actors['SPIDER'].J.chest, shock_k, n=2, seed=5), layer='front')
    seq.overlay(73, 104, pw.electrify('DOOM', lambda a: 0.35 * shock_k(a), seed=9, n=2, aura=False), layer='front')

    def zaps(fx, sc, rf, a):
        J = sc.actors['SPIDER'].J
        if a % 3 == 0:
            pw.sparks(fx, J.chest[0], J.chest[1], -1, 0.5, n=4, speed=6, spread=1.4)
        fx.add(pw.Smoke(J.chest[0], J.chest[1], n=1, size=0.08, rise=0.8, seed=rf, col=(0.3, 0.3, 0.34), alpha=0.35))
    seq.emit(75, 99, zaps)

    # ================================================================ 3D the throw
    G2 = (G[0] + 0.3, G[1] + 0.32)
    G3 = (G[0] - 0.55, 2.15)
    twind = plant_hand(DOOM, stance_at(DOOM, DM['throw_wind'], DF, DR, -1), 'n', G2)
    tthrow = plant_hand(DOOM, stance_at(DOOM, DM['throw'], DF, DR, -1), 'n', G3)
    d.key(100, twind, lock='nf', ease='acc', label='hauls him up')
    d.key(104, tthrow, lock='nf', ease='dec', label='HURLS him')
    d.key(112, stance_at(DOOM, DM['throw'], DF, DR, -1, an=110, en=10), lock='nf', ease='smooth')
    d.key(124, stance_at(DOOM, DM['stand_wide'], DF, DR, -1), lock='nf', ease='smooth')
    d.smear(103, 105, ['an'], 0.8)
    up1 = P(SP['thrown'], 0, 1, an=170, en=10)
    up1 = plant_hand(SPIDER, dict(up1, x=G2[0] - 0.5, y=G2[1] - 0.95), 'n', G2)
    s.key(99, P(gr, gr['x'], 1), lock='nf')
    s.key(100, up1, ease='acc', label='hauled off his feet')
    rel = plant_hand(SPIDER, dict(P(SP['thrown'], 0, 1, an=150, rot=-30), x=G3[0] - 0.25, y=G3[1] - 0.7), 'n', G3)
    s.key(104, rel, ease='lin', label='released')
    landx = -1.0
    roll0 = P(SP['roll'], landx, 1)
    s.path(105, 118, arc(105, 118, (rel['x'] - 0.2, rel['y'] + 0.05), (roll0['x'], roll0['y']), height=0.9, hang=1.6,
                         xease=('dec', 1.4)))
    s.key(105, P(SP['thrown'], 0, 1, rot=-40), ease='lin', label='tumbles')
    s.key(109, P(SP['thrown'], 0, 1, rot=-150, an=120, ln=60, kn=90), ease='lin')
    s.key(113, P(SP['roll'], 0, 1, rot=-260), ease='lin')
    s.key(118, P(SP['roll'], landx, 1, rot=-360), ease='lin', label='hits the roof, rolls')
    s.key(122, P(SP['roll'], landx - 0.55, 1, rot=-540), ease='lin')
    s.key(125, P(SP['roll'], landx - 0.95, 1, rot=-670, dy=0.05), ease='dec')
    kneel = P(SP['kneel'], landx - 1.35, 1)
    s.key(131, kneel, ease='dec', xease=('dec', 2.0), lock='nf', label='skids to his knees')
    s.lag(105, 125, 'arms', 1)

    # ================================================================ 3E aftermath
    kshake = foot_on(SPIDER, P(SP['kneel_shake'], 0, 1), 'n', ankle(SPIDER, kneel, 'n')[0])
    s.key(140, kneel, lock='nf', ease='smooth')
    s.key(146, kshake, lock='nf', ease='smooth', label='shakes it off')
    for k, f in enumerate(range(148, 160, 2)):
        s.key(f, P(kshake, kshake['x'], 1, head=34 + (10 if k % 2 else -10), yaw=10 if k % 2 else -6), lock='nf',
              ease='smooth')
    s.key(166, P(kneel, kneel['x'], 1, head=-4), lock='nf', ease='smooth', label='looks up')
    s.key(N - 1, P(kneel, kneel['x'], 1, head=-8, dy=0.01), lock='nf', ease='smooth')
    dpoint = stance_at(DOOM, DM['point'], DF, DR, -1)
    d.key(140, stance_at(DOOM, DM['stand_wide'], DF, DR, -1), lock='nf', ease='smooth')
    d.key(152, dpoint, lock='nf', ease='dec', label='points: the verdict')
    d.key(172, P(dpoint, dpoint['x'], -1, dy=0.005), lock='nf', ease='smooth')
    dsw = stance_at(DOOM, DM['stand_wide'], DF, DR, -1)
    d.key(184, dsw, lock='nf', ease='smooth')
    d.key(N - 1, P(dsw, dsw['x'], -1, dy=0.004), lock='nf', ease='smooth')

    seq.add(d, z=0)
    seq.add(s, z=1)
    seq.fast = [('SPIDER', 99, 106)]          # hauled up and hurled: deliberate high-speed travel

    # ================================================================ camera
    c = seq.cam
    moon = dict(moon_r=0.5, moon_x=2.6, moon_dy=1.75)
    mid0 = (sg['x'] + D0['x']) / 2
    c.key(0, cx=mid0 + 0.4, cy=1.5, h=5.8, ease='smooth', **moon)
    c.key(30, cx=mid0 + 0.2, cy=1.3, h=5.4, ease='smooth', **moon)
    c.key(46, cx=(sl1['x'] + D0['x']) / 2, cy=1.2, h=4.2, ease='smooth', **moon)
    c.key(56, cx=(sfight['x'] + D0['x']) / 2 + 0.1, cy=1.2, h=3.4, ease='smooth', **moon)
    c.key(72, cx=(sfight['x'] + D0['x']) / 2 + 0.1, cy=1.3, h=3.1, ease='dec', **moon)
    c.key(98, cx=G[0], cy=1.35, h=2.7, ease='smooth', **moon)
    c.key(108, cx=1.4, cy=1.5, h=5.6, ease='smooth', **moon)
    c.key(131, cx=(kneel['x'] + D0['x']) / 2 + 0.3, cy=1.5, h=6.2, **moon)
    sh = head_of(SPIDER, kneel)
    c.key(140, cut=True, cx=sh[0] + 0.55, cy=sh[1] - 0.15, h=1.7, ease='smooth', moon_r=0.5, moon_x=-1.6,
          moon_dy=1.75)
    c.key(168, cx=sh[0] + 0.6, cy=sh[1] - 0.12, h=1.6, moon_r=0.5, moon_x=-1.6, moon_dy=1.75)
    c.key(169, cut=True, cx=(kneel['x'] + D0['x']) / 2 + 0.4, cy=1.45, h=5.9, ease='smooth', **moon)
    c.key(N - 1, cx=(kneel['x'] + D0['x']) / 2 + 0.4, cy=1.45, h=5.6, **moon)

    # ================================================================ fx
    def touch(x, n=6):
        return lambda fx, sc, rf: fx.dust(x, n=n, dirx=-1, speed=2.0, size=0.15, alpha=0.45, col=pw.GRIT)
    seq.at(31, touch(land2['x']))
    seq.emit(35, 43, lambda fx, sc, rf, a: fx.dust(sc.actors['SPIDER'].J.knee_f[0], n=1, dirx=-1, speed=1.8,
                                                   size=0.12, alpha=0.45, life=(10, 16), col=pw.GRIT))
    seq.at(56, touch(sfight['x']))
    seq.at(118, lambda fx, sc, rf: (fx.dust(landx, n=9, dirx=-1, speed=2.6, size=0.2, alpha=0.55, up=0.7,
                                            col=pw.GRIT), sc.shake.add(rf, 0.05, frames=7, dy=1.0, seed=118)))
    seq.emit(118, 131, lambda fx, sc, rf, a: fx.dust(sc.actors['SPIDER'].J.hip[0], n=1, dirx=-1, speed=1.6,
                                                     size=0.13, alpha=0.45, life=(10, 18), col=pw.GRIT))
    seq.at(131, lambda fx, sc, rf: fx.skidmark(kneel['x'] - 0.1, landx + 0.2, w=0.04))

    def wisps(fx, sc, rf, a):
        if a % 3 == 0:
            J = sc.actors['SPIDER'].J
            q = fx.rnd.choice((J.chest, J.head, J.hip, J.elbow_n))
            fx.add(pw.Smoke(q[0], q[1], n=1, size=0.06, rise=0.7, seed=rf, col=(0.36, 0.36, 0.4), alpha=0.35,
                            life=(20, 30)))
    seq.emit(100, 190, wisps)

    def doom_glow(a):
        if 73 <= a < 100:
            return 2.4
        return 1.3
    seq.glow['DOOM'] = doom_glow
    seq.glow['SPIDER'] = lambda a: (1.25 if 73 <= a < 100 else (0.55 if 146 <= a < 160 else
                                                                 (0.7 if a >= 166 else 0.9)))

    def motes(fx, sc, rf, a):
        if a % 4 == 0:
            fx.dust(fx.rnd.uniform(-8, 10), fx.rnd.uniform(0.1, 2.2), n=1, dirx=-1, speed=1.0, size=0.025,
                    life=(30, 50), up=0.05, alpha=0.3)
    seq.emit(0, N, motes)

    # ================================================================ sound
    seq.sfx(2, 'spider_sense', 0.9)
    for f_ in (4, 18, 30):
        seq.sfx(f_, 'charge_short', 0.6)
    for f_ in (10, 22, 34):
        seq.sfx(f_, 'bolt', 0.9)
    seq.sfx(13, 'whoosh', 0.7)
    seq.sfx(24, 'jump', 0.7)
    seq.sfx(27, 'blast', 0.9)
    seq.sfx(31, 'land', 0.6)
    seq.sfx(35, 'skid', 0.8)
    seq.sfx(47, 'whoosh_big', 0.8)
    seq.sfx(56, 'land', 0.6)
    seq.sfx(58, 'whoosh', 0.5)
    seq.sfx(63, 'whoosh', 0.5)
    seq.sfx(69, 'whoosh', 0.6)
    seq.sfx(70, 'grab', 1.0)
    seq.sfx(76, 'electric', 1.0)
    seq.sfx(100, 'whoosh_big', 0.9)
    seq.sfx(104, 'whoosh_big', 0.7)
    seq.sfx(118, 'thud', 1.0)
    seq.sfx(122, 'skid', 0.7)
    seq.sfx(152, 'doom_glint', 0.4)

    for f_, t_ in [(0, '3A barrage'), (10, 'bolt 1: lean back'), (22, 'bolt 2: hop'), (34, 'bolt 3: knee slide'),
                   (47, '3B flying kick'), (59, 'jab parried'), (64, 'cross parried'), (70, 'CAUGHT'),
                   (73, '3C the shock'), (100, '3D the throw'), (118, 'lands'), (140, '3E MCU'), (169, 'wide')]:
        seq.note(f_, t_)
    seq.state = dict(spider=s.eval(N - 1), doom=d.eval(N - 1),
                     scorches=prev['scorches'] + [tB[0]], splats=prev['splats'])
    seq.geometry = dict(boltA_y_at_spidey=head_y, slide_end=sl1['x'], kick_x=kickp['x'], fight_x=sfight['x'],
                        grip_x=G[0], grip_y=G[1], spidey_end=kneel['x'], doom_x=D0['x'],
                        puddle_left_edge=dv02.PUDDLE_X - dv02.puddle_half(since0 + 70),
                        spidey_front_foot=SF2, doom_front_foot=DF, gap_feet=DF - SF2)
    return seq


if __name__ == '__main__':
    for kk, v in build().geometry.items():
        print(f'{kk:22s} {v:7.2f}')
