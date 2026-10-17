"""Procedural sound design and score.

Every sound is synthesised (filtered noise + oscillators), so the soundtrack is
as regenerable as the picture. Cues come from the sequence scripts (`seq.sfx`)
in animation frames and are mapped through each sequence's hit-stop frame map,
so a sound always lands on the exact rendered frame of its contact drawing.

usage: python3 audio.py OUT.wav            (all sequences)
"""
import sys
import wave

import numpy as np
from scipy.signal import butter, sosfilt

from engine import build_frame_map, FPS

SR = 48000
RNG = np.random.default_rng(11)


# ------------------------------------------------------------------ building blocks
def noise(dur):
    return RNG.standard_normal(int(dur * SR))


def filt(x, kind, f):
    if kind == 'band':
        sos = butter(2, [f[0] / (SR / 2), f[1] / (SR / 2)], btype='band', output='sos')
    else:
        sos = butter(2, f / (SR / 2), btype=kind, output='sos')
    return sosfilt(sos, x)


def env(n, attack, decay, curve=3.0):
    t = np.arange(n) / SR
    a = np.clip(t / max(attack, 1e-4), 0, 1)
    d = np.exp(-np.maximum(t - attack, 0) / max(decay, 1e-4) * curve / 3.0)
    return a * d


def tone(dur, f0, f1, decay):
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = f1 + (f0 - f1) * np.exp(-t / 0.05)          # fast pitch drop: the "thump"
    ph = 2 * np.pi * np.cumsum(f) / SR
    return np.sin(ph) * np.exp(-t / decay)


def norm(x, g=1.0):
    m = np.max(np.abs(x)) or 1.0
    return x / m * g


# ------------------------------------------------------------------ sound effects
def whoosh(big=False):
    dur = 0.42 if big else 0.28
    n = int(dur * SR)
    t = np.linspace(0, 1, n)
    lo = filt(noise(dur), 'band', (180, 700) if big else (350, 1100))
    hi = filt(noise(dur), 'band', (900, 3200) if big else (1400, 4200))
    bell = np.sin(np.pi * np.clip(t, 0, 1)) ** (1.5 if big else 2.2)
    sweep = np.clip(t * 1.6, 0, 1)
    x = (lo * (1 - 0.6 * sweep) + 0.6 * hi * np.sin(np.pi * t) ** 3) * bell
    return norm(x, 0.55 if big else 0.4)


def impact(power=1.0, kind='hit'):
    dur = 0.35 + 0.6 * power
    sub = tone(dur, 140 + 30 * power, 52, 0.12 + 0.12 * power)
    body = filt(noise(dur), 'low', 1800) * env(int(dur * SR), 0.001, 0.05 + 0.03 * power)
    crack = filt(noise(dur), 'high', 2600) * env(int(dur * SR), 0.0005, 0.012 + 0.006 * power)
    tail = filt(noise(dur), 'low', 700) * env(int(dur * SR), 0.01, 0.18 + 0.35 * power, 2.0) * 0.35 * power
    x = 1.0 * sub + 0.7 * body + 0.6 * crack + tail
    if kind == 'hit_shin':
        x += 0.5 * filt(noise(dur), 'band', (700, 1800)) * env(int(dur * SR), 0.0005, 0.03)
    if kind in ('clash', 'finish'):
        ring = sum(np.sin(2 * np.pi * f * np.arange(int(dur * SR)) / SR) for f in (220, 331, 497))
        x += 0.12 * ring * env(int(dur * SR), 0.002, 0.6 * power, 2.0)
        x += 0.8 * tone(dur, 90, 38, 0.4 * power)
    return norm(x, min(1.0, 0.55 + 0.25 * power))


def parry():
    dur = 0.12
    x = filt(noise(dur), 'band', (1800, 6000)) * env(int(dur * SR), 0.0005, 0.02)
    x += 0.4 * tone(dur, 400, 220, 0.03)
    return norm(x, 0.45)


