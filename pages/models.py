from datetime import datetime
from dateutil.relativedelta import relativedelta
from decimal import Decimal
from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models
from django.db import connections
from django.db.models import Min, Max, Sum
from django.db.models.signals import post_save, post_delete, pre_delete
from django.dispatch import receiver
from django.utils import timezone
from django.utils.text import slugify
from pages.workspace import WorkspaceManager

import os
import uuid


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
    tenant_physical_invoice_required = models.BooleanField(
        default=False,
        verbose_name="Generate Physical Invoice",
        help_text="Also generate and email a PDF VAT invoice for this tenant each month.",
    )
    tenant_bill_levies = models.BooleanField(
        default=False,
        verbose_name="Bill Communal Fees (Levies)",
        help_text="Include tenant_levies as a communal line — on the physical invoice and in the collection amount. Off = today's rent-only behaviour.",
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
    invoice_amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    # Date the invoice was marked paid. Captured automatically in save() below
    # for FUTURE use (e.g. a "traditionally pays late" signal in analytics); no
    # current report reads it. Null while the invoice is unpaid.
    invoice_paid_date = models.DateField(blank=True, null=True)

    def save(self, *args, **kwargs):
        # Stamp the paid date the first time the invoice is marked paid, and
        # clear it if it is set back to unpaid. Living on the model (not the
        # form) means every save path — form, admin, shell — captures it.
        is_paid = (self.invoice_paid or "").strip().lower() == "yes"
        if is_paid and self.invoice_paid_date is None:
            from datetime import date as _paid_date
            self.invoice_paid_date = _paid_date.today()
        elif not is_paid:
            self.invoice_paid_date = None
        super().save(*args, **kwargs)

    class Meta:
        db_table="invoice"

    @property
    def effective_amount(self):
        """Amount to bill/collect for this invoice.

        Returns the per-invoice override (invoice_amount) when set -- what the
        physical-invoice send cron writes for flagged tenants -- and falls back
        to the tenant's base rent otherwise. Single source of truth for the
        Open Invoices list and the Debtors Age Analysis report so the two
        can no longer drift.
        """
        if self.invoice_amount is not None:
            return self.invoice_amount
        return self.tenant.tenant_rent or 0

class InvoiceCustomer(models.Model):
    """A non-tenant customer for ad-hoc (customer) invoices. The invoice freezes
    its own copy of these fields (bill_*), so editing or deleting a customer
    never rewrites an already-issued invoice. PROTECT on the invoice FK means a
    customer with invoices cannot be deleted."""
    name = models.CharField(max_length=255)
    customer_id_label = models.CharField(max_length=255, blank=True,
        help_text="Shown in the 'Customer ID' box on the invoice.")
    billing_address = models.TextField(blank=True, help_text="One line per row.")
    billing_tel = models.CharField(max_length=64, blank=True)
    email_to = models.TextField(blank=True, help_text="Comma-separated To addresses.")
    email_cc = models.TextField(blank=True, help_text="Comma-separated CC addresses.")
    email_body = models.TextField(blank=True,
        help_text="Optional saved greeting/body for this customer's invoice e-mail. "
                  "Blank uses a generic default.")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "invoice_customers"
        verbose_name = "Invoice Customer"
        verbose_name_plural = "Invoice Customers"
        ordering = ["name"]

    def __str__(self):
        return self.name


class PhysicalInvoiceProfile(models.Model):
    tenant = models.OneToOneField(
        tenant, on_delete=models.CASCADE, related_name="physical_invoice_profile",
    )
    # Customer block on the invoice. Blank fields fall back to tenant values at render time.
    customer_id_label = models.CharField(max_length=255, blank=True,
        help_text="Shown in the 'Customer ID' box. Defaults to the tenant name if blank.")
    billing_name = models.CharField(max_length=255, blank=True,
        help_text="Customer name on the invoice. Defaults to the tenant name if blank.")
    billing_address = models.TextField(blank=True,
        help_text="Customer address — one line per row.")
    billing_tel = models.CharField(max_length=64, blank=True,
        help_text="Defaults to the tenant contact number if blank.")
    client_email_body = models.TextField(blank=True,
        help_text="Saved greeting and body for the monthly invoice e-mail. "
                  "Use {month} where the period should appear; the send cron "
                  "replaces it with the month and year (e.g. 'June 2026'). "
                  "Leave blank to use a generic default.")
    # Water Consumed line: variable amount entered at confirmation; this is just the schedule.
    water_enabled = models.BooleanField(default=False,
        help_text="Prompt for a (VAT-free) Water Consumed line on the scheduled months.")
    water_cycle_anchor = models.DateField(null=True, blank=True,
        help_text="Any month this tenant's water cycle lands on; the interval counts from here.")
    water_cycle_interval_months = models.PositiveSmallIntegerField(default=2,
        help_text="Months between water lines (2 = every second month).")

    def __str__(self):
        return f"Physical invoice profile — {self.tenant}"

    class Meta:
        db_table = "physical_invoice_profile"
        verbose_name = "Physical Invoice Profile"
        verbose_name_plural = "Physical Invoice Profiles"

def physical_invoice_pdf_upload_path(instance, filename):
    """Storage path for a rendered physical-invoice PDF."""
    ext = (filename.rsplit('.', 1)[-1] or 'pdf').lower()
    if getattr(instance, 'tenant_id', None):
        name = getattr(instance.tenant, 'tenant_name', '') or 'tenant'
    else:
        name = getattr(instance, 'bill_name', '') or 'customer'
    tenant_slug = slugify(name)
    period = f"{instance.period_year:04d}{instance.period_month:02d}"
    number = slugify(instance.invoice_number or 'draft')
    return os.path.join('physical_invoices', f"{tenant_slug}-{period}-{number}.{ext}")


class PhysicalInvoice(models.Model):
    """A physical (PDF) VAT invoice for one tenant for one month.

    Lifecycle: draft -> approved -> sent (linear; un-approve drops an approved
    invoice back to draft). Editable only while draft; approving locks it,
    sending freezes it. Created by the prepare cron ~5 days before month-end,
    dated for the UPCOMING month; emailed to the customer by the send cron on
    the 1st.
    """

    STATUS_DRAFT = 'draft'
    STATUS_APPROVED = 'approved'
    STATUS_SENT = 'sent'
    STATUS_CHOICES = [
        (STATUS_DRAFT, 'Draft'),
        (STATUS_APPROVED, 'Approved'),
        (STATUS_SENT, 'Sent'),
    ]

    physical_invoice_id = models.AutoField(primary_key=True)
    tenant = models.ForeignKey(tenant, on_delete=models.PROTECT, null=True, blank=True,
                               related_name='physical_invoices')
    # Customer (non-tenant) invoices: tenant is NULL, customer + bill_* snapshot are used.
    customer = models.ForeignKey('InvoiceCustomer', on_delete=models.PROTECT,
                                 null=True, blank=True, related_name='invoices')
    bill_name = models.CharField(max_length=255, blank=True)
    bill_customer_label = models.CharField(max_length=255, blank=True)
    bill_address = models.TextField(blank=True)
    bill_tel = models.CharField(max_length=64, blank=True)
    bill_email_to = models.TextField(blank=True,
        help_text='Comma-separated To addresses for a customer invoice.')
    bill_email_cc = models.TextField(blank=True,
        help_text='Comma-separated CC addresses for a customer invoice.')
    bill_email_body = models.TextField(blank=True)
    # Collections invoice for the same month (created on the 1st). Linked later
    # for the balancing step; null until then.
    collection_invoice = models.ForeignKey(
        invoices, on_delete=models.SET_NULL, null=True, blank=True, related_name='physical_invoice')

    period_year = models.PositiveSmallIntegerField()
    period_month = models.PositiveSmallIntegerField(help_text='1-12')
    invoice_date = models.DateField(help_text='Printed on the invoice (1st of the period month).')
    invoice_number = models.CharField(max_length=32, blank=True, null=True,
        help_text='PR-#### — assigned when the invoice is sent.')

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_DRAFT)

    vat_rate = models.DecimalField(max_digits=5, decimal_places=4, default=Decimal('0.1900'),
        help_text='VAT rate applied to vatable lines, frozen on this invoice.')
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    vat = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    total = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    currency = models.CharField(max_length=3, default='EUR')

    pdf_file = models.FileField(upload_to=physical_invoice_pdf_upload_path, blank=True, null=True)

    approved_at = models.DateTimeField(null=True, blank=True)
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='approved_physical_invoices')
    sent_at = models.DateTimeField(null=True, blank=True)
    email_status = models.CharField(max_length=20, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'physical_invoices'
        verbose_name = 'Physical Invoice'
        verbose_name_plural = 'Physical Invoices'
        ordering = ['-period_year', '-period_month', 'tenant_id']
        unique_together = [('tenant', 'period_year', 'period_month')]

    def __str__(self):
        who = self.tenant if self.tenant_id else (self.bill_name or 'Customer')
        return f"{self.invoice_number or 'DRAFT'} — {who} — {self.period_month:02d}/{self.period_year}"

    @property
    def is_editable(self):
        return self.status == self.STATUS_DRAFT

    def assert_editable(self):
        if not self.is_editable:
            raise ValidationError(
                f"Invoice {self.invoice_number or self.pk} is {self.get_status_display()} "
                f"and can no longer be edited. Un-approve it first.")

    def recalc_totals(self, save=True):
        """Recompute subtotal/vat/total from the current line rows."""
        lines = list(self.lines.all())
        subtotal = sum((ln.line_total or Decimal('0.00')) for ln in lines) or Decimal('0.00')
        vatable_base = sum((ln.line_total or Decimal('0.00')) for ln in lines if ln.vatable) or Decimal('0.00')
        self.subtotal = Decimal(subtotal).quantize(Decimal('0.01'))
        self.vat = (Decimal(vatable_base) * self.vat_rate).quantize(Decimal('0.01'))
        self.total = (self.subtotal + self.vat).quantize(Decimal('0.01'))
        if save:
            self.save(update_fields=['subtotal', 'vat', 'total', 'updated_at'])
        return self.total

    def approve(self, user=None):
        if self.status != self.STATUS_DRAFT:
            raise ValidationError("Only a draft invoice can be approved.")
        self.status = self.STATUS_APPROVED
        self.approved_at = timezone.now()
        self.approved_by = user
        self.save(update_fields=['status', 'approved_at', 'approved_by', 'updated_at'])

    def unapprove(self):
        if self.status != self.STATUS_APPROVED:
            raise ValidationError("Only an approved (not yet sent) invoice can be un-approved.")
        self.status = self.STATUS_DRAFT
        self.approved_at = None
        self.approved_by = None
        self.save(update_fields=['status', 'approved_at', 'approved_by', 'updated_at'])

    def mark_sent(self):
        if self.status != self.STATUS_APPROVED:
            raise ValidationError("Only an approved invoice can be marked as sent.")
        self.status = self.STATUS_SENT
        self.sent_at = timezone.now()
        self.save(update_fields=['status', 'sent_at', 'updated_at'])


class PhysicalInvoiceLine(models.Model):
    physical_invoice_line_id = models.AutoField(primary_key=True)
    physical_invoice = models.ForeignKey(PhysicalInvoice, on_delete=models.CASCADE, related_name='lines')
    service = models.CharField(max_length=50, blank=True)
    unit_of_measure = models.CharField(max_length=50, blank=True)
    description = models.CharField(max_length=255, blank=True)
    qty = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal('1.00'))
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    line_total = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    vatable = models.BooleanField(default=False)
    sort_order = models.IntegerField(default=0)

    class Meta:
        db_table = 'physical_invoice_lines'
        verbose_name = 'Physical Invoice Line'
        verbose_name_plural = 'Physical Invoice Lines'
        ordering = ['sort_order', 'physical_invoice_line_id']

    def save(self, *args, **kwargs):
        self.line_total = (Decimal(self.qty or 0) * Decimal(self.unit_price or 0)).quantize(Decimal('0.01'))
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.service} {self.description} = {self.line_total}"

