# latent_open

Where could massive parallel compute change a scientific answer? A question-tree pipeline turns a root question or a
one-line idea into research cards: a plan with a costed compute axis, a cheap check to run first, and predictions for
either outcome. Fresh model contexts then check every cited claim against its page, score the card, and place it in
the existing research or industrial programmes its result would feed.

## Layout

- `pipeline/` the tool, the copy we tinker on. `src/` modules, built by `build.js` into `dist/`; `tests/`
  (`node pipeline/tests/run.js`); `CONTRACT.md` the spec; `idea/` the OpenCode runtime (`wf.js` runs a dist script with
  OpenCode models, `frame.js` the frame check, `loop.js` one idea's improvement round, `status.js` progress).
- `experiments/<name>/` one latent project each: `QUESTION.md`, `seed.json`, and one folder per run.
- `experiments/<name>/<stamp>-<kind>/` a run: `RUN.md` (command, source commit), `pipeline/` (read-only copy of what
  ran), `out/` (every output and log), `console.log`.
- `experiments/_meta/` notes across experiments (`COMPARE.md`: the two runtimes side by side).

## Cold start

1. Make `experiments/<name>/` with `QUESTION.md` (the question in the asker's words, and where it came from) and
   `seed.json`: `{id, title, text, root_question, kind}`, plus `root_link`, `compute_open`, `sequential` when known.
   A seed whose `compute_open` is "not given" is expanded first by the pipeline's framer and widener.
2. `node pipeline/launch.js <name> loop` (or `card`, or `frame --card-file <card.md> --root "<question>"`).
   Add `--dry-run` to see the run folder and command first.
3. Watch with `node pipeline/idea/status.js --latest`, or `/idea-status` in OpenCode.
4. Read `out/loop.md`, then each round's `card/RESULT.md` and `frame/frame.md`.

## What a run records

Per model call: the exact prompt, OpenCode's event stream, the full session export (reasoning, tool calls with input
and output, tokens, cost), the exact provider request through a local logging proxy (system prompt, tools, messages;
credentials redacted), the reply and its checks. Per run: the journal of every call with its returned value, the
result, and the spend by model.

## Deployment links

The files live here; what loads them is a symlink: `/home/hal/stage/qt2` -> `pipeline/` (Claude Workflow launches), and
`~/.config/opencode/commands/idea-status.md` -> `pipeline/idea/commands/idea-status.md`.

## Private

Run logs carry full tool output, local paths and fetched pages. Keep this repository private.
