#!/bin/sh
# revert_all.sh - release 8 push 1. NEWEST ROUND FIRST.
#
# Both write to Push-PendingChanges.ps1, alv_rounds.py,
# alv_tree.py and test_waiting_down.py - and BOTH write
# base.html, RV-1 first, so IR-1 must revert BEFORE it.
#
# Reverting oldest-first restores the LATER round's text over
# the earlier one and loses the original. That is the 18 Oct
# bug and it cost a hand repair.
#
# cp, NOT a text copy. A revert is a byte copy and a
# helper that read backups as text crashed on a UTF-16 file
# on 22 Oct and left three files reverted in an applied tree.
# Reverting NL-1 deletes the migration FILE; it does not
#
# Run from the repo root.
set -e

echo "reverting IR-1 - one register for one kind of identifier"
find . -name "*.bak_reflink" -not -path "./.git/*" | while read b; do
  f="${b%.bak_reflink}"; cp "$b" "$f"; rm "$b"
done

echo "reverting RV-1 - the receipt has a screen that shows the record"
find . -name "*.bak_receiptview" -not -path "./.git/*" | while read b; do
  f="${b%.bak_receiptview}"; cp "$b" "$f"; rm "$b"
done
rm -f "pages/templates/cash_receipt_detail.html"   # created by RV-1, no before to restore

echo "both reverted. Backups still on disk (want 0):"
find . \( -name "*.bak_reflink" -o -name "*.bak_receiptview" \) -not -path "./.git/*" | wc -l
