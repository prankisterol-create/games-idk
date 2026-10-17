"""Character construction: builds, poses, forward/inverse kinematics and drawing.

World units are metres, y is up, the ground is y = 0.

Angle conventions (degrees), in the body frame, mirrored by `face` (+1 right, -1 left):
  limbs   -- absolute angle measured from straight DOWN, positive rotates toward
             the facing direction. 0 = hanging, 90 = pointing forward, 180 = up.
  elbow   -- flex, positive curls the forearm forward/up (an + en = forearm angle)
  knee    -- flex, positive folds the shin backward  (ln - kn = shin angle)
  lean    -- torso angle from vertical UP, positive leans forward
  bend    -- spine curvature, positive hunches (back bulges away from facing)
  head    -- neck tilt relative to the top of the spine, positive nods forward
  rot     -- whole-body rotation about the hip, positive = forward (front-flip)
Everything except x / y / face / hand shapes is interpolated linearly, so the
animator controls spin direction explicitly (rot 0 -> 360 is a full flip).
"""
import math
from dataclasses import dataclass

import cairo

DEG = math.pi / 180.0


def hexrgb(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4))


@dataclass
class Build:
    name: str
    thigh: float
    shin: float
    torso: float
    neck: float
    head_r: float
    uarm: float
    farm: float
    foot: float
    w_chest: float
    w_hip: float
    w_neck: float
    w_uarm: float
    w_wrist: float
    w_thigh: float
    w_ankle: float
    fist_r: float
    near: tuple
    far: tuple
    accent: tuple
    eye: tuple
    glow: tuple
    trait: str            # 'headband' or 'ponytail'
    shoulder_at: float = 0.9


# --------------------------------------------------------------------------
# The cast
# --------------------------------------------------------------------------
KAI = Build(
    name='KAI', thigh=0.46, shin=0.45, torso=0.50, neck=0.06, head_r=0.132,
    uarm=0.31, farm=0.30, foot=0.11,
    w_chest=0.165, w_hip=0.115, w_neck=0.07, w_uarm=0.092, w_wrist=0.066,
    w_thigh=0.105, w_ankle=0.07, fist_r=0.052,
    near=hexrgb('#F06A2C'), far=hexrgb('#A9431C'), accent=hexrgb('#EFE6D2'),
    eye=hexrgb('#FFF6DE'), glow=hexrgb('#FFB04A'), trait='headband')

SEN = Build(
    name='SEN', thigh=0.51, shin=0.51, torso=0.52, neck=0.065, head_r=0.116,
    uarm=0.34, farm=0.33, foot=0.115,
    w_chest=0.125, w_hip=0.085, w_neck=0.055, w_uarm=0.068, w_wrist=0.05,
    w_thigh=0.08, w_ankle=0.054, fist_r=0.042,
    near=hexrgb('#3CC8CB'), far=hexrgb('#1F7F8C'), accent=hexrgb('#E9FBF9'),
    eye=hexrgb('#F1FFFF'), glow=hexrgb('#7DF6FF'), trait='ponytail')

CAST = {'KAI': KAI, 'SEN': SEN}

DEFAULT = dict(x=0.0, y=None, face=1, lean=0.0, bend=0.0, head=0.0, rot=0.0, yaw=0.0,
               an=10.0, en=20.0, af=-10.0, ef=20.0,
               ln=6.0, kn=6.0, lf=-6.0, kf=6.0,
               pn=0.0, pf=0.0,                 # foot point (0 flat .. 1 pointed)
               san=1.0, saf=1.0, sln=1.0, slf=1.0,  # limb stretch (smear drawings)
               sq=1.0,                          # torso squash/stretch
               hn='fist', hf='fist')            # hand shapes: fist | open | blade
DISCRETE = ('face', 'hn', 'hf')


def pose(**kw):
    p = dict(DEFAULT)
    p.update(kw)
    return p


# --------------------------------------------------------------------------
# Kinematics
# --------------------------------------------------------------------------
def ldir(theta_deg, f):
    t = theta_deg * DEG
    return (f * math.sin(t), -math.cos(t))


def udir(theta_deg, f):
    t = theta_deg * DEG
    return (f * math.sin(t), math.cos(t))


def add(a, b, s=1.0):
    return (a[0] + b[0] * s, a[1] + b[1] * s)


def qbez(p0, p1, p2, t):
    a = (1 - t) * (1 - t)
    b = 2 * (1 - t) * t
    c = t * t
    return (a * p0[0] + b * p1[0] + c * p2[0], a * p0[1] + b * p1[1] + c * p2[1])


