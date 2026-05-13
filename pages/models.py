from django.db import models
from django.db import connections
from django.db.models import Min, Max, Sum
from django.contrib.auth.models import User
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.text import slugify
from django.utils import timezone
from decimal import Decimal
import os
from django.db.models.signals import post_save, post_delete, pre_delete
from django.dispatch import receiver
from dateutil.relativedelta import relativedelta

def project_document_upload_path(instance, filename):
    """Generate upload path for project documents"""
    # Get the file extension
    ext = filename.split('.')[-1]
    
    # Get project name and clean it
    project_name = slugify(instance.project.project_name or 'project')
    
    # Format the date as YYYYMMDD
    date_str = timezone.now().strftime('%Y%m%d')
    
    # Get the original filename without extension
    original_name = os.path.splitext(filename)[0]
    
    # Create the new filename
    new_filename = f"{project_name}-{date_str}-{original_name}.{ext}"
    
    # Return the full path
    return os.path.join('project_docs', new_filename)

class Project(models.Model):
    project_id = models.AutoField(primary_key=True)
    project_name = models.CharField(max_length=255, blank=True, null=True)
    prop = models.ForeignKey('props', on_delete=models.CASCADE)  # Changed to string reference
    project_start_date = models.DateField(blank=True, null=True)
    project_expected_completion_date = models.DateField(blank=True, null=True)
    project_actual_completion_date = models.DateField(blank=True, null=True)
    
    PROJECT_STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('In Progress', 'In Progress'),
        ('Completed', 'Completed'),
    ]
    project_status = models.CharField(
        max_length=20,
        choices=PROJECT_STATUS_CHOICES,
        default='Pending',
        blank=True,
        null=True
    )
    
    project_description = models.TextField(blank=True, null=True)
    project_name_greek = models.CharField(max_length=255, blank=True, null=True, help_text='Greek translation of project name')
    project_description_greek = models.TextField(blank=True, null=True, help_text='Greek translation of project description')
    project_total_budgeted_cost = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, default=0.00)
    project_total_actual_cost = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, default=0.00)
    project_created_date = models.DateTimeField(auto_now_add=True)
    project_updated_date = models.DateTimeField(auto_now=True)
    
    def clean(self):
        """Validate project dates"""
        if self.project_start_date and self.project_expected_completion_date:
            if self.project_expected_completion_date <= self.project_start_date:
                raise ValidationError("Expected completion date must be after start date")
        
        if self.project_status == 'Completed' and not self.project_actual_completion_date:
            raise ValidationError("Actual completion date is required when project status is Completed")
        
        if self.project_actual_completion_date and self.project_start_date:
            if self.project_actual_completion_date < self.project_start_date:
                raise ValidationError("Actual completion date cannot be before start date")
    
    def update_totals(self):
        """Update total budgeted and actual costs from main tasks"""
        main_tasks = self.projecttask_set.filter(parent_task__isnull=True)
        self.project_total_budgeted_cost = sum(task.get_calculated_budgeted_cost() for task in main_tasks)
        self.project_total_actual_cost = sum(task.get_calculated_actual_cost() for task in main_tasks)
        self.save()
    
    def get_calculated_status(self):
        """Calculate project status based on all main tasks - OPTIMIZED to use prefetched data"""
        # Use prefetched data instead of new query
        all_tasks = list(self.projecttask_set.all())
        main_tasks = [task for task in all_tasks if task.parent_task_id is None]
        
        if not main_tasks:
            return 'Pending'
        
        completed_count = 0
        in_progress_count = 0
        
        for task in main_tasks:
            task_status = task.get_calculated_status()
            if task_status == 'Completed':
                completed_count += 1
            elif task_status == 'In Progress':
                in_progress_count += 1
        
        total_tasks = len(main_tasks)
        
        if completed_count == total_tasks:
            return 'Completed'
        elif in_progress_count > 0 or completed_count > 0:
            return 'In Progress'
        else:
            return 'Pending'

    def get_calculated_start_date(self):
        """Get earliest start date from all main tasks - OPTIMIZED to use prefetched data"""
        # Use prefetched data instead of new query
        all_tasks = list(self.projecttask_set.all())
        main_tasks = [task for task in all_tasks if task.parent_task_id is None]
        
        earliest_dates = []
        
        for task in main_tasks:
            task_start = task.get_calculated_start_date()
            if task_start:
                earliest_dates.append(task_start)
        
        return min(earliest_dates) if earliest_dates else None

    def get_calculated_expected_completion(self):
        """Get latest expected completion from all main tasks - OPTIMIZED to use prefetched data"""
        # Use prefetched data instead of new query
        all_tasks = list(self.projecttask_set.all())
        main_tasks = [task for task in all_tasks if task.parent_task_id is None]
        
        latest_dates = []
        
        for task in main_tasks:
            task_completion = task.get_calculated_expected_completion()
            if task_completion:
                latest_dates.append(task_completion)
        
        return max(latest_dates) if latest_dates else None

    def get_calculated_actual_completion(self):
        """Get latest actual completion when all main tasks completed - OPTIMIZED to use prefetched data"""
        if self.get_calculated_status() == 'Completed':
            # Use prefetched data instead of new query
            all_tasks = list(self.projecttask_set.all())
            main_tasks = [task for task in all_tasks if task.parent_task_id is None]
            
            latest_dates = []
            
            for task in main_tasks:
                task_completion = task.get_calculated_actual_completion()
                if task_completion:
                    latest_dates.append(task_completion)
            
            return max(latest_dates) if latest_dates else None
        return None

    def get_calculated_budgeted_cost(self):
        """Calculate total budgeted cost from all main tasks - OPTIMIZED to use prefetched data"""
        # Use prefetched data instead of new query
        all_tasks = list(self.projecttask_set.all())
        main_tasks = [task for task in all_tasks if task.parent_task_id is None]
        
        return sum(task.get_calculated_budgeted_cost() for task in main_tasks)

    def get_calculated_actual_cost(self):
        """Calculate total actual cost from all main tasks - OPTIMIZED to use prefetched data"""
        # Use prefetched data instead of new query
        all_tasks = list(self.projecttask_set.all())
        main_tasks = [task for task in all_tasks if task.parent_task_id is None]
        
        return sum(task.get_calculated_actual_cost() for task in main_tasks)

    def get_progress_percentage(self):
        """Calculate project progress based on subtask completion using day-based calculation - OPTIMIZED to use prefetched data"""
        total_project_days = 0
        completed_project_days = 0
        
        # Use prefetched data instead of new query
        all_tasks = list(self.projecttask_set.all())
        main_tasks = [task for task in all_tasks if task.parent_task_id is None]
        
        for task in main_tasks:
            completed_days, total_days = task.get_completed_days()
            total_project_days += total_days
            completed_project_days += completed_days
        
        if total_project_days > 0:
            return round((completed_project_days / total_project_days) * 100, 1)
        return 0.0
    
    def get_total_main_tasks(self):
        """Get count of main tasks (not subtasks) - OPTIMIZED to use prefetched data"""
        all_tasks = list(self.projecttask_set.all())
        return len([task for task in all_tasks if task.parent_task_id is None])
    
    def get_completed_main_tasks(self):
        """Get count of completed main tasks - OPTIMIZED to use prefetched data"""
        all_tasks = list(self.projecttask_set.all())
        main_tasks = [task for task in all_tasks if task.parent_task_id is None]
        completed_count = 0
        
        for task in main_tasks:
            if task.get_calculated_status() == 'Completed':
                completed_count += 1
        
        return completed_count
    
    def get_total_subtasks(self):
        """Get count of all subtasks in the project - OPTIMIZED to use prefetched data"""
        all_tasks = list(self.projecttask_set.all())
        return len([task for task in all_tasks if task.parent_task_id is not None])
    
    def get_completed_subtasks(self):
        """Get count of completed subtasks in the project - OPTIMIZED to use prefetched data"""
        all_tasks = list(self.projecttask_set.all())
        subtasks = [task for task in all_tasks if task.parent_task_id is not None]
        return len([task for task in subtasks if task.task_status == 'Completed'])
    
    def update_project_from_tasks(self):
        """Update project fields based on calculated values from tasks"""
        self.project_status = self.get_calculated_status()
        self.project_start_date = self.get_calculated_start_date()
        self.project_expected_completion_date = self.get_calculated_expected_completion()
        self.project_actual_completion_date = self.get_calculated_actual_completion()
        self.project_total_budgeted_cost = self.get_calculated_budgeted_cost()
        self.project_total_actual_cost = self.get_calculated_actual_cost()
        # Don't call save() here to avoid recursion
    
    def save(self, *args, **kwargs):
        # Only run validation if not being called from update methods
        if not kwargs.pop('skip_validation', False):
            self.full_clean()
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.project_name or f"Project {self.project_id}"
    
    class Meta:
        db_table = "projects"
        verbose_name = "Project"
        verbose_name_plural = "Projects"
        ordering = ['-project_created_date']


