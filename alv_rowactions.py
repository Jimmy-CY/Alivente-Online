# -*- coding: utf-8 -*-
"""alv_rowactions.py - the ACTION COLUMN, read as blocks rather than text.

RA-1, 4 Oct 2026. Demetri: "I think that we should put the Delete Action
Item on the right hand side of all the icons. We should define a standard
order that we place all icons in all tables, in the Action Column and
apply this across the app."

THE ORDER, agreed: LOOK -> CHANGE -> COPY -> ADVANCE -> DESTROY.

    LOOK     you are shown something and nothing happens
    CHANGE   this record is edited
    COPY     a new record is made from this one
    ADVANCE  the record moves on - sent, approved, locked, voided
    DESTROY  it is gone

Reading left to right the row gets more consequential, and the thing that
cannot be undone is at the end, furthest from the thing you press most.

THIS MODULE IS SHARED BY THREE CALLERS so the order is defined once:
apply_row_action_order.py, Show-RowActionDrift.py and
test_row_action_order.py. A rule that each of them spelled out would be
three rules a week from now.

WHY BLOCKS AND NOT A REGEX OVER THE TEXT. An action in this tree is not
one element. It is usually

    {% if perms.auth.can_edit_tenants %}
      <a class="icon-action-btn icon-edit">...</a>
    {% else %}
      <span class="icon-action-btn icon-disabled">...</span>
    {% endif %}

- a permission test, the control, and the disabled mirror a read-only
user sees instead. Reordering has to carry all three together, and the
delete on tenant.html is a whole <form> with a csrf token and an onsubmit
confirm in it. So the wrapper is split into balanced blocks and the
BLOCKS are sorted; nothing inside one is rewritten.
"""
import re

# The order, and the only place it is written down.
LOOK, CHANGE, COPY, ADVANCE, DESTROY = range(5)

FAMILY = {
    # LOOK - shows you something, changes nothing.
    'view': LOOK, 'document': LOOK, 'pdf': LOOK, 'list': LOOK,
    'assets': LOOK, 'manage': LOOK, 'event': LOOK,
    # CHANGE
    'edit': CHANGE,
    # COPY
    'duplicate': COPY,
    # ADVANCE - the record moves on.
    'upload': ADVANCE, 'send': ADVANCE, 'approve': ADVANCE,
    'unapprove': ADVANCE, 'void': ADVANCE, 'lock': ADVANCE,
    'unlock': ADVANCE, 'permissions': ADVANCE, 'reset-pw': ADVANCE,
    # DESTROY - last, always.
    'delete': DESTROY,
}

FAMILY_NAME = {LOOK: 'look', CHANGE: 'change', COPY: 'copy',
               ADVANCE: 'advance', DESTROY: 'destroy'}

# WITHIN "look", a second order: the record itself, then its papers, then
# its children. Everything else sorts stably on the family alone, so a
# page that already reads sensibly is left exactly as it is.
WITHIN = {'view': 0, 'manage': 0, 'event': 0,
          'document': 1, 'pdf': 1,
          'list': 2, 'assets': 2}

OPEN = re.compile(r'<(span|div)[^>]*class="[^"]*\brow-actions\b[^"]*"[^>]*>',
                  re.I)


# NAMED, NOT UNEXAMINED.                           [RA-5, 5 Oct 2026]
#
# A .row-actions wrapper is for a GROUP of actions in a row's action
# column. These four controls are not that: each is a single Remove
# button beside the one thing it removes, and wrapping it would tell the
# drift report there is an action column with one action in it - a column
# invented to satisfy a census.
#
# Demetri ruled on the edit_asset one when AI-1 built it: "Leave it
# named, it is not an action column." The three on create_meal_plan are
# the same control on a different page.
#
# THE COUNT IS THE POINT. Each entry pins an exact number. A page that
# grows one more loose button does not inherit the exemption - the count
# stops matching and the report calls it a problem by name. An exemption
# that covered whatever turned up next to it would be worse than none.
NAMED = {
    'edit_asset.html': {
        'count': 1,
        'classes': ('icon-delete',),
        'why': 'Remove the attached invoice - one control beside the file '
               'name it removes. AI-1, and Demetri: leave it named.',
    },
    'create_meal_plan.html': {
        'count': 3,
        'classes': ('icon-delete',),
        'why': 'Remove this recipe - one control at the end of each recipe '
               'row, beside the name and the servings box. Built inside a '
               'JavaScript template literal.',
    },
}


