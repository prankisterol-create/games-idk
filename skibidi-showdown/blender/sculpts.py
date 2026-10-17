"""Sculpted (signed distance field) parts: realistic heads and porcelain toilets.

Heads are modelled in a normalised space where the head is 1 unit from chin to crown,
centred on the origin, facing -Y. `head()` places that sculpt in the model with a scale.
"""

import math

import numpy as np

import lib
import sdf as S


# ======================================================================================
# Head
# ======================================================================================

EXPRESSIONS = {
    # eye opening (upper, lower), pupil radius, brow polyline (x, z) inner->outer,
    # mouth: half width, open height, corner lift
    "manic": dict(lid_top=0.036, lid_bot=0.03, pupil=0.0085, iris=0.021,
                  brow=[(0.05, 0.118), (0.12, 0.142), (0.2, 0.122)],
                  mouth_w=0.15, mouth_open=0.042, corner=2.2),
    "angry": dict(lid_top=0.026, lid_bot=0.026, pupil=0.0095, iris=0.021,
                  brow=[(0.05, 0.078), (0.12, 0.105), (0.2, 0.125)],
                  mouth_w=0.14, mouth_open=0.036, corner=0.6),
    "smug": dict(lid_top=0.022, lid_bot=0.024, pupil=0.0095, iris=0.021,
                 brow=[(0.05, 0.095), (0.12, 0.118), (0.2, 0.112)],
                 mouth_w=0.13, mouth_open=0.026, corner=2.6),
}

EYE_X, EYE_Z, EYE_Y, EYE_R = 0.13, 0.035, -0.343, 0.053


def _mouth_curve(x, e):
    """Centre line z, half opening and lip-front y of the mouth at horizontal position x."""
    w = e["mouth_w"]
    t = np.clip(np.abs(x) / w, 0, 1)
    zc = -0.272 + e["corner"] * 0.02 * t ** 2
    half = e["mouth_open"] * np.power(np.clip(1 - t ** 2, 0, 1), 0.55)
    yf = -0.452 + 0.11 * t ** 2
    return zc, half, yf


