# MD-ML-thermophysical

Reproducibility package for *Benchmarking Machine Learning and Molecular Dynamics
Methods for the Prediction of the Thermophysical Properties of Organic Liquids*
(Ogbomo, Carman, Dini, Ewen).

The package lives in two places: the git repository
<https://github.com/fionn-carman/MD-ML-thermophysical> and its Zenodo deposit
(DOI: [10.5281/zenodo.20326213](https://doi.org/10.5281/zenodo.20326213)). The two are
identical except that the deposit additionally carries the fitted model weights in
`ML/weights/`, which are too large for git and are ignored in the repository.

```
environment.yml   conda environment for everything below
ML/               the machine-learning benchmark
MD/               the molecular-dynamics case study
```

## ML

| Path | Contents |
|---|---|
| `ML/data/dataset.csv` | The benchmark dataset: one row per molecule (835), with name, type, canonical SMILES, density / dynamic viscosity / thermal conductivity at 40 and 100 °C, the per-label source method for every property, and `fold`, the locked cross-validation fold that holds the molecule out for testing. |
| `ML/data/dataset.report.json` | Machine-readable build report: label counts, per-property source-method counts, value ranges, and the deduplication and unit-conversion policy. |
| `ML/training/` | One `train_<model>.sh` per model–representation combination (26), the shared runner, and the benchmark source code. See `ML/training/README.md`. |
| `ML/results/predictions_<property>.csv` | One file per property. Every molecule with a label: identity, fold, both experimental values, and the out-of-fold prediction of all 26 models at both temperatures. |
| `ML/results/model_performance.csv` | Test RMSE, between-fold standard deviation and R² for each of the 26 models on each of the 6 targets, plus the overall rank used in the paper. |
| `ML/results/selected_hyperparameters.csv` | The hyperparameters selected on the inner validation split for every model, target, and outer fold (26 × 6 × 5 rows), with the validation RMSE of the selected configuration. |
| `ML/results/ood/` | The out-of-distribution study: the paper's 40-molecule OOD test set, the four applicability-domain signals and out-of-fold error for every training molecule, the same for the OOD molecules, the binned degradation curves, and the leave-one-family-out results. |
| `ML/weights/md_ml_model_weights.tar.xz` | The fitted model weights behind the released predictions (Zenodo deposit only). All 26 models, all six targets, all five folds. See below. |

All viscosities are dynamic (mPa s); kinematic source values were converted with
μ = ν·ρ before deduplication. Predictions are out-of-fold: each molecule is scored only
by the fold model that never saw it in training. Deduplicating the source entries gives
1,114 unique molecules, of which 279 retain no usable label after unit conversion and
conflict screening; the 835 labelled molecules are released here.

Within each fold, the models hold out `fold` for testing and split the remaining
molecules 85/15 into training and validation with a seeded draw, so both levels of the
nested split follow from the `fold` column alone.

One molecule (`mol_00305`, bis(2-ethylhexyl) sebacate) had its viscosity, density and
thermal-conductivity labels recovered from NIST WTT after training. Its predictions come from the fold-4
models, which never saw it, so they are genuine out-of-fold values; the models for the
other folds were not retrained, so their training sets omit this single molecule. See
`ML/data/dataset.report.json`.

## Model weights

`ML/weights/md_ml_model_weights.tar.xz` (in the Zenodo deposit) holds the trained models
behind the released out-of-fold predictions. **The predictions in `ML/results/`
reproduce every number in the paper on their own**; the weights are provided for anyone
who wants to re-run inference or inspect a fitted model directly. The archive unpacks
to:

```
<model>/<target>/             one file per outer fold
<model>/selected_parameters/  hyperparameters chosen for each fold
```

`<target>` is one of `viscosity_40c`, `viscosity_100c`, `density_40c`, `density_100c`,
`thermal_conductivity_40c`, `thermal_conductivity_100c`. Scikit-learn and XGBoost models
are `.joblib`; PyTorch and PyTorch Geometric models are `.pt` state dictionaries, which
must be loaded into the architecture named by the matching entry in
`selected_parameters/` (see `ML/training/src/thermo_ml_benchmark/`).

Each file is the model fitted on that fold's training and validation molecules and used
to predict that fold's held-out test molecules, exactly as released in
`ML/results/predictions_<property>.csv`.

### Which run each weight comes from

Every file is the model that produced the corresponding released out-of-fold prediction,
which means the archive draws on more than one training run:

- **Viscosity** — the run on the audited dynamic-viscosity dataset.
- **Density and thermal conductivity** — the earlier run. Those labels were byte-identical
  between the two datasets and the earlier run's predictions are the published ones, so
  its weights are the matching ones. A later re-run on the audited dataset reproduced the
  deterministic models to about 1e-5 and is not included.
- **The three transformer models, all six targets** — the run with positional encoding.
  These models were retrained after a missing positional encoding was corrected, and the
  published predictions for every target come from that retraining; the superseded
  weights will not load into the released code.

### Coverage

All 26 combinations, all six targets, all five folds: 780 weight files, 130 per target.

The viscosity heads of `chemberta_embeddings` were regenerated after the fact, because the
runner that produced the published results did not write them to disk. They were retrained
on the same data and seeds and kept only after reproducing the published out-of-fold
predictions to about 1e-7, so they are the same models.

### Loading the frozen ChemBERTa head

`chemberta_embeddings` is an MLP trained on fixed embeddings rather than a model that
consumes molecules directly. Its `.pt` files therefore sit next to a
`scaler_and_parameters.json` giving the per-fold standardisation of the embeddings and the
selected hyperparameters; the head expects embeddings standardised with those statistics,
and will return meaningless values on raw ones. Build the embeddings with
`thermo_ml_benchmark.build_chemberta_cache`. The encoder itself is the public checkpoint
`DeepChem/ChemBERTa-77M-MTR` and is not redistributed here.

### Integrity

`md_ml_model_weights.tar.xz.sha256` carries the SHA-256 of the archive.

## MD

Green–Kubo transport properties for eight representative molecules with the LOPLS-AA
force field. `MD/builder/` turns a SMILES string into a LAMMPS data file,
`MD/lammps/` holds the generic equilibration, production and continuation decks, and
`MD/analyse_tdm.py` turns the run output into the three properties. See
`MD/README.md`.

## Reproducing the ML benchmark

```bash
conda env create -f environment.yml && conda activate mol-rl

# cache the Mordred descriptors once (~20 min)
PYTHONPATH=ML/training/src python -m thermo_ml_benchmark.build_descriptor_cache \
    --data ML/data/dataset.csv --output ML/training/descriptor_cache

bash ML/training/train_xgboost_descriptors.sh          # one model, six targets
python ML/training/scripts/build_release_files.py      # rebuild the results tables
```

Every run reads the folds from `ML/data/dataset.csv`, so results are comparable across
models by construction. Fitted model files are written next to each run's predictions
under `ML/results/raw/`. The fitted weights behind the published results are in
`ML/weights/` of the Zenodo deposit; the released out-of-fold predictions reproduce
every number in the paper without them.
