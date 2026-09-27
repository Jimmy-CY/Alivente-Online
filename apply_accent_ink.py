# -*- coding: utf-8 -*-
"""apply_accent_ink.py - Section F round F2a-2, 26 Sep 2026.

#0a5e6a -> var(--alv-accent-ink). 120 sites across 41 templates.

The second colour of the exact-match literal sweep. Unlike F2a-1, this one
needs NO property split. base declares --alv-accent-ink as "hover /
pressed", and that is what almost every site is:

    interaction state (:hover, :focus, :active, .active)      99
    the dark end of a linear-gradient paired with #0e7c8b     17
    resting - a shadow, three text colours, two list values    6

Properties carrying it: border-color 42, background-color 28, background 25,
gradient stops 19, color 5, box-shadow 3. Every one a legitimate use of a
darker accent, so all 120 take the token.

THE INSTINCT THAT WAS WRONG, AND WHY IT IS RECORDED HERE.
Two selectors dominate, and base already declares BOTH of them:

    .btn-info:hover         44 sites, 22 files
    .action-primary:hover   22 sites, 11 files

base's own versions use var(--alv-accent-ink) already. That looked like 66 of
120 sites being dead duplicates to DELETE rather than tokenise - the E3
pattern, where a page joins the standard by deleting its local copy.

It is not. Reading what the rules DECLARE rather than trusting their selector
name (lesson 39), every one of those 33 local rules adds two properties base
does not have:

    transform: translateY(-1px);
    box-shadow: 0 2px 4px rgba(0,0,0,0.2);

Deleting them would strip a lift-and-shadow hover from 33 templates. They are
overrides, not duplicates. Each selector counts twice per file because each
rule holds two #0a5e6a declarations - 22 rules and 11 rules respectively.

That hover lift is the largest block of duplicated button CSS found so far,
and it is NOT this round's business. Its own round, after F2a finishes,
decides whether base adopts it and all 33 local rules go.

SIX SITES CONTRADICT BASE, AND ARE TOKENISED ANYWAY - DELIBERATELY.
.action-secondary:hover in projects/projects.html, projects/projects_detail
and projects/project_task_list (the last as a grouped selector with
.action-primary:hover) paints #0a5e6a with white text. base declares that
same state as var(--alv-surface) with var(--alv-ink) - light surface, dark
text. These three carry no extra properties, and the page's <style> comes
after base's, so the local rule wins: on these pages a SECONDARY button
hovers like a PRIMARY one.

Tokenising preserves the divergence, and that is the agreed choice: nothing
moves in this round, and the three rules are deleted in the same standards
round that decides the hover lift, so every button-hover question is settled
on one body of evidence instead of piecemeal.

TWO USES IN A SCRIPT ARE LEFT, AND ONE OF THEM IS ALREADY THE RIGHT PATTERN.
act_expense.html holds two #0a5e6a inside <script>:

    borderColor: '#0a5e6a'                      a Chart.js config - a canvas
                                                needs a real colour string
    Q_INFO = anTok('accent-ink', '#0a5e6a')     reads the token off the DOM
                                                and falls back to the literal

The second is var(--tok, #literal) written in JavaScript. Both stay.

EXCLUDED, AS IN EVERY ROUND OF THIS SWEEP: the five standalone documents and
the one naked fragment that base's :root never reaches. An undefined custom
property is invalid at computed-value time and resolves to `unset`, so var()
there would lose the colour rather than keep it. base.html's own two sites are
held back to F2a-B, which is hand-reviewed and must precede F3.
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
SUFFIX = '.bak_accentink'
CHECK = '--check' in sys.argv

LITERAL = '#0a5e6a'
TOKEN = 'var(--alv-accent-ink)'

# Machine-derived. E3's hand-counted table was wrong for three files and only
# the patcher's own assertion caught it.
EXPECTED = {
    'act_expense.html': 1,
    'act_expense_add.html': 2,
    'act_expense_edit.html': 2,
    'admin_apms.html': 1,
    'categories_management.html': 1,
    'comments_report.html': 1,
    'customer_form.html': 2,
    'customer_invoice_form.html': 2,
    'dashboard_pl.html': 5,
    'finance.html': 6,
    'finance/vacancy_management.html': 2,
    'finance_expense_line_types_edit.html': 3,
    'finance_pl_act.html': 3,
    'finance_valuations_add.html': 4,
    'finance_valuations_edit.html': 5,
    'fsr.html': 2,
    'help_modal_shell.html': 1,
    'help_page.html': 7,
    'home.html': 5,
    'import_recipe.html': 2,
    'meal_plan_calendar.html': 1,
    'meal_plans.html': 1,
    'notifications.html': 2,
    'occupancy_trends.html': 1,
    'physical_invoice_edit.html': 2,
    'physical_invoice_list.html': 2,
    'preview_imported_recipe.html': 3,
    'projects/project_gantt.html': 4,
    'projects/project_subtasks_add.html': 4,
    'projects/project_task_list.html': 2,
    'projects/project_tasks_add.html': 4,
    'projects/project_tasks_edit.html': 4,
    'projects/projects.html': 6,
    'projects/projects_add.html': 4,
    'projects/projects_detail.html': 8,
    'projects/projects_edit.html': 4,
    'properties.html': 2,
    'property_management_dashboard.html': 3,
    'recipe_management.html': 2,
    'suppliers.html': 2,
    'tenant.html': 2,
}

# Left in <script>, on purpose. See the docstring.
IN_SCRIPT = {'act_expense.html': 2}

# No {% extends %}, own <!DOCTYPE> or served as a whole fragment.
NO_TOKEN_SCOPE = (
    'error_pages/connectivity_error.html',
    'invoices/physical_invoice.html',
    'manual_pdf.html',
    'receipts/cash_receipt.html',
    'recipe_pdf.html',
    'total_expense_details.html',
)

# help_modal_shell.html has no {% extends %} but IS in scope: it is an
# @register.inclusion_tag rendered by {% render_help_modal %} into 37 pages,
# every one of which extends base. Checked, not assumed. It is NOT what
# manual_pdf.html renders - that takes the help CONTENT, not this shell.
SHELL = 'help_modal_shell.html'

STYLE = re.compile(r'<style\b[^>]*>(.*?)</style\s*>', re.S | re.I)
SCRIPT = re.compile(r'<script\b[^>]*>(.*?)</script\s*>', re.S | re.I)
HTML_C = re.compile(r'<!--.*?-->', re.S)
DJ_CB = re.compile(r'\{%\s*comment\s*%\}.*?\{%\s*endcomment\s*%\}', re.S | re.I)
DJ_C = re.compile(r'\{#.*?#\}', re.S)
CSS_C = re.compile(r'/\*.*?\*/', re.S)
INLINE = re.compile(r'\bstyle\s*=\s*"([^"]*)"|\bstyle\s*=\s*\'([^\']*)\'', re.S)
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


def css_spans(text):
    """(css_positions, script_positions) - offsets into `text` itself.

    MARKUP COMMENTS FIRST, on the raw text. The house order - CSS comments
    across the whole file, then find <style> - is defeated by
    accept="image/*", whose /* opens a comment running forward to the first
    */ inside the stylesheet, taking the <style> tag with it. Measured, that
    hides the WHOLE stylesheet on three real templates. preview_imported_
    recipe.html, one of this round's 41, carries accept="image/*"."""
    t = text
    for rx in (HTML_C, DJ_CB, DJ_C):
        t = rx.sub(_sp, t)
    if len(t) != len(text):
        raise SystemExit('F2a-2: comment blanking changed length')
    style = [(m.start(1), m.end(1)) for m in STYLE.finditer(t)]
    script = [(m.start(1), m.end(1)) for m in SCRIPT.finditer(t)]
    # CSS comments only INSIDE a style body
    out = list(t)
    for a, b in style:
        out[a:b] = list(CSS_C.sub(_sp, t[a:b]))
    t = ''.join(out)
    inline = []
    for m in INLINE.finditer(t):
        i = 1 if m.group(1) is not None else 2
        a, b = m.start(i), m.end(i)
        if not any(x <= a < y for x, y in style + script):
            inline.append((a, b))
    return t, style + inline, script


