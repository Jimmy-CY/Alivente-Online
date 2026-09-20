"""apply_sections_fix.py - three things the entry-sections round got wrong,
   found by looking at the screens.

    python apply_sections_fix.py --check     dry run
    python apply_sections_fix.py             apply

Run from the repo root. Idempotent.

1. A SECTION TITLE IS NOT A GRID CELL

  Six screens lay their fields out in `.form-grid { display: grid;
  grid-template-columns: 1fr 1fr }` and customer_invoice_form puts its
  invoice date and VAT rate in `.settings-row { display: flex }`. Push 2 put
  the title INSIDE those containers, so it became an ITEM: it took one cell,
  its accent rule stopped halfway across the panel, and the first field sat
  BESIDE the heading instead of under it. Seven screens, all from push 2,
  and every one of them looked wrong on screen while every check passed -
  because every check asked whether the title was THERE, and none asked
  where.

2. A MODAL HEADER IS ALREADY A TITLE

  "A modal body is already a panel" was right, and it was half the rule.
  Push 3 gave three single-section modals a title that repeats the header
  the modal already carries - and on view_meal_plan it repeats it WORD FOR
  WORD: a modal headed "Duplicate Meal Plan" with a section titled
  "Duplicate Meal Plan". A title on a one-section modal has nothing to add.

  A modal with MORE than one section keeps its titles, because there they
  do the dividing.

3. asset_detail WAS NEVER REACHED

  It was in the first survey with "Maintenance Record" proposed, and it was
  lost between that document and push 1. No reason was recorded because
  there was not one.

  It does not get "Maintenance Record" - that is fault 2, and its modal
  header already says it. It gets the split its six fields actually have:
  what was done, and who did it and what it cost.

WHY NOT FIX FAULT 1 IN base

  `.form-section-title { grid-column: 1 / -1 }` would make the component
  span wherever it lands, and it was tempting. But
  preview_imported_recipe's Cooking Calculator heading sits inside
  `.cooking-calc-toggle { display: flex }` ON PURPOSE, beside a chevron, and
  notification_settings' heading IS a flex container rather than an item in
  one. A blanket rule would break the two places the arrangement is
  deliberate. The structural fix is precise; the global one is a guess that
  happens to be right six times out of seven.

WHAT THIS ROUND DOES NOT DO

  It moves no field. Every control on every screen it touches is in the
  same order afterwards, and the self-check fails the run if one is not.
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

SUFFIX = '.bak_sectfix'
TAG, CLS = 'h3', 'form-section-title'
SUITE = 'test_entry_sections.py'
PS1 = 'Push-PendingChanges.ps1'
VOID = {'input', 'img', 'br', 'hr', 'meta', 'link', 'source', 'col', 'area',
        'base', 'embed', 'param', 'track', 'wbr'}

problems, report = [], []
MOVES = {}


def read(p):
    with open(p, encoding='utf-8') as f:
        return f.read()


def markup_only(text):
    out = list(text)
    for m in re.finditer(r'<(script|style)[^>]*>(.*?)</\1>', text, re.S):
        for i in range(m.start(2), m.end(2)):
            if out[i] != '\n':
                out[i] = ' '
    return ''.join(out)


def indent_at(text, pos):
    ls = text.rfind('\n', 0, pos) + 1
    return re.match(r'[ \t]*', text[ls:pos]).group(0)


def parents_of_titles(mk):
    """(heading_start, heading_end, parent_open_start, parent_classes) for
    every section title, walking a stack so the parent is the element that
    actually encloses it rather than the nearest <div> before it."""
    out, stack = [], []
    pat = re.compile(r'<(/?)([a-zA-Z][\w-]*)([^>]*?)(/?)>')
    for m in pat.finditer(mk):
        closing, tag, attrs, self_close = (m.group(1), m.group(2).lower(),
                                           m.group(3), m.group(4))
        if tag == TAG and not closing and CLS in attrs:
            end = mk.find('</%s>' % TAG, m.end())
            end = end + len('</%s>' % TAG) if end > 0 else m.end()
            if stack:
                out.append((m.start(), end, stack[-1][1], stack[-1][2]))
            continue
        if tag in VOID or self_close:
            continue
        if closing:
            for k in range(len(stack) - 1, -1, -1):
                if stack[k][0] == tag:
                    del stack[k:]
                    break
            continue
        cls = re.search(r'class\s*=\s*["\']([^"\']*)', attrs)
        stack.append((tag, m.start(), cls.group(1).strip() if cls else ''))
    return out


# ==========================================================================
# 1. A SECTION TITLE IS NOT A GRID CELL
#
# Six screens lay their fields out in `.form-grid { display: grid;
# grid-template-columns: 1fr 1fr }`, and customer_invoice_form puts its
# invoice date and VAT rate in `.settings-row { display: flex }`. Push 2 put
# the title INSIDE those containers, so it became an ITEM: it took one cell,
# its accent rule stopped halfway across, and the first field sat BESIDE the
# heading instead of under it.
#
# WHY NOT FIX IT IN base. `.form-section-title { grid-column: 1 / -1 }`
# would make the component span wherever it lands, and it was tempting. But
# preview_imported_recipe's Cooking Calculator heading sits inside
# `.cooking-calc-toggle { display: flex }` ON PURPOSE, beside a chevron -
# a blanket `flex-basis: 100%` would break the one place the arrangement is
# deliberate. The structural fix is precise; the global one is a guess that
# happens to work six times out of seven.
#
# So: the heading moves to just before the container opens. Every one of
# these screens has exactly ONE title inside its container, which is
# asserted rather than assumed - with two, moving both out would reorder the
# fields between them.
LAYOUT_PARENTS = ('form-grid', 'settings-row')

# Named, with the reason. These two are section titles INSIDE a flex
# container and are meant to be.
NOT_A_FAULT = {
    'preview_imported_recipe.html': 'cooking-calc-toggle - the heading sits '
                                    'beside the toggle chevron, deliberately',
    'notification_settings.html': 'the heading IS the flex container, not an '
                                  'item in one - it lays out its own chevron',
}

for dp, _d, names in os.walk(ROOT):
    for n in sorted(names):
        if not n.endswith('.html'):
            continue
        rel = os.path.relpath(os.path.join(dp, n), ROOT).replace(os.sep, '/')
        path = os.path.join(dp, n)
        src = read(path)
        mk = markup_only(src)
        hits = [h for h in parents_of_titles(mk)
                if any(c in LAYOUT_PARENTS for c in h[3].split())]
        if not hits:
            continue
        if len(hits) > 1:
            problems.append('%s: %d titles inside a layout container - '
                            'moving them all out would reorder the fields '
                            'between them' % (rel, len(hits)))
            continue
        h0, h1, p0, pcls = hits[0]
        heading = src[h0:h1].strip()
        # cut the heading out, including the line it sat on
        ls_h = src.rfind('\n', 0, h0) + 1
        le_h = src.find('\n', h1)
        le_h = len(src) if le_h < 0 else le_h + 1
        cut = src[:ls_h] + src[le_h:]
        # and put it in front of the container, at the container's indent
        p0c = p0 - (le_h - ls_h) if p0 > ls_h else p0
        ls_p = cut.rfind('\n', 0, p0c) + 1
        pad = re.match(r'[ \t]*', cut[ls_p:p0c]).group(0)
        out = cut[:ls_p] + pad + heading + '\n' + cut[ls_p:]
        MOVES[rel] = (path, src, out)
        report.append('%-38s   title moved out of .%s'
                      % (rel, [c for c in pcls.split()
                               if c in LAYOUT_PARENTS][0]))


# ==========================================================================
# 2. A MODAL HEADER IS ALREADY A TITLE
#
# "A modal body is already a panel" was right and it was half the rule.
# Push 3 gave three single-section modals a title that repeats the header
# the modal already carries - and on view_meal_plan it repeats it WORD FOR
# WORD. A section title on a one-section modal has nothing to add: it says
# the heading again, one line lower.
#
# A modal with MORE than one section keeps its titles, because there the
# titles are doing the dividing. passport_management keeps Document,
# Validity and File; celebration_management's Add Event keeps Event and
# Notifications.
DROP = {
    'view_meal_plan.html': ['Duplicate Meal Plan'],
    'household_member_management.html': ['Person'],
    'celebration_management.html': ['Contact'],
}

for rel, titles in sorted(DROP.items()):
    path = os.path.join(ROOT, rel)
    if not os.path.isfile(path):
        continue
    src = MOVES[rel][2] if rel in MOVES else read(path)
    base = MOVES[rel][1] if rel in MOVES else read(path)
    text, gone = src, []
    for t in titles:
        pat = re.compile(r'[ \t]*<%s class="%s"><i[^>]*></i>\s*%s\s*</%s>\n'
                         % (TAG, CLS, re.escape(t), TAG))
        found = list(pat.finditer(text))
        if not found:
            continue
        if len(found) != 1:
            problems.append('%s: the title %r appears %d time(s), expected 1'
                            % (rel, t, len(found)))
            continue
        text = text[:found[0].start()] + text[found[0].end():]
        gone.append(t)
    if gone:
        MOVES[rel] = (path, base, text)
        report.append('%-38s - %s  (the modal header already says it)'
                      % (rel, ', '.join(gone)))


# ==========================================================================
# 3. asset_detail, which no push reached
#
# It was in the first survey with "Maintenance Record" proposed and it was
# simply lost between that document and push 1. Its two modals - Add and
# Edit Maintenance Record - carry six fields each in one undivided run.
#
# It does NOT get "Maintenance Record": that is the fault above, and the
# modal header already says it. It gets the split the six fields actually
# have - what was done, and who did it and what it cost.
MODAL_SECTIONS = {
    'asset_detail.html': [
        ('Add Maintenance Record', [('wrench', 'Work', 'date'),
                                    ('euro-sign', 'Provider &amp; Cost',
                                     'service_provider')]),
        ('Edit Maintenance Record', [('wrench', 'Work', 'date'),
                                     ('euro-sign', 'Provider &amp; Cost',
                                      'service_provider')]),
    ],
}


def close_of(mk, open_end):
    depth, i = 1, open_end
    while depth and i < len(mk):
        m = re.compile(r'<div\b|</div>').search(mk, i)
        if not m:
            return None
        depth += -1 if m.group(0) == '</div>' else 1
        i = m.end()
    return i if not depth else None


for rel, modals in sorted(MODAL_SECTIONS.items()):
    path = os.path.join(ROOT, rel)
    if not os.path.isfile(path):
        problems.append('%s: not found' % rel)
        continue
    src = read(path)
    if 'class="%s"' % CLS in markup_only(src):
        report.append('%-38s already sectioned' % rel)
        continue
    text, placed = src, []
    # right to left so earlier offsets stay valid
    for header, sections in reversed(modals):
        mk = markup_only(text)
        # THE MODAL IS FOUND BY ITS OWN HEADER, because both modals hold the
        # same field names - date, maintenance_type, cost - and a first-match
        # anchor would put every title in the first one and none in the
        # second.
        hh = [m for m in re.finditer(
            r'class="modal-title"[^>]*>\s*%s\s*<' % re.escape(header), mk)]
        if len(hh) != 1:
            problems.append('%s: the modal header %r appears %d time(s), '
                            'expected 1' % (rel, header, len(hh)))
            break
        body = re.compile(r'<div class="modal-body"[^>]*>').search(
            mk, hh[0].end())
        if not body:
            problems.append('%s: no modal body after %r' % (rel, header))
            break
        end = close_of(mk, body.end())
        if end is None:
            problems.append('%s: the modal body after %r does not close'
                            % (rel, header))
            break
        for icon, title, first in reversed(sections):
            grp = None
            for m in re.finditer(r'<div class="[^"]*form-group[^"]*"[^>]*>',
                                 mk[body.end():end]):
                s0 = body.end() + m.start()
                s1 = close_of(mk, body.end() + m.end())
                if s1 and re.search(r'\bname\s*=\s*["\']%s["\']'
                                    % re.escape(first), mk[s0:s1]):
                    grp = s0
                    break
            if grp is None:
                problems.append('%s: %r has no field named %r'
                                % (rel, header, first))
                break
            ls = text.rfind('\n', 0, grp) + 1
            pad = indent_at(text, grp)
            text = (text[:ls] + '%s<%s class="%s"><i class="fas fa-%s"></i> '
                    '%s</%s>\n' % (pad, TAG, CLS, icon, title, TAG)
                    + text[ls:])
            placed.append('%s / %s' % (header.split()[0], title))
            mk = markup_only(text)
    if len(placed) == sum(len(s) for _h, s in modals):
        MOVES[rel] = (path, src, text)
        report.append('%-38s + %s' % (rel, ', '.join(reversed(placed))))


# ==========================================================================
# SELF-CHECK
# ==========================================================================
planned = MOVES

for rel, (path, src, text) in sorted(planned.items()):
    if text == src:
        problems.append('%s: planned a change and produced none' % rel)
        continue
    for tag in ('div', 'form'):
        d0 = len(re.findall(r'<%s\b' % tag, src)) - src.count('</%s>' % tag)
        d1 = len(re.findall(r'<%s\b' % tag, text)) - text.count('</%s>' % tag)
        if d1 != d0:
            problems.append('%s: <%s> balance moved %d -> %d'
                            % (rel, tag, d0, d1))

    def names(t):
        return [(re.search(r'\bname\s*=\s*["\']([^"\']+)', m.group(2))
                 or [None, '-'])[1]
                for m in re.finditer(r'<(input|select|textarea)\b([^>]*)>',
                                     markup_only(t), re.I)
                if not re.search(r'type\s*=\s*["\'](?:submit|button|reset'
                                 r'|image)["\']', m.group(2), re.I)]
    if names(src) != names(text):
        problems.append('%s: a control moved - this round moves NO field, '
                        'only headings' % rel)
    # and nothing this round touched may still be a layout item
    left = [h for h in parents_of_titles(markup_only(text))
            if any(c in LAYOUT_PARENTS for c in h[3].split())]
    if left:
        problems.append('%s: %d title(s) still inside a layout container'
                        % (rel, len(left)))

print('\n' + '=' * 74)
print('SECTIONS FIX - %s' % ('DRY RUN' if CHECK else 'APPLY'))
print('=' * 74)
for line in report:
    print('  ' + line)
print('\n  Deliberately left inside a flex container:')
for rel, why in sorted(NOT_A_FAULT.items()):
    print('      %-34s %s' % (rel, why))

if problems:
    print('\n' + '!' * 74)
    print('%d PROBLEM(S). Nothing has been written.' % len(problems))
    print('!' * 74)
    for p in problems:
        print('  FAIL %s' % p)
    sys.exit(1)

if not planned:
    print('\n  Nothing to do - this round has already been applied.')
    sys.exit(0)

if CHECK:
    print('\n  --check: nothing written. Re-run without --check to apply.')
    sys.exit(0)

for path, src, text in planned.values():
    bak = path + SUFFIX
    if not os.path.exists(bak):
        with open(bak, 'w', encoding='utf-8', newline='') as f:
            f.write(src)
    with open(path, 'w', encoding='utf-8', newline='') as f:
        f.write(text)

print('\n  %d file(s) written, backups at *%s' % (len(planned), SUFFIX))
print('\n  Next:  python %s' % SUITE)
print('         python %s   (the gate)' % PS1)
