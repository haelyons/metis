# s28 narrowing

No narrowing.

The root question stays the seed's question, verbatim (`m5/BRIEF.md`): whether MEGADOCK's GPU implementation makes denser docking search affordable and whether that improves pose recovery within a fixed budget, on the four seed cases. It keeps the three separate conclusions: execution acceleration, scientific agreement at identical settings, and quality change from denser search.

The next run is a repeat of s27's fixture recording run, which measures the inputs to the sealed tolerance rule (`science/s27/TOLERANCE_RULE.md`). It changes how the GPU binary is built and how the evaluator is invoked, plus the run's warmup, timeouts, budget and seeds. It does not change the arms, the outputs, the comparisons or the rule. The fixtures are measuring instruments, not new cases. Every conclusion stays limited to the seed's four cases. Nothing is dropped.
