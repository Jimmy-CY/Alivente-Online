# RA31, 26 Nov 2026 - Secret Santa.

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('pages', '0121_activity_log'),
    ]

    operations = [
        migrations.CreateModel(
            name='SantaExchange',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('year', models.PositiveIntegerField()),
                ('title', models.CharField(max_length=120)),
                ('event_date', models.DateField(blank=True, null=True)),
                ('event_time', models.TimeField(blank=True, null=True)),
                ('place', models.CharField(blank=True, max_length=200)),
                ('budget', models.DecimalField(blank=True, decimal_places=2, max_digits=9, null=True)),
                ('rules', models.TextField(blank=True)),
                ('remind_week', models.BooleanField(default=True)),
                ('remind_day', models.BooleanField(default=True)),
                ('drawn_at', models.DateTimeField(blank=True, null=True)),
                ('revealed_at', models.DateTimeField(blank=True, null=True)),
                ('week_sent_at', models.DateTimeField(blank=True, null=True)),
                ('day_sent_at', models.DateTimeField(blank=True, null=True)),
                ('reveal_sent_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('owner', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='santa_exchanges', to=settings.AUTH_USER_MODEL)),
            ],
            options={'db_table': 'santa_exchanges', 'ordering': ['-year', '-id'], 'unique_together': {('owner', 'year')}},
        ),
        migrations.CreateModel(
            name='SantaPerson',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('first_name', models.CharField(max_length=80)),
                ('surname', models.CharField(blank=True, max_length=80)),
                ('nickname', models.CharField(blank=True, max_length=80)),
                ('email', models.EmailField(max_length=254)),
                ('emailed_at', models.DateTimeField(blank=True, null=True)),
                ('contact', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='pages.contact')),
                ('exchange', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='people', to='pages.santaexchange')),
            ],
            options={'db_table': 'santa_people', 'ordering': ['first_name', 'surname', 'id']},
        ),
        migrations.CreateModel(
            name='SantaExclusion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('exchange', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='exclusions', to='pages.santaexchange')),
                ('giver', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='+', to='pages.santaperson')),
                ('receiver', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='+', to='pages.santaperson')),
            ],
            options={'db_table': 'santa_exclusions', 'unique_together': {('giver', 'receiver')}},
        ),
        migrations.CreateModel(
            name='SantaPair',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('exchange', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='pairs', to='pages.santaexchange')),
                ('giver', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='pair', to='pages.santaperson')),
                ('receiver', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='+', to='pages.santaperson')),
            ],
            options={'db_table': 'santa_pairs'},
        ),
    ]
