#!/usr/bin/env python3
"""STEP 1 - organise the footage: ffprobe every file, give each a role, pick the main clip.

    python3 scripts/probe.py <footage_folder> <work_dir>

Roles: no picture = mic · picture = camera or screen (a guess, confirmed with the user).
Main clip = the longest camera clip unless the user says otherwise. Nothing is renamed, moved or deleted.
"""
import os, sys
from fractions import Fraction
from common import ffprobe, save, MEDIA

def main(folder, work):
    os.makedirs(work, exist_ok=True); files = []
    for root, _, names in os.walk(folder):
        for n in sorted(names):
            if n.startswith('.') or os.path.splitext(n)[1].lower() not in MEDIA: continue
            p = os.path.join(root, n); info = ffprobe(p)
            v = next((s for s in info.get('streams', []) if s['codec_type'] == 'video'
                      and s.get('disposition', {}).get('attached_pic', 0) == 0), None)
            a = [s for s in info.get('streams', []) if s['codec_type'] == 'audio']
            d = float(info.get('format', {}).get('duration', 0) or 0)
            f = dict(path=p, name=n, dur=round(d, 3), audio_streams=len(a),
                     audio_sr=int(a[0]['sample_rate']) if a else None)
            if v:
                rot = 0
                for sd in v.get('side_data_list', []): rot = int(sd.get('rotation', rot) or rot)
                w, h = v['width'], v['height']
                if abs(rot) in (90, 270): w, h = h, w
                fps = Fraction(v.get('r_frame_rate', '30/1'))
                name = n.lower()
                screen = any(k in name for k in ('screen', 'obs', 'capture', 'recording', 'شاشة')) or \
                         (not a) or v.get('codec_name') in ('qtrle', 'prores') and 'screen' in name
                f.update(w=w, h=h, fps=[fps.numerator, fps.denominator], vcodec=v.get('codec_name'),
                         role='screen' if screen else 'camera', role_sure=False)
            else:
                f.update(role='mic', role_sure=True)
            files.append(f)
    cams = [f for f in files if f['role'] == 'camera'] or [f for f in files if f['role'] == 'screen']
    main_clip = max(cams, key=lambda f: f['dur'])['path'] if cams else None
    for f in files: f['main'] = f['path'] == main_clip
    save(os.path.join(work, 'roles.json'), dict(folder=folder, files=files))
    print(f"{'role':7} {'main':4} {'dur':>9}  {'size':>10} {'fps':>7}  name")
    for f in files:
        fps = f"{f['fps'][0]/f['fps'][1]:.2f}" if 'fps' in f else '-'
        size = f"{f['w']}x{f['h']}" if 'w' in f else '-'
        print(f"{f['role']:7} {'*' if f['main'] else '':4} {f['dur']:9.1f}  {size:>10} {fps:>7}  {f['name']}"
              + ('' if f['role_sure'] else '   (role is a guess)') + ('' if f['audio_streams'] else '   NO AUDIO - cannot be synced by sound'))
if __name__ == '__main__': main(sys.argv[1], sys.argv[2])
