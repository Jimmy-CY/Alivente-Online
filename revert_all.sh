#!/bin/sh
# revert_all.sh - release 9 push 1. NEWEST ROUND FIRST.
#
# All three write Push-PendingChanges.ps1, alv_rounds.py,
# alv_tree.py and test_waiting_down.py. Applied ES-1, ES-2,
# UO-1 - so they revert UO-1, ES-2, ES-1.
#
# Reverting oldest-first restores the LATER round's text over
# the earlier one and loses the original. That is the 18 Oct
# bug and it cost a hand repair.
#
# cp, NOT a text copy. A revert is a byte copy and a
# helper that read backups as text crashed on a UTF-16 file
# on 22 Oct and left three files reverted in an applied tree.
#
# ES-1 and ES-2 each CREATE a file, which a revert deletes -
# there was no before to restore.
# Run from the repo root.
set -e

echo "reverting UO-1 - the lease and the deed survive a failed save"
find . -name "*.bak_uploadorder" -not -path "./.git/*" | while read b; do
  f="${b%.bak_uploadorder}"; cp "$b" "$f"; rm "$b"
done

echo "reverting ES-2 - the lease renders to page images and the seal appends"
find . -name "*.bak_esignpdf" -not -path "./.git/*" | while read b; do
  f="${b%.bak_esignpdf}"; cp "$b" "$f"; rm "$b"
done
rm -f "pages/services/lease_sealing.py"   # created by ES-2, no before to restore

echo "reverting ES-1 - the envelope, its parties and its audit trail"
find . -name "*.bak_esignmodel" -not -path "./.git/*" | while read b; do
  f="${b%.bak_esignmodel}"; cp "$b" "$f"; rm "$b"
done
rm -f "pages/migrations/0103_es1_lease_signing.py"   # created by ES-1, no before to restore

echo "all three reverted. Backups still on disk (want 0):"
find . \( -name "*.bak_uploadorder" -o -name "*.bak_esignpdf" -o -name "*.bak_esignmodel" \) -not -path "./.git/*" | wc -l
