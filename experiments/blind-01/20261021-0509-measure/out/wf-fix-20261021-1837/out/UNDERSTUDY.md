# Understudy report: blind-01-m4-fix

Primary family claude, mode fallback, on refusal understudy, hands over on timeout, exit, runner, nojson, schema, declined; profile latent_skeptic; routes 1.

| # | label | role | tier | primary | kind | understudy | used? | by | ms | USD |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | fixer | ls-fixer | strong | claude/opus | none | opencode-go/mimo-v2.6-pro | - | claude/opus | 157 s | 0.259 |
| 2 | verifier | ls-fixer | main | claude/sonnet | none | opencode-go/mimo-v2.6-pro | - | claude/sonnet | 153 s | 0.058 |

Calls 2: 2 returned (0 by the understudy), 0 failed, 0 cached; refusals 0; primary failure kinds {}.

## By role

| role | calls | substituted | failed |
|---|---|---|---|
| ls-fixer | 2 | 0 | 0 |

## By family

| family | calls | failed | refusals | tokens | USD |
|---|---|---|---|---|---|
| claude | 2 | 0 | 0 | 7,510 | 0.317 |
