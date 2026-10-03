# -*- coding: utf-8 -*-
"""LZ-1 - AN IMAGE THAT IS ONE OF A LIST WAITS UNTIL IT IS LOOKED AT

Demetri, 3 Oct 2026: "When I initially select Calendar, the app seems to
be hanging. Clicking on List after going to the Calendar view takes
extremely long. Pressing on one of the Meal Plans to see it in the
calendar and its details takes very long."

==========================================================================
WHAT THE CALENDAR ACTUALLY DOES ON LOAD
==========================================================================
Its Add Recipe modal renders EVERY recipe in the database, each with

    <img src="{{ recipe.recipe_image.url }}" style="width: 50px; ...">

A hidden modal's images still download. display:none does not stop a
fetch; only `loading="lazy"` does, and not one image in this tree had it.

So opening the Calendar asks the server for every recipe photograph, at
full size, to draw it fifty pixels wide. That is the hang. It is also why
the NEXT page is slow - the browser's connections to the host are all
still busy with photographs nobody has asked to see - and why pressing a
meal plan is slow, because selectMealPlan reloads the same page and does
the whole thing again.

==========================================================================
THE RULE, AND WHAT IT DELIBERATELY LEAVES ALONE
==========================================================================
AN IMAGE THAT IS ONE OF A LIST waits. One built per row or per card -
whether Django builds the list with a for loop or a script builds it from
JSON - is an image the reader may never scroll to.

NOT LAZY, and each for its own reason:

    the logo, the header profile photo    above the fold. Lazy there
                                          costs a paint, it does not save
                                          a fetch.
    a detail page's hero                  the one image the page is about
    anything in a PRINT or PDF template   A PDF RENDERER DOES NOT SCROLL.
                                          recipe_pdf, physical_invoice,
                                          cash_receipt and the lease all
                                          draw one page with no viewport
                                          to enter, and a lazy image
                                          there can come out blank. This
                                          is the one that would have been
                                          a silent data loss.

Backups: .bak_lazyimg. Idempotent. --check writes nothing.
"""
import os
import re
import sys

CHECK = '--check' in sys.argv
SUFFIX = '.bak_lazyimg'
ROOT = os.getcwd()
CRLF = {}
ADD = ' loading="lazy" decoding="async"'

sys.path.insert(0, ROOT)
import alv_tree

# An image whose CLASS says it is a card in a list. These are built by a
# script from JSON, so no for loop surrounds them in the source - the
# class is what carries the fact. book-detail-image is NOT here: that is
# the one image the detail panel is about.
LIST_CLASSES = ('recipe-selector-card-image', 'book-recipe-card-image',
                'recipe-image', 'recipe-list-image')

# A renderer with no viewport. Nothing in these is ever lazy.
PRINT_PAGES = ('recipe_pdf.html', 'invoices/physical_invoice.html',
               'receipts/cash_receipt.html', 'generate_lease_agreement.html',
               'components/pdf_viewer.html')


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
            raise SystemExit('LZ1: %s is not a byte copy' % bak)


def classes_of(tag):
    """Every class TOKEN on the tag. Not a substring search: recipe-image
    is not book-recipe-card-image, and `\\b` sits happily between a hyphen
    and a letter."""
    m = re.search(r'class="([^"]*)"', tag)
    return set(m.group(1).split()) if m else set()


def targets(src):
    """Every <img> in SOURCE that is one of a list, as (start, tag).

    Measured on the MARKUP, with comments blanked - an <img> written out
    inside a comment explaining this round is not an image. Two ways in:

      inside a {% for %}        Django builds the list
      a class from LIST_CLASSES a script builds it from JSON

    The for-depth is counted rather than matched with a regex, because a
    loop may hold another loop - the calendar's week rows do.
    """
    code = alv_tree.code_only(src)
    out = []
    depth = 0
    for m in re.finditer(r'\{%\s*(?:for|endfor)\b|<img\b[^>]*>', code):
        tag = m.group(0)
        if tag.startswith('{%'):
            depth += -1 if 'endfor' in tag else 1
            continue
        if depth > 0 or (classes_of(tag) & set(LIST_CLASSES)):
            out.append((m.start(), src[m.start():m.start() + len(tag)]))
    return out


print('=' * 74)
print('LZ-1 - AN IMAGE THAT IS ONE OF A LIST WAITS%s'
      % (' - CHECK ONLY' if CHECK else ''))
print('=' * 74)

