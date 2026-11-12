# -*- coding: utf-8 -*-
"""apply_wellness_twentyone.py - round WL-17, 12 Nov 2026.

RELEASE 65 - WELLNESS: WORKOUTS. Bundled with Release 64.

    Demetri, 12 Nov 07:54-08:13:
    - Sports (padel, tennis, squash, netball, soccer...) and Dance, Zumba,
      spin class under Cardio; "Racket or ball" as kit.
    - A routine asks each exercise for what fits it: sets, reps (one
      number; a range only if wanted), a starting weight and rest; seconds
      for a hold, minutes for cardio, dance and sports.
    - Every rep on every set -> the next weight owned; reps only -> one
      more rep; a hold -> a little longer; cardio is not pushed.
    - Your own exercises: edit, delete (with checks) or hide.

New files ship beside this patcher. Stands on Release 64. Idempotent.
Edits backed up to .bak_wellness21. MIGRATION 0013_workouts_sports.
"""
import os
import sys

SUFFIX = '.bak_wellness21'
MARK = 'WL-17, 12 Nov 2026'
CHECK = False
PS1 = 'Push-PendingChanges.ps1'
CREATES = (
    'wellness/migrations/0013_workouts_sports.py',
    'wellness/templates/wellness/my_exercises.html',
    'test_wellness_twentyone.py',
)

