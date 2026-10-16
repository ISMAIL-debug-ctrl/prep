#!/usr/bin/env python3
"""STEP 7 (the arithmetic) - from a dump of the Rough Cut to the Tight plan.

    python3 scripts/tight_plan.py <rough_dump.txt> <tight_dir> [--from-frame F] [--fps 60000/1001]

rough_dump.txt is written by scripts/dump_sequence.jsx: 'track|name|start|end|inPoint|mediaPath' (ticks).
Recorders = clips of audio-only files on the audio tracks (a shoot without recorders falls back to every audio clip).
Nothing before --from-frame is touched (e.g. an intro the editor already trimmed).
Writes tight_dir/layout.json, tight.json (cuts + markers) and plan.json (kept ranges + marker positions in the new sequence).
"""
import os, sys, json, collections
from fractions import Fraction
sys.path.insert(0, os.path.dirname(__file__)); import tight
AUDIO_ONLY = ('.wav', '.mp3', '.m4a', '.aif', '.aiff', '.flac')
TPS = 254016000000

def opt(k, d):
    return sys.argv[sys.argv.index(k) + 1] if k in sys.argv else d

def main():
    dump, out = sys.argv[1], sys.argv[2]; os.makedirs(out, exist_ok=True)
    fps = Fraction(opt('--fps', '60000/1001')); fr = Fraction(TPS) / fps
    rows = [l.split('|') for l in open(dump, encoding='utf-8').read().splitlines() if l]
    aud = [r for r in rows if r[0].startswith('A') and len(r) > 5]
    rec = [r for r in aud if r[5].lower().endswith(AUDIO_ONLY)] or aud
    end = max(int(r[3]) for r in rows); f0 = int(opt('--from-frame', 0)); f1 = int(round(end / fr))
    by = collections.defaultdict(list)
    for r in rec: by[r[5]].append([int(round(int(r[2]) / fr)), int(round(int(r[3]) / fr)), float(int(r[4]) / fr)])
    layout = dict(fps=[fps.numerator, fps.denominator], from_frame=f0, end_frame=f1,
                  mics=[dict(path=p, pieces=sorted(v)) for p, v in by.items()])
    json.dump(layout, open(os.path.join(out, 'layout.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    tight.main(os.path.join(out, 'layout.json'), os.path.join(out, 'tight.json'))
    T = json.load(open(os.path.join(out, 'tight.json'), encoding='utf-8')); cuts = T['cuts']
    keep, prev = [], 0
    for s, e in cuts: keep.append([prev, s]); prev = e
    keep.append([prev, f1]); keep = [k for k in keep if k[1] > k[0]]
    newpos = lambda f: f - sum(min(e, f) - s for s, e in cuts if s < f)
    marks = [dict(frame=newpos(m['frame']), why=m['why']) for m in T['marks']]
    total = sum(b - a for a, b in keep)
    json.dump(dict(keep=keep, marks=marks, total=total, ticks_per_frame=str(int(fr))), open(os.path.join(out, 'plan.json'), 'w', encoding='utf-8'), ensure_ascii=False)
    print(f'{f1} → {total} frames ({float(f1 / fps) / 60:.2f} → {float(total / fps) / 60:.2f} min) · {len(keep)} ranges · {len(marks)} markers')
if __name__ == '__main__': main()
