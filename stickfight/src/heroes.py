"""DOOM vs SPIDER-MAN: the two costumed builds.

Same skeleton, kinematics and pose conventions as rig.py; what changes is the
drawing. Each build carries a *painter* that dresses the solved joints:
two-tone limb bands cut square across the limb, a clipped torso panel, a
sphere-mapped head (mask features are decals on a unit sphere, projected with
a fixed 3/4 "cheat" so the face reads even in profile) and, for DOOM, a
simulated cape driven by the engine's Verlet chain.

Every painter honours the rig's styles: 'normal' (full costume), 'flat' (one
colour: afterimages) and 'silhouette' (impact frames).
"""
import math

import cairo

from rig import Build, hexrgb, udir, DEG
from engine import Chain

TAU = 2 * math.pi


# ------------------------------------------------------------------ palette
def shade(c, k):
    return tuple(max(0.0, min(1.0, v * k)) for v in c)


def mixc(a, b, t):
    return tuple(x + (y - x) * t for x, y in zip(a, b))


SP_RED = hexrgb('#D3232C')
SP_BLUE = hexrgb('#2150B8')
SP_WEB = hexrgb('#3B0710')
SP_LENS = hexrgb('#F3F6FF')
SP_INK = hexrgb('#0B0B12')

DM_STEEL = hexrgb('#A6AFBA')
DM_STEEL_DK = hexrgb('#555D68')
DM_GREEN = hexrgb('#2F7A3C')
DM_HOOD = hexrgb('#2B6E36')
DM_CAPE = hexrgb('#235A2C')
DM_LINING = hexrgb('#163B1C')
DM_BELT = hexrgb('#4A3823')
DM_GOLD = hexrgb('#D9B24A')
DM_EYE = hexrgb('#9CFFAE')
DM_SLIT = hexrgb('#0A120C')


# ------------------------------------------------------------------ geometry
def unit(v):
    L = math.hypot(v[0], v[1]) or 1.0
    return (v[0] / L, v[1] / L)


def sub(a, b):
    return (a[0] - b[0], a[1] - b[1])


def addv(a, b, s=1.0):
    return (a[0] + b[0] * s, a[1] + b[1] * s)


def lerp2(a, b, t):
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


def rot2(v, ang):
    c, s = math.cos(ang), math.sin(ang)
    return (v[0] * c - v[1] * s, v[0] * s + v[1] * c)


def capsule_path(ctx, a, b, wa, wb):
    """Closed outline of a tapered capsule (path only)."""
    dx, dy = b[0] - a[0], b[1] - a[1]
    ctx.new_sub_path()
    if math.hypot(dx, dy) < 1e-6:
        ctx.arc(a[0], a[1], max(wa, wb) / 2, 0, TAU)
        ctx.close_path()
        return
    ang = math.atan2(dy, dx)
    ctx.arc(b[0], b[1], wb / 2, ang - math.pi / 2, ang + math.pi / 2)
    ctx.arc(a[0], a[1], wa / 2, ang + math.pi / 2, ang + 3 * math.pi / 2)
    ctx.close_path()


def fill_capsule(ctx, a, b, wa, wb, col):
    ctx.set_source_rgb(*col)
    capsule_path(ctx, a, b, wa, wb)
    ctx.fill()


def axis_quad(a, b, s0, s1, half):
    """Rectangle along the axis a->b from distance s0 to s1, +-half wide."""
    d = unit(sub(b, a))
    n = (-d[1], d[0])
    p0, p1 = addv(a, d, s0), addv(a, d, s1)
    return [addv(p0, n, half), addv(p1, n, half), addv(p1, n, -half), addv(p0, n, -half)]


def poly(ctx, pts):
    ctx.move_to(*pts[0])
    for q in pts[1:]:
        ctx.line_to(*q)
    ctx.close_path()


def band(ctx, a, b, wa, wb, t0, t1, col, detail=None):
    """Fill the part of capsule a-b between axis fractions t0..t1, cut square.
    t0 <= 0 / t1 >= 1 include the round end caps. detail(ctx) runs inside the clip."""
    L = math.dist(a, b)
    W = max(wa, wb) * 1.5
    s0 = t0 * L if t0 > 0 else -W
    s1 = t1 * L if t1 < 1 else L + W
    ctx.save()
    capsule_path(ctx, a, b, wa, wb)
    ctx.clip()
    ctx.set_source_rgb(*col)
    poly(ctx, axis_quad(a, b, s0, s1, W))
    ctx.fill()
    if detail:
        poly(ctx, axis_quad(a, b, s0, s1, W))
        ctx.clip()
        detail(ctx)
    ctx.restore()


