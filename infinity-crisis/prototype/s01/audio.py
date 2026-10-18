"""Synthesised temp soundtrack for the Sequence 1 prototype, cue-locked to data/shots/s01.yaml.

    python3 audio.py out.wav

Everything is generated (no samples, no existing music). Dialogue is not voiced; the picture
carries captions. Cue times come from the shot list, so retiming a shot moves its sound.
"""
import os
import sys

import numpy as np
from scipy import signal
from scipy.io import wavfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'tools'))
import common as C  # noqa: E402

SR = 48000
seq = C.load_yaml(os.path.join(C.DATA, 'shots', 's01.yaml'))
START = {}
t0 = 0.0
for shot in seq['shots']:
    START[shot['id']] = t0
    t0 += shot['dur']
DUR = t0
N = int(DUR * SR)
T = np.arange(N) / SR
R = np.random.default_rng(1)


def at(sid, offset=0.0):
    return START[sid] + offset


def env(points):
    """Piecewise-linear envelope from [(time, gain), ...]."""
    ts, gs = zip(*points)
    return np.interp(T, ts, gs, left=gs[0], right=gs[-1]).astype(np.float32)


def lp(x, f, order=2):
    return signal.sosfilt(signal.butter(order, f, 'low', fs=SR, output='sos'), x)


def hp(x, f, order=2):
    return signal.sosfilt(signal.butter(order, f, 'high', fs=SR, output='sos'), x)


def bp(x, lo, hi, order=2):
    return signal.sosfilt(signal.butter(order, [lo, hi], 'band', fs=SR, output='sos'), x)


def noise():
    return R.normal(0, 1, N).astype(np.float32)


def saw(freq, detune=0.0):
    ph = np.cumsum(np.full(N, freq * (1 + detune)) / SR)
    return (2 * (ph % 1) - 1).astype(np.float32)


def tone_burst(t, dur, freq, decay=8.0, harm=(1.0,), gain=1.0):
    out = np.zeros(N, np.float32)
    i0 = int(t * SR)
    n = min(int(dur * SR), N - i0)
    if n <= 0:
        return out
    tt = np.arange(n) / SR
    s = sum(a * np.sin(2 * np.pi * freq * (k + 1) * tt) for k, a in enumerate(harm))
    out[i0:i0 + n] = s * np.exp(-tt * decay) * gain
    return out


def drum(t, gain=1.0, f0=130, f1=45, decay=6.0):
    out = np.zeros(N, np.float32)
    i0 = int(t * SR)
    n = min(int(1.2 * SR), N - i0)
    if n <= 0:
        return out
    tt = np.arange(n) / SR
    f = f1 + (f0 - f1) * np.exp(-tt * 18)
    ph = np.cumsum(f) / SR
    body = np.sin(2 * np.pi * ph) * np.exp(-tt * decay)
    click = R.normal(0, 1, n) * np.exp(-tt * 60) * 0.3
    out[i0:i0 + n] = (body + click) * gain
    return out


L = np.zeros(N, np.float32)
Rr = np.zeros(N, np.float32)


def mix(x, g=1.0, pan=0.0):
    global L, Rr
    L += x * g * np.sqrt(0.5 * (1 - pan))
    Rr += x * g * np.sqrt(0.5 * (1 + pan))


# --- S01_010-020: silence, sub pressure, distant choir, wind
mix(np.sin(2 * np.pi * 30 * T) * env([(0, 0), (at('S01_010', 2.5), 0), (at('S01_010', 5), 0.012),
                                       (at('S01_050'), 0.012), (at('S01_060', 1), 0)]))
choir = np.zeros(N, np.float32)
for f in (146.83, 220.0, 293.66):                          # D3, A3, D4, 'oo' vowel
    for d in (-0.004, 0.0, 0.005):
        vib = 1 + 0.004 * np.sin(2 * np.pi * (5.1 + d * 100) * T)
        ph = np.cumsum(f * (1 + d) * vib) / SR
        voice = sum(a * np.sin(2 * np.pi * k * ph) for k, a in ((1, 1.0), (2, 0.5), (3, 0.12), (4, 0.05)))
        choir += voice
choir = bp(choir, 180, 1100) * env([(0, 0), (at('S01_010', 4), 0), (at('S01_020', 1.5), 0.03),
                                     (at('S01_030', 2.5), 0.02), (at('S01_040'), 0)])
