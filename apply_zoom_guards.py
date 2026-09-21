# -*- coding: utf-8 -*-
"""apply_zoom_guards.py - the page-local iOS zoom guards base made redundant.

    python apply_zoom_guards.py --check
    python apply_zoom_guards.py
    python test_zoom_guards.py
    python Push-PendingChanges.ps1

    Show-ZoomGuards.py is the read-only survey this round was sized from.

WHAT BASE SAID, AND WHAT WAS TRUE

  base's own comment, written by push 1:

      "62 pages had each written this rule locally before base did. Those
       locals are now redundant; removing them is a round of its own."

  Measured against the live tree it is 72 guard rules on 60 pages, and a
  third of them are NOT redundant. base guards ONE selector - .form-control -
  at ONE width - screen and (max-width: 768px). A page-local guard is
  redundant only where it reaches nothing base does not.

    REDUNDANT   35 rules / 34 pages   base covers them exactly. They go.
    MIXED       17 rules / 16 pages   the 16px is redundant, but the same
                                      rule sets padding (16) or width (1).
                                      Only the font-size declaration goes.
    ORPHANS     18 rules / 13 pages   they guard 82 controls with NO
                                      .form-control class - 45 text, 26
                                      number, 11 select, mostly the recipe
                                      screens. base never reaches them, so
                                      their guard is the only thing stopping
                                      the zoom. UNTOUCHED, by decision.
    EVERY-WIDTH  2 rules /  1 page    projects.html sets 16px on the desktop
                                      too, which base does not. UNTOUCHED.

  AND ONE THE COUNT COULD NOT SEE. fsr.html's guard is !important and base's
  is not. The page also sets .filter-select and .search-input to 14px at
  every width, and those controls carry .form-control too - equal
  specificity, and the page's stylesheet comes after base's. RENDERED at
  375px: today they are 16px; remove the guard and they drop to 14px, and
  iOS zooms on the Issues filter. So the rule this patcher follows is not a
  list with fsr on it: A PAGE THAT SETS ANY CONTROL BELOW 16PX ANYWHERE KEEPS
  EVERY GUARD IT HAS. fsr is the only page that rule currently catches.

WHY THE ORPHANS STAY

  Giving those 82 controls .form-control is the right end state - it joins
  them to the field component and makes their guards genuinely redundant.
  But it changes how they look: border, padding, radius, on 13 pages. That
  is a visible change, and it belongs with fsr_details' .ei-* dialect in a
  form-components round where the visual change is the point, rather than
  bundled into a clean-up that should change nothing anyone can see.

THE INVARIANT

  A redundant rule is, by definition, one whose removal changes nothing.
  test_zoom_guards.py renders every page this round touches, at 375 and at
  1280, before and after, and requires EVERY control's computed font-size
  and padding to be identical. That is not a proxy for redundant; it is what
  redundant means.

ALSO

  * base declares its own guard TWICE - the form-components round wrote it,
    and push 1 wrote it again without noticing. Push 1's copy goes; its
    comment, which carried the optimistic 62, is rewritten to say what was
    measured.
  * A guard in a media block with nothing else in it empties that block, and
    an empty block goes. Where that page is one test_print_leaks.py watches,
    its LATER map needs an entry, and this round adds it - the same thing
    stage E did, for the same reason.
  * Line endings are preserved per file.
"""
import ast
import os
import re
import sys

CHECK = '--check' in sys.argv
ROOT = os.path.join(os.getcwd(), 'pages', 'templates')
if not os.path.isdir(ROOT):
    sys.exit('! pages/templates not found - run from the repo root')

SUFFIX = '.bak_zoomguard'
SUITE = 'test_zoom_guards.py'
PS1 = 'Push-PendingChanges.ps1'
LEAK_SUITE = 'test_print_leaks.py'