def skid(dur=0.6):
    n = int(dur * SR)
    grit = filt(noise(dur), 'band', (700, 3800))
    am = 0.6 + 0.4 * np.abs(filt(noise(dur), 'low', 40)) / 2
    fade = np.linspace(1, 0, n) ** 1.5
    return norm(grit * am * fade * env(n, 0.01, 10), 0.35)


def step(g=1.0):
    dur = 0.18
    x = 0.8 * tone(dur, 120, 70, 0.04) + 0.5 * filt(noise(dur), 'low', 1400) * env(int(dur * SR), 0.001, 0.03)
    return norm(x, 0.3 * g)


def glint():
    dur = 0.9
    n = int(dur * SR)
    t = np.arange(n) / SR
    x = sum(np.sin(2 * np.pi * f * t + RNG.uniform(0, 6)) * w for f, w in ((2350, 1), (3520, 0.6), (5280, 0.35)))
    x *= (0.75 + 0.25 * np.sin(2 * np.pi * 9 * t)) * env(n, 0.004, 0.28)
    return norm(x, 0.22)


def breath(g=1.0):
    dur = 0.9
    n = int(dur * SR)
    x = filt(noise(dur), 'band', (400, 2200)) * np.sin(np.pi * np.linspace(0, 1, n)) ** 2
    return norm(x, 0.12 * g)


def taiko(g=1.0):
    dur = 1.6
    x = tone(dur, 110, 48, 0.45) + 0.35 * filt(noise(dur), 'low', 500) * env(int(dur * SR), 0.002, 0.25)
    return norm(x, 0.9 * g)


SFX = {
    'whoosh': lambda g: whoosh(False) * g,
    'whoosh_big': lambda g: whoosh(True) * g,
    'dash': lambda g: (whoosh(True) * 0.6 + np.pad(step(1.2), (0, int(0.42 * SR) - int(0.18 * SR)))) * g,
    'jump': lambda g: (whoosh(True) * 0.7 + np.pad(step(1.4), (0, int(0.42 * SR) - int(0.18 * SR)))) * g,
    'hit': lambda g: impact(1.0 * g, 'hit'),
    'hit_shin': lambda g: impact(0.8 * g, 'hit_shin'),
    'hit_block': lambda g: impact(1.1 * g, 'hit'),
    'slam': lambda g: impact(1.6 * g, 'clash'),
    'clash': lambda g: impact(1.6 * g, 'clash'),
    'finish': lambda g: impact(2.0 * g, 'finish'),
    'thud': lambda g: impact(0.7 * g, 'hit') * 0.8,
    'parry': lambda g: parry() * g,
    'skid': lambda g: skid() * g,
    'step': lambda g: step(g),
    'land': lambda g: step(1.4 * g),
    'glint': lambda g: glint() * g,
    'breath': lambda g: breath(g),
}


def reverb(x, mix=0.22):
    """Cheap stereo room: a few damped feedback delays."""
    out = np.copy(x)
    for d, g in ((0.031, 0.5), (0.047, 0.42), (0.071, 0.35), (0.113, 0.28), (0.167, 0.2)):
        k = int(d * SR)
        y = np.zeros_like(x)
        y[k:] = x[:-k] * g
        out += filt(y, 'low', 3500) * mix
    return out


# ------------------------------------------------------------------ assembly
def cue_times(seqs):
    """[(seconds, kind, gain)] for every sfx cue, plus per-sequence spans."""
    out = []
    spans = []
    t0 = 0
    for seq in seqs:
        fmap = build_frame_map(seq.n, seq.hitstops)
        first = {}
        for i, (a, stop) in enumerate(fmap):
            first.setdefault(a, i)
        for f, kind, g in seq.sound:
            if f in first:
                out.append(((t0 + first[f]) / FPS, kind, g))
        spans.append((seq.name, t0 / FPS, (t0 + len(fmap)) / FPS, first))
        t0 += len(fmap)
    return out, spans, t0 / FPS


