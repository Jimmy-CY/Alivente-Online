#!/bin/sh
# revert_all.sh - release 6 push 1. NEWEST ROUND FIRST.
#
# All seven write to Push-PendingChanges.ps1, alv_rounds.py,
# alv_tree.py and test_waiting_down.py. DP-1 and SD-1 both
# write convert_recipe_photos.py and DP-1 went first, so
# SD-1 must revert BEFORE it.
# Reverting oldest-first restores the LATER round's text over
# the earlier one and loses the original. That is the 18 Oct
# bug and it cost a hand repair.
#
# cp, NOT a text copy. CF-1 backup of
# mysite/cron-requirements.txt is UTF-16LE and a revert is a
# byte copy. A helper that read it as text crashed on 22 Oct
# and left three files reverted in an applied tree.
#
# Run from the repo root.
set -e

echo "reverting LK-1 - a killed planter leaves a lock behind"
find . -name "*.bak_planterlock" -not -path "./.git/*" | while read b; do
  f="${b%.bak_planterlock}"; cp "$b" "$f"; rm "$b"
done
rm -f "alv_plant.py"   # created by LK-1, no before to restore

echo "reverting WN-1 - the workspace list is two queries, not N"
find . -name "*.bak_wsprefetch" -not -path "./.git/*" | while read b; do
  f="${b%.bak_wsprefetch}"; cp "$b" "$f"; rm "$b"
done

echo "reverting CF-1 - the configuration says what it really is"
find . -name "*.bak_configtruth" -not -path "./.git/*" | while read b; do
  f="${b%.bak_configtruth}"; cp "$b" "$f"; rm "$b"
done

echo "reverting SD-1 - a rebuild replaces the file it rebuilds"
find . -name "*.bak_photorebuild" -not -path "./.git/*" | while read b; do
  f="${b%.bak_photorebuild}"; cp "$b" "$f"; rm "$b"
done

echo "reverting DP-1 - the push finds out whether it deployed"
find . -name "*.bak_deployprobe" -not -path "./.git/*" | while read b; do
  f="${b%.bak_deployprobe}"; cp "$b" "$f"; rm "$b"
done

echo "reverting WD-1 - the week columns drag into order"
find . -name "*.bak_weekdrag" -not -path "./.git/*" | while read b; do
  f="${b%.bak_weekdrag}"; cp "$b" "$f"; rm "$b"
done

echo "reverting HG-1 - the guide and the page agree, both ways"
find . -name "*.bak_helpagrees" -not -path "./.git/*" | while read b; do
  f="${b%.bak_helpagrees}"; cp "$b" "$f"; rm "$b"
done

echo "all seven reverted. Backups still on disk (want 0):"
find . \( -name "*.bak_planterlock" -o -name "*.bak_wsprefetch" -o -name "*.bak_configtruth" -o -name "*.bak_photorebuild" -o -name "*.bak_deployprobe" -o -name "*.bak_weekdrag" -o -name "*.bak_helpagrees" \) -not -path "./.git/*" | wc -l
