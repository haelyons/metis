# s23 assessment: third revision of the seed-neutral "Sealed comparison (U57, U58)" draft (2026-11-03)

**Scope.** I ran no test, used no network, contacted no box, ran no git commands and read no credentials. Bash was denied, so I used only the file tools and wrote only into `science/s23/`.

I read:
- `s17/PROMPT.md:40-43`, the seed-neutrality rules;
- `s20/ASSESSMENT.md`;
- `s21/` (DRAFT.md, ASSESSMENT.md, OWNER.json, NARROWING.md);
- `s22/` (AUDIT.json, ASSESSMENT.md).

Earlier steps reach me through those files' citations of them.

`DRAFT.md` is one section, starting with `## Sealed comparison (U57, U58)`. It replaces s21's draft and changes only four places: the Purpose bullet, and steps 3, 7 and the cleanup paragraph under Separated users. Every other line is s21's text, word for word. That keeps everything s18, s20 and s22 found right:
- the arm-identity fixes (the `i<k>` tokens, job files, `log/`);
- the three channels s20 found, which s21 closed;
- the isolation views;
- the scorer;
- the compute record.

## 1. s22's problem `other`: the cleanup deleted the private data and every output (K3-K7 missing)

**Finding** (`s22/ASSESSMENT.md:64-80`). The shared run directory lies under `/tmp`, which every user can write. So `/tmp` is listed for both part users in `cmp_writable.json`. The cleanup's `find /tmp -mindepth 1 -user <user> -delete` then went down into the shared run directory and deleted three things:
- `cmp-private` after the fetch (users step 5);
- `out/`, `run/` and `home/` after each arm part, before they were re-owned;
- `eval/` and `ehome/` after each evaluator part.

In any design with an evaluator, this left K3-K7 undecidable.