class PhysicalInvoiceNumbering(models.Model):
    """Singleton: the running counter for physical-invoice (PR) numbers.

    Numbers are <prefix><zero-padded>, e.g. PR-0170. `next_number` is the next
    value the system will issue; it advances automatically as invoices are
    sent, and can be bumped up by hand when an external invoice has consumed a
    number in between.
    """
    prefix = models.CharField(max_length=10, default="PR-")
    pad_width = models.PositiveSmallIntegerField(default=4,
        help_text="Zero-padding width (4 -> PR-0170).")
    next_number = models.PositiveIntegerField(default=1,
        help_text="The next PR number the system will issue.")
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "physical_invoice_numbering"
        verbose_name = "Physical Invoice Numbering"
        verbose_name_plural = "Physical Invoice Numbering"

    def __str__(self):
        return f"Numbering — next {self.format(self.next_number)}"

    def format(self, n):
        return f"{self.prefix}{int(n):0{self.pad_width}d}"

    @classmethod
    def get_solo(cls):
        obj = cls.objects.first()
        return obj or cls.objects.create()

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
    issues_details_last_notified_at = models.DateTimeField(null=True, blank=True)    

    def __str__(self):
        return self.issues_details_comment

    @property
    def is_in_urgent_cooldown(self):
        """True if a 'Notify Now' was pressed within the cooldown window."""
        if not self.issues_details_last_notified_at:
            return False
        from django.utils import timezone
        from datetime import timedelta
        from pages.email_utils import URGENT_NOTIFICATION_COOLDOWN_MINUTES
        delta = timezone.now() - self.issues_details_last_notified_at
        return delta < timedelta(minutes=URGENT_NOTIFICATION_COOLDOWN_MINUTES)

    @property
    def urgent_cooldown_minutes_ago(self):
        """Whole minutes elapsed since last 'Notify Now'. None if never pressed."""
        if not self.issues_details_last_notified_at:
            return None
        from django.utils import timezone
        delta = timezone.now() - self.issues_details_last_notified_at
        return int(delta.total_seconds() // 60)

    class Meta:
        db_table="issues_details"

class IssueAuditLog(models.Model):
    """Field-level change history for an issue (and, later, its comments).

    One row per changed field per edit: editing the heading and the property
    in a single save writes two rows. The issue-edit view captures a
    before-snapshot, diffs it against the submitted values, and writes a row
    only for fields that actually changed. Rendered as the History section on
    the issue detail page, and the substrate a later edit-notification email
    reads from.

    Not workspace-scoped: issues are property-management records with no
    workspace FK, so their history follows the same unscoped pattern.
    Property changes store the property NAME in old_value/new_value for
    readability, not the pk. The `comment` FK stays NULL for issue-field
    changes; it is populated by the (later) comment-editing step, which shares
    this same log.
    """
    issue = models.ForeignKey(
        issues,
        on_delete=models.CASCADE,
        related_name='audit_log',
    )
    comment = models.ForeignKey(
        issues_details,
        on_delete=models.CASCADE,
        null=True, blank=True,
        related_name='audit_log',
        help_text='Set when the change was to a comment rather than an issue '
                  'field; NULL for issue-field changes.',
    )
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='issue_edits',
        help_text='Who made the change. NULL if the account was later removed.',
    )
    field_name = models.CharField(
        max_length=50,
        help_text="Model field that changed, e.g. 'issues_heading', "
                  "'issues_description', 'prop'.",
    )
    old_value = models.TextField(blank=True, null=True)
    new_value = models.TextField(blank=True, null=True)
    changed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'issue_audit_log'
        verbose_name = 'Issue Audit Log Entry'
        verbose_name_plural = 'Issue Audit Log'
        ordering = ['-changed_at', '-id']

    def __str__(self):
        who = self.user.username if self.user else 'unknown'
        return f"{self.field_name} on issue {self.issue_id} by {who}"

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
    # Which lease value (if any) this line type is fed from. '' = normal editable
    # revenue-table line type; 'rent'/'levies' = driven by the lease, read-only on
    # leased properties. Replaces the old name-substring matching so renaming the
    # "Rental"/"Levies" line types no longer breaks lease revenue.
    lease_role = models.CharField(max_length=10, blank=True, default='')
    
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

    workspace = models.ForeignKey(
        'pages.Workspace',
        on_delete=models.CASCADE,
        related_name='passports',
        help_text='The workspace this passport belongs to.',
    )
    holder_name = models.CharField(max_length=200)
    document_type = models.CharField(max_length=20, choices=DOCUMENT_TYPE_CHOICES)
    document_number = models.CharField(max_length=50)
    country_of_issue = models.CharField(max_length=100)
    date_of_issue = models.DateField(null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    document_file = models.FileField(upload_to='passports/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = WorkspaceManager()

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
    
    # Macros â€” per 100g
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
    
    # Key micros â€” per 100g
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
    matching engine â€” a recipe calling for "Chicken Breasts" will match a
    user who has "Chicken Thighs" at a reduced score (controlled by
    settings.WCIM_FAMILY_MATCH_WEIGHT, default 0.7).

    Family assignment is opt-in: most ingredients should have no family.
    Only assign a family when items are genuinely interchangeable for
    cooking purposes â€” over-equating creates bad matches.
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
    
    # Amount stored as decimal (1.5 for 1Â½)
    amount = models.DecimalField(max_digits=8, decimal_places=3, help_text='Amount (use decimal: 1.5 for 1Â½)')
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
            0.125: '\u215B',  # one-eighth
            0.25:  '\u00BC',  # one-quarter
            0.333: '\u2153',  # one-third
            0.375: '\u215C',  # three-eighths
            0.5:   '\u00BD',  # one-half
            0.625: '\u215D',  # five-eighths
            0.666: '\u2154',  # two-thirds
            0.75:  '\u00BE',  # three-quarters
            0.875: '\u215E',  # seven-eighths
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
    
    is_complete=True only when every ingredient is mapped AND convertible â€”
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
    workspace = models.ForeignKey(
        'pages.Workspace',
        on_delete=models.CASCADE,
        related_name='contacts',
    )
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = WorkspaceManager()

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

class HouseholdMember(models.Model):
    """A person within a workspace who can be linked to celebration events
    (relevance) and, from Phase 2, to notification delivery.

    Members are an AUDIENCE, not necessarily logins — the user FK is
    optional and null for people who never sign in. Replaces the hardcoded
    notify_demetri / notify_angy / notify_erene / notify_alexandra flags.
    """
    workspace = models.ForeignKey(
        'pages.Workspace',
        on_delete=models.CASCADE,
        related_name='household_members',
    )
    name = models.CharField(max_length=200)
    email = models.EmailField(blank=True, null=True)
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='household_memberships',
        help_text='Optional link to a login account. NULL for members who never sign in.',
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = WorkspaceManager()

    class Meta:
        db_table = 'household_members'
        ordering = ['name']
        unique_together = [('workspace', 'name')]
        verbose_name = 'Household Member'
        verbose_name_plural = 'Household Members'

    def __str__(self):
        return f"{self.name} ({self.workspace.name})"

class MemberNotificationSubscription(models.Model):
    """Per-member opt-in to a personal notification type (celebration
    reminders, document expiry). Replaces the comma-separated address lists
    on NotificationRecipient for personal types: a member receives a given
    type iff an active subscription row exists for them.

    Workspace is inherited via member.workspace, so there is no direct
    workspace FK — reach these through HouseholdMember.subscriptions.
    """

    # Mirrors NotificationRecipient.PERSONAL_NOTIFICATION_TYPES.
    NOTIFICATION_TYPE_CHOICES = [
        ('celebration_reminder', 'Celebration Reminders'),
        ('document_expiry', 'Document Expiry Alerts'),
    ]

    member = models.ForeignKey(
        'pages.HouseholdMember',
        on_delete=models.CASCADE,
        related_name='subscriptions',
    )
    notification_type = models.CharField(max_length=50, choices=NOTIFICATION_TYPE_CHOICES)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'member_notification_subscriptions'
        unique_together = [('member', 'notification_type')]
        ordering = ['member__name', 'notification_type']
        verbose_name = 'Member Notification Subscription'
        verbose_name_plural = 'Member Notification Subscriptions'

    def __str__(self):
        return f"{self.member.name} · {self.get_notification_type_display()} ({'on' if self.is_active else 'off'})"

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

    # Relevance axis (Phase 3): which household members this event pertains to.
    # Replaces the four notify_* booleans above. Final recipients are these
    # members intersected with their per-type notification opt-ins
    # (MemberNotificationSubscription), resolved in get_notification_emails().
    relevant_to = models.ManyToManyField(
        'pages.HouseholdMember',
        blank=True,
        related_name='relevant_events',
        help_text='Household members this event pertains to (the relevance axis).',
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
        """Return emails to notify for this event.

        Composes the two axes:
          - relevance: the household members this event pertains to
            (self.relevant_to), and
          - delivery:  those members who are active and hold an active
            celebration_reminder subscription, with an email.

        Final recipients = relevant members who are opted in. Returns empty
        if no relevant member is subscribed — the cron treats empty as
        "skip", which is correct (no point emailing nobody, and no
        cross-workspace leakage since everything is scoped through the
        members' own workspace).
        """
        emails, seen = [], set()
        members = (
            self.relevant_to
            .filter(
                is_active=True,
                subscriptions__notification_type='celebration_reminder',
                subscriptions__is_active=True,
            )
            .order_by('name')
        )
        for m in members:
            if not m.email:
                continue
            key = m.email.strip().lower()
            if key and key not in seen:
                seen.add(key)
                emails.append(m.email.strip())
        return emails

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
        ('issue_comment_urgent', 'Urgent Issue Comment Alert'),
        ('physical_invoice_review', 'Physical Invoices Awaiting Approval'),
        ('physical_invoice_client', 'Physical Invoice to Client'),
    )

    # Notification types that are scoped to a workspace (one recipient row
    # per workspace). All other types are global (workspace = NULL).
    PERSONAL_NOTIFICATION_TYPES = frozenset({
        'celebration_reminder',
        'document_expiry',
    })

    notification_type = models.CharField(max_length=50, choices=NOTIFICATION_TYPES)
    workspace = models.ForeignKey(
        'pages.Workspace',
        on_delete=models.CASCADE,
        related_name='notification_recipients',
        null=True, blank=True,
        help_text=(
            'Required for personal notification types (celebration_reminder, '
            'document_expiry); NULL for admin types (daily_report, etc.).'
        ),
    )
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
        unique_together = [('notification_type', 'workspace')]

    def __str__(self):
        ws_label = f" [{self.workspace.name}]" if self.workspace_id else ""
        return f"{self.get_notification_type_display()}{ws_label}"


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

def asset_photo_upload_path(instance, filename):
    """
    Generate storage path for asset photos:
    asset_photos/{property-slug}-{asset-slug}-{YYYYMMDD}-{uuid6}.{ext}
    Matches the existing asset_invoices/ naming convention.
    """
    ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else 'jpg'
    if ext not in ('jpg', 'jpeg', 'png'):
        ext = 'jpg'  # defensive fallback; view layer also validates
    prop_slug = slugify(instance.asset.property.prop_name) or 'property'
    asset_slug = slugify(instance.asset.name) or 'asset'
    stamp = datetime.now().strftime('%Y%m%d')
    uid = uuid.uuid4().hex[:6]
    return f'asset_photos/{prop_slug}-{asset_slug}-{stamp}-{uid}.{ext}'


class AssetPhoto(models.Model):
    """
    Photo attached to a PropertyAsset. Max 5 per asset (enforced at view layer).
    display_order drives sort: lowest = cover photo (shown as thumbnail).
    """
    asset = models.ForeignKey(
        'PropertyAsset',
        on_delete=models.CASCADE,
        related_name='photos'
    )
    image = models.ImageField(upload_to=asset_photo_upload_path)
    display_order = models.IntegerField(default=0, db_index=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='+'
    )

    class Meta:
        ordering = ['display_order', 'uploaded_at']

    def __str__(self):
        return f"Photo for {self.asset.name} ({self.image.name})"


@receiver(post_delete, sender=AssetPhoto)
def delete_asset_photo_file(sender, instance, **kwargs):
    """When an AssetPhoto row is deleted, remove the file from disk too."""
    if instance.image:
        try:
            instance.image.delete(save=False)
        except Exception:
            pass  # already gone or storage error — don't block deletion

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
# WORKSPACE MODEL
# ============================================================================


class Workspace(models.Model):
    """A tenancy boundary for Personal-module data (Passports, Celebrations,
    Recipes).

    Every tenanted record (passport, celebration, recipe, ingredient, etc.)
    references exactly one Workspace; users belong to exactly one Workspace
    (via UserProfile.workspace) and see only the data within it.

    Lifecycle:
      - Created either explicitly via User Administration, or auto-created
        lazily on first access by a user with no workspace assigned.
      - The owner is the user who can manage workspace settings (initially
        just rename it). Superusers can do the same regardless of ownership.
      - Delete is PROTECTed by UserProfile.workspace — you can't drop a
        workspace while any user still belongs to it. Move users to another
        workspace first.
    """

    name = models.CharField(
        max_length=200,
        help_text="Display name for the workspace (e.g. \"Demetri's Household\").",
    )
    owner = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='owned_workspaces',
        help_text="The user who can manage this workspace's settings. "
                  "Superusers bypass this restriction.",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'workspaces'
        ordering = ['name']
        verbose_name = 'Workspace'
        verbose_name_plural = 'Workspaces'

    def __str__(self):
        return self.name


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
    workspace = models.ForeignKey(
        'pages.Workspace',
        on_delete=models.PROTECT,
        related_name='members',
        null=True,
        blank=True,
        help_text="The workspace this user belongs to (for Personal modules). "
                  "Auto-created on first access if not assigned explicitly.",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'user_profiles'
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'

    def __str__(self):
        return f"{self.user.username} - Profile"
# =============================================================================
# Financial Figure History (Phase 1) — append-only record of BUDGETED figures.
# Installed by install_financial_history.py.  Nothing in the app READS this in
# Phase 1; it only records. The P&L consumes it in Phase 2.
#
# One row per save/edit of a budgeted expense or a direct/seasonal revenue.
# effective_date = the month a value takes effect FROM (defaults to the day of
# the edit; the edit form may override it). The twelve monthly columns mirror
# expense_jan.. / revenue_jan.. so a history row reads exactly like a live row.
# =============================================================================
from datetime import date as _fh_date
import logging as _fh_logging

_fh_log = _fh_logging.getLogger(__name__)
_FH_MONTHS = ['jan', 'feb', 'mar', 'apr', 'may', 'jun',
              'jul', 'aug', 'sep', 'oct', 'nov', 'dec']


class FinancialFigureHistory(models.Model):
    KIND_REVENUE = 'revenue'          # direct / seasonal revenue (revenue table)
    KIND_BUDGET = 'budget_expense'    # budgeted expense (expense table)
    KIND_CHOICES = [
        (KIND_REVENUE, 'Revenue (direct / seasonal)'),
        (KIND_BUDGET, 'Budgeted expense'),
    ]

    financial_figure_history_id = models.AutoField(primary_key=True)
    prop = models.ForeignKey('props', on_delete=models.CASCADE, related_name='figure_history')
    kind = models.CharField(max_length=20, choices=KIND_CHOICES)

    # pk of the source config row that changed (expense_id / revenue_id)
    source_pk = models.IntegerField(help_text='expense_id or revenue_id of the source row')
    line_type = models.CharField(max_length=255, blank=True, null=True,
        help_text='Denormalised line-type label, e.g. Rental / Insurance.')

    effective_date = models.DateField(help_text='Date from which these values apply.')
    amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True,
        help_text='Base amount at this version (mirrors expense_amount / revenue_amount).')

    # Monthly snapshot — mirrors the twelve columns on expense / revenue.
    jan = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    feb = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    mar = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    apr = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    may = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    jun = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    jul = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    aug = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    sep = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    oct = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    nov = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    dec = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)

    source = models.CharField(max_length=30, blank=True, null=True,
        help_text='budget | direct | prorata | prorata_line | prorata_valuation | seed')
    changed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='+')
    changed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'financial_figure_history'
        verbose_name = 'Financial Figure History'
        verbose_name_plural = 'Financial Figure History'
        ordering = ['prop_id', 'kind', '-effective_date', '-changed_at']
        indexes = [
            models.Index(fields=['prop', 'kind', 'effective_date']),
            models.Index(fields=['kind', 'source_pk']),
        ]

    def __str__(self):
        return '%s — %s — eff %s' % (self.get_kind_display(), self.line_type, self.effective_date)


