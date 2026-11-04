#!/usr/bin/env bash
# Run COPIES copies of each suite at once, ROUNDS times; report every copy's exit status and FAIL lines.
# Usage: bash tools/stress.sh [copies] [rounds] [suite ...]
set -u
copies=${1:-4}
rounds=${2:-2}
shift 2 2>/dev/null || shift $#
suites=("$@")
(( ${#suites[@]} )) || suites=(tools/test_m5_units_check.js tools/test_m5_reproduce.js)
# Suites that support it keep a failed run's scratch directory (printed as "scratch kept: ...").
export M5_TEST_KEEP_SCRATCH=1
logs=$(mktemp -d "${TMPDIR:-/tmp}/m5-stress.XXXXXX")
echo "logs in $logs"
total=0 failed=0
for suite in "${suites[@]}"; do
  name=$(basename -- "$suite" .js)
  for ((round = 1; round <= rounds; round++)); do
    pids=()
    for ((copy = 1; copy <= copies; copy++)); do
      node "$suite" > "$logs/$name.r$round.c$copy.log" 2>&1 &
      pids+=("$!")
    done
    for ((copy = 1; copy <= copies; copy++)); do
      wait "${pids[copy - 1]}"
      rc=$?
      log="$logs/$name.r$round.c$copy.log"
      total=$((total + 1))
      fails=$(grep -c '^FAIL' "$log")
      oks=$(grep -c '^ok' "$log")
      printf '%s round %d copy %d: rc=%d ok=%d FAIL=%d\n' "$name" "$round" "$copy" "$rc" "$oks" "$fails"
      if (( rc != 0 || fails != 0 )); then
        failed=$((failed + 1))
        grep '^FAIL' "$log" | cut -c1-400
        (( fails )) || tail -n 5 "$log"
      fi
    done
  done
done
echo "summary: $failed of $total runs failed"
(( failed == 0 ))
