Run10 input-restriction assessment — 2026-11-01

Prepared-input route exists: restrict `out/results/frodock_setup.csv`, then invoke exactly the same measured `pinder_methods predict` command. Predictor consumes this table as its job list. No new published-source edit, alternate launcher, direct internal-function call, regenerated structure or changed docking parameter is needed for that restriction.

**Complete requested combination is not established and does not satisfy every literal rule.** Measured run9 already patches published entry and per-unit adapter code. Restricting inputs retains those patches; it does not produce a pristine published-code run. Baseline also constructs absolute run-local PATH/TMPDIR, conflicting with the stated relative-path rule. Per-unit numerical/file invariance under restriction remains unknown, with a concrete native time-seeded random path identified below.

Scope: read `run10_why/`, `run10_mech/`, `run10_review2/` reports/status first, then named harness, configuration, source and record files selectively. All writes confined to `run10_inputs/`. No workload, harness execution, box contact, network fetch, git command, credential, `.keys` or `~/.codex/` read. Local standard-library audit only. No input PDB, final PDB, large intermediate, profiler database or raw-decoy archive content needed. Paths relative to experiment directory unless absolute. Source copies retain original bytes and line numbers.

Evidence labels: **Measured here** means local hashes, byte comparisons and in-memory CSV checks. **Read** means source/document/record evidence. **Inferred** means consequence of those facts. No subset execution measured.

Status interpretation:

| Key | Value | Meaning |
| --- | --- | --- |
| `restriction_possible` | `yes` | Existing measured entry consumes a restrictable prepared job list. This positive mechanism finding does not certify the full unmodified-code/rules conjunction. |
| `restriction_kind` | `config_input_list` | CSV inference-configuration/job list, not a new YAML selector, directory scan or command-line PDB list. |
| `published_code_unmodified` | `no` | Literally relative to published pinned source: run9 fixes remain. Relative to measured installed run9 code, restriction requires no further source changes. |
| `same_paths` | `yes` | Selected units retain the same final PDB path formula under `out/`; this says nothing about byte equality. |
| `restriction_changes_computation` | `unknown` | Same per-row explicit arguments/stages established. Whether changed grouping/order/timing changes these chosen units' numerical execution or final bytes is unmeasured; native time-seeded conditional work prevents certifying independence. |
| `harness_rules_satisfiable` | `no` | Under unchanged measured command/environment and input/config-selection-only scope, inherited absolute run-local paths already violate the literal rule. |
| `config_differs_only_in_units` | `yes` | A reduced CSV can preserve header and retained rows byte for byte; numerical YAML, structural inputs, SOAP file and other settings need no change. Existing source patches are separate from configuration differences. |

**Measured here: source and selection checks**

`audit.py` uses only Python standard library, does not import experiment code, and writes only this folder. `audit.json` records hashes and preserved members. Local cached archives, identified by `intake_mirror/verify.py:58–68`, match intake identities (`run9/agent/intake/baseline.json:4–5`):

| Cached archive | Measured SHA-256 |
| --- | --- |
| `/home/hal/.cache/blind01/intake_check_dl/codex/pinder_code.1.body` | `b577532820ebbe5c16432b78c5e9c197690e863cb70a0a35a8ebcbe5277b76dd` |
| `/home/hal/.cache/blind01/intake_check_dl/acquire/gcp_mirror_package.body` | `91b9aeff747346046c7f8c4c92fa5749c9f082d8122ee9d2d4769855d35368f4` |

PINDER pin: `ebeb28a2f8411363cef722b7d293c978f7442672`. Copies in `evidence/`: published main, methods enums, FroDock adapter, full evaluator `dockq/method.py`; native grid driver, SAS implementation, Mersenne generator and relevant build recipes. `audit.json` maps every copy to exact archive member and digest. Main/adapter copies also equal `run10_why/evidence/` bytes. Native mirror identity with original study remains unresolved (`baseline.json:68`); this audit verifies the recorded run9 material, not external original identity.

Independent byte comparisons:

