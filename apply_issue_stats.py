# -*- coding: utf-8 -*-
"""SECTION DB, ROUND DB-7 - THE ISSUE FIGURES, AT THE TOP, ON THE HOUSE TILE

Demetri, with a screenshot of Dashboard -> a property -> Issues: "we still
need to move these three summary boxes to the top of the page."

He is quoting his own list - DB-7, 1 Oct: "move the issues figures up and
convert them to .alv-stats. Self-contained." Both halves, then.

==========================================================================
WHERE THEY WERE
==========================================================================
Below the table. On a property with sixteen issues that is two full
screens down, so the figure that tells you whether anything needs doing
is the last thing you reach - after reading every row it summarises.

==========================================================================
AND WHAT THEY WERE MADE OF
==========================================================================
Seventeen rules of the page's own, for a component base already owns:

    .issues-summary          a wash and a top border
    .summary-card            a white card, a radius, a shadow, a hover lift
    .summary-card.resolved   border-left 4px #28a745
    .summary-card.unresolved border-left 4px #ffc107
    .summary-card.total      border-left 4px #0e7c8b
    .summary-icon            2rem, and the same three colours again
    .summary-number          1.8rem bold #2c3e50
    .summary-label           0.9rem uppercase #6c757d
    + a Bootstrap .row/.col-md-4 grid
    + two phone blocks, at 768 and at 576

base's ALV-STAT says all of it: the grid, the figure, the uppercase
letter-spaced label, the phone behaviour, and the tones. Nine literal
colours go with the rules.

    Resolved    .alv-stat-good   var(--alv-good)
    Unresolved  .alv-stat-attn   var(--alv-warn)
    Total       plain ink - a total is not a verdict

AND --alv-stats-cols: 3, which is the one thing base leaves to the page,
the same way .filter-grid leaves it the column count.

------------------------------------
THE ICONS GO, AND THAT IS THE STANDARD
------------------------------------
base's stat tile is a FIGURE AND THE WORDS FOR IT. No icon slot, and no
stat strip in this app has one - not Issues Analysis, not Receipts, not
the dashboard. The green tick, the amber clock and the teal list went
with the three rules that coloured them.

A tile that needs an icon to say what it is has a label problem, not an
icon problem; "Resolved" over a green 16 is not ambiguous.

------------------------------------------------
AND THEY KEEP THE ONE THING THAT WAS ALREADY RIGHT
------------------------------------------------
They render only inside {% if property_issues %}. A property with no
issues shows the empty state and no figures, which is correct - three
zeroes would be noise - and this round does not touch it.

Backups: .bak_issuestats. Idempotent. --check writes nothing.
"""
import os
import re
import sys

import alv_tree

CHECK = '--check' in sys.argv
SUFFIX = '.bak_issuestats'
CRLF = {}
SENTINEL = 'test_issue_stats.py'
ROOT = os.getcwd()


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


def back_up(path, original_bytes):
    bak = path + SUFFIX
    if os.path.exists(bak):
        return
    with open(bak, 'wb') as fh:
        fh.write(original_bytes)
    with open(bak, 'rb') as fh:
        if fh.read() != original_bytes:
            raise SystemExit('DB7: %s is not a byte copy' % bak)


def swap(text, old, new, what, path):
    """Replace exactly once, in the file's own line endings, and refuse an
    anchor that lands mid-line. A3's lesson."""
    o = old.replace('\r\n', '\n')
    n = new.replace('\r\n', '\n')
    if CRLF.get(path):
        o, n = o.replace('\n', '\r\n'), n.replace('\n', '\r\n')
    c = text.count(o)
    if c != 1:
        raise SystemExit('DB7: %s appears %d times, not once' % (what, c))
    i = text.index(o)
    if i and not o.startswith(('\n', '\r')) and text[i - 1] not in '\n\r':
        raise SystemExit('DB7: the anchor for %s starts MID-LINE (after %r)'
                         % (what, text[i - 1]))
    return text.replace(o, n)


def code_only(text):
    """Comments blanked, length preserved. A check that a name is absent
    must not read the note recording its removal - nine gates across five
    rounds got that wrong before the instrument was fixed."""
    def blank(m):
        return re.sub(r'[^\n]', ' ', m.group(0))
    text = re.sub(r'<!--.*?-->', blank, text, flags=re.S)
    text = re.sub(r'\{#.*?#\}', blank, text, flags=re.S)
    return re.sub(r'/\*.*?\*/', blank, text, flags=re.S)


print('=' * 74)
print('SECTION DB, ROUND DB-7 - THE ISSUE FIGURES%s'
      % (' - CHECK ONLY' if CHECK else ''))
print('=' * 74)

