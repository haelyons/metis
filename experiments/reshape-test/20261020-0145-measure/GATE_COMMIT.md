# GATE COMMIT: measure run m1 (triage wf_1afd659f-b55)

Date: 2026-10-20. Written by the operating session as gate. The owner set the budget rules on 2026-10-20 (RUN.md);
every other answer below is the gate's own and is recorded as such.

## Inputs read (and nothing else)

| File | sha256 |
|---|---|
| `out/design_record.json` | `f31e3c3b15e738fd6e9ac51736f5102d12f0af2d149932a12dd00078c0992a15` |
| `out/triage_wf_1afd659f-b55_return.json` | `9f179ee2d941f0c119545552b29e54be3ff5d71361785f36dbabea0be04d7e3e` |
| `QUESTION.md` | `fe110be5c0209d88a7e745789649ee38ea580e1daf14bb69b7745497b00a11d8` |
| `out/design.json` | `ae8d3be1d79602d6b70d5a226dc9297a2f84e60d98dec97d3032c2036e64d9cb` |

## What is being gated, in plain words

One rented GPU box times a small rainfall-runoff model (GR4J) written as a scan over 7,300 days, batched over 2,684
parameter sets, on the GPU and on the box's CPU. Two published numbers anchor the model first. The measured times go
into a card's own arithmetic and decide whether the card's prediction (GPU throughput is not the blocker) holds.

## Decision on budget and build

**Budget: APPROVED.** Hard cap USD 5 for this run, one launch, cheapest single-GPU instance with capacity (A10 at
USD 1.29/h if still the cheapest at launch). Within the owner's calibration limit (about USD 10). Project cap USD 500.

**Design: APPROVED FOR BUILD** with the changes below and nothing else.

## Answers of record

Each item gets one verdict: ACCEPTED AS-IS, REJECTED, or QUEUED CONTROL.

### Diff departure questions (5)

- **D1 (A10 replaces A6000).** ACCEPTED AS-IS. The decision rule compares GPU and CPU on the same box; the rate and
  vCPU count are recorded and the cost block is recomputed at the recorded rate. The label on every timing endpoint
  reads "measured on <instance> (card priced an A6000)".
- **D2 (tiled single-basin forcing).** ACCEPTED AS-IS, with the control under R1 below. The CAMELS fidelity check
  stays out of scope and is listed in does_not_test.
- **D3 (measured overhead replaces the DESIGN constant 4).** ACCEPTED AS-IS. Both numbers are reported; the decision
  rule E5 is read with the measured overhead; E5 is also reported with overhead 4 as a sensitivity line, labelled.
- **D4 (install R and airGR on the box).** ACCEPTED AS-IS. One attempt each for `apt-get` and `R CMD INSTALL`. If
  either fails, E1 is written NOT_RUN with the error text, E2 reduces to the NSE check against 0.495 alone and is
  labelled "page value only; no independent code ran", and the timing endpoints proceed. The run is then labelled
  "anchor by page value" throughout.
- **D5 (phase gpu_bench only).** ACCEPTED AS-IS. The run resolves the card's prediction through the card's own
  derivation from measured inputs. TAKEAWAYS must say so in its first paragraph.

### Grounding (reader verdict: null)

- **G1.** The isolated reader did not run: the Workflow could not find the `triage-reader` agent type in this
  session (agents load at session start; the role files were copied after). Recorded as a deviation. The gate's own
  grounding, arithmetic and file checks only: every committed input's sha256 in `out/INPUT_HASHES.txt` matches
  QUESTION.md; the airGR page values (0.495 and 0.57 for X = 165.05, 6.46, 422.50, 2.45; 0.336 and 0.777 for the
  generalist set X = 291, 0.30, 109.10, 2.01; calibration period 1990-01-01 to 1990-02-28; validation period
  1990-03-01 to 1999-12-31) were fetched twice and agree. No other number in the design is cited. ACCEPTED with this
  note; the post-run reader will ground the measured numbers in the raw rows.

### Run queue (1)

- **R1 (per-chain distinct parameters).** QUEUED CONTROL, binding on the build. Every timing arm uses 2,684 distinct
  parameter vectors drawn uniformly, seed-fixed, within the parameter ranges airGR's own transformation functions
  define (read `airGR/R/TransfoParam_GR4J.R` in the committed tarball; do not take ranges from memory). The anchor
  arms use the fixed X. A second timing row with all chains at the fixed X is also written, labelled "identical
  chains", so any broadcasting shortcut shows as a gap between the two rows.

### Instrument queue (7): validation controls, all inside the run, no extra spend

- **I1 (E1 readout, airGR NSE).** QUEUED CONTROL: held-out ground truth from the same page, not used to set the
  anchor: with the generalist set X = (291, 0.30, 109.10, 2.01) on the same calibration period, airGR must give
  NSE 0.336 +/- 0.02; with the Michel set on the validation period 1990-03-01 to 1999-12-31, 0.57 +/- 0.02. Both
  written as records. If I1 fails while E1 passes, the period reading is suspect and the run is labelled.
