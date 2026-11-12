# WL-17, 12 Nov 2026 - Workouts: Sports and Dance, a starting weight, your
# own exercises edited, deleted or hidden.

from django.db import migrations, models

# (name, how counted, group, equipment) - added to the shared library.
MORE = [
    ('Dance', 'time', 'cardio', 'none'),
    ('Zumba', 'time', 'cardio', 'none'),
    ('Spin class', 'time', 'cardio', 'machine'),
    ('Hiking', 'distance', 'cardio', 'none'),
    ('Elliptical', 'time', 'cardio', 'machine'),
    ('Stair climber', 'time', 'cardio', 'machine'),
    ('Padel', 'time', 'sport', 'ball'),
    ('Tennis', 'time', 'sport', 'ball'),
    ('Squash', 'time', 'sport', 'ball'),
    ('Badminton', 'time', 'sport', 'ball'),
    ('Table tennis', 'time', 'sport', 'ball'),
    ('Pickleball', 'time', 'sport', 'ball'),
    ('Netball', 'time', 'sport', 'ball'),
    ('Basketball', 'time', 'sport', 'ball'),
    ('Soccer', 'time', 'sport', 'ball'),
    ('Volleyball', 'time', 'sport', 'ball'),
    ('Golf', 'time', 'sport', 'ball'),
    ('Hockey', 'time', 'sport', 'ball'),
    ('Rugby', 'time', 'sport', 'ball'),
    ('Cricket', 'time', 'sport', 'ball'),
    ('Climbing', 'time', 'sport', 'none'),
    ('Martial arts', 'time', 'sport', 'none'),
]


def seed(apps, schema_editor):
    Exercise = apps.get_model('wellness', 'Exercise')
    have = set(Exercise.objects.filter(user__isnull=True)
               .values_list('name', flat=True))
    Exercise.objects.bulk_create([
        Exercise(user=None, name=n, kind=k, muscle=m, equipment=e)
        for n, k, m, e in MORE if n not in have])


def unseed(apps, schema_editor):
    Exercise = apps.get_model('wellness', 'Exercise')
    WorkoutSet = apps.get_model('wellness', 'WorkoutSet')
    RoutineItem = apps.get_model('wellness', 'RoutineItem')
    used = set(WorkoutSet.objects.values_list('exercise_id', flat=True)) | \
        set(RoutineItem.objects.values_list('exercise_id', flat=True))
    Exercise.objects.filter(user__isnull=True,
                            name__in=[x[0] for x in MORE]) \
        .exclude(id__in=used).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("wellness", "0012_habit_pauses"),
    ]

    operations = [
        migrations.AlterField(
            model_name="exercise",
            name="muscle",
            field=models.CharField(choices=[
                ("chest", "Chest"), ("back", "Back"),
                ("shoulders", "Shoulders"), ("arms", "Arms"),
                ("legs", "Legs"), ("core", "Core"), ("full", "Full body"),
                ("cardio", "Cardio"), ("sport", "Sports")], max_length=10),
        ),
        migrations.AlterField(
            model_name="exercise",
            name="equipment",
            field=models.CharField(choices=[
                ("dumbbell", "Dumbbells"), ("barbell", "Barbell"),
                ("kettlebell", "Kettlebell"), ("bodyweight", "Bodyweight"),
                ("machine", "Machine or cable"), ("band", "Band"),
                ("ball", "Racket or ball"), ("none", "Nothing")],
                max_length=12),
        ),
        migrations.AddField(
            model_name="exercise",
            name="hidden_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="routineitem",
            name="weight",
            field=models.DecimalField(blank=True, decimal_places=2,
                                      max_digits=6, null=True),
        ),
        migrations.RunPython(seed, unseed),
    ]
