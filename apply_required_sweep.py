"""apply_required_sweep.py - the required marker reaches the screens the
   first round could not see.

    python apply_required_sweep.py --check     dry run, writes nothing
    python apply_required_sweep.py

Run from the repo root.

WHAT THE FIRST ROUND DID, AND WHY IT MISSED THESE

`apply_required_marker.py` normalised the asterisks that were ALREADY THERE -
112 of them, in seven spellings, across 33 templates - into one `.alv-req`
span in a colour base owns. It was a scan for asterisks, so it found every
page that already said "required" and no page that did not.

SEVENTY-SEVEN REQUIRED FIELDS SAY NOTHING AT ALL.

Fourteen screens carry `required` on a control and no marker anywhere near
it. The browser blocks the submit, so the form is not broken - but nothing
tells you WHICH field until you press Save and get a validation bubble. Four
of the fourteen are signed-off modules and are the most-used Add screens in
the system:

    tenant_add / tenant_edit          15 required fields each, 0 marked
    properties_add / properties_edit   9 each, 0 marked
    act_expense_edit                   6, 0 marked
    act_expense_add, cash_receipt_add, fsr_details   4 each, 0 marked
    finance_valuations_add, fsr_add    3 each
    fsr                                2
    act_expense, tenant_lease_agreement, title_deeds_management   1 each

THE SITE IS DECIDED BY THE CONTROL, NOT BY THE TEXT. A site is a control
carrying the `required` attribute whose `id` is named by a `<label for=...>`.
That is a different rule from the first round's - it looks at what the form
DOES rather than at what it already says, which is the only way to find a
field that says nothing.

76 of the 77 resolve to a label. The one that does not is a comment textarea
in `fsr_details` with no `id` at all; it is reported and left alone, because
guessing which label belongs to an unnamed control is how a sweep does
damage.

EVERY REQUIRED FIELD IS MARKED, INCLUDING ON FORMS WHERE ALL OF THEM ARE.
Four of these screens are entirely required - `act_expense_add` is 4 of 4,
`act_expense_edit` 6 of 6 - and on those an asterisk distinguishes nothing.
It is still marked. A reader moving between screens learns ONE rule and does
not have to notice that this particular form happens to be all-required, and
this project has been bitten more than once by exception lists that seemed
obviously right at the time. The screens are named in the report so the
choice is visible rather than silent.

THE FOUR GUARDS, inherited from the first round because each has a scar:

  1. MARKUP ONLY. Scripts, styles and HTML comments are blanked before
     anything is located, so no attribute value and no JavaScript string is
     reachable. The first round wrapped the `*` in `accept="image/*"` and
     broke a file picker.

  2. NEVER TOUCH A LABEL THAT ALREADY SAYS IT. A label carrying an
     `.alv-req`, any other asterisk, or the word "required" is left alone
     and counted separately.

  3. THE EDIT IS ANCHORED ON THE WHOLE LABEL ELEMENT, matched once. A label
     that appears twice byte-for-byte in one file is reported, not guessed
     at.

  4. SELF-CHECK BEFORE WRITING, and every marker must land inside the label
     it was meant for, with the control it belongs to still carrying
     `required`.

HOUSE RULES: idempotent, per-file .bak_reqs backups never overwritten,
--check writes nothing.
"""
import os
import re
import sys

CHECK = '--check' in sys.argv
T = os.path.join(os.getcwd(), 'pages', 'templates')
if not os.path.isdir(T):
    sys.exit('! pages/templates not found - run from the repo root')

MARK = '<span class="alv-req">*</span>'

SKIP = ('recipe', 'meal_plan', 'wcim_', 'pantry_', 'ingredient_',
        'unit_conversions', 'celebration_', 'import_recipe',
        'map_ingredients', 'measurement_units', 'household_member',
        'categories_management')

FAIL = []
NOTES = []


def want(c, m):
    if not c:
        FAIL.append(m)


def load(p):
    with open(p, encoding='utf-8', newline='') as f:
        raw = f.read()
    return raw, ('\r\n' in raw), raw.replace('\r\n', '\n')


