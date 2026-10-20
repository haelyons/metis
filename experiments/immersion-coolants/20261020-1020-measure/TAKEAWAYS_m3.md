# Takeaways: does a coolant-simulation plan's speed estimate hold up?

[1] Every measured number in this file comes from one setup. It is one box of 250 nonylcyclohexane molecules (11,250 atoms). It ran on one rented 40 GB Nvidia GPU. The engine was Lammps 29 Aug 2024, built from source, with its GPU package.

## What was the research question, and the hypothesis?

A planning document, called the card here, proposes a computer-simulation study of liquid coolants. It prices the whole study using one speed figure.

That figure is 250 nanoseconds of simulated time per day of computing, per GPU. The card did not measure it. It took the number from a public Amber benchmark and divided by a safety factor of about 2.4 [1].

The card also sets a gate. If speed is at least 150 ns/day, the plan stands. Otherwise the card says to drop the extension tier and re-plan with 48 molecules at 3 replicas.

The research question was this. Does the 250 ns/day figure hold when the card's own protocol is run on one rented GPU? And does the 150 ns/day gate pass?

The stated hypothesis was as follows. Measured speed would replace the card's 250. It would then be read against the gate and used to re-price the card's $941 plan. First, the liquid density had to be within 4% of the reference [1].

The implied expectation was that the card was roughly right. The design never wrote a separate forecast number, so the card's own 250 ns/day is the prediction under test.

## What did the experiment try to find?

It tried to find five things on one trajectory of one liquid.

- The production speed of the card's own protocol, with the card's stress and heat-flux sampling every 5 steps.
- Whether the gate at 150 ns/day passes.
- What the $941 plan costs at the measured speed.
- Whether the simulated liquid has the reference density of 0.805 g/cm3 at 40 C, within 4% [1].
- What per-step sampling costs, using three variants of the same run, plus whether the heat-flux calculation runs with the GPU at all.

It also measured the step where an earlier pilot had halted: packing molecules into the box.

The three variants were the deck as written, pressure tensor only, and no sampling. All three started from the same equilibrated state.

## What was predicted, and what happened?

Each line gives the threshold, then the number measured on the box. [1]

- Density anchor, passed. The threshold was within 4% of 0.805 g/cm3 [1]. The constant-pressure run gave 0.795028 g/cm3 on the box, which is 1.24% low [1]. [1]
- Speed claim, refuted. The threshold was 100 to 625 ns/day. The deck as written ran at 12.600 ns/day on the box, below the range [1]. [1]
- That is 19.84 times below the card's 250 ns/day, measured on the box. [1]
- Gate, failed. The threshold was at least 150 ns/day. The measured 12.600 ns/day is 11.9 times below it [1]. [1]
- Re-priced plan, over the cap. The card's cap is $1,000. The measured speed re-prices the plan to $18,670.63, which is 19.8413 times the card's figure [1]. [1]
- Pressure-tensor-only variant, reported. It ran at 18.185 ns/day on the box, 1.4433 times the deck as written [1]. [1]
- No-sampling variant, reported. It ran at 18.426 ns/day on the box, 1.4624 times the deck as written [1]. [1]
- Per-atom step rate of the deck as written was 820.342 thousand atom-steps per second at a 2 fs timestep. [1]
- Does the heat-flux compute run with the GPU pair style? The record reads yes. The timed run finished with no refusal. [1]
- Sanity control, passed. The mean temperature stayed within 313.15 plus or minus 5 K in all three production runs [1]. The means were 313.56, 313.59 and 311.71 K [1]. [1]
- Build reading, descriptive. Compiling the engine on the box took 136.741 seconds [1]. The card budgets 4 hours for build plus a dry run. [1]

## Is this what we expected?

No. The card's speed claim is refuted, and the failure is large. The simulated liquid itself looks right, so the cause is not a wrong liquid.

The speed is too low by a factor near 20 on this box. That is far beyond the factor of 2.5 the claim allowed [1]. The card's own else-branch now applies.

