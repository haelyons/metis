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
- `intake_check_post.py`: validates each reader's status as fixed enums (all the operator sees), checks the addendum prefix, scans for secrets, then commits and pushes.

The materials the readers downloaded (about 2.4 GB) stay in `~/.cache/blind01/intake_check_dl/` on the operator machine and are not committed. Pushing third-party materials to a remote would re-host them, which the readers' rules exclude.
