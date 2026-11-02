# Authorized reader report: blind-01 materials for blind-02 run1


2026-11-02. All four sampled apo cases are identified; prepared CSV records and canonical input sources are pinned; all four native reference locations are pinned. All 85 inventoried remote files returned HTTP 200 to anonymous HEAD requests. The seed’s case count, kind and unit-probe description match the records. The requested MEGADOCK software pins are absent from the inspected run9 records, so software pin coverage is partial. FroDock distribution provenance remains `unverified_mirror`.


Only `b01_materials/` was written. No workload, installation, pipeline change, GPU-box contact, outreach, commit, push, upload or full-file network download occurred. Earlier cache files and blind-01 records were read without modification. No credential, `.keys` file or `~/.codex/` path was read.


## Source convention and trace

All `run*/...`, `intake*/...` source references below are relative to `/home/hal/dev/interp/metis/experiments/blind-01/m5/`. LF-based line numbers are used. `BRIEF.md` below means the blind-02 seed in the current directory. `records.json` preserves copied records, their byte hashes and the file inventory; `reachability.json` preserves every current check’s command method, start/end time, headers, HTTP result and curl result. These two evidence files are incorporated into this report.


Read the seed; run11’s unit manifest, unit/full wrappers, digest reference and concurrency summary; run10_harness3’s origin report and wrappers; run10_review3, run10_post, run10_post2, run11_post and run11_post2 REPORT.md files; intake_mirror’s brief, HASHES.tsv and report; run9 intake and harness records plus saved setup/CSV records. Selected cached PINDER source and test-ZIP member names were inspected locally, without fetching source or structures again.


## Cases, exact prepared records and references

The seed identifies the cases at `BRIEF.md:3`. Probe sample indices are 3, 5, 9 and 15 (`run11/agent/results/reproduce/out/concurrency/concurrency.json:6–24`). The corresponding manifest identities occur at the lines below. Wrapper selection preserves raw original header/record bytes (`run11/agent/harness/run_units.sh:119–146`). Origin and sample construction are documented at `run10_harness3/REPORT.md:45–51,72–78`, independently reviewed at `run10_review3/REPORT.md:98–147`. All three run11 files `units.json`, `run_units.sh` and `run_command.sh` byte-match run10_harness3’s copies.


| Unit identity | run11 manifest | run9 prepared CSV record | Canonical index-record copy |
| --- | --- | --- | --- |
| `1aua__A1_P24280--1aua__A2_P24280:apo` | `run11/agent/harness/units.json:172` | `run9/agent/results/reproduce/out/results/frodock_setup.csv:5` | `intake_check_codex/selected_cases.csv:3` |
| `1ax2__A1_P16404--1ax2__A2_P16404:apo` | `run11/agent/harness/units.json:284` | `run9/agent/results/reproduce/out/results/frodock_setup.csv:7` | `intake_check_codex/selected_cases.csv:4` |
| `1dv1__A1_P24182--1dv1__B1_P24182:apo` | `run11/agent/harness/units.json:508` | `run9/agent/results/reproduce/out/results/frodock_setup.csv:11` | `intake_check_codex/selected_cases.csv:6` |
| `1nr5__A1_P07547--1nr5__A2_P07547:apo` | `run11/agent/harness/units.json:844` | `run9/agent/results/reproduce/out/results/frodock_setup.csv:17` | `intake_check_codex/selected_cases.csv:9` |


Each source CSV record is 155 bytes including its terminating LF. Each per-case header-plus-record block is 179 bytes. Their exact hashes appear in the addendum and `records.json`. The ordered four-unit header-plus-records selection is 644 bytes, SHA-256 `f34c87e11bc77f02997f41aaae17cf6958ce02976b9621886d96c03029b27af0`, matching the previously recorded sample hash (`run10_harness3/REPORT.md:72`, `run10_review3/REPORT.md:147`). The preserved run10 subset list at `run10/agent/results/reproduce/units-check/files/results/frodock_setup.csv:1–5` supplies another retained copy.


The canonical source-file names are copied from the earlier index-derived CSV rows cited above. Their remote index source is the pinned `index.parquet`, with exact row selection by full `id` and canonical `apo_R_pdb`/`apo_L_pdb` fields. The PINDER archive’s `src/pinder-methods/pinder/methods/preprocess/__init__.py:30–55` reads `apo_receptor` and `apo_ligand` and writes the two prepared files; `src/pinder-core/pinder/core/index/system.py:198–240,767–790` loads those canonical monomer paths and assigns R/L chain labels. The preparation route does not call the separate native-alignment helpers. Run9’s setup command and manifest assembly are recorded in `run9/agent/harness/setup.sh:3975–4005`, with observed rows in saved `out/setup/setup.log:205,207,211,217`. No prepared remote structural tree was retained for independent new byte hashing; the exact copied artifacts here are prepared CSV records, plus the recorded canonical source pins and existing preparation route. Raw-source hashes are not represented as hashes of serialized prepared PDBs.


### `1aua__A1_P24280--1aua__A2_P24280:apo`

