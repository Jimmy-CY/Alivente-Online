"""Show-ButtonDrift - which pages still disagree with base.html about buttons.

    python Show-ButtonDrift.py
    python Show-ButtonDrift.py --full tenant.html
    python Show-ButtonDrift.py --wrappers      (bar NAMES, not buttons)
    python Show-ButtonDrift.py --patterns      (how many distinct edits)
    python Show-ButtonDrift.py --clean         (also list the ones that agree)
    python Show-ButtonDrift.py --strict        (exit 1 while drift remains)
    python Show-ButtonDrift.py --recipes       (recipe/meal-plan side too)

READ ONLY. Writes nothing, changes nothing.

WHY THIS EXISTS
---------------
There are two kinds of change to base.html, and they behave completely
differently:

  OPT-IN NAMES - .alv-table, .alv-card, .alv-pill, .alv-tag, and (this is
      the sting) .page-action-buttons. A page gets these only if its markup
      ADDS the class. An un-migrated page is untouched.

  HOISTED NAMES - .action-primary, .action-secondary, .action-back,
      .back-button, .disabled-btn. Every page ALREADY carries these names;
      that is what made them worth hoisting. The moment base.html defines
      them, base reaches all of those pages, migrated or not.

For a hoisted name there is no such thing as an un-migrated page - only a
page whose MARKUP has not caught up.

WHAT V1 GOT WRONG, AND HOW
--------------------------
V1 looked for buttons in three places: a `.page-action-buttons` div, a
`.modal-footer`, and Back links. It reported 158 drifting buttons on the
property side and I nearly shipped `--strict` on the strength of it.

The real figure is 233. V1 missed 75 because THE BAR IS NOT ALWAYS CALLED
`page-action-buttons`. There are fifteen names for it:

    action-bar 20   page-action-buttons 19   form-action-buttons 5
    action-buttons-wrap 4   page-action-bar(+ -inner) 3
    expense- / admin- / pl- / invoices- / notification-action-buttons

A guard that cannot see two thirds of the bars is worse than no guard,
because zero drift reads as "done".

So v2 finds a bar by what it CONTAINS, not what it is called. That matters
in both directions: `categories_management.html` has a
`<div class="action-buttons">` that is the per-row edit/delete cluster in a
table, not a page bar at all. Name-matching would have swept it.
"""

import collections
import os
import re
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
TPL = os.path.join(ROOT, 'pages', 'templates')

# ---------------------------------------------------------------------------
# vocabulary
# ---------------------------------------------------------------------------

BOOTSTRAP = ('btn-info', 'btn-primary', 'btn-secondary', 'btn-success',
             'btn-warning', 'btn-danger', 'btn-light', 'btn-dark',
             # The outline variants are Bootstrap colour too. Leaving them
             # off the list did not make them out of scope, it made them
             # INVISIBLE - a filter chip and a bar button look identical to
             # a scanner that cannot see either.
             'btn-outline-secondary', 'btn-outline-primary',
             'btn-outline-info', 'btn-outline-danger',
             'btn-outline-success', 'btn-outline-warning')

# Tones set COLOUR. Exactly one .action-primary belongs on a bar.
TONES = ('action-primary', 'action-secondary', 'action-danger',
         'action-back', 'back-button')

# Position/layout classes base.html owns. Not tones; they must survive the
# swap. .action-more-btn is styled by base directly and takes no tone.
POSITION = ('action-add-new', 'action-more-btn', 'action-more-item',
            'ui-menu-toggle', 'disabled-btn')

# Names that MEAN a house class but are spelt wrong. Two pages copied
# `action-btn-back` from somewhere; nothing defines it in base.
MISNAMED = {'action-btn-back': 'action-back'}

HOUSE = TONES + POSITION + tuple(MISNAMED)

# Wrapper names used for BOTH a page bar and a per-row cluster inside a
# table. For these, holding a house class is the only proof it is a bar.
AMBIGUOUS_BAR = ('action-buttons',)

# Wrapper names seen in this codebase. Being on this list makes a div a
# CANDIDATE; it is only treated as a bar if it actually holds page verbs.
BAR_NAMES = ('page-action-buttons', 'action-bar', 'form-action-buttons',
             'action-buttons-wrap', 'page-action-bar', 'page-action-bar-inner',
             'action-buttons', 'expense-action-buttons', 'admin-action-buttons',
             'pl-action-bar', 'invoices-action-buttons',
             'notification-action-buttons',
             # Found in round two, by walking the directories v2 never opened
             # and by looking at what the LOOSE buttons actually sat in. Each
             # is the same component under another name.
             'form-footer-actions', 'form-action-row', 'form-actions',
             'desktop-wizard-controls', 'action-row')

STANDARD_BAR = 'page-action-buttons'

# ---------------------------------------------------------------------------
# Buttons that are NOT in a bar, and never will be
# ---------------------------------------------------------------------------
# A button in one of these wrappers is deliberately out of scope: row actions,
# filter chrome, segmented toggles, input add-ons. base.html does not own them
# and this round does not touch them. Listed by name so `--strict` can tell
# "decided to leave" apart from "nobody has looked at this yet" - which is the
# distinction v2 lacked, and why it reported zero over 199 buttons.
LEAVE = {
    'filter-header': 'filter panel chrome',
    'passport-filter-header': 'filter panel chrome',
    'filter-header-right': 'filter panel chrome',
    'pdf-viewer-controls': "the PDF viewer's own icon toolbar",
    'input-group-append': 'welded to an input; Bootstrap owns the geometry',
    'btn-group': 'row actions',
    'subtask-actions': 'row actions',
    'project-status-container': 'row actions',
    'zoom-controls': 'a zoom widget',
    'fi-trend-controls': 'segmented toggle - colour is state',
    'pd-toolbar': 'segmented toggle - colour is state',
    'selection-buttons': 'segmented toggle - colour is state',
}

