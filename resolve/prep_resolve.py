#!/usr/bin/env python3
"""/prep for DaVinci Resolve - builds the same three timelines as the Premiere route (Assembly, Rough Cut, Tight).

Runs two ways, with the same CFG:
  1. Inside Resolve through the DaVinci Resolve MCP (works with the free edition through its bridge):
         exec(open("<SK>/resolve/prep_resolve.py").read(), {"resolve": resolve, "CFG": {...}})
     (the MCP's script tool provides `resolve`).
  2. From a terminal with Resolve Studio (Preferences > System > General > External scripting = Local):
         python resolve/prep_resolve.py <cfg.json>

CFG["action"]:
  assembly  {project, work, name}          new project (or the open one with that name), import, `<name> Assembly` from
                                           roles.json + sync.json: one video track per camera, recorders on A1..An,
                                           camera audio after them - disabled when recorders exist.
  cut       {project, source, name, keep}  new timeline `name` from timeline `source`, keeping `keep` = [[f0, f1], ...]
                                           (timeline frames from 0, end exclusive) or a path to plan.json / cuts.json.
                                           Every piece keeps its source in-point and enabled state. One AppendToTimeline call.
  dump      {project, timeline, out, fps}  writes 'track|name|start|end|in|path|enabled' in ticks (254016000000/s, like
                                           Premiere), so tight_plan.py and verify_rebuild.py work unchanged.
  markers   {project, timeline, marks, name, color}   marks = path to plan.json or [{frame, why}]
Result: a dict in RESULT (and printed as JSON when run from a terminal).
"""
import os, json

TICKS = 254016000000
AUDIO_ONLY = ('.wav', '.mp3', '.m4a', '.aac', '.aif', '.aiff', '.flac')


def _load(p):
    with open(p, encoding='utf-8') as f: return json.load(f)


def _project(resolve, name, create=False):
    pm = resolve.GetProjectManager()
    cur = pm.GetCurrentProject()
    if cur and cur.GetName() == name: return cur
    p = pm.LoadProject(name)
    if not p and create: p = pm.CreateProject(name)
    if not p: raise RuntimeError(f'project "{name}" not found')
    return p


def _timeline(project, name):
    for i in range(1, project.GetTimelineCount() + 1):
        t = project.GetTimelineByIndex(i)
        if t.GetName() == name: return t
    raise RuntimeError(f'timeline "{name}" not found')


def _ensure_tracks(tl, kind, n, sub='stereo'):
    while tl.GetTrackCount(kind) < n:
        tl.AddTrack(kind) if kind == 'video' else tl.AddTrack('audio', sub)


def assembly(resolve, C):
    work = C['work']; roles, sync = _load(os.path.join(work, 'roles.json')), _load(os.path.join(work, 'sync.json'))
    cam = next((f for f in roles['files'] if f.get('main') and f.get('fps')), None) or next(f for f in roles['files'] if f.get('fps'))
    fps = cam['fps'][0] / cam['fps'][1]
    project = _project(resolve, C['project'], create=True)
    project.SetSetting('timelineFrameRate', str(round(fps, 3)).rstrip('0').rstrip('.'))
    project.SetSetting('timelineResolutionWidth', str(cam['w'])); project.SetSetting('timelineResolutionHeight', str(cam['h']))
    mp = project.GetMediaPool(); root = mp.GetRootFolder()
    folder = mp.AddSubFolder(root, 'Footage') or root; mp.SetCurrentFolder(folder)
    ok = [c for c in sync['clips'] if c.get('ok') and not c.get('synthetic') and 'timeline_start' in c]
    items = {}
    for it in mp.ImportMedia([c['path'] for c in ok]) or []:
        items[it.GetClipProperty('File Path')] = it
    group = lambda c: c.get('track') or os.path.dirname(c['path'])
    cams = [c for c in ok if not c['path'].lower().endswith(AUDIO_ONLY)]
    recs = [c for c in ok if c['path'].lower().endswith(AUDIO_ONLY)]
    vgroups = list(dict.fromkeys(group(c) for c in cams)); rgroups = list(dict.fromkeys(group(c) for c in recs))
    tl = mp.CreateEmptyTimeline(C['name'] + ' Assembly'); project.SetCurrentTimeline(tl)
    _ensure_tracks(tl, 'video', len(vgroups)); _ensure_tracks(tl, 'audio', len(rgroups) + len(vgroups))
    t0 = tl.GetStartFrame(); F = lambda s: int(round(s * fps)); info = []
    for c in cams:
        frames = int(float(items[c['path']].GetClipProperty('Frames') or 0)) or F(c['dur'])
        info.append({'mediaPoolItem': items[c['path']], 'startFrame': 0, 'endFrame': frames - 1,
                     'recordFrame': t0 + F(c['timeline_start']), 'trackIndex': vgroups.index(group(c)) + 1, 'mediaType': 1})
        info.append({'mediaPoolItem': items[c['path']], 'startFrame': 0, 'endFrame': frames - 1,
                     'recordFrame': t0 + F(c['timeline_start']), 'trackIndex': len(rgroups) + vgroups.index(group(c)) + 1, 'mediaType': 2})
    for c in recs:
        info.append({'mediaPoolItem': items[c['path']], 'startFrame': 0, 'endFrame': F(c['dur']) - 1,
                     'recordFrame': t0 + F(c['timeline_start']), 'trackIndex': rgroups.index(group(c)) + 1, 'mediaType': 2})
    placed = mp.AppendToTimeline(info) or []
    if recs:                                                  # recorders are the sound: camera audio stays, disabled
        for k in range(len(rgroups) + 1, tl.GetTrackCount('audio') + 1):
            for it in tl.GetItemListInTrack('audio', k) or []: it.SetClipEnabled(False)
    for i, g in enumerate(vgroups): tl.SetTrackName('video', i + 1, os.path.basename(g) or f'cam {i + 1}')
    return {'timeline': tl.GetName(), 'placed': len(placed), 'expected': len(info), 'fps': fps}


