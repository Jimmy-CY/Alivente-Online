# -*- coding: utf-8 -*-
"""PX-1, 13 Oct 2026 - the derived display copy.

Schema only. It adds a nullable column and converts nothing: the 324
photos already on the volume are the batch command's job, deliberately,
because a data migration that re-encodes 200 MB runs inside a deploy
where nobody is watching and nothing can be inspected first.
"""
from django.db import migrations, models

import pages.models


class Migration(migrations.Migration):

    dependencies = [
        ('pages', '0098_comment_length'),
    ]

    operations = [
        migrations.AddField(
            model_name='recipe',
            name='recipe_image_display',
            field=models.ImageField(
                blank=True,
                editable=False,
                null=True,
                help_text=('Derived JPEG of recipe_image. Rebuilt by '
                           'manage.py convert_recipe_photos --write.'),
                upload_to=pages.models.recipe_display_upload_path),
        ),
    ]
