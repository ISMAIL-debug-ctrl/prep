#!/usr/bin/env python3
"""TIGHT CUT - remove silences for pace (rhythm only, no content decisions). Multi-recorder aware.

    python3 scripts/tight.py <layout.json> <out.json>        (normally called by tight_plan.py)

Defaults chosen on the first real show (2026-10-14): sound = within 18 dB of a recorder's speech level, silences of
0.35 s or more are cut. Override with TIGHT_BELOW_DB / TIGHT_MIN_GAP.

layout.json: {"fps":[60000,1001], "from_frame": F, "end_frame": E,
              "mics": [{"path":..., "pieces": [[start_frame, end_frame, src_in_frame], ...]}, ...]}
Each recorder is measured on its own (10 ms loudness). A frame has sound when ANY recorder is above its own threshold
(speech level - 22 dB, never below its noise floor + 10 dB). A silence is when everyone is quiet.
Silences shorter than MIN_GAP stay. Longer ones are cut, leaving HEAD of air after the sound and TAIL before the next.
Not cut, marked for the editor instead: silences of LONG_GAP or more (likely a bite, an action, a reaction) and silences
right after several people sounded at once (laughter, a joke landing).
"""
import sys, json, subprocess, numpy as np
SR, HOP = 16000, 160                     # 10 ms
import os
MIN_GAP, HEAD, TAIL, LONG_GAP = float(os.environ.get('TIGHT_MIN_GAP', 0.35)), 0.12, 0.10, 2.0
BELOW = float(os.environ.get('TIGHT_BELOW_DB', 18))   # sound = within this many dB of the recorder's speech level
MIN_SOUND, FILL = 0.08, 0.12

def load(path, a, n):                     # n seconds from a (source clock)
    cmd = ['ffmpeg', '-v', 'error', '-ss', f'{a:.4f}', '-t', f'{n:.4f}', '-i', path, '-ac', '1', '-ar', str(SR), '-f', 'f32le', '-']
    return np.frombuffer(subprocess.run(cmd, capture_output=True).stdout, np.float32)

def runs(b):
    d = np.diff(np.r_[0, b.astype(np.int8), 0]); return list(zip(np.where(d == 1)[0], np.where(d == -1)[0]))

def main(lp, op):
    L = json.load(open(lp, encoding='utf-8')); fps = L['fps'][0] / L['fps'][1]; f0, f1 = L['from_frame'], L['end_frame']
    T = int((f1 - f0) / fps * 100) + 1; dbs, own = [], []
    L['mics'] = [m for m in L['mics'] if any(min(e, f1) > max(s, f0) for s, e, _ in m['pieces'])]   # recorders inside the range only
    for m in L['mics']:
        env = np.full(T, -120.0)
        for s, e, i in m['pieces']:
            s2, e2 = max(s, f0), min(e, f1)
            if e2 <= s2: continue
            x = load(m['path'], (i + s2 - s) / fps, (e2 - s2) / fps); n = len(x) // HOP
            db = 10 * np.log10((x[:n * HOP].reshape(n, HOP) ** 2).mean(1) + 1e-12)
            a = int((s2 - f0) / fps * 100); env[a:a + n] = db[:max(0, min(n, T - a))]
        v = env[env > -119]; floor, level = np.percentile(v, 10), np.percentile(v, 95)
        thr = max(floor + 10, level - BELOW); dbs.append(env); own.append(env > thr)
        m['floor'], m['level'], m['thr'] = round(float(floor), 1), round(float(level), 1), round(float(thr), 1)
    loud = np.any(own, axis=0)
    for a, b in runs(loud):                                  # drop clicks
        if b - a < MIN_SOUND * 100: loud[a:b] = False
    for a, b in runs(~loud):                                 # close tiny holes inside a word
        if b - a < FILL * 100 and a > 0 and b < T: loud[a:b] = True
    near = np.sum([d > m['level'] - 12 for d, m in zip(dbs, L['mics'])], axis=0) >= 2   # several people at once
    cuts, marks, kept_long = [], [], 0.0
    for a, b in runs(~loud):
        g = (b - a) / 100
        if g < MIN_GAP or a == 0 or b >= T: continue
        before = near[max(0, a - 80):a].mean() if a > 0 else 0
        t0 = f0 + a / 100 * fps
        if g >= LONG_GAP:
            marks.append(dict(frame=int(round(t0)), dur=round(g, 2), why=f'silence {g:.1f}s - an action, a bite, a reaction? left uncut'))
            kept_long += g; continue
        if before > 0.35 and g >= 0.8:
            marks.append(dict(frame=int(round(t0)), dur=round(g, 2), why=f'silence {g:.1f}s after laughter or crosstalk - left uncut'))
            continue
        s = int(np.ceil(f0 + (a / 100 + HEAD) * fps)); e = int(np.floor(f0 + (b / 100 - TAIL) * fps))
        if e - s >= 3: cuts.append([s, e])
    removed = sum(e - s for s, e in cuts) / fps
    json.dump(dict(cuts=cuts, marks=marks, removed_s=round(removed, 1), mics=[{k: m[k] for k in ('path', 'floor', 'level', 'thr')} for m in L['mics']],
                   params=dict(MIN_GAP=MIN_GAP, HEAD=HEAD, TAIL=TAIL, LONG_GAP=LONG_GAP)), open(op, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(f'{len(cuts)} cuts · {removed:.0f} s removed · {len(marks)} markers · long silences kept {kept_long:.0f} s')
    for m in L['mics']: print('  ', os.path.basename(m['path']), 'floor', m['floor'], 'speech', m['level'], 'threshold', m['thr'])
if __name__ == '__main__': main(sys.argv[1], sys.argv[2])

