# -*- coding: utf-8 -*-
"""SECTION G, ROUND G3a - THE PAGE TITLE IS 32px ON A PHONE ON 20 PAGES

base declares the page title twice:

    .page-title-h2 { text-align: center; margin-top: .5rem; margin-bottom: 1rem; }
    @media (...small...) { .page-title-h2 { font-size: 1.25rem; } }   <- line 3960

THE PHONE RULE REACHES THE CLASS AND NOTHING ELSE. A page that writes
`<h2><center>TITLE</center></h2>` looks the same on a desktop and keeps
Bootstrap's 2rem on a phone.

Rendered, every page that extends base, at 390px:

    20 - 20.8px   96 pages   <- all 81 .page-title-h2 wearers are here
    32px          26 pages   <- not one of them wears the class

PROPERTIES, SUPPLIERS, TENANTS AND FINANCE ARE IN THE 26. The pages held up
as the reference have a title 60% larger on a phone than the pages that were
brought to the standard.

base's own standards block, line 281, says of these pages:

    "22 list pages still write h2 > center, which renders the same and is a
     mechanical tidy for a later round, not a second standard."

"Renders the same" IS FALSE ON A PHONE - 32px against 20px - so it is not a
mechanical tidy either. The note is corrected in the same round. (Lesson 20:
a written finding is a measurement too.)

WHAT THIS ROUND DOES NOT DO
---------------------------
Twenty-one pages, one edit each, and nothing else:

    <h2><center>TITLE</center></h2>  ->  <h2 class="page-title-h2">TITLE</h2>

  * The <h5><center>sentence</center></h5> SUBTITLE on eleven of them is left
    exactly as it is. It is not a mistake: test_heading_standard's rule is
    that an h4 holds a mode label and SHOUTS while an h5 holds a descriptive
    sentence in sentence case, and these are the h5 form. base declares no
    .page-subtitle-h5 - only lease_timeline does, locally - so giving them a
    class means adding one to base, which is a round of its own.
  * The six pages with a hand-rolled `<h2 class="mb-1">` header are NOT here.
    Five carry an icon, an inline #2c3e50 and a descriptive paragraph, and
    the sixth (dashboard_pl) holds a RECORD NAME whose case is not ours to
    change. Those are content decisions, not a class swap.
  * Three of these pages carry a landscape-phone rule that sizes `h2` BY
    ELEMENT (finance_pl_act 16px, cashflow_forecast 14px). Adding a class
    does not stop an element selector matching, so they are untouched - and
    the suite renders at that viewport to prove it.

Backups: .bak_housetitle, written with the ORIGINAL's line endings.
Idempotent. --check prints and writes nothing.
"""
import os
import re
import sys

import alv_tree

CHECK = '--check' in sys.argv
HERE = os.getcwd()
ROOT = os.path.join(HERE, 'pages', 'templates')
SUFFIX = '.bak_housetitle'
CRLF = {}

TITLE_CLS = 'page-title-h2'

# Every one, written out. The title text is the anchor, so a page whose
# heading has been reworded stops the round instead of being rewritten blind.
JOBS = [
    ('customer_list.html', 'INVOICE CUSTOMERS'),
    ('finance.html', 'FINANCE'),
    ('finance_expense.html', 'EXPENSES'),
    ('finance_expense_line_types.html', 'EXPENSE LINE TYPES'),
    ('finance_expense_types.html', 'EXPENSE TYPES'),
    # A BARE &, not &amp; - the file really is written that way, and this
    # round changes the wrapper, not the text.
    ('finance_pl_act.html', 'PROFIT & LOSS'),
    ('finance_revenue.html', 'REVENUE'),
    ('finance_revenue_line_types.html', 'REVENUE LINE TYPES'),
    ('finance_revenue_types.html', 'REVENUE TYPES'),
    ('finance_valuations.html', 'PROPERTY VALUATIONS'),
    ('login.html', 'LOGIN'),
    # A TWENTY-FIRST, added 30 Sep. This list was written on 27 Sep
    # and notifications.html was not in it. Its heading is the same
    # shape as the other twenty, character for character, and the
    # census gate below asks the whole tree - so leaving it out would
    # have stopped the round rather than quietly shipping 20 of 21.
    ('notifications.html', 'NOTIFICATIONS DASHBOARD'),
    ('occupancy_trends.html', 'PERFORMANCE TRENDS'),
    ('physical_invoice_list.html', 'PHYSICAL INVOICES'),
    ('properties.html', 'PROPERTIES'),
    ('property_management_dashboard.html', 'PROPERTY DASHBOARD'),
    ('suppliers.html', 'SUPPLIERS'),
    ('tenant.html', 'TENANTS'),
    ('finance/cashflow_forecast.html', 'FORECASTED CASHFLOWS'),
    ('finance/financial_indicators.html', 'FINANCIAL INDICATORS'),
    ('finance/vacancy_management.html', 'VACANCY MANAGEMENT'),
]

