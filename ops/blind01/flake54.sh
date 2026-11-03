# Flake rate of test_m5_reproduce.js: worktree (U54-U56) vs main (pre-U54), 4 runs each, two at a time.
for i in 1 2 3 4; do
  for T in /home/hal/dev/interp/metis-wt /home/hal/dev/interp/metis; do
    ( cd $T/dut/pipeline && timeout 1800 node tools/test_m5_reproduce.js > ~/.cache/blind01/flake54.$(basename $T).$i.log 2>&1; echo "$(basename $T) $i rc $? $(tail -1 ~/.cache/blind01/flake54.$(basename $T).$i.log)" ) &
  done; wait
done
grep -h "^FAIL" ~/.cache/blind01/flake54.*.log | cut -d: -f1 | sort | uniq -c