Canonical receptor `pdbs/6f0e__A1_P24280.pdb`; canonical ligand `pdbs/6f0e__A1_P24280.pdb`. Each is the complete source monomer, assigned the role in the copied record. Reference native: `pdbs/1aua__A1_P24280--1aua__A2_P24280.pdb`. Source bytes and SHA-256, copied from the named HASHES.tsv lines:


- `pdbs/6f0e__A1_P24280.pdb`: https://pinderdata.org/2024-02/pdbs/6f0e__A1_P24280.pdb; 192456 bytes; SHA-256 `622eacb7b46e1a4c25d16aa1c56a0546d1b23d31a41aad5c275886159f6d98cd`; source `blind-01/m5/intake_mirror/HASHES.tsv:2646`.

- `pdbs/1aua__A1_P24280--1aua__A2_P24280.pdb`: https://pinderdata.org/2024-02/pdbs/1aua__A1_P24280--1aua__A2_P24280.pdb; 388881 bytes; SHA-256 `a12fd5f7506b927c1d435464cabbb9cd59299fdc4a826b63302052b0fef41a48`; source `blind-01/m5/intake_mirror/HASHES.tsv:1630`.



### `1ax2__A1_P16404--1ax2__A2_P16404:apo`

Canonical receptor `pdbs/3n35__A1_P16404.pdb`; canonical ligand `pdbs/3n35__A1_P16404.pdb`. Each is the complete source monomer, assigned the role in the copied record. Reference native: `pdbs/1ax2__A1_P16404--1ax2__A2_P16404.pdb`. Source bytes and SHA-256, copied from the named HASHES.tsv lines:


- `pdbs/3n35__A1_P16404.pdb`: https://pinderdata.org/2024-02/pdbs/3n35__A1_P16404.pdb; 151794 bytes; SHA-256 `b39b7288e39983302280e4f83a69a3afbeee879fe2c0db13a8072c5c0e06090e`; source `blind-01/m5/intake_mirror/HASHES.tsv:2189`.

- `pdbs/1ax2__A1_P16404--1ax2__A2_P16404.pdb`: https://pinderdata.org/2024-02/pdbs/1ax2__A1_P16404--1ax2__A2_P16404.pdb; 300591 bytes; SHA-256 `111ed0e1daea9ff8575bb61a2184b5f58fedd5437846e0f8026bebb53ef77a10`; source `blind-01/m5/intake_mirror/HASHES.tsv:1633`.



### `1dv1__A1_P24182--1dv1__B1_P24182:apo`

Canonical receptor `pdbs/3g8c__A1_P24182.pdb`; canonical ligand `pdbs/3g8d__A1_P24182.pdb`. Each is the complete source monomer, assigned the role in the copied record. Reference native: `pdbs/1dv1__A1_P24182--1dv1__B1_P24182.pdb`. Source bytes and SHA-256, copied from the named HASHES.tsv lines:


- `pdbs/3g8c__A1_P24182.pdb`: https://pinderdata.org/2024-02/pdbs/3g8c__A1_P24182.pdb; 277182 bytes; SHA-256 `48aa5f4b2ac1e57d855b85d56a9c4a74c4b16f7d165b0fce03535815e26bdb60`; source `blind-01/m5/intake_mirror/HASHES.tsv:2134`.

- `pdbs/3g8d__A1_P24182.pdb`: https://pinderdata.org/2024-02/pdbs/3g8d__A1_P24182.pdb; 234657 bytes; SHA-256 `1f5320894a6ca42ffd58a164620e159cc6d95d21f978246b3f73f7620885f20c`; source `blind-01/m5/intake_mirror/HASHES.tsv:2135`.

- `pdbs/1dv1__A1_P24182--1dv1__B1_P24182.pdb`: https://pinderdata.org/2024-02/pdbs/1dv1__A1_P24182--1dv1__B1_P24182.pdb; 536625 bytes; SHA-256 `a159da5b6b145570b4d03ac9e17eb7b4315f7a8afd0497a93ad1f77a55debf3e`; source `blind-01/m5/intake_mirror/HASHES.tsv:1682`.



### `1nr5__A1_P07547--1nr5__A2_P07547:apo`

Canonical receptor `pdbs/1sg6__A1_P07547.pdb`; canonical ligand `pdbs/1sg6__A1_P07547.pdb`. Each is the complete source monomer, assigned the role in the copied record. Reference native: `pdbs/1nr5__A1_P07547--1nr5__A2_P07547.pdb`. Source bytes and SHA-256, copied from the named HASHES.tsv lines:


- `pdbs/1sg6__A1_P07547.pdb`: https://pinderdata.org/2024-02/pdbs/1sg6__A1_P07547.pdb; 234171 bytes; SHA-256 `4a7227a5777521835f4dcb9af450bf5f8be13ebbe10144ab4fdfa7eeb7900da5`; source `blind-01/m5/intake_mirror/HASHES.tsv:1812`.

- `pdbs/1nr5__A1_P07547--1nr5__A2_P07547.pdb`: https://pinderdata.org/2024-02/pdbs/1nr5__A1_P07547--1nr5__A2_P07547.pdb; 484785 bytes; SHA-256 `ee2fc49ec38f26a216154fd7ce0a93086f2ba60dde6997d86deb196bac96f861`; source `blind-01/m5/intake_mirror/HASHES.tsv:1777`.