def visible(t):
    """Markup with scripts, styles and comments BLANKED - same length, so
       offsets still line up with the original, but nothing inside them can
       be matched. Blanked rather than removed for exactly that reason."""
    def blank(m):
        return ' ' * len(m.group(0))
    t = re.sub(r'<(script|style)[^>]*>.*?</\1>', blank, t, flags=re.S)
    return re.sub(r'<!--.*?-->', blank, t, flags=re.S)


def already_marked(inner):
    return ('alv-req' in inner or '*' in re.sub(r'<[^>]*>', '', inner)
            or re.search(r'\brequired\b', inner, re.I) is not None)


TEMPLATES = []
for _d, _s, _fs in os.walk(T):
    for _f in _fs:
        if _f.endswith('.html'):
            _p = os.path.join(_d, _f)
            _r = os.path.relpath(_p, T).replace(os.sep, '/')
            if _r != 'base.html' and not any(s in _r for s in SKIP):
                TEMPLATES.append(_p)
TEMPLATES.sort()

OUT, REPORT = {}, []
for p in TEMPLATES:
    rel = os.path.relpath(p, T).replace(os.sep, '/')
    orig, crlf, f = load(p)
    vis = visible(f)
    if not re.search(r'<form[^>]*method\s*=\s*["\']post', vis, re.I):
        continue

    # Every control that says it is required, and where it sits.
    need = []
    for m in re.finditer(r'<(?:input|select|textarea)\b[^>]*>', vis, re.I):
        tag = m.group(0)
        if not re.search(r'\brequired\b', tag, re.I):
            continue
        i = re.search(r'\bid\s*=\s*"([^"]+)"', tag)
        need.append((m.start(), i.group(1) if i else None))
    if not need:
        continue

    def find_label(pos, cid):
        """The label this control answers to, as (start, end) or None.

           TWO WAYS A LABEL CAN BELONG TO A CONTROL, and the first version
           of this only knew one. `<label for="id">` is the explicit form.
           But `edit_asset`, `asset_detail` and `property_assets` write
           `<label>Category <span class="alv-req">*</span></label>` with no
           `for` at all - and reporting those as unlabelled said twenty
           required fields were unmarked when they were already marked.

           The fallback is the nearest PRECEDING label with NO OTHER CONTROL
           between it and this one. That last condition is what makes the
           association safe: if another input sits in between, the label
           belongs to that one, and this returns nothing rather than
           guessing."""
        if cid:
            m = re.search(r'<label\b[^>]*\bfor\s*=\s*"' + re.escape(cid)
                          + r'"[^>]*>.*?</label>', vis, re.S)
            if m:
                return m.start(), m.end()
        best = None
        for m in re.finditer(r'<label\b[^>]*>.*?</label>', vis, re.S):
            if m.end() <= pos:
                best = m
            else:
                break
        if best is None:
            return None
        between = vis[best.end():pos]
        if re.search(r'<(?:input|select|textarea)\b', between, re.I):
            return None
        if len(between) > 400:
            return None
        return best.start(), best.end()

    added, marked_already, unlabelled, ambiguous = 0, 0, [], []
    mine = []                       # the ids THIS round marked
    done = set()
    while True:
        moved = False
        vis = visible(f)
        need = []
        for m in re.finditer(r'<(?:input|select|textarea)\b[^>]*>', vis,
                             re.I):
            if not re.search(r'\brequired\b', m.group(0), re.I):
                continue
            i = re.search(r'\bid\s*=\s*"([^"]+)"', m.group(0))
            need.append((m.start(), i.group(1) if i else None))
        for pos, cid in need:
            key = cid or ('@%d' % pos)
            if key in done:
                continue
            span = find_label(pos, cid)
            if span is None:
                done.add(key)
                unlabelled.append(cid or '(a control with no id, at %d)' % pos)
                continue
            a, b = span
            whole = f[a:b]
            inner = re.match(r'<label\b[^>]*>(.*)</label>$', whole, re.S)
            # ALREADY MARKED IS CHECKED FIRST, BEFORE UNIQUENESS.
            #
            # The other order reported six of asset_detail's fields as
            # AMBIGUOUS when they were simply already marked: its add and
            # edit modals hold byte-identical `<label>Date ...</label>`
            # markup, so the duplicate-literal guard fired before anyone
            # asked whether there was anything to do. A guard against
            # editing the wrong one of two identical labels is only
            # relevant when an edit is going to happen.
            if inner is not None and already_marked(inner.group(1)):
                done.add(key)
                marked_already += 1
                continue
            if inner is None or f.count(whole) != 1:
                done.add(key)
                ambiguous.append(cid or '(unnamed)')
                continue
            body = inner.group(1)
            tail = re.match(r'^(.*?)(\s*)$', body, re.S)
            new_label = ('<label'
                         + re.match(r'<label\b([^>]*)>', whole).group(1) + '>'
                         + tail.group(1) + ' ' + MARK + tail.group(2)
                         + '</label>')
            f = f.replace(whole, new_label, 1)
            done.add(key)
            mine.append(cid or '(unnamed)')
            added += 1
            moved = True
            break                    # offsets shifted; recompute
        if not moved:
            break

    if added or unlabelled or ambiguous:
        REPORT.append((rel, len(need), added, marked_already, unlabelled,
                       ambiguous))
    if added:
        OUT[rel] = (orig, crlf, f, mine)