def limb_web(ctx, a, b, t0, t1, w, px, col=SP_WEB, spacing=0.05, alpha=0.5):
    """Spider webbing on a limb segment: a seam down the middle, curved rungs across."""
    L = math.dist(a, b)
    d = unit(sub(b, a))
    n = (-d[1], d[0])
    lw = max(0.0035, 0.8 * px)
    ctx.set_line_width(lw)
    ctx.set_source_rgba(*col, alpha)
    s0, s1 = max(0.0, t0) * L - w, min(1.0, t1) * L + w
    ctx.move_to(*addv(a, d, s0))
    ctx.line_to(*addv(a, d, s1))
    ctx.stroke()
    s = s0 + spacing * 0.5
    while s < s1:
        c = addv(a, d, s)
        ctx.move_to(*addv(c, n, w))
        ctx.curve_to(*addv(addv(c, n, w * 0.4), d, spacing * 0.22),
                     *addv(addv(c, n, -w * 0.4), d, spacing * 0.22),
                     *addv(c, n, -w))
        ctx.stroke()
        s += spacing


# ------------------------------------------------------------------ torso frame
class Torso:
    """The torso as a strip around the solved spine curve: (s along, n across)."""

    def __init__(self, J, wh, wc):
        self.pts = J.spine
        self.f = J.face
        self.wh, self.wc = wh, wc
        n = len(self.pts)
        self.left = []
        for i, p in enumerate(self.pts):
            a = self.pts[max(i - 1, 0)]
            b = self.pts[min(i + 1, n - 1)]
            d = unit(sub(b, a))
            self.left.append((-d[1], d[0]))

    def at(self, s, nn):
        """World point at spine fraction s (may exceed 0..1) and across-fraction nn
        (+1 = front edge, -1 = back edge)."""
        m = len(self.pts) - 1
        x = max(0.0, min(1.0, s)) * m
        i = min(int(x), m - 1)
        t = x - i
        p = lerp2(self.pts[i], self.pts[i + 1], t)
        lv = unit(lerp2(self.left[i], self.left[i + 1], t))
        if s > 1.0:
            p = addv(p, unit(sub(self.pts[-1], self.pts[-2])), (s - 1.0) * math.dist(self.pts[0], self.pts[-1]))
        elif s < 0.0:
            p = addv(p, unit(sub(self.pts[0], self.pts[1])), -s * math.dist(self.pts[0], self.pts[-1]))
        w = (self.wh + (self.wc - self.wh) * max(0.0, min(1.0, s))) / 2
        front = (-self.f * lv[0], -self.f * lv[1])
        return addv(p, front, nn * w)

    def direction(self, s=0.9):
        i = max(1, min(len(self.pts) - 1, int(round(s * (len(self.pts) - 1)))))
        return unit(sub(self.pts[i], self.pts[i - 1]))

    def front(self, s=0.9):
        d = self.direction(s)
        return (self.f * d[1], -self.f * d[0])

    def path(self, ctx):
        n = len(self.pts)
        ws = [(self.wh + (self.wc - self.wh) * i / (n - 1)) / 2 for i in range(n)]
        L = [addv(p, l, w) for p, l, w in zip(self.pts, self.left, ws)]
        R = [addv(p, l, -w) for p, l, w in zip(self.pts, self.left, ws)]
        ctx.new_sub_path()
        ctx.move_to(*L[0])
        for q in L[1:]:
            ctx.line_to(*q)
        # rounded top cap
        c, l, w = self.pts[-1], self.left[-1], ws[-1]
        a0 = math.atan2(l[1], l[0])
        for k in range(1, 12):
            a = a0 - math.pi * k / 12
            ctx.line_to(c[0] + math.cos(a) * w, c[1] + math.sin(a) * w)
        for q in reversed(R):
            ctx.line_to(*q)
        c, l, w = self.pts[0], self.left[0], ws[0]
        a0 = math.atan2(-l[1], -l[0])
        for k in range(1, 12):
            a = a0 - math.pi * k / 12
            ctx.line_to(c[0] + math.cos(a) * w, c[1] + math.sin(a) * w)
        ctx.close_path()

    def region(self, ctx, s0, s1, n0, n1, steps=8):
        """Path of the (s, n) rectangle mapped onto the torso (for panels)."""
        pts = [self.at(s0 + (s1 - s0) * i / steps, n0) for i in range(steps + 1)]
        pts += [self.at(s1 - (s1 - s0) * i / steps, n1) for i in range(steps + 1)]
        poly(ctx, pts)


