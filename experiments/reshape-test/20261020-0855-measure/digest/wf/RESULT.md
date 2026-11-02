# Digest run

Status: done, all checks pass.
Run digested: experiments/reshape-test/20261020-0855-measure
Digest directory: experiments/reshape-test/20261020-0855-measure/digest
Command, from /home/hal/dev/interp/metis: `node /home/hal/dev/interp/metis/dut/pipeline/idea/wf.js --config dut/digest/wf_config.json --script dut/digest/pipeline.js --args /tmp/claude-1000/-home-hal-dev-local/657d7e99-4b9b-4e49-a361-8a4cfa8f0b42/scratchpad/digest-m2.json --out experiments/reshape-test/20261020-0855-measure/digest/wf --mode fallback --on-refusal halt`
Pipeline commit: 3b070f79676badf647eb82aeabe890d0554e7a01 (working tree dirty); pipeline.js sha256 e550dedad578933d486140cc70bb8ff6caa6511a6e09b5839794251bd93bd8c0
Wall time: 655.0 s (2026-11-02T14:54:21.515Z to 2026-11-02T15:05:16.491Z)
Spend, as the runners report it (Codex reports tokens, not dollars): USD 0.000, 838342 tokens
Calls:
  0001 reader: primary codex/default@high, answered by codex/default@high, understudies claude/opus, opencode-go/mimo-v2.6-pro, ok, 1 attempt(s), 558032 tokens, 234 s, USD 0.000
  0002 verify: primary codex/default@high, answered by codex/default@high, understudies claude/opus, opencode-go/mimo-v2.6-pro, ok, 1 attempt(s), 122142 tokens, 208 s, USD 0.000
  0003 writer: primary codex/default@high, answered by codex/default@high, understudies claude/opus, opencode-go/mimo-v2.6-pro, ok, 1 attempt(s), 19378 tokens, 60 s, USD 0.000
  0004 notebook: primary codex/default@medium, answered by codex/default@medium, understudies claude/sonnet, opencode-go/mimo-v2.6-pro, ok, 1 attempt(s), 138790 tokens, 148 s, USD 0.000
Verify: 48 cited sentences, 43 supported, 0 contradicted, 5 not addressed
Notebook export: not needed
Check: pass; details in CHECK.json
Every prompt and reply: wf/agents/; every call: wf/journal.jsonl.
