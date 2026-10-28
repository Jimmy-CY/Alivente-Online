from datetime import datetime
from dateutil.relativedelta import relativedelta
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
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
    project_name = models.CharField(max_length=255, blank=True)
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
        blank=True
    )
    
    project_description = models.TextField(blank=True)
    project_name_greek = models.CharField(max_length=255, blank=True, help_text='Greek translation of project name')
    project_description_greek = models.TextField(blank=True, help_text='Greek translation of project description')
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
    task_name = models.CharField(max_length=255, blank=True)
    task_description = models.TextField(blank=True)  # longtext
    task_name_greek = models.CharField(max_length=255, blank=True, help_text='Greek translation of task name')
    task_description_greek = models.TextField(blank=True, help_text='Greek translation of task description')
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
        blank=True
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
        blank=True
    )
    
    task_budgeted_cost = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True, default=0.00)
    task_actual_cost = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True, default=0.00)
    task_assigned_to = models.CharField(max_length=255, blank=True)
    
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
    
    def update_from_subtasks(self):
        """Write this task's six calculated values onto its stored columns.

        THE EXACT SHAPE OF Project.update_project_from_tasks(), and that is
        the point. A Project is kept up to date from its tasks: that method
        writes calculated to stored, and a post_save and post_delete signal
        on ProjectTask fires it. A PARENT TASK had all six matching
        get_calculated_* methods and NOTHING THAT CALLED THEM. The rollup
        existed one level up and was never implemented one level down.

        What that looked like from outside: tick the last subtask Completed
        and the parent still said In Progress everywhere except
        project_tasks_edit, which renders the accessors into its disabled
        (Auto-calculated) inputs - so the one screen that advertised the
        behaviour was the one screen that had it.

        WHY THE VALUE HAS TO BE STORED AND NOT JUST READ. Every
        get_calculated_* already falls back to the stored value when a task
        has no subtasks, so reading the accessor is never wrong and a
        read-side fix is tempting. But a database cannot call a Python
        method: any .filter(task_status=...), .order_by() or Sum() over main
        tasks reads the column. That is what settles it.

        NO save() HERE - the caller saves, exactly as
        update_project_from_tasks does, so neither can recurse into itself.
        """
        self.task_status = self.get_calculated_status()
        self.task_start_date = self.get_calculated_start_date()
        self.task_expected_completion_date = (
            self.get_calculated_expected_completion())
        self.task_actual_completion_date = (
            self.get_calculated_actual_completion())
        self.task_budgeted_cost = self.get_calculated_budgeted_cost()
        self.task_actual_cost = self.get_calculated_actual_cost()

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
    document_name = models.CharField(max_length=255, blank=True)
    document_description = models.TextField(blank=True)
    document_file = models.FileField(upload_to=project_document_upload_path, blank=True, null=True)
    document_uploaded_date = models.DateTimeField(auto_now_add=True)
    document_uploaded_by = models.CharField(max_length=255, blank=True)
    
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
    prop_name = models.CharField(max_length=255, blank=True)
    prop_address1 = models.CharField(max_length=255, blank=True)
    prop_address2 = models.CharField(max_length=255, blank=True)
    prop_suburb = models.CharField(max_length=255, blank=True)
    prop_city = models.CharField(max_length=255, blank=True)
    prop_province = models.CharField(max_length=255, blank=True)
    prop_country = models.CharField(max_length=255, blank=True)
    prop_pcode = models.CharField(max_length=255, blank=True)
    prop_latitude = models.DecimalField(max_digits=10, decimal_places=8, blank=True, null=True)
    prop_longitude = models.DecimalField(max_digits=11, decimal_places=8, blank=True, null=True)
    prop_floor_area = models.IntegerField(blank=True, null=True)
    prop_year_built = models.IntegerField(blank=True, null=True)
    prop_status = models.CharField(max_length=255, blank=True)
    prop_available_for_rent = models.CharField(max_length=255, blank=True)
    prop_title_deed = models.FileField(upload_to=title_deed_upload_path, blank=True, null=True)
    prop_title_deed_status = models.CharField(max_length=255, blank=True)
    prop_electricity = models.CharField(max_length=255, blank=True)
    prop_water = models.CharField(max_length=255, blank=True)
    prop_refuse = models.CharField(max_length=255, blank=True)
    prop_property_tax = models.CharField(max_length=255, blank=True)
    prop_sewerage = models.CharField(max_length=255, blank=True)
    prop_insurance = models.CharField(max_length=255, blank=True)
    prop_include_in_occupancy = models.BooleanField(
        default=True,
        verbose_name="Include in Occupancy",
        help_text="Uncheck to exclude this property from occupancy rate and days-to-fill calculations (e.g., for seasonal rentals)"
    )

    # OWNED FROM - OF-3, 28 Oct 2026. His rule, in his words: "We could
    # use the date of the first rental for that property as the date that
    # we owned it from" - the gap between buying and first letting is
    # accepted. Filled from the first lease by migration 0112 and editable
    # on the property. Blank means "use the first lease", and a property
    # with no lease and no date counts as owned all along (seasonal).
    # Nothing - no budget line, no share of a pro-rata line, no revenue -
    # counts in a month before this one. See property_owned_from().
    prop_owned_from = models.DateField(
        blank=True, null=True, verbose_name="Owned From",
        help_text="Budgets and revenue count from this month. Blank = the first lease start.")

    def __str__(self):
        return self.prop_name or f"Property {self.prop_id}"

    # THE ADDRESS A TENANT SEES - ES-7, 25 Oct 2026. His instruction: the
    # property NAME is internal ("Apolloneon - Demetri") and must never
    # reach a tenant. Built the way Generate Lease builds the address it
    # writes into the lease, so the email, the signing page and the lease
    # itself describe the place in the same words. Empty when no address
    # is recorded - and then a tenant sees no place at all, never the name.
    ADDRESS_FIELDS = ('prop_address1', 'prop_address2', 'prop_suburb',
                      'prop_city', 'prop_province', 'prop_country',
                      'prop_pcode')

    @property
    def tenant_address(self):
        return ', '.join(p.strip() for p in
                         (getattr(self, f) or '' for f in self.ADDRESS_FIELDS)
                         if p and p.strip())

    @property
    def tenant_address_short(self):
        """First line and city - short enough for an email subject."""
        return ', '.join(p.strip() for p in
                         (self.prop_address1 or '', self.prop_city or '')
                         if p and p.strip())

    class Meta:
        db_table = "prop"
        verbose_name = "Property"
        verbose_name_plural = "Properties"

class petty(models.Model):
    petty_cash_id = models.AutoField(primary_key=True)
    petty_cash_date = models.DateField(blank=True, null=True)
    petty_cash_description = models.CharField(max_length=55, blank=True)
    petty_cash_amount = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True)
    petty_cash_dr_cr = models.CharField(max_length=2, blank=True)

    def __str__(self):
        return self.petty_cash_description

    class Meta:
        db_table="petty_cash"

