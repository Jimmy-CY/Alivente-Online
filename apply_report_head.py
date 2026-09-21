# -*- coding: utf-8 -*-
"""apply_report_head.py - one report title, owned by base; the brand on
paper; and the two dead title-deed templates gone.

    python apply_report_head.py --check     dry run, nothing written
    python apply_report_head.py             apply

Run from the repo root. Idempotent: a second run reports nothing to do.

WHAT WAS MEASURED (21 Sep, claude/report_title_survey.md)

  Eleven business report screens build their title row three ways, and
  base defined none of them. Title colour #2c3e50 on seven and the ink
  token on two; subtitle 1.4, 1.2 or 1.1rem, in three different greys -
  two print the date as dark as the title; on a phone the title shrinks
  to one of four sizes and is centred on three, left on the rest. No
  report prints a brand at the top - base records that it belongs here.

  title_deed_report.html is rendered by nothing - its view returns JSON
  that nothing calls. properties_title_deed.html is rendered by a view
  that never passes the `property` it reads, so it would draw
  "TITLE DEED ()"; nothing links to it, and its upload/delete handling
  duplicates Administration's title_deeds_management.

WHAT THIS DOES - agreed 21 Sep

  1. base gains ALV REPORT HEAD v1: .alv-report-head (the row: titles
     left, Back or a figure right), .alv-report-titles, .alv-report-title
     (1.8rem bold capitals, ink), .alv-report-sub (1.4rem, soft ink) and
     .alv-report-brand - ALIVENTE ONLINE above the title, hidden on
     screen and shown on paper. On a phone the row stacks, centred, the
     title at 1.25rem and the subtitle at 1rem, Back full width.
  2. The nine report screens that use the title-row shape take it; their
     own rules for the row, the titles and the phone Back go. Text,
     Django tags and everything else on the page are unchanged.
     comments_report is NOT in this round: its header is the banner that
     test_banner_pages and test_comments_report - two of the five
     off-gate suites - are about, so it goes with that item (B11).
  3. title_deed_report.html and properties_title_deed.html are deleted,
     with their two views, two URLs and the access-rule entry.
  4. test_table_tenant_report.py pinned tenant_report's own title rules
     as kept; it now reads them from the file as its round left it.
     alv_rounds.py learns this round; test_report_head.py goes on the gate.
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

import ast
import os
import re
import sys

CHECK = '--check' in sys.argv
T = os.path.join('pages', 'templates')
if not os.path.isdir(T):
    sys.exit('! pages/templates not found - run from the repo root')

SUFFIX = '.bak_reporthead'
SUITE = 'test_report_head.py'
PS1 = 'Push-PendingChanges.ps1'
BASE = os.path.join(T, 'base.html')
ANCHOR = '/* /ALV MODAL HEAD v1 */'
MARK_OPEN = '/* ALV REPORT HEAD v1'

PAGES = ['property_report.html', 'tenant_report.html', 'supplier_report.html',
         'open_invoices_report.html', 'lease_renewal_report.html',
         'resolved_issues_report.html', 'friday_status_report.html',
         'tenant_payment_days.html', 'lease_agreement_report.html']
DEAD = ['title_deed_report.html', 'properties_title_deed.html']
BRAND = '<div class="alv-report-brand">ALIVENTE ONLINE</div>'

# Rules the page wrote for the row that base now owns. Only these
# selectors, only as a whole rule - top level or inside a media block.
GONE_SELECTORS = ('.header-container', '.report-title-container',
                  '.title-wrapper', '.report-title-main', '.report-title-sub',
                  '.report-title', '.report-subtitle')
PHONE_BACK = '.back-button'

BLOCK = """/* ALV REPORT HEAD v1 - the title row every business report shares.
   Titles on the left, Back or a headline figure on the right. The title
   is a label, so capitals, in ink; the subtitle - a date, a period, the
   record - in the soft ink, a size down. ALIVENTE ONLINE sits above the
   title on paper only: since 8 Sep no heading carries the brand, and a
   printed or emailed report is the one place it is the content rather
   than chrome. On a phone the row stacks and centres. See
   test_report_head.py. */
