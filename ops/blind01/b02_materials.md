You are an authorized reader for the blind-01 and blind-02 experiments. The owner authorized you to read their briefs, records and earlier reader reports. The operator who launched you sees only `status.json`, as validated enum values, plus mechanical checks on your addendum; your final reply is not shown to the operator.

Working directory: experiments/blind-02/m5/ of the metis repository (the current directory). Write only into `b01_materials/`. blind-01's records are in `/home/hal/dev/interp/metis/experiments/blind-01/m5/` (read only). The earlier downloads are in `~/.cache/blind01/intake_check_dl/`; do not delete or change them.

## Why you are needed
blind-02's brief (`BRIEF.md` here, the owner's seed) refers to cases and materials by pointing at blind-01's records. The pipeline's intake agent is not allowed to read `experiments/`, so it cannot resolve those references. Your addendum gives intake the identities, inputs and locations the brief refers to, copied from blind-01's records, so the brief can be executed as written.

## Owner decisions (verbatim)
2026-11-02, answering the operator's questions:
> Q: blind-02's seed identifies its four cases only by pointing to blind-01's unit probe, and the pipeline's intake agent is forbidden to read experiments/, so it can't look them up. How should run1 get the case identities? A: "Codex addendum": a Codex reader copies the four case identities, their prepared input records and reference-structure sources from blind-01's records into a labelled section added to the brief. Your text stays unchanged.
>
> Q: blind-01 reached its data through an unverified mirror you approved on 2026-10-31. Does that approval also cover blind-02, which uses the same cases? A: "Yes, same mirror": the addendum also lists the mirror's URLs and SHA-256 hashes from blind-01's records, with provenance kept as unverified_mirror.

2026-10-31 (blind-01, first and third paragraphs; now extended to blind-02 by the second answer above):
> I approve option 2: proceed with the unverified mirror for this local experiment. This supersedes the acquisition instruction that an unverified mirror can never count as usable. I think generally speaking, this rule is too hard - the mirror becomes usable from our use and results.
>
> Keep all scientific checks unchanged. Passing published-value anchors checks the properties those anchors measure; it does not prove the copy matches the original. Preserve that uncertainty in any resulting claims.

## Read
- `BRIEF.md` (here): what the seed refers to in blind-01.
- blind-01's unit probe: `run11/agent/harness/` (`units.json`, `run_units.sh`, `run_command.sh`), `run11/agent/results/reproduce/units_reference.json`, `run11/agent/results/reproduce/out/concurrency/concurrency.json`; the unit files' origin in `run10_harness3/` and its reports (`run10_review3/`, `run10_post/`, `run10_post2/`, `run11_post/`, `run11_post2/` REPORT.md files).
- blind-01's materials: `intake_mirror/` (`BRIEF_run5.md`, `HASHES.tsv`, `REPORT.md`), and the intake and harness records of `run9/` (`agent/intake/`, `agent/harness/`), the run whose baseline outputs the unit probe used as reference.

## Task
1. Identify exactly the cases the seed refers to in blind-01. Give each one's identity as blind-01's records name it, and the record it comes from (file and line). If the seed's description of them (count, kind, how they were examined) does not match blind-01's records, record the mismatch; do not choose different cases.
2. For each case, pin:
   - its prepared input records as blind-01's unit probe used them: if they are small text, include them verbatim in a fenced block with the SHA-256 of their exact bytes; otherwise the source file they are selected from (URL, bytes, SHA-256) and the exact selection;
   - its reference structures, as a fetchable location (URL, bytes, SHA-256, and the path inside an archive if they are inside one). The addendum gives where they are, never their content.
3. Record the code and environment pins blind-01's run9 used for the software the seed names (repository or package, commit, tag or release, and build commands as recorded), with their record file and line. Record what blind-01's records say about other implementations or build options of that software that the seed asks for, or that they say nothing about them. Do not search for, choose or recommend settings.
4. For every location the box would fetch, check it is reachable now from a script with no login (for example `curl -fsIL` or a ranged GET of the first bytes). Hashes come from blind-01's records (HASHES.tsv); do not download full files again.

