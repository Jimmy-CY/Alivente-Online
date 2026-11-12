# -*- coding: utf-8 -*-
"""apply_meal_share.py - round MS-1, 12 Nov 2026.

RELEASE 69 - ONE MEAL PLAN PER PERSON, SHARED WITH WHOM THEY CHOOSE.

    Demetri, 14:38-14:44: one meal plan per person, shown as the
    person's name; they choose who to share it with; those people can
    see and change it. The meals already planned go onto his plan,
    shared with Angy - by manage.py meal_calendar_backfill, dry by
    default, after the deploy.
    15:20: Take a photo / Choose from gallery on Add a photo.

New files ship beside this patcher. Stands on Release 68. Idempotent.
Edits backed up to .bak_mealshare. MIGRATION 0116_meal_calendars.
"""
import os
import sys

SUFFIX = '.bak_mealshare'
MARK = 'MS-1, 12 Nov 2026'
CHECK = False
PS1 = 'Push-PendingChanges.ps1'
CREATES = (
    'pages/meal_calendar.py',
    'pages/migrations/0116_meal_calendars.py',
    'pages/management/commands/meal_calendar_backfill.py',
    'test_meal_share.py',
)

SWAPS = [
    (os.path.join('Push-PendingChanges.ps1'), [
        (r'''    @{ File = 'wellness/phases.py'; Text = 'DISCLAIMER = ('; What = 'CY-2/CY-4: the cycle phases are on disk, honestly worded - without them the cycle tracker cannot open' },
    @{ File = 'pages/css_files.py'; Text = 'def stylesheet(request, digest):'; What = 'SP-1: base.html links its stylesheets from here - without it every page loses its styling' },
    @{ File = 'wellness/crypto.py'; Text = 'def seal_bytes('; What = 'WL-19: the lock for progress photos is on disk - without it no photo can be saved or shown' },
    @{ File = 'wellness/body.py'; Text = 'def goal_check('; What = 'WL-18: Body puts the goal date to work - without it the Body page cannot open' },
''',
         r'''    @{ File = 'wellness/phases.py'; Text = 'DISCLAIMER = ('; What = 'CY-2/CY-4: the cycle phases are on disk, honestly worded - without them the cycle tracker cannot open' },
    @{ File = 'pages/css_files.py'; Text = 'def stylesheet(request, digest):'; What = 'SP-1: base.html links its stylesheets from here - without it every page loses its styling' },
    @{ File = 'pages/meal_calendar.py'; Text = 'class MealCalendarMiddleware:'; What = 'MS-1: which meal plan a request is about - without it the planner cannot open' },
    @{ File = 'wellness/crypto.py'; Text = 'def seal_bytes('; What = 'WL-19: the lock for progress photos is on disk - without it no photo can be saved or shown' },
    @{ File = 'wellness/body.py'; Text = 'def goal_check('; What = 'WL-18: Body puts the goal date to work - without it the Body page cannot open' },
'''),
        (r'''    'test_wellness_twentytwo.py',
    # WL-19, 12 Nov 2026 - Wellness: progress photos and download your data.
    'test_wellness_twentythree.py'
)
# NUMBER EVERY SUITE AS IT RUNS - Demetri, 1 Oct 2026: "for every check of
''',
         r'''    'test_wellness_twentytwo.py',
    # WL-19, 12 Nov 2026 - Wellness: progress photos and download your data.
    'test_wellness_twentythree.py',
    # MS-1, 12 Nov 2026 - one meal plan per person, shared with whom they choose.
    'test_meal_share.py'
)
# NUMBER EVERY SUITE AS IT RUNS - Demetri, 1 Oct 2026: "for every check of
'''),
    ]),
    (os.path.join('alv_rounds.py'), [
        (r'''    # WL-19, 12 Nov 2026 - Wellness: progress photos and download your data.
    '.bak_wellness23',
]

''',
         r'''    # WL-19, 12 Nov 2026 - Wellness: progress photos and download your data.
    '.bak_wellness23',
    # MS-1, 12 Nov 2026 - one meal plan per person, shared with whom they choose.
    '.bak_mealshare',
]

'''),
    ]),
    (os.path.join('mysite', 'settings.py'), [
        (r'''    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    'pages.workspace.WorkspaceMiddleware',    
    # WL-1, 30 Oct 2026 - 30 days for Wellness on a phone, the main app's
''',
         r'''    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    # MS-1, 12 Nov 2026 - which meal plan a meal_plans/ request is about.
    "pages.meal_calendar.MealCalendarMiddleware",
    'pages.workspace.WorkspaceMiddleware',    
    # WL-1, 30 Oct 2026 - 30 days for Wellness on a phone, the main app's
'''),
    ]),
    (os.path.join('pages', 'help_content', 'administration.html'), [
        (r'''
      <div style="background:#f8f9fa; border-radius:8px; padding:12px; border-left:4px solid #0e7c8b; font-size:13px; color:#6c757d;">
        <strong style="color:#2c3e50;"><i class="fas fa-users" style="color:#0e7c8b;"></i> Everyone sees the same calendar.</strong> Meals are not private to the person who planned them &mdash; this is deliberate, and it matches the recipes they are built from, which are shared across the whole installation. If you can open Recipes, you can see the planner.
      </div>

''',
         r'''
      <div style="background:#f8f9fa; border-radius:8px; padding:12px; border-left:4px solid #0e7c8b; font-size:13px; color:#6c757d;">
        <strong style="color:#2c3e50;"><i class="fas fa-users" style="color:#0e7c8b;"></i> Your own plan.</strong> Everyone has one meal plan. Tap <strong>Share</strong> beside its name to choose who may see it and change it &mdash; they can add meals and make the shopping list. Plans shared with you show beside yours, above the calendar, so you can switch between them.
      </div>

'''),
    ]),
    (os.path.join('pages', 'models.py'), [
        (r'''        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='meal_entries')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
''',
         r'''        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='meal_entries')
    # MS-1, 12 Nov 2026 - whose meal plan this meal is on. Empty only for
    # meals planned before sharing existed, until the backfill places
    # them; see pages/meal_calendar.py.
    calendar = models.ForeignKey(
        'pages.MealCalendar', on_delete=models.CASCADE, null=True,
        blank=True, related_name='entries')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
'''),
        (r'''        """A note buys nothing, and leftovers were bought once already."""
        return bool(self.recipe) and self.leftover_of_id is None


''',
         r'''        """A note buys nothing, and leftovers were bought once already."""
        return bool(self.recipe) and self.leftover_of_id is None


class MealCalendar(models.Model):
    """MS-1, 12 Nov 2026 - one person's meal plan, and who it is shared
    with. Shown as "Demetri's meal plan". Everyone it is shared with can
    see and change it; only the owner changes who that is."""
    owner = models.OneToOneField(User, on_delete=models.CASCADE,
                                 related_name='meal_calendar')
    shared_with = models.ManyToManyField(
        User, blank=True, related_name='shared_meal_calendars')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'meal_calendars'

    def __str__(self):
        return self.label

    @property
    def label(self):
        name = (self.owner.first_name or self.owner.username).strip()
        return "%s's meal plan" % name


'''),
    ]),
    (os.path.join('pages', 'templates', 'meal_planner.html'), [
        (r'''        .recipe-item { flex-wrap: wrap; row-gap: 6px; }
    }
</style>

<div class="calendar-container">

    <h2 class="page-title-h2">MEAL PLANNER</h2>

    {# ONE BAR, and Back is LAST and carries no colour - test_bar_top. #}
''',
         r'''        .recipe-item { flex-wrap: wrap; row-gap: 6px; }
    }
    /* MS-1, 12 Nov 2026 - whose meal plan. */
    .mp-whose { display: flex; flex-wrap: wrap; align-items: center; gap: 8px 16px; margin: 0 0 12px; }
    .mp-whose-label { margin: 0; font-size: 13px; color: var(--alv-ink-soft); }
    .mp-whose-tab { display: inline-flex; align-items: center; min-height: 44px; padding: 0 14px; border: 1px solid var(--alv-line); border-radius: 22px; color: var(--alv-ink); text-decoration: none; }
    .mp-whose-tab.is-on { border: 2px solid var(--alv-accent); color: var(--alv-accent-ink); font-weight: 600; }
    .mp-whose-name { font-weight: 600; }
    .mp-whose-share { display: inline-flex; align-items: center; gap: 6px; min-height: 44px; font-weight: 600; background: none; border: 0; color: var(--alv-accent-ink); padding: 0 4px; }
    .mp-share-list { list-style: none; margin: 0; padding: 0; }
    .mp-share-actions { display: flex; justify-content: flex-end; margin-top: 16px; }
    .mp-share-list label { display: flex; align-items: center; gap: 12px; min-height: 44px; margin: 0; cursor: pointer; }
    .mp-whose-note { font-size: 13px; color: var(--alv-ink-soft); }
</style>

<div class="calendar-container">

    <h2 class="page-title-h2">MEAL PLANNER</h2>

    {# MS-1, 12 Nov 2026 - WHOSE PLAN. One per person. Links, not a form: #}
    {# the plans shared with you appear beside yours; Share opens a      #}
    {# dialog on your own.                                               #}
    {% if request.meal_calendar %}
    <div class="mp-whose" data-meal-calendar>
        {% if request.meal_calendars|length > 1 %}
        <span class="mp-whose-label">Meal plan:</span>
        {% for c in request.meal_calendars %}<a class="mp-whose-tab{% if c.pk == request.meal_calendar.pk %} is-on{% endif %}" href="?calendar={{ c.pk }}&amp;date={{ anchor|date:'Y-m-d' }}&amp;view={{ view_mode }}" data-meal-calendar-tab{% if c.pk == request.meal_calendar.pk %} aria-current="true"{% endif %}>{% if c.owner_id == request.user.pk %}My meal plan{% else %}{{ c.label }}{% endif %}</a>{% endfor %}
        {% else %}
        <span class="mp-whose-name">{{ request.meal_calendar.label }}</span>
        {% endif %}
        {% if request.meal_calendar.owner_id == request.user.pk %}
        <button type="button" class="mp-whose-share" data-toggle="modal" data-target="#mealShareModal"><i class="fas fa-user-friends"></i> {% if share_count %}Shared with {{ share_count }}{% else %}Share{% endif %}</button>
        {% else %}
        <span class="mp-whose-note">Shared with you - you can change it</span>
        {% endif %}
    </div>
    {% endif %}

    {# ONE BAR, and Back is LAST and carries no colour - test_bar_top. #}
'''),
        (r'''{# TWO SIBLING FORMS, because they post to different endpoints and  #}
{# a form cannot nest. Both endpoints are untouched by this round.  #}
<div class="modal fade" id="menusModal" tabindex="-1" role="dialog"
     aria-labelledby="menusLabel" aria-hidden="true">
''',
         r'''{# TWO SIBLING FORMS, because they post to different endpoints and  #}
{# a form cannot nest. Both endpoints are untouched by this round.  #}
{# MS-1, 12 Nov 2026 - who can see and change my meal plan. #}
{% if share_people is not None %}
<div class="modal fade" id="mealShareModal" tabindex="-1" role="dialog"
     aria-labelledby="mealShareLabel" aria-hidden="true">
    <div class="modal-dialog" role="document">
        <div class="modal-content">
            <form method="POST" action="{% url 'meal_plan_share' %}">
                {% csrf_token %}
                <div class="modal-header alv-modal-head">
                    <h5 class="modal-title" id="mealShareLabel">
                        <i class="fas fa-user-friends"></i> Share {{ request.meal_calendar.label }}
                    </h5>
                    <button type="button" class="close" data-dismiss="modal" aria-label="Close">
                        <span aria-hidden="true">&times;</span>
                    </button>
                </div>
                <div class="modal-body">
                    <p class="text-muted" style="font-size:13px;">Everyone you tick can see your meal plan and change it - add and remove meals, copy days, use saved menus and make the shopping list. Untick someone and it leaves their planner. Nobody else sees it.</p>
                    {% if share_people %}
                    <ul class="mp-share-list" data-share-people>
                        {% for p in share_people %}<li><label><input type="checkbox" name="share" value="{{ p.pk }}"{% if p.on %} checked{% endif %}> <span>{{ p.name }}</span></label></li>{% endfor %}
                    </ul>
                    {% else %}
                    <p class="text-muted" style="font-size:13px;margin:0;">Nobody else can open Recipes yet, so there is nobody to share with.</p>
                    {% endif %}
                    <div class="mp-share-actions">
                        <button type="submit" class="btn action-primary">Update sharing</button>
                    </div>
                </div>
            </form>
        </div>
    </div>
</div>
{% endif %}
<div class="modal fade" id="menusModal" tabindex="-1" role="dialog"
     aria-labelledby="menusLabel" aria-hidden="true">
'''),
    ]),
    (os.path.join('pages', 'urls.py'), [
        (r'''    # PP-1, 20 Oct 2026 - the plan, laid out for paper. Beside the
    # shopping list because it takes the same two parameters.
    path('meal_plans/print/', views.meal_plan_print,
         name='meal_plan_print'),
''',
         r'''    # PP-1, 20 Oct 2026 - the plan, laid out for paper. Beside the
    # shopping list because it takes the same two parameters.
    # MS-1, 12 Nov 2026 - who can see and change my meal plan.
    path('meal_plans/share/', views.meal_plan_share, name='meal_plan_share'),
    path('meal_plans/print/', views.meal_plan_print,
         name='meal_plan_print'),
'''),
    ]),
    (os.path.join('pages', 'views', 'recipes', 'meal_planning.py'), [
        (r'''logger = logging.getLogger(__name__)

from pages.models import (
    CustomProtein,
''',
         r'''logger = logging.getLogger(__name__)

# MS-1, 12 Nov 2026 - every meal read or written here is on the meal plan
# being looked at; see pages/meal_calendar.py.
from pages import meal_calendar as MC
from pages.models import (
    CustomProtein,
'''),
        (r'''@login_required
@permission_required('auth.can_access_recipes', raise_exception=True)
def meal_planner(request):
    """The calendar, at one of three zoom levels.
''',
         r'''@login_required
@permission_required('auth.can_access_recipes', raise_exception=True)
def meal_plan_share(request):
    """MS-1, 12 Nov 2026 - who can see and change MY meal plan.

    The planner's Share dialog posts here. Only ever the poster's own
    plan: a shared plan's people are its owner's choice. The choice is
    everyone who can open Recipes - nobody else could open a planner.
    """
    cal = MC.own(request.user)
    if request.method == 'POST':
        people = share_people(request.user)
        want = set(request.POST.getlist('share'))
        chosen = [u for u in people if str(u.pk) in want]
        cal.shared_with.set(chosen)
        messages.success(request, 'Saved - %s.' % (
            'shared with %d' % len(chosen) if chosen
            else 'not shared with anyone'))
    return redirect('%s?calendar=%d' % (reverse('meal_planner'), cal.pk))


def share_people(user):
    """Everyone, other than `user`, who can open Recipes."""
    from django.contrib.auth.models import User
    from django.db.models import Q
    # ONE query, however many people: has_perm per person would ask the
    # database twice for each of them.
    code = 'can_access_recipes'
    return list(User.objects.filter(is_active=True).filter(
        Q(is_superuser=True) |
        Q(user_permissions__codename=code,
          user_permissions__content_type__app_label='auth') |
        Q(groups__permissions__codename=code,
          groups__permissions__content_type__app_label='auth'))
        .exclude(pk=user.pk).distinct().order_by('first_name', 'username'))


@login_required
@permission_required('auth.can_access_recipes', raise_exception=True)
def meal_planner(request):
    """The calendar, at one of three zoom levels.
'''),
        (r'''    # that day's recipes, seven times over.
    entries = list(
        MealEntry.objects.filter(date__gte=week_start, date__lte=week_end)
        # MO-1, 19 Oct 2026 - leftover_of joins the ONE query. The
        # leftover row prints the date of the meal it came from, and
''',
         r'''    # that day's recipes, seven times over.
    entries = list(
        MC.entries().filter(date__gte=week_start, date__lte=week_end)
        # MO-1, 19 Oct 2026 - leftover_of joins the ONE query. The
        # leftover row prints the date of the meal it came from, and
'''),
        (r'''    # queries to paint one screen. [E29]
    month_by_date = {}
    for e in (MealEntry.objects
              .filter(date__gte=first_of_month, date__lte=month_end)
              .select_related('recipe', 'leftover_of')
''',
         r'''    # queries to paint one screen. [E29]
    month_by_date = {}
    for e in (MC.entries()
              .filter(date__gte=first_of_month, date__lte=month_end)
              .select_related('recipe', 'leftover_of')
'''),
        (r'''        ).order_by('name'),
    }
    return render(request, 'meal_planner.html', context)

''',
         r'''        ).order_by('name'),
    }
    # MS-1, 12 Nov 2026 - the Share dialog, on your own plan only.
    cal = getattr(request, 'meal_calendar', None)
    if cal is not None and cal.owner_id == request.user.pk:
        chosen = set(cal.shared_with.values_list('pk', flat=True))
        context['share_people'] = [
            {'pk': u.pk, 'name': u.get_full_name() or u.username,
             'on': u.pk in chosen} for u in share_people(request.user)]
        context['share_count'] = len(chosen)
    return render(request, 'meal_planner.html', context)

'''),
        (r'''def day_payload(when):
    """Every meal on `when`, in the order the planner draws them."""
    rows = (MealEntry.objects
            .filter(date=when)
            .select_related('recipe')
''',
         r'''def day_payload(when):
    """Every meal on `when`, in the order the planner draws them."""
    rows = (MC.entries()
            .filter(date=when)
            .select_related('recipe')
'''),
        (r'''
    by_day = defaultdict(list)
    for e in (MealEntry.objects
              .filter(date__gte=grid_start, date__lte=grid_end)
              .select_related('recipe', 'leftover_of')
''',
         r'''
    by_day = defaultdict(list)
    for e in (MC.entries()
              .filter(date__gte=grid_start, date__lte=grid_end)
              .select_related('recipe', 'leftover_of')
'''),
        (r'''        servings = recipe.servings or household_size(request.user)

    last = MealEntry.objects.filter(date=when).aggregate(
        Max('sort_order'))['sort_order__max']
    # KEPT, WHICH IT WAS NOT - AP-1, 20 Oct 2026. The row was created
    # and dropped on the floor, so the JSON branch could describe the
    # DAY and never the thing it had just added. An Undo needs
    # something to point at.
    entry = MealEntry.objects.create(
        date=when, recipe=recipe, servings=servings,
        sort_order=(last or 0) + 1, created_by=request.user)
''',
         r'''        servings = recipe.servings or household_size(request.user)

    last = MC.entries().filter(date=when).aggregate(
        Max('sort_order'))['sort_order__max']
    # KEPT, WHICH IT WAS NOT - AP-1, 20 Oct 2026. The row was created
    # and dropped on the floor, so the JSON branch could describe the
    # DAY and never the thing it had just added. An Undo needs
    # something to point at.
    entry = MealEntry.objects.create(calendar=MC.current(), 
        date=when, recipe=recipe, servings=servings,
        sort_order=(last or 0) + 1, created_by=request.user)
'''),
        (r'''    """
    try:
        entry = MealEntry.objects.select_related(
            'recipe', 'leftover_of').get(
                meal_entry_id=request.POST.get('meal_entry_id'))
''',
         r'''    """
    try:
        entry = MC.entries().select_related(
            'recipe', 'leftover_of').get(
                meal_entry_id=request.POST.get('meal_entry_id'))
'''),
        (r'''        return JsonResponse({'ok': False, 'why': 'twice'}, status=400)

    on_day = list(MealEntry.objects.filter(date=day)
                  .order_by('sort_order', 'meal_entry_id')
                  .values_list('meal_entry_id', flat=True))
''',
         r'''        return JsonResponse({'ok': False, 'why': 'twice'}, status=400)

    on_day = list(MC.entries().filter(date=day)
                  .order_by('sort_order', 'meal_entry_id')
                  .values_list('meal_entry_id', flat=True))
'''),
        (r'''    with transaction.atomic():
        for n, eid in enumerate(ids, start=1):
            MealEntry.objects.filter(meal_entry_id=eid).update(sort_order=n)

    return JsonResponse({'ok': True, 'order': ids})
''',
         r'''    with transaction.atomic():
        for n, eid in enumerate(ids, start=1):
            MC.entries().filter(meal_entry_id=eid).update(sort_order=n)

    return JsonResponse({'ok': True, 'order': ids})
'''),
        (r'''    """Take a meal off its date."""
    try:
        entry = MealEntry.objects.select_related('recipe').get(
            meal_entry_id=request.POST.get('meal_entry_id'))
    except (MealEntry.DoesNotExist, ValueError, TypeError):
''',
         r'''    """Take a meal off its date."""
    try:
        entry = MC.entries().select_related('recipe').get(
            meal_entry_id=request.POST.get('meal_entry_id'))
    except (MealEntry.DoesNotExist, ValueError, TypeError):
'''),
        (r'''    """
    try:
        entry = MealEntry.objects.select_related('recipe').get(
            meal_entry_id=request.POST.get('meal_entry_id'))
    except (MealEntry.DoesNotExist, ValueError, TypeError):
''',
         r'''    """
    try:
        entry = MC.entries().select_related('recipe').get(
            meal_entry_id=request.POST.get('meal_entry_id'))
    except (MealEntry.DoesNotExist, ValueError, TypeError):
'''),
        (r'''    week are read the same way.
    """
    return (MealEntry.objects
            .filter(date__gte=start, date__lte=end)
            .select_related('recipe')
''',
         r'''    week are read the same way.
    """
    return (MC.entries()
            .filter(date__gte=start, date__lte=end)
            .select_related('recipe')
'''),
        (r'''def week_entries(week_start):
    """Every meal on the seven days from week_start."""
    return (MealEntry.objects
            .filter(date__gte=week_start,
                    date__lte=week_start + timedelta(days=6))
''',
         r'''def week_entries(week_start):
    """Every meal on the seven days from week_start."""
    return (MC.entries()
            .filter(date__gte=week_start,
                    date__lte=week_start + timedelta(days=6))
'''),
        (r'''        when = dst_start + timedelta(days=offset)
        if when not in tails:
            last = MealEntry.objects.filter(date=when).aggregate(
                Max('sort_order'))['sort_order__max']
            tails[when] = last or 0
        tails[when] += 1
        return MealEntry.objects.create(
            date=when, recipe=entry.recipe, note=entry.note,
            servings=entry.servings, sort_order=tails[when],
''',
         r'''        when = dst_start + timedelta(days=offset)
        if when not in tails:
            last = MC.entries().filter(date=when).aggregate(
                Max('sort_order'))['sort_order__max']
            tails[when] = last or 0
        tails[when] += 1
        return MealEntry.objects.create(calendar=MC.current(), 
            date=when, recipe=entry.recipe, note=entry.note,
            servings=entry.servings, sort_order=tails[when],
'''),
        (r'''                                 'error': 'A copy covers at most '
                                          '13 weeks.'}, status=400)
        span = list(MealEntry.objects
                    .filter(date__gte=first, date__lte=last)
                    .only('date'))
''',
         r'''                                 'error': 'A copy covers at most '
                                          '13 weeks.'}, status=400)
        span = list(MC.entries()
                    .filter(date__gte=first, date__lte=last)
                    .only('date'))
'''),
        (r'''        return redirect(back)

    rows = list(MealEntry.objects
                .filter(date__gte=start, date__lte=end)
                .select_related('recipe', 'leftover_of')
''',
         r'''        return redirect(back)

    rows = list(MC.entries()
                .filter(date__gte=start, date__lte=end)
                .select_related('recipe', 'leftover_of')
'''),
        (r'''            when = onto + timedelta(days=it.day_index)
            if when not in tails:
                last = MealEntry.objects.filter(date=when).aggregate(
                    Max('sort_order'))['sort_order__max']
                tails[when] = last or 0
            tails[when] += 1
            MealEntry.objects.create(
                date=when, recipe=it.recipe, note=it.note,
                servings=it.servings, sort_order=tails[when],
''',
         r'''            when = onto + timedelta(days=it.day_index)
            if when not in tails:
                last = MC.entries().filter(date=when).aggregate(
                    Max('sort_order'))['sort_order__max']
                tails[when] = last or 0
            tails[when] += 1
            MealEntry.objects.create(calendar=MC.current(), 
                date=when, recipe=it.recipe, note=it.note,
                servings=it.servings, sort_order=tails[when],
'''),
        (r'''        return redirect(back)

    last = MealEntry.objects.filter(date=when).aggregate(
        Max('sort_order'))['sort_order__max']
    MealEntry.objects.create(date=when, recipe=None, note=note,
                             servings=0, sort_order=(last or 0) + 1,
                             created_by=request.user)
''',
         r'''        return redirect(back)

    last = MC.entries().filter(date=when).aggregate(
        Max('sort_order'))['sort_order__max']
    MealEntry.objects.create(calendar=MC.current(), date=when, recipe=None, note=note,
                             servings=0, sort_order=(last or 0) + 1,
                             created_by=request.user)
'''),
        (r'''    when = week_of(request.POST.get('date'), None)
    try:
        src = MealEntry.objects.select_related('recipe', 'leftover_of').get(
            meal_entry_id=request.POST.get('meal_entry_id'))
    except (MealEntry.DoesNotExist, ValueError, TypeError):
''',
         r'''    when = week_of(request.POST.get('date'), None)
    try:
        src = MC.entries().select_related('recipe', 'leftover_of').get(
            meal_entry_id=request.POST.get('meal_entry_id'))
    except (MealEntry.DoesNotExist, ValueError, TypeError):
'''),
        (r'''        return redirect(back)

    last = MealEntry.objects.filter(date=when).aggregate(
        Max('sort_order'))['sort_order__max']
    MealEntry.objects.create(
        date=when, recipe=root.recipe, note=root.note,
        servings=root.servings, sort_order=(last or 0) + 1,
''',
         r'''        return redirect(back)

    last = MC.entries().filter(date=when).aggregate(
        Max('sort_order'))['sort_order__max']
    MealEntry.objects.create(calendar=MC.current(), 
        date=when, recipe=root.recipe, note=root.note,
        servings=root.servings, sort_order=(last or 0) + 1,
'''),
        (r'''    try:
        entries = (
            MealEntry.objects.filter(date__gte=start, date__lte=end)
            .select_related('recipe')
            .prefetch_related(
''',
         r'''    try:
        entries = (
            MC.entries().filter(date__gte=start, date__lte=end)
            .select_related('recipe')
            .prefetch_related(
'''),
        (r'''        # not days. A seven-day range used to be emailed as
        # "7 recipes" whatever was on it.
        total_recipes = MealEntry.objects.filter(
            date__gte=start, date__lte=end,
            recipe__isnull=False, leftover_of__isnull=True).count()
''',
         r'''        # not days. A seven-day range used to be emailed as
        # "7 recipes" whatever was on it.
        total_recipes = MC.entries().filter(
            date__gte=start, date__lte=end,
            recipe__isnull=False, leftover_of__isnull=True).count()
'''),
    ]),
    (os.path.join('test_wellness_twentythree.py'), [
        (r'''base = read(J(WT, 'base.html'))
vv = re.findall(r'\?v=([\w-]+)', base)
ok(vv and set(vv) == {'wl21-1'} and
   "SW_VERSION = 'wl21-1'" in read(J(APP, 'views.py')),
   'the app files carry a new version', vv)

''',
         r'''base = read(J(WT, 'base.html'))
vv = re.findall(r'\?v=([\w-]+)', base)
# Loosened by MS-1: a later round bumps the version again.
ok(vv and len(set(vv)) == 1 and vv[0] not in ('wl20-1',) and
   ("SW_VERSION = '%s'" % vv[0]) in read(J(APP, 'views.py')),
   'the app files carry a new version', vv)

'''),
    ]),
    (os.path.join('test_planner.py'), [
        (r'''    c['  and normalises the week to a Monday'] = (
        'week_start -= timedelta(days=week_start.weekday())' in vcode)
    c['  in ONE query for the week'] = (
        'MealEntry.objects.filter(date__gte=week_start, date__lte=week_end)'
        in vcode)
    c['add, remove and servings are three views'] = all(
        ('def %s(request):' % n) in vcode
''',
         r'''    c['  and normalises the week to a Monday'] = (
        'week_start -= timedelta(days=week_start.weekday())' in vcode)
    # MS-1, 12 Nov 2026 - the week is read through the meal plan being
    # looked at (MC.entries()), still in one query.
    c['  in ONE query for the week'] = any(
        ('%s.filter(date__gte=week_start, date__lte=week_end)' % q) in vcode
        for q in ('MealEntry.objects', 'MC.entries()'))
    c['add, remove and servings are three views'] = all(
        ('def %s(request):' % n) in vcode
'''),
        (r'''    # picker's filter strip is built from. One query, not one per
    # course and not one per card.
    ok(q_big <= 14, '  and that number is under 14', q_big)

    head('8f. the shopping list shops a range')
''',
         r'''    # picker's filter strip is built from. One query, not one per
    # course and not one per card.
    # MS-1, 12 Nov 2026 - eighteen. Four more, all fixed: whose plan
    # this is, the plans shared with you, who yours is shared with, and
    # the people the Share dialog offers (one query, however many).
    # None of them grows with the meals - the check above proves that.
    ok(q_big <= 18, '  and that number is under 18', q_big)

    head('8f. the shopping list shops a range')
'''),
    ]),
    (os.path.join('test_print_plan.py'), [
        (r'''        "'in_range'" in code)
    c['  one query for the whole grid, not one per day'] = (
        'for e in (MealEntry.objects' in code
        and code.count('MealEntry.objects') == 1)
    c['  the same 13-week ceiling the shopping list has'] = (
        '(end - start).days > 92' in code)
''',
         r'''        "'in_range'" in code)
    c['  one query for the whole grid, not one per day'] = (
        # MS-1, 12 Nov 2026 - read through the meal plan being looked at.
        any(('for e in (%s' % q) in code and code.count(q) == 1
            for q in ('MealEntry.objects', 'MC.entries()')))
    c['  the same 13-week ceiling the shopping list has'] = (
        '(end - start).days > 92' in code)
'''),
    ]),
    (os.path.join('test_copy_menus.py'), [
        (r'''for name in ('copy_week_rows', 'delete_menu', 'copy_meal_week'):
    a, b = fn(oldv, name), fn(NOW[VIEW], name)
    ok(bool(a) and a == b,
       'CONTROL: %s is byte-identical before and after' % name,
''',
         r'''for name in ('copy_week_rows', 'delete_menu', 'copy_meal_week'):
    a, b = fn(oldv, name), fn(NOW[VIEW], name)
    # MS-1, 12 Nov 2026 - meals are read and written on the meal plan
    # being looked at. That is the only change to these three; undo it
    # and they must still be the same to the byte.
    b = (b.replace('MealEntry.objects.create(calendar=MC.current(), ',
                   'MealEntry.objects.create(')
         .replace('MC.entries()', 'MealEntry.objects'))
    ok(bool(a) and a == b,
       'CONTROL: %s is byte-identical before and after' % name,
'''),
    ]),
    (os.path.join('wellness', 'assets', 'wellness.js'), [
        (r'''    var img = document.querySelector('[data-photo-preview]');
    var label = document.querySelector('[data-photo-label]');
    input.addEventListener('change', function () {
      var f = input.files && input.files[0];
''',
         r'''    var img = document.querySelector('[data-photo-preview]');
    var label = document.querySelector('[data-photo-label]');
    // MS-1 - the camera, or the gallery: the same input, with or
    // without capture, so only one file is ever sent.
    var ways = document.querySelector('[data-photo-ways]');
    if (ways) {
      ways.hidden = false;
      if (label) label.textContent = 'Your photo shows here';
      var pick = input.closest('label');
      if (pick) pick.addEventListener('click', function (e) { if (e.target !== input) e.preventDefault(); });
      ways.querySelector('[data-photo-camera]').addEventListener('click', function () {
        input.setAttribute('capture', 'environment'); input.click();
      });
      ways.querySelector('[data-photo-gallery]').addEventListener('click', function () {
        input.removeAttribute('capture'); input.click();
      });
    }
    input.addEventListener('change', function () {
      var f = input.files && input.files[0];
'''),
    ]),
    (os.path.join('wellness', 'guide.py'), [
        (r'''     'steps': [
         'Body > Progress photos > Add a photo.',
         'Tap the box: take the photo, or choose one from your gallery.',
         'Pick Front, Side, Back or Other and Save. It is locked like '
         'your journal - only you can see it.',
''',
         r'''     'steps': [
         'Body > Progress photos > Add a photo.',
         'Tap Take a photo to use the camera, or Choose from gallery.',
         'Pick Front, Side, Back or Other and Save. It is locked like '
         'your journal - only you can see it.',
'''),
    ]),
    (os.path.join('wellness', 'help.py'), [
        (r'''        'purpose': 'One progress photo.',
        'steps': [
            'Tap the box to take a photo or choose one from your gallery.',
            'Pick Front, Side, Back or Other, and the day it was taken.',
            'Save. It is locked before it is stored.',
''',
         r'''        'purpose': 'One progress photo.',
        'steps': [
            'Tap Take a photo to use the camera, or Choose from gallery.',
            'Pick Front, Side, Back or Other, and the day it was taken.',
            'Save. It is locked before it is stored.',
'''),
    ]),
    (os.path.join('wellness', 'templates', 'wellness', 'base.html'), [
        (r'''<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,500&amp;family=Inter:wght@400;500;600&amp;display=swap">
<link rel="stylesheet" href="{% url 'wellness:asset' 'wellness.css' %}?v=wl21-1">
</head>
{% load tz %}{% get_current_timezone as W_TZ %}
''',
         r'''<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,500&amp;family=Inter:wght@400;500;600&amp;display=swap">
<link rel="stylesheet" href="{% url 'wellness:asset' 'wellness.css' %}?v=wl22-1">
</head>
{% load tz %}{% get_current_timezone as W_TZ %}
'''),
        (r'''</nav>
{% endblock %}
<script src="{% url 'wellness:asset' 'wellness.js' %}?v=wl21-1" defer></script>
</body>
</html>
''',
         r'''</nav>
{% endblock %}
<script src="{% url 'wellness:asset' 'wellness.js' %}?v=wl22-1" defer></script>
</body>
</html>
'''),
    ]),
    (os.path.join('wellness', 'templates', 'wellness', 'photo_new.html'), [
        (r'''  {% csrf_token %}
  <h1 class="w-hello" style="font-size:28px">Add a photo</h1>
  <label class="w-photo-pick" for="ph-file">
    <input id="ph-file" name="photo" type="file" accept="image/*" required data-photo-input>
    <span data-photo-label>Take a photo or choose one</span>
    <img alt="" hidden data-photo-preview>
  </label>
  <fieldset style="border:0;padding:0;margin:0"><legend class="w-small w-quiet" style="margin-bottom:8px">Which way are you facing?</legend>
    <div class="w-chips">{% for k, l in poses %}<label class="w-chip"><input type="radio" name="pose" value="{{ k }}"{% if k == pose %} checked{% endif %}><span>{{ l }}</span></label>{% endfor %}</div>
''',
         r'''  {% csrf_token %}
  <h1 class="w-hello" style="font-size:28px">Add a photo</h1>
  {% comment %} MS-1, 12 Nov 2026 - Demetri: "if I'm on my phone, the phone camera should allow me to take a photo." Two buttons, so the camera does not depend on what the phone's file picker offers: Take a photo opens the camera, Choose from gallery the photos. Without script, tapping the box gives the phone's own choice. {% endcomment %}
  <label class="w-photo-pick" for="ph-file">
    <input id="ph-file" name="photo" type="file" accept="image/*" required data-photo-input>
    <span data-photo-label>Tap to add a photo</span>
    <img alt="" hidden data-photo-preview>
  </label>
  <div class="w-btn-row" data-photo-ways hidden>
    <button type="button" class="w-btn" data-photo-camera>Take a photo</button>
    <button type="button" class="w-btn ghost" data-photo-gallery>Choose from gallery</button>
  </div>
  <fieldset style="border:0;padding:0;margin:0"><legend class="w-small w-quiet" style="margin-bottom:8px">Which way are you facing?</legend>
    <div class="w-chips">{% for k, l in poses %}<label class="w-chip"><input type="radio" name="pose" value="{{ k }}"{% if k == pose %} checked{% endif %}><span>{{ l }}</span></label>{% endfor %}</div>
'''),
    ]),
    (os.path.join('wellness', 'views.py'), [
        (r'''# or script changes: the installed app keeps the old files until the
# version moves. test_wellness_one.py checks the two agree.
SW_VERSION = 'wl21-1'


''',
         r'''# or script changes: the installed app keeps the old files until the
# version moves. test_wellness_one.py checks the two agree.
SW_VERSION = 'wl22-1'


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
    raise SystemExit('MS-1 REFUSED: %s' % msg)


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
    if "'test_meal_share.py'" in read(pq):
        print('MS-1 already applied.')
        return 0
    if "'test_wellness_twentythree.py'" not in read(pq):
        refuse('Release 68 is not applied - this round registers after it.')
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
        print('MS-1 --check: %d file(s) would change, none written; %d '
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
    print('MS-1 applied - one meal plan per person, shared with whom they choose.')
    print('      MIGRATION 0116_meal_calendars - run migrate before pushing.')
    print('      %d file(s) written, backed up to %s' % (len(out), SUFFIX))
    print('      %d file(s) ship with it, wired in rather than written'
          % len(CREATES))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
