"""SEQUENCE 4 — CLASH & RESOLUTION (anim frames 0-335, ~14 s)

  4A   0- 15  mirrored wide: both coil at the same moment
  4B  16- 43  both sprint; KAI's fist meets SEN's palm mid-screen: DOUBLE IMPACT FRAME (white focus,
              then dark), double ring, ground shockwave; both thrown back, skidding
  4C  44- 91  the beat: wide breath; CU SEN closes his eyes, opens them blazing; CU KAI, embers
              at full heat, sinks into his launch crouch
  4D  92-118  KAI's last charge -- the S1 sprint and straight right, again. SEN does not sway back:
              he steps IN, the fist passes over his shoulder, and his rising palm meets KAI's chin
              as KAI's whole weight arrives: DOUBLE IMPACT FRAME, 6-frame hit-stop
  4E 119-175  KAI launched, lands on his back, bounces, slides. SEN holds the follow-through.
  4F 176-335  SEN lowers his hand; KAI lifts his head and lets it fall; SEN bows, turns, walks
              into the dark. Fade. Title.
"""
from rig import KAI, SEN, solve
from poses import LIB, with_hand_on_ground
from engine import Track, arc
from scene import Sequence
from author import P, swap, foot_on, ankle, hand, head_of, breathe, stance_at, lifted
from titles import title_card

K, S = LIB['KAI'], LIB['SEN']
S3_END_CX = 2.42     # matches the final framing of sequence 3 (no jump cut)


def run_plan(build, L, rear_pin, face, scale, final_name, flights=(0.5, 0.6), contact=0.45, strides=2,
             final_adv=0.45):
    """push(far) -> flight -> contact(near) -> push(near) -> flight -> final drawing (near foot lands).
    Returns the list of (frame offset, pose, lock) and the final pose."""
    out = []
    push1 = foot_on(build, P(swap(L['run_push']), 0, face), 'f', rear_pin)
    fl1 = P(swap(L['run_flight']), push1['x'] + face * flights[0] * scale, face)
    if strides == 1:
        out += [(0, push1, 'f'), (3, fl1, '')]
        fin = P(L[final_name], fl1['x'] + face * 0.45 * scale, face)
        return out, fin, None
    con1 = P(L['run_contact'], fl1['x'] + face * contact * scale, face)
    pin1 = ankle(build, con1, 'n')[0]
    push2 = foot_on(build, P(L['run_push'], 0, face), 'n', pin1)
    fl2 = P(L['run_flight'], push2['x'] + face * flights[1] * scale, face)
    out += [(0, push1, 'f'), (2, fl1, ''), (4, con1, 'n'), (6, push2, 'n'), (8, fl2, '')]
    fin = P(L[final_name], fl2['x'] + face * final_adv * scale, face)
    return out, fin, pin1