PAGE = alv_tree.join('property_detail.html')
pt, praw = read(PAGE)

OLD_MARKUP = '''                                        <!-- Summary Stats -->
                                        <div class="issues-summary mt-3">
                                            <div class="row">
                                                <div class="col-md-4">
                                                    <div class="summary-card resolved">
                                                        <div class="summary-icon">
                                                            <i class="fas fa-check-circle"></i>
                                                        </div>
                                                        <div class="summary-content">
                                                            <div class="summary-number">{{ resolved_count }}</div>
                                                            <div class="summary-label">Resolved</div>
                                                        </div>
                                                    </div>
                                                </div>
                                                <div class="col-md-4">
                                                    <div class="summary-card unresolved">
                                                        <div class="summary-icon">
                                                            <i class="fas fa-clock"></i>
                                                        </div>
                                                        <div class="summary-content">
                                                            <div class="summary-number">{{ unresolved_count }}</div>
                                                            <div class="summary-label">Unresolved</div>
                                                        </div>
                                                    </div>
                                                </div>
                                                <div class="col-md-4">
                                                    <div class="summary-card total">
                                                        <div class="summary-icon">
                                                            <i class="fas fa-list"></i>
                                                        </div>
                                                        <div class="summary-content">
                                                            <div class="summary-number">{{ total_issues_count }}</div>
                                                            <div class="summary-label">Total Issues</div>
                                                        </div>
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
'''

NEW_MARKUP = '''                                    <!-- The figures moved ABOVE the table - DB-7, 2 Oct 2026.
                                         They used to sit under it, which on a property with
                                         sixteen issues is two screens down: the number telling
                                         you whether anything needs doing came last, after every
                                         row it summarises. -->
                                    <div class="alv-stats issues-stats">
                                        <div class="alv-stat alv-stat-good">
                                            <div class="alv-stat-value">{{ resolved_count }}</div>
                                            <div class="alv-stat-label">Resolved</div>
                                        </div>
                                        <div class="alv-stat alv-stat-attn">
                                            <div class="alv-stat-value">{{ unresolved_count }}</div>
                                            <div class="alv-stat-label">Unresolved</div>
                                        </div>
                                        <div class="alv-stat">
                                            <div class="alv-stat-value">{{ total_issues_count }}</div>
                                            <div class="alv-stat-label">Total Issues</div>
                                        </div>
                                    </div>

'''

if 'alv-stats issues-stats' in pt:
    print('  property_detail.html         already done')
else:
    # ----------------------------------------------------------------
    # out from under the table
    # ----------------------------------------------------------------
    pt = swap(pt, OLD_MARKUP, '', 'the summary cards under the table', PAGE)

    # ----------------------------------------------------------------
    # and in above it
    # ----------------------------------------------------------------
    pt = swap(pt, '''                                {% if property_issues %}
                                    <!-- Issues Table -->
''', '''                                {% if property_issues %}
''' + NEW_MARKUP + '''                                    <!-- Issues Table -->
''', 'the place above the table', PAGE)

    # ----------------------------------------------------------------
    # seventeen rules the page no longer needs
    # ----------------------------------------------------------------
    pt = swap(pt, '''.issues-summary { padding: 20px; background: #f8f9fa; border-top: 1px solid #dee2e6; }
.summary-card { background: white; border-radius: 8px; padding: 15px; display: flex; align-items: center; box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05); transition: transform 0.2s ease; }
.summary-card:hover { transform: translateY(-2px); box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1); }
.summary-card.resolved { border-left: 4px solid #28a745; }
.summary-card.unresolved { border-left: 4px solid #ffc107; }
.summary-card.total { border-left: 4px solid #0e7c8b; }
.summary-icon { font-size: 2rem; margin-right: 15px; opacity: 0.8; }
.summary-card.resolved .summary-icon { color: #28a745; }
.summary-card.unresolved .summary-icon { color: #ffc107; }
.summary-card.total .summary-icon { color: #0e7c8b; }
.summary-content { text-align: left; }
.summary-number { font-size: 1.8rem; font-weight: bold; color: #2c3e50; line-height: 1; }
.summary-label { font-size: 0.9rem; color: #6c757d; text-transform: uppercase; letter-spacing: 0.5px; margin-top: 2px; }
''', '''/* THE COLUMN COUNT IS ALL THAT IS LEFT TO SAY - DB-7, 2 Oct 2026.
   Thirteen rules stood here for a component base already owns: a card, a
   radius, a shadow, a hover lift, three left borders in #28a745 / #ffc107
   / #0e7c8b, an icon in those same three, a 1.8rem figure in #2c3e50 and
   an uppercase 0.9rem label in #6c757d. base's ALV-STAT says every one of
   them, from tokens, and sizes the figure and the label itself.

   base leaves the column count to the page - the same way it leaves
   .filter-grid its columns - because how many figures a screen has is the
   screen's business. This screen has three. */
.issues-stats { --alv-stats-cols: 3; margin-bottom: 16px; }
''', 'the summary-card rules', PAGE)

    # ----------------------------------------------------------------
    # and the two phone blocks
    # ----------------------------------------------------------------
    pt = swap(pt, '''    /* Issues summary cards */
    .issues-summary {
        padding: 12px;
    }
    .issues-summary .row {
        margin-left: 0;
        margin-right: 0;
    }
    .issues-summary .col-md-4 {
        padding-left: 0;
        padding-right: 0;
    }
    .summary-card {
        padding: 12px;
        margin-bottom: 10px;
    }
    .summary-icon {
        font-size: 1.6rem;
        margin-right: 12px;
    }
    .summary-number {
        font-size: 1.4rem;
    }
    .summary-label {
        font-size: 0.75rem;
    }
''', '''    /* A phone block for the summary cards used to be here, and a
       second one at 576px below. base's ALV-STAT carries its own phone
       behaviour, so there is nothing left for either to say. [DB-7] */
''', 'the 768px phone block', PAGE)

    pt = swap(pt, '''    .summary-card {
        margin-bottom: 15px;
    }
    .summary-number {
        font-size: 1.5rem;
    }
    .summary-icon {
        font-size: 1.5rem;
    }
''', '''    /* and the 576px one. [DB-7] */
''', 'the 576px phone block', PAGE)

    if not CHECK:
        back_up(PAGE, praw)
        write(PAGE, pt)
    print('  property_detail.html         the figures moved above the table '
          'and onto .alv-stats')
    print('  %-28s seventeen rules dropped, nine literal colours' % '')