class ProjectTask(models.Model):
    task_id = models.AutoField(primary_key=True)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    parent_task = models.ForeignKey('self', on_delete=models.CASCADE, blank=True, null=True, related_name='subtasks')
    task_name = models.CharField(max_length=255, blank=True, null=True)
    task_description = models.TextField(blank=True, null=True)  # longtext
    task_name_greek = models.CharField(max_length=255, blank=True, null=True, help_text='Greek translation of task name')
    task_description_greek = models.TextField(blank=True, null=True, help_text='Greek translation of task description')
    task_start_date = models.DateField(blank=True, null=True)
    task_expected_completion_date = models.DateField(blank=True, null=True)
    task_actual_completion_date = models.DateField(blank=True, null=True)
    
    TASK_STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('In Progress', 'In Progress'),
        ('Completed', 'Completed'),
    ]
    task_status = models.CharField(
        max_length=20,
        choices=TASK_STATUS_CHOICES,
        default='Pending',
        blank=True,
        null=True
    )
    
    TASK_PRIORITY_CHOICES = [
        ('Low', 'Low'),
        ('Medium', 'Medium'),
        ('High', 'High'),
        ('Critical', 'Critical'),
    ]
    task_priority = models.CharField(
        max_length=10,
        choices=TASK_PRIORITY_CHOICES,
        blank=True,
        null=True
    )
    
    task_budgeted_cost = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True, default=0.00)
    task_actual_cost = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True, default=0.00)
    task_assigned_to = models.CharField(max_length=255, blank=True, null=True)
    
    # NEW: Progress percentage field (only for subtasks)
    task_progress_percentage = models.IntegerField(
        default=0,
        blank=True,
        null=True,
        help_text="Progress percentage (0-100). Only used for subtasks."
    )
    
    task_created_date = models.DateTimeField(auto_now_add=True)
    task_updated_date = models.DateTimeField(auto_now=True)
    
    def clean(self):
        """Validate task dates and progress percentage"""
        from django.core.exceptions import ValidationError
        
        if self.task_start_date and self.task_expected_completion_date:
            if self.task_expected_completion_date <= self.task_start_date:
                raise ValidationError("Expected completion date must be after start date")
        
        if self.task_status == 'Completed' and not self.task_actual_completion_date:
            raise ValidationError("Actual completion date is required when task status is Completed")
        
        if self.task_actual_completion_date and self.task_start_date:
            if self.task_actual_completion_date < self.task_start_date:
                raise ValidationError("Actual completion date cannot be before start date")
        
        # NEW: Progress percentage validation
        if self.task_progress_percentage is not None:
            if self.task_progress_percentage < 0 or self.task_progress_percentage > 100:
                raise ValidationError("Progress percentage must be between 0 and 100")
            
            # Auto-set progress based on status for subtasks only
            if self.parent_task:  # This is a subtask
                if self.task_status == 'Pending':
                    self.task_progress_percentage = 0
                elif self.task_status == 'Completed':
                    self.task_progress_percentage = 100
                elif self.task_status == 'In Progress':
                    # Validate that In Progress has a value between 1-99
                    if self.task_progress_percentage == 0 or self.task_progress_percentage == 100:
                        if self.task_progress_percentage == 0:
                            self.task_progress_percentage = 1  # Set minimum for In Progress
                        elif self.task_progress_percentage == 100:
                            self.task_progress_percentage = 99  # Set maximum for In Progress
    
    def get_calculated_status(self):
        """Calculate task status based on subtasks if any - OPTIMIZED to use prefetched data"""
        # Use prefetched data instead of new query
        subtasks = list(self.subtasks.all())
        if not subtasks:
            return self.task_status or 'Pending'
        
        completed_count = 0
        in_progress_count = 0
        
        for subtask in subtasks:
            if subtask.task_status == 'Completed':
                completed_count += 1
            elif subtask.task_status == 'In Progress':
                in_progress_count += 1
        
        total_subtasks = len(subtasks)
        
        if completed_count == total_subtasks:
            return 'Completed'
        elif in_progress_count > 0 or completed_count > 0:
            return 'In Progress'
        else:
            return 'Pending'
    
    def get_calculated_start_date(self):
        """Get earliest start date from subtasks or own start date - OPTIMIZED to use prefetched data"""
        # Use prefetched data instead of new query
        subtasks = list(self.subtasks.all())
        if not subtasks:
            return self.task_start_date
        
        dates = [self.task_start_date] if self.task_start_date else []
        for subtask in subtasks:
            if subtask.task_start_date:
                dates.append(subtask.task_start_date)
        
        return min(dates) if dates else None
    
    def get_calculated_expected_completion(self):
        """Get latest expected completion from subtasks or own date - OPTIMIZED to use prefetched data"""
        # Use prefetched data instead of new query
        subtasks = list(self.subtasks.all())
        if not subtasks:
            return self.task_expected_completion_date
        
        dates = [self.task_expected_completion_date] if self.task_expected_completion_date else []
        for subtask in subtasks:
            if subtask.task_expected_completion_date:
                dates.append(subtask.task_expected_completion_date)
        
        return max(dates) if dates else None
    
    def get_calculated_actual_completion(self):
        """Get latest actual completion when all subtasks completed - OPTIMIZED to use prefetched data"""
        if self.get_calculated_status() == 'Completed':
            # Use prefetched data instead of new query
            subtasks = list(self.subtasks.all())
            if not subtasks:
                return self.task_actual_completion_date
            
            dates = [self.task_actual_completion_date] if self.task_actual_completion_date else []
            for subtask in subtasks:
                if subtask.task_actual_completion_date:
                    dates.append(subtask.task_actual_completion_date)
            
            return max(dates) if dates else None
        return None
    
    def get_calculated_budgeted_cost(self):
        """Calculate total budgeted cost including subtasks - OPTIMIZED to use prefetched data"""
        # Use prefetched data instead of new query
        subtasks = list(self.subtasks.all())
        
        # If this task has subtasks, only count subtask costs (not the main task cost)
        if subtasks:
            total = Decimal('0.00')
            for subtask in subtasks:
                total += subtask.task_budgeted_cost or Decimal('0.00')
            return total
        
        # If no subtasks, return own cost
        return self.task_budgeted_cost or Decimal('0.00')

    def get_calculated_actual_cost(self):
        """Calculate total actual cost including subtasks - OPTIMIZED to use prefetched data"""
        # Use prefetched data instead of new query
        subtasks = list(self.subtasks.all())
        
        # If this task has subtasks, only count subtask costs (not the main task cost)
        if subtasks:
            total = Decimal('0.00')
            for subtask in subtasks:
                total += subtask.task_actual_cost or Decimal('0.00')
            return total
        
        # If no subtasks, return own cost
        return self.task_actual_cost or Decimal('0.00')
    
    def get_completed_days(self):
        """Calculate completed and total days for progress calculation - OPTIMIZED to use prefetched data"""
        # If this is a main task with subtasks, calculate based on subtasks
        subtasks = list(self.subtasks.all())
        if subtasks:
            total_subtask_days = 0
            completed_subtask_days = 0
            
            for subtask in subtasks:
                completed_days, total_days = subtask.get_completed_days()
                total_subtask_days += total_days
                completed_subtask_days += completed_days
            
            return completed_subtask_days, total_subtask_days
        
        # For subtasks or main tasks without subtasks, calculate based on own dates and progress percentage
        if not self.task_start_date or not self.task_expected_completion_date:
            return 0, 0
        
        total_days = (self.task_expected_completion_date - self.task_start_date).days + 1
        
        # For subtasks, use the progress percentage to calculate completed days
        if self.parent_task:  # This is a subtask
            progress_percentage = self.task_progress_percentage or 0
            completed_days = round((progress_percentage / 100.0) * total_days)
            return completed_days, total_days
        else:
            # For main tasks without subtasks, use simple status-based logic
            if self.task_status == 'Completed':
                return total_days, total_days
            elif self.task_status == 'In Progress':
                from django.utils import timezone
                today = timezone.now().date()
                if today >= self.task_start_date:
                    completed_days = min((today - self.task_start_date).days + 1, total_days)
                    return completed_days, total_days
            
            # For 'Pending', 'Not Started', 'On Hold', etc.
            return 0, total_days
    
    def get_completed_subtask_count(self):
        """Get count of completed subtasks - OPTIMIZED to use prefetched data"""
        subtasks = list(self.subtasks.all())
        return len([subtask for subtask in subtasks if subtask.task_status == 'Completed'])

    def get_subtask_count(self):
        """Get total count of subtasks - OPTIMIZED to use prefetched data"""
        subtasks = list(self.subtasks.all())
        return len(subtasks)

    def get_subtask_progress(self):
        """Get progress percentage for main tasks based on subtask day-based calculation - OPTIMIZED to use prefetched data"""
        # Use prefetched data instead of new query
        subtasks = list(self.subtasks.all())
        if not subtasks:
            # For tasks without subtasks, use simple completion logic
            if self.task_status == 'Completed':
                return 100.0
            elif self.task_status == 'In Progress':
                return 50.0  # Default for in progress tasks without subtasks
            else:
                return 0.0
        
        # Use the same day-based calculation as projects
        total_task_days = 0
        completed_task_days = 0
        
        for subtask in subtasks:
            completed_days, total_days = subtask.get_completed_days()
            total_task_days += total_days
            completed_task_days += completed_days
        
        if total_task_days > 0:
            return round((completed_task_days / total_task_days) * 100, 1)
        return 0.0
    
    def get_progress_for_gantt(self):
        """Get progress value for Gantt chart (0.0 to 1.0) - uses day-based calculation for consistency"""
        if self.parent_task:  # This is a subtask
            return (self.task_progress_percentage or 0) / 100.0
        else:  # This is a main task - use day-based calculation like projects
            return self.get_subtask_progress() / 100.0
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.task_name or f"Task {self.task_id}"
    
    class Meta:
        db_table = "project_tasks"  # Update this to match your actual table name if different
        verbose_name = "Project Task"
        verbose_name_plural = "Project Tasks"
        ordering = ['task_start_date', 'task_name']

class ProjectDocument(models.Model):
    document_id = models.AutoField(primary_key=True)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='project_documents')
    task = models.ForeignKey('ProjectTask', on_delete=models.CASCADE, blank=True, null=True, related_name='task_documents')  # Changed to string reference
    document_name = models.CharField(max_length=255, blank=True, null=True)
    document_description = models.TextField(blank=True, null=True)
    document_file = models.FileField(upload_to=project_document_upload_path, blank=True, null=True)
    document_uploaded_date = models.DateTimeField(auto_now_add=True)
    document_uploaded_by = models.CharField(max_length=255, blank=True, null=True)
    
    def __str__(self):
        return self.document_name or f"Document {self.document_id}"
    
    class Meta:
        db_table = "project_documents"
        verbose_name = "Project Document"
        verbose_name_plural = "Project Documents"
        ordering = ['-document_uploaded_date']

def expense_document_upload_path(instance, filename):
    """
    Generate custom upload path for expense documents
    Format: expense_docs/PropertyName-YYYYMMDD-OriginalFileName.ext
    """
    # Get the file extension
    ext = filename.split('.')[-1]

    # Get property name and clean it (remove spaces, special chars)
    property_name = slugify(instance.prop.prop_name)

    # Format the date as YYYYMMDD
    date_str = instance.act_expense_date.strftime('%Y%m%d')

    # Get the original filename without extension
    original_name = os.path.splitext(filename)[0]

    # Create the new filename
    new_filename = f"{property_name}-{date_str}-{original_name}.{ext}"

    # Return the full path
    return os.path.join('expense_docs', new_filename)

def title_deed_upload_path(instance, filename):
    """Generate upload path for title deeds"""
    # Sanitize the property name
    prop_name_slug = slugify(instance.prop_name or 'property')
    
    # Get file extension
    ext = os.path.splitext(filename)[1].lower()
    
    # Generate filename
    filename = f"prop_{instance.prop_id}_{prop_name_slug[:50]}_title_deed{ext}"
    
    # Return full path
    return os.path.join('properties', 'title_deeds', filename)

def lease_agreement_upload_path(instance, filename):
    """Generate upload path for lease agreements"""
    # Sanitize the tenant name
    tenant_name_slug = slugify(instance.tenant_name or 'tenant')
    
    # Get file extension
    ext = os.path.splitext(filename)[1].lower()
    
    # Generate filename
    filename = f"tenant_{instance.tenant_id}_{tenant_name_slug[:50]}_lease_agreement{ext}"
    
    # Return full path
    return os.path.join('tenants', 'lease_agreements', filename)

