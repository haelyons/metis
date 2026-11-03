set -u
# One full rerun of every suite after retry54b (known pre-existing reproduce-suite flake, flake54: main fails 1/4 the same way).
# Same gate as retry54b (same regexes, all suites); commits only when all pass. Both runs are reported.
eval "$(sed -n '/^suites(){/p;/^lc(){/,/^}/p' ~/.cache/blind01/retry54b.sh)"
P=/home/hal/dev/interp/metis-wt/dut/pipeline
echo "== suites rerun after u54fix"; suites && lc "m5 U54-U56: card calibration run, tree records, write-back and re-judging (gap G2; Opus understudy, separate tests; fixes after Codex review)

Suites: first run after the fix round FAILING=1 (test_m5_reproduce.js, concurrency receipt missing in ceiling-repairs: the
pre-existing fixture race also seen on main before U54, 1 of 4 runs); this full rerun passed every suite."
cd /home/hal/dev/interp/metis-wt && git status --short | grep -v "^?? experiments/"
echo CHAIN_DONE
