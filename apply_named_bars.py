# -*- coding: utf-8 -*-
"""apply_named_bars.py - Section E round E3b, 25 Sep 2026.

THE LAST FOUR ACTION BARS ON NAMES OF THEIR OWN.

E3 moved nine Personal page bars onto .page-action-buttons. The count that
had been deferring the rest - test_banner_pages' "at least 25 templates
still use .action-bar" - turned out to be a SUBSTRING count that had been
tallying mobile-action-bar all along. Replacing it with an exact-token
check exposed four more bars, each under a local name.

They are TWO DIFFERENT HOUSE COMPONENTS, not one:

  PAGE BARS -> .page-action-buttons
    preview_imported_recipe.html  .preview-action-bar        6 rules
    view_recipe.html              .recipe-action-bar         9 rules

  MOBILE ROW GRIDS -> .mobile-action-bar
    celebration_management.html   .contact-action-bar-mobile 11 rules
    celebration_management.html   .event-action-bar-mobile    9 rules

.recipe-action-bar is the plainest case in the whole section. It retypes
base's layout declaration for declaration, including

    .recipe-action-bar .action-back { margin-left: auto; }

which is base's own rule carrying base's own reasoning - "Back is
navigation, not an action on the data" - under a different container name.

The two grids already use base's CHILDREN - .mobile-action-btn,
.mobile-action-icon, .mobile-action-label. Only the container is local, and
what it declares is what base declares: repeat(3, 1fr) IS base's default,
and 1fr 1fr IS base's .cols-2. Twenty rules to restate a component the file
is already half-using.

has-primary BECOMES page-action-buttons-single, INVERTED.
preview_imported_recipe carries a Django conditional inside its class
attribute: has-primary when mode == 'edit', because Back shrinks to an icon
when a primary button is present and expands when it is not. base says the
same thing with .page-action-buttons-single, which tenant_lease_agreement
and title_deeds_management already wear - and in both of those the bar
holds ONLY a Back button. So -single is the NO-primary case, and the
conditional flips: {% if mode != 'edit' %}.

WHAT THE SURVEY GOT WRONG, MEASURED AGAIN.
Its contrast numbers were taken against the HOVER tile. At rest, base's
.mobile-action-btn paints var(--alv-surface), and against that, on the 3:1
bar icons are judged by:

    #28a745  add      2.97  FAIL   (the survey said 2.64)
    #ffc107  edit     1.55  FAIL
    #dc3545  delete   4.30  passes (the survey called it a failure)

Two failures, but not the two reported. It also claimed base defines no
.icon-color-* rules; base defines TWELVE, all house tokens. Deleting the
local overrides really does hand the icons back to base.

ONE LINE OF BASE, AND ONLY ONE. base has .icon-color-edit, -view, -delete,
-approve, -upload, -send, -duplicate, -manage, -permissions, -lock and
-unlock. It has no -add, and celebration_management's Add Event icon uses
one. Rather than leave that icon uncoloured, base gains the missing member
of its own family, valued like its sibling .icon-color-approve:

    .icon-color-add { color: var(--alv-good); }

E3 changed no base rule. This round changes exactly that one line, and the
suite asserts it is the only base change.

A VISIBLE CHANGE WORTH NAMING: base's .icon-color-edit is BLUE (#2563eb),
where these two grids painted their edit icon amber. Adopting base changes
that icon's colour. It is the house standard and used across the app, but
it is not invisible.
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
SUFFIX = '.bak_namedbars'
CHECK = '--check' in sys.argv

BARS = ('preview-action-bar', 'recipe-action-bar',
        'contact-action-bar-mobile', 'event-action-bar-mobile')
TOKEN = re.compile(r'(?<![\w-])\.(%s)(?![\w-])' % '|'.join(BARS))

# Where each local name is going, and what it becomes in a class attribute.
TO_CLASS = {
    'recipe-action-bar': 'page-action-buttons',
}

# A CLASS NAME WAS DOING TWO JOBS, AND THE RENAME TOOK ONE AWAY.
# celebration_management's script does
#     card.querySelector('.contact-action-bar-mobile')
# to hide a contact's actions when its card collapses. Both grids live
# inside the same .contact-card - the event grid first - so once both are
# .mobile-action-bar, that query returns the WRONG ONE and the script
# hides the event actions instead. The old name was a styling name AND a
# JS hook; only the styling half is base's to take over.
#
# The hook becomes a data attribute, which is what base itself already
# uses for exactly this - [data-menu], [data-menu-toggle],
# [data-menu-panel]. A name that identifies WHICH group is data, not
# style, and it no longer changes when the styling does.
GRID_MARKUP = [
    ('<div class="contact-action-bar-mobile">',
     '<div class="mobile-action-bar" data-actions="contact">'),
    ('<div class="event-action-bar-mobile">',
     '<div class="mobile-action-bar cols-2" data-actions="event">'),
]
# The script, and the comment that explains it. A patcher that rewrites
# CSS and markup but not <script> leaves a querySelector pointing at a
# name that no longer exists - which is exactly what the first version of
# this round did, and it would have shipped the card collapse broken.
SCRIPT_EDITS = [
    ("card.querySelector('.contact-action-bar-mobile')",
     "card.querySelector('[data-actions=\"contact\"]')"),
    ('and show .contact-action-bar-mobile) takes over again.',
     'and show the contact action grid) takes over again.'),
]
TO_SELECTOR = {
    'preview-action-bar': '.page-action-buttons',
    'recipe-action-bar': '.page-action-buttons',
    'contact-action-bar-mobile': '.mobile-action-bar',
    'event-action-bar-mobile': '.mobile-action-bar',
}

# A RULE THAT SAYS SOMETHING BASE CANNOT KNOW IS KEPT AND RE-SCOPED.
# Exactly one qualifies: a collapsed contact card hides its own action
# grid. That is this page's behaviour, not the component's, and base has
# no opinion about it. Named rather than inferred, and asserted below.
KEEP = {
    '.contact-card.compact-view:not(.expanded) .contact-action-bar-mobile':
        'a collapsed card hides its actions - this page\'s behaviour, '
        'not the grid\'s',
}

# (rules deleted, rules re-scoped, class attributes rewritten)
EXPECTED = {
    'preview_imported_recipe.html': (6, 0, 1),
    'view_recipe.html': (9, 0, 1),
    'celebration_management.html': (19, 1, 2),
}

PREVIEW_OLD = ('class="preview-action-bar'
               "{% if mode == 'edit' %} has-primary{% endif %}\"")
PREVIEW_NEW = ('class="page-action-buttons'
               "{% if mode != 'edit' %} page-action-buttons-single"
               '{% endif %}"')

BASE_ANCHOR = '.icon-color-delete'
BASE_ADD = '.icon-color-add'

CSS_COMMENT = re.compile(r'/\*.*?\*/', re.S)
HTML_COMMENT = re.compile(r'<!--.*?-->', re.S)
STYLE = re.compile(r'<style[^>]*>(.*?)</style>', re.S | re.I)
RULE = re.compile(r'([^{}]+)\{([^{}]*)\}')
CLASSATTR = re.compile(r'class="([^"]*)"')

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


def blanked(text):
    """Comments to spaces, SAME LENGTH - offsets still line up, and a
    name that lives only in prose is never rewritten (lesson 34)."""
    def spaces(m):
        return re.sub(r'[^\n]', ' ', m.group(0))
    return HTML_COMMENT.sub(spaces, CSS_COMMENT.sub(spaces, text))


def patch_css(text):
    """(new_text, dropped, kept)."""
    scan = blanked(text)
    edits, dropped, kept = [], 0, 0
    for blk in STYLE.finditer(scan):
        at = blk.start(1)
        for m in RULE.finditer(blk.group(1)):
            sel = ' '.join(m.group(1).split())
            if not TOKEN.search(sel):
                continue
            a, b = at + m.start(), at + m.end()
            if sel in KEEP:
                new = TOKEN.sub(lambda mm: TO_SELECTOR[mm.group(1)],
                                text[a:b])
                edits.append((a, b, new))
                kept += 1
                continue
            end = b
            while end < len(text) and text[end] in ' \t':
                end += 1
            if end < len(text) and text[end] == '\r':
                end += 1
            if end < len(text) and text[end] == '\n':
                end += 1
            start = a
            while start > 0 and text[start - 1] in ' \t':
                start -= 1
            edits.append((start, end, ''))
            dropped += 1
    for a, b, to in sorted(edits, reverse=True):
        text = text[:a] + to + text[b:]
    return text, dropped, kept


def patch_classes(text, rel):
    """Rewrite the class ATTRIBUTE by exact token - never a regex on the
    file. base's standards block records what a substring count costs."""
    n = 0
    if rel == 'preview_imported_recipe.html':
        hits = text.count(PREVIEW_OLD)
        if hits == 0 and PREVIEW_NEW in text:
            return text, 0
        if hits != 1:
            raise SystemExit('E3b: the preview bar anchor matched %d times '
                             '- it must match exactly once' % hits)
        return text.replace(PREVIEW_OLD, PREVIEW_NEW), 1
    if rel == 'celebration_management.html':
        for old, new in GRID_MARKUP:
            c = text.count(old)
            if c == 0 and new in text:
                continue
            if c != 1:
                raise SystemExit('E3b: grid anchor matched %d times in %s '
                                 '- it must match exactly once' % (c, rel))
            text = text.replace(old, new)
            n += 1
        for old, new in SCRIPT_EDITS:
            c = text.count(old)
            if c == 0 and new in text:
                continue
            if c < 1:
                raise SystemExit('E3b: script anchor %r not found in %s'
                                 % (old[:40], rel))
            text = text.replace(old, new)
        return text, n
    out = []
    for m in CLASSATTR.finditer(blanked(text)):
        names = m.group(1).split()
        if not any(x in names for x in TO_CLASS):
            continue
        new = []
        for x in names:
            new.extend(TO_CLASS[x].split() if x in TO_CLASS else [x])
        seen, uniq = set(), []
        for x in new:
            if x not in seen:
                seen.add(x)
                uniq.append(x)
        out.append((m.start(1), m.end(1), ' '.join(uniq)))
        n += 1
    for a, b, to in sorted(out, reverse=True):
        text = text[:a] + to + text[b:]
    return text, n


