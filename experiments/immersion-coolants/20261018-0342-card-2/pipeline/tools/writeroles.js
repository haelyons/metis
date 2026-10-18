// Writes the role files /home/hal/stage/.claude/agents/<name>.md from ROLE_FILES in src/prompts.js. Usage: node tools/writeroles.js
const fs = require('fs'), vm = require('vm'), path = require('path')
const ROOT = path.join(__dirname, '..'), AGENTS = path.join(ROOT, '..', '.claude', 'agents')
const ctx = {}; vm.createContext(ctx)
vm.runInContext(fs.readFileSync(path.join(ROOT, 'src/prompts.js'), 'utf8') + '\n;this.__ = ROLE_FILES', ctx)
fs.mkdirSync(AGENTS, { recursive: true })
for (const [name, md] of Object.entries(ctx.__)) fs.writeFileSync(path.join(AGENTS, `${name}.md`), md)
console.log('wrote', Object.keys(ctx.__).map(n => `${n}.md`).join(', '), 'to', AGENTS)