class tenant(models.Model):
    tenant_id = models.AutoField(primary_key=True)
    prop = models.ForeignKey(props, on_delete=models.CASCADE)
    tenant_type = models.CharField(max_length=255, blank=True)
    tenant_name = models.CharField(max_length=255, blank=True)
    tenant_contact_person = models.CharField(max_length=255, blank=True)
    tenant_contact_number = models.CharField(max_length=255, blank=True)
    tenant_email = models.CharField(max_length=255, blank=True)

    # A SECOND TENANT - T2-1, 24 Oct 2026.
    #
    # A JOINT TENANT WHO SIGNS AND IS LIABLE, not a non-signing
    # occupant - his decision of 23 October. The Cyprus lease
    # templates have assumed one for months: generate_lease_agreement
    # asks for a full set of details and throws every one of them
    # away when the document downloads.
    #
    # THREE COLUMNS AND NOT SIX. The first tenant has no passport and
    # no address stored either - those live in Generate's
    # per-document data. Giving the second person columns the first
    # does not have would make this model say more about a joint
    # tenant than about the one who signs first.
    #
    # BLANK BY DEFAULT, so every row already in the database is
    # correct the moment the migration lands and nothing is touched.
    tenant_2_name = models.CharField(max_length=255, blank=True)
    tenant_2_contact_number = models.CharField(max_length=255, blank=True)
    tenant_2_email = models.CharField(max_length=255, blank=True)
    # IDENTITY NUMBERS - TI-1, 26 Oct 2026, his decision. Optional, all
    # three: the Company Reg Number for a Company, a Passport/ID for each
    # Individual tenant. T2-1 left them out on purpose - "the first
    # tenant stores no passport either; those live in Generate's
    # per-document data" - and he has now asked for them on the record,
    # for both people alike, so Generate can read them instead of asking.
    #
    # BLANK BY DEFAULT, so every existing row is correct the moment the
    # migration lands; nothing is back-filled.
    tenant_company_reg_no = models.CharField(max_length=50, blank=True)
    tenant_id_number = models.CharField(max_length=50, blank=True)
    tenant_2_id_number = models.CharField(max_length=50, blank=True)
    # THE COUNTRY THAT ISSUED IT - PC-1, 28 Oct 2026, his decision. The
    # lease names it beside the number, and Generate asked for it afresh
    # on every document and kept none of it. Now it lives here, for both
    # people, chosen from one list (pages/countries.py) so it is spelt
    # one way. Blank by default; nothing is back-filled.
    tenant_id_country = models.CharField(max_length=100, blank=True)
    tenant_2_id_country = models.CharField(max_length=100, blank=True)
    tenant_deposit = models.IntegerField(blank=True, null=True)
    tenant_lease_start_date = models.DateField(blank=True, null=True)
    tenant_lease_end_date = models.DateField(blank=True, null=True)
    tenant_rental_type = models.CharField(max_length=255, blank=True)
    tenant_renewal = models.CharField(max_length=255, blank=True)
    tenant_renewal_period = models.IntegerField(blank=True, null=True)
    tenant_rent = models.IntegerField(blank=True, null=True)
    tenant_levies = models.IntegerField(blank=True, null=True)
    tenant_payment_terms = models.IntegerField(blank=True, null=True)
    tenant_current = models.CharField(max_length=255, blank=True)
    tenant_lease_agreement = models.FileField(
        upload_to=lease_agreement_upload_path, 
        blank=True, 
        null=True,
        verbose_name="Lease Agreement Document"
    )
    tenant_lease_agreement_status = models.CharField(
        max_length=255, 
        blank=True,
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
        """Validate lease dates, and who may hold a joint tenancy."""
        # A SECOND TENANT ONLY ON AN INDIVIDUAL TENANCY - T2-2, 24 Oct
        # 2026, his decision of the same day.
        #
        # THIS RULE IS NOT NEW AND IT IS NOT MINE. Generate Lease
        # Agreement has refused this since before the columns existed
        # and says so in an alert. What was new was that the RECORD
        # would have accepted what Generate refuses, so T2-3's prefill
        # could have handed Generate a tenancy it will not open.
        #
        # HERE AND NOT ONLY IN THE SCRIPT, because a script is a
        # courtesy and clean() is the rule. save() calls full_clean(),
        # so the admin, a management command and a POST from a stale
        # page all meet it.
        #
        # NO ROW IN THE DATABASE CAN FAIL THIS TODAY: the three
        # columns landed blank in T2-1's migration yesterday and
        # nothing has written one yet.
        refusal = self.second_tenant_refusal(
            self.tenant_type, self.has_second_tenant)
        if refusal:
            raise ValidationError(refusal)

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

    # WHO MAY HOLD A JOINT TENANCY, lifted out of clean().
    # T2-3, 24 Oct 2026 - and it is the same rule it always was.
    #
    # THE DATE SITS ON ONE LINE ON PURPOSE. main() asks whether MARK
    # is already in this file to decide that the round has run, and
    # the first spelling wrapped the mark across two comment lines.
    # The check never fired, so a second run refused on a missing
    # anchor instead of saying it was already applied - safe, and
    # not what the house pattern says.
    #
    # IT IS A STATICMETHOD BECAUSE THE SECOND CALLER HAS NO ROW IN
    # HAND. T2-3 saves a joint tenant back from Generate with
    # .update(), which never loads the object and never calls
    # clean() - and .update() is deliberate: .save() runs full_clean()
    # over the WHOLE row, so an old tenancy with a pre-existing lease
    # date problem would make LEASE GENERATION fail over something
    # that has nothing to do with the lease being generated.
    #
    # BUT BYPASSING clean() BYPASSES THIS RULE, so the rule had to
    # stop living inside clean() to be asked anywhere else. One rule,
    # named once, two callers - rather than a second copy of the
    # sentence in a view, which is what T2-2 refused to do when it
    # read Generate's wording rather than inventing its own.
    #
    # Returns the refusal, or None when there is nothing to refuse,
    # so a caller can raise it, show it or log it as it needs to.
    @staticmethod
    def second_tenant_refusal(tenant_type, has_second):
        """Why this tenancy may not hold a joint tenant, or None."""
        if not has_second:
            return None
        if (tenant_type or '').strip() == 'Individual':
            return None
        return ("You must remove the second tenant before changing to "
                "Company type. Second tenants are only allowed for "
                "Individual tenants.")

    @property
    def has_second_tenant(self):
        """Is there a second person on this tenancy? T2-1.

        THE NAME DECIDES, not the email and not the telephone. A
        joint tenant who has not given an address is still a joint
        tenant and still liable; a blank name with an email is a
        half-typed form, not a person.

        ONE PREDICATE, HERE. Twenty templates and twenty-seven python
        modules read the first tenant's details. Each deciding this
        for itself is how two screens come to disagree about whether
        somebody exists.
        """
        return bool((self.tenant_2_name or '').strip())

    # THE ADDRESS PARSER, AND IT IS NOT A STRIP.
    #
    # tenant_email is FREE TEXT and always has been: the form labels
    # it Email Address(es) and its placeholder reads One or more
    # emails, separated by commas. send_physical_invoices already
    # pulls every address out of it with this exact expression and
    # mails all of them - so a joint tenant crammed into that one box
    # has been receiving invoices for as long as anyone has typed
    # them that way.
    #
    # THE FIRST SPELLING OF tenant_emails TREATED IT AS ONE ADDRESS,
    # which would have made the model and the mailer disagree about
    # who is on a tenancy: the model saying one person, the mailer
    # sending to two. The worst kind of disagreement, because each is
    # right about its own half.
    #
    # ONE EXPRESSION, HERE, so T2-5 can point the mailer at this
    # instead of keeping a second copy of it.
    EMAIL_RE = r'[^\s,;<>()]+@[^\s,;<>()]+\.[^\s,;<>()]+'

    @property
    def tenant_emails(self):
        """Every address on this tenancy, in order, without repeats.

        WHO ACTUALLY GETS EMAILED IS NOT DECIDED BY THIS. Renewal
        notices do not read it at all - check_lease_renewal_and_
        invoices mails configured staff recipients, not tenants. T2-5
        points send_physical_invoices here so a joint tenant in the
        proper column is reached exactly as one typed into the
        free-text box already is. This only answers what addresses
        EXIST.
        """
        import re as _re
        out = []
        for raw in ((self.tenant_email or ''), (self.tenant_2_email or '')):
            for e in _re.findall(self.EMAIL_RE, raw):
                if e.lower() not in [x.lower() for x in out]:
                    out.append(e)
        return out

    # HOW A TENANCY IS NAMED ON A SCREEN - T2-2, 24 Oct 2026.
    #
    # The register's Tenant column, and the four reports T2-4 will
    # build, all have to answer the same question: whose tenancy is
    # this. Five screens each joining two names for themselves is five
    # chances to disagree about the separator, about which name comes
    # first, and about what to show when the second one is blank.
    JOINT_SEPARATOR = ' & '

    @property
    def tenant_display_name(self):
        """Who is on this tenancy, as one line.

        THE STORED NAME IS UNCHANGED, and nothing here is written back
        to the column. NB-1, 26 Oct 2026: the Tenants register and Open
        Invoices filters now OFFER and MATCH this name (his decision, so
        a joint tenancy is chosen as the table shows it); joins and
        lookups elsewhere still go by tenant_name.

        A BLANK FIRST NAME IS NOT A REASON TO PRINT A SEPARATOR. It
        should not happen - the form requires the first name - but a
        row imported or edited around the form could carry one, and
        "& Maria Georgiou" would read as a bug in the screen rather
        than as a gap in the record.
        """
        return self.joint_name(self.tenant_name, self.tenant_2_name)

    # THE JOIN ITSELF, BECAUSE ONE CALLER IS NOT A MODEL.
    # T2-4, 24 Oct 2026 - and the date sits on ONE line on purpose.
    #
    # main() asks whether MARK is already in this file to decide the
    # round has run. T2-3 wrapped its mark across two comment lines
    # four hours ago and the check never fired - a second run refused
    # on a missing anchor instead of saying it was already applied.
    # This round made the identical mistake. Both are one line now.
    #
    # get_overdue_invoices builds its rows from RAW SQL and never
    # loads a tenant object, so it cannot ask the property above. It
    # can ask this. The alternative was a second join written out in
    # a view, and two joins are two separators - the exact fault
    # tenant_display_name exists to prevent.
    #
    # Same shape as second_tenant_refusal, which T2-3 lifted out of
    # clean() for the same reason: one rule, named once, asked by
    # whoever needs it.
    @staticmethod
    def joint_name(first, second):
        """Both people on a tenancy, as one line. Either may be blank.

        A BLANK FIRST NAME IS NOT A REASON TO PRINT A SEPARATOR. It
        should not happen - the form requires it - but a row imported
        or edited around the form could carry one, and "& Maria
        Georgiou" reads as a bug in the screen rather than as a gap
        in the record.
        """
        a = (first or '').strip()
        b = (second or '').strip()
        if not b:
            return a
        if not a:
            return b
        return a + tenant.JOINT_SEPARATOR + b

    def __str__(self):
        return self.tenant_name if self.tenant_name else ""

    class Meta:
        db_table = "tenant"
        verbose_name = "Tenant"
        verbose_name_plural = "Tenants"

class supplier(models.Model):
    supplier_id = models.AutoField(primary_key=True)
    supplier_contact_person = models.CharField(max_length=255, blank=True)
    supplier_contact_number = models.CharField(max_length=255, blank=True)
    supplier_email = models.CharField(max_length=255, blank=True)
    supplier_company_name = models.CharField(max_length=255, blank=True)
    supplier_role = models.CharField(max_length=255, blank=True)
    supplier_country = models.CharField(max_length=255, blank=True)
    
    def __str__(self):
        return self.supplier_contact_person

    class Meta:
        db_table="supplier"

class invoices(models.Model):
    invoice_id = models.AutoField(primary_key=True)
    tenant = models.ForeignKey(tenant, on_delete=models.CASCADE)
    invoice_date = models.DateField(blank=True, null=True)
    invoice_paid = models.CharField(max_length=255, blank=True)
    invoice_amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    # Date the invoice was marked paid, stamped automatically in save() below.
    # Read by the tenant payment-behaviour report (tenant_payment_days_view)
    # and by the tenant_payment_days management command. Null while unpaid.
    # History starts 3 Aug 2026, when this field was added: anything marked
    # paid before then has no date and cannot be reconstructed.
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
    invoice_number = models.CharField(max_length=32, blank=True,
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
    email_status = models.CharField(max_length=20, blank=True)

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
    issues_heading = models.CharField(max_length=255, blank=True)
    issues_description = models.CharField(max_length=255, blank=True)
    issues_date_logged = models.DateField(blank=True, null=True)
    issues_status = models.CharField(max_length=255, blank=True)
    issues_resolution_date = models.DateField(blank=True, null=True, default=None)
    issues_resolving_user = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return self.issues_heading

    class Meta:
        db_table="issues"

class issues_details(models.Model):
    issues_details_id = models.AutoField(primary_key=True)
    issues = models.ForeignKey(issues, on_delete=models.CASCADE)
    issues_details_comment = models.CharField(max_length=1000, blank=True)
    issues_details_user = models.CharField(max_length=255, blank=True)
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
    old_value = models.TextField(blank=True)
    new_value = models.TextField(blank=True)
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
    revenue_types_name = models.CharField(max_length=255, blank=True)
    revenue_types_jan = models.CharField(max_length=3, blank=True)
    revenue_types_feb = models.CharField(max_length=3, blank=True)
    revenue_types_mar = models.CharField(max_length=3, blank=True)
    revenue_types_apr = models.CharField(max_length=3, blank=True)
    revenue_types_may = models.CharField(max_length=3, blank=True)
    revenue_types_jun = models.CharField(max_length=3, blank=True)
    revenue_types_jul = models.CharField(max_length=3, blank=True)
    revenue_types_aug = models.CharField(max_length=3, blank=True)
    revenue_types_sep = models.CharField(max_length=3, blank=True)
    revenue_types_oct = models.CharField(max_length=3, blank=True)
    revenue_types_nov = models.CharField(max_length=3, blank=True)
    revenue_types_dec = models.CharField(max_length=3, blank=True)

    def __str__(self):
        return str(self.revenue_types_name)

    class Meta:
        db_table="revenue_types"

class revenue_line_types(models.Model):
    revenue_line_types_id = models.AutoField(primary_key=True)
    revenue_line_types_name = models.CharField(max_length=255, blank=True)
    revenue_line_types_description = models.CharField(max_length=255, blank=True)
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
    expense_types_name = models.CharField(max_length=255, blank=True)
    expense_types_jan = models.CharField(max_length=3, blank=True)
    expense_types_feb = models.CharField(max_length=3, blank=True)
    expense_types_mar = models.CharField(max_length=3, blank=True)
    expense_types_apr = models.CharField(max_length=3, blank=True)
    expense_types_may = models.CharField(max_length=3, blank=True)
    expense_types_jun = models.CharField(max_length=3, blank=True)
    expense_types_jul = models.CharField(max_length=3, blank=True)
    expense_types_aug = models.CharField(max_length=3, blank=True)
    expense_types_sep = models.CharField(max_length=3, blank=True)
    expense_types_oct = models.CharField(max_length=3, blank=True)
    expense_types_nov = models.CharField(max_length=3, blank=True)
    expense_types_dec = models.CharField(max_length=3, blank=True)

    def __str__(self):
        return str(self.expense_types_name)

    class Meta:
        db_table="expense_types"

class expense_line_types(models.Model):
    expense_line_types_id = models.AutoField(primary_key=True)
    expense_line_types_name = models.CharField(max_length=255, blank=True)
    expense_line_types_description = models.CharField(max_length=255, blank=True)
    expense_line_types_prorata = models.CharField(max_length=3, blank=True)
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
    act_expense_description = models.CharField(max_length=55, blank=True)
    # max_digits widened 6 -> 10 (Aug 2026). At 6 the ceiling was EUR 9,999.99,
    # which silently blocked any larger invoice (a renovation, a boiler).
    act_expense_amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    act_expense_approved = models.CharField(max_length=3, blank=True)
    act_expense_paid = models.CharField(max_length=3, blank=True)
    act_expense_document = models.FileField(upload_to=expense_document_upload_path, blank=True, null=True)

    # ---- Invoice verification (two-way match) -----------------------------
    # Written by pages.services.invoice_verification when a document is
    # uploaded. Advisory only: nothing here ever alters a financial figure.
    act_expense_verify_status = models.CharField(
        max_length=20, blank=True,
        help_text='verified | mismatch | unverified | not_invoice | pending')
    act_expense_verify_checked_at = models.DateTimeField(blank=True, null=True)
    act_expense_verify_total = models.DecimalField(
        max_digits=10, decimal_places=2, blank=True, null=True,
        help_text='Payable total as read from the invoice.')
    act_expense_verify_date = models.DateField(blank=True, null=True)
    act_expense_verify_number = models.CharField(max_length=60, blank=True)
    act_expense_verify_supplier = models.CharField(max_length=120, blank=True)
    act_expense_verify_notes = models.TextField(blank=True)
    act_expense_verify_raw = models.TextField(
        blank=True, help_text='Full extraction payload - the audit record.')
    act_expense_verify_model = models.CharField(
        max_length=60, blank=True,
        help_text='Model + prompt version, so old verdicts stay interpretable.')

    def verify_badge(self):
        """(css_class, icon, label) for the list icon and the modal banner."""
        return {
            'verified':    ('success', 'fa-check-circle',        'Invoice verified'),
            'mismatch':    ('danger',  'fa-exclamation-triangle', 'Invoice does not match'),
            'unverified':  ('secondary', 'fa-question-circle',   'Not checked - review by eye'),
            'not_invoice': ('secondary', 'fa-file',              'Not an invoice'),
            'split':       ('info',    'fa-object-group',        'One invoice covering several expenses'),
        }.get(self.act_expense_verify_status, ('secondary', 'fa-file-invoice', 'Document attached'))

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
    # PH-1, 5 Oct 2026 - THE HOLDER AS A PERSON, BESIDE THE STRING.
    #
    # holder_name stays and keeps every row it has; this is added NULL
    # everywhere and nothing reads it yet. PA-1's filter still filters on
    # the string, and will until backfill_passport_holder has run and
    # somebody has looked at what it could not match.
    #
    # PROTECT, not SET_NULL: a register whose subject can be deleted out
    # from under it is not a register. Deleting a household member who
    # holds documents is refused until the documents are dealt with.
    holder = models.ForeignKey(
        'pages.HouseholdMember',
        on_delete=models.PROTECT,
        null=True, blank=True,
        related_name='passports',
        help_text='The household member this document belongs to. NULL '
                  'until the backfill has matched it to holder_name.',
    )
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
    abbreviation = models.CharField(max_length=10, blank=True, help_text='Singular short form (e.g., tsp, cup, g)')
    abbreviation_plural = models.CharField(max_length=10, blank=True, help_text='Plural short form (e.g., tsp, cups, g)')
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
    description = models.TextField(blank=True)
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
    notes = models.TextField(blank=True, help_text='Storage tips, substitutions, etc.')
    
    # === USDA FoodData Central nutrition data ===
    # All nutrition values are per 100g. The recipe nutrition calculator
    # scales these by the ingredient amount (after unit conversion).
    # Set when the ingredient is mapped to a USDA food via the mapping wizard.
    
    fdc_id = models.IntegerField(
        null=True, blank=True,
        help_text='USDA FoodData Central food ID (set when mapped to nutrition data)'
    )
    fdc_description = models.CharField(
        max_length=300, blank=True,
        help_text='USDA description of the matched food (for reference)'
    )
    fdc_data_type = models.CharField(
        max_length=30, blank=True,
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
    description = models.TextField(blank=True)
    created_date = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        db_table = "recipe_categories"
        verbose_name = "Recipe Category"
        verbose_name_plural = "Recipe Categories"
        ordering = ['name']

# HOW MUCH OF A RECIPE NAME GOES INTO A FILENAME - NL-1, 22 Oct 2026.
#
# A generated basename is recipe-{id}-{slug}-{14 digit stamp}.{ext}:
# 'recipe-' is 7, a six digit id is 6, two hyphens are 2, the stamp is
# 14, and '.jpeg' is 5 - 34 characters before any of the name. The
# longest directory, 'recipe_images_display/', is 22 more.
#
# 40 IS NOT A ROUND NUMBER, IT IS THE ONE THAT FITS. 40 + 34 + 22 = 96,
# inside the 255 the fields now hold AND inside the 100 they used to,
# so a tree that has somehow not run the migration still behaves
# rather than silently truncating. The first draft said 60, which is
# 116, and the gate below refused the round - correctly.
#
# The filename is not shown to anybody. A recipe called 'Pork Shoulder
# (Deboned, Rind-off) - Oven and Gas Braai' losing its last few words
# HERE costs nothing; losing its display copy cost four recipes a
# rebuild on every edit.
#
# A module constant and not a literal inside three functions, so a
# suite can read it and so the three agree by construction.
NAME_SLUG_CAP = 40


def recipe_image_upload_path(instance, filename):
    """Where a recipe's uploaded photo lives.

    THE SLUG IS BOUNDED - NL-1, 22 Oct 2026. Unbounded, a long recipe
    name generates a filename that does not fit the column, and Django
    truncates the stem and adds a random suffix rather than refusing.
    Four recipes on Live were left permanently stale that way, because
    display_copy_is_stale compares names and a truncated name can
    never match. NAME_SLUG_CAP keeps a generated basename near 100
    characters whatever the recipe is called.
    """
    ext = filename.split('.')[-1]
    recipe_name_slug = slugify(instance.recipe_name or 'recipe')[:NAME_SLUG_CAP]
    recipe_id = instance.recipe_id or 'new'
    timestamp = timezone.now().strftime('%Y%m%d%H%M%S')
    new_filename = f"recipe-{recipe_id}-{recipe_name_slug}-{timestamp}.{ext}"
    return os.path.join('recipe_images', new_filename)

def recipe_display_upload_path(instance, filename):
    """Where a derived display copy lives. PX-1, 13 Oct 2026.

    Beside the masters, not among them: recipe_images_display/ rather
    than recipe_images/. A later round that wants to count, archive or
    rebuild the originals can do it with a directory listing instead of
    a filename rule.
    """
    return os.path.join('recipe_images_display', filename)


# THE PHONE HERO ASKS FOR ABOUT 1170 REAL PIXELS - PX-2, 21 Oct 2026.
# Full-width at 390 CSS px and device-pixel-ratio 3. A round number is
# easier to check than a clever one, and it is a module constant
# rather than a literal inside the function so a suite can read it.
DISPLAY_FLOOR = 1200


def make_display_jpeg(field_file, quality=85):
    """The ONE place that knows how a display copy is made.

    PX-1, 13 Oct 2026. Called from Recipe.save() for new uploads and
    from the convert_recipe_photos command for the 324 already on the
    volume, so a photo converted today and one converted next year are
    the same photo. Returns JPEG bytes, or None if the source cannot be
    read - a recipe with an unreadable image is not a reason to refuse a
    save.

    NEVER SHRINKS, AND LIFTS THE SMALL ONES - PX-1 then PX-2.
    Measured 13 Oct: nothing in the library is over 1000px on the long
    edge, and the sizes the app draws want up to about 1170. Shrinking
    these would make a soft picture softer to save bytes the encoder
    gives up for nothing, so nothing is ever shrunk.

    AND 97 OF THE 324 ARE UNDER 500px, which is where PX-2 comes in.
    The recipe hero is 200x200 on a desktop and 150x150 on a tablet -
    both downscale, both sharp - but below 768px it is the full width
    of the screen at 240px tall. At 390 CSS px and device-pixel-ratio
    3 that wants about 1170 real pixels, so a 500px photo is stretched
    2.3x by the browser, with a cheap filter, on every page load.

    DOING IT ONCE, PROPERLY, HERE IS BETTER THAN BADLY, THERE. Lanczos
    plus a light unsharp mask invents no detail - a 500px photo will
    never be a 1600px photo - but it beats bilinear-in-a-browser, and
    the renders Demetri approved on 21 Oct show the difference: the
    weave of a tablecloth and the tines of a fork come back.

    THE FLOOR IS 1200 because 1170 is what the widest phone hero asks
    for and a round number is easier to check than a clever one.

    THE FLATTEN IS DEFENCE, NOT NEED. Measured the same day: 0 of 324
    images have a single non-opaque pixel, though 322 carry an alpha
    channel. If one ever does, white is what it lands on, chosen here
    rather than discovered later as a black rectangle.
    """
    import io
    from PIL import Image, ImageFilter

    if not field_file:
        return None
    try:
        field_file.open('rb')
        im = Image.open(field_file)
        im.load()
    except Exception:
        return None
    finally:
        try:
            field_file.close()
        except Exception:
            pass

    rgba = im.convert('RGBA')
    flat = Image.new('RGB', im.size, (255, 255, 255))
    flat.paste(rgba, mask=rgba.split()[3])

    # THE FLOOR - PX-2, 21 Oct 2026. Up only, never down.
    #
    # FLATTENED FIRST, SO THE SHARPEN HAS REAL PIXELS UNDER IT. An
    # unsharp mask over an alpha edge haloes the transparency rather
    # than the subject, and 322 of the 324 carry an alpha channel.
    long_edge = max(flat.size)
    if long_edge and long_edge < DISPLAY_FLOOR:
        scale = DISPLAY_FLOOR / float(long_edge)
        flat = flat.resize((max(1, int(round(flat.size[0] * scale))),
                            max(1, int(round(flat.size[1] * scale)))),
                           Image.LANCZOS)
        # A LIGHT HAND. 110 per cent at radius 1.6 was chosen against
        # real renders at device-pixel-ratio 3; heavier than this and
        # the edges ring, which reads as worse than soft.
        flat = flat.filter(ImageFilter.UnsharpMask(
            radius=1.6, percent=110, threshold=2))

    out = io.BytesIO()
    flat.save(out, 'JPEG', quality=quality, optimize=True,
              progressive=True)
    return out.getvalue()


def store_display_jpeg(recipe, data):
    """Put JPEG bytes at the display copy's PROPER name. SD-1, 22 Oct 2026.

    THE ONE PLACE THAT KNOWS HOW A DISPLAY COPY IS STORED, as
    make_display_jpeg has been the one place that knows how one is made
    since PX-1. Both callers go through it: the convert_recipe_photos
    command and Recipe.save().

    WHY IT EXISTS. FieldFile.save() asks the storage for an AVAILABLE
    name, and FileSystemStorage answers one that is not taken - the name
    you asked for with a random seven-character suffix on it. Writing a
    display copy over itself therefore produced

        recipe-1-alpha-20261022063218_xUkNf5M.jpg

    and three consequences. The old copy was never deleted, so a rebuild
    of 324 photos left 324 orphans. display_copy_is_stale compares the
    stored name with display_name_for(original) - by design, so that
    there is no column to forget to clear - and the suffixed name is
    never equal to it, so every recipe became permanently stale. And
    permanently stale means save() rebuilds the copy every time the
    recipe is edited, leaving another orphan each time.

    SO IT DELETES THE TARGET PATH FIRST and then writes there. One
    path, asked of the storage by exact name - not a pattern, not a
    glob, not a listing. The file deleted is the one about to be
    replaced at the same path, and nothing else on the volume can be
    reached from here.

    AND IT CHECKS RATHER THAN HOPES. If the stored name still is not
    the name asked for, this returns False and says nothing more; the
    caller decides. That check is the thing nobody did before, and it
    is why this round exists.

    Returns True when the display copy is on the volume under its
    proper name, False otherwise. Never raises: a picture is worth less
    than the recipe it belongs to, which is PX-1's rule and still true.
    """
    from django.core.files.base import ContentFile
    try:
        want = display_name_for(recipe.recipe_image.name)
        field = recipe.recipe_image_display
        target = recipe_display_upload_path(recipe, want)
        if field.storage.exists(target):
            field.storage.delete(target)
        field.save(want, ContentFile(data), save=False)
        return os.path.basename(field.name) == want
    except Exception:
        return False


def file_holders(model, name, fields):
    """How many rows of this model name this file, across these fields.

    SI-1, 22 Oct 2026. Asked of the DATABASE, by exact path, because
    that is the only place the answer lives: a file on a media volume
    carries no record of who points at it.

    ACROSS FIELDS, not one field. A display copy's path can be named by
    recipe_image_display on any row, and asking about one field would
    answer 'nobody' while somebody was plainly standing there.
    """
    if not name:
        return 0
    total = 0
    for field_name in fields:
        total += model._default_manager.filter(**{field_name: name}).count()
    return total


def let_go_of_file(instance, field_name):
    """Clear the reference and return the name. DELETES NOTHING. SI-1.

    THE BYTES MUST OUTLIVE THE SAVE. edit_recipe used to call
    field.delete(save=False) and then recipe.save(), and a save that
    fails after that leaves the file gone and the row still naming it -
    which is exactly the MISSING state the 22 October rebuild found on
    Live. It was demonstrated on 22 October by a test POST that omitted
    difficulty_level: the except fired, the redirect looked like
    success, and the photo was already destroyed.

    So this half only lets go. delete_unheld does the other half, after
    the save has committed, and a failed save therefore costs nothing.
    """
    field = getattr(instance, field_name, None)
    name = getattr(field, 'name', None)
    if not name:
        return None
    setattr(instance, field_name, None)
    return name


def delete_unheld(model, names, fields):
    """Delete the bytes of each name no row still holds. SI-1.

    CALLED AFTER THE SAVE, never before - see let_go_of_file.

    AND IT COUNTS FIRST. A duplicated recipe used to share its photo
    path with the recipe it came from, so deleting on the strength of
    one row letting go destroyed the other row's picture. That is how
    71 Cottage Pie and 336 Beans, Edamame lost theirs.

    One name at a time, by exact path, asked of the storage. No
    pattern, no listing, no glob: a delete on a media volume that takes
    anything wider than a path is a delete nobody can bound.

    Returns the names whose bytes were removed. Never raises - a
    leftover file costs disk, and an exception here would lose the edit
    that has already been saved.
    """
    from django.core.files.storage import default_storage

    gone = []
    for name in [n for n in names if n]:
        if file_holders(model, name, fields):
            # SOMEBODY ELSE IS STANDING ON IT. The last row out turns
            # off the light.
            continue
        try:
            if default_storage.exists(name):
                default_storage.delete(name)
                gone.append(name)
        except Exception:
            pass
    return gone


def unshare_file(instance, field_name):
    """Give this row its OWN copy of the file its field names. SI-1.

    For a row made by copying another - duplicate_recipe sets pk to
    None and saves, which copies the PATH, not the picture.

    THE NEW NAME IS NOT INVENTED HERE. The bytes are saved back through
    the field, which runs upload_to, and recipe_image_upload_path
    builds its name from the row's own id and a fresh timestamp. A
    second naming scheme in this function is a second thing to keep in
    agreement with display_name_for.

    Returns True when the field now names a file of its own. On a file
    that cannot be read the field is CLEARED and False returned: a row
    pointing at nothing is honest, and leaving it pointing at somebody
    else's file is the fault this round exists to end.
    """
    from django.core.files.base import ContentFile

    field = getattr(instance, field_name, None)
    old = getattr(field, 'name', None)
    if not old:
        return False
    try:
        field.open('rb')
        data = field.read()
    except Exception:
        setattr(instance, field_name, None)
        return False
    finally:
        try:
            field.close()
        except Exception:
            pass
    field.save(os.path.basename(old), ContentFile(data), save=False)
    return field.name != old


def display_name_for(original_name):
    """The display copy's filename for a given original. PX-1.

    The stem is the original's, so the two are obviously a pair on a
    directory listing AND so staleness is decidable without a database
    column: the original's name already carries a timestamp, so a
    re-upload produces a new stem and the old display copy stops
    matching.
    """
    return os.path.splitext(os.path.basename(original_name))[0] + '.jpg'


def recipe_document_upload_path(instance, filename):
    """Where a recipe's document lives. Slug bounded - NL-1, 22 Oct 2026."""
    ext = filename.split('.')[-1]
    recipe_name_slug = slugify(instance.recipe_name or 'recipe')[:NAME_SLUG_CAP]
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
    recipe_description = models.TextField(blank=True, help_text='Brief description or introduction')
    
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
    difficulty_level = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES, blank=True)
    # NL-1, 22 Oct 2026 - 255, NOT THE DEFAULT 100. Four recipes on
    # Live generated a display name that did not fit, and Django
    # truncated the stem mid-timestamp and suffixed it, which left
    # them permanently stale. See apply_name_width.
    recipe_image = models.ImageField(upload_to=recipe_image_upload_path, blank=True, null=True, max_length=255)
    # PX-1, 13 Oct 2026 - THE DERIVED DISPLAY COPY, never uploaded
    # to directly. editable=False keeps it out of every ModelForm in
    # the application, because a field nobody may set by hand cannot
    # drift from the original it is derived from.
    recipe_image_display = models.ImageField(
        upload_to=recipe_display_upload_path, blank=True, null=True,
        editable=False,
        # NL-1, 22 Oct 2026 - AND THIS IS THE ONE THAT OVERFLOWED.
        # recipe_images_display/ is 22 characters before the filename
        # starts, which is why this field hit the limit and
        # recipe_images/ did not.
        max_length=255,
        help_text='Derived JPEG of recipe_image. Rebuilt by '
                  'manage.py convert_recipe_photos --write.')
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
    created_by = models.CharField(max_length=255, blank=True, help_text='User who created this recipe')
    
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
    
    @property
    def photo_url(self):
        """The URL to DRAW this recipe with. PX-1, 13 Oct 2026.

        Display copy, else the original, else None. Fifteen call sites
        ask this instead of reaching for recipe_image.url themselves -
        eight Python serialisers and seven templates - so the question
        of which file to serve is answered once.

        The fallback is load-bearing while the batch runs: a recipe
        whose display copy does not exist yet draws from its original
        and looks exactly as it does today.
        """
        if self.recipe_image_display:
            return self.recipe_image_display.url
        if self.recipe_image:
            return self.recipe_image.url
        return None

    def display_copy_is_stale(self):
        """True when a display copy should be built. PX-1.

        Asked of the NAMES, not of a flag: the original's filename
        carries a timestamp, so a re-upload gives a new stem and the old
        display copy stops matching. No column to forget to clear.
        """
        if not self.recipe_image:
            return False
        if not self.recipe_image_display:
            return True
        want = display_name_for(self.recipe_image.name)
        return os.path.basename(self.recipe_image_display.name) != want

    def save(self, *args, **kwargs):
        # Auto-calculate total_time if not provided
        if not self.total_time and self.prep_time and self.cook_time:
            self.total_time = self.prep_time + self.cook_time
        super().save(*args, **kwargs)
        # PX-1, 13 Oct 2026 - BUILD THE DISPLAY COPY ON UPLOAD, so the
        # library cannot drift back. A one-time batch alone regresses the
        # moment somebody adds a recipe.
        #
        # AFTER super().save(), because on a fresh upload recipe_image is
        # still an in-memory file until Django has stored it. The second
        # write names its one field, and a failure here must never lose
        # the recipe the person just saved - the picture is worth less
        # than the recipe.
        #
        # THROUGH store_display_jpeg SINCE SD-1, 22 Oct 2026. This block
        # used to call field.save() directly, which asks the storage for
        # an AVAILABLE name and gets the one you asked for with a random
        # suffix whenever the target already exists. A recipe left
        # permanently stale by that - see store_display_jpeg - came
        # through here on EVERY edit and left another orphan each time.
        if self.display_copy_is_stale():
            try:
                data = make_display_jpeg(self.recipe_image)
                if data is not None and store_display_jpeg(self, data):
                    super().save(update_fields=['recipe_image_display'])
            except Exception:
                pass
    
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
        help_text='Additional preparation notes'
    )
    
    ingredient_order = models.IntegerField(default=0, help_text='Display order in recipe')
    ingredient_group = models.CharField(
        max_length=100, 
        blank=True, 
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
    ingredient_group = models.CharField(max_length=100, blank=True, help_text='Ingredient grouping')  # ADD THIS
    order = models.IntegerField(default=0, help_text='Display order')
    
    def __str__(self):
        return self.ingredient_text
    
    class Meta:
        db_table = "recipe_ingredient_text"
        verbose_name = "Recipe Ingredient (Text)"
        verbose_name_plural = "Recipe Ingredients (Text)"
        ordering = ['ingredient_group', 'order']  # UPDATED to order by group first


def instruction_image_upload_path(instance, filename):
    """Where a step photo lives. Slug bounded - NL-1, 22 Oct 2026."""
    ext = filename.split('.')[-1]
    recipe_name_slug = slugify(instance.recipe.recipe_name or 'recipe')[:NAME_SLUG_CAP]
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
        help_text='e.g., "Preparation", "Cooking", "Assembly"'
    )
    time_estimate = models.IntegerField(
        blank=True, 
        null=True, 
        help_text='Estimated time for this step in minutes'
    )
    
    # Optional step image
    # NL-1, 22 Oct 2026 - 255, for the same reason as the other two.
    # No step image has overflowed yet; this one is widened because a
    # rule that holds for two of three fields is a rule somebody will
    # trip over on the third.
    step_image = models.ImageField(upload_to=instruction_image_upload_path, blank=True, null=True, max_length=255)
    
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


class MealEntry(models.Model):
    """One meal on one date. MN-1, 18 Oct 2026 - release 3.

    THE CALENDAR IS THE PLAN. This replaces the chain
    MealPlan -> MealPlanDay -> MealPlanRecipe, where a meal could only
    exist inside a named box with a start and an end date. Those boxes
    could overlap, could not exceed seven days, and threw meals away
    when their dates changed - which was C13, C17 and half of release
    1's group C between them.

    A meal has a DATE. That is the whole model change.

    NO WORKSPACE, BY DECISION - 18 Oct 2026. The design record gives
    this table one. `Recipe` has no workspace at all and its created_by
    is a plain CharField, so a tenanted meal holding an untenanted
    recipe would be precisely the inconsistency MP-1 recorded in
    Workspace's own docstring. If recipes are ever tenanted, meal
    entries follow in that round, in one migration.

    RECIPE IS NULLABLE, because not every slot is a recipe. A note -
    "Eat out", "At Yiayia's" - makes an empty night a DECISION rather
    than a gap, and stays off the shopping list. Push 2 writes those;
    the column is here from the start because adding it later would be
    a second migration for a column this shape already implies.

    CASCADE ON recipe, which is what MealPlanRecipe did. Deleting a
    recipe you no longer want takes it off future plans too, and the
    alternative - PROTECT - would refuse to delete any recipe that had
    ever been planned.
    """
    meal_entry_id = models.AutoField(primary_key=True)
    date = models.DateField(db_index=True)
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE, null=True, blank=True,
        related_name='meal_entries',
        help_text='The recipe planned for this date, or blank for a note')
    note = models.CharField(
        max_length=200, blank=True, default='',
        help_text='A planned night that is not a recipe - Eat out, Leftovers')
    servings = models.IntegerField(
        default=4,
        help_text='How many this meal is cooked for. Scales the shopping list.')
    sort_order = models.IntegerField(default=0)
    leftover_of = models.ForeignKey(
        'self', on_delete=models.CASCADE, null=True, blank=True,
        related_name='leftovers',
        help_text='Set when this meal is the leftovers of an earlier one. '
                  'It costs nothing on the shopping list.')
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='meal_entries')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'meal_entries'
        ordering = ['date', 'sort_order', 'meal_entry_id']
        verbose_name_plural = 'Meal entries'

    def __str__(self):
        what = self.recipe.recipe_name if self.recipe else (self.note or 'Meal')
        return '%s on %s' % (what, self.date.strftime('%a %d %b %Y'))

    @property
    def servings_multiplier(self):
        """How far to scale this meal's ingredients.

        The same guarded expression MD-1 put on MealPlanRecipe: Decimal
        because every quantity downstream is one and mixing the two
        raises, and `or 1` because a recipe with no yield recorded
        should scale by one rather than refuse to be shopped for.
        """
        if not self.recipe:
            return Decimal('0')
        return Decimal(self.servings) / Decimal(self.recipe.servings or 1)

    @property
    def counts_on_shopping_list(self):
        """A note buys nothing, and leftovers were bought once already."""
        return bool(self.recipe) and self.leftover_of_id is None


