"""Sequence 1 'The Sky Breaks': procedural 2D previs prototype.

Shot order and durations are read from data/shots/s01.yaml, so this render always matches
the storyboard. Each shot has a render function below, named after its shot ID.

    python3 render.py --out s01_16x9.mp4 [--scale 0.5] [--shots S01_060,S01_080] [--png DIR]

Renders a 16:9 open-gate picture. The 2.39:1 scope master is a centre extraction of it
(make_video.sh does both). This is previs: stylised drawing, captions in place of recorded
dialogue.
"""
import argparse
import math
import os
import subprocess
import sys
from multiprocessing import Pool

import cairo
import numpy as np
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'tools'))
import common as C  # noqa: E402

FPS = 24
W, H = 1920, 1080
S = 1.0          # resolution scale relative to 1920
SCOPE = 804      # 2.39:1 extraction height at 1920 wide
CAPTIONS = {     # shot id: [(start, end, text)] in shot-local seconds
    'S01_150': [(0.8, 3.9, 'Every world believes it is the exception.')],
    'S01_160': [(1.5, 3.45, 'Every world learns the truth.')],
}
G = {}           # per-process asset cache


# ------------------------------------------------------------------ utilities

def ease(x):
    x = min(max(x, 0.0), 1.0)
    return x * x * (3 - 2 * x)


def lerp(a, b, t):
    return a + (b - a) * t


def rng(seed):
    return np.random.default_rng(seed)


def spectral_noise(n, beta, seed):
    """Tileable fractal noise in [0,1] by spectral synthesis."""
    r = rng(seed)
    f = np.fft.fftfreq(n)
    fx, fy = np.meshgrid(f, f)
    k = np.sqrt(fx * fx + fy * fy)
    k[0, 0] = 1
    spec = (r.normal(size=(n, n)) + 1j * r.normal(size=(n, n))) / k ** (beta / 2)
    spec[0, 0] = 0
    img = np.real(np.fft.ifft2(spec))
    img = (img - img.min()) / (img.max() - img.min())
    return img.astype(np.float32)


def sample(tex, u, v):
    """Bilinear wrap sampling; u, v in texel units."""
    n0, n1 = tex.shape
    x0 = np.floor(u).astype(np.int64)
    y0 = np.floor(v).astype(np.int64)
    fx = (u - x0).astype(np.float32)
    fy = (v - y0).astype(np.float32)
    x0 %= n1
    y0 %= n0
    x1 = (x0 + 1) % n1
    y1 = (y0 + 1) % n0
    a = tex[y0, x0] * (1 - fx) + tex[y0, x1] * fx
    b = tex[y1, x0] * (1 - fx) + tex[y1, x1] * fx
    return a * (1 - fy) + b * fy


def surface():
    s = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
    return s, cairo.Context(s)


def to_np(surf):
    """Cairo ARGB32 (premultiplied BGRA) to float RGBA premultiplied."""
    surf.flush()
    a = np.ndarray((H, W, 4), np.uint8, surf.get_data()).astype(np.float32) / 255.0
    return a[..., [2, 1, 0, 3]]


def over(dst, src):
    """Composite premultiplied RGBA src over RGB dst."""
    return src[..., :3] + dst * (1 - src[..., 3:4])


def add(dst, src_rgb, k=1.0):
    return dst + src_rgb * k


def blur(img, sigma):
    if sigma <= 0:
        return img
    f = 4 if sigma > 6 else 1
    if f > 1:
        small = img[::f, ::f]
        sm = ndimage.gaussian_filter(small, (sigma / f, sigma / f) + (0,) * (img.ndim - 2))
        out = np.repeat(np.repeat(sm, f, 0), f, 1)[:img.shape[0], :img.shape[1]]
        return ndimage.uniform_filter(out, (f, f) + (1,) * (img.ndim - 2))
    return ndimage.gaussian_filter(img, (sigma, sigma) + (0,) * (img.ndim - 2))


def glow(img, sigma, k):
    return img + blur(np.clip(img - 0.6, 0, None), sigma * S) * k


def grid():
    if 'grid' not in G:
        G['grid'] = np.meshgrid(np.arange(W, dtype=np.float32), np.arange(H, dtype=np.float32))
    return G['grid']


def vgrad(top, bottom, y0=0.0, y1=1.0):
    y = np.linspace(0, 1, H, dtype=np.float32)
    t = np.clip((y - y0) / max(y1 - y0, 1e-6), 0, 1)[:, None, None]
    img = np.empty((H, W, 3), np.float32)
    img[:] = np.array(top, np.float32) * (1 - t) + np.array(bottom, np.float32) * t
    return img


def rain(ctx, t, n, seed, color=(0.75, 0.8, 0.9), alpha=0.25, length=40, speed=1400, angle=0.26,
         width=1.2, frozen_at=None, region=None):
    """Rain streaks. frozen_at=(t_freeze, t_release): drops stop as beads in between."""
    r = rng(seed)
    x0 = r.uniform(-0.2, 1.2, n) * W
    y0 = r.uniform(0, 1, n) * H
    sp = r.uniform(0.7, 1.3, n) * speed * S
    tt = t
    beads = False
    if frozen_at and frozen_at[0] <= t < frozen_at[1]:
        tt = frozen_at[0]
        beads = True
    elif frozen_at and t >= frozen_at[1]:
        tt = t - (frozen_at[1] - frozen_at[0])
    dx, dy = math.sin(angle), math.cos(angle)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    for i in range(n):
        y = (y0[i] + sp[i] * tt) % (H * 1.1) - 0.05 * H
        x = x0[i] + y * math.tan(angle)
        if region and not region(x, y):
            continue
        if beads:
            rad = (2.0 + 1.5 * (i % 3)) * S
            ctx.set_source_rgba(color[0], color[1], color[2], alpha * 2.2)
            ctx.arc(x, y, rad, 0, 2 * math.pi)
            ctx.fill()
            ctx.set_source_rgba(1, 1, 1, alpha * 2.5)
            ctx.arc(x - rad * 0.3, y - rad * 0.3, rad * 0.35, 0, 2 * math.pi)
            ctx.fill()
        else:
            ln = length * S * (sp[i] / (speed * S))
            ctx.set_source_rgba(color[0], color[1], color[2], alpha)
            ctx.set_line_width(width * S)
            ctx.move_to(x, y)
            ctx.line_to(x - dx * ln, y - dy * ln)
            ctx.stroke()


def caption(ctx, text, alpha=1.0):
    ctx.select_font_face('Inter', cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
    ctx.set_font_size(34 * S)
    ext = ctx.text_extents(text)
    x = (W - ext.width) / 2 - ext.x_bearing
    y = H / 2 + SCOPE * S / 2 - 70 * S
    ctx.set_source_rgba(0, 0, 0, 0.55 * alpha)
    for ox, oy in ((2, 2), (-1, 1), (1, -1), (0, 3)):
        ctx.move_to(x + ox * S, y + oy * S)
        ctx.show_text(text)
    ctx.set_source_rgba(0.96, 0.95, 0.92, alpha)
    ctx.move_to(x, y)
    ctx.show_text(text)


# ------------------------------------------------------------------ shared assets

def city_texture():
    """Top-down night city (Manhattan-like island in a harbor), 2048 px, RGB float."""
    if 'city' in G:
        return G['city']
    n = 2048
    yy, xx = np.meshgrid(np.arange(n, dtype=np.float32), np.arange(n, dtype=np.float32), indexing='ij')
    nz = spectral_noise(n, 2.2, 11)
    fine = spectral_noise(n, 0.6, 12)
    # island: rotated ellipse + noisy shore; mainland on both sides
    cx, cy = n * 0.5, n * 0.5
    ang = math.radians(29)
    u = (xx - cx) * math.cos(ang) + (yy - cy) * math.sin(ang)
    v = -(xx - cx) * math.sin(ang) + (yy - cy) * math.cos(ang)
    island = ((u / (n * 0.12)) ** 2 + (v / (n * 0.5)) ** 2) < 1 + (nz - 0.5) * 0.6
    left = u < -n * 0.2 + (nz - 0.5) * 300
    right = u > n * 0.19 + (nz - 0.5) * 300
    harbor = (v > n * 0.28) & (np.abs(u) < n * 0.35)
    land = (island | left | right) & ~(harbor & ~island)
    # streets: grid in the rotated frame
    su = np.abs(((u / 70.0) % 1) - 0.5)
    sv = np.abs(((v / 26.0) % 1) - 0.5)
    street = np.clip(1 - np.minimum(su * 30, sv * 14), 0, 1) ** 1.5
    lights = (fine > 0.62) * (fine - 0.62) * 6
    lum = land * (0.55 * street * (0.5 + fine) + lights * 1.2 + 0.015 * nz)
    lum = ndimage.gaussian_filter(lum, 0.7)
    col = np.zeros((n, n, 3), np.float32)
    col[..., 0] = lum * 1.0
    col[..., 1] = lum * 0.62
    col[..., 2] = lum * 0.3
    water = ~land
    col[water] = (0.004, 0.008, 0.016)
    G['city'] = col
    return col


def skyline_layer(seed, n, hmin, hmax, wmin, wmax, base, color, win_density, width_px, spire_p=0.15,
                  lamp=True):
    """Pre-rendered skyline strip (RGBA premultiplied) wider than the frame for parallax."""
    key = ('sky', seed, W)
    if key in G:
        return G[key]
    r = rng(seed)
    sw = int(width_px)
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, sw, H)
    ctx = cairo.Context(surf)
    lamps = []
    x = -50.0
    while x < sw:
        w = r.uniform(wmin, wmax) * S
        h = r.uniform(hmin, hmax) * S * (1.6 if r.random() < 0.08 else 1.0)
        top = base - h
        ctx.set_source_rgb(*color)
        ctx.rectangle(x, top, w, H - top)
        ctx.fill()
        if r.random() < 0.35:   # setback tower
            w2, h2 = w * r.uniform(0.4, 0.7), h * r.uniform(0.1, 0.3)
            ctx.rectangle(x + (w - w2) / 2, top - h2, w2, h2 + 1)
            ctx.fill()
            top -= h2
        if r.random() < spire_p:
            ctx.set_line_width(2 * S)
            ctx.move_to(x + w / 2, top)
            ctx.line_to(x + w / 2, top - h * 0.18)
            ctx.stroke()
            lamps.append((x + w / 2, top - h * 0.18))
        elif lamp and r.random() < 0.3:
            lamps.append((x + w / 2, top))
        # windows
        cw, ch = 4.0 * S * (wmax / 120), 3.0 * S * (wmax / 120)
        cols = int(w / (cw * 2.2))
        rows = int((base - (base - h)) / (ch * 2.4))
        tint = r.choice([(1.0, 0.78, 0.45), (0.95, 0.85, 0.65), (0.7, 0.85, 1.0)])
        lit = r.random(size=(rows, cols)) < win_density * r.uniform(0.5, 1.4)
        for i in range(rows):
            for j in range(cols):
                if lit[i, j]:
                    b = r.uniform(0.35, 1.0)
                    ctx.set_source_rgb(tint[0] * b, tint[1] * b, tint[2] * b)
                    ctx.rectangle(x + j * cw * 2.2 + cw * 0.6, base - h + i * ch * 2.4 + ch, cw, ch)
                    ctx.fill()
        x += w + r.uniform(0, 12) * S
    surf.flush()
    a = np.ndarray((H, sw, 4), np.uint8, surf.get_data()).astype(np.float32)[..., [2, 1, 0, 3]] / 255.0
    G[key] = (a, lamps)
    return G[key]


def blit_layer(img, layer, offset, yshift=0, k=1.0):
    a, _ = layer
    sw = a.shape[1]
    o = int(offset) % max(sw - W, 1)
    part = a[:, o:o + W]
    if yshift:
        part = np.roll(part, int(yshift), axis=0)
    return part[..., :3] * k + img * (1 - part[..., 3:4])


