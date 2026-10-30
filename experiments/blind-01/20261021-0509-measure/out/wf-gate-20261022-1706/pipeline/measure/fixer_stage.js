export const meta = { name: 'box-fixer', description: 'Bounded fixer on a held-open box: environment and glue only, every change a git commit on the box; then a claim-blind verifier reads the change log', phases: [{ title: 'Fix' }, { title: 'Verify' }] }
// args: { box_helper (path of box.sh: `box.sh <command>` runs it on the box over ssh), hold_dir (remote dir with HOLD/RESUME),
//         env_dir (remote environment directory, a git repo), failure_summary (short text: which stage failed and the log paths),
//         scope (what the fixer may touch), max_attempts, time_budget_min, tag }
const A = (typeof args === 'string' ? JSON.parse(args) : args) || {}
if (!A.box_helper || !A.hold_dir || !A.env_dir) return { error: 'fixer needs box_helper, hold_dir, env_dir' }
phase('Fix')
const FIX_SCHEMA = { type: 'object', additionalProperties: false, required: ['outcome', 'attempts', 'changes', 'commands_run', 'reason_kind'],
  properties: { outcome: { type: 'string', enum: ['fixed', 'gave_up', 'out_of_scope'] }, attempts: { type: 'integer' },
    changes: { type: 'array', items: { type: 'object', additionalProperties: false, required: ['file', 'what', 'commit'], properties: { file: { type: 'string' }, what: { type: 'string' }, commit: { type: 'string' } } } },
    commands_run: { type: 'integer' }, reason_kind: { type: 'string', description: 'one short infrastructure phrase: which kind of failure and which kind of fix' } } }
const fix = await agent(`You are the fixer for one held-open GPU box. A stage of an environment build failed and the box is waiting for you. You work ONLY through the helper \`${A.box_helper} <command>\` (it runs the command on the box over ssh and prints its output; use it with the Bash tool); you never run anything else locally and never read local files other than this helper's output.

Failure summary: ${A.failure_summary || 'see the logs on the box'}
On the box: the hold directory is ${A.hold_dir} (it contains HOLD; the logs are under ${A.hold_dir}/results_env/out/: install_pip.log, apt.log, import_check.json, env_report.json). The environment directory is ${A.env_dir}: a git repository holding pins.txt, apt.txt and venv/. The build script re-runs when you create the file ${A.hold_dir}/RESUME; it writes HOLD again if the retry fails. Create ${A.hold_dir}/ABANDON to stop.

Scope (binding): ${A.scope || 'environment and glue only: pins.txt (versions, extras, a different distribution of the same package, a build dependency), apt.txt (system libraries and build tools), environment variables of the install. Never the measurement protocol, never record fields, never files outside the environment directory and the hold directory.'}
Bounds: at most ${A.max_attempts || 3} retries, about ${A.time_budget_min || 30} minutes. Every change to pins.txt or apt.txt is one git commit in ${A.env_dir} with a one-line message saying what and why (git -C ${A.env_dir} add -A && git -C ${A.env_dir} commit -m "..."). Read the logs first; change the smallest thing that explains the failure; then touch RESUME and poll ${A.hold_dir}/HOLD every 30 to 60 seconds (its absence while the build runs, its reappearance on a new failure, or the build's exit which the launcher records). If a fix needs anything outside scope, do not do it: report outcome out_of_scope. Do not install anything on the box outside the environment directory except apt packages listed in apt.txt.`,
  { label: 'fixer', agentType: 'ls-fixer', model: 'opus', schema: FIX_SCHEMA })
if (!fix) return { failed: true, stage: 'fixer' }
log(`fixer: ${fix.outcome} after ${fix.attempts} retry(ies), ${fix.changes.length} change(s)`)
phase('Verify')
const VER_SCHEMA = { type: 'object', additionalProperties: false, required: ['within_scope', 'findings', 'files_changed'],
  properties: { within_scope: { type: 'boolean' }, files_changed: { type: 'array', items: { type: 'string' } }, findings: { type: 'array', items: { type: 'string' } } } }
const ver = await agent(`You verify a fixer's changes on a held-open box against its scope, reading only. Use \`${A.box_helper} <command>\` with the Bash tool to run, on the box: git -C ${A.env_dir} log --stat --oneline; git -C ${A.env_dir} log -p -- pins.txt apt.txt; ls -la ${A.hold_dir}; cat ${A.hold_dir}/results_env/out/env_report.json. Scope the fixer had: ${A.scope || 'environment and glue only (pins.txt, apt.txt, install environment variables); never the measurement protocol, record fields, or files outside the environment and hold directories'}. The fixer reported: ${JSON.stringify(fix)}.
Decide within_scope (every changed file and every change inside the scope), list the files changed, and findings: anything outside scope, any change that alters what will be measured, any change the fixer did not report. Do not fix anything.`,
  { label: 'verifier', agentType: 'ls-fixer', model: 'sonnet', schema: VER_SCHEMA })
return { fix, verify: ver, tag: A.tag || null }
