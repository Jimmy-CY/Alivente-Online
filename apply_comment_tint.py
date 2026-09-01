#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""The comment wash comes off, and the author gets a name instead of a colour.

DECIDED 30 AUG: colour should not encode WHO wrote a comment. Amber means
"attention" in five other places in this system - `--alv-warn`,
`.alv-pill-attn`, `.alv-age-2`, `.alv-grade-4`, and the flagged stat tile - and
on the Friday Status Report an amber comment sat directly under a red
"257 days open" with nothing to say the amber was about authorship. Author
identity is a CATEGORY, not a verdict. The initials are already printed; a
quiet chip carries them better than a background.

THREE FILES, FOUR EXPRESSIONS OF ONE IDEA, AND THEY DISAGREE.

    comments_report.html   tr.admin-comment / tr.user-comment
                           #e3f2fd / #fff3e0, plus :hover, plus PRINT
                           variants, plus phone-card variants
    comments_report.html   .user-cell.admin-user / .regular-user
                           the author's NAME in #1565c0 / #e65100
    comments_report.html   .comment-item.admin-comment-item / .user-comment-item
                           the same two fills, DIFFERENT left borders
    fsr_details.html and   .detail-row.ss-comment / .regular-comment
    friday_status_report   the same two fills - and they colour the TEXT:
                           date, author and body all set to #ff8c00 or #0e7c8b
                           at weight 600

The last one paints the CONTENT rather than the container, so a comment's words
were orange or teal depending on who typed them. And `.regular-comment` took
its identity colour from #0e7c8b - the system ACCENT, the colour that means
"this is a control" on every other screen.

THE HARDCODED NAME. On two of the three screens the split is not admin-versus-
user at all. It is

    {% if detail.issues_details_user == 'SS' %}ss-comment{% else %}regular-comment{% endif %}

- a person's initials, compared as a string literal, in a template. Anyone else
who becomes an admin gets the "regular" colour; if SS leaves, the rule points
at nobody. comments_report.html uses a real `item.is_admin` flag for the same
idea. Removing the wash removes the literal, which is the part of this round
that is not cosmetic at all.

(The OTHER `== user_initials` comparison in fsr_details.html is a different
thing and stays: it decides whether YOU may edit YOUR comment.)

ONE NEUTRAL TONE, agreed 1 Sep. Every author gets the same quiet `.alv-tag`
chip and the NAME does the distinguishing. Two tones would rebuild the same
two-colour split in miniature, and the split is what is being removed.

THE LEGEND GOES WITH IT. `.color-legend` and its two swatches exist only to
explain the wash. Once there is no wash there is nothing to explain, and a
legend for a colour that is no longer used is worse than no legend.

SECTION 4b, FOUND BY THE PUSH GATE - and it is the SCOPE GUARD variant.

test_sticky_sweep.py section 5 asserts that the sweep changed no MARKUP, by
comparing each page with its .bak_sticky snapshot. That is a good check and a
correct claim. It is also a claim with an expiry date built into it: it holds
only until some later round legitimately edits one of those pages, and this
round edits comments_report.html.

The claim is still provable - just not against the LIVE file. .bak_cmttint is
comments_report.html AS THE STICKY SWEEP LEFT IT, because this round is the
first to touch its markup since. So the comparison moves from

    live vs .bak_sticky          (expires the next time anyone edits the page)

to

    .bak_cmttint vs .bak_sticky  (two snapshots, true for good)

which is strictly better: the sweep's historical claim becomes permanently
checkable instead of decaying. The other five pages keep comparing against the
live file, because nothing has touched them.

WHAT THIS ROUND DOES NOT DO. The Comments Report page itself - its teal
gradient banner, its `.stat-box` figures, its `.report-table`, its red Delete -
is the next round. So is the Issues Analysis modal, and so are the Friday
Status Report's cards and `Notify Now`. This round is the tint, in all three
places at once, so they cannot go on disagreeing about it.