class Menu(models.Model):
    """A saved SPAN OF DAYS, kept by NAME rather than by date.

    MN-1, 18 Oct 2026. Repeat copies last week. A Menu is for the days
    you come back to months later - Christmas, girls visiting, the
    usual rotation - so it holds DAY OFFSETS and not dates.

    MN-2, 21 Oct 2026 - IT WAS NEVER A WEEK. This said "DAY INDEXES, 0
    to 6" and the table never agreed: MenuItem.day_index has read "0 is
    the first day of the menu, not a weekday" since the day it was
    written. What held a menu to seven days was save_menu and
    apply_menu, which now take a range and a landing date. The ceiling
    is MENU_MAX_DAYS, 92, and it lives in the view with the rule it
    serves.

    THE COLUMN KEEPS ITS NAME. day_offset would be better English;
    renaming a column on a live table buys nothing this docstring does
    not say.
    """
    menu_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=120)
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='menus')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'menus'
        ordering = ['name']

    def __str__(self):
        return self.name


class MenuItem(models.Model):
    """One meal in a saved menu, on a day INDEX. MN-1, 18 Oct 2026."""
    menu_item_id = models.AutoField(primary_key=True)
    menu = models.ForeignKey(Menu, on_delete=models.CASCADE,
                             related_name='items')
    day_index = models.IntegerField(
        default=0, help_text='0 is the first day of the menu, not a weekday')
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE,
                               null=True, blank=True,
                               related_name='menu_items')
    note = models.CharField(max_length=200, blank=True, default='')
    servings = models.IntegerField(default=4)
    sort_order = models.IntegerField(default=0)

    class Meta:
        db_table = 'menu_items'
        ordering = ['day_index', 'sort_order', 'menu_item_id']

    def __str__(self):
        what = self.recipe.recipe_name if self.recipe else (self.note or 'Meal')
        return '%s, day %d of %s' % (what, self.day_index + 1, self.menu.name)


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
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=50, blank=True)
    photo = models.ImageField(upload_to='contacts/', blank=True, null=True)
    notes = models.TextField(blank=True)
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
    email = models.EmailField(blank=True)
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
    notes = models.TextField(blank=True)
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
    
    # ---------------------------------------------------------------
    # CC-1, 15 Oct 2026 - A CALENDAR ASKS A DIFFERENT QUESTION.
    #
    # get_next_occurrence() answers "when is this next?" and returns ONE
    # date. A month grid needs "does this fall in THIS month?", and the
    # two are not the same question: asked the first way, a birthday on
    # 20 November exists in November 2026 and in no other November ever,
    # and the 1st to the 14th of the current month vanish the moment the
    # 15th arrives. Demetri found the first half of that as a blank
    # November 2027; the second half nobody had noticed.
    #
    # get_next_occurrence is LEFT ALONE. The dashboard, the timeline
    # countdown and the notification scheduler all want "when is this
    # next?" and are right to.
    def occurrences_in(self, year, month):
        """Every occurrence of this event inside the given month."""
        if not self.is_recurring:
            d = self.event_date
            return [d] if (d.year == year and d.month == month) else []
        if self.event_date.month != month:
            return []
        try:
            return [self.event_date.replace(year=year)]
        except ValueError:
            # 29 February in a non-leap year, handled the same way
            # get_next_occurrence handles it - on the 28th.
            return [self.event_date.replace(year=year, day=28)]

    # AND THE AGE HAS TO BE TAKEN AT THE OCCURRENCE BEING DRAWN.
    # get_age() derives from get_next_occurrence(), so once a grid can
    # show any year it would print November 2026's ages in November 2027.
    def age_at(self, when):
        """Age at a given occurrence, for birthdays with a known year."""
        if self.event_type == 'birthday' and self.event_date.year != 1900 \
                and when:
            return when.year - self.event_date.year
        return None

    def years_at(self, when):
        """Years at a given occurrence, for anniversaries."""
        if self.event_type == 'anniversary' and self.event_date.year != 1900 \
                and when:
            return when.year - self.event_date.year
        return None

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
    
    #: An event TYPE is a category, not a verdict. This used to be
    #: get_color_class(), returning Bootstrap names - and 'danger' is the
    #: red this system uses for a failure, 'success' the green it uses
    #: for one that worked. An anniversary was painted in the error
    #: colour and a custom event in the success colour, on three screens.
    #:
    #: base owns a categorical chip set for exactly this: five hues that
    #: mean nothing but themselves. The four types map onto four of them.
    #: The value is a class name, used as-is - not a Bootstrap suffix, so
    #: a template writes `class="alv-tag {{ event.tone_class }}"`.
    TONE_CLASSES = {
        'birthday': 'alv-tag-sky',
        'nameday': 'alv-tag-moss',
        'anniversary': 'alv-tag-clay',
        'custom': 'alv-tag-plum',
    }

    @property
    def tone_class(self):
        """The categorical chip class for this event's type."""
        return self.TONE_CLASSES.get(self.event_type, 'alv-tag-slate')
    
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
        ('expense_mismatch', 'Expense Invoice Uploaded'),
        ('friday_status_report_supervisor', 'Friday Status Report (Submitted by Supervisor)'),
        ('friday_status_report_staff', 'Friday Status Report (Submitted by Staff)'),
        ('invoice_paid', 'Invoice Marked as Paid'),
        ('issue_comments_daily', 'Daily Issue Comments Report'),
        ('issue_comment_urgent', 'Urgent Issue Comment Alert'),
        ('physical_invoice_review', 'Physical Invoices Awaiting Approval'),
        ('physical_invoice_client', 'Physical Invoice to Client'),
        # CR-2, 27 Oct 2026 - a cash receipt emailed to its payer. The
        # payer's own address is always a To; this card adds any further
        # To and any CC.
        ('cash_receipt_payer', 'Cash Receipt to Payer'),
        # THE 16TH, added by Section A round A1: who hears about it
        # when somebody asks for a password link. Configurable from
        # Administration -> Notification Settings rather than
        # hardcoded - and see notification_settings() in
        # views/notifications.py, which filters these choices
        # through a SECOND, hardcoded list. A type missing from that
        # list renders on no screen and reports no error.
        #                                   [test_auth_flow.py]
        ('password_reset_requested', 'Password Reset Requested'),
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
    notes = models.TextField(blank=True)
    
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
    """A tenancy boundary for Personal-module data (Passports,
    Celebrations).

    Every tenanted record references exactly one Workspace; users belong to
    exactly one Workspace (via UserProfile.workspace) and see only the data
    within it.

    MP-1, 18 Oct 2026. THIS DOCSTRING USED TO NAME RECIPES among the
    tenanted records, twice - "(Passports, Celebrations, Recipes)" and
    "(passport, celebration, recipe, ingredient, etc.)". Only Passports and
    Celebrations actually carry the field. `Recipe` has no workspace at all -
    its `created_by` is a plain CharField, not even a user link - so recipes,
    ingredients and meal plans are global across the installation.

    It cost a session: this text sent MP-1 looking for meal-plan scoping that
    does not exist. It is a recorded position now rather than an oversight.
    Demetri decided on 18 Oct that all users see all meal plans, and the code
    already agreed with him - plans built from global recipes being global
    follows the module around them. The cost is nil while there is one
    household. If a second one ever uses the system, recipes and meal plans
    are the two things that would not separate.

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
    line_type = models.CharField(max_length=255, blank=True,
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

    source = models.CharField(max_length=30, blank=True,
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


# How far back a baseline snapshot is dated.
#
# Deliberately remote. A baseline is not a claim about a particular year - it
# says "this is what the figure was until something changed it". Date it too
# recently and any earlier year falls outside the resolver's range, the source
# drops out of the result, and the caller falls back to the LIVE row - which
# always holds TODAY's value. The symptom is a past year quietly showing the
# current figure, which looks plausible and is wrong.
FH_BASELINE_DATE = _fh_date(2000, 1, 1)


def _ensure_baseline(prop, kind, source_pk, line_type,
                     before_months, before_amount, user):
    """Preserve what a figure held BEFORE its first-ever recorded change.

    The resolver handles "no history at all" gracefully: the source is absent
    from the result and the caller keeps the live cells. It does NOT handle
    "history that starts too late" - every month before the earliest snapshot
    resolves to None, the year totals zero, and the P&L drops the row entirely.

    So the first edit of a long-standing line would erase its own past. This
    closes that window by writing the previous values at FH_BASELINE_DATE, once,
    the first time a line is touched.

    Fail-safe: never raises, so a history problem cannot break the user's save.
    """
    try:
        if FinancialFigureHistory.objects.filter(kind=kind,
                                                 source_pk=source_pk).exists():
            return None                      # not the first change; nothing to do
        if not any(v for v in before_months.values() if v):
            return None                      # nothing was budgeted before
        return FinancialFigureHistory.objects.create(
            prop=prop, kind=kind, source_pk=source_pk, line_type=line_type,
            effective_date=FH_BASELINE_DATE, amount=before_amount,
            source='baseline', changed_by=user, **before_months,
        )
    except Exception:
        _fh_log.exception('_ensure_baseline failed (save itself was not affected)')
        return None


def ensure_expense_baseline(exp, before_months, before_amount, *, user=None):
    """Baseline for a budgeted expense. `before_months` is {month: value} using
    the bare month names, as the history columns are named."""
    return _ensure_baseline(
        exp.prop, FinancialFigureHistory.KIND_BUDGET, exp.expense_id,
        str(exp.expense_line_types), before_months, before_amount, user)


def ensure_revenue_baseline(rev, before_months, before_amount, *, user=None):
    """Baseline for a direct/seasonal revenue row."""
    return _ensure_baseline(
        rev.prop, FinancialFigureHistory.KIND_REVENUE, rev.revenue_id,
        str(rev.revenue_line_types), before_months, before_amount, user)


def _open_baseline(prop, kind, source_pk, line_type, user):
    """Record that a figure was ZERO before its row existed.

    The mirror image of _ensure_baseline. That one preserves what a
    long-standing figure held before its first change; this one states that a
    brand-new row held nothing at all beforehand.

    Without it a new row has no history covering earlier years, so the resolver
    leaves it out of the result entirely and the caller falls back to the LIVE
    cells - which always hold today's figure. A monthly expense created in
    August 2026 then reads as a full year of spend in 2024 and 2025, while
    January to July of 2026 resolve to None and are dropped from the P&L.

    With it, the effective date the user types is the only thing that decides
    which years the figure reaches - including backdating a line that has been
    running for years, and forward-dating next year's budget.

    Fail-safe: logs and returns None rather than raising, so a history problem
    can never break the save that triggered it.
    """
    try:
        if FinancialFigureHistory.objects.filter(kind=kind,
                                                 source_pk=source_pk).exists():
            return None
        zero = Decimal('0')
        return FinancialFigureHistory.objects.create(
            prop=prop, kind=kind, source_pk=source_pk, line_type=line_type,
            effective_date=FH_BASELINE_DATE, amount=zero,
            source='opening', changed_by=user,
            **{m: zero for m in _FH_MONTHS},
        )
    except Exception:
        _fh_log.exception('_open_baseline failed (save itself was not affected)')
        return None


def ensure_expense_opening(exp, *, user=None):
    """Opening zero snapshot for a newly created budgeted expense row."""
    return _open_baseline(
        exp.prop, FinancialFigureHistory.KIND_BUDGET, exp.expense_id,
        str(exp.expense_line_types), user)


def ensure_revenue_opening(rev, *, user=None):
    """Opening zero snapshot for a newly created revenue row."""
    return _open_baseline(
        rev.prop, FinancialFigureHistory.KIND_REVENUE, rev.revenue_id,
        str(rev.revenue_line_types), user)


def prorata_reconcile(total, amounts):
    """Round a pro-rata split to 2dp so the shares sum EXACTLY to `total`.

    Rounding each share on its own leaves a residual: ten shares of a 6,600
    charge came to 6,599.98, and nothing ever placed the missing two cents.
    Small, but it recurs on every recalculation of every pro-rata line, and the
    P&L then reports a charge that does not match the bill.

    The remainder goes to the LARGEST share, where it is proportionally least
    visible - two cents on 1,448.90 rather than on 195.76.

    Returns a list of Decimals in the order given. Never raises: bad input
    comes back rounded but unreconciled rather than blowing up a save.
    """
    q = Decimal('0.01')
    try:
        target = Decimal(str(total)).quantize(q, rounding=ROUND_HALF_UP)
        out = [Decimal(str(a if a is not None else 0)).quantize(
            q, rounding=ROUND_HALF_UP) for a in amounts]
    except (InvalidOperation, TypeError, ValueError):
        _fh_log.exception('prorata_reconcile could not parse its input')
        return [a for a in amounts]

    if not out:
        return out

    residual = target - sum(out)
    if residual:
        biggest = max(range(len(out)), key=lambda i: out[i])
        out[biggest] = out[biggest] + residual
    return out


def purge_figure_history(kind, source_pk):
    """Delete every snapshot for a source row being removed outright.

    The counterpart to a closing snapshot. "Stop it from a date" keeps the row
    and its past; "remove it completely" means the figure never happened, so
    its history goes too.

    Deleting the snapshots is the whole point rather than a tidy-up: leaving
    them behind is what creates orphans - rows pointing at an id nothing owns,
    unreachable by the resolver and waiting to attach themselves to whatever
    is unlucky enough to be given that id later.

    Deliberately NOT fail-safe. It runs inside the same transaction as the
    delete, and quietly leaving history behind is the failure being fixed.
    """
    deleted, _ = FinancialFigureHistory.objects.filter(
        kind=kind, source_pk=source_pk).delete()
    return deleted


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
def resolve_year_months_bulk(prop_ids, kind, year, with_sources=False):
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
    prov = {}
    for src, versions in by_src.items():
        vals = []
        srcs = []
        for m in range(1, 13):
            chosen = None
            for v in versions:              # ascending by effective_date
                if (v.effective_date.year, v.effective_date.month) <= (year, m):
                    chosen = v
                else:
                    break
            vals.append(getattr(chosen, _FH_MONTHS[m - 1]) if chosen is not None else None)
            # WHICH SNAPSHOT ANSWERED THIS MONTH.
            #
            # Recorded in the same loop that chooses it, so provenance cannot
            # drift from the figure. A caller asking "does this year straddle
            # a change" would otherwise have to re-implement the choice, and
            # two answers to one question is how this system gets hurt.
            #
            # ONLY WHEN ASKED. Reading the primary key unconditionally made
            # this touch an attribute the caller never needed, and a suite
            # whose stub row legitimately has no pk died on it. A default
            # caller must be able to hand this function anything with the
            # thirteen fields it actually reads.
            if with_sources:
                srcs.append(chosen.financial_figure_history_id
                            if chosen is not None else None)
        out[src] = vals
        if with_sources:
            prov[src] = srcs
    return (out, prov) if with_sources else out


# =============================================================================
# Effective-dated property valuations (year-aware Value Increase %).
# Reuses FinancialFigureHistory with kind='valuation': one append-only row per
# valuation change, source_pk = prop_values_id, amount = the current value at
# that point. A property's Value Increase for a year uses the value in force at
# the END of that year — so a value entered in 2026 doesn't retro-apply to 2023.
# No new table / schema migration: kind is stored as the raw string 'valuation'.
# =============================================================================
KIND_VALUATION = 'valuation'


def _fh_today():
    from datetime import date as _d
    return _d.today()


KIND_ACTUAL_EXPENSE = 'expense_actual'   # ad-hoc act_expense amount amendments


def record_actual_expense_history(exp, effective_date=None, *, source='actual', user=None):
    """Append-only log of an `act_expense` amount.

    Why this exists: the amount captured at creation is an ESTIMATE (the work
    has not been done). When the invoice arrives higher, the superuser
    un-approves, the amount is edited and it is re-approved - and the original
    approved figure is overwritten and lost. Logging each value makes
    "which suppliers routinely exceed their estimate" answerable.

    Stored as a raw kind string (like KIND_VALUATION) so no migration to
    KIND_CHOICES is needed. Fail-safe: never raises, so a history problem
    cannot break the user's save.
    """
    try:
        if exp is None or exp.act_expense_amount is None:
            return None
        return FinancialFigureHistory.objects.create(
            prop=exp.prop, kind=KIND_ACTUAL_EXPENSE,
            source_pk=exp.act_expense_id, line_type='Actual expense',
            effective_date=effective_date or exp.act_expense_date or _fh_today(),
            amount=exp.act_expense_amount,
            source=source, changed_by=user,
        )
    except Exception:
        _fh_log.exception('record_actual_expense_history failed (save itself was not affected)')
        return None


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


# =============================================================================
# OWNED FROM - OF-3, 28 Oct 2026.
#
# His rules, agreed 28 October:
#   - a property is owned from its first lease start (or the date typed on
#     the property, which wins); the gap between buying and first letting
#     is accepted;
#   - no budget, no revenue, in a month before the Owned-from month (any
#     part of a month counts as the month);
#   - OPTION B for pro-rata lines: each owned property keeps its own share,
#     and the share of a property not yet owned simply drops. His words:
#     "the earlier years would be more accurate because we don't burden
#     them with the full amount."
#
# ONE implementation, used by the P&L, its drill-downs, the expense matrix
# and Financial Indicators - so no two screens can disagree about a month.
# =============================================================================
def property_owned_from(prop):
    """The date `prop` counts from, or None for "owned all along"."""
    if getattr(prop, 'prop_owned_from', None):
        return prop.prop_owned_from
    return tenant.objects.filter(prop_id=prop.pk).exclude(
        tenant_lease_start_date__isnull=True).aggregate(
            _m=Min('tenant_lease_start_date'))['_m']


def owned_from_map(prop_ids):
    """{prop_id: date or None} for many properties, in two queries."""
    ids = [i for i in set(prop_ids) if i is not None]
    if not ids:
        return {}
    out = dict(props.objects.filter(prop_id__in=ids)
               .values_list('prop_id', 'prop_owned_from'))
    need = [i for i, d in out.items() if not d]
    if need:
        for pid, d in (tenant.objects.filter(prop_id__in=need)
                       .exclude(tenant_lease_start_date__isnull=True)
                       .values('prop_id')
                       .annotate(_m=Min('tenant_lease_start_date'))
                       .values_list('prop_id', '_m')):
            out[pid] = d
    return out


def owned_months(owned_from, year):
    """Twelve booleans: is the property owned in each month of `year`?"""
    if owned_from is None:
        return [True] * 12
    return [(year, m) >= (owned_from.year, owned_from.month)
            for m in range(1, 13)]


def apply_owned_from(values, owned_from, year):
    """`values` (twelve months) with every month before Owned From as 0."""
    mask = owned_months(owned_from, year)
    return [v if mask[i] else _fh_Decimal('0') for i, v in enumerate(values)]


def budget_year_months(expense_rows, year, with_sources=False):
    """{expense_id: twelve figures} for `year`, for EVERY row given.

    Each row resolved from its effective-dated history exactly as before
    (rows with no history keep their live cells), then every month before
    the property's Owned From set to 0. Pro-rata rows are no exception:
    that IS Option B - the unowned share drops, the owned shares stay.
    With with_sources=True also returns the resolver's provenance map.
    """
    rows = list(expense_rows)
    pids = sorted({r.prop_id for r in rows if r.prop_id is not None})
    res = resolve_year_months_bulk(pids, FinancialFigureHistory.KIND_BUDGET,
                                   year, with_sources=with_sources)
    vmap, prov = res if with_sources else (res, None)
    ofm = owned_from_map(pids)
    out = {}
    for r in rows:
        v = vmap.get(r.expense_id)
        if v is None:
            v = [getattr(r, 'expense_' + m, 0) or 0 for m in _FH_MONTHS]
        out[r.expense_id] = apply_owned_from(list(v), ofm.get(r.prop_id), year)
    return (out, prov) if with_sources else out


def lease_monthly_rent_levies(prop, year, today=None):
    """(rent[12], levies[12], has_leases) for a property/year from its leases."""
    today = today or _fh_date.today()
    leases = list(tenant.objects.filter(prop=prop))
    rent = [0.0] * 12
    lev = [0.0] * 12
    if not leases:
        return rent, lev, False
    # A property that is no longer Active gets no PROJECTION.
    #
    # _lease_month's 'assumed' tag carries the most recent lease forward at
    # today's rent for months nothing covers. That is right for a live property
    # between tenants; for one that has been sold it would invent rent for every
    # year after the sale - which matters now that the P&L no longer filters
    # inactive properties out.
    #
    # Only the projection is suppressed. Real, dated leases still resolve
    # normally, so the years the property actually earned are untouched.
    _projectable = (getattr(prop, 'prop_status', 'Active') or 'Active') == 'Active'
    for m in range(1, 13):
        _t, _l, r, v = _lease_month(leases, year, m, today)
        if _t == 'assumed' and not _projectable:
            r, v = 0, 0
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
    # OF-3, 28 Oct 2026: nothing counts before the property's Owned From.
    # Lease rent cannot predate the first lease anyway; this is for the
    # revenue table (seasonal and ancillary rows) and a typed date that is
    # later than the first lease. Table rows are handed back as unsaved
    # COPIES when a month is masked - never save what this returns.
    _mask = owned_months(property_owned_from(prop), year)
    if not has:
        return [_owned_copy(r, _mask) for r in prop.revenue_set.all()]
    rent = [v if _mask[i] else 0 for i, v in enumerate(rent)]
    lev = [v if _mask[i] else 0 for i, v in enumerate(lev)]
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
            rows.append(_owned_copy(r, _mask))
    return rows


def _owned_copy(r, mask):
    """`r` itself when every month is owned, else an unsaved copy with the
    unowned months at 0 - the database row is never touched."""
    if all(mask):
        return r
    import copy as _copy
    c = _copy.copy(r)
    for i, mm in enumerate(_FH_REV_MON):
        if not mask[i]:
            setattr(c, 'revenue_' + mm, _fh_Decimal('0'))
    return c


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
    # OF-3, 28 Oct 2026: "in service from" is now the property's Owned From
    # (the first lease start unless a date is typed on the property), and
    # the months come from the same helper the P&L uses - so the two
    # cannot disagree about a single month.
    total = _fh_Decimal('0')
    for vals in budget_year_months(prop.expense_set.all(), year).values():
        for v in vals:
            total += (v or 0)
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


# ============================================================================
# CASH RECEIPTS
# ============================================================================
def cash_receipt_pdf_upload_path(instance, filename):
    """Storage path for a rendered cash-receipt PDF.

    Named by the receipt NUMBER first, because that is what somebody looking
    for a file will know. The payer's name follows it for readability only.
    """
    ext = (filename.rsplit('.', 1)[-1] or 'pdf').lower()
    number = slugify(instance.receipt_number or 'unnumbered')
    who = slugify(instance.payer_name or 'receipt')
    return os.path.join('cash_receipts', f"{number}-{who}.{ext}")


class CashReceiptNumbering(models.Model):
    """Singleton: the running counter for cash-receipt (CR) numbers.

    Deliberately a separate counter from PhysicalInvoiceNumbering. Receipts and
    invoices are different documents with different sequences; sharing one
    counter would interleave them and make either sequence unexplainable.

    Seeded at 372 so the first receipt the system issues is CR-00372, carrying
    on from the book that was in use before it.
    """
    prefix = models.CharField(max_length=10, default="CR-")
    pad_width = models.PositiveSmallIntegerField(default=5,
        help_text="Zero-padding width (5 -> CR-00372).")
    next_number = models.PositiveIntegerField(default=372,
        help_text="The next CR number the system will issue.")
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "cash_receipt_numbering"
        verbose_name = "Cash Receipt Numbering"
        verbose_name_plural = "Cash Receipt Numbering"

    def __str__(self):
        return f"Receipt numbering — next {self.format(self.next_number)}"

    def format(self, n):
        return f"{self.prefix}{int(n):0{self.pad_width}d}"

    @classmethod
    def get_solo(cls):
        obj = cls.objects.first()
        return obj or cls.objects.create()


class CashReceipt(models.Model):
    """A numbered receipt acknowledging that a payment was received.

    A DOCUMENT, NOT A POSTING. Issuing a receipt changes no balances and marks
    no invoice paid; it records that money arrived. `reference` may name the
    invoice it settles, as free text, without binding the two together.

    The payer's name and contact are SNAPSHOTTED at issue - `payer_name`,
    `payer_address`, `payer_tel` - exactly as PhysicalInvoice freezes its
    bill_* fields. Editing a tenant next year must not rewrite a receipt that
    was handed over last year. The FKs are kept alongside so the receipt can
    still be listed under that tenant, but they are never read back onto the
    document.

    Void, never delete. A voided receipt keeps its number and stays in the
    list, so the sequence has no gap that nobody can account for.
    """

    FORMAT_ELECTRONIC = 'electronic'
    FORMAT_PRINTED = 'printed'
    FORMAT_CHOICES = [
        (FORMAT_ELECTRONIC, 'Electronic'),
        (FORMAT_PRINTED, 'Printed'),
    ]

    METHOD_CASH = 'cash'
    METHOD_TRANSFER = 'transfer'
    METHOD_CHEQUE = 'cheque'
    METHOD_CARD = 'card'
    METHOD_OTHER = 'other'
    METHOD_CHOICES = [
        (METHOD_CASH, 'Cash'),
        (METHOD_TRANSFER, 'Bank Transfer'),
        (METHOD_CHEQUE, 'Cheque'),
        (METHOD_CARD, 'Card'),
        (METHOD_OTHER, 'Other'),
    ]

    cash_receipt_id = models.AutoField(primary_key=True)

    # unique=True is the last line of defence on the number. The counter and
    # the reconciliation in services/cash_receipt_numbering.py should make a
    # duplicate impossible; this makes the database refuse one anyway.
    receipt_number = models.CharField(max_length=32, unique=True,
        help_text='CR-##### — assigned when the receipt is issued.')
    receipt_date = models.DateField(help_text='The date the money was received.')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, default='EUR')
    description = models.TextField(help_text='What the payment was for.')
    method = models.CharField(max_length=20, choices=METHOD_CHOICES,
                              default=METHOD_TRANSFER)
    reference = models.CharField(max_length=64, blank=True,
        help_text='Optional — e.g. the invoice this settles. May be left blank.')
    doc_format = models.CharField(max_length=20, choices=FORMAT_CHOICES,
        default=FORMAT_ELECTRONIC,
        help_text='Electronic omits the signature block and states the '
                  'receipt is valid without one. Printed carries the ruled '
                  'lines instead. Chosen once, at issue.')

    # Who paid, as links (for finding receipts later) ...
    tenant = models.ForeignKey(tenant, on_delete=models.PROTECT, null=True,
                               blank=True, related_name='cash_receipts')
    customer = models.ForeignKey('InvoiceCustomer', on_delete=models.PROTECT,
                                 null=True, blank=True,
                                 related_name='cash_receipts')
    prop = models.ForeignKey(props, on_delete=models.PROTECT, null=True,
                             blank=True, related_name='cash_receipts')

    # ... and as a frozen snapshot (what the document says).
    payer_name = models.CharField(max_length=255)
    payer_address = models.TextField(blank=True,
        help_text='One line per row. Optional — a receipt is valid without it.')
    payer_tel = models.CharField(max_length=64, blank=True)
    payer_email = models.TextField(blank=True,
        help_text='Comma-separated addresses used when the receipt is emailed.')

    pdf_file = models.FileField(upload_to=cash_receipt_pdf_upload_path,
                                blank=True, null=True)

    is_void = models.BooleanField(default=False)
    voided_at = models.DateTimeField(null=True, blank=True)
    voided_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True,
                                  blank=True, related_name='voided_cash_receipts')
    void_reason = models.CharField(max_length=255, blank=True)

    # An edit changes what the record says AFTER a copy may already have been
    # handed over. The system cannot recall that copy; stamping the change is
    # the least it can do, and the list shows it.
    edited_at = models.DateTimeField(null=True, blank=True)
    edited_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True,
                                  blank=True, related_name='edited_cash_receipts')

    sent_at = models.DateTimeField(null=True, blank=True)
    # CR-2, 27 Oct 2026 - WHO THE LAST EMAIL WENT TO, as sent (To and Cc),
    # so the history can say "Emailed to ..." rather than only "Emailed".
    sent_to = models.TextField(blank=True, default='',
        help_text='The addresses the receipt was last emailed to.')
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True,
                                   blank=True, related_name='issued_cash_receipts')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "cash_receipts"
        verbose_name = "Cash Receipt"
        verbose_name_plural = "Cash Receipts"
        # Newest on top, which is how the list is asked to read. The id is the
        # tie-break so two receipts dated the same day keep a stable order
        # rather than swapping places between page loads.
        ordering = ['-receipt_date', '-cash_receipt_id']

    def __str__(self):
        return f"{self.receipt_number} — {self.payer_name}"

    @property
    def address_lines(self):
        return [l.strip() for l in (self.payer_address or '').splitlines()
                if l.strip()]

    # CR-2, 27 Oct 2026 - EMAILING A RECEIPT.
    @property
    def email_list(self):
        """The payer's addresses - comma or semicolon separated, deduped."""
        out, seen = [], set()
        for part in (self.payer_email or '').replace(';', ',').split(','):
            a = part.strip()
            if a and a.lower() not in seen:
                seen.add(a.lower())
                out.append(a)
        return out

    @property
    def is_sent(self):
        """Emailed, and not edited since - his decision of 27 October: an
        edit after sending puts the receipt back to plain Issued, so it is
        plain that the corrected copy has not gone out yet."""
        if not self.sent_at or self.is_void:
            return False
        return not self.edited_at or self.edited_at <= self.sent_at

