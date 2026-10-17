"""Powers and set-piece effects for DOOM vs SPIDER-MAN.

Two kinds of effect:
  * overlays -- fn(ctx, seq, a, rf, px, ink) drawn by the renderer every frame
    from the *animation* frame, so anything that must meet a drawing on an exact
    frame (a bolt reaching its target, a web line pinned to a hand) stays locked
    to the timeline and freezes with the characters during hit-stops. Flicker
    uses the render frame rf, so energy keeps crackling through a freeze.
  * FX items / particles -- free-running debris, smoke, sparks and splashes
    spawned by the sequence script at chosen frames.
`ink` is the silhouette colour on impact frames (None otherwise): effects then
draw as flat ink with no glow.
"""
import math
import random

import cairo

from fx import Particle
from heroes import unit, sub, addv, lerp2, rot2, capsule_path, poly

TAU = 2 * math.pi
GREEN = (0.42, 1.0, 0.52)
GREEN_HOT = (0.86, 1.0, 0.86)
ELEC = (0.62, 0.84, 1.0)
ELEC_HOT = (0.93, 0.97, 1.0)
WEB = (0.93, 0.95, 1.0)
WATER = (0.62, 0.74, 0.92)
FIRE = [(1.0, 0.95, 0.75), (1.0, 0.72, 0.3), (1.0, 0.45, 0.15)]
GRIT = (0.40, 0.40, 0.48)          # roof dust: darker and cooler than the salt-flat dust


# ------------------------------------------------------------------ helpers
def glow(ctx, x, y, r, col, alpha, core=0.0):
    g = cairo.RadialGradient(x, y, r * core, x, y, r)
    g.add_color_stop_rgba(0, *col, alpha)
    g.add_color_stop_rgba(0.35, *col, alpha * 0.45)
    g.add_color_stop_rgba(1, *col, 0)
    ctx.set_source(g)
    ctx.arc(x, y, r, 0, TAU)
    ctx.fill()


def joint(seq, name, part):
    J = seq.actors[name].J
    return getattr(J, part)


def hand_tip(J, side, ahead=0.07):
    el = J.elbow_n if side == 'n' else J.elbow_f
    ha = J.hand_n if side == 'n' else J.hand_f
    return addv(ha, unit(sub(ha, el)), ahead)


def jag(p0, p1, rnd, amp=0.18, depth=5):
    """Midpoint-displacement lightning between two points."""
    pts = [p0, p1]
    a = amp * math.dist(p0, p1)
    for _ in range(depth):
        out = [pts[0]]
        for q0, q1 in zip(pts, pts[1:]):
            m = lerp2(q0, q1, 0.5)
            d = unit(sub(q1, q0))
            n = (-d[1], d[0])
            out.append(addv(m, n, rnd.uniform(-a, a)))
            out.append(q1)
        pts = out
        a *= 0.55
    return pts


def stroke_pts(ctx, pts, w, col, alpha=1.0):
    ctx.set_line_width(w)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    ctx.set_source_rgba(*col, alpha)
    ctx.move_to(*pts[0])
    for q in pts[1:]:
        ctx.line_to(*q)
    ctx.stroke()


def bolt_line(ctx, pts, px, col=ELEC, hot=ELEC_HOT, w=0.03, ink=None, alpha=1.0):
    if ink:
        stroke_pts(ctx, pts, max(w * 0.7, 1.5 * px), ink)
        return
    stroke_pts(ctx, pts, w * 4.0, col, 0.18 * alpha)
    stroke_pts(ctx, pts, w * 1.8, col, 0.55 * alpha)
    stroke_pts(ctx, pts, max(w * 0.6, 1.2 * px), hot, alpha)


