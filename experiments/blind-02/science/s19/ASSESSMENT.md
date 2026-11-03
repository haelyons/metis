# s19 assessment: revised seed-neutral draft of "Sealed comparison (U57, U58)" (2026-11-03)

**Scope.** I ran no test. I used no network, contacted no box, ran no git commands and read no credentials. Bash was denied, so I used only the file tools, and wrote only into `science/s19/`. I read:
- `science/s13/` (FINAL.json; ASSESSMENT.md §4–5), `s15/SHAPES.json`, `s17/` (PROMPT.md, DRAFT.md, ASSESSMENT.md) and `s18/` (AUDIT.json, ASSESSMENT.md);
- `dut/pipeline/m5/SCHEMAS.md`: lines 16–60 (intake, probe, harness, repairs) and 228–231 (wf `isolation`, implement views);
- `dut/pipeline/m5/pipeline.js`: lines 21–22 (`input.cwd = A`), 85–110 (the intake prompt reads the brief by path), 275–290 (repairs and the restore of protected scripts) and 394–421 (the harness prompt reads `A/intake/*`);
- `dut/pipeline/m5/implement.js`: lines 89 and 121 (a per-call `mkdtemp` view; `hidden: [root, journal dir]`).

`DRAFT.md` is one section, starting with `## Sealed comparison (U57, U58)`, and it replaces s17's draft. All of s17's seed-neutrality rules still hold:
- It names no seed program, case, file or output, and no number from the seed, its materials or the findings.
- The only new literals are generic: file modes (`600`, `700`, `711`), the user names `cmp-arm` and `cmp-eval`, and the system tools `sudo`, `pkill`, `pgrep` and `env`.

## 1. s18's finding `leaks_or_biases`: the evaluator could learn the arm

**s18's finding** (`s18/ASSESSMENT.md:77-83`). The invocation path `comparison-work/<round>/<arm>/<input>/` was both the evaluator's working directory and its `CMP_ARM_OUT`.

**Fix** (DRAFT "Rounds", "Each invocation"):
- **Opaque tokens.** Each invocation is named on the box only by the token `i<k>` (its index in run order).
- **Arm identity off the command line.** The arm and input go into a job file `comparison-jobs/i<k>.json`:
  - It is written by a separate, earlier box command.
  - The file has mode `600` in a directory with mode `700`, owned by the box user.
  - The wrapper's only argument is the token. This matters because process arguments are world-readable under `/proc`, so an arm id in `argv` would be visible to the evaluator.
- **Evaluator surroundings.**
  - It runs from the shared run directory, not from the arm's `run/`. This also stops the arm from planting a fake `harness/` link that the evaluator would execute.
  - It runs the absolute path of `evaluate.sh`.
  - It runs as `cmp-eval`, which cannot read the job files or the `600` `wrap.json` files of earlier invocations.
  - Every `cmp-arm` process, whose arguments name the arm's commands, is killed before the evaluator part starts.
- **Host side.** The fetched results keep the `<round>/<arm>/<input>` layout. The pipeline maps tokens back from its own record, so the scorer is unchanged.

**Residual (not fixable by any path rule).** The evaluator reads the arm's output by design. If an arm's output text identifies the program (for example a banner in `cmd1.stdout`), an agent-written `evaluate.sh` could still branch on it. The sealed `evaluate.sh` bytes make that auditable afterwards. A science step can also point the evaluator only at output files that carry no program identity.

## 2. Operator point 1: a hostile arm defeats the mode-`000` protection

**Fix.** s17's mode-`000` toggle (s17 DRAFT lines 46 and 48) is gone, and so is the static `cmp-private` name check on adapters. When the design has an evaluator, the arm part and the evaluator part run as two separate unprivileged users, set up by a trusted script (DRAFT "Separated users"):
- **What the setup does.**
  - `cmp-private` is owned by `cmp-eval` with mode `700`.
  - The shared run directory loses group and other write access, so `cmp-arm` can read the built programs and data but cannot change `evaluate.sh`, the wrapper, the evaluator program or any mode.
  - Both users join the groups that own the GPU device files.