# ==========================================================================
# E-SIGNING - ES-1, 23 Oct 2026
# ==========================================================================
# THREE TABLES. One envelope, one row per signer, one row per thing
# that happened.
#
# AN ENVELOPE IS NOT A LEASE, which is why none of this is a column on
# `tenant`. The lease is the PDF, and `tenant.tenant_lease_agreement`
# stays exactly where it is as the place a FINISHED one lives. This is
# the ATTEMPT to get one signed - and an attempt can expire, be
# cancelled, be resent, and be followed by another attempt. A process
# stored on the thing it is about can only ever have one of itself,
# and has nowhere to put an audit trail.
#
# THE AUDIT TRAIL IS THE EVIDENCE. There is no certificate - decided
# 23 October, see claude/esign_no_certificate_23_oct.md - so nothing
# in the FILE proves anything. LeaseSigningEvent and the sha256 taken
# at sealing are what a dispute would be argued from, and neither is
# ever updated or deleted.
#
# UPLOADED ONLY, TODAY. `source` exists now so the system-generated
# lease is a branch in one view later rather than a migration and a
# second table.
def lease_signing_upload_path(instance, filename):
    """Where an envelope's PDFs live.

    THE SLUG IS BOUNDED AT NAME_SLUG_CAP - NL-1's lesson, 22 Oct 2026,
    inherited rather than rediscovered. An unbounded slug built from a
    tenant's name generates a filename Django truncates mid-timestamp
    and suffixes, and everything that compares names is then
    permanently wrong. Four recipes spent a week in that state.
    """
    ext = (filename.rsplit('.', 1)[-1] or 'pdf').lower()[:8]
    who = slugify(getattr(instance.tenant, 'tenant_name', '')
                  or 'tenant')[:NAME_SLUG_CAP]
    stamp = timezone.now().strftime('%Y%m%d%H%M%S')
    return os.path.join(
        'lease_signing',
        'lease-%s-%s-%s.%s' % (instance.pk or 'new', who, stamp, ext))