OUT_OF_SCOPE = {
    'create_recipe (OLD DO NOT USE).html': 'no view renders it',
    'edit_recipe (OLD DO NOT USE).html': 'no view renders it',
    'error_pages/connectivity_error.html':
        'does not extend base, so base\'s guard never reaches it',
}

report, problems = [], []
planned = {}        # path -> (src, text)
CRLF = {}


def read(p):
    """Text as LF - and remember what the file used, so it is written back
    the same way. Earlier rounds converted six files to LF and put every
    line of them in the commit."""
    with open(p, encoding='utf-8', newline='') as f:
        raw = f.read()
    CRLF[p] = '\r\n' in raw
    return raw.replace('\r\n', '\n')


def write(p, text):
    if CRLF.get(p):
        text = text.replace('\n', '\r\n')
    with open(p, 'w', encoding='utf-8', newline='') as f:
        f.write(text)


COMMENT = re.compile(r'/\*.*?\*/', re.S)


def declarations(body):
    out = {}
    for part in COMMENT.sub('', body).split(';'):
        if ':' in part:
            k, v = part.split(':', 1)
            out[k.strip().lower()] = ' '.join(v.split())
    return out


# ==========================================================================
# THE CLASSIFICATION - the same one Show-ZoomGuards.py reports.
#
# It is a SECOND COPY of that logic, and this project has paid for copies
# before. It is tolerable here for one reason: the suite does not re-run
# this classification to check the result. It RENDERS every touched page
# and requires nothing computed to change. If this copy and the survey
# drift apart, the render catches it, because a wrongly-classified guard is
# exactly one whose removal changes something.
# ==========================================================================
CONTROL = re.compile(r'<(input|select|textarea)\b([^>]*)>', re.I)
SKIP_TYPES = {'submit', 'button', 'reset', 'hidden', 'checkbox', 'radio',
              'file', 'image', 'range', 'color'}
GUARD_SUBJECT = re.compile(r'form-control|(?<![-\w])(input|select|textarea)'
                           r'(?![-\w])|filter-select|search-input')


def controls(text):
    """Text-entry controls, from markup AND script strings - a guard can
    exist for a control a script builds."""
    out = []
    for m in CONTROL.finditer(text):
        tag, attrs = m.group(1).lower(), m.group(2)
        ty = 'text'
        t = re.search(r'type\s*=\s*["\']?([a-zA-Z-]+)', attrs)
        if tag == 'input' and t:
            ty = t.group(1).lower()
        if tag == 'input' and ty in SKIP_TYPES:
            continue
        cls = re.search(r'class\s*=\s*["\']([^"\']*)', attrs)
        out.append({'tag': tag, 'type': ty if tag == 'input' else tag,
                    'classes': set((cls.group(1) if cls else '').split())})
    return out


def subject(selector):
    last = re.split(r'\s+|>|\+|~', selector.strip())[-1]
    last = re.sub(r':[\w-]+(\([^)]*\))?', '', last)
    tag = re.match(r'^([a-zA-Z]+)', last)
    ty = re.search(r'\[type\s*=\s*["\']?([a-zA-Z-]+)', last)
    return (tag.group(1).lower() if tag else None,
            set(re.findall(r'\.([\w-]+)', last)),
            ty.group(1).lower() if ty else None)


def matches(ctl, subj):
    tag, classes, ty = subj
    if tag and tag != ctl['tag']:
        return False
    if classes and not classes <= ctl['classes']:
        return False
    if ty and ty != ctl['type']:
        return False
    return bool(tag or classes or ty)


def is_guard(sels, decl):
    return (decl.get('font-size', '').startswith('16px')
            and any(GUARD_SUBJECT.search(s) for s in sels))


def verdict(media, sels, decl, ctls):
    if not media:
        return 'EVERY-WIDTH'
    if '768' not in media:
        return 'OTHER-WIDTH'
    for s in sels:
        subj = subject(s)
        if any(matches(c, subj) and 'form-control' not in c['classes']
               for c in ctls):
            return 'ORPHANS'
    if [k for k in decl if k != 'font-size']:
        return 'MIXED'
    return 'REDUNDANT'


