# s20: independent audit of `science/s19/DRAFT.md` (seed content, then sufficiency), 2026-11-03

**Scope.** I ran no test. I used no network, contacted no box, ran no git commands, read no credentials and did not edit DRAFT.md. Bash was denied, so I used only the file tools, and I wrote only into `science/s20/`. I read:
- the seed `m5/BRIEF.md:1-23`, and `m5/b01_materials/BRIEF_run1.md`, which I searched for local file references (it has none, only URLs);
- the physical card's plan `20261103-0124-tree/out/work/seed-20261103/R1/physical/1fffee1a/producer.md` ("PC"), lines 18-113;
- `science/s13/FINAL.json` and `science/s15/SHAPES.json`;
- s14's CHECK.json, and s16's PROMPT.md, CHECK.json and ASSESSMENT.md;
- `science/s18/` (AUDIT.json, ASSESSMENT.md) and `science/s19/` (PROMPT.md, DRAFT.md lines 1-78, ASSESSMENT.md);
- `dut/pipeline/m5/SCHEMAS.md:226-231` (wf `isolation`, implement views) and `dut/pipeline/m5/pipeline.js:261-299` (the reproduce repairs and the restore of protected scripts).

## 1. Seed audit: `none`

I read every line of DRAFT.md against the seed, the card and the findings of s13-s19. I also searched it for:
- the seed's program, data, evaluator and library names, the case identifiers, and domain words (the structure, pose, rank, sampling, grid and thread vocabulary);
- every number in the draft.

The only hits were inside generic words: "pose" in "Purpose" (line 2) and "propose" (line 45), and "eps" in "steps" (line 2). Every number is one of the following, and none matches a seed, card or finding value:
- a unit identifier (U54, U57, U58);
- the route date 2026-11-03;
- a step number (s13-s19);
- a structural bound (2-5 arms, 1-8 commands, 1-10 inputs, 0-10 outputs, 1-30 replicates, 0-3 warmups, 1000-1000000 resamples, 0-12 comparisons, `[0.5, 1)`);
- a regex bound;
- RFC 6901;
- SHA-256;
- the file modes 600, 700 and 711;
- 3600 as seconds per hour (line 59);
- the utilization range `[0,100]` (line 54).

The bootstrap resample count of the card is still a design field (`bootstrap_resamples`, line 14), not a literal.

I checked these items one by one and rejected each:

| Item (DRAFT.md line) | Why it is not seed content |
|---|---|
| `cmp-arm`, `cmp-eval`, `sudo`, `pkill`, `pgrep`, `env -i`, `/dev/nvidia*` (47, 50, 52) | Generic Unix mechanisms. m5 is a general GPU pipeline, and `nvidia-smi` and GPU-busy sampling are already in m5 (`SCHEMAS.md:38, 334-335`). |
| `lscpu`, `uname`, `ldd`, `nvidia-smi --query-gpu` (48) | Generic system tools. |
| Private-data evaluator (13, 38, 53) | The generic held-out evaluation pattern. It names no domain, data or metric. |
| `value_at_max_key`, `max`, `first`, `expect_count` (12, 40, 57) | Generic reducers. |
| `elementwise_abs_plus_rel_max` (18, 67) | The generic symmetric closeness test. |
| Gap labels G1, G3 and G6, and "science steps s13 to s19" (2) | Route and contract identifiers. The blind operator already wrote them (`s16/PROMPT.md:43`). |
| The job file, opaque tokens `i<k>`, the isolation views (29-34, 49-50) | Generic sandboxing. |

No line names a program, library, model, dataset, case, input, file or output of the seed. No line quotes the seed or carries one of its numbers, margins, tolerances or references. The text tells a reader only that some run compares published configurations under sealed tolerances, with a private evaluator and compute accounting. That does not reveal what the seed asks or what the route found. **Seed content: none.** As far as seed content is concerned, the operator may commit DRAFT.md.

## 2. Sufficiency: `partial` (one problem, no missing item)

### Arms and comparisons: all expressible and decidable

