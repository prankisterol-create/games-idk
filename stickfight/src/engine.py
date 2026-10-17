"""Timeline engine: keyframe tracks, spacing, locks, overlap, hit-stop, camera.

Animation is authored in *animation frames* (24 fps). Hit-stops insert extra
*render frames* in which character drawings freeze while FX, hair and camera
shake keep running, so the action timing stays editable independently of the
impact emphasis.
"""
import math
import random

from rig import solve, plant_leg, plant_hand, ankle_pos, hand_pos, DISCRETE, hair_anchor

FPS = 24

# ----------------------------------------------------------------- spacing
def ease(u, kind):
    """Spacing curves. Named for what the spacing does between two keys."""
    if isinstance(kind, tuple):
        kind, k = kind
    else:
        k = None
    u = max(0.0, min(1.0, u))
    if kind == 'lin':
        return u
    if kind == 'smooth':            # slow out of A, slow into B
        return u * u * (3 - 2 * u)
    if kind == 'acc':               # spacing widens: slow out of A, arrive fast
        return u ** (k or 2.0)
    if kind == 'dec':               # spacing narrows: leave fast, cushion into B
        return 1 - (1 - u) ** (k or 2.0)
    if kind == 'snap':              # late explosive burst
        return u ** (k or 4.0)
    if kind == 'whip':              # explosive start, long settle
        return 1 - (1 - u) ** (k or 4.0)
    if kind == 'hold':              # stepped key: hold A, pop to B
        return 1.0 if u >= 1.0 else 0.0
    raise ValueError(kind)


GROUPS = {
    'arms': ('an', 'en', 'af', 'ef', 'san', 'saf'),
    'arm_n': ('an', 'en', 'san'),
    'arm_f': ('af', 'ef', 'saf'),
    'head': ('head',),
    'legs': ('ln', 'kn', 'lf', 'kf', 'sln', 'slf', 'pn', 'pf'),
    'torso': ('lean', 'bend'),
}


def lerp(a, b, t):
    return a + (b - a) * t