##### Create your models here ###############
class props(models.Model):
    prop_id = models.AutoField(primary_key=True)
    prop_name = models.CharField(max_length=255, blank=True, null=True)
    prop_address1 = models.CharField(max_length=255, blank=True, null=True)
    prop_address2 = models.CharField(max_length=255, blank=True, null=True)
    prop_suburb = models.CharField(max_length=255, blank=True, null=True)
    prop_city = models.CharField(max_length=255, blank=True, null=True)
    prop_province = models.CharField(max_length=255, blank=True, null=True)
    prop_country = models.CharField(max_length=255, blank=True, null=True)
    prop_pcode = models.CharField(max_length=255, blank=True, null=True)
    prop_latitude = models.DecimalField(max_digits=10, decimal_places=8, blank=True, null=True)
    prop_longitude = models.DecimalField(max_digits=11, decimal_places=8, blank=True, null=True)
    prop_floor_area = models.IntegerField(blank=True, null=True)
    prop_year_built = models.IntegerField(blank=True, null=True)
    prop_status = models.CharField(max_length=255, blank=True, null=True)
    prop_available_for_rent = models.CharField(max_length=255, blank=True, null=True)
    prop_title_deed = models.FileField(upload_to=title_deed_upload_path, blank=True, null=True)
    prop_title_deed_status = models.CharField(max_length=255, blank=True, null=True)
    prop_electricity = models.CharField(max_length=255, blank=True, null=True)
    prop_water = models.CharField(max_length=255, blank=True, null=True)
    prop_refuse = models.CharField(max_length=255, blank=True, null=True)
    prop_property_tax = models.CharField(max_length=255, blank=True, null=True)
    prop_sewerage = models.CharField(max_length=255, blank=True, null=True)
    prop_insurance = models.CharField(max_length=255, blank=True, null=True)
    prop_include_in_occupancy = models.BooleanField(
        default=True,
        verbose_name="Include in Occupancy Metrics",
        help_text="Uncheck to exclude this property from occupancy rate and days-to-fill calculations (e.g., for seasonal rentals)"
    )

    def __str__(self):
        return self.prop_name or f"Property {self.prop_id}"

    class Meta:
        db_table = "prop"
        verbose_name = "Property"
        verbose_name_plural = "Properties"

class petty(models.Model):
    petty_cash_id = models.AutoField(primary_key=True)
    petty_cash_date = models.DateField(blank=True, null=True)
    petty_cash_description = models.CharField(max_length=55, blank=True, null=True)
    petty_cash_amount = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True)
    petty_cash_dr_cr = models.CharField(max_length=2, blank=True, null=True)

    def __str__(self):
        return self.petty_cash_description

    class Meta:
        db_table="petty_cash"

class tenant(models.Model):
    tenant_id = models.AutoField(primary_key=True)
    prop = models.ForeignKey(props, on_delete=models.CASCADE)
    tenant_type = models.CharField(max_length=255, blank=True, null=True)
    tenant_name = models.CharField(max_length=255, blank=True, null=True)
    tenant_contact_person = models.CharField(max_length=255, blank=True, null=True)
    tenant_contact_number = models.CharField(max_length=255, blank=True, null=True)
    tenant_email = models.CharField(max_length=255, blank=True, null=True)
    tenant_deposit = models.IntegerField(blank=True, null=True)
    tenant_lease_start_date = models.DateField(blank=True, null=True)
    tenant_lease_end_date = models.DateField(blank=True, null=True)
    tenant_rental_type = models.CharField(max_length=255, blank=True, null=True)
    tenant_renewal = models.CharField(max_length=255, blank=True, null=True)
    tenant_renewal_period = models.IntegerField(blank=True, null=True)
    tenant_rent = models.IntegerField(blank=True, null=True)
    tenant_levies = models.IntegerField(blank=True, null=True)
    tenant_payment_terms = models.IntegerField(blank=True, null=True)
    tenant_current = models.CharField(max_length=255, blank=True, null=True)
    tenant_lease_agreement = models.FileField(
        upload_to=lease_agreement_upload_path, 
        blank=True, 
        null=True,
        verbose_name="Lease Agreement Document"
    )
    tenant_lease_agreement_status = models.CharField(
        max_length=255, 
        blank=True, 
        null=True,
        verbose_name="Lease Agreement Status"
    )
    RENEWAL_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('declined', 'Declined'),
        ('new_lease_signed', 'New Lease Signed'),
    ]
    tenant_renewal_status = models.CharField(
        max_length=20,
        choices=RENEWAL_STATUS_CHOICES,
        default='pending',
        blank=True,
        null=True,
        verbose_name="Renewal Status"
    )

    def clean(self):
        """Validate lease dates and check for ACTIVE tenant overlaps only"""
        if self.tenant_lease_start_date and self.tenant_lease_end_date:
            # Validate date order
            if self.tenant_lease_end_date <= self.tenant_lease_start_date:
                raise ValidationError("Lease end date must be after start date")
            
            # Only check for overlaps with ACTIVE tenants
            if hasattr(self, 'prop'):
                overlapping = tenant.objects.filter(
                    prop=self.prop,
                    tenant_current='Yes',  # KEY CHANGE - only active tenants
                    tenant_lease_start_date__lte=self.tenant_lease_end_date,
                    tenant_lease_end_date__gte=self.tenant_lease_start_date
                ).exclude(pk=self.pk)
                
                if overlapping.exists():
                    tenant_list = ", ".join([f"{t.tenant_name} ({'Active' if t.tenant_current == 'Yes' else 'Inactive'})" 
                                           for t in overlapping])
                    raise ValidationError(
                        f"Property already has active tenant(s) during this period: {tenant_list}"
                    )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.tenant_name if self.tenant_name else ""

    class Meta:
        db_table = "tenant"
        verbose_name = "Tenant"
        verbose_name_plural = "Tenants"

class supplier(models.Model):
    supplier_id = models.AutoField(primary_key=True)
    supplier_contact_person = models.CharField(max_length=255, blank=True, null=True)
    supplier_contact_number = models.CharField(max_length=255, blank=True, null=True)
    supplier_email = models.CharField(max_length=255, blank=True, null=True)
    supplier_company_name = models.CharField(max_length=255, blank=True, null=True)
    supplier_role = models.CharField(max_length=255, blank=True, null=True)
    supplier_country = models.CharField(max_length=255, blank=True, null=True)
    
    def __str__(self):
        return self.supplier_contact_person

    class Meta:
        db_table="supplier"

class invoices(models.Model):
    invoice_id = models.AutoField(primary_key=True)
    tenant = models.ForeignKey(tenant, on_delete=models.CASCADE)
    invoice_date = models.DateField(blank=True, null=True)
    invoice_paid = models.CharField(max_length=255, blank=True, null=True)
    
    class Meta:
        db_table="invoice"

class issues(models.Model):
    issues_id = models.AutoField(primary_key=True)
    prop = models.ForeignKey(props, on_delete=models.CASCADE)
    issues_heading = models.CharField(max_length=255, blank=True, null=True)
    issues_description = models.CharField(max_length=255, blank=True, null=True)
    issues_date_logged = models.DateField(blank=True, null=True)
    issues_status = models.CharField(max_length=255, blank=True, null=True)
    issues_resolution_date = models.DateField(blank=True, null=True, default=None)
    issues_resolving_user = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.issues_heading

    class Meta:
        db_table="issues"

class issues_details(models.Model):
    issues_details_id = models.AutoField(primary_key=True)
    issues = models.ForeignKey(issues, on_delete=models.CASCADE)
    issues_details_comment = models.CharField(max_length=255, blank=True, null=True)
    issues_details_user = models.CharField(max_length=255, blank=True, null=True)
    issues_details_date = models.DateField(blank=True, null=True)

    def __str__(self):
        return self.issues_details_comment

    class Meta:
        db_table="issues_details"

class prop_values(models.Model):
    prop_values_id = models.AutoField(primary_key=True)
    prop = models.ForeignKey(props, on_delete=models.CASCADE)
    prop_values_purchase_price = models.IntegerField(blank=True, null=True)
    prop_values_current_value = models.IntegerField(blank=True, null=True)

    def __str__(self):
        return str(self.prop_values_purchase_price)

    class Meta:
        db_table="prop_values"

class revenue_types(models.Model):
    revenue_types_id = models.AutoField(primary_key=True)
    revenue_types_name = models.CharField(max_length=255, blank=True, null=True)
    revenue_types_jan = models.CharField(max_length=3, blank=True, null=True)
    revenue_types_feb = models.CharField(max_length=3, blank=True, null=True)
    revenue_types_mar = models.CharField(max_length=3, blank=True, null=True)
    revenue_types_apr = models.CharField(max_length=3, blank=True, null=True)
    revenue_types_may = models.CharField(max_length=3, blank=True, null=True)
    revenue_types_jun = models.CharField(max_length=3, blank=True, null=True)
    revenue_types_jul = models.CharField(max_length=3, blank=True, null=True)
    revenue_types_aug = models.CharField(max_length=3, blank=True, null=True)
    revenue_types_sep = models.CharField(max_length=3, blank=True, null=True)
    revenue_types_oct = models.CharField(max_length=3, blank=True, null=True)
    revenue_types_nov = models.CharField(max_length=3, blank=True, null=True)
    revenue_types_dec = models.CharField(max_length=3, blank=True, null=True)

    def __str__(self):
        return str(self.revenue_types_name)

    class Meta:
        db_table="revenue_types"

class revenue_line_types(models.Model):
    revenue_line_types_id = models.AutoField(primary_key=True)
    revenue_line_types_name = models.CharField(max_length=255, blank=True, null=True)
    revenue_line_types_description = models.CharField(max_length=255, blank=True, null=True)
    
    def __str__(self):
        return str(self.revenue_line_types_name)

    class Meta:
        db_table="revenue_line_types"

class revenue(models.Model):
    revenue_id = models.AutoField(primary_key=True)
    revenue_types = models.ForeignKey(revenue_types, on_delete=models.CASCADE)
    prop = models.ForeignKey(props, on_delete=models.CASCADE)
    revenue_line_types = models.ForeignKey(revenue_line_types, on_delete=models.CASCADE)
    revenue_amount = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True)
    revenue_jan = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True)
    revenue_feb = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True)
    revenue_mar = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True)
    revenue_apr = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True)
    revenue_may = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True)
    revenue_jun = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True)
    revenue_jul = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True)
    revenue_aug = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True)
    revenue_sep = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True)
    revenue_oct = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True)
    revenue_nov = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True)
    revenue_dec = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True)

    def __str__(self):
        return str(self.revenue_id)

    class Meta:
        db_table="revenue"

class expense_types(models.Model):
    expense_types_id = models.AutoField(primary_key=True)
    expense_types_name = models.CharField(max_length=255, blank=True, null=True)
    expense_types_jan = models.CharField(max_length=3, blank=True, null=True)
    expense_types_feb = models.CharField(max_length=3, blank=True, null=True)
    expense_types_mar = models.CharField(max_length=3, blank=True, null=True)
    expense_types_apr = models.CharField(max_length=3, blank=True, null=True)
    expense_types_may = models.CharField(max_length=3, blank=True, null=True)
    expense_types_jun = models.CharField(max_length=3, blank=True, null=True)
    expense_types_jul = models.CharField(max_length=3, blank=True, null=True)
    expense_types_aug = models.CharField(max_length=3, blank=True, null=True)
    expense_types_sep = models.CharField(max_length=3, blank=True, null=True)
    expense_types_oct = models.CharField(max_length=3, blank=True, null=True)
    expense_types_nov = models.CharField(max_length=3, blank=True, null=True)
    expense_types_dec = models.CharField(max_length=3, blank=True, null=True)

    def __str__(self):
        return str(self.expense_types_name)

    class Meta:
        db_table="expense_types"

