# Independent named-location check

Authorized reader check started 2026-10-31 00:28 UTC. No files under `intake_check/` were opened before `status_independent.json` was written. Downloads reside only under `/home/hal/.cache/blind01/intake_check_dl/codex/`.

## Why the intake decisions differ

All four readers identified the same benchmark, PINDER-S release 2024-02, and the same PINDER code commit, `ebeb28a2f8411363cef722b7d293c978f7442672`. Their copied briefs are byte-identical to `BRIEF.md`.

| Draw | Data label | What was counted | Remaining issue in its own records |
| --- | --- | --- | --- |
| run1 | available | Published distribution and HEAD 200 for data endpoints | FroDock archive acquisition page returned 404; no selected-input inventory or completeness check. See `run1/agent/intake/data.json`, `baseline.json`, `EXECUTION.json`. |
| run2 | partial | Structures plus external baseline software and manifest completeness | FroDock archive unavailable; all selected entries not verified. See `run2/agent/intake/data.json` and `baseline.json`. |
| run3 | available | Remote accessibility of published protein data and evaluation harness | Its `baseline.json` explicitly says external FroDock archive, immutable pin, and complete configuration were unresolved. Evaluation alone does not generate docking predictions. See `run3/agent/intake/data.json`, `baseline.json`, `EXECUTION.json`. |
| run4 | partial | Every required structural file and baseline software/scoring input | FroDock archive and `soap.bin` unavailable; archive omissions not resolved per selected case. See `run4/agent/intake/data.json`, `baseline.json`, `EXECUTION.json`. |

This is substantially a scope/completeness distinction, not evidence that protein data were alternately available and unavailable. The available decisions did not establish completeness and did not resolve the missing docking dependency. All readers recorded the broken FroDock page. Transcript references include run1 intake transcript lines 103 and 134, run3 line 106, and run4 lines 133 and 142 (`runN/agent/wf/agents/0001-intake/codex-1.jsonl`). The run2 access checks also appear in `run2/agent/intake/access_evidence.json`.

The unresolved materials prerequisite is the external FroDock package, including the distributed `soap.bin` scoring potential required by PINDER's adapter. The named acquisition URL is `https://chaconlab.org/modeling/frodock/frodock-donwload`; correcting the spelling does not repair it. Persistent 404 at these paths points to moved/dead source locations, not a demonstrated login or transient outage. Relocation itself is investigated only in Phase B. The data label here covers all materials needed for the recorded docking comparator, including software and its scoring data.

Licence uncertainty is not a blocking prerequisite under the current intake rule. Run1 failed its older licence rule; run3's later installation failure does not prove material availability or failure. No licence conclusion is inferred from reachability.

## Inputs and completeness

The downloaded index has 2,319,564 rows, exactly 250 PINDER-S cases and 93 with both primary apo structures. `selected_cases.csv` records the prioritized 93; `pinder_s_cases.csv` records all 250, for verification coverage only. These inventories do not prescribe a new selection, protocol or scale.

For all 250 PINDER-S cases, the check enumerated native dimers, separated holo receptor/ligand files, every available primary apo receptor/ligand, and their published residue mappings: 1,618 unique files. The 500 required separated holo files were present in the official test archive; 1,118 further files were retrieved individually from the documented release directory. Every file parsed as nonempty PDB or Parquet, every native dimer contained receptor R and ligand L, and every file matched the publisher's manifest size and MD5. All 250 case IDs occur in metadata. The complete test archive passed ZIP CRC verification. The huge full-release PDB and mapping archives are optional distribution bundles, not additional scientific inputs; HEAD checks confirm reachability, but their full bytes were not downloaded. Required files were checked individually instead.

Official root checksums verified for:

| Input | Downloaded bytes | Published MD5 (base64) | Result |
| --- | ---: | --- | --- |
| index.parquet | 124511839 | UYXtX+N0ppWyIYrzham+LQ== | exact size and MD5 match |
| metadata.parquet | 103835983 | jWDRle0qZGXXKIDkcXGEFA== | exact size and MD5 match |
| test_set_pdbs.zip | 181968169 | pY207ZtGIaECxWYBu1g9Mg== | exact size and MD5 match; all ZIP CRCs valid |

Publisher checksum sources are the manifests at `https://pinderdata.org/2024-02/manifests/{root,pdbs,mappings,test_set_pdbs}.jsonl.gz`, as specified by the pinned PINDER downloader. These manifests contain 3,826,764 PDB records, 1,448,950 mapping records and 3,914 separated-test-file records. All 1,618 required keys are present. Multipart ETags are not treated as content checksums. `checksum_verification.json` and `selected_published_checksums.json` hold the comparisons; `input_inventory.json` has per-file SHA-256, byte counts and parse evidence.

The three original RCSB mmCIF locations returned complete, parseable structures: 6IHB (551618 bytes, 4868 atoms), 6JCQ (529158 bytes, 4809 atoms), 6JCS (527195 bytes, 4880 atoms). Entry block IDs match requested accessions. No external published cryptographic checksum was established for these current downloads; locally computed SHA-256 values and retrieval times appear in `fetch_attempts.jsonl`. Accessions do not freeze historical revisions. Assembly/chain/domain extraction remains study preparation, not evidence of absent source material.

The original PINDER source was downloaded at the pinned commit and inspected without installing or executing PINDER. Its method README names the broken download page; its Dockerfile expects `frodock3_linux64` from an external tar archive and `compile_frodock.sh`; its FroDock adapter invokes MPI binaries, clustering/view tools and `soap.bin`. The named author GitHub README is reachable but is documentation, not that software/data package.

Additional verification covers the default API's eager fetching of predicted monomers and alternative apo pairings for the prioritized 93 cases. These optional structures are not substituted into the benchmark's primary apo selection. Details and final results are in `api_extra_inventory.json` and `api_extra_summary.json`.

All fetch attempts, including scheduled retries, have UTC start/end times, HTTP/curl results, byte counts and SHA-256 in `fetch_attempts.jsonl`. `REPORT.md` supplies a human-readable attempt ledger after Phase B. No run was launched, no prediction generated, and GPU-box reachability was not tested.

The eager API check completed for 1,972 additional files (269,556,692 bytes), with no HTTP, size, MD5 or nonempty-parse failures. The independent status was then written before opening the earlier reader’s files. All named FroDock acquisition paths failed the initial attempt and three retries, separated by approximately 60 seconds. Materials are therefore not usable at the named locations alone.
