// Writes the latent_skeptic roles into idea/ocx/opencode.json as OpenCode agents, from dut/latent_skeptic/agents/*.md
// (prompt = the file body; permissions = the file's tools), plus the three generic roles its scripts need without an
// agentType (ls-general, ls-builder, ls-writer). The same prompts reach Claude as appended system prompts (wf.js), so a
// role reads the same text in either family. Usage: node tools/ocx_roles.js
const fs = require('node:fs'), path = require('node:path')
const ROOT = path.join(__dirname, '..'), CFG = path.join(ROOT, 'idea', 'ocx', 'opencode', 'opencode.json'), MD = path.join(ROOT, '..', 'latent_skeptic', 'agents')
const PERM = { Read: ['read'], Grep: ['grep'], Glob: ['glob'], Bash: ['bash'], Write: ['write'], Edit: ['edit'], WebFetch: ['webfetch'], WebSearch: ['websearch'] }
const cfg = JSON.parse(fs.readFileSync(CFG, 'utf8'))
const perm = tools => Object.fromEntries([['*', 'deny'], ...tools.flatMap(t => PERM[t] || []).map(k => [k, 'allow']), ['external_directory', 'deny'], ['doom_loop', 'deny']])
let n = 0
for (const f of fs.readdirSync(MD).filter(f => f.endsWith('.md'))) {
  const s = fs.readFileSync(path.join(MD, f), 'utf8'), m = s.match(/^---\n([\s\S]*?)\n---\n([\s\S]*)$/)
  if (!m) continue
  const fm = Object.fromEntries(m[1].split('\n').map(l => l.split(/:\s(.*)/s)).filter(x => x[0]).map(([k, v]) => [k.trim(), (v || '').trim()]))
  const tools = fm.tools.split(',').map(t => t.trim())
  cfg.agent[fm.name] = { mode: 'primary', description: fm.description, prompt: m[2].trim(), permission: perm(tools), tools_md: fm.tools }
  n++
}
cfg.agent['ls-general'] = { mode: 'primary', description: 'Reads the files the prompt names and returns the record asked for', prompt: 'You read the files the prompt names and nothing else; you may run read-only shell commands to inspect them. You write no files. You return only the JSON or text asked for.', permission: perm(['Read', 'Glob', 'Grep', 'Bash']), tools_md: 'Read, Glob, Grep, Bash' }
cfg.agent['ls-builder'] = { mode: 'primary', description: 'Builds the execution layer of one pre-registered experiment', prompt: 'You implement exactly the spec you are given, in the files the prompt names, and run only the local checks it names. You never patch infrastructure or rescope the design: when something is broken or ambiguous you stop and report. You return only the record asked for.', permission: perm(['Read', 'Write', 'Edit', 'Glob', 'Grep', 'Bash']), tools_md: 'Read, Write, Edit, Glob, Grep, Bash' }
cfg.agent['ls-writer'] = { mode: 'primary', description: 'Writes the takeaways file under the contract and runs the gates on it', prompt: 'You write the one file the prompt names from the sources it names, run the gate scripts it names on that file, and rewrite until they pass. You return only what the prompt asks for.', permission: perm(['Read', 'Write', 'Glob', 'Grep', 'Bash']), tools_md: 'Read, Write, Glob, Grep, Bash' }
fs.writeFileSync(CFG, JSON.stringify(cfg, null, 2) + '\n')
console.log(`wrote ${n} triage roles + 3 generic roles into ${path.relative(ROOT, CFG)}: ${Object.keys(cfg.agent).join(', ')}`)