def head_field(e):
    """Signed distance field of the head + neck in normalised units."""
    cranium = S.ellipsoid((0, 0.02, 0.1), (0.305, 0.405, 0.4))
    parietal = S.mirror_x(S.ellipsoid((0.13, 0.06, 0.22), (0.18, 0.31, 0.26)))
    forehead = S.ellipsoid((0, -0.2, 0.17), (0.255, 0.2, 0.22))
    midface = S.ellipsoid((0, -0.15, -0.1), (0.24, 0.26, 0.27))
    mandible = S.mirror_x(S.tube_path([(0.2, 0.04, -0.27), (0.16, -0.2, -0.39),
                                       (0.06, -0.335, -0.445), (0.0, -0.345, -0.45)],
                                      [0.05, 0.05, 0.05, 0.05]))
    cheek = S.mirror_x(S.ellipsoid((0.17, -0.255, -0.035), (0.09, 0.085, 0.06)))
    brow_ridge = S.capsule((-0.165, -0.36, 0.105), (0.165, -0.36, 0.105), 0.04)
    head = S.union(cranium, parietal, k=0.1)
    head = S.union(head, forehead, k=0.12)
    head = S.union(head, midface, k=0.1)
    head = S.union(head, mandible, k=0.07)
    head = S.union(head, cheek, k=0.07)
    head = S.union(head, brow_ridge, k=0.06)
    temple = S.mirror_x(S.ellipsoid((0.315, -0.2, 0.1), (0.035, 0.1, 0.09)))
    head = S.subtract(head, temple, k=0.08)

    # eye sockets + eyelids that wrap the eyeballs
    socket = S.mirror_x(S.ellipsoid((EYE_X, -0.372, EYE_Z), (0.074, 0.068, 0.058)))
    head = S.subtract(head, socket, k=0.035)
    head = S.union(head, _eyelids(e), k=0.016)

    # nose
    bridge = S.capsule((0, -0.39, 0.06), (0, -0.482, -0.1), 0.024, 0.033)
    tip = S.sphere((0, -0.487, -0.118), 0.036)
    alae = S.mirror_x(S.ellipsoid((0.042, -0.452, -0.137), (0.028, 0.032, 0.028)))
    nose = S.union(bridge, tip, k=0.03)
    nose = S.union(nose, alae, k=0.025)
    head = S.union(head, nose, k=0.04)
    nostrils = S.mirror_x(S.ellipsoid((0.019, -0.47, -0.162), (0.011, 0.016, 0.009)))
    head = S.subtract(head, nostrils, k=0.008)

    # mouth: push the muzzle forward, cut the grin, roll the lips
    muzzle = S.ellipsoid((0, -0.39, -0.268), (0.135, 0.062, 0.075))
    head = S.union(head, muzzle, k=0.045)
    head = S.subtract(head, _mouth_cavity(e), k=0.01)
    head = S.union(head, _lips(e), k=0.014)

    # ears
    ear = S.ellipsoid((0.312, 0.07, -0.03), (0.034, 0.066, 0.112), rot=(-12, 0, -18))
    ear = S.subtract(ear, S.ellipsoid((0.338, 0.07, -0.045), (0.02, 0.044, 0.072),
                                      rot=(-12, 0, -18)), k=0.01)
    head = S.union(head, S.mirror_x(ear), k=0.02)

    # neck (long: it disappears into the toilet water) and its muscles
    neck = S.cylinder((0, 0.07, -1.15), 0.165, 0.85, sy=1.08)
    adam = S.ellipsoid((0, -0.1, -0.6), (0.035, 0.03, 0.045))
    scm = S.mirror_x(S.capsule((0.17, 0.12, -0.32), (0.05, -0.07, -0.85), 0.032))
    neck = S.union(neck, adam, k=0.04)
    neck = S.union(neck, scm, k=0.06)
    head = S.union(head, neck, k=0.09)
    under_jaw = S.ellipsoid((0, -0.25, -0.63), (0.22, 0.14, 0.15))
    return S.subtract(head, under_jaw, k=0.05)


def _eyelids(e):
    def f(P):
        q = P.copy()
        q[:, 0] = np.abs(q[:, 0]) - EYE_X
        q[:, 1] = q[:, 1] - EYE_Y
        q[:, 2] = q[:, 2] - EYE_Z
        r = np.sqrt(np.sum(q * q, axis=1))
        shell = np.abs(r - (EYE_R + 0.011)) - 0.01
        u = q[:, 0] / 0.062
        top = e["lid_top"] * np.clip(1 - u ** 2, 0, 1) ** 0.7
        bot = e["lid_bot"] * np.clip(1 - u ** 2, 0, 1) ** 0.7
        opening = np.where(q[:, 2] > 0, q[:, 2] - top, -q[:, 2] - bot)   # >0: covered by a lid
        lid = -S._smin(-shell, opening, 0.008)
        front = q[:, 1] - 0.015                                            # only the front half
        return np.maximum(lid, front)
    return f


def _mouth_cavity(e):
    def f(P):
        x, y, z = P[:, 0], P[:, 1], P[:, 2]
        zc, half, yf = _mouth_curve(x, e)
        d_open = np.abs(z - zc) - half
        d_side = np.abs(x) - e["mouth_w"]
        d_depth = np.maximum(y - (-0.34), -0.62 - y)
        slot = np.maximum(np.maximum(d_open, d_side), d_depth)
        inner = S.ellipsoid((0, -0.34, -0.275), (e["mouth_w"] * 0.85, 0.075, 0.06))(P)
        return np.minimum(slot, inner)
    return f


