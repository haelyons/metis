# GATE COMMIT: coolant_proxy, design attempt 2 (run wf_1e76375d-cc7)

Date: 2026-10-18. Written by the gate, standing in for the owner of the research question.

This file answers, of record, every item listed in `out/gate_text_attempt2.md`. It must exist before mode=build.

## Inputs read (and nothing else)

| File | sha256 |
|---|---|
| `out/gate_text_attempt2.md` | `06865cd44bbfffa1509d2d11641b3fdb5d3d50f61b4082568b18b37d26e293bf` |
| `QUESTION.md` | `10926ed874bc71b24b6b1c83d72c58a2864be1028d2d0853d334c036b53e43f6` |
| `out/design_record_attempt2.json` | `9f320ef3d15f224a9bebeb30d7ff4dfe6eeab79230ec9785f2a977de0af6e641` |
| `out/design_wf_b06f2a6a-35f_return.json` (attempt 1) | `fbf3c8aa6ba5e8d820fc795dfa01cd8819a49e16d32e6c574ba4e5360fa21d77` |
| `out/design_attempt2_wf_1e76375d-cc7_return.json` (attempt 2) | `74e482cf78b463995bced9d296b90bc7ab61a69de0650fbefa31aec52326f487` |

The attempt-2 return has the same seed, design, diff, triage and gate fields as the design record.

## What is being gated, in plain words

**The question.** Take eight liquid molecules from a published simulation study. Run about 1 nanosecond (ns) of molecular dynamics for each at 40 °C. Measure how fast the molecules diffuse. Turn that into a viscosity "proxy". Does the proxy put the eight molecules in the same order as their reference viscosities? Success means a Spearman rank correlation (rho) of at least 0.8.

**The design.** The proxy is kT/(6π·D·R). D is the diffusion coefficient. R is the radius of a sphere with the volume one molecule fills. Each molecule gets three reruns. Each rerun is a box of about 15,000 atoms, run 1.0 ns at constant pressure with a 2 femtosecond (fs) step. Work runs in four priority tiers on one rented GPU. Tier 1 is reruns 1 and 2 of all eight molecules. Tier 2 extends rerun 1 to 2 ns. Tier 3 is rerun 3. Tier 4 is a 1 fs timestep check. The design has 12 endpoints, one per claim, and no combined score.

**History.** Attempt 1 halted at the budget check. It priced the run at $200 against a $20 cap, on a guessed speed of 25 ns per day. Attempt 2 prices it at $19. It takes a published GPU benchmark (610.09 ns per day) and multiplies it by a guessed 0.15. That gives 91.5 ns per day, or 530 steps per second at 2 fs. The plan is 12.54 hours at a guessed $1.5 per hour, or $18.8.

**How to read the answers.** Each item gets exactly one verdict:
- **ACCEPTED AS-IS**: the design stands for this item.
- **REJECTED**: the design's choice is not accepted. The text says what is dropped, narrowed or relabelled. Nothing else in the design changes.
- **QUEUED CONTROL**: a named control is added. It fits inside the $19 plan and needs no extra launch.

For a triage finding, the verdict applies to how the design handles that finding.

## Decision on budget and build

**Budget: APPROVED.** Up to $19 of Lambda spend in total, on one single-GPU box. The $20 cap is not raised. The design needs one launch. If a second launch is ever used, it spends what is left of the same $19. It is not new money.

**Design: APPROVED FOR BUILD**, with the changes stated below and nothing else:
- New labels: D1 (what a fail rules out) and F1 (the forced and tautological endpoints).
- Narrowed rules: D3. The non-diffusive count and the window check may only downgrade a result, never refute it. Claim 5 is judged against the three orderings that need no simulation.
- Queued controls: D5 (throughput probe), F2, I2, I3, I5, I7, I8, I10 and I12.

**What the additions cost.** No queued control uses GPU time beyond the planned tiers, and none displaces a tier. The planted checks use seconds of CPU on synthetic data. The real-data checks read files the run already writes. The D5 probe can only shorten the run. The plan stays at 12.54 hours and $18.8.

**Label for a run that stops early.** The design says that if tier 1 cannot finish, the run reports that it did not run to the end and claims no pass or refutation. That stands. Any numbers from finished cells may still be reported. Each one is labelled "incomplete run: descriptive only, no verdict".

## Checks the gate made before answering

