"""Show-FormSections.py - how every Add/Edit screen in the system says
   "this is a section", and what it would say after the entry-sections round.

    python Show-FormSections.py              every template
    python Show-FormSections.py projects     only paths containing 'projects'
    python Show-FormSections.py --fields     also print each screen's field list

Run from the repo root. READ-ONLY. Writes nothing, touches nothing.

WHY IT EXISTS. `Show-EntryScreens.py` measured the entry screens but carried a
NAME-BASED SKIP LIST - recipe_, meal_plan_, celebration_, household_member_,
passport_, ingredient_, categories_management. Those are not stray files; they
are the Personal module, and "all the Add/Edit screens across the entire
application" includes it. Its own docstring warns that naming rounds on this
codebase have gone wrong twice by matching filenames, and then it matches
filenames. THIS TOOL HAS NO SKIP LIST. A page is in or out because of what it
does.

WHAT IT FOUND, 18 Sep 2026: seven different ways to say "section" -
form-section-title, form-section-heading, section-title, pi-section-title,
lines-title, a bare <h2>/<h5>/<h6>, and h5.mb-0. base.html declares exactly
one of them.
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

ARGS = [a for a in sys.argv[1:]]
WANT_FIELDS = '--fields' in ARGS
NEEDLE = ([a for a in ARGS if not a.startswith('--')] or [''])[0]

ROOT = os.path.join(os.getcwd(), 'pages', 'templates')
if not os.path.isdir(ROOT):
    sys.exit('! pages/templates not found - run from the repo root')

# THE STANDARD, and the six impostors. base.html declares the first one.
STANDARD = 'form-section-title'
IMPOSTORS = ('form-section-heading', 'section-title', 'pi-section-title',
             'lines-title')

# A page is EXCLUDED only for a reason that is about what it does. Each
# entry carries that reason, because a list without reasons is a list.
EXCLUDE = {
    'base.html': 'the layout, not a screen',
    'physical_invoice_edit.html': 'every control is an invoice-line cell',
    'create_recipe (OLD DO NOT USE).html': 'the filename says so',
    'edit_recipe (OLD DO NOT USE).html': 'the filename says so',
}

# A LISTING FILTER IS NOT AN ENTRY SCREEN, and three listing pages post one:
# fsr, properties and tenant. They are not excluded by filename - that is the
# habit this tool exists to break - but by what the form is made of. A filter
# names its controls after the COLUMNS it narrows, marks nothing required, and
# has nowhere for prose. A record does the opposite.
FILTER_NAMES = {'search', 'country', 'status', 'sort', 'filter', 'act',
                'propname', 'propcountry', 'tenantname', 'issuestatus',
                'propstatus', 'suppliername'}


def looks_like_a_filter(names, chunk):
    if re.search(r'\brequired\b', chunk) or re.search(r'<textarea', chunk, re.I):
        return False
    hits = sum(1 for n in names if n in FILTER_NAMES)
    return hits >= 2 and hits >= len(names) - 1


def read(p):
    with open(p, encoding='utf-8', errors='replace') as f:
        return f.read().replace('\r\n', '\n')


def markup(t):
    return re.sub(r'<(script|style)[^>]*>.*?</\1>', '', t, flags=re.S)


def text_of(h):
    return re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', h)).strip()


files = []
for dp, _d, ns in os.walk(ROOT):
    for n in sorted(ns):
        if not n.endswith('.html'):
            continue
        rel = os.path.relpath(os.path.join(dp, n), ROOT).replace(os.sep, '/')
        if NEEDLE and NEEDLE not in rel:
            continue
        files.append((rel, os.path.join(dp, n)))

screens, skipped, excluded = [], [], []

VOID = {'input', 'img', 'br', 'hr', 'meta', 'link', 'source', 'col', 'area',
        'base', 'embed', 'param', 'track', 'wbr'}


def forms_of(mk):
    """Every <form method="post"> in the page, with its span and whether it
    is inside a modal.

    WHY A STACK AND NOT A REGEX. The first version of this tool answered
    "is this in a modal?" with `'class="modal"' in page`, and said modal for
    properties_edit - a full-page form on a page that happens to also carry a
    pro-rata warning dialog. The question is not whether the PAGE has a modal;
    it is whether THIS FORM is inside one. That is an ancestry question and
    ancestry needs a stack.

    It also answers a second question the page-level version could not: a
    listing page like fsr.html is not an entry screen, but the Add Issue modal
    inside it IS one. Counting per page merged the two.

    Tolerant on purpose: Django templates put {% if %} around opening tags
    whose closing tag lives in the else branch, so an unmatched close pops
    nothing rather than raising."""
    stack, out = [], []
    open_form = None
    for m in re.finditer(r'<(/?)([a-zA-Z][\w-]*)([^>]*?)(/?)>', mk):
        closing, tag, attrs, selfclose = (m.group(1), m.group(2).lower(),
                                          m.group(3), m.group(4))
        if tag in VOID or selfclose:
            continue
        if closing:
            if tag == 'form' and open_form is not None:
                out.append((open_form[0], m.end(), open_form[1]))
                open_form = None
            for k in range(len(stack) - 1, -1, -1):
                if stack[k][0] == tag:
                    del stack[k:]
                    break
            continue
        cls = re.search(r'class\s*=\s*["\']([^"\']*)', attrs)
        cls = cls.group(1) if cls else ''
        if tag == 'form':
            if re.search(r'method\s*=\s*["\']post["\']', attrs, re.I):
                in_modal = any('modal' in c.split() for _t, c in stack)
                open_form = (m.start(), in_modal)
        stack.append((tag, cls))
    if open_form is not None:
        out.append((open_form[0], len(mk), open_form[1]))
    return out


for rel, p in files:
    base = rel.rsplit('/', 1)[-1]
    if base in EXCLUDE:
        excluded.append((rel, EXCLUDE[base]))
        continue

    mk = markup(read(p))
    found_any = noted = False
    for start, end, in_modal in forms_of(mk):
        chunk = mk[start:end]
        ctrl = re.findall(r'<(input|select|textarea)\b([^>]*)>', chunk, re.I)
        real = [c for c in ctrl
                if not re.search(r'type\s*=\s*["\'](?:hidden|submit|button|'
                                 r'search|reset|image)["\']', c[1], re.I)]
        if len(real) < 3:
            continue
        names = [(re.search(r'\bname\s*=\s*["\']([^"\']+)', c[1])
                  or [None, '-'])[1] for c in real]
        if looks_like_a_filter(names, chunk):
            skipped.append((rel, 'a listing filter - %s' % ', '.join(names)))
            noted = True
            continue
        found_any = True
        panels = len(re.findall(r'class="[^"]*\bform-card\b', chunk))

        # --- HOW DOES THIS FORM SAY "SECTION"? ----------------------------
        # Headings INSIDE the form. A heading above it is the page title or
        # the modal's own title bar, and neither is a section.
        said = {}
        for m in re.finditer(r'<(h[1-6])([^>]*)>(.*?)</\1>', chunk, re.S):
            tag, attrs, inner = m.group(1), m.group(2), m.group(3)
            cls = re.search(r'class\s*=\s*["\']([^"\']*)', attrs)
            cls = cls.group(1).strip() if cls else ''
            if re.search(r'page-(?:title|subtitle)|modal-title|alert-heading',
                         cls):
                continue
            key = (STANDARD if STANDARD in cls.split()
                   else next((i for i in IMPOSTORS if i in cls.split()), None)
                   or (('%s.%s' % (tag, cls.replace(' ', '.')))
                       if cls else '<%s> bare' % tag))
            said.setdefault(key, []).append(text_of(inner)[:52])

        label = rel + ('  [modal]' if in_modal else '')
        screens.append(dict(rel=rel, label=label, ctrl=len(real),
                            panels=panels, modal=in_modal, said=said,
                            fields=names))
    if not (found_any or noted):
        skipped.append((rel, 'no posted form of three or more data controls'))

# --------------------------------------------------------------------------
print('\n%d ADD/EDIT SCREEN(S) - a page that posts three or more data controls'
      % len(screens))
print('=' * 78)
print('\n%-44s %5s %6s %6s %s'
      % ('form', 'ctrls', 'panels', 'sects', 'where'))
print('-' * 78)
for s in screens:
    n = sum(len(v) for v in s['said'].values())
    print('%-44s %5d %6d %6d %s'
          % (s['rel'], s['ctrl'], s['panels'], n,
             'modal' if s['modal'] else 'page'))

print('\n' + '=' * 78)
print('HOW THE SYSTEM SAYS "THIS IS A SECTION"')
print('base.html declares one class. This is how many are in use.')
print('=' * 78)
dialects = {}
for s in screens:
    for k, v in s['said'].items():
        dialects.setdefault(k, []).append((s['label'], len(v)))
for k in sorted(dialects, key=lambda k: (-sum(n for _r, n in dialects[k]), k)):
    tot = sum(n for _r, n in dialects[k])
    mark = '  <-- THE STANDARD' if k == STANDARD else ''
    print('\n  %-34s %3d heading(s) on %2d page(s)%s'
          % (k, tot, len(dialects[k]), mark))
    for r, n in sorted(dialects[k]):
        print('        %-52s %2d' % (r, n))

print('\n' + '=' * 78)
print('SCREENS WITH NO SECTION AT ALL - what the round is for')
print('=' * 78)
none = [s for s in screens if not s['said']]
for s in sorted(none, key=lambda s: -s['ctrl']):
    print('  %-44s %3d control(s)%s'
          % (s['label'], s['ctrl'], '  (in a modal)' if s['modal'] else ''))
print('\n  %d screen(s), %d control(s) between them'
      % (len(none), sum(s['ctrl'] for s in none)))

print('\n' + '=' * 78)
print('SECTIONS BUT NO PANEL - the panel-title round could not reach these,')
print('because it sweeps a .form-card\'s first heading and there is no card')
print('=' * 78)
for s in screens:
    if s['said'] and not s['panels']:
        print('  %-44s %2d heading(s), 0 panels'
              % (s['label'], sum(len(v) for v in s['said'].values())))

print('\n' + '=' * 78)
print('THE RULE: six or fewer controls is one section; seven or more splits,')
print('and no section holds more than eight')
print('=' * 78)
for s in sorted(screens, key=lambda s: -s['ctrl']):
    n = sum(len(v) for v in s['said'].values())
    want = 1 if s['ctrl'] <= 6 else max(2, -(-s['ctrl'] // 8))
    flag = 'ok' if n >= want else 'NEEDS %d more' % (want - n)
    print('  %-44s %3d ctrl  has %2d  wants >=%d  %s'
          % (s['label'], s['ctrl'], n, want, flag))

if WANT_FIELDS:
    print('\n' + '=' * 78)
    print('THE FIELD ORDER - the round\'s invariant is that this list is')
    print('byte-identical before and after, except where a move is named')
    print('=' * 78)
    for s in screens:
        print('\n  %s' % s['label'])
        for f in s['fields']:
            print('      %s' % f)

print('\n' + '=' * 78)
print('NOT ENTRY SCREENS')
print('=' * 78)
print('\n  %d page(s) post a form of fewer than three data controls:'
      % len(skipped))
for r, why in skipped:
    print('      %-52s %s' % (r, why))
print('\n  %d page(s) excluded with a reason:' % len(excluded))
for r, why in excluded:
    print('      %-52s %s' % (r, why))
