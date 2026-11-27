# -*- coding: utf-8 -*-
"""test_ra32_secret_santa_more.py - round RA32, 27 Nov 2026.

RELEASE RA32 - SECRET SANTA: BACK, WHO MAY SEE IT, AND THE REDRAW.
Demetri, 27 Nov: "When I am in Secret Santa and I go Back, it takes me to
the Contacts, instead of back to the place I entered from."
The Celebrations dashboard links with ?from=dashboard, Contacts with
?from=contacts; the session keeps it through the page's own saves and
year chips. Anything else, or nothing, goes back to Celebrations.
"Each user can create and edit their own secret santa events only. They
can however view another users' secret santa event, but do not have the
rights to edit another user's event." And "the ability to re-draw, in case
a new person is added or an existing person is removed (after the initial
draw). It should prompt if this happens." The redraw changes as few pairs
as it can. "Why is the pill at the top showing Christmas 2026??" - the
year switcher only shows when there is something to switch to. "There might
be a need for more than one event per year / xmas" - migration 0123. And
"the user needs to be able to stipulate if this is a XMAS event or other ...
Maybe it is a company party ... the email messages would differ", "signed
by the person who created the event" - Christmas, office party, other.
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

SUFFIX = '.bak_ra32'
ME = 'test_ra32_secret_santa_more.py'
PATCHER = 'apply_ra32_secret_santa_more.py'
PS1 = 'Push-PendingChanges.ps1'
J = os.path.join
PG = J(ROOT, 'pages')
T = J(PG, 'templates')

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

head('1. THE SOURCE')
views = read(J(PG, 'views', 'secret_santa.py'))
page = read(J(T, 'secret_santa.html'))
dash = read(J(T, 'celebration_dashboard.html'))
mgmt = read(J(T, 'celebration_management.html'))
helpt = read(J(PG, 'help_content', 'administration.html'))
ok(dash.count("{% url 'secret_santa' %}?from=dashboard\"") == 2,
   'THE DASHBOARD links say ?from=dashboard (bar and More)')
ok(mgmt.count("{% url 'secret_santa' %}?from=contacts\"") == 2,
   'CONTACTS links say ?from=contacts (bar and More)')
ok("{% url 'celebration_management' %}\" class=\"btn action-back\"" not in page
   and 'href="{{ back_url }}" class="btn action-back"' in page,
   'BACK is no longer fixed on Contacts; it follows back_url')
ok("request.session['santa_back']" in views and 'if src in BACK' in views,
   'ONLY known names are remembered, in the session')
ok('returns to the page you came from' in helpt, 'HELP says where Back goes')
santa = read(J(PG, 'santa.py'))
ok("@permission_required(PERM, raise_exception=True)\ndef secret_santa_save(" in views
   and 'can_edit_celebrations' not in views, 'CELEBRATIONS ACCESS runs your own; edit rights are not asked for')
ok("filter(owner=request.user, year=year)" in views, 'EVERY SAVE is still the signed-in owner\'s own row')
ok('def repair(' in santa and "'change': (" in santa, 'THE REDRAW keeps standing pairs; a Change of plan email')
ok('Redraw and send' in helpt and 'view' in helpt, 'HELP: viewing others, and the redraw')
ok('{% if show_pills %}' in page and "'show_pills': len(events) > 1" in views, 'THE PILLS only when there is a choice')
models = read(J(PG, 'models.py'))
ok("unique_together = [('owner', 'year')]" not in models
   and os.path.isfile(J(PG, 'migrations', '0123_santa_many_per_year.py')), 'MORE THAN ONE A CHRISTMAS (migration 0123)')

head('2. DRIVEN (database)')
os.environ.setdefault('SECRET_KEY', 'test-only-not-a-secret')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
import django                                               # noqa: E402
django.setup()
from django.conf import settings as _dj                     # noqa: E402
if 'testserver' not in _dj.ALLOWED_HOSTS and '*' not in _dj.ALLOWED_HOSTS:
    _dj.ALLOWED_HOSTS = list(_dj.ALLOWED_HOSTS) + ['testserver']
_dj.EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
_dj.DB_FORCE_CLEANUP_INTERVAL = 10 ** 9


class Rollback(Exception):
    pass


try:
    from django.db import transaction
    from django.test import Client
    from django.contrib.auth.models import Permission, User

    def perm(code):
        p, _ = Permission.objects.get_or_create(codename=code, content_type__app_label='auth',
                                                defaults={'name': code})
        return p

    def back_of(resp):
        m = re.search(r'<a href="([^"]*)" class="btn action-back" aria-label="([^"]*)"',
                      resp.content.decode())
        return m.groups() if m else (None, None)

    with transaction.atomic():
        me = User.objects.create_user('ss32_me', 'p32@example.com', 'x')
        me.user_permissions.add(perm('can_access_celebrations'), perm('can_edit_celebrations'))
        C = Client(SERVER_NAME='localhost')
        C.force_login(me)
        url = '/celebrations/secret-santa/'
        ok(back_of(C.get(url)) == ('/celebrations/', 'Back to Celebrations'),
           'NO from: Back goes to the Celebrations dashboard', back_of(C.get(url)))
        ok(back_of(C.get(url + '?from=contacts')) == ('/celebrations/contacts/', 'Back to Contacts'),
           'FROM CONTACTS: Back goes to Contacts')
        ok(back_of(C.get(url + '?year=2025')) == ('/celebrations/contacts/', 'Back to Contacts'),
           '  and still does after a year chip (no from= on it)')
        ok(back_of(C.get(url + '?from=dashboard')) == ('/celebrations/', 'Back to Celebrations'),
           'FROM THE DASHBOARD: Back goes to Celebrations')
        ok(back_of(C.get(url + '?from=https://evil.example')) == ('/celebrations/', 'Back to Celebrations'),
           'AN UNKNOWN from is ignored - never an outside address')
        d = C.get('/celebrations/').content.decode()
        ok('/celebrations/secret-santa/?from=dashboard' in d, 'THE DASHBOARD renders the from= link')
        ok('class="ss-years"' not in C.get(url).content.decode(), 'ONE CHRISTMAS, no others: no year pills')
        raise Rollback
except Rollback:
    pass
except Exception as e:                                       # noqa: BLE001
    import traceback
    traceback.print_exc()
    ok(False, 'section 2 ran', str(e)[:200])

head('3. WHO MAY SEE IT, AND THE REDRAW')
try:
    import random
    from django.core import mail
    from django.utils import timezone
    from pages.models import SantaExchange, SantaPerson, UserProfile
    from pages.workspace import ensure_workspace
    from pages import santa as SS

    # the repair, on its own
    rng = random.Random(7)
    full = {i: {j for j in range(1, 6) if j != i} for i in range(1, 6)}
    now = {1: 2, 2: 3, 3: 4, 4: 5, 5: 1}
    ok(SS.repair(full, now, rng) == now and SS.stale(full, now) == 0, 'REPAIR: a whole draw is left alone')
    add = {i: {j for j in range(1, 7) if j != i} for i in range(1, 7)}
    got = SS.repair(add, now, rng)
    ch = {g for g in got if now.get(g) != got[g]}
    ok(SS.stale(add, now) == 1 and len(ch) == 2 and 6 in ch and sorted(got.values()) == [1, 2, 3, 4, 5, 6]
       and all(g != r for g, r in got.items()), 'REPAIR: a newcomer splits one pair - two people change')
    rem = {i: {j for j in (1, 2, 4, 5) if j != i} for i in (1, 2, 4, 5)}
    got = SS.repair(rem, now, rng)
    ch = {g for g in got if now.get(g) != got[g]}
    ok(ch == {2} and got[2] == 4, 'REPAIR: a leaver\'s Santa takes the leaver\'s person - one changes')
    bad = 0
    for _ in range(200):
        n = rng.randint(4, 12)
        ok_ = {i: {j for j in range(n) if j != i and rng.random() > 0.15} for i in range(n)}
        base = SS.draw(ok_, rng)
        if base is None:
            continue
        ok2 = {i: set(v) for i, v in ok_.items() if i != 0}
        for v in ok2.values():
            v.discard(0)
        ok2[n] = {j for j in range(1, n)}
        for i in range(1, n):
            ok2[i].add(n)
        g2 = SS.repair(ok2, base, rng)
        if g2 is None:
            continue
        if (sorted(g2) != sorted(ok2) or len(set(g2.values())) != len(g2)
                or any(r not in ok2[g] for g, r in g2.items())):
            bad += 1
    ok(bad == 0, 'REPAIR, 200 random rosters: always a valid draw within the rules')

    with transaction.atomic():
        me = User.objects.create_user('ss32_owner', 'own32@example.com', 'x', first_name='Demetri')
        she = User.objects.create_user('ss32_she', 'she32@example.com', 'x', first_name='Angie')
        out = User.objects.create_user('ss32_out', 'out32@example.com', 'x')
        for u in (me, she, out):
            u.user_permissions.add(perm('can_access_celebrations'))     # NOT edit
        C, S, O = (Client(SERVER_NAME='localhost') for _ in range(3))
        C.force_login(me)
        S.force_login(she)
        O.force_login(out)
        ws = ensure_workspace(me)       # after the logins, as RA31's suite does
        UserProfile.objects.update_or_create(user=me, defaults={'workspace': ws})
        UserProfile.objects.update_or_create(user=she, defaults={'workspace': ws})
        ensure_workspace(out)
        url, save, Y = '/celebrations/secret-santa/', '/celebrations/secret-santa/save/', 2026
        C.post(save, {'action': 'event', 'year': Y, 'title': 'Full Manias Family', 'event_date': '2026-12-25',
                      'budget': '40', 'remind_week': '1'})
        ex = SantaExchange.objects.filter(owner=me, year=Y).first()
        ok(ex is not None, 'ACCESS ALONE (no edit rights) sets up your own Secret Santa')
        for f, e in (('Demetri', 'd32@example.com'), ('Angie', 'a32@example.com'), ('Alex', 'x32@example.com'),
                     ('Erene', 'e32@example.com'), ('Laz', 'l32@example.com')):
            C.post(save, {'action': 'person_add', 'year': Y, 'first_name': f, 'email': e})
        mail.outbox = []
        C.post(save, {'action': 'draw', 'year': Y})
        ex.refresh_from_db()
        ok(ex.drawn_at and ex.pairs.count() == 5 and len(mail.outbox) == 5, '  and draws it: five pairs, five emails')

        # viewing
        t = S.get(url).content.decode()
        ok('?ex=%d' % ex.pk in t and 'Demetri &middot; Full Manias Family' in t, 'SHE SEES his among Others\'')
        t = S.get(url + '?ex=%d' % ex.pk).content.decode()
        ok('Full Manias Family' in t and 'Alex' in t and 'Only they can change it' in t, '  and can open it to view')
        ok('/celebrations/secret-santa/save/' not in t and 'name="action"' not in t and '#ssDrawModal' not in t
           and 'icon-action-btn icon-delete' not in t and '/celebrations/secret-santa/preview/' not in t,
           '  read-only: no form, no button that sends',
           [k for k in ('/celebrations/secret-santa/save/', 'name="action"', '#ssDrawModal', 'icon-action-btn icon-delete',
                        '/celebrations/secret-santa/preview/') if k in t])
        ex.revealed_at = timezone.now()
        ex.save()
        t = S.get(url + '?ex=%d' % ex.pk).content.decode()
        ok('&rarr;' not in t, '  and never a pairing, even after he revealed them')
        ex.revealed_at = None
        ex.save()
        S.post(save, {'action': 'person_add', 'year': Y, 'first_name': 'Hack', 'email': 'h32@example.com'})
        ok(not ex.people.filter(email='h32@example.com').exists(), '  her saves land on her own, never his')
        # a second event the same Christmas
        C.post(save, {'action': 'event', 'year': Y, 'title': 'Friends', 'event_date': '2026-12-23'})
        two = list(SantaExchange.objects.filter(owner=me, year=Y).order_by('id'))
        t = C.get(url + '?ex=%d' % two[0].pk).content.decode()
        ok(len(two) == 2 and two[1].title == 'Friends' and two[1].people.count() == 0
           and 'Friends</a>' in t and 'Full Manias Family</a>' in t,
           'A SECOND SECRET SANTA THE SAME CHRISTMAS: its own, and both pills show')
        C.post(save, {'action': 'person_add', 'ex': two[1].pk, 'first_name': 'Bob', 'email': 'b32@example.com'})
        ok(two[1].people.count() == 1 and ex.people.count() == 5, '  people go to the event named, not the other')
        C.post(save, {'action': 'person_add', 'ex': ex.pk, 'first_name': 'Hack', 'email': 'hh32@example.com'}, )
        S.post(save, {'action': 'person_add', 'ex': ex.pk, 'first_name': 'Hack', 'email': 'h32@example.com'})
        ok(not ex.people.filter(email='h32@example.com').exists(), '  naming his event, she still cannot add to it')
        ex.people.filter(email='hh32@example.com').delete()
        two[1].delete()
        # the occasion and who signs
        from pages.models import SantaPerson as SP
        mail.outbox = []
        ok(SS.santa_name(ex) == 'Santa (Demetri)', 'CHRISTMAS: signed Santa (the creator\'s first name)')
        S.post(save, {'action': 'event', 'year': Y, 'title': '', 'occasion': 'office', 'event_date': '2026-12-18',
                      'budget': '25'})
        off = SantaExchange.objects.filter(owner=she).first()
        she.last_name = 'Manias'
        she.save()
        off.refresh_from_db()
        p1 = SP(first_name='Bob', email='bob@example.com')
        s1, txt, h = SS.message(off, 'draw', p1, 'Carol Day')
        ok(off.occasion == 'office' and off.title == 'Office party 2026' and SS.santa_name(off) == 'Angie Manias'
           and 'Hi Bob,' in h and 'Ho ho ho' not in h and 'Merry Christmas' not in h and '&#127876;' not in h
           and 'Thank you' in h and 'gift exchange' in s1 and 'Angie Manias' in txt,
           'OFFICE PARTY: businesslike, no Christmas words, signed with her full name', s1)
        s2, txt2, h2 = SS.message(off, 'reveal', p1, 'Carol Day')
        ok('secret gift-giver' in h2 and 'Thank you</b> for taking part' in h2, '  its reveal too')
        S.post(save, {'action': 'event', 'year': Y, 'occasion': 'other', 'occasion_name': 'Easter',
                      'event_date': '2027-04-04'})
        eas = SantaExchange.objects.filter(owner=she, occasion='other').first()
        s3, txt3, h3 = SS.message(eas, 'draw', p1, 'Carol Day')
        ok(eas and eas.year == 2027 and eas.title == 'Easter 2027' and 'Hi Bob!' in h3 and 'Happy gifting!' in h3
           and 'Santa (Angie)' in h3 and 'Christmas' not in h3, 'OTHER OCCASION: named by her, friendly, no Christmas words')
        s4, t4, h4 = SS.message(ex, 'draw', p1, 'Carol Day')
        ok('Ho ho ho, Bob!' in h4 and 'Merry Christmas!' in h4 and '&#127876;' in h4 and s4.endswith('your Secret Santa')
           and "keep it secret - don't tell anyone who you drew." in t4, 'CHRISTMAS reads exactly as before')
        ok(SS.last_year_pairs(eas) == {} and SS.last_year_pairs(off) == {}, '  last year\'s pairs: Christmas only')
        t = S.get(url + '?ex=%d' % off.pk).content.decode()
        ok('value="office" selected' in t, '  the page shows the occasion chosen')
        r = O.get(url + '?ex=%d' % ex.pk)
        ok(r.status_code == 302 and SantaExchange.objects.filter(owner=out).count() == 0,
           'OUTSIDE THE HOUSEHOLD: not viewable')

        # the redraw
        before = dict(ex.pairs.values_list('giver_id', 'receiver_id'))
        r = C.post(save, {'action': 'person_add', 'year': Y, 'first_name': 'Lida', 'email': 'li32@example.com'}, follow=True)
        lida = ex.people.get(email='li32@example.com')
        t = r.content.decode()
        ok('Redraw and send' in t and 'draw needs updating' in t, 'A PERSON JOINS AFTER THE DRAW: the page prompts Redraw and send')
        mail.outbox = []
        C.post(save, {'action': 'redraw', 'year': Y})
        after = dict(ex.pairs.values_list('giver_id', 'receiver_id'))
        changed = {g for g in after if before.get(g) != after[g]}
        tos = sorted(m.to[0] for m in mail.outbox)
        ok(len(after) == 6 and len(changed) == 2 and lida.pk in changed and len(mail.outbox) == 2,
           '  REDRAW: six pairs, only two changed, two emails', (len(after), changed, tos))
        subj = {m.to[0]: m.subject for m in mail.outbox}
        other = [p.email for p in ex.people.filter(pk__in=changed - {lida.pk})]
        ok('your Secret Santa' in subj.get('li32@example.com', '') and other
           and subj.get(other[0], '').startswith('Change of plan'), '  the newcomer the usual email, the other "Change of plan"')
        ok(all(g != r for g, r in after.items()) and len(set(after.values())) == 6, '  still everyone gives once and receives once')
        t = C.get(url).content.decode()
        ok('draw needs updating' not in t and '&rarr;' not in t, '  then the prompt goes; still no pairing shown')

        before = after
        gone = ex.people.get(first_name='Laz')
        santa_of_gone = next(g for g, r in before.items() if r == gone.pk)
        C.post(save, {'action': 'person_remove', 'year': Y, 'pid': gone.pk})
        mail.outbox = []
        C.post(save, {'action': 'redraw', 'year': Y})
        after = dict(ex.pairs.values_list('giver_id', 'receiver_id'))
        changed = {g for g in after if before.get(g) != after[g]}
        ok(len(after) == 5 and changed == {santa_of_gone} and len(mail.outbox) == 1
           and mail.outbox[0].subject.startswith('Change of plan'),
           'A PERSON LEAVES: only their Santa gets a new person, one "Change of plan" email')
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
