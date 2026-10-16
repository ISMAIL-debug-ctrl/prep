# /prep — raw footage to a Premiere project, ready to edit

A Claude Code skill by **Ismail — [ISMAILX](https://ismailx.com)**. Hand it a folder of raw footage and it builds a Premiere Pro project
with three sequences:

| Sequence | What it is |
|---|---|
| **Assembly** | every camera and every mic in sync, untouched — camera audio kept but disabled |
| **Rough Cut** | only what will never be used is gone: setup, countdowns, "cut" calls, abandoned takes, talk not for the viewer, the tail |
| **Tight** | silences removed for pace across all mics at once; every moment that needs a human call is left alone with a `DECIDE` marker |

You open Premiere and start editing — or pick which of the three you continue from.

## What makes it different
- **Real multi-camera, multi-mic sync.** Audio cross-correlation measured in up to 15 windows per file, accepted only within one
  frame; separate recorders become the sync base. Tested on a 3-camera, 3-recorder, 46-minute show.
- **It never decides your edit.** The rough cut only removes the obvious; when in doubt it keeps. The tight cut is rhythm only.
- **Every step is proven.** Clip positions are read back from Premiere in ticks and compared with the plan — zero mismatches or it fixes them.
- **Your files are safe.** Originals are never renamed, moved or touched; every stage is a new sequence; other open projects are never touched.

Real run: 45:56 of raw footage → Rough Cut 33:24 → Tight 28:19 with 78 `DECIDE` markers, overnight, no editor in the room.

## Install
See [`INSTALL.md`](INSTALL.md). In short: ffmpeg + Python (numpy, mlx-whisper) + Premiere Pro + the `premiere-pro` MCP bridge, then
clone this repo into `~/.claude/skills/prep`.

## Use
In Claude Code:
```
/prep  /path/to/footage  "Video name"
```

## Inside
| | |
|---|---|
| `SKILL.md` | the workflow Claude follows, step by step, with every trap already hit |
| `scripts/` | probe · sync · phrases (transcription) · cutlist · tight / tight_plan · verify_rebuild |
| `premiere/` | ExtendScript run through the bridge: build a cut from kept ranges, dump a sequence, batch build, fix, markers |
| `tools/open_bridge_panel.js` | opens the bridge panel when Premiere's Extensions menu is missing |

The rough-cut approach follows the Editing Lair workflow (editinglair.com/roughcut).

## Limits
- Runs on macOS and Windows. Proven on macOS / Apple Silicon / Premiere Pro 2026; the Windows path (faster-whisper, Windows temp folder) is written but not yet run on a Windows PC.
- Building a long Tight in Premiere is slow (≈ 40 min for a 30-minute show) — it runs unattended, but it is not instant.
- Transcripts of several people talking over each other are rough; they are used to find takes, not to quote.

MIT licence.
