# Understudy report: args

Primary family codex, mode fallback, on refusal halt, hands over on timeout, exit, runner, nojson, schema, declined; profile latent_skeptic; routes 2.

| # | label | role | tier | primary | kind | understudy | used? | by | ms | USD |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | intake | ls-writer | main | codex/default@medium | none | opencode-go/mimo-v2.6-pro | - | codex/default@medium | 132 s | 0.000 |
| 2 | harness | ls-writer | main | codex/default@medium | none | opencode-go/mimo-v2.6-pro | - | codex/default@medium | 213 s | 0.000 |
| 3 | seal | ls-writer | main | codex/default@medium | none | opencode-go/mimo-v2.6-pro | - | codex/default@medium | 123 s | 0.000 |
| 4 | propose | ls-writer | main | codex/default@medium | none | opencode-go/mimo-v2.6-pro | - | codex/default@medium | 43 s | 0.000 |
| 5 | skeptic-1 | qt-bare | cheap | codex/default@low | none | opencode-go/glm-5.3-flash | - | codex/default@low | 4 s | 0.000 |
| 6 | skeptic-2 | qt-bare | cheap | codex/default@low | none | opencode-go/glm-5.3-flash | - | codex/default@low | 5 s | 0.000 |
| 7 | skeptic-3 | qt-bare | cheap | codex/default@low | none | opencode-go/glm-5.3-flash | - | codex/default@low | 4 s | 0.000 |
| 8 | skeptic-4 | qt-bare | cheap | claude/sonnet | none | codex/default@low | - | claude/sonnet | 5 s | 0.035 |
| 9 | skeptic-5 | qt-bare | cheap | claude/sonnet | none | codex/default@low | - | claude/sonnet | 2 s | 0.032 |
| 10 | tests | ls-writer | main | codex/default@medium | none | opencode-go/mimo-v2.6-pro | - | codex/default@medium | 104 s | 0.000 |
| 11 | implement | ls-writer | main | codex/default@medium | none | opencode-go/mimo-v2.6-pro | - | codex/default@medium | 331 s | 0.000 |
| 12 | review | qt-bare | main | claude/sonnet | none | codex/default@medium | - | claude/sonnet | 11 s | 0.156 |

Calls 12: 12 returned (0 by the understudy), 0 failed, 0 cached; refusals 0; primary failure kinds {}.

## By role

| role | calls | substituted | failed |
|---|---|---|---|
| ls-writer | 6 | 0 | 0 |
| qt-bare | 6 | 0 | 0 |

## By family

| family | calls | failed | refusals | tokens | USD |
|---|---|---|---|---|---|
| codex | 9 | 0 | 0 | 1,564,203 | 0.000 |
| claude | 3 | 0 | 0 | 1,451 | 0.223 |
