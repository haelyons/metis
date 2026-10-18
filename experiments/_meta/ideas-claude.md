# Ideas from Claude (director session), 2026-10-18

Written from what passed in the runs so far: a named, active programme whose current practice has a gap the result
would fill; a quantity that more GPU time buys and that can vary tenfold within the budget; an independent truth to
score against; a published number to reproduce first. Programme names are from memory and unverified.

## C1 · Ensemble size for rare extremes in machine-learned weather forecasts
Machine-learned weather models make an ensemble member cheap, so operational centres can run far more members than
physics ensembles allow. Does going from tens to hundreds or thousands of members improve probability forecasts of
rare extremes (top-percentile wind or rain) scored against reanalysis or station data, or does error shared by all
members cap the skill? Programmes to check: ECMWF's machine-learned ensemble, Google's weather models.
Root question: do more members of a learned ensemble buy better forecasts of rare extremes?

## C2 · Classifier ensembles against spectroscopic truth for Rubin alert brokers
Rubin Observatory will send millions of transient alerts a night; brokers classify them so scarce spectroscopic
follow-up goes to the right objects. Does a larger ensemble of classifiers, or more retraining on simulated light
curves, raise the share of follow-up targets later confirmed by spectroscopy, scored on past survey data with public
classifications? Programmes to check: the Rubin community brokers, the Transient Name Server.
Root question: does more classifier compute pick better follow-up targets, or does label noise cap it?

## C3 · Methane plume detection scored on controlled releases
Satellite and aircraft programmes detect methane plumes with retrieval and machine-learning pipelines, and blind
controlled-release tests publish the true emission rates. Does running more detection models, or more retrieval
passes per scene, lower the smallest emission rate detected and the error on rate estimates against those known
releases? Programmes to check: Carbon Mapper, the UN methane alert system.
Root question: does more compute per scene find smaller leaks, measured against releases of known size?