# Buttons outside any bar whose tone was decided one at a time, from rendered
# before/after pictures. wrapper -> [(label fragment, tone)]; '*' matches all.
# Order matters: the first matching fragment wins.
S, P, B = 'action-secondary', 'action-primary', 'action-back'
DANGER = 'action-secondary action-danger'
DECIDED = {
    'col-md-6':                [('login', P)],
    'col-12':                  [('generate lease', P)],
    'lease-document-actions':  [('*', P)],
    'title-deed-actions':      [('not available', S + ' disabled-btn'),
                                ('view', P)],
    'title-deed-toolbar':      [('download', P), ('*', S)],
    'comment-right-col':       [('*', P)],
    'pdf-viewer-error':        [('*', P)],
    'notification-card':       [('save', P)],
    'timeline-controls-group': [('*', S)],
    'timeline-controls-secondary': [('*', B)],
    'alert':                   [('*', S)],
    'map-controls':            [('*', S)],
    'translation-buttons':     [('*', S)],
    'document-launcher-card':  [('*', S)],
    'page-header-actions':     [('*', S)],
    'expenses-actions':        [('*', S)],
    'revenue-actions':         [('*', S)],
    'tasks-section-header':    [('*', S)],
    'task-title-section':      [('*', S)],
    'numbering-controls':      [('*', S)],
    'header-actions':          [('*', S)],
    'd-flex':                  [('*', S)],
    'detail-row':              [('*', S)],
    'add-line-wrap':           [('*', S)],
    'modal-body':              [('*', B)],
    'dashboard-side-actions':  [('*', B)],
    'text-center':             [('cancel', S), ('delete', DANGER), ('*', S)],
    'select-all-bar':          [('*', DANGER)],
    # Retoned but NOT renamed: connectivity_error's pair is centred, and
    # passport_management already has a real bar of its own. Giving either
    # the bar layout would move buttons that are fine where they are.
    'button-group':            [('go back', B), ('*', P)],
    'add-new-button-row':      [('*', P)],
    'page-header':             [('back', B)],
    'desktop-only-content':    [('back', B)],
    'rotate-prompt-content':   [('*', B)],
}

# Modal-footer vocabulary. Replaces the verb whitelist v1 used, which
# mis-called five confirms (Upload Document, Upload Lease Agreement,
# Upload Title Deed, Download, Go to Expenses) as secondary.
CANCELS = ('cancel', 'close', 'dismiss', 'not now', 'never mind')
DESTRUCTIVE = ('delete', 'remove', 'permanently', 'discard', 'revoke')


def read(p):
    return open(p, encoding='utf-8-sig', errors='replace').read().replace(
        '\r\n', '\n')


def markup_of(t):
    """The template with <style> and <script> removed.

    A class name inside a CSS rule is not a button.

    LENGTH IS PRESERVED. Each stripped block becomes the same number of
    spaces (newlines kept, so line numbers still line up). A patcher rewrites
    buttons at the offsets this function reports, and collapsing a 30 KB
    <style> block to one space would shift every later offset by 30 KB -
    silently, into the middle of unrelated markup.
    """
    def blank(m):
        return re.sub(r'[^\n]', ' ', m.group(0))
    t = re.sub(r'<style[^>]*>.*?</style>', blank, t, flags=re.S | re.I)
    return re.sub(r'<script[^>]*>.*?</script>', blank, t, flags=re.S | re.I)


def spans(text, opening_re):
    """(start, end) of each element matching opening_re, counting nesting.

    A non-greedy `<div class="x">.*?</div>` stops at the first INNER </div>,
    which on this project truncated an action bar before its Back link and
    reported it missing. Count, do not guess.
    """
    out = []
    for m in re.finditer(opening_re, text):
        depth, end = 0, m.start()
        for d in re.finditer(r'<div\b|</div>', text[m.start():]):
            if d.group(0) == '</div>':
                depth -= 1
                if depth == 0:
                    end = m.start() + d.end()
                    break
            else:
                depth += 1
        out.append((m.start(), end))
    return out


# Matches a button-shaped element by its CLASS LIST, which must name either
# Bootstrap's .btn or one of base.html's own button classes.
#
# Requiring `.btn` (as v1 did) missed finance_valuations_add.html entirely:
# its bar holds `class="action-primary"` and `class="action-back"` with no
# `.btn` at all. Those match base's UNPAIRED selector `.action-primary`
# (0,1,0) rather than the paired `.btn.action-primary` (0,2,0) - and that
# page defines its own `.action-primary`, later in the document. So base
# loses, silently, on exactly the pages that look most converted.
BTN = re.compile(r'<(a|button|span)\b[^>]*class="([^"]*(?:\bbtn\b|\baction-'
                 r'(?:primary|secondary|danger|back|add-new|btn-back)\b|'
                 r'\bback-button\b)[^"]*)"[^>]*>(.*?)</\1>', re.S)


def label_of(inner):
    lab = ' '.join(re.sub(r'<[^>]+>', ' ', inner).split())
    lab = re.sub(r'\{[{%][^}%]*[%}]\}', '', lab).strip()
    return lab or '(icon only)'


def wrapper_name(cls):
    for n in cls.split():
        if n in BAR_NAMES:
            return n
    return None


