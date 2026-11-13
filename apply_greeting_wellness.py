# -*- coding: utf-8 -*-
"""apply_greeting_wellness.py - round PT-4, 13 Nov 2026.

RELEASE 76 - A CELEBRATION ON WELLNESS TODAY OPENS ITS GREETING: Claude
writes it, English or Greek, change anything, Open in WhatsApp.

New files ship beside this patcher. Stands on Releases 74 and 75.
Idempotent. Edits backed up to .bak_greetwell. No migration.
"""
import os
import sys

SUFFIX = '.bak_greetwell'
MARK = 'PT-4, 13 Nov 2026'
CHECK = False
PS1 = 'Push-PendingChanges.ps1'
CREATES = (
    'wellness/views_greeting.py',
    'wellness/templates/wellness/greeting.html',
    'test_wellness_twentysix.py',
)

SWAPS = [
    (os.path.join('Push-PendingChanges.ps1'), [
        (r'''    @{ File = 'pages/models.py'; Text = 'class Gift(models.Model):'; What = 'CG-1: gifts - without it migration 0119 has no model and Celebrations cannot open' },
    @{ File = 'pages/views/celebration_gifts.py'; Text = 'def my_gifts(request):'; What = 'CG-1: My gifts and the Christmas list - without it the Celebrations links go nowhere' },
    @{ File = 'pages/meal_calendar.py'; Text = 'class MealCalendarMiddleware:'; What = 'MS-1: which meal plan a request is about - without it the planner cannot open' },
    @{ File = 'wellness/crypto.py'; Text = 'def seal_bytes('; What = 'WL-19: the lock for progress photos is on disk - without it no photo can be saved or shown' },
''',
         r'''    @{ File = 'pages/models.py'; Text = 'class Gift(models.Model):'; What = 'CG-1: gifts - without it migration 0119 has no model and Celebrations cannot open' },
    @{ File = 'pages/views/celebration_gifts.py'; Text = 'def my_gifts(request):'; What = 'CG-1: My gifts and the Christmas list - without it the Celebrations links go nowhere' },
    @{ File = 'wellness/views_greeting.py'; Text = 'def greeting(request, event_id):'; What = 'PT-4: a celebration on Today opens its greeting - without it the card links to nothing' },
    @{ File = 'pages/meal_calendar.py'; Text = 'class MealCalendarMiddleware:'; What = 'MS-1: which meal plan a request is about - without it the planner cannot open' },
    @{ File = 'wellness/crypto.py'; Text = 'def seal_bytes('; What = 'WL-19: the lock for progress photos is on disk - without it no photo can be saved or shown' },
'''),
        (r'''    'test_wellness_twentyfive.py',
    # BV-1 + CG-1, 13 Nov 2026 - Releases 74 and 75: the recipe book on demand; gifts.
    'test_gifts.py'
)
# NUMBER EVERY SUITE AS IT RUNS - Demetri, 1 Oct 2026: "for every check of
''',
         r'''    'test_wellness_twentyfive.py',
    # BV-1 + CG-1, 13 Nov 2026 - Releases 74 and 75: the recipe book on demand; gifts.
    'test_gifts.py',
    # PT-4, 13 Nov 2026 - Release 76: a celebration on Today opens its greeting.
    'test_wellness_twentysix.py'
)
# NUMBER EVERY SUITE AS IT RUNS - Demetri, 1 Oct 2026: "for every check of
'''),
    ]),
    (os.path.join('pages', 'templates', 'lease_signing_list.html'), [
        (r'''        <i class="fas fa-question-circle"></i> Help
    </button>
    <a href="{% url 'admin_apms' %}?tab=functional" class="btn action-back"
       role="button" aria-label="Back to Administration">
''',
         r'''        <i class="fas fa-question-circle"></i> Help
    </button>
    {# PT-4, 13 Nov 2026 - Demetri, 09:15: "Buttons do not look right on  #}
    {# mobile" - four wide buttons in a phone's width, Start e-signing cut. #}
    {# The house "More": below 768px base hides the two secondaries above  #}
    {# and they are in here, so a phone gets Start e-signing, More, Back.  #}
    <div class="action-more-wrapper" data-menu>
        <button type="button" class="btn action-more-btn" id="actionMoreBtn" data-menu-toggle
                aria-label="More actions" aria-expanded="false" aria-haspopup="true">
            <i class="fas fa-ellipsis-v"></i>
        </button>
        <div class="action-more-menu" id="actionMoreMenu" data-menu-panel role="menu" hidden>
            {% if show_all %}
            <a href="{% url 'lease_signing_list' %}" class="action-more-item" role="menuitem">
                <i class="fas fa-hourglass-half"></i> Live only
            </a>
            {% else %}
            <a href="{% url 'lease_signing_list' %}?all=1" class="action-more-item" role="menuitem">
                <i class="fas fa-clock-rotate-left"></i> Include finished
            </a>
            {% endif %}
            <button type="button" class="action-more-item" role="menuitem"
                    data-toggle="modal" data-target="#lease_signingHelpModal">
                <i class="fas fa-question-circle"></i> Help
            </button>
        </div>
    </div>
    <a href="{% url 'admin_apms' %}?tab=functional" class="btn action-back"
       role="button" aria-label="Back to Administration">
'''),
    ]),
    (os.path.join('pages', 'templates', 'lease_signing_detail.html'), [
        (r'''        <i class="fas fa-file-word"></i> Word version
    </a>
    {% endif %}
    <a href="{% url 'lease_signing_list' %}?all=1" class="btn action-back"
''',
         r'''        <i class="fas fa-file-word"></i> Word version
    </a>
    {% endif %}
    {# PT-4, 13 Nov 2026 - Demetri, 09:16: on a phone the bar ran off the  #}
    {# edge. The house "More": below 768px base hides the secondaries     #}
    {# above, and they are in here - Decline as a red item, still through #}
    {# its own form and its own "cannot be undone" question.             #}
    {% if awaiting and user.is_superuser or env.sealed_pdf or env.word_docx %}
    <div class="action-more-wrapper" data-menu>
        <button type="button" class="btn action-more-btn" id="actionMoreBtn" data-menu-toggle
                aria-label="More actions" aria-expanded="false" aria-haspopup="true">
            <i class="fas fa-ellipsis-v"></i>
        </button>
        <div class="action-more-menu" id="actionMoreMenu" data-menu-panel role="menu" hidden>
            {% if env.sealed_pdf %}
            <a href="{% url 'lease_signing_sealed' env.pk %}" class="action-more-item" role="menuitem"
               onclick="openPdfViewer('{% url 'lease_signing_sealed' env.pk as sealed_url2 %}{{ sealed_url2|escapejs }}', 'Signed lease &mdash; {{ tenant.tenant_display_name|escapejs }}', 'lease-agreement-signed-{{ env.pk|escapejs }}.pdf'); return false;">
                <i class="fas fa-file-pdf"></i> View signed lease
            </a>
            {% endif %}
            {% if env.word_docx %}
            <a href="{% url 'lease_signing_word' env.pk %}" class="action-more-item" role="menuitem">
                <i class="fas fa-file-word"></i> Word version
            </a>
            {% endif %}
            {% if awaiting and user.is_superuser %}
            <button type="submit" form="lsd-decline-form" class="action-more-item action-more-item-danger" role="menuitem">
                <i class="fas fa-times"></i> Decline
            </button>
            {% endif %}
        </div>
    </div>
    {% endif %}
    <a href="{% url 'lease_signing_list' %}?all=1" class="btn action-back"
'''),
    ]),
    (os.path.join('pages', 'templates', 'view_recipe.html'), [
        (r'''.cm-next { border: 0; background: var(--alv-accent); color: var(--alv-on-accent); }
.cm-prev:disabled { opacity: .4; }
.cooked-section { margin-top: 24px; }
.cooked-summary { color: var(--alv-ink-soft); margin: 0 0 12px; }
''',
         r'''.cm-next { border: 0; background: var(--alv-accent); color: var(--alv-on-accent); }
.cm-prev:disabled { opacity: .4; }
/* PT-4, 13 Nov 2026 - cook mode on a wide screen (Demetri, 09:14: "does
   not look good on Desktop"): one centred reading column, larger type,
   the buttons under the step rather than across the window. */
@media screen and (min-width: 720px) {
  .cm-screen { align-items: center; justify-content: center; padding-top: 48px; padding-bottom: 48px; }
  .cm-screen > * { width: 100%; max-width: 680px; }
  .cm-text { flex: 0 1 auto; font-size: 32px; min-height: 30vh; }
}
.cooked-section { margin-top: 24px; }
.cooked-summary { color: var(--alv-ink-soft); margin: 0 0 12px; }
'''),
    ]),
    (os.path.join('alv_rounds.py'), [
        (r'''    # BV-1 + CG-1, 13 Nov 2026 - Releases 74 and 75: the book on demand; gifts.
    '.bak_gifts',
]

''',
         r'''    # BV-1 + CG-1, 13 Nov 2026 - Releases 74 and 75: the book on demand; gifts.
    '.bak_gifts',
    # PT-4, 13 Nov 2026 - Release 76: the greeting from Wellness Today.
    '.bak_greetwell',
]

'''),
    ]),
    (os.path.join('wellness', 'assets', 'wellness.css'), [
        (r'''.cm-next { border: 0; background: var(--w-sage-deep); color: var(--w-on-accent); }
.cm-prev:disabled { opacity: .4; }
@media (prefers-color-scheme: dark) {
  .w-home-when.gone, .cm-timer-btn.is-done { color: #F0A097; }
  .cm-timer-btn.is-done { border-color: #F0A097; }
  .w-rc-star:has(input:checked), .w-rc-star:has(~ .w-rc-star input:checked), .w-rc-stars:hover .w-rc-star, .w-rc-rate { color: #E9B56A; }
}
''',
         r'''.cm-next { border: 0; background: var(--w-sage-deep); color: var(--w-on-accent); }
.cm-prev:disabled { opacity: .4; }
/* PT-4, 13 Nov 2026 - cook mode on a wide screen (Demetri, 09:14: "does
   not look good on Desktop"): one centred reading column, larger type,
   the buttons under the step rather than across the window. */
@media screen and (min-width: 720px) {
  .cm-screen { align-items: center; justify-content: center; padding-top: 48px; padding-bottom: 48px; }
  .cm-screen > * { width: 100%; max-width: 680px; }
  .cm-text { flex: 0 1 auto; font-size: 32px; min-height: 30vh; }
}
@media (prefers-color-scheme: dark) {
  .w-home-when.gone, .cm-timer-btn.is-done { color: #F0A097; }
  .cm-timer-btn.is-done { border-color: #F0A097; }
  .w-rc-star:has(input:checked), .w-rc-star:has(~ .w-rc-star input:checked), .w-rc-stars:hover .w-rc-star, .w-rc-rate { color: #E9B56A; }
}

/* PT-4, 13 Nov 2026 - the greeting page: a roomy message box and the
   WhatsApp button with its mark. */
.w-gr-text { min-height: 150px; resize: vertical; font-size: 16px; line-height: 1.5; padding: 12px 14px; }
.w-gr-send { display: flex; align-items: center; justify-content: center; gap: 8px; text-decoration: none; }
'''),
    ]),
    (os.path.join('wellness', 'home.py'), [
        (r'''
  CELEBRATIONS  today only: events relevant to them (they are in
                "relevant to"). Nobody today: no line.
  MEALS         every meal planned today, from their own meal plan and
                plans shared with them. A recipe opens inside Wellness
''',
         r'''
  CELEBRATIONS  today only: events relevant to them (they are in
                "relevant to"). Nobody today: no line. PT-4, 13 Nov: a tap
                opens a greeting written by Claude, sent by WhatsApp.
  MEALS         every meal planned today, from their own meal plan and
                plans shared with them. A recipe opens inside Wellness
'''),
        (r'''        elif e.event_type == 'anniversary' and n:
            what = 'anniversary, %d years' % n
        rows.append({'name': e.contact.name, 'what': what})
    rows.sort(key=lambda r: r['name'])
    return rows
''',
         r'''        elif e.event_type == 'anniversary' and n:
            what = 'anniversary, %d years' % n
        rows.append({'name': e.contact.name, 'what': what,
                     # PT-4 - a tap opens the greeting (views_greeting).
                     'event_id': e.pk})
    rows.sort(key=lambda r: r['name'])
    return rows
'''),
    ]),
    (os.path.join('wellness', 'templates', 'wellness', 'today.html'), [
        (r'''</header>

{% comment %} PT-1, 12 Nov 2026 - At home today. PT-2, the same evening: the card is the whole of it - today's celebrations (plain lines), every meal planned today (a recipe opens inside Wellness, with Cook mode) and your own documents from the start of their reminder window (plain lines). Only when there is something to say. {% endcomment %}
{% if home %}
<section class="w-card w-home-card" data-home-card>
  <span class="w-home-head"><span class="w-h2" style="font-size:16px">At home today</span></span>
  {% for r in home.cel %}
  <span class="w-home-row" data-home-cel><span class="w-home-ico cel"><svg width="18" height="18" viewBox="0 0 24 24" aria-hidden="true"><rect x="4" y="9" width="16" height="11" rx="1.5" fill="none" stroke="currentColor" stroke-width="1.8"/><path d="M12 9v11M4 13h16M12 9c-2-4-6-4-6-1.5S12 9 12 9zm0 0c2-4 6-4 6-1.5S12 9 12 9z" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"/></svg></span><span class="w-home-text"><b>{{ r.name }}</b><span>{{ r.what|capfirst }}</span></span><span class="w-home-when soon">Today</span></span>
  {% endfor %}
  {% for m in home.meals %}
''',
         r'''</header>

{% comment %} PT-1, 12 Nov 2026 - At home today. PT-2, the same evening: the card is the whole of it - today's celebrations (each opens its greeting - PT-4), every meal planned today (a recipe opens inside Wellness, with Cook mode) and your own documents from the start of their reminder window (plain lines). Only when there is something to say. {% endcomment %}
{% if home %}
<section class="w-card w-home-card" data-home-card>
  <span class="w-home-head"><span class="w-h2" style="font-size:16px">At home today</span></span>
  {% for r in home.cel %}
  {# PT-4, 13 Nov 2026 - a celebration opens its greeting (Demetri, 09:01). #}
  <a class="w-home-row" href="{% url 'wellness:greeting' r.event_id %}" data-home-cel><span class="w-home-ico cel"><svg width="18" height="18" viewBox="0 0 24 24" aria-hidden="true"><rect x="4" y="9" width="16" height="11" rx="1.5" fill="none" stroke="currentColor" stroke-width="1.8"/><path d="M12 9v11M4 13h16M12 9c-2-4-6-4-6-1.5S12 9 12 9zm0 0c2-4 6-4 6-1.5S12 9 12 9z" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"/></svg></span><span class="w-home-text"><b>{{ r.name }}</b><span>{{ r.what|capfirst }}</span></span><span class="w-home-when soon">Today</span><svg class="w-home-go" width="16" height="16" viewBox="0 0 16 16" aria-hidden="true"><path d="M6 3.5L10.5 8 6 12.5" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg></a>
  {% endfor %}
  {% for m in home.meals %}
'''),
    ]),
    (os.path.join('wellness', 'templates', 'wellness', 'base.html'), [
        (r'''<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,500&amp;family=Inter:wght@400;500;600&amp;display=swap">
<link rel="stylesheet" href="{% url 'wellness:asset' 'wellness.css' %}?v=wl24-1">
</head>
{% load tz %}{% get_current_timezone as W_TZ %}
''',
         r'''<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,500&amp;family=Inter:wght@400;500;600&amp;display=swap">
<link rel="stylesheet" href="{% url 'wellness:asset' 'wellness.css' %}?v=wl25-1">
</head>
{% load tz %}{% get_current_timezone as W_TZ %}
'''),
        (r'''</nav>
{% endblock %}
<script src="{% url 'wellness:asset' 'wellness.js' %}?v=wl24-1" defer></script>
</body>
</html>
''',
         r'''</nav>
{% endblock %}
<script src="{% url 'wellness:asset' 'wellness.js' %}?v=wl25-1" defer></script>
</body>
</html>
'''),
    ]),
    (os.path.join('wellness', 'help.py'), [
        (r'''            'done, and is back on Monday.',
            'Tap the arrow beside a habit to see its calendar and streak.',
            'At home today, at the top: who celebrates today, today\'s '
            'meals (tap a recipe to open it, with Cook mode) and your '
            'documents due for renewal.',
            'Take a breath, weigh in, or write a few lines, from the cards '
            'below.',
''',
         r'''            'done, and is back on Monday.',
            'Tap the arrow beside a habit to see its calendar and streak.',
            'At home today, at the top: who celebrates today (tap to send '
            'a greeting), today\'s meals (tap a recipe for Cook mode) and '
            'your documents due for renewal.',
            'Take a breath, weigh in, or write a few lines, from the cards '
            'below.',
'''),
        (r'''    # PT-2, 12 Nov 2026 - At home today is the card on Today; a recipe
    # from it opens here.
    'recipe': {
        'title': 'A recipe',
''',
         r'''    # PT-2, 12 Nov 2026 - At home today is the card on Today; a recipe
    # from it opens here.
    # PT-4, 13 Nov 2026 - a celebration on the card opens its greeting.
    'greeting': {
        'title': 'A greeting',
        'purpose': 'A message for someone celebrating today, sent by '
                   'WhatsApp.',
        'steps': [
            'Claude writes a short message. Pick English or Ελληνικά and it '
            'writes it again in that language.',
            'Change anything you like in the box.',
            'Open in WhatsApp: it goes to their number, or WhatsApp asks '
            'who to send it to.',
            'Write another, for a different one.',
        ],
        'signs': [],
    },
    'recipe': {
        'title': 'A recipe',
'''),
    ]),
    (os.path.join('wellness', 'guide.py'), [
        (r'''    {'q': 'What is At home today?',
     'a': 'A card at the top of Today with the rest of your Alivente: who '
          'celebrates today, every meal planned for today and your own '
          'documents due for renewal - from six months before they expire, '
          'or the nine or twelve chosen under Remind me. Tap a recipe to '
''',
         r'''    {'q': 'What is At home today?',
     'a': 'A card at the top of Today with the rest of your Alivente: who '
          'celebrates today (tap them for a greeting Claude writes, in '
          'English or Greek, to send by WhatsApp), every meal planned for '
          'today and your own '
          'documents due for renewal - from six months before they expire, '
          'or the nine or twelve chosen under Remind me. Tap a recipe to '
'''),
    ]),
    (os.path.join('wellness', 'views.py'), [
        (r'''# version moves. test_wellness_one.py checks the two agree.
# PT-2, 12 Nov 2026 - the card's lines and the recipe page.
SW_VERSION = 'wl24-1'


''',
         r'''# version moves. test_wellness_one.py checks the two agree.
# PT-2, 12 Nov 2026 - the card's lines and the recipe page.
# PT-4, 13 Nov 2026 - the greeting page.
SW_VERSION = 'wl25-1'


'''),
    ]),
    (os.path.join('wellness', 'urls.py'), [
        (r'''from . import views_cycle as CY
from . import views_photos as PH
from . import views_recipe as RC
from . import views_workouts as W
''',
         r'''from . import views_cycle as CY
from . import views_photos as PH
from . import views_greeting as GR
from . import views_recipe as RC
from . import views_workouts as W
'''),
        (r'''    # PT-2, 12 Nov 2026 - a recipe from today's meals, inside Wellness.
    path('recipe/<int:recipe_id>/', RC.recipe, name='recipe'),
    # WL-3, 30 Oct 2026 - Workouts.
    path('workouts/', W.home, name='workouts'),
''',
         r'''    # PT-2, 12 Nov 2026 - a recipe from today's meals, inside Wellness.
    path('recipe/<int:recipe_id>/', RC.recipe, name='recipe'),
    # PT-4, 13 Nov 2026 - a greeting for today's celebration, by WhatsApp.
    path('greeting/<int:event_id>/', GR.greeting, name='greeting'),
    # WL-3, 30 Oct 2026 - Workouts.
    path('workouts/', W.home, name='workouts'),
'''),
    ]),
    (os.path.join('test_wellness_twentyfive.py'), [
        (r'''doc = td[td.index('{% for d in home.docs %}'):td.index('{% endfor %}',
                                                       td.index('{% for d in home.docs %}'))]
ok('<a ' not in cel and '<a ' not in doc,
   '  celebrations and documents are plain lines, not links')
ok(not os.path.isfile(J(WT, 'home.html')),
   'THE PAGE: wellness/home.html is gone',
''',
         r'''doc = td[td.index('{% for d in home.docs %}'):td.index('{% endfor %}',
                                                       td.index('{% for d in home.docs %}'))]
# PT-4, 13 Nov 2026 - a celebration now opens its greeting (Demetri, 09:01);
# documents stay plain lines. test_wellness_twentysix holds the greeting.
ok('<a ' not in doc,
   '  documents are plain lines, not links')
ok(not os.path.isfile(J(WT, 'home.html')),
   'THE PAGE: wellness/home.html is gone',
'''),
    ]),
]


