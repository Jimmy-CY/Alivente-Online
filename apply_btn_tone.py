# -*- coding: utf-8 -*-
"""SECTION B, ROUND B-1 - THIRTEEN BOOTSTRAP COLOURS, TWELVE OF THEM INERT

Found while surveying the action bars for A-BAR: thirteen controls on five
pages wear a Bootstrap colour class ON TOP OF a house role - twelve of them
spelled plainly, and the thirteenth built by a Django tag, which is why the
tree-wide census below reads 12 and this round touches 13.

    btn btn-danger action-secondary
    btn btn-info action-primary
    btn btn-secondary action-secondary

==========================================================================
MEASURED BEFORE IT WAS TOUCHED, AND THE MEASUREMENT IS THE ROUND
==========================================================================
`.btn.action-secondary` is (0,2,0). `.btn-danger` is (0,1,0). The house
role wins on specificity, so it wins wherever it appears, whatever the
stylesheet order. Rendered in Chromium against base's real sheet:

    class                                    background            border
    btn action-secondary                     rgb(255, 255, 255)    line
    btn btn-danger action-secondary          rgb(255, 255, 255)    line
    btn btn-info action-secondary            rgb(255, 255, 255)    line
    btn btn-secondary action-secondary       rgb(255, 255, 255)    line
    btn btn-outline-danger action-secondary  rgb(255, 255, 255)    line
    btn action-primary                       rgb(14, 124, 139)     accent
    btn btn-info action-primary              rgb(14, 124, 139)     accent

Identical. Every one of them. So twelve of the thirteen classes change
NOTHING and can go with no visible effect at all - which is the point of
measuring first rather than arguing from the cascade.

They are not harmless, though: Show-ButtonDrift reads class lists, and a
control wearing two vocabularies is a control the next survey has to decide
about.

==========================================================================
THE THIRTEENTH IS A LIVE DEFECT
==========================================================================
recipe_management.html, the Favourites filter:

    class="btn {% if show_favourites %}btn-danger
                {% else %}btn-outline-danger{% endif %} action-secondary"

The colour IS the state. btn-danger when Favourites is on, outline when it
is off - and since BOTH resolve to the same white secondary, THE STATE HAS
NEVER BEEN VISIBLE. You cannot tell by looking whether you are seeing all
your recipes or only your favourites.

Base already has the answer and already wrote down the reason, four
thousand lines up, against the filter button:

    /* Pressed. A toggle with no visible state gets pressed twice. */
    .btn.action-filter[aria-pressed="true"] {
      background: var(--alv-accent-soft);
      border-color: var(--alv-accent-line);
      color: var(--alv-accent-ink);
    }

So .action-secondary gets the same pressed state, from the same three
tokens, and the Favourites link carries aria-pressed instead of a colour.
Which also means a screen reader is told, for the first time, whether the
filter is on.

NOT A NEW COLOUR. The three tokens are the ones .action-filter already
uses; nothing here invents a tone, and B-1 adds no literal to base.

==========================================================================
WHAT THIS ROUND DOES NOT DO
==========================================================================
It does not touch finance_pl_act's Budget/Actuals pair. Those are
btn-info / btn-outline-info with NO house role at all - a hand-rolled
segmented control, and base has had ALV-SEG v1 for exactly that since
2 Sep. Converting it changes how that control looks and it is a round of
its own, with its own renders.

It does not touch a bare Bootstrap colour on a control that has no house
role. Those are not drift between two vocabularies; they are a page that
has not been converted yet, which is a different queue.

Backups: .bak_btntone. Idempotent. --check writes nothing.
"""
import os
import re
import sys

import alv_tree

CHECK = '--check' in sys.argv
SUFFIX = '.bak_btntone'
CRLF = {}
ROOT = os.getcwd()
# A CLASS IS A TOKEN, NOT A SUBSTRING - and the first draft of this round
# got that wrong four hours after A-BAR's instrument got it wrong the same
# way. `\bbtn-primary\b` matches inside `modal-btn-primary`, because the
# hyphen before `btn` is a word boundary, so projects_detail reported four
# drifted controls that wear no Bootstrap colour at all. Tokens now, and
# the helpers below split the attribute rather than searching it.
BS_NAMES = frozenset(
    ['btn-primary', 'btn-secondary', 'btn-success', 'btn-danger',
     'btn-warning', 'btn-info', 'btn-light', 'btn-dark'])
