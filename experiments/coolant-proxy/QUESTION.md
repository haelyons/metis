# QUESTION: does a 1-ns diffusion-derived proxy rank the 8 benchmark coolant molecules' viscosity?

## The question

Take the eight molecules that Ogbomo, Carman, Dini and Ewen simulated with Green-Kubo equilibrium MD. Compute a viscosity proxy for each one from about 1 ns of LOPLS-AA MD at 40 °C: self-diffusion from mean-squared displacement, combined with density and molecular size through a Stokes-Einstein-like or excess-entropy-like scaling. **Does the proxy's ordering of the eight molecules match the ordering of their reference dynamic viscosities at 40 °C with Spearman rank correlation of at least 0.8?**

The reframing step expected 0.7 to 0.9. It named the main risk as a systematic offset between hydrocarbons and esters (oxygenates). It would count the idea as not worth pursuing below 0.6.

## Sources and committed data

| Committed file (under `data/`) | Bytes | sha256 | Source URL |
|---|---|---|---|
| `results_paper.pdf` (accepted manuscript, Digital Discovery, doi:10.1039/D6DD00260A, 58 pp) | 3941962 | `8d4cac4fafaf146fad0ec1d24364ffd1382f6a20c6a4d1b4b6701da5cbcf36f4` | https://spiral.imperial.ac.uk/server/api/core/bitstreams/fa07c113-8958-4f1e-a010-0ef2bfc39e17/content |
| `MD-ML-thermophysical/ML/data/dataset.csv` (835-molecule reference dataset) | 164094 | `962d1c7e9517b04b97f73f7a016e102eb1cacbd13a190222c0f1e30aa33cded0` | https://raw.githubusercontent.com/fionn-carman/MD-ML-thermophysical/23121719ac1918597e75ebcdeeaed3e99df7be87/ML/data/dataset.csv |
| `MD-ML-thermophysical/ML/data/dataset.report.json` | 3063 | `2e3ae0dde81b7d7cb1b0e65f65a6bacb4ddfe77b2d6b38aede54cbb93c9b2eb9` | same commit, `ML/data/dataset.report.json` |
| `MD-ML-thermophysical/ML/results/predictions_viscosity.csv` (OOF ML predictions; also has the reference columns) | 618589 | `bf0e17fc60c8ac816debb48ca497b75a4d459f810a123f7d9c76330d06ab420d` | same commit, `ML/results/predictions_viscosity.csv` |
| `MD-ML-thermophysical/README.md` | 7885 | `cfdd004de455a66850e2de633fc24f3e790f1f325aa4050f748ab4f721ac97f3` | same commit, `README.md` |
| `MD-ML-thermophysical/environment.yml` | 1136 | `728448d63c2eb1dc9a2281018a6a93cd009026ce58982c7bafe76b9658cd09a6` | same commit, `environment.yml` |
| `MD-ML-thermophysical/MD/README.md` | 2724 | `74ddc2704a7191ed6ac83839efedb8ade8d1f8c7a5bd283cb8ba9d83e0eddcb8` | same commit, `MD/README.md` |
| `MD-ML-thermophysical/MD/builder/smiles2loplsaa.py` (SMILES to LAMMPS LOPLS-AA builder) | 43257 | `91cac1d5307eb3a0ab54be1cfd2fac3d01919bdd1cd35e7c75929bd016977008` | same commit, `MD/builder/smiles2loplsaa.py` |
| `MD-ML-thermophysical/MD/lammps/equilibrate.in` | 4066 | `1e79c3f7669b8ae2e994caacc6f56dc4bfac19737f6f61a3b0f68a94269816cb` | same commit, `MD/lammps/equilibrate.in` |
| `MD-ML-thermophysical/MD/lammps/tdm.in` | 3706 | `4d6a778e7148335a35bf680829a934c7ce4cc864fc6e050a3f23ed9854058a98` | same commit, `MD/lammps/tdm.in` |
| `MD-ML-thermophysical/MD/lammps/tdm_continue.in` | 3315 | `8504650e53d0cd5c6595b541823499bf28f7158b97720c31a05af1369833f0f6` | same commit, `MD/lammps/tdm_continue.in` |
| `MD-ML-thermophysical/MD/analyse_tdm.py` (Green-Kubo analysis) | 8482 | `6583736d33d49f17653e5c5f4f582d291129e59604f31cd3f4aa91cd57ca52f7` | same commit, `MD/analyse_tdm.py` |

Repository commit: `fionn-carman/MD-ML-thermophysical@23121719ac1918597e75ebcdeeaed3e99df7be87` (master, fetched 2026-10-18). All downloaded files are untrusted data. Do not execute any of them in place. The builder, decks and analysis script are kept for reference only, and must be reviewed before any use.