def read(p):
    with open(p, encoding='utf-8', newline='') as f:
        return f.read()


def write_file(p, t):
    with open(p, 'w', encoding='utf-8', newline='') as f:
        f.write(t)


def backup(p):
    b = p + SUFFIX
    if not os.path.exists(b) and not CHECK:
        write_file(b, read(p))


def refuse(msg):
    raise SystemExit('PT-4 REFUSED: %s' % msg)


def fit(text, lit):
    if '\n' not in lit:
        return lit
    crlf = text.count('\r\n')
    lf = text.count('\n') - crlf
    body = lit.replace('\r\n', '\n')
    return body.replace('\n', '\r\n') if crlf > lf else body


def once(text, lit, where):
    got = text.count(fit(text, lit))
    if got != 1:
        refuse('%s: the anchor appears %d time(s), expected exactly 1 - %r'
               % (where, got, lit[:72]))


def swap(text, old, new, where):
    once(text, old, where)
    return text.replace(fit(text, old), fit(text, new))


def main(argv):
    global CHECK
    CHECK = '--check' in argv
    root = os.path.dirname(os.path.abspath(__file__))
    out = {}

    pq = os.path.join(root, PS1)
    if "'test_wellness_twentysix.py'" in read(pq):
        print('PT-4 already applied.')
        return 0
    if "'test_gifts.py'" not in read(pq):
        refuse('Releases 74 and 75 are not applied - this round registers '
               'after them.')
    for rel in CREATES:
        if not os.path.isfile(os.path.join(root, *rel.split('/'))):
            refuse('%s is missing - it ships with this patcher; copy the '
                   'new wellness files and the suite in first.' % rel)

    for rel, pairs in SWAPS:
        pth = os.path.join(root, rel)
        t = read(pth)
        for i, (was, now) in enumerate(pairs):
            t = swap(t, was, now, '%s (swap %d of %d)'
                     % (rel, i + 1, len(pairs)))
        out[pth] = t

    if CHECK:
        print('PT-4 --check: %d file(s) would change, none written; %d '
              'ship with it.' % (len(out), len(CREATES)))
        for k in sorted(out):
            print('        %s' % os.path.relpath(k, root))
        return 0

    for k, val in sorted(out.items()):
        backup(k)
        write_file(k, val)
    for k in sorted(out):
        if read(k) != out[k]:
            refuse('%s was not written' % os.path.relpath(k, root))
    print('PT-4 applied - a celebration on Today opens its greeting.')
    print('      %d file(s) written, backed up to %s' % (len(out), SUFFIX))
    print('      %d file(s) ship with it, wired in rather than written'
          % len(CREATES))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
