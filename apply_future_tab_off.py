# -*- coding: utf-8 -*-
"""SECTION P, ROUND P2 - THE FUTURE TAB GOES QUIET

Demetri: comment out the Future tab, we can re-instate it in future.

WHAT IT ACTUALLY WAS. A tab with no panel behind it. The strip holds two
tabs, PERSONAL and FUTURE, and the content container holds exactly one
panel - personal-panel. Clicking FUTURE has never shown anything, because
there has never been anything to show.

{% comment %}, NOT <!-- -->. An HTML comment is still sent to the browser:
the tab would vanish from the page and stay in View Source, where the next
person to read it has to work out whether it is live. A Django comment
never reaches the response at all, and it is the form that survives a
multi-line note - which is the thing X12 was fixing this morning.

THE CSS STAYS. .future-tab, .future-panel and the two --future-* tokens
are left exactly where they are, unused, so re-instating this is deleting
two lines rather than reconstructing a component. That is deliberate and
it is written into the comment, so a sweep for unused rules finds the
reason next to the rules.

Backups: .bak_futuretab. Idempotent. --check writes nothing.
"""
import os
import re
import sys

import alv_tree

CHECK = '--check' in sys.argv
SUFFIX = '.bak_futuretab'
PAGE = 'personal.html'
CRLF = {}

WAS = """  <div class="admin-tab future-tab personal-active">
    <i class="fas fa-clock"></i>
    <span>FUTURE</span>
  </div>"""

NOW = """  {% comment %}
    THE FUTURE TAB, OFF SINCE 29 SEP 2026, AT DEMETRI'S ASK.
    It never had a panel behind it - the container below holds
    personal-panel and nothing else - so clicking it did nothing, on a
    page whose other tab is the whole point of the screen.

    TO PUT IT BACK: delete this line and the endcomment line. Nothing
    else was removed. The rules it needs are still in the stylesheet
    below - .admin-tab.future-tab, .tab-panel.future-panel and the two
    --future-* tokens - left there unused on purpose, so reinstating is
    two deletions and not a rebuild. A sweep for unused rules should
    find this note before it finds them.
  <div class="admin-tab future-tab personal-active">
    <i class="fas fa-clock"></i>
    <span>FUTURE</span>
  </div>
  {% endcomment %}"""


def read(path):
    with open(path, 'rb') as fh:
        raw = fh.read()
    CRLF[path] = b'\r\n' in raw
    return raw.decode('utf-8'), raw


def write(path, text):
    data = text.encode('utf-8')
    if CRLF.get(path):
        data = data.replace(b'\r\n', b'\n').replace(b'\n', b'\r\n')
    else:
        data = data.replace(b'\r\n', b'\n')
    with open(path, 'wb') as fh:
        fh.write(data)


def eol(path, s):
    return (s.replace('\r\n', '\n').replace('\n', '\r\n')
            if CRLF.get(path) else s.replace('\r\n', '\n'))


def back_up(path, original_bytes):
    bak = path + SUFFIX
    if os.path.exists(bak):
        return
    with open(bak, 'wb') as fh:
        fh.write(original_bytes)
    with open(bak, 'rb') as fh:
        if fh.read() != original_bytes:
            raise SystemExit('P2: %s is not a byte copy' % bak)


print('=' * 74)
print('SECTION P, ROUND P2 - THE FUTURE TAB GOES QUIET%s'
      % (' - CHECK ONLY' if CHECK else ''))
print('=' * 74)

path = alv_tree.path_of(PAGE)
text, raw = read(path)

if '{% comment %}' in text and 'future-tab' in text:
    print('  %s already has it commented out' % PAGE)
else:
    a = eol(path, WAS)
    if text.count(a) != 1:
        raise SystemExit('P2: the FUTURE tab is there %d time(s), not 1'
                         % text.count(a))

    # IT HAD NO PANEL. Said out loud, because if one ever appears this
    # round has quietly hidden a tab that leads somewhere.
    panels = re.findall(r'class="tab-panel ([\w\- ]+)"', text)
    if any('future' in p for p in panels):
        raise SystemExit('P2: there IS a future panel now (%s) - this round '
                         'is written for a tab that leads nowhere' % panels)
    print('  panels on the page: %s - none of them the tab\'s' % panels)

    text = text.replace(a, eol(path, NOW), 1)
    print('  the FUTURE tab is wrapped in a Django comment')

    for need in ('.admin-tab.future-tab', '.tab-panel.future-panel',
                 '--future-dark', '--future-light'):
        if need not in text:
            raise SystemExit('P2: %s went with it - the CSS was meant to '
                             'stay, so putting the tab back is two '
                             'deletions' % need)
    if '<!--' in eol(path, NOW):
        raise SystemExit('P2: an HTML comment would still be sent to the '
                         'browser')
    print('  the future CSS is untouched, so re-instating is two deletions')
    if not CHECK:
        back_up(path, raw)
        write(path, text)

print('-' * 74)
if CHECK:
    print('  CHECK ONLY - nothing written')
print('=' * 74)
