# -*- coding: utf-8 -*-
"""MN-1, 18 Oct 2026 - release 3, the calendar is the plan.

Three new tables and nothing else. MealEntry replaces the chain
MealPlan -> MealPlanDay -> MealPlanRecipe; Menu and MenuItem hold the
saved weeks that push 2 fills.

NO DATA MIGRATION, by decision on 18 Oct: the four meal plans on
production are test data and are cleared rather than converted. The old
tables are left in place, empty and unread, until 0101 drops them in
push 3 - which is the only irreversible step in this release and so
goes last.

NO WORKSPACE on MealEntry, also by decision: Recipe has no workspace
field, so a tenanted meal holding an untenanted recipe would be an
inconsistency rather than a boundary.
"""
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('pages', '0099_recipe_image_display'),
    ]

    operations = [
        migrations.CreateModel(
            name='Menu',
            fields=[
                ('menu_id', models.AutoField(primary_key=True,
                                             serialize=False)),
                ('name', models.CharField(max_length=120)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='menus', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'menus',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='MealEntry',
            fields=[
                ('meal_entry_id', models.AutoField(primary_key=True,
                                                   serialize=False)),
                ('date', models.DateField(db_index=True)),
                ('note', models.CharField(
                    blank=True, default='',
                    help_text='A planned night that is not a recipe - Eat out, Leftovers',
                    max_length=200)),
                ('servings', models.IntegerField(
                    default=4,
                    help_text='How many this meal is cooked for. Scales the shopping list.')),
                ('sort_order', models.IntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='meal_entries', to=settings.AUTH_USER_MODEL)),
                ('leftover_of', models.ForeignKey(
                    blank=True,
                    help_text='Set when this meal is the leftovers of an earlier one. It costs nothing on the shopping list.',
                    null=True,
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='leftovers', to='pages.mealentry')),
                ('recipe', models.ForeignKey(
                    blank=True,
                    help_text='The recipe planned for this date, or blank for a note',
                    null=True,
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='meal_entries', to='pages.recipe')),
            ],
            options={
                'verbose_name_plural': 'Meal entries',
                'db_table': 'meal_entries',
                'ordering': ['date', 'sort_order', 'meal_entry_id'],
            },
        ),
        migrations.CreateModel(
            name='MenuItem',
            fields=[
                ('menu_item_id', models.AutoField(primary_key=True,
                                                  serialize=False)),
                ('day_index', models.IntegerField(
                    default=0,
                    help_text='0 is the first day of the menu, not a weekday')),
                ('note', models.CharField(blank=True, default='',
                                          max_length=200)),
                ('servings', models.IntegerField(default=4)),
                ('sort_order', models.IntegerField(default=0)),
                ('menu', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='items', to='pages.menu')),
                ('recipe', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='menu_items', to='pages.recipe')),
            ],
            options={
                'db_table': 'menu_items',
                'ordering': ['day_index', 'sort_order', 'menu_item_id'],
            },
        ),
    ]