def vec_angle_from_down(v, f):
    """Inverse of ldir: the limb angle that points along v."""
    return math.atan2(f * v[0], -v[1]) / DEG


class Joints:
    """World-space joint positions for one drawing."""
    __slots__ = ('hip', 'spine', 'chest', 'shoulder', 'shoulder_n', 'shoulder_f', 'head', 'elbow_n',
                 'hand_n', 'elbow_f', 'hand_f', 'knee_n', 'ankle_n', 'toe_n', 'knee_f', 'ankle_f',
                 'toe_f', 'hip_n', 'hip_f', 'face', 'build', 'pose', 'head_ang', 'yaw', 'rotm')


def solve(build, p):
    """Forward kinematics. Returns Joints in world space.

    Points are built in a profile plane (u = forward, v = up) plus a lateral
    offset w (+ toward camera). `yaw` turns the figure toward the camera:
    screen_x = face * (u*cos(yaw) + w*sin(yaw)).
    """
    f = 1 if p['face'] >= 0 else -1
    b = build
    yaw = p.get('yaw', 0.0) * DEG
    cy, sy = math.cos(yaw), math.sin(yaw)
    hip = (p['x'], p['y'] if p['y'] is not None else ground_y(build, p))
    lean, bend = p['lean'], p['bend']
    T = b.torso * p['sq']
    chest = add((0, 0), udir(lean, 1), T)
    ctrl = add((0, 0), udir(lean - bend, 1), 0.5 * T)
    spine = [qbez((0, 0), ctrl, chest, i / 10.0) for i in range(11)]
    shoulder = qbez((0, 0), ctrl, chest, b.shoulder_at)
    tx, ty = chest[0] - ctrl[0], chest[1] - ctrl[1]
    top_ang = math.atan2(tx, ty) / DEG
    head_ang = top_ang + p['head']
    head = add(chest, udir(head_ang, 1), b.neck + b.head_r)
    sw = b.w_chest * 0.95           # half shoulder span (only visible when yaw != 0)
    hw = b.w_hip * 0.75

    def arm(a, e, s):
        el = add(shoulder, ldir(a, 1), b.uarm * s)
        ha = add(el, ldir(a + e, 1), b.farm * s)
        return el, ha

    def leg(l, k, s, pt):
        kn = add((0, 0), ldir(l, 1), b.thigh * s)
        an = add(kn, ldir(l - k, 1), b.shin * s)
        fa = 90.0 + ((l - k + 14.0) - 90.0) * max(0.0, min(1.0, pt))
        toe = add(an, ldir(fa, 1), b.foot)
        return kn, an, toe

    elbow_n, hand_n = arm(p['an'], p['en'], p['san'])
    elbow_f, hand_f = arm(p['af'], p['ef'], p['saf'])
    knee_n, ankle_n, toe_n = leg(p['ln'], p['kn'], p['sln'], p['pn'])
    knee_f, ankle_f, toe_f = leg(p['lf'], p['kf'], p['slf'], p['pf'])

    r = -f * p['rot'] * DEG
    cr, sr = math.cos(r), math.sin(r)

    def W(q, w=0.0):
        x = f * (q[0] * cy + w * sy)
        y = q[1]
        return (hip[0] + x * cr - y * sr, hip[1] + x * sr + y * cr)

    J = Joints()
    J.hip = hip
    J.spine = [W(q) for q in spine]
    J.chest, J.shoulder, J.head = W(chest), W(shoulder), W(head)
    J.shoulder_n, J.shoulder_f = W(shoulder, sw), W(shoulder, -sw)
    J.hip_n, J.hip_f = W((0, 0), hw), W((0, 0), -hw)
    J.elbow_n, J.hand_n = W(elbow_n, sw + 0.035), W(hand_n, sw + 0.06)
    J.elbow_f, J.hand_f = W(elbow_f, -sw - 0.035), W(hand_f, -sw - 0.06)
    J.knee_n, J.ankle_n, J.toe_n = W(knee_n, hw * 1.1), W(ankle_n, hw * 1.25), W(toe_n, hw * 1.25)
    J.knee_f, J.ankle_f, J.toe_f = W(knee_f, -hw * 1.1), W(ankle_f, -hw * 1.25), W(toe_f, -hw * 1.25)
    J.face, J.build, J.pose = f, build, p
    J.head_ang = head_ang + p['rot']   # angle-from-up in world (for eyes / hair anchors)
    J.yaw = yaw
    J.rotm = (cr, sr)
    return J


