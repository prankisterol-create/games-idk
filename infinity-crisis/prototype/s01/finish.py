"""Mux picture + sound into the 16:9 and 2.39:1 deliverables and pull storyboard frames.

    python3 finish.py picture_16x9.mp4 sound.wav [sequence_number]
"""
import os
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'tools'))
import common as C  # noqa: E402



def run(args):
    subprocess.run(args, check=True)


def main(picture, sound, n=1):
    OUT = os.path.join(C.OUTPUT, 's%02d_prototype' % n)
    tag = 's%02d' % n
    os.makedirs(os.path.join(OUT, 'storyboard'), exist_ok=True)
    # cinematic finishing: denoise, bloom, anamorphic streaks, slight chromatic fringe, grade
    grade = ("hqdn3d=1.5:1.5:3:3,format=gbrp,split=3[b][g][s];"
             "[g]lutrgb=r='clip((val-135)*2,0,255)':g='clip((val-135)*2,0,255)':b='clip((val-135)*2,0,255)',"
             "gblur=sigma=22[gl];"
             "[s]lutrgb=r='clip((val-185)*3,0,255)':g='clip((val-185)*3,0,255)':b='clip((val-185)*3,0,255)',"
             "gblur=sigma=80:sigmaV=1,colorchannelmixer=rr=0.55:gg=0.75:bb=1.25[st];"
             "[b][gl]blend=all_mode=screen:all_opacity=0.5[c1];"
             "[c1][st]blend=all_mode=screen:all_opacity=0.55,rgbashift=rh=-2:bh=2,"
             "colorbalance=rs=-0.04:bs=0.05:rh=0.05:gh=0.01:bh=-0.03,format=yuv420p,eq=contrast=1.06:saturation=1.08")
    enc = ['-c:v', 'libx264', '-preset', 'medium', '-crf', '22', '-maxrate', '4M', '-bufsize', '8M',
           '-c:a', 'aac', '-b:a', '256k', '-movflags', '+faststart', '-shortest']
    run(['ffmpeg', '-y', '-loglevel', 'error', '-i', picture, '-i', sound, '-vf', grade] + enc +
        [os.path.join(OUT, 'infinity_crisis_%s_16x9_1920x1080.mp4' % tag)])
    run(['ffmpeg', '-y', '-loglevel', 'error', '-i', picture, '-i', sound, '-vf', 'crop=1920:804:0:138,' + grade] + enc +
        [os.path.join(OUT, 'infinity_crisis_%s_scope_1920x804.mp4' % tag)])
    seq = C.load_yaml(os.path.join(C.DATA, 'shots', '%s.yaml' % tag))
    t0, tiles = 0.0, []
    font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 18)
    for shot in seq['shots']:
        for ab, frac in (('a', 0.3), ('b', 0.8)):
            t = t0 + shot['dur'] * frac
            path = os.path.join(OUT, 'storyboard', '%s_%s.jpg' % (shot['id'], ab))
            run(['ffmpeg', '-y', '-loglevel', 'error', '-ss', '%.3f' % t, '-i',
                 os.path.join(OUT, 'infinity_crisis_%s_16x9_1920x1080.mp4' % tag), '-frames:v', '1',
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
    main(sys.argv[1], sys.argv[2], int(sys.argv[3]) if len(sys.argv) > 3 else 1)
