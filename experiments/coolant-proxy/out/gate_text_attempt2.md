# Gate text — attempt 2 (design run wf_1e76375d-cc7)

Verbatim gate instruction from the design return:

BUDGET_AND_DESIGN_APPROVAL: human commits a gate file answering, of record, every diff question, every non-reproducing grounding note, and every queued item (instrument validations included; "accepted as-is" is an answer) before mode=build.

Items of record needing an answer (copied verbatim from out/design_record_attempt2.json):

## Diff departure questions

D1. What: The question allows two proxy forms. One is Stokes-Einstein-like: viscosity varies inversely with diffusion coefficient times molecular radius. The other is excess-entropy-like. The design tests only the first. It uses temperature times the Boltzmann constant, divided by 6π times diffusion coefficient times radius. The radius comes from the volume one molecule fills at the simulated density. The design applies no correction for the finite simulation box, which it estimates at 25 to 30 percent of the diffusion coefficient. It admits an entropy-based form might still pass.
    Question: If this one size-based form scores below a Spearman rank correlation (rho, the ordinary correlation of the two rank orders) of 0.8, does that answer your question with 'no'? Or does it only rule out this one form, leaving the entropy-based form open?

D2. What: The question says to follow the paper's builder and equilibration protocol, with about 1 ns at constant pressure. The design sets the timestep to 2 femtoseconds (fs), where the committed input deck uses 1 fs. It measures diffusion at constant pressure, though the design says the paper's production runs are at constant volume. It reads diffusion only from the 0.2 to 1.0 ns window, fitting lags of 0.1 to 0.4 ns. The one-molecule timestep check is lowest priority and may not run. The design also says a failed density check leaves the main claim neither passed nor refuted. The question states no such consequence.
    Question: Do you accept a 2 fs step and constant-pressure diffusion in place of the paper's settings? And should a failed density check be allowed to stop the main claim from being judged at all?

D3. What: The design adds rules the question does not contain. Three or more of eight molecules with non-diffusive motion refutes the 1 ns claim 'whatever rho shows'; the limit of 2 is a guess. The result is called robust only if rho is at least 0.8 in all three fit windows. Within-group order needs at least 10 of 12 pairs right, a bar the question never sets. The proxy must beat every free ordering by more than the spread between reruns. The free orderings now include two built from the same simulations: inverse diffusion and simulated density.
    Question: Which of these added rules do you want to be able to refute, or downgrade, a result that the question's own rules would have passed?

D4. What: The question asks for stability across independent replicas and agreement with a longer trajectory. The design runs three reruns per molecule in one GPU session at one box size, and says these are same-box reruns, not replication. The longer trajectory is rerun 1 extended to 2 ns, only twice as long. It is compared with the mean of reruns 2 and 3. Both tests use a bar of rho at least 0.8, which the question gives only for agreement with reference. The third rerun is scheduled after the extensions. It may be dropped, leaving a single pair to judge.
    Question: Do three same-session reruns and a 2 ns extension count as 'independent replicas' and a 'longer trajectory'? Is 0.8 the right bar for agreement between them?

D5. What: The question judges cost in CPU-hours (processor time). The paper's baseline is 10 replicas of 8 ns, about 1.5 × 10⁴ CPU-hours per molecule per temperature. The design instead compares simulated time per molecule. Its bar is 8 ns, one tenth of the paper's 80 ns; that reading of 'well below' is a guess. The design also sets a $19 cap, an assumed GPU price of $1.5 per hour, and a 12-hour limit. If throughput is three times slower than guessed, the first batch (reruns 1 and 2 of all eight molecules) cannot finish and no answer is given.
    Question: Is simulated time an acceptable stand-in for the paper's CPU-hours, and is one tenth the right meaning of 'well below'? Are you willing to spend up to $19 on this run?

## Triage grounding

Claim design-core: grounding = reproduces. Observed: Pre-check: the experimental_40C_mPa_s column equals the reference values for all 8 ids (rho 1.0), and the order matches the stated one. Free-ordering rho: XGBoost 0.738 (claim 0.738), reference density 0.048 (0.048), molar mass 0.524 (0.524). Note: Only the design-time data numbers can be checked, and all of them reproduce. No simulation outputs exist yet, so the simulation endpoints have not been run. The molar masses were computed from formulas by hand.

Findings:
- [EXPLAINS] decidability by construction: any endpoint forced, unable to occur, or deciding a different question: The cost endpoint is forced by the plan (3.375 ns planned against an 8 ns limit, so it can only fail with 8 or more reruns). The data-only pre-check is tautological (rho = 1.0 because the column equals the reference). The main rho endpoint is open, with a named refutation (rho < 0.8, chance 439/40,320). Reaching it depends on tier 1 finishing, which is unrun.
- [NEEDS_RUN] The fit window (0.1-0.4 ns), timestep, box size and the cube-root radius term could make D or the proxy degenerate or sub-diffusive for every cell (especially long molecules such as squalane), whatever the chemistry.: No real D or slope has been measured. The design guards against this scale confound (planted-truth reachability of all four labels, a slope band, a three-window sensitivity endpoint, and a diffusive-regime count), but those guards have not been executed, and the planted walks lack cage motion. A committed number does not exist yet to rule the confound out.

