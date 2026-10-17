#!/usr/bin/env node
// Build: dist/question_tree_v2.js and dist/replay_v2.js = `export const meta` header + modules + body.
// The Workflow runtime needs one self-contained plain-JS file starting with `export const meta = {...}`.
'use strict';
const fs = require('node:fs');
const path = require('node:path');

const ROOT = __dirname;
const ORDER = ['text', 'schemas', 'cost', 'pick', 'gates', 'render', 'prompts'];
const MARK = '// @@MODULES@@';
const FORBIDDEN = [/\bimport\s/, /\bexport\s(?!const meta)/, /\brequire\(/, /module\.exports/, /Math\.random\(/, /Date\.now\(/, /new Date\(\s*\)/];

function modules() {
  return ORDER.map((m) => {
    const f = path.join(ROOT, 'src', `${m}.js`);
    if (!fs.existsSync(f)) throw new Error(`missing src/${m}.js`);
    const s = fs.readFileSync(f, 'utf8');
    for (const re of FORBIDDEN) if (re.test(s)) throw new Error(`src/${m}.js violates ${re}`);
    return `// ---- src/${m}.js ----\n${s}`;
  }).join('\n\n');
}

function buildOne(bodyFile, outFile) {
  const body = fs.readFileSync(path.join(ROOT, 'src', bodyFile), 'utf8');
  if (!body.startsWith('export const meta')) throw new Error(`${bodyFile} must start with "export const meta"`);
  if (!body.includes(MARK)) throw new Error(`${bodyFile} lacks ${MARK}`);
  for (const re of FORBIDDEN) if (re.test(body.replace(/^export const meta/, ''))) throw new Error(`${bodyFile} violates ${re}`);
  // replacer function: a string replacement would expand `$&`, `$$`, `$'` found inside the module text
  const out = body.replace(MARK, () => modules());
  if (out.includes(MARK)) throw new Error('marker survived the build');
  fs.mkdirSync(path.join(ROOT, 'dist'), { recursive: true });
  fs.writeFileSync(path.join(ROOT, 'dist', outFile), out);
  // syntax check only (the body uses harness globals agent/pipeline/parallel/log/args at run time;
  // top-level await and return are legal inside an async function body)
  const AsyncFunction = Object.getPrototypeOf(async function () {}).constructor;
  new AsyncFunction(out.replace(/^export const meta/, 'const meta'));
  console.log(`built dist/${outFile} (${out.length} bytes)`);
}

const which = process.argv[2] || 'all';
if (which === 'all' || which === 'main') buildOne('main.js', 'question_tree_v2.js');
if (which === 'all' || which === 'replay') buildOne('replay.js', 'replay_v2.js');
