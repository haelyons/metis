# OpenCode runtime

Every model call goes through OpenCode (`opencode-go/*` models), under the isolated config in `ocx/`. Start runs with
`node dut/pipeline/launch.js` from the repository root, which copies the pipeline into the run folder first.

- `loop.js` one idea, one round: seed expansion when the seed is one line (FRAMER, WIDENER, screen), card (`wf.js`),
  frame check (`frame.js`), three neighbours, option-critic screen, and card plus frame check for a variant that scores
  higher. Stops if the first card is not judged.
- `wf.js` runs a dist script (card generation, full tree, replay) with OpenCode models; `config.json` `label_rules` run
  the card critic as a three-model panel and send the second dramaturg to another family.
- `frame.js` frame check: researcher, two checkers on different families, three critics; `frame_rules.js` caps scores
  the checked record contradicts (inactive programme: change 1; contradicted "not done": new 3) and flags a step put
  in the card's terms.
- `status.js` progress and spend; `httplog.js` per-call logging proxy; `panel.js` critic-panel merge; `oc.js` one call.
- `test/stub-oc.js` smoke test with no model calls:
  `NODE_OPTIONS="--require $PWD/test/stub-oc.js" node loop.js --seed <seed.json> --dir <scratch>`, and for the frame
  check `... node frame.js --card-file <card.md> --root "<q>" --out <scratch>` (the loop stops before it on a stub card).

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

## Understudies (2026-10-21)

Every `agent()` call wf.js serves has a primary model and an understudy from the other family. Families: `opencode`
(oc.js, the isolated config in ./ocx) and `claude` (claude_cli.js: `claude -p` on stdin, `--restricted
--strict-mcp-config` so the user's hooks, plugins and MCP servers never reach the call, the role's tool list from
understudy.js, the role's prompt from ocx/opencode.json as an appended system prompt; models sonnet, opus, haiku only).
A pinned Workflow model (opus / sonnet / haiku) maps to a tier (strong / main / cheap) and each family names one model
per tier, so a script asks for the same tier whichever family answers.

Policy (understudy.js, config.json `understudy`, CLI overrides): `--family opencode|claude` picks the primary;
`--mode fallback` (understudy only on a primary failure of a kind in `retry_on`), `shadow` (both run from the start,
outcomes compared in shadow.jsonl and UNDERSTUDY.md; the primary's value is used), `swap`, `primary-only`;
`--on-refusal halt|understudy` (a refusal is its own kind and never hands over unless the run says so);
`routes` (per label regex or role: primary family, models, mode) roll a family out one role at a time; `profiles`
(`--profile metis|latent_skeptic`) decide which role a call without agentType plays. Every call's folder carries
`meta.json` with the kind of its failure; `journal.jsonl` carries `understudy` and `shadow` rows; `run.json` totals by
model and family.

Roles for latent_skeptic (triage-reader, triage-runner, triage-author from dut/latent_skeptic/agents/*.md; ls-general,
ls-builder, ls-writer) are written into ocx/opencode.json by `node tools/ocx_roles.js`. `workflow({scriptPath})` runs
one level deep. `node tools/e2e_wf.js` runs the policy on stubs for both families (no model, no network);
`node understudy.js --selftest` checks the pure functions; `node understudy_report.js <run dir>` prints the report.

Running a latent_skeptic stage: `node dut/pipeline/launch.js <exp> stage --measure <measure dir> --stage design|build|post
[--family …] [--mode …] [--on-refusal …]` (args from the measure folder's out/*_args.json; the return value is copied
to the file measure.sh expects).
