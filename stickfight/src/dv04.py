"""DOOM vs SPIDER-MAN -- SEQUENCE 4: BACKFIRE (360 animation frames, 15 s)

  4A   0- 57  DOOM raises both gauntlets and draws in everything he has (green force, arcs
              leaping hand to hand, the cape thrown back). INSERT: his steel boots are standing
              in the pool from the tank, the green light shining on the water. CU SPIDER-MAN:
              the lenses narrow. He has seen it.
  4B  58- 85  DOOM levels both palms at him -- and two web balls plug them. He fires anyway.
              The energy has nowhere to go: it glows through the webbing, then crawls back
              up his arms.
  4C  86-139  BACKFIRE (white/dark impact frames, 6-frame hit-stop): the gauntlets blow, the
              discharge runs through the armour into the water and the whole pool lights up.
              DOOM convulses, then sags.
  4D 140-199  He goes down on one knee in the water, smoking, eye slits guttering.
  4E 200-269  He rises, glares, and leaves: the rocket boots cough, he wobbles into the air and
              blasts away across the moon. SPIDER-MAN waves him off.
  4F 270-359  A line to the water tower, a zip, a flip: SPIDER-MAN perched on the finial against
              the moon. Fade. Title.
"""
import math
import random

from heroes import SPIDER, DOOM, Head
from heroposes import LIB2
from engine import Track, arc, lerp
from scene import Sequence
from author import P, foot_on, ankle, hand, head_of, breathe, stance_at, mix
from rooftop import Rooftop, TOWER_X, TANK_Y1
from rig import solve
import powers as pw
import dv02
import dv03
from dv02 import HOLE, LEAK_F, add_water, aim, PUDDLE_X
from seq03 import moon_behind
from titles import title_card

SP, DM = LIB2['SPIDER'], LIB2['DOOM']
N = 360
FIN = (TOWER_X, TANK_Y1 + 1.0)          # top of the finial ball