def ground_y(build, p):
    """Hip height that puts the lowest ankle on the ground (pose with rot applied)."""
    q = dict(p)
    q['y'] = 0.0
    J = solve(build, q)
    low = min(J.ankle_n[1], J.ankle_f[1])
    return build.w_ankle * 0.5 - low


def ik2(root, target, l1, l2, f, bend_forward):
    """Two-bone IK in the body frame. Returns (root_angle, flex, stretch)."""
    vx, vy = target[0] - root[0], target[1] - root[1]
    d = math.hypot(vx, vy)
    L = l1 + l2
    stretch = 1.0
    if d > L * 0.9995:
        stretch = min(d / (L * 0.9995), 1.08)
        l1, l2 = l1 * stretch, l2 * stretch
        d = min(d, (l1 + l2) * 0.9995)
    d = max(d, abs(l1 - l2) + 1e-4)
    base = vec_angle_from_down((vx, vy), f)
    ca = (l1 * l1 + d * d - l2 * l2) / (2 * l1 * d)
    alpha = math.acos(max(-1.0, min(1.0, ca))) / DEG
    cb = (l1 * l1 + l2 * l2 - d * d) / (2 * l1 * l2)
    beta = math.acos(max(-1.0, min(1.0, cb))) / DEG
    flex = 180.0 - beta
    if bend_forward:      # knee: joint in front, child rotates back
        return base + alpha, flex, stretch
    return base - alpha, flex, stretch   # elbow: joint behind, child rotates forward


def to_body(p, world_pt, hip):
    """World point -> unrotated body frame relative to hip."""
    f = 1 if p['face'] >= 0 else -1
    r = f * p['rot'] * DEG
    dx, dy = world_pt[0] - hip[0], world_pt[1] - hip[1]
    cr, sr = math.cos(r), math.sin(r)
    return (dx * cr - dy * sr, dx * sr + dy * cr)


def plant_leg(build, p, side, ankle_world):
    """Return a copy of p whose `side` ('n'/'f') ankle sits on ankle_world."""
    q = dict(p)
    if q['y'] is None:
        q['y'] = ground_y(build, q)
    f = 1 if q['face'] >= 0 else -1
    tgt = to_body(q, ankle_world, (q['x'], q['y']))
    a, k, s = ik2((0, 0), tgt, build.thigh, build.shin, f, True)
    q['l' + side], q['k' + side], q['sl' + side] = a, k, s
    return q


def plant_hand(build, p, side, hand_world):
    q = dict(p)
    if q['y'] is None:
        q['y'] = ground_y(build, q)
    J = solve(build, q)
    f = J.face
    sh = to_body(q, J.shoulder, J.hip)
    tgt = to_body(q, hand_world, J.hip)
    a, e, s = ik2(sh, tgt, build.uarm, build.farm, f, False)
    q['a' + side], q['e' + side], q['sa' + side] = a, e, s
    return q


def ankle_pos(build, p, side):
    J = solve(build, p)
    return J.ankle_n if side == 'n' else J.ankle_f


def hand_pos(build, p, side):
    J = solve(build, p)
    return J.hand_n if side == 'n' else J.hand_f


# --------------------------------------------------------------------------
# Drawing (cairo context already transformed to world space, y up)
# --------------------------------------------------------------------------
def capsule(ctx, a, b, wa, wb):
    dx, dy = b[0] - a[0], b[1] - a[1]
    L = math.hypot(dx, dy)
    if L < 1e-6:
        ctx.arc(a[0], a[1], max(wa, wb) / 2, 0, 2 * math.pi)
        ctx.fill()
        return
    nx, ny = -dy / L, dx / L
    # tangent points so the quad meets the end circles smoothly
    ctx.move_to(a[0] + nx * wa / 2, a[1] + ny * wa / 2)
    ctx.line_to(b[0] + nx * wb / 2, b[1] + ny * wb / 2)
    ctx.line_to(b[0] - nx * wb / 2, b[1] - ny * wb / 2)
    ctx.line_to(a[0] - nx * wa / 2, a[1] - ny * wa / 2)
    ctx.close_path()
    ctx.fill()
    ctx.arc(a[0], a[1], wa / 2, 0, 2 * math.pi)
    ctx.fill()
    ctx.arc(b[0], b[1], wb / 2, 0, 2 * math.pi)
    ctx.fill()