# ==========================================================================
print('')
print('  REGISTRATION')
print('  ' + '-' * 70)
for rel, old, new, what, mark in (
        ('alv_rounds.py', "    '.bak_jsescape',\n]\n",
         "    '.bak_jsescape',\n    '%s',\n]\n" % SUFFIX,
         'the end of ROUNDS', SUFFIX),
        ('Push-PendingChanges.ps1', "    'test_js_escape.py'\n)\n",
         "    'test_js_escape.py'\n"
         "    # The issue figures, moved above the table they summarise and\n"
         "    # put on base's stat tile. Its section 3 renders the real\n"
         "    # markup in Chromium and reads back that the figures sit ABOVE\n"
         "    # the table - an ordering claim that a grep cannot make.\n"
         "    'test_issue_stats.py'\n)\n", 'the end of $suites', SENTINEL)):
    path = os.path.join(ROOT, rel)
    tt, rr = read(path)
    if mark in tt:
        print('  %-34s already done' % rel)
        continue
    tt = swap(tt, old, new, what, path)
    if not CHECK:
        back_up(path, rr)
        write(path, tt)
    print('  %-34s %s' % (rel, what))

print('')
print('  GATES')
print('  ' + '-' * 70)
if CHECK:
    print('  skipped - they read the finished files, and --check writes none')
    print('-' * 74)
    print('  CHECK ONLY - every anchor matched exactly once, nothing written')
    print('=' * 74)
    raise SystemExit(0)

now = read(PAGE)[0]
code = code_only(now)

# THE FIGURES ARE ABOVE THE TABLE, IN THE SOURCE.
i_stats = code.index('alv-stats issues-stats')
i_table = code.index('issues-table-container')
if not i_stats < i_table:
    raise SystemExit('DB7: the figures are still below the table')
print('  the figures come before the table in the markup')

# NOT ONE summary-card RULE OR CLASS LEFT.
for name in ('summary-card', 'issues-summary', 'summary-icon',
             'summary-number', 'summary-label', 'summary-content'):
    if name in code:
        raise SystemExit('DB7: %s is still in the page' % name)
print('  and not one of the six old class names survives')

# THE PAGE KEEPS ONLY THE COLUMN COUNT.
own = re.findall(r'(?m)^\.issues-stats\s*\{([^}]*)\}', code)
if len(own) != 1:
    raise SystemExit('DB7: .issues-stats is declared %d time(s)' % len(own))
keys = set(k.split(':')[0].strip() for k in own[0].split(';') if ':' in k)
if keys - {'--alv-stats-cols', 'margin-bottom'}:
    raise SystemExit('DB7: the page says more than the column count: %s'
                     % sorted(keys))
print('  and the page says only the column count and a margin')

# THE TONES ARE base's, AND THE TOTAL HAS NONE.
seg = code[i_stats:i_table]
for want in ('alv-stat alv-stat-good', 'alv-stat alv-stat-attn'):
    if want not in seg:
        raise SystemExit('DB7: %s is missing' % want)
