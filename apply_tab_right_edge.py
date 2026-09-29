# -*- coding: utf-8 -*-
"""SECTION P, ROUND P6 - THE TAB GETS ITS RIGHT EDGE BACK

Demetri, looking at /personal/ after P2 deployed: the right bar next to
Personal is missing. It is, and P2 is why.

WHAT WAS ACTUALLY HOLDING THAT LINE UP.

    .admin-tab.personal-tab { border-right: none; }

The Personal tab was drawn with no right border on purpose, because the
FUTURE tab sat hard against it and supplied the line itself:

    .admin-tab.future-tab.personal-active { border-left-color: ...; }

Two tabs, one shared edge, drawn once. It is a reasonable way to build a
tab strip and it is completely invisible until one of the two tabs goes
away - which P2 did this afternoon, leaving a tab open on its right and a
panel border starting in mid-air.

THE FIX IS TO DELETE THE LINE THAT SAID "SOMEBODY ELSE DRAWS THIS". With
nothing to butt against, the tab draws its own four sides, and the strip
closes. Nothing else about it moves: the radius, the colours, the -3px
overlap onto the panel and the active tab's bottom edge blending into the
panel are all untouched.

admin_apms.html HAS THE SAME RULE AND MUST KEEP IT. Its strip is
.alivente-tab + .future-tab, and BOTH tabs are still there, so its shared
edge still has somebody drawing it. This round refuses if that page has
lost its Future tab, because then it would have the same hole and this
would be the wrong fix applied to one page out of two.

Backups: .bak_tabedge. Idempotent. --check writes nothing.
"""
import os
import re
import sys

import alv_tree

CHECK = '--check' in sys.argv
SUFFIX = '.bak_tabedge'
PAGE = 'personal.html'
OTHER = 'admin_apms.html'
CRLF = {}

WAS = """  .admin-tab.personal-tab {
    border-color: var(--personal-dark);
    color: var(--personal-dark);
    background-color: white;
    border-bottom-color: var(--personal-dark);
    border-right: none;
    border-radius: 10px 10px 0 0;
  }"""

NOW = """  .admin-tab.personal-tab {
    border-color: var(--personal-dark);
    color: var(--personal-dark);
    background-color: white;
    border-bottom-color: var(--personal-dark);
    /* IT DRAWS ITS OWN RIGHT EDGE NOW - 29 Sep, and here is the history.
       This rule said `border-right: none`, because the FUTURE tab sat
       hard against it and drew the shared line itself, through
       .admin-tab.future-tab.personal-active's border-left-color. Two
       tabs, one edge, drawn once.

       P2 commented the Future tab out, and the line went with it: the
       tab was left open on its right and the panel's border began in
       mid-air. Nothing butts against this tab any more, so it draws all
       four of its own sides.

       admin_apms.html carries the same `border-right: none` and KEEPS
       it - both of its tabs are still there, so its shared edge still
       has somebody drawing it. If its Future tab is ever switched off
       too, it needs this same line removed; apply_tab_right_edge.py
       refuses to run while that page's Future tab is missing, so the
       question cannot be forgotten. */
    border-radius: 10px 10px 0 0;
  }"""


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
            raise SystemExit('P6: %s is not a byte copy' % bak)


print('=' * 74)
print('SECTION P, ROUND P6 - THE TAB GETS ITS RIGHT EDGE BACK%s'
      % (' - CHECK ONLY' if CHECK else ''))
print('=' * 74)

path = alv_tree.path_of(PAGE)
text, raw = read(path)

# THE PREMISE: this page has ONE tab now.
mk = re.sub(r'<style\b.*?</style>', '', text, flags=re.S)
mk = re.sub(r'\{%\s*comment\s*%\}.*?\{%\s*endcomment\s*%\}', '', mk, flags=re.S)
tabs = re.findall(r'class="admin-tab ([\w\- ]+)"', mk)
if len(tabs) != 1:
    raise SystemExit('P6: %s renders %d tab(s) (%s) - this round is for a '
                     'strip with ONE tab, where nothing butts against it'
                     % (PAGE, len(tabs), tabs))
print('  %s renders one tab: %s' % (PAGE, tabs[0]))

# THE OTHER PAGE: it keeps the shared-edge rule, and must still have the
# tab that draws the shared edge.
other = read(alv_tree.path_of(OTHER))[0]
omk = re.sub(r'<style\b.*?</style>', '', other, flags=re.S)
omk = re.sub(r'\{%\s*comment\s*%\}.*?\{%\s*endcomment\s*%\}', '', omk,
             flags=re.S)
otabs = re.findall(r'class="admin-tab ([\w\- ]+)"', omk)
if not any('future-tab' in t for t in otabs):
    raise SystemExit('P6: %s no longer renders a Future tab (%s), so its '
                     '`border-right: none` now leaves the same hole this '
                     'round is closing. Fix both or neither.'
                     % (OTHER, otabs))
if 'border-right: none' not in other:
    raise SystemExit('P6: %s no longer carries `border-right: none` - the '
                     'two pages have diverged and this round\'s reasoning '
                     'about them is stale' % OTHER)
print('  %s still renders %d tabs, so it keeps its shared edge'
      % (OTHER, len(otabs)))

if 'border-right: none' not in text:
    print('  %s already draws its own right edge' % PAGE)
else:
    a = eol(path, WAS)
    if text.count(a) != 1:
        raise SystemExit('P6: the personal-tab rule is there %d time(s), '
                         'not 1' % text.count(a))
    text = text.replace(a, eol(path, NOW), 1)

    if 'border-right' in re.sub(r'/\*.*?\*/', '', text, flags=re.S):
        raise SystemExit('P6: a border-right declaration survives in %s'
                         % PAGE)
    for need in ('border-radius: 10px 10px 0 0;',
                 'border-color: var(--personal-dark);',
                 'margin-bottom: -3px;'):
        if need not in text:
            raise SystemExit('P6: %s went missing - this round removes one '
                             'declaration and nothing else' % need)
    print('  border-right: none deleted; the tab draws all four sides')
    if not CHECK:
        back_up(path, raw)
        write(path, text)

print('-' * 74)
if CHECK:
    print('  CHECK ONLY - nothing written')
print('=' * 74)
