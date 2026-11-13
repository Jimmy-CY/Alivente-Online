# -*- coding: utf-8 -*-
"""apply_recipe_list.py - round LL-1, 13 Nov 2026.

RELEASE 77 - RECIPE MANAGEMENT BUILDS THE LIST VIEW ONLY WHEN IT IS USED:
from a cookie when List is the view in use, else fetched (?part=list) the
first time List is chosen.

New files ship beside this patcher. Stands on Release 76.
Idempotent. Edits backed up to .bak_listlazy. No migration.
"""
import os
import sys

SUFFIX = '.bak_listlazy'
MARK = 'LL-1, 13 Nov 2026'
CHECK = False
PS1 = 'Push-PendingChanges.ps1'
CREATES = (
    'test_recipe_list.py',
)

SWAPS = [
    (os.path.join('Push-PendingChanges.ps1'), [
        (r'''    'test_gifts.py',
    # PT-4, 13 Nov 2026 - Release 76: a celebration on Today opens its greeting.
    'test_wellness_twentysix.py'
)
# NUMBER EVERY SUITE AS IT RUNS - Demetri, 1 Oct 2026: "for every check of
''',
         r'''    'test_gifts.py',
    # PT-4, 13 Nov 2026 - Release 76: a celebration on Today opens its greeting.
    'test_wellness_twentysix.py',
    # LL-1, 13 Nov 2026 - Release 77: the recipe list view built only when used.
    'test_recipe_list.py'
)
# NUMBER EVERY SUITE AS IT RUNS - Demetri, 1 Oct 2026: "for every check of
'''),
    ]),
    (os.path.join('alv_rounds.py'), [
        (r'''    # PT-4, 13 Nov 2026 - Release 76: the greeting from Wellness Today.
    '.bak_greetwell',
]

''',
         r'''    # PT-4, 13 Nov 2026 - Release 76: the greeting from Wellness Today.
    '.bak_greetwell',
    # LL-1, 13 Nov 2026 - Release 77: the recipe list view on demand.
    '.bak_listlazy',
]

'''),
    ]),
    (os.path.join('pages', 'templates', 'recipe_management.html'), [
        (r'''<!-- List View -->
<div class="recipe-list" id="recipeListView" style="display: none;">
    {% for recipe in recipes %}
    <div class="recipe-list-item">
''',
         r'''<!-- List View -->
<div class="recipe-list" id="recipeListView" style="display: none;">
    {# LL-1, 13 Nov 2026 - the list is built only when it is the view in  #}
    {# use: the same 48 recipes as the grid, 201 KB of the page's 742 on   #}
    {# Live (13 Nov) for a view most visits never show. A cookie says list #}
    {# and it is built here; otherwise the page fetches ?part=list when    #}
    {# List is first chosen, and the two markers below are what it keeps. #}
    <!--list:start-->{% if render_list %}
    {% for recipe in recipes %}
    <div class="recipe-list-item">
'''),
        (r'''        <p class="text-muted">Try adjusting your filters or add a new recipe!</p>
    </div>
    {% endfor %}
</div>

<!-- Book View -->
''',
         r'''        <p class="text-muted">Try adjusting your filters or add a new recipe!</p>
    </div>
    {% endfor %}
    {% endif %}<!--list:end-->
</div>

<!-- Book View -->
'''),
        (r'''    currentView = view;
    localStorage.setItem('recipeView', view);

    if (view === 'grid') {
''',
         r'''    currentView = view;
    localStorage.setItem('recipeView', view);
    // LL-1 - the server reads this to know whether to build the list.
    document.cookie = 'recipeView=' + view + '; path=/; max-age=31536000; SameSite=Lax';

    if (view === 'grid') {
'''),
        (r'''        listBtn.classList.add('active');
        if (countContainer) countContainer.style.display = 'flex';
    } else if (view === 'book') {
        bookView.style.display = 'block';
''',
         r'''        listBtn.classList.add('active');
        if (countContainer) countContainer.style.display = 'flex';
        loadListView();
    } else if (view === 'book') {
        bookView.style.display = 'block';
'''),
        (r'''// ==================== END BOOK VIEW ====================

</script>

''',
         r'''// ==================== END BOOK VIEW ====================

// LL-1, 13 Nov 2026 - the list, fetched the first time List is chosen
// when the page was not built with it. Same address, same filters,
// ?part=list. Its rows go in FIRST: anything Load more already added
// to the list belongs after the first page.
let listLoaded = {% if render_list %}true{% else %}false{% endif %};
let listLoading = null;
function loadListView() {
    if (listLoaded || listLoading) return listLoading;
    const q = new URLSearchParams(window.location.search);
    q.set('part', 'list');
    const listView = document.getElementById('recipeListView');
    listLoading = fetch(window.location.pathname + '?' + q.toString(),
                        {credentials: 'same-origin'})
        .then(r => r.ok ? r.text() : '')
        .then(html => {
            listView.insertAdjacentHTML('afterbegin', html);
            listLoaded = true;
            updateRecipeCount();
        })
        .catch(() => {})
        .finally(() => { listLoading = null; });
    return listLoading;
}

</script>

'''),
    ]),
    (os.path.join('pages', 'views', 'recipes', 'recipe_crud.py'), [
        (r'''    }

    return render(request, 'recipe_management.html', context)

''',
         r'''    }

    # LL-1, 13 Nov 2026 - the list view only when it is the view in use
    # (the cookie the page sets) or asked for (?part=list, when List is
    # first chosen). ?part=list answers with the list's rows alone.
    want = request.GET.get('part') == 'list'
    context['render_list'] = want or request.COOKIES.get('recipeView') == 'list'
    if want:
        # The page as the browser would get it, cut to the list's rows -
        # a browser render, not a string for mail or a PDF.
        html = render(request, 'recipe_management.html',
                      context).content.decode()
        a, b = html.find('<!--list:start-->'), html.find('<!--list:end-->')
        return HttpResponse(html[a + len('<!--list:start-->'):b]
                            if a >= 0 and b > a else '')
    return render(request, 'recipe_management.html', context)

'''),
    ]),
    (os.path.join('pages', 'views', 'celebration_gifts.py'), [
        (r'''def celebration_greeting(request, event_id):
    """{"text", "wa"} - a greeting for one of MY celebrations."""
    mine = my_member_ids(request.user)
    event = (CelebrationEvent.objects
''',
         r'''def celebration_greeting(request, event_id):
    """{"text", "wa"} - a greeting for one of MY celebrations."""
    return greeting_response(request, event_id)


def greeting_response(request, event_id):
    """The greeting, for Celebrations and for Wellness alike. PT-5, 13 Nov
    2026: Wellness asks through its own address (wellness/greeting/<id>/
    write/) - on a phone the main app's hour had run out, so asking here
    met the login page and the phone said "Could not reach Claude"."""
    mine = my_member_ids(request.user)
    event = (CelebrationEvent.objects
'''),
    ]),
    (os.path.join('wellness', 'views_greeting.py'), [
        (r'''from django.http import Http404
from django.shortcuts import render

from .views import wellness_view
''',
         r'''from django.http import Http404
from django.shortcuts import render
from django.views.decorators.http import require_POST

from .views import wellness_view
'''),
        (r'''        'what': what, 'number': CG.wa_number(event.contact.phone),
    })
''',
         r'''        'what': what, 'number': CG.wa_number(event.contact.phone),
    })


@wellness_view
@require_POST
def greeting_write(request, event_id):
    """PT-5, 13 Nov 2026 - the greeting, asked for through Wellness's own
    address. Demetri, 10:55, on his phone: "Could not reach Claude right
    now". The page asked /celebrations/..., a main-app address, and on a
    phone the main app's hour (wellness/session.py) had run out: the
    answer was the login page. Under /wellness/ the 30-day sign-in holds.
    The same checks and the same Claude call as Celebrations."""
    if not request.user.has_perm(PERM):
        raise PermissionDenied
    import importlib
    CG = importlib.import_module('pages.views.celebration_gifts')
    return CG.greeting_response(request, event_id)
'''),
    ]),
    (os.path.join('wellness', 'views_recipe.py'), [
        (r'''from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, render

from .views import _today, wellness_view
''',
         r'''from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_POST

from .views import _today, wellness_view
'''),
        (r'''        'today': _today(),
    })
''',
         r'''        'today': _today(),
    })


@wellness_view
@require_POST
def cooked(request, recipe_id):
    """PT-5, 13 Nov 2026 - Cooked it, saved through Wellness's own address
    for the reason views_greeting.greeting_write gives: on a phone the
    main app's hour runs out, and /recipe/<id>/cooked/ met the login page.
    Recipes' own view does the work - the same rules, the same rows."""
    if not request.user.has_perm(PERM):
        raise PermissionDenied
    from pages.views.recipes.recipe_extras import recipe_cooked
    return recipe_cooked(request, recipe_id)
'''),
    ]),
    (os.path.join('wellness', 'urls.py'), [
        (r'''    # PT-4, 13 Nov 2026 - a greeting for today's celebration, by WhatsApp.
    path('greeting/<int:event_id>/', GR.greeting, name='greeting'),
    # WL-3, 30 Oct 2026 - Workouts.
    path('workouts/', W.home, name='workouts'),
''',
         r'''    # PT-4, 13 Nov 2026 - a greeting for today's celebration, by WhatsApp.
    path('greeting/<int:event_id>/', GR.greeting, name='greeting'),
    # PT-5, 13 Nov 2026 - asked through Wellness, so a phone's 30 days hold.
    path('greeting/<int:event_id>/write/', GR.greeting_write,
         name='greeting_write'),
    path('recipe/<int:recipe_id>/cooked/', RC.cooked, name='recipe_cooked'),
    # WL-3, 30 Oct 2026 - Workouts.
    path('workouts/', W.home, name='workouts'),
'''),
    ]),
    (os.path.join('wellness', 'help.py'), [
        (r'''    'exercise_delete', 'exercise_hide',
    'photo_image', 'photo_delete',
}

''',
         r'''    'exercise_delete', 'exercise_hide',
    'photo_image', 'photo_delete',
    # PT-5, 13 Nov 2026 - the greeting and Cooked it, asked through Wellness.
    'greeting_write', 'recipe_cooked',
}

'''),
    ]),
    (os.path.join('wellness', 'templates', 'wellness', 'recipe.html'), [
        (r'''  <p class="w-small w-quiet" style="margin:0">Not cooked yet. Made it? Record how it turned out.</p>
  {% endif %}
  <form method="post" action="{% url 'recipe_cooked' recipe.recipe_id %}" class="w-rc-cooked">{% csrf_token %}<input type="hidden" name="from" value="wellness">
    <div class="w-rc-stars" role="radiogroup" aria-label="How it turned out">
      {% for n in "12345" %}<label class="w-rc-star"><input type="radio" name="rating" value="{{ n }}"><span aria-hidden="true">&#9733;</span><span class="w-sr">{{ n }} star{{ n|pluralize }}</span></label>{% endfor %}
''',
         r'''  <p class="w-small w-quiet" style="margin:0">Not cooked yet. Made it? Record how it turned out.</p>
  {% endif %}
  <form method="post" action="{% url 'wellness:recipe_cooked' recipe.recipe_id %}" class="w-rc-cooked">{% csrf_token %}<input type="hidden" name="from" value="wellness">
    <div class="w-rc-stars" role="radiogroup" aria-label="How it turned out">
      {% for n in "12345" %}<label class="w-rc-star"><input type="radio" name="rating" value="{{ n }}"><span aria-hidden="true">&#9733;</span><span class="w-sr">{{ n }} star{{ n|pluralize }}</span></label>{% endfor %}
'''),
    ]),
    (os.path.join('wellness', 'templates', 'wellness', 'greeting.html'), [
        (r'''</header>

<section class="w-card" data-greeting data-url="{% url 'celebration_greeting' event.id %}" data-number="{{ number }}">
  {% csrf_token %}
  <span class="w-label" id="gr-lang-label">Language</span>
''',
         r'''</header>

<section class="w-card" data-greeting data-url="{% url 'wellness:greeting_write' event.id %}" data-number="{{ number }}">
  {% csrf_token %}
  <span class="w-label" id="gr-lang-label">Language</span>
'''),
        (r'''    return on ? on.value : 'English';
  }
  function write() {
    status.textContent = 'Claude is writing...';
    var body = new FormData();
    body.append('language', lang());
    body.append('csrfmiddlewaretoken', box.querySelector('[name=csrfmiddlewaretoken]').value);
    fetch(box.getAttribute('data-url'), {method: 'POST', body: body, credentials: 'same-origin'})
      .then(function (r) { return r.json(); })
      .then(function (d) {
        if (d.text) { text.value = d.text; status.textContent = ''; }
        else { status.textContent = d.error || 'Could not write one just now - write your own.'; }
        if (d.number) number = d.number;
        link();
      })
      .catch(function () { status.textContent = 'Could not reach Claude just now - write your own.'; });
  }
  box.querySelectorAll('input[name="gr_lang"]').forEach(function (r) { r.addEventListener('change', write); });
''',
         r'''    return on ? on.value : 'English';
  }
  // PT-5, 13 Nov 2026 - asked through Wellness's own address; gives up
  // after 40 seconds; says what went wrong; and leaves the box ready for
  // a message of your own.
  function giveUp(why) {
    status.textContent = why;
    text.placeholder = 'Write your message here';
    link();
  }
  function write() {
    status.textContent = 'Claude is writing...';
    text.placeholder = 'Claude is writing...';
    var body = new FormData();
    body.append('language', lang());
    body.append('csrfmiddlewaretoken', box.querySelector('[name=csrfmiddlewaretoken]').value);
    var ctl = window.AbortController ? new AbortController() : null;
    var timer = ctl ? setTimeout(function () { ctl.abort(); }, 40000) : null;
    fetch(box.getAttribute('data-url'), {method: 'POST', body: body, credentials: 'same-origin',
                                         headers: {'X-Requested-With': 'fetch'},
                                         signal: ctl ? ctl.signal : undefined})
      .then(function (r) {
        var json = (r.headers.get('Content-Type') || '').indexOf('json') !== -1;
        if (!json) {
          throw new Error(r.redirected || r.status === 200 ? 'You are signed out - open Wellness again.'
                          : 'The server said ' + r.status + '.');
        }
        return r.json();
      })
      .then(function (d) {
        if (timer) clearTimeout(timer);
        if (d.number) number = d.number;
        if (d.text) { text.value = d.text; status.textContent = ''; link(); }
        else { giveUp(d.error || 'Claude could not write one just now - write your own.'); }
      })
      .catch(function (e) {
        if (timer) clearTimeout(timer);
        giveUp(e && e.name === 'AbortError' ? 'Claude took too long - try Write another, or write your own.'
               : (e && e.message && e.message.indexOf('signed out') !== -1 ? e.message
                  : 'Could not reach Claude just now (' + ((e && e.message) || 'no answer') + ') - write your own.'));
      });
  }
  box.querySelectorAll('input[name="gr_lang"]').forEach(function (r) { r.addEventListener('change', write); });
'''),
    ]),
    (os.path.join('test_wellness_twentysix.py'), [
        (r'''   'TODAY: a celebration line opens its greeting')
gt = read(J(WT, 'greeting.html'))
ok("{% url 'celebration_greeting' event.id %}" in gt and
   'value="Greek"' in gt and 'https://wa.me/' in gt and
   "encodeURIComponent(text.value)" in gt,
   'GREETING: the one Celebrations endpoint; English or Greek; WhatsApp '
   'with the words as they stand')
gv = read(J(APP, 'views_greeting.py'))
''',
         r'''   'TODAY: a celebration line opens its greeting')
gt = read(J(WT, 'greeting.html'))
# PT-5, 13 Nov 2026 - asked through Wellness's own address now (a phone's
# main-app hour sent the old one to the login page); same checks behind it.
ok("{% url 'wellness:greeting_write' event.id %}" in gt and
   'value="Greek"' in gt and 'https://wa.me/' in gt and
   "encodeURIComponent(text.value)" in gt,
   'GREETING: asked through Wellness; English or Greek; WhatsApp '
   'with the words as they stand')
gv = read(J(APP, 'views_greeting.py'))
'''),
        (r'''               'Anniversary, 27 years' in t and
               'data-number="35799123456"' in t and
               '/celebrations/event/%d/greeting/' % e.pk in t,
               'GREETING: her name, 27 years, her WhatsApp number')
            ok(cb.get('/wellness/greeting/%d/' % e.pk).status_code == 404,
''',
         r'''               'Anniversary, 27 years' in t and
               'data-number="35799123456"' in t and
               '/wellness/greeting/%d/write/' % e.pk in t,
               'GREETING: her name, 27 years, her WhatsApp number')
            ok(cb.get('/wellness/greeting/%d/' % e.pk).status_code == 404,
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
    raise SystemExit('LL-1 REFUSED: %s' % msg)


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
    if "'test_recipe_list.py'" in read(pq):
        print('LL-1 already applied.')
        return 0
    if "'test_wellness_twentysix.py'" not in read(pq):
        refuse('Release 76 is not applied - this round registers after it.')
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
        print('LL-1 --check: %d file(s) would change, none written; %d '
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
    print('LL-1 applied - the recipe list view is built only when used.')
    print('      %d file(s) written, backed up to %s' % (len(out), SUFFIX))
    print('      %d file(s) ship with it, wired in rather than written'
          % len(CREATES))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
