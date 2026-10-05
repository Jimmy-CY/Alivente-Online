"""FN-1 - THE SIX FINANCE PAGES JOIN THE REST OF THE APP.

   Demetri, 5 Oct 2026, of Revenue Types, Revenue Line Types, Revenue and
   the three Expense screens: "The Action Buttons ... do not conform to
   our standards. I also don't want the Revenue table to be Green and the
   Expense table to be red."

   THE BUTTONS WERE NOT DRIFT, WHICH CHANGES WHAT THE FIX IS.
   .btn-row-edit and .btn-row-delete are declared in BASE. They are a
   house component - a bordered pill with a text label - used 22 times on
   exactly these six pages and nowhere else. So the app had grown TWO
   sanctioned row-action vocabularies:

       .icon-action-btn in .row-actions   icon only, 34px   119 buttons, 32 pages
       .btn-row-edit / .btn-row-delete    labelled pill      22 buttons,  6 pages

   That is why these pages looked different: not because somebody
   drifted, but because base said two things. Demetri chose the icons,
   and the pills are retired from base in part E.

   FIVE PARTS.

   A. THE 22 CONTROLS. Four variants, counted before a line was written:

          btn-row-edit             8   active, a link
          btn-row-edit-disabled    9   a span, every one carrying a title
          btn-row-delete           2   active, a button
          btn-row-delete-disabled  3   a span, every one carrying a title

      TEN OF THEM CARRY NO TITLE, because they never needed one - the
      word Edit was right there. Take the word away without putting a
      name on the control and you have exactly the defect RA-2 found on
      Passports: a button that says it is disabled without saying what it
      would have done. So every converted control gains title AND
      aria-label; the twelve that already have one keep theirs, because
      those titles say something no generic label could ("Rent/levies
      come from the lease - edit the lease to change them").

      fa-trash-alt becomes fa-trash. .icon-delete draws fa-trash 42 times
      in the tree and fa-trash-alt nowhere else; one name, one picture.

      ONE JUDGEMENT CALL, NAMED RATHER THAN BURIED. finance_revenue.html
      has a disabled-edit that draws a PADLOCK - the lease-driven rows,
      which cannot be edited here. In the house set .icon-lock draws
      fa-ban, so the padlock has no name of its own. It becomes
      .icon-edit .icon-disabled on a pencil, like every other
      cannot-edit-this, and the title keeps the reason. The picture that
      is lost said less than the sentence that stays.

   B. EACH ROW'S ACTIONS GO IN A .row-actions WRAPPER, which is what
      RA-1's ordering standard is read from and what RA-3 has just
      finished giving the rest of the tree.

   C. THE GREEN AND THE RED. The property header rows announced which
      table you were in by colour: Revenue #f0fbf4 on #155724, Expenses
      #fdecee on #721c24, with matching hovers, borders and a gradient on
      the phone card. Both go to base's surface tokens - the same on both
      - and the page title does the announcing instead.

   D. YES AND NO STAY GREEN AND RED, on tokens. That colour means yes and
      no, not revenue and expenses - it is the vocabulary of a tick and a
      cross, and stripping it would take the at-a-glance read out of a
      twelve-month grid. Demetri: "keep them, on house tokens".

   E. base loses .btn-row-edit, .btn-row-delete and their disabled and
      card variants. A component nothing uses is a component the next
      page will use by accident.

   FILES: six templates and base.html.          [test_finance_rows.py]
"""
import os
import re
import sys

import alv_tree as T
from apply_row_wrap import runs_of, OPENS, CLOSES

SUFFIX = '.bak_finrows'

PAGES = ['finance_revenue_types.html', 'finance_revenue_line_types.html',
         'finance_revenue.html', 'finance_expense_types.html',
         'finance_expense_line_types.html', 'finance_expense.html']

# Measured before this was written. An exact total, not a floor.
EXPECT_CONTROLS = 22


def read(path):
    with open(path, encoding='utf-8', newline='') as fh:
        return fh.read()


def write(path, text):
    with open(path, 'w', encoding='utf-8', newline='') as fh:
        fh.write(text)


def backup(path):
    bak = path + SUFFIX
    if not os.path.exists(bak):
        with open(path, 'rb') as src, open(bak, 'wb') as dst:
            dst.write(src.read())


def page(name):
    hits = [p for p in T.templates()
            if T.rel(p).replace(os.sep, '/') == name]
    if len(hits) != 1:
        raise SystemExit('FN-1: %s matched %d templates' % (name, len(hits)))
    return hits[0]


# ===================================================================== A

CONTROL = re.compile(
    r'<(a|button|span)\b([^>]*?)class="([^"]*btn-row-[^"]*)"([^>]*)>'
    r'([\s\S]*?)</\1>')

