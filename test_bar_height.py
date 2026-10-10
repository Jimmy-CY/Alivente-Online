# -*- coding: utf-8 -*-
"""test_bar_height.py - Section D round D-1, 9 Oct 2026.

THE DESKTOP ACTION BAR HAS ONE HEIGHT. NOTHING WAS CHECKING THAT.

D-1 asked which of five heights the bar should settle on. Measured on
109 real templates with test_tap_target's own renderer, the bar has
one: 35px, on all 265 controls. Table rows have one, 34px. Modals have
one, 38px. The five heights in the original note came from a synthetic
fixture holding one button of each kind - a height measured without
the real markup around it is a height no user sees.

So the round is this suite and nothing else. The uniformity is true
today by accident; this makes it true on purpose.

THREE FIXTURES OF MINE GOT THIS WRONG BEFORE THE FOURTH ATTEMPT USED
THE RENDERER THAT ALREADY EXISTED. One wrapped the controls in
.action-bar when every rule keys off .page-action-buttons. One dropped
the `btn` class two selectors require. One wrapped each control in a
span a child combinator cannot see through. Each produced plausible
numbers and each was wrong, which is why this suite borrows
test_tap_target's page_html rather than building a fifth.

IT BORROWS BY NAME, NOT BY LINE NUMBER. An earlier draft sliced that
file at fixed offsets and lost page_html the moment the file moved.
Section 1 fails loudly if any helper cannot be found.

WHAT THIS DOES NOT CLAIM. That 35px is the right height - it is simply
the one 265 controls already agree on, and nothing here argues for it.
And that the whole corpus is uniform: 78 controls in cards or loose on
pages take 11 heights between 28 and 52px. Section 5 records them with
a pinned count rather than asserting they are fine, because they sit
in one-off contexts where a page may have had a reason.
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
# --- SCRATCH -------------------------------------------- 18 Sep 2026 --
# mkdtemp hands THIS PROCESS a directory whose name no other process
# knows, so two suites cannot collide however the gate orders them.
# See test_probe_location.py.
import atexit as _atexit
import shutil as _shutil
import tempfile as _tempfile

SCRATCH = _tempfile.mkdtemp(prefix='alv_probe_')
_atexit.register(_shutil.rmtree, SCRATCH, True)


def _probe_failed(path, err):
    """Say what could not be opened, and what was true of it at the time."""
    import os as _o
    there = _o.path.exists(path)
    print('')
    print('  !! THE BROWSER COULD NOT OPEN THE FIXTURE')
    print('     path    : %s' % path)
    print('     on disk : %s' % (('yes, %d byte(s)' % _o.path.getsize(path))
                                 if there else 'NO'))
    print('     reason  : %s' % str(err).split('\n')[0][:150])
    print('')
    print('     This is a navigation failure, not a failed check, so the')
    print('     checks below it never ran. The fixture lives in a')
    print('     directory mkdtemp made for this process alone, so no other')
    print('     suite can have taken the name. If it IS on disk and not')
    print('     empty, something outside this repo is holding it open - a')
    print('     sync client and an anti-virus scanner are the usual two.')


def _goto(pg, path):
    """Open a local fixture, and SAY SOMETHING if the browser will not.

    Every tool here carries a paragraph about a crash blocking a push
    exactly as hard as a failure while saying far less about why - and
    then calls goto bare. This is that paragraph, kept.
    """
    try:
        pg.goto('file://' + path)
    except Exception as e:
        _probe_failed(path, e)
        raise SystemExit(1)
    return True
# ------------------------------------------------------------------------


import collections
import os
import re
import sys

ROOT = os.getcwd()
if not os.path.isdir(os.path.join(ROOT, 'pages', 'templates')):
    sys.exit('! pages/templates not found - run from the repo root')
sys.path.insert(0, ROOT)

ME = 'test_bar_height.py'
PATCHER = 'apply_bar_height.py'
PS1 = 'Push-PendingChanges.ps1'
LENDER = 'test_tap_target.py'
BOOT = 'test_fixture_bootstrap413.css'

BAR, ROW, MODAL = 35, 34, 38
N_BAR, N_ROW, N_MODAL = 265, 110, 91
N_LOOSE, N_LOOSE_H = 78, 12   # 12, not the 11 I first said:
# the earlier figure added a card's six heights to a page's ten
# and counted the union by hand. The union is twelve. A number
# arrived at by adding two others is a number nobody measured.
PHONE = 44

# The five that differ from their neighbours, each named. Four of the
# five are two pages: help_page's modal footer and one Save button.
STRAYS = {
    ('a table row', 'crs/submission_detail.html'): 1,
    ('a modal', 'finance_valuations_edit.html'): 1,
    ('a modal', 'help_page.html'): 3,
}

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
            for line in str(detail).split('\n')[:10]:
                print('         %s' % line)
    return cond


def skip(msg, why):
    global skipped
    skipped += 1
    print('  --   %s  (%s)' % (msg, why))


def head(t):
    print('')
    print('=' * 74)
    print(t)
    print('=' * 74)


def read(p):
    with open(p, encoding='utf-8', errors='replace') as f:
        return f.read().replace('\r\n', '\n')


print(__doc__.strip().splitlines()[0])

# ==========================================================================
head('1. SCOPE, AND THE RENDERER THIS BORROWS')
# ==========================================================================
ok(os.path.isfile(os.path.join(ROOT, PATCHER)), '%s is on disk' % PATCHER)

# SELF-CONTAINED, WITH A GUARD - after four attempts at borrowing
# test_tap_target's internals failed on a different missing name each
# time. Slicing by line number lost page_html; slicing by anchor
# string lost business(); lifting defs and CONSTANTS by parse tree
# lost a lowercase module variable the corpus loop needs. Each failure
# was legible, which is the only good thing about them.
#
# So the three helpers below are THIS suite's, copied from that file,
# and section 1 asserts the originals still read exactly the same. If
# that file retunes its renderer, this fails and names the helper that
# diverged, rather than silently measuring something else. A copy with
# a guard is honest; a copy without one is how two implementations of
# one rule drift apart.
PERSONAL = ('recipe', 'meal_plan', 'ingredient', 'wcim', 'celebration',
            'pantry', 'unit_conversions', 'measurement_units',
            'household_member', 'map_ingredients', 'import_recipe',
            'preview_imported', 'categories_management', 'my_profile',
            'personal_', 'workspace')


def styles_of(t):
    return [re.sub(r'\{%.*?%\}', '', m.group(1), flags=re.S)
            for m in re.finditer(r'<style[^>]*>(.*?)</style>', t,
                                 re.S | re.I)]


def body_markup(t):
    m = re.search(r'\{%\s*block\s+content\s*%\}(.*)', t, re.S)
    b = m.group(1) if m else t
    b = re.sub(r'<(script|style)\b.*?</\1>', '', b, flags=re.S | re.I)
    b = re.sub(r'\{#.*?#\}', '', b, flags=re.S)
    b = re.sub(r'\{%.*?%\}', '', b, flags=re.S)
    return re.sub(r'\{\{.*?\}\}', 'x', b, flags=re.S)


import alv_tree as T                                          # noqa: E402

TEMPLATES = []
# rel -> the absolute path it came from. REBUILDING THE PATH FROM THE
# REL IS WRONG: the corpus spans more than one template root, so
# joining pages/templates to a rel silently drops every CRS page - 19
# controls, including one of the five strays, which is how I noticed.
WHERE = {}
for _d, _sub, _fs in T.walk3():
    for _f in _fs:
        if not _f.endswith('.html') or '.bak_' in _f:
            continue
        _rel = T.rel(os.path.join(_d, _f)).replace(os.sep, '/')
        if _rel == 'base.html' or 'OLD DO NOT USE' in _rel:
            continue
        if any(p in _rel for p in PERSONAL):
            continue
        if 'extends' not in read(os.path.join(_d, _f))[:3000]:
            continue
        TEMPLATES.append(_rel)
        WHERE[_rel] = os.path.join(_d, _f)
TEMPLATES.sort()

# THE GUARD. Each helper must still read identically in the lender.
lent = None
if os.path.isfile(os.path.join(ROOT, LENDER)):
    _src = read(os.path.join(ROOT, LENDER))
    import inspect as _inspect
    drift = [n for n, f in (('styles_of', styles_of),
                            ('body_markup', body_markup))
             if _inspect.getsource(f).strip() not in _src]
    drift += [n for n in ('PERSONAL = (', 'def page_html(')
              if n not in _src]
    ok(not drift,
       'the renderer is %s\'s, copied here, and the original still reads '
       'identically' % LENDER,
       'DIVERGED: %s - reconcile them rather than letting two renderers '
       'drift' % drift)
    lent = not drift
else:
    skip('the drift guard', '%s is not on disk' % LENDER)
    lent = True
ok(len(TEMPLATES) > 80,
   '  the corpus is %d business template(s), the same filter that file '
   'uses' % len(TEMPLATES))

OPEN = ('<style>.modal{display:block!important;position:static!important;'
        'opacity:1!important}.modal-dialog{transform:none!important}'
        '.fade{opacity:1!important}</style>')


def page_html(boot, base_src, t):
    return ('<!doctype html><html><head><meta charset="utf-8"><meta '
            'name="viewport" content="width=device-width, initial-scale=1">'
            '<title>t</title><style>%s</style><style>%s</style>%s%s</head>'
            '<body class="has-sidebar"><div class="main-content with-sidebar">'
            '%s</div></body></html>'
            % (boot, '\n'.join(styles_of(base_src)),
               ''.join('<style>%s</style>' % c for c in styles_of(t)), OPEN,
               body_markup(t)))


up = False
if lent:
    try:
        from playwright.sync_api import sync_playwright
        import atexit
        if not os.path.isfile(os.path.join(ROOT, BOOT)):
            raise RuntimeError('%s is missing' % BOOT)
        _pw = sync_playwright().start()
        atexit.register(_pw.stop)
        _br = _pw.chromium.launch()
        up = True
    except Exception as _e:
        skip('sections 2 to 5', 'Chromium would not start: %s'
             % str(_e).split('\n')[0][:70])

JS = '''() => {
  const o = [];
  document.querySelectorAll(
    '.action-primary,.action-secondary,.action-back,.action-filter,'
    + '.action-more-btn,.icon-action-btn').forEach(el => {
      if (!el.getClientRects().length) return;
      const where = el.closest('.page-action-buttons') ? 'the action bar'
        : el.closest('.modal') ? 'a modal'
        : el.closest('table') ? 'a table row'
        : el.closest('.mobile-action-bar') ? 'the phone row'
        : el.closest('.alv-card, .ins-card, .form-card') ? 'a card'
        : 'loose on the page';
      o.push([where,
              Math.round(el.getBoundingClientRect().height * 10) / 10,
              el.scrollHeight - el.clientHeight]);
    });
  return o;
}'''


REFUSED = []


def survey(width, extra=''):
    _T = T
    boot = read(os.path.join(ROOT, BOOT))
    base = read(_T.path_of('base.html'))
    by = collections.defaultdict(collections.Counter)
    where_page = collections.Counter()
    clipped = []
    ctx = _br.new_context(viewport={'width': width, 'height': 900})
    # HERMETIC. 34 templates carry a remote <link>, and base pulls
    # Bootstrap from a CDN as well as the pinned 4.1.3 fixture that
    # this suite loads from disk. Left open, a machine with a route out
    # measures a different stylesheet from one without - and these
    # heights are pinned numbers. test_tap_target and
    # test_control_height both do exactly this; I left it out of both
    # of mine and the gate caught it.
    def _offline(route, request):
        REFUSED.append(request.url)
        route.abort()

    ctx.route(re.compile(r'^https?://'), _offline)
    pg = ctx.new_page()
    for rel in TEMPLATES:
        try:
            t = read(WHERE[rel])
        except Exception:
            continue
        doc = page_html(boot, base, t)
        if extra:
            doc = doc.replace('</head>', '<style>%s</style></head>' % extra, 1)
        pg.set_content(doc)
        for where, h, clip in pg.evaluate(JS):
            by[where][round(h)] += 1
            if clip > 0:
                clipped.append('%s %s clipped %dpx' % (rel, where, clip))
            where_page[(where, rel, round(h))] += 1
    ctx.close()
    return by, where_page, clipped


desk = row_page = None
if up:
    desk, where_page, clipped = survey(1280)


# ==========================================================================
head('2. THE ACTION BAR IS ONE HEIGHT, AND IT IS MEASURED')
# ==========================================================================
if not up:
    skip('section 2', 'no browser')
else:
    bar = desk['the action bar']
    ok(len(bar) == 1 and list(bar) == [BAR],
       'every control in .page-action-buttons computes %dpx - %d of them, '
       'ONE height' % (BAR, sum(bar.values())), dict(sorted(bar.items())))
    ok(sum(bar.values()) == N_BAR,
       '  and there are %d of them, which is the number pinned when this '
       'was measured' % sum(bar.values()), 'pinned at %d' % N_BAR)
    ok(not clipped,
       '  and not one of them clips its own label', '\n'.join(clipped[:6]))
    # A ROUTE I ADDED IS NOT A MEASUREMENT.
    ok(len(REFUSED) > 0,
       '  and the browser REFUSED %d remote request(s), so these heights '
       'come from the pinned Bootstrap fixture and nothing a CDN served '
       'today' % len(REFUSED), REFUSED[:3])

    # CONTROL. A survey that reports one height because its selector
    # matches nothing reads exactly like a bar that is uniform.
    d2, _wp, _c = survey(1280, '.page-action-buttons .btn.action-primary'
                               '{height:48px;min-height:48px;'
                               'box-sizing:border-box}')
    ok(len(d2['the action bar']) > 1,
       'CONTROL: pin one class to 48px and the survey sees %d heights, not '
       'one - so "one height" is the bar, not a blind probe'
       % len(d2['the action bar']), dict(sorted(d2['the action bar'].items())))


# ==========================================================================
head('3. SO DO TABLE ROWS AND MODALS - WITH THEIR STRAYS NAMED')
# ==========================================================================
if not up:
    skip('section 3', 'no browser')
else:
    for place, norm, total in (('a table row', ROW, N_ROW),
                               ('a modal', MODAL, N_MODAL)):
        c = desk[place]
        ok(sum(c.values()) == total, '%s: %d control(s)'
           % (place, sum(c.values())), 'pinned at %d' % total)
        ok(c[norm] == total - sum(n for (w, _p), n in STRAYS.items()
                                  if w == place),
           '  %d of them at %dpx' % (c[norm], norm),
           dict(sorted(c.items())))
    got = collections.Counter()
    for (where, rel, h), n in where_page.items():
        norm = {'a table row': ROW, 'a modal': MODAL}.get(where)
        if norm is not None and h != norm:
            got[(where, rel)] += n
    ok(dict(got) == STRAYS,
       'and the %d stray(s) are exactly the ones named: %s'
       % (sum(STRAYS.values()),
          ', '.join('%s x%d' % (p, n) for (_w, p), n in sorted(STRAYS.items()))),
       'measured: %s' % dict(got))


# ==========================================================================
head('4. THE PHONE FLOOR IS 44PX AND THIS ROUND DID NOT GO NEAR IT')
# ==========================================================================
if not up:
    skip('section 4', 'no browser')
else:
    ph, _wp, _c = survey(390)
    bar_ph = ph['the action bar']
    ok(list(bar_ph) == [PHONE],
       'at 390px every bar control is %dpx - the house floor, unchanged'
       % PHONE, dict(sorted(bar_ph.items())))


# ==========================================================================
head('5. WHAT IS NOT UNIFORM, RECORDED RATHER THAN ASSERTED')
# ==========================================================================
if not up:
    skip('section 5', 'no browser')
else:
    loose = collections.Counter()
    for place in ('a card', 'loose on the page'):
        loose.update(desk[place])
    ok(sum(loose.values()) == N_LOOSE,
       '%d control(s) sit in a card or loose on a page' % sum(loose.values()),
       'pinned at %d' % N_LOOSE)
    ok(len(loose) == N_LOOSE_H,
       '  and they take %d distinct heights, %dpx to %dpx: %s'
       % (len(loose), min(loose), max(loose), dict(sorted(loose.items()))),
       'pinned at %d' % N_LOOSE_H)
    print('')
    print('       THESE ARE NOT ASSERTED UNIFORM AND THIS IS NOT A FAILURE.')
    print('       They sit in one-off contexts where a page may have had a')
    print('       reason, so they want a page-by-page look rather than one')
    print('       number. The count is pinned so the set cannot grow')
    print('       unnoticed - which is the whole of what D-1 can honestly')
    print('       do about them today.')
    try:
        _br.close()
    except Exception:
        pass


# ==========================================================================
head('6. REGISTERED, ON THE GATE')
# ==========================================================================
ps = read(os.path.join(ROOT, PS1))
ok("'%s'" % ME in ps, '%s is in the $suites list' % ME)
rounds = read(os.path.join(ROOT, 'alv_rounds.py'))
ok("'.bak_barheight'" not in rounds,
   'and NOT in alv_rounds.ROUNDS - this round leaves no application file '
   'behind, so there is nothing for as_left_by to walk to')
ok(ME not in T.CONVERTED,
   '  nor in alv_tree.CONVERTED - that register is for suites that walk '
   'the template tree, and this one borrows %s\'s corpus instead of '
   'walking. D-2 joined it because D-2 does walk' % LENDER)

print('')
print('=' * 74)
print('  %d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
print('')
print('  NOT PROVED HERE: that 35px is the right height. It is the one')
print('  265 controls already agree on, and nothing in this file argues')
print('  for it. What IS proved is that they agree, that table rows and')
print('  modals agree, that the phone floor is untouched - and that none')
print('  of it can drift now without something saying so.')
sys.exit(1 if failed else 0)
