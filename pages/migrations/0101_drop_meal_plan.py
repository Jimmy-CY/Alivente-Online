# -*- coding: utf-8 -*-
"""MX-1, 19 Oct 2026 - release 3, push 3. The old planner's tables go.

0100 wrote down what this migration would be, on 18 October:

    NO DATA MIGRATION, by decision on 18 Oct: the four meal plans on
    production are test data and are cleared rather than converted.
    The old tables are left in place, empty and unread, until 0101
    drops them in push 3 - which is the only irreversible step in
    this release and so goes last.

THE COUNT IS TAKEN BEFORE ANYTHING IS DROPPED, and printed. A
DeleteModel reverses into an empty CreateModel - it gives back the
shape and never the rows - so a record of how much was destroyed is
the only honest safety this migration can offer. It is written into
the deploy log, where it can be found afterwards by anybody asking
where their meal plans went.

CHILDREN FIRST. meal_plan_recipes points at meal_plan_days, which
points at meal_plans, and a parent dropped before its child leaves a
foreign key pointing at nothing.
"""
from django.db import migrations


def count_first(apps, schema_editor):
    """Say what is about to be destroyed, before destroying it."""
    for label in ('MealPlanRecipe', 'MealPlanDay', 'MealPlan'):
        try:
            model = apps.get_model('pages', label)
            n = model.objects.count()
        except Exception as e:                         # pragma: no cover
            print('  MX-1: %s could not be counted (%s)' % (label, e))
            continue
        print('  MX-1: dropping %s - %d row(s)' % (label, n))


def no_going_back(apps, schema_editor):
    """The reverse of a count is a count."""
    print('  MX-1: reversed. The tables come back EMPTY - a DeleteModel '
          'restores the shape and never the rows.')


class Migration(migrations.Migration):

    dependencies = [
        ('pages', '0100_meal_entry'),
    ]

    operations = [
        migrations.RunPython(count_first, no_going_back),
        migrations.DeleteModel(name='MealPlanRecipe'),
        migrations.DeleteModel(name='MealPlanDay'),
        migrations.DeleteModel(name='MealPlan'),
    ]
