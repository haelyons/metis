# HALT — coolant_proxy run, attempt 2, step 2 (design)

Time: 2026-10-18T11:54:35Z. Lambda spend: $0.00. Instances running at halt: 0 (checked via GET /instances).

## What halted

The design step could not be launched. The operating instructions say pipeline.js runs only through the
Workflow tool. That tool is not present in this session: a direct lookup for it returned no match. Attempt 1
had it (its design ran as wf_b06f2a6a-35f).

Running the pipeline any other way (hand-driving its prompts with agents, or a local JavaScript runner) would
break the "only through the Workflow tool" rule. The pipeline's own law also says infrastructure that is not
runnable as given is a halt, never a patch. So the step was not retried and not emulated.

This is not a budget halt. The calibration step (2b) is conditional on a design budget halt, so no Lambda
instance was launched.

## What was done before the halt

- Published throughput proxies gathered for the design's hardware note (out/substrate_note_attempt2.txt):
  Amber pmemd.cuda, JAC benchmark, 23,558 atoms, particle-mesh Ewald, 2 fs step, NPT:
  A100 610.09 ns/day, H100 741.10 ns/day; with a 4 fs step, A100 1194.50 ns/day.
  Source: https://ambermd.org/GPUPerformance.php.
- OpenMM's published benchmark page (https://openmm.org/benchmarks) returned HTTP 404, as did four alternate
  locations tried. No OpenMM figure is cited.
- These proxies are about 24 times attempt 1's guessed 25 ns/day. Taken at face value they would cut
  attempt 1's $200 estimate well under the $20 cap. That is untested: no design has been run on them.

## What would unblock it (for the human owner)

Rerun attempt 2's step 2 in a session where the Workflow tool is available, passing
out/substrate_note_attempt2.txt as substrate_note. Steps 3 to 7 were not run.
