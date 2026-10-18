"""Render the Fountain screenplay to a US-Letter PDF in standard screenplay layout.

    python3 tools/fountain_pdf.py   # writes docs/B_screenplay.pdf
"""
import os
import sys
import textwrap

import cairo

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C  # noqa: E402

PT = 1.0
PW, PH = 612, 792                     # US Letter in points
TOP, BOTTOM = 72, 72
LINE = 12                             # Courier 12 pt, 6 lines per inch
COL = {'heading': (108, 61), 'action': (108, 61), 'character': (266, 38), 'dialogue': (180, 35),
       'parenthetical': (223, 26), 'transition': (432, 20), 'centered': (108, 61), 'section': (108, 61)}


class Writer:
    def __init__(self, path):
        self.surf = cairo.PDFSurface(path, PW, PH)
        self.ctx = cairo.Context(self.surf)
        self.ctx.select_font_face('Courier 10 Pitch', cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
        self.ctx.set_font_size(12)
        self.page = 0
        self.y = None

    def new_page(self, number=True):
        if self.page:
            self.ctx.show_page()
        self.page += 1
        self.y = TOP
        if number and self.page > 1:
            self.text(PW - 72 - 30, 36 + 12, '%d.' % (self.page - 1))

    def text(self, x, y, s, bold=False):
        self.ctx.select_font_face('Courier 10 Pitch', cairo.FONT_SLANT_NORMAL,
                                  cairo.FONT_WEIGHT_BOLD if bold else cairo.FONT_WEIGHT_NORMAL)
        self.ctx.move_to(x, y)
        self.ctx.show_text(s)

    def block(self, kind, text, gap=1, scene=None, keep=1):
        x, width = COL[kind]
        lines = []
        for para in text.split('\n'):
            lines += textwrap.wrap(para, width) or ['']
        need = (len(lines) + gap) * LINE
        if self.y + min(need, (keep + gap) * LINE) > PH - BOTTOM:
            self.new_page()
        elif self.y > TOP:
            self.y += gap * LINE
        for ln in lines:
            if self.y > PH - BOTTOM:
                self.new_page()
            if kind == 'centered':
                self.ctx.set_font_size(12)
                w = self.ctx.text_extents(ln).x_advance
                self.text((PW - w) / 2, self.y, ln, bold=True)
            elif kind == 'transition':
                w = self.ctx.text_extents(ln).x_advance
                self.text(PW - 72 - w, self.y, ln)
            else:
                self.text(x, self.y, ln, bold=kind in ('heading', 'section'))
            if scene and ln is lines[0]:
                self.text(60, self.y, scene)
                self.text(PW - 60 - self.ctx.text_extents(scene).x_advance, self.y, scene)
            self.y += LINE

    def close(self):
        self.surf.finish()


def main():
    title, elements = C.parse_fountain(os.path.join(C.DOCS, 'B_screenplay.fountain'))
    out = os.path.join(C.DOCS, 'B_screenplay.pdf')
    w = Writer(out)
    w.new_page(number=False)
    w.y = 280
    for line in title.get('Title', []):
        w.block('centered', line, gap=0)
    w.y += 24
    for key in ('Credit', 'Author'):
        for line in title.get(key, []):
            w.block('centered', line, gap=0)
    w.y += 24
    for line in title.get('Source', []):
        w.block('centered', line, gap=0)
    w.y = PH - 120
    for key in ('Draft date', 'Contact'):
        for line in title.get(key, []):
            w.block('action', line, gap=0)
    w.new_page()
    prev = None
    for kind, text, extra in elements:
        if kind == 'section':
            w.block('centered', text.upper(), gap=2)
        elif kind == 'heading':
            w.block('heading', text.upper(), gap=2, scene=extra, keep=3)
        elif kind == 'character':
            w.block('character', text + (' ' + extra if extra else ''), gap=1, keep=3)
        elif kind == 'dialogue':
            w.block('dialogue', text, gap=0)
        elif kind == 'parenthetical':
            w.block('parenthetical', text, gap=0)
        elif kind == 'transition':
            w.block('transition', text, gap=1)
        elif kind == 'centered':
            w.block('centered', text, gap=2)
        else:
            w.block('action', text, gap=1)
        prev = kind
    w.close()
    print('%s: %d pages' % (out, w.page - 1))


if __name__ == '__main__':
    main()
