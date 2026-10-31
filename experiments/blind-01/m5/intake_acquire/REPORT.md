# Materials acquisition report

Authorized reader for owner, 2026-10-31. Work began 02:22 UTC. All times below UTC. No outreach, redistribution, benchmark execution, GPU-box contact, installation, commit, push, or pipeline change.

## Result

**Materials remain unusable under required provenance rules.** Protein inputs pass integrity and completeness checks. Required FroDock distribution, including scoring input `bin/soap.bin`, remains available only as an **unverified mirror**. No qualifying replacement for this dependency established. `BRIEF_run5.md` not written.

New evidence beyond earlier reports:

- Recovered actual historical software licence text from official-site archive, with content digest matching CDX record. Licence ambiguity does not block this local experiment; provenance still does.
- Resolved both FroDock paper DOIs; retrieved author-hosted papers and publisher's 2016 supplement. Supplement contains one results document, no software/scoring package or distribution checksum.
- Checked latest PINDER preprint: bioRxiv API lists versions 1–4; DOI resolves to v4, dated 2024-08-13. Retrieved v4 full text and JATS. Supplement PDF request hit HTTP 429; stopped there.
- Expanded Wayback search to original 2009 institutional site, current domain's binary captures, complete downloads prefix, and old server hostname. Found v1.02 archive records; wrong version and scoring generation for recorded comparator. No qualifying 3-series archive found.
- Checked author repository history and upload trees, author's entire repository listing, and migrated website source. None supplies missing distribution.
- Re-downloaded protein index, metadata, test ZIP, AAV structures and publisher manifests. Rehashed all 3,590 previously retrieved structural/mapping files against fresh manifests: zero failures.
- Independently downloaded public mirror again: same SHA-256 as earlier reader. This proves continuity between reader downloads, not identity with official distribution.

`status.json` uses `prerequisite=data`: material dependency unresolved, licence evidence not blocking. `cause=source_moved` follows persistent official-path 404 and replacement documentation-only route. `alternative=unverified_mirror` records best complete fetchable candidate, rejected for run5; it does not certify a run5 source set.

## Scope and required inputs

Read [original brief](../BRIEF.md), [Opus report](../intake_check/REPORT.md), [Codex report including phases A/B](../intake_check_codex/REPORT.md), and relevant run4 intake records. Acquisition follows recorded [baseline](../run4/agent/intake/baseline.json) and [materials inventory](../run4/agent/intake/data.json), without changing comparator or benchmark. PINDER source pin remains `ebeb28a2f8411363cef722b7d293c978f7442672`.

Required materials:

1. PINDER 2024-02 index and metadata; all 250 PINDER-S native complexes and appropriate separated/apo/mapping inputs, prioritizing 93 primary paired-apo cases.
2. Original RCSB structures 6IHB, 6JCQ, 6JCS for separated-component redocking; no claim that these supply independently determined unbound structures.
3. Published PINDER software/evaluator and FroDock adapter at recorded commit.
4. External FroDock 3-series distribution expected by published Dockerfile and adapter, including compilation sources/scripts, required GNU/MPI tools, and `bin/soap.bin`.

Generated poses, potential maps and AAV component extraction are later study work, not missing downloadable source inputs. Seeds, case selection, anchors, candidate counts, scale, metrics and budget unchanged. No alternate docking method or old software release substituted.

## Candidates and provenance

