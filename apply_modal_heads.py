# -*- coding: utf-8 -*-
"""apply_modal_heads.py - one pop-up header, owned by base: the teal banner,
and red only where the pop-up deletes something.

    python apply_modal_heads.py --check     dry run, nothing written
    python apply_modal_heads.py             apply

Run from the repo root. Idempotent: a second run reports nothing to do.

WHAT WAS MEASURED (21 Sep, claude/modal_headers_survey.md)

  Every modal on every template rendered open at 1280 wide: 87 headers on
  48 templates in 16 different looks - white, flat and gradient teal, red,
  green, grey, purple, Bootstrap blue, and yellow with white text that
  fails contrast. base defined no modal header at all. Delete confirmations
  were red on fourteen, white on two, grey on one; four red headers
  deleted nothing.

WHAT THIS DOES - agreed 21 Sep

  1. base gains .alv-modal-head: the teal banner the Issues, Help and
     preview pop-ups already wear, white title at 20px/600, white close
     button - and .alv-modal-head--danger, the same in red. Its paint is
     !important on purpose: headers are painted today by Bootstrap's own
     !important bg-* classes, by page rules scoped to a modal's id, and by
     inline styles, and the standard has to win over all three.
  2. The 51 headers on the 31 business templates take the class. A header
     whose title says Delete takes the danger variant too - nine of them.
     Their bg-* and text-white classes go, and so does any background,
     colour or border in a header's own inline style. Nothing inside a
     header is touched.
  3. The 36 headers on the Personal side are NOT touched - agreed, they go
     with the Personal round, so that section is reviewed as a whole.
  4. test_modal_heads.py is wired onto the push gate.

  Page rules that painted a header are left where they are and lose to
  base. They are named by test_modal_heads.py as dead weight for a tidy.
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

CHECK = '--check' in sys.argv
ROOT = os.path.join(os.getcwd(), 'pages', 'templates')
if not os.path.isdir(ROOT):
    sys.exit('! pages/templates not found - run from the repo root')

SUFFIX = '.bak_modalhead'
SUITE = 'test_modal_heads.py'
PS1 = 'Push-PendingChanges.ps1'
BASE = os.path.join(ROOT, 'base.html')
MARK_OPEN = '/* ALV MODAL HEAD v1'
MARK_CLOSE = '/* /ALV MODAL HEAD v1 */'
ANCHOR = '/* /ALV PRINT BUTTONS v1 */'
HEAD, DANGER = 'alv-modal-head', 'alv-modal-head--danger'

BUSINESS = [
    'act_expense.html', 'asset_detail.html', 'comments_report.html',
    'components/pdf_viewer.html', 'finance/cashflow_forecast.html',
    'finance/financial_indicators.html', 'finance/vacancy_management.html',
    'finance_expense.html', 'finance_expense_add.html',
    'finance_expense_edit.html', 'finance_expense_line_types.html',
    'finance_expense_line_types_edit.html', 'finance_pl_act.html',
    'finance_valuations_edit.html', 'fsr.html', 'fsr_details.html',
    'generate_lease_agreement.html', 'help_modal_shell.html',
    'help_page.html', 'map_view.html', 'occupancy_trends.html',
    'open_invoices_report.html', 'projects/projects_detail.html',
    'properties_edit.html', 'property_assets.html',
    'property_management_dashboard.html', 'suppliers.html',
    'tenant_lease_agreement.html', 'title_deeds_management.html',
    'user_administration.html', 'workspace_management.html',
]

report, problems = [], []
planned = {}
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


def blank(m):
    return re.sub(r'[^\n]', ' ', m.group(0))


def mask(t):
    """Scripts, styles and comments blanked - a header written inside a
    script string is not markup and is not touched."""
    t = re.sub(r'<(script|style)\b.*?</\1>', blank, t, flags=re.S | re.I)
    t = re.sub(r'<!--.*?-->', blank, t, flags=re.S)
    return re.sub(r'\{#.*?#\}', blank, t, flags=re.S)


OPEN = re.compile(r'<div\s+class="([^"]*\b(?:modal-header|ei-modal-header)'
                  r'\b[^"]*)"([^>]*)>')
PAINT = re.compile(r'^\s*(background(-color|-image)?|color|border-bottom)\s*:',
                   re.I)


def heads(text):
    """(start, end, classes, rest, title) for every header opening tag."""
    msk, out = mask(text), []
    for m in OPEN.finditer(msk):
        after = msk[m.end():m.end() + 1500]
        t = re.search(r'<(h\d)\b[^>]*>(.*?)</\1>', after, re.S)
        title = re.sub(r'<[^>]+>|\s+', ' ', t.group(2)).strip() if t else ''
        out.append((m.start(), m.end(), text[m.start(1):m.end(1)],
                    text[m.start(2):m.end(2)], title))
    return out


def rewrite(classes, rest, title):
    keep = [c for c in classes.split()
            if not re.match(r'bg-|text-white$', c) and c not in (HEAD, DANGER)]
    keep.append(HEAD)
    if re.search(r'\bdelete\b', title, re.I):
        keep.append(DANGER)
    st = re.search(r'\sstyle="([^"]*)"', rest)
    if st:
        decls = [d for d in st.group(1).split(';') if d.strip()
                 and not PAINT.match(d)]
        new = '; '.join(d.strip() for d in decls)
        rest = rest.replace(st.group(0), (' style="%s;"' % new) if new else '')
    return '<div class="%s"%s>' % (' '.join(keep), rest)


BLOCK = """

