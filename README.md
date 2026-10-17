# latent_open

Question-tree research pipeline: generate research cards from root questions, check them, and place them in existing
research or industrial programmes. Two runtimes share one script and one set of prompts and gates.

## Layout

- `qt2/src/` pipeline modules (text, schemas, cost, pick, gates, render, prompts, main, replay); `qt2/build.js`
  concatenates them into `qt2/dist/question_tree_v2.js` and `qt2/dist/replay_v2.js`. `qt2/CONTRACT.md` is the spec,
  `qt2/PROMPTS.md` the generated prompt listing, `qt2/tests/` (`node qt2/tests/run.js`).
- `qt2/replay/` args and outputs of the replay and run-F launches (Claude Workflow runtime).
- `qt2/idea/` OpenCode runtime:
  - `wf.js` runs a dist script with every agent call served by an OpenCode model (card generation, full tree, replay).
  - `frame.js` frame check for one card: existing programmes, checked citations, fit scores.
  - `status.js` progress and spend of either kind of run; `oc.js` one OpenCode call; `schema.js` reply checks.
  - `ocx/opencode/opencode.json` the isolated OpenCode config every call runs under (no MCP, deny by default).
  - `config.json` models, timeouts, run directories, OpenCode Go caps.
- `runs/idea/`, `runs/oc/` full logs of OpenCode runs (see below).

## Deployment links

The files live here; the places that load them are symlinks:
- `/home/hal/stage/qt2` -> `qt2/` (Claude Workflow launches and operator prompts use this path)
- `/home/hal/stage/runs-idea`, `/home/hal/stage/runs-oc` -> `runs/idea`, `runs/oc`
- `~/.config/opencode/commands/idea-status.md` -> `qt2/idea/commands/idea-status.md` (`/idea-status` in OpenCode)

Git stores a symlink inside a repo as a link, not the file it points to, so the real file is always the one in this repo.

## Running on OpenCode

```
cd qt2/idea
node wf.js --args seed-I1.json --name I1-card   # card generation (or any dist script via --script)
node frame.js --card R4:interp:I1               # frame check of a run-F card; --card-file for any card
node status.js --latest [--watch]
```

## What a run records

Each `runs/oc/<name>/<stamp>/` holds `run.json` (script hash, args, models, versions, git commit, totals),
`journal.jsonl` (every agent call: started, result with its value, failed, cached; every log line), `status.json`,
`result.json`, `RESULT.md`, and per call `agents/NNNN-<label>/` with `prompt.md` (exact text sent), `events.jsonl`
(OpenCode event stream), `export.json` (`opencode export`: messages, reasoning, tool calls with input and output,
tokens, cost), `reply.txt` and `meta.json`. Frame runs keep `ledger.jsonl`, `raw/` and `research/notes.md` likewise.
Each call also goes through a local logging proxy (`qt2/idea/httplog.js`), so `http/NNN.request.json` holds the exact
provider request (OpenCode's system prompt, tool definitions, messages; credentials redacted) and `NNN.response.txt`
the streamed reply. Passing a session title skips OpenCode's extra title-generation request.
