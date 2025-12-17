from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone
from .models import tenant, VacancyPeriod

@receiver(post_save, sender=tenant)
def handle_tenant_vacancy(sender, instance, created, **kwargs):
    """
    Automatically create/close vacancy periods when tenants are created or updated.
    
    Logic:
    - When a NEW tenant is created (lease starts): Close any active vacancy
    - When a tenant's lease ENDS (tenant_current changes to 'No'): Create new vacancy
    """
    
    if created:
        # NEW TENANT CREATED - Check if there's an active vacancy to close
        active_vacancy = VacancyPeriod.objects.filter(
            prop=instance.prop,
            status='ACTIVE',
            end_date__isnull=True
        ).first()
        
        if active_vacancy:
            # Close the vacancy period with the new tenant's start date
            active_vacancy.end_date = instance.tenant_lease_start_date
            active_vacancy.next_lease = instance
            active_vacancy.save()  # Will auto-update days_vacant and status
            
            print(f"✓ Closed vacancy for {instance.prop.prop_name} - Vacant for {active_vacancy.days_vacant} days")
    
    else:
        # EXISTING TENANT UPDATED
        # Check if tenant just became inactive (lease ended)
        if instance.tenant_current == 'No':
            # Check if we already created a vacancy for this tenant
            existing_vacancy = VacancyPeriod.objects.filter(
                prop=instance.prop,
                previous_lease=instance
            ).first()
            
            if not existing_vacancy and instance.tenant_lease_end_date:
                # Create new vacancy period
                vacancy = VacancyPeriod.objects.create(
                    prop=instance.prop,
                    start_date=instance.tenant_lease_end_date,
                    previous_lease=instance,
                    reason='BETWEEN_TENANTS',
                    status='ACTIVE'
                )
                
                print(f"✓ Created vacancy for {instance.prop.prop_name} starting {instance.tenant_lease_end_date}")


def sync_all_historical_vacancies():
    """
    ONE-TIME FUNCTION: Analyze all historical tenants and create vacancy periods.
    
    Run this once after implementing the VacancyPeriod model to populate historical data.
    
    Usage:
        python manage.py shell
        >>> from pages.signals import sync_all_historical_vacancies
        >>> sync_all_historical_vacancies()
    """
    from .models import props, tenant
    from datetime import timedelta
    
    print("Starting historical vacancy sync...")
    vacancies_created = 0
    
    # Process each property
    for property in props.objects.filter(prop_status='Active'):
        print(f"\nProcessing: {property.prop_name}")
        
        # Get all tenants for this property, ordered by lease start date
        property_tenants = tenant.objects.filter(
            prop=property
        ).order_by('tenant_lease_start_date')
        
        if not property_tenants.exists():
            print(f"  ⚠ No tenants found - skipping")
            continue
        
        # Check for gaps between consecutive tenants
        tenant_list = list(property_tenants)
        for i in range(len(tenant_list) - 1):
            current_tenant = tenant_list[i]
            next_tenant = tenant_list[i + 1]
            
            if not current_tenant.tenant_lease_end_date or not next_tenant.tenant_lease_start_date:
                continue
            
            # Calculate gap in days
            gap_days = (next_tenant.tenant_lease_start_date - current_tenant.tenant_lease_end_date).days
            
            if gap_days > 0:
                # There was a vacancy period - create it if it doesn't exist
                vacancy, created = VacancyPeriod.objects.get_or_create(
                    prop=property,
                    start_date=current_tenant.tenant_lease_end_date,
                    end_date=next_tenant.tenant_lease_start_date,
                    defaults={
                        'previous_lease': current_tenant,
                        'next_lease': next_tenant,
                        'reason': 'BETWEEN_TENANTS',
                        'status': 'FILLED'
                    }
                )
                
                if created:
                    print(f"  ✓ Created vacancy: {gap_days} days ({current_tenant.tenant_lease_end_date} to {next_tenant.tenant_lease_start_date})")
                    vacancies_created += 1
                else:
                    print(f"  - Vacancy already exists: {gap_days} days")
        
        # Check if the last tenant's lease has ended (current vacancy)
        last_tenant = tenant_list[-1]
        if (last_tenant.tenant_current == 'No' and 
            last_tenant.tenant_lease_end_date and 
            last_tenant.tenant_lease_end_date < timezone.now().date()):
            
            # Check if active vacancy already exists
            existing = VacancyPeriod.objects.filter(
                prop=property,
                previous_lease=last_tenant,
                status='ACTIVE'
            ).first()
            
            if not existing:
                vacancy = VacancyPeriod.objects.create(
                    prop=property,
                    start_date=last_tenant.tenant_lease_end_date,
                    previous_lease=last_tenant,
                    reason='BETWEEN_TENANTS',
                    status='ACTIVE'
                )
                days_vacant = (timezone.now().date() - last_tenant.tenant_lease_end_date).days
                print(f"  ✓ Created ACTIVE vacancy: {days_vacant} days (since {last_tenant.tenant_lease_end_date})")
                vacancies_created += 1
    
    print(f"\n{'='*60}")
    print(f"Sync complete! Created {vacancies_created} new vacancy periods.")
    print(f"{'='*60}")
    
    # Summary statistics
    total_vacancies = VacancyPeriod.objects.count()
    active_vacancies = VacancyPeriod.objects.filter(status='ACTIVE').count()
    filled_vacancies = VacancyPeriod.objects.filter(status='FILLED').count()
    
    print(f"\nVacancy Statistics:")
    print(f"  Total vacancy periods: {total_vacancies}")
    print(f"  Currently vacant: {active_vacancies}")
    print(f"  Filled vacancies: {filled_vacancies}")
    
    if active_vacancies > 0:
        print(f"\nCurrently Vacant Properties:")
        for vacancy in VacancyPeriod.objects.filter(status='ACTIVE'):
            print(f"  - {vacancy.prop.prop_name}: {vacancy.days_vacant} days (since {vacancy.start_date})")