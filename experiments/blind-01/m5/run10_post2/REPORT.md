Run10 second post-check — 2026-11-02

All subset error classes also occur in run9. MPI abort messages have identifiable program cause: successful VdW/electrostatic grid branch calls `exit(1)` after writing map and finalizing MPI. Four sample units were computed; their 200 final PDBs match both their own retained temporary models and run9. All 24 retained numerical intermediates also match run9. Exhaustive outside-output write inventory, and consequently complete minimal-copy isolation guarantee, remain unestablished.

Read `run10_post/REPORT.md` first, then requested harness3/differential reports and relevant harness/source/records. No workload, harness invocation, box contact, network fetch, git command, credential, `.keys`, or `~/.codex/` read. All authored files under `run10_post2/`. Executed only local standard-library record/source audit. Large result trees inspected by sample manifest paths and four logged temporary directory names.

References relative to experiment directory unless absolute. `U` = `run10/agent/harness/run_units.sh`; `L` = `run10/agent/results/reproduce/units-check/run.log`; `R` = `run9/agent/results/reproduce/out/run_command/run_command.log`; `F` = `run10/agent/results/reproduce/units-check/files/`; `E` = `run10_post2/evidence/`. Log line numbers count LF separators, retaining embedded CR progress updates. `PIPE` = `/home/hal/dev/interp/metis/dut/pipeline/m5/pipeline.js`; `SCHEMAS` = same directory's `SCHEMAS.md`.

Source provenance checked independently: cached Pinder and FroDock archive hashes equal run10 setup record (`run10/agent/results/reproduce/out/setup/setup_record.json:2–6`). Selected source members preserved with hashes in `audit.json`. Applied patch equals run9 harness patch. `E/main_patched.py.txt` and `E/predict_patched.py.txt` reconstruct pinned source plus that exact patch, checking every context/deleted line; reconstructed line numbers agree with runtime trace. These are source reconstructions, not newly fetched installed files (`audit.py:20–88`). Run10 setup records patch application and compiled grid binary (`out/setup/setup.log:422–431` beneath run10 reproduce results).

**A. Error kinds, origin, and output consequences**

| Diagnostic | Subset | Run9 final full run | Cause |
| --- | ---: | ---: | --- |
| Python logging failure / formatting TypeError | 4 | 16, one per unit | `log.info("OUT", output_dir)` has argument but no format placeholder. Logging handler reports failure; control continues. |
| MPI abort diagnostic, exit code 1 | 8 | 32, two per unit | Native grid success branch returns failure status after producing VdW/electrostatic map. |
| Missing-system evaluator ERROR records | 18 | 18 | Both evaluate small selected sets against complete benchmark populations. Restricted subset increases four missing counts. |
| Ligand-size warnings | 24 | 104 | Geometry advisory; warning branch only prints. |
| Biotite element-guess warnings | 4 | 15 | PDB reader infers omitted elements from atom names. Same warning for all four corresponding run9 units. |

All four corresponding unit blocks contain same logging/MPI/warning patterns. Exact block references:

| Apo unit | Subset L block | Run9 R block | Logging / MPI / ligand warnings / element warnings, in each block |
| --- | --- | --- | --- |
| `1aua__A1_P24280--1aua__A2_P24280:apo` | 8–701 | 2132–2825 | 1 / 2 / 8 / 1 |
| `1ax2__A1_P16404--1ax2__A2_P16404:apo` | 702–1395 | 3520–4213 | 1 / 2 / 8 / 1 |
| `1dv1__A1_P24182--1dv1__B1_P24182:apo` | 1396–2073 | 6264–6941 | 1 / 2 / 0 / 1 |
| `1nr5__A1_P07547--1nr5__A2_P07547:apo` | 2074–2768 | 10421–11115 | 1 / 2 / 8 / 1 |

`audit.py:90–112` records per-unit marker lines, full-run counts, and every evaluator ERROR in `audit.json`. Additional case-insensitive inspection of error/warning/failure/abort/traceback terms found no additional diagnostic class in either final command log. Failed earlier run9 anchor attempts are not substituted for final measured run9 log.

Logging failure: `L:9–38` identifies exact call and caught formatting error. Reconstructed adapter `E/predict_patched.py.txt:54–60` then stages inputs and changes directory; no numerical value comes from logging. Same traceback appears at `R:2133–2162`, and once in every run9 unit. Symlink spelling in traceback is diagnostic context, not cause of TypeError.

