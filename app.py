"""
Parametric Modular STEP File Generator — Web Server & Generator Engine
Zero external web dependencies (uses standard library http.server).
Runs on any system with Python 3.
"""
import os
import sys
import re
import json
import urllib.parse
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
import mimetypes

# Import parametric generator
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from parametric_generator import generate_exact_step

PORT = int(os.environ.get("PORT", 8080))
TEMPLATE_PATH = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        "../../brain/72edf0fd-246c-46c9-b742-1d19eb47c407/.user_uploaded/media_1794256214054_fb0e9ed9.stp"
    )
)
if not os.path.exists(TEMPLATE_PATH):
    # Fallback search
    alt = "C:/Users/lion/.gemini/antigravity/brain/72edf0fd-246c-46c9-b742-1d19eb47c407/.user_uploaded/media_1794256214054_fb0e9ed9.stp"
    if os.path.exists(alt):
        TEMPLATE_PATH = alt

HTML_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Parametric STEP Generator | M×N Modular CAD</title>
  <style>
    :root {
      --bg: #0f172a;
      --card: #1e293b;
      --border: #334155;
      --primary: #38bdf8;
      --primary-hover: #0284c7;
      --text: #f8fafc;
      --text-muted: #94a3b8;
      --accent: #22c55e;
      --cell: #0284c7;
      --cell-border: #38bdf8;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }
    body {
      background: var(--bg);
      color: var(--text);
      min-height: 100vh;
      display: flex;
      flex-direction: column;
      align-items: center;
      padding: 2rem 1rem;
    }
    .container {
      width: 100%;
      max-width: 900px;
      display: flex;
      flex-direction: column;
      gap: 1.5rem;
    }
    .header {
      text-align: center;
    }
    .header h1 {
      font-size: 2.2rem;
      font-weight: 700;
      background: linear-gradient(135deg, #38bdf8, #818cf8);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      margin-bottom: 0.5rem;
    }
    .header p { color: var(--text-muted); font-size: 1rem; }
    .card {
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 1.5rem;
      box-shadow: 0 8px 24px rgba(0,0,0,0.3);
    }
    .controls {
      display: grid;
      grid-template-columns: 1fr 1fr auto;
      gap: 1.2rem;
      align-items: end;
    }
    .field {
      display: flex;
      flex-direction: column;
      gap: 0.5rem;
    }
    .field label {
      font-size: 0.85rem;
      font-weight: 600;
      color: var(--text-muted);
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }
    .field input {
      background: #0f172a;
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 0.8rem 1rem;
      color: var(--text);
      font-size: 1.2rem;
      font-weight: 600;
      outline: none;
      transition: border-color 0.2s;
    }
    .field input:focus { border-color: var(--primary); }
    .btn {
      background: linear-gradient(135deg, #38bdf8, #2563eb);
      color: white;
      border: none;
      border-radius: 8px;
      padding: 0.85rem 1.8rem;
      font-size: 1rem;
      font-weight: 600;
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 0.5rem;
      height: 48px;
      transition: transform 0.15s, opacity 0.2s;
    }
    .btn:hover { opacity: 0.95; transform: translateY(-1px); }
    .btn:active { transform: translateY(0); }
    .btn:disabled { opacity: 0.5; cursor: not-allowed; }
    .preview-card {
      display: flex;
      flex-direction: column;
      gap: 1rem;
    }
    .preview-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
    .preview-header h2 { font-size: 1.1rem; color: var(--text); }
    .stats-bar {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 1rem;
      padding: 1rem;
      background: #0f172a;
      border-radius: 8px;
      border: 1px solid var(--border);
    }
    .stat-item {
      display: flex;
      flex-direction: column;
      gap: 0.2rem;
    }
    .stat-label { font-size: 0.75rem; color: var(--text-muted); text-transform: uppercase; }
    .stat-val { font-size: 1.25rem; font-weight: 700; color: var(--primary); }
    #canvas-container {
      width: 100%;
      height: 340px;
      background: #090d16;
      border-radius: 8px;
      border: 1px solid var(--border);
      position: relative;
      overflow: hidden;
      display: flex;
      align-items: center;
      justify-content: center;
    }
    canvas { display: block; }
    .status-area {
      font-size: 0.9rem;
      padding: 0.8rem 1rem;
      border-radius: 8px;
      display: none;
      align-items: center;
      gap: 0.6rem;
    }
    .status-area.loading {
      display: flex;
      background: #1e293b;
      color: #38bdf8;
      border: 1px solid #38bdf8;
    }
    .status-area.success {
      display: flex;
      background: #064e3b;
      color: #34d399;
      border: 1px solid #059669;
    }
    .status-area.error {
      display: flex;
      background: #4c0519;
      color: #fb7185;
      border: 1px solid #e11d48;
    }
    .spinner {
      width: 16px;
      height: 16px;
      border: 2px solid #38bdf8;
      border-top-color: transparent;
      border-radius: 50%;
      animation: spin 0.8s linear infinite;
    }
    @keyframes spin { to { transform: rotate(360deg); } }
    .presets {
      display: flex;
      gap: 0.5rem;
      align-items: center;
      flex-wrap: wrap;
    }
    .preset-pill {
      background: #0f172a;
      border: 1px solid var(--border);
      color: var(--text-muted);
      border-radius: 20px;
      padding: 0.3rem 0.8rem;
      font-size: 0.8rem;
      cursor: pointer;
      transition: all 0.2s;
    }
    .preset-pill:hover {
      border-color: var(--primary);
      color: var(--primary);
    }
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1>Parametric STEP Generator</h1>
      <p>Instant M×N CAD Assembly Generator for Modular STP Structures</p>
    </div>

    <div class="card">
      <div class="controls">
        <div class="field">
          <label>Rows (M) &bull; X-Axis</label>
          <input type="number" id="rows" min="1" max="50" value="4" oninput="updatePreview()">
        </div>
        <div class="field">
          <label>Columns (N) &bull; Y-Axis</label>
          <input type="number" id="cols" min="2" max="100" value="7" oninput="updatePreview()">
        </div>
        <button class="btn" id="gen-btn" onclick="generateStep()">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M7 10l5 5 5-5M12 15V3"/>
          </svg>
          Generate .STP
        </button>
      </div>

      <div style="margin-top: 1rem; display: flex; align-items: center; gap: 0.8rem;">
        <span style="font-size: 0.8rem; color: var(--text-muted);">Quick Presets:</span>
        <div class="presets">
          <span class="preset-pill" onclick="setPreset(3, 4)">3×4</span>
          <span class="preset-pill" onclick="setPreset(4, 7)">4×7</span>
          <span class="preset-pill" onclick="setPreset(4, 8)">4×8</span>
          <span class="preset-pill" onclick="setPreset(5, 9)">5×9</span>
          <span class="preset-pill" onclick="setPreset(6, 12)">6×12</span>
          <span class="preset-pill" onclick="setPreset(8, 16)">8×16</span>
        </div>
      </div>
    </div>

    <div id="status-box" class="status-area"></div>

    <div class="card preview-card">
      <div class="preview-header">
        <h2>Assembly Layout Preview</h2>
        <span style="font-size: 0.8rem; color: var(--text-muted);">Pitch: 506 mm (Row) &bull; 180 mm (Col)</span>
      </div>

      <div class="stats-bar">
        <div class="stat-item">
          <span class="stat-label">Total Modules</span>
          <span class="stat-val" id="stat-modules">28</span>
        </div>
        <div class="stat-item">
          <span class="stat-label">Connectors (Cent)</span>
          <span class="stat-val" id="stat-connectors">24</span>
        </div>
        <div class="stat-item">
          <span class="stat-label">Columns (Soton)</span>
          <span class="stat-val" id="stat-columns">3</span>
        </div>
        <div class="stat-item">
          <span class="stat-label">Est. File Size</span>
          <span class="stat-val" id="stat-size">~5.4 MB</span>
        </div>
      </div>

      <div id="canvas-container">
        <canvas id="preview-canvas" width="800" height="340"></canvas>
      </div>
    </div>
  </div>

  <script>
    const canvas = document.getElementById('preview-canvas');
    const ctx = canvas.getContext('2d');

    function setPreset(m, n) {
      document.getElementById('rows').value = m;
      document.getElementById('cols').value = n;
      updatePreview();
    }

    function updatePreview() {
      const M = Math.max(1, parseInt(document.getElementById('rows').value) || 1);
      const N = Math.max(1, parseInt(document.getElementById('cols').value) || 1);

      // Update stats
      const totalModules = M * N;
      const connectors = M * Math.max(0, N - 1);
      const columns = Math.max(0, M - 1);
      const estSizeMb = (4.0 + (totalModules * 0.05)).toFixed(1);

      document.getElementById('stat-modules').textContent = totalModules;
      document.getElementById('stat-connectors').textContent = connectors;
      document.getElementById('stat-columns').textContent = columns;
      document.getElementById('stat-size').textContent = `~${estSizeMb} MB`;

      // Draw 2D canvas layout
      const w = canvas.width;
      const h = canvas.height;
      ctx.clearRect(0, 0, w, h);

      const margin = 40;
      const availW = w - margin * 2;
      const availH = h - margin * 2;

      // Module aspect ratio: col pitch = 180mm, row pitch = 506mm
      const cellPitchX = availW / Math.max(N, 1);
      const cellPitchY = availH / Math.max(M, 1);
      const cellW = Math.max(6, Math.min(cellPitchX * 0.85, 45));
      const cellH = Math.max(6, Math.min(cellPitchY * 0.85, 45));

      const gridW = (N - 1) * cellPitchX + cellW;
      const gridH = (M - 1) * cellPitchY + cellH;
      const startX = (w - gridW) / 2;
      const startY = (h - gridH) / 2;

      // Outer Frame
      ctx.strokeStyle = '#64748b';
      ctx.lineWidth = 2;
      ctx.strokeRect(startX - 15, startY - 15, gridW + 30, gridH + 30);

      // Support Columns (Soton) between rows
      ctx.fillStyle = '#f59e0b';
      for (let r = 0; r < M - 1; r++) {
        const y = startY + (r + 0.5) * cellPitchY + cellH / 2;
        ctx.fillRect(startX - 10, y - 2, gridW + 20, 4);
      }

      // Modules and Connectors
      for (let r = 0; r < M; r++) {
        const y = startY + r * cellPitchY;

        // Row rail
        ctx.strokeStyle = 'rgba(56, 189, 248, 0.2)';
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.moveTo(startX, y + cellH / 2);
        ctx.lineTo(startX + (N - 1) * cellPitchX + cellW, y + cellH / 2);
        ctx.stroke();

        for (let c = 0; c < N; c++) {
          const x = startX + c * cellPitchX;

          // Connectors (Cent) between modules
          if (c < N - 1) {
            ctx.fillStyle = '#22c55e';
            ctx.fillRect(x + cellW, y + cellH / 2 - 3, cellPitchX - cellW, 6);
          }

          // Module Cell (MouDul)
          ctx.fillStyle = '#0284c7';
          ctx.strokeStyle = '#38bdf8';
          ctx.lineWidth = 1.5;
          ctx.beginPath();
          ctx.roundRect(x, y, cellW, cellH, 4);
          ctx.fill();
          ctx.stroke();

          // Inner detail circle
          if (cellW > 14) {
            ctx.fillStyle = '#38bdf8';
            ctx.beginPath();
            ctx.arc(x + cellW / 2, y + cellH / 2, Math.min(3, cellW / 6), 0, Math.PI * 2);
            ctx.fill();
          }
        }
      }
    }

    async function generateStep() {
      const M = parseInt(document.getElementById('rows').value);
      const N = parseInt(document.getElementById('cols').value);
      const btn = document.getElementById('gen-btn');
      const statusBox = document.getElementById('status-box');

      if (!M || !N || M < 1 || N < 1) {
        alert('Please enter valid positive numbers for Rows and Columns.');
        return;
      }

      btn.disabled = true;
      statusBox.className = 'status-area loading';
      statusBox.innerHTML = `<div class="spinner"></div> Generating <strong>${M}×${N}</strong> STEP file... please wait`;

      try {
        const response = await fetch(`/api/generate?m=${M}&n=${N}`);
        if (!response.ok) {
          const err = await response.text();
          throw new Error(err || 'Generation failed');
        }

        // Trigger direct browser download
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${M}X${N}_01.stp`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);

        statusBox.className = 'status-area success';
        statusBox.innerHTML = `✓ Successfully generated and downloaded <strong>${M}X${N}_01.stp</strong> (${(blob.size / 1024 / 1024).toFixed(2)} MB)!`;
      } catch (err) {
        statusBox.className = 'status-area error';
        statusBox.innerHTML = `✕ Error: ${err.message}`;
      } finally {
        btn.disabled = false;
      }
    }

    // Initial render
    updatePreview();
  </script>
</body>
</html>
"""


class StepServerHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        client_ip = self.client_address[0] if self.client_address else "unknown"
        print(f"[HTTP] {client_ip} - {format % args}", flush=True)

    def do_GET(self):
        try:
            parsed = urllib.parse.urlparse(self.path)
            path = parsed.path
            query = urllib.parse.parse_qs(parsed.query)

            if path == "/" or path == "/index.html":
                body = HTML_PAGE.encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.send_header("Connection", "close")
                self.end_headers()
                self.wfile.write(body)
                return

            elif path == "/api/generate":
                m_str = query.get("m", [""])[0]
                n_str = query.get("n", [""])[0]

                if not m_str.isdigit() or not n_str.isdigit():
                    self.send_response(400)
                    self.end_headers()
                    self.wfile.write(b"Invalid parameters. 'm' and 'n' must be positive integers.")
                    return

                M = int(m_str)
                N = int(n_str)
                if M < 1 or N < 1:
                    self.send_response(400)
                    self.end_headers()
                    self.wfile.write(b"M and N must be >= 1.")
                    return

                print(f"[Server] Request to generate {M}x{N} STEP file...", flush=True)
                temp_dir = os.path.join(os.path.dirname(__file__), "output")
                os.makedirs(temp_dir, exist_ok=True)
                filename = f"{M}X{N}_01.stp"
                out_path = os.path.join(temp_dir, filename)

                try:
                    generate_exact_step(M, N, out_path)
                    with open(out_path, "rb") as f:
                        data = f.read()

                    self.send_response(200)
                    self.send_header("Content-Type", "application/step")
                    self.send_header("Content-Disposition", f'attachment; filename="{filename}"')
                    self.send_header("Content-Length", str(len(data)))
                    self.send_header("Connection", "close")
                    self.end_headers()
                    self.wfile.write(data)
                    print(f"[Server] Successfully delivered {filename} ({len(data):,} bytes).", flush=True)
                except Exception as e:
                    import traceback
                    traceback.print_exc()
                    self.send_response(500)
                    self.end_headers()
                    self.wfile.write(f"Generation error: {str(e)}".encode("utf-8"))
                return

            else:
                self.send_response(404)
                self.end_headers()
                self.wfile.write(b"Not Found")
        except Exception as e:
            import traceback
            traceback.print_exc()


def start_server(port=PORT):
    server = ThreadingHTTPServer(("0.0.0.0", port), StepServerHandler)
    print(f"============================================================")
    print(f"  Parametric STEP Generator Server Running!")
    print(f"  Open in your browser: http://localhost:{port}")
    print(f"  Press Ctrl+C to stop.")
    print(f"============================================================")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping server...")
        server.server_close()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", sys.argv[1] if len(sys.argv) > 1 else PORT))
    start_server(port)
