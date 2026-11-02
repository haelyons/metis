Can MEGADOCK’s GPU implementation make denser docking search affordable, and does that improve pose recovery within a fixed budget?

Use the four unbound PINDER cases examined by blind01’s unit probe. Pin their exact identities, prepared inputs and reference structures before execution. Treat this as a small pilot.

Compare three configurations:

1. CPU execution with standard rotational sampling.
2. GPU execution with the same sampling and scientific settings.
3. GPU execution with the documented denser rotational sampling.

Use MEGADOCK’s existing implementations. Keep scoring settings and the number of retained predictions fixed at 50.

First establish correct execution and scientific agreement between CPU and GPU configurations at identical search settings. Define justified numerical tolerances before examining comparative results.

Then measure whether denser search improves recovery. Report DockQ for the top-ranked prediction and the best of 50 separately. Use reference structures only for evaluation.

Use a small runtime calibration to define feasible budgets. Seal configurations, timing repetitions, comparison rules and the total spending cap before evaluation. Report complete workflow time, GPU activity and billed allocation cost.

Keep three conclusions separate: execution acceleration, scientific agreement at identical settings, and quality changes from additional search. Preserve negative results and budget overruns.

Identify any pipeline contract that cannot express these comparisons. Report that limitation explicitly without substituting a different scientific question.

Limit conclusions to these four cases. Do not infer biological efficacy from docking accuracy.
