"""Effects: sparks, dust, debris, shockwave rings, cracks, speed lines,
afterimages and limb smears. All effects are spawned explicitly by the
sequence script at chosen frames -- nothing is emitted automatically."""
import math
import random

import cairo

from rig import solve, draw_figure, draw_arm, draw_leg, capsule, DISCRETE

FPS = 24
DUST = (0.66, 0.61, 0.66)
HOT = [(1.0, 1.0, 0.95), (1.0, 0.86, 0.45), (1.0, 0.55, 0.2)]


class Particle:
    __slots__ = ('kind', 'x', 'y', 'vx', 'vy', 'life', 'age', 'r', 'grow', 'col', 'alpha', 'g',
                 'drag', 'w', 'rot', 'vr', 'squash', 'bounce')

    def __init__(self, kind, x, y, vx=0.0, vy=0.0, life=12, r=0.05, grow=0.0, col=(1, 1, 1),
                 alpha=1.0, g=0.0, drag=1.0, w=0.02, squash=1.0, bounce=0.0):
        self.kind, self.x, self.y, self.vx, self.vy = kind, x, y, vx, vy
        self.life, self.age, self.r, self.grow, self.col = life, 0, r, grow, col
        self.alpha, self.g, self.drag, self.w, self.squash = alpha, g, drag, w, squash
        self.rot = random.uniform(0, math.pi)
        self.vr = random.uniform(-8, 8)
        self.bounce = bounce


