# blind-openmm run2: content review (after the sealed blind diagnosis, 5acccb0)

## What intake did
- One search call, using the hint, and one candidate inspected; the agent stopped at the first qualifying one. It selected the same study as run1: the OpenMM 7 paper's energy-conservation benchmark (Eastman et al. 2017, PLoS Comput Biol), `SI/Benchmarks/energyBenchmarks.py`. The workload is DHFR (23,558 atoms, PME, VerletIntegrator, 2 fs): 10 trials of 500,000 steps in each of single, mixed and double precision. That is 30 simulations, 30 ns, and the score is the energy-drift slope.
- Evidence access works now. Both supplementary archives were downloaded and hashed (13.7 MB and 20.7 MB, with sha256 recorded). The licence was established as permitted and the data as available. The run1 blocker, the network allowlist, is gone (7c14eef).
- Anchors: three references, the published mean drift per precision (Table 5) with standard errors, and no tolerances. U20 is working as intended.
- baseline.json has `repo`, `build_commands`, `run_commands` and `published_configuration`, and `commit` null with a reason. The agent recorded an immutable pin under the key `immutable_pin`: OpenMM 7.0.1 plus the archive and script sha256.

## Cause of the FAIL
The intake check requires `commit` or `pin` in baseline.json (SCHEMAS.md: "plus commit or pin"). The prompt says "repo, commit or immutable pin, build_commands, ...". It never names the key `pin`, so the agent's `immutable_pin` was a correct pin under a name the check does not read. This is a pipeline defect: the prompt and the check disagree on a key name. It is not a missing pin.

## Blind hypotheses scored
- H1 0.35, no commit or pin: **true in effect, wrong in mechanism**. A pin existed; its key name did not match.
- H2 0.3, an EXECUTION field empty: **false**. All four fields are present.
- H3 0.2, a baseline command field missing: **false**.
- H4 0.15, a missing or invalid file: **false**.

## What comes next, if intake passes
- **Build:** the baseline is OpenMM 7.0.1 built from source through an interactive `ccmake` workflow, on a CUDA 7.5-era toolchain. A modern stock image (CUDA 12, Hopper or Ampere) may not build it, and the pipeline forbids substituting a released OpenMM for the published baseline. Reproduce on setup is the likely next stop, and that would be a legitimate measured finding.
- **Budgets:** the agent set `stage_budgets_s` up to 604,800 s (seven days) for anchors, profile, method_run and evaluate. The chain bounds a run at 5.8 h of pipeline time and the box at 6 h. Nothing at intake compares the workload's expected cost with what a run can spend, so a 30 ns run including double precision would be cut by the chain rather than judged by the pipeline.
- **The hint:** it selects this study twice out of two. As written ("a fixed set of independent simulations with distinct random seeds") it describes the drift study's trials better than a throughput benchmark. The study's script has no seed interface ("implicit random seeds"), so even the hint's "distinct random seeds" is not met by the published command.

## System issues found (for the next units)
1. **U39:** the intake prompt names baseline.json's `pin` key exactly (`commit` or `pin`), along with every key the check reads.
2. **Intake reporting:** a FAIL on incomplete files is invisible in the signature. A closed list of the missing required keys (contract key names only, no values) would let a blind operator see it.
3. **Intake cost:** budgets above what a run can spend are accepted silently. That needs an owner decision on a per-stage ceiling before it becomes a gate.
4. **Intake stops at the first qualifying candidate** (again), so the throughput benchmark (`benchmark.py`) is never compared.
