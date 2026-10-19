#!/bin/sh
# revert_all.sh - Release 3, push 3. NEWEST ROUND FIRST.
#
# All three rounds write to Push-PendingChanges.ps1,
# alv_tree.py, alv_rounds.py and test_waiting_down.py.
# Reverting oldest-first restores the LATER round's text over
# the earlier one and loses the original. That is the 18 Oct
# bug and it cost a hand repair.
#
# TWO FILES ARE DELETED, not restored: they were created by
# these rounds and have no before. Leaving 0101 behind would
# leave a migration Django tries to run against tables that
# still exist.
#
# Run from the repo root.
set -e

echo "reverting PF-2 - the picker filters by five things, on one shared function"
find . -name "*.bak_pickfilter" -not -path "./.git/*" | while read b; do
  f="${b%.bak_pickfilter}"; cp "$b" "$f"; rm "$b"
done
rm -f "pages/views/recipes/_recipe_filter.py"   # created by PF-2, no before to restore

echo "reverting MX-1 - the old planner three tables go"
find . -name "*.bak_mealdrop" -not -path "./.git/*" | while read b; do
  f="${b%.bak_mealdrop}"; cp "$b" "$f"; rm "$b"
done
rm -f "pages/migrations/0101_drop_meal_plan.py"   # created by MX-1, no before to restore

echo "reverting GS-1 - the contended suite leaves the pool"
find . -name "*.bak_gateserial" -not -path "./.git/*" | while read b; do
  f="${b%.bak_gateserial}"; cp "$b" "$f"; rm "$b"
done

echo "all three reverted. Backups still on disk (want 0):"
find . \( -name "*.bak_pickfilter" -o -name "*.bak_mealdrop" -o -name "*.bak_gateserial" \) -not -path "./.git/*" | wc -l
