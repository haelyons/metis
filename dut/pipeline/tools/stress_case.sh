#!/usr/bin/env bash
# Dump a kept case directory's box receipts and profile-stage logs: bash tools/stress_case.sh <scratch>/<case>
set -u
case_dir=$1
for receipt in "$case_dir"/control/receipts/*.json; do
  [[ -f $receipt ]] || continue
  echo "=== $(basename -- "$receipt")"
  cut -c1-800 "$receipt"
done
for log in "$case_dir"/agent/results/profile/*.log "$case_dir"/box/m5-*/*profile*.log "$case_dir"/box/m5-*/*profile*.rc; do
  [[ -f $log ]] || continue
  echo "=== $log"
  tail -n 25 "$log" | cut -c1-400
done
[[ -f $case_dir/box-calls.log ]] && { echo '=== box-calls.log'; tail -n 20 "$case_dir/box-calls.log"; }
[[ -f $case_dir/stderr.log ]] && { echo '=== stderr.log'; tail -n 20 "$case_dir/stderr.log" | cut -c1-400; }
for record in "$case_dir"/control/stages/profile.json "$case_dir"/agent/profile-packet.json; do
  [[ -f $record ]] && { echo "=== $record"; cut -c1-1500 "$record"; }
done
echo '=== profile results tree'
find "$case_dir/agent/results/profile" -printf '%y %s %P\n' 2>&1 | sort | head -n 60
echo '=== remote profile tree'
find "$case_dir"/box/m5-* -path '*profile*' -printf '%y %s %P\n' 2>&1 | sort | head -n 60
echo '=== remote profile_nsys.sh head'
for script in "$case_dir"/box/m5-*/profiler/profile_nsys.sh "$case_dir"/box/m5-*/*/profile_nsys.sh; do
  [[ -f $script ]] && { echo "--- $script"; head -n 6 "$script" | cut -c1-200; }
done
exit 0