def lamps(ctx, layer, offset, t, yshift=0, size=3.0):
    _, ls = layer
    on = (t % 1.0) < 0.5
    if not on:
        return
    for (x, y) in ls:
        xx = x - offset
        if -10 < xx < W + 10:
            ctx.set_source_rgba(1, 0.12, 0.08, 0.95)
            ctx.arc(xx, y + yshift, size * S, 0, 2 * math.pi)
            ctx.fill()


def rupture_layer(cx, cy, radius, t, open_amt, seed=5, lattice=0.0):
    """Emissive rupture ring + dark violet interior with stars + hex lattice (RGB, additive)."""
    X, Y = grid()
    dx, dy = X - cx, Y - cy
    r = np.sqrt(dx * dx + dy * dy) + 1e-3
    out = np.zeros((H, W, 3), np.float32)
    if radius > 1:
        ring = np.exp(-((r - radius) / (radius * 0.035 + 2 * S)) ** 2)
        halo = np.exp(-np.abs(r - radius) / (radius * 0.18 + 8 * S)) * 0.35
        theta = np.arctan2(dy, dx)
        flick = 0.85 + 0.15 * np.sin(theta * 9 + t * 3.0)
        out += (ring * 2.2 * flick + halo)[..., None] * np.array([0.85, 0.35, 1.0], np.float32)
        out += (ring * 1.2)[..., None] * np.array([0.6, 0.6, 1.0], np.float32)
        inside = np.clip((radius - r) / (radius * 0.04 + 1), 0, 1)
        out += inside[..., None] * np.array([0.05, 0.0, 0.1], np.float32) * open_amt
    if lattice > 0:
        # hex lattice: distance to hex grid edges in a scaled frame
        sc = 46.0 * S
        q = (dx / sc) * (2 / 3)
        rr = (-dx / 3 + math.sqrt(3) / 3 * dy) / sc
        # cube rounding
        xq, zq = q, rr
        yq = -xq - zq
        rx, ry, rz = np.round(xq), np.round(yq), np.round(zq)
        ddx, ddy, ddz = np.abs(rx - xq), np.abs(ry - yq), np.abs(rz - zq)
        edge = np.maximum(np.maximum(ddx, ddy), ddz)
        line = np.clip((edge - 0.42) / 0.08, 0, 1)
        front = lattice
        mask = np.clip((front - r) / (60 * S), 0, 1) * np.exp(-np.maximum(r - radius, 0) / (front * 0.5 + 1))
        rings = np.clip(1 - np.abs(((r / (radius * 0.5 + 30 * S)) % 1) - 0.5) * 12, 0, 1) * 0.5
        out += ((line + rings) * mask * 0.55)[..., None] * np.array([0.9, 0.4, 1.0], np.float32)
    return out


def stars_into(img, mask, seed, n=1400, bright=0.8):
    r = rng(seed)
    xs = r.integers(0, W, n)
    ys = r.integers(0, H, n)
    b = r.uniform(0.15, 1.0, n) ** 3 * bright
    m = mask[ys, xs] > 0.5
    img[ys[m], xs[m]] += b[m, None] * np.array([0.9, 0.92, 1.0], np.float32)
    return img


def violet_grade(img, k):
    """Shift city sodium light toward violet as the rupture opens."""
    if k <= 0:
        return img
    lum = img @ np.array([0.3, 0.55, 0.15], np.float32)
    viol = lum[..., None] * np.array([1.05, 0.55, 1.45], np.float32)
    return img * (1 - 0.65 * k) + viol * 0.65 * k


# ------------------------------------------------------------------ shots

def S01_010(t, d):
    """Earth from orbit."""
    u = t / d
    X, Y = grid()
    sc = lerp(1.0, 1.12, ease(u))
    px, py = 0.66 * W, 0.62 * H                       # push-in target: the NE corridor
    Xs = (X - px) / sc + px
    Ys = (Y - py) / sc + py
    R = 2.7 * W
    cx, cy = 0.40 * W, 0.30 * H + R
    nx = (Xs - cx) / R
    ny = (Ys - cy) / R
    rr = nx * nx + ny * ny
    inside = rr < 1
    nz = np.sqrt(np.clip(1 - rr, 0, 1))
    # camera looks at lat0 from above; rotate about x
    lat0 = math.radians(-34)   # the frame shows the cap ~70 deg up from the sub-camera point
    x3, y3, z3 = nx, -ny, nz
    y4 = y3 * math.cos(lat0) + z3 * math.sin(lat0)
    z4 = -y3 * math.sin(lat0) + z3 * math.cos(lat0)
    lon = np.degrees(np.arctan2(x3, z4)) - 81 - t * 0.05
    lat = np.degrees(np.arcsin(np.clip(y4, -1, 1)))
    if 'earth' not in G:
        G['earth'] = (spectral_noise(1024, 2.0, 1), spectral_noise(1024, 1.7, 2),
                      spectral_noise(1024, 0.8, 3))
    n1, n2, n3 = G['earth']
    tu = (lon / 360.0) * 1024 * 3
    tv = (0.5 - lat / 180.0) * 1024 * 3
    coast = (np.interp(lat, [24, 30, 33, 35, 37, 38.5, 40.7, 42, 43.5, 45, 47, 50, 56],
                       [-80, -81.3, -79, -76, -75.8, -75.2, -74, -70.5, -69.5, -66, -61, -59, -61])
             + (sample(n2, tu * 9, tv * 9) - 0.5) * 2.2)
    gulf = np.clip((30.3 - lat) / 0.5, 0, 1) * np.clip((-82.5 + 0.35 * (lat - 27) - lon) / 0.5, 0, 1)
    land = np.clip((coast - lon) / 0.4, 0, 1) * (1 - gulf)
    cloud = np.clip((sample(n1, tu * 2.0 + 40 + t * 0.6, tv * 2.0) - 0.56) * 3.0, 0, 1)
    # lights: coast-hugging corridor + scattered towns
    dcoast = np.clip(1 - (coast - lon) / 6.0, 0, 1) * land
    towns = np.clip((sample(n3, tu * 9, tv * 9) - 0.6) * 7, 0, 1)
    hubs = np.zeros_like(lat)
    for la, lo, s in ((42.36, -71.1, 1.1), (40.71, -74.0, 2.0), (39.95, -75.2, 1.0), (39.3, -76.6, 0.8),
                      (38.9, -77.0, 1.0), (35.2, -80.8, 0.6), (33.75, -84.4, 0.9), (40.4, -80.0, 0.6),
                      (45.5, -73.6, 0.8), (43.65, -79.4, 1.0), (41.9, -87.6, 1.3), (25.8, -80.2, 0.8),
                      (28.5, -81.4, 0.5), (36.85, -76.3, 0.5), (42.9, -78.9, 0.4), (41.5, -81.7, 0.6)):
        hubs += np.exp(-(((lat - la) / 0.2) ** 2 + ((lon - lo) / 0.26) ** 2)) * s * 0.7
    lights = (towns * (0.6 + 2.5 * dcoast) + hubs * 3.0) * land
    # sun just below the eastern limb
    sun = np.array([0.80, 0.12, -0.60])
    sun /= np.linalg.norm(sun)
    ndl = nx * sun[0] + (-ny) * sun[1] + nz * sun[2]
    day = np.clip((nx - 0.172) / 0.05, 0, 1) ** 2 * 0.85
    ocean_n = np.array([0.008, 0.016, 0.04], np.float32)
    land_n = np.array([0.006, 0.006, 0.007], np.float32)
    base = ocean_n * (1 - land[..., None]) + land_n * land[..., None]
    img = base + day[..., None] * (np.array([0.05, 0.16, 0.4], np.float32) * (1 - land[..., None])
                                   + np.array([0.22, 0.2, 0.12], np.float32) * land[..., None])
    img += (lights * (1 - cloud * 0.8))[..., None] * np.array([1.0, 0.68, 0.32], np.float32) * 0.9
    moon = np.clip(0.35 + 0.65 * (nz * 0.6 + nx * -0.3 + 0.2), 0, 1)
    cl = cloud[..., None] * (np.array([0.06, 0.07, 0.1], np.float32) * moon[..., None]
                             + day[..., None] * np.array([0.9, 0.85, 0.8], np.float32))
    img = img * (1 - cloud[..., None] * 0.7) + cl
    # storm-cell lightning flashes
    for tf in (2.1, 4.6):
        if tf <= t < tf + 0.12:
            k = 1 - (t - tf) / 0.12
            fl = np.exp(-(((lat - 31) / 2.0) ** 2 + ((lon + 58) / 2.5) ** 2)) * cloud * 2.5 * k
            img += fl[..., None] * np.array([0.7, 0.75, 1.0], np.float32)
    # atmosphere
    limb = np.clip(1 - nz, 0, 1)
    rim_col = np.array([0.25, 0.5, 1.0], np.float32)
    img += (limb ** 4 * 0.9)[..., None] * rim_col * (0.25 + 0.75 * day[..., None])
    img *= inside[..., None]
    r = np.sqrt(rr)
    halo = np.exp(-np.clip(r - 1, 0, None) / 0.004) * (~inside)
    sunside = np.clip(nx * 1.6 + 0.4, 0.15, 1.6)
    hal_col = rim_col[None, None, :] * (halo * sunside)[..., None] * 0.8
    dawn = np.exp(-((nx - 0.55) / 0.12) ** 2) * halo
    hal_col += dawn[..., None] * np.array([1.0, 0.55, 0.25], np.float32) * 1.2
    img += hal_col
    img = stars_into(img, (~inside).astype(np.float32) * (halo < 0.05), 7)
    # satellite (foreground, slightly defocused)
    s, ctx = surface()
    su = (t - 0.6) / 4.5
    if -0.1 < su < 1.15:
        sx = lerp(-0.15, 1.15, su) * W
        sy = lerp(0.80, 0.74, su) * H
        ctx.translate(sx, sy)
        ctx.rotate(-0.12 + su * 0.05)
        sz = 0.09 * W
        ctx.set_source_rgb(0.05, 0.05, 0.06)
        ctx.rectangle(-sz * 0.12, -sz * 0.1, sz * 0.24, sz * 0.2)
        ctx.fill()
        for sgn in (-1, 1):
            ctx.set_source_rgb(0.06, 0.08, 0.13)
            ctx.rectangle(sgn * sz * 0.15 if sgn > 0 else -sz * 0.75, -sz * 0.07, sz * 0.6, sz * 0.14)
            ctx.fill()
            ctx.set_source_rgba(0.3, 0.45, 0.7, 0.35)
            ctx.set_line_width(1 * S)
            for k in range(6):
                xx = (sz * 0.15 if sgn > 0 else -sz * 0.75) + k * sz * 0.1
                ctx.move_to(xx, -sz * 0.07)
                ctx.line_to(xx, sz * 0.07)
            ctx.stroke()
        ctx.set_source_rgba(0.85, 0.75, 0.55, 0.6)
        ctx.rectangle(-sz * 0.12, -sz * 0.1, sz * 0.24, sz * 0.03)
        ctx.fill()
        ctx.identity_matrix()
        sat = blur(to_np(s), 1.6 * S)
        img = over(img, sat)
        if 2.8 < t < 3.6:   # glint
            k = math.sin((t - 2.8) / 0.8 * math.pi)
            gx, gy = sx + sz * 0.3, sy - sz * 0.02
            d2 = ((X - gx) ** 2 + (Y - gy) ** 2)
            img += (np.exp(-d2 / (30 * S) ** 2) * 2.5 * k)[..., None]
            streak = np.exp(-((Y - gy) / (2.5 * S)) ** 2) * np.exp(-np.abs(X - gx) / (260 * S)) * k * 0.9
            img += streak[..., None] * np.array([0.7, 0.8, 1.0], np.float32)
    return glow(img, 6, 0.6)


