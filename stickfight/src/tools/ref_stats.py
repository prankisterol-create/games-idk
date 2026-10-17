"""Reference-video statistics used in docs/01_reference_analysis.md.

usage: python3 ref_stats.py VIDEO.mp4
Decodes the video at 160x90 greyscale, then reports cut timing, single-frame
flash/impact inserts and how often drawings change per second.
"""
import subprocess, sys
import numpy as np

W, H, FPS = 160, 90, 24


def load(path):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-vf", f"scale={W}:{H},format=gray",
                          "-f", "rawvideo", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(-1, H, W).astype(np.int16)


def main(path, lo_s=60, hi_s=340):
    a = load(path)
    d = np.abs(np.diff(a, axis=0)).mean(axis=(1, 2))
    br = a.reshape(len(a), -1).mean(1)
    cuts = [i + 1 for i in range(len(d)) if d[i] > 18 and d[i] > 3 * np.median(d[max(0, i - 6):i + 6] + 0.5)]
    lo, hi = lo_s * FPS, hi_s * FPS
    cs = [c for c in cuts if lo <= c < hi]
    flash = [c for c in cs if c + 1 in cs]
    real = [c for c in cs if c not in flash and c - 1 not in flash]
    dark = [c for c in flash if br[c] < 0.6 * min(br[c - 1], br[c + 1])]
    bright = [c for c in flash if br[c] > 1.4 * max(br[c - 1], br[c + 1])]
    sl = np.diff(real) / FPS
    print(f"frames {len(a)}  single-frame inserts {len(flash)} (dark {len(dark)}, bright {len(bright)})")
    print(f"true cuts {len(real)}  shot length mean {sl.mean():.2f}s median {np.median(sl):.2f}s")
    changes = np.array([(d[s * FPS:(s + 1) * FPS] >= 0.35).sum() for s in range(lo_s, hi_s)])
    print(f"changed frames per second: mean {changes.mean():.1f} median {np.median(changes):.0f}")
    for w in range(lo_s, hi_s, 20):
        n = sum(1 for c in flash if w * FPS <= c < (w + 20) * FPS)
        print(f"  {w // 60}:{w % 60:02d} flashes {n:2d} " + "#" * n)


if __name__ == "__main__":
    main(sys.argv[1])
