# Ensemble size for rare extremes in a machine-learned weather ensemble

## Question

Does 10 to 1,000 AIFS-ENS members beat 50 for top-percentile wind, temperature, and rain
probability forecasts, or does shared model error cap the skill?

## What to build

Run the public ECMWF AIFS-ENS v1 model (`ecmwf/aifs-ens-1.0`, N320 / 0.25 deg / 13 levels,
weights CC-BY-4.0) with the official `anemoi-inference` runner on Lambda A100 40 GB GPUs.
For each of 7 initialization dates, generate 1,000 fifteen-day members by taking the 50
IFS-ENS perturbed initial conditions from ECMWF open data and drawing 20 stochastic
realizations each (matching the operational IC structure, scaling only the stochastic
sampling). Score probability forecasts of rare extremes (top-1% and top-0.1% of 10 m wind,
2 m temperature, 24 h precipitation against a 1991–2020 ERA5 per-gridpoint seasonal
climatology) with fair CRPS and the Brier score, then subsample each date's 1,000 members
down to 10 / 50 / 100 / 250 / 500 / 1,000 with bootstrap to read off skill versus N.

## Baseline

ECMWF operational AIFS-ENS: 50 perturbed members plus one control member
(s_ecmwf_50). We reproduce and then exceed that size on the same public model weights.

## How to check it is right

- Anchor: reproduce the published "four minutes for AIFS-CRPS N320 on an A100 40 GB GPU"
  per-member time and the 38 GB memory requirement; one control run must match the ECMWF
  open-data AIFS ENS control for the same date within the ensemble's own spread (exact
  match is impossible because GPU runs are non-deterministic).
- Calibration sanity: the 1,000-member rank histogram against ERA5 is near-uniform.
- Fair-score sanity: at N=1000 the fair CRPS converges to the raw CRPS (the size correction
  is only material at small N).
- Decision: if_lever if extreme-event Brier / fair-CRPS skill at 1,000 members beats 50 by
  >= 0.01 and keeps rising to 1,000; if_not if the gain past 100 members is < 0.005 (flat
  within the bootstrap CI). Noise is separated from signal by bootstrapping over which
  members are sampled and over the 7 dates, and by the fair-score correction, which strips
  the finite-ensemble-size bias out of the raw score.

## Cost (Lambda on-demand, prices read 2026-10-18)

- Rate: 8x NVIDIA A100 SXM 40 GB at $1.99/GPU/hr (s_lambda).
- Per member: 4 min (s_crps_paper) = 0.0667 GPU-h.
- Main run: 7 dates x 1,000 members = 7,000 members x 0.0667 h = 466.7 GPU-h.
- Main cost: 466.7 x $1.99 = $928.7.
- Pilot (time box): 10 GPU-h on 1 A100 = $19.9.
- Scoring (time box): 6 GPU-h on 1 A100 = $11.9.
- Storage: ~100 GiB for ~4 days at $0.20/GiB-month = $2.7.
- Total stated: ~$963; hard stop $1,000.

## Phases

1. pilot — setup, timing, memory, anchor one control run (gate: per-member time <= 10 min).
2. era5 — download ERA5 verification + climatology thresholds.
3. main — 7 x 1,000 members on the 8-GPU instance.
4. score — subsample, fair CRPS + Brier vs N, bootstrap CIs.
5. station (optional) — verify top-percentile events against SYNOP stations.

## Prior art

HENS Part 2 (Mahesh et al. 2025) ran 7,424 members of SFNO-BVMC for each day of summer
2023 and showed huge ensembles sample 4-sigma tails and reduce outliers — but for a
different model (an MSE-trained multi-checkpoint ensemble), and it did not measure a
skill-versus-N saturation curve with a fair score for AIFS-CRPS, whose members are
exchangeable draws of one afCRPS-trained distribution.