def patch(rel):
    path = os.path.join(ROOT, rel)
    text = read(path)
    before = text
    text, dropped, kept = patch_css(text)
    text, renamed = patch_classes(text, rel)
    want = EXPECTED[rel]
    got = (dropped, kept, renamed)
    if got != (0, 0, 0) and got != want:
        raise SystemExit('E3b: %s gave %s, the survey says %s. Re-survey '
                         'before writing anything.' % (rel, got, want))
    if text == before:
        return (0, 0, 0)
    if not CHECK:
        bak = path + SUFFIX
        if not os.path.exists(bak):
            CRLF[bak] = CRLF.get(path)   # a backup is a copy (lesson 46)
            write(bak, before)
        write(path, text)
    return got


def patch_base():
    """The one line. base owns eleven .icon-color-* members and is missing
    the one celebration_management uses."""
    path = os.path.join(ROOT, 'base.html')
    text = read(path)
    before = text
    if BASE_ADD in text:
        return 0
    m = re.search(r'(?m)^([ \t]*)\.icon-color-delete\s*\{[^{}]*\}[ \t]*\r?\n',
                  text)
    if not m:
        raise SystemExit('E3b: could not find %s in base to insert beside'
                         % BASE_ANCHOR)
    pad = m.group(1)
    line = ('%s/* ADDED by E3b, 25 Sep - the family was missing its own\n'
            '%s   -add. celebration_management paints an Add Event icon\n'
            '%s   with it; valued like .icon-color-approve. */\n'
            '%s.icon-color-add { color: var(--alv-good); }\n'
            % (pad, pad, pad, pad))
    text = text[:m.end()] + line + text[m.end():]
    if not CHECK:
        bak = path + SUFFIX
        if not os.path.exists(bak):
            CRLF[bak] = CRLF.get(path)
            write(bak, before)
        write(path, text)
    return 1


