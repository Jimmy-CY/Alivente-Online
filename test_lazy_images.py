# -*- coding: utf-8 -*-
"""test_lazy_images.py - Section LZ round LZ-1, 3 Oct 2026.

Demetri, 3 Oct 2026: "When I initially select Calendar, the app seems to
be hanging. Clicking on List after going to the Calendar view takes
extremely long."

The Calendar's Add Recipe modal renders EVERY recipe in the database,
each with <img src="{{ recipe.recipe_image.url }}">. A HIDDEN MODAL'S
IMAGES STILL DOWNLOAD - display:none does not stop a fetch, only
loading="lazy" does, and before this round not one image in this tree had
it. So opening the Calendar asked the server for every recipe photograph,
at full size, to draw it fifty pixels wide.

SECTION 3 IS THE ONE THAT MATTERS, and it is driven in a browser. The
claim is not "the attribute is present" - it is "the browser does not
fetch it". A page with four lazy images inside a hidden container is
loaded against a server that COUNTS requests, and the count must be zero.
Then the container is shown and the count must rise. An attribute
asserted in the markup is not evidence that a browser honoured it.

AND SECTION 4 IS THE ONE THAT COULD HAVE COST DATA. A PDF renderer has no
viewport to scroll into, so a lazy image in a print template can come out
blank - on an invoice, a receipt or a lease. Those five templates are
excluded by name and the suite holds the list.
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
import ast
import shutil
import tempfile

ROOT = os.getcwd()
sys.path.insert(0, ROOT)
try:
    from alv_rounds import as_left_by
except Exception:
    as_left_by = None
import alv_tree

SUFFIX = '.bak_lazyimg'
ME = 'test_lazy_images.py'
PATCHER = 'apply_lazy_images.py'
PS1 = 'Push-PendingChanges.ps1'

SCRATCH = tempfile.mkdtemp(prefix='alv_lazyimg_')

passed = failed = skipped = 0


def ok(cond, msg, detail=''):
    global passed, failed
    if cond:
        passed += 1
        print('  ok   %s' % msg)
    else:
        failed += 1
        print('  FAIL %s' % msg)
        if detail:
            for line in str(detail).split('\n')[:8]:
                print('         %s' % line)
    return cond


def skip(msg, why):
    global skipped
    skipped += 1
    print('  --   %s  (%s)' % (msg, why))


def read(p):
    with open(p, encoding='utf-8', errors='replace') as f:
        return f.read().replace('\r\n', '\n')


def head(t):
    print('\n' + '=' * 74 + '\n' + t + '\n' + '=' * 74)


def now(p):
    return as_left_by(p, SUFFIX, read) if as_left_by else read(p)


def was(p):
    return read(p + SUFFIX) if os.path.isfile(p + SUFFIX) else ''


def code(p):
    return alv_tree.code_only(now(p))

def path_rel(rel):
    """A template by its path RELATIVE TO A ROOT, not by its basename.
    path_of takes a basename and three of the print templates live in a
    subdirectory - invoices/ and receipts/ - so asking for the basename
    raises and the gate below skipped three of the five it exists for."""
    for p in alv_tree.templates():
        if alv_tree.rel(p).replace(os.sep, '/') == rel:
            return p
    return None



def source(*parts):
    """A python file of this project, BY ITS PATH, not by walking for it.

    A walk here would put this suite on the debt register that
    test_waiting_down keeps - os.walk over a root a file built for itself
    is exactly what alv_tree exists to replace - and it would find the
    first file of that name anywhere under the tree, backups included.
    Named, so a file that moves makes the gate SKIP and say so rather
    than quietly measure something else."""
    p = os.path.join(ROOT, *parts)
    return read(p) if os.path.isfile(p) else ''


PRINT_PAGES = ('recipe_pdf.html', 'invoices/physical_invoice.html',
               'receipts/cash_receipt.html', 'generate_lease_agreement.html',
               'components/pdf_viewer.html')
LIST_CLASSES = ('recipe-selector-card-image', 'book-recipe-card-image',
                'recipe-image', 'recipe-list-image')
CAL = alv_tree.path_of('meal_plan_calendar.html')


def imgs(src):
    return re.findall(r'<img\b[^>]*>', alv_tree.code_only(src))


def in_a_list(src):
    """Every <img> in SOURCE that is one of a list, with its for-depth.

    The depth is COUNTED, not matched: the calendar nests a loop inside a
    loop for its week rows, and a regex from {% for %} to {% endfor %}
    would close the outer one on the inner one's end tag."""
    c = alv_tree.code_only(src)
    out, depth = [], 0
    for m in re.finditer(r'\{%\s*(?:for|endfor)\b|<img\b[^>]*>', c):
        tag = m.group(0)
        if tag.startswith('{%'):
            depth += -1 if 'endfor' in tag else 1
        elif depth > 0 or (set(re.findall(r'class="([^"]*)"', tag)[0].split())
                           & set(LIST_CLASSES) if 'class="' in tag else False):
            out.append(tag)
    return out