Native reference use/path is corroborated by `run10_post/REPORT.md:57–64`, `run10_post2/REPORT.md:94–101`, and saved evaluator source `run10_review3/evidence/eval_method.py.txt:231–251`. The reference PDBs are direct files, not members of an archive; no reference content is copied.


## Seed match, prior examination and record discrepancies

No mismatch found in the seed’s four-case count, unbound/apo kind, or statement that the unit probe examined them. The unit universe contained sixteen jobs, from eight systems each in holo and apo pairings; the probe’s actual sample was four apo jobs (`run11/agent/results/reproduce/out/concurrency/concurrency.json:6–24`; `run9/agent/intake/EXECUTION.json:3–7`). The four are 1aua, 1ax2, 1dv1 and 1nr5, not the first four systems or all eight systems. Their apo monomer sources are distinct from their bound-case identifiers; three homomer cases reuse one canonical source in both roles.

The earlier probe was FroDock CPU/MPI concurrency, not a prior MEGADOCK CPU/GPU or denser-search experiment (`run11/agent/harness/run_units.sh:10–14,24–34,149–152`). The seed proposes the latter comparison; it does not claim blind-01 already performed it. Therefore this historical software difference is recorded as a pin gap, not a fabricated case-description mismatch.

Probe digest keys match exactly the union of the selected units’ 200 listed final PDB paths, fifty ranks per case (`run11/agent/results/reproduce/units_reference.json:3–202`). Prior reports explicitly limit comparison coverage: `run11_post/REPORT.md:9,34–36`; `run11_post2/REPORT.md:50–79`. The probe’s recorded match verdicts do not cover every scientific table/intermediate, and this reader ran no scientific check or evaluation.

A location discrepancy exists within the earlier intake: `run9/agent/intake/EXECUTION.json:11,15` and `data.json:28–38` describe native complexes/apo monomers as shipped in the test ZIP. Actual cached ZIP member names contain none of these four native complexes or five canonical apo sources; the eight listed separated holo files are present. Actual saved evaluator source resolves natives under `pdbs/`, and HASHES.tsv records direct native and apo URLs. The addendum records those direct locations and exact source hashes. This is not a mismatch in blind-02’s seed, which names no archive.


## Software and environment pins, with source records

The seed names MEGADOCK (`BRIEF.md:1,9–11,13`), PINDER (`:3`) and DockQ (`:17`). MEGADOCK has no occurrence in run9’s inspected intake directory, harness directory or saved reproduce setup records, including the saved package freeze. No MEGADOCK repository/package URL, commit, tag/release, build command, CPU/GPU build option or documented denser-rotation option can be copied from those records. No external settings search was performed. This is why `software_pins_recorded=partly`. A new MEGADOCK pin cannot be invented from FroDock evidence.

PINDER/DockQ code pin: `run9/agent/intake/baseline.json:2–6`, `benchmark.json:5,18,28`, `run9/agent/harness/setup.sh:29–38`, and `run9/agent/results/reproduce/out/setup/setup_record.json:2–5,35`. Repository `https://github.com/pinder-org/pinder`; commit `ebeb28a2f8411363cef722b7d293c978f7442672`; tree `adc153de2eef1ac428c1136d609b30728c88cc7b`; archive 22,835,334 bytes, SHA-256 `b577532820ebbe5c16432b78c5e9c197690e863cb70a0a35a8ebcbe5277b76dd` (`intake_mirror/HASHES.tsv:3102`). No release/tag recorded; the installed `0.0.0+gebeb28a2` was an SCM pretend version for an archive without Git metadata. DockQ was PINDER’s in-repository evaluator, not a separately pinned standalone DockQ package.

Build/install commands: published recipe in `run9/agent/intake/baseline.json:7–18`; actual setup’s source extraction at `run9/agent/harness/setup.sh:132–141`, patch application at `:208–213`, venv creation at `:252–257`, build tools at `:264–265`, PINDER install with no build isolation and SCM variables at `:275–276`, fire at `:278`, numpy constraint and dependency refresh at `:285–287`. The addendum copies the operative install lines as historical excerpts. Recorded fix patch hash `295af03d22550b21c1e0852f723f324c35e9f5caa75e1759ba82bee5ed0259c3` appears at `setup.sh:42`; patch content at `:143–206` and `run9/agent/harness/pinder_frodock_fixes.patch:1–64`. Output chain repair is in `run9/agent/harness/run_command.sh:126–174`.

FroDock historical baseline: `run9/agent/intake/baseline.json:2,5,12–16`; archive URL/hash at `run9/agent/harness/setup.sh:34–37`; actual build invocation `:215–226`; compiled/prebuilt fallback `:229–240`. Saved `out/setup/setup_record.json:6–15` records provenance `unverified_mirror`, all four required tools compiled, README version/date and SOAP hash. `out/setup/setup.log:19–26` records the observed build and tool hashes. The archive is 26,637,000 bytes, SHA-256 `91b9aeff747346046c7f8c4c92fa5749c9f082d8122ee9d2d4769855d35368f4` (`intake_mirror/HASHES.tsv:5`). No FroDock git commit or authenticated original release checksum was established.

