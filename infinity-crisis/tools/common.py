"""Shared loaders for the Infinity Crisis production data.

Everything downstream (storyboard docs, edit decision list, video prompts, QC, the
Sequence 1 prototype) reads the same YAML through these helpers, so the deliverables
cannot drift apart.
"""
import copy
import glob
import os
import re

import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'data')
DOCS = os.path.join(ROOT, 'docs')
OUTPUT = os.path.join(ROOT, 'output')
FPS = 24
FILM_START_TC = 1 * 3600 * FPS  # 01:00:00:00, the usual picture start

SHOT_FIELDS = [  # the 13 fields the brief requires for every shot, in its order
    ('id', 'Shot number'),
    ('dur', 'Duration'),
    ('camera', 'Camera position'),
    ('lens', 'Lens / field of view'),
    ('movement', 'Camera movement'),
    ('framing', 'Subject framing'),
    ('action', 'Character action'),
    ('lighting', 'Lighting'),
    ('environment', 'Environmental motion'),
    ('vfx', 'Visual effects'),
    ('sound', 'Sound effects'),
    ('dialogue', 'Dialogue'),
    ('transition', 'Transition'),
]

STATE_FIELDS = ['look', 'damage', 'equipment', 'injury', 'objective', 'power',
                'emotion', 'knowledge', 'status']


def load_yaml(path):
    with open(path) as f:
        return yaml.safe_load(f)


def load_sequences():
    seqs = []
    for path in sorted(glob.glob(os.path.join(DATA, 'shots', 's*.yaml'))):
        seqs.append(load_yaml(path))
    seqs.sort(key=lambda s: s['sequence'])
    return seqs


def load_bible():
    return load_yaml(os.path.join(DATA, 'characters.yaml'))


def load_continuity():
    return load_yaml(os.path.join(DATA, 'continuity.yaml'))


def load_locations():
    return load_yaml(os.path.join(DATA, 'locations.yaml'))


def frames(seconds):
    return int(round(seconds * FPS))


