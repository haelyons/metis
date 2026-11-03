# Predictions before corrected evaluator calibration

Next test: NEXT.json and CALIBRATION_BRIEF.md. No test launched by s03. Operator commits these files before launch to seal predictions. IDs local to s03; prior s02 IDs resolved separately in outcomes.json. Probabilities are forecasts, not acceptance criteria. Original CPU-only endpoint and decision rules unchanged.

Protocol: four fixed apo cases, CPU standard 3600 rotations, 50 retained poses each, four fixed serial evaluator blocks, fresh subprocess for each case/block. Retain all16 full-child walls including first block. T=max16 walls, seconds; not docking, calculation-only or allocation wall. Historical evidence supplied without loosening source/prepared identity checks. No fresh GPU/dense comparison.

| ID | p | One checkable statement | Resolution |
| --- | ---: | --- | --- |
| Q1 | 0.70 | Requested CPU-only setup and operational anchors complete successfully. | True iff reproduce setup and anchors succeed with all four requested cases/settings/checks. False for observed setup/anchors failure or protocol substitution. Null if neither attempted or records missing; empty scalar anchors alone do not satisfy. |
| Q2 | 0.60 | Maximum of all16 complete evaluator subprocess walls lies in [5,30] seconds inclusive. | True iff all16 valid walls exist and maximum in range. False for valid completed maximum outside range or valid censored evaluator lower bound >30. Null for other incomplete/invalid evidence. |
| Q3 | 0.80 | CPU-standard 60-second evaluator screen passes. | True iff all16 valid full walls <=60 s, pins/output/native-self checks valid. False for any valid complete wall >60 or confirmed evaluator-only lower bound >60. Null otherwise. |
| Q4 | 0.80 | Every case passes native-self DockQ identity smoke within 1e-6 of1. | True iff four valid fixed-mapping scores meet bound. False for any observed valid score outside bound. Null if missing/uninterpretable. DESIGN identity check only. |
| Q5 | 0.85 | Actual allocation charge through termination is at most USD10. | True/false only from actual billed total including applicable tax/rounding through termination. Null if only wall/rate estimate or no final charge/termination evidence. |
| Q6 | 0.80 | C2 survives this runtime screen provisionally. | True iff Q3 true; false iff Q3 false; null iff Q3 null. Does not resolve full card input or other scientific blockers. |
| Q7 | 0.85 | Corrected brief passes intake with data=available. | True iff completed next intake PASS and data=available in retained reply/stage evidence. False for completed intake FAIL or completed non-available data judgement. Null if no completed valid intake evidence. No forecast that licence changes from unknown. |

Q2/Q3/Q6 correlated. All claims scored under these definitions after next result. A repeat intake failure is scored and diagnosed; no reinterpretation as measured runtime failure. Q7 tests whether supplied evidence closes diagnosed handoff failure, not scientific agreement or future source-hash identity. No automatic further run authorized by forecasts.
