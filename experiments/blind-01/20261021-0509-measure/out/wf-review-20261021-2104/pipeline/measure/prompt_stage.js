export const meta = { name: 'prompt-stage', description: 'One instruction file as one agent() call: the gate writer or the launch reviewer of a measure run, on wf.js with understudies', phases: [{ title: 'Stage' }] }
// args: { prompt (the instruction text), role (agentType, e.g. ls-writer), model ('sonnet'|'opus'), label, reply_pattern (regex the one-line reply must match) }
const A = (typeof args === 'string' ? JSON.parse(args) : args) || {}
if (!A.prompt || !A.role || !A.label) return { error: 'prompt_stage needs prompt, role and label' }
phase('Stage')
const reply = await agent(A.prompt, { label: A.label, agentType: A.role, model: A.model || 'sonnet' })
if (reply == null) return { failed: true, stage: A.label }
const line = String(reply).trim().split('\n').pop()
const ok = A.reply_pattern ? new RegExp(A.reply_pattern).test(line) : true
return { stage: A.label, reply: line, conforming: ok }
