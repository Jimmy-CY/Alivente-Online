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
    '.bak_oldrounds',
    '.bak_stddoc',
    '.bak_csmall',
    '.bak_tap',
    '.bak_chip',
    '.bak_quad',
    '.bak_lease',
    '.bak_dead',
    '.bak_three',
    '.bak_rowact',
    '.bak_field',
    '.bak_series',
    '.bak_modal',
    '.bak_backlabel',
    '.bak_horizon',
    '.bak_avatar',
    '.bak_contrast',
    '.bak_pershead',
    '.bak_purple',
    '.bak_actionbar',
    '.bak_namedbars',
    '.bak_palette',
]


def as_left_by(path, suffix, read):
    """The text of `path` as the round whose backups end in `suffix` left
    it - the earliest later round's backup of it, or the file itself.

    A round in ROUNDS is placed by the list. A round OLDER than the list
    is placed by its backups' times: see later_backup()."""
    if suffix in ROUNDS:
        for s in ROUNDS[ROUNDS.index(suffix) + 1:]:
            if os.path.isfile(path + s):
                return read(path + s)
        return read(path)
    return read(later_backup(path, suffix) or path)


def later_backup(path, suffix):
    """For a round older than ROUNDS: of the file's backups, the one
    written FIRST AFTER this round's own - by modification time, which is
    when the next round saved the file before touching it, so its content
    is the file exactly as this round left it. None when no later round
    touched the file (the file itself is then the answer), or when this
    round left no backup to date it by."""
    own = path + suffix
    if not os.path.isfile(own):
        return None
    return backup_after(path, os.path.getmtime(own), own)


def backup_after(path, when, skip=None):
    """The file's first backup written after `when`, or None."""
    folder, name = os.path.split(path)
    best = None
    for n in os.listdir(folder or '.'):
        p = os.path.join(folder, n)
        if not n.startswith(name + '.bak_') or p == skip:
            continue
        t = os.path.getmtime(p)
        if t > when and (best is None or t < best[0]):
            best = (t, p)
    return best[1] if best else None


def as_of(path, when, read):
    """The text of `path` as it stood at time `when` - for a file a round
    READ but did not back up: its first backup written after `when`, or
    the file itself if nothing has touched it since."""
    return read(backup_after(path, when) or path)
