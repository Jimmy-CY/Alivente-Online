# -*- coding: utf-8 -*-
"""alv_impact.py - which suites can a round actually break?

Demetri, 7 Oct 2026, on CM-1: "I don't understand why a point solution
like CM-1 needs to do the whole sweep. There is no change to the base.
The impact is on a few screens in Issues and a few reports, which I will
personally test. The sweep is a waste of time and effort."

HE IS RIGHT, AND THE EVIDENCE IS IN THE FOUR ROUNDS BUILT ON 6 OCTOBER.
The full sweep found exactly eight red suites across all four, and every
single one of them falls into one of two sets:

  1. A suite that NAMES a file the round changed. test_ei_modal reads
     fsr_details.html; test_celebration_az reads recipe_management.html.
  2. A suite that COUNTS something across the whole repo, and so breaks
     when any round ADDS a file to it - a template, a migration, a
     suite. There are nine of those and they are listed below by name.

Run against all four rounds, the two sets together caught 8 of 8:

    round             picked   of 298   caught every real failure
    E-2b (403 page)      235      298   YES
    E-2c (urlconf)        13      298   YES
    B-3 (green/red)       42      298   YES
    CM-1 (comment)        50      298   YES

E-2b IS THE LINE, AND IT IS THE HONEST ONE. It picked 235 because it
touched base.html, which nearly every suite reads. A round that touches
base gets the whole sweep whether it asks for one or not; a round that
touches four files in Issues does not. The instrument says so itself
rather than somebody judging it each time.

WHAT THIS IS AND IS NOT. It is PRE-FLIGHT, not the gate. The gate is
Push-PendingChanges.ps1 -Push, which runs all 298 on his machine, every
time, and that does not change. The only job of a sweep here is to stop
a push failing on something I could have seen. A selection that would
have caught all eight is good enough for that job, and the difference is
50 suites against 298.

WHEN TO IGNORE IT: run the full sweep anyway if the round touches
base.html, alv_tree.py, alv_cssrules.py or alv_rounds.py. Those four are
read by so much that "what names them" is most of the tree, and the
selector will tell you so by picking almost everything.

    python alv_impact.py <changed file> [<changed file> ...]
    python alv_sweep.py --only-impact <changed file> ...
"""
import glob
import os
import re
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))

# THE NINE THAT COUNT THE WHOLE REPO. Every one of these has been seen
# to go red for a round that did not name it, because it asserts a
# NUMBER about the tree rather than a fact about one file. They are
# named rather than detected: a static rule that tried to find them
# picked 140 suites, because almost every suite calls templates() for
# its own narrow purpose.
COUNTERS = [
    'test_settings_env.py',      # how many suites boot Django
    'test_sentinels.py',         # the sentinel table, and the $suites list
    'test_console_encoding.py',  # the preamble of every test_*.py
    'test_tree_roots.py',        # how many templates, by root
    'test_subtree_tones.py',     # the same, walked and flat
    'test_house_title.py',       # how many pages wear the house title
    'test_stranded.py',          # every template, for stranded markup
    'test_css_order.py',         # every template, for selector collisions
    'test_passport_holder.py',   # the migration chain
    # B-4, 7 Oct 2026. These two were added by CR-1 and
    # IM-1 and neither added itself here, so every round
    # since has been swept against an incomplete list.
    'test_cssrules_outside.py',  # colour literals, whole tree
    'test_important_base.py',    # !important, whole tree
    # B-4b, 8 Oct 2026 - adding itself: it counts the
    # fill/ink pairs of every rule in every template.
    'test_pair_contrast.py',     # fill/ink pairs, whole tree
    # B-5a, 8 Oct 2026 - adding itself, because its
    # sections 3 and 5 read every template in the tree.
    'test_neutrals.py',          # the greys, whole tree
]

# A round that touches one of these is not a point round, whatever it
# looks like. The selector will pick almost everything anyway; this is
# here so the reason is printed rather than inferred.
WIDE = ('base.html', 'alv_tree.py', 'alv_cssrules.py', 'alv_rounds.py',
        'Push-PendingChanges.ps1')


def suites():
    return sorted(os.path.basename(p)
                  for p in glob.glob(os.path.join(ROOT, 'test_*.py')))


def select(changed):
    """(picked, named, why) for the files this round changed.

    A suite is picked if it names one of the changed files - by full
    relative path or by basename - or if it is one of the nine that
    count the whole repo.
    """
    keys = set()
    for c in changed:
        c = c.replace('\\', '/')
        keys.add(c)
        keys.add(os.path.basename(c))
    named = set()
    for s in suites():
        with open(os.path.join(ROOT, s), encoding='utf-8',
                  errors='replace') as fh:
            text = fh.read()
        if any(k in text for k in keys):
            named.add(s)
    wide = [os.path.basename(c) for c in changed
            if os.path.basename(c) in WIDE]
    return sorted(named | set(COUNTERS)), sorted(named), wide


def pins(text):
    """Suites that quote `text` as a whole string - the ONLY ones a copy
    change can break.

    Demetri, 7 Oct 2026: "I am questioning if changing the label of a
    field needs a sweep?" Measured across all 811 <label> texts in the
    tree against every quoted string in all 298 suites: 626 of them -
    77 per cent - are asserted by NO suite at all. Change one of those
    and nothing can go red, so the right number of suites to run is
    nought.

    Where a label IS pinned it is usually one suite and it is exact:
    "Lease Start Date" only test_label_fit, "Upload Document" only
    test_manage_modal. Seconds, not an hour.

    A one-word label over-reports, because a generic word like Code or
    File appears as a quoted string in suites that have nothing to do
    with it - test_sentinels quotes File because the sentinel table is
    written @{ File = ... }. Over-reporting is safe; it costs a few
    seconds of running suites that were never at risk.
    """
    out = []
    for s in suites():
        with open(os.path.join(ROOT, s), encoding='utf-8',
                  errors='replace') as fh:
            src = fh.read()
        for m in re.finditer(r"'([^'\n]{2,160})'|\"([^\"\n]{2,160})\"",
                             src):
            q = (m.group(1) or m.group(2)).strip()
            if q == text or q == text + ':' or q.endswith('>' + text):
                out.append(s)
                break
    return sorted(out)


def main(argv):
    if argv and argv[0].startswith('--text='):
        text = argv[0].split('=', 1)[1]
        hit = pins(text)
        print('label or copy   : %r' % text)
        print('suites that pin it: %d of %d' % (len(hit), len(suites())))
        if not hit:
            print('')
            print('  NOTHING asserts this text. A change to it cannot turn')
            print('  any suite red. Push it.')
        else:
            print('')
            for s in hit:
                print(s)
        return 0
    if not argv:
        print(__doc__.strip())
        return 2
    picked, named, wide = select(argv)
    total = len(suites())
    print('changed            : %d file(s)' % len(argv))
    for c in argv:
        print('                     %s' % c)
    print('suites naming them : %d' % len(named))
    print('whole-repo counters: %d' % len(COUNTERS))
    print('PICKED             : %d of %d' % (len(picked), total))
    if wide:
        print('')
        print('  NOT A POINT ROUND. It touches %s, which most of the tree'
              % ', '.join(wide))
        print('  reads. Run the full sweep.')
    elif len(picked) > total * 0.5:
        print('')
        print('  More than half the tree is picked. That is the selector')
        print('  telling you this is not a point round - run them all.')
    print('')
    for s in picked:
        print(s)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
