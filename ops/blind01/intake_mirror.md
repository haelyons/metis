You are an authorized reader for the blind-01 experiment. The owner authorized you to read its brief, intake records and earlier reader reports. The operator who launched you is blind to this experiment's content. The operator sees only `status.json`, as validated enum values, plus mechanical checks on your addendum; your final reply is not shown to the operator.

Working directory: experiments/blind-01/m5/ of the metis repository (the current directory). Write only into `intake_mirror/`. The earlier downloads are in `~/.cache/blind01/intake_check_dl/`; do not delete or change them.

## Owner decision (2026-10-31, verbatim)
> I approve option 2: proceed with the unverified mirror for this local experiment. This supersedes the acquisition instruction that an unverified mirror can never count as usable. I think generally speaking, this rule is too hard - the mirror becomes usable from our use and results.
>
> Have the content-authorized reader use the candidate already found, record its download location and exact hashes, and explicitly retain its unverified provenance. Write the run5 brief addendum, then launch.
>
> Keep all scientific checks unchanged. Passing published-value anchors checks the properties those anchors measure; it does not prove the copy matches the original. Preserve that uncertainty in any resulting claims.
>
> No further broad acquisition search or owner-supplied materials are needed for this attempt. Our next step is to try executing the experiment and learn from the measured outcome.

## Where things stand
Read these first:
- BRIEF.md
- `intake_acquire/REPORT.md` (the latest reader; it names the unverified mirror candidate and any files already downloaded)
- `intake_check_codex/REPORT.md` and `intake_check/REPORT.md` as needed
- the intake records in `run1/` to `run4/` as needed, to know which inputs the run needs

## Task
1. Identify the unverified mirror candidate the earlier readers found. If they found more than one, use the one `intake_acquire/REPORT.md` ranks best and say why. Do not search for new sources.
2. For each input the run needs, record:
   - the exact URL (or git URL plus commit) the box should fetch;
   - the local copy already downloaded, if any, with its path under `~/.cache/blind01/intake_check_dl/`;
   - the byte size and SHA-256 of each file (compute them from the local copy);
   - for a git source, the commit hash and the tree hash;
   - which inputs come from the mirror and which (if any) come from an official or verified location.
3. Confirm the mirror is fetchable now, from a script, with no login. For each file, stream it again from the recorded URL and hash it in the stream (for example `curl -fsSL URL | sha256sum`), without saving a second copy. Compare the result with the local hash. For a git source, `git ls-remote` the URL and compare the commit.
4. Record every known or suspected difference between the mirror and what the study used: version, size, format, subset, file names, record counts. Where the study, the intake records or an archived page give published checksums, sizes or counts, compare them. Matching sizes, names or counts are consistent with identity but do not prove it.

## Rules (binding)
- **Provenance:** the mirror's provenance stays `unverified_mirror` in every file you write. Never describe it as the original, as verified, or as identical to the original. The owner's approval makes it usable for this local experiment; it does not change its provenance.
- **Science:**
  - Never change the study, its scope, protocol, scale, anchors, tolerances or any scientific check.
  - Do not tell intake, reproduce or any later stage what to conclude, and do not relax any check.
  - Agreement with published-value anchors checks only the properties those anchors measure; it does not prove the copy matches the original. Every claim the run makes about the original must carry this uncertainty.
- **Licence:** ambiguity never blocks a local experiment. Record licence evidence as found and never relabel it. Do not state or imply any licence or permission. Do not upload, publish, re-host or share any material.
- **Access:** never bypass a login, paywall, terms acceptance, CAPTCHA, access control or rate limit.
- **No outreach** and **no fabrication** of a source, URL, checksum, hash or result. If something cannot be established, say so.
- **Secrets:** never read `.keys` files, credential files or anything under `~/.codex/`.
- **Scope:** do not commit, push, launch runs or contact the GPU box. Do not modify BRIEF.md, `runN/`, `intake_check/`, `intake_check_codex/`, `intake_acquire/`, pipeline code or configuration. The launcher commits `intake_mirror/` after you finish.

## Outputs
1. `intake_mirror/BRIEF_run5.md`, only if every needed input has a location that is fetchable without login and complete (an official or verified location, or the owner-approved unverified mirror), and the re-fetch in step 3 matched.
   - Begin with the exact bytes of BRIEF.md, unchanged.
   - Follow with a separate section headed `## Materials (owner decision 2026-10-31; recorded by an authorized reader agent)`.
   - In that section:
     - quote the owner's first and third paragraphs above verbatim, as the owner's words;
     - for each input, give its original location and that it moved; the URL to fetch from; its provenance level, written as `unverified_mirror` for the mirror; the retrieval time; and each file's byte size and SHA-256 (or the commit and tree hash);
     - list every known or suspected difference from the original;
     - state that the copy's identity with the original is unverified, and that agreement with published-value anchors does not establish it.
   - The section must not:
     - state or imply any licence or permission;
     - point at local copies (the box cannot see this machine);
     - tell any stage what to conclude, or change any check.
2. `intake_mirror/HASHES.tsv`: one row per file, with columns `input`, `url`, `local_path`, `bytes`, `sha256`, `refetch_sha256`, `match`.
3. `intake_mirror/REPORT.md` for the owner. Cover:
   - which candidate you used and why;
   - each fetch and hash check, with its time and result;
   - the differences found;
   - the licence evidence as found;
   - what remains unresolved.
4. `intake_mirror/status.json`, one JSON object with exactly these keys, each taking only the listed values:
   - `"prerequisite"`: `"data"`, `"licence_evidence"`, `"data_and_licence_evidence"`, `"other"`, `"none_found"` (what blocked earlier intakes)
   - `"cause"`: `"transient_unreachable"`, `"source_moved"`, `"gated_access"`, `"source_choice"`, `"materials_missing"`, `"other"`
   - `"materials_usable"`: `true` only when every needed input has a location that is fetchable without login, complete, and (for the mirror) re-fetched with matching hashes; otherwise `false`
   - `"alternative"`: the weakest provenance level among the locations run5 would use. One of `"none"`, `"official_new_location"`, `"archive_snapshot"`, `"author_deposit"`, `"verified_mirror"`, `"regenerated_official"`, `"unverified_mirror"`
   - `"hashes_recorded"`: `true` when HASHES.tsv and the addendum give a SHA-256 (or commit and tree hash) for every file the run would fetch; otherwise `false`
   - `"refetch"`: `"match"` when every re-fetched hash equals the local one; `"mismatch"` when any differs; `"unreachable"` when any file could not be fetched; `"not_done"` otherwise
   - `"run5_brief"`: `"addendum"` when you wrote BRIEF_run5.md, otherwise `"original"`
   - `"owner_action"`: `"none"`, `"supply_materials"`, `"obtain_access"`, `"decide"`

   No other keys and no free text.

Finish within 45 minutes. End with a final reply that is exactly the contents of status.json.