def sites(text):
    """The offsets this round may rewrite, and the ones it must not."""
    scan, css, script = css_spans(text)
    take, leave = [], 0
    for m in LIT.finditer(scan):
        if any(a <= m.start() < b for a, b in css):
            take.append(m.start())
        elif any(a <= m.start() < b for a, b in script):
            leave += 1
        else:
            raise SystemExit('F2a-2: a %s sits outside CSS and outside a '
                             'script at offset %d - re-survey before running'
                             % (LITERAL, m.start()))
    return take, leave


def patch(rel):
    path = os.path.join(ROOT, rel)
    text = read(path)
    take, leave = sites(text)
    want = EXPECTED[rel]

    if len(take) != want:
        if TOKEN in text and not take:
            return 0                        # already applied
        raise SystemExit('F2a-2: %s - %d CSS site(s), expected %d'
                         % (rel, len(take), want))
    if leave != IN_SCRIPT.get(rel, 0):
        raise SystemExit('F2a-2: %s - %d script use(s), expected %d'
                         % (rel, leave, IN_SCRIPT.get(rel, 0)))

    before = text
    for pos in reversed(take):
        if text[pos:pos + len(LITERAL)].lower() != LITERAL:
            raise SystemExit('F2a-2: %s - offset %d is %r, not the literal'
                             % (rel, pos, text[pos:pos + len(LITERAL)]))
        text = text[:pos] + TOKEN + text[pos + len(LITERAL):]

    # Self-checks BEFORE anything is written.
    if text.count(TOKEN) - before.count(TOKEN) != want:
        raise SystemExit('F2a-2: %s - token count moved by %d, not %d'
                         % (rel, text.count(TOKEN) - before.count(TOKEN), want))
    after_take, after_leave = sites(text)
    if after_take:
        raise SystemExit('F2a-2: %s - %d literal(s) still in CSS'
                         % (rel, len(after_take)))
    if after_leave != leave:
        raise SystemExit('F2a-2: %s - the script uses changed' % rel)

    if not CHECK:
        bak = path + SUFFIX
        if not os.path.exists(bak):
            CRLF[bak] = CRLF.get(path)
            write(bak, before)
        write(path, text)
    return want