def bars(m):
    """Confirmed page-action bars: (name, start, end).

    A candidate wrapper is confirmed only if it DIRECTLY holds a button
    carrying a house class. That rejects categories_management.html's
    per-row `.action-buttons` cluster, whose buttons are `.action-btn
    .btn-edit` - table chrome, not page verbs.

    Nested candidates (fsr.html's page-action-bar > page-action-bar-inner)
    both confirm; the INNERMOST is the real bar, so the outer is dropped.
    """
    found = []
    for a, z in spans(m, r'<div[^>]*class="([^"]*)"[^>]*>'):
        head = re.match(r'<div[^>]*class="([^"]*)"', m[a:z])
        name = wrapper_name(head.group(1)) if head else None
        if not name:
            continue
        classes = [c for b in BTN.finditer(m[a:z]) for c in b.group(2).split()]
        holds_house = any(c in HOUSE for c in classes)
        # An unambiguous wrapper name plus any real button is enough. That
        # rescues fsr_details.html, whose bar holds two plain `btn btn-info`
        # buttons and had never been given a tone at all.
        holds_btn = 'btn' in classes and name not in AMBIGUOUS_BAR
        if holds_house or holds_btn:
            found.append((name, a, z))
    # drop any bar that fully contains another confirmed bar
    inner = [f for f in found
             if not any(g is not f and f[1] <= g[1] and g[2] <= f[2]
                        for g in found)]
    return inner


def rejected_wrappers(m):
    """Candidates that did NOT confirm - reported, never silently dropped."""
    out = []
    for a, z in spans(m, r'<div[^>]*class="([^"]*)"[^>]*>'):
        head = re.match(r'<div[^>]*class="([^"]*)"', m[a:z])
        name = wrapper_name(head.group(1)) if head else None
        if not name:
            continue
        classes = [c for b in BTN.finditer(m[a:z]) for c in b.group(2).split()]
        if not (any(c in HOUSE for c in classes)
                or ('btn' in classes and name not in AMBIGUOUS_BAR)):
            out.append(name)
    return out


def footers(m):
    return [('modal footer', a, z)
            for a, z in spans(m, r'<div[^>]*class="[^"]*modal-footer[^"]*"'
                                 r'[^>]*>')]


def is_cancel(lab):
    low = lab.lower().strip().rstrip('.!')
    return any(low == c or low.startswith(c + ' ') for c in CANCELS)


def is_destructive(lab):
    return any(d in lab.lower() for d in DESTRUCTIVE)


def is_disabled(open_tag, cls):
    """Every shape of 'this button is switched off' used in this codebase.

    Three of them, found by counting rather than assuming: a <span> with an
    inline opacity/pointer-events style (13), a class of .disabled-btn (3),
    and a <button disabled> with an inline style (1). Miss one and it ships
    as a solid teal button that looks clickable.
    """
    if 'disabled-btn' in cls.split():
        return True
    if re.search(r'\sdisabled(?=[\s>=])', open_tag):
        return True
    return 'pointer-events' in open_tag or 'not-allowed' in open_tag


SIZES = ('btn-sm', 'btn-lg', 'btn-block')

# Class names carried by the markup that NOTHING defines and NOTHING
# references - no CSS rule, no JavaScript selector. Checked by grep across
# templates and static/ before being listed here. Carried forward they would
# read as meaningful; dropped, nothing changes.
DEAD = ('modal-btn-cancel', 'modal-btn-confirm')

# Left alone entirely, and reported as skipped rather than silently passed:
#   - a class attribute containing Django logic, because its colour IS the
#     state (finance_pl_act's budget/actuals toggle switches btn-info and
#     btn-secondary from the template). Flattening it to one tone would
#     delete the active state.
#   - .action-more-item, which base.html styles directly as a menu row and
#     which takes no tone.
def skip_reason(cls):
    if '{%' in cls or '{{' in cls:
        return 'colour is template logic (a segmented toggle)'
    if 'action-more-item' in cls.split():
        return 'dropdown menu row - base styles .action-more-item directly'
    return None


def rebuild(cls, tone):
    """The final class list: swap the tone, PRESERVE everything else.

    Reconstructing the list from scratch is how a sweep quietly eats
    `btn-sm` (a size), `help-btn` (a page hook) and `disabled-btn` (the
    difference between a live button and a dead one). So: remove only the
    Bootstrap colours and the old tone names, then insert the new tone.
    """
    out, seen = [], set()
    for c in cls.split():
        if c in BOOTSTRAP or c in TONES or c in MISNAMED or c in DEAD:
            continue
        if c == 'disabled-btn':          # re-derived, re-added below
            continue
        if c in seen:
            continue
        seen.add(c)
        out.append(c)
    if 'btn' not in out:
        out.insert(0, 'btn')             # pair the tone: (0,2,0) beats a page
    i = out.index('btn') + 1
    return ' '.join(out[:i] + tone.split() + out[i:])


def plan_footer(items):
    """Tone every button in one modal footer.

    Positional, not a verb whitelist:
      cancel/close        -> action-secondary
      destructive verb    -> action-secondary action-danger
      the LAST of what is left -> action-primary; earlier ones secondary

    Verified against all 33 drifting footers in the property module. Every
    one is 'Cancel/Close plus at most one other button'.
    """
    out = [None] * len(items)
    rest = []
    for i, (lab, cls, _tag) in enumerate(items):
        if is_cancel(lab):
            out[i] = 'action-secondary'
        elif is_destructive(lab) or 'btn-danger' in cls.split() \
                or 'action-danger' in cls.split():
            # finance_expense.html's confirm is labelled just "Confirm" but
            # carries btn-danger. The label alone would have made it the
            # primary - a solid teal button that deletes an expense.
            #
            # `action-danger` has to be read here too, not just `btn-danger`.
            # Reading only the Bootstrap class made this rule depend on the
            # very class the sweep removes: run once and the button was
            # correctly a danger, run again and it flipped to a solid teal
            # primary. A classifier must be a fixed point on its own output.
            out[i] = 'action-secondary action-danger'
        else:
            rest.append(i)
    for n, i in enumerate(rest):
        out[i] = 'action-primary' if n == len(rest) - 1 else 'action-secondary'
    return out


