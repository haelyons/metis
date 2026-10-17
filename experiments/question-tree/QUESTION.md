# question-tree

The full pipeline on five fixed root questions (run F) and the runs before it, all on the Claude Code Workflow runtime.
The director's goal is kept out of this repository by design; agents never see it.

Roots (run F, `replay/args_F.json` `fixed_roots`): R1 automated review of ML papers with many scoped open models; R2 what
stops general-purpose robot hands; R3 why earthquakes cannot be predicted days ahead; R4 what stops autoformalizing
published maths into Lean; R5 what limits general-purpose robot manipulation.

| Folder | What | Result |
|---|---|---|
| `replay/` | replay args and outputs (A, B, F), operator prompts, predictions | B: 34 of 64 filed predictions held; F: 23 picks, 13 PASS, 6 REJECT, 4 halted |
| `claude/` | workflow and operator transcripts of every run, outputs (not committed: see below) | run 2: 3 PASS of 20; F as above |

`claude/` is on disk but not in git: committing it was blocked as a possible credential leak (transcripts carry full tool
output). Decide before adding it.
