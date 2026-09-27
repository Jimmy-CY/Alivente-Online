# -*- coding: utf-8 -*-
"""SECTION G, ROUND G2 - THE ACTION BAR JOINS THE HOUSE

Three faults, all of them Personal, all of them counted before being fixed.

1. THE BAR SITS ABOVE THE TITLE on eight pages.
   The house order is TITLE, then bar: 68 pages do that and 8 do not, and
   all 8 are Personal. It is markup order and nothing else - the bar was
   written above the coloured banner long before G1, and taking the banner
   off is what made it visible. The block moves; not a byte of it changes.

2. A BACK BUTTON SAYS WHERE IT GOES.
   94 Back controls in this tree say exactly "Back". Twelve say something
   longer and eleven of those are Personal: "Back to Recipe Management" x4,
   "Back to Recipe" x2, "Back to Recipes", "Back to Meal Plan", "Back to
   Meal Plans", "Back to Import". The VISIBLE label becomes "Back"; the
   aria-label keeps the destination, because a screen reader has no
   surrounding page to read it from.

   TWO ARE LEFT ALONE, on purpose:
     create_meal_plan.html          says "Cancel" - that is a form, and
                                    Cancel may well be the right word
     projects/project_task_list.html says {% if greek %}Πίσω{% else %}Back
                                    - a language toggle, not a stray label

3. A BACK BUTTON HAS NO COLOUR.
   The house Back is `btn action-back` and nothing else - properties.html
   line 74, and 80-odd more. Fourteen carry a Bootstrap colour class that
   paints them: thirteen btn-secondary (the grey pill) and one btn-success
   (view_recipe, green). Every one of the fourteen is Personal. The colour
   class comes off; the word and the link are untouched.

AND ONE THING FOUND WHILE COUNTING (2): four of these controls put their
label as BARE TEXT rather than inside <span class="action-back-label">, so
base cannot hide the word on a phone and the control is a full-width pill
where every other page shows a 44px arrow. They get the span.

Backups: .bak_bartop, written with the ORIGINAL's line endings.
Idempotent. --check prints and writes nothing.
"""
import os
import re
import sys

CHECK = '--check' in sys.argv
HERE = os.getcwd()
ROOT = os.path.join(HERE, 'pages', 'templates')
SUFFIX = '.bak_bartop'
CRLF = {}

TITLE_CLS = 'page-title-h2'
SUB_CLS = 'page-subtitle-h4'
BAR_CLS = 'page-action-buttons'
BACK_CLS = 'action-back'
LABEL_CLS = 'action-back-label'

# (1) The eight whose bar sits above the title. Counted, not guessed.
MOVE = [
    'categories_management.html',
    'ingredient_base_units_management.html',
    'map_ingredients_nutrition.html',
    'meal_plan_shopping_list.html',
    'measurement_units_management.html',
    'preview_imported_recipe.html',
    'unit_conversions_management.html',
    'unit_conversions_wizard.html',
]

# (2) + (3) Every file holding an action-back that needs either fix, and
# what should be true of each one AFTERWARDS. Written out so a template that
# has changed stops the round instead of being rewritten blind.
#   (file, index within the file, label before, colour class before)
BACKS = [
    ('categories_management.html', 0, 'Back to Recipe Management', None),
    ('create_meal_plan.html', 0, 'Cancel', 'btn-secondary'),
    ('ingredient_base_units_management.html', 0,
     'Back to Recipe Management', 'btn-secondary'),
    ('map_ingredients_nutrition.html', 0, 'Back to Recipe', 'btn-secondary'),
    ('map_ingredients_nutrition.html', 1, 'Back', 'btn-secondary'),
    ('meal_plan_calendar.html', 0, 'Back', 'btn-secondary'),
    ('meal_plan_shopping_list.html', 0, 'Back to Meal Plan', 'btn-secondary'),
    ('meal_plans.html', 0, 'Back to Recipes', 'btn-secondary'),
    ('measurement_units_management.html', 0,
     'Back to Recipe Management', 'btn-secondary'),
    ('preview_imported_recipe.html', 0, None, 'btn-secondary'),   # conditional
    ('unit_conversions_management.html', 0,
     'Back to Recipe Management', 'btn-secondary'),
    ('unit_conversions_wizard.html', 0, 'Back to Recipe', 'btn-secondary'),
    ('unit_conversions_wizard.html', 1, 'Back', 'btn-secondary'),
    ('view_meal_plan.html', 0, 'Back to Meal Plans', 'btn-secondary'),
    ('view_recipe.html', 0, 'Back', 'btn-success'),
    # FOUND BY RE-COUNTING, AND ONLY BY RE-COUNTING. The first census read
    # only the controls INSIDE a .page-action-buttons bar, so every Back
    # that sits outside one was invisible to it - including two of the
    # loudest, on pages the round is meant to be about. A file-wide count
    # found four more. (Lesson 38: the measuring instrument is the most
    # common liar, and a scope drawn from one is the wrong scope.)
    ('celebration_management.html', 0, 'Back to Dashboard', 'btn-secondary'),
    ('recipe_management.html', 0, 'Back', 'btn-success'),
    ('lease_timeline.html', 0, 'Back to Tenants', None),
]
# The label is left exactly as it is on these. See the docstring.
KEEP_LABEL = {('create_meal_plan.html', 0),
              ('projects/project_task_list.html', 0)}