def S01_020(t, d):
    """Through the cloud deck."""
    u = t / d
    X, Y = grid()
    city = city_texture()
    if 'cl' not in G:
        G['cl'] = (spectral_noise(1024, 2.4, 21), spectral_noise(1024, 2.0, 22))
    c1, c2 = G['cl']
    # city seen from above, zooming in as we descend
    zc = lerp(0.55, 1.2, ease(u))
    cu = (X - W * 0.62) / (zc * S) + 1024
    cv = (Y - H * 0.55) / (zc * S) + 1024
    img = np.stack([sample(city[..., k], cu, cv) for k in range(3)], -1) * 1.6
    img = blur(img, 1.0 * S)
    # cloud layers (zoom outward)
    for i, (tex, base, rate, thr) in enumerate(((c1, 0.6, 1.8, 0.56), (c2, 0.9, 2.6, 0.6), (c1, 1.3, 3.8, 0.63))):
        z = base * (1 + rate * u)
        uu = (X - W / 2) / (z * S * 1.3) + 300 * i
        vv = (Y - H / 2) / (z * S * 1.3) + 170 * i
        n = sample(tex, uu, vv)
        a = np.clip((n - thr) * 4.5, 0, 1) * (1 - 0.6 * ease((u - 0.55) / 0.45) * (i == 0))
        top = np.array([0.2, 0.22, 0.28], np.float32) * (0.4 + n[..., None])
        warm = np.array([0.16, 0.08, 0.04], np.float32) * (1 - n[..., None]) * 0.6
        img = img * (1 - a[..., None]) + (top * 0.55 + warm) * a[..., None]
    # horizon enters at the end (tilt up)
    hz = lerp(-0.15, 0.16, ease((u - 0.7) / 0.3)) * H
    sky = np.clip((hz - Y) / (40 * S), 0, 1)[..., None]
    img = img * (1 - sky) + sky * vgrad((0.01, 0.012, 0.025), (0.12, 0.07, 0.05), 0, 0.2)
    s, ctx = surface()
    if u > 0.82:
        rain(ctx, t, 160, 3, alpha=0.18 * (u - 0.82) / 0.18, length=60)
    return glow(over(img, to_np(s)), 5, 0.5)


def skyline_layers():
    far = skyline_layer(101, 0, 70, 190, 30, 70, 0.62 * H, (0.035, 0.04, 0.055), 0.28, W * 1.6)
    mid = skyline_layer(102, 0, 110, 300, 50, 120, 0.66 * H, (0.025, 0.028, 0.04), 0.32, W * 1.9)
    near = skyline_layer(103, 0, 120, 380, 80, 190, 0.70 * H, (0.016, 0.018, 0.026), 0.3, W * 2.6, 0.25)
    return far, mid, near


def low_cloud(img, t, y0, y1, drift, k=1.0, seed=31):
    X, Y = grid()
    if ('lc', seed) not in G:
        G[('lc', seed)] = spectral_noise(1024, 2.3, seed)
    n = sample(G[('lc', seed)], X / (1.6 * S) + drift + t * 6, Y / (0.7 * S))
    band = np.clip((Y - y0) / (y1 - y0), 0, 1)
    dens = np.clip((n - 0.35) * 2.2, 0, 1) * (1 - band) * np.clip(Y / max(y0, 1), 0, 1)
    col = np.array([0.28, 0.16, 0.09], np.float32) * (0.55 + n[..., None]) * k
    a = (dens * 0.9)[..., None]
    return img * (1 - a) + col * a


def S01_030(t, d):
    """Skyline in rain, across the river."""
    far, mid, near = skyline_layers()
    img = vgrad((0.03, 0.03, 0.045), (0.2, 0.11, 0.06), 0.0, 0.62)
    img = blit_layer(img, far, 200 + t * 10 * S)
    img = low_cloud(img, t, 0.06 * H, 0.42 * H, 0, 0.8)
    img = blit_layer(img, mid, 300 + t * 26 * S)
    img = blit_layer(img, near, 500 + t * 48 * S)
    img = low_cloud(img, t, 0.0, 0.3 * H, 400, 0.9, 32)
    s, ctx = surface()
    lamps(ctx, mid, 300 + t * 26 * S, t)
    lamps(ctx, near, 500 + t * 48 * S, t + 0.3)
    img = over(img, to_np(s))
    # river reflection
    X, Y = grid()
    hz = int(0.70 * H)
    refl = img[hz - (np.arange(H) - hz).clip(0, hz - 1)]
    wob = (np.sin(Y[hz:] * 0.09 + t * 4) * 6 + np.sin(Y[hz:] * 0.023 - t * 2) * 10) * S
    xs = np.clip((X[hz:] + wob).astype(int), 0, W - 1)
    rr = refl[hz:][np.arange(H - hz)[:, None], xs]
    rr = ndimage.gaussian_filter(rr, (6 * S, 1.5 * S, 0)) * 0.75
    img[hz:] = rr + np.array([0.004, 0.006, 0.012], np.float32)
    # ferry
    fx = (1.1 - (t / d) * 0.35) * W
    s, ctx = surface()
    ctx.set_source_rgb(0.02, 0.02, 0.025)
    ctx.rectangle(fx, 0.715 * H, 90 * S, 10 * S)
    ctx.fill()
    for k in range(9):
        ctx.set_source_rgba(1, 0.85, 0.5, 0.9)
        ctx.rectangle(fx + 6 * S + k * 9 * S, 0.718 * H, 4 * S, 3 * S)
        ctx.fill()
    # pier pilings (foreground parallax)
    for k in range(6):
        px = ((k * 420 - t * 210) * S) % (W + 400 * S) - 200 * S
        ctx.set_source_rgb(0.008, 0.008, 0.01)
        ctx.rectangle(px, 0.78 * H, 34 * S, 0.3 * H)
        ctx.fill()
    rain(ctx, t, 420, 4, alpha=0.16, length=34)
    rain(ctx, t, 120, 5, alpha=0.24, length=70, width=2.0, speed=2200)
    img = over(img, to_np(s))
    return glow(img, 8, 0.7)


def project(Xw, Yw, Zw, cam_z, f, cx, cy, cam_h=1.5, cam_x=0.0):
    z = Zw - cam_z
    return cx + f * (Xw - cam_x) / z, cy - f * (Yw - cam_h) / z, z


def S01_040(t, d):
    """Street level: pedestrians, traffic, rain."""
    s, ctx = surface()
    f = (W / 2) / math.tan(math.radians(27))
    cx, cy = W * 0.5, H * 0.43
    cz = t * 1.2
    r = rng(40)
    # sky slit
    ctx.set_source_rgb(0.14, 0.08, 0.05)
    ctx.paint()
    # road
    ctx.set_source_rgb(0.012, 0.012, 0.016)
    ctx.rectangle(0, cy, W, H - cy)
    ctx.fill()
    # facades: left (x=-14) and right (x=+14) slabs from far to near
    blds = G.setdefault('blds040', [(side, z0, r.uniform(8, 26), r.uniform(25, 140), r.random())
                                    for side in (-1, 1) for z0 in np.cumsum(r.uniform(8, 26, 40)) + 4])
    lights = []
    for side, z0, depth, h, seed in sorted(blds, key=lambda b: -b[1]):
        z1 = z0 + depth
        if z0 - cz < 1.0:
            continue
        xw = 14 * side
        (ax, ay0, _), (bx, by0, _) = project(xw, 0, z1, cz, f, cx, cy), project(xw, 0, z0, cz, f, cx, cy)
        _, ay1, _ = project(xw, h, z1, cz, f, cx, cy)
        _, by1, _ = project(xw, h, z0, cz, f, cx, cy)
        haze = min(1.0, (z0 - cz) / 160.0)
        shade = 0.022 + 0.004 * seed
        ctx.set_source_rgb(lerp(shade, 0.12, haze), lerp(shade, 0.07, haze), lerp(shade * 1.2, 0.05, haze))
        ctx.move_to(ax, ay0)
        ctx.line_to(ax, ay1)
        ctx.line_to(bx, by1)
        ctx.line_to(bx, by0)
        ctx.close_path()
        ctx.fill()
        # windows
        rr = rng(int(seed * 1e6))
        for fl in range(2, int(h / 3.5)):
            for wi in range(int(depth / 2.5)):
                if rr.random() < 0.45:
                    zz = z0 + wi * 2.5 + 0.6
                    x0, y0, _ = project(xw, fl * 3.5, zz, cz, f, cx, cy)
                    x1, y1, _ = project(xw, fl * 3.5 + 1.6, zz + 1.4, cz, f, cx, cy)
                    b = rr.uniform(0.3, 0.9)
                    ctx.set_source_rgba(1.0 * b, 0.8 * b, 0.5 * b, 0.9)
                    ctx.rectangle(min(x0, x1), min(y0, y1), abs(x1 - x0) + 0.5, abs(y1 - y0) + 0.5)
                    ctx.fill()
        # storefront glow
        x0, y0, _ = project(xw, 0.2, z0, cz, f, cx, cy)
        x1, y1, _ = project(xw, 2.8, z1, cz, f, cx, cy)
        hue = [(1.0, 0.6, 0.3), (0.4, 0.8, 1.0), (1.0, 0.3, 0.5), (1.0, 0.85, 0.6)][int(seed * 4)]
        ctx.set_source_rgba(hue[0], hue[1], hue[2], 0.22)
        ctx.rectangle(min(x0, x1), min(y0, y1), abs(x1 - x0), abs(y1 - y0))
        ctx.fill()
        lights.append(((x0 + x1) / 2, max(y0, y1), hue, abs(x1 - x0)))
    img = to_np(s)[..., :3]
    # cars
    s2, c2 = surface()
    for k in range(14):
        lane = [-7.5, -3.8, 3.8, 7.5][k % 4]
        onc = lane < 0
        zc = ((k * 23.0 + (-11 if onc else 6) * t) % 220) + 6 + cz
        x, y, z = project(lane, 0.7, zc, cz, f, cx, cy)
        if z < 2:
            continue
        sz = f / z
        col = (1.0, 0.95, 0.85) if onc else (1.0, 0.08, 0.05)
        c2.set_source_rgb(0.01, 0.01, 0.012)
        c2.rectangle(x - sz * 0.9, y - sz * 0.9, sz * 1.8, sz * 0.9)
        c2.fill()
        for sgn in (-1, 1):
            c2.set_source_rgba(col[0], col[1], col[2], 1)
            c2.arc(x + sgn * sz * 0.7, y - sz * 0.25, max(sz * 0.11, 1.2 * S), 0, 2 * math.pi)
            c2.fill()
            lights.append((x + sgn * sz * 0.7, y + sz * 0.6, col, sz * 0.25))
    # yellow taxi near camera splashing
    # pedestrians with umbrellas
    for k in range(16):
        side = -1 if k % 2 else 1
        xw = side * r.uniform(8.5, 12.5) if False else side * (8.8 + (k * 0.37) % 3.4)
        dirn = 1 if k % 3 else -1
        zc = ((k * 13.0 + dirn * 1.3 * t) % 120) + 3 + cz
        x, y, z = project(xw, 0.0, zc, cz, f, cx, cy)
        if z < 1.6:
            continue
        sz = f / z
        phase = math.sin(t * 7 + k)
        c2.set_source_rgb(0.012, 0.012, 0.016)
        c2.rectangle(x - sz * 0.22, y - sz * 1.45, sz * 0.44, sz * 1.0)
        c2.fill()
        for leg in (-1, 1):
            c2.set_line_width(sz * 0.12)
            c2.move_to(x + leg * sz * 0.08, y - sz * 0.5)
            c2.line_to(x + leg * sz * 0.08 + leg * phase * sz * 0.12, y)
            c2.stroke()
        c2.arc(x, y - sz * 1.55, sz * 0.12, 0, 2 * math.pi)
        c2.fill()
        uc = [(0.08, 0.08, 0.1), (0.25, 0.05, 0.06), (0.05, 0.1, 0.2)][k % 3]
        c2.set_source_rgb(*uc)
        c2.save()
        c2.translate(x, y - sz * 1.75)
        c2.scale(sz * 0.62, sz * 0.28)
        c2.arc(0, 0, 1, math.pi, 2 * math.pi)
        c2.restore()
        c2.fill()
        c2.set_source_rgba(1, 0.75, 0.5, 0.25)
        c2.set_line_width(max(1, sz * 0.03))
        c2.save()
        c2.translate(x, y - sz * 1.75)
        c2.scale(sz * 0.62, sz * 0.28)
        c2.arc(0, 0, 1, math.pi * 1.05, math.pi * 1.6)
        c2.restore()
        c2.stroke()
    # traffic signal
    x, y, z = project(11.5, 0, 26 - 0 + 0, cz, f, cx, cy)
    sz = f / z
    c2.set_source_rgb(0.01, 0.01, 0.01)
    c2.rectangle(x - sz * 0.06, y - sz * 5, sz * 0.12, sz * 5)
    c2.fill()
    green = t >= 2.0
    c2.set_source_rgba(*(0.2, 1.0, 0.6, 1) if green else (1.0, 0.15, 0.1, 1))
    c2.arc(x, y - sz * (4.4 if green else 4.8), sz * 0.14, 0, 2 * math.pi)
    c2.fill()
    lights.append((x, y + sz * 0.5, (0.2, 1, 0.6) if green else (1, 0.15, 0.1), sz * 0.3))
    img = over(img, to_np(s2))
    # wet-road reflections: vertical streaks under every light
    s3, c3 = surface()
    for (x, y, col, wd) in lights:
        if y < cy:
            continue
        g = cairo.LinearGradient(0, y, 0, y + (H - y) * 0.6)
        g.add_color_stop_rgba(0, col[0], col[1], col[2], 0.35)
        g.add_color_stop_rgba(1, col[0], col[1], col[2], 0.0)
        c3.set_source(g)
        c3.rectangle(x - max(wd, 2 * S) / 2, y, max(wd, 2 * S), (H - y) * 0.6)
        c3.fill()
    img = add(img, blur(to_np(s3)[..., :3], 3 * S), 0.8)
    s4, c4 = surface()
    rain(c4, t, 520, 6, alpha=0.2, length=38)
    rain(c4, t, 90, 7, alpha=0.3, length=90, width=2.2, speed=2400)
    img = over(img, to_np(s4))
    return glow(img, 7, 0.8)