These are arithmetic only, on numbers in the five inputs. No experiment was run.
- Chance counts: enumerating all 40,320 orders of eight items gives 439 orders with rho at least 0.8 and 2,318 with rho at least 0.6. Both match the record.
- Within-family chance: enumerating all 576 pairs of four-item orders gives 26 with at least 10 of 12 pairs concordant, and 68 with at least 9. Both match the record.
- Free orderings: molar masses from the molecular formulas in QUESTION.md give rho 0.524. The reference densities give rho 0.048. Both match the record. For context, the paper's simulated densities (built from rounded labels) give rho 0.143.
- Molecules per box: 15,000 divided by atoms per molecule gives 163, 333, 246, 312, 174, 188, 283 and 349 after rounding. These match the record.
- Density bands: ±2% of each paper value gives the record's eight bands.
- Cost model: 610.09 × 0.15 = 91.5 ns per day, which is 530 steps per second at 2 fs. A 600,000-step run takes 18.9 minutes. Tiers 1 to 4 take 5.04, 2.10, 2.52 and 0.60 hours. The total is 12.54 hours, or $18.8 at $1.5 per hour. All of this matches the record.
- Throughput margin: the time limit is 12.0 hours at $1.5 per hour. After 1.0 hour of setup and 15 minutes of spare, tier 1 fits only if the box runs at least 1/2.13 of the guessed speed.
- Size term: from formula masses and the paper's simulated densities, R varies by only a factor of 1.26 across the eight molecules. The reference viscosities vary by a factor of 5.81.

---

## Diff departure questions

### D1. "The question allows two proxy forms. One is Stokes-Einstein-like…"

**REJECTED.** What is rejected is reading a fail of this one form as the answer "no".

A rho below 0.8 rules out only the Stokes-Einstein-like form kT/(6π·D·R). It does not answer the question "no". The question allows a Stokes-Einstein-like or an excess-entropy-like form, and the design tests only the first.

What changes:
- Labels only. Endpoint 3's refutation reads: "refuted for the Stokes-Einstein-like form only; the excess-entropy-like form was not tested."
- The abandon line (rho below 0.6) gets the same label. It says this form is not worth pursuing. It does not say the idea is not worth pursuing.
- A pass (rho of 0.8 or more) answers "yes" for this form.
- Nothing is dropped, and no entropy arm is added.

Running without a finite-size correction is accepted. The correction needs the viscosity, which is the unknown. If the Stokes-Einstein form held exactly, the correction would be 2.837 × R/L of D, where L is the box edge. For these eight boxes that is 25.0% (glycol ether) to 32.2% (squalane). So leaving it out moves one molecule's proxy against another's by at most about 5.8%. Only one reference pair is that close: squalane and hexyl-diphenylheptane, 3.4% apart. The question already says their order is within reference uncertainty.

### D2. "The question says to follow the paper's builder and equilibration protocol…"

**ACCEPTED AS-IS.**
- **2 fs step:** yes. A 2 fs step with hydrogen bonds held rigid is a standard setting, and it is what lets the plan fit in $19.
- **Constant-pressure diffusion:** yes. The question asks for the proxy from the same ~1 ns constant-pressure trajectory that gives the density. Reading D from 0.2 to 1.0 ns follows the question's note that density levels off within about 0.2 ns.
- **Failed density gate:** yes, it may stop the main claim from being judged. The question says the density check comes "before any proxy is trusted". As the design says, the rho is still reported and labelled untrusted.

### D3. "The design adds rules the question does not contain."

**REJECTED in part.** Each added rule is answered below. Only rule (c) keeps the power to refute.

- **(a) Three or more of eight non-diffusive refutes the 1 ns claim "whatever rho shows."** It may not refute. It only adds a label: "apparent D: slope outside the planted band for N of 8 molecules". Claim 2 (convergence) is judged only by endpoints 4 and 5, which are the question's own tests. Reason: the slope band comes from planted random walks with no cage motion and hundreds of molecules. So the band may be very narrow. Long molecules such as squalane could fall outside it in a 0.1–0.4 ns window whatever their ranking does. Triage finding F2 raises exactly this.
- **(b) "Robust" only if rho is at least 0.8 in all three fit windows.** It may downgrade, not refute. A pass in the main window with another window below 0.8 is reported as "passed in the pre-registered window (0.1–0.4 ns); window-dependent". It is not reported as "not established".
- **(c) At least 10 of 12 within-family pairs in the right order.** It may refute claim 4, the question's own family claim. The question gives no number for that claim. A random order reaches 10 of 12 only 26 times in 576 (4.5%), so this is a fair bar. It cannot change the main claim's verdict. The discordant pairs are listed beside the count.
- **(d) Beat every free ordering by more than the rerun spread.** This is narrowed. Claim 5 is judged against the three orderings that need no simulation: molar mass (0.524), reference density (0.048) and XGBoost (0.738).
  - If the main rho is at or below the best of these, claim 5 is refuted. That is the question's own rule.
  - If the main rho is above the best but within the rerun margin, claim 5 is downgraded to "higher than free orderings, within rerun noise".
  - 1/D and simulated density stay as reported ablations, and they cannot refute claim 5. If 1/D matches or beats the proxy, the label is "size term adds nothing". If simulated density matches or beats it, the label is "diffusion adds nothing over density".
  - Reason: both come from the same simulation, so they are not free. Also, R varies by only a factor of 1.26 while the reference viscosities vary by 5.81. So the proxy and 1/D share almost all of their order. Requiring the proxy to beat 1/D by a margin would make claim 5 fail almost by construction.

