# -*- coding: utf-8 -*-
"""apply_lease_sections.py - Section C, round C5: the lease generator takes
the house sections.

    python apply_lease_sections.py --check     dry run, nothing written
    python apply_lease_sections.py             apply

Run from the repo root. Idempotent: a second run reports nothing to do.

Decided 22 Sep (claude/section_c_decision_sheet.md item 9) and 23 Sep, from
claude/lease_generator_survey.md - the sheet said twelve coloured bars; the
survey counted THIRTEEN:

  - THE WIZARD'S THREE STEPS become house panels: .form-card, with
    h3.form-section-title and the icon each already had. Nothing moves.
  - THE TEN INSIDE THE POP-UP become TITLES, no panels. A modal body is
    already a panel - that is the rule every other pop-up in the system
    follows, and the one the entry-sections round wrote down.
  - THE COLOURS GO AND NOTHING REPLACES THEM. The amber New Tenant bar and
    the green Second Tenant bar only ever appear when they apply, so the
    colour repeated what their presence already said.
  - THREE TITLES CARRY A CONTROL - Add Second Tenant, Remove, and the Fully
    Furnished checkbox. They stay beside the title. The TITLE is the flex
    container, never a flex item: an item's underline would stop halfway
    across the section, which is the fault the 20 Sep fix round found on
    seven screens. Notification Settings' collapse header does the same.
  - EVERY SECTION GETS ONE ICON, as the entry screens do.
  - THE FIVE SUB-HEADINGS inside Furniture - Kitchen, Lounge / Dining,
    Bedroom, General, Balcony - keep their words and their teal, and take a
    class instead of an inline style. So does the Fully Furnished note.

Not in this round: the page is deliberately desktop-only below 768px - it
shows "Desktop or Tablet Required" instead of the wizard - so the phone
rule that every Add/Edit screen works on a phone is answered here by that
guard, not by this round.
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
T = os.path.join('pages', 'templates')
if not os.path.isdir(T):
    sys.exit('! pages/templates not found - run from the repo root')
SUFFIX = '.bak_lease'
SUITE = 'test_lease_sections.py'
PS1 = 'Push-PendingChanges.ps1'
ROUNDS_FILE = 'alv_rounds.py'
PAGE = os.path.join(T, 'generate_lease_agreement.html')

# LONGEST FIRST. "New Tenant Information" must not take the icon of
# "Tenant Information", which is a different section three cards above it.
ICONS = [('Second Tenant Information', 'fa-user-friends'),
         ('New Tenant Information', 'fa-user-plus'),
         ('Additional Information Required', 'fa-id-card'),
         ('Property Information', 'fa-building'),
         ('Tenant Information', 'fa-user'),
         ('Landlord Information', 'fa-user-tie'),
         ('Lease Terms', 'fa-file-contract'),
         ('Furniture and Appliances', 'fa-couch'),
         ('Keys Provided', 'fa-key'),
         ('Amenities', 'fa-star'),
         ('Step 1', 'fa-globe-americas'),
         ('Step 2', 'fa-home'),
         ('Step 3', 'fa-file-download')]

CSS = """
  /* THE SECTIONS ARE BASE'S - 23 Sep 2026. The page's thirteen coloured
     card headers are h3.form-section-title now; base draws them. Only the
     three that carry a control need anything of their own.

     THE TITLE IS THE FLEX CONTAINER, not a flex item. A title that is an
     item gets an underline as wide as its own words - the fault the fix
     round found on seven screens in September - while a title that IS the
     row keeps base's rule right across the section. Notification Settings'
     collapse header works the same way.        [test_lease_sections.py] */
  .lease-title-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
  }
  .lease-title-note {
    font-size: 14px;
    font-weight: 400;
    color: var(--alv-ink-soft);
  }
  /* Kitchen, Lounge / Dining, Bedroom, General, Balcony - a group inside
     the Furniture section, not a section of its own. Same words, same
     teal, said in a class. */
  .lease-subhead {
    color: var(--alv-accent);
    font-weight: 600;
  }
