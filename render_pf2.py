# -*- coding: utf-8 -*-
"""render_pf2.py - before and after, desktop and phone, for PF-2.

    python render_pf2.py

THE STANDING RULE: before/after renders at desktop and phone before
any visible round is delivered. PF-2 is the only visible round in
push 3, and the picker is what it changes.

HOW THE BEFORE IS GOT, AND WHY IT IS NOT A SHADOW TEMPLATE.

render_r3p2 shadowed the template alone - a pre-round copy put in a
directory prepended to TEMPLATES DIRS - and that was right for a round
that only moved markup.

PF-2 also moved the VIEW: all_recipes left the planner's context.
Render the pre-round template against the post-round view and the
dialog comes out empty, which is a picture of neither version. The
first run of this script did exactly that and refused itself.

So the BEFORE is rendered from a COPY of the whole application with
every one of this round's files restored from its .bak_pickfilter.
The copy lives in a temp directory; the real tree is never touched;
and what is photographed is the application as it was this morning.

HOW THE AFTER'S RECIPES GET INTO THE DIALOG. After this round the
picker FETCHES its rows, and a page loaded with set_content has no
server to fetch from. So the real endpoint is called through the test
client, its real JSON captured, and window.fetch replaced with a
function returning exactly those bytes. The rows are then drawn by
the page's own pfDraw(). Real server output, real client rendering,
only the HTTP hop stubbed - nothing about the picture is invented.

The BEFORE needs none of that: its recipes are in the markup, which
is the thing this round removes.
"""
import datetime as dt
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = '/mnt/user-data/outputs/PF2_renders'
SUFFIX = '.bak_pickfilter'
WIDTHS = ((1200, 'desktop'), (390, 'phone'))
MON = dt.date(2026, 10, 19)

COURSES = ['Starter', 'Main', 'Salad', 'Dessert', 'Side', 'Snack']
CATS = ['Pasta', 'Greek', 'Asian', 'Bakes']
PROTS = ['Lamb', 'Fish', 'Chicken', 'Beef']
AUTHORS = ['General', 'Demetri & Angy', 'Erene', 'Alexandra']
NAMES = [
    'Fakes', 'Greek Salad (Horiatiki)', 'Potato Salad',
    'Salad - Arugula and Roasted Carrot', 'Salad - Beet',
    'Salad - Butternut Squash', 'Salad - Butternut Squash Quinoa',
    'Salad - Caprese Pasta', 'Salad - Chopped Asparagus',
    'Salad - Grilled Shrimp', 'Salad - Homemade Italian Dressing',
    'Salad - Italian Pasta', 'Moussaka', 'Pastitsio', 'Souvlaki',
    'Tzatziki', 'Lemon Potatoes', 'Baklava', 'Galaktoboureko',
    'Briam', 'Dolmades', 'Avgolemono', 'Spanakopita', 'Tiropita',
    'Gigantes Plaki', 'Keftedes', 'Stifado', 'Kleftiko',
    'Loukoumades', 'Revani',
]


