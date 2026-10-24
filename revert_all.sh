#!/bin/sh
# revert_all.sh - release 10 push 1. NEWEST ROUND FIRST.
#
# All three write Push-PendingChanges.ps1, alv_rounds.py,
# alv_tree.py and test_waiting_down.py. Applied CF-2, WK-1,
# ES-3a - so they revert ES-3a, WK-1, CF-2.
#
# Reverting oldest-first restores the LATER round's text over
# the earlier one and loses the original. That is the 18 Oct
# bug and it cost a hand repair.
#
# cp, NOT a text copy. A revert is a byte copy and a
# helper that read backups as text crashed on a UTF-16 file
# on 22 Oct and left three files reverted in an applied tree.
# CF-2 retires three UTF-16 files, so this matters here more
# than anywhere: their backups ARE the only copies.
#
# ES-3a CREATES two files, which a revert deletes - there
# was no before to restore.
# Run from the repo root.
set -e

echo "reverting ES-3a - the fourth tile and the envelope register"
find . -name "*.bak_leasesigning" -not -path "./.git/*" | while read b; do
  f="${b%.bak_leasesigning}"; cp "$b" "$f"; rm "$b"
done
rm -f "pages/views/lease_signing.py"   # created by ES-3a, no before to restore
rm -f "pages/templates/lease_signing_list.html"   # created by ES-3a, no before to restore

echo "reverting WK-1 - the sweep can be told how many workers to use"
find . -name "*.bak_pushworkers" -not -path "./.git/*" | while read b; do
  f="${b%.bak_pushworkers}"; cp "$b" "$f"; rm "$b"
done

echo "reverting CF-2 - one requirements file, and it is the one that deploys"
find . -name "*.bak_onelist" -not -path "./.git/*" | while read b; do
  f="${b%.bak_onelist}"; cp "$b" "$f"; rm "$b"
done

echo "all three reverted. Backups still on disk (want 0):"
find . \( -name "*.bak_leasesigning" -o -name "*.bak_pushworkers" -o -name "*.bak_onelist" \) -not -path "./.git/*" | wc -l
