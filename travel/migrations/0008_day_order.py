# TR-9, 16 Nov 2026 - the order you chose for a day of the itinerary.

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("travel", "0007_pass_marks"),
    ]

    operations = [
        migrations.CreateModel(
            name="DayOrder",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True,
                                        serialize=False, verbose_name="ID")),
                ("day", models.DateField()),
                ("keys", models.TextField(blank=True, default="")),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("trip", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="day_orders", to="travel.trip")),
                ("updated_by", models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name="+", to=settings.AUTH_USER_MODEL)),
            ],
            options={"unique_together": {("trip", "day")}},
        ),
    ]