mix(choir)
wind = lp(noise(), 700) * env([(at('S01_020'), 0), (at('S01_020', 2), 0.12), (at('S01_030', 0.5), 0.03),
                               (at('S01_040'), 0)])
mix(wind, pan=-0.2)

# --- rain bed (city), with the local silence of the freeze and the observatory interior
rain = hp(noise(), 1200) * 0.6
drops = np.zeros(N, np.float32)
idx = R.integers(0, N, 9000)
drops[idx] = R.uniform(0.3, 1.0, idx.size)
rain += bp(drops, 2000, 7000) * 0.7
rain_env = env([(at('S01_020', 3.8), 0), (at('S01_030', 1.5), 0.05), (at('S01_050', 1), 0.05),
                (at('S01_050', 1.1), 0.036), (at('S01_080', 0.48), 0.036), (at('S01_080', 0.5), 0.0),
                (at('S01_080', 2.0), 0.0), (at('S01_080', 2.03), 0.06), (at('S01_110'), 0.06),
                (at('S01_110', 0.02), 0.01), (at('S01_120'), 0.01), (at('S01_120', 0.05), 0.04),
                (at('S01_150'), 0.03), (at('S01_150', 0.2), 0.0)])
mix(rain * rain_env, pan=0.3)
mix(hp(noise(), 1300) * rain_env * 0.6, pan=-0.3)

# --- city: traffic rumble, horn, tyres, bell, crosswalk chirp
mix(lp(noise(), 250) * env([(at('S01_030'), 0), (at('S01_030', 1.5), 0.08), (at('S01_060', 4), 0.08),
                            (at('S01_070'), 0.03), (at('S01_100'), 0)]))
horn = (saw(233.1) + saw(277.2) * 0.8)
mix(lp(horn, 900) * env([(at('S01_030', 2.6), 0), (at('S01_030', 2.7), 0.02), (at('S01_030', 3.6), 0.02),
                         (at('S01_030', 3.9), 0)]), pan=-0.5)
for k in range(5):
    tk = at('S01_040', 0.3 + k * 0.75)
    mix(bp(noise(), 400, 3000) * env([(tk, 0), (tk + 0.25, 0.08), (tk + 0.7, 0)]), pan=(-1) ** k * 0.6)
mix(tone_burst(at('S01_040', 1.7), 1.0, 2350, 6, (1, 0.4, 0.2), 0.05), pan=0.5)
for k in range(6):
    mix(tone_burst(at('S01_040', 2.0 + k * 0.28), 0.06, 2900, 30, (1,), 0.03), pan=0.7)

# --- the anomaly: shimmer, sub swell, glass hum, alarms, crack
shim = (np.sin(2 * np.pi * 2800 * T) + 0.6 * np.sin(2 * np.pi * 4200 * T)) * (0.6 + 0.4 * np.sin(2 * np.pi * 0.8 * T))
mix(shim * env([(at('S01_050', 1), 0), (at('S01_050', 1.3), 0.006), (at('S01_060', 2), 0.01), (at('S01_070'), 0)]))
sweep_f = np.interp(T, [at('S01_060'), at('S01_070')], [25, 45])
sub = np.sin(2 * np.pi * np.cumsum(sweep_f) / SR) + lp(noise(), 90) * 2
mix(sub * env([(at('S01_060'), 0), (at('S01_060', 5.8), 0.22), (at('S01_070', 1.4), 0.25), (at('S01_080'), 0.06),
               (at('S01_090'), 0.04), (at('S01_130'), 0)]))
hum = sum(np.sin(2 * np.pi * f * T + k) / (k + 1) for k, f in enumerate((120, 241, 362, 484)))
hum *= 1 + 0.5 * np.sin(2 * np.pi * np.interp(T, [at('S01_060'), at('S01_070')], [0.5, 9]) * T)
mix(hum * env([(at('S01_060', 1.5), 0), (at('S01_070', 0.9), 0.08), (at('S01_070', 1.0), 0.02),
               (at('S01_080'), 0)]))
