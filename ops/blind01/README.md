# blind-01 operator tooling (copies)

The scripts and prompts the blind operator used for blind-01 m5, copied from `~/.cache/blind01/` and `~/.claude/hooks/` so they can be audited. The live copies stay in those locations; these are snapshots as of 2026-10-31.

- `blind_guard.py`: PreToolUse hook that keeps the operator's session blind to experiments/blind-01 content.
- `blind_read.py`: the operator's only reader of run metadata (signature fields, enum facts, receipts, box).
- `new_run.py`, `retry38.sh`, `commit_run.sh`: run creation, the run chain and its commit step.
- `backfill_blind.py`: commits uncommitted blind evidence unread.
- `intake_check.md`/`.sh`: the authorized reader on Claude Opus (restricted mode). Output in `experiments/blind-01/m5/intake_check/`.
- `intake_check_codex.md`/`.sh`: the Codex cross-check, with an independent phase A and then alternatives. Output in `m5/intake_check_codex/`.
- `intake_acquire.md`/`.sh`: the Codex acquisition pass. Output in `m5/intake_acquire/`.
- `intake_mirror.md`/`.sh`: the Codex mirror reader after the owner approved the unverified mirror (2026-10-31, option 2). No new search: it records the candidate's URLs, sizes and SHA-256, re-fetches to check them, keeps the provenance `unverified_mirror` and writes the run5 brief addendum. Output in `m5/intake_mirror/`. The same day `intake_acquire.md` was amended so an unverified mirror counts as usable only with the owner's approval.
- `run5_diag.md`/`.sh`: read-only Codex diagnosis of run5's reproduce `infra` failure (no network). Output in `m5/run5_diag/`; it led to U44 (chunked harness uploads).
- `run6_diag*.md`/`.sh`: three read-only Codex diagnoses of run6's setup failures (the third may look up package-index metadata only). Outputs in `m5/run6_diag*/`; they led to U45 (apt from enabled sources).
- `run7_diag*.md`/`.sh`: two read-only Codex diagnoses of run7's setup failures (no network). Outputs in `m5/run7_diag*/`; they led to U46 (setup four repairs).
- `run8_family.md`/`.sh`: a check-only Codex reader of run8's call records: whether the Codex usage outage changed which family answered (it did not). Output in `m5/run8_family/`.
- `run8_diag*.md`/`.sh`: two read-only Codex diagnoses of run8's anchors failures (no network). Outputs in `m5/run8_diag*/`; they led to U47 (finish-first timing for setup, anchors and profile). `retry38.sh` since then gives the pipeline 46,800 s and the box `--max-hours 14`, one hour beyond the 12 h run ceiling.
- `run9_obs.md`/`.sh` and `run9_diag*.md`/`.sh`: Codex readers of run9 (reproduce PASS, profile FAIL parse). They found a CPU-only published baseline and Nsight 2025 writing empty skipped reports, which led to U48.
- `retry44.sh` (U48) and `retry45.sh` (U48 correction), with their prompts `u48*.md`: Codex implements, Opus writes tests from SCHEMAS.md with the implementation Read-denied.
- `run9_replay.md`/`.sh`, `run9_replay2.md`/`.sh`, `run9_par.md`/`.sh`, `run9_scale.md`/`.sh` and `run9_scale2.md`/`.sh`: the owner's neutral assessment of run9. The replays ran the summariser and gate on saved files and showed that merged U48 used phrases Nsight never prints. The others covered the workload's parallel structure and what the reduced-scale reproduce pass establishes.
- `run9_outputs.md`/`.sh`: Codex reader of run9's per-unit outputs and costs; it showed the host-only condition (U49) holds on run9's saved profile.
- `run10_harness*.md`/`.sh` (three attempts) and `run10_review*.md`/`.sh` (independent reviews), with `run10_why`, `run10_mech`, `run10_inputs` and `run10_diff`: unit files for the equivalence check. The command-line selector has no effect; the usable route is a restricted copy of the prepared input list holding original records, passed through an input the measured command already accepts (owner decision 2026-11-01). `run10_harness3` is the one used; run9's own `run_command.sh` has an inherited path conflict, recorded separately.
- `retry46.sh` (U49), `retry47.sh` (U50a, U51) with prompts `u49*.md`, `u50a*.md`, `u51*.md`; `u50.md`/`u50_t.md` are the held whole-U50 prompts, superseded by U50a. `retry48.sh` is `retry38.sh` with run9's box type first, used for run10.
- `new_run.py`: creates a run's `args.json` from run1's; options `--addendum`, `--harness-from=<folder>`, `--stop-after-profile`, `--units-check=<run>`.
- `blind_guard.py`: copy of the operator's PreToolUse hook (`~/.claude/hooks/`), which keeps the operator's tools off blind content; its launcher allowlist covers the `new_run.py` options above.
- `intake_check_post.py`: validates each reader's status as fixed enums (all the operator sees), checks the addendum prefix, scans for secrets, then commits and pushes.

The materials the readers downloaded (about 2.4 GB) stay in `~/.cache/blind01/intake_check_dl/` on the operator machine and are not committed. Pushing third-party materials to a remote would re-host them, which the readers' rules exclude.