# Never touched at all - no colour to strip and no label to shorten.
SKIP = {'projects/project_task_list.html'}
# THE OTHER TWO THE FILE-WIDE COUNT FOUND, and why each is left:
#   act_expense.html [3]   "Back to overview" - a DRILL-DOWN return inside a
#                          report, not a page Back. It names where it goes
#                          because it goes somewhere on the same page.
#   error_pages/connectivity_error.html  "Go Back" - an error page with no
#                          action bar and no arrow. Its own thing.

COLOUR = re.compile(r'\bbtn-(?:secondary|success|light|info|primary|dark|'
                    r'warning|danger)\b')

HTML_C = re.compile(r'<!--.*?-->', re.S)
DJ_CB = re.compile(r'\{%\s*comment\s*%\}.*?\{%\s*endcomment\s*%\}', re.S | re.I)
DJ_C = re.compile(r'\{#.*?#\}', re.S)
STYLE = re.compile(r'<style\b[^>]*>(.*?)</style\s*>', re.S | re.I)
SCRIPT = re.compile(r'<script\b[^>]*>(.*?)</script\s*>', re.S | re.I)


def read(path):
    with open(path, 'rb') as fh:
        raw = fh.read()
    CRLF[path] = b'\r\n' in raw
    return raw.decode('utf-8')


def write(path, text):
    data = text.encode('utf-8')
    if CRLF.get(path):
        data = data.replace(b'\r\n', b'\n').replace(b'\n', b'\r\n')
    else:
        data = data.replace(b'\r\n', b'\n')
    with open(path, 'wb') as fh:
        fh.write(data)


def _sp(m):
    return re.sub(r'[^\n]', ' ', m.group(0))


def blanked(t):
    """Comments blanked on the RAW text FIRST, then script and style bodies.

    The house order - comments across the whole file, then find <style> -
    is defeated by accept="image/*", whose /* opens a CSS comment that runs
    to the first */ inside the stylesheet (lesson 58)."""
    t = HTML_C.sub(_sp, t)
    t = DJ_CB.sub(_sp, t)
    t = DJ_C.sub(_sp, t)
    for rx in (STYLE, SCRIPT):
        out, pos = [], 0
        for m in rx.finditer(t):
            out.append(t[pos:m.start(1)])
            out.append(re.sub(r'[^\n]', ' ', m.group(1)))
            pos = m.end(1)
        out.append(t[pos:])
        t = ''.join(out)
    return t


def div_end(scan, start):
    """Offset just PAST the </div> that closes the div opening at `start`."""
    d, i = 0, start
    for m in re.finditer(r'</?div\b', scan[start:]):
        d += 1 if m.group(0) == '<div' else -1
        if d == 0:
            i = start + m.end()
            j = scan.find('>', i)
            if j < 0:
                raise SystemExit('G2: unterminated </div> at %d' % i)
            return j + 1
    raise SystemExit('G2: unbalanced <div> from offset %d' % start)


def bar_span(text):
    """(start, end) of the FIRST .page-action-buttons block."""
    scan = blanked(text)
    m = re.search(r'<div[^>]*class="[^"]*(?<![\w-])' + BAR_CLS
                  + r'(?![\w-])[^"]*"[^>]*>', scan)
    if not m:
        return None
    return (m.start(), div_end(scan, m.start()))


def head_end(text):
    """Offset just past the page head - the title, and the subtitle when
    there is one, including the {% if %} that may wrap it."""
    scan = blanked(text)
    h = re.search(r'<h2[^>]*class="[^"]*(?<![\w-])' + TITLE_CLS
                  + r'(?![\w-])[^"]*"[^>]*>.*?</h2\s*>', scan, re.S)
    if not h:
        return None
    end = h.end()
    # {% if x %}<h4 class="page-subtitle-h4">...</h4>{% endif %}, or a bare
    # <h4>. Anything else and the head stops at the title.
    tail = re.match(r'\s*(?:\{%[^%]*%\})?\s*<h4[^>]*class="[^"]*'
                    + SUB_CLS + r'[^"]*"[^>]*>.*?</h4\s*>'
                    r'(?:\s*\{%\s*endif\s*%\})?', scan[end:], re.S)
    if tail:
        end += tail.end()
    return end


