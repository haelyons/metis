#!/usr/bin/env node
'use strict'
// Start a run of one experiment. Copies this pipeline into experiments/<name>/<stamp>-<kind>/pipeline (files read-only),
// writes RUN.md (command, source commit), then runs the copy with every output under <run>/out and the console in
// <run>/console.log. The copy is what ran; edit dut/pipeline/ freely afterwards.
//
// usage: node dut/pipeline/launch.js <experiment> loop             (needs experiments/<experiment>/seed.json)
//        node dut/pipeline/launch.js <experiment> card [--main <model>]  (one card for the seed; --main swaps the producer's model)
//        node dut/pipeline/launch.js <experiment> frame --card-file <card.md> --root "<question>"
//        node dut/pipeline/launch.js <experiment> tree --seed <args.json>  (the full tree; args.json overrides run F's args,
//                                                                          e.g. {"fixed_roots": ["..."], "picks_per_branch": 1})
//        node dut/pipeline/launch.js <experiment> measure --card <card run dir | its out dir | result.json> [--pick <key>]
//        node dut/pipeline/launch.js <experiment> stage --measure <measure dir> --stage design|build|post|gate|review [--family opencode|claude]
//                                                                  [--mode fallback|shadow|swap|primary-only] [--on-refusal halt|understudy]
//                                                                  (one latent_skeptic stage on wf.js with understudies; run under <measure dir>/out/)
//                                                                 (compiles a card's calibration record into a latent_skeptic
//                                                                  measure folder: QUESTION.md, SEALED_PREDICTIONS.md,
//                                                                  out/triage_args.json, CARD.json; runs nothing)
//        add --dry-run to prepare the run folder and print the command without running it;
//        add --seed <file> to run card or loop on another seed than the experiment's seed.json (a variant)
const fs = require('node:fs')
const path = require('node:path')
const { spawn, execFileSync } = require('node:child_process')

const PIPE = __dirname
const REPO = path.resolve(PIPE, '..', '..')
const [name, kind, ...rest] = process.argv.slice(2)
const dry = rest.includes('--dry-run')
const si = rest.indexOf('--seed'), seedFile = si >= 0 ? path.resolve(rest[si + 1]) : null
const extra = rest.filter((a, i) => a !== '--dry-run' && !(si >= 0 && (i === si || i === si + 1)))
const EXP = path.join(REPO, 'experiments', name || '')
if (!name || !['loop', 'card', 'frame', 'tree', 'measure', 'stage'].includes(kind) || !fs.existsSync(EXP)) {
  console.error('usage: node dut/pipeline/launch.js <experiment> <loop|card|frame|tree|measure|stage> [args] [--dry-run]; the experiment folder must exist')
  process.exit(2)
}
const stamp = new Date().toISOString().replace(/[-:]/g, '').replace(/\..*/, '').replace('T', '-').slice(0, 13)
// two launches in the same minute get -2, -3 ...
const mi = rest.indexOf('--measure'), MDIR = mi >= 0 ? path.resolve(rest[mi + 1]) : null
const sti = rest.indexOf('--stage'), STAGE = sti >= 0 ? rest[sti + 1] : null
if (kind === 'stage' && (!MDIR || !fs.existsSync(path.join(MDIR, 'pipeline.js')) || !['design', 'build', 'post', 'gate', 'review'].includes(STAGE))) {
  console.error('stage needs --measure <measure dir with pipeline.js> and --stage design|build|post|gate|review'); process.exit(2)
}
let RUN = kind === 'stage' ? path.join(MDIR, 'out', `wf-${STAGE}-${stamp}`) : path.join(EXP, `${stamp}-${kind}`)
for (let i = 2; fs.existsSync(RUN); i++) RUN = kind === 'stage' ? path.join(MDIR, 'out', `wf-${STAGE}-${stamp}-${i}`) : path.join(EXP, `${stamp}-${kind}-${i}`)
const COPY = path.join(RUN, 'pipeline')
fs.mkdirSync(path.join(RUN, 'out'), { recursive: true })

