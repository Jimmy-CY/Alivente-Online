# -*- coding: utf-8 -*-
"""apply_surface_deep.py - Section F round F2a-3, 27 Sep 2026.

#e9ecef -> var(--alv-surface-deep), BACKGROUNDS ONLY: 85 sites, 50 templates.

THE HALF THIS ROUND REFUSES IS BIGGER THAN THE HALF IT TAKES.
#e9ecef is 180 uses in templates with token scope, and parsed by property
they split almost evenly:

    background / background-color / background-image    85   <- this round
    border / border-top / -bottom / -left / -right /
      -color                                           93   <- NOT this round
    --future-light (a page-local custom property)        2   <- NOT this round

--alv-surface-deep is a SURFACE token: base declares it as "the far stop of
the panel wash". base's two LINE tokens are --alv-line #e3e8ea and
--alv-line-soft #f1f3f5, and NEITHER equals #e9ecef. So the 93 borders have
no correct token to go to. Binding them to a surface token would be
pixel-identical and semantically false - change the panel wash and 93 table
and card borders move with it. That is the same trap F2a-1 refused for six
fills, and base's own print stylesheet fell into with #55606b.

F2b decides them properly, and the honest question there is whether they
should become var(--alv-line): #e9ecef -> #e3e8ea is 1.04:1, six, four and
five per channel, on borders that are 1px in 60 of the 93 cases - and
var(--alv-line) is already carrying 59 borders elsewhere in the app. That is
a visible change in principle, which is exactly why it cannot live in F2a.

THE TWO CUSTOM PROPERTIES ARE LEFT FOR THE SAME REASON, NOT LAZINESS.
admin_apms.html and personal.html both declare

    --future-light: #e9ecef;

and admin_apms then spends it on background-color THREE times and on
border-bottom-color ONCE. One page-local token doing both jobs is precisely
the fill-or-line question F2b has to answer, so the definition waits for the
answer rather than being pinned to a surface now.

PROPERTIES ARE PARSED, NOT GUESSED (lesson 66).
The first property census for this colour searched backwards from the hex to
the nearest ; { , or " and read the word before the colon. It is wrong
whenever the hex is not the first value in its declaration: it reported
padding, font-weight, border-radius, transform and even bare class names as
properties carrying a colour, and put 72 of the 180 sites in a bucket called
"gradient-or-list". This patcher walks the CSS instead - rules, then
declarations split at TOP-LEVEL semicolons only - and reads each
declaration's own property name. Under that reading the counts are exact and
the buckets are real.

EXCLUDED, AS IN EVERY ROUND OF THIS SWEEP: the five standalone documents and
the one naked fragment that base's :root never reaches, because an undefined
custom property is invalid at computed-value time and resolves to `unset` -
a background would go transparent, not stay grey. base.html has no #e9ecef
of its own outside its :root declaration, so nothing is held back this time.

IN SCOPE WITHOUT AN EXTENDS TAG: components/pdf_viewer.html, a fragment
included by twelve base-extending pages. Checked, not assumed.

A STYLE ATTRIBUTE AUTHORED INSIDE A SCRIPT IS STILL A STYLE ATTRIBUTE.
unit_conversions_management.html builds two read-only inputs in a JS template
literal:

    <input ... readonly style="background: #e9ecef;">

The first version of this patcher's zone finder excluded inline styles that
sit inside a <script> body, the way F2a-2's did - and F2a-2 was RIGHT to,
because its two script uses were a Chart.js colour string and an anTok
fallback: JavaScript VALUES, which a canvas and a DOM read cannot resolve a
var() from. These two are different. They are markup, and the markup lands in
the DOM of a page that extends base, so var(--alv-surface-deep) resolves
there exactly as it would if the attribute had been typed in the template.
Both are inside backticks with ${...} interpolation, and the replacement adds
no dollar sign and no backtick, so the literal is all that changes.

The discrepancy is how this was found: the patcher's own tree total said 87
backgrounds where the survey had said 85. Two is a small number to notice,
and the only reason it was noticed is that the count is computed twice by
different code.
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

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, 'pages', 'templates')
SUFFIX = '.bak_surfdeep'
CHECK = '--check' in sys.argv

LITERAL = '#e9ecef'
TOKEN = 'var(--alv-surface-deep)'

BG = ('background', 'background-color', 'background-image')

# Machine-derived, by the parsing census - never hand-written.
EXPECTED = {
    'act_expense.html': 3,
    'categories_management.html': 1,
    'components/pdf_viewer.html': 1,
    'customer_invoice_form.html': 1,
    'dashboard_pl.html': 2,
    'finance/financial_indicators.html': 3,
    'finance/vacancy_management.html': 3,
    'finance_expense_add.html': 1,
    'finance_expense_edit.html': 1,
    'finance_expense_line_types_add.html': 1,
    'finance_expense_line_types_edit.html': 1,
    'finance_pl_act.html': 1,
    'finance_valuations_add.html': 1,
    'finance_valuations_edit.html': 1,
    'fsr.html': 2,
    'generate_lease_agreement.html': 1,
    'help_page.html': 5,
    'import_recipe.html': 1,
    'ingredient_base_units_management.html': 4,
    'invoices.html': 1,
    'lease_agreement_report.html': 1,
    'lease_timeline.html': 1,
    'map_ingredients_nutrition.html': 2,
    'meal_plan_calendar.html': 2,
    'meal_plan_shopping_list.html': 1,
    'meal_plans.html': 2,
    'measurement_units_management.html': 1,
    'notifications.html': 1,
    'passport_management.html': 2,
    'physical_invoice_edit.html': 1,
    'physical_invoice_list.html': 3,
    'preview_imported_recipe.html': 4,
    'projects/project_gantt.html': 2,
    'projects/project_tasks_edit.html': 2,
    'projects/projects.html': 2,
    'projects/projects_detail.html': 1,
    'projects/projects_edit.html': 1,
    'properties.html': 1,
    'properties_add.html': 1,
    'properties_edit.html': 1,
    'recipe_management.html': 7,
    'suppliers.html': 1,
    'tenant.html': 1,
    'title_deeds_management.html': 1,
    'unit_conversions_management.html': 4,
    'unit_conversions_wizard.html': 1,
    'user_add.html': 1,
    'user_edit.html': 1,
    'view_meal_plan.html': 1,
    'view_recipe.html': 2,
}

# What must still be there afterwards, tree-wide: 93 borders + 2 custom
# property definitions. A survey's floor is worth more than its ceiling
# (lesson 48) - this is the assertion that catches the next round's
# overreach.
LEFT_BORDERS = 93
# THREE, not two: base.html's own :root DECLARATION of --alv-surface-deep is
# counted here and is not a use - it can never be tokenised (lesson 65). The
# two real ones are admin_apms.html and personal.html's --future-light.
LEFT_CUSTOM = 3

NO_TOKEN_SCOPE = (
    'error_pages/connectivity_error.html',
    'invoices/physical_invoice.html',
    'manual_pdf.html',
    'receipts/cash_receipt.html',
    'recipe_pdf.html',
    'total_expense_details.html',
)
# No extends tag of its own, but included by twelve base-extending pages.
FRAGMENT = 'components/pdf_viewer.html'

STYLE = re.compile(r'<style\b[^>]*>(.*?)</style\s*>', re.S | re.I)
HTML_C = re.compile(r'<!--.*?-->', re.S)
DJ_CB = re.compile(r'\{%\s*comment\s*%\}.*?\{%\s*endcomment\s*%\}', re.S | re.I)
DJ_C = re.compile(r'\{#.*?#\}', re.S)
CSS_C = re.compile(r'/\*.*?\*/', re.S)
INLINE = re.compile(r'\bstyle\s*=\s*"([^"]*)"|\bstyle\s*=\s*\'([^\']*)\'', re.S)
RULE = re.compile(r'([^{}]*)\{([^{}]*)\}')
LIT = re.compile(re.escape(LITERAL), re.I)

CRLF = {}


def read(path):
    with open(path, 'rb') as fh:
        raw = fh.read()
    CRLF[path] = b'\r\n' in raw
    return raw.decode('utf-8')


def write(path, text):
    data = text.encode('utf-8')
    if CRLF.get(path):
        data = data.replace(b'\r\n', b'\n').replace(b'\n', b'\r\n')
    else:
        data = data.replace(b'\r\n', b'\n')
    with open(path, 'wb') as fh:
        fh.write(data)


def _sp(m):
    return re.sub(r'[^\n]', ' ', m.group(0))


def declarations(body):
    """[(prop, value_start, value_end)] for one rule body, offsets relative
    to `body`. Split at TOP-LEVEL semicolons only: a semicolon inside
    parentheses or a string is not a declaration boundary, and reading the
    property by searching backwards from a value is what put `padding` and
    `font-weight` in a colour census (lesson 66)."""
    out, depth, i, start, q = [], 0, 0, 0, None
    while i < len(body):
        c = body[i]
        if q:
            if c == q and body[i - 1] != '\\':
                q = None
        elif c in '"\'':
            q = c
        elif c == '(':
            depth += 1
        elif c == ')':
            depth = max(0, depth - 1)
        elif c == ';' and depth == 0:
            out.append((start, i))
            start = i + 1
        i += 1
    if body[start:].strip():
        out.append((start, len(body)))
    res = []
    for a, b in out:
        d = body[a:b]
        if ':' not in d:
            continue
        k = d.split(':', 1)[0]
        res.append((k.strip().lower(), a + len(k) + 1, b))
    return res


def css_regions(text):
    """(scan, [(start, end)]) - the CSS payloads, on text whose markup
    comments and in-style CSS comments are blanked to spaces so offsets
    still index into `text`.

    MARKUP COMMENTS FIRST, on the raw text. The house order - CSS comments
    across the whole file, then find the style tags - is defeated by an
    accept=image/* attribute, whose /* opens a comment running forward to
    the first */ inside the stylesheet. Measured, that hides the WHOLE
    stylesheet on three real templates, and two of them -
    passport_management and preview_imported_recipe - are in this round."""
    t = text
    for rx in (HTML_C, DJ_CB, DJ_C):
        t = rx.sub(_sp, t)
    if len(t) != len(text):
        raise SystemExit('F2a-3: comment blanking changed length')
    style = [(m.start(1), m.end(1)) for m in STYLE.finditer(t)]
    out = list(t)
    for a, b in style:
        out[a:b] = list(CSS_C.sub(_sp, t[a:b]))
    t = ''.join(out)
    regions = list(style)
    for m in INLINE.finditer(t):
        i = 1 if m.group(1) is not None else 2
        if not any(a <= m.start(i) < b for a, b in style):
            regions.append((m.start(i), m.end(i)))
    return t, sorted(regions)


def classify(text):
    """(background_offsets, border_count, custom_count, other_count) -
    every occurrence of the literal in a CSS payload, bucketed by the
    property that actually carries it."""
    scan, regions = css_regions(text)
    bg, border, custom, other = [], 0, 0, 0
    for a, b in regions:
        payload = scan[a:b]
        if '{' in payload:
            spans = [(a + m.start(2), m.group(2)) for m in RULE.finditer(payload)]
        else:
            spans = [(a, payload)]          # an inline style= attribute
        for base, body in spans:
            for prop, va, vb in declarations(body):
                for m in LIT.finditer(body[va:vb]):
                    pos = base + va + m.start()
                    if prop in BG:
                        bg.append(pos)
                    elif prop.startswith('border'):
                        border += 1
                    elif prop.startswith('--'):
                        custom += 1
                    else:
                        other += 1
    return sorted(bg), border, custom, other


def patch(rel):
    path = os.path.join(ROOT, rel)
    text = read(path)
    bg, border, custom, other = classify(text)
    want = EXPECTED[rel]

    if len(bg) != want:
        if TOKEN in text and not bg:
            return 0                        # already applied
        raise SystemExit('F2a-3: %s - %d background site(s), expected %d'
                         % (rel, len(bg), want))
    if other:
        raise SystemExit('F2a-3: %s - %d occurrence(s) on a property that is '
                         'neither a background, a border nor a custom '
                         'property; re-survey before running' % (rel, other))

    before = text
    for pos in reversed(bg):
        if text[pos:pos + len(LITERAL)].lower() != LITERAL:
            raise SystemExit('F2a-3: %s - offset %d is %r, not the literal'
                             % (rel, pos, text[pos:pos + len(LITERAL)]))
        text = text[:pos] + TOKEN + text[pos + len(LITERAL):]

    # Self-checks BEFORE anything is written.
    if text.count(TOKEN) - before.count(TOKEN) != want:
        raise SystemExit('F2a-3: %s - token count moved by %d, not %d'
                         % (rel, text.count(TOKEN) - before.count(TOKEN), want))
    bg2, border2, custom2, other2 = classify(text)
    if bg2:
        raise SystemExit('F2a-3: %s - %d background literal(s) left'
                         % (rel, len(bg2)))
    if (border2, custom2) != (border, custom):
        raise SystemExit('F2a-3: %s - the borders or custom properties moved '
                         '(%d/%d -> %d/%d)'
                         % (rel, border, custom, border2, custom2))
    if re.sub(r'<style\b[^>]*>.*?</style\s*>', '<style/>',
              INLINE.sub('style="@"', before), flags=re.S | re.I) != \
       re.sub(r'<style\b[^>]*>.*?</style\s*>', '<style/>',
              INLINE.sub('style="@"', text), flags=re.S | re.I):
        raise SystemExit('F2a-3: %s - something outside a CSS payload changed'
                         % rel)

    if not CHECK:
        bak = path + SUFFIX
        if not os.path.exists(bak):
            CRLF[bak] = CRLF.get(path)
            write(bak, before)
        write(path, text)
    return want


def tree_totals():
    """(background, border, custom) across every template with token scope."""
    bg = bd = cu = 0
    for d, _x, fs in os.walk(ROOT):
        for f in fs:
            if not f.endswith('.html') or '.bak_' in f:
                continue
            rel = os.path.relpath(os.path.join(d, f), ROOT).replace('\\', '/')
            if rel in NO_TOKEN_SCOPE:
                continue
            a, b, c, _o = classify(read(os.path.join(d, f)))
            bg += len(a)
            bd += b
            cu += c
    return bg, bd, cu


def guard_scope():
    for rel in NO_TOKEN_SCOPE:
        path = os.path.join(ROOT, rel)
        if not os.path.isfile(path):
            raise SystemExit('F2a-3: %s is not in this tree' % rel)
        t = read(path)
        if 'var(--alv-' in t:
            raise SystemExit('F2a-3: %s has gained a var(--alv-*) and has no '
                             ':root to resolve it' % rel)
        if re.search(r'\{%\s*extends\b', t):
            raise SystemExit('F2a-3: %s now extends a template - re-survey its '
                             'token scope before excluding it' % rel)
    # The fragment is in scope only because every page that includes it has
    # an extends tag. A MENTION IS NOT A USE (lesson 34), so the scan reads
    # the markup with comments blanked.
    n = 0
    for d, _x, fs in os.walk(ROOT):
        for f in fs:
            if not f.endswith('.html') or '.bak_' in f:
                continue
            if os.path.relpath(os.path.join(d, f), ROOT).replace('\\', '/') \
                    == FRAGMENT:
                continue
            t = read(os.path.join(d, f))
            for rx in (HTML_C, DJ_CB, DJ_C):
                t = rx.sub(_sp, t)
            # Concatenated, not %-formatted: the pattern contains {% and a
            # percent sign in a format string is a format character.
            inc = r"\{%\s*include\s+['\"]" + re.escape(FRAGMENT) + r"['\"]"
            if re.search(inc, t):
                n += 1
                if not re.search(r'\{%\s*extends\b', t):
                    raise SystemExit('F2a-3: %s includes %s and does not '
                                     'extend base - the fragment would lose '
                                     'its tokens there'
                                     % (os.path.basename(f), FRAGMENT))
    if n < 10:
        raise SystemExit('F2a-3: only %d page(s) include %s - expected ~12; '
                         're-survey' % (n, FRAGMENT))
    return n


LATER = [
    ('alv_rounds.py',
     "    '.bak_accentink',\n]",
     "    '.bak_accentink',\n    '.bak_surfdeep',\n]"),
    ('Push-PendingChanges.ps1',
     "    'test_accent_ink.py'",
     "    'test_accent_ink.py'\n    'test_surface_deep.py'"),
]


def patch_later():
    done = 0
    for name, old, new in LATER:
        path = os.path.join(HERE, name)
        text = read(path)
        if new in text:              # decided by the NEW text alone (47)
            continue
        if text.count(old) != 1:
            raise SystemExit('F2a-3/LATER: anchor matched %d times in %s'
                             % (text.count(old), name))
        if not CHECK:
            bak = path + SUFFIX
            if not os.path.exists(bak):
                CRLF[bak] = CRLF.get(path)
                write(bak, text)
            write(path, text.replace(old, new))
        done += 1
    return done


def main():
    print('=' * 70)
    print('SECTION F, ROUND F2a-3 - %s -> %s (BACKGROUNDS ONLY) - %s'
          % (LITERAL, TOKEN, 'CHECK ONLY' if CHECK else 'APPLYING'))
    print('=' * 70)
    guard_scope()
    b0, d0, c0 = tree_totals()
    print('  before: %d background, %d border, %d custom-property'
          % (b0, d0, c0))
    total = files = 0
    for rel in sorted(EXPECTED):
        n = patch(rel)
        if n:
            files += 1
            print('  %-44s %2d' % (rel, n))
        else:
            print('  %-44s already applied' % rel)
        total += n
    later = patch_later()
    b1, d1, c1 = tree_totals()
    print('-' * 70)
    print('  %d background literal(s) tokenised across %d file(s); '
          '%d LATER edit(s).' % (total, files, later))
    print('  after : %d background, %d border, %d custom-property'
          % (b1, d1, c1))
    if (d1, c1) != (LEFT_BORDERS, LEFT_CUSTOM):
        raise SystemExit('F2a-3: expected %d border and %d custom-property '
                         'use(s) to remain, found %d and %d'
                         % (LEFT_BORDERS, LEFT_CUSTOM, d1, c1))
    print()
    print('  LEFT FOR F2b, AND NOT BY OMISSION:')
    print('    %d BORDER uses. --alv-surface-deep is a surface token, and'
          % LEFT_BORDERS)
    print('    base has no line token valued %s: --alv-line is #e3e8ea and'
          % LITERAL)
    print('    --alv-line-soft is #f1f3f5. F2b decides whether they become')
    print('    var(--alv-line) - a 1.04:1 change on mostly 1px borders.')
    print('    %d custom-property declarations: base\'s own :root definition'
          % LEFT_CUSTOM)
    print('    of the token, which is not a use and never can be, plus TWO')
    print('    page-local --future-light definitions - spent on a fill three')
    print('    times and on a border once, which is the same question.')
    print()
    print('  EXCLUDED - no :root in scope, so var() would resolve to unset:')
    for rel in NO_TOKEN_SCOPE:
        print('    %s' % rel)
    print('=' * 70)


if __name__ == '__main__':
    main()