How the named sources map onto these files:
- **The "database" link** (spiral.imperial.ac.uk/entities/publication/9423c271-…) is the Spiral record of the results paper itself, not a separate database. It holds only the paper PDF and a licence file. The database of 835 molecules with about 4,700 values is released in the paper's GitHub repository. That copy is `dataset.csv`, committed above.
- **The Zenodo deposit** (doi:10.5281/zenodo.21824121, v2.0.0; concept doi 10.5281/zenodo.20326213) is a single 947,472,059-byte zip, `MD-ML-thermophysical-v2.0.0.zip`, md5 `e0779005cb1ca9a2500318a9b6f995e1`, at https://zenodo.org/api/records/21824121/files/MD-ML-thermophysical-v2.0.0.zip/content. It was **not downloaded** because it is over the size cap. According to its description and the repository README, it is the same repository plus fitted ML weights, so the files the question needs are already committed from git.
- **PMC5509262** is Ewen et al., "A Comparison of Classical Force-Fields for Molecular Dynamics Simulations of Lubricants", Materials 2016, doi:10.3390/ma9080651. It is cited as background on L-OPLS-AA accuracy for long-chain liquids. No data from it is committed or needed.

## The 8 benchmark molecules and their reference viscosities

The molecules are identified in the paper's Figure 2 caption (PDF p. 13, manuscript p. 12) and in Figure 7 (PDF p. 31, manuscript p. 30). The values below are copied verbatim from `dataset.csv` (columns `viscosity_40c`, `viscosity_100c`, `*_source`). They match the grey "Reference" bars of Figure 7b by eye, and they match the percentage deviations quoted in the text (manuscript p. 31 to 32). Units are mPa·s. The pressure is atmospheric.

| Family | Molecule (dataset name) | id | SMILES | η 40 °C | η 100 °C | Source of the 40/100 °C label | ρ 40 °C (g/cm³) |
|---|---|---|---|---|---|---|---|
| alkane | squalane | mol_00105 | `CC(C)CCCC(C)CCCC(C)CCCCC(C)CCCC(C)CCCC(C)C` | 15.06 | 3.12 | Experimental | 0.796 |
| alkane | nonylcyclohexane (1-cyclohexylnonane) | mol_00557 | `CCCCCCCCCC1CCCCC1` | 2.68 | 1.00 | Experimental | 0.805 |
| aromatic | 4-hexyl-1,7-diphenylheptane | mol_00426 | `CCCCCCC(CCCc1ccccc1)CCCc1ccccc1` | 15.56688 | 2.7927 | Experimental | 0.904 |
| aromatic | 2-(1-propylheptyl)naphthalene | mol_00400 | `CCCCCCC(CCC)c1ccc2ccccc2c1` | 13.3444 | 2.22387 | Experimental | 0.914 |
| ester | decyl stearate (octadecanoic acid decyl ester) | mol_00764 | `CCCCCCCCCCCCCCCCCC(=O)OCCCCCCCCCC` | 11.17585 | 3.12832 | Experimental | 0.863 |
| ester | bis(2-ethylhexyl) sebacate | mol_00305 | `CCCCC(CC)COC(=O)CCCCCCCCC(=O)OCC(CC)CCCC` | 10.445688 | 2.69039 | "Experimental" (patched in from NIST WTT; see below) | 0.89925 |
| polyether | 7,10,13-trioxanonadecane | mol_00942 | `CCCCCCOCCOCCOCCCCCC` | 6.4 | 2.4 | PPDS 9 correlation | 0.859 |
| polyether | tetraethylene glycol diethyl ether | mol_01025 | `CCOCCOCCOCCOCCOCC` | 5.5 | 2.2 | PPDS 9 correlation | 1.069 |

Reference ordering at 40 °C, from most to least viscous:

hexyl-diphenylheptane > squalane > propylheptyl-naphthalene > decyl stearate > bis(2-ethylhexyl) sebacate > trioxanonadecane > tetraethylene glycol diethyl ether > nonylcyclohexane

Caveats on the word "measured" in the question. Not all of these were checked against primary literature.
- **Only six of the eight labels are tagged `Experimental`.** Both polyether labels are PPDS 9 correlation values. The paper's Figure 7 caption says that all reference values are "obtained by correlation or interpolation from the source databases". The paper also states that about 44% of all viscosity labels come from database correlations (manuscript p. 7). So the target is the paper's reference values, not necessarily direct measurements.
- **The bis(2-ethylhexyl) sebacate label was added after training.** `dataset.report.json` (`post_patches`) records that it came from NIST WTT as kinematic viscosity × density: 11.616 cSt × 0.89925 g/cm³ = 10.4457 mPa·s.
- **The two highest values are close.** Squalane (15.06) and hexyl-diphenylheptane (15.57) differ by 3.4%. Propylheptyl-naphthalene (13.34) is within 15% of both. Their mutual order is within plausible reference uncertainty. This is unverified, because the paper gives no per-label uncertainty.
- **The tetraethylene glycol diethyl ether density looks high.** The reference density of 1.069 g/cm³ at 40 °C is high for a glycol diethyl ether. MD under-predicts it by 10% (manuscript p. 29). I did not verify it against primary data. It matters only if a proxy uses the reference density.
- **The paper's per-molecule MD values are not committed.** Tables S14 to S16 are in the Supporting Information, which is not on Spiral (only the PDF and the licence are deposited). MD values can only be read from the rounded percentage labels in Figure 7 and from the text on manuscript p. 31.

