#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

from sql_null_decomposer import analyze_schema, schema_from_text


HTML = r"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>SQL-null Decomposer</title>
  <style>
    :root {
      color-scheme: light;
      --bg: #f4f6f7;
      --panel: #ffffff;
      --ink: #172026;
      --muted: #62717a;
      --line: #d8e0e5;
      --accent: #0f6f73;
      --accent-hover: #0a5559;
      --warn: #9a4f12;
      --soft: #eef5f5;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      background: var(--bg);
      color: var(--ink);
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
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
      gap: 16px;
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
      grid-template-columns: minmax(360px, 0.9fr) minmax(430px, 1.1fr);
      gap: 16px;
      align-items: start;
    }
    section {
      min-width: 0;
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
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
      min-height: 34px;
      border: 1px solid var(--line);
      border-radius: 6px;
      background: #fff;
      color: var(--ink);
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
    button.primary:hover { background: var(--accent-hover); }
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
      background: #fbfcfd;
      color: var(--ink);
      font: 14px/1.45 ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
      tab-size: 2;
    }
    .result {
      padding: 14px;
      min-height: 520px;
    }
    .empty {
      padding: 12px;
      color: var(--muted);
      font-size: 14px;
    }
    .summary {
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 10px;
      margin-bottom: 12px;
    }
    .metric {
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 10px;
      background: #fff;
      min-width: 0;
    }
    .metric strong {
      display: block;
      font-size: 22px;
      line-height: 1;
      margin-bottom: 6px;
    }
    .metric span {
      color: var(--muted);
      font-size: 13px;
    }
    .grid {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 12px;
    }
    .box {
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 10px;
      background: #fff;
      min-width: 0;
    }
    .box.full { grid-column: 1 / -1; }
    .box h3 {
      margin: 0 0 8px;
      color: var(--muted);
      font-size: 13px;
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
    .chip.removed {
      background: #fff4e8;
      border-color: #f0d3b0;
      color: var(--warn);
    }
    ul {
      margin: 8px 0 0 18px;
      padding: 0;
    }
    li {
      margin: 7px 0;
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
      max-height: 240px;
    }
    @media (max-width: 880px) {
      main { width: min(100vw - 20px, 760px); padding: 18px 0; }
      header, .panel-head { align-items: stretch; flex-direction: column; }
      .layout, .summary, .grid { grid-template-columns: 1fr; }
      .controls { justify-content: flex-start; }
      textarea, .result { min-height: 380px; }
      .status { white-space: normal; }
    }
  </style>
</head>
<body>
  <main>
    <header>
      <h1>SQL-null Decomposer</h1>
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
            <button id="runButton" class="primary" type="button">Normalise</button>
          </div>
        </div>
        <textarea id="input" spellcheck="false">relation R: A B C D E
nullable: B C D
B -N-> C
B <-N-> C
B ->N<- D</textarea>
      </section>

      <section>
        <div class="panel-head">
          <h2>Result</h2>
        </div>
        <div id="result" class="result">
          <div class="empty">Compute a SQL-null decomposition to see the result.</div>
        </div>
      </section>
    </div>
  </main>

  <script>
    const input = document.getElementById('input');
    const result = document.getElementById('result');
    const statusEl = document.getElementById('status');

    const sample = `relation R: A B C D
nullable: B C D
B -N-> C
B <-N-> C
B ->N<- D`;

    function escapeHtml(value) {
      return String(value)
        .replaceAll('&', '&amp;')
        .replaceAll('<', '&lt;')
        .replaceAll('>', '&gt;')
        .replaceAll('"', '&quot;')
        .replaceAll("'", '&#039;');
    }

    function fmtSet(values) {
      if (!values || values.length === 0) return '{}';
      return values.join(values.some(value => value.length > 1) ? ', ' : '');
    }

    function chips(items, cls = '') {
      if (!items || items.length === 0) return '<span class="chip">none</span>';
      return items.map(item => `<span class="chip ${cls}">${escapeHtml(item)}</span>`).join('');
    }

    function render(data) {
      if (data.errors) {
        result.innerHTML = `<div class="box full"><h3>Input Error</h3><ul>${
          data.errors.map(error => `<li>${escapeHtml(error)}</li>`).join('')
        }</ul></div><pre>${escapeHtml(JSON.stringify(data, null, 2))}</pre>`;
        return;
      }

      const provisional = data.provisional_decomposition || [];
      const namedFinalRelations = data.named_sql_null_decomposition || [];
      const finalRelations = namedFinalRelations.length
        ? namedFinalRelations
        : (data.sql_null_decomposition || []);
      const restrictedNullable = data.restricted_nullable_powerset || [];
      const removed = data.removed_relations || {};
      const removedNullable = data.removed_nullable_sets || {};
      const dependencies = (data.dependencies || []).map(dep => dep.text);
      const removedItems = Object.entries(removed).map(([relation, reasons]) => {
        return `<li><strong>${escapeHtml(relation)}</strong>: ${escapeHtml(reasons.join('; '))}</li>`;
      }).join('');
      const removedNullableItems = Object.entries(removedNullable).map(([relation, reasons]) => {
        return `<li><strong>${escapeHtml(relation)}</strong>: ${escapeHtml(reasons.join('; '))}</li>`;
      }).join('');
      const namedFinal = namedFinalRelations.map(item => `${item.name}: ${fmtSet(item.attributes)}`);

      let html = `<div class="summary">
        <div class="metric"><strong>${provisional.length}</strong><span>Provisional relations</span></div>
        <div class="metric"><strong>${finalRelations.length}</strong><span>Final relations</span></div>
        <div class="metric"><strong>${Object.keys(removed).length}</strong><span>Removed relations</span></div>
      </div>`;

      html += `<div class="grid">
        <div class="box"><h3>Relation</h3><div class="chips">${chips([data.relation || 'R'])}</div></div>
        <div class="box"><h3>Attributes</h3><div class="chips">${chips(data.attributes)}</div></div>
        <div class="box"><h3>SQL-nullable Attributes</h3><div class="chips">${chips(data.nullable)}</div></div>
        <div class="box full"><h3>Dependencies</h3><div class="chips">${chips(dependencies)}</div></div>
        <div class="box"><h3>Restricted Nullable Powerset</h3><div class="chips">${chips(restrictedNullable.map(fmtSet))}</div></div>
        <div class="box"><h3>Provisional Decomposition</h3><div class="chips">${chips(provisional.map(fmtSet))}</div></div>
        <div class="box"><h3>SQL-null Decomposition</h3><div class="chips">${chips(namedFinal)}</div></div>
        <div class="box full"><h3>Removed Nullable Sets</h3>${
          removedNullableItems ? `<ul>${removedNullableItems}</ul>` : '<div class="chips"><span class="chip">none</span></div>'
        }</div>
        <div class="box full"><h3>Removed Relations</h3>${
          removedItems ? `<ul>${removedItems}</ul>` : '<div class="chips"><span class="chip">none</span></div>'
        }</div>
      </div>`;
      html += `<pre>${escapeHtml(JSON.stringify(data, null, 2))}</pre>`;
      result.innerHTML = html;
    }

    async function compute() {
      statusEl.textContent = 'Running';
      result.innerHTML = '<div class="empty">Computing decomposition...</div>';
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
        result.innerHTML = `<div class="box full"><h3>Request Failed</h3><pre>${escapeHtml(error.message)}</pre></div>`;
        statusEl.textContent = 'Failed';
      }
    }

    document.getElementById('runButton').addEventListener('click', compute);
    document.getElementById('sampleButton').addEventListener('click', () => { input.value = sample; });
    document.getElementById('clearButton').addEventListener('click', () => {
      input.value = '';
      result.innerHTML = '<div class="empty">Compute a SQL-null decomposition to see the result.</div>';
      statusEl.textContent = 'Ready';
    });
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
            output = analyze_schema(schema_from_text(text))
            status = HTTPStatus.OK
        except Exception as exc:
            output = {"errors": [str(exc)]}
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
    parser.add_argument("--port", type=int, default=8766)
    args = parser.parse_args()

    server = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"Serving SQL-null Decomposer at http://{args.host}:{args.port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
