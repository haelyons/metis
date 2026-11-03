set -u; B=~/.cache/blind01
# s23 revises the G1/G3/G6 draft a third time (s22's findings); s24, an independent session, audits it.
bash $B/sci.sh 02 s23 > $B/sci_s23.out 2>&1
python3 $B/sci_owner_check.py 02 s23 >> $B/sci_s23.out 2>&1
grep -q '"draft_written": "yes"' $B/sci_s23.out && grep -q '^VALID' $B/sci_s23.out || { echo S19_NOT_READY; exit 1; }
bash $B/sci.sh 02 s24 > $B/sci_s24.out 2>&1
python3 $B/sci_audit_check.py 02 s24 s13 >> $B/sci_s24.out 2>&1
echo CHAIN_DONE