- **What the setup checks before any invocation.**
  - Each user sees the same number of GPUs as the box user.
  - `cmp-arm` cannot read `cmp-private`.
  - If either check fails, evaluate fails with `infra`.
- **What happens after each arm part.**
  - Every `cmp-arm` process is killed until none remains, so no leftover process survives into the evaluator part.
  - `out/` is taken over by the box user.
  - A symbolic link or special file in `out/` makes the invocation `invalid`. This blocks an arm from pointing its output at private data so that the evaluator would compare private data with itself.
- **Each part's environment** is built with `env -i`: no `CMP_PRIVATE` for the arm, and a fresh `HOME` for each part. That is why the harness prompt now requires that arm programs are installed under the shared run directory or with apt, never under the home directory.
- **Precondition.** This needs passwordless sudo on the box. The probe already records it (`SCHEMAS.md:43`, `sudo_nopasswd`), so a design with an evaluator fails reproduce with `infra` right after the probe when sudo is unavailable, before any agent call or box spend.

**Why this option rather than keeping the private data off the box during the arm part.** A same-user arm could leave a process running, or edit `evaluate.sh` or a shell start-up file, and then read the data as soon as it arrives. So separate users are needed either way.

**Residual.** The draft cannot check that `setup.sh` put private files *only* under `cmp-private/`, for example rather than also in a download cache. The harness prompt requires it, but this is not enforced.

## 3. Operator point 2: isolation must keep each role's reads and writes

**Today's behaviour.**
- Intake, harness and repairs run with `cwd = A` (`pipeline.js:22`), and only the prompt tells them not to read elsewhere.
- Intake reads the brief by its own path (`pipeline.js:90`).
- Harness reads `A/intake/*` (`pipeline.js:394`).
- Repairs read intake evidence and rewrite named scripts in `A/harness/`. Protected scripts are restored afterwards (`pipeline.js:277-289`).

**Constraint from `isolation`** (`SCHEMAS.md:230`): the host is read-only, the view is the only writable host directory, and `hidden` paths are unreadable. So `directory = A` cannot work, because `A` lies under the run root, which must be hidden.

**Rule** (DRAFT "Isolation of agent calls"). It follows implement's existing pattern (`implement.js:89, 121`):
- **View.** Each call gets a fresh temporary view, holding copies of exactly what the role reads today:
  - intake: the view file and a copy of the brief;
  - harness: the view file and `intake/`;
  - repairs: the view file, `intake/` and `harness/`.
  
  The probe and the log tail stay in the prompt, as today.
- **Writable output directory.** `intake/` for intake, `harness/` for harness and repairs.
- **Copy-back** into `A/`, limited to what each role may write today:
  - intake: regular files in `intake/`;
  - harness: regular files in `harness/` and `harness/arms/<id>.sh`;
  - repairs: only the scripts that repair may rewrite.
- **`hidden`** covers:
  - the run root, which includes `A/`, `C/` and `S/`;
  - the workflow journal directory, as implement hides it;
  - the design's parent directory;
  - the design's git work tree, because a committed design is also readable from `.git` objects.
- **Other settings.** `box_access` is false. Network is unchanged: s18 found that the sandbox unshares only PID and IPC (`s18/ASSESSMENT.md:91`), so intake can still fetch sources.
- **Science step's duty.** The science step must keep no other copy of the design on the pipeline host. The pipeline cannot check this, so the draft states it as that step's responsibility, next to its existing responsibility for the view's free text.

## 4. Rules dropped because no comparison, arm or compute fact needs them

I checked each rule against FINAL.json (K1–K7, arms A0–A2, compute_facts) and SHAPES.json. Dropped:

