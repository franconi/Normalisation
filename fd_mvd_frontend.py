#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

from fd_mvd_normalizer import analyze_schema, schema_from_text


HTML = r"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>FD/MVD Normalizer</title>
  <style>
    :root {
      color-scheme: light;
      --bg: #f5f7f8;
      --panel: #ffffff;
      --ink: #172026;
      --muted: #5e6b73;
      --line: #d8e0e5;
      --accent: #0f6f73;
      --accent-strong: #0a5559;
      --bad: #a33a2b;
      --good: #197049;
      --soft: #edf4f4;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background: var(--bg);
      color: var(--ink);
      letter-spacing: 0;
    }
    main {
      width: min(1180px, calc(100vw - 32px));
      margin: 0 auto;
      padding: 28px 0;
    }
    header {
      display: flex;
      align-items: flex-end;
      justify-content: space-between;
      gap: 18px;
      margin-bottom: 18px;
    }
    h1 {
      margin: 0;
      font-size: 28px;
      line-height: 1.15;
      font-weight: 720;
    }
    .status {
      min-height: 28px;
      padding: 5px 10px;
      border: 1px solid var(--line);
      border-radius: 6px;
      background: var(--panel);
      color: var(--muted);
      font-size: 13px;
      white-space: nowrap;
    }
    .layout {
      display: grid;
      grid-template-columns: minmax(360px, 0.92fr) minmax(420px, 1.08fr);
      gap: 16px;
      align-items: start;
    }
    section {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      min-width: 0;
    }
    .panel-head {
      min-height: 50px;
      padding: 12px 14px;
      border-bottom: 1px solid var(--line);
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
    }
    h2 {
      margin: 0;
      font-size: 15px;
      font-weight: 680;
    }
    .controls {
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
      justify-content: flex-end;
    }
    button, .file-label {
      appearance: none;
      border: 1px solid var(--line);
      border-radius: 6px;
      background: #fff;
      color: var(--ink);
      min-height: 34px;
      padding: 7px 11px;
      font: inherit;
      font-size: 13px;
      cursor: pointer;
    }
    button.primary {
      background: var(--accent);
      border-color: var(--accent);
      color: white;
      font-weight: 650;
    }
    button.primary:hover { background: var(--accent-strong); }
    button:hover, .file-label:hover { border-color: #a9b8c0; }
    input[type="file"] { display: none; }
    textarea {
      display: block;
      width: 100%;
      min-height: 520px;
      resize: vertical;
      border: 0;
      padding: 14px;
      outline: none;
      font: 14px/1.45 ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
      color: var(--ink);
      background: #fbfcfd;
      tab-size: 2;
    }
    .result {
      padding: 14px;
      min-height: 520px;
    }
    .empty {
      color: var(--muted);
      font-size: 14px;
      padding: 12px;
    }
    .badge {
      display: inline-flex;
      align-items: center;
      min-height: 26px;
      padding: 3px 9px;
      border-radius: 999px;
      font-size: 13px;
      font-weight: 650;
      margin-bottom: 14px;
    }
    .badge.good {
      background: #e7f4ee;
      color: var(--good);
    }
    .badge.bad {
      background: #fae9e6;
      color: var(--bad);
    }
    .grid {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 12px;
      margin-bottom: 12px;
    }
    .box {
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 10px;
      background: #fff;
      min-width: 0;
    }
    .box h3 {
      margin: 0 0 8px;
      font-size: 13px;
      color: var(--muted);
      font-weight: 680;
    }
    .chips {
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
      min-height: 24px;
    }
    .chip {
      display: inline-flex;
      align-items: center;
      max-width: 100%;
      min-height: 26px;
      border: 1px solid var(--line);
      border-radius: 6px;
      padding: 3px 7px;
      background: var(--soft);
      font: 13px/1.35 ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
      overflow-wrap: anywhere;
    }
    .checks {
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 8px;
      margin: 12px 0;
    }
    .check {
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 9px;
      background: #fff;
      font-size: 13px;
      color: var(--muted);
    }
    .check strong {
      display: block;
      color: var(--ink);
      margin-bottom: 3px;
    }
    ul {
      margin: 8px 0 0 18px;
      padding: 0;
    }
    li {
      margin: 6px 0;
      line-height: 1.35;
      overflow-wrap: anywhere;
    }
    pre {
      margin: 12px 0 0;
      padding: 10px;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: #fbfcfd;
      overflow: auto;
      font: 12px/1.45 ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
      max-height: 260px;
    }
    @media (max-width: 880px) {
      main { width: min(100vw - 20px, 760px); padding: 18px 0; }
      header, .panel-head { align-items: stretch; flex-direction: column; }
      .layout, .grid, .checks { grid-template-columns: 1fr; }
      .controls { justify-content: flex-start; }
      textarea, .result { min-height: 380px; }
      .status { white-space: normal; }
    }
  </style>
</head>
<body>
  <main>
    <header>
      <h1>FD/MVD Normalizer</h1>
      <div id="status" class="status">Ready</div>
    </header>

    <div class="layout">
      <section>
        <div class="panel-head">
          <h2>Input</h2>
          <div class="controls">
            <label class="file-label" for="fileInput">Open TXT</label>
            <input id="fileInput" type="file" accept=".txt,text/plain">
            <button id="sampleButton" type="button">Sample</button>
            <button id="clearButton" type="button">Clear</button>
            <button id="runButton" class="primary" type="button">Analyze</button>
          </div>
        </div>
        <textarea id="input" spellcheck="false">attributes: A B C D
AB -> C
A ->> D</textarea>
      </section>

      <section>
        <div class="panel-head">
          <h2>Result</h2>
        </div>
        <div id="result" class="result">
          <div class="empty">Run the analyzer to see the decomposition.</div>
        </div>
      </section>
    </div>
  </main>

  <script>
    const input = document.getElementById('input');
    const result = document.getElementById('result');
    const statusEl = document.getElementById('status');

    const sample = `attributes: A B C E F G
A -> CG
B -> A
E -> GF
GF -> E
A ->> B
CG ->> ABC`;

    function fmtSet(values) {
      if (!values || values.length === 0) return '{}';
      return values.join('');
    }

    function fmtDep(dep, op) {
      return `${fmtSet(dep.lhs)} ${op} ${fmtSet(dep.rhs)}`;
    }

    function chips(items) {
      if (!items || items.length === 0) return '<span class="chip">none</span>';
      return items.map(item => `<span class="chip">${escapeHtml(item)}</span>`).join('');
    }

    function escapeHtml(value) {
      return String(value)
        .replaceAll('&', '&amp;')
        .replaceAll('<', '&lt;')
        .replaceAll('>', '&gt;')
        .replaceAll('"', '&quot;')
        .replaceAll("'", '&#039;');
    }

    function render(data) {
      const attrs = data.attributes || [];
      const fds = (data.fds || []).map(dep => fmtDep(dep, '->'));
      const mvds = (data.mvds || []).map(dep => fmtDep(dep, '->>'));
      const badgeClass = data.extended_conflict_free ? 'good' : 'bad';
      const badgeText = data.extended_conflict_free ? 'Extended conflict-free' : 'Not extended conflict-free';

      let html = `<div class="badge ${badgeClass}">${badgeText}</div>`;
      html += `<div class="grid">
        <div class="box"><h3>Attributes</h3><div class="chips">${chips(attrs)}</div></div>
        <div class="box"><h3>FDs</h3><div class="chips">${chips(fds)}</div></div>
        <div class="box"><h3>MVDs</h3><div class="chips">${chips(mvds)}</div></div>
        <div class="box"><h3>Decomposition</h3><div class="chips">${chips((data.decomposition || []).map(fmtSet))}</div></div>
      </div>`;

      if (data.extended_conflict_free) {
        html += `<div class="checks">
          <div class="check"><strong>${data.acyclic ? 'Yes' : 'No'}</strong>Acyclic</div>
          <div class="check"><strong>${data.lossless ? 'Yes' : 'No'}</strong>Lossless</div>
          <div class="check"><strong>${data.dependency_preserving ? 'Yes' : 'No'}</strong>Dependency-preserving</div>
        </div>`;
      }

      if (data.errors && data.errors.length) {
        html += '<div class="box"><h3>Extended Conflict-Free Condition Failure</h3><ul>';
        html += data.errors.map(error => `<li>${escapeHtml(error)}</li>`).join('');
        html += '</ul></div>';
      }

      html += `<pre>${escapeHtml(JSON.stringify(data, null, 2))}</pre>`;
      result.innerHTML = html;
    }

    async function analyze() {
      statusEl.textContent = 'Running';
      result.innerHTML = '<div class="empty">Running analyzer...</div>';
      try {
        const response = await fetch('/api/analyze', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({text: input.value})
        });
        const data = await response.json();
        render(data);
        statusEl.textContent = response.ok ? 'Done' : 'Check input';
      } catch (error) {
        result.innerHTML = `<div class="badge bad">Request failed</div><pre>${escapeHtml(error.message)}</pre>`;
        statusEl.textContent = 'Failed';
      }
    }

    document.getElementById('runButton').addEventListener('click', analyze);
    document.getElementById('sampleButton').addEventListener('click', () => { input.value = sample; });
    document.getElementById('clearButton').addEventListener('click', () => { input.value = ''; result.innerHTML = '<div class="empty">Run the analyzer to see the decomposition.</div>'; });
    document.getElementById('fileInput').addEventListener('change', async (event) => {
      const file = event.target.files[0];
      if (!file) return;
      input.value = await file.text();
      statusEl.textContent = file.name;
    });
  </script>
</body>
</html>
"""


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        if self.path not in {"/", "/index.html"}:
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        self._send(HTTPStatus.OK, HTML.encode("utf-8"), "text/html; charset=utf-8")

    def do_POST(self) -> None:
        if self.path != "/api/analyze":
            self.send_error(HTTPStatus.NOT_FOUND)
            return

        try:
            length = int(self.headers.get("content-length", "0"))
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
            text = str(payload.get("text", ""))
            schema = schema_from_text(text)
            output = analyze_schema(schema, max_rows=8192, max_relations=8)
            status = HTTPStatus.OK if output.get("extended_conflict_free") else HTTPStatus.UNPROCESSABLE_ENTITY
        except Exception as exc:
            output = {"extended_conflict_free": False, "errors": [str(exc)]}
            status = HTTPStatus.BAD_REQUEST

        self._send(
            status,
            json.dumps(output, indent=2).encode("utf-8"),
            "application/json; charset=utf-8",
        )

    def log_message(self, format: str, *args: Any) -> None:
        return

    def _send(self, status: HTTPStatus, body: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header("content-type", content_type)
        self.send_header("content-length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()

    server = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"Serving FD/MVD Normalizer at http://{args.host}:{args.port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