### D4. "The question asks for stability across independent replicas and agreement with a longer trajectory."

**ACCEPTED AS-IS.**
- **Independent replicas:** yes. Each rerun has its own packed box and its own velocity seed, which is what "independent replica" means in molecular dynamics. Sharing one GPU session does not couple the trajectories. The design already lists what the reruns do not cover (other hardware, builds and box sizes) as untested.
- **Longer trajectory:** yes, the 2 ns extension counts. It is reported as agreement with a 2 ns run, not with long-time behaviour, as the design already says.
- **The 0.8 bar:** yes, it is right. It is the only bar the question gives, and an ordering should agree with itself at least as well as it agrees with the reference.
- **Dropping rerun 3:** if that happens, judging the single remaining pair is accepted.

### D5. "The question judges cost in CPU-hours (processor time)."

**QUEUED CONTROL: a throughput probe inside wave 1.**

The answers to the three questions:
- **Simulated time as a stand-in for CPU-hours:** yes. The force field, engine and box size match the paper's, so cost follows simulated time at a given step. The 2 fs step can only make the proxy cheaper per ns.
- **One tenth (8 ns of 80 ns) as "well below":** yes. The plan uses 3 × 1.125 = 3.375 ns per molecule, which is 4.2% of 80 ns.
- **Spending up to $19:** yes. See "Decision on budget and build".

Why the control is needed. The risk D5 names is real. Tier 1 fits only if the box runs at least 1/2.13 of the guessed 530 steps per second. Attempt 1 guessed 25 ns per day. At 2 fs that is 145 steps per second, 3.7 times slower than this design's guess, and tier 1 would not fit. At 1 fs it is 289 steps per second, 1.8 times slower, and tier 1 would fit. The design's own clock rule first projects after a whole wave of four runs. By my reading of that rule, a box 3 times slower would run two full waves before stopping. That is about 8.8 hours and about $13.2, with no verdict.

How the probe runs:
1. In wave 1, each of the four runs reaches its first 50,000 steps of the constant-pressure stage. That is 150,000 steps per run and 600,000 in all.
2. The runner then reads the combined step rate from the LAMMPS logs.
3. It applies the design's own clock rule to all of tier 1 straight away. Hours used so far, plus the 9.0 million remaining tier-1 steps divided by the measured rate, must fit the time limit with 15 minutes spare.
4. If the projection does not fit, the runner stops all runs and tears the box down. It reports "not run to the end" and gives the measured rate beside the guessed 530.

On a box 3 times slower, this stop comes after about 2.2 hours, about $3.3. The probe uses the same box session. It adds no runs, needs no extra launch and displaces no tier.

---

## Triage grounding

### G. "Claim design-core: grounding = reproduces."

**ACCEPTED AS-IS.** Every number that can be checked before any simulation reproduces. The triage reader matched them, and the gate re-derived these: molar mass 0.524, reference density 0.048, chance counts 439 and 2,318 of 40,320, and 26 of 576. The record says the molar masses were worked out by hand; endpoint 1 recomputes them in code, as designed. No simulation number exists yet. R1 and R2 will produce them.

## Triage findings

### F1. "[EXPLAINS] decidability by construction: any endpoint forced, unable to occur, or deciding a different question"

**REJECTED.** What is rejected is counting the forced or tautological endpoints as tests. Changes, all labels:
- **Endpoint 6 (cost)** is reported as "met by the plan's arithmetic: 3.375 ns per molecule, 4.2% of 80 ns; not an empirical test". If endpoint 4 (rerun stability) fails, claim 3 is labelled "not shown", because the number of reruns needed is then unknown.
- **Endpoint 1 (data-only pre-check)** stays a go/no-go integrity check. A failure stops the run before any spend. A pass is labelled "integrity check, not evidence".
- **Endpoint 3 (main rho)** is unchanged. It is open and has a named refutation.

