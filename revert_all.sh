#!/bin/sh
# revert_all.sh - release 7 push 1. NEWEST ROUND FIRST.
#
# All four write to Push-PendingChanges.ps1, alv_rounds.py,
# alv_tree.py and test_waiting_down.py. SI-1 and NL-1 both
# write check_recipe_files.py and models.py, SI-1 first, so
# NL-1 must revert BEFORE it.
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

echo "reverting PT-1 - the print sheet knows which view sent it"
find . -name "*.bak_printorigin" -not -path "./.git/*" | while read b; do
  f="${b%.bak_printorigin}"; cp "$b" "$f"; rm "$b"
done

echo "reverting NL-1 - a generated name fits its column"
find . -name "*.bak_namewidth" -not -path "./.git/*" | while read b; do
  f="${b%.bak_namewidth}"; cp "$b" "$f"; rm "$b"
done
rm -f "pages/migrations/0102_nl1_name_width.py"   # created by NL-1, no before to restore

echo "reverting SI-1 - a copied recipe does not share its photo"
find . -name "*.bak_sharedimage" -not -path "./.git/*" | while read b; do
  f="${b%.bak_sharedimage}"; cp "$b" "$f"; rm "$b"
done
rm -f "pages/management/commands/check_recipe_files.py"   # created by SI-1, no before to restore

echo "reverting SB-2 - one primary per state on the shopping bar"
find . -name "*.bak_shopbar2" -not -path "./.git/*" | while read b; do
  f="${b%.bak_shopbar2}"; cp "$b" "$f"; rm "$b"
done

echo "all four reverted. Backups still on disk (want 0):"
find . \( -name "*.bak_printorigin" -o -name "*.bak_namewidth" -o -name "*.bak_sharedimage" -o -name "*.bak_shopbar2" \) -not -path "./.git/*" | wc -l
