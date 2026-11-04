B = "/home/hal/.cache/blind01"
lines = open(f"{B}/retry57.sh").read().split("\n")
start = next(i for i, l in enumerate(lines) if l.startswith('cd $W && [ -z "$(git status --porcelain -- dut/pipeline | grep -v run_failures_only.js)" ]'))
dfi = next(i for i, l in enumerate(lines) if l.startswith("df(){"))
st = next(i for i, l in enumerate(lines) if l.startswith("stress(){"))
u56 = next(i for i, l in enumerate(lines) if l.startswith("ci u56b;"))
head = lines[:start]
head[1:1] = ["# retry57b (2026-11-03): resume of retry57 after STOP_AT_U59. The contract is committed (db332caf); U59's first",
             "# round is uncommitted in the worktree; u59b fixes the real race (fixture walks of the box tree during a job).",
             "# Gate: 4 copies of each affected suite at once, twice (the load that reproduced the failure), then every suite."]
stress4 = ("stress(){ cd $P; f=0; for i in 1 2; do for t in tools/test_m5_units_check.js tools/test_m5_reproduce.js; do "
           "for j in a b c d; do ( r=$(timeout 2400 node $t 2>&1 | tail -1); echo \"stress $i$j $t: $r\"; "
           "echo \"$r\" | grep -qE 'all ([0-9]+ )?checks passed' ) & done; for j in a b c d; do wait -n || f=$((f+1)); done; done; done; "
           "uptime; echo \"STRESS_FAILING=$f\"; return $f; }")
body = [lines[dfi], stress4,
        'df u59b; cd $W && [ -z "$(git status --porcelain -- dut/pipeline | grep -v run_failures_only.js | grep -v \' dut/pipeline/tools/\')" ] || { echo "U59_TOUCHED_NON_TOOLS"; exit 1; }',
        'echo "== stress after u59b"; stress && { echo "== suites after u59b"; suites; } && lc "tools U59: fake-box fixtures no longer race the job they started (directory walks skip entries that vanish; longer completion waits; test fixtures only, Opus; reproduce and units-check suites intermittently failed on main and units)" || { echo STOP_AT_U59; exit 1; }']
out = head + body + lines[u56:]
open(f"{B}/retry57b.sh", "w").write("\n".join(out))
print("ok", len(out))
