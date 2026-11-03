set -u; B=~/.cache/blind01
# s17 drafts the G1/G3/G6 contract (content reader, seed-neutral); s18, an independent session, audits it for seed content and
# sufficiency. The operator reads DRAFT.md only after DRAFT_CLEAN.
bash $B/sci.sh 02 s17 > $B/sci_s17.out 2>&1
grep -q '"draft_written": "yes"' $B/sci_s17.out && grep -q '^VALID' $B/sci_s17.out || { echo S17_NOT_READY; exit 1; }
bash $B/sci.sh 02 s18 > $B/sci_s18.out 2>&1
python3 $B/sci_audit_check.py 02 s18 s13 >> $B/sci_s18.out 2>&1
echo CHAIN_DONE