# ---- Write-hook helpers. Called AFTER commit via transaction.on_commit(); they
#      NEVER raise, so a history-write problem can't break the user's save. -----
def record_expense_history(exp, effective_date, *, source='budget', user=None):
    """Snapshot a budgeted `expense` row into history. Fail-safe (logs, returns
    None on any error)."""
    try:
        months = {m: getattr(exp, 'expense_' + m) for m in _FH_MONTHS}
        return FinancialFigureHistory.objects.create(
            prop=exp.prop, kind=FinancialFigureHistory.KIND_BUDGET,
            source_pk=exp.expense_id, line_type=str(exp.expense_line_types),
            effective_date=effective_date, amount=exp.expense_amount,
            source=source, changed_by=user, **months,
        )
    except Exception:
        _fh_log.exception('record_expense_history failed (save itself was not affected)')
        return None


def record_revenue_history(rev, effective_date, *, source='direct', user=None):
    """Snapshot a `revenue` row into history. Fail-safe."""
    try:
        months = {m: getattr(rev, 'revenue_' + m) for m in _FH_MONTHS}
        return FinancialFigureHistory.objects.create(
            prop=rev.prop, kind=FinancialFigureHistory.KIND_REVENUE,
            source_pk=rev.revenue_id, line_type=str(rev.revenue_line_types),
            effective_date=effective_date, amount=rev.revenue_amount,
            source=source, changed_by=user, **months,
        )
    except Exception:
        _fh_log.exception('record_revenue_history failed (save itself was not affected)')
        return None


