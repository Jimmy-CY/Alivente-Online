#!/bin/sh
# revert_all.sh - release 4 push 4. NEWEST ROUND FIRST.
#
# All ten write to Push-PendingChanges.ps1, alv_rounds.py,
# alv_tree.py and test_waiting_down.py; four write to
# meal_planner.html and two to meal_plan_print.html,
# meal_planning.py and test_pair_contrast.py.
# Reverting oldest-first restores the LATER round's text over
# the earlier one and loses the original. That is the 18 Oct
# bug and it cost a hand repair.
#
# Run from the repo root.
set -e

echo "reverting RG-2 - From and To on the printed plan"
find . -name "*.bak_printrange" -not -path "./.git/*" | while read b; do
  f="${b%.bak_printrange}"; cp "$b" "$f"; rm "$b"
done

echo "reverting RG-1 - the sheet follows the range"
find . -name "*.bak_printshape" -not -path "./.git/*" | while read b; do
  f="${b%.bak_printshape}"; cp "$b" "$f"; rm "$b"
done

echo "reverting CP-2 - Copy any span, and Saved Menus"
find . -name "*.bak_copymenus" -not -path "./.git/*" | while read b; do
  f="${b%.bak_copymenus}"; cp "$b" "$f"; rm "$b"
done

echo "reverting BA-1 - the instrument that could not see the bar"
find . -name "*.bak_baraudit" -not -path "./.git/*" | while read b; do
  f="${b%.bak_baraudit}"; cp "$b" "$f"; rm "$b"
done

echo "reverting HP-1 - Help, reachable on a phone"
find . -name "*.bak_helpphone" -not -path "./.git/*" | while read b; do
  f="${b%.bak_helpphone}"; cp "$b" "$f"; rm "$b"
done

echo "reverting MG-1 - a page that writes a message can show one"
find . -name "*.bak_msgbar2" -not -path "./.git/*" | while read b; do
  f="${b%.bak_msgbar2}"; cp "$b" "$f"; rm "$b"
done

echo "reverting SH-2 - the range row: 221px becomes 44px"
find . -name "*.bak_slrangerow" -not -path "./.git/*" | while read b; do
  f="${b%.bak_slrangerow}"; cp "$b" "$f"; rm "$b"
done

echo "reverting WT-1 - the week owns the edge, the meal the fill"
find . -name "*.bak_weekband" -not -path "./.git/*" | while read b; do
  f="${b%.bak_weekband}"; cp "$b" "$f"; rm "$b"
done

echo "reverting BO-1 - the planner bar puts its verb first"
find . -name "*.bak_barfirst" -not -path "./.git/*" | while read b; do
  f="${b%.bak_barfirst}"; cp "$b" "$f"; rm "$b"
done

echo "reverting SC-1 - Today, not Tonight"
find . -name "*.bak_saytoday" -not -path "./.git/*" | while read b; do
  f="${b%.bak_saytoday}"; cp "$b" "$f"; rm "$b"
done

echo "all ten reverted. Backups still on disk (want 0):"
find . \( -name "*.bak_printrange" -o -name "*.bak_printshape" -o -name "*.bak_copymenus" -o -name "*.bak_baraudit" -o -name "*.bak_helpphone" -o -name "*.bak_msgbar2" -o -name "*.bak_slrangerow" -o -name "*.bak_weekband" -o -name "*.bak_barfirst" -o -name "*.bak_saytoday" \) -not -path "./.git/*" | wc -l