class FX:
    def __init__(self, seed=7):
        self.ps = []
        self.decals = []          # persistent ground marks
        self.ghosts = []          # afterimages (joints, colour, age, life, alpha)
        self.flash = 0.0          # screen flash level
        self.flash_col = (1, 1, 1)
        self.rnd = random.Random(seed)

    # ------------------------------------------------------------ spawners
    def sparks(self, x, y, dirx, diry, n=18, speed=9.0, spread=0.9, life=(5, 11)):
        R = self.rnd
        base = math.atan2(diry, dirx)
        for _ in range(n):
            a = base + R.gauss(0, spread)
            s = speed * R.uniform(0.35, 1.0)
            self.ps.append(Particle('spark', x, y, math.cos(a) * s, math.sin(a) * s,
                                    life=R.randint(*life), col=R.choice(HOT), g=4.0, drag=0.86,
                                    w=R.uniform(0.012, 0.026)))

    def dust(self, x, y=0.04, n=8, dirx=0.0, speed=1.5, size=0.16, life=(10, 20), up=0.6, alpha=0.5):
        """Low, flat puffs that spread and dissipate quickly."""
        R = self.rnd
        n = max(1, int(round(n * 0.7)))
        for _ in range(n):
            self.ps.append(Particle('dust', x + R.uniform(-0.12, 0.12), y + R.uniform(0, 0.05),
                                    dirx * speed * R.uniform(0.4, 1.1) + R.uniform(-0.5, 0.5),
                                    up * R.uniform(0.15, 0.8), life=R.randint(*life),
                                    r=size * R.uniform(0.45, 0.9), grow=size * 0.16, col=DUST,
                                    alpha=alpha * 0.42 * R.uniform(0.6, 1.0), drag=0.86, squash=0.62))

    def debris(self, x, n=10, speed=4.0, up=5.0):
        R = self.rnd
        for _ in range(n):
            self.ps.append(Particle('debris', x + R.uniform(-0.15, 0.15), 0.05, R.uniform(-speed, speed),
                                    up * R.uniform(0.4, 1.0), life=R.randint(16, 30), r=R.uniform(0.02, 0.05),
                                    col=(0.33, 0.29, 0.34), g=1.6, drag=0.97, bounce=0.35))

    def ring(self, x, y, r0=0.1, r1=1.2, life=8, w=0.08, squash=1.0, col=(1, 0.95, 0.85), alpha=0.9):
        p = Particle('ring', x, y, life=life, r=r0, grow=(r1 - r0), col=col, alpha=alpha, w=w,
                     squash=squash)
        self.ps.append(p)

    def burst(self, x, y, size=0.6, life=4, col=(1, 0.97, 0.9)):
        self.ps.append(Particle('burst', x, y, life=life, r=size, col=col))

    def streak(self, x, y, length=3.0, life=4, col=(1, 0.9, 0.7), w=0.03):
        self.ps.append(Particle('streak', x, y, life=life, r=length, col=col, w=w))

    def crack(self, x, n=7, length=1.4):
        R = self.rnd
        lines = []
        for i in range(n):
            a = (i / (n - 1) - 0.5) * 2.4
            px, py = x, 0.0
            pts = [(px, py)]
            L = length * R.uniform(0.5, 1.0)
            for k in range(4):
                px += math.sin(a + R.uniform(-0.4, 0.4)) * L / 4
                py += -abs(math.cos(a)) * L / 4 * 0.08
                pts.append((px, py))
            lines.append(pts)
        self.decals.append(('crack', lines))

    def speedlines(self, x, y, dirx, n=6, length=2.2, life=3, spread=0.8):
        R = self.rnd
        for _ in range(n):
            self.ps.append(Particle('line', x - dirx * R.uniform(0.2, 1.0), y + R.uniform(-spread, spread),
                                    -dirx * 4, 0, life=life, r=length * R.uniform(0.5, 1.0),
                                    col=(1, 1, 1), alpha=R.uniform(0.25, 0.55), w=R.uniform(0.008, 0.018)))

    def embers(self, J, n=2, heat=1.0):
        """KAI's signature: sparks of heat lifting off the body."""
        R = self.rnd
        pts = [J.hip, J.chest, J.head, J.hand_n, J.hand_f, J.elbow_n, J.knee_n]
        for _ in range(n):
            x, y = R.choice(pts)
            self.ps.append(Particle('ember', x + R.uniform(-0.08, 0.08), y + R.uniform(-0.08, 0.08),
                                    R.uniform(-0.25, 0.25), R.uniform(0.5, 1.4) * heat, life=R.randint(12, 26),
                                    r=R.uniform(0.008, 0.02) * (0.8 + 0.4 * heat),
                                    col=R.choice([(1.0, 0.75, 0.3), (1.0, 0.55, 0.2), (1.0, 0.9, 0.6)]),
                                    g=-0.02, drag=0.97))

    def ghost(self, J, col, life=6, alpha=0.45):
        self.ghosts.append([J, col, 0, life, alpha])

    def flash_screen(self, level=1.0, col=(1, 1, 1)):
        self.flash = level
        self.flash_col = col

    # ------------------------------------------------------------ update
    def step(self):
        dt = 1.0 / FPS
        alive = []
        for p in self.ps:
            p.age += 1
            if p.age > p.life:
                continue
            p.vx *= p.drag
            p.vy = p.vy * p.drag - 9.8 * p.g * dt
            p.x += p.vx * dt
            p.y += p.vy * dt
            p.rot += p.vr * dt
            if p.kind == 'debris' and p.y < 0.02 and p.vy < 0:
                p.y = 0.02
                p.vy = -p.vy * p.bounce
                p.vx *= 0.6
            alive.append(p)
        self.ps = alive
        for g in self.ghosts:
            g[2] += 1
        self.ghosts = [g for g in self.ghosts if g[2] < g[3]]
        self.flash *= 0.35

    # ------------------------------------------------------------ drawing
    def skidmark(self, x0, x1, y=0.0, w=0.035):
        self.decals.append(('skid', [[(x0, y), (x1, y)]], w))

    def glint(self, x, y, size=0.12, life=7, col=(1, 0.95, 0.85)):
        self.ps.append(Particle('glint', x, y, life=life, r=size, col=col))

    def draw_decals(self, ctx, px):
        for d in self.decals:
            kind, lines = d[0], d[1]
            if kind == 'skid':
                ctx.set_line_cap(cairo.LINE_CAP_ROUND)
                ctx.set_source_rgba(0.10, 0.08, 0.12, 0.55)
                ctx.set_line_width(d[2])
                for pts in lines:
                    ctx.move_to(*pts[0])
                    ctx.line_to(*pts[1])
                    ctx.stroke()
                continue
            ctx.set_source_rgba(0.12, 0.10, 0.14, 0.75)
            ctx.set_line_cap(cairo.LINE_CAP_ROUND)
            for pts in lines:
                ctx.set_line_width(max(1.2 * px, 0.018))
                ctx.move_to(*pts[0])
                for q in pts[1:]:
                    ctx.line_to(*q)
                ctx.stroke()

    def draw_ghosts(self, ctx):
        for J, col, age, life, alpha in self.ghosts:
            a = alpha * (1 - age / life) ** 1.5
            ctx.push_group()
            draw_figure(ctx, J, style='flat', near=col)
            ctx.pop_group_to_source()
            ctx.paint_with_alpha(a)

    def draw(self, ctx, px, layer='front'):
        """px = world size of one pixel (for minimum line widths)."""
        for p in self.ps:
            t = p.age / max(p.life, 1)
            if p.kind == 'spark':
                ctx.set_line_cap(cairo.LINE_CAP_ROUND)
                ctx.set_source_rgba(*p.col, 1 - t * t)
                ctx.set_line_width(max(p.w * (1 - t * 0.6), 1.2 * px))
                ctx.move_to(p.x, p.y)
                ctx.line_to(p.x - p.vx * 0.022, p.y - p.vy * 0.022)
                ctx.stroke()
            elif p.kind == 'dust':
                r = p.r + p.grow * p.age * (1 - 0.5 * t)
                a = p.alpha * (1 - t) ** 1.6
                ctx.save()
                ctx.translate(p.x, p.y)
                ctx.scale(1.0, p.squash)
                g = cairo.RadialGradient(0, 0, 0, 0, 0, r)
                g.add_color_stop_rgba(0, *p.col, a)
                g.add_color_stop_rgba(0.45, *p.col, a * 0.7)
                g.add_color_stop_rgba(1, *p.col, 0)
                ctx.set_source(g)
                ctx.arc(0, 0, r, 0, 2 * math.pi)
                ctx.fill()
                ctx.restore()
            elif p.kind == 'debris':
                ctx.save()
                ctx.translate(p.x, p.y)
                ctx.rotate(p.rot)
                ctx.set_source_rgba(*p.col, 1 - max(0, t - 0.7) / 0.3)
                ctx.move_to(-p.r, -p.r * 0.6)
                ctx.line_to(p.r, -p.r * 0.3)
                ctx.line_to(p.r * 0.2, p.r * 0.8)
                ctx.close_path()
                ctx.fill()
                ctx.restore()
            elif p.kind == 'ring':
                e = 1 - (1 - t) ** 3
                r = p.r + p.grow * e
                ctx.save()
                ctx.translate(p.x, p.y)
                ctx.scale(1, p.squash)
                ctx.set_source_rgba(*p.col, p.alpha * (1 - t) ** 1.2)
                ctx.set_line_width(max(p.w * (1 - t * 0.85), 1.0 * px) / max(p.squash, 0.2) * min(1.0, p.squash * 2))
                ctx.arc(0, 0, r, 0, 2 * math.pi)
                ctx.stroke()
                ctx.restore()
            elif p.kind == 'burst':
                r = p.r * (1 + t * 0.6)
                g = cairo.RadialGradient(p.x, p.y, 0, p.x, p.y, r)
                g.add_color_stop_rgba(0, *p.col, 1 - t)
                g.add_color_stop_rgba(0.25, *p.col, 0.85 * (1 - t))
                g.add_color_stop_rgba(1, *p.col, 0)
                ctx.set_source(g)
                ctx.arc(p.x, p.y, r, 0, 2 * math.pi)
                ctx.fill()
                # star spikes
                ctx.set_source_rgba(*p.col, (1 - t) * 0.9)
                for k in range(8):
                    a = k * math.pi / 4 + 0.3
                    L = r * (1.7 if k % 2 == 0 else 1.0)
                    w = r * 0.07
                    ctx.move_to(p.x + math.cos(a + 1.57) * w, p.y + math.sin(a + 1.57) * w)
                    ctx.line_to(p.x + math.cos(a) * L, p.y + math.sin(a) * L)
                    ctx.line_to(p.x - math.cos(a + 1.57) * w, p.y - math.sin(a + 1.57) * w)
                    ctx.close_path()
                    ctx.fill()
            elif p.kind == 'streak':
                a = (1 - t)
                g = cairo.LinearGradient(p.x - p.r, p.y, p.x + p.r, p.y)
                g.add_color_stop_rgba(0, *p.col, 0)
                g.add_color_stop_rgba(0.5, *p.col, a)
                g.add_color_stop_rgba(1, *p.col, 0)
                ctx.set_source(g)
                ctx.rectangle(p.x - p.r, p.y - p.w * a / 2, 2 * p.r, p.w * a)
                ctx.fill()
            elif p.kind == 'ember':
                fl = 0.6 + 0.4 * math.sin(p.age * 1.7 + p.rot * 5)
                a = (1 - t) * fl
                g = cairo.RadialGradient(p.x, p.y, 0, p.x, p.y, p.r * 3)
                g.add_color_stop_rgba(0, *p.col, a)
                g.add_color_stop_rgba(0.35, *p.col, a * 0.6)
                g.add_color_stop_rgba(1, *p.col, 0)
                ctx.set_source(g)
                ctx.arc(p.x, p.y, p.r * 3, 0, 2 * math.pi)
                ctx.fill()
                p.vx += math.sin(p.age * 0.5 + p.rot) * 0.03
            elif p.kind == 'glint':
                k = math.sin(math.pi * min(1.0, t * 1.4))
                r = p.r * (0.4 + 0.8 * k)
                ctx.set_source_rgba(*p.col, k)
                for a, L in ((0, 1.0), (math.pi / 2, 0.55), (math.pi, 1.0), (3 * math.pi / 2, 0.55)):
                    w = r * 0.09
                    ctx.move_to(p.x + math.cos(a + 1.57) * w, p.y + math.sin(a + 1.57) * w)
                    ctx.line_to(p.x + math.cos(a) * r * L, p.y + math.sin(a) * r * L)
                    ctx.line_to(p.x - math.cos(a + 1.57) * w, p.y - math.sin(a + 1.57) * w)
                    ctx.close_path()
                    ctx.fill()
                g = cairo.RadialGradient(p.x, p.y, 0, p.x, p.y, r * 0.5)
                g.add_color_stop_rgba(0, *p.col, k)
                g.add_color_stop_rgba(1, *p.col, 0)
                ctx.set_source(g)
                ctx.arc(p.x, p.y, r * 0.5, 0, 2 * math.pi)
                ctx.fill()
            elif p.kind == 'line':
                ctx.set_source_rgba(*p.col, p.alpha * (1 - t))
                ctx.set_line_width(max(p.w, px))
                ctx.move_to(p.x, p.y)
                ctx.line_to(p.x + (p.r if p.vx > 0 else -p.r), p.y)
                ctx.stroke()


