# positive-openmm run9: outcome against sealed predictions (predictions/run9.md, 8ce0c43)

Run committed dd4a7a5. Box gpu_1x_a10, USD 1.29/h; run_box_usd 2.33; 1.52M tokens in; wall 6,507 s; pipeline exit 0; box torn down; push verified by the chain.

## Verdict
Evaluate VOID, after the first clean implement. The baseline evaluation adapter, written during reproduce before the seal existed, produced records that do not carry the sealed metric names and do not mean what the method adapter's records mean. No equivalence or performance verdict exists. The method looks sound on the evidence recorded so far.

- Intake to propose passed on the A10 for the second run running. Sequential ensemble 62.5 s; MPS verified, factor 1.32. Seal margins SD/sqrt(8) cited from reproduce's `ensemble.json` (192.3 kJ/mol final, 43.6 mean); 16 repetitions, budgets [80, 100, 120], minimum gain 1.05. Propose approved `ensembles` 5 of 5, expected 1.175.
- U30 held: the test author's checks read only `BASELINE_OUT` and `METHOD_OUT` and say so; all 8 cases passed on the first attempt. No repair; launch review passed.
- The method runs replicas in two waves of four MPS worker processes, with no SM cap. Its per-seed energies match the baseline's within 0.02 kJ/mol (readout noise; baseline reruns agree within 0.03). Representative wall 49.5 s against 62.5 s (1.26).
- Evaluate: validity passed (method anchors). The equivalence scorer exited 2 after 601 s with `missing_or_invalid_measurements`. Both arms ran and wrote 8 records for input `dhfr-23558-pme-fixed-eight-replicas` at seeds 1000 to 1007, but:
  - the baseline adapter treated each seed as an ensemble's `seed0` and ran 8 full ensembles (513 s), one record per ensemble, with only `replica_<i>_*` fields and no top-level `final_potential_kj_mol` or `mean_potential_kj_mol`;
  - the method adapter ran one ensemble at `seed0=1000` and wrote one record per replica seed, keyed by the sealed metric names.
  The seal's seeds are the eight replica seeds of one ensemble (`generated_inputs`), so the method adapter matched the seal and the baseline adapter could not have known it.
- Root cause: the contract never said that a record's `metrics` carry the sealed `equivalence_metrics` names, or that both adapters' records must mean the same execution. The baseline adapter is written before the seal and nothing runs it before evaluate, so a mismatch surfaces only as a VOID evaluation. This is the run7 later-unit candidate (smoke the baseline adapter before evaluate) with a second, semantic, half.

## Scores
| Prediction | Outcome | Hit |
|---|---|---|
| H100 SXM5 0.35, H100 PCIe 0.3, A100 SXM4 0.15, A100 PCIe 0.05, A10 0.15 | A10 | no (0.15) |
| intake PASS 0.93 | PASS | yes |
| reproduce PASS 0.9; 58 to 68 s on A10 | PASS; 62.5 s | yes; yes |
| profile PASS 0.93; MPS verified 0.93; A10 headroom 1.3 [1.15, 1.45] | PASS; verified; 1.32 | yes; yes; yes |
| seal PASS 0.85; margins cite reproduce 0.9; one SD rather than SD/sqrt(n) 0.45; seal implies more than 2,400 s per script 0.45 | PASS; cited; SD/sqrt(8); equivalence scorer 601 s, full evaluate not reached | yes; yes; yes (against 0.45); n/a |
| propose approved 0.85; data-parallel 0.5, ensembles 0.45 | approved 5/5; ensembles | yes; yes (0.45) |
| implement reached 0.65 | reached | yes |
| test author reads only representative outputs 0.85 | yes | yes |
| implement PASS 0.65; repair used 0.4; method caps MPS SMs 0.35 | PASS; no repair; no cap | yes; yes; yes |
| evaluate reached 0.4 | reached | yes |
| every adapter run writes valid measurements 0.75 | no (baseline records lack sealed metric names) | no |
| an evaluation script hits its 2,400 s budget 0.4 | no | yes |
| validity_pass 0.85 | true | yes |
| equivalence_pass, performance_pass, speedup, evaluate PASS 0.3 | not measured (VOID) | n/a |
| takeaways PASS 0.95 | PASS | yes |
| run_box_usd 5 to 25 if it reaches evaluate | 2.33 | no (A10 price, VOID after 1,059 s) |
| pipeline exit 0, box torn down, push verified 0.9 | yes | yes |

## What changed my mind
- With the evaluate interface now the only failing part across runs 7 and 9, the pattern is clear: anything authored before the seal and first executed in evaluate fails in evaluate. A fixed shape statement (U29) was not enough, because the adapter also needs the seal's metric names and seed meaning, which do not exist when it is written.
- The A10 fell out of the list twice running; H100 capacity was not available at launch either time.

## Fix
U31 (one gate: baseline adapter smoke with one repair). After the implement snapshot and before any test or method author call, implement runs the baseline adapter once as evaluate would (equivalence mode, sealed inputs, first sealed seed). It passes only when the records follow the evaluation record rules and each record's `metrics` carries every sealed `equivalence_metrics` name as a finite number. On failure, one `adapter-repair` call (harness role) with the seal may rewrite only `run_evaluation.sh`; a second failure stops implement as VOID before authoring. The contract also states that each record's `metrics` is keyed by the sealed metric names and that the method adapter's records mean the same execution and metric definitions as the baseline adapter's; the method author sees the repaired harness. Regression: run9's recorded `run_evaluation.sh` with run9's seal fails the smoke on `metrics`; run9's method records satisfy the record rule. Then run10 from the same brief.

## Later unit candidates (carried)
- Identity smoke: frozen tests against the baseline as method, before the method author.
- Seal cost against the evaluate budget at measured ensemble cost.
- Implement signature `exit_kind: infra` with `error_class: numeric` for a test failure.
- `test_m5_reproduce.js` intermittent failure.
