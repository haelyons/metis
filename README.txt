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

  pipeline/            the tool, the copy we edit
    src/               modules, built by build.js into dist/
    tests/             node pipeline/tests/run.js
    CONTRACT.md        the spec
    idea/              the OpenCode runtime
      loop.js          one idea, one round: expand a one-line seed, card,
                       frame check, three neighbours, screen, better variant
      wf.js            runs a dist script with OpenCode models
      frame.js         which programmes would use the result, and how well
      status.js        progress and spend of any run
    launch.js          starts a run (below)
  experiments/<name>/  one project: QUESTION.md, seed.json, one folder per run
  experiments/_meta/   notes across projects (COMPARE.md, idea memos)

A run folder, experiments/<name>/<stamp>-<kind>/, holds RUN.md (command and
source commit), pipeline/ (a read-only copy of what ran), out/ (every output
and log) and console.log.

REQUIREMENTS
------------
- node 24+.
- OpenCode with an OpenCode Go subscription (opencode-go/* models). Calls run
  under the isolated config in pipeline/idea/ocx: no MCP servers, every
  permission denied unless the agent needs it.
- Optional: Claude Code, for the Workflow runtime (pipeline/dist/*.js).

COLD START
----------
1. Make experiments/<name>/ with QUESTION.md (the question in the asker's
   words, and where it came from) and seed.json:
     {id, title, text, root_question, kind}
   plus root_link, compute_open and sequential when known. A seed whose
   compute_open is "not given" is first expanded by the pipeline's own framer
   and widener.
2. node pipeline/launch.js <name> loop
   (or card, or frame --card-file <card.md> --root "<question>";
   add --dry-run to see the run folder and command first)
3. node pipeline/idea/status.js --latest, or /idea-status inside OpenCode.
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
  /home/hal/stage/qt2                          -> pipeline/
  ~/.config/opencode/commands/idea-status.md   -> pipeline/idea/commands/

PRIVATE
-------
Run logs carry full tool output, local paths and fetched pages.