def street_skyline(t, point=None, ring=None, grade=0.0):
    """View from street level up at the skyline (S01_050, S01_180)."""
    far, mid, near = skyline_layers()
    img = vgrad((0.025, 0.025, 0.04), (0.18, 0.1, 0.06), 0.0, 0.75)
    if ring is not None:
        img += rupture_layer(*ring)
    yshift = int(0.12 * H)
    img = low_cloud(img, t, 0.05 * H, 0.4 * H, 0, 0.75)
    img = blit_layer(img, far, 700, yshift)
    img = blit_layer(img, mid, 900, yshift + int(0.04 * H))
    img = blit_layer(img, near, 1300, yshift + int(0.12 * H))
    s, ctx = surface()
    lamps(ctx, mid, 900, t, yshift + int(0.04 * H))
    # near buildings across the avenue (big, dark) at frame bottom
    r = rng(55)
    x = -40 * S
    while x < W:
        w = r.uniform(160, 380) * S
        top = H * r.uniform(0.62, 0.74)
        ctx.set_source_rgb(0.012, 0.012, 0.016)
        ctx.rectangle(x, top, w, H - top)
        ctx.fill()
        for i in range(int((H - top) / (22 * S))):
            for j in range(int(w / (26 * S))):
                if r.random() < 0.4:
                    b = r.uniform(0.25, 0.8)
                    ctx.set_source_rgb(b, b * 0.78, b * 0.5)
                    ctx.rectangle(x + j * 26 * S + 6 * S, top + i * 22 * S + 7 * S, 12 * S, 8 * S)
                    ctx.fill()
        x += w + 6 * S
    img = over(img, to_np(s))
    img = violet_grade(img, grade)
    if point is not None:
        X, Y = grid()
        px, py, k = point
        d2 = (X - px) ** 2 + (Y - py) ** 2
        img += (np.exp(-d2 / (2.2 * S) ** 2) * 3.0 * k)[..., None] * np.array([1.0, 0.8, 1.0], np.float32)
        img += (np.exp(-d2 / (14 * S) ** 2) * 0.35 * k)[..., None] * np.array([0.8, 0.4, 1.0], np.float32)
        spk = (np.exp(-((Y - py) / (0.9 * S)) ** 2) * np.exp(-np.abs(X - px) / (22 * S))
               + np.exp(-((X - px) / (0.9 * S)) ** 2) * np.exp(-np.abs(Y - py) / (22 * S)))
        img += (spk * 0.6 * k)[..., None] * np.array([0.9, 0.6, 1.0], np.float32)
    return img


def S01_050(t, d):
    """The point of light (locked off)."""
    k = 0 if t < 1.0 else min(1, (t - 1.0) / 0.25) * (0.85 + 0.15 * math.sin((t - 1) / 1.2 * 2 * math.pi))
    img = street_skyline(t, point=(0.40 * W, 0.17 * H, k))
    s, ctx = surface()
    rain(ctx, t, 380, 8, alpha=0.18, length=36)
    img = over(img, to_np(s))
    # two soft foreground pedestrians (right); the nearer stops at 2.5 s
    s2, c2 = surface()
    for k2, (bx, sc, stop) in enumerate(((0.80, 1.0, 2.5), (0.92, 0.8, 99))):
        walk = min(t, stop) if k2 == 0 else t
        x = (bx - 0.02 * walk) * W
        y = H * 1.02
        sz = 520 * S * sc
        c2.set_source_rgb(0.006, 0.006, 0.008)
        c2.rectangle(x - sz * 0.16, y - sz * 0.95, sz * 0.32, sz)
        c2.fill()
        c2.arc(x + (sz * 0.03 if (k2 == 1 and t > 2.8) else 0), y - sz * 1.05, sz * 0.1, 0, 2 * math.pi)
        c2.fill()
        c2.save()
        c2.translate(x - sz * 0.05, y - sz * 1.2)
        c2.scale(sz * 0.45, sz * 0.22)
        c2.arc(0, 0, 1, math.pi, 2 * math.pi)
        c2.restore()
        c2.fill()
    img = over(img, blur(to_np(s2), 7 * S))
    return glow(img, 7, 0.7)


def S01_060(t, d):
    """The rupture opens, looking up the canyon of towers."""
    u = t / d
    X, Y = grid()
    tilt = ease(u) * 0.22 * H
    cxr, cyr = W * 0.5, H * 0.26 + tilt
    radius = (0 if t < 0.4 else ease((t - 0.4) / 4.0) ** 1.4 * 0.27 * H) + 2 * S
    grade = ease((t - 0.6) / 3.0)
    # sky: swirling cloud around the rupture
    if 'sw' not in G:
        G['sw'] = spectral_noise(1024, 2.2, 61)
    dx, dy = X - cxr, Y - cyr
    rr = np.sqrt(dx * dx + dy * dy) + 1
    th = np.arctan2(dy, dx) + (t * 0.5 + 0.3 * u) * (300 * S / (rr + 200 * S)) * 3
    pull = rr * (1 - 0.08 * u)
    n = sample(G['sw'], np.cos(th) * pull / (2.2 * S) + 500, np.sin(th) * pull / (2.2 * S) + 500)
    cloud = np.clip((n - 0.3) * 1.8, 0, 1)
    sky = (np.array([0.16, 0.09, 0.06], np.float32) * (1 - grade) + np.array([0.16, 0.05, 0.22], np.float32) * grade)
    img = np.zeros((H, W, 3), np.float32) + sky * (0.35 + cloud[..., None] * 1.1)
    lit = np.exp(-np.clip(rr - radius, 0, None) / (0.35 * H)) * grade
    img += (lit * cloud * 0.5)[..., None] * np.array([0.8, 0.3, 1.0], np.float32)
    inside = rr < radius * 0.97
    dark = np.array([0.012, 0.0, 0.03], np.float32)
    img[inside] = dark + 0.02 * n[inside][..., None]
    img = stars_into(img, inside.astype(np.float32), 62, 900, 1.2)
    img += rupture_layer(cxr, cyr, radius, t, 1.0, lattice=(0 if t < 0.9 else (t - 0.9) * 0.55 * H))
    # towers converging upward (four walls), windows reflect the sky colour
    s, ctx = surface()
    vy = cyr - 1.4 * H
    for side in (-1, 1):
        for layer, (x_bot, x_top, shade) in enumerate(((0.16, 0.33, 0.03), (0.07, 0.27, 0.02), (-0.04, 0.2, 0.012))):
            xb = W * (0.5 + side * (0.5 - x_bot))
            xt = W * (0.5 + side * (0.5 - x_top))
            xw = W * (0.5 + side * 0.72)
            ctx.set_source_rgb(shade, shade, shade * 1.3)
            ctx.move_to(xb, H)
            ctx.line_to(xt, -0.02 * H + tilt * 0.3 - layer * 40 * S)
            ctx.line_to(xw, -0.02 * H)
            ctx.line_to(xw, H)
            ctx.close_path()
            ctx.fill()
            # window rows (perspective lines converging upward)
            rws = rng(600 + layer * 10 + (side > 0))
            for i in range(26):
                fy = (i / 26.0) ** 1.6
                y = H - fy * H * 1.05 + tilt * 0.15
                xa = lerp(xb, xt, fy)
                for j in range(9):
                    if rws.random() < 0.3:
                        xx = lerp(xa, xw, j / 9.0 + 0.03)
                        wv = abs(xw - xa) / 9.0 * 0.5
                        b = rws.uniform(0.2, 0.7)
                        ctx.set_source_rgba(lerp(b, b * 0.8, grade), lerp(b * 0.75, b * 0.45, grade),
                                            lerp(b * 0.45, b * 1.1, grade), 0.85)
                        ctx.rectangle(min(xx, xx + side * wv), y, abs(wv), 7 * S * (1 - fy * 0.7))
                        ctx.fill()
    # hazard lights at the bottom edge once alarms start
    if t > 3.5:
        on = (t * 1.6) % 1 < 0.5
        for hx in (0.1, 0.27, 0.71, 0.88):
            if on:
                g = cairo.RadialGradient(hx * W, H * 0.99, 0, hx * W, H * 0.99, 80 * S)
                g.add_color_stop_rgba(0, 1, 0.55, 0.1, 0.8)
                g.add_color_stop_rgba(1, 1, 0.55, 0.1, 0)
                ctx.set_source(g)
                ctx.paint()
    walls = to_np(s)
    img = over(img, walls)
    s2, c2 = surface()
    rain(c2, t, 360, 9, alpha=0.16, length=30, angle=0.05 + 0.05 * u)
    img = over(img, to_np(s2))
    return glow(img, 9, 0.9)


def S01_070(t, d):
    """Close on the glass: drops shiver, a crack races across."""
    X, Y = grid()
    img = vgrad((0.05, 0.03, 0.09), (0.02, 0.03, 0.06))
    # warped ring reflection, out of focus
    ring = np.exp(-((np.sqrt(((X - W * 0.62) / 1.25) ** 2 + (Y - H * 0.42) ** 2) - 0.28 * H) / (40 * S)) ** 2)
    img += ring[..., None] * np.array([0.6, 0.22, 0.85], np.float32)
    img += np.exp(-((X - W * 0.18) ** 2 + (Y - H * 0.7) ** 2) / (220 * S) ** 2)[..., None] * np.array([0.1, 0.18, 0.3], np.float32)
    s, ctx = surface()
    r = rng(70)
    for i in range(70):
        x = r.uniform(0, W) + math.sin(t * 2 * math.pi * 30 + i) * 1.5 * S
        y = r.uniform(0, H) + math.cos(t * 2 * math.pi * 30 + i * 1.7) * 1.5 * S
        rad = r.uniform(6, 26) * S
        g = cairo.RadialGradient(x - rad * 0.3, y - rad * 0.3, 0, x, y, rad)
        g.add_color_stop_rgba(0, 1.0, 0.85, 1.0, 0.9)
        g.add_color_stop_rgba(0.5, 0.45, 0.25, 0.6, 0.45)
        g.add_color_stop_rgba(1, 0.05, 0.02, 0.08, 0.6)
        ctx.set_source(g)
        ctx.arc(x, y, rad, 0, 2 * math.pi)
        ctx.fill()
    if t > 0.9:
        k = min(1, (t - 0.9) / 0.25)
        rc = rng(71)
        pts = [(W * 0.15, H * 0.2)]
        for i in range(40):
            px, py = pts[-1]
            pts.append((px + W * 0.02 + rc.normal() * 8 * S, py + H * 0.017 + rc.normal() * 8 * S))
        m = int(len(pts) * k)
        ctx.set_source_rgba(0.95, 0.9, 1.0, 0.85)
        ctx.set_line_width(1.6 * S)
        ctx.move_to(*pts[0])
        for p in pts[1:m]:
            ctx.line_to(*p)
        ctx.stroke()
        for b in range(0, m, 6):
            bx, by = pts[b]
            ctx.set_line_width(1.0 * S)
            ctx.move_to(bx, by)
            ctx.line_to(bx + rc.normal() * 40 * S, by + rc.normal() * 40 * S)
            ctx.stroke()
    img = over(img, to_np(s))
    return glow(img, 6, 0.7)


