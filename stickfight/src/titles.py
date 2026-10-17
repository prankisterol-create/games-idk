"""Title / name cards drawn over the picture (screen space)."""
import math

import cairo


def _text(ctx, s, x, y, size, rgba, weight=cairo.FONT_WEIGHT_BOLD, spacing=0.0, align='left'):
    ctx.select_font_face('Inter Display', cairo.FONT_SLANT_NORMAL, weight)
    ctx.set_font_size(size)
    widths = [ctx.text_extents(ch).x_advance for ch in s]
    total = sum(widths) + spacing * (len(s) - 1)
    if align == 'right':
        x -= total
    elif align == 'center':
        x -= total / 2
    ctx.set_source_rgba(*rgba)
    for ch, w in zip(s, widths):
        ctx.move_to(x, y)
        ctx.show_text(ch)
        x += w + spacing
    return total


def name_card(name, epithet, color, side='left'):
    """Slides in with a fast wipe, holds, then fades."""
    def draw(ctx, R, t, n):
        W, H = R.W, R.H
        k = H / 720.0
        ain = min(1.0, t / 4.0)
        aout = min(1.0, max(0.0, (n - t) / 6.0))
        a = ain * aout
        e = 1 - (1 - ain) ** 3
        x0 = 70 * k if side == 'left' else W - 70 * k
        sgn = 1 if side == 'left' else -1
        y = H * 0.70
        # slash bar
        bar_w = 380 * k * e
        ctx.save()
        ctx.set_source_rgba(*color, 0.85 * a)
        ctx.move_to(x0 - sgn * 20 * k, y + 18 * k)
        ctx.line_to(x0 + sgn * bar_w, y + 18 * k)
        ctx.line_to(x0 + sgn * (bar_w - 14 * k), y + 26 * k)
        ctx.line_to(x0 - sgn * 20 * k, y + 26 * k)
        ctx.close_path()
        ctx.fill()
        align = 'left' if side == 'left' else 'right'
        _text(ctx, name, x0 + sgn * (1 - e) * -40 * k, y, 92 * k, (1, 1, 1, a), spacing=10 * k, align=align)
        _text(ctx, epithet, x0, y + 58 * k, 22 * k, (*color, a), weight=cairo.FONT_WEIGHT_NORMAL,
              spacing=6 * k, align=align)
        ctx.restore()
    return draw


def title_card(title, sub):
    def draw(ctx, R, t, n):
        W, H = R.W, R.H
        k = H / 720.0
        a = min(1.0, t / 8.0) * min(1.0, max(0.0, (n - t) / 10.0))
        _text(ctx, title, W / 2, H * 0.48, 72 * k, (0.95, 0.93, 0.9, a), spacing=18 * k, align='center')
        _text(ctx, sub, W / 2, H * 0.48 + 44 * k, 20 * k, (0.75, 0.72, 0.78, a), weight=cairo.FONT_WEIGHT_NORMAL,
              spacing=8 * k, align='center')
    return draw
