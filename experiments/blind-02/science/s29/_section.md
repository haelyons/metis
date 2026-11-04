

## Comparison request (science step s29)

This request asks for one comparison-mode run: the arms, fixture inputs, outputs and evaluator exactly as the comparison view (`comparison_view.json`) describes them. It is a recording run on fixture inputs, repeating an earlier recording run of this route with corrections to how the programs are built, how the evaluator is invoked, and how the harness scripts get their data on the box. It is not the seed's main experiment, and the seed's four cases above are not run, fetched or evaluated in it. Preserve the seed above.

What the run does

- Four arms, as the view describes them. A0 is the published baseline (the seed's configuration 1). A1 is the seed's configuration 2. A2 repeats A0's commands and A3 repeats A1's commands, each as separate invocations. The pipeline runs every arm's commands itself; the adapters only check that the input's prepared files exist.
- Four fixture inputs, as the view describes them: holo test-set monomer pairs of four PINDER `2024-02` systems that are not among the seed's four cases. Each input's `spec` names its receptor and ligand sources (URL, byte count, SHA-256), the prepared paths the arms read, and its native complex, which only the evaluator may read.
- The evaluator: PINDER's DockQ implementation at the pinned commit, as the view describes it, scoring each arm's assembled models of one input against that input's native complex.
- Outputs, as the view describes them: the ranked rows of each arm's `docking.out` (transform fields and score field), the coordinates of the assembled models, and the evaluator's DockQ value for each model. They are recorded and compared across arms by the pipeline. No agent computes or reports a comparison.

Which harness files reach the box (correction)

- The pipeline uploads only these files from `harness/` to the box: `setup.sh`, `run_anchors.sh`, `run_command.sh`; `run_evaluation.sh`, `run_units.sh` and `units.json` when they exist; and the sealed comparison files `arms/<arm id>.sh`, `cmp_files.json`, `cmp_extract.json`, `versions.sh`, `fetch_private.sh` and `evaluate.sh`. Any other file written under `harness/` (a Python helper, a JSON list of inputs, a table of published values) never reaches the box. A repair may change only `setup.sh` (or `run_anchors.sh` and `run_command.sh`); the sealed comparison files are never repaired, so a defect in one of them stops the run.
- Every one of these scripts is therefore self-contained: it reads no file under `harness/` except itself, and carries in its own text every list, value and program it needs, or reads it from the variables the pipeline sets (`CMP_INPUT`, `CMP_INPUT_SPEC`, `CMP_OUT`, `CMP_ARM_OUT`, `CMP_EVAL_OUT`, `CMP_PRIVATE`). Write no other file under `harness/`.
- `fetch_private.sh` runs as a separate user with the private directory as its working directory and has no `CMP_INPUT_SPEC`; its output is not kept. It carries in its own text, for each of the four inputs, the native complex's name, URL, byte count and SHA-256 exactly as `spec.reference` gives them in the view, downloads each one, checks its byte count and SHA-256 (a mismatch exits nonzero), and writes it under its working directory at that name.
- `evaluate.sh` takes the input id from `CMP_INPUT` and the native complex's name, byte count and SHA-256 from `spec.reference` in `CMP_INPUT_SPEC`; it reads no input list from any file.

Materials, pins and preparation

- MEGADOCK: the published repository https://github.com/akiyamalab/MEGADOCK at commit `9575280c875732553266e26adc607dd892b02616`, built twice from the same checkout under `baseline-published/megadock/` in the shared run directory, so that `baseline-published/megadock/megadock`, `baseline-published/megadock/megadock-gpu` and `baseline-published/megadock/decoygen` exist there. The CUDA samples headers come from https://github.com/NVIDIA/cuda-samples at tag `v12.8`; they are build dependencies only. The CPU build uses single-precision FFTW exactly as below. The GPU build keeps `-Xcompiler -fopenmp` and `-use_fast_math` and the libraries below, and targets the compute capability of the GPU on this box: `setup.sh` reads it with `nvidia-smi --query-gpu=compute_cap --format=csv,noheader` (for example `8.6` gives `sm_86`, `9.0` gives `sm_90`, `8.0` gives `sm_80`), passes that one target as `SM_VERSIONS` and in `-arch`, records it in the setup record, and checks with `cuobjdump --list-elf` (from the CUDA toolkit) that `megadock-gpu` contains code for that target; a missing target stops setup. Historical build commands for an `sm_90` box (blind-02 m5 run2 `setup.sh:52-80`, as carried by earlier briefs of this route; replace `sm_90` by the box's target):

```bash
if [[ ! -d baseline-published/cuda-samples/.git ]]; then
    git clone --depth 1 --branch v12.8 https://github.com/NVIDIA/cuda-samples baseline-published/cuda-samples
fi
git -C baseline-published/cuda-samples describe --tags --exact-match
samples=$(pwd)/baseline-published/cuda-samples
make -C baseline-published/megadock -j 8 USE_GPU=0 USE_MPI=0 \
    CPPCOMPILER=/usr/bin/g++ FFTW_INSTALL_PATH=/usr \
    FFTW_CFLAGS=-I/usr/include FFTW_LDFLAGS='-lm -L/usr/lib/x86_64-linux-gnu -lfftw3f'
make -C baseline-published/megadock -j 8 USE_GPU=1 USE_MPI=0 \
    CPPCOMPILER=/usr/bin/g++ SM_VERSIONS=sm_90 \
    "NVCC=$CUDA_NVCC -Xcompiler -fopenmp -arch=sm_90 -use_fast_math" \
    "INCLUDES=-Isrc -I$CUDA_INCLUDE -I$samples/Common" \
    FFTW_CFLAGS=-I/usr/include \
    "LIB=-lm -L/usr/lib/x86_64-linux-gnu -lfftw3f -L$CUDA_LIB -Wl,-rpath,$CUDA_LIB -lcudart -lcufft"
```

  CUDA paths are discovered on the box. In this published release `megadock -h` and `megadock-gpu -h` print their usage and exit with status 255; accept that status only together with the usage text.
- Fixture inputs: `setup.sh` fetches each input's receptor and ligand source from the URL in its `spec`, checks the byte count and SHA-256 recorded there (any mismatch stops the run), and writes the prepared files to the `spec`'s `prepared` paths under the shared run directory by changing only the chain field (column 22) to `R` in the receptor and `L` in the ligand on ATOM, HETATM, ANISOU and TER records, keeping every other byte and line. It records the SHA-256 of every prepared file in its setup record. The URLs, byte counts, SHA-256 values and prepared paths are written in `setup.sh` itself.
- Native complexes: only `fetch_private.sh` fetches them, from the URLs in the inputs' `spec.reference`, and checks their byte counts and SHA-256. `setup.sh`, the adapters and the arms never fetch, copy or read them.
- Evaluator: install PINDER from the pinned source archive (URL and SHA-256 in the materials above and in the view), as run9's excerpt above shows, under the shared run directory or with apt, never under the home directory. After installing it, `setup.sh` checks that the evaluator's interpreter imports `BiotiteDockQ` from `pinder.eval.dockq` (an import only; no private data, no scoring) and stops setup if it does not. `evaluate.sh` reads `model_<rank>.pdb` from `CMP_ARM_OUT` in rank order, scores each against the input's native complex under `CMP_PRIVATE` with BiotiteDockQ and the model's chains `R` and `L` mapped to the native's receptor and ligand chains, and writes `CMP_EVAL_OUT/dockq.json` as one JSON array of the DockQ values in rank order with no other number. Per-model components, if written, go to a separate file.
- Evaluator invocation (correction): BiotiteDockQ is constructed with `parallel_io=False`, so it reads the models in its own process. PINDER's parallel reader starts worker processes with the `spawn` method, which re-imports the main program from its file; a program given to Python on standard input has no such file, and the workers then fail and the pool never returns. `evaluate.sh` carries the evaluator's Python program in its own text (for example in a quoted here-document written with `cat`), writes it at each call to a regular file under `CMP_EVAL_OUT` (for example under `CMP_EVAL_OUT/tmp/`), and runs it as `"$VPY" <that file>`. It never runs `python -` with a here-document or any other standard-input program, and never runs a Python file kept under `harness/`, which is not on the box.
- `cmp_files.json`: `transforms` and `scores` at `out/docking.out`; `coords` at `{"glob": "out/model_*.pdb"}`; `dockq` at `eval/dockq.json`.
- `versions.sh`: for A0 and A2 the `megadock` executable, for A1 and A3 the `megadock-gpu` executable, and for the evaluator the Python interpreter that runs it, each with its version string (the MEGADOCK commit for the MEGADOCK arms, the installed PINDER version for the evaluator).
- Reproduce for A0: no published anchors exist for these inputs. `run_anchors.sh` writes `out/anchors_measured.json` as `{}`, as earlier runs of this route did. `run_command.sh` may run A0's two commands once on input `f1a19` as a smoke check of the build; it compares nothing.

Boundaries

- No agent, adapter or harness script computes, prints or asserts any difference between arms, any tolerance or any summary of DockQ values. The pipeline records and compares the outputs.
- Preserve every invocation's files, failures and timeouts as they are. Do not rerun any invocation outside the pipeline's schedule.
- If intake or the harness cannot express this run within these boundaries, report the exact contract gap and stop before paid work.
