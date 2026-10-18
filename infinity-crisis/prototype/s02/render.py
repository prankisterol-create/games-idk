"""Sequence 2 'The Avengers Respond': 2D previs prototype.

Shot order and durations come from data/shots/s02.yaml. Each shot is a function S02_xxx(t, d)
returning an HxWx3 float RGB frame, defined in one of shots_g1.py .. shots_g4.py. Shared helpers:
  r1        prototype/s01/render.py (noise, rain, skyline, rupture, glow, compositing, post)
  heroes2d  prototype/lib/heroes2d.py (the character kit)
Captions for dialogue are generated from the shot list.

    python3 render.py --out s02_16x9.mp4 [--scale 0.5] [--shots S02_020,S02_030] [--png DIR] [--every N]
"""
import argparse
import importlib.util
import os
import subprocess
import sys
from multiprocessing import Pool

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
PROTO = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(PROTO, 'lib'))
sys.path.insert(0, os.path.join(PROTO, '..', 'tools'))
_spec = importlib.util.spec_from_file_location('r1', os.path.join(PROTO, 's01', 'render.py'))
R = importlib.util.module_from_spec(_spec)
sys.modules['r1'] = R
_spec.loader.exec_module(R)
sys.path.insert(0, HERE)
import common as C  # noqa: E402

SEQ = C.load_yaml(os.path.join(C.DATA, 'shots', 's02.yaml'))
SHOTS = {}
for g in ('shots_g1', 'shots_g2', 'shots_g3', 'shots_g4'):
    if os.path.exists(os.path.join(HERE, g + '.py')):
        mod = importlib.import_module(g)
        SHOTS.update({k: v for k, v in vars(mod).items() if k.startswith('S02_') and callable(v)})


def captions():
    out = {}
    for shot in SEQ['shots']:
        lines = shot.get('dialogue') or []
        if not lines:
            continue
        d = shot['dur']
        a0, a1 = 0.12 * d, 0.96 * d
        step = (a1 - a0) / len(lines)
        out[shot['id']] = [(a0 + i * step, a0 + (i + 1) * step - 0.05, l['line']) for i, l in enumerate(lines)]
    return out


CAPS = captions()


def placeholder(sid, t, d):
    img = np.zeros((R.H, R.W, 3), np.float32) + 0.03
    s, ctx = R.surface()
    ctx.set_source_rgba(1, 1, 1, 0.6)
    ctx.set_font_size(40 * R.S)
    ctx.move_to(R.W * 0.3, R.H * 0.5)
    ctx.show_text('%s - not animated yet' % sid)
    return R.over(img, R.to_np(s))


def render_frame(job):
    sid, t, d, k, idx = job
    fn = SHOTS.get(sid)
    img = fn(t, d) if fn else placeholder(sid, t, d)
    return R.post(img, sid, t, idx + 100000, captions=CAPS,
                  label='INFINITY CRISIS  S02 PREVIS PROTOTYPE  %s' % sid)


def plan():
    jobs, i = [], 0
    for shot in SEQ['shots']:
        for k in range(C.frames(shot['dur'])):
            jobs.append((shot['id'], k / R.FPS, shot['dur'], k, i))
            i += 1
    return jobs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out')
    ap.add_argument('--png')
    ap.add_argument('--scale', type=float, default=1.0)
    ap.add_argument('--shots')
    ap.add_argument('--every', type=int, default=1)
    ap.add_argument('--jobs', type=int, default=os.cpu_count())
    a = ap.parse_args()
    R.init(a.scale)
    jobs = plan()
    if a.shots:
        keep = set(a.shots.split(','))
        jobs = [j for j in jobs if j[0] in keep]
    jobs = jobs[::a.every]
    proc = None
    if a.out:
        proc = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24',
                                 '-s', '%dx%d' % (R.W, R.H), '-r', str(R.FPS), '-i', '-', '-c:v', 'libx264',
                                 '-preset', 'medium', '-crf', '16', '-pix_fmt', 'yuv420p', a.out],
                                stdin=subprocess.PIPE)
    if a.png:
        os.makedirs(a.png, exist_ok=True)
    with Pool(a.jobs, initializer=R.init, initargs=(a.scale,)) as pool:
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
