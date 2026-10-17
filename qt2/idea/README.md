# Frame check for one card or idea

Asks which existing research or industrial programme a card's result would feed, checks the cited practice, and
scores the fit. Every model call goes through OpenCode (`opencode-go/*` models), not Claude.

```
node frame.js --card R4:interp:I1                      # a card from run F (runs-v4/seed-1/RESULT.md)
node frame.js --card-file my-idea.md --root "question" # any card or idea written as text
node status.js --latest [--watch]                      # progress, cost, failed calls
```

Stages: researcher (`research` model, web) finds one to three programmes and cites their practice; two dramaturgs on
different models check every claim against its page; three critics on different models score `fit`, `change` and
`new` (1-5) per grounded programme; the script takes medians. Output in `runs_dir/<card>/<stamp>/`: `frame.md`
(read this), `frame.json`, `ledger.jsonl` (every call: model, tokens, cost, time), `status.json`, `raw/` (OpenCode
event streams), `research/notes.md`.

Models and timeouts: `config.json`, or `--research-model`, `--dramaturgs m1,m2`, `--critics m1,m2,m3`.

## Isolation

Calls run with `XDG_CONFIG_HOME=./ocx`, so OpenCode loads `ocx/opencode/opencode.json` and none of the global config:
no MCP servers, every permission denied by default. Agents: `qt-bare` (no tools), `qt-web` (web fetch and search
only), `qt-research` (web, plus read and write inside its working directory). Check with
`XDG_CONFIG_HOME=$PWD/ocx opencode debug agent qt-web`.

## Running it

- From a Claude session: start it in tmux (`tmux new -d -s idea-frame "node frame.js --card …"`), then watch with
  `node status.js --latest`. Claude spends tokens only on launching and reading `frame.md`.
- From `claude-alt` or a terminal: the same commands.
- From OpenCode: `/idea-status` (global command) shows progress and summarises a finished run.