MPI messages: first maps emitted at `L:44,61`, immediately before abort diagnostics at `L:45–55,62–72`. Native source selects branch for `in_option==0 || in_option==1` (`E/frodockgrid.cpp.txt:162–170`). Master merges worker values, writes map, prints completion (`:253–269`); all ranks finish communication and call `MPI_Finalize()` (`:287–309`); branch then unconditionally calls `exit(1)` (`:319–320`). Adapter invokes exactly those options in stages 1/2 (`E/predict_patched.py.txt:94–101`) and ignores subprocess return codes (`:129–140`). Thus these particular aborts are inherited native success-status defect, not evidence of failed map generation, missing environment, exhausted MPI slots, record-selection failure, or cross-invocation path collision. Wrapper's exit 0 alone would not establish this; native source plus retained artifacts does.

Independently checked all sixteen retained MRC files: mode 2, positive dimensions, exact file length `1024 + nx*ny*nz*4`. All sixteen maps, all four `dock.dat`, and all four `clust_dock.dat` compare byte for byte with corresponding run9 job's retained temporary files: **24/24 equal** (`audit.py:120–144`; `audit.json`, `stages[].intermediate_comparisons`). Therefore aborted-status messages did not leave a detectable truncated/different map or downstream numerical intermediate in measured comparison. This does not infer correctness merely from exit 0.

Missing-system diagnostics: subset first group `L:2771,4732,5076,6829,7085,7180,7436,7622,7658`, repeated during aggregation at `L:7811–7819`. Run9 equivalents `R:11118,13071,13411,15164,15412,15503,15759,15945,15981` and `R:16192–16200`. Missing counts, run9 → subset:

| Population | holo | apo | predicted |
| --- | --- | --- | --- |
| pinder_xl | 1947 → 1955 | 334 → 338 | 1747 → 1747 |
| pinder_s | 242 → 250 | 85 → 89 | 250 → 250 |
| pinder_af2 | 180 → 180 | 30 → 30 | 127 → 127 |

Run9 processes eight holo and eight apo jobs; subset processes four apo jobs. Coverage differences explain changed counts. Evaluator computes expected populations, prints errors, and asks permission to apply penalties (`run10_review3/evidence/eval_method.py.txt:141–228`); `U:208–216` deliberately supplies `yes y`. Later missing-system handling adds penalty rows to metrics dataframe (`eval_method.py.txt:423–482`). These diagnostics concern benchmark coverage, not failure to compute four requested units. They occur after final PDB production and chain validation (`L:2767–2771`). Evaluator writes metrics/leaderboard CSVs, not PDBs (`run10_review3/evidence/eval_run.py.txt:85–100`). Those aggregate CSVs are outside compared unit-file set and do change with coverage.

Ligand-size warning branch only prints (`E/libfrodock.cpp.txt:853–856`); same geometry triggers same warnings for corresponding run9 units. Element guessing belongs to inherited PDB loading/serialization (`L:699,1393,2071,2765`), not new selection or directory failure. It can supply element annotations during pose assembly; no subset-specific annotation change was observed. All generated/staged/final PDBs agree as described below.

**Answers A:** `subset_errors_vs_run9=also_in_run9` refers to error classes, not identical missing-system counts or timestamps. `subset_error_source=multiple`: program nonfatal diagnostics plus selection/limited-coverage evaluator errors. No evidence attributes these errors to working-directory links, inherited absolute-path rule conflict, environment/setup failure, or actual concurrent collision. `errors_affect_compared_outputs=no` for diagnosed conditions in measured four-unit comparison: output-producing grid work completed, logging does not control computation, evaluator errors act on other files, and compared PDBs/intermediates agree. This finding does not certify scientific accuracy of inherited baseline.

**B. Computation and file provenance**

All four units actually computed. Evidence extends beyond existence/equality:

