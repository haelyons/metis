# Takeaways from the first timing run

Footnote [1] applies to every number below. The model timed is a four-parameter daily river-flow model (GR4J), rewritten in the JAX software library. It ran on one A10 graphics card with a 30-core processor on the same machine. The reference implementation (airGR) never ran.

## What was the research question, and the hypothesis?

A planning document, called "the card", proposes calibrating river-flow models for 671 catchments at once. It predicts that graphics-card speed is not what limits how many catchments get full Bayesian calibration. Bayesian calibration here means sampling many plausible parameter sets per catchment.

The card rested on two guesses it promised to measure first. One was the time of a single batched model run over 2,684 chains, guessed at 2 ms. A chain is one sampler walking through parameter values. The other was processor time for 100,000 steps, guessed at 3 hours.

The question: do both guesses hold, and does the card's decision rule give its expected answer ("if_not")?

The hypothesis: with measured times, either the graphics-card run takes at least 1 hour, or it beats the processor by under 20 times. Either one gives "if_not". The card's own gate also requires the main run to take at most 6 hours.

## What did the experiment try to find?

It timed the model on the graphics card and on the processor at 268, 1,340 and 2,684 chains, each over 7,300 days. It also timed 1,000 steps of a simple sampler, to measure how much a real sampling step costs beyond a bare model run. Then it put the measured numbers into the card's own formula.

It did not run any real calibration, use any real catchment data, or test the model on a second implementation of the loop. The forcing data was one basin's rain and evaporation series, tiled across chains.

## What was predicted, and what happened?

Each line gives the refuting threshold, then the measured number [1].

- Anchor, reference code: airGR should reproduce a fit score of 0.495, within 0.02 [1]. It did not run. The record says "not run". Nothing was measured [1].
- Anchor, our rewrite: should score within 0.02 of 0.495 and match airGR daily flows within 1 percent [1]. It scored 0.49478 on the graphics card and 0.49477 on the processor [1]. The flow comparison was skipped. The record says "pass, page value only" [1].
- Claim A, graphics-card time for 2,684 chains: the guess of 2 ms holds if the median is between 0.67 and 6 ms [1]. The median was 88.36 ms over 30 passes [1]. REFUTED, 44 times the guess [1].
- Claim B, processor hours: the guess of 3 hours holds if the derived value is between 1 and 9 hours. The derived value was 29.84 hours, from 1,037.50 ms per pass [1]. REFUTED, 9.9 times the guess [1].
- Claim C, the card's expected "if_not": refuted only if the main run is under 1 hour and the speedup is at least 20. The main run was 2.46 hours and the speedup was 12.11 [1]. The card's answer holds [1].
- Card gate: main run at most 6 hours. It was 2.46 hours, so it passed [1]. With the card's own overhead factor of 4, it would be 9.82 hours and fail [1].
- Scaling, report only: throughput should rise about 10 times from 268 to 2,684 chains, within 20 percent. It rose 8.76 times, and the record reads "linear" [1].

The overhead factor is the cost of a sampling step divided by the cost of a bare model run. It was measured as 1.0035 on the graphics card and 1.0354 on the processor [1]. The card had assumed 4 [1].

Two guesses missed by more than 3 times. The design calls that a finding about the card's cost estimates, whichever way the decision falls [1].

## Is this what we expected?

Partly. The card's verdict held. Its two numeric guesses did not. Both were refuted, one by 44 times [1].

The verdict holds by a thin margin. The speedup was 12.11 against a limit of 20, and the main run was 2.46 hours against a limit of 1 hour [1].

The verdict also rests on an unchecked overhead of about 1. Exploratory: with the overhead set to 4, the speedup was 11.74 and the verdict was still "if_not" [1].

The run is labelled valid. The only label on it is "anchor by page value", meaning the reference code did not run. Nothing was voided.

Supporting checks all passed. A 100 ms sleep read as 100.32 ms on the graphics card and 100.20 ms on the processor [1]. A 730-day pass took 0.1020 of a 7,300-day pass on the graphics card [1].

## What in these files does not fit

### Open questions

1. Is the sampling step too cheap to stand for the real job?
   - The test step is one model run plus one Gaussian score. The overhead was 1.0035 on the graphics card, from 88.67 ms against 88.36 ms [1].
   - The real job also stores samples, checks convergence and may need careful proposals. The true factor could be well above 1.
   - The 6-hour gate and the "at least 1 hour" clause depend on this factor. At 4, the main run is 9.82 hours and the gate fails [1].

