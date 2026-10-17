"""Night rooftop above the city: the stage for DOOM vs SPIDER-MAN.

Same camera model as scene.Renderer (parallax layers by depth d, 1 = the
fighters' plane, the ground plane at y = HZ * (1 - d) on layer d). The roof
ends at a parapet at depth DP; beyond it the city falls away and only the
upper floors of the skyline show, in three layers. A water tower stands on
the roof in the fighters' plane (drawn behind them); it can be holed.
"""
import math
import random

import cairo

from rig import hexrgb
from scene import HZ, YC, H0
from engine import lerp

SKY_TOP = hexrgb('#04060E')
SKY_MID = hexrgb('#0E1430')
SKY_LOW = hexrgb('#262A52')
CITY_GLOW = hexrgb('#5E4260')
FAR = hexrgb('#141933')
MID = hexrgb('#1A2041')
NEAR = hexrgb('#20264B')
WIN_WARM = hexrgb('#F2BE6A')
WIN_COOL = hexrgb('#9CC6FF')
PARAPET = hexrgb('#30324A')
PARAPET_TOP = hexrgb('#4A4B66')
ROOF_FAR = hexrgb('#34364C')
ROOF_NEAR = hexrgb('#16171F')
MOON = hexrgb('#ECE8DC')
WOOD = hexrgb('#4C3E3A')
WOOD_DK = hexrgb('#2E2527')
IRON = hexrgb('#22232B')
RIM = hexrgb('#8C8FB0')

DP = 0.42                       # parapet depth
TOWER_X = 7.5                   # water tower centre (fighters' plane)
TANK_R = 1.15
TANK_Y0, TANK_Y1 = 2.3, 4.5
LEGS = (-0.95, -0.32, 0.32, 0.95)


def _skyline(seed, x0, x1, wmin, wmax, hmin, hmax, base, spire=0.12):
    R = random.Random(seed)
    out = []
    x = x0
    while x < x1:
        w = R.uniform(wmin, wmax)
        h = R.uniform(hmin, hmax) * (1.0 if R.random() < 0.8 else 1.35)
        kind = R.random()
        b = dict(x=x, w=w, top=base + h, kind=kind, seed=R.randint(0, 10 ** 6))
        if R.random() < spire:
            b['spire'] = R.uniform(0.15, 0.6)
        if R.random() < 0.25:
            b['step'] = R.uniform(0.25, 0.45)
        out.append(b)
        x += w * R.uniform(0.75, 1.05)
    return out


LAYERS = [
    # depth, colour, buildings, window density
    (0.03, FAR, _skyline(21, -45, 45, 0.35, 0.9, 0.25, 1.45, HZ - 0.2, 0.18), 0.25),
    (0.08, MID, _skyline(33, -45, 45, 0.55, 1.3, 0.15, 1.15, HZ - 0.35, 0.12), 0.38),
    (0.18, NEAR, _skyline(47, -45, 50, 0.9, 2.0, -0.1, 0.75, HZ - 0.55, 0.05), 0.45),
]
_R = random.Random(9)
STARS = [(_R.uniform(-12, 12), _R.uniform(HZ + 0.6, HZ + 3.0), _R.uniform(0.004, 0.011), _R.uniform(0.2, 0.7))
         for _ in range(140)]
SEAMS = [(_R.uniform(-40, 40), _R.uniform(DP + 0.04, 2.2), _R.uniform(0.6, 3.0)) for _ in range(380)]
GRAVEL = [(_R.uniform(-40, 40), _R.uniform(0.75, 2.4), _R.uniform(0.008, 0.022)) for _ in range(260)]
PROPS = [  # (kind, x, depth)
    ('hut', -9.5, 0.62), ('ac', -5.8, 0.78), ('vent', -3.1, 0.9), ('skylight', 0.6, 0.7), ('vent', 2.4, 0.86),
    ('ac', 4.2, 0.66), ('mast', -8.0, 0.5), ('vent', 11.5, 0.88), ('ac', 14.0, 0.72), ('hut', 18.0, 0.6),
    ('vent', -13.0, 0.85), ('ac', -16.0, 0.7),
]


def ground_at(d):
    return HZ * (1 - d)


