# s24: independent audit of `science/s23/DRAFT.md` (seed content, then sufficiency), 2026-11-03

**Scope.** I ran no test. I used no network, contacted no box, ran no git commands, read no credentials and did not edit DRAFT.md. Bash was denied, so I used only the file tools, and I wrote only into `science/s24/`. I read:
- the seed `m5/BRIEF.md:1-23`;
- `science/s13/FINAL.json` and `science/s15/SHAPES.json`;
- s16's PROMPT.md (the CHECK.json definitions, lines 90-93) and CHECK.json; s18's and s20's AUDIT.json; s20's and s22's ASSESSMENT.md; s22's AUDIT.json;
- s19's PROMPT.md (the operator's two points, lines 38-41);
- s21's DRAFT.md (lines 46-57, to diff the changed paragraph);
- s23's DRAFT.md (lines 1-88) and ASSESSMENT.md.

## 1. Seed audit: `none`

I read every line of DRAFT.md against the seed and the route's findings, and searched it for the seed's program, data and evaluator names and its domain vocabulary, and for every number.

**Word hits**, all generic:
- "pose" only inside "Purpose" (line 2) and "propose" (line 45);
- "sampl" only inside "resamples" (14, 81) and "sampled" (63);
- "case" once, as a generic example of what a `spec` may hold (8);
- "top" only in "top-level" (30, 59);
- "refer" only in the contract's own `reference` field and in "referenced" mechanisms (16, 17, 25, 29, 78).

**Numbers.** Every number is a unit id (U54, U57, U58), the date 2026-11-03, the experiment label blind-02, gap labels G1/G3/G6, step labels s13 to s23, a structural bound (2-5, 1-8, 1-10, 0-10, 1-30, 0-3, 1000-1000000, 0-12, `[0.5, 1)`), a regex bound, RFC 6901, SHA-256, a file mode (600, 640, 700, 711, 750), a step number 1-8, 3600 seconds per hour, or the utilization range `[0,100]`. None is a value from the seed, its materials or the findings.

**s23's new literals** (`find` flags `-path`, `-mindepth`, `-delete`, `-depth`, `-prune`; `chmod -R go-w,o+rX`; the placeholder `<S>`; "an archive, a re-encoding, a derived file") are generic Unix mechanisms and generic wording.

**Inference.** A reader learns only that some run compares published configurations on a GPU box under sealed tolerances, with a held-out evaluator and compute accounting. That does not reveal what the seed asks or what the route found.

**Seed content: none.** As far as seed content goes, the operator may commit DRAFT.md.

## 2. Sufficiency: `sufficient`, nothing missing, no problem

### What changed from s21 (checked by diff)
Only the Purpose bullet (line 2), users step 3 (50), step 7 (54) and the cleanup paragraph (56) differ from s21's text. Everything else is s21's text word for word, which s22 found correct apart from the cleanup defect. s20 and s22 had already checked it against every arm, every comparison K1-K7 as SHAPES.json shapes them, and every compute fact. I re-checked the scorer (75-87) and the compute record (68-74) against FINAL.json and SHAPES.json and agree with them.

### s22's problem (`other`; K3-K7 missing): resolved
- **The rule.** Cleanup now "never deletes or changes anything in the shared run directory" and runs `find <dir> -mindepth 1 -user <user> ! -path <S> ! -path <S>/* -delete`, with metacharacters in `<S>` escaped and each pattern passed as one argument (56).
- **Why it works.** `-delete` implies `-depth`, but `find` still tests every entry. Every entry inside the shared run directory fails `! -path <S>/*`, and the directory itself fails `! -path <S>`, so nothing there is deleted. The draft states this reason correctly (56). Entries outside it that the part user owns are still deleted, so s20's channel-1 fix (residue in `/tmp`, `/var/tmp`, `/dev/shm`) still holds.
- **What survives now:**
  - `cmp-private` after the fetch (step 5): it is inside the shared run directory, so the sweep leaves it, and step 6 then freezes it;
  - `out/`, `run/` after the arm part (wrapper step 2): wrapper step 2 re-owns them;
  - `eval/` after the evaluator part (wrapper step 3).
