# -*- coding: utf-8 -*-
"""test_message_bar.py - Section M round M1, 29 Sep 2026.

A message bar now takes its colour from the message's tag: green for a
success, red for a failure, amber for a caution, the accent for
information. Seventy-seven loops in sixteen shapes became one.

SECTION 1 IS THE PRECONDITION AND IT ASKS DJANGO, NOT THE FILE. Django
tags an error 'error'; Bootstrap 4.1.3 has no .alert-error at all. So
without MESSAGE_TAGS the commonest message in this system - 281
messages.error(...) calls - renders as an unstyled box. The control
removes the setting and shows the tag going back to 'error'.

SECTION 4 measures the four tones in Chromium against the real Bootstrap
4.1.3 stylesheet, because base only OVERRIDES parts of it and what the
screen shows is the two together.

SECTION 5 is the tone the house never owned: base had rules for
.alert-info, -success and -warning and none for -danger, which this round
makes the commonest bar of the four.

This suite reads mysite/settings.py to answer two questions and prints
none of it.
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
    """Open a local fixture, and SAY SOMETHING if the browser will not."""
    try:
        pg.goto('file://' + path)
    except Exception as e:
        _probe_failed(path, e)
        raise SystemExit(1)
    return True
# ------------------------------------------------------------------------
import os
import re
import sys

ROOT = os.getcwd()
sys.path.insert(0, ROOT)
try:
    import alv_tree
except Exception as e:
    sys.exit('! alv_tree could not be imported: %s' % e)

SUFFIX = '.bak_msgbar'
ME = 'test_message_bar.py'
PATCHER = 'apply_message_bar.py'
SETTINGS = os.path.join('mysite', 'settings.py')
PS1 = 'Push-PendingChanges.ps1'
BOOT = 'test_fixture_bootstrap413.css'
EXE = '/opt/pw-browsers/chromium'

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


def read(p):
    with open(p, encoding='utf-8', errors='replace') as f:
        return f.read().replace('\r\n', '\n')


def head(t):
    print('\n' + '=' * 74 + '\n' + t + '\n' + '=' * 74)


def css_of(t):
    return '\n'.join(re.findall(r'<style\b[^>]*>(.*?)</style>', t, re.S))


def loops(t):
    out = []
    for m in re.finditer(r'\{%\s*for\s+(\w+)\s+in\s+messages\s*%\}', t):
        depth, i = 1, m.end()
        while depth:
            nxt = re.search(r'\{%\s*(for|endfor)\b', t[i:])
            if not nxt:
                return out
            depth += 1 if nxt.group(1) == 'for' else -1
            i += nxt.end()
        out.append((m.group(1), t[m.start():i]))
    return out


def lum(rgb):
    def f(c):
        c = c / 255.0
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    return 0.2126 * f(rgb[0]) + 0.7152 * f(rgb[1]) + 0.0722 * f(rgb[2])


def ratio(a, b):
    la, lb = lum(a), lum(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def rgb(s):
    return tuple(int(x) for x in re.findall(r'\d+', s)[:3])


base = read(alv_tree.path_of('base.html'))
# NOTE: this suite never prints a line of settings.py. It reads it to
# answer two questions and reports only the answers.
settings_src = read(os.path.join(ROOT, SETTINGS))

print('=' * 74)
print('%s - M1, THE MESSAGE BAR SAYS WHAT HAPPENED' % ME)
print('=' * 74)

# ==========================================================================
head('1. THE PRECONDITION')
# ==========================================================================
ok('MESSAGE_TAGS' in settings_src, 'settings.py sets MESSAGE_TAGS')
ok("MESSAGE_TAGS = {message_constants.ERROR: 'danger'}" in settings_src,
   '  mapping ERROR to danger, which is the class Bootstrap actually has')
ok('from django.contrib.messages import constants as message_constants'
   in settings_src, '  with the import it needs')

# AND DJANGO IS ASKED, rather than the file being read.
try:
    import django
    from django.conf import settings as dj
    if not dj.configured:
        from django.contrib.messages import constants as mc
        dj.configure(MESSAGE_TAGS={mc.ERROR: 'danger'}, TEMPLATES=[{
            'BACKEND': 'django.template.backends.django.DjangoTemplates',
            'DIRS': [], 'APP_DIRS': False, 'OPTIONS': {}}])
        django.setup()
    from django.contrib.messages.storage.base import Message
    from django.contrib.messages import constants as mc
    from django.template import Context, Template
    HAVE_DJANGO = True
except Exception as e:
    HAVE_DJANGO = False
    print('  !! django unavailable (%s)' % e)

if HAVE_DJANGO:
    got = {lvl: Message(lvl, 'x').tags
           for lvl in (mc.SUCCESS, mc.INFO, mc.WARNING, mc.ERROR)}
    ok(got[mc.ERROR] == 'danger',
       'DJANGO SAYS SO: an ERROR message now tags itself "danger", not '
       '"error"', got[mc.ERROR])
    for lvl, name in ((mc.SUCCESS, 'success'), (mc.INFO, 'info'),
                      (mc.WARNING, 'warning')):
        ok(got[lvl] == name, '  and %s is untouched' % name, got[lvl])

    # THE CONTROL: without the setting, the class Bootstrap has no rule for.
    import django.contrib.messages.storage.base as msgbase
    old = dj.MESSAGE_TAGS
    try:
        dj.MESSAGE_TAGS = {}
        msgbase.LEVEL_TAGS = django.contrib.messages.utils.get_level_tags()
        ok(Message(mc.ERROR, 'x').tags == 'error',
           'CONTROL: without the setting the tag is "error" - and there is '
           'no .alert-error in Bootstrap 4.1.3, which is what 281 messages '
           'were heading for')
    finally:
        dj.MESSAGE_TAGS = old
        msgbase.LEVEL_TAGS = django.contrib.messages.utils.get_level_tags()

    boot = read(os.path.join(ROOT, BOOT)) if os.path.isfile(
        os.path.join(ROOT, BOOT)) else ''
    if boot:
        ok('.alert-error' not in boot,
           '  and the Bootstrap fixture confirms it: no .alert-error rule '
           'exists at all')
    else:
        skipped += 1
else:
    skipped += 6

# ==========================================================================
head('2. ONE SHAPE, AND ONLY ONE')
# ==========================================================================
shapes, pages, centres, scripts, errs = set(), 0, 0, 0, []
for p in alv_tree.templates():
    t = read(p)
    ls = loops(t)
    if ls:
        pages += 1
    for var, block in ls:
        flat = ' '.join(block.split())
        for w, n in (('for %s in' % var, 'for VAR in'),
                     ('{{ %s ' % var, '{{ VAR '),
                     ('{{ %s.' % var, '{{ VAR.')):
            flat = flat.replace(w, n)
        shapes.add(flat)
        if '<center>' in block:
            centres += 1
        if '<script' in block:
            scripts += 1
        if 'alert-error' in block:
            errs.append(alv_tree.rel(p))

ok(len(shapes) == 1,
   'all %d message loops across %d page(s) are ONE shape - there were '
   'sixteen' % (sum(len(loops(read(p))) for p in alv_tree.templates()),
                pages),
   '\n'.join(sorted(shapes))[:400])
ok(pages >= 70, '  and that is %d pages, not a handful' % pages, pages)
one = list(shapes)[0] if shapes else ''
ok('alert-{{ VAR.tags }}' in one,
   '  the shape takes its colour from the tag')
ok('alv-message' in one,
   '  and marks itself as a message bar, so base can tell it from the '
   'static alerts a page puts in its own content')
ok('alert-dismissible' in one and 'data-dismiss="alert"' in one,
   '  and can always be dismissed by hand')
ok(not centres, '  no loop uses <center> any more', centres)
ok(not scripts, '  and none carries a script of its own', scripts)
ok(not errs, 'nothing in the tree can render alert-error', errs)

left = sum(read(p).count('auto-dismiss') for p in alv_tree.templates())
ok(left == 0,
   'the class the 51 copies keyed on is gone from the tree entirely', left)

# ==========================================================================
head('3. WHICH BARS LEAVE ON THEIR OWN')
# ==========================================================================
js = base[base.index('THE MESSAGE BAR'):]
js = js[:js.index('</script>')]
ok('.alv-message.alert-success, .alv-message.alert-info' in js,
   'base fades a SUCCESS and an INFORMATION bar')
ok('alert-danger' not in js and 'alert-warning' not in js,
   '  and leaves danger and warning alone - a failure waits to be read')
ok('2000' in js, '  after the same two seconds the 51 copies used')
ok('.alv-message' in js,
   '  and only message bars: a static alert in page content is not '
   'touched')

b = alv_tree.path_of('base.html') + SUFFIX
if os.path.isfile(b):
    was = read(b)
    ok('.alv-message' not in was,
       'CONTROL: base carried none of this before the round')
    ok('querySelectorAll(\'.auto-dismiss\')' not in was,
       '  the timer lived on the pages, 51 times over')
else:
    skipped += 2

# ==========================================================================
head('4. THE FOUR TONES, MEASURED IN CHROMIUM')
# ==========================================================================
try:
    from playwright.sync_api import sync_playwright
    HAVE_PW = True
except Exception as e:
    HAVE_PW = False
    print('  !! playwright unavailable (%s)' % e)

bootp = os.path.join(ROOT, BOOT)
if HAVE_PW and os.path.isfile(bootp):
    bars = ''.join(
        '<div class="alert alert-%s alert-dismissible fade show alv-message" '
        'data-tag="%s" role="alert">message<button type="button" '
        'class="close" data-dismiss="alert"><span>&times;</span></button>'
        '</div>' % (tag, tag)
        for tag in ('success', 'info', 'warning', 'danger'))
    fx = os.path.join(SCRATCH, 'msgbar.html')
    with open(fx, 'w', encoding='utf-8') as fh:
        fh.write('<!doctype html><html><head><meta charset="utf-8">'
                 '<style>%s</style><style>%s</style></head><body>%s</body>'
                 '</html>' % (read(bootp), css_of(base), bars))
    with sync_playwright() as pw:
        br = pw.chromium.launch(**({'executable_path': EXE}
                                   if os.path.exists(EXE) else {}))
        pg = br.new_page(viewport={'width': 1000, 'height': 600})
        pg.route(re.compile(r'^https?://'), lambda r: r.abort())
        _goto(pg, fx)
        seen = pg.evaluate('''() => {
            const o = {};
            document.querySelectorAll('[data-tag]').forEach(e => {
              const c = getComputedStyle(e);
              o[e.dataset.tag] = [c.color, c.backgroundColor, c.textAlign,
                                  c.paddingLeft, c.paddingRight];
            });
            return o;
        }''')
        br.close()

    for tag in ('success', 'info', 'warning', 'danger'):
        fg, bg, align, pl, pr = seen[tag]
        r = ratio(rgb(fg), rgb(bg))
        ok(r >= 4.5, '%-8s reads %.2f against its own ground' % (tag, r),
           (fg, bg))
        ok(align == 'center', '  and is centred, without a <center> tag',
           align)
        ok(pl == pr,
           '  with the same room on both sides, so the centred text does '
           'not sit under the close button', (pl, pr))
    grounds = set(v[1] for v in seen.values())
    ok(len(grounds) == 4,
       'the four tags are four different colours - they were one grey',
       grounds)
else:
    skipped += 13

# ==========================================================================
head('5. THE TONE THE HOUSE DID NOT OWN')
# ==========================================================================
bb = re.sub(r'/\*.*?\*/', '', css_of(base), flags=re.S)
for tone in ('info', 'success', 'warning', 'danger'):
    m = re.search(r'\.alert-%s\s*\{([^}]*)\}' % tone, bb)
    ok(m is not None and 'var(--alv-' in m.group(1),
       '.alert-%-8s is painted from the tokens' % tone,
       m.group(1) if m else 'no rule')
ok('--alv-bad-ink' in bb and '--alv-bad-line' in bb,
   '  and --alv-bad finally has the -ink and -line that --alv-good and '
   '--alv-warn always had')

if os.path.isfile(b):
    was = re.sub(r'/\*.*?\*/', '', css_of(read(b)), flags=re.S)
    ok(not re.search(r'\.alert-danger\s*\{', was),
       'CONTROL: base had NO .alert-danger rule before this round - the '
       'one tone that says a thing failed was Bootstrap\'s own, and this '
       'round makes it the commonest bar in the system')

said = re.search(r'(\d+) design tokens', base)
toks = len(set(re.findall(r'(--alv-[a-z0-9-]+)\s*:', css_of(base))))
ok(said and int(said.group(1)) == toks,
   'the standards block still counts itself: %s tokens'
   % (said.group(1) if said else '?'), toks)

# ==========================================================================
head('6. THE NOTICE THAT WAS NOT A SUCCESS')
# ==========================================================================
cal = read(alv_tree.path_of('celebration_calendar.html'))
cb = re.sub(r'/\*.*?\*/', '', css_of(cal), flags=re.S)
m = re.search(r'\.mobile-view-banner\s*\{([^}]*)\}', cb)
ok(m and 'var(--alv-accent-soft)' in m.group(1),
   'the timeline notice is the accent - it explains what you are looking '
   'at, it does not report that something happened',
   m.group(1) if m else 'no rule')
ok(m and 'linear-gradient' not in m.group(1),
   '  and no longer a gradient ending in Bootstrap\'s success green')
ok('#d4edda' not in cb, '  #d4edda is gone from the page')

# ==========================================================================
head('7. THE GATE')
# ==========================================================================
ps1 = os.path.join(ROOT, PS1)
if os.path.isfile(ps1):
    t = read(ps1)
    ok(ME in t, 'this suite is on the gate  %s' % PS1)
    ok(PATCHER not in re.sub(r'#.*', '', t),
       '  and the patcher is not - a gate runs suites, not rounds')
else:
    skipped += 2

try:
    from alv_rounds import ROUNDS
    ok(SUFFIX in ROUNDS, '%s is registered in alv_rounds.ROUNDS' % SUFFIX)
except Exception as e:
    failed += 1
    print('  FAIL alv_rounds could not be read: %s' % e)

print('')
print('=' * 74)
print('  %d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('')
print('  NOT PROVED HERE: that every message in the system carries the')
print('  right LEVEL. A messages.success() call about a failure would')
print('  now be green and confident about it. That is 439 call sites')
print('  and it is reading, not measuring.')
print('=' * 74)
sys.exit(1 if failed else 0)