# ==========================================================================
head('1. THE CENSUS - WHICH IMAGES WAIT, AND WHICH DO NOT')
# ==========================================================================
lazy, eager, pages = [], [], set()
for p in sorted(alv_tree.templates()):
    rel = alv_tree.rel(p)
    for tag in imgs(now(p)):
        (lazy if 'loading="lazy"' in tag else eager).append((rel, tag))
        if 'loading="lazy"' in tag:
            pages.add(rel)
ok(len(lazy) == 14, '%d image(s) wait, on %d page(s)' % (len(lazy), len(pages)),
   '\n'.join('%s %s' % (r, t[:60]) for r, t in lazy[:4]))
ok(len(eager) >= 20, 'and %d do not' % len(eager))

# EVERY LAZY IMAGE IS ONE OF A LIST. Asked of the markup, not of a list of
# filenames: a new card image added to a loop next month is covered, and an
# attribute put on a hero by hand would be caught.
wrong = []
for p in sorted(alv_tree.templates()):
    listed = set(in_a_list(now(p)))
    for tag in imgs(now(p)):
        if 'loading="lazy"' in tag and tag not in listed:
            wrong.append('%s %s' % (alv_tree.rel(p), tag[:60]))
ok(not wrong, 'and every one of them is one of a list', '\n'.join(wrong[:4]))

missing = []
for p in sorted(alv_tree.templates()):
    if alv_tree.rel(p) in PRINT_PAGES:
        continue
    for tag in in_a_list(now(p)):
        if 'loading="lazy"' not in tag:
            missing.append('%s %s' % (alv_tree.rel(p), tag[:60]))
ok(not missing, 'and every image that is one of a list waits',
   '\n'.join(missing[:4]))

# ==========================================================================
head('2. THE CALENDAR - THE PAGE THAT WAS HANGING')
# ==========================================================================
cal = now(CAL)
modal = [t for t in imgs(cal) if 'recipe_image.url' in t and 'width: 50px' in t]
ok(len(modal) == 1, 'the Add Recipe modal has one thumbnail per recipe')
if modal:
    ok('loading="lazy"' in modal[0], '  and it waits')
    ok('decoding="async"' in modal[0],
       '  and decodes off the main thread, so a photograph that does '
       'arrive does not stall the page')
old = was(CAL)
if old:
    omodal = [t for t in imgs(old) if 'recipe_image.url' in t
              and 'width: 50px' in t]
    ok(omodal and 'loading=' not in omodal[0],
       'CONTROL: before this round it did not, which is the hang')
else:
    skip('CONTROL: before this round it did not', 'no backup')

# AND IT IS STILL INSIDE A HIDDEN LIST, which is what makes it free.
i = alv_tree.code_only(cal).find('id="recipeList"')
ok(i >= 0 and alv_tree.code_only(cal).find(modal[0]) > i,
   'and it is still inside the hidden recipe list')

# ONE PER RECIPE, FROM EVERY RECIPE. The size of the problem, named.
v = source('pages', 'views', 'recipes', 'meal_planning.py')
ok(v and 'all_recipes = Recipe.objects.all()' in v,
   'the view still hands the modal every recipe in the database - this '
   'round makes that free to RENDER, it does not make the page small')

# ==========================================================================
head('3. A BROWSER, AND A SERVER THAT COUNTS REQUESTS')
# ==========================================================================
# THE CLAIM IS NOT "THE ATTRIBUTE IS THERE". It is "the browser does not
# fetch it", and only a browser can say that. Four images in a hidden
# container, served by a counting server: zero requests while it is
# hidden, more than zero once it is shown.
try:
    from playwright.sync_api import sync_playwright
except Exception:
    sync_playwright = None

if sync_playwright is None:
    skip('a hidden lazy image is not fetched', 'playwright not installed')
    skip('CONTROL: a hidden eager image IS', 'playwright not installed')
