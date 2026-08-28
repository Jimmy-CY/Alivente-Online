#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""The Manage Expense modal joins the button standard - inside the JavaScript.

WHAT THIS IS. `Show-ButtonDrift.py` has been reporting the same thing for
weeks: "16 BUTTON(S) BUILT INSIDE <script> ... NOT rewritten. In a string
fragment there is often no wrapper to say whether a button is a page verb or a
row action, and a wrong guess edits working JavaScript. These are decided by
hand." Twelve of the sixteen are on this page, and this is the hand deciding
them.

ELEVEN BUTTONS ACROSS SIX BOOTSTRAP COLOURS. Green meant "add", green also
meant "save", green also meant "upload"; amber meant "replace"; blue meant
"take a photo" and a different blue meant "upload a document". Green as "do the
safe thing" and amber as "do the other one" is not a scale used anywhere else
in this system.

DECIDED 28 Aug:

  * THE INVOICE DOCUMENT TAB HAS NO PRIMARY. Add to Existing, Replace and
    Delete Document are ALTERNATIVES, not a recommended path with two escape
    hatches, and a solid button says "this is what you came here to do". All
    three are outlined; Delete carries the danger TONE, which is what makes it
    read as destructive - not a red fill.
  * A SUB-PANEL'S CONFIRM IS ITS PRIMARY. Merge Documents, Upload and Upload
    Document each complete a panel that is the only thing on screen when it is
    open, so each is the primary of that panel. Their Cancels are outlined.
  * SAVE CHANGES is the primary of the Expense Details tab, which is exactly
    what a primary is for.

AND THE BANNER. base has no alert or note component at all, so the verify
banner stays page-local - but on house tokens rather than Bootstrap's alert
palette. `.exp-note` in five tones replaces `alert alert-*` for the verify
banner and the two read-only notices, and the four `.verify-icon` colours in
the grid move off their Bootstrap hexes.

WHY THE BUTTONS ARE REWRITTEN BY (CLASS, LABEL) AND NOT BY EXACT STRING. Three
buttons share the class list `btn btn-success btn-sm` and two share
`btn btn-secondary btn-sm`; the label is the only thing that tells them apart.
Every rewrite below is asserted against an expected table, so a button that
moves, changes label, or appears from nowhere stops this patcher rather than
being guessed at.

Run from the repo root.  --check plans without writing.
"""
import os, re, sys, shutil

ROOT   = os.path.dirname(os.path.abspath(__file__))
TPL    = os.path.join(ROOT, 'pages', 'templates')
PAGE   = os.path.join(TPL, 'act_expense.html')
BASE   = os.path.join(TPL, 'base.html')
CHECK  = '--check' in sys.argv
SUFFIX = '.bak_managemodal'

# (class list, label) -> new class list.  The label disambiguates the three
# btn-success buttons and the two Cancels.
BUTTONS = {
    ('btn btn-primary btn-sm', 'Take Photo'):            'btn action-secondary btn-sm',
    ('btn btn-outline-secondary btn-sm', 'Choose File'): 'btn action-secondary btn-sm',
    ('btn btn-success', 'Save Changes'):                 'btn action-primary',
    ('btn btn-success btn-sm', 'Add to Existing'):       'btn action-secondary btn-sm',
    ('btn btn-warning btn-sm', 'Replace'):               'btn action-secondary btn-sm',
    ('btn btn-danger btn-sm', 'Delete Document'):        'btn action-danger btn-sm',
    ('btn btn-success btn-sm', 'Merge Documents'):       'btn action-primary btn-sm',
    ('btn btn-secondary btn-sm', 'Cancel'):              'btn action-secondary btn-sm',
    ('btn btn-success btn-sm', 'Upload'):                'btn action-primary btn-sm',
    ('btn btn-info', 'Upload Document'):                 'btn action-primary',
    # A LINK, not a button: Download is a GET that fetches a file, which is
    # exactly what an anchor is for. It is still a control on that tab, and it
    # is the twelfth - the one the first version of this patcher missed by
    # matching only <button>, which is also why Show-ButtonDrift always said
    # twelve where the button scan said eleven.
    ('btn btn-info btn-sm', 'Download'):                 'btn action-secondary btn-sm',
}
EXPECTED = 12          # two Cancels share one entry

NOTE_CSS = """
/* ------------------------------------------------------------------
   A quiet explanatory strip. base has no alert or note component, so
   this stays page-local - but on the house tokens, not Bootstrap's
   alert palette. Five tones, matching the five verification states.
   ------------------------------------------------------------------ */