class Track:
    """Pose keyframes for one character."""

    def __init__(self, build, name=None):
        self.b = build
        self.name = name or build.name
        self.keys = []
        self.lags = []
        self.twos = []
        self.smears = []
        self._prepared = False

    def key(self, f, p, ease='smooth', lock=(), hands=(), jump=None, xease=None, label=None):
        """Add a key drawing at animation frame f.

        ease   spacing from this key to the next
        lock   feet ('n', 'f') pinned to the ground from this key while the next key also pins them
        hands  same for hands ('n', 'f')
        jump   apex height (m) of a ballistic arc to the next key (x linear, y parabolic)
        xease  separate spacing for travel (x) when it should differ from the drawing spacing
        """
        self.keys.append(dict(f=f, p=dict(p), ease=ease, lock=tuple(lock), hands=tuple(hands),
                              jump=jump, xease=xease, label=label))
        self._prepared = False
        return self

    def lag(self, f0, f1, group, frames):
        self.lags.append((f0, f1, GROUPS[group], frames))
        return self

    def on_twos(self, f0, f1):
        self.twos.append((f0, f1))
        return self

    def smear(self, f0, f1, limbs, strength=1.0):
        self.smears.append((f0, f1, tuple(limbs), strength))
        return self

    # ------------------------------------------------------------------
    def prepare(self):
        self.keys.sort(key=lambda k: k['f'])
        b = self.b
        # pins: a run of consecutive keys that lock a foot shares the first key's ankle position
        for side in ('n', 'f'):
            pin = None
            for k in self.keys:
                if side in k['lock']:
                    if pin is None:
                        pin = ankle_pos(b, k['p'], side)
                        pin = (pin[0], b.w_ankle * 0.5)
                    k['p'] = plant_leg(b, k['p'], side, pin)
                    k.setdefault('pins', {})[side] = pin
                else:
                    pin = None
        for side in ('n', 'f'):
            pin = None
            for k in self.keys:
                if side in k['hands']:
                    if pin is None:
                        pin = hand_pos(b, k['p'], side)
                        pin = (pin[0], b.fist_r * 0.55)
                    k['p'] = plant_hand(b, k['p'], side, pin)
                    k.setdefault('hpins', {})[side] = pin
                else:
                    pin = None
        self._prepared = True

    def _seg(self, f):
        ks = self.keys
        if f <= ks[0]['f']:
            return 0, 0.0
        for i in range(len(ks) - 1):
            if ks[i]['f'] <= f < ks[i + 1]['f']:
                return i, (f - ks[i]['f']) / (ks[i + 1]['f'] - ks[i]['f'])
        return len(ks) - 1, 0.0

    def _raw(self, f):
        if not self._prepared:
            self.prepare()
        i, u = self._seg(f)
        ks = self.keys
        A = ks[i]
        if i == len(ks) - 1 or u == 0.0:
            p = dict(A['p'])
            p = self._apply_pins(p, A, ks[i + 1] if i + 1 < len(ks) else None)
            return p
        B = ks[i + 1]
        e = ease(u, A['ease'])
        pa, pb = A['p'], B['p']
        p = {}
        for k, va in pa.items():
            vb = pb.get(k, va)
            if k in DISCRETE or not isinstance(va, (int, float)) or va is None or vb is None:
                p[k] = va if e < 1.0 else vb
            else:
                p[k] = lerp(va, vb, e)
        if A['xease'] is not None:
            ex = ease(u, A['xease'])
            p['x'] = lerp(pa['x'], pb['x'], ex)
            p['y'] = lerp(pa['y'], pb['y'], ex)
        if A['jump'] is not None:
            p['x'] = lerp(pa['x'], pb['x'], u)
            p['y'] = lerp(pa['y'], pb['y'], u) + 4.0 * A['jump'] * u * (1 - u)
        return self._apply_pins(p, A, B)

    def _apply_pins(self, p, A, B):
        b = self.b
        for side, pin in A.get('pins', {}).items():
            if B is None or side in B.get('pins', {}):
                p = plant_leg(b, p, side, pin)
        for side, pin in A.get('hpins', {}).items():
            if B is None or side in B.get('hpins', {}):
                p = plant_hand(b, p, side, pin)
        return p

    def sample_frame(self, f):
        """Drawing frame actually shown at animation frame f (handles 'on twos')."""
        for f0, f1 in self.twos:
            if f0 <= f < f1:
                return f0 + 2 * ((f - f0) // 2)
        return f

    def eval(self, f):
        f = self.sample_frame(f)
        p = self._raw(f)
        for f0, f1, params, lag in self.lags:
            if f0 <= f < f1:
                q = self._raw(f - lag)
                for k in params:
                    p[k] = q[k]
        return p

    def smear_at(self, f):
        out = []
        for f0, f1, limbs, s in self.smears:
            if f0 <= f < f1:
                out.append((limbs, s))
        return out

    @property
    def end(self):
        return self.keys[-1]['f']


class CamTrack:
    """Camera keys: cx, cy (world centre), h (view height in m), rot (deg),
    fw (follow weight toward the fighters' smoothed midpoint), ox (offset)."""

    DEF = dict(cx=0.0, cy=1.0, h=4.6, rot=0.0, fw=0.0, ox=0.0, oy=0.0)

    def __init__(self):
        self.keys = []

    def key(self, f, ease='smooth', cut=False, **kw):
        prev = dict(self.keys[-1]['v']) if self.keys and not cut else dict(self.DEF)
        if self.keys and cut:
            prev = dict(self.DEF)
        prev.update(kw)
        self.keys.append(dict(f=f, v=prev, ease=ease, cut=cut))
        self.keys.sort(key=lambda k: k['f'])
        return self

    def eval(self, f):
        ks = self.keys
        if f <= ks[0]['f']:
            return dict(ks[0]['v'])
        for i in range(len(ks) - 1):
            A, B = ks[i], ks[i + 1]
            if A['f'] <= f < B['f']:
                if B['cut']:
                    return dict(A['v'])
                u = (f - A['f']) / (B['f'] - A['f'])
                e = ease(u, A['ease'])
                return {k: lerp(A['v'][k], B['v'][k], e) for k in A['v']}
        return dict(ks[-1]['v'])

    def cuts(self):
        return [k['f'] for k in self.keys if k['cut']]


# ----------------------------------------------------------- secondary
class Chain:
    """Verlet rope for hair / headband tails. Runs on 1s at all times."""

    def __init__(self, n, seg, gravity=1.0, drag=0.86, trail=0.6, stiff=0.0):
        self.n, self.seg = n, seg
        self.g, self.drag, self.trail, self.stiff = gravity, drag, trail, stiff
        self.p = None
        self.q = None

    def reset(self, anchor, face):
        self.p = [(anchor[0] - face * self.seg * i, anchor[1] - 0.02 * i) for i in range(self.n)]
        self.q = list(self.p)

    def step(self, anchor, face, wind=0.0, dt=1.0 / FPS, sub=4):
        if self.p is None or math.dist(anchor, self.p[0]) > 0.6:
            self.reset(anchor, face)
        h = dt / sub
        a0 = self.p[0]
        for s in range(sub):
            t = (s + 1) / sub
            anc = (lerp(a0[0], anchor[0], t), lerp(a0[1], anchor[1], t))
            newp = [anc]
            for i in range(1, self.n):
                x, y = self.p[i]
                px, py = self.q[i]
                vx, vy = (x - px) * self.drag ** (1 / sub), (y - py) * self.drag ** (1 / sub)
                ax = wind - face * self.trail
                ay = -9.8 * self.g
                newp.append((x + vx + ax * h * h, y + vy + ay * h * h))
            self.q = list(self.p)
            self.q[0] = anc
            for _ in range(3):
                for i in range(1, self.n):
                    x0, y0 = newp[i - 1]
                    x1, y1 = newp[i]
                    d = math.hypot(x1 - x0, y1 - y0) or 1e-6
                    k = (d - self.seg) / d
                    if i == 1:
                        newp[i] = (x1 - (x1 - x0) * k, y1 - (y1 - y0) * k)
                    else:
                        newp[i - 1] = (x0 + (x1 - x0) * k * 0.5, y0 + (y1 - y0) * k * 0.5)
                        newp[i] = (x1 - (x1 - x0) * k * 0.5, y1 - (y1 - y0) * k * 0.5)
                    newp[0] = anc
            newp = [(x, max(y, 0.01)) for x, y in newp]
            self.p = newp
        return list(self.p)


def chains_for_build(build):
    if build.trait == 'headband':
        return [(Chain(7, 0.05, gravity=0.55, drag=0.84, trail=2.2), 0.05, 0.024, build.accent),
                (Chain(6, 0.048, gravity=0.7, drag=0.82, trail=1.6), 0.045, 0.02, build.accent)]
    return [(Chain(9, 0.055, gravity=0.9, drag=0.86, trail=1.2), 0.075, 0.014, build.far)]


# ----------------------------------------------------------- hit-stop map
def build_frame_map(n_anim, hitstops):
    """Return [(anim_frame, is_stop)] for every render frame."""
    hs = dict(hitstops)
    out = []
    for a in range(n_anim):
        out.append((a, False))
        for _ in range(hs.get(a, 0)):
            out.append((a, True))
    return out


class Shake:
    def __init__(self):
        self.ev = []

    def add(self, rf, amp, frames=8, dx=0.0, dy=1.0, seed=0):
        self.ev.append((rf, amp, frames, dx, dy, seed))

    def at(self, rf):
        sx = sy = 0.0
        for r0, amp, n, dx, dy, seed in self.ev:
            k = rf - r0
            if 0 <= k < n:
                decay = (1 - k / n) ** 2
                rnd = random.Random(seed * 1000 + k)
                sign = 1 if k % 2 == 0 else -1
                sx += amp * decay * (sign * dx * 0.8 + rnd.uniform(-0.4, 0.4))
                sy += amp * decay * (sign * dy * 0.8 + rnd.uniform(-0.4, 0.4))
        return sx, sy