| Baseline `run9/agent/harness/run_command.sh` | Existing `run10_harness2/run_units.sh` | Result |
| --- | --- | --- |
| 21–48: environment | 23–50 | Identical |
| 50–81: output setup/configuration | 52–83 | Identical |
| 117–185: prediction, repair, evaluation | 132–200 | Identical |

Harness fixes patch equals saved `run9/agent/results/reproduce/out/setup/pinder_frodock_fixes.applied.patch` bytes. No fresh audit of installed remote executables occurred.

Saved full manifest `run9/agent/results/reproduce/out/results/frodock_setup.csv:1–17` has exactly 16 rows and four nonempty string fields: `id,kind,receptor,ligand`. Unit order matches `run10_harness2/units.json`. All 800 manifest output strings match the code's per-unit path formula. In-memory checks selected each singleton and one reversed four-unit list: parsed rows exactly equal original selected rows, in requested order, while retaining original header/row bytes. These are CSV-format checks, not prediction tests or demonstrations of subset output equality.

**Read and inferred: 1. Exact input mechanism**

Console entry is `pinder_methods = "pinder.methods.main:main"` (`run10_why/evidence/pyproject.toml.txt:36–41`). Main dispatches `predict` (`evidence/main.py.txt:143–151`). Measured command (`run9/agent/harness/run_command.sh:119–120`):

```sh
"$VPY" "$VENV/bin/pinder_methods" predict --method "$METHOD" --data_dir data/frodock \
    --results_dir "$RESULTS" --subset pinder-s --pairs all --config "$RUN_DIR/frodock_config.yaml"
```

Here `RESULTS=out/results`, `RUN_DIR=out/run_command` (`:51–52`). Wrapper copies prepared input table into output tree (`:82`):

```sh
cp data/frodock/frodock_setup.csv "$RESULTS/frodock_setup.csv"
```

Installed loop, established by upstream body plus applied patch (`evidence/main.py.txt:122–137`; `run9/agent/harness/pinder_frodock_fixes.patch:12–20`):

```python
config_dict["data_dir"] = data_dir
config_dict["results_dir"] = results_dir
inference_config = pd.read_csv(Path(results_dir) / f"{method}_setup.csv")
for complex_config in inference_config.to_dict("records"):
    predict_method(complex_config, config_dict)
```

Thus selected complete rows at the **existing** `out/results/frodock_setup.csv` path restrict prediction. Input structures can stay untouched under `data/frodock`. No links/copies of those structures are necessary. Requested row order controls prediction order.

`--ids`, `--subset`, `--pairs` exist in signature/docstring but are unused throughout prediction body (`evidence/main.py.txt:80–140`). YAML is loaded as adapter parameters (`:102–115`); the actual list comes from CSV. Adding an `ids` field to YAML would not select rows. Deleting/unlinking unrequested PDB directories while retaining full CSV would leave jobs referencing missing files; predictor does not discover its jobs by scanning that directory. No direct receptor/ligand command-line list appears in this entry's signature. Published preprocessing is unnecessary and would add a different action/input-generation step.

Existing `run10_harness2/run_units.sh:93,113–122` already implements this operational input-list route, reading full CSV then writing selected records. Calling it a prepared-input mechanism is supported by source. It is not a second, newly discovered pristine implementation. Earlier reports' `other` mechanism category described wrapper filtering; this task's more specific `config_input_list` category describes the same CSV input.

**Read and inferred: 2. Per-unit code, configuration, scale and result paths**

Adapter extracts only current row's `id`, `kind`, `receptor`, `ligand`, plus results directory, solution count, MPI count and force (`evidence/predict.py.txt:209–233`). Existing patch resolves relative structure paths against unchanged `data_dir` (`pinder_frodock_fixes.patch:53–64`). Complete original rows therefore retain the same structural inputs and explicit call arguments.

Fixed settings: `N_SOLUTIONS=50`, `MPI_NP=8`, `FORCE=false`, `EVAL_MAX_WORKERS=8`, CPU-only CUDA visibility, zero GPUs (`run_command.sh:22–30`). Saved YAML (`run9/agent/results/reproduce/out/run_command/frodock_config.yaml:1–3`) is:

```yaml
n_solutions: 50
mpi_np: 8
force: false
```