def score(total, spans):
    """Wind bed + drone whose level follows the fight's intensity, and taiko on story beats."""
    n = int(total * SR)
    t = np.arange(n) / SR
    wind = filt(noise(total), 'low', 380) * 0.5 + filt(noise(total), 'band', (500, 1300)) * 0.15
    wind *= 0.55 + 0.45 * np.sin(2 * np.pi * 0.11 * t + 1.0) ** 2
    wind = norm(wind, 0.09)

    def at(name, f):
        for nm, s0, s1, first in spans:
            if nm == name:
                return s0 + first.get(f, 0) / FPS
        return 0.0
    # intensity keyframes (seconds, level)
    pts = [(0, 0.15), (at('S1', 132), 0.35), (at('S1', 179), 0.55), (at('S2', 0), 0.45), (at('S2', 94), 0.6),
           (at('S3', 0), 0.6), (at('S3', 28), 0.8), (at('S3', 84), 0.55), (at('S4', 26), 1.0), (at('S4', 44), 0.35),
           (at('S4', 92), 0.75), (at('S4', 118), 1.0), (at('S4', 119) + 0.05, 0.0), (at('S4', 200), 0.0),
           (at('S4', 230), 0.3), (total - 1.5, 0.35), (total, 0.0)]
    lvl = np.interp(t, [p[0] for p in pts], [p[1] for p in pts])
    drone = (np.sin(2 * np.pi * 55 * t) + 0.6 * np.sin(2 * np.pi * 82.41 * t + 0.4) +
             0.35 * np.sin(2 * np.pi * 110.0 * t * (1 + 0.002 * np.sin(2 * np.pi * 0.2 * t))))
    drone = filt(drone, 'low', 400) * (0.8 + 0.2 * np.sin(2 * np.pi * 0.25 * t)) * lvl
    drone = norm(drone, 0.16)
    mus = wind + drone
    beats = [at('S1', 85), at('S1', 112), at('S3', 21), at('S4', 26), at('S4', 118), at('S4', 302)]
    # heartbeat under the beat before the last charge
    hb0, hb1 = at('S4', 44), at('S4', 99)
    hb = list(np.arange(hb0, hb1, 0.82)) + list(np.arange(hb0 + 0.22, hb1, 0.82))
    for b in beats:
        add(mus, taiko(0.8), b)
    for b in hb:
        add(mus, taiko(0.35), b)
    return mus


def add(buf, x, t, pan=0.0):
    i = int(t * SR)
    if buf.ndim == 1:
        j = min(len(buf), i + len(x))
        if i < len(buf):
            buf[i:j] += x[:j - i]
        return
    j = min(len(buf), i + len(x))
    if i < len(buf):
        buf[i:j, 0] += x[:j - i] * (1 - pan) * 0.5 * 2 ** 0.5
        buf[i:j, 1] += x[:j - i] * (1 + pan) * 0.5 * 2 ** 0.5


def render(seqs, path):
    cues, spans, total = cue_times(seqs)
    n = int(total * SR) + SR
    sfx = np.zeros((n, 2))
    for tsec, kind, g in cues:
        if kind in SFX:
            add(sfx, SFX[kind](g), tsec, pan=float(RNG.uniform(-0.25, 0.25)))
    sfx[:, 0] = reverb(sfx[:, 0])
    sfx[:, 1] = reverb(sfx[:, 1])
    mus = score(total + 1, spans)[:n]
    mix = sfx * 0.9 + np.stack([mus, mus], 1)[:n] * 0.8
    mix = np.tanh(mix * 1.2) / np.tanh(1.2)                  # soft limiter
    mix = mix / (np.max(np.abs(mix)) or 1) * 0.89             # -1 dBFS
    fade = int(0.5 * SR)
    mix[-fade:] *= np.linspace(1, 0, fade)[:, None]
    pcm = (mix * 32767).astype('<i2')
    with wave.open(path, 'wb') as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    return total, len(cues)


if __name__ == '__main__':
    import importlib
    seqs = [importlib.import_module(m).build() for m in ('seq01', 'seq02', 'seq03', 'seq04')]
    total, ncues = render(seqs, sys.argv[1])
    print(f'{total:.2f}s of audio, {ncues} cues -> {sys.argv[1]}')
