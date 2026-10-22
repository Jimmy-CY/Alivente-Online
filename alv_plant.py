# -*- coding: utf-8 -*-
"""alv_plant.py - the planter lock. LK-1, 22 Oct 2026.

A PLANTER KILLED MID-PLANT LEAVES A DEFECT ON DISK AND NOTHING NOTICES.

Fifteen suites in this tree WRITE INTO A REAL FILE to prove a detector
catches something - test_css_order proves a selector collision by
MAKING one, test_icon_names plants a ghost glyph on a button. Each one
copies the victim aside, writes the defect, checks, and restores in a
finally. That is correct, and it holds for everything Python can catch.

IT DOES NOT HOLD FOR A KILL. Ctrl-C twice, a closed laptop, a timeout
that reaches SIGKILL, a machine that loses power - and the finally
never runs. The defect stays in the file, every later suite reads it,
and the diagnosis is a day of looking at the wrong thing. This was
logged on 17 October after exactly that explanation was proposed for a
mismatched backup, fitted the evidence, and turned out to be untrue -
which is the reason it was logged rather than built: it fits, it is
mechanically possible, and nothing would tell you.

WHAT THIS DOES, AND WHAT IT DELIBERATELY DOES NOT.

It takes a FINGERPRINT of every text file the repo owns - 1,504 files,
32.6 MB, measured at 0.12 seconds on 22 October - and writes it to a
lock before a planter starts. After the planter it takes another and
compares. A file that differs is a file the planter did not put back,
and the run stops and names it.

If the planter was killed, the lock is still there on the next run.
recover() finds it, compares, and names every file that differs from
the pre-plant state, refusing to let a sweep start on a tree that is
not the tree anybody meant to test.

IT DOES NOT RESTORE THE CONTENT. Keeping 32 MB of bytes in a lock to
insure against a kill that has never happened is a cost paid on every
planter, on every run, for ever. It keeps hashes, which name the damage
exactly; putting a named file back is `git checkout -- <file>`, which
is exact, and which the operator runs. A tool that silently rewrote
source files would be a worse thing to have in this tree than the
problem it fixed.

AND IT NEEDS NO CHANGE TO ANY PLANTER. alv_run.py already knows which
suites plant - the list is explicit and test_gate_speed re-derives the
signature and fails if a suite outside it starts planting. Arming
around that list covers all fifteen at once, and covers the sixteenth
the day it joins the list, without fifteen edits in fifteen suites
that each have their own shape.
"""
import hashlib
import json
import os
import time

ROOT = os.path.dirname(os.path.abspath(__file__)) or '.'
LOCK = os.path.join(ROOT, '.alv_plant_lock.json')

# WHAT THE REPO OWNS. Not media, not staticfiles, not a cache, not a
# backup - a .bak_ file is a round's own record and a planter has no
# business near one, but they change for ordinary reasons and would
# make every fingerprint differ from every other.
EXT = ('.py', '.html', '.ps1', '.css', '.js', '.json', '.txt', '.md',
       '.cfg', '.ini', '.toml', '.yml', '.yaml')
# migrations IS SKIPPED ON PURPOSE. No planter goes near one, and a
# migration written by something else during a run would otherwise be
# reported as damage a planter did - which is the one thing this must
# never say, because a false accusation here costs a `git checkout` of
# a file somebody meant to keep.
SKIP_DIRS = ('.git', 'node_modules', '__pycache__', 'media',
             'staticfiles', '.venv', 'venv', '.pytest_cache', 'migrations')
# AND NOT THE THINGS A RUN ITSELF WRITES. The log is rewritten after
# every suite by design - GT-2 - and the lock is this file's own.
#
# AND ANY LOCK, NOT ONLY THE DEFAULT ONE. LOCK is a module global so a
# suite can point it at a scratch file and drive the mechanism without
# touching the real lock that alv_run has armed around it - and the
# first draft of this skipped the default NAME, so the scratch lock
# appeared in every fingerprint and the suite reported itself as damage.
SKIP_FILES = ('.alv_run_log.json',)
SKIP_PREFIX = '.alv_plant_lock'