# ------------------------------------------------------------------ mystic bolts
def bolt(p0, p1, f0, f1, col=GREEN, size=0.14, trail=2.2):
    """A bolt of green force: leaves p0 on f0, arrives at p1 on f1 (then gone)."""
    L = math.dist(p0, p1)
    d = unit(sub(p1, p0))
    n = (-d[1], d[0])

    def fn(ctx, seq, a, rf, px, ink):
        u = (a - f0) / max(1, f1 - f0)
        if u > 1.0:
            return
        head = lerp2(p0, p1, u)
        tl = min(trail, u * L + 0.05)
        tail = addv(head, d, -tl)
        rnd = random.Random(rf * 7 + int(f0))
        if ink:
            poly(ctx, [addv(head, n, size * 0.5), addv(tail, n, size * 0.1), addv(tail, n, -size * 0.1),
                       addv(head, n, -size * 0.5)])
            ctx.set_source_rgb(*ink)
            ctx.fill()
            return
        # outer glow streak, mid, white-hot core
        for wk, al, c in ((2.6, 0.16, col), (1.5, 0.35, col), (0.8, 0.85, col), (0.35, 1.0, GREEN_HOT)):
            g = cairo.LinearGradient(*tail, *head)
            g.add_color_stop_rgba(0, *c, 0)
            g.add_color_stop_rgba(1, *c, al)
            ctx.set_source(g)
            poly(ctx, [addv(head, n, size * wk * 0.5), addv(tail, n, size * wk * 0.08),
                       addv(tail, n, -size * wk * 0.08), addv(head, n, -size * wk * 0.5)])
            ctx.fill()
        glow(ctx, head[0], head[1], size * 4.0, col, 0.45)
        glow(ctx, head[0], head[1], size * 1.3, GREEN_HOT, 0.95)
        # crackling filaments around the head
        for _ in range(3):
            q = addv(addv(head, d, -rnd.uniform(0.0, tl * 0.6)), n, rnd.uniform(-size, size) * 1.4)
            bolt_line(ctx, jag(head, q, rnd, 0.3, 3), px, col, GREEN_HOT, w=0.008, alpha=0.8)
    return fn


def charge(name, side, size_fn, col=GREEN, hot=GREEN_HOT, ahead=0.1, arcs=True):
    """Energy gathering in a palm: a pulsing orb, motes spiralling in, crackles."""
    def fn(ctx, seq, a, rf, px, ink):
        s = size_fn(a)
        if s <= 0.005:
            return
        J = seq.actors[name].J
        c = hand_tip(J, side, ahead)
        rnd = random.Random(rf * 13 + (1 if side == 'n' else 2))
        if ink:
            ctx.set_source_rgb(*ink)
            ctx.arc(c[0], c[1], s * 0.55, 0, TAU)
            ctx.fill()
            return
        pulse = 1.0 + 0.12 * math.sin(rf * 1.9)
        glow(ctx, c[0], c[1], s * 4.0 * pulse, col, 0.32)
        glow(ctx, c[0], c[1], s * 1.6 * pulse, col, 0.75)
        glow(ctx, c[0], c[1], s * 0.75, hot, 1.0)
        for k in range(8):
            ang = rnd.uniform(0, TAU)
            r = s * rnd.uniform(1.6, 4.0)
            q = (c[0] + math.cos(ang) * r, c[1] + math.sin(ang) * r)
            q2 = lerp2(q, c, 0.35)
            stroke_pts(ctx, [q, q2], max(0.006, px), col, 0.7)
        if arcs and s > 0.04:
            for _ in range(2):
                ang = rnd.uniform(0, TAU)
                q = (c[0] + math.cos(ang) * s * 3.0, c[1] + math.sin(ang) * s * 3.0)
                bolt_line(ctx, jag(c, q, rnd, 0.35, 3), px, col, hot, w=0.01, alpha=0.9)
    return fn


# ------------------------------------------------------------------ electricity
def arc_between(pa, pb, inten_fn, col=ELEC, hot=ELEC_HOT, n=2, w=0.022, seed=0):
    """Crackling arcs between two (possibly moving) points: pa/pb are fn(seq, a) -> point."""
    def fn(ctx, seq, a, rf, px, ink):
        k = inten_fn(a)
        if k <= 0.02:
            return
        p0, p1 = pa(seq, a), pb(seq, a)
        rnd = random.Random(rf * 31 + seed)
        for _ in range(n):
            bolt_line(ctx, jag(p0, p1, rnd, 0.22, 5), px, col, hot, w=w * k, ink=ink, alpha=min(1.0, k))
    return fn


BODY_PAIRS = [('hand_n', 'elbow_n'), ('elbow_n', 'shoulder_n'), ('hand_f', 'elbow_f'), ('elbow_f', 'shoulder_f'),
              ('shoulder', 'hip'), ('hip', 'knee_n'), ('knee_n', 'ankle_n'), ('hip', 'knee_f'),
              ('knee_f', 'ankle_f'), ('head', 'chest'), ('hand_n', 'chest'), ('hand_f', 'hip'),
              ('ankle_n', 'ankle_f')]


