'use strict'
// Family dispatcher: one call goes to OpenCode (oc.js) or to Claude headless (claude_cli.js) by its model name.
// WF_STUB=<module> replaces both with a stub (tools/e2e_wf.js) for runs without network or models.
const path = require('node:path')
const { familyOf } = require('./understudy.js')
const stub = process.env.WF_STUB ? require(path.resolve(process.env.WF_STUB)) : null

async function run(o) {
  if (stub) return stub.run(o)
  if (familyOf(o.model) === 'claude') return require('./claude_cli.js').run(o)
  return require('./oc.js').run(o)
}
async function exportSession(model, sessionID, outPath) {
  if (stub) return stub.exportSession ? stub.exportSession(sessionID, outPath) : false
  if (familyOf(model) === 'claude') return false   // the raw result envelope is already in the call's folder
  return require('./oc.js').exportSession(sessionID, outPath)
}
module.exports = { run, exportSession, familyOf }