# ===========================================================================
# SELF-CHECK - before a byte is written
# ===========================================================================
for rel, (orig, crlf, f, mine) in OUT.items():
    vis = visible(f)
    was = visible(orig.replace('\r\n', '\n'))
    ids = set()
    for m in re.finditer(r'<(?:input|select|textarea)\b[^>]*>', vis, re.I):
        if re.search(r'\brequired\b', m.group(0), re.I):
            i = re.search(r'\bid\s*=\s*"([^"]+)"', m.group(0))
            if i:
                ids.add(i.group(1))
    # ONLY THE MARKERS THIS ROUND ADDED. The first version asserted that
    # EVERY marker in the file sits on a required control, and twelve
    # pre-existing ones do not - eleven in generate_lease_agreement, one in
    # passport_management, all of them saying "required" beside a control
    # that does not enforce it. That is a real inconsistency and it is
    # REPORTED below, but failing this round for it would be a whole-file
    # claim about a per-site change, which has failed correct work four
    # times on this codebase.
    for cid in mine:
        if cid == '(unnamed)':
            continue                 # no id to look it up by; covered below
        m = re.search(r'<label\b[^>]*\bfor\s*=\s*"' + re.escape(cid)
                      + r'"[^>]*>(.*?)</label>', vis, re.S)
        if m is not None:
            want('alv-req' in m.group(1),
                 '%s: the marker for %s is not in its label' % (rel, cid))
            want(cid in ids,
                 '%s: marked %s, whose control is not required' % (rel, cid))
    # Not one marker outside a label.
    stripped = re.sub(r'<label\b[^>]*>.*?</label>', ' ', vis, flags=re.S)
    want('alv-req' not in stripped,
         '%s: a marker landed outside a label' % rel)
    # NOTHING ELSE MOVED. Strip the marker from BOTH sides and compare.
    #
    # The first version stripped it from the new file only and compared with
    # the untouched original, which fails on any page that ALREADY had
    # markers - passport_management has six. Same fault as measuring against
    # the wrong referent: the claim is 'nothing but markers differ', so both
    # sides have to be reduced the same way.
    _strip = lambda t: t.replace(' ' + MARK, '')
    want(_strip(f) == _strip(orig.replace('\r\n', '\n')),
         '%s: something other than a marker changed' % rel)
    # And the number of markers went up by exactly what was added.
    want(f.count(MARK) - orig.replace('\r\n', '\n').count(MARK) == len(mine),
         '%s: marker count moved by %d, expected %d'
         % (rel, f.count(MARK) - orig.replace('\r\n', '\n').count(MARK),
            len(mine)))
    # Structure untouched.
    for tag in ('div', 'form', 'label', 'span'):
        a = (len(re.findall(r'<%s\b' % tag, vis))
             - len(re.findall(r'</%s>' % tag, vis)))
        b = (len(re.findall(r'<%s\b' % tag, was))
             - len(re.findall(r'</%s>' % tag, was)))
        want(a == b, '%s: <%s> balance moved %+d -> %+d' % (rel, tag, b, a))