Same eight native stages remain: four potential grids, docking with the same maps/`--th 10`/SOAP file, clustering, visualization, coordinate generation (`evidence/predict.py.txt:79–137`). Pose assembly/ranking remains per job (`:139–166`). Comment “normalize the results” at `:139` means assembling/renaming solutions, not statistics across input units.

Published final path formula (`evidence/predict.py.txt:169–172,218`) and retained copy fix (`pinder_frodock_fixes.patch:43–48`):

```python
results_path_complete = results_dir / f"frodock/{complex_id}/{complex_kind}_decoys/"
```

Hence selected final files remain `out/results/frodock/<id>/<kind>_decoys/model_1.pdb` through `model_50.pdb`, independent of selected position/count. Same wrapper chain restoration processes those files (`run_command.sh:132–174`). `same_paths=yes` concerns these owned files; shared metrics, leaderboard, archive, manifest and logs are not each unit's owned outputs.

Literal unmodified-published-code answer is **no**. Setup applies recorded source patch before installation (`run9/agent/harness/setup.sh:208–213`; saved `setup_record.json:16–22`). Patch changes entry enum handling/CSV reader (`pinder_frodock_fixes.patch:3–20`), per-unit input staging (`:24–30`), executable prefix (`:33–40`), result copying (`:43–48`) and input path resolution (`:53–64`). Wrapper also edits blank ligand HETATM chain labels (`run_command.sh:162–168`), a retained output-affecting harness operation outside published adapter.

Input-only selection cannot remove those changes. Pristine entry is itself defective: `SUPPORTED_ACTIONS.PREDICT.value` is a string tested against ordinary Enum members (`evidence/main.py.txt:117–120`; `evidence/methods_init.py.txt:17–29`), and CSV call is `pd.from_csv`, replaced by measured patch. Merely changing unit inputs does not repair either problem. No successful pristine published-code alternative through this same entry is established. If “unmodified” instead means unchanged since measured run9 installation, the selection route meets that narrower source criterion; it does not meet pristine-source criterion.

**Read and inferred: 3. Input-set effects and remaining unknowns**

At Python prediction-loop level, no cross-row mean, normalization, quota allocation, shuffle, shared random generator, seed derived from row index/count or shared decoy ranking appears. Each row gets same parameter dict; shown adapter reads it without mutating it. Fresh native process calls and fresh per-job temporary directory isolate ordinary native process state (`evidence/predict.py.txt:54–89,126–137`; staging patch above). Ordering changes which row starts next, but path/rank formulas do not use that position.

**New concrete source caveat: wall-clock-seeded native work.** This is not a demonstrated output mismatch.

1. Published adapter runs desolvation grids with `-m 3` for receptor and ligand (`evidence/predict.py.txt:100–106`). Grid's solvation branch is `if(in_option==3)` (`evidence/frodockgrid.cpp.txt:347–349`). MPI path calls `ASA::localSAS(startatom,endatom,sas,sasa)` (`:395–427`); non-MPI alternative calls corresponding overload (`:477–479`).
2. Called SAS routine initializes local Mersenne generator from current seconds (`evidence/sas.cpp.txt:683–690`):

   ```cpp
   int32 seed = (int32)time(0);        // random seed
   CRandomMersenne rg(seed);           // make instance of random number generator
   ```

3. Conditional geometric degeneracy handling draws random rotation before ASA computation (`evidence/sas.cpp.txt:747–759`):

   ```cpp
   while(north_pole_test_local(sas.sphere_local, nls) == 0)
   {
       spheres_rotation (sas.sphere_local, nls, rg.Random());
       npole++;
   }
   area = asa(sas.sphere_local, nls, sas.circles, sas.arcs, sas.arcsnew, sas.angles, &narcs2);
   ```