The saved software environment is at `run9/agent/results/reproduce/out/setup/setup_record.json:24–35`: no new apt install, torch 2.7.0 from stock site-packages in both interpreters, distro CUDA paths, Open MPI 4.1.2, Xeon Platinum 8480+, 26 logical CPUs, Python 3.10.12 and installed PINDER version. CPU visibility and MPI/rank/prediction-count environment are in `run9/agent/harness/run_command.sh:22–33,45–48`. OS package list and conditional apt commands are at `run9/agent/harness/setup.sh:101–129`; observed installed-package state at saved `out/setup/setup.log:11–13`. No immutable actual base-image digest or complete OS dependency lock was found. This CUDA-layout evidence does not establish a MEGADOCK CUDA build.

Relevant saved freeze pins, with line references in `run9/agent/results/reproduce/out/setup/pip_freeze.txt`: biotite 1.2.0 (:17), fire 0.7.1 (:48), networkx 3.4.2 (:114), numpy 1.26.4 (:115), packaging 26.3 (:121), pandas 2.3.3 (:122), PINDER source install (:127), pyarrow 25.0.1 (:138), scikit-learn 1.7.2 (:168), setuptools-scm 10.3.4 (:172). They are observed environment records, not new dependency selections or a complete fetchable wheel lock.

Other implementation/build-option evidence: FroDock distribution contained prebuilt alternatives and run9 setup allowed fallback, but its saved record says all four required tools were compiled. Earlier README/compiler/version-label evidence appears at `intake_mirror/BRIEF_run5.md:54–59` and `REPORT.md:41–44`; it concerns FroDock, not MEGADOCK. The inspected run9 records say nothing about alternative MEGADOCK CPU/GPU implementations or standard/denser rotational builds. No recommendation is made.


## File inventory and current reachability

`HASHES.tsv` has exactly one row per inventoried fetchable file, 85 rows total; its source_record column gives each exact blind-01 inventory file/line. All byte counts and SHA-256 values were copied from `intake_mirror/HASHES.tsv`, with no full remote download or new payload checksum assertion. The addendum includes the same 85 URL/byte/hash/provenance tuples. It does not point to experiment-local sources or cache copies. FroDock distribution provenance remains `unverified_mirror`; all other inventory files retain `official_original_location`.

The inventory covers only these four index entries’ locations: four native complexes, five distinct canonical apo structures, eight separated holo structures, 36 residue-mapping files, and 27 default-API auxiliary structures; plus index, metadata, test-monomer ZIP and two software archives. Auxiliary filenames come from those same entries’ recorded apo alternatives/predicted names and the existing API path formulas (`run10_review3/evidence/core_index_utils.py.txt:695–762`; `run10_post/evidence/core_index_system.py.txt:613–647`). Auxiliary inventory is not an instruction to use alternative or predicted monomer pairings. It neither includes the other benchmark cases nor changes scientific scope.

`check_reachability.py` issued four parallel anonymous HTTPS HEAD requests at a time, using `curl -q -f -s -S -I -L --proto =https --proto-redir =https --connect-timeout 10 --max-time 30`. `-q` disables curl configuration loading. No cookies, authorization headers, login, acceptance action, access workaround or retry was supplied. All checks returned HTTP 200 with curl exit 0 and zero downloaded payload bytes. No access barriers or rate-limit responses occurred. All available final Content-Length headers match recorded byte counts; the source-archive response provides no Content-Length. Reachability does not establish current full-content equality, original identity or GPU-box connectivity.


