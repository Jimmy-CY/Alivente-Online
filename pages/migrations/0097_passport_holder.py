from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    """PH-1 - a nullable holder FK on Passport.

    ADDITIVE AND REVERSIBLE. The column is added NULL on every existing
    row and nothing reads it: holder_name keeps the data and every view
    keeps using it. Deploys run migrations automatically, so this goes
    out with the push, which is exactly why it does nothing a rollback
    could not undo.

    NO DATA MIGRATION. Matching a holder_name to a household member is a
    judgement - PA-3 recorded that there is no safe automatic mapping for
    Angy - and a migration is the worst possible place to make one. That
    work is backfill_passport_holder, which is dry by default.
                                            [test_passport_holder.py]
    """

    dependencies = [
        ('pages', '0096_notification_type_password_reset'),
    ]

    operations = [
        migrations.AddField(
            model_name='passport',
            name='holder',
            field=models.ForeignKey(
                blank=True,
                help_text='The household member this document belongs to. '
                          'NULL until the backfill has matched it to '
                          'holder_name.',
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='passports',
                to='pages.householdmember',
            ),
        ),
    ]