# base's own note about these pages, which this round makes untrue.
NOTE_OLD = ("      h2.page-title-h2 and h4.page-subtitle-h4 and styles neither. 66 pages\n"
            "      do. 22 list pages still write h2 > center, which renders the same and\n"
            "      is a mechanical tidy for a later round, not a second standard.")
NOTE_NEW = ("      h2.page-title-h2 and h4.page-subtitle-h4 and styles neither. 117 pages\n"
            "      do.\n"
            "\n"
            "      THE h2 > center SPELLING WAS NOT THE SAME THING, and this note used\n"
            "      to say it was. The phone rule below sizes .page-title-h2 at 1.25rem\n"
            "      and reaches THE CLASS ONLY, so a hand-written h2 > center kept\n"
            "      Bootstrap's 2rem - 32px against 20px, measured at 390px, with\n"
            "      Properties, Suppliers, Tenants and Finance among the larger set.\n"
            "      G3a moved all 21 of them onto the class on 30 Sep. What is left\n"
            "      is six hand-rolled headers that need a content decision, not a\n"
            "      class swap.")

HTML_C = re.compile(r'<!--.*?-->', re.S)
DJ_CB = re.compile(r'\{%\s*comment\s*%\}.*?\{%\s*endcomment\s*%\}', re.S | re.I)
DJ_C = re.compile(r'\{#.*?#\}', re.S)
STYLE = re.compile(r'<style\b[^>]*>(.*?)</style\s*>', re.S | re.I)
SCRIPT = re.compile(r'<script\b[^>]*>(.*?)</script\s*>', re.S | re.I)


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


def blanked(t):
    """Comments blanked on the RAW text FIRST, then script and style bodies.
    The house order is defeated by accept="image/*" (lesson 61)."""
    t = HTML_C.sub(_sp, t)
    t = DJ_CB.sub(_sp, t)
    t = DJ_C.sub(_sp, t)
    for rx in (STYLE, SCRIPT):
        out, pos = [], 0
        for m in rx.finditer(t):
            out.append(t[pos:m.start(1)])
            out.append(re.sub(r'[^\n]', ' ', m.group(1)))
            pos = m.end(1)
        out.append(t[pos:])
        t = ''.join(out)
    return t


def patch(rel, title):
    path = os.path.join(ROOT, rel.replace('/', os.sep))
    if not os.path.isfile(path):
        raise SystemExit('G3a: %s is not on disk' % rel)
    text = read(path)

    old = '<h2><center>%s</center></h2>' % title
    new = '<h2 class="%s">%s</h2>' % (TITLE_CLS, title)
    if new in text and old not in text:
        return None                       # already applied

    # THE ANCHOR IS COUNTED IN THE MARKUP, NOT THE WHOLE FILE. finance_expense
    # writes <center>EXPENSES</center> a second time for its print header, and
    # a naive count of the TITLE would have found two.
    scan = blanked(text)
    if scan.count(old) != 1:
        raise SystemExit('G3a: %s - the heading anchor matched %d times: %s'
                         % (rel, scan.count(old), old))
    at = scan.index(old)
    text = text[:at] + new + text[at + len(old):]

    # --- self-checks BEFORE anything is written ---------------------------
    after = blanked(text)
    if after.count(new) != 1:
        raise SystemExit('G3a: %s - the new heading is not in the output once'
                         % rel)
    if re.search(r'<h2><center>', after):
        raise SystemExit('G3a: %s - an h2 > center survived' % rel)
    for what in ('<h2', '</h2>', '<h5', '<center>', '</center>'):
        before_n = blanked(read(path)).count(what)
        want = before_n - (1 if what in ('<center>', '</center>') else 0)
        if after.count(what) != want:
            raise SystemExit('G3a: %s - %s went %d -> %d, wanted %d'
                             % (rel, what, before_n, after.count(what), want))
    if title not in after:
        raise SystemExit('G3a: %s - the title text is gone' % rel)

    if not CHECK:
        bak = path + SUFFIX
        if not os.path.exists(bak):
            CRLF[bak] = CRLF.get(path)
            write(bak, read(path))
        write(path, text)
    return title


