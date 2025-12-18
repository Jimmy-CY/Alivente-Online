from django.core.management.base import BaseCommand
from pages.models import VacancyPeriod, props, tenant
from datetime import date

class Command(BaseCommand):
    help = 'Fix Spain - Eusebi Guell vacancy period'

    def handle(self, *args, **kwargs):
        self.stdout.write("=" * 60)
        self.stdout.write("Fixing Spain vacancy on PRODUCTION database...")
        self.stdout.write("=" * 60)
        
        try:
            spain = props.objects.get(prop_name='Spain - Eusebi Guell')
            self.stdout.write(self.style.SUCCESS(f"✓ Found property: {spain.prop_name}"))
        except props.DoesNotExist:
            self.stdout.write(self.style.ERROR("❌ Spain property not found"))
            return
        
        try:
            easywin = tenant.objects.get(prop=spain, tenant_name='Easywin Solutions SL')
            self.stdout.write(self.style.SUCCESS(f"✓ Found Easywin: ends {easywin.tenant_lease_end_date}"))
        except tenant.DoesNotExist:
            self.stdout.write(self.style.ERROR("❌ Easywin not found"))
            self.stdout.write("\nAll Spain tenants:")
            for t in tenant.objects.filter(prop=spain):
                self.stdout.write(f"  - {t.tenant_name}: {t.tenant_lease_start_date} to {t.tenant_lease_end_date}")
            return
            
        try:
            dmytro = tenant.objects.get(prop=spain, tenant_name='Dmytro Pozniakov')
            self.stdout.write(self.style.SUCCESS(f"✓ Found Dmytro: starts {dmytro.tenant_lease_start_date}"))
        except tenant.DoesNotExist:
            self.stdout.write(self.style.ERROR("❌ Dmytro not found"))
            return
        
        # Check if vacancy already exists
        existing = VacancyPeriod.objects.filter(
            prop=spain,
            start_date=date(2025, 9, 1)
        ).first()
        
        if existing:
            self.stdout.write(f"\n✓ Vacancy already exists: {existing.status}")
            if existing.status == 'ACTIVE':
                existing.end_date = dmytro.tenant_lease_start_date
                existing.next_lease = dmytro
                existing.save()
                self.stdout.write(self.style.SUCCESS(f"✓ Closed vacancy: {existing.days_vacant} days"))
            else:
                self.stdout.write(f"Vacancy already closed: {existing.days_vacant} days")
        else:
            # Create the missing vacancy
            vacancy = VacancyPeriod.objects.create(
                prop=spain,
                start_date=date(2025, 9, 1),
                end_date=date(2025, 9, 30),
                previous_lease=easywin,
                next_lease=dmytro,
                status='FILLED',
                reason='BETWEEN_TENANTS'
            )
            self.stdout.write(self.style.SUCCESS(f"✓ Created vacancy: {vacancy.days_vacant} days"))
        
        # Verify
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write("All vacancies for Spain:")
        for v in VacancyPeriod.objects.filter(prop=spain):
            self.stdout.write(f"  - {v.start_date} to {v.end_date}: {v.days_vacant} days ({v.status})")
        
        self.stdout.write("\n" + self.style.SUCCESS("✅ Done!"))
        self.stdout.write("=" * 60)