### F2. "[NEEDS_RUN] The fit window (0.1-0.4 ns), timestep, box size and the cube-root radius term could make D or the proxy degenerate…"

**QUEUED CONTROL.** The control has two parts:
- R2's own readouts: each molecule's log-log slope in the main window, and the main rho in all three windows.
- One added readout from files the run already writes: the log-log slope of each molecule's mean-squared displacement in the 2 ns extension, at lags of 0.1 to 0.9 ns. This shows whether long molecules become diffusive at longer lags.

It runs in the session's analysis pass on tier-1 and tier-2 output. It uses no GPU time beyond the planned tiers and displaces no tier. If tier 2 does not finish, the extension readout is reported as not run. Under D3(a), the outcome can add a label but cannot decide a verdict.

---

## Run queue

### R1. "Planted known-truth check (a)-(d), no GPU, seed 7…"

**ACCEPTED AS-IS.** It needs no GPU and no spend. It is the only proof that every decision label can be reached, and it must pass before any real result is read.

### R2. "Tier-1 runs with the diffusive-regime slope count and the three-window rho sensitivity…"

**ACCEPTED AS-IS.** Tier 1 is reruns 1 and 2 of all eight molecules: 16 runs, 9.6 million steps, 5.04 hours at the guessed speed. It is the least work that reaches the main endpoint, and it sits inside the $19 plan. The D5 probe guards it.

## Author queue

**Empty.** There is nothing to answer.

---

## Instrument queue

Each item asks for held-out ground truth for one endpoint's readout. Unless an answer says otherwise, the "planted" controls below follow the same rules:
- They run beside R1, on the workstation or on the box's CPU in the same session.
- They run before any real result is read.
- They use no GPU time, need no extra launch and displace no tier.
- If one fails, real results are not read until the code is fixed.

### I1. "AUTHOR: validation control for instrument endpoint-1-readout vv1" ("Data-only pre-check, no simulation…")

**ACCEPTED AS-IS.** It is a fixed computation on committed, hash-checked files. The triage reader reproduced it independently (rho 1.0, 0.738, 0.048 and 0.524), and the gate re-derived 0.524 and 0.048.

### I2. "AUTHOR: validation control for instrument endpoint-2-readout vv1" ("Density gate, the first number to reproduce…")

**QUEUED CONTROL.** For every built box (8 molecules × 3 packings = 24), compute the density by hand from the data file. That is the total atom mass divided by the box volume in the file header, converted to g/cm³. It must match LAMMPS's own density at step 0 to within 0.1%. This uses the zero-step read the design already does on the workstation before launch. It needs no box time and no extra launch, and it displaces no tier. A mismatch stops the run before launch. The gate's decision logic is already covered by I11(d).

### I3. "AUTHOR: validation control for instrument endpoint-3-readout vv1" ("MAIN. Spearman rho between the main proxy…")

**QUEUED CONTROL.** This is a planted test of the proxy path.
1. Assign made-up viscosities of 1, 2, … 8 mPa·s to the eight molecules in a shuffle with seed 7.
2. Set each planted D to kT/(6π·η·R), with T = 313.15 K and R from the formula mass and the paper's simulated density.
3. The analysis code must return each planted η to within 1 part in 10⁶, and rho = 1.0 against the planted η.
4. Reversing the planted η must give rho = −1.

This checks the formula, the units and the radius from end to end. It follows the shared planted rules above.

### I4. "AUTHOR: validation control for instrument endpoint-4-readout vv1" ("Stability across reruns…")

**ACCEPTED AS-IS.** It uses the same Spearman function that I11(d) checks (+1 and −1). It applies that function to proxy values that the I3 control checks. It adds no new instrument.

### I5. "AUTHOR: validation control for instrument endpoint-5-readout vv1" ("Agreement with a longer run…")

**QUEUED CONTROL.** Two parts:
1. **Planted.** Repeat I11(a) with a 1.8 ns window and lags of 0.1 to 0.9 ns. Split each planted trajectory into two files at 1.0 ns, the way the extension is written. The recovered-D bias must be within 2 standard errors. This part follows the shared planted rules above.
2. **Real data.** On each extended run, the largest one-frame jump of any molecule's centre across the 1.0 ns join must be no larger than the largest one-frame jump inside either part. If it is larger (for example because of a lost periodic image), endpoint 5 is reported as not judged. This runs in the session's analysis pass on tier-2 output.

