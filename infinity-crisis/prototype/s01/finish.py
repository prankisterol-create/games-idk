"""Mux picture + sound into the 16:9 and 2.39:1 deliverables and pull storyboard frames.

    python3 finish.py picture_16x9.mp4 sound.wav
"""
import os
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'tools'))
import common as C  # noqa: E402

OUT = os.path.join(C.OUTPUT, 's01_prototype')


def run(args):
    subprocess.run(args, check=True)


def main(picture, sound):
    os.makedirs(os.path.join(OUT, 'storyboard'), exist_ok=True)
    enc = ['-c:v', 'libx264', '-preset', 'slow', '-crf', '20', '-pix_fmt', 'yuv420p',
           '-c:a', 'aac', '-b:a', '256k', '-movflags', '+faststart', '-shortest']
    run(['ffmpeg', '-y', '-loglevel', 'error', '-i', picture, '-i', sound] + enc +
        [os.path.join(OUT, 'infinity_crisis_s01_16x9_1920x1080.mp4')])
    run(['ffmpeg', '-y', '-loglevel', 'error', '-i', picture, '-i', sound, '-vf', 'crop=1920:804:0:138'] + enc +
        [os.path.join(OUT, 'infinity_crisis_s01_scope_1920x804.mp4')])
    seq = C.load_yaml(os.path.join(C.DATA, 'shots', 's01.yaml'))
    t0, tiles = 0.0, []
    font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 18)
    for shot in seq['shots']:
        for tag, frac in (('a', 0.3), ('b', 0.8)):
            t = t0 + shot['dur'] * frac
            path = os.path.join(OUT, 'storyboard', '%s_%s.jpg' % (shot['id'], tag))
            run(['ffmpeg', '-y', '-loglevel', 'error', '-ss', '%.3f' % t, '-i', picture, '-frames:v', '1',
                 '-vf', 'crop=1920:804:0:138,scale=960:402', '-q:v', '3', path])
            tiles.append((shot, path))
        t0 += shot['dur']
    w, h, cols = 480, 201, 6
    rows = (len(tiles) + cols - 1) // cols
    sheet = Image.new('RGB', (cols * w, rows * (h + 28)), (12, 12, 14))
    draw = ImageDraw.Draw(sheet)
    for i, (shot, path) in enumerate(tiles):
        x, y = (i % cols) * w, (i // cols) * (h + 28)
        sheet.paste(Image.open(path).resize((w, h)), (x, y))
        draw.text((x + 6, y + h + 4), '%s  %s' % (shot['id'], shot['title']), fill=(220, 220, 220), font=font)
    sheet.save(os.path.join(OUT, 'contact_sheet.jpg'), quality=88)
    print('done:', OUT)


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
