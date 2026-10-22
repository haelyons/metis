# On-box execution contract (seed for the launcher writer)

What the execution layer of a measure run must look like, as requirements and a schema, not code. The build agent
reads this beside the design record and the execution directive; the gate's directive may tighten any item, never
loosen one. Every item below exists because a run failed without it (m1 to m4, 2026-10; the frozen launcher's own
billing incidents, 2026-06 to 2026-08). Where an item names a number, the number is a floor or a ceiling, not a
suggestion.

## 1. Shape

Two files, nothing else: `run_<tag>.py` (stages, parsers, records; stdlib only unless the design names a
library, and then only inside the on-box stages) and `onbox_<tag>.sh` (environment, order of stages, guards, exit
codes). The local launcher (`lambda_run_<tag>.sh`, operator-owned, never written by the build) ships the payload,
starts `remote_run_<tag>.sh bash onbox_<tag>.sh` detached under `timeout REMOTE_TIMEOUT`, polls a marker, fetches
`results_<tag>/out/` and terminates the box. The build never edits the launcher; if the launcher must change, the
build stops and reports the exact declared point.

## 2. Interface

Environment in (every one optional, every one read through a default and echoed once into the environment record,
never dumped wholesale): `PRICE_USD_PER_HOUR`, `BUDGET_LEFT_USD`, `REMOTE_TIMEOUT` (seconds, the whole box
lifetime the launcher enforces), `INSTANCE_TYPE`, `LAMBDA_INSTANCE_ID`, `GIT_COMMIT`, `HF_TOKEN` (downloads only).
Files in: the payload under `~/<tag>_run/` exactly as listed in the directive; `data/` if shipped. Files out:
everything under `~/<tag>_run/results_<tag>/out/`; nothing written anywhere else on the box except the engine build
directories the directive names. Exit codes of `onbox_<tag>.sh`: 0 every stage done and valid; 2 infrastructure
(install, compile, download, GPU not visible); 3 guard stop (time or cost); 4 anchor failed; 5 a stage failed after
the anchor. The launcher records the code in `RUN_DONE`; the script never writes that file.

## 3. Order of stages, each a hard gate for the next

1. **Preflight** (seconds): GPU visible and named (`nvidia-smi`), driver and CUDA versions, free disk, python and
   the preinstalled libraries' versions, clock; all into `env_<tag>.json`. Any missing requirement: exit 2 at once.
2. **Install or compile** from the sources the directive names, pinned by version or commit, hash of every
   downloaded archive recorded; non-interactive (`DEBIAN_FRONTEND=noninteractive`, `apt-get -y`, `pip -q`); wait
   for the apt lock rather than fail on it; never patch the source, never substitute a package: failure is exit 2.
3. **Engine capability check** before any physics: query the built binary for the features the design relies on
   (package list, precision, styles, device) and compare with the directive's list; a missing feature is exit 2,
   never a fallback. This is the m3 lesson (a pinned build with the GPU package off ran two builds before anyone asked
   the binary).
4. **Timed dry run** on the real input and the real command line, short (1 to 2 % of the main phase), measuring the
   rate the whole plan depends on; from it, project every remaining phase's wall-clock and cost.
5. **Guard decision**, written as a record before the long phases: allowed seconds =
   `REMOTE_TIMEOUT - elapsed - fetch_margin(600 s)`; allowed cost = `BUDGET_LEFT_USD`; projected seconds from the
   measured rate with a 1.5x margin; if either projection exceeds its allowance, shorten per the directive's stated
   rule or stop with exit 3; the record carries every number of the arithmetic so a reader can redo it.
6. **Anchor** (the published value the protocol must reproduce) before the inputs; a miss outside its tolerance
   writes the anchor record with decision FAIL and sets `run_valid=false` (scientifically unvalidated) for every later
   record; the measurement phases still run unless the directive says stop, and the script exits 4 at the end. Every
   later record carries `calibration_valid`, decided only by that phase's own checks (the guards, completion, and the
   workload checks the directive names: input sizes, step counts, well-formed outputs), never by the anchor; the
   anchor's verdict is never changed by what follows. The anchor stage also writes its diagnostics into the anchor
   record: the reference scored against itself, against a rigidly transformed copy of itself, the count of elements
   paired between result and reference, and an independent scoring where the directive names one.
7. **Measurement phases** in the directive's order; each writes its record the moment it finishes (atomic: write a
   temp file, rename), never at the end of the run, so a killed run keeps every finished result.
8. **Summary** last (`<tag>_summary.json`), then `RUN_VALID.json`; then exit. The summary carries a `compute` table:
   for every stage that ran (stages after an anchor FAIL and the stage that failed included), its wall-clock seconds,
   GPU-busy seconds where measurable, GPU name and exit code. An exit trap writes it on every exit, early stops
   included, so every launch leaves its compute record whatever the anchor or a stage decided.