# ------------------------------------------------------------------ the head
class Head:
    """Sphere projection for mask features. (u, v, w) = forward, up, lateral on a
    unit sphere; `cheat` turns the face toward camera on top of the body's yaw."""

    def __init__(self, J, cheat, scale=1.0):
        self.c = J.head
        self.r = J.build.head_r * scale
        f = J.face
        cr, sr = J.rotm
        a = J.head_ang - J.pose['rot']

        def W(v):
            x = f * v[0]
            return (x * cr - v[1] * sr, x * sr + v[1] * cr)
        self.U = W(udir(a, 1))
        self.F = W(udir(a + 90, 1))
        # the cheat fades out as the body itself turns to face the camera
        y = J.yaw + cheat * DEG * (1.0 - min(1.0, max(0.0, J.yaw) / (math.pi / 2)))
        self.cy, self.sy = math.cos(y), math.sin(y)

    def cam(self, u, v, w):
        """(in-plane x, up, depth toward camera)"""
        return u * self.cy - w * self.sy, v, u * self.sy + w * self.cy

    def screen(self, x, v, k=1.0):
        return (self.c[0] + self.r * k * (x * self.F[0] + v * self.U[0]),
                self.c[1] + self.r * k * (x * self.F[1] + v * self.U[1]))

    def pt(self, u, v, w, clamp=True):
        x, v2, d = self.cam(u, v, w)
        if clamp and d < 0:
            L = math.hypot(x, v2) or 1.0
            x, v2 = x / L, v2 / L
        return self.screen(x, v2), d

    def decal(self, a, b, clamp=True):
        """Frontal decal coordinates (a lateral, b up) wrapped onto the front of the sphere."""
        q = 1.0 - a * a - b * b
        u = math.sqrt(max(q, 0.0))
        if q < 0:
            L = math.hypot(a, b)
            a, b = a / L, b / L
        return self.pt(u, b, a, clamp)

    def depth_of(self, a, b):
        q = 1.0 - a * a - b * b
        return self.cam(math.sqrt(max(q, 0.0)), b, a)[2]

    def facing(self):
        """How much the face points at the camera (0 = profile .. 1 = frontal)."""
        return self.sy


def smooth_closed(pts, n=6):
    """Catmull-Rom resample of a closed polygon."""
    out = []
    m = len(pts)
    for i in range(m):
        p0, p1, p2, p3 = pts[i - 1], pts[i], pts[(i + 1) % m], pts[(i + 2) % m]
        for k in range(n):
            t = k / n
            t2, t3 = t * t, t * t * t
            out.append(tuple(0.5 * ((2 * p1[j]) + (-p0[j] + p2[j]) * t + (2 * p0[j] - 5 * p1[j] + 4 * p2[j] - p3[j]) * t2
                                    + (-p0[j] + 3 * p1[j] - 3 * p2[j] + p3[j]) * t3) for j in range(2)))
    return out


def head_shadow(ctx, H, col, alpha=0.25):
    """Terminator shading on the back of a sphere head."""
    g = cairo.RadialGradient(*H.screen(0.35, 0.3), H.r * 0.2, *H.screen(0.2, 0.15), H.r * 1.15)
    g.add_color_stop_rgba(0, *col, 0)
    g.add_color_stop_rgba(0.75, *col, 0)
    g.add_color_stop_rgba(1, *col, alpha)
    ctx.set_source(g)
    ctx.arc(H.c[0], H.c[1], H.r, 0, TAU)
    ctx.fill()


# ------------------------------------------------------------------ hands
def hand_dir(J, side):
    el = J.elbow_n if side == 'n' else J.elbow_f
    ha = J.hand_n if side == 'n' else J.hand_f
    return ha, unit(sub(ha, el))


def draw_hand(ctx, J, side, shape, col, r, detail=True):
    """fist | open (palm out, wrist cocked) | blade | thwip (web-shooter sign) | claw (grip)."""
    ha, d = hand_dir(J, side)
    f = J.face
    ctx.set_source_rgb(*col)
    if shape == 'fist':
        c = addv(ha, d, r * 0.35)
        ctx.arc(c[0], c[1], r, 0, TAU)
        ctx.fill()
        return c
    # bend direction: +angle toward the facing side, as rig.draw_arm
    def bent(deg):
        theta = math.atan2(f * d[0], -d[1]) + deg * DEG
        return (f * math.sin(theta), -math.cos(theta))
    if shape == 'blade':
        tip = addv(ha, d, r * 2.6)
        capsule_path(ctx, ha, tip, r * 1.3, r * 0.8)
        ctx.fill()
        return tip
    if shape == 'open':
        h = bent(35)
        tip = addv(ha, h, r * 1.9)
        capsule_path(ctx, ha, tip, r * 1.35, r * 0.85)
        ctx.fill()
        return tip
    if shape == 'thwip':
        h = bent(70)
        palm = addv(ha, h, r * 1.05)
        capsule_path(ctx, ha, palm, r * 1.3, r * 1.15)
        ctx.fill()
        if detail:
            # index and little finger out, middle two folded onto the palm: the web-shooter sign
            for da, L in ((-14, 1.15), (16, 0.95)):
                fd = rot2(h, f * da * DEG)
                capsule_path(ctx, palm, addv(palm, fd, r * L), r * 0.42, r * 0.32)
                ctx.fill()
            th = rot2(h, -f * 70 * DEG)
            capsule_path(ctx, addv(ha, h, r * 0.4), addv(addv(ha, h, r * 0.4), th, r * 0.8), r * 0.42, r * 0.32)
            ctx.fill()
        return palm
    if shape == 'claw':
        h = bent(20)
        palm = addv(ha, h, r * 0.9)
        capsule_path(ctx, ha, palm, r * 1.3, r * 1.2)
        ctx.fill()
        for da in (-35, 0, 35):
            fd = rot2(h, f * da * DEG + f * 40 * DEG)
            capsule_path(ctx, palm, addv(palm, fd, r * 0.75), r * 0.42, r * 0.34)
            ctx.fill()
        return palm
    c = addv(ha, d, r * 0.35)
    ctx.arc(c[0], c[1], r, 0, TAU)
    ctx.fill()
    return c