def patch_base():
    """base's note said these pages render the same. They do not."""
    path = os.path.join(ROOT, 'base.html')
    text = read(path)
    # DECIDED BY A SENTENCE THAT EXISTS. This line used to read
    # NOTE_NEW.split('\n')[2], which is the BLANK line between the two
    # paragraphs - and an empty string is in every file ever written. The
    # round reported "base's note already correct" on a base that still
    # carried the old note, every time, and would have shipped the page
    # edits with the note they contradict. Ask for a sentence.
    MARK = 'THE h2 > center SPELLING WAS NOT THE SAME THING'
    if MARK in text:
        return False
    if text.count(NOTE_OLD) != 1:
        raise SystemExit('G3a: base.html - the note anchor matched %d times'
                         % text.count(NOTE_OLD))
    if not CHECK:
        bak = path + SUFFIX
        if not os.path.exists(bak):
            CRLF[bak] = CRLF.get(path)
            write(bak, text)
        # THE NOTE IS A COMMENT. Nothing outside the comment may move.
        #
        # AND IT IS A DJANGO COMMENT, not a CSS one. This check stripped
        # /* */ and compared, which removed nothing at all here - base's
        # standards block opens with {% comment %} on line 4 - so the two
        # sides always differed and the round refused itself. It had never
        # been run, so nobody had found out.
        out = text.replace(NOTE_OLD, NOTE_NEW)

        def _inert(s):
            s = DJ_CB.sub('', s)
            return re.sub(r'/\*.*?\*/', '', s, flags=re.S)

        a, b = _inert(text), _inert(out)
        if a != b:
            raise SystemExit('G3a: base.html - the note edit reached live code')
        if a == text:
            raise SystemExit('G3a: base.html - the comment stripper removed '
                             'nothing, so this check proves nothing')
        write(path, out)
    return True


# WHERE A ROUND REGISTERS IS NOT A DETAIL. These anchors were written on
# 27 Sep and put .bak_housetitle after .bak_bartop, which was last then.
# Eighteen rounds have landed since. ROUNDS is an ORDER, and as_left_by
# walks forward from a round's place in it to find the next backup of a
# file - so registering in the middle would tell every later round that
# this one came first, and hand them the wrong "as I left it". It runs
# today, so it goes last today.
LATER = [
    ('alv_rounds.py',
     "    '.bak_applyclose',\n]",
     "    '.bak_applyclose',\n    '.bak_housetitle',\n]"),
    ('Push-PendingChanges.ps1',
     "    'test_filter_on_close.py'",
     "    'test_filter_on_close.py'\n    'test_house_title.py'"),
]


def patch_later():
    done = 0
    for name, old, new in LATER:
        path = os.path.join(HERE, name)
        text = read(path)
        if new in text:
            continue
        if text.count(old) != 1:
            raise SystemExit('G3a/LATER: anchor matched %d times in %s'
                             % (text.count(old), name))
        if not CHECK:
            bak = path + SUFFIX
            if not os.path.exists(bak):
                CRLF[bak] = CRLF.get(path)
                write(bak, text)
            write(path, text.replace(old, new))
        done += 1
    return done


CODE_ONLY = '''def code_only(text):
    """Python source with its comments and its docstrings blanked out,
    line for line, so a detector reads CODE and not prose.

    LESSON 21, INSIDE THE INSTRUMENT - 30 Sep 2026. G3a's patcher carried
    a comment explaining that it used alv_tree and not a walk of its own
    root, and it NAMED the call it was avoiding. walks_own_root read the
    words, found a template root assigned two lines above, and counted
    the file. The debt rose by one, two suites failed, and nothing was
    wrong.

    Every gate in this repo strips comments before it reads markup or
    CSS. This one reads PYTHON, and did not. tokenize is exact where a
    regex would not be: it knows a # inside a string is not a comment,
    which matters in a repo whose scripts are full of hexes.

    Spans are blanked rather than removed, so every row and column stays
    where it was and the assignment-reader below still sees a statement
    per line. Unparsable source is returned untouched: measuring it as it
    stands is honest, and refusing to measure it is not.
    """
    lines = text.split('\\n')
    try:
        toks = list(tokenize.generate_tokens(io.StringIO(text).readline))
    except Exception:
        return text
    STARTS = (tokenize.NEWLINE, tokenize.NL, tokenize.INDENT,
              tokenize.DEDENT, tokenize.ENCODING)
    kill, prev = [], None
    for tok in toks:
        drop = tok.type == tokenize.COMMENT
        if tok.type == tokenize.STRING and (prev is None or prev in STARTS):
            drop = True          # a string opening a statement: a docstring
        if drop:
            (r1, c1), (r2, c2) = tok.start, tok.end
            for r in range(r1, r2 + 1):
                a = c1 if r == r1 else 0
                b = c2 if r == r2 else len(lines[r - 1])
                kill.append((r - 1, a, b))
        prev = tok.type
    for r, a, b in kill:
        ln = lines[r]
        lines[r] = ln[:a] + ' ' * (b - a) + ln[b:]
    return '\\n'.join(lines)


'''

