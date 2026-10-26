#!/usr/bin/env node
'use strict'

// Black-box contracts from m5/SCHEMAS.md. Never inspect profiler/pipeline source.
// Usage: node tools/test_m5_profile.js
const fs = require('node:fs')
const path = require('node:path')
const os = require('node:os')
const assert = require('node:assert/strict')
const { spawnSync } = require('node:child_process')
const ROOT = path.resolve(__dirname, '..')
const scratch = fs.mkdtempSync(path.join(os.tmpdir(), 'test_m5_profile_'))
const read = file => JSON.parse(fs.readFileSync(file, 'utf8'))
const write = (file, value) => fs.writeFileSync(file, JSON.stringify(value))
let checks = 0, failures = 0
function check(name, run) {
  checks++
  try { run(); console.log(`ok ${name}`) }
  catch (error) { failures++; console.log(`FAIL ${name}: ${error.stack}`) }
}
function near(actual, expected) {
  assert.ok(Number.isFinite(actual) && Math.abs(actual - expected) < 1e-8, `${actual} != ${expected}`)
}
function execute(command, args, options = {}) {
  const logDir = fs.mkdtempSync(path.join(scratch, 'process-'))
  const stdout = fs.openSync(path.join(logDir, 'stdout'), 'w')
  const stderr = fs.openSync(path.join(logDir, 'stderr'), 'w')
  let result
  try {
    result = spawnSync(command, args, { cwd: ROOT, timeout: 30000,
      env: { ...process.env, PYTHONDONTWRITEBYTECODE: '1', M5_RAIDS_LEDGER: path.join(scratch, 'ledger.jsonl') },
      ...options, stdio: ['ignore', stdout, stderr] })
  } finally { fs.closeSync(stdout); fs.closeSync(stderr) }
  result.stdout = fs.readFileSync(path.join(logDir, 'stdout'), 'utf8')
  result.stderr = fs.readFileSync(path.join(logDir, 'stderr'), 'utf8')
  assert.ifError(result.error)
  return result
}
function csv(directory, { unit = 'ns', total = 10, sums = [2, 1, 0.5, 1.5] } = {}) {
  const factor = { ns: 1e9, us: 1e6, 'µs': 1e6, ms: 1e3, s: 1 }[unit]
  const report = (name, rows) => fs.writeFileSync(path.join(directory, `stats_${name}.csv`),
    `Time (%),Total Time (${unit}),Instances,Name\n` + rows.map(([seconds, name]) => `50,${seconds * factor},1,"${name}"\n`).join(''))
  report('cuda_gpu_kern_sum', [[sums[0] / 4, 'kernel, one'], [sums[0] * 3 / 4, 'kernel two']])
  report('cuda_gpu_mem_time_sum', [[sums[1], '[CUDA memcpy Host-to-Device]'], [sums[2], '[CUDA memcpy Device-to-Host]']])
  report('cuda_api_sum', [[sums[3] / 2, 'cudaLaunchKernel'], [sums[3] / 2, 'cudaMemcpy']])
  write(path.join(directory, 'raw_wall_s.json'), { total_wall_s: total, start_monotonic_s: 100 })
  fs.writeFileSync(path.join(directory, 'gpu_util_raw.jsonl'),
    [{ t: 99, util: 100 }, { t: 100, util: 0 }, { t: 101, util: 50 }, { t: 100 + total + 1, util: 90 }]
      .map(row => JSON.stringify(row)).join('\n') + '\n')
}
function summarise(directory) {
  return execute('python3', [path.join(ROOT, 'm5/profile_summarise.py'), directory])
}
function summariserTests() {
  for (const unit of ['ns', 'us', 'µs', 'ms', 's']) check(`CSV ${unit}: sums, host remainder, telemetry clock`, () => {
    const dir = fs.mkdtempSync(path.join(scratch, 'csv-'))
    csv(dir, { unit })
    const result = summarise(dir)
    assert.equal(result.status, 0, result.stderr)
    assert.deepEqual(read(path.join(dir, 'stages.json')), [
      { stage: 'kernels', kind: 'compute', wall_s: 2, gpu_s: 2 },
      { stage: 'memcpy H2D', kind: 'transfer', wall_s: 1, gpu_s: 1 },
      { stage: 'memcpy D2H', kind: 'transfer', wall_s: 0.5, gpu_s: 0.5 },
      { stage: 'CUDA API host time', kind: 'other', wall_s: 1.5, gpu_s: null },
      { stage: 'other host time', kind: 'other', wall_s: 5, gpu_s: null },
    ])
    assert.deepEqual(read(path.join(dir, 'total_wall_s.json')), { total_wall_s: 10 })
    assert.deepEqual(read(path.join(dir, 'gpu_util.json')), [{ t: 0, util: 0 }, { t: 1, util: 50 }])
    const before = fs.readFileSync(path.join(dir, 'stages.json'))
    assert.equal(summarise(dir).status, 0)
    assert.deepEqual(fs.readFileSync(path.join(dir, 'stages.json')), before)
  })
  check('overlapping sums scale wall allocations, preserve GPU seconds, invent no timestamps', () => {
    const dir = fs.mkdtempSync(path.join(scratch, 'overlap-'))
    csv(dir, { total: 2 })
    assert.equal(summarise(dir).status, 0)
    const stages = read(path.join(dir, 'stages.json'))
    ;[0.8, 0.4, 0.2, 0.6, 0].forEach((seconds, i) => near(stages[i].wall_s, seconds))
    assert.deepEqual(stages.map(row => row.gpu_s), [2, 1, 0.5, null, null])
    assert.ok(stages.every(row => !Object.hasOwn(row, 'start_s')))
    near(stages.reduce((sum, row) => sum + row.wall_s, 0), 2)
  })
  check('known Nsight absent-activity skips count as zero', () => {
    const dir = fs.mkdtempSync(path.join(scratch, 'skips-'))
    csv(dir)
    for (const [report, activity] of [
      ['cuda_gpu_kern_sum', 'CUDA kernel'], ['cuda_gpu_mem_time_sum', 'CUDA memory'], ['cuda_api_sum', 'CUDA API'],
    ]) fs.writeFileSync(path.join(dir, `stats_${report}.csv`),
      `SKIPPED: fixture.nsys-rep does not contain ${activity} data.\n`)
    assert.equal(summarise(dir).status, 0)
    const stages = read(path.join(dir, 'stages.json'))
    assert.deepEqual(stages.map(row => row.wall_s), [0, 0, 0, 0, 10])
    assert.deepEqual(stages.map(row => row.gpu_s), [0, 0, 0, null, null])
  })
  for (const failure of ['missing', 'malformed']) check(`${failure} CSV fails parsing`, () => {
    const dir = fs.mkdtempSync(path.join(scratch, 'invalid-'))
    csv(dir)
    const file = path.join(dir, 'stats_cuda_api_sum.csv')
    if (failure === 'missing') fs.unlinkSync(file)
    else fs.writeFileSync(file, 'not,a,report\n')
    assert.notEqual(summarise(dir).status, 0)
  })
}
function script(file, body) {
  fs.writeFileSync(file, '#!/bin/bash\nset -eu\n' + body + '\n', { mode: 0o700 })
}
function profilerTests() {
  for (const mode of ['success', 'collection-failure', 'export-failure', 'missing-nsys', 'deb-hash-mismatch', 'deb-success']) check(`profile_nsys.sh: ${mode}`, () => {
    const deb = mode.startsWith('deb-')
    const dir = fs.mkdtempSync(path.join(scratch, 'collect-')), bin = path.join(dir, 'bin')
    fs.mkdirSync(bin)
    fs.mkdirSync(path.join(dir, 'profiler'))
    for (const file of ['profile_nsys.sh', 'profile_summarise.py'])
      fs.copyFileSync(path.join(ROOT, 'm5', file), path.join(dir, 'profiler', file))
    write(path.join(dir, 'profiler/probe.json'), { nvcc: [], nvidia: { gpus: ['Fixture GPU'] }, apt_sources: [] })
    if (deb) {
      const source = path.join(dir, 'nvidia.list')
      const lines = ['deb https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2204/x86_64/ /']
      fs.writeFileSync(source, lines.join('\n') + '\n')
      write(path.join(dir, 'profiler/probe.json'), {
        nvcc: [], nvidia: { gpus: ['Fixture GPU'] }, apt_sources: [{ file: source, lines }], sudo_nopasswd: true,
      })
    }
    // Restricted PATH: installation/network tools cannot reach host tools.
    for (const tool of ['bash', 'python3', 'mkdir', 'rm', 'date', 'sleep', 'cat', 'dirname', 'head', 'tail', 'grep', 'awk', 'sed', 'uname', 'mktemp', 'readlink', 'find', 'sort', 'tr', 'cut', 'timeout', 'tee', 'ls']) {
      const located = execute('/bin/bash', ['-c', 'command -v "$1"', 'locate', tool])
      if (located.status === 0) fs.symlinkSync(located.stdout.trim(), path.join(bin, tool))
    }
    for (const tool of ['sudo', 'apt', 'apt-get', 'apt-cache', 'curl', 'wget', 'sha256sum', 'dpkg', 'dpkg-query'])
      script(path.join(bin, tool), 'printf "%s\\n" "$0 $*" >> "$FAKE_CALLS"\nexit 1')
    if (deb) {
      // Route Python download/hash APIs through the same PATH fakes. No real
      // package can have the official pinned digest, so verification is simulated.
      fs.writeFileSync(path.join(dir, 'sitecustomize.py'), `import hashlib, io, os, re, subprocess, urllib.request
real_sha256 = hashlib.sha256
def download(url, *args, **kwargs):
    target = os.path.join(os.environ['HOME'], 'download.deb')
    subprocess.run(['curl', '-o', target, url], check=True)
    with open(target, 'rb') as stream:
        return io.BytesIO(stream.read())
class Digest(str):
    def __eq__(self, expected):
        assert re.fullmatch(r'[a-fA-F0-9]{64}', expected)
        with open(os.environ['FAKE_CALLS'], 'a') as stream:
            stream.write('checksum ' + expected + '\\n')
        return self.valid
    def __ne__(self, expected):
        return not self == expected
class Hash:
    def hexdigest(self):
        result = subprocess.run(['sha256sum'], input=b'fixture deb\\n', capture_output=True)
        digest = Digest('0' * 64)
        digest.valid = result.returncode == 0
        return digest
def sha256(data=b'', *args, **kwargs):
    return Hash() if data == b'fixture deb\\n' else real_sha256(data, *args, **kwargs)
urllib.request.urlopen = download
hashlib.sha256 = sha256
`)
      script(path.join(bin, 'id'), 'echo 1000')
      script(path.join(bin, 'sudo'), `printf 'sudo %s\\n' "$*" >> "$FAKE_CALLS"
test "$1" = -n
shift
"$@"`)
      script(path.join(bin, 'apt-cache'), `printf 'apt-cache %s\\n' "$*" >> "$FAKE_CALLS"
echo 'nsight-systems-cli - fixture package'`)
      script(path.join(bin, 'apt-get'), `printf 'apt-get %s\\n' "$*" >> "$FAKE_CALLS"
[[ " $* " == *" -f "* ]]`)
      script(path.join(bin, 'curl'), `printf 'curl %s\\n' "$*" >> "$FAKE_CALLS"
output=
while (( $# )); do
  case "$1" in
    -o|--output) output=$2; shift 2;;
    https://*) test "$1" = 'https://developer.download.nvidia.com/devtools/repos/ubuntu2204/amd64/NsightSystems-linux-cli-public-2025.3.1.90-3582212.deb'; shift;;
    *) shift;;
  esac
done
test -n "$output"
printf 'fixture deb\\n' > "$output"`)
      script(path.join(bin, 'sha256sum'), `printf 'sha256sum %s\\n' "$*" >> "$FAKE_CALLS"
if (( $# == 0 )); then
  test "$(cat)" = 'fixture deb'
  ${mode === 'deb-hash-mismatch' ? 'exit 1' : ': > "$HOME/verified"'}
  printf '%064d  -\\n' 0
  exit 0
fi
[[ " $* " == *" -c "* || " $* " == *" --check "* ]]
IFS= read -r checksum
printf 'checksum %s\\n' "$checksum" >> "$FAKE_CALLS"
[[ "$checksum" =~ ^[[:xdigit:]]{64}[[:space:]]+ ]]
package=\${checksum#*  }
test "$(cat "$package")" = 'fixture deb'
${mode === 'deb-hash-mismatch' ? 'exit 1' : ': > "$HOME/verified"'}`)
      script(path.join(bin, 'dpkg'), `printf 'dpkg %s\\n' "$*" >> "$FAKE_CALLS"
test "$1" = -i
test -f "$HOME/verified"
test "$(cat "$2")" = 'fixture deb'
python3 -c 'import os, shutil; shutil.copy(os.environ["HOME"] + "/nsys-fixture", os.environ["PATH"] + "/nsys")'`)
    }
    script(path.join(bin, 'nvidia-smi'), 'printf "20\\n40\\n"')
    if (mode !== 'missing-nsys') script(deb ? path.join(dir, 'nsys-fixture') : path.join(bin, 'nsys'), `
printf '%s\\n' "$*" >> "$FAKE_CALLS"
case "$1" in
  --version) echo 'NVIDIA Nsight Systems version fixture';;
  profile)
    ${mode === 'collection-failure' ? 'exit 9' : ''}
    sleep 0.3
    shift
    while [[ $1 == -* ]]; do
      case "$1" in --output=*) output=\${1#*=}; shift;; *) shift;; esac
    done
    : > "$output.nsys-rep"
    "$@"
    sleep 0.3;;
  stats)
    sleep 0.3
    ${mode === 'export-failure' ? 'exit 9' : `while (( $# )); do
      if [[ $1 == --output ]]; then output=$2; shift 2; else shift; fi
    done
    for report in cuda_gpu_kern_sum cuda_gpu_mem_time_sum cuda_api_sum; do
      printf 'Time (%%),Total Time (ns),Instances,Name\\n100,1000000,1,' > "\${output}_\${report}.csv"
      case "$report" in
        cuda_gpu_kern_sum) echo kernel;;
        cuda_gpu_mem_time_sum) echo '[CUDA memcpy Host-to-Device]';;
        cuda_api_sum) echo cudaLaunchKernel;;
      esac >> "\${output}_\${report}.csv"
    done`}
    ;;
  *) exit 8;;
esac`)
    script(path.join(dir, 'run_command.sh'), `test "$FIXTURE_ENV" = preserved\nprintf 'baseline sentinel\\n'\nprintf 'executed\\n' >> command-calls\nsleep 0.3`)
    const out = path.join(dir, 'out')
    fs.mkdirSync(out)
    write(path.join(out, 'stages.json'), [{ stage: 'stale' }])
    const env = { PATH: bin, HOME: dir, TMPDIR: dir, FIXTURE_ENV: 'preserved', FAKE_CALLS: path.join(dir, 'calls'),
      ...(deb ? { PYTHONPATH: dir, PYTHONDONTWRITEBYTECODE: '1' } : {}),
      M5_RAIDS_LEDGER: path.join(scratch, 'ledger.jsonl') }
    const started = process.hrtime.bigint()
    const result = execute('/bin/bash', [path.join(dir, 'profiler/profile_nsys.sh'), 'run_command.sh', out, '10'], { cwd: dir, env })
    if (deb) {
      assert.ok(fs.existsSync(env.FAKE_CALLS), result.stderr + result.stdout)
      const calls = fs.readFileSync(env.FAKE_CALLS, 'utf8')
      assert.match(calls, /apt-get .*nsight-systems-cli/)
      assert.ok(calls.indexOf('apt-get ') < calls.indexOf('curl '), calls + result.stderr + result.stdout)
      assert.match(calls, /curl .*https:\/\/developer\.download\.nvidia\.com\/devtools\/repos\/ubuntu2204\/amd64\/NsightSystems-linux-cli-public-2025\.3\.1\.90-3582212\.deb/)
      assert.match(calls, /checksum [a-fA-F0-9]{64}\s+/)
      if (mode === 'deb-hash-mismatch') {
        assert.doesNotMatch(calls, /(?:sudo -n )?dpkg /)
        assert.ok(!fs.existsSync(path.join(bin, 'nsys')))
      } else {
        assert.match(calls, /sudo -n dpkg -i /)
        assert.match(calls, /sudo -n apt-get -f install -y/)
        assert.ok(calls.indexOf('sha256sum ') < calls.indexOf('dpkg -i '), calls)
        assert.ok(calls.indexOf('dpkg -i ') < calls.indexOf('profile --trace='), calls)
      }
    }
    if (mode === 'success' || mode === 'deb-success') {
      assert.equal(result.status, 0, result.stderr + result.stdout)
      const calls = fs.readFileSync(env.FAKE_CALLS, 'utf8')
      assert.match(calls, /profile --trace=cuda,nvtx,osrt --sample=none/)
      assert.match(calls, /stats --report cuda_gpu_kern_sum,cuda_gpu_mem_time_sum,cuda_api_sum --format csv/)
      assert.equal(fs.readFileSync(path.join(dir, 'command-calls'), 'utf8'), 'executed\n')
      assert.match(fs.readFileSync(path.join(out, 'baseline.log'), 'utf8'), /baseline sentinel/)
      assert.ok(fs.existsSync(path.join(out, 'baseline.nsys-rep')))
      const wall = read(path.join(out, 'total_wall_s.json')).total_wall_s
      const elapsed = Number(process.hrtime.bigint() - started) / 1e9
      assert.ok(wall >= 0.3 && wall < elapsed - 0.8, `collection/export overhead included: wall=${wall}, elapsed=${elapsed}`)
      const stages = read(path.join(out, 'stages.json'))
      near(stages.reduce((sum, row) => sum + row.wall_s, 0), wall)
      assert.equal(stages.length, 5)
      const telemetry = read(path.join(out, 'gpu_util.json'))
      assert.ok(telemetry.length > 0, 'missing telemetry')
      assert.ok(telemetry.every(row => row.t >= 0 && row.t <= wall && row.util === 30))
    } else {
      assert.equal(result.status, 2, result.stderr + result.stdout)
      assert.match(result.stderr + result.stdout, /M5_PROFILER_INFRA/)
      assert.equal(typeof read(path.join(out, 'infra.json')), 'object')
      assert.ok(!fs.existsSync(path.join(out, 'stages.json')), 'stale profile survived')
      if (mode === 'missing-nsys' || mode === 'deb-hash-mismatch') assert.ok(!fs.existsSync(path.join(dir, 'command-calls')))
    }
  })
}
try {
  summariserTests()
  profilerTests()
  check('pipeline coverage/gate and shared command contracts; no profile agent or repair', () => {
    const result = execute(process.execPath, [path.join(__dirname, 'test_m5_reproduce.js'), '--profile-only'], { timeout: 240000 })
    assert.equal(result.status, 0, result.stdout + result.stderr)
    assert.match(result.stdout, /low-coverage/)
    assert.match(result.stdout, /empty-gpu-util/)
    assert.match(result.stdout, /fixed profiler uses shared command without profile agent/)
  })
} finally { fs.rmSync(scratch, { recursive: true, force: true }) }
console.log(`${checks} checks, ${failures} failures`)
if (!failures) console.log('all checks passed')
process.exitCode = failures ? 1 : 0
