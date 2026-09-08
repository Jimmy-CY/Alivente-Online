"""apply_heading_standard.py - every page heads itself the same way.

    python apply_heading_standard.py --check     dry run, writes nothing
    python apply_heading_standard.py

Run from the repo root. TWENTY-NINE templates.

THE STANDARD, as written into base.html on 8 Sep:

    <h2><center>ALIVENTE ONLINE - PAGE NAME</center></h2>
    <h5><center>A sentence describing the page</center></h5>   (optional)
    <br/>

  TITLE     CAPITALS, prefixed `ALIVENTE ONLINE - `. It is a LABEL: short,
            scanned rather than read.
  SUBTITLE  Sentence case. It is a SENTENCE - often eight words or more, and
            all-caps measurably slows reading by removing the word shapes
            that let you recognise a word without spelling it out.

The general rule, which base already followed without anyone writing it
down: CAPITALS FOR LABELS, SENTENCE CASE FOR PROSE. `.alv-stat-label` is
uppercase and letter-spaced because it is a label; nothing else in base
shouts.

WHY THIS ROUND EXISTS, INCLUDING THE PART THAT IS MY FAULT.

The Financials headings round, pushed an hour before this one, moved twenty
templates onto the SHAPE - centred h2, centred h5, no band, no icon - and
left every one of them mixed-case with no prefix. It even asked the right
question, "match each page's neighbours rather than one rule", and then
never checked what the neighbours did. Forty of the fifty-four centred
headings in this system carry `ALIVENTE ONLINE - ` and forty-five are
entirely capitals. The round finished half a standard.

WHAT MOVES, MEASURED

  20  Financials + Performance Trends + Vacancy Management
        `Revenue Types` -> `ALIVENTE ONLINE - REVENUE TYPES`
   3  asset_detail, edit_asset, generate_lease_agreement
        already capitals, missing the prefix
   1  finance/cashflow_forecast - the page held up as the example of a good
        heading, and in fact the ONLY one in the system in mixed case with
        no prefix. It reads well because it is centred with no band, which
        is what was being responded to; on casing it was the outlier.
   5  subtitles in capitals -> sentence case
   ---
  29 templates.

EVERY REPLACEMENT IS WRITTEN OUT IN FULL BELOW, not computed. Sentence case
cannot be done by `.capitalize()` without eating proper nouns, and a title
is text a person reads - it deserves to be reviewed as text, in a table,
rather than trusted to a transform.

DELIBERATELY EXCLUDED: `property_assets.html`, whose heading is
`PROPERTY ASSETS - {{ property.prop_name|upper }}`. Prefixing gives
`ALIVENTE ONLINE - PROPERTY ASSETS - APOLLONEON`, with two dashes doing
different jobs. That is the identical shape as the nine `projects/` pages -
`EDIT TASK - {{ task.task_name|upper }}` and its siblings - and Demetri
asked for those to be surveyed before a rule is chosen. Ten pages, one
question, one later round.

HOUSE RULES: idempotent, .bak_hstd backups never overwritten, --check writes
nothing, SELF-CHECK BEFORE WRITING, guards PER FILE.
"""
import os
import re
import sys

CHECK = '--check' in sys.argv
T = os.path.join(os.getcwd(), 'pages', 'templates')
PREFIX = 'ALIVENTE ONLINE - '

# --------------------------------------------------------------------------
# TITLES. before -> after, written out, so a person can read the table.
# --------------------------------------------------------------------------
TITLES = {
    'finance_revenue.html': ('Revenue', 'REVENUE'),
    'finance_revenue_add.html': ('Add Revenue', 'ADD REVENUE'),
    'finance_revenue_edit.html': ('Edit Revenue', 'EDIT REVENUE'),
    'finance_revenue_line_types.html': ('Revenue Line Types',
                                        'REVENUE LINE TYPES'),
    'finance_revenue_line_types_add.html': ('Add Revenue Line Type',
                                            'ADD REVENUE LINE TYPE'),
    'finance_revenue_line_types_edit.html': ('Edit Revenue Line Type',
                                             'EDIT REVENUE LINE TYPE'),
    'finance_revenue_types.html': ('Revenue Types', 'REVENUE TYPES'),
    'finance_revenue_types_add.html': ('Add Revenue Type', 'ADD REVENUE TYPE'),
    'finance_revenue_types_edit.html': ('Edit Revenue Type',
                                        'EDIT REVENUE TYPE'),
    'finance_expense.html': ('Expense', 'EXPENSES'),
    'finance_expense_add.html': ('Add Expense', 'ADD EXPENSE'),
    'finance_expense_edit.html': ('Edit Expense', 'EDIT EXPENSE'),
    'finance_expense_line_types.html': ('Expense Line Types',
                                        'EXPENSE LINE TYPES'),
    'finance_expense_line_types_add.html': ('Add Expense Line Type',
                                            'ADD EXPENSE LINE TYPE'),
    'finance_expense_line_types_edit.html': ('Edit Expense Line Type',
                                             'EDIT EXPENSE LINE TYPE'),
    'finance_expense_types.html': ('Expense Types', 'EXPENSE TYPES'),
    'finance_expense_types_add.html': ('Add Expense Type', 'ADD EXPENSE TYPE'),
    'finance_expense_types_edit.html': ('Edit Expense Type',
                                        'EDIT EXPENSE TYPE'),
    'occupancy_trends.html': ('Performance Trends', 'PERFORMANCE TRENDS'),
    'finance/vacancy_management.html': ('Vacancy Management',
                                        'VACANCY MANAGEMENT'),
    'finance/cashflow_forecast.html': ('Forecasted Cashflows',
                                       'FORECASTED CASHFLOWS'),
    # Already capitals; only the prefix is missing.
    'asset_detail.html': ('ASSET DETAILS', 'ASSET DETAILS'),
    'edit_asset.html': ('EDIT ASSET', 'EDIT ASSET'),
    'generate_lease_agreement.html': ('GENERATE LEASE AGREEMENT',
                                      'GENERATE LEASE AGREEMENT'),
}