ROLE_NAMES = frozenset(['action-primary', 'action-secondary'])


def bootstrap_colours(cls):
    return [c for c in cls.split()
            if c in BS_NAMES or c.startswith('btn-outline-')]


def house_roles(cls):
    return [c for c in cls.split() if c in ROLE_NAMES]


def read(path):
    with open(path, 'rb') as fh:
        raw = fh.read()
    CRLF[path] = b'\r\n' in raw
    return raw.decode('utf-8'), raw


def write(path, text):
    data = text.encode('utf-8')
    data = (data.replace(b'\r\n', b'\n').replace(b'\n', b'\r\n')
            if CRLF.get(path) else data.replace(b'\r\n', b'\n'))
    with open(path, 'wb') as fh:
        fh.write(data)


def back_up(path, raw):
    bak = path + SUFFIX
    if os.path.exists(bak):
        return
    with open(bak, 'wb') as fh:
        fh.write(raw)
    with open(bak, 'rb') as fh:
        if fh.read() != raw:
            raise SystemExit('B1: %s is not a byte copy' % bak)


def swap(text, old, new, what, path):
    o = old.replace('\r\n', '\n')
    n = new.replace('\r\n', '\n')
    if CRLF.get(path):
        o, n = o.replace('\n', '\r\n'), n.replace('\n', '\r\n')
    c = text.count(o)
    if c != 1:
        raise SystemExit('B1: %s appears %d times, not once' % (what, c))
    return text.replace(o, n)


def code_only(text):
    def blank(m):
        return re.sub(r'[^\n]', ' ', m.group(0))
    text = re.sub(r'<!--.*?-->', blank, text, flags=re.S)
    text = re.sub(r'\{#.*?#\}', blank, text, flags=re.S)
    return re.sub(r'/\*.*?\*/', blank, text, flags=re.S)


def drifted(text):
    """Every class attribute carrying BOTH a house role and a Bootstrap
    colour. Comment-stripped, so a note quoting the old class is not read
    as the defect - the mistake five rounds made before the instrument was
    fixed."""
    out = []
    for m in re.finditer(r'class="([^"]*)"', code_only(text)):
        c = m.group(1)
        if house_roles(c) and bootstrap_colours(c):
            out.append(c)
    return out


print('=' * 74)
print('SECTION B, ROUND B-1 - BOOTSTRAP COLOUR ON A HOUSE ROLE%s'
      % (' - CHECK ONLY' if CHECK else ''))
print('=' * 74)

# ==========================================================================
# THE CENSUS, ACROSS BOTH TEMPLATE ROOTS.
# ==========================================================================
before = {}
for p in alv_tree.templates():
    d = drifted(read(p)[0])
    if d:
        before[alv_tree.rel(p)] = d
n_before = sum(len(v) for v in before.values())
print('  %d control(s) on %d page(s) wear both vocabularies'
      % (n_before, len(before)))
for k in sorted(before):
    print('      %-40s %d' % (k, len(before[k])))
print('-' * 74)

FAV_OLD = '''           class="btn {% if show_favourites %}btn-danger{% else %}btn-outline-danger{% endif %} action-secondary">'''
FAV_NEW = '''           class="btn action-secondary"
           aria-pressed="{% if show_favourites %}true{% else %}false{% endif %}">'''

# ==========================================================================
# 1. THE ONE THAT MATTERS. Done first, and on its own, because it is the
#    only edit in the round that changes what the user sees.
# ==========================================================================
RM = alv_tree.path_of('recipe_management.html')
rm, rm_raw = read(RM)
if 'aria-pressed="{% if show_favourites %}' in rm:
    print('  recipe_management.html   Favourites already on aria-pressed')
