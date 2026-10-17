"""DOOM vs SPIDER-MAN -- SEQUENCE 1: ARRIVAL (240 animation frames, 10 s @ 24 fps)

  1A   0- 96  crane down out of the night sky: DOOM descends on rocket boots past the moon,
              brakes, cuts the jets and drops into a three-point landing that cracks the roof;
              he rises to his full height (cape settling)
  1B  97-128  CU DOOM: the eye slits flare. Name card.
  1C 129-181  wide: a web line snaps onto the water-tower finial from off screen; SPIDER-MAN
              swings in under the tank (pendulum, fastest at the bottom), lets go on the upswing,
              front-flips over DOOM's head with a half twist and lands in a crouch BEHIND him.
              DOOM's head tracks him overhead.
  1D 182-215  CU SPIDER-MAN rising out of the crouch, lenses narrowing. Name card.
  1E 216-239  wide two-shot: DOOM has turned around; they face each other across the roof.
"""
import math
import random

from heroes import SPIDER, DOOM, TAU
from heroposes import LIB2
from engine import Track, arc
from scene import Sequence
from author import P, foot_on, ankle, hand, head_of, breathe
from rooftop import Rooftop, TOWER_X, TANK_Y1
from rig import solve
import powers as pw
from titles import name_card

SP, DM = LIB2['SPIDER'], LIB2['DOOM']
DX = 1.4                  # where DOOM lands
SX = -3.0                 # where SPIDER-MAN lands
ANCHOR = (TOWER_X, TANK_Y1 + 0.98)      # the finial on top of the water tower


def swing_fn(f0, f1, th0, th1, R, amp, face=-1, start_hold=0):
    """Pendulum about ANCHOR: phase advances linearly (true harmonic motion), so the
    swing is fastest at the bottom. Drives hip x, y and the body rotation."""
    p0 = math.acos(max(-1, min(1, th0 / amp)))
    p1 = math.acos(max(-1, min(1, th1 / amp)))

    def theta(f):
        if f < f0 + start_hold:
            return th0
        u = (f - f0 - start_hold) / float(f1 - f0 - start_hold)
        return amp * math.cos(p0 + (p1 - p0) * u)

    def fn(f):
        th = theta(f)
        t = math.radians(th)
        return dict(x=ANCHOR[0] + R * math.sin(t), y=ANCHOR[1] - R * math.cos(t), rot=-face * th)
    return fn, theta


