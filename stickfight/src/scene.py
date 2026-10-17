"""Sequence container + renderer (background, camera, actors, FX, post)."""
import math
import os
import random
import subprocess
from collections import defaultdict

import cairo
import numpy as np

from rig import solve, draw_figure, hair_anchor, hexrgb
from engine import CamTrack, Shake, build_frame_map, chains_for_build, lerp, FPS
from fx import FX, draw_smear

# ------------------------------------------------------------------ palette
SKY_TOP = hexrgb('#0A0C18')
SKY_MID = hexrgb('#181A2E')
SKY_LOW = hexrgb('#3A3654')
GLOW = hexrgb('#7A6175')
MOON = hexrgb('#ECE6D8')
MESA_FAR = hexrgb('#363350')
MESA_MID = hexrgb('#272439')
GROUND_FAR = hexrgb('#4C4459')
GROUND_NEAR = hexrgb('#1F1B27')
H0 = 4.6        # reference view height (m) of a standard wide shot
HZ = 1.45       # horizon world height for the farthest layer
YC = 1.0        # camera height at which the horizon sits at its default place


def _ridge(seed, x0, x1, base, amp, step, rough=0.55):
    R = random.Random(seed)
    pts = []
    x = x0
    y = base
    while x <= x1:
        pts.append((x, y))
        x += step * R.uniform(0.6, 1.4)
        y = base + amp * (R.random() ** 1.6) * (1 if R.random() < 0.7 else 0.3)
        if R.random() < 0.25:            # flat-topped mesas
            pts.append((x, y))
            x += step * R.uniform(1.5, 3.5)
            pts.append((x, y))
    return pts


MESA_FAR_PTS = _ridge(3, -40, 40, HZ + 0.02, 0.55, 0.9)
MESA_MID_PTS = _ridge(11, -40, 40, HZ - 0.15, 0.35, 0.7)
_R = random.Random(5)
GROUND_MARKS = [(_R.uniform(-40, 40), _R.uniform(0.15, 1.9), _R.uniform(0.3, 2.2)) for _ in range(520)]
PEBBLES = [(_R.uniform(-40, 40), _R.uniform(0.7, 2.4), _R.uniform(0.012, 0.035)) for _ in range(160)]
CLOUDS = [(_R.uniform(-30, 30), _R.uniform(HZ + 0.9, HZ + 2.6), _R.uniform(1.5, 5.0), _R.uniform(0.03, 0.08))
          for _ in range(20)]


class Actor:
    def __init__(self, track, z=0):
        self.track = track
        self.b = track.b
        self.chains = chains_for_build(self.b)
        self.prev_pose = None
        self.prev_a = None
        self.z = z
        self.visible = [(-10 ** 9, 10 ** 9)]
        self.J = None
        self.pose = None


class Sequence:
    def __init__(self, name, n_anim, wind=-0.4):
        self.name = name
        self.n = n_anim
        self.actors = {}
        self.cam = CamTrack()
        self.events = defaultdict(list)
        self.emitters = []
        self.hitstops = {}
        self.impacts = {}           # anim frame -> (style, x, y)
        self.fades = []             # (f0, f1, a0, a1)
        self.cards = []             # (f0, f1, drawfn)
        self.zorders = []           # (f, [names back..front])
        self.wind = wind
        self.cam_follow = None
        self.sound = []             # (anim frame, kind, gain) cues for the audio pass
        self.notes = {}             # anim frame -> annotation (timeline doc)
        self.glow = {}              # actor name -> fn(anim frame) eye-glow intensity
        self.depth = []             # (f0, f1, actor, amount) atmospheric tint when passing behind

    def wind_at(self, a):
        return self.wind(a) if callable(self.wind) else self.wind

    def add(self, track, z=0):
        self.actors[track.name] = Actor(track, z)
        return self.actors[track.name]

    def at(self, f, fn):
        self.events[f].append(fn)

    def emit(self, f0, f1, fn):
        self.emitters.append((f0, f1, fn))

    def sfx(self, f, kind, gain=1.0):
        self.sound.append((f, kind, gain))

    def note(self, f, text):
        self.notes[f] = text

    def hitstop(self, f, n):
        self.hitstops[f] = self.hitstops.get(f, 0) + n

    def impact(self, f, x, y, dirx=1.0, diry=0.0, power=1.0, style=None, stop=None, ring=True,
               sparks=True, shake=True, sound='hit'):
        """One-call impact package: hit-stop, optional flash frame, ring, sparks, shake."""
        stop = stop if stop is not None else int(round(1 + 2.5 * power))
        if stop:
            self.hitstop(f, stop)
        if style:
            self.impacts[f] = (style, x, y)
        if sound:
            self.sfx(f, sound, power)

        def ev(fx, scene, rf):
            fx.burst(x, y, size=0.16 + 0.2 * power, life=3 + int(power * 2))
            if ring:
                fx.ring(x, y, 0.06, 0.4 + 0.5 * power, life=6 + int(3 * power), w=0.03 + 0.03 * power)
            if sparks:
                fx.sparks(x, y, dirx, diry, n=int(8 + 14 * power), speed=5 + 5 * power)
            fx.streak(x, y, length=0.7 + 1.1 * power, life=3 + int(2 * power), w=0.02 + 0.015 * power)
            if shake:
                scene.shake.add(rf, 0.04 + 0.07 * power, frames=6 + int(5 * power), dx=dirx, dy=diry * 0.5 + 0.3,
                                seed=f)
        self.at(f, ev)

    def fade(self, f0, f1, a0, a1):
        self.fades.append((f0, f1, a0, a1))

    def zorder(self, f, names):
        self.zorders.append((f, names))