def _lips(e):
    xs = np.linspace(-e["mouth_w"] * 1.02, e["mouth_w"] * 1.02, 9)
    upper, lower, ru, rl = [], [], [], []
    for x in xs:
        zc, half, yf = _mouth_curve(np.array([x]), e)
        t = abs(x) / e["mouth_w"]
        upper.append((x, yf[0] + 0.012, zc[0] + half[0] + 0.012))
        lower.append((x, yf[0] + 0.01, zc[0] - half[0] - 0.014))
        ru.append(0.019 * (1 - 0.55 * t ** 2))
        rl.append(0.024 * (1 - 0.6 * t ** 2))
    return S.union(S.tube_path(upper, ru), S.tube_path(lower, rl), k=0.012)


def teeth_field(e):
    """Upper and lower teeth rows following the grin."""
    nodes = []
    for row, sign, n in (("upper", 1, 12), ("lower", -1, 10)):
        w = e["mouth_w"] * (0.92 if row == "upper" else 0.82)
        for i in range(n):
            x = -w + (2 * w) * (i + 0.5) / n
            zc, half, yf = _mouth_curve(np.array([x]), e)
            t = abs(x) / e["mouth_w"]
            tooth_h = (0.032 if row == "upper" else 0.022) * (1 - 0.3 * t)
            if row == "upper" and abs(x) < w / n * 1.2:
                tooth_h *= 1.12
            z = zc[0] + sign * (half[0] - tooth_h * 0.42)
            y = yf[0] + 0.03
            tw = (2 * w) / n * 0.5
            nodes.append(S.round_box((x, y, z), (tw * 1.02, 0.013, tooth_h * 0.6), 0.0055,
                                     rot=(0, 0, -math.degrees(math.atan2(0.5 * x, 1.0)))))
    return S.union(*nodes, k=0.002)


def tongue_field(e):
    zc, half, yf = _mouth_curve(np.array([0.0]), e)
    return S.ellipsoid((0, -0.37, zc[0] - half[0] + 0.006), (e["mouth_w"] * 0.55, 0.06, 0.02))


def brow_field(e, field):
    """Eyebrows as a thick layer of hair lying on the skin (follows the brow ridge)."""
    xs = np.array([p[0] for p in e["brow"]], np.float32)
    zs = np.array([p[1] for p in e["brow"]], np.float32)
    half = np.array([0.021, 0.019, 0.009], np.float32)

    def region(P):
        x, z = np.abs(P[:, 0]), P[:, 2]
        best = np.full(len(P), 1e3, np.float32)
        for i in range(len(xs) - 1):
            ax, az, bx, bz = xs[i], zs[i], xs[i + 1], zs[i + 1]
            dx, dz = bx - ax, bz - az
            t = np.clip(((x - ax) * dx + (z - az) * dz) / (dx * dx + dz * dz), 0, 1)
            px, pz = ax + t * dx, az + t * dz
            hw = half[i] + (half[i + 1] - half[i]) * t
            best = np.minimum(best, np.sqrt((x - px) ** 2 + (z - pz) ** 2) - hw)
        return np.maximum(best, P[:, 1] + 0.2)

    def f(P):
        layer = np.abs(field(P) - 0.007) - 0.007
        return -S._smin(-layer, -region(P), 0.006)
    return f


def skin_paint(e, base="skin", stubble=True):
    """Vertex colour layers in normalised head space."""
    lips = _lips(e)
    cavity = _mouth_cavity(e)
    layers = [
        # warm blood flush: ears, cheeks, nose
        (S.falloff(S.mirror_x(S.ellipsoid((0.32, 0.07, -0.03), (0.06, 0.09, 0.13))), 0.03),
         (214, 132, 118)),
        (lambda P: 0.55 * S.falloff(S.mirror_x(S.ellipsoid((0.17, -0.29, -0.11), (0.07, 0.06, 0.06))),
                                    0.06)(P), (220, 128, 116)),
        (lambda P: 0.7 * S.falloff(S.sphere((0, -0.487, -0.118), 0.032), 0.04)(P), (218, 126, 112)),
        # eye socket shadow / lids
        (lambda P: 0.35 * S.falloff(S.mirror_x(S.ellipsoid((EYE_X, -0.36, EYE_Z), (0.08, 0.06, 0.07))),
                                    0.02)(P), (176, 120, 104)),
    ]
    if stubble:
        def beard(P):
            x, y, z = P[:, 0], P[:, 1], P[:, 2]
            jaw = np.clip((-0.13 - z) / 0.06, 0, 1) * np.clip((0.12 - y) / 0.1, 0, 1)
            lip_top = np.clip((0.06 - np.abs(z + 0.205)) / 0.03, 0, 1) * np.clip((-0.36 - y) / 0.04, 0, 1)
            neck_cut = np.clip((z + 0.55) / 0.08, 0, 1)
            return 0.38 * np.maximum(jaw, lip_top) * neck_cut
        layers.append((beard, (150, 132, 128)))
    layers += [
        (S.falloff(lips, 0.012), (186, 92, 94)),
        (S.falloff(cavity, 0.004), (74, 18, 26)),
    ]
    return layers


