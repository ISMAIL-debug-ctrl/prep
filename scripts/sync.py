#!/usr/bin/env python3
"""STEP 3 - sync every recording to the main clip by audio cross-correlation.

    python3 scripts/sync.py <work_dir>          (reads roles.json, writes sync.json)

Rough pass on 4 kHz audio over the whole files, fine pass at 48 kHz, then the offset is measured
again near the start, middle and end. offset = where the recording starts on the main clip's
timeline (negative = it starts before the main clip). Drift is reported, nothing is ever stretched.
"""
import os, sys, numpy as np
from common import audio, load, save
LO, HI, WIN = 4000, 48000, 20.0
NWIN, FRAME_MS = 15, 16.7      # windows per file · one frame at 59.94 fps

def xcorr_lag(ref, x):
    """lag (samples) such that x[i] lines up with ref[i+lag]; plus a z-score for the peak."""
    n = 1 << int(np.ceil(np.log2(len(ref) + len(x))))
    c = np.fft.irfft(np.fft.rfft(ref, n) * np.conj(np.fft.rfft(x, n)), n)
    k = int(np.argmax(c)); peak = c[k]
    z = float((peak - c.mean()) / (c.std() + 1e-12))
    return (k - n if k > n // 2 else k), z

def whiten(a):
    a = np.diff(a, prepend=a[:1]); return a / (a.std() + 1e-9)

def local(main_path, path, t_in_x, coarse):
    """Precise offset for a WIN-second window of x starting at t_in_x (seconds on x's own clock)."""
    x = audio(path, HI, t_in_x, WIN); pad = 1.0
    r0 = t_in_x + coarse - pad
    r = audio(main_path, HI, r0, WIN + 2 * pad)
    if len(x) < HI or len(r) < HI or r0 < 0: return None, 0.0
    lag, z = xcorr_lag(whiten(r), whiten(x))
    return r0 + lag / HI - t_in_x, z

def measure(ref, f, ref_lo=None):
    """Offset of f on ref's clock. Coarse lag over the whole files, then up to NWIN local windows spread
    across f; quiet windows (weak peak) are dropped and the median of the rest is the offset.
    In a room shoot (lavs on people who move, camera mics metres away) the windows legitimately differ by
    the sound's travel time, so 'steady' means the middle half of the windows agree within one video frame."""
    if ref_lo is None: ref_lo = whiten(audio(ref['path'], LO))
    lag, z = xcorr_lag(ref_lo, whiten(audio(f['path'], LO))); coarse = lag / LO
    n = int(min(NWIN, max(3, f['dur'] // WIN))); pts = []
    for k in range(n):
        t = max(0.0, f['dur'] * (k + 0.5) / n - WIN / 2)
        if t + coarse < 1.0: t = 1.0 - coarse + 0.5            # stay inside the reference
        if t + coarse + WIN > ref['dur'] - 1: t = ref['dur'] - 1 - WIN - coarse
        if t < 0 or t + WIN > f['dur']: continue
        o, zz = local(ref['path'], f['path'], t, coarse)
        if o is not None: pts.append(dict(at=round(t, 2), offset=o, z=round(zz, 1)))
    loud = [q for q in pts if q['z'] > 8 and abs(q['offset'] - coarse) < 0.5]
    offs = sorted(q['offset'] for q in loud)
    if len(offs) >= 3:
        spread = (offs[(3 * len(offs)) // 4] - offs[len(offs) // 4]) * 1000   # middle half
        half = len(loud) // 2
        a, b = np.median([q['offset'] for q in loud[:half]]), np.median([q['offset'] for q in loud[-half:]])
        span = (np.mean([q['at'] for q in loud[-half:]]) - np.mean([q['at'] for q in loud[:half]])) / 60
        drift = float((b - a) * 1000 / span) if span > 0.2 else 0.0
    else: spread, drift = None, 0.0
    strong = z > 8 and len(offs) >= 3 and len(offs) >= len(pts) / 3
    steady = spread is not None and spread < FRAME_MS
    ok = bool(strong and steady)
    why = None if ok else ('correlation peak does not stand out - probably not from this shoot' if not strong else 'the windows disagree by more than a frame')
    return dict(offset=float(np.median(offs)) if offs else coarse, coarse=coarse, z=round(z, 1), points=pts, used=len(offs),
                spread_ms=None if spread is None else round(spread, 2), drift_ms_per_min=round(drift, 3),
                drift_flag=abs(drift) > 1.0, ok=ok, why=why)

def main(work):
    roles = load(os.path.join(work, 'roles.json')); files = roles['files']
    m = next(f for f in files if f['main']); ref = whiten(audio(m['path'], LO)); out = []
    for f in files:
        base = dict(path=f['path'], name=f['name'], role=f['role'], dur=f['dur'])
        if f['main']: out.append(dict(base, offset=0.0, ok=True, main=True)); continue
        if not f['audio_streams']: out.append(dict(base, ok=False, why='no audio to sync with')); continue
        out.append(dict(base, **measure(m, f, ref)))
    # a recording that does not overlap the main clip (camera restarted, mic started early) is tried against
    # every recording that did sync, longest first, and its offset is carried over to the main clip's clock
    for o in out:
        if o['ok'] or 'points' not in o: continue
        for g in sorted((x for x in out if x['ok'] and not x.get('via')), key=lambda x: -x['dur']):
            if g['path'] == o['path']: continue
            r = measure(g, o)
            if r['ok']:
                r['offset'] += g['offset']; o.update(r, via=g['name']); break
    good = [o for o in out if o['ok']]
    shift = max(0.0, -min(o['offset'] for o in good))                # nothing may start before 0
    for o in out:
        if o['ok']: o['timeline_start'] = o['offset'] + shift
    save(os.path.join(work, 'sync.json'), dict(main=m['path'], shift=shift, clips=out))
    print(f"{'name':38} {'offset s':>11} {'spread ms':>9} {'drift ms/min':>12} {'z':>6}  status")
    for o in out:
        if o.get('main'): print(f"{o['name'][:38]:38} {'0 (main)':>11}"); continue
        if 'points' not in o: print(f"{o['name'][:38]:38} {'-':>11} {'-':>9} {'-':>12} {'-':>6}  LEFT OFF: {o['why']}"); continue
        st = 'ok' if o['ok'] else 'LEFT OFF: ' + o['why']
        if o['ok'] and o['drift_flag']: st += '  DRIFT over 1 ms/min - told, not stretched'
        if o.get('via'): st += f"  (matched through {o['via']})"
        print(f"{o['name'][:38]:38} {o['offset']:11.4f} {(o['spread_ms'] if o['spread_ms'] is not None else float('nan')):9.2f} {o['drift_ms_per_min']:12.3f} {o['z']:6.1f}  {st}")
    if shift: print(f"everything moves right by {shift:.4f}s so nothing is cut off")
if __name__ == '__main__': main(sys.argv[1])