# A MARKER WITH NOTHING BEHIND IT - the mirror image of what this round
# fixes, found by the check above and reported rather than swept.
BACKWARDS = []
for _p in TEMPLATES:
    _rel = os.path.relpath(_p, T).replace(os.sep, '/')
    _v = visible(load(_p)[2])
    _ids = set()
    for m in re.finditer(r'<(?:input|select|textarea)\b[^>]*>', _v, re.I):
        if re.search(r'\brequired\b', m.group(0), re.I):
            i = re.search(r'\bid\s*=\s*"([^"]+)"', m.group(0))
            if i:
                _ids.add(i.group(1))
    for m in re.finditer(r'<label\b([^>]*)>(.*?)</label>', _v, re.S):
        if 'alv-req' not in m.group(2):
            continue
        fo = re.search(r'\bfor\s*=\s*"([^"]+)"', m.group(1))
        if fo and fo.group(1) not in _ids:
            BACKWARDS.append((_rel, fo.group(1)))

if FAIL:
    print('\n! SELF-CHECK FAILED - nothing written\n')
    for x in FAIL:
        print('   - %s' % x)
    sys.exit(1)

print('\n%-34s %8s %7s %8s' % ('template', 'required', 'marked', 'already'))
print('-' * 62)
tot = 0
for rel, need, added, was_marked, unl, amb in REPORT:
    print('%-34s %8d %7d %8d' % (rel, need, added, was_marked))
    tot += added
    for x in unl:
        print('      NO LABEL, left alone: %s' % x)
    for x in amb:
        print('      AMBIGUOUS, left alone: %s' % x)
print('\n  %d marker(s) added across %d template(s)' % (tot, len(OUT)))

ALL_REQUIRED = []
for rel in OUT:
    vis = visible(OUT[rel][2])
    ctrls = [m.group(0) for m in
             re.finditer(r'<(?:input|select|textarea)\b[^>]*>', vis, re.I)
             if not re.search(r'type\s*=\s*"(hidden|submit|button|search)"',
                              m.group(0), re.I)]
    req = [c for c in ctrls if re.search(r'\brequired\b', c, re.I)]
    if ctrls and len(req) == len(ctrls):
        ALL_REQUIRED.append(rel)
if ALL_REQUIRED:
    print('\n  NOTE  every field is required on these, so the marker '
          'distinguishes\n        nothing there. Marked anyway, on purpose - '
          'one rule the reader\n        learns once beats a screen that '
          'quietly opts out:')
    for rel in ALL_REQUIRED:
        print('          %s' % rel)

print()
if BACKWARDS:
    print('\n  NOTE  %d label(s) already say a field is required beside a '
          'control that\n        does NOT enforce it - the mirror image of '
          'what this round fixes.\n        Reported, not swept: adding '
          '`required` changes what a form ACCEPTS,\n        which is '
          'behaviour, not styling, and wants its own round.' % len(BACKWARDS))
    _by = {}
    for _r, _i in BACKWARDS:
        _by.setdefault(_r, []).append(_i)
    for _r in sorted(_by):
        print('          %-38s %s' % (_r, ', '.join(_by[_r][:4])
                                      + (' ...' if len(_by[_r]) > 4 else '')))

print()
for rel in sorted(OUT):
    orig, crlf, f, _m = OUT[rel]
    out = f.replace('\n', '\r\n') if crlf else f
    print('  %-38s %6d -> %6d bytes'
          % (rel, len(orig.encode('utf-8')), len(out.encode('utf-8'))))

if not CHECK:
    for rel in sorted(OUT):
        orig, crlf, f, _m = OUT[rel]
        out = f.replace('\n', '\r\n') if crlf else f
        p = os.path.join(T, rel.replace('/', os.sep))
        bak = p + '.bak_reqs'
        if not os.path.exists(bak):
            with open(bak, 'w', encoding='utf-8', newline='') as fh:
                fh.write(orig)
        with open(p, 'w', encoding='utf-8', newline='') as fh:
            fh.write(out)

print('\n  --check: nothing written.' if CHECK else '\n  done.')
