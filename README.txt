metis — turns a question or a one-line idea into checked research cards
=======================================================================

Named for the Titaness of counsel whose story sits under Athena's birth: the
cards sit under the work that follows them.

WHAT THIS IS
------------
A question-tree pipeline. A root question branches into options; an option
becomes a card: a concrete experiment with a quantity that more GPU time buys,
a priced plan, a published number to reproduce first, and a prediction for
either outcome. Fresh model contexts then check every cited claim against its
page, score the card, and name the existing research or industrial programmes
its result would feed. A loop proposes close variants and keeps a better one.

  dut/                 the designers under test
  dut/pipeline/        this tool, the copy we edit
    src/               modules, built by build.js into dist/
    tests/             node dut/pipeline/tests/run.js
    CONTRACT.md        the spec
    idea/              the OpenCode runtime
      loop.js          one idea, one round: expand a one-line seed, card,
                       frame check, three neighbours, screen, better variant.
                       The framer's verdict routes the expansion (COMPUTE-BOUND
                       deepens, NOT COMPUTE-BOUND widens and asks each option
                       for a narrowing); src/screen.js gates every option before
                       ranking (bears on the root question, open compute quantity,
                       narrowing stated when not compute-bound) and ranks the rest
                       by the main pick rule; nothing passing is a valid end
      wf.js            runs a dist script (or latent_skeptic's pipeline.js and
                       triage_workflow.js) with two model families: OpenCode Go
                       models (oc.js) and Claude models headless (claude_cli.js),
                       each the other's understudy (understudy.js): a call whose
                       primary fails on a named kind (timeout, exit, runner,
                       nojson, schema) is retried on the other family; a refusal
                       halts unless the run says --on-refusal understudy. Modes
                       fallback | shadow (both run, compared in shadow.jsonl) |
                       swap | primary-only; --family picks the primary; routes
                       and profiles in config.json "understudy"; UNDERSTUDY.md
                       per run (understudy_report.js); tools/e2e_wf.js is the
                       stubbed harness. Nested workflow() runs one level deep.
      frame.js         which programmes would use the result, and how well
      status.js        progress and spend of any run
    launch.js          starts a run (below)
  dut/latent_skeptic/  submodule at ff9a63c: the pipeline that designs, gates,
                       runs and writes up one GPU experiment (the coolant pilot ran on it)
  reframe/             a separate stage: from a problem to investigable reframings
  experiments/<name>/  one project: QUESTION.md, seed.json, one folder per run
  experiments/_meta/   notes across projects (COMPARE.md, idea memos)

A run folder, experiments/<name>/<stamp>-<kind>/, holds RUN.md (command and
source commit), pipeline/ (a read-only copy of what ran), out/ (every output
and log) and console.log.

REQUIREMENTS
------------
- node 24+.
- OpenCode with an OpenCode Go subscription (opencode-go/* models). Calls run
  under the isolated config in dut/pipeline/idea/ocx: no MCP servers, every
  permission denied unless the agent needs it.
- Optional: Claude Code, for the Workflow runtime (dut/pipeline/dist/*.js) and
  for the Claude family in wf.js (claude -p, logged in; calls run --restricted
  --strict-mcp-config so no hook, plugin or MCP server reaches them; models
  sonnet, opus, haiku only).
- dut/pipeline/measure/ONBOX_CONTRACT.md seeds the build agent of a measure
  run (copied into <measure dir>/frozen/ by experiments/blind-01/measure.sh
  prepare; launch.js <exp> stage runs one latent_skeptic stage on wf.js).
- After cloning: git submodule update --init (dut/latent_skeptic).

COLD START
----------
1. Make experiments/<name>/ with QUESTION.md (the question in the asker's
   words, and where it came from) and seed.json:
     {id, title, text, root_question, kind}
   plus root_link, compute_open and sequential when known. A seed whose
   compute_open is "not given" is first expanded by the pipeline's own framer
   and widener.
2. node dut/pipeline/launch.js <name> loop
   (or card, or frame --card-file <card.md> --root "<question>";
   add --dry-run to see the run folder and command first)
   A PASS card whose cost rests on a GUESS or PROXY is calibration_required
   (result.json .calibration). node dut/pipeline/launch.js <name> measure
   --card <card run dir> compiles that record into a latent_skeptic measure
   folder (QUESTION.md, SEALED_PREDICTIONS.md, out/triage_args.json); the
   measure run then resolves each input on a rented box and writes a ledger
   row (experiments/_meta/LEDGER.jsonl, kind card_number_resolved).
3. node dut/pipeline/idea/status.js --latest, or /idea-status inside OpenCode.
4. Read out/loop.md, then each round's card/RESULT.md and frame/frame.md.

WHAT A RUN RECORDS
------------------
Per model call: the exact prompt, OpenCode's event stream, the full session
export (reasoning, tool calls with input and output, tokens, cost), the exact
provider request through a local logging proxy (system prompt, tools,
messages; credentials and workspace ids redacted), the reply and its checks.
Per run: a journal of every call with its returned value, the result, and the
spend by model.

LOCAL LINKS
-----------
The files live here; what loads them is a symlink:
  /home/hal/stage/qt2                          -> dut/pipeline/
  ~/.config/opencode/commands/idea-status.md   -> dut/pipeline/idea/commands/

PRIVATE
-------
Run logs carry full tool output, local paths and fetched pages.
