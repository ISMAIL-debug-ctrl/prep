"""Shared helpers for the rough-cut workflow. Originals are only ever read."""
import json, subprocess, numpy as np
TICKS = 254016000000          # Premiere ticks per second
MEDIA = {'.mp4', '.mov', '.mkv', '.m4v', '.mxf', '.avi', '.wav', '.mp3', '.m4a', '.aac', '.flac', '.aif', '.aiff'}

def ffprobe(path):
    r = subprocess.run(['ffprobe', '-v', 'error', '-print_format', 'json', '-show_format', '-show_streams', path],
                       capture_output=True, text=True)
    return json.loads(r.stdout or '{}')

def audio(path, sr, start=None, dur=None):
    """Decode to mono float32 at sr. start/dur in seconds read only that window."""
    cmd = ['ffmpeg', '-v', 'error']
    if start is not None: cmd += ['-ss', f'{max(0, start):.6f}']
    cmd += ['-i', path]
    if dur is not None: cmd += ['-t', f'{dur:.6f}']
    cmd += ['-vn', '-ac', '1', '-ar', str(sr), '-f', 'f32le', '-']
    return np.frombuffer(subprocess.run(cmd, capture_output=True).stdout, np.float32)

def load(p): return json.load(open(p))
def save(p, d): json.dump(d, open(p, 'w'), ensure_ascii=False, indent=1)
