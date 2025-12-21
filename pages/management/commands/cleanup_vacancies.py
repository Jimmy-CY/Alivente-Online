from django.core.management.base import BaseCommand
from pages.models import props, VacancyPeriod
from datetime import datetime


class Command(BaseCommand):
    help = 'Cleanup duplicate and incorrect OPEN vacancy periods'

    def handle(self, *args, **options):
        """Remove duplicate and incorrect OPEN vacancy periods"""
        
        self.stdout.write("=" * 60)
        self.stdout.write(self.style.SUCCESS("VACANCY PERIOD CLEANUP"))
        self.stdout.write("=" * 60)
        
        total_deleted = 0
        
        for prop in props.objects.all():
            self.stdout.write(f"\nChecking: {prop.prop_name}")
            
            # Get all OPEN vacancies for this property
            open_vacancies = VacancyPeriod.objects.filter(
                prop=prop,
                status='OPEN'
            ).order_by('start_date')
            
            if open_vacancies.count() > 0:
                self.stdout.write(f"  Found {open_vacancies.count()} OPEN vacancy periods")
                
                # Check if property is truly vacant
                today = datetime.now().date()
                tenants = prop.tenant_set.all()
                
                is_currently_vacant = True
                for t in tenants:
                    if (t.tenant_lease_start_date and t.tenant_lease_end_date and
                        t.tenant_lease_start_date <= today <= t.tenant_lease_end_date):
                        is_currently_vacant = False
                        self.stdout.write(f"  Property has active lease: {t.tenant_name} ({t.tenant_lease_start_date} → {t.tenant_lease_end_date})")
                        break
                
                if not is_currently_vacant:
                    # Delete all OPEN vacancies - property is not vacant
                    count = open_vacancies.delete()[0]
                    self.stdout.write(self.style.ERROR(f"  ❌ Deleted {count} incorrect OPEN vacancies"))
                    total_deleted += count
                else:
                    # Keep only the most recent OPEN vacancy
                    if open_vacancies.count() > 1:
                        latest = open_vacancies.last()
                        to_delete = open_vacancies.exclude(pk=latest.pk)
                        count = to_delete.delete()[0]
                        self.stdout.write(self.style.WARNING(f"  ✂️ Deleted {count} duplicate OPEN vacancies (kept latest)"))
                        total_deleted += count
                    else:
                        self.stdout.write(self.style.SUCCESS(f"  ✅ Single OPEN vacancy is correct"))
        
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write(self.style.SUCCESS(f"TOTAL DELETED: {total_deleted} vacancy periods"))
        self.stdout.write("=" * 60)
        
        # Show summary by property
        self.stdout.write("\n=== FINAL VACANCY SUMMARY ===")
        for prop in props.objects.all():
            vacancies = VacancyPeriod.objects.filter(prop=prop)
            if vacancies.exists():
                self.stdout.write(f"\n{prop.prop_name}:")
                for v in vacancies.order_by('start_date'):
                    status_symbol = "🟢" if v.status == 'FILLED' else "🔴"
                    self.stdout.write(f"  {status_symbol} {v.status}: {v.start_date} → {v.end_date} ({v.days_vacant} days)")