def palette(style, near, normal, flat_keys):
    """Return colours: in flat/silhouette styles everything is one colour."""
    if style == 'normal':
        return normal
    return {k: near for k in flat_keys}


def px_of(ctx):
    """World size of one device pixel under the current transform."""
    x, y = ctx.device_to_user_distance(1.0, 0.0)
    return math.hypot(x, y)


# ================================================================== SPIDER-MAN
def paint_spider(ctx, J, style='normal', chains=None, near=None, far=None, eye_glow=1.0):
    b = J.build
    p = J.pose
    normal = style == 'normal'
    px = px_of(ctx)
    ink = near if (not normal and near) else b.near
    keys = ('red', 'blue', 'red_f', 'blue_f', 'web')
    C = palette(style, ink, dict(red=SP_RED, blue=SP_BLUE, red_f=shade(SP_RED, 0.62), blue_f=shade(SP_BLUE, 0.62),
                                 web=SP_WEB), keys)

    def leg(hip, kn, an, toe, red, blue):
        mid = (b.w_thigh + b.w_ankle) / 2
        fill_capsule(ctx, hip, kn, b.w_thigh, mid, blue)
        fill_capsule(ctx, kn, an, mid, b.w_ankle, blue)
        det = (lambda c: limb_web(c, kn, an, 0.12, 1.0, mid * 0.55, px)) if normal else None
        band(ctx, kn, an, mid, b.w_ankle, 0.12, 1.0, red, det)
        fill_capsule(ctx, an, toe, b.w_ankle, b.w_ankle * 0.66, red)

    def arm(side, sh, el, ha, shape, red, blue):
        mid = (b.w_uarm + b.w_wrist) / 2
        fill_capsule(ctx, sh, el, b.w_uarm, mid, blue)
        band(ctx, sh, el, b.w_uarm, mid, 0.0, 0.24, red,
             (lambda c: limb_web(c, sh, el, 0.0, 0.24, b.w_uarm * 0.55, px, spacing=0.045)) if normal else None)
        fill_capsule(ctx, el, ha, mid, b.w_wrist, blue)
        band(ctx, el, ha, mid, b.w_wrist, 0.42, 1.0, red,
             (lambda c: limb_web(c, el, ha, 0.42, 1.0, mid * 0.55, px, spacing=0.042)) if normal else None)
        draw_hand(ctx, J, side, shape, red, b.fist_r, normal)

    front = math.sin(J.yaw)
    leg(J.hip_f, J.knee_f, J.ankle_f, J.toe_f, C['red_f'], C['blue_f'])
    arm('f', J.shoulder_f, J.elbow_f, J.hand_f, p['hf'], C['red_f'], C['blue_f'])

    # torso: blue base, red chest + front panel, webbing radiating from the emblem
    wc = b.w_chest + front * b.w_chest * 0.75
    wh = b.w_hip + front * b.w_hip * 0.6
    T = Torso(J, wh, wc)
    ctx.set_source_rgb(*C['blue'])
    T.path(ctx)
    ctx.fill()
    ctx.save()
    T.path(ctx)
    ctx.clip()
    ctx.set_source_rgb(*C['red'])
    T.region(ctx, 0.56, 1.25, -0.55, 1.6)
    ctx.fill()
    T.region(ctx, -0.2, 0.7, 0.22, 1.6)
    ctx.fill()
    if normal:
        emb = T.at(0.76, 0.42 - 0.3 * front)
        ctx.save()
        T.region(ctx, 0.56, 1.25, -0.55, 1.6)
        T.region(ctx, -0.2, 0.7, 0.22, 1.6)
        ctx.clip()
        ctx.set_source_rgba(*C['web'], 0.5)
        ctx.set_line_width(max(0.0035, 0.8 * px))
        d = T.direction(0.8)
        for k in range(14):
            v = rot2(d, k * TAU / 14)
            ctx.move_to(*emb)
            ctx.line_to(*addv(emb, v, 0.45))
            ctx.stroke()
        for rr in (0.06, 0.11, 0.165, 0.22, 0.28):
            ctx.save()
            ctx.translate(*emb)
            ctx.rotate(math.atan2(d[1], d[0]))
            ctx.scale(1.0, 0.8)
            ctx.arc(0, 0, rr, 0, TAU)
            ctx.restore()
            ctx.stroke()
        ctx.restore()
        spider_emblem(ctx, emb, T.direction(0.8), 0.062, 0.55 + 0.45 * abs(front), SP_INK, px)
    ctx.restore()

    # neck + head
    fill_capsule(ctx, J.chest, J.head, b.w_neck, b.w_neck, C['red'])
    ctx.set_source_rgb(*C['red'])
    ctx.arc(J.head[0], J.head[1], b.head_r, 0, TAU)
    ctx.fill()
    if normal:
        spider_head(ctx, J, px, eye_glow)

    leg(J.hip_n, J.knee_n, J.ankle_n, J.toe_n, C['red'], C['blue'])
    arm('n', J.shoulder_n, J.elbow_n, J.hand_n, p['hn'], C['red'], C['blue'])


