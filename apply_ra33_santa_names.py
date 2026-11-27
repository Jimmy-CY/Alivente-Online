# -*- coding: utf-8 -*-
"""apply_ra33_santa_names.py - round RA33, 27 Nov 2026.

RELEASE RA33 - SECRET SANTA EMAILS: NICKNAME (NAME), AND WHO'S TAKING PART.

    - NEW, shipped beside this file: test_ra33_santa_names.py.
    - pages/santa.py: the recipient (and the reveal's Santa) shown as the
      nickname over the name; the draw, test and change emails list
      everyone taking part, names only.
    - pages/help_content/administration.html: says so.

Stands on RA32. Idempotent. Edits backed up to .bak_ra33. No migration.
    python apply_ra33_santa_names.py --check
    python apply_ra33_santa_names.py
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
SUFFIX = '.bak_ra33'
SHIPPED = ('test_ra33_santa_names.py',)
RETIRED = ()
# (file, the text it holds now, what it becomes) - exact, line endings
# included.
EDITS = json.loads('[["pages/santa.py", "            santa = by_receiver.get(person.pk)\\n            name = santa.full_name if santa else \'\'\\n        else:\\n            pair = pairs.get(person.pk)\\n            name = pair.receiver.full_name if pair else \'\'\\n        if not name:\\n            continue\\n        subject, text, body = message(ex, kind, person, name)\\n", "            name = by_receiver.get(person.pk)\\n        else:\\n            pair = pairs.get(person.pk)\\n            name = pair.receiver if pair else None\\n        if not name:\\n            continue\\n        subject, text, body = message(ex, kind, person, name, people=crowd)\\n"], ["pages/santa.py", "    by_receiver = {p.receiver_id: p.giver for p in pairs.values()}\\n", "    by_receiver = {p.receiver_id: p.giver for p in pairs.values()}\\n    crowd = roster(ex)\\n"], ["pages/santa.py", "    body = _page(ex, hi, lead, label, receiver_name, after, thanks=(kind == \'reveal\'))\\n    text = _text(ex, hi, _plain(lead), receiver_name,\\n                 \'This is a test, sent only to you.\' if kind == \'test\' else \'\', thanks=(kind == \'reveal\'))\\n", "    big, small = shown(receiver_name)\\n    if kind in (\'draw\', \'test\', \'change\'):\\n        crowd = people if people is not None else (roster(ex) if ex.pk else [])\\n    else:\\n        crowd = []\\n    body = _page(ex, hi, lead, box, big, after, thanks=(kind == \'reveal\'), box_small=small, people=crowd)\\n    text = _text(ex, hi, _plain(lead), big,\\n                 \'This is a test, sent only to you.\' if kind == \'test\' else \'\', thanks=(kind == \'reveal\'),\\n                 box_small=small, people=crowd)\\n"], ["pages/santa.py", "    label = T[\'giver\'] if kind == \'reveal\' else \'your secret recipient\'\\n", "    box = T[\'giver\'] if kind == \'reveal\' else \'your secret recipient\'\\n"], ["pages/santa.py", "def message(ex, kind, person, receiver_name):\\n    \\"\\"\\"(subject, text, html) for one person. kind: draw, test, week, day,\\n    reveal, change (RA32 - a redraw gave them someone new). For reveal,\\n    receiver_name is who their Santa was. The words follow the occasion\\n    (RA32): Christmas, an office party, or another occasion.\\"\\"\\"\\n", "def message(ex, kind, person, receiver_name, people=None):\\n    \\"\\"\\"(subject, text, html) for one person. kind: draw, test, week, day,\\n    reveal, change (RA32 - a redraw gave them someone new). For reveal,\\n    receiver_name is who their Santa was. The words follow the occasion\\n    (RA32): Christmas, an office party, or another occasion.\\n    RA33: receiver_name may be the SantaPerson (shown as nickname over name);\\n    the draw, test and change emails list everyone taking part - `people`,\\n    or the event\'s own list when not given.\\"\\"\\"\\n"], ["pages/santa.py", "def _text(ex, hello, lead, box_name, after=\'\', thanks=False):\\n    T = tone(ex)\\n    lines = [ex.title, \'\', hello, \'\', lead]\\n    if box_name:\\n        lines += [\'\', \'    %s\' % box_name, \'\']\\n    lines += [\'%s: %s\' % kv for kv in _details(ex)]\\n", "def _text(ex, hello, lead, box_name, after=\'\', thanks=False, box_small=\'\', people=()):\\n    T = tone(ex)\\n    lines = [ex.title, \'\', hello, \'\', lead]\\n    if box_name:\\n        lines += [\'\', \'    %s\' % box_name] + ([\'    (%s)\' % box_small] if box_small else []) + [\'\']\\n    lines += [\'%s: %s\' % kv for kv in _details(ex)]\\n    if people:\\n        lines += [\'\', \\"Who\'s taking part (%d):\\" % len(people)] + [\'  - %s\' % n for n in people]\\n"], ["pages/santa.py", "           \'<div style=\\"font-size:24px;font-weight:bold;color:%s;\\">%s</div></td></tr></table>\'\\n           % (TEAL, SOFT, e(box_label), TEAL_INK, e(box_name))) if box_name else \'\'\\n", "           \'<div style=\\"font-size:24px;font-weight:bold;color:%s;\\">%s</div>%s</td></tr></table>\'\\n           % (TEAL, SOFT, e(box_label), TEAL_INK, e(box_name),\\n              (\'<div style=\\"font-size:14px;color:%s;\\">%s</div>\' % (SOFT, e(box_small))) if box_small else \'\')\\n           ) if box_name else \'\'\\n    if people:\\n        after = (\'<p style=\\"margin:14px 0 4px;font-size:14px;color:%s;\\"><b>Who&rsquo;s taking part (%d)</b></p>\'\\n                 \'<ul style=\\"margin:0;padding-left:20px;font-size:14px;line-height:1.6;color:%s;\\">%s</ul>\'\\n                 % (INK, len(people), INK, \'\'.join(\'<li>%s</li>\' % e(n) for n in people))) + after\\n"], ["pages/santa.py", "def _page(ex, hello, lead, box_label, box_name, after, thanks=False):\\n", "# --------------------------------------------------------------------------\\n# RA33, 27 Nov 2026 - names in the emails. Demetri: \\"For those that we have\\n# saved a nickname, then maybe it can state the Nickname (Name)\\", and list\\n# the people taking part. Names only - nobody\'s email address goes to the\\n# others - and the same list for everyone, so it gives nothing away.\\n# --------------------------------------------------------------------------\\ndef shown(p):\\n    \\"\\"\\"(big, small) for a person: the nickname over their name when they\\n    have one that says something different; else just the name.\\"\\"\\"\\n    if isinstance(p, str):\\n        return p, \'\'\\n    nick = (p.nickname or \'\').strip()\\n    if nick and nick.lower() != p.full_name.lower():\\n        return nick, p.full_name\\n    return p.full_name, \'\'\\n\\n\\ndef label(p):\\n    \\"\\"\\"\'Papa (Demetri Manias)\', or the name alone.\\"\\"\\"\\n    big, small = shown(p)\\n    return \'%s (%s)\' % (big, small) if small else big\\n\\n\\ndef roster(ex):\\n    \\"\\"\\"Everyone taking part, as the emails list them, A to Z.\\"\\"\\"\\n    return sorted((label(p) for p in ex.people.all()), key=lambda s: s.lower())\\n\\n\\ndef _page(ex, hello, lead, box_label, box_name, after, thanks=False, box_small=\'\', people=()):\\n"], ["pages/help_content/administration.html", "    <p style=\\"font-size:13px; color:#6c757d; margin-bottom:12px;\\"><strong>People</strong> (up to 20): <strong>From contacts</strong> lists your Celebrations contacts (Celebrations &rarr; Contacts) that have an email address &mdash; tick and add. A contact without an email is not offered: add the email with the pencil on Contacts, or use Add person. <strong>Add person</strong> takes a name, surname, nickname and email; tick <strong>Also save to my contacts</strong> to keep them there too. The email greets each person by their nickname (or first name). The pencil edits a person, the bin removes them. <strong>Back</strong> returns to the page you came from &mdash; the Celebrations dashboard or Contacts.</p>\\r\\n", "    <p style=\\"font-size:13px; color:#6c757d; margin-bottom:12px;\\"><strong>People</strong> (up to 20): <strong>From contacts</strong> lists your Celebrations contacts (Celebrations &rarr; Contacts) that have an email address &mdash; tick and add. A contact without an email is not offered: add the email with the pencil on Contacts, or use Add person. <strong>Add person</strong> takes a name, surname, nickname and email; tick <strong>Also save to my contacts</strong> to keep them there too. The email greets each person by their nickname (or first name). Whoever has a nickname is shown as <em>Nickname (Name)</em> &mdash; in the box naming who they drew, and in the <strong>Who&rsquo;s taking part</strong> list the draw email carries (names only, never email addresses; everyone gets the same list, so it gives nothing away). The pencil edits a person, the bin removes them. <strong>Back</strong> returns to the page you came from &mdash; the Celebrations dashboard or Contacts.</p>\\r\\n"], ["alv_rounds.py", "    \'.bak_ra32\',\\n", "    \'.bak_ra32\',\\n    # RA33, 27 Nov 2026 - Secret Santa emails: Nickname (Name), and who\'s taking part.\\n    \'.bak_ra33\',\\n"], ["Push-PendingChanges.ps1", "    \'test_ra32_secret_santa_more.py\'\\n", "    \'test_ra32_secret_santa_more.py\',\\n    # RA33, 27 Nov 2026 - Secret Santa emails: Nickname (Name), and who\'s taking part.\\n    \'test_ra33_santa_names.py\'\\n"]]')


def refuse(msg):
    raise SystemExit('RA33 REFUSED: %s' % msg)


def load(rel):
    with open(os.path.join(ROOT, rel), 'rb') as f:
        raw = f.read()
    return raw.decode('utf-8-sig'), raw[:3] == b'\xef\xbb\xbf'


def main():
    check = '--check' in sys.argv[1:]
    ps1, _ = load('Push-PendingChanges.ps1')
    if "'test_ra33_santa_names.py'" in ps1:
        print('RA33 already applied.')
        return 0
    if "'test_ra32_secret_santa_more.py'" not in ps1:
        refuse('RA32 (apply_ra32_secret_santa_more.py) is not applied - '
               'this round registers after it.')
    for rel in SHIPPED:
        if not os.path.isfile(os.path.join(ROOT, *rel.split('/'))):
            refuse('%s is not in place - it ships with this patcher; copy it '
                   'in first.' % rel)
    # A file's edits are made one after another on the same text, in the
    # order listed; every anchor must be found exactly once when its turn
    # comes, or nothing at all is written.
    texts, order = {}, []
    for rel, old, new in EDITS:
        if rel not in texts:
            texts[rel] = list(load(rel))
            order.append(rel)
        text = texts[rel][0]
        if text.count(old) != 1:
            refuse('%s: the anchor is found %d time(s), not once'
                   % (rel, text.count(old)))
        texts[rel][0] = text.replace(old, new)
    plan = [(rel, texts[rel][0], texts[rel][1]) for rel in order]
    for rel, text, bom in plan:
        if check:
            print('RA33 --check: %s would change' % rel)
            continue
        p = os.path.join(ROOT, rel)
        if not os.path.exists(p + SUFFIX):
            shutil.copy2(p, p + SUFFIX)
        with open(p, 'wb') as f:
            f.write((b'\xef\xbb\xbf' if bom else b'') + text.encode('utf-8'))
        print('  changed %s' % rel)
    for rel in RETIRED:
        p = os.path.join(ROOT, *rel.split('/'))
        if not os.path.isfile(p):
            continue
        if check:
            print('RA33 --check: %s would be moved to %s' % (rel, SUFFIX))
            continue
        if os.path.exists(p + SUFFIX):
            os.remove(p)
        else:
            os.rename(p, p + SUFFIX)
        print('  retired %s (kept as %s)' % (rel, SUFFIX))
    if not check:
        print('RA33 applied - Secret Santa emails: Nickname (Name), and who\'s taking part. No migration.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
