# -*- coding: utf-8 -*-
"""WL-3, 30 Oct 2026 - the shared exercise library (user=None).

The list lives HERE, not imported from app code, so this migration means
the same thing whenever it runs. Rows are matched by name: running it on a
database that already has them changes nothing, and reversing it removes
only library rows that no workout or routine uses.
"""
from django.db import migrations

LIBRARY = [
    # (name, kind, muscle, equipment)
    ('Dumbbell shoulder press', 'weight', 'shoulders', 'dumbbell'),
    ('Arnold press', 'weight', 'shoulders', 'dumbbell'),
    ('Lateral raise', 'weight', 'shoulders', 'dumbbell'),
    ('Front raise', 'weight', 'shoulders', 'dumbbell'),
    ('Reverse fly', 'weight', 'back', 'dumbbell'),
    ('Dumbbell bent-over row', 'weight', 'back', 'dumbbell'),
    ('One-arm dumbbell row', 'weight', 'back', 'dumbbell'),
    ('Dumbbell shrug', 'weight', 'back', 'dumbbell'),
    ('Dumbbell bicep curl', 'weight', 'arms', 'dumbbell'),
    ('Hammer curl', 'weight', 'arms', 'dumbbell'),
    ('Overhead tricep extension', 'weight', 'arms', 'dumbbell'),
    ('Tricep kickback', 'weight', 'arms', 'dumbbell'),
    ('Dumbbell chest press', 'weight', 'chest', 'dumbbell'),
    ('Dumbbell floor press', 'weight', 'chest', 'dumbbell'),
    ('Dumbbell fly', 'weight', 'chest', 'dumbbell'),
    ('Goblet squat', 'weight', 'legs', 'dumbbell'),
    ('Dumbbell lunge', 'weight', 'legs', 'dumbbell'),
    ('Dumbbell Romanian deadlift', 'weight', 'legs', 'dumbbell'),
    ('Step-up', 'weight', 'legs', 'dumbbell'),
    ('Dumbbell calf raise', 'weight', 'legs', 'dumbbell'),
    ('Barbell back squat', 'weight', 'legs', 'barbell'),
    ('Barbell front squat', 'weight', 'legs', 'barbell'),
    ('Barbell deadlift', 'weight', 'full', 'barbell'),
    ('Barbell Romanian deadlift', 'weight', 'legs', 'barbell'),
    ('Barbell bench press', 'weight', 'chest', 'barbell'),
    ('Barbell overhead press', 'weight', 'shoulders', 'barbell'),
    ('Barbell bent-over row', 'weight', 'back', 'barbell'),
    ('Barbell curl', 'weight', 'arms', 'barbell'),
    ('Barbell upright row', 'weight', 'shoulders', 'barbell'),
    ('Hip thrust', 'weight', 'legs', 'barbell'),
    ('Kettlebell swing', 'weight', 'full', 'kettlebell'),
    ('Kettlebell goblet squat', 'weight', 'legs', 'kettlebell'),
    ('Kettlebell clean and press', 'weight', 'full', 'kettlebell'),
    ('Turkish get-up', 'weight', 'full', 'kettlebell'),
    ('Push-up', 'reps', 'chest', 'bodyweight'),
    ('Knee push-up', 'reps', 'chest', 'bodyweight'),
    ('Pull-up', 'reps', 'back', 'bodyweight'),
    ('Chin-up', 'reps', 'back', 'bodyweight'),
    ('Dip', 'reps', 'arms', 'bodyweight'),
    ('Bodyweight squat', 'reps', 'legs', 'bodyweight'),
    ('Walking lunge', 'reps', 'legs', 'bodyweight'),
    ('Glute bridge', 'reps', 'legs', 'bodyweight'),
    ('Burpee', 'reps', 'full', 'bodyweight'),
    ('Mountain climber', 'reps', 'core', 'bodyweight'),
    ('Plank', 'time', 'core', 'bodyweight'),
    ('Side plank', 'time', 'core', 'bodyweight'),
    ('Hollow hold', 'time', 'core', 'bodyweight'),
    ('Dead bug', 'reps', 'core', 'bodyweight'),
    ('Bird dog', 'reps', 'core', 'bodyweight'),
    ('Crunch', 'reps', 'core', 'bodyweight'),
    ('Russian twist', 'reps', 'core', 'bodyweight'),
    ('Lying leg raise', 'reps', 'core', 'bodyweight'),
    ('Lat pulldown', 'weight', 'back', 'machine'),
    ('Seated cable row', 'weight', 'back', 'machine'),
    ('Leg press', 'weight', 'legs', 'machine'),
    ('Leg extension', 'weight', 'legs', 'machine'),
    ('Leg curl', 'weight', 'legs', 'machine'),
    ('Machine chest press', 'weight', 'chest', 'machine'),
    ('Band pull-apart', 'reps', 'back', 'band'),
    ('Band row', 'reps', 'back', 'band'),
    ('Walk', 'distance', 'cardio', 'none'),
    ('Run', 'distance', 'cardio', 'none'),
    ('Cycle', 'distance', 'cardio', 'none'),
    ('Swim', 'distance', 'cardio', 'none'),
    ('Rowing machine', 'distance', 'cardio', 'machine'),
    ('Skipping', 'time', 'cardio', 'none'),
    ('Stretching', 'time', 'full', 'none'),
    ('Yoga', 'time', 'full', 'none'),
]


def seed(apps, schema_editor):
    Exercise = apps.get_model('wellness', 'Exercise')
    have = set(Exercise.objects.filter(user__isnull=True)
               .values_list('name', flat=True))
    Exercise.objects.bulk_create([
        Exercise(user=None, name=n, kind=k, muscle=m, equipment=e)
        for n, k, m, e in LIBRARY if n not in have])


def unseed(apps, schema_editor):
    Exercise = apps.get_model('wellness', 'Exercise')
    WorkoutSet = apps.get_model('wellness', 'WorkoutSet')
    RoutineItem = apps.get_model('wellness', 'RoutineItem')
    used = set(WorkoutSet.objects.values_list('exercise_id', flat=True)) | \
        set(RoutineItem.objects.values_list('exercise_id', flat=True))
    Exercise.objects.filter(user__isnull=True,
                            name__in=[x[0] for x in LIBRARY]) \
        .exclude(id__in=used).delete()


class Migration(migrations.Migration):
    dependencies = [('wellness', '0003_workouts')]
    operations = [migrations.RunPython(seed, unseed)]
