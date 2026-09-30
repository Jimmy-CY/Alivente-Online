# -*- coding: utf-8 -*-
"""SECTION D, ROUND D3 - A SMALL ADD BUTTON WELDED TO A FIELD

Demetri, on the Add New Asset panel: "Why are these + buttons in green.
They should be in teal."

He is right, and the interesting part is WHY they were green.

    <div class="input-group-append">
      <button class="btn btn-outline-success"><i class="fas fa-plus"></i>

Three of them on property_assets.html - add a category, add a
subcategory, add a supplier - and raw Bootstrap green on all three, with
not one line of CSS on the page. They are green because nothing ever
decided they should be anything else.

THIS ROUND OVERTURNS A WRITTEN DECISION, and says so. Show-ButtonDrift
lists `input-group-append` under LEAVE - "welded to an input; Bootstrap
owns the geometry" - which is why the drift report has been saying
"nothing drifting" over three green buttons for weeks. That entry was a
fair call when the alternative was hand-styling each one; it is not a
fair call now, because the answer is a NAME, and base is where names
live. Demetri asked for teal on 30 Sep.

    .action-field-add - a small add control welded to a field.

BOOTSTRAP KEEPS THE GEOMETRY, which is what the LEAVE note was really
protecting: `btn` stays on the element and `input-group-append` still
sets the height against the select beside it. Only the COLOUR moves, from
Bootstrap's green to the house accent, and a hover that fills rather than
tints - the same move .btn.action-secondary already makes.

WHY A BASE CLASS AND NOT THREE PAGE RULES. Because there will be a
fourth. A page that grows an inline add button next to a field reaches
for btn-outline-success, and today there is nothing else for it to
reach for. Now there is.

THE DRIFT TOOL IS TOLD. Its LEAVE entry keeps covering the seven other
welded buttons and its note now says why these three left - a tool that
reports a decision must report the decision that was actually made.

Backups: .bak_fieldadd. Idempotent. --check writes nothing.
"""
import os
import re
import sys

import alv_tree

CHECK = '--check' in sys.argv
SUFFIX = '.bak_fieldadd'
CRLF = {}

BASE = 'base.html'
PAGE = 'property_assets.html'
DRIFT = 'Show-ButtonDrift.py'


def read(path):
    with open(path, 'rb') as fh:
        raw = fh.read()
    CRLF[path] = b'\r\n' in raw
    return raw.decode('utf-8'), raw


def write(path, text):
    data = text.encode('utf-8')
    if CRLF.get(path):
        data = data.replace(b'\r\n', b'\n').replace(b'\n', b'\r\n')
    else:
        data = data.replace(b'\r\n', b'\n')
    with open(path, 'wb') as fh:
        fh.write(data)


def eol(path, s):
    return (s.replace('\r\n', '\n').replace('\n', '\r\n')
            if CRLF.get(path) else s.replace('\r\n', '\n'))


def back_up(path, original_bytes):
    bak = path + SUFFIX
    if os.path.exists(bak):
        return
    with open(bak, 'wb') as fh:
        fh.write(original_bytes)
    with open(bak, 'rb') as fh:
        if fh.read() != original_bytes:
            raise SystemExit('D3: %s is not a byte copy' % bak)


# ==========================================================================
# THE ANCHOR IS INDENTED AND MULTI-LINE. The first version of this
# round copied the rule as one line from a CSS dump and found it zero
# times - a dump is not the file.
B_WAS = """      .btn.action-secondary {
        background: var(--alv-paper);
        border: 1px solid var(--alv-line);
        color: var(--alv-ink);
      }"""
B_NOW = """      .btn.action-secondary {
        background: var(--alv-paper);
        border: 1px solid var(--alv-line);
        color: var(--alv-ink);
      }
      /* A SMALL ADD CONTROL WELDED TO A FIELD - 30 Sep 2026. Demetri, on the
         Add New Asset panel: why are these + buttons in green, they
         should be in teal. Three of them on property_assets - add a
         category, a subcategory, a supplier - all raw
         btn-outline-success, with not one line of CSS on the page. They
         were green because nothing had ever decided otherwise, and
         Show-ButtonDrift had them under LEAVE as welded to an input, so
         the report said nothing drifting over three green buttons.

         BOOTSTRAP KEEPS THE GEOMETRY. `btn` stays on the element and
         input-group-append still matches the height of the field beside
         it - that is what the LEAVE note was really protecting. Only
         the colour moves, and the hover fills rather than tints, which
         is the move .btn.action-secondary above already makes.

         A NAME, because there will be a fourth: a page that grows an
         inline add button reaches for btn-outline-success today because
         there is nothing else to reach for.   [test_field_add.py] */
      .btn.action-field-add {
        background: var(--alv-paper);
        border: 1px solid var(--alv-accent);
        color: var(--alv-accent);
      }
      .btn.action-field-add:hover,
      .btn.action-field-add:focus {
        background: var(--alv-accent);
        border-color: var(--alv-accent);
        color: var(--alv-paper);
      }"""

P_WAS = """class="btn btn-outline-success\""""
P_NOW = """class="btn action-field-add\""""

D_WAS = """    'input-group-append': 'welded to an input; Bootstrap owns the geometry',"""
D_NOW = """    # 30 Sep 2026: this still covers the buttons welded to an input
    # whose GEOMETRY is Bootstrap's, which is what the note meant. It
    # no longer covers their COLOUR. property_assets carried three
    # btn-outline-success + buttons under this entry, and the report
    # said "nothing drifting" over them for weeks - Demetri saw the
    # green. base now has .action-field-add and they wear it, so they
    # are not in this count any more. See test_field_add.py.
    'input-group-append': 'welded to an input; Bootstrap owns the geometry',"""