def build():
    random.seed(101)
    seq = Sequence('D1', 240, wind=lambda a: -0.5)
    seq.stage = Rooftop()
    d = Track(DOOM)
    s = Track(SPIDER)

    # ================================================================ 1A DOOM's descent
    def hov(y, x=DX, **kw):
        q = P(DM['hover'], x, 1, yaw=15, **kw)
        q['y'] = y
        return q
    y0, y1 = 9.6, 1.95
    d.key(0, hov(y0, an=34, af=-26), ease=('dec', 2.4), label='descending on the jets')
    d.key(14, hov(y0 - (y0 - y1) * 0.62, x=DX + 0.12, an=28, af=-20, head=10), ease='smooth')
    d.key(30, hov(y1 + 0.55, x=DX - 0.06, an=40, af=-34), ease='dec')
    d.key(42, hov(y1 + 0.12, x=DX + 0.02), ease='smooth', label='brakes')
    brake = P(DM['brake'], DX, 1, yaw=15)
    brake['y'] = y1
    d.key(48, brake, ease='smooth', label='hover: knees up, arms out')
    d.key(53, dict(brake, y=y1 + 0.04), ease='acc', label='jets cut')
    land = P(DM['land'], DX, 1)
    drop = P(DM['hover'], DX, 1, ln=30, kn=40, lf=10, kf=30, an=60, af=-50, pn=0.4, pf=0.4)
    drop['y'] = 1.15
    d.key(56, drop, ease='acc', label='drops')
    d.key(58, land, ease='dec', lock='n', hands='n', label='THREE-POINT LANDING')
    d.key(62, P(DM['land'], DX, 1, dy=-0.03, head=-14), ease='smooth', lock='n', hands='n')
    d.key(74, P(DM['land'], DX, 1, dy=-0.02, head=-22), ease='smooth', lock='n', hands='n')
    rise = foot_on(DOOM, P(DM['rise'], 0, 1), 'n', ankle(DOOM, land, 'n')[0])
    d.key(84, rise, ease='smooth', lock='n', label='rises')
    stand = foot_on(DOOM, P(DM['stand'], 0, 1), 'n', ankle(DOOM, land, 'n')[0])
    d.key(94, stand, ease='smooth', lock='nf', label='full height')
    d.lag(84, 96, 'arms', 2)
    DS = stand['x']

    # ================================================================ 1B CU DOOM
    dcu = P(DM['stand'], DS, 1, yaw=24)
    d.key(97, dcu, lock='nf')
    d.key(108, P(DM['stand'], DS, 1, yaw=24, head=-6, dy=0.01), ease='smooth', lock='nf')
    d.key(128, P(DM['stand'], DS, 1, yaw=24, head=-5), ease='hold', lock='nf')

    # ================================================================ 1C the swing
    R = 4.45
    amp = 64.0
    sw0, sw1, fl1 = 136, 150, 172
    swing, theta = swing_fn(133, sw1, 55.0, -46.0, R, amp, face=-1, start_hold=sw0 - 133)
    s.path(133, sw1, swing)
    hang = P(SP['swing'], 0, -1)
    s.key(133, P(SP['swing'], 0, -1, an=150, en=20), ease='smooth', label='on the line (off screen)')
    s.key(139, hang, ease='smooth', label='swing')
    s.key(144, P(SP['swing_pump'], 0, -1), ease='smooth', label='pump: legs drive through the bottom')
    s.key(149, P(SP['release'], 0, -1), ease='lin', label='release')
    rel = swing(sw1)
    landp = P(SP['crouch3'], SX, 1)
    s.path(sw1, fl1, arc(sw1, fl1, (rel['x'], rel['y']), (landp['x'], landp['y']), height=1.25, hang=1.7))
    s.key(sw1, P(SP['release'], 0, -1, rot=rel['rot']), ease='dec')
    s.key(154, P(SP['tuck'], 0, -1, rot=rel['rot'] + 110), ease='lin', label='front flip over DOOM')
    s.key(158, P(SP['tuck'], 0, -1, rot=rel['rot'] + 230), ease='lin')
    # half twist inside the tuck: facing flips, the world rotation carries on
    w = -(-1) * (rel['rot'] + 270)
    s.key(159, P(SP['tuck'], 0, 1, rot=-w), ease='lin', label='half twist')
    s.key(165, P(SP['open_out'], 0, 1, rot=-360 + 10), ease='dec', label='opens out')
    s.key(169, P(SP['land'], 0, 1, rot=-360, dy=0.25), ease='acc')
    s.key(fl1, landp, ease='dec', lock='nf', hands='n', label='lands: crouch')
    s.key(176, P(SP['crouch3'], SX, 1, dy=-0.03), ease='smooth', lock='nf', hands='n')
    s.key(181, landp, ease='smooth', lock='nf', hands='n')
    s.lag(150, 170, 'arms', 1)

    # DOOM watches him come, tracks him overhead, starts to turn
    d.key(129, stand, lock='nf')
    d.key(140, P(stand, DS, 1, head=-8), ease='smooth', lock='nf', label='sees him')
    d.key(156, P(stand, DS, 1, head=-34, lean=-6), ease='smooth', lock='nf', label='head tracks him overhead')
    d.key(166, P(stand, DS, 1, head=-14, yaw=40), ease='smooth', lock='nf')
    d.key(176, P(stand, DS, 1, head=-4, yaw=70), ease='smooth', lock='nf', label='turning')
    d.key(181, P(stand, DS, 1, yaw=80), ease='lin', lock='nf')

    # ================================================================ 1D CU SPIDER-MAN
    scu = P(SP['crouch3'], SX, 1, yaw=26)
    s.key(182, scu, lock='nf', hands='n')
    s.key(192, P(SP['crouch3'], SX, 1, yaw=26, head=-40, dy=0.01), ease='smooth', lock='nf', hands='n',
          label='looks up at DOOM')
    sg = foot_on(SPIDER, P(SP['guard'], 0, 1), 'n', ankle(SPIDER, landp, 'n')[0])
    s.key(203, P(sg, sg['x'], 1, yaw=26), ease='smooth', lock='nf', label='rises into his stance')
    s.key(215, P(sg, sg['x'], 1, yaw=26, dy=0.01), ease='smooth', lock='nf')
    d.key(182, P(stand, DS, -1, yaw=60))
    d.key(196, P(stand, DS, -1, yaw=10), ease='smooth', lock='nf')

    # ================================================================ 1E two-shot
    s.key(216, sg, lock='nf')
    breathe(s, 217, 240, sg, amp=0.02, period=12, arm=4)
    dst = P(DM['stand'], DS, -1)
    d.key(216, dst, lock='nf')
    breathe(d, 217, 240, dst, amp=0.008, period=30, arm=1.5)
    s.key(239, sg, lock='nf')
    d.key(239, dst, lock='nf')

    seq.add(d, z=0)
    seq.add(s, z=1)
    seq.actors['SPIDER'].visible = [(133, 10 ** 9)]
    seq.fast = [('DOOM', 0, 14), ('SPIDER', 136, 151)]     # rocket descent, the bottom of the swing

    # ================================================================ camera
    c = seq.cam
    moon = dict(moon_r=0.62, moon_x=0.15, moon_dy=1.55)
    c.key(0, cx=DX, cy=4.4, h=6.8, ease='smooth', **moon)
    c.key(30, cx=DX, cy=2.5, h=6.2, ease='smooth', **moon)
    c.key(50, cx=DX, cy=1.45, h=5.4, ease='smooth', **moon)
    c.key(58, cx=DX, cy=1.25, h=5.4, ease='smooth', **moon)
    c.key(64, cx=DX, cy=1.2, h=5.3, ease='smooth', **moon)
    c.key(96, cx=DX - 0.1, cy=1.15, h=3.5, **moon)
    dh = head_of(DOOM, dcu)
    c.key(97, cut=True, cx=dh[0] + 0.42, cy=dh[1] - 0.12, h=1.45, ease='lin', moon_r=0.55, moon_x=1.6,
          moon_dy=1.7)
    c.key(128, cx=dh[0] + 0.38, cy=dh[1] - 0.1, h=1.3, moon_r=0.55, moon_x=1.6, moon_dy=1.7)
    c.key(129, cut=True, cx=4.1, cy=2.3, h=7.6, ease='smooth', moon_r=0.5, moon_x=2.6, moon_dy=1.75)
    c.key(146, cx=3.4, cy=2.2, h=7.4, ease='smooth')
    c.key(172, cx=-0.6, cy=1.6, h=6.6, ease='dec')
    c.key(181, cx=-0.7, cy=1.5, h=6.4)
    sh = head_of(SPIDER, P(SP['crouch3'], SX, 1, yaw=26, head=-40))
    c.key(182, cut=True, cx=sh[0] + 0.62, cy=sh[1] + 0.02, h=1.8, ease='smooth', moon_r=0.5, moon_x=-2.4,
          moon_dy=1.7)
    c.key(215, cx=sh[0] + 0.75, cy=sh[1] + 0.22, h=1.95, moon_r=0.5, moon_x=-2.4, moon_dy=1.7)
    mid = (sg['x'] + DS) / 2
    c.key(216, cut=True, cx=mid, cy=1.15, h=5.6, ease='smooth', moon_r=0.5, moon_x=2.6, moon_dy=1.75)
    c.key(239, cx=mid, cy=1.15, h=5.3, moon_r=0.5, moon_x=2.6, moon_dy=1.75)

    # ================================================================ fx
    seq.fade(0, 16, 1.0, 0.0)
    jet = lambda a: (1.0 if a < 42 else (1.35 if a < 53 else max(0.0, 1.35 - (a - 53) * 0.6))) \
        * (1.0 + 0.06 * math.sin(a * 2.1))
    seq.overlay(0, 58, pw.jets('DOOM', jet), layer='back')

    def exhaust(fx, sc, rf, a):
        J = sc.actors['DOOM'].J
        for an in (J.ankle_n, J.ankle_f):
            fx.add(pw.Smoke(an[0], an[1] - 0.35, n=1, size=0.1, rise=-0.4, life=(14, 24), seed=rf * 3 + int(an[0] * 9),
                            col=(0.4, 0.38, 0.42), alpha=0.35))
        if a % 2 == 0:
            pw.sparks(fx, J.ankle_n[0], J.ankle_n[1] - 0.3, 0, -1, n=2, speed=4, spread=0.4,
                      cols=pw.FIRE, life=(4, 8))
    seq.emit(0, 54, exhaust)
    seq.emit(36, 54, lambda fx, sc, rf, a: fx.dust(DX + fx.rnd.uniform(-0.4, 0.4), n=1, dirx=fx.rnd.choice((-1, 1)),
                                                     speed=2.6, size=0.18, alpha=0.35, up=0.3, col=pw.GRIT))
    hand_pt = hand(DOOM, land, 'n')

    def landing(fx, sc, rf):
        fx.ring(DX, 0.02, 0.1, 3.0, life=14, w=0.08, squash=0.16, col=(0.85, 0.85, 0.95))
        fx.ring(DX, 0.02, 0.1, 1.8, life=10, w=0.05, squash=0.16)
        fx.crack(hand_pt[0], n=9, length=1.6)
        fx.debris(hand_pt[0], n=16, speed=3.2, up=5.0)
        fx.dust(DX, n=7, dirx=-1, speed=3.6, size=0.22, alpha=0.55, life=(12, 22), up=0.6, col=pw.GRIT)
        fx.dust(DX, n=7, dirx=1, speed=3.6, size=0.22, alpha=0.55, life=(12, 22), up=0.6, col=pw.GRIT)
        sc.shake.add(rf, 0.12, frames=12, dx=0.2, dy=1.0, seed=58)
        fx.flash_screen(0.12, (0.85, 0.9, 1.0))
    seq.at(58, landing)
    seq.hitstop(58, 3)

    def doom_glow(a):
        if a < 97:
            return 0.7
        if a < 108:
            return 0.7 + 1.9 * (a - 97) / 11.0
        if a < 129:
            return 2.6 - 1.2 * (a - 108) / 21.0
        return 1.2
    seq.glow['DOOM'] = doom_glow

    def flare(fx, sc, rf):
        J = sc.actors['DOOM'].J
        from heroes import Head
        H = Head(J, 36)
        for sx_ in (-1, 1):
            q = H.decal(sx_ * 0.27, 0.17)[0]
            fx.glint(q[0], q[1], size=0.13, life=9, col=(0.75, 1.0, 0.8))
    seq.at(107, flare)
    seq.cards.append((110, 129, name_card('DOOM', 'MONARCH OF LATVERIA', (0.45, 0.85, 0.5), 'right')))

    # the web line onto the finial, held through the swing
    seq.overlay(133, sw1 + 1, pw.webline(lambda sc, a: pw.hand_tip(sc.actors['SPIDER'].J, 'n', 0.0), ANCHOR,
                                         133, sw1 + 1, shoot=3), layer='front')
    # the released line falls away
    seq.overlay(sw1 + 1, sw1 + 9, lambda ctx, sc, a, rf, px, ink: pw.web_strand(
        ctx, ANCHOR, (ANCHOR[0] - 1.2 - (a - sw1) * 0.2, ANCHOR[1] - 1.4 - (a - sw1) ** 1.6 * 0.25), px, ink,
        alpha=max(0.0, 1 - (a - sw1) / 8.0), wobble=0.05, rf=rf))
    seq.emit(sw0, sw1, lambda fx, sc, rf, a: fx.speedlines(sc.actors['SPIDER'].J.hip[0], sc.actors['SPIDER'].J.hip[1],
                                                           -1, n=1, length=1.4, spread=0.5))

    def touch(fx, sc, rf):
        fx.dust(SX, n=7, dirx=-1, speed=2.4, size=0.16, alpha=0.5, col=pw.GRIT)
        fx.dust(SX + 0.3, n=4, dirx=1, speed=1.6, size=0.13, alpha=0.45, col=pw.GRIT)
    seq.at(fl1, touch)

    def lens(a):
        if a < 186:
            return 1.0
        if a < 196:
            return 1.0 - 0.38 * (a - 186) / 10.0
        return 0.62 if a < 216 else 0.8
    seq.glow['SPIDER'] = lens
    seq.cards.append((193, 216, name_card('SPIDER-MAN', 'YOUR FRIENDLY NEIGHBORHOOD', (0.95, 0.3, 0.3), 'right')))

    def motes(fx, sc, rf, a):
        if a % 4 == 0:
            fx.dust(fx.rnd.uniform(-8, 10), fx.rnd.uniform(0.1, 2.2), n=1, dirx=-1, speed=1.0, size=0.025,
                    life=(30, 50), up=0.05, alpha=0.3)
    seq.emit(0, 240, motes)

    # ================================================================ sound
    seq.sfx(0, 'jet_long', 0.9)
    seq.sfx(42, 'jet_brake', 1.0)
    seq.sfx(56, 'whoosh_big', 0.8)
    seq.sfx(58, 'slam', 1.0)
    seq.sfx(70, 'debris', 0.6)
    seq.sfx(107, 'doom_glint', 1.0)
    seq.sfx(133, 'thwip', 1.0)
    seq.sfx(140, 'whoosh_big', 0.9)
    seq.sfx(150, 'whoosh', 0.8)
    seq.sfx(160, 'whoosh', 0.6)
    seq.sfx(fl1, 'land', 1.0)
    seq.sfx(190, 'glint', 0.6)

    for f_, t_ in [(0, '1A crane down: DOOM descends'), (58, '1A landing'), (97, '1B CU DOOM'),
                   (129, '1C the swing'), (150, '1C release / flip'), (172, '1C lands'),
                   (182, '1D CU SPIDER-MAN'), (216, '1E two-shot')]:
        seq.note(f_, t_)
    rel_x = rel['x']
    Jd = solve(DOOM, stand)
    top_of_doom = Jd.head[1] + DOOM.head_r
    over = [solve(SPIDER, s.eval(f)) for f in range(sw1, fl1) if abs(s.eval(f)['x'] - DS) < 0.5]
    clear = min(min(J.hip[1], J.ankle_n[1], J.ankle_f[1], J.head[1]) for J in over) - top_of_doom if over else 9
    seq.geometry = dict(doom_x=DS, spider_x=sg['x'], gap=DS - sg['x'], release_x=rel_x, release_y=rel['y'],
                        flip_clearance=clear)
    return seq


if __name__ == '__main__':
    for kk, v in build().geometry.items():
        print(f'{kk:22s} {v:7.2f}')