def electrify(name, inten_fn, col=ELEC, hot=ELEC_HOT, seed=0, n=5, aura=True, ground=False):
    """Arcs crawling over a body (joint to joint), plus an aura. ground=True also
    sends arcs from the feet into the floor."""
    def fn(ctx, seq, a, rf, px, ink):
        k = inten_fn(a)
        if k <= 0.02:
            return
        J = seq.actors[name].J
        rnd = random.Random(rf * 17 + seed)
        if aura and not ink:
            for q in (J.chest, J.hip, J.head):
                glow(ctx, q[0], q[1], 0.55 * k, col, 0.22 * min(1.0, k))
        for _ in range(int(n * min(1.5, k) + 0.5)):
            a_, b_ = rnd.choice(BODY_PAIRS)
            p0 = addv(getattr(J, a_), (rnd.uniform(-0.05, 0.05), rnd.uniform(-0.05, 0.05)))
            p1 = addv(getattr(J, b_), (rnd.uniform(-0.05, 0.05), rnd.uniform(-0.05, 0.05)))
            bolt_line(ctx, jag(p0, p1, rnd, 0.35, 4), px, col, hot, w=0.016 * min(1.4, k), ink=ink,
                      alpha=min(1.0, k))
        if ground:
            for an in (J.ankle_n, J.ankle_f):
                q = (an[0] + rnd.uniform(-0.6, 0.6), 0.0)
                bolt_line(ctx, jag(an, q, rnd, 0.3, 4), px, col, hot, w=0.016 * min(1.4, k), ink=ink,
                          alpha=min(1.0, k))
    return fn


# ------------------------------------------------------------------ force field
def shield(name, inten_fn, hits=(), rx=1.2, ry=1.42, col=GREEN):
    """Doom's force field: a translucent hex-lattice dome; hits = [(frame, x, y)] ripple."""
    def fn(ctx, seq, a, rf, px, ink):
        k = inten_fn(a)
        if k <= 0.01:
            return
        J = seq.actors[name].J
        cx, cy = J.hip[0], J.hip[1] + 0.25
        if ink:
            ctx.set_source_rgb(*ink)
            ctx.set_line_width(max(0.02, 2 * px))
            ctx.save()
            ctx.translate(cx, cy)
            ctx.scale(rx * k, ry * k)
            ctx.arc(0, 0, 1, 0, TAU)
            ctx.restore()
            ctx.stroke()
            return
        ctx.save()
        ctx.translate(cx, cy)
        ctx.scale(rx * (0.6 + 0.4 * k), ry * (0.6 + 0.4 * k))
        g = cairo.RadialGradient(0, 0, 0.2, 0, 0, 1)
        g.add_color_stop_rgba(0, *col, 0.03 * k)
        g.add_color_stop_rgba(0.8, *col, 0.12 * k)
        g.add_color_stop_rgba(1, *col, 0.4 * k)
        ctx.set_source(g)
        ctx.arc(0, 0, 1, 0, TAU)
        ctx.fill_preserve()
        ctx.restore()
        ctx.save()
        ctx.clip()
        # hex lattice
        ctx.set_source_rgba(*col, 0.16 * k)
        ctx.set_line_width(max(0.006, px))
        s = 0.16
        for j in range(-12, 13):
            for i in range(-10, 11):
                hx = cx + i * s * 1.5
                hy = cy + j * s * math.sqrt(3) + (i % 2) * s * math.sqrt(3) / 2
                for m in range(6):
                    a0, a1 = m * TAU / 6, (m + 1) * TAU / 6
                    if m == 0:
                        ctx.move_to(hx + s * math.cos(a0), hy + s * math.sin(a0))
                    ctx.line_to(hx + s * math.cos(a1), hy + s * math.sin(a1))
        ctx.stroke()
        # impact ripples
        for hf, hx, hy in hits:
            if 0 <= a - hf < 10:
                t = (a - hf) / 10.0
                for rr, al in ((0.15 + 1.6 * t, 1.0), (0.05 + 1.0 * t, 0.6)):
                    ctx.set_source_rgba(*GREEN_HOT, al * (1 - t) * k)
                    ctx.set_line_width(0.05 * (1 - t) + px)
                    ctx.arc(hx, hy, rr, 0, TAU)
                    ctx.stroke()
                glow(ctx, hx, hy, 0.8 * (1 - t), GREEN_HOT, 0.6 * (1 - t))
        ctx.restore()
        # rim
        ctx.save()
        ctx.translate(cx, cy)
        ctx.scale(rx * (0.6 + 0.4 * k), ry * (0.6 + 0.4 * k))
        ctx.arc(0, 0, 1, 0, TAU)
        ctx.restore()
        ctx.set_source_rgba(*GREEN_HOT, 0.6 * k * (0.85 + 0.15 * math.sin(rf * 1.3)))
        ctx.set_line_width(max(0.012, 1.5 * px))
        ctx.stroke()
    return fn


