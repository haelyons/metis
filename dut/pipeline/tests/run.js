#!/usr/bin/env node
// Test runner: concatenates src modules in build order plus tests/*.test.js and runs them in one vm context.
// Usage: node tests/run.js [module-filter]
'use strict';
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const assert = require('node:assert/strict');

const ROOT = path.resolve(__dirname, '..');
const ORDER = ['text', 'schemas', 'cost', 'pick', 'gates', 'render', 'prompts', 'screen'];   // screen: the idea loop's gate, not bundled
const filter = process.argv[2] || null;

let src = '';
for (const m of ORDER) {
  const f = path.join(ROOT, 'src', `${m}.js`);
  if (fs.existsSync(f)) src += `\n// ---- src/${m}.js ----\n${fs.readFileSync(f, 'utf8')}\n`;
  else src += `\n// ---- src/${m}.js (missing) ----\n`;
}

const tests = [];
const context = {
  assert,
  test: (name, fn) => tests.push({ name, fn }),
  fixture: (rel) => {
    const p = path.isAbsolute(rel) ? rel : path.join(ROOT, 'tests', 'fixtures', rel);
    const raw = fs.readFileSync(p, 'utf8');
    return rel.endsWith('.json') ? JSON.parse(raw) : raw;
  },
  console,
};
vm.createContext(context);

const testFiles = fs.readdirSync(path.join(ROOT, 'tests'))
  .filter((f) => f.endsWith('.test.js') && (!filter || f.startsWith(filter)))
  .sort();

try {
  vm.runInContext(src, context, { filename: 'src(concat).js' });
} catch (e) {
  console.error('module load failed:', e && e.stack || e);
  process.exit(2);
}
for (const f of testFiles) {
  try {
    vm.runInContext(fs.readFileSync(path.join(ROOT, 'tests', f), 'utf8'), context, { filename: f });
  } catch (e) {
    console.error(`test file ${f} failed to load:`, e && e.stack || e);
    process.exit(2);
  }
}

let pass = 0, fail = 0;
for (const t of tests) {
  try { t.fn(); pass++; }
  catch (e) { fail++; console.error(`FAIL ${t.name}\n  ${(e && e.stack || String(e)).split('\n').slice(0, 6).join('\n  ')}`); }
}
console.log(`${pass} passed, ${fail} failed (${testFiles.length} test files)`);
process.exit(fail ? 1 : 0);
