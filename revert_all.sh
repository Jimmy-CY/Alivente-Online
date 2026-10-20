#!/bin/sh
# revert_all.sh - release 4 push 3. NEWEST ROUND FIRST.
#
# Seven of the nine write to Push-PendingChanges.ps1,
# alv_rounds.py, alv_tree.py and test_waiting_down.py, and
# four of them to meal_planner.html.
# Reverting oldest-first restores the LATER round's text over
# the earlier one and loses the original. That is the 18 Oct
# bug and it cost a hand repair.
#
# Run from the repo root.
set -e

echo "reverting MH-5 - the guide catches up with the calendar"
find . -name "*.bak_mealguide5" -not -path "./.git/*" | while read b; do
  f="${b%.bak_mealguide5}"; cp "$b" "$f"; rm "$b"
done

echo "reverting PP-1 - a meal plan you can put on the fridge"
find . -name "*.bak_printplan" -not -path "./.git/*" | while read b; do
  f="${b%.bak_printplan}"; cp "$b" "$f"; rm "$b"
done
rm -f "pages/templates/meal_plan_print.html"   # created by PP-1, no before to restore

echo "reverting CE-1 - the probe writes outside the tree"
find . -name "*.bak_cescratch" -not -path "./.git/*" | while read b; do
  f="${b%.bak_cescratch}"; cp "$b" "$f"; rm "$b"
done

echo "reverting SL-7 - the list covers what you are looking at"
find . -name "*.bak_listrange" -not -path "./.git/*" | while read b; do
  f="${b%.bak_listrange}"; cp "$b" "$f"; rm "$b"
done

echo "reverting NT-1 - a Note, from the picker"
find . -name "*.bak_picknote" -not -path "./.git/*" | while read b; do
  f="${b%.bak_picknote}"; cp "$b" "$f"; rm "$b"
done

echo "reverting LO-1 - Leftovers, from Month and Week"
find . -name "*.bak_chipleft" -not -path "./.git/*" | while read b; do
  f="${b%.bak_chipleft}"; cp "$b" "$f"; rm "$b"
done

echo "reverting FV-1 - the heart stops returning 403"
find . -name "*.bak_favtoken" -not -path "./.git/*" | while read b; do
  f="${b%.bak_favtoken}"; cp "$b" "$f"; rm "$b"
done

echo "reverting AP-1 - a recipe onto a day from the library"
find . -name "*.bak_addplanner" -not -path "./.git/*" | while read b; do
  f="${b%.bak_addplanner}"; cp "$b" "$f"; rm "$b"
done

echo "reverting RD-3 - the photo opens a quick look"
find . -name "*.bak_quicklook" -not -path "./.git/*" | while read b; do
  f="${b%.bak_quicklook}"; cp "$b" "$f"; rm "$b"
done

echo "all nine reverted. Backups still on disk (want 0):"
find . \( -name "*.bak_mealguide5" -o -name "*.bak_printplan" -o -name "*.bak_cescratch" -o -name "*.bak_listrange" -o -name "*.bak_picknote" -o -name "*.bak_chipleft" -o -name "*.bak_favtoken" -o -name "*.bak_addplanner" -o -name "*.bak_quicklook" \) -not -path "./.git/*" | wc -l