# ------------------------------------------------------------------ webs
def web_strand(ctx, p0, p1, px, ink=None, alpha=1.0, wobble=0.0, rf=0):
    """A web line: a main strand plus a thinner twisting second strand."""
    if ink:
        stroke_pts(ctx, [p0, p1], max(0.012, 1.5 * px), ink)
        return
    L = math.dist(p0, p1)
    d = unit(sub(p1, p0))
    n = (-d[1], d[0])
    m = max(2, int(L / 0.08))
    pts, pts2 = [], []
    for i in range(m + 1):
        t = i / m
        q = lerp2(p0, p1, t)
        wv = wobble * math.sin(t * 9.0 + rf * 1.7) * math.sin(math.pi * t)
        pts.append(addv(q, n, wv))
        pts2.append(addv(q, n, wv + 0.012 * math.sin(t * L * 18)))
    stroke_pts(ctx, pts, max(0.016, 1.6 * px), WEB, 0.95 * alpha)
    stroke_pts(ctx, pts2, max(0.006, 0.9 * px), WEB, 0.55 * alpha)


def splat_shape(ctx, c, r, rnd, px, col=WEB, ink=None, alpha=1.0, up=(0, 1)):
    """A web splat: a lumpy blob with radiating strands and a ring of webbing."""
    colr = ink or col
    ctx.set_source_rgba(*colr, alpha)
    pts = []
    for k in range(12):
        ang = k * TAU / 12
        rr = r * rnd.uniform(0.35, 0.6)
        pts.append((c[0] + math.cos(ang) * rr, c[1] + math.sin(ang) * rr))
    poly(ctx, pts)
    ctx.fill()
    ctx.set_line_width(max(0.008, 1.0 * px))
    for k in range(9):
        ang = k * TAU / 9 + rnd.uniform(-0.2, 0.2)
        rr = r * rnd.uniform(0.9, 1.3)
        ctx.move_to(*c)
        ctx.line_to(c[0] + math.cos(ang) * rr, c[1] + math.sin(ang) * rr)
    ctx.stroke()
    ctx.set_line_width(max(0.005, 0.7 * px))
    ctx.arc(c[0], c[1], r * 0.8, 0, TAU)
    ctx.stroke()


def webline(src, dst, f0, f1, shoot=3, wobble=0.04):
    """A web line from src(seq, a) to dst (point or fn(seq, a)). It shoots out over
    `shoot` frames (arriving on f0 + shoot), then holds taut until f1."""
    def fn(ctx, seq, a, rf, px, ink):
        if not (f0 <= a < f1):
            return
        p0 = src(seq, a)
        p1 = dst(seq, a) if callable(dst) else dst
        u = min(1.0, (a - f0 + 1) / float(shoot))
        tip = lerp2(p0, p1, u)
        web_strand(ctx, p0, tip, px, ink, wobble=wobble * (1 - u) * 3 + 0.004, rf=rf)
        rnd = random.Random(int(f0 * 7 + p1[0] * 100))
        if u >= 1.0:
            splat_shape(ctx, p1, 0.07, rnd, px, ink=ink)
        else:
            splat_shape(ctx, tip, 0.04, rnd, px, ink=ink)
    return fn


def webball(p0, p1, f0, f1, r=0.07):
    """A web ball in flight from p0 (f0) to p1 (f1), trailing strands."""
    d = unit(sub(p1, p0))

    def fn(ctx, seq, a, rf, px, ink):
        u = (a - f0) / max(1, f1 - f0)
        if u > 1.0 or u < 0:
            return
        c = lerp2(p0, p1, u)
        rnd = random.Random(int(f0) * 3 + 1)
        tail = addv(c, d, -min(0.9, u * math.dist(p0, p1)))
        web_strand(ctx, tail, c, px, ink, alpha=0.6)
        splat_shape(ctx, c, r, rnd, px, ink=ink)
    return fn


