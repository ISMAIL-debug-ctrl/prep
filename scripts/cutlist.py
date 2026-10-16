#!/usr/bin/env python3
"""STEP 6 (the arithmetic) - turn decisions into frame-accurate cut ranges for every track.

    python3 scripts/cutlist.py <work_dir>        (reads phrases.json, roles.json, decisions.json -> cuts.json)

decisions.json is written by the editor (Claude) AFTER reading the whole phrase list:
    {"remove": [{"phrases": [1, 2], "why": "setup before the first complete opening line", "kind": "setup"},
                {"phrases": [14],   "why": "abandoned, said again in 15", "kind": "retake"}],
     "unsure_kept": [{"phrases": [22], "why": "two complete versions - fine cut decides"}]}
kind: setup | end | retake | bad_take | not_to_viewer | noise

Only whole phrases are removed. 0.5 s of air stays before and after every kept phrase. Pauses of 2 s or more
between kept phrases are closed down to that air (screen recordings: check the picture first, list the pause
under "keep_pauses" to protect it). Every cut lands on a whole frame, rounded so that MORE is kept.
"""
import os, sys, math
from fractions import Fraction
from common import load, save, TICKS
AIR, LONG_PAUSE = 0.5, 2.0

def main(work):
    P = load(os.path.join(work, 'phrases.json')); ph = P['phrases']
    roles = load(os.path.join(work, 'roles.json')); sync = load(os.path.join(work, 'sync.json'))
    D = load(os.path.join(work, 'decisions.json'))
    m = next(f for f in roles['files'] if f['main']); fps = Fraction(*m.get('fps', [30, 1]))
    end = max(c['timeline_start'] + c['dur'] for c in sync['clips'] if c['ok'])
    why = {}
    for r in D.get('remove', []):
        for n in r['phrases']: why[n] = r
    keep_pause = set(D.get('keep_pauses', []))                 # phrase numbers whose following pause must stay
    kept = [p for p in ph if p['n'] not in why]
    if not kept: sys.exit('nothing kept - refusing')
    raw = [(0.0, kept[0]['start'] - AIR, 'head')]
    for a, b in zip(kept, kept[1:]):
        between = [p for p in ph if a['n'] < p['n'] < b['n']]
        gap = b['start'] - a['end']
        if between: raw.append((a['end'] + AIR, b['start'] - AIR, 'removed ' + ','.join(str(p['n']) for p in between)))
        elif gap >= LONG_PAUSE and a['n'] not in keep_pause: raw.append((a['end'] + AIR, b['start'] - AIR, f'pause {gap:.1f}s'))
    raw.append((kept[-1]['end'] + AIR, end, 'tail'))
    cuts = []
    for s, e, label in raw:
        fs, fe = math.ceil(Fraction(s).limit_denominator(100000) * fps), math.floor(Fraction(e).limit_denominator(100000) * fps)
        if label == 'head': fs = 0
        if label == 'tail': fe = math.ceil(Fraction(end).limit_denominator(100000) * fps)
        if fe - fs < 1: continue
        tpf = Fraction(TICKS) / fps
        cuts.append(dict(label=label, start_frame=fs, end_frame=fe, start=float(fs / fps), end=float(fe / fps),
                         start_ticks=str(int(fs * tpf)), end_ticks=str(int(fe * tpf)), dur=float((fe - fs) / fps)))
    body = [p for p in ph if why.get(p['n'], {}).get('kind') not in ('setup', 'end')]
    said = sum(p['dur'] for p in body); gone = sum(p['dur'] for p in body if p['n'] in why)
    share = gone / said if said else 0
    removed = sum(c['dur'] for c in cuts)
    save(os.path.join(work, 'cuts.json'), dict(fps=[fps.numerator, fps.denominator], ticks_per_second=str(TICKS), before=end,
         after=end - removed, removed=removed, speech_removed_share=round(share, 3), too_much=share > 0.2, cuts=cuts,
         removals=[dict(phrases=r['phrases'], why=r['why'], kind=r.get('kind'), words=' / '.join(p['text'] for p in ph if p['n'] in r['phrases']))
                   for r in D.get('remove', [])], unsure_kept=D.get('unsure_kept', [])))
    print(f"before {end:.1f}s · after {end-removed:.1f}s · {len(cuts)} cuts · speech removed (excl. setup/end) {share:.0%}"
          + ('   ⚠ MORE THAN A FIFTH - cutting too much, re-read the decisions' if share > 0.2 else ''))
if __name__ == '__main__': main(sys.argv[1])