# ONE DELIBERATE WORDING CHANGE, flagged rather than slipped in:
# finance_expense.html said `Expense`, singular, while every sibling and the
# menu item say Expenses. It becomes EXPENSES.
REWORDED = {'finance_expense.html'}

# --------------------------------------------------------------------------
# SUBTITLES. Capitals -> sentence case, written out for the same reason.
# --------------------------------------------------------------------------
SUBS = {
    'finance_pl_act.html': (
        '12 MONTH BUDGET INCLUDING ACTUALS INCURRED FOR THE YEAR',
        '12 month budget including actuals incurred for the year'),
    'lease_timeline.html': ('VISUAL LEASE CALENDAR', 'Visual lease calendar'),
    # A raw ampersand in the source, not an entity - taken from the file
    # rather than from what it renders as.
    'notifications.html': ('PROPERTY MANAGEMENT ALERTS & STATUS',
                           'Property management alerts & status'),
    'property_management_dashboard.html': ('VISUAL HUB FOR PROPERTY EXPLORATION',
                                           'Visual hub for property exploration'),
    'finance/financial_indicators.html': ('PROPERTY PERFORMANCE DASHBOARD',
                                          'Property performance dashboard'),
    # Title Case is not sentence case either.
    'finance/cashflow_forecast.html': (
        'Upcoming Revenue and Expense Planning Dashboard',
        'Upcoming revenue and expense planning dashboard'),
}

PAGES = sorted(set(TITLES) | set(SUBS))
for _r in PAGES:
    if not os.path.exists(os.path.join(T, _r.replace('/', os.sep))):
        sys.exit('! %s not found - run from the repo root' % _r)


def load(p):
    with open(p, encoding='utf-8', newline='') as f:
        raw = f.read()
    return raw, ('\r\n' in raw), raw.replace('\r\n', '\n')


FAIL = []


def want(c, m):
    if not c:
        FAIL.append(m)


def one(text, old, new, what):
    """Replace exactly once, or refuse. Whitespace-tolerant on the way in,
       because a heading may be wrapped across lines, but the words must
       match exactly."""
    pat = re.compile(re.escape(old).replace(r'\ ', r'\s+'))
    hits = list(pat.finditer(text))
    if len(hits) != 1:
        sys.exit('! %s: %r matched %d times, expected 1' % (what, old[:60],
                                                            len(hits)))
    return text[:hits[0].start()] + new + text[hits[0].end():]


NOTE = ('        {# HEADING STANDARD - 8 Sep. Title in capitals prefixed '
        '"ALIVENTE ONLINE - "; subtitle in sentence case. See the standards '
        'block at the top of base.html. #}\n')

PREEXISTING = []
CHANGED = {}
for rel in PAGES:
    path = os.path.join(T, rel.replace('/', os.sep))
    orig, crlf, f = load(path)
    if 'HEADING STANDARD - 8 Sep' in f:
        CHANGED[rel] = (path, orig, crlf, f, True)
        continue

    if rel in TITLES:
        was, now = TITLES[rel]
        want(now == now.upper(), '%s: the new title is not capitals' % rel)
        # The <h2> must exist and hold exactly that text.
        m = re.search(r'<h2([^>]*)>\s*<center>\s*(.*?)\s*</center>\s*</h2>',
                      f, re.S)
        want(m is not None, '%s: no centred <h2> to work on' % rel)
        if m:
            cur = re.sub(r'\s+', ' ', m.group(2)).strip()
            want(cur == was,
                 '%s: the heading reads %r, not the %r this round was '
                 'written against' % (rel, cur[:40], was))
            f = f[:m.start()] + '<h2%s><center>%s%s</center></h2>' % (
                m.group(1), PREFIX, now) + f[m.end():]

    if rel in SUBS:
        was, now = SUBS[rel]
        f = one(f, was, now, '%s: the subtitle' % rel)

    # A pointer at the standard, as a Django comment so it does not ship.
    _h2 = f.find('<h2')
    _ls = f.rfind('\n', 0, _h2) + 1
    f = f[:_ls] + NOTE + f[_ls:]
    CHANGED[rel] = (path, orig, crlf, f, False)