alarm = np.zeros(N, np.float32)
a1 = signal.square(2 * np.pi * np.where((T * 3) % 1 < 0.5, 800, 1000) * T) * 0.5
a2 = np.sin(2 * np.pi * np.cumsum(1050 + 350 * np.sin(2 * np.pi * 0.8 * T)) / SR)
a3 = signal.square(2 * np.pi * 1200 * T) * ((T * 4) % 1 < 0.4) * 0.5
for a, ts, p in ((a1, 3.5, -0.6), (a2, 4.3, 0.5), (a3, 5.1, 0.1)):
    st = at('S01_060', ts)
    alarm += lp(a, 3500) * env([(st, 0), (st + 0.1, 1), (at('S01_080', 0.48), 1), (at('S01_080', 0.5), 0),
                                (at('S01_080', 2.0), 0), (at('S01_080', 2.05), 0.7), (at('S01_130'), 0.4),
                                (at('S01_150'), 0)]) * 0.016
mix(alarm, pan=0.2)
crack = np.zeros(N, np.float32)
i0 = int(at('S01_070', 0.9) * SR)
crack[i0:i0 + 3000] = R.normal(0, 1, 3000) * np.exp(-np.arange(3000) / 300)
mix(hp(crack, 2500) * 0.5)
# freeze: high ringing and her breath
mix(np.sin(2 * np.pi * 6200 * T) * env([(at('S01_080', 0.5), 0), (at('S01_080', 0.7), 0.006),
                                         (at('S01_080', 1.9), 0.006), (at('S01_080', 2.0), 0)]))
mix(bp(noise(), 300, 2000) * env([(at('S01_080', 1.0), 0), (at('S01_080', 1.25), 0.05), (at('S01_080', 1.9), 0)]))

# --- inserts: birds, jet, observatory, heartbeat
flut = bp(noise(), 400, 3200) * (0.5 + 0.5 * np.sign(np.sin(2 * np.pi * 17 * T)))
mix(flut * env([(at('S01_090'), 0), (at('S01_090', 0.1), 0.2), (at('S01_090', 1.3), 0.05), (at('S01_100'), 0)]), pan=0.3)
jf = np.interp(T, [at('S01_100'), at('S01_110')], [1900, 2900])
jet = bp(noise(), 150, 2500) + 0.15 * np.sin(2 * np.pi * np.cumsum(jf) / SR)
mix(jet * env([(at('S01_100'), 0), (at('S01_100', 0.6), 0.12), (at('S01_110', -0.2), 0.08), (at('S01_110'), 0)]), pan=-0.3)
for k in range(4):
    mix(tone_burst(at('S01_110', 0.15 + k * 0.5), 0.12, 1000, 20, (1,), 0.02))
mix(bp(noise(), 2000, 6000) * env([(at('S01_110'), 0), (at('S01_110', 0.3), 0.03), (at('S01_120'), 0)]))
for k in range(8):                                        # heartbeat, 70 bpm, joins the score
    b = at('S01_120', 0.2) + k * 60 / 70
    mix(drum(b, 0.12 + k * 0.02, 70, 42, 9) + drum(b + 0.22, 0.08 + k * 0.015, 70, 42, 9))

# --- the fleet: drones, percussion, Thanos motif on brass, choir
drone = sum(saw(f, d) for f in (55.0, 73.42, 82.41) for d in (-0.006, 0.0, 0.007))
drone = lp(drone, 380)
mix(drone * env([(at('S01_130'), 0), (at('S01_130', 2), 0.035), (at('S01_150'), 0.05), (at('S01_160'), 0.02),
                 (at('S01_170'), 0.06), (at('S01_180', 0.25), 0.09), (at('S01_180', 0.26), 0)]))
whine = np.sin(2 * np.pi * np.cumsum(np.interp(T, [at('S01_130'), at('S01_150')], [300, 900])) / SR)
mix(whine * env([(at('S01_130'), 0), (at('S01_140'), 0.008), (at('S01_150'), 0)]))
beat = 60 / 90
for k in range(int((at('S01_150') - at('S01_130')) / beat)):
    tk = at('S01_130') + k * beat
    mix(drum(tk, 0.25 + 0.03 * k, 140, 50, 5))
    if k % 2:
        mix(drum(tk + beat / 2, 0.12, 200, 90, 9), pan=0.3)
