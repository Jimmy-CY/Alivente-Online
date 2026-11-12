# RC-3, 12 Nov 2026 - "Cooked it": when someone made a recipe, how it
# turned out (1-5) and a note. Private to whoever cooked it.

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("pages", "0117_document_types_remind"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="RecipeCook",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True,
                                           serialize=False, verbose_name="ID")),
                ("cooked_on", models.DateField()),
                ("rating", models.PositiveSmallIntegerField(blank=True, null=True)),
                ("note", models.CharField(blank=True, max_length=200)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("recipe", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,
                                             related_name="cooks", to="pages.recipe")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,
                                           related_name="recipe_cooks",
                                           to=settings.AUTH_USER_MODEL)),
            ],
            options={"db_table": "recipe_cooks",
                     "ordering": ["-cooked_on", "-created_at"]},
        ),
    ]