NAMES = {
    'btn-row-edit': ('icon-action-btn icon-edit', 'Edit'),
    'btn-row-edit-disabled': ('icon-action-btn icon-edit icon-disabled',
                              'Edit'),
    'btn-row-delete': ('icon-action-btn icon-delete', 'Delete'),
    'btn-row-delete-disabled': ('icon-action-btn icon-delete icon-disabled',
                                'Delete'),
}


def convert(m):
    tag, pre, cls, post, inner = m.groups()
    base_name = None
    for k in ('btn-row-edit-disabled', 'btn-row-delete-disabled',
              'btn-row-edit', 'btn-row-delete'):
        if re.search(r'\b%s\b' % re.escape(k), cls):
            base_name = k
            break
    if not base_name:
        return m.group(0)

    house, label = NAMES[base_name]
    # anything else on the class attribute is the page's own hook and stays
    extra = [c for c in cls.split() if not c.startswith('btn-row-')]
    new_cls = ' '.join([house] + extra)

    attrs = pre + post
    # THE NAME THE CONTROL NEEDS NOW IT HAS NO WORDS. Ten of the 22 had
    # no title: they did not need one while 'Edit' was printed beside the
    # icon. An unnamed icon is a control nobody can read.
    if 'title=' not in attrs:
        attrs = attrs.rstrip() + ' title="%s"' % label
    if 'aria-label=' not in attrs:
        attrs = attrs.rstrip() + ' aria-label="%s"' % label

    # the glyph, and nothing else from the body - the word goes
    glyph = re.search(r'<i\b[^>]*class="([^"]*)"[^>]*>\s*</i>', inner)
    icon = glyph.group(1) if glyph else 'fas fa-pencil-alt'
    icon = icon.replace('fa-trash-alt', 'fa-trash')
    # the padlock has no name of its own in the house set; it becomes the
    # pencil its title already explains
    icon = icon.replace('fa-lock', 'fa-pencil-alt')

    return ('<%s%s class="%s"><i class="%s"></i></%s>'
            % (tag, attrs if attrs.startswith(' ') else ' ' + attrs.lstrip(),
               new_cls, icon, tag))


# ===================================================================== C

TINTS = [
    # (page, old, new)
    ('finance_revenue.html', 'background: #f0fbf4;',
     'background: var(--alv-surface);'),
    ('finance_revenue.html', 'color: #155724;', 'color: var(--alv-ink);'),
    ('finance_revenue.html', 'background: #d4edda;',
     'background: var(--alv-surface-deep);'),
    ('finance_revenue.html', 'color: #28a745;', 'color: var(--alv-accent);'),
    ('finance_revenue.html',
     'background: linear-gradient(135deg, #f0fbf4 0%, #e8f7ee 100%);',
     'background: var(--alv-surface);'),
    ('finance_revenue.html', 'border-bottom: 1px solid #c3e6cb;',
     'border-bottom: 1px solid var(--alv-line);'),
    ('finance_revenue.html', 'border: 1px solid #c3e6cb;',
     'border: 1px solid var(--alv-line);'),
    ('finance_expense.html', 'background: #fdecee;',
     'background: var(--alv-surface);'),
    ('finance_expense.html', 'color: #721c24;', 'color: var(--alv-ink);'),
    ('finance_expense.html', 'background: #f8d7da;',
     'background: var(--alv-surface-deep);'),
    ('finance_expense.html', 'color: #dc3545;', 'color: var(--alv-accent);'),
    ('finance_expense.html',
     'background: linear-gradient(135deg, #fdecee 0%, #fbe1e4 100%);',
     'background: var(--alv-surface);'),
    ('finance_expense.html', 'border-bottom: 1px solid #f5c6cb;',
     'border-bottom: 1px solid var(--alv-line);'),
    ('finance_expense.html', 'border: 1px solid #f5c6cb;',
     'border: 1px solid var(--alv-line);'),
]

# ===================================================================== D

# PER DECLARATION, NOT PER PAIR. The first build asked for
# 'background: #d4edda; color: #155724;' as one string, which is how the
# rule reads when you normalise it and not how it is written: base and
# these pages put one declaration per line. Two of the six anchors
# matched and four did not, and the gate said nothing because the gate
# counted controls. Match the value, in any declaration, inside the month
# rules only.
YESNO_MAP = {
    '#d4edda': 'var(--alv-good-soft)',
    '#155724': 'var(--alv-good-ink)',
    '#f8d7da': 'var(--alv-bad-soft)',
    '#721c24': 'var(--alv-bad-ink)',
    '#c3e6cb': 'var(--alv-good-line)',
    '#f5c6cb': 'var(--alv-bad-line)',
}
# ONLY the rules that colour a month. The same hexes appear elsewhere on
# these pages in components this round is not about.
MONTH_RULE = re.compile(r'([^{}]*month-(?:cell|chip)-(?:yes|no)[^{}]*\{)([^{}]*)(\})')


