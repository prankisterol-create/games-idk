"""Automated QC over every animation frame of every sequence (no rendering).

Flags: ground penetration (any foot/hand/head below the ground), limb-length
drift (bones must stay within stretch limits), root teleports, and body
overlap between the two fighters' torsos.
usage: python3 tools/qc_scan.py [--film doom]
"""
import importlib
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from rig import solve  # noqa: E402

MODS = ['seq01', 'seq02', 'seq03', 'seq04']
FILM_MODS = {'furnace': MODS, 'doom': ['dv01', 'dv02', 'dv03', 'dv04']}


def scan(mods=MODS):
    issues = []
    for m in mods:
        seq = importlib.import_module(m).build()
        prev = {}
        for f in range(seq.n):
            Js = {}
            for nm, act in seq.actors.items():
                p = act.track.eval(f)
                J = solve(act.b, p)
                Js[nm] = J
                b = act.b
                low = {'ankle_n': J.ankle_n[1] - b.w_ankle / 2, 'ankle_f': J.ankle_f[1] - b.w_ankle / 2,
                       'toe_n': J.toe_n[1] - b.w_ankle * 0.31, 'toe_f': J.toe_f[1] - b.w_ankle * 0.31,
                       'hand_n': J.hand_n[1] - b.fist_r, 'hand_f': J.hand_f[1] - b.fist_r,
                       'head': J.head[1] - b.head_r}
                for part, y in low.items():
                    if y < -0.035:
                        issues.append((seq.name, f, nm, f'{part} {y * 100:.0f} cm below ground'))
                for a_, b_, L in (('hip_n', 'knee_n', b.thigh), ('knee_n', 'ankle_n', b.shin),
                                  ('hip_f', 'knee_f', b.thigh), ('knee_f', 'ankle_f', b.shin)):
                    d = math.dist(getattr(J, a_), getattr(J, b_))
                    yaw = abs(p.get('yaw', 0))
                    if yaw < 5 and not (0.9 * L <= d <= 1.3 * L):
                        issues.append((seq.name, f, nm, f'{a_}-{b_} length {d / L:.2f}x'))
                shown = any(v0 <= f < v1 for v0, v1 in act.visible)
                fast = any(n_ == nm and f0 <= f < f1 for n_, f0, f1 in getattr(seq, 'fast', ()))
                if shown and not fast and nm in prev and math.dist(prev[nm], J.hip) > 0.6:
                    issues.append((seq.name, f, nm, f'hip moved {math.dist(prev[nm], J.hip):.2f} m in one frame'))
                prev[nm] = J.hip if shown else prev.get(nm, J.hip)
                if not shown:
                    prev.pop(nm, None)
            a, b2 = list(Js.values())
            if math.dist(a.chest, b2.chest) < 0.22 and math.dist(a.hip, b2.hip) < 0.3:
                issues.append((seq.name, f, 'both', 'torsos overlap'))
    return issues


if __name__ == '__main__':
    film = sys.argv[sys.argv.index('--film') + 1] if '--film' in sys.argv else 'furnace'
    iss = scan(FILM_MODS[film])
    for i in iss:
        print(*i)
    print(f'{len(iss)} issues')