def spider_emblem(ctx, c, up, size, squash, col, px):
    """Small black spider: two body ovals and eight bent legs."""
    ctx.save()
    ctx.translate(*c)
    ctx.rotate(math.atan2(up[1], up[0]) - math.pi / 2)
    ctx.scale(squash, 1.0)
    ctx.set_source_rgb(*col)
    for cy_, rx, ry in ((0.18, 0.16, 0.2), (-0.22, 0.2, 0.32)):
        ctx.save()
        ctx.translate(0, cy_ * size)
        ctx.scale(rx * size, ry * size)
        ctx.arc(0, 0, 1, 0, TAU)
        ctx.restore()
        ctx.fill()
    ctx.set_line_width(max(0.0045, 1.0 * px))
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    for s in (-1, 1):
        for y0, kx, ky in ((0.25, 0.55, 0.75), (0.12, 0.7, 0.2), (0.0, 0.7, -0.25), (-0.1, 0.55, -0.8)):
            ctx.move_to(0, y0 * size)
            ctx.line_to(s * kx * 0.6 * size, (y0 + ky * 0.45) * size)
            ctx.line_to(s * kx * size, (y0 + ky) * size)
            ctx.stroke()
    ctx.restore()


SPIDER_EYE = [(0.09, -0.04), (0.26, -0.15), (0.48, -0.15), (0.66, -0.03), (0.74, 0.16), (0.68, 0.36),
              (0.50, 0.45), (0.30, 0.38), (0.16, 0.18)]


def spider_head(ctx, J, px, openness=1.0):
    H = Head(J, cheat=32)
    r = H.r
    ctx.save()
    ctx.arc(H.c[0], H.c[1], r, 0, TAU)
    ctx.clip()
    head_shadow(ctx, H, shade(SP_RED, 0.45), 0.55)
    # web lines: meridians from a centre just below the eyes, plus rings
    tilt = 12 * DEG
    ctx.set_source_rgba(*SP_WEB, 0.55)
    ctx.set_line_width(max(0.0032, 0.75 * px))

    def sph(phi, th):
        u, v, w = math.cos(phi), math.sin(phi) * math.sin(th), math.sin(phi) * math.cos(th)
        return u * math.cos(tilt) + v * math.sin(tilt), -u * math.sin(tilt) + v * math.cos(tilt), w

    def polyline(pts3):
        on = False
        for u, v, w in pts3:
            (x, y), d = H.pt(u, v, w, clamp=False)
            if d > -0.05:
                if on:
                    ctx.line_to(x, y)
                else:
                    ctx.move_to(x, y)
                on = True
            else:
                on = False
        ctx.stroke()
    for k in range(14):
        th = k * TAU / 14
        polyline([sph(0.04 + i * 0.12, th) for i in range(22)])
    for phi in (0.32, 0.64, 0.96, 1.28, 1.6, 1.92, 2.24):
        polyline([sph(phi, i * TAU / 48) for i in range(49)])
    # the lenses: black frame, white lens; openness narrows them (squint) or widens them
    for s in (1, -1):
        pts = []
        dep = 0.0
        for a, bb in SPIDER_EYE:
            bb = 0.15 + (bb - 0.15) * openness
            q, d = H.decal(s * a, bb)
            pts.append(q)
            dep += d
        if dep / len(SPIDER_EYE) < -0.25:
            continue
        sm = smooth_closed(pts, 5)
        ctx.set_source_rgb(*SP_INK)
        ctx.set_line_width(r * 0.16)
        ctx.set_line_join(cairo.LINE_JOIN_ROUND)
        poly(ctx, sm)
        ctx.stroke_preserve()
        ctx.set_source_rgb(*SP_LENS)
        ctx.fill()
        # a faint reflection
        c = H.decal(s * 0.45, 0.25 + 0.06 * openness)[0]
        g = cairo.RadialGradient(c[0], c[1], 0, c[0], c[1], r * 0.35)
        g.add_color_stop_rgba(0, 1, 1, 1, 0.0)
        g.add_color_stop_rgba(1, 0.7, 0.75, 0.9, 0.35)
        ctx.save()
        poly(ctx, sm)
        ctx.clip()
        ctx.set_source(g)
        ctx.paint()
        ctx.restore()
    ctx.restore()


def spider_chains():
    return []


