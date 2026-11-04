#!/usr/bin/env bash
# Print the FAIL lines (with context) and the end of a stress.sh log: bash tools/stress_show.sh <log> [context]
set -u
grep -n -A "${2:-15}" -e '^FAIL' -e 'TypeError' -e '    at ' "$1" | cut -c1-600
echo '--- tail'
tail -n 20 "$1" | cut -c1-600