def smooth(ctx, pts, closed=True, move=True):
    """Catmull-Rom spline through pts as cubic Beziers."""
    n = len(pts)
    P = pts + pts[:2] if closed else [pts[0]] + pts + [pts[-1]]
    if move:
        ctx.move_to(*pts[0])
    rng_ = range(n) if closed else range(n - 1)
    for i in rng_:
        p0, p1, p2, p3 = (P[i - 1] if (closed and i == 0) else P[i - 1 + (0 if closed else 1)],
                          P[i + (0 if closed else 1)], P[i + 1 + (0 if closed else 1)],
                          P[i + 2 + (0 if closed else 1)])
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        ctx.curve_to(c1[0], c1[1], c2[0], c2[1], p2[0], p2[1])
    if closed:
        ctx.close_path()


def profile_path(ctx, pts):
    ctx.move_to(*pts[0])
    for i in range(1, len(pts) - 2, 3):
        ctx.curve_to(*pts[i], *pts[i + 1], *pts[i + 2])
    ctx.close_path()


def S01_080(t, d):
    """The woman: rain freezes around her face."""
    X, Y = grid()
    img = vgrad((0.05, 0.02, 0.08), (0.03, 0.02, 0.03))
    r = rng(80)
    bok = np.zeros((H, W, 3), np.float32)
    s0, c0 = surface()
    for i in range(30):
        x, y, rad = r.uniform(0, W * 0.55), r.uniform(0, H), r.uniform(25, 80) * S
        col = [(0.7, 0.3, 1.0), (1.0, 0.55, 0.2), (0.9, 0.5, 0.2)][i % 3]
        if i % 3 == 2 and (t * 1.6) % 1 > 0.5:
            continue
        c0.set_source_rgba(col[0], col[1], col[2], 0.22)
        c0.arc(x, y, rad, 0, 2 * math.pi)
        c0.fill()
    img = over(img, blur(to_np(s0), 6 * S))
    sc = 1 + 0.02 * t / d
    s, ctx = surface()
    ctx.translate(W * 0.62, H * 0.55)
    ctx.scale(sc * S, sc * S)
    ctx.rotate(-0.38)
    # hair mass
    ctx.set_source_rgb(0.02, 0.015, 0.015)
    ctx.arc(60, -40, 260, 0, 2 * math.pi)
    ctx.fill()
    ctx.set_line_width(3)
    for k in range(14):                      # wet hair strands catching the violet key
        a0 = -2.6 + k * 0.16
        ctx.set_source_rgba(0.6, 0.35, 0.85, 0.28)
        ctx.move_to(60 + math.cos(a0) * 240, -40 + math.sin(a0) * 240)
        ctx.curve_to(60 + math.cos(a0 + 0.3) * 270, -40 + math.sin(a0 + 0.3) * 270,
                     60 + math.cos(a0 + 0.6) * 250, -40 + math.sin(a0 + 0.6) * 250,
                     60 + math.cos(a0 + 0.9) * 262, -40 + math.sin(a0 + 0.9) * 262)
        ctx.stroke()
    # face profile facing left (nose to -x)
    face = [(40, -300), (-60, -300), (-150, -230), (-175, -120),
            (-185, -60), (-215, -10), (-235, 40), (-230, 70), (-205, 80),
            (-200, 110), (-210, 140), (-195, 160), (-200, 185), (-190, 230), (-140, 255),
            (-100, 270), (-40, 280), (40, 330), (60, 600), (300, 600), (300, -200)]
    ctx.move_to(*face[0])
    for i in range(1, 19, 3):
        ctx.curve_to(*face[i], *face[i + 1], *face[i + 2])
    ctx.line_to(300, 600)
    ctx.line_to(300, -200)
    ctx.close_path()
    g = cairo.LinearGradient(-220, -300, 120, 300)
    g.add_color_stop_rgb(0, 0.58, 0.38, 0.33)
    g.add_color_stop_rgb(0.35, 0.24, 0.14, 0.12)
    g.add_color_stop_rgb(1, 0.04, 0.025, 0.025)
    ctx.set_source(g)
    ctx.fill_preserve()
    ctx.save()
    ctx.clip()
    # violet key from above along the profile edge
    ctx.set_line_width(26)
    ctx.set_source_rgba(0.75, 0.4, 1.0, 0.5)
    ctx.move_to(*face[0])
    for i in range(1, 13, 3):
        ctx.curve_to(*face[i], *face[i + 1], *face[i + 2])
    ctx.stroke()
    ctx.restore()
    ctx.set_line_width(5)
    ctx.set_source_rgba(0.95, 0.75, 1.0, 0.85)
    ctx.move_to(*face[0])
    for i in range(1, 13, 3):
        ctx.curve_to(*face[i], *face[i + 1], *face[i + 2])
    ctx.stroke()
    # eye glint
    ctx.set_source_rgba(0.9, 0.7, 1.0, 0.9)
    ctx.arc(-130, -95, 7, 0, 2 * math.pi)
    ctx.fill()
    # hair over the crown and the back of the head, falling to the collar
    hair = [(-95, -285), (0, -350), (150, -350), (290, -250), (345, -60), (340, 160), (290, 360),
            (190, 330), (120, 150), (40, 20), (-10, -150)]
    smooth(ctx, hair)
    ctx.set_source_rgb(0.025, 0.018, 0.02)
    ctx.fill()
    ctx.set_line_width(3)
    for k in range(12):
        ctx.set_source_rgba(0.65, 0.4, 0.9, 0.30)
        smooth(ctx, [(-60 + k * 30, -300 + k * 6), (60 + k * 22, -320 + k * 18), (220 + k * 9, -230 + k * 25),
                     (290 - k * 3, -40 + k * 28), (280 - k * 8, 160 + k * 14)], closed=False)
        ctx.stroke()
    # coat collar
    ctx.set_source_rgb(0.02, 0.02, 0.03)
    ctx.move_to(-120, 330)
    ctx.line_to(80, 280)
    ctx.line_to(320, 420)
    ctx.line_to(320, 700)
    ctx.line_to(-200, 700)
    ctx.close_path()
    ctx.fill()
    ctx.identity_matrix()
    img = over(img, to_np(s))
    # breath (the drops do not move)
    if 1.0 < t < 2.0:
        k = math.sin((t - 1.0) * math.pi)
        bx, by = W * 0.40, H * 0.47
        d2 = ((X - bx - (t - 1.0) * 60 * S) / 1.6) ** 2 + (Y - by) ** 2
        img += (np.exp(-d2 / (70 * S) ** 2) * 0.12 * k)[..., None] * np.array([0.8, 0.7, 1.0], np.float32)
    s2, c2 = surface()
    rain(c2, t, 520, 81, color=(0.85, 0.75, 1.0), alpha=0.22, length=42, frozen_at=(0.5, 2.0))
    img = over(img, to_np(s2))
    return glow(img, 6, 0.8)


def S01_090(t, d):
    """Birds scatter from a cornice."""
    u = t / d
    yo = ease(u) * 0.08 * H
    X, Y = grid()
    img = vgrad((0.12, 0.04, 0.2), (0.3, 0.12, 0.25))
    img += rupture_layer(W * 0.86, H * 0.12 + yo, 0.5 * H, t + 6, 1.0) * 0.8
    s, ctx = surface()
    # water tower and cornice silhouettes
    ctx.set_source_rgb(0.015, 0.01, 0.02)
    ctx.rectangle(W * 0.08, H * 0.42 + yo, W * 0.1, H * 0.2)
    ctx.fill()
    ctx.move_to(W * 0.07, H * 0.42 + yo)
    ctx.line_to(W * 0.13, H * 0.34 + yo)
    ctx.line_to(W * 0.19, H * 0.42 + yo)
    ctx.fill()
    ctx.rectangle(0, H * 0.70 + yo, W, H)
    ctx.fill()
    ctx.rectangle(0, H * 0.66 + yo, W, H * 0.025)
    ctx.fill()
    r = rng(90)
    for i in range(42):
        x0 = r.uniform(0.15, 0.95) * W
        y0 = H * 0.655 + yo
        t0 = r.uniform(0, 0.35)
        tt = max(0, t - t0)
        vx = r.uniform(-1, 0.4) * 520 * S
        vy = -r.uniform(300, 650) * S
        x = x0 + vx * tt
        y = y0 + vy * tt + 120 * S * tt * tt
        sz = r.uniform(10, 20) * S * (1 + tt * 0.6)
        flap = math.sin((tt * 11 + i) * 2 * math.pi * 0.9) if tt > 0 else -0.6
        ctx.set_source_rgb(0.02, 0.012, 0.025)
        ctx.move_to(x, y)
        ctx.curve_to(x - sz * 0.5, y - sz * flap * 0.8, x - sz, y - sz * flap, x - sz * 1.3, y - sz * flap * 0.4)
        ctx.curve_to(x - sz * 0.7, y + sz * 0.15, x - sz * 0.3, y + sz * 0.1, x, y + sz * 0.15)
        ctx.curve_to(x + sz * 0.3, y + sz * 0.1, x + sz * 0.7, y + sz * 0.15, x + sz * 1.3, y - sz * flap * 0.4)
        ctx.curve_to(x + sz, y - sz * flap, x + sz * 0.5, y - sz * flap * 0.8, x, y)
        ctx.fill()
    img = over(img, to_np(s))
    return glow(img, 7, 0.7)