LATER = [
    ('test_tap_target.py', "for rel in ('celebration_management.html', 'view_recipe.html',\n            'ingredient_base_units_management.html', 'wcim_extras.html'):\n    if os.path.isfile(path(rel)):\n        ok('min-height: 44px' in read(path(rel))\n           and not os.path.isfile(path(rel) + SUFFIX),\n           '%s (Personal) is untouched until its own round' % rel)", '# LATER - Section E round E3b, 25 Sep. celebration_management HAS HAD ITS\n# ROUND. It no longer declares a minimum of its own: its two action grids\n# were local copies of .mobile-action-bar, and deleting them hands the\n# buttons to base\'s .mobile-action-btn, which gives 56px - LARGER than the\n# 44px and 50px the local rules declared. Rendered at 390px the round\n# leaves no control under 44px at all (see test_named_bars.py section 2).\n# So the page is no longer "untouched", and what it lost made it better.\n# The tap round itself still never touched it - no .bak_tap backup. [E3b]\nDONE_OWN_ROUND = {\'celebration_management.html\':\n                  \'E3b - its grids are base\\\'s now, and base gives 56px\'}\nfor rel in (\'celebration_management.html\', \'view_recipe.html\',\n            \'ingredient_base_units_management.html\', \'wcim_extras.html\'):\n    if os.path.isfile(path(rel)):\n        if rel in DONE_OWN_ROUND:\n            ok(not os.path.isfile(path(rel) + SUFFIX),\n               \'%s had its own round (%s), and the tap round still never \'\n               \'touched it\' % (rel, DONE_OWN_ROUND[rel]))\n            continue\n        ok(\'min-height: 44px\' in read(path(rel))\n           and not os.path.isfile(path(rel) + SUFFIX),\n           \'%s (Personal) is untouched until its own round\' % rel)'),
    ('alv_rounds.py',
     "    '.bak_actionbar',\n]",
     "    '.bak_actionbar',\n    '.bak_namedbars',\n]"),
    ('Push-PendingChanges.ps1',
     "    'test_action_bar.py'",
     "    'test_action_bar.py'\n    'test_named_bars.py'"),
]