def plan_bar(items, in_bar=False):
    """Tone every button in one page-action bar.

    Order of reading - position class, then Back, then existing tone, then
    verb. v1 read only the Bootstrap colour and told me to make "Add New" a
    secondary, which is backwards: Add New is the whole point of a list page.
    """
    out = []
    for lab, cls, tag in items:
        names = cls.split()
        low = lab.lower()

        if 'action-more-btn' in names:
            out.append('')                                  # base styles it
            continue
        if 'back-button' in names:
            out.append('back-button')
            continue
        if 'action-back' in names or 'action-btn-back' in names \
                or low.strip() == 'back':
            out.append('action-back')
            continue

        if 'action-add-new' in names or low.startswith('add new'):
            tone = 'action-primary'
        elif is_destructive(lab) or 'btn-danger' in names \
                or 'action-danger' in names:
            tone = 'action-secondary action-danger'      # fixed point: see
            #                                              plan_footer
        elif low.startswith('help'):
            tone = 'action-secondary'                       # never the verb
        elif 'action-primary' in names:
            tone = 'action-primary'
        else:
            tone = 'action-secondary'

        if is_disabled(tag, cls):
            tone += ' disabled-btn'
        out.append(tone)

    # A bar holding exactly ONE button that is not Back and not the More
    # toggle: that button IS the page's verb, whatever it is called.
    #
    # Two real misses came from relying on a verb list instead. "Submit FSR"
    # is not in the list, so it came out secondary on a page with nothing
    # else. customer_form.html was worse: its label is
    # `{% if mode == 'edit' %}Save Changes{% else %}Add Customer{% endif %}`,
    # the extractor could read no word at all, and the page ended up with no
    # primary whatsoever. A rule that counts buttons cannot be fooled by a
    # label it cannot read.
    #
    # Help is the one exception, settled on passport_management.html: a page
    # whose only button is Help has no primary, because Help is never the
    # verb.
    # Two guards the rule needs, which I did not state when I proposed it:
    #
    #  - IN A BAR ONLY. The loose scan calls this with a single button, so
    #    "exactly one" is trivially true there and every lone button in a
    #    card slot would be promoted. asset_detail.html's Add Record pair
    #    got promoted exactly that way.
    #  - CANCEL IS NEVER THE VERB. edit_asset.html has a bar whose only
    #    non-Back button is Cancel, and the rule made Cancel the primary.
    real = [i for i, (lab, cls, _t) in enumerate(items)
            if not out[i].startswith('action-back')
            and out[i] != ''
            and 'back-button' not in out[i]
            and not lab.lower().startswith('help')
            and not is_cancel(lab)]
    if in_bar and len(real) == 1:
        i = real[0]
        if out[i].startswith('action-secondary') and 'action-danger' not in out[i]:
            out[i] = out[i].replace('action-secondary', 'action-primary', 1)
    return out


def in_table(m, pos):
    """Is this offset inside a <table>? Row actions are a different
    vocabulary - icons in rows - and always were out of scope."""
    for t in re.finditer(r'<table\b', m):
        e = m.find('</table>', t.start())
        if t.start() <= pos < (e if e > 0 else len(m)):
            return True
    return False


def innermost_wrapper(m, pos):
    """Class list of the innermost element containing `pos`.

    The tone of a button that sits in no bar is decided by WHERE it sits -
    a filter panel, a notification card, a confirmation page - so the
    wrapper has to be known, not guessed from the class string.
    """
    best = None
    for w in re.finditer(r'<(?:div|section|form|td|li)\b[^>]*class="([^"]*)"[^>]*>',
                         m):
        a = w.start()
        if a > pos:
            break
        depth, end = 0, None
        for d in re.finditer(r'<div\b|</div>', m[a:]):
            if d.group(0) == '</div>':
                depth -= 1
                if depth == 0:
                    end = a + d.end()
                    break
            else:
                depth += 1
        if end and a <= pos < end and (best is None or a > best[0]):
            best = (a, w.group(1))
    return best[1].split() if best else []


def decided_tone(wrapper_names, label):
    """(tone, reason) for a button outside any bar, or (None, None)."""
    for n in wrapper_names:
        if n in LEAVE:
            return None, LEAVE[n]
        if n in DECIDED:
            low = label.lower()
            for frag, tone in DECIDED[n]:
                if frag == '*' or frag in low:
                    return tone, None
    return None, None


def scan_text(name, raw):
    """scan(), but over text held in memory rather than read from disk.

    The patcher edits a file in one pass and writes once. A plan built by
    re-reading the file from disk would be a plan for the version BEFORE
    those edits - which is how --check and apply came to disagree once
    already.
    """
    return _scan(name, markup_of(raw))


def scan(name):
    """Every button base.html owns on this page, with what it should carry.

    Returns [(where, label, bootstrap, current classes, wanted classes,
              start, end_of_open_tag)] - offsets so a patcher can rewrite
        the exact occurrence rather than a string that may mean two things.
    """
    return _scan(name, markup_of(read(os.path.join(TPL, name))))


