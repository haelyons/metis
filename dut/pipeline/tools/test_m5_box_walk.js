'use strict'
// m5_box_walk.js: vanished entries (ENOENT, ENOTDIR) are skipped; any other error is thrown.
const fs = require('node:fs'), os = require('node:os'), path = require('node:path')
const assert = require('node:assert/strict')
const boxWalk = require('./m5_box_walk.js')
const scratch = fs.mkdtempSync(path.join(os.tmpdir(), 'test_m5_box_walk_'))
let checks = 0, failures = 0
function check(label, test) {
  checks++
  try { test(); console.log(`ok ${label}`) } catch (error) { failures++; console.log(`FAIL ${label}: ${error.message}`) }
}
try {
  const file = path.join(scratch, 'a.sh')
  fs.writeFileSync(file, 'text')
  check('present directory and file are read', () => {
    assert.deepEqual(boxWalk.entries(scratch).map(entry => entry.name), ['a.sh'])
    assert.equal(boxWalk.text(file), 'text')
  })
  check('removed directory lists as empty (ENOENT)', () => assert.deepEqual(boxWalk.entries(path.join(scratch, 'gone')), []))
  check('removed file reads as undefined (ENOENT)', () => assert.equal(boxWalk.text(path.join(scratch, 'gone.sh')), undefined))
  check('directory replaced by a file lists as empty (ENOTDIR)', () => assert.deepEqual(boxWalk.entries(file), []))
  check('path under a file reads as undefined (ENOTDIR)', () => assert.equal(boxWalk.text(path.join(file, 'x')), undefined))
  check('other errors are thrown (EISDIR)', () => assert.throws(() => boxWalk.text(scratch), { code: 'EISDIR' }))
  if (process.getuid?.() !== 0) {
    const locked = path.join(scratch, 'locked')
    fs.mkdirSync(locked, { mode: 0o000 })
    check('other errors are thrown (EACCES)', () => assert.throws(() => boxWalk.entries(locked), { code: 'EACCES' }))
    fs.chmodSync(locked, 0o700)
  }
} finally { fs.rmSync(scratch, { recursive: true, force: true }) }
console.log(failures ? `${failures} of ${checks} check(s) FAILED` : `all ${checks} checks passed`)
process.exit(failures ? 1 : 0)
