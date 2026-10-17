"""DOOM vs SPIDER-MAN -- SEQUENCE 2: FIRST EXCHANGE (190 animation frames, ~8 s)

  2A   0- 36  DOOM draws his palm back and fires a bolt of force at the crouching SPIDER-MAN.
              Spider-sense: he is already in the air. The roof where he crouched explodes under
              him; he front-flips over the blast and lands a metre closer.
  2B  37- 66  Two web balls -> DOOM throws up his force field: both splat on the lattice and
              slide. He drops the field to charge a bigger bolt overhead...
  2C  67-100  ...and that is the opening: two web lines onto his chest, a yank, and SPIDER-MAN
              arrives feet first. DOUBLE-FOOT DROPKICK (impact frames, 5-frame hit-stop). The
              charged bolt goes off wild, up and behind DOOM -- into the water tower. DOOM skids
              back 2.4 m, boots throwing sparks; SPIDER-MAN back-flips off his chest.
  2D 101-189  Water gushes from the holed tank and pools around DOOM's feet (set-up for the
              finale). DOOM straightens, looks down at the webbing on his chest, tears it off and
              flings it away. Eyes flare.
"""
import math
import random

from heroes import SPIDER, DOOM
from heroposes import LIB2
from engine import Track, arc
from scene import Sequence
from author import P, foot_on, ankle, hand, head_of, breathe, bounce, stance_at, mix
from rooftop import Rooftop, TOWER_X, TANK_R
from rig import solve, vec_angle_from_down
import powers as pw

SP, DM = LIB2['SPIDER'], LIB2['DOOM']
HOLE = (TOWER_X - TANK_R + 0.02, 3.35)
LEAK_F = 87                                  # the bolt holes the tank on this frame
LEAK_V0 = 2.2                                # horizontal speed of the gush (m/s)


def aim(build, p, side, target, bend=0.0):
    """Point a (straight) arm from its shoulder at a world target."""
    J = solve(build, p)
    sh = J.shoulder_n if side == 'n' else J.shoulder_f
    q = dict(p)
    q['a' + side] = vec_angle_from_down((target[0] - sh[0], target[1] - sh[1]), J.face) - bend * 0.5
    q['e' + side] = bend
    return q


def leak_land_x():
    """Where the gush from the holed tank hits the roof."""
    return HOLE[0] - LEAK_V0 * math.sqrt(2 * HOLE[1] / 9.8)


PUDDLE_X = leak_land_x() - 0.2              # centre of the pool (sequences 2-4)


def puddle_half(a_since_leak):
    """Half-width of the pool, from frames since the leak (it keeps spreading through sequence 4)."""
    k = max(0.0, min(1.0, (a_since_leak - 8) / 90.0))
    return 1.25 * k ** 0.8 + 0.55 * max(0.0, min(1.0, (a_since_leak - 100) / 260.0))


def add_water(seq, since0, n, elec_fn=None, glow_fn=None):
    """The running leak for a later sequence: since0 = frames since the leak at a = 0."""
    stream_fn, land_x = pw.stream(HOLE, -since0, v0=LEAK_V0)
    seq.overlay(0, n, stream_fn, layer='back')
    seq.overlay(0, n, pw.puddle(lambda a: PUDDLE_X, lambda a: puddle_half(a + since0), elec_fn, glow_fn),
                layer='back')
    seq.emit(0, n, lambda fx, sc, rf, a: pw.splash(fx, land_x, n=2, speed=2.0, up=2.6))


