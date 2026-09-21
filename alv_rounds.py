# -*- coding: utf-8 -*-
"""alv_rounds.py - the file as a round LEFT it.

Most suites check that their round changed exactly what it said it would:
the file now is its backup plus the change. A later round that edits the
same file breaks that check, although nothing is wrong - it has done its
own job. Four rounds on 21 Sep each had to patch older suites by hand for
exactly this, one at a time, and the laptop's gate found each of them.

The answer is the same every time. The file as round R left it is the
BACKUP TAKEN BY THE FIRST LATER ROUND that touched it - that backup is,
by definition, the file just before that later round began. If no later
round touched it, it is the file as it is now.

ROUNDS is that order, oldest first. A new round appends its backup suffix
here, once, and every suite that asks as_left_by() keeps judging only its
own round without being edited.
"""
import os

ROUNDS = [
    '.bak_zoomguard',
    '.bak_smallctl',
    '.bak_printq',
    '.bak_printbtn',
    '.bak_divbal',
    '.bak_histpurge',
    '.bak_modalhead',
    '.bak_eimodal',
    '.bak_reporthead',
    '.bak_appliesfrom',
]


def as_left_by(path, suffix, read):
    """The text of `path` as the round whose backups end in `suffix` left
    it - the earliest later round's backup of it, or the file itself."""
    later = ROUNDS[ROUNDS.index(suffix) + 1:] if suffix in ROUNDS else []
    for s in later:
        if os.path.isfile(path + s):
            return read(path + s)
    return read(path)