.alv-report-head {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 16px;
    margin-bottom: 24px;
}
.alv-report-titles {
    display: flex;
    flex-direction: column;
    align-items: flex-start;
    flex: 1;
    min-width: 0;
}
.alv-report-title {
    font-size: 1.8rem;
    font-weight: 700;
    color: var(--alv-ink);
    text-transform: uppercase;
    margin: 0;
    overflow-wrap: anywhere;
}
.alv-report-sub {
    font-size: 1.4rem;
    font-weight: 400;
    color: var(--alv-ink-soft);
    margin: 5px 0 0 0;
    overflow-wrap: anywhere;
}
.alv-report-brand { display: none; }
@media screen and (max-width: 768px) {
    .alv-report-head {
        flex-direction: column;
        align-items: stretch;
        gap: 12px;
        margin-bottom: 16px;
    }
    .alv-report-titles { align-items: center; text-align: center; }
    .alv-report-title { font-size: 1.25rem; }
    .alv-report-sub { font-size: 1rem; }
    .alv-report-head > .btn {
        width: 100%;
        justify-content: center;
        text-align: center;
        padding: 10px 12px;
    }
}
@media print {
    .alv-report-brand {
        display: block;
        margin: 0 0 4px 0;
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 0.14em;
        color: var(--alv-accent-ink);
    }
}
/* /ALV REPORT HEAD v1 */"""

report, problems = [], []
planned = {}
deletes = []
CRLF = {}


def read(p):
    with open(p, encoding='utf-8', newline='') as f:
        raw = f.read()
    CRLF[p] = '\r\n' in raw
    return raw.replace('\r\n', '\n')


def write(p, text):
    if CRLF.get(p):
        text = text.replace('\n', '\r\n')
    with open(p, 'w', encoding='utf-8', newline='') as f:
        f.write(text)


def plan(path, old, new, what):
    cur = planned[path][1] if path in planned else read(path)
    if cur.count(old) != 1:
        problems.append('%s: %s - anchor found %d time(s), expected 1'
                        % (path, what, cur.count(old)))
        return False
    orig = planned[path][0] if path in planned else cur
    planned[path] = (orig, cur.replace(old, new, 1))
    return True


def rule_re(sel):
    return re.compile(r'(?m)^[ \t]*' + re.escape(sel) + r'[ \t]*\{[^{}]*\}'
                      r'[ \t]*\n')


def strip_rules(text):
    """Remove whole rules for GONE_SELECTORS anywhere in the <style>s, and
    the phone .back-button rule inside a max-width block. Then drop any
    media block left empty. Returns (text, n)."""
    n = 0
    out = []
    pos = 0
    for m in re.finditer(r'(<style[^>]*>)(.*?)(</style>)', text, re.S):
        css = m.group(2)
        for sel in GONE_SELECTORS:
            css, k = rule_re(sel).subn('', css)
            n += k
        # the phone Back: only inside a screen max-width block
        def phone(mm):
            nonlocal n
            body, k = rule_re(PHONE_BACK).subn('', mm.group(2))
            n += k
            return mm.group(1) + body + mm.group(3)
        css = re.sub(r'(@media screen and \(max-width: 768px\)\s*\{)'
                     r'((?:[^{}]*\{[^{}]*\})*[^{}]*)(\})', phone, css)
        css, k = re.subn(r'(?m)^[ \t]*@media[^{\n]*\{\s*\}[ \t]*\n', '', css)
        out.append(text[pos:m.start(2)] + css)
        pos = m.end(2)
    out.append(text[pos:])
    return ''.join(out), n


# ---- 1. base --------------------------------------------------------------
b = read(BASE)
if MARK_OPEN in b:
    report.append('%-44s already carries the component' % 'base.html')
elif b.count(ANCHOR) != 1:
    problems.append('base.html: anchor %r found %d time(s)'
                    % (ANCHOR, b.count(ANCHOR)))
else:
    planned[BASE] = (b, b.replace(ANCHOR, ANCHOR + '\n\n' + BLOCK, 1))
    report.append('%-44s + ALV REPORT HEAD v1' % 'base.html')

# ---- 2. the nine report screens -------------------------------------------
for name in PAGES:
    p = os.path.join(T, name)
    if not os.path.isfile(p):
        problems.append('%s not found' % name)
        continue
    t = read(p)
    if 'class="alv-report-head"' in t:
        report.append('%-44s already done' % name)
        continue
    ok = plan(p, '<div class="header-container">',
              '<div class="alv-report-head">', 'the row')
    wrap = ('report-title-container' if 'class="report-title-container"' in t
            else 'title-wrapper')
    m = re.search(r'([ \t]*)<div class="%s">\n' % wrap, t)
    if not m:
        problems.append('%s: no %s' % (name, wrap))
        continue
    ind = m.group(1)
    inner = ind + '    '
    ok &= plan(p, m.group(0), '%s<div class="alv-report-titles">\n%s%s\n'
               % (ind, inner, BRAND), 'the titles + brand')
    if wrap == 'title-wrapper':
        ok &= plan(p, '<h2 class="report-title">',
                   '<h2 class="alv-report-title">', 'the title')
        ok &= plan(p, '<h3 class="report-subtitle">',
                   '<h3 class="alv-report-sub">', 'the subtitle')
    else:
        ok &= plan(p, '<h2 class="report-title-main">',
                   '<h2 class="alv-report-title">', 'the title')
        cur = planned[p][1]
        k = cur.count('<h3 class="report-title-sub')
        if k < 1:
            problems.append('%s: no subtitle' % name)
        cur = cur.replace('<h3 class="report-title-sub text-danger">',
                          '<h3 class="alv-report-sub text-danger">')
        cur = cur.replace('<h3 class="report-title-sub">',
                          '<h3 class="alv-report-sub">')
        planned[p] = (planned[p][0], cur)
    new, n = strip_rules(planned[p][1])
    planned[p] = (planned[p][0], new)
    report.append('%-44s row, titles, brand; %d local rule(s) removed'
                  % (name, n))

# ---- 3. the dead title-deed pair ------------------------------------------
for name in DEAD:
    p = os.path.join(T, name)
    if os.path.isfile(p):
        deletes.append(p)
        report.append('%-44s DELETED (rendered by nothing usable)' % name)
    else:
        report.append('%-44s already gone' % name)

VIEWS = os.path.join('pages', 'views', 'properties.py')
URLS = os.path.join('pages', 'urls.py')
MW = os.path.join('pages', 'middleware.py')


def cut_view(path, fn, last_line):
    cur = planned[path][1] if path in planned else read(path)
    head = ("@login_required\n@permission_required('auth.can_access_"
            "properties', raise_exception=True)\ndef %s(" % fn)
    if 'def %s(' % fn not in cur:
        report.append('%-44s %s already gone' % (os.path.basename(path), fn))
        return
    i = cur.find(head)
    j = cur.find(last_line, i)
    if i < 0 or j < 0 or cur.count(head) != 1:
        problems.append('%s: could not bound %s' % (path, fn))
        return
    j += len(last_line)
    chunk = cur[i:j]
    if chunk.count('\ndef ') + chunk.startswith('def ') > 1 or \
            len(re.findall(r'(?m)^def ', chunk)) != 1:
        problems.append('%s: %s would take more than one function'
                        % (path, fn))
        return
    orig = planned[path][0] if path in planned else cur
    planned[path] = (orig, cur[:i] + cur[j:])
    report.append('%-44s - view %s' % (os.path.basename(path), fn))


if os.path.isfile(VIEWS):
    cut_view(VIEWS, 'properties_title_deed',
             "    return render(request, 'properties_title_deed.html', "
             "context)\n\n\n")
    cut_view(VIEWS, 'title_deed_report',
             "        'file_type': property.prop_title_deed.name.split('.')"
             "[-1].lower()\n    })\n\n\n")
for path, line, what in (
        (URLS, "    path('property/<int:prop_id>/title-deed/', "
               "views.title_deed_report, name='title_deed_report'),\n",
         'url title_deed_report'),
        (URLS, "    path('properties_title_deed/', views.properties_title_deed,"
               " name='properties_title_deed'),\n",
         'url properties_title_deed'),
        (MW, "            ('properties_title_deed', "
             "'auth.can_access_properties'),\n",
         'access rule properties_title_deed')):
    cur = planned[path][1] if path in planned else read(path)
    if line not in cur:
        report.append('%-44s %s already gone' % (os.path.basename(path), what))
    elif plan(path, line, '', what):
        report.append('%-44s - %s' % (os.path.basename(path), what))

# ---- 4. suites, rounds, gate ------------------------------------------------
TTR = 'test_table_tenant_report.py'
if os.path.isfile(TTR):
    cur = read(TTR)
    old = """for sel, why in (('.report-container', 'the page shell'),
                 ('.report-content', 'the sheet'),
                 ('.header-container', 'the title row'),
                 ('.report-title-main', 'the title'),"""
    new = """# LATER - test_report_head.py, 21 Sep: the title row and the title went
# to base's report-title component, so those two are judged on the file as
# THIS round left it.
_RT = PAGE + '.bak_reporthead'
_CSS_LEFT = CSS
if os.path.exists(_RT):
    _CSS_LEFT = '\\n'.join(re.findall(r'<style[^>]*>(.*?)</style>',
                                      read(_RT), re.S))
for sel, why in (('.report-container', 'the page shell'),
                 ('.report-content', 'the sheet'),
                 ('.header-container', 'the title row'),
                 ('.report-title-main', 'the title'),"""
    old2 = """    check('  KEPT %-20s (%s)' % (sel, why),
          re.search(re.escape(sel) + r'\\s*[,{:.]', CSS) is not None)"""
    new2 = """    check('  KEPT %-20s (%s)' % (sel, why),
          re.search(re.escape(sel) + r'\\s*[,{:.]',
                    _CSS_LEFT if sel in ('.header-container',
                                         '.report-title-main') else CSS)
          is not None)"""
    old3 = """def group(prefix):
    return sum(1 for x in _sels if prefix in x)"""
    new3 = """_sels_left = [' '.join(re.sub(r'/\\*.*?\\*/', '', mm.group(1),
                                flags=re.S).split())
              for mm in re.finditer(r'([^{}]+)\\{', _CSS_LEFT)]


def group(prefix):
    # LATER - test_report_head.py, 21 Sep: '.report' counts the page shell
    # AND the title, and the title's rules went to base - so that group is
    # counted on the file as THIS round left it.
    src = _sels_left if prefix == '.report' else _sels
    return sum(1 for x in src if prefix in x)"""
    done = 0
    for o, n_ in ((old, new), (old2, new2), (old3, new3)):
        cur = planned[TTR][1] if TTR in planned else read(TTR)
        if n_ in cur:
            continue
        if plan(TTR, o, n_, 'LATER'):
            done += 1
    report.append('%-44s LATER: %s' % (TTR, 'the title rules as its round '
                  'left them' if done else 'already reads the file as its '
                  'round left it'))

ROUNDS_FILE = 'alv_rounds.py'
if os.path.isfile(ROUNDS_FILE):
    cur = read(ROUNDS_FILE)
    if "'.bak_reporthead'" in cur:
        report.append('%-44s already lists this round' % ROUNDS_FILE)
    elif plan(ROUNDS_FILE, "    '.bak_eimodal',\n]",
              "    '.bak_eimodal',\n    '.bak_reporthead',\n]", 'rounds'):
        report.append('%-44s learns .bak_reporthead' % ROUNDS_FILE)
else:
    problems.append('%s missing' % ROUNDS_FILE)

GATE_NOTE = """    # One report title, owned by base. Nine report screens render the
    # same title and subtitle at 1280, 375 and on paper, the brand shows
    # on paper only, and the dead title-deed pair stays gone - no view,
    # URL or access rule points at it.
    # Newest, so most likely to be what breaks.
    'test_report_head.py'"""
if os.path.isfile(PS1):
    psrc = read(PS1)
    if "'%s'" % SUITE in psrc:
        report.append('%-44s already runs %s' % (PS1, SUITE))
    else:
        i = psrc.find('$suites = @(')
        m = re.search(r'\n\)\s*?\n', psrc[i:]) if i >= 0 else None
        last = (re.search(r"'([A-Za-z0-9_.-]+\.py)'\s*$",
                          psrc[i:i + m.start()]) if m else None)
        if not last:
            problems.append('%s: could not find the end of $suites' % PS1)
        else:
            j = i + m.start()
            planned[PS1] = (psrc, psrc[:j] + ',\n' + GATE_NOTE + psrc[j:])
            report.append('%-44s + %s, after %s' % (PS1, SUITE,
                                                    last.group(1)))

# ==========================================================================
# SELF-CHECK
# ==========================================================================
for path, (src, text) in planned.items():
    if path.endswith('.py'):
        try:
            ast.parse(text)
        except SyntaxError as e:
            problems.append('%s: does not parse - line %s' % (path, e.lineno))
    if path.endswith('.html') and path != BASE:
        for tag in ('{% if', '{% endif %}', '{% for', '{% endfor %}',
                    '{% url', '{{'):
            if src.count(tag) != text.count(tag):
                problems.append('%s: %s count changed' % (path, tag))
        for dead in ('header-container', 'report-title-container',
                     'title-wrapper', 'report-title-main',
                     'report-title-sub', 'class="report-title"',
                     'report-subtitle'):
            body = re.sub(r'/\*.*?\*/', '', text, flags=re.S)
            if dead in body:
                problems.append('%s: %s survives' % (path, dead))
        if text.count(BRAND) != 1:
            problems.append('%s: brand line count %d' % (path,
                                                         text.count(BRAND)))
        if len(re.findall(r'<div\b', src)) + 1 != \
                len(re.findall(r'<div\b', text)) or \
                src.count('</div>') != text.count('</div>') - 1:
            problems.append('%s: div count moved by more than the brand'
                            % path)
if BASE in planned:
    src, text = planned[BASE]
    if text.replace('\n\n' + BLOCK, '', 1) != src:
        problems.append('base.html: more changed than the one block')
    c = re.findall(r'/\*.*?\*/', BLOCK, re.S)
    if any('{' in x or '@' in x for x in c):
        problems.append('base.html: a comment reads like CSS')
for fn in ('properties_title_deed', 'title_deed_report'):
    for path in (VIEWS, URLS, MW):
        text = planned[path][1] if path in planned else read(path)
        if re.search(r"\b%s\b" % fn, text):
            problems.append('%s still names %s' % (path, fn))

print('\n' + '=' * 74)
print('ONE REPORT TITLE - %s' % ('DRY RUN' if CHECK else 'APPLY'))
print('=' * 74)
for line in report:
    print('  ' + line)
print('')
if problems:
    print('!' * 74)
    print('%d PROBLEM(S). Nothing has been written.' % len(problems))
    print('!' * 74)
    for p in problems:
        print('  FAIL %s' % p)
    sys.exit(1)
if not planned and not deletes:
    print('  Nothing to do - this round has already been applied.')
    sys.exit(0)
if CHECK:
    print('  --check: nothing written. Re-run without --check to apply.')
    sys.exit(0)
for path, (src, text) in sorted(planned.items()):
    bak = path + SUFFIX
    if not os.path.exists(bak):
        CRLF[bak] = CRLF.get(path)
        write(bak, src)
    write(path, text)
for p in deletes:
    bak = p + SUFFIX
    if not os.path.exists(bak):
        src = read(p)
        CRLF[bak] = CRLF.get(p)
        write(bak, src)
    os.remove(p)
print('  %d file(s) written, %d deleted, backups at *%s'
      % (len(planned), len(deletes), SUFFIX))
print('  %d keep CRLF line endings, %d keep LF'
      % (sum(1 for p in planned if CRLF.get(p)),
         sum(1 for p in planned if not CRLF.get(p))))
print('')
print('  Next:  python %s' % SUITE)
