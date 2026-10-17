"""Sound design and score for DOOM vs SPIDER-MAN.

Everything is synthesised (filtered noise, oscillators, additive metal, a small
subtractive "orchestra"), so the soundtrack regenerates with the picture. SFX
cues come from the sequence scripts (seq.sfx, in animation frames) and are
mapped through each sequence's hit-stop frame map onto the exact rendered frame.

Score: a dark low-brass motif for DOOM (D minor: D-F-E-D), a bright plucked
arpeggio and a rising hero motif for SPIDER-MAN, a 132 bpm bass ostinato under
the fighting, a riser into the backfire -- then silence -- and the hero motif in
full over the final perch and title.

usage: python3 dv_audio.py OUT.wav
"""
import sys
import wave

import numpy as np

from audio import (SR, noise, filt, env, tone, norm, add, reverb, cue_times, whoosh, impact, step, glint, taiko,
                   skid, SFX as BASE_SFX)

RNG = np.random.default_rng(23)


def t_axis(dur):
    return np.arange(int(dur * SR)) / SR


def chirp(dur, f0, f1, curve='exp'):
    t = t_axis(dur)
    u = t / dur
    f = f0 * (f1 / f0) ** u if curve == 'exp' else f0 + (f1 - f0) * u
    return np.sin(2 * np.pi * np.cumsum(f) / SR)


def fade(x, a=0.005, r=0.02):
    n = len(x)
    e = np.ones(n)
    na, nr = int(a * SR), int(r * SR)
    if na:
        e[:na] = np.linspace(0, 1, na)
    if nr:
        e[-nr:] *= np.linspace(1, 0, nr)
    return x * e


def metal(f0, dur, decay=0.4, ratios=(1.0, 2.76, 5.40, 8.93, 13.34), amps=(1, 0.6, 0.35, 0.2, 0.12)):
    """Inharmonic struck metal."""
    t = t_axis(dur)
    x = sum(a * np.sin(2 * np.pi * f0 * r * t + RNG.uniform(0, 6)) * np.exp(-t / (decay / (1 + 0.4 * k)))
            for k, (r, a) in enumerate(zip(ratios, amps)))
    return x


def crackle(dur, rate=180, width=0.0012):
    """Random electric clicks."""
    n = int(dur * SR)
    x = np.zeros(n)
    k = RNG.poisson(rate * dur)
    for i in RNG.integers(0, n, k):
        w = int(width * SR * RNG.uniform(0.5, 2.0))
        seg = RNG.standard_normal(w) * np.exp(-np.arange(w) / max(1, w / 4))
        x[i:i + w] += seg[:max(0, min(w, n - i))]
    return filt(x, 'high', 900)


# ------------------------------------------------------------------ effects
def thwip():
    dur = 0.2
    t = t_axis(dur)
    sweep = chirp(dur, 3600, 650) * np.exp(-t / 0.05)
    hiss = filt(noise(dur), 'band', (1500, 7000)) * np.exp(-t / 0.04)
    snap = filt(noise(dur), 'high', 3000) * np.exp(-t / 0.006)
    return norm(0.5 * sweep + hiss + 0.8 * snap, 0.5)


def spider_sense():
    dur = 0.8
    t = t_axis(dur)
    x = sum(np.sin(2 * np.pi * f * t + RNG.uniform(0, 6)) for f in (2900, 3650, 4410, 5230))
    x *= (0.6 + 0.4 * np.sin(2 * np.pi * 23 * t)) * env(len(t), 0.03, 0.25)
    x += 0.3 * chirp(dur, 900, 2600) * env(len(t), 0.01, 0.2)
    return norm(x, 0.2)


