'use strict'
// Understudy policy for wf.js (2026-10-21). Every agent() call has a primary model and an understudy from the other
// model family (OpenCode Go models <-> Claude models run headless through the claude CLI). The policy decides which
// role a call plays, which two models it gets, and whether a failure of the primary hands the call to the understudy.
// Pure functions, no I/O; `node understudy.js --selftest` checks them.
//
// Config (config.json "understudy"; every field optional):
//   primary_family   "opencode" | "claude"          the family that answers first (CLI --family overrides)
//   mode             "fallback" | "shadow" | "swap" | "primary-only"   (CLI --mode overrides)
//                    fallback: the understudy runs only when the primary fails on a kind in retry_on
//                    shadow:   both run from the start; the primary's value is used; both outcomes are compared and
//                              logged (shadow.jsonl); the understudy's value is used only if the primary failed
//                    swap:     the understudy becomes the primary (roll a family out one route at a time)
//                    primary-only: no understudy at all
//   on_refusal       "halt" | "understudy"           a refusal (the model declined the content) is its own kind and is
//                    NOT handed over unless the run says so explicitly; the default halts the call (returns null)
//   retry_on         failure kinds that hand over: timeout, exit, runner, nojson, schema (default: all five)
//   families.<f>.models  { strong, main, cheap }     one model per tier; a pinned Workflow model (opus/sonnet/haiku)
//                    maps to a tier, so the same script gets the same tier in either family
//   families.<f>.by_role { role: model }             per-role override inside a family
//   families.claude.tools { role: "Tool,Tool" }      the Claude tool list per role (defaults below)
//   routes           [{ match: <label regex> | role: <role>, primary_family?, primary?, understudy?, mode? }]
//   profiles.<name>  { default: <role>, by_label: [{ match, role }] }   which role a call without agentType plays
//   timeouts_min     { role: minutes }

const TIER = { opus: 'strong', sonnet: 'main', haiku: 'cheap' }
const KINDS = ['none', 'refusal', 'timeout', 'exit', 'runner', 'nojson', 'schema']
const CLAUDE_OK = new Set(['sonnet', 'opus', 'haiku'])   // owner rule 2026-10-20: no Fable agents in any workflow