4. Generator constructor seeds state and performs 37 `BRandom()` calls (`evidence/mersenne.h.txt:173–183`). SAS results populate occupancy in generated `<input>_ASA.pdb` (`evidence/frodockgrid.cpp.txt:456–458,488–500`); docking later reads those ASA inputs (`evidence/predict.py.txt:109–110`).
5. Build connection is explicit: grid MPI compile defines `MPI_RELEASE` (`evidence/grid_MPI_GCC_subdir.mk.txt:20`); grid link uses `-lsas_gcc` (`evidence/grid_MPI_GCC_objects.mk.txt:7`; makefile `:40–46`); SAS library builds from `sas.cpp` (`evidence/sas_gcc_subdir.mk.txt:6–20`, makefile `:40–46`). Setup runs archived compilation script (`setup.sh:225–242`), whose library/tool list includes these targets (`evidence/compile_frodock.sh.txt:9`). Saved setup record identifies all four native tools as compiled (`run9/agent/results/reproduce/out/setup/setup_record.json:8–13`).

Restriction/reordering can change grid launch times, hence time-derived seeds. No shared random stream across units is shown; local time seeding is a different dependence. Whether these selected structures enter random-rotation branch, whether resulting floating-point differences survive output precision, and whether final models change are **unknown**. Even unchanged scientific result could involve different incidental RNG state or geometric work. No source proof of per-unit bitwise independence follows from equal row fields. Conversely, finding a conditional random path does not establish an actual changed chosen-unit result. `restriction_changes_computation=unknown` preserves that distinction.

Cache behavior also matters: `force=false` skips when `model_1.pdb` already exists (`evidence/predict.py.txt:218–223`). Same baseline history/fresh-result setup must remain (`run_command.sh:59–82`) so selected units are recomputed. Native stage temp files are per job; ordinary OS/library caches can change elapsed time. Full dependency/cache state and installed binaries were not traced in this read-only audit.

Shared evaluation definitely depends on selected set. Scorer scans produced system/decoy directories (`evidence/eval_method.py.txt:81–129,238–266`), evaluates structures per system (`:270–354`), then concatenates tables (`:376–393`). Missing-system penalties depend on coverage (`:423–482`), and summaries aggregate metrics (`:601–631`). CLI writes shared `frodock_metrics.csv` and `frodock_leaderboard.csv` (`run10_review2/saved_eval_run.py.txt:85–100`). Those shared files generally differ; they are not unit-owned PDBs. No shown scorer path writes models back or feeds scoring into prediction/chain repair.

Earlier 800/800 saved reproduce/profile PDB equality is an earlier measurement (`run10_review2/REPORT.md:63`), not repeated here. Both full runs processed same list/order. It does not settle restriction, singleton or reordering effects. No such runtime results are claimed.

**Read and inferred: 4. Exact input-only script design and harness rules**

Mechanically, a `run_units.sh` could copy measured shell wrapper, reject empty/duplicate/unknown requested `system_id:kind` keys, retain full-universe validation, and replace only copied CSV with selected original rows before the existing prediction command. One exact insertion point: after baseline `run_command.sh:115`, before `:117`. Existing full copy/validation at `:82–113` stays; numerical YAML and complete prediction/repair/evaluation suffix stay unchanged. Original printed CONFIG then describes validated full universe; selection block should print its selected keys/count separately.

Concrete selection block, using the existing `VPY`/`RESULTS` variables and script arguments; **design only, not executed as a harness here**:

```sh
"$VPY" - "$RESULTS/frodock_setup.csv" "$@" <<'PY'
import csv
import io
from pathlib import Path
import re
import sys

target = Path(sys.argv[1])
requested = sys.argv[2:]
if not requested or len(set(requested)) != len(requested):
    sys.exit("ERROR: provide one or more distinct system_id:kind keys")
raw = target.read_bytes().splitlines(keepends=True)
rows = list(csv.DictReader(io.StringIO(b"".join(raw).decode("utf-8"))))
if not rows or list(rows[0]) != ["id", "kind", "receptor", "ligand"]:
    sys.exit("ERROR: unexpected prepared manifest schema")
if len(raw) != len(rows) + 1:
    sys.exit("ERROR: expected the recorded one-line-per-row manifest format")
keys = [row["id"] + ":" + row["kind"] for row in rows]
if len(set(keys)) != len(keys):
    sys.exit("ERROR: duplicate prepared unit")
if any(not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:+=-]{0,127}", key)
       or key not in keys for key in requested):
    sys.exit("ERROR: unknown or invalid requested unit")
target.write_bytes(raw[0] + b"".join(raw[keys.index(key) + 1] for key in requested))
print("RESTRICTED_UNITS=" + ",".join(requested))
PY
```

