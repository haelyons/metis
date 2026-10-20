# GATE COMMIT: measure run m2 (triage wf_da9ff4cd-543)

Date: 2026-10-20. Written by the operating session as gate. The owner set the budget rules on 2026-10-20 (RUN.md) and
said "Proceed with the P card"; every other answer below is the gate's own and is recorded as such.

## Inputs read (and nothing else)

| File | sha256 |
|---|---|
| `out/design_record.json` | `1b88987404151a07ae86256f2a43ad923d5c8f40a89ab6b33b5a56a9288dab59` |
| `out/triage_wf_da9ff4cd-543_return.json` | `1fcace6ae910dd413d9a38fbd7b5e3c1fd0f1c433d74159121f602f0156925fb` |
| `QUESTION.md` | `ea54a9182df53f3e3fe6e7f5844a4e36d72a6b103d0c0f3d99425bfc79ec4810` |
| `out/design.json` | `5de4d72d3545b4249e44fc680fdac649870e92bc7e3f5e45c4d97f37d984e1e8` |
| `out/diff.json` | `e52d30d3405fd957f8cb99e510160ca4ea1e91890442569fba53c4b21dda5200` |

## What is being gated, in plain words

One rented A100 box times two ways of solving one tridiagonal system of N equations: the sequential Thomas algorithm
run by a single GPU thread (the card's baseline) and parallel cyclic reduction (the card's method), for N from 1,024 to
16.8 million, five random systems each. Both are first checked against NVIDIA's library solver and against scipy on the
CPU. The measured times go into the card's own rule and decide whether its prediction (the lever) holds. Beside that,
report-only readings: the CPU library solver as the practical sequential floor, the growth shape of the parallel
solver's time, a batched baseline, and NVIDIA's solver's time.

## Decision on budget and build

**Budget: APPROVED.** Hard cap USD 8 for this run, at most two launches together, `gpu_1x_a100_sxm4` at USD 1.99/h in
us-east-1 (capacity confirmed at 08:55Z). If capacity is gone at launch: the cheapest single GPU with capacity, recorded
as a departure on every timing record. Within the owner's calibration limit (about USD 10). Project cap USD 500; spent
so far USD 2.12.

**Design: APPROVED FOR BUILD** with the changes below and nothing else.

## Answers of record

Each item gets one verdict: ACCEPTED AS-IS, REJECTED, or QUEUED CONTROL.

### Diff departure questions (7)

- **D1 (plain one-thread Thomas).** ACCEPTED AS-IS. The baseline is "the one-thread Thomas this build wrote": recurrence
  values carried in registers, each of a, b, c, d read once per step, scratch written once per step. No variant search.
  The label on every E3, E4, E5 record reads "baseline: one CUDA thread per system, this build's kernel".
- **D2 (no mid-run kernel fix).** ACCEPTED AS-IS. An anchor failure for one solver labels that solver's timing rows
  "descriptive only; anchor failed" and E3, E4, E5 are written NOT_READ. The box is not stopped: the other arms still
  carry information. If the two references disagree with each other, run_valid is false everywhere.
- **D3 ("grows with N").** ACCEPTED AS-IS, with one addition: the record also reports whether any adjacent pair of
  levels shows a decrease, so a reader holding the stricter reading can apply it.
- **D4 (report-only readings).** ACCEPTED AS-IS. Every E6 to E9 record carries `role: "report-only; does not decide the
  card"` and TAKEAWAYS must state the card's verdict (E3) before any report-only number.
- **D5 (timing blocks; K rule).** ACCEPTED AS-IS, with the control under R1 below (launch-latency probe).
- **D6 (REJECT card measured without resample).** ACCEPTED AS-IS. Label on every record: "card dramaturg: REJECT (3
  blocking, citations)". The ledger row carries the same label.
- **D7 (p3, p4 not run; E10 compares the anchor-plus-sweep line only).** ACCEPTED AS-IS.

### Grounding (reader verdict: null)

- **G1.** The isolated reader did not run: the Workflow could not find the `triage-reader` agent type in this session
  (the role files exist at `/home/hal/dev/interp/.claude/agents/` since m1, but agent types load at session start and
  this session predates them). Recorded as a deviation (INTERVENTIONS.md). The gate's own grounding, file checks
  only: the card numbers in `out/design.json` (levels 2^10..2^24; `res_tol` 1e-10; `res_measured` 1e-13; `crossover_n`
  1,024; `speedup_at_nmax` 28; `gate_speedup` 2; A100 SXM 40 GB at USD 1.99/h; `l_anchor_sweep` hours 6, need 2) were
  re-read in the producer reply (`../20261019-2344-tree/out/agents/0008-R1_physical_top_producer/reply.txt`, sha256
  `5edcb633490ee446d7a77a8f32cf246efae31aab79919fe6b21ac4f6aa411b33`) and match. ACCEPTED with this note; the post-run
  reader, if it runs, grounds the measured numbers in the raw rows.
- **Gate observation (not a triage finding).** The skeptics ruled decidability out on design structure. The gate notes
  that the card's baseline (one GPU thread) makes the lever reading very likely regardless of PCR's merit; this is a
  construct risk declared in QUESTION.md, not a defect of the measurement, and E7 is its labelled sensitivity line.
  The sealed predictions (hashed before triage) carry the gate's forecast.

### Run queue (1)