Two things stand out. Removing all sampling still gave only 18.426 ns/day on the box, 13.6 times below 250 [1]. Removing only the heat-flux part gave 18.185 ns/day on the box [1].

So the gate fails with or without the card's sampling. The heat flux alone costs about 31% of the speed on the box [1]. [1]

Status of each reading. The speed claim, the gate and the cost cap are refuted outcomes. The density anchor passed. The sampling-cost comparison is exploratory, because each variant is one run. The build-time reading is descriptive.

## What in these files does not fit

The open questions come first. Each is stated plainly, with where it shows up and what it would change.

### 1. Is the headline speed a measure of the GPU at all?

In the timed deck-as-written run on the box, bonded forces and bond constraints took 433 of 685.69 seconds, or 63% [1]. The GPU-run pair forces took 34 seconds, or 5% [1]. [1]

The same pattern holds in the other runs. Bonds took 77% in the pressure-only run [1]. The record shows the thread-count setting empty, though the build used 30 parallel jobs.

If true, the card's per-GPU proxy was tested against a number set by one CPU core. A faster GPU would barely move it. The gate failure and the 19.8-fold under-pricing would describe this machine's CPU, not the card's GPU plan [1].

### 2. Why was the Amber benchmark never run on this same box?

The card's 250 comes from a 23,558-atom Amber benchmark at 611 ns/day, divided by about 2.4 [1]. Nothing here puts that benchmark and this protocol in the same units.

In atom-steps per second the Amber figure would be about 41.6 million at a 4 fs step [1]. It would be about 83 million at 2 fs. That is my arithmetic, because the step is not in the files.

The measured run gave 0.82 million on the box [1]. [1] The gap would be 50 to 100 times. It would come from the engine, force field, constraints or build, not from the safety factor.

### 3. Is the card's named suspect, stress-tensor accumulation, the wrong one?

Pressure-tensor sampling every 5 steps cost about 1.3% on the box, comparing 18.185 with 18.426 ns/day [1]. Heat-flux sampling cost about 31% [1]. [1]

In the deck-as-written run, long-range electrostatics took 118.61 seconds, against 30.44 seconds in the pressure-only run. Bond time was 433 seconds against 365 seconds. [1]

Ten thousand warm-up steps, before any sampling exists, ran at 18.346 ns/day on the box. So the thermal-conductivity arm carries the real sampling cost. The card prices its two measurement arms as one. [1]

### 4. Why does the re-priced plan scale the whole $941?

The design says only GPU-hour lines scale, and the storage line is held. The reported cost is exactly 941 times 250 divided by 12.6, which is 18,670.63 [1]. [1]

Either the storage line is zero, or it was scaled by mistake, or the line items were never read. The true cost would be a little lower. It would still sit far above the $1,000 cap. The 19.84-fold figure may be slightly overstated [1]. [1]

### 5. Does "the deck runs on the GPU" license the word runs?

It does not, fully. The committed equilibration deck was refused by the GPU package. It stopped after 17.643 seconds with "Cannot currently use pppm/gpu with fix balance" [1]. [1]

The load-balancing line was removed and the second attempt ran for 2798.294 seconds. The compatibility reading looked only at the production run and reports runs with no mention of the edit. So the card's protocol was not run unmodified.

### 6. Is a one-sided density shortfall, from a short noisy run, "the card's liquid"?

The measured density was 0.795028 against 0.805, which is 1.24% low [1]. [1] The design planned 0.5 ns at constant pressure, averaged over 250 ps. The run used 300 ps, averaged over 100 ps.

Over the last 100 ps, the density rows swing between 0.7843 and 0.8021 [1]. The mean rests on 11 rows. The same value fixed the box volume of 109865.89 in all three production runs [1]. [1]

One more thing in the files. The drift check found the density still rising, by 0.00468 g/cm3 over the window, about 0.59% of the mean [1]. It stayed under the 1% limit for calling it drifting [1]. [1]

So the true plateau is probably nearer 0.805. A 1% density shift would change speed little [1]. But the claim that the timed system is the reference liquid rests on a short estimate, not a plateau.

### 7. How precise are the figures, when each rests on one run?

