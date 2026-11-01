# Understudy report: args

Primary family codex, mode fallback, on refusal halt, hands over on timeout, exit, runner, nojson, schema, declined; profile latent_skeptic; routes 3.

| # | label | role | tier | primary | kind | understudy | used? | by | ms | USD |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | intake | ls-writer | main | codex/default@medium | runner | claude/opus (ok) | yes | claude/opus | 2 s | 0.000 |
| 2 | harness | ls-writer | main | codex/default@medium | runner | claude/opus (ok) | yes | claude/opus | 1 s | 0.000 |
| 3 | harness-repair | ls-writer | main | codex/default@medium | runner | claude/opus (ok) | yes | claude/opus | 1 s | 0.000 |
| 4 | harness-repair | ls-writer | main | codex/default@medium | runner | claude/opus (ok) | yes | claude/opus | 1 s | 0.000 |
| 5 | harness-repair | ls-writer | main | codex/default@medium | runner | claude/opus (ok) | yes | claude/opus | 1 s | 0.000 |
| 6 | anchors-repair | ls-writer | main | codex/default@medium | none | claude/opus | - | codex/default@medium | 148 s | 0.000 |
| 7 | anchors-repair | ls-writer | main | codex/default@medium | none | claude/opus | - | codex/default@medium | 76 s | 0.000 |

Calls 7: 7 returned (5 by the understudy), 0 failed, 0 cached; refusals 0; primary failure kinds {"runner":5}.

## By role

| role | calls | substituted | failed |
|---|---|---|---|
| ls-writer | 7 | 5 | 0 |

## By family

| family | calls | failed | refusals | tokens | USD |
|---|---|---|---|---|---|
| codex | 7 | 5 | 0 | 1,374,610 | 0.000 |
| claude | 5 | 0 | 0 | 167,046 | 6.593 |
