from django.db import models
from django.db import connections
from django.db.models import Min, Max, Sum
from django.core.exceptions import ValidationError
from django.utils.text import slugify
from django.utils import timezone
from decimal import Decimal
import os
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

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

@receiver(post_save, sender=ProjectTask)
def update_project_on_task_save(sender, instance, **kwargs):
    """Update project totals when a task is saved"""
    try:
        instance.project.update_project_from_tasks()
        instance.project.save(skip_validation=True)
    except Exception as e:
        # Log error but don't break the save operation
        print(f"Error updating project from task save: {e}")

@receiver(post_delete, sender=ProjectTask)
def update_project_on_task_delete(sender, instance, **kwargs):
    """Update project totals when a task is deleted"""
    try:
        instance.project.update_project_from_tasks()
        instance.project.save(skip_validation=True)
    except Exception as e:
        # Log error but don't break the delete operation
        print(f"Error updating project from task delete: {e}")

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