- **Arms A0-A2.** Each is a sealed `commands`/`env` argument vector of published programs, run by the trusted wrapper (lines 5-6, 51). The adapters only stage inputs (37). A0's thread and affinity settings fit in `env` or in a published launcher argv. A0 still passes through intake and reproduce as usual (4, 45). **Runnable.**
- **K1** (needs `cross_arm_outputs`, `elementwise_abs`, `per_input_all`, `paired_replicate`, `all_pairs`):
  - Per-field `select` outputs (9) split the transform and rank fields (`exact`) from the score fields.
  - A `{glob}` location in natural order (39, 66) reads the many per-item files.
  - A length mismatch disagrees (67), so a cutoff mismatch fails.
- **K2** (needs `abs_plus_rel` with a per-element symmetric base): `elementwise_abs_plus_rel_max`, `abs_tol + rel_tol * max(|a|,|b|)` (67), which is exactly PC:58.
- **K3:** the evaluator's per-item output, through `eval` locations (39), compared with `elementwise_abs`.
- **K1-K3, common rules:**
  - Agreement needs at least one compared pair and no missing side (73).
  - A missing side makes the pair missing (66).
  - `missing` set to `void` or `fail` blocks a vacuous "supported" (69).
- **K4** (needs `trusted_wall`, `pooled_mean`, `paired_replicate`, `bootstrap`, ratio of means):
  - `trusted_wall` is the adapter plus the commands plus the evaluator (11, 57). That is the complete-workflow scope of PC:68.
  - `ratio_at_least` with `lower_better` gives mean(A0)/mean(A1) (68).
  - The bootstrap resamples replicate rounds jointly across inputs, with a design-set `B` and confidence (71), as PC:30 requires.
  - `strict: true` gives "> threshold" (24, 73).
- **K5** (needs `per_input_each`, `unpaired`, `all_pairs`, a previous-run reference):
  - Non-inferiority, `lower_better`, with a null margin, is supported iff every replicate is at or below the tier value (73).
  - `missing: fail` turns a timeout into not supported (69), as PC:107 requires.
  - `timeout_s` can be set per arm and input (15).
  - Use one comparison per tier.
- **K6/K7** (need `sealed_extraction`, `per_input_each`, `unpaired`, `all_pairs`, abs margin):
  - Two-sided superiority with `sign` (73-74). Under `unpaired` + `all_pairs`, lo = min(A2) − max(A1) and hi = max(A2) − min(A1), which is PC:29's gain/loss rule.
  - `reduce: max` with `expect_count` gives best-of-all; `value_at_max_key` or `first` gives the top-ranked item (12, 57).
  - `given` points to the tier rows (27, 70), and `missing: void` means "unavailable comparison" (PC:29).
  - The comparison budget holds: K4, three K5 tiers and K6/K7 at three tiers make 10, within the cap of 12 (16).
- **Gating K4-K7 on K1-K3:** separate designs, with launch conditioned on the earlier `C/comparison_scored.json` (2).
- **compute_facts:**
  - per-arm wall and GPU-busy seconds, with the evaluator kept separate (54, 60);
  - hardware identity: CPU model, GPU name, UUID and memory, driver, CUDA, kernel, and executable and library hashes (48);
  - the bill, kept separate from attribution, with `final` marking an estimate (59, 63). All are recorded.

So `missing` is empty.

### s18's finding (the arm name was visible to the evaluator): fixed on paths, environment and argv

- Invocations are named by the token `i<k>` (49).
- The arm is recorded only in a job file at mode `600` in a directory at mode `700` (50).
- The evaluator runs from the shared run directory, as `cmp-eval`, after every `cmp-arm` process has been killed (52-53).

No path, argv or environment variable that the evaluator can read names the arm.

### Operator point 2 (isolation keeps each role's reads and writes): met

- Each call gets a fresh temporary view holding copies of what the role reads today (31-33):
  - intake: the view file and the brief;
  - harness: also `intake/`;
  - repairs: also `harness/`.