- **R1 (run the sweep; check block times and launch latency).** ACCEPTED: the sweep is the run. The inspection it asks
  for becomes a QUEUED CONTROL, binding on the build: (a) every timed block is at least 50 ms and the block length R is
  recorded per row; (b) one extra arm `launch_probe`: an empty CUDA kernel launched R times under the same block
  protocol gives ms per launch; every PCR row at every level carries `launch_fraction = rounds x ms_per_launch / ms_per_solve`
  and the E3/E4 records report it at 2^10 and 2^24. A `launch_fraction` above 0.5 at 2^10 labels the E4 record
  "crossover at 2^10 is launch-bound".

### Instrument queue (10): validation controls, all inside the run or the selftest, no extra spend

- **I1 (E1 readout, residuals and agreement).** QUEUED CONTROL: planted on the box at N = 2^10, seed 0: (a) the exact
  solution x* = ones with d = A x* must give relative residual <= 1e-14 from the readout; (b) x* perturbed by 1e-6
  relative must give a readout in [1e-7, 1e-5]; (c) the two references (cuSPARSE, scipy) must agree with each other to
  < 1e-8 (the card's fourth check). Written as records.
- **I2 (E2 readout).** QUEUED CONTROL: selftest planted arithmetic: 1e-13 holds; 5e-15 refuted "too pessimistic";
  5e-12 refuted "too optimistic".
- **I3 (E3 readout).** QUEUED CONTROL: selftest planted medians: Thomas [1, 16, 256, 4096, 16384] ms and PCR
  [0.5, 0.6, 1, 10, 40] ms give speedups [2, 26.667, 256, 409.6, 409.6], slope > 0, if_lever; equal speedups at all
  levels give if_not (not growing); speedup(2^24) = 1.9 gives if_not; a lower quartile of 1.8 at 2^24 with median 3
  gives if_lever "within noise". Exact to 4 digits.
- **I4 (E4 readout).** QUEUED CONTROL: selftest planted lower quartiles [1.2, 3, 10, 50, 100] give crossover 2^10
  (holds); [0.8, 1.5, 10, 50, 100] give 2^14 (refuted); all below 1 give none (refuted).
- **I5 (E5 readout).** QUEUED CONTROL: selftest planted 28 holds; 100 refuted above (ratio 3.571); 5 refuted below.
- **I6 (E6 readout).** QUEUED CONTROL: selftest planted PCR ms (2^22, 2^24) = (10, 11) gives g 1.0488 log-like;
  (10, 40) gives g 2 linear-like; (10, 20) gives g 1.4142 between.
- **I7 (E7 readout).** QUEUED CONTROL: selftest planted CPU medians [0.01, 0.1, 2, 40, 160] ms against the PCR
  medians of I3 give speedup_cpu(2^24) = 4 and if_lever under the CPU baseline; CPU [.., 60] at 2^24 gives 1.5 and
  if_not.
- **I8 (E8 readout).** QUEUED CONTROL: selftest planted ratios [1.0, 1.1, 1.5, 2.9, 1.2] hold; [1.0, 3.5, ...] fail;
  throughput factor K / ratio exact.
- **I9 (E9 readout).** QUEUED CONTROL: selftest planted cuSPARSE 10 ms against PCR 30 ms gives ratio 3.
- **I10 (E10 readout).** QUEUED CONTROL: selftest planted wall-clock 0.5 h refuted below; 2 h holds; 7 h refuted above.
  On the box the two timestamps (first anchor solve, last sweep row) are written as a record.
- **Timers (design arm).** QUEUED CONTROL (in-run): 100 ms sleep within +/- 5 ms; cudaEvent against wall-clock within
  5% on one block; a block of 2R solves against R within 15% at N = 2^14, both solvers.
- **Gate propagation.** QUEUED CONTROL: selftest planted E1 failure for Thomas (residual 1e-9) labels Thomas rows and
  writes E3, E4, E5 NOT_READ; planted reference disagreement (1e-7) sets run_valid false in every record written after.

## Labels

- Every timing record carries: instance type, GPU name, driver version, CUDA runtime version, nvcc version, vCPU
  count, BLAS/LAPACK vendor string from scipy, price per hour (from `PRICE_USD_PER_HOUR`), block length R, and the
  two labels "card dramaturg: REJECT (3 blocking, citations)" and "baseline: one CUDA thread per system, this build's
  kernel".
- If the cuSPARSE library cannot be loaded: the cusparse arm is NOT_RUN, E1 is read against scipy alone and labelled
  "one reference only", E9 NOT_RUN; the run continues.
- If the box stops before all levels run: finished rows are reported, each labelled "incomplete run: descriptive only,
  no verdict".

## Checks the gate made before answering

Arithmetic only, on numbers in the inputs. No experiment was run.
- Memory at the top level: 4 arrays x 2^24 x 8 B = 537 MB; PCR ping-pong doubles it to about 1.1 GB; batched K = 16 at
  2^24: 16 x 537 MB = 8.6 GB. All within 40 GB.
- Time box: anchor plus sweep is expected in minutes (one-thread Thomas at 2^24: seconds per solve; PCR: tens of ms);
  the cap of USD 8 holds at a 4 h box at USD 1.99/h.
- Levels: 2^10 = 1,024; 2^14 = 16,384; 2^18 = 262,144; 2^22 = 4,194,304; 2^24 = 16,777,216 (the card's five).
- K rule: 2^28 / N = 262,144; 16,384; 1,024; 64; 16, capped at 256 gives 256, 256, 256, 64, 16.

## Pre-authorisation (learned from m1)

- **A1 (second launch).** If launch 1 halts before the sweep for a toolchain or launcher reason, one more launch is
  authorised within the same USD 8 cap after the cause is recorded in RUN.md and, if the directive changes, the build
  is re-run through pipeline.js build mode. No built file is edited by hand.
