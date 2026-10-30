# Understudy report: blind-01-m4-build

Primary family opencode, mode fallback, on refusal halt, hands over on timeout, exit, runner, nojson, schema, declined; profile latent_skeptic; routes 1.

| # | label | role | tier | primary | kind | understudy | used? | by | ms | USD |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | gatecheck | ls-general | main | opencode-go/mimo-v2.6-pro | timeout | claude/sonnet | yes | claude/sonnet | 1800 s | 0.000 |
| 2 | build | ls-builder | strong | opencode-go/mimo-v2.6-pro | timeout | claude/opus | yes | claude/opus | 7200 s | 0.000 |

Calls 2: 2 returned (2 by the understudy), 0 failed, 0 cached; refusals 0; primary failure kinds {"timeout":2}.

## By role

| role | calls | substituted | failed |
|---|---|---|---|
| ls-general | 1 | 1 | 0 |
| ls-builder | 1 | 1 | 0 |

## By family

| family | calls | failed | refusals | tokens | USD |
|---|---|---|---|---|---|
| opencode | 2 | 2 | 0 | 0 | 0.000 |
| claude | 2 | 0 | 0 | 8,391 | 2.016 |