def tapered_path(ctx, pts, w0, w1):
    n = len(pts)
    left, right = [], []
    for i, pt in enumerate(pts):
        a = pts[max(i - 1, 0)]
        b = pts[min(i + 1, n - 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        L = math.hypot(dx, dy) or 1.0
        nx, ny = -dy / L, dx / L
        w = (w0 + (w1 - w0) * i / (n - 1)) / 2
        left.append((pt[0] + nx * w, pt[1] + ny * w))
        right.append((pt[0] - nx * w, pt[1] - ny * w))
    ctx.move_to(*left[0])
    for q in left[1:]:
        ctx.line_to(*q)
    for q in reversed(right):
        ctx.line_to(*q)
    ctx.close_path()
    ctx.fill()
    ctx.arc(pts[0][0], pts[0][1], w0 / 2, 0, 2 * math.pi)
    ctx.fill()
    ctx.arc(pts[-1][0], pts[-1][1], w1 / 2, 0, 2 * math.pi)
    ctx.fill()


def draw_arm(ctx, b, sh, el, ha, shape, f):
    capsule(ctx, sh, el, b.w_uarm, (b.w_uarm + b.w_wrist) / 2)
    capsule(ctx, el, ha, (b.w_uarm + b.w_wrist) / 2, b.w_wrist)
    dx, dy = ha[0] - el[0], ha[1] - el[1]
    L = math.hypot(dx, dy) or 1.0
    ux, uy = dx / L, dy / L
    if shape == 'fist':
        c = (ha[0] + ux * b.fist_r * 0.35, ha[1] + uy * b.fist_r * 0.35)
        ctx.arc(c[0], c[1], b.fist_r, 0, 2 * math.pi)
        ctx.fill()
    else:  # open palm (wrist bent back, palm toward the target) / knife hand (straight)
        theta = math.atan2(f * dx, -dy) + (35 * DEG if shape == 'open' else 0.0)
        hx, hy = f * math.sin(theta), -math.cos(theta)
        ln = b.fist_r * (1.9 if shape == 'open' else 2.6)
        tip = (ha[0] + hx * ln, ha[1] + hy * ln)
        capsule(ctx, ha, tip, b.fist_r * 1.3, b.fist_r * 0.8)


def draw_leg(ctx, b, hip, kn, an, toe):
    mid = (b.w_thigh + b.w_ankle) / 2
    capsule(ctx, hip, kn, b.w_thigh, mid * 1.02)
    capsule(ctx, kn, an, mid * 1.02, b.w_ankle)
    capsule(ctx, an, toe, b.w_ankle, b.w_ankle * 0.62)


def head_axes(J):
    """Screen-space forward / up / lateral unit-ish vectors for the head."""
    f = J.face
    cr, sr = J.rotm
    a = J.head_ang - J.pose['rot']          # body-frame angle from up
    fu = udir(a + 90, 1)                    # forward in profile plane
    uu = udir(a, 1)

    def W(v, w=0.0):
        x = f * (v[0] * math.cos(J.yaw) + w * math.sin(J.yaw))
        y = v[1]
        return (x * cr - y * sr, x * sr + y * cr)
    return W(fu), W(uu), W((0, 0), 1.0)


def draw_head(ctx, J, color, style):
    b = J.build
    hx, hy = J.head
    r = b.head_r
    ctx.set_source_rgb(*color)
    ctx.arc(hx, hy, r, 0, 2 * math.pi)
    ctx.fill()
    if style != 'normal':
        return
    fwd, up, lat = head_axes(J)
    if b.trait == 'headband':
        ctx.save()
        ctx.arc(hx, hy, r, 0, 2 * math.pi)
        ctx.clip()
        c = add((hx, hy), up, r * 0.50)
        side = (up[1], -up[0]) if J.face > 0 else (-up[1], up[0])
        ang = math.atan2(side[1], side[0])
        ctx.translate(*c)
        ctx.rotate(ang)
        ctx.set_source_rgb(*b.accent)
        ctx.rectangle(-r * 1.2, -r * 0.13, r * 2.4, r * 0.26)
        ctx.fill()
        ctx.restore()


def eye_points(J):
    """List of (centre, slit direction, up) for visible eyes."""
    b = J.build
    fwd, up, lat = head_axes(J)
    r = b.head_r
    out = []
    sides = (1.0,) if abs(J.yaw) < 0.12 else (1.0, -1.0)
    for s in sides:
        c = add(add(add(J.head, fwd, r * 0.48), up, r * 0.05), lat, s * r * 0.36)
        # slit direction: along forward in profile, toward the outside of the face when frontal
        d = add(fwd, lat, s * 0.0)
        dl = math.hypot(*d)
        if abs(J.yaw) > 0.12:
            o = (lat[0] * -s, lat[1] * -s)   # inner corner points toward the nose
            mix = min(1.0, abs(J.yaw) / (math.pi / 2))
            d = (fwd[0] * (1 - mix) + o[0] * mix, fwd[1] * (1 - mix) + o[1] * mix)
            dl = math.hypot(*d)
        d = (d[0] / (dl or 1), d[1] / (dl or 1))
        out.append((c, d, up, s))
    return out


def eye_point(J):
    c, d, up, s = eye_points(J)[0]
    return c, d, up


def draw_eye(ctx, J, glow=1.0):
    b = J.build
    r = b.head_r
    for (ex, ey), fwd, up, s in eye_points(J):
        scale = 1.0 if s > 0 else 0.85 + 0.15 * math.sin(J.yaw)
        if glow > 0:
            g = cairo.RadialGradient(ex, ey, 0, ex, ey, r * 0.9)
            g.add_color_stop_rgba(0, *b.glow, 0.5 * glow)
            g.add_color_stop_rgba(1, *b.glow, 0.0)
            ctx.set_source(g)
            ctx.arc(ex, ey, r * 0.9, 0, 2 * math.pi)
            ctx.fill()
        L = r * 0.40 * scale
        H = r * 0.11 * scale
        # perpendicular "up" for the slit, flipped so it points to the top of the head
        nu = (-fwd[1], fwd[0])
        if nu[0] * up[0] + nu[1] * up[1] < 0:
            nu = (-nu[0], -nu[1])
        back = add((ex, ey), fwd, -L * 0.55)
        front = add(add((ex, ey), fwd, L * 0.45), nu, -H * 0.6)
        top = add(add((ex, ey), nu, H * 0.9), fwd, -L * 0.05)
        bot = add((ex, ey), nu, -H * 0.7)
        ctx.set_source_rgb(*b.eye)
        ctx.move_to(*back)
        ctx.curve_to(top[0], top[1], top[0], top[1], *front)
        ctx.curve_to(bot[0], bot[1], bot[0], bot[1], *back)
        ctx.close_path()
        ctx.fill()


def hair_anchor(J):
    """World anchor for secondary chains (headband knot / ponytail root)."""
    b = J.build
    fwd, up, lat = head_axes(J)
    if b.trait == 'headband':
        return add(add(J.head, fwd, -b.head_r * 0.86), up, b.head_r * 0.48)
    return add(add(J.head, fwd, -b.head_r * 0.7), up, b.head_r * 0.62)


def draw_chain(ctx, pts, w0, w1, color):
    if not pts or len(pts) < 2:
        return
    ctx.set_source_rgb(*color)
    tapered_path(ctx, pts, w0, w1)


def draw_figure(ctx, J, style='normal', chains=None, near=None, far=None, eye_glow=1.0):
    """Draw a solved figure. style: normal | flat (single colour) | silhouette."""
    b = J.build
    near = near or b.near
    far = far or b.far
    if style in ('flat', 'silhouette'):
        far = near
    p = J.pose
    if chains:
        for pts, w0, w1, col in chains:
            draw_chain(ctx, pts, w0, w1, near if style != 'normal' else col)
    front = math.sin(J.yaw)
    ctx.set_source_rgb(*far)
    draw_leg(ctx, b, J.hip_f, J.knee_f, J.ankle_f, J.toe_f)
    draw_arm(ctx, b, J.shoulder_f, J.elbow_f, J.hand_f, p['hf'], J.face)
    ctx.set_source_rgb(*near)
    wc = b.w_chest + front * b.w_chest * 0.75
    wh = b.w_hip + front * b.w_hip * 0.6
    tapered_path(ctx, J.spine, wh, wc)
    capsule(ctx, J.chest, J.head, b.w_neck, b.w_neck)
    draw_head(ctx, J, near, style)
    ctx.set_source_rgb(*near)
    draw_leg(ctx, b, J.hip_n, J.knee_n, J.ankle_n, J.toe_n)
    draw_arm(ctx, b, J.shoulder_n, J.elbow_n, J.hand_n, p['hn'], J.face)
    if style == 'normal' and J.yaw > -0.3:
        draw_eye(ctx, J, eye_glow)
