export const meta = { name: 'tests-author', description: 'A claim-blind author writes the acceptance tests of a measure run from the directive and the contract, never from the implementation; the builder never sees them; the runner executes them in the shipped environment before the physics', phases: [{ title: 'Author' }] }
// args: { directive (EXEC_NOTE.md path), contract (frozen/ONBOX_CONTRACT.md path), design_record (path), question (QUESTION.md path),
//         out_file (where the one test file is written, e.g. <mdir>/tests/tests_<tag>.py), tag, results_dir_on_box (e.g. results_<tag>/out) }
const A = (typeof args === 'string' ? JSON.parse(args) : args) || {}
if (!A.directive || !A.out_file || !A.tag) return { error: 'tests stage needs directive, out_file, tag' }
phase('Author')
const SCHEMA = { type: 'object', additionalProperties: false, required: ['file', 'behaviours', 'count', 'needs_gpu'],
  properties: { file: { type: 'string' }, behaviours: { type: 'array', items: { type: 'string' }, description: 'one short infrastructure-level line per behaviour tested (no experiment content)' }, count: { type: 'integer' }, needs_gpu: { type: 'boolean' } } }
const r = await agent(`You write the acceptance tests of one measurement run from its specification, never from its implementation. You have not seen and must not look for the runner or the on-box script; you read only: the directive ${A.directive}, the execution contract ${A.contract || '(none given)'}, the design record ${A.design_record || '(none given)'}, the question ${A.question || '(none given)'}.

Write exactly one file, ${A.out_file}, a standalone Python 3.10 program using only the standard library plus whatever the directive says is installed in the shipped environment. It is run ON THE BOX, inside the shipped environment, before the physics, from the run directory, as: python3 ${A.out_file.split('/').pop()} --results ${A.results_dir_on_box || 'results_' + A.tag + '/out'}. It must:
1. Check the environment the directive requires: every import the directive names, the engine's capability or platform query exactly as the directive specifies it, the presence and versions the directive pins; each as one test.
2. Check the records contract: for each record file the directive says the run writes (endpoint records, the anchor record, RUN_VALID.json, the summary, the guard record), that a planted minimal example conforms: write a tiny valid record through the record writer the contract names if it is importable, else check the schema the directive states (fields, decision values, run_valid presence, units).
3. Check the guard arithmetic and the void propagation the directive states, with planted inputs that must stop and must go, and a planted anchor miss that must void later records.
4. Check the directive's own consistency: numbers that appear in two items must agree.
Each test prints one line "TEST <name>: PASS" or "TEST <name>: FAIL <one-line reason>" and the program ends with "TESTS: <passed> of <total> passed" and exactly "TESTS: PASS" or "TESTS: FAIL" on the last line, exit code 1 on FAIL, under 300 s, no network. Tests must be able to fail: never write a test that cannot fail. Do not read, import or reference the runner; the tests are black-box. Write nothing else anywhere.`,
  { label: 'tests-author', agentType: 'triage-author', model: 'opus', schema: SCHEMA })
if (!r) return { failed: true, stage: 'tests-author' }
log(`tests author: ${r.count} test(s), needs_gpu=${r.needs_gpu}`)
return { tests: r, tag: A.tag }
