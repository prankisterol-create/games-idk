"""Model sheets for DOOM vs SPIDER-MAN: turnaround, construction, costume
breakdown and the action-pose library (PNG + editable SVG).

usage: python3 dv_modelsheet.py [outdir]
"""
import math
import os
import sys

import cairo

from rig import solve, draw_figure
from heroes import SPIDER, DOOM, doom_cape_anchor, SP_RED, SP_BLUE, SP_LENS, DM_STEEL, DM_GREEN, DM_CAPE, \
    DM_GOLD, DM_EYE
from heroposes import LIB2
from modelsheet import text, place, BG, INK, DIM

W = 3000


def static_cape(J, n=10, L=1.3):
    ax, ay = doom_cape_anchor(J)
    return [(ax - J.face * 0.22 * (i / (n - 1)) ** 1.5, max(0.02, ay - L * i / (n - 1))) for i in range(n)]


def figure(ctx, build, p, cx, ground_px, scale, label=None, skeleton=False):
    J = solve(build, p)
    place(ctx, cx, ground_px, scale)
    ctx.save()
    ctx.translate(J.hip[0], 0)
    ctx.scale(1, 0.12)
    g = cairo.RadialGradient(0, 0, 0, 0, 0, 0.6)
    g.add_color_stop_rgba(0, 0, 0, 0, 0.45)
    g.add_color_stop_rgba(1, 0, 0, 0, 0)
    ctx.set_source(g)
    ctx.arc(0, 0, 0.6, 0, 2 * math.pi)
    ctx.fill()
    ctx.restore()
    chains = [(static_cape(J), 0.26, 0.5, DM_CAPE)] if build is DOOM else []
    draw_figure(ctx, J, chains=chains, eye_glow=1.2 if build is DOOM else 1.0)
    if skeleton:
        ctx.set_line_width(2.0 / scale)
        ctx.set_source_rgba(1, 1, 1, 0.85)
        for a, b in [(J.hip, J.shoulder), (J.shoulder, J.chest), (J.chest, J.head),
                     (J.shoulder_n, J.elbow_n), (J.elbow_n, J.hand_n),
                     (J.hip_n, J.knee_n), (J.knee_n, J.ankle_n), (J.ankle_n, J.toe_n)]:
            ctx.move_to(*a)
            ctx.line_to(*b)
            ctx.stroke()
        for q in (J.hip, J.shoulder, J.chest, J.elbow_n, J.hand_n, J.knee_n, J.ankle_n):
            ctx.arc(q[0], q[1], 4.0 / scale, 0, 2 * math.pi)
            ctx.fill()
    ctx.restore()
    ctx.set_source_rgba(*DIM, 1)
    ctx.set_line_width(1.5)
    ctx.move_to(cx - 0.75 * scale, ground_px)
    ctx.line_to(cx + 0.75 * scale, ground_px)
    ctx.stroke()
    if label:
        text(ctx, label, cx, ground_px + 30, 18, INK, align='center')
    return J


def draw_sheet(ctx, build, title, notes, chips, Hh):
    ctx.set_source_rgb(*BG)
    ctx.paint()
    text(ctx, title, 60, 80, 44, build.near if build is SPIDER else DM_GREEN, bold=True)
    for i, line in enumerate(notes):
        text(ctx, line, 60, 120 + i * 28, 20, INK)
    scale = 300
    gy = 820
    hu = build.head_r * 2
    for k in range(0, 9):
        y = gy - k * hu * scale
        ctx.set_source_rgba(1, 1, 1, 0.07 if k else 0.18)
        ctx.set_line_width(1)
        ctx.move_to(40, y)
        ctx.line_to(1340, y)
        ctx.stroke()
        text(ctx, f'{k}', 44, y - 4, 14, DIM)
    lib = LIB2[build.name]
    base = lib['neutral'] if 'neutral' in lib else lib['stand']
    figure(ctx, build, dict(base, yaw=90), 230, gy, scale, 'FRONT')
    figure(ctx, build, dict(base, yaw=40), 520, gy, scale, '3/4')
    figure(ctx, build, base, 800, gy, scale, 'SIDE')
    figure(ctx, build, base, 1090, gy, scale, 'CONSTRUCTION', skeleton=True)
    J = solve(build, base)
    text(ctx, f'height {J.head[1] + build.head_r:.2f} m  =  {(J.head[1] + build.head_r) / hu:.1f} heads', 60, 920, 20,
         INK)
    text(ctx, f'thigh {build.thigh:.2f}  shin {build.shin:.2f}  torso {build.torso:.2f}  upper arm {build.uarm:.2f}'
              f'  forearm {build.farm:.2f}  head r {build.head_r:.3f}', 60, 952, 20, INK)
    for i, (nm, c) in enumerate(chips):
        ctx.set_source_rgb(*c)
        ctx.rectangle(60 + i * 250, 990, 34, 34)
        ctx.fill()
        text(ctx, nm, 104 + i * 250, 1015, 18, INK)
    names = [n for n in lib if n not in ('neutral', 'stand')]
    x0, y0, dx, dy = 1470, 430, 255, 330
    text(ctx, 'ACTION POSES (authored facing right, mirrored in use)', 1470, 80, 26, INK, bold=True)
    for i, n in enumerate(names):
        r, c = divmod(i, 6)
        p = dict(lib[n])
        if p['y'] is not None and p['y'] > 1.3 and n not in ('hover', 'brake', 'fly'):
            p['y'] = 1.15
        if n in ('hover', 'brake', 'fly'):
            p['y'] = 1.05
        figure(ctx, build, p, x0 + c * dx + 40, y0 + r * dy, 135, n)


def sheet(build, title, notes, chips, path):
    lib = LIB2[build.name]
    rows = (len(lib) - 1 + 5) // 6
    Hh = max(1300, 470 + rows * 330)
    surf = cairo.ImageSurface(cairo.FORMAT_RGB24, W, Hh)
    draw_sheet(cairo.Context(surf), build, title, notes, chips, Hh)
    surf.write_to_png(path)
    vs = cairo.SVGSurface(path.replace('.png', '.svg'), W, Hh)
    draw_sheet(cairo.Context(vs), build, title, notes, chips, Hh)
    vs.finish()


if __name__ == '__main__':
    out = sys.argv[1] if len(sys.argv) > 1 else '../output/doom_vs_spiderman/modelsheets'
    os.makedirs(out, exist_ok=True)
    sheet(SPIDER, 'SPIDER-MAN — MODEL SHEET',
          ['Small, fast, never square to the threat. Low wide stances, knees always bent, hands open.',
           'Silhouette ID: big angled white lenses, red/blue split, webbing on every red panel.',
           'Moves in arcs and lines of web; every landing is a crouch; fires webs with the web-shooter sign.'],
          [('red', SP_RED), ('blue', SP_BLUE), ('lens', SP_LENS)], os.path.join(out, 'SPIDER_model_sheet.png'))
    sheet(DOOM, 'DOCTOR DOOM — MODEL SHEET',
          ['Tall, upright, chest out, chin level. Economy of motion: he barely moves his feet.',
           'Silhouette ID: hood + floor-length cape (simulated), steel mask with glowing eye slits.',
           'Palms open when casting (green force bolts, a hex force field), fists otherwise; rocket boots.'],
          [('steel', DM_STEEL), ('tunic', DM_GREEN), ('cape', DM_CAPE), ('gold', DM_GOLD), ('eyes', DM_EYE)],
          os.path.join(out, 'DOOM_model_sheet.png'))
    print('written')
