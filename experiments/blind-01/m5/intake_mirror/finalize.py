"""Build owner outputs after matching refetches; preserve unverified_mirror provenance."""
import csv
import datetime
import hashlib
import json
from pathlib import Path

OUT = Path(__file__).resolve().parent
WORK = OUT.parent
PIN = 'ebeb28a2f8411363cef722b7d293c978f7442672'
HEADER = '## Materials (owner decision 2026-10-31; recorded by an authorized reader agent)'
FIRST = ('I approve option 2: proceed with the unverified mirror for this local experiment. '
         'This supersedes the acquisition instruction that an unverified mirror can never count as usable. '
         'I think generally speaking, this rule is too hard - the mirror becomes usable from our use and results.')
THIRD = ('Keep all scientific checks unchanged. Passing published-value anchors checks the properties '
         'those anchors measure; it does not prove the copy matches the original. Preserve that uncertainty in any resulting claims.')

DIFFERENCES = '''- The FroDock distribution page originally cited by PINDER is `https://chaconlab.org/modeling/frodock/frodock-donwload`. Earlier intakes repeatedly received HTTP 404; the lab's replacement tools route leads to documentation. The selected GCS URL is a third-party `unverified_mirror`, with no established author endorsement or authenticated upstream package comparison. The original static payload URL was not established. This is a replacement fetch location, not an authenticated official relocation.
- The mirror README identifies FroDock 3.12, dated 2020-02-08; the archived official page identifies 3.12 (2020), updated 2020-02-14. The study/intake did not establish an immutable external FroDock release/hash. Matching release text cannot establish the study's exact software or scoring bytes.
- The mirror archive is `frodock3_linux64.tgz`, a gzip-compressed tar with root `frodock3_linux64/`; the published Dockerfile's local argument/default is `frodock.tar.gz`. These suffixes denote the same container format. Local build filename differs; archive contents and source pin are not changed by recording that difference.
- Mirror size is 26,637,000 bytes (25.403023 MiB), consistent with the rounded 25.40-MB size reported by the earlier reader from historical-page evidence. No exact upstream distribution size, cryptographic checksum or member manifest was established. The mirror's own MD5 and repeated downloads identify its bytes only.
- The archive contains 542 members, 445 regular files and 65,507,120 uncompressed regular-file bytes; gzip CRC and complete member reads pass. Expected GNU/MPI docking, grid, clustering and view tools, compilation sources/script and `bin/soap.bin` are present. No authoritative original member count or per-member hash set is available for comparison; unknown additions, omissions or modifications remain possible.
- README utility versions differ internally: docking 3.12, grid 2.1, clustering 3.0, view 2.0, constraints 2.3 and check 2.1. Several README headings still say 3.0; `compile_frodock.sh` prints `COMPILING & LINKING FRODOCK-2.0 TOOLS (v1.06)`. Whether these same mixed labels appear in the study's copy is unestablished. The README lists GNU gcc 7.3.0 and Intel compiler 18; compatibility, rebuilding and equivalence of compiled/prebuilt executables were not measured.
- Required `bin/soap.bin` is 7,536,604 bytes, SHA-256 `791f31ec8ef1ef1466092b425638e926755519c9626f5678ca675ef6c76234fc`. A different `src/frodockonstraint/Release_intel/soap.bin` is 3,014,640 bytes, SHA-256 `6c791aad8ef72a600a9388adfbfda83b4d998cc87023d00c70cf0f2a9bb06948`. They are distinct archive members; the latter is not a replacement for the adapter's scoring file. Scoring identity with the study remains unverified.
- PINDER materials remain at the official 2024-02 locations already recorded in intake; no relocation is asserted. Index and metadata each contain 2,319,564 rows, including 250 PINDER-S cases and 93 with both primary apo monomers; all 250 IDs have metadata. These match published case counts. The inventory covers 1,618 structural/mapping inputs for all 250 cases plus 1,972 default-API auxiliary downloads for the prioritized 93. Auxiliary predicted/alternative apo files do not replace primary paired apo inputs or change scientific scope. The full training set and optional bulk PDB/mapping ZIPs are not required by this source inventory.
- Official test ZIP contains 3,914 regular files plus one directory entry (3,915 total entries), with 730,945,215 uncompressed bytes and valid CRCs. The published code's 3,914 file count excludes the directory. Current official manifests list 18 root, 3,826,764 PDB, 1,448,950 mapping and 3,914 separated-test entries. All 3,590 inventoried individual inputs and the three root data files match published manifest sizes and MD5s. This establishes consistency with the current official release, not unspecified historical-study byte identity. No missing required file or truncated subset was found.
- AAV entry IDs and atom counts are 6IHB: 4,868, 6JCQ: 4,809 and 6JCS: 4,880, consistent with earlier reader copies. RCSB entry IDs and release labels do not pin historical revisions; no independent published checksum for these mmCIF responses was established. Assembly/chain/domain extraction remains later study work, and separated components remain redocking inputs, not independently determined unbound structures.
- The PINDER evaluator/adapter source uses the existing recorded commit, not a substituted registry release or third-party container. GitHub tar bytes differ from PyPI distribution containers; no archive-byte equality is asserted. Published build dependencies remain described by that source; this inventory does not establish a resolved installed environment. Source-inspection concerns previously recorded for the adapter and Dockerfile remain untested. No docking result, runtime or anchor outcome is established here.
'''

