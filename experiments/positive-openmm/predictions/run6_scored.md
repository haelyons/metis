# positive-openmm run6: outcome against sealed predictions (predictions/run6.md, 6e233bf)

Run committed a255d48. Box gpu_1x_h100_sxm5, USD 4.29/h; run_box_usd 2.53; 746k tokens in; pipeline exit 0; box torn down; push verified by the chain.

## Verdict
Inconclusive: the first run to pass intake, reproduce, profile, seal and propose, then stopped at implement on a host sandbox defect. No method was written, so nothing about the method or its evaluation was tested.

- Reproduce: `run_command.sh` holds only the environment and the measured command; no preflight block, no repair needed (U27's prompt rule held). Sequential ensemble 45.9 s on H100 SXM5.
- Profile: MPS verified (`mps` true, `mps_failed` false), concurrency factor 2.00.
- Seal: margins SD/sqrt(8) of each per-seed outcome from reproduce's `ensemble.json` (37.7 kJ/mol for mean potential), each citing file and statistic. Minimum worthwhile gain 1.05, 7 repetitions, 32 paired seeds, compute caps 60/120/240 s.
- Propose: approved 5 of 5, data-parallel over inputs, expected speedup 1.575.
- Implement FAIL (`parse`, exit_kind infra): the isolated test author (Codex exec, `-s workspace-write`, inside the pipeline's bubblewrap namespace) got `bwrap: No permissions to create a new namespace` for every command and replied "Blocked". This host sets `kernel.apparmor_restrict_unprivileged_userns=1` with Ubuntu's `bwrap-userns-restrict` profile: the outer bwrap works, nothing inside it can create another user namespace, so Codex's own sandbox cannot start. Reproduced outside the pipeline (`codex sandbox -- echo` works alone and fails inside bwrap). No earlier m5 run reached implement, so the isolated Codex path had never run for real on this host.

## Scores
| Prediction | Outcome | Hit |
|---|---|---|
| H100 SXM5 0.45 | H100 SXM5 | yes |
| intake PASS 0.9 | PASS | yes |
| reproduce PASS 0.85; no preflight in run_command.sh 0.7 | PASS; none | yes; yes |
| sequential ensemble 35 to 55 s on H100 | 45.9 s | yes |
| profile PASS 0.9; MPS verified 0.9 | PASS; verified | yes; yes |
| H100 headroom median 2.0 [1.4, 2.8] | 2.00 | yes |
| seal PASS 0.7; margins cite reproduce 0.85; SD/sqrt(n) 0.5 | PASS; cited; SD/sqrt(8) | yes; yes; yes |
| propose approved 0.65; data-parallel 0.5 | approved 5/5; data-parallel, 1.575 | yes; yes |
| implement reached 0.3 | reached | yes |
| implement PASS 0.45 given reached | FAIL (host sandbox, no method written) | no, not a method outcome |
| MPS daemon 0.7; processes over threads 0.75 | not tested | n/a |
| evaluate reached 0.14 | SKIPPED | no |
| takeaways PASS 0.95 | PASS | yes |
| run_box_usd bins | 2.53 (stopped in implement, between the two bins) | n/a |
| pipeline exit 0, box torn down, push verified 0.9 | yes | yes |

## Fix
U28 (runner, no gate change): the pipeline's bubblewrap namespace is the only sandbox for isolated roles. Inside it Codex runs with `danger-full-access`; roles without Write, Edit or Bash get their view mounted read-only, so the writable set is unchanged. Regression: with real bubblewrap on this host, an isolated Codex writer runs a command and writes in its view, a read-only role cannot, and neither writes outside the view. Then run7 from the same brief.

## Note for evaluate
The seal fixes 32 paired seeds, 7 repetitions and three compute caps. Its stated per-method cap of 188,160 GPU-seconds is a prospective ceiling, not a projected cost; actual evaluation cost is set by fixed work (about 46 s per eight-replica ensemble on H100).
