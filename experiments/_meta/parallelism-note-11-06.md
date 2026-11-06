# Parallelism note, 2026-11-06

Written for the SoTA Scientific Parallelism Hackathon (21-22 Nov, London) and for the PhD question behind it.
Sources read: this repo (`dut/pipeline`, `experiments/_meta`, blind-01/02), `haelyons/proteus` at b6c55b2
(README, `results/README.md`, kernels, intervention scripts), `haelyons/janus` at fab5c61 (README rounds 1-36,
CONTRACT, the Fable consult). Web: secondary coverage of the Goodfire essay and the Prima Mente work, the
InterPLM line, AtP*, the 2026 auto-interp evaluation papers, the hackathon listing.

## 0. Three corrections before anything else

1. The essay is "Neural Networks Are Already Clean" (Cammarata, Goodfire, 2026-10-15), not "Circuits are
   already clean". Janus already has the title right; the note matters only because the circuits claim is the
   weaker half of the essay and the one your own round 16-17 results bear on most directly.
2. It is about 1,000 neuron *reports*, not 1,000 papers: roughly 500 from Qwen3-32B and 500 from
   Qwen3.6-35B-A3B, each an explainer agent's write-up plus, for most, intervention numbers. The headline
   validation is 76% against 11%, on 183 positive-side descriptions from 200 sampled neurons, where "strong"
   means at least 30% of the neuron's top corpus activation.
3. The Alzheimer's work is not a genome model. It is Prima Mente's Pleiades, a 7B epigenetic foundation model
   over methylation and genomic sequence, applied to cell-free DNA; Goodfire's reported finding is that the
   classifier leans mostly on fragment length. The DNA-model SAE work is a separate Arc Institute
   collaboration on Evo 2 (BatchTopK SAE on the residual stream after layer 26).

I could not fetch `already-clean.goodfire.com` or `goodfire.com` from this session: the network policy
blocked them. Everything above is secondary coverage. The companion technical paper is still described as
forthcoming, so the 76/11 number has no methods section behind it yet. That matters for section 5.

## 1. What I take the question to be

Three nested questions, and they need different answers.

**Hackathon (two days, GPUs provided, judged on whether the entry reshapes a problem to expose parallelism and
on the scientific value of the result).** What single reshape, built on what you already have, is both
demonstrable in two days and genuinely a reshape rather than an optimisation?

**Programme.** Given what Janus measured about agent pipelines and what Proteus measured about units, what
changes to the agent loop are worth making, in order of evidence?

**PhD.** You wrote the motivation as: biology foundation models encode fantastic priors, you want to decode
and then use them, and it is unclear what using them would look like. That last clause is the real question.
Section 7 proposes a form for it that is falsifiable and that your existing assets uniquely support.

Throughout, the operative constraint is the one you named: what is parallelisable, and what is the lowest
hanging fruit given the footprints of the experiments that already ran.

## 2. Footprint audit: where the time actually goes

All numbers from `proteus/results/README.md`, measured, not estimated.

### The full ESM-2 650M pass over Swiss-Prot (A100 40 GB, follow-up run)

| stage | time | share |
|---|---|---|
| forward | 48.8 min | 74% |
| atlas collection (compaction, merges, subsample stats, Gram) | 11.6 min | 18% |
| checkpoints | 3.8 min | 6% |
| paired timing forwards (run configuration, not method) | 2.0 min | 3% |
| pilot + final save | 5.0 min | - |
| **end to end** | **71.3 min** | |

Steady-state atlas overhead settled at 0.208 of a forward, from 0.286 on the science pass and 1.24 in phase 1.

### Inside one forward (A10, 32k-row batch, 1.33 s)

| kernel class | time | share | what it is |
|---|---|---|---|
| elementwise | ~640 ms | 50% | HF ESM code: unfused erf-GELU (five kernels per layer over [32k, 5120], ~225 ms) and rotary embeddings in fp32 with casts, cat and neg (~300 ms) |
| GEMM | 517 ms | 40% | bf16, 69-75 TFLOP/s standalone |
| attention | 92 ms | 7% | SDPA; not the bottleneck at these lengths |
| layer norm | 30 ms | 2% | |