| Input | Check started UTC | Check completed UTC | Result |
| --- | --- | --- | --- |
| `frodock_distribution:unverified_mirror` | 2026-11-02T16:07:43.800350+00:00 | 2026-11-02T16:07:44.007752+00:00 | HTTP 200; curl 0; payload 0 bytes |
| `index.parquet` | 2026-11-02T16:07:43.800675+00:00 | 2026-11-02T16:07:44.224415+00:00 | HTTP 200; curl 0; payload 0 bytes |
| `mappings/1aua__A1_P24280-R.parquet` | 2026-11-02T16:07:43.801057+00:00 | 2026-11-02T16:07:44.208062+00:00 | HTTP 200; curl 0; payload 0 bytes |
| `mappings/1aua__A2_P24280-L.parquet` | 2026-11-02T16:07:43.801326+00:00 | 2026-11-02T16:07:44.195741+00:00 | HTTP 200; curl 0; payload 0 bytes |
| `mappings/1ax2__A1_P16404-R.parquet` | 2026-11-02T16:07:44.007805+00:00 | 2026-11-02T16:07:44.278880+00:00 | HTTP 200; curl 0; payload 0 bytes |
| `mappings/1ax2__A2_P16404-L.parquet` | 2026-11-02T16:07:44.195792+00:00 | 2026-11-02T16:07:44.449497+00:00 | HTTP 200; curl 0; payload 0 bytes |
| `mappings/1dv1__A1_P24182-R.parquet` | 2026-11-02T16:07:44.208111+00:00 | 2026-11-02T16:07:44.509525+00:00 | HTTP 200; curl 0; payload 0 bytes |
| `mappings/1dv1__B1_P24182-L.parquet` | 2026-11-02T16:07:44.224476+00:00 | 2026-11-02T16:07:44.521255+00:00 | HTTP 200; curl 0; payload 0 bytes |
| `mappings/1dv2__A1_P24182.parquet` | 2026-11-02T16:07:44.278973+00:00 | 2026-11-02T16:07:44.544390+00:00 | HTTP 200; curl 0; payload 0 bytes |
| `mappings/1nr5__A1_P07547-R.parquet` | 2026-11-02T16:07:44.449541+00:00 | 2026-11-02T16:07:44.714713+00:00 | HTTP 200; curl 0; payload 0 bytes |
| `mappings/1nr5__A2_P07547-L.parquet` | 2026-11-02T16:07:44.509584+00:00 | 2026-11-02T16:07:44.796258+00:00 | HTTP 200; curl 0; payload 0 bytes |
| `mappings/1sg6__A1_P07547.parquet` | 2026-11-02T16:07:44.521302+00:00 | 2026-11-02T16:07:44.808786+00:00 | HTTP 200; curl 0; payload 0 bytes |
| `mappings/2gps__A1_P24182.parquet` | 2026-11-02T16:07:44.544441+00:00 | 2026-11-02T16:07:44.833243+00:00 | HTTP 200; curl 0; payload 0 bytes |
| `mappings/2gpw__A1_P24182.parquet` | 2026-11-02T16:07:44.714761+00:00 | 2026-11-02T16:07:44.978375+00:00 | HTTP 200; curl 0; payload 0 bytes |
| `mappings/2j9g__A1_P24182.parquet` | 2026-11-02T16:07:44.796302+00:00 | 2026-11-02T16:07:45.056683+00:00 | HTTP 200; curl 0; payload 0 bytes |
| `mappings/2v58__A1_P24182.parquet` | 2026-11-02T16:07:44.808837+00:00 | 2026-11-02T16:07:45.044919+00:00 | HTTP 200; curl 0; payload 0 bytes |
| `mappings/2v59__A1_P24182.parquet` | 2026-11-02T16:07:44.833292+00:00 | 2026-11-02T16:07:45.064071+00:00 | HTTP 200; curl 0; payload 0 bytes |
| `mappings/2v5a__A1_P24182.parquet` | 2026-11-02T16:07:44.978443+00:00 | 2026-11-02T16:07:45.229977+00:00 | HTTP 200; curl 0; payload 0 bytes |
| `mappings/2vr1__A1_P24182.parquet` | 2026-11-02T16:07:45.044977+00:00 | 2026-11-02T16:07:45.336678+00:00 | HTTP 200; curl 0; payload 0 bytes |
| `mappings/2w6m__A1_P24182.parquet` | 2026-11-02T16:07:45.056744+00:00 | 2026-11-02T16:07:45.305305+00:00 | HTTP 200; curl 0; payload 0 bytes |
| `mappings/2w6n__A1_P24182.parquet` | 2026-11-02T16:07:45.064122+00:00 | 2026-11-02T16:07:45.325338+00:00 | HTTP 200; curl 0; payload 0 bytes |
| `mappings/2w6o__A1_P24182.parquet` | 2026-11-02T16:07:45.230022+00:00 | 2026-11-02T16:07:45.520218+00:00 | HTTP 200; curl 0; payload 0 bytes |
| `mappings/2w6p__A1_P24182.parquet` | 2026-11-02T16:07:45.305370+00:00 | 2026-11-02T16:07:45.580425+00:00 | HTTP 200; curl 0; payload 0 bytes |
| `mappings/2w6q__A1_P24182.parquet` | 2026-11-02T16:07:45.325401+00:00 | 2026-11-02T16:07:45.593335+00:00 | HTTP 200; curl 0; payload 0 bytes |
| `mappings/2w6z__A1_P24182.parquet` | 2026-11-02T16:07:45.336741+00:00 | 2026-11-02T16:07:45.601285+00:00 | HTTP 200; curl 0; payload 0 bytes |
| `mappings/2w70__A1_P24182.parquet` | 2026-11-02T16:07:45.520292+00:00 | 2026-11-02T16:07:45.747707+00:00 | HTTP 200; curl 0; payload 0 bytes |
| `mappings/2w71__A1_P24182.parquet` | 2026-11-02T16:07:45.580485+00:00 | 2026-11-02T16:07:45.825349+00:00 | HTTP 200; curl 0; payload 0 bytes |
| `mappings/3g8c__A1_P24182.parquet` | 2026-11-02T16:07:45.593413+00:00 | 2026-11-02T16:07:45.868117+00:00 | HTTP 200; curl 0; payload 0 bytes |
| `mappings/3g8d__A1_P24182.parquet` | 2026-11-02T16:07:45.601348+00:00 | 2026-11-02T16:07:45.792709+00:00 | HTTP 200; curl 0; payload 0 bytes |
| `mappings/3n35__A1_P16404.parquet` | 2026-11-02T16:07:45.747781+00:00 | 2026-11-02T16:07:45.972480+00:00 | HTTP 200; curl 0; payload 0 bytes |
| `mappings/3n36__A1_P16404.parquet` | 2026-11-02T16:07:45.792782+00:00 | 2026-11-02T16:07:46.068227+00:00 | HTTP 200; curl 0; payload 0 bytes |
| `mappings/3n3h__A1_P16404.parquet` | 2026-11-02T16:07:45.825412+00:00 | 2026-11-02T16:07:46.135944+00:00 | HTTP 200; curl 0; payload 0 bytes |
| `mappings/6f0e__A1_P24280.parquet` | 2026-11-02T16:07:45.868189+00:00 | 2026-11-02T16:07:46.173238+00:00 | HTTP 200; curl 0; payload 0 bytes |
| `mappings/7zg9__A1_P24280.parquet` | 2026-11-02T16:07:45.972539+00:00 | 2026-11-02T16:07:46.238764+00:00 | HTTP 200; curl 0; payload 0 bytes |
| `mappings/7zga__A1_P24280.parquet` | 2026-11-02T16:07:46.068288+00:00 | 2026-11-02T16:07:46.455556+00:00 | HTTP 200; curl 0; payload 0 bytes |
| `mappings/7zgb__A1_P24280.parquet` | 2026-11-02T16:07:46.136023+00:00 | 2026-11-02T16:07:46.474270+00:00 | HTTP 200; curl 0; payload 0 bytes |
| `mappings/7zgc__A1_P24280.parquet` | 2026-11-02T16:07:46.173288+00:00 | 2026-11-02T16:07:46.420722+00:00 | HTTP 200; curl 0; payload 0 bytes |
| `mappings/7zgd__A1_P24280.parquet` | 2026-11-02T16:07:46.238831+00:00 | 2026-11-02T16:07:46.505958+00:00 | HTTP 200; curl 0; payload 0 bytes |
| `metadata.parquet` | 2026-11-02T16:07:46.420774+00:00 | 2026-11-02T16:07:46.752796+00:00 | HTTP 200; curl 0; payload 0 bytes |
| `pdbs/1aua__A1_P24280--1aua__A2_P24280.pdb` | 2026-11-02T16:07:46.455610+00:00 | 2026-11-02T16:07:46.761443+00:00 | HTTP 200; curl 0; payload 0 bytes |
| `pdbs/1ax2__A1_P16404--1ax2__A2_P16404.pdb` | 2026-11-02T16:07:46.474320+00:00 | 2026-11-02T16:07:46.814913+00:00 | HTTP 200; curl 0; payload 0 bytes |
| `pdbs/1dv1__A1_P24182--1dv1__B1_P24182.pdb` | 2026-11-02T16:07:46.506041+00:00 | 2026-11-02T16:07:46.730485+00:00 | HTTP 200; curl 0; payload 0 bytes |
| `pdbs/1dv2__A1_P24182.pdb` | 2026-11-02T16:07:46.730531+00:00 | 2026-11-02T16:07:47.014836+00:00 | HTTP 200; curl 0; payload 0 bytes |
| `pdbs/1nr5__A1_P07547--1nr5__A2_P07547.pdb` | 2026-11-02T16:07:46.752844+00:00 | 2026-11-02T16:07:47.077968+00:00 | HTTP 200; curl 0; payload 0 bytes |
| `pdbs/1sg6__A1_P07547.pdb` | 2026-11-02T16:07:46.761493+00:00 | 2026-11-02T16:07:47.022679+00:00 | HTTP 200; curl 0; payload 0 bytes |
| `pdbs/2gps__A1_P24182.pdb` | 2026-11-02T16:07:46.814985+00:00 | 2026-11-02T16:07:47.051142+00:00 | HTTP 200; curl 0; payload 0 bytes |
| `pdbs/2gpw__A1_P24182.pdb` | 2026-11-02T16:07:47.014930+00:00 | 2026-11-02T16:07:47.373182+00:00 | HTTP 200; curl 0; payload 0 bytes |
| `pdbs/2j9g__A1_P24182.pdb` | 2026-11-02T16:07:47.022740+00:00 | 2026-11-02T16:07:47.611116+00:00 | HTTP 200; curl 0; payload 0 bytes |
| `pdbs/2v58__A1_P24182.pdb` | 2026-11-02T16:07:47.052868+00:00 | 2026-11-02T16:07:47.419480+00:00 | HTTP 200; curl 0; payload 0 bytes |
| `pdbs/2v59__A1_P24182.pdb` | 2026-11-02T16:07:47.078025+00:00 | 2026-11-02T16:07:47.424662+00:00 | HTTP 200; curl 0; payload 0 bytes |
| `pdbs/2v5a__A1_P24182.pdb` | 2026-11-02T16:07:47.373241+00:00 | 2026-11-02T16:07:47.636619+00:00 | HTTP 200; curl 0; payload 0 bytes |
| `pdbs/2vr1__A1_P24182.pdb` | 2026-11-02T16:07:47.419531+00:00 | 2026-11-02T16:07:47.650937+00:00 | HTTP 200; curl 0; payload 0 bytes |
| `pdbs/2w6m__A1_P24182.pdb` | 2026-11-02T16:07:47.424709+00:00 | 2026-11-02T16:07:47.723679+00:00 | HTTP 200; curl 0; payload 0 bytes |
| `pdbs/2w6n__A1_P24182.pdb` | 2026-11-02T16:07:47.611180+00:00 | 2026-11-02T16:07:48.111243+00:00 | HTTP 200; curl 0; payload 0 bytes |
| `pdbs/2w6o__A1_P24182.pdb` | 2026-11-02T16:07:47.636677+00:00 | 2026-11-02T16:07:47.919895+00:00 | HTTP 200; curl 0; payload 0 bytes |
| `pdbs/2w6p__A1_P24182.pdb` | 2026-11-02T16:07:47.651018+00:00 | 2026-11-02T16:07:47.972680+00:00 | HTTP 200; curl 0; payload 0 bytes |
| `pdbs/2w6q__A1_P24182.pdb` | 2026-11-02T16:07:47.723723+00:00 | 2026-11-02T16:07:47.967674+00:00 | HTTP 200; curl 0; payload 0 bytes |
| `pdbs/2w6z__A1_P24182.pdb` | 2026-11-02T16:07:47.919952+00:00 | 2026-11-02T16:07:48.211848+00:00 | HTTP 200; curl 0; payload 0 bytes |
| `pdbs/2w70__A1_P24182.pdb` | 2026-11-02T16:07:47.967719+00:00 | 2026-11-02T16:07:48.183085+00:00 | HTTP 200; curl 0; payload 0 bytes |
| `pdbs/2w71__A1_P24182.pdb` | 2026-11-02T16:07:47.972731+00:00 | 2026-11-02T16:07:48.231058+00:00 | HTTP 200; curl 0; payload 0 bytes |
| `pdbs/3g8c__A1_P24182.pdb` | 2026-11-02T16:07:48.111289+00:00 | 2026-11-02T16:07:48.431096+00:00 | HTTP 200; curl 0; payload 0 bytes |
| `pdbs/3g8d__A1_P24182.pdb` | 2026-11-02T16:07:48.183133+00:00 | 2026-11-02T16:07:48.419566+00:00 | HTTP 200; curl 0; payload 0 bytes |
| `pdbs/3n35__A1_P16404.pdb` | 2026-11-02T16:07:48.211901+00:00 | 2026-11-02T16:07:48.479222+00:00 | HTTP 200; curl 0; payload 0 bytes |
| `pdbs/3n36__A1_P16404.pdb` | 2026-11-02T16:07:48.231118+00:00 | 2026-11-02T16:07:48.504573+00:00 | HTTP 200; curl 0; payload 0 bytes |
| `pdbs/3n3h__A1_P16404.pdb` | 2026-11-02T16:07:48.419612+00:00 | 2026-11-02T16:07:48.681641+00:00 | HTTP 200; curl 0; payload 0 bytes |
| `pdbs/6f0e__A1_P24280.pdb` | 2026-11-02T16:07:48.431143+00:00 | 2026-11-02T16:07:48.692376+00:00 | HTTP 200; curl 0; payload 0 bytes |
| `pdbs/7zg9__A1_P24280.pdb` | 2026-11-02T16:07:48.479266+00:00 | 2026-11-02T16:07:48.792651+00:00 | HTTP 200; curl 0; payload 0 bytes |
| `pdbs/7zga__A1_P24280.pdb` | 2026-11-02T16:07:48.504691+00:00 | 2026-11-02T16:07:48.781602+00:00 | HTTP 200; curl 0; payload 0 bytes |
| `pdbs/7zgb__A1_P24280.pdb` | 2026-11-02T16:07:48.681699+00:00 | 2026-11-02T16:07:49.082121+00:00 | HTTP 200; curl 0; payload 0 bytes |
| `pdbs/7zgc__A1_P24280.pdb` | 2026-11-02T16:07:48.692421+00:00 | 2026-11-02T16:07:48.937027+00:00 | HTTP 200; curl 0; payload 0 bytes |
| `pdbs/7zgd__A1_P24280.pdb` | 2026-11-02T16:07:48.781651+00:00 | 2026-11-02T16:07:49.065859+00:00 | HTTP 200; curl 0; payload 0 bytes |
| `pdbs/af__P07547.pdb` | 2026-11-02T16:07:48.792697+00:00 | 2026-11-02T16:07:48.980476+00:00 | HTTP 200; curl 0; payload 0 bytes |
| `pdbs/af__P16404.pdb` | 2026-11-02T16:07:48.937074+00:00 | 2026-11-02T16:07:49.209712+00:00 | HTTP 200; curl 0; payload 0 bytes |
| `pdbs/af__P24182.pdb` | 2026-11-02T16:07:48.980534+00:00 | 2026-11-02T16:07:49.269472+00:00 | HTTP 200; curl 0; payload 0 bytes |
| `pdbs/af__P24280.pdb` | 2026-11-02T16:07:49.065928+00:00 | 2026-11-02T16:07:49.275847+00:00 | HTTP 200; curl 0; payload 0 bytes |
| `pinder_source@ebeb28a2f8411363cef722b7d293c978f7442672` | 2026-11-02T16:07:49.082189+00:00 | 2026-11-02T16:07:49.312427+00:00 | HTTP 200; curl 0; payload 0 bytes |
| `test_set_pdbs.zip` | 2026-11-02T16:07:49.209759+00:00 | 2026-11-02T16:07:49.413702+00:00 | HTTP 200; curl 0; payload 0 bytes |
| `test_set_pdbs/1aua__A1_P24280-R.pdb` | 2026-11-02T16:07:49.269524+00:00 | 2026-11-02T16:07:49.476820+00:00 | HTTP 200; curl 0; payload 0 bytes |
| `test_set_pdbs/1aua__A2_P24280-L.pdb` | 2026-11-02T16:07:49.275918+00:00 | 2026-11-02T16:07:49.525399+00:00 | HTTP 200; curl 0; payload 0 bytes |
| `test_set_pdbs/1ax2__A1_P16404-R.pdb` | 2026-11-02T16:07:49.312470+00:00 | 2026-11-02T16:07:49.519350+00:00 | HTTP 200; curl 0; payload 0 bytes |
| `test_set_pdbs/1ax2__A2_P16404-L.pdb` | 2026-11-02T16:07:49.413750+00:00 | 2026-11-02T16:07:49.695702+00:00 | HTTP 200; curl 0; payload 0 bytes |
| `test_set_pdbs/1dv1__A1_P24182-R.pdb` | 2026-11-02T16:07:49.476873+00:00 | 2026-11-02T16:07:49.696382+00:00 | HTTP 200; curl 0; payload 0 bytes |
| `test_set_pdbs/1dv1__B1_P24182-L.pdb` | 2026-11-02T16:07:49.519394+00:00 | 2026-11-02T16:07:49.921632+00:00 | HTTP 200; curl 0; payload 0 bytes |
| `test_set_pdbs/1nr5__A1_P07547-R.pdb` | 2026-11-02T16:07:49.525448+00:00 | 2026-11-02T16:07:49.804990+00:00 | HTTP 200; curl 0; payload 0 bytes |
| `test_set_pdbs/1nr5__A2_P07547-L.pdb` | 2026-11-02T16:07:49.695824+00:00 | 2026-11-02T16:07:49.938439+00:00 | HTTP 200; curl 0; payload 0 bytes |