class expense_line_types(models.Model):
    expense_line_types_id = models.AutoField(primary_key=True)
    expense_line_types_name = models.CharField(max_length=255, blank=True, null=True)
    expense_line_types_description = models.CharField(max_length=255, blank=True, null=True)
    expense_line_types_prorata = models.CharField(max_length=3, blank=True, null=True)
    expense_line_types_pr_amount = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True)

    def __str__(self):
        return str(self.expense_line_types_name)

    class Meta:
        db_table="expense_line_types"

class expense(models.Model):
    expense_id = models.AutoField(primary_key=True)
    expense_types = models.ForeignKey(expense_types, on_delete=models.CASCADE)
    expense_line_types = models.ForeignKey(expense_line_types, on_delete=models.CASCADE)
    expense_amount = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True)
    prop = models.ForeignKey(props, on_delete=models.CASCADE)
    expense_jan = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True)
    expense_feb = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True)
    expense_mar = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True)
    expense_apr = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True)
    expense_may = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True)
    expense_jun = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True)
    expense_jul = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True)
    expense_aug = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True)
    expense_sep = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True)
    expense_oct = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True)
    expense_nov = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True)
    expense_dec = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True)

    def __str__(self):
        return str(self.expense_id)

    class Meta:
        db_table="expense"

class act_expense(models.Model):
    act_expense_id = models.AutoField(primary_key=True)
    act_expense_date = models.DateField(blank=True, null=True)
    prop = models.ForeignKey(props, on_delete=models.CASCADE)
    act_expense_description = models.CharField(max_length=55, blank=True, null=True)
    act_expense_amount = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True)
    act_expense_approved = models.CharField(max_length=3, blank=True, null=True)
    act_expense_paid = models.CharField(max_length=3, blank=True, null=True)
    act_expense_document = models.FileField(upload_to=expense_document_upload_path, blank=True, null=True)

    def __str__(self):
        return self.act_expense_description
    def approved_display(self):
        return "Yes" if self.act_expense_approved == 'Yes' else "No"
    def paid_display(self):
        return "Yes" if self.act_expense_paid == 'Yes' else "No"

    class Meta:
        db_table="act_expense"

class VacancyPeriod(models.Model):
    """
    Tracks vacancy periods for properties between leases.
    
    Purpose:
    - Automatically tracks when properties are vacant
    - Links to the leases before/after the vacancy
    - Calculates occupancy rates and time-to-fill metrics
    - Distinguishes between different types of vacancies (tenant turnover vs renovation)
    
    Auto-population:
    - Created automatically when a lease ends
    - Closed automatically when a new lease starts
    - Can also be manually created for renovations, etc.
    """
    
    # ==================== CORE FIELDS ====================
    
    prop = models.ForeignKey(
        'props',
        on_delete=models.CASCADE,
        related_name='vacancy_periods',
        help_text='The property that is vacant'
    )
    
    start_date = models.DateField(
        help_text='Date the vacancy period began (usually previous lease end date)'
    )
    
    end_date = models.DateField(
        null=True,
        blank=True,
        help_text='Date the vacancy ended (usually next lease start date). NULL = currently vacant'
    )
    
    days_vacant = models.IntegerField(
        default=0,
        help_text='Number of days vacant. Auto-calculated on save.'
    )
    
    # ==================== STATUS TRACKING ====================
    
    STATUS_CHOICES = [
        ('ACTIVE', 'Currently Vacant'),
        ('FILLED', 'Filled'),
        ('EXCLUDED', 'Excluded from Analysis'),
    ]
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='ACTIVE',
        help_text='Current status of this vacancy period'
    )
    
    # ==================== REASON CATEGORIZATION ====================
    
    REASON_CHOICES = [
        ('BETWEEN_TENANTS', 'Between Tenants'),
        ('RENOVATION', 'Renovation/Repairs'),
        ('SEASONAL', 'Seasonal (Not Marketing)'),
        ('FIRST_LISTING', 'Initial Property Listing'),
        ('OWNER_USE', 'Owner/Personal Use'),
        ('OTHER', 'Other'),
    ]
    
    reason = models.CharField(
        max_length=50,
        choices=REASON_CHOICES,
        default='BETWEEN_TENANTS',
        help_text='Why is/was this property vacant?'
    )
    
    # ==================== LEASE LINKAGE ====================
    
    previous_lease = models.ForeignKey(
        'tenant',  # CHANGED from 'leases' to 'tenant'
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='vacancy_after',
        help_text='The lease that ended before this vacancy'
    )
    
    next_lease = models.ForeignKey(
        'tenant',  # CHANGED from 'leases' to 'tenant'
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='vacancy_before',
        help_text='The lease that started after this vacancy'
    )
    
    # ==================== ADDITIONAL INFO ====================
    
    notes = models.TextField(
        blank=True,
        help_text='Additional notes about this vacancy period'
    )
    
    # ==================== METADATA ====================
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text='When this record was created'
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text='When this record was last updated'
    )
    
    # ==================== META OPTIONS ====================
    
    class Meta:
        ordering = ['-start_date']
        verbose_name = 'Vacancy Period'
        verbose_name_plural = 'Vacancy Periods'
        indexes = [
            models.Index(fields=['prop', 'status']),
            models.Index(fields=['start_date', 'end_date']),
            models.Index(fields=['status', 'reason']),
        ]
    
    # ==================== METHODS ====================
    
    def save(self, *args, **kwargs):
        """
        Auto-calculate days_vacant and update status when saving
        """
        if self.end_date:
            # Vacancy has ended - calculate total days (INCLUSIVE)
            self.days_vacant = (self.end_date - self.start_date).days + 1
            
            # If it was ACTIVE, mark it as FILLED
            if self.status == 'ACTIVE':
                self.status = 'FILLED'
        else:
            # Still vacant - calculate days so far (INCLUSIVE)
            if self.status == 'ACTIVE':
                today = timezone.now().date()
                self.days_vacant = (today - self.start_date).days + 1
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        """
        Human-readable representation
        """
        if self.end_date:
            return f"{self.prop.prop_name} - Vacant {self.days_vacant} days ({self.start_date} to {self.end_date})"
        else:
            return f"{self.prop.prop_name} - Currently vacant for {self.days_vacant} days (since {self.start_date})"
    
    @property
    def is_active(self):
        """
        Helper property to check if vacancy is currently active
        """
        return self.status == 'ACTIVE' and self.end_date is None
    
    @property
    def should_count_in_metrics(self):
        """
        Helper property to determine if this vacancy should be counted in performance metrics
        Only count 'BETWEEN_TENANTS' and 'FIRST_LISTING' reasons
        """
        return self.reason in ['BETWEEN_TENANTS', 'FIRST_LISTING']

class Passport(models.Model):
    DOCUMENT_TYPE_CHOICES = [
        ('passport', 'Passport'),
        ('id', 'ID'),
        ('drivers_license', 'Driver\'s License'),
        ('visa', 'Visa'),
        ('arc', 'Alien Registration Card'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('renewal', 'Applied for Renewal'),
        ('inactive', 'Inactive'),
    ]
    
    holder_name = models.CharField(max_length=200)
    document_type = models.CharField(max_length=20, choices=DOCUMENT_TYPE_CHOICES)
    document_number = models.CharField(max_length=50)
    country_of_issue = models.CharField(max_length=100)
    date_of_issue = models.DateField(null=True, blank=True)  # ADD null=True, blank=True
    expiry_date = models.DateField(null=True, blank=True)  # ADD null=True, blank=True
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    document_file = models.FileField(upload_to='passports/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.holder_name} - {self.get_document_type_display()}"
    
    class Meta:
        db_table = "passports"
        verbose_name = "Passport/ID Document"
        verbose_name_plural = "Passport/ID Documents"


##### RECIPE KEEPER MODELS #####

class MeasurementUnit(models.Model):
    """Units of measurement for recipe ingredients"""
    UNIT_TYPE_CHOICES = [
        ('volume', 'Volume'),
        ('weight', 'Weight'),
        ('count', 'Count'),
        ('other', 'Other'),
    ]
    
    measurement_unit_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50, help_text='Singular name (e.g., teaspoon, cup, gram)')
    name_plural = models.CharField(max_length=50, blank=True, help_text='Plural name (e.g., teaspoons, cups, grams)')
    abbreviation = models.CharField(max_length=10, blank=True, null=True, help_text='Singular short form (e.g., tsp, cup, g)')
    abbreviation_plural = models.CharField(max_length=10, blank=True, null=True, help_text='Plural short form (e.g., tsp, cups, g)')
    unit_type = models.CharField(max_length=20, choices=UNIT_TYPE_CHOICES, default='other')
    created_date = models.DateTimeField(auto_now_add=True)
    
    def get_display_name(self, amount=1):
        """Return the appropriate unit display based on amount"""
        # Use abbreviation if available, otherwise use name
        if amount == 1 or amount == -1:  # -1 for "to taste" type units
            return self.abbreviation or self.name
        else:
            return self.abbreviation_plural or self.abbreviation or self.name_plural or self.name
    
    def __str__(self):
        return f"{self.name} ({self.abbreviation})" if self.abbreviation else self.name
    
    class Meta:
        db_table = "measurement_units"
        verbose_name = "Measurement Unit"
        verbose_name_plural = "Measurement Units"
        ordering = ['unit_type', 'name']

class IngredientCategory(models.Model):
    """Categories for organizing ingredients"""
    ingredient_category_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100, unique=True, help_text='e.g., Vegetables, Poultry, Dairy')
    description = models.TextField(blank=True, null=True)
    created_date = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        db_table = "ingredient_categories"
        verbose_name = "Ingredient Category"
        verbose_name_plural = "Ingredient Categories"
        ordering = ['name']

