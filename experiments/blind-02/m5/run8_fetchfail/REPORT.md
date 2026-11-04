# run8 evaluate failure: why `fetch_private.sh` exited 1

Paths are relative to `experiments/blind-02/m5/` unless stated. `PL` = `/home/hal/dev/interp/metis/dut/pipeline/m5/`.

## Summary

run8's sealed `harness/fetch_private.sh` is not self-contained. It reads its input list from `harness/inputs.json`. The pipeline never uploads that file to the box: it uploads only a fixed list of harness files, and the list does not include `inputs.json`. On the box, Python's `Path(sys.argv[1]).read_text()` raises `FileNotFoundError`, so Python exits 1 and `set -e` makes the script exit 1. The cause is the harness script that run8's harness agent wrote. `cmp_users.sh` (the comparison mechanism) behaved as the contract specifies. The source of the private data has not changed since run7.

## A. Why it exited nonzero

- Exit code: **1**. The receipt `run8/control/receipts/0012-comparison-users.json` has `"rc": 1, "wall_s": 32`. The command's whole log, `run8/agent/results/evaluate/comparison-box/0012-comparison-users.log:1`, is:
  `comparison users: fetch_private.sh exited 1`
- There are no further log lines to quote, by design. `PL/cmp_users.sh:126-128` sends the script's stdout and stderr to `/dev/null` ("Its output may hold private data: it is not kept"). So the Python traceback was never recorded. The cause below is inferred from the code and the run records, not read from a log. The inference is strong for the reasons below.
- The script, `run8/agent/harness/fetch_private.sh`:
  - l.4: `script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)`. This resolves to `<run dir>/harness`.
  - l.5: `python3 - "$script_dir/inputs.json" <<'PY'`
  - l.9: `for item in json.loads(Path(sys.argv[1]).read_text()):`. This is the first file access. It raises `FileNotFoundError` when `harness/inputs.json` is absent, before any network access.
- `harness/inputs.json` is never on the box:
  - The reproduce-stage upload (`PL/pipeline.js:834-836`) sends `setup.sh`, `run_anchors.sh` and `run_command.sh`; `run_evaluation.sh`, `run_units.sh` and `units.json` if they exist; and `comparisonFiles()`. That function (`PL/pipeline.js:342-343`) returns `arms/*.sh`, `cmp_files.json`, `cmp_extract.json`, `versions.sh`, `fetch_private.sh` and `evaluate.sh`. `inputs.json` is not among them.
  - Repairs re-upload only the repaired script names (`PL/pipeline.js:665`).
  - The evaluate stage uploads only `profiler/cmp_users.sh`, `cmp_system.py` and `cmp_wrap.py` before `comparison-users` (`PL/comparison.js:39-47`).
  - `inputs.json` is also absent from the seal (`run8/control/arms_seal.json`).
- The same run already hit this failure twice for other auxiliary files:
  - `run8/agent/results/reproduce/0004-setup.log:267`: `python3: can't open file '.../harness/prepare_inputs.py': [Errno 2] No such file or directory` (setup rc 2).
  - `run8/agent/results/reproduce/0006-setup.log:32`: `FileNotFoundError: [Errno 2] No such file or directory: 'harness/published.json'` (setup rc 1).
  - The repairs fixed `setup.sh` by inlining that data. `run8/agent/harness/setup.sh:80` now carries the comment "Keep setup self-contained: auxiliary harness files may not be staged". Contract and code allow repairs to change only `setup.sh`. The sealed `fetch_private.sh` could not be repaired and kept the same dependency.