CENSUS = [
    # Both suites carry the detector VERBATIM, and X11 says why in its own
    # docstring: "Two detectors and one constant is how X0's first ceiling
    # came out wrong." So the repair goes into both, identically.
    ('test_tree_roots.py', 'test_waiting_down.py'),
]

DETECT_WAS = """    walked = set(re.findall(r'os\\.walk\\(\\s*([A-Za-z_][\\w.]*)\\s*\\)', text))"""
DETECT_NOW = """    # CODE, NOT PROSE - 30 Sep. This line used to read the whole file,
    # comments included, so a comment that NAMED os.walk of a root was
    # indistinguishable from a call to it. G3a's own patcher was counted
    # that way. Every other gate in this repo strips comments before it
    # reads; this one reads Python, and now does too.
    text = code_only(text)
    walked = set(re.findall(r'os\\.walk\\(\\s*([A-Za-z_][\\w.]*)\\s*\\)', text))"""

CONTROL_AT = """ok(not walks_own_root('for a, b, c in alv_tree.walk3():\\n    pass\\n'),
   '  and does not see a converted loop')"""
CONTROL_NOW = """ok(not walks_own_root('for a, b, c in alv_tree.walk3():\\n    pass\\n'),
   '  and does not see a converted loop')

# THE SHAPE THAT FOOLED IT, 30 Sep. A file that says os.walk of a template
# root IN A COMMENT and never calls it. This detector counted G3a's patcher
# for exactly this, so the control is kept executable.
ok(not walks_own_root("T = os.path.join(R, 'pages', 'templates')\\n"
                      "# this file does not os.walk(T) - it uses alv_tree\\n"
                      "for p in alv_tree.templates():\\n    pass\\n"),
   '  and does NOT see a walk that exists only in a comment - which is '
   'what it saw on 30 Sep, in the round that fixed it')
ok(walks_own_root("T = os.path.join(R, 'pages', 'templates')\\n"
                  "# a comment mentioning nothing\\n"
                  "for a, b, c in os.walk(T):\\n    pass\\n"),
   '  while a REAL walk beside a comment is still seen - the fix removes '
   'prose, not sight')"""


TREE_WAS = """MENTIONS_ONLY = {
    'test_waiting_down.py': 'X11  the words are in two string literals - a '
                            'borrowed detector and the CONTROL that proves '
                            'it works. No os.walk call in the parse tree.',
}"""

TREE_NOW = """MENTIONS_ONLY = {
    'test_waiting_down.py': 'X11  the words are in two string literals - a '
                            'borrowed detector and the CONTROL that proves '
                            'it works. No os.walk call in the parse tree.',
    'test_house_title.py': 'G3a  the same shape, one round later. It lifts '
                           'the detector out of X0 and runs it against four '
                           'CONTROL strings - one of which is a walk of a '
                           'template root, because the whole point is that '
                           'the detector still sees a real one. It reads the '
                           'tree through alv_tree and calls os.walk nowhere.',
}"""


def patch_tree():
    """A NEW SUITE THAT SAYS THE WORDS MUST BE ACCOUNTED FOR.

    X11's register gate asks that every file the crude net finds sits on
    exactly one of alv_tree's five lists - and it found this round's own
    suite, which carries `pages, templates` and a walk inside CONTROL
    strings. That is what MENTIONS_ONLY exists for, and X11 put its own
    suite there for exactly the same reason.

    Excusing it by loosening the net would be the wrong repair: the net
    is crude ON PURPOSE, and a fifth list is how X11 chose to answer a
    crude net honestly."""
    path = os.path.join(ROOT, 'alv_tree.py')
    if not os.path.isfile(path):
        path = os.path.join(HERE, 'alv_tree.py')
    text = read(path)
    if 'test_house_title.py' in text:
        return False
    if text.count(TREE_WAS) != 1:
        raise SystemExit('G3a: alv_tree.py - MENTIONS_ONLY matched %d times'
                         % text.count(TREE_WAS))
    out = text.replace(TREE_WAS, TREE_NOW)
    if not CHECK:
        bak = path + SUFFIX
        if not os.path.exists(bak):
            CRLF[bak] = CRLF.get(path)
            write(bak, text)
        write(path, out)
    return True