class Ingredient(models.Model):
    """Master list of ingredients"""
    
    NUTRITION_SOURCE_CHOICES = [
        ('usda', 'USDA'),
        ('manual', 'Manual'),
    ]
    
    ingredient_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=200, unique=True, help_text='e.g., Onion, Chicken Breast')
    category = models.ForeignKey(IngredientCategory, on_delete=models.SET_NULL, null=True, blank=True)
    default_unit = models.ForeignKey(
        MeasurementUnit, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        help_text='Default measurement unit for this ingredient'
    )
    notes = models.TextField(blank=True, null=True, help_text='Storage tips, substitutions, etc.')
    
    # === USDA FoodData Central nutrition data ===
    # All nutrition values are per 100g. The recipe nutrition calculator
    # scales these by the ingredient amount (after unit conversion).
    # Set when the ingredient is mapped to a USDA food via the mapping wizard.
    
    fdc_id = models.IntegerField(
        null=True, blank=True,
        help_text='USDA FoodData Central food ID (set when mapped to nutrition data)'
    )
    fdc_description = models.CharField(
        max_length=300, null=True, blank=True,
        help_text='USDA description of the matched food (for reference)'
    )
    fdc_data_type = models.CharField(
        max_length=30, null=True, blank=True,
        help_text='USDA data type: Foundation, SR Legacy, Survey (FNDDS), or Branded'
    )
    
    # Macros — per 100g
    calories_per_100g = models.DecimalField(
        max_digits=7, decimal_places=2, null=True, blank=True,
        help_text='Calories (kcal) per 100g'
    )
    protein_per_100g = models.DecimalField(
        max_digits=6, decimal_places=2, null=True, blank=True,
        help_text='Protein (g) per 100g'
    )
    carbs_per_100g = models.DecimalField(
        max_digits=6, decimal_places=2, null=True, blank=True,
        help_text='Carbohydrates (g) per 100g'
    )
    fat_per_100g = models.DecimalField(
        max_digits=6, decimal_places=2, null=True, blank=True,
        help_text='Total fat (g) per 100g'
    )
    
    # Key micros — per 100g
    fiber_per_100g = models.DecimalField(
        max_digits=6, decimal_places=2, null=True, blank=True,
        help_text='Dietary fiber (g) per 100g'
    )
    sugar_per_100g = models.DecimalField(
        max_digits=6, decimal_places=2, null=True, blank=True,
        help_text='Total sugars (g) per 100g'
    )
    sodium_per_100g = models.DecimalField(
        max_digits=7, decimal_places=2, null=True, blank=True,
        help_text='Sodium (mg) per 100g'
    )
    
    # Tracking
    nutrition_synced_at = models.DateTimeField(
        null=True, blank=True,
        help_text='When nutrition data was last fetched from USDA'
    )
    
    # NEW: where the per-100g values came from. 'usda' = pulled from USDA
    # FoodData Central via the mapping wizard. 'manual' = entered or
    # overridden by the user via the manual-entry panel in the mapping
    # modal. NULL = not set yet (e.g., unmapped ingredients, or rows
    # created before this field existed and never re-saved).
    nutrition_source = models.CharField(
        max_length=10,
        choices=NUTRITION_SOURCE_CHOICES,
        null=True,
        blank=True,
        help_text='Where the per-100g nutrition values came from. NULL = not set yet.'
    )
    
    # === WCIM (What Can I Make?) statistics ===
    # Cached values used by the recipe matching engine. Recomputed by the
    # rebuild_recipe_stats management command and the post_save / post_delete
    # signal on RecipeIngredient (see pages/services/wcim.py).
    
    document_frequency = models.PositiveIntegerField(
        default=0,
        help_text='Number of recipes that use this ingredient. Recomputed by rebuild_recipe_stats.'
    )
    idf = models.FloatField(
        default=0.0,
        help_text='Inverse document frequency: log(N / df). Higher = more distinctive. Recomputed by rebuild_recipe_stats.'
    )
    family = models.ForeignKey(
        'IngredientFamily',
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='members',
        help_text='WCIM equivalence family. Items in the same family are partial substitutes when matching recipes.'
    )
    
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name
    
    def is_nutrition_mapped(self):
        """
        True if this ingredient has nutrition data the calculator can use.
        Covers both USDA-mapped ingredients (fdc_id + calories) and
        manually-entered ingredients (calories without fdc_id).
        """
        return self.calories_per_100g is not None
    
    class Meta:
        db_table = "ingredients"
        verbose_name = "Ingredient"
        verbose_name_plural = "Ingredients"
        ordering = ['name']

class IngredientFamily(models.Model):
    """
    Equivalence family for WCIM substitution matching.

    Ingredients in the same family are treated as partial substitutes by the
    matching engine — a recipe calling for "Chicken Breasts" will match a
    user who has "Chicken Thighs" at a reduced score (controlled by
    settings.WCIM_FAMILY_MATCH_WEIGHT, default 0.7).

    Family assignment is opt-in: most ingredients should have no family.
    Only assign a family when items are genuinely interchangeable for
    cooking purposes — over-equating creates bad matches.
    """
    family_id = models.AutoField(primary_key=True)
    name = models.CharField(
        max_length=100,
        unique=True,
        help_text='e.g., "Chicken cuts", "Pork chops", "Beef steaks"'
    )
    description = models.TextField(
        blank=True,
        help_text='Notes on what belongs and what does NOT. Critical for safe substitutions.'
    )
    created_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'ingredient_families'
        verbose_name = 'Ingredient Family'
        verbose_name_plural = 'Ingredient Families'
        ordering = ['name']

    def __str__(self):
        return self.name

class RecipeCourse(models.Model):
    """Course types for recipes (Starter, Main, Dessert, etc.)"""
    recipe_course_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50, unique=True, help_text='e.g., Starter, Main, Dessert, Snack')
    display_order = models.IntegerField(default=0, help_text='Order for display (lower numbers first)')
    created_date = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        db_table = "recipe_courses"
        verbose_name = "Recipe Course"
        verbose_name_plural = "Recipe Courses"
        ordering = ['display_order', 'name']


class RecipeCategory(models.Model):
    """Categories for recipes (Pasta, Salad, Asian, etc.)"""
    recipe_category_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100, unique=True, help_text='e.g., Pasta, Salad, Asian, Burgers')
    description = models.TextField(blank=True, null=True)
    created_date = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        db_table = "recipe_categories"
        verbose_name = "Recipe Category"
        verbose_name_plural = "Recipe Categories"
        ordering = ['name']

def recipe_image_upload_path(instance, filename):
    """Generate upload path for recipe images"""
    ext = filename.split('.')[-1]
    recipe_name_slug = slugify(instance.recipe_name or 'recipe')
    recipe_id = instance.recipe_id or 'new'
    timestamp = timezone.now().strftime('%Y%m%d%H%M%S')
    new_filename = f"recipe-{recipe_id}-{recipe_name_slug}-{timestamp}.{ext}"
    return os.path.join('recipe_images', new_filename)

def recipe_document_upload_path(instance, filename):
    """Generate upload path for recipe documents"""
    ext = filename.split('.')[-1]
    recipe_name_slug = slugify(instance.recipe_name or 'recipe')
    date_str = timezone.now().strftime('%Y%m%d')
    new_filename = f"recipe-{recipe_name_slug}-{date_str}.{ext}"
    return os.path.join('recipe_docs', new_filename)

class Recipe(models.Model):
    """Main recipe table"""
    DIFFICULTY_CHOICES = [
        ('Easy', 'Easy'),
        ('Medium', 'Medium'),
        ('Hard', 'Hard'),
    ]
    
    recipe_id = models.AutoField(primary_key=True)
    recipe_name = models.CharField(max_length=255, help_text='Name of the recipe')
    recipe_description = models.TextField(blank=True, null=True, help_text='Brief description or introduction')
    
    # Time fields (in minutes)
    prep_time = models.IntegerField(blank=True, null=True, help_text='Preparation time in minutes')
    cook_time = models.IntegerField(blank=True, null=True, help_text='Cooking time in minutes')
    total_time = models.IntegerField(blank=True, null=True, help_text='Total time in minutes (auto-calculated if not provided)')
    
    servings = models.IntegerField(default=4, help_text='Number of servings')
    
    # Classification - CHANGED TO MANY-TO-MANY
    courses = models.ManyToManyField(RecipeCourse, blank=True, related_name='recipes')
    categories = models.ManyToManyField(RecipeCategory, blank=True, related_name='recipes')
    
    # Dietary information - CHANGED TO MANY-TO-MANY
    is_vegetarian = models.BooleanField(default=False)
    proteins = models.ManyToManyField('CustomProtein', blank=True, related_name='recipes')
    
    # Additional fields
    difficulty_level = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES, blank=True, null=True)
    recipe_image = models.ImageField(upload_to=recipe_image_upload_path, blank=True, null=True)
    recipe_document = models.FileField(
        upload_to=recipe_document_upload_path,
        null=True,
        blank=True,
        verbose_name="Recipe Document",
        help_text="Optional document attachment (PDF, Word, etc.)"
    )
    
    # AI Import fields (NEW)
    is_ai_imported = models.BooleanField(default=False, help_text='Flag to indicate if recipe was imported via AI')
    ai_extracted_data = models.JSONField(blank=True, null=True, help_text='Raw AI extraction data including structured ingredients')
    
    # Tracking
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)
    created_by = models.CharField(max_length=255, blank=True, null=True, help_text='User who created this recipe')
    
    AUTHOR_CHOICES = [
        ('General', 'General'),
        ('Demetri & Angy', 'Demetri & Angy'),
        ('Erene', 'Erene'),
        ('Alexandra', 'Alexandra'),
    ]
    
    author = models.CharField(
        max_length=50,
        choices=AUTHOR_CHOICES,
        default='General',
        help_text='Recipe author or source'
    )
    
    # === WCIM (What Can I Make?) statistics ===
    # Cached value used by the recipe matching engine. Recomputed by the
    # rebuild_recipe_stats management command and the post_save / post_delete
    # signal on RecipeIngredient (see pages/services/wcim.py).
    weighted_total = models.FloatField(
        default=0.0,
        help_text='Sum of IDF for all ingredients in this recipe. Used as the denominator in WCIM match scoring. Recomputed by rebuild_recipe_stats.'
    )
    
    def save(self, *args, **kwargs):
        # Auto-calculate total_time if not provided
        if not self.total_time and self.prep_time and self.cook_time:
            self.total_time = self.prep_time + self.cook_time
        super().save(*args, **kwargs)
    
    def get_total_time_display(self):
        """Return formatted total time"""
        if self.total_time:
            hours = self.total_time // 60
            minutes = self.total_time % 60
            if hours > 0:
                return f"{hours}h {minutes}m" if minutes > 0 else f"{hours}h"
            return f"{minutes}m"
        return "N/A"
    
    def __str__(self):
        return self.recipe_name
    
    class Meta:
        db_table = "recipes"
        verbose_name = "Recipe"
        verbose_name_plural = "Recipes"
        ordering = ['-created_date']

class PreparationMethod(models.Model):
    """Common preparation methods for ingredients"""
    preparation_method_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100, unique=True, help_text='e.g., chopped, diced, minced, grated')
    created_date = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        db_table = "preparation_methods"
        verbose_name = "Preparation Method"
        verbose_name_plural = "Preparation Methods"
        ordering = ['name']
        
