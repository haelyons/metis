You are an authorized reader for the blind-01 experiment. The owner authorized readers to see its brief and records. The operator who launched you is blind to this experiment's content and sees only `status.json`, as validated enum values; your final reply is not shown to the operator.

Working directory: experiments/blind-01/m5/ of the metis repository (the current directory). Write only into `run5_diag/`. This is a read-only diagnosis: change nothing else, run no workloads, contact no box, fetch nothing from the network.

## What the operator knows (metadata only)
Run5 (`run5/`) passed intake. Reproduce failed with error class `infra` after about 250 s. The run's receipts are `0001-upload` and `0002-probe`, both rc 0; no third receipt exists, although the harness-writing agent ran. In `dut/pipeline/m5/pipeline.js`, `boxCommand` returns `infra` when `m5/boxrun.sh` leaves no receipt; `boxrun.sh` writes a receipt on every exit, so it likely never started. One candidate: `uploadHarness` puts every harness script, base64-encoded, into a single `--cmd` argument, and Linux rejects any single argument over 131072 bytes with E2BIG at spawn. Check this and any other cause with equal care; do not assume it.

## Read
- `run5/pipeline.log` and the run's wf records under `run5/agent/` (the error around the harness upload)
- the harness scripts the agent wrote for run5 (find them under `run5/agent/`; `pipeline.js` names the harness directory)
- `dut/pipeline/m5/pipeline.js` (`boxCommand`, `uploadHarness`, `reproduce`) and `dut/pipeline/m5/boxrun.sh`, read-only
- `run5/` intake records, and `intake_mirror/BRIEF_run5.md`, only as needed to say why the harness is the size it is

## Rules
- Never read `.keys` files, credential files or anything under `~/.codex/`.
- Do not commit or push; the launcher commits `run5_diag/`.
- No fabrication. If something cannot be established, use the `unknown` value.

## Outputs
1. `run5_diag/REPORT.md` for the owner: the failing step and its evidence (quote the decisive log lines), the byte size of each uploaded harness script and of the base64 upload command, what makes the harness large if it is, and whether the brief or intake records ask for per-file hash checks.
2. `run5_diag/status.json`, one JSON object with exactly these keys, each taking only the listed values:
   - `"failed_step"`: `"probe"`, `"harness_agent"`, `"harness_upload"`, `"setup"`, `"other"`, `"unknown"`
   - `"upload_error"`: `"e2big"` (the log shows E2BIG or "argument list too long" for the upload), `"other"`, `"none"`, `"unknown"`
   - `"upload_command_bytes"`: the size of the single upload `--cmd` argument: `"under_128k"`, `"over_128k"`, `"unknown"`
   - `"large_content"`: what dominates the harness bytes: `"embedded_hashes"`, `"embedded_data"`, `"other"`, `"not_large"`
   - `"hash_checks_requested"`: `true` when the brief or the intake records list per-file hashes for the run to check, otherwise `false`

   No other keys and no free text.

Finish within 20 minutes. End with a final reply that is exactly the contents of status.json.