def splat_at(pos, f0, f1, r=0.09, seed=0, slide=0.0, fade=0):
    """A web splat stuck at pos (point or fn(seq, a)); slides down `slide` m over its life."""
    def fn(ctx, seq, a, rf, px, ink):
        if not (f0 <= a < f1):
            return
        c = pos(seq, a) if callable(pos) else pos
        t = (a - f0) / max(1, f1 - f0)
        c = (c[0], c[1] - slide * t * t)
        al = 1.0 if not fade else min(1.0, (f1 - a) / fade)
        splat_shape(ctx, c, r * min(1.0, 0.5 + (a - f0) * 0.25), random.Random(seed), px, ink=ink, alpha=al)
    return fn


def web_glob(name, side, f0, f1, r=0.12, seed=0, glow_fn=None):
    """Webbing gumming up a hand: a lumpy white glob that follows it. glow_fn(a)
    makes trapped energy shine through (0..1)."""
    def fn(ctx, seq, a, rf, px, ink):
        if not (f0 <= a < f1):
            return
        J = seq.actors[name].J
        c = hand_tip(J, side, 0.02)
        rnd = random.Random(seed)
        grow = min(1.0, 0.45 + (a - f0) * 0.3)
        if ink:
            ctx.set_source_rgb(*ink)
            ctx.arc(c[0], c[1], r * grow, 0, TAU)
            ctx.fill()
            return
        k = glow_fn(a) if glow_fn else 0.0
        if k > 0:
            glow(ctx, c[0], c[1], r * (2.0 + 2.5 * k), GREEN, 0.5 * k)
        ctx.set_source_rgb(*[w * (1 - 0.15 * k) + g * 0.15 * k for w, g in zip(WEB, GREEN_HOT)])
        pts = []
        for i in range(14):
            ang = i * TAU / 14
            rr = r * grow * rnd.uniform(0.75, 1.1)
            pts.append((c[0] + math.cos(ang) * rr, c[1] + math.sin(ang) * rr))
        poly(ctx, pts)
        ctx.fill()
        ctx.set_source_rgba(0.55, 0.6, 0.7, 0.5)
        ctx.set_line_width(max(0.004, 0.7 * px))
        for i in range(6):
            ang = rnd.uniform(0, TAU)
            ctx.move_to(c[0] + math.cos(ang) * r * 0.9 * grow, c[1] + math.sin(ang) * r * 0.9 * grow)
            ctx.line_to(c[0] + math.cos(ang + 2.4) * r * 0.9 * grow, c[1] + math.sin(ang + 2.4) * r * 0.9 * grow)
        ctx.stroke()
        if k > 0.3:
            # light leaking through cracks in the webbing
            for i in range(int(3 + 5 * k)):
                ang = rnd.uniform(0, TAU) + rf * 0.05
                q = (c[0] + math.cos(ang) * r * 1.0, c[1] + math.sin(ang) * r * 1.0)
                q2 = (c[0] + math.cos(ang) * r * (1.4 + k), c[1] + math.sin(ang) * r * (1.4 + k))
                stroke_pts(ctx, [q, q2], max(0.01, 1.5 * px) * (0.5 + k), GREEN_HOT, 0.85)
    return fn


# ------------------------------------------------------------------ rocket boots
def jets(name, inten_fn, sputter=None):
    """Flames from DOOM's boot soles, along the shin. sputter(a) in 0..1 makes them
    cough and gutter (damaged armour)."""
    def fn(ctx, seq, a, rf, px, ink):
        k = inten_fn(a)
        if k <= 0.02:
            return
        J = seq.actors[name].J
        rnd = random.Random(rf * 5 + 3)
        sp = sputter(a) if sputter else 0.0
        for kn, an, toe in ((J.knee_f, J.ankle_f, J.toe_f), (J.knee_n, J.ankle_n, J.toe_n)):
            if sp > 0 and rnd.random() < sp * 0.7:
                continue
            d = unit(sub(an, kn))
            base = addv(lerp2(an, toe, 0.25), d, 0.03)
            n = (-d[1], d[0])
            L = (0.45 + 0.25 * rnd.random()) * k * (1 - 0.5 * sp * rnd.random())
            w = 0.075 * (0.7 + 0.3 * k)
            tip = addv(base, d, L)
            if ink:
                poly(ctx, [addv(base, n, w), tip, addv(base, n, -w)])
                ctx.set_source_rgb(*ink)
                ctx.fill()
                continue
            glow(ctx, base[0], base[1], 0.55 * k, FIRE[1], 0.35)
            for wk, lk, col, al in ((1.0, 1.0, FIRE[2], 0.75), (0.7, 0.75, FIRE[1], 0.9),
                                    (0.4, 0.45, FIRE[0], 1.0)):
                t = addv(base, d, L * lk)
                ctx.set_source_rgba(*col, al)
                ctx.move_to(*addv(base, n, w * wk))
                ctx.curve_to(*addv(addv(base, d, L * lk * 0.4), n, w * wk * 1.1), *addv(t, n, w * wk * 0.2), *t)
                ctx.curve_to(*addv(t, n, -w * wk * 0.2), *addv(addv(base, d, L * lk * 0.4), n, -w * wk * 1.1),
                             *addv(base, n, -w * wk))
                ctx.close_path()
                ctx.fill()
            # shock diamonds
            for m in range(2):
                q = addv(base, d, L * (0.25 + 0.2 * m))
                glow(ctx, q[0], q[1], w * 0.6, (1, 1, 0.95), 0.7)
    return fn