def patch_census():
    """The detector learns to read code. Both copies, or neither."""
    done = 0
    for name in CENSUS[0]:
        path = os.path.join(HERE, name)
        if not os.path.isfile(path):
            raise SystemExit('G3a: %s is not on disk' % name)
        text = read(path)
        if 'def code_only(' in text:
            continue
        if text.count(DETECT_WAS) != 1:
            raise SystemExit('G3a: %s - the detector line matched %d times'
                             % (name, text.count(DETECT_WAS)))
        out = text.replace(DETECT_WAS, DETECT_NOW)
        # The helper goes in front of the detector that uses it.
        at = out.index('def walks_own_root(text):')
        out = out[:at] + CODE_ONLY + out[at:]
        if 'import tokenize' not in out:
            out = out.replace('import re\n', 'import io\nimport re\n'
                                             'import tokenize\n', 1)
        if name == 'test_tree_roots.py':
            if out.count(CONTROL_AT) != 1:
                raise SystemExit('G3a: %s - the control anchor matched %d '
                                 'times' % (name, out.count(CONTROL_AT)))
            out = out.replace(CONTROL_AT, CONTROL_NOW)
        for must in ('import tokenize', 'def code_only(',
                     'text = code_only(text)'):
            if must not in out:
                raise SystemExit('G3a: %s - %s did not land' % (name, must))
        if not CHECK:
            bak = path + SUFFIX
            if not os.path.exists(bak):
                CRLF[bak] = CRLF.get(path)
                write(bak, text)
            write(path, out)
        done += 1
    return done


def main():
    print('=' * 74)
    print('SECTION G, ROUND G3a - THE HOUSE TITLE, WHERE THE PHONE RULE '
          'CAN REACH IT - %s' % ('CHECK ONLY' if CHECK else 'APPLYING'))
    print('=' * 74)
    done = 0
    for rel, title in JOBS:
        r = patch(rel, title)
        if r is None:
            print('  %-42s already applied' % rel)
            continue
        print('  %-42s %s' % (rel, title))
        done += 1
    note = patch_base()
    census = patch_census()
    tree = patch_tree()
    print('  the new suite is accounted for on alv_tree.MENTIONS_ONLY: %s'
          % ('added' if tree else 'already there'))
    later = patch_later()
    print('  the debt census reads code, not prose - %d suite(s)' % census)
    print('-' * 74)
    print("  %d title(s) moved onto .%s; base's note %s; %d LATER edit(s)."
          % (done, TITLE_CLS, 'corrected' if note else 'already correct',
             later))
    print()
    print('  NOT IN THIS ROUND, on purpose:')
    # COUNTED, NOT REMEMBERED. This line said 11 from the day it was
    # written; there are more than that now, and a number a round states
    # about the tree should be read off the tree.
    # alv_tree, NOT os.walk(ROOT). The debt census in test_tree_roots
    # counts scripts that build a template root and walk it, and its
    # ceiling may only FALL - a new reader of the tree has no business
    # adding to a debt the X rounds spent a week paying down.
    #
    # THIS COMMENT IS ALSO THE REASON PART 3 OF THIS ROUND EXISTS. Written
    # exactly as it stands, it made the census count this file: the
    # detector read the words os.walk(ROOT) in prose and believed them.
    # Lesson 21, inside the measuring instrument. The detector now strips
    # comments before it looks, so these two lines say what they mean and
    # are counted as what they are - nothing.
    # counts scripts that build a template root and walk it, and the
    # ceiling may only fall - this count is a new reader of the tree, and
    # a new reader has no business adding to a debt the X rounds spent a
    # week paying down.
    n_h5 = 0
    for _p in alv_tree.templates():
        n_h5 += len(re.findall(r'<h5[^>]*>\s*<center>', blanked(read(_p))))
    print('    the %d h5 > center subtitles - base declares no '
          '.page-subtitle-h5' % n_h5)
    print('    the 6 hand-rolled mb-1 headers - a content decision, not a '
          'class swap')
    print('=' * 74)


if __name__ == '__main__':
    main()
