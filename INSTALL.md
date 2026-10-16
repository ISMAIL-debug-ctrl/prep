# Install

Tested on macOS (Apple Silicon) with Premiere Pro 2026 and Claude Code.

## 1. Tools
```bash
brew install ffmpeg node python
```
```bash
python3 -m venv ~/.prep-venv && ~/.prep-venv/bin/pip install -r requirements.txt
```
Run the scripts with `~/.prep-venv/bin/python`. The first transcription downloads the Whisper model (≈ 1.5 GB).

## 2. The skill
```bash
git clone https://github.com/ISMAIL-debug-ctrl/prep ~/.claude/skills/prep
```
Claude Code then offers `/prep`.

## 3. The Premiere bridge
`/prep` drives Premiere through [adobe-premiere-pro-mcp](https://www.npmjs.com/package/adobe-premiere-pro-mcp) (MIT, third-party —
read it before installing). Version used: 1.2.8.
```bash
npm install -g adobe-premiere-pro-mcp@1.2.8 --ignore-scripts
```
```bash
premiere-pro-mcp --install-cep
```
```bash
premiere-pro-mcp --doctor
```
Optional, turns its anonymous telemetry off:
```bash
mkdir -p ~/.premiere-mcp-bridge && printf '{\n  "telemetry": false,\n  "updateCheck": false\n}\n' > ~/.premiere-mcp-bridge/config.json
```
Register it for Claude Code: copy `mcp.example.json` to `.mcp.json` in the folder you run Claude from (or add the same entry with `claude mcp add`).

Restart Premiere, open a project, open `Window > Extensions > MCP Bridge (CEP)` and start it. If the Extensions menu is missing,
`node tools/open_bridge_panel.js` opens the panel through another panel's debug port.

## Not on Apple Silicon?
`scripts/phrases.py` uses `mlx-whisper`. On Windows / Linux / Intel, swap the two `mlx_whisper.transcribe(...)` calls for
`faster-whisper` (same idea: one pass with word times over the whole file, one pass per phrase). Everything else is plain numpy + ffmpeg.
