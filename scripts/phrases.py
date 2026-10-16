#!/usr/bin/env python3
"""STEP 4 - phrases from loudness, words from Whisper (twice).

    python3 scripts/phrases.py <work_dir> [--lang ar] [--source <file>] [--model mlx-community/whisper-large-v3-turbo]

A phrase = speech with no gap of 0.5 s inside it. Loudness is measured in 10 ms steps; anything within
30 dB of the speech level counts as sound; sounds shorter than 0.12 s are ignored.
Phrase times and pauses come from loudness, NEVER from Whisper (its word times can be 0.5 s early).
Transcribed twice: the whole file with word timestamps, then every phrase on its own with 0.2 s padding -
Whisper tidies restarts and repeated lines away on the whole file, and those are what the rough cut must find.
Phrase times are on the source's clock; the sync offset is added to get timeline times.
"""
import os, sys, re, difflib, numpy as np
from common import audio, load, save
SR, STEP, GAP, MIN_SOUND, RANGE_DB, PAD = 16000, 0.010, 0.5, 0.12, 30.0, 0.2

# Whisper invents these on breaths and clicks; a very short "phrase" carrying one of them is noise, not speech.
GHOSTS = ('ترجمة نانسي', 'اشتركوا في القناة', 'شكرا للمشاهدة', 'thanks for watching', 'subtitles by')
def norm(t): return re.sub(r'[^\w]', '', re.sub(r'[\u064b-\u0652\u0640]', '', t)).replace('أ', 'ا').replace('إ', 'ا').replace('ة', 'ه')
def differs(a, b): return (not b.strip()) or difflib.SequenceMatcher(None, norm(a), norm(b)).ratio() < 0.6

def find_phrases(x):
    hop = int(SR * STEP); n = len(x) // hop
    db = 10 * np.log10((x[:n * hop].reshape(n, hop) ** 2).mean(1) + 1e-12)
    level = float(np.percentile(db[db > db.max() - 60], 90))          # speech level
    on = db > level - RANGE_DB
    runs = []; s = None
    for i, v in enumerate(np.append(on, False)):
        if v and s is None: s = i
        elif not v and s is not None:
            if (i - s) * STEP >= MIN_SOUND: runs.append([s * STEP, i * STEP])
            s = None
    ph = []
    for a, b in runs:
        if ph and a - ph[-1][1] < GAP: ph[-1][1] = b
        else: ph.append([a, b])
    return ph, level

def main():
    a = sys.argv[1:]; work = a[0]
    opt = lambda k, d: a[a.index(k) + 1] if k in a else d
    lang, model = opt('--lang', 'ar'), opt('--model', 'mlx-community/whisper-large-v3-turbo')
    sync = load(os.path.join(work, 'sync.json')); clips = [c for c in sync['clips'] if c['ok']]
    src = opt('--source', None)
    if not src:                                                       # mic first, else the main camera
        mics = [c for c in clips if c['role'] == 'mic']
        src = (max(mics, key=lambda c: c['dur']) if mics else next(c for c in clips if c.get('main')))['path']
    clip = next(c for c in clips if c['path'] == src); t0 = clip['timeline_start']
    x = audio(src, SR); ph, level = find_phrases(x)
    import mlx_whisper
    kw = dict(path_or_hf_repo=model, language=lang, condition_on_previous_text=False, verbose=None)
    whole = mlx_whisper.transcribe(x, word_timestamps=True, **kw)
    words = [dict(w=w['word'].strip(), s=round(float(w['start']), 2), e=round(float(w['end']), 2))
             for s in whole['segments'] for w in s.get('words', [])]
    out = []
    for i, (s, e) in enumerate(ph):
        seg = x[int(max(0, s - PAD) * SR):int((e + PAD) * SR)]
        text = mlx_whisper.transcribe(seg, **kw)['text'].strip() if len(seg) > SR * 0.2 else ''
        if e - s < 0.6 and any(g in text.lower() for g in GHOSTS): text = ''
        whole_text = ' '.join(w['w'] for w in words if s - 0.3 <= (w['s'] + w['e']) / 2 <= e + 0.3)
        nxt = ph[i + 1][0] if i + 1 < len(ph) else len(x) / SR
        out.append(dict(n=i + 1, src_start=round(s, 3), src_end=round(e, 3), start=round(s + t0, 3), end=round(e + t0, 3),
                        dur=round(e - s, 3), pause_after=round(nxt - e, 3), text=text, whole_file_text=whole_text))
    save(os.path.join(work, 'phrases.json'), dict(source=src, lang=lang, model=model, speech_level_db=round(level, 1),
                                                   timeline_offset=t0, total=len(x) / SR, phrases=out, words=words))
    with open(os.path.join(work, 'phrases.txt'), 'w') as f:
        f.write(f"# source: {os.path.basename(src)} · {len(out)} phrases · times are TIMELINE seconds\n")
        f.write("#  n | start    | len   | pause after | words   (≠ = the whole-file pass heard it differently)\n")
        for p in out:
            diff = f"   ≠ whole: {p['whole_file_text'] or '(nothing)'}" if p['text'] and differs(p['text'], p['whole_file_text']) else ''
            f.write(f"{p['n']:4d} | {p['start']:8.2f} | {p['dur']:5.2f} | {p['pause_after']:5.2f} | {p['text'] or '(no words - noise)'}{diff}\n")
    speech = sum(p['dur'] for p in out)
    print(f"{len(out)} phrases · speech {speech:.1f}s of {len(x)/SR:.1f}s · speech level {level:.1f} dB · {os.path.join(work, 'phrases.txt')}")
if __name__ == '__main__': main()
