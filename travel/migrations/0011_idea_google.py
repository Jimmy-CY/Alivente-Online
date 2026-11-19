# RA03, 19 Nov 2026 - each suggestion checked on Google: where it is, how
# far from the centre, rating, price level, and why it is greyed out.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('travel', '0010_suggestions'),
    ]

    operations = [
        migrations.AddField(model_name='idea', name='checked',
                            field=models.BooleanField(default=False)),
        migrations.AddField(model_name='idea', name='gid',
                            field=models.CharField(blank=True, default='',
                                                   max_length=300)),
        migrations.AddField(model_name='idea', name='lat',
                            field=models.FloatField(blank=True, null=True)),
        migrations.AddField(model_name='idea', name='lng',
                            field=models.FloatField(blank=True, null=True)),
        migrations.AddField(model_name='idea', name='dist_km',
                            field=models.FloatField(blank=True, null=True)),
        migrations.AddField(model_name='idea', name='rating',
                            field=models.FloatField(blank=True, null=True)),
        migrations.AddField(model_name='idea', name='ratings',
                            field=models.PositiveIntegerField(blank=True,
                                                              null=True)),
        migrations.AddField(model_name='idea', name='price_level',
                            field=models.CharField(blank=True, default='',
                                                   max_length=8)),
        migrations.AddField(model_name='idea', name='flag',
                            field=models.CharField(
                                blank=True, default='', max_length=8,
                                choices=[('', 'Fine'),
                                         ('closed', 'Closed on your days'),
                                         ('far', 'Too far'),
                                         ('temp', 'Temporarily closed')])),
        migrations.AddField(model_name='idea', name='flag_text',
                            field=models.CharField(blank=True, default='',
                                                   max_length=160)),
    ]
