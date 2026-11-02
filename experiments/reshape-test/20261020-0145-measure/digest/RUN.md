# Digest run

Status: done, all checks pass.
Run digested: experiments/reshape-test/20261020-0145-measure
Digest directory: experiments/reshape-test/20261020-0145-measure/digest
Command, from /home/hal/dev/interp/metis: `node /home/hal/dev/interp/metis/dut/pipeline/idea/wf.js --config dut/digest/wf_config.json --script dut/digest/pipeline.js --args /tmp/claude-1000/-home-hal-dev-local/657d7e99-4b9b-4e49-a361-8a4cfa8f0b42/scratchpad/digest-m1.json --out experiments/reshape-test/20261020-0145-measure/digest/wf --mode fallback --on-refusal halt`
Pipeline commit: 3b070f79676badf647eb82aeabe890d0554e7a01 (working tree dirty); pipeline.js sha256 e550dedad578933d486140cc70bb8ff6caa6511a6e09b5839794251bd93bd8c0
Wall time: 760.3 s (2026-11-02T14:41:15.495Z to 2026-11-02T14:53:55.834Z)
Spend, as the runners report it (Codex reports tokens, not dollars): USD 0.000, 646568 tokens
Calls:
  0001 reader: primary codex/default@high, answered by codex/default@high, understudies claude/opus, opencode-go/mimo-v2.6-pro, ok, 1 attempt(s), 353031 tokens, 318 s, USD 0.000
  0002 verify: primary codex/default@high, answered by codex/default@high, understudies claude/opus, opencode-go/mimo-v2.6-pro, ok, 1 attempt(s), 125355 tokens, 197 s, USD 0.000
  0003 writer: primary codex/default@high, answered by codex/default@high, understudies claude/opus, opencode-go/mimo-v2.6-pro, ok, 1 attempt(s), 19979 tokens, 81 s, USD 0.000
  0004 notebook: primary codex/default@medium, answered by codex/default@medium, understudies claude/sonnet, opencode-go/mimo-v2.6-pro, ok, 1 attempt(s), 148203 tokens, 160 s, USD 0.000
Verify: 50 cited sentences, 37 supported, 0 contradicted, 13 not addressed
Notebook export: not needed
Check: pass; details in CHECK.json
Every prompt and reply: wf/agents/; every call: wf/journal.jsonl.
