'use strict'
// A fresh mount/PID namespace for an agent with a private HOME and /tmp.
const fs = require('node:fs')
const path = require('node:path')
const os = require('node:os')
const { spawn } = require('node:child_process')

async function run(options) {
  const directory = fs.realpathSync(options.isolation.directory)
  const runtime = fs.mkdtempSync(path.join(directory, '.runtime-'))
  const home = path.join(runtime, 'home')
  fs.mkdirSync(home)
  if (options.isolation.box_access) {
    fs.mkdirSync(path.join(home, '.cache'))
    fs.symlinkSync(path.join(os.homedir(), '.cache/metis-serve'), path.join(home, '.cache/metis-serve'))
    fs.symlinkSync(path.join(os.homedir(), '.ssh'), path.join(home, '.ssh'))
  }
  // Copy credentials, never provider histories, session databases or resume state.
  for (const relative of ['.codex/auth.json', '.local/share/opencode/auth.json', '.claude/.credentials.json']) {
    const source = path.join(os.homedir(), relative), target = path.join(home, relative)
    if (fs.existsSync(source)) {
      fs.mkdirSync(path.dirname(target), { recursive: true })
      fs.copyFileSync(source, target)
    }
  }
  const args = ['--die-with-parent', '--new-session', '--unshare-pid', '--unshare-ipc', '--ro-bind', '/', '/',
    '--tmpfs', '/tmp', '--proc', '/proc', '--dev', '/dev']
  const hidden = [...(options.isolation.hidden || []), `/run/user/${process.getuid()}`,
    ...['.codex', '.claude', '.cursor', '.cache', '.local/share/opencode', '.local/state/opencode']
      .map(name => path.join(os.homedir(), name))]
  if (!options.isolation.box_access) hidden.push(path.join(os.homedir(), '.ssh'))
  for (const file of [...new Set(hidden)].sort((a, b) => a.length - b.length)) {
    // /tmp is already private; exposing directory below is the only exception.
    if (!file.startsWith('/tmp/') && fs.existsSync(file)) args.push('--tmpfs', file)
  }
  const code = path.dirname(__dirname)
  if (hidden.some(file => code.startsWith(file + path.sep))) args.push('--ro-bind', code, code)
  const writer = /(?:^|,)\s*(?:Write|Edit|Bash)(?:\([^)]*\))?\s*(?:,|$)/.test(options.tools || '')
  args.push(writer ? '--bind' : '--ro-bind', directory, directory)
  if (!writer) args.push('--bind', runtime, runtime)
  if (options.isolation.box_access) {
    const cache = path.join(os.homedir(), '.cache/metis-serve')
    if (fs.existsSync(cache)) args.push('--ro-bind', cache, cache)
  }
  args.push('--chdir', directory, '--', process.execPath, __filename, '--worker')
  const worker = { ...options, isolation: undefined, isolated: true, cwd: directory, session: null, addDirs: [directory],
    rawPath: path.join(runtime, 'events'), httpLogDir: path.join(runtime, 'http'),
    env: { ...options.env, HOME: home, CODEX_HOME: path.join(home, '.codex'), CODEX_EPHEMERAL: '1', SSH_AUTH_SOCK: '',
      XDG_DATA_HOME: path.join(home, '.local/share'), XDG_STATE_HOME: path.join(home, '.local/state'),
      XDG_CACHE_HOME: path.join(home, '.cache'), TMPDIR: runtime } }
  const started = Date.now()
  try {
    return await new Promise(resolve => {
      const child = spawn('bwrap', args, { cwd: directory, stdio: ['pipe', 'pipe', 'pipe'] })
      let stdout = '', done = false
      const finish = result => {
        if (done) return
        done = true
        clearTimeout(timer)
        resolve(result || { text: '', json: null, tokens: { input: 0, output: 0, reasoning: 0 },
          tokens_known: false, cost: 0, tools: 0, ms: Date.now() - started,
          errors: ['runner error: isolation unavailable'], refusal: false })
      }
      const timer = setTimeout(() => { child.kill('SIGKILL'); finish() }, (options.timeoutMs || 1200000) + 30000)
      child.stdout.on('data', bytes => { stdout += bytes })
      child.stderr.resume()
      child.on('error', () => finish())
      child.on('close', code => {
        let result
        if (code === 0) { try { result = JSON.parse(stdout) } catch { /* fail closed */ } }
        finish(result)
      })
      child.stdin.on('error', () => {})
      child.stdin.end(JSON.stringify(worker))
    })
  } finally {
    if (options.rawPath && fs.existsSync(worker.rawPath)) fs.copyFileSync(worker.rawPath, options.rawPath)
    if (options.httpLogDir && fs.existsSync(worker.httpLogDir)) fs.cpSync(worker.httpLogDir, options.httpLogDir, { recursive: true })
    fs.rmSync(runtime, { recursive: true, force: true })
  }
}

module.exports = { run }
if (require.main === module && process.argv[2] === '--worker') {
  let input = ''
  process.stdin.on('data', bytes => { input += bytes })
  process.stdin.on('end', async () => {
    try { process.stdout.write(JSON.stringify(await require('./runner.js').run(JSON.parse(input)))) }
    catch { process.exitCode = 2 }
  })
}
