You are an authorized reader for the blind-01 experiment. The owner authorized readers to see its brief and records. The operator who launched you is blind to this experiment's content and sees only `status.json`, as validated enum values; your final reply is not shown to the operator.

Working directory: experiments/blind-01/m5/ of the metis repository (the current directory). Write only into `run6_diag3/`. Change nothing else, run no workloads, contact no box. Network use is limited to package-index metadata lookups: packages.ubuntu.com, launchpad.net package pages, and pypi.org project pages or its JSON API. Download no packages or materials.

## Context
Two earlier diagnoses (`run6_diag/` and `run6_diag2/`; read their REPORT.md and status.json) found that run6's setup failed three times on one missing tool, that the harness rules as the pipeline wrote them forbade installing it, and that the smallest fix is for the rules to permit the install. The probe (`run6/agent/results/probe/probe.json`, or where `dut/pipeline/m5/pipeline.js` puts it) gives the box's OS and version. The operator needs to know which install route the permission must cover.

## Questions
1. Is the missing tool (or the package that provides it) in the Ubuntu archive for the box's release (main or universe), and under which package name?
2. Is it available from PyPI?
3. What does setup need it for: fetching or unpacking inputs, building the baseline, a library the built baseline uses at run time, or something else?
4. Would installing it change the published baseline's code, its configuration, or the stock Python packages (torch included)?

## Rules
- Never read `.keys` files, credential files or anything under `~/.codex/`.
- Do not commit or push; the launcher commits `run6_diag3/`.
- No fabrication. If something cannot be established, use the `unknown` value.

## Outputs
1. `run6_diag3/REPORT.md` for the owner: the answers with evidence (the package names and the index pages you checked).
2. `run6_diag3/status.json`, one JSON object with exactly these keys, each taking only the listed values:
   - `"ubuntu_archive"`: `"main"`, `"universe"`, `"no"`, `"unknown"`
   - `"pypi"`: `"yes"`, `"no"`, `"unknown"`
   - `"role"`: `"fetch_or_unpack"`, `"build"`, `"runtime_library"`, `"other"`, `"unknown"`
   - `"changes_stock_python"`: `"yes"` (installing it by the obvious route would change stock Python packages), `"no"`, `"unknown"`

   No other keys and no free text.

Finish within 15 minutes. End with a final reply that is exactly the contents of status.json.