## Licence evidence as found

Evidence is copied from `intake_mirror/REPORT.md:56–64` and run9 intake records; no new licence search or permission determination was performed. Ambiguity does not block this local experiment under the owner’s instructions.

- Historical FroDock text: the earlier reader’s 2016 archived official licence-text capture was 1,580 bytes, SHA-256 `f0d7a714bafdc13882bf23c8c2abb469f0c40159bae464c436b41ecb25e9ba9e`; the report records CSIC copyright 2013, a grant, source/binary notice clauses, a non-endorsement clause and warranty/liability exclusions. That capture does not establish the text governing a 2020 package or all bundled components. The download-page action was not invoked. The FroDock distribution with provenance `unverified_mirror` has no member named LICENSE, LICENCE or COPYING (`intake_mirror/REPORT.md:60–61`).
- PINDER repository LICENSE text was recorded as Apache License 2.0; that evidence concerns repository code, not blanket coverage for hosted processed data or external FroDock (`intake_mirror/REPORT.md:62`).
- The earlier cached wwPDB usage-policy page said PDB archive data were under CC0 1.0; that does not establish processed PINDER data coverage or historical structural revisions (`intake_mirror/REPORT.md:63`).
- The PINDER preprint v4 metadata/source carried CC-BY 4.0; that publication label was not transferred to software/data. Hosted processed-data coverage, historical FroDock-text applicability and bundled components remain unresolved (`intake_mirror/REPORT.md:64`). Run9 `agent/intake/data.json:13–14,24–25,37–38,48–50,59–60` records data licence as unknown, including earlier HTTP 404 for the distribution’s LICENSE location.
- No MEGADOCK licence evidence occurs in the inspected run9 records. Nothing was uploaded, published, re-hosted or shared.


