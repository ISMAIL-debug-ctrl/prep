---
name: prep
description: Raw footage folder -> a Premiere Pro project ready to edit, with three sequences - Assembly (every camera and mic synced, untouched), Rough Cut (what will never be used removed) and Tight (silences removed for pace, judgement moments marked). Works for one camera, screen recordings, and multi-camera shoots with separate audio recorders. Use when the user says "prep", "prep this footage", "sync and rough cut", "set up the project", or hands over a folder of raw footage for one video. Input - footage folder + video name.
---

# /prep — footage folder → Premiere project with Assembly, Rough Cut and Tight

`SK` = this skill's folder. Run every Python script with a Python that has `requirements.txt` installed (`PY`) —
`~/.prep-venv/bin/python` on macOS, `$HOME\.prep-venv\Scripts\python.exe` on Windows. Paths given to Premiere scripts use forward slashes.
The Premiere half runs through the `premiere-pro` MCP server (see `INSTALL.md`).

**Input:** the footage folder and the video's name. Ask only for those (and the spoken language if it is not obvious).

## Ground rules
- Never rename, move, edit or delete an original file. Read them where they are.
- Before every change in Premiere, confirm the active project is the one this run created. If not, **stop** — other open
  projects are never touched. Always pass `sequenceId`; never rely on the active sequence.
- **One sequence per stage.** Every stage works on a duplicate of the previous one; the previous one is never edited again.
- When unsure, keep it. A wrong keep costs two seconds; a wrong cut hides footage.
- Never say a step worked unless its result was read back from Premiere (positions in ticks, 254016000000 per second).

## How the Premiere MCP behaves
- Call `verify_premiere_connection` first. Find tools with `search_tools`, run them with `invoke_tool`.
- `execute_extendscript` takes `{script}`; the script must end with a `return`. It is arbitrary code inside Premiere: use it
  only on the project this run created.
- Imports, new sequences and duplicates can land outside the requested bin — read the bins back and move strays.
- Placing a clip snaps to a whole frame; `projectItem.setInPoint()` on an audio-only file can land up to 2 frames off. Set the
  track item's points afterwards in this order: `outPoint` (+2 frames) → `inPoint` → `outPoint` → `end`, and read them back.
- The bridge gives up after 45 s while Premiere keeps working. Long jobs are done in batches that resume from where they stopped.
- No Premiere project open = no panel loaded = no bridge. If the `Window > Extensions` menu is missing, `tools/open_bridge_panel.js`.

## Lessons that are now rules
- **No Premiere project yet → create it.** The delivery is always a Premiere project with the three sequences.
- **Phone clips are variable frame rate.** A sequence made from an iPhone clip can come out at an odd rate (28.14 fps): set the
  sequence to the clips' nominal rate (30 / 60) with `getSettings()` → `videoFrameRate` → `setSettings()` before placing anything, then read positions back.
- **Clips shot one after another (one phone, no recorder):** no sync — lay them end to end in recording order (check `creation_time`).
  The phone's own audio is the only audio: keep it enabled.
- **Noisy room audio:** phrase detection uses `max(speech level − 30 dB, noise floor + 8 dB)`, so a fan or a phone mic does not glue everything into one phrase.
- **Something personal on screen** (an email address, an inbox, a code): if it is part of the explanation, do not cut it — put a
  regular `DECIDE` marker on it with the reason, and mention it in the report.
- ExtendScript `File.write` ends lines with CR on macOS; Python's `splitlines()` reads it fine — set `f.lineFeed = 'Unix'` for clean files.

## Step 1 · Organise
Inside the footage folder create `_work/`, `_assets/`, `exports/` (everything new goes there; originals stay put).
`PY SK/scripts/probe.py <footage> <footage>/_work` → `roles.json` + a table. No picture = mic. Picture = camera or screen
recording (a guess — confirm when unclear). Show the list.

## Step 2 · Premiere project (always — create it if the folder has none)
`create_project` (named after the video, saved in the footage folder) → bins `Footage` and `Sequences` → import every file into
`Footage` → `createNewSequenceFromClips` from the main camera clip (takes its size and rate), named `<name> Assembly`, then emptied.