def named(page, hits):
    """(reason, exact) for a page's unwrapped buttons, or (None, None).

    `exact` is False when the register knows the page but the number of
    loose buttons on it has moved, which is the case the register must
    not quietly absorb.
    """
    e = NAMED.get(page)
    if not e:
        return None, None
    if len(hits) != e['count']:
        return e['why'], False
    for classes, _ in hits:
        if not any(c in e['classes'] for c in classes):
            return e['why'], False
    return e['why'], True


def wrappers(src):
    """[(start, end, inner)] for every .row-actions wrapper.

    Balanced on its OWN tag name: the class sits on a <span> on eight
    pages and a <div> on five. A scanner written for one of them misses
    six pages and says nothing."""
    out = []
    for m in OPEN.finditer(src):
        tag = m.group(1).lower()
        pat = re.compile(r'</?%s\b[^>]*>' % tag, re.I)
        depth = 0
        for t in pat.finditer(src, m.start()):
            depth += -1 if t.group(0).startswith('</') else 1
            if depth == 0:
                out.append((m.end(), t.start(), src[m.end():t.start()]))
                break
    return out


IFTAG = re.compile(r'\{%\s*(if|endif)\b[^%]*%\}')
ELEM = re.compile(r'<(a|form|button|span|div)\b', re.I)


# BTN_FULL, not BTN. alv_rowactions already defines a BTN further down -
# a single-group match on the class attribute alone - and a second
# module-level BTN simply shadows the first by source order, so
# unwrapped() called the OTHER one and m.group(2) raised IndexError on
# the first page it read. Two constants, two names.
BTN_FULL = re.compile(
    r'<(?:button|a)[^>]*class="([^"]*\bicon-action-btn\b[^"]*)"[^>]*>'
    r'(.*?)</(?:button|a)>', re.S)


def unwrapped(src):
    """[(classes, glyphs)] for every icon button NOT inside a wrapper.

    RA-2, 5 Oct 2026. wrappers() answers "what is inside a .row-actions",
    and every caller has treated that as "every icon button in the file".
    It is not: 37 of 120 are outside one. This is the other question,
    asked separately, so that no caller has to assume an answer it was
    never given.
    """
    spans = [(s, e) for s, e, _ in wrappers(src)]
    out = []
    for m in BTN_FULL.finditer(src):
        if any(s <= m.start() < e for s, e in spans):
            continue
        # FOUND BY PATTERN, NOT BY SPLITTING ON SPACES. A class attribute
        # in this tree is not a list of words - household_member writes
        #     class="icon-action-btn {% if m.is_active %}icon-lock
        #            {% else %}icon-unlock{% endif %}"
        # and splitting that yields the Django tags, no icon- token, and
        # a report that says the button has no icon class when it has
        # one of two chosen at render. The first build of this helper did
        # exactly that and named a perfectly correct button as a defect.
        names = [c for c in re.findall(r'\bicon-[\w-]+', m.group(1))
                 if c != 'icon-action-btn']
        glyphs = [g for g in re.findall(r'fa-[a-z-]+', m.group(2))
                  if g not in ('fa-fw', 'fa-sm', 'fa-lg')]
        out.append((tuple(names), tuple(glyphs)))
    return out


