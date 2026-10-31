Run5 failed during harness upload, before setup. Reconstructed single upload `--cmd` argument measures **441,652 bytes**, exceeding Linux's 131,072-byte per-string limit on a 4 KiB-page host. Oversized argument strongly supports pre-execution E2BIG as cause. **Actual exception remains unknown:** saved pipeline and workflow records contain neither `E2BIG` nor `argument list too long`; pipeline discards execution exceptions. Accordingly, `status.json` records `failed_step: harness_upload`, `upload_command_bytes: over_128k`, and `upload_error: unknown`.

Decisive saved evidence:

- `run5/pipeline.log:1–2`:

  ```text
  [args] intake: PASS
  [args] reproduce: FAIL
  ```

- `run5/control/stages/reproduce.json:1`, quoted verbatim:

  ```json
  {"stage":"reproduce","status":"FAIL","error_class":"infra","exit_code":2,"wall_s":250.15728892299998,"model_family":"codex","gpu_s":0,"usd":0.014372222222222222,"tokens_in":764114,"tokens_out":11975,"notes":[]}
  ```

- `run5/agent/wf/journal.jsonl:5` and `:8`:

  ```json
  {"ts":"2026-10-31T15:49:33.915Z","type":"phase","t":"reproduce"}
  {"ts":"2026-10-31T15:53:44.151Z","type":"log","m":"reproduce: FAIL"}
  ```

- Journal line 7 records harness agent's successful result at `15:53:44.068Z`, only 83 ms before failure. `run5/agent/wf/agents/0002-harness/meta.json` records `"errors": []`; workflow status records harness state `ok`. Final acknowledgement, also present in harness transcript line 271:

  ```text
  Created four harness scripts. Syntax checks pass. No local builds or workloads run.
  ```

- Only receipts present: `run5/control/receipts/0001-upload.json` and `0002-probe.json`. Both record `"rc": 0`, `"timed_out": false`, `"fetched": true`, and `"wall_s": 13`. First receipt covers probe-script upload, not harness upload. No `0003-upload.json`, setup receipt, or reproduce output/log exists.

Failure location follows pipeline control flow. `dut/pipeline/m5/pipeline.js:273–325` collects probe, awaits harness agent, uploads four scripts, then invokes setup. Missing/unreadable harness scripts or generation failure would take `parse` paths. Instead stage reports `infra`. At lines 169–200, `boxCommand` executes `bash m5/boxrun.sh ... --cmd <command> ...`, catches and discards exception, then returns `{ error: 'infra' }` if receipt cannot be read. `reproduce` immediately propagates failed upload at line 324. Setup lies after that gate.

Current `pipeline.js` SHA-256 matches run's recorded `run5/agent/wf/run.json` value exactly: `cbe43c6c35ed9fc337bf278a62b244f0989b707afe76e5b99d76df45c99640db`. Thus reconstructed upload uses recorded pipeline version.

Uploaded scripts, in pipeline order:

| Script under `run5/agent/harness/` | File bytes | Base64 payload bytes | Upload statement bytes |
| --- | ---: | ---: | ---: |
| `setup.sh` | 317,610 | 423,480 | 423,525 |
| `run_anchors.sh` | 3,470 | 4,628 | 4,679 |
| `run_command.sh` | 4,640 | 6,188 | 6,239 |
| `run_evaluation.sh` | 5,343 | 7,124 | 7,178 |
| Total | 331,063 | 441,420 | 441,621 |

`uploadHarness` (lines 202–208) base64-encodes each complete file without wrapping and emits `printf %s '<base64>' | base64 -d > 'harness/<name>'`. All four statements share one argument, prefixed with `set -e\nmkdir -p harness out\n` and separated by newlines; no final newline. Base64 payloads total 441,420 bytes; shell syntax, paths, prefix and separators add 232 bytes. Result: **441,652 UTF-8 bytes excluding terminating NUL**, or **441,653 including NUL**. Argument SHA-256: `3a659ff6a4671eb232234436f8f87de1280db160e68d7d0c09e6224776c66a68`. Count excludes `--cmd` option name and other argv entries. Reconstruction reads files as data; it executes no uploaded command.