def S01_100(t, d):
    """Airliner banks hard away from the ring (long lens)."""
    X, Y = grid()
    pan = t * 40 * S
    img = vgrad((0.08, 0.03, 0.14), (0.2, 0.07, 0.2))
    img += rupture_layer(W * 0.62 - pan, H * 0.62, 0.95 * H, t + 3, 1.0) * 0.9
    img = low_cloud(img, t, 0.0, 1.2 * H, 900 + pan / S, 0.6, 33)
    s, ctx = surface()
    roll = math.radians(lerp(12, 45, ease(t / d)))
    ctx.translate(W * 0.47, H * 0.48)
    ctx.rotate(-roll * 0.6)
    L = 0.36 * W
    ctx.set_source_rgb(0.02, 0.015, 0.03)
    # fuselage
    ctx.save()
    ctx.scale(L / 2, L * 0.045)
    ctx.arc(0, 0, 1, 0, 2 * math.pi)
    ctx.restore()
    ctx.fill()
    ws = math.cos(roll) * 0.9 + 0.1
    for sgn in (-1, 1):
        ctx.move_to(-L * 0.02, 0)
        ctx.line_to(-L * 0.2, sgn * L * 0.42 * ws * (1.15 if sgn > 0 else 0.85))
        ctx.line_to(-L * 0.27, sgn * L * 0.42 * ws * (1.15 if sgn > 0 else 0.85))
        ctx.line_to(-L * 0.16, 0)
        ctx.fill()
        ctx.move_to(-L * 0.43, 0)
        ctx.line_to(-L * 0.5, sgn * L * 0.13 * ws)
        ctx.line_to(-L * 0.54, sgn * L * 0.13 * ws)
        ctx.line_to(-L * 0.5, 0)
        ctx.fill()
    ctx.move_to(-L * 0.42, 0)
    ctx.line_to(-L * 0.52, -L * 0.12)
    ctx.line_to(-L * 0.55, -L * 0.12)
    ctx.line_to(-L * 0.5, 0)
    ctx.fill()
    tips = {-1: (-L * 0.27, -L * 0.42 * ws * 0.85), 1: (-L * 0.27, L * 0.42 * ws * 1.15)}
    lights = [(tips[-1], (1, 0.1, 0.1), 5), (tips[1], (0.1, 1, 0.3), 5), ((L * 0.05, L * 0.05), (1, 1, 0.95), 9),
              ((-L * 0.08, L * 0.12 * ws), (1, 1, 0.95), 9)]
    if (t % 1.0) < 0.06:
        lights += [(tips[-1], (1, 1, 1), 12), (tips[1], (1, 1, 1), 12)]
    pts = []
    for (lx, ly), col, rad in lights:
        ux, uy = ctx.user_to_device(lx, ly)
        pts.append((ux, uy, col, rad))
    ctx.identity_matrix()
    # wingtip vortex trails
    for (lx, ly) in (tips[-1], tips[1]):
        pass
    img = over(img, to_np(s))
    for ux, uy, col, rad in pts:
        d2 = (X - ux) ** 2 + (Y - uy) ** 2
        img += (np.exp(-d2 / (rad * S) ** 2) * 3)[..., None] * np.array(col, np.float32)
        img += (np.exp(-d2 / (rad * 6 * S) ** 2) * 0.25)[..., None] * np.array(col, np.float32)
    s2, c2 = surface()
    for (ux, uy, col, rad) in pts[:2]:
        c2.set_source_rgba(0.9, 0.9, 1.0, 0.18)
        c2.set_line_width(3 * S)
        c2.move_to(ux, uy)
        c2.curve_to(ux + 120 * S, uy + 10 * S, ux + 300 * S, uy - 20 * S, ux + 520 * S, uy + 30 * S)
        c2.stroke()
    rain(c2, t, 300, 101, alpha=0.14, length=50, angle=0.9)
    img = over(img, blur(to_np(s2), 1.2 * S))
    return glow(img, 8, 0.8)


def S01_110(t, d):
    """Observatory control room: every trace off its scale."""
    u = t / d
    X, Y = grid()
    img = np.zeros((H, W, 3), np.float32) + np.array([0.01, 0.012, 0.016], np.float32)
    zoom = lerp(1.0, 1.07, ease(u))
    s, ctx = surface()
    ctx.translate(W * 0.62, H * 0.5)
    ctx.scale(zoom * S, zoom * S)
    ctx.translate(-960, -540)
    r = rng(110)
    for row in range(3):
        for col in range(4):
            x0, y0 = 120 + col * 250, 170 + row * 190
            ctx.set_source_rgb(0.01, 0.03, 0.035)
            ctx.rectangle(x0, y0, 230, 165)
            ctx.fill()
            ctx.set_source_rgba(0.2, 0.9, 0.8, 0.85)
            ctx.set_line_width(2)
            spike_at = r.uniform(0.15, 0.5)
            ctx.move_to(x0 + 8, y0 + 120)
            for k in range(1, 60):
                xx = x0 + 8 + k * 3.6
                base = y0 + 120 + math.sin(k * 0.7 + row + col) * 6
                frac = k / 60.0
                if frac > 1 - (u - spike_at) * 2.2 and u > spike_at:
                    base = y0 + 10 + r.normal() * 4
                ctx.line_to(xx, base)
            ctx.stroke()
            ctx.set_source_rgba(1, 0.2, 0.2, 0.9 if (t * 4) % 1 < 0.5 and u > spike_at else 0.0)
            ctx.rectangle(x0 + 195, y0 + 8, 26, 10)
            ctx.fill()
    # seismograph paper and scribble
    ctx.set_source_rgb(0.75, 0.72, 0.66)
    ctx.rectangle(120, 760, 980, 110)
    ctx.fill()
    ctx.set_source_rgb(0.05, 0.05, 0.06)
    ctx.set_line_width(2)
    ctx.move_to(120, 815)
    for k in range(240):
        amp = 4 if k < 150 else 4 + (k - 150) * 0.6 * min(1, u * 3)
        ctx.line_to(120 + k * 4.08, 815 + math.sin(k * 1.3) * amp * r.uniform(0.5, 1.0))
    ctx.stroke()
    ctx.identity_matrix()
    screens = to_np(s)
    sharp = 1.0 - ease((t - 1.0) / 0.5)
    screens = blur(screens, (1 - sharp) * 6 * S) if sharp < 0.99 else screens
    img = over(img, screens)
    # Dr. Okafor in profile, lit by the screens
    s2, c2 = surface()
    c2.translate(W * 0.80, H * 0.52)
    c2.scale(zoom * S * 1.1, zoom * S * 1.1)
    c2.set_source_rgb(0.03, 0.03, 0.035)
    c2.arc(30, -170, 120, 0, 2 * math.pi)
    c2.fill()
    head = [(60, -290), (-20, -300), (-80, -250), (-95, -170), (-100, -130), (-125, -95), (-120, -70),
            (-105, -60), (-110, -40), (-100, -20), (-104, 0), (-60, 40), (-40, 70), (-30, 120),
            (-160, 170), (-180, 400), (300, 400)]
    c2.move_to(*head[0])
    for i in range(1, 13, 3):
        c2.curve_to(*head[i], *head[i + 1], *head[i + 2])
    c2.line_to(*head[13])
    c2.line_to(*head[14])
    c2.line_to(*head[15])
    c2.line_to(*head[16])
    c2.close_path()
    c2.set_source_rgb(0.06, 0.045, 0.04)
    c2.fill()
    c2.move_to(*head[0])
    for i in range(1, 13, 3):
        c2.curve_to(*head[i], *head[i + 1], *head[i + 2])
    c2.set_source_rgba(0.3, 1.0, 0.9, 0.75)
    c2.set_line_width(6)
    c2.stroke()
    c2.set_source_rgba(0.6, 0.7, 0.75, 0.5)   # reading glasses pushed up
    c2.set_line_width(3)
    c2.arc(-40, -285, 22, 0, 2 * math.pi)
    c2.stroke()
    c2.identity_matrix()
    lady = to_np(s2)
    lady = blur(lady, sharp * 3 * S) if sharp > 0.01 else lady
    img = over(img, lady)
    # rotating red beacon wash
    ang = t * 5.0
    bx = W * 0.5 + math.cos(ang) * W * 0.7
    img += (np.exp(-((X - bx) ** 2) / (300 * S) ** 2) * 0.12 * (0.5 + 0.5 * math.sin(ang)))[..., None] * np.array([1, 0.05, 0.05], np.float32)
    return glow(img, 6, 0.8)


def S01_120(t, d):
    """Close on a child's hand inside a parent's: the fingers tighten."""
    X, Y = grid()
    img = vgrad((0.03, 0.025, 0.04), (0.06, 0.04, 0.05))
    s0, c0 = surface()
    r = rng(120)
    for i in range(18):
        c0.set_source_rgba(1.0, 0.6, 0.3, 0.12)
        c0.arc(r.uniform(0, W), r.uniform(0, H), r.uniform(40, 110) * S, 0, 2 * math.pi)
        c0.fill()
    img = over(img, blur(to_np(s0), 10 * S))
    grip = ease((t - 0.7) / 0.6)
    s, ctx = surface()
    ctx.scale(S, S)
    # parent's sleeve (grey parka) from the upper left and hand
    ctx.set_source_rgb(0.18, 0.19, 0.21)
    ctx.move_to(-50, 80)
    ctx.line_to(520, 300)
    ctx.line_to(470, 520)
    ctx.line_to(-50, 420)
    ctx.close_path()
    ctx.fill()
    skin_p = (0.42, 0.27, 0.19)
    ctx.set_source_rgb(*skin_p)
    ctx.move_to(470, 300)
    ctx.curve_to(640, 330, 760, 400, 830, 470)
    ctx.curve_to(860, 520, 840, 590, 780, 600)
    ctx.curve_to(700, 610, 560, 560, 480, 520)
    ctx.close_path()
    ctx.fill()
    for k in range(2):                      # index and middle fingers held by the child
        ctx.save()
        ctx.translate(800, 500 + k * 55)
        ctx.rotate(0.35)
        ctx.rectangle(0, -24, 230, 48)
        ctx.fill()
        ctx.arc(230, 0, 24, -math.pi / 2, math.pi / 2)
        ctx.fill()
        ctx.restore()
    # child's sleeve (yellow raincoat) from the lower right and small hand
    ctx.set_source_rgb(0.78, 0.6, 0.08)
    ctx.move_to(1950, 900)
    ctx.line_to(1180, 640)
    ctx.line_to(1110, 900)
    ctx.line_to(1950, 1100)
    ctx.close_path()
    ctx.fill()
    skin_c = (0.62, 0.43, 0.33)
    ctx.set_source_rgb(*skin_c)
    ctx.move_to(1180, 650)
    ctx.curve_to(1120, 600, 1050, 590, 1000, 610)
    ctx.curve_to(960, 640, 970, 720, 1010, 760)
    ctx.curve_to(1060, 800, 1150, 800, 1190, 760)
    ctx.close_path()
    ctx.fill()
    for k in range(4):                      # small fingers curling over the parent's fingers
        ang = -2.1 + k * 0.18 - grip * 0.35
        ctx.save()
        ctx.translate(1010 + k * 26, 625 + k * 8)
        ctx.rotate(ang)
        ctx.rectangle(0, -13, 95 - k * 6, 26)
        ctx.fill()
        ctx.arc(95 - k * 6, 0, 13, -math.pi / 2, math.pi / 2)
        ctx.fill()
        ctx.restore()
    ctx.identity_matrix()
    hands = to_np(s)
    img = over(img, hands)
    # violet sweep, only on the hands and sleeves
    sweep_x = lerp(-0.3, 1.3, t / d) * W
    band = np.exp(-((X - sweep_x - (Y - H / 2) * 0.4) / (260 * S)) ** 2)
    img += (band * hands[..., 3])[..., None] * np.array([0.55, 0.2, 0.8], np.float32)
    s2, c2 = surface()
    rr = rng(121)
    for i in range(40):
        x, y = rr.uniform(0.25, 0.65) * W, rr.uniform(0.3, 0.8) * H
        c2.set_source_rgba(1, 0.9, 1, 0.5)
        c2.arc(x, y, rr.uniform(1.5, 4) * S, 0, 2 * math.pi)
        c2.fill()
    rain(c2, t, 200, 122, alpha=0.12, length=40)
    img = over(img, to_np(s2) * hands[..., 3:4] * 0.8 + to_np(s2) * 0.2)
    return glow(img, 6, 0.6)


def ship_shape(ctx, x, y, size, ang, cls=0, lights=True):
    ctx.save()
    ctx.translate(x, y)
    ctx.rotate(ang)
    ctx.scale(size, size)
    ctx.set_source_rgb(0.012, 0.01, 0.018)
    if cls == 0:
        ctx.move_to(1.0, 0)
        ctx.line_to(-0.6, -0.45)
        ctx.line_to(-0.35, 0)
        ctx.line_to(-0.6, 0.45)
    elif cls == 1:
        ctx.move_to(1.0, 0)
        ctx.line_to(0.3, -0.25)
        ctx.line_to(-0.9, -0.3)
        ctx.line_to(-0.9, 0.3)
        ctx.line_to(0.3, 0.25)
    else:
        ctx.move_to(1.0, -0.08)
        ctx.line_to(-1.0, -0.18)
        ctx.line_to(-1.0, 0.18)
        ctx.line_to(1.0, 0.08)
    ctx.close_path()
    ctx.fill()
    if lights:
        ctx.set_source_rgba(0.85, 0.4, 1.0, 0.95)
        for lx, ly in ((0.3, 0.0), (-0.5, -0.2), (-0.5, 0.2)):
            ctx.arc(lx, ly, 0.05, 0, 2 * math.pi)
            ctx.fill()
    ctx.restore()


