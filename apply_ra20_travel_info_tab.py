# -*- coding: utf-8 -*-
"""apply_ra20_travel_info_tab.py - round RA20, 24 Nov 2026.

RELEASE RA20 - GOOD TO KNOW SHOWS GOOD TO KNOW.

    - travel/templates/travel/trip.html: the tab chain's last branch names
      its tab (elif tab == 'costs') instead of a bare else. Good to know
      (RA12) sits after the chain, so the bare else drew the whole Costs
      section above its cards - and, without the days the view builds for
      Costs only, that section said "The trip needs its dates first".
      (Demetri, 24 Nov: "Why does the Good to Know Button open the Costs?")
    - pages/templates/user_activity.html and the Administration Help: a
      sign-in is a password or passkey login; Wellness and Travel on a
      phone keep someone signed in for 30 days, so their visits can show
      under Pages and time with no sign-in. (Demetri: "Is that because the
      Wellness app keeps her logged in?")
    - Registers test_ra20_travel_info_tab.py (shipped beside this file) on
      the push gate, and .bak_ra20 in alv_rounds.ROUNDS.

Stands on RA19. Idempotent. Edits backed up to .bak_ra20. No migration.
    python apply_ra20_travel_info_tab.py --check    (changes nothing)
    python apply_ra20_travel_info_tab.py
"""

# --- CONSOLE ENCODING ----------------------------------- 16 Sep 2026 --
# This file prints text it read out of the templates, and some of that
# text is not ASCII - projects/project_task_list.html carries a Greek
# heading behind the language switch, and it will not be the last. On
# Windows, Python writes stdout as cp1252 whenever it is not a UTF-8
# console, and cp1252 cannot encode Greek: the print itself raises
# UnicodeEncodeError and the run dies part-way through. A crash blocks a
# push exactly as hard as a failure and says far less about why.
#
# So keep the encoding the console really has - forcing UTF-8 only moves
# the problem to whoever decodes us - and change the ERROR HANDLER, so a
# character the console cannot draw arrives as a question mark instead of
# ending the run. stderr too, because a traceback is a print as well.
# Guarded, because stdout is not always a stream that can be told.
# See test_console_encoding.py.
import sys as _sys
for _stream in (_sys.stdout, _sys.stderr):
    try:
        _stream.reconfigure(errors='replace')
    except Exception:
        pass
# ------------------------------------------------------------------------


import json
import os
import shutil
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
SUFFIX = '.bak_ra20'
# (file, the text it holds now, what it becomes) - exact, line endings
# included.
EDITS = json.loads('[["travel/templates/travel/trip.html", "    </section>\\n{% else %}\\n", "    </section>\\n{% elif tab == \'costs\' %}{% comment %} RA20, 24 Nov 2026 - Costs by name, not \'everything else\': Good to know (RA12) sits after this chain, so a bare else drew the whole Costs section above its cards (Demetri: \\"Why does the Good to Know Button open the Costs?\\"). {% endcomment %}\\n"], ["pages/templates/user_activity.html", "    <p class=\\"act-note\\">Five wrong passwords in a row for one sign-in send you an email.</p>\\n", "    <p class=\\"act-note\\">Five wrong passwords in a row for one sign-in send you an email.</p>\\n    {# RA20, 24 Nov 2026 - why a person can have pages but no sign-in (Demetri: \\"Is that because the Wellness app keeps her logged in?\\"). #}\\n    <p class=\\"act-note\\" data-act-long>A sign-in is a password or passkey login. Wellness and Travel on a phone keep someone signed in for 30 days, so their visits can show under Pages and time with no sign-in here.</p>\\n"], ["pages/help_content/administration.html", "      <li><strong>Sign-ins</strong> &mdash; signed in, signed out and wrong passwords, with the device and IP address. <strong>Five wrong passwords in a row</strong> for one sign-in send you an email.</li>\\r\\n", "      <li><strong>Sign-ins</strong> &mdash; signed in, signed out and wrong passwords, with the device and IP address. <strong>Five wrong passwords in a row</strong> for one sign-in send you an email. A sign-in is a password or passkey login: Wellness and Travel on a phone keep someone signed in for 30 days, so their visits can appear under <strong>Pages and time</strong> with no sign-in.</li>\\r\\n"], ["Push-PendingChanges.ps1", "    \'test_ra19_acquisitions_screens.py\'\\n", "    \'test_ra19_acquisitions_screens.py\',\\n    # RA20, 24 Nov 2026 - Good to know shows Good to know; why pages can come with no sign-in.\\n    \'test_ra20_travel_info_tab.py\'\\n"], ["alv_rounds.py", "    \'.bak_ra19\',\\n", "    \'.bak_ra19\',\\n    # RA20, 24 Nov 2026 - Good to know shows Good to know; why pages can come with no sign-in.\\n    \'.bak_ra20\',\\n"]]')


def refuse(msg):
    raise SystemExit('RA20 REFUSED: %s' % msg)


def load(rel):
    with open(os.path.join(ROOT, rel), 'rb') as f:
        raw = f.read()
    return raw.decode('utf-8-sig'), raw[:3] == b'\xef\xbb\xbf'


def main():
    check = '--check' in sys.argv[1:]
    ps1, _ = load('Push-PendingChanges.ps1')
    if "'test_ra20_travel_info_tab.py'" in ps1:
        print('RA20 already applied.')
        return 0
    if "'test_ra19_acquisitions_screens.py'" not in ps1:
        refuse('RA19 (apply_ra19_acquisitions_screens.py) is not applied - '
               'this round registers after it.')
    if not os.path.isfile(os.path.join(ROOT, 'test_ra20_travel_info_tab.py')):
        refuse('test_ra20_travel_info_tab.py is not beside this file.')
    plan = []
    for rel, old, new in EDITS:
        text, bom = load(rel)
        if text.count(old) != 1:
            refuse('%s: the anchor is found %d time(s), not once'
                   % (rel, text.count(old)))
        plan.append((rel, text.replace(old, new), bom))
    for rel, text, bom in plan:
        if check:
            print('RA20 --check: %s would change' % rel)
            continue
        p = os.path.join(ROOT, rel)
        if not os.path.exists(p + SUFFIX):
            shutil.copy2(p, p + SUFFIX)
        with open(p, 'wb') as f:
            f.write((b'\xef\xbb\xbf' if bom else b'') + text.encode('utf-8'))
        print('  changed %s' % rel)
    if not check:
        print('RA20 applied - Good to know shows Good to know. No migration.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
