#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from combined_null_4nf_decomposer import analyze_combined_schema, schema_from_text


SOURCE_ROOT = Path(__file__).resolve().parent
APP_ROOT = Path(getattr(sys, "_MEIPASS", SOURCE_ROOT))


def read_help_markdown() -> str:
    for path in (APP_ROOT / "readme.md", SOURCE_ROOT / "readme.md"):
        if path.exists():
            return path.read_text(encoding="utf-8")
    return "# Normaliser\n\nThe help file `readme.md` was not found."


HTML = r"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Normaliser</title>
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
      --soft-warn: #fff4e8;
      --soft-blue: #eef4fb;
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
      width: min(1240px, calc(100vw - 32px));
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
    .header-actions {
      display: flex;
      align-items: center;
      justify-content: flex-end;
      gap: 8px;
      flex-wrap: wrap;
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
      grid-template-columns: minmax(360px, 0.86fr) minmax(500px, 1.14fr);
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
    button:disabled {
      cursor: not-allowed;
    }
    input[type="file"] { display: none; }
    textarea {
      display: block;
      width: 100%;
      min-height: 590px;
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
      min-height: 590px;
    }
    .empty {
      padding: 12px;
      color: var(--muted);
      font-size: 14px;
    }
    .summary {
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
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
      margin-bottom: 12px;
    }
    .result-section {
      margin-bottom: 20px;
      padding-bottom: 18px;
      border-bottom: 2px solid var(--line);
    }
    .result-section:last-child {
      margin-bottom: 0;
      padding-bottom: 0;
      border-bottom: 0;
    }
    .result-section-heading {
      display: flex;
      align-items: center;
      gap: 8px;
      margin: 0 0 12px;
    }
    .result-section-title {
      flex: 1 1 auto;
      min-width: 0;
      margin: 0;
    }
    .result-section-actions {
      flex: 0 0 auto;
      display: flex;
      align-items: center;
      justify-content: flex-end;
      gap: 8px;
      flex-wrap: wrap;
    }
    .section-toggle {
      appearance: none;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      width: 100%;
      min-height: 34px;
      margin: 0;
      padding: 7px 10px;
      border: 0;
      border-left: 4px solid var(--accent);
      background: var(--soft);
      border-radius: 6px;
      color: var(--ink);
      font-size: 15px;
      font-weight: 720;
      text-transform: none;
      cursor: pointer;
    }
    .section-toggle:hover {
      background: #e4eeee;
      border-color: var(--accent);
    }
    .section-toggle::after {
      content: "";
      width: 0;
      height: 0;
      flex: 0 0 auto;
      border-left: 5px solid transparent;
      border-right: 5px solid transparent;
      border-top: 6px solid currentColor;
      transition: transform 120ms ease;
    }
    .section-toggle[aria-expanded="false"]::after {
      transform: rotate(-90deg);
    }
    .result-section-body[hidden] { display: none; }
    .relation-grid {
      grid-template-columns: repeat(2, minmax(0, 1fr));
    }
    .primary-grid {
      grid-template-columns: minmax(0, 1.2fr) minmax(0, 0.8fr);
    }
    .context-grid {
      grid-template-columns: repeat(2, minmax(0, 1fr));
    }
    .details-toggle-row {
      display: flex;
      align-items: center;
      gap: 10px;
      margin: 14px 0 12px;
    }
    .details-toggle-row::before,
    .details-toggle-row::after {
      content: "";
      height: 1px;
      flex: 1;
      background: var(--line);
    }
    .details-toggle {
      appearance: none;
      display: inline-flex;
      align-items: center;
      gap: 7px;
      min-height: 30px;
      border: 1px solid var(--line);
      border-radius: 6px;
      background: #fff;
      color: var(--muted);
      padding: 5px 10px;
      font: inherit;
      font-size: 12px;
      font-weight: 680;
      text-transform: uppercase;
      cursor: pointer;
    }
    .details-toggle:hover { border-color: #a9b8c0; }
    .details-toggle::after {
      content: "";
      width: 0;
      height: 0;
      border-left: 4px solid transparent;
      border-right: 4px solid transparent;
      border-top: 5px solid currentColor;
      transition: transform 120ms ease;
    }
    .details-toggle[aria-expanded="true"]::after {
      transform: rotate(180deg);
    }
    .details-panel[hidden] { display: none; }
    .box {
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 10px;
      background: #fff;
      min-width: 0;
    }
    .box.full { grid-column: 1 / -1; }
    .box.final-4nf-box {
      background: #fff8d6;
      border-color: #eadc8a;
    }
    .box.sql-null-box {
      background: #fff8d6;
      border-color: #eadc8a;
    }
    .relation-block {
      grid-column: 1 / -1;
      padding: 10px 0 2px;
      border-top: 1px solid var(--line);
    }
    .relation-title {
      margin: 0 0 10px;
      color: var(--ink);
      font-size: 14px;
      font-weight: 680;
    }
    .box h3 {
      margin: 0 0 8px;
      color: var(--muted);
      font-size: 13px;
      font-weight: 680;
    }
    .relation-box h3 {
      color: var(--ink);
      font-size: 14px;
    }
    .attribute-list {
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
      min-height: 24px;
    }
    .attribute-token {
      display: inline-flex;
      align-items: baseline;
      max-width: 100%;
      min-height: 26px;
      border: 1px solid var(--line);
      border-radius: 6px;
      padding: 3px 7px;
      background: var(--soft);
      font: 13px/1.35 ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
      overflow-wrap: anywhere;
    }
    .attribute-token.key-attribute {
      background: var(--key-bg, #e4f7e8);
      border-color: var(--key-border, #a8d8b1);
    }
    .attribute-token sup {
      margin-left: 1px;
      color: var(--warn);
      font-size: 9px;
      font-weight: 760;
      line-height: 1;
    }
    .cnf-relation-input,
    .cnf-attribute-input {
      width: 100%;
      max-width: 100%;
      border: 1px solid var(--line);
      border-radius: 6px;
      background: #fff;
      color: var(--ink);
      font: 13px/1.35 ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
      letter-spacing: 0;
      outline: none;
      box-sizing: border-box;
    }
    .cnf-relation-input {
      min-height: 30px;
      margin: 0 0 8px;
      padding: 5px 7px;
      font-weight: 680;
    }
    .cnf-attribute-input {
      width: min(180px, 100%);
      min-height: 26px;
      padding: 3px 7px;
      background: var(--soft);
    }
    .cnf-attribute-input.key-attribute {
      background: var(--key-bg, #e4f7e8);
      border-color: var(--key-border, #a8d8b1);
    }
    .cnf-attribute-input.kind-identifier-attribute {
      border-color: var(--kind-border, #7c3aed);
      border-width: 3px;
      box-shadow: 0 0 0 1px var(--kind-ring, rgba(124, 58, 237, 0.2));
    }
    .attribute-edit {
      display: inline-flex;
      align-items: center;
      gap: 4px;
      max-width: 100%;
    }
    .kind-draft-checkbox {
      width: 14px;
      height: 14px;
      margin: 0;
      accent-color: #7c3aed;
      flex: 0 0 auto;
    }
    .kind-identifier-actions {
      display: flex;
      gap: 6px;
      align-items: center;
      flex-wrap: wrap;
      margin: 6px 0;
    }
    .kind-identifier-actions button {
      min-height: 26px;
      padding: 3px 8px;
      font-size: 12px;
    }
    .kind-identifier-actions button:disabled {
      background: #eef2f3;
      border-color: var(--line);
      color: var(--muted);
      cursor: not-allowed;
      opacity: 0.62;
    }
    .kind-identifier-actions button:disabled:hover {
      border-color: var(--line);
    }
    .kind-identifier-summary {
      background: #fff;
    }
    .kind-identifier-summary.ok {
      background: #eef8f1;
      border-color: #a8d8b1;
    }
    .kind-identifier-summary.warn {
      background: #fff7e6;
      border-color: #ebcf93;
      color: #6d4a05;
    }
    .kind-identifier-summary-text {
      font: 13px/1.35 ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
      overflow-wrap: anywhere;
    }
    .kind-identifier-summary-list {
      margin: 0;
      padding: 0;
      list-style: none;
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
    }
    .kind-identifier-summary-list li {
      display: inline-flex;
      align-items: center;
      gap: 4px;
      min-height: 24px;
      border: 1px solid var(--line);
      border-radius: 6px;
      padding: 2px 7px;
      background: #fff;
    }
    .kind-identifier-summary-list li.joint {
      border-color: #b79bf5;
      background: #f6f1ff;
    }
    .kind-identifier-summary-separator {
      color: var(--muted);
    }
    .cnf-relation-input:focus,
    .cnf-attribute-input:focus {
      border-color: var(--accent);
      box-shadow: 0 0 0 2px rgba(15, 111, 115, 0.14);
    }
    .cnf-save-button {
      min-width: 92px;
    }
    .create-kinds-button {
      min-width: 108px;
    }
    button.create-kinds-button:disabled {
      background: #eef2f3;
      border-color: var(--line);
      color: var(--muted);
      cursor: not-allowed;
    }
    button.create-kinds-button:disabled:hover {
      background: #eef2f3;
      border-color: var(--line);
    }
    button.cnf-save-button:disabled {
      background: #eef2f3;
      border-color: var(--line);
      color: var(--muted);
      cursor: not-allowed;
    }
    button.cnf-save-button:disabled:hover {
      background: #eef2f3;
      border-color: var(--line);
    }
    button.cnf-save-button[data-cnf-save-state="invalid"]:disabled {
      background: #fff1f0;
      border-color: #f0b8b2;
      color: #9f3328;
    }
    button.cnf-save-button[data-cnf-save-state="invalid"]:disabled:hover {
      background: #fff1f0;
      border-color: #f0b8b2;
    }
    .export-button {
      min-width: 104px;
    }
    .help-dialog[hidden] {
      display: none;
    }
    .joint-kind-dialog[hidden] {
      display: none;
    }
    .help-dialog,
    .joint-kind-dialog {
      position: fixed;
      inset: 0;
      z-index: 20;
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 28px;
      background: rgba(23, 32, 38, 0.42);
    }
    .joint-kind-dialog {
      z-index: 30;
    }
    .help-panel,
    .joint-kind-panel {
      width: min(920px, 100%);
      max-height: min(820px, calc(100vh - 56px));
      display: flex;
      flex-direction: column;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: var(--panel);
      box-shadow: 0 18px 48px rgba(23, 32, 38, 0.22);
    }
    .joint-kind-panel {
      width: min(420px, 100%);
    }
    .help-head,
    .joint-kind-head {
      min-height: 52px;
      padding: 12px 14px;
      border-bottom: 1px solid var(--line);
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
    }
    .help-title,
    .joint-kind-title {
      margin: 0;
      font-size: 16px;
      font-weight: 720;
    }
    .joint-kind-controls {
      display: flex;
      gap: 6px;
      align-items: center;
    }
    .joint-kind-controls button {
      width: 32px;
      min-width: 32px;
      min-height: 32px;
      padding: 0;
      font-size: 16px;
      line-height: 1;
    }
    .joint-kind-options {
      display: grid;
      gap: 8px;
      padding: 14px;
    }
    .joint-kind-option {
      display: flex;
      align-items: center;
      gap: 8px;
      min-height: 30px;
      font: 13px/1.35 ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
    }
    .joint-kind-option input {
      width: 15px;
      height: 15px;
      margin: 0;
      accent-color: #7c3aed;
    }
    .markdown-body {
      padding: 18px;
      overflow: auto;
      line-height: 1.55;
      font-size: 14px;
    }
    .markdown-body h1,
    .markdown-body h2,
    .markdown-body h3,
    .markdown-body h4,
    .markdown-body h5,
    .markdown-body h6 {
      margin: 18px 0 8px;
      line-height: 1.25;
      color: var(--ink);
    }
    .markdown-body h1:first-child,
    .markdown-body h2:first-child,
    .markdown-body h3:first-child,
    .markdown-body h4:first-child {
      margin-top: 0;
    }
    .markdown-body h1 { font-size: 24px; }
    .markdown-body h2 { font-size: 20px; }
    .markdown-body h3 { font-size: 17px; }
    .markdown-body h4 { font-size: 15px; }
    .markdown-body p {
      margin: 8px 0;
      color: var(--ink);
    }
    .markdown-body ul,
    .markdown-body ol {
      margin: 8px 0 12px 22px;
      padding: 0;
    }
    .markdown-body li {
      margin: 5px 0;
    }
    .markdown-body code {
      border: 1px solid var(--line);
      border-radius: 5px;
      padding: 1px 4px;
      background: #fbfcfd;
      font: 12px/1.4 ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
    }
    .markdown-body pre {
      max-height: none;
      margin: 10px 0 12px;
    }
    .markdown-body pre code {
      border: 0;
      padding: 0;
      background: transparent;
      font: inherit;
    }
    .markdown-body a {
      color: var(--accent);
      text-decoration: underline;
      text-underline-offset: 2px;
    }
    .nested-box {
      margin-top: 10px;
      border: 1px solid var(--line);
      border-radius: 7px;
      padding: 8px;
      background: #fbfcfd;
    }
    .nested-box h4 {
      margin: 0 0 6px;
      color: var(--muted);
      font-size: 12px;
      font-weight: 680;
    }
    .dep-list {
      margin: 0 0 0 17px;
      padding: 0;
      font: 13px/1.35 ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
    }
    .dep-list li {
      margin: 5px 0;
    }
    .dep-list-empty {
      color: var(--muted);
      font: 13px/1.35 ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
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
    .chip.warn {
      background: var(--soft-warn);
      border-color: #f0d3b0;
      color: var(--warn);
    }
    .chip.dep {
      background: var(--soft-blue);
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
    .step {
      margin: 6px 0;
      padding: 8px;
      border-radius: 7px;
      background: #fbfcfd;
      border: 1px solid var(--line);
      font: 13px/1.4 ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
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
    @media (max-width: 920px) {
      main { width: min(100vw - 20px, 760px); padding: 18px 0; }
      header, .panel-head { align-items: stretch; flex-direction: column; }
      .layout, .summary, .grid, .relation-grid, .primary-grid, .context-grid { grid-template-columns: 1fr; }
      .controls { justify-content: flex-start; }
      .header-actions { justify-content: flex-start; }
      textarea, .result { min-height: 420px; }
      .status { white-space: normal; }
      .help-dialog { padding: 14px; }
      .help-panel { max-height: calc(100vh - 28px); }
    }
  </style>
</head>
<body>
  <main>
    <header>
      <h1>Normaliser</h1>
      <div class="header-actions">
        <button id="helpButton" type="button">Help</button>
        <div id="status" class="status">Ready</div>
      </div>
    </header>

    <div class="layout">
      <section>
        <div class="panel-head">
          <h2>Input</h2>
          <div class="controls">
            <label class="file-label" for="fileInput">Import Schema</label>
            <input id="fileInput" type="file" accept=".txt,text/plain">
            <button id="sampleButton" type="button">Sample</button>
            <button id="clearButton" type="button">Clear</button>
            <button id="runButton" class="primary" type="button">Normalise</button>
          </div>
        </div>
        <textarea id="input" spellcheck="false">database schema Registry:
relation T: ssn empid name hdate phone email dept manager
nullable: empid hdate dept manager
empid -N-> dept
dept &lt;-N-&gt; manager
empid &lt;-N-&gt; hdate
ssn -&gt; name empid
ssn -&gt;&gt; phone
ssn -&gt;&gt; email
empid -&gt; ssn hdate dept
dept -&gt; manager
manager =&gt; empid</textarea>
      </section>

      <section>
        <div class="panel-head">
          <h2>Result</h2>
        </div>
        <div id="result" class="result">
          <div class="empty">Compute the combined decomposition to see the result.</div>
        </div>
      </section>
    </div>
  </main>

  <div id="helpDialog" class="help-dialog" role="dialog" aria-modal="true" aria-labelledby="helpTitle" hidden>
    <div class="help-panel">
      <div class="help-head">
        <h2 id="helpTitle" class="help-title">Help</h2>
        <button id="helpCloseButton" type="button">Close</button>
      </div>
      <div id="helpContent" class="markdown-body"></div>
    </div>
  </div>

  <div id="jointKindDialog" class="joint-kind-dialog" role="dialog" aria-modal="true" aria-labelledby="jointKindTitle" hidden>
    <div class="joint-kind-panel">
      <div class="joint-kind-head">
        <h2 id="jointKindTitle" class="joint-kind-title">Joint Kind Identifiers</h2>
        <div class="joint-kind-controls">
          <button id="jointKindCancelButton" type="button" aria-label="Cancel" title="Cancel">×</button>
          <button id="jointKindApplyButton" type="button" aria-label="Apply" title="Apply">✓</button>
        </div>
      </div>
      <div id="jointKindOptions" class="joint-kind-options"></div>
    </div>
  </div>

  <script>
    const input = document.getElementById('input');
    const result = document.getElementById('result');
    const statusEl = document.getElementById('status');
    const helpButton = document.getElementById('helpButton');
    const helpDialog = document.getElementById('helpDialog');
    const helpCloseButton = document.getElementById('helpCloseButton');
    const helpContent = document.getElementById('helpContent');
    const jointKindDialog = document.getElementById('jointKindDialog');
    const jointKindOptions = document.getElementById('jointKindOptions');
    const jointKindCancelButton = document.getElementById('jointKindCancelButton');
    const jointKindApplyButton = document.getElementById('jointKindApplyButton');
    let activeData = null;
    let cnfState = null;
    let helpMarkdown = null;
    let activeJointKindDialog = null;
    const sectionCollapseState = {};
    const kindIdentifierDraftSelections = new Map();

    const sample = `database schema Registry:
relation T: ssn empid name hdate phone email dept manager
nullable: empid hdate dept manager
empid -N-> dept
dept <-N-> manager
empid <-N-> hdate
ssn -> name empid
ssn ->> phone
ssn ->> email
empid -> ssn hdate dept
dept -> manager
manager => empid`;

    function escapeHtml(value) {
      return String(value)
        .replaceAll('&', '&amp;')
        .replaceAll('<', '&lt;')
        .replaceAll('>', '&gt;')
        .replaceAll('"', '&quot;')
        .replaceAll("'", '&#039;');
    }

    function sanitizeHelpUrl(url) {
      const value = String(url || '').trim();
      if (/^(https?:|mailto:)/i.test(value)) return value;
      if (/^[./#]/.test(value)) return value;
      return '#';
    }

    function renderInlineMarkdown(value) {
      let html = escapeHtml(value);
      html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, (_, label, url) => {
        return `<a href="${escapeHtml(sanitizeHelpUrl(url))}" target="_blank" rel="noreferrer">${label}</a>`;
      });
      html = html.replace(/``([^`]+)``/g, '<code>$1</code>');
      html = html.replace(/`([^`]+)`/g, '<code>$1</code>');
      html = html.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
      html = html.replace(/\*([^*]+)\*/g, '<em>$1</em>');
      html = html.replace(/&amp;nbsp;/g, '&nbsp;');
      return html;
    }

    function renderMarkdown(markdown) {
      const lines = String(markdown || '').replace(/\r\n?/g, '\n').split('\n');
      const output = [];
      let paragraph = [];
      let listType = null;
      let codeLines = null;

      function flushParagraph() {
        if (!paragraph.length) return;
        output.push(`<p>${renderInlineMarkdown(paragraph.join(' '))}</p>`);
        paragraph = [];
      }

      function flushList() {
        if (!listType) return;
        output.push(`</${listType}>`);
        listType = null;
      }

      function openList(type) {
        if (listType === type) return;
        flushParagraph();
        flushList();
        listType = type;
        output.push(`<${type}>`);
      }

      function flushCode() {
        if (codeLines === null) return;
        output.push(`<pre><code>${escapeHtml(codeLines.join('\n'))}</code></pre>`);
        codeLines = null;
      }

      for (const line of lines) {
        if (/^\s*```/.test(line)) {
          if (codeLines === null) {
            flushParagraph();
            flushList();
            codeLines = [];
          } else {
            flushCode();
          }
          continue;
        }
        if (codeLines !== null) {
          codeLines.push(line);
          continue;
        }

        if (!line.trim()) {
          flushParagraph();
          flushList();
          continue;
        }

        const heading = line.match(/^(#{1,6})\s+(.*)$/);
        if (heading) {
          flushParagraph();
          flushList();
          const level = heading[1].length;
          output.push(`<h${level}>${renderInlineMarkdown(heading[2])}</h${level}>`);
          continue;
        }

        const unordered = line.match(/^\s*[-*]\s+(.*)$/);
        if (unordered) {
          openList('ul');
          output.push(`<li>${renderInlineMarkdown(unordered[1])}</li>`);
          continue;
        }

        const ordered = line.match(/^\s*\d+\.\s+(.*)$/);
        if (ordered) {
          openList('ol');
          output.push(`<li>${renderInlineMarkdown(ordered[1])}</li>`);
          continue;
        }

        flushList();
        paragraph.push(line.trim());
      }

      flushParagraph();
      flushList();
      flushCode();
      return output.join('');
    }

    async function showHelp() {
      helpDialog.hidden = false;
      helpContent.innerHTML = '<p>Loading help...</p>';
      helpCloseButton.focus();
      try {
        if (helpMarkdown === null) {
          const response = await fetch('/api/help', {cache: 'no-store'});
          if (!response.ok) throw new Error(`Help request failed (${response.status})`);
          helpMarkdown = await response.text();
        }
        helpContent.innerHTML = renderMarkdown(helpMarkdown);
      } catch (error) {
        helpContent.innerHTML = `<p>${escapeHtml(error.message)}</p>`;
      }
    }

    function closeHelp() {
      helpDialog.hidden = true;
      helpButton.focus();
    }

    function selectedJointKindIdentifierIndexes() {
      return [...jointKindOptions.querySelectorAll('input[type="checkbox"]:checked')]
        .map(input => Number.parseInt(input.dataset.jointKindIndex || '', 10))
        .filter(Number.isInteger);
    }

    function closeJointKindIdentifierDialog(selected) {
      const active = activeJointKindDialog;
      if (!active) return;
      activeJointKindDialog = null;
      jointKindDialog.hidden = true;
      jointKindOptions.innerHTML = '';
      active.resolve(selected);
    }

    function confirmJointKindIdentifierDialog() {
      closeJointKindIdentifierDialog(selectedJointKindIdentifierIndexes());
    }

    function jointKindIdentifierChoiceGroupKey(identifiers) {
      return unique((identifiers || [])
        .map(kindIdentifierDisplayKey)
        .filter(Boolean))
        .sort((left, right) => left.localeCompare(right, undefined, {numeric: true}))
        .join('\u0002');
    }

    function jointKindIdentifierChoiceGroupLabel(identifiers) {
      const labelsByKey = new Map();
      for (const attrs of uniqueAttributeSets(identifiers || [])) {
        const key = kindIdentifierDisplayKey(attrs);
        if (!key || labelsByKey.has(key)) continue;
        labelsByKey.set(key, jointKindIdentifierChoiceLabel(attrs));
      }
      return [...labelsByKey.entries()]
        .sort((left, right) => left[1].localeCompare(right[1], undefined, {numeric: true}))
        .map(([, label]) => label)
        .join(', ');
    }

    function makeJointKindIdentifierChoice(identifiers) {
      const attrs = uniqueAttributeSets(identifiers || []);
      const key = jointKindIdentifierChoiceGroupKey(attrs);
      if (!key) return null;
      return {
        key,
        label: jointKindIdentifierChoiceGroupLabel(attrs),
        identifiers: attrs,
      };
    }

    function showJointKindIdentifierDialog(choices) {
      if (!choices.length) return Promise.resolve([]);
      if (activeJointKindDialog) closeJointKindIdentifierDialog(null);

      jointKindOptions.innerHTML = choices.map((choice, index) => {
        return `<label class="joint-kind-option">
          <input type="checkbox" data-joint-kind-index="${index}">
          <span>${escapeHtml(choice.label)}</span>
        </label>`;
      }).join('');
      jointKindDialog.hidden = false;

      return new Promise(resolve => {
        activeJointKindDialog = {resolve};
        const firstChoice = jointKindOptions.querySelector('input[type="checkbox"]');
        (firstChoice || jointKindApplyButton).focus();
      });
    }

    function fmtSet(values) {
      if (!values || values.length === 0) return '{}';
      return values.join(values.some(value => value.length > 1) ? ', ' : '');
    }

    function chips(items, cls = '') {
      if (!items || items.length === 0) return '<span class="chip">none</span>';
      return items.map(item => `<span class="chip ${cls}">${escapeHtml(item)}</span>`).join('');
    }

    function unique(items) {
      return Array.from(new Set((items || []).filter(item => item !== undefined && item !== null && String(item).length)));
    }

    function uniqueAttributeSets(items) {
      const out = [];
      const seen = new Set();
      for (const item of items || []) {
        const attrs = (item || []).filter(attr => attr !== undefined && attr !== null && String(attr).length);
        const key = canonicalAttributes(attrs);
        if (!key || seen.has(key)) continue;
        seen.add(key);
        out.push(attrs);
      }
      return out;
    }

    function normalizedDependencyText(value) {
      return String(value).trim().replace(/\s+/g, ' ').replace(/\s*,\s*/g, ', ');
    }

    function dependencyKey(item) {
      const split = splitDependencyText(item);
      if (!split) return normalizedDependencyText(item);
      return `${normalizedDependencyText(split.lhs)} ${split.symbol} ${normalizedDependencyText(split.rhs)}`;
    }

    function uniqueDependencies(items) {
      const out = [];
      const seen = new Set();
      for (const item of items || []) {
        if (item === undefined || item === null || !String(item).trim().length) continue;
        const key = dependencyKey(item);
        if (seen.has(key)) continue;
        seen.add(key);
        out.push(item);
      }
      return out;
    }

    function dependencyChips(items) {
      return chips(uniqueDependencies(items), 'dep');
    }

    function uniqueInclusionDependencies(items) {
      const out = [];
      const seen = new Set();
      for (const item of items || []) {
        const key = dependencyKey(typeof item === 'string' ? item : inclusionText(item));
        if (seen.has(key)) continue;
        seen.add(key);
        out.push(item);
      }
      return out;
    }

    function dedupeDependencyFields(item) {
      if (!item) return item;
      const out = {...item};
      for (const key of ['sql_null_dependencies', 'fds', 'mvds', 'applicable_sql_null_dependencies', 'applicable_mvds']) {
        if (Array.isArray(out[key])) out[key] = uniqueDependencies(out[key]);
      }
      if (Array.isArray(out.inclusion_dependencies)) {
        out.inclusion_dependencies = uniqueInclusionDependencies(out.inclusion_dependencies);
      }
      return out;
    }

    function attrSet(values) {
      return new Set(values || []);
    }

    function isSubset(values, set) {
      return (values || []).every(value => set.has(value));
    }

    function relationNameFor(attributes) {
      if (!attributes || attributes.length === 0) return '{}';
      return [...attributes].sort((a, b) => a.localeCompare(b, undefined, {numeric: true})).join('_');
    }

    const keyAttributeColors = [
      {bg: '#d8f3dc', border: '#65b875'},
      {bg: '#ffe0e0', border: '#df8585'},
      {bg: '#dceeff', border: '#7aaee8'},
    ];
    const kindIdentifierBorderColors = [
      {border: '#7c3aed', ring: 'rgba(124, 58, 237, 0.22)'},
      {border: '#d97706', ring: 'rgba(217, 119, 6, 0.22)'},
      {border: '#2563eb', ring: 'rgba(37, 99, 235, 0.22)'},
      {border: '#be123c', ring: 'rgba(190, 18, 60, 0.2)'},
      {border: '#047857', ring: 'rgba(4, 120, 87, 0.2)'},
    ];

    function keyAttributeColor(index) {
      return keyAttributeColors[index % keyAttributeColors.length];
    }

    function keyAttributeStyle(color) {
      if (!color) return '';
      return `--key-bg:${color.bg};--key-border:${color.border}`;
    }

    function kindIdentifierBorderColor(index) {
      return kindIdentifierBorderColors[index % kindIdentifierBorderColors.length];
    }

    function kindIdentifierStyle(color) {
      if (!color) return '';
      return `--kind-border:${color.border};--kind-ring:${color.ring}`;
    }

    function disjointKeyGroups(keyConstraints = []) {
      const keys = uniqueAttributeSets(keyConstraints)
        .map(attrs => unique(attrs))
        .filter(attrs => attrs.length)
        .sort((left, right) => {
          if (left.length !== right.length) return left.length - right.length;
          return canonicalAttributes(left).localeCompare(canonicalAttributes(right), undefined, {numeric: true});
        });
      const used = new Set();
      const groups = [];
      for (const attrs of keys) {
        if (attrs.some(attr => used.has(attr))) continue;
        groups.push(attrs);
        for (const attr of attrs) used.add(attr);
      }
      return groups.length > 1 ? groups : [];
    }

    function keyAttributeStyleMap(attributes, keyConstraints = []) {
      const styles = new Map();
      for (const attr of (keyConstraints || []).flatMap(attrs => attrs || [])) {
        if ((attributes || []).includes(attr)) styles.set(attr, keyAttributeColor(0));
      }

      for (const [index, attrs] of disjointKeyGroups(keyConstraints).entries()) {
        const color = keyAttributeColor(index);
        for (const attr of attrs) {
          if ((attributes || []).includes(attr)) styles.set(attr, color);
        }
      }
      return styles;
    }

    function renderAttributes(attributes, nullable = [], keyConstraints = []) {
      if (!attributes || attributes.length === 0) return '<span class="dep-list-empty">none</span>';
      const nullableSet = attrSet(nullable);
      const keyStyles = keyAttributeStyleMap(attributes, keyConstraints);
      return `<div class="attribute-list">${attributes.map(attribute => {
        const nullableMark = nullableSet.has(attribute) ? '<sup>N</sup>' : '';
        const keyStyle = keyAttributeStyle(keyStyles.get(attribute));
        const cls = keyStyle ? 'attribute-token key-attribute' : 'attribute-token';
        const style = keyStyle ? ` style="${escapeHtml(keyStyle)}"` : '';
        return `<span class="${cls}"${style}>${escapeHtml(attribute)}${nullableMark}</span>`;
      }).join('')}</div>`;
    }

    function normalizedOriginalAttributes(relation) {
      const attributes = relation && Array.isArray(relation.attributes)
        ? relation.attributes.map(String)
        : [];
      const originals = relation && Array.isArray(relation.original_attributes)
        ? relation.original_attributes.map(String)
        : [];
      if (originals.length === attributes.length) return originals;
      return attributes.map((attribute, index) => originals[index] || attribute);
    }

    function ensureRelationOriginalNames(relation) {
      if (!relation) return relation;
      if (!relation.original_name) {
        relation.original_name = relation.name || relationNameFor(relation.attributes || []);
      }
      relation.original_attributes = normalizedOriginalAttributes(relation);
      return relation;
    }

    function relationOriginalName(relation) {
      return (relation && relation.original_name)
        ? relation.original_name
        : (relation && relation.name) || '';
    }

    function relationOriginalAttribute(relation, index, attribute) {
      const originals = normalizedOriginalAttributes(relation);
      return originals[index] || attribute;
    }

    function originalNameTitle(originalName, currentName) {
      return originalName && originalName !== currentName
        ? ` title="Original name: ${escapeHtml(originalName)}"`
        : '';
    }

    function cloneCnf(source) {
      const cnf = JSON.parse(JSON.stringify(source || {}));
      return {
        name: cnf.name || 'CNF',
        relations: (cnf.relations || []).map(relation => ensureRelationOriginalNames(relation)),
        cross_relation_inclusion_dependencies: cnf.cross_relation_inclusion_dependencies || [],
      };
    }

    function cnfSnapshot(source) {
      const cnf = cloneCnf(source);
      return JSON.stringify({
        name: 'CNF',
        relations: cnf.relations,
        cross_relation_inclusion_dependencies: cnf.cross_relation_inclusion_dependencies,
      });
    }

    function isCnfDirty() {
      if (!activeData || !cnfState) return false;
      const savedCnf = activeData.CNF || activeData['6NF'] || {};
      return cnfSnapshot(cnfState) !== cnfSnapshot(savedCnf);
    }

    function isPendingCnfRelationRenameSavable(oldName, requestedName) {
      const cleanName = String(requestedName || '').trim();
      if (!cleanName || cleanName === oldName || !cnfState) return false;
      const names = (cnfState.relations || []).map(relation => relation.name);
      if (!names.includes(oldName)) return names.includes(cleanName);
      return !names.some(name => name === cleanName && name !== oldName);
    }

    function isPendingCnfAttributeRenameSavable(oldAttribute, requestedName) {
      const trimmed = String(requestedName || '').trim();
      if (!trimmed || !cnfState) return false;
      const oldBase = attributeParts(oldAttribute).base;
      const newBase = newBaseForAttribute(oldAttribute, trimmed);
      if (!newBase || newBase === oldBase) return false;
      const attributes = allCnfAttributes(cnfState);
      const oldBaseExists = attributes.some(attribute => attributeParts(attribute).base === oldBase);
      if (!oldBaseExists) {
        return attributes.some(attribute => attributeParts(attribute).base === newBase);
      }
      return canRenameCnfAttribute(cnfState, oldBase, newBase);
    }

    function pendingCnfInputState() {
      let savable = false;
      let invalid = false;
      for (const control of result.querySelectorAll('[data-cnf-action]')) {
        const original = control.dataset.cnfRelation || control.dataset.cnfAttribute || '';
        const requested = String(control.value || '').trim();
        if (requested === String(original)) continue;
        let valid = false;
        if (control.dataset.cnfAction === 'rename-relation') {
          valid = isPendingCnfRelationRenameSavable(control.dataset.cnfRelation || '', requested);
        }
        if (control.dataset.cnfAction === 'rename-attribute') {
          valid = isPendingCnfAttributeRenameSavable(control.dataset.cnfAttribute || '', requested);
        }
        savable = savable || valid;
        invalid = invalid || !valid;
      }
      return {savable, invalid};
    }

    function cnfSaveButtonState(options = {}) {
      if (!activeData || !cnfState) {
        return {applicable: false, key: 'unavailable', label: 'Unavailable', title: 'No CNF available'};
      }
      const includePending = options.includePending !== false;
      const pending = includePending ? pendingCnfInputState() : {savable: false, invalid: false};
      if (pending.invalid) {
        return {applicable: false, key: 'invalid', label: 'Invalid', title: 'Fix Conceptual names before saving'};
      }
      if (isCnfDirty() || pending.savable) {
        return {applicable: true, key: 'dirty', label: 'Save CNF', title: 'Save Conceptual renamings into CNF'};
      }
      return {applicable: false, key: 'saved', label: 'Saved', title: 'No CNF changes to save'};
    }

    function renderCnfSaveButton() {
      const state = cnfSaveButtonState({includePending: false});
      return `<button class="primary cnf-save-button" type="button" data-cnf-save="true" data-cnf-save-state="${escapeHtml(state.key)}" title="${escapeHtml(state.title)}"${state.applicable ? '' : ' disabled'}>${escapeHtml(state.label)}</button>`;
    }

    function createKindsButtonState(options = {}) {
      if (!activeData || !cnfState) {
        return {applicable: false, key: 'unavailable', label: 'Create Kinds', title: 'No CNF available'};
      }
      const includePending = options.includePending !== false;
      const pending = includePending ? pendingCnfInputState() : {savable: false, invalid: false};
      if (pending.invalid) {
        return {applicable: false, key: 'invalid', label: 'Create Kinds', title: 'Fix Conceptual names before creating kinds'};
      }
      const coverage = kindIdentifierCoverage(cnfState);
      if (!coverage.ok) {
        return {applicable: false, key: 'missing', label: 'Create Kinds', title: 'Every Conceptual relation must contain at least one selected kind identifier'};
      }
      if (kindRelationsInSync(cnfState)) {
        return {applicable: false, key: 'created', label: 'Kinds Created', title: 'All selected kind identifiers have kind relations'};
      }
      return {
        applicable: true,
        key: hasGeneratedKindRelations(cnfState) ? 'stale' : 'ready',
        label: hasGeneratedKindRelations(cnfState) ? 'Update Kinds' : 'Create Kinds',
        title: 'Create one kind relation for each root selected kind identifier',
      };
    }

    function renderCreateKindsButton() {
      const state = createKindsButtonState({includePending: false});
      return `<button class="create-kinds-button" type="button" data-create-kinds="true" data-create-kinds-state="${escapeHtml(state.key)}" title="${escapeHtml(state.title)}"${state.applicable ? '' : ' disabled'}>${escapeHtml(state.label)}</button>`;
    }

    function renderConceptualActions() {
      return `${renderCreateKindsButton()}${renderCnfSaveButton()}`;
    }

    function renderSixNfExportButton() {
      const available = Boolean(activeData && activeData['6NF']);
      return `<button class="export-button" type="button" data-six-nf-export="true" title="Export Sixth Normal Form as JSON"${available ? '' : ' disabled'}>Export 6NF</button>`;
    }

    function updateCnfSaveButtonState() {
      const button = result.querySelector('[data-cnf-save]');
      if (!button) return;
      const state = cnfSaveButtonState();
      button.disabled = !state.applicable;
      button.textContent = state.label;
      button.title = state.title;
      button.dataset.cnfSaveState = state.key;
    }

    function updateCreateKindsButtonState() {
      const button = result.querySelector('[data-create-kinds]');
      if (!button) return;
      const state = createKindsButtonState();
      button.disabled = !state.applicable;
      button.textContent = state.label;
      button.title = state.title;
      button.dataset.createKindsState = state.key;
    }

    function updateConceptualActionButtons() {
      updateCnfSaveButtonState();
      updateCreateKindsButtonState();
    }

    function normalFormForDisplay(form) {
      const data = cloneCnf(form);
      return {
        ...data,
        relations: (data.relations || []).map(relation => ({
          ...relation,
          attributes: relation.attributes || [],
          dependencies: uniqueDependencies(relation.dependencies || []),
        })),
        cross_relation_inclusion_dependencies: uniqueDependencies(
          data.cross_relation_inclusion_dependencies || []
        ),
      };
    }

    function regexEscape(value) {
      return String(value).replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    }

    function attributeParts(attribute) {
      const match = String(attribute || '').match(/^(.*)#(\d+)$/);
      if (!match) return {base: String(attribute || ''), suffix: ''};
      return {base: match[1], suffix: `#${match[2]}`};
    }

    function renamedAttribute(attribute, oldBase, newBase) {
      const parts = attributeParts(attribute);
      return parts.base === oldBase ? `${newBase}${parts.suffix}` : String(attribute);
    }

    function newBaseForAttribute(oldAttribute, requestedName) {
      const trimmed = String(requestedName || '').trim();
      if (!trimmed) return attributeParts(oldAttribute).base;
      return attributeParts(trimmed).base;
    }

    function allCnfAttributes(cnf) {
      return unique((cnf.relations || []).flatMap(relation => relation.attributes || []));
    }

    function dependencySideIsRelationReference(text) {
      return /^att\s*\(/i.test(String(text || '').trim());
    }

    function rewriteAttributeSide(text, knownAttributes, oldBase, newBase) {
      const attrs = parseAttributeSide(text, knownAttributes);
      if (!attrs.length) return String(text || '').trim();
      return fmtSet(attrs.map(attribute => renamedAttribute(attribute, oldBase, newBase)));
    }

    function rewriteDependencyAttributes(text, knownAttributes, oldBase, newBase) {
      const split = splitDependencyText(text);
      if (!split) return String(text);
      const lhs = rewriteAttributeSide(split.lhs, knownAttributes, oldBase, newBase);
      const rhs = dependencySideIsRelationReference(split.rhs)
        ? split.rhs
        : rewriteAttributeSide(split.rhs, knownAttributes, oldBase, newBase);
      return `${lhs} ${split.symbol} ${rhs}`;
    }

    function rewriteDependencyRelationName(text, oldName, newName) {
      const pattern = new RegExp(`att\\(\\s*${regexEscape(oldName)}\\s*\\)`, 'g');
      return String(text).replace(pattern, `att(${newName})`);
    }

    function canRenameCnfAttribute(cnf, oldBase, newBase) {
      if (oldBase === newBase) return true;
      return (cnf.relations || []).every(relation => {
        const renamed = (relation.attributes || []).map(attribute => renamedAttribute(attribute, oldBase, newBase));
        return new Set(renamed).size === renamed.length;
      });
    }

    function renameCnfRelation(oldName, newName) {
      if (!cnfState) return false;
      for (const relation of cnfState.relations || []) ensureRelationOriginalNames(relation);
      const cleanName = String(newName || '').trim();
      if (!cleanName || cleanName === oldName) return false;
      if (!(cnfState.relations || []).some(relation => relation.name === oldName)) return false;
      if ((cnfState.relations || []).some(relation => relation.name === cleanName && relation.name !== oldName)) {
        statusEl.textContent = 'Relation name already exists';
        return false;
      }

      for (const relation of cnfState.relations || []) {
        if (relation.name === oldName) relation.name = cleanName;
        relation.dependencies = (relation.dependencies || [])
          .map(dep => rewriteDependencyRelationName(dep, oldName, cleanName));
      }
      statusEl.textContent = 'Conceptual relation renamed';
      return true;
    }

    function renameCnfAttribute(oldAttribute, newName) {
      if (!cnfState) return false;
      for (const relation of cnfState.relations || []) ensureRelationOriginalNames(relation);
      const oldBase = attributeParts(oldAttribute).base;
      const newBase = newBaseForAttribute(oldAttribute, newName);
      if (!newBase || newBase === oldBase) return false;
      if (!allCnfAttributes(cnfState).some(attribute => attributeParts(attribute).base === oldBase)) return false;
      if (!canRenameCnfAttribute(cnfState, oldBase, newBase)) {
        statusEl.textContent = 'Attribute name would collide';
        return false;
      }

      const knownAttributes = allCnfAttributes(cnfState);
      const refreshGeneratedKinds = hasGeneratedKindRelations(cnfState);
      for (const relation of cnfState.relations || []) {
        const generatedAutoName = isGeneratedKindRelation(relation)
          ? rootKindRelationName([relation.attributes || []])
          : '';
        relation.attributes = (relation.attributes || [])
          .map(attribute => renamedAttribute(attribute, oldBase, newBase));
        relation.dependencies = (relation.dependencies || [])
          .map(dep => rewriteDependencyAttributes(dep, knownAttributes, oldBase, newBase));
        if (generatedAutoName && relation.name === generatedAutoName) {
          const nextGeneratedAutoName = rootKindRelationName([relation.attributes || []]);
          if (nextGeneratedAutoName && nextGeneratedAutoName !== relation.name) {
            relation.dependencies = (relation.dependencies || [])
              .map(dep => rewriteDependencyRelationName(dep, relation.name, nextGeneratedAutoName));
            relation.name = nextGeneratedAutoName;
          }
        }
        if (Array.isArray(relation.kind_identifiers)) {
          const renamedKindIdentifiers = relationKindIdentifierObjects(relation, knownAttributes)
            .map(identifier => identifier.attributes
              .map(attribute => renamedAttribute(attribute, oldBase, newBase)));
          setRelationKindIdentifierObjects(relation, renamedKindIdentifiers);
        }
      }
      cnfState.cross_relation_inclusion_dependencies = (cnfState.cross_relation_inclusion_dependencies || [])
        .map(dep => rewriteDependencyAttributes(dep, knownAttributes, oldBase, newBase));
      if (refreshGeneratedKinds) materializeKindRelations(cnfState);
      statusEl.textContent = 'Conceptual attribute renamed';
      return true;
    }

    function draftKeyForRelation(relation) {
      return relation && relation.name
        ? relation.name
        : relationNameFor(relation ? relation.attributes || [] : []);
    }

    function draftSelectionForRelation(relation) {
      return kindIdentifierDraftSelections.get(draftKeyForRelation(relation)) || new Set();
    }

    function setDraftSelectionForRelation(relation, selected) {
      const relationKey = draftKeyForRelation(relation);
      if (selected.size) {
        kindIdentifierDraftSelections.set(relationKey, selected);
      } else {
        kindIdentifierDraftSelections.delete(relationKey);
      }
    }

    function draftSelectedAttributes(relation) {
      const selected = draftSelectionForRelation(relation);
      return (relation.attributes || []).filter(attribute => selected.has(attribute));
    }

    function samePrefixAttributes(relation, base) {
      return (relation.attributes || []).filter(attribute => {
        const parts = attributeParts(attribute);
        return parts.base === base;
      });
    }

    function kindIdentifierExpansionBases(attributes) {
      const candidate = unique(attributes || []);
      if (!candidate.length) return [];
      const parts = candidate.map(attributeParts);
      if (!parts.every(part => part.base)) return [];
      return unique(parts.map(part => part.base));
    }

    function expandedKindIdentifierAttributes(cnf, attributes) {
      const selectedAttributes = new Set(unique(attributes || []));
      if (!selectedAttributes.size) return [];
      const selectedBases = new Set(kindIdentifierExpansionBases([...selectedAttributes]));
      const relations = sourceConceptualRelations(cnf || {});
      const preorderGroups = inclusionPreorderConnectedAttributeGroups(cnf || {});

      let changed = true;
      while (changed) {
        changed = false;

        for (const relation of relations) {
          for (const attribute of relation.attributes || []) {
            const parts = attributeParts(attribute);
            if (!parts.base || !selectedBases.has(parts.base) || selectedAttributes.has(attribute)) continue;
            selectedAttributes.add(attribute);
            changed = true;
          }
        }

        for (const group of preorderGroups) {
          if (!group.some(attribute => selectedAttributes.has(attribute))) continue;
          for (const attribute of group) {
            if (selectedAttributes.has(attribute)) continue;
            selectedAttributes.add(attribute);
            changed = true;
          }
        }

        for (const attribute of selectedAttributes) {
          const parts = attributeParts(attribute);
          if (!parts.base || selectedBases.has(parts.base)) continue;
          selectedBases.add(parts.base);
          changed = true;
        }
      }

      return [...selectedAttributes];
    }

    function expandedKindIdentifierCandidates(cnf, attributes) {
      const candidate = unique(attributes || []);
      if (!candidate.length) return [];
      const expandedAttributes = expandedKindIdentifierAttributes(cnf, candidate);
      const expandedSet = attrSet(expandedAttributes);
      const expanded = [];
      for (const relation of sourceConceptualRelations(cnf || {})) {
        const attrs = (relation.attributes || []).filter(attribute => expandedSet.has(attribute));
        if (attrs.length) expanded.push(unique(attrs));
      }

      return uniqueAttributeSets(expanded.length ? expanded : [candidate]);
    }

    function updateKindIdentifierDraftSelection(relation, attribute, checked) {
      const expanded = attrSet(expandedKindIdentifierAttributes(cnfState || {}, [attribute]));
      for (const sourceRelation of sourceConceptualRelations(cnfState || {})) {
        const selected = new Set(draftSelectionForRelation(sourceRelation));
        let touched = false;
        for (const candidateAttribute of sourceRelation.attributes || []) {
          if (!expanded.has(candidateAttribute)) continue;
          touched = true;
          if (checked) {
            selected.add(candidateAttribute);
          } else {
            selected.delete(candidateAttribute);
          }
        }
        if (touched) setDraftSelectionForRelation(sourceRelation, selected);
      }
    }

    function clearExpandedKindIdentifierDraft(relation, attributes) {
      const expanded = attrSet(expandedKindIdentifierAttributes(cnfState || {}, attributes));
      if (!expanded.size) {
        clearKindIdentifierDraft(relation);
        return;
      }

      for (const sourceRelation of sourceConceptualRelations(cnfState || {})) {
        const selected = new Set(draftSelectionForRelation(sourceRelation));
        let changed = false;
        for (const attribute of sourceRelation.attributes || []) {
          if (expanded.has(attribute) && selected.delete(attribute)) changed = true;
        }
        if (changed) setDraftSelectionForRelation(sourceRelation, selected);
      }
    }

    function relationHasKindIdentifier(relation, attributes) {
      const key = canonicalAttributes(attributes);
      return relationKindIdentifierObjects(relation)
        .some(item => canonicalAttributes(item.attributes || []) === key);
    }

    function relationSelectedKindIdentifiers(relation) {
      return relationKindIdentifierObjects(relation)
        .map(item => item.attributes || []);
    }

    function normalizeJointKindIdentifierGroup(group, relation) {
      if (!Array.isArray(group)) return [];
      const identifiers = group.every(item => typeof item === 'string')
        ? [normalizeKindIdentifier(group, relation.attributes || [])]
        : group.map(item => normalizeKindIdentifier(item, relation.attributes || []));
      return uniqueAttributeSets(identifiers);
    }

    function normalizeJointKindIdentifierGroups(relation) {
      return (relation.joint_kind_identifiers || [])
        .map(group => normalizeJointKindIdentifierGroup(group, relation))
        .filter(group => group.length > 1);
    }

    function setRelationJointKindIdentifierGroups(relation, groups) {
      const existing = relationKindIdentifierObjects(relation);
      const existingKeys = new Set(existing.map(item => canonicalAttributes(item.attributes || [])));
      const mergedGroups = (groups || [])
        .map(group => uniqueAttributeSets(group || [])
          .filter(attrs => existingKeys.has(canonicalAttributes(attrs))))
        .filter(group => group.length > 1)
        .map(group => unique(group.flat()));
      const groupedKeys = new Set(mergedGroups.map(canonicalAttributes));
      const ungrouped = existing
        .filter(item => !groupedKeys.has(canonicalAttributes(item.attributes || [])));
      setRelationKindIdentifierObjects(relation, [
        ...ungrouped,
        ...mergedGroups.map(makeKindIdentifier),
      ]);
    }

    function uniqueJointKindIdentifierGroups(groups) {
      const out = [];
      const seen = new Set();
      for (const group of groups || []) {
        const identifiers = uniqueAttributeSets(group || []);
        if (identifiers.length < 2) continue;
        const key = identifiers.map(canonicalAttributes)
          .sort((left, right) => left.localeCompare(right, undefined, {numeric: true}))
          .join('\u0002');
        if (seen.has(key)) continue;
        seen.add(key);
        out.push(identifiers);
      }
      return out;
    }

    function pruneRelationJointKindIdentifierGroups(relation) {
      setRelationKindIdentifierObjects(relation, relationKindIdentifierObjects(relation));
    }

    function addRelationJointKindIdentifierGroup(relation, identifiers) {
      mergeRelationKindIdentifiers(relation, identifiers);
    }

    function kindIdentifierStyleMap(relation) {
      const styles = new Map();
      const identifiers = relationSelectedKindIdentifiers(relation);
      for (const [index, item] of identifiers.entries()) {
        const color = kindIdentifierBorderColor(index);
        for (const attr of item) {
          styles.set(attr, color);
        }
      }
      return styles;
    }

    function kindIdentifierDraftActionState(relation) {
      const selected = draftSelectedAttributes(relation);
      const hasSelection = selected.length > 0;
      const relationKey = draftKeyForRelation(relation);
      const sourceRelation = sourceRelationByDraftKey(relationKey) || relation;
      const expandedCandidates = hasSelection && cnfState
        ? expandedKindIdentifierCandidates(cnfState, selected)
        : [];
      const removing = hasSelection && relationHasKindIdentifier(sourceRelation, selected);
      let disabled = !hasSelection;
      let title = hasSelection
        ? 'Add selected attributes as a kind identifier'
        : 'Select one or more attributes to add a kind identifier';

      if (hasSelection && removing) {
        title = expandedCandidates.length > 1
          ? 'Remove matching prefixed kind identifiers'
          : 'Remove the selected kind identifier';
      } else if (hasSelection && !cnfState) {
        disabled = true;
        title = 'Compute a conceptual model before adding a kind identifier';
      } else if (hasSelection) {
        const validation = validateKindIdentifierCandidateSet(cnfState, expandedCandidates);
        disabled = !validation.ok;
        title = validation.ok
          ? expandedCandidates.length > 1
            ? 'Add matching prefixed attributes as kind identifiers'
            : 'Add selected attributes as a kind identifier'
          : validation.message;
      }

      return {
        selected,
        relationKey,
        label: removing ? 'Remove Kind ID' : 'Add Kind ID',
        disabled,
        title,
        clearDisabled: !hasSelection,
        clearTitle: hasSelection
          ? 'Clear selected attributes'
          : 'No selected attributes to clear',
      };
    }

    function renderKindIdentifierRelationActions(relation) {
      const state = kindIdentifierDraftActionState(relation);
      return `<div class="kind-identifier-actions">
        <button type="button" data-kind-identifier-apply="${escapeHtml(state.relationKey)}" title="${escapeHtml(state.title)}"${state.disabled ? ' disabled' : ''}>${escapeHtml(state.label)}</button>
        <button type="button" data-kind-identifier-clear="${escapeHtml(state.relationKey)}" title="${escapeHtml(state.clearTitle)}"${state.clearDisabled ? ' disabled' : ''}>Clear</button>
      </div>`;
    }

    function renderCnfRelationInput(relation) {
      const name = relation && relation.name
        ? relation.name
        : relationNameFor(relation ? relation.attributes || [] : []);
      const originalName = relationOriginalName(relation) || name;
      return `<input class="cnf-relation-input" value="${escapeHtml(name)}" data-cnf-action="rename-relation" data-cnf-relation="${escapeHtml(name)}" data-cnf-original-relation="${escapeHtml(originalName)}" aria-label="Rename relation ${escapeHtml(name)}"${originalNameTitle(originalName, name)}>`;
    }

    function renderEditableAttributes(attributes, keyConstraints = [], relation = null, options = {}) {
      if (!attributes || attributes.length === 0) return '<span class="dep-list-empty">none</span>';
      const includeKindDraft = options.includeKindDraft !== false
        && relation
        && !isGeneratedKindRelation(relation);
      const keyStyles = keyAttributeStyleMap(attributes, keyConstraints);
      const draftSelected = includeKindDraft ? draftSelectionForRelation(relation) : new Set();
      const kindStyles = relation ? kindIdentifierStyleMap(relation) : new Map();
      return `<div class="attribute-list">${attributes.map((attribute, index) => {
        const keyStyle = keyAttributeStyle(keyStyles.get(attribute));
        const kindStyle = kindIdentifierStyle(kindStyles.get(attribute));
        const isKeyAttribute = Boolean(keyStyle);
        const isKindIdentifier = Boolean(kindStyle);
        const isDraftSelected = draftSelected.has(attribute);
        const originalAttribute = relation ? relationOriginalAttribute(relation, index, attribute) : attribute;
        const classes = ['cnf-attribute-input'];
        if (isKeyAttribute) classes.push('key-attribute');
        if (isKindIdentifier) classes.push('kind-identifier-attribute');
        const width = Math.max(6, Math.min(24, String(attribute).length + 2));
        const renderedWidth = isKindIdentifier
          ? `calc(${width}ch + 4px)`
          : `${width}ch`;
        const styleParts = [`width:${renderedWidth}`];
        if (keyStyle) styleParts.push(keyStyle);
        if (kindStyle) styleParts.push(kindStyle);
        const relationKey = relation ? draftKeyForRelation(relation) : '';
        const draftControl = includeKindDraft
          ? `<input class="kind-draft-checkbox" type="checkbox" data-kind-draft-relation="${escapeHtml(relationKey)}" data-kind-draft-attribute="${escapeHtml(attribute)}" title="Select for kind identifier"${isDraftSelected ? ' checked' : ''}>`
          : '';
        return `<span class="attribute-edit">
          ${draftControl}
          <input class="${classes.join(' ')}" style="${escapeHtml(styleParts.join(';'))}" value="${escapeHtml(attribute)}" data-cnf-action="rename-attribute" data-cnf-attribute="${escapeHtml(attribute)}" data-cnf-original-attribute="${escapeHtml(originalAttribute)}" aria-label="Rename attribute ${escapeHtml(attribute)}"${originalNameTitle(originalAttribute, attribute)}>
        </span>`;
      }).join('')}</div>`;
    }

    function renderDependencyList(dependencies) {
      const items = uniqueDependencies(dependencies);
      if (!items.length) return '<div class="dep-list-empty">none</div>';
      return `<ul class="dep-list">${items.map(dep => `<li>${escapeHtml(dep)}</li>`).join('')}</ul>`;
    }

    function renderDependencyBox(dependencies, relationName = '', attributes = []) {
      return `<div class="nested-box">${renderDependencyList(displayDependenciesForRelation(relationName, attributes, dependencies))}</div>`;
    }

    function renderCrossRelationBox(dependencies = []) {
      const content = dependencies && dependencies.length
        ? renderDependencyList(dependencies)
        : '<div class="dep-list-empty">no dependency</div>';
      return `<div class="box full">
        <h3>Cross-relation Inclusion Dependency</h3>
        ${content}
      </div>`;
    }

    function sectionKey(title) {
      return String(title || '').toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '') || 'section';
    }

    function renderSection(title, content, actions = '') {
      const key = sectionKey(title);
      const bodyId = `${key}SectionBody`;
      const isCollapsed = Boolean(sectionCollapseState[key]);
      const actionHtml = actions ? `<div class="result-section-actions">${actions}</div>` : '';
      return `<div class="result-section" data-result-section="${escapeHtml(key)}">
        <div class="result-section-heading">
          <h3 class="result-section-title">
            <button class="section-toggle" type="button" data-section-toggle="${escapeHtml(key)}" aria-expanded="${String(!isCollapsed)}" aria-controls="${escapeHtml(bodyId)}">
              <span>${escapeHtml(title)}</span>
            </button>
          </h3>
          ${actionHtml}
        </div>
        <div id="${escapeHtml(bodyId)}" class="result-section-body"${isCollapsed ? ' hidden' : ''}>${content}</div>
      </div>`;
    }

    function getSourceRelations(data) {
      const relations = [];
      for (const database of data.database_schemas || []) {
        for (const relation of database.relations || []) {
          relations.push({...relation, database_schema: database.name});
        }
      }
      if (relations.length) return relations;
      return (data.input_relations || []).map(relation => ({...relation, database_schema: ''}));
    }

    function normalizedInclusionSymbol(symbol, sourceCount) {
      if (sourceCount === 1 && symbol === 'x=>') return '=>';
      if (sourceCount === 1 && symbol === 'o=>') return '==';
      return symbol;
    }

    function inclusionSources(dep, knownAttributes = []) {
      if (dep && Array.isArray(dep.sources)) {
        return dep.sources.map(source => (source || []).map(String));
      }
      const text = typeof dep === 'string'
        ? dep
        : dep && dep.text;
      const split = text ? splitDependencyText(text) : null;
      if (split && ['==', 'o=>', 'x=>', '=>'].includes(split.symbol)) {
        return split.lhs.split('|')
          .map(source => source.trim())
          .filter(Boolean)
          .map(source => parseAttributeSide(source, knownAttributes));
      }
      return [((dep && dep.lhs) || []).map(String)];
    }

    function inclusionTarget(dep, knownAttributes = []) {
      if (dep && Array.isArray(dep.target)) return dep.target.map(String);
      const text = typeof dep === 'string'
        ? dep
        : dep && dep.text;
      const split = text ? splitDependencyText(text) : null;
      if (split && ['==', 'o=>', 'x=>', '=>'].includes(split.symbol)) {
        return parseAttributeSide(split.rhs, knownAttributes);
      }
      return ((dep && dep.rhs) || []).map(String);
    }

    function inclusionAttributes(dep, knownAttributes = []) {
      return [
        ...inclusionSources(dep, knownAttributes).flat(),
        ...inclusionTarget(dep, knownAttributes),
      ];
    }

    function inclusionSymbol(dep, knownAttributes = []) {
      const text = typeof dep === 'string'
        ? dep
        : dep && dep.text;
      const split = text ? splitDependencyText(text) : null;
      const sourceCount = inclusionSources(dep, knownAttributes).length;
      if (split && ['==', 'o=>', 'x=>', '=>'].includes(split.symbol)) {
        return normalizedInclusionSymbol(split.symbol, sourceCount);
      }
      if (dep && dep.symbol) return normalizedInclusionSymbol(dep.symbol, sourceCount);
      if (dep && dep.kind === 'equality') return '==';
      if (dep && dep.kind === 'covering') return normalizedInclusionSymbol('o=>', sourceCount);
      if (dep && dep.kind === 'disjoint') return normalizedInclusionSymbol('x=>', sourceCount);
      return '=>';
    }

    function inclusionText(dep) {
      if (typeof dep === 'string') return dep;
      const sources = inclusionSources(dep);
      const target = inclusionTarget(dep);
      return `${sources.map(fmtSet).join(' | ')} ${inclusionSymbol(dep)} ${fmtSet(target)}`;
    }

    function isLocalInclusionForAttributes(dep, attributes) {
      return isSubset(inclusionAttributes(dep, attributes || []), attrSet(attributes || []));
    }

    function isLocalInclusionForAnyRelation(dep, relations) {
      return (relations || []).some(relation => isLocalInclusionForAttributes(dep, relation.attributes || []));
    }

    function crossInclusionTextsForRelations(inclusions, relations) {
      return uniqueDependencies((inclusions || [])
        .filter(dep => !isLocalInclusionForAnyRelation(dep, relations || []))
        .map(inclusionText));
    }

    function localInclusionTextsForItem(data, item) {
      return uniqueDependencies((data.inclusion_dependencies || [])
        .filter(dep => isLocalInclusionForAttributes(dep, item.attributes || []))
        .map(inclusionText));
    }

    function detailsDisplayData(data) {
      const displayData = JSON.parse(JSON.stringify(data));
      const sourceRelations = getSourceRelations(data);
      const isLocalToSource = dep => sourceRelations.some(relation => isLocalInclusionForAttributes(dep, relation.attributes || []));

      displayData.sql_null_dependencies = uniqueDependencies(displayData.sql_null_dependencies || []);
      displayData.fds = uniqueDependencies(displayData.fds || []);
      displayData.mvds = uniqueDependencies(displayData.mvds || []);
      displayData.inclusion_dependencies = uniqueInclusionDependencies(
        (displayData.inclusion_dependencies || []).filter(isLocalToSource)
      );
      if (displayData['6NF']) {
        displayData['6NF'] = normalFormForDisplay(displayData['6NF']);
      }
      displayData.CNF = normalFormForDisplay(cnfState || displayData.CNF || displayData['6NF']);
      displayData.database_schemas = (displayData.database_schemas || []).map(database => {
        const schemaRelations = database.relations || [];
        const isLocalToSchema = dep => schemaRelations.some(relation => isLocalInclusionForAttributes(dep, relation.attributes || []));
        return {
          ...dedupeDependencyFields(database),
          relations: (database.relations || []).map(dedupeDependencyFields),
          inclusion_dependencies: uniqueInclusionDependencies(
            (database.inclusion_dependencies || []).filter(isLocalToSchema)
          ),
        };
      });
      displayData.input_relations = (displayData.input_relations || []).map(dedupeDependencyFields);
      displayData.per_input_relation = (displayData.per_input_relation || []).map(item => {
        const applicableInclusions = localInclusionTextsForItem(data, item);
        return {
          ...dedupeDependencyFields(item),
          applicable_sql_null_dependencies: uniqueDependencies(item.applicable_sql_null_dependencies || []),
          applicable_fds: displayDependenciesForRelation(item.input_relation, item.attributes || [], item.applicable_fds || []),
          applicable_mvds: uniqueDependencies(item.applicable_mvds || []),
          applicable_inclusion_dependencies: uniqueDependencies(applicableInclusions),
          per_relation_4nf: (item.per_relation_4nf || []).map(perRelation => ({
            ...dedupeDependencyFields(perRelation),
            applicable_fds: displayDependenciesForRelation(
              perRelation.sql_null_relation_name || '',
              perRelation.renamed_sql_null_relation || perRelation.sql_null_relation || [],
              perRelation.applicable_fds || []
            ),
            applicable_mvds: uniqueDependencies(perRelation.applicable_mvds || []),
            steps: displayStepsForRelation(perRelation.steps || [], perRelation.sql_null_relation_name || ''),
          })),
        };
      });
      return displayData;
    }

    function displayDependenciesForRelation(relationName, attributes, dependencies) {
      const items = uniqueDependencies(dependencies);
      if (!items.length || !attributes || !attributes.length) return items;

      const targetAttrs = attrSet(attributes);
      const functionalDependencies = items
        .map((text, index) => ({text, index, dep: functionalDependencyParts(text, attributes)}))
        .filter(item => item.dep && isSubset([...item.dep.lhs, ...item.dep.rhs], targetAttrs));
      if (!functionalDependencies.length) return items;

      const parsedFds = functionalDependencies.map(item => item.dep);
      const keyGroups = new Map();
      const fdGroups = new Map();
      for (const item of functionalDependencies) {
        const key = canonicalAttributes(item.dep.lhs);
        if (isSubset(attributes, closure(item.dep.lhs, parsedFds))) {
          if (!keyGroups.has(key)) {
            keyGroups.set(key, {
              lhs: item.dep.lhs,
              indexes: new Set(),
            });
          }
          keyGroups.get(key).indexes.add(item.index);
          continue;
        }

        if (!fdGroups.has(key)) {
          fdGroups.set(key, {
            lhs: item.dep.lhs,
            rhs: [],
            indexes: new Set(),
          });
        }
        const group = fdGroups.get(key);
        group.indexes.add(item.index);
        for (const attr of item.dep.rhs) {
          if (!group.rhs.includes(attr)) group.rhs.push(attr);
        }
      }
      for (const [key, group] of Array.from(fdGroups.entries())) {
        if (group.indexes.size < 2) fdGroups.delete(key);
      }
      if (!keyGroups.size && !fdGroups.size) return items;

      const indexToGroup = new Map();
      for (const [key, group] of keyGroups.entries()) {
        for (const index of group.indexes) indexToGroup.set(index, {kind: 'key', key});
      }
      for (const [key, group] of fdGroups.entries()) {
        for (const index of group.indexes) indexToGroup.set(index, {kind: 'fd', key});
      }

      const displayed = [];
      const emittedGroups = new Set();
      for (let index = 0; index < items.length; index += 1) {
        const groupRef = indexToGroup.get(index);
        if (!groupRef) {
          displayed.push(items[index]);
          continue;
        }
        const emittedKey = `${groupRef.kind}\u0002${groupRef.key}`;
        if (emittedGroups.has(emittedKey)) continue;

        if (groupRef.kind === 'key') {
          const group = keyGroups.get(groupRef.key);
          const name = relationName || relationNameFor(attributes);
          displayed.push(`${fmtSet(group.lhs)} -> att(${name})`);
        } else {
          const group = fdGroups.get(groupRef.key);
          displayed.push(`${fmtSet(group.lhs)} -> ${fmtSet(group.rhs)}`);
        }
        emittedGroups.add(emittedKey);
      }
      return uniqueDependencies(displayed);
    }

    function stepDependencyText(step) {
      const symbol = step.dependency_kind === 'MVD' ? '->>' : '->';
      return `${fmtSet(step.dependency_lhs || [])} ${symbol} ${fmtSet(step.dependency_rhs || [])}`;
    }

    function displayStepsForRelation(steps, relationName = '') {
      const items = steps || [];
      if (!items.length) return items;

      const fdSteps = items
        .map((step, index) => ({step, index}))
        .filter(item => item.step.dependency_kind === 'FD');
      if (!fdSteps.length) return items;

      const byRelation = new Map();
      for (const item of fdSteps) {
        const relationKey = canonicalAttributes(item.step.relation || []);
        if (!byRelation.has(relationKey)) byRelation.set(relationKey, []);
        byRelation.get(relationKey).push(item);
      }

      const groups = new Map();
      const indexToGroup = new Map();
      for (const relationItems of byRelation.values()) {
        const relation = relationItems[0].step.relation || [];
        const fds = relationItems.map(item => ({
          lhs: item.step.dependency_lhs || [],
          rhs: item.step.dependency_rhs || [],
        }));
        for (const item of relationItems) {
          const lhs = item.step.dependency_lhs || [];
          if (!isSubset(relation, closure(lhs, fds))) continue;

          const groupKey = `${canonicalAttributes(relation)}\u0002${canonicalAttributes(lhs)}`;
          if (!groups.has(groupKey)) {
            groups.set(groupKey, {
              relation,
              lhs,
              indexes: new Set(),
              result: [],
              template: item.step,
            });
          }
          const group = groups.get(groupKey);
          group.indexes.add(item.index);
          for (const resultRelation of item.step.result || []) group.result.push(resultRelation);
        }
      }
      if (!groups.size) return items;

      for (const [groupKey, group] of groups.entries()) {
        for (const index of group.indexes) indexToGroup.set(index, groupKey);
      }

      const displayed = [];
      const emittedGroups = new Set();
      for (let index = 0; index < items.length; index += 1) {
        const groupKey = indexToGroup.get(index);
        if (!groupKey) {
          displayed.push(items[index]);
          continue;
        }
        if (emittedGroups.has(groupKey)) continue;

        const group = groups.get(groupKey);
        const name = relationName || fmtSet(group.relation);
        const resultKeys = unique(group.result.map(canonicalAttributes));
        displayed.push({
          ...group.template,
          dependency: `${fmtSet(group.lhs)} -> att(${name})`,
          dependency_lhs: group.lhs,
          dependency_rhs: group.relation,
          result: resultKeys.map(key => group.result.find(relation => canonicalAttributes(relation) === key) || []),
        });
        emittedGroups.add(groupKey);
      }
      return displayed;
    }

    function renderSource(data) {
      const relations = getSourceRelations(data);
      const perInput = new Map((data.per_input_relation || []).map(item => [item.input_relation, item]));
      const crossInclusions = crossInclusionTextsForRelations(data.inclusion_dependencies || [], relations);
      const relationBoxes = relations.map(relation => {
        const item = perInput.get(relation.name) || {};
        const relationAttrs = attrSet(relation.attributes || []);
        const localInclusions = (data.inclusion_dependencies || [])
          .filter(dep => isSubset(inclusionAttributes(dep, relation.attributes || []), relationAttrs))
          .map(inclusionText);
        const dependencies = uniqueDependencies([
          ...(item.applicable_sql_null_dependencies || []),
          ...(item.applicable_fds || []),
          ...(item.applicable_mvds || []),
          ...localInclusions,
        ]);
        const keyConstraints = relationKeyConstraints(relation.attributes || [], dependencies);
        return `<div class="box relation-box">
          <h3>${escapeHtml(relation.name)}</h3>
          ${renderAttributes(relation.attributes || [], relation.nullable || [], keyConstraints)}
          ${renderDependencyBox(dependencies, relation.name, relation.attributes || [])}
        </div>`;
      }).join('');
      return `<div class="grid relation-grid">${relationBoxes}${renderCrossRelationBox(crossInclusions)}</div>`;
    }

    function canonicalAttributes(attributes) {
      return [...(attributes || [])].sort((a, b) => a.localeCompare(b, undefined, {numeric: true})).join('\u0001');
    }

    function splitDependencyText(text) {
      for (const symbol of ['->>N<<-', '<-N->', '->N<-', '-N->', '->>', 'o=>', 'x=>', '==', '->', '=>']) {
        const index = String(text).indexOf(symbol);
        if (index !== -1) {
          return {
            lhs: String(text).slice(0, index).trim(),
            symbol,
            rhs: String(text).slice(index + symbol.length).trim(),
          };
        }
      }
      return null;
    }

    function parseAttributeSide(text, knownAttributes = []) {
      let value = String(text || '').trim();
      if (!value || value === '{}' || value === '∅') return [];
      const knownSet = attrSet(knownAttributes);
      if (knownSet.has(value)) return [value];
      if (/^att\s*\(/i.test(value)) return [...knownSet];
      value = value.replace(/^\{|\}$/g, '').replace(/^\[|\]$/g, '').replace(/^\(|\)$/g, '');
      if (knownSet.has(value)) return [value];
      if (value.includes(',') || /\s/.test(value)) {
        return value.split(/[\s,]+/).map(token => token.trim()).filter(Boolean);
      }
      return [...value];
    }

    function functionalDependencyParts(dependency, knownAttributes) {
      const split = splitDependencyText(dependency);
      if (!split || split.symbol !== '->') return null;
      return {
        lhs: parseAttributeSide(split.lhs, knownAttributes),
        rhs: parseAttributeSide(split.rhs, knownAttributes),
      };
    }

    function inclusionDependencyParts(dependency, knownAttributes = []) {
      const text = typeof dependency === 'string'
        ? dependency
        : inclusionText(dependency);
      const split = splitDependencyText(text);
      if (!split || !['=>', '==', 'o=>', 'x=>'].includes(split.symbol)) return null;
      const lhsSources = inclusionSources(dependency, knownAttributes)
        .map(source => source.map(String));
      const rhs = inclusionTarget(dependency, knownAttributes).map(String);
      const symbol = normalizedInclusionSymbol(split.symbol, lhsSources.length);
      const normalizedText = `${lhsSources.map(fmtSet).join(' | ')} ${symbol} ${fmtSet(rhs)}`;
      return {
        symbol,
        lhs: lhsSources[0] || [],
        rhs,
        target: rhs,
        lhsSources,
        sources: lhsSources,
        text: normalizedText,
      };
    }

    function closure(attributes, functionalDependencies) {
      const result = attrSet(attributes);
      let changed = true;
      while (changed) {
        changed = false;
        for (const dep of functionalDependencies) {
          if (!isSubset(dep.lhs, result)) continue;
          for (const attr of dep.rhs) {
            if (!result.has(attr)) {
              result.add(attr);
              changed = true;
            }
          }
        }
      }
      return result;
    }

    function relationKeyConstraints(attributes, dependencies) {
      const targetAttrs = attrSet(attributes);
      const functionalDependencies = uniqueDependencies(dependencies)
        .map(dep => functionalDependencyParts(dep, attributes))
        .filter(dep => dep && isSubset([...dep.lhs, ...dep.rhs], targetAttrs));
      const keys = [];
      const seen = new Set();
      for (const dep of functionalDependencies) {
        if (isSubset(attributes, closure(dep.lhs, functionalDependencies))) {
          const key = canonicalAttributes(dep.lhs);
          if (key && !seen.has(key)) {
            seen.add(key);
            keys.push(dep.lhs);
          }
        }
      }
      return keys;
    }

    function relationKeyAttributes(attributes, dependencies) {
      const keyAttrs = new Set();
      for (const keyAttrsForRelation of relationKeyConstraints(attributes, dependencies)) {
        for (const attr of keyAttrsForRelation) keyAttrs.add(attr);
      }
      return Array.from(keyAttrs);
    }

    function normalizeKindIdentifier(value, knownAttributes = []) {
      if (value && typeof value === 'object' && Array.isArray(value.attributes)) {
        return value.attributes.map(String).filter(Boolean);
      }
      if (Array.isArray(value)) return value.map(String).filter(Boolean);
      return parseAttributeSide(value, knownAttributes);
    }

    function makeKindIdentifier(attributes) {
      const attrs = unique(attributes || [])
        .sort((left, right) => {
          const leftParts = attributeParts(left);
          const rightParts = attributeParts(right);
          const prefixOrder = leftParts.base.localeCompare(rightParts.base, undefined, {numeric: true});
          if (prefixOrder) return prefixOrder;
          return String(left).localeCompare(String(right), undefined, {numeric: true});
        });
      return {
        name: kindIdentifierName(attrs),
        attributes: attrs,
      };
    }

    function relationKindIdentifierObjects(relation, knownAttributes = []) {
      const identifiersByKey = new Map();
      const parent = new Map();

      function ensure(attributes) {
        const attrs = unique(attributes || []);
        const key = canonicalAttributes(attrs);
        if (!key) return '';
        if (!identifiersByKey.has(key)) identifiersByKey.set(key, attrs);
        if (!parent.has(key)) parent.set(key, key);
        return key;
      }

      function find(key) {
        if (!key) return '';
        const next = parent.get(key);
        if (!next) return '';
        if (next === key) return key;
        const root = find(next);
        parent.set(key, root);
        return root;
      }

      function union(left, right) {
        const leftRoot = find(left);
        const rightRoot = find(right);
        if (leftRoot && rightRoot && leftRoot !== rightRoot) parent.set(rightRoot, leftRoot);
      }

      for (const item of relation.kind_identifiers || []) {
        ensure(normalizeKindIdentifier(item, knownAttributes.length ? knownAttributes : relation.attributes || []));
      }

      for (const group of normalizeJointKindIdentifierGroups(relation)) {
        const keys = group.map(ensure).filter(Boolean);
        for (let index = 1; index < keys.length; index += 1) {
          union(keys[0], keys[index]);
        }
      }

      const groups = new Map();
      for (const key of parent.keys()) {
        const root = find(key);
        if (!root) continue;
        if (!groups.has(root)) groups.set(root, []);
        groups.get(root).push(identifiersByKey.get(key));
      }

      const out = [];
      const seen = new Set();
      for (const group of groups.values()) {
        const identifier = makeKindIdentifier(unique(group.flat()));
        const key = canonicalAttributes(identifier.attributes || []);
        if (!key || seen.has(key)) continue;
        seen.add(key);
        out.push(identifier);
      }
      return out.sort((left, right) => left.name.localeCompare(right.name, undefined, {numeric: true}));
    }

    function setRelationKindIdentifierObjects(relation, identifiers) {
      const byKey = new Map();
      for (const item of identifiers || []) {
        const identifier = makeKindIdentifier(
          item && typeof item === 'object' && Array.isArray(item.attributes)
            ? item.attributes
            : item
        );
        const key = canonicalAttributes(identifier.attributes || []);
        if (!key || byKey.has(key)) continue;
        byKey.set(key, identifier);
      }
      const normalized = [...byKey.values()]
        .sort((left, right) => left.name.localeCompare(right.name, undefined, {numeric: true}));
      if (normalized.length) {
        relation.kind_identifiers = normalized;
      } else {
        delete relation.kind_identifiers;
      }
      delete relation.joint_kind_identifiers;
    }

    function mergeRelationKindIdentifiers(relation, identifiers) {
      const incoming = uniqueAttributeSets(identifiers || []);
      if (!incoming.length) return;

      const incomingKeys = new Set(incoming.map(canonicalAttributes));
      const existing = relationKindIdentifierObjects(relation);
      const mergedAttributes = unique([
        ...incoming.flat(),
        ...existing
          .filter(item => incomingKeys.has(canonicalAttributes(item.attributes || [])))
          .flatMap(item => item.attributes || []),
      ]);
      const rest = existing
        .filter(item => !incomingKeys.has(canonicalAttributes(item.attributes || [])));
      setRelationKindIdentifierObjects(relation, [
        ...rest,
        makeKindIdentifier(mergedAttributes),
      ]);
    }

    function isGeneratedKindRelation(relation) {
      return Boolean(relation && relation.generated_kind_relation);
    }

    function hasGeneratedKindRelations(cnf) {
      return (cnf.relations || []).some(isGeneratedKindRelation);
    }

    function sourceConceptualRelations(cnf) {
      return (cnf.relations || []).filter(relation => !isGeneratedKindRelation(relation));
    }

    function relationContainsKindIdentifier(relation, kindIdentifierSets) {
      const relationAttrs = attrSet(relation.attributes || []);
      return (kindIdentifierSets || [])
        .some(attrs => attrs.length && attrs.some(attribute => relationAttrs.has(attribute)));
    }

    function kindIdentifierCoverage(cnf) {
      const kindIdentifierSets = selectedKindIdentifierSets(cnf);
      const missing = [];
      for (const relation of sourceConceptualRelations(cnf)) {
        if (relationContainsKindIdentifier(relation, kindIdentifierSets)) {
          continue;
        }
        missing.push(relation.name || relationNameFor(relation.attributes || []));
      }
      return {
        ok: missing.length === 0,
        missing,
      };
    }

    function kindIdentifierStatusText(cnf) {
      const coverage = kindIdentifierCoverage(cnf);
      if (coverage.ok) {
        const items = jointKindIdentifierSummaryItems(cnf);
        return `Kind identifiers: ${items.join('; ') || 'none'}`;
      }
      return `Missing kind identifier: ${coverage.missing.join(', ')}`;
    }

    function relationContainsAttributes(relation, attributes) {
      return isSubset(attributes, attrSet(relation.attributes || []));
    }

    function kindIdentifierKeyCompatible(relation, attributes) {
      const candidate = attrSet(attributes || []);
      const keys = relationKeyConstraints(relation.attributes || [], relation.dependencies || []);
      if (!keys.length) return true;
      const candidateKey = canonicalAttributes(attributes || []);
      if (keys.some(keyAttrs => canonicalAttributes(keyAttrs) === candidateKey)) return true;
      return keys.every(keyAttrs => {
        const keySet = attrSet(keyAttrs);
        const isWithinKey = isSubset(attributes, keySet);
        const isDisjointFromKey = keyAttrs.every(attribute => !candidate.has(attribute));
        return isWithinKey || isDisjointFromKey;
      });
    }

    function inclusionDependenciesForKindIdentifiers(cnf) {
      const dependencies = [];
      for (const relation of sourceConceptualRelations(cnf)) {
        dependencies.push(...(relation.dependencies || []));
      }
      dependencies.push(...(cnf.cross_relation_inclusion_dependencies || []));

      if (activeData) {
        dependencies.push(...(activeData.inclusion_dependencies || []));
        for (const database of activeData.database_schemas || []) {
          dependencies.push(...(database.inclusion_dependencies || []));
          for (const relation of database.relations || []) {
            dependencies.push(...(relation.inclusion_dependencies || []));
          }
        }
      }
      return dependencies;
    }

    function inclusionDependencySidesForKindIdentifiers(cnf) {
      const knownAttributes = allCnfAttributes(cnf);
      const knownSet = attrSet(knownAttributes);
      const sides = [];
      const seen = new Set();
      for (const dependency of inclusionDependenciesForKindIdentifiers(cnf)) {
        const parsed = inclusionDependencyParts(dependency, knownAttributes);
        if (!parsed) continue;
        const sidesForDependency = [
          ...parsed.lhsSources.map(attrs => ['source', attrs]),
          ['target', parsed.rhs],
        ];
        for (const [role, attrs] of sidesForDependency) {
          const side = unique(attrs || []);
          if (!side.length || !isSubset(side, knownSet)) continue;
          const key = `${role}\u0001${canonicalAttributes(side)}\u0001${dependencyKey(parsed.text)}`;
          if (seen.has(key)) continue;
          seen.add(key);
          sides.push({role, attributes: side, dependency: parsed.text});
        }
      }
      return sides;
    }

    function inclusionPreorderAttributePairs(lhs, rhs) {
      const left = [...(lhs || [])];
      const right = [...(rhs || [])];
      if (!left.length || !right.length) return [];
      if (left.length !== right.length) return [];
      return left.map((attribute, index) => [attribute, right[index]]);
    }

    function addInclusionPreorderEdge(edges, seen, left, right) {
      if (!left || !right) return;
      const key = `${left}\u0001${right}`;
      if (seen.has(key)) return;
      seen.add(key);
      edges.push([left, right]);
    }

    function inclusionPreorderDependencyEdges(cnf, knownAttributes, knownSet) {
      const edges = [];
      const seen = new Set();

      for (const dependency of inclusionDependenciesForKindIdentifiers(cnf)) {
        const parsed = inclusionDependencyParts(dependency, knownAttributes);
        if (!parsed || !['=>', '==', 'o=>', 'x=>'].includes(parsed.symbol)) continue;
        for (const source of parsed.lhsSources || [parsed.lhs]) {
          const lhs = (source || []).filter(attribute => knownSet.has(attribute));
          const rhs = (parsed.rhs || []).filter(attribute => knownSet.has(attribute));
          for (const [left, right] of inclusionPreorderAttributePairs(lhs, rhs)) {
            addInclusionPreorderEdge(edges, seen, left, right);
            if (parsed.symbol === '==') {
              addInclusionPreorderEdge(edges, seen, right, left);
            }
          }
        }
      }

      return edges;
    }

    function implicitEqualAttributeInclusionPreorderEdges(cnf, knownSet) {
      const groups = new Map();
      for (const [relationIndex, relation] of sourceConceptualRelations(cnf).entries()) {
        const relationKey = `${relationIndex}\u0001${relation.name || relationNameFor(relation.attributes || [])}`;
        for (const [attributeIndex, attribute] of (relation.attributes || []).entries()) {
          if (!knownSet.has(attribute)) continue;
          const originalAttribute = relationOriginalAttribute(relation, attributeIndex, attribute);
          const keys = unique([
            `current\u0001${attribute}`,
            originalAttribute ? `original\u0001${originalAttribute}` : '',
          ].filter(Boolean));
          for (const key of keys) {
            if (!groups.has(key)) groups.set(key, []);
            groups.get(key).push({relationKey, attribute});
          }
        }
      }

      const edges = [];
      const seen = new Set();
      for (const occurrences of groups.values()) {
        const relationKeys = new Set(occurrences.map(item => item.relationKey));
        if (relationKeys.size < 2) continue;
        for (const left of occurrences) {
          for (const right of occurrences) {
            if (left.relationKey === right.relationKey) continue;
            addInclusionPreorderEdge(edges, seen, left.attribute, right.attribute);
          }
        }
      }
      return edges;
    }

    function inclusionPreorderAttributeEdges(cnf) {
      const knownAttributes = allCnfAttributes(cnf);
      const knownSet = attrSet(knownAttributes);
      const edges = [];
      const seen = new Set();
      for (const [left, right] of [
        ...inclusionPreorderDependencyEdges(cnf, knownAttributes, knownSet),
        ...implicitEqualAttributeInclusionPreorderEdges(cnf, knownSet),
      ]) {
        addInclusionPreorderEdge(edges, seen, left, right);
      }
      return edges;
    }

    function inclusionPreorderConnectedAttributeGroups(cnf) {
      const knownAttributes = allCnfAttributes(cnf);
      const knownSet = attrSet(knownAttributes);
      const parent = new Map();

      function ensure(attribute) {
        if (!knownSet.has(attribute)) return '';
        if (!parent.has(attribute)) parent.set(attribute, attribute);
        return attribute;
      }

      function find(attribute) {
        const next = parent.get(attribute);
        if (next === attribute) return attribute;
        const root = find(next);
        parent.set(attribute, root);
        return root;
      }

      function union(left, right) {
        const leftAttr = ensure(left);
        const rightAttr = ensure(right);
        if (!leftAttr || !rightAttr) return;
        const leftRoot = find(leftAttr);
        const rightRoot = find(rightAttr);
        if (leftRoot !== rightRoot) parent.set(rightRoot, leftRoot);
      }

      for (const attribute of knownAttributes) ensure(attribute);

      for (const [left, right] of inclusionPreorderAttributeEdges(cnf)) {
        union(left, right);
      }

      const groups = new Map();
      for (const attribute of parent.keys()) {
        const root = find(attribute);
        if (!groups.has(root)) groups.set(root, []);
        groups.get(root).push(attribute);
      }
      return [...groups.values()].filter(group => group.length > 1);
    }

    function activeSourceAttributesForRootPreorder() {
      const attributes = [];
      if (activeData) {
        attributes.push(...(activeData.attributes || []));
        for (const relation of activeData.input_relations || []) {
          attributes.push(...(relation.attributes || []));
        }
        for (const database of activeData.database_schemas || []) {
          attributes.push(...(database.attributes || []));
          for (const relation of database.relations || []) {
            attributes.push(...(relation.attributes || []));
          }
        }
      }
      return unique(attributes);
    }

    function activeNullableBasesForRootPreorder() {
      const nullable = [];
      if (activeData) {
        nullable.push(...(activeData.nullable || []));
        for (const relation of activeData.input_relations || []) {
          nullable.push(...(relation.nullable || []));
        }
        for (const database of activeData.database_schemas || []) {
          nullable.push(...(database.nullable || []));
          for (const relation of database.relations || []) {
            nullable.push(...(relation.nullable || []));
          }
        }
      }
      return new Set(nullable.map(attribute => attributeParts(attribute).base));
    }

    function activeFunctionalDependenciesForRootPreorder() {
      const dependencies = [];
      if (activeData) {
        dependencies.push(...(activeData.fds || []));
        for (const item of activeData.per_input_relation || []) {
          dependencies.push(...(item.applicable_fds || []));
        }
      }
      return uniqueDependencies(dependencies);
    }

    function cnfAttributesByBase(cnf) {
      const byBase = new Map();
      for (const attribute of allCnfAttributes(cnf)) {
        const base = attributeParts(attribute).base;
        if (!byBase.has(base)) byBase.set(base, []);
        byBase.get(base).push(attribute);
      }
      return byBase;
    }

    function sameSuffixAttributes(attribute, candidates) {
      const suffix = attributeParts(attribute).suffix;
      return (candidates || []).filter(candidate => attributeParts(candidate).suffix === suffix);
    }

    function functionalRootPreorderAttributeEdges(cnf) {
      const nullableBases = activeNullableBasesForRootPreorder();
      if (!nullableBases.size) return [];
      const sourceAttributes = activeSourceAttributesForRootPreorder();
      const attributesByBase = cnfAttributesByBase(cnf);
      const edges = [];
      const seen = new Set();

      for (const dependency of activeFunctionalDependenciesForRootPreorder()) {
        const parsed = functionalDependencyParts(dependency, sourceAttributes);
        if (!parsed || parsed.lhs.length !== 1) continue;
        const lhsBase = attributeParts(parsed.lhs[0]).base;
        if (!nullableBases.has(lhsBase)) continue;
        const lhsAttributes = attributesByBase.get(lhsBase) || [];

        for (const rhsAttribute of parsed.rhs || []) {
          const rhsBase = attributeParts(rhsAttribute).base;
          if (nullableBases.has(rhsBase)) continue;
          const rhsAttributes = attributesByBase.get(rhsBase) || [];
          for (const lhsAttribute of lhsAttributes) {
            for (const rhsMatch of sameSuffixAttributes(lhsAttribute, rhsAttributes)) {
              const key = `${lhsAttribute}\u0001${rhsMatch}`;
              if (seen.has(key)) continue;
              seen.add(key);
              edges.push([lhsAttribute, rhsMatch]);
            }
          }
        }
      }

      return edges;
    }

    function addRootPreorderEdgesForBases(edges, seen, attributesByBase, lhsBase, rhsBase) {
      if (!lhsBase || !rhsBase || lhsBase === rhsBase) return;
      const lhsAttributes = attributesByBase.get(lhsBase) || [];
      const rhsAttributes = attributesByBase.get(rhsBase) || [];
      for (const lhsAttribute of lhsAttributes) {
        for (const rhsMatch of sameSuffixAttributes(lhsAttribute, rhsAttributes)) {
          const key = `${lhsAttribute}\u0001${rhsMatch}`;
          if (seen.has(key)) continue;
          seen.add(key);
          edges.push([lhsAttribute, rhsMatch]);
        }
      }
    }

    function relationKeyRootPreorderAttributeEdges(cnf) {
      const nullableBases = activeNullableBasesForRootPreorder();
      if (!nullableBases.size) return [];
      const attributesByBase = cnfAttributesByBase(cnf);
      const edges = [];
      const seen = new Set();

      for (const relation of sourceConceptualRelations(cnf || {})) {
        const keyConstraints = relationKeyConstraints(relation.attributes || [], relation.dependencies || []);
        const singleAttributeKeys = keyConstraints
          .filter(key => key.length === 1)
          .map(key => key[0]);
        for (const lhsAttribute of singleAttributeKeys) {
          const lhsBase = attributeParts(lhsAttribute).base;
          if (!nullableBases.has(lhsBase)) continue;
          for (const rhsAttribute of singleAttributeKeys) {
            const rhsBase = attributeParts(rhsAttribute).base;
            if (nullableBases.has(rhsBase)) continue;
            addRootPreorderEdgesForBases(edges, seen, attributesByBase, lhsBase, rhsBase);
          }
        }
      }

      return edges;
    }

    function inclusionPreorderReachability(cnf, extraEdges = []) {
      const adjacency = new Map();
      for (const attribute of allCnfAttributes(cnf)) {
        if (!adjacency.has(attribute)) adjacency.set(attribute, new Set());
      }
      for (const [left, right] of [...inclusionPreorderAttributeEdges(cnf), ...extraEdges]) {
        if (!adjacency.has(left)) adjacency.set(left, new Set());
        if (!adjacency.has(right)) adjacency.set(right, new Set());
        adjacency.get(left).add(right);
      }

      const memo = new Map();
      function reachableFrom(attribute) {
        if (memo.has(attribute)) return memo.get(attribute);
        const reached = new Set();
        const stack = [...(adjacency.get(attribute) || [])];
        while (stack.length) {
          const next = stack.pop();
          if (reached.has(next)) continue;
          reached.add(next);
          for (const target of adjacency.get(next) || []) stack.push(target);
        }
        memo.set(attribute, reached);
        return reached;
      }

      return {
        reaches(left, right) {
          return left === right || reachableFrom(left).has(right);
        },
      };
    }

    function kindIdentifierInclusionConflict(cnf, attributes) {
      const candidate = attrSet(attributes || []);
      for (const side of inclusionDependencySidesForKindIdentifiers(cnf)) {
        const isContained = isSubset(side.attributes, candidate);
        const isDisjoint = side.attributes.every(attribute => !candidate.has(attribute));
        if (!isContained && !isDisjoint) return side;
      }
      return null;
    }

    function relationKindIdentifierOverlap(relation, attributes, ignoreExact = false) {
      const candidate = attrSet(attributes || []);
      const candidateKey = canonicalAttributes(attributes || []);
      for (const item of relationKindIdentifierObjects(relation)) {
        const existing = item.attributes || [];
        if (ignoreExact && canonicalAttributes(existing) === candidateKey) continue;
        if (existing.some(attribute => candidate.has(attribute))) return existing;
      }
      return null;
    }

    function affectedKindIdentifierRelations(cnf, attributes) {
      return sourceConceptualRelations(cnf)
        .filter(relation => relationContainsAttributes(relation, attributes));
    }

    function validateKindIdentifierCandidate(cnf, attributes, options = {}) {
      const candidate = unique(attributes || []);
      if (!candidate.length) {
        return {ok: false, message: 'Select at least one attribute'};
      }
      const affected = affectedKindIdentifierRelations(cnf, candidate);
      if (!affected.length) {
        return {ok: false, message: 'Kind identifier attributes are not contained in any relation'};
      }
      const removing = Boolean(options.removing);
      const inclusionConflict = !removing
        ? kindIdentifierInclusionConflict(cnf, candidate)
        : null;
      if (inclusionConflict) {
        return {
          ok: false,
          message: `Kind identifier ${fmtSet(candidate)} conflicts with the ${inclusionConflict.role} ${fmtSet(inclusionConflict.attributes)} of inclusion dependency ${inclusionConflict.dependency}`,
        };
      }
      for (const relation of affected) {
        if (!removing && !kindIdentifierKeyCompatible(relation, candidate)) {
          return {
            ok: false,
            message: `Kind identifier ${fmtSet(candidate)} conflicts with a key in ${relation.name || relationNameFor(relation.attributes || [])}`,
          };
        }
        if (!removing) {
          const overlap = relationKindIdentifierOverlap(relation, candidate, true);
          if (overlap) {
            const keys = relationKeyConstraints(relation.attributes || [], relation.dependencies || []);
            const isCandidateKey = keys.some(keyAttrs => canonicalAttributes(keyAttrs) === canonicalAttributes(candidate));
            const isOverlapKey = keys.some(keyAttrs => canonicalAttributes(keyAttrs) === canonicalAttributes(overlap));
            if (!isCandidateKey || !isOverlapKey) {
              return {
                ok: false,
                message: `Kind identifier ${fmtSet(candidate)} overlaps ${fmtSet(overlap)} in ${relation.name || relationNameFor(relation.attributes || [])}`,
              };
            }
          }
        }
      }
      return {ok: true, affected};
    }

    function validateKindIdentifierCandidateSet(cnf, candidates, options = {}) {
      const normalized = uniqueAttributeSets(candidates || []);
      if (!normalized.length) {
        return {ok: false, message: 'Select at least one attribute'};
      }
      const affected = [];
      for (const candidate of normalized) {
        const validation = validateKindIdentifierCandidate(cnf, candidate, options);
        if (!validation.ok) return validation;
        affected.push(...(validation.affected || []));
      }
      return {ok: true, affected};
    }

    function selectedKindIdentifierSets(cnf) {
      const byKey = new Map();
      for (const relation of sourceConceptualRelations(cnf)) {
        for (const attrs of relationSelectedKindIdentifiers(relation)) {
          const key = canonicalAttributes(attrs);
          if (!key || byKey.has(key)) continue;
          byKey.set(key, [...attrs]);
        }
      }
      return [...byKey.values()].sort((left, right) => {
        const leftKey = canonicalAttributes(left);
        const rightKey = canonicalAttributes(right);
        return leftKey.localeCompare(rightKey, undefined, {numeric: true});
      });
    }

    function kindIdentifierDisplayAttributes(attributes) {
      return unique((attributes || []).map(attribute => {
        const parts = attributeParts(attribute);
        return parts.base || String(attribute);
      })).sort((left, right) => left.localeCompare(right, undefined, {numeric: true}));
    }

    function relationHasAttributesFromBoth(relation, leftAttributes, rightAttributes) {
      const relationAttributes = attrSet(relation && relation.attributes || []);
      return (leftAttributes || []).some(attribute => relationAttributes.has(attribute))
        && (rightAttributes || []).some(attribute => relationAttributes.has(attribute));
    }

    function kindIdentifierDisplayKey(attributes) {
      return canonicalAttributes(kindIdentifierDisplayAttributes(attributes));
    }

    function kindIdentifierName(attributes) {
      const names = kindIdentifierDisplayAttributes(attributes);
      return names.length ? names.join(', ') : '{}';
    }

    function kindIdentifierDisplayLabel(attributes) {
      return kindIdentifierName(attributes);
    }

    function jointKindIdentifierChoiceLabel(attributes) {
      return kindIdentifierName(attributes);
    }

    function kindIdentifierNamePart(attributes) {
      return kindIdentifierName(attributes);
    }

    function selectedKindIdentifierGroupDescriptors(cnf) {
      const descriptors = new Map();
      const parent = new Map();

      function ensure(attributes) {
        const attrs = unique(attributes || []);
        const key = kindIdentifierDisplayKey(attrs);
        if (!key) return '';
        if (!parent.has(key)) parent.set(key, key);
        if (!descriptors.has(key)) {
          descriptors.set(key, {
            key,
            label: kindIdentifierDisplayLabel(attrs),
            name: kindIdentifierNamePart(attrs),
            identifiers: [],
            identifierKeys: new Set(),
          });
        }

        const descriptor = descriptors.get(key);
        const actualKey = canonicalAttributes(attrs);
        if (actualKey && !descriptor.identifierKeys.has(actualKey)) {
          descriptor.identifierKeys.add(actualKey);
          descriptor.identifiers.push(attrs);
        }
        return key;
      }

      function find(key) {
        if (!key) return '';
        const next = parent.get(key);
        if (next === key) return key;
        const root = find(next);
        parent.set(key, root);
        return root;
      }

      function union(left, right) {
        const leftRoot = find(left);
        const rightRoot = find(right);
        if (leftRoot !== rightRoot) parent.set(rightRoot, leftRoot);
      }

      for (const relation of sourceConceptualRelations(cnf)) {
        for (const identifier of relationKindIdentifierObjects(relation)) {
          ensure(identifier.attributes || []);
        }
      }

      const descriptorKeysByAttribute = new Map();
      for (const descriptor of descriptors.values()) {
        for (const identifier of descriptor.identifiers || []) {
          for (const attribute of identifier || []) {
            if (!descriptorKeysByAttribute.has(attribute)) descriptorKeysByAttribute.set(attribute, new Set());
            descriptorKeysByAttribute.get(attribute).add(descriptor.key);
          }
        }
      }

      for (const attributeGroup of inclusionPreorderConnectedAttributeGroups(cnf)) {
        const keys = unique(attributeGroup.flatMap(attribute => {
          return [...(descriptorKeysByAttribute.get(attribute) || [])];
        }));
        for (let index = 1; index < keys.length; index += 1) {
          union(keys[0], keys[index]);
        }
      }

      const groups = new Map();
      for (const key of descriptors.keys()) {
        const root = find(key);
        if (!groups.has(root)) groups.set(root, []);
        groups.get(root).push(descriptors.get(key));
      }

      return [...groups.values()].map(group => {
        return group.map(descriptor => ({
          key: descriptor.key,
          label: descriptor.label,
          name: descriptor.name,
          identifiers: descriptor.identifiers,
        })).sort((left, right) => {
          return left.label.localeCompare(right.label, undefined, {numeric: true});
        });
      }).sort((left, right) => {
        const leftKey = left.map(item => item.label).join('\u0001');
        const rightKey = right.map(item => item.label).join('\u0001');
        return leftKey.localeCompare(rightKey, undefined, {numeric: true});
      });
    }

    function jointKindIdentifierSummaryGroups(cnf) {
      return selectedKindIdentifierGroupDescriptors(cnf)
        .map(group => [kindIdentifierName(unique(group.flatMap(kindIdentifierGroupItemAttributes)))]);
    }

    function jointKindIdentifierSummaryItems(cnf) {
      return jointKindIdentifierSummaryGroups(cnf)
        .map(group => group[0] || '{}');
    }

    function renderKindIdentifierSummaryItem(group) {
      return `<li>${escapeHtml(group[0] || '{}')}</li>`;
    }

    function kindIdentifierGroupAttributes(group) {
      return unique((group || []).flatMap(kindIdentifierGroupItemAttributes));
    }

    function makeJointKindIdentifierChoiceForGroup(group) {
      const identifiers = uniqueAttributeSets((group || []).flatMap(item => item.identifiers || []));
      const key = jointKindIdentifierChoiceGroupKey(identifiers);
      if (!key) return null;
      return {
        key,
        label: kindIdentifierName(kindIdentifierGroupAttributes(group)),
        identifiers,
      };
    }

    function kindIdentifierGroupCanMergeWithCandidate(cnf, group, candidate) {
      const candidateAttributes = unique(candidate || []);
      const candidateDisplayKey = kindIdentifierDisplayKey(candidate || []);
      const groupAttributes = kindIdentifierGroupAttributes(group);
      if (!candidateAttributes.length || !groupAttributes.length) return false;
      if (kindIdentifierDisplayKey(groupAttributes) === candidateDisplayKey) return false;
      return sourceConceptualRelations(cnf || {})
        .some(relation => relationHasAttributesFromBoth(relation, groupAttributes, candidateAttributes));
    }

    function jointKindIdentifierChoiceGroupsForCandidate(cnf, candidate) {
      const choicesByKey = new Map();
      for (const group of selectedKindIdentifierGroupDescriptors(cnf || {})) {
        if (!kindIdentifierGroupCanMergeWithCandidate(cnf, group, candidate)) continue;
        const choice = makeJointKindIdentifierChoiceForGroup(group);
        if (!choice) continue;
        if (!choicesByKey.has(choice.key)) {
          choicesByKey.set(choice.key, choice);
        } else {
          const existing = choicesByKey.get(choice.key);
          existing.identifiers = uniqueAttributeSets([...existing.identifiers, ...choice.identifiers]);
          existing.label = kindIdentifierName(unique(existing.identifiers.flat()));
        }
      }

      return [...choicesByKey.values()].sort((left, right) => {
        return left.label.localeCompare(right.label, undefined, {numeric: true});
      });
    }

    async function collectFinalKindIdentifierAdditions(candidates) {
      const additions = [];
      const pendingByCandidateKey = new Map();

      for (const candidate of uniqueAttributeSets(candidates || [])) {
        const candidateDisplayKey = kindIdentifierDisplayKey(candidate);
        if (!candidateDisplayKey) continue;
        for (const relation of affectedKindIdentifierRelations(cnfState, candidate)) {
          if (relationHasKindIdentifier(relation, candidate)) continue;
          if (!pendingByCandidateKey.has(candidateDisplayKey)) {
            pendingByCandidateKey.set(candidateDisplayKey, []);
          }
          pendingByCandidateKey.get(candidateDisplayKey).push({
            relation,
            candidate,
          });
        }
      }

      for (const pendingItems of pendingByCandidateKey.values()) {
        const existingByKey = new Map();
        for (const item of pendingItems) {
          for (const choice of jointKindIdentifierChoiceGroupsForCandidate(cnfState, item.candidate)) {
            if (!existingByKey.has(choice.key)) {
              existingByKey.set(choice.key, {
                key: choice.key,
                label: choice.label,
                identifiers: [],
              });
            }
            const existing = existingByKey.get(choice.key);
            existing.identifiers = uniqueAttributeSets([...existing.identifiers, ...choice.identifiers]);
            existing.label = kindIdentifierName(unique(existing.identifiers.flat()));
          }
        }

        const candidateChoices = [...existingByKey.values()].sort((left, right) => {
          return left.label.localeCompare(right.label, undefined, {numeric: true});
        });

        let selectedKeys = new Set();
        if (candidateChoices.length) {
          const indexes = await showJointKindIdentifierDialog(candidateChoices);
          if (indexes === null) return null;
          selectedKeys = new Set(indexes
            .filter(index => index >= 0 && index < candidateChoices.length)
            .map(index => candidateChoices[index].key));
        }

        for (const item of pendingItems) {
          const selectedExisting = jointKindIdentifierChoiceGroupsForCandidate(cnfState, item.candidate)
            .filter(choice => selectedKeys.has(choice.key))
            .flatMap(choice => choice.identifiers);
          additions.push({
            relation: item.relation,
            identifiers: [item.candidate, ...selectedExisting],
            consumedIdentifiers: selectedExisting,
          });
        }
      }

      return additions;
    }

    function kindRelationDependency(attributes, name) {
      return `${fmtSet(attributes)} -> att(${name})`;
    }

    function kindRelationGroupKey(group) {
      return (group || []).map(item => item.key).join('\u0002');
    }

    function kindIdentifierGroupItemAttributes(item) {
      return unique((item && item.identifiers || []).flat());
    }

    function strictPreorderBefore(left, right, reachability) {
      return left !== right
        && reachability.reaches(left, right)
        && !reachability.reaches(right, left);
    }

    function rootAttributesForKindIdentifier(identifier, candidateAttributes, reachability) {
      const reachableCandidates = unique((candidateAttributes || []).filter(candidate => {
        return (identifier || []).some(attribute => reachability.reaches(attribute, candidate));
      }));
      const candidates = reachableCandidates.length ? reachableCandidates : unique(identifier || []);
      return candidates.filter(candidate => {
        return !candidates.some(other => strictPreorderBefore(candidate, other, reachability));
      }).sort((left, right) => left.localeCompare(right, undefined, {numeric: true}));
    }

    function rootKindIdentifiersForGroup(cnf, group) {
      const identifiers = uniqueAttributeSets((group || []).flatMap(item => item.identifiers || []));
      const candidateAttributes = unique((group || []).flatMap(kindIdentifierGroupItemAttributes));
      const reachability = inclusionPreorderReachability(cnf, [
        ...functionalRootPreorderAttributeEdges(cnf),
        ...relationKeyRootPreorderAttributeEdges(cnf),
      ]);
      const mergedIdentifier = unique(identifiers.flat());
      const rootIdentifier = rootAttributesForKindIdentifier(
        mergedIdentifier,
        candidateAttributes,
        reachability
      );
      return rootIdentifier.length ? [rootIdentifier] : [];
    }

    function rootKindRelationName(rootIdentifiers) {
      const rootAttributes = unique((rootIdentifiers || []).flat());
      const names = kindIdentifierDisplayAttributes(rootAttributes);
      return names.length ? names.join(', ') : '{}';
    }

    function kindRelationForGroup(cnf, group) {
      const identifiers = rootKindIdentifiersForGroup(cnf, group);
      const attrs = unique(identifiers.flat())
        .sort((left, right) => left.localeCompare(right, undefined, {numeric: true}));
      const name = rootKindRelationName(identifiers);
      return {
        name,
        attributes: attrs,
        original_name: name,
        original_attributes: [...attrs],
        dependencies: uniqueDependencies(identifiers.map(identifier => kindRelationDependency(identifier, name))),
        generated_kind_relation: true,
        kind_identifier_group_key: kindRelationGroupKey(group),
      };
    }

    function generatedKindRelationAutoName(relation) {
      return rootKindRelationName([relation.attributes || []]);
    }

    function customGeneratedKindRelationName(relation) {
      if (!relation || !relation.name) return '';
      return relation.name === generatedKindRelationAutoName(relation)
        ? ''
        : relation.name;
    }

    function preserveGeneratedKindRelationName(cnf, expectedRelation) {
      const generatedRelations = (cnf.relations || []).filter(isGeneratedKindRelation);
      const expectedGroupKey = expectedRelation.kind_identifier_group_key || '';
      const expectedAttributeKey = canonicalAttributes(expectedRelation.attributes || []);
      const existing = generatedRelations.find(relation => {
        return expectedGroupKey && relation.kind_identifier_group_key === expectedGroupKey;
      }) || generatedRelations.find(relation => {
        return expectedAttributeKey && canonicalAttributes(relation.attributes || []) === expectedAttributeKey;
      });
      if (existing) ensureRelationOriginalNames(existing);
      if (existing && Array.isArray(existing.original_attributes)
        && existing.original_attributes.length === (expectedRelation.attributes || []).length) {
        expectedRelation = {
          ...expectedRelation,
          original_attributes: [...existing.original_attributes],
        };
      }
      if (existing && existing.original_name) {
        expectedRelation = {
          ...expectedRelation,
          original_name: existing.original_name,
        };
      }
      const preservedName = customGeneratedKindRelationName(existing);
      if (!preservedName) return expectedRelation;
      return {
        ...expectedRelation,
        name: preservedName,
        dependencies: uniqueDependencies((expectedRelation.dependencies || [])
          .map(dep => rewriteDependencyRelationName(dep, expectedRelation.name, preservedName))),
      };
    }

    function normalizedKindRelationSignature(relation) {
      return {
        key: relation.kind_identifier_group_key || relation.kind_identifier_key || canonicalAttributes(relation.attributes || []),
        name: relation.name || '',
        attributes: relation.attributes || [],
        dependencies: uniqueDependencies(relation.dependencies || []),
      };
    }

    function sortedKindRelationSignatures(relations) {
      return (relations || [])
        .map(normalizedKindRelationSignature)
        .sort((left, right) => left.key.localeCompare(right.key, undefined, {numeric: true}));
    }

    function expectedKindRelations(cnf) {
      return selectedKindIdentifierGroupDescriptors(cnf)
        .map(group => kindRelationForGroup(cnf, group))
        .filter(relation => (relation.attributes || []).length)
        .map(relation => preserveGeneratedKindRelationName(cnf, relation));
    }

    function kindRelationsInSync(cnf) {
      const actual = sortedKindRelationSignatures((cnf.relations || []).filter(isGeneratedKindRelation));
      const expected = sortedKindRelationSignatures(expectedKindRelations(cnf));
      return JSON.stringify(actual) === JSON.stringify(expected);
    }

    function materializeKindRelations(cnf) {
      const expected = expectedKindRelations(cnf);
      const before = JSON.stringify(sortedKindRelationSignatures((cnf.relations || []).filter(isGeneratedKindRelation)));
      cnf.relations = [
        ...sourceConceptualRelations(cnf),
        ...expected,
      ];
      const after = JSON.stringify(sortedKindRelationSignatures(expected));
      return {
        changed: before !== after,
        count: expected.length,
      };
    }

    function setRelationKindIdentifier(relation, keyAttrs, checked) {
      const key = canonicalAttributes(keyAttrs);
      const selected = [];
      for (const item of relationKindIdentifierObjects(relation)) {
        const attrs = item.attributes || [];
        if (!attrs.length || canonicalAttributes(attrs) === key) continue;
        selected.push(item);
      }
      if (checked) selected.push(makeKindIdentifier(keyAttrs));
      setRelationKindIdentifierObjects(relation, selected);
    }

    function sourceRelationByDraftKey(key) {
      if (!cnfState) return null;
      return sourceConceptualRelations(cnfState)
        .find(relation => draftKeyForRelation(relation) === key) || null;
    }

    function clearKindIdentifierDraft(relation) {
      kindIdentifierDraftSelections.delete(draftKeyForRelation(relation));
    }

    function setKindIdentifierEverywhere(attributes, checked) {
      if (!cnfState) return {changed: false, count: 0};
      const candidate = unique(attributes || []);
      let changed = false;
      let count = 0;
      for (const relation of affectedKindIdentifierRelations(cnfState, candidate)) {
        const before = JSON.stringify(relation.kind_identifiers || []);
        setRelationKindIdentifier(relation, candidate, checked);
        const after = JSON.stringify(relation.kind_identifiers || []);
        if (before !== after) {
          changed = true;
          count += 1;
        }
      }
      return {changed, count};
    }

    function setKindIdentifierCandidatesEverywhere(candidates, checked) {
      if (!cnfState) return {changed: false, count: 0};
      const changedRelations = new Set();
      let changed = false;
      for (const candidate of uniqueAttributeSets(candidates || [])) {
        for (const relation of affectedKindIdentifierRelations(cnfState, candidate)) {
          const before = JSON.stringify(relation.kind_identifiers || []);
          setRelationKindIdentifier(relation, candidate, checked);
          const after = JSON.stringify(relation.kind_identifiers || []);
          if (before !== after) {
            changed = true;
            changedRelations.add(draftKeyForRelation(relation));
          }
        }
      }
      return {changed, count: changedRelations.size};
    }

    function relationContainsAnyAttribute(relation, attributes) {
      const relationAttributes = attrSet(relation && relation.attributes || []);
      return (attributes || []).some(attribute => relationAttributes.has(attribute));
    }

    function kindIdentifierDisplayKeys(identifiers) {
      return new Set(uniqueAttributeSets(identifiers || [])
        .map(kindIdentifierDisplayKey)
        .filter(Boolean));
    }

    function removeKindIdentifiersEverywhere(displayKeys, changedRelations) {
      if (!displayKeys || !displayKeys.size || !cnfState) return false;
      let changed = false;
      for (const relation of sourceConceptualRelations(cnfState)) {
        const before = JSON.stringify(relation.kind_identifiers || []);
        const remaining = relationKindIdentifierObjects(relation)
          .filter(item => !displayKeys.has(kindIdentifierDisplayKey(item.attributes || [])));
        setRelationKindIdentifierObjects(relation, remaining);
        const after = JSON.stringify(relation.kind_identifiers || []);
        if (before !== after) {
          changed = true;
          if (changedRelations) changedRelations.add(draftKeyForRelation(relation));
        }
      }
      return changed;
    }

    function applyFinalKindIdentifierAdditions(additions) {
      const changedRelations = new Set();
      let changed = false;
      for (const addition of additions || []) {
        if (!addition || !addition.relation) continue;
        const mergedAttributes = unique((addition.identifiers || []).flat());
        if (!mergedAttributes.length) continue;
        const consumedDisplayKeys = kindIdentifierDisplayKeys(addition.consumedIdentifiers || []);
        changed = removeKindIdentifiersEverywhere(consumedDisplayKeys, changedRelations) || changed;
        const targetRelations = consumedDisplayKeys.size
          ? sourceConceptualRelations(cnfState).filter(relation => relationContainsAnyAttribute(relation, mergedAttributes))
          : [addition.relation];
        for (const relation of targetRelations) {
          const before = JSON.stringify(relation.kind_identifiers || []);
          mergeRelationKindIdentifiers(relation, [mergedAttributes]);
          const after = JSON.stringify(relation.kind_identifiers || []);
          if (before !== after) {
            changed = true;
            changedRelations.add(draftKeyForRelation(relation));
          }
        }
      }
      return {changed, count: changedRelations.size};
    }

    async function applyKindIdentifierDraft(relationKey) {
      if (!cnfState) return;
      const relation = sourceRelationByDraftKey(relationKey);
      if (!relation) return;
      const attributes = draftSelectedAttributes(relation);
      const expandedCandidates = expandedKindIdentifierCandidates(cnfState, attributes);
      const removing = relationHasKindIdentifier(relation, attributes);
      const validation = validateKindIdentifierCandidateSet(cnfState, expandedCandidates, {removing});
      if (!validation.ok) {
        statusEl.textContent = validation.message;
        render(activeData);
        return;
      }

      const finalAdditions = removing
        ? []
        : await collectFinalKindIdentifierAdditions(expandedCandidates);
      if (finalAdditions === null) {
        statusEl.textContent = 'Kind identifier addition cancelled';
        render(activeData);
        return;
      }

      const result = removing
        ? setKindIdentifierCandidatesEverywhere(expandedCandidates, false)
        : applyFinalKindIdentifierAdditions(finalAdditions);
      clearExpandedKindIdentifierDraft(relation, attributes);
      statusEl.textContent = removing
        ? `Kind identifier${expandedCandidates.length === 1 ? '' : 's'} removed from ${result.count} relation${result.count === 1 ? '' : 's'}`
        : `Kind identifier${expandedCandidates.length === 1 ? '' : 's'} added to ${result.count} relation${result.count === 1 ? '' : 's'}`;
      render(activeData);
    }

    function renderKindIdentifierSummary(cnf) {
      const coverage = kindIdentifierCoverage(cnf);
      const cls = coverage.ok ? 'ok' : 'warn';
      const groups = jointKindIdentifierSummaryGroups(cnf);
      const items = [];
      if (groups.length) {
        items.push(`<ul class="kind-identifier-summary-list">${groups
          .map(renderKindIdentifierSummaryItem)
          .join('')}</ul>`);
      } else if (coverage.ok) {
        items.push('<div class="kind-identifier-summary-text">Kind identifiers: none</div>');
      }
      if (!coverage.ok) {
        items.push(`<div class="kind-identifier-summary-text">Missing kind identifier: ${escapeHtml(coverage.missing.join(', '))}</div>`);
      }
      const content = items.join('');
      return `<div class="box full kind-identifier-summary ${cls}">
        <h3>Kind Identifiers</h3>
        ${content}
      </div>`;
    }

    function renderTarget(data) {
      const sixNF = normalFormForDisplay(data['6NF'] || {relations: [], cross_relation_inclusion_dependencies: []});
      const crossInclusions = uniqueDependencies(sixNF.cross_relation_inclusion_dependencies || []);
      const relationBoxes = (sixNF.relations || []).map(target => {
        const dependencies = uniqueDependencies(target.dependencies || []);
        const keyConstraints = relationKeyConstraints(target.attributes || [], dependencies);
        return `<div class="box relation-box">
          <h3>${escapeHtml(target.name)}</h3>
          ${renderAttributes(target.attributes, [], keyConstraints)}
          ${renderDependencyBox(dependencies, target.name, target.attributes)}
        </div>`;
      }).join('');
      return `<div class="grid relation-grid">${relationBoxes}${renderCrossRelationBox(crossInclusions)}</div>`;
    }

    function renderConceptual(data) {
      const source = cnfState || data.CNF || data['6NF'] || {relations: [], cross_relation_inclusion_dependencies: []};
      const cnf = normalFormForDisplay(source);
      const crossInclusions = uniqueDependencies(cnf.cross_relation_inclusion_dependencies || []);
      const relationBoxes = (cnf.relations || []).map(target => {
        const dependencies = uniqueDependencies(target.dependencies || []);
        const keyConstraints = relationKeyConstraints(target.attributes, dependencies);
        if (isGeneratedKindRelation(target)) {
          return `<div class="box relation-box">
            ${renderCnfRelationInput(target)}
            ${renderEditableAttributes(target.attributes || [], keyConstraints, target, {includeKindDraft: false})}
            ${renderDependencyBox(dependencies, target.name, target.attributes)}
          </div>`;
        }
        return `<div class="box relation-box">
          ${renderCnfRelationInput(target)}
          ${renderEditableAttributes(target.attributes, keyConstraints, target)}
          ${renderKindIdentifierRelationActions(target)}
          ${renderDependencyBox(dependencies, target.name, target.attributes)}
        </div>`;
      }).join('');
      return `<div class="grid relation-grid">${renderKindIdentifierSummary(cnf)}${relationBoxes}${renderCrossRelationBox(crossInclusions)}</div>`;
    }

    function renderRemoved(removed) {
      const entries = Object.entries(removed || {});
      if (!entries.length) return '<div class="chips"><span class="chip">none</span></div>';
      return `<ul>${entries.map(([relation, reasons]) => {
        return `<li><strong>${escapeHtml(relation)}</strong>: ${escapeHtml(reasons.join('; '))}</li>`;
      }).join('')}</ul>`;
    }

    function renderSteps(steps, relationName = '') {
      const displaySteps = displayStepsForRelation(steps || [], relationName);
      if (!displaySteps.length) return '<div class="chips"><span class="chip">already NF</span></div>';
      return displaySteps.map(step => {
        const resultText = (step.result || []).map(fmtSet).join(' + ');
        const dependency = step.dependency || stepDependencyText(step);
        return `<div class="step">${escapeHtml(fmtSet(step.relation))} by ${escapeHtml(step.dependency_kind)} ${escapeHtml(dependency)} => ${escapeHtml(resultText)}</div>`;
      }).join('');
    }

    function renderPerRelation(items) {
      if (!items || !items.length) return '<div class="box full"><h3>Per-relation NF</h3><div class="chips"><span class="chip">none</span></div></div>';
      return items.map(item => {
        const fds = item.applicable_fds || [];
        const mvds = item.applicable_mvds || [];
        const rel = fmtSet(item.renamed_sql_null_relation || item.sql_null_relation);
        const relTitle = item.sql_null_relation_name ? `${item.sql_null_relation_name} = ${rel}` : rel;
        const relationAttributes = item.renamed_sql_null_relation || item.sql_null_relation || [];
        const displayedFds = displayDependenciesForRelation(item.sql_null_relation_name || '', relationAttributes, fds);
        const decomp = (item.four_nf_decomposition || []).map(fmtSet);
        return `<div class="relation-block">
          <div class="relation-title">NF for ${escapeHtml(relTitle)}</div>
          <div class="grid">
            <div class="box"><h3>Applicable FDs</h3><div class="chips">${dependencyChips(displayedFds)}</div></div>
            <div class="box"><h3>Applicable MVDs</h3><div class="chips">${dependencyChips(mvds)}</div></div>
            <div class="box full"><h3>NF Decomposition</h3><div class="chips">${chips(decomp)}</div></div>
            <div class="box full"><h3>Steps</h3>${renderSteps(item.steps, item.sql_null_relation_name || '')}</div>
          </div>
        </div>`;
      }).join('');
    }

    function renderRemovedSources(items) {
      const rows = [];
      for (const item of items || []) {
        const removed = ((item.sql_null_stage || {}).removed_relations) || {};
        for (const [relation, reasons] of Object.entries(removed)) {
          rows.push(`<li><strong>${escapeHtml(item.input_relation)}:${escapeHtml(relation)}</strong>: ${escapeHtml(reasons.join('; '))}</li>`);
        }
      }
      if (!rows.length) return '<div class="chips"><span class="chip">none</span></div>';
      return `<ul>${rows.join('')}</ul>`;
    }

    function prefixedRelations(items, stageKey) {
      const out = [];
      for (const item of items || []) {
        const stage = item.sql_null_stage || {};
        if (stageKey === 'sql_null_decomposition' && stage.named_sql_null_decomposition) {
          for (const relation of stage.named_sql_null_decomposition || []) {
            out.push(`${relation.name}: ${fmtSet(relation.attributes)}`);
          }
          continue;
        }
        for (const relation of stage[stageKey] || []) {
          out.push(`${item.input_relation}: ${fmtSet(relation)}`);
        }
      }
      return out;
    }

    function renderInputRelations(items) {
      if (!items || !items.length) return '';
      return items.map(item => {
        const stage = item.sql_null_stage || {};
        const final = (item.final_decomposition || []).map(fmtSet);
        const namedSqlNull = (stage.named_sql_null_decomposition || []).map(relation => `${relation.name}: ${fmtSet(relation.attributes)}`);
        const title = `${item.input_relation} = ${fmtSet(item.attributes || [])}`;
        const applicableDependencies = displayDependenciesForRelation(item.input_relation, item.attributes || [], [
          ...(item.applicable_sql_null_dependencies || []),
          ...(item.applicable_fds || []),
          ...(item.applicable_mvds || []),
          ...(item.applicable_inclusion_dependencies || [])
        ]);
        return `<div class="relation-block">
          <div class="relation-title">${escapeHtml(title)}</div>
          <div class="grid">
            <div class="box"><h3>Attributes</h3><div class="chips">${chips(item.attributes)}</div></div>
            <div class="box"><h3>Nullable Attributes</h3><div class="chips">${chips(item.nullable)}</div></div>
            <div class="box"><h3>Applicable Dependencies</h3><div class="chips">${dependencyChips(applicableDependencies)}</div></div>
            <div class="box sql-null-box"><h3>SQL-null Decomposition</h3><div class="chips">${chips(namedSqlNull)}</div></div>
            <div class="box"><h3>Final NF</h3><div class="chips">${chips(final)}</div></div>
            <div class="box full"><h3>Removed Relations</h3>${renderRemoved(stage.removed_relations || {})}</div>
          </div>
          <div class="grid">${renderPerRelation(item.per_relation_4nf)}</div>
        </div>`;
      }).join('');
    }

    function render(data) {
      if (data.extended_conflict_free === false) {
        result.innerHTML = `<div class="box full"><h3>Result</h3><p>${escapeHtml(data.message || 'Source database schema is not extended conflict-free')}</p></div>`;
        return;
      }

      if (data.errors) {
        result.innerHTML = `<div class="box full"><h3>Input Error</h3><ul>${
          data.errors.map(error => `<li>${escapeHtml(error)}</li>`).join('')
        }</ul></div><pre>${escapeHtml(JSON.stringify(data, null, 2))}</pre>`;
        return;
      }

      const inputItems = data.per_input_relation || [];
      const provisional = prefixedRelations(inputItems, 'provisional_decomposition');
      const sqlNull = prefixedRelations(inputItems, 'sql_null_decomposition');
      const final4nf = data.final_decomposition || [];
      const removedCount = inputItems.reduce((total, item) => {
        return total + Object.keys(((item.sql_null_stage || {}).removed_relations) || {}).length;
      }, 0);
      if (!cnfState) cnfState = cloneCnf(data.CNF || data['6NF']);
      let html = renderSection('Source Schema', renderSource(data));
      html += renderSection(
        'Sixth Normal Form',
        renderTarget(data),
        renderSixNfExportButton()
      );
      html += renderSection(
        'Conceptual Normal Form',
        renderConceptual(data),
        renderConceptualActions()
      );

      html += `<div class="details-toggle-row">
        <button id="detailsToggle" class="details-toggle" type="button" aria-expanded="false" aria-controls="detailsPanel">Details</button>
      </div>`;

      html += `<div id="detailsPanel" class="details-panel" hidden>
        <div class="grid">
          <div class="box sql-null-box full"><h3>SQL-null Decomposition</h3><div class="chips">${chips(sqlNull)}</div></div>
        </div>
        <div class="summary">
        <div class="metric"><strong>${provisional.length}</strong><span>Provisional</span></div>
        <div class="metric"><strong>${sqlNull.length}</strong><span>SQL-null relations</span></div>
        <div class="metric"><strong>${removedCount}</strong><span>Removed</span></div>
        <div class="metric"><strong>${final4nf.length}</strong><span>Final NF</span></div>
      </div>`;

      html += `<div class="grid">
        <div class="box"><h3>Provisional Decomposition</h3><div class="chips">${chips(provisional)}</div></div>
        <div class="box full"><h3>Removed Relations</h3>${renderRemovedSources(inputItems)}</div>
      </div>`;

      const displayData = detailsDisplayData(data);
      html += `<div class="grid">${renderInputRelations(displayData.per_input_relation || [])}</div>`;
      html += `<pre>${escapeHtml(JSON.stringify(displayData, null, 2))}</pre>`;
      html += `</div>`;
      result.innerHTML = html;

      const detailsToggle = document.getElementById('detailsToggle');
      const detailsPanel = document.getElementById('detailsPanel');
      if (detailsToggle && detailsPanel) {
        detailsToggle.addEventListener('click', () => {
          const isOpen = detailsToggle.getAttribute('aria-expanded') === 'true';
          detailsToggle.setAttribute('aria-expanded', String(!isOpen));
          detailsPanel.hidden = isOpen;
        });
      }
    }

    function commitCnfInput(target, options = {}) {
      const renderAfter = options.renderAfter !== false;
      if (!target || !target.dataset || !target.dataset.cnfAction) return;
      if (!activeData || !cnfState) return;

      let changed = false;
      if (target.dataset.cnfAction === 'rename-relation') {
        changed = renameCnfRelation(target.dataset.cnfRelation || '', target.value);
      }
      if (target.dataset.cnfAction === 'rename-attribute') {
        changed = renameCnfAttribute(target.dataset.cnfAttribute || '', target.value);
      }
      if (renderAfter && (changed || String(target.value || '').trim() !== String(target.dataset.cnfRelation || target.dataset.cnfAttribute || ''))) {
        render(activeData);
      }
      return changed;
    }

    function handleCnfChange(event) {
      const saving = event.type === 'focusout'
        && event.relatedTarget
        && event.relatedTarget.dataset
        && event.relatedTarget.dataset.cnfSave;
      commitCnfInput(event.target, {renderAfter: !saving});
      if (saving) updateConceptualActionButtons();
    }

    function handleCnfInput(event) {
      const target = event.target;
      if (!target || !target.dataset || !target.dataset.cnfAction) return;
      updateConceptualActionButtons();
    }

    function handleCnfKeydown(event) {
      const target = event.target;
      if (!target || !target.dataset || !target.dataset.cnfAction) return;
      if (event.key === 'Enter') {
        event.preventDefault();
        commitCnfInput(target);
      }
      if (event.key === 'Escape') {
        event.preventDefault();
        if (activeData) render(activeData);
      }
    }

    function kindIdentifierStatusMessage() {
      if (!cnfState) return '';
      const coverage = kindIdentifierCoverage(cnfState);
      if (coverage.ok) return kindIdentifierStatusText(cnfState);
      return `Missing kind identifier: ${coverage.missing.join(', ')}`;
    }

    function handleKindIdentifierDraftChange(event) {
      const target = event.target && event.target.closest
        ? event.target.closest('[data-kind-draft-attribute]')
        : null;
      if (!target || !activeData || !cnfState) return;
      const relation = sourceRelationByDraftKey(target.dataset.kindDraftRelation || '');
      if (!relation) return;
      const attribute = target.dataset.kindDraftAttribute || '';
      updateKindIdentifierDraftSelection(relation, attribute, target.checked);
      render(activeData);
    }

    async function handleKindIdentifierAction(event) {
      const applyButton = event.target && event.target.closest
        ? event.target.closest('[data-kind-identifier-apply]')
        : null;
      if (applyButton) {
        if (applyButton.disabled) return;
        await applyKindIdentifierDraft(applyButton.dataset.kindIdentifierApply || '');
        return;
      }

      const clearButton = event.target && event.target.closest
        ? event.target.closest('[data-kind-identifier-clear]')
        : null;
      if (clearButton) {
        if (clearButton.disabled) return;
        const relation = sourceRelationByDraftKey(clearButton.dataset.kindIdentifierClear || '');
        if (relation) clearKindIdentifierDraft(relation);
        render(activeData);
      }
    }

    function commitVisibleCnfInputs() {
      let changed = false;
      for (const control of result.querySelectorAll('[data-cnf-action]')) {
        changed = Boolean(commitCnfInput(control, {renderAfter: false})) || changed;
      }
      return changed;
    }

    function saveCnf() {
      if (!activeData || !cnfState) return;
      commitVisibleCnfInputs();
      if (!isCnfDirty()) {
        updateConceptualActionButtons();
        render(activeData);
        return;
      }
      activeData.CNF = cloneCnf(cnfState);
      activeData.CNF.name = 'CNF';
      statusEl.textContent = `CNF saved; ${kindIdentifierStatusMessage()}`;
      render(activeData);
    }

    function handleCnfSave(event) {
      const button = event.target && event.target.closest
        ? event.target.closest('[data-cnf-save]')
        : null;
      if (!button) return;
      if (button.disabled) return;
      saveCnf();
    }

    function createKinds() {
      if (!activeData || !cnfState) return;
      commitVisibleCnfInputs();

      const coverage = kindIdentifierCoverage(cnfState);
      if (!coverage.ok) {
        statusEl.textContent = kindIdentifierStatusText(cnfState);
        render(activeData);
        return;
      }

      const result = materializeKindRelations(cnfState);
      let message = result.changed
        ? `Kinds created: ${result.count}`
        : 'Kinds already created';
      statusEl.textContent = message;
      render(activeData);
    }

    function handleCreateKinds(event) {
      const button = event.target && event.target.closest
        ? event.target.closest('[data-create-kinds]')
        : null;
      if (!button) return;
      if (button.disabled) return;
      createKinds();
    }

    function exportSixNf() {
      if (!activeData || !activeData['6NF']) return;
      const body = `${JSON.stringify(activeData['6NF'], null, 2)}\n`;
      const blob = new Blob([body], {type: 'application/json'});
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = 'sixth-normal-form.json';
      document.body.appendChild(link);
      link.click();
      link.remove();
      URL.revokeObjectURL(url);
      statusEl.textContent = '6NF exported';
    }

    function handleSixNfExport(event) {
      const button = event.target && event.target.closest
        ? event.target.closest('[data-six-nf-export]')
        : null;
      if (!button) return;
      if (button.disabled) return;
      exportSixNf();
    }

    function handleSectionToggle(event) {
      const button = event.target && event.target.closest
        ? event.target.closest('[data-section-toggle]')
        : null;
      if (!button) return;
      const key = button.dataset.sectionToggle;
      const body = document.getElementById(button.getAttribute('aria-controls'));
      const expanded = button.getAttribute('aria-expanded') === 'true';
      sectionCollapseState[key] = expanded;
      button.setAttribute('aria-expanded', String(!expanded));
      if (body) body.hidden = expanded;
    }

    async function compute() {
      statusEl.textContent = 'Running';
      result.innerHTML = '<div class="empty">Computing decomposition...</div>';
      kindIdentifierDraftSelections.clear();
      try {
        const response = await fetch('/api/analyze', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({text: input.value})
        });
        const data = await response.json();
        activeData = data;
        cnfState = data.errors || data.extended_conflict_free === false
          ? null
          : cloneCnf(data.CNF || data['6NF']);
        render(data);
        statusEl.textContent = response.ok ? 'Done' : 'Check input';
      } catch (error) {
        activeData = null;
        cnfState = null;
        result.innerHTML = `<div class="box full"><h3>Request Failed</h3><pre>${escapeHtml(error.message)}</pre></div>`;
        statusEl.textContent = 'Failed';
      }
    }

    result.addEventListener('click', handleSectionToggle);
    result.addEventListener('click', handleCnfSave);
    result.addEventListener('click', handleKindIdentifierAction);
    result.addEventListener('click', handleCreateKinds);
    result.addEventListener('click', handleSixNfExport);
    result.addEventListener('input', handleCnfInput);
    result.addEventListener('change', handleKindIdentifierDraftChange);
    result.addEventListener('focusout', handleCnfChange);
    result.addEventListener('keydown', handleCnfKeydown);
    document.getElementById('runButton').addEventListener('click', compute);
    document.getElementById('sampleButton').addEventListener('click', () => { input.value = sample; });
    document.getElementById('clearButton').addEventListener('click', () => {
      input.value = '';
      activeData = null;
      cnfState = null;
      kindIdentifierDraftSelections.clear();
      result.innerHTML = '<div class="empty">Compute the combined decomposition to see the result.</div>';
      statusEl.textContent = 'Ready';
    });
    document.getElementById('fileInput').addEventListener('change', async (event) => {
      const file = event.target.files[0];
      if (!file) return;
      input.value = await file.text();
      statusEl.textContent = file.name;
    });
    helpButton.addEventListener('click', showHelp);
    helpCloseButton.addEventListener('click', closeHelp);
    helpDialog.addEventListener('click', (event) => {
      if (event.target === helpDialog) closeHelp();
    });
    jointKindCancelButton.addEventListener('click', () => closeJointKindIdentifierDialog(null));
    jointKindApplyButton.addEventListener('click', confirmJointKindIdentifierDialog);
    jointKindDialog.addEventListener('click', (event) => {
      if (event.target === jointKindDialog) closeJointKindIdentifierDialog(null);
    });
    document.addEventListener('keydown', (event) => {
      if (event.key === 'Escape' && !jointKindDialog.hidden) {
        closeJointKindIdentifierDialog(null);
        return;
      }
      if (event.key === 'Enter' && !jointKindDialog.hidden && jointKindDialog.contains(document.activeElement)) {
        event.preventDefault();
        confirmJointKindIdentifierDialog();
        return;
      }
      if (event.key === 'Escape' && !helpDialog.hidden) closeHelp();
    });
  </script>
</body>
</html>
"""


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        if self.path == "/api/help":
            self._send(
                HTTPStatus.OK,
                read_help_markdown().encode("utf-8"),
                "text/markdown; charset=utf-8",
            )
            return

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
            output = analyze_combined_schema(schema_from_text(text))
            status = (
                HTTPStatus.UNPROCESSABLE_ENTITY
                if output.get("extended_conflict_free") is False
                else HTTPStatus.OK
            )
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
    parser.add_argument("--port", type=int, default=8767)
    args = parser.parse_args()

    server = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"Serving Normaliser at http://{args.host}:{args.port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
