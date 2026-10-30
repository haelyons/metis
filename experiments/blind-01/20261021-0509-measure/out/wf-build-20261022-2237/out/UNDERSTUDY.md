# Understudy report: blind-01-m4-build

Primary family opencode, mode fallback, on refusal halt, hands over on timeout, exit, runner, nojson, schema, declined; profile latent_skeptic; routes 1.

| # | label | role | tier | primary | kind | understudy | used? | by | ms | USD |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | gatecheck | ls-general | main | opencode-go/mimo-v2.6-pro | none | claude/sonnet | - | opencode-go/mimo-v2.6-pro | 38 s | 0.012 |
| 2 | build | ls-builder | strong | opencode-go/mimo-v2.6-pro | timeout | claude/opus | yes | claude/opus | 5262 s | 0.195 |

Calls 2: 2 returned (1 by the understudy), 0 failed, 0 cached; refusals 0; primary failure kinds {"timeout":1}.

## By role

| role | calls | substituted | failed |
|---|---|---|---|
| ls-general | 1 | 0 | 0 |
| ls-builder | 1 | 1 | 0 |

## By family

| family | calls | failed | refusals | tokens | USD |
|---|---|---|---|---|---|
| opencode | 2 | 1 | 0 | 364,554 | 0.206 |
| claude | 1 | 0 | 0 | 42,704 | 3.315 |
