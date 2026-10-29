# Understudy report: args

Primary family codex, mode fallback, on refusal halt, hands over on timeout, exit, runner, nojson, schema, declined; profile latent_skeptic; routes 2.

| # | label | role | tier | primary | kind | understudy | used? | by | ms | USD |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | intake | ls-writer | main | codex/default@medium | none | opencode-go/mimo-v2.6-pro | - | codex/default@medium | 102 s | 0.000 |
| 2 | harness | ls-writer | main | codex/default@medium | none | opencode-go/mimo-v2.6-pro | - | codex/default@medium | 145 s | 0.000 |
| 3 | seal | ls-writer | main | codex/default@medium | none | opencode-go/mimo-v2.6-pro | - | codex/default@medium | 105 s | 0.000 |
| 4 | propose | ls-writer | main | codex/default@medium | none | opencode-go/mimo-v2.6-pro | - | codex/default@medium | 33 s | 0.000 |
| 5 | skeptic-1 | qt-bare | cheap | codex/default@low | none | opencode-go/glm-5.3-flash | - | codex/default@low | 4 s | 0.000 |
| 6 | skeptic-2 | qt-bare | cheap | codex/default@low | none | opencode-go/glm-5.3-flash | - | codex/default@low | 4 s | 0.000 |
| 7 | skeptic-3 | qt-bare | cheap | codex/default@low | none | opencode-go/glm-5.3-flash | - | codex/default@low | 4 s | 0.000 |
| 8 | skeptic-4 | qt-bare | cheap | claude/sonnet | none | codex/default@low | - | claude/sonnet | 3 s | 0.034 |
| 9 | skeptic-5 | qt-bare | cheap | claude/sonnet | none | codex/default@low | - | claude/sonnet | 2 s | 0.031 |
| 10 | adapter-repair | ls-writer | main | codex/default@medium | none | opencode-go/mimo-v2.6-pro | - | codex/default@medium | 107 s | 0.000 |
| 11 | tests | ls-writer | main | codex/default@medium | none | opencode-go/mimo-v2.6-pro | - | codex/default@medium | 103 s | 0.000 |
| 12 | implement | ls-writer | main | codex/default@medium | none | opencode-go/mimo-v2.6-pro | - | codex/default@medium | 267 s | 0.000 |
| 13 | implement | ls-writer | main | codex/default@medium | none | opencode-go/mimo-v2.6-pro | - | codex/default@medium | 70 s | 0.000 |

Calls 13: 13 returned (0 by the understudy), 0 failed, 0 cached; refusals 0; primary failure kinds {}.

## By role

| role | calls | substituted | failed |
|---|---|---|---|
| ls-writer | 8 | 0 | 0 |
| qt-bare | 5 | 0 | 0 |

## By family

| family | calls | failed | refusals | tokens | USD |
|---|---|---|---|---|---|
| codex | 11 | 0 | 0 | 1,922,276 | 0.000 |
| claude | 2 | 0 | 0 | 44 | 0.065 |
