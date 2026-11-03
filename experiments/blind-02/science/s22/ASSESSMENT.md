# s22: independent audit of `science/s21/DRAFT.md` (seed content, then sufficiency), 2026-11-03

**Scope.** I ran no test. I used no network, contacted no box, ran no git commands, read no credentials and did not edit DRAFT.md. Bash was denied, so I used only the file tools, and I wrote only into `science/s22/`. I read:
- the seed `m5/BRIEF.md:1-23`;
- `science/s13/FINAL.json` and `science/s15/SHAPES.json`;
- s14's and s16's CHECK.json, and s16's PROMPT.md and ASSESSMENT.md;
- s19's PROMPT.md (the operator's two points, lines 38-41);
- s20's AUDIT.json and ASSESSMENT.md;
- s21's PROMPT.md, DRAFT.md (lines 1-88) and ASSESSMENT.md;
- `dut/pipeline/m5/SCHEMAS.md:147-149`, which says where the box's shared run directory lies.

## 1. Seed audit: `none`

I read every line of DRAFT.md against the seed and the findings of s13-s21. I also searched it for:
- the seed's program, data and evaluator names, and its domain vocabulary (structure, pose, rank, sampling, rotation, thread, FFT, case, decoy);
- every number it contains.

**Word hits.** All of them are inside generic words or are generic uses:
- "pose" occurs only in "Purpose" (line 2) and "propose" (line 45);
- "sampl" occurs only in "resamples" (lines 14, 81) and "sampled" (line 63);
- "case" occurs once, as a generic example inside `spec` ("pins, case, configuration", line 8).

**Numbers.** Every number is one of these, and none matches a seed or finding value:
- unit identifiers (U54, U57, U58);
- the date 2026-11-03;
- gap and step labels (G1, G3, G6, s13 to s21);
- structural bounds (2-5, 1-8, 1-10, 0-10, 1-30, 0-3, 1000-1000000, 0-12, `[0.5, 1)`);
- regex bounds;
- RFC 6901;
- SHA-256;
- file modes (600, 640, 700, 711, 750);
- step numbers 1-8;
- 3600 seconds per hour;
- the utilization range `[0,100]`.

**New literals in s21.** These are all generic Unix or pipeline mechanisms: `iptables`, `ip6tables`, `find`, `rm`, System V IPC, `fetch_private.sh`, `log/`, `cmp_writable.json` and `comparison-private-remove`. The fields `value_at_max_key`, `elementwise_abs_plus_rel_max` and the private-data evaluator are generic too, as s20 found for s19 (`s20/ASSESSMENT.md:33-41`).

**Inference.** A reader learns only that some run compares published configurations on a GPU box, under sealed tolerances, with a held-out evaluator and compute accounting. That does not reveal what the seed asks or what the route found.

**Seed content: none.** As far as seed content goes, the operator may commit DRAFT.md.

## 2. Sufficiency: `partial`, missing K3-K7, one problem (`other`)

### What s21 resolves
- **s20 channel 1 (evaluator residue reaches later arms).** Resolved, apart from the defect below:
  - finished invocation directories go to mode `700` (DRAFT:63);
  - `home/` and `ehome/` are removed (61-62);
  - `comparison-work/` is at `711` (50);
  - each part user is cleaned up: its processes, its files in writable directories and its IPC objects (56).
- **s20 channel 2 (stray copies of the private data).** Resolved:
  - only `cmp-eval` fetches, through the sealed `fetch_private.sh` (36, 38, 52);
  - the data are then frozen as `root:cmp-eval` at `750`/`640` (53);
  - a size-and-hash backstop covers the shared run directory and the box user's home (54);
  - the data are removed after the run (65).
