"""
refresh_tenant_active — set tenant.tenant_current from each lease's dates.

A lease whose term [start, end] covers today is marked Active ('Yes'); every
other lease is Inactive ('No'). With non-overlapping lease terms per property
this is unambiguous, so activation/deactivation happens automatically as dates
roll over. Safe to run repeatedly.

    python manage.py refresh_tenant_active            # apply
    python manage.py refresh_tenant_active --dry-run  # preview only, nothing saved

Uses .update() (not .save()), so it does NOT re-trigger validation on each row.
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from pages.models import tenant


class Command(BaseCommand):
    help = "Set tenant_current (Active/Inactive) from each lease's dates."

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run', action='store_true',
            help="Show what would change without saving anything.",
        )

    def handle(self, *args, **options):
        dry = options['dry_run']
        today = timezone.now().date()

        changed = []
        for t in tenant.objects.select_related('prop').all():
            covers = bool(
                t.tenant_lease_start_date and t.tenant_lease_end_date
                and t.tenant_lease_start_date <= today <= t.tenant_lease_end_date
            )
            desired = 'Yes' if covers else 'No'
            if (t.tenant_current or '') != desired:
                changed.append((t, t.tenant_current, desired))
                if not dry:
                    tenant.objects.filter(pk=t.pk).update(tenant_current=desired)

        if not changed:
            self.stdout.write(self.style.SUCCESS(
                "All tenant_current flags already match the lease dates — nothing to change."))
            return

        verb = "Would change" if dry else "Changed"
        self.stdout.write(self.style.WARNING(f"{verb} {len(changed)} tenant(s):"))
        for t, old, new in changed:
            prop_name = t.prop.prop_name if t.prop_id else '—'
            self.stdout.write(
                f"  {prop_name}: {t.tenant_name or 'Unnamed'} "
                f"({t.tenant_lease_start_date} - {t.tenant_lease_end_date})  "
                f"{old or 'None'} -> {new}")

        if dry:
            self.stdout.write(self.style.NOTICE(
                "Dry run — nothing saved. Re-run without --dry-run to apply."))
        else:
            self.stdout.write(self.style.SUCCESS("Done."))