## Remaining limits and outcome

MEGADOCK pins, CPU/GPU build alternatives and the documented denser-sampling option cannot be established from the permitted records. The addendum explicitly records that absence. Scientific configuration, tolerances, comparisons, budgets and pipeline-contract assessment remain solely the seed’s task; this reader made no such decisions and added no checks. Run9’s actual prepared PDB byte hashes are unavailable in the retained structural tree; the copied prepared input records, their canonical source hashes and recorded source preparation route are established. No claim of new bit-for-bit prepared-structure verification is made.

The FroDock distribution’s provenance remains `unverified_mirror`; identity with the original remains unresolved. Agreement with published-value anchors measures only their properties and does not authenticate the copy. HEAD reachability is not payload revalidation. No new scientific result is established. Licence ambiguity remains recorded solely here, with no assertion in the addendum.

`BRIEF_run1.md` was written because every case was identified and every inventoried input/reference location was reachable. Its initial bytes equal the seed exactly. Owner action for this materials-copy task is `none`: no material/access problem or new study decision was invented; software absence is disclosed for the seed’s subsequent work. The completed inventory does not claim to pin future software/dependency downloads not named in the old records.


Mechanical validation is recorded in `validation.json`: exact seed prefix, four exact owner quotations, four byte-exact CSV blocks, equality with the independent retained run10 sample list, all 85 inventory tuples and source-record line references, all 85 anonymous HEAD successes with zero payload bytes, literal install-excerpt parity with run9, absence of experiment/cache pointers in the addendum, and exact status keys/enums. These are materials/output checks, not additional scientific checks.