def _scan(name, m):
    regions = [(n, a, z) for n, a, z in bars(m)] + \
              [(w, a, z) for w, a, z in footers(m)]

    hits = []
    claimed = set()
    for kind, a, z in regions:
        items, spots = [], []
        for b in BTN.finditer(m[a:z]):
            open_tag = b.group(0)[:b.group(0).index('>') + 1]
            items.append((label_of(b.group(3)), b.group(2), open_tag))
            spots.append((a + b.start(), a + b.start() + len(open_tag)))
        tones = (plan_footer(items) if kind == 'modal footer'
                 else plan_bar(items, in_bar=True))
        for (lab, cls, _t), tone, (s, e) in zip(items, tones, spots):
            claimed.add(s)
            boot = [c for c in cls.split() if c in BOOTSTRAP]
            why = skip_reason(cls)
            want = cls if why else rebuild(cls, tone)
            hits.append((kind, lab, boot, cls, want, s, e, why))

    # Buttons outside every recognised bar. v1 ignored these entirely (75
    # missed); v2 caught only the ones already wearing a house class (154
    # still missed). A button is in scope here if it has a house class, OR
    # its wrapper appears in DECIDED - and it is explicitly OUT of scope if
    # its wrapper appears in LEAVE. Anything else is UNCLASSIFIED and says
    # so, loudly, instead of being silently skipped.
    for b in BTN.finditer(m):
        if b.start() in claimed:
            continue
        cls = b.group(2)
        names = cls.split()
        boot = [c for c in names if c in BOOTSTRAP]
        has_house = any(c in HOUSE for c in names)
        if not boot and not has_house:
            continue
        open_tag = b.group(0)[:b.group(0).index('>') + 1]
        lab = label_of(b.group(3))
        wrap = innermost_wrapper(m, b.start())
        why = skip_reason(cls)

        if in_table(m, b.start()):
            why = why or 'a row action inside a table'
        tone, leave_why = decided_tone(wrap, lab)
        if leave_why:
            why = why or leave_why

        if why:
            hits.append(('skipped', lab, boot, cls, cls,
                         b.start(), b.start() + len(open_tag), why))
            continue

        if tone is None and has_house:
            tone = plan_bar([(lab, cls, open_tag)])[0]
        if tone is None:
            # Nobody has decided this one. That is a finding, not a no-op.
            hits.append(('UNCLASSIFIED', lab, boot, cls, cls,
                         b.start(), b.start() + len(open_tag), None))
            continue

        where = ('back link'
                 if ('back-button' in names or 'action-back' in names
                     or 'action-btn-back' in names)
                 else 'decided')
        hits.append((where, lab, boot, cls, rebuild(cls, tone),
                     b.start(), b.start() + len(open_tag), None))

    hits.extend(twins(m, hits))
    return sorted(hits, key=lambda h: h[5])


# How far apart the two halves of a permission pair can sit. Measured: the
# widest real pair in this codebase is 214 characters.
TWIN_WINDOW = 600


def twins(m, hits):
    """The other half of a `{% if perms %} / {% else %}` permission pair.

    asset_detail.html:

        {% if perms… %} <button class="btn btn-sm btn-info">Add Record</button>
        {% else %}      <span class="btn btn-sm btn-info disabled-btn">Add
                        Record</span>
        {% endif %}

    Only the disabled half carries a house class, so only that half is
    found. Sweeping it alone leaves the live button Bootstrap-teal beside
    its house-grey twin, on the same card. A pair is one decision: if one
    half is in scope, both are.
    """
    taken = {h[5] for h in hits}
    out = []
    for kind, lab, _boot, _cls, want, s, _e, why in list(hits):
        if why:
            continue
        for b in BTN.finditer(m):
            if b.start() in taken or abs(b.start() - s) > TWIN_WINDOW:
                continue
            if label_of(b.group(3)) != lab:
                continue
            gap = m[min(b.start(), s):max(b.start(), s)]
            if '{% else %}' not in gap and '{% elif' not in gap:
                continue
            cls2 = b.group(2)
            open2 = b.group(0)[:b.group(0).index('>') + 1]
            if skip_reason(cls2):
                continue
            tone = ' '.join(c for c in want.split()
                            if c in TONES or c == 'disabled-btn')
            tone = ' '.join(c for c in tone.split() if c != 'disabled-btn')
            if is_disabled(open2, cls2):
                tone += ' disabled-btn'
            taken.add(b.start())
            out.append((kind + ' (twin)', lab,
                        [c for c in cls2.split() if c in BOOTSTRAP],
                        cls2, rebuild(cls2, tone), b.start(),
                        b.start() + len(open2), None))
    return out


# ---------------------------------------------------------------------------
# buttons that only exist once JavaScript has run
# ---------------------------------------------------------------------------
# THE FOURTH BLIND SPOT. markup_of() blanks <script> on purpose - a class name
# in a CSS rule is not a button, and neither is one in a string the page never
# uses. But this codebase builds whole modals inside template literals, and
# every button in them was invisible to a guard that reported zero drift. The
# green "Save Changes" on the Manage Expense modal is the one that was found
# by hand, and it is one of twenty.
#
# This pass deliberately does NOT rewrite anything. In markup, a wrapper tells
# you what a button is for; in a string fragment there may be no wrapper at
# all, and the difference between a page verb and a row action is the
# difference between "make it teal" and "recolour every row in a table".
# So: find them, say where they are, say what CONTEXT was visible, and let a
# person decide. A false positive here is a rewrite inside working JavaScript.

SCRIPT = re.compile(r'<script\b[^>]*>(.*?)</script>', re.S | re.I)

