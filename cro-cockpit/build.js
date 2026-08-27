#!/usr/bin/env node
/**
 * Bundles the cockpit into one self-contained HTML file (dist/cro-cockpit.html)
 * so it can be opened from disk or published as an artifact.
 *
 * The modules are plain ES modules with named imports/exports only, so a
 * topological concatenation plus stripping the module keywords is enough — no
 * dependency needed to build this project.
 */

import { readFileSync, writeFileSync, mkdirSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = dirname(fileURLToPath(import.meta.url));

/** Dependency order: a module only ever imports from those above it. */
const MODULES = [
  'src/rules.js',
  'src/dom.js',
  'src/charts.js',
  'src/data.js',
  'src/store.js',
  'src/views/dashboard.js',
  'src/views/table.js',
  'src/views/emails.js',
  'src/views/review.js',
  'src/views/exceptions.js',
  'src/views/perf.js',
  'src/views/settings.js',
  'src/views/drawer.js',
  'src/app.js',
];

const read = (p) => readFileSync(join(root, p), 'utf8');

function stripModuleSyntax(source, file) {
  let out = source
    // import { a, b } from './x.js';  (single or multi-line)
    .replace(/^import\s+[\s\S]*?from\s+'[^']+';\s*$/gm, '')
    .replace(/^import\s+'[^']+';\s*$/gm, '')
    // export const / function / class / let
    .replace(/^export\s+(?=(const|let|var|function|async|class)\b)/gm, '')
    // export { a, b };
    .replace(/^export\s*\{[^}]*\};\s*$/gm, '');

  if (/(^|\n)\s*(import|export)\s/.test(out)) {
    throw new Error(`Unhandled module syntax in ${file}`);
  }
  return `/* ── ${file} ─────────────────────────────────────────── */\n${out.trim()}\n`;
}

const bundle = MODULES.map((f) => stripModuleSyntax(read(f), f)).join('\n');
const css = read('src/styles.css');

const html = read('index.html')
  .replace('<link rel="stylesheet" href="src/styles.css">', `<style>\n${css}\n</style>`)
  .replace(/<script type="module">[\s\S]*?<\/script>/, [
    '<script type="module">',
    bundle,
    'start(document.getElementById(\'root\'));',
    '</script>',
  ].join('\n'));

mkdirSync(join(root, 'dist'), { recursive: true });
writeFileSync(join(root, 'dist/cro-cockpit.html'), html);

// Artifact variant: page content only — the host supplies the document shell,
// so <!doctype>, <html>, <head> and <body> must not appear.
const artifact = html
  .replace(/^[\s\S]*?<meta name="description"/, '<meta name="description"')
  .replace(/<\/head>\s*<body>/, '')
  .replace(/<\/body>\s*<\/html>\s*$/, '')
  .trim();
writeFileSync(join(root, 'dist/artifact.html'), `<title>CRO Approval Cockpit</title>\n${artifact}`);

console.log(`dist/cro-cockpit.html — ${(html.length / 1024).toFixed(0)} KB from ${MODULES.length} modules`);
console.log(`dist/artifact.html    — ${(artifact.length / 1024).toFixed(0)} KB (publishable page content)`);