def charge(dur, f0=180, f1=900, crack=True):
    t = t_axis(dur)
    u = t / dur
    x = 0.6 * chirp(dur, f0, f1) + 0.3 * chirp(dur, f0 * 2.01, f1 * 2.01) + 0.4 * chirp(dur, f0 / 2, f1 / 2)
    x *= (0.3 + 0.7 * u) * (0.85 + 0.15 * np.sin(2 * np.pi * (6 + 20 * u) * t))
    if crack:
        x += 0.5 * crackle(dur, rate=60 + 200 * dur) * (0.2 + 0.8 * u)
    return norm(fade(x, 0.02, 0.03), 0.45)


def bolt():
    dur = 0.45
    t = t_axis(dur)
    saw = 2 * ((np.cumsum(1400 * (200 / 1400) ** (t / 0.3)) / SR) % 1.0) - 1
    x = filt(saw, 'low', 3000) * np.exp(-t / 0.12)
    x += 0.8 * filt(noise(dur), 'band', (500, 5000)) * np.exp(-t / 0.05)
    x += 0.9 * tone(dur, 160, 50, 0.08)
    return norm(x, 0.6)


def blast(power=1.0):
    dur = 1.6
    t = t_axis(dur)
    x = impact(1.3 * power, 'hit')
    x = np.pad(x, (0, max(0, len(t) - len(x))))[:len(t)]
    rumble = filt(noise(dur), 'low', 220) * env(len(t), 0.01, 0.6, 2.0)
    x += 0.9 * rumble + 0.35 * crackle(dur, rate=120) * np.exp(-t / 0.5)
    return norm(x, 0.85)


def shield_up():
    dur = 0.7
    t = t_axis(dur)
    x = sum(a * chirp(dur, f * 0.8, f) for f, a in ((440, 1), (660, 0.7), (990, 0.5), (1320, 0.3)))
    x *= env(len(t), 0.05, 0.35) * (0.8 + 0.2 * np.sin(2 * np.pi * 14 * t))
    return norm(x, 0.3)


def shield_down():
    return shield_up()[::-1] * 0.8


def shield_hit():
    dur = 0.9
    x = metal(620, dur, 0.35) + 0.6 * tone(dur, 300, 120, 0.06)
    x += 0.5 * filt(noise(dur), 'band', (2000, 6000)) * env(int(dur * SR), 0.001, 0.02)
    return norm(x, 0.5)


def clank(big=False):
    dur = 0.8 if big else 0.45
    x = metal(380 if big else 760, dur, 0.28 if big else 0.14)
    x += (1.0 if big else 0.6) * tone(dur, 180, 70, 0.05)
    x += 0.6 * filt(noise(dur), 'high', 2500) * env(int(dur * SR), 0.0005, 0.01)
    return norm(x, 0.7 if big else 0.5)


def kick_metal():
    x = impact(1.6, 'hit')
    m = metal(300, len(x) / SR, 0.5)
    return norm(x + 0.35 * m, 0.95)


def skid_metal():
    dur = 0.9
    t = t_axis(dur)
    x = filt(noise(dur), 'band', (1800, 7000)) * (0.6 + 0.4 * np.abs(np.sin(2 * np.pi * 31 * t)))
    x += 0.6 * crackle(dur, rate=300)
    return norm(x * np.linspace(1, 0, len(t)) ** 1.3, 0.35)


def water_gush():
    dur = 1.8
    t = t_axis(dur)
    x = filt(noise(dur), 'band', (250, 2600)) * (0.7 + 0.3 * filt(noise(dur), 'low', 12) * 4)
    return norm(x * env(len(t), 0.02, 1.2, 1.5), 0.45)


def grab():
    dur = 0.3
    x = metal(900, dur, 0.06) + tone(dur, 220, 90, 0.04)
    return norm(x, 0.5)


def electric(dur=1.0, power=1.0):
    t = t_axis(dur)
    buzz = 2 * ((t * 120) % 1.0) - 1 + 0.5 * (2 * ((t * 240.7) % 1.0) - 1)
    buzz = filt(buzz, 'low', 2500) * (0.5 + 0.5 * (filt(noise(dur), 'low', 30) * 6).clip(-1, 1))
    x = 0.5 * buzz + crackle(dur, rate=500 * power)
    return norm(fade(x, 0.005, 0.15), 0.55 * min(1.2, power))