class HeadPlacer:
    """Maps the normalised head sculpt into model space."""

    def __init__(self, center, scale):
        self.c = np.asarray(center, np.float32)
        self.s = float(scale)

    def node(self, n):
        return lambda P: n((P - self.c) / self.s) * self.s

    def weight(self, w):
        return lambda P: w((P - self.c) / self.s)

    def point(self, p):
        return tuple(float(v) for v in self.c + self.s * np.asarray(p, np.float32))

    def size(self, v):
        return tuple(float(a) * self.s for a in v) if isinstance(v, (tuple, list)) else v * self.s

    def bounds(self, bmin, bmax):
        return (self.c + self.s * np.asarray(bmin, np.float32),
                self.c + self.s * np.asarray(bmax, np.float32))


def head(m, center, scale, expression="manic", joint="Head", eyes="normal", iris="iris_brown",
         neck_bottom=-1.2, res=0.0085, base="skin"):
    """Add a sculpted head to model `m`. Returns the HeadPlacer for extra accessories."""
    e = EXPRESSIONS[expression]
    H = HeadPlacer(center, scale)
    field = head_field(e)
    paint = lib.paint_layers(base, [(H.weight(w), c) for w, c in skin_paint(e, base)])
    bmin, bmax = H.bounds((-0.38, -0.58, neck_bottom), (0.38, 0.5, 0.52))
    m.sdf("HeadSculpt", H.node(field), bmin, bmax, "skin", res=res * scale, joint=joint,
          paint=paint, max_tris=12000)

    teeth = teeth_field(e)
    tb = H.bounds((-0.2, -0.5, -0.36), (0.2, -0.3, -0.2))
    m.sdf("Teeth", H.node(teeth), *tb, "teeth", res=0.004 * scale, joint=joint, max_tris=3000)
    m.sdf("Tongue", H.node(tongue_field(e)), *tb, "tongue", res=0.005 * scale, joint=joint,
          max_tris=1500)
    m.sdf("Brows", H.node(brow_field(e, field)),
          *H.bounds((-0.26, -0.47, 0.03), (0.26, -0.28, 0.2)), "brow", res=0.004 * scale,
          joint=joint, max_tris=3000)

    # eyes: white ball, iris and pupil caps (or a glowing ball)
    for side, sx in (("L", 1), ("R", -1)):
        ec = (sx * EYE_X, EYE_Y, EYE_Z)
        if eyes == "normal":
            m.sphere("Eye" + side, H.size(EYE_R * 2), H.point(ec), "eye_white", joint=joint)
            look = np.array([-sx * 0.12, -1.0, 0.04])
            look /= np.linalg.norm(look)
            iris_c = np.asarray(ec) + look * (EYE_R - 0.004)
            m.sphere("Iris" + side, H.size((e["iris"] * 2, 0.012, e["iris"] * 2)), H.point(iris_c),
                     iris, rot=(0, 0, math.degrees(math.atan2(look[0], -look[1]))), joint=joint)
            pupil_c = np.asarray(ec) + look * (EYE_R + 0.0015)
            m.sphere("Pupil" + side, H.size((e["pupil"] * 2, 0.008, e["pupil"] * 2)),
                     H.point(pupil_c), "pupil",
                     rot=(0, 0, math.degrees(math.atan2(look[0], -look[1]))), joint=joint)
        else:
            m.sphere("Eye" + side, H.size(EYE_R * 2.04), H.point(ec), eyes, joint=joint)

    # Part-version proxies (one Roblox part each)
    m.sphere("HeadProxy", H.size((0.62, 0.86, 1.0)), H.point((0, -0.02, 0.0)), base, joint=joint,
             role="proxy")
    m.cylinder("NeckProxy", H.size(0.165), H.size(-0.25 - neck_bottom),
               H.point((0, 0.07, (neck_bottom - 0.25) / 2)), base, joint=joint, role="proxy")
    m.sphere("NoseProxy", H.size((0.09, 0.12, 0.17)), H.point((0, -0.47, -0.1)), "skin_shade",
             joint=joint, role="proxy")
    m.sphere("MouthProxy", H.size((e["mouth_w"] * 2, 0.08, e["mouth_open"] * 2.4)),
             H.point((0, -0.43, -0.272 + e["corner"] * 0.004)), "mouth", joint=joint,
             role="proxy")
    m.box("TeethProxy", H.size((e["mouth_w"] * 1.6, 0.02, 0.026)),
          H.point((0, -0.462, -0.272 + e["mouth_open"] * 0.55)), "teeth", joint=joint,
          role="proxy")
    for side, sx in (("L", 1), ("R", -1)):
        (x0, z0), (x1, z1) = e["brow"][0], e["brow"][-1]
        ang = math.degrees(math.atan2(z1 - z0, x1 - x0))
        m.box("BrowProxy" + side, H.size((0.17, 0.03, 0.032)),
              H.point((sx * (x0 + x1) / 2, -0.405, (z0 + z1) / 2 + 0.01)), "brow",
              rot=(0, sx * ang, sx * 14), joint=joint, role="proxy")
        m.sphere("EarProxy" + side, H.size((0.07, 0.13, 0.22)), H.point((sx * 0.31, 0.07, -0.03)),
                 "skin_shade", joint=joint, role="proxy")
    return H