def patch_later():
    done = 0
    for name, old, new in LATER:
        path = os.path.join(HERE, name)
        text = read(path)
        if new in text:              # decided by the NEW text alone (47)
            continue
        if text.count(old) != 1:
            raise SystemExit('E3b/LATER: anchor matched %d times in %s'
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
    print('SECTION E, ROUND E3b - THE LAST FOUR NAMED BARS - %s'
          % ('CHECK ONLY' if CHECK else 'APPLYING'))
    print('=' * 70)
    td = tk = tr = files = 0
    for rel in sorted(EXPECTED):
        d, k, r = patch(rel)
        if d or k or r:
            files += 1
            print('  %-34s drop %2d  keep %d  rename %d' % (rel, d, k, r))
        else:
            print('  %-34s already applied' % rel)
        td += d
        tk += k
        tr += r
    b = patch_base()
    later = patch_later()
    print('-' * 70)
    print('  %d rule(s) deleted, %d re-scoped, %d class attribute(s) '
          'rewritten,\n  across %d file(s); %d base line added; %d LATER '
          'edit(s).' % (td, tk, tr, files, b, later))
    print()
    print('  KEPT, with the reason:')
    for sel, why in KEEP.items():
        print('    %s' % sel)
        print('        %s' % why)
    print('=' * 70)


if __name__ == '__main__':
    main()
