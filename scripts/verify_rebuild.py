#!/usr/bin/env python3
"""Proof for a rebuilt sequence: every piece the plan asks for, read back from Premiere, compared in ticks.

    python3 scripts/verify_rebuild.py <source_dump.txt> <target_dump.txt> <plan.json> [--fix fix.json]

Dumps are lines 'track|name|start|end|inPoint' (ticks) written by an ExtendScript. plan.json holds "keep": [[f0, f1], ...]
(source-sequence frames, in order). Prints missing, wrong and extra pieces per track.
"""
import sys, json, collections
src, dst, plan = sys.argv[1:4]; FR = int(json.load(open(plan)).get('ticks_per_frame', 4237833600))
FIX = sys.argv[sys.argv.index('--fix') + 1] if '--fix' in sys.argv else None
def rows(p): return [(l.split('|')[0], l.split('|')[1], *map(int, l.split('|')[2:5])) for l in open(p, encoding='utf-8').read().splitlines() if l]   # extra fields ignored
S, D = rows(src), rows(dst); keep = json.load(open(plan))['keep']
exp = collections.defaultdict(list); pos = 0
for a, b in keep:
    ks, ke = a * FR, b * FR
    for tr, name, s, e, i in S:
        os_, oe = max(ks, s), min(ke, e)
        if oe - os_ < FR: continue
        exp[tr].append((pos + os_ - ks, pos + oe - ks, i + os_ - s, name))
    pos += ke - ks
got = collections.defaultdict(list)
for tr, name, s, e, i in D: got[tr].append((s, e, i, name))
end = max((x[1] for v in got.values() for x in v), default=0)
print(f'built up to frame {end // FR} of {pos // FR}')
for tr in sorted(set(exp) | set(got)):
    E = [x for x in exp[tr] if x[0] < end]; G = set(got[tr]); Es = set(E)
    missing = [x for x in E if x not in G]; extra = [x for x in got[tr] if x not in Es]
    print(f'{tr}: expected {len(E)} · placed {len(got[tr])} · missing/wrong {len(missing)} · extra {len(extra)}')
    for x in (missing[:3] + extra[:3]): print('    ', 'missing' if x in missing else 'extra', [x[0] // FR, x[1] // FR, x[2] / FR, x[3]])

if FIX:                                                     # pieces that sit at the right start but carry a wrong in/end
    at = {(tr, s): (e, i) for tr, name, s, e, i in D}; fix = []
    for tr, L in exp.items():
        if not tr.startswith('A'): continue
        for s, e, i, name in L:
            g = at.get((tr, s))
            if g and g != (e, i): fix.append([int(tr[1:]) - 1, str(s), str(i), str(i + e - s), str(e)])
    json.dump(fix, open(FIX, 'w')); print(len(fix), 'pieces written to', FIX)