def backs_in(text):
    """Every action-back control, as (start, end) over the WHOLE element."""
    scan = blanked(text)
    out = []
    for m in re.finditer(r'<(a|button|span)\b[^>]*class="([^"]*)"[^>]*>',
                         scan):
        if BACK_CLS not in m.group(2).split():
            continue
        tag = m.group(1)
        d, end = 0, None
        for t in re.finditer(r'</?%s\b' % tag, scan[m.start():]):
            d += 1 if t.group(0) == '<' + tag else -1
            if d == 0:
                j = scan.find('>', m.start() + t.end())
                end = j + 1
                break
        if end is None:
            raise SystemExit('G2: unbalanced <%s> for an action-back' % tag)
        out.append((m.start(), end))
    return out


LABEL_SPAN = re.compile(r'<span[^>]*class="[^"]*(?<![\w-])' + LABEL_CLS
                        + r'(?![\w-])[^"]*"[^>]*>(.*?)</span\s*>', re.S)
ARROW = re.compile(r'(<i\b[^>]*fa-arrow-left[^>]*>\s*</i\s*>)', re.S)


def fix_back(html, relabel):
    """One action-back control: colour class off, and - when `relabel` -
    the visible word reduced to Back inside the label span base hides on a
    phone. The href, the aria-label and every template tag are untouched."""
    was = html
    changed = []

    def strip(m):
        cls = ' '.join(c for c in m.group(1).split() if not COLOUR.match(c))
        return 'class="%s"' % cls

    new = re.sub(r'class="([^"]*)"',
                 lambda m: (strip(m) if BACK_CLS in m.group(1).split()
                            else m.group(0)), html, count=1)
    if new != html:
        changed.append('colour')
    html = new

    if relabel:
        if LABEL_SPAN.search(html):
            new = LABEL_SPAN.sub(
                lambda m: m.group(0)[:m.start(1) - m.start()] + ' Back'
                + m.group(0)[m.end(1) - m.start():], html, count=1)
        else:
            # Bare text after the arrow - give it the span the other 94 have,
            # or base cannot hide the word on a phone.
            a = ARROW.search(html)
            if not a:
                raise SystemExit('G2: an action-back with neither a label '
                                 'span nor an arrow: %s' % html[:80])
            close = html.rfind('</')
            new = (html[:a.end()]
                   + '<span class="%s"> Back</span>' % LABEL_CLS
                   + html[close:])
        if new != html:
            changed.append('label')
        html = new
    # WHAT THE NEW LABEL NO LONGER SAYS. preview_imported_recipe's word was
    # {% if mode == 'import' %}Back to Import{% else %}Back to Recipes
    # {% endif %}, and reducing it to Back drops that conditional ON PURPOSE.
    # The file-level tag-count check is right to notice; it is handed this
    # list so it allows exactly these and nothing else. The aria-label keeps
    # its own copy of the same conditional, which is why the tags do not
    # vanish from the file.
    dropped = []
    for t in set(re.findall(r'\{\{.*?\}\}|\{%.*?%\}', was, re.S)):
        dropped += [t] * max(0, was.count(t) - html.count(t))
    return html, changed, dropped


def label_of(html):
    m = LABEL_SPAN.search(html)
    inner = m.group(1) if m else ARROW.sub('', html)
    inner = re.sub(r'<[^>]+>', '', inner)
    if '{%' in inner or '{{' in inner:
        return None                       # conditional - not one word
    return ' '.join(inner.split()) or None


