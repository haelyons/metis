coolant_proxy
=============

Self-contained run directory for one latent_skeptic run, operated without a human. The question comes from a
reframing step in the metis repository (experiments/reframe-pilot, run 20261018-1021, coolant case, independent lens,
question 2): can a cheap diffusion-based quantity rank liquids by measured viscosity, so that compute buys coverage of
candidates instead of trajectory length?

What this directory carries: SEED_INPUT.md (material for the seed author); QUESTION.md (the seed, written by a fresh
agent that saw only SEED_INPUT.md); data/ (the seed's committed data, with hashes in QUESTION.md); the latent_skeptic
pieces at commit ff9a63c, read-only (pipeline.js, triage_workflow.js, gates/, .claude/agents/); frozen/ provisioning
copied from ../latent_verify_b, read-only; LAMBDA_API.md; the keys symlink; out/. OPERATOR.md holds the operating
session's instructions.

Where latent_skeptic expects a human (choosing the seed, writing the gate commit, reading the takeaways), this run
uses fresh agents instead and records that here and in RUN_LOG.md. Lambda spend cap for the whole run: $20.

This repository is public. Nothing from this run is committed or pushed until reviewed.

Attempt 2 (2026-10-18): attempt 1 halted at the design budget check on a guessed simulation throughput
(HALT_attempt1.md). Attempt 2 cites published throughput into the design's hardware note, with a pre-authorised
calibration launch (own cap: $2, one launch) if the design still halts on a hardware guess.

Moved 2026-10-20 from latent_skeptic_meta/experiments/coolant_proxy (public repository, never committed there) into
metis (private). Paths inside the records still name the old location. Not copied: .toolchain/ (3.2 GB local
micromamba environment, still at the old location), the .keys symlink, __pycache__. The operator's transcript is here
on disk but not committed, like experiments/question-tree/claude/. The latent_skeptic pieces match dut/latent_skeptic
at ff9a63c byte for byte.
