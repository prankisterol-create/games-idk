"""Automated QC for the shot list, continuity sheet and screenplay.

    python3 tools/qc_shots.py          # prints every issue, exits 1 if any

Checks:
  1. Every shot has all 13 fields from the brief, a unique ordered ID and a frame-accurate
     duration (whole frames at 24 fps).
  2. Every character, extra and force in a shot exists in the design bible; every location
     is declared by its sequence and described in locations.yaml.
  3. Continuity: characters only appear in locations on their path, visited in order (no
     teleporting between cuts, no character in two zones of a cross-cut); nobody appears
     after leaving; damage never decreases within or across sequences.
  4. Dialogue: every line in the shot list appears verbatim in the screenplay under the
     right character, in the same order, and vice versa; speakers are in their shots.
  5. Scenes: every screenplay scene number is covered by at least one shot and every shot
     points at a real scene.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C  # noqa: E402


def main():
    seqs = C.load_sequences()
    bible = C.load_bible()
    cont = C.load_continuity()
    locs = C.load_locations()
    total = C.timeline(seqs)
    ids = C.roster(bible)
    issues = []

    def bad(where, msg):
        issues.append('%s: %s' % (where, msg))

    # 1-2. schema, roster, locations
    seen = set()
    for seq in seqs:
        n = seq['sequence']
        prefix = 'S%02d_' % n
        last = ''
        for shot in seq['shots']:
            sid = shot.get('id', '?')
            for key, label in C.SHOT_FIELDS:
                if key not in shot:
                    bad(sid, 'missing field %r (%s)' % (key, label))
                elif key != 'dialogue' and (shot[key] is None or str(shot[key]).strip() == ''):
                    bad(sid, 'empty field %r (%s)' % (key, label))
            if not sid.startswith(prefix):
                bad(sid, 'ID does not match sequence %d' % n)
            if sid in seen:
                bad(sid, 'duplicate ID')
            if sid <= last:
                bad(sid, 'IDs out of order (after %s)' % last)
            seen.add(sid)
            last = sid
            if abs(shot['dur'] * C.FPS - round(shot['dur'] * C.FPS)) > 1e-6:
                bad(sid, 'duration %.3f s is not a whole number of frames' % shot['dur'])
            for who in (shot.get('characters') or []) + (shot.get('background') or []):
                if who not in ids:
                    bad(sid, 'unknown character/extra/force %s' % who)
            loc = shot.get('location')
            if loc not in (seq.get('locations') or []):
                bad(sid, 'location %s not declared by sequence %d' % (loc, n))
            if loc not in locs:
                bad(sid, 'location %s has no description in locations.yaml' % loc)
            for d in shot.get('dialogue') or []:
                if not isinstance(d, dict) or 'who' not in d or 'line' not in d:
                    bad(sid, 'malformed dialogue entry %r' % (d,))

    # 3. continuity
    principals = set(bible['characters'])
    pointer = {}
    last_damage = {}
    prev_seq = None
    final_damage = {}
    for seq, shot, state in C.shot_states(seqs, cont):
        n = seq['sequence']
        if n != prev_seq:
            # new sequence: baseline damage must not be lower than the previous final damage
            for cid, st in (cont['sequences'].get(n) or {}).items():
                if cid in final_damage and st.get('damage', 0) < final_damage[cid][0]:
                    bad('S%02d %s' % (n, cid), 'damage drops from %d (end of S%02d) to %d'
                        % (final_damage[cid][0], final_damage[cid][1], st.get('damage', 0)))
            pointer = {}
            prev_seq = n
        for cid in shot.get('characters') or []:
            if cid not in principals:
                continue
            st = state.get(cid)
            if st is None:
                bad(shot['id'], '%s appears but has no continuity state in S%02d' % (cid, n))
                continue
            if st.get('status') in ('gone', 'unknown'):
                bad(shot['id'], '%s appears after leaving (status %s)' % (cid, st['status']))
            path = st.get('path') or []
            p = pointer.get(cid, 0)
            try:
                j = path.index(shot['location'], p)
            except ValueError:
                bad(shot['id'], '%s at %s, which is not on their path %s after %s'
                    % (cid, shot['location'], path, path[p] if p < len(path) else 'end'))
                continue
            pointer[cid] = j
        for cid, st in state.items():
            dmg = st.get('damage', 0)
            if cid in last_damage and last_damage[cid][1] == n and dmg < last_damage[cid][0]:
                bad(shot['id'], '%s damage decreases' % cid)
            last_damage[cid] = (dmg, n)
        # remember state after this shot's events for the next sequence's comparison
        after = dict((cid, dict(v)) for cid, v in state.items())
        for cid, change in ((cont.get('events') or {}).get(shot['id']) or {}).items():
            after.setdefault(cid, {}).update(change)
        for cid, st in after.items():
            final_damage[cid] = (st.get('damage', 0), n)

    for sid in (cont.get('events') or {}):
        if sid not in seen:
            bad('continuity', 'event for unknown shot %s' % sid)
        for cid, change in cont['events'][sid].items():
            for k in change:
                if k not in C.STATE_FIELDS:
                    bad('continuity', '%s %s: unknown state field %r' % (sid, cid, k))

    # 4-5. screenplay
    title, elements = C.parse_fountain(os.path.join(C.DOCS, 'B_screenplay.fountain'))
    script = C.dialogue_segments(elements)
    shot_lines = []
    for seq in seqs:
        for shot in seq['shots']:
            for d in shot.get('dialogue') or []:
                shot_lines.append((shot, d))
    cue_of = {cid: c.get('cue', cid) for cid, c in bible['characters'].items()}
    if len(script) != len(shot_lines):
        bad('dialogue', '%d screenplay segments vs %d shot lines' % (len(script), len(shot_lines)))
    for k in range(min(len(script), len(shot_lines))):
        cue, text, scene = script[k]
        shot, d = shot_lines[k]
        cid = C.speaker_id(d['who'], bible)
        if cid is None:
            bad(shot['id'], 'unknown speaker %s' % d['who'])
            continue
        if cue_of[cid] != cue:
            bad(shot['id'], 'line %d speaker %s, screenplay has %s' % (k + 1, cue_of[cid], cue))
        if C.norm(text) != C.norm(d['line']):
            bad(shot['id'], 'line differs from screenplay:\n      shot  : %s\n      script: %s'
                % (d['line'], text))
        if scene and str(shot['scene']) != scene:
            bad(shot['id'], 'line %r is in screenplay scene %s but shot scene is %s'
                % (d['line'][:30], scene, shot['scene']))
        present = set(shot.get('characters') or [])
        if cid == 'RING':
            cid = 'GL'
        if cid not in present:
            bad(shot['id'], 'speaker %s is not in the shot' % cid)
    scenes = [extra for kind, text, extra in elements if kind == 'heading' and extra]
    shot_scenes = set(str(s['scene']) for seq in seqs for s in seq['shots'])
    for sc in scenes:
        if sc not in shot_scenes:
            bad('screenplay', 'scene %s has no shots' % sc)
    for sc in shot_scenes - set(scenes):
        bad('shots', 'scene %s does not exist in the screenplay' % sc)

    # report
    n_shots = sum(len(s['shots']) for s in seqs)
    print('Sequences: %d   Shots: %d   Runtime: %s (%d frames at %d fps)   Screenplay lines: %d'
          % (len(seqs), n_shots, C.short_tc(total), total, C.FPS, len(script)))
    for seq in seqs:
        flag = '' if abs(seq['frames'] / C.FPS - seq['target']) < 0.01 else '  (target %.1f s)' % seq['target']
        print('  S%02d %-48s %3d shots  %s%s' % (seq['sequence'], seq['title'], len(seq['shots']),
                                              C.short_tc(seq['frames']), flag))
    if issues:
        print('\n%d issue(s):' % len(issues))
        for i in issues:
            print('  - ' + i)
        return 1
    print('\n0 issues.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