It uses no GPU time beyond tier 2, needs no extra launch and displaces no tier.

### I6. "AUTHOR: validation control for instrument endpoint-6-readout vv1" ("Cost. Simulated time per molecule for the proxy…")

**ACCEPTED AS-IS.** It is a count of finished reruns times a fixed 1.125 ns, and GPU-hours come from the box clock. No held-out truth is needed. It is labelled as set in F1.

### I7. "AUTHOR: validation control for instrument endpoint-7-readout vv1" ("Family test. Among 12 within-family pairs…")

**QUEUED CONTROL.** Planted orderings:
- The known order must give 12 of 12, and the reversed order 0 of 12.
- A planted proxy equal to reference × 2 for the four hydrocarbons and reference × 0.5 for the four oxygenates must give 12 of 12. Its between-family log difference must be ln 4, a factor of 4.
- Enumerating all 576 pairs of within-family orders must give exactly 26 with 10 or more concordant and 68 with 9 or more. The gate confirmed both counts.

It follows the shared planted rules above.

### I8. "AUTHOR: validation control for instrument endpoint-8-readout vv1" ("Added value over free orderings…")

**QUEUED CONTROL.**
- Feed the margin code three identical rerun D sets. It must halt with WRONG_VARIANCE_SOURCE.
- Feed it three planted rerun D sets drawn from the I11(a) ensembles. It must give a positive margin, computed over exactly 6,561 picks (256 when given two reruns).

It follows the shared planted rules above. Judging follows the narrowing in D3(d).

### I9. "AUTHOR: validation control for instrument endpoint-9-readout vv1" ("Diffusive-regime label…")

**ACCEPTED AS-IS.** I11(b) and I11(c) are its validation: ordinary planted walks fall inside the band, and t^0.7 walks fall outside it. Under D3(a) this endpoint now only sets a label, so the planted walks' missing cage motion cannot flip a verdict. F2's extension readout shows what happens at longer lags.

### I10. "AUTHOR: validation control for instrument endpoint-10-readout vv1" ("Fit-window sensitivity…")

**QUEUED CONTROL.** Repeat I11(a) at the two other lag windows, 0.05–0.2 ns and 0.2–0.4 ns. The recovered-D bias must be within 2 standard errors in each. This stops a code error in an alternative window from producing a false "window-dependent" label. It follows the shared planted rules above.

### I11. "AUTHOR: validation control for instrument endpoint-11-readout vv1" ("Planted known truth, no GPU…")

**ACCEPTED AS-IS.** It is its own ground truth: the D values and orderings are chosen, so the right answer is known. Its guessed settings are accepted: 20 and 200 ensembles, the 95% criterion, exponent 0.7 and seed 7. The planted controls queued under I3, I5, I7, I8 and I10 run beside it and change none of (a) to (d).

### I12. "AUTHOR: validation control for instrument endpoint-12-readout vv1" ("Timestep control, lowest priority…")

**QUEUED CONTROL.** This is a time-axis check. The analysis must take each frame's time from its step number times that run's own timestep, never from the frame count. For the 1 fs run, the frame spacing worked out this way must be 1.000 ps, the same as in the 2 fs reruns. Otherwise D from the 1 fs run could be off by a factor of 2. If the check fails, endpoint 12 is reported as not judged. It runs in the session's analysis pass on tier-4 output. Tier 4 stays lowest priority and is the first tier cut. The check uses no extra GPU time, needs no extra launch and displaces no tier.

## Shared queue

**Empty.** There is nothing to answer.

---

## Summary of answers

