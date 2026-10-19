# Seed input: material for the seed author (not the seed itself)

A separate reframing step looked at an immersion-coolant study plan. That plan computes viscosity and thermal
conductivity of candidate coolant liquids directly with long equilibrium molecular-dynamics runs (Green-Kubo), which
converge slowly. The reframing step raised this question:

> Does a 1-ns diffusion-derived proxy rank the 8 published benchmark molecules' measured viscosity with Spearman rank
> correlation of at least 0.8?

The reasoning behind it, as the reframing step wrote it:
- Bottleneck: cost per molecule is dominated by converging the stress autocorrelation for direct viscosity (about
  30 ns per molecule), while the real need is rank order over hundreds of candidates.
- Assumption challenged: that viscosity must be computed directly and accurately in order to rank candidates.
- Reframe: measure a cheaper related quantity that converges in about 1 ns, such as the self-diffusion coefficient
  from mean-squared displacement, combined with density and molecular size through a Stokes-Einstein-like or excess-
  entropy-like scaling, and check whether it preserves the measured ordering.
- Expected by the reframing step: correlation around 0.7 to 0.9 within a homologous series; main risk a systematic
  offset between hydrocarbons and esters. It would count the idea as not worth pursuing below 0.6.

Open sources the plan relied on (check each; prefer what can be downloaded and committed):
- Database of about 4,700 critically evaluated reference values (density, viscosity, thermal conductivity) for 835
  organic molecules: https://spiral.imperial.ac.uk/entities/publication/9423c271-1953-481c-8e8d-88eeb67e2535
- Results paper with equilibrium MD of eight representative molecules (LOPLS-AA; density within 4% for seven of
  eight at 40 C; force-field errors chemistry-dependent):
  https://spiral.imperial.ac.uk/server/api/core/bitstreams/fa07c113-8958-4f1e-a010-0ef2bfc39e17/content
- SMILES-to-LAMMPS builder for LOPLS-AA with input decks and analysis script: https://doi.org/10.5281/zenodo.21824121
- L-OPLS-AA viscosity accuracy for long-chain liquids: https://pmc.ncbi.nlm.nih.gov/articles/PMC5509262/

The seed's duties (latent_skeptic_meta README, cold start step 2): the question; its committed data, or the rule
that generates it; the number to reproduce first, with its tolerance; what would refute each claim; what is out of
scope. Question level only: no arms, metrics, readout positions or thresholds beyond what would refute the claim.
