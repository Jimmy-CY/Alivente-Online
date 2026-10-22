#!/bin/sh
# revert_all.sh - release 5 push 1. NEWEST ROUND FIRST.
#
# All seven write to Push-PendingChanges.ps1, alv_rounds.py,
# alv_tree.py and test_waiting_down.py; three write to
# meal_planner.html and two to meal_planning.py.
# BM-1 alone touches 89 files, and MN-2, RO-1 and VR-1 all
# edit files it edits too - so it must revert AFTER them.
# Reverting oldest-first restores the LATER round's text over
# the earlier one and loses the original. That is the 18 Oct
# bug and it cost a hand repair.
#
# Run from the repo root.
set -e

echo "reverting VR-1 - the schedule readout wears tokens"
find . -name "*.bak_recipetidy" -not -path "./.git/*" | while read b; do
  f="${b%.bak_recipetidy}"; cp "$b" "$f"; rm "$b"
done

echo "reverting RO-1 - a day dragged into order by its grip"
find . -name "*.bak_dayorder" -not -path "./.git/*" | while read b; do
  f="${b%.bak_dayorder}"; cp "$b" "$f"; rm "$b"
done

echo "reverting MN-2 - a menu is a span, landing where you say"
find . -name "*.bak_menurange" -not -path "./.git/*" | while read b; do
  f="${b%.bak_menurange}"; cp "$b" "$f"; rm "$b"
done

echo "reverting BM-1 - one message loop, in base - 81 copies gone"
find . -name "*.bak_msgbase" -not -path "./.git/*" | while read b; do
  f="${b%.bak_msgbase}"; cp "$b" "$f"; rm "$b"
done

echo "reverting PX-2 - a floor under every display copy"
find . -name "*.bak_photofloor" -not -path "./.git/*" | while read b; do
  f="${b%.bak_photofloor}"; cp "$b" "$f"; rm "$b"
done

echo "reverting RG-3 - the printed week and day stop at the end"
find . -name "*.bak_printcompact" -not -path "./.git/*" | while read b; do
  f="${b%.bak_printcompact}"; cp "$b" "$f"; rm "$b"
done

echo "reverting WF-1 - the week band fills with moss"
find . -name "*.bak_weekfill" -not -path "./.git/*" | while read b; do
  f="${b%.bak_weekfill}"; cp "$b" "$f"; rm "$b"
done

echo "all seven reverted. Backups still on disk (want 0):"
find . \( -name "*.bak_recipetidy" -o -name "*.bak_dayorder" -o -name "*.bak_menurange" -o -name "*.bak_msgbase" -o -name "*.bak_photofloor" -o -name "*.bak_printcompact" -o -name "*.bak_weekfill" \) -not -path "./.git/*" | wc -l