# `foo.innerHTML = ` / `const html = ` immediately above the fragment. This is
# the only structural clue some of these have - cashflow_forecast.html's three
# buttons live in a bare fragment assigned to modalFooter.innerHTML, with no
# wrapper div anywhere in the string.
#
# The optional-dot version of this pattern matched `class="` and reported
# every button in the list as "assigned to class". A hint that is wrong on
# nineteen of twenty is worse than no hint: it is a confident-sounding label
# on a decision somebody is about to make by eye. Require a real assignment.
SINK = re.compile(r'([A-Za-z_$][\w$]*)\.(?:inner|outer)HTML\s*(?:\+)?=\s*[`\'"]'
                  r'|(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=\s*[`\'"]', re.S)

# A wrapper opened earlier in the SAME fragment. Same idea as
# innermost_wrapper(), but a fragment is not a document - it is often not even
# balanced - so this reports the nearest preceding one as a hint and does not
# pretend to know it encloses the button.
JSWRAP = re.compile(r'<(?:div|section|form)\b[^>]*class="([^"$]*)"')


def js_context(body, at):
    """(wrapper hint, sink hint) for a button at offset `at` in script text."""
    near = body[max(0, at - 700):at]
    wrap = None
    for w in JSWRAP.finditer(near):
        wrap = w.group(1)
    sink = None
    for s in SINK.finditer(near):
        sink = s.group(1) or s.group(2)
    return wrap, sink


def js_buttons(raw):
    """[(label, classes, wrapper hint, sink hint, line, leave reason)].

    Only COMPLETE class attributes are considered - `class="btn btn-info"`,
    not `class="btn ${tone}"`. A class list with a substitution in it is not
    a string this pass can reason about, and guessing at one is how you end
    up rewriting a variable name.
    """
    out = []
    for s in SCRIPT.finditer(raw):
        body, base = s.group(1), s.start(1)
        for b in BTN.finditer(body):
            cls = b.group(2)
            if '$' in cls or '{' in cls or '}' in cls:
                continue                      # interpolated - not decidable
            if not [c for c in cls.split() if c in BOOTSTRAP]:
                continue                      # nothing base.html would own
            wrap, sink = js_context(body, b.start())
            line = raw.count('\n', 0, base + b.start()) + 1
            # A wrapper already on the LEAVE list was decided once, in
            # markup, and the decision does not change because the div
            # happens to be built by JavaScript. financial_indicators and
            # vacancy_management both put their Select All / Select None
            # pair in .selection-buttons - a segmented toggle whose colour
            # IS its state. Carry the reason across rather than asking for
            # the same four decisions a second time.
            why = LEAVE.get(wrap.split()[0]) if wrap else None
            out.append((label_of(b.group(3)), cls, wrap, sink, line, why))
    return out


def drifting(h):
    """Is this button actually wrong today?

    Wrong = still carries a Bootstrap colour, or its class list does not
    already say what it should say.
    """
    _kind, _lab, _boot, cls, want, _s, _e, why = h
    if why:
        return False                     # deliberately out of scope
    return cls.split() != want.split()


# ---------------------------------------------------------------------------
# reporting
# ---------------------------------------------------------------------------

RECIPE = ('recipe', 'meal_plan', 'meal_plans', 'ingredient', 'wcim',
          'celebration', 'pantry', 'unit_conversions', 'measurement_units',
          'household_member', 'map_ingredients', 'import_recipe',
          'preview_imported')


def is_recipe_side(f):
    return any(k in f for k in RECIPE)


def templates(include_recipes):
    """Every template, RECURSIVELY.

    v2 called os.listdir and never opened a subdirectory. pages/templates has
    six of them, holding seventeen templates: the whole Projects section,
    Cashflow Forecast, Financial Indicators, Vacancy Management, the PDF
    viewer, physical invoice and the connectivity error page. The guard
    reported zero drift across the property module while 76 buttons in those
    files had never been looked at once.
    """
    out = []
    for root, dirs, files in os.walk(TPL):
        dirs[:] = sorted(d for d in dirs if d != 'lease_templates')
        for f in sorted(files):
            if not f.endswith('.html') or '.bak' in f:
                continue
            rel = os.path.relpath(os.path.join(root, f), TPL).replace(os.sep, '/')
            if rel == 'base.html' or 'DO NOT USE' in rel:
                continue
            if not include_recipes and is_recipe_side(rel):
                continue
            out.append(rel)
    return out


def print_js(js_rows):
    """The <script> findings, on WHICHEVER report branch we end up in.

    It has to print on the clean path too. "Nothing drifting" returning
    early, with twenty buttons sitting in template literals, is precisely
    the shape of every blind spot this guard has already had.
    """
    if not js_rows:
        return
    open_rows = [r for r in js_rows if not r[6]]
    left_n = collections.Counter(r[6] for r in js_rows if r[6])
    print('')
    if not open_rows:
        print('  %d button(s) built inside <script>, all already decided.'
              % len(js_rows))
        for _why, _n in left_n.most_common():
            print('     %-52s %3d' % (_why, _n))
        return
    print('  %d BUTTON(S) BUILT INSIDE <script>' % len(open_rows))
    print('  Invisible to every earlier version of this guard: markup_of()')
    print('  blanks <script>, and nothing ever looked in there.')
    print('  NOT rewritten. In a string fragment there is often no wrapper to')
    print('  say whether a button is a page verb or a row action, and a wrong')
    print('  guess edits working JavaScript. These are decided by hand.')
    for _f, _n in collections.Counter(r[0] for r in open_rows).most_common():
        print('     %-44s %3d' % (_f, _n))
    for _why, _n in left_n.most_common():
        print('  (%d more carry a wrapper already decided: %s)' % (_n, _why))
    print('  Run --js for the full list, with what context was visible.')