### Inside the collection (A100, batch 3000, per batch)

| component | time |
|---|---|
| subsample statistics | 80.9 ms (stats kernel 40.1, Gram 25.3, int8 enrichment GEMM 11.0) |
| merge | 23.2 ms |
| compaction (the Triton filter) | 19.1 ms |

The row split later took the stats kernel to 19.1 ms per batch.

### The conclusion that should change your plan

**The Triton kernel for speeding up activation collection is already built, already won, and is no longer
where the hour goes.** The compaction kernel went from 2.58 ms to 0.95 ms per [32768, 5120] with the empty-tile
early exit, and across 33 layers that is 2.4% of a forward. The complete collection at steady state costs 0.21
of a forward while an unfiltered top-K alone costs 0.92 (baukit's algorithm) or 1.5 (dense). You measured a 12x
gain against the fair external comparison and 133x against your own dense reference.

What is left in collection is the statistics kernel and the Gram, which run at roughly a third to a fifth of
what you predicted for them: the Gram reaches about 55 TFLOP/s of the A100's 312, and the stats kernel is
latency-bound rather than bandwidth-bound. Fixing both might take the atlas from 11.6 min to perhaps 7. That is
about 6% of the job.

Meanwhile 50% of the forward on the A10 is HF's unfused elementwise code, and the forward is 74% of the job.
That single number is the largest measured inefficiency anywhere in the stack, and it belongs to the model
implementation, not to your collector.

Caveats I will not paper over. The 50% is an A10 measurement; the share on an A100 is unmeasured and will be
different, because elementwise work is bandwidth-bound (A10 roughly 600 GB/s, A100 roughly 1,555) while the
GEMMs scale with compute (70 against 312 TFLOP/s measured and peak respectively). The direction is clear, the
magnitude is not. `torch.compile` appears nowhere in the repo; `attn_implementation="sdpa"` is set, the rest is
stock HF. So the first half day of any kernel work is a profile on the target GPU, and possibly one line of
`torch.compile`, before anything is hand-written.

### The other footprint: the scientific loop

The whole Proteus programme, phase 1 through the use study, cost about $19.90 of GPU. Six units got full
round-2 case studies. For none of the six did a frozen prediction establish that the model *uses* the unit.
The 650M repeat-counter unit took a discovery pass, three failed pre-registered explanations, a post-hoc
hypothesis, a fresh test, a null downstream result, and then a whole further study to find that the model does
use the repeat and that almost none of the use passes through that unit, its layer-15 co-responders, or layer
15's FFN at all.

So the binding constraint on the science is not GPU hours. It is that every unit costs a serial chain of
hypothesis, test and revision, and most links in that chain are agent turns and human judgement.

## 3. The parallelism map

Three classes. They need different treatment and only one of them is unsolved.

### P1. Already parallel, and provably so: the stream

This is the reshape you have already pulled off, and I do not think you are selling it correctly. The claim is
not "we wrote a fast filter". The claim is:

> A per-unit, per-token statistic over a corpus looks like a materialisation problem of about 70 TB. Replace
> the materialisation with a monotone admission rule plus an order-independent sampler, and it becomes a
> single streaming pass whose result is exact and whose shards merge exactly.

Three properties make it shardable, and each is load-bearing:

- top-K admission uses `s >= tau` on an int64 key where the running K-th key only rises, so any arrival order
  admits every token that could still enter;
- the reservoir is bottom-k on a bijective 32-bit hash of the packed token id, which is order-independent by
  construction;
- `Atlas.merge_from` combines runs over disjoint data exactly, provided shards share seeds computed from the
  global stream size.

Which means N GPUs give close to N times the throughput with a bitwise-identical result, and the only global
coupling is the seeding pass (2.6 min). You verified 0 of 1,666,065 seeded bins short. You have the exactness
proof that most streaming interpretability infrastructure does not bother with.

For the hackathon this is the credential, not the project. It is already done, and judges reward a reshape
performed during the event.

### P2. Parallel in principle, serial in practice: the interventions

This is the gap, and it is large.

`scripts/pair_silencing.py`, `unit_writes.py`, `case_tests.py`, `ubq650_*.py` all run interventions as a
Python loop over sequences, positions and conditions, one forward per condition, batch size 1. Measurement #3
was 900 cases and 1,800 silenced forwards. On a CPU at 8M that took 201 s and was fine. On an A100 at 650M,
batch size 1 leaves the device almost entirely idle: the GEMMs you measured at 69-75 TFLOP/s are running at
batch 1 against a shape designed for 32,768 rows.

Every axis here is independent:

- unit (168,960 x 2 poles)
- position within a protein
- condition (silence, scale, control-matched unit, joint)
- construct (transplant, shuffle, chimera, point mutation, repeat count)
- protein

The only reason these are serial is that the hook applies one modification per forward. A hook that reads a
per-row plan tensor turns the whole product into a batch dimension. Nothing about the science changes.

### P3. Genuinely serial: hypothesis, test, revision

The chain per unit is: look at evidence, propose a computation, freeze a prediction, run a fresh test, read
the outcome, revise. Latency-bound on agent turns and on your own reading.

The important result here is Janus's, and it is the hinge of this whole note. See section 5: the agent's
*choosing* of experiments adds nothing measurable over *seeing* the same experiments, and a precomputed
generic measurement table beats agent exploration at the one thing exploration kept failing at. That means P3
is not irreducibly serial. It is serial because the pipeline is written as a loop, and a large part of it
factors into a parallel precompute plus a cheap selection.

## 4. What I would build at the hackathon

### Primary: the effect atlas

**One sentence.** Today, measuring what a unit does downstream costs one forward per unit per intervention;
reshape it into one screening pass over all units plus an exactly-verified filtered set, and the question "does
the model use this unit" becomes answerable for 168,960 units instead of six.

**The reshape, in your own idiom.** This is the same move you already made for collection, applied one level
up. Collection: do not materialise 70 TB, use a monotone bound to admit only what can matter, and keep a dense
fallback for the bursts. Effects: do not run U separate forwards, compute a cheap bound on every unit's effect
in one pass, admit only the candidates that could exceed the threshold, and verify those exactly with real
patched forwards. The dense path stays as the correctness reference, exactly as `--naive` does now.

**Prior art, named honestly.** The screen is attribution patching, and AtP* (DeepMind, 2403.00745) is the
careful version: two forward passes and one backward give every component's attribution at once, with a
softmax recomputation for query and key patching and GradDrop for cancellation false negatives, and the
authors already propose using it as a pre-filter ahead of real patching plus a statistical bound on remaining
false negatives. You are not inventing the screen. What is not in the literature, as far as I can find:

- the screen applied to FFN units at whole-model, whole-corpus scale to produce an *atlas of effects* rather
  than a circuit for one prompt;
- a batched intervention kernel where the plan is a tensor, so verification itself is parallel;
- any of it in a protein model, where the readout is a residue distribution with real biological endpoints
  rather than a logit difference on a curated prompt;
- the exactness discipline you already apply to collection, carried into the causal measurement.

**Two days of work, concretely.**

Day 1 morning: profile the forward on whatever GPU the organisers provide. Try `torch.compile` on the ESM
encoder and measure. If the A10 ratio holds at all, a fused GELU and a bf16 rotary are the next step and both
are small Triton kernels over a [rows, 5120] tile, which is the shape your compaction kernel already tiles
well. Target: a measured forward-pass reduction, stated as a fraction, with a bitwise or tolerance-stated
equivalence check against the stock implementation. This is the part that is certain to produce a number.

Day 1 afternoon: the batched intervention hook. A plan tensor of (row, layer, unit, position, new value) and a
hook that scatters it. Correctness gate: the batched path must reproduce the existing one-at-a-time results
bitwise on a fixture, in the style of your v1-against-v3 equivalence gates.

Day 2: the screen. Gradient times activation for every unit at every position against a chosen readout
(masked log probability of the true residue is the natural one, since you already use it everywhere), then
exact verification of the top candidates through the batched path, then the calibration plot that is the real
scientific deliverable: screened effect against verified effect, with the false-negative rate measured on a
random subset rather than assumed.

**Scientific value, stated the way the judges will want it.** Your own records say the open question in the
field is not what a unit responds to but whether the model uses it. Goodfire's headline validation is a
response test: does the neuron fire on new inputs the explanation predicts. That is a statement about the
input side. The 2026 auto-interp literature has now proved the limit of this formally: detection-style scores
are invariant under substitution of any collision-equivalent feature, so a high score cannot certify that a
description is correct. The effect atlas measures the output side at the same scale, which nobody has done,
and your Proteus case studies are the evidence that doing it one unit at a time does not scale.

**Fallback that still ships.** If the screen calibrates badly, the batched intervention path alone is a
complete result: the same six-unit case study battery, run across thousands of units, with a measured speedup
and an exactness gate. That is a reshape and a number.

**Risks.** Attribution is a first-order approximation and protein models are small enough that saturation
effects may differ from the LLM setting where AtP* was developed; measure, do not assume. A masked-prediction
readout has a confidence ceiling, which bit you already in the ubiquitin study, so pick readouts with headroom
(the disagreeing-copy construct had log p(true) at -6.3 and no ceiling). Two days is tight for three
components; the ordering above is deliberate, each stage ships on its own.

### The alternative, if you want to stay closer to your original framing

Streaming SAE training as a one-pass estimator. The standard pipeline is two-phase: dump activations to disk,
then shuffle and train. Llama Scope reports latent activations at 8 KB per token against 2 bytes for text and
says data loading becomes the main bottleneck; their answer was a producer-consumer buffer. Your reshape would
be stronger: you already have a principled, order-independent, reproducible sampler over the stream (the
hashed subsample at rho_sub, the reservoir bins), so an SAE can be fitted inside the same pass that builds the
atlas, with a stated sampling guarantee rather than a buffer heuristic.

I rank this second for the hackathon for two reasons. The epoch problem is real: SAEs normally want many
passes over shuffled activations, so a one-pass version is a different estimator and you would have to defend
it rather than just benchmark it. And the SAE-on-protein-models space is now crowded: InterPLM is in Nature
Methods, there is an ESMC layer-60 SAE for enzyme function, a 2026 preprint steers SAE features for variant
effect prediction on VenusMutHub, and there are public ESM SAE checkpoints. Entering it needs a differentiator
and "we trained one too, faster" is not one.

## 5. The agent pipeline, ordered by the evidence you already hold

Everything in this section is from Janus's measured rounds. I have added the 2026 literature only where it
converges with what you found.

**1. Measurement first, agent second. This is the big one, and it is also a parallelism result.**

Rounds 27 and 28: when the agent had to find the axis by looking at photos, it named a facing direction in 0
of 72 refinements. The signal was in front of it. Round 29: give the same agent a generic, blind-answered
measurement table with peer percentiles and a held-out check, and it picks the correct side for all four
oriented units, 3 of 3 samples, with no mention of direction anywhere in the prompt. Round 29B: the final
reader keeps a row if and only if it held, 31 of 32, and drops 0 of 30 that did not.

The structural fact underneath it is the one that matters for the hackathon: in round 29, 570 photos were
answered once, by 48 calls, and that single pass served all six units. Cost goes from O(units x turns) to
O(corpus) + O(units x one cheap call). That is the same reshape as the effect atlas, applied to the
annotation step.

In proteins the annotation is already free. You computed descriptors for 549,655 accessions and 194.8M
residues in 21 minutes on 28 processes: ss3, contacts, burial, pLDDT, phi/psi, C-beta. No VLM, no LLM, no
agreement problem. The protein version of round 29 is pure compute, and it is sitting on disk.

**2. Stop using pick-style scoring as the primary metric.**

Round 15: on mixed4e:55 the *wrong unit's* explanation scored fire_hit 1.00. Round 18: the pick test rejects
readings that are wrong (wrong-unit lowest in 5 of 5) but cannot rank readings that are partly right, because
six picks only need to find some firing photos. Round 19 fixes it: predicting activation across the whole pool
and scoring by Spearman passes both planted controls and charges a half-right reading for the firing items it
rates low.

This is exactly Goodfire's validation design, and it is the design the 2026 collision paper proves cannot
certify a description. You have the empirical demonstration and the field now has the proof. Writing that up,
with your planted pairs as the controls, is a short paper with a clear claim.

**3. Control the basis, or do not make claims about the basis.**

Round 33 full: an agent reads neurons better than random directions in the same MLP space (simulator rho 0.64
against 0.48), but the gap rests on one bad direction, and two random directions read as well as the best
neurons (0.68, 0.76). Round 32: random directions keep about three quarters of a random channel's excess over
chance and two thirds of its replication rate. Round 36: random directions keep their cores better than
neurons do.

"Neural networks are already clean" is a claim about the neuron basis. A random-direction control is the one
experiment that separates "the basis is special" from "our description methods find structure anywhere", and
I cannot find it in the public Goodfire material. Running it properly, in a domain with external ground truth,
is a real contribution and it costs you almost nothing because you have already built it twice.

**4. Control the family, not just the layer.**

Round 27 post hoc: of the held predictions, 15 of 16 were shared with the unit's peers. A layer percentile
tests a unit against the whole layer, and a held prediction then often describes a family rather than a unit.
Against peers, the oriented units stood out exactly where the layer percentile hid them.

Proteus has the protein analogue already measured: co-activation tracks input weights at Spearman 0.62 in the
trained model against 0.22 in shuffled-weight controls, while output cosine is unrelated to everything. So
"family by input or by firing" is well defined and "family by output" is not. Peer sets should be built from
input weights or co-activation, and every per-unit claim should carry its peers' numbers beside it.

**5. Price the exits.**

Janus round 1: no arm ever said "cannot tell" on the card whose deciding context was outside the window, and
held-out accuracy there was near chance. Confident wrong readings every time. Separately, the Metis card
pipeline shows the mirror image: cheap judges saturate (`open` was 5 on 18 of 19 run-F cards, `reshape` 1 on
15). A pipeline with no priced exit produces a confident answer for every unit, which at atlas scale is a
confident answer for 168,960 units.

Two exits need prices. "Unrelated" must be earned by single-variable rivals failing. "Cannot tell" must be
reachable, and the only way I know to make it reachable is to make a wrong confident answer cost more than an
abstention in the score the agent is actually optimised against.

**6. Do not let the agent choose the experiments.**

Round 33, the sealed test: P1 (chooses its own probes) against Y1 (sees the same probes, chose nothing).
P1 minus Y1 on simulator rho is +0.013, ahead on 8 of 14, sign test p 0.40. Post hoc on held-out it is +0.033.
Experiments help a lot (+0.06 held-out over the card alone, +0.25 on the misleading planted card), but the
gain comes from seeing what they show.

This is the finding that makes everything parallel. If choosing adds nothing, the serial propose-run-observe
loop can be replaced by a fixed battery computed in advance, in parallel, for every unit at once. It is the
single most actionable result in Janus and it points straight at the hackathon project.

**7. Protein-specific traps, from Proteus, that an agent pipeline will walk into at scale.**

- Top-k enrichment measures database redundancy. The 650M unit whose top-64 was 100% ubiquitin is a repeat
  counter, not a ubiquitin unit: isolated human ubiquitin reads -1.34 at the same residue, and the response
  grows monotonically with copies of *any* local sequence, confirmed on 5 of 5 held-out fragments. Your own
  note is the right one: a DMS comparison against that unit would have been meaningless.
- At bf16, 79.9% of a 650M unit's top-64 slots sit in exact-value ties, and 76.4% of columns have their K-th
  value tied with a token outside the list. "The top-64 tokens of a unit" is not well defined without a tie
  rule. Any pipeline that ships top-k lists to an explainer agent is shipping an arbitrary choice.
- Untrained units are *more* residue-specific than trained ones (effective residues 1.3-2.4 against 2.9-4.7).
  "This unit fires on one amino acid" is the easiest result to obtain from a network that learned nothing.
  Every description pipeline needs the shuffled-weight control as a floor.
- Your ruler calls 93.2% of trained units "context", and so it does for untrained ones (98.0%). Only the
  "structural" call separates them (408 against 4-11). A category that fires for everything is not a finding.

**8. Keep the seal.** The sealed-prediction discipline across both repos is, bluntly, the most valuable thing
you have. Nearly every interesting result in Proteus is a *failed* prediction that was recorded anyway: the
stats kernel 3-5x slower than predicted, the ubiquitin copy counts wrong by two orders of magnitude and wrong
in direction on the control, the row split giving 1.7x instead of 4-6x, the layer-15 FFN patch increasing
copying when it was predicted to decrease it. No agentic pipeline I know of has this property, and it is what
would make a thesis out of the work rather than a tool.

## 6. The geneticist: what they are actually for

Not for explaining features. For three things that nothing in the pipeline can do.

**Killing redundancy artifacts early.** A geneticist looks at "this unit's top 64 are all ubiquitin" and says
"those are polyubiquitin precursors, they are tandem repeats" in about one second. It cost you a discovery
pass, three failed explanations and two studies to get there. At atlas scale this class of error will be the
dominant one, because Swiss-Prot's redundancy structure is not uniform.

**Supplying endpoints that are not in UniProt.** Everything the ruler can test is an annotation the model may
well have seen. The questions a geneticist brings (does this variant segregate with disease, does this
residue matter in this condition, which of these two paralogues is the functional one here) are the ones where
a model-internal feature could be worth something. ProteinGym and the DMS literature are the public version;
a collaborator with an assay is the real version. Note your own ubiquitin DMS finding: 43 of 70 positions
differ between conditions, and at a +-0.1 margin 38 of 70 are equivalent across conditions, so "the DMS says
this position matters" is not one statement. A geneticist is who tells you which margin is the right one.

**Judging novelty.** Is this feature a known annotation under another name, or is it something the databases
do not have? That judgement is the whole difference between a demonstration and a result, and it is not
available from inside the pipeline.

**The one experiment worth their time, and you already built the asset for it.** `strict_heldout_20261105`
produced 287 Swiss-Prot entries with no MMseqs2 hit at 30% identity over 50% coverage to any UniRef50 2021_04
representative, 284 with no hit at all at E <= 1e-3, and 109-111 of those with AlphaFold models. With the
caveat you recorded honestly: UniRef50 membership is defined against cluster seeds, 80.6% of representatives
are seeds, so for about one cluster in five the defining sequence was not searched, and ESM-2 sampled UniRef90
members inside clusters.

Nobody else has this set. It is the only clean place to ask the question that makes a prior *usable*:

> On proteins with no detectable homolog in the model's training release, does a model-internal feature
> predict a property that composition and homology baselines cannot?

Pre-register it, pick the property with the geneticist, and the answer is informative either way. A negative
result says the priors are interpolation over the training distribution, which is worth knowing and nobody has
shown it cleanly. A positive result is the thing you are reaching for.

The AAV capsid question in blind-01 came from exactly this kind of collaboration and has exactly this shape:
a matched transcytosing-against-retained pair, a readout from the same system, and a colleague who knows which
comparison is real.

## 7. The PhD question

Your draft motivation ("models encode fantastic priors, decode and use them") is not yet a question because
"use" is unspecified. Here is a form that is falsifiable, that three of your assets uniquely support, and that
does not depend on the Goodfire claim being true.

> **Which internal features of a protein foundation model are usable priors: ones the model itself uses, that
> survive a held-out test, and that predict biology no sequence-similarity baseline can? And is the apparent
> legibility of those features a property of the model, or of the methods we describe it with?**

Three legs, each already instrumented:

**Basis.** Run one description-and-validation pipeline over four populations in the same space: FFN units,
random directions, SAE latents, and shuffled-weight controls. Same evidence, same scorer, same held-out
protocol. Janus has the evidence this is the right question (random directions read as well as the best
neurons on two measures) and Proteus has the shuffled-weight controls. The null is that the basis does not
matter and the description method does.

**Use.** The effect atlas from section 4. Primary endpoint, not an afterthought: for what fraction of units
does a frozen prediction establish that the model uses the unit, and what distinguishes those units? Current
score from Proteus round 2: zero of six.

**Transfer.** The strict held-out set from section 6. This is where "usable prior" gets a definition: a
feature is a usable prior if it carries information about a protein the model has no homolog for, beyond what
composition and search give you.

What makes it yours rather than a crowded-field entry: the exact atlas and its shardable design, the strict
held-out set, the sealed-prediction record including the failures, and the measured negative results about
agent pipelines. Four things that are hard to acquire and that nobody applying to the same programmes will
have.

One honest warning. Do not build the programme on top of "neurons are already clean". The companion paper is
not out, the headline number measures responses to new positives rather than explanation accuracy, and your own
Janus rounds 15, 18 and 19 show the validation design cannot rank partly-right readings, which the 2026
collision result now proves in general. Build the programme that *tests* the claim. You are most of the way
there already and it is a better thesis either way.

## 8. Lowest hanging fruit, ranked

| # | Thing | Effort | Expected gain | Evidence it is the right target |
|---|---|---|---|---|
| 1 | Profile the forward on the target GPU, then `torch.compile` the ESM encoder | hours | unmeasured, possibly large | elementwise is 50% of the A10 forward and the forward is 74% of the job |
| 2 | Batch the interventions behind a plan tensor | one day | tens to hundreds of times on GPU | every intervention script runs batch size 1 in a Python loop |
| 3 | Fused GELU and bf16 rotary, if 1 leaves headroom | one day | up to ~39% of forward on A10 ratios | 225 ms + 300 ms of a 1.33 s forward |
| 4 | Replace pick-style scoring with pool-ranking plus planted controls | one day | removes a scorer that cannot rank partly-right readings | Janus rounds 15, 18, 19; the 2026 collision result |
| 5 | Precompute the descriptor table once, serve all units | hours | turns O(units x turns) into O(corpus) | Janus round 29; descriptors already computed for 549,655 accessions |
| 6 | Random-direction and shuffled-weight controls on every claim | hours | makes basis claims meaningful | Janus 32, 33; Proteus #6 |
| 7 | Attribution screen with exact verification | two days | turns U forwards into one pass plus a filtered set | AtP* exists; the atlas-scale application does not |
| 8 | Shard the atlas pass across N GPUs | hours | near-linear | `merge_from` is already exact across disjoint shards |
| 9 | Tune the stats kernel and accumulate the Gram inside the GEMM | one day | perhaps 4 min of 71 | 55 of 312 TFLOP/s; the `+=` costs 21.5 ms per batch |
| 10 | Further compaction-kernel tuning | - | 2.4% of a forward, at most | already won; stop |

## 9. What I would not do

- Train another SAE on ESM-2 as the centrepiece. InterPLM is in Nature Methods, there is an ESMC layer-60 SAE
  for enzyme function, a 2026 preprint already steers SAE features for variant effect prediction, and public
  checkpoints exist. Use theirs as one of the four populations in the basis leg.
- Optimise the compaction kernel further.
- Build a larger agent loop before fixing the scorer. A better explainer scored by a metric that cannot rank
  partly-right readings produces more confident text and no more knowledge.
- Lead with "neurons are clean" in an application. Lead with the thing you can show: sealed predictions,
  measured failures, and an exactness discipline.

## 10. What I could not check

- The Goodfire pages did not resolve from this session (network policy). Everything about the essay, the
  gallery, the 76/11 result and the Alzheimer's work is from secondary coverage. Fetch them yourself before
  citing any of it.
- The hackathon details (dates, prize, judging on reshaping for parallelism and on scientific value) come
  from one source, the SoTA Letters announcement, via search.
- Whether the A10 elementwise share holds on A100 or H100 is unmeasured, and it is the number the first
  recommendation rests on.
- `dut/latent_skeptic` is an uninitialised submodule here, so I read the measure route only through
  `dut/pipeline/m5` and the blind-01/02 records.