- Other plausible causes are ruled out:
  - **Step 1 sealed-hash check:** it passed. A mismatch would print "is not the sealed file" (`PL/cmp_users.sh:55`), and the script ran.
  - **Permissions:** `cmp-eval` could run the script via `bash $S/harness/fetch_private.sh`. Step 3 grants `o+rX` across the run directory (`PL/cmp_users.sh:95-96`). `cmp-private` is owned by `cmp-eval` at mode 700 (`:100`).
  - **Network:** only `cmp-arm` has the REJECT rule (`:12`, `:85-87`).
  - **Source:** the URLs, byte counts and SHA-256 values in `run8/agent/harness/inputs.json` and `run8/control/comparison.json` match run7's inline list exactly.
  - **rc 1 itself:** this is what an uncaught Python exception under `set -e` produces. A checksum mismatch would also raise. But the script cannot reach any download or checksum step without first reading `inputs.json`.

## B. Where the cause lies

**The harness script.** It is not in the comparison mechanism, the private-data source, or the box.

- What `cmp_users.sh` gives `cmp-eval` matches `PL/SCHEMAS.md:166` (Separated users step 5):
  - working directory `cmp-private`
  - `HOME` and `TMPDIR` set to `cmp-private/.home`
  - the box environment minus `CMP_*`, `SUDO_*`, `HOME` and `TMPDIR`, so `PATH` is kept (`PL/cmp_users.sh:118-128`)
  - membership in the `/dev/nvidia*` groups
  - no network rule
- None of these is implicated. `inputs.json` would be missing for any user.
- The contract gives the harness everything it needs to be self-contained:
  - The harness prompt asks for "self-contained bash scripts" (`PL/pipeline.js:774`).
  - Only the named comparison files are sealed and uploaded with the harness (`PL/SCHEMAS.md:157`).
  - run7's `fetch_private.sh` was self-contained and passed.
- No mechanism defect: `mechanism_defect: none`, `contract_requires_behaviour: not_applicable`.

A note for the owner on pipeline hardening, not needed to explain this failure: the pipeline could reject a sealed comparison file that references a harness file it does not upload, or upload and seal such files. Today this only shows up on the box.

## C. Same script as run7? Did a repair change it?

- **Not the same.** The sealed hashes differ:
  - run7: `96f56759…` (`run7/control/arms_seal.json:10`)
  - run8: `88e00b9a…` (`run8/control/arms_seal.json:10`)
- **How they differ:**
  - run7's script embeds the four reference items (URL, bytes, SHA-256) inline in a Python heredoc and reads no other file.
  - run8's script reads `harness/inputs.json` instead.
  - Each run's harness agent writes these scripts fresh. Neither is supplied by s27 or s28: `run8/args.json` has no `harness_from`. The s27 and s28 briefs say the same thing about `fetch_private.sh` (`FIXTURE_BRIEF.md:347` in both).
- **Repairs did not touch it.**
  - Both repairs changed only `setup.sh`: `run8/agent/wf/agents/0003-harness-repair/reply.txt` and `0004-harness-repair/reply.txt`; their `codex-1.jsonl` records file changes only to `harness/setup.sh`.
  - The pipeline restores protected scripts after a repair (`PL/pipeline.js:654-657`). Sealed files "never" change (`PL/SCHEMAS.md:157`).
  - The box copy matched the seal taken at 22:43:01Z, before setup ran (step 1 passed).

## D. What should happen next

- **Do not rerun run8 unchanged.** The sealed `fetch_private.sh` will fail the same way every time.
- **A second defect is waiting.** `run8/agent/harness/evaluate.sh:8` runs `harness/evaluate_dockq.py`, which is also never uploaded, and `evaluate_dockq.py:16` reads `inputs.json`. Evaluate would fail at the first evaluator call even if the fetch were fixed.
- **Recommended:** a science step (s29) changes the brief/design. It should require every sealed comparison file (`fetch_private.sh`, `evaluate.sh`, `arms/*.sh`, `versions.sh`) to be self-contained. That means reading no other file under `harness/` and embedding what they need (for `fetch_private.sh`: each reference's URL, bytes and SHA-256, as run7 did). It should also note that only the listed harness files reach the box. Alternatively, supply a vetted harness with `args.harness_from`. Then rerun the fixture.
- **No pipeline fix or public reproduction is required.** The mechanism worked as specified. The optional hardening in B is useful but is not a precondition.
