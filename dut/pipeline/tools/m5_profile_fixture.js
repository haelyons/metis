'use strict'

// Fixed-profiler transport fixture. Agent fixtures never write profiling outputs.
const fs = require('node:fs')
const path = require('node:path')
const assert = require('node:assert/strict')
const timings = [
  { stage: 'prepare', kind: 'compute', start_s: 0, wall_s: 3, gpu_s: null },
  { stage: 'transfer', kind: 'transfer', start_s: 3, wall_s: 5, gpu_s: 999 },
  { stage: 'finish', kind: 'other', start_s: 8, wall_s: 2, gpu_s: null },
]
// A stale calibration in the shared out/ that the pipeline must clear before probing.
const STALE_CONCURRENCY = { mps: true, mps_failed: false, single_wall_s: [1, 1, 1],
  batches: [{ n: 2, wall_s: 1, all_ok: true, skipped: false, factor: 2 },
    { n: 4, wall_s: 4 / 7.77, all_ok: true, skipped: false, factor: 7.77 }], factor: 7.77 }
// Valid probe outputs: T1 = median(1, 1.2, 1.1) = 1.1; factor_n = n * T1 / wall_n.
const VALID_CONCURRENCY = { mps: false, mps_failed: false, single_wall_s: [1, 1.2, 1.1],
  batches: [{ n: 2, wall_s: 1.375, all_ok: true, skipped: false, factor: 1.6 },
    { n: 4, wall_s: 2, all_ok: true, skipped: false, factor: 2.2 }], factor: 2.2 }
const NULL_CONCURRENCY = { mps: true, mps_failed: true, single_wall_s: [0.5, null, null],
  batches: [{ n: 2, wall_s: null, all_ok: false, skipped: false, factor: null },
    { n: 4, wall_s: null, all_ok: false, skipped: false, factor: null }], factor: null }
// Raw file contents written by the fake probe for each mode.
const PROBE_OUTPUTS = {
  valid: JSON.stringify(VALID_CONCURRENCY),
  'valid-null': JSON.stringify(NULL_CONCURRENCY),
  rc: JSON.stringify(VALID_CONCURRENCY),
  'invalid-json': '{"mps": false,',
  'invalid-extra-key': JSON.stringify({ ...VALID_CONCURRENCY, note: 'extra' }),
  'invalid-batch-order': JSON.stringify({ ...VALID_CONCURRENCY, batches: [...VALID_CONCURRENCY.batches].reverse() }),
  'invalid-nonfinite': JSON.stringify(VALID_CONCURRENCY).replace('"factor":2.2}', '"factor":NaN}'),
  'invalid-singles': JSON.stringify({ ...VALID_CONCURRENCY, single_wall_s: [1, 1.2] }),
}
function profiler(config = {}) {
  const emit = (file, value) => `cat > "$2/${file}" <<'PROFILE_FIXTURE'\n${JSON.stringify(value)}\nPROFILE_FIXTURE\n`
  return '#!/usr/bin/env bash\nset -eu\n' +
    (config.profileTimeout ? 'sleep 4\n' : '') +
    'test "$1" = harness/run_command.sh\nbash "$1"\nmkdir -p "$2"\n' +
    'mkdir -p "$2/../concurrency"\n' +
    `cat > "$2/../concurrency/concurrency.json" <<'PROFILE_FIXTURE'\n${JSON.stringify(STALE_CONCURRENCY)}\nPROFILE_FIXTURE\n` +
    ': > "$2/../concurrency/stale-marker"\n' +
    (config.profileFailures ? 'echo M5_PROFILER_INFRA\nprintf \'{"reason":"fixture"}\\n\' > "$2/infra.json"\nexit 2\n' :
      emit('stages.json', config.timings ? config.timings.map(row => ({ ...row, private_content: 'HARNESS_PRIVATE_SENTINEL_846291' })) : timings) + emit('total_wall_s.json', { total_wall_s: config.total ?? 10 }) +
      (config.gpuUtil === null ? '' : emit('gpu_util.json', config.gpuUtil || [{ t: 0, util: 25 }, { t: 3, util: 25 }, { t: 8, util: 25 }])) +
      emit('raw-telemetry.txt', 'HARNESS_PRIVATE_SENTINEL_846291'))
}
// Fake concurrency probe, substituted at invocation time by a box-side python3 shim:
// records how it was invoked, then behaves per mode.
function concurrencyProbe(mode) {
  return `import json, os, sys, time
mode = ${JSON.stringify(mode)}
out = sys.argv[2] if len(sys.argv) > 2 else None
record = {"label": "concurrency", "argv": sys.argv, "isolated": bool(sys.flags.isolated), "cwd": os.getcwd(),
          "harness": os.path.isfile("harness/run_command.sh"),
          "stale": sorted(os.listdir(out)) if out and os.path.isdir(out) else None}
calls = os.environ.get("M5_CONCURRENCY_CALLS")
if calls:
    with open(calls, "a") as stream:
        stream.write(json.dumps(record) + "\\n")
if mode == "timeout":
    time.sleep(30)
os.makedirs(out, exist_ok=True)
contents = ${JSON.stringify(PROBE_OUTPUTS)}
if mode in contents:
    with open(os.path.join(out, "concurrency.json"), "w") as stream:
        stream.write(contents[mode])
sys.exit(3 if mode == "rc" else 0)
`
}
function replace(directory, config) {
  if (!fs.existsSync(directory)) return
  for (const entry of fs.readdirSync(directory, { withFileTypes: true })) {
    const file = path.join(directory, entry.name)
    if (entry.isDirectory()) replace(file, config)
    else if (entry.isFile() && entry.name === 'profile_nsys.sh') fs.writeFileSync(file, profiler(config))
  }
}
// Exact concurrency.json shape from SCHEMAS.md "Concurrency probe".
function assertConcurrencyShape(value) {
  const positive = (x, label) => assert.ok(typeof x === 'number' && Number.isFinite(x) && x > 0, `${label}: ${x}`)
  const nullablePositive = (x, label) => { if (x !== null) positive(x, label) }
  assert.ok(value && typeof value === 'object' && !Array.isArray(value), 'concurrency must be an object')
  assert.deepEqual(Object.keys(value).sort(), ['batches', 'factor', 'mps', 'mps_failed', 'single_wall_s'])
  assert.equal(typeof value.mps, 'boolean')
  assert.equal(typeof value.mps_failed, 'boolean')
  assert.ok(Array.isArray(value.single_wall_s) && value.single_wall_s.length === 3, 'three single walls')
  value.single_wall_s.forEach((x, i) => nullablePositive(x, `single_wall_s[${i}]`))
  assert.ok(Array.isArray(value.batches) && value.batches.length === 2, 'two batches')
  value.batches.forEach((row, i) => {
    assert.deepEqual(Object.keys(row).sort(), ['all_ok', 'factor', 'n', 'skipped', 'wall_s'])
    assert.equal(row.n, [2, 4][i], 'batch order')
    nullablePositive(row.wall_s, `batches[${i}].wall_s`)
    nullablePositive(row.factor, `batches[${i}].factor`)
    assert.equal(typeof row.all_ok, 'boolean')
    assert.equal(typeof row.skipped, 'boolean')
  })
  nullablePositive(value.factor, 'factor')
}
module.exports = { profiler, replace, concurrencyProbe, assertConcurrencyShape,
  STALE_CONCURRENCY, VALID_CONCURRENCY, NULL_CONCURRENCY, PROBE_OUTPUTS }
if (require.main === module) replace(process.argv[2], JSON.parse(process.argv[3] || '{}'))