1. Launcher removes previous work/output directories, creates fresh work directory, links shared entries, creates real empty private `out/`, and launches exactly one subset invocation (`PIPE:321–345`; `SCHEMAS:75`). It copies only that invocation's private `out/` to saved `files/` afterwards (`PIPE:346–349`). Baseline reference enters local comparison, not remote output creation (`PIPE:352–363`; `SCHEMAS:76`).
2. Wrapper moves any existing results aside before creating fresh results (`U:61–84`), then writes original selected record bytes (`U:121–146`). Audit independently verifies selected CSV equals original header plus run9 records at manifest indices 3, 5, 9, 15 (`audit.py:160–162`). Prediction loop consumes those records (`E/main_patched.py.txt:130–136`). `force=false` can skip only if private result `model_1.pdb` already exists (`E/predict_patched.py.txt:228–233`); empty fresh tree prevents that. No skip marker occurs.
3. Each unit has distinct new temporary directory in L's logging traceback, complete grid and docking output, fifty ranked ligand-coordinate-generation lines, and copy-out marker. Native grid/docking/cluster/view stages execute sequentially (`E/predict_patched.py.txt:94–140`). Pose assembly saves new files and renames them to `model_<rank>.pdb` (`:142–156`); patched copy loop copies those private stage files to private result directory (`:171–176`). No baseline-read, reference-copy, symlink, or hardlink operation exists in this output path.

| Unit | Private stage under `F/tmp/` | L: four completed maps | L: generated ligand models 1–50 | L: copy-out |
| --- | --- | --- | --- | --- |
| 1aua apo | `tmp5grg8h1w` | 44, 61, 87, 102 | 649–698 | 701 |
| 1ax2 apo | `tmpnquwr2gq` | 738, 755, 781, 796 | 1343–1392 | 1395 |
| 1dv1 apo | `tmpjvuifm4j` | 1432, 1449, 1475, 1490 | 2021–2070 | 2073 |
| 1nr5 apo | `tmp8qhahlpl` | 2110, 2127, 2153, 2168 | 2715–2764 | 2767 |

Native programs start around `L:8` (01:03:44) and finish copying last unit at `L:2767` (01:20:39); full invocation wall is 1080.947 seconds (`run10/agent/results/reproduce/units-check/wall.json:1`). Distinct run9 timestamps appear in corresponding R blocks. `L:2768–2770` reports four completed systems, prediction exit 0, zero chain-label repairs; evaluator exits 0 at `L:7820`.

Independently read each of 200 manifest-listed final files, its same-rank model in logged private stage, and run9 reference: **200/200 three-way byte-identical, nonempty; 83,417,850 bytes per side** (`audit.py:145–158`; `audit.json`, `outputs`). Every local fetched result and temporary model is regular, link count one; result ancestors contain no symlinks; stage/result inode identities differ. Fetch can remove remote link metadata, so local link checks alone are not remote provenance proof. Fresh private destination plus inspected generating/copying code and recorded native activity supply that proof. “Written by subset” includes normal copy-out from its own newly computed stage. It does not mean no internal copy operation.

`units_all_computed=yes`; `outputs_written_by_subset=yes`. Chain-restoration pass made no sample edits (`F/run_command/chain_labels_restored.json:1`, `[]`), so staged-to-final comparison is direct.

**C. Outside private out/temp: resolved paths, naming, use, and limits**

Let `S=/tmp/m5-a3e31127-1e00-48ca-9d4a-e4514bd0cf96`, shared run root, and `W=S/units-check`, measured working directory. Logged executable and temp paths establish W (`L:5,21,38`); link construction establishes `W/data -> S/data`, `W/baseline-published -> S/baseline-published`, `W/harness -> S/harness` (`PIPE:331–341`). `W/out` is real/private. Resolving links matters: shared dataset under S remains shared, despite ancestor `/tmp`. No remote `readlink` or write trace was available.

There is one established outside-private-output write often omitted from workload-only inventories: **captured stdout/stderr at `S/out/units-check/run.log`**. Supervisor opens that file before launching child and child inherits it (`PIPE:342–345`). Wrapper `tee` writes private `W/out/run_command/run_command.log` and inherited stdout (`U:66`), so captured outer log receives writes too. It has fixed name for this U51 operation; purpose logging; no later unit reads it. Concurrent probe already assigns separate outer files `S/out/concurrency/logs/<work-label>.log` (`SCHEMAS:121`). This is not a symlink collision or mutable numerical cache.