%s - ONE POP-UP HEADER.
   Measured 21 Sep: 87 modal headers in 16 looks, and base defined none. A
   delete confirmation was red on fourteen, white on two, grey on one.
   This is the teal banner the Issues, Help and preview pop-ups already
   wore, with a white title and a white close button; the danger variant
   is the same banner in red, for a pop-up that deletes something.
   The paint is important on purpose. Headers were painted by Bootstrap's
   own important colour classes, by page rules scoped to a modal's id and
   by inline styles, and the standard has to win over all three.
   See test_modal_heads.py. */
.alv-modal-head {
    background: linear-gradient(135deg, var(--alv-accent) 0%%,
                var(--alv-accent-ink) 100%%) !important;
    color: var(--alv-on-accent) !important;
    border-bottom: 0 !important;
    padding: 16px 20px !important;
    align-items: center;
}
.alv-modal-head--danger {
    background: linear-gradient(135deg, var(--alv-bad) 0%%,
                color-mix(in srgb, var(--alv-bad) 78%%, #000) 100%%) !important;
}
.alv-modal-head .modal-title,
.alv-modal-head h1, .alv-modal-head h2, .alv-modal-head h3,
.alv-modal-head h4, .alv-modal-head h5, .alv-modal-head h6 {
    color: var(--alv-on-accent) !important;
    font-size: 20px !important;
    font-weight: 600 !important;
    line-height: 1.3;
    margin: 0;
}
.alv-modal-head .modal-title i,
.alv-modal-head h5 i { color: inherit !important; margin-right: 8px; }
.alv-modal-head .close {
    color: var(--alv-on-accent) !important;
    opacity: 0.85 !important;
    text-shadow: none !important;
}
.alv-modal-head .close:hover { opacity: 1 !important; }
%s""" % (MARK_OPEN, MARK_CLOSE)

# ---- 1. base --------------------------------------------------------------
src = read(BASE)
if MARK_OPEN in src:
    report.append('%-40s already carries the component' % 'base.html')
elif src.count(ANCHOR) != 1:
    problems.append('base.html: anchor %r found %d time(s) - is the buttons '
                    'round applied?' % (ANCHOR, src.count(ANCHOR)))
else:
    planned[BASE] = (src, src.replace(ANCHOR, ANCHOR + BLOCK, 1))
    report.append('%-40s + .alv-modal-head and its danger variant'
                  % 'base.html')

# ---- 2. the business headers ----------------------------------------------
n_heads = n_danger = 0
for rel in BUSINESS:
    p = os.path.join(ROOT, rel)
    if not os.path.isfile(p):
        problems.append('%s: not on disk' % rel)
        continue
    src = read(p)
    hs = heads(src)
    if not hs:
        problems.append('%s: no modal header found' % rel)
        continue
    if all(HEAD in c.split() for _s, _e, c, _r, _t in hs):
        report.append('%-40s already done' % rel)
        continue
    text, shift, dn = src, 0, 0
    for s, e, classes, rest, title in hs:
        new = rewrite(classes, rest, title)
        text = text[:s + shift] + new + text[e + shift:]
        shift += len(new) - (e - s)
        dn += DANGER in new
    planned[p] = (src, text)
    n_heads += len(hs)
    n_danger += dn
    report.append('%-40s %d header(s)%s' % (rel, len(hs),
                                           ', %d danger' % dn if dn else ''))

# ---- 2b. the file as a round left it, in ONE place -----------------------
# Four suites judge "the file now is my backup plus my change", and this
# round edits files they own - the whole-suite sweep found test_zoom_guards,
# test_print_queries, test_print_buttons and test_div_balance failing on
# work that is correct. That has happened in every round today, patched one
# suite at a time. alv_rounds.as_left_by() answers it once: the file as a
# round left it is the next round's backup of it. Those suites (and
# test_small_controls, which had the same hand-written chain) now ask it.
ROUNDS_FILE = 'alv_rounds.py'
ROUNDS_SRC = open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                               'alv_rounds.py'), encoding='utf-8').read() \
    if os.path.isfile(os.path.join(os.path.dirname(os.path.abspath(
        __file__)), 'alv_rounds.py')) else None
NEW_FILES = {}
if os.path.isfile(ROUNDS_FILE):
    if "'.bak_modalhead'" in read(ROUNDS_FILE):
        report.append('%-40s already lists this round' % ROUNDS_FILE)
    else:
        problems.append('%s exists without this round in it' % ROUNDS_FILE)
elif ROUNDS_SRC is None:
    problems.append('alv_rounds.py must sit beside this patcher')
else:
    NEW_FILES[ROUNDS_FILE] = ROUNDS_SRC
    report.append('%-40s new: the file as a round left it' % ROUNDS_FILE)

USE = "from alv_rounds import as_left_by\n"
SUITE_EDITS = [
    ('test_zoom_guards.py',
     """        after = (read(p + '.bak_printq') if os.path.isfile(p + '.bak_printq')
                 else read(p))""",
     """        from alv_rounds import as_left_by
        after = as_left_by(p, SUFFIX, read)"""),
    ('test_small_controls.py',
     """    _then = (read(BASE_PATH + '.bak_printbtn')
             if os.path.isfile(BASE_PATH + '.bak_printbtn') else BASE)""",
     """    from alv_rounds import as_left_by
    _then = as_left_by(BASE_PATH, SUFFIX, read)"""),
    ('test_small_controls.py',
     """        then = (read(DASH + '.bak_printq')
                if os.path.isfile(DASH + '.bak_printq') else d)""",
     """        from alv_rounds import as_left_by
        then = as_left_by(DASH, SUFFIX, read)"""),
    ('test_print_queries.py',
     """        now = next((read(p + s) for s in ('.bak_printbtn', '.bak_divbal')
                    if os.path.isfile(p + s)), None) or read(p)
        was = read(p + SUFFIX)
        k = now.count(ADD) - was.count(ADD)""",
     """        from alv_rounds import as_left_by
        now = as_left_by(p, SUFFIX, read)
        was = read(p + SUFFIX)
        k = now.count(ADD) - was.count(ADD)"""),
    ('test_print_queries.py',
     """            now = next((read(p + s) for s in ('.bak_printbtn', '.bak_divbal')
                        if os.path.isfile(p + s)), None) or read(p)
            was = read(p + SUFFIX)
            for w in (375, 1280):""",
     """            from alv_rounds import as_left_by
            now = as_left_by(p, SUFFIX, read)
            was = read(p + SUFFIX)
            for w in (375, 1280):"""),
    ('test_print_buttons.py',
     """    ok(re.sub(r'\\n\\n' + MARK.pattern, '', BASE, count=1, flags=re.S)
       == read(bak), 'nothing else in base changed')""",
     """    # LATER - test_modal_heads.py, 21 Sep: base as THIS round left it.
    from alv_rounds import as_left_by
    ok(re.sub(r'\\n\\n' + MARK.pattern, '', as_left_by(BASE_PATH, SUFFIX,
                                                       read),
              count=1, flags=re.S)
       == read(bak), 'nothing else in base changed')"""),
    ('test_print_buttons.py',
     """                a = render(br, fixture(boot, base_was, styles_of(old_t),
                                       old_mk), w, 'screen', SNAP)
                b = render(br, fixture(boot, base_now, styles_of(t), mk), w,
                           'screen', SNAP)""",
     """                # LATER - test_modal_heads.py, 21 Sep. The screen as THIS
                # round found it against the screen as it LEFT it - base and
                # page both. A page this round never touched is the same
                # text on both sides, so only base can differ.
                from alv_rounds import as_left_by
                _lt = as_left_by(p, SUFFIX, read)
                _ot = read(p + SUFFIX) if os.path.isfile(p + SUFFIX) else _lt
                a = render(br, fixture(boot, base_was, styles_of(_ot),
                                       body_markup(_ot)), w, 'screen', SNAP)
                b = render(br, fixture(boot, '\\n'.join(styles_of(
                    as_left_by(BASE_PATH, SUFFIX, read))), styles_of(_lt),
                    body_markup(_lt)), w, 'screen', SNAP)"""),
    ('test_div_balance.py',
     """    a, b = read(p + SUFFIX).split('\\n'), read(p).split('\\n')""",
     """    # LATER - test_modal_heads.py, 21 Sep: the file as THIS round left it.
    from alv_rounds import as_left_by
    a = read(p + SUFFIX).split('\\n')
    b = as_left_by(p, SUFFIX, read).split('\\n')"""),
    # test_ia_drill.py pinned "base has NO modal component" with a regex
    # that .alv-modal-head now matches - the laptop sweep caught it, this
    # checkout could not (no fsr.html.bak_iadrill here). The decision it
    # records still holds: base owns the pop-up HEADER only, no dialog,
    # overlay or body, and the drill overlay is not a .modal-header.
    ('test_ia_drill.py',
     """check('base still has no modal component of its own - so this is one asker',
      not re.search(r'\\.alv-(modal|dialog|overlay|sheet)\\b', BASE_CSS))""",
     """# LATER - test_modal_heads.py, 21 Sep: base now owns the pop-up HEADER
# (.alv-modal-head, .alv-modal-head--danger) and nothing else - no dialog,
# overlay or body. The drill overlay is hand-rolled, not a .modal-header,
# so it is still one asker and keeps its own rules.
NO_MODAL = re.compile(r'\\.alv-(modal|dialog|overlay|sheet)(?![\\w-])'
                      r'|\\.alv-modal-(?!head\\b)[\\w-]')
check('base still has no modal component of its own - only the header',
      not NO_MODAL.search(BASE_CSS))
check('  CONTROL: a whole .alv-modal in base would be caught',
      bool(NO_MODAL.search(BASE_CSS + '\\n.alv-modal{display:block}')))
check('  CONTROL: so would a .alv-modal-body',
      bool(NO_MODAL.search(BASE_CSS + '\\n.alv-modal-body{padding:0}')))
check('  and the drill head did not become one of base\\'s modal heads',
      not re.search(r'ia-drill-head[^"]*alv-modal-head'
                    r'|alv-modal-head[^"]*ia-drill-head', read(IA)))"""),
]
for name, old, new in SUITE_EDITS:
    if not os.path.isfile(name):
        report.append('%-40s not on disk - nothing to adjust' % name)
        continue
    cur = planned[name][1] if name in planned else read(name)
    if new in cur:
        continue
    if cur.count(old) != 1:
        problems.append('%s: anchor found %d time(s), expected 1: %r'
                        % (name, cur.count(old), old[:50]))
        continue
    orig = planned[name][0] if name in planned else cur
    planned[name] = (orig, cur.replace(old, new, 1))
for name in sorted(set(n for n, _o, _n in SUITE_EDITS)):
    if name in planned:
        report.append('%-40s %s' % (name, 'base owns the header only - '
                      'the no-modal check now says so'
                      if name == 'test_ia_drill.py' else
                      'asks alv_rounds for the file its round left'))

# ---- 3. the gate ----------------------------------------------------------
GATE_NOTE = """    # One pop-up header, owned by base. Every business modal is opened
    # in the browser and must read the teal banner - or red, exactly when
    # its title says Delete - white title, white close, one size. Its
    # control puts the class on a header painted by bg-info, a page rule
    # and an inline style at once, and base must win over all three.
    # Newest, so most likely to be what breaks.
    'test_modal_heads.py'"""
if os.path.isfile(PS1):
    psrc = read(PS1)
    if "'%s'" % SUITE in psrc:
        report.append('%-40s already runs %s' % (PS1, SUITE))
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
            report.append('%-40s + %s, after %s' % (PS1, SUITE,
                                                    last.group(1)))

# ==========================================================================
# SELF-CHECK - only header opening tags changed in the templates
# ==========================================================================
import ast
COMMENT = re.compile(r'/\*.*?\*/', re.S)
for path, (src, text) in planned.items():
    if path.endswith('.py'):
        try:
            ast.parse(text)
        except SyntaxError as e:
            problems.append('%s: does not parse - line %s' % (path, e.lineno))
        continue
    if path == BASE:
        if text.replace(BLOCK, '', 1) != src:
            problems.append('base.html: more changed than the one block')
        c = COMMENT.findall(BLOCK)
        if len(c) != 2 or any('@' in x or '{' in x for x in c):
            problems.append('base.html: a comment reads like CSS')
        continue
    if not path.endswith('.html'):
        continue
    a, b = src.split('\n'), text.split('\n')
    if len(a) != len(b):
        problems.append('%s: line count changed' % path)
        continue
    for x, y in zip(a, b):
        if x != y and not re.search(r'modal-header', x):
            problems.append('%s: a line that is not a header tag changed'
                            % os.path.relpath(path, ROOT))
            break

print('\n' + '=' * 74)
print('ONE POP-UP HEADER - %s' % ('DRY RUN' if CHECK else 'APPLY'))
print('=' * 74)
for line in report:
    print('  ' + line)
print('')
print('  %d business header(s), %d of them danger. Personal side untouched.'
      % (n_heads, n_danger))
print('')
if problems:
    print('!' * 74)
    print('%d PROBLEM(S). Nothing has been written.' % len(problems))
    print('!' * 74)
    for p in problems:
        print('  FAIL %s' % p)
    sys.exit(1)
if not planned and not NEW_FILES:
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
for name, text in NEW_FILES.items():
    with open(name, 'w', encoding='utf-8', newline='') as f:
        f.write(text)
print('  %d file(s) written, backups at *%s' % (len(planned), SUFFIX))
if NEW_FILES:
    print('  new: %s' % ', '.join(sorted(NEW_FILES)))
print('  %d keep CRLF line endings, %d keep LF'
      % (sum(1 for p in planned if CRLF.get(p)),
         sum(1 for p in planned if not CRLF.get(p))))
print('')
print('  Next:  python %s' % SUITE)
