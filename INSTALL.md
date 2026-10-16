# Install

Works on macOS and Windows with Premiere Pro 2026 and Claude Code. Run on macOS (Apple Silicon); the Windows path below is written for it but has not yet been run on a Windows PC.

## 1. Tools

**macOS**
```bash
brew install ffmpeg node python
```
```bash
python3 -m venv ~/.prep-venv && ~/.prep-venv/bin/pip install -r requirements.txt
```
Run the scripts with `~/.prep-venv/bin/python`.

**Windows** (PowerShell)
```powershell
winget install --id Gyan.FFmpeg -e; winget install --id OpenJS.NodeJS.LTS -e; winget install --id Python.Python.3.12 -e
```
Close and reopen PowerShell, then:
```powershell
py -3 -m venv $HOME\.prep-venv; & $HOME\.prep-venv\Scripts\python.exe -m pip install -r requirements.txt
```
Run the scripts with `$HOME\.prep-venv\Scripts\python.exe`.

The transcriber is picked automatically: `mlx-whisper` on Apple Silicon Macs, `faster-whisper` everywhere else (NVIDIA GPU
when CUDA works, otherwise CPU — slower). The first transcription downloads the model (≈ 1.5 GB).

## 2. The skill
```bash
git clone https://github.com/ISMAIL-debug-ctrl/prep ~/.claude/skills/prep
```
Windows: `git clone https://github.com/ISMAIL-debug-ctrl/prep $HOME\.claude\skills\prep`
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
Windows: the bridge's own installer is `npm run setup:win` from its repository (see its QUICKSTART); in the panel set the
Temp Directory to `%TEMP%\premiere-mcp-bridge` and use the same folder for `PREMIERE_TEMP_DIR` in `.mcp.json`.

Register it for Claude Code: copy `mcp.example.json` to `.mcp.json` in the folder you run Claude from (or add the same entry with `claude mcp add`).

Restart Premiere, open a project, open `Window > Extensions > MCP Bridge (CEP)` and start it. If the Extensions menu is missing,
`node tools/open_bridge_panel.js` opens the panel through another panel's debug port.

## Windows notes
- Paths given to Premiere scripts use forward slashes: `C:/Users/you/Videos/shoot`.
- `tools/open_bridge_panel.js` uses `%TEMP%\premiere-mcp-bridge` on Windows (or `PREMIERE_TEMP_DIR` if set).
- Every file the scripts write is UTF-8, so Arabic and other non-Latin names work.