Supervisor, not `run_units.sh`, also writes `S/out/units-check/wall.json` and copies `W/out/**` into `S/out/units-check/files/**` after child completion (`PIPE:346–348`). Supervisor creates work directory and links first. These control/collection artifacts are outside W's private `out/`, but never inputs to unit computations. They must not be confused with dependency writes through linked data trees.

All explicit wrapper result/configuration/history/log/archive/repair/scoring writes remain under `W/out`: `U:53–84,145,164–205,212`; scorer output paths above. Python bytecode writing disabled (`U:50`). Native stage gets fresh `W/out/tmp/tmp<random>` per unit (`U:67–68`; `E/predict_patched.py.txt:54–60`). Input copies, four grids, ASA PDBs, `dock.dat`, `clust_dock.dat`, generated ligand/pose/model PDBs, and optional native visualization files resolve inside that private stage (`:94–176`). Fixed native basenames therefore do not share a directory across units or invocations. Each stage retains exactly fifty models plus four maps and two `.dat` files in fetched records (`audit.json`, `stages[].files`). Temporary PDB cleanup at adapter `:163–166` removes staged inputs/ASA/ligand visualization files. Shared SOAP file is opened for reading, `"rb"`, not writing (`E/libfrodock.cpp.txt:440–508`); commented-out SOAP conversion is not executed.

Known conditional persistent writes through linked dataset:

| Logical target | Resolved target | Naming / purpose / triggering condition |
| --- | --- | --- |
| `W/data/pinder/2024-02/` | `S/data/pinder/2024-02/` | Fixed release directory; mkdir if missing. |
| `W/data/pinder/2024-02/index.parquet` | `S/data/pinder/2024-02/index.parquet` | Fixed dataset cache shared by all units/invocations; download/serialize only if absent, unless explicit update/custom index. Measured calls use default existing-file path. |
| `W/data/pinder/2024-02/pdbs/<system-id>.pdb` | Same suffix under S | Per-system native evaluation input/cache, shared across holo/apo units of that system; downloader invoked only when native missing. |
| Entry-associated `pdbs/<name>.pdb`, `test_set_pdbs/<name>.pdb`, `mappings/<name>.parquet` | Same suffix under `S/data/pinder/2024-02/` | Per-entry structural/mapping input cache, potentially shared across units referencing same structure. Downloader expands entry's native/holo/apo/alternative/predicted PDBs and mappings; downloads missing files only. |

Sources: `run10_review3/evidence/core_index_utils.py.txt:42–55,90–134` (location/index); `run10_review3/evidence/eval_method.py.txt:231–251` (native existence guard); `run10_post/evidence/core_index_system.py.txt:133–145,613–647` (entry download); `core_index_utils.py.txt:696–754,759–762` (exact filename formulas). Entry destinations are input caches, not previously computed docking results or shared native scratch. Downloader stages random sibling `.part` files and atomically replaces final per-entry target (`run10_post/evidence/core_utils_dataset.py.txt:151–167,199–211,230`). Those `.part` files are temporary; their final datasets remain shared persistent paths. Index dataframe serialization lacks this replacement/locking protocol (`core_index_utils.py.txt:125–134`).

Four conditional native destinations, under resolved `S/data/pinder/2024-02/pdbs/`:

- `1aua__A1_P24280--1aua__A2_P24280.pdb`
- `1ax2__A1_P16404--1ax2__A2_P16404.pdb`
- `1dv1__A1_P24182--1dv1__B1_P24182.pdb`
- `1nr5__A1_P07547--1nr5__A2_P07547.pdb`

All four appear in prepared input inventory (`run10_harness3/pinder_inputs.tsv:1622,1625,1674,1769`). Run10 setup fetched/verified index at `out/setup/setup.log:678`, metadata at `:682`, and reports 3,590 structural/mapping inputs with zero failures at `:688`. Setup verification code at `run10/agent/harness/setup.sh:3907–3949` checks inventory before invocation. This supports those conditional writes being dormant in measured prepared state. It is not an observed download/write during subset. Default environment bypasses home dataset fallback (`U:31–35`). No `metadata.parquet`/supplementary/custom-index download call was established in executed prediction/scoring path; existence of other utility writers does not make them actual invocation writes.