2. Was the test sampler stuck?
   - On the graphics card, seed 1, the share of accepted proposals fell from 0.2278 in the first 100 steps to 0.0337, then 0.0075 [1]. By the tenth block it was 0.0015 [1]. The processor fell from 0.2277 to 0.0015 [1].
   - Overall acceptance was about 0.029 in every run [1]. Proposals were 5 percent of each parameter's range, likely too wide for settled chains.
   - Exploratory: cost per step is mostly the model run, so a stuck sampler probably costs the same per step. Steps needed was never studied. Real runs may need tuned proposals and more than 100,000 steps. The hours figure counts steps, not steps needed.

3. Are the timed parameters realistic?
   - The 2,684 parameter sets were drawn uniformly over the full airGR allowed range. In these files, 2,554 have store capacity above 1,000 mm, and 2,657 have an exchange term beyond plus or minus 100 [1].
   - The median store capacity was 10,793. The question claims real catchments sit far lower. No file here shows that. Run time could change on extreme parameters.
   - The only check compared identical chains with distinct parameters. On the graphics card, identical chains took 87.67 ms and distinct ones 88.36 ms [1]. On the processor, identical took 1,056.95 ms and distinct 1,037.50 ms [1].
   - The question as posed had the graphics-card labels reversed. Also, that check varies parameters across chains, not toward realism.

4. Is the graphics card mostly idle, and why was 8.76 called "linear" [1]? [1]
   - Median time rose from 77.31 ms at 268 chains to 82.45 ms at 1,340 and 88.36 ms at 2,684. Ten times the chains cost 1.14 times the time [1].
   - The model runs 7,300 sequential days, about 12 microseconds each. The 730-day control, at 8.99 ms against 88.17 ms, shows time follows day count [1]. So the card is likely far from full [1].
   - The design said a ratio below 10 means "saturates below 2,684 chains". That reading runs backwards. A ratio near 10 means time stayed nearly flat. The label "linear" hides this.
   - Sizes beyond 2,684 chains were never run. The processor went from 131.12 ms to 1,037.50 ms, a ratio of 7.9 [1].

5. Why did two wrong guesses give nearly the same ratio?
   - The graphics card measured 88.36 ms against 2 ms [1]. The processor derived 29.84 hours against 3 hours [1]. Yet the speedup was 12.11, near the guess-based 13.5 [1].
   - The speedup is set by the ratio of the two guesses, not by either absolute time. Both were wrong by a similar factor, 44 and 9.9 [1]. The files do not say what the guesses were based on [1].
   - So the decision rule tests a ratio, and the guessed times were barely consulted. The ratio landed under 20, but the margin is thin.

6. What was actually compared in the model check?
   - The airGR install stopped when the package download failed. The record shows an exit code of 100, and the build step was "not tried". The model check is recorded as "pass".
   - What passed: our rewrite scored 0.49478 against a rounded number, 0.495, copied from a web page [1]. The tolerance was 0.02 [1]. No daily flows were compared [1].
   - Held-out values also matched the page: 0.3360 against 0.336, and 0.5699 against 0.570 [1].
   - The design said timing is void if the model is not the right one. That test was weakened. A retry with refreshed package lists was never tried.

7. Does the timing survive 64-bit arithmetic?
   - All numbers are 32-bit floating point, the library default. airGR's reference is Fortran, normally 64-bit. The design does not list precision under what it does not test.
   - Cards of this class run 64-bit far slower. Long recurrences may need it for accuracy. The 88.36 ms may be a best case [1].
   - The card was also priced on a different graphics card, an A6000. This run used an A10 at 1.29 dollars per hour [1]. The design records that swap, but no one examined its effect.

8. Does the processor denominator match what the card intended?
   - The 1,037.50 ms figure ran on 30 cores [1]. No file records how many threads the library used. The environment file lists no thread or compiler settings [1].
   - Time rose 7.9 times for 10 times the chains, from 131.12 ms to 583.16 ms to 1,037.50 ms [1]. That suggests parallel work or fixed costs, not a clean single-core baseline [1].
   - The speedup is the second leg of the decision rule. A different processor job would change it. The 20-times threshold has no stated source.