# ==========================================================================
print('=' * 74)
print('SECTION D, ROUND D3 - A SMALL ADD BUTTON WELDED TO A FIELD%s'
      % (' - CHECK ONLY' if CHECK else ''))
print('=' * 74)

# ---- base ---------------------------------------------------------------
p = alv_tree.path_of(BASE)
t, raw = read(p)
print('  %s' % BASE)
if 'action-field-add' in t:
    print('     already names the control')
else:
    a = eol(p, B_WAS)
    if t.count(a) != 1:
        raise SystemExit('D3: base - the action-secondary anchor is there '
                         '%d time(s), not 1' % t.count(a))
    t = t.replace(a, eol(p, B_NOW), 1)
    print('     .action-field-add - the accent, and a hover that fills')

    css = re.sub(r'/\*.*?\*/', ' ', '\n'.join(
        re.findall(r'<style\b[^>]*>(.*?)</style>', t, re.S)), flags=re.S)
    sels = {}
    for m in re.finditer(r'([^{}]+)\{([^}]*)\}', css):
        k = ' '.join(m.group(1).split())
        sels[k] = sels.get(k, 0) + 1
    for sel, n in (('.btn.action-field-add', 1),
                   ('.btn.action-field-add:hover, .btn.action-field-add:focus',
                    1)):
        if sels.get(sel, 0) != n:
            raise SystemExit('D3: base declares %s %d time(s), not %d'
                             % (sel, sels.get(sel, 0), n))
    body = re.search(r'\.btn\.action-field-add\s*\{([^}]*)\}', css).group(1)
    if 'var(--alv-accent)' not in body:
        raise SystemExit('D3: the rule does not use the accent token')
    if re.search(r'#[0-9a-fA-F]{3,8}\b', body):
        raise SystemExit('D3: the rule carries a literal colour: %s'
                         % ' '.join(body.split()))
    # IT MUST NOT SET GEOMETRY. Bootstrap owns that here, which is the
    # whole reason this button was left alone in the first place.
    for banned in ('width', 'height', 'padding', 'display', 'min-width'):
        if re.search(r'\b' + banned + r'\s*:', body):
            raise SystemExit('D3: the rule sets %s - Bootstrap owns the '
                             'geometry of a welded button' % banned)
    if not CHECK:
        back_up(p, raw)
        write(p, t)

# ---- the page -----------------------------------------------------------
q = alv_tree.path_of(PAGE)
t2, raw2 = read(q)
print('  %s' % PAGE)
if 'action-field-add' in t2:
    print('     the three already wear it')
else:
    a2 = eol(q, P_WAS)
    n = t2.count(a2)
    if n != 3:
        raise SystemExit('D3: %s carries the green class %d time(s), not 3'
                         % (PAGE, n))
    t2 = t2.replace(a2, eol(q, P_NOW), 3)
    print('     three + buttons take the accent')

    mk = re.sub(r'<(script|style)\b.*?</\1>', '',
                re.sub(r'<!--.*?-->', '', t2, flags=re.S), flags=re.S)
    if 'btn-outline-success' in mk:
        raise SystemExit('D3: a green one survived')
    if mk.count('action-field-add') != 3:
        raise SystemExit('D3: %d wear the new name, not 3'
                         % mk.count('action-field-add'))
    # STILL WELDED, AND STILL A BUTTON. Dropping `btn` would take the
    # geometry with it; leaving the wrapper is what keeps the height.
    for m in re.finditer(r'<button[^>]*action-field-add[^>]*>', mk):
        if 'class="btn action-field-add"' not in m.group(0):
            raise SystemExit('D3: a + button lost the btn class: %s'
                             % m.group(0)[:80])
    if mk.count('input-group-append') < 3:
        raise SystemExit('D3: the wrapper that sets the height is gone')
    # AND THE PAGE STILL WRITES NO RULE FOR THEM.
    css2 = re.sub(r'/\*.*?\*/', ' ', '\n'.join(
        re.findall(r'<style\b[^>]*>(.*?)</style>', t2, re.S)), flags=re.S)
    if re.search(r'\.action-field-add\b[^{}]*\{', css2):
        raise SystemExit('D3: the page writes a rule base already owns')
    if not CHECK:
        back_up(q, raw2)
        write(q, t2)

# ---- the drift tool -----------------------------------------------------
d = os.path.join(os.getcwd(), DRIFT)
if not os.path.isfile(d):
    raise SystemExit('D3: %s is not on disk' % DRIFT)
t3, raw3 = read(d)
print('  %s' % DRIFT)
if 'Demetri saw the' in t3:
    print('     already records why the three left')
else:
    a3 = eol(d, D_WAS)
    if t3.count(a3) != 1:
        raise SystemExit('D3: the LEAVE entry is there %d time(s), not 1'
                         % t3.count(a3))
    t3 = t3.replace(a3, eol(d, D_NOW), 1)
    print('     its LEAVE note says why three of them left the count')
    import ast
    try:
        ast.parse(t3)
    except SyntaxError as e:
        raise SystemExit('D3: %s no longer parses: %s' % (DRIFT, e))
    # THE ENTRY ITSELF SURVIVES - seven welded buttons still rely on it.
    if "'input-group-append':" not in re.sub(r'#.*', '', t3):
        raise SystemExit('D3: the LEAVE entry was removed, not annotated')
    if not CHECK:
        back_up(d, raw3)
        write(d, t3)

print('-' * 74)
print('  one name in base, three buttons in teal, and a tool that no')
print('  longer reports a decision nobody would defend.')
if CHECK:
    print('  CHECK ONLY - nothing written')
print('=' * 74)
