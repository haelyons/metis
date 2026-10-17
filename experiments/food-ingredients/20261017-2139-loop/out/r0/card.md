**FD1 · Industrial food ingredient replacement for sustainability.** seed pick · compute tested: yes · plan expects: the lever · REJECT

**Question.** Does increasing the capacity of a neural ingredient-substitution model measurably improve its ranking of sustainable replacements, measured as Hit@1 on Recipe1MSubs [src_gismo_sizes]?

**What is known.** Rita 2024 fine-tuned GPT-3.5 and TinyLlama on Recipe1MSubs, lifting Hit@1 from 34.53 to 38.03; no capacity sweep within one protocol exists [src_llm]. Whether ranking quality keeps rising with model capacity inside one fixed protocol on Recipe1MSubs is unmeasured; the only scaling evidence is cross-protocol.

**Hypothesis.** More capacity in a substitution ranker improves substitution ranking because larger encoders capture finer ingredient context, as LLM results suggest [src_llm].

**If compute is the lever.** Hit@1 rises with width, reaching at least 22 percent at width 512, above GISMo's 20.56, and still climbing.

**If not.** Hit@1 plateaus near GISMo's 20.56 at every width; extra capacity adds nothing, so wider models are not the lever.

**Test.** Reproduce GISMo's Recipe1MSubs result, then train the ranker at four widths 64, 128, 256, 512 with five seeds each on four GPUs; if Hit@1 climbs past the 20.56 baseline with width, compute is the lever.

*Compute axis.* Substitution-ranker capacity (ingredient-encoder embedding width): 64–512 dimension, 4 levels. Closest prior: not on this axis.

*Restructuring.* none.

**Check first.** Reproduce GISMo's published test-set MRR of 31.51 and Hit@1 of 20.56 using the official code, within 2 MRR points [src_gismo_gismo]. Tolerance: plus or minus 2.0 MRR points (mean over 5 seeds).

**Would not show.** Shows ranking accuracy on home recipes, not industrial formulations, and never measures actual environmental footprint or sensory quality of the substitute.

*Cost.* Plans $104.48 of the $1,000 budget over 22 machine-hours, leaving $895.52. Main guess: wall-clock per training run on one A100 40GB [g], measured after $24.88 of spend; the budget is reached if it is 20× higher.