class RecipeIngredient(models.Model):
    """Junction table linking recipes to ingredients with amounts and units"""
    recipe_ingredient_id = models.AutoField(primary_key=True)
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name='recipe_ingredients')
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
    
    # Amount stored as decimal (1.5 for 1½)
    amount = models.DecimalField(max_digits=8, decimal_places=3, help_text='Amount (use decimal: 1.5 for 1½)')
    unit = models.ForeignKey(MeasurementUnit, on_delete=models.SET_NULL, null=True, blank=True)
    
    # CHANGED: Use ForeignKey instead of CharField
    preparation = models.ForeignKey(
        PreparationMethod,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text='e.g., diced, chopped finely, minced'
    )
    
    # Keep this for backward compatibility or remove if not needed
    preparation_note = models.CharField(
        max_length=255, 
        blank=True, 
        null=True, 
        help_text='Additional preparation notes'
    )
    
    ingredient_order = models.IntegerField(default=0, help_text='Display order in recipe')
    ingredient_group = models.CharField(
        max_length=100, 
        blank=True, 
        null=True, 
        help_text='e.g., "For the sauce", "For garnish"'
    )
    
    def get_amount_display(self):
        """Return a nicely formatted string for the amount, removing unnecessary zeros and converting common decimals to fractions."""
        if self.amount is None:
            return ''
        try:
            amount_float = float(self.amount)
        except (TypeError, ValueError):
            return str(self.amount)
        
        # If the amount is a whole number, return it as an integer
        if amount_float.is_integer():
            return str(int(amount_float))
        
        # Map of decimal to common fraction symbols
        fraction_map = {
            0.125: '⅛',
            0.25: '¼',
            0.333: '⅓',
            0.375: '⅜',
            0.5: '½',
            0.625: '⅝',
            0.666: '⅔',
            0.75: '¾',
            0.875: '⅞',
        }

        whole_part = int(amount_float)
        decimal_part = round(amount_float - whole_part, 3)

        # Check if decimal part matches a common fraction
        for dec_value, symbol in fraction_map.items():
            if abs(decimal_part - dec_value) < 0.001:
                return f"{whole_part}{symbol}" if whole_part > 0 else symbol

        # Otherwise, format to up to 3 decimal places, removing trailing zeros and dot
        formatted = '{:.3f}'.format(amount_float).rstrip('0').rstrip('.')
        return formatted

    
    def __str__(self):
        unit_str = self.unit.abbreviation if self.unit and self.unit.abbreviation else (self.unit.name if self.unit else '')
        prep_str = f", {self.preparation_note}" if self.preparation_note else ''
        return f"{self.get_amount_display()} {unit_str} {self.ingredient.name}{prep_str}"
    
    class Meta:
        db_table = "recipe_ingredients"
        verbose_name = "Recipe Ingredient"
        verbose_name_plural = "Recipe Ingredients"
        ordering = ['ingredient_group', 'ingredient_order']


class RecipeIngredientText(models.Model):
    """Simple text-based ingredients for AI-imported recipes"""
    recipe_ingredient_text_id = models.AutoField(primary_key=True)
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name='text_ingredients')
    ingredient_text = models.CharField(max_length=500, help_text='Plain text ingredient')
    ingredient_group = models.CharField(max_length=100, blank=True, null=True, help_text='Ingredient grouping')  # ADD THIS
    order = models.IntegerField(default=0, help_text='Display order')
    
    def __str__(self):
        return self.ingredient_text
    
    class Meta:
        db_table = "recipe_ingredient_text"
        verbose_name = "Recipe Ingredient (Text)"
        verbose_name_plural = "Recipe Ingredients (Text)"
        ordering = ['ingredient_group', 'order']  # UPDATED to order by group first


def instruction_image_upload_path(instance, filename):
    """Generate upload path for instruction step images"""
    ext = filename.split('.')[-1]
    recipe_name_slug = slugify(instance.recipe.recipe_name or 'recipe')
    step_num = instance.step_number
    new_filename = f"recipe-{recipe_name_slug}-step{step_num}.{ext}"
    return os.path.join('recipe_instructions', new_filename)


class RecipeInstruction(models.Model):
    """Step-by-step instructions for recipes"""
    recipe_instruction_id = models.AutoField(primary_key=True)
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name='instructions')
    step_number = models.IntegerField(help_text='Step number in sequence')
    instruction_text = models.TextField(help_text='Detailed instruction for this step')
    
    # Optional grouping and timing
    instruction_group = models.CharField(
        max_length=100, 
        blank=True, 
        null=True, 
        help_text='e.g., "Preparation", "Cooking", "Assembly"'
    )
    time_estimate = models.IntegerField(
        blank=True, 
        null=True, 
        help_text='Estimated time for this step in minutes'
    )
    
    # Optional step image
    step_image = models.ImageField(upload_to=instruction_image_upload_path, blank=True, null=True)
    
    def __str__(self):
        return f"Step {self.step_number}: {self.instruction_text[:50]}..."
    
    class Meta:
        db_table = "recipe_instructions"
        verbose_name = "Recipe Instruction"
        verbose_name_plural = "Recipe Instructions"
        ordering = ['step_number']

class CustomProtein(models.Model):
    """Store custom protein types added by users"""
    custom_protein_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50, unique=True)
    created_date = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        db_table = "custom_proteins"
        verbose_name = "Custom Protein"
        verbose_name_plural = "Custom Proteins"
        ordering = ['name']


class RecipeNutritionCache(models.Model):
    """
    Denormalized snapshot of a recipe's calculated nutrition.
    
    Populated automatically by signals whenever the recipe, its ingredients,
    or the underlying ingredient nutrition data change. Used by the recipe
    list page to sort/filter by nutrition without re-running the calculator
    for every recipe on every search.
    
    Per-100g values are the canonical sortable fields (matches the FDA-style
    label shown in the nutrition modal). Per-serving values are stored too
    for future per-serving features.
    
    is_complete=True only when every ingredient is mapped AND convertible —
    i.e., the calculator returned no unmapped or unconvertible items. The
    sortable search UI filters to is_complete=True so the rankings are
    trustworthy.
    """
    recipe = models.OneToOneField(
        Recipe,
        on_delete=models.CASCADE,
        related_name='nutrition_cache',
    )
    
    # === Per-100g (the canonical sortable fields) ===
    calories_per_100g = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, db_index=True)
    protein_per_100g  = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, db_index=True)
    carbs_per_100g    = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, db_index=True)
    fat_per_100g      = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, db_index=True)
    fiber_per_100g    = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    sugar_per_100g    = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    sodium_per_100g   = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # === Per-serving (for future per-serving features) ===
    calories_per_serving = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    protein_per_serving  = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    carbs_per_serving    = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    fat_per_serving      = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    fiber_per_serving    = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    sugar_per_serving    = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    sodium_per_serving   = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # === Metadata ===
    total_weight_g      = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    is_complete         = models.BooleanField(default=False, db_index=True)
    mapped_count        = models.IntegerField(default=0)
    unmapped_count      = models.IntegerField(default=0)
    unconvertible_count = models.IntegerField(default=0)
    calculated_at       = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'recipe_nutrition_cache'
        verbose_name = 'Recipe Nutrition Cache'
        verbose_name_plural = 'Recipe Nutrition Caches'
    
    def __str__(self):
        return f"Nutrition cache for {self.recipe.recipe_name}"