done = 0
pages = 0
for p in sorted(alv_tree.templates()):
    rel = alv_tree.rel(p)
    if rel in PRINT_PAGES:
        continue
    t, raw = read(p)
    hits = [h for h in targets(t) if 'loading=' not in h[1]]
    if not hits:
        continue
    # LAST FIRST, so an earlier offset is still the offset it was.
    nt = t
    for start, tag in reversed(hits):
        if nt[start:start + len(tag)] != tag:
            raise SystemExit('LZ1: %s moved under me at %d' % (rel, start))
        nt = nt[:start] + '<img' + ADD + nt[start + 4:]
    if not CHECK:
        back_up(p, raw)
        write(p, nt)
    pages += 1
    done += len(hits)
    print('  %-44s %d image(s)' % (rel, len(hits)))

print('  %d image(s) on %d page(s)' % (done, pages))
print('-' * 74)

if CHECK:
    print('  --check: nothing written, gates skipped')
    print('=' * 74)
    raise SystemExit(0)

# ==========================================================================
# THE GATES.
# ==========================================================================
# 1. THE CALENDAR'S MODAL - the image this round is about.
cal = alv_tree.path_of('meal_plan_calendar.html')
src = read(cal)[0]
modal = [tag for _, tag in targets(src)
         if 'recipe_image.url' in tag and 'width: 50px' in tag]
if len(modal) != 1:
    raise SystemExit('LZ1: expected one modal thumbnail on the calendar, '
                     'found %d' % len(modal))
if 'loading="lazy"' not in modal[0]:
    raise SystemExit('LZ1: the calendar modal image is not lazy - this '
                     'round did nothing about the hang')
print('  the Add Recipe modal thumbnail is lazy')

# 2. AND IT IS STILL INSIDE A HIDDEN MODAL, which is what makes it free.
i = src.find('id="recipeList"')
if i < 0 or src.find(modal[0]) < i:
    raise SystemExit('LZ1: the thumbnail is no longer inside the recipe '
                     'list - the premise of gate 1 has moved')
print('  and still inside the hidden list, so nothing is fetched until it '
      'opens')

# 3. NO IMAGE IN A PRINT TEMPLATE IS LAZY. A PDF renderer has no viewport.
bad = []
for rel in PRINT_PAGES:
    try:
        s = read(alv_tree.path_of(os.path.basename(rel)))[0]
    except Exception:
        continue
    if 'loading="lazy"' in alv_tree.code_only(s):
        bad.append(rel)
if bad:
    raise SystemExit('LZ1: a print template got a lazy image: %s'
                     % ', '.join(bad))
print('  no image in a print or PDF template is lazy')

# 4. NOR THE LOGO, NOR THE HEADER PHOTO. Above the fold, so lazy costs a
#    paint and saves nothing.
b = read(alv_tree.path_of('base.html'))[0]
for probe in ('alivente_online_logo.png', 'profile_photo.url'):
    for tag in re.findall(r'<img\b[^>]*>', alv_tree.code_only(b)):
        if probe in tag and 'loading=' in tag:
            raise SystemExit('LZ1: %s in base became lazy' % probe)
print('  the logo and the header photo in base are untouched')

# 5. NOR A DETAIL PAGE'S HERO - the control that proves the rule narrows.
rm = read(alv_tree.path_of('recipe_management.html'))[0]
hero = [tag for tag in re.findall(r'<img\b[^>]*>', alv_tree.code_only(rm))
        if 'book-detail-image' in tag]
if len(hero) != 1:
    raise SystemExit('LZ1: expected one book-detail-image, found %d'
                     % len(hero))
if 'loading=' in hero[0]:
    raise SystemExit('LZ1: CONTROL FAILED - the detail hero became lazy, '
                     'so the rule is matching by name and not by role')
print('  CONTROL: the book detail hero beside it did NOT - it is one '
      'image, not one of a list')

# 6. EVERY TAG STILL CLOSES, AND NO ATTRIBUTE WAS DOUBLED.
bad = []
for p in sorted(alv_tree.templates()):
    s = read(p)[0]
    for tag in re.findall(r'<img\b[^>]*>', s):
        if tag.count('loading=') > 1 or tag.count('decoding=') > 1:
            bad.append('%s %s' % (alv_tree.rel(p), tag[:60]))
if bad:
    raise SystemExit('LZ1: %d doubled attribute(s):\n   %s'
                     % (len(bad), '\n   '.join(bad[:4])))
print('  no image carries the attribute twice - a second run is a no-op')

print('-' * 74)
print('  %d images on %d pages now wait to be looked at.' % (done, pages))
print('  The Calendar asked the server for every recipe photograph in the')
print('  database, at full size, to draw it fifty pixels wide.')
print('=' * 74)