SPIDER = Build(
    name='SPIDER', thigh=0.46, shin=0.45, torso=0.50, neck=0.06, head_r=0.113,
    uarm=0.31, farm=0.29, foot=0.11,
    w_chest=0.152, w_hip=0.098, w_neck=0.064, w_uarm=0.08, w_wrist=0.054,
    w_thigh=0.096, w_ankle=0.058, fist_r=0.044,
    near=SP_RED, far=shade(SP_RED, 0.62), accent=SP_BLUE, eye=SP_LENS, glow=(1.0, 1.0, 1.0),
    trait='none', painter=paint_spider, chains=spider_chains,
    anchor=lambda J: J.head)


# ================================================================== DOOM
def doom_cape_anchor(J):
    d = unit(sub(J.spine[-1], J.spine[-3]))
    front = (J.face * d[1], -J.face * d[0])
    return addv(addv(J.shoulder, front, -J.build.w_chest * 0.5), d, 0.03)


def doom_chains():
    return [(Chain(10, 0.135, gravity=0.8, drag=0.9, trail=1.1), 0.26, 0.5, DM_CAPE)]


def cape_shape(ctx, pts, w0, w1):
    """Cape ribbon with a square hem."""
    n = len(pts)
    L, R = [], []
    for i, p in enumerate(pts):
        a = pts[max(i - 1, 0)]
        b = pts[min(i + 1, n - 1)]
        d = unit(sub(b, a))
        nv = (-d[1], d[0])
        w = (w0 + (w1 - w0) * (i / (n - 1)) ** 0.8) / 2
        L.append(addv(p, nv, w))
        R.append(addv(p, nv, -w))
    poly(ctx, L + list(reversed(R)))


