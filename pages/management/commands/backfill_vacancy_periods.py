from django.core.management.base import BaseCommand
from django.db import transaction
from pages.models import props, tenant, VacancyPeriod
from datetime import datetime, timedelta

class Command(BaseCommand):
    help = 'Backfill VacancyPeriod records for all historical leases'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be created without actually creating records',
        )
        parser.add_argument(
            '--property',
            type=int,
            help='Only process specific property ID',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        property_id = options.get('property')
        
        self.stdout.write(self.style.WARNING('=' * 80))
        self.stdout.write(self.style.WARNING('VACANCY PERIOD BACKFILL'))
        self.stdout.write(self.style.WARNING('=' * 80))
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No records will be created'))
        
        # Get properties to process
        if property_id:
            properties = props.objects.filter(prop_id=property_id, prop_status='Active')
            if not properties.exists():
                self.stdout.write(self.style.ERROR(f'Property {property_id} not found or not active'))
                return
        else:
            properties = props.objects.filter(prop_status='Active')
        
        total_created = 0
        total_skipped = 0
        
        for prop in properties:
            self.stdout.write('')
            self.stdout.write(self.style.SUCCESS(f'Processing: {prop.prop_name}'))
            self.stdout.write('-' * 80)
            
            # Get all tenants for this property, ordered by lease start date
            tenants = tenant.objects.filter(
                prop=prop  # ← Changed from tenant_prop_name to prop
            ).exclude(
                tenant_lease_start_date__isnull=True
            ).order_by('tenant_lease_start_date')

            if not tenants.exists():
                self.stdout.write(self.style.WARNING('  No tenants with lease dates found'))
                continue
            
            self.stdout.write(f'  Found {tenants.count()} tenant(s) with lease dates')
            
            # Process each consecutive pair of tenants to find vacancies
            tenants_list = list(tenants)
            
            for i in range(len(tenants_list)):
                current_tenant = tenants_list[i]
                
                # Check if this tenant has an end date
                if not current_tenant.tenant_lease_end_date:
                    self.stdout.write(f'  → {current_tenant.tenant_name}: Current tenant (no end date)')
                    continue
                
                # Look for the next tenant (if exists)
                next_tenant = tenants_list[i + 1] if i + 1 < len(tenants_list) else None
                
                if next_tenant:
                    # There's a next tenant - check for gap between leases
                    vacancy_start = current_tenant.tenant_lease_end_date + timedelta(days=1)
                    vacancy_end = next_tenant.tenant_lease_start_date - timedelta(days=1)
                    
                    # Only create vacancy if there's actually a gap
                    if vacancy_start <= vacancy_end:
                        days_vacant = (vacancy_end - vacancy_start).days + 1
                        
                        # Check if this vacancy period already exists
                        existing = VacancyPeriod.objects.filter(
                            prop=prop,
                            previous_lease=current_tenant,
                            next_lease=next_tenant
                        ).exists()
                        
                        if existing:
                            self.stdout.write(
                                self.style.WARNING(
                                    f'  ⊗ Vacancy already exists: {current_tenant.tenant_name} → '
                                    f'{next_tenant.tenant_name} ({days_vacant} days)'
                                )
                            )
                            total_skipped += 1
                        else:
                            if not dry_run:
                                VacancyPeriod.objects.create(
                                    prop=prop,
                                    previous_lease=current_tenant,
                                    next_lease=next_tenant,
                                    start_date=vacancy_start,
                                    end_date=vacancy_end,
                                    days_vacant=days_vacant,
                                    status='FILLED'
                                )
                            
                            self.stdout.write(
                                self.style.SUCCESS(
                                    f'  ✓ Created vacancy: {current_tenant.tenant_name} → '
                                    f'{next_tenant.tenant_name}'
                                )
                            )
                            self.stdout.write(
                                f'    Period: {vacancy_start.strftime("%Y-%m-%d")} to '
                                f'{vacancy_end.strftime("%Y-%m-%d")} ({days_vacant} days)'
                            )
                            total_created += 1
                    else:
                        # Leases overlap or are consecutive
                        self.stdout.write(
                            f'  → {current_tenant.tenant_name} → {next_tenant.tenant_name}: '
                            f'No vacancy (consecutive leases)'
                        )
                else:
                    # This is the last tenant - no next tenant
                    # Check if lease has ended and property is currently vacant
                    if current_tenant.tenant_lease_end_date < datetime.now().date():
                        # Property should be vacant now
                        vacancy_start = current_tenant.tenant_lease_end_date + timedelta(days=1)
                        days_vacant = (datetime.now().date() - vacancy_start).days + 1
                        
                        # Check if this current vacancy already exists
                        existing = VacancyPeriod.objects.filter(
                            prop=prop,
                            previous_lease=current_tenant,
                            next_lease__isnull=True,
                            status='OPEN'
                        ).exists()
                        
                        if existing:
                            self.stdout.write(
                                self.style.WARNING(
                                    f'  ⊗ Current vacancy already exists: After {current_tenant.tenant_name} '
                                    f'({days_vacant} days so far)'
                                )
                            )
                            total_skipped += 1
                        else:
                            if not dry_run:
                                VacancyPeriod.objects.create(
                                    prop=prop,
                                    previous_lease=current_tenant,
                                    next_lease=None,
                                    start_date=vacancy_start,
                                    end_date=None,
                                    days_vacant=days_vacant,
                                    status='OPEN'
                                )
                            
                            self.stdout.write(
                                self.style.SUCCESS(
                                    f'  ✓ Created OPEN vacancy: After {current_tenant.tenant_name}'
                                )
                            )
                            self.stdout.write(
                                f'    Started: {vacancy_start.strftime("%Y-%m-%d")} '
                                f'({days_vacant} days so far)'
                            )
                            total_created += 1
                    else:
                        self.stdout.write(
                            f'  → {current_tenant.tenant_name}: Lease still active or recently ended'
                        )
        
        # Summary
        self.stdout.write('')
        self.stdout.write(self.style.WARNING('=' * 80))
        self.stdout.write(self.style.WARNING('SUMMARY'))
        self.stdout.write(self.style.WARNING('=' * 80))
        
        if dry_run:
            self.stdout.write(self.style.SUCCESS(f'Would create: {total_created} vacancy period(s)'))
        else:
            self.stdout.write(self.style.SUCCESS(f'Created: {total_created} vacancy period(s)'))
        
        self.stdout.write(self.style.WARNING(f'Skipped (already exist): {total_skipped} vacancy period(s)'))
        
        if dry_run:
            self.stdout.write('')
            self.stdout.write(self.style.WARNING('Run without --dry-run to actually create the records'))