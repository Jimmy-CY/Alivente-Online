# -*- coding: utf-8 -*-
"""NL-1, 22 Oct 2026 - a generated name fits the column it is stored in.

Three AlterField, 100 -> 255. No data is touched and no file on the
volume is renamed. The four rows left permanently stale by the old
width are repaired by `manage.py convert_recipe_photos --rebuild
--write`, which is a command somebody runs on purpose rather than a
side effect of a deploy.
"""
from django.db import migrations, models

import pages.models


class Migration(migrations.Migration):

    dependencies = [
        ('pages', '0101_drop_meal_plan'),
    ]

    operations = [
        migrations.AlterField(
            model_name='recipe',
            name='recipe_image',
            field=models.ImageField(
                blank=True, max_length=255, null=True,
                upload_to=pages.models.recipe_image_upload_path),
        ),
        migrations.AlterField(
            model_name='recipe',
            name='recipe_image_display',
            field=models.ImageField(
                blank=True, editable=False, max_length=255, null=True,
                help_text='Derived JPEG of recipe_image. Rebuilt by '
                          'manage.py convert_recipe_photos --write.',
                upload_to=pages.models.recipe_display_upload_path),
        ),
        migrations.AlterField(
            model_name='recipeinstruction',
            name='step_image',
            field=models.ImageField(
                blank=True, max_length=255, null=True,
                upload_to=pages.models.instruction_image_upload_path),
        ),
    ]