def lease_sealed_upload_path(instance, filename):
    """Where an envelope's SEALED pdf lives. ES-2a, 24 Oct 2026.

    ONE ENVELOPE, ONE OUTPUT, REBUILT IN PLACE - which is what SD-1
    is about, and what the timestamped path above could not deliver.

    THIS NAME DEPENDS ON THE PRIMARY KEY AND NOTHING ELSE. The other
    path in this file embeds a clock AND a tenant slug, and seal()
    calls its path function twice - once to decide what to delete and
    once to write. Either ingredient moving between those two calls
    leaves the delete pointing at a file that is no longer the one
    being replaced:

        the CLOCK moves whenever the two calls straddle a second,
        which on a loaded machine is most of the time - Demetri's
        push gate caught exactly that on 24 October

        the SLUG moves whenever a tenant is renamed, which T2-1 and
        T2-4 made an ordinary thing to do this morning

    A primary key moves never.

    SLASHES, NOT os.path.join - ES-2's lesson of 23 October, learned
    forty lines below this one and not applied here until now.
    os.path.join gives Windows a backslash key and Linux a slash, so
    the same envelope is named differently on a laptop and on Live.
    """
    del filename                      # the extension is always pdf
    return 'lease_signing/sealed/lease-%s.pdf' % instance.pk