**Fix (a contract rule; DRAFT, cleanup paragraph after users step 8).**
- **What is excluded.** Cleanup "never deletes or changes anything in the shared run directory". Entries there are handled only by the explicit rules for `cmp-private` (steps 5-6) and for invocation directories (wrapper steps 2-4).
- **The command.** It is now `find <dir> -mindepth 1 -user <user> ! -path <S> ! -path <S>/* -delete`, with `<S>` the shared run directory's absolute path. The rule also says:
  - glob metacharacters in `<S>` are escaped;
  - each pattern is passed as one argument;
  - why `-path` exclusion is used rather than `-prune`: `-delete` implies `-depth`, which voids `-prune` (s22's point).
- **Nested directories.** Only listed directories that are not below another listed directory are swept. This avoids deleting the same entry twice.
- **How it runs.** Cleanup runs with `sudo -n`, which s21 left implicit.

**Why nothing else needs changing.** Users step 3 gives the part users no write access anywhere in the shared run directory except two places:
- their own invocation subdirectories, which wrapper steps 2-3 re-own to the box user and step 4 closes at `700`;
- `cmp-private`, which step 6 freezes as `root:cmp-eval`.

So excluding the shared run directory leaves no residue a later part can read. Outside it, the sweep is unchanged, so s20's channel-1 fix still holds: residue in `/tmp`, `/var/tmp` and `/dev/shm` is removed whatever paths a part chose.

**Effect on K1-K7** (as s20 and s22 checked them against `s15/SHAPES.json`):
- `cmp-private`, `out/` and `eval/` now survive.
- `eval_status` can be `ok`, so the evaluator's wall feeds `trusted_wall`.
- K3, K6 and K7 (evaluator output and extraction) and K4 and K5 (walls that include the evaluator) are decidable again.
- K1 and K2 were unaffected.

## 2. s22's builder note: files that should stay executable
Users step 3 granted other users read access on files but no execute access. An installed executable without the other-users execute bit would then not run as `cmp-arm`. Step 3 now has the effect of `chmod -R go-w,o+rX`: other users get execute access on any file that already has an execute bit. Write protection is unchanged.

## 3. s22's scope limit: a harness script that disobeys the private-data rule
The byte-identity backstop (step 7) checked only the shared run directory and the box user's home (`s22/ASSESSMENT.md:58-60`). A non-compliant `setup.sh` could leave a copy in `/tmp`, or a transformed copy anywhere.
- **Closed by a rule (byte-identical copies).** Step 7 now also checks every directory listed for `cmp-arm` in `cmp_writable.json`, which includes `/tmp`. It excludes `cmp-private`, which lies in the shared run directory under `/tmp`. A byte-identical copy anywhere the arm part can write therefore fails safe with `infra`.
- **Declared residual (transformed copies).** An archive, a re-encoding or a derived file has different bytes. No deterministic rule can recognise it as derived from the private data. It is now the third declared residual risk in the Purpose bullet. The risk is auditable: `setup.sh` and its repairs are kept in `A/harness/` and in the stage's receipts.
- **Why `setup.sh` is not sealed.** Setup repair may rewrite `setup.sh`, so sealing it would conflict with "No repair changes them".

## 4. Seed neutrality (s17's rules)
The new literals are all generic:
- `find` flags (`-path`, `-mindepth`, `-delete`, `-depth`, `-prune`);
- `chmod -R go-w,o+rX`;
- the placeholder `<S>`;
- the step label s23.

The draft adds no number, and it names no program, library, model, dataset, case, input, file, path or output of the seed. It quotes no seed text, and none of its numbers come from the seed or the route's findings. An independent audit, like s18, s20 and s22, has not been run on this revision. The operator should not commit DRAFT.md before one.

## 5. `leak_fix`: `needs_owner_decision`
- **s22's problem** is fixed by a contract rule.
- **s20's channels** stay closed by rules. One of those rules, closing channel 2, encodes my recommended private-data option: only `cmp-eval` fetches, the data are held read-only and removed after the run, and the pipeline uses passwordless sudo. The owner must still choose that option.
- **What no rule removes** is declared in the Purpose bullet: the evaluator reading `out/` by design, shared hardware state, and transformed copies left by a non-compliant harness script.

## 6. Decisions the owner must make before a final run (OWNER.json)
1. **`margins`.** The tolerances of the agreement comparisons (K1-K3), and with them the matching term in the K6/K7 margins. Neither the question nor a published source gives them. The options are unchanged from `s13/ASSESSMENT.md:76-82`, as listed at `s21/ASSESSMENT.md:65-68`:
   - (a) a fixture analysis;
   - (b) a declared engineering tolerance, labelled as unjustified;
   - (c) agreement left unresolved, with the dependent parts gated.
2. **`evaluator_private_data`.** Whether the evaluator's private data may be fetched to and held on the box.
   - **My recommendation, which the draft encodes:** yes. The data are fetched only by the sealed `fetch_private.sh` running as `cmp-eval`. They are held only under `cmp-private`, read-only to `cmp-eval`. They are removed after the last invocation.
   - **What this needs:** approval for the pipeline's trusted scripts to use passwordless sudo on the box, beyond the harness rule "sudo only for apt". With it, the scripts will:
     - create two system users;
     - change GPU device groups;
     - change ownership and modes in the shared run directory;
     - add `iptables`/`ip6tables` output rules;
     - delete the part users' files outside the shared run directory.
   - **The alternative:** no private data on the box. Every design then has `evaluator: null`, and K3, K6 and K7 cannot be decided on this route.
3. **`spend_above_20`.** The main run projects USD 49.48 (`s13/ASSESSMENT.md:86`, cited at `s21/ASSESSMENT.md:81`), above the USD 20 rule. The added sweeps and the wider step-7 hash scan add box time that has not been measured.

**Not listed:**
- Thresholds and references are sealed design values from the card, or are derived from a recording run.
- Arm selection, run splits and replicates remain science-step design choices (`s21/ASSESSMENT.md:84-86`).

## 7. Not yet checked
- Nothing has been built or tested.
- Three things depend on the box image. Each is checked before any invocation, and a failure is `infra`:
  - `iptables`/`ip6tables` owner matching;
  - `sudo -n -u`;
  - GPU access through group membership.
- Builder note carried over from s20 and s22: hiding the design's git work tree may also hide a provider CLI that is installed inside the repository.

## Predictions and next action
- s22 sealed no predictions, so `outcomes.json` is empty.
- This step runs no test and seals no predictions.
- Next action: stop, `contract_gap`. The draft awaits an independent audit and then the operator's commit to `dut/pipeline/m5/SCHEMAS.md`.