# ==========================================================================
# THE WORKER - run inside ONE tree, dumps what that tree renders
# ==========================================================================
def dump(path):
    """Boot the application in THIS tree and write what it renders."""
    here = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, here)
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')

    import django
    from django.conf import settings as S

    django.setup()
    from django.test.utils import setup_test_environment

    setup_test_environment()
    from django.db import connections
    from asgiref.local import Local

    S.DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3',
                               'NAME': ':memory:'}}
    S.ROOT_URLCONF = 'mysite.urls'
    S.ALLOWED_HOSTS = list(S.ALLOWED_HOSTS) + ['testserver']
    S.PASSWORD_HASHERS = ['django.contrib.auth.hashers.MD5PasswordHasher']
    try:
        have = bool(S.SECRET_KEY)
    except Exception:
        have = False
    if not have:
        # A fixed throwaway for an in-memory database in one process.
        S.SECRET_KEY = 'pf2-render-only-not-a-secret'
    S.DEBUG = False
    connections.__dict__.pop('settings', None)
    connections._settings = None
    connections._connections = Local(connections.thread_critical)

    from django.core.management import call_command
    call_command('migrate', run_syncdb=True, verbosity=0,
                 stdout=io.StringIO())

    from django.contrib.auth.models import Permission, User
    from django.test import Client
    from pages.models import (CustomProtein, Recipe, RecipeCategory,
                              RecipeCourse, RecipeFavourite)

    u = User.objects.create_user(username='render', password='x',
                                 email='r@example.test')
    for c in ('can_access_recipes', 'can_edit_recipes'):
        try:
            u.user_permissions.add(Permission.objects.get(codename=c))
        except Permission.DoesNotExist:
            pass
    cl = Client()
    cl.force_login(u)

    cs = [RecipeCourse.objects.create(name=n, display_order=i)
          for i, n in enumerate(COURSES)]
    ks = [RecipeCategory.objects.create(name=n) for n in CATS]
    ps = [CustomProtein.objects.create(name=n) for n in PROTS]
    for i, n in enumerate(NAMES):
        r = Recipe.objects.create(
            recipe_name=n, servings=4 + (i % 3) * 2,
            prep_time=5 + (i % 6) * 5, cook_time=10 + (i % 7) * 10,
            author=AUTHORS[i % 4], is_vegetarian=(i % 3 == 0))
        r.courses.add(cs[i % len(cs)])
        r.categories.add(ks[i % len(ks)])
        if i % 3 != 0:
            r.proteins.add(ps[i % len(ps)])
        if i % 7 == 0:
            RecipeFavourite.objects.create(user=u, recipe=r)

    url = '/meal_plans/planner/?week=' + MON.strftime('%Y-%m-%d')
    resp = cl.get(url)
    if resp.status_code != 200:
        raise SystemExit('render_pf2: the planner answered %d'
                         % resp.status_code)
    out = {'html': resp.content.decode('utf-8', 'replace'),
           'rows': None, 'salad': None}

    # ONLY THE AFTER HAS AN ENDPOINT. Asked of the tree rather than
    # of a flag, so this worker does not need to be told which half
    # of the comparison it is.
    try:
        from django.urls import reverse
        ep = reverse('picker_recipes')
    except Exception:
        ep = None
    if ep:
        out['rows'] = cl.get(ep).content.decode('utf-8')
        out['salad'] = cl.get(
            '%s?course=%d' % (ep, cs[2].recipe_course_id)
        ).content.decode('utf-8')

    with open(path, 'w', encoding='utf-8') as f:
        json.dump(out, f)
    print('  dumped %s  (%d bytes of html, endpoint %s)'
          % (os.path.basename(path), len(out['html']),
             'yes' if ep else 'no'))


# ==========================================================================
# THE DRIVER
# ==========================================================================
def reverted_copy():
    """A copy of the application with PF-2 undone, in a temp dir."""
    tmp = tempfile.mkdtemp(prefix='alv_pf2_before_')
    dest = os.path.join(tmp, 'tree')
    shutil.copytree(
        ROOT, dest,
        ignore=shutil.ignore_patterns('.git', '__pycache__', 'media',
                                      'node_modules', '*.pyc', 'staticfiles'))
    n = 0
    for dp, dn, fn in os.walk(dest):
        for f in list(fn):
            if f.endswith(SUFFIX):
                live = os.path.join(dp, f[:-len(SUFFIX)])
                shutil.copy2(os.path.join(dp, f), live)
                n += 1
    # THE FILE THIS ROUND CREATED HAS NO BACKUP, so reverting means
    # DELETING it - a copy that kept _recipe_filter.py would be a
    # tree that is neither before nor after.
    made = os.path.join(dest, 'pages', 'views', 'recipes',
                        '_recipe_filter.py')
    if os.path.isfile(made):
        os.remove(made)
        n += 1
    print('  reverted %d file(s) in the copy' % n)
    return tmp, dest


