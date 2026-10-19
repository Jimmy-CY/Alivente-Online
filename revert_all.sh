#!/bin/sh
# revert_all.sh - Release 4, push 1. NEWEST ROUND FIRST.
#
# All four rounds write to Push-PendingChanges.ps1,
# alv_tree.py, alv_rounds.py, test_waiting_down.py and
# meal_planner.html.
# Reverting oldest-first restores the LATER round's text over
# the earlier one and loses the original. That is the 18 Oct
# bug and it cost a hand repair.
#
# ONE FILE IS RESTORED rather than reverted: MV-2 retired
# test_mini_grid.py and removed it from disk. Its backup is
# here, so copying it back is the revert.
#
# Run from the repo root.
set -e

echo "reverting MV-4 - one day in full, and the list of seven goes"
find . -name "*.bak_dayview" -not -path "./.git/*" | while read b; do
  f="${b%.bak_dayview}"; cp "$b" "$f"; rm "$b"
done

echo "reverting MV-3 - the week is seven columns"
find . -name "*.bak_weekcols" -not -path "./.git/*" | while read b; do
  f="${b%.bak_weekcols}"; cp "$b" "$f"; rm "$b"
done

echo "reverting MV-2 - the month is the view, and the mini calendar is deleted"
find . -name "*.bak_monthview" -not -path "./.git/*" | while read b; do
  f="${b%.bak_monthview}"; cp "$b" "$f"; rm "$b"
done

echo "reverting MV-1 - three zoom levels on one calendar"
find . -name "*.bak_viewswitch" -not -path "./.git/*" | while read b; do
  f="${b%.bak_viewswitch}"; cp "$b" "$f"; rm "$b"
done

echo "all four reverted. Backups still on disk (want 0):"
find . \( -name "*.bak_dayview" -o -name "*.bak_weekcols" -o -name "*.bak_monthview" -o -name "*.bak_viewswitch" \) -not -path "./.git/*" | wc -l
