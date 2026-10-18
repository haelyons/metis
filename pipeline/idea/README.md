# OpenCode runtime

Every model call goes through OpenCode (`opencode-go/*` models), under the isolated config in `ocx/`. Start runs with
`node pipeline/launch.js` from the repository root, which copies the pipeline into the run folder first.

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