else:
    import threading
    import http.server

    HITS = []

    class H(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            HITS.append(self.path)
            png = (b'\x89PNG\r\n\x1a\n' + b'\x00' * 64)
            self.send_response(200)
            self.send_header('Content-Type', 'image/png')
            self.send_header('Content-Length', str(len(png)))
            self.end_headers()
            self.wfile.write(png)

        def log_message(self, *a):
            pass

    srv = http.server.HTTPServer(('127.0.0.1', 0), H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    port = srv.server_address[1]

    def page(attr):
        rows = ''.join(
            '<img src="http://127.0.0.1:%d/%s-%d.png" %s width="50" '
            'height="50">' % (port, attr or 'eager', k, attr) for k in range(4))
        return ('<!doctype html><html><head><meta charset="utf-8"></head>'
                '<body><div id="box" style="display:none">%s</div>'
                '<div style="height:3000px"></div></body></html>' % rows)

    def run(attr):
        del HITS[:]
        with sync_playwright() as pw:
            b = pw.chromium.launch()
            p = b.new_page(viewport={'width': 400, 'height': 600})
            p.set_content(page(attr))
            p.wait_for_timeout(400)
            hidden = len(HITS)
            p.evaluate("document.getElementById('box').style.display='block'")
            p.wait_for_timeout(600)
            shown = len(HITS)
            b.close()
        return hidden, shown

    h, s = run('loading="lazy"')
    ok(h == 0, 'HIDDEN, a lazy image is not fetched - %d request(s)' % h)
    ok(s >= 1, 'SHOWN, it is - %d request(s)' % s)
    h2, s2 = run('')
    ok(h2 >= 1,
       'CONTROL: the same four images with no attribute ARE fetched while '
       'hidden - %d request(s). display:none does not stop a fetch.' % h2)
    srv.shutdown()

# ==========================================================================
head('4. NOT IN A PRINT TEMPLATE - A PDF RENDERER DOES NOT SCROLL')
# ==========================================================================
# This is the one that would have been a silent data loss: a lazy image on
# an invoice, a receipt or a lease comes out BLANK, and nothing says so
# except a customer holding a piece of paper with a hole in it.
for rel in PRINT_PAGES:
    p = path_rel(rel)
    if p is None:
        skip(rel, 'not on disk')
        continue
    bad = [t for t in imgs(now(p)) if 'loading=' in t]
    ok(not bad, '%-32s no lazy image' % rel, '\n'.join(b[:60] for b in bad))

# AND THEY DO HOLD IMAGES, or the gate above passes by being empty.
holds = [rel for rel in PRINT_PAGES
         if path_rel(rel) and imgs(now(path_rel(rel)))]
ok(len(holds) >= 4,
   'CONTROL: %d of the %d print templates hold an image, so that gate is '
   'not passing by being empty' % (len(holds), len(PRINT_PAGES)))

# ==========================================================================
head('5. NOR ABOVE THE FOLD')
# ==========================================================================
b = now(alv_tree.path_of('base.html'))
for probe, what in (('alivente_online_logo.png', 'the logo'),
                    ('profile_photo.url', 'the header photo')):
    bad = [t for t in imgs(b) if probe in t and 'loading=' in t]
    ok(not bad, '%-18s in base is not lazy' % what)

rm = now(alv_tree.path_of('recipe_management.html'))
hero = [t for t in imgs(rm) if 'book-detail-image' in t]
ok(len(hero) == 1, 'the recipe book has one detail hero')
ok(hero and 'loading=' not in hero[0],
   'CONTROL: and it did NOT become lazy, though a card image two hundred '
   'lines away did - the rule matches role, not name')

# ==========================================================================
head('6. AND NO ATTRIBUTE IS DOUBLED')
# ==========================================================================
dbl = []
for p in sorted(alv_tree.templates()):
    for tag in re.findall(r'<img\b[^>]*>', now(p)):
        if tag.count('loading=') > 1 or tag.count('decoding=') > 1:
            dbl.append('%s %s' % (alv_tree.rel(p), tag[:60]))
ok(not dbl, 'no image carries it twice, so a second run is a no-op',
   '\n'.join(dbl[:4]))

# ==========================================================================
head('7. REGISTERED')
# ==========================================================================
rounds = read(os.path.join(ROOT, 'alv_rounds.py'))
ok("'%s'" % SUFFIX in rounds, '%s is in alv_rounds.ROUNDS' % SUFFIX)
ps = read(os.path.join(ROOT, PS1))
ok("'%s'" % ME in ps, '%s is in the $suites list' % ME)
ok(os.path.isfile(os.path.join(ROOT, PATCHER)), '%s is on disk' % PATCHER)

shutil.rmtree(SCRATCH, ignore_errors=True)
print('')
print('=' * 74)
print('  %d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