def shrinks_a_control(css_clean, ctls):
    """Does anything on this page set a text control's font-size below 16px?

    If so, the page keeps every guard it has - base's plain 16px can lose to
    that smaller number once a local guard is gone. fsr proved it by
    rendering.

    WHAT A SELECTOR MATCHES, NOT WHAT IT SAYS. The first version looked for
    selector TEXT naming a control - input, select, .form-control - and so
    missed `.line-input { font-size: 14px }` on customer_invoice_form and
    physical_invoice_edit. `.line-input` names no control, and every
    element it matches is one. The guard removed there was load-bearing,
    and the rendered suite caught it: those inputs went 16px -> 14px at 375.
    Each rule is now matched against the page's actual controls."""
    for m in re.finditer(r'([^{}@]+)\{([^{}]*)\}', css_clean):
        fs = dict(x.split(':', 1) for x in
                  (y.strip() for y in COMMENT.sub('', m.group(2)).split(';'))
                  if ':' in x)
        fs = {k.strip().lower(): v.strip() for k, v in fs.items()}
        v = re.match(r'([\d.]+)(px|rem|em)', fs.get('font-size', ''))
        if not v:
            continue
        px = float(v.group(1)) * (16 if v.group(2) in ('rem', 'em') else 1)
        if px >= 16:
            continue
        sels = [x.strip() for x in m.group(1).split(',') if x.strip()]
        hit = [x for x in sels
               if any(matches(c, subject(x)) for c in ctls)]
        if hit:
            return '%s -> %s' % (', '.join(hit)[:50], fs['font-size'])
    return None


# ==========================================================================
# THE EDITOR - works on the RAW text, comments and all, and only rewrites
# what it removes. A kept rule is emitted exactly as found.
# ==========================================================================
FONT_DECL = re.compile(
    r'[ \t]*font-size\s*:\s*16px\s*(?:!important\s*)?;[ \t]*'
    r'(?:/\*[^*]*(?:\*(?!/)[^*]*)*\*/[ \t]*)?\n?')


def mask(css):
    """The same text with every comment blanked to spaces, OFFSETS KEPT.

    Structure is searched for in the mask and output is sliced from the
    raw text. That is the only way to be sure a `@media` or a brace written
    inside a comment is never read as one - which this project has now got
    wrong seven times, the last time in this round's own survey tool."""
    return COMMENT.sub(lambda m: re.sub(r'[^\n]', ' ', m.group(0)), css)


def split_attached(pre):
    """(kept, attached) - the comment written DIRECTLY above a rule, with no
    blank line between, is taken to annotate that rule and goes with it. A
    comment separated by a blank line is a section heading for what follows
    and stays, because the rules after it are still there."""
    body = pre.rstrip(' \t')
    if not body.rstrip().endswith('*/'):
        return pre, ''
    k = body.rfind('/*')
    tail = pre[body.rstrip().__len__():]
    # between the comment's end and the selector: one newline at most
    if tail.count('\n') > 1:
        return pre, ''
    before = pre[:k]
    # the comment must start its own line
    line_start = before.rfind('\n') + 1
    if before[line_start:].strip():
        return pre, ''
    return pre[:line_start], pre[line_start:]


TRAILING = re.compile(r'[ \t]*/\*[^\n]*?\*/[ \t]*(?=\n|$)')