def blocks(inner):
    """Split a wrapper into [(gap, block)] - balanced top-level units.

    A unit is a whole {% if %}...{% endif %}, or a whole element. The gap
    is the whitespace that preceded it, kept so reordering does not
    reflow the file."""
    out = []
    i = 0
    n = len(inner)
    while i < n:
        j = i
        while j < n and inner[j].isspace():
            j += 1
        if j >= n:
            out.append((inner[i:], ''))
            break
        gap = inner[i:j]
        m = IFTAG.match(inner, j)
        if m and m.group(1) == 'if':
            depth = 0
            end = None
            for t in IFTAG.finditer(inner, j):
                depth += 1 if t.group(1) == 'if' else -1
                if depth == 0:
                    end = t.end()
                    break
            if end is None:
                out.append((gap, inner[j:]))
                break
        else:
            e = ELEM.match(inner, j)
            if not e:
                # Not a block we recognise - a bare comment, say. Take
                # it to the next blank line and leave it where it is.
                nl = inner.find('\n\n', j)
                end = nl if nl > 0 else n
            else:
                tag = e.group(1).lower()
                if tag in ('br', 'img', 'input'):
                    end = inner.find('>', j) + 1
                else:
                    pat = re.compile(r'</?%s\b[^>]*>' % tag, re.I)
                    depth = 0
                    end = n
                    for t in pat.finditer(inner, j):
                        depth += -1 if t.group(0).startswith('</') else 1
                        if depth == 0:
                            end = t.end()
                            break
        out.append((gap, inner[j:end]))
        i = end
    return out


BTN = re.compile(r'class="([^"]*\bicon-action-btn\b[^"]*)"')


def verbs_of(block, live_only=True):
    """Every action this block performs, in source order.

    A BLOCK IS NOT ONE ACTION. crs/country_list writes Edit and Delete
    inside a single {% if perms %} with a two-span disabled mirror in
    the else; reading only the first control reported "view -> edit" on
    a row that has three buttons, and the first version of this module
    did exactly that on six pages.

    live_only drops the else-branch mirror, which is always
    icon-disabled. A block whose ONLY control is disabled is a
    placeholder and keeps its verb, so a read-only user sees the same
    order as everybody else."""
    out = []
    body = block
    if live_only:
        body = re.sub(r'\{%\s*else\s*%\}.*?\{%\s*endif\s*%\}', '',
                      block, flags=re.S)
        if not BTN.search(body):
            body = block          # a block with no live arm at all
    for m in BTN.finditer(body):
        for c in m.group(1).split():
            if not c.startswith('icon-') or c in ('icon-action-btn',):
                continue
            nm = c[5:]
            if nm in FAMILY:
                out.append(nm)
                break
    return out


def verb_of(block):
    """The block's FIRST action - what it sorts on."""
    v = verbs_of(block)
    return v[0] if v else None


def rank(block):
    v = verb_of(block)
    if v is None:
        return (99, 99)
    return (FAMILY[v], WITHIN.get(v, 0))


def ordered(inner):
    """The wrapper's blocks in house order, as one string.

    STABLE. Two actions of the same family keep the order the page put
    them in - this round decides where Delete goes, not which of two
    Advance buttons a page meant to come first."""
    bs = blocks(inner)
    live = [(g, b) for g, b in bs if verb_of(b)]
    dead = [(i, g, b) for i, (g, b) in enumerate(bs) if not verb_of(b)]
    gaps = [g for g, _ in live]
    body = [b for _, b in live]
    body = [b for _, b in sorted(enumerate(body),
                                 key=lambda x: (rank(x[1]), x[0]))]
    out = []
    k = 0
    for i, (g, b) in enumerate(bs):
        if verb_of(b):
            out.append(gaps[k] + body[k])
            k += 1
        else:
            out.append(g + b)
    return ''.join(out)


def sequence(inner):
    """Every verb the wrapper performs, in source order - flattened
    across blocks, because a block may hold more than one."""
    out = []
    for _, b in blocks(inner):
        out.extend(verbs_of(b))
    return out


def unfixable(inner):
    """Verbs that are out of order INSIDE one block.

    Sorting blocks cannot repair those - the two controls share a
    permission test - so they are reported rather than silently left
    wrong by a patcher that claims to have put the page in order."""
    bad = []
    for _, b in blocks(inner):
        v = verbs_of(b)
        if len(v) > 1 and not in_order(v):
            bad.append(v)
    return bad


def in_order(seq):
    keys = [(FAMILY[v], WITHIN.get(v, 0)) for v in seq]
    return keys == sorted(keys)