class RecipeModificationSuggestion(models.Model):
    """
    Cache table for AI-generated recipe modification suggestions.
    """
    
    GOAL_CHOICES = [
        ('reduce_carbs',     'Reduce carbs'),
        ('reduce_calories',  'Reduce calories'),
        ('increase_protein', 'Increase protein'),
        ('reduce_fat',       'Reduce fat'),
    ]
    
    recipe_modification_suggestion_id = models.AutoField(primary_key=True)
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='modification_suggestions',
    )
    goal_type = models.CharField(max_length=30, choices=GOAL_CHOICES)
    suggestions_json = models.JSONField(
        help_text='Validated response from the LLM, matching the schema in recipe_ai.py'
    )
    recipe_version_hash = models.CharField(
        max_length=64,
        help_text='SHA256 hash of recipe + ingredient nutrition state at generation time'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'recipe_modification_suggestions'
        verbose_name = 'Recipe Modification Suggestion'
        verbose_name_plural = 'Recipe Modification Suggestions'
        unique_together = [('recipe', 'goal_type', 'recipe_version_hash')]
        indexes = [
            models.Index(fields=['recipe', 'goal_type'], name='rms_recipe_goal_idx'),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"AI suggestion ({self.get_goal_type_display()}) for {self.recipe.recipe_name}"

# ========== MEAL PLANNING MODELS ==========

class MealPlan(models.Model):
    """Main meal plan header - represents a weekly meal plan"""
    meal_plan_id = models.AutoField(primary_key=True)
    plan_name = models.CharField(max_length=200)
    start_date = models.DateField()
    end_date = models.DateField()
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'meal_plans'
        ordering = ['-start_date']
    
    def __str__(self):
        return f"{self.plan_name} ({self.start_date} to {self.end_date})"
    
    @property
    def total_days(self):
        """Calculate total number of days in the meal plan"""
        return (self.end_date - self.start_date).days + 1
    
    @property
    def total_recipes(self):
        """Count total recipes across all days"""
        return MealPlanRecipe.objects.filter(
            meal_plan_day__meal_plan=self
        ).count()
    
    @property
    def date_range_display(self):
        """Format date range for display"""
        return f"{self.start_date.strftime('%b %d')} - {self.end_date.strftime('%b %d, %Y')}"


class MealPlanDay(models.Model):
    """Individual day within a meal plan"""
    meal_plan_day_id = models.AutoField(primary_key=True)
    meal_plan = models.ForeignKey(MealPlan, on_delete=models.CASCADE, related_name='days')
    date = models.DateField()
    
    class Meta:
        db_table = 'meal_plan_days'
        ordering = ['date']
        unique_together = ['meal_plan', 'date']
    
    def __str__(self):
        return f"{self.date.strftime('%A, %B %d, %Y')}"
    
    @property
    def day_name(self):
        """Get day name (Monday, Tuesday, etc.)"""
        return self.date.strftime('%A')
    
    @property
    def formatted_date(self):
        """Get formatted date for display"""
        return self.date.strftime('%B %d, %Y')

class CookingCalculation(models.Model):
    """Optional cooking time calculator for braai/BBQ/roast recipes"""

    COOKING_METHOD_CHOICES = [
        ('braai', 'Braai / BBQ'),
        ('oven', 'Oven'),
    ]

    recipe = models.OneToOneField(
        Recipe,
        on_delete=models.CASCADE,
        related_name='cooking_calculation'
    )
    cooking_method = models.CharField(
        max_length=10,
        choices=COOKING_METHOD_CHOICES,
        default='braai',
        help_text='Braai/BBQ or Oven'
    )
    serving_time = models.TimeField(
        help_text='Default serving time (e.g. 20:00)'
    )
    fire_lighting_duration = models.PositiveIntegerField(
        help_text='Fire lighting / oven pre-heating time in minutes'
    )
    resting_duration = models.PositiveIntegerField(
        help_text='Resting time in minutes'
    )
    cutting_sauce_duration = models.PositiveIntegerField(
        help_text='Cutting and sauce making time in minutes'
    )
    meat_weight = models.PositiveIntegerField(
        help_text='Default meat weight in grams'
    )
    rate1_minutes_per_500g = models.DecimalField(
        max_digits=5, decimal_places=1,
        help_text='Cooking rate for first portion (mins per 500g)'
    )
    rate1_threshold_grams = models.PositiveIntegerField(
        null=True, blank=True,
        help_text='Weight at which rate switches to rate2 (e.g. 3000). Leave blank if single rate.'
    )
    rate2_minutes_per_500g = models.DecimalField(
        max_digits=5, decimal_places=1,
        null=True, blank=True,
        help_text='Cooking rate for weight above threshold (mins per 500g). Leave blank if single rate.'
    )
    additional_cooking_minutes = models.PositiveIntegerField(
        null=True, blank=True,
        help_text='Fixed extra cooking time in minutes added regardless of weight (e.g. searing time)'
    )

    class Meta:
        db_table = 'cooking_calculations'

    def calculate_cooking_minutes(self, weight_grams=None):
        """Calculate total cooking time in minutes for given weight"""
        weight = weight_grams or self.meat_weight
        rate1 = float(self.rate1_minutes_per_500g)

        if not self.rate1_threshold_grams or not self.rate2_minutes_per_500g:
            # Single rate
            weight_based = (weight / 500) * rate1
        else:
            threshold = self.rate1_threshold_grams
            rate2 = float(self.rate2_minutes_per_500g)
            if weight <= threshold:
                weight_based = (weight / 500) * rate1
            else:
                weight_based = (threshold / 500) * rate1 + ((weight - threshold) / 500) * rate2

        # Add fixed additional cooking time if set
        additional = self.additional_cooking_minutes or 0
        return weight_based + additional

    def calculate_schedule(self, serving_time=None, weight_grams=None):
        """Return full schedule as dict, working backwards from serving time"""
        from datetime import datetime, timedelta

        base_time = serving_time or self.serving_time
        base_dt = datetime.combine(datetime.today(), base_time)

        cooking_minutes = self.calculate_cooking_minutes(weight_grams)
        total_cooking = timedelta(minutes=cooking_minutes)
        fire_lighting = timedelta(minutes=self.fire_lighting_duration)
        resting = timedelta(minutes=self.resting_duration)
        cutting_sauce = timedelta(minutes=self.cutting_sauce_duration)

        serving_dt = base_dt
        start_cutting_dt = serving_dt - cutting_sauce
        finish_cooking_dt = start_cutting_dt - resting
        start_cooking_dt = finish_cooking_dt - total_cooking
        light_fire_dt = start_cooking_dt - fire_lighting

        return {
            'cooking_minutes': round(cooking_minutes),
            'light_fire': light_fire_dt.strftime('%H:%M'),
            'start_cooking': start_cooking_dt.strftime('%H:%M'),
            'finish_cooking': finish_cooking_dt.strftime('%H:%M'),
            'start_cutting': start_cutting_dt.strftime('%H:%M'),
            'serving_time': serving_dt.strftime('%H:%M'),
        }

    def __str__(self):
        return f"Cooking calculation for {self.recipe.recipe_name}"

class MealPlanRecipe(models.Model):
    """Recipe assignment to a specific day in a meal plan"""
    meal_plan_recipe_id = models.AutoField(primary_key=True)
    meal_plan_day = models.ForeignKey(MealPlanDay, on_delete=models.CASCADE, related_name='recipes')
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    servings = models.IntegerField()  # Can override recipe's default servings
    sort_order = models.IntegerField(default=0)
    
    class Meta:
        db_table = 'meal_plan_recipes'
        ordering = ['sort_order', 'meal_plan_recipe_id']
    
    def __str__(self):
        return f"{self.recipe.recipe_name} ({self.servings} servings)"
    
    @property
    def servings_multiplier(self):
        """Calculate multiplier for scaling ingredients"""
        return self.servings / self.recipe.servings

class UnitConversion(models.Model):
    """Conversion rates between different measurement units"""
    unit_conversion_id = models.AutoField(primary_key=True)
    from_unit = models.ForeignKey(
        MeasurementUnit, 
        on_delete=models.CASCADE, 
        related_name='conversions_from'
    )
    to_unit = models.ForeignKey(
        MeasurementUnit, 
        on_delete=models.CASCADE, 
        related_name='conversions_to'
    )
    specific_ingredient = models.ForeignKey(
        'Ingredient',
        on_delete=models.CASCADE,
        related_name='specific_conversions',
        null=True,
        blank=True,
        help_text='If set, this conversion only applies to this specific ingredient. If NULL, conversion is generic.'
    )
    multiplier = models.DecimalField(max_digits=10, decimal_places=6)
    notes = models.CharField(max_length=200, blank=True)
    
    class Meta:
        db_table = 'unit_conversions'
        unique_together = ['from_unit', 'to_unit', 'specific_ingredient']
    
    def __str__(self):
        return f"1 {self.from_unit.name} = {self.multiplier} {self.to_unit.name}"

class RecipeFavourite(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipe_favourites'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='favourited_by'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'recipe')  # Prevents duplicate favourites
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.recipe.recipe_name}"

class PantryStaple(models.Model):
    """
    A single ingredient that a user always considers themselves to have on
    hand. The "What Can I Make?" matching engine treats these as silently
    present, so they don't count against a match.

    Defaults are seeded from DEFAULT_PANTRY_STAPLE_IDS (in pages/services/wcim.py)
    on a user's first visit to the staples management page.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="pantry_staples",
    )
    ingredient = models.ForeignKey(
        "Ingredient",
        on_delete=models.CASCADE,
        related_name="users_having_as_staple",
    )
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "pantry_staples"
        unique_together = [("user", "ingredient")]
        indexes = [models.Index(fields=["user"])]
        ordering = ["ingredient__name"]
        verbose_name = "Pantry Staple"
        verbose_name_plural = "Pantry Staples"

    def __str__(self):
        return f"{self.user.username}'s staple: {self.ingredient.name}"

# Celebration/Event Management Models

class Contact(models.Model):
    """People you want to track celebrations for"""
    RELATIONSHIP_CHOICES = [
        ('family', 'Family'),
        ('friend', 'Friend'),
        ('colleague', 'Colleague'),
        ('other', 'Other'),
    ]
    
    name = models.CharField(max_length=200)
    relationship = models.CharField(max_length=20, choices=RELATIONSHIP_CHOICES, default='other')
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=50, blank=True, null=True)
    photo = models.ImageField(upload_to='contacts/', blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        verbose_name = 'Contact'
        verbose_name_plural = 'Contacts'
    
    def __str__(self):
        return f"{self.name} ({self.get_relationship_display()})"
    
    def get_upcoming_events(self):
        """Get all upcoming events for this contact in the next 365 days"""
        today = timezone.now().date()
        events = []
        for event in self.celebration_events.all():
            next_occurrence = event.get_next_occurrence()
            if next_occurrence and (next_occurrence - today).days <= 365:
                events.append({
                    'event': event,
                    'next_date': next_occurrence,
                    'days_until': (next_occurrence - today).days
                })
        return sorted(events, key=lambda x: x['days_until'])

class CelebrationEvent(models.Model):
    """Events to celebrate (birthdays, namedays, anniversaries, etc.)"""
    EVENT_TYPE_CHOICES = [
        ('birthday', 'Birthday'),
        ('nameday', 'Nameday'),
        ('anniversary', 'Anniversary'),
        ('custom', 'Custom Event'),
    ]
    
    PRIORITY_CHOICES = [
        ('high', 'High'),
        ('normal', 'Normal'),
        ('low', 'Low'),
    ]
    
    contact = models.ForeignKey(Contact, on_delete=models.CASCADE, related_name='celebration_events')
    event_type = models.CharField(max_length=20, choices=EVENT_TYPE_CHOICES)
    event_date = models.DateField(help_text="The date of the event (month and day)")
    is_recurring = models.BooleanField(default=True, help_text="If checked, event repeats annually")
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='normal')
    notes = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Notification settings
    notify_one_week = models.BooleanField(default=True, verbose_name="Notify 1 week before")
    notify_one_day = models.BooleanField(default=True, verbose_name="Notify 1 day before")
    notify_same_day = models.BooleanField(default=True, verbose_name="Notify same day")
    notify_time = models.TimeField(default='09:00:00', help_text="Time to send same-day notification")
    
    # Individual notification preferences - who should be notified about this event
    notify_demetri = models.BooleanField(
        default=True,
        verbose_name="Notify Demetri",
        help_text="Send notification to Demetri (demetrimanias@gmail.com)"
    )
    notify_angy = models.BooleanField(
        default=True,
        verbose_name="Notify Angy",
        help_text="Send notification to Angy (angmaniasbakers@gmail.com)"
    )
    notify_erene = models.BooleanField(
        default=True,
        verbose_name="Notify Erene",
        help_text="Send notification to Erene (erenemanias@gmail.com)"
    )
    notify_alexandra = models.BooleanField(
        default=True,
        verbose_name="Notify Alexandra",
        help_text="Send notification to Alexandra (leximanias@gmail.com)"
    )
    
    class Meta:
        ordering = ['event_date']
        verbose_name = 'Celebration Event'
        verbose_name_plural = 'Celebration Events'
    
    def __str__(self):
        return f"{self.contact.name} - {self.get_event_type_display()} on {self.event_date.strftime('%B %d')}"
    
    def get_next_occurrence(self):
        """Calculate the next occurrence of this event"""
        if not self.is_recurring:
            # For non-recurring events, return the event date if it's in the future
            if self.event_date >= timezone.now().date():
                return self.event_date
            return None
        
        today = timezone.now().date()
        current_year = today.year
        
        # Create date for this year
        try:
            this_year_date = self.event_date.replace(year=current_year)
        except ValueError:
            # Handle Feb 29 on non-leap years
            this_year_date = self.event_date.replace(year=current_year, day=28)
        
        if this_year_date >= today:
            return this_year_date
        else:
            # Event already passed this year, return next year's date
            try:
                return self.event_date.replace(year=current_year + 1)
            except ValueError:
                # Handle Feb 29
                return self.event_date.replace(year=current_year + 1, day=28)
    
    def days_until(self):
        """Days until next occurrence"""
        next_date = self.get_next_occurrence()
        if next_date:
            return (next_date - timezone.now().date()).days
        return None
    
    def get_age(self):
        """Calculate age for birthdays (if original year is known)"""
        if self.event_type == 'birthday' and self.event_date.year != 1900:  # 1900 = placeholder year
            next_occurrence = self.get_next_occurrence()
            if next_occurrence:
                return next_occurrence.year - self.event_date.year
        return None
    
    def get_years(self):
        """Calculate years for anniversaries"""
        if self.event_type == 'anniversary' and self.event_date.year != 1900:
            next_occurrence = self.get_next_occurrence()
            if next_occurrence:
                return next_occurrence.year - self.event_date.year
        return None
    
    def get_color_class(self):
        """Get Bootstrap color class based on event type"""
        colors = {
            'birthday': 'info',      # Blue
            'nameday': 'primary',    # Purple/Blue
            'anniversary': 'danger', # Red
            'custom': 'success',     # Green
        }
        return colors.get(self.event_type, 'secondary')
    
    def get_icon(self):
        """Get icon for event type"""
        icons = {
            'birthday': 'fa-birthday-cake',
            'nameday': 'fa-cross',
            'anniversary': 'fa-heart',
            'custom': 'fa-calendar-star',
        }
        return icons.get(self.event_type, 'fa-calendar')
    
    def get_notification_emails(self):
        """
        Return list of email addresses who should be notified about this event.
        Only includes people who are both checked for this event AND in the TO/CC list.
        """
        # Mapping of notification flags to email addresses
        notification_mapping = {
            'notify_demetri': 'demetrimanias@gmail.com',
            'notify_angy': 'angmaniasbakers@gmail.com',
            'notify_erene': 'erenemanias@gmail.com',
            'notify_alexandra': 'leximanias@gmail.com',
        }
        
        # Get the celebration notification recipients
        from pages.management.commands.email_utils import get_email_recipients
        try:
            recipients = get_email_recipients('celebration_reminder')
            all_notification_emails = recipients['all']  # TO + CC combined
        except:
            # Fallback if database lookup fails
            all_notification_emails = []
        
        # Build list of emails for people who should be notified
        notify_emails = []
        for field_name, email in notification_mapping.items():
            # Person is checked for this event AND their email is in TO/CC list
            if getattr(self, field_name) and email in all_notification_emails:
                notify_emails.append(email)
        
        return notify_emails

class EventNotification(models.Model):
    """Track which notifications have been sent"""
    NOTIFICATION_TYPE_CHOICES = [
        ('one_week', '1 Week Before'),
        ('one_day', '1 Day Before'),
        ('same_day', 'Same Day'),
    ]
    
    event = models.ForeignKey(CelebrationEvent, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPE_CHOICES)
    occurrence_date = models.DateField(help_text="The specific occurrence date this notification is for")
    send_datetime = models.DateTimeField(help_text="When to send this notification")
    sent = models.BooleanField(default=False)
    sent_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        ordering = ['send_datetime']
        unique_together = ['event', 'notification_type', 'occurrence_date']
        verbose_name = 'Event Notification'
        verbose_name_plural = 'Event Notifications'
    
    def __str__(self):
        return f"{self.event} - {self.get_notification_type_display()} on {self.occurrence_date}"

class NotificationRecipient(models.Model):
    NOTIFICATION_TYPES = (
        ('celebration_reminder', 'Celebration Reminders'),
        ('document_expiry', 'Document Expiry Alerts'),
        ('daily_report', 'Daily Property Management Report'),
        ('new_lease_upload', 'New Lease Upload Reminders'),
        ('expense_needs_approval', 'Expense Needs Approval'),
        ('expense_approved', 'Expense Approved'),
        ('expense_paid', 'Expense Paid'),
        ('friday_status_report_supervisor', 'Friday Status Report (Submitted by Supervisor)'),
        ('friday_status_report_staff', 'Friday Status Report (Submitted by Staff)'),
        ('invoice_paid', 'Invoice Marked as Paid'),
        ('issue_comments_daily', 'Daily Issue Comments Report'),
    )
    notification_type = models.CharField(max_length=50, choices=NOTIFICATION_TYPES, unique=True)
    to_addresses = models.TextField(help_text="Comma-separated TO email addresses (primary recipients)")
    cc_addresses = models.TextField(blank=True, help_text="Comma-separated CC email addresses (optional)")
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def get_to_list(self):
        return [email.strip() for email in self.to_addresses.split(',') if email.strip()]
    
    def get_cc_list(self):
        if not self.cc_addresses:
            return []
        return [email.strip() for email in self.cc_addresses.split(',') if email.strip()]
    
    def get_all_recipients(self):
        """Returns combined list of TO and CC for sending"""
        return self.get_to_list() + self.get_cc_list()
    
    class Meta:
        verbose_name = "Notification Recipient"
        verbose_name_plural = "Notification Recipients"
    
    def __str__(self):
        return f"{self.get_notification_type_display()}"

# ============================================================================
# ASSET MANAGEMENT MODELS
# ============================================================================

def asset_invoice_upload_path(instance, filename):
    ext = filename.split('.')[-1]
    prop_name_slug = slugify(instance.property.prop_name or 'property')
    asset_name_slug = slugify(instance.name or 'asset')
    date_str = instance.purchase_date.strftime('%Y%m%d') if instance.purchase_date else timezone.now().strftime('%Y%m%d')
    new_filename = f"{prop_name_slug}-{asset_name_slug}-{date_str}.{ext}"
    return os.path.join('asset_invoices', new_filename)

def maintenance_invoice_upload_path(instance, filename):
    ext = filename.split('.')[-1]
    asset_name_slug = slugify(instance.asset.name or 'asset')
    if instance.date:
        if hasattr(instance.date, 'strftime'):
            date_str = instance.date.strftime('%Y%m%d')
        else:
            date_str = str(instance.date).replace('-', '')
    else:
        date_str = timezone.now().strftime('%Y%m%d')
    new_filename = f"{asset_name_slug}-maintenance-{date_str}.{ext}"
    return os.path.join('maintenance_invoices', new_filename)

class AssetCategory(models.Model):
    """Main category for assets (e.g., Appliances, Furniture)"""
    name = models.CharField(max_length=100, unique=True)
    icon = models.CharField(
        max_length=50, 
        blank=True, 
        null=True, 
        help_text="FontAwesome icon class (e.g., 'fa-snowflake')"
    )
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['name']
        verbose_name_plural = 'Asset Categories'
        db_table = 'asset_categories'
    
    def __str__(self):
        return self.name


class AssetSubcategory(models.Model):
    """Subcategory for assets (e.g., Air Conditioner, Washing Machine)"""
    category = models.ForeignKey(
        AssetCategory, 
        on_delete=models.CASCADE, 
        related_name='subcategories'
    )
    name = models.CharField(max_length=100)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['category__name', 'name']
        verbose_name_plural = 'Asset Subcategories'
        unique_together = ['category', 'name']
        db_table = 'asset_subcategories'
    
    def __str__(self):
        return f"{self.category.name} - {self.name}"


class AssetSupplier(models.Model):
    """Supplier/vendor for assets"""
    name = models.CharField(max_length=200, unique=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['name']
        verbose_name = 'Asset Supplier'
        verbose_name_plural = 'Asset Suppliers'
        db_table = 'asset_suppliers'
    
    def __str__(self):
        return self.name


class PropertyAsset(models.Model):
    """Individual asset within a property"""
    # Core relationships
    property = models.ForeignKey('props', on_delete=models.CASCADE, related_name='assets')
    category = models.ForeignKey(AssetCategory, on_delete=models.PROTECT)
    subcategory = models.ForeignKey(AssetSubcategory, on_delete=models.PROTECT)
    
    # Basic info
    name = models.CharField(max_length=200, help_text="Asset name/description")
    location_room = models.CharField(max_length=100, help_text="Room/location within property")
    
    # Purchase info
    purchase_date = models.DateField(null=True, blank=True)
    supplier = models.ForeignKey(AssetSupplier, on_delete=models.PROTECT, null=True, blank=True)
    purchase_price = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True
    )
    purchase_invoice = models.FileField(
        upload_to=asset_invoice_upload_path, 
        null=True, 
        blank=True
    )
    
    # Optional details
    brand_manufacturer = models.CharField(
        max_length=100, 
        blank=True, 
        null=True, 
        verbose_name="Brand/Manufacturer"
    )
    
    # Warranty tracking - Option C: Both methods available
    warranty_duration_months = models.IntegerField(
        null=True, 
        blank=True, 
        help_text="Warranty duration in months (will auto-calculate expiry date)"
    )
    warranty_expiry_date = models.DateField(
        null=True, 
        blank=True, 
        help_text="Warranty expiry date (calculated automatically or entered manually)"
    )
    
    # Notes
    notes = models.TextField(blank=True, null=True)
    
    # Metadata
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['property', 'category', 'subcategory', 'name']
        verbose_name = 'Property Asset'
        verbose_name_plural = 'Property Assets'
        db_table = 'property_assets'
    
    def __str__(self):
        return f"{self.property.prop_name} - {self.name}"
    
    def save(self, *args, **kwargs):
        """Auto-calculate warranty expiry if duration provided and expiry not manually set"""
        if self.warranty_duration_months and self.purchase_date and not self.warranty_expiry_date:
            self.warranty_expiry_date = self.purchase_date + relativedelta(
                months=self.warranty_duration_months
            )
        super().save(*args, **kwargs)
    
    def is_warranty_active(self):
        """Check if warranty is still active"""
        if self.warranty_expiry_date:
            from datetime import date
            return date.today() <= self.warranty_expiry_date
        return False
    
    def warranty_days_remaining(self):
        """Calculate days remaining on warranty"""
        if self.warranty_expiry_date:
            from datetime import date
            delta = self.warranty_expiry_date - date.today()
            return delta.days if delta.days > 0 else 0
        return 0
    
    def get_total_maintenance_cost(self):
        """Calculate total maintenance/repair costs for this asset"""
        return self.maintenance_records.aggregate(
            total=models.Sum('cost')
        )['total'] or Decimal('0.00')


class AssetMaintenance(models.Model):
    """Maintenance/repair log for assets"""
    MAINTENANCE_TYPES = [
        ('cleaning', 'Cleaning'),
        ('inspection', 'Inspection'),
        ('part_replacement', 'Part Replacement'),
        ('repair', 'Repair'),
        ('scheduled', 'Scheduled Maintenance'),
        ('service', 'Service'),
    ]
    
    asset = models.ForeignKey(
        PropertyAsset, 
        on_delete=models.CASCADE, 
        related_name='maintenance_records'
    )
    date = models.DateField()
    maintenance_type = models.CharField(max_length=20, choices=MAINTENANCE_TYPES)
    description = models.TextField()
    cost = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True, 
        help_text="Optional cost"
    )
    service_provider = models.CharField(
        max_length=200, 
        blank=True, 
        null=True, 
        help_text="Technician/company name (optional)"
    )
    invoice = models.FileField(
        upload_to=maintenance_invoice_upload_path,
        null=True,
        blank=True,
        help_text="Optional maintenance invoice or receipt"
    )
    
    # Metadata
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-date']
        verbose_name = 'Asset Maintenance Record'
        verbose_name_plural = 'Asset Maintenance Records'
        db_table = 'asset_maintenance'
    
    def __str__(self):
        return f"{self.asset.name} - {self.get_maintenance_type_display()} on {self.date}"

# ============================================================================
# USER PROFILE MODEL
# ============================================================================

class UserProfile(models.Model):
    MENU_PREFERENCE_CHOICES = [
        ('top', 'Top Menu'),
        ('sidebar', 'Side Menu'),
    ]

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile'
    )
    menu_preference = models.CharField(
        max_length=10,
        choices=MENU_PREFERENCE_CHOICES,
        default='top'
    )
    is_active = models.BooleanField(
        default=True,
        help_text='Uncheck to disable this user from logging in'
    )
    profile_photo = models.ImageField(
        upload_to='profile_photos/',
        blank=True,
        null=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'user_profiles'
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'

    def __str__(self):
        return f"{self.user.username} - Profile"
