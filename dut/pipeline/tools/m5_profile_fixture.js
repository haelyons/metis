'use strict'

// Fixed-profiler transport fixture. Agent fixtures never write profiling outputs.
const fs = require('node:fs')
const path = require('node:path')
const timings = [
  { stage: 'prepare', kind: 'compute', start_s: 0, wall_s: 3, gpu_s: null },
  { stage: 'transfer', kind: 'transfer', start_s: 3, wall_s: 5, gpu_s: 999 },
  { stage: 'finish', kind: 'other', start_s: 8, wall_s: 2, gpu_s: null },
]
function profiler(config = {}) {
  const emit = (file, value) => `cat > "$2/${file}" <<'PROFILE_FIXTURE'\n${JSON.stringify(value)}\nPROFILE_FIXTURE\n`
  return '#!/usr/bin/env bash\nset -eu\n' +
    (config.profileTimeout ? 'sleep 4\n' : '') +
    'test "$1" = harness/run_command.sh\nbash "$1"\nmkdir -p "$2"\n' +
    (config.profileFailures ? 'echo M5_PROFILER_INFRA\nprintf \'{"reason":"fixture"}\\n\' > "$2/infra.json"\nexit 2\n' :
      emit('stages.json', config.timings ? config.timings.map(row => ({ ...row, private_content: 'HARNESS_PRIVATE_SENTINEL_846291' })) : timings) + emit('total_wall_s.json', { total_wall_s: config.total ?? 10 }) +
      (config.gpuUtil === null ? '' : emit('gpu_util.json', config.gpuUtil || [{ t: 0, util: 25 }, { t: 3, util: 25 }, { t: 8, util: 25 }])) +
      emit('raw-telemetry.txt', 'HARNESS_PRIVATE_SENTINEL_846291'))
}
function replace(directory, config) {
  if (!fs.existsSync(directory)) return
  for (const entry of fs.readdirSync(directory, { withFileTypes: true })) {
    const file = path.join(directory, entry.name)
    if (entry.isDirectory()) replace(file, config)
    else if (entry.isFile() && entry.name === 'profile_nsys.sh') fs.writeFileSync(file, profiler(config))
  }
}
module.exports = { profiler, replace }
if (require.main === module) replace(process.argv[2], JSON.parse(process.argv[3] || '{}'))