def zap_big():
    dur = 0.9
    t = t_axis(dur)
    x = electric(dur, 1.4) + 0.8 * tone(dur, 140, 40, 0.15) + 0.7 * filt(noise(dur), 'high', 1500) * np.exp(-t / 0.04)
    return norm(x, 0.8)


def web_splat():
    dur = 0.3
    t = t_axis(dur)
    x = filt(noise(dur), 'low', 1500) * np.exp(-t / 0.04) + 0.6 * tone(dur, 260, 90, 0.03)
    return norm(x, 0.5)


def strain():
    dur = 0.6
    t = t_axis(dur)
    x = np.tanh(3 * (chirp(dur, 500, 1500) + 0.5 * chirp(dur, 760, 2300))) * env(len(t), 0.02, 0.5)
    return norm(x + 0.4 * crackle(dur, rate=300), 0.35)


def backfire():
    dur = 3.0
    t = t_axis(dur)
    x = np.zeros(len(t))
    hit = impact(2.4, 'finish')
    x[:len(hit)] += 1.4 * hit
    x += 1.0 * filt(noise(dur), 'low', 160) * env(len(t), 0.005, 1.4, 1.6)
    x += 0.6 * crackle(dur, rate=700) * np.exp(-t / 1.0)
    x += 0.3 * metal(210, dur, 1.2)
    return norm(x, 1.0)


def steam():
    dur = 2.4
    t = t_axis(dur)
    x = filt(noise(dur), 'high', 2500) * env(len(t), 0.03, 1.4, 1.5)
    return norm(x, 0.25)


def splash():
    dur = 0.6
    t = t_axis(dur)
    x = filt(noise(dur), 'band', (400, 4000)) * np.exp(-t / 0.12)
    for k in range(5):
        i = int(RNG.uniform(0.02, 0.3) * SR)
        p = chirp(0.05, 1400, 500) * np.exp(-t_axis(0.05) / 0.015)
        x[i:i + len(p)] += 0.4 * p
    return norm(x, 0.4)


def drips():
    dur = 1.2
    x = np.zeros(int(dur * SR))
    for k in range(6):
        i = int(RNG.uniform(0, 1.0) * SR)
        p = chirp(0.06, 1600 + RNG.uniform(-200, 300), 700) * np.exp(-t_axis(0.06) / 0.012)
        x[i:i + len(p)] += p
    return norm(x, 0.25)


def jet(dur, power=1.0, sputter=0.0):
    t = t_axis(dur)
    roar = filt(noise(dur), 'low', 900) + 0.5 * filt(noise(dur), 'band', (900, 3500))
    roar *= 0.8 + 0.2 * filt(noise(dur), 'low', 8) * 5
    if sputter:
        gate = (filt(noise(dur), 'low', 6) > -0.05 + 0.15 * sputter).astype(float)
        gate = filt(gate, 'low', 40)
        roar *= 0.3 + 0.7 * gate
    roar += 0.6 * tone(dur, 70, 55, 10.0) * power
    return norm(fade(roar, 0.15, 0.4), 0.55 * power)


def doom_glint():
    dur = 1.2
    t = t_axis(dur)
    g = glint()
    x = 0.7 * np.sin(2 * np.pi * 73.4 * t) * env(len(t), 0.01, 0.6)
    x[:len(g)] += 0.5 * g[:len(t)]
    return norm(x, 0.35)


def debris():
    dur = 1.0
    x = np.zeros(int(dur * SR))
    for k in range(14):
        i = int(RNG.uniform(0, 0.8) * SR)
        p = metal(RNG.uniform(1200, 2600), 0.05, 0.02)
        x[i:i + len(p)] += p * RNG.uniform(0.3, 1.0)
    return norm(x, 0.25)