def tokenise_months(text):
    """Returns (text, n). The green still means yes and the red still
    means no - only the spelling moves."""
    hits = [0]

    def one(m):
        body = m.group(2)
        for hexv, tok in YESNO_MAP.items():
            n = len(re.findall(re.escape(hexv) + r'\b', body, re.I))
            if n:
                body = re.sub(re.escape(hexv) + r'\b', tok, body, flags=re.I)
                hits[0] += n
        return m.group(1) + body + m.group(3)

    out = MONTH_RULE.sub(one, text)
    return out, hits[0]

# ===================================================================== E

# RETIRING A RULE IS NOT A REGEX JOB, and the first build proved it. A
# pattern anchored on `.btn-row-` matched the SECOND selector of
#
#     .rev-type-card .btn-row-edit,
#     .rev-type-card .btn-row-edit-disabled { ... }
#
# consumed from there to the closing brace, and left
#
#     .rev-type-card .btn-row-edit,
#     .rev-type-card}
#
# behind on two pages - broken CSS that the round's own gate did not
# catch, because the gate counted CONTROLS and said nothing about whether
# the stylesheet still parsed.
#
# So: walk the rules, take a rule only when EVERY selector in its list
# names a btn-row-* class, and leave any rule that also styles something
# else - which would otherwise lose that component along with this one.
RULE = re.compile(r'([^{}]*)\{([^{}]*)\}')


def retire(text):
    """Remove every rule whose selector list is ONLY btn-row-* names."""
    out = []
    last = 0
    n = 0
    for m in RULE.finditer(text):
        sel = m.group(1)
        # the selector list starts after the previous rule or block edge
        cut = max(sel.rfind('}'), sel.rfind('{'), sel.rfind('*/'))
        names = sel[cut + 1:] if cut >= 0 else sel
        parts = [x.strip() for x in names.split(',') if x.strip()]
        if not parts or not all('btn-row-' in x for x in parts):
            continue
        start = m.start(1) + (cut + 1 if cut >= 0 else 0)
        # take the whitespace in front of it, and the newline after
        while start > 0 and text[start - 1] in ' \t':
            start -= 1
        end = m.end()
        while end < len(text) and text[end] in ' \t':
            end += 1
        if text[end:end + 2] == '\r\n':
            end += 2
        elif text[end:end + 1] == '\n':
            end += 1
        out.append(text[last:start])
        last = end
        n += 1
    out.append(text[last:])
    return ''.join(out), n


def main(argv):
    check = '--check' in argv
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    controls = tints = yesno = wrapped = retired_local = 0

    for name in PAGES:
        p = page(name)
        text = read(p)
        before = text

        # A + the glyph fixes
        text, n = CONTROL.subn(convert, text)
        controls += n

        # C
        for pg_name, old, new in TINTS:
            if pg_name != name:
                continue
            c = text.count(old)
            if c:
                text = text.replace(old, new)
                tints += c

        # D
        text, c = tokenise_months(text)
        yesno += c

        # B - the wrapper RA-1's ordering standard is read from. Same
        # run-grouping as RA-3: buttons with nothing but whitespace and
        # template tags between them are one action column.
        for r in reversed(runs_of(text)):
            a, z = r[0][0], r[-1][1]
            seg = text[a:z]
            if len(OPENS.findall(seg)) != len(CLOSES.findall(seg)):
                raise SystemExit('FN-1: a run on %s is not template-balanced'
                                 % name)
            text = text[:a] + '<span class="row-actions">' + seg \
                + '</span>' + text[z:]
            wrapped += 1

        if text != before and not check:
            backup(p)
            write(p, text)

    # E - base loses the component, and so do the two pages that
    # overrode it on their card layout. A rule whose selector names a
    # class nothing wears is dead weight that reads as live.
    for name in PAGES:
        p = page(name)
        text = read(p)
        text2, n = retire(text)
        if n:
            if not check:
                backup(p)
                write(p, text2)
            retired_local += n

    base = T.path_of('base.html')
    btext = read(base)
    retired = 0
    if '.btn-row-edit' in btext:
        btext, retired = retire(btext)
        if retired and not check:
            backup(base)
            write(base, btext)

    print('FN-1  controls converted : %d' % controls)
    print('FN-1  tints neutralised  : %d' % tints)
    print('FN-1  yes/no tokenised   : %d' % yesno)
    print('FN-1  action columns wrapped : %d' % wrapped)
    print('FN-1  base rules retired : %d' % retired)
    print('FN-1  page rules retired : %d' % retired_local)

    done = (controls or tints or yesno or wrapped or retired
            or retired_local)
    if check:
        if done:
            print('FN-1  NOT APPLIED')
            return 1
        print('FN-1  applied')
        return 0
    if controls not in (0, EXPECT_CONTROLS):
        print('FN-1  REFUSED: %d control(s), expected %d'
              % (controls, EXPECT_CONTROLS))
        return 2
    print('FN-1  ok')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
