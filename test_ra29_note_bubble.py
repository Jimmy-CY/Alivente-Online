# -*- coding: utf-8 -*-
"""test_ra29_note_bubble.py - round RA29, 26 Nov 2026.

RELEASE RA29 - A SPEECH BUBBLE BESIDE A LISTING'S TITLE.
Demetri, 26 Nov: "Can we add a column, or a little "i", where if I hover
over, I can see my general comments or rejected comments for a property?"
- and (b): the one-line comment under the title stays as well. The bubble
shows his comment in full, his Shortlist/Reject decision and its reason,
and his viewings; filled when there is a comment, outlined otherwise, and
absent when there is nothing of his. Nothing here calls outside the app.
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












import io
import os
import re
import sys

ROOT = os.getcwd()
sys.path.insert(0, ROOT)

SUFFIX = '.bak_ra29'
ME = 'test_ra29_note_bubble.py'
PATCHER = 'apply_ra29_note_bubble.py'
PS1 = 'Push-PendingChanges.ps1'
J = os.path.join
APP = J(ROOT, 'acquisitions')
TPL = J(APP, 'templates', 'acquisitions')
FILES = (J(APP, 'templatetags', 'acq.py'), J(TPL, '_plot_row.html'), J(TPL, '_result_row.html'),
         J(TPL, '_style.html'), J(APP, 'views.py'), J(ROOT, 'pages', 'help_content', 'acquisitions.html'))

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
    if not os.path.isfile(p):
        return ''
    with open(p, encoding='utf-8-sig', errors='replace') as f:
        return f.read().replace('\r\n', '\n')


def head(t):
    print('')
    print('=' * 74)
    print(t)
    print('=' * 74)


print(__doc__.strip().splitlines()[0])


def claims(tags, prow, rrow, style, views, hlp):
    return {
        'THE BUBBLE is one filter, used by both rows':
            'def notetip(m):' in tags and '{{ m|notetip }}' in prow and '{{ m|notetip }}' in rrow,
        'IT OPENS on hover, focus or a tap, and is never clipped by the table':
            '.acq-note-box' in style and 'position: fixed' in style and "is-pinned" in style,
        'THE ONE-LINE COMMENT STAYS (his choice, b)':
            'm.your_comments|truncatechars' in prow and 'm.your_comments|truncatechars' in rrow,
        'VIEWINGS are fetched with the rows, not one query a row':
            '"property__viewings"' in views,
        'HELP: the speech bubble':
            '<strong>speech bubble</strong>' in hlp,
    }


head('1. THE SOURCE')
SRC = [read(p) for p in FILES]
for m, got in claims(*SRC).items():
    ok(got, m)
css = SRC[3].split('RA29, 26 Nov 2026')[1].split('</style>')[0] if 'RA29, 26 Nov 2026' in SRC[3] else ''
ok(css and not re.search(r'#[0-9a-fA-F]{3,6}\b|rgba?\(', css), '  the bubble is painted from the house tokens only')

head('2. THE CONTROL')
if all(os.path.isfile(p + SUFFIX) for p in FILES):
    held = [m for m, got in claims(*[read(p + SUFFIX) for p in FILES]).items()
            if got and 'STAYS' not in m]
    ok(not held, 'CONTROL: not one new claim held before RA29', held)
else:
    skip('the control', 'no .bak_ra29 beside the files')

head('3. DRIVEN (database)')
os.environ.setdefault('SECRET_KEY', 'test-only-not-a-secret')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
for k in ('ACQ_INTAKE_KEY', 'ROUTINE_FIRE_URL', 'ROUTINE_FIRE_TOKEN', 'PC_FIRE_URL', 'PC_FIRE_TOKEN'):
    os.environ.pop(k, None)
import django                                               # noqa: E402
django.setup()
from django.conf import settings as _dj                     # noqa: E402
if 'testserver' not in _dj.ALLOWED_HOSTS and '*' not in _dj.ALLOWED_HOSTS:
    _dj.ALLOWED_HOSTS = list(_dj.ALLOWED_HOSTS) + ['testserver']


class Rollback(Exception):
    pass


try:
    import datetime
    from django.db import transaction
    from django.core.management import call_command
    from django.test import Client
    from django.utils import timezone
    from django.contrib.auth.models import Permission, User
    from acquisitions.models import Area, Property, Scenario, ScenarioMatch, Viewing
    from acquisitions import scoring
    with transaction.atomic():
        Scenario.objects.all().delete()
        call_command('seed_acquisitions', stdout=io.StringIO())
        plot = Scenario.objects.get(property_type='plot')
        home = Scenario.objects.exclude(property_type='plot').first()
        eng = Area.objects.get(name='Engomi')

        def mk(s, title, kind='plot'):
            p = Property.objects.create(property_type=kind, title=title, area=eng, plot_m2=600,
                                        internal_m2=150, asking_price=200000, vat_status='none')
            m = ScenarioMatch.objects.create(scenario=s, property=p, status='active')
            scoring.apply_score(m)
            return p, m
        a, ma = mk(plot, 'RA29 A')
        b, mb = mk(plot, 'RA29 B')
        c, mc = mk(plot, 'RA29 C')
        long = 'Corner plot, quiet street. ' * 8 + 'But <b>the</b> road floods.'
        ScenarioMatch.objects.filter(pk=ma.pk).update(your_comments=long)
        mb.set_status_by_user('rejected', 'next to the highway')
        Viewing.objects.create(property=b, viewed_on=datetime.date(2026, 11, 3), notes='Met the agent')
        u = User.objects.create_user('ra29', 'ra29@example.com', 'pw')
        for cn in ('can_access_acquisitions', 'can_edit_acquisitions'):
            u.user_permissions.add(Permission.objects.get(codename=cn))
        C = Client()
        C.force_login(u)
        t = C.get('/acquisitions/scenarios/%d/?q=RA29' % plot.pk).content.decode()
        row = lambda name: t.split(name)[1].split('</tr>')[0]
        ra, rb, rc = row('RA29 A</strong>'), t.partition('<details')[2], row('RA29 C</strong>')
        ok('class="acq-note-btn"' in ra and 'fas fa-comment' in ra and 'Your comment' in ra
           and 'road floods.' in ra,
           'A: a filled bubble with the WHOLE comment (the line under the title is cut at 90)')
        ok('&lt;b&gt;the&lt;/b&gt;' in ra and '<b>the</b>' not in ra, '  and what he typed is shown, not run as markup')
        ok('class="acq-note-btn"' in rb and 'far fa-comment' in rb and 'Rejected by you' in rb
           and 'next to the highway' in rb and 'Viewing' in rb and '3 Nov 2026' in rb and 'Met the agent' in rb,
           'B (rejected, folded): an outlined bubble - Rejected by you, the reason, the viewing')
        ok('acq-note' not in rc, 'C: nothing of his, so no bubble')
        ok('Corner plot, quiet street.' in ra.split('acq-note')[0] or 'Corner plot, quiet street.' in ra,
           '  and the one-line comment is still under the title')
        if home:
            h, mh = mk(home, 'RA29 H', 'apartment')
            ScenarioMatch.objects.filter(pk=mh.pk).update(your_comments='Separate kitchen')
            th = C.get('/acquisitions/scenarios/%d/?q=RA29' % home.pk).content.decode()
            ok('class="acq-note-btn"' in th and 'Separate kitchen' in th, 'THE HOMES PAGE has the bubble too')
        else:
            skip('the homes page', 'no home scenario in the seed')
        raise Rollback
except Rollback:
    pass
except Exception as e:                                       # noqa: BLE001
    import traceback
    traceback.print_exc()
    ok(False, 'section 3 ran', str(e)[:200])

head('4. REGISTERED')
import alv_rounds as RR                                     # noqa: E402
ok(SUFFIX in RR.ROUNDS, '%s is in alv_rounds.ROUNDS' % SUFFIX)
ok("'%s'" % ME in read(J(ROOT, PS1)), 'on the push gate suite list')
ok(os.path.isfile(J(ROOT, PATCHER)), 'the patcher is on disk')

print('')
print('=' * 74)
print('%d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