if seg.count('alv-stat-value') != 3 or seg.count('alv-stat-label') != 3:
    raise SystemExit('DB7: there are not three tiles')
print('  three tiles: good, attn, and a plain one - a total is not a verdict')

# NINE LITERAL COLOURS GONE, AND NONE GAINED.
was = code_only(read(PAGE + SUFFIX)[0])
a = len(re.findall(r'#[0-9a-fA-F]{3,6}\b', code))
b = len(re.findall(r'#[0-9a-fA-F]{3,6}\b', was))
if a > b:
    raise SystemExit('DB7: the page gained %d literal colour(s)' % (a - b))
print('  literal colours %d -> %d' % (b, a))

# THE MARKUP STILL CLOSES.
body = re.sub(r'<(script|style)\b.*?</\1>', '', code, flags=re.S)
n = len(re.findall(r'<div\b', body)) - len(re.findall(r'</div\s*>', body))
if n:
    raise SystemExit('DB7: property_detail.html has %+d unbalanced <div>' % n)
print('  every <div> closes')

# THE % IN A REGEX IS NOT A FORMAT SPECIFIER, and the first draft of this
# built the pattern with % interpolation - so {%\s* was read as a format
# character and the gate crashed instead of checking. Built by
# concatenation now.
for tag, close in (('if', 'endif'), ('for', 'endfor')):
    o = len(re.findall(r'\{%\s*' + tag + r'\b', code))
    c = len(re.findall(r'\{%\s*' + close + r'\s*%\}', code))
    if o != c:
        raise SystemExit('DB7: %s %d vs %s %d' % (tag, o, close, c))
print('  and every {% if %} and {% for %} still closes')

# AND THE FIGURES STILL ONLY RENDER WHEN THERE ARE ISSUES.
if '{% if property_issues %}' not in code:
    raise SystemExit('DB7: the property_issues guard is gone')
seg2 = code[code.index('{% if property_issues %}'):]
if seg2.index('alv-stats issues-stats') > seg2.index('{% else %}'):
    raise SystemExit('DB7: the figures moved outside the issues guard - a '
                     'property with none would show three zeroes')
print('  and they still render only when the property HAS issues')

# EVERY SENTINEL IN THE PUSH GATE STILL RESOLVES - F3's lesson.
_Q = r"'((?:[^']|'')*)'|\"((?:[^\"]|\"\")*)\""
SF = re.compile(r"\b(File|Text|What)\s*=\s*(?:%s)" % _Q)
SG = re.compile(r"\b(Absent|Code)\s*=\s*\$(true|false)")
ps_text = read(os.path.join(ROOT, 'Push-PendingChanges.ps1'))[0]
rows = []
for line in ps_text.split('\n'):
    if '@{' not in line or 'File' not in line:
        continue
    f = {}
    for k, sq, dq in SF.findall(line):
        f[k] = sq.replace("''", "'") if sq else dq.replace('""', '"')
    for k, v in SG.findall(line):
        f[k] = (v == 'true')
    if 'File' in f and 'Text' in f:
        rows.append(f)
raw = len(re.findall(r'@\{ *File *=', ps_text))
if len(rows) != raw:
    raise SystemExit('DB7: the push gate has %d sentinel rows, parsed %d'
                     % (raw, len(rows)))


def strip(t):
    t = re.sub(r'<!--.*?-->', '', t, flags=re.S)
    t = re.sub(r'\{#.*?#\}', '', t, flags=re.S)
    t = re.sub(r'/\*.*?\*/', '', t, flags=re.S)
    t = re.sub(r'(?m)^\s*//.*$', '', t)
    return re.sub(r'(?m)^\s*#.*$', '', t)


stale = []
for r in rows:
    p = os.path.join(ROOT, *r['File'].replace('\\', '/').split('/'))
    if not os.path.isfile(p):
        stale.append('%s FILE MISSING' % r['File'])
        continue
    b2 = read(p)[0]
    if r.get('Code'):
        b2 = strip(b2)
    if (r['Text'].lower() in b2.lower()) != (not r.get('Absent')):
        stale.append('%s %s %r' % (r['File'],
                                   'NOT FOUND' if not r.get('Absent')
                                   else 'IS BACK', r['Text'][:50]))
if stale:
    raise SystemExit('DB7: %d push-gate sentinel(s) no longer resolve:\n   %s'
                     % (len(stale), '\n   '.join(stale[:6])))
print('  and all %d push-gate sentinels still resolve' % len(rows))

print('-' * 74)
print('  The figure that says whether anything needs doing is the first thing')
print('  on the screen, not the last, and it is the tile the rest of the app')
print('  uses.')
print('=' * 74)