def build():
    random.seed(404)
    st3 = dv03.build().state
    seq = Sequence('D4', N, wind=lambda a: -0.5 - (1.6 if 8 <= a < 86 else 0.0) * min(1.0, (a - 8) / 20.0)
                   - (2.6 if 86 <= a < 96 else 0.0))
    seq.stage = Rooftop(hole=(-10 ** 6, HOLE[0], HOLE[1]))
    since0 = 190 - LEAK_F + dv03.N
    BF = 86                               # the backfire

    def elec(a):
        if a < BF:
            return 0.0
        if a < 112:
            return 1.6
        return max(0.0, 1.6 - (a - 112) / 20.0)

    def reflect(a):
        return (st3['doom']['x'], 0.0 if a < 8 or a >= BF else min(1.0, (a - 8) / 20.0))
    add_water(seq, since0, N, elec_fn=elec, glow_fn=reflect)
    dv03.persistent(seq, dict(scorches=st3['scorches'], splats=st3['splats']), N)
    d = Track(DOOM)
    s = Track(SPIDER)
    S0, D0 = st3['spider'], st3['doom']
    DF, DR = ankle(DOOM, D0, 'n')[0], ankle(DOOM, D0, 'f')[0]
    KF = ankle(SPIDER, S0, 'n')[0]

    # ================================================================ 4A the big charge
    dup = stance_at(DOOM, DM['charge_up'], DF, DR, -1)
    d.key(0, D0, lock='nf')
    d.key(6, P(D0, D0['x'], -1, dy=-0.02, an=-10, af=-14), ease='acc', lock='nf')
    d.key(16, dup, ease='dec', lock='nf', label='both gauntlets up: the big charge')
    R = random.Random(4)
    for f in range(20, 57, 4):
        d.key(f, P(dup, dup['x'], -1, dy=R.uniform(-0.012, 0.012), lean=dup['lean'] + R.uniform(-1.5, 1.5),
                   an=dup['an'] + R.uniform(-3, 3), af=dup['af'] + R.uniform(-3, 3)), ease='smooth', lock='nf')

    def charge_k(a):
        if a < 10:
            return 0.0
        if a < 58:
            return 0.04 + 0.11 * (a - 10) / 48.0
        if a < 72:
            return 0.16
        return 0.0
    seq.overlay(8, 72, pw.charge('DOOM', 'n', charge_k, ahead=0.12))
    seq.overlay(8, 72, pw.charge('DOOM', 'f', charge_k, ahead=0.12))
    seq.overlay(18, 72, pw.arc_between(lambda sc, a: pw.hand_tip(sc.actors['DOOM'].J, 'n', 0.12),
                                       lambda sc, a: pw.hand_tip(sc.actors['DOOM'].J, 'f', 0.12),
                                       lambda a: 0.6 + 0.6 * min(1.0, (a - 18) / 30.0), col=pw.GREEN,
                                       hot=pw.GREEN_HOT, n=2, seed=11))

    # SPIDER-MAN gets up
    sg = stance_at(SPIDER, SP['guard'], KF, KF - 0.76, 1)
    s.key(0, S0, lock='nf')
    s.key(10, P(S0, S0['x'], 1, head=-14), ease='smooth', lock='nf')
    s.key(28, sg, ease='smooth', lock='nf', label='back on his feet')
    s.key(40, P(sg, sg['x'], 1, dy=0.01), ease='smooth', lock='nf')
    scu = P(sg, sg['x'], 1, yaw=26)
    s.key(44, scu, lock='nf')
    s.key(57, P(scu, scu['x'], 1, head=-4, dy=0.005), ease='smooth', lock='nf', label='the lenses narrow')

    # ================================================================ 4B plugged
    target = (sg['x'] + 0.1, head_of(SPIDER, sg)[1] - 0.35)
    dfwd = stance_at(DOOM, DM['charge_fwd'], DF, DR, -1)
    dfwd = aim(DOOM, aim(DOOM, dfwd, 'n', target), 'f', (target[0], target[1] - 0.12))
    d.key(58, dup, lock='nf')
    d.key(66, dfwd, ease='dec', lock='nf', label='levels both palms at him')
    d.key(71, P(dfwd, dfwd['x'], -1, dy=-0.01), ease='smooth', lock='nf')
    d.key(74, P(dfwd, dfwd['x'], -1, lean=dfwd['lean'] + 8, dy=-0.02), ease='dec', lock='nf',
          label='FIRES -- nothing comes out')
    for k, f in enumerate(range(76, BF, 2)):
        d.key(f, P(dfwd, dfwd['x'], -1, lean=dfwd['lean'] + 4 + (3 if k % 2 else -2), bend=-4 + (4 if k % 2 else 0),
                   an=dfwd['an'] + (6 if k % 2 else -4), af=dfwd['af'] + (-5 if k % 2 else 5),
                   head=-6 if k % 2 else 4), ease='lin', lock='nf', label='strains' if k == 0 else None)
    Jfwd = solve(DOOM, dfwd)
    palm_n = pw.hand_tip(Jfwd, 'n', 0.02)
    palm_f = pw.hand_tip(Jfwd, 'f', 0.02)
    tb = stance_at(SPIDER, SP['thwip_both'], KF, KF - 0.76, 1)
    s.key(58, sg, lock='nf')
    s.key(61, tb, ease='dec', lock='nf', label='thwip-thwip: one for each palm')
    s.key(70, P(tb, tb['x'], 1, dy=0.01), ease='smooth', lock='nf')
    s.key(76, sg, ease='smooth', lock='nf')
    s.smear(60, 62, ['an', 'af'], 0.5)
    Jtb = solve(SPIDER, tb)
    seq.overlay(62, 69, pw.webball(pw.hand_tip(Jtb, 'n', 0.06), palm_n, 62, 68, r=0.08))
    seq.overlay(62, 69, pw.webball(pw.hand_tip(Jtb, 'f', 0.06), palm_f, 62, 68, r=0.08))

    def trapped(a):
        return 0.0 if a < 74 else min(1.0, (a - 74) / 11.0)
    seq.overlay(68, BF + 1, pw.web_glob('DOOM', 'n', 68, BF + 1, r=0.13, seed=21, glow_fn=trapped), layer='front')
    seq.overlay(68, BF + 1, pw.web_glob('DOOM', 'f', 68, BF + 1, r=0.12, seed=22, glow_fn=trapped), layer='front')
    seq.overlay(74, 200, pw.electrify('DOOM', lambda a: (0.0 if a < 74 else 0.25 + 0.9 * (a - 74) / 12.0) if a < BF
                                      else (2.2 if a < 112 else max(0.0, 2.2 - (a - 112) / 18.0)
                                            + (0.25 if a < 200 and (a // 3) % 5 == 0 else 0.0)),
                                      seed=13, n=6, ground=True), layer='front')

    # ================================================================ 4C BACKFIRE
    dbf = stance_at(DOOM, DM['backfire'], DF, DR, -1)
    d.key(BF, P(dfwd, dfwd['x'], -1, lean=dfwd['lean'] + 6), ease='lin', lock='nf', label='BACKFIRE')
    d.key(BF + 2, dbf, ease='dec', lock='nf', label='blown back')
    for k, f in enumerate(range(BF + 4, 112, 2)):
        base = DM['convulse_a'] if k % 2 == 0 else DM['convulse_b']
        d.key(f, stance_at(DOOM, base, DF, DR, -1, dy=R.uniform(-0.03, 0.02)), ease='hold', lock='nf',
              label='electrocuted in the water' if k == 0 else None)
    dsl = stance_at(DOOM, DM['slump'], DF, DR, -1)
    d.key(112, dsl, ease='smooth', lock='nf', label='sags')
    d.key(126, P(dsl, dsl['x'], -1, dy=-0.04, head=36), ease='acc', lock='nf')
    dkn = foot_on(DOOM, P(DM['kneel'], 0, -1), 'n', DF)
    d.key(138, dkn, ease='dec', lock='n', hands='n', label='down on one knee, in the water')
    d.key(150, P(dkn, dkn['x'], -1, dy=-0.01, head=24), ease='smooth', lock='n', hands='n')
    d.key(199, P(dkn, dkn['x'], -1, head=26), ease='smooth', lock='n', hands='n')
    s.key(80, sg, lock='nf')
    scov = stance_at(SPIDER, SP['cover'], KF, KF - 0.76, 1)
    s.key(84, scov, ease='dec', lock='nf', label='shields his lenses')
    s.key(104, P(scov, scov['x'], 1, dy=0.01), ease='smooth', lock='nf')
    sneu = stance_at(SPIDER, SP['neutral'], KF - 0.1, KF - 0.36, 1)
    s.key(118, sg, ease='smooth', lock='nf')
    s.key(140, sneu, ease='smooth', lock='nf', label='lowers his guard')
    s.key(160, P(sneu, sneu['x'], 1, head=8, yaw=8), ease='smooth', lock='nf')
    s.key(176, P(sneu, sneu['x'], 1, head=2), ease='smooth', lock='nf')
    Jbf = solve(DOOM, dfwd)
    h1, h2 = pw.hand_tip(Jbf, 'n', 0.02), pw.hand_tip(Jbf, 'f', 0.02)
    bx, by = (h1[0] + h2[0]) / 2, (h1[1] + h2[1]) / 2
    seq.impact(BF, bx, by, dirx=1, diry=0.3, power=2.0, stop=6, style=['white', 'dark', 'white'], sound='backfire',
               ring=True, sparks=False)

    def blow(fx, sc, rf):
        pw.explosion(fx, h1[0], h1[1], power=1.6, seed=86)
        pw.explosion(fx, h2[0], h2[1], power=1.3, seed=87)
        fx.ring(DF, 0.02, 0.1, 3.4, life=14, w=0.07, squash=0.16, col=pw.ELEC)
        pw.sparks(fx, bx, by, 0, 1, n=30, speed=9, spread=1.8)
        for _ in range(8):
            q = (fx.rnd.uniform(-0.12, 0.12), fx.rnd.uniform(0.0, 0.2))
            fx.ps.append(pw.Particle('spark', bx + q[0], by + q[1], fx.rnd.uniform(-4, 4), fx.rnd.uniform(1, 5),
                                     life=fx.rnd.randint(8, 14), col=pw.WEB, g=1.0, drag=0.95, w=0.03))
        fx.flash_screen(0.6, (0.85, 1.0, 0.9))
        sc.shake.add(rf, 0.16, frames=16, dx=0.5, dy=1.0, seed=BF)
    seq.at(BF, blow)

    def steam(fx, sc, rf, a):
        x = PUDDLE_X + fx.rnd.uniform(-1.2, 1.2)
        fx.add(pw.Smoke(x, 0.05, n=1, size=0.16, rise=1.1, seed=rf, col=(0.62, 0.66, 0.74), alpha=0.35,
                        life=(20, 36)))
        if a < 112 and a % 2 == 0:
            pw.splash(fx, PUDDLE_X + fx.rnd.uniform(-1.0, 1.0), n=3, speed=2.4, up=3.0, col=(0.75, 0.88, 1.0))
    seq.emit(BF, 150, steam)

    def armour_smoke(fx, sc, rf, a):
        J = sc.actors['DOOM'].J
        if a % 2 == 0:
            q = fx.rnd.choice((J.chest, J.hand_n, J.hand_f, J.shoulder, J.head, J.elbow_n))
            fx.add(pw.Smoke(q[0], q[1], n=1, size=0.08, rise=0.9, seed=rf, col=(0.25, 0.25, 0.28), alpha=0.45,
                            life=(24, 40)))
        if a % 7 == 0:
            q = fx.rnd.choice((J.hand_n, J.hand_f, J.elbow_n, J.chest))
            pw.sparks(fx, q[0], q[1], fx.rnd.uniform(-1, 1), 1, n=4, speed=4, spread=1.2)
    seq.emit(BF, 260, armour_smoke)

    # ================================================================ 4E rise and retreat
    dkl = foot_on(DOOM, P(DM['kneel_look'], 0, -1), 'n', DF)
    d.key(206, dkl, ease='smooth', lock='n', hands='n', label='looks up at him')
    drise = stance_at(DOOM, DM['rise'], DF, DR, -1)
    d.key(216, drise, ease='smooth', lock='nf', label='rises')
    dstand = stance_at(DOOM, DM['stand'], DF, DR, -1)
    d.key(224, dstand, ease='smooth', lock='nf', label='glares')
    dto = stance_at(DOOM, DM['takeoff'], DF, DR, -1)
    d.key(230, dstand, ease='smooth', lock='nf')
    d.key(234, dto, ease='acc', lock='nf', label='the boots cough')
    fly0 = P(DM['fly'], D0['x'], -1, lean=4)
    fly0['y'] = 1.15
    d.key(237, fly0, ease='dec', label='lifts off, unsteady')

    def wob(f):
        u = (f - 237) / 15.0
        return dict(x=D0['x'] + 0.18 * math.sin(f * 0.9), y=1.15 + 1.1 * (u ** 0.8) + 0.06 * math.sin(f * 1.3),
                    lean=6 * math.sin(f * 0.8))
    d.path(238, 252, wob)
    d.key(244, P(DM['fly'], 0, -1, an=30, af=-40), ease='smooth')
    d.key(252, P(DM['fly'], 0, 1, lean=-6, yaw=20), ease='smooth')
    end0 = wob(252)

    def away(f):
        u = (f - 252) / 16.0
        return dict(x=end0['x'] + 4.5 * u ** 1.6, y=end0['y'] + 9.5 * u ** 2.0)
    d.path(253, N - 1, away)
    d.key(268, P(DM['fly'], 0, 1, lean=-20, yaw=20, an=-30, af=-40), ease='smooth', label='blasts away')
    sputter = lambda a: 0.7 if a < 246 else (0.35 if a < 254 else 0.1)
    jet_k = lambda a: 0.0 if a < 233 else (0.7 if a < 237 else (1.0 if a < 253 else 1.5))
    seq.overlay(233, 270, pw.jets('DOOM', jet_k, sputter=sputter), layer='back')

    def exhaust(fx, sc, rf, a):
        J = sc.actors['DOOM'].J
        for an in (J.ankle_n, J.ankle_f):
            fx.add(pw.Smoke(an[0], an[1] - 0.3, n=1, size=0.1, rise=-0.3, life=(16, 26), seed=rf + int(an[0] * 7),
                            col=(0.3, 0.3, 0.33), alpha=0.45))
    seq.emit(234, 270, exhaust)

    # SPIDER-MAN waves him off
    swv = stance_at(SPIDER, SP['wave'], KF - 0.1, KF - 0.36, 1)
    s.key(214, sneu, lock='nf')
    s.key(226, P(sneu, sneu['x'], 1, head=-10), ease='smooth', lock='nf')
    s.key(246, swv, ease='smooth', lock='nf', label='waves him off')
    for k, f in enumerate(range(249, 264, 3)):
        s.key(f, P(swv, swv['x'], 1, an=swv['an'] + (14 if k % 2 else -6), en=swv['en'] + (10 if k % 2 else 0),
                   head=-18), ease='smooth', lock='nf')
    s.key(266, P(sneu, sneu['x'], 1, head=-20), ease='smooth', lock='nf')

    # ================================================================ 4F the zip and the perch
    tup = stance_at(SPIDER, SP['thwip_up'], KF - 0.1, KF - 0.36, 1)
    tup = aim(SPIDER, tup, 'n', FIN)
    s.key(272, sneu, lock='nf')
    s.key(276, tup, ease='dec', lock='nf', label='a line to the tower')
    Jup = solve(SPIDER, tup)
    zhand0 = pw.hand_tip(Jup, 'n', 0.0)
    zip0 = P(SP['zip'], tup['x'] + 0.2, 1)
    zip0['y'] = tup['y'] + 0.3
    perch = P(SP['perch'], FIN[0], 1, dy=FIN[1] + 0.02, yaw=18)
    zip1 = (FIN[0] - 1.25, FIN[1] - 1.1)

    def zipping(f):
        u = (f - 279) / 15.0
        e = u * u * (3 - 2 * u) * 0.35 + 0.65 * u ** 1.4
        x = lerp(zip0['x'], zip1[0], e)
        y = lerp(zip0['y'], zip1[1], e) + 0.4 * math.sin(math.pi * u)
        ang = math.degrees(math.atan2(FIN[0] - x, FIN[1] - y))
        return dict(x=x, y=y, rot=ang * 0.8)
    s.key(279, P(zip0, zip0['x'], 1) | dict(y=zip0['y']), ease='lin', label='ZIP')
    s.path(279, 294, zipping)
    s.key(286, P(SP['zip'], 0, 1, ln=-20, lf=-40, kf=60), ease='smooth')
    s.key(294, P(SP['zip'], 0, 1, ln=20, kn=60, lf=0, kf=70), ease='dec')
    s.path(295, 304, arc(295, 304, zip1, (perch['x'], perch['y']), height=0.9, hang=1.8))
    s.key(295, P(SP['tuck'], 0, 1, rot=40), ease='lin', label='flips over the top')
    s.key(299, P(SP['tuck'], 0, 1, rot=200), ease='lin')
    s.key(302, P(SP['open_out'], 0, 1, rot=320), ease='dec')
    s.key(304, P(perch, perch['x'], 1, rot=360) | dict(y=perch['y']), ease='dec', label='PERCHED')
    s.key(316, P(perch, perch['x'], 1) | dict(y=perch['y'] + 0.01, head=-30), ease='smooth')
    s.key(N - 1, P(perch, perch['x'], 1) | dict(y=perch['y'], head=-26), ease='smooth')
    seq.overlay(276, 295, pw.webline(lambda sc, a: pw.hand_tip(sc.actors['SPIDER'].J, 'n', 0.0), FIN, 276, 295,
                                     shoot=3))

    seq.add(d, z=0)
    seq.add(s, z=1)
    seq.actors['DOOM'].visible = [(-10 ** 9, 270)]
    seq.fast = [('DOOM', 252, 270), ('SPIDER', 279, 296)]   # rocket exit, web-zip

    # ================================================================ camera
    c = seq.cam
    moon = dict(moon_r=0.5, moon_x=2.6, moon_dy=1.75)
    mid = (sg['x'] + D0['x']) / 2
    c.key(0, cx=(S0['x'] + D0['x']) / 2 + 0.4, cy=1.45, h=5.6, ease='smooth', **moon)
    c.key(12, cx=mid, cy=1.5, h=6.9, ease='smooth', **moon)
    c.key(19, cx=D0['x'] - 0.3, cy=1.6, h=4.4, ease='smooth', **moon)
    c.key(20, cut=True, cx=DF + 0.15, cy=0.32, h=1.05, ease='lin', moon_r=0.5, moon_x=2.6, moon_dy=1.75)
    c.key(33, cx=DF + 0.22, cy=0.34, h=1.0, moon_r=0.5, moon_x=2.6, moon_dy=1.75)
    c.key(34, cut=True, cx=D0['x'] - 0.1, cy=1.75, h=3.3, ease='smooth', moon_r=0.45, moon_x=1.0, moon_dy=1.9)
    c.key(43, cx=D0['x'] - 0.15, cy=1.8, h=3.1, moon_r=0.45, moon_x=1.0, moon_dy=1.9)
    sh = head_of(SPIDER, scu)
    c.key(44, cut=True, cx=sh[0] + 0.25, cy=sh[1] - 0.04, h=1.0, ease='lin', moon_r=0.5, moon_x=-2.4, moon_dy=1.7)
    c.key(57, cx=sh[0] + 0.24, cy=sh[1] - 0.03, h=0.88, moon_r=0.5, moon_x=-2.4, moon_dy=1.7)
    c.key(58, cut=True, cx=mid + 0.2, cy=1.45, h=6.4, ease='smooth', **moon)
    c.key(70, cx=mid + 0.4, cy=1.45, h=6.2, ease='acc', **moon)
    c.key(BF, cx=D0['x'] - 0.6, cy=1.45, h=4.4, ease='dec', **moon)
    c.key(112, cx=D0['x'] - 0.9, cy=1.5, h=5.2, ease='smooth', **moon)
    c.key(139, cx=mid + 0.6, cy=1.5, h=6.0, **moon)
    dh = head_of(DOOM, dkn)
    c.key(140, cut=True, cx=dh[0] - 0.45, cy=dh[1] - 0.18, h=1.9, ease='smooth', moon_r=0.5, moon_x=0.8,
          moon_dy=1.8)
    c.key(176, cx=dh[0] - 0.5, cy=dh[1] - 0.12, h=1.75, moon_r=0.5, moon_x=0.8, moon_dy=1.8)
    c.key(177, cut=True, cx=mid + 0.6, cy=1.5, h=6.0, ease='smooth', **moon)
    c.key(232, cx=mid + 0.8, cy=1.6, h=6.0, ease='smooth', **moon)
    c.key(252, cx=mid + 1.2, cy=2.5, h=6.6, ease='smooth', **moon)
    c.key(271, cx=mid + 1.6, cy=3.0, h=7.4, ease='smooth', **moon)
    c.key(304, cx=(sneu['x'] + FIN[0]) / 2 + 0.6, cy=3.0, h=8.6, ease='smooth', **moon)
    end_cam = dict(cx=FIN[0] - 0.35, cy=FIN[1] - 0.05, h=3.1)
    mx, mdy = moon_behind(end_cam, (FIN[0] + 0.05, FIN[1] + 0.45))
    c.key(305, cut=True, ease='smooth', moon_r=0.95, moon_x=mx, moon_dy=mdy, **end_cam)
    end2 = dict(cx=FIN[0] - 0.35, cy=FIN[1] + 0.05, h=3.5)
    mx2, mdy2 = moon_behind(end2, (FIN[0] + 0.05, FIN[1] + 0.45))
    c.key(N - 1, moon_r=0.95, moon_x=mx2, moon_dy=mdy2, **end2)

    # ================================================================ fx / looks
    def doom_glow(a):
        if a < 8:
            return 1.3
        if a < BF:
            return 1.3 + 1.4 * min(1.0, (a - 8) / 30.0)
        if a < 140:
            return 2.6 if (a // 2) % 3 else 0.2
        if a < 204:
            return 0.25 + (0.5 if (a // 3) % 7 == 0 else 0.0)
        return min(2.0, 0.25 + 1.75 * (a - 204) / 12.0)
    seq.glow['DOOM'] = doom_glow

    def lens(a):
        if 44 <= a < 58:
            return 1.0 - 0.45 * max(0.0, min(1.0, (a - 46) / 8.0))
        if 84 <= a < 104:
            return 0.5
        if 140 <= a < 180:
            return 1.05
        if 246 <= a < 266:
            return 0.8
        return 0.85
    seq.glow['SPIDER'] = lens

    def doom_flare(fx, sc, rf):
        H = Head(sc.actors['DOOM'].J, 36)
        for sx_ in (-1, 1):
            q = H.decal(sx_ * 0.27, 0.17)[0]
            fx.glint(q[0], q[1], size=0.12, life=9, col=(0.75, 1.0, 0.8))
    seq.at(216, doom_flare)
    seq.at(138, lambda fx, sc, rf: pw.splash(fx, ankle(DOOM, dkn, 'f')[0], n=10, speed=2.4, up=3.0))

    def ripples(fx, sc, rf, a):
        if a % 5 == 0:
            for x in (DF, DR):
                fx.ring(x, 0.0, 0.05, 0.45, life=14, w=0.012, squash=0.16, col=(0.75, 0.85, 1.0), alpha=0.5)
        if a % 3 == 0:
            fx.ps.append(pw.Particle('spark', DF + fx.rnd.uniform(-0.3, 0.5), 0.5 + fx.rnd.uniform(0, 0.4),
                                     fx.rnd.uniform(-0.3, 0.3), -2.0, life=8, col=(0.8, 0.9, 1.0), g=1.0, drag=1.0,
                                     w=0.008))
    seq.emit(16, 34, ripples)
    seq.at(237, lambda fx, sc, rf: (pw.splash(fx, D0['x'], n=14, speed=3.0, up=3.0),
                                    fx.ring(D0['x'], 0.02, 0.1, 1.6, life=10, w=0.04, squash=0.16, col=pw.WATER)))

    def motes(fx, sc, rf, a):
        if a % 4 == 0:
            fx.dust(fx.rnd.uniform(-8, 10), fx.rnd.uniform(0.1, 2.2), n=1, dirx=-1, speed=1.0, size=0.025,
                    life=(30, 50), up=0.05, alpha=0.3)
    seq.emit(0, N, motes)
    seq.fade(328, 340, 0.0, 1.0)
    seq.fade(340, N, 1.0, 1.0)
    seq.cards.append((338, N, title_card('DOOM  vs  SPIDER-MAN', 'a stick-fight animation')))

    # ================================================================ sound
    seq.sfx(8, 'charge_big', 1.0)
    seq.sfx(20, 'water_drip', 0.8)
    seq.sfx(46, 'glint', 0.5)
    seq.sfx(61, 'thwip', 1.0)
    seq.sfx(62, 'thwip', 0.9)
    seq.sfx(68, 'web_splat', 1.0)
    seq.sfx(74, 'strain', 1.0)
    seq.sfx(BF + 1, 'electric_long', 1.0)
    seq.sfx(BF + 2, 'steam', 1.0)
    seq.sfx(138, 'splash', 0.8)
    seq.sfx(216, 'doom_glint', 0.8)
    seq.sfx(234, 'jet_sputter', 1.0)
    seq.sfx(253, 'jet_long', 0.8)
    seq.sfx(276, 'thwip', 1.0)
    seq.sfx(279, 'whoosh_big', 0.8)
    seq.sfx(295, 'whoosh', 0.6)
    seq.sfx(304, 'land', 0.5)

    for f_, t_ in [(0, '4A the big charge'), (20, 'INSERT boots in the water'), (34, 'DOOM charging'),
                   (44, 'CU SPIDER-MAN: lenses narrow'), (58, '4B plugged'), (74, 'fires: nothing'),
                   (BF, '4C BACKFIRE'), (112, 'sags'), (140, '4D CU DOOM kneeling'), (177, 'wide'),
                   (206, '4E rises'), (234, 'retreat'), (272, '4F zip'), (305, 'perched'), (338, 'title')]:
        seq.note(f_, t_)
    seq.geometry = dict(doom_x=D0['x'], doom_front_foot=DF, puddle_x=PUDDLE_X,
                        puddle_half=dv02.puddle_half(since0 + BF), spidey_x=sg['x'], palm_n_x=palm_n[0],
                        palm_n_y=palm_n[1], perch_y=perch['y'])
    return seq


if __name__ == '__main__':
    for kk, v in build().geometry.items():
        print(f'{kk:22s} {v:7.2f}')
