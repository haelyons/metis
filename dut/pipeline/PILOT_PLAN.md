# Pilot plan: experiments first, benchmark first (pre-hackathon, from 2026-10-25)

Resume file. Each unit is small, is committed on its own, and leaves the system working. To pick up, read this file,
find the first unit not marked DONE, and continue from it.

## Owner's direction (2026-10-24/25)
- Refocus: autonomous scientific parallelism. Start from a credible workload: a field benchmark (inputs, known
  results, a strong baseline). The blind01 benchmark comes in the owner's brief. On other runs, Metis finds one or
  states clearly that none is available.
- Calibrate before committing: reproduce the benchmark's known results (anchors) at representative scale, and profile
  the real bottlenecks before designing anything large.
- Two independent evaluations: scientific validity (anchors), and parallel versus optimised baseline. Add an
  equivalence check of the outputs, compare at equal cost, and have the baseline tuned by someone other than the
  method's author. Measure both a speedup at equal outcome and outcome against compute.
- Keep the blind operator. Scientific agents read the content; the operator reads only fixed-schema signatures.
- Budget: compute USD 2,000 for this pilot (no ledger balancing needed). Inference is scarce: Claude was at 95 % of
  the weekly limit on 2026-10-25, and the OpenCode Go usage limit was hit on 2026-10-23. Trade tokens for GPU hours.
- Codex CLI (0.164) is installed locally; use it as a further agent family. Open models served on Lambda are an option
  if useful and efficient.
- Two takeaways: an operator takeaway (mechanical, no domain content, shareable) and a research takeaway (agents).

## Current system (as of 2026-10-25)
- `dut/pipeline/idea/wf.js` runs workflow scripts. `agent()` calls go to a primary family (opencode or claude) and,
  on failure, to the other family as understudy (`understudy.js`, `config.json`). The runners are `oc.js` (OpenCode;
  a usage-limit 429 now fails fast) and `claude_cli.js`.
- `dut/pipeline/launch.js stage`, called from `experiments/blind-01/measure.sh`, runs the m4 route: design, gate,
  build, review, tests, fix, ask and post, then the Lambda launch, score and post. That route works end to end, but
  it is heavy on inference (m4: 34 builds, 19 reviews, 16 gate addenda, a 39-call post).
- On Lambda: the environment of record lives on the filesystem `metis-env-us-east-1`, the launcher fetches the
  results, the box is held open with a fixer, and the summary carries a compute table.

## Rules
- Tests: separate agents for design and implementation, and for tests; neither sees the other's code (the m4 rule).
- Every change an agent makes to pipeline code is verified by the operator (the tests re-run, a live check, the key diffs read) before it is committed.
- Karpathy guidelines: the smallest change; subtract before adding.

## Units
- U1 codex family: DONE 2026-10-25 (Codex wrote it; the operator verified: e2e and selftest pass, live codex call ok in 37 s). Gap: Codex wrote both the code and its e2e checks, which the testing rule below forbids; an independent test pass is still owed. Add `idea/codex_cli.js` (`codex exec --json -o --output-schema --sandbox`) and make the
  understudy a chain (primary, then up to two fallbacks, from config; default opencode, then codex, then claude).
  Add codex to the e2e stub test. Verify with the e2e test and one live call.
- U2 signatures and the operator takeaway: TODO. Add `measure/SIGNATURE.md` (a fixed-enum schema: stage, status,
  exit and error class, depth, wall_s, gpu_s, usd, tokens per stage, validity flags, reproducibility blockers) and a
  mechanical `OPERATOR_TAKEAWAY.md` written by `score` in place of PREDICTIONS_SCORED.md. No model calls.
- U3 dev box: TODO. `measure.sh devbox up|status|down`: a long-held Lambda box with the environment filesystem
  attached and `env/box.sh` for agents. It stops itself when idle; the owner authorised always-on cost.
- U4 benchmark route (m5): WAITING for the owner's brief. Steps: probe the baseline on the dev box (reproduce the
  anchors), profile it, seal the predictions, pick a parallelisation from a fixed menu, implement it as a diff,
  evaluate (anchors, equivalence, speedup at equal cost, outcome against compute), then write both takeaways.
- U5 lean cuts on that route: TODO. Post in one or two calls, the gate once (and again only on a scope change), one
  review per launch, the baseline's own tests in place of the tests author.
- U6 open models on Lambda (vLLM as an OpenCode provider): NEXT (brought forward by the owner 2026-10-25). One H100 serves
  one open model; OpenCode reaches it through an ssh tunnel. Check: re-run the anchor diagnostics brief (DIAG_3) and
  compare its one-line answer with mimo's; measure tokens/s and USD per call. Reference systems: AISLE's
  github.com/weareaisle/nano-analyzer and github.com/stanislavfort/mythos-jagged-frontier.
