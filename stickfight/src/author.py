"""Authoring helpers used by the sequence scripts."""
from rig import solve, pose as _pose, ground_y

NEAR_FAR = (('an', 'af'), ('en', 'ef'), ('ln', 'lf'), ('kn', 'kf'), ('pn', 'pf'),
            ('san', 'saf'), ('sln', 'slf'), ('hn', 'hf'))


def P(base, x, face=1, dy=0.0, **over):
    """Place a library pose: copy, override any parameter, set x/face."""
    q = dict(base)
    q.update(over)
    q['x'] = x
    q['face'] = face
    q['y'] = (q['y'] if q['y'] is not None else 0.0) + dy
    return q


def swap(p):
    """Exchange near/far limbs (alternate stride of a cycle)."""
    q = dict(p)
    for a, b in NEAR_FAR:
        q[a], q[b] = p[b], p[a]
    return q


def ankle(build, p, side):
    J = solve(build, p)
    return J.ankle_n if side == 'n' else J.ankle_f


def hand(build, p, side):
    J = solve(build, p)
    return J.hand_n if side == 'n' else J.hand_f


def foot_on(build, p, side, foot_x):
    """Shift p so its `side` ankle sits at world x = foot_x."""
    q = dict(p)
    q['x'] += foot_x - ankle(build, p, side)[0]
    return q


def hand_on(build, p, side, hand_x):
    q = dict(p)
    q['x'] += hand_x - hand(build, p, side)[0]
    return q


def mix(p, q, t, **over):
    """In-between drawing: blend two poses (discrete fields from q)."""
    from fx import lerp_pose
    r = lerp_pose(p, q, t)
    r.update(over)
    return r


def head_of(build, p):
    return solve(build, p).head


def breathe(track, f0, f1, base, amp=0.012, period=36, lock='nf', arm=2.0):
    """Subtle idle on 2s: hip rises/falls, shoulders and guard drift."""
    f = f0
    up = True
    while f < f1:
        q = dict(base)
        q['y'] = base['y'] + (amp if up else 0.0)
        q['an'] = base['an'] + (arm if up else 0.0)
        q['af'] = base['af'] + (arm * 0.6 if up else 0.0)
        q['head'] = base['head'] + (-1.5 if up else 0.0)
        track.key(f, q, ease='smooth', lock=lock)
        f += period // 2
        up = not up
    track.on_twos(f0, f1)


def bounce(track, f0, f1, low, high, period=12, lock='nf'):
    """Boxer's bounce between two grounded drawings (on 2s)."""
    f = f0
    i = 0
    while f < f1:
        track.key(f, high if i % 2 else low, ease='smooth', lock=lock)
        f += period // 2
        i += 1
    track.on_twos(f0, f1)


def stance_at(build, base, front_x, rear_x, face=1, frac=0.55, dy=0.0, front='n', **over):
    """Grounded drawing whose feet sit exactly on world x positions."""
    from rig import plant_leg
    q = dict(base)
    q.update(over)
    q['face'] = face
    q['x'] = rear_x + (front_x - rear_x) * frac
    q['y'] = (base['y'] if base['y'] is not None else 0.9) + dy
    rear = 'f' if front == 'n' else 'n'
    q = plant_leg(build, q, front, (front_x, build.w_ankle * 0.5))
    q = plant_leg(build, q, rear, (rear_x, build.w_ankle * 0.5))
    return q


def lifted(build, p, side, x, h=0.12):
    """Put one foot in the air at world (x, h) (a stepping foot)."""
    from rig import plant_leg
    return plant_leg(build, p, side, (x, h))
