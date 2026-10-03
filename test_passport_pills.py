# -*- coding: utf-8 -*-
"""test_passport_pills.py - Section PA round PA-2, 3 Oct 2026.

Demetri, 3 Oct 2026: "Do the row actions and badges next." And of the Type
column: "One neutral pill".

==========================================================================
TEN BADGES, AND TEN LABELS THE MODEL ALREADY KNEW
==========================================================================
The Type cell was a SIX-BRANCH chain writing out "Passport", "ID",
"Driver's License", "Visa" and "ARC" - beside a {% else %} that already
called get_document_type_display. Status was four more. PA-1's defect
again, in the row instead of the dropdown.

AND FIVE OF THE TEN BADGES HAD NO RULE AT ALL. Section 2 renders them:
badge-primary, badge-dark and badge-secondary are Bootstrap classes this
app never defined, so Passport, ARC and Inactive drew as plain text with
no pill while Visa and Active drew as solid blocks. The "five colours"
were two.

==========================================================================
SECTION 3 IS THE ONE THAT WILL MATTER LATER
==========================================================================
The pill tone is written WHOLE in each branch, not assembled as
"alv-pill-" plus a word. SG-2 found an eighth hand-rolled segmented
control that had been invisible to every census for a month, because its
class was built across a template tag and the string btn-info never
appeared in the file. This suite refuses an assembled pill class, and
proves the check can fail by building one.

AND SECTION 5 IS A CORRECTION. The mobile action bar was down as a
pattern the house had replaced. Counting says otherwise - 23 pages use it
- so it is untouched, and the suite holds the count so that "left alone"
stays a decision rather than an oversight.
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
import ast
import shutil
import tempfile

ROOT = os.getcwd()
sys.path.insert(0, ROOT)
try:
    from alv_rounds import as_left_by
except Exception:
    as_left_by = None
import alv_tree

SUFFIX = '.bak_passpills'
ME = 'test_passport_pills.py'
PATCHER = 'apply_passport_pills.py'
PS1 = 'Push-PendingChanges.ps1'

SCRATCH = tempfile.mkdtemp(prefix='alv_passpills_')

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
            for line in str(detail).split('\n')[:8]:
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


def code(p):
    return alv_tree.code_only(now(p))

PAGE = alv_tree.path_of('passport_management.html')
BASE = alv_tree.path_of('base.html')
SRC = alv_tree.code_only(now(PAGE))
OLD = alv_tree.code_only(was(PAGE)) if was(PAGE) else ''

TOKENS = [('#f8f9fa', 'var(--alv-surface)', 3),
          ('#e9ecef', 'var(--alv-surface-deep)', 1),
          ('#dee2e6', 'var(--alv-line)', 1),
          ('#495057', 'var(--alv-ink-soft)', 2),
          ('#adb5bd', 'var(--alv-ink-faint)', 2),
          ('#dc3545', 'var(--alv-bad)', 1)]

ROWS = [('Demetri Manias', 'passport', 'Passport', 'active', 'Active'),
        ('Angela Manias', 'visa', 'Visa', 'renewal', 'Applied for Renewal'),
        ('Erene Manias', 'arc', 'Alien Registration Card', 'inactive',
         'Inactive')]


def css_of(x):
    return '\n'.join(re.findall(r'<style[^>]*>(.*?)</style>', x, re.S | re.I))


# ==========================================================================
head('1. NO BOOTSTRAP BADGE, AND TEN LABELS THE MODEL OWNS')
# ==========================================================================
left = re.findall(r'class="[^"]*\bbadge\s+badge-\w+', SRC)
ok(not left, 'not one Bootstrap badge on the page', left[:4])
if OLD:
    had = re.findall(r'class="[^"]*\bbadge-(\w+)', OLD)
    ok(len(had) == 10, 'CONTROL: the backup had %d' % len(had),
       sorted(set(had)))
else:
    skip('CONTROL: the backup had ten', 'no backup')

for probe in ('get_document_type_display', 'get_status_display'):
    ok(probe in SRC, 'the row calls %s' % probe)
for word in ("Driver's License", '>Visa<', '>ARC<',
             '>Applied for Renewal<', '>Inactive<'):
    ok(word not in SRC, '%-24s is not written into the row' % word)
    if OLD:
        ok(word in OLD, '  CONTROL: and the backup wrote it')

ok(len(re.findall(r'\{%\s*if passport\.document_type', SRC)) == 0,
   'the Type cell has no branch at all now - one pill, one label')
if OLD:
    ok(len(re.findall(r'\{%\s*el?i?f?\s*passport\.document_type', OLD)) >= 4,
       'CONTROL: the backup branched on document_type five times')

# ==========================================================================
head('2. WHAT THEY ACTUALLY DREW - AND FIVE OF TEN DREW NOTHING')
# ==========================================================================
try:
    from playwright.sync_api import sync_playwright
except Exception:
    sync_playwright = None


def one_row(src, row):
    """The page's REAL <tr>, with its {% if %} chains resolved for one
    document. Not a hand-written fixture: the branches are the thing
    under test, so they are evaluated rather than deleted."""
    i = src.index('{% for passport in passports %}')
    j = src.index('{% endfor %}', i)
    tr = re.sub(r'\{#.*?#\}', '', src[i + 31:j], flags=re.S)
    holder, dt, dtl, st, stl = row
    ctx = {'passport.holder_name': holder, 'passport.document_type': dt,
           'passport.get_document_type_display': dtl,
           'passport.status': st, 'passport.get_status_display': stl}

    def truth(expr):
        m = re.match(r"passport\.(\w+) == '([^']*)'", expr.strip())
        if m:
            return ctx.get('passport.' + m.group(1)) == m.group(2)
        return True

    while True:
        m = re.search(r'\{%\s*if\s+([^%]+?)\s*%\}', tr)
        if not m:
            break
        depth, k = 1, m.end()
        branches, cond, start = [], m.group(1), m.end()
        end = None
        pat = re.compile(r'\{%\s*(if|elif|else|endif)\b([^%]*)%\}')
        while depth:
            mm = pat.search(tr, k)
            if not mm:
                break
            kw = mm.group(1)
            if kw == 'if':
                depth += 1
                k = mm.end()
                continue
            if depth == 1:
                branches.append((cond, tr[start:mm.start()]))
                cond = (mm.group(2).strip() if kw == 'elif'
                        else ('ELSE' if kw == 'else' else None))
                start = mm.end()
            if kw == 'endif':
                depth -= 1
                if depth == 0:
                    end = mm.end()
                    break
            k = mm.end()
        chosen = ''
        for c, b in branches:
            if c == 'ELSE' or truth(c):
                chosen = b
                break
        tr = tr[:m.start()] + chosen + tr[end:]
    for k2, v in ctx.items():
        tr = tr.replace('{{ %s }}' % k2, v)
        tr = re.sub(r'\{\{\s*' + re.escape(k2) + r'\|[^}]*\}\}', v, tr)
    tr = re.sub(r'\{\{[^}]*\}\}', 'x', tr)
    tr = re.sub(r'\{%[^%]*%\}', '', tr)
    return tr


def draw(src):
    trs = ''.join(one_row(src, r) for r in ROWS)
    html = ('<!doctype html><html><head><meta charset="utf-8">'
            '<style>%s</style><style>%s</style></head>'
            '<body style="margin:0;padding:16px"><div class="table-container">'
            '<table class="table alv-table"><tbody>%s</tbody></table></div>'
            '</body></html>'
            % (css_of(alv_tree.code_only(now(BASE))), css_of(src), trs))
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        pg = b.new_page(viewport={'width': 1280, 'height': 800})
        pg.set_content(html)
        pg.wait_for_timeout(150)
        r = pg.evaluate("""() => {
          const out = {pills: [], cells: []};
          for (const e of document.querySelectorAll('.badge, .alv-pill')) {
            const s = getComputedStyle(e);
            out.pills.push({t: e.textContent.trim(), bg: s.backgroundColor,
                            ink: s.color});
          }
          for (const c of document.querySelectorAll('td.desktop-action-cell')) {
            const b = [...c.querySelectorAll('.icon-action-btn')];
            const g = [];
            for (let i = 1; i < b.length; i += 1) {
              g.push(Math.round(b[i].getBoundingClientRect().left
                              - b[i - 1].getBoundingClientRect().right));
            }
            out.cells.push({n: b.length, gaps: g});
          }
          return out;
        }""")
        b.close()
    return r


if sync_playwright is None or not OLD:
    for _ in range(6):
        skip('what they drew', 'playwright or backup missing')
else:
    A = draw(was(PAGE))
    B = draw(now(PAGE))

    def clear(p):
        return p['bg'] in ('rgba(0, 0, 0, 0)', 'transparent')

    blank = [p['t'] for p in A['pills'] if clear(p)]
    ok(len(blank) >= 3,
       'CONTROL: %d of the backup\'s badges drew with NO background at all '
       '- badge-primary, badge-dark and badge-secondary are Bootstrap '
       'classes this app never defined' % len(blank), blank)
    ok(not [p['t'] for p in B['pills'] if clear(p)],
       'every pill now draws a pill')
    solid = [p for p in A['pills'] if p['ink'] == 'rgb(255, 255, 255)']
    ok(len(solid) >= 2,
       '  and %d drew as a solid block with white text' % len(solid),
       [p['t'] for p in solid])
    ok(not [p for p in B['pills'] if p['ink'] == 'rgb(255, 255, 255)'],
       '  where the house pill is soft fill with coloured ink')

    tones = {p['t']: p['ink'] for p in B['pills']}
    ok(tones.get('Active') == 'rgb(30, 125, 79)',
       'Active is the good tone', tones.get('Active'))
    ok(tones.get('Applied for Renewal') == 'rgb(142, 98, 7)',
       'Applied for Renewal is the attention tone',
       tones.get('Applied for Renewal'))
    ok(tones.get('Passport') == tones.get('Visa')
       == tones.get('Alien Registration Card'),
       'and all three TYPES are the same neutral - on this page colour '
       'means state', {k: v for k, v in tones.items()
                      if k in ('Passport', 'Visa',
                               'Alien Registration Card')})

    # THE WRAPPER, MEASURED. Without it the icons take whatever the cell
    # gives them; with it they take .row-actions' 6px.
    ga = sorted(set(g for c in A['cells'] for g in c['gaps']))
    gb = sorted(set(g for c in B['cells'] for g in c['gaps']))
    ok(gb == [6], 'the icons sit 6px apart - the house gap', gb)
    ok(ga != gb, 'CONTROL: they did not before - %s' % ga)
    ok(all(c['n'] == A['cells'][i]['n'] for i, c in enumerate(B['cells'])),
       'and the same number of icons in each row')

# ==========================================================================
head('3. THE PILL CLASS IS WRITTEN WHOLE - THE SG-2 LESSON')
# ==========================================================================
ok(not re.search(r'alv-pill-\s*\{', SRC),
   'no pill tone is assembled across a template tag')
tones = sorted(set(re.findall(r'\balv-pill-\w+', SRC)))
ok(tones == ['alv-pill-attn', 'alv-pill-good', 'alv-pill-neutral'],
   'the three tones are greppable: %s' % ', '.join(tones))
# AND THE CHECK CAN FAIL. Built here rather than asserted, because the
# whole point is that an assembled class READS fine.
sneaky = '<span class="alv-pill alv-pill-{% if x %}good{% endif %}">y</span>'
ok(bool(re.search(r'alv-pill-\s*\{', sneaky)),
   'CONTROL: and a class built across a tag IS caught')
ok(not re.findall(r'\balv-pill-\w+', sneaky),
   '  while a grep for the tone finds nothing in it - which is how SG-2 '
   'hid a control for a month')

# ==========================================================================
head('4. ONE WRAPPER, ROUND ALL FOUR BRANCHES')
# ==========================================================================
n = len(re.findall(r'<div class="row-actions">', SRC))
ok(n == 1, '%d row-actions wrapper on the page' % n)
if n == 1:
    i = SRC.index('<div class="row-actions">')
    j = SRC.index('</td>', i)
    ok(len(re.findall(r'class="icon-action-btn', SRC[i:j])) == 9,
       'and it holds all 9 icons - one wrapper, not one per branch')
ok(OLD and 'row-actions' not in OLD,
   'CONTROL: the backup had none')

# ==========================================================================
head('5. THE MOBILE ACTION BAR IS LEFT ALONE, AND WHY')
# ==========================================================================
# A CORRECTION, RECORDED. This was down as a pattern the house component
# had replaced. It has not: counting says it is the live house pattern for
# row actions on a phone.
users = sorted(alv_tree.rel(p) for p in alv_tree.templates()
               if re.search(r'class="[^"]*\bmobile-action-bar\b',
                            alv_tree.code_only(now(p))))
ok(len(users) >= 20,
   '%d pages use the mobile action bar - it is the house pattern, not a '
   'leftover' % len(users))
for p in ('properties.html', 'tenant.html', 'suppliers.html',
          'projects/projects.html'):
    ok(p in users, '  including %s' % p)
ok(alv_tree.rel(PAGE) in users, 'and this page still does')


def mobile_cell(x):
    i = x.index('<td class="mobile-action-bar">')
    return re.sub(r'\s+', ' ', x[i:x.index('</td>', i)])


if OLD:
    ok(mobile_cell(SRC) == mobile_cell(OLD),
       'its cell is character for character what it was')
else:
    skip('its cell is character for character what it was', 'no backup')

# ==========================================================================
head('6. SIX HEXES, SIX TOKENS')
# ==========================================================================
hexes = re.findall(r'#[0-9a-fA-F]{3,6}\b', SRC)
ok(not hexes, 'not one hex left on the page', hexes[:5])
for hexv, token, n_ in TOKENS:
    ok(token in SRC, '%-8s -> %s' % (hexv, token))
    if OLD:
        got = len(re.findall(re.escape(hexv), OLD, re.I))
        ok(got == n_, '  CONTROL: the backup used it %d time(s)' % got)

# ==========================================================================
head('7. AND THE EXPIRY RULE IS THE SAME RULE')
# ==========================================================================
# Demetri: leave the expiry question as it currently is. So its colour
# moves onto the token and nothing else about it does.
def rule(x, sel):
    m = re.search(re.escape(sel) + r'[^{}]*\{([^}]*)\}', x)
    return re.sub(r'\s+', ' ', m.group(1)).strip() if m else None


a, b = (rule(OLD, '.expiry-expired') if OLD else None,
        rule(SRC, '.expiry-expired'))
ok(b, 'the expiry rule is still there')
if a:
    ok(a.replace('#dc3545', 'var(--alv-bad)') == b,
       'and differs from the backup by its colour and nothing else',
       'was %s\nnow %s' % (a, b))
# NOTED, NOT CHANGED: expired and expiring-soon share one rule, so a
# passport that expired last year looks exactly like one expiring in May.
ok('.expiry-expired,' in SRC and '.expiry-soon' in SRC,
   'NOTED: expired and expiring-soon still share one rule - a document '
   'that expired last year looks like one expiring in May. Left as it is, '
   'by his instruction.')

# ==========================================================================
head('8. REGISTERED')
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