def edit(css, decide):
    """decide(media, sels, decl) -> 'drop' | 'strip' | None.

    Returns (css, dropped, stripped). THE PATCHER REMOVES; IT DOES NOT
    REFORMAT. A kept rule is emitted byte for byte. The first draft of this
    function collapsed every run of blank lines in every file it touched,
    and changed files it removed nothing from - the same fault as the CRLF
    conversion, one layer up. Whitespace now moves only where a rule went.

    What goes with a dropped rule, and nothing else:
      * a comment written directly above it with no blank line between -
        it annotated that rule. A comment after a blank line is a section
        heading for what follows, and what follows is still there.
      * a comment on the same line AFTER its closing brace -
        `.x { font-size: 16px; } /* prevent iOS zoom */` - which the first
        draft stranded on a line of its own.
      * the media block around it, if the rule was the last thing in it.
        ONLY if this round emptied it: fsr_details already carries an empty
        `@media print { }`, and the first draft removed that too."""
    dropped, stripped = [], []
    AT = re.compile(r'@media([^{]*)\{')
    RULE = re.compile(r'([^{}@]+)\{([^{}]*)\}')

    def walk(raw, msk, media):
        out, i, n = [], 0, len(raw)
        while i < n:
            at = AT.search(msk, i)
            rule = RULE.search(msk, i)
            if at and (not rule or at.start() < rule.start()):
                depth, j = 1, at.end()
                while j < n and depth:
                    depth += 1 if msk[j] == '{' else (
                        -1 if msk[j] == '}' else 0)
                    j += 1
                cond = ' '.join(at.group(1).split())
                inner_raw = raw[at.end():j - 1]
                inner = walk(inner_raw, msk[at.end():j - 1], cond)
                lead = raw[i:at.start()]
                had = '{' in mask(inner_raw)
                has = '{' in mask(inner)
                if had and not has:
                    kept, _attached = split_attached(lead)
                    out.append(kept.rstrip())
                    m = TRAILING.match(raw, j)
                    i = m.end() if m else j
                else:
                    out.append(lead + raw[at.start():at.end()] + inner + '}')
                    i = j
                continue
            if not rule:
                out.append(raw[i:])
                break
            sels = [' '.join(x.split()) for x in rule.group(1).split(',')
                    if x.strip()]
            body_raw = raw[rule.start(2):rule.end(2)]
            decl = declarations(body_raw)
            what = decide(media, sels, decl) if sels else None
            gap = raw[i:rule.start()]
            sel_raw = raw[rule.start(1):rule.end(1)]
            if what == 'drop':
                # the selector starts at the first non-space in the MASK
                sel_start = len(sel_raw) - len(mask(sel_raw).lstrip())
                kept, _attached = split_attached(sel_raw[:sel_start])
                out.append(gap + kept.rstrip())
                dropped.append((media, sels))
                m = TRAILING.match(raw, rule.end())
                i = m.end() if m else rule.end()
                continue
            if what == 'strip':
                out.append(gap + sel_raw + '{'
                           + FONT_DECL.sub('', body_raw, count=1) + '}')
                stripped.append((media, sels))
            else:
                out.append(raw[i:rule.end()])
            i = rule.end()
        return ''.join(out)

    return walk(css, mask(css), ''), dropped, stripped


def queries(css):
    return sorted(' '.join(COMMENT.sub('', m.group(1)).split())
                  for m in re.finditer(r'@media([^{]*)\{',
                                       COMMENT.sub('', css)))


# ==========================================================================
# 1. THE PAGES
# ==========================================================================
kept_whole = {}         # rel -> why every guard on it stayed
tally = {'drop': 0, 'strip': 0, 'orphan': 0, 'every': 0}
lost_queries = {}       # rel -> [queries that disappeared]