- **I2 (E2 readout, JAX vs airGR).** QUEUED CONTROL: the JAX model must reproduce the same two held-out values
  (0.336 and 0.57, +/- 0.02) and match airGR daily flow to < 1% MARE on the validation period as well as the
  calibration period. Plus planted selftest rows: zero rain gives zero quickflow; the unit hydrograph ordinates sum
  to 1 within 1e-9; mass balance closes within 1e-6 over a planted year.
- **I3 (E3 readout, GPU timer).** QUEUED CONTROL: the timing harness measures a 100 ms `time.sleep` within
  +/- 5 ms (planted known duration), and a 730-day scan at 2,684 chains takes between 7% and 13% of the 7,300-day
  scan (linearity in depth). Both written as records.
- **I4 (E4 readout, CPU timer).** QUEUED CONTROL: same two checks on the CPU backend.
- **I5 (E5 derivation).** QUEUED CONTROL: planted arithmetic in the selftest: ms = 2 and overhead = 4 give
  main_run_hours 0.2222 (the card's own figure); ms = 20 gives 2.2222; speedup with cpu_hours 3 gives 13.5 and
  1.35. Exact to 4 digits.
- **I6 (E6 gate).** QUEUED CONTROL: planted rows at main_run_hours 5.9 (pass) and 6.1 (fail) must produce the
  pass and the "Stop and replan" label; the planted gate-failure row must set run_valid false in every record written
  after it.
- **I7 (E7 throughput).** QUEUED CONTROL: planted arithmetic: 2,684 chains x 7,300 days in 60 ms gives
  3.2655e8 chain-steps per second; the ratio check at 268 vs 2,684 on planted equal times gives exactly 10.

## Labels

- Every timing record carries: instance type, GPU name, driver, jax version, vCPU count, price per hour.
- If E1 or E2 fails: run_valid false everywhere; timing rows are still written and labelled "descriptive only;
  anchor failed".
- If the box stops before all sizes run: finished rows are reported, each labelled "incomplete run: descriptive
  only, no verdict".

## Checks the gate made before answering

Arithmetic only, on numbers in the inputs. No experiment was run.
- The skeptic's band arithmetic reproduces: 1e5 x 0.67 ms x 4 / 3.6e6 = 0.0744 h; 1e5 x 6 ms x 4 / 3.6e6 = 0.667 h;
  speedup 1 h / 0.667 h = 1.5 and 9 h / 0.0744 h = 121.
- Time box: 2 h at USD 1.29 = USD 2.58; with 1 h setup slack the cap of USD 5 holds at a 3.5 h box.
- Chains: 671 x 4 = 2,684; 67 x 4 = 268; 335 x 4 = 1,340.

---

## Addendum after launch 1 (2026-10-20, 03:1xZ): attempt 2 authorised

**New input of record.** `results_m1/out/logs/pip_install.log` and `results_m1/out/logs/stop.log` from launch 1 (box
490e3fae09ad433f82b7ffc6bf2762ee, A10, us-east-1): `pip install --user -U "jax[cuda12]" pyreadr numpy` downloaded at
about 450 kB/s and hit its 1500 s timeout (exit 124) inside the 766 MB cuDNN wheel; `onbox_m1.sh` stopped cleanly with
rc=2, run_valid false, no stage run. The operator then found that the image already provides JAX 0.6.0 with a CUDA
device (`python3 -c "import jax; print(jax.devices())"` gave `[CudaDevice(id=0)]`).

- **A1 (toolchain).** REJECTED: the design's "pip install -U jax[cuda12]". REPLACED BY: use the image's preinstalled
  JAX as is (no upgrade, no CUDA wheels); `pip install --user pyreadr` only; the GPU assertion stays and still exits 3
  if JAX sees no GPU. Record `jax.__version__` and `jaxlib.__version__` in env.txt and in every timing record. This
  is the same rule `frozen/remote_run.sh` applies to torch.
- **A2 (summary file).** QUEUED CONTROL: the runner writes `results_m1/out/m1_summary.json` after the endpoints
  stage (and after an early stop): run_valid, labels, and every endpoint and control decision. It exists so the
  launcher's criticals-first fetch has a small file to verify. It restates records; it decides nothing.
- **A3 (launch 2).** Budget: a second launch is authorised. The cap stays USD 5 for launches 1 and 2 together.
  Launch 1 cost about 0.6 h at USD 1.29/h (exact figure from the audit log once posted). Same instance type if it has
  capacity, else the cheapest single GPU with capacity, recorded.
- **A4 (launcher).** The adapted launcher is unchanged. Observation of record: its poll loop printed nothing for
  about 26 minutes and then reported the DONE marker "after 60s"; the elapsed counter counts only the launcher's own
  sleeps (known deviation D3 in the lineage). Not repaired here; noted for the launcher's next frozen version.

Everything else in this gate stands. The build is re-run through pipeline.js build mode with the updated directive;
no built file is edited by hand.
