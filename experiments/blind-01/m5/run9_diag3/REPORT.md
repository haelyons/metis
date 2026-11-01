# Run9 input format classification

Kernel CSV is **empty**, not status text or an unmatched header. Memory and API CSVs are also empty. Current parser rejects all three separately. Treating only kernel report as having no rows still fails on memory report.

## Scope and method

Evidence sources: seven files in `run9_diag2/work/`, `run9_diag2/REPORT.md`, and `run9_diag/REPORT.md`; prior status was also read as requested. No linked experiment records were opened. Seven input files were copied unchanged into `run9_diag3/work/`; byte comparisons and SHA-256 values appear in [validation.json](validation.json). No workloads, network requests, box contact, git commands, credential reads, or pipeline edits occurred. All writes stayed within `run9_diag3/`.

Local check: `python3 -I -B run9_diag3/check_inputs.py`. [check_inputs.py](check_inputs.py) imports existing `profile_summarise.py` with bytecode disabled, calls its functions against copied inputs, and temporarily replaces only kernel report handling in memory for the requested counterfactual. Original function is restored afterward. No candidate parser fix was applied.

## Evidence for categories

| Status key | Value | Evidence |
| --- | --- | --- |
| `kern_file_state` | `empty` | Kernel CSV is exactly 0 bytes. No text, CSV header, or data rows exist. |
| `stats_log_says_no_kernel_data` | `yes` | Copied `stats.log` explicitly says `does not contain CUDA kernel data.` |
| `stats_log_says_skipped` | `yes` | Same kernel diagnostic begins `SKIPPED:` after kernel report's `PROCESSED (EMPTY RESULTS)` record. |
| `duration_column_form` | `not_applicable` | No header exists; duration-column spelling and units cannot cause this instance. |
| `other_reports_parse` | `neither` | Independent calls to current `report_rows()` on memory and API copies both raise `ValueError: missing CSV header`. Each CSV is 0 bytes. |
| `succeeds_if_kern_has_no_rows` | `no` | Returning `[]` for kernel only lets `summarise()` advance to memory report, which raises same exception. Call sequence saved in validation output. |
| `workload_has_cuda_kernels` | `no` | Logs state no CUDA kernel, GPU memory, or CUDA trace data. Telemetry has 39,680 samples, all 0% utilization; 38,622 lie within measured wall interval. Prior `run9_diag/REPORT.md` independently records CPU-only harness configuration with zero exposed GPUs. Classification concerns this recorded workload run. |
| `nsys_version` | `2025` | Version file: `NVIDIA Nsight Systems version 2025.3.1.90-253135822126v0`. |

Copied `stats.log` gives these report-specific diagnostics:

```text
SKIPPED: out/profile/baseline.sqlite does not contain CUDA kernel data.
SKIPPED: out/profile/baseline.sqlite does not contain GPU memory data.
SKIPPED: out/profile/baseline.sqlite does not contain CUDA trace data.
```

Each follows corresponding `PROCESSED (EMPTY RESULTS)` export record. Status lines reside in `stats.log`, not CSV files. This is Nsight's zero-byte empty-result variant for all three reports. Empty bytes alone would not establish intentional absence; corresponding export diagnostics do.

Original `summarise()` also reproduces `ValueError: missing CSV header`. Kernel-only bypass fails before API parsing; independent API test establishes its failure separately. Thus kernel-only correction cannot make current summary succeed. Both prior reports identify additional report-specific wording compatibility: memory diagnostic says `GPU memory data`, API says `CUDA trace data`.

Telemetry alone would not prove absence of short CUDA activity. Here it corroborates explicit no-activity diagnostics and prior report's CPU-only configuration. No broader claim about workload variants or downstream profile acceptance is implied.