# ===========================================================================
# SELF-CHECK - before a byte is written
# ===========================================================================
for rel, (path, orig, crlf, f, done) in CHANGED.items():
    if done:
        continue
    mk = re.sub(r'<(script|style)[^>]*>.*?</\1>', '', f, flags=re.S)
    m = re.search(r'<h2[^>]*>\s*<center>\s*(.*?)\s*</center>\s*</h2>', mk, re.S)
    want(m is not None, '%s: the <h2> vanished' % rel)
    if m:
        t = re.sub(r'\s+', ' ', m.group(1)).strip()
        want(t.startswith(PREFIX), '%s: no prefix - %r' % (rel, t[:40]))
        want(t == t.upper(), '%s: the title is not capitals - %r' % (rel, t))
        want('<i ' not in m.group(1), '%s: an icon crept in' % rel)
        # The words must survive. A prefix is added; nothing is renamed,
        # except the one page listed in REWORDED.
        if rel in TITLES and rel not in REWORDED:
            want(TITLES[rel][0].upper() in t,
                 '%s: the title lost its words - %r' % (rel, t))
    h5 = re.search(r'</h2>\s*(?:\{#.*?#\}\s*)?<h5[^>]*>\s*<center>\s*(.*?)\s*'
                   r'</center>', mk, re.S)
    if h5:
        st = re.sub(r'\s+', ' ', h5.group(1)).strip()
        _letters = [c for c in re.sub(r'\{[{%#][^}]*[}%#]\}', '', st)
                    if c.isalpha()]
        want(not _letters or not all(c.isupper() for c in _letters),
             '%s: the subtitle is still all capitals - %r' % (rel, st[:40]))
    want('HEADING STANDARD - 8 Sep' in f, '%s: unexplained' % rel)
    # The pointer must be a Django comment, which does not ship.
    want('{# HEADING STANDARD' in f, '%s: the note would be sent to the '
         'browser - use a Django comment' % rel)

    stack, fault = [], None
    OPEN = {'if': 'endif', 'for': 'endfor', 'block': 'endblock',
            'with': 'endwith'}
    CLOSE = {v: k for k, v in OPEN.items()}
    for mm in re.finditer(r'\{%\s*(\w+)', f):
        t2 = mm.group(1)
        if t2 in OPEN:
            stack.append(t2)
        elif t2 in CLOSE and (not stack or OPEN[stack.pop()] != t2):
            fault = t2
            break
    want(fault is None and not stack,
         '%s: Django tags do not balance (%s)' % (rel, fault or stack))
    # THE DELTA, NOT THE ABSOLUTE. This round edits heading TEXT and adds a
    # Django comment; it cannot change structure, so the claim is that the
    # div balance is UNCHANGED - not that it is zero.
    #
    # Asserting zero failed asset_detail.html, which has a genuinely
    # unclosed <div class="alv-card"> at markup line 201 - the maintenance
    # card. Pre-existing, unrelated to headings, and reported rather than
    # fixed here: folding a structural repair into a text round is how a
    # round stops being reviewable.
    _wasmk = re.sub(r'<(script|style)[^>]*>.*?</\1>', '',
                    orig.replace('\r\n', '\n'), flags=re.S)
    _d_now = len(re.findall(r'<div\b', mk)) - len(re.findall(r'</div>', mk))
    _d_was = len(re.findall(r'<div\b', _wasmk)) - len(re.findall(r'</div>',
                                                                 _wasmk))
    want(_d_now == _d_was,
         '%s: the round changed the <div> balance (%+d -> %+d)'
         % (rel, _d_was, _d_now))
    if _d_now:
        PREEXISTING.append('%s (%+d)' % (rel, _d_now))
    for blk in re.findall(r'<style[^>]*>(.*?)</style>', f, re.S):
        want(blk.count('{') == blk.count('}'), '%s: unbalanced braces' % rel)

want('property_assets.html' not in CHANGED,
     'property_assets is in scope - it has a record name in its title and '
     'was deliberately left for the projects/ survey')

if PREEXISTING:
    print('  NOTE  pre-existing unbalanced <div>s, untouched by this round: %s'
          % ', '.join(PREEXISTING))

if FAIL:
    print('\n! SELF-CHECK FAILED - nothing written\n')
    for x in FAIL[:24]:
        print('   - %s' % x)
    sys.exit(1)

n = 0
for rel in PAGES:
    path, orig, crlf, f, done = CHANGED[rel]
    if done:
        print('  %-44s already patched' % rel)
        continue
    out = f.replace('\n', '\r\n') if crlf else f
    print('  %-44s %d -> %d' % (rel, len(orig.encode('utf-8')),
                                len(out.encode('utf-8'))))
    n += 1
    if CHECK:
        continue
    bak = path + '.bak_hstd'
    if not os.path.exists(bak):
        with open(bak, 'w', encoding='utf-8', newline='') as fh:
            fh.write(orig)
    with open(path, 'w', encoding='utf-8', newline='') as fh:
        fh.write(out)

print('\n  --check: nothing written (%d file(s) would change).' % n if CHECK
      else '\n  done - %d file(s).' % n)
