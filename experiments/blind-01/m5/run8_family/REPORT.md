# Run8 agent-family check

Reviewed at **2026-10-31T23:36:46Z**. Scope: calls recorded so far, without waiting for run8. Latest workflow status: `updated=2026-10-31T22:53:16.675Z`, `stage=reproduce`, `done=false`. Six calls started; all six returned results. Findings concern this recorded interval, not the eventual run outcome.

**1. Codex usage, quota or rate-limit error: no.**

No such provider error line was found, so there is no error line to quote. Every call has `errors: []`, `kind: "none"`, one attempt and a successful result. All six raw Codex logs contain a completed turn with null error; none contains an app-server error notification, an error response or a failed turn.

The logs do contain 59 routine `account/rateLimits/updated` notifications. These are usage telemetry, not errors. First notification reports 3% primary-window usage and 97% secondary-window usage (`0001-intake/codex-1.jsonl:36`, 21:59:32.820Z). Last reports 16% and 99%, with `rateLimitReachedType:null` and `spendControlReached:null` (`0006-anchors-repair/codex-1.jsonl:195`, 22:53:16.633Z). The latter call subsequently completed successfully. High reported usage does not establish exhaustion.

Additional provider-error searches across 182 text records/logs under `run8/agent/` and 60 under `run8/control/` found no matching error lines after excluding routine limit notifications. Control searches were restricted to provider-error patterns; no control experiment content was used.

**2. Initial harness, setup repairs and anchors repairs: all Codex.**

Every call used workflow model **`codex/default@medium`**, served by family **`codex`**. Raw app-server `thread/started` metadata identifies actual provider **`openai`**, model **`gpt-6.1-sol`**, reasoning effort **`medium`**, for every call (`codex-1.jsonl:4` in each call directory). No fallback ran.

All timestamps below are UTC on 2026-10-31. Start/result timestamps come from `run8/agent/wf/journal.jsonl`; directory names are under `run8/agent/wf/agents/`.

| Call directory / label | Started | Result recorded | Family | Journal lines | Raw completed-turn line |
| --- | --- | --- | --- | --- | --- |
| `0001-intake` | 21:59:28.329Z | 22:01:45.112Z | codex | 2–3 | 237 |
| `0002-harness` | 22:02:03.633Z | 22:05:40.017Z | codex | 6–7 | 408 |
| `0003-harness-repair` — setup repair 1 | 22:09:06.002Z | 22:09:44.616Z | codex | 8–9 | 173 |
| `0004-harness-repair` — setup repair 2 | 22:15:08.216Z | 22:15:41.509Z | codex | 10–11 | 161 |
| `0005-anchors-repair` — anchors repair 1 | 22:21:14.705Z | 22:23:03.318Z | codex | 12–13 | 238 |
| `0006-anchors-repair` — anchors repair 2 | 22:52:31.376Z | 22:53:16.675Z | codex | 14–15 | 198 |

Each call's `meta.json` independently records `family: "codex"`, `model: "codex/default@medium"`, `attempts: 1`, `errors: []`, `kind: "none"`. Each journal result records `substituted: false`. Workflow `status.json` records `by: "codex/default@medium"` and `state: "ok"` for every call, `substitutions: 0`, and only Codex in `by_family` (six calls, zero failed, zero refusals). No understudy directories or additional attempt logs exist in the inspected call records.

Calls 0003 and 0004 are setup repairs despite their generic `harness-repair` label: each `prompt.md:1` begins `setup.sh failed (rc 1)` and restricts editing to `setup.sh`, identifying repair attempts 1 and 2 respectively. Calls 0005 and 0006 explicitly repair anchors.

**3. Call lost, or repair/step ended because of provider failure: no recorded occurrence.**

All six journal `started` events have matching nonempty `result` events. Intake returned an object; the other five calls returned nonempty text. Every `reply.txt` is nonempty. There are no `failed` or `understudy` journal events. Raw completed-turn entries all report `"status":"completed","error":null`.

Recorded repair triggers concern scripts, not agent providers:

- Setup repairs 0003 and 0004: `setup.sh failed (rc 1)` (`prompt.md:1` in each directory). Their replies diagnose build-tool compatibility and NetworkX/NumPy compatibility respectively.
- Anchors repair 0005: `run_anchors.sh failed (rc 1)` (`prompt.md:1`); its reply describes legacy MPI exit status and output validation.
- Anchors repair 0006: `run_anchors.sh failed (rc 124, output gate: timeout)` (`prompt.md:1`), with 1,200-second budget and recorded 1,751-second elapsed time (`prompt.md:2`). Its reply describes a bounded abort while preserving fixed workload scale. This is a completed authoring result, not a missing result or provider failure.

Workflow remains unfinished in the inspected records. Final step/run outcome is **unknown**; this check makes no claim that reproduction or anchors ultimately passed.

**4. Other course change caused by provider failure: no recorded occurrence.**

No provider failure, fallback, substituted author, lost response or provider-induced retry appears. In particular, Opus was configured but never served these calls. The latest repair did change script behavior: its reply says it added a bounded abort because the fixed workload lacked evidence of fitting the runtime budget (`0006-anchors-repair/reply.txt:2–5`). Recorded cause is workload timing, not Codex availability.

Whether the owner's outage/reset occurred before, between or after these calls is **unknown** from these records. There were no recorded agent calls between 22:23:03.318Z and 22:52:31.376Z, or after 22:53:16.675Z through this inspection. This check cannot establish account availability during intervals without calls.

**How family and fallback were established.**

Policy alone was not treated as evidence of execution. `dut/pipeline/m5/SCHEMAS.md:12–13` specifies Codex first, `claude/opus` first understudy and OpenCode second for authoring calls. The run's `run.json` and every journal `started` event agree: chain is `["claude/opus", "opencode-go/mimo-v2.6-pro"]`, mode `fallback`.

Implementation confirms record meaning:

- `dut/pipeline/idea/understudy.js:34` maps model prefixes to families; `claude/opus` belongs to Claude family (the requested status enum calls this `opus`). Lines 128–143 classify errors and decide handover; successful kind `none` never hands over.
- `dut/pipeline/idea/wf.js:167` writes per-model `meta.json` with family, model, attempts, errors and kind. Lines 239–253 put fallback records in `understudy/` or `understudy-N/` and journal the source/target models and failure. Lines 256–262 record actual producer in status `by`, journal result `model`, and substitution flag, returning null on errors.
- `dut/pipeline/idea/codex_cli.js:175–181` handles provider error and turn-completion notifications. Raw events were checked as well as summaries, including retryable errors that might not survive in final `errors`.

Only `run8_family/REPORT.md` and `run8_family/status.json` were authored by this check. No workload, box contact, network fetch, commit or push was performed. Existing run8 files and existing audit-launcher logs were left untouched.
