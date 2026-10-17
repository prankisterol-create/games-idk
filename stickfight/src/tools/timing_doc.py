"""Generate docs/04_timing_plan.md tables straight from the sequence tracks.

usage: python3 tools/timing_doc.py ../docs/04_timing_plan.md
"""
import importlib
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from engine import build_frame_map  # noqa: E402

MODS = ['seq01', 'seq02', 'seq03', 'seq04']

HEAD = """# 04 — Timed Animation Plan

*Generated from the animation tracks by `src/tools/timing_doc.py`. Do not hand-edit the tables; edit the sequence scripts and regenerate.*

## Frame-rate decisions

- **Playback:** 24 fps (film standard; the reference is also 24 fps).
- **Drawing rate:** varies by shot type, chosen per range in the scripts:
  - **On 1s (24 drawings/s):** all fast action (sprints, strikes, spins, flips, impacts).
  - **On 2s (12 drawings/s):** idles, breathing, KAI's stalking shuffle, SEN's slow guard raise, lowering the hand, the walk-off. Ranges are listed per sequence below.
- **Camera, FX, hair and headband secondary motion:** always on 1s, even over drawings held on 2s (as observed in the reference close-ups).
- **Hit-stop:** extra render frames inserted *after* a contact drawing. The drawing holds while sparks, rings, shake and hair keep moving. Authored in animation frames, so choreography timing and impact emphasis are edited independently.
- **Spacing curves** (`ease` per key, meaning the spacing *from that key to the next*):

| Curve | Meaning |
|---|---|
| `lin` | Even spacing (constant speed). Used inside sprint cycles and ballistic travel. |
| `acc` | Spacing widens: slow out of the key, arriving fast. Used for anticipations. |
| `dec` | Spacing narrows: explosive departure, cushioned arrival. Used on most extremes. |
| `whip` | Very explosive start, long settle. Used for reactions and evasions. |
| `smooth` | Slow out and slow in. Used for settles and idles. |
| `hold` | Hold the drawing, then pop. Used across cuts. |

Measured per-frame travel of the striking limb for the signature actions is in `output/timing/spacing.txt`, and drawn as spacing charts in `output/timing/timing_*.png`.

"""


def main(out):
    lines = [HEAD]
    total_rf = 0
    for m in MODS:
        seq = importlib.import_module(m).build()
        fmap = build_frame_map(seq.n, seq.hitstops)
        first = {}
        for i, (a, stop) in enumerate(fmap):
            first.setdefault(a, i)
        doc = (importlib.import_module(m).__doc__ or '').strip().splitlines()
        lines.append(f'## {doc[0] if doc else seq.name}\n')
        lines.append(f'- **Length:** {seq.n} animation frames + {sum(seq.hitstops.values())} hit-stop frames = '
                     f'{len(fmap)} rendered frames ({len(fmap) / 24:.2f} s), starting at film time '
                     f'{total_rf / 24:.2f} s.')
        hs = ', '.join(f'{f} (+{n})' for f, n in sorted(seq.hitstops.items()))
        lines.append(f'- **Hit-stops** (anim frame, +extra frames): {hs or "none"}.')
        imp = ', '.join(f'{f} ({"+".join(v[0])})' for f, v in sorted(seq.impacts.items()))
        lines.append(f'- **Impact frames:** {imp or "none"}.')
        cuts = ', '.join(str(f) for f in seq.cam.cuts())
        lines.append(f'- **Camera cuts** at anim frames: {cuts or "none"}.\n')
        for nm, act in seq.actors.items():
            tr = act.track
            twos = ', '.join(f'{a}-{b - 1}' for a, b in tr.twos)
            lines.append(f'### {nm}\n')
            lines.append(f'- **On 2s:** {twos or "none"}.')
            sm = ', '.join(f'{a}-{b - 1} {"+".join(l)}' for a, b, l, s in tr.smears)
            lines.append(f'- **Smear frames:** {sm or "none"}.\n')
            lines.append('| Anim frame | Film time (s) | Drawing | Spacing to next | Locks |')
            lines.append('|---:|---:|---|---|---|')
            for k in tr.keys:
                if not k['label']:
                    continue
                t = (total_rf + first.get(k['f'], 0)) / 24
                e = k['ease'] if isinstance(k['ease'], str) else f"{k['ease'][0]}({k['ease'][1]})"
                locks = ' '.join([f'foot:{s}' for s in k['lock']] + [f'hand:{s}' for s in k['hands']])
                lines.append(f"| {k['f']} | {t:.2f} | {k['label']} | {e} | {locks} |")
            lines.append('')
        total_rf += len(fmap)
    lines.append(f'**Total running time:** {total_rf} frames = {total_rf / 24:.2f} s.\n')
    with open(out, 'w') as fh:
        fh.write('\n'.join(lines))
    print('->', out)


if __name__ == '__main__':
    main(sys.argv[1])
