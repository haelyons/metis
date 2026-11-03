set -u; B=~/.cache/blind01
# s19 revises the G1/G3/G6 draft (s18's finding + two operator review points); s20, an independent session, audits it.
bash $B/sci.sh 02 s19 > $B/sci_s19.out 2>&1
python3 $B/sci_owner_check.py 02 s19 >> $B/sci_s19.out 2>&1
grep -q '"draft_written": "yes"' $B/sci_s19.out && grep -q '^VALID' $B/sci_s19.out || { echo S19_NOT_READY; exit 1; }
bash $B/sci.sh 02 s20 > $B/sci_s20.out 2>&1
python3 $B/sci_audit_check.py 02 s20 s13 >> $B/sci_s20.out 2>&1
echo CHAIN_DONE