# ---------------------------------------------------------------- renderer
class Renderer:
    def __init__(self, W=1280, H=720, grain=True, debug=False):
        self.W, self.H = W, H
        self.grain = grain
        self.debug = debug
        self.rng = np.random.default_rng(1)

    def vignette(self):
        if getattr(self, '_vig', None) is None:
            W, H = self.W, self.H
            v = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
            c = cairo.Context(v)
            g = cairo.RadialGradient(W / 2, H / 2, H * 0.35, W / 2, H / 2, H * 0.95)
            g.add_color_stop_rgba(0, 0, 0, 0, 0)
            g.add_color_stop_rgba(1, 0, 0, 0, 0.55)
            c.set_source(g)
            c.paint()
            self._vig = v
        return self._vig

    # camera transforms ---------------------------------------------------
    def layer(self, ctx, cam, d):
        """Set world->screen transform for a parallax layer at depth d (1 = fighters)."""
        W, H = self.W, self.H
        z = H0 / cam['h']
        s = (H / H0) * z ** d
        ctx.identity_matrix()
        ctx.translate(W / 2 + cam['sx'] * H / cam['h'], H / 2 + cam['sy'] * H / cam['h'] + cam['tilt'] * H)
        ctx.rotate(cam['rot'] * math.pi / 180 * d)
        ctx.scale(s, -s)
        ctx.translate(-cam['cx'] * d, -(cam['cy'] * d + YC * (1 - d)))
        return s

    def horizon_y(self, cam):
        W, H = self.W, self.H
        return H / 2 - (H / H0) * (HZ - YC) + cam['sy'] * H / cam['h'] + cam['tilt'] * H

    # background ------------------------------------------------------------
    def draw_bg(self, ctx, cam, t):
        W, H = self.W, self.H
        ctx.identity_matrix()
        hy = self.horizon_y(cam)
        g = cairo.LinearGradient(0, 0, 0, hy)
        g.add_color_stop_rgb(0, *SKY_TOP)
        g.add_color_stop_rgb(0.55, *SKY_MID)
        g.add_color_stop_rgb(0.92, *SKY_LOW)
        g.add_color_stop_rgb(1.0, *GLOW)
        ctx.set_source(g)
        ctx.rectangle(0, 0, W, hy + 2)
        ctx.fill()
        # moon
        self.layer(ctx, cam, 0.015)
        mx, my, mr = cam['moon_x'], YC + cam['moon_dy'], cam['moon_r']
        g = cairo.RadialGradient(mx, my, mr * 0.9, mx, my, mr * 4)
        g.add_color_stop_rgba(0, *MOON, 0.22)
        g.add_color_stop_rgba(1, *MOON, 0)
        ctx.set_source(g)
        ctx.arc(mx, my, mr * 4, 0, 2 * math.pi)
        ctx.fill()
        ctx.set_source_rgb(*MOON)
        ctx.arc(mx, my, mr, 0, 2 * math.pi)
        ctx.fill()
        ctx.set_source_rgba(0.75, 0.72, 0.72, 0.35)
        for ox, oy, rr in ((-0.12, 0.08, 0.1), (0.1, -0.12, 0.07), (0.15, 0.13, 0.05)):
            ctx.arc(mx + ox, my + oy, rr, 0, 2 * math.pi)
            ctx.fill()
        # clouds (slow drift)
        self.layer(ctx, cam, 0.04)
        for cx, cy, w, h in CLOUDS:
            x = ((cx + t * 0.06 + 30) % 60) - 30
            g = cairo.LinearGradient(x - w, 0, x + w, 0)
            g.add_color_stop_rgba(0, 0.36, 0.33, 0.45, 0)
            g.add_color_stop_rgba(0.5, 0.36, 0.33, 0.45, 0.16)
            g.add_color_stop_rgba(1, 0.36, 0.33, 0.45, 0)
            ctx.set_source(g)
            ctx.save()
            ctx.translate(x, cy)
            ctx.scale(w, h)
            ctx.arc(0, 0, 1, 0, 2 * math.pi)
            ctx.restore()
            ctx.fill()
        # mesas
        for pts, d, col in ((MESA_FAR_PTS, 0.08, MESA_FAR), (MESA_MID_PTS, 0.22, MESA_MID)):
            self.layer(ctx, cam, d)
            ctx.set_source_rgb(*col)
            ctx.move_to(pts[0][0], HZ - 3)
            for x, y in pts:
                ctx.line_to(x, y)
            ctx.line_to(pts[-1][0], HZ - 3)
            ctx.close_path()
            ctx.fill()
        # ground plane
        ctx.identity_matrix()
        gy = hy - 1
        g = cairo.LinearGradient(0, gy, 0, H)
        g.add_color_stop_rgb(0, *GROUND_FAR)
        g.add_color_stop_rgb(0.35, *[lerp(a, b, 0.55) for a, b in zip(GROUND_FAR, GROUND_NEAR)])
        g.add_color_stop_rgb(1, *GROUND_NEAR)
        ctx.set_source(g)
        ctx.rectangle(0, gy, W, H - gy)
        ctx.fill()
        # horizon haze line
        g = cairo.LinearGradient(0, gy - 30, 0, gy + 40)
        g.add_color_stop_rgba(0, *GLOW, 0)
        g.add_color_stop_rgba(0.45, *GLOW, 0.35)
        g.add_color_stop_rgba(1, *GLOW, 0)
        ctx.set_source(g)
        ctx.rectangle(0, gy - 30, W, 70)
        ctx.fill()
        # ground streaks at many depths (perspective scroll)
        for x, d, L in GROUND_MARKS:
            if abs(x - cam['cx'] * d) > 18:
                continue
            s = self.layer(ctx, cam, d)
            y = HZ * (1 - d)
            a = min(0.22, 0.05 + 0.12 * d)
            ctx.set_source_rgba(0.09, 0.08, 0.11, a)
            ctx.set_line_width(max(0.012, 1.0 / s) * (0.5 + d * 0.5))
            ctx.move_to(x - L / 2, y)
            ctx.line_to(x + L / 2, y)
            ctx.stroke()
            ctx.set_source_rgba(0.75, 0.70, 0.78, a * 0.35)
            ctx.move_to(x - L * 0.3, y + 0.6 / s)
            ctx.line_to(x + L * 0.3, y + 0.6 / s)
            ctx.stroke()

    def draw_pebbles(self, ctx, cam):
        for x, d, r in PEBBLES:
            if abs(x - cam['cx'] * d) > 14:
                continue
            self.layer(ctx, cam, d)
            y = HZ * (1 - d)
            ctx.set_source_rgba(0.13, 0.11, 0.15, 0.45)
            ctx.save()
            ctx.translate(x, y)
            ctx.scale(1, 0.45)
            ctx.arc(0, 0, r, 0, 2 * math.pi)
            ctx.restore()
            ctx.fill()

    def draw_shadow(self, ctx, J):
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
        g.add_color_stop_rgba(0, 0, 0, 0, 0.55 * k)
        g.add_color_stop_rgba(1, 0, 0, 0, 0)
        ctx.set_source(g)
        ctx.arc(0, 0, 1, 0, 2 * math.pi)
        ctx.restore()
        ctx.fill()

    # impact-frame backgrounds ---------------------------------------------
    def draw_impact_bg(self, ctx, style, cam, x, y):
        W, H = self.W, self.H
        ctx.identity_matrix()
        if style == 'dark':
            g = cairo.LinearGradient(0, 0, 0, H)
            g.add_color_stop_rgb(0, 0.04, 0.01, 0.03)
            g.add_color_stop_rgb(0.6, 0.20, 0.03, 0.06)
            g.add_color_stop_rgb(1, 0.06, 0.01, 0.02)
            ctx.set_source(g)
            ctx.paint()
        elif style == 'white':
            ctx.set_source_rgb(0.97, 0.95, 0.92)
            ctx.paint()
        elif style == 'focus':
            ctx.set_source_rgb(0.95, 0.93, 0.9)
            ctx.paint()
        # radial focus lines toward the contact point
        s = self.layer(ctx, cam, 1.0)
        R = random.Random(int(x * 100 + y * 1000))
        col = (0.95, 0.85, 0.8) if style == 'dark' else (0.05, 0.04, 0.06)
        for i in range(70):
            a = R.uniform(0, 2 * math.pi)
            r0 = R.uniform(0.5, 1.4) * cam['h'] * 0.18
            r1 = cam['h'] * 1.5
            w = R.uniform(0.004, 0.02) * cam['h']
            ctx.set_source_rgba(*col, R.uniform(0.15, 0.6))
            ctx.move_to(x + math.cos(a) * r0, y + math.sin(a) * r0)
            ctx.line_to(x + math.cos(a + w / r1) * r1, y + math.sin(a + w / r1) * r1)
            ctx.line_to(x + math.cos(a - w / r1) * r1, y + math.sin(a - w / r1) * r1)
            ctx.close_path()
            ctx.fill()

    # main loop -------------------------------------------------------------
    def frames(self, seq):
        """Generator over rendered frames: yields (rf, anim_frame, is_stop, surface)."""
        fmap = build_frame_map(seq.n, seq.hitstops)
        seq.fmap = fmap
        seq.shake = Shake()
        fx = FX(seed=hash(seq.name) % 1000)
        seq.fx = fx
        actors = list(seq.actors.values())
        # pre-roll the hair so it starts settled
        for act in actors:
            p = act.track.eval(0)
            J = solve(act.b, p)
            for ch, w0, w1, col in act.chains:
                ch.reset(hair_anchor(J), J.face)
                for _ in range(24):
                    ch.step(hair_anchor(J), J.face, seq.wind_at(0))
        mid_s = None
        last_a = -1
        surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, self.W, self.H)
        for rf, (a, stop) in enumerate(fmap):
            new_anim = a != last_a
            ctx = cairo.Context(surf)
            # --- poses
            for act in actors:
                if new_anim:
                    act.prev_pose = act.pose
                    act.pose = act.track.eval(a)
                    act.J = solve(act.b, act.pose)
                    act.smears = act.track.smear_at(a)
                act.shown = any(v0 <= a < v1 for v0, v1 in act.visible)
            # --- camera
            cam = seq.cam.eval(a)
            mids = [act.J.hip[0] for act in actors if act.shown]
            mid = sum(mids) / len(mids) if mids else cam['cx']
            mid_s = mid if mid_s is None else mid_s + (mid - mid_s) * 0.18
            if seq.cam_follow:
                mid_s = seq.cam_follow(a, mid_s)
            cam['cx'] = lerp(cam['cx'], mid_s + cam['ox'], cam['fw'])
            sx, sy = seq.shake.at(rf)
            cam['sx'], cam['sy'] = sx, sy
            # --- events
            if new_anim:
                for fn in seq.events.get(a, []):
                    fn(fx, seq, rf)
                for f0, f1, fn in seq.emitters:
                    if f0 <= a < f1:
                        fn(fx, seq, rf, a)
            # --- hair
            chains = {}
            for act in actors:
                out = []
                for ch, w0, w1, col in act.chains:
                    out.append((ch.step(hair_anchor(act.J), act.J.face, seq.wind_at(a)), w0, w1, col))
                chains[act.track.name] = out
            # --- draw
            impact = seq.impacts.get(a) if (new_anim and a in seq.impacts) else None
            if impact:
                style, ix, iy = impact
                self.draw_impact_bg(ctx, style, cam, ix, iy)
            else:
                self.draw_bg(ctx, cam, rf / FPS)
            s = self.layer(ctx, cam, 1.0)
            px = 1.0 / s
            if not impact:
                fx.draw_decals(ctx, px)
                for act in actors:
                    if act.shown:
                        self.draw_shadow(ctx, act.J)
                fx.draw_ghosts(ctx)
            order = sorted(actors, key=lambda q: q.z)
            for f0, names in sorted(seq.zorders):
                if a >= f0:
                    order = [seq.actors[n] for n in names if n in seq.actors]
            for act in order:
                if not act.shown:
                    continue
                if impact:
                    ink = (0.02, 0.0, 0.01) if impact[0] == 'dark' else (0.03, 0.03, 0.04)
                    draw_figure(ctx, act.J, style='silhouette', near=ink,
                                chains=[(c, w0, w1, ink) for c, w0, w1, col in chains[act.track.name]])
                    continue
                if not stop:
                    for limbs, strength in act.smears:
                        draw_smear(ctx, act.b, act.prev_pose, act.pose, limbs, strength)
                g = seq.glow.get(act.track.name)
                tint = 0.0
                for d0, d1, nm, amt in seq.depth:
                    if nm == act.track.name and d0 <= a < d1:
                        u = (a - d0) / max(1, d1 - d0)
                        tint = amt * min(1.0, 4 * u, 4 * (1 - u))
                haze = (0.24, 0.21, 0.30)
                near = tuple(lerp(c_, h_, tint) for c_, h_ in zip(act.b.near, haze))
                far = tuple(lerp(c_, h_, tint) for c_, h_ in zip(act.b.far, haze))
                draw_figure(ctx, act.J, chains=chains[act.track.name], eye_glow=g(a) if g else 1.0,
                            near=near, far=far)
            if not impact:
                self.draw_pebbles(ctx, cam)
            self.layer(ctx, cam, 1.0)
            fx.draw(ctx, px)
            ctx.identity_matrix()
            # --- post: flash, vignette, fades, cards
            if fx.flash > 0.02:
                ctx.set_source_rgba(*fx.flash_col, min(1.0, fx.flash))
                ctx.paint()
            W, H = self.W, self.H
            ctx.set_source_surface(self.vignette(), 0, 0)
            ctx.paint()
            for f0, f1, a0, a1 in seq.fades:
                if f0 <= a < f1:
                    t = (a - f0) / max(1, f1 - f0)
                    ctx.set_source_rgba(0, 0, 0, lerp(a0, a1, t))
                    ctx.paint()
            for f0, f1, fn in seq.cards:
                if f0 <= a < f1:
                    fn(ctx, self, a - f0, f1 - f0)
            if self.debug:
                ctx.select_font_face('DejaVu Sans Mono')
                ctx.set_font_size(16)
                ctx.set_source_rgba(1, 1, 0, 0.9)
                ctx.move_to(10, 22)
                ctx.show_text(f'{seq.name} rf {rf} anim {a}{" STOP" if stop else ""}  {seq.notes.get(a, "")}')
            surf.flush()
            yield rf, a, stop, surf
            if new_anim:
                for act in actors:
                    pass
            last_a = a
            fx.step()

    def to_rgb(self, surf):
        buf = np.ndarray((self.H, self.W, 4), np.uint8, surf.get_data()).copy()
        rgb = buf[:, :, [2, 1, 0]].astype(np.int16)
        if self.grain:
            n = self.rng.integers(-5, 6, (self.H, self.W, 1), dtype=np.int16)
            rgb += n
        return np.clip(rgb, 0, 255).astype(np.uint8)


def encode(frames_rgb_iter, W, H, path, fps=FPS, crf=18):
    os.makedirs(os.path.dirname(path) or '.', exist_ok=True)
    p = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24',
                          '-s', f'{W}x{H}', '-r', str(fps), '-i', '-', '-c:v', 'libx264', '-preset', 'medium',
                          '-crf', str(crf), '-pix_fmt', 'yuv420p', '-movflags', '+faststart', path],
                         stdin=subprocess.PIPE)
    n = 0
    for rgb in frames_rgb_iter:
        p.stdin.write(rgb.tobytes())
        n += 1
    p.stdin.close()
    p.wait()
    return n