def lease_signature_upload_path(instance, filename):
    """Where one person's signature mark lives. Bounded, as above."""
    who = slugify(instance.name or 'party')[:NAME_SLUG_CAP]
    stamp = timezone.now().strftime('%Y%m%d%H%M%S')
    return os.path.join('lease_signatures',
                        'sig-%s-%s-%s.png' % (instance.pk or 'new',
                                              who, stamp))


class LeaseSigning(models.Model):
    """One envelope: one lease, going out to be signed, once."""

    SOURCE_UPLOADED = 'uploaded'
    SOURCE_GENERATED = 'generated'
    SOURCE_CHOICES = [
        (SOURCE_UPLOADED, 'Uploaded'),
        (SOURCE_GENERATED, 'Generated by the system'),
    ]

    DRAFT = 'draft'
    SENT = 'sent'
    PART = 'part_signed'
    COMPLETED = 'completed'
    EXPIRED = 'expired'
    CANCELLED = 'cancelled'
    # ES-5, 25 Oct 2026 - A TENANT WHO REFUSES ENDS THE ENVELOPE. His
    # decision: it stops accepting signatures from anybody, he is
    # told, and a changed lease goes out as a NEW envelope - a clean
    # record of attempt one and attempt two rather than one envelope
    # that changed its mind. ES-1 gave the trail a `declined` event on
    # 23 October and left what a decline DOES undecided until now.
    DECLINED = 'declined'
    STATUS_CHOICES = [
        (DRAFT, 'Draft'),
        (SENT, 'Out for signature'),
        (PART, 'Partly signed'),
        (COMPLETED, 'Signed'),
        (EXPIRED, 'Expired'),
        (CANCELLED, 'Cancelled'),
        (DECLINED, 'Declined'),
    ]

    # THE SIGNING WINDOW AND ITS REMINDERS - ES-5, 25 Oct 2026, his
    # decisions. Seven days (22 October); a nudge on day 3 and on day
    # 6, the day before it lapses. Day 6 alone finds a wrong address
    # on day 6; day 1/3/6 is three emails in a week.
    SIGNING_DAYS = 7
    # ES-6, 25 Oct 2026 - DAY 3, AND THE DAY BEFORE IT LAPSES. ES-5 wrote
    # (3, 6) against a seven-day window, but the Send screen lets the
    # window be anything from 1 to 60 days, and with fourteen days the
    # fixed pair landed on days 10 and 13. His two rules, read literally:
    # one nudge on day 3, one the day before it lapses. For the usual
    # seven days those ARE day 3 and day 6.
    FIRST_REMINDER_DAY = 3
    LAST_REMINDER_DAYS_BEFORE = 1
    REMINDER_RULE = ('Day 3, and the day before the link lapses, to '
                     'whoever has not signed')

    lease_signing_id = models.AutoField(primary_key=True)
    tenant = models.ForeignKey(tenant, on_delete=models.PROTECT,
                               related_name='lease_signings')
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES,
                              default=SOURCE_UPLOADED)

    # THE ORIGINAL IS NEVER TOUCHED. Signatures go on an APPENDED page
    # - decided 23 October - so the lease everyone signed stays
    # byte-for-byte the lease that was sent.
    original_pdf = models.FileField(upload_to=lease_signing_upload_path,
                                    max_length=255)
    # ES-2a, 24 Oct 2026 - ITS OWN PATH, and the original keeps the
    # timestamped one. Uploading a REPLACEMENT lease is a different
    # act from re-sealing the same one: two documents want two names.
    # Only the sealed file is one envelope, one output, rebuilt in
    # place - and a name with a clock in it cannot be rebuilt in
    # place at all.
    sealed_pdf = models.FileField(upload_to=lease_sealed_upload_path,
                                  max_length=255, blank=True, null=True)

    # THE TAMPER-EVIDENCE, because there is no certificate. Taken of
    # the sealed bytes at the moment of sealing. A year from now the
    # question is "what did the tenant actually sign", and only this
    # answers it.
    pdf_sha256 = models.CharField(max_length=64, blank=True)
    page_count = models.PositiveSmallIntegerField(default=0)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES,
                              default=DRAFT)

    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL,
                                   null=True, blank=True,
                                   related_name='lease_signings_created')
    sent_at = models.DateTimeField(null=True, blank=True)
    # SEVEN DAYS - his decision of 22 October - STORED, not computed.
    # A resend moves it, and `sent_at + 7` would then be a different
    # date from the one the tenant was told in writing.
    expires_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    last_reminder_at = models.DateTimeField(null=True, blank=True)

    cancelled_at = models.DateTimeField(null=True, blank=True)
    cancelled_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='lease_signings_cancelled')
    cancel_reason = models.CharField(max_length=255, blank=True)

    # WHERE A LINK POINTS - ES-5, 25 Oct 2026. ES-4 builds every link
    # from the request, deliberately: there is no SITE_URL in this
    # project and inventing one with a production default would make
    # a link mailed from a laptop point at Live. But a REMINDER is
    # sent by the cron, and the cron has no request. So the first
    # send records the address the envelope was sent FROM, and a
    # reminder points where the original did - which is the only
    # answer that is right on Live and on a laptop alike.
    link_base = models.CharField(max_length=200, blank=True)

    # THE APPROVAL - ES-6, 25 Oct 2026. His decision of 23 October: a
    # signed lease is NOT written onto the tenant by the tenant's own
    # action on a page nobody at Alivente is watching. A completed
    # envelope waits here until somebody approves it (the sealed copy
    # becomes the tenant's lease) or declines it (nothing is written).
    #
    # TWO PAIRS AND NOT A STATUS. `status` says what happened to the
    # SIGNING; these say what happened to the RESULT. A completed
    # envelope stays completed whichever way the approval goes, and the
    # register can still ask "was it signed" separately from "was it
    # attached".
    #
    # DECLINE IS FINAL - his decision of 25 October. A declined approval
    # never reappears; attaching that lease means a new envelope.
    approved_at = models.DateTimeField(null=True, blank=True)
    approved_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='lease_signings_approved')
    approval_declined_at = models.DateTimeField(null=True, blank=True)
    approval_declined_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='lease_signings_approval_declined')

    class Meta:
        db_table = 'lease_signings'
        ordering = ['-created_at']
        verbose_name = 'Lease signing'

    def __str__(self):
        return 'Lease signing %s for %s' % (self.pk, self.tenant_id)

    @property
    def is_open(self):
        """Can anybody still sign this?"""
        return self.status in (self.SENT, self.PART)

    @property
    def has_expired(self):
        """Past its date - which is not the same as marked expired."""
        return bool(self.expires_at and timezone.now() > self.expires_at)

    @property
    def awaiting_approval(self):
        """Signed by everybody, and nobody has yet approved or declined it.

        ES-6, 25 Oct 2026. THE ONE ANSWER, asked by the register, the
        approval page, the bell and the two dashboards - five places
        that must never disagree about whether there is work waiting.
        """
        return (self.status == self.COMPLETED and bool(self.sealed_pdf)
                and self.approved_at is None
                and self.approval_declined_at is None)

    @classmethod
    def pending_approval(cls):
        """The same question as awaiting_approval, asked of the table."""
        return (cls.objects.filter(status=cls.COMPLETED,
                                   approved_at__isnull=True,
                                   approval_declined_at__isnull=True)
                .exclude(sealed_pdf='').exclude(sealed_pdf__isnull=True))

    def outstanding(self):
        """The parties who have not signed and have not declined.

        ES-5, 25 Oct 2026. THE ONE ANSWER TO "WHO ARE WE WAITING FOR",
        which reminders, extend and the expiry record all ask. Anyone
        who has already signed is never emailed again - a co-operative
        tenant is not chased for somebody else's silence.
        """
        return [p for p in self.parties.order_by('order', 'party_id')
                if not p.signed_at and not p.declined_at]

    @classmethod
    def closing_moment(cls, days, now=None):
        """The last moment a link works: END of the day, Cyprus time.

        ES-7, 25 Oct 2026, his decision. A link sent at 15:00 on the 24th
        used to die at 15:00 on the 31st while the email said only
        "31 October", so a tenant signing that evening found it closed.
        Now it closes at 23:59:59 local time on the date the email names.
        Used by the Send screen and by Extend, so both say the same.
        """
        import datetime as _dt
        day = timezone.localdate(now or timezone.now()) + \
            _dt.timedelta(days=days)
        return timezone.make_aware(_dt.datetime.combine(
            day, _dt.time(23, 59, 59)))

    def _last_reminder_at(self):
        """The start of the day before the closing date, local time.

        ES-7 - with links open to the end of the day, "the day before it
        lapses" measured back 24 hours from 23:59 would land on the last
        day itself. Counted from the start of the previous day, it stays
        the day before.
        """
        import datetime as _dt
        close_day = timezone.localtime(self.expires_at).date()
        return timezone.make_aware(_dt.datetime.combine(
            close_day - _dt.timedelta(days=self.LAST_REMINDER_DAYS_BEFORE),
            _dt.time(0, 0)))

    def window_start(self):
        """When the current signing window opened - ES-6, 25 Oct 2026.

        THE LATER OF THE FIRST SEND AND THE LAST EXTENSION. The window
        opens when the links go out (the house signature sends them), and
        an extension opens a new one; a reminder counts from there, not
        from when the envelope was created.
        """
        start = self.sent_at
        if self.pk:
            ext = (self.events.filter(kind='extended')
                   .order_by('-at').values_list('at', flat=True).first())
            if ext and (start is None or ext > start):
                start = ext
        return start

    def reminder_due(self, now=None):
        """The reminder day that has come and not been sent, or None.

        ES-5, 25 Oct 2026; ES-6 made it follow any window length. Day 3
        of the window, and the day before it lapses - each only if it
        falls INSIDE the window. AT MOST ONE A RUN, and a cron that was
        down across both sends one email rather than two in a minute.
        Returns the day number counted from the window's start.
        """
        if not (self.is_open and self.expires_at):
            return None
        now = now or timezone.now()
        if now >= self.expires_at:
            return None
        start = self.window_start()
        if start is None:
            return None
        due = None
        close_day = timezone.localtime(self.expires_at).date()
        for at in (start + timezone.timedelta(days=self.FIRST_REMINDER_DAY),
                   self._last_reminder_at()):
            # NEVER ON THE CLOSING DAY ITSELF - ES-7, 25 Oct 2026. With
            # the link open all of that day, "day 3" of a three-day window
            # would fall on the deadline, the day after the "day before"
            # reminder: two emails on consecutive days, which is not his
            # rule. A reminder has to land on a day BEFORE the closing date.
            if not (start < at
                    and timezone.localtime(at).date() < close_day):
                continue
            if now >= at and (self.last_reminder_at is None
                              or self.last_reminder_at < at):
                # CALENDAR DAYS, LOCAL - ES-7, 25 Oct 2026. With links
                # open to the end of the day, the last reminder is counted
                # from midnight, so measuring in hours would call the day
                # before a 14-day deadline "day 12". People count days.
                due = (timezone.localtime(at).date()
                       - timezone.localtime(start).date()).days
        return due


