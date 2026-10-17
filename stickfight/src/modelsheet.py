"""Character model sheets: construction, turnaround and action-pose library.

usage: python3 modelsheet.py [outdir]
"""
import math
import os
import sys

import cairo

from rig import KAI, SEN, solve, draw_figure, pose, hair_anchor
from poses import LIB, at

W, H = 3000, 1560
BG = (0.105, 0.098, 0.125)
INK = (0.86, 0.84, 0.80)
DIM = (0.45, 0.43, 0.48)


def text(ctx, s, x, y, size=22, col=INK, bold=False, align='left'):
    ctx.select_font_face('Inter', cairo.FONT_SLANT_NORMAL,
                         cairo.FONT_WEIGHT_BOLD if bold else cairo.FONT_WEIGHT_NORMAL)
    ctx.set_font_size(size)
    ext = ctx.text_extents(s)
    if align == 'center':
        x -= ext.width / 2 + ext.x_bearing
    ctx.set_source_rgb(*col)
    ctx.move_to(x, y)
    ctx.show_text(s)


def place(ctx, cx, ground_px, scale):
    """Set a world transform: world x=0 at cx, ground y=0 at ground_px, y up."""
    ctx.save()
    ctx.translate(cx, ground_px)
    ctx.scale(scale, -scale)


def static_chain(J, n, length, droop):
    """Hang a chain from the hair anchor (used only for still drawings)."""
    ax, ay = hair_anchor(J)
    pts = [(ax, ay)]
    for i in range(1, n):
        t = i / (n - 1)
        pts.append((ax - J.face * length * t * (1 - droop), ay - length * t * droop - 0.04 * t * t))
    return pts


def chains_for(J):
    b = J.build
    if b.trait == 'headband':
        c1 = static_chain(J, 7, 0.30, 0.55)
        c2 = [(x - J.face * 0.02, y - 0.05 * i / 6) for i, (x, y) in enumerate(static_chain(J, 7, 0.24, 0.75))]
        return [(c1, 0.045, 0.025, b.accent), (c2, 0.04, 0.02, b.accent)]
    return [(static_chain(J, 9, 0.42, 0.85), 0.07, 0.015, b.far)]


def figure(ctx, build, p, cx, ground_px, scale, label=None, skeleton=False):
    J = solve(build, p)
    place(ctx, cx, ground_px, scale)
    # ground shadow
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
    draw_figure(ctx, J, chains=chains_for(J))
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


def sheet(build, notes, path):
    surf = cairo.ImageSurface(cairo.FORMAT_RGB24, W, H)
    ctx = cairo.Context(surf)
    ctx.set_source_rgb(*BG)
    ctx.paint()
    text(ctx, f'{build.name} — MODEL SHEET', 60, 80, 44, build.near, bold=True)
    for i, line in enumerate(notes):
        text(ctx, line, 60, 120 + i * 28, 20, INK)

    # construction / turnaround on a head-unit grid
    scale = 300
    gy = 760
    hu = build.head_r * 2
    for k in range(0, 8):
        y = gy - k * hu * scale
        ctx.set_source_rgba(1, 1, 1, 0.07 if k else 0.18)
        ctx.set_line_width(1)
        ctx.move_to(40, y)
        ctx.line_to(1300, y)
        ctx.stroke()
        text(ctx, f'{k}', 44, y - 4, 14, DIM)
    neutral = LIB[build.name]['neutral']
    figure(ctx, build, dict(neutral, yaw=90), 230, gy, scale, 'FRONT')
    figure(ctx, build, dict(neutral, yaw=42), 520, gy, scale, '3/4')
    figure(ctx, build, neutral, 790, gy, scale, 'SIDE')
    figure(ctx, build, neutral, 1060, gy, scale, 'CONSTRUCTION', skeleton=True)

    J = solve(build, neutral)
    text(ctx, f'height {J.head[1] + build.head_r:.2f} m  =  {(J.head[1] + build.head_r) / hu:.1f} heads', 60, 860, 20, INK)
    text(ctx, f'thigh {build.thigh:.2f}  shin {build.shin:.2f}  torso {build.torso:.2f}', 60, 892, 20, INK)
    text(ctx, f'upper arm {build.uarm:.2f}  forearm {build.farm:.2f}  head r {build.head_r:.3f}', 60, 924, 20, INK)
    text(ctx, f'line weight: chest {build.w_chest:.3f} > hip {build.w_hip:.3f}; limb taper '
              f'{build.w_uarm:.3f}->{build.w_wrist:.3f} / {build.w_thigh:.3f}->{build.w_ankle:.3f}', 60, 956, 20, INK)
    # colour chips
    for i, (nm, c) in enumerate([('near limbs / body', build.near), ('far limbs', build.far),
                                 ('accent', build.accent), ('eye', build.eye), ('eye glow', build.glow)]):
        ctx.set_source_rgb(*c)
        ctx.rectangle(60 + i * 250, 1000, 34, 34)
        ctx.fill()
        text(ctx, nm, 104 + i * 250, 1025, 18, INK)

    # action poses
    lib = LIB[build.name]
    names = [n for n in lib if n != 'neutral']
    cols = 7
    scale2 = 140
    x0, y0, dx, dy = 1440, 420, 255, 330
    text(ctx, 'ACTION POSES (authored facing right, mirrored in use)', 1440, 80, 26, INK, bold=True)
    for i, n in enumerate(names):
        r, c = divmod(i, 6)
        cx = x0 + c * dx + 40
        gpx = y0 + r * dy
        p = lib[n]
        y = p['y'] if p['y'] is not None else 0
        figure(ctx, build, p, cx, gpx, scale2, n)
    surf.write_to_png(path)


if __name__ == '__main__':
    out = sys.argv[1] if len(sys.argv) > 1 else '../output/modelsheets'
    os.makedirs(out, exist_ok=True)
    sheet(KAI, ['"The Furnace" — power striker. Square, heavy, chin tucked, elbows in.',
                'Silhouette ID: broad chest taper, black headband with two tails, ember-orange body.',
                'Moves in straight lines; commits the whole body (torso 30-45° into every strike).'],
          os.path.join(out, 'KAI_model_sheet.png'))
    sheet(SEN, ['"The Tide" — evasive counter-fighter. Tall, long-limbed, loose open hands.',
                'Silhouette ID: long ponytail, slim taper, small head, teal body, ice-blue eyes.',
                'Moves in arcs and level changes; turns every defence into the next attack.'],
          os.path.join(out, 'SEN_model_sheet.png'))
    print('written')