"""
CSS_ANCHOR = ('  /* Desktop-only message — hidden by default */\n')

SUBHEADS = [
    ('<h6 class="mt-2 mb-2" style="color: #0e7c8b; font-weight: 600;">',
     '<h6 class="mt-2 mb-2 lease-subhead">'),
    ('<h6 class="mt-3 mb-2" style="color: #0e7c8b; font-weight: 600;">',
     '<h6 class="mt-3 mb-2 lease-subhead">'),
    ('<span style="margin-left: 20px; font-size: 14px; color: #6c757d;">',
     '<span class="lease-title-note">'),
]

# LATER - the button classifier. Show-ButtonDrift.py tones a button
# outside a bar by the WRAPPER it sits in, and this round gives the Remove
# and Add Second Tenant buttons a new one: the section title itself. With
# no entry for it the classifier walked up to .modal-body, whose rule is
# "a button loose in a pop-up body is a Back", and proposed turning Remove
# into one. Two suites read that table - test_button_sweep and
# test_disabled_state - so the decision is recorded once, here.
DRIFT = 'Show-ButtonDrift.py'
# A WRAPPER CAN BE A HEADING. innermost_wrapper() read div, section, form,
# td and li, and found a wrapper's end by counting <div> - so a control
# inside a section TITLE had no wrapper of its own and inherited the
# pop-up body's. Both are one idea: read any element, and end it at its
# own closing tag.
DRIFT_WRAP_OLD = (
    "    best = None\n"
    "    for w in re.finditer(r'<(?:div|section|form|td|li)\\b[^>]*"
    "class=\"([^\"]*)\"[^>]*>',\n"
    "                         m):\n"
    "        a = w.start()\n"
    "        if a > pos:\n"
    "            break\n"
    "        depth, end = 0, None\n"
    "        for d in re.finditer(r'<div\\b|</div>', m[a:]):\n"
    "            if d.group(0) == '</div>':\n")
DRIFT_WRAP_NEW = (
    "    best = None\n"
    "    for w in re.finditer(r'<(div|section|form|td|li|h[1-6])\\b[^>]*"
    "class=\"([^\"]*)\"[^>]*>',\n"
    "                         m):\n"
    "        a = w.start()\n"
    "        if a > pos:\n"
    "            break\n"
    "        # ITS OWN TAG, not always a div - round C5, 23 Sep. A section\n"
    "        # title that carries a control is the wrapper of that control,\n"
    "        # and it ends at </h3>, not at the next </div>.\n"
    "        _tag = w.group(1)\n"
    "        depth, end = 0, None\n"
    "        for d in re.finditer(r'<%s\\b|</%s>' % (_tag, _tag), m[a:]):\n"
    "            if d.group(0) == '</%s>' % _tag:\n")
DRIFT_GRP_OLD = "        if end and a <= pos < end and (best is None or a > best[0]):\n            best = (a, w.group(1))\n"
DRIFT_GRP_NEW = "        if end and a <= pos < end and (best is None or a > best[0]):\n            best = (a, w.group(2))\n"
DRIFT_OLD = "    'd-flex':                  [('*', S)],\n"
DRIFT_NEW = ("    'd-flex':                  [('*', S)],\n"
             "    # A section title that carries its own control - round C5,\n"
             "    # 23 Sep. The control belongs to the section, not to the\n"
             "    # pop-up around it, so it is a secondary like the d-flex\n"
             "    # header it replaced.\n"
             "    'lease-title-row':         [('*', S)],\n")

report, problems = [], []
planned = {}
CRLF = {}


def read(p):
    with open(p, encoding='utf-8', newline='') as f:
        raw = f.read()
    CRLF[p] = '\r\n' in raw
    return raw.replace('\r\n', '\n')


def write(p, text):
    if CRLF.get(p):
        text = text.replace('\n', '\r\n')
    with open(p, 'w', encoding='utf-8', newline='') as f:
        f.write(text)


def controls(t):
    """Every form control, in order: the invariant a round that rewrites
       markup has to keep. A field that moved is a field that can be lost."""
    return re.findall(r'<(?:input|select|textarea)\b[^>]*?'
                      r'(?:name|id)="([^"]+)"', t)


def ids(t):
    return sorted(re.findall(r'\bid="([^"]+)"', t))


def transform(src):
    """The thirteen cards, rebuilt. A card is a <div class="card ..."> whose
       first child is a .card-header; the wizard's three keep a panel, the
       pop-up's ten keep only their title."""
    lines = src.split('\n')

    def close_of(i):
        depth = 0
        for j in range(i, len(lines)):
            depth += len(re.findall(r'<div\b', lines[j])) \
                - len(re.findall(r'</div>', lines[j]))
            if depth == 0:
                return j
        raise ValueError('unbalanced div from line %d' % (i + 1))

    def icon_for(txt):
        for k, v in ICONS:
            if k in txt:
                return v
        raise ValueError('no icon chosen for %r' % txt[:60])

    out, i, done, withctrl = [], 0, 0, 0
    while i < len(lines):
        line = lines[i]
        m = re.match(r'(\s*)<div class="card(["\s])', line)
        nxt = i + 1
        while nxt < len(lines) and not lines[nxt].strip():
            nxt += 1
        if not m or nxt >= len(lines) or 'card-header' not in lines[nxt]:
            out.append(line)
            i += 1
            continue
        ind = m.group(1)
        cend = close_of(i)
        hstart = nxt
        hend = close_of(hstart)
        bstart = hend + 1
        while bstart < len(lines) and not lines[bstart].strip():
            bstart += 1
        bm = re.match(r'\s*<div class="card-body"([^>]*)>', lines[bstart])
        if not bm:
            raise ValueError('card at line %d has no body' % (i + 1))
        bend = close_of(bstart)

        header = '\n'.join(lines[hstart + 1:hend])
        hm = re.search(r'<(h[456])[^>]*>(.*?)</\1>', header, re.S)
        if not hm:
            raise ValueError('card at line %d has no heading' % (i + 1))
        text = re.sub(r'^<i class="[^"]*"></i>\s*', '', hm.group(2).strip())
        icon = icon_for(re.sub('<[^>]+>', '', text))
        rest = header[:hm.start()] + header[hm.end():]
        ctrl = [c for c in re.findall(
            r'(<(?:button|span)\b.*?</(?:button|span)>)', rest, re.S)
            if 'class="d-flex' not in c]

        wizard = 'mb-4' in line
        tind = ind + '  ' if wizard else ind
        if ctrl:
            withctrl += 1
            raw = '\n'.join(ctrl).split('\n')
            base = min((len(x) - len(x.lstrip()) for x in raw[1:] if x.strip()),
                       default=0)
            body_ = '\n'.join((tind + '  ' + x[base:]) if x.strip() else x
                              for x in raw[1:])
            title = (tind + '<h3 class="form-section-title lease-title-row">\n'
                     + tind + '  <span><i class="fas %s"></i> %s</span>\n'
                     % (icon, text)
                     + tind + '  ' + raw[0].strip() + '\n'
                     + (body_ + '\n' if body_.strip() else '')
                     + tind + '</h3>')
        else:
            title = (tind + '<h3 class="form-section-title">'
                     '<i class="fas %s"></i> %s</h3>' % (icon, text))

        body = lines[bstart + 1:bend]
        cut = 2 if wizard else 4
        body = [(x[cut:] if x.startswith(' ' * cut) else x) for x in body]
        if wizard:
            out.append(line.replace('class="card mb-4"',
                                    'class="form-card mb-4"'))
            out.append(title)
            out += body
            out.append(lines[cend])
        else:
            bid = re.search(r'id="([^"]+)"', bm.group(1) or '')
            out.append(title)
            if bid:
                out.append(ind + '<div id="%s">' % bid.group(1))
                out += [('  ' + x if x.strip() else x) for x in body]
                out.append(ind + '</div>')
            else:
                out += body
        done += 1
        i = cend + 1
    return '\n'.join(out), done, withctrl