else:
    rm = swap(rm, FAV_OLD,
              '''           <!-- B-1, 2 Oct 2026. The colour WAS the state here - btn-danger
                when Favourites is on, btn-outline-danger when it is off -
                and since .btn.action-secondary is (0,2,0) against
                btn-danger's (0,1,0), both resolved to the same white
                secondary. The state has never once been visible.

                aria-pressed instead, which base already answers for
                .action-filter and already explains there: a toggle with no
                visible state gets pressed twice. A screen reader is told
                as well, for the first time. -->
''' + FAV_NEW, 'the Favourites filter class', RM)
    if not CHECK:
        back_up(RM, rm_raw)
        write(RM, rm)
    print('  recipe_management.html   Favourites onto aria-pressed')

# ==========================================================================
# 2. BASE GETS THE PRESSED STATE - the same three tokens .action-filter
#    uses, so no tone is invented and no literal is added.
# ==========================================================================
BASE = alv_tree.path_of('base.html')
bs, bs_raw = read(BASE)
ANCHOR = '''      .action-secondary:hover,
      .action-secondary:focus,'''
if '.btn.action-secondary[aria-pressed="true"]' in bs:
    print('  base.html                already has the pressed secondary')
else:
    bs = swap(bs, ANCHOR,
              '''      /* PRESSED - B-1, 2 Oct 2026.

         The same answer .action-filter has had since the filter round, and
         for the reason written down there: a toggle with no visible state
         gets pressed twice. recipe_management's Favourites link was saying
         it with btn-danger versus btn-outline-danger, and losing, because
         .btn.action-secondary is (0,2,0) against btn-danger's (0,1,0).

         THE SAME THREE TOKENS as .action-filter[aria-pressed="true"]. This
         round invents no tone and adds no literal to base. */
      .btn.action-secondary[aria-pressed="true"] {
        background: var(--alv-accent-soft);
        border-color: var(--alv-accent-line);
        color: var(--alv-accent-ink);
      }

''' + ANCHOR, 'the secondary hover block', BASE)
    if not CHECK:
        back_up(BASE, bs_raw)
        write(BASE, bs)
    print('  base.html                .action-secondary[aria-pressed]')

# ==========================================================================
# 3. THE TWELVE INERT ONES. Programmatic, with an exact count per page.
# ==========================================================================
EXPECT = {
    'ingredient_base_units_management.html': 4,
    'meal_plan_shopping_list.html': 1,
    'view_meal_plan.html': 3,
    'view_recipe.html': 4,
}
done = 0
for label, n in sorted(EXPECT.items()):
    p = alv_tree.path_of(label)
    t, raw = read(p)
    hits = drifted(t)
    if not hits:
        print('  %-24s already clean' % label)
        continue
    if len(hits) != n:
        raise SystemExit('B1: %s has %d drifted control(s), expected %d'
                         % (label, len(hits), n))

    def clean(m):
        c = m.group(1)
        if not (house_roles(c) and bootstrap_colours(c)):
            return m.group(0)
        gone = set(bootstrap_colours(c))
        return 'class="%s"' % ' '.join(x for x in c.split() if x not in gone)

    t2 = re.sub(r'class="([^"]*)"', clean, t)
    # A COMMENT CANNOT BE EDITED BY THIS. The re.sub above runs on the whole
    # file, so a note quoting an old class list would be rewritten too -
    # check that the comment bytes are unchanged before writing.
    a = re.findall(r'<!--.*?-->', t, flags=re.S)
    b = re.findall(r'<!--.*?-->', t2, flags=re.S)
    if a != b:
        raise SystemExit('B1: %s - the sweep edited a COMMENT, which is a '
                         'record and not markup' % label)
    if not CHECK:
        back_up(p, raw)
        write(p, t2)
    done += len(hits)
    print('  %-24s %d class(es) cleaned' % (label, len(hits)))

print('-' * 74)

if CHECK:
    print('  --check: nothing written, gates skipped')
    print('=' * 74)
    raise SystemExit(0)