# A VIRTUAL ENVIRONMENT IS NOT SOURCE, AND IT IS NOT CALLED venv.
#
# Found on Demetri's laptop, 22 October, by his gate: the fingerprint
# covered 8,392 files there against 1,395 in the mirror, and took 3.26
# seconds instead of 0.12. His environment lives in a directory called
# `code` - the name in his PowerShell prompt - so a skip list of names
# walked straight into it and hashed every .py in site-packages.
#
# THE MARKER, NOT THE NAME. A directory holding pyvenv.cfg is an
# environment whatever somebody called it. That is also the only
# version of this check that keeps working when the next machine calls
# it something else again.
#
# AND IT IS NOT ONLY SLOW. A pip install between arm and disarm would
# have been reported as a planter leaving thousands of files behind,
# which is the one thing this must never say.
def is_env(path):
    """True when this directory is a virtual environment."""
    return os.path.isfile(os.path.join(path, 'pyvenv.cfg'))


def fingerprint(root=None):
    """path -> sha256, for every text file the repo owns."""
    root = root or ROOT
    out = {}
    for base, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs
                   if d not in SKIP_DIRS
                   and not is_env(os.path.join(base, d))]
        for name in files:
            if name in SKIP_FILES or '.bak_' in name:
                continue
            if name.startswith(SKIP_PREFIX):
                continue
            if not name.endswith(EXT):
                continue
            path = os.path.join(base, name)
            try:
                with open(path, 'rb') as fh:
                    out[os.path.relpath(path, root).replace('\\', '/')] = (
                        hashlib.sha256(fh.read()).hexdigest())
            except OSError:
                # A FILE THAT CANNOT BE READ IS NOT A FILE THAT CHANGED.
                # Saying nothing about it is honest; inventing a hash
                # for it would make every later comparison lie.
                continue
    return out


def differences(before, after):
    """(changed, vanished, appeared) - sorted, so a report is stable."""
    changed = sorted(p for p in before
                     if p in after and before[p] != after[p])
    vanished = sorted(p for p in before if p not in after)
    appeared = sorted(p for p in after if p not in before)
    return changed, vanished, appeared


def arm(suite):
    """Write the lock. Called before a planter runs."""
    data = {'suite': suite, 'started': time.time(),
            'files': fingerprint()}
    with open(LOCK, 'w', encoding='utf-8') as fh:
        json.dump(data, fh)
    return data


def disarm(suite, armed):
    """Compare and clear. Returns the differences the planter left.

    An EMPTY answer is the normal one: a planter restores what it
    planted, and the tree after is the tree before. Anything else is a
    planter that did not put something back, which nothing checked
    until this round - a kill is the loud version of the same fault,
    and this catches the quiet version too.
    """
    now = fingerprint()
    changed, vanished, appeared = differences(armed['files'], now)
    if os.path.exists(LOCK):
        os.remove(LOCK)
    return changed, vanished, appeared


def stale():
    """The lock a killed planter left, or None."""
    if not os.path.exists(LOCK):
        return None
    try:
        with open(LOCK, encoding='utf-8') as fh:
            return json.load(fh)
    except (OSError, ValueError):
        # A LOCK THAT CANNOT BE READ IS STILL A LOCK. Something was
        # planting and did not finish; saying so with no file list is
        # far better than deleting it and saying nothing.
        return {'suite': '(unreadable lock)', 'started': 0, 'files': {}}


def recover():
    """What a killed planter left behind. Called before a run starts.

    Returns (suite, changed, vanished, appeared) or None. It does NOT
    put anything back - see the module docstring. Naming the files is
    the job; `git checkout -- <file>` is the fix, and it belongs to
    whoever can see whether that file has other work in it.
    """
    lock = stale()
    if lock is None:
        return None
    changed, vanished, appeared = differences(lock.get('files', {}),
                                              fingerprint())
    return lock.get('suite', '?'), changed, vanished, appeared


def release():
    """Drop the lock, having dealt with it."""
    if os.path.exists(LOCK):
        os.remove(LOCK)