Only manifest under private `out/` changes. Original header and retained rows are byte-identical, including receptor/ligand path spellings. No data/source changes, new native launcher or timed preprocessing needed. No invocation of published `--ids` needed. Compound strings are wrapper keys for original `(id,kind)` fields; they must not be represented as strings accepted by ignored native `--ids` option.

This operational design still cannot be certified under **every literal unchanged rule**:

| Rule / source | Finding |
| --- | --- |
| Exact measured binary, args, configuration, environment and per-unit scale; SCHEMAS:54,56 | Input-only insertion retains these, including existing installed patches. Does not turn measured patched code into pristine published source. |
| Relative paths, never absolute run-local paths; SCHEMAS:55 | Baseline `run_command.sh:47` exports `PATH="$PWD/baseline-published/frodock/bin:$PWD/$VENV/bin:$PATH"`; `:66` exports `TMPDIR="$PWD/out/tmp"`. Both become absolute into current run directory. Keeping environment preserves literal violation. Changing these exceeds input/config-list selection and violates unchanged-environment condition. |
| Writes only out/temp; SCHEMAS:55–56 | Selection writes only out/. Explicit wrapper writes confined there; adapter uses temp. Exhaustive dependency confinement unknown: evaluator creates/downloads missing natives (`evidence/eval_method.py.txt:231–251`), core index helper can create release directory (`run10_review2/saved_core_utils_excerpt.py.txt:24–26`). Prepared state may avoid these branches; no observed forbidden write claimed. |
| Published program's own subset selection/native unit identity/order; SCHEMAS:56 | Program itself consumes only listed CSV records, in row order. No separate CLI selector needed for this input mechanism. Strict acceptance of wrapper compound keys and whether prepared-list restriction meets contract's wording remain interpretations requiring an explicit contract decision; lack of effective `--ids` alone does not disprove this input route. Existing absolute-path failure suffices for `harness_rules_satisfiable=no`, independent of that interpretation. |
| No `CUDA_MPS_*` changes; SCHEMAS:56–57 | No added MPS operation. Existing wrapper and inspected adapter preserve inheritance; CUDA visibility is separate and unchanged. |
| Exit status propagated; SCHEMAS:54,56 | Original prediction status captured/returned (`run_command.sh:118–124`); evaluator status captured as `${PIPESTATUS[1]}`/returned (`:179–185`). Selection failure exits via existing errexit. Native subprocess calls lack `check=True` (`evidence/predict.py.txt:126–137`), a baseline limitation, not a new wrapper status change. |

Contract path is `/home/hal/dev/interp/metis-wt/dut/pipeline/m5/SCHEMAS.md`. No compliant launch script is supplied because input selection alone cannot remove demonstrated unchanged-environment/path conflict or meet pristine-source demand. No contract/baseline modification authorized or performed.

**Read and inferred: 5. Configuration/input differences**

For the operational measured-entry route, only CSV row membership/order need differ. Header and each retained row can remain exact bytes, as code above and in-memory audit demonstrate. YAML remains exactly `50 / 8 / false`; full `data/selection.json`, dataset index, original pretransformed receptor/ligand files, SOAP file, executables, evaluation settings, environment and working directory need no change. Prepared manifest's input paths still resolve against `data/frodock`. No per-unit rescaling or input regeneration required.

Full validation must use original full list before restriction: baseline insists on all eight selected systems and both pairings (`run_command.sh:99–107`). Filtering `data/selection.json` or shrinking CSV before that validation would fail or require broader validator changes. The stated insertion point avoids that problem. Merely staging a smaller input directory and invoking the entire unedited `run_command.sh` would not implement this design: wrapper recopies full table and checks full universe. Input restriction belongs between that validation and unchanged published prediction command.

`config_differs_only_in_units=yes` is therefore a configuration/input-format finding, not certification of source purity, exhaustive writes or numerical invariance. Overall evidence supports a real CSV restriction mechanism with the same explicit measured per-row calls and output paths, while the strict requested pristine-code/rules-compliant faithful run remains unavailable or unproven for the distinct reasons above.