| Candidate | Provenance considered | Evidence, differences, verdict |
| --- | --- | --- |
| Original protein distribution | Original official source, stronger than a relocation | [PINDER distribution](https://pinderdata.org/2024-02/index.parquet), [test ZIP](https://pinderdata.org/2024-02/test_set_pdbs.zip), and individual `pdbs/`, `mappings/`, `test_set_pdbs/` keys remain anonymously fetchable. Fresh manifest hashes match required files. These inputs have not moved. No replacement needed. |
| RCSB AAV entries | Original official source | [6IHB](https://files.rcsb.org/download/6IHB.cif), [6JCQ](https://files.rcsb.org/download/6JCQ.cif), [6JCS](https://files.rcsb.org/download/6JCS.cif) downloaded successfully and parsed. Current bytes equal both earlier readers' hashes. Entry IDs alone do not pin historical revisions; no historical-study byte identity invented. |
| PINDER source and PyPI packages | Original official source / registry route | [Pinned source](https://github.com/pinder-org/pinder/tree/ebeb28a2f8411363cef722b7d293c978f7442672) accessible; [PyPI 0.6.0 metadata](https://pypi.org/pypi/pinder/0.6.0/json) supplies wheel/sdist checksums, both verified after download. Wheel has adapter only; sdist has adapter and Dockerfile, no external FroDock binary/source distribution or `soap.bin`. Wheel/sdist containers differ from GitHub source archive; no claim of archive-byte equality. Registry packages not substituted for recorded source pin. |
| Dead FroDock distribution page | Original official source | [Named path](https://chaconlab.org/modeling/frodock/frodock-donwload) still HTTP 404, 13,631-byte body. Same persistent failure already established across four runs and earlier readers. Missing software remains required by [methods README](https://github.com/pinder-org/pinder/blob/ebeb28a2f8411363cef722b7d293c978f7442672/src/pinder-methods/pinder/methods/README.md). |
| Current lab tools page and author GitHub | `official_new_location` candidate | [Tools page](https://chaconlab.org/tools/) links to [chaconlab/FRODOCK](https://github.com/chaconlab/FRODOCK). Main commit `8bc416f66e6c0c0427576218d7c3336853906ed5`; sole branch main; tags/releases empty. Current tree has README, guide and images. History has 25 commits; initial and all three upload trees checked, also documentation/images only. No qualifying material replacement. |
| Author's other repositories and migrated website | `official_new_location` candidate | [Author repository listing](https://api.github.com/users/chaconlab/repos?per_page=100) returned 12 repositories, including [Website](https://github.com/chaconlab/Website). Website recursive tree has 158 entries, no FroDock package; its only FroDock-named asset is server image. No repository redirect or renamed software distribution established. |
| Author's current server / old institutional server hostname | `official_new_location` candidate | [frodock.iqf.csic.es](https://frodock.iqf.csic.es/) returns same server page as earlier `frodock.chaconlab.org` check. Service generates remote docking jobs; it does not supply locally controlled comparator package. No job submitted. Remote server would change execution and measurements. |
| FroDock PyPI, Anaconda, Hugging Face | `official_new_location` candidates | [PyPI](https://pypi.org/pypi/frodock/json) 404; [Anaconda search](https://api.anaconda.org/search?name=frodock) empty; [HF datasets](https://huggingface.co/api/datasets?search=frodock) and [models](https://huggingface.co/api/models?search=frodock) empty. No package/deposit found through these queries. |
| FroDock papers and publisher supplement | Official publication / potential `author_deposit` route | DOIs [2009](https://doi.org/10.1093/bioinformatics/btp447) and [2016](https://doi.org/10.1093/bioinformatics/btw141) resolve to publisher article paths; curl gets 403. Author-linked [2009 PDF](https://chaconlab.org/pdf/bioinf2009.pdf) and [2016 PDF](https://chaconlab.org/pdf/bioinf2016.pdf) fetched normally. Publisher's public 2016 supplement link retrieved successfully: ZIP with only `frodock_sup.docx`, no source, binary, scoring file or package checksum. Publications point to old institutional software site / docking server. |
| Latest PINDER paper and project | Official publication route | [bioRxiv version API](https://api.biorxiv.org/details/biorxiv/10.1101/2024.07.17.603980) confirms v4 latest among returned versions. [v4 full text](https://www.biorxiv.org/content/10.1101/2024.07.17.603980v4.full) and JATS retrieved; source link remains PINDER GitHub. [Project page](https://www.pinder.sh/) points to same code/docs. Supplement PDF request 429, not retried. No external FroDock identity checksum established from inspected material. |
| Official download-page Wayback capture | `archive_snapshot` of documentation | [Raw 2026-07-10 capture](https://web.archive.org/web/20260710163751id_/https://chaconlab.org/modeling/frodock/frodock-donwload) identifies release 3.12 (2020), filename and rounded size; no cryptographic package hash. Capture is HTML, not required archive. Download action tied to agreement acknowledgement; not invoked. |
| Broader Wayback official-domain search | `archive_snapshot` candidates | Successful CDX downloads-prefix query returned 53 records; domain binary-MIME query 254; old institutional FroDock-prefix query 20; old server-host query eight. No required 3-series software capture established. Download actions returned in CDX are HTML records, not program captures. Domain binary results include unrelated iMODFIT tar and FroDock fonts/JavaScript. CDX compressed record lengths are not package sizes. Initial 503s followed by successful normal retries, more than 60 seconds later. |
| Original institutional software page and old binaries | `archive_snapshot`, rejected version | [Archived 2010 page](https://web.archive.org/web/20100903044204id_/http://sbg.cib.csic.es:80/Software/FRODOCK/) describes v1.02 dated 2009-06-19. CDX lists 2009 captures of `down/frodock_lx_v1.02.tar.gz` and `down/frodock_lx_bin64_v1.02.tar.gz`. Binary captures not downloaded: wrong version, and page requests user details/source-code outreach. 2009 release precedes published scoring changes; equality with 3.12 and required scoring file unestablished. Cannot use these to preserve recorded measurements. |
| Software Heritage official origin/content | `archive_snapshot` of documentation | [Origin](https://archive.softwareheritage.org/api/1/origin/https://github.com/chaconlab/FRODOCK/get/) → snapshot `d2babf71b428e5286414d2fc89c8c4cd6ff4f708` → same author commit/root directory. Root README/guide/assets only. [Raw README by content hash](https://archive.softwareheritage.org/api/1/content/sha1_git:9529ba7b61171d4ce7d3caf235914fa119dd0586/raw/) fetched, 13,544 bytes, SHA-256 equals current official README. Searches for `chaconlab.org`, original `sbg.cib.csic.es`, and `frodock` found no software origin beyond documentation. This authenticates README, not software. |
| Institutional repositories | `author_deposit` candidates | [DIGITAL.CSIC search](https://digital.csic.es/simple-search?query=FRODOCK) returned publication records, including [2016 paper record](https://digital.csic.es/handle/10261/142002). That record lists only `accesoRestringido.pdf`, no program/scoring files. Other results concern papers/annual report, not qualifying distribution. Restricted attachment not requested. No qualifying author software deposit established. |
| Zenodo, DataCite and figshare | `author_deposit` candidates | [Zenodo public query](https://zenodo.org/api/records?q=frodock&size=20) and author query returned zero hits. [DataCite](https://api.datacite.org/dois?query=frodock) returned five DOI records, comprising third-party PPDbench versions/collection and interface-assessment work. [Figshare search](https://api.figshare.com/v2/articles/search) returned 12 records, mainly docking results/figures and other studies. None establishes FroDock-author deposit or official checksum for required distribution. No benchmark substituted. |
| Public GCS archive | `unverified_mirror` | [Independent Dockerfile](https://github.com/antonpp/frodock-on-gcp/blob/main/docker-build/Dockerfile) names [GCS tar](https://storage.googleapis.com/gke-dja-demo_static_assets/frodock3_linux64.tgz). Complete transfer, valid gzip/tar, expected files. No author/project endorsement, upstream checksum, matching official/archive/deposit copy, or study-recorded FroDock git pin. Rejected for usability. Details below. |
| Scipion public package | `unverified_mirror` candidate | [Package URL](https://scipion.cnb.csic.es/downloads/scipion/software/em/frodock3_linux64.tgz) timed out with no response/bytes. Exact Wayback CDX query empty. Earlier directory search snippets give filename, rounded size and date only. Shared institutional affiliation is not proof of author deposit. |
| Other docking wrappers | Third-party source-discovery routes | [PROTAC-Model](https://github.com/gaoqiweng/PROTAC-Model) and [Scipion PROTAC plugin](https://github.com/danigual/scipion-chem-protac) trees inspected. Plugin install recipe uses old official Joomla download action, explains stale-token HTML failure, and supplies no checksum. Recipe not executed; agreement action not followed. No independent authenticity proof. |
| SBGrid | Third-party distribution, gated and different versions | [Catalog](https://sbgrid.org/software/titles/frodock) lists 2.1, 2.0, 1.04. [Access page](https://sbgrid.org/software/access-software/) describes consortium installation. No login/installer used. Older versions and absent equality proof mean access alone would not establish required identity. |
| Public GCP container from earlier report | `unverified_mirror` candidate, inherited evidence | Earlier Codex report records Docker Hub image digest and Dockerfile fetching same GCS tar. Not pulled or executed here. Image digest identifies third-party container, not official program/scoring bytes. No promotion in provenance. |
| Compile/regenerate route | `regenerated_official`, not established | PINDER Dockerfile requires external archive then runs its `compile_frodock.sh`; it does not generate missing upstream source/scoring material. Author GitHub contains no published program source. Mirror compilation script uses mirror's local source. Recompiling unverified source cannot establish official identity. No official procedure plus published checks established for regenerating complete required 3-series software/scoring input. No compilation or benchmark run attempted. |

All negative findings bounded by inspected sources. No claim that an unsearched deposit cannot exist.

## Mirror integrity and unresolved identity

Fresh transfer: **2026-10-31 02:25:16.333672–02:25:17.972808 UTC**, HTTP 200, no login. Source exact URL:

`https://storage.googleapis.com/gke-dja-demo_static_assets/frodock3_linux64.tgz`

| Object | Bytes | SHA-256 |
| --- | ---: | --- |
| Archive | 26,637,000 | `91b9aeff747346046c7f8c4c92fa5749c9f082d8122ee9d2d4769855d35368f4` |
| `bin/frodock_mpi_gcc` | 7,169,224 | `90550be435ba2239d030d84f7bb0dc5ed033e038cf3a22a678353975a303d557` |
| `bin/soap.bin` | 7,536,604 | `791f31ec8ef1ef1466092b425638e926755519c9626f5678ca675ef6c76234fc` |

Archive MD5 `1b13acacf8288471ee7cb8e26e29c3ac`; SHA-1 `130e541f404bd506943c14b7d01620186308079f`. 542 tar members, 445 regular files, 65,507,120 uncompressed regular-file bytes. Gzip CRC passes; every regular member read. Required MPI/grid/clustering/view programs, compilation script, source and scoring file present. README self-identifies 3.12 dated 2020-02-08. No executable/script run.

Separate `src/frodockonstraint/Release_intel/soap.bin` differs: 3,014,640 bytes, SHA-256 `6c791aad8ef72a600a9388adfbfda83b4d998cc87023d00c70cf0f2a9bb06948`. Not substituted for `bin/soap.bin`.

Full member hashes: [mirror_verification.json](mirror_verification.json). These prove retrieved bytes and archive integrity only. Matching filename, version text, expected layout, rounded size, mirror MD5 header, two reader downloads, or third-party container digest do not meet requested identity proofs. No published checksum or matching level-1–3 package established. Unknown code/scoring differences could alter scientific results.

## Protein material verification

Fresh GETs completed 02:27:03–02:27:06 UTC. All six top-level scientific input hashes equal earlier readers' hashes; PINDER root files also equal publisher MD5 checksums.

| Input | Original official URL | Bytes | SHA-256 |
| --- | --- | ---: | --- |
| Index | `https://pinderdata.org/2024-02/index.parquet` | 124,511,839 | `ced1936c4f36ea79161579df8d4b23bb4862b9c88f30af9defeeb85af99adac4` |
| Metadata | `https://pinderdata.org/2024-02/metadata.parquet` | 103,835,983 | `3e3cfdc21d6c685891d6732edda13fea9d5566d056dfea56a2ae902ab80b4e6c` |
| Test ZIP | `https://pinderdata.org/2024-02/test_set_pdbs.zip` | 181,968,169 | `884052770ed6c2e8d7ae9d133f0fb5dd618eaacca6d57425d3e096143057d99c` |
| 6IHB | `https://files.rcsb.org/download/6IHB.cif` | 551,618 | `4d21c63db04eb915fb656a3ed0a28f004a63e71a340098f6cecfd56b69cfc9d9` |
| 6JCQ | `https://files.rcsb.org/download/6JCQ.cif` | 529,158 | `5d8ad99cc6953dfe8499198db290650a66ef5322676566c2c565a14a1cb8a5d3` |
| 6JCS | `https://files.rcsb.org/download/6JCS.cif` | 527,195 | `19af2cc309713ccd0f163802830ec9f02949446bb52202004e0e34ba2f4a3ae4` |

Index/metadata each 2,319,564 rows. Exactly 250 PINDER-S cases, 93 with both primary apo monomers; no missing PINDER-S metadata IDs. Test ZIP: 3,914 regular files plus directory, 730,945,215 uncompressed bytes, all CRCs pass. AAV entries parse with expected IDs and 4,868 / 4,809 / 4,880 atoms.

Fresh manifests from `https://pinderdata.org/2024-02/manifests/{root,pdbs,mappings,test_set_pdbs}.jsonl.gz` contain 18 / 3,826,764 / 1,448,950 / 3,914 entries. All **1,618** required structural/mapping files covering 250-case native/holo/available primary apo inputs, plus **1,972** additional default-API downloads for 93 prioritized cases, rehashed locally against those manifests: zero absent entries, size differences, MD5 differences or changes from earlier SHA-256 values. Predicted/alternative apo inputs were checked for downloader completeness, not substituted for primary paired apo inputs.

Individual-file network GETs are earlier reader evidence, not repeated here. Current pass uses their explicitly authorized inventory and cached bytes, independently rehashed against freshly fetched official manifests. Cache-only copies are not proposed sources: [per_file_evidence.json](per_file_evidence.json) lists exact original public URLs for every file. Original earlier transfer times remain in [earlier fetch ledger](../intake_check_codex/fetch_attempts.jsonl). Summary: [protein_verification.json](protein_verification.json).

No need to fetch optional 169-GB PDB or 7.2-GB mapping bulk containers; all required members individually located. Protein data is complete at currently published 2024-02 locations. This does not prove unspecified historical-study revision identity. No GPU-box reachability, executable compatibility, runtime or scientific reproduction claim follows from local HTTP/hash checks.

## Licence evidence as found

- Historical official [3.12 download page](https://web.archive.org/web/20260710163751id_/https://chaconlab.org/modeling/frodock/frodock-donwload) links `/downloads/License.txt` and makes Download action acknowledge agreement. Action not invoked.
- Current licence path returns 404. [Archived licence, 2016-02-15 20:57:24 UTC](https://web.archive.org/web/20160215205724id_/http://chaconlab.org:80/downloads/License.txt) retrieved 02:24:17 UTC: 1,580 bytes, SHA-256 `f0d7a714bafdc13882bf23c8c2abb469f0c40159bae464c436b41ecb25e9ba9e`. SHA-1 base32 `EEAUVAMLPGVE6UWDYFZ67JTZLGMWF6AJ` exactly matches CDX digest.
- Text carries CSIC copyright 2013, broad software permissions, source/binary notice requirements, endorsement restriction, and warranty/liability disclaimers. No SPDX label assigned. A 2016 capture cannot prove that text remained unchanged for 2020 release or every bundled component. Mirror has no separately named LICENSE/LICENCE/COPYING member. No redistribution undertaken, regardless of historical text.
- PINDER repository [LICENSE at recorded commit](https://github.com/pinder-org/pinder/blob/ebeb28a2f8411363cef722b7d293c978f7442672/LICENSE) is Apache License 2.0. This is code evidence; not relabelled as blanket licence for all hosted processed data or external FroDock.
- [wwPDB usage policy](https://www.wwpdb.org/about/usage-policies) places PDB archive data under CC0 1.0. Retrieved policy retained in cache.
- bioRxiv v4 metadata/source records CC-BY 4.0 for preprint; not treated as software/data distribution licence.
- Owner's standing authorization covers this local experiment despite ambiguity. It does not authorize redistribution or accepting third-party acquisition agreements. Licence ambiguity is not reason for `materials_usable=false`; missing authenticated software provenance is.

## Access limits and unsuccessful routes

Full HTTP attempt ledger below includes errors, timeouts, retries and HTTP-200 non-material pages. Notable limits:

- Publisher DOI requests return 403; no protected publisher path forced. Author-hosted PDFs and article's public supplement link used normally.
- Crossref 2016 metadata request returned 429. No retry or rate-limit workaround.
- Latest PINDER supplement PDF returned 429. No retry or alternate download route after that response.
- PMC 2009 article is readable, but supplementary URLs returned small JavaScript download-challenge HTML, not `.doc`/index contents. Challenge not executed, solved or bypassed; those responses not counted as downloaded supplements.
- Scipion transfer timed out after connection limit. No authentication or access bypass attempted.
- Zenodo request with `size=100` returned 400 explaining public limit 25; corrected to ordinary anonymous `size=20`. No account used. Local curl bracket-globbing error on DataCite request recorded; corrected with `--globoff`.
- DIGITAL.CSIC guessed modern API path 404; ordinary public search worked. Restricted publication attachment not requested.
- Wayback 503s were transient for two broad queries; later successful queries still found no qualifying 3-series software. Main software cause remains source relocation, not archive transient failure.

## What remains and owner action

Need **complete, authenticated required FroDock distribution plus scoring potential at an anonymously script-fetchable public location**. One of these would resolve material identity without changing study:

1. Official new location, author-deposited copy, or genuine archive capture of required distribution.
2. Authoritative published checksums/reference copy matching public mirror, covering required source/program/scoring bytes; mere version/name/size match insufficient.
3. Recorded study/upstream content-addressed pin plus matching accessible mirror, if one exists and is actually for required software.

Owner action is **supply_materials**: supply qualifying location/provenance evidence, not only a local attachment. Owner-held file alone cannot reach cloud box under pipeline constraint. If qualifying publisher route requires agreement/account/request, owner must handle access. No request sent and no material uploaded or re-hosted here. Older release or alternative comparator would change science; no such decision made.

Acquisition exhausted inspected ungated routes without authenticating missing dependency. No run5 addendum warranted. Original brief and run/intake records left unchanged. Downloads and extracted inspection text kept only under authorized cache; this output directory contains report, scripts and derived audit metadata, not redistributed scientific/software payloads.

## Audit files and discovery log

- [fetch_attempts.jsonl](fetch_attempts.jsonl): each new HTTP acquisition attempt, precise UTC start/end, URL/effective URL, result, bytes, SHA-256 and cache references.
- [FETCH_LEDGER.md](FETCH_LEDGER.md): same attempts rendered for review.
- [SEARCH_LOG.md](SEARCH_LOG.md): browser discovery queries/pages and conservative time brackets.
- [protein_verification.json](protein_verification.json), [per_file_evidence.json](per_file_evidence.json): fresh-manifest comparison and exact public structural/mapping URLs.
- [mirror_verification.json](mirror_verification.json): unverified package member hashes and layout checks.
- [pinder_package_verification.json](pinder_package_verification.json): both PyPI payload checksums against published registry metadata.
- [protected_inputs_sha256.json](protected_inputs_sha256.json): read-only checksums of protected brief/reports/intake records.
- [validation.json](validation.json): final schema, audit and output checks.

Source-discovery search results are leads, not package authenticity evidence. Browser result times before explicit query logging are reported as enclosing intervals, not invented exact timestamps. Every attempted payload acquisition in current pass is in HTTP ledger; earlier reader attempts remain separately attributed to their reports.