# ---- Phase-2 resolver (unused until the P&L rework; safe to ship now). --------
def figure_monthly_value_as_of(prop, kind, source_pk, year, month_idx):
    """The monthly figure in force for `month_idx` (1-12) of `year`: the latest
    history row whose effective_date falls in that month or earlier. A change
    dated any day in a month applies to that month and forward. Returns None if
    no history exists (caller falls back to the live row)."""
    nxt = _fh_date(year + 1, 1, 1) if month_idx >= 12 else _fh_date(year, month_idx + 1, 1)
    row = (FinancialFigureHistory.objects
           .filter(prop=prop, kind=kind, source_pk=source_pk, effective_date__lt=nxt)
           .order_by('-effective_date', '-changed_at')
           .first())
    if row is None:
        return None
    return getattr(row, _FH_MONTHS[month_idx - 1])
# ---- Phase 2: bulk year resolver (one query) for the P&L -----------------------
def resolve_year_months_bulk(prop_ids, kind, year):
    """Bulk form of figure_monthly_value_as_of for a whole year.

    Returns {source_pk: [v_jan, ..., v_dec]} — for each source row belonging to
    prop_ids, the twelve budgeted figures IN FORCE during `year`, resolved month
    by month (a change takes effect from its own month forward; earlier months
    and earlier years keep earlier values). One DB query. A source with no
    history is simply absent from the dict, so the caller keeps its live cells.
    """
    from collections import defaultdict
    rows = (FinancialFigureHistory.objects
            .filter(prop_id__in=list(prop_ids), kind=kind,
                    effective_date__lte=_fh_date(year, 12, 31))
            .order_by('source_pk', 'effective_date', 'changed_at'))
    by_src = defaultdict(list)
    for r in rows:
        by_src[r.source_pk].append(r)
    out = {}
    for src, versions in by_src.items():
        vals = []
        for m in range(1, 13):
            chosen = None
            for v in versions:              # ascending by effective_date
                if (v.effective_date.year, v.effective_date.month) <= (year, m):
                    chosen = v
                else:
                    break
            vals.append(getattr(chosen, _FH_MONTHS[m - 1]) if chosen is not None else None)
        out[src] = vals
    return out