| Dropped | Why |
|---|---|
| `commands: null` (adapter-run arms) | A0–A2 all use published commands (FINAL.json `needs_new_code: no`; `s18/ASSESSMENT.md:96`). Dropping it also removes the residual of agent-run arms. |
| Comparators `elementwise_rel`, `elementwise_abs_plus_rel` | K1/K3 use `elementwise_abs`, K2 uses `elementwise_abs_plus_rel_max`, and transform or rank fields use `exact`. |
| Criterion `equivalence`; one-sided superiority | K1–K3 are expressed as `agreement`; K6/K7 are two-sided. |
| Metric `rel` margins, and the `pooled_mean` reference mean | K4 uses `threshold`, K5 a null margin, K6/K7 `abs`. K5 is per input. |
| `missing: drop`; bootstrap of unpaired data and of a mean difference | s17 maps every comparison to `void` or `fail`. Only K4 bootstraps, and it is paired and uses a ratio of means. |
| Metric `scope` (`commands`, `invocation`) | `trusted_wall` is now always the complete invocation, plus the evaluator when there is one (K4, K5 per `s18/ASSESSMENT.md:51, 94`). |
| Reducers `last`, `min`, `mean`, `value_at_min_key` | K6/K7 need `max` and either `value_at_max_key` or `first` (`s18/ASSESSMENT.md:60, 93`). |
| Glob `order: lexical` | K1 needs natural order only. |
| `CMP_ARM`, `CMP_MODE`, `CMP_ROUND` | Adapters are per arm and only stage inputs. Leaving `CMP_ARM` out also helps keep the arm hidden. |
| Evaluate facts `comparisons_*` counts | The science step reads `comparison_scored.json`. |

**Changed:** `comparisons` may now be empty. A recording-only run can then supply walls for later references (s18 note 5) without a dummy comparison.

**Kept as written:** the per-command executable SHA-256 and `all_invocations`. s17 added them to resolve s16's compute findings.

## 5. Decisions the owner must make before a final run (OWNER.json)

1. **`margins`.** The tolerances of the agreement comparisons (K1–K3), and with them the matching term in the K6/K7 margins. Neither the seed nor a published source gives them. This is still open from `s13/ASSESSMENT.md:76-82`, with options (a) a fixture analysis, (b) a declared engineering tolerance labelled as unjustified, or (c) leaving agreement unresolved, with dependent parts gated.
2. **`evaluator_private_data`.** Whether the evaluator's private data may be fetched to and held on the box. If so, whether the pipeline may use passwordless sudo there to create the two system users `cmp-arm` and `cmp-eval`, change group membership for GPU devices, and change ownership and modes inside the shared run directory. This goes beyond today's "sudo only for apt" rule for harness scripts (`SCHEMAS.md:52`). Without this approval, a design with an evaluator cannot run, and K3, K6 and K7 cannot be decided.
3. **`spend_above_20`.** The main run projects USD 49.48 (`s13/ASSESSMENT.md:86`; `s15/ASSESSMENT.md:58`), above the USD 20 rule. The extra commands per invocation (job file, user setup) are small. Their cost is not measured.

**Not listed:**
- *Thresholds and references.* The ratio threshold and the quality margin are design values already sealed in the card. The owner may confirm them, but they do not block anything (`s13/ASSESSMENT.md:84`). Reference values come from a recording run by the card's sealed rule.
- *Run split, replicates and arms.* These are science-step design choices within the rules above.

## 6. Not yet checked
- Nothing here has been built or tested.
- An independent seed-content and sufficiency audit of this revision, like s18's, has not been run.
- Two points depend on the box image and are unverified: that `sudo -n -u <user>` works with this image's sudoers, and that GPU device access through group membership is enough. The draft checks both before any invocation and fails with `infra` otherwise.

## Predictions and next action
- s18 sealed no predictions, so `outcomes.json` is empty.
- This step runs no test, so it seals none.
- Next action: stop, `contract_gap`. The draft awaits its audit and the operator's commit to `dut/pipeline/m5/SCHEMAS.md`.