for dp, _d, ns in os.walk(ROOT):
    for n in sorted(ns):
        if not n.endswith('.html'):
            continue
        path = os.path.join(dp, n)
        rel = os.path.relpath(path, ROOT).replace(os.sep, '/')
        if rel == 'base.html' or rel in OUT_OF_SCOPE:
            continue
        src = read(path)
        styles = list(re.finditer(r'(<style[^>]*>)(.*?)(</style>)', src, re.S))
        if not styles:
            continue
        clean_all = COMMENT.sub('', '\n'.join(m.group(2) for m in styles))
        if not re.search(r'font-size\s*:\s*16px', clean_all):
            continue
        ctls = controls(src)
        why = shrinks_a_control(clean_all, ctls)

        def decide(media, sels, decl):
            if not is_guard(sels, decl):
                return None
            v = verdict(media, sels, decl, ctls)
            if v == 'ORPHANS':
                tally['orphan'] += 1
                return None
            if v in ('EVERY-WIDTH', 'OTHER-WIDTH'):
                tally['every'] += 1
                return None
            if why:
                return None
            return 'drop' if v == 'REDUNDANT' else 'strip'

        text, cursor, d_all, s_all = '', 0, [], []
        for m in styles:
            new_css, d, s = edit(m.group(2), decide)
            text += src[cursor:m.start(2)] + new_css
            cursor = m.end(2)
            d_all += d
            s_all += s
        text += src[cursor:]

        if why and (re.search(r'font-size\s*:\s*16px', clean_all)):
            kept_whole[rel] = why
        if text == src:
            continue
        tally['drop'] += len(d_all)
        tally['strip'] += len(s_all)
        was = queries('\n'.join(m.group(2) for m in styles))
        now = queries('\n'.join(m.group(1) for m in re.finditer(
            r'<style[^>]*>(.*?)</style>', text, re.S)))
        gone = [q for q in set(was) if was.count(q) > now.count(q)]
        if gone:
            lost_queries[rel] = sorted(gone)
        planned[path] = (src, text)
        report.append('%-42s -%d rule(s), %d font-size line(s)%s'
                      % (rel, len(d_all), len(s_all),
                         ('; %d empty media block(s) went' % len(gone))
                         if gone else ''))


# ==========================================================================
# 2. base - one guard, not two
# ==========================================================================
BASE = os.path.join(ROOT, 'base.html')
B_OLD = """   FONT-SIZE. iOS Safari zooms the page whenever a focused input is under
   16px, and .form-control is 14px. 62 pages had each written this rule
   locally before base did. Those locals are now redundant; removing them is
   a round of its own. */
@media screen and (max-width: 768px) {
    .form-card    { padding: 16px 14px; }
    .form-control { font-size: 16px; }
    .form-section-title small { display: block; font-size: 0.75rem; }
}"""
B_NEW = """   FONT-SIZE is not here, and that is deliberate. The iOS zoom guard -
   .form-control at 16px below 768px - lives ONCE, in the form-components
   rule further down. This block used to declare it a second time, written
   without noticing the first; the zoom-guard round removed the copy.

   It also said "62 pages had each written this rule locally" and that
   those were redundant. Measured, it was 72 rules on 60 pages, and a third
   of them were not: they guard controls with no .form-control class, which
   this rule never reaches. See Show-ZoomGuards.py. */
@media screen and (max-width: 768px) {
    .form-card    { padding: 16px 14px; }
    .form-section-title small { display: block; font-size: 0.75rem; }
}"""
KEEP_ANCHOR = """@media screen and (max-width: 768px) {
    .form-control { font-size: 16px; }
}"""

if not os.path.isfile(BASE):
    problems.append('base.html: not found')
else:
    bsrc = read(BASE)
    if B_NEW in bsrc:
        report.append('%-42s already declares the guard once' % 'base.html')
    elif bsrc.count(B_OLD) != 1:
        problems.append('base.html: push 1\'s phone block appears %d time(s), '
                        'expected 1' % bsrc.count(B_OLD))
    elif bsrc.count(KEEP_ANCHOR) != 1:
        problems.append('base.html: the form-components guard appears %d '
                        'time(s), expected 1 - removing the copy would leave '
                        'none' % bsrc.count(KEEP_ANCHOR))
    else:
        planned[BASE] = (bsrc, bsrc.replace(B_OLD, B_NEW, 1))
        report.append('%-42s the guard declared once, not twice' % 'base.html')