SFX = dict(BASE_SFX)
SFX.update({
    'thwip': lambda g: thwip() * g,
    'spider_sense': lambda g: spider_sense() * g,
    'charge_short': lambda g: charge(0.5, 220, 700) * g,
    'charge': lambda g: charge(1.0, 160, 900) * g,
    'charge_big': lambda g: charge(3.2, 90, 1100) * g,
    'bolt': lambda g: bolt() * g,
    'blast': lambda g: blast(g),
    'shield_up': lambda g: shield_up() * g,
    'shield_down': lambda g: shield_down() * g,
    'shield_hit': lambda g: shield_hit() * g,
    'kick_metal': lambda g: kick_metal() * g,
    'skid_metal': lambda g: skid_metal() * g,
    'water_gush': lambda g: water_gush() * g,
    'clank': lambda g: clank() * min(1.0, g + 0.3),
    'clank_big': lambda g: clank(True) * g,
    'grab': lambda g: grab() * g,
    'zap_big': lambda g: zap_big() * min(1.0, g),
    'electric': lambda g: electric(1.1, 1.0) * g,
    'electric_long': lambda g: electric(2.0, 1.4) * g,
    'web_splat': lambda g: web_splat() * g,
    'strain': lambda g: strain() * g,
    'backfire': lambda g: backfire(),
    'steam': lambda g: steam() * g,
    'splash': lambda g: splash() * g,
    'water_drip': lambda g: drips() * g,
    'jet_long': lambda g: jet(2.6, 1.0) * g,
    'jet_brake': lambda g: jet(0.8, 1.3) * g,
    'jet_sputter': lambda g: jet(1.6, 0.9, sputter=1.0) * g,
    'doom_glint': lambda g: doom_glint() * g,
    'debris': lambda g: debris() * g,
})


# ------------------------------------------------------------------ score
def mtof(m):
    return 440.0 * 2 ** ((m - 69) / 12.0)


NOTE = {n: i for i, n in enumerate(['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B'])}


def nm(s):
    """'D3' -> midi number"""
    return 12 * (int(s[-1]) + 1) + NOTE[s[:-1]]


def saw(f, dur, detune=0.0):
    t = t_axis(dur)
    ph = (t * f * (1 + detune)) % 1.0
    return 2 * ph - 1


def adsr(n, a, d, s, r, sustain_end=None):
    e = np.ones(n) * s
    na, nd, nr = int(a * SR), int(d * SR), int(r * SR)
    na = min(na, n)
    e[:na] = np.linspace(0, 1, na)
    if nd:
        e[na:na + nd] = np.linspace(1, s, len(e[na:na + nd]))
    if nr:
        e[-nr:] *= np.linspace(1, 0, min(nr, n))
    return e


def brass(note, dur, cutoff=1400, vel=1.0):
    f = mtof(nm(note) if isinstance(note, str) else note)
    x = saw(f, dur, -0.003) + saw(f, dur, 0.004) + 0.5 * saw(f / 2, dur)
    n = len(x)
    # filter "swell": blend a darker and a brighter version
    dark, bright = filt(x, 'low', cutoff * 0.4), filt(x, 'low', cutoff)
    sw = np.clip(np.arange(n) / (0.12 * SR), 0, 1)
    y = dark * (1 - sw) + bright * sw
    return y * adsr(n, 0.05, 0.2, 0.75, 0.25) * vel


def pluck(note, dur, vel=1.0, bright=4000):
    f = mtof(nm(note) if isinstance(note, str) else note)
    t = t_axis(dur)
    x = (0.6 * np.sign(np.sin(2 * np.pi * f * t)) + saw(f, dur, 0.002)) * np.exp(-t / 0.25)
    return filt(x, 'low', bright) * fade(np.ones(len(t)), 0.002, 0.05) * vel