brass = np.zeros(N, np.float32)
for start, dur, f in ((0.0, 1.25, 73.42), (1.25, 1.25, 58.27), (2.5, 1.9, 55.0)):   # D, Bb, A
    s0 = at('S01_140', start)
    e = env([(s0, 0), (s0 + 0.15, 1), (s0 + dur - 0.1, 0.9), (s0 + dur + 0.25, 0)])
    tone = sum(saw(f * m, d) for m in (1, 2) for d in (-0.004, 0.004))
    cutoff = 300 + 900 * e
    brass += lp(tone, 900) * e * (0.5 + 0.5 * e)
mix(brass * 0.09)
ah = np.zeros(N, np.float32)
for f in (146.83, 174.61, 220.0):                       # D minor 'ah'
    for d in (-0.005, 0.005):
        ph = np.cumsum(np.full(N, f * (1 + d))) / SR
        ah += sum(a * np.sin(2 * np.pi * k * ph) for k, a in ((1, 1), (2, 0.6), (3, 0.4), (4, 0.2)))
mix(bp(ah, 200, 1600) * env([(at('S01_140'), 0), (at('S01_140', 1.5), 0.02), (at('S01_150'), 0.012),
                             (at('S01_160'), 0.0)]))
# prow: wind roar under the (captioned) lines, near silence, one held low note
mix(lp(noise(), 500) * env([(at('S01_150'), 0), (at('S01_150', 0.4), 0.18), (at('S01_160'), 0.12),
                            (at('S01_160', 1.4), 0.05), (at('S01_170'), 0.1)]), pan=-0.4)
cello = lp(saw(36.71) + saw(36.71, 0.003), 260)
mix(cello * env([(at('S01_150', 1), 0), (at('S01_150', 2), 0.05), (at('S01_160', 3.4), 0.05), (at('S01_170'), 0)]))

# --- descent: riser, drum roll, then silence on the flash and the delayed boom
riser = bp(noise(), 300, 6000) * env([(at('S01_170'), 0), (at('S01_180', 0.24), 0.25), (at('S01_180', 0.25), 0)])
mix(riser)
rf = np.interp(T, [at('S01_170'), at('S01_180', 0.25)], [110, 220])
mix(lp(sum(saw(rf * m) for m in (1, 1.5, 2)), 1500) * env([(at('S01_170'), 0), (at('S01_180', 0.24), 0.08),
                                                         (at('S01_180', 0.25), 0)]))
k = 0
tk = at('S01_170')
while tk < at('S01_180', 0.25):
    mix(drum(tk, 0.15 + 0.4 * (tk - at('S01_170')) / 1.75, 180, 70, 10), pan=(-1) ** k * 0.2)
    tk += max(0.04, 0.2 - 0.09 * (tk - at('S01_170')))
    k += 1
boom_t = at('S01_180', 0.25 + 14 / 24)
boom = np.zeros(N, np.float32)
i0 = int(boom_t * SR)
n = N - i0
tt = np.arange(n) / SR
boom[i0:] = (np.sin(2 * np.pi * (28 + 60 * np.exp(-tt * 6)) * tt) * 1.0 + R.normal(0, 1, n) * 0.6) * np.exp(-tt * 1.5)
mix(lp(boom, 2500) * 0.9)
fl = int(at('S01_180', 0.25) * SR)
L[fl:i0] *= 0.0
Rr[fl:i0] *= 0.0

# --- reverb send (exponential noise tail), master, fades
ir_n = int(2.6 * SR)
ir = R.normal(0, 1, ir_n) * np.exp(-np.arange(ir_n) / SR * 2.6)
ir /= np.sqrt(np.sum(ir ** 2))
wetL = signal.fftconvolve(L, ir)[:N] * 0.35
wetR = signal.fftconvolve(Rr, ir[::-1].copy())[:N] * 0.35
out = np.stack([L + wetL, Rr + wetR], 1)
out[:int(at('S01_010', 2.5) * SR)] = 0.0                    # true digital silence at the head
out[fl:i0] = 0.0                                            # silence between flash and boom
peak = np.max(np.abs(out))
out = out / peak * 10 ** (-1 / 20)
wavfile.write(sys.argv[1] if len(sys.argv) > 1 else 's01.wav', SR, (out * 32767).astype(np.int16))
print('wrote %.2f s, peak -1 dBFS' % DUR)
