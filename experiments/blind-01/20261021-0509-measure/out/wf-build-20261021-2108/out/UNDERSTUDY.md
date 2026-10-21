# Understudy report: blind-01-m4-build

Primary family claude, mode fallback, on refusal understudy, hands over on timeout, exit, runner, nojson, schema, declined; profile latent_skeptic; routes 1.

| # | label | role | tier | primary | kind | understudy | used? | by | ms | USD |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | gatecheck | ls-general | main | claude/sonnet | none | opencode-go/mimo-v2.6-pro | - | claude/sonnet | 7 s | 0.124 |
| 2 | build | ls-builder | strong | claude/opus | none | opencode-go/mimo-v2.6-pro | - | claude/opus | 106 s | 1.330 |

Calls 2: 2 returned (0 by the understudy), 0 failed, 0 cached; refusals 0; primary failure kinds {}.

## By role

| role | calls | substituted | failed |
|---|---|---|---|
| ls-general | 1 | 0 | 0 |
| ls-builder | 1 | 0 | 0 |

## By family

| family | calls | failed | refusals | tokens | USD |
|---|---|---|---|---|---|
| claude | 2 | 0 | 0 | 9,275 | 1.453 |