if not os.path.isfile(PAGE):
    problems.append('%s not found' % PAGE)
else:
    src = read(PAGE)
    if 'card-header' not in src:
        report.append('%-46s already done' % 'generate_lease_agreement.html')
        cur = src
    else:
        try:
            cur, done, withctrl = transform(src)
        except ValueError as e:
            problems.append('generate_lease_agreement.html: %s' % e)
            cur = src
            done = withctrl = 0
        if done:
            report.append('%-46s %d card(s) -> sections, %d with a control'
                          % ('generate_lease_agreement.html', done, withctrl))
    for old, new in SUBHEADS:
        if old in cur:
            report.append('%-46s %d inline style(s) -> a class'
                          % ('', cur.count(old)))  # noqa: E501
            cur = cur.replace(old, new)
    if CSS not in cur:
        if cur.count(CSS_ANCHOR) != 1:
            problems.append('generate_lease_agreement.html: cannot find the '
                            'CSS anchor')
        else:
            cur = cur.replace(CSS_ANCHOR, CSS + '\n' + CSS_ANCHOR, 1)
            report.append('%-46s + the three page rules' % '')
    if cur != src:
        planned[PAGE] = (src, cur)

    # --- self-checks, before a byte is written ---------------------------
    if PAGE in planned:
        t = planned[PAGE][1]
        if controls(t) != controls(src):
            problems.append('a form control moved or was lost')
        if ids(t) != ids(src):
            problems.append('an id moved or was lost')
        if t.count('{%') != src.count('{%') or t.count('{{') != src.count('{{'):
            problems.append('a Django tag changed')
        if re.findall(r'<div\b', t).__len__() - re.findall(r'</div>', t).__len__() \
                != re.findall(r'<div\b', src).__len__() \
                - re.findall(r'</div>', src).__len__():
            problems.append('the div balance moved')
        if 'card-header' in t or 'card-body' in t or 'bg-info' in t \
                or 'bg-warning' in t or 'bg-success' in t or 'bg-light' in t:
            problems.append('a card header or its colour survives')
        n = len(re.findall(r'<h3 class="form-section-title', t))
        if n != 13:
            problems.append('%d section titles, expected 13' % n)
        if len(re.findall(r'class="form-card mb-4"', t)) != 3:
            problems.append('the wizard does not have its three panels')
        for who in ('add-second-tenant-btn', 'remove-second-tenant-btn',
                    'fully-furnished-checkbox'):
            if who not in t:
                problems.append('%s was lost' % who)
        mk = re.sub(r'<style.*?</style>', '', t, flags=re.S)
        if len(re.findall(r'lease-title-row', mk)) != 3:
            problems.append('the three titles with a control are not three')
        if '#0e7c8b' in re.sub(r'<style.*?</style>', '', t, flags=re.S):
            problems.append('an inline teal survives outside the stylesheet')
        # ONE ICON ON THE TITLE - counted on the title's own words, not on
        # the control beside it. Add Second Tenant and Remove carry an icon
        # of their own, and always did.
        for tag in re.findall(r'<h3 class="form-section-title[^"]*">'
                              r'((?:(?!</h3>).)*)</h3>', t, re.S):
            words = re.match(r'\s*<span>(.*?)</span>', tag, re.S)
            words = words.group(1) if words else tag
            if words.count('<i class="fas') != 1:
                problems.append('a section title has %d icons: %r'
                                % (words.count('<i class="fas'), words[:60]))

