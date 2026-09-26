# -*- coding: utf-8 -*-
"""apply_line_soft.py - Section F round F2a-1, 26 Sep 2026.

THE FIRST COLOUR OF THE LITERAL SWEEP: #f1f3f5 -> var(--alv-line-soft).

F2a's claim is that a hex literal which is EXACTLY a token's value can
become var(--token) with no pixel change anywhere. #f1f3f5 is the
smallest of the five such colours, so it goes first and proves the
machinery before the accent's 358 sites go anywhere near it.

WHAT THE SURVEY FOUND, AND WHERE IT STOPPED.
30 uses across 16 files, every one inside a <style> block - none inline,
none in markup, none in a script. But they are not 30 of the same thing:

    border-bottom   17
    border-top       7        24 LINES   - this round
    background       5
    background-color 1         6 FILLS   - NOT this round

base declares --alv-line-soft under "Surfaces and ink", beside
--alv-line: #e3e8ea. It is the softer of two LINE colours. Using it for a
FILL is the same trap base's own print stylesheet fell into with
#55606b - a value that happens to match a token, bound forever to a
token that means something else. Substituting those six would be
pixel-identical and semantically false, so they wait for F2b, where the
question "what token should a muted panel fill be?" gets answered
properly. Exact match means "no pixel moved". It does not mean "correct".

The six left behind, named so the suite can assert they are still there:

    admin_apms.html                     .admin-tab.future-tab:hover
    finance/financial_indicators.html   .fi-weights-reset:hover
    home.html                           .ins-tag--grey, .ins-tag--low
    household_member_management.html    .status-inactive
    property_management_dashboard.html  .dash-card-disabled

THE FILE THAT CANNOT HAVE TOKENS.
manual_pdf.html carries one #f1f3f5 and is excluded, along with four
other standalone documents and one naked fragment. They have their own
<!DOCTYPE> and no {% extends %}, so base's :root never reaches them. An
undefined custom property does NOT make a declaration no-op - it makes it
invalid at computed-value time, which resolves to `unset`. A border would
not keep its old colour; it would lose it. Corroboration that this is
diagnosis and not guesswork: not one of the six uses var(--alv-*)
anywhere today.

    error_pages/connectivity_error.html   own doctype
    invoices/physical_invoice.html        own doctype
    manual_pdf.html                       own doctype  <- has a #f1f3f5
    receipts/cash_receipt.html            own doctype
    recipe_pdf.html                       own doctype
    total_expense_details.html            fragment served whole

THE COMMENT ORDER, WHICH IS NOT THE HOUSE ORDER.
Every patcher in this tree blanks comments as
    HTML_COMMENT.sub(sp, CSS_COMMENT.sub(sp, text))
- CSS first, across the whole file. That order is defeated by
accept="image/*" on a file input: the /* opens a "comment" that runs
forward to the first */ inside the stylesheet and swallows the <style>
tag with it. On passport_management.html it eats 4261 bytes - 9.4% of the
file - and passport_management is one of THIS round's 14 files.

So the order here is inverted: markup comments first, on the raw text
(none of <!-- -->, {# #} or {% comment %} can be opened by an attribute
value), THEN find the <style> bodies, THEN strip CSS comments only inside
them. base.html's own standards comment warns about the mirror image of
this bug - a <style> tag written inside an HTML comment - and this order
handles both.

WHY THE GATE IS NOT A PICTURE.
The first gate I built for this round rendered every file before and
after and compared the PNGs. Measured, it is VACUOUS: a border changed to
#ff0000 was invisible at 1280px on all five sample files and invisible at
390px on home.html, because these rules live behind @media (max-width)
card conversions and on tooltip and :hover states that a static render
never paints. "Identical" meant "neither side drew anything".

The real gate is a ROUND TRIP, and it is strictly stronger:

    expand(CSS before) == expand(CSS after)

where expand() replaces every var(--alv-x[, fallback]) with the value
base declares. If the two expansions are byte-identical then no
declaration's value changed anywhere - in any media query, on any
pseudo-class, painted or not. A wrong colour cannot match it and an
undefined token cannot expand at all. Proved sensitive on all 14 files
before being trusted: see test_line_soft.py section 3.
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
SUFFIX = '.bak_linesoft'
CHECK = '--check' in sys.argv

LITERAL = '#f1f3f5'
TOKEN = 'var(--alv-line-soft)'

# Counts are machine-derived, never hand-written. E3's hand-counted table
# was wrong for three files and only the patcher's own assertion caught it.
EXPECTED = {
    'act_expense.html': 1,
    'asset_detail.html': 1,
    'finance_expense_add.html': 1,
    'finance_expense_edit.html': 1,
    'home.html': 2,
    'household_member_management.html': 2,
    'open_invoices_report.html': 1,
    'passport_management.html': 2,
    'physical_invoice_list.html': 2,
    'projects/project_task_list.html': 1,
    'projects/projects.html': 1,
    'property_detail.html': 6,
    'property_management_dashboard.html': 1,
    'title_deeds_management.html': 2,
}

# The fills that stay, and the selector each one paints. Asserted still
# present, so a later careless sweep cannot quietly take them too.
LEFT_ALONE = {
    'admin_apms.html': 1,
    'finance/financial_indicators.html': 1,
    'home.html': 2,
    'household_member_management.html': 1,
    'property_management_dashboard.html': 1,
}

# No {% extends %}, own <!DOCTYPE> or served as a whole fragment: base's
# :root never reaches them, so var() here would resolve to `unset`.
NO_TOKEN_SCOPE = (
    'error_pages/connectivity_error.html',
    'invoices/physical_invoice.html',
    'manual_pdf.html',
    'receipts/cash_receipt.html',
    'recipe_pdf.html',
    'total_expense_details.html',
)

# border, border-top/bottom/left/right, border-color - and deliberately
# NOT background. border-radius cannot match: after `border` the optional
# group must be one of the five or nothing, and then a colon.
BORDER = re.compile(r'(border(?:-bottom|-top|-left|-right|-color)?\s*:'
                    r'[^;{}]*?)' + re.escape(LITERAL), re.I)

STYLE = re.compile(r'<style\b[^>]*>(.*?)</style\s*>', re.S | re.I)
HTML_C = re.compile(r'<!--.*?-->', re.S)
DJ_CB = re.compile(r'\{%\s*comment\s*%\}.*?\{%\s*endcomment\s*%\}', re.S | re.I)
DJ_C = re.compile(r'\{#.*?#\}', re.S)
CSS_C = re.compile(r'/\*.*?\*/', re.S)

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


def style_only(text):
    """Same length as `text`; everything outside a <style> body is spaces,
    and CSS comments inside one are spaces too.

    MARKUP COMMENTS FIRST, on the raw text - see the module docstring.
    Offsets in the result index straight back into `text`."""
    t = text
    for rx in (HTML_C, DJ_CB, DJ_C):
        t = rx.sub(_sp, t)
    keep = [' '] * len(t)
    for m in STYLE.finditer(t):
        body = CSS_C.sub(_sp, m.group(1))
        keep[m.start(1):m.end(1)] = list(body)
    out = ''.join(keep)
    if len(out) != len(text):
        raise SystemExit('F2a-1: the scan changed length - offsets are void')
    return out


def patch(rel):
    path = os.path.join(ROOT, rel)
    text = read(path)
    scan = style_only(text)

    want = EXPECTED[rel]
    hits = [m for m in BORDER.finditer(scan)]
    if len(hits) != want:
        if TOKEN in text and not hits:
            return 0                        # already applied
        raise SystemExit('F2a-1: %s - %d border site(s), expected %d'
                         % (rel, len(hits), want))

    before = text
    for m in reversed(hits):
        a = m.start() + len(m.group(1))
        b = m.end()
        if text[a:b].lower() != LITERAL:
            raise SystemExit('F2a-1: %s - offset %d is %r, not the literal'
                             % (rel, a, text[a:b]))
        text = text[:a] + TOKEN + text[b:]

    # Self-checks BEFORE anything is written.
    if text.count(TOKEN) - before.count(TOKEN) != want:
        raise SystemExit('F2a-1: %s - token count moved by %d, not %d'
                         % (rel, text.count(TOKEN) - before.count(TOKEN), want))
    left = LEFT_ALONE.get(rel, 0)
    if len(re.findall(re.escape(LITERAL), style_only(text), re.I)) != left:
        raise SystemExit('F2a-1: %s - %d literal(s) left in CSS, expected %d'
                         % (rel, len(re.findall(re.escape(LITERAL),
                                                style_only(text), re.I)), left))
    # Nothing outside a <style> body may move, byte for byte.
    if re.sub(r'<style\b[^>]*>.*?</style\s*>', '<style/>', before,
              flags=re.S | re.I) != \
       re.sub(r'<style\b[^>]*>.*?</style\s*>', '<style/>', text,
              flags=re.S | re.I):
        raise SystemExit('F2a-1: %s - markup outside <style> changed' % rel)

    if not CHECK:
        bak = path + SUFFIX
        if not os.path.exists(bak):
            CRLF[bak] = CRLF.get(path)
            write(bak, before)
        write(path, text)
    return want


def guard_scope():
    """The six documents with no token scope must still carry their
    literals, and must still contain no var(--alv-*) at all."""
    for rel in NO_TOKEN_SCOPE:
        path = os.path.join(ROOT, rel)
        if not os.path.isfile(path):
            raise SystemExit('F2a-1: %s is not in this tree' % rel)
        t = read(path)
        if 'var(--alv-' in t:
            raise SystemExit('F2a-1: %s has gained a var(--alv-*) and has '
                             'no :root to resolve it' % rel)
        if re.search(r'\{%\s*extends\b', t):
            raise SystemExit('F2a-1: %s now extends a template - re-survey '
                             'its token scope before excluding it' % rel)


LATER = [
    ('alv_rounds.py',
     "    '.bak_palette',\n]",
     "    '.bak_palette',\n    '.bak_linesoft',\n]"),
    ('Push-PendingChanges.ps1',
     "    'test_palette.py'",
     "    'test_palette.py'\n    'test_line_soft.py'"),
]


def patch_later():
    done = 0
    for name, old, new in LATER:
        path = os.path.join(HERE, name)
        text = read(path)
        if new in text:              # decided by the NEW text alone (47)
            continue
        if text.count(old) != 1:
            raise SystemExit('F2a-1/LATER: anchor matched %d times in %s'
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
    print('SECTION F, ROUND F2a-1 - %s -> %s - %s'
          % (LITERAL, TOKEN, 'CHECK ONLY' if CHECK else 'APPLYING'))
    print('=' * 70)
    guard_scope()
    total = files = 0
    for rel in sorted(EXPECTED):
        n = patch(rel)
        if n:
            files += 1
            print('  %-40s %2d line(s)' % (rel, n))
        else:
            print('  %-40s already applied' % rel)
        total += n
    later = patch_later()
    print('-' * 70)
    print('  %d border literal(s) tokenised across %d file(s); '
          '%d LATER edit(s).' % (total, files, later))
    print()
    print('  LEFT ALONE - a fill is not a line (F2b decides these):')
    for rel in sorted(LEFT_ALONE):
        print('    %-42s %d' % (rel, LEFT_ALONE[rel]))
    print()
    print('  EXCLUDED - no :root in scope, so var() would resolve to unset:')
    for rel in NO_TOKEN_SCOPE:
        print('    %s' % rel)
    print('=' * 70)


if __name__ == '__main__':
    main()
