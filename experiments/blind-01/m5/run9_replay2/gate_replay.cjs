// Execute the actual validateProfile function without running the pipeline.
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const base = __dirname;
const pipeline = path.resolve(base, '../../../../dut/pipeline/m5/pipeline.js');
const source = fs.readFileSync(pipeline, 'utf8');
const begin = source.indexOf('    function validateProfile() {');
const end = source.indexOf('\n    try {\n      rmSync', begin);
if (begin < 0 || end < 0) throw new Error('Cannot locate validator');
const validator = source.slice(begin, end);
fs.writeFileSync(path.join(base, 'validateProfile.source.js'), validator + '\n');
const gateDir = path.join(base, 'gate');
const destination = path.join(gateDir, 'input');
fs.mkdirSync(path.join(destination, 'out'), { recursive: true });
const inputLink = path.join(destination, 'out/profile');
if (!fs.existsSync(inputLink)) fs.symlinkSync(path.join(base, 'patched'), inputLink, 'dir');
const facts = {};
const context = {
  facts, destination, A: gateDir, C: path.join(gateDir, 'control'), boxProbe: {}, path,
  readJSON: file => JSON.parse(fs.readFileSync(file, 'utf8')),
  nonnegative: value => typeof value === 'number' && Number.isFinite(value) && value >= 0,
  rmSync: fs.rmSync, writeFileSync: fs.writeFileSync,
};
const result = vm.runInNewContext(validator + '\nvalidateProfile()', context);
const stages = context.readJSON(path.join(base, 'patched/stages.json'));
const { total_wall_s } = context.readJSON(path.join(base, 'patched/total_wall_s.json'));
const gpuUtil = context.readJSON(path.join(base, 'patched/gpu_util.json'));
const named = stages.filter(item => /(?:^|[\s_-])(?:process|wrapper|telemetry|total|overall)(?:$|[\s_-])/i.test(item.stage));
const timed = stages.filter(item => item.wall_s >= total_wall_s * 0.98 && item.wall_s <= total_wall_s * 1.02);
const evidence = {
  validator_return: result, facts, stages, stage_count: stages.length,
  stage_count_ok: stages.length >= 3, total_wall_s,
  timed_wall_s: stages.reduce((sum, item) => sum + item.wall_s, 0),
  timed_fraction: facts.timed_fraction, timed_fraction_ok: facts.timed_fraction >= 0.9,
  wrapper_lower_inclusive: total_wall_s * 0.98,
  wrapper_upper_inclusive: total_wall_s * 1.02,
  wrapper_name_matches: named.map(item => item.stage),
  wrapper_wall_matches: timed.map(item => item.stage),
  gpu_util_sample_count: gpuUtil.length, gpu_telemetry: facts.gpu_telemetry,
};
fs.writeFileSync(path.join(base, 'gate_evidence.json'), JSON.stringify(evidence, null, 2) + '\n');
console.log(JSON.stringify(evidence, null, 2));