def read(name):
    return json.loads((OUT / name).read_text())

def main():
    rows = sorted(read('refetch_results.json'), key=lambda r: r['input'])
    git = read('git_verification.json')
    science = read('scientific_input_inspection.json')
    mirror = read('mirror_inspection.json')
    assert len(rows) == 3602 and all(r['match'] and r['http_status'] == 200 and r['curl_exit'] == 0 for r in rows)
    assert git['ls_remote_contains_pin'] and git['commit_match'] and git['tree_match'] and science['complete']
    assert all(r['refetch_md5_base64'] == r.get('published_md5', r['refetch_md5_base64']) for r in rows)
    assert mirror['provenance'] == 'unverified_mirror' and mirror['regular_files'] == 445
    for r in rows:
        p = Path(r['local_path'])
        assert p.stat().st_size == r['bytes'] and p.stat().st_mtime_ns == r['cache_mtime_ns']
    with (OUT / 'HASHES.tsv').open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=['input', 'url', 'local_path', 'bytes', 'sha256', 'refetch_sha256', 'match'], delimiter='\t')
        writer.writeheader()
        for r in rows:
            writer.writerow({key: ('true' if key == 'match' else r[key]) for key in writer.fieldnames})
    start = min(r['started_utc'] for r in rows)
    end = max(r['ended_utc'] for r in rows)
    individual_keys = {x['key'] for x in json.loads((WORK / 'intake_acquire/per_file_evidence.json').read_text())}
    top = [r for r in rows if r['input'] not in individual_keys]
    section = f'''\n\n{HEADER}

Owner's words, first paragraph:

> {FIRST}

Owner's words, third paragraph:

> {THIRD}

The FroDock material below has provenance `unverified_mirror`. Its identity with the original study distribution remains unverified. Agreement with published-value anchors checks only the properties those anchors measure and does not establish identity with the original. Claims about the original remain conditional on this unresolved material identity; use of these bytes does not remove that uncertainty. This materials record changes no study scope, protocol, scale, anchors, tolerances or scientific check, and records no experimental conclusion.

Original locations and movement:

- FroDock: original cited distribution page `https://chaconlab.org/modeling/frodock/frodock-donwload` is a moved/dead path in earlier intake evidence. Replacement fetch URL: `https://storage.googleapis.com/gke-dja-demo_static_assets/frodock3_linux64.tgz`; provenance `unverified_mirror`. Original payload URL and original package hash are unestablished. This archive supplies both software and distributed scoring input.
- PINDER index, metadata, test ZIP, individual PDB/mapping inputs and manifests: original official locations under `https://pinderdata.org/2024-02/`, unchanged from intake. Each exact original/fetch URL appears below. Provenance `official_original_location`; no movement found.
- AAV structures: original official RCSB locations `https://files.rcsb.org/download/6IHB.cif`, `https://files.rcsb.org/download/6JCQ.cif`, `https://files.rcsb.org/download/6JCS.cif`, unchanged. Provenance `official_original_location`.
- PINDER source: original official git URL `https://github.com/pinder-org/pinder.git`, unchanged, commit `{PIN}`, tree `{git['official_tree']}`. Exact source-archive fetch URL appears below. Provenance `official_original_location`. Anonymous `git ls-remote` returned the recorded commit for `refs/heads/main` at {git['ls_remote_ended_utc']}; the archive's independently computed Git tree matches official commit metadata.

All 3,602 recorded URLs were anonymously re-fetched from this reader's machine between {start} and {end}, with streaming SHA-256 and size checks matching existing copies. No second payload copy was saved. Retrieval times below are completion times of these current full streaming GETs, in UTC. The source archive contains the published evaluator, adapter and build recipes. Ordinary runtime dependency resolution and execution remain later build work.

Known or suspected differences and comparison limits:

{DIFFERENCES}
File inventory: exact remote locations, provenance, current retrieval times, byte sizes and SHA-256. Each row's SHA-256 is both the locally computed digest and the matching streaming re-fetch digest. This inventory includes four official checksum manifests and the default-API auxiliary files so those potential fetches are explicit; it does not preregister a new case selection.

| Input | Exact fetch URL (also original URL for official inputs) | Provenance | Retrieval completed UTC | Bytes | SHA-256 (local and re-fetch) |
| --- | --- | --- | --- | ---: | --- |
'''
    for r in rows:
        section += f'| `{r["input"]}` | {r["url"]} | `{r["provenance"]}` | {r["ended_utc"]} | {r["bytes"]} | `{r["sha256"]}` |\n'
    original = (WORK / 'BRIEF.md').read_bytes()
    (OUT / 'BRIEF_run5.md').write_bytes(original + section.encode())
    ledger = '''# Anonymous streaming fetch ledger

FroDock provenance remains `unverified_mirror`. All timestamps UTC. Every response body was hashed in a stream and discarded; no second payload copy saved. `curl -q --fail --silent --show-error --location` with HTTPS-only redirects, bounded timeouts and no credentials or cookie jar. Eight concurrent ordinary GETs, no retry or access-control bypass. Every row below returned HTTP 200 / curl exit 0 and matching byte count, local SHA-256, streaming SHA-256; published MD5s also matched where available.

| Input | URL | Started UTC | Ended UTC | Bytes | SHA-256 (local and stream) | Result |
| --- | --- | --- | --- | ---: | --- | --- |
'''
    for r in rows:
        ledger += f'| `{r["input"]}` | {r["url"]} | {r["started_utc"]} | {r["ended_utc"]} | {r["bytes"]} | `{r["sha256"]}` | match |\n'
    (OUT / 'FETCH_LEDGER.md').write_text(ledger)
    licence_path = Path('/home/hal/.cache/blind01/intake_check_dl/acquire/archive_license.body')
    licence_hash = hashlib.sha256(licence_path.read_bytes()).hexdigest()
    report = f'''# Owner report: mirror materials for run5

Authorized reader, 2026-10-31. Work began 15:26 UTC. FroDock provenance: **`unverified_mirror`**. Materials are usable for this local attempt under the owner's 2026-10-31 decision; scientific checks and identity uncertainty remain unchanged. `BRIEF_run5.md` begins with the exact bytes of `../BRIEF.md` and adds the required materials section. No experiment or GPU-box operation was launched.

## Candidate and earlier blocker

Selected `https://storage.googleapis.com/gke-dja-demo_static_assets/frodock3_linux64.tgz`, the best complete fetchable `unverified_mirror` identified by `../intake_acquire/REPORT.md`. That reader found the required source, programs, compilation script and scoring input there. Scipion's candidate timed out; the current author repository supplies documentation only; the third-party container derives from the same GCS archive; old releases differ from the recorded comparator. No new source search was performed. Original required FroDock distribution path had moved/disappeared; prerequisite was data, including software/scoring bytes. Earlier licence evidence ambiguity is recorded, not treated as a blocker.

The owner's decision supersedes the earlier rejection of this candidate for local usability. It does not authenticate the mirror or settle any software or scoring differences. Weakest provenance remains `unverified_mirror`.

## Fetches, local copies and exact hashes

Computed local sizes/SHA-256 for all **3,602** files, totalling **{sum(r['bytes'] for r in rows):,} bytes**, by reading existing files beneath `/home/hal/.cache/blind01/intake_check_dl/`. Existing cache files were not modified. `HASHES.tsv` gives every exact URL, absolute cache path, byte count, SHA-256, re-fetch SHA-256 and match flag. Paths are owner audit references; none occurs in the run5 addendum.

Each file was fetched again anonymously from its recorded URL, streaming and hashing the full response without saving another payload copy. Checks ran {start}–{end}. **3,602 HTTP 200 responses; 3,602 matching byte counts and SHA-256 values; zero failures, mismatches or access barriers.** All available published MD5 comparisons also match. Precise start/end times, URLs, sizes, hashes and results for every individual fetch are in [FETCH_LEDGER.md](FETCH_LEDGER.md) and [fetch_checks.jsonl](fetch_checks.jsonl); `refetch_results.json` carries the same results with local evidence. This report incorporates those per-file ledgers.

Top-level payload and manifest transfers (SHA-256 values and cache locations in `HASHES.tsv`):

| Input | Started UTC | Ended UTC | Bytes | Result |
| --- | --- | --- | ---: | --- |
'''
    for r in top:
        report += f'| `{r["input"]}` | {r["started_utc"]} | {r["ended_utc"]} | {r["bytes"]} | match |\n'
    report += f'''
PINDER git URL: `https://github.com/pinder-org/pinder.git`; recorded commit `{PIN}`; tree `{git['official_tree']}`. `git ls-remote` ran {git['ls_remote_started_utc']}–{git['ls_remote_ended_utc']}, exit 0, and advertised the same commit at `refs/heads/main`. Commit metadata GET ran {git['commit_metadata_started_utc']}–{git['commit_metadata_ended_utc']}, curl exit 0; SHA and tree matched. The tree was independently reconstructed from archive member names, modes, symlinks and Git blob/tree object hashes without checkout or executing source. Details: [git_verification.json](git_verification.json).

The mirror archive's 445 regular member hashes and its required scoring-file distinction were independently rechecked: [mirror_inspection.json](mirror_inspection.json). The archive itself is the fetched input, hence one HASHES.tsv row; internal member hashes supplement that row rather than inventing separately fetchable URLs. No FroDock git commit/tree is established; the selected source is a tar archive, not a git source.

## Completeness, differences and scientific limits

{DIFFERENCES}
The local index/count, metadata coverage, ZIP CRC, AAV atom/revision and manifest-count checks were repeated independently; see [scientific_input_inspection.json](scientific_input_inspection.json). Prior per-file parse evidence is retained in the earlier reader inventories; current local and network hashes establish that the inspected bytes persist. Sizes/MD5s for the 3,590 individual inputs and three root data files were compared against the earlier reader's official-manifest evidence. This pass also re-fetched all four complete official manifests with matching SHA-256, so that published evidence remains current. No extra primary/apo/predicted substitution was made.

FroDock identity with the original remains unverified. Matching filename, rounded size, self-reported version, archive integrity, transport checksum, repeated downloads or available published-value anchors do not establish it. Anchor agreement checks only properties measured by those anchors. Any statement about the original study remains conditional on unresolved identity of the selected `unverified_mirror`, including possible effects of different source, binaries or scoring potential. This intake records no experimental result or recommended conclusion and changes no check.

## Licence evidence as found

No licence or permission determination is made here, and no material was uploaded, published, re-hosted or shared. Evidence is recorded without assigning it to unproven components:

- Earlier reader retrieved [archived official text](https://web.archive.org/web/20160215205724id_/http://chaconlab.org:80/downloads/License.txt) at 2026-10-31T02:24:17.025208+00:00. Existing local evidence `/home/hal/.cache/blind01/intake_check_dl/acquire/archive_license.body` was read and rehashed: {licence_path.stat().st_size} bytes, SHA-256 `{licence_hash}`. Text carries CSIC copyright 2013, a grant clause, source/binary notice clauses, a non-endorsement clause, and warranty/liability exclusions. No SPDX label assigned. Earlier reader matched its SHA-1 base32 to CDX digest `EEAUVAMLPGVE6UWDYFZ67JTZLGMWF6AJ`.
- Earlier official download-page capture links that text and ties its Download action to acknowledgement. The action was not invoked. Current text URL returned 404 in earlier evidence. A 2016 text capture does not establish the text governing a 2020 package or every bundled component. Mirror has no member named LICENSE, LICENCE or COPYING. Its provenance remains `unverified_mirror`.
- The pinned PINDER repository's LICENSE text identifies Apache License 2.0. This is evidence about repository code, not a blanket label for processed hosted data or external FroDock.
- Cached [wwPDB usage-policy page](https://www.wwpdb.org/about/usage-policies) says PDB archive data are under CC0 1.0. This policy statement is recorded as found and does not authenticate a historical structural revision or label other materials.
- Earlier reader recorded CC-BY 4.0 in PINDER preprint v4 metadata/source; that publication label is not transferred to software/data. Hosted processed PINDER data coverage, applicability of historical FroDock text and bundled-component coverage remain unresolved. Ambiguity does not block this local attempt under the owner's instruction.

## Unresolved and scope

Unresolved: mirror identity/authoritative original comparison; exact study-era external FroDock revision; unpinned historical structure revisions; licence applicability; installed build/runtime compatibility and previous source-inspection concerns; preregistered selection/seeds/configuration; assembly/domain extraction; scientific reproduction, performance, anchors and docking outcomes. These remain later study work or limits on claims. The material inputs themselves are complete and anonymously script-fetchable from this machine now. GPU-box reachability was not tested or asserted.

No broad acquisition search, outreach, login, agreement acceptance, challenge solving, rate-limit workaround, installation, benchmark execution, GPU-box contact, pipeline/configuration edit, commit or push occurred. Only `intake_mirror/` was written. Earlier downloads remain in place. `protected_before.json` records read-only protected-input hashes; final validation checks them, exact brief prefix, owner quotations, full per-file coverage, hash equality and enum-only status.

Owner action: none for this materials attempt. Launcher action remains outside this reader's scope. The brief contains only remote locations, never machine-local cache references or licence assertions.
'''
    (OUT / 'REPORT.md').write_text(report)
    status = dict(prerequisite='data', cause='source_moved', materials_usable=True,
                  alternative='unverified_mirror', hashes_recorded=True, refetch='match',
                  run5_brief='addendum', owner_action='none')
    (OUT / 'status.json').write_text(json.dumps(status, indent=2) + '\n')
    print(json.dumps({'outputs_written': True, 'file_rows': len(rows), 'brief_bytes': (OUT / 'BRIEF_run5.md').stat().st_size}))

if __name__ == '__main__':
    main()