def main():
    if '--dump' in sys.argv:
        return dump(sys.argv[sys.argv.index('--dump') + 1])

    os.makedirs(OUT, exist_ok=True)
    print('PF-2 renders')
    print('  AFTER - this tree')
    after_p = os.path.join(OUT, '_after.json')
    subprocess.run([sys.executable, os.path.abspath(__file__),
                    '--dump', after_p], cwd=ROOT, check=True)

    print('  BEFORE - a copy with every .bak_pickfilter restored')
    tmp, dest = reverted_copy()
    try:
        before_p = os.path.join(OUT, '_before.json')
        subprocess.run([sys.executable,
                        os.path.join(dest, 'render_pf2.py'),
                        '--dump', before_p], cwd=dest, check=True)
    finally:
        shutil.rmtree(tmp, True)

    A = json.load(open(after_p, encoding='utf-8'))
    B = json.load(open(before_p, encoding='utf-8'))

    # A BEFORE THAT IS THE SAME AS THE AFTER IS A BEFORE THAT WAS NOT
    # READ. render_r3p2 paid for this guard; it is kept.
    if A['html'] == B['html']:
        raise SystemExit('render_pf2: before and after are the same '
                         'bytes - the revert did not take')
    if 'class="recipe-option"' not in B['html']:
        raise SystemExit('render_pf2: the BEFORE has no recipe cards in '
                         'its markup, which is the thing this round '
                         'removes')
    if 'class="recipe-option"' in A['html']:
        raise SystemExit('render_pf2: the AFTER still ships recipe cards')
    if 'name="author"' in B['html']:
        raise SystemExit('render_pf2: the BEFORE already has an author '
                         'filter')
    if B['rows'] is not None:
        raise SystemExit('render_pf2: the BEFORE has a picker endpoint')
    print('')
    print('  markup   BEFORE %d recipe cards, %d <img>'
          % (B['html'].count('class="recipe-option"'),
             B['html'].count('<img')))
    print('           AFTER  %d recipe cards, %d <img>'
          % (A['html'].count('class="recipe-option"'),
             A['html'].count('<img')))
    print('           page   %d bytes -> %d  (%+d%%)'
          % (len(B['html']), len(A['html']),
             round(100.0 * (len(A['html']) - len(B['html']))
                   / len(B['html']))))

    try:
        from playwright.sync_api import sync_playwright
    except Exception:
        raise SystemExit('render_pf2: playwright is not available')

    fixcss = os.path.join(ROOT, 'test_fixture_bootstrap413.css')
    if not os.path.isfile(fixcss):
        raise SystemExit('render_pf2: the Bootstrap fixture is not in '
                         'the tree, so the render would measure a page '
                         'with no grid')
    fix = '<style>%s</style>' % open(fixcss, encoding='utf-8').read()

    # jQuery COMES FROM A CDN AND IS NOT HERE. openPicker ends by
    # calling $('#pickerModal').modal('show'), which is Bootstrap's
    # job and not this round's - every line before it is the reset
    # and the fetch, which ARE this round's. A no-op $ lets the real
    # function run to the end instead of dying on its last line.
    stub = """
<script>
window.$ = function () { return {modal: function () {}}; };
window.__R = %s; window.__S = %s;
window.fetch = function (url) {
    var b = (String(url).indexOf('course=') >= 0) ? window.__S : window.__R;
    return Promise.resolve({ok: true, json: function () {
        return Promise.resolve(b); }});
};
</script>
""" % (A['rows'], A['salad'])

    def dressed(html, with_stub):
        i = html.lower().find('</head>')
        add = fix + (stub if with_stub else '')
        return html[:i] + add + html[i:] if i > 0 else add + html

    OPEN = """() => {
        const d = document.getElementById('pickerModal');
        d.style.display = 'block';
        d.classList.add('show');
        d.removeAttribute('aria-hidden');
        d.style.position = 'static';
        const g = d.querySelector('.modal-dialog');
        if (g) { g.style.margin = '0 auto'; g.style.maxWidth = 'none'; }
        document.querySelectorAll('.modal-backdrop').forEach(
            b => b.remove());
    }"""

    MEASURE = """() => ({
        cards: document.querySelectorAll(
            '#pickerList .recipe-option').length,
        controls: document.querySelectorAll(
            '.picker-filter .pf-btn, .picker-filter .pf-fav, '
            + '.picker-filter .alv-seg button').length,
        stripH: Math.round(document.querySelector('.picker-filter')
            .getBoundingClientRect().height),
        dialogW: Math.round(document.querySelector(
            '#pickerModal .modal-content').getBoundingClientRect().width)
    })"""

    shots, metrics = {}, {}
    with sync_playwright() as pw:
        br = pw.chromium.launch()
        for label, D in (('before', B), ('after', A)):
            for w, where in WIDTHS:
                pg = br.new_page(viewport={'width': w, 'height': 1100})
                pg.set_content(dressed(D['html'], label == 'after'),
                               wait_until='domcontentloaded')
                pg.evaluate(OPEN)
                if label == 'after':
                    pg.evaluate(
                        "() => openPicker('2026-10-19', 'Monday')")
                    pg.evaluate(OPEN)
                    pg.wait_for_timeout(600)
                key = '%s_%s' % (label, where)
                metrics[key] = pg.evaluate(MEASURE)
                png = os.path.join(OUT, 'picker_%s.png' % key)
                el = pg.query_selector('#pickerModal .modal-content')
                (el or pg).screenshot(path=png)
                shots[key] = png
                pg.close()
        br.close()

    os.remove(after_p)
    os.remove(before_p)

    print('')
    print('=' * 70)
    print('  PF-2  the picker, before and after')
    print('=' * 70)
    print('  %-16s %7s %9s %8s %8s'
          % ('', 'cards', 'filters', 'strip', 'dialog'))
    for k in ('before_desktop', 'after_desktop', 'before_phone',
              'after_phone'):
        m = metrics[k]
        print('  %-16s %7d %9d %7dpx %7dpx'
              % (k, m['cards'], m['controls'], m['stripH'],
                 m['dialogW']))
    print('')
    print('  cards   - cards in the dialog. In the BEFORE every one of')
    print('            them is in the PAGE, opened or not.')
    print('  filters - one course strip became five controls.')
    print('')
    for k in sorted(shots):
        print('  %s' % shots[k])
    print('=' * 70)


if __name__ == '__main__':
    main()