# ---------------------------------------------------------------- smears
def lerp_pose(a, b, t):
    out = {}
    for k, va in a.items():
        vb = b.get(k, va)
        if k in DISCRETE or not isinstance(va, (int, float)) or va is None or vb is None:
            out[k] = vb
        else:
            out[k] = va + (vb - va) * t
    return out


def draw_smear(ctx, build, prev_pose, cur_pose, limbs, strength=1.0, steps=None):
    """Fill the arc a limb swept between the previous drawing and this one.

    The swept copies are interpolated in joint-angle space, so the smear
    follows the real arc of the strike, then composited semi-transparent
    *behind* the opaque current drawing. The number of copies scales with
    how far the limb's end travelled, so long sweeps stay solid."""
    if prev_pose is None or prev_pose.get('face') != cur_pose.get('face'):
        return
    J0, J1 = solve(build, prev_pose), solve(build, cur_pose)
    ends = {'an': 'hand_n', 'af': 'hand_f', 'ln': 'toe_n', 'lf': 'toe_f'}
    travel = max([math.dist(getattr(J0, ends[l]), getattr(J1, ends[l])) for l in limbs if l in ends] + [0.2])
    if steps is None:
        steps = int(min(64, max(12, travel / (build.w_wrist * 0.35))))
    ctx.push_group()
    for i in range(steps):
        t = i / steps
        p = lerp_pose(prev_pose, cur_pose, t)
        J = solve(build, p)
        a = (0.15 + 0.85 * t) ** 1.6
        ctx.push_group()
        for limb in limbs:
            if limb == 'an':
                ctx.set_source_rgb(*build.near)
                draw_arm(ctx, build, J.shoulder_n, J.elbow_n, J.hand_n, p['hn'], J.face)
            elif limb == 'af':
                ctx.set_source_rgb(*build.far)
                draw_arm(ctx, build, J.shoulder_f, J.elbow_f, J.hand_f, p['hf'], J.face)
            elif limb == 'ln':
                ctx.set_source_rgb(*build.near)
                draw_leg(ctx, build, J.hip_n, J.knee_n, J.ankle_n, J.toe_n)
            elif limb == 'lf':
                ctx.set_source_rgb(*build.far)
                draw_leg(ctx, build, J.hip_f, J.knee_f, J.ankle_f, J.toe_f)
            elif limb == 'body':
                draw_figure(ctx, J, style='flat', near=build.near)
        ctx.pop_group_to_source()
        ctx.paint_with_alpha(min(1.0, a * 0.32 * 16.0 / steps * 1.6))
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(min(1.0, 0.95 * strength))