class LeaseSigningParty(models.Model):
    """One person who has to sign. At most three per envelope.

    ONE FROM ALIVENTE AND UP TO TWO TENANTS, to two different email
    addresses - his decision 6 of 22 October.

    THE TOKEN IS STORED HASHED, NEVER IN THE CLEAR. The emailed link
    is the credential, and a credential sitting readable in a database
    column is the thing password resets stopped doing a decade ago. A
    resend issues a NEW token and the old link dies, which is also the
    only honest behaviour: a link that expires and then works again
    never really expired.
    """

    ROLE_ALIVENTE = 'alivente'
    ROLE_TENANT = 'tenant'
    ROLE_CHOICES = [
        (ROLE_ALIVENTE, 'Alivente Limited'),
        (ROLE_TENANT, 'Tenant'),
    ]

    KIND_DRAWN = 'drawn'
    KIND_TYPED = 'typed'
    # ES-7, 25 Oct 2026 - HIS SAVED SIGNATURE, applied when he signs as
    # himself and chooses it. Recorded as its own kind so the record says
    # how the mark got there; the printed page says only "Signed", as it
    # does for drawn and typed - his decision of 25 October.
    KIND_SAVED = 'saved'
    KIND_CHOICES = [(KIND_DRAWN, 'Drawn'), (KIND_TYPED, 'Typed'),
                    (KIND_SAVED, 'Saved signature')]

    party_id = models.AutoField(primary_key=True)
    signing = models.ForeignKey(LeaseSigning, on_delete=models.CASCADE,
                                related_name='parties')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    # ALIVENTE IS ORDER 0 AND SIGNS FIRST - his decision 2 - so the
    # tenant sees the agreement already committed before committing.
    order = models.PositiveSmallIntegerField(default=0)

    name = models.CharField(max_length=255)
    email = models.CharField(max_length=255, blank=True)

    token_hash = models.CharField(max_length=64, blank=True, db_index=True)
    token_issued_at = models.DateTimeField(null=True, blank=True)

    # WHAT HAPPENED ON THE PAGE. None of it gates anything - decided
    # 23 October - and all of it is recorded.
    first_viewed_at = models.DateTimeField(null=True, blank=True)
    view_count = models.PositiveSmallIntegerField(default=0)
    read_to_end = models.BooleanField(default=False)
    seconds_open = models.PositiveIntegerField(default=0)

    consent_at = models.DateTimeField(null=True, blank=True)
    signed_at = models.DateTimeField(null=True, blank=True)
    signature_kind = models.CharField(max_length=10, choices=KIND_CHOICES,
                                      blank=True)
    signature_image = models.ImageField(
        upload_to=lease_signature_upload_path, max_length=255,
        blank=True, null=True)
    typed_name = models.CharField(max_length=255, blank=True)
    # THE HOUSE MARKS, COPIED - ES-7, 25 Oct 2026. When he signs as
    # himself the stored signature (if he chose it) and the company stamp
    # are COPIED onto this party, in the database. A copy and not a
    # pointer: replacing the stored mark next year must not change a
    # lease already signed, and the sealed page must be rebuildable from
    # the envelope alone. Never media - nothing serves these by URL.
    mark_signature = models.BinaryField(null=True, blank=True,
                                        editable=False)
    mark_stamp = models.BinaryField(null=True, blank=True, editable=False)

    signed_ip = models.CharField(max_length=45, blank=True)
    signed_user_agent = models.CharField(max_length=400, blank=True)

    # HOW THEY PROVED WHO THEY WERE - decided 23 October, and the two
    # are not equally strong.
    #
    # A LINK HOLDER is somebody who had the token. That is all the
    # system can honestly say, and it is what a tenant will always be.
    #
    # A SIGNED-IN USER is somebody the application authenticated. When
    # the Alivente signer is the person creating the envelope they go
    # straight to the page with no email at all, and the trail can say
    # WHO rather than only that a link was held.
    #
    # RECORDED RATHER THAN LEVELLED DOWN. With no certificate the
    # audit trail is the whole of the evidence, so a stronger fact
    # about one signature is worth keeping even though the other
    # cannot have it.
    AUTH_TOKEN = 'token'
    AUTH_SESSION = 'session'
    AUTH_CHOICES = [
        (AUTH_TOKEN, 'Link holder'),
        (AUTH_SESSION, 'Signed in'),
    ]
    signed_auth = models.CharField(max_length=10, choices=AUTH_CHOICES,
                                   blank=True)
    signed_by_user = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='lease_signatures',
        help_text='The authenticated user, when the signature was made '
                  'while signed in rather than through a link.')

    declined_at = models.DateTimeField(null=True, blank=True)
    decline_reason = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = 'lease_signing_parties'
        ordering = ['signing', 'order', 'party_id']
        verbose_name = 'Lease signing party'
        verbose_name_plural = 'Lease signing parties'

    def __str__(self):
        return '%s (%s)' % (self.name, self.role)

    @staticmethod
    def hash_token(raw):
        """The one place a token becomes a stored value."""
        import hashlib
        return hashlib.sha256((raw or '').encode('utf-8')).hexdigest()

    def issue_token(self):
        """Mint a link token, keep only its hash, return the raw one.

        THE RETURN VALUE IS THE ONLY TIME THE TOKEN EXISTS. The caller
        puts it in the email and forgets it; nothing can read it back.
        """
        import secrets
        raw = secrets.token_urlsafe(32)
        self.token_hash = self.hash_token(raw)
        self.token_issued_at = timezone.now()
        return raw