| ID | Item opens with | Verdict |
|---|---|---|
| D1 | "The question allows two proxy forms." | REJECTED (labels: a fail rules out this form only) |
| D2 | "The question says to follow the paper's builder…" | ACCEPTED AS-IS |
| D3 | "The design adds rules the question does not contain." | REJECTED in part ((a), (b) and (d) narrowed; (c) stands) |
| D4 | "The question asks for stability across independent replicas…" | ACCEPTED AS-IS |
| D5 | "The question judges cost in CPU-hours…" | QUEUED CONTROL (throughput probe in wave 1; $19 approved) |
| G | "Claim design-core: grounding = reproduces." | ACCEPTED AS-IS |
| F1 | "[EXPLAINS] decidability by construction…" | REJECTED (cost and pre-check relabelled as non-evidence) |
| F2 | "[NEEDS_RUN] The fit window (0.1-0.4 ns)…" | QUEUED CONTROL (R2 readouts plus extension slope) |
| R1 | "Planted known-truth check (a)-(d)…" | ACCEPTED AS-IS |
| R2 | "Tier-1 runs with the diffusive-regime slope count…" | ACCEPTED AS-IS |
| Author queue | (empty) | Empty |
| I1 | "…endpoint-1-readout vv1" | ACCEPTED AS-IS |
| I2 | "…endpoint-2-readout vv1" | QUEUED CONTROL (density by hand from data file) |
| I3 | "…endpoint-3-readout vv1" | QUEUED CONTROL (planted proxy path) |
| I4 | "…endpoint-4-readout vv1" | ACCEPTED AS-IS |
| I5 | "…endpoint-5-readout vv1" | QUEUED CONTROL (planted 1.8 ns window; join check) |
| I6 | "…endpoint-6-readout vv1" | ACCEPTED AS-IS |
| I7 | "…endpoint-7-readout vv1" | QUEUED CONTROL (planted family orderings; 26/576 count) |
| I8 | "…endpoint-8-readout vv1" | QUEUED CONTROL (margin halt and pick count) |
| I9 | "…endpoint-9-readout vv1" | ACCEPTED AS-IS |
| I10 | "…endpoint-10-readout vv1" | QUEUED CONTROL (planted alternative windows) |
| I11 | "…endpoint-11-readout vv1" | ACCEPTED AS-IS |
| I12 | "…endpoint-12-readout vv1" | QUEUED CONTROL (time-axis check) |
| Shared queue | (empty) | Empty |

Totals: 24 items answered. That is 22 items of substance plus the 2 empty queues. 10 accepted as-is, 3 rejected (D1, D3, F1) and 9 queued controls (D5, F2, I2, I3, I5, I7, I8, I10, I12).

**Budget: approved, up to $19 total on one single-GPU box; the $20 cap is not raised. Design: approved for build with the changes above.**

---

## Addendum after build halt 1: execution directives for build

Date: 2026-10-18. Added after the first build try halted. Nothing above this heading is changed.

**New input of record.** `out/build_cp1_try1_wf_bcd297f8-bc7_return.json` (sha256 `2829f55fa6d85612805bd94e873d61ba9ea632a2fa35601abf49ccdba691bd75`).
- The builder stopped before writing any file. It spent $0.00 and launched no box.
- It named two blockers and some launcher items, and it asked three questions.
- The operator also confirmed some facts about the infrastructure. They are quoted where they are used below. The gate did not check them itself.

**How this addendum is used.** The operator passes this section, word for word, to the build as its execution directive (exec_note).

### (a) Which document binds

- The build binds to three texts. This addendum comes first. The item answers in GATE_COMMIT.md above come second. The design record (`out/design_record_attempt2.json`, sha256 `9f320ef3d15f224a9bebeb30d7ff4dfe6eeab79230ec9785f2a977de0af6e641`) comes third.
- Where two of them differ, the earlier one in that list wins. Where the first two are silent, the design record binds as written, GUESS numbers included.
- The builder must read GATE_COMMIT.md in full. The checklist below is there to make sure nothing is missed. If the checklist and an item answer above ever seem to differ, the item answer above binds.

**Checklist of gate changes the build must carry (16 entries).**

Labels and narrowed rules:
1. **D1.** A main rho below 0.8 is labelled "refuted for the Stokes-Einstein-like form kT/(6π·D·R) only; the excess-entropy-like form was not tested". The rho-below-0.6 abandon line gets the same label. A pass answers "yes" for this form.
2. **D3(a).** Endpoint 9 never refutes. If 3 or more of 8 molecules fall outside the slope band, it adds the label "apparent D: slope outside the planted band for N of 8 molecules". Claim 2 is judged only by endpoints 4 and 5.
3. **D3(b).** Endpoint 10 never refutes. A main-window pass with another window below 0.8 is reported as "passed in the pre-registered window (0.1–0.4 ns); window-dependent".
4. **D3(c).** Endpoint 7 is unchanged. It may refute claim 4 only. The discordant pairs are listed beside the count.
5. **D3(d).** Endpoint 8 judges claim 5 against molar mass, reference density and XGBoost only.
   - At or below the best of these: refuted.
   - Above the best but within the rerun margin: "higher than free orderings, within rerun noise".
   - Above the best by more than the margin: passed.
   - 1/D and simulated density are reported as ablations and cannot refute claim 5. If either matches or beats the proxy, the label is "size term adds nothing" or "diffusion adds nothing over density".
