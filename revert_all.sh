#!/bin/sh
# revert_all.sh - the four fixes. NEWEST ROUND FIRST.
#
# All four write to Push-PendingChanges.ps1, alv_rounds.py
# and test_waiting_down.py, three to alv_tree.py, and all
# four to meal_planner.html.
# Reverting oldest-first restores the LATER round's text over
# the earlier one and loses the original. That is the 18 Oct
# bug and it cost a hand repair.
#
# Run from the repo root.
set -e

echo "reverting PB-3 - a write leaves you on the day you were on"
find . -name "*.bak_backdate" -not -path "./.git/*" | while read b; do
  f="${b%.bak_backdate}"; cp "$b" "$f"; rm "$b"
done

echo "reverting RL-1 - the picker reload actually binds"
find . -name "*.bak_pickreload" -not -path "./.git/*" | while read b; do
  f="${b%.bak_pickreload}"; cp "$b" "$f"; rm "$b"
done

echo "reverting CL-1 - a meal in the calendar is a pill again"
find . -name "*.bak_chippill" -not -path "./.git/*" | while read b; do
  f="${b%.bak_chippill}"; cp "$b" "$f"; rm "$b"
done

echo "reverting DB-1 - the responsive block that never closed"
find . -name "*.bak_datebar" -not -path "./.git/*" | while read b; do
  f="${b%.bak_datebar}"; cp "$b" "$f"; rm "$b"
done

echo "all four reverted. Backups still on disk (want 0):"
find . \( -name "*.bak_backdate" -o -name "*.bak_pickreload" -o -name "*.bak_chippill" -o -name "*.bak_datebar" \) -not -path "./.git/*" | wc -l