class Rooftop:
    def __init__(self, hole=None, searchlights=True):
        self.hole = hole                # None or (frame from which the tank is holed, x, y)
        self.searchlights = searchlights

    # --------------------------------------------------------------- background
    def draw_bg(self, R, ctx, cam, t, a):
        W, H = R.W, R.H
        ctx.identity_matrix()
        hy = R.horizon_y(cam)
        g = cairo.LinearGradient(0, hy - H * 1.1, 0, hy)
        g.add_color_stop_rgb(0, *SKY_TOP)
        g.add_color_stop_rgb(0.55, *SKY_MID)
        g.add_color_stop_rgb(0.9, *SKY_LOW)
        g.add_color_stop_rgb(1.0, *CITY_GLOW)
        ctx.set_source(g)
        ctx.paint()
        # stars
        R.layer(ctx, cam, 0.0)
        for x, y, r, al in STARS:
            tw = 0.75 + 0.25 * math.sin(t * 2.3 + x * 7)
            ctx.set_source_rgba(0.9, 0.9, 1.0, al * tw)
            ctx.arc(x, y, r, 0, 2 * math.pi)
            ctx.fill()
        # moon
        R.layer(ctx, cam, 0.015)
        mx, my, mr = cam['moon_x'], YC + cam['moon_dy'], cam['moon_r']
        g = cairo.RadialGradient(mx, my, mr * 0.9, mx, my, mr * 4.5)
        g.add_color_stop_rgba(0, *MOON, 0.2)
        g.add_color_stop_rgba(1, *MOON, 0)
        ctx.set_source(g)
        ctx.arc(mx, my, mr * 4.5, 0, 2 * math.pi)
        ctx.fill()
        ctx.set_source_rgb(*MOON)
        ctx.arc(mx, my, mr, 0, 2 * math.pi)
        ctx.fill()
        ctx.set_source_rgba(0.72, 0.7, 0.72, 0.35)
        for ox, oy, rr in ((-0.12, 0.08, 0.1), (0.1, -0.12, 0.07), (0.15, 0.13, 0.05), (-0.05, -0.18, 0.04)):
            ctx.arc(mx + ox * mr / 0.42, my + oy * mr / 0.42, rr * mr / 0.42, 0, 2 * math.pi)
            ctx.fill()
        # searchlights sweeping behind the skyline
        if self.searchlights:
            R.layer(ctx, cam, 0.02)
            for k, (x0, ph, sp) in enumerate(((-6.0, 0.3, 0.21), (5.5, 2.1, 0.17))):
                ang = math.pi / 2 + 0.42 * math.sin(t * sp + ph)
                L = 9.0
                dx, dy = math.cos(ang), math.sin(ang)
                nx, ny = -dy, dx
                y0 = HZ - 0.3
                g = cairo.LinearGradient(x0, y0, x0 + dx * L, y0 + dy * L)
                g.add_color_stop_rgba(0, 0.75, 0.8, 1.0, 0.12)
                g.add_color_stop_rgba(1, 0.75, 0.8, 1.0, 0.0)
                ctx.set_source(g)
                ctx.move_to(x0 + nx * 0.06, y0 + ny * 0.06)
                ctx.line_to(x0 + dx * L + nx * 0.9, y0 + dy * L + ny * 0.9)
                ctx.line_to(x0 + dx * L - nx * 0.9, y0 + dy * L - ny * 0.9)
                ctx.line_to(x0 - nx * 0.06, y0 - ny * 0.06)
                ctx.close_path()
                ctx.fill()
        # skyline layers
        for d, col, blds, dens in LAYERS:
            R.layer(ctx, cam, d)
            span = cam['h'] * 1.2 / max(0.3, (H0 / cam['h']) ** d)
            vis = [b for b in blds if abs(b['x'] - cam['cx'] * d) < span + 3]
            for b in vis:
                self.building(ctx, b, col, dens, t, d)
            # haze at the feet of each layer
            ctx.identity_matrix()
        # haze over the city below the parapet line
        R.layer(ctx, cam, 0.2)
        g = cairo.LinearGradient(0, HZ - 1.2, 0, HZ + 0.6)
        g.add_color_stop_rgba(0, *CITY_GLOW, 0.55)
        g.add_color_stop_rgba(1, *CITY_GLOW, 0.0)
        ctx.set_source(g)
        ctx.rectangle(cam['cx'] * 0.2 - 40, HZ - 1.2, 80, 1.8)
        ctx.fill()
        self.draw_roof(R, ctx, cam, t, a)

    def building(self, ctx, b, col, dens, t, d):
        x, w, top = b['x'], b['w'], b['top']
        base = top - 12
        ctx.set_source_rgb(*col)
        if b.get('step'):
            s = b['step'] * w
            ctx.rectangle(x, base, w, top - base - 0.18)
            ctx.fill()
            ctx.rectangle(x + s * 0.5, base, w - s, top - base)
            ctx.fill()
        else:
            ctx.rectangle(x, base, w, top - base)
            ctx.fill()
        if b.get('spire'):
            cxs = x + w / 2
            ctx.move_to(cxs - w * 0.08, top)
            ctx.line_to(cxs, top + b['spire'])
            ctx.line_to(cxs + w * 0.08, top)
            ctx.close_path()
            ctx.fill()
            # aircraft warning light
            on = (math.sin(t * 3.0 + b['seed']) > 0.3)
            if on:
                g = cairo.RadialGradient(cxs, top + b['spire'], 0, cxs, top + b['spire'], 0.06)
                g.add_color_stop_rgba(0, 1.0, 0.25, 0.2, 0.9)
                g.add_color_stop_rgba(1, 1.0, 0.25, 0.2, 0.0)
                ctx.set_source(g)
                ctx.arc(cxs, top + b['spire'], 0.06, 0, 2 * math.pi)
                ctx.fill()
        # rim light from the moon on the right edge
        ctx.set_source_rgba(*RIM, 0.10)
        ctx.rectangle(x + w - 0.02, base, 0.02, top - base)
        ctx.fill()
        # windows
        R = random.Random(b['seed'])
        cw, ch = 0.06 + 0.02 * (d > 0.1), 0.05 + 0.02 * (d > 0.1)
        nx = max(1, int(w / (cw * 2.1)))
        gx = w / nx
        rows = int(3.0 / (ch * 2.2))
        warm = R.random() < 0.7
        for j in range(rows):
            yy = top - 0.12 - j * ch * 2.2
            for i in range(nx):
                if R.random() < dens:
                    c = WIN_WARM if (warm or R.random() < 0.2) else WIN_COOL
                    al = R.uniform(0.25, 0.8)
                    if R.random() < 0.03:
                        al *= 0.5 + 0.5 * math.sin(t * 1.3 + i + j)
                    ctx.set_source_rgba(*c, al)
                    ctx.rectangle(x + gx * i + (gx - cw) / 2, yy - ch, cw, ch)
                    ctx.fill()

    # --------------------------------------------------------------- the roof
    def draw_roof(self, R, ctx, cam, t, a):
        W, H = R.W, R.H
        # roof surface from the parapet to the bottom of the frame
        R.layer(ctx, cam, DP)
        x0 = cam['cx'] * DP
        top = ground_at(DP)
        # convert the parapet base to screen space for the surface gradient
        sx, sy = ctx.user_to_device(x0, top)
        ctx.identity_matrix()
        g = cairo.LinearGradient(0, sy, 0, H)
        g.add_color_stop_rgb(0, *ROOF_FAR)
        g.add_color_stop_rgb(0.4, *[lerp(p, q, 0.6) for p, q in zip(ROOF_FAR, ROOF_NEAR)])
        g.add_color_stop_rgb(1, *ROOF_NEAR)
        ctx.set_source(g)
        ctx.rectangle(0, sy - 1, W, H - sy + 1)
        ctx.fill()
        # parapet wall with a coping stone and a moonlit edge
        R.layer(ctx, cam, DP)
        ctx.set_source_rgb(*PARAPET)
        ctx.rectangle(x0 - 60, top - 0.02, 120, 0.3)
        ctx.fill()
        ctx.set_source_rgb(*PARAPET_TOP)
        ctx.rectangle(x0 - 60, top + 0.28, 120, 0.06)
        ctx.fill()
        ctx.set_source_rgba(*RIM, 0.25)
        ctx.rectangle(x0 - 60, top + 0.335, 120, 0.012)
        ctx.fill()
        ctx.set_source_rgba(0, 0, 0, 0.25)
        for k in range(-60, 61):
            ctx.rectangle(x0 + k * 0.9 - (x0 % 0.9), top + 0.28, 0.012, 0.06)
        ctx.fill()
        # tar seams in perspective
        for x, d, L in SEAMS:
            if abs(x - cam['cx'] * d) > 16:
                continue
            s = R.layer(ctx, cam, d)
            y = ground_at(d)
            al = min(0.3, 0.06 + 0.14 * d)
            ctx.set_source_rgba(0.06, 0.06, 0.09, al)
            ctx.set_line_width(max(0.012, 1.0 / s) * (0.5 + 0.5 * d))
            ctx.move_to(x - L / 2, y)
            ctx.line_to(x + L / 2, y)
            ctx.stroke()
        # props on the roof, far to near
        for kind, x, d in sorted(PROPS, key=lambda q: q[2]):
            if abs(x - cam['cx'] * d) > 14:
                continue
            R.layer(ctx, cam, d)
            self.prop(ctx, kind, x, ground_at(d), t)
        # the water tower stands in the fighters' plane
        R.layer(ctx, cam, 1.0)
        if abs(TOWER_X - cam['cx']) < cam['h'] * 1.2 + 3:
            self.tower(ctx, a, t)

    def prop(self, ctx, kind, x, y, t):
        if kind == 'ac':
            ctx.set_source_rgb(0.2, 0.21, 0.28)
            ctx.rectangle(x - 0.55, y, 1.1, 0.55)
            ctx.fill()
            ctx.set_source_rgba(0, 0, 0, 0.35)
            for k in range(7):
                ctx.rectangle(x - 0.45 + k * 0.14, y + 0.1, 0.05, 0.32)
            ctx.fill()
            ctx.set_source_rgba(*RIM, 0.25)
            ctx.rectangle(x - 0.55, y + 0.53, 1.1, 0.02)
            ctx.fill()
            # fan housing
            ctx.set_source_rgb(0.16, 0.17, 0.22)
            ctx.rectangle(x - 0.35, y + 0.55, 0.7, 0.08)
            ctx.fill()
        elif kind == 'hut':
            ctx.set_source_rgb(0.17, 0.18, 0.25)
            ctx.rectangle(x - 1.1, y, 2.2, 1.55)
            ctx.fill()
            ctx.set_source_rgb(0.21, 0.22, 0.3)
            ctx.rectangle(x - 1.2, y + 1.55, 2.4, 0.1)
            ctx.fill()
            ctx.set_source_rgb(0.09, 0.09, 0.13)
            ctx.rectangle(x - 0.3, y, 0.6, 1.1)
            ctx.fill()
            # caged lamp over the door, with its pool of light
            g = cairo.RadialGradient(x, y + 1.25, 0, x, y + 1.25, 0.9)
            g.add_color_stop_rgba(0, 1.0, 0.82, 0.5, 0.35)
            g.add_color_stop_rgba(1, 1.0, 0.82, 0.5, 0.0)
            ctx.set_source(g)
            ctx.arc(x, y + 1.25, 0.9, 0, 2 * math.pi)
            ctx.fill()
            ctx.set_source_rgb(1.0, 0.88, 0.6)
            ctx.arc(x, y + 1.25, 0.05, 0, 2 * math.pi)
            ctx.fill()
        elif kind == 'vent':
            ctx.set_source_rgb(0.24, 0.25, 0.31)
            ctx.rectangle(x - 0.07, y, 0.14, 0.62)
            ctx.fill()
            ctx.move_to(x - 0.18, y + 0.62)
            ctx.line_to(x + 0.18, y + 0.62)
            ctx.line_to(x + 0.1, y + 0.74)
            ctx.line_to(x - 0.1, y + 0.74)
            ctx.close_path()
            ctx.fill()
        elif kind == 'skylight':
            ctx.set_source_rgb(0.2, 0.21, 0.28)
            ctx.rectangle(x - 0.9, y, 1.8, 0.25)
            ctx.fill()
            ctx.set_source_rgba(0.55, 0.65, 0.85, 0.35)
            ctx.move_to(x - 0.85, y + 0.25)
            ctx.line_to(x, y + 0.6)
            ctx.line_to(x + 0.85, y + 0.25)
            ctx.close_path()
            ctx.fill()
            ctx.set_source_rgba(0, 0, 0, 0.4)
            ctx.set_line_width(0.02)
            for k in range(-3, 4):
                ctx.move_to(x + k * 0.24, y + 0.25)
                ctx.line_to(x + k * 0.24 * 0.1, y + 0.6 - abs(k) * 0.03)
            ctx.stroke()
        elif kind == 'mast':
            ctx.set_source_rgb(0.16, 0.16, 0.22)
            ctx.set_line_width(0.04)
            ctx.move_to(x, y)
            ctx.line_to(x, y + 3.2)
            ctx.stroke()
            ctx.set_line_width(0.02)
            for h in (1.2, 2.0, 2.7):
                ctx.move_to(x - 0.3 * (3.4 - h) / 2, y + h)
                ctx.line_to(x + 0.3 * (3.4 - h) / 2, y + h)
            ctx.stroke()
            ctx.move_to(x, y + 3.0)
            ctx.line_to(x - 0.8, y)
            ctx.move_to(x, y + 3.0)
            ctx.line_to(x + 0.8, y)
            ctx.set_line_width(0.008)
            ctx.stroke()
            if math.sin(t * 2.0) > 0:
                g = cairo.RadialGradient(x, y + 3.2, 0, x, y + 3.2, 0.18)
                g.add_color_stop_rgba(0, 1.0, 0.2, 0.15, 0.9)
                g.add_color_stop_rgba(1, 1.0, 0.2, 0.15, 0.0)
                ctx.set_source(g)
                ctx.arc(x, y + 3.2, 0.18, 0, 2 * math.pi)
                ctx.fill()

    def tower(self, ctx, a, t):
        X = TOWER_X
        ctx.set_line_cap(cairo.LINE_CAP_BUTT)
        # legs and cross bracing
        ctx.set_source_rgb(*IRON)
        for k, dx in enumerate(LEGS):
            w = 0.12 if k in (0, 3) else 0.09
            ctx.rectangle(X + dx * TANK_R - w / 2, 0, w, TANK_Y0)
            ctx.fill()
        ctx.set_line_width(0.035)
        for i in range(len(LEGS) - 1):
            xa, xb = X + LEGS[i] * TANK_R, X + LEGS[i + 1] * TANK_R
            for y0, y1 in ((0.15, 1.15), (1.15, 2.2)):
                ctx.move_to(xa, y0)
                ctx.line_to(xb, y1)
                ctx.move_to(xa, y1)
                ctx.line_to(xb, y0)
        ctx.stroke()
        ctx.rectangle(X - TANK_R * 1.08, TANK_Y0 - 0.1, TANK_R * 2.16, 0.12)
        ctx.fill()
        # the tank: wooden staves, iron hoops, moonlit right edge
        x0, x1 = X - TANK_R, X + TANK_R
        g = cairo.LinearGradient(x0, 0, x1, 0)
        g.add_color_stop_rgb(0, *WOOD_DK)
        g.add_color_stop_rgb(0.6, *WOOD)
        g.add_color_stop_rgb(0.92, *[min(1, c * 1.35) for c in WOOD])
        g.add_color_stop_rgb(1, *WOOD_DK)
        ctx.set_source(g)
        ctx.rectangle(x0, TANK_Y0, x1 - x0, TANK_Y1 - TANK_Y0)
        ctx.fill()
        ctx.set_source_rgba(0, 0, 0, 0.3)
        for k in range(1, 16):
            u = k / 16.0
            xs = X - TANK_R * math.cos(math.pi * u)
            ctx.rectangle(xs - 0.008, TANK_Y0, 0.016, TANK_Y1 - TANK_Y0)
        ctx.fill()
        ctx.set_source_rgb(*IRON)
        for hy in (TANK_Y0 + 0.25, TANK_Y0 + 0.9, TANK_Y0 + 1.55, TANK_Y1 - 0.2):
            ctx.rectangle(x0 - 0.01, hy, x1 - x0 + 0.02, 0.05)
        ctx.fill()
        # conical roof and finial
        ctx.set_source_rgb(*WOOD_DK)
        ctx.move_to(x0 - 0.1, TANK_Y1)
        ctx.line_to(X, TANK_Y1 + 0.75)
        ctx.line_to(x1 + 0.1, TANK_Y1)
        ctx.close_path()
        ctx.fill()
        ctx.set_source_rgba(*RIM, 0.35)
        ctx.set_line_width(0.025)
        ctx.move_to(X, TANK_Y1 + 0.75)
        ctx.line_to(x1 + 0.1, TANK_Y1)
        ctx.stroke()
        ctx.set_source_rgb(*IRON)
        ctx.rectangle(X - 0.035, TANK_Y1 + 0.7, 0.07, 0.22)
        ctx.fill()
        ctx.arc(X, TANK_Y1 + 0.93, 0.075, 0, 2 * math.pi)
        ctx.fill()
        ctx.set_source_rgba(*RIM, 0.4)
        ctx.arc(X + 0.02, TANK_Y1 + 0.95, 0.03, 0, 2 * math.pi)
        ctx.fill()
        # ladder up the right side
        ctx.set_source_rgba(*IRON, 1)
        ctx.set_line_width(0.025)
        lx = x1 + 0.12
        ctx.move_to(lx, 0)
        ctx.line_to(lx, TANK_Y1)
        ctx.move_to(lx + 0.3, 0)
        ctx.line_to(lx + 0.3, TANK_Y0)
        ctx.stroke()
        ctx.set_line_width(0.018)
        for k in range(int(TANK_Y1 / 0.3)):
            ctx.move_to(lx, k * 0.3 + 0.15)
            ctx.line_to(lx + (0.3 if k * 0.3 < TANK_Y0 else 0.12), k * 0.3 + 0.15)
        ctx.stroke()
        # rim light on the right edge of the tank
        ctx.set_source_rgba(*RIM, 0.3)
        ctx.rectangle(x1 - 0.035, TANK_Y0, 0.035, TANK_Y1 - TANK_Y0)
        ctx.fill()
        if self.hole and a >= self.hole[0]:
            _, hx, hy = self.hole
            ctx.set_source_rgb(0.04, 0.03, 0.04)
            ctx.save()
            ctx.translate(hx, hy)
            ctx.scale(0.16, 0.2)
            ctx.arc(0, 0, 1, 0, 2 * math.pi)
            ctx.restore()
            ctx.fill()
            ctx.set_line_width(0.03)
            ctx.set_source_rgba(0.55, 1.0, 0.6, 0.35 + 0.2 * math.sin(t * 9))
            ctx.save()
            ctx.translate(hx, hy)
            ctx.scale(0.18, 0.22)
            ctx.arc(0, 0, 1, 0, 2 * math.pi)
            ctx.restore()
            ctx.stroke()

    def draw_shadow(self, R, ctx, J):
        lowest = min(J.ankle_n[1], J.ankle_f[1], J.hip[1])
        h = max(0.0, lowest - 0.05)
        k = 1.0 / (1.0 + 1.6 * h)
        xs = [J.ankle_n[0], J.ankle_f[0], J.hip[0], J.head[0]]
        cx = (min(xs) + max(xs)) / 2
        w = (max(xs) - min(xs)) / 2 + 0.35
        ctx.save()
        ctx.translate(cx, 0.0)
        ctx.scale(w * (0.8 + 0.2 * k), 0.07 * w)
        g = cairo.RadialGradient(0, 0, 0, 0, 0, 1)
        g.add_color_stop_rgba(0, 0, 0, 0, 0.6 * k)
        g.add_color_stop_rgba(1, 0, 0, 0, 0)
        ctx.set_source(g)
        ctx.arc(0, 0, 1, 0, 2 * math.pi)
        ctx.fill()
        ctx.restore()

    # --------------------------------------------------------------- foreground
    def draw_front(self, R, ctx, cam, a):
        for x, d, r in GRAVEL:
            if abs(x - cam['cx'] * d) > 14:
                continue
            R.layer(ctx, cam, d)
            y = ground_at(d)
            ctx.set_source_rgba(0.08, 0.08, 0.11, 0.55)
            ctx.save()
            ctx.translate(x, y)
            ctx.scale(1, 0.45)
            ctx.arc(0, 0, r, 0, 2 * math.pi)
            ctx.restore()
            ctx.fill()


def tank_left_edge():
    return TOWER_X - TANK_R