6. **F1.** Endpoint 6 is labelled "met by the plan's arithmetic: 3.375 ns per molecule, 4.2% of 80 ns; not an empirical test". If endpoint 4 fails, claim 3 is labelled "not shown". A pass of endpoint 1 is labelled "integrity check, not evidence". A failure of endpoint 1 stops the run before any spend.
7. **Early stop.** If tier 1 does not finish, numbers from finished cells may be reported, each labelled "incomplete run: descriptive only, no verdict". No pass or refutation is claimed.

Queued controls:

8. **D5.** The throughput probe in wave 1, against the time limit T defined in (d).
9. **F2.** The log-log slope of each molecule's mean-squared displacement in the 2 ns extension, at lags 0.1–0.9 ns. Report only.
10. **I2.** Density computed by hand from each data file must match LAMMPS's step-0 density to within 0.1%.
11. **I3.** Planted proxy path: made-up η of 1 to 8 mPa·s with seed 7. Each η must come back to within 1 part in 10⁶, with rho +1, and −1 when reversed.
12. **I5.** A planted 1.8 ns window split into two files at 1.0 ns, plus the real-data join check.
13. **I7.** Planted family orderings (12, 0, and 12 with ln 4 offset), and the enumeration giving 26 and 68 of 576.
14. **I8.** Identical reruns must halt with WRONG_VARIANCE_SOURCE. Planted reruns must give a positive margin over exactly 6,561 picks (256 with two reruns).
15. **I10.** Planted (a) bias check at the 0.05–0.2 ns and 0.2–0.4 ns windows.
16. **I12.** For the 1 fs run, frame times come from step number × timestep, and the frame spacing must be 1.000 ps.

### (b) Where boxes are built and checked

**On this workstation, before launch, as the design says.** The operator reports that `.toolchain/env` in this folder now holds RDKit 2025.09.5, Packmol, numpy 1.26.4 and the LAMMPS 29 Aug 2024 CPU build. So blocker 2 no longer holds. Boxes are not built on the rented box.

Pre-launch steps, in order, all local and all at $0.00:
1. Build 24 boxes with the committed builder (sha256 `91cac1d5307eb3a0ab54be1cfd2fac3d01919bdd1cd35e7c75929bd016977008`). That is 8 molecules × 3 packing seeds (61453, 61454, 61455), with the design's molecule counts and the packing density from (c).
2. Check that the net charge per molecule is near zero, from the builder's metadata.
3. Do a zero-step read of every box with the local LAMMPS build.
4. Run the I2 density check on every box.
5. Run R1 and the planted controls (I3, I5 part 1, I7, I8, I10) with the local numpy. The item answers above allow either the workstation or the box. The workstation is chosen, because a failure there costs nothing.
6. Record the sha256 of every built data file and the version of every tool used.

If any step fails, stop before launch and report. Do not launch with a partial set of boxes.

The on-box script starts from the 24 shipped data files and never runs the builder, Packmol or RDKit. Its stages, in order:
1. Check the price and budget variables (d).
2. Set up the engine (f, item 2).
3. Check each data file's sha256 against step 6 above.
4. Run tiers 1 to 4 under the clock rule and the D5 probe.
5. Run the analysis pass (the endpoints, F2, I5 part 2, I12).
6. Write results as in (e).

### (c) Packing density

**0.75 g/cm³ for all 24 boxes.** This is the builder's own default. Do not use the README example's 0.3 g/cm³.

Reason:
- 0.75 is closest to where the boxes end up. The paper's simulated densities run from 0.797 to 0.962 g/cm³.
- Starting from 0.75, a box shrinks by at most a factor of 1.28 in volume. Starting from 0.3, it would have to shrink by a factor of 2.66 to 3.21.
- The design reads D from 0.2 ns of the constant-pressure stage onward. That assumes the density has levelled off by then, and a start near the final density makes that most likely.
- The gate did not check which packing density the paper itself used.

If Packmol cannot pack any box at 0.75, stop before launch and report. Do not lower the density for some boxes only.

Report only, with no effect on any verdict: for each molecule, the mean density over 0.20–0.45 ns of the constant-pressure stage, beside the mean over its last 250 ps. This shows whether density had levelled off when the D window opened.

### (d) Price variable and time cap

**Variables** the operator forwards to the box:
- `PRICE_USD_PER_HOUR`: the listed on-demand hourly price, in US dollars, of the instance type actually launched (for example `1.29`).
- `BUDGET_LEFT_USD`: the part of the $19.0 approval not yet spent by earlier launches of this run. It is `19.0` on the first launch.