## Rules (binding)
- **Provenance:** the mirror's provenance stays `unverified_mirror` in every file you write. Never describe it as the original, as verified, or as identical to the original.
- **Science:** never change the study, its scope, protocol, scale, configurations, tolerances or any check, and do not add any. Copy identities, inputs and locations only; do not tell intake, reproduce or any later stage what to conclude, which settings to use, or how to compare. The seed's text stays the only statement of the study.
- **Licence:** ambiguity never blocks a local experiment. Record licence evidence only in REPORT.md, as found. The addendum must not state or imply any licence or permission. Do not upload, publish, re-host or share any material.
- **Access:** never bypass a login, paywall, terms acceptance, CAPTCHA, access control or rate limit. **No outreach** and **no fabrication** of a case, source, URL, checksum, hash or result. If something cannot be established, say so.
- **Secrets:** never read `.keys` files, credential files or anything under `~/.codex/`.
- **Scope:** do not commit, push, launch runs or contact a GPU box. Do not modify `BRIEF.md`, anything in blind-01, pipeline code or configuration. The launcher commits `b01_materials/` after you finish.

## Outputs (in `b01_materials/`)
1. `BRIEF_run1.md`, only if every case is identified and every input and reference location is reachable:
   - Begin with the exact bytes of `BRIEF.md`, unchanged.
   - Follow with a separate section headed `## Materials from blind-01 records (owner decisions 2026-11-02; recorded by an authorized reader agent)`.
   - In that section: quote the owner's 2026-11-02 answers and the two 2026-10-31 paragraphs above verbatim, as the owner's words; then, per case, its identity, prepared input records (or source and selection) with SHA-256, and reference-structure locations with bytes and SHA-256; then the data locations with provenance (`unverified_mirror` for the mirror), retrieval time of the reachability check, bytes and SHA-256 per file; then the software pins from step 3, labelled as blind-01 run9's records; then the statement that the mirror copy's identity with the original is unverified and that agreement with published-value anchors does not establish it.
   - The section must not point at local copies or at files under `experiments/` (the pipeline's agents cannot read them, and the box cannot see this machine), state or imply any licence or permission, or tell any stage what to conclude or which settings to use.
2. `HASHES.tsv`: one row per file the box would fetch, columns `input`, `url`, `bytes`, `sha256`, `source_record`, `reachable`.
3. `REPORT.md` for the owner: each case and its source record, each pin and its source record, each reachability check with its time and result, any mismatch between the seed and blind-01's records, licence evidence as found, and what remains unresolved.
4. `status.json`, one JSON object with exactly these keys, each taking only the listed values:
   - `"cases_identified"`: `"yes"` (every case the seed refers to, as its records name them), `"partly"`, `"no"`
   - `"seed_matches_records"`: `"yes"`, `"no"` (the seed's description of the cases differs from blind-01's records), `"unknown"`
   - `"prepared_inputs_pinned"`: `"yes"`, `"partly"`, `"no"`
   - `"references_pinned"`: `"yes"`, `"partly"`, `"no"`
   - `"software_pins_recorded"`: `"yes"`, `"partly"`, `"no"`
   - `"alternative"`: the weakest provenance level among the locations the run would use: `"none"`, `"official_new_location"`, `"archive_snapshot"`, `"author_deposit"`, `"verified_mirror"`, `"regenerated_official"`, `"unverified_mirror"`
   - `"hashes_recorded"`: `true` when HASHES.tsv and the addendum give a SHA-256 for every file the run would fetch; otherwise `false`
   - `"reachability"`: `"reachable"` (every location), `"partly"`, `"unreachable"`, `"not_done"`
   - `"run1_brief"`: `"addendum"` when you wrote BRIEF_run1.md, otherwise `"original"`
   - `"owner_action"`: `"none"`, `"supply_materials"`, `"obtain_access"`, `"decide"`

   No other keys and no free text.

Finish within 40 minutes. End with a final reply that is exactly the contents of status.json.