- The writable output is copied back only for the files each role writes today. This matches the restore of protected scripts at `pipeline.js:276-290`.
- That is the existing `isolation` setting (`SCHEMAS.md:230`), with an explicit `directory`, `hidden` and `box_access: false`.
- The run brief has no local file references, so a copy of the brief is enough.

**Builder note.** Hiding the design's git work tree hides the whole repository, including `dut/`. That is harmless only if the provider CLI and its runtime are not installed inside it. This is unverified.

### Operator point 1 (a hostile arm against the private data): direct reading closed, derived channels open → `leaks_or_biases`

**What the fix closes.**
- Separate users, with `cmp-private` owned by `cmp-eval` at mode `700`.
- No write access for the arm to the shared run directory.
- Processes killed after the arm part.
- No links allowed in `out/`.
- The `env -i` environments.
- The pre-invocation checks (47, 50-52).

Together these close the same-user `chmod` attack that the operator described.

**Remaining channels.** Three remain, and the contract states them nowhere:
1. **Evaluator residue reaches later arm parts.**
   - After the evaluator part, `eval/` is only re-owned by the box user, and its modes are unspecified (53). `ehome/` is never restricted.
   - Invocation directories are `711` with predictable tokens (49-50).
   - So a later invocation's arm part, as `cmp-arm`, can read `../../i<j>/eval/` and `ehome/` of every earlier invocation. Those hold the evaluator's results and any caches it wrote, all derived from the private data.
   - Likewise, files that `cmp-eval` leaves in the box's shared `/tmp`, `/var/tmp` or `/dev/shm` persist, because only processes are killed.
   - That is native-derived information reaching an arm, which the seed forbids ("reference structures only for evaluation"), and which the operator asked to be excluded against a hostile arm.
2. **Stray copies of the private data stay readable to the arm.**
   - After setup, the users script grants other users read access to every file in the shared run directory except `cmp-private` (47).
   - Any download, extraction or cache copy of the private data that `setup.sh` left elsewhere therefore becomes readable to `cmp-arm`.
   - s19 disclosed this as unenforced (`s19/ASSESSMENT.md:52`). It can be enforced.
3. **The arm's identity reaches the evaluator through `out/`.**
   - The wrapper itself writes each command's stdout and stderr into `out/cmd<k>.*` (51), and `CMP_ARM_OUT` hands the whole `out/` to the evaluator (53).
   - Program banners and the number of command files identify the arm. That reopens part of s18's finding through files the pipeline chose to place there, not through the arm's scientific output.

**Smallest fix (additions only).**
- **(a)** After the evaluator part, set the invocation's `eval/` (and its whole directory) to box-user-only access, remove `ehome/`, give each part a private `TMPDIR` under its home, and, after each part, delete every file the part user owns outside the invocation directory.
- **(b)** In `data.json`, record the SHA-256 of each private file. Before any invocation, `cmp_users.sh` fails with `infra` if a file with one of those hashes exists outside `cmp-private` in the shared run directory or the box user's home.
- **(c)** Write command logs to a `log/` directory beside `out/`. It is fetched, but the evaluator does not receive it, unless an output maps them.

**Builder notes.** These are not problem codes.
- "Every group that owns a `/dev/nvidia*` file" (47) is usually `root` on stock drivers, because the devices are world-accessible. Only add a group when the device's other-permission bits lack read/write.
- The mode of `comparison-work/` itself is unspecified.

## For the owner
- **Seed content:** none. The operator may commit DRAFT.md as far as seed content is concerned.
- **Sufficiency:** `partial`. Every arm, every comparison K1-K7 and every compute fact can be expressed and decided as SHAPES.json shapes them. s18's finding and operator point 2 are resolved.
- **Operator point 1** is resolved for direct reads. Three channels remain, closed by fixes (a)-(c) above.
- **Still open from s19's OWNER.json:** margins, approval of private data and sudo use, and spend above USD 20.
- s19 sealed no predictions, so `outcomes.json` is empty. This step runs no test.
- **Next action:** stop, `contract_gap`.