Run from the repo root.  --check plans without writing.
"""
import os
import re
import sys
import shutil

ROOT = os.path.dirname(os.path.abspath(__file__))
T = os.path.join(ROOT, 'pages', 'templates')
CR = os.path.join(T, 'comments_report.html')
FS = os.path.join(T, 'friday_status_report.html')
FD = os.path.join(T, 'fsr_details.html')
BASE = os.path.join(T, 'base.html')
SWEEP = os.path.join(ROOT, 'test_sticky_sweep.py')
CHECK = '--check' in sys.argv
SUFFIX = '.bak_cmttint'

SENTINEL = 'alv-tag comment-author'

NOTE = """/* THE COMMENT WASH IS GONE - 1 Sep.

   tr.admin-comment painted the row #e3f2fd and tr.user-comment painted it
   #fff3e0, each with a hover, a print and a phone-card variant; the author's
   NAME was coloured to match by .user-cell.admin-user / .regular-user; the
   history cards repeated the pair as .admin-comment-item /
   .user-comment-item; and .color-legend explained the arrangement. Amber means
   "attention" in five other places in this system; author identity is a
   CATEGORY, not a verdict, and it is now a quiet .alv-tag chip carrying the
   initials that were being printed anyway.

   ONE tone for every author. Two would rebuild the same split in miniature. */"""


def read(p):
    with open(p, encoding='utf-8') as f:
        return f.read().replace('\r\n', '\n')


def one(text, old, new, what):
    n = text.count(old)
    if n != 1:
        sys.exit('! %s did not match exactly once (%d) - the file may already '
                 'have been edited:\n%s' % (what, n, old[:240]))
    return text.replace(old, new, 1)


def between(text, start, end, new, what):
    """start..end INCLUSIVE. `start` must be unique; `end` is the first at or
    after it, because a closing brace repeats everywhere."""
    if text.count(start) != 1:
        sys.exit('! %s: the start marker appears %d times, expected 1:\n%s'
                 % (what, text.count(start), start[:200]))
    i = text.index(start)
    j = text.find(end, i)
    if j < 0:
        sys.exit('! %s: the end marker never appears after the start:\n%s'
                 % (what, end[:200]))
    return text[:i] + new + text[j + len(end):]


def nocomment_html(text):
    text = re.sub(r'<!--.*?-->', '', text, flags=re.S)
    text = re.sub(r'\{#[^\n]*?#\}', '', text)   # NOT re.S - Django has no DOTALL

    def strip(m):
        body = re.sub(r'/\*.*?\*/', '', m.group(2), flags=re.S)
        if m.group(1).startswith('<script'):
            body = '\n'.join('' if l.lstrip().startswith('//') else l
                             for l in body.split('\n'))
        return m.group(1) + body + m.group(3)

    return re.sub(r'(<(?:script|style)[^>]*>)(.*?)(</(?:script|style)>)',
                  strip, text, flags=re.S)


def css_of(text):
    return re.sub(r'/\*.*?\*/', '',
                  '\n'.join(re.findall(r'<style[^>]*>(.*?)</style>', text,
                                       re.S)), flags=re.S)


CHIP = '<span class="alv-tag comment-author">'

# ---------------------------------------------------------------------------
# comments_report.html - four of the six expressions live here
# ---------------------------------------------------------------------------
CR_CUTS = [
    ('CR: the row wash and its hover',
     '/* Comment highlighting based on user type */',
     '.report-table tbody tr.user-comment:hover {\n'
     '    background-color: #ffe0b2;\n}',
     NOTE),
    ("CR: the author's name stops being a colour",
     '.user-cell.admin-user {',
     '.user-cell.regular-user {\n    color: #e65100;\n}\n\n', ''),
    ('CR: the history cards lose theirs too',
     '.comment-item.admin-comment-item {',
     '.comment-item.user-comment-item {\n'
     '    background-color: #fff3e0;\n    border-left-color: #e65100;\n}\n\n',
     ''),
    ('CR: and the legend that explained it',
     '/* Legend */',
     '.legend-color.user {\n    background-color: #fff3e0;\n'
     '    border: 1px solid #ffcc80;\n}\n\n', ''),
    ('CR: the print variants',
     '    .report-table tbody tr.admin-comment {\n'
     '        background-color: #e3f2fd !important;',
     '    .report-table tbody tr.user-comment {\n'
     '        background-color: #fff3e0 !important;\n'
     '        -webkit-print-color-adjust: exact;\n'
     '        print-color-adjust: exact;\n    }\n\n', ''),
    ('CR: the phone-card variants',
     '    .report-table tbody tr.admin-comment {\n'
     '        background-color: #e3f2fd;\n        border-left-color: #1565c0;',
     '    .report-table tbody tr.user-comment {\n'
     '        background-color: #fff3e0;\n'
     '        border-left-color: #e65100;\n    }\n\n', ''),
    ('CR: the legend markup',
     '    <!-- Color Legend -->',
     '    </div>\n\n    <div class="table-container">',
     '    <div class="table-container">'),
    ('CR: the row stops carrying an author class',
     '                <tr class="{% if item.is_admin %}admin-comment{% else %}'
     'user-comment{% endif %}">',
     '>',
     '                <tr>'),
    ('CR: the author becomes a chip',
     '                    <td class="user-cell {% if item.is_admin %}'
     'admin-user{% else %}regular-user{% endif %}">',
     '</td>',
     '                    <td class="user-cell">\n'
     '                        ' + CHIP + '{{ item.user }}</span>\n'
     '                    </td>'),
    ('CR: and so does the author in the history modal',
     '            const commentClass = ',
     '<span class="comment-user">${comment.user}</span>',
     '''            commentsHtml += `
                <div class="comment-item">
                    <div class="comment-meta">
                        ''' + CHIP + '${comment.user}</span>'),
]

CR_MOBILE_LEGEND = [
    ('CR: the legend rule the phone block kept',
     '    /* Legend wraps */\n    .color-legend {',
     '        padding: 0 4px;\n    }\n', ''),
]

CR_ONE = [
    ('CR: the print block stops hiding a legend that is gone',
     '.page-action-buttons, .color-legend, .btn-delete-icon, .modal {',
     '.page-action-buttons, .btn-delete-icon, .modal {'),
]

# ---------------------------------------------------------------------------
# the two screens that compared a username to the string 'SS'
# ---------------------------------------------------------------------------
# The two files spell it differently - one indents four spaces inside a block
# and carries no section comment, the other sits at column zero with two. And
# both repeat the pair inside a media block. So this is matched as a RULE
# GROUP rather than as literal text: every .detail-row.ss-comment /
# .regular-comment rule goes, wherever it is and however it is indented, and
# the first one is replaced by the note.
SS_RULE = re.compile(
    r'([ \t]*)(?:/\*[^*]*(?:SS User|Regular User)[^*]*\*/[ \t]*\n)?'
    r'[ \t]*\.detail-row\.(?:ss|regular)-comment[^{]*\{[^}]*\}\n')

SS_NOTE = """/* THE COMMENT WASH IS GONE - 1 Sep.

   .ss-comment and .regular-comment painted the row AND the text - date,
   author and body all set to #ff8c00 or #0e7c8b at weight 600 - so a
   comment's words were coloured by who typed them. #0e7c8b is the system
   accent, which means "this is a control" everywhere else.

   And the class was chosen by comparing a username to the literal 'SS'. A
   person's initials, in a template. The author is a quiet .alv-tag chip now,
   and there is no name to keep up to date. */"""


def strip_ss(txt, what):
    """Every rule in the group goes; the first is replaced by the note."""
    hits = SS_RULE.findall(txt)
    if len(hits) < 4:
        sys.exit('! %s: found %d .detail-row rule(s), expected at least the '
                 'four that make the pair' % (what, len(hits)))
    state = {'n': 0}

    def sub(m):
        state['n'] += 1
        if state['n'] != 1:
            return ''
        pad = m.group(1)
        return '\n'.join(pad + l if l else l
                          for l in SS_NOTE.split('\n')) + '\n'

    return SS_RULE.sub(sub, txt), len(hits)


def ss_markup(var):
    return ('<div class="detail-row {%% if %s.issues_details_user == \'SS\' %%}'
            'ss-comment{%% else %%}regular-comment{%% endif %%}"' % var)


def ss_author(var):
    # The trailing colon goes with it. It separated an author from the comment
    # text when the author was "(SS)"; a chip does not need punctuation after
    # it to say it has ended.
    return ('<span class="comment-user">({{ %s.issues_details_user }})</span>:'
            % var)


def ss_author_new(var):
    return (CHIP + '{{ %s.issues_details_user }}</span>' % var)


# ---------------------------------------------------------------------------
# section 4b - the sticky sweep's scope guard moves to two snapshots
# ---------------------------------------------------------------------------
S_OLD = """    for rel in PAGES:
        path = os.path.join(TPL, *rel.split('/'))
        src, bak = read(path), read(path + SUFFIX)

        def markup(t):
            t = re.sub(r'<style[^>]*>.*?</style>', '', t, flags=re.S)
            return re.sub(r'<!--.*?-->', '', t, flags=re.S)
        check('%-30s markup is byte-for-byte unchanged' % rel,
              markup(src) == markup(bak))"""

S_NEW = """    # SUPERSEDED 1 Sep by the comment-tint round, and MOVED - this is the
    # SCOPE GUARD kind. The claim is that the sticky sweep changed no MARKUP,
    # and it was measured live-vs-.bak_sticky. Correct, and with an expiry
    # date built in: it holds only until a later round legitimately edits one
    # of these pages. The comment-tint round edits comments_report.html.
    #
    # The claim is still provable, just not against the LIVE file.
    # .bak_cmttint is the page AS THE SWEEP LEFT IT, because that round was
    # the first to touch its markup afterwards. So for a page a later round
    # owns, the comparison is between the TWO SNAPSHOTS - which is true for
    # good, rather than decaying the next time anyone edits anything.
    LATER = {'comments_report.html': '.bak_cmttint'}
    for rel in PAGES:
        path = os.path.join(TPL, *rel.split('/'))
        _later = LATER.get(rel)
        _as_left = (path + _later) if _later else path
        if _later and not os.path.exists(_as_left):
            check('%-30s a later round left a snapshot to measure' % rel,
                  False, _later)
            continue
        src, bak = read(_as_left), read(path + SUFFIX)

        def markup(t):
            t = re.sub(r'<style[^>]*>.*?</style>', '', t, flags=re.S)
            return re.sub(r'<!--.*?-->', '', t, flags=re.S)
        check('%-30s markup is byte-for-byte unchanged%s'
              % (rel, ' (%s vs %s - a later round owns the live file)'
                 % (_later, SUFFIX) if _later else ''),
              markup(src) == markup(bak))"""


def read_all():
    return read(CR), read(FS), read(FD), read(BASE)


def main():
    for p in (CR, FS, FD, BASE, SWEEP):
        if not os.path.exists(p):
            sys.exit('! %s not found - run from the repo root' % p)
    cr, fs, fd, bs = read_all()
    sw = read(SWEEP)
    cr0, fs0, fd0, sw0 = cr, fs, fd, sw

    # PER-FILE GUARDS. The push gate found the 4b edit after the templates
    # were already patched; one guard for the whole round would leave the
    # patcher unable to finish itself.
    tint_done = SENTINEL in cr
    sweep_done = S_OLD not in sw
    if tint_done and sweep_done:
        print('  the comment tint                 already applied')
        print('\n  0 file(s) changed')
        return

    names = []
    if sweep_done:
        print('  test_sticky_sweep.py             already moved')
    else:
        sw = one(sw, S_OLD, S_NEW, "4b: the sweep's scope guard moves")
        names.append("4b: the sticky sweep's scope guard moves to two "
                     "snapshots")
    if tint_done:
        print('  the templates                    already applied')
    if not tint_done:
      for what, start, end, new in CR_CUTS:
        cr = between(cr, start, end, new, what)
        names.append(what)
      for what, start, end, new in CR_MOBILE_LEGEND:
        if start in cr:
            cr = between(cr, start, end, new, what)
            names.append(what)
      for what, old, new in CR_ONE:
        cr = one(cr, old, new, what)
        names.append(what)

      for label, src, var in (('FSR', 'fs', 'detail'),
                            ('issue comments', 'fd', 'idresults')):
        txt = fs if src == 'fs' else fd
        txt, _hits = strip_ss(txt, label)
        txt = one(txt, ss_markup(var), '<div class="detail-row"',
                  '%s: the row stops asking who SS is' % label)
        txt = one(txt, ss_author(var), ss_author_new(var),
                  '%s: the author becomes a chip' % label)
        if src == 'fs':
            fs = txt
        else:
            fd = txt
        names += ['%s: %d wash rules out, and the text they coloured'
                  % (label, _hits),
                  "%s: the row stops asking who 'SS' is" % label,
                  '%s: the author becomes a chip' % label]

    # -----------------------------------------------------------------------
    # SELF-CHECK. Nothing is written unless every one of these holds.
    # -----------------------------------------------------------------------
    bad = []
    bc = nocomment_html(bs)
    files = (('comments_report.html', cr, cr0),
             ('friday_status_report.html', fs, fs0),
             ('fsr_details.html', fd, fd0))

    for name, raw, before in files:
        c = nocomment_html(raw)
        _fresh = not tint_done
        for _dead in ('admin-comment', 'user-comment', 'admin-comment-item',
                      'user-comment-item', 'admin-user', 'regular-user',
                      'ss-comment', 'regular-comment', 'color-legend',
                      'legend-color'):
            if re.search(r'(?<![\w-])%s(?![\w-])' % _dead, c):
                bad.append('%s: %s survives' % (name, _dead))
        for _lit in ('#fff3e0', '#ffe0b2', '#e65100', '#1565c0', '#ff8c00',
                     '#bbdefb', '#90caf9', '#ffcc80'):
            if _lit in c:
                bad.append('%s: the wash literal %s survives' % (name, _lit))
        if SENTINEL not in c:
            bad.append('%s: the author has no chip' % name)
        # ONE tone. A second would rebuild the split.
        if re.search(r'alv-tag comment-author[^"]*alv-tag-', c):
            bad.append('%s: the chip carries a tone - one tone was the '
                       'decision' % name)
        if re.search(r'\.comment-author\s*\{[^}]*background', c):
            bad.append('%s: the chip paints a background of its own' % name)
        # THE HARDCODED NAME.
        if "issues_details_user == 'SS'" in c:
            bad.append("%s: a username is still compared to the literal 'SS'"
                       % name)
        # ... but the one that decides who may EDIT stays.
        if name == 'fsr_details.html' and 'user_initials' not in c:
            bad.append('fsr_details.html: the edit-permission comparison was '
                       'removed - that one is not the wash')
        # The round must SHRINK these files - but only on the run that
        # actually edits them.
        if _fresh and len(raw) >= len(before):
            bad.append('%s did not get smaller (%d -> %d)'
                       % (name, len(before), len(raw)))
        # Structure.
        _css = css_of(raw)
        if _css.count('{') != _css.count('}'):
            bad.append('%s: CSS braces do not balance' % name)
        for o, cl in ((r'\{%\s*if\b', r'\{%\s*endif\s*%\}'),
                      (r'\{%\s*for\b', r'\{%\s*endfor\s*%\}')):
            if len(re.findall(o, raw)) != len(re.findall(cl, raw)):
                bad.append('%s: a Django block no longer balances' % name)
        for _l in raw.split('\n'):
            if _l.count('{#') != _l.count('#}'):
                bad.append('%s: a {# #} comment spans lines' % name)
                break
        for tag in ('div', 'span', 'tr', 'td'):
            if not _fresh:
                break
            _o = (len(re.findall(r'<%s\b' % tag, c))
                  - len(re.findall(r'</%s\s*>' % tag, c)))
            _b = (len(re.findall(r'<%s\b' % tag, nocomment_html(before)))
                  - len(re.findall(r'</%s\s*>' % tag, nocomment_html(before))))
            if _o != _b:
                bad.append('%s: <%s> balance changed by %d' % (name, tag,
                                                               _o - _b))

    # base must own the chip.
    if '.alv-tag' not in bc:
        bad.append('base does not define .alv-tag')
    if re.search(r'\.alv-tag\s*\{[^}]*var\(--alv-(good|warn|bad)', bc):
        bad.append('the tag borrows a verdict token, which is the collision '
                   'this round exists to remove')

    # -- 4b: the sweep still parses, and still says at least as much -------
    try:
        compile(sw, 'test_sticky_sweep.py', 'exec')
    except SyntaxError as exc:
        bad.append('the patched sticky suite does not parse: %s' % exc)
    if sw.count('check(') < sw0.count('check('):
        bad.append('the sticky suite lost checks - an expectation was DELETED')
    if "'comments_report.html': '.bak_cmttint'" not in sw:
        bad.append('the sweep does not know a later round owns that page')
    if SUFFIX not in sw:
        bad.append('the sweep names a snapshot this round does not write')

    # -- CONTROL on the stripper -------------------------------------------
    # Each note names the classes it replaced, so an unstripped check would
    # find them in the explanation of why they are gone.
    if 'admin-comment' not in cr or 'ss-comment' not in fs:
        bad.append('CONTROL: a round lost the prose it strips against')
    if 'admin-comment' in nocomment_html(cr):
        bad.append('CONTROL: comments are not being stripped')

    if bad:
        sys.exit('! comment-tint self-check FAILED, nothing written:\n   - %s'
                 % '\n   - '.join(bad))

    for n in names:
        print('  %s' % n)
    for name, raw, before in files:
        print('  %-28s %d -> %d bytes' % (name, len(before), len(raw)))

    if not CHECK:
        for path, out, before, suf in ((CR, cr, cr0, SUFFIX),
                                       (FS, fs, fs0, SUFFIX),
                                       (FD, fd, fd0, SUFFIX),
                                       (SWEEP, sw, sw0, '.bak_cmttint4b')):
            if out == before:
                continue
            b = path + suf
            if not os.path.exists(b):
                shutil.copy2(path, b)
            with open(path, 'w', encoding='utf-8') as f:
                f.write(out)

    _n = (0 if tint_done else 3) + (0 if sweep_done else 1)
    print('\n  %d file(s) %s' % (_n, 'would change' if CHECK else 'changed'))


if __name__ == '__main__':
    main()