def pad(notes, dur, cutoff=900, vel=1.0):
    x = sum(saw(mtof(nm(n)), dur, d) for n in notes for d in (-0.004, 0.005))
    x = filt(x, 'low', cutoff)
    return x * adsr(len(x), 0.6, 0.2, 0.9, 0.8) * vel


def bell(note, dur=1.5, vel=1.0):
    f = mtof(nm(note))
    return metal(f, dur, 0.6, ratios=(1, 2.0, 3.01, 4.2), amps=(1, 0.5, 0.3, 0.15)) * vel


def score(total, spans, leak_t):
    n = int(total * SR)
    mus = np.zeros(n)
    amb = np.zeros(n)

    def at(name, f):
        for nm_, s0, s1, first in spans:
            if nm_ == name:
                return s0 + first.get(f, max(first.values()) if f > max(first) else 0) / 24.0
        return 0.0

    def put(buf, x, ts, g=1.0):
        add(buf, x * g, ts)

    # ---- ambience: wind, city hum, a distant siren, and the leak after it starts
    t = np.arange(n) / SR
    wind = filt(noise(total), 'low', 350) * 0.6 + filt(noise(total), 'band', (500, 1400)) * 0.12
    wind *= 0.6 + 0.4 * np.sin(2 * np.pi * 0.09 * t + 1.0) ** 2
    hum = filt(noise(total), 'low', 140) * (0.8 + 0.2 * np.sin(2 * np.pi * 0.05 * t))
    amb += norm(wind, 0.07) + norm(hum, 0.05)
    for t0, dur in ((2.0, 7.0), (at('D3', 140), 6.0)):
        tt = t_axis(dur)
        f = 780 + 170 * np.sin(2 * np.pi * 0.45 * tt)
        sir = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.sin(np.pi * tt / dur) ** 2
        put(amb, filt(sir, 'low', 1200), t0, 0.018)
    i0 = int(leak_t * SR)
    if i0 < n:
        m = n - i0
        water = filt(noise(m / SR), 'band', (300, 3000)) * (0.75 + 0.25 * np.sin(2 * np.pi * 0.7 * np.arange(m) / SR))
        water *= np.clip(np.arange(m) / (0.6 * SR), 0, 1)
        amb[i0:] += norm(water, 0.04)

    # ---- DOOM: drone under the descent, a hit on the landing, the motif on his close-up
    d_end = at('D1', 58)
    drone = pad(['D2', 'A2'], d_end + 1.0, cutoff=500, vel=1.0) + 0.6 * pad(['D1'], d_end + 1.0, cutoff=200)
    put(mus, norm(drone, 0.18), 0.0)
    put(mus, taiko(0.8), at('D1', 58))
    put(mus, norm(brass('D2', 1.6, 900), 0.3), at('D1', 58))
    t0 = at('D1', 99)
    for k, nt in enumerate(['D3', 'F3', 'E3', 'D3']):
        put(mus, norm(brass(nt, 0.55 if k < 3 else 1.1, 1200), 0.28), t0 + k * 0.45)
    put(mus, norm(pad(['D2', 'A2', 'F3'], 2.4, 600), 0.14), t0)

    # ---- SPIDER-MAN: plucked arpeggio under the swing, hero motif on his close-up
    t0 = at('D1', 133)
    beat = 60 / 140.0 / 2
    arp = ['F4', 'A4', 'C5', 'F5', 'C5', 'A4', 'F4', 'A4', 'D4', 'F4', 'A4', 'D5', 'A4', 'F4', 'C4', 'E4']
    for k in range(int((at('D1', 182) - t0) / beat)):
        put(mus, norm(pluck(arp[k % len(arp)], 0.4), 0.16), t0 + k * beat)
    t0 = at('D1', 186)
    motif = [('D5', 0.3), ('A4', 0.3), ('D5', 0.3), ('F5', 0.6), ('E5', 0.6)]
    tt = t0
    for nt, du in motif:
        put(mus, norm(pluck(nt, du + 0.3, bright=6000), 0.2), tt)
        put(mus, norm(brass(nt, du + 0.1, 2600), 0.1), tt)
        tt += du
    put(mus, norm(pad(['F3', 'A3', 'C4'], 2.4, 1000), 0.12), t0)
    put(mus, norm(pad(['D3', 'A3', 'F4'], at('D2', 0) - at('D1', 216) + 0.6, 700), 0.12), at('D1', 216))

    # ---- the fight: a 132 bpm bass ostinato (sixteenths) whose level follows the action
    bpm = 132.0
    six = 60.0 / bpm / 4
    pattern = ['D2', 'D2', 'D3', 'D2', 'D2', 'F2', 'D2', 'G2', 'D2', 'D2', 'D3', 'D2', 'A2', 'D2', 'C3', 'D2']
    level = [(at('D2', 0), 0.0), (at('D2', 4), 0.6), (at('D2', 60), 0.8), (at('D2', 82), 1.0), (at('D2', 100), 0.45),
             (at('D2', 180), 0.5), (at('D3', 0), 0.8), (at('D3', 46), 1.0), (at('D3', 72), 1.0), (at('D3', 75), 0.0),
             (at('D3', 100), 0.0), (at('D3', 104), 0.6), (at('D3', 132), 0.3), (at('D3', 140), 0.0)]
    lt = [p[0] for p in level]
    lv = [p[1] for p in level]
    k = 0
    tk = at('D2', 0)
    while tk < at('D3', 140):
        g = float(np.interp(tk, lt, lv))
        if g > 0.02:
            f = mtof(nm(pattern[k % 16]))
            dur = six * 0.9
            tt_ = t_axis(dur)
            b = (saw(f, dur) + 0.8 * np.sin(2 * np.pi * f * tt_)) * np.exp(-tt_ / 0.09)
            put(mus, filt(b, 'low', 600) * 0.11 * g, tk)
            if k % 4 == 0:
                put(mus, filt(noise(0.05), 'high', 6000) * np.exp(-t_axis(0.05) / 0.01) * 0.05 * g, tk)
            if k % 8 == 4:
                put(mus, filt(noise(0.12), 'band', (180, 1800)) * np.exp(-t_axis(0.12) / 0.04) * 0.09 * g, tk)
        tk += six
        k += 1
    for f_, nt in ((82, 'D3'), (86, 'A2')):
        put(mus, norm(brass(nt, 0.9, 2000), 0.26), at('D2', f_))
    for k2, nt in enumerate(['D3', 'F3', 'E3', 'D3']):
        put(mus, norm(brass(nt, 0.5 if k2 < 3 else 1.0, 1100), 0.22), at('D2', 160) + k2 * 0.42)
    # the shock: a tritone stab; then the hurt, minor version of his motif
    put(mus, norm(brass('D3', 1.2, 2200) + brass('G#3', 1.2, 2200), 0.3), at('D3', 75))
    put(mus, norm(pad(['D2', 'G#2', 'D3'], 2.0, 700), 0.12), at('D3', 75))
    tt = at('D3', 146)
    for nt, du in [('D4', 0.45), ('A3', 0.45), ('D4', 0.45), ('F4', 0.9), ('E4', 1.2)]:
        put(mus, norm(pluck(nt, du + 0.4, bright=2500), 0.15), tt)
        tt += du
    put(mus, norm(pad(['D3', 'F3', 'A3'], at('D4', 0) - at('D3', 140) + 1.0, 600), 0.12), at('D3', 140))

    # ---- the backfire: a riser that cuts to silence on the impact
    r0, r1 = at('D4', 6), at('D4', 86)
    dur = r1 - r0
    tt = t_axis(dur)
    u = tt / dur
    riser = filt(noise(dur), 'band', (300, 5000)) * u ** 2 * 0.5 + 0.4 * chirp(dur, 110, 880) * u ** 1.5
    riser += pad(['D2', 'A2', 'D3', 'G#3'], dur, cutoff=1500) * u * 0.3
    put(mus, norm(riser, 0.3), r0)
    tk = r0
    while tk < r1:
        uu = (tk - r0) / dur
        p = (saw(73.4, 0.08) + np.sin(2 * np.pi * 73.4 * t_axis(0.08))) * np.exp(-t_axis(0.08) / 0.04)
        put(mus, filt(p, 'low', 500) * 0.12 * (0.3 + 0.7 * uu), tk)
        tk += six * (2.0 - 1.4 * uu)
    put(mus, norm(bell('A5', 1.6), 0.12), at('D4', 48))
    # aftermath and the retreat
    put(mus, norm(pad(['D2', 'A2'], at('D4', 206) - at('D4', 104), 400), 0.12), at('D4', 104))
    for k2, nt in enumerate(['D3', 'F3', 'E3', 'D3']):
        put(mus, norm(brass(nt, 0.45 if k2 < 3 else 0.9, 1000), 0.2), at('D4', 216) + k2 * 0.38)
    t0 = at('D4', 246)
    for k in range(int((at('D4', 279) - t0) / beat)):
        put(mus, norm(pluck(arp[k % len(arp)], 0.4), 0.13), t0 + k * beat)
    # the perch and the title: the hero motif, in full
    t0 = at('D4', 304)
    tt = t0
    for nt, du in [('D4', 0.36), ('A4', 0.36), ('D5', 0.36), ('F5', 0.72), ('E5', 0.36), ('D5', 0.36),
                   ('C5', 0.36), ('D5', 1.6)]:
        put(mus, norm(brass(nt, du + 0.15, 2400), 0.22), tt)
        put(mus, norm(pluck(nt, du + 0.4, bright=6000), 0.14), tt)
        tt += du
    put(mus, norm(pad(['D3', 'A3', 'F4', 'A4'], total - t0, 1200), 0.16), t0)
    put(mus, norm(pad(['D2', 'A2'], total - t0, 400), 0.12), t0)
    put(mus, taiko(0.9), t0)
    put(mus, taiko(0.7), at('D4', 338))
    return mus, amb