def S01_130(t, d):
    """The fleet pours out of the rupture toward camera."""
    u = t / d
    X, Y = grid()
    sc = lerp(1.0, 1.08, ease(u))
    cx, cy, R = W * 0.5, H * 0.40, 0.34 * H * sc
    if 'sw' not in G:
        G['sw'] = spectral_noise(1024, 2.2, 61)
    dx, dy = X - cx, Y - cy
    rr = np.sqrt(dx * dx + dy * dy) + 1
    th = np.arctan2(dy, dx) + (t * 0.6 + 2) * (300 * S / (rr + 200 * S)) * 3
    n = sample(G['sw'], np.cos(th) * rr / (2.2 * S) + 500, np.sin(th) * rr / (2.2 * S) + 500)
    cloud = np.clip((n - 0.3) * 1.8, 0, 1)
    img = np.array([0.15, 0.05, 0.22], np.float32) * (0.4 + cloud[..., None])
    inside = rr < R * 0.97
    img[inside] = np.array([0.015, 0.0, 0.035], np.float32)
    img = stars_into(img, inside.astype(np.float32), 62, 900, 1.2)
    img += rupture_layer(cx, cy, R, t + 6, 1.0)
    if (t % 0.9) < 0.07:
        img += (np.exp(-np.abs(rr - R * 1.25) / (40 * S)) * cloud * 1.2)[..., None] * np.array([0.7, 0.6, 1.0], np.float32)
    s, ctx = surface()
    r = rng(130)
    ships = []
    for i in range(160):
        t0 = r.uniform(-1.0, d)
        tt = t - t0
        if tt <= 0:
            continue
        ang = r.uniform(0, 2 * math.pi)
        dist = R * (0.05 + tt * r.uniform(0.25, 0.6)) ** 1.25 * 1.4
        size = (4 + tt * r.uniform(10, 26)) * S
        x = cx + math.cos(ang) * dist
        y = cy + math.sin(ang) * dist * 0.8
        ships.append((size, x, y, ang, i % 3))
    for size, x, y, ang, cls in sorted(ships):
        ship_shape(ctx, x, y, size, ang + math.pi * 0.0, cls)
    img = over(img, to_np(s))
    return glow(img, 8, 0.9)


def throne_path(ctx, x, y, L):
    """The Silent Throne: a cathedral-like flagship seen nose-on/three-quarter from below."""
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(L, L)
    ctx.move_to(-0.5, 0.02)
    ctx.line_to(-0.42, -0.04)
    for k in range(9):          # buttress fins / spires along the top
        xx = -0.4 + k * 0.1
        h = 0.06 + 0.07 * (1 - abs(xx) / 0.45) + (0.05 if k == 4 else 0)
        ctx.line_to(xx - 0.02, -0.045)
        ctx.line_to(xx, -0.045 - h)
        ctx.line_to(xx + 0.02, -0.045)
    ctx.line_to(0.42, -0.04)
    ctx.line_to(0.5, 0.02)
    ctx.line_to(0.2, 0.07)
    ctx.line_to(0.0, 0.11)
    ctx.line_to(-0.2, 0.07)
    ctx.close_path()
    ctx.restore()


def S01_140(t, d):
    """Extreme wide from across the harbor: the flagship emerges."""
    u = t / d
    X, Y = grid()
    crane = ease(u) * 0.03 * H
    hz = 0.66 * H + crane
    img = vgrad((0.05, 0.015, 0.09), (0.25, 0.08, 0.2), 0.0, hz / H)
    cx, cy = W * 0.5, 0.33 * H + crane
    R = 0.45 * H
    rr = np.sqrt((X - cx) ** 2 + (Y - cy) ** 2)
    inside = (rr < R) & (Y < hz)
    img[inside] = np.array([0.02, 0.0, 0.04], np.float32)
    img = stars_into(img, inside.astype(np.float32), 140, 700, 1.0)
    img += rupture_layer(cx, cy, R, t + 9, 1.0)
    img = low_cloud(img, t, 0.0, hz, 2000, 0.5, 34)
    s, ctx = surface()
    # escorts parting
    r = rng(140)
    for i in range(70):
        a = r.uniform(0, 2 * math.pi)
        dd = R * r.uniform(0.2, 0.9) * (1 + u * 0.4)
        ship_shape(ctx, cx + math.cos(a) * dd, cy + math.sin(a) * dd * 0.6, r.uniform(3, 7) * S, a, i % 3)
    # flagship
    L = lerp(0.08, 0.62, ease(u ** 0.8)) * W
    fy = cy + lerp(0.0, 0.08, u) * H
    throne_path(ctx, cx, fy, L)
    g = cairo.LinearGradient(0, fy - L * 0.15, 0, fy + L * 0.11)
    g.add_color_stop_rgb(0, 0.03, 0.015, 0.045)
    g.add_color_stop_rgb(0.7, 0.02, 0.015, 0.02)
    g.add_color_stop_rgb(1, 0.22, 0.1, 0.05)
    ctx.set_source(g)
    ctx.fill_preserve()
    ctx.set_source_rgba(0.75, 0.4, 1.0, 0.5)
    ctx.set_line_width(max(1.0, L * 0.003))
    ctx.stroke()
    rs = rng(141)
    for i in range(30):
        ctx.set_source_rgba(0.85, 0.45, 1.0, 0.9)
        ctx.rectangle(cx + rs.uniform(-0.4, 0.4) * L, fy + rs.uniform(-0.03, 0.06) * L, L * 0.012, L * 0.002)
        ctx.fill()
    img = over(img, to_np(s))
    # haze between flagship and city
    img += (np.clip((Y - (hz - 0.12 * H)) / (0.12 * H), 0, 1) * (Y < hz))[..., None] * np.array([0.1, 0.05, 0.1], np.float32)
    # city strip and water
    far, _, _ = skyline_layers()
    a, _ = far
    strip = a[int(0.40 * H):int(0.62 * H), 400:400 + W]
    small = strip[::4, :, :]
    h = small.shape[0]
    y0 = int(hz - h)
    region = img[y0:y0 + h]
    img[y0:y0 + h] = small[..., :3] * 1.4 + region * (1 - small[..., 3:4])
    hzi = int(hz)
    refl = img[hzi - np.clip(np.arange(H - hzi), 0, hzi - 1) - 1]
    wob = (np.sin(Y[hzi:] * 0.15 + t * 3) * 5) * S
    xs = np.clip((X[hzi:] + wob).astype(int), 0, W - 1)
    img[hzi:] = blur(refl[np.arange(H - hzi)[:, None], xs], 1.5 * S) * 0.45 + 0.004
    return glow(img, 9, 0.9)


def thanos_back(ctx, sc):
    """Thanos from behind and below, looking down over his right shoulder (user units)."""
    # neck and head (bald back of skull, ear on the right)
    ctx.set_source_rgb(0.14, 0.08, 0.19)
    smooth(ctx, [(270, 640), (250, 520), (262, 400), (300, 315), (380, 285), (462, 310), (505, 390),
                 (512, 470), (530, 480), (545, 520), (522, 560), (500, 600), (490, 650)])
    ctx.fill()
    # torso armor
    ctx.set_source_rgb(0.022, 0.02, 0.028)
    smooth(ctx, [(-90, 1200), (-110, 900), (-40, 700), (90, 600), (380, 590), (640, 610), (760, 720),
                 (800, 940), (790, 1200)])
    ctx.fill()
    for px, flip in ((120, -1), (650, 1)):
        ctx.save()
        ctx.translate(px, 640)
        ctx.scale(flip, 1)
        ctx.set_source_rgb(0.04, 0.036, 0.045)
        smooth(ctx, [(-180, 50), (-150, -50), (0, -105), (160, -70), (185, 20), (120, 100), (-60, 120)])
        ctx.fill()
        ctx.set_source_rgba(0.85, 0.65, 0.3, 0.6)
        ctx.set_line_width(7)
        smooth(ctx, [(-150, -50), (0, -105), (160, -70), (185, 20)], closed=False)
        ctx.stroke()
        ctx.restore()
    ctx.set_source_rgba(0.8, 0.6, 0.28, 0.45)
    ctx.set_line_width(6)
    ctx.move_to(240, 640)
    ctx.curve_to(310, 680, 460, 680, 520, 640)
    ctx.stroke()
    for k in range(3):
        ctx.move_to(170 + k * 12, 800 + k * 120)
        ctx.curve_to(320, 830 + k * 120, 460, 830 + k * 120, 600 - k * 12, 800 + k * 120)
        ctx.stroke()


def S01_150(t, d):
    """Over Thanos's shoulder on the prow, the city far below."""
    u = t / d
    X, Y = grid()
    img = vgrad((0.07, 0.02, 0.12), (0.22, 0.08, 0.18), 0.0, 0.5)
    # city far below in perspective (rows compressed toward the horizon)
    city = city_texture()
    hz = 0.36 * H
    below = Y > hz
    depth = np.clip((Y - hz) / (H - hz), 1e-3, 1)
    cu = (X - W * 0.62) / (depth * 2.2 * S) + 1024 + t * 6
    cv = 1700 - 900 / (depth * 3 + 0.4)
    c = np.stack([sample(city[..., k], cu, cv) for k in range(3)], -1) * 1.8
    fog = np.clip(1 - depth * 2.5, 0, 1)[..., None]
    c = c * (1 - fog) + fog * np.array([0.2, 0.08, 0.16], np.float32)
    img = np.where(below[..., None], c, img)
    img = low_cloud(img, t * 3, 0.4 * H, 1.1 * H, 700 + t * 30, 0.6, 35)
    img += rupture_layer(W * 0.75, -0.25 * H, 0.55 * H, t, 1.0) * 0.6
    # the platform edge and Thanos
    s, ctx = surface()
    sc = lerp(1.0, 1.06, ease(u))
    lift = ease(u) * 30 * S
    ctx.set_source_rgb(0.015, 0.014, 0.02)
    ctx.move_to(0, H * 0.78 - lift)
    ctx.line_to(W * 0.55, H * 0.95 - lift)
    ctx.line_to(W * 0.62, H)
    ctx.line_to(0, H)
    ctx.close_path()
    ctx.fill()
    ctx.set_source_rgba(0.85, 0.65, 0.3, 0.35)
    ctx.set_line_width(3 * S)
    ctx.move_to(0, H * 0.78 - lift)
    ctx.line_to(W * 0.55, H * 0.95 - lift)
    ctx.stroke()
    ctx.translate(-0.06 * W, H * 0.02 - lift)
    ctx.scale(sc * S, sc * S)
    thanos_back(ctx, sc)
    ctx.identity_matrix()
    th = to_np(s)
    img = over(img, th)
    # violet rim on his upper edges from the rupture
    edge = th[..., 3] - np.roll(np.roll(th[..., 3], int(7 * S), 0), -int(7 * S), 1)
    img += (np.clip(edge, 0, 1) * 1.6)[..., None] * np.array([0.7, 0.35, 1.0], np.float32) * (Y < H * 0.7)[..., None]
    s2, c2 = surface()
    r = rng(150)
    for i in range(80):   # wind particles
        x = (r.uniform(0, 1) * W + t * 900 * S * r.uniform(0.6, 1.4)) % W
        y = r.uniform(0, H)
        c2.set_source_rgba(0.8, 0.7, 0.9, 0.12)
        c2.set_line_width(1.2 * S)
        c2.move_to(x, y)
        c2.line_to(x - 60 * S, y + 4 * S)
        c2.stroke()
    img = over(img, to_np(s2))
    return glow(img, 8, 0.7)