def patch(rel):
    path = os.path.join(ROOT, rel)
    if not os.path.isfile(path):
        raise SystemExit('G2: %s is not on disk' % rel)
    text = read(path)
    before = text
    moved = False
    fixes = []
    allow = []                  # tags a relabel deliberately drops

    # ---- (1) the bar goes below the head ---------------------------------
    if rel in MOVE:
        span = bar_span(text)
        he = head_end(text)
        if span is None or he is None:
            raise SystemExit('G2: %s - no bar (%s) or no head (%s)'
                             % (rel, span, he))
        if span[0] < he:
            block = text[span[0]:span[1]]
            # the run of whitespace the block leaves behind goes with it
            rest = text[span[1]:]
            eat = re.match(r'[ \t]*\r?\n', rest)
            cut_end = span[1] + (eat.end() if eat else 0)
            text = text[:span[0]] + text[cut_end:]
            he = head_end(text)
            if he is None:
                raise SystemExit('G2: %s - the head vanished with the bar'
                                 % rel)
            nl = '\n'
            text = text[:he] + nl + block + text[he:]
            moved = True
        # else: already below - idempotent

    # ---- (2) and (3) the Back controls -----------------------------------
    if rel not in SKIP:
        spans = backs_in(text)
        wanted = [b for b in BACKS if b[0] == rel]
        if wanted and len(spans) <= max(b[1] for b in wanted):
            raise SystemExit('G2: %s - %d action-back control(s), but index '
                             '%d was expected'
                             % (rel, len(spans), max(b[1] for b in wanted)))
        for _f, idx, want_label, want_colour in sorted(wanted,
                                                       key=lambda x: -x[1]):
            s, e = spans[idx]
            html = text[s:e]
            got = label_of(html)
            got_col = COLOUR.search(html)
            got_col = got_col.group(0) if got_col else None
            # Already done? Then this file has been patched; say nothing.
            if got_col is None and (got == 'Back'
                                    or (rel, idx) in KEEP_LABEL
                                    or want_label is None):
                continue
            if got != want_label or got_col != want_colour:
                raise SystemExit(
                    'G2: %s [%d] - expected label %r colour %r, found %r %r'
                    % (rel, idx, want_label, want_colour, got, got_col))
            new, changed, dropped = fix_back(html,
                                             (rel, idx) not in KEEP_LABEL)
            if changed:
                text = text[:s] + new + text[e:]
                fixes.append('%d:%s' % (idx, '+'.join(changed)))
                allow += dropped

    # ---- self-checks BEFORE anything is written --------------------------
    if text == before:
        return None
    for tag in set(re.findall(r'\{\{.*?\}\}|\{%.*?%\}', before, re.S)):
        if before.count(tag) - allow.count(tag) != text.count(tag):
            raise SystemExit('G2: %s - %s appeared %d times and now %d '
                             '(%d deliberately dropped)'
                             % (rel, tag.strip()[:50], before.count(tag),
                                text.count(tag), allow.count(tag)))
    for what in ('<div', '</div>', 'href=', 'aria-label='):
        if before.count(what) != text.count(what):
            raise SystemExit('G2: %s - %s count moved %d -> %d'
                             % (rel, what, before.count(what),
                                text.count(what)))
    if rel in MOVE:
        span, he = bar_span(text), head_end(text)
        if span is None or he is None or span[0] < he:
            raise SystemExit('G2: %s - the bar is still above the head' % rel)
    if len(backs_in(text)) != len(backs_in(before)):
        raise SystemExit('G2: %s - an action-back was lost' % rel)

    if not CHECK:
        bak = path + SUFFIX
        if not os.path.exists(bak):
            CRLF[bak] = CRLF.get(path)
            write(bak, before)
        write(path, text)
    return (moved, fixes)


LATER = [
    ('alv_rounds.py',
     "    '.bak_pagetitle',\n]",
     "    '.bak_pagetitle',\n    '.bak_bartop',\n]"),
    ('Push-PendingChanges.ps1',
     "    'test_page_title.py'",
     "    'test_page_title.py'\n    'test_bar_top.py'"),
]


def patch_later():
    done = 0
    for name, old, new in LATER:
        path = os.path.join(HERE, name)
        text = read(path)
        if new in text:                  # decided by the NEW text alone (47)
            continue
        if text.count(old) != 1:
            raise SystemExit('G2/LATER: anchor matched %d times in %s'
                             % (text.count(old), name))
        if not CHECK:
            bak = path + SUFFIX
            if not os.path.exists(bak):
                CRLF[bak] = CRLF.get(path)
                write(bak, text)
            write(path, text.replace(old, new))
        done += 1
    return done


def main():
    print('=' * 74)
    print('SECTION G, ROUND G2 - THE ACTION BAR JOINS THE HOUSE - %s'
          % ('CHECK ONLY' if CHECK else 'APPLYING'))
    print('=' * 74)
    files = sorted(set(MOVE) | set(b[0] for b in BACKS))
    moves = touched = 0
    for rel in files:
        r = patch(rel)
        if r is None:
            print('  %-42s already applied' % rel)
            continue
        moved, fixes = r
        touched += 1
        moves += 1 if moved else 0
        print('  %-42s %-6s %s' % (rel, 'MOVED' if moved else '',
                                   ', '.join(fixes)))
    later = patch_later()
    print('-' * 74)
    print('  %d file(s) changed; %d bar(s) moved below the head; '
          '%d LATER edit(s).' % (touched, moves, later))
    print()
    print('  LEFT ALONE, on purpose:')
    print('    create_meal_plan.html        its word is "Cancel" - a form, '
          'not a list')
    print('    projects/project_task_list   its label is a Greek/English '
          'toggle')
    print('=' * 74)


if __name__ == '__main__':
    main()