def print_double_bars(rows):
    if not rows:
        return
    print('')
    print('  %d PAGE(S) RENDER THEIR ACTIONS TWICE' % len(rows))
    print('  Two action bars, each holding a real verb - the same buttons')
    print('  once above the form and once below it. A second bar holding')
    print('  only Back is navigation and does NOT count. Found by measuring')
    print('  every page, not by looking at one.')
    for f, labels in rows:
        print('     %s' % f)
        for k, labs in enumerate(labels):
            print('        bar %d: %s' % (k + 1, ' | '.join(labs)[:56]))


def main():
    if not os.path.isdir(TPL):
        sys.exit('! pages/templates not found - run from the project root')

    argv = sys.argv[1:]
    full = None
    if '--full' in argv:
        i = argv.index('--full')
        if i + 1 < len(argv):
            full = argv[i + 1]
    recipes = '--recipes' in argv
    files = templates(recipes)

    # TWO BARS IS NOT THE FAULT. TWO SETS OF VERBS IS.
    #
    # The first version of this counted standard bars, which caught the three
    # real duplicates and would also have caught the delete-confirmation page
    # after we deliberately fixed it - its top bar keeps Back and nothing
    # else, which is navigation, not a second copy of the page's actions.
    # A gate that fires on the shape we agreed to adopt teaches people to
    # ignore it. So: a page is flagged when TWO bars each hold a real verb.
    def _verbs(seg):
        out = []
        for b in BTN.finditer(seg):
            cls, lab = b.group(2), label_of(b.group(3))
            if 'action-back' in cls or 'back-button' in cls:
                continue
            if 'action-more' in cls or is_cancel(lab):
                continue
            out.append(lab)
        return out

    dbl = []
    for _f in files:
        _m = markup_of(read(os.path.join(TPL, _f)))
        _std = [(a, z) for n, a, z in bars(_m) if n == STANDARD_BAR]
        if len([1 for a, z in _std if _verbs(_m[a:z])]) > 1:
            dbl.append((_f, [[label_of(b.group(3))
                              for b in BTN.finditer(_m[a:z])]
                             for a, z in _std]))

    # ---------------------------------------------------------------------
    # buttons that only exist once JavaScript has run
    # ---------------------------------------------------------------------
    js_rows = []
    for _f in files:
        for _hit in js_buttons(read(os.path.join(TPL, _f))):
            js_rows.append((_f,) + _hit)

    if '--js' in argv:
        print('')
        print('=' * 74)
        print(' BUTTONS BUILT INSIDE <script> - context, not a decision')
        print('=' * 74)
        print('')
        print('  %-30s %5s %-20s %s' % ('file', 'line', 'label', 'class'))
        print('  ' + '-' * 88)
        for _f, _lab, _cls, _wrap, _sink, _line, _why in js_rows:
            print('  %-30s %5d %-20s %s'
                  % (_f[:30], _line, _lab[:20], _cls))
            _hint = []
            if _wrap:
                _hint.append('inside .%s' % _wrap.split()[0])
            if _sink:
                _hint.append('assigned to %s' % _sink)
            print('  %-30s %5s %s'
                  % ('', '', '  ' + (', '.join(_hint)
                                     or 'no context visible')))
            if _why:
                print('  %-30s %5s   -> already decided: %s'
                      % ('', '', _why))
        print('  ' + '-' * 88)
        print('')
        print('  %d button(s) in %d file(s), %d still undecided.'
              % (len(js_rows), len({r[0] for r in js_rows}),
                 len([r for r in js_rows if not r[6]])))
        print('  None of these were rewritten.')
        print('')
        return 0


    if full:
        if not os.path.exists(os.path.join(TPL, full)):
            sys.exit('! %s not found' % full)
        print('')
        print('=' * 74)
        print(' %s' % full)
        print('=' * 74)
        m = markup_of(read(os.path.join(TPL, full)))
        for n, a, _z in bars(m):
            print('')
            print('  bar wrapper : .%s%s' % (n, '' if n == STANDARD_BAR
                                             else '   -> rename to .%s'
                                             % STANDARD_BAR))
        for n in rejected_wrappers(m):
            print('  .%s holds no page verbs - NOT a bar, left alone' % n)
        hits = scan(full)
        if not any(drifting(h) for h in hits):
            print('')
            print('  Clean - every button here agrees with base.html.')
        for h in hits:
            kind, lab, _boot, cls, want, _s, _e, _w = h
            if not drifting(h):
                continue
            print('')
            print('  %-14s %s' % (kind, lab))
            print('     carries : %s' % cls)
            print('     becomes : class="%s"' % want)
        print('')
        return 0

    rows = []
    skipped_n = collections.Counter()
    unclassified = []
    for f in files:
        found = scan(f)
        h = [x for x in found if drifting(x)]
        if h:
            rows.append((f, h))
        for x in found:
            if x[0] == 'skipped':
                skipped_n[x[7]] += 1
            elif x[0] == 'UNCLASSIFIED':
                unclassified.append((f, x[1], x[3]))

    print('')
    print('=' * 74)
    print(' BUTTON DRIFT - markup that has not caught up with base.html')
    print('=' * 74)
    print('')
    print('  scope: %s' % ('the whole application'
                           if recipes else 'property management '
                           '(--recipes adds the recipe/meal-plan side)'))
    print('')
    if not rows and not unclassified:
        print('  Nothing drifting, and nothing undecided.')
        print('  %d button(s) are deliberately left alone:' % sum(skipped_n.values()))
        for why, n in skipped_n.most_common():
            print('     %-52s %3d' % (why, n))
        print_double_bars(dbl)
        print_js(js_rows)
        print('')
        # Even here. "Nothing drifting" is not the same as "nothing wrong",
        # and this branch returning a flat 0 is how a gate quietly stops
        # being a gate - the exact shape of every blind spot this file has
        # already had.
        return 1 if ('--strict' in argv and dbl) else 0
    if not rows:
        print('  Nothing drifting - but see the undecided list below.')

    total = sum(len(h) for _, h in rows)
    print('  %-34s %6s   %s' % ('template', 'btns', 'where'))
    print('  ' + '-' * 68)
    for f, h in sorted(rows, key=lambda r: -len(r[1])):
        where = sorted(set(w for w, _, _, _, _, _, _, _ in h))
        print('  %-34s %6d   %s' % (f[:34], len(h), ', '.join(where)))
    print('  ' + '-' * 68)
    print('  %-34s %6d   across %d template(s)'
          % ('TOTAL', total, len(rows)))
    print('')

    tally = {}
    for _, h in rows:
        for _, _, boot, _, _, _, _, _ in h:
            for c in boot:
                tally[c] = tally.get(c, 0) + 1
    print('  still carried:  %s'
          % '   '.join('%s x%d' % (k, v)
                       for k, v in sorted(tally.items(), key=lambda x: -x[1])))

    print('')
    print('  deliberately left alone, with a reason on record:')
    for why, n in skipped_n.most_common():
        print('     %-52s %3d' % (why, n))

    if unclassified:
        print('')
        print('  %d BUTTON(S) NOBODY HAS DECIDED ON' % len(unclassified))
        print('  Not drift and not out of scope - simply never looked at.')
        print('  This is the bucket that made the last two guards lie.')
        for f, lab, cls in unclassified[:14]:
            print('     %-40s %-22s %s' % (f[:40], lab[:22], cls[:30]))
        if len(unclassified) > 14:
            print('     ... and %d more' % (len(unclassified) - 14))

    loose = sum(1 for _, h in rows for x in h if x[0] == 'loose')
    if loose:
        print('')
        print('  %d of those sit in a bar that is NOT called '
              '.page-action-buttons,' % loose)
        print('  so base.html reaches their colour but not their layout.'
              ' Run --wrappers.')

    print_double_bars(dbl)
    print_js(js_rows)

    if '--wrappers' in argv:
        print('')
        print('=' * 74)
        print(' BAR WRAPPERS - one design, %s names' % 'many')
        print('=' * 74)
        print('')
        names, off = {}, []
        for f in files:
            m = markup_of(read(os.path.join(TPL, f)))
            for n, _a, _z in bars(m):
                names.setdefault(n, []).append(f)
                if n != STANDARD_BAR:
                    off.append((f, n))
        print('  %-32s %5s' % ('wrapper class', 'bars'))
        print('  ' + '-' * 44)
        for n, v in sorted(names.items(), key=lambda x: -len(x[1])):
            print('  %-32s %5d%s' % ('.' + n, len(v),
                                     '   <- the standard'
                                     if n == STANDARD_BAR else ''))
        print('  ' + '-' * 44)
        print('  %d bar(s) carry a name base.html does not style'
              % len(off))
        print('')
        for f, n in sorted(off):
            print('     %-40s .%s' % (f, n))
        print('')
        return 0

    if '--patterns' in argv:
        pat = {}
        for f, h in rows:
            for _kind, _lab, _boot, cls, want, _s, _e, _w in h:
                pat.setdefault((cls, want), []).append(f)
        print('')
        print('=' * 74)
        print(' DISTINCT PATTERNS - what a sweep would actually have to do')
        print('=' * 74)
        print('')
        print('  %-46s %5s  %s' % ('class="..."', 'count', 'becomes'))
        print('  ' + '-' * 70)
        for (cls, want), where in sorted(pat.items(), key=lambda x: -len(x[1])):
            print('  %-46s %5d  %s' % (cls[:46], len(where), want))
        print('  ' + '-' * 70)
        print('  %d distinct pattern(s) covering %d button(s)'
              % (len(pat), sum(len(v) for v in pat.values())))
        print('')
        dup = {}
        for (cls, want) in pat:
            dup.setdefault(cls, []).append(want)
        amb = {c: w for c, w in dup.items() if len(w) > 1}
        if amb:
            print('  %d class string(s) mean DIFFERENT things depending on '
                  'context -' % len(amb))
            print('  a find-and-replace on these would be silently wrong:')
            for c, w in sorted(amb.items()):
                print('     %-44s -> %s' % (c[:44], ' | '.join(sorted(w))))
        print('')
        return 0

    if '--clean' in argv:
        drift_files = {f for f, _ in rows}
        clean = [f for f in files if f not in drift_files]
        print('')
        print('  %d template(s) already agree with base.html:' % len(clean))
        for f in clean:
            print('     %s' % f)

    print('')
    print('  --wrappers  the bar NAMES, and which ones base cannot style')
    print('  --patterns  how many DISTINCT edits this really is')
    print('  --full <f>  one page, with the class each button should carry')
    print('  --recipes   include the recipe / meal-plan side')
    print('  --js        the buttons built inside <script>, with context')
    print('  --strict    exit 1 while any drift remains (for the push script)')
    print('')
    # `dbl` gates too. A duplicated action bar is a defect on the page, not
    # a decision anybody deferred, and the only reason it was not gated
    # before is that nothing measured it.
    return 1 if ('--strict' in argv and (rows or unclassified or dbl)) else 0


if __name__ == '__main__':
    sys.exit(main())