- **Residue inside the shared run directory.** None reaches a later part. After step 3, a part user can write there only in its own invocation subdirectories, which wrapper steps 2-4 re-own and close at `700`. `home/` and `ehome/` are removed explicitly (61, 62), and `cmp-private/.home` is removed after the fetch (52).
- **Effect on the comparisons.** `eval_status` can be `ok` again, so:
  - K3 (evaluator output, `eval` locations, `elementwise_abs`) is decidable;
  - K6/K7 (`sealed_extraction` from evaluator files) are decidable;
  - K4/K5 (`trusted_wall` including the evaluator's wall, 11, 67) are decidable.
  
  K1/K2 were unaffected. So `missing` is empty.

### s22's builder note (execute bits): resolved
Step 3 now has the effect of `chmod -R go-w,o+rX` (50). Installed executables with any execute bit stay runnable as `cmp-arm`, and write protection is unchanged.

### s22's scope limit (a non-compliant `setup.sh`): resolved, part by rule, part as a declared residual
- **By rule.** Step 7 (54) now checks byte-identical copies also below every directory listed for `cmp-arm` in `cmp_writable.json`, which covers `/tmp` and the other shared writable directories. A byte-identical copy anywhere the arm part can write therefore fails safe with `infra` before any invocation.
- **Declared residual.** Transformed copies (archive, re-encoding, derived file) are declared as the third residual risk in the Purpose bullet (2). No deterministic rule can recognise a derived file. The declaration is sound: `setup.sh` and its repairs are kept in `A/harness/` and the receipts, so the risk can be audited. The draft also explains why `setup.sh` cannot be sealed (setup repair may rewrite it; `s23/ASSESSMENT.md:57`). Under this step's brief, a soundly declared residual counts as resolved.

### Operator point 1 (a hostile arm): met
- separate users;
- private data frozen as `root:cmp-eval` `750`/`640` (53);
- no group or other write access in the shared run directory (50);
- the network closed for `cmp-arm` (49, 55);
- process kills, file sweeps outside the shared run directory, and IPC removal (56);
- the link and type check on `out/` (61);
- finished invocations closed at `700` (63);
- command logs kept away from the evaluator (59-60);
- the byte-identity backstop (54).

The remaining paths are the three declared residuals (2): `out/` content reaching the evaluator by design, shared hardware state, and transformed copies left by a non-compliant harness script. Each declaration is sound.

### Operator point 2 (isolation keeps reads and writes): met
The views are unchanged from s19 and s21 (30-34). s20 and s22 found them met.

### Arms, comparisons, compute facts
- **A0-A2:** runnable as sealed argument vectors (5-7).
- **K1-K7:** expressible and decidable as SHAPES.json shapes them. This uses output `select` and `{glob}`, `elementwise_abs` and `elementwise_abs_plus_rel_max`, `ratio_at_least` with a bootstrap ratio of means, `per_input_each` unpaired non-inferiority against a previous-run reference with `missing: fail`, two-sided superiority with `sign`, and `given` gating.
- **Compute facts:** `per_arm_wall`, `per_arm_gpu_s`, `hardware_identity` and `usd` are recorded (57, 68-73). Attribution and the bill are kept apart.

### Builder notes (not problem codes; none blocks a comparison)
1. **Empty private files.** Step 7 matches by size and SHA-256. If `fetch_private.sh` leaves a zero-length file in `cmp-private`, any empty file in the scanned directories (common in installed software) fails the run with `infra`. That fails safe and leaks nothing, but it can waste a box run. The fix is to skip zero-length files in the match, or to have `fetch_private.sh` leave none.
2. **No-follow semantics.** Wrapper step 2 re-owns `run/` and `out/` (61), and `run/` holds symbolic links by design. Re-owning and changing modes should not follow symbolic links (for example `chown -R -P`, `lchown`). The type check on `out/` should run before the mode change, as the text's order already implies.
3. **Mode of `eval/`.** The mode of `eval/` at creation is not stated (59). It should not be writable by `cmp-arm`, for example `755` or `700` owned by `cmp-eval`. Otherwise an arm could pre-plant evaluation files. A normal umask already gives this.
4. **Box-image checks and the provider CLI.** Still unverified, as in s20 and s22, and checked before any invocation with an `infra` failure:
   - `iptables`/`ip6tables` owner matching;
   - `sudo -n -u`;
   - GPU access through groups.
   
   Hiding the git work tree may also hide a provider CLI installed inside the repository.
5. **Cost.** The full-tree `find` sweeps after every part and the wider hash scan add box time that has not been measured (`s23/ASSESSMENT.md:87`).

## For the owner
- **Seed content:** none.
- **Sufficiency:** `sufficient`. s22's problem is fixed, and so are every earlier finding and both operator points. What no rule can remove is declared soundly as residual. The contract can run A0-A2, decide K1-K7 as shaped, and record every compute fact.
- **Still open from s23's OWNER.json:**
  - margins (the K1-K3 tolerances and the matching K6/K7 term);
  - approval of the evaluator's private data on the box, with the pipeline's passwordless sudo use;
  - spend above USD 20 (the main run projects USD 49.48, `s13/ASSESSMENT.md:86`, as cited by s23).
- s23 sealed no predictions, so `outcomes.json` is empty. This step runs no test.
- **Next action:** stop, `contract_gap`. The draft can go to the operator to commit into `dut/pipeline/m5/SCHEMAS.md`.
