#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

from combined_null_4nf_decomposer import analyze_combined_schema, schema_from_text


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
    .result-section-title {
      margin: 0 0 12px;
      padding: 7px 10px;
      border-left: 4px solid var(--accent);
      background: var(--soft);
      border-radius: 6px;
      color: var(--ink);
      font-size: 15px;
      font-weight: 720;
    }
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
      background: #e4f7e8;
      border-color: #a8d8b1;
    }
    .attribute-token sup {
      margin-left: 1px;
      color: var(--warn);
      font-size: 9px;
      font-weight: 760;
      line-height: 1;
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
      textarea, .result { min-height: 420px; }
      .status { white-space: normal; }
    }
  </style>
</head>
<body>
  <main>
    <header>
      <h1>Normaliser</h1>
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
        <textarea id="input" spellcheck="false">database schema registry:
relation legal-company: companyID SSN director surname postcode city email

nullable: companyID SSN director surname

companyID ->N<- SSN
companyID <-N-> director
SSN <-N-> surname

companyID -> director postcode
SSN -> surname postcode
postcode -> city
companyID ->> email
SSN ->> email</textarea>
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

  <script>
    const input = document.getElementById('input');
    const result = document.getElementById('result');
    const statusEl = document.getElementById('status');

    const sample = `database schema registry:
relation legal-company: companyID SSN director surname postcode city email

nullable: companyID SSN director surname

companyID ->N<- SSN
companyID <-N-> director
SSN <-N-> surname

companyID -> director postcode
SSN -> surname postcode
postcode -> city
companyID ->> email
SSN ->> email`;

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

    function unique(items) {
      return Array.from(new Set((items || []).filter(item => item !== undefined && item !== null && String(item).length)));
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

    function attrPostfixNumber(attribute) {
      const match = String(attribute).match(/#(\d+)$/);
      return match ? Number(match[1]) : 0;
    }

    function relationPostfixNumber(attributes) {
      const numbers = (attributes || []).map(attrPostfixNumber);
      return numbers.length ? Math.min(...numbers) : 0;
    }

    function renderAttributes(attributes, nullable = [], keyAttributes = []) {
      if (!attributes || attributes.length === 0) return '<span class="dep-list-empty">none</span>';
      const nullableSet = attrSet(nullable);
      const keySet = attrSet(keyAttributes);
      return `<div class="attribute-list">${attributes.map(attribute => {
        const nullableMark = nullableSet.has(attribute) ? '<sup>N</sup>' : '';
        const cls = keySet.has(attribute) ? 'attribute-token key-attribute' : 'attribute-token';
        return `<span class="${cls}">${escapeHtml(attribute)}${nullableMark}</span>`;
      }).join('')}</div>`;
    }

    function renderDependencyList(dependencies) {
      const items = unique(dependencies);
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

    function renderSection(title, content) {
      return `<div class="result-section"><h3 class="result-section-title">${escapeHtml(title)}</h3>${content}</div>`;
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

    function inclusionText(dep) {
      return dep.text || `${fmtSet(dep.lhs || [])} ${inclusionSymbol(dep)} ${fmtSet(dep.rhs || [])}`;
    }

    function inclusionSymbol(dep) {
      const split = dep && dep.text ? splitDependencyText(dep.text) : null;
      if (split && ['==', 'o=>', 'x=>', '=>'].includes(split.symbol)) return split.symbol;
      if (dep && dep.symbol) return dep.symbol;
      if (dep && dep.kind === 'equality') return '==';
      if (dep && dep.kind === 'covering') return 'o=>';
      if (dep && dep.kind === 'disjoint') return 'x=>';
      return '=>';
    }

    function isLocalInclusionForAttributes(dep, attributes) {
      return isSubset([...(dep.lhs || []), ...(dep.rhs || [])], attrSet(attributes || []));
    }

    function isLocalInclusionForAnyRelation(dep, relations) {
      return (relations || []).some(relation => isLocalInclusionForAttributes(dep, relation.attributes || []));
    }

    function crossInclusionTextsForRelations(inclusions, relations) {
      return (inclusions || [])
        .filter(dep => !isLocalInclusionForAnyRelation(dep, relations || []))
        .map(inclusionText);
    }

    function localInclusionTextsForItem(data, item) {
      return (data.inclusion_dependencies || [])
        .filter(dep => isLocalInclusionForAttributes(dep, item.attributes || []))
        .map(inclusionText);
    }

    function detailsDisplayData(data) {
      const displayData = JSON.parse(JSON.stringify(data));
      const sourceRelations = getSourceRelations(data);
      const isLocalToSource = dep => sourceRelations.some(relation => isLocalInclusionForAttributes(dep, relation.attributes || []));

      displayData.inclusion_dependencies = (displayData.inclusion_dependencies || []).filter(isLocalToSource);
      displayData.database_schemas = (displayData.database_schemas || []).map(database => {
        const schemaRelations = database.relations || [];
        const isLocalToSchema = dep => schemaRelations.some(relation => isLocalInclusionForAttributes(dep, relation.attributes || []));
        return {
          ...database,
          inclusion_dependencies: (database.inclusion_dependencies || []).filter(isLocalToSchema),
        };
      });
      displayData.per_input_relation = (displayData.per_input_relation || []).map(item => {
        const applicableInclusions = localInclusionTextsForItem(data, item);
        return {
          ...item,
          applicable_fds: displayDependenciesForRelation(item.input_relation, item.attributes || [], item.applicable_fds || []),
          applicable_inclusion_dependencies: applicableInclusions,
          per_relation_4nf: (item.per_relation_4nf || []).map(perRelation => ({
            ...perRelation,
            applicable_fds: displayDependenciesForRelation(
              perRelation.sql_null_relation_name || '',
              perRelation.renamed_sql_null_relation || perRelation.sql_null_relation || [],
              perRelation.applicable_fds || []
            ),
            steps: displayStepsForRelation(perRelation.steps || [], perRelation.sql_null_relation_name || ''),
          })),
        };
      });
      return displayData;
    }

    function displayDependenciesForRelation(relationName, attributes, dependencies) {
      const items = unique(dependencies);
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
      return displayed;
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
          .filter(dep => isSubset([...(dep.lhs || []), ...(dep.rhs || [])], relationAttrs))
          .map(inclusionText);
        const dependencies = unique([
          ...(item.applicable_sql_null_dependencies || []),
          ...(item.applicable_fds || []),
          ...(item.applicable_mvds || []),
          ...localInclusions,
        ]);
        return `<div class="box relation-box">
          <h3>${escapeHtml(relation.name)}</h3>
          ${renderAttributes(relation.attributes || [], relation.nullable || [], relationKeyAttributes(relation.attributes || [], dependencies))}
          ${renderDependencyBox(dependencies, relation.name, relation.attributes || [])}
        </div>`;
      }).join('');
      return `<div class="grid relation-grid">${relationBoxes}${renderCrossRelationBox(crossInclusions)}</div>`;
    }

    function canonicalAttributes(attributes) {
      return [...(attributes || [])].sort((a, b) => a.localeCompare(b, undefined, {numeric: true})).join('\u0001');
    }

    function renameAttributeForRelation(attribute, relationName) {
      const match = String(relationName || '').match(/#(\d+)$/);
      return match ? `${attribute}#${match[1]}` : attribute;
    }

    function splitDependencyText(text) {
      for (const symbol of ['<-N->', '->N<-', '-N->', '->>', 'o=>', 'x=>', '==', '->', '=>']) {
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

    function dependencyAttributes(text, knownAttributes = []) {
      const split = splitDependencyText(text);
      if (!split) return [];
      return [
        ...parseAttributeSide(split.lhs, knownAttributes),
        ...parseAttributeSide(split.rhs, knownAttributes),
      ];
    }

    function mappedInclusion(dep, origin) {
      return {
        lhs: (dep.lhs || []).map(attr => renameAttributeForRelation(attr, origin.perRelation.sql_null_relation_name)),
        rhs: (dep.rhs || []).map(attr => renameAttributeForRelation(attr, origin.perRelation.sql_null_relation_name)),
      };
    }

    function targetAttributePrefixGroups(targetRelations) {
      const byPrefix = new Map();
      for (const relation of targetRelations || []) {
        for (const attribute of relation.attributes || []) {
          const match = String(attribute).match(/^(.*)#(\d+)$/);
          if (!match || !match[1]) continue;
          const prefix = match[1];
          if (!byPrefix.has(prefix)) byPrefix.set(prefix, new Map());
          byPrefix.get(prefix).set(Number(match[2]), attribute);
        }
      }

      return Array.from(byPrefix.entries())
        .map(([prefix, attributesByNumber]) => ({
          prefix,
          attributes: Array.from(attributesByNumber.entries())
            .sort((a, b) => a[0] - b[0])
            .map(entry => entry[1]),
        }))
        .filter(group => group.attributes.length >= 2)
        .sort((a, b) => a.prefix.localeCompare(b.prefix, undefined, {numeric: true}));
    }

    function buildTargetRelations(data) {
      const byKey = new Map();
      for (const attributes of data.final_decomposition || []) {
        const key = canonicalAttributes(attributes);
        byKey.set(key, {
          name: relationNameFor(attributes),
          attributes: [...attributes].sort((a, b) => a.localeCompare(b, undefined, {numeric: true})),
          origins: [],
        });
      }
      for (const inputItem of data.per_input_relation || []) {
        for (const perRelation of inputItem.per_relation_4nf || []) {
          for (const attributes of perRelation.four_nf_decomposition || []) {
            const key = canonicalAttributes(attributes);
            if (!byKey.has(key)) {
              byKey.set(key, {
                name: relationNameFor(attributes),
                attributes: [...attributes].sort((a, b) => a.localeCompare(b, undefined, {numeric: true})),
                origins: [],
              });
            }
            byKey.get(key).origins.push({
              inputItem,
              perRelation,
              sourceAttributes: attrSet(inputItem.attributes || []),
              sqlNullAttributes: attrSet(perRelation.sql_null_relation || []),
            });
          }
        }
      }
      const relations = Array.from(byKey.values());
      for (const group of targetAttributePrefixGroups(relations)) {
        addTargetKeyRelation(relations, group.prefix);
      }
      for (const relation of Array.from(relations)) {
        const baseDependencies = targetBaseRelationDependencies(relation, data);
        for (const inclusion of targetKeyInclusionsForRelation(relation, baseDependencies)) {
          const split = splitDependencyText(inclusion);
          if (!split || split.symbol !== 'x=>') continue;
          for (const attr of parseAttributeSide(split.rhs, relation.attributes || [])) {
            addTargetKeyRelation(relations, attr);
          }
        }
      }
      return relations.sort((a, b) => {
        const numberCompare = relationPostfixNumber(a.attributes) - relationPostfixNumber(b.attributes);
        if (numberCompare !== 0) return numberCompare;
        return a.name.localeCompare(b.name, undefined, {numeric: true});
      });
    }

    function addTargetKeyRelation(relations, attribute) {
      if (!attribute) return;
      const name = `${attribute}_K`;
      if (relations.some(relation => relation.name === name)) return;
      relations.push({
        name,
        attributes: [attribute],
        origins: [],
      });
    }

    function targetBaseRelationDependencies(target, data) {
      const targetAttrs = attrSet(target.attributes);
      const dependencies = [];
      for (const origin of target.origins || []) {
        for (const dep of origin.perRelation.applicable_fds || []) {
          if (isSubset(dependencyAttributes(dep, target.attributes), targetAttrs)) dependencies.push(dep);
        }
        for (const dep of origin.perRelation.applicable_mvds || []) {
          const functionalText = dep.replace('->>', '->');
          if (isSubset(dependencyAttributes(functionalText, target.attributes), targetAttrs)) dependencies.push(functionalText);
        }
        for (const dep of data.inclusion_dependencies || []) {
          if (!isSubset([...(dep.lhs || []), ...(dep.rhs || [])], origin.sourceAttributes)) continue;
          const mapped = mappedInclusion(dep, origin);
          if (isSubset([...mapped.lhs, ...mapped.rhs], targetAttrs)) {
            dependencies.push(`${fmtSet(mapped.lhs)} ${inclusionSymbol(dep)} ${fmtSet(mapped.rhs)}`);
          }
        }
      }
      return unique(dependencies);
    }

    function targetKeyInclusionsForRelation(target, dependencies) {
      const targetAttrs = attrSet(target.attributes);
      const functionalDependencies = unique(dependencies)
        .map(dep => functionalDependencyParts(dep, target.attributes))
        .filter(dep => dep && isSubset([...dep.lhs, ...dep.rhs], targetAttrs));
      if (!functionalDependencies.length) return [];

      const inclusions = [];
      const emitted = new Set();
      for (const dep of functionalDependencies) {
        if (!isSubset(target.attributes, closure(dep.lhs, functionalDependencies))) continue;

        const keyAttrs = dep.lhs;
        const dependentAttrs = (target.attributes || []).filter(attr => !keyAttrs.includes(attr));
        const pairs = [];
        if (keyAttrs.length === 1) {
          for (const attr of dependentAttrs) pairs.push({lhs: [attr], rhs: keyAttrs});
        } else if (dependentAttrs.length === keyAttrs.length) {
          pairs.push({lhs: dependentAttrs, rhs: keyAttrs});
        }

        for (const pair of pairs) {
          const base = `${canonicalAttributes(pair.lhs)}\u0002${canonicalAttributes(pair.rhs)}`;
          if (emitted.has(base)) continue;
          inclusions.push(`${fmtSet(pair.lhs)} x=> ${fmtSet(pair.rhs)}`);
          inclusions.push(`${fmtSet(pair.lhs)} o=> ${fmtSet(pair.rhs)}`);
          emitted.add(base);
        }
      }
      return inclusions;
    }

    function targetRelationDependencies(target, data) {
      const baseDependencies = targetBaseRelationDependencies(target, data);
      return unique([
        ...baseDependencies,
        ...targetKeyInclusionsForRelation(target, baseDependencies),
      ]);
    }

    function targetGeneratedPrefixInclusions(targetRelations) {
      const dependencies = [];
      for (const group of targetAttributePrefixGroups(targetRelations)) {
        dependencies.push(`${fmtSet(group.attributes)} x=> ${fmtSet([group.prefix])}`);
        dependencies.push(`${fmtSet(group.attributes)} o=> ${fmtSet([group.prefix])}`);
      }
      return dependencies;
    }

    function targetCrossInclusionTexts(data, targetRelations) {
      const sourceCrossInclusions = crossInclusionTextsForRelations(
        data.inclusion_dependencies || [],
        getSourceRelations(data)
      );
      return unique([
        ...sourceCrossInclusions,
        ...targetGeneratedPrefixInclusions(targetRelations),
      ]);
    }

    function functionalDependencyParts(dependency, knownAttributes) {
      const split = splitDependencyText(dependency);
      if (!split || split.symbol !== '->') return null;
      return {
        lhs: parseAttributeSide(split.lhs, knownAttributes),
        rhs: parseAttributeSide(split.rhs, knownAttributes),
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

    function relationKeyAttributes(attributes, dependencies) {
      const targetAttrs = attrSet(attributes);
      const functionalDependencies = unique(dependencies)
        .map(dep => functionalDependencyParts(dep, attributes))
        .filter(dep => dep && isSubset([...dep.lhs, ...dep.rhs], targetAttrs));
      const keyAttrs = new Set();
      for (const dep of functionalDependencies) {
        if (isSubset(attributes, closure(dep.lhs, functionalDependencies))) {
          for (const attr of dep.lhs) keyAttrs.add(attr);
        }
      }
      return Array.from(keyAttrs);
    }

    function renderTarget(data) {
      const targetRelations = buildTargetRelations(data);
      const crossInclusions = targetCrossInclusionTexts(data, targetRelations);
      const relationBoxes = targetRelations.map(target => {
        const dependencies = targetRelationDependencies(target, data);
        return `<div class="box relation-box">
          <h3>${escapeHtml(target.name)}</h3>
          ${renderAttributes(target.attributes, [], relationKeyAttributes(target.attributes, dependencies))}
          ${renderDependencyBox(dependencies, target.name, target.attributes)}
        </div>`;
      }).join('');
      return `<div class="grid relation-grid">${relationBoxes}${renderCrossRelationBox(crossInclusions)}</div>`;
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
            <div class="box"><h3>Applicable FDs</h3><div class="chips">${chips(displayedFds, 'dep')}</div></div>
            <div class="box"><h3>Applicable MVDs</h3><div class="chips">${chips(mvds, 'dep')}</div></div>
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
            <div class="box"><h3>Applicable Dependencies</h3><div class="chips">${chips(applicableDependencies, 'dep')}</div></div>
            <div class="box sql-null-box"><h3>SQL-null Decomposition</h3><div class="chips">${chips(namedSqlNull)}</div></div>
            <div class="box"><h3>Final NF</h3><div class="chips">${chips(final)}</div></div>
            <div class="box full"><h3>Removed Relations</h3>${renderRemoved(stage.removed_relations || {})}</div>
          </div>
          <div class="grid">${renderPerRelation(item.per_relation_4nf)}</div>
        </div>`;
      }).join('');
    }

    function render(data) {
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
      let html = renderSection('Source', renderSource(data));
      html += renderSection('Target', renderTarget(data));

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
      result.innerHTML = '<div class="empty">Compute the combined decomposition to see the result.</div>';
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
            output = analyze_combined_schema(schema_from_text(text))
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
    parser.add_argument("--port", type=int, default=8767)
    args = parser.parse_args()

    server = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"Serving Normaliser at http://{args.host}:{args.port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