# ======================================================================================
# Toilet
# ======================================================================================

BOWL_C = (0.0, -0.1)


def toilet_body_field():
    cx, cy = BOWL_C
    bowl = S.ellipsoid((cx, cy, 1.98), (1.14, 1.44, 1.05))
    bowl = S.intersect(bowl, S.half_space((0, 0, 2.03), (0, 0, 1)), k=0.05)
    pedestal = S.cylinder((0, 0.18, 0.62), 0.54, 0.6, sy=1.32, round_r=0.05)
    foot = S.cylinder((0, 0.18, 0.08), 0.76, 0.08, sy=1.33, round_r=0.06)
    trap = S.tube_path([(0, 0.4, 0.32), (0, 0.82, 0.55), (0, 1.0, 1.0), (0, 0.9, 1.45)],
                       [0.36, 0.36, 0.34, 0.3])
    deck = S.round_box((0, 1.12, 1.66), (0.72, 0.45, 0.38), 0.18)
    body = S.union(pedestal, foot, k=0.22)
    body = S.union(body, trap, k=0.2)
    body = S.union(body, bowl, k=0.35)
    body = S.union(body, deck, k=0.22)
    rim = S.torus((cx, cy, 1.99), 1.02, 0.1, sx=1.0, sy=1.27)
    body = S.union(body, rim, k=0.06)
    cavity = S.ellipsoid((cx, cy - 0.04, 2.1), (0.9, 1.17, 0.72))
    body = S.subtract(body, cavity, k=0.06)
    bolts = S.mirror_x(S.ellipsoid((0.66, 0.2, 0.13), (0.1, 0.1, 0.08)))
    return S.union(body, bolts, k=0.04)


def water_level_radii(z=1.8):
    rz = 0.72
    f = math.sqrt(max(1 - ((z - 2.1) / rz) ** 2, 0))
    return 0.9 * f, 1.17 * f
