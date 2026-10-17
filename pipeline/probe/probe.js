export const meta = {
  name: 'qt-role-probe',
  description: 'Stage-1 probe: one qt-bare and one qt-research agent in parallel, each asked for a tiny schema without tools; checks the restricted roles return their schema and gives tools/measure_floor.py two transcripts to measure',
  phases: [{ title: 'Probe', detail: 'qt-bare returns {a, b, c}; qt-research returns {ok} without using tools' }],
}

const A = (typeof args === 'string' ? JSON.parse(args) : args) || {}
const OV = A.agent_types || {}
const TYPES = { 'probe:qt-bare': OV['qt-bare'] || 'qt-bare', 'probe:qt-research': OV['qt-research'] || 'qt-research' }
const [bare, research] = await parallel([
  () => agent('Return this record and nothing else: a = 1, b = "x", c = true. Do not use any tool.', {
    label: 'probe:qt-bare', phase: 'Probe', agentType: TYPES['probe:qt-bare'],
    schema: { type: 'object', properties: { a: { type: 'integer' }, b: { type: 'string' }, c: { type: 'boolean' } }, required: ['a', 'b', 'c'] },
  }),
  () => agent('Return the record {ok: true}. Do not use any tool.', {
    label: 'probe:qt-research', phase: 'Probe', agentType: TYPES['probe:qt-research'],
    schema: { type: 'object', properties: { ok: { type: 'boolean' } }, required: ['ok'] },
  }),
])
return {
  bare, research, agent_types: TYPES,
  bare_ok: !!bare && bare.a === 1 && bare.b === 'x' && bare.c === true,
  research_ok: !!research && research.ok === true,
}