def solve_run(build, L, rear_pin, face, final_name, target_x, side, part='hand', strides=2, final_adv=0.45):
    """Find the stride scale so the final drawing's hand/head reaches target_x."""
    lo, hi = 0.2, 3.0
    for _ in range(40):
        mid = (lo + hi) / 2
        _, fin, _ = run_plan(build, L, rear_pin, face, mid, final_name, strides=strides, final_adv=final_adv)
        x = hand(build, fin, side)[0] if part == 'hand' else head_of(build, fin)[0]
        if (x - target_x) * face < 0:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def build():
    seq = Sequence('S4', 336, wind=lambda a: -0.55 - (1.4 if 118 <= a < 124 else 0.0))
    k = Track(KAI)
    s = Track(SEN)

    KF, KR = 3.74, 4.60
    SF, SR = 1.23, 0.47
    kg = stance_at(KAI, K['guard'], KF, KR, -1)
    sg = stance_at(SEN, S['guard'], SF, SR, 1)

    # ================================================================ 4A mirrored coil
    breathe(k, 0, 8, kg, amp=0.03, period=14, arm=4)
    breathe(s, 0, 8, sg, amp=0.025, period=14, arm=3)
    k.key(9, kg, lock='nf', ease='acc')
    s.key(9, sg, lock='nf', ease='acc')
    k.key(14, stance_at(KAI, K['launch'], KF - 0.05, KR, -1, frac=0.5), lock='nf', ease='lin', label='coil')
    s.key(14, stance_at(SEN, S['land'], SF + 0.05, SR, 1, frac=0.5), lock='nf', ease='lin', label='coil')

    # ================================================================ 4B charge & clash
    xc = (KF + SF) / 2
    # KAI's fist and SEN's palm meet at (xc, yc)
    kce0 = P(K['cross_ext'], 0, -1)
    kfist = hand(KAI, kce0, 'f')
    yc = kfist[1]
    # pick SEN's arm angle so the palm arrives at the same height
    best = None
    for an in range(90, 125):
        q = P(S['clash_palm'], 0, 1, an=an)
        hy = hand(SEN, q, 'n')[1]
        if best is None or abs(hy - yc) < best[0]:
            best = (abs(hy - yc), an)
    s_an = best[1]
    sk = solve_run(KAI, K, KR, -1, 'cross_ext', xc + 0.06, 'f', strides=1)
    plan_k, kfin, kpin = run_plan(KAI, K, KR, -1, sk, 'cross_ext', strides=1)
    S2 = dict(S)
    S2['clash_palm_x'] = P(S['clash_palm'], 0, 1, an=s_an)
    ss = solve_run(SEN, S2, SR, 1, 'clash_palm_x', xc - 0.06, 'n', strides=1)
    plan_s, sfin, spin = run_plan(SEN, S2, SR, 1, ss, 'clash_palm_x', strides=1)
    for off, pz, lk in plan_k:
        k.key(18 + off, pz, ease='lin', lock=lk)
    for off, pz, lk in plan_s:
        s.key(18 + off, pz, ease='lin', lock=lk)
    k.key(25, P(K['cross_break'], kfin['x'] + 0.15, -1, dy=0.02), ease='lin')
    k.key(26, kfin, ease='dec', label='CLASH (fist)')
    s.key(25, P(S['clash_palm'], sfin['x'] - 0.15, 1, an=s_an - 30, en=60), ease='lin')
    s.key(26, sfin, ease='dec', label='CLASH (palm)')
    k.smear(25, 27, ['af'])
    s.smear(25, 27, ['an'])
    # thrown apart
    k.key(28, P(K['hit_body'], kfin['x'] + 0.35, -1, dy=0.06, lean=-20, bend=10, head=-20, an=120, af=150),
          ease='dec', label='thrown back')
    s.key(28, P(S['slip_back'], sfin['x'] - 0.35, 1, dy=0.04, lean=-26, an=130, af=150), ease='dec')
    kskid = P(K['skid'], kfin['x'] + 1.75, -1)
    sskid = P(S['skid'], sfin['x'] - 1.75, 1)
    k.key(31, P(K['skid'], kfin['x'] + 0.85, -1, dy=0.04), ease='smooth', xease='lin')
    s.key(31, P(S['skid'], sfin['x'] - 0.85, 1, dy=0.04), ease='smooth', xease='lin')
    k.key(42, kskid, ease='smooth', xease=('dec', 3), lock='nf', label='skid stops')
    s.key(42, sskid, ease='smooth', xease=('dec', 3), lock='nf', label='skid stops')
    k.lag(28, 42, 'arms', 2)
    s.lag(28, 42, 'arms', 2)

    # ================================================================ 4C the beat
    breathe(k, 44, 92, kskid, amp=0.035, period=14, arm=4)
    breathe(s, 44, 60, sskid, amp=0.03, period=16, arm=3)
    # CU SEN: eyes close, settle, open
    scu = P(sskid, sskid['x'], 1, yaw=30)
    s.key(60, scu, lock='nf', label='CU: eyes close')
    s.key(68, P(scu, scu['x'], 1, dy=0.02, head=10), lock='nf', ease='smooth')
    s.key(74, P(scu, scu['x'], 1, dy=-0.01, head=-4), lock='nf', ease='smooth', label='eyes open')
    s.key(91, P(scu, scu['x'], 1, head=-4), lock='nf', ease='hold')
    sg2 = stance_at(SEN, S['guard'], ankle(SEN, sskid, 'n')[0], ankle(SEN, sskid, 'f')[0], 1, dy=-0.08, lean=12,
                    bend=10, an=50, en=80)
    s.key(92, sskid, lock='nf')
    s.key(100, sg2, lock='nf', ease='smooth', label='low, still guard: waits')
    s.key(110, P(sg2, sg2['x'], 1, dy=-0.01), lock='nf', ease='smooth')
    # CU KAI: embers, sinks into the launch crouch
    kcu = P(kskid, kskid['x'], -1, yaw=30)
    k.key(76, kcu, lock='nf', label='CU KAI')
    klaunch = stance_at(KAI, K['launch'], ankle(KAI, kskid, 'n')[0], ankle(KAI, kskid, 'f')[0], -1, frac=0.5)
    k.key(84, P(kcu, kcu['x'], -1, dy=0.02, head=-6), lock='nf', ease='smooth')
    k.key(90, P(klaunch, klaunch['x'], -1, yaw=30), lock='nf', ease='acc', label='sinks into the crouch')
    k.key(91, P(klaunch, klaunch['x'], -1, yaw=30), lock='nf', ease='hold')

    # ================================================================ 4D the final exchange
    # SEN steps in and down; the rising palm meets KAI's chin at frame 118.
    sfront = ankle(SEN, sg2, 'n')[0]
    srear = ankle(SEN, sg2, 'f')[0]
    kc0 = P(K['cross_ext'], 0, -1)
    Jk0 = solve(KAI, kc0)
    chin_dx = Jk0.head[0] - 0.03 - kc0['x']
    chin_y = Jk0.head[1] - KAI.head_r * 0.95
    # search SEN's arm angle so the palm (wrist + bent hand) arrives at chin height
    best = None
    for an in range(90, 160):
        q_ = stance_at(SEN, S['palm_upper'], sfront + 0.28, srear + 0.12, 1, frac=0.62, an=an)
        hy = hand(SEN, q_, 'n')[1] + 0.08
        if best is None or abs(hy - chin_y) < best[0]:
            best = (abs(hy - chin_y), an, q_)
    sup = best[2]
    palm = hand(SEN, sup, 'n')
    chin_target = (palm[0] + 0.05, chin_y)
    kce = P(K['cross_ext'], chin_target[0] - chin_dx, -1)
    kfinal_fist = hand(KAI, kce, 'f')
    # KAI's sprint is solved so the cross lands exactly there
    kr2 = ankle(KAI, klaunch, 'f')[0]
    sk2 = solve_run(KAI, K, kr2, -1, 'cross_ext', kfinal_fist[0], 'f', final_adv=1.1)
    plan_k2, kfin2, kpin2 = run_plan(KAI, K, kr2, -1, sk2, 'cross_ext', final_adv=1.1)
    k.key(92, klaunch, lock='nf')
    k.key(99, P(klaunch, klaunch['x'], -1, dy=-0.02), lock='nf', ease='acc', label='LAST CHARGE')
    # strides every 3 frames: push 101, flight 104, contact 107, push 110, flight 113
    for off, pz, lk in plan_k2:
        k.key(101 + int(off * 1.5), pz, ease='lin', lock=lk)
    k.key(116, P(K['cross_break'], kce['x'] + 0.2, -1, dy=kce['y'] - K['cross_ext']['y']), ease='lin')
    k.key(118, kce, ease='dec', label='straight right: passes over his shoulder')
    k.smear(116, 119, ['af'])
    k.lag(98, 116, 'head', 1)
    s.key(111, sg2, lock='nf', ease='whip')
    sslip = stance_at(SEN, S['slip_in'], sfront + 0.3, srear + 0.1, 1, frac=0.55)
    s.key(114, sslip, lock='nf', ease='dec', label='steps IN, under the line')
    s.key(116, stance_at(SEN, S['palm_antic'], sfront + 0.3, srear + 0.12, 1, frac=0.55), lock='nf', ease='acc')
    s.key(118, sup, lock='nf', ease='dec', label='RISING PALM: chin')
    s.smear(117, 119, ['an'])

    # ================================================================ 4E launch
    Jk = solve(KAI, kce)
    hc = P(K['hit_chin'], 0, -1)
    land = P(K['lie'], kce['x'] + 2.5, -1)
    k.path(119, 140, arc(119, 140, (kce['x'] + 0.1, kce['y'] + 0.12), (land['x'], land['y']), height=1.0, hang=1.4,
                         xease=('dec', 2.2)))
    k.key(119, P(hc, 0, -1), ease='dec', label='launched')
    k.key(124, P(hc, 0, -1, rot=-30, head=-30), ease='smooth')
    k.key(130, P(K['launched'], 0, -1, rot=-70), ease='smooth')
    k.key(136, P(K['launched'], 0, -1, rot=-86, an=170, af=150), ease='smooth')
    k.key(140, land, ease='dec', label='lands on his back')
    k.lag(119, 140, 'arms', 2)
    k.lag(119, 140, 'legs', 1)
    k.path(141, 147, arc(141, 147, (land['x'] + 0.05, land['y']), (land['x'] + 0.35, land['y']), height=0.14,
                         hang=2.0))
    k.key(144, P(K['lie'], 0, -1, ln=60, kn=40, an=170), ease='smooth', label='bounce')
    land2 = P(K['lie'], land['x'] + 0.95, -1)
    k.key(147, P(K['lie'], land['x'] + 0.35, -1), ease='smooth')
    k.key(160, land2, ease='dec', xease=('dec', 3), label='slides to rest')
    # SEN holds the follow-through; secondary motion settles
    s.key(132, P(sup, sup['x'], 1, dy=0.01, an=142), lock='nf', ease='smooth', label='holds the follow-through')
    s.key(162, P(sup, sup['x'], 1, an=144), lock='nf', ease='smooth')

    # ================================================================ 4F resolution
    sneu = stance_at(SEN, S['neutral'], sfront + 0.2, srear + 0.22, 1)
    s.key(184, sneu, lock='nf', ease='smooth', label='lowers his hand')
    s.on_twos(162, 184)
    k.key(202, land2, ease='smooth')
    kup = with_hand_on_ground(KAI, P(K['lie_up'], land2['x'] - 0.05, -1), 'n', -0.25)
    k.key(210, kup, ease='smooth', label='lifts his head toward SEN')
    k.key(217, P(kup, kup['x'], -1, head=30), ease='smooth')
    k.key(225, land2, ease='acc', label='lets it fall')
    k.on_twos(202, 226)
    sbow = stance_at(SEN, S['bow'], sfront + 0.2, srear + 0.22, 1)
    s.key(226, sneu, lock='nf', ease='smooth')
    s.key(232, sbow, lock='nf', ease='smooth', label='bows')
    s.key(238, sbow, lock='nf', ease='smooth')
    s.key(244, sneu, lock='nf', ease='smooth')
    s.key(247, P(sneu, sneu['x'], 1, yaw=60), lock='nf', ease='lin', label='turns away')
    s.key(249, P(sneu, sneu['x'], -1, yaw=60), lock='nf', ease='lin')
    sw0 = stance_at(SEN, S['neutral'], sneu['x'] - 0.06, sneu['x'] + 0.1, -1)
    s.key(252, sw0, lock='nf', ease='smooth')
    # walk into the dark (on 2s): contact -> pass -> contact(swap) -> pass(swap)...
    f = 254
    front, rear = ankle(SEN, sw0, 'n')[0], ankle(SEN, sw0, 'f')[0]
    step = 0.62
    side = 'n'
    for i in range(6):
        other = 'f' if side == 'n' else 'n'
        stance = S['walk_contact'] if side == 'n' else swap(S['walk_contact'])
        passp = S['walk_pass'] if side == 'n' else swap(S['walk_pass'])
        # the stepping foot lands `step` ahead of the planted one
        planted = rear if i == 0 else last_land
        land_x = planted - step
        cpose = stance_at(SEN, stance, land_x, planted, -1, front=side)
        s.key(f + 6, cpose, lock='nf', ease='smooth')
        ppose = foot_on(SEN, P(swap(passp) if True else passp, 0, -1), side, land_x)
        s.key(f + 12, ppose, lock=side, ease='smooth')
        last_land = land_x
        side = other
        f += 12
    s.on_twos(254, 336)

    seq.add(k, z=0)
    seq.add(s, z=1)
    seq.zorder(110, ['SEN', 'KAI'])
    seq.zorder(124, ['KAI', 'SEN'])

    # ================================================================ camera
    c = seq.cam
    c.key(0, cx=S3_END_CX, cy=1.1, h=4.7, ease='smooth')
    c.key(14, cx=xc, cy=1.05, h=5.3, ease='acc')
    c.key(26, cx=xc, cy=1.05, h=4.3, ease='dec')
    c.key(43, cx=xc, cy=1.1, h=5.6, ease='smooth')
    c.key(59, cx=xc, cy=1.1, h=5.5)
    sh = head_of(SEN, scu)
    c.key(60, cut=True, cx=sh[0] + 0.3, cy=sh[1] - 0.1, h=1.15, ease='lin')
    c.key(75, cx=sh[0] + 0.28, cy=sh[1] - 0.08, h=1.0)
    kh = head_of(KAI, kcu)
    c.key(76, cut=True, cx=kh[0] - 0.3, cy=kh[1] - 0.16, h=1.2, ease='lin')
    c.key(91, cx=kh[0] - 0.28, cy=kh[1] - 0.24, h=1.05)
    xm = (klaunch['x'] + sg2['x']) / 2
    c.key(92, cut=True, cx=xm, cy=1.05, h=5.0, ease='smooth')
    c.key(104, cx=xm - 0.4, cy=1.05, h=4.4, ease='acc')
    c.key(118, cx=sup['x'] + 0.45, cy=1.1, h=3.4, ease='dec')
    c.key(140, cx=sup['x'] + 1.4, cy=1.0, h=5.0, ease='smooth')
    c.key(176, cx=(sup['x'] + land2['x']) / 2, cy=1.05, h=5.4, ease='smooth')
    c.key(198, cx=(sup['x'] + land2['x']) / 2, cy=1.05, h=5.3)
    # low close-up on KAI: he lifts his head toward SEN, and lets it fall (moon above him)
    kh2 = head_of(KAI, land2)
    c.key(199, cut=True, cx=kh2[0] - 0.35, cy=0.5, h=1.45, ease='lin')
    c.key(226, cx=kh2[0] - 0.3, cy=0.48, h=1.32)
    c.key(227, cut=True, cx=(sup['x'] + land2['x']) / 2, cy=1.1, h=5.5, ease='lin')
    c.key(250, cx=(sup['x'] + land2['x']) / 2 + 0.2, cy=1.15, h=5.8, ease='lin')
    c.key(300, cx=(sup['x'] + land2['x']) / 2 + 0.5, cy=1.3, h=6.8)

    # ================================================================ fx / sound
    def motes(fx, sc, rf, a):
        if a % 3 == 0:
            fx.dust(fx.rnd.uniform(-5, 9), fx.rnd.uniform(0.05, 1.6), n=1, dirx=-1, speed=1.2, size=0.03,
                    life=(30, 50), up=0.05, alpha=0.35)
    seq.emit(0, 336, motes)
    seq.at(16, lambda fx, sc, rf: (fx.dust(KR, n=8, dirx=1, speed=2.4, size=0.18, alpha=0.6),
                                   fx.dust(SR, n=8, dirx=-1, speed=2.4, size=0.18, alpha=0.6)))
    seq.sfx(16, 'dash')
    # the clash
    cpx = (hand(KAI, kfin, 'f')[0] + hand(SEN, sfin, 'n')[0]) / 2
    cpy = (hand(KAI, kfin, 'f')[1] + hand(SEN, sfin, 'n')[1]) / 2
    seq.impact(26, cpx, cpy, dirx=0, diry=1, power=1.6, stop=5, style=['focus', 'dark'], sound='clash')

    def clash(fx, sc, rf):
        fx.ring(cpx, cpy, 0.1, 2.0, life=10, w=0.08)
        fx.sparks(cpx, cpy, -1, 0.2, n=18, speed=10)
        fx.sparks(cpx, cpy, 1, 0.2, n=18, speed=10)
        fx.ring(cpx, 0.02, 0.1, 3.4, life=14, w=0.07, squash=0.16, col=(0.9, 0.85, 0.85))
        fx.dust(cpx, n=12, dirx=-1, speed=4.0, size=0.22, alpha=0.65, up=0.4)
        fx.dust(cpx, n=12, dirx=1, speed=4.0, size=0.22, alpha=0.65, up=0.4)
        fx.flash_screen(0.3, (1, 0.95, 0.9))
    seq.at(26, clash)

    def skids(fx, sc, rf, a):
        for act, b in ((k, KAI), (s, SEN)):
            p = act.eval(a)
            d = 1 if act is k else -1
            fx.dust(ankle(b, p, 'n')[0], n=1, dirx=d, speed=2.0, size=0.12, alpha=0.5, life=(10, 18))
    seq.emit(30, 42, skids)
    seq.sfx(30, 'skid')
    seq.at(42, lambda fx, sc, rf: (fx.skidmark(ankle(KAI, kskid, 'n')[0], ankle(KAI, kfin, 'n')[0] + 0.3),
                                   fx.skidmark(ankle(SEN, sskid, 'n')[0], ankle(SEN, sfin, 'n')[0] - 0.3)))

    def embers(fx, sc, rf, a):
        heat = 1.3 if a < 118 else max(0.0, 1.3 - (a - 118) / 30.0)
        if heat > 0.05:
            fx.embers(solve(KAI, k.eval(a)), n=3 if 76 <= a < 118 else 2, heat=heat)
    seq.emit(0, 160, embers)
    seq.glow['KAI'] = lambda a: 2.2 if a < 118 else (0.4 if a > 150 else 2.2 - 1.8 * (a - 118) / 32.0)
    seq.glow['SEN'] = lambda a: (-1.0 if 63 <= a < 73 else (2.0 if 73 <= a < 140 else 1.1))

    def sen_open(fx, sc, rf):
        from rig import eye_point
        e, _, _ = eye_point(solve(SEN, s.eval(73)))
        fx.glint(e[0], e[1], size=0.13, life=9, col=(0.75, 1.0, 1.0))
    seq.at(73, sen_open)
    seq.sfx(73, 'glint')
    seq.sfx(100, 'dash')
    seq.at(101, lambda fx, sc, rf: fx.dust(kr2, n=10, dirx=1, speed=2.6, size=0.2, alpha=0.6))
    seq.emit(100, 116, lambda fx, sc, rf, a: fx.speedlines(k.eval(a)['x'], 1.1, -1, n=2, length=1.6, spread=0.6))
    seq.sfx(114, 'whoosh_big')

    # the finish
    seq.impact(118, palm[0] + 0.06, palm[1] + 0.1, dirx=0.3, diry=1, power=2.0, stop=6, style=['white', 'dark'],
               sound='finish')

    def finish(fx, sc, rf):
        fx.ring(palm[0], palm[1] + 0.1, 0.1, 2.4, life=12, w=0.09)
        fx.ring(palm[0], palm[1] + 0.1, 0.05, 1.3, life=8, w=0.05)
        fx.sparks(palm[0], palm[1] + 0.1, 0.4, 1, n=30, speed=11, spread=0.7)
        fx.streak(palm[0], palm[1] + 0.1, length=3.5, life=6, w=0.04)
        fx.flash_screen(0.45, (1, 0.97, 0.92))
        fx.dust(sup['x'], n=10, dirx=-1, speed=2.5, size=0.2, alpha=0.6)
    seq.at(118, finish)
    seq.at(119, lambda fx, sc, rf: fx.speedlines(kce['x'] + 1.0, 1.4, 1, n=5, length=2.0, spread=0.7))

    def thud(fx, sc, rf):
        fx.dust(land['x'], n=12, dirx=1, speed=2.8, size=0.24, alpha=0.7, up=0.8)
        fx.dust(land['x'] + 0.6, n=8, dirx=-1, speed=1.8, size=0.2, alpha=0.6, up=0.6)
        sc.shake.add(rf, 0.06, frames=8, dx=0.3, dy=1.0, seed=140)
    seq.at(140, thud)
    seq.sfx(140, 'thud')
    seq.emit(147, 160, lambda fx, sc, rf, a: fx.dust(k.eval(a)['x'] - 0.3, n=1, dirx=1, speed=1.4, size=0.14,
                                                      alpha=0.45, life=(12, 20)))
    seq.sfx(147, 'skid')
    seq.at(160, lambda fx, sc, rf: fx.skidmark(land['x'] + 0.3, land2['x'] + 0.2, y=0.0, w=0.05))
    for f_ in range(266, 336, 12):
        seq.sfx(f_, 'step', 0.4)
    seq.sfx(232, 'breath', 0.5)

    seq.fade(280, 300, 0.0, 1.0)
    seq.fade(300, 336, 1.0, 1.0)
    seq.cards.append((302, 336, title_card('FURNACE  &  TIDE', 'an original stick-fight animation')))

    for f_, t_ in [(0, '4A coil'), (16, '4B charge'), (26, '4B CLASH'), (44, '4C beat'), (60, '4C CU SEN'),
                   (76, '4C CU KAI'), (92, '4D last charge'), (118, '4D FINISH'), (119, '4E launch'),
                   (176, '4F resolution'), (199, '4F CU KAI'), (227, '4F bow'), (254, '4F walk away'), (300, 'title')]:
        seq.note(f_, t_)
    seq.geometry = dict(clash_x=cpx, clash_y=cpy, sen_palm_an=s_an, kai_stride_scale=sk, sen_stride_scale=ss,
                        final_stride_scale=sk2, kai_lead_foot=ankle(KAI, kce, 'n')[0],
                        sen_front_foot=ankle(SEN, sup, 'n')[0], fist_over_sen_head_top=kfinal_fist[1] -
                        head_of(SEN, sup)[1] - SEN.head_r, sen_palm_an_final=best[1], kai_land=land2['x'])
    return seq


if __name__ == '__main__':
    for kk, v in build().geometry.items():
        print(f'{kk:22s} {v:7.2f}')