Local `/usr/include/linux/binfmts.h:15` defines `MAX_ARG_STRLEN (PAGE_SIZE * 32)`; current host page size is 4,096 bytes. Single-string limit therefore equals 131,072 bytes including NUL. Reconstructed argument exceeds limit by 310,581 bytes. `setup.sh`'s base64 payload alone already exceeds limit. Aggregate argv capacity cannot fix this per-string violation. No oversized spawn was attempted during diagnosis.

Large content is **embedded_hashes**: `setup.sh:57` embeds base64 of zlib-compressed JSON inventory, copied exactly from `run5/agent/intake/data.json`'s 3,602-entry `inventory`. Decoded JSON measures 1,114,666 bytes; compressed bytes measure 231,816; base64 literal measures 309,088. Literal occupies 97.32% of setup and 93.36% of all four scripts. Without literal, setup measures 8,522 bytes. Inventory contains file names, URLs, provenance, retrieval timestamps, byte sizes and per-file SHA-256 digests, rather than molecular coordinates, archives, or other workload payloads. All 3,602 digests are valid 64-character hexadecimal strings. Associated metadata contributes bytes too; label identifies hash-bearing manifest as dominant content, not hashes alone.

Brief's inventory rows (`intake_mirror/BRIEF_run5.md:69–3670`) match all embedded records. Intake brief is byte-identical to supplied brief. Inventory spans 1,610 mapping files, 1,480 PDB files, 500 separated test PDBs, four manifests and eight root entries. Brief line 60 explains coverage: inputs for all 250 PINDER-S cases plus default-API auxiliary downloads for prioritized 93 cases. In contrast, intake `EXECUTION.json` fixes calibration to one apo pair, five poses and eight MPI processes. Harness carries complete materials inventory even though setup fetches index/metadata and selected case's inputs (`setup.sh:82–84,118–138`). Large harness reflects embedded provenance/checksum inventory, not large executable logic or calibration scale.

**Hash checks requested: true under supplied definition.** Brief and intake list per-file hashes available for run to check. Brief line 65 states:

> File inventory: exact remote locations, provenance, current retrieval times, byte sizes and SHA-256. Each row's SHA-256 is both the locally computed digest and the matching streaming re-fetch digest.

Table then lists 3,602 named files and SHA-256 values; `data.json:28` carries same inventory. Setup checks fetched archive hashes (`:59–64,78–80`), index/metadata hashes (`:82–84`), and listed selected inputs (`:128–135`). These records supply per-file checks, but do not require embedding entire inventory inside script or checking every listed file during one-case calibration. Mirror checks identify selected bytes; brief explicitly leaves identity with original study distribution unresolved.

Other causes considered: probe failure conflicts with two successful receipts and completed harness generation. Harness-agent failure conflicts with completed turn, empty error list and four present scripts. Dependency installation, CUDA checks, compilation, input downloads and scientific scoring are downstream of upload and cannot explain this observed failure. Ordinary remote launch/fetch failures after argument parsing normally still produce receipt via `boxrun.sh`'s EXIT handler (`:11–39`). However, receipt-on-every-exit premise has limits: `mktemp`/`date` run before EXIT trap, receipt path is assigned only during argument parsing, receipt Python/write can fail, and SIGKILL bypasses trap. Transient local spawn, early startup or receipt-storage failures cannot be excluded solely by missing receipt. No saved evidence identifies one of those alternatives. Oversized argument is independently established and sufficient to prevent ordinary Linux launch; actual historical errno was swallowed and cannot be recovered from these records.

Diagnosis used local record/code reads, byte counting, hashing and data-only inventory decompression. No harness, build, workload, pipeline or box command ran; no network access, credential reads, commits or pushes occurred. Only requested diagnosis files were written under `run5_diag/`.
