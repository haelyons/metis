#!/usr/bin/env node
'use strict'
// Start a run of one experiment. Copies this pipeline into experiments/<name>/<stamp>-<kind>/pipeline (files read-only),
// writes RUN.md (command, source commit), then runs the copy with every output under <run>/out and the console in
// <run>/console.log. The copy is what ran; edit pipeline/ freely afterwards.
//
// usage: node pipeline/launch.js <experiment> loop             (needs experiments/<experiment>/seed.json)
//        node pipeline/launch.js <experiment> card             (one card for the seed, no frame check or neighbours)
//        node pipeline/launch.js <experiment> frame --card-file <card.md> --root "<question>"
//        add --dry-run to prepare the run folder and print the command without running it
const fs = require('node:fs')
const path = require('node:path')
const { spawn, execFileSync } = require('node:child_process')

const PIPE = __dirname
const REPO = path.dirname(PIPE)
const [name, kind, ...rest] = process.argv.slice(2)
const dry = rest.includes('--dry-run')
const extra = rest.filter(a => a !== '--dry-run')
const EXP = path.join(REPO, 'experiments', name || '')
if (!name || !['loop', 'card', 'frame'].includes(kind) || !fs.existsSync(EXP)) {
  console.error('usage: node pipeline/launch.js <experiment> <loop|card|frame> [args] [--dry-run]; the experiment folder must exist')
  process.exit(2)
}
const stamp = new Date().toISOString().replace(/[-:]/g, '').replace(/\..*/, '').replace('T', '-').slice(0, 13)
const RUN = path.join(EXP, `${stamp}-${kind}`)
const COPY = path.join(RUN, 'pipeline')
fs.mkdirSync(path.join(RUN, 'out'), { recursive: true })

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
if (kind === 'loop') cmd = node('loop.js', ['--seed', path.join(EXP, 'seed.json'), '--name', name, '--dir', path.join(RUN, 'out')])
if (kind === 'frame') cmd = node('frame.js', [...extra, '--out', path.join(RUN, 'out')])
if (kind === 'card') {
  const cfg = JSON.parse(fs.readFileSync(path.join(COPY, 'idea', 'config.json'), 'utf8'))
  const F = JSON.parse(fs.readFileSync(cfg.roots_args, 'utf8'))
  const seed = JSON.parse(fs.readFileSync(path.join(EXP, 'seed.json'), 'utf8'))
  const args = { ...Object.fromEntries(Object.entries(F).filter(([k]) => !['fixed_roots', 'base'].includes(k))), base: 'auto', fixed_roots: [], seed_ideas: [seed] }
  fs.writeFileSync(path.join(RUN, 'args.json'), JSON.stringify(args, null, 1))
  cmd = node('wf.js', ['--args', path.join(RUN, 'args.json'), '--name', name, '--out', path.join(RUN, 'out')])
}
const commit = git(['rev-parse', '--short', 'HEAD']), dirty = git(['status', '--porcelain', '--', 'pipeline']) ? ' (pipeline/ had uncommitted changes)' : ''
fs.writeFileSync(path.join(RUN, 'RUN.md'), [`# ${name} · ${kind} · ${stamp}`, '',
  `Pipeline: copy of pipeline/ at commit ${commit}${dirty}, in ./pipeline (read-only).`,
  `Command: ${cmd[0]} ${cmd[1].map(a => (/\s/.test(a) ? JSON.stringify(a) : a)).join(' ')}`,
  `Outputs: ./out · console: ./console.log`, ''].join('\n'))
console.log(`run folder: ${RUN}\n${fs.readFileSync(path.join(RUN, 'RUN.md'), 'utf8')}`)
if (dry) process.exit(0)

const log = fs.createWriteStream(path.join(RUN, 'console.log'))
const child = spawn(cmd[0], cmd[1], { stdio: ['ignore', 'pipe', 'pipe'] })
for (const s of [child.stdout, child.stderr]) s.on('data', d => { process.stdout.write(d); log.write(d) })
child.on('close', code => { log.end(`\n[exit ${code}]\n`); process.exitCode = code })
