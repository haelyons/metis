# Browser discovery audit

2026-10-31 UTC. Search queries discover leads only. Reachability, identity and completeness decisions use separately logged direct HTTP acquisitions. No search snippet treated as file checksum or successful download.

Initial browser calls were not individually timestamped to disk. Enclosing interval **02:22:17–02:30:38 UTC** covers all browser calls below; exact call seconds not invented. Later calls also have tool-clock records and raw tool responses in authorized cache: `acquire/web09.json`, `web10.json`, `web12.json`. Labels below preserve invocation order, not exact timestamps.

| Batch | Queries / pages | Result used |
| --- | --- | --- |
| 0 | `FRODOCK 3.12 download chaconlab github source`; `"frodock3_linux64" checksum archive`; `FRODOCK 3.0 paper software supplementary download` | Author docs and dead download page; Scipion mirror lead; papers. |
| 1 | `"FRODOCK" "3.12"`; `"frodock3_linux64.tgz"`; `"FRODOCK" github Chacon Lopez Blanco download`; `"FRODOCK" Zenodo figshare software` | Same official page/version and Scipion; third-party PPDbench deposit. No upstream package hash. |
| 2 | `FRODOCK site:github.com "soap.bin"`; `FRODOCK site:github.com "compile_frodock.sh"`; `FRODOCK "download" "López-Blanco" software source code`; `"frodock" "sha256"` | Official methods papers/docs; no qualifying source/checksum found. |
| 3 | `PINDER FroDock docker image github ghcr`; `"frodock" "supplementary" "btw141"`; `"frodock" "arxiv"`; `"frodock" "deposit" software` | No authenticated public container established. Papers point to supplementary data. |
| 3 pages | Opened both publisher article paths `https://academic.oup.com/bioinformatics/article/32/15/2386/1743604` and `/25/19/2544/180723` | 2016 public article text accessible through tool's ordinary publisher-CDN redirect; 2009 open failed. |
| 4 | Found `Supplementary`, `.zip`, `Availability` within 2016 article view | Same public article/availability information; supplementary link identified. |
| 5 | Clicked publisher 2016 supplementary link | Browser fetch reported cache miss; exact public link subsequently retrieved by logged curl as `frodock2016_supplement`. No URL signature forged or changed. |
| 6 | `"FRODOCK" site:digital.csic.es`; `"FRODOCK" site:figshare.com`; `"FRODOCK" site:zenodo.org "Chacon"`; `"FRODOCK" "download" "3.0" software archive` | No qualifying author program deposit established; direct repository/API checks followed. |
| 7 | `"frodock3_linux64" -site:scipion.cnb.csic.es -site:chaconlab.org`; `"frodock" "1b13acacf8288471ee7cb8e26e29c3ac"`; `"frodock" "91b9aeff747346"`; `"FRODOCK" "López-Blanco" "github.com"` | No authoritative checksum source established. No reported identity proof from search absence. |
| 8 | `"FRODOCK" site:digital.csic.es "2016"`; `"frodock3_linux64.tgz" md5 checksum`; `"frodock" "sourceforge"`; `"frodock" "conda-forge"` | Scipion listing remained lead; no qualifying registry package or checksum found. |
| 9 | `"FRODOCK" "scipion" github`; `"frodock3" github`; `"frodock" "sha" checksum md5`; `"frodock3_linux64" download source` | Third-party wrapper/dependency lead; direct GitHub trees/readmes inspected separately. |
| 10 | Opened 2009 DOI; searched `"btw141" "s0.zip"`; `"btp447" "supplementary" "zip"`; `"FRODOCK" "digital.csic.es" Ramírez` | DOI browser open failed. Primary literature references established PMC article availability, later queried through Europe PMC/PMC. |
| 11 | Reopened 2009 publisher article | Tool failed publisher-CDN open again. Author-hosted PDF already available; no protected access forced. |
| 12 | `PINDER Protein INteraction Dataset Evaluation Resource paper doi preprint`; `"PMC2800348" "supplement"`; `"btp447" "supplementary_data"` | PINDER preprint DOI and project page identified. Direct bioRxiv metadata then confirmed latest v4. |

Primary-source checks and payload attempts have precise UTC timestamps in [fetch_attempts.jsonl](fetch_attempts.jsonl). Other search results were background leads, not accepted material sources. No browser outreach, form submission, login, challenge solving or docking job.
