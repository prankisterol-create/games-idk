"""Timing & spacing charts generated from the real animation tracks.

For each signature action: ghosts of the key drawings, the striking limb's
position on every animation frame (numbered dots: wide gaps = fast, bunched =
slow), and a frame bar marking keys (K), in-betweens (|), smear frames (S)
and hit-stop frames (H).

usage: python3 timing.py OUTDIR
"""
import importlib
import math
import os
import sys

import cairo

from rig import solve, draw_figure

ACTIONS = [
    ('seq01', 'S1  KAI sprint -> straight right (near miss)', 'KAI', 140, 168, 'hand_f', 'SEN'),
    ('seq01', 'S1  SEN spinning back kick', 'SEN', 170, 182, 'toe_f', 'KAI'),
    ('seq02', 'S2  feint -> low kick -> check', 'KAI', 44, 56, 'toe_f', 'SEN'),
    ('seq03', 'S3  leaping axe kick (hang time at the apex)', 'KAI', 11, 30, 'toe_n', 'SEN'),
    ('seq04', 'S4  final charge -> rising palm', 'SEN', 108, 121, 'hand_n', 'KAI'),
    ('seq04', 'S4  KAI launched', 'KAI', 117, 147, 'head', None),
]


def chart(seq, title, who, f0, f1, joint, other, path, W=1600, H=900):
    tr = seq.actors[who].track
    keys = sorted(k['f'] for k in tr.keys if f0 <= k['f'] <= f1)
    poses = {f: tr.eval(f) for f in range(f0, f1 + 1)}
    Js = {f: solve(tr.b, p) for f, p in poses.items()}
    pts = {f: (getattr(J, joint) if joint != 'head' else J.head) for f, J in Js.items()}
    xs = [q[0] for J in Js.values() for q in (J.hip, J.head, J.ankle_n, J.ankle_f, J.hand_n, J.hand_f)]
    ys = [q[1] for J in Js.values() for q in (J.hip, J.head, J.ankle_n, J.ankle_f, J.hand_n, J.hand_f)]
    x0, x1 = min(xs) - 0.6, max(xs) + 0.6
    y1 = max(max(ys) + 0.4, 2.2)
    sc = min((W - 120) / (x1 - x0), (H - 300) / y1)
    surf = cairo.ImageSurface(cairo.FORMAT_RGB24, W, H)
    ctx = cairo.Context(surf)
    ctx.set_source_rgb(0.10, 0.095, 0.12)
    ctx.paint()
    ctx.select_font_face('Inter', cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    ctx.set_font_size(30)
    ctx.set_source_rgb(0.92, 0.9, 0.86)
    ctx.move_to(40, 50)
    ctx.show_text(title)
    ctx.select_font_face('Inter', cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
    ctx.set_font_size(17)
    ctx.set_source_rgb(0.6, 0.58, 0.64)
    ctx.move_to(40, 80)
    ctx.show_text(f'{who}: path of {joint} on every animation frame {f0}-{f1} (24 fps). '
                  'Wide gaps = fast, bunched = slow. Ghosts = key drawings.')
    gy = H - 220
    ctx.save()
    ctx.translate(60 - x0 * sc, gy)
    ctx.scale(sc, -sc)
    ctx.set_source_rgba(1, 1, 1, 0.15)
    ctx.set_line_width(2 / sc)
    ctx.move_to(x0, 0)
    ctx.line_to(x1, 0)
    ctx.stroke()
    if other:
        ot = seq.actors[other].track
        mid = (f0 + f1) // 2
        Jo = solve(ot.b, ot.eval(mid))
        ctx.push_group()
        draw_figure(ctx, Jo, style='flat', near=(0.35, 0.33, 0.4))
        ctx.pop_group_to_source()
        ctx.paint_with_alpha(0.5)
    for i, f in enumerate(keys):
        ctx.push_group()
        draw_figure(ctx, Js[f])
        ctx.pop_group_to_source()
        ctx.paint_with_alpha(0.16 + 0.5 * (i + 1) / len(keys))
    # spacing path
    fs = sorted(pts)
    ctx.set_source_rgba(1, 0.85, 0.3, 0.55)
    ctx.set_line_width(2 / sc)
    ctx.move_to(*pts[fs[0]])
    for f in fs[1:]:
        ctx.line_to(*pts[f])
    ctx.stroke()
    for f in fs:
        x, y = pts[f]
        k = f in keys
        ctx.set_source_rgb(*((1, 0.35, 0.25) if k else (1, 0.9, 0.4)))
        ctx.arc(x, y, (9 if k else 5) / sc, 0, 2 * math.pi)
        ctx.fill()
    ctx.restore()
    for f in fs:
        x, y = pts[f]
        sx, sy = 60 + (x - x0) * sc, gy - y * sc
        ctx.set_source_rgb(0.95, 0.95, 0.95)
        ctx.set_font_size(14)
        ctx.move_to(sx + 8, sy - 8)
        ctx.show_text(str(f))
    # frame bar
    bx, by, cw = 60, H - 120, (W - 120) / (f1 - f0 + 1)
    smears = set()
    for a0, a1, limbs, s in tr.smears:
        smears |= set(range(a0, a1))
    for i, f in enumerate(range(f0, f1 + 1)):
        x = bx + i * cw
        stops = seq.hitstops.get(f, 0)
        ctx.set_source_rgb(*((0.85, 0.3, 0.25) if f in keys else (0.3, 0.29, 0.34)))
        ctx.rectangle(x + 1, by, cw - 2, 34)
        ctx.fill()
        ctx.set_source_rgb(1, 1, 1)
        ctx.set_font_size(13)
        ctx.move_to(x + 4, by + 22)
        ctx.show_text(('K' if f in keys else '|') + (' S' if f in smears else ''))
        ctx.set_source_rgb(0.6, 0.58, 0.64)
        ctx.move_to(x + 4, by + 52)
        ctx.show_text(str(f))
        if stops:
            ctx.set_source_rgb(1, 0.85, 0.3)
            ctx.move_to(x + 4, by - 8)
            ctx.show_text(f'H+{stops}')
    ctx.set_source_rgb(0.6, 0.58, 0.64)
    ctx.move_to(bx, H - 24)
    ctx.show_text('K key drawing   | in-between   S smear frame   H+n hit-stop frames inserted after this drawing')
    surf.write_to_png(path)
    # numeric spacing (for the timing plan doc)
    d = [math.dist(pts[fs[i]], pts[fs[i + 1]]) for i in range(len(fs) - 1)]
    return keys, d


def main(out):
    os.makedirs(out, exist_ok=True)
    cache = {}
    rows = []
    for i, (mod, title, who, f0, f1, joint, other) in enumerate(ACTIONS):
        if mod not in cache:
            cache[mod] = importlib.import_module(mod).build()
        keys, d = chart(cache[mod], title, who, f0, f1, joint, other, os.path.join(out, f'timing_{i + 1:02d}.png'))
        rows.append((title, f0, f1, keys, d))
    with open(os.path.join(out, 'spacing.txt'), 'w') as fh:
        for title, f0, f1, keys, d in rows:
            fh.write(f'{title}\n  keys: {keys}\n  per-frame travel (m): ' +
                     ' '.join(f'{x:.2f}' for x in d) + '\n\n')
    print('charts ->', out)


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else '../output/timing')