The on-box script reads both before anything else. If either is missing, not a number, or not above zero, it exits at once.

**Runner time limit**, in hours, counted from box boot (the machine's uptime clock), so boot, bootstrap installs and setup all count against it:

  T = min(18.0 / P, B / P − 0.75), where P = `PRICE_USD_PER_HOUR` and B = `BUDGET_LEFT_USD`.

- On a first launch at $1.33 per hour or less, this is exactly the design's rule, 18.0 / P.
- The second term is a gate change. The design's rule assumes that the 0.75 hours of boot, teardown and backstop cost $1.0 or less. That holds only up to $1.33 per hour. At the design's own guessed $1.5, the worst case would have been $19.13. With the second term, the worst case never goes above B.
- T is the limit used by both the design's clock rule and the D5 probe.

**Backstop.** `REMOTE_TIMEOUT` = floor((T + 0.5) × 3600) seconds. These are the design's 30 minutes of backstop. The operator computes it from the same P and B and sets it.

**Worst-case spend** is P × (T + 0.5 + 0.25 for boot and teardown). It is never more than B.

**Launch rule.** Launch the cheapest single-GPU type with capacity at launch time, as the design says. Do not launch if T would be under 6.29 hours. That figure is 1.0 h setup + 5.04 h for tier 1 + 0.25 h spare, at the guessed speed. On a first launch, it means do not launch above $2.69 per hour.

| Price per hour | T (hours) | REMOTE_TIMEOUT (s) | Worst case | Tiers that fit at the guessed speed |
|---|---|---|---|---|
| $1.29 (gpu_1x_a10) | 13.953 | 52032 | $18.97 | 1, 2, 3, 4 |
| $1.50 (design's guess) | 11.917 | 44700 | $19.00 | 1, 2, 3, 4 |
| $1.99 (gpu_1x_a100_sxm4) | 8.798 | 33471 | $19.00 | 1, 2 |

The guessed speed of 530 steps per second was scaled from an A100 benchmark, and an A10 may be slower. The D5 probe measures the real speed. It stops the run early if tier 1 cannot fit.

### (e) Results path

- On the box, every path is relative to the one working folder named in the launcher copy's working-folder line. The operator matches that folder to the one the frozen bootstrap enters, as in the worked example.
- The runner writes every result under `out/results_cp1/` in that folder, because the launcher fetches the box's `out/` folder. This replaces the build instruction's `results_cp1/out/`.
- The runner writes each cell's records as soon as that cell finishes, and flushes them to disk. So whatever is fetched after a probe stop, a clock stop or a backstop kill is complete up to that point.
- It also writes these as soon as each is known: the measured probe rate, the acceleration path that ran (GPU or CPU), the tool versions, and the box hashes.
- Locally, pre-launch records go to `out/results_cp1/prelaunch/`. The on-box script never writes into a folder named `prelaunch`, so a fetch cannot overwrite them.

### (f) Other items in the halt that need an owner answer

1. **The frozen bootstrap's language-model checks (torch, Gemma-2)** are accepted as they are. The operator reports they are installs and checks that pass on a Lambda image. Their time counts against setup and against T. They are not a reason to halt.
2. **The GPU engine on the box.**
   - Install LAMMPS 29 Aug 2024 from conda-forge, cuda126 build. That is the same release as the local build. Do not compile from source on the box.
   - Turn GPU acceleration on with LAMMPS command-line switches only. The deck text keeps only the design's listed edits.
   - The operator reports this GPU path is not verified. So the run logs which path actually ran: GPU, or the design's CPU fallback.
   - If no GPU path works, run on the CPU as the design says. The D5 probe then decides whether tier 1 can fit.
3. **"The on-box script runs every stage in order."** This is settled by (b). Building boxes, the zero-step read, I2, R1 and the planted controls are local stages before launch. The on-box script runs only the stages listed in (b).
4. **The default `REMOTE_TIMEOUT` of 5400 seconds and the missing price setting** are settled by (d).
5. **The two frozen files name different working folders.** This is infrastructure, settled by the operator under (e). The gate sets only that the on-box script uses paths relative to that single folder.
6. **What this addendum changes in the design record.** It makes four changes:
   - the second term of T and the launch rule above $2.69 per hour, which can only shorten or prevent spend;
   - the packing density, which the design left open;
   - local execution of R1 and the planted controls, which the item answers already allowed;
   - one report-only density readout.

   No verdict rule changes. No answer above changes. The $20 cap and the $19 approval stand.