def guard_scope():
    for rel in NO_TOKEN_SCOPE:
        path = os.path.join(ROOT, rel)
        if not os.path.isfile(path):
            raise SystemExit('F2a-2: %s is not in this tree' % rel)
        t = read(path)
        if 'var(--alv-' in t:
            raise SystemExit('F2a-2: %s has gained a var(--alv-*) and has no '
                             ':root to resolve it' % rel)
        if re.search(r'\{%\s*extends\b', t):
            raise SystemExit('F2a-2: %s now extends a template - re-survey its '
                             'token scope before excluding it' % rel)
    # The shell is in scope only because every page that renders it extends
    # base. If that stops being true, this round's premise fails.
    tag = os.path.join(HERE, 'pages', 'templatetags', 'help_modal_tags.py')
    if os.path.isfile(tag):
        if "inclusion_tag('%s')" % SHELL not in read(tag):
            raise SystemExit('F2a-2: %s is no longer an inclusion tag - '
                             're-survey its token scope' % SHELL)
    n = 0
    for d, _x, fs in os.walk(ROOT):
        for f in fs:
            if not f.endswith('.html') or '.bak_' in f:
                continue
            if f == SHELL:
                continue
            # A MENTION IS NOT A USE (lesson 34). The shell's own header
            # comment names the render_help_modal tag in prose, and the
            # first version of this guard read that as a use and refused
            # the whole round.
            t = read(os.path.join(d, f))
            for rx in (HTML_C, DJ_CB, DJ_C):
                t = rx.sub(_sp, t)
            if re.search(r'\{%\s*render_help_modal\b', t):
                n += 1
                if not re.search(r'\{%\s*extends\b', t):
                    raise SystemExit('F2a-2: %s renders the help modal and '
                                     'does not extend base - %s would lose '
                                     'its tokens there'
                                     % (os.path.basename(f), SHELL))
    if n < 30:
        raise SystemExit('F2a-2: only %d page(s) render the help modal - '
                         'expected ~37; re-survey' % n)
    return n


