# Understudy report: blind-01-m4-post

Primary family claude, mode fallback, on refusal halt, hands over on timeout, exit, runner, nojson, schema, declined; profile latent_skeptic; routes 1.

| # | label | role | tier | primary | kind | understudy | used? | by | ms | USD |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | gatecheck | ls-general | main | claude/sonnet | none | opencode-go/mimo-v2.6-pro | - | claude/sonnet | 9 s | 0.566 |
| 2 | elicit | ls-general | main | claude/sonnet | none | opencode-go/mimo-v2.6-pro | - | claude/sonnet | 41 s | 0.235 |
| 3 | read:q1 | triage-reader | strong | claude/opus | none | opencode-go/mimo-v2.6-pro | - | claude/opus | 60 s | 0.551 |
| 4 | read:q2 | triage-reader | strong | claude/opus | none | opencode-go/mimo-v2.6-pro | - | claude/opus | 41 s | 0.309 |
| 5 | read:q3 | triage-reader | strong | claude/opus | none | opencode-go/mimo-v2.6-pro | - | claude/opus | 17 s | 0.127 |
| 6 | skeptic:q1:off-distribution abl | ls-general | main | claude/sonnet | none | opencode-go/mimo-v2.6-pro | - | claude/sonnet | 6 s | 0.016 |
| 7 | skeptic:q1:downstream compensat | ls-general | main | claude/sonnet | none | opencode-go/mimo-v2.6-pro | - | claude/sonnet | 5 s | 0.016 |
| 8 | skeptic:q1:selection bias | ls-general | main | claude/sonnet | none | opencode-go/mimo-v2.6-pro | - | claude/sonnet | 6 s | 0.016 |
| 9 | skeptic:q1:readout artifact | ls-general | main | claude/sonnet | none | opencode-go/mimo-v2.6-pro | - | claude/sonnet | 6 s | 0.016 |
| 10 | skeptic:q1:regime specificity | ls-general | main | claude/sonnet | none | opencode-go/mimo-v2.6-pro | - | claude/sonnet | 6 s | 0.017 |
| 11 | skeptic:q1:construct validity | ls-general | main | claude/sonnet | none | opencode-go/mimo-v2.6-pro | - | claude/sonnet | 5 s | 0.016 |
| 12 | skeptic:q1:scale incomparabilit | ls-general | main | claude/sonnet | none | opencode-go/mimo-v2.6-pro | - | claude/sonnet | 6 s | 0.017 |
| 13 | skeptic:q1:noise floor | ls-general | main | claude/sonnet | none | opencode-go/mimo-v2.6-pro | - | claude/sonnet | 6 s | 0.017 |
| 14 | skeptic:q1:ceiling or floor eff | ls-general | main | claude/sonnet | none | opencode-go/mimo-v2.6-pro | - | claude/sonnet | 5 s | 0.016 |
| 15 | skeptic:q1:single-case overfit | ls-general | main | claude/sonnet | none | opencode-go/mimo-v2.6-pro | - | claude/sonnet | 5 s | 0.016 |
| 16 | skeptic:q2:off-distribution abl | ls-general | main | claude/sonnet | none | opencode-go/mimo-v2.6-pro | - | claude/sonnet | 4 s | 0.016 |
| 17 | skeptic:q2:downstream compensat | ls-general | main | claude/sonnet | none | opencode-go/mimo-v2.6-pro | - | claude/sonnet | 5 s | 0.016 |
| 18 | skeptic:q2:selection bias | ls-general | main | claude/sonnet | none | opencode-go/mimo-v2.6-pro | - | claude/sonnet | 5 s | 0.016 |
| 19 | skeptic:q2:readout artifact | ls-general | main | claude/sonnet | none | opencode-go/mimo-v2.6-pro | - | claude/sonnet | 5 s | 0.016 |
| 20 | skeptic:q2:regime specificity | ls-general | main | claude/sonnet | none | opencode-go/mimo-v2.6-pro | - | claude/sonnet | 5 s | 0.016 |
| 21 | skeptic:q2:construct validity | ls-general | main | claude/sonnet | none | opencode-go/mimo-v2.6-pro | - | claude/sonnet | 5 s | 0.016 |
| 22 | skeptic:q2:scale incomparabilit | ls-general | main | claude/sonnet | none | opencode-go/mimo-v2.6-pro | - | claude/sonnet | 5 s | 0.016 |
| 23 | skeptic:q2:noise floor | ls-general | main | claude/sonnet | none | opencode-go/mimo-v2.6-pro | - | claude/sonnet | 5 s | 0.016 |
| 24 | skeptic:q2:ceiling or floor eff | ls-general | main | claude/sonnet | none | opencode-go/mimo-v2.6-pro | - | claude/sonnet | 5 s | 0.017 |
| 25 | skeptic:q2:single-case overfit | ls-general | main | claude/sonnet | none | opencode-go/mimo-v2.6-pro | - | claude/sonnet | 5 s | 0.016 |
| 26 | skeptic:q3:off-distribution abl | ls-general | main | claude/sonnet | none | opencode-go/mimo-v2.6-pro | - | claude/sonnet | 5 s | 0.016 |
| 27 | skeptic:q3:downstream compensat | ls-general | main | claude/sonnet | none | opencode-go/mimo-v2.6-pro | - | claude/sonnet | 6 s | 0.016 |
| 28 | skeptic:q3:selection bias | ls-general | main | claude/sonnet | none | opencode-go/mimo-v2.6-pro | - | claude/sonnet | 5 s | 0.016 |
| 29 | skeptic:q3:readout artifact | ls-general | main | claude/sonnet | none | opencode-go/mimo-v2.6-pro | - | claude/sonnet | 6 s | 0.016 |
| 30 | skeptic:q3:regime specificity | ls-general | main | claude/sonnet | none | opencode-go/mimo-v2.6-pro | - | claude/sonnet | 4 s | 0.015 |
| 31 | skeptic:q3:construct validity | ls-general | main | claude/sonnet | none | opencode-go/mimo-v2.6-pro | - | claude/sonnet | 5 s | 0.016 |
| 32 | skeptic:q3:scale incomparabilit | ls-general | main | claude/sonnet | none | opencode-go/mimo-v2.6-pro | - | claude/sonnet | 5 s | 0.016 |
| 33 | skeptic:q3:noise floor | ls-general | main | claude/sonnet | none | opencode-go/mimo-v2.6-pro | - | claude/sonnet | 5 s | 0.016 |
| 34 | skeptic:q3:ceiling or floor eff | ls-general | main | claude/sonnet | none | opencode-go/mimo-v2.6-pro | - | claude/sonnet | 5 s | 0.016 |
| 35 | skeptic:q3:single-case overfit | ls-general | main | claude/sonnet | none | opencode-go/mimo-v2.6-pro | - | claude/sonnet | 5 s | 0.016 |
| 36 | adjudicate:q1 | ls-general | main | claude/sonnet | none | opencode-go/mimo-v2.6-pro | - | claude/sonnet | 6 s | 0.027 |
| 37 | adjudicate:q2 | ls-general | main | claude/sonnet | none | opencode-go/mimo-v2.6-pro | - | claude/sonnet | 4 s | 0.021 |
| 38 | adjudicate:q3 | ls-general | main | claude/sonnet | none | opencode-go/mimo-v2.6-pro | - | claude/sonnet | 3 s | 0.020 |
| 39 | write | ls-writer | main | claude/sonnet | none | opencode-go/mimo-v2.6-pro | - | claude/sonnet | 168 s | 0.586 |

Calls 39: 39 returned (0 by the understudy), 0 failed, 0 cached; refusals 0; primary failure kinds {}.

## By role

| role | calls | substituted | failed |
|---|---|---|---|
| ls-general | 35 | 0 | 0 |
| triage-reader | 3 | 0 | 0 |
| ls-writer | 1 | 0 | 0 |

## By family

| family | calls | failed | refusals | tokens | USD |
|---|---|---|---|---|---|
| claude | 39 | 0 | 0 | 56,567 | 2.926 |
