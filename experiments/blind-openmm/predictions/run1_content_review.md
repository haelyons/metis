# blind-openmm run1: content review (after the sealed blind diagnosis, 6386703)

## What intake did
- First search used the hint verbatim. It matched the OpenMM 7 paper (Eastman et al. 2017, PLoS Comput Biol) energy-drift experiment: ten independent 1 ns DHFR simulations, mixed precision, mean drift -0.0047 ± 0.0008 (kJ/mol)/ps. Not the OpenMM benchmark script with published ns/day.
- One candidate inspected of the three allowed; the second search went to the same paper's scripts.
- The supporting archive download failed: `Network access to "journals.plos.org" was blocked: domain is not on the allowlist for the current sandbox mode.` Web fetches of the archive and the 7.0.1 LICENSE were cache misses.
- Gate missing: an eligible anchor with a supported tolerance (published standard errors are not accepted as tolerances), verified inputs, verified permissions. found=false, honestly reported, nothing invented.

## Blind hypotheses scored
- H1 0.35, hint over-specified: **partly true**. The hint's wording selected an energy-drift study rather than a throughput benchmark.
- H2 0.30, no qualifying anchor: **true**. The paper's only reference observation has a standard error and no tolerance.
- H3 0.25, search budget exhausted on large pages: **mostly false**. Two searches were used, but only one candidate was inspected; the agent stopped instead of trying another.
- H4 0.10, network failure in the sandbox: **true**. Codex's network proxy domain allowlist blocked the archive.
Three causes compound; the probability mass was spread too evenly to call any of them.

## System issues found (for the next units)
1. Network: pipeline Codex agents run under `features.network_proxy` with a domain allowlist; journal and data hosts are blocked, so evidence behind a DOI is unreachable.
2. Isolation: pipeline Codex agents inherit every MCP server from the operator's personal Codex config and the operator's personal skills directory (the intake agent loaded a style skill).
3. Intake stops after one failed candidate although three are allowed.
4. Anchor rule: only published tolerances qualify; hint-only intake will rarely find one. Needs an owner decision on a fixed derivation rule.
5. Intake FAIL signs error_class none, exit_kind unknown; a blind operator cannot see why.
6. The box is up during intake, which needs no GPU.