const familyOf = m => (/^claude\//.test(String(m)) ? 'claude' : 'opencode')
const otherFamily = f => (f === 'claude' ? 'opencode' : 'claude')
function claudeModel(m) {
  const n = String(m).replace(/^claude\//, '')
  if (!CLAUDE_OK.has(n)) throw new Error(`claude model "${m}" is not one of sonnet, opus, haiku (no Fable agents)`)
  return n
}

// Claude tool lists per role: the same rights the OpenCode agent of that role has in ocx/opencode.json
const CLAUDE_TOOLS = {
  'qt-bare': '', 'qt-web': 'WebFetch,WebSearch', 'qt-extract': 'Read',
  'qt-research': 'Read,Write,Edit,Glob,Grep,WebFetch,WebSearch', 'qt-producer': 'Read,Write,Edit,Glob,Grep,WebFetch,WebSearch',
  'triage-reader': 'Read,Grep,Glob,Bash', 'triage-runner': 'Bash,Read', 'triage-author': 'Read,Glob,Grep,Write',
  'ls-general': 'Read,Glob,Grep,Bash', 'ls-builder': 'Read,Write,Edit,Glob,Grep,Bash', 'ls-writer': 'Read,Write,Glob,Grep,Bash',
}

const DEFAULTS = {
  primary_family: 'opencode', mode: 'fallback', on_refusal: 'halt', retry_on: ['timeout', 'exit', 'runner', 'nojson', 'schema'],
  families: { opencode: { models: {} }, claude: { models: { strong: 'claude/opus', main: 'claude/sonnet', cheap: 'claude/sonnet' } } },
  routes: [], profiles: { metis: { default: 'qt-bare', by_label: [] } }, timeouts_min: {},
}

function withDefaults(cfg = {}) {
  const c = { ...DEFAULTS, ...cfg }
  c.families = { opencode: { ...DEFAULTS.families.opencode, ...(cfg.families || {}).opencode }, claude: { ...DEFAULTS.families.claude, ...(cfg.families || {}).claude } }
  c.families.claude.models = { ...DEFAULTS.families.claude.models, ...(c.families.claude.models || {}) }
  c.families.claude.tools = { ...CLAUDE_TOOLS, ...(c.families.claude.tools || {}) }
  c.profiles = { ...DEFAULTS.profiles, ...(cfg.profiles || {}) }
  return c
}

// which role a call plays: its agentType, else the profile's label rule, else the profile's default
function roleFor(cfg, profile, { label, agentType }) {
  if (agentType) return agentType
  const p = cfg.profiles[profile] || cfg.profiles.metis
  const hit = (p.by_label || []).find(r => new RegExp(r.match).test(label || ''))
  return hit ? hit.role : p.default
}

// the two models of a call and the mode they run in
function resolve(cfg, { label, role, pinned, familyOverride, modeOverride }) {
  const tier = TIER[pinned] || 'main'
  const route = (cfg.routes || []).find(r => (r.match && new RegExp(r.match).test(label || '')) || (r.role && r.role === role)) || null
  const fam = familyOverride || (route && route.primary_family) || cfg.primary_family
  const modelFor = (f, t) => { const F = cfg.families[f] || {}; return (F.by_role && F.by_role[role]) || (F.models || {})[t] || (F.models || {}).main || null }
  let primary = (route && route.primary) || modelFor(fam, tier)
  let understudy = (route && route.understudy) || modelFor(otherFamily(fam), tier)
  let mode = modeOverride || (route && route.mode) || cfg.mode
  if (mode === 'swap') { [primary, understudy] = [understudy, primary]; mode = 'fallback' }
  if (primary && understudy && familyOf(primary) === familyOf(understudy)) understudy = modelFor(otherFamily(familyOf(primary)), tier)
  return { primary, understudy, mode, tier, route: route ? (route.match || route.role) : null }
}

// the kind of a failed call, from the runner's errors and flags
function classify(res, errors) {
  if (!errors || !errors.length) return 'none'
  if (res && res.refusal) return 'refusal'
  const e = errors.join(' | ')
  if (/^timeout after/.test(e)) return 'timeout'
  if (/^runner error/.test(e)) return 'runner'
  if (/^exit( |:)/.test(e)) return 'exit'
  if (/no JSON value found|the JSON does not parse|empty reply/.test(e)) return 'nojson'
  return 'schema'
}

// does a failure of this kind hand the call to the understudy?
function handover(cfg, mode, kind) {
  if (mode === 'primary-only' || kind === 'none' || !kind) return false
  if (kind === 'refusal') return cfg.on_refusal === 'understudy'
  return (cfg.retry_on || []).includes(kind)
}

const claudeTools = (cfg, role) => (cfg.families.claude.tools[role] != null ? cfg.families.claude.tools[role] : 'Read,Glob,Grep')

function selftest() {
  const assert = require('node:assert/strict')
  const cfg = withDefaults({ families: { opencode: { models: { strong: 'opencode-go/mimo-v2.6-pro', main: 'opencode-go/mimo-v2.6-pro', cheap: 'opencode-go/glm-5.3-flash' } } },
    routes: [{ match: '^build$', primary_family: 'claude', mode: 'shadow' }, { role: 'qt-web', primary: 'opencode-go/kimi-k3' }],
    profiles: { latent_skeptic: { default: 'ls-general', by_label: [{ match: '^build$', role: 'ls-builder' }] } } })
  assert.equal(familyOf('claude/opus'), 'claude'); assert.equal(familyOf('opencode-go/kimi-k3'), 'opencode')
  assert.equal(claudeModel('claude/sonnet'), 'sonnet'); assert.throws(() => claudeModel('claude/fable'))
  assert.equal(roleFor(cfg, 'metis', { label: 'x:producer' }), 'qt-bare')
  assert.equal(roleFor(cfg, 'metis', { label: 'x', agentType: 'qt-web' }), 'qt-web')
  assert.equal(roleFor(cfg, 'latent_skeptic', { label: 'build' }), 'ls-builder')
  assert.equal(roleFor(cfg, 'latent_skeptic', { label: 'design' }), 'ls-general')
  let r = resolve(cfg, { label: 'x:producer', role: 'qt-bare', pinned: undefined })
  assert.deepEqual([r.primary, r.understudy, r.mode, r.tier], ['opencode-go/mimo-v2.6-pro', 'claude/sonnet', 'fallback', 'main'])
  r = resolve(cfg, { label: 'read:C1', role: 'triage-reader', pinned: 'opus' })
  assert.deepEqual([r.primary, r.understudy, r.tier], ['opencode-go/mimo-v2.6-pro', 'claude/opus', 'strong'])
  r = resolve(cfg, { label: 'build', role: 'ls-builder', pinned: 'opus' })
  assert.deepEqual([r.primary, r.understudy, r.mode, r.route], ['claude/opus', 'opencode-go/mimo-v2.6-pro', 'shadow', '^build$'])
  r = resolve(cfg, { label: 'y', role: 'qt-web', pinned: 'sonnet' })
  assert.deepEqual([r.primary, r.understudy], ['opencode-go/kimi-k3', 'claude/sonnet'])
  r = resolve(cfg, { label: 'z', role: 'qt-bare', pinned: 'sonnet', familyOverride: 'claude', modeOverride: 'swap' })
  assert.deepEqual([r.primary, r.understudy, r.mode], ['opencode-go/mimo-v2.6-pro', 'claude/sonnet', 'fallback'])
  assert.equal(classify(null, []), 'none'); assert.equal(classify({ refusal: true }, ['refusal']), 'refusal')
  assert.equal(classify(null, ['timeout after 10 min']), 'timeout'); assert.equal(classify(null, ['exit 1: boom']), 'exit')
  assert.equal(classify(null, ['runner error: spawn']), 'runner'); assert.equal(classify(null, ['no JSON value found in the reply']), 'nojson')
  assert.equal(classify(null, ['$: missing "x"']), 'schema')
  assert.equal(handover(cfg, 'fallback', 'timeout'), true); assert.equal(handover(cfg, 'fallback', 'refusal'), false)
  assert.equal(handover(withDefaults({ on_refusal: 'understudy' }), 'fallback', 'refusal'), true)
  assert.equal(handover(cfg, 'primary-only', 'timeout'), false); assert.equal(handover(cfg, 'fallback', 'none'), false)
  assert.equal(handover(withDefaults({ retry_on: ['timeout'] }), 'fallback', 'schema'), false)
  assert.equal(claudeTools(cfg, 'qt-bare'), ''); assert.equal(claudeTools(cfg, 'ls-builder'), 'Read,Write,Edit,Glob,Grep,Bash'); assert.equal(claudeTools(cfg, 'unknown-role'), 'Read,Glob,Grep')
  console.log('understudy selftest: 30 checks passed')
}

module.exports = { TIER, KINDS, familyOf, otherFamily, claudeModel, withDefaults, roleFor, resolve, classify, handover, claudeTools, CLAUDE_TOOLS }
if (require.main === module && process.argv.includes('--selftest')) selftest()