# =============================================================================
# Effective-dated property valuations (year-aware Value Increase %).
# Reuses FinancialFigureHistory with kind='valuation': one append-only row per
# valuation change, source_pk = prop_values_id, amount = the current value at
# that point. A property's Value Increase for a year uses the value in force at
# the END of that year — so a value entered in 2026 doesn't retro-apply to 2023.
# No new table / schema migration: kind is stored as the raw string 'valuation'.
# =============================================================================
KIND_VALUATION = 'valuation'


def record_valuation_history(pv, effective_date, *, source='valuation', user=None):
    """Snapshot a `prop_values` current value into effective-dated history.
    Fail-safe: logs and returns None on any error, so a valuation save is never
    broken by a history-write problem."""
    try:
        if pv is None or pv.prop_values_current_value is None:
            return None
        return FinancialFigureHistory.objects.create(
            prop=pv.prop, kind=KIND_VALUATION,
            source_pk=pv.prop_values_id, line_type='Valuation',
            effective_date=effective_date,
            amount=pv.prop_values_current_value,
            source=source, changed_by=user,
        )
    except Exception:
        _fh_log.exception('record_valuation_history failed (save itself was not affected)')
        return None


def property_value_as_of(prop, year):
    """The property's current value in force at the END of `year`: the latest
    'valuation' history row with effective_date on or before 31 Dec of `year`.
    Returns a Decimal, or None if no dated valuation applies to that year yet
    (caller shows Value Increase as N/A and drops it from that year's score)."""
    row = (FinancialFigureHistory.objects
           .filter(prop=prop, kind=KIND_VALUATION, effective_date__lte=_fh_date(year, 12, 31))
           .order_by('-effective_date', '-changed_at')
           .first())
    return row.amount if row is not None else None


