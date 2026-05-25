"""
Phase 1 of the Personal-module multi-tenancy rollout.

Creates the Workspace model (tenancy boundary for Passports, Celebrations,
Recipes) and adds a nullable workspace ForeignKey to UserProfile.

After this migration runs:
  - The Workspace table exists but is empty.
  - All existing UserProfile rows have workspace = NULL.
  - The rest of the system is functionally unchanged — workspace doesn't
    enter the picture until tenanted models (passports, etc.) are migrated
    in Phase 3+ and views start filtering on it.

The Phase 2 data migration (next migration) will create the default
"Demetri's Household" workspace and assign existing users to it.
"""
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pages', '0065_split_personal_permissions'),
    ]

    operations = [
        migrations.CreateModel(
            name='Workspace',
            fields=[
                (
                    'id',
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name='ID',
                    ),
                ),
                (
                    'name',
                    models.CharField(
                        help_text='Display name for the workspace '
                                  '(e.g. "Demetri\'s Household").',
                        max_length=200,
                    ),
                ),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                (
                    'owner',
                    models.ForeignKey(
                        help_text="The user who can manage this workspace's "
                                  "settings. Superusers bypass this restriction.",
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name='owned_workspaces',
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                'verbose_name': 'Workspace',
                'verbose_name_plural': 'Workspaces',
                'db_table': 'workspaces',
                'ordering': ['name'],
            },
        ),
        migrations.AddField(
            model_name='userprofile',
            name='workspace',
            field=models.ForeignKey(
                blank=True,
                help_text='The workspace this user belongs to '
                          '(for Personal modules). Auto-created on first '
                          'access if not assigned explicitly.',
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='members',
                to='pages.workspace',
            ),
        ),
    ]