## 4. Guards

A guard reads only measured quantities: the dry run's rate, the clock, the price. It never trusts the card's or the
design's number for a rate. It re-checks before every long phase, not once. It stops cleanly: the current phase's
partial output is kept and labelled partial; the guard record states which phases did not run and why. Time cap
arithmetic uses the launcher's `REMOTE_TIMEOUT` from the environment, never a constant copied into the script.

## 5. Records (provenance.py)

One record per endpoint, control and phase; the decision rule in the record before the values; `cell`, `inputs`
with hashes, `metric`, `values`, `threshold`, `decision`, `env`, `run_valid`, `run_valid_voided_by`, `calibration_valid`. The inputs the
card is measured on: `endpoint-C<i>_tag-<tag>.json` with `values.measured` (a number, the card's unit), `values.unit`,
`values.card_value`, `values.band`; `decision` PASS, FAIL or VOID against the band. Labels in every measured record:
instance type, GPU name and driver, engine version and build flags, precision, wall-clock, process and thread counts
(a per-GPU rate on one process with the GPU idle is a different quantity from a per-GPU rate; m3 measured the former
and the card meant the latter). Raw rows (every run, every thermo or step line) as JSON lines beside the records.
Units in field names or in `values.unit`, never implied.

## 6. Logging

All stdout and stderr of every stage into files under `results_<tag>/out/`; one short progress line per minute or per
phase to the main log so the launcher's one-line poll shows movement (a silent hour reads as a hang). No secrets, no
`env` dumps, no token in any log. Keep every engine log; keep the first and last lines of large sampling files, not
the whole.

## 7. Stage interface (what the tests call; no implementer selftest)

`python3 run_<tag>.py --stage <name> --in <dir> --out <dir>` runs exactly one stage of section 3 (the directive names
the stages) on the inputs in `--in` (an earlier stage's outputs or a fixture) and writes only under `--out`, with the
exit codes of section 2. Every external program a stage calls is resolved through an environment variable the
directive names (default: the real program), so a test can put a replay program in its place. Every parser of external
output is a module-level function the directive names, taking a path and returning a dict, raising `ValueError` on
malformed input; the stage turns that into a failed record and its exit code, never a default value. Importing
`run_<tag>.py` does no work. Tests are written by a separate author against this interface, with fixtures recorded on
the box, and run locally in a copy of the environment of record before every launch.

## 8. Predictable failures and the check that catches each before money is spent

| failure (seen) | check in the build |
|---|---|
| engine built without the feature the design uses (m3 build 2) | stage 3 capability query against the directive's feature list |
| GPU style incompatible with a deck line (m3 launch 2) | dry run on the real deck and command line, not a toy input |
| main phase longer than the window (m3 launch 1) | stage 4 rate, stage 5 projection with margin, re-check per phase |
| labels or constants copied from the card and stale (m3 build 3) | labels read from runtime queries, never literals |
| rate measured on an idle GPU (m3 result) | process and thread counts in every record; the directive names the parallel layout |
| CRLF script shipped from a Windows checkout (2026-07) | launcher normalises; the build writes LF |
| silent CPU fallback (2026-06) | device assertion at preflight and in the engine check |
| numpy or torch ABI break from a pip upgrade (2026-08) | pin per `frozen/remote_run.sh`; never upgrade the preinstalled torch |
| pip resolver replacing the CUDA torch | install only pure-python packages, never torch |
| dropped SSH killing the job | the launcher's setsid and marker poll; the build never relies on the session |
| results written outside the fetched directory | one output root; the summary lists every file written |
| guard reads a constant instead of the environment | local test runs the guard stage with a different `REMOTE_TIMEOUT` and checks the arithmetic follows it |
| the directive contradicts itself (m3 build 1, m4 build 3) | the build stops and reports the two items, never chooses |
| parser meets the real program's output for the first time (m4 launch 6) | the box output becomes a fixture; local test of the parser on it and on a malformed copy |
| repeated program calls share a working directory (m4 launches 7, 8) | local test runs the stage twice with a replay program, checks the outputs stay separate |
| anchor scoring or pairing wrong (m4 launches 9, 10) | anchor diagnostics in the anchor record; local round-trip and transformation tests on the reference |
| apt lock held by unattended upgrades at boot | wait loop on the lock with a cap, then exit 2 |
| disk full during download or compile | free-space check at preflight against the directive's estimate |
| long phase with no output line | periodic progress line; the launcher's poll shows the tail |
| teardown not confirmed (2026-06) | launcher's retry loop; the build never terminates the box itself |

## 9. What the build returns

`runner_py` and `onbox_sh` as paths; `stages`: the stage names with their inputs; `onbox_command` as the single line the operator runs
through `remote_run_<tag>.sh`; `expected`: a table of phases with projected wall-clock from the design's numbers and
the record files each writes, so the reviewer can check the projection against the caps before launch.
