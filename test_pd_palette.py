# -*- coding: utf-8 -*-
"""test_pd_palette.py - Section PD round PD-1, 4 Oct 2026.

property_detail.html is 1,992 lines carrying 227 local CSS rules, and
before this round the only house component on it was the action bar.
PD-1 takes the palette: the table headers and the badges. PD-2 takes the
tables themselves; PD-3 takes what is left.

==========================================================================
SECTION 1 RENDERS EVERY TABLE, AND THAT IS NOT DECORATION
==========================================================================
The census that scoped this round searched for #343a40 and found FIVE
table headers. It missed two: categories-table and assets-table colour
the ROW rather than the cell, in #2c3e50, with a #34495e cell border.
The first build of the round left those two standing dark beside five
that had changed - which is worse than seven that match - and the RENDER
is what showed it.

So this suite does not ask which rules the page contains. It paints every
table in the page and reads the computed background off the header, which
is a question the next odd selector cannot hide from.

==========================================================================
SECTION 2 - A COUNT IS NOT A VERDICT
==========================================================================
Active Warranties and Expired Warranties were a green pill and a red
pill on two NUMBERS, one of them a hex written on the element. Demetri,
asked: "Neutral - they are numbers."

That is the ageing decision one page along. Green to red is a verdict
vocabulary; AG-1 took it off a scale this morning because ageing is a
progression, and a tally is not a verdict either. Status, Available,
Current and Overdue ARE verdicts and keep good and bad.

So the gate is not "no red on this page". It is: red appears on the
things that are judgements and nowhere else.
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
import os
import re
import sys
import shutil
import tempfile

ROOT = os.getcwd()
sys.path.insert(0, ROOT)
try:
    from alv_rounds import as_left_by
except Exception:
    as_left_by = None
import alv_tree

SUFFIX = '.bak_pdpalette'
ME = 'test_pd_palette.py'
PATCHER = 'apply_pd_palette.py'
PS1 = 'Push-PendingChanges.ps1'

SCRATCH = tempfile.mkdtemp(prefix='alv_pdpalette_')

passed = failed = skipped = 0


def ok(cond, msg, detail=''):
    global passed, failed
    if cond:
        passed += 1
        print('  ok   %s' % msg)
    else:
        failed += 1
        print('  FAIL %s' % msg)
        if detail:
            for line in str(detail).split('\n')[:10]:
                print('         %s' % line)
    return cond


def skip(msg, why):
    global skipped
    skipped += 1
    print('  --   %s  (%s)' % (msg, why))


def read(p):
    with open(p, encoding='utf-8', errors='replace') as f:
        return f.read().replace('\r\n', '\n')


def head(t):
    print('\n' + '=' * 74 + '\n' + t + '\n' + '=' * 74)


def now(p):
    return as_left_by(p, SUFFIX, read) if as_left_by else read(p)


def was(p):
    return read(p + SUFFIX) if os.path.isfile(p + SUFFIX) else ''


PAGE = alv_tree.path_of('property_detail.html')
BASE = alv_tree.path_of('base.html')
BOOT = os.path.join(ROOT, 'test_fixture_bootstrap413.css')

RAW = now(PAGE)
OLDRAW = was(PAGE)
SRC = alv_tree.code_only(RAW)
OLD = alv_tree.code_only(OLDRAW) if OLDRAW else ''


def css_of(x):
    return '\n'.join(re.findall(r'<style[^>]*>(.*?)</style>', x, re.S | re.I))


def classes_worn(markup):
    """Every class TOKEN the markup wears, Django tags removed.

    ASKED FOR THE TOKEN, NOT THE SUBSTRING. The patcher's own gate first
    tested `'badge' in body` and refused to run, because this page also
    carries .renewal-status-badge and .status-badge - two different
    components whose names merely end in the word."""
    body = re.sub(r'<style[^>]*>.*?</style>', '', markup, flags=re.S)
    body = re.sub(r'<script[^>]*>.*?</script>', '', body, flags=re.S)
    body = re.sub(r'\{#.*?#\}', '', body, flags=re.S)
    out = set()
    for m in re.finditer(r'class="([^"]*)"', body):
        v = re.sub(r'\{%[^%]*%\}', ' ', m.group(1))
        v = re.sub(r'\{\{[^}]*\}\}', ' ', v)
        out |= set(v.split())
    return out


WORN = classes_worn(RAW)
WORN_OLD = classes_worn(OLDRAW) if OLDRAW else set()

# ==========================================================================
head('1. EVERY TABLE HEADER ON THIS PAGE, PAINTED')
# ==========================================================================
try:
    from playwright.sync_api import sync_playwright
except Exception:
    sync_playwright = None


def detag(s):
    s = re.sub(r'\{%\s*(block|endblock|extends|load|csrf_token)[^%]*%\}', '', s)
    s = re.sub(r'\{%\s*(else|endif|endfor|empty)\s*%\}', '', s)
    s = re.sub(r'\{%[^%]*%\}', '', s)
    s = re.sub(r'\{\{[^}]*\}\}', 'Sample', s)
    return re.sub(r'\{#.*?#\}', '', s, flags=re.S)


def paint(raw, probe):
    body = re.sub(r'<style[^>]*>.*?</style>', '', raw, flags=re.S | re.I)
    body = re.sub(r'<script[^>]*>.*?</script>', '', body, flags=re.S | re.I)
    html = ('<!doctype html><html><head><meta charset="utf-8">'
            '<style>%s</style><style>%s</style><style>%s</style></head>'
            '<body style="margin:0">%s</body></html>'
            % (read(BOOT), css_of(alv_tree.code_only(now(BASE))),
               css_of(raw), detag(body)))
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        pg = b.new_page(viewport={'width': 1180, 'height': 1000})
        pg.set_content(html)
        pg.wait_for_timeout(280)
        r = pg.evaluate(probe)
        b.close()
    return r


HEAD_PROBE = """() => {
  const tok = v => { const d = document.createElement('span');
    d.style.color = 'var(' + v + ')'; document.body.appendChild(d);
    const c = getComputedStyle(d).color; d.remove(); return c; };
  const o = {rows: [], surface: tok('--alv-surface'),
             inkStrong: tok('--alv-ink-strong')};
  for (const t of document.querySelectorAll('table')) {
    const th = t.querySelector('th'); if (!th) continue;
    const s = getComputedStyle(th);
    const bg = s.backgroundColor === 'rgba(0, 0, 0, 0)'
      ? getComputedStyle(th.parentElement).backgroundColor
      : s.backgroundColor;
    o.rows.push({cls: (t.className || '').toString().slice(0, 34) || '(none)',
                 bg: bg, fg: s.color, up: s.textTransform});
  }
  return o;
}"""

if sync_playwright is None or not OLD:
    for _ in range(6):
        skip('the table headers', 'playwright or backup missing')
    A = None
else:
    A = paint(RAW, HEAD_PROBE)
    B = paint(OLDRAW, HEAD_PROBE)
    print('   %-36s %-22s %s' % ('TABLE', 'BEFORE', 'AFTER'))
    for b, a in zip(B['rows'], A['rows']):
        print('   %-36s %-22s %s' % (a['cls'], b['bg'], a['bg']))

    ok(len(A['rows']) == 7, 'the page paints %d tables' % len(A['rows']))
    ok(len(B['rows']) == len(A['rows']),
       '  the same number before and after - none lost')
    # THE SURFACE TOKEN, read out of the live stylesheet rather than typed
    # here, so the check follows base if base ever moves it.
    ok(all(r['bg'] == A['surface'] for r in A['rows']),
       'every header draws on --alv-surface (%s)' % A['surface'],
       '\n'.join('%s: %s' % (r['cls'], r['bg'])
                 for r in A['rows'] if r['bg'] != A['surface']))
    ok(all(r['up'] == 'uppercase' for r in A['rows']),
       '  and every one of them is uppercase, as the house header is')
    darks = sorted({r['bg'] for r in B['rows']})
    ok(len(darks) == 2,
       'CONTROL: before this round they wore %d DIFFERENT darks: %s'
       % (len(darks), ', '.join(darks)),
       'two colours, two selectors, one bar - which is why a search for '
       'one of them found five tables and missed two')
    ok(all(r['bg'] != A['surface'] for r in B['rows']),
       '  and not one of them was the house surface')

# ==========================================================================
head('2. A COUNT IS NOT A VERDICT')
# ==========================================================================
boot = [c for c in WORN
        if re.fullmatch(r'badge(-(primary|secondary|success|danger|warning'
                        r'|info|light|dark|available|not-available))?', c)]
ok(not boot, 'no Bootstrap badge class is worn anywhere on the page',
   ', '.join(sorted(boot)))
oldboot = [c for c in WORN_OLD
           if re.fullmatch(r'badge(-\w[\w-]*)?', c)]
ok(len(oldboot) >= 5,
   'CONTROL: the backup wore %d of them: %s'
   % (len(oldboot), ', '.join(sorted(oldboot))))
ok('alv-pill' in WORN, 'the house pill is worn instead')

# THE TWO COUNTS, by name. Read out of the markup so a later edit that
# re-colours them is caught rather than assumed away.
for label, var in (('Active Warranties', 'active_warranties'),
                   ('Expired Warranties', 'expired_warranties')):
    m = re.search(r'<span class="([^"]*)">\s*\{\{\s*%s[^}]*\}\}' % var, SRC)
    cls = m.group(1) if m else ''
    ok('alv-pill-neutral' in cls,
       '%s is a NEUTRAL pill - it is a count, not a verdict' % label,
       cls or 'no pill found for %s' % var)
if OLD:
    ok('style="background-color: #dc3545' in OLD,
       '  CONTROL: Expired Warranties was a hex written ON the element')
ok('style="background-color: #dc3545' not in SRC,
   '  and no colour is written on an element any more')

# AND THE VERDICTS KEEP THEIR TONES.
VERDICTS = [
    ('prop_status', 'alv-pill-good', 'alv-pill-neutral'),
    ('prop_available_for_rent', 'alv-pill-good', 'alv-pill-neutral'),
    ('tenant_current', 'alv-pill-good', 'alv-pill-neutral'),
]
for var, good, other in VERDICTS:
    # CONCATENATED, NOT FORMATTED. `%` is a format character AND the
    # opening of a Django tag, so '{%' + '[^%]*%s' % var raises
    # ValueError: unsupported format character. Third time this tree has
    # paid for that one.
    m = re.search('<span class="alv-pill \\{%[^%]*' + re.escape(var)
                  + '[^}]*\\}[^"]*"', SRC)
    cls = m.group(0) if m else ''
    ok(good in cls and other in cls,
       '%s keeps good and neutral - it is a verdict' % var, cls[:110])
m = re.search('<span class="alv-pill \\{%\\s*if invoice\\.overdue[^"]*"', SRC)
ok(m is not None and 'alv-pill-bad' in m.group(0),
   'an OVERDUE invoice still reads bad - it is the one red left, and it '
   'is red on the Invoices list too', (m.group(0)[:110] if m else 'not found'))

# ==========================================================================
head('3. THE RULES WITH NO CALLER LEFT ARE GONE')
# ==========================================================================
# A round that removes the last caller of a rule owns the rule.
for sel in ('.badge', '.badge-secondary', '.badge-light', '.badge-danger',
            '.badge-available', '.badge-not-available'):
    ok(re.search(re.escape(sel) + r'\s*[,{]', SRC) is None,
       '%s is gone with its last caller' % sel)
if OLD:
    ok(len(re.findall(r'^\.badge \{', OLD, re.M)) == 2,
       'CONTROL: .badge was declared TWICE in the backup, 138 lines apart '
       'and with different values, so the first never rendered')

# ==========================================================================
head('4. NOTHING NEW WAS ADDED TO THE PALETTE')
# ==========================================================================
hx = re.findall(r'#[0-9a-fA-F]{3,8}\b', SRC)
oldhx = re.findall(r'#[0-9a-fA-F]{3,8}\b', OLD) if OLD else []
print('   hexes  before %d uses / %d distinct   after %d / %d'
      % (len(oldhx), len(set(h.lower() for h in oldhx)),
         len(hx), len(set(h.lower() for h in hx))))
ok(len(hx) < len(oldhx), 'the page carries fewer colour literals than before',
   '%d -> %d' % (len(oldhx), len(hx)))
new = set(h.lower() for h in hx) - set(h.lower() for h in oldhx)
ok(not new, '  and not one value this round introduced', ', '.join(sorted(new)))
for gone in ('#343a40', '#2c3e50', '#34495e'):
    was_n = oldhx.count(gone) if OLD else 0
    now_n = hx.count(gone)
    ok(now_n < was_n or was_n == 0,
       '  %s: %d uses -> %d' % (gone, was_n, now_n))
ok(SRC.count('!important') < OLD.count('!important') if OLD else True,
   'and fewer !important: %d -> %d'
   % (OLD.count('!important') if OLD else -1, SRC.count('!important')))

# ==========================================================================
head('5. REGISTERED')
# ==========================================================================
rounds = read(os.path.join(ROOT, 'alv_rounds.py'))
ok("'%s'" % SUFFIX in rounds, '%s is in alv_rounds.ROUNDS' % SUFFIX)
ps = read(os.path.join(ROOT, PS1))
ok("'%s'" % ME in ps, '%s is in the $suites list' % ME)
ok(os.path.isfile(os.path.join(ROOT, PATCHER)), '%s is on disk' % PATCHER)

shutil.rmtree(SCRATCH, ignore_errors=True)
print('')
print('=' * 74)
print('  %d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