# --- LATER: the classifier learns the new wrapper ------------------------
if not os.path.isfile(DRIFT):
    problems.append('%s not found' % DRIFT)
else:
    d = read(DRIFT)
    cur_d, dn = d, 0
    for old_, new_ in ((DRIFT_WRAP_OLD, DRIFT_WRAP_NEW),
                       (DRIFT_GRP_OLD, DRIFT_GRP_NEW),
                       (DRIFT_OLD, DRIFT_NEW)):
        if new_ in cur_d:
            continue
        if cur_d.count(old_) != 1:
            problems.append('%s: anchor found %d time(s): %r'
                            % (DRIFT, cur_d.count(old_), old_.strip()[:50]))
            continue
        cur_d = cur_d.replace(old_, new_, 1)
        dn += 1
    if not dn:
        report.append('%-46s already reads a heading as a wrapper' % DRIFT)
    else:
        try:
            compile(cur_d, DRIFT, 'exec')
        except SyntaxError as e:
            problems.append('%s would not compile: line %s' % (DRIFT, e.lineno))
        planned[DRIFT] = (d, cur_d)
        report.append('%-46s LATER: a heading is a wrapper, and '
                      '.lease-title-row is a secondary (%d)' % (DRIFT, dn))

# --- registered, and on the gate ----------------------------------------
if os.path.isfile(ROUNDS_FILE):
    r = read(ROUNDS_FILE)
    if "'%s'" % SUFFIX in r:
        report.append('%-46s already lists this round' % ROUNDS_FILE)
    elif r.count("    '.bak_quad',\n]") != 1:
        problems.append('%s: cannot find the end of ROUNDS (.bak_quad) - '
                        'apply_quadrant_tokens.py first' % ROUNDS_FILE)
    else:
        planned[ROUNDS_FILE] = (r, r.replace(
            "    '.bak_quad',\n]", "    '.bak_quad',\n    '%s',\n]" % SUFFIX,
            1))
        report.append('%-46s learns %s' % (ROUNDS_FILE, SUFFIX))
else:
    problems.append('%s missing' % ROUNDS_FILE)

GATE_NOTE = """    # Section C round C5: the lease generator's thirteen coloured card
    # headers are house sections - three panels and ten titles,
    'test_lease_sections.py'"""
if os.path.isfile(PS1):
    psrc = read(PS1)
    if "'%s'" % SUITE in psrc:
        report.append('%-46s already runs %s' % (PS1, SUITE))
    else:
        i = psrc.find('$suites = @(')
        m = re.search(r'\n\)\s*?\n', psrc[i:]) if i >= 0 else None
        if not m:
            problems.append('%s: could not find the end of $suites' % PS1)
        else:
            j = i + m.start()
            planned[PS1] = (psrc, psrc[:j] + ',\n' + GATE_NOTE + psrc[j:])
            report.append('%-46s + %s' % (PS1, SUITE))
else:
    problems.append('%s missing' % PS1)

print('\n' + '=' * 78)
print('SECTION C, ROUND C5 - THE LEASE GENERATOR - %s'
      % ('DRY RUN' if CHECK else 'APPLY'))
print('=' * 78)
for line in report:
    print('  ' + line)
print('')
if problems:
    print('!' * 78)
    print('%d PROBLEM(S). Nothing has been written.' % len(problems))
    print('!' * 78)
    for p in sorted(set(problems)):
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
        CRLF[bak] = CRLF.get(path)
        write(bak, src)
    write(path, text)
print('  %d file(s) written, backups at *%s' % (len(planned), SUFFIX))
print('')
print('  Next:  python %s' % SUITE)
