# s21 assessment: second revision of the seed-neutral "Sealed comparison (U57, U58)" draft (2026-11-03)

**Scope.** I ran no test. I used no network, contacted no box, ran no git commands and read no credentials. Bash was denied, so I used only the file tools and wrote only into `science/s21/`. I read `s17/PROMPT.md` (the seed-neutrality rules), `s19/` (DRAFT.md, ASSESSMENT.md, OWNER.json, NARROWING.md, the operator's two points in PROMPT.md:38-39), `s20/` (AUDIT.json, ASSESSMENT.md, PROMPT.md), `s13/ASSESSMENT.md:70-89`, and `dut/pipeline/m5/SCHEMAS.md` where it mentions sudo and the shared run directory (lines 43, 52, 62, 75, 109, 128).

`DRAFT.md` is one section, starting with `## Sealed comparison (U57, U58)`. It replaces s19's draft and keeps every rule of s19 that s20 found right: the design format, sealing, the isolation views, the scorer and the compute record are unchanged word for word, except for the edits listed below. s17's seed-neutrality rules still hold. The only new literals are generic:
- the operation names `comparison-private-remove`;
- the file name `fetch_private.sh` and the directory names `log/` and `profiler/cmp_writable.json`;
- the modes `640` and `750`;
- the system tools `iptables`, `ip6tables`, `find`, `rm`, and System V IPC.

The draft names no program, case, input, file or output of the seed, and uses no number from the seed, its materials or the route's findings.

## 1. s20's finding `leaks_or_biases`: three derived channels (`s20/ASSESSMENT.md:115-128`)

### Channel 1: evaluator residue reaches later arm parts
s20 found two paths:
- earlier invocations' `eval/` and `ehome/` stayed readable through `711` directories with predictable tokens;
- files that `cmp-eval` left in `/tmp`, `/var/tmp` or `/dev/shm` persisted.

**Fix (contract rule):**
- **Finished invocations are closed.** Step 4 of the wrapper (DRAFT:63) sets each finished invocation directory to mode `700`, owned by the box user. No later part, of either user, can then read any earlier invocation's files. This also stops arms from reading each other's outputs.
- **Homes are removed.** `home/` is removed after the arm part and `ehome/` after the evaluator part (DRAFT:61-62). `run/` goes to mode `700` (DRAFT:61).
- **A defined cleanup per part user** (DRAFT:56):
  - Before any invocation, `cmp_users.sh` lists, for each user, every directory outside the shared run directory that the user can write (step 4, DRAFT:51).
  - After each part, the wrapper kills the user's processes, deletes every entry that user owns below those directories, and removes the user's System V IPC objects.
  - This removes `/tmp`, `/var/tmp` and `/dev/shm` residue whatever paths the evaluator chose. It is symmetric: an arm cannot plant files there for the evaluator either.
- **`comparison-work/` gets a mode.** It is created at mode `711`. s20 noted that its mode was unspecified.

### Channel 2: stray copies of the private data stay readable to the arm
Under s19, `setup.sh` fetched the private data as the box user. The users script then granted read access to everything except `cmp-private` (s19 DRAFT:36, 47).

**Fix (contract rule; it depends on the owner decision below):**
- **Only the evaluator's user fetches.** `setup.sh` may no longer fetch, copy or write the private data (DRAFT:36). A new sealed script `harness/fetch_private.sh` does it (DRAFT:38, 43):
  - `cmp_users.sh` runs it as `cmp-eval`, inside `cmp-private`, with `HOME` and `TMPDIR` inside `cmp-private` (step 5, DRAFT:52), and then cleans up after `cmp-eval`.
  - `cmp-eval` can write nowhere in the shared run directory except `cmp-private`, and the cleanup removes anything it wrote in `/tmp`-like directories. So downloads, archives and caches of the private data cannot land anywhere `cmp-arm` reads.
- **Then frozen.** `cmp-private` becomes owned by `root`, with group `cmp-eval` and modes `750`/`640` (step 6, DRAFT:53). The evaluator can read the data but cannot change it. This also blocks the evaluator from keeping memory across invocations there.
- **Backstop check.** If a file with the size and SHA-256 of a private file exists anywhere in the shared run directory outside `cmp-private`, or under the box user's home, evaluate fails with `infra` (step 7, DRAFT:54). This enforces what s19 left unenforced (`s19/ASSESSMENT.md:52`).
  - Unlike s20's suggestion (b), the hashes are computed by the trusted script from `cmp-private` itself. So intake does not need to know them before the data are downloaded.
- **Removed after the run.** After the last invocation, `cmp-private` is deleted (DRAFT:65).

**Added because the hostile-arm requirement (operator point 1, `s19/PROMPT.md:39`) covers it:**
- **The network.** A hostile arm could fetch the private data from where it is published. Step 2 (DRAFT:49) rejects every non-loopback packet of `cmp-arm`, and step 8 (DRAFT:55) checks that the rules are in place.
- **Consequence.** Arms must therefore run offline. That is already implied, since `setup.sh` installs everything before the run. An arm that does need the network fails, and its values are missing, which the scorer reports.

### Channel 3: the arm's identity reaches the evaluator through command logs in `out/`
**Fix (contract rule):**
- **Logs move to `log/`.** The wrapper writes the adapter's and every command's standard output and error into `log/`, at mode `700` and owned by the box user (DRAFT:59-60), not into `out/`. The evaluator receives only `out/`, so it no longer sees banners or the number of commands.
- **`log/` is still usable.** It is fetched (DRAFT:64), and `log` is an allowed first component for `cmp_files.json` and `cmp_extract.json` locations (DRAFT:39-40). An arm whose result is printed to standard output can still be compared and extracted, but not evaluated.

### Residual risks no rule removes (declared in the Purpose bullet, DRAFT:2)
1. **The evaluator reads the arm's output files by design.** File names or content under `out/` that identify the program can still reach it. The sealed `evaluate.sh` bytes make any dependence on them auditable after the run.
2. **Shared hardware state is not cleared between parts.** This covers device memory, caches and timing.

### What this means for `leak_fix`
- Every file, path, process, network and IPC channel s20 named is closed by a rule.
- The closing rules for channel 2 assume my recommended option for the evaluator's private data: fetched onto the box only by the evaluator's user, held read-only, and removed after the run. They also assume that the pipeline may use passwordless sudo for this.
- Because the owner must choose that option, `leak_fix` is `needs_owner_decision`.

## 2. s20's builder notes (no problem code; handled where cheap)
- **GPU device groups.** Users are added only to groups that own a `/dev/nvidia*` file whose permission bits for other users lack read or write (DRAFT:48), as s20 suggested.
- **`comparison-work/` mode:** now specified (DRAFT:50).
- **Not changed and still unverified: hiding the design's git work tree** may also hide the provider CLI if it is installed inside the repository (`s20/ASSESSMENT.md:101`). This is a build check, not a contract rule.

## 3. Decisions the owner must make before a final run (OWNER.json)
1. **`margins`.** The tolerances of the agreement comparisons (K1-K3), and with them the matching term in the K6/K7 margins. Neither the seed nor a published source gives them. The options are unchanged from `s13/ASSESSMENT.md:76-82`:
   - (a) a fixture analysis;
   - (b) a declared engineering tolerance, labelled as unjustified;
   - (c) leaving agreement unresolved, with the dependent parts gated.
2. **`evaluator_private_data`.** Whether the evaluator's private data may be fetched to and held on the box.
   - **My recommendation, which the draft encodes:** yes, under these conditions:
     - the data are fetched only by `fetch_private.sh` running as `cmp-eval`;
     - they are held only under `cmp-private`, read-only to `cmp-eval` and unreadable to everyone else except root;
     - they are removed after the last invocation.
   - **What this needs:** approval for the pipeline's trusted scripts to use passwordless sudo on the box, beyond today's "sudo only for apt" rule for harness scripts (`SCHEMAS.md:52`). With it, the scripts will:
     - create two system users;
     - change GPU device group membership;
     - change ownership and modes inside the shared run directory;
     - add `iptables`/`ip6tables` output rules for `cmp-arm`;
     - delete the part users' files outside the shared run directory.
   - **The alternative:** no private data on the box. A design must then have `evaluator: null`, and K3, K6 and K7 cannot be decided on this route.
3. **`spend_above_20`.** The main run projects USD 49.48 (`s13/ASSESSMENT.md:86`), above the USD 20 rule.
   - The cleanup and fetch steps add box time per invocation that has not been measured. The writable-directory listing is done once. The per-part `find ... -user ... -delete` covers only the listed directories.

**Not listed:**
- Thresholds and references are design values already sealed in the card, or derived from a recording run (`s13/ASSESSMENT.md:84`).
- Arm selection, run split and replicates remain science-step design choices.

## 4. Not yet checked
- Nothing has been built or tested.
- These points depend on the box image:
  - that `iptables`/`ip6tables` with the owner match are available;
  - that `sudo -n -u` works;
  - that group membership is enough for GPU access.

  Each is checked before any invocation, and a failure is `infra`. If `iptables` is missing, a design with an evaluator cannot run on that image.
- An independent audit of this revision for seed content and sufficiency, like s18 and s20, has not been run. The operator should not commit DRAFT.md before one.

## Predictions and next action
- s20 sealed no predictions, so `outcomes.json` is empty.
- This step runs no test and seals no predictions.
- Next action: stop, `contract_gap`. The draft awaits its audit and the operator's commit to `dut/pipeline/m5/SCHEMAS.md`.