def thanos_profile(ctx):
    """Thanos in profile facing right; user units, head about 900 tall."""
    front = [(120, -425), (225, -330), (262, -250), (300, -205), (292, -168), (262, -150),
             (280, -105), (318, -40), (352, 10), (338, 38), (302, 52), (312, 84), (300, 112),
             (310, 140), (300, 178), (322, 240), (340, 300), (326, 372), (286, 418), (190, 438),
             (90, 430), (62, 520)]
    back = [(62, 900), (-430, 900), (-360, 420), (-345, 120), (-360, -120), (-300, -330), (-130, -440)]
    skin = cairo.LinearGradient(320, -300, -300, 300)
    skin.add_color_stop_rgb(0, 0.42, 0.26, 0.54)
    skin.add_color_stop_rgb(0.45, 0.2, 0.11, 0.27)
    skin.add_color_stop_rgb(1, 0.05, 0.03, 0.07)
    smooth(ctx, front + back)
    ctx.set_source(skin)
    ctx.fill_preserve()
    path = ctx.copy_path()
    ctx.save()
    ctx.clip()
    # brow shadow over the eye, cheek and chin-ridge grooves
    g = cairo.RadialGradient(225, -125, 5, 225, -125, 95)
    g.add_color_stop_rgba(0, 0.0, 0.0, 0.01, 0.95)
    g.add_color_stop_rgba(1, 0.0, 0.0, 0.01, 0.0)
    ctx.set_source(g)
    ctx.paint()
    ctx.set_source_rgba(0.85, 0.7, 0.95, 0.85)
    ctx.arc(250, -120, 5, 0, 2 * math.pi)
    ctx.fill()
    for k in range(6):
        x0 = 150 + k * 30
        ctx.set_source_rgba(0.02, 0.01, 0.03, 0.7)
        ctx.set_line_width(10)
        ctx.move_to(x0, 228)
        ctx.curve_to(x0 + 16, 300, x0 + 12, 370, x0 - 8, 430)
        ctx.stroke()
        ctx.set_source_rgba(0.62, 0.42, 0.72, 0.4)
        ctx.set_line_width(4)
        ctx.move_to(x0 + 12, 232)
        ctx.curve_to(x0 + 28, 300, x0 + 24, 370, x0 + 4, 430)
        ctx.stroke()
    ctx.set_source_rgba(0.03, 0.01, 0.04, 0.6)
    ctx.set_line_width(6)
    ctx.move_to(300, 128)
    ctx.line_to(250, 135)
    ctx.stroke()
    ctx.restore()
    # violet rim only along the front of the face
    smooth(ctx, front, closed=False)
    ctx.set_source_rgba(0.88, 0.55, 1.0, 0.95)
    ctx.set_line_width(7)
    ctx.stroke()
    # armored gorget with worn gold edge
    ctx.set_source_rgb(0.035, 0.032, 0.04)
    ctx.move_to(-470, 600)
    ctx.curve_to(-220, 540, 140, 560, 360, 690)
    ctx.line_to(420, 1000)
    ctx.line_to(-470, 1000)
    ctx.close_path()
    ctx.fill_preserve()
    ctx.set_source_rgba(0.9, 0.68, 0.3, 0.75)
    ctx.set_line_width(10)
    ctx.stroke()


def S01_160(t, d):
    """Close on Thanos's profile; slow push."""
    u = t / d
    X, Y = grid()
    img = vgrad((0.05, 0.015, 0.08), (0.02, 0.01, 0.03))
    img += (np.exp(-((X - W * 0.85) ** 2 + (Y - H * 0.3) ** 2) / (500 * S) ** 2) * 0.25)[..., None] * np.array([0.7, 0.3, 1.0], np.float32)
    sc = lerp(0.95, 1.03, ease(u))
    s, ctx = surface()
    ctx.translate(W * 0.42, H * 0.47)
    ctx.scale(sc * S * 0.95, sc * S * 0.95)
    thanos_profile(ctx)
    ctx.identity_matrix()
    th = to_np(s)
    img = over(img, th)
    # warm under-fill on the jaw
    img += (np.exp(-((X - W * 0.55) ** 2 + (Y - H * 0.95) ** 2) / (300 * S) ** 2) * th[..., 3] * 0.35)[..., None] * np.array([1.0, 0.5, 0.25], np.float32)
    return glow(img, 7, 0.8)


def S01_170(t, d):
    """Above and behind the fleet as it dives on the city."""
    u = t / d
    X, Y = grid()
    city = city_texture()
    z = lerp(0.5, 1.4, u ** 1.5)
    rot = 0.08 * u
    xx, yy = X - W / 2, Y - H * 0.62
    cu = (xx * math.cos(rot) - yy * math.sin(rot)) / (z * S) + 1024
    cv = (xx * math.sin(rot) + yy * math.cos(rot)) / (z * S) + 1060
    img = np.stack([sample(city[..., k], cu, cv) for k in range(3)], -1) * 1.8
    img = violet_grade(img, 0.4)
    if 'cl' not in G:
        G['cl'] = (spectral_noise(1024, 2.4, 21), spectral_noise(1024, 2.0, 22))
    zc = 0.8 * (1 + 3 * u)
    n = sample(G['cl'][0], xx / (zc * S) + 77, yy / (zc * S) + 33)
    a = np.clip((n - 0.55) * 3, 0, 1)[..., None]
    img = img * (1 - a) + a * np.array([0.25, 0.12, 0.3], np.float32) * (0.5 + n[..., None])
    s, ctx = surface()
    r = rng(170)
    for i in range(14):
        x = r.uniform(0.05, 0.95) * W
        y = r.uniform(0.05, 0.5) * H + u * r.uniform(60, 220) * S
        size = r.uniform(40, 160) * S
        tip = lerp(-0.2, 0.9, u)
        ctx.save()
        ctx.translate(x, y)
        ctx.scale(size, size * (0.4 + 0.6 * abs(math.cos(tip))))
        ctx.set_source_rgb(0.01, 0.008, 0.015)
        ctx.move_to(0, 1.0)
        ctx.line_to(-0.6, -0.4)
        ctx.line_to(0, -0.1)
        ctx.line_to(0.6, -0.4)
        ctx.close_path()
        ctx.fill()
        ctx.restore()
        g = cairo.RadialGradient(x, y - size * 0.25, 0, x, y - size * 0.25, size * 0.7)
        g.add_color_stop_rgba(0, 1.0, 0.85, 1.0, 0.9)
        g.add_color_stop_rgba(0.3, 0.8, 0.35, 1.0, 0.5)
        g.add_color_stop_rgba(1, 0.6, 0.2, 1.0, 0.0)
        ctx.set_source(g)
        ctx.arc(x, y - size * 0.25, size * 0.7, 0, 2 * math.pi)
        ctx.fill()
    img = over(img, to_np(s))
    return glow(img, 9, 1.0)


def S01_180(t, d):
    """First strike: flash, shockwave, delayed sound (see audio)."""
    f = int(round(t * FPS))
    X, Y = grid()
    ring = (W * 0.5, -0.35 * H, 0.75 * H, t + 12, 1.0)
    img = street_skyline(t, ring=ring, grade=1.0)
    s, ctx = surface()
    # streaks of the descending wave
    r = rng(180)
    for i in range(12):
        x = W * r.uniform(0.3, 0.75)
        y = H * (r.uniform(-0.1, 0.2) + t * 1.2)
        ctx.set_source_rgba(0.95, 0.75, 1.0, 0.8)
        ctx.set_line_width(3 * S)
        ctx.move_to(x, y)
        ctx.line_to(x - 30 * S, y - 160 * S)
        ctx.stroke()
    img = over(img, to_np(s))
    ix, iy = W * 0.56, H * 0.52
    if f >= 6:
        k = (f - 6) / 18.0
        rr = np.sqrt((X - ix) ** 2 + ((Y - iy) * 1.3) ** 2)
        fire = np.exp(-rr / (lerp(80, 420, k ** 0.6) * S))
        img += fire[..., None] * np.array([1.6, 0.6, 0.5], np.float32) * (1.4 - k * 0.5)
        front = lerp(40, 1600, k ** 0.8) * S
        shock = np.exp(-((rr - front) / (24 * S)) ** 2)
        img += shock[..., None] * np.array([0.9, 0.85, 1.0], np.float32) * 0.9
        img *= (1 + 0.2 * np.exp(-((rr - front) / (60 * S)) ** 2))[..., None]
    if f in (6, 7):
        img = img * 0.2 + 3.0
    if f >= 18:
        shift = int((rng(f).normal() * 14) * S)
        img = np.roll(img, shift, axis=1 if f % 2 else 0)
    s2, c2 = surface()
    rain(c2, t, 380, 181, alpha=0.18, length=40, angle=0.05 if f < 14 else 1.0)
    img = over(img, to_np(s2))
    return glow(img, 10, 1.0)


# ------------------------------------------------------------------ assembly

def post(img, sid, t, frame_no, captions=None, label=None):
    img = np.clip(img, 0, None)
    img = 1 - np.exp(-img * 1.35)                                   # filmic shoulder
    X, Y = grid()
    vig = 1 - 0.32 * (((X - W / 2) / (W * 0.62)) ** 2 + ((Y - H / 2) / (H * 0.75)) ** 2)
    img *= np.clip(vig, 0, 1)[..., None]
    r = rng(frame_no)
    gr = r.normal(0, 0.012, (H // 2 + 1, W // 2 + 1)).astype(np.float32)
    img += np.repeat(np.repeat(gr, 2, 0), 2, 1)[:H, :W, None]
    s, ctx = surface()
    for (a, b, text) in (CAPTIONS if captions is None else captions).get(sid, []):
        if a <= t < b:
            al = min(1, (t - a) / 0.15, (b - t) / 0.15)
            caption(ctx, text, al)
    ctx.select_font_face('Inter', cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
    ctx.set_font_size(15 * S)
    ctx.set_source_rgba(1, 1, 1, 0.38)
    label = label or 'INFINITY CRISIS  S01 PREVIS PROTOTYPE  %s' % sid
    ext = ctx.text_extents(label)
    ctx.move_to(W - ext.width - 24 * S, H / 2 + SCOPE * S / 2 - 18 * S)
    ctx.show_text(label)
    ov = to_np(s)
    img = over(img, ov)
    return (np.clip(img, 0, 1) * 255 + 0.5).astype(np.uint8)


def plan():
    seq = C.load_yaml(os.path.join(C.DATA, 'shots', 's01.yaml'))
    out = []
    for shot in seq['shots']:
        n = C.frames(shot['dur'])
        for k in range(n):
            out.append((shot['id'], k / FPS, shot['dur'], k))
    return out


def render_frame(args):
    sid, t, d, k = args[:4]
    idx = args[4]
    img = globals()[sid](t, d)
    return post(img, sid, t, idx)


def init(scale):
    global W, H, S
    S = scale
    W, H = int(round(1920 * scale / 2) * 2), int(round(1080 * scale / 2) * 2)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', default=None)
    ap.add_argument('--png', default=None)
    ap.add_argument('--scale', type=float, default=1.0)
    ap.add_argument('--shots', default=None)
    ap.add_argument('--every', type=int, default=1, help='render every Nth frame (PNG previews)')
    ap.add_argument('--jobs', type=int, default=os.cpu_count())
    a = ap.parse_args()
    init(a.scale)
    jobs = plan()
    jobs = [j + (i,) for i, j in enumerate(jobs)]
    if a.shots:
        keep = set(a.shots.split(','))
        jobs = [j for j in jobs if j[0] in keep]
    jobs = jobs[::a.every]
    proc = None
    if a.out:
        proc = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24',
                                 '-s', '%dx%d' % (W, H), '-r', str(FPS), '-i', '-', '-c:v', 'libx264',
                                 '-preset', 'medium', '-crf', '16', '-pix_fmt', 'yuv420p', a.out],
                                stdin=subprocess.PIPE)
    if a.png:
        os.makedirs(a.png, exist_ok=True)
    with Pool(a.jobs, initializer=init, initargs=(a.scale,)) as pool:
        for j, frame in zip(jobs, pool.imap(render_frame, jobs, chunksize=2)):
            if proc:
                proc.stdin.write(frame.tobytes())
            if a.png:
                from PIL import Image
                Image.fromarray(frame).save(os.path.join(a.png, '%s_%03d.png' % (j[0], j[3])))
    if proc:
        proc.stdin.close()
        proc.wait()


if __name__ == '__main__':
    main()
