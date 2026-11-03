set -u; B=~/.cache/blind01
# s21 revises the G1/G3/G6 draft again (s20's finding); s22, an independent session, audits it.
bash $B/sci.sh 02 s21 > $B/sci_s21.out 2>&1
python3 $B/sci_owner_check.py 02 s21 >> $B/sci_s21.out 2>&1
grep -q '"draft_written": "yes"' $B/sci_s21.out && grep -q '^VALID' $B/sci_s21.out || { echo S19_NOT_READY; exit 1; }
bash $B/sci.sh 02 s22 > $B/sci_s22.out 2>&1
python3 $B/sci_audit_check.py 02 s22 s13 >> $B/sci_s22.out 2>&1
echo CHAIN_DONE
