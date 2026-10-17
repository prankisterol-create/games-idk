"""Render sequences to video, review contact sheets, PNG frames and SVG keys.

usage:
  python3 film.py --seq s1 --out ../output/preview/s1.mp4 --sheets ../output/sheets/s1
  python3 film.py --all --out ../output/preview/stickfight.mp4 --res 1920x1080
"""
import argparse
import importlib
import os
import time

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from scene import Renderer, encode

SEQUENCES = ['s1', 's2', 's3', 's4']
MODULES = {'s1': 'seq01', 's2': 'seq02', 's3': 'seq03', 's4': 'seq04'}


def load(name):
    return importlib.import_module(MODULES[name]).build()


class SheetWriter:
    """Every rendered frame as a numbered thumbnail, 8 x 6 per page."""

    def __init__(self, outdir, prefix, cols=8, rows=6, tw=320):
        self.outdir, self.prefix = outdir, prefix
        self.cols, self.rows, self.tw = cols, rows, tw
        self.th = tw * 9 // 16
        self.buf = []
        self.page = 0
        self.font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 13)
        os.makedirs(outdir, exist_ok=True)

    def add(self, rgb, label):
        im = Image.fromarray(rgb).resize((self.tw, self.th), Image.BILINEAR)
        d = ImageDraw.Draw(im)
        d.rectangle((0, 0, 150, 16), fill=(0, 0, 0))
        d.text((3, 1), label, fill=(255, 230, 0), font=self.font)
        self.buf.append(im)
        if len(self.buf) == self.cols * self.rows:
            self.flush()

    def flush(self):
        if not self.buf:
            return
        sheet = Image.new('RGB', (self.cols * self.tw, self.rows * self.th), (0, 0, 0))
        for i, im in enumerate(self.buf):
            r, c = divmod(i, self.cols)
            sheet.paste(im, (c * self.tw, r * self.th))
        sheet.save(os.path.join(self.outdir, f'{self.prefix}_{self.page:02d}.png'))
        self.page += 1
        self.buf = []


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seq', nargs='*', default=[])
    ap.add_argument('--all', action='store_true')
    ap.add_argument('--res', default='1280x720')
    ap.add_argument('--out', required=True)
    ap.add_argument('--sheets', default=None)
    ap.add_argument('--png', default=None, help='dump every frame as PNG into this dir')
    ap.add_argument('--debug', action='store_true')
    ap.add_argument('--range', default=None, help='a0:a1 anim frames (first sequence only)')
    ap.add_argument('--log', default=None, help='write the per-render-frame timeline CSV here')
    args = ap.parse_args()
    W, H = map(int, args.res.split('x'))
    names = SEQUENCES if args.all else args.seq
    R = Renderer(W, H, debug=args.debug)
    t0 = time.time()
    seqs = []
    log = []
    sheet = SheetWriter(args.sheets, 'sheet') if args.sheets else None
    if args.png:
        os.makedirs(args.png, exist_ok=True)

    def gen():
        n = 0
        for name in names:
            seq = load(name)
            seqs.append(seq)
            lo, hi = 0, 10 ** 9
            if args.range:
                lo, hi = map(int, args.range.split(':'))
            for rf, a, stop, surf in R.frames(seq):
                if not (lo <= a < hi):
                    continue
                rgb = R.to_rgb(surf)
                if sheet:
                    sheet.add(rgb, f'{seq.name} {a}{"*" if stop else ""} #{n}')
                if args.png:
                    Image.fromarray(rgb).save(os.path.join(args.png, f'{seq.name}_{n:05d}.png'))
                cam = seq.cam.eval(a)
                row = [n, f'{n / 24:.3f}', seq.name, a, int(stop)]
                for act in seq.actors.values():
                    p = act.pose
                    row += [act.track.name, f"{p['x']:.2f}", f"{p['y']:.2f}", p['face']]
                row += [f"{cam['h']:.2f}", seq.notes.get(a, '')]
                log.append(row)
                n += 1
                yield rgb
    n = encode(gen(), W, H, args.out)
    if sheet:
        sheet.flush()
    if args.log:
        import csv
        with open(args.log, 'w', newline='') as fh:
            w = csv.writer(fh)
            w.writerow(['render_frame', 'time_s', 'seq', 'anim_frame', 'hitstop', 'A', 'A_x', 'A_y', 'A_face',
                        'B', 'B_x', 'B_y', 'B_face', 'view_h_m', 'note'])
            w.writerows(log)
    print(f'{n} frames ({n / 24:.2f}s) in {time.time() - t0:.1f}s -> {args.out}')


if __name__ == '__main__':
    main()
