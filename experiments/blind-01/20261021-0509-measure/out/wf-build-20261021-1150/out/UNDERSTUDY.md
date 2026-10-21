# Understudy report: blind-01-m4-build

Primary family claude, mode fallback, on refusal understudy, hands over on timeout, exit, runner, nojson, schema, declined; profile latent_skeptic; routes 1.

| # | label | role | tier | primary | kind | understudy | used? | by | ms | USD |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | gatecheck | ls-general | main | claude/sonnet | none | opencode-go/mimo-v2.6-pro | - | claude/sonnet | 7 s | 0.108 |
| 2 | build | ls-builder | strong | claude/opus | declined | opencode-go/mimo-v2.6-pro | tried, failed | - | 1017 s | 9.373 |

Calls 2: 1 returned (0 by the understudy), 1 failed, 0 cached; refusals 0; primary failure kinds {"declined":1}.

## By role

| role | calls | substituted | failed |
|---|---|---|---|
| ls-general | 1 | 0 | 0 |
| ls-builder | 1 | 0 | 1 |

## By family

| family | calls | failed | refusals | tokens | USD |
|---|---|---|---|---|---|
| claude | 2 | 1 | 0 | 80,797 | 9.481 |
| opencode | 1 | 1 | 0 | 227,571 | 0.141 |