## Number to reproduce first

**What to reproduce.** LOPLS-AA liquid density at 40 °C (313.15 K) for the eight molecules. Use the paper's builder and equilibration protocol: a box of about 15,000 atoms, about 1 ns NPT, and the density plateau, which the paper reports is reached within about 0.2 ns (manuscript p. 29).

This number comes from the same short trajectory that a diffusion proxy would use, so it checks that the systems are built and equilibrated the way the paper's were, before any proxy is trusted.

**Paper values.** Each paper value is the reference density × (1 + label), using the blue MD labels in Figure 7a (PDF p. 31):

| Molecule | Figure 7a label | Paper MD density (g/cm³) |
|---|---|---|
| squalane | +1% | ≈0.804 |
| nonylcyclohexane | −1% | ≈0.797 |
| hexyl-diphenylheptane | 0% | ≈0.904 |
| propylheptyl-naphthalene | −1% | ≈0.905 |
| decyl stearate | −3% | ≈0.837 |
| bis(2-ethylhexyl) sebacate | −1% | ≈0.890 |
| trioxanonadecane | −1% | ≈0.850 |
| tetraethylene glycol diethyl ether | −10% | ≈0.962 |

**Tolerance.** Each molecule must fall within ±2% of its paper MD density. That allows for the 1% rounding of the labels plus seed and box differences. Tetraethylene glycol diethyl ether must also remain the single clear outlier, at about −10% against reference.

**Data-only pre-check (no MD).** Spearman ρ of the reference 40 °C viscosities against themselves, taken from `dataset.csv`, must give the ordering listed above. The `experimental_40C_mPa_s` column of `predictions_viscosity.csv` must agree with it for the eight ids.

**Context for interpreting the main claim.** I derived these numbers myself; the paper does not state them as Spearman values.
- **Paper's own Green-Kubo MD (8 ns × 10 replicas).** I rebuilt each molecule's value as the reference viscosity × (1 + its viscosity deviation in the manuscript p. 31 text). This gives Spearman ρ ≈ 0.857 against reference at 40 °C. At 100 °C it gives ρ ≈ 0.69. The paper says the force field "largely preserves the ordering … at both temperatures"; the 100 °C figure is weaker than that wording suggests. These values come from rounded deviations, and trioxanonadecane (≈2.94) and nonylcyclohexane (≈2.89) nearly tie at 40 °C.
- **XGBoost-descriptor OOF predictions** (`predictions_viscosity.csv`, column `xgboost_descriptors_40C`) give ρ ≈ 0.738 at 40 °C.
- **Granularity.** With n = 8, ρ moves in steps of 6/504 ≈ 0.012. ρ ≥ 0.8 is equivalent to a sum of squared rank differences of 16 or less.

## What would refute each claim

1. **Main claim: the proxy ranks the eight molecules with ρ ≥ 0.8 at 40 °C.** Refuted if the 40 °C proxy's Spearman ρ against the reference viscosities above is below 0.8. The reframing step's own abandon line is ρ < 0.6.
2. **The proxy converges in about 1 ns.** Refuted if the eight-molecule ordering from 1 ns trajectories is not stable across independent replicas, or does not agree with a longer trajectory of the same systems. In either case the ranking claim rests on noise.
3. **The proxy is cheaper than direct Green-Kubo viscosity.** Refuted if its total MD cost per molecule is not well below the paper's: 10 replicas × 8 ns, about 1.5 × 10⁴ CPU-hours per molecule per temperature (manuscript p. 33).
4. **Implied claim: the proxy works across chemical families, not only within one.** Refuted if reaching ρ ≥ 0.8 depends on an ordering already fixed by family. One example: hydrocarbons and oxygenates are offset in opposite directions, and the overall ρ is carried by between-family order while the within-family order is wrong.
5. **Implied claim: the proxy adds over what is already free.** If the proxy's ρ is not higher than that of trivial cheap orderings of the same eight molecules (for example molecular weight, the reference density, or the released XGBoost OOF predictions, ρ ≈ 0.74), then "preserves the measured ordering" is true but uninformative. The run must report this comparison.

## Out of scope

- Computing viscosity or thermal conductivity directly by Green-Kubo or NEMD, and re-running the paper's 8 ns × 10-replica protocol.
- Thermal conductivity proxies. The paper reports that LOPLS-AA misorders κ even with full Green-Kubo, which makes that a separate question.
- Screening the hundreds of candidate molecules, other force fields, and force-field reparameterisation.
- Correcting or re-measuring the reference labels. These include the PPDS 9 ether values, the sebacate post-patch and the tetraethylene glycol diethyl ether density. They are taken as given, with the caveats above.
- Any claim at 100 °C, unless it is reported as secondary. The question is posed at 40 °C.
- The ML benchmark (26 model and representation combinations) beyond using the released XGBoost OOF values as a comparison ordering.
- Absolute viscosity accuracy. Only rank order is asked about.