# =============================================================================
# Phase 3: lease-driven Revenue for the P&L (both P&Ls share this).
# Rent + levies come from the lease covering each month (any part of a month =
# full month; latest-starting lease wins on overlap). Current-year future months
# with no lease continue at the most recent rent IF the property was rented this
# year and no later lease is loaded; otherwise VACANT. Seasonal / no-lease
# properties fall back to the Financials revenue table.
# =============================================================================
from calendar import monthrange as _fh_monthrange
from decimal import Decimal as _fh_Decimal

_FH_REV_MON = ['jan', 'feb', 'mar', 'apr', 'may', 'jun',
               'jul', 'aug', 'sep', 'oct', 'nov', 'dec']


def _lease_month(leases, y, m, today):
    """(tag, lease|None, rent, levies) for month m/year y."""
    ms = _fh_date(y, m, 1)
    me = _fh_date(y, m, _fh_monthrange(y, m)[1])
    over = [l for l in leases
            if l.tenant_lease_start_date and l.tenant_lease_end_date
            and l.tenant_lease_start_date <= me and l.tenant_lease_end_date >= ms]
    if over:
        l = max(over, key=lambda x: x.tenant_lease_start_date)
        return ('lease', l, l.tenant_rent or 0, l.tenant_levies or 0)
    if (y, m) < (today.year, today.month):
        return ('vacant', None, 0, 0)   # past month -> real vacancy; current/future -> continuation below
    later = [l for l in leases
             if l.tenant_lease_start_date and l.tenant_lease_start_date > me]
    if later:
        return ('vacant', None, 0, 0)
    ys = _fh_date(today.year, 1, 1)
    active = [l for l in leases if l.tenant_lease_end_date and l.tenant_lease_end_date >= ys]
    if active:
        l = max(active, key=lambda x: x.tenant_lease_end_date)
        return ('assumed', l, l.tenant_rent or 0, l.tenant_levies or 0)
    return ('vacant', None, 0, 0)


