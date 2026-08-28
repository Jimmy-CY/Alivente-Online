#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""One verb, one glyph: the Edit icon is a pencil everywhere.

base owns the COLOUR of an icon action button - `.icon-edit { color:
var(--alv-edit) }` - but not the glyph, because the glyph is an `<i>` in each
page's markup. So it drifted, and nothing was watching:

    fa-pencil-alt   properties, tenants, suppliers, customer_list   (4)
    fa-edit         asset_detail, finance_valuations                (2)

Two different pictures for the same verb, on screens a user moves between.
`fa-pencil-alt` is the majority and the one on every list page that has been
through a table round, so the two outliers join it.

ONE OF THE TWO IS MINE - the Valuations round copied the glyph the page
already had instead of the glyph the standard uses. The other, asset_detail,
is inherited.

WHAT IS DELIBERATELY LEFT ALONE. `asset_detail.html` also has a LABELLED bar
button, `<i class="fas fa-edit"></i> Edit Asset`. That keeps its glyph. An
icon standing alone is the only signal the reader gets and has to be
consistent; an icon sitting beside the word "Edit" is decoration, and the word
is doing the work. The rule this patcher applies is exactly that distinction:
only an `<i>` that is alone inside its button is rewritten.

test_icon_buttons.py gains a check that scans EVERY template, so the next page
to disagree fails at the push rather than in front of you.

Run from the repo root.  --check plans without writing.
"""
import os, re, sys, shutil

ROOT   = os.path.dirname(os.path.abspath(__file__))
TPL    = os.path.join(ROOT, 'pages', 'templates')
CHECK  = '--check' in sys.argv
SUFFIX = '.bak_editicon'

HOUSE = 'fa-pencil-alt'
OUTLIER = 'fa-edit'

FILES = ('finance_valuations.html', 'asset_detail.html')

# An <i> ALONE inside its button - nothing but whitespace between it and the
# closing tag. That is the icon-only case, where the picture is the whole
# message.
ALONE = re.compile(
    r'(<i class="fas )%s("></i>\s*</(?:a|button|span)>)' % re.escape(OUTLIER))
# The mobile twin carries extra classes and is followed by a label span, so it
# is matched on its class list instead.
MOBILE = re.compile(r'(<i class="fas )%s( [^"]*mobile-action-icon)'
                    % re.escape(OUTLIER))


def read(p):
    with open(p, encoding='utf-8') as f:
        return f.read()


def rewrite(text):
    text, a = ALONE.subn(r'\g<1>%s\g<2>' % HOUSE, text)
    text, b = MOBILE.subn(r'\g<1>%s\g<2>' % HOUSE, text)
    return text, a + b


def labelled_count(text):
    """`<i ...></i> Edit Asset` - an icon beside a word. Left alone."""
    return len(re.findall(r'<i class="fas fa-[a-z-]+"></i>\s*\w', text))


def main():
    changed, plans = 0, []
    for name in FILES:
        p = os.path.join(TPL, name)
        if not os.path.exists(p):
            sys.exit('! %s is missing - is this the repo root?' % name)
        src = read(p)
        out, n = rewrite(src)

        bad = []
        # The labelled buttons must survive untouched. Counted before and
        # after rather than assumed, because the two rules above are the only
        # thing separating them from the icon-only ones.
        if labelled_count(src) != labelled_count(out):
            bad.append('%s: a labelled button changed glyph (%d -> %d) - only '
                       'icon-only buttons should' % (name, labelled_count(src),
                                                     labelled_count(out)))
        # Nothing but the glyph may move.
        if len(out) - len(src) != n * (len(HOUSE) - len(OUTLIER)):
            bad.append('%s: the edit changed more than the glyph' % name)
        if re.findall(r'icon-edit[^>]*>\s*<i class="fas fa-edit', out):
            bad.append('%s: an icon-edit button still carries fa-edit' % name)
        if bad:
            sys.exit('! edit-icon self-check FAILED, nothing written:\n   - %s'
                     % '\n   - '.join(bad))

        left = out.count(OUTLIER)
        plans.append('  %-28s %d icon(s) -> %s%s'
                     % (name, n, HOUSE,
                        ', %d labelled left alone' % left if left else ''))
        if n and not CHECK:
            b = p + SUFFIX
            if not os.path.exists(b):
                shutil.copy2(p, b)
            with open(p, 'w', encoding='utf-8') as f:
                f.write(out)
        if n:
            changed += 1

    # A whole-system check, because the point is that the two files above are
    # now the LAST two, not merely two fewer.
    stray = []
    for f in sorted(os.listdir(TPL)):
        if not f.endswith('.html'):
            continue
        t = read(os.path.join(TPL, f))
        if CHECK and f in FILES:
            t = rewrite(t)[0]
        for m in re.finditer(r'icon-edit[^>]*>\s*<i class="[^"]*?(fa-[a-z0-9-]+)', t):
            if m.group(1) != HOUSE:
                stray.append('%s (%s)' % (f, m.group(1)))
    if stray:
        print('  ! still disagreeing: %s' % ', '.join(sorted(set(stray))))

    for line in plans:
        print(line)
    print('     every icon-only Edit button is a pencil now')
    print('\n  %d file(s) %s' % (changed, 'would change' if CHECK else 'changed'))


if __name__ == '__main__':
    main()