.exp-note {
    border: 1px solid var(--alv-line);
    border-radius: var(--alv-radius-sm);
    padding: 10px 12px;
    margin-bottom: 12px;
    color: var(--alv-ink);
}
/* Tint only. base's pill variants pair each tint with a hand-picked border
   literal; there is no token for those, and three more hexes to keep in step
   is a worse trade than one neutral hairline under every tone. */
.exp-note-success   { background: var(--alv-good-soft); }
.exp-note-danger    { background: var(--alv-bad-soft); }
.exp-note-warning   { background: var(--alv-warn-soft); }
.exp-note-secondary { background: var(--alv-neutral-soft); }
.exp-note-info      { background: var(--alv-info-soft); border-color: var(--alv-accent-line); }
.exp-note-success .verify-banner-head   { color: var(--alv-good); }
.exp-note-danger .verify-banner-head    { color: var(--alv-bad); }
.exp-note-warning .verify-banner-head   { color: var(--alv-warn); }
.exp-note-secondary .verify-banner-head { color: var(--alv-neutral); }
.exp-note-info .verify-banner-head      { color: var(--alv-accent-ink); }
"""

ICONS = {
    '.verify-icon.verify-success   { color: #28a745; }':
        '.verify-icon.verify-success   { color: var(--alv-good); }',
    '.verify-icon.verify-danger    { color: #dc3545; }':
        '.verify-icon.verify-danger    { color: var(--alv-bad); }',
    '.verify-icon.verify-secondary { color: #6c757d; }':
        '.verify-icon.verify-secondary { color: var(--alv-neutral); }',
    '.verify-icon.verify-info      { color: #0e7c8b; }':
        '.verify-icon.verify-info      { color: var(--alv-accent); }',
}


def read(p):
    with open(p, encoding='utf-8') as f:
        return f.read()


def nocomment(text):
    """Comments out, before anything is counted or searched.

    Sixth and seventh instances of this in three rounds. Strip first.
    """
    text = re.sub(r'<!--.*?-->', '', text, flags=re.S)
    text = re.sub(r'\{#.*?#\}', '', text, flags=re.S)
    return re.sub(r'(<script[^>]*>)(.*?)(</script>)',
                  lambda m: m.group(1) + '\n'.join(
                      '' if l.lstrip().startswith('//') else l
                      for l in re.sub(r'/\*.*?\*/', '', m.group(2),
                                      flags=re.S).split('\n')) + m.group(3),
                  text, flags=re.S)


def scripts_span(text):
    return [(m.start(1), m.end(1)) for m in
            re.finditer(r'<script[^>]*>(.*?)</script>', text, re.S)]


def rewrite_buttons(text):
    """Rewrite only inside <script>, and only the (class, label) pairs known."""
    seen, unknown = [], []

    def one(m):
        cls, inner = m.group(1), m.group(2)
        label = ' '.join(re.sub(r'<[^>]+>', '', inner).split())
        # ${...} in a label would mean the text is computed; do not guess.
        key = (cls, label)
        if '${' in label:
            unknown.append((cls, label))
            return m.group(0)
        if key not in BUTTONS:
            unknown.append(key)
            return m.group(0)
        seen.append(key)
        return m.group(0).replace('class="%s"' % cls, 'class="%s"' % BUTTONS[key], 1)

    out, last = [], 0
    for a, z in scripts_span(text):
        out.append(text[last:a])
        seg = text[a:z]
        seg = re.sub(r'<button[^>]*class="(btn[^"]*)"[^>]*>(.*?)</button>',
                     one, seg, flags=re.S)
        # And anchors wearing a .btn class - a control is a control whichever
        # element draws it.
        seg = re.sub(r'<a\b[^>]*class="(btn[^"]*)"[^>]*>(.*?)</a>',
                     one, seg, flags=re.S)
        out.append(seg)
        last = z
    out.append(text[last:])
    return ''.join(out), seen, unknown


def main():
    src, bsrc = read(PAGE), read(BASE)

    if 'exp-note-success' in src:
        print('  manage modal               already migrated')
        print('\n  0 file(s) changed')
        return

    out, seen, unknown = rewrite_buttons(src)

    # ---- the notes: the verify banner and the two read-only notices
    out = out.replace('class="alert alert-${s[0]} verify-banner"',
                      'class="exp-note exp-note-${s[0]} verify-banner"', 1)
    n_alerts = len(re.findall(r'class="alert alert-(info|warning)"', out))
    out = re.sub(r'class="alert alert-(info|warning)"',
                 r'class="exp-note exp-note-\1"', out)

    for old, new in ICONS.items():
        if old not in out:
            sys.exit('! the verify icon rule was not found as expected:\n    %s' % old)
        out = out.replace(old, new, 1)

    j = out.find('</style>')
    if j < 0:
        sys.exit('! no </style> to append to')
    out = out[:j] + NOTE_CSS + out[j:]

    # ---- self-check BEFORE anything is written
    bad = []
    if len(seen) != EXPECTED:
        bad.append('rewrote %d button(s), expected %d' % (len(seen), EXPECTED))
    if unknown:
        bad.append('a script button did not match the expected table, so it '
                   'was LEFT ALONE rather than guessed at: %s' % unknown[:3])
    _code = nocomment(out)
    _js = '\n'.join(_code[a:z] for a, z in scripts_span(_code))
    for gone in ('btn-success', 'btn-warning', 'btn-danger', 'btn-info',
                 'btn-primary', 'btn-secondary', 'btn-outline-secondary'):
        if gone in _js:
            bad.append('%s survives in a script' % gone)
    if 'alert alert-' in _js:
        bad.append('a Bootstrap alert survives in a script')
    if n_alerts != 3:
        bad.append('expected 3 read-only notices, found %d' % n_alerts)
    for want in ('exp-note exp-note-${s[0]}', 'action-danger btn-sm',
                 'action-primary', 'action-secondary'):
        if want not in out:
            bad.append('expected and missing: %s' % want)
    # base must own every tone the notes lean on.
    for token in ('--alv-good-soft', '--alv-bad-soft', '--alv-warn-soft',
                  '--alv-neutral-soft', '--alv-info-soft', '--alv-radius-sm',
                  '--alv-accent-line'):
        if token not in bsrc:
            bad.append('base.html does not define %s' % token)
    for tone in ('action-primary', 'action-secondary', 'action-danger'):
        if '.btn.%s' % tone not in bsrc and '.%s' % tone not in bsrc:
            bad.append('base.html does not define .%s' % tone)
    if len(re.findall(r'<button\b', _code)) != len(re.findall(r'</button\s*>', _code)):
        bad.append('button tags do not balance')
    css = '\n'.join(re.findall(r'<style[^>]*>(.*?)</style>', out, re.S))
    if css.count('{') != css.count('}'):
        bad.append('CSS braces do not balance')
    for blk in re.findall(r'<script[^>]*>(.*?)</script>', nocomment(out), re.S):
        if blk.count('{') != blk.count('}'):
            bad.append('a script block no longer balances its braces')
            break
    if bad:
        sys.exit('! manage modal self-check FAILED, nothing written:\n   - %s'
                 % '\n   - '.join(bad))

    print('  act_expense.html            %d script button(s) on the house tones'
          % len(seen))
    print('     no primary on the Invoice Document tab - they are alternatives')
    print('  act_expense.html            %d Bootstrap alert(s) -> .exp-note, '
          'and 4 verify icons off their hexes' % (n_alerts + 1))

    if not CHECK:
        b = PAGE + SUFFIX
        if not os.path.exists(b):
            shutil.copy2(PAGE, b)
        with open(PAGE, 'w', encoding='utf-8') as f:
            f.write(out)

    print('\n  1 file(s) %s' % ('would change' if CHECK else 'changed'))


if __name__ == '__main__':
    main()