# A SENTINEL THAT QUOTES A LITERAL IS A DEBT THIS ROUND HAS TO PAY.
# Push-PendingChanges.ps1 carries 188 sentinels - strings it asserts are
# present in the tree - and two of them quote #0a5e6a, both recorded by the
# deeper-teal round. Tokenising the literal makes the sentinel's own text
# unfindable, so the FIRST laptop sweep of this round stopped on
#
#     FAIL  pages\templates\suppliers.html
#           (and so does a page-local btn-info hover)  - not found
#
# The sentinel is not wrong, it is out of date, and -Force would only hide
# that. It is rewritten to the tokenised form, which says MORE than the old
# one did: the page-local hover is on the house token, not merely on some
# dark teal. Scanned for the whole set, exactly two sentinels quote this
# colour and NONE quotes #f1f3f5, #e9ecef, #f8f9fa or #0e7c8b - so F2a-1 was
# safe and F2a-3/4/5 will be.
#
# THE SECOND ONE IS BASE'S, AND IT IS LEFT ALONE ON PURPOSE:
#     .sidebar-toggle:hover { background: #0a5e6a;
# base is held back to F2a-B, so that sentinel still passes - and it will go
# red on the round that tokenises base. That is the deferral working
# (lesson 53), and F2a-B must rewrite it rather than force past it.
SENTINEL_OLD = ("Text = 'border-color: #0a5e6a';         "
                "What = 'and so does a page-local btn-info hover'")
SENTINEL_NEW = ("Text = 'border-color: var(--alv-accent-ink)'; "
                "What = 'and so does a page-local btn-info hover'")

LATER = [
    ('alv_rounds.py',
     "    '.bak_linesoft',\n]",
     "    '.bak_linesoft',\n    '.bak_accentink',\n]"),
    ('Push-PendingChanges.ps1',
     "    'test_line_soft.py'",
     "    'test_line_soft.py'\n    'test_accent_ink.py'"),
    ('Push-PendingChanges.ps1', SENTINEL_OLD, SENTINEL_NEW),
]


def patch_later():
    done = 0
    for name, old, new in LATER:
        path = os.path.join(HERE, name)
        text = read(path)
        if new in text:              # decided by the NEW text alone (47)
            continue
        if text.count(old) != 1:
            raise SystemExit('F2a-2/LATER: anchor matched %d times in %s'
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
    print('SECTION F, ROUND F2a-2 - %s -> %s - %s'
          % (LITERAL, TOKEN, 'CHECK ONLY' if CHECK else 'APPLYING'))
    print('=' * 70)
    pages = guard_scope()
    print('  the help modal shell is rendered into %d base-extending pages'
          % pages)
    total = files = 0
    for rel in sorted(EXPECTED):
        n = patch(rel)
        if n:
            files += 1
            print('  %-42s %2d' % (rel, n))
        else:
            print('  %-42s already applied' % rel)
        total += n
    later = patch_later()
    print('-' * 70)
    print('  %d literal(s) tokenised across %d file(s); %d LATER edit(s).'
          % (total, files, later))
    print()
    print('  LEFT IN <script> - a canvas needs a real colour, and anTok is')
    print('  already var(--tok, #literal) written in JavaScript:')
    for rel in sorted(IN_SCRIPT):
        print('    %-42s %d' % (rel, IN_SCRIPT[rel]))
    print()
    print('  TOKENISED THOUGH IT CONTRADICTS BASE, by agreement - the three')
    print('  Projects pages whose .action-secondary:hover paints a PRIMARY')
    print('  hover. Deleted in the button-standards round, not here.')
    print()
    print('  EXCLUDED - no :root in scope, so var() would resolve to unset:')
    for rel in NO_TOKEN_SCOPE:
        print('    %s' % rel)
    print('  HELD BACK - base.html\'s own 2, to F2a-B (hand-reviewed).')
    print('=' * 70)


if __name__ == '__main__':
    main()