def paint_doom(ctx, J, style='normal', chains=None, near=None, far=None, eye_glow=1.0):
    b = J.build
    p = J.pose
    normal = style == 'normal'
    px = px_of(ctx)
    ink = near if (not normal and near) else b.near
    keys = ('steel', 'steel_f', 'dark', 'dark_f', 'green', 'green_f', 'hood', 'cape', 'lining', 'belt', 'gold')
    C = palette(style, ink, dict(steel=DM_STEEL, steel_f=shade(DM_STEEL, 0.62), dark=DM_STEEL_DK,
                                 dark_f=shade(DM_STEEL_DK, 0.7), green=DM_GREEN, green_f=shade(DM_GREEN, 0.66),
                                 hood=DM_HOOD, cape=DM_CAPE, lining=DM_LINING, belt=DM_BELT, gold=DM_GOLD), keys)

    # ---- cape (behind everything)
    if chains:
        pts, w0, w1, col = chains[0]
        if pts and len(pts) > 2:
            ctx.set_source_rgb(*C['lining'])
            cape_shape(ctx, pts, w0 * 1.05, w1 * 1.04)
            ctx.fill()
            ctx.set_source_rgb(*C['cape'])
            cape_shape(ctx, [addv(q, (0, 0), 0) for q in pts], w0 * 0.8, w1 * 0.86)
            ctx.fill()
            if normal:
                ctx.set_source_rgba(*DM_LINING, 0.45)
                ctx.set_line_width(max(0.006, px))
                for off in (-0.25, 0.2):
                    ctx.move_to(*pts[1])
                    for i, q in enumerate(pts[2:], 2):
                        a_, b_ = pts[i - 1], q
                        d = unit(sub(b_, a_))
                        ctx.line_to(*addv(q, (-d[1], d[0]), off * (w0 + (w1 - w0) * i / len(pts)) * 0.5))
                    ctx.stroke()

    def leg(hip, kn, an, toe, steel, dark, flap):
        mid = (b.w_thigh + b.w_ankle) / 2
        fill_capsule(ctx, hip, kn, b.w_thigh, mid * 1.05, steel)
        fill_capsule(ctx, kn, an, mid * 1.1, b.w_ankle * 1.05, steel)
        # boot cuff and boot
        band(ctx, kn, an, mid * 1.1, b.w_ankle * 1.05, 0.66, 0.78, dark)
        fill_capsule(ctx, an, toe, b.w_ankle * 1.25, b.w_ankle * 0.78, steel)
        ctx.set_source_rgb(*dark)
        ctx.arc(kn[0], kn[1], mid * 0.62, 0, TAU)
        ctx.fill()
        if normal:
            ctx.set_source_rgba(1, 1, 1, 0.18)
            ctx.arc(kn[0], kn[1], mid * 0.36, 0, TAU)
            ctx.fill()
        # tunic skirt panel over the thigh: narrow at the belt, flaring to mid-thigh
        d = unit(sub(kn, hip))
        nv = (-d[1], d[0])
        Lt = math.dist(hip, kn) * 0.58
        top = addv(hip, d, -0.03)
        bot = addv(hip, d, Lt)
        ctx.set_source_rgb(*flap)
        poly(ctx, [addv(top, nv, b.w_hip * 0.52), addv(bot, nv, b.w_thigh * 0.82),
                   addv(bot, nv, -b.w_thigh * 0.82), addv(top, nv, -b.w_hip * 0.52)])
        ctx.fill()
        if normal:
            ctx.set_source_rgba(*shade(flap, 0.55), 1)
            ctx.set_line_width(max(0.012, px))
            ctx.move_to(*addv(addv(bot, d, -0.006), nv, b.w_thigh * 0.8))
            ctx.line_to(*addv(addv(bot, d, -0.006), nv, -b.w_thigh * 0.8))
            ctx.stroke()

    def arm(side, sh, el, ha, shape, steel, dark):
        mid = (b.w_uarm + b.w_wrist) / 2
        fill_capsule(ctx, sh, el, b.w_uarm, mid * 1.05, steel)
        fill_capsule(ctx, el, ha, mid * 1.05, b.w_wrist, steel)
        # flared gauntlet cuff
        d = unit(sub(ha, el))
        L = math.dist(el, ha)
        nv = (-d[1], d[0])
        c0, c1 = addv(el, d, L * 0.5), addv(el, d, L * 0.86)
        ctx.set_source_rgb(*dark)
        poly(ctx, [addv(c0, nv, mid * 0.62), addv(c1, nv, b.w_wrist * 0.95), addv(c1, nv, -b.w_wrist * 0.95),
                   addv(c0, nv, -mid * 0.62)])
        ctx.fill()
        ctx.arc(el[0], el[1], mid * 0.52, 0, TAU)
        ctx.fill()
        draw_hand(ctx, J, side, shape, dark, b.fist_r, normal)

    front = math.sin(J.yaw)
    leg(J.hip_f, J.knee_f, J.ankle_f, J.toe_f, C['steel_f'], C['dark_f'], C['green_f'])
    arm('f', J.shoulder_f, J.elbow_f, J.hand_f, p['hf'], C['steel_f'], C['dark_f'])

    # ---- torso: green tunic over the armour, belt with gold clasps
    wc = b.w_chest + front * b.w_chest * 0.75
    wh = b.w_hip + front * b.w_hip * 0.6
    T = Torso(J, wh, wc)
    ctx.set_source_rgb(*C['green'])
    T.path(ctx)
    ctx.fill()
    ctx.save()
    T.path(ctx)
    ctx.clip()
    if normal:
        ctx.set_source_rgba(*shade(DM_GREEN, 0.6), 0.8)
        T.region(ctx, -0.2, 1.2, -1.6, -0.45)
        ctx.fill()
        ctx.set_source_rgba(1, 1, 1, 0.08)
        T.region(ctx, 0.2, 1.1, 0.35, 0.8)
        ctx.fill()
    ctx.set_source_rgb(*C['belt'])
    T.region(ctx, 0.07, 0.17, -1.6, 1.6)
    ctx.fill()
    ctx.restore()
    if normal:
        for nn, rr in ((0.62 - 0.5 * front, 0.034), (-0.2 - 0.5 * front, 0.026)):
            c = T.at(0.12, nn)
            ctx.set_source_rgb(*C['gold'])
            ctx.arc(c[0], c[1], rr, 0, TAU)
            ctx.fill()
            ctx.set_source_rgba(*shade(DM_GOLD, 0.5), 1)
            ctx.set_line_width(max(0.004, px))
            ctx.arc(c[0], c[1], rr * 0.62, 0, TAU)
            ctx.stroke()

    # ---- near leg (+ flap), then hood and mask, then the near arm
    leg(J.hip_n, J.knee_n, J.ankle_n, J.toe_n, C['steel'], C['dark'], C['green'])
    doom_head(ctx, J, T, C, normal, px, eye_glow)
    arm('n', J.shoulder_n, J.elbow_n, J.hand_n, p['hn'], C['steel'], C['dark'])


DOOM_MASK = [(0.0, 0.74), (0.34, 0.70), (0.58, 0.52), (0.68, 0.20), (0.66, -0.20), (0.54, -0.64),
             (0.30, -0.90), (0.0, -0.96), (-0.30, -0.90), (-0.54, -0.64), (-0.66, -0.20), (-0.68, 0.20),
             (-0.58, 0.52), (-0.34, 0.70)]