def lease_monthly_rent_levies(prop, year, today=None):
    """(rent[12], levies[12], has_leases) for a property/year from its leases."""
    today = today or _fh_date.today()
    leases = list(tenant.objects.filter(prop=prop))
    rent = [0.0] * 12
    lev = [0.0] * 12
    if not leases:
        return rent, lev, False
    for m in range(1, 13):
        _t, _l, r, v = _lease_month(leases, year, m, today)
        rent[m - 1] = float(r or 0)
        lev[m - 1] = float(v or 0)
    return rent, lev, True


LEASE_ROLE_RENT = 'rent'
LEASE_ROLE_LEVIES = 'levies'


def lease_line_type(role):
    """The revenue_line_types row feeding lease `role` ('rent'|'levies'), or None."""
    return revenue_line_types.objects.filter(lease_role=role).first()


def lease_revenue_rows(prop, year, rental_lt=None, levies_lt=None, today=None):
    """Unsaved `revenue` instances for this property's revenue in `year`.
    Leased: a Rental row (lease rent/mo) + a Levies row (lease levies/mo) + any
    non rental/levies revenue-table rows. Seasonal: the revenue-table rows as-is."""
    rent, lev, has = lease_monthly_rent_levies(prop, year, today)
    if not has:
        return list(prop.revenue_set.all())
    if rental_lt is None:
        rental_lt = lease_line_type(LEASE_ROLE_RENT)
    if levies_lt is None:
        levies_lt = lease_line_type(LEASE_ROLE_LEVIES)
    rows = []
    if rental_lt is not None:
        r = revenue(prop=prop, revenue_line_types=rental_lt)
        for i, mm in enumerate(_FH_REV_MON):
            setattr(r, 'revenue_' + mm, _fh_Decimal(str(rent[i])))
        rows.append(r)
    if levies_lt is not None and any(lev):
        r = revenue(prop=prop, revenue_line_types=levies_lt)
        for i, mm in enumerate(_FH_REV_MON):
            setattr(r, 'revenue_' + mm, _fh_Decimal(str(lev[i])))
        rows.append(r)
    for r in prop.revenue_set.all():
        if not (r.revenue_line_types and r.revenue_line_types.lease_role):
            rows.append(r)
    return rows