### Found while reading

- The processor sampler probe took about 1,080 seconds per 1,000 steps, roughly 18 minutes. That is a cost of the test, not a flaw [1].
- The anchor window is only 59 days. It checks arithmetic on one basin, not behaviour across basins. The design already declares this.
- The record gives main run hours with no confidence interval. Only three seeds were used, and they differ only by forcing offset. Spread among the 30 passes was small: 88.28 to 88.78 ms [1].
- The sampler probe's acceptance is nearly the same on the graphics card and the processor, to four digits. That is consistent with both running the same arithmetic [1].

## Raw samples, verbatim

This is one row of the input table of timed parameter sets, the first four sets as stored in the parameter file (first 12 lines).

```
{
 "n": 2684,
 "order": [
  "X1",
  "X2",
  "X3",
  "X4"
 ],
 "params": [
  [
   18414.55963509567,
   5625.28872940942,
```

This is one randomly chosen graphics-card timing row at 268 chains, which is an output row.

```
{"arm": "gpu_timing", "backend": "gpu", "device": "cuda:0", "driver_version": "570.148.08", "dtype": "float32 (JAX default)", "forcing_offset_days": 3, "gpu_count": 1, "gpu_name": "NVIDIA A10", "instance_type": "gpu_1x_a10", "jax_version": "0.6.0", "jaxlib_version": "0.6.0", "lambda_instance_id": "d607a8f8da3249d0ac3cb985100b7458", "ms": 77.37049000002116, "n_chains": 268, "n_days": 7300, "params_mode": "distinct", "price_usd_per_hour": 1.29, "repeat": 7, "run_labels": ["anchor by page value"], "run_valid": true, "run_void_reasons": [], "seed": 3, "vcpu_count": 30, "warmup": false, "written_utc": "2026-10-20T03:26:28+00:00"}
```

This is one randomly chosen processor timing row at 2,684 chains.

```
{"arm": "cpu_timing", "backend": "cpu", "device": "TFRT_CPU_0", "driver_version": "570.148.08", "dtype": "float32 (JAX default)", "forcing_offset_days": 3, "gpu_count": 1, "gpu_name": "NVIDIA A10", "instance_type": "gpu_1x_a10", "jax_version": "0.6.0", "jaxlib_version": "0.6.0", "lambda_instance_id": "d607a8f8da3249d0ac3cb985100b7458", "ms": 1072.0158800000092, "n_chains": 2684, "n_days": 7300, "params_mode": "distinct", "price_usd_per_hour": 1.29, "repeat": 8, "run_labels": ["anchor by page value"], "run_valid": true, "run_void_reasons": [], "seed": 3, "vcpu_count": 30, "warmup": false, "written_utc": "2026-10-20T03:27:32+00:00"}
```

This is one randomly chosen block row of the sampler probe, which shows the falling acceptance.

```
{"acceptance_rate": 0.0020380029806259313, "accepted": 547, "arm": "overhead_probe", "backend": "cpu", "block": 7, "device": "TFRT_CPU_0", "driver_version": "570.148.08", "dtype": "float32 (JAX default)", "gpu_count": 1, "gpu_name": "NVIDIA A10", "instance_type": "gpu_1x_a10", "iterations": 100, "jax_version": "0.6.0", "jaxlib_version": "0.6.0", "lambda_instance_id": "d607a8f8da3249d0ac3cb985100b7458", "ms": 105801.67588299992, "ms_per_iteration": 1058.0167588299992, "n_chains": 2684, "n_days": 7300, "price_usd_per_hour": 1.29, "proposal_fraction": 0.05, "run_labels": ["anchor by page value"], "run_valid": true, "run_void_reasons": [], "seed": 1, "vcpu_count": 30, "warmup": false, "written_utc": "2026-10-20T03:46:34+00:00"}
```

This is the stored install status for the reference code, which shows why it never ran.

```
apt_rc=100
rcmd_rc=not_tried
r_libs_user=/home/ubuntu/m1_run/Rlib
```

Gate outputs, run on a copy truncated at the raw-samples heading:

```
/tmp/claude-1000/-home-hal-dev-interp/72fa6ea2-188d-4e00-b467-74ae55869166/scratchpad/trunc.md: 3.9 codes/1000 words (7 codes, 1795 words); threshold 10.0
0 unscoped result sentence(s)
```