SWAPS = [
    (os.path.join('wellness', 'models.py'), [
        (r'''        ('arms', 'Arms'), ('legs', 'Legs'), ('core', 'Core'),
        ('full', 'Full body'), ('cardio', 'Cardio'),
    ]
    EQUIPMENT = [
        ('dumbbell', 'Dumbbells'), ('barbell', 'Barbell'),
        ('kettlebell', 'Kettlebell'), ('bodyweight', 'Bodyweight'),
        ('machine', 'Machine or cable'), ('band', 'Band'),
        ('none', 'Nothing'),
    ]
''',
         r'''        ('arms', 'Arms'), ('legs', 'Legs'), ('core', 'Core'),
        ('full', 'Full body'), ('cardio', 'Cardio'),
        # WL-17, 12 Nov 2026 - Demetri, 07:54: "add a section like Sports".
        ('sport', 'Sports'),
    ]
    EQUIPMENT = [
        ('dumbbell', 'Dumbbells'), ('barbell', 'Barbell'),
        ('kettlebell', 'Kettlebell'), ('bodyweight', 'Bodyweight'),
        ('machine', 'Machine or cable'), ('band', 'Band'),
        ('ball', 'Racket or ball'),
        ('none', 'Nothing'),
    ]
'''),
        (r'''    muscle = models.CharField(max_length=10, choices=MUSCLES)
    equipment = models.CharField(max_length=12, choices=EQUIPMENT)

    class Meta:
''',
         r'''    muscle = models.CharField(max_length=10, choices=MUSCLES)
    equipment = models.CharField(max_length=12, choices=EQUIPMENT)
    # WL-17 - your own exercise, hidden: off every list and routine, still in
    # the workouts it was logged in. Bring it back from My exercises.
    hidden_at = models.DateTimeField(null=True, blank=True)

    class Meta:
'''),
        (r'''    seconds = models.PositiveIntegerField(null=True, blank=True)
    rest = models.PositiveSmallIntegerField(default=60)

    class Meta:
''',
         r'''    seconds = models.PositiveIntegerField(null=True, blank=True)
    rest = models.PositiveSmallIntegerField(default=60)
    # WL-17, 12 Nov 2026 - the starting weight (Demetri, 08:01: "Why do we
    # not put our starting weight when we set up the routine"). Fills the
    # first workout; after that last time's numbers lead.
    weight = models.DecimalField(max_digits=6, decimal_places=2, null=True,
                                 blank=True)

    class Meta:
'''),
    ]),
    (os.path.join('wellness', 'training.py'), [
        (r'''def suggest(rep_min, rep_max, last_sets, equipment_kind, kit):
    """Double progression. `last_sets` = [(weight, reps), ...] of the last
    session's done working sets. Returns {'weight', 'reps', 'why'}."""
    done = [(w, r) for w, r in last_sets if r]
    if not done:
        return {'weight': None, 'reps': rep_min, 'why': 'first'}
    weight = max((w for w, _ in done if w is not None), default=None)
    at_top = [r for w, r in done if w == weight]
    if at_top and all(r >= rep_max for r in at_top):
        up = next_weight(weight, equipment_kind, kit) if weight else None
        if up:
            return {'weight': up, 'reps': rep_min, 'why': 'up'}
        return {'weight': weight, 'reps': rep_max, 'why': 'top'}
    return {'weight': weight, 'reps': min(rep_max, max(at_top or [0]) + 1),
            'why': 'reps'}


''',
         r'''def suggest(rep_min, rep_max, last_sets, equipment_kind, kit):
    """Double progression. `last_sets` = [(weight, reps), ...] of the last
    session's done working sets. Returns {'weight', 'reps', 'why'}.

    WL-17, 12 Nov 2026 - one number works too (rep_min == rep_max: "3 sets
    of 10"): every rep on every set and the next weight up is suggested.
    With no weight (reps only), every rep on every set suggests one more."""
    done = [(w, r) for w, r in last_sets if r]
    if not done:
        return {'weight': None, 'reps': rep_min, 'why': 'first'}
    weight = max((w for w, _ in done if w is not None), default=None)
    at_top = [r for w, r in done if w == weight]
    if at_top and all(r >= rep_max for r in at_top):
        if weight is None:
            return {'weight': None, 'reps': max(at_top) + 1,
                    'why': 'more_reps'}
        up = next_weight(weight, equipment_kind, kit) if weight else None
        if up:
            return {'weight': up, 'reps': rep_min, 'why': 'up'}
        return {'weight': weight, 'reps': rep_max, 'why': 'top'}
    return {'weight': weight, 'reps': min(rep_max, max(at_top or [0]) + 1),
            'why': 'reps'}


# --------------------------------------------------------------------------
# WL-17, 12 Nov 2026 - time in the units people use. Demetri, 08:01: "For
# Zumba or other dances, would we would not measure in seconds?? Maybe 3
# sets of 15 minutes with 5 minute rest between??"
# --------------------------------------------------------------------------
HOLD_STEP = 5      # seconds longer, once every set was held in full


def in_minutes(exercise):
    """Cardio, dance and sports are timed in minutes; a hold (a plank) in
    seconds."""
    return exercise.kind in ('time', 'distance') and \
        exercise.muscle in ('cardio', 'sport')


def suggest_hold(target, last_seconds):
    """A hold: every set held for the whole target last time - a little
    longer today. Returns (seconds, why)."""
    done = [s for s in last_seconds if s]
    if target and done and all(s >= target for s in done):
        return max(done) + HOLD_STEP, 'longer'
    return target, ''


def item_words(item):
    """'3 × 10', '3 × 8–12', '3 × 45 s', '1 × 45 min' - a routine line."""
    ex = item.exercise
    if ex.kind in ('time', 'distance'):
        secs = item.seconds or 0
        if in_minutes(ex):
            return '%d × %d min' % (item.sets, secs // 60)
        return '%d × %d s' % (item.sets, secs)
    if item.rep_min == item.rep_max:
        reps = '%d' % item.rep_max
    else:
        reps = '%d–%d' % (item.rep_min, item.rep_max)
    return '%d × %s' % (item.sets, reps)


def rest_words(seconds, minutes=False):
    if minutes or (seconds and seconds >= 120 and seconds % 60 == 0):
        return '%d min' % (seconds // 60)
    return '%d s' % seconds


'''),
    ]),
    (os.path.join('wellness', 'views_workouts.py'), [
        (r'''
def _exercises(user):
    return Exercise.objects.filter(Q(user__isnull=True) | Q(user=user))


def _my_exercise(user, pk):
    return get_object_or_404(_exercises(user), pk=pk)


''',
         r'''
def _exercises(user):
    """What can be picked: the library and your own, less the hidden."""
    return Exercise.objects.filter(Q(user__isnull=True) | Q(user=user),
                                   hidden_at__isnull=True)


def _my_exercise(user, pk):
    """Any exercise you can see - a hidden one of yours too, for its
    history."""
    return get_object_or_404(
        Exercise.objects.filter(Q(user__isnull=True) | Q(user=user)), pk=pk)


# WL-17, 12 Nov 2026 - a new exercise in a routine opens asking for its
# starting numbers (Demetri, 08:01-08:05), with these filled in to change.
def _starting(ex):
    """{sets, rep_min, rep_max, seconds, rest} for a newly added one."""
    if ex.kind in ('time', 'distance'):
        if TR.in_minutes(ex):
            return {'sets': 1, 'rep_min': 1, 'rep_max': 1, 'seconds': 30 * 60,
                    'rest': 0}
        return {'sets': 3, 'rep_min': 1, 'rep_max': 1, 'seconds': 30,
                'rest': 30}
    return {'sets': 3, 'rep_min': 10, 'rep_max': 10, 'seconds': None,
            'rest': 90 if ex.kind == 'weight' else 60}


'''),
        (r'''                return _routine_page(request, None, 'Give it a short name.')
            routine = Routine.objects.create(user=request.user, name=name)
        if action == 'add':
            ex = _my_exercise(request.user, request.POST.get('exercise'))
            RoutineItem.objects.create(
                routine=routine, exercise=ex,
                position=routine.items.count(),
                sets=3, rep_min=8 if ex.kind != 'time' else 1,
                rep_max=12 if ex.kind != 'time' else 1,
                seconds=30 if ex.kind == 'time' else None,
                rest=60)
        elif action.startswith('remove:'):
            routine.items.filter(pk=action.split(':')[1]).delete()
''',
         r'''                return _routine_page(request, None, 'Give it a short name.')
            routine = Routine.objects.create(user=request.user, name=name)
        new_item = None
        if action == 'add':
            ex = _my_exercise(request.user, request.POST.get('exercise'))
            new_item = RoutineItem.objects.create(
                routine=routine, exercise=ex,
                position=routine.items.count(), **_starting(ex))
        elif action.startswith('remove:'):
            routine.items.filter(pk=action.split(':')[1]).delete()
'''),
        (r'''                if len(d) == 1 and d in '0123456'}))
            routine.save()
            for item in routine.items.all():
                for f, lo, hi in (('sets', 1, 20), ('rep_min', 1, 100),
                                  ('rep_max', 1, 100), ('rest', 0, 600),
                                  ('seconds', 1, 7200)):
                    v = request.POST.get('%s_%d' % (f, item.pk))
                    if v not in (None, ''):
                        try:
                            n = max(lo, min(hi, int(v)))
                        except ValueError:
                            continue
                        setattr(item, f, n)
                if item.rep_max < item.rep_min:
                    item.rep_max = item.rep_min
                item.save()
        if action == 'save':
            return redirect('wellness:workouts')
        return redirect('wellness:routine_edit', pk=routine.pk)
    return _routine_page(request, routine, '')


''',
         r'''                if len(d) == 1 and d in '0123456'}))
            routine.save()
            for item in routine.items.select_related('exercise'):
                if new_item is not None and item.pk == new_item.pk:
                    continue
                _save_item(item, request.POST)
        if action == 'save':
            return redirect('wellness:workouts')
        if new_item is not None:
            return redirect('%s?new=%d#item-%d' % (
                reverse('wellness:routine_edit', args=[routine.pk]),
                new_item.pk, new_item.pk))
        return redirect('wellness:routine_edit', pk=routine.pk)
    return _routine_page(request, routine, '')


def _save_item(item, post):
    """WL-17 - one exercise's numbers from the routine form: sets, reps
    (one number - or a range, if it shows one), a starting weight, time in
    minutes (cardio, dance, sports) or seconds (a hold), and rest."""
    def got(name, lo, hi, cls=int):
        v = post.get('%s_%d' % (name, item.pk))
        if v in (None, ''):
            return None
        try:
            return max(lo, min(hi, cls(str(v).replace(',', '.'))))
        except (ValueError, InvalidOperation):
            return None
    minutes = TR.in_minutes(item.exercise)
    n = got('sets', 1, 20)
    if n is not None:
        item.sets = n
    one = got('reps', 1, 100)
    if one is not None:
        item.rep_min = item.rep_max = one
    lo, hi = got('rep_min', 1, 100), got('rep_max', 1, 100)
    if lo is not None:
        item.rep_min = lo
    if hi is not None:
        item.rep_max = hi
    if item.rep_max < item.rep_min:
        item.rep_max = item.rep_min
    if '%s_%d' % ('weight', item.pk) in post:
        item.weight = got('weight', Decimal('0'), Decimal('1000'), Decimal)
    if minutes:
        m = got('minutes', 1, 600)
        if m is not None:
            item.seconds = m * 60
        r = got('rest_min', 0, 60)
        if r is not None:
            item.rest = r * 60
    else:
        s = got('seconds', 1, 7200)
        if s is not None:
            item.seconds = s
        r = got('rest', 0, 600)
        if r is not None:
            item.rest = r
    item.save()


'''),
        (r'''        if xs:
            groups.append({'label': label, 'exercises': xs})
    return render(request, 'wellness/routine_form.html', {
        'tab': 'workouts', 'routine': routine, 'error': error,
        'items': list(routine.items.select_related('exercise'))
        if routine else [],
        'groups': groups,
        'weekdays': [{'num': str(i), 'name': n,
''',
         r'''        if xs:
            groups.append({'label': label, 'exercises': xs})
    items = list(routine.items.select_related('exercise')) if routine else []
    rng = request.GET.get('range', '')
    for it in items:
        it.in_min = TR.in_minutes(it.exercise)
        it.minutes = (it.seconds or 0) // 60
        it.rest_min = (it.rest or 0) // 60
        it.show_range = it.rep_min != it.rep_max or rng == str(it.pk)
    return render(request, 'wellness/routine_form.html', {
        'tab': 'workouts', 'routine': routine, 'error': error,
        'items': items, 'new_pk': request.GET.get('new', ''),
        'groups': groups,
        'weekdays': [{'num': str(i), 'name': n,
'''),
        (r'''                             [(x.weight, x.reps) for x in last],
                             item.exercise.equipment, profile.equipment)
            for n in range(1, item.sets + 1):
                WorkoutSet.objects.create(
                    session=s, exercise=item.exercise, position=pos,
                    set_no=n,
                    weight=(Decimal(str(sug['weight']))
                            if sug['weight'] is not None else None),
                    reps=sug['reps'] if item.exercise.kind in
                    ('weight', 'reps') else None,
                    seconds=item.seconds if item.exercise.kind == 'time'
                    else None)
    return redirect('wellness:session_live', pk=s.pk)
''',
         r'''                             [(x.weight, x.reps) for x in last],
                             item.exercise.equipment, profile.equipment)
            # WL-17 - the very first time, the routine's starting weight.
            weight = sug['weight']
            if sug['why'] == 'first' and item.weight is not None:
                weight = item.weight
            secs = item.seconds
            if item.exercise.kind == 'time' and \
                    not TR.in_minutes(item.exercise):
                secs, _w = TR.suggest_hold(item.seconds,
                                           [x.seconds for x in last])
            for n in range(1, item.sets + 1):
                WorkoutSet.objects.create(
                    session=s, exercise=item.exercise, position=pos,
                    set_no=n,
                    weight=(Decimal(str(weight))
                            if weight is not None else None),
                    reps=sug['reps'] if item.exercise.kind in
                    ('weight', 'reps') else None,
                    seconds=secs if item.exercise.kind == 'time'
                    else None)
    return redirect('wellness:session_live', pk=s.pk)
'''),
        (r'''                             [(x.weight, x.reps) for x in last],
                             st.exercise.equipment, profile.equipment)
            b = {'exercise': st.exercise, 'rows': [], 'item': it,
                 'rest': it.rest if it else 60, 'last': last,
                 'hint': _hint(sug, it), 'position': st.position}
            by_ex[st.exercise_id] = b
            blocks.append(b)
''',
         r'''                             [(x.weight, x.reps) for x in last],
                             st.exercise.equipment, profile.equipment)
            mins = TR.in_minutes(st.exercise)
            hint = _hint(sug, it)
            if st.exercise.kind == 'time' and not mins and it:
                secs, why = TR.suggest_hold(it.seconds,
                                            [x.seconds for x in last])
                if why:
                    hint = 'You held it every set last time - try %d s.' % secs
            elif mins:
                done_m = sum((x.seconds or 0) for x in last) // 60
                hint = ('Last time: %d min. No pushing here - just enjoy '
                        'it.' % done_m) if done_m else ''
            b = {'exercise': st.exercise, 'rows': [], 'item': it,
                 'rest': it.rest if it else 60, 'last': last,
                 'hint': hint, 'position': st.position, 'in_min': mins,
                 'words': TR.item_words(it) if it else '',
                 'rest_words': TR.rest_words(it.rest if it else 60, mins)}
            by_ex[st.exercise_id] = b
            blocks.append(b)
'''),
        (r'''def _hint(sug, item):
    if sug['why'] == 'up':
        return 'You topped the range last time - %s kg today.' % TR._kg(
            sug['weight'])
    if sug['why'] == 'reps' and sug['weight'] is not None:
        return 'Same weight, aim for %d reps.' % sug['reps']
''',
         r'''def _hint(sug, item):
    if sug['why'] == 'up':
        return ('You did every rep last time - try %s kg today, the next '
                'weight you own.' % TR._kg(sug['weight']))
    if sug['why'] == 'more_reps':
        return 'Every rep last time - aim for %d today.' % sug['reps']
    if sug['why'] == 'reps' and sug['weight'] is not None:
        return 'Same weight, aim for %d reps.' % sug['reps']
'''),
        (r'''

@wellness_view
def kit(request):
''',
         r'''

# --------------------------------------------------------------------------
# WL-17, 12 Nov 2026 - your own exercises: edited, deleted or hidden.
# Demetri, 07:54: "once I have create my own exercise, then I should have
# the ability to Edit it and to Delete it (with the appropriate checks)".
#
#   - Only your own; the library stays as it is.
#   - Name, group and kit can always change. How it is counted can change
#     only until it is logged - a past 3 x 10 at 20 kg means nothing as
#     "time".
#   - Delete says where it is used first:
#       never used            -> gone;
#       in routines only      -> taken out of them, once you tick that;
#       logged in workouts    -> cannot be deleted without losing them, so
#                                Hide it: off every list and routine, still
#                                in the workouts, back any time.
# --------------------------------------------------------------------------
def _own(user, pk):
    return get_object_or_404(Exercise, pk=pk, user=user)


def _uses(ex):
    """(routines it is in, number of workouts it was logged in)."""
    routines = list(Routine.objects.filter(items__exercise=ex,
                                           archived=False).distinct())
    logged = WorkoutSession.objects.filter(sets__exercise=ex).distinct() \
        .count()
    return routines, logged


@wellness_view
def my_exercises(request):
    rows = []
    for ex in Exercise.objects.filter(user=request.user).order_by(
            'hidden_at', 'name'):
        routines, logged = _uses(ex)
        rows.append({'ex': ex, 'routines': len(routines), 'logged': logged,
                     'group': dict(Exercise.MUSCLES).get(ex.muscle, ''),
                     'counted': dict(Exercise.TYPES).get(ex.kind, '').lower()})
    return render(request, 'wellness/my_exercises.html', {
        'tab': 'workouts', 'rows': rows,
    })


@wellness_view
def exercise_edit(request, pk):
    ex = _own(request.user, pk)
    routines, logged = _uses(ex)
    error = ''
    if request.method == 'POST':
        name = (request.POST.get('name') or '').strip()[:80]
        kind = request.POST.get('kind') or ex.kind
        muscle = request.POST.get('muscle')
        equip = request.POST.get('equipment')
        if not name:
            error = 'Give it a name.'
        elif (kind not in dict(Exercise.TYPES) or muscle not in
              dict(Exercise.MUSCLES) or equip not in dict(Exercise.EQUIPMENT)):
            error = 'Choose how it is counted, the group and the kit.'
        elif logged and kind != ex.kind:
            error = ('It is logged in %d workout%s, so how it is counted '
                     'stays as it is.' % (logged, '' if logged == 1 else 's'))
        else:
            ex.name, ex.kind, ex.muscle, ex.equipment = name, kind, muscle, \
                equip
            ex.save()
            return redirect('wellness:my_exercises')
    return render(request, 'wellness/exercise_form.html', {
        'tab': 'workouts', 'error': error, 'types': Exercise.TYPES,
        'muscles': Exercise.MUSCLES, 'equipment': Exercise.EQUIPMENT,
        'ex': ex, 'logged': logged, 'routines': routines,
        'next': '',
    })


@wellness_view
@require_POST
def exercise_delete(request, pk):
    ex = _own(request.user, pk)
    routines, logged = _uses(ex)
    if logged:
        return HttpResponseBadRequest('logged in workouts - hide it instead')
    if routines and request.POST.get('confirm') != 'yes':
        return HttpResponseBadRequest('not confirmed')
    RoutineItem.objects.filter(exercise=ex).delete()
    ex.delete()
    return redirect('wellness:my_exercises')


@wellness_view
@require_POST
def exercise_hide(request, pk):
    ex = _own(request.user, pk)
    if request.POST.get('back') == '1':
        ex.hidden_at = None
    else:
        ex.hidden_at = timezone.now()
        RoutineItem.objects.filter(exercise=ex).delete()
    ex.save(update_fields=['hidden_at'])
    return redirect('wellness:my_exercises')


@wellness_view
def kit(request):
'''),
    ]),
    (os.path.join('wellness', 'urls.py'), [
        (r'''    path('workouts/sets/<int:pk>/delete/', W.set_delete, name='set_delete'),
    path('workouts/exercises/new/', W.exercise_new, name='exercise_new'),
    path('workouts/exercises/<int:pk>/', W.exercise_detail,
         name='exercise_detail'),
''',
         r'''    path('workouts/sets/<int:pk>/delete/', W.set_delete, name='set_delete'),
    path('workouts/exercises/new/', W.exercise_new, name='exercise_new'),
    # WL-17 - your own exercises: edit, delete, hide.
    path('workouts/exercises/mine/', W.my_exercises, name='my_exercises'),
    path('workouts/exercises/<int:pk>/edit/', W.exercise_edit,
         name='exercise_edit'),
    path('workouts/exercises/<int:pk>/delete/', W.exercise_delete,
         name='exercise_delete'),
    path('workouts/exercises/<int:pk>/hide/', W.exercise_hide,
         name='exercise_hide'),
    path('workouts/exercises/<int:pk>/', W.exercise_detail,
         name='exercise_detail'),
'''),
    ]),
    (os.path.join('wellness', 'help.py'), [
        (r'''    'routine_form': {
        'title': 'A routine',
        'purpose': 'A saved workout: its exercises, sets, reps and rest.',
        'steps': [
            'Add exercises from the library, or make your own.',
            'Set the rep range - when you reach the top on every set, the '
            'next workout suggests the next weight you own.',
            'Choose the days it shows on Today.',
        ],
''',
         r'''    'routine_form': {
        'title': 'A routine',
        'purpose': 'A saved workout: its exercises, sets, reps, weight and '
                   'rest.',
        'steps': [
            'Add exercises from the library, or make your own. A new one '
            'opens asking for its starting numbers.',
            'Weights: sets, reps, a starting weight and rest - "3 x 10 at '
            '20 kg, rest 90 s". Reps only: sets, reps and rest.',
            'A hold like a plank: seconds. Cardio, dance and sports: '
            'minutes - "1 x 45 min".',
            'Do every rep on every set and the next workout suggests the '
            'next weight you own; reps only, one more rep; a hold, a little '
            'longer.',
            'Choose the days it shows on Today.',
        ],
'''),
        (r'''        'purpose': 'Log each set as you go.',
        'steps': [
            'The grey numbers are last time - beat them by a rep or a '
            'little weight.',
            'Change the weight or reps if you need to, then tick the set.',
            'A tick starts the rest timer. Skip it whenever you are ready.',
''',
         r'''        'purpose': 'Log each set as you go.',
        'steps': [
            'The grey numbers are last time. A line under the name says '
            'what to try today - "Try 22 kg" after every rep last time.',
            'Cardio, dance and sports are in minutes, and just show last '
            'time - no pushing.',
            'Change the weight or reps if you need to, then tick the set.',
            'A tick starts the rest timer. Skip it whenever you are ready.',
'''),
        (r'''    'exercise_new': {
        'title': 'Your own exercise',
        'purpose': 'Add an exercise the library does not have.',
        'steps': ['Choose how it is measured: weight and reps, reps only, '
                  'time or distance.'],
        'signs': [],
    },
''',
         r'''    'exercise_new': {
        'title': 'Your own exercise',
        'purpose': 'Add an exercise the library does not have - or edit '
                   'one you made.',
        'steps': ['Choose how it is measured: weight and reps, reps only, '
                  'time or distance. Time is minutes for cardio, dance and '
                  'sports; seconds for a hold.',
                  'Mostly works: dance and classes like Zumba are Cardio; '
                  'games like padel or netball are Sports.',
                  'Editing: the name, group and kit can always change; how '
                  'it is counted, only until it is logged in a workout.',
                  'Delete asks first. Logged in a workout? Hide it instead - '
                  'your past workouts keep it.'],
        'signs': [],
    },
    # WL-17, 12 Nov 2026 - your own exercises.
    'my_exercises': {
        'title': 'My exercises',
        'purpose': 'The exercises you made, to edit, delete or hide.',
        'steps': ['Tap Edit to change one, or to delete it at the bottom.',
                  'Never used: Delete removes it. In routines only: it is '
                  'taken out of them, once you tick that.',
                  'Logged in workouts: it can only be hidden - off every '
                  'list and routine, still in your past workouts.',
                  'A hidden one says so here; Bring back puts it back in '
                  'the lists.',
                  'The built-in exercises stay as they are.'],
        'signs': [],
    },
'''),
        (r'''    'journal_new': 'journal_form', 'journal_edit': 'journal_form',
    'routine_new': 'routine_form', 'routine_edit': 'routine_form',
}

''',
         r'''    'journal_new': 'journal_form', 'journal_edit': 'journal_form',
    'routine_new': 'routine_form', 'routine_edit': 'routine_form',
    'exercise_edit': 'exercise_new',
}

'''),
        (r'''    'badges_seen', 'push_subscribe', 'push_unsubscribe', 'push_test',
    'calm_done', 'cycle_quick', 'session_calories',
}

''',
         r'''    'badges_seen', 'push_subscribe', 'push_unsubscribe', 'push_test',
    'calm_done', 'cycle_quick', 'session_calories',
    'exercise_delete', 'exercise_hide',
}

'''),
        (r'''    ],
    'routine_form': [
        'A rep range like 8 to 12 works for most: reach 12 on every set and '
        'the next weight up is suggested.',
        'Rest of 60 to 90 seconds suits most lifts; 2 to 3 minutes for the '
        'heaviest.',
''',
         r'''    ],
    'routine_form': [
        'Most people do 3 x 8 to 12 reps. Prefer a range? Tap "Aim for a '
        'range instead" - the top of it then drives the next weight.',
        'No starting weight? Leave it empty - your first workout asks.',
        'Rest of 60 to 90 seconds suits most lifts; 2 to 3 minutes for the '
        'heaviest.',
'''),
    ]),
    (os.path.join('wellness', 'guide.py'), [
        (r'''          'bathroom, before food.'},
    {'q': 'How does Wellness suggest the next weight?',
     'a': 'Each exercise in a routine has a rep range, say 8 to 12. When you '
          'reach the top of the range on every set, the next workout suggests '
          'the next weight up that you own (set your kit under My '
          'equipment). Until then it suggests the same weight and one more '
          'rep. This is called double progression.'},
    {'q': 'What counts as a record?',
     'a': 'Your heaviest weight on an exercise, the most reps at a weight, '
''',
         r'''          'bathroom, before food.'},
    {'q': 'How does Wellness suggest the next weight?',
     'a': 'Each exercise in a routine has its reps - say 3 x 10. Do every '
          'rep on every set and the next workout suggests the next weight '
          'up that you own (set your kit under My equipment) - "Try 22 kg '
          'today". Miss some and it keeps the weight until you get them all. '
          'Prefer a range, say 8 to 12? Tap "Aim for a range instead": the '
          'top of it then drives the next weight. Reps only: every rep '
          'suggests one more. A hold like a plank: held in full, a little '
          'longer. Cardio, dance and sports are not pushed.'},
    # WL-17, 12 Nov 2026 - Workouts.
    {'q': 'Set up: a routine with your starting numbers',
     'a': 'Each exercise asks for what fits it, starting from sensible '
          'numbers you only change where you differ.',
     'steps': [
         'Workouts > New routine. Name it, then Next: add exercises.',
         'Pick an exercise and tap Add it. It opens highlighted: "Set your '
         'starting numbers".',
         'Weights: sets, reps, a starting weight and rest (3 x 10 at 20 kg, '
         'rest 90 s). A plank: seconds. Zumba, padel, a run: minutes.',
         'Add the next one the same way, then Save routine.']},
    {'q': 'Set up: edit or delete an exercise you made',
     'a': 'Only your own - the built-in ones stay as they are.',
     'steps': [
         'Workouts > My exercises, then Edit beside it.',
         'Change the name, group (Sports, Cardio...) or kit. How it is '
         'counted can change only until you log it.',
         'At the bottom: Delete. Wellness says first where it is used.',
         'Logged in a workout? Hide it instead - it leaves the lists and '
         'routines, and your past workouts keep it.']},
    {'q': 'Where do sports and dance go?',
     'a': 'Padel, tennis, squash, netball, soccer and other games are under '
          'Sports; dance, Zumba and spin class under Cardio. They are timed '
          'in minutes - "1 x 90 min" - and add your watch\'s calories at '
          'the end as usual.'},
    {'q': 'What counts as a record?',
     'a': 'Your heaviest weight on an exercise, the most reps at a weight, '
'''),
        (r'''    # ---- Workouts
    {'q': 'Set up: a routine that tells you when to go heavier',
     'a': 'Wellness suggests the next weight once you reach the top of the '
          'rep range on every set - but only weights you own.',
     'steps': [
         'Workouts > My equipment: type your dumbbells (for example 2 4 6 '
         '8), kettlebells, and your heaviest barbell load. Save.',
         'Workouts > New routine. Give it a name.',
         'Add an exercise, then set Sets, Reps from - to (say 8 to 12) and '
         'Rest.',
         'Under "Show it on Today on...", pick its days. Save.',
         'Start it from Today or Workouts. Grey numbers are last time.']},
''',
         r'''    # ---- Workouts
    {'q': 'Set up: a routine that tells you when to go heavier',
     'a': 'Wellness suggests the next weight once you do every rep on '
          'every set - but only weights you own.',
     'steps': [
         'Workouts > My equipment: type your dumbbells (for example 2 4 6 '
         '8), kettlebells, and your heaviest barbell load. Save.',
         'Workouts > New routine. Give it a name.',
         'Add an exercise, then set Sets, Reps (say 10), a starting Weight '
         'and Rest.',
         'Under "Show it on Today on...", pick its days. Save.',
         'Start it from Today or Workouts. Grey numbers are last time.']},
'''),
        (r'''    ('body', ('trend weight', 'weigh in')),
    ('workouts', ('weight', 'record', 'calories', 'train', 'routine',
                  'workout')),
    ('journal', ('journal', 'Insights', 'line under the quote')),
    ('privacy', ('see my Wellness', 'badges', 'Monday email')),
''',
         r'''    ('body', ('trend weight', 'weigh in')),
    ('workouts', ('weight', 'record', 'calories', 'train', 'routine',
                  'workout', 'exercise', 'sports and dance')),
    ('journal', ('journal', 'Insights', 'line under the quote')),
    ('privacy', ('see my Wellness', 'badges', 'Monday email')),
'''),
    ]),
    (os.path.join('wellness', 'views.py'), [
        (r'''# or script changes: the installed app keeps the old files until the
# version moves. test_wellness_one.py checks the two agree.
SW_VERSION = 'wl18-1'


''',
         r'''# or script changes: the installed app keeps the old files until the
# version moves. test_wellness_one.py checks the two agree.
SW_VERSION = 'wl19-1'


'''),
    ]),
    (os.path.join('wellness', 'templatetags', 'wellness_modules.py'), [
        (r'''    except Exception:  # noqa: BLE001 - a sound must never break a page
        return 'on'
''',
         r'''    except Exception:  # noqa: BLE001 - a sound must never break a page
        return 'on'


@register.filter
def nice_secs(seconds):
    """WL-17, 12 Nov 2026 - 45 -> '45 s', 2700 -> '45 min', 90 -> '90 s':
    a Zumba class reads in minutes, a plank in seconds."""
    try:
        s = int(seconds)
    except (TypeError, ValueError):
        return ''
    if s >= 120:
        return '%d min' % round(s / 60.0)
    return '%d s' % s

'''),
    ]),
    (os.path.join('wellness', 'assets', 'wellness.css'), [
        (r'''  .w-pop, .w-confetti i { animation: none !important; }
}

''',
         r'''  .w-pop, .w-confetti i { animation: none !important; }
}

/* ==========================================================================
   WL-17, 12 Nov 2026 - a routine's numbers: what each exercise asks for, in
   its own units, and a newly added one asking for its starting numbers.
   ========================================================================== */
.w-rgrid { display: grid; grid-template-columns: repeat(auto-fit, minmax(64px, 1fr)); gap: 8px; }
.w-rbox { display: flex; flex-direction: column; gap: 4px; }
.w-rbox .w-input { min-height: 44px; padding: 6px; text-align: center; }
.w-unit { position: relative; display: block; }
.w-unit .w-input { width: 100%; padding-right: 26px; }
.w-unit em { position: absolute; right: 9px; top: 50%; transform: translateY(-50%); font-style: normal; font-size: 13px; color: var(--w-quiet); pointer-events: none; }
.w-ritem.is-new { background: var(--w-sage-track); box-shadow: 0 0 0 2px var(--w-sage); border-radius: 16px; padding: 12px; border-bottom: 0 !important; }
.w-ritem.is-new .w-input { box-shadow: inset 0 0 0 1.5px var(--w-sage-deep); }

'''),
    ]),
    (os.path.join('wellness', 'templates', 'wellness', 'base.html'), [
        (r'''<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,500&amp;family=Inter:wght@400;500;600&amp;display=swap">
<link rel="stylesheet" href="{% url 'wellness:asset' 'wellness.css' %}?v=wl18-1">
</head>
{% load tz %}{% get_current_timezone as W_TZ %}
''',
         r'''<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,500&amp;family=Inter:wght@400;500;600&amp;display=swap">
<link rel="stylesheet" href="{% url 'wellness:asset' 'wellness.css' %}?v=wl19-1">
</head>
{% load tz %}{% get_current_timezone as W_TZ %}
'''),
        (r'''</nav>
{% endblock %}
<script src="{% url 'wellness:asset' 'wellness.js' %}?v=wl18-1" defer></script>
</body>
</html>
''',
         r'''</nav>
{% endblock %}
<script src="{% url 'wellness:asset' 'wellness.js' %}?v=wl19-1" defer></script>
</body>
</html>
'''),
    ]),
    (os.path.join('wellness', 'templates', 'wellness', 'routine_form.html'), [
        (r'''  <section class="w-card" style="gap:14px">
    <h2 class="w-h2" style="font-size:16px">Exercises</h2>
    {% for it in items %}
    <div style="display:flex;flex-direction:column;gap:8px;padding-bottom:12px;border-bottom:1px solid var(--w-line)">
      <div style="display:flex;justify-content:space-between;align-items:center;gap:8px">
        <strong>{{ it.exercise.name }}</strong>
''',
         r'''  <section class="w-card" style="gap:14px">
    <h2 class="w-h2" style="font-size:16px">Exercises</h2>
    {% comment %} WL-17, 12 Nov 2026 - what each exercise asks for: sets, reps (one number; a range if you want), a starting weight and rest; seconds for a hold; minutes for cardio, dance and sports. A new one opens asking for its starting numbers. {% endcomment %}
    {% for it in items %}
    <div id="item-{{ it.pk }}" class="w-ritem{% if new_pk == it.pk|stringformat:'d' %} is-new{% endif %}" style="display:flex;flex-direction:column;gap:8px;padding-bottom:12px;border-bottom:1px solid var(--w-line)" data-routine-item>
      <div style="display:flex;justify-content:space-between;align-items:center;gap:8px">
        <strong>{{ it.exercise.name }}</strong>
'''),
        (r'''        </span>
      </div>
      <div style="display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:8px">
        <label class="w-small w-quiet" style="display:flex;flex-direction:column;gap:4px">Sets<input class="w-input" name="sets_{{ it.pk }}" value="{{ it.sets }}" inputmode="numeric" style="min-height:44px;padding:6px;text-align:center"></label>
        {% if it.exercise.kind == 'time' %}
        <label class="w-small w-quiet" style="display:flex;flex-direction:column;gap:4px;grid-column:span 2">Seconds<input class="w-input" name="seconds_{{ it.pk }}" value="{{ it.seconds|default_if_none:'' }}" inputmode="numeric" style="min-height:44px;padding:6px;text-align:center"></label>
        {% else %}
        <label class="w-small w-quiet" style="display:flex;flex-direction:column;gap:4px">Reps from<input class="w-input" name="rep_min_{{ it.pk }}" value="{{ it.rep_min }}" inputmode="numeric" style="min-height:44px;padding:6px;text-align:center"></label>
        <label class="w-small w-quiet" style="display:flex;flex-direction:column;gap:4px">to<input class="w-input" name="rep_max_{{ it.pk }}" value="{{ it.rep_max }}" inputmode="numeric" style="min-height:44px;padding:6px;text-align:center"></label>
        {% endif %}
        <label class="w-small w-quiet" style="display:flex;flex-direction:column;gap:4px">Rest (s)<input class="w-input" name="rest_{{ it.pk }}" value="{{ it.rest }}" inputmode="numeric" style="min-height:44px;padding:6px;text-align:center"></label>
      </div>
    </div>
    {% empty %}
''',
         r'''        </span>
      </div>
      {% if new_pk == it.pk|stringformat:'d' %}<span class="w-small" style="color:var(--w-sage-deep);font-weight:600" data-new-item>Set your starting numbers</span>{% endif %}
      <div class="w-rgrid">
        <label class="w-small w-quiet w-rbox">Sets<input class="w-input" name="sets_{{ it.pk }}" value="{{ it.sets }}" inputmode="numeric"{% if new_pk == it.pk|stringformat:'d' %} autofocus{% endif %}></label>
        {% if it.exercise.kind == 'time' or it.exercise.kind == 'distance' %}
        {% if it.in_min %}
        <label class="w-small w-quiet w-rbox">Time<span class="w-unit"><input class="w-input" name="minutes_{{ it.pk }}" value="{{ it.minutes }}" inputmode="numeric"><em>min</em></span></label>
        <label class="w-small w-quiet w-rbox">Rest<span class="w-unit"><input class="w-input" name="rest_min_{{ it.pk }}" value="{{ it.rest_min }}" inputmode="numeric"><em>min</em></span></label>
        {% else %}
        <label class="w-small w-quiet w-rbox">Hold<span class="w-unit"><input class="w-input" name="seconds_{{ it.pk }}" value="{{ it.seconds|default_if_none:'' }}" inputmode="numeric"><em>s</em></span></label>
        <label class="w-small w-quiet w-rbox">Rest<span class="w-unit"><input class="w-input" name="rest_{{ it.pk }}" value="{{ it.rest }}" inputmode="numeric"><em>s</em></span></label>
        {% endif %}
        {% else %}
        {% if it.show_range %}
        <label class="w-small w-quiet w-rbox">Reps from<input class="w-input" name="rep_min_{{ it.pk }}" value="{{ it.rep_min }}" inputmode="numeric"></label>
        <label class="w-small w-quiet w-rbox">to<input class="w-input" name="rep_max_{{ it.pk }}" value="{{ it.rep_max }}" inputmode="numeric"></label>
        {% else %}
        <label class="w-small w-quiet w-rbox">Reps<input class="w-input" name="reps_{{ it.pk }}" value="{{ it.rep_max }}" inputmode="numeric"></label>
        {% endif %}
        {% if it.exercise.kind == 'weight' %}
        <label class="w-small w-quiet w-rbox">Weight<span class="w-unit"><input class="w-input" name="weight_{{ it.pk }}" value="{{ it.weight|default_if_none:''|floatformat:'-2' }}" inputmode="decimal" placeholder="—"><em>kg</em></span></label>
        {% endif %}
        <label class="w-small w-quiet w-rbox">Rest<span class="w-unit"><input class="w-input" name="rest_{{ it.pk }}" value="{{ it.rest }}" inputmode="numeric"><em>s</em></span></label>
        {% endif %}
      </div>
      {% if it.exercise.kind == 'weight' or it.exercise.kind == 'reps' %}{% if not it.show_range %}<a class="w-small" href="?range={{ it.pk }}#item-{{ it.pk }}">Aim for a range instead</a>{% elif it.rep_min == it.rep_max %}<a class="w-small" href="?#item-{{ it.pk }}">Use one number</a>{% endif %}{% endif %}
      {% if new_pk == it.pk|stringformat:'d' and it.exercise.kind == 'weight' %}<span class="w-small w-quiet">Your first workout starts from these. After that, last time's numbers lead.</span>{% endif %}
    </div>
    {% empty %}
'''),
        (r'''    <button class="w-btn ghost" name="action" value="add">Add it</button>
    <a class="w-small" href="{% url 'wellness:exercise_new' %}?next={{ request.path|urlencode }}">Not in the list? Make your own</a>
    <p class="w-small w-quiet" style="margin:0">The rep range drives progress: reach the top on every set and the next workout suggests a little more weight - one you own.</p>
  </section>
  {% endif %}
''',
         r'''    <button class="w-btn ghost" name="action" value="add">Add it</button>
    <a class="w-small" href="{% url 'wellness:exercise_new' %}?next={{ request.path|urlencode }}">Not in the list? Make your own</a>
    <p class="w-small w-quiet" style="margin:0">Do every rep on every set and the next workout suggests a little more weight - one you own. Reps only: one more rep. A hold: a little longer.</p>
  </section>
  {% endif %}
'''),
    ]),
    (os.path.join('wellness', 'templates', 'wellness', 'session_live.html'), [
        (r'''  <div style="display:flex;justify-content:space-between;align-items:baseline;gap:8px">
    <a href="{% url 'wellness:exercise_detail' b.exercise.pk %}" style="font-family:var(--w-serif);font-size:20px;color:inherit;text-decoration:none">{{ b.exercise.name }}</a>
    {% if b.item %}<span class="w-small w-quiet">{% if b.exercise.kind == 'time' %}{{ b.item.seconds }} s{% else %}{{ b.item.rep_min }}–{{ b.item.rep_max }} reps{% endif %} · rest {{ b.rest }} s</span>{% endif %}
  </div>
  {% if b.hint %}<div class="w-small" style="color:var(--w-sage-deep)">{{ b.hint }}</div>{% endif %}
  <div class="w-sets">
    <div class="w-set head"><span class="n">Set</span><span>Last time</span>
      {% if b.exercise.kind == 'weight' %}<span style="text-align:center">kg</span><span style="text-align:center">Reps</span>
      {% elif b.exercise.kind == 'reps' %}<span></span><span style="text-align:center">Reps</span>
      {% elif b.exercise.kind == 'time' %}<span></span><span style="text-align:center">Sec</span>
      {% else %}<span style="text-align:center">km</span><span style="text-align:center">Min</span>{% endif %}<span></span></div>
    {% for r in b.rows %}
    <form class="w-set{% if r.set.done %} is-done{% endif %}" method="post" action="{% url 'wellness:set_save' r.set.pk %}" data-set data-rest="{{ b.rest }}">
      {% csrf_token %}
      <input type="hidden" name="done" value="{% if r.set.done %}0{% else %}1{% endif %}">
      <span class="n">{{ r.set.set_no }}</span>
      <span class="prev">{% if r.prev %}{% if r.prev.weight is not None %}{{ r.prev.weight|floatformat:"-2" }} × {{ r.prev.reps }}{% elif r.prev.reps %}{{ r.prev.reps }} reps{% elif r.prev.seconds %}{{ r.prev.seconds }} s{% elif r.prev.distance_m %}{% widthratio r.prev.distance_m 1000 1 %} km{% endif %}{% else %}—{% endif %}</span>
      {% if b.exercise.kind == 'weight' %}
      <input name="weight" inputmode="decimal" value="{{ r.set.weight|default_if_none:''|floatformat:'-2' }}" aria-label="Set {{ r.set.set_no }} weight in kilos">
      <input name="reps" inputmode="numeric" value="{{ r.set.reps|default_if_none:'' }}" aria-label="Set {{ r.set.set_no }} reps">
      {% elif b.exercise.kind == 'reps' %}
      <span></span><input name="reps" inputmode="numeric" value="{{ r.set.reps|default_if_none:'' }}" aria-label="Set {{ r.set.set_no }} reps">
      {% elif b.exercise.kind == 'time' %}
      <span></span><input name="seconds" inputmode="numeric" value="{{ r.set.seconds|default_if_none:'' }}" aria-label="Set {{ r.set.set_no }} seconds">
''',
         r'''  <div style="display:flex;justify-content:space-between;align-items:baseline;gap:8px">
    <a href="{% url 'wellness:exercise_detail' b.exercise.pk %}" style="font-family:var(--w-serif);font-size:20px;color:inherit;text-decoration:none">{{ b.exercise.name }}</a>
    {% comment %} WL-17 - "3 × 10 · rest 90 s", "1 × 45 min". {% endcomment %}
    {% if b.item %}<span class="w-small w-quiet" data-item-words>{{ b.words }}{% if b.rest %} · rest {{ b.rest_words }}{% endif %}</span>{% endif %}
  </div>
  {% if b.hint %}<div class="w-small" style="color:var(--w-sage-deep)">{{ b.hint }}</div>{% endif %}
  <div class="w-sets">
    <div class="w-set head"><span class="n">Set</span><span>Last time</span>
      {% if b.exercise.kind == 'weight' %}<span style="text-align:center">kg</span><span style="text-align:center">Reps</span>
      {% elif b.exercise.kind == 'reps' %}<span></span><span style="text-align:center">Reps</span>
      {% elif b.exercise.kind == 'time' %}<span></span><span style="text-align:center">{% if b.in_min %}Min{% else %}Sec{% endif %}</span>
      {% else %}<span style="text-align:center">km</span><span style="text-align:center">Min</span>{% endif %}<span></span></div>
    {% for r in b.rows %}
    <form class="w-set{% if r.set.done %} is-done{% endif %}" method="post" action="{% url 'wellness:set_save' r.set.pk %}" data-set data-rest="{{ b.rest }}">
      {% csrf_token %}
      <input type="hidden" name="done" value="{% if r.set.done %}0{% else %}1{% endif %}">
      <span class="n">{{ r.set.set_no }}</span>
      <span class="prev">{% if r.prev %}{% if r.prev.weight is not None %}{{ r.prev.weight|floatformat:"-2" }} × {{ r.prev.reps }}{% elif r.prev.reps %}{{ r.prev.reps }} reps{% elif r.prev.seconds and b.in_min %}{% widthratio r.prev.seconds 60 1 %} min{% elif r.prev.seconds %}{{ r.prev.seconds }} s{% elif r.prev.distance_m %}{% widthratio r.prev.distance_m 1000 1 %} km{% endif %}{% else %}—{% endif %}</span>
      {% if b.exercise.kind == 'weight' %}
      <input name="weight" inputmode="decimal" value="{{ r.set.weight|default_if_none:''|floatformat:'-2' }}" aria-label="Set {{ r.set.set_no }} weight in kilos">
      <input name="reps" inputmode="numeric" value="{{ r.set.reps|default_if_none:'' }}" aria-label="Set {{ r.set.set_no }} reps">
      {% elif b.exercise.kind == 'reps' %}
      <span></span><input name="reps" inputmode="numeric" value="{{ r.set.reps|default_if_none:'' }}" aria-label="Set {{ r.set.set_no }} reps">
      {% elif b.exercise.kind == 'time' and b.in_min %}
      <span></span><input name="minutes" inputmode="numeric" value="{% if r.set.seconds %}{% widthratio r.set.seconds 60 1 %}{% endif %}" aria-label="Set {{ r.set.set_no }} minutes">
      {% elif b.exercise.kind == 'time' %}
      <span></span><input name="seconds" inputmode="numeric" value="{{ r.set.seconds|default_if_none:'' }}" aria-label="Set {{ r.set.set_no }} seconds">
'''),
    ]),
    (os.path.join('wellness', 'templates', 'wellness', 'exercise_form.html'), [
        (r'''{% extends "wellness/base.html" %}
{% block title %}New exercise · Wellness{% endblock %}
{% block top_left %}<a class="w-home" href="{% if next %}{{ next }}{% else %}{% url 'wellness:workouts' %}{% endif %}"><svg width="16" height="16" viewBox="0 0 16 16" aria-hidden="true"><path d="M10 3.5L5.5 8l4.5 4.5" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg> Back</a>{% endblock %}
{% block tabs %}{% endblock %}
{% block content %}
<form method="post" style="display:flex;flex-direction:column;gap:16px">
  {% csrf_token %}
  <input type="hidden" name="next" value="{{ next }}">
  <h1 class="w-hello" style="font-size:28px">Your own exercise</h1>
  <label for="x-name" class="w-small w-quiet">Name</label>
  <input class="w-input" id="x-name" name="name" maxlength="80" autocomplete="off">
  <fieldset style="border:0;padding:0;margin:0"><legend class="w-small w-quiet" style="margin-bottom:8px">How is it counted?</legend>
    <div class="w-chips">{% for k, l in types %}<label class="w-chip"><input type="radio" name="kind" value="{{ k }}"{% if forloop.first %} checked{% endif %}><span>{{ l }}</span></label>{% endfor %}</div></fieldset>
  <fieldset style="border:0;padding:0;margin:0"><legend class="w-small w-quiet" style="margin-bottom:8px">Mostly works</legend>
    <div class="w-chips">{% for k, l in muscles %}<label class="w-chip"><input type="radio" name="muscle" value="{{ k }}"{% if forloop.first %} checked{% endif %}><span>{{ l }}</span></label>{% endfor %}</div></fieldset>
  <fieldset style="border:0;padding:0;margin:0"><legend class="w-small w-quiet" style="margin-bottom:8px">With</legend>
    <div class="w-chips">{% for k, l in equipment %}<label class="w-chip"><input type="radio" name="equipment" value="{{ k }}"{% if forloop.first %} checked{% endif %}><span>{{ l }}</span></label>{% endfor %}</div></fieldset>
  {% if error %}<div class="w-error">{{ error }}</div>{% endif %}
  <button class="w-btn full" type="submit">Save</button>
</form>
{% endblock %}
''',
         r'''{% extends "wellness/base.html" %}
{% block title %}{% if ex %}{{ ex.name }}{% else %}New exercise{% endif %} · Wellness{% endblock %}
{% block top_left %}<a class="w-home" href="{% if ex %}{% url 'wellness:my_exercises' %}{% elif next %}{{ next }}{% else %}{% url 'wellness:workouts' %}{% endif %}"><svg width="16" height="16" viewBox="0 0 16 16" aria-hidden="true"><path d="M10 3.5L5.5 8l4.5 4.5" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg> {% if ex %}My exercises{% else %}Back{% endif %}</a>{% endblock %}
{% block tabs %}{% endblock %}
{% block content %}
{% comment %} WL-17, 12 Nov 2026 - one form for a new exercise and for editing your own: Sports, Racket or ball, and how it is counted fixed once it is logged. {% endcomment %}
<form method="post" style="display:flex;flex-direction:column;gap:16px">
  {% csrf_token %}
  <input type="hidden" name="next" value="{{ next }}">
  <h1 class="w-hello" style="font-size:28px">{% if ex %}Edit your exercise{% else %}Your own exercise{% endif %}</h1>
  <label for="x-name" class="w-small w-quiet">Name</label>
  <input class="w-input" id="x-name" name="name" maxlength="80" autocomplete="off" value="{{ ex.name|default:'' }}">
  <fieldset style="border:0;padding:0;margin:0"><legend class="w-small w-quiet" style="margin-bottom:8px">How is it counted?</legend>
    {% if ex and logged %}
    <input type="hidden" name="kind" value="{{ ex.kind }}">
    <div class="w-chips">{% for k, l in types %}{% if k == ex.kind %}<label class="w-chip"><input type="radio" checked disabled aria-label="{{ l }}"><span>{{ l }}</span></label>{% endif %}{% endfor %}</div>
    <span class="w-small w-quiet" data-kind-fixed>Logged in {{ logged }} workout{{ logged|pluralize }}, so this stays as it is - your past numbers keep their meaning.</span>
    {% else %}
    <div class="w-chips">{% for k, l in types %}<label class="w-chip"><input type="radio" name="kind" value="{{ k }}"{% if ex %}{% if ex.kind == k %} checked{% endif %}{% elif forloop.first %} checked{% endif %}><span>{{ l }}</span></label>{% endfor %}</div>
    {% endif %}
    <span class="w-small w-quiet" style="display:block;margin-top:6px">Time is in minutes for cardio, dance and sports; in seconds for holds like a plank.</span></fieldset>
  <fieldset style="border:0;padding:0;margin:0"><legend class="w-small w-quiet" style="margin-bottom:8px">Mostly works</legend>
    <div class="w-chips">{% for k, l in muscles %}<label class="w-chip"><input type="radio" name="muscle" value="{{ k }}"{% if ex %}{% if ex.muscle == k %} checked{% endif %}{% elif forloop.first %} checked{% endif %}><span>{{ l }}</span></label>{% endfor %}</div>
    <span class="w-small w-quiet" style="display:block;margin-top:6px">Dance and fitness classes like Zumba: Cardio. Games like padel or netball: Sports.</span></fieldset>
  <fieldset style="border:0;padding:0;margin:0"><legend class="w-small w-quiet" style="margin-bottom:8px">With</legend>
    <div class="w-chips">{% for k, l in equipment %}<label class="w-chip"><input type="radio" name="equipment" value="{{ k }}"{% if ex %}{% if ex.equipment == k %} checked{% endif %}{% elif forloop.first %} checked{% endif %}><span>{{ l }}</span></label>{% endfor %}</div></fieldset>
  {% if error %}<div class="w-error">{{ error }}</div>{% endif %}
  <button class="w-btn full" type="submit">Save</button>
</form>
{% if ex %}
<details class="w-card" data-exercise-delete>
  <summary style="cursor:pointer;min-height:44px;display:flex;align-items:center">{% if logged %}Hide this exercise{% else %}Delete this exercise{% endif %}</summary>
  {% if logged %}
  <p class="w-quiet" style="margin:0">You logged {{ ex.name }} in {{ logged }} workout{{ logged|pluralize }}, so it cannot be deleted without losing them. Hide it instead: it leaves the exercise list{% if routines %} and {{ routines|length }} routine{{ routines|length|pluralize }}{% endif %}, and your past workouts keep it. Bring it back from My exercises any time.</p>
  <form method="post" action="{% url 'wellness:exercise_hide' ex.pk %}">{% csrf_token %}<button class="w-btn ghost full" type="submit">Hide it</button></form>
  {% elif routines %}
  <p class="w-quiet" style="margin:0">It is in {{ routines|length }} routine{{ routines|length|pluralize }}: {% for r in routines %}{{ r.name }}{% if not forloop.last %}, {% endif %}{% endfor %}. Deleting takes it out of {% if routines|length == 1 %}it{% else %}them{% endif %}.</p>
  <form method="post" action="{% url 'wellness:exercise_delete' ex.pk %}" style="display:flex;flex-direction:column;gap:12px">{% csrf_token %}
    <label style="display:flex;gap:10px;align-items:center;min-height:44px"><input type="checkbox" name="confirm" value="yes" required style="width:22px;height:22px"> Yes, take it out of {% if routines|length == 1 %}that routine{% else %}those routines{% endif %} too</label>
    <button class="w-btn ghost" type="submit">Delete</button></form>
  {% else %}
  <p class="w-quiet" style="margin:0">It is not in any routine or workout. Delete it?</p>
  <form method="post" action="{% url 'wellness:exercise_delete' ex.pk %}">{% csrf_token %}<button class="w-btn ghost full" type="submit">Delete</button></form>
  {% endif %}
</details>
{% endif %}
{% endblock %}
'''),
    ]),
    (os.path.join('wellness', 'templates', 'wellness', 'workouts.html'), [
        (r'''{% extends "wellness/base.html" %}
{% block title %}Workouts · Wellness{% endblock %}
{% block content %}
''',
         r'''{% extends "wellness/base.html" %}
{% load wellness_modules %}
{% block title %}Workouts · Wellness{% endblock %}
{% block content %}
'''),
        (r'''  <a href="{% url 'wellness:exercise_detail' p.exercise.pk %}" class="w-row" style="min-height:44px">
    <span>{{ p.exercise.name }}</span>
    <span class="w-small w-quiet">{% if p.weight is not None %}{{ p.weight|floatformat:"-2" }} kg × {{ p.reps }}{% elif p.reps %}{{ p.reps }} reps{% elif p.seconds %}{{ p.seconds }} s{% endif %} · {{ p.session.date|date:"j M" }}</span>
  </a>
  {% endfor %}
''',
         r'''  <a href="{% url 'wellness:exercise_detail' p.exercise.pk %}" class="w-row" style="min-height:44px">
    <span>{{ p.exercise.name }}</span>
    <span class="w-small w-quiet">{% if p.weight is not None %}{{ p.weight|floatformat:"-2" }} kg × {{ p.reps }}{% elif p.reps %}{{ p.reps }} reps{% elif p.seconds %}{{ p.seconds|nice_secs }}{% endif %} · {{ p.session.date|date:"j M" }}</span>
  </a>
  {% endfor %}
'''),
        (r'''{% endif %}

<a class="w-btn quiet" href="{% url 'wellness:kit' %}" style="align-self:flex-start;padding:0">My equipment</a>
{% endblock %}
''',
         r'''{% endif %}

<span style="display:flex;gap:18px;flex-wrap:wrap"><a class="w-btn quiet" href="{% url 'wellness:kit' %}" style="align-self:flex-start;padding:0">My equipment</a>
<a class="w-btn quiet" href="{% url 'wellness:my_exercises' %}" style="align-self:flex-start;padding:0" data-my-exercises-link>My exercises</a></span>
{% endblock %}
'''),
    ]),
    (os.path.join('wellness', 'templates', 'wellness', 'session_detail.html'), [
        (r'''{% extends "wellness/base.html" %}
{% block title %}{{ s.name }} · Wellness{% endblock %}
{% block top_left %}<a class="w-home" href="{% url 'wellness:workouts' %}"><svg width="16" height="16" viewBox="0 0 16 16" aria-hidden="true"><path d="M10 3.5L5.5 8l4.5 4.5" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg> Workouts</a>{% endblock %}
''',
         r'''{% extends "wellness/base.html" %}
{% load wellness_modules %}
{% block title %}{{ s.name }} · Wellness{% endblock %}
{% block top_left %}<a class="w-home" href="{% url 'wellness:workouts' %}"><svg width="16" height="16" viewBox="0 0 16 16" aria-hidden="true"><path d="M10 3.5L5.5 8l4.5 4.5" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg> Workouts</a>{% endblock %}
'''),
        (r'''<div class="w-card sand" style="flex-direction:row;align-items:center;gap:12px;padding:14px 18px">
  <svg width="26" height="26" viewBox="0 0 40 40" aria-hidden="true"><path d="M20 5l4.4 9 9.6 1.3-7 6.7 1.7 9.6L20 27l-8.7 4.6 1.7-9.6-7-6.7 9.6-1.3z" fill="#E8DCC8" stroke="#A0824F" stroke-width="1.6" stroke-linejoin="round"/></svg>
  <span><strong>{{ r.exercise.name }}</strong> · {% if r.weight is not None %}{{ r.weight|floatformat:"-2" }} kg × {{ r.reps }}{% elif r.reps %}{{ r.reps }} reps{% elif r.seconds %}{{ r.seconds }} s{% endif %}</span>
</div>
{% endfor %}
{% for b in blocks %}
<section class="w-list">
  <a href="{% url 'wellness:exercise_detail' b.exercise.pk %}" class="w-h2" style="font-size:16px;display:flex;min-height:52px;align-items:center;color:inherit;text-decoration:none">{{ b.exercise.name }}</a>
  {% for st in b.sets %}
  <div class="w-row" style="min-height:44px"><span class="w-quiet">Set {{ st.set_no }}</span><span>{% if st.weight is not None %}{{ st.weight|floatformat:"-2" }} kg × {{ st.reps }}{% elif st.reps %}{{ st.reps }} reps{% elif st.distance_m %}{% widthratio st.distance_m 1000 1 %} km{% endif %}{% if st.seconds %} · {{ st.seconds }} s{% endif %}{% if st.is_pr %} ★{% endif %}</span></div>
  {% endfor %}
</section>
''',
         r'''<div class="w-card sand" style="flex-direction:row;align-items:center;gap:12px;padding:14px 18px">
  <svg width="26" height="26" viewBox="0 0 40 40" aria-hidden="true"><path d="M20 5l4.4 9 9.6 1.3-7 6.7 1.7 9.6L20 27l-8.7 4.6 1.7-9.6-7-6.7 9.6-1.3z" fill="#E8DCC8" stroke="#A0824F" stroke-width="1.6" stroke-linejoin="round"/></svg>
  <span><strong>{{ r.exercise.name }}</strong> · {% if r.weight is not None %}{{ r.weight|floatformat:"-2" }} kg × {{ r.reps }}{% elif r.reps %}{{ r.reps }} reps{% elif r.seconds %}{{ r.seconds|nice_secs }}{% endif %}</span>
</div>
{% endfor %}
{% for b in blocks %}
<section class="w-list">
  <a href="{% url 'wellness:exercise_detail' b.exercise.pk %}" class="w-h2" style="font-size:16px;display:flex;min-height:52px;align-items:center;color:inherit;text-decoration:none">{{ b.exercise.name }}</a>
  {% for st in b.sets %}
  <div class="w-row" style="min-height:44px"><span class="w-quiet">Set {{ st.set_no }}</span><span>{% if st.weight is not None %}{{ st.weight|floatformat:"-2" }} kg × {{ st.reps }}{% elif st.reps %}{{ st.reps }} reps{% elif st.distance_m %}{% widthratio st.distance_m 1000 1 %} km{% endif %}{% if st.seconds %} · {{ st.seconds|nice_secs }}{% endif %}{% if st.is_pr %} ★{% endif %}</span></div>
  {% endfor %}
</section>
'''),
    ]),
    (os.path.join('wellness', 'templates', 'wellness', 'exercise_detail.html'), [
        (r'''{% extends "wellness/base.html" %}
{% block title %}{{ ex.name }} · Wellness{% endblock %}
{% block top_left %}<a class="w-home" href="{% url 'wellness:workouts' %}"><svg width="16" height="16" viewBox="0 0 16 16" aria-hidden="true"><path d="M10 3.5L5.5 8l4.5 4.5" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg> Workouts</a>{% endblock %}
''',
         r'''{% extends "wellness/base.html" %}
{% load wellness_modules %}
{% block title %}{{ ex.name }} · Wellness{% endblock %}
{% block top_left %}<a class="w-home" href="{% url 'wellness:workouts' %}"><svg width="16" height="16" viewBox="0 0 16 16" aria-hidden="true"><path d="M10 3.5L5.5 8l4.5 4.5" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg> Workouts</a>{% endblock %}
'''),
        (r'''  {% if best.e1rm %}<div class="w-row" style="min-height:44px"><span>Estimated one-rep max</span><strong>{{ best.e1rm|floatformat:1 }} kg</strong></div>{% endif %}
  {% if best.reps %}<div class="w-row" style="min-height:44px"><span>Most reps</span><strong>{{ best.reps }}</strong></div>{% endif %}
  {% if best.seconds %}<div class="w-row" style="min-height:44px"><span>Longest</span><strong>{{ best.seconds }} s</strong></div>{% endif %}
  {% if best.metres %}<div class="w-row" style="min-height:44px"><span>Furthest</span><strong>{% widthratio best.metres 1000 1 %} km</strong></div>{% endif %}
  {% if best.weight is None and not best.reps and not best.seconds and not best.metres %}<p class="w-quiet" style="margin:0">No sets logged yet.</p>{% endif %}
''',
         r'''  {% if best.e1rm %}<div class="w-row" style="min-height:44px"><span>Estimated one-rep max</span><strong>{{ best.e1rm|floatformat:1 }} kg</strong></div>{% endif %}
  {% if best.reps %}<div class="w-row" style="min-height:44px"><span>Most reps</span><strong>{{ best.reps }}</strong></div>{% endif %}
  {% if best.seconds %}<div class="w-row" style="min-height:44px"><span>Longest</span><strong>{{ best.seconds|nice_secs }}</strong></div>{% endif %}
  {% if best.metres %}<div class="w-row" style="min-height:44px"><span>Furthest</span><strong>{% widthratio best.metres 1000 1 %} km</strong></div>{% endif %}
  {% if best.weight is None and not best.reps and not best.seconds and not best.metres %}<p class="w-quiet" style="margin:0">No sets logged yet.</p>{% endif %}
'''),
        (r'''  <h2 class="w-h2" style="font-size:16px;padding-top:16px">History</h2>
  {% for h in history %}
  <div class="w-row"><span class="w-row-main"><span class="w-row-name">{{ h.date|date:"D j M" }}</span><span class="w-row-sub">{% for st in h.sets %}{% if st.weight is not None %}{{ st.weight|floatformat:"-2" }}×{{ st.reps }}{% elif st.reps %}{{ st.reps }}{% elif st.seconds %}{{ st.seconds }}s{% endif %}{% if not forloop.last %}, {% endif %}{% endfor %}</span></span></div>
  {% endfor %}
</section>
''',
         r'''  <h2 class="w-h2" style="font-size:16px;padding-top:16px">History</h2>
  {% for h in history %}
  <div class="w-row"><span class="w-row-main"><span class="w-row-name">{{ h.date|date:"D j M" }}</span><span class="w-row-sub">{% for st in h.sets %}{% if st.weight is not None %}{{ st.weight|floatformat:"-2" }}×{{ st.reps }}{% elif st.reps %}{{ st.reps }}{% elif st.seconds %}{{ st.seconds|nice_secs }}{% endif %}{% if not forloop.last %}, {% endif %}{% endfor %}</span></span></div>
  {% endfor %}
</section>
'''),
    ]),
    (os.path.join('test_wellness_three.py'), [
        (r'''gate = read(J(ROOT, PS1))
ok("'%s'" % ME in gate, 'on the push gate suite list')
ok("Text = 'def suggest('" in gate, '  with a sentinel on the progression')
ok(os.path.isfile(J(ROOT, PATCHER)), 'the patcher is on disk')

''',
         r'''gate = read(J(ROOT, PS1))
ok("'%s'" % ME in gate, 'on the push gate suite list')
# WL-17, 12 Nov 2026: the row moved to 'def suggest_hold(' when training.py
# was backed up again (a Text in every backup can never fail).
ok("Text = 'def suggest('" in gate or
   "File = 'wellness/training.py'; Text = 'def suggest_hold('" in gate,
   '  with a sentinel on the progression')
ok(os.path.isfile(J(ROOT, PATCHER)), 'the patcher is on disk')

'''),
    ]),
    (os.path.join('Push-PendingChanges.ps1'), [
        (r'''    @{ File = 'pages/views/lease_signing_create.py'; Text = 'from .lease_signing_sign import _invite'; What = 'ES-3b: one spelling of mint-a-link-and-send-it, imported from ES-4 rather than copied - a second copy here would be a second answer to what a resend does to the old link, and ES-1 made that a rule when it stored the token hashed' },
    @{ File = 'pages/management/commands/check_lease_renewal_and_invoices.py'; Text = 'Celebration email to %s'; What = 'CX-1: the celebrations email retries like the others - without it one mail-server hiccup loses every celebration email for the day' },
    @{ File = 'wellness/training.py'; Text = 'def suggest('; What = 'WL-3: the workout rules are on disk - without them no workout can start' },
    @{ File = 'wellness/cycle.py'; Text = 'open_period'; What = 'CY-1/CY-2: the cycle rules are on disk, with the one-tap period - without them the tracker cannot open' },
    @{ File = 'wellness/badges.py'; Text = 'First breath'; What = 'WL-4a/WL-7: the badge rules are on disk, with the Calm badges - without them Today cannot open' },
''',
         r'''    @{ File = 'pages/views/lease_signing_create.py'; Text = 'from .lease_signing_sign import _invite'; What = 'ES-3b: one spelling of mint-a-link-and-send-it, imported from ES-4 rather than copied - a second copy here would be a second answer to what a resend does to the old link, and ES-1 made that a rule when it stored the token hashed' },
    @{ File = 'pages/management/commands/check_lease_renewal_and_invoices.py'; Text = 'Celebration email to %s'; What = 'CX-1: the celebrations email retries like the others - without it one mail-server hiccup loses every celebration email for the day' },
    @{ File = 'wellness/training.py'; Text = 'def suggest_hold('; What = 'WL-3/WL-17: the workout rules are on disk, holds included - without them no workout can start' },
    @{ File = 'wellness/cycle.py'; Text = 'open_period'; What = 'CY-1/CY-2: the cycle rules are on disk, with the one-tap period - without them the tracker cannot open' },
    @{ File = 'wellness/badges.py'; Text = 'First breath'; What = 'WL-4a/WL-7: the badge rules are on disk, with the Calm badges - without them Today cannot open' },
'''),
        (r'''    @{ File = 'wellness/modules.py'; Text = 'def tz_or_none('; What = 'WL-9/WL-16: the section switches and the time zone reader are on disk - without them no Wellness page opens' },
    @{ File = 'wellness/phases.py'; Text = 'DISCLAIMER = ('; What = 'CY-2/CY-4: the cycle phases are on disk, honestly worded - without them the cycle tracker cannot open' },
    @{ File = 'wellness/modules.py'; Text = 'def phone_now('; What = "WL-16: Wellness runs on the phone's clock - without it no Wellness page can be drawn" },
    @{ File = 'wellness/templatetags/wellness_modules.py'; Text = 'def fx_state('; What = 'WL-15: the sounds-and-vibration switch is on disk - without it no Wellness page can be drawn' },
''',
         r'''    @{ File = 'wellness/modules.py'; Text = 'def tz_or_none('; What = 'WL-9/WL-16: the section switches and the time zone reader are on disk - without them no Wellness page opens' },
    @{ File = 'wellness/phases.py'; Text = 'DISCLAIMER = ('; What = 'CY-2/CY-4: the cycle phases are on disk, honestly worded - without them the cycle tracker cannot open' },
    @{ File = 'wellness/training.py'; Text = 'def in_minutes('; What = 'WL-17: the workout rules know minutes from seconds - without them no workout can be started' },
    @{ File = 'wellness/modules.py'; Text = 'def phone_now('; What = "WL-16: Wellness runs on the phone's clock - without it no Wellness page can be drawn" },
    @{ File = 'wellness/templatetags/wellness_modules.py'; Text = 'def fx_state('; What = 'WL-15: the sounds-and-vibration switch is on disk - without it no Wellness page can be drawn' },
'''),
        (r'''    'test_gate_solo.py',
    # WL-16, 12 Nov 2026 - Wellness: catch up, the whole day done, the phone's clock.
    'test_wellness_twenty.py'
)
# NUMBER EVERY SUITE AS IT RUNS - Demetri, 1 Oct 2026: "for every check of
''',
         r'''    'test_gate_solo.py',
    # WL-16, 12 Nov 2026 - Wellness: catch up, the whole day done, the phone's clock.
    'test_wellness_twenty.py',
    # WL-17, 12 Nov 2026 - Wellness: workouts - sports, starting numbers, your own exercises.
    'test_wellness_twentyone.py'
)
# NUMBER EVERY SUITE AS IT RUNS - Demetri, 1 Oct 2026: "for every check of
'''),
    ]),
    (os.path.join('alv_rounds.py'), [
        (r'''    # WL-16, 12 Nov 2026 - Wellness: catch up, the whole day done, the phone's clock.
    '.bak_wellness20',
]

''',
         r'''    # WL-16, 12 Nov 2026 - Wellness: catch up, the whole day done, the phone's clock.
    '.bak_wellness20',
    # WL-17, 12 Nov 2026 - Wellness: workouts - sports, starting numbers, your own exercises.
    '.bak_wellness21',
]

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
    raise SystemExit('WL-17 REFUSED: %s' % msg)


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
    if "'test_wellness_twentyone.py'" in read(pq):
        print('WL-17 already applied.')
        return 0
    if "'test_wellness_twenty.py'" not in read(pq):
        refuse('Release 64 is not applied - this round registers after it.')
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
        print('WL-17 --check: %d file(s) would change, none written; %d '
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
    print('WL-17 applied - Wellness: workouts - sports, starting numbers, your own exercises.')
    print('      MIGRATION 0013_workouts_sports - run migrate before pushing.')
    print('      %d file(s) written, backed up to %s' % (len(out), SUFFIX))
    print('      %d file(s) ship with it, wired in rather than written'
          % len(CREATES))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