def build():
    random.seed(202)
    seq = Sequence('D2', 190, wind=-0.5)
    seq.stage = Rooftop(hole=(LEAK_F, HOLE[0], HOLE[1]))
    d = Track(DOOM)
    s = Track(SPIDER)

    DS = 1.70
    SXg = -3.02
    sg = foot_on(SPIDER, P(SP['guard'], 0, 1), 'n', ankle(SPIDER, P(SP['guard'], SXg, 1), 'n')[0])
    dst = P(DM['stand'], DS, -1)

    # ================================================================ 2A bolt 1
    crouch_x = sg['x']
    s.key(0, sg, lock='nf')
    s.key(8, P(sg, sg['x'], 1, dy=0.015), ease='smooth', lock='nf')
    santic = foot_on(SPIDER, P(SP['crouch_low'], 0, 1), 'n', ankle(SPIDER, sg, 'n')[0])
    s.key(14, P(sg, sg['x'], 1, head=-24), ease='smooth', lock='nf', label='spider-sense')
    s.key(17, santic, ease='acc', lock='nf', hands='n', label='drops for the jump')
    leap = P(SP['leap'], sg['x'] + 0.15, 1)
    leap['y'] = 1.1
    s.key(19, leap, ease='dec', label='LEAPS')
    s.smear(18, 20, ['ln', 'lf'], 0.6)
    land1 = P(SP['land'], sg['x'] + 1.15, 1)
    s.path(19, 33, arc(19, 33, (leap['x'], leap['y']), (land1['x'], land1['y']), height=1.55, hang=2.0))
    s.key(22, P(SP['tuck'], 0, 1, rot=60), ease='lin', label='front flip over the blast')
    s.key(25, P(SP['tuck'], 0, 1, rot=160), ease='lin')
    s.key(28, P(SP['tuck'], 0, 1, rot=260), ease='lin')
    s.key(31, P(SP['open_out'], 0, 1, rot=340, an=60, af=-80), ease='dec')
    s.key(33, land1, ease='dec', lock='nf', label='lands, closer')
    s.lag(19, 32, 'arms', 1)

    d.key(0, dst, lock='nf')
    d.key(6, P(dst, DS, -1, dy=0.005), ease='smooth', lock='nf')
    dant = foot_on(DOOM, P(DM['cast_antic'], 0, -1), 'f', ankle(DOOM, dst, 'f')[0])
    d.key(13, dant, ease='acc', lock='nf', label='draws the palm back: charge')
    target1 = (crouch_x + 0.05, 0.12)
    dcast = foot_on(DOOM, P(DM['cast'], 0, -1), 'f', ankle(DOOM, dst, 'f')[0])
    dcast = aim(DOOM, dcast, 'n', target1)
    d.key(20, mix(dant, dcast, 0.55), ease='lin')
    d.key(21, dcast, ease='dec', lock='nf', label='FIRES')
    d.smear(20, 22, ['an'])
    d.key(26, P(dcast, dcast['x'], -1, an=dcast['an'] + 22, en=14, lean=-2), ease='smooth', lock='nf',
          label='recoil')
    d.key(34, P(DM['stand'], dcast['x'], -1, an=30, en=30), ease='smooth', lock='nf')
    Jc = solve(DOOM, dcast)
    p0 = pw.hand_tip(Jc, 'n', 0.12)
    seq.overlay(13, 22, pw.charge('DOOM', 'n', lambda a: 0.075 * min(1.0, (a - 12) / 7.0) if a < 21 else 0.0))
    seq.overlay(21, 26, pw.bolt(p0, target1, 21, 25))

    def blast1(fx, sc, rf):
        pw.explosion(fx, target1[0], 0.18, power=1.2, seed=25)
        fx.debris(target1[0], n=14, speed=3.0, up=5.0)
        fx.dust(target1[0], n=8, dirx=-1, speed=3.0, size=0.22, alpha=0.5, up=0.8, col=pw.GRIT)
        fx.dust(target1[0], n=8, dirx=1, speed=3.0, size=0.22, alpha=0.5, up=0.8, col=pw.GRIT)
        fx.crack(target1[0], n=7, length=1.1)
        sc.shake.add(rf, 0.08, frames=9, dx=0.2, dy=1.0, seed=25)
        fx.flash_screen(0.22, (0.6, 1.0, 0.65))
    seq.at(25, blast1)
    seq.hitstop(25, 2)
    seq.overlay(25, 190, pw.scorch(target1[0], 25, w=0.85, seed=3), layer='back')
    seq.overlay(8, 26, pw.spider_sense('SPIDER', lambda a: max(0.0, min(1.0, (a - 8) / 5.0, (26 - a) / 5.0))),
                layer='top')

    # ================================================================ 2B web balls -> force field
    sx2 = land1['x']
    sF, sR = ankle(SPIDER, land1, 'n')[0], ankle(SPIDER, land1, 'f')[0]
    s.key(36, stance_at(SPIDER, SP['guard'], sF, sR, 1), ease='smooth', lock='nf')
    t1 = stance_at(SPIDER, SP['thwip_n'], sF, sR, 1)
    t2 = stance_at(SPIDER, SP['thwip_f'], sF, sR, 1)
    s.key(39, t1, ease='dec', lock='nf', label='web ball (near hand)')
    s.key(42, t2, ease='dec', lock='nf', label='web ball (far hand)')
    s.smear(38, 40, ['an'], 0.5)
    s.smear(41, 43, ['af'], 0.5)
    sgb = stance_at(SPIDER, SP['guard_b'], sF, sR, 1)
    sga = stance_at(SPIDER, SP['guard'], sF, sR, 1)
    s.key(46, sga, ease='smooth', lock='nf')
    bounce(s, 48, 62, sga, sgb, period=8)

    dsh = foot_on(DOOM, P(DM['shield'], 0, -1), 'f', ankle(DOOM, dst, 'f')[0])
    d.key(37, P(DM['stand'], dcast['x'], -1, an=30, en=30), lock='nf')
    d.key(41, dsh, ease='dec', lock='nf', label='FORCE FIELD')
    d.key(46, P(dsh, dsh['x'], -1, lean=-9, head=10), ease='smooth', lock='nf')
    d.key(50, dsh, ease='smooth', lock='nf')
    d.key(57, dsh, ease='smooth', lock='nf')
    Jsh = solve(DOOM, dsh)
    ccx, ccy = Jsh.hip[0], Jsh.hip[1] + 0.25
    hit1 = (ccx - 1.2 * 0.98, ccy + 0.25)
    hit2 = (ccx - 1.2 * 0.99, ccy - 0.1)
    Jt1, Jt2 = solve(SPIDER, t1), solve(SPIDER, t2)
    seq.overlay(39, 45, pw.webball(pw.hand_tip(Jt1, 'n', 0.06), hit1, 40, 44))
    seq.overlay(42, 48, pw.webball(pw.hand_tip(Jt2, 'f', 0.06), hit2, 43, 47))
    shield_k = lambda a: (min(1.0, (a - 38) / 4.0) if a < 58 else max(0.0, 1 - (a - 58) / 4.0))
    seq.overlay(38, 63, pw.shield('DOOM', shield_k, hits=[(44, *hit1), (47, *hit2)]), layer='front')
    seq.overlay(44, 59, pw.splat_at(hit1, 44, 59, r=0.11, seed=4, slide=0.3), layer='top')
    seq.overlay(47, 59, pw.splat_at(hit2, 47, 59, r=0.11, seed=5, slide=0.25), layer='top')
    seq.at(44, lambda fx, sc, rf: fx.ring(hit1[0], hit1[1], 0.05, 0.5, life=6, w=0.03, col=pw.GREEN_HOT))
    seq.at(47, lambda fx, sc, rf: fx.ring(hit2[0], hit2[1], 0.05, 0.5, life=6, w=0.03, col=pw.GREEN_HOT))
    # the field drops: the splats fall to the roof
    falls = []
    for hp, sd, sl in ((hit1, 4, 0.3), (hit2, 5, 0.25)):
        def fall(a, hp=hp, sl=sl):
            t = (a - 59) / 24.0
            t = min(t, math.sqrt(max(0.0, hp[1] - sl - 0.03) / 4.9))      # it stops where it lands
            return (hp[0] - 0.6 * t, max(0.03, hp[1] - sl - 4.9 * t * t))
        falls.append(fall)
        seq.overlay(59, 190, pw.splat_at(lambda sc, a, fall=fall: fall(a), 59, 190, r=0.1, seed=sd), layer='back')

    # ================================================================ 2B/2C DOOM charges overhead
    target_tank = (HOLE[0], HOLE[1])
    dhigh = foot_on(DOOM, P(DM['cast_high'], 0, -1), 'f', ankle(DOOM, dst, 'f')[0])
    d.key(60, P(DM['stand'], dsh['x'], -1, an=40, en=40), ease='smooth', lock='nf', label='drops the field')
    d.key(66, dhigh, ease='dec', lock='nf', label='charges a bigger bolt overhead')
    d.key(80, P(dhigh, dhigh['x'], -1, an=dhigh['an'] + 6, lean=-6, dy=0.01), ease='smooth', lock='nf')
    charge_k = lambda a: 0.0 if a < 64 else (0.16 * min(1.0, (a - 64) / 14.0) if a < 84 else 0.0)
    seq.overlay(64, 84, pw.charge('DOOM', 'n', charge_k, ahead=0.12))

    # ================================================================ 2C web-yank dropkick
    tb = stance_at(SPIDER, SP['thwip_both'], sF, sR, 1)
    s.key(64, sga, lock='nf', ease='smooth')
    s.key(68, tb, ease='dec', lock='nf', label='two lines onto his chest')
    yank = stance_at(SPIDER, SP['yank'], sF, sR, 1)
    s.key(72, yank, ease='acc', lock='nf', label='YANK')
    # contact geometry: both soles on DOOM's chest plate
    Jh = solve(DOOM, P(dhigh, dhigh['x'], -1, an=dhigh['an'] + 6, lean=-6, dy=0.01))
    chest_pt = (Jh.chest[0] + 0.03, Jh.chest[1] - 0.12)
    kext = P(SP['dropkick_ext'], 0, 1)
    Jk = solve(SPIDER, kext)
    toe = ((Jk.toe_n[0] + Jk.toe_f[0]) / 2 - kext['x'], (Jk.toe_n[1] + Jk.toe_f[1]) / 2 - kext['y'])
    kick = P(SP['dropkick_ext'], chest_pt[0] - toe[0], 1)
    kick['y'] = chest_pt[1] - toe[1]
    fly = P(SP['dropkick'], (yank['x'] + kick['x']) / 2 - 0.3, 1)
    fly['y'] = (yank['y'] + kick['y']) / 2 + 0.12
    s.key(75, P(SP['chamber'], yank['x'] + 0.35, 1, dy=0.0) | dict(y=yank['y'] + 0.25), ease='lin',
          label='yanked off his feet')
    s.key(78, fly, ease='lin', label='feet first')
    s.key(81, P(SP['dropkick_ext'], kick['x'] - 0.32, 1) | dict(y=kick['y'] + 0.03), ease='lin')
    s.key(82, kick, ease='dec', label='DROPKICK CONTACT')
    s.smear(80, 83, ['ln', 'lf'], 0.9)
    s.lag(72, 82, 'head', 1)
    web_tgt = [(lambda sc, a, o=o: (sc.actors['DOOM'].J.chest[0] + 0.02, sc.actors['DOOM'].J.chest[1] - 0.08 + o))
               for o in (0.05, -0.12)]
    seq.overlay(68, 83, pw.webline(lambda sc, a: pw.hand_tip(sc.actors['SPIDER'].J, 'n', 0.0), web_tgt[0], 68, 83,
                                   shoot=3))
    seq.overlay(68, 83, pw.webline(lambda sc, a: pw.hand_tip(sc.actors['SPIDER'].J, 'f', 0.0), web_tgt[1], 68, 83,
                                   shoot=3))
    # the web stays stuck on his chest plate (two splats) until he tears it off
    seq.overlay(71, 140, pw.splat_at(web_tgt[0], 71, 140, r=0.075, seed=8), layer='front')
    seq.overlay(71, 140, pw.splat_at(web_tgt[1], 71, 140, r=0.075, seed=9), layer='front')
    seq.overlay(64, 76, pw.spider_sense('SPIDER', lambda a: max(0.0, min(1.0, (a - 64) / 3.0, (76 - a) / 4.0))),
                layer='top')

    # DOOM is folded backwards; the wild bolt goes up and behind him into the tank
    dhit = P(DM['hit_chest'], dhigh['x'] + 0.12, -1, dy=0.05, an=204, en=6)
    fire_pt = pw.hand_tip(solve(DOOM, dhit), 'n', 0.12)
    d.key(82, P(dhigh, dhigh['x'], -1, an=dhigh['an'] + 6, lean=-6, dy=0.01), ease='lin', lock='nf',
          label='CONTACT: the bolt goes off')
    d.key(84, dhit, ease='dec', label='folded back, arm flung up')
    d.key(88, P(DM['skid'], dhigh['x'] + 1.05, -1, lean=4, head=-6, an=100, en=40), ease='smooth', xease='lin')
    dsk = P(DM['skid'], dhigh['x'] + 2.4, -1)
    d.key(100, dsk, ease='smooth', xease=('dec', 2.6), lock='nf', label='skid stops')
    d.lag(84, 100, 'arms', 2)
    d.lag(82, 98, 'head', 1)
    seq.overlay(84, LEAK_F + 1, pw.bolt(fire_pt, target_tank, 84, LEAK_F, size=0.18))

    # SPIDER-MAN springs off the chest: back flip, lands in a crouch
    sl2 = P(SP['crouch3'], kick['x'] - 2.3, 1)
    s.path(83, 96, arc(83, 96, (kick['x'] - 0.1, kick['y'] + 0.1), (sl2['x'], sl2['y']), height=1.1, hang=1.8))
    s.key(83, P(SP['chamber'], 0, 1), ease='dec', label='springs off the chest')
    s.key(86, P(SP['tuck'], 0, 1, rot=-110), ease='lin', label='back flip')
    s.key(89, P(SP['tuck'], 0, 1, rot=-210), ease='lin')
    s.key(92, P(SP['open_out'], 0, 1, rot=-300), ease='dec')
    s.key(96, sl2, ease='dec', lock='nf', hands='n', label='lands')
    s.lag(83, 95, 'arms', 1)

    # ================================================================ 2D aftermath
    sgx = foot_on(SPIDER, P(SP['guard'], 0, 1), 'n', ankle(SPIDER, sl2, 'n')[0])
    s.key(104, sl2, ease='smooth', lock='nf', hands='n')
    s.key(114, sgx, ease='smooth', lock='nf', label='rises')
    sbk = foot_on(SPIDER, P(SP['beckon'], 0, 1), 'n', ankle(SPIDER, sgx, 'n')[0] - 0.05)
    s.key(128, sgx, ease='smooth', lock='nf')
    s.key(134, sbk, ease='smooth', lock='nf', label='"come on"')
    s.key(138, P(sbk, sbk['x'], 1, en=80, ef=60), ease='smooth', lock='nf')
    s.key(142, sbk, ease='smooth', lock='nf')
    s.key(146, P(sbk, sbk['x'], 1, en=80), ease='smooth', lock='nf')
    s.key(156, sgx, ease='smooth', lock='nf')
    breathe(s, 158, 190, sgx, amp=0.02, period=12, arm=4)
    s.key(189, sgx, lock='nf')

    dF = ankle(DOOM, dsk, 'n')[0]
    dR = ankle(DOOM, dsk, 'f')[0]
    dstand2 = stance_at(DOOM, DM['stand_wide'], dF + 0.1, dR, -1)
    d.key(108, P(dsk, dsk['x'], -1, dy=0.02, lean=16), ease='smooth', lock='nf')
    d.key(118, dstand2, ease='smooth', lock='nf', label='straightens')
    drip = stance_at(DOOM, DM['rip'], dF + 0.1, dR, -1)
    d.key(126, drip, ease='smooth', lock='nf', label='looks down at the webbing')
    d.key(131, P(drip, drip['x'], -1, head=30, dy=-0.01), ease='smooth', lock='nf')
    dfl = stance_at(DOOM, DM['fling'], dF + 0.1, dR, -1)
    d.key(140, P(drip, drip['x'], -1, head=26, an=50, en=100), ease='acc', lock='nf')
    d.key(143, dfl, ease='whip', lock='nf', label='tears it off, flings it away')
    d.smear(141, 144, ['an'], 0.7)
    d.key(156, dstand2, ease='smooth', lock='nf')
    d.key(162, P(dstand2, dstand2['x'], -1, head=-6), ease='smooth', lock='nf', label='eyes flare')
    breathe(d, 164, 190, P(dstand2, dstand2['x'], -1, head=-6), amp=0.006, period=26, arm=1.0)
    d.key(189, P(dstand2, dstand2['x'], -1, head=-6), lock='nf')
    # the torn-off webbing: in his fist, then flung (ballistic) onto the roof
    Jfl = solve(DOOM, dfl)

    def torn(sc, a):
        if a < 143:
            return pw.hand_tip(sc.actors['DOOM'].J, 'n', 0.0)
        t = (a - 143) / 24.0
        y0 = Jfl.hand_n[1]
        t = min(t, (2.4 + math.sqrt(2.4 * 2.4 + 4 * 4.9 * (y0 - 0.03))) / 9.8)
        return (Jfl.hand_n[0] + 2.6 * t, max(0.03, y0 + 2.4 * t - 4.9 * t * t))
    seq.overlay(140, 190, pw.splat_at(torn, 140, 190, r=0.09, seed=8))

    seq.add(d, z=0)
    seq.add(s, z=1)
    seq.zorder(76, ['DOOM', 'SPIDER'])

    # ================================================================ water
    stream_fn, land_x = pw.stream(HOLE, LEAK_F, v0=LEAK_V0)
    seq.overlay(LEAK_F, 190, stream_fn, layer='back')
    pc = PUDDLE_X
    seq.overlay(LEAK_F, 190, pw.puddle(lambda a: pc, lambda a: puddle_half(a - LEAK_F)), layer='back')

    def gush(fx, sc, rf, a):
        if a >= LEAK_F + 8:
            pw.splash(fx, land_x, n=2, speed=2.0, up=2.6)
    seq.emit(LEAK_F, 190, gush)

    def holed(fx, sc, rf):
        pw.explosion(fx, HOLE[0], HOLE[1], power=1.0, seed=86)
        fx.debris(HOLE[0], n=0)
        for _ in range(10):
            fx.ps.append(pw.Particle('debris', HOLE[0], HOLE[1], fx.rnd.uniform(-4, -1), fx.rnd.uniform(-1, 3),
                                     life=fx.rnd.randint(16, 28), r=fx.rnd.uniform(0.02, 0.05),
                                     col=(0.3, 0.24, 0.22), g=1.6, drag=0.97, bounce=0.3))
        sc.shake.add(rf, 0.05, frames=8, dx=0.3, dy=0.6, seed=86)
    seq.at(LEAK_F, holed)

    # ================================================================ camera
    c = seq.cam
    moon = dict(moon_r=0.5, moon_x=2.6, moon_dy=1.75)
    mid0 = (sg['x'] + DS) / 2
    c.key(0, cx=mid0, cy=1.15, h=5.3, ease='smooth', **moon)
    c.key(18, cx=mid0 - 0.2, cy=1.2, h=5.0, ease='smooth', **moon)
    c.key(34, cx=mid0 + 0.1, cy=1.15, h=4.8, ease='smooth', **moon)
    c.key(64, cx=(sx2 + DS) / 2, cy=1.2, h=4.6, ease='smooth', **moon)
    c.key(82, cx=chest_pt[0] - 0.2, cy=1.3, h=3.6, ease='smooth', **moon)
    c.key(88, cx=3.0, cy=2.0, h=7.0, ease='smooth', **moon)
    c.key(96, cx=(sl2['x'] + dsk['x']) / 2 + 1.0, cy=1.75, h=6.9, ease='smooth', **moon)
    c.key(110, cx=(sl2['x'] + dsk['x']) / 2 + 0.6, cy=1.55, h=6.2, ease='smooth', **moon)
    # MCU DOOM tearing the webbing off (water pouring behind him)
    dh = head_of(DOOM, drip)
    c.key(122, cut=True, cx=dh[0] - 0.55, cy=dh[1] - 0.45, h=2.3, ease='smooth', moon_r=0.5, moon_x=0.9,
          moon_dy=1.75)
    c.key(158, cx=dh[0] - 0.62, cy=dh[1] - 0.4, h=2.1, moon_r=0.5, moon_x=0.9, moon_dy=1.75)
    c.key(159, cut=True, cx=(sgx['x'] + dstand2['x']) / 2 + 0.4, cy=1.5, h=6.0, ease='smooth', **moon)
    c.key(189, cx=(sgx['x'] + dstand2['x']) / 2 + 0.4, cy=1.5, h=5.8, **moon)

    # ================================================================ impact + fx
    seq.impact(82, chest_pt[0] - 0.05, chest_pt[1], dirx=1, diry=0.2, power=1.6, stop=5, style=['focus', 'white'],
               sound='kick_metal')

    def kickfx(fx, sc, rf):
        fx.ring(chest_pt[0], chest_pt[1], 0.08, 1.6, life=10, w=0.07)
        pw.sparks(fx, chest_pt[0], chest_pt[1], 1, 0.3, n=16, speed=9, cols=pw.FIRE)
        fx.flash_screen(0.3, (1, 0.97, 0.9))
    seq.at(82, kickfx)

    def scrape(fx, sc, rf, a):
        J = sc.actors['DOOM'].J
        for an in (J.ankle_n, J.ankle_f):
            pw.sparks(fx, an[0] - 0.05, 0.04, -1, 0.5, n=3, speed=5, spread=0.5, cols=pw.FIRE, life=(3, 7))
        fx.dust(J.ankle_n[0], n=1, dirx=-1, speed=1.6, size=0.12, alpha=0.4, life=(10, 16), col=pw.GRIT)
    seq.emit(85, 99, scrape)
    seq.at(99, lambda fx, sc, rf: (fx.skidmark(ankle(DOOM, dsk, 'n')[0], ankle(DOOM, dhit, 'n')[0] + 0.2),
                                   fx.skidmark(ankle(DOOM, dsk, 'f')[0], ankle(DOOM, dhit, 'f')[0] + 0.2, w=0.03)))
    seq.at(96, lambda fx, sc, rf: fx.dust(ankle(SPIDER, sl2, 'n')[0], n=6, dirx=-1, speed=2.2, size=0.15,
                                          alpha=0.45, col=pw.GRIT))
    seq.at(33, lambda fx, sc, rf: fx.dust(sx2, n=6, dirx=1, speed=2.0, size=0.15, alpha=0.45, col=pw.GRIT))

    def doom_glow(a):
        if a < 160:
            return 1.2 if a < 82 else 0.8
        return 0.8 + 1.8 * min(1.0, (a - 160) / 5.0) - 0.8 * max(0.0, (a - 172) / 18.0)
    seq.glow['DOOM'] = doom_glow
    seq.glow['SPIDER'] = lambda a: 1.15 if 10 <= a < 22 else (0.75 if 66 <= a < 82 else 0.9)

    def flare(fx, sc, rf):
        from heroes import Head
        H = Head(sc.actors['DOOM'].J, 36)
        for sx_ in (-1, 1):
            q = H.decal(sx_ * 0.27, 0.17)[0]
            fx.glint(q[0], q[1], size=0.12, life=9, col=(0.75, 1.0, 0.8))
    seq.at(163, flare)

    def motes(fx, sc, rf, a):
        if a % 4 == 0:
            fx.dust(fx.rnd.uniform(-8, 10), fx.rnd.uniform(0.1, 2.2), n=1, dirx=-1, speed=1.0, size=0.025,
                    life=(30, 50), up=0.05, alpha=0.3)
    seq.emit(0, 190, motes)

    # ================================================================ sound
    seq.sfx(10, 'spider_sense', 1.0)
    seq.sfx(12, 'charge_short', 0.8)
    seq.sfx(19, 'jump', 0.8)
    seq.sfx(21, 'bolt', 1.0)
    seq.sfx(25, 'blast', 1.0)
    seq.sfx(33, 'land', 0.8)
    seq.sfx(39, 'thwip', 1.0)
    seq.sfx(40, 'shield_up', 0.9)
    seq.sfx(42, 'thwip', 0.9)
    seq.sfx(44, 'shield_hit', 1.0)
    seq.sfx(47, 'shield_hit', 0.9)
    seq.sfx(58, 'shield_down', 0.7)
    seq.sfx(64, 'charge', 1.0)
    seq.sfx(64, 'spider_sense', 0.8)
    seq.sfx(68, 'thwip', 1.0)
    seq.sfx(69, 'thwip', 0.8)
    seq.sfx(73, 'whoosh_big', 1.0)
    seq.sfx(84, 'bolt', 0.8)
    seq.sfx(84, 'skid_metal', 1.0)
    seq.sfx(LEAK_F, 'blast', 0.9)
    seq.sfx(LEAK_F + 2, 'water_gush', 1.0)
    seq.sfx(86, 'whoosh', 0.7)
    seq.sfx(96, 'land', 0.8)
    seq.sfx(143, 'whoosh', 0.6)
    seq.sfx(163, 'doom_glint', 0.9)

    for f_, t_ in [(0, '2A stand-off'), (13, '2A charge'), (21, '2A bolt 1'), (25, '2A blast'), (37, '2B webs/field'),
                   (60, '2B overhead charge'), (68, '2C web-yank'), (82, '2C DROPKICK'), (86, '2C tank holed'),
                   (100, '2D aftermath'), (122, '2D MCU DOOM'), (159, '2D wide')]:
        seq.note(f_, t_)
    seq.state = dict(spider=s.eval(189), doom=d.eval(189), scorch_x=target1[0],
                     roof_splats=[fall(189) for fall in falls], torn=torn(None, 189))
    Jd_end = solve(DOOM, dsk)
    seq.geometry = dict(bolt1_from_x=p0[0], bolt1_from_y=p0[1], crouch_x=crouch_x, kick_hip_x=kick['x'],
                        kick_hip_y=kick['y'], chest_x=chest_pt[0], doom_skid_end=dsk['x'], puddle_x=pc,
                        leak_land_x=land_x, spider_end=sgx['x'], doom_end=dstand2['x'],
                        fire_x=fire_pt[0], fire_y=fire_pt[1])
    return seq


if __name__ == '__main__':
    for kk, v in build().geometry.items():
        print(f'{kk:22s} {v:7.2f}')
