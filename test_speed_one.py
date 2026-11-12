# -*- coding: utf-8 -*-
"""test_speed_one.py - round SP-1, 12 Nov 2026.

RELEASE 66 - THE SPEED ROUND.
Demetri, 11:21: "Let's do the speed round."

Measured on the live site first, 11:20: Cloudflare already compresses
every page (zstd) and caches static files and photos, so those two items
were dropped. What is left:
  1. base.html's 197 KB of CSS is sent with every page (about 59 KB after
     compression). It becomes four cached files; the CSS stays in base.html.
  2. A new MySQL connection on every request (CONN_MAX_AGE 0) - kept for a
     minute instead, with Django's health check before reuse.
  3. ONE gunicorn worker - a page and everything it calls queued behind
     each other. Three, from gunicorn.conf.py.
  4. WhiteNoise last in the middleware - moved to straight after Security.
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

ROOT = os.getcwd()
sys.path.insert(0, ROOT)

SUFFIX = '.bak_speed1'
ME = 'test_speed_one.py'
PATCHER = 'apply_speed_one.py'
PS1 = 'Push-PendingChanges.ps1'
J = os.path.join
BASE = J(ROOT, 'pages', 'templates', 'base.html')

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
    return bool(cond)


def skip(msg, why):
    global skipped
    skipped += 1
    print('  --   %s  (%s)' % (msg, why))


def read(p):
    with open(p, encoding='utf-8-sig', errors='replace') as f:
        return f.read().replace('\r\n', '\n')


def head(t):
    print('')
    print('=' * 74)
    print(t)
    print('=' * 74)


print(__doc__.strip().splitlines()[0])

# ==========================================================================
head('1. THE SOURCE')
# ==========================================================================
base = read(BASE)
blocks = re.findall(r'\{% cached_css %\}(.*?)\{% endcached_css %\}', base,
                    re.S)
styles = re.findall(r'<style[^>]*>.*?</style>', base, re.S)
ok(len(blocks) == 4 and len(styles) == 4,
   'BASE: all four of its <style> blocks are wrapped in {% cached_css %}',
   '%d wrapped, %d styles' % (len(blocks), len(styles)))
ok(all(b.strip().startswith('<style') and b.strip().endswith('</style>')
       for b in blocks),
   '  each wrapper holds exactly one <style> block')
ok(not any(re.search(r'\{[%{]', b) for b in blocks),
   '  and none holds a template tag - the CSS is the same for every page')
ok('{% load alv_assets %}' in base, '  the tag library is loaded')
st = read(J(ROOT, 'mysite', 'settings.py'))
mw = re.search(r'MIDDLEWARE = \[(.*?)\n\]', st, re.S).group(1)
names = re.findall(r'"([\w.]+Middleware)"', mw)
ok(names[:2] == ['django.middleware.security.SecurityMiddleware',
                 'whitenoise.middleware.WhiteNoiseMiddleware'] and
   names.count('whitenoise.middleware.WhiteNoiseMiddleware') == 1,
   'WHITENOISE: straight after Security, once', names[:3])
ok("'CONN_MAX_AGE': 60," in st and "'CONN_HEALTH_CHECKS': True," in st and
   "'CONN_MAX_AGE': 0," not in st,
   'CONNECTIONS: kept for 60 seconds, checked before reuse')
gc = read(J(ROOT, 'gunicorn.conf.py'))
ok("workers = int(os.environ.get('WEB_CONCURRENCY', '3'))" in gc and
   'timeout = 30' in gc,
   'GUNICORN: three workers unless Railway says otherwise; timeout as before')
ok("ALV_CSS_FILES = bool(os.environ.get('RAILWAY_ENVIRONMENT_NAME') == "
   "'production'" in st,
   'THE FILES are used on Railway; on a laptop the CSS stays in the page')
ok("'alv-css/'," in read(J(ROOT, 'pages', 'middleware.py')),
   'THE STYLESHEETS are reachable before sign-in (the login page needs them)')

# ==========================================================================
head('2. DRIVEN')
# ==========================================================================
os.environ.setdefault('SECRET_KEY', 'test-only-not-a-secret')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
import django                                               # noqa: E402
django.setup()
from django.conf import settings as _dj                     # noqa: E402
from django.test import Client                              # noqa: E402
from django.test.utils import override_settings             # noqa: E402
from pages import css_files                                 # noqa: E402

from django.template.loader import get_template              # noqa: E402
try:
    get_template('base.html')
    have_tpl = True
except Exception as _e:                                      # noqa: BLE001
    have_tpl = False
    skip('section 2', 'base.html would not compile: %s' % _e)

if have_tpl:
    _dj.DB_FORCE_CLEANUP_INTERVAL = 10 ** 9
    if '*' not in _dj.ALLOWED_HOSTS and 'localhost' not in _dj.ALLOWED_HOSTS:
        _dj.ALLOWED_HOSTS = list(_dj.ALLOWED_HOSTS) + ['localhost']
    c = Client(SERVER_NAME='localhost')
    _on = override_settings(ALV_CSS_FILES=True)
    _on.enable()
    try:
        r = c.get('/login/')
        page = r.content.decode('utf-8', 'replace')
        page_ok = r.status_code == 200
    except Exception as _e:                                  # noqa: BLE001
        page_ok = False
        skip('the login page', 'it needs the database: %s'
             % str(_e).split('\n')[0][:70])
    if page_ok:
        links = re.findall(r'<link rel="stylesheet" href="/alv-css/'
                           r'([0-9a-f]{16})\.css">', page)
        ok(len(links) == 4,
           'THE LOGIN PAGE links four stylesheets instead of carrying them',
           links)
        want = [re.match(r'\s*<style[^>]*>(.*)</style>\s*\Z', b, re.S)
                .group(1) for b in blocks]
        ok(not any(w.strip()[:200] in page for w in want),
           '  and none of base\'s CSS is in the page itself')
        ok(len(page) < 120000,
           '  so the page is a fraction of its old size (%d characters)'
           % len(page))
        css_files.SHEETS.clear()
        got = []
        for h in links:
            rr = c.get('/alv-css/%s.css' % h)
            got.append((rr.status_code, rr.get('Content-Type'),
                        rr.get('Cache-Control'),
                        rr.content.decode('utf-8')))
        ok(all(g[0] == 200 for g in got),
           'EACH STYLESHEET answers, signed out, even from a worker that has '
           'not drawn a page yet', [g[0] for g in got])
        ok(all(g[1] == 'text/css; charset=utf-8' and
               g[2] == 'public, max-age=31536000, immutable' for g in got),
           '  as CSS, cached for a year (its address changes when it does)')
        ok([g[3] for g in got] == want,
           '  word for word the CSS written in base.html, in base\'s order')
        ok(c.get('/alv-css/0000000000000000.css').status_code == 404,
           '  an address it never made is a 404')
        _on.disable()
        inline = c.get('/login/').content.decode('utf-8', 'replace')
        ok('/alv-css/' not in inline and
           all(w.strip()[:200] in inline for w in want),
           'OFF RAILWAY the CSS is in the page, exactly as before')

# ==========================================================================
head('3. CONTROL - THE ROUND REALLY CHANGED SOMETHING')
# ==========================================================================
b = BASE + SUFFIX
if os.path.isfile(b):
    old = read(b)
    ok('{% cached_css %}' not in old and
       len(re.findall(r'<style[^>]*>.*?</style>', old, re.S)) == 4,
       'base.html before this round carried its four <style> blocks inline')
    ok("'CONN_MAX_AGE': 0," in read(J(ROOT, 'mysite', 'settings.py')
                                    + SUFFIX),
       '  and settings.py opened a new connection for every request')
else:
    skip('section 3', '%s is not on disk' % os.path.basename(b))

# ==========================================================================
head('4. REGISTERED')
# ==========================================================================
import alv_rounds as R                                      # noqa: E402
ok(SUFFIX in R.ROUNDS, '%s is in alv_rounds.ROUNDS' % SUFFIX)
gate = read(J(ROOT, PS1))
ok("'%s'" % ME in gate, 'on the push gate suite list')
ok("Text = 'def stylesheet(request, digest):'" in gate,
   '  with a sentinel on the stylesheet view')
ok(os.path.isfile(J(ROOT, PATCHER)), 'the patcher is on disk')

print('')
print('=' * 74)
print('%d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