## Step 3 · Sync
`PY SK/scripts/sync.py <work>` → `sync.json` + a table. Audio cross-correlation, median of up to 15 windows, a recording is
accepted when the middle half of its windows agree within one frame; a file that matches nothing is retried against every
file that did sync.
- **Separate audio recorders are the sync base** when the shoot has them: set the longest recorder as `main` in `roles.json`
  for `sync.py`, then set a camera back as `main` so the frame rate is known to `cutlist.py`.
- A file that matches nothing is **asked about, never dropped** — it may be an intro or a pickup shot separately; sync such a pair to each other.
- Camera timecode is often Rec Run (continuous across clips whatever the real gap) — it proves nothing about position.

Tracks: one video track per camera; recorders on A1…An; each camera's own audio on the tracks after them, every clip
**disabled** (Shift+E, `trackItem.disabled = true`) — kept, never deleted. Name the tracks.
**Proof:** read every clip's position back in ticks and compare with `sync.json`.

## Step 4 · Transcribe
`PY SK/scripts/phrases.py <work> --lang <ar|en|…> [--source <file>]` → `phrases.json`, `phrases.txt`.
Phrase times come from loudness, never from Whisper; each phrase is transcribed twice (whole file, then alone) because Whisper
tidies retakes away on the whole file. Several speakers: mix the recorders as laid out on the timeline into one file and pass it with `--source`.

## Step 5 · Duplicate
Duplicate the Assembly → `<name> Rough Cut`, in `Sequences`.

## Step 6 · Rough cut
**Read all of `phrases.txt` before deciding.** Remove only what will never be used: setup before the first real line and
everything after the last, countdowns and "cut" calls, abandoned lines that are said again, lines flagged as bad, talk not meant
for the viewer, pauses of 2 s+ where nothing happens on screen (screen recordings, cooking, any action: keep the pause).
Keep two complete versions of a line, a broken line with no retake, stumbles inside a sentence — choosing is the editor's job.
Write `decisions.json` (format in `cutlist.py`) → `PY SK/scripts/cutlist.py <work>` → `cuts.json` (warns if more than a fifth of
the speech goes). In Premiere build the Rough Cut from the kept ranges with `premiere/apply_cuts.jsx` (no razor + ripple: there is no ripple across all tracks).
**Proof:** zero mismatches in the script's read-back; the Assembly still has one whole clip per track.

More than one camera: nest the camera video tracks (one nest per continuous block). Recorders and disabled camera audio stay
outside the nest. Leave multicam enabling to the editor.

## Step 7 · Tight
Rhythm only — silences out, content untouched. Built every time; the editor decides later which sequence to continue from.
1. Duplicate the **latest** Rough Cut (if the editor already worked on it, theirs) → `<name> Tight`, empty it.
2. `premiere/dump_sequence.jsx` on the Rough Cut → `<work>/tight/rough_dump.txt`.
3. `PY SK/scripts/tight_plan.py <work>/tight/rough_dump.txt <work>/tight [--from-frame F]` → `plan.json`.
   Each recorder is measured on its own; a silence is when **everyone** is quiet; laughter counts as sound; silences of 0.35 s+
   are cut with 0.12 s / 0.10 s of air; silences of 2 s+ and silences right after laughter are **left uncut and marked**.
4. `premiere/build_from_plan.jsx` — run it again and again until it answers `{done:true}`.
5. `dump_sequence.jsx` on the Tight → `PY SK/scripts/verify_rebuild.py rough_dump.txt tight_dump.txt plan.json --fix fix.json`;
   if pieces are listed, `premiere/fix_pieces.jsx`, then dump and verify again until every track reads 0 / 0.
6. `premiere/add_markers.jsx` — a `DECIDE` marker with the reason on every judgement moment.

## Report
Save the project. Then: where it is · the three sequence names and lengths · each rough-cut removal with the words that went
and why · anything kept but doubtful · the Tight's silences removed and markers by kind.

---
By Ismail — [ISMAILX](https://ismailx.com). MIT licence.