def current_lease_revenue(prop, today=None):
    """(rent, levies, has_leases, has_active_lease) for a property RIGHT NOW.
    has_leases -> the property has any lease record ever (a "leased property").
    has_active_lease -> a lease covers today. Leased but not active -> rent/levies 0
    (present it as "Vacant - no active lease"). Seasonal (no leases) -> (None, None,
    False, False); the caller uses the revenue table instead."""
    today = today or _fh_date.today()
    leases = list(tenant.objects.filter(prop=prop))
    if not leases:
        return (None, None, False, False)
    active = [l for l in leases
              if l.tenant_lease_start_date and l.tenant_lease_end_date
              and l.tenant_lease_start_date <= today <= l.tenant_lease_end_date]
    if active:
        l = max(active, key=lambda x: x.tenant_lease_start_date)
        return (l.tenant_rent or 0, l.tenant_levies or 0, True, True)
    return (0, 0, True, False)


def property_annual_lease_revenue(prop, year=None):
    """Annual revenue for a property, matching the P&L exactly: lease-driven rent +
    levies for a leased property (current-year future months continued at the
    current rent) plus any ancillary revenue-table rows; the revenue table as-is
    for seasonal / no-lease properties. Sums the same rows lease_revenue_rows feeds
    the P&L, so Financial Indicators and the P&L never disagree."""
    year = year or _fh_date.today().year
    total = _fh_Decimal('0')
    for r in lease_revenue_rows(prop, year):
        for mm in _FH_REV_MON:
            total += (getattr(r, 'revenue_' + mm, 0) or 0)
    return total


def property_annual_budgeted_expenses(prop, year=None):
    """Annual budgeted expenses for a property, matching the P&L: each expense row
    resolved to the effective-dated figure in force during `year` (rows with no
    history keep their current monthly cells).

    Pro-rated to the months the property was IN SERVICE that year, so a first
    partial year does not carry a full 12 months of budget against only a few
    months of rent. "In service from" is the property's earliest lease start (a
    proxy for the purchase date): before that year -> nothing; the first year ->
    from the lease-start month to December (any part of a month = a full month);
    later years -> the full 12. A property with no leases (seasonal / no-lease)
    is treated as in service all year, unchanged."""
    year = year or _fh_date.today().year
    _first_lease = tenant.objects.filter(prop=prop).exclude(
        tenant_lease_start_date__isnull=True).aggregate(
            _m=Min('tenant_lease_start_date'))['_m']
    if _first_lease is None:
        _start_month = 1                     # no leases -> owned/active all year
    elif _first_lease.year > year:
        return _fh_Decimal('0')              # not yet in service this year
    elif _first_lease.year == year:
        _start_month = _first_lease.month    # first (partial) year
    else:
        _start_month = 1                     # full year
    vals_map = resolve_year_months_bulk([prop.prop_id], FinancialFigureHistory.KIND_BUDGET, year)
    total = _fh_Decimal('0')
    for e in prop.expense_set.all():
        vals = vals_map.get(e.expense_id)
        if vals is not None:
            for _i in range(_start_month - 1, 12):
                total += (vals[_i] or 0)
        else:
            for _i in range(_start_month - 1, 12):
                total += (getattr(e, 'expense_' + _FH_REV_MON[_i], 0) or 0)
    return total


def property_annual_actual_expenses(prop, year=None):
    """Annual actual (ad-hoc) expenses for a property in `year`, matching the P&L
    Actuals view: approved + paid transactions dated in that year."""
    year = year or _fh_date.today().year
    agg = act_expense.objects.filter(
        prop=prop,
        act_expense_date__year=year,
        act_expense_approved="Yes",
        act_expense_paid="Yes",
    ).aggregate(_t=Sum('act_expense_amount'))
    return agg['_t'] or _fh_Decimal('0')