// ---------- measure: compile a card's calibration record into a latent_skeptic measure folder (2026-10-21) ----------
// No model call, no one reads the card: the record main.js returns carries the inputs, their measuring phase, the
// anchor and the predictions. The folder is what the m1-m3 runs had by hand before their first agent.
if (kind === 'measure') {
  const crypto = require('node:crypto')
  const sha256 = b => crypto.createHash('sha256').update(b).digest('hex')
  const ci = rest.indexOf('--card'), cardArg = ci >= 0 ? path.resolve(rest[ci + 1]) : null
  if (!cardArg) { console.error('measure needs --card <card run dir | its out dir | result.json>'); process.exit(2) }
  const resPath = [cardArg, path.join(cardArg, 'result.json'), path.join(cardArg, 'out', 'result.json'), path.join(cardArg, 'out', 'r0', 'card', 'result.json')].find(p => fs.existsSync(p) && fs.statSync(p).isFile())
  if (!resPath) { console.error(`measure: no result.json under ${cardArg}`); process.exit(2) }
  const res = JSON.parse(fs.readFileSync(resPath, 'utf8'))
  const pi = rest.indexOf('--pick'), want = pi >= 0 ? rest[pi + 1] : null
  const recs = res.calibration || []
  const rec = want ? recs.find(r => r.key === want) : recs.find(r => r.state === 'calibration_required')
  if (!rec) { console.error(`measure: no calibration_required record in ${resPath} (${recs.length ? recs.map(r => `${r.key}: ${r.state}`).join('; ') : 'no calibration records: the card predates them; re-run the card'})`); process.exit(2) }
  const sha = sha256(fs.readFileSync(resPath))
  const band = u => (u.basis === 'PROXY' ? 2.5 : 3)   // refuted outside [value/k, value*k]; ledger 2026-10-20: three proxies off by 20x or more
  const fmt = v => (typeof v === 'number' ? (Number.isInteger(v) ? String(v) : Number(v.toPrecision(4)).toString()) : String(v))
  const lo = u => fmt(u.value / band(u)), hi = u => fmt(u.value * band(u))
  const gateText = u => (u.phase && u.phase.gate ? `the card's gate ${u.phase.gate.on} ${u.phase.gate.op} ${u.phase.gate.value} is then applied to the measured value, else "${u.phase.gate.else}"` : 'the card names no gate on it')
  const CONFOUNDS = ['decidability by construction: is any endpoint outcome forced, unable to occur, or deciding a different question than the seed asks', 'coordinates and scale: could the chosen layers, strengths, or units make every cell degenerate or null regardless of the hypothesis']
  const claims = rec.required.map((u, i) => ({
    id: `C${i + 1}`,
    text: `If run exactly as specified, this design decides: the card's ${u.basis} value for ${u.id} (${fmt(u.value)}) holds on the card's own protocol, measured in its phase ${u.measured_by || '(none named)'}${u.phase ? ` (${u.phase.what})` : ''} on one rented box. Endpoints: E${i + 1} ${u.id} read from the run's own log line; refuted when the measured value lies outside [${lo(u)}, ${hi(u)}]; ${gateText(u)}.`,
    evidence: JSON.stringify({ basis: u.basis, value: u.value, differs_in: u.differs_in, measured_by: u.measured_by, cum_spend_through_measured_by: u.cum_spend_through_measured_by, k_budget: u.k_budget, phase: u.phase, line: u.line, anchor: rec.anchor, predictions: rec.predictions }),
    confounds: CONFOUNDS,
  }))
  const instruments = rec.required.map((u, i) => ({ id: `endpoint-${i + 1}-readout`, version: 'v1', asserts: `E${i + 1}: ${u.id} is read from the run's own output line of phase ${u.measured_by || '?'}, with its unit, and the box, engine and configuration are recorded beside it`, validation_artifact: null }))
  fs.writeFileSync(path.join(RUN, 'out', 'triage_args.json'), JSON.stringify({ claims, instruments }, null, 1))
  fs.writeFileSync(path.join(RUN, 'CARD.json'), JSON.stringify({ source: path.relative(REPO, resPath), result_json_sha256: sha, record: rec }, null, 1))
  const a = rec.anchor
  const Q = [`# QUESTION: do the card's unmeasured load-bearing inputs hold on its own protocol?`, '',
    `Compiled by launch.js measure from \`${path.relative(REPO, resPath)}\` (sha256 ${sha}); no one read the card to write this. Card ${rec.key}: "${rec.title}"; plan USD ${rec.plan_usd ?? '?'}; calibration state ${rec.state}.`, '',
    '## The question', '', `For each load-bearing input the card's cost rests on, measure it on the card's own protocol on one rented box, within the owner's calibration cap, and read the result against the card's own gate. The card's planned run is not executed.`, '',
    '## Committed data', '', `- \`${path.relative(REPO, resPath)}\`: sha256 ${sha}; its calibration record is copied to \`CARD.json\`.`,
    ...rec.required.map((u, i) => `- Input ${i + 1}: ${u.id}, basis ${u.basis}, value ${fmt(u.value)}, measured in phase ${u.measured_by || '(none named)'}${u.line ? ` (line ${u.line.id}: ${u.line.hours} h, USD ${fmt(u.line.usd)})` : ''}; spend through that phase USD ${fmt(u.cum_spend_through_measured_by ?? '?')}; the budget is reached at ${u.k_budget ? fmt(u.k_budget) + 'x' : '?'}${u.differs_in && u.differs_in.length ? `; differs from its source in: ${u.differs_in.join(', ')}` : ''}.`), '',
    '## Anchor', '', a ? `${a.what} Published value ${fmt(a.published_value ?? '?')}, tolerance ${a.tolerance || 'as stated'}${a.source_id ? ` [${a.source_id}]` : ''}. The run reproduces it first; a miss stops the run before the inputs are measured.` : 'The card names no anchor: the run has none, declared below as a construct risk.', '',
    '## What would refute each claim', '', ...rec.required.map((u, i) => `- C${i + 1}: measured ${u.id} outside [${lo(u)}, ${hi(u)}] (${u.basis}: band ${band(u)}x either side). ${gateText(u)}.`), '',
    '## Scope', '', `One rented box; the measuring phase's protocol as the card states it${rec.required.some(u => u.phase) ? ': ' + [...new Set(rec.required.filter(u => u.phase).map(u => u.phase.what))].join('; ') : ''}. Cost cap: the lesser of the phase's own line and the owner's calibration cap (USD 10 without re-approval; above USD 20 needs approval before launch). No production phase runs.`, '',
    '## Declared construct risks', '', ...rec.required.filter(u => u.basis === 'PROXY').map(u => `- ${u.id} is a PROXY: its source setting differs in ${(u.differs_in || []).join(', ') || 'ways the card does not list'}.`), ...rec.required.filter(u => u.basis !== 'PROXY').map(u => `- ${u.id} is a ${u.basis}: no page states it; the card's value is the producer's estimate.`),
    `- The producer's own local pilots, if any, ran on a shared CPU host and are not GPU measurements.`, `- One sample on one box unless the phase repeats; run-to-run spread is not measured.`, ...(a ? [] : ['- No anchor: nothing checks the setup reproduces a published number before the inputs are read.']), '',
    '## How the card maps onto this record', '', `Card key ${rec.key}. ${rec.predictions ? `Predictions: if_lever "${rec.predictions.if_lever}"; if_not "${rec.predictions.if_not}"; noise rule "${rec.predictions.noise_rule}"; the producer expects ${rec.predictions.expected}.` : 'The record carries no predictions.'} This run resolves the inputs only; the card's own decision rule is not evaluated here.`, '']
  fs.writeFileSync(path.join(RUN, 'QUESTION.md'), Q.join('\n'))
  const S = [`# Sealed predictions, compiled before any agent or box`, '', `Rule: each input's card value is the prediction; p is the ledger's base rate for load-bearing GUESS and PROXY values holding within their band (2026-10-20: 0 of 3 held; p set to 0.30 to leave room for the small sample).`, '',
    ...rec.required.map((u, i) => `- P${i + 1}: measured ${u.id} within [${lo(u)}, ${hi(u)}]: p = 0.30`), '']
  fs.writeFileSync(path.join(RUN, 'SEALED_PREDICTIONS.md'), S.join('\n'))
  fs.writeFileSync(path.join(RUN, 'out', 'SEALS.txt'), `${sha256(S.join('\n'))}  SEALED_PREDICTIONS.md\n${sha}  ${path.relative(REPO, resPath)}\n`)
  const mgit = a2 => { try { return execFileSync('git', ['-C', REPO, ...a2], { encoding: 'utf8' }).trim() } catch { return '?' } }
  fs.writeFileSync(path.join(RUN, 'RUN.md'), [`# ${name} · measure · ${stamp}`, '', `Compiled by dut/pipeline/launch.js at commit ${mgit(['rev-parse', '--short', 'HEAD'])} from ${path.relative(REPO, resPath)} (sha256 ${sha}), card ${rec.key}, state ${rec.state}, ${rec.required.length} input(s) to measure.`, '',
    'Files: QUESTION.md (five duties), SEALED_PREDICTIONS.md (sha in out/SEALS.txt), out/triage_args.json (latent_skeptic design-mode claims and instruments), CARD.json (the record).', '',
    'Next, in order, as m1-m3 did (dut/latent_skeptic, Claude Workflow runtime): design (triage_workflow.js with out/triage_args.json) -> GATE_COMMIT.md -> EXEC_NOTE.md -> build mode -> frozen launcher -> post mode -> ledger row kind card_number_resolved. Nothing here has run yet.', ''].join('\n'))
  console.log(`measure folder: ${RUN}\n${fs.readFileSync(path.join(RUN, 'RUN.md'), 'utf8')}`)
  process.exit(0)
}