## Run queue

R1. Planted known-truth check (a)-(d), no GPU, seed 7: confirm all four decision labels are reachable before reading any real result
R2. Tier-1 runs with the diffusive-regime slope count and the three-window rho sensitivity (reads true slopes of squalane and other long molecules in the 0.1-0.4 ns window)

## Author queue

(empty)

## Instrument queue

I1. AUTHOR: validation control for instrument endpoint-1-readout vv1: held-out ground truth for "Data-only pre-check, no simulation. Spearman rho between the reference 40 °C viscosities of the eight molecules and the experimental_40C_mPa_s column of predictions_viscosity.csv. Also the resulting order. Free orderings are recomputed here."
I2. AUTHOR: validation control for instrument endpoint-2-readout vv1: held-out ground truth for "Density gate, the first number to reproduce. Mean simulated density over the last 250 ps of the constant-pressure stage (the deck's own averaging window), averaged over reruns. Compared with the paper's simulated density for each molecule."
I3. AUTHOR: validation control for instrument endpoint-3-readout vv1: held-out ground truth for "MAIN. Spearman rho between the main proxy and the reference 40 °C viscosities of the eight molecules. D is averaged over finished reruns, and ties get average ranks. Reported beside it: the exact chance probability of reaching the value."
I4. AUTHOR: validation control for instrument endpoint-4-readout vv1: held-out ground truth for "Stability across reruns. Spearman rho between the proxy orderings of each pair of the three reruns (three pairs). Also each rerun's own rho against reference, with its minimum and maximum."
I5. AUTHOR: validation control for instrument endpoint-5-readout vv1: held-out ground truth for "Agreement with a longer run. Spearman rho between two proxy orderings. One uses rerun 1 continued to 2 ns, with D from the 0.2 to 2.0 ns window. The other uses the mean of reruns 2 and 3. The two share no data."
I6. AUTHOR: validation control for instrument endpoint-6-readout vv1: held-out ground truth for "Cost. Simulated time per molecule for the proxy: finished reruns times 1.125 ns each (25 ps relaxation, 100 ps settling, 1.0 ns constant pressure). The longer runs and the timestep control are validation and are excluded but reported. Measured GPU-hours per molecule are also reported. The paper's baseline is 10 reruns of 8 ns, 80 ns per molecule. GPU-hours and the paper's CPU-hours are not comparable, so simulated time is judged."
I7. AUTHOR: validation control for instrument endpoint-7-readout vv1: held-out ground truth for "Family test. Among 12 within-family pairs (6 among the four hydrocarbons, 6 among the four oxygenates), the number where proxy order equals reference order. Reported beside it: the difference between the group means of log(proxy/reference), as a between-family offset factor."
I8. AUTHOR: validation control for instrument endpoint-8-readout vv1: held-out ground truth for "Added value over free orderings. Main-proxy rho minus the highest rho among the controls: molar mass 0.524, reference density 0.048, XGBoost 0.738, simulated density, and 1/D. Margin rule: the standard deviation of rho against reference over every way of picking one rerun's D per molecule (3^8 = 6,561 ways, or 2^8 = 256 with two reruns). Variance source: reruns of the same cell."
I9. AUTHOR: validation control for instrument endpoint-9-readout vv1: held-out ground truth for "Diffusive-regime label. Number of the eight molecules whose mean mean-squared displacement has a log-log slope outside the band from the planted check, within the main fit window. The main rho is also reported with those molecules flagged."
I10. AUTHOR: validation control for instrument endpoint-10-readout vv1: held-out ground truth for "Fit-window sensitivity. Main rho recomputed with lag windows 0.1-0.4 ns (main), 0.05-0.2 ns, and 0.2-0.4 ns (GUESS: two alternatives of procedure). The longer run uses 0.1 ns to half its window."
I11. AUTHOR: validation control for instrument endpoint-11-readout vv1: held-out ground truth for "Planted known truth, no GPU. (a) 20 synthetic random-walk ensembles with chosen D, using the real molecule counts, 1 ps spacing and 0.8 ns window: recovered-D bias. (b) Slope band: narrowest symmetric band around 1 holding the fitted log-log slope of at least 95% of 200 ordinary ensembles (GUESS counts). (c) 200 ensembles with mean-squared displacement growing as t^0.7 (GUESS) labelled non-diffusive. (d) Known-order input gives rho +1, reversed gives -1, one density 5% off fails the density gate."
I12. AUTHOR: validation control for instrument endpoint-12-readout vv1: held-out ground truth for "Timestep control, lowest priority. D of nonylcyclohexane from one 1 fs run, against the mean of its three 2 fs reruns. Spread rule: standard deviation of D over those reruns. Variance source: reruns of the same cell."

## Shared queue

(empty)
