# Predictions sealed before CPU-standard evaluator calibration

Next test: NEXT.json and CALIBRATION_BRIEF.md. No new test launched or observed in s02. Operator commits these files before launch. Probabilities are forecasts, not acceptance criteria. IDs are local to this step; s01 outcomes are recorded separately.

Protocol: four fixed cases, CPU standard3600,50 poses per case, four fixed serial evaluator blocks with a fresh Python process per case;16 retained walls including initial launches. T is maximum complete evaluator wall, not docking time, warm calculate-only time or allocation receipt wall. Full definitions and cost cap are frozen in calibration brief. Scientific root remains unchanged.

## Q1 — p=0.85

Setup and requested CPU-only operational anchors complete successfully.

Resolution: True iff reproduce setup and anchors finish successfully with requested four-case CPU-standard configuration and checks; false for observed setup/anchors failure or protocol substitution; null if no attempt or missing records. Empty scalar anchor counts alone do not satisfy this statement.

## Q2 — p=0.65

Maximum of all16 complete evaluator subprocess walls lies in [5,30] seconds inclusive.

Resolution: True iff all16 valid retained measurements exist and their maximum is in range; false for a completed valid maximum outside range, or a valid censored lower bound>30; null for other incomplete/invalid evidence. Use full parent wall, not calculate-only time.

## Q3 — p=0.85

CPU-standard60-second evaluator screen passes.

Resolution: True iff all16 valid complete walls<=60 seconds with required pins, operational checks and self-smokes valid. False if any valid complete evaluator wall>60 or confirmed evaluator-only lower bound>60. Null for incomplete/invalid measurement without such falsifying witness.

## Q4 — p=0.80

Every case passes native-self DockQ smoke within1e-6 of1.

Resolution: True iff all four valid fixed-mapping identity scores meet bound; false for an observed valid score outside bound; null if missing or uninterpretable. This is a mathematical identity smoke, not scientific agreement.

## Q5 — p=0.80

Allocation charge through termination is at mostUSD10.

Resolution: True/false using actual billed allocation charge including applicable tax and billing rounding, through termination. Null if only receipt-stage estimates or no termination/final charge; record estimates separately.

## Q6 — p=0.80

C2 survives this runtime screen provisionally.

Resolution: True iff Q3 true: retain C2 for later GPU coverage and independent tolerance repair. False iff Q3 false: drop unchanged60-second allowance and cap schedule. Null iff Q3 null. Other existing blockers stay; this is not a full card PASS or resolved-input prediction.

Q2/Q3/Q6 correlated. Q3/Q6 only resolve CPU-standard necessary condition; successful screen leaves full card eval_runtime_s unresolved. A failed allowance stays failed even if a future plan adopts a larger budget. Physical branch remains conditional in either outcome; no forecast of dense quality or numerical agreement is made.