# ==========================================================================
# 3. test_print_leaks.py - a LATER entry for every page it watches that
#    lost a query, added by the round that caused it
# ==========================================================================
if lost_queries and os.path.isfile(LEAK_SUITE):
    lsrc = read(LEAK_SUITE)
    tm = re.search(r'TARGETS\s*=\s*\[(.*?)\]', lsrc, re.S)
    targets = set(re.findall(r"'([^']+\.html)'", tm.group(1))) if tm else set()
    lm = re.search(r'LATER\s*=\s*\{(.*?)\n\s*\}', lsrc, re.S)
    later = dict(re.findall(r"'([^']+\.html)'\s*:\s*'([^']+)'",
                            lm.group(1))) if lm else {}
    need = sorted(r for r in lost_queries if r in targets)
    clash = [r for r in need if r in later]
    if clash:
        problems.append('%s: %s already have a LATER entry, and this round '
                        'would need another - the map holds one backup per '
                        'page' % (LEAK_SUITE, ', '.join(clash)))
    fresh = [r for r in need if r not in later]
    if fresh and not clash:
        anchor = re.search(r"(\n(\s*)'workspace_management\.html':\s*"
                           r"'\.bak_stagee')(\})", lsrc)
        if not anchor:
            problems.append('%s: could not find the end of the LATER map'
                            % LEAK_SUITE)
        else:
            pad = anchor.group(2)
            add = ''.join(
                ',\n%s# Zoom-guard round, 21 Sep: its only rule in this '
                'query was a\n%s# redundant 16px guard, so the block emptied '
                'and went.\n%s%r: %r' % (pad, pad, pad, r, SUFFIX)
                for r in fresh)
            ltext = lsrc[:anchor.end(1)] + add + lsrc[anchor.end(1):]
            planned[LEAK_SUITE] = (lsrc, ltext)
            report.append('%-42s + %d LATER entr%s: %s'
                          % (LEAK_SUITE, len(fresh),
                             'y' if len(fresh) == 1 else 'ies',
                             ', '.join(fresh)))


# ==========================================================================
# 4. THE GATE
# ==========================================================================
GATE_NOTE = """    # The page-local iOS zoom guards base made redundant. Its rendered
    # section is the definition of redundant: every page touched, at 375
    # and 1280, before and after, and NO control's computed font-size or
    # padding may change. fsr.html is its control - a guard that is NOT
    # redundant, which the same render must show changing. Newest, so
    # most likely to be what breaks.
    'test_zoom_guards.py'"""

if not os.path.isfile(PS1):
    report.append('%-42s not on disk - the suite is not wired' % PS1)
else:
    psrc = read(PS1)
    if SUITE in psrc:
        report.append('%-42s already runs %s' % (PS1, SUITE))
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
            report.append('%-42s + %s, after %s'
                          % (PS1, SUITE, last.group(1)))


