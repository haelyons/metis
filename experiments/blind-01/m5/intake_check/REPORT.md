# blind-01 m5: intake prerequisite check (authorized reader, 2026-10-30)

Written by an authorized reader agent for the owner. Paths are relative to `experiments/blind-01/m5/`.

## Summary

- The protein data is not the problem. In all four draws, every PINDER and RCSB endpoint intake checked returned HTTP 200. Today I downloaded all six from this machine, and their sizes match the sizes intake recorded.
- The unresolved prerequisite is the **FroDock software archive** (`frodock.tar.gz` / `frodock3_linux64`). PINDER's published docking baseline requires it, and so do the brief's "existing docking methods" and "optimised existing implementation" comparisons. Its evidence of licence terms is also unresolved.
  - PINDER's methods README links to `https://chaconlab.org/modeling/frodock/frodock-donwload`. That link returned HTTP 404 in **all four** draws and in all my attempts today.
- **Why draws differ:** the draws classified the same 404 differently. The 404 itself was the same in every run.
  - run2 and run4 listed the FroDock archive as a required input in `data.json`, so they set `availability: "partial"` and `licence_basis: "unreachable"`.
  - run1 and run3 saw the same 404 but recorded it only in `baseline.json`, as a baseline blocker, and kept `data` as "available".
  - The intake prompt does not say whether baseline software counts as "required data". See `run4/agent/wf/agents/0001-intake/prompt.md:8,14`.
- **Cause:** the official source has moved, and the replacement location does not distribute the program. The Chacón lab website has been restructured:
  - The old `/modeling/frodock/...` and `/downloads` pages now return 404.
  - The new `/tools/` page links FRODOCK only to `https://github.com/chaconlab/FRODOCK`.
  - That repository contains only `README.md`, `user_guide.md` and images. It has no source, no binary, no releases and no licence file.
  - I found no official public location for the archive. Search-engine snapshots of the old download page say that downloading meant accepting a "Software Licensing Agreement". I could not verify this because the page is gone.
- **Not resolved:** I found no working official source for the FroDock archive, so materials are not usable for run5 as briefed. A run5 brief addendum would not help, because there is no confirmed official location to point intake at. I did not write one.
- **Owner action:** supply the FroDock archive. For example, contact the Chacón lab, which is an official author distribution, and accept any licence agreement it requires. Alternatively, decide on a different baseline. SBGrid is a third-party consortium distribution that likely needs membership, lists older versions (2.1 and earlier) and publishes no checksums I could find. I did not use it.

## 1. Comparison of intake decisions

| | run1 | run2 | run3 | run4 |
|---|---|---|---|---|
| data availability | available | partial | available | partial |
| FroDock link status seen | 404 (`run1/agent/intake/baseline.json:14`) | 404 (`run2/agent/intake/data.json:18-24`) | 404 (`run3/agent/intake/baseline.json:42-43`) | 404 (`run4/agent/intake/data.json:48-55`, `baseline.json:46-47`) |
| Where FroDock was recorded | baseline.json only | data.json `required_inputs` + benchmark licences | baseline.json `docking_baseline_candidate` + benchmark `unresolved` | data.json `required_inputs` + benchmark licences/blockers |
| licence_basis | (licence rule fail, since removed) | `unreachable`, from the FroDock entry (`run2/agent/intake/benchmark.json:53-60,70`) | `none`, from the PINDER hosted data (`run3/agent/intake/benchmark.json:79-84`) | `unreachable`, from the FroDock entry (`run4/agent/intake/benchmark.json:74-84`) |
| PINDER/RCSB endpoints | all 200 (`run1/agent/intake/data.json:26-62`) | all 200 (`run2/agent/intake/access_evidence.json`) | all 200 (`run3/agent/intake/data.json`) | all 200 (`run4/agent/intake/data.json:17-73`) |
| Gate | FAIL (licence) | FAIL `data_unavailable` (`run2/control/stages/intake.json`) | PASS | FAIL `data_unavailable` (`run4/control/stages/intake.json`) |

Notes:
- **Secondary reason in run2 and run4.** Both also cite "completeness of every required apo/native/mapping file not established" (`run2/agent/intake/data.json:44`, `run4/agent/intake/data.json:3`). run1 and run3 did not verify per-file completeness either (`run1/agent/intake/data.json:3`, `run3/agent/intake/data.json:123`), but still called the data available. So this is also a judgement difference, not a difference in evidence.
- **One extra 404 in run2.** run2 also got a 404 for `https://pinderdata.org/2024-02/test_set_pdbs.tar.gz` (`run2/agent/intake/access_evidence.json:14-17`). That is a guessed filename; the published archive is `.zip`, and run2 reached it.
- **Other URLs run4 tried.** run4 also probed `https://chaconlab.org/modeling/frodock/frodock-download` (correct spelling) and `https://chaconlab.org/downloads`. Both returned 404. See `run4/agent/wf/agents/0001-intake/codex-1.jsonl`, lines 140-142 and 190-192.

## 2. Prerequisite and cause

- **Prerequisite:** the FroDock program archive, and its licence evidence, which comes from the same page.
  - Intake files it under "data". That is the input that set `data: partial` and `licence_basis: unreachable` in the failed draws.
  - The archive is not optional for the study as briefed. Running PINDER's published FroDock baseline needs it (`docker build --build-arg FRODOCK_SOURCE_ARCHIVE=./frodock.tar.gz ...`, pinder `src/pinder-methods/pinder/methods/README.md` at `ebeb28a2`).
  - The PINDER evaluator alone (`pinder_eval`) does not generate poses.