class LeaseSigningEvent(models.Model):
    """One row per thing that happened. APPEND ONLY.

    With no certificate, this table and LeaseSigning.pdf_sha256 ARE
    the evidence. Nothing here is ever updated or deleted, and it is
    what the appended signature page prints.
    """

    KIND_CHOICES = [
        ('created', 'Created'),
        ('sent', 'Sent'),
        ('resent', 'Resent'),
        ('reminded', 'Reminder sent'),
        ('viewed', 'Opened'),
        ('consented', 'Agreed to sign electronically'),
        ('signed', 'Signed'),
        ('declined', 'Declined'),
        ('sealed', 'Sealed'),
        ('delivered', 'Copy emailed'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled'),
        # ES-5, 25 Oct 2026 - another seven days, who gave them and to
        # when. The fresh links it sends are recorded as `sent`, one
        # per outstanding party; this row is the decision itself.
        ('extended', 'Extended'),
        # ES-6, 25 Oct 2026 - what happened to the RESULT. `rejected`
        # and not `declined`, because `declined` already means a TENANT
        # refused to sign, and one word for two acts is a trail nobody
        # can read.
        ('approved', 'Approved onto the tenant'),
        ('rejected', 'Approval declined'),
    ]

    event_id = models.AutoField(primary_key=True)
    signing = models.ForeignKey(LeaseSigning, on_delete=models.CASCADE,
                                related_name='events')
    # NULL FOR AN ENVELOPE EVENT. Created, cancelled and expired belong
    # to the envelope rather than to a person, and inventing a party
    # for them would make the trail say something untrue.
    party = models.ForeignKey(LeaseSigningParty,
                              on_delete=models.SET_NULL,
                              null=True, blank=True,
                              related_name='events')
    at = models.DateTimeField(auto_now_add=True)
    kind = models.CharField(max_length=20, choices=KIND_CHOICES)
    detail = models.CharField(max_length=400, blank=True)
    ip = models.CharField(max_length=45, blank=True)
    user_agent = models.CharField(max_length=400, blank=True)

    class Meta:
        db_table = 'lease_signing_events'
        ordering = ['at', 'event_id']
        verbose_name = 'Lease signing event'


# ==========================================================================
# HOUSE MARKS - ES-7, 25 Oct 2026
# ==========================================================================
class HouseMark(models.Model):
    """His signature and the company stamp, stored once, securely.

    HIS DECISIONS OF 25 OCTOBER. The stamp is the company NAME only
    ("ALIVENTE LIMITED" - the company number left off). Both are used
    ONLY when Demetri Manias is the signatory, decided by the signed-in
    account that signs and never by a typed name. Stored securely: in the
    database, never in media, never served by any URL, and managed by a
    superuser only.

    ONE OF EACH KIND, BELONGING TO WHOEVER UPLOADED IT. The upload screen
    is superuser-only and the owner is the uploader, so there is exactly
    one account the marks can ever be applied for. Another superuser
    uploading would REPLACE them, visibly, not add a second set.

    PNG BYTES, ALPHA KEPT. The upload screen normalises whatever it is
    given into a transparent PNG, so the sealed page never has to.
    """
    SIGNATURE = 'signature'
    STAMP = 'stamp'
    KIND_CHOICES = [(SIGNATURE, 'Signature'), (STAMP, 'Company stamp')]

    house_mark_id = models.AutoField(primary_key=True)
    kind = models.CharField(max_length=20, choices=KIND_CHOICES, unique=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE,
                              related_name='house_marks')
    image = models.BinaryField(editable=False)
    sha256 = models.CharField(max_length=64)
    width = models.PositiveIntegerField(default=0)
    height = models.PositiveIntegerField(default=0)
    uploaded_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'house_marks'
        verbose_name = 'House mark'

    def __str__(self):
        return '%s (%s)' % (self.get_kind_display(), self.owner)

    @classmethod
    def for_signer(cls, user, kind):
        """The mark's bytes if THIS user owns it, else None.

        THE ONE QUESTION THE SIGNING PAGE ASKS. Ownership is the account,
        so a name typed into "Signing for Alivente" can never reach it.
        """
        if user is None or not getattr(user, 'is_authenticated', False):
            return None
        row = cls.objects.filter(kind=kind, owner=user).first()
        return bytes(row.image) if row and row.image else None