- **s20 channel 3 (the arm's identity reaches the evaluator).** Resolved: command logs go to `log/` at `700` (59-60), which the evaluator never receives. The remaining paths are declared as residual risks in the Purpose bullet (line 2): out/ content, by design, and shared hardware state. Both declarations are sound.
- **The network.** It is closed for `cmp-arm` (49, 55).
- **Operator point 1 (a hostile arm).** The rules hold against anything the arm part does: separate users, frozen private data, no write access to the shared directory, kills, the network block and the link check.
  - Scope limit (not a problem code): the claim "whatever its adapter or commands do" (56) assumes that `setup.sh` obeyed "never fetches, copies or writes the evaluator's private data" (36). The backstop (54) detects only byte-identical copies, and only in the shared run directory and the box user's home. An archive or re-encoded copy, or a copy in `/tmp`, left by a non-compliant `setup.sh` would stay readable to `cmp-arm`.
  - That threat is a hostile harness agent, not a hostile arm. `setup.sh` is kept in `A/harness/` for audit.
  - Accidental byte-identical copies fail safe, with `infra`.
- **Operator point 2 (isolation).** Met. The views are unchanged from s19, which s20 found met (`s20/ASSESSMENT.md:91-99`), at DRAFT:30-34.
- **Arms, statistics and compute.** These are unchanged from s19's draft, which s20 found expressible for A0-A2, for K1-K7 as SHAPES.json shapes them, and for every compute fact (`s20/ASSESSMENT.md:47-81`). I re-checked the scorer (75-87) and the compute record (68-74) and agree.

### The problem: the cleanup deletes the private data and every arm and evaluator output (`other`; K3-K7 missing)
**The rule.** Cleanup after a part user deletes "every entry the user owns below each directory listed for it in `profiler/cmp_writable.json` (`find <dir> -mindepth 1 -user <user> -delete`)" (DRAFT:56).

**The listing prunes the shared run directory itself (51), but not its parent.** The shared run directory is a fresh `/tmp/m5-<uuid>` (`SCHEMAS.md:149`). `/tmp` is writable by every user, so it is listed for both part users. The cleanup's `find /tmp -mindepth 1 -user <user> -delete` therefore descends into the shared run directory. Nothing excludes it, and `-delete` implies `-depth`, so a `-prune` added to the same command would also have no effect.

**What is deleted, in order:**
1. **Users step 5 (52).** The cleanup after `fetch_private.sh` deletes `cmp-private` and everything just fetched into it, because all of it is still owned by `cmp-eval`. Step 6 (53) only re-owns afterwards. The directory is reachable even to a non-root `find`, because step 3 makes the shared run directory searchable and listable to other users (50). Every evaluation then fails.
2. **Wrapper step 2 (61).** The cleanup after `cmp-arm` runs before `run/` and `out/` are re-owned. So, with the cleanup run as root (as `pkill -u` of another user requires), it deletes the invocation's `out/`, `run/` and `home/`, all owned by `cmp-arm`. The same holds for `eval/` and `ehome/` in wrapper step 3 (62).

**Consequence.** In any design with an evaluator, which is the only case with separated users:
- every output, every `out`/`eval` extraction and every evaluator wall is missing;
- K3 (evaluator output), K6 and K7 (extracted from evaluator files) cannot be decided;
- K4 and K5 cannot be decided either: their walls must include the evaluator (11, 67), which is null unless `eval_status` is `ok`.

K1 and K2 remain decidable in a separate design without an evaluator, which has no part users and no cleanup. The arms stay runnable.

**Smallest fix (one clause).** In the cleanup (56), delete only entries outside the shared run directory, for example `find <dir> -mindepth 1 -user <user> ! -path '<shared run directory>' ! -path '<shared run directory>/*' -delete`. Entries inside the shared run directory are already handled by the explicit rules for invocation directories and `cmp-private`. Under step 3, a part user can write nowhere else there.

### Builder notes (not problem codes)
- Step 3 grants other users read on files and search on directories (50), but not execute. An installed executable without `o+x`, for example under a restrictive umask, would not run as `cmp-arm`. `chmod -R o+rX` semantics would be safer.
- Still unverified (from s20 and s21): hiding the git work tree may hide a provider CLI installed inside the repository. Whether the box image supports `iptables`/`ip6tables` owner matching, `sudo -n -u` and GPU access through groups is checked before any invocation.

## For the owner
- **Seed content:** none.
- **Sufficiency:** `partial`. One clause, added at DRAFT:56, fixes it; without it, designs with an evaluator cannot decide K3-K7. Every finding of s18 and s20, and both operator points, is otherwise resolved or soundly declared as residual.
- **Still open from s21's OWNER.json:** margins, approval of the evaluator's private data and sudo use, and spend above USD 20.
- s21 sealed no predictions, so `outcomes.json` is empty. This step runs no test.
- **Next action:** stop, `contract_gap`.
