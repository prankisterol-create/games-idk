"""Render sequences to video, review contact sheets, PNG frames and SVG keys.

usage:
  python3 film.py --seq s1 --out ../output/preview/s1.mp4 --sheets ../output/sheets/s1
  python3 film.py --all --out ../output/preview/stickfight.mp4 --res 1920x1080
  python3 film.py --film doom --all --out /tmp/doom.mp4          (DOOM vs SPIDER-MAN)
"""
import argparse
import importlib
import os
import time

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from scene import Renderer, encode

FILMS = {
    'furnace': dict(seqs=['s1', 's2', 's3', 's4'],
                    modules={'s1': 'seq01', 's2': 'seq02', 's3': 'seq03', 's4': 'seq04'},
                    panels='storyboard_frames', title='FURNACE & TIDE'),
    'doom': dict(seqs=['d1', 'd2', 'd3', 'd4'],
                 modules={'d1': 'dv01', 'd2': 'dv02', 'd3': 'dv03', 'd4': 'dv04'},
                 panels='dv_storyboard', title='DOOM vs SPIDER-MAN'),
}
FILM = FILMS['furnace']
SEQUENCES = FILM['seqs']
MODULES = FILM['modules']


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
        sheet.save(os.path.join(self.outdir, f'{self.prefix}_{self.page:02d}.jpg'), quality=85)
        self.page += 1
        self.buf = []


def storyboard_pages(d, cols=4, tw=480):
    PANELS = importlib.import_module(FILM['panels']).PANELS
    th = tw * 9 // 16
    font = ImageFont.truetype('/usr/share/fonts/opentype/inter/Inter-Regular.otf', 17)
    bold = ImageFont.truetype('/usr/share/fonts/opentype/inter/Inter-Bold.otf', 30)
    per = cols * 4
    for page in range(0, len(PANELS), per):
        chunk = PANELS[page:page + per]
        rows = (len(chunk) + cols - 1) // cols
        im = Image.new('RGB', (cols * (tw + 20) + 20, rows * (th + 64) + 80), (24, 23, 30))
        dr = ImageDraw.Draw(im)
        dr.text((20, 22), f'{FILM["title"]}  storyboard  {page // per + 1}', fill=(236, 230, 216), font=bold)
        for i, (s, fa, cap) in enumerate(chunk):
            r, c = divmod(i, cols)
            x, y = 20 + c * (tw + 20), 80 + r * (th + 64)
            p = os.path.join(d, 'panels', f'{s}_{fa:03d}.jpg')
            if os.path.exists(p):
                im.paste(Image.open(p).resize((tw, th), Image.LANCZOS), (x, y))
            dr.text((x, y + th + 6), f'{s} / frame {fa}', fill=(150, 146, 160), font=font)
            dr.text((x, y + th + 28), cap, fill=(236, 230, 216), font=font)
        im.save(os.path.join(d, f'storyboard_{page // per + 1}.jpg'), quality=90)


def main():
    global FILM, SEQUENCES, MODULES
    ap = argparse.ArgumentParser()
    ap.add_argument('--film', default='furnace', choices=sorted(FILMS))
    ap.add_argument('--seq', nargs='*', default=[])
    ap.add_argument('--all', action='store_true')
    ap.add_argument('--res', default='1280x720')
    ap.add_argument('--out', required=True)
    ap.add_argument('--sheets', default=None)
    ap.add_argument('--png', default=None, help='dump every frame as PNG into this dir')
    ap.add_argument('--debug', action='store_true')
    ap.add_argument('--range', default=None, help='a0:a1 anim frames (first sequence only)')
    ap.add_argument('--log', default=None, help='write the per-render-frame timeline CSV here')
    ap.add_argument('--storyboard', default=None, help='write storyboard panels (PNG + SVG) here')
    args = ap.parse_args()
    FILM = FILMS[args.film]
    SEQUENCES, MODULES = FILM['seqs'], FILM['modules']
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
        prev = None
        for name in names:
            seq = load(name)
            if prev is not None:
                # exact handoff: first drawing = previous last drawing; hair keeps its motion
                for nm, act in seq.actors.items():
                    if nm in prev.actors:
                        act.track.continue_from(prev.actors[nm].track.eval(prev.n - 1))
                seq.carry = {nm: act.chains for nm, act in prev.actors.items()}
            seqs.append(seq)
            prev = seq
            lo, hi = 0, 10 ** 9
            if args.range:
                lo, hi = map(int, args.range.split(':'))
            svg_out = {}
            if args.storyboard:
                PANELS = importlib.import_module(FILM['panels']).PANELS
                os.makedirs(os.path.join(args.storyboard, 'svg'), exist_ok=True)
                os.makedirs(os.path.join(args.storyboard, 'panels'), exist_ok=True)
                for sname, fa, cap in PANELS:
                    if sname == seq.name:
                        svg_out.setdefault(fa, []).append(
                            os.path.join(args.storyboard, 'svg', f'{sname}_{fa:03d}.svg'))
            panel_png = {}
            for rf, a, stop, surf in R.frames(seq, svg_out=svg_out):
                if a in svg_out and a not in panel_png:
                    panel_png[a] = R.to_rgb(surf)
                    Image.fromarray(panel_png[a]).resize((960, 540), Image.LANCZOS).save(
                        os.path.join(args.storyboard, 'panels', f'{seq.name}_{a:03d}.jpg'), quality=88)
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
    if args.storyboard:
        storyboard_pages(args.storyboard)
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