Ratios are given to four decimals, but each variant is one 100 ps run from one restart. The design planned 200 ps and a 25,000-step warm-up. The runs used 100 ps and 10,000 steps.

The warm-up rates of the three runs were 18.346, 18.400 and 18.442 ns/day on the box, a spread of 0.5% [1]. [1]

The 1.3% gap between pressure-only and no-sampling is only about twice that noise. The no-sampling run sat 1.9 K cooler, though inside the limit [1]. The mean pressures were -155.5, +190.8 and +114.2 bar [1]. [1]

The 12.6 headline is robust to this noise. The sampling-cost comparison is not. The four-decimal ratios imply a precision the three runs do not support.

### 8. Which engine was measured, and which setup record is missing?

The design declared a packaged conda-forge build. The run used a source build with the basic built-in Fourier transform library, no threading, and mixed precision. The design itself warned a hand-built engine could differ by 2 times.

The first-stage check reads a pass on parts present. The builder's exit code and the zero-step read check are absent, so only three of five parts were seen.

Install took 136.741 seconds on the box [1]. The card budgets 4 hours, so that comparison is never really made. [1]

### Found while writing

- The design record's density endpoint says the last 250 ps. The endpoint file for density says the last 100 ps. The run followed the second. [1]
- The speed claim as planned read a 200 ps segment after a 50 ps warm-up. The timed segment was 100 ps after 20 ps. [1]
- The guard's time estimate for equilibration was 664.8 seconds. The stage took 2798.294 seconds, about 4.2 times longer [1]. [1]
- The record's own packing check was partial. The builder's log is empty, so the exit code was never recorded. The earlier pilot's packing failure was therefore not truly re-measured. [1]
- Only one molecule was tested. Larger molecules in the card give boxes up to about 23,000 atoms. Their speed is unmeasured.

## Raw samples, verbatim

The rows below were drawn at random with a fixed seed from files on disk. Each is shown exactly as stored.

Three rows from the built input box, each giving one atom's number, molecule, type, charge and position:

```
    5306    118     4  0.074000000000   29.367675000   53.796759000   44.282409000
    2472     55     4  0.074000000000   29.442914000   23.512281000   20.274623000
    6469    144     4  0.074000000000   52.719866000   29.905592000   37.581863000
```

Two output rows from the pressure-only production run's printed thermodynamic table, giving step, temperature, pressure, density, volume and energy:

```
     50000   314.81228      628.5208       0.79502765     109865.89      14667.181    
```

One output record from the same run, as the harness stored it, then one from the equilibration's first step:

```
{"attempt": 1, "block": 0, "density": "0.79502765", "etotal": "14440.629", "kind": "thermo", "line_no": 171, "log": "prod_b.deck.log", "press": "-907.3104", "raw": "     55000   313.42362     -907.3104       0.79502765     109865.89      14440.629    ", "run_labels": [], "run_valid": true, "step": "55000", "temp": "313.42362", "variant": "prod_b", "vol": "109865.89", "written_utc": "2026-10-20T13:46:31+00:00"}
{"attempt": 2, "block": 0, "density": "0.29999997", "etotal": "2571.3986", "kind": "thermo", "line_no": 185, "log": "equilibrate.deck.log", "press": "-9005.487", "raw": "         0   0             -9005.487       0.29999997     291154.77      66.2788        66.2788        66.2788        2571.3986      2571.3986    ", "run_labels": [], "run_valid": true, "step": "0", "temp": "0", "variant": "equilibrate", "vol": "291154.77", "written_utc": "2026-10-20T13:24:00+00:00"}
```

The density file the equilibration wrote, which is the single number behind the density check:

```
# Time-averaged data for fix npt_density
# TimeStep v_rho
150000 0.795028
```

## Gate outputs

Run on a copy truncated at the Raw samples heading.

```
/tmp/claude-1000/-home-hal-dev-interp/72fa6ea2-188d-4e00-b467-74ae55869166/scratchpad/trunc.md: 1.1 codes/1000 words (2 codes, 1868 words); threshold 10.0
0 unscoped result sentence(s)
```