// the copy: everything but node_modules; OpenCode's plugin modules are linked, not copied
fs.cpSync(PIPE, COPY, { recursive: true, filter: s => !s.split(path.sep).includes('node_modules') && !/\.log$/.test(s) })
const mods = path.join(PIPE, 'idea', 'ocx', 'opencode', 'node_modules')
if (fs.existsSync(mods)) fs.symlinkSync(mods, path.join(COPY, 'idea', 'ocx', 'opencode', 'node_modules'))
const lock = d => { for (const e of fs.readdirSync(d, { withFileTypes: true })) {
  const p = path.join(d, e.name)
  if (e.isDirectory() && e.name !== 'ocx') lock(p)   // OpenCode may write in its config folder
  else if (e.isFile()) fs.chmodSync(p, 0o444)
} }
lock(COPY)

const git = a => { try { return execFileSync('git', ['-C', REPO, ...a], { encoding: 'utf8' }).trim() } catch { return '' } }
const node = (script, args) => ['node', [path.join(COPY, 'idea', script), ...args]]
let cmd
const SEED = seedFile || path.join(EXP, 'seed.json')
if (kind === 'loop') cmd = node('loop.js', ['--seed', SEED, '--name', name, '--dir', path.join(RUN, 'out')])
if (kind === 'frame') cmd = node('frame.js', [...extra, '--out', path.join(RUN, 'out')])
if (kind === 'stage') {
  // the stage's args file as measure.sh wrote it (design_args.json, build<N>_args.json, post<N>_args.json: the latest)
  const latest = re => fs.readdirSync(path.join(MDIR, 'out')).filter(f => re.test(f)).sort().pop()
  const argsFile = STAGE === 'design' ? 'design_args.json' : latest(new RegExp(`^${STAGE}\\d+_args\\.json$`))
  if (!argsFile || !fs.existsSync(path.join(MDIR, 'out', argsFile))) { console.error(`stage: no ${STAGE} args file under ${MDIR}/out (measure.sh writes it)`); process.exit(2) }
  const a = JSON.parse(fs.readFileSync(path.join(MDIR, 'out', argsFile), 'utf8'))
  const args = { ...a, cwd: MDIR, base: path.join(RUN, 'work') }   // file-writing roles work in the measure folder, as the Workflow runtime did
  fs.writeFileSync(path.join(RUN, 'args.json'), JSON.stringify(args, null, 1))
  const tag = fs.existsSync(path.join(MDIR, 'TAG')) ? fs.readFileSync(path.join(MDIR, 'TAG'), 'utf8').trim() : 'm'
  const flags = extra.filter((x, i, xs) => !['--measure', '--stage'].includes(x) && !['--measure', '--stage'].includes(xs[i - 1]))
  // gate and review are one instruction file each: measure/prompt_stage.js turns it into one agent() call (role ls-writer / ls-general)
  const script = ['gate', 'review'].includes(STAGE) ? path.join(PIPE, 'measure', 'prompt_stage.js') : path.join(MDIR, 'pipeline.js')
  cmd = node('wf.js', ['--script', script, '--args', path.join(RUN, 'args.json'), '--name', `${name}-${tag}-${STAGE}`, '--out', path.join(RUN, 'out'), '--profile', 'latent_skeptic', ...flags])
  // the stage's return value lands where measure.sh expects it, after the run
  const target = STAGE === 'design' ? 'design_record.json' : argsFile.replace('_args.json', '_return.json')
  process.on('exit', () => {
    const r = path.join(RUN, 'out', 'result.json')
    if (fs.existsSync(r)) { fs.copyFileSync(r, path.join(MDIR, 'out', target)); console.log(`stage ${STAGE}: return value copied to out/${target}`) }
  })
}
if (kind === 'card' || kind === 'tree') {
  const cfg = JSON.parse(fs.readFileSync(path.join(COPY, 'idea', 'config.json'), 'utf8'))
  const F = JSON.parse(fs.readFileSync(cfg.roots_args, 'utf8'))
  const seed = JSON.parse(fs.readFileSync(SEED, 'utf8'))
  const given = Object.fromEntries(Object.entries(F).filter(([k]) => !['fixed_roots', 'base'].includes(k)))
  const args = kind === 'card' ? { ...given, base: 'auto', fixed_roots: [], seed_ideas: [seed] } : { ...given, base: 'auto', ...seed }
  fs.writeFileSync(path.join(RUN, 'args.json'), JSON.stringify(args, null, 1))
  cmd = node('wf.js', ['--args', path.join(RUN, 'args.json'), '--name', name, '--out', path.join(RUN, 'out'), ...extra])   // extra: e.g. --main <model>
}
const commit = git(['rev-parse', '--short', 'HEAD']), dirty = git(['status', '--porcelain', '--', 'dut/pipeline']) ? ' (dut/pipeline/ had uncommitted changes)' : ''
fs.writeFileSync(path.join(RUN, 'RUN.md'), [`# ${name} · ${kind} · ${stamp}`, '',
  `Pipeline: copy of dut/pipeline/ at commit ${commit}${dirty}, in ./pipeline (read-only).`,
  `Command: ${cmd[0]} ${cmd[1].map(a => (/\s/.test(a) ? JSON.stringify(a) : a)).join(' ')}`,
  kind === 'stage' ? `Stage: ${STAGE} of ${path.relative(REPO, MDIR)} · args: ./args.json` : `Seed: ${path.relative(EXP, SEED)}`, `Outputs: ./out · console: ./console.log`, ''].join('\n'))
console.log(`run folder: ${RUN}\n${fs.readFileSync(path.join(RUN, 'RUN.md'), 'utf8')}`)
if (dry) process.exit(0)

const log = fs.createWriteStream(path.join(RUN, 'console.log'))
const child = spawn(cmd[0], cmd[1], { stdio: ['ignore', 'pipe', 'pipe'] })
for (const s of [child.stdout, child.stderr]) s.on('data', d => { process.stdout.write(d); log.write(d) })
child.on('close', code => { log.end(`\n[exit ${code}]\n`); process.exitCode = code })