# ==========================================================================
# SELF-CHECK
# ==========================================================================
for path, (src, text) in sorted(planned.items()):
    rel = os.path.relpath(path, ROOT).replace(os.sep, '/') \
        if path.startswith(ROOT) else path
    if path.endswith('.py'):
        try:
            ast.parse(text)
        except SyntaxError as e:
            problems.append('%s: does not parse - line %s' % (rel, e.lineno))
        continue
    if not path.endswith('.html') or path == BASE:
        continue
    # ONLY STYLESHEETS CHANGED. Markup outside <style> must be byte-equal.
    outside = lambda t: re.sub(r'<style[^>]*>.*?</style>', '<style/>', t,
                               flags=re.S)
    if outside(src) != outside(text):
        problems.append('%s: something outside a <style> block changed' % rel)
    css_a = '\n'.join(re.findall(r'<style[^>]*>(.*?)</style>', src, re.S))
    css_b = '\n'.join(re.findall(r'<style[^>]*>(.*?)</style>', text, re.S))
    if css_b.count('{') - css_b.count('}') != \
            css_a.count('{') - css_a.count('}'):
        problems.append('%s: the stylesheet\'s braces no longer balance'
                        % rel)
    # EVERY LINE THAT SURVIVES WAS ALREADY THERE. The round removes; it
    # does not get to rewrite.
    old = set(l.strip() for l in css_a.split('\n'))
    new_lines = [l.strip() for l in css_b.split('\n') if l.strip()]
    added = [l for l in new_lines if l not in old]
    if added:
        problems.append('%s: %d CSS line(s) are new - %r'
                        % (rel, len(added), added[0][:60]))
    # AND EVERY DECLARATION THAT WENT WAS A 16px FONT-SIZE
    def decls_of(c):
        out = []
        for m in re.finditer(r'\{([^{}]*)\}', COMMENT.sub('', c)):
            for k, v in declarations(m.group(1)).items():
                out.append('%s:%s' % (k, v))
        return out
    from collections import Counter
    gone = Counter(decls_of(css_a)) - Counter(decls_of(css_b))
    wrong = [d for d in gone if not re.match(r'font-size:16px( !important)?$',
                                             d)]
    if wrong:
        problems.append('%s: removed a declaration that was not a 16px '
                        'font-size - %s' % (rel, wrong[:2]))


# ==========================================================================
print('\n' + '=' * 74)
print('THE ZOOM GUARDS - %s' % ('DRY RUN' if CHECK else 'APPLY'))
print('=' * 74)
for line in report:
    print('  ' + line)
print("""
  %d whole rule(s) removed, and the font-size line taken out of %d more.

  UNTOUCHED, by decision:
      %d ORPHAN guard(s) - they reach controls with no .form-control, which
        base never does. Their controls joining the field component is a
        visible change, and it belongs in a form-components round.
      %d EVERY-WIDTH guard(s) - they set 16px on the desktop too.
""" % (tally['drop'], tally['strip'], tally['orphan'], tally['every']))
if kept_whole:
    print('  UNTOUCHED, by rule - a page that sets a control below 16px '
          'keeps every guard:')
    for rel, why in sorted(kept_whole.items()):
        print('      %-38s %s' % (rel, why))
    print('')
print('  OUT OF SCOPE:')
for rel, why in sorted(OUT_OF_SCOPE.items()):
    print('      %-38s %s' % (rel, why))
print('')

if problems:
    print('!' * 74)
    print('%d PROBLEM(S). Nothing has been written.' % len(problems))
    print('!' * 74)
    for p in problems:
        print('  FAIL %s' % p)
    sys.exit(1)

if not planned:
    print('  Nothing to do - this round has already been applied.')
    sys.exit(0)

if CHECK:
    print('  --check: nothing written. Re-run without --check to apply.')
    sys.exit(0)

for path, (src, text) in sorted(planned.items()):
    bak = path + SUFFIX
    if not os.path.exists(bak):
        # THE BACKUP KEEPS THE ORIGINAL'S LINE ENDINGS TOO. The line ending
        # is recorded against the file's own path, and the first draft wrote
        # the backup to path + SUFFIX - a key nothing had recorded, so every
        # backup of a CRLF file came out LF. The file was right; the copy
        # you would restore it from was not. apply_entry_sections_4.py and
        # apply_admin_stage_e.py carry the same line. Found by running this
        # patcher on an exact copy of the live bytes and checking them.
        CRLF[bak] = CRLF.get(path)
        write(bak, src)
    write(path, text)

print('  %d file(s) written, backups at *%s' % (len(planned), SUFFIX))
print('  %d keep CRLF line endings, %d keep LF'
      % (sum(1 for p in planned if CRLF.get(p)),
         sum(1 for p in planned if not CRLF.get(p))))
print('')
print('  Next:  python %s' % SUITE)
print('         python %s   (the gate)' % PS1)
