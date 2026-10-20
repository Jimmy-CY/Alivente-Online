#!/bin/sh
# revert_all.sh - Release 4, push 2. NEWEST ROUND FIRST.
#
# Seven of the eight write to Push-PendingChanges.ps1,
# alv_tree.py, alv_rounds.py and test_waiting_down.py, and
# five of them write to meal_planner.html.
# Reverting oldest-first restores the LATER round's text over
# the earlier one and loses the original. That is the 18 Oct
# bug and it cost a hand repair.
#
# THREE FILES ARE DELETED, NOT RESTORED: RD-1 creates
# _recipe_read.py, recipe_quicklook.html and its shell, and
# there is no before to put back. A revert that read only
# backups would leave a module nothing imports and two
# templates nothing renders.
#
# Run from the repo root.
set -e

echo "reverting PS-1 - the picker adds on click and stays open"
find . -name "*.bak_pickerstays" -not -path "./.git/*" | while read b; do
  f="${b%.bak_pickerstays}"; cp "$b" "$f"; rm "$b"
done

echo "reverting DC-1 - the Day card uses its width"
find . -name "*.bak_daycard" -not -path "./.git/*" | while read b; do
  f="${b%.bak_daycard}"; cp "$b" "$f"; rm "$b"
done

echo "reverting WC-1 - a day is a day in every view"
find . -name "*.bak_weekclick" -not -path "./.git/*" | while read b; do
  f="${b%.bak_weekclick}"; cp "$b" "$f"; rm "$b"
done

echo "reverting MB-2 - the date bar is a bar"
find . -name "*.bak_monthbar" -not -path "./.git/*" | while read b; do
  f="${b%.bak_monthbar}"; cp "$b" "$f"; rm "$b"
done

echo "reverting RD-2 - a meal in the calendar has a menu"
find . -name "*.bak_chipmenu" -not -path "./.git/*" | while read b; do
  f="${b%.bak_chipmenu}"; cp "$b" "$f"; rm "$b"
done

echo "reverting PB-2 - a write on the planner leaves you where you were"
find . -name "*.bak_viewback" -not -path "./.git/*" | while read b; do
  f="${b%.bak_viewback}"; cp "$b" "$f"; rm "$b"
done

echo "reverting RW-1 - the weight is worked out in grams"
find . -name "*.bak_recipeweight" -not -path "./.git/*" | while read b; do
  f="${b%.bak_recipeweight}"; cp "$b" "$f"; rm "$b"
done

echo "reverting RD-1 - a recipe opens without leaving the calendar"
find . -name "*.bak_recipemodal" -not -path "./.git/*" | while read b; do
  f="${b%.bak_recipemodal}"; cp "$b" "$f"; rm "$b"
done
rm -f "pages/views/recipes/_recipe_read.py"   # created by RD-1, no before to restore
rm -f "pages/templates/recipe_quicklook.html"   # created by RD-1, no before to restore
rm -f "pages/templates/recipe_quicklook_shell.html"   # created by RD-1, no before to restore

echo "all eight reverted. Backups still on disk (want 0):"
find . \( -name "*.bak_pickerstays" -o -name "*.bak_daycard" -o -name "*.bak_weekclick" -o -name "*.bak_monthbar" -o -name "*.bak_chipmenu" -o -name "*.bak_viewback" -o -name "*.bak_recipeweight" -o -name "*.bak_recipemodal" \) -not -path "./.git/*" | wc -l
