# -*- coding: utf-8 -*-
"""pages/passport_holder.py - PT-2, 12 Nov 2026. Whose document this is.

Every document carries the holder's name as typed ("Demetri Manias") and,
since PH-1, a link to the household member ("Demetri"). The link was only
ever filled by backfill_passport_holder, once, in October: adding or
editing a document left it empty. So a document added since had no
holder, and Wellness Today - which asks "which documents are mine?" -
could not see it. Demetri, 12 Nov, on his own two passports: "Shouldn't I
be seeing two???"

THE SAME RULE AS THE BACKFILL, in the same order, and nothing looser:

    exact   the typed name is a member's name, character for character
    loose   it is once case and spacing are folded
    named   the typed name is in backfill_passport_holder.ALIASES, which
            Demetri wrote down on 5 Oct ("demetri manias" -> Demetri)

Only one member in the document's workspace may match. Two or more is
ambiguous, and an ambiguous name is no match: a register that guessed
would be worse than one that is empty.
"""
from pages.management.commands.backfill_passport_holder import ALIASES, fold


def matches(members, holder_name):
    """The members (of one workspace) this typed name names."""
    hits = [m for m in members if m.name == holder_name]
    if not hits:
        hits = [m for m in members if fold(m.name) == fold(holder_name)]
    if not hits and fold(holder_name) in ALIASES:
        want = ALIASES[fold(holder_name)]
        hits = [m for m in members if m.name == want]
    return hits


def member_for(workspace_id, holder_name):
    """The one household member this name belongs to, or None."""
    from pages.models import HouseholdMember
    if not (holder_name or '').strip():
        return None
    hits = matches(list(HouseholdMember.objects.filter(
        workspace_id=workspace_id)), holder_name)
    return hits[0] if len(hits) == 1 else None


def names_of(member):
    """Every typed name that means this member, folded."""
    out = {fold(member.name)}
    out.update(k for k, v in ALIASES.items() if v == member.name)
    return out
