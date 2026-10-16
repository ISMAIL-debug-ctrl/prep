#!/usr/bin/env node
// Opens the "MCP Bridge (CEP)" panel inside a running Premiere Pro when Window > Extensions is missing.
// It asks another open CEP panel (set CEP_DEBUG_PORT, default 8860) to open it. Optional: only needed when the Window > Extensions menu is missing.
//   node scripts/open_bridge_panel.js
const PORT = process.env.CEP_DEBUG_PORT || 8860;
const os = require('os'), path = require('path');
require('fs').mkdirSync(process.env.PREMIERE_TEMP_DIR || (process.platform === 'win32' ? path.join(os.tmpdir(), 'premiere-mcp-bridge') : '/tmp/premiere-mcp-bridge'), { recursive: true });
(async () => {
  const pages = await (await fetch(`http://127.0.0.1:${PORT}/json`)).json();
  if (!pages.length) throw new Error('no CEP panel is listening on the debug port - open any CEP panel that has a debug port (set CEP_DEBUG_PORT)');
  const ws = new WebSocket(pages[0].webSocketDebuggerUrl);
  ws.onopen = () => ws.send(JSON.stringify({ id: 1, method: 'Runtime.evaluate', params: {
    expression: 'window.__adobe_cep__.requestOpenExtension("com.mcp.premiere.cepbridge.panel","");"sent"' } }));
  ws.onmessage = () => { console.log('bridge panel requested'); ws.close(); process.exit(0); };
  ws.onerror = () => { console.error('could not reach the panel'); process.exit(1); };
})().catch(e => { console.error(String(e.message || e)); process.exit(1); });