# ------------------------------------------------------------------ water
def stream(hole, f0, v0=2.6, ramp=8, end=None):
    """Water gushing from the tank: a ribbon along a ballistic arc (leftward)."""
    g = 9.8

    def path(T, wob):
        pts = []
        for i in range(25):
            t = T * i / 24.0
            pts.append((hole[0] - v0 * t + wob * math.sin(i * 0.7), hole[1] - 0.5 * g * t * t))
        return pts
    T = math.sqrt(2 * hole[1] / g)

    def fn(ctx, seq, a, rf, px, ink):
        if a < f0 or (end is not None and a >= end):
            return
        k = min(1.0, (a - f0 + 1) / float(ramp))
        Tk = T * k
        wob = 0.015 * math.sin(rf * 0.9)
        pts = path(Tk, wob)
        if ink:
            stroke_pts(ctx, pts, 0.1, ink)
            return
        for w, col, al in ((0.2, WATER, 0.25), (0.12, WATER, 0.6), (0.05, (0.9, 0.95, 1.0), 0.7)):
            stroke_pts(ctx, pts, w * (0.6 + 0.4 * k), col, al)
        # broken strands at the edges
        rnd = random.Random(rf)
        for i in range(6):
            t = rnd.uniform(0.2, 1.0) * Tk
            x = hole[0] - v0 * t
            y = hole[1] - 0.5 * g * t * t
            stroke_pts(ctx, [(x, y), (x - 0.05, y - 0.18)], max(0.008, px), (0.85, 0.92, 1.0), 0.6)
    return fn, (hole[0] - v0 * T)


def puddle(cx_fn, half_fn, elec_fn=None, glow_fn=None):
    """The puddle under the leak: a flattened sheen whose half-width grows with time;
    elec_fn(a) lights it with crawling arcs (electrified water); glow_fn(a) -> (x, k)
    reflects green energy held above it."""
    def fn(ctx, seq, a, rf, px, ink):
        hw = half_fn(a)
        if hw <= 0.02 or ink:
            return
        cx = cx_fn(a)
        ctx.save()
        ctx.translate(cx, 0.0)
        ctx.scale(hw, 0.12)
        g = cairo.RadialGradient(0, 0, 0, 0, 0, 1)
        g.add_color_stop_rgba(0, 0.55, 0.62, 0.82, 0.42)
        g.add_color_stop_rgba(0.8, 0.45, 0.52, 0.72, 0.30)
        g.add_color_stop_rgba(1, 0.4, 0.45, 0.6, 0.0)
        ctx.set_source(g)
        ctx.arc(0, 0, 1, 0, TAU)
        ctx.fill()
        ctx.restore()
        # moon/sky reflections: soft horizontal glints
        rnd = random.Random(5)
        for i in range(7):
            x = cx + rnd.uniform(-0.75, 0.75) * hw
            y = rnd.uniform(-0.05, 0.05)
            L = rnd.uniform(0.1, 0.35) * min(1.0, hw)
            al = 0.25 + 0.15 * math.sin(rf * 0.3 + i)
            stroke_pts(ctx, [(x - L, y), (x + L, y)], max(0.008, px), (0.85, 0.9, 1.0), al)
        if glow_fn:
            gx, gk = glow_fn(a)
            if gk > 0.02:
                ctx.save()
                ctx.translate(gx, 0.0)
                ctx.scale(min(hw, 1.4), 0.1)
                g = cairo.RadialGradient(0, 0, 0, 0, 0, 1)
                g.add_color_stop_rgba(0, *GREEN, 0.45 * gk * (0.85 + 0.15 * math.sin(rf * 1.7)))
                g.add_color_stop_rgba(1, *GREEN, 0.0)
                ctx.set_source(g)
                ctx.arc(0, 0, 1, 0, TAU)
                ctx.fill()
                ctx.restore()
        k = elec_fn(a) if elec_fn else 0.0
        if k > 0.02:
            rr = random.Random(rf * 11)
            ctx.save()
            ctx.translate(cx, 0.0)
            ctx.scale(hw, 0.12)
            g = cairo.RadialGradient(0, 0, 0, 0, 0, 1)
            g.add_color_stop_rgba(0, *ELEC, 0.6 * k)
            g.add_color_stop_rgba(1, *ELEC, 0.0)
            ctx.set_source(g)
            ctx.arc(0, 0, 1, 0, TAU)
            ctx.fill()
            ctx.restore()
            for _ in range(int(3 + 6 * k)):
                x0 = cx + rr.uniform(-0.9, 0.9) * hw
                x1 = x0 + rr.uniform(-0.8, 0.8)
                y0, y1 = rr.uniform(-0.08, 0.08), rr.uniform(-0.08, 0.08)
                bolt_line(ctx, jag((x0, y0), (x1, y1), rr, 0.25, 4), px, w=0.012 * min(1.5, k),
                          alpha=min(1.0, k))
    return fn