def doom_head(ctx, J, T, C, normal, px, eye_glow):
    b = J.build
    H = Head(J, cheat=36)
    r = H.r
    # hood mantle over the shoulders, then the hood itself
    ctx.set_source_rgb(*C['hood'])
    hb = addv(addv(H.c, H.F, -1.0 * r), H.U, -0.5 * r)
    hf = addv(addv(H.c, H.F, 0.3 * r), H.U, -0.9 * r)
    poly(ctx, [hb, T.at(0.86, -1.25), T.at(0.7, -1.12), T.at(0.7, 1.0), T.at(0.84, 0.95), hf])
    ctx.fill()
    hc = addv(addv(H.c, H.F, -0.16 * r), H.U, 0.06 * r)
    ctx.arc(hc[0], hc[1], 1.22 * r, 0, TAU)
    ctx.fill()
    if not normal:
        return
    # hood shading (a darker back)
    g = cairo.LinearGradient(*addv(hc, H.F, 1.2 * r), *addv(hc, H.F, -1.2 * r))
    g.add_color_stop_rgba(0, 0, 0, 0, 0.0)
    g.add_color_stop_rgba(1, 0, 0, 0, 0.35)
    ctx.set_source(g)
    ctx.arc(hc[0], hc[1], 1.22 * r, 0, TAU)
    ctx.fill()
    # the mask: steel face plate seen through the hood opening
    pts = [H.decal(a, bb)[0] for a, bb in DOOM_MASK]
    sm = smooth_closed(pts, 4)
    ctx.set_source_rgb(*DM_LINING)
    ctx.set_line_width(r * 0.18)
    poly(ctx, sm)
    ctx.stroke()
    lit = H.decal(0.1, 0.25)[0]
    g = cairo.RadialGradient(lit[0], lit[1], r * 0.05, lit[0], lit[1], r * 1.1)
    g.add_color_stop_rgb(0, *mixc(DM_STEEL, (1, 1, 1), 0.25))
    g.add_color_stop_rgb(0.6, *DM_STEEL)
    g.add_color_stop_rgb(1, *shade(DM_STEEL, 0.55))
    ctx.set_source(g)
    poly(ctx, sm)
    ctx.fill()
    ctx.save()
    poly(ctx, sm)
    ctx.clip()
    lw = max(0.004, 0.9 * px)
    ctx.set_line_width(lw)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    dk = shade(DM_STEEL, 0.42)

    def line3(pts2, col, alpha=1.0, w=None):
        ctx.set_source_rgba(*col, alpha)
        ctx.set_line_width(w or lw)
        first = True
        for a, bb in pts2:
            q, d = H.decal(a, bb)
            if first:
                ctx.move_to(*q)
                first = False
            else:
                ctx.line_to(*q)
        ctx.stroke()
    # brow plate, nose ridge, cheek ridges
    line3([(-0.5, 0.34), (-0.15, 0.36), (0.0, 0.3), (0.15, 0.36), (0.5, 0.34)], dk, 0.8)
    line3([(0.0, 0.3), (0.0, -0.25)], dk, 0.7)
    for s in (-1, 1):
        line3([(s * 0.34, 0.05), (s * 0.33, -0.3), (s * 0.24, -0.68)], dk, 0.7)
        q, d = H.decal(s * 0.47, 0.02)
        if d > 0:
            ctx.set_source_rgba(*dk, 0.9)
            ctx.arc(q[0], q[1], r * 0.045, 0, TAU)
            ctx.fill()
    # mouth grille
    ctx.set_source_rgb(*DM_SLIT)
    poly(ctx, [H.decal(a, bb)[0] for a, bb in ((-0.24, -0.42), (0.24, -0.42), (0.21, -0.56), (-0.21, -0.56))])
    ctx.fill()
    for k in range(-3, 4):
        a = k * 0.06
        line3([(a, -0.41), (a, -0.57)], shade(DM_STEEL, 0.75), 0.9)
    # eye slits, glowing
    glow = max(0.0, eye_glow)
    for s in (-1, 1):
        if H.depth_of(s * 0.27, 0.2) < -0.1:
            continue
        slit = [H.decal(s * a, bb)[0] for a, bb in ((0.08, 0.17), (0.44, 0.22), (0.42, 0.13), (0.1, 0.1))]
        ctx.set_source_rgb(*mixc(DM_SLIT, DM_EYE, min(1.0, 0.35 + 0.45 * glow)))
        poly(ctx, slit)
        ctx.fill()
    ctx.restore()
    if glow > 0.05:
        for s in (-1, 1):
            if H.depth_of(s * 0.27, 0.2) < -0.1:
                continue
            c = H.decal(s * 0.27, 0.17)[0]
            R = r * (0.45 + 0.35 * glow)
            g = cairo.RadialGradient(c[0], c[1], 0, c[0], c[1], R)
            g.add_color_stop_rgba(0, *DM_EYE, min(0.9, 0.35 * glow))
            g.add_color_stop_rgba(1, *DM_EYE, 0)
            ctx.set_source(g)
            ctx.arc(c[0], c[1], R, 0, TAU)
            ctx.fill()


DOOM = Build(
    name='DOOM', thigh=0.50, shin=0.49, torso=0.56, neck=0.07, head_r=0.128,
    uarm=0.34, farm=0.32, foot=0.13,
    w_chest=0.215, w_hip=0.15, w_neck=0.095, w_uarm=0.112, w_wrist=0.086,
    w_thigh=0.13, w_ankle=0.092, fist_r=0.06,
    near=DM_STEEL, far=shade(DM_STEEL, 0.62), accent=DM_GREEN, eye=DM_EYE, glow=DM_EYE,
    trait='cape', painter=paint_doom, anchor=doom_cape_anchor, chains=doom_chains)

HEROES = {'SPIDER': SPIDER, 'DOOM': DOOM}