**Cross-unit reading:** shown docking path reads original prepared structures, SOAP, and newly created same-unit stage files. Every next unit creates another stage; no shown lookup reuses earlier unit's grids/solutions. Evaluator reads produced PDBs only after docking loop finishes. Dataset caches, if missing-file branches ran, can be reused by later consumers (e.g. holo/apo evaluation of same system; index shared across processes). These are input downloads, not learned state. No retained evidence shows an earlier sample unit writing a persistent cache that a later sample unit read.

**Inventory limit:** no filesystem syscall trace, before/after shared-tree inventory, or installed dependency/runtime source snapshot covers all transitive Python imports and MPI/library side effects. Inspected application/native paths establish private scratch, prepared conditional dataset mechanisms, and outer log. They do not establish every actual outside-out write, including any incidental dependency cache. Nor do setup records prove shared files remained unchanged throughout invocation. Thus no exhaustive actual-write inventory or universal absence of cross-unit disk dependence can be claimed. No concurrent invocation ran, so collision remains hypothetical.

`outside_out_naming=unknown` and `outside_out_purpose=unknown` describe requested complete actual-write inventory. Established outer capture is fixed-name/logging; conditional dataset mechanisms mix fixed and per-entry names and serve reusable input caches. Reporting those conditional possibilities as observed `mixed`/`multiple`, or reporting `none`, would overstate evidence. `later_units_read_earlier_writes=unknown` covers all requested outside paths; known native stage flow shows no such reuse, while complete dependency flow is unestablished.

**D. Private copies of written locations**

For identified dataset mechanisms, **byte-preserving private cache copies can preserve explicit per-unit computation, parameters, and inputs**, with remaining inputs/code still linked. More targeted than copying whole `data/`:

- Build real private ancestor directories `W_i/data/`, `W_i/data/pinder/`, `W_i/data/pinder/2024-02/`. Link unchanged siblings, including `data/frodock` and `data/selection.json`, to corresponding shared entries.
- Independently copy prepared `index.parquet` and prepared contents of potentially writable `pdbs/`, `test_set_pdbs/`, `mappings/` beneath private release root. Preserve relative names and bytes. Use real independent files/directories, not writable hardlinks or symlinks back to shared destinations. Copy preparation precedes measured invocation. Creating private descendants beneath a still-linked `data/` would instead mutate shared tree.
- Keep `baseline-published`, `harness`, other read-only siblings linked, `out/` private, and native temporary directories under private `out/tmp`. Keep outer capture unique per concurrent invocation, as probe already does.

Unchanged `U:31–35,84,93,103,151–152` still sees same relative data paths, release, index values, selection, original CSV records, and structural input bytes. Adapter uses same per-row fields, 50 solutions, eight MPI ranks, force=false, four maps, SOAP input, clustering, pose assembly, and copy formula (`E/predict_patched.py.txt:94–176,213–243`). Evaluator reads same native bytes through same relative layout. Copying existing prepared caches preserves existence guards; starting empty would add downloads and is not equivalent preparation. Copies should start from same prepared pre-invocation state and retain within-invocation updates if any, rather than resetting between units.

This removes possible shared-dataset write races without editing measured program or numerical settings. It is a source-based prospective conclusion for enumerated mechanisms, not measured concurrent equivalence. Inherited absolute PATH/TMPDIR spelling (`U:49,68`) resolves from each W_i; it neither points all invocations at shared scratch nor explains MPI diagnostics. Private copies do not resolve separate literal path-spelling rule conflict.

**Complete requested minimal-copy proposition remains unknown.** Complete set of actually written locations was not established, so cannot certify that copying *only* that set isolates every dependency while all remaining locations stay safely linked. No copy-layout execution or concurrency validation authorized here. Existing native time-seeded SAS behavior also means unchanged explicit inputs/parameters alone do not prove future bitwise equality (`run10_inputs/evidence/sas.cpp.txt:683–690,747–759`); measured equality here includes subset grids and final files, not arbitrary future schedules. Accordingly `private_copies_preserve_computation=unknown` applies to full requested guarantee; positive conditional construction above applies only to identified dataset paths.

Validation: `python3 -I -B run10_post2/audit.py` passed. It checks source provenance/patch reconstruction, log attribution, original-record selection, complete MRC lengths, 24 intermediate comparisons, and 200 three-way PDB comparisons. No workload module imported. `audit.json` retains exact per-file/line evidence; status uses unknown where requested complete inventory/guarantee exceeds retained evidence.