def splash(fx, x, y=0.02, n=10, speed=2.6, up=3.2, col=(0.8, 0.88, 1.0)):
    R = fx.rnd
    for _ in range(n):
        a = R.uniform(0.25, math.pi - 0.25)
        s = speed * R.uniform(0.4, 1.0)
        fx.ps.append(Particle('spark', x + R.uniform(-0.08, 0.08), y, math.cos(a) * s,
                              math.sin(a) * s * up / speed, life=R.randint(6, 12), col=col, g=1.0, drag=0.97,
                              w=R.uniform(0.012, 0.022)))
    fx.ring(x, 0.02, 0.05, 0.35, life=8, w=0.02, squash=0.18, col=col, alpha=0.6)


# ------------------------------------------------------------------ sparks / smoke
def sparks(fx, x, y, dirx, diry, n=14, speed=8.0, spread=0.9, cols=(ELEC_HOT, ELEC, (1, 1, 1)), life=(4, 9),
           g=3.0):
    R = fx.rnd
    base = math.atan2(diry, dirx)
    for _ in range(n):
        a = base + R.gauss(0, spread)
        s = speed * R.uniform(0.35, 1.0)
        fx.ps.append(Particle('spark', x, y, math.cos(a) * s, math.sin(a) * s, life=R.randint(*life),
                              col=R.choice(cols), g=g / 9.8 * 4, drag=0.86, w=R.uniform(0.01, 0.022)))


class Smoke:
    """Puffs that rise, swell and thin out (smoke from scorched armour, steam)."""

    def __init__(self, x, y, n=6, col=(0.32, 0.32, 0.36), size=0.12, rise=0.9, life=(24, 40), spread=0.12,
                 seed=1, drift=0.0, alpha=0.45, delay=0):
        R = random.Random(seed)
        self.p = []
        for _ in range(n):
            self.p.append([x + R.uniform(-spread, spread), y + R.uniform(-spread, spread) * 0.5,
                           R.uniform(-0.25, 0.25) + drift, rise * R.uniform(0.5, 1.0), 0, R.randint(*life),
                           size * R.uniform(0.6, 1.1)])
        self.col = col
        self.alpha = alpha
        self.delay = delay

    def step(self):
        if self.delay > 0:
            self.delay -= 1
            return True
        dt = 1.0 / 24
        for q in self.p:
            q[0] += q[2] * dt
            q[1] += q[3] * dt
            q[3] *= 0.97
            q[4] += 1
        self.p = [q for q in self.p if q[4] < q[5]]
        return bool(self.p)

    def draw(self, ctx, px):
        if self.delay > 0:
            return
        for x, y, vx, vy, age, life, s in self.p:
            t = age / life
            r = s * (1 + 2.2 * t)
            al = self.alpha * math.sin(math.pi * min(1.0, t * 1.2 + 0.05)) * (1 - t)
            g = cairo.RadialGradient(x, y, 0, x, y, r)
            g.add_color_stop_rgba(0, *self.col, al)
            g.add_color_stop_rgba(1, *self.col, 0)
            ctx.set_source(g)
            ctx.arc(x, y, r, 0, TAU)
            ctx.fill()