def _keep(C, end):
    k = C['keep']
    if isinstance(k, list): return k
    P = _load(k)
    if 'keep' in P: return P['keep']
    keep, prev = [], 0
    for c in sorted(P['cuts'], key=lambda c: c['start_frame']): keep.append([prev, c['start_frame']]); prev = c['end_frame']
    keep.append([prev, end]); return [x for x in keep if x[1] > x[0]]


def cut(resolve, C):
    project = _project(resolve, C['project']); src = _timeline(project, C['source']); mp = project.GetMediaPool()
    s0 = src.GetStartFrame(); end = src.GetEndFrame() - s0; keep = _keep(C, end)
    pieces = []                                              # (kind, track, item, start, end, srcIn, enabled) in timeline frames from 0
    for kind in ('video', 'audio'):
        for k in range(1, src.GetTrackCount(kind) + 1):
            for it in src.GetItemListInTrack(kind, k) or []:
                pieces.append((kind, k, it.GetMediaPoolItem(), it.GetStart() - s0, it.GetEnd() - s0,
                               it.GetSourceStartFrame(), it.GetClipEnabled()))
    tl = mp.CreateEmptyTimeline(C['name']); project.SetCurrentTimeline(tl)
    _ensure_tracks(tl, 'video', src.GetTrackCount('video')); _ensure_tracks(tl, 'audio', src.GetTrackCount('audio'))
    t0 = tl.GetStartFrame(); info, enabled, pos = [], [], 0
    for a, b in keep:
        for kind, k, mpi, s, e, sin, en in pieces:
            o1, o2 = max(a, s), min(b, e)
            if o2 - o1 < 1 or mpi is None: continue
            first = sin + (o1 - s)
            info.append({'mediaPoolItem': mpi, 'startFrame': first, 'endFrame': first + (o2 - o1) - 1,
                         'recordFrame': t0 + pos + (o1 - a), 'trackIndex': k, 'mediaType': 1 if kind == 'video' else 2})
            enabled.append(en)
        pos += b - a
    placed = mp.AppendToTimeline(info) or []
    for it, en in zip(placed, enabled):
        if not en: it.SetClipEnabled(False)
    return {'timeline': tl.GetName(), 'ranges': len(keep), 'placed': len(placed), 'expected': len(info), 'frames': pos}


def dump(resolve, C):
    project = _project(resolve, C['project']); tl = _timeline(project, C['timeline'])
    fps = float(C.get('fps') or project.GetSetting('timelineFrameRate')); tpf = TICKS / fps; s0 = tl.GetStartFrame(); rows = []
    for kind, tag in (('video', 'V'), ('audio', 'A')):
        for k in range(1, tl.GetTrackCount(kind) + 1):
            for it in tl.GetItemListInTrack(kind, k) or []:
                mpi = it.GetMediaPoolItem(); path = mpi.GetClipProperty('File Path') if mpi else ''
                rows.append('|'.join([f'{tag}{k}', it.GetName(), str(round((it.GetStart() - s0) * tpf)), str(round((it.GetEnd() - s0) * tpf)),
                                      str(round(it.GetSourceStartFrame() * tpf)), path, 'true' if it.GetClipEnabled() else 'false']))
    with open(C['out'], 'w', encoding='utf-8') as f: f.write('\n'.join(rows))
    return {'clips': len(rows), 'out': C['out']}


def markers(resolve, C):
    project = _project(resolve, C['project']); tl = _timeline(project, C['timeline'])
    marks = C['marks'] if isinstance(C['marks'], list) else _load(C['marks'])['marks']
    n = sum(bool(tl.AddMarker(int(m['frame']), C.get('color', 'Red'), C.get('name', 'DECIDE'), m.get('why', ''), 1)) for m in marks)
    return {'markers': n, 'of': len(marks)}


def run(resolve, C):
    return {'assembly': assembly, 'cut': cut, 'dump': dump, 'markers': markers}[C['action']](resolve, C)


if 'resolve' in globals() and 'CFG' in globals():            # inside Resolve (MCP script tool)
    RESULT = run(globals()['resolve'], globals()['CFG'])
elif __name__ == '__main__':                                  # terminal, Resolve Studio
    import sys
    api = os.environ.get('RESOLVE_SCRIPT_API', '/Library/Application Support/Blackmagic Design/DaVinci Resolve/Developer/Scripting')
    sys.path.append(os.path.join(api, 'Modules'))
    import DaVinciResolveScript as dvr
    r = dvr.scriptapp('Resolve')
    if not r: sys.exit('cannot reach Resolve: open it, and in Studio set Preferences > System > General > External scripting = Local')
    print(json.dumps(run(r, _load(sys.argv[1])), ensure_ascii=False))