# ==========================================================================
# THE GATES.
# ==========================================================================
after = {}
for p in alv_tree.templates():
    d = drifted(read(p)[0])
    if d:
        after[alv_tree.rel(p)] = d
if after:
    raise SystemExit('B1: %d control(s) still wear both vocabularies:\n   %s'
                     % (sum(len(v) for v in after.values()),
                        '\n   '.join('%s %s' % (k, v)
                                     for k, v in sorted(after.items()))))
print('  not one control in the tree wears both vocabularies (was %d)'
      % n_before)

# THE HOUSE ROLES ARE ALL STILL THERE. Stripping a colour must not have
# stripped the role with it.
for label in list(EXPECT) + ['recipe_management.html']:
    p = alv_tree.path_of(label)
    cnt = lambda s: sum(len(house_roles(m.group(1))) for m in
                        re.finditer(r'class="([^"]*)"', s))
    a = cnt(code_only(read(p)[0]))
    b = cnt(code_only(read(p + SUFFIX)[0]))
    if a != b:
        raise SystemExit('B1: %s has %d house roles, had %d' % (label, a, b))
print('  and every house role survived - same count on all %d pages'
      % (len(EXPECT) + 1))

# THE PRESSED RULE USES ONLY TOKENS .action-filter ALREADY USES.
bs = read(BASE)[0]
m = re.search(r'\.btn\.action-secondary\[aria-pressed="true"\]\s*\{([^}]*)\}',
              bs)
if not m:
    raise SystemExit('B1: the pressed rule is not in base')
mine = set(re.findall(r'var\(([^)]+)\)', m.group(1)))
f = re.search(r'\.btn\.action-filter\[aria-pressed="true"\]\s*\{([^}]*)\}', bs)
theirs = set(re.findall(r'var\(([^)]+)\)', f.group(1))) if f else set()
if not mine or mine != theirs:
    raise SystemExit('B1: the pressed rule uses %s, .action-filter uses %s - '
                     'this round was not supposed to invent a tone'
                     % (sorted(mine), sorted(theirs)))
if re.search(r'#[0-9a-fA-F]{3,6}\b', m.group(1)):
    raise SystemExit('B1: the pressed rule carries a literal colour')
print('  the pressed rule uses %s - exactly .action-filter\'s tokens'
      % ', '.join(sorted(mine)))

# AND THE FAVOURITES LINK REALLY CARRIES THE STATE NOW.
rm = code_only(read(RM)[0])
if 'aria-pressed="{% if show_favourites %}true{% else %}false{% endif %}"' \
        not in rm:
    raise SystemExit('B1: the Favourites link does not carry aria-pressed')
if re.search(r'class="btn \{% if show_favourites %\}btn-', rm):
    raise SystemExit('B1: the Favourites link still says it with a colour')
print('  and Favourites says its state with aria-pressed, not a colour')

# THE MARKUP STILL CLOSES.
for label in list(EXPECT) + ['recipe_management.html', 'base.html']:
    p = alv_tree.path_of(label)
    c = code_only(read(p)[0])
    body = re.sub(r'<(script|style)\b.*?</\1>', '', c, flags=re.S)
    d = len(re.findall(r'<div\b', body)) - len(re.findall(r'</div\s*>', body))
    if d:
        raise SystemExit('B1: %s has %+d unbalanced <div>' % (label, d))
    for tag, close in (('if', 'endif'), ('for', 'endfor')):
        a = len(re.findall(r'\{%\s*' + tag + r'\b', c))
        b = len(re.findall(r'\{%\s*' + close + r'\s*%\}', c))
        if a != b:
            raise SystemExit('B1: %s has %s %d vs %s %d'
                             % (label, tag, a, close, b))
    css = '\n'.join(re.findall(r'<style\b[^>]*>(.*?)</style>', c, re.S))
    if css.count('{') != css.count('}'):
        raise SystemExit('B1: %s CSS does not balance' % label)
print('  every <div>, {% if %}, {% for %} and every brace still closes')

print('-' * 74)
print('  Twelve classes that did nothing are gone, and the one that was')
print('  TRYING to say something can finally be seen saying it.')
print('=' * 74)
