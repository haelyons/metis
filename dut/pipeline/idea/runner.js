'use strict'
// Family dispatcher: OpenCode, Claude headless, Codex CLI or Cursor Agent, selected by model name.
// WF_STUB=<module> replaces every family with a stub (tools/e2e_wf.js) for runs without network or models.
const path = require('node:path')
const { familyOf } = require('./understudy.js')
const stub = process.env.WF_STUB ? require(path.resolve(process.env.WF_STUB)) : null

async function run(o) {
  if (stub) return stub.run(o)
  if (familyOf(o.model) === 'claude') return require('./claude_cli.js').run(o)
  if (familyOf(o.model) === 'codex') return require('./codex_cli.js').run(o)
  if (familyOf(o.model) === 'cursor') return require('./cursor_cli.js').run(o)
  return require('./oc.js').run(o)
}
async function exportSession(model, sessionID, outPath) {
  if (stub) return stub.exportSession ? stub.exportSession(sessionID, outPath) : false
  if (familyOf(model) !== 'opencode') return false   // raw CLI output is already in the call's folder
  return require('./oc.js').exportSession(sessionID, outPath)
}
module.exports = { run, exportSession, familyOf }