class Fireball:
    """An expanding ball of light that cools as it grows (the body of an explosion)."""

    def __init__(self, x, y, r=0.6, life=10, col=GREEN, hot=GREEN_HOT):
        self.x, self.y, self.r, self.life, self.col, self.hot = x, y, r, life, col, hot
        self.age = 0

    def step(self):
        self.age += 1
        return self.age < self.life

    def draw(self, ctx, px):
        t = self.age / float(self.life)
        r = self.r * (0.45 + 0.75 * (1 - (1 - t) ** 2))
        glow(ctx, self.x, self.y + 0.25 * self.r * t, r * 1.8, self.col, 0.45 * (1 - t))
        glow(ctx, self.x, self.y + 0.25 * self.r * t, r, self.hot, 0.9 * (1 - t) ** 1.5, core=0.2)


def explosion(fx, x, y, power=1.0, col=GREEN, smoke=True, seed=0):
    """A green force explosion: fireball, flash, ring, sparks, smoke."""
    fx.add(Fireball(x, y, r=0.55 * power, life=int(9 + 3 * power), col=col))
    fx.burst(x, y, size=0.35 * power, life=4, col=GREEN_HOT)
    fx.ring(x, y, 0.08, 1.1 * power, life=9, w=0.05 * power, col=col, alpha=0.9)
    sparks(fx, x, y, 0, 1, n=int(20 * power), speed=7 * power, spread=1.6, cols=(GREEN_HOT, col, (1, 1, 1)))
    if smoke:
        fx.add(Smoke(x, y + 0.15 * power, n=int(8 * power), size=0.18 * power, rise=1.2, seed=seed,
                     col=(0.30, 0.34, 0.32), alpha=0.35, delay=6))


# ------------------------------------------------------------------ spider-sense
def spider_sense(name, inten_fn):
    """The classic warning: wavy strokes radiating from the head."""
    def fn(ctx, seq, a, rf, px, ink):
        k = inten_fn(a)
        if k <= 0.02 or ink:
            return
        J = seq.actors[name].J
        c = J.head
        r = J.build.head_r
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        for i in range(9):
            ang = math.pi / 2 + (i - 4) * 0.36 + (0.04 * math.sin(rf * 2.1 + i))
            r0 = r * (1.45 + 0.1 * math.sin(rf * 1.7 + i * 2))
            L = r * (0.9 + 0.5 * k)
            pts = []
            for m in range(9):
                t = m / 8.0
                rr = r0 + L * t
                wv = 0.08 * r * math.sin(t * 10 + rf * 2.5)
                pts.append((c[0] + math.cos(ang) * rr - math.sin(ang) * wv,
                            c[1] + math.sin(ang) * rr + math.cos(ang) * wv))
            stroke_pts(ctx, pts, max(0.012, 1.4 * px) * (0.6 + 0.6 * k), (0.95, 0.95, 1.0), 0.9 * min(1.0, k))
    return fn


# ------------------------------------------------------------------ scorch marks
def scorch(x, f0, w=0.9, seed=0):
    """A scorch mark on the roof (persistent from f0)."""
    def fn(ctx, seq, a, rf, px, ink):
        if a < f0 or ink:
            return
        ctx.save()
        ctx.translate(x, 0.0)
        ctx.scale(w, 0.09)
        g = cairo.RadialGradient(0, 0, 0, 0, 0, 1)
        g.add_color_stop_rgba(0, 0.02, 0.03, 0.02, 0.85)
        g.add_color_stop_rgba(0.7, 0.05, 0.06, 0.05, 0.5)
        g.add_color_stop_rgba(1, 0, 0, 0, 0)
        ctx.set_source(g)
        ctx.arc(0, 0, 1, 0, TAU)
        ctx.fill()
        ctx.restore()
        t = a - f0
        if t < 60:
            rnd = random.Random(seed + rf)
            for _ in range(3):
                q = (x + rnd.uniform(-0.4, 0.4) * w, 0.02)
                glow(ctx, q[0], q[1], 0.12 * (1 - t / 60), GREEN, 0.5)
    return fn