def timecode(frame):
    f = frame % FPS
    s = frame // FPS
    return '%02d:%02d:%02d:%02d' % (s // 3600, (s // 60) % 60, s % 60, f)


def short_tc(frame):
    """mm:ss:ff for durations and sequence-relative positions."""
    s = frame // FPS
    return '%02d:%02d:%02d' % (s // 60, s % 60, frame % FPS)


def timeline(seqs):
    """Attach frame-accurate positions: seq_in/seq_out (sequence-relative) and rec_in/rec_out
    (film-relative, starting at 0). Returns the total frame count."""
    rec = 0
    for seq in seqs:
        pos = 0
        seq['rec_in'] = rec
        for shot in seq['shots']:
            n = frames(shot['dur'])
            shot['frames'] = n
            shot['seq_in'], shot['seq_out'] = pos, pos + n
            shot['rec_in'], shot['rec_out'] = rec, rec + n
            pos += n
            rec += n
        seq['frames'] = pos
        seq['rec_out'] = rec
    return rec


def roster(bible):
    """All valid character / extra / force IDs."""
    ids = set(bible['characters'])
    ids |= set(bible.get('extras', {}))
    ids |= set(bible.get('forces', {}))
    return ids


def speaker_id(who, bible):
    """Map a dialogue speaker (ID or screenplay cue) to a character ID."""
    chars = bible['characters']
    if who in chars:
        return who
    for cid, c in chars.items():
        if c.get('cue') == who:
            return cid
    return None


AS_REF = re.compile(r'^As S(\d+)\b\.?\s*(.*)$')


def resolve_look(continuity, cid, look, depth=0):
    """Expand shorthand like 'As S7 (mask down).' into the full description it refers to, so
    every state (and every video prompt built from it) stands on its own."""
    m = AS_REF.match(look or '')
    if not m or depth > 10:
        return look
    ref = (continuity['sequences'].get(int(m.group(1))) or {}).get(cid, {})
    full = resolve_look(continuity, cid, ref.get('look', ''), depth + 1)
    extra = m.group(2).strip()
    return (full + ' ' + extra).strip() if extra else full


def shot_states(seqs, continuity):
    """Yield (seq, shot, state) where state maps character ID to its continuity state as
    seen during the shot. Events take effect after their shot."""
    events = continuity.get('events', {}) or {}
    for seq in seqs:
        base = continuity['sequences'].get(seq['sequence'], {}) or {}
        state = {cid: dict(v, status=v.get('status', 'present'),
                           look=resolve_look(continuity, cid, v.get('look', '')))
                 for cid, v in base.items()}
        for shot in seq['shots']:
            yield seq, shot, copy.deepcopy(state)
            for cid, change in (events.get(shot['id']) or {}).items():
                state.setdefault(cid, {}).update(change)


# ---------------------------------------------------------------- Fountain screenplay

SCENE_NUM = re.compile(r'\s*#([\w.\-]+)#\s*$')
HEADING = re.compile(r'^(INT|EXT|EST|INT\./EXT|I/E)[ .]', re.I)


def parse_fountain(path):
    """Minimal Fountain parser: returns a list of elements (type, text, extra) covering the
    title page, scene headings (with numbers), sections, action, character cues, dialogue,
    parentheticals, transitions and centred text."""
    with open(path) as f:
        lines = f.read().split('\n')
    elements = []
    title = {}
    i = 0
    # title page: key: value lines until the first blank line
    key = None
    while i < len(lines) and lines[i].strip():
        m = re.match(r'^([A-Za-z ]+):\s*(.*)$', lines[i])
        if m and not lines[i].startswith(' '):
            key = m.group(1).strip()
            title[key] = [m.group(2)] if m.group(2) else []
        elif key:
            title[key].append(lines[i].strip())
        i += 1
    n = len(lines)
    while i < n:
        line = lines[i]
        s = line.strip()
        if not s:
            i += 1
            continue
        prev_blank = i == 0 or not lines[i - 1].strip()
        nxt = lines[i + 1].strip() if i + 1 < n else ''
        if s.startswith('#'):
            elements.append(('section', s.lstrip('#').strip(), None))
        elif s.startswith('>') and s.endswith('<'):
            elements.append(('centered', s[1:-1].strip(), None))
        elif s.startswith('>'):
            elements.append(('transition', s[1:].strip(), None))
        elif (s.startswith('.') and not s.startswith('..')) or (HEADING.match(s) and prev_blank):
            text = s[1:] if s.startswith('.') else s
            m = SCENE_NUM.search(text)
            num = m.group(1) if m else None
            if m:
                text = text[:m.start()].rstrip()
            elements.append(('heading', text, num))
        elif s.isupper() and s.endswith('TO:') and prev_blank:
            elements.append(('transition', s, None))
        elif (prev_blank and nxt and s == s.upper() and any(c.isalpha() for c in s)
              and not s.startswith('!')):
            cue = re.sub(r'\s*\(.*?\)\s*', ' ', s).strip()
            ext = ' '.join(re.findall(r'\(.*?\)', s))
            elements.append(('character', cue, ext))
            i += 1
            while i < n and lines[i].strip():
                t = lines[i].strip()
                if t.startswith('(') and t.endswith(')'):
                    elements.append(('parenthetical', t, cue))
                else:
                    elements.append(('dialogue', t, cue))
                i += 1
            continue
        else:
            # action paragraph (keep line breaks)
            para = [line.rstrip()]
            i += 1
            while i < n and lines[i].strip():
                para.append(lines[i].rstrip())
                i += 1
            elements.append(('action', '\n'.join(para), None))
            continue
        i += 1
    return title, elements


def dialogue_segments(elements):
    """Dialogue as (cue, text, scene_number) segments; a parenthetical splits a speech."""
    segs = []
    scene = None
    cur = None
    for kind, text, extra in elements:
        if kind == 'heading':
            scene = extra or scene
            cur = None
        elif kind == 'character':
            cur = None
        elif kind == 'dialogue':
            if cur is None:
                cur = [extra, text, scene]
                segs.append(cur)
            else:
                cur[1] += ' ' + text
        elif kind == 'parenthetical':
            cur = None
        else:
            cur = None
    return [tuple(s) for s in segs]


def norm(text):
    text = text.replace('’', "'").replace('‘', "'").replace('“', '"').replace('”', '"')
    return re.sub(r'\s+', ' ', text).strip()