def render(seqs, path):
    cues, spans, total = cue_times(seqs)
    leak_t = 0.0
    for nm_, s0, s1, first in spans:
        if nm_ == 'D2':
            from dv02 import LEAK_F
            leak_t = s0 + first[LEAK_F] / 24.0
    n = int(total * SR) + SR
    sfx = np.zeros((n, 2))
    for tsec, kind, g in cues:
        if kind in SFX:
            add(sfx, SFX[kind](g), tsec, pan=float(RNG.uniform(-0.25, 0.25)))
        else:
            print('missing sfx:', kind)
    sfx[:, 0] = reverb(sfx[:, 0])
    sfx[:, 1] = reverb(sfx[:, 1])
    mus, amb = score(total + 1, spans, leak_t)
    mus = reverb(mus[:n], 0.3)
    mix = sfx * 0.9 + np.stack([mus, mus], 1)[:n] * 0.9 + np.stack([amb, amb * 0.95], 1)[:n]
    mix = np.tanh(mix * 1.2) / np.tanh(1.2)
    mix = mix / (np.max(np.abs(mix)) or 1) * 0.89
    f_ = int(0.8 * SR)
    mix[-f_:] *= np.linspace(1, 0, f_)[:, None]
    pcm = (mix * 32767).astype('<i2')
    with wave.open(path, 'wb') as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    return total, len(cues)


if __name__ == '__main__':
    import importlib
    seqs = [importlib.import_module(m).build() for m in ('dv01', 'dv02', 'dv03', 'dv04')]
    total, ncues = render(seqs, sys.argv[1])
    print(f'{total:.2f}s of audio, {ncues} cues -> {sys.argv[1]}')