- **Cause:** the source has moved, and the new official location does not host the program.
  - Not transient: the 404 was the same across four draws spread over the day and three probes of mine. All returned an identical 13,631-byte 404 page.
  - Not a choice between sources: every draw used the same link, the one PINDER publishes.
  - Gating may also apply. The old page reportedly required accepting a licence agreement, but that can no longer be observed.

## 3. Fetch attempts (from this machine, UTC, 2026-10-30)

Downloads are in `~/.cache/blind01/intake_check_dl/`.

| Time (UTC) | URL | Result |
|---|---|---|
| ~21:33:50 | https://chaconlab.org/modeling/frodock/frodock-donwload | 404 (attempt 1) |
| ~21:33:55 | https://chaconlab.org/downloads | 404 |
| ~21:33:55 | https://chaconlab.org/modeling/frodock | 404 |
| ~21:33:55 | https://frodock.chaconlab.org/ | 200: web docking server only, no program download link |
| ~21:34 | https://chaconlab.org/ | 200: new site; nav has /tools/ and /servers/ |
| ~21:34 | https://chaconlab.org/tools/ | 200: FRODOCK links only to https://github.com/chaconlab/FRODOCK |
| ~21:34 | https://chaconlab.org/servers/ | 200: FRODOCK web server only |
| ~21:34 | https://chaconlab.org/methods/docking/frodock | 404 |
| ~21:34 | https://chaconlab.org/modeling/frodock/frodock-donwload/item/frodock-3-0-linux64 (from search index) | 404 |
| ~21:34 | api.github.com/repos/chaconlab/FRODOCK (+ `/releases`, `/git/trees/main?recursive=1`) | 200; licence null, 0 releases, tree = README.md, user_guide.md, assets/*.jpg, assets/temp (last push 2024-06-21) |
| ~21:35:10 | https://pinderdata.org/2024-02/index.parquet | 200, 124,511,839 B |
| ~21:35:15 | https://pinderdata.org/2024-02/metadata.parquet | 200, 103,835,983 B |
| ~21:35:20 | https://pinderdata.org/2024-02/test_set_pdbs.zip | 200, 181,968,169 B |
| ~21:35:25 | https://files.rcsb.org/download/6IHB.cif, 6JCQ.cif, 6JCS.cif | 200 each: 551,618 / 529,158 / 527,195 B |
| 21:35:30 | https://chaconlab.org/modeling/frodock/frodock-donwload | 404 (attempt 2) |
| 21:36:00 | same | 404 (extra probe; only ~30 s after attempt 2) |
| 21:36:53 | same | 404, 13,631 B (attempt 3, 83 s after attempt 2) |

SHA-256 of downloaded files (computed locally; no published SHA-256 exists to compare against):

```
ced1936c4f36ea79161579df8d4b23bb4862b9c88f30af9defeeb85af99adac4  pinder/index.parquet
3e3cfdc21d6c685891d6732edda13fea9d5566d056dfea56a2ae902ab80b4e6c  pinder/metadata.parquet
884052770ed6c2e8d7ae9d133f0fb5dd618eaacca6d57425d3e096143057d99c  pinder/test_set_pdbs.zip
4d21c63db04eb915fb656a3ed0a28f004a63e71a340098f6cecfd56b69cfc9d9  rcsb/6IHB.cif
5d8ad99cc6953dfe8499198db290650a66ef5322676566c2c565a14a1cb8a5d3  rcsb/6JCQ.cif
19af2cc309713ccd0f163802830ec9f02949446bb52202004e0e34ba2f4a3ae4  rcsb/6JCS.cif
```

How the downloads compare with published values:

- **Byte counts:** the three PINDER files match the Content-Length that intake recorded in every draw.
- **ETags:** these are S3 multipart ETags (`-2` suffix), not content hashes, so I could not compare them.
- **Test-set archive contents:** `unzip -l` lists 3,915 entries totalling 730,945,215 bytes uncompressed. The pinned `TEST_SET_PDB_FILE_COUNT = 3914` (pinder `src/pinder-core/pinder/core/utils/constants.py` at `ebeb28a2`) and the README's "0.73 GB test_set_pdbs" are consistent with this. The one-entry difference is probably the directory entry, but my directory-entry count was not permitted, so I have not confirmed it.
- **RCSB files:** the PDB publishes no checksums for these entries, and IDs do not pin a revision.

## 4. Resolved / not resolved

Resolved:
- **PINDER-S data (index, metadata, test structures) and the three AAV entries** are reachable now from this machine from official sources, with consistent sizes.
- **The difference between draws** comes from how each draw classified the FroDock 404, not from any change in reachability.

Not resolved:
- **FroDock archive:** I found no reachable official source, and its licence terms are also not established.
- **Per-case completeness of the 93 paired-apo cases:** not verified.
  - I could not run `unzip -t` or parse the parquet index; this session's tool permissions denied both commands.
  - PINDER's README says the archives omit some manifest files and that the API or `pinder_sync_data` fetches them, so full completeness depends on the PINDER API at run time.
  - `mappings.zip` (7.2 GB) and `pdbs.zip` (169 GB) were not downloaded.
- **GPU box:** reachability from the GPU box was not tested; the reproduce stage tests it.

## 5. Owner action

Either one of these:
1. **Obtain the FroDock archive and supply it.** Contact the Chacón lab, or follow whatever official channel the lab names, and accept its licence terms if required. Record the version and SHA-256 so intake and reproduce can pin it.
2. **Decide on a different, obtainable docking baseline.** That would change the study's comparator, so it is an owner decision. I did not propose a substitute.

I did not write a run5 brief addendum, because no confirmed official location exists for intake to use.
