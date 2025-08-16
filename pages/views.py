from django.conf import settings
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.forms import UserCreationForm, UserChangeForm, PasswordChangeForm
from django.core.exceptions import ValidationError
from django.core.files.storage import FileSystemStorage
from django.core.paginator import Paginator
from django.core.serializers import serialize
from django.db import connection, transaction
from django.db.models import Q, Prefetch, Subquery, OuterRef, Sum, F
from django.db.models.functions import Coalesce
from django.http import HttpResponse, HttpResponseServerError, FileResponse, Http404, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import render_to_string, get_template
from django.templatetags.static import static
from django.urls import reverse
from django.utils import timezone
from django.utils.dateparse import parse_date
from django.utils.html import strip_tags
from django.utils.safestring import mark_safe
from django.utils.timezone import now
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from django.views.decorators.http import require_POST
from django.views.static import serve
from .translation_service import ensure_project_translations, get_translated_text
from . import forms
from .forms import PropForm, TenantForm, PettyForm, InvoicesForm, IssuesForm, DetailsForm, SupplierForm, ValuesForm, RevenueTypesForm, RevenueLineForm, RevenueForm, ExpenseTypesForm, ExpenseLineForm, ExpenseForm, ActExpenseForm 
from .models import (
    props,
    petty,
    issues,
    issues_details, 
    tenant, 
    invoices,
    supplier,
    prop_values,
    revenue_types,
    revenue_line_types,
    revenue,
    expense_types,
    expense_line_types,
    expense,
    act_expense,
    Project, 
    ProjectTask,
    ProjectDocument,
    )
from decimal import Decimal
from collections import defaultdict
from datetime import date, datetime, timedelta
from urllib.parse import urlparse, parse_qs
from xhtml2pdf import pisa
import mysql.connector
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import re
import uuid
import logging
import json

logger = logging.getLogger(__name__)

### FINANCIAL DASHBOARD ###
@login_required
def financial_indicators_view(request):
    """
    Display the Financial Indicators Dashboard - ONLY for Active Properties
    Using Portfolio-Wide Calculations
    """
    if request.method == 'GET' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        # AJAX request for property data
        try:
            # Get ONLY active properties for all calculations and display
            properties = props.objects.filter(prop_status='Active')
            properties_data = []
            
            # Portfolio-wide totals for all active properties
            portfolio_totals = {
                'total_revenue': Decimal('0.00'),
                'total_budgeted_expenses': Decimal('0.00'),
                'total_purchase_price': Decimal('0.00'),
                'total_current_value': Decimal('0.00'),
                'total_floor_area': 0,
                'property_count': 0
            }
            
            for prop in properties:
                # Get revenue totals using your existing revenue model structure
                revenue_total = calculate_property_revenue(prop)
                
                # Get ONLY budgeted expense totals using your existing expense model
                budgeted_expense_total = calculate_property_budgeted_expenses(prop)
                
                # Get property values - ONLY for active properties
                property_values = prop_values.objects.filter(prop=prop).first()
                purchase_price = property_values.prop_values_purchase_price if property_values else 0
                current_value = property_values.prop_values_current_value if property_values else 0
                
                # Add to portfolio totals
                portfolio_totals['total_revenue'] += revenue_total
                portfolio_totals['total_budgeted_expenses'] += budgeted_expense_total
                portfolio_totals['total_purchase_price'] += purchase_price or 0
                portfolio_totals['total_current_value'] += current_value or 0
                portfolio_totals['total_floor_area'] += prop.prop_floor_area or 0
                portfolio_totals['property_count'] += 1
                
                # Calculate individual property indicators for display purposes
                gross_roi = (revenue_total / purchase_price * 100) if purchase_price > 0 else 0
                net_roi = ((revenue_total - budgeted_expense_total) / purchase_price * 100) if purchase_price > 0 else 0
                expense_ratio = (budgeted_expense_total / revenue_total * 100) if revenue_total > 0 else 0
                rent_per_sqm = (revenue_total / 12 / prop.prop_floor_area) if prop.prop_floor_area and prop.prop_floor_area > 0 else 0
                value_increase = ((current_value - purchase_price) / purchase_price * 100) if purchase_price > 0 and current_value > 0 else 0
                
                # Store individual property data
                properties_data.append({
                    'id': prop.prop_id,
                    'name': prop.prop_name or f"Property {prop.prop_id}",
                    'status': prop.prop_status,
                    'grossROI': round(float(gross_roi), 2),
                    'netROI': round(float(net_roi), 2),
                    'expensesToRevenue': round(float(expense_ratio), 2),
                    'rentPerSqm': round(float(rent_per_sqm), 2),
                    'valueIncrease': round(float(value_increase), 2),
                    'revenue': float(revenue_total),
                    'expenses': float(budgeted_expense_total),
                    'profit': float(revenue_total - budgeted_expense_total)
                })
            
            # Calculate TRUE PORTFOLIO-WIDE indicators
            portfolio_indicators = {
                'grossROI': round(float(
                    (portfolio_totals['total_revenue'] / portfolio_totals['total_purchase_price'] * 100) 
                    if portfolio_totals['total_purchase_price'] > 0 else 0
                ), 2),
                'netROI': round(float(
                    ((portfolio_totals['total_revenue'] - portfolio_totals['total_budgeted_expenses']) / 
                     portfolio_totals['total_purchase_price'] * 100) 
                    if portfolio_totals['total_purchase_price'] > 0 else 0
                ), 2),
                'expensesToRevenue': round(float(
                    (portfolio_totals['total_budgeted_expenses'] / portfolio_totals['total_revenue'] * 100) 
                    if portfolio_totals['total_revenue'] > 0 else 0
                ), 2),
                'rentPerSqm': round(float(
                    (portfolio_totals['total_revenue'] / 12 / portfolio_totals['total_floor_area']) 
                    if portfolio_totals['total_floor_area'] > 0 else 0
                ), 2),
                'valueIncrease': round(float(
                    ((portfolio_totals['total_current_value'] - portfolio_totals['total_purchase_price']) / 
                     portfolio_totals['total_purchase_price'] * 100) 
                    if portfolio_totals['total_purchase_price'] > 0 and portfolio_totals['total_current_value'] > 0 else 0
                ), 2)
            }
            
            return JsonResponse({
                'properties': properties_data,
                'portfolio_indicators': portfolio_indicators,
                'portfolio_totals': {
                    'total_revenue': float(portfolio_totals['total_revenue']),
                    'total_expenses': float(portfolio_totals['total_budgeted_expenses']),
                    'total_purchase_price': float(portfolio_totals['total_purchase_price']),
                    'total_current_value': float(portfolio_totals['total_current_value']),
                    'total_floor_area': portfolio_totals['total_floor_area'],
                    'property_count': portfolio_totals['property_count']
                },
                'total_active_properties': len(properties_data),
                'message': f'Showing {len(properties_data)} active properties with portfolio-wide calculations (budgeted expenses only)'
            })
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    # Regular page load
    context = {
        'page_title': 'Financial Indicators Dashboard - Portfolio-Wide Analysis (Active Properties)'
    }
    return render(request, 'finance/financial_indicators.html', context)

def calculate_property_revenue(property_obj):
    """
    Calculate total annual revenue for a property using your revenue model
    ONLY processes Active properties
    """
    # Additional safety check - only calculate for active properties
    if property_obj.prop_status != 'Active':
        return Decimal('0.00')
        
    # Get all revenue records for this active property
    revenue_records = revenue.objects.filter(prop=property_obj)
    
    total_revenue = Decimal('0.00')
    
    for record in revenue_records:
        # Sum all monthly revenue amounts
        monthly_total = (
            (record.revenue_jan or Decimal('0.00')) +
            (record.revenue_feb or Decimal('0.00')) +
            (record.revenue_mar or Decimal('0.00')) +
            (record.revenue_apr or Decimal('0.00')) +
            (record.revenue_may or Decimal('0.00')) +
            (record.revenue_jun or Decimal('0.00')) +
            (record.revenue_jul or Decimal('0.00')) +
            (record.revenue_aug or Decimal('0.00')) +
            (record.revenue_sep or Decimal('0.00')) +
            (record.revenue_oct or Decimal('0.00')) +
            (record.revenue_nov or Decimal('0.00')) +
            (record.revenue_dec or Decimal('0.00'))
        )
        total_revenue += monthly_total
    
    return total_revenue

def calculate_property_budgeted_expenses(property_obj):
    """
    Calculate total annual budgeted expenses for a property using your expense model
    ONLY processes Active properties
    """
    # Additional safety check - only calculate for active properties
    if property_obj.prop_status != 'Active':
        return Decimal('0.00')
        
    # Get all budgeted expense records for this active property
    expense_records = expense.objects.filter(prop=property_obj)
    
    total_expenses = Decimal('0.00')
    
    for record in expense_records:
        # Sum all monthly expense amounts
        monthly_total = (
            (record.expense_jan or Decimal('0.00')) +
            (record.expense_feb or Decimal('0.00')) +
            (record.expense_mar or Decimal('0.00')) +
            (record.expense_apr or Decimal('0.00')) +
            (record.expense_may or Decimal('0.00')) +
            (record.expense_jun or Decimal('0.00')) +
            (record.expense_jul or Decimal('0.00')) +
            (record.expense_aug or Decimal('0.00')) +
            (record.expense_sep or Decimal('0.00')) +
            (record.expense_oct or Decimal('0.00')) +
            (record.expense_nov or Decimal('0.00')) +
            (record.expense_dec or Decimal('0.00'))
        )
        total_expenses += monthly_total
    
    return total_expenses

def calculate_property_actual_expenses(property_obj):
    """
    Calculate total actual expenses for a property using your act_expense model
    ONLY processes Active properties
    """
    # Additional safety check - only calculate for active properties
    if property_obj.prop_status != 'Active':
        return Decimal('0.00')
        
    # Get all actual expense records for this active property
    actual_expenses = act_expense.objects.filter(prop=property_obj)
    
    # Sum all actual expense amounts
    total_actual = actual_expenses.aggregate(
        total=Sum('act_expense_amount')
    )['total'] or Decimal('0.00')
    
    return total_actual

# Additional helper function for year-specific calculations if needed
def calculate_property_revenue_for_year(property_obj, year):
    """
    Calculate revenue for a specific year (if you need year filtering later)
    This would require adding year fields to your revenue model or 
    filtering by revenue_types that have year information
    """
    # This is a placeholder - you'd need to modify based on how you handle years
    # in your revenue_types model or add year fields to your models
    return calculate_property_revenue(property_obj)

def calculate_property_expenses_for_year(property_obj, year):
    """
    Calculate expenses for a specific year (if you need year filtering later)
    """
    # For budgeted expenses
    budgeted = calculate_property_budgeted_expenses(property_obj)
    
    # For actual expenses, you can filter by year using the date field
    from django.db.models import Q
    actual_expenses = act_expense.objects.filter(
        prop=property_obj,
        act_expense_date__year=year
    )
    actual_total = actual_expenses.aggregate(
        total=Sum('act_expense_amount')
    )['total'] or Decimal('0.00')
    
    return budgeted + actual_total

### PROJECTS ###
@login_required
def projects_list(request):
    """Display list of projects with filtering and handle modal-based deletion"""
    
    # Handle POST request for modal-based deletion
    if request.method == 'POST' and 'delete_project_id' in request.POST:
        if not request.user.is_superuser:
            messages.error(request, "You don't have permission to delete projects.")
            return redirect('projects')
        
        project_id = request.POST.get('delete_project_id')
        project = get_object_or_404(Project, project_id=project_id)
        
        try:
            with transaction.atomic():
                logger.info(f"User {request.user.username} deleting project via modal: {project.project_name}")
                
                # Get counts for message
                main_task_count = project.projecttask_set.filter(parent_task__isnull=True).count()
                subtask_count = project.projecttask_set.filter(parent_task__isnull=False).count()
                document_count = project.project_documents.count() if hasattr(project, 'project_documents') else 0
                project_name = project.project_name
                
                # Delete the project
                project.delete()
                
                # Success message
                if subtask_count > 0:
                    messages.success(
                        request, 
                        f"Project '{project_name}' has been permanently deleted along with {main_task_count} main tasks, {subtask_count} subtasks, and {document_count} documents."
                    )
                else:
                    messages.success(
                        request, 
                        f"Project '{project_name}' has been permanently deleted along with {main_task_count} tasks and {document_count} documents."
                    )
                
        except Exception as e:
            logger.error(f"Error deleting project {project_id}: {str(e)}")
            messages.error(request, f"An error occurred while deleting the project '{project.project_name}'.")
        
        return redirect('projects')
    
    # FIXED: Get filter parameters from GET request (for proper filtering)
    projects_list = Project.objects.select_related('prop').all().order_by(
        F('project_start_date').desc(nulls_last=True)
    )
    
    # Initialize filter variables from GET parameters
    search_query = request.GET.get('search', '').strip()
    selected_property = request.GET.get('property', '')
    selected_status = request.GET.get('status', '')
    
    # Apply filters
    if search_query:
        projects_list = projects_list.filter(
            Q(project_name__icontains=search_query) |
            Q(project_description__icontains=search_query)
        )
    
    if selected_property:
        try:
            # Convert to int to handle proper filtering
            property_id = int(selected_property)
            projects_list = projects_list.filter(prop_id=property_id)
        except (ValueError, TypeError):
            # Invalid property ID, ignore filter
            selected_property = ""
    
    if selected_status:
        # Validate that the status is one of the valid choices
        valid_statuses = [choice[0] for choice in Project.PROJECT_STATUS_CHOICES]
        if selected_status in valid_statuses:
            projects_list = projects_list.filter(project_status=selected_status)
        else:
            # Invalid status, ignore filter
            selected_status = ""
    
    # Get all properties for filter dropdown
    properties = props.objects.all().order_by('prop_name')
    
    # Pagination with filter preservation
    paginator = Paginator(projects_list, 25)
    page_number = request.GET.get('page')
    projects_page = paginator.get_page(page_number)
    
    context = {
        'projects': projects_page,
        'properties': properties,
        'search_query': search_query,
        'selected_property': selected_property,
        'selected_status': selected_status,
        'status_choices': Project.PROJECT_STATUS_CHOICES,
    }
    
    return render(request, 'projects/projects.html', context)

@login_required
def projects_add(request):
    """Add new project"""
    if not request.user.is_superuser:
        messages.error(request, "You don't have permission to add projects.")
        return redirect('projects')
    
    if request.method == 'POST':
        project_name = request.POST.get('project_name')
        prop_id = request.POST.get('prop_id')
        project_start_date = request.POST.get('project_start_date')
        project_expected_completion_date = request.POST.get('project_expected_completion_date')
        project_status = request.POST.get('project_status', 'Pending')
        project_actual_completion_date = request.POST.get('project_actual_completion_date')
        project_description = request.POST.get('project_description')
        
        try:
            # Get the property
            property_obj = get_object_or_404(props, prop_id=prop_id)
            
            # Create the project
            project = Project(  # Updated model name
                project_name=project_name,
                prop=property_obj,
                project_start_date=project_start_date if project_start_date else None,
                project_expected_completion_date=project_expected_completion_date if project_expected_completion_date else None,
                project_status=project_status,
                project_actual_completion_date=project_actual_completion_date if project_actual_completion_date else None,
                project_description=project_description
            )
            project.save()
            
            messages.success(request, f"Project '{project_name}' has been created successfully.")
            return redirect('projects')
            
        except Exception as e:
            messages.error(request, f"Error creating project: {str(e)}")
    
    # Get all properties for dropdown
    properties = props.objects.all().order_by('prop_name')
    
    context = {
        'properties': properties,
        'status_choices': Project.PROJECT_STATUS_CHOICES,  # Updated model name
    }
    
    return render(request, 'projects/projects_add.html', context)

@login_required
def projects_edit(request, project_id):
    """Edit existing project - enhanced to handle Gantt chart returns"""
    if not request.user.is_superuser:
        messages.error(request, "You don't have permission to edit projects.")
        return redirect('projects')
    
    project = get_object_or_404(Project, project_id=project_id)
    
    # Check if coming from Gantt chart
    from_gantt = request.GET.get('from_gantt', 'false') == 'true'
    
    if request.method == 'POST':
        project.project_name = request.POST.get('project_name')
        prop_id = request.POST.get('prop_id')
        project.project_start_date = request.POST.get('project_start_date') if request.POST.get('project_start_date') else None
        project.project_expected_completion_date = request.POST.get('project_expected_completion_date') if request.POST.get('project_expected_completion_date') else None
        project.project_status = request.POST.get('project_status', 'Pending')
        project.project_actual_completion_date = request.POST.get('project_actual_completion_date') if request.POST.get('project_actual_completion_date') else None
        project.project_description = request.POST.get('project_description')
        
        try:
            # Update the property
            property_obj = get_object_or_404(props, prop_id=prop_id)
            project.prop = property_obj
            
            project.save()
            
            messages.success(request, f"Project '{project.project_name}' has been updated successfully.")
            
            # Redirect based on where user came from
            if from_gantt:
                return redirect('project_gantt', project_id=project_id)
            else:
                return redirect('projects')
                
        except Exception as e:
            messages.error(request, f"Error updating project: {str(e)}")
    
    # Get all properties for dropdown
    properties = props.objects.all().order_by('prop_name')
    
    context = {
        'project': project,
        'properties': properties,
        'status_choices': Project.PROJECT_STATUS_CHOICES,
        'from_gantt': from_gantt,  # Pass this to template for form action
    }
    
    return render(request, 'projects/projects_edit.html', context)

@login_required
def projects_delete(request, project_id):
    """Delete project with enhanced cascade deletion and warnings"""
    if not request.user.is_superuser:
        messages.error(request, "You don't have permission to delete projects.")
        return redirect('projects')
    
    project = get_object_or_404(Project, project_id=project_id)
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Log the deletion attempt
                logger.info(f"User {request.user.username} attempting to delete project: {project.project_name} (ID: {project_id})")
                
                # Get counts for the success message BEFORE deletion
                main_task_count = project.projecttask_set.filter(parent_task__isnull=True).count()
                subtask_count = project.projecttask_set.filter(parent_task__isnull=False).count()
                total_task_count = project.projecttask_set.count()
                document_count = project.project_documents.count() if hasattr(project, 'project_documents') else 0
                
                project_name = project.project_name
                
                # Delete the project (this will cascade to delete all related tasks and subtasks)
                project.delete()
                
                # Log successful deletion
                logger.info(f"Successfully deleted project: {project_name} (ID: {project_id}) with {main_task_count} main tasks, {subtask_count} subtasks, and {document_count} documents")
                
                # Success message with detailed information
                if subtask_count > 0:
                    messages.success(
                        request, 
                        f"Project '{project_name}' has been permanently deleted along with {main_task_count} main tasks, {subtask_count} subtasks, and {document_count} documents."
                    )
                else:
                    messages.success(
                        request, 
                        f"Project '{project_name}' has been permanently deleted along with {total_task_count} tasks and {document_count} documents."
                    )
                
        except Exception as e:
            # Log the error
            logger.error(f"Error deleting project {project_id}: {str(e)}")
            
            # Error message
            messages.error(
                request, 
                f"An error occurred while deleting the project '{project.project_name}'. Please try again or contact support."
            )
            
            # Redirect back to the delete confirmation page
            return render(request, 'projects/projects_delete.html', {'project': project})
        
        return redirect('projects')
    
    # GET request - show confirmation page with detailed information
    # Get counts for the confirmation page
    main_tasks = project.projecttask_set.filter(parent_task__isnull=True)
    subtasks = project.projecttask_set.filter(parent_task__isnull=False)
    documents = project.project_documents.all() if hasattr(project, 'project_documents') else []
    
    context = {
        'project': project,
        'main_task_count': main_tasks.count(),
        'subtask_count': subtasks.count(),
        'document_count': len(documents),
        'main_tasks': main_tasks[:5],  # Show first 5 main tasks as examples
        'subtasks': subtasks[:10],     # Show first 10 subtasks as examples
        'documents': documents[:5],    # Show first 5 documents as examples
    }
    
    return render(request, 'projects/projects_delete.html', context)

@login_required
def projects_detail(request, project_id):
    """Display project details with tasks and subtasks"""
    project = get_object_or_404(Project.objects.select_related('prop'), project_id=project_id)  # Updated model name
    
    # Get all tasks for this project (main tasks only, not subtasks)
    main_tasks = ProjectTask.objects.filter(  # Updated model name
        project=project, 
        parent_task__isnull=True
    ).prefetch_related('subtasks').order_by('task_start_date', 'task_id')
    
    context = {
        'project': project,
        'main_tasks': main_tasks,
        'task_status_choices': ProjectTask.TASK_STATUS_CHOICES,  # Updated model name
        'task_priority_choices': ProjectTask.TASK_PRIORITY_CHOICES,  # Updated model name
    }
    
    return render(request, 'projects/projects_detail.html', context)

@login_required
def project_tasks_add(request, project_id):
    """Add new task to project"""
    if not request.user.is_superuser:
        messages.error(request, "You don't have permission to add tasks.")
        return redirect('projects_detail', project_id=project_id)
    
    project = get_object_or_404(Project, project_id=project_id)  # Updated model name
    
    if request.method == 'POST':
        task_name = request.POST.get('task_name')
        task_description = request.POST.get('task_description')
        task_start_date = request.POST.get('task_start_date')
        task_expected_completion_date = request.POST.get('task_expected_completion_date')
        task_status = request.POST.get('task_status', 'Pending')
        task_priority = request.POST.get('task_priority', 'Medium')
        task_budgeted_cost = request.POST.get('task_budgeted_cost')
        task_actual_cost = request.POST.get('task_actual_cost')
        task_assigned_to = request.POST.get('task_assigned_to')
        task_actual_completion_date = request.POST.get('task_actual_completion_date')
        
        try:
            task = ProjectTask(  # Updated model name
                project=project,
                task_name=task_name,
                task_description=task_description,
                task_start_date=task_start_date if task_start_date else None,
                task_expected_completion_date=task_expected_completion_date if task_expected_completion_date else None,
                task_status=task_status,
                task_priority=task_priority,
                task_budgeted_cost=task_budgeted_cost if task_budgeted_cost else 0.00,
                task_actual_cost=task_actual_cost if task_actual_cost else 0.00,
                task_assigned_to=task_assigned_to,
                task_actual_completion_date=task_actual_completion_date if task_actual_completion_date else None
            )
            task.save()
            
            messages.success(request, f"Task '{task_name}' has been added successfully.")
            return redirect('projects_detail', project_id=project_id)
            
        except Exception as e:
            messages.error(request, f"Error adding task: {str(e)}")
    
    context = {
        'project': project,
        'task_status_choices': ProjectTask.TASK_STATUS_CHOICES,  # Updated model name
        'task_priority_choices': ProjectTask.TASK_PRIORITY_CHOICES,  # Updated model name
    }
    
    return render(request, 'projects/project_tasks_add.html', context)

@login_required
def project_tasks_edit(request, project_id, task_id):
    """Edit existing task - enhanced to handle Gantt chart returns"""
    if not request.user.is_superuser:
        messages.error(request, "You don't have permission to edit tasks.")
        return redirect('projects_detail', project_id=project_id)
    
    project = get_object_or_404(Project, project_id=project_id)
    task = get_object_or_404(ProjectTask, task_id=task_id, project=project)
    
    # Check if coming from Gantt chart
    from_gantt = request.GET.get('from_gantt', 'false') == 'true'
    
    if request.method == 'POST':
        # Only update fields that are not auto-calculated
        task.task_name = request.POST.get('task_name')
        task.task_description = request.POST.get('task_description')
        
        # For main tasks, don't update calculated fields
        if not task.parent_task:  # This is a main task
            # Auto-calculate all fields based on subtasks
            task.task_status = task.get_calculated_status()
            task.task_start_date = task.get_calculated_start_date()
            task.task_expected_completion_date = task.get_calculated_expected_completion()
            task.task_actual_completion_date = task.get_calculated_actual_completion()
            task.task_budgeted_cost = task.get_calculated_budgeted_cost()
            task.task_actual_cost = task.get_calculated_actual_cost()
        else:  # This is a subtask
            # Allow manual editing of all fields for subtasks
            task.task_start_date = request.POST.get('task_start_date') if request.POST.get('task_start_date') else None
            task.task_expected_completion_date = request.POST.get('task_expected_completion_date') if request.POST.get('task_expected_completion_date') else None
            task.task_status = request.POST.get('task_status', 'Not Started')
            task.task_priority = request.POST.get('task_priority', 'Medium')
            task.task_budgeted_cost = request.POST.get('task_budgeted_cost') if request.POST.get('task_budgeted_cost') else 0.00
            task.task_actual_cost = request.POST.get('task_actual_cost') if request.POST.get('task_actual_cost') else 0.00
            task.task_assigned_to = request.POST.get('task_assigned_to')
            task.task_actual_completion_date = request.POST.get('task_actual_completion_date') if request.POST.get('task_actual_completion_date') else None
            
            # Handle progress percentage
            progress_percentage = request.POST.get('task_progress_percentage')
            if progress_percentage is not None:
                task.task_progress_percentage = int(progress_percentage)
            else:
                # Set default based on status
                if task.task_status == 'Pending':
                    task.task_progress_percentage = 0
                elif task.task_status == 'Completed':
                    task.task_progress_percentage = 100
                else:  # In Progress
                    task.task_progress_percentage = task.task_progress_percentage or 1
        
        try:
            task.save()
            
            # If this is a subtask, update the parent task's calculated fields
            if task.parent_task:
                parent = task.parent_task
                parent.task_status = parent.get_calculated_status()
                parent.task_start_date = parent.get_calculated_start_date()
                parent.task_expected_completion_date = parent.get_calculated_expected_completion()
                parent.task_actual_completion_date = parent.get_calculated_actual_completion()
                parent.task_budgeted_cost = parent.get_calculated_budgeted_cost()
                parent.task_actual_cost = parent.get_calculated_actual_cost()
                parent.save()
            
            messages.success(request, f"Task '{task.task_name}' has been updated successfully.")
            
            # Redirect based on where user came from
            if from_gantt:
                return redirect('project_gantt', project_id=project_id)
            else:
                return redirect('projects_detail', project_id=project_id)
                
        except Exception as e:
            messages.error(request, f"Error updating task: {str(e)}")
    
    context = {
        'project': project,
        'task': task,
        'task_status_choices': ProjectTask.TASK_STATUS_CHOICES,
        'task_priority_choices': ProjectTask.TASK_PRIORITY_CHOICES,
        'from_gantt': from_gantt,  # Pass this to template for form action
    }
    
    return render(request, 'projects/project_tasks_edit.html', context)

@login_required
def project_tasks_delete(request, project_id, task_id):
    """Delete task"""
    if not request.user.is_superuser:
        messages.error(request, "You don't have permission to delete tasks.")
        return redirect('projects_detail', project_id=project_id)
    
    project = get_object_or_404(Project, project_id=project_id)  # Updated model name
    task = get_object_or_404(ProjectTask, task_id=task_id, project=project)  # Updated model name
    task_name = task.task_name
    
    if request.method == 'POST':
        task.delete()
        messages.success(request, f"Task '{task_name}' has been deleted successfully.")
        return redirect('projects_detail', project_id=project_id)
    
    context = {
        'project': project,
        'task': task,
    }
    
    return render(request, 'projects/project_tasks_delete.html', context)

@login_required
def project_subtasks_add(request, project_id, parent_task_id):
    """Add subtask to a main task"""
    if not request.user.is_superuser:
        messages.error(request, "You don't have permission to add subtasks.")
        return redirect('projects_detail', project_id=project_id)
    
    project = get_object_or_404(Project, project_id=project_id)  # Updated model name
    parent_task = get_object_or_404(ProjectTask, task_id=parent_task_id, project=project)  # Updated model name
    
    if request.method == 'POST':
        task_name = request.POST.get('task_name')
        task_description = request.POST.get('task_description')
        task_start_date = request.POST.get('task_start_date')
        task_expected_completion_date = request.POST.get('task_expected_completion_date')
        task_status = request.POST.get('task_status', 'Pending')
        task_priority = request.POST.get('task_priority', 'Medium')
        task_budgeted_cost = request.POST.get('task_budgeted_cost')
        task_actual_cost = request.POST.get('task_actual_cost')
        task_assigned_to = request.POST.get('task_assigned_to')
        task_actual_completion_date = request.POST.get('task_actual_completion_date')
        
        try:
            subtask = ProjectTask(  # Updated model name
                project=project,
                parent_task=parent_task,
                task_name=task_name,
                task_description=task_description,
                task_start_date=task_start_date if task_start_date else None,
                task_expected_completion_date=task_expected_completion_date if task_expected_completion_date else None,
                task_status=task_status,
                task_priority=task_priority,
                task_budgeted_cost=task_budgeted_cost if task_budgeted_cost else 0.00,
                task_actual_cost=task_actual_cost if task_actual_cost else 0.00,
                task_assigned_to=task_assigned_to,
                task_actual_completion_date=task_actual_completion_date if task_actual_completion_date else None
            )
            subtask.save()
            
            messages.success(request, f"Subtask '{task_name}' has been added successfully.")
            return redirect('projects_detail', project_id=project_id)
            
        except Exception as e:
            messages.error(request, f"Error adding subtask: {str(e)}")
    
    context = {
        'project': project,
        'parent_task': parent_task,
        'task_status_choices': ProjectTask.TASK_STATUS_CHOICES,  # Updated model name
        'task_priority_choices': ProjectTask.TASK_PRIORITY_CHOICES,  # Updated model name
    }
    
    return render(request, 'projects/project_subtasks_add.html', context)

@login_required
def project_gantt(request, project_id):
    """Display Gantt chart for project with tasks and subtasks"""
    project = get_object_or_404(Project.objects.select_related('prop'), project_id=project_id)
    
    # Check if returning from edit page
    from_edit = request.GET.get('from_edit', False)
    if from_edit:
        messages.success(request, "Changes saved successfully. Gantt chart has been refreshed.")
    
    # Get all main tasks for this project
    main_tasks = ProjectTask.objects.filter(
        project=project, 
        parent_task__isnull=True
    ).prefetch_related('subtasks').order_by('task_start_date', 'task_id')
    
    # Build Gantt data structure
    gantt_data = []
    task_counter = 1
    
    # Add project as the main item
    project_start = project.get_calculated_start_date()
    project_end = project.get_calculated_expected_completion()
    
    if project_start and project_end:
        project_item = {
            'id': f'project_{project.project_id}',
            'text': project.project_name,
            'start_date': project_start.strftime('%Y-%m-%d'),
            'end_date': project_end.strftime('%Y-%m-%d'),
            'duration': (project_end - project_start).days + 1,
            'progress': project.get_progress_percentage() / 100,
            'type': 'project',
            'status': project.get_calculated_status(),
            'budgeted_cost': float(project.get_calculated_budgeted_cost() or 0),
            'actual_cost': float(project.get_calculated_actual_cost() or 0),
            'open': True
        }
        gantt_data.append(project_item)
    
    # Add main tasks and their subtasks
    for task in main_tasks:
        task_start = task.get_calculated_start_date()
        task_end = task.get_calculated_expected_completion()
        
        if task_start and task_end:
            # Add main task
            task_item = {
                'id': f'task_{task.task_id}',
                'text': task.task_name,
                'start_date': task_start.strftime('%Y-%m-%d'),
                'end_date': task_end.strftime('%Y-%m-%d'),
                'duration': (task_end - task_start).days + 1,
                'progress': task.get_subtask_progress() / 100 if task.subtasks.exists() else (1.0 if task.get_calculated_status() == 'Completed' else 0.0),
                'type': 'task',  # Changed from missing to explicit 'task'
                'status': task.get_calculated_status(),
                'budgeted_cost': float(task.get_calculated_budgeted_cost() or 0),
                'actual_cost': float(task.get_calculated_actual_cost() or 0),
                'assigned_to': task.task_assigned_to or '',
                'parent': f'project_{project.project_id}' if project_start and project_end else None,
                'open': True,
                'calculated_progress_percentage': round(task.get_subtask_progress(), 1)  # For display
            }
            gantt_data.append(task_item)
            
            # Add subtasks for this main task
            subtasks = task.subtasks.filter(
                task_start_date__isnull=False,
                task_expected_completion_date__isnull=False
            ).order_by('task_start_date', 'task_id')
            
            for subtask in subtasks:
                subtask_start = subtask.task_start_date
                subtask_end = subtask.task_expected_completion_date
                
                if subtask_start and subtask_end:
                    # Calculate progress for subtask
                    subtask_progress = 0
                    if subtask.task_status == 'Completed':
                        subtask_progress = 1.0
                    elif subtask.task_status == 'In Progress':
                        subtask_progress = (subtask.task_progress_percentage or 0) / 100
                    
                    subtask_item = {
                        'id': f'subtask_{subtask.task_id}',
                        'text': subtask.task_name,
                        'start_date': subtask_start.strftime('%Y-%m-%d'),
                        'end_date': subtask_end.strftime('%Y-%m-%d'),
                        'duration': (subtask_end - subtask_start).days + 1,
                        'progress': subtask_progress,
                        'type': 'subtask',
                        'status': subtask.task_status,
                        'budgeted_cost': float(subtask.task_budgeted_cost or 0),
                        'actual_cost': float(subtask.task_actual_cost or 0),
                        'assigned_to': subtask.task_assigned_to or '',
                        'parent': f'task_{task.task_id}',  # Link to parent main task
                        'priority': subtask.task_priority,
                        'progress_percentage': subtask.task_progress_percentage or 0  # For display in bars
                    }
                    gantt_data.append(subtask_item)
    
    # If no tasks have dates, create a placeholder message
    if not gantt_data:
        # Create a simple project timeline with today's date
        from datetime import datetime
        today = datetime.now().date()
        placeholder_item = {
            'id': 'placeholder_1',
            'text': f'{project.project_name} (No dates set)',
            'start_date': today.strftime('%Y-%m-%d'),
            'duration': 30,
            'progress': 0,
            'type': 'project',
            'status': 'Pending'
        }
        gantt_data.append(placeholder_item)
    
    context = {
        'project': project,
        'main_tasks': main_tasks,
        'gantt_data': json.dumps(gantt_data),
    }
    
    return render(request, 'projects/project_gantt.html', context)

@login_required
def ajax_update_project_status(request):
    """AJAX view to update project status"""
    if request.method == 'POST' and request.user.is_superuser:
        try:
            data = json.loads(request.body)
            project_id = data.get('project_id')
            new_status = data.get('status')
            actual_completion_date = data.get('actual_completion_date')
            
            project = get_object_or_404(Project, project_id=project_id)
            project.project_status = new_status
            
            if new_status == 'Completed' and actual_completion_date:
                project.project_actual_completion_date = actual_completion_date
            elif new_status != 'Completed':
                project.project_actual_completion_date = None
            
            project.save()
            
            return JsonResponse({
                'success': True,
                'message': f"Project status updated to {new_status}"
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f"Error updating project status: {str(e)}"
            })
    
    return JsonResponse({'success': False, 'message': 'Invalid request'})

@login_required
def ajax_update_task_status(request):
    """AJAX view to update task status"""
    if request.method == 'POST' and request.user.is_superuser:
        try:
            data = json.loads(request.body)
            task_id = data.get('task_id')
            new_status = data.get('status')
            actual_completion_date = data.get('actual_completion_date')
            
            task = get_object_or_404(ProjectTask, task_id=task_id)
            task.task_status = new_status
            
            if new_status == 'Completed' and actual_completion_date:
                task.task_actual_completion_date = actual_completion_date
            elif new_status != 'Completed':
                task.task_actual_completion_date = None
            
            task.save()
            
            return JsonResponse({
                'success': True,
                'message': f"Task status updated to {new_status}"
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f"Error updating task status: {str(e)}"
            })
    
    return JsonResponse({'success': False, 'message': 'Invalid request'})

@login_required
def ajax_duplicate_project(request):
    """
    AJAX view to duplicate a project with all its tasks and subtasks,
    adjusting all dates based on the new project start date and handling budget copy options
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Only POST method allowed'})
    
    if not request.user.is_superuser:
        return JsonResponse({
            'success': False,
            'message': 'You do not have permission to duplicate projects'
        })
    
    try:
        # Parse JSON data
        data = json.loads(request.body)
        project_id = data.get('project_id')
        new_project_name = data.get('new_project_name', '').strip()
        new_project_start_date_str = data.get('new_project_start_date', '').strip()
        budget_copy_option = data.get('budget_copy_option', 'budgeted')  # 'budgeted' or 'actual'
        copy_translations = data.get('copy_translations', False)  # NEW: Flag to copy Greek translations
        
        if not project_id or not new_project_name or not new_project_start_date_str:
            return JsonResponse({
                'success': False,
                'message': 'Project ID, new project name, and start date are required'
            })
        
        # Validate budget copy option
        if budget_copy_option not in ['budgeted', 'actual']:
            budget_copy_option = 'budgeted'  # Default to budgeted if invalid option
        
        # Parse the new start date
        try:
            from datetime import datetime, timedelta
            new_project_start_date = datetime.strptime(new_project_start_date_str, '%Y-%m-%d').date()
        except ValueError:
            return JsonResponse({
                'success': False,
                'message': 'Invalid date format. Please use YYYY-MM-DD format.'
            })
        
        # Ensure project_id is an integer
        try:
            project_id = int(project_id)
        except (ValueError, TypeError):
            return JsonResponse({
                'success': False,
                'message': f'Invalid project ID: {project_id}'
            })
        
        # Get the original project
        try:
            original_project = Project.objects.get(project_id=project_id)
        except Project.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': f'Project with ID {project_id} was not found'
            })
        
        # Check if project name already exists
        if Project.objects.filter(project_name=new_project_name).exists():
            return JsonResponse({
                'success': False,
                'message': f'A project with the name "{new_project_name}" already exists'
            })
        
        # Calculate date offset if original project has a start date
        date_offset = None
        original_start_date = original_project.get_calculated_start_date()
        
        if original_start_date:
            date_offset = (new_project_start_date - original_start_date).days
        
        def adjust_date(original_date, offset_days):
            """Helper function to adjust a date by the offset"""
            if original_date and offset_days is not None:
                return original_date + timedelta(days=offset_days)
            return original_date
        
        def get_cost_for_budget(original_task, budget_option):
            """Helper function to determine which cost to use as the new budget"""
            if budget_option == 'actual':
                return original_task.task_actual_cost
            else:
                return original_task.task_budgeted_cost
        
        def copy_translation_fields(source_obj, target_obj, field_prefixes):
            """Helper function to copy Greek translation fields"""
            translations_found = False
            for prefix in field_prefixes:
                greek_field = f"{prefix}_greek"
                if hasattr(source_obj, greek_field):
                    greek_value = getattr(source_obj, greek_field, None)
                    if greek_value:
                        setattr(target_obj, greek_field, greek_value)
                        translations_found = True
            return translations_found
        
        # Use transaction to ensure all-or-nothing duplication
        with transaction.atomic():
            # Calculate new project dates
            new_project_expected_completion = None
            if original_project.get_calculated_expected_completion() and date_offset is not None:
                new_project_expected_completion = adjust_date(
                    original_project.get_calculated_expected_completion(), 
                    date_offset
                )
            
            # Calculate new project budget based on option
            new_project_total_budgeted_cost = original_project.project_total_budgeted_cost
            if budget_copy_option == 'actual':
                # Use actual cost as new budget
                new_project_total_budgeted_cost = original_project.get_calculated_actual_cost()
            
            # Create new project (copy all fields from original)
            new_project = Project.objects.create(
                project_name=new_project_name,
                project_description=original_project.project_description,
                prop=original_project.prop,  # Same property
                project_start_date=new_project_start_date,  # Use the new start date
                project_expected_completion_date=new_project_expected_completion,
                project_status='Pending',  # Reset status to Pending
                project_actual_completion_date=None,  # Clear completion date
                project_total_budgeted_cost=new_project_total_budgeted_cost,  # Use calculated budget
                project_total_actual_cost=Decimal('0.00'),  # Reset actual cost
            )
            
            # Copy Greek translations for project
            translations_copied = False
            if copy_translations:
                project_translations_found = copy_translation_fields(
                    original_project, 
                    new_project, 
                    ['project_name', 'project_description']
                )
                if project_translations_found:
                    translations_copied = True
                    new_project.save()
            
            # Get all main tasks (tasks without parent_task)
            main_tasks = ProjectTask.objects.filter(
                project=original_project,
                parent_task__isnull=True
            ).order_by('task_id')
            
            # Dictionary to map old task IDs to new task objects
            task_mapping = {}
            
            # First pass: Create all main tasks
            for original_task in main_tasks:
                # Adjust main task dates
                new_task_start_date = adjust_date(original_task.task_start_date, date_offset)
                new_task_expected_completion = adjust_date(original_task.task_expected_completion_date, date_offset)
                
                # Get the appropriate cost for the new budget
                new_task_budgeted_cost = get_cost_for_budget(original_task, budget_copy_option)
                
                new_task = ProjectTask.objects.create(
                    project=new_project,
                    task_name=original_task.task_name,
                    task_description=original_task.task_description,
                    task_start_date=new_task_start_date,
                    task_expected_completion_date=new_task_expected_completion,
                    task_budgeted_cost=new_task_budgeted_cost,
                    task_actual_cost=Decimal('0.00'),  # Reset actual cost
                    task_priority=original_task.task_priority,
                    task_status='Pending',  # Reset status to Pending
                    task_actual_completion_date=None,  # Clear completion date
                    task_assigned_to=original_task.task_assigned_to,
                    parent_task=None,  # This is a main task
                    task_progress_percentage=0,  # Reset progress
                )
                
                # Copy Greek translations for main task
                if copy_translations:
                    task_translations_found = copy_translation_fields(
                        original_task, 
                        new_task, 
                        ['task_name', 'task_description']
                    )
                    if task_translations_found:
                        translations_copied = True
                        new_task.save()
                
                task_mapping[original_task.task_id] = new_task
            
            # Second pass: Create all subtasks
            for original_main_task in main_tasks:
                subtasks = ProjectTask.objects.filter(
                    project=original_project,
                    parent_task=original_main_task
                ).order_by('task_id')
                
                for original_subtask in subtasks:
                    # Adjust subtask dates
                    new_subtask_start_date = adjust_date(original_subtask.task_start_date, date_offset)
                    new_subtask_expected_completion = adjust_date(original_subtask.task_expected_completion_date, date_offset)
                    
                    # Get the appropriate cost for the new budget
                    new_subtask_budgeted_cost = get_cost_for_budget(original_subtask, budget_copy_option)
                    
                    new_subtask = ProjectTask.objects.create(
                        project=new_project,
                        task_name=original_subtask.task_name,
                        task_description=original_subtask.task_description,
                        task_start_date=new_subtask_start_date,
                        task_expected_completion_date=new_subtask_expected_completion,
                        task_budgeted_cost=new_subtask_budgeted_cost,
                        task_actual_cost=Decimal('0.00'),  # Reset actual cost
                        task_priority=original_subtask.task_priority,
                        task_status='Pending',  # Reset status to Pending
                        task_actual_completion_date=None,  # Clear completion date
                        task_assigned_to=original_subtask.task_assigned_to,
                        parent_task=task_mapping[original_main_task.task_id],  # Link to new parent
                        task_progress_percentage=0,  # Reset progress
                    )
                    
                    # Copy Greek translations for subtask
                    if copy_translations:
                        subtask_translations_found = copy_translation_fields(
                            original_subtask, 
                            new_subtask, 
                            ['task_name', 'task_description']
                        )
                        if subtask_translations_found:
                            translations_copied = True
                            new_subtask.save()
            
            # Copy project documents if they exist
            try:
                original_documents = original_project.project_documents.all()
                for original_doc in original_documents:
                    # Note: This copies the document reference, not the actual file
                    # If you want to copy the actual files, you'll need additional logic
                    ProjectDocument.objects.create(
                        project=new_project,
                        task=None,  # Project-level document
                        document_name=f"Copy of {original_doc.document_name}" if original_doc.document_name else None,
                        document_description=original_doc.document_description,
                        document_file=original_doc.document_file,  # Same file reference
                        document_uploaded_by=request.user.username,
                    )
            except Exception as doc_error:
                # If document copying fails, log it but don't fail the entire duplication
                pass  # Silent fail for document copying
        
        # Build success message based on budget option and translations
        budget_message = ""
        if budget_copy_option == 'actual':
            budget_message = " with actual costs copied as budgeted costs"
        else:
            budget_message = " with budgeted costs copied"
        
        translation_message = ""
        if copy_translations and translations_copied:
            translation_message = " and Greek translations copied"
        elif copy_translations and not translations_copied:
            translation_message = " (no Greek translations found to copy)"
            
        success_message = f'Project "{new_project_name}" created successfully{budget_message}{translation_message}'
        if date_offset is not None:
            success_message += f' and all dates adjusted by {date_offset} days'
        
        return JsonResponse({
            'success': True,
            'message': success_message,
            'new_project_id': new_project.project_id,
            'date_offset': date_offset,
            'budget_copy_option': budget_copy_option,
            'translations_copied': translations_copied  # NEW: Return translation status
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Invalid JSON data'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'An error occurred while duplicating the project: {str(e)}'
        })

@login_required
def project_task_list(request, project_id):
    """Display task list for a specific project and assignee"""
    project = get_object_or_404(Project.objects.select_related('prop'), project_id=project_id)
    
    # Get parameters
    assigned_to = request.GET.get('assigned_to', '')
    language = request.GET.get('language', 'english')
    
    # Ensure Greek translations if language is Greek
    if language == 'greek':
        ensure_project_translations(project)
    
    # Get all main tasks for this project
    main_tasks = ProjectTask.objects.filter(
        project=project, 
        parent_task__isnull=True
    ).prefetch_related('subtasks').order_by('task_start_date', 'task_id')
    
    # Filter by assigned_to if specified
    if assigned_to:
        main_tasks = main_tasks.filter(
            Q(task_assigned_to=assigned_to) |
            Q(subtasks__task_assigned_to=assigned_to)
        ).distinct()
    
    # Build task list with hierarchy
    task_list = []
    total_tasks = 0
    completed_tasks = 0
    pending_tasks = 0
    
    # Add project as root item
    project_item = {
        'name': project.project_name,
        'name_greek': get_translated_text(
            project.project_name, 
            getattr(project, 'project_name_greek', None), 
            language
        ) if language == 'greek' else project.project_name,
        'description': project.project_description,
        'description_greek': get_translated_text(
            project.project_description, 
            getattr(project, 'project_description_greek', None), 
            language
        ) if language == 'greek' else project.project_description,
        'type': 'project',
        'status': project.get_calculated_status(),
        'start_date': project.get_calculated_start_date(),
        'end_date': project.get_calculated_expected_completion(),
        'priority': None,
        'indent_level': 0,
        'is_overdue': False
    }
    task_list.append(project_item)
    
    # Process main tasks and subtasks
    for main_task in main_tasks:
        # Check if this task or its subtasks match the assigned_to filter
        include_task = True
        if assigned_to:
            task_matches = main_task.task_assigned_to == assigned_to
            subtask_matches = main_task.subtasks.filter(task_assigned_to=assigned_to).exists()
            include_task = task_matches or subtask_matches
        
        if include_task:
            # Add main task
            is_overdue = (
                main_task.task_expected_completion_date and 
                main_task.task_expected_completion_date < timezone.now().date() and 
                main_task.task_status != 'Completed'
            )
            
            main_task_item = {
                'name': main_task.task_name,
                'name_greek': get_translated_text(
                    main_task.task_name, 
                    getattr(main_task, 'task_name_greek', None), 
                    language
                ) if language == 'greek' else main_task.task_name,
                'description': main_task.task_description,
                'description_greek': get_translated_text(
                    main_task.task_description, 
                    getattr(main_task, 'task_description_greek', None), 
                    language
                ) if language == 'greek' else main_task.task_description,
                'type': 'task',
                'status': main_task.task_status,
                'start_date': main_task.task_start_date,
                'end_date': main_task.task_expected_completion_date,
                'priority': main_task.task_priority,
                'indent_level': 1,
                'is_overdue': is_overdue
            }
            task_list.append(main_task_item)
            total_tasks += 1
            
            if main_task.task_status == 'Completed':
                completed_tasks += 1
            else:
                pending_tasks += 1
            
            # Add subtasks
            subtasks = main_task.subtasks.all().order_by('task_start_date', 'task_id')
            if assigned_to:
                subtasks = subtasks.filter(task_assigned_to=assigned_to)
            
            for subtask in subtasks:
                is_overdue = (
                    subtask.task_expected_completion_date and 
                    subtask.task_expected_completion_date < timezone.now().date() and 
                    subtask.task_status != 'Completed'
                )
                
                subtask_item = {
                    'name': subtask.task_name,
                    'name_greek': get_translated_text(
                        subtask.task_name, 
                        getattr(subtask, 'task_name_greek', None), 
                        language
                    ) if language == 'greek' else subtask.task_name,
                    'description': subtask.task_description,
                    'description_greek': get_translated_text(
                        subtask.task_description, 
                        getattr(subtask, 'task_description_greek', None), 
                        language
                    ) if language == 'greek' else subtask.task_description,
                    'type': 'subtask',
                    'status': subtask.task_status,
                    'start_date': subtask.task_start_date,
                    'end_date': subtask.task_expected_completion_date,
                    'priority': subtask.task_priority,
                    'indent_level': 2,
                    'is_overdue': is_overdue
                }
                task_list.append(subtask_item)
                total_tasks += 1
                
                if subtask.task_status == 'Completed':
                    completed_tasks += 1
                else:
                    pending_tasks += 1
    
    # Calculate completion percentage
    completion_percentage = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
    
    context = {
        'project': project,
        'task_list': task_list,
        'assigned_to': assigned_to,
        'language': language,
        'total_tasks': total_tasks,
        'completed_tasks': completed_tasks,
        'pending_tasks': pending_tasks,
        'completion_percentage': completion_percentage,
        'current_date': timezone.now(),
    }
    
    return render(request, 'projects/project_task_list.html', context)

@login_required
def get_project_assignees(request, project_id):
    """AJAX endpoint to get all assignees for a project"""
    project = get_object_or_404(Project, project_id=project_id)
    
    # Get all unique assignees from tasks and subtasks
    assignees = set()
    
    # Get assignees from main tasks
    main_tasks = ProjectTask.objects.filter(
        project=project, 
        parent_task__isnull=True,
        task_assigned_to__isnull=False
    ).exclude(task_assigned_to='')
    
    for task in main_tasks:
        if task.task_assigned_to:
            assignees.add(task.task_assigned_to.strip())
    
    # Get assignees from subtasks
    subtasks = ProjectTask.objects.filter(
        project=project, 
        parent_task__isnull=False,
        task_assigned_to__isnull=False
    ).exclude(task_assigned_to='')
    
    for subtask in subtasks:
        if subtask.task_assigned_to:
            assignees.add(subtask.task_assigned_to.strip())
    
    # Convert to sorted list
    assignees_list = sorted(list(assignees))
    
    return JsonResponse({
        'success': True,
        'assignees': assignees_list,
        'project_name': project.project_name
    })

def render_to_pdf(template_src, context_dict):
    template = get_template(template_src)
    html = template.render(context_dict)
    response = HttpResponse(content_type='application/pdf')
    pisa_status = pisa.CreatePDF(html, dest=response)
    if pisa_status.err:
        return HttpResponse('PDF generation failed', status=500)
    return response

### HOME ###
def home(request):
	results = props.objects.all().order_by('prop_country','prop_name')
	tresults = tenant.objects.filter(tenant_current="Yes")
	sresults = supplier.objects.all().order_by('supplier_country','supplier_contact_person')
	return render (request, "home.html", {"props":results, "tenant":tresults, "supplier":sresults})

### ADMIN ###
@login_required
def admin_apms(request):
    results = props.objects.all().order_by('prop_country', 'prop_name')
    tresults = tenant.objects.select_related('prop').all().order_by('tenant_name')
    return render(request, "admin_apms.html", {
        "props": results, 
        "tenant": tresults
    })

@login_required
def lease_agreement_report(request, tenant_id):
    try:
        # Get tenant and property info
        tenant_obj = get_object_or_404(tenant, pk=tenant_id)
        if not hasattr(tenant_obj, 'prop') or not tenant_obj.prop:
            raise Http404("Tenant has no property assigned")
        
        property_name = tenant_obj.prop.prop_name
        filename = f"{property_name} - Lease Agreement.pdf"
        file_path = os.path.join(settings.MEDIA_ROOT, 'lease_agreements', filename)
        
        context = {
            'tenant': tenant_obj,
            'property': tenant_obj.prop,
            'filename': filename,
            'file_exists': os.path.exists(file_path),
            'file_url': os.path.join(settings.MEDIA_URL, 'lease_agreements', filename)
        }
        return render(request, 'lease_agreement_report.html', context)
        
    except Exception as e:
        return render(request, 'error.html', {'error': str(e)})

@login_required
def serve_lease(request, filename):
    try:
        # Security validation
        if not filename.endswith(' - Lease Agreement.pdf'):
            raise Http404("Invalid filename format")
            
        file_path = os.path.join(settings.MEDIA_ROOT, 'lease_agreements', filename)
        
        if not os.path.exists(file_path):
            raise Http404("File not found")
            
        response = FileResponse(open(file_path, 'rb'), content_type='application/pdf')
        response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        return response
        
    except Exception as e:
        return Http404(str(e))

@login_required
def upload_lease_agreement(request):
    if request.method == 'POST':
        tenant_id = request.POST.get('tenant')
        uploaded_file = request.FILES.get('lease_agreement')
        
        if not uploaded_file:
            messages.error(request, "No file was uploaded.")
            return redirect('admin_apms')
        
        try:
            # Validate file
            if not uploaded_file.name.lower().endswith('.pdf'):
                raise ValueError("Only PDF files are allowed")
                
            tenant_obj = tenant.objects.get(pk=tenant_id)
            if not hasattr(tenant_obj, 'prop') or not tenant_obj.prop:
                raise ValueError("No property assigned to tenant")
                
            property_name = tenant_obj.prop.prop_name
            lease_dir = os.path.join(settings.STATIC_ROOT, 'lease_agreements')
            os.makedirs(lease_dir, exist_ok=True)
            
            filename = f"{property_name} - Lease Agreement.pdf"
            file_path = os.path.join(lease_dir, filename)
            
            # Save file
            with open(file_path, 'wb+') as destination:
                for chunk in uploaded_file.chunks():
                    destination.write(chunk)
            
            messages.success(request, f"Lease agreement uploaded successfully!")
            return redirect('admin_apms')
            
        except Exception as e:
            messages.error(request, f"Error: {str(e)}")
        
        return redirect('admin_apms')
    return redirect('admin_apms')

@login_required
def serve_lease(request, filename):
    """Secure file serving for exact filename format"""
    try:
        # Verify filename format
        if not filename.endswith(' - Lease Agreement.pdf'):
            raise Http404("Invalid filename format")
            
        file_path = os.path.join(settings.STATIC_ROOT, 'lease_agreements', filename)
        
        if not os.path.exists(file_path):
            raise Http404("Lease agreement not found")
            
        # Serve with cache-control headers
        response = FileResponse(open(file_path, 'rb'), content_type='application/pdf')
        response['Cache-Control'] = 'no-store, must-revalidate'
        response['Pragma'] = 'no-cache'
        return response
        
    except Exception as e:
        messages.error(request, f"Error serving file: {str(e)}")
        return redirect('admin_apms')

@login_required
def upload_title_deed(request):
    if request.method == 'POST':
        # Get the selected property name
        property_name = request.POST.get('property')
        
        # Get the uploaded file
        uploaded_file = request.FILES.get('title_deed')
        
        if not uploaded_file:
            messages.error(request, "No file was uploaded.")
            return redirect('admin_apms')
        
        # Validate file extension
        if not uploaded_file.name.lower().endswith('.pdf'):
            messages.error(request, "Only PDF files are allowed.")
            return redirect('admin_apms')
        
        # Create the title_deeds directory if it doesn't exist
        title_deeds_dir = os.path.join(settings.STATIC_ROOT, 'title_deeds')
        os.makedirs(title_deeds_dir, exist_ok=True)
        
        # Create the filename
        filename = f'{property_name} - Title Deed.pdf'
        file_path = os.path.join(title_deeds_dir, filename)
        
        # Save the file
        try:
            # Delete existing file if it exists
            if os.path.exists(file_path):
                os.remove(file_path)
                
            with open(file_path, 'wb+') as destination:
                for chunk in uploaded_file.chunks():
                    destination.write(chunk)
            messages.success(request, f"Title deed for {property_name} uploaded successfully!")
        except Exception as e:
            messages.error(request, f"Error saving file: {str(e)}")
        
        return redirect('admin_apms')
    
    return redirect('admin_apms')

@login_required
def admin_clear(request):
	import os
	import glob
	file_path = "C:/Users/DemetrisManias/Desktop/code/djangoproject/static/reports/*.pdf"
	files = glob.glob(file_path)
	for f in files:
		os.remove(f)
	return redirect("admin_apms")

@login_required
def admin_unpaid(request):
	import open_invoices
	rep_output = "Email"
	check = "Yes"
	email = "demetrimanias@gmail.com"
	fname = "Demetri"
	open_invoices.open_invoices(rep_output, check, email, fname)
#	email = "stella.simitopoulos@alivente.com"
#	fname = "Stella"
#	open_invoices.open_invoices(rep_output, check, email, fname)
	return redirect("admin_apms")

@login_required
def admin_renewals(request):
	import lease_renewal
	rep_output = "Email"
	check = "Yes"
	email = "demetrimanias@gmail.com"
	fname = "Demetri"
	lease_renewal.lease_renewal(rep_output,check, email, fname)
#	email = "stella.simitopoulos@alivente.com"
#	fname = "Stella"
#	lease_renewal.lease_renewal(rep_output,check, email, fname)
	return redirect("admin_apms")

@login_required
def admin_invoices(request):
	import open_invoices
	today = date.today()
	months = ('Month','January','February','March','April','May','June','July','August','September','October','November','December')
	open_invoices.create_invoices(months[today.month],today.year,request)
	return redirect("admin_apms")

### DASHBOARD ###
@login_required
def property_management_dashboard(request):
    """
    Main property dashboard view with spoke-and-wheel interface
    """
    try:
        # Get all properties for the dropdown
        properties = props.objects.filter(prop_status='Active').order_by('prop_name')
        
        # Check if a specific property was selected
        selected_property_id = request.GET.get('property')
        selected_property = None
        
        if selected_property_id:
            try:
                selected_property = props.objects.get(prop_id=selected_property_id)
            except props.DoesNotExist:
                messages.error(request, f"Property with ID {selected_property_id} not found.")
        
        context = {
            'properties': properties,
            'selected_property': selected_property,
        }
        
        return render(request, 'property_management_dashboard.html', context)
        
    except Exception as e:
        messages.error(request, f"Error loading dashboard: {str(e)}")
        return redirect('properties')

@login_required
def property_detail(request, property_id, box_type):
    property_obj = get_object_or_404(props, prop_id=property_id)
    
    # Get the active tenant for this property (there should only be one)
    active_tenant = tenant.objects.filter(
        prop=property_obj, 
        tenant_current='Yes'
    ).first()
    
    # Get open invoices data for this property
    open_invoices_data = None
    total_invoices_amount = 0
    
    # Lease renewal data
    lease_renewal_data = None
    
    # Issues data for this specific property
    property_issues = None
    resolved_count = 0
    unresolved_count = 0
    total_issues_count = 0
    
    # Valuation data for this specific property
    property_valuation = None
    
    # Revenue data for this specific property
    property_revenues = None
    total_revenue_amount = 0
    
    # Budgeted expenses data for this specific property
    property_budgeted_expenses = None
    total_budgeted_expense_amount = 0
    
    # Actual expenses data for this specific property
    property_actual_expenses = None
    actual_expense_years = []
    selected_actual_year = None
    
    if active_tenant:
        # Get all unpaid invoices for this tenant
        unpaid_invoices = invoices.objects.filter(
            tenant=active_tenant
        ).exclude(
            invoice_paid='Yes'  # Exclude paid invoices
        ).order_by('invoice_date')
        
        # Calculate days overdue and prepare data
        open_invoices_data = []
        today = timezone.now().date()
        
        for invoice in unpaid_invoices:
            # Calculate due date (invoice_date + payment_terms)
            payment_terms = active_tenant.tenant_payment_terms or 0
            due_date = invoice.invoice_date + timedelta(days=payment_terms)
            
            # Calculate days overdue
            days_overdue = (today - due_date).days if today > due_date else 0
            
            # Use the actual invoice amount if available, otherwise fall back to tenant rent
            invoice_amount = getattr(invoice, 'invoice_amount', None) or active_tenant.tenant_rent
            
            open_invoices_data.append({
                'invoice_date': invoice.invoice_date,
                'due_date': due_date,
                'days_overdue': days_overdue,
                'overdue': days_overdue > 0,
                'amount': invoice_amount
            })
            
            # Add to total amount
            total_invoices_amount += invoice_amount
        
        # Lease renewal logic for this specific property
        if box_type == 'lease-renewals':
            lease_renewal_data = {
                'tenant': active_tenant,
                'property': property_obj,
                'needs_renewal': False,
                'renewal_date': None,
                'status': 'current',
                'message': None
            }
            
            if active_tenant.tenant_lease_end_date:
                # Calculate renewal contact date
                renewal_period = active_tenant.tenant_renewal_period or 30
                renewal_contact_date = active_tenant.tenant_lease_end_date - timedelta(days=renewal_period)
                
                # Check if renewal is needed
                if today >= renewal_contact_date:
                    lease_renewal_data['needs_renewal'] = True
                    lease_renewal_data['renewal_date'] = renewal_contact_date
                    
                    # Check renewal status
                    if active_tenant.tenant_renewal_status == 'declined':
                        lease_renewal_data['status'] = 'declined'
                        lease_renewal_data['message'] = f"TENANT DECLINED RENEWAL - LEASE EXPIRES {active_tenant.tenant_lease_end_date}"
                    elif active_tenant.tenant_renewal_status == 'new_lease_signed':
                        lease_renewal_data['status'] = 'renewed'
                        lease_renewal_data['message'] = "NEW LEASE SIGNED"
                    else:
                        lease_renewal_data['status'] = 'pending'
                        lease_renewal_data['message'] = f"RENEWAL CONTACT REQUIRED BY {renewal_contact_date}"
    
    elif box_type == 'lease-renewals':
        # No active tenant - property is vacant
        lease_renewal_data = {
            'tenant': None,
            'property': property_obj,
            'status': 'vacant',
            'message': "NO CURRENT TENANT - NEED NEW TENANT"
        }
    
    # Issues logic - process for any box_type but only use data when box_type is 'issues'
    if box_type == 'issues':
        # Get all issues for this property, ordered by date (most recent first)
        property_issues = issues.objects.filter(
            prop=property_obj
        ).order_by('-issues_date_logged')
        
        # Calculate issue counts
        total_issues_count = property_issues.count()
        resolved_count = property_issues.filter(issues_status='Resolved').count()
        
        # Updated logic: Include both "Unresolved" AND "Issue" status as unresolved
        unresolved_count = property_issues.filter(
            issues_status__in=['Unresolved', 'Issue']
        ).count()
    
    # Valuation logic - process when box_type is 'valuation'
    if box_type == 'valuation':
        # Get valuation data for this property
        try:
            property_valuation = prop_values.objects.get(prop=property_obj)
            
            # Calculate value change in the view
            if property_valuation.prop_values_current_value and property_valuation.prop_values_purchase_price:
                difference = property_valuation.prop_values_current_value - property_valuation.prop_values_purchase_price
                if property_valuation.prop_values_purchase_price > 0:
                    percentage = (difference / property_valuation.prop_values_purchase_price) * 100
                else:
                    percentage = 0
                
                # Add calculated values to the valuation object
                property_valuation.value_difference = difference
                property_valuation.value_percentage = percentage
            else:
                property_valuation.value_difference = 0
                property_valuation.value_percentage = 0
                
        except prop_values.DoesNotExist:
            property_valuation = None
    
    # Revenue logic - process when box_type is 'revenues'
    if box_type == 'revenues':
        # Get all revenue data for this property
        property_revenues = property_obj.revenue_set.all().order_by('revenue_line_types__revenue_line_types_name', 'revenue_types__revenue_types_name')
        
        # Calculate total revenue amount
        total_revenue_amount = sum(rev.revenue_amount for rev in property_revenues)
    
    # Budgeted Expenses logic - process when box_type is 'budgeted-expenses'
    if box_type == 'budgeted-expenses':
        # Get all budgeted expense data for this property, sorted by expense line type
        property_budgeted_expenses = property_obj.expense_set.all().order_by('expense_line_types__expense_line_types_name', 'expense_types__expense_types_name')
        
        # Calculate total budgeted expense amount
        total_budgeted_expense_amount = sum(exp.expense_amount for exp in property_budgeted_expenses)
    
    # Actual Expenses logic - process when box_type is 'actual-expenses'
    if box_type == 'actual-expenses':
        from django.db.models import Q
        
        # Get selected year from request or default to current year
        selected_actual_year = request.GET.get('year')
        current_year = timezone.now().year
        
        # Get all years that have actual expenses for this property (approved and paid only)
        actual_expense_years = list(
            property_obj.act_expense_set.filter(
                act_expense_approved='Yes',
                act_expense_paid='Yes'
            ).dates('act_expense_date', 'year', order='DESC').distinct()
        )
        actual_expense_years = [date.year for date in actual_expense_years]
        
        # Default to the latest year if no year selected
        if not selected_actual_year and actual_expense_years:
            selected_actual_year = actual_expense_years[0]
        elif not selected_actual_year:
            selected_actual_year = current_year
        else:
            selected_actual_year = int(selected_actual_year)
        
        # Get actual expenses for the selected year (only approved and paid)
        property_actual_expenses = property_obj.act_expense_set.filter(
            act_expense_date__year=selected_actual_year,
            act_expense_approved='Yes',
            act_expense_paid='Yes'
        ).order_by('-act_expense_date')
        
        # Calculate total actual expenses amount
        total_actual_expense_amount = sum(exp.act_expense_amount for exp in property_actual_expenses)
    
    # Map box types to display names
    box_type_display_map = {
        'title-deed': 'Title Deed',
        'property-report': 'Property Report',
        'tenant': 'Tenant Information',
        'actual-expenses': 'Actual Expenses',
        'issues': 'Property Issues',
        'valuation': 'Property Valuation',
        'profit-loss': 'Profit & Loss',
        'revenues': 'Revenues',
        'expenses': 'Budgeted Expenses',
        'open-invoices': 'Open Invoices',
        'lease-renewals': 'Lease Renewals',
        'lease': 'Lease Details',
    }
    
    context = {
        'property': property_obj,
        'active_tenant': active_tenant,
        'open_invoices_data': open_invoices_data,
        'total_invoices_amount': total_invoices_amount,
        'lease_renewal_data': lease_renewal_data,
        'property_issues': property_issues,
        'resolved_count': resolved_count,
        'unresolved_count': unresolved_count,
        'total_issues_count': total_issues_count,
        'property_valuation': property_valuation,
        'property_revenues': property_revenues,
        'total_revenue_amount': total_revenue_amount,
        'property_budgeted_expenses': property_budgeted_expenses,
        'total_budgeted_expense_amount': total_budgeted_expense_amount,
        'property_actual_expenses': property_actual_expenses,
        'actual_expense_years': actual_expense_years,
        'selected_actual_year': selected_actual_year,
        'total_actual_expense_amount': locals().get('total_actual_expense_amount', 0),
        'box_type': box_type,
        'box_type_display': box_type_display_map.get(box_type, box_type.title()),
        'today': timezone.now().date(),
    }
    
    return render(request, 'property_detail.html', context)

@login_required
def dashboard_pl(request, property_id):
    """
    Dedicated view for Profit & Loss dashboard
    """
    property_obj = get_object_or_404(props, prop_id=property_id)
    
    from django.db.models import Sum, Q
    from collections import defaultdict
    
    # Get selected year from request
    selected_year = request.GET.get('year', 'budget')
    
    # Get available years for this property (from actual expenses only since revenues/expenses are budget data)
    actual_expense_years_obj = set(property_obj.act_expense_set.filter(
        act_expense_approved='Yes',
        act_expense_paid='Yes'
    ).dates('act_expense_date', 'year', order='DESC').distinct())
    
    # Convert to integers and sort
    available_years = sorted([date.year for date in actual_expense_years_obj], reverse=True)
    
    # Set display name for selected year
    if selected_year == 'budget':
        selected_year_display = 'Budget'
    else:
        try:
            selected_year = int(selected_year)
            selected_year_display = str(selected_year)
        except (ValueError, TypeError):
            selected_year = 'budget'
            selected_year_display = 'Budget'
    
    # Get revenue and expense line types - using correct model names
    revenue_line_types_queryset = revenue_line_types.objects.all().order_by('revenue_line_types_name')
    expense_line_types_queryset = expense_line_types.objects.all().order_by('expense_line_types_name')
    
    # Initialize totals dictionaries
    property_revenue_totals = {}
    property_expense_totals = {}
    
    # Initialize monthly totals
    months = ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec']
    property_revenue_total = {month: 0 for month in months}
    property_revenue_total['year'] = 0
    property_expense_total = {month: 0 for month in months}
    property_expense_total['year'] = 0
    property_actual_expense_total = {month: 0 for month in months}
    property_actual_expense_total['year'] = 0
    
    # Process revenues for this property (using monthly fields)
    for line_type in revenue_line_types_queryset:
        line_totals = {month: 0 for month in months}
        line_totals['total'] = 0
        
        # Get revenues for this line type and property
        revenues = property_obj.revenue_set.filter(
            revenue_line_types=line_type
        )
        
        # Sum revenues by month using the monthly fields
        for rev in revenues:
            line_totals['jan'] += rev.revenue_jan or 0
            line_totals['feb'] += rev.revenue_feb or 0
            line_totals['mar'] += rev.revenue_mar or 0
            line_totals['apr'] += rev.revenue_apr or 0
            line_totals['may'] += rev.revenue_may or 0
            line_totals['jun'] += rev.revenue_jun or 0
            line_totals['jul'] += rev.revenue_jul or 0
            line_totals['aug'] += rev.revenue_aug or 0
            line_totals['sep'] += rev.revenue_sep or 0
            line_totals['oct'] += rev.revenue_oct or 0
            line_totals['nov'] += rev.revenue_nov or 0
            line_totals['dec'] += rev.revenue_dec or 0
        
        # Calculate total for this line type
        line_totals['total'] = sum(line_totals[month] for month in months)
        
        property_revenue_totals[line_type.revenue_line_types_id] = line_totals
        
        # Add to property totals
        for month in months:
            property_revenue_total[month] += line_totals[month]
        property_revenue_total['year'] += line_totals['total']
    
    # Process budgeted expenses for this property (using monthly fields)
    for line_type in expense_line_types_queryset:
        line_totals = {month: 0 for month in months}
        line_totals['total'] = 0
        
        # Get expenses for this line type and property
        expenses = property_obj.expense_set.filter(
            expense_line_types=line_type
        )
        
        # Sum expenses by month using the monthly fields
        for exp in expenses:
            # Your expense model has monthly fields
            line_totals['jan'] += exp.expense_jan or 0
            line_totals['feb'] += exp.expense_feb or 0
            line_totals['mar'] += exp.expense_mar or 0
            line_totals['apr'] += exp.expense_apr or 0
            line_totals['may'] += exp.expense_may or 0
            line_totals['jun'] += exp.expense_jun or 0
            line_totals['jul'] += exp.expense_jul or 0
            line_totals['aug'] += exp.expense_aug or 0
            line_totals['sep'] += exp.expense_sep or 0
            line_totals['oct'] += exp.expense_oct or 0
            line_totals['nov'] += exp.expense_nov or 0
            line_totals['dec'] += exp.expense_dec or 0
        
        # Calculate total for this line type
        line_totals['total'] = sum(line_totals[month] for month in months)
        
        property_expense_totals[line_type.expense_line_types_id] = line_totals
        
        # Add to property totals
        for month in months:
            property_expense_total[month] += line_totals[month]
        property_expense_total['year'] += line_totals['total']
    
    # Process actual expenses for this property (only if not budget view)
    if selected_year != 'budget':
        actual_expenses = property_obj.act_expense_set.filter(
            act_expense_date__year=selected_year,
            act_expense_approved='Yes',
            act_expense_paid='Yes'
        ).values('act_expense_date', 'act_expense_amount')
        
        # Sum actual expenses by month
        for exp in actual_expenses:
            month_name = months[exp['act_expense_date'].month - 1]
            property_actual_expense_total[month_name] += exp['act_expense_amount']
            property_actual_expense_total['year'] += exp['act_expense_amount']
    
    context = {
        'property': property_obj,
        'available_years': available_years,
        'selected_year': selected_year,
        'selected_year_display': selected_year_display,
        'revenue_line_types': revenue_line_types_queryset,  # Updated variable name
        'expense_line_types': expense_line_types_queryset,  # Updated variable name
        'property_revenue_totals': property_revenue_totals,
        'property_expense_totals': property_expense_totals,
        'property_revenue_total': property_revenue_total,
        'property_expense_total': property_expense_total,
        'property_actual_expense_total': property_actual_expense_total,
        'today': timezone.now().date(),
    }
    
    return render(request, 'dashboard_pl.html', context)

### FINANCE ###
@login_required
def finance(request):
#	return redirect("finance")
	return render (request, "finance.html", {})

@login_required
def finance_revenue(request):
	prop_output = request.POST.get('propname')
	if prop_output is None or prop_output == "All":
			props_data = props.objects.prefetch_related(
				Prefetch(
					'revenue_set',
					queryset=revenue.objects.select_related('revenue_line_types', 'revenue_types')
				)
			).all().order_by('prop_country', 'prop_name')
	else:
		if prop_output is not None:
				props_data = props.objects.prefetch_related(
					Prefetch(
						'revenue_set',
						queryset=revenue.objects.select_related('revenue_line_types', 'revenue_types')
					)
				).all().order_by('prop_country', 'prop_name').filter(prop_name=prop_output)
	return render(request, "finance_revenue.html", {
		"props_data": props_data,
	})

@login_required
def finance_revenue_add(request):
    props_data = props.objects.all().order_by('prop_country', 'prop_name')
    revenue_types_list = revenue_types.objects.all()  # Fetch all revenue types
    revenue_line_types_list = revenue_line_types.objects.all()  # Fetch all revenue line types

    return render(request, "finance_revenue_add.html", {
        "props_data": props_data,
        "revenue_types": revenue_types_list,  # Pass to template
        "revenue_line_types": revenue_line_types_list,  # Pass to template
    })

@login_required
def finance_revenue_commit(request):
    if request.method == "POST":
        # Extract form data
        prop_id = request.POST.get('prop')
        rlt_id = request.POST.get('revenue_line_types')  # revenue_line_types_id
        rt_id = request.POST.get('revenue_types')    # revenue_types_id
        revenue_amount = request.POST.get('revenue_amount')

        # Fetch the revenue_type to check monthly flags
        try:
            revenue_type = revenue_types.objects.get(revenue_types_id=rt_id)
        except revenue_types.DoesNotExist:
            messages.error(request, "Invalid Revenue Type")
            return redirect('finance_revenue_add')
        # Initialize monthly revenue data
        monthly_data = {
            'prop_id': prop_id,
            'revenue_line_types_id': rlt_id,
            'revenue_types_id': rt_id,
            'revenue_amount': revenue_amount,
        }
        # Check each month and set revenue_jan, revenue_feb, etc. if "YES"
        months = ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 
                 'jul', 'aug', 'sep', 'oct', 'nov', 'dec']
        
        for month in months:
            if getattr(revenue_type, f'revenue_types_{month}') == "Yes":
                monthly_data[f'revenue_{month}'] = revenue_amount
                print(monthly_data[f'revenue_{month}'])
        # Create or update the revenue record
        revenue.objects.update_or_create(
            prop_id=prop_id,
            revenue_line_types_id=rlt_id,
            revenue_types_id=rt_id,
            defaults=monthly_data
        )
        messages.success(request, "Revenue Updated Successfully")
        return redirect('finance_revenue')
    # If not a POST request, redirect back
    return redirect('finance_revenue_add')

@login_required
def finance_revenue_edit(request, revenue_id):
    rev = get_object_or_404(revenue, pk=revenue_id)
    props_data = props.objects.all().order_by('prop_country', 'prop_name')
    revenue_types_list = revenue_types.objects.all()
    revenue_line_types_list = revenue_line_types.objects.all()
    form = RevenueForm(instance=rev)  # Use your actual form class
    
    return render(request, "finance_revenue_edit.html", {
        "rev": rev,  # Changed from rresults to rev for clarity
        "props_data": props_data,
        "revenue_types": revenue_types_list,
        "revenue_line_types": revenue_line_types_list,
        "form": form,  # Pass the form to template
    })

@login_required
def finance_revenue_edit_commit(request, revenue_id):
    rev = get_object_or_404(revenue, pk=revenue_id)
    
    if request.method == "POST":
        # Extract form data
        prop_id = request.POST.get('prop')
        rlt_id = request.POST.get('revenue_line_types')
        rt_id = request.POST.get('revenue_types')
        revenue_amount = request.POST.get('revenue_amount')

        # Fetch the revenue_type to check monthly flags
        try:
            revenue_type = revenue_types.objects.get(revenue_types_id=rt_id)
        except revenue_types.DoesNotExist:
            messages.error(request, "Invalid Revenue Type")
            return redirect('finance_revenue_edit', revenue_id=revenue_id)

        # Initialize monthly revenue data
        monthly_data = {
            'prop_id': prop_id,
            'revenue_line_types_id': rlt_id,
            'revenue_types_id': rt_id,
            'revenue_amount': revenue_amount,
        }

        # Check each month and set revenue_jan, revenue_feb, etc. if "YES"
        months = ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 
                 'jul', 'aug', 'sep', 'oct', 'nov', 'dec']
        
        for month in months:
            if getattr(revenue_type, f'revenue_types_{month}') == "Yes":
                monthly_data[f'revenue_{month}'] = revenue_amount
            else:
                monthly_data[f'revenue_{month}'] = None  # Clear if not applicable

        # Update the revenue record
        for key, value in monthly_data.items():
            setattr(rev, key, value)
        rev.save()

        messages.success(request, "Revenue Updated Successfully")
        return redirect('finance_revenue')

    # If GET request, show the form
    props_data = props.objects.all().order_by('prop_country', 'prop_name')
    revenue_types_list = revenue_types.objects.all()
    revenue_line_types_list = revenue_line_types.objects.all()
    form = RevenueForm(instance=rev)
    
    return render(request, "finance_revenue_edit.html", {
        "rev": rev,
        "props_data": props_data,
        "revenue_types": revenue_types_list,
        "revenue_line_types": revenue_line_types_list,
        "form": form,
    })

@login_required
def finance_revenue_types(request):
    rev_types = revenue_types.objects.all()
    return render(request, "finance_revenue_types.html", {
        "rtresults": rev_types,
    })

@login_required
def finance_revenue_types_add(request):
    rev_types = revenue_types.objects.all().order_by('revenue_types_name')
    return render(request, "finance_revenue_types_add.html", {"rtresults":rev_types})

@login_required
def finance_revenue_types_commit(request):
    if request.method == "POST":
        form = RevenueTypesForm(request.POST or None)
        if form.is_valid():
            form.save()
            messages.success(request, "Revenue Types Added Successfully")
    rev_types = revenue_types.objects.all()
    return render(request, "finance_revenue_types.html", {"rtresults":rev_types})

@login_required
def finance_revenue_types_edit(request, revenue_types_id):
    rev_types = revenue_types.objects.filter(pk=revenue_types_id)
    return render(request, "finance_revenue_types_edit.html", {"rtresults":rev_types})

@login_required
def finance_revenue_types_edit_commit(request, revenue_types_id):
    rev = get_object_or_404(revenue_types, pk=revenue_types_id)
    all_types = revenue_types.objects.all().order_by('revenue_types_name')
    if request.method == "POST":
        name = request.POST.get('revenue_types_name')
        # Check for duplicates (case-insensitive, excluding current record)
        if revenue_types.objects.filter(
            revenue_types_name__iexact=name
        ).exclude(
            pk=revenue_types_id
        ).exists():
            messages.error(request, "No duplicate Revenue Types Allowed")
            return render(request, "finance_revenue_types.html", {
                "rtresults": all_types,
                "rev": rev,
                "name_error": True
            })
        form = RevenueTypesForm(request.POST, instance=rev)
        if form.is_valid():
            form.save()
            messages.success(request, "Revenue Type Edited Successfully")
            return redirect('finance_revenue_types')
    # If GET request or form invalid
    return render(request, "finance_revenue_types.html", {
        "rtresults": all_types,
        "rev": rev
    })

@login_required
def finance_revenue_line_types(request):
    rev_line_types = revenue_line_types.objects.all()
    return render(request, "finance_revenue_line_types.html", {
        "rltresults": rev_line_types,
    })

@login_required
def finance_revenue_line_types_add(request):
    rev_line_types = revenue_line_types.objects.all().order_by('revenue_line_types_name')
    return render(request, "finance_revenue_line_types_add.html", {"rltresults":rev_line_types})

@login_required
def finance_revenue_line_types_commit(request):
    if request.method == "POST":
        form = RevenueLineForm(request.POST or None)
        if form.is_valid():
            form.save()
            messages.success(request, "Revenue Line Types Added Successfully")
    rev_line_types = revenue_line_types.objects.all()
    return render(request, "finance_revenue_line_types.html", {"rltresults":rev_line_types})

@login_required
def finance_revenue_line_types_edit(request, revenue_line_types_id):
    rev_line_types = revenue_line_types.objects.filter(pk=revenue_line_types_id)
    return render(request, "finance_revenue_line_types_edit.html", {"rltresults":rev_line_types})

@login_required
def finance_revenue_line_types_edit_commit(request, revenue_line_types_id):
    rev = get_object_or_404(revenue_line_types, pk=revenue_line_types_id)
    all_types = revenue_line_types.objects.all().order_by('revenue_line_types_name')
    if request.method == "POST":
        name = request.POST.get('revenue_line_types_name')
        # Check for duplicates (case-insensitive, excluding current record)
        if revenue_line_types.objects.filter(
            revenue_line_types_name__iexact=name
        ).exclude(
            pk=revenue_line_types_id
        ).exists():
            messages.error(request, "No duplicate Revenue Line Types Allowed")
            return render(request, "finance_revenue_line_types.html", {
                "rltresults": all_types,
                "rev": rev,
                "name_error": True
            })
        form = RevenueLineForm(request.POST, instance=rev)
        if form.is_valid():
            form.save()
            messages.success(request, "Revenue Line Type Edited Successfully")
            return redirect('finance_revenue_line_types')
    
    # If GET request or form invalid
    return render(request, "finance_revenue_line_types.html", {
        "rltresults": all_types,
        "rev": rev
    })

@login_required
def finance_expense(request):
    prop_output = request.POST.get('propname')
    if prop_output is None or prop_output == "All":
            props_data = props.objects.prefetch_related(
                Prefetch(
                    'expense_set',
                    queryset=expense.objects.select_related('expense_line_types', 'expense_types')
                )
            ).all().order_by('prop_country', 'prop_name')
    else:
        if prop_output is not None:
                props_data = props.objects.prefetch_related(
                    Prefetch(
                        'expense_set',
                        queryset=expense.objects.select_related('expense_line_types', 'expense_types')
                    )
                ).all().order_by('prop_country', 'prop_name').filter(prop_name=prop_output)
    return render(request, "finance_expense.html", {
        "props_data": props_data,
    })

@login_required
def finance_expense_add(request):
    # Get properties with their values (using select_related if it's a ForeignKey)
    props_data = props.objects.all().order_by('prop_country', 'prop_name')
    # Annotate each property with its current value (0 if none exists)
    props_data = props_data.annotate(
        current_value=Coalesce(
            Subquery(
                prop_values.objects.filter(prop_id=OuterRef('prop_id'))
                .values('prop_values_current_value')[:1]
            ),
            0
        )
    )
    expense_types_list = expense_types.objects.all()
    expense_line_types_list = expense_line_types.objects.all().order_by('expense_line_types_name')
    return render(request, "finance_expense_add.html", {
        "props_data": props_data,
        "expense_types": expense_types_list,
        "expense_line_types": expense_line_types_list,
    })

@login_required
def finance_expense_commit(request):
    if request.method == "POST":
        # Extract form data
        prop_id = request.POST.get('prop')
        elt_id = request.POST.get('expense_line_types')
        et_id = request.POST.get('expense_types')  # Fix: Changed from 'expense_types' to match your form
        expense_amount = request.POST.get('expense_amount')
        prorata_data = request.POST.get('prorata_calculation_data')

        # Define months list outside the prorata block
        months = ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 
                 'jul', 'aug', 'sep', 'oct', 'nov', 'dec']

        try:
            expense_type = expense_types.objects.get(expense_types_id=et_id)
        except expense_types.DoesNotExist:
            messages.error(request, "Invalid Expense Type")
            return redirect('finance_expense_add')

        # Check if this is a pro-rata expense with multiple properties
        if prorata_data:
            try:
                prorata_data = json.loads(prorata_data)
                selected_properties = prorata_data.get('selected_properties', [])
                
                # Create an expense for each selected property
                for property_data in selected_properties:
                    monthly_data = {
                        'prop_id': property_data['prop_id'],
                        'expense_line_types_id': elt_id,
                        'expense_types_id': et_id,
                        'expense_amount': property_data['calculated_amount'],
                    }
                    
                    for month in months:
                        if getattr(expense_type, f'expense_types_{month}') == "Yes":
                            monthly_data[f'expense_{month}'] = property_data['calculated_amount']
                    
                    expense.objects.update_or_create(
                        prop_id=property_data['prop_id'],
                        expense_line_types_id=elt_id,
                        expense_types_id=et_id,
                        defaults=monthly_data
                    )
                
                messages.success(request, f"{len(selected_properties)} pro-rata expenses created successfully")
                return redirect('finance_expense')
                
            except json.JSONDecodeError:
                messages.error(request, "Invalid pro-rata data")
                return redirect('finance_expense_add')

        # Handle non-pro-rata or single property expense
        monthly_data = {
            'prop_id': prop_id,
            'expense_line_types_id': elt_id,
            'expense_types_id': et_id,
            'expense_amount': expense_amount,
        }
        
        for month in months:
            if getattr(expense_type, f'expense_types_{month}') == "Yes":
                monthly_data[f'expense_{month}'] = expense_amount
        
        expense.objects.update_or_create(
            prop_id=prop_id,
            expense_line_types_id=elt_id,
            expense_types_id=et_id,
            defaults=monthly_data
        )
        
        messages.success(request, "Expense Updated Successfully")
        return redirect('finance_expense')
    
    return redirect('finance_expense_add')

@login_required
def finance_expense_edit(request, expense_id):
    # Get the existing expense
    try:
        existing_expense = expense.objects.get(expense_id=expense_id)
    except expense.DoesNotExist:
        messages.error(request, "Expense not found")
        return redirect('finance_expense')

    # Get properties with their values (using select_related if it's a ForeignKey)
    props_data = props.objects.all().order_by('prop_country', 'prop_name')
    # Annotate each property with its current value (0 if none exists)
    props_data = props_data.annotate(
        current_value=Coalesce(
            Subquery(
                prop_values.objects.filter(prop_id=OuterRef('prop_id'))
                .values('prop_values_current_value')[:1]
            ),
            0
        )
    )
    
    expense_types_list = expense_types.objects.all()
    expense_line_types_list = expense_line_types.objects.all().order_by('expense_line_types_name')
    
    return render(request, "finance_expense_edit.html", {
        "props_data": props_data,
        "expense_types": expense_types_list,
        "expense_line_types": expense_line_types_list,
        "existing_expense": existing_expense,
    })

@login_required
def finance_expense_edit_commit(request, expense_id):
    # Get the existing expense first
    try:
        existing_expense = expense.objects.get(expense_id=expense_id)
    except expense.DoesNotExist:
        messages.error(request, "Expense not found")
        return redirect('finance_expense')

    if request.method == "POST":
        # Extract form data
        prop_id = request.POST.get('prop')
        elt_id = request.POST.get('expense_line_types')
        et_id = request.POST.get('expense_types')
        expense_amount = request.POST.get('expense_amount')
        prorata_data = request.POST.get('prorata_calculation_data')

        # Define months list outside the prorata block
        months = ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 
                 'jul', 'aug', 'sep', 'oct', 'nov', 'dec']

        try:
            expense_type = expense_types.objects.get(expense_types_id=et_id)
        except expense_types.DoesNotExist:
            messages.error(request, "Invalid Expense Type")
            return redirect('finance_expense_edit', expense_id=expense_id)

        # Check if this is a pro-rata expense with multiple properties
        if prorata_data and prorata_data != 'undefined':
            try:
                prorata_data = json.loads(prorata_data)
                selected_properties = prorata_data.get('selected_properties', [])
                
                if not selected_properties:
                    messages.error(request, "No properties selected for pro-rata distribution")
                    return redirect('finance_expense_edit', expense_id=expense_id)
                
                # For pro-rata expenses, we need to handle the original expense differently
                # First, get all existing expenses with the ORIGINAL line type and expense type
                original_expenses = expense.objects.filter(
                    expense_line_types_id=existing_expense.expense_line_types_id,
                    expense_types_id=existing_expense.expense_types_id
                )
                
                # Delete all original pro-rata expenses (they will be recreated)
                original_expenses.delete()
                
                # Create new expenses for each selected property
                for property_data in selected_properties:
                    monthly_data = {
                        'prop_id': property_data['prop_id'],
                        'expense_line_types_id': elt_id,
                        'expense_types_id': et_id,
                        'expense_amount': property_data['calculated_amount'],
                    }
                    
                    for month in months:
                        if getattr(expense_type, f'expense_types_{month}') == "Yes":
                            monthly_data[f'expense_{month}'] = property_data['calculated_amount']
                    
                    # Create new expense
                    expense.objects.create(**monthly_data)
                
                messages.success(request, f"{len(selected_properties)} pro-rata expenses updated successfully")
                return redirect('finance_expense')
                
            except json.JSONDecodeError:
                messages.error(request, "Invalid pro-rata data")
                return redirect('finance_expense_edit', expense_id=expense_id)
            except Exception as e:
                messages.error(request, f"Error processing pro-rata expense: {str(e)}")
                return redirect('finance_expense_edit', expense_id=expense_id)

        # Handle non-pro-rata or single property expense
        # IMPORTANT: Clear all monthly amounts first, then set only the active ones
        monthly_data = {
            'prop_id': prop_id,
            'expense_line_types_id': elt_id,
            'expense_types_id': et_id,
            'expense_amount': expense_amount,
            # Clear all monthly amounts first
            'expense_jan': None,
            'expense_feb': None,
            'expense_mar': None,
            'expense_apr': None,
            'expense_may': None,
            'expense_jun': None,
            'expense_jul': None,
            'expense_aug': None,
            'expense_sep': None,
            'expense_oct': None,
            'expense_nov': None,
            'expense_dec': None,
        }
        
        # Set only the active months based on the NEW expense type
        for month in months:
            if getattr(expense_type, f'expense_types_{month}') == "Yes":
                monthly_data[f'expense_{month}'] = expense_amount
        
        # Update the existing expense directly (don't use update_or_create)
        for field, value in monthly_data.items():
            setattr(existing_expense, field, value)
        existing_expense.save()
        
        messages.success(request, "Expense Updated Successfully")
        return redirect('finance_expense')
    
    return redirect('finance_expense_edit', expense_id=expense_id)

@login_required
def finance_expense_types(request):
    exp_types = expense_types.objects.all()
    return render(request, "finance_expense_types.html", {
        "etresults": exp_types,
    })

@login_required
def finance_expense_types_add(request):
    exp_types = expense_types.objects.all().order_by('expense_types_name')
    return render(request, "finance_expense_types_add.html", {"etresults":exp_types})

@login_required
def finance_expense_types_commit(request):
    if request.method == "POST":
        form = ExpenseTypesForm(request.POST or None)
        if form.is_valid():
            form.save()
            messages.success(request, "Expense Types Added Successfully")
    exp_types = expense_types.objects.all()
    return render(request, "finance_expense_types.html", {"etresults":exp_types})

@login_required
def finance_expense_types_edit(request, expense_types_id):
    exp_types = expense_types.objects.filter(pk=expense_types_id)
    return render(request, "finance_expense_types_edit.html", {"etresults":exp_types})

@login_required
def finance_expense_types_edit_commit(request, expense_types_id):
    exp = get_object_or_404(expense_types, pk=expense_types_id)
    all_types = expense_types.objects.all().order_by('expense_types_name')
    if request.method == "POST":
        name = request.POST.get('expense_types_name')
        # Check for duplicates (case-insensitive, excluding current record)
        if expense_types.objects.filter(
            expense_types_name__iexact=name
        ).exclude(
            pk=expense_types_id
        ).exists():
            messages.error(request, "No duplicate Expense Types Allowed")
            return render(request, "finance_expense_types.html", {
                "etresults": all_types,
                "exp": exp,
                "name_error": True
            })
        form = ExpenseTypesForm(request.POST, instance=exp)
        if form.is_valid():
            form.save()
            messages.success(request, "Expense Type Edited Successfully")
            return redirect('finance_expense_types')
    
    # If GET request or form invalid
    return render(request, "finance_expense_types.html", {
        "etresults": all_types,
        "exp": exp
    })

@login_required
def finance_expense_line_types(request):
    exp_line_types = expense_line_types.objects.all().order_by('expense_line_types_name')
    return render(request, "finance_expense_line_types.html", {
        "eltresults": exp_line_types,
    })

@login_required
def finance_expense_line_types_add(request):
    exp_line_types = expense_line_types.objects.all()
    return render(request, "finance_expense_line_types_add.html", {"eltresults":exp_line_types})

@login_required
def finance_expense_line_types_commit(request):
    if request.method == "POST":
        form = ExpenseLineForm(request.POST or None)
        if form.is_valid():
            form.save()
            messages.success(request, "Expense Line Type Added Successfully")
    exp_line_types = expense_line_types.objects.all()
    return render(request, "finance_expense_line_types.html", {"eltresults":exp_line_types})

@login_required
def finance_expense_line_types_edit(request, expense_line_types_id):
    exp_line_types = expense_line_types.objects.filter(pk=expense_line_types_id)
    return render(request, "finance_expense_line_types_edit.html", {"eltresults":exp_line_types})

@login_required
def finance_expense_line_types_edit_commit(request, expense_line_types_id):
    exp = get_object_or_404(expense_line_types, pk=expense_line_types_id)
    all_types = expense_line_types.objects.all().order_by('expense_line_types_name')
    if request.method == "POST":
        name = request.POST.get('expense_line_types_name')
        # Check for duplicates (case-insensitive, excluding current record)
        if expense_line_types.objects.filter(
            expense_line_types_name__iexact=name
        ).exclude(
            pk=expense_line_types_id
        ).exists():
            messages.error(request, "No duplicate Expense Line Types Allowed")
            return render(request, "finance_expense_line_types.html", {
                "eltresults": all_types,
                "exp": exp,
                "name_error": True
            })
        form = ExpenseLineForm(request.POST, instance=exp)
        if form.is_valid():
            form.save()
            messages.success(request, "Expense Line Type Edited Successfully")
            return redirect('finance_expense_line_types')
    
    # If GET request or form invalid
    return render(request, "finance_expense_line_types.html", {
        "eltresults": all_types,
        "exp": exp
    })

@login_required
def check_expenses_for_line_type(request, expense_line_type_id):
    """
    Check if there are expenses linked to this expense line type
    Returns JSON with expense details if any exist
    """
    if not request.user.is_superuser:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    try:
        # Get the expense line type
        expense_line_type = get_object_or_404(expense_line_types, expense_line_types_id=expense_line_type_id)
        
        # Check for linked expenses using the correct foreign key field name
        linked_expenses = expense.objects.filter(expense_line_types=expense_line_type)
        
        if linked_expenses.exists():
            # Prepare expense data for the frontend
            expenses_data = []
            for exp in linked_expenses:
                # Calculate total amount from all months
                total_amount = 0
                monthly_amounts = []
                
                months = ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 
                         'jul', 'aug', 'sep', 'oct', 'nov', 'dec']
                
                for month in months:
                    month_value = getattr(exp, f'expense_{month}', None)
                    if month_value:
                        total_amount += month_value
                        monthly_amounts.append(f'{month.capitalize()}: {month_value}')
                
                # Use base expense_amount if available, otherwise use calculated total
                display_amount = exp.expense_amount if exp.expense_amount else total_amount
                
                expenses_data.append({
                    'id': exp.expense_id,
                    'expense_type': str(exp.expense_types) if exp.expense_types else 'N/A',
                    'property': str(exp.prop) if exp.prop else 'N/A',
                    'base_amount': str(exp.expense_amount) if exp.expense_amount else '0.00',
                    'total_monthly': str(total_amount),
                    'display_amount': str(display_amount),
                    'monthly_breakdown': monthly_amounts
                })
            
            return JsonResponse({
                'has_expenses': True,
                'expense_count': linked_expenses.count(),
                'expenses': expenses_data
            })
        else:
            return JsonResponse({
                'has_expenses': False,
                'expense_count': 0,
                'expenses': []
            })
            
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def delete_expense_line_type(request, expense_line_type_id):
    """
    Delete an expense line type and all its linked expenses
    """
    if not request.user.is_superuser:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        with transaction.atomic():
            # Get the expense line type
            expense_line_type = get_object_or_404(expense_line_types, expense_line_types_id=expense_line_type_id)
            
            # Get linked expenses before deletion
            linked_expenses = expense.objects.filter(expense_line_types=expense_line_type)
            expense_count = linked_expenses.count()
            
            # Delete all linked expenses first
            linked_expenses.delete()
            
            # Delete the expense line type
            expense_line_type_name = expense_line_type.expense_line_types_name
            expense_line_type.delete()
            
            # Create success message
            if expense_count > 0:
                message = f'Expense line type "{expense_line_type_name}" and {expense_count} linked expense(s) have been deleted successfully.'
            else:
                message = f'Expense line type "{expense_line_type_name}" has been deleted successfully.'
            
            messages.success(request, message)
            
            return JsonResponse({
                'success': True,
                'message': message,
                'deleted_expenses': expense_count
            })
            
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@login_required
def finance_valuations(request):
    props_list = props.objects.all().order_by('prop_country', 'prop_name')
    valuations = prop_values.objects.all()
    
    # Create a dictionary for easy lookup
    valuations_dict = {v.prop_id: v for v in valuations}
    
    # Calculate totals
    pur_balance = sum(
        v.prop_values_purchase_price 
        for v in valuations 
        if v.prop_values_purchase_price is not None
    )
    cur_balance = sum(
        v.prop_values_current_value 
        for v in valuations 
        if v.prop_values_current_value is not None
    )
    
    return render(request, "finance_valuations.html", {
        "props": props_list,
        "prop_values": valuations_dict,
        "pur_balance": pur_balance,
        "cur_balance": cur_balance
    })

@login_required
def finance_valuations_add(request):
	results = props.objects.all().order_by('prop_country', 'prop_name')
	vresults = prop_values.objects.all()
	context = {
		'props': results,
		'prop_values': vresults,
	}
	return render(request, "finance_valuations_add.html", context)

@login_required
def finance_valuations_commit(request):
    if request.method == "POST":
        prop_id = request.POST.get('prop_id')  # Get property ID from form
        
        # Check if valuation already exists for this property
        if prop_values.objects.filter(prop_id=prop_id).exists():
            messages.error(request, "A valuation already exists for this property. Please edit the existing valuation.")
            return redirect('finance_valuations')
            
        form = ValuesForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Valuation Added Successfully")
            return redirect('finance_valuations')
        else:
            messages.error(request, "Please correct the errors below")
    
    # Rest of your view remains the same...
    results = props.objects.all().order_by('prop_country','prop_name')
    vresults = prop_values.objects.all().order_by('prop_values_purchase_price')    
    
    pur_balance = sum(x.prop_values_purchase_price for x in vresults if x.prop_values_purchase_price is not None)
    cur_balance = sum(x.prop_values_current_value for x in vresults if x.prop_values_current_value is not None)

    context = {
        'pur_balance': pur_balance,
        'cur_balance': cur_balance,        
        'props': results,
        'prop_values': vresults,
    }
    return render(request, "finance_valuations.html", context)

@login_required
def finance_valuations_edit(request, prop_values_id):
	try:
		vresults = prop_values.objects.get(pk=prop_values_id)
	except prop_values.DoesNotExist:
		print(f"ERROR: No prop_values record found for ID {prop_values_id}")
		raise Http404("Valuation not found")
	results = props.objects.all().order_by('prop_country','prop_name')
	return render(request, "finance_valuations_edit.html", {
		"props": results,
		"vresults": vresults
	})

@login_required
def finance_valuations_edit_commit(request, prop_values_id):
    print("Form data received:", request.POST)
    vresult = prop_values.objects.get(pk=prop_values_id)
    
    if request.method == "POST":
        form = ValuesForm(request.POST, instance=vresult)
        if form.is_valid():
            print("Form is valid, saving...")
            form.save()
            print("Saved values:", vresult.prop_values_purchase_price, vresult.prop_values_current_value)
            messages.success(request, "Valuations Edited Successfully")
            return redirect('finance_valuations')  # Redirect instead of render
        else:
        	print("Form errors:", form.errors)
    
    # If GET or invalid form, show the valuations page
    return redirect('finance_valuations')

### TENANTS ###
@login_required
def tenant_page(request):
    # Get filter values from the new form
    selected_property = request.POST.get('propname', '').strip()
    selected_tenant = request.POST.get('tenantname', '').strip()
    selected_status = request.POST.get('act', '').strip()
    
    # Start with all properties and tenants
    all_properties = props.objects.all().order_by('prop_country', 'prop_name')
    all_tenants = tenant.objects.all().order_by('tenant_name')
    
    # Filter tenants based on the selected criteria
    filtered_tenants = all_tenants
    
    # Apply tenant name filter
    if selected_tenant:
        filtered_tenants = filtered_tenants.filter(tenant_name=selected_tenant)
    
    # Apply status filter
    if selected_status:
        filtered_tenants = filtered_tenants.filter(tenant_current=selected_status)
    
    # Filter properties based on the selected property
    filtered_properties = all_properties
    if selected_property:
        filtered_properties = filtered_properties.filter(prop_name=selected_property)
    
    # Pass filter values back to template for form persistence
    context = {
        'tenant': filtered_tenants,
        'props': filtered_properties,
        'selected_property': selected_property,
        'selected_tenant': selected_tenant,
        'selected_status': selected_status,
    }
    
    return render(request, "tenant.html", context)

@login_required
def tenant_add(request):
	results = props.objects.all().order_by('prop_country','prop_name')
	tresults = tenant.objects.all().order_by('tenant_name')
	return render(request, "tenant_add.html", {"props":results, "tenant":tresults})

@login_required
def tenant_edit(request, tenant_id):
	tresults = tenant.objects.filter(pk=tenant_id)
	results = props.objects.all().order_by('prop_country','prop_name')
	return render (request, "tenant_edit.html", {"props":results, "tenant":tresults})

@login_required
def tenant_commit(request):
    props_list = props.objects.all().order_by('prop_country','prop_name')
    
    if request.method == "POST":
        form = TenantForm(request.POST)
        
        if form.is_valid():
            try:
                new_tenant = form.save()
                messages.success(request, f"Tenant {new_tenant.tenant_name} added successfully")
                return redirect('tenant')
            except ValidationError as e:
                # Clean up the error message
                clean_error = str(e).replace('__all__: ', '')
                messages.error(request, clean_error)
                return render(request, "tenant_add.html", {
                    'form': form,
                    'props': props_list,
                    'form_data': request.POST
                })
            except Exception as e:
                messages.error(request, f"Error saving tenant: {str(e)}")
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    clean_error = str(error).replace('__all__: ', '')
                    messages.error(request, clean_error)
    
    return render(request, "tenant_add.html", {
        'form': TenantForm(request.POST if request.method == "POST" else None),
        'props': props_list,
        'form_data': request.POST if request.method == "POST" else None
    })

@login_required
def tenant_edit_commit(request, tenant_id):
	ten = tenant.objects.get(pk=tenant_id)
	if request.method == "POST":
		form = TenantForm(request.POST or None, instance=ten)
		if form.is_valid():
			form.save()
			messages.success(request, "Tenant Edited Successfully")
	results = props.objects.all().order_by('prop_country','prop_name')
	tresults = tenant.objects.all().order_by('tenant_name')
	return render (request, "tenant.html", {"tenant":tresults, "props":results})

@login_required
def tenant_lease_agreement(request):
    tenants = tenant.objects.all().order_by('prop__prop_country', 'prop__prop_name', 'tenant_name')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        tenant_id = request.POST.get('tenant_id')
        
        if not tenant_id:
            messages.error(request, 'No tenant selected')
            return redirect('tenant_lease_agreement')
        
        try:
            tenant_obj = get_object_or_404(tenant, pk=tenant_id)
            
            if action == 'delete':
                if tenant_obj.tenant_lease_agreement:
                    # Delete the file from storage
                    tenant_obj.tenant_lease_agreement.delete()
                    tenant_obj.tenant_lease_agreement_status = "No Lease Agreement"
                    tenant_obj.save()
                    messages.success(request, f'Lease agreement deleted for {tenant_obj.tenant_name}!')
                else:
                    messages.warning(request, 'No lease agreement found to delete.')
                    

            elif action == 'upload':
                if 'lease_agreement' in request.FILES:
                    uploaded_file = request.FILES['lease_agreement']
                    
                    # Validate file size (10MB limit)
                    if uploaded_file.size > 10 * 1024 * 1024:
                        messages.error(request, 'File size exceeds 10MB limit')
                        return redirect('tenant_lease_agreement')
                    
                    # Validate file type
                    allowed_extensions = ['.pdf', '.jpg', '.jpeg', '.png']
                    file_extension = os.path.splitext(uploaded_file.name)[1].lower()
                    
                    if file_extension not in allowed_extensions:
                        messages.error(request, 'Invalid file type. Please upload PDF or image files only.')
                        return redirect('tenant_lease_agreement')
                    
                    try:
                        # Ensure directory exists
                        upload_path = os.path.join(settings.MEDIA_ROOT, 'tenants', 'lease_agreements')
                        os.makedirs(upload_path, exist_ok=True)
                        
                        # Delete old file if exists
                        if tenant_obj.tenant_lease_agreement:
                            tenant_obj.tenant_lease_agreement.delete(save=False)
                        
                        # Save new file
                        tenant_obj.tenant_lease_agreement = uploaded_file
                        tenant_obj.tenant_lease_agreement_status = "Lease Agreement Uploaded"
                        tenant_obj.save()
                        
                        messages.success(request, f'Lease agreement uploaded successfully for {tenant_obj.tenant_name}!')
                    except Exception as e:
                        messages.error(request, f'Error saving file: {str(e)}')
                else:
                    messages.error(request, 'Please select a file to upload')
                    
        except Exception as e:
            messages.error(request, f'Error processing request: {str(e)}')
    
    context = {
        'tenants': tenants,
    }
    return render(request, 'tenant_lease_agreement.html', context)

### SUPPLIERS ###
@login_required
def suppliers(request):
    sup_output = request.POST.get('supname')
    sup_count = request.POST.get('supcount')
    
    # Start with all suppliers
    sresults = supplier.objects.all().order_by('supplier_country','supplier_contact_person')
    
    # Apply search filter if provided and not "All"
    if sup_output and sup_output != "All":
        sresults = sresults.filter(supplier_contact_person__icontains=sup_output)
    
    # Apply country filter if provided and not "All"  
    if sup_count and sup_count != "All":
        sresults = sresults.filter(supplier_country=sup_count)
    
    # Pass the search values back to template for form preservation
    context = {
        "supplier": sresults,
        "selected_supplier": sup_output if sup_output and sup_output != "All" else "",
        "selected_country": sup_count if sup_count and sup_count != "All" else "All"
    }
    
    return render(request, "suppliers.html", context)

@login_required
def suppliers_add(request):
	sresults = supplier.objects.all().order_by('supplier_country','supplier_contact_person')
	return render(request, "suppliers_add.html", {"supplier":sresults})

@login_required
def suppliers_edit(request, supplier_id):
	sresults = supplier.objects.filter(pk=supplier_id)
	return render (request, "suppliers_edit.html", {"supplier":sresults})

@login_required
def suppliers_commit(request):
	if request.method == "POST":
		form = SupplierForm(request.POST or None)
		if form.is_valid():
			form.save()
			messages.success(request, "Supplier Added Successfully")
		else:
			print(form.errors.as_data())
	sresults = supplier.objects.all().order_by('supplier_country','supplier_contact_person')
	return render (request, "suppliers.html", {"supplier":sresults})

@login_required
def suppliers_edit_commit(request, supplier_id):
	sup = supplier.objects.get(pk=supplier_id)
	if request.method == "POST":
		form = SupplierForm(request.POST or None, instance=sup)
		if form.is_valid():
			form.save()
			messages.success(request, "Supplier Edited Successfully")
	sresults = supplier.objects.all().order_by('supplier_country','supplier_contact_person')
	return render (request, "suppliers.html", {"supplier":sresults})


### INVOICES ###
@login_required
def invoices_page(request):
    # Get filter values from POST request
    prop_output = request.POST.get('propname', '')
    tenant_output = request.POST.get('tenantname', '')
    
    # Always get all props for the dropdown
    all_props = props.objects.all().order_by('prop_country', 'prop_name')
    
    # Always get all tenants for the dropdown  
    all_tenants = tenant.objects.all().order_by('tenant_name')
    
    # Get unpaid invoices
    iresults = invoices.objects.filter(invoice_paid="No").order_by('invoice_date')
    
    # Filter props based on selection
    if prop_output and prop_output != "All":
        filtered_props = props.objects.filter(prop_name=prop_output)
    else:
        filtered_props = all_props
    
    # Filter tenants based on selection
    if tenant_output and tenant_output != "All":
        filtered_tenants = tenant.objects.filter(tenant_name=tenant_output)
    else:
        filtered_tenants = all_tenants
    
    context = {
        "invoices": iresults,
        "tenant": filtered_tenants,  # Filtered tenants for display
        "props": filtered_props,     # Filtered props for display
        "all_props": all_props,      # All props for dropdown
        "all_tenants": all_tenants,  # All tenants for dropdown
        "selected_property": prop_output if prop_output != "All" else "",
        "selected_tenant": tenant_output if tenant_output != "All" else "",
    }
    
    return render(request, "invoices.html", context)

@login_required
def invoices_commit(request, invoice_id):
    inv_tbp = invoices.objects.filter(pk=invoice_id).update(invoice_paid="Yes")
    iresults = invoices.objects.get(pk=invoice_id)
    tresults = tenant.objects.get(pk=iresults.tenant_id)
    # Attempt to send the notification email
    if send_invoices_paid_email(tresults, iresults.invoice_date):
        messages.info(request, "Invoice marked as Paid notification email sent.")
    else:
        messages.warning(request, "Invoice marked as Paid, but email could not be sent.")
    return redirect('invoices')

def send_invoices_paid_email(tenant, invoice_date):
    """
    Send email notification of an expense payment for a specific expense
    """
    smtp_object = None
    try:
        # Create message
        msg = MIMEMultipart()
        msg['From'] = "demetrimanias@gmail.com"
        msg['To'] = "demetrimanias@gmail.com"
        msg['Subject'] = "Rent Payment"
        
        # Email body with proper formatting
        body = f"""Dear User,

The rent has been received from the following tenant:
 • Tenant: {tenant}
 • Invoice Date: {invoice_date}

Thanks,

Alivente Property Management System"""
        
        msg.attach(MIMEText(body, 'plain'))
        
        # Get email credentials from environment variables
        email_password = os.environ.get('EMAIL_PASSWORD')
        
        if not email_password:
            logger.error('❌ EMAIL_PASSWORD environment variable not set')
            return False
        
        # SMTP setup with more detailed error handling
        smtp_object = smtplib.SMTP('smtp.gmail.com', 587)
        smtp_object.ehlo()
        smtp_object.starttls()
        
        email = "demetrimanias@gmail.com"
        
        smtp_object.login(email, email_password)
        
        # Send email
        text = msg.as_string()
        smtp_object.sendmail(email, "demetrimanias@gmail.com", text)
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        logger.error(f"SMTP Authentication Error: {e}")
        return False
    except smtplib.SMTPException as e:
        logger.error(f"SMTP Error: {e}")
        return False
    except Exception as e:
        logger.error(f"Error sending email: {e}")
        return False
    finally:
        if smtp_object:
            try:
                smtp_object.quit()
            except:
                pass

### PROPERTIES ###
@login_required
def properties_page(request):
    # Get filter values from the new form
    search_query = request.POST.get('search', '').strip()
    selected_country = request.POST.get('country', '')
    selected_status = request.POST.get('status', '')
    
    # Start with all properties
    results = props.objects.all()
    
    # Apply cumulative filters (all work together)
    if search_query:
        results = results.filter(prop_name__icontains=search_query)
    
    if selected_country:
        results = results.filter(prop_country=selected_country)
    
    if selected_status:
        results = results.filter(prop_status=selected_status)
    
    # Always order the results
    results = results.order_by('prop_country', 'prop_name')
    
    # Pass filter values back to template for form persistence
    context = {
        'props': results,
        'search_query': search_query,
        'selected_country': selected_country,
        'selected_status': selected_status,
    }

    return render(request, "properties.html", context)

@login_required
def properties_map_view(request):
    """Display all properties on an interactive map"""
    
    # Get all properties from the database
    properties = props.objects.all()
    
    # Convert properties to JSON format for JavaScript
    properties_data = []
    for prop in properties:
        # Handle Decimal fields properly
        latitude = None
        longitude = None
        
        if prop.prop_latitude is not None:
            latitude = float(prop.prop_latitude)
        if prop.prop_longitude is not None:
            longitude = float(prop.prop_longitude)
        
        property_dict = {
            'id': prop.prop_id,
            'name': prop.prop_name,
            'address1': prop.prop_address1,
            'address2': prop.prop_address2,
            'suburb': prop.prop_suburb,
            'city': prop.prop_city,
            'province': prop.prop_province,
            'country': prop.prop_country,
            'pcode': prop.prop_pcode,
            'latitude': latitude,
            'longitude': longitude,
            'floor_area': prop.prop_floor_area,
            'year_built': prop.prop_year_built,
            'status': prop.prop_status,
            'available_for_rent': prop.prop_available_for_rent,
        }
        properties_data.append(property_dict)
    
    context = {
        'properties_json': json.dumps(properties_data),
        'properties_count': len(properties_data)
    }
    
    return render(request, 'map_view.html', context)

@login_required
def properties_title_deed(request):
    properties = props.objects.all().order_by('prop_country','prop_name')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        prop_id = request.POST.get('property_id')  # Changed from 'prop_id' to match form
        
        if not prop_id:
            messages.error(request, 'No property selected')
            return redirect('properties_title_deed')
        
        try:
            property_obj = get_object_or_404(props, pk=prop_id)
            
            if action == 'delete':
                if property_obj.prop_title_deed:
                    # Delete the file from storage
                    property_obj.prop_title_deed.delete()
                    property_obj.prop_title_deed_status = "No Title Deed"
                    property_obj.save()
                    messages.success(request, f'Title deed deleted for {property_obj.prop_name}!')
                else:
                    messages.warning(request, 'No title deed found to delete.')
                    

            elif action == 'upload':
                if 'title_deed' in request.FILES:
                    uploaded_file = request.FILES['title_deed']
                    
                    # Validate file size (10MB limit)
                    if uploaded_file.size > 10 * 1024 * 1024:
                        messages.error(request, 'File size exceeds 10MB limit')
                        return redirect('properties_title_deed')
                    
                    # Validate file type
                    allowed_extensions = ['.pdf', '.jpg', '.jpeg', '.png']
                    file_extension = os.path.splitext(uploaded_file.name)[1].lower()
                    
                    if file_extension not in allowed_extensions:
                        messages.error(request, 'Invalid file type. Please upload PDF or image files only.')
                        return redirect('properties_title_deed')
                    
                    try:
                        # Ensure directory exists
                        upload_path = os.path.join(settings.MEDIA_ROOT, 'properties', 'title_deeds')
                        os.makedirs(upload_path, exist_ok=True)
                        
                        # Delete old file if exists
                        if property_obj.prop_title_deed:
                            property_obj.prop_title_deed.delete(save=False)
                        
                        # Save new file
                        property_obj.prop_title_deed = uploaded_file
                        property_obj.prop_title_deed_status = "Title Deed Uploaded"
                        property_obj.save()
                        
                        messages.success(request, f'Title deed uploaded successfully for {property_obj.prop_name}!')
                    except Exception as e:
                        messages.error(request, f'Error saving file: {str(e)}')
                else:
                    messages.error(request, 'Please select a file to upload')
                    
        except Exception as e:
            messages.error(request, f'Error processing request: {str(e)}')
    
    context = {
        'properties': properties,
    }
    return render(request, 'properties_title_deed.html', context)

@login_required
def properties_add(request):
	results = props.objects.all().order_by('prop_country','prop_name')
	existing_names = list(props.objects.values_list('prop_name', flat=True))
	return render(request, "properties_add.html", {"props":results, "existing_names": existing_names})

@login_required
def properties_commit(request):
	if request.method == "POST":
		form = PropForm(request.POST or None)
		if form.is_valid():
			form.save()
	results = props.objects.all().order_by('prop_country','prop_name')
	messages.success(request, "Property Added Successfully")
	return render (request, "properties.html", {"props":results})

@login_required
def properties_edit(request, prop_id):
    # Get the current property being edited
    current_property = get_object_or_404(props, pk=prop_id)
    
    # Get all other property names (excluding the current one)
    existing_names = props.objects.exclude(prop_id=prop_id).values_list('prop_name', flat=True)
    
    return render(request, "properties_edit.html", {
        "props": [current_property],  # Maintain your existing structure
        "existing_names": list(existing_names)  # Add this for client-side validation
    })

@login_required
def properties_edit_commit(request, prop_id):
    prop = get_object_or_404(props, pk=prop_id)
    existing_names = props.objects.exclude(prop_id=prop_id).values_list('prop_name', flat=True)
    
    if request.method == "POST":
        form = PropForm(request.POST, instance=prop)
        
        if form.is_valid():
            new_name = form.cleaned_data.get('prop_name')
            current_name = prop.prop_name
            
            if new_name.lower() != current_name.lower():
                if props.objects.exclude(prop_id=prop_id).filter(prop_name__iexact=new_name).exists():
                    messages.error(request, "A property with this name already exists.")
                    return render(request, "properties_edit.html", {
                        'props': [prop],
                        'existing_names': list(existing_names)
                    })
            
            form.save()
            messages.success(request, "Property Edited Successfully")
            results = props.objects.all().order_by('prop_country','prop_name')
            return redirect('properties')  # Better to redirect after POST
        
        # Form is invalid
        messages.error(request, "Please correct the errors below.")
        return render(request, "properties_edit.html", {
            'props': [prop],
            'existing_names': list(existing_names)
        })
    
    # If not POST, redirect to properties page
    return redirect('properties')


### ACTUAL EXPENSES ###
@login_required
def act_expense_manage_document(request):
    """
    Handle document upload, replacement, and deletion within the main expense page
    """
    if request.method == 'POST':
        action = request.POST.get('action')
        expense_id = request.POST.get('expense_id')
        
        if not expense_id:
            messages.error(request, 'No expense selected')
            return redirect('act_expense_all')
        
        try:
            expense = get_object_or_404(act_expense, pk=expense_id)
            
            if action == 'delete_document':
                # Handle document deletion only (not the entire expense)
                if expense.act_expense_document:
                    # Delete the physical file
                    if expense.act_expense_document.storage.exists(expense.act_expense_document.name):
                        expense.act_expense_document.delete(save=False)
                    
                    # Clear the database field
                    expense.act_expense_document = None
                    expense.save()
                    
                    messages.success(request, f'Invoice document deleted successfully for expense on {expense.act_expense_date}!')
                else:
                    messages.warning(request, 'No document found to delete.')
                    
            elif action == 'upload':
                # Handle file upload/replacement
                if 'act_expense_document' in request.FILES:
                    uploaded_file = request.FILES['act_expense_document']
                    
                    # Validate file size (5MB limit)
                    if uploaded_file.size > 5 * 1024 * 1024:
                        messages.error(request, 'File size exceeds 5MB limit')
                        return redirect('act_expense_all')
                    
                    # Validate file type
                    allowed_extensions = ['.pdf', '.jpg', '.jpeg', '.png', '.xlsx', '.xls', '.doc', '.docx']
                    file_extension = os.path.splitext(uploaded_file.name)[1].lower()
                    
                    if file_extension not in allowed_extensions:
                        messages.error(request, 'Invalid file type. Please upload PDF, JPG, PNG, Excel, or Word files only.')
                        return redirect('act_expense_all')
                    
                    # Delete existing file if present
                    if expense.act_expense_document:
                        if expense.act_expense_document.storage.exists(expense.act_expense_document.name):
                            expense.act_expense_document.delete(save=False)
                    
                    expense.act_expense_document = uploaded_file
                    expense.save()
                    messages.success(request, f'Invoice document uploaded successfully for expense on {expense.act_expense_date}!')
                else:
                    messages.error(request, 'Please select a file to upload')
                    
        except Exception as e:
            messages.error(request, f'Error processing request: {str(e)}')
    
    return redirect('act_expense_all')

from datetime import datetime

@login_required
def act_expense_all(request):
    # Get filter parameters from request
    search_query = request.GET.get('search', '').strip()
    property_filter = request.GET.get('property', '').strip()
    status_filter = request.GET.get('status', '').strip()
    from_date = request.GET.get('from_date', '').strip()
    to_date = request.GET.get('to_date', '').strip()

    # Base queryset - all expenses, ordered by date (most recent first)
    expenses = act_expense.objects.select_related('prop').order_by('-act_expense_date')
    
    # Apply filters one by one
    
    # 1. Search filter - search in description
    if search_query:
        expenses = expenses.filter(
            act_expense_description__icontains=search_query
        )
    
    # 2. Property filter
    if property_filter:
        try:
            property_id = int(property_filter)
            expenses = expenses.filter(prop_id=property_id)
        except (ValueError, TypeError):
            pass
    
    # 3. Status filter
    if status_filter:
        if status_filter == 'require_approval':
            expenses = expenses.filter(act_expense_approved='No', act_expense_paid='No')
        elif status_filter == 'approved_not_paid':
            expenses = expenses.filter(act_expense_approved='Yes', act_expense_paid='No')
        elif status_filter == 'approved_and_paid':
            expenses = expenses.filter(act_expense_approved='Yes', act_expense_paid='Yes')
    
    # 4. Date range filtering
    if from_date:
        try:
            # Ensure proper date format
            parsed_from_date = datetime.strptime(from_date, '%Y-%m-%d').date()
            expenses = expenses.filter(act_expense_date__gte=parsed_from_date)
        except ValueError:
            pass
    
    if to_date:
        try:
            # Ensure proper date format
            parsed_to_date = datetime.strptime(to_date, '%Y-%m-%d').date()
            expenses = expenses.filter(act_expense_date__lte=parsed_to_date)
        except ValueError:
            pass
    
    # Get properties for filter dropdown
    properties = props.objects.filter(prop_status="Active").order_by('prop_country', 'prop_name')
    
    # Determine navigation context
    came_from = request.GET.get('from', None)
    from_finance_pl_act = request.GET.get('from_finance_pl_act', False)
    
    # Convert string 'True'/'False' to boolean if needed
    if isinstance(from_finance_pl_act, str):
        from_finance_pl_act = from_finance_pl_act.lower() == 'true'

    return render(request, 'act_expense.html', {
        'expenses': expenses,
        'props': properties,
        'current_year': datetime.now().year,
        'from_finance_pl_act': from_finance_pl_act,
        'came_from': came_from,
        # Pass filter values back to template to maintain state
        'search_query': search_query,
        'selected_property': property_filter,
        'selected_status': status_filter,
        'selected_from_date': from_date,
        'selected_to_date': to_date,
    })

@login_required
def act_expense_upload_inv(request):
    # Get all expenses to display in the table
    expenses = act_expense.objects.all().order_by('-act_expense_date')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        expense_id = request.POST.get('expense_id')
        
        if not expense_id:
            messages.error(request, 'No expense selected')
            return redirect('act_expense_upload_inv')
        
        try:
            expense = get_object_or_404(act_expense, pk=expense_id)
            
            if action == 'delete':
                # Handle file deletion
                if expense.act_expense_document:
                    # Delete the physical file
                    if expense.act_expense_document.storage.exists(expense.act_expense_document.name):
                        expense.act_expense_document.delete(save=False)
                    
                    # Clear the database field
                    expense.act_expense_document = None
                    expense.save()
                    
                    messages.success(request, f'Document deleted successfully for expense on {expense.act_expense_date}!')
                else:
                    messages.warning(request, 'No document found to delete.')
                    
            elif action == 'upload':
                # Handle file upload (your existing code)
                if 'act_expense_document' in request.FILES:
                    uploaded_file = request.FILES['act_expense_document']
                    
                    # Validate file size (5MB limit)
                    if uploaded_file.size > 5 * 1024 * 1024:
                        messages.error(request, 'File size exceeds 5MB limit')
                        return redirect('act_expense_upload_inv')
                    
                    # Validate file type
                    allowed_extensions = ['.pdf', '.jpg', '.jpeg', '.png', '.xlsx', '.xls', '.doc', '.docx']
                    file_extension = os.path.splitext(uploaded_file.name)[1].lower()
                    
                    if file_extension not in allowed_extensions:
                        messages.error(request, 'Invalid file type. Please upload PDF, JPG, PNG, Excel, or Word files only.')
                        return redirect('act_expense_upload_inv')
                    
                    # Delete existing file if present
                    if expense.act_expense_document:
                        if expense.act_expense_document.storage.exists(expense.act_expense_document.name):
                            expense.act_expense_document.delete(save=False)
                    
                    expense.act_expense_document = uploaded_file
                    expense.save()
                    messages.success(request, f'Document uploaded successfully for expense on {expense.act_expense_date}!')
                else:
                    messages.error(request, 'Please select a file to upload')
                    
        except Exception as e:
            messages.error(request, f'Error processing request: {str(e)}')
    
    context = {
        'expenses': expenses,
    }
    return render(request, 'act_expense_upload_inv.html', context)

@login_required
def act_expense_view(request):
    # Get year/month from request or use current year as default
    selected_year = request.GET.get('year', datetime.now().year)
    selected_month = request.GET.get('month')
    from_finance_pl_act = request.GET.get('from_finance_pl_act', False)
    property_id = request.GET.get('property_id')
    
#    template_name = 'act_expense.html'  # default full-page view
#    if request.GET.get('from_finance_pl_act') == 'true':
#        template_name = 'act_expense_modal_table.html'

    # Base queryset - only approved and paid expenses, ordered by date
    expenses = act_expense.objects.select_related('prop').filter(
        act_expense_approved="Yes",
        act_expense_paid="Yes"
    ).order_by('-act_expense_date')
    
    # Filter by property if specified
    if property_id:
        try:
            expenses = expenses.filter(prop_id=int(property_id))
        except (ValueError, TypeError):
            pass  # Skip if property_id is invalid
    
    # Handle YEAR/MONTH filtering (convert to int safely)
    try:
        year = int(request.GET.get('year', 0)) if request.GET.get('year') else None
        month = int(request.GET.get('month', 0)) if request.GET.get('month') else None
    except (ValueError, TypeError):
        year, month = None, None  # Fallback if invalid input
    
    if year:
        expenses = expenses.filter(act_expense_date__year=year)
        if month:
            expenses = expenses.filter(act_expense_date__month=month)
    
    # Handle DATE RANGE filtering
    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')
    
    if from_date and to_date:
        expenses = expenses.filter(
            act_expense_date__gte=from_date,
            act_expense_date__lte=to_date
        )
    
    # Get available years for filter dropdown
    available_years = act_expense.objects.filter(
        act_expense_approved="Yes",
        act_expense_paid="Yes"
    ).dates('act_expense_date', 'year').order_by('-act_expense_date')
    
    return render(request, 'act_expense.html', {
        'expenses': expenses,
        'selected_year': year if year else int(selected_year),
        'selected_month': month,
        'current_year': datetime.now().year,
        'available_years': [y.year for y in available_years],
        'from_finance_pl_act': from_finance_pl_act,
        'selected_property_id': property_id
    })

@login_required
def act_expense_edit(request, expense_id):
    # Get the current expense being edited
    current_expense = get_object_or_404(act_expense, pk=expense_id)
    
    # Get property details from props table
    results = props.objects.filter(prop_status="Active").order_by('prop_country','prop_name')

    return render(request, "act_expense_edit.html", {
        "props": results,
        "current_expense": current_expense,
    })

@login_required
def act_expense_edit_commit(request, expense_id):
    if request.method == 'POST':
        try:
            expense = act_expense.objects.get(act_expense_id=expense_id)
            
            # Update expense fields
            expense.act_expense_date = request.POST.get('act_expense_date')
            expense.prop_id = request.POST.get('prop')
            expense.act_expense_description = request.POST.get('act_expense_description')
            expense.act_expense_amount = request.POST.get('act_expense_amount')
            
            if request.user.is_superuser:
                expense.act_expense_approved = request.POST.get('act_expense_approved')
                
                # Handle the paid field - check for hidden field if main field is missing
                paid_value = request.POST.get('act_expense_paid')
                if not paid_value:  # If main field is empty (disabled)
                    paid_value = request.POST.get('act_expense_paid_hidden')
                
                expense.act_expense_paid = paid_value
            
            expense.save()
            
            messages.success(request, 'Expense updated successfully!')
            
        except act_expense.DoesNotExist:
            messages.error(request, 'Expense not found.')
        except Exception as e:
            messages.error(request, f'Error updating expense: {str(e)}')
    
    return redirect('act_expense_all')

@login_required
def get_expense_invoice(request, expense_id):
    try:
        # Adjust this query based on your Expense model
        # expense_id might be the date or actual expense ID
        expense = YourExpenseModel.objects.filter(
            # Add your filter logic here - could be by date, ID, etc.
            date=expense_id  # or id=expense_id
        ).first()
        
        if expense and expense.invoice_file:  # Adjust field name
            response = HttpResponse(
                expense.invoice_file.read(), 
                content_type='application/pdf'  # or detect content type
            )
            response['Content-Disposition'] = f'inline; filename="invoice_{expense_id}.pdf"'
            return response
        else:
            raise Http404("Invoice not found")
            
    except Exception as e:
        raise Http404("Invoice not found")

@login_required
def mark_approved(request, expense_id):
    expense = get_object_or_404(act_expense, pk=expense_id)
    if expense.act_expense_approved != 'Yes':  # Only update if not already approved
        expense.act_expense_approved = 'Yes'
        expense.save()
        # Attempt to send the notification email
        if send_expense_approved_email(expense.act_expense_description, expense.act_expense_amount):
            messages.info(request, "Expense approved and notification email sent.")
        else:
            messages.warning(request, "Expense approved, but email could not be sent.")
    return redirect('act_expense_all')

@login_required
def mark_paid(request, expense_id):
    expense = get_object_or_404(act_expense, pk=expense_id)
    if expense.act_expense_paid != 'Yes':  # Only update if not already paid
        expense.act_expense_paid = 'Yes'
        expense.save()
        # Attempt to send the notification email
        if send_expense_paid_email(expense.act_expense_description, expense.act_expense_amount):
            messages.info(request, "Expense marked as paid and notification email sent.")
        else:
            messages.warning(request, "Expense marked as paid, but email could not be sent.")
    return redirect('act_expense_all')

@login_required
def mark_deleted(request, expense_id):
    try:
        expense = get_object_or_404(act_expense, pk=expense_id)
        expense.delete()  # Permanently deletes the record
        messages.success(request, "Expense deleted successfully")
    except Exception as e:
        messages.error(request, f"Error deleting expense: {str(e)}")
    return redirect('act_expense_all')

@login_required
def act_expense_add(request):
    results = props.objects.filter(prop_status="Active").order_by('prop_country','prop_name')
    return render(request, "act_expense_add.html", {'props': results})

def send_expense_approved_email(description, amount):
    """
    Send email notification of an expense approval for a specific expense
    """
    smtp_object = None
    try:
        # Create message
        msg = MIMEMultipart()
        msg['From'] = "demetrimanias@gmail.com"
        msg['To'] = "demetrimanias@gmail.com"
        msg['Subject'] = "Expense Approval"
        
        # Email body with proper formatting
        body = f"""Dear User,

An expense has been approved.  The details are as follows:
 • Description: {description}
 • Amount: € {amount}

Thanks,

Alivente Property Management System"""
        
        msg.attach(MIMEText(body, 'plain'))
        
        # Get email credentials from environment variables
        email_password = os.environ.get('EMAIL_PASSWORD')
        
        if not email_password:
            logger.error('❌ EMAIL_PASSWORD environment variable not set')
            return False
        
        # SMTP setup with more detailed error handling
        smtp_object = smtplib.SMTP('smtp.gmail.com', 587)
        smtp_object.ehlo()
        smtp_object.starttls()
        
        email = "demetrimanias@gmail.com"
        
        smtp_object.login(email, email_password)
        
        # Send email
        text = msg.as_string()
        smtp_object.sendmail(email, "demetrimanias@gmail.com", text)
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        logger.error(f"SMTP Authentication Error: {e}")
        return False
    except smtplib.SMTPException as e:
        logger.error(f"SMTP Error: {e}")
        return False
    except Exception as e:
        logger.error(f"Error sending email: {e}")
        return False
    finally:
        if smtp_object:
            try:
                smtp_object.quit()
            except:
                pass

def send_expense_paid_email(description, amount):
    """
    Send email notification of an expense payment for a specific expense
    """
    smtp_object = None
    try:
        # Create message
        msg = MIMEMultipart()
        msg['From'] = "demetrimanias@gmail.com"
        msg['To'] = "demetrimanias@gmail.com"
        msg['Subject'] = "Expense Payment"
        
        # Email body with proper formatting
        body = f"""Dear User,

An expense has been paid.  The details are as follows:
 • Description: {description}
 • Amount: € {amount}

Thanks,

Alivente Property Management System"""
        
        msg.attach(MIMEText(body, 'plain'))
        
        # Get email credentials from environment variables
        email_password = os.environ.get('EMAIL_PASSWORD')
        
        if not email_password:
            logger.error('❌ EMAIL_PASSWORD environment variable not set')
            return False
        
        # SMTP setup with more detailed error handling
        smtp_object = smtplib.SMTP('smtp.gmail.com', 587)
        smtp_object.ehlo()
        smtp_object.starttls()
        
        email = "demetrimanias@gmail.com"
        
        smtp_object.login(email, email_password)
        
        # Send email
        text = msg.as_string()
        smtp_object.sendmail(email, "demetrimanias@gmail.com", text)
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        logger.error(f"SMTP Authentication Error: {e}")
        return False
    except smtplib.SMTPException as e:
        logger.error(f"SMTP Error: {e}")
        return False
    except Exception as e:
        logger.error(f"Error sending email: {e}")
        return False
    finally:
        if smtp_object:
            try:
                smtp_object.quit()
            except:
                pass

def send_expense_approval_email_with_link(description, amount):
    """
    Send email notification for expense approval with link to specific expense
    """
    smtp_object = None
    try:
        # Create message
        msg = MIMEMultipart()
        msg['From'] = "demetrimanias@gmail.com"
        msg['To'] = "demetrimanias@gmail.com"
        msg['Subject'] = "Actual Expense Approval"
        
        # Email body with proper formatting
        body = f"""Dear User,

A new Actual Expense has been created that requires your approval.  The details are as follows:
 • Description: {description}
 • Amount: € {amount}

Thanks,

Alivente Property Management System"""
        
        msg.attach(MIMEText(body, 'plain'))
        
        # Get email credentials from environment variables
        email_password = os.environ.get('EMAIL_PASSWORD')
        
        if not email_password:
            logger.error('❌ EMAIL_PASSWORD environment variable not set')
            return False
        
        # SMTP setup with more detailed error handling
        smtp_object = smtplib.SMTP('smtp.gmail.com', 587)
        smtp_object.ehlo()
        smtp_object.starttls()
        
        email = "demetrimanias@gmail.com"
        
        smtp_object.login(email, email_password)
        
        # Send email
        text = msg.as_string()
        smtp_object.sendmail(email, "demetrimanias@gmail.com", text)
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        logger.error(f"SMTP Authentication Error: {e}")
        return False
    except smtplib.SMTPException as e:
        logger.error(f"SMTP Error: {e}")
        return False
    except Exception as e:
        logger.error(f"Error sending email: {e}")
        return False
    finally:
        if smtp_object:
            try:
                smtp_object.quit()
            except:
                pass

@login_required
def act_expense_commit(request):
    if request.method == 'POST':
        try:
            # Get data from the form
            expense_date = request.POST.get('act_expense_date')
            expense_prop = request.POST.get('prop')
            expense_description = request.POST.get('act_expense_description')
            expense_amount = request.POST.get('act_expense_amount')
            expense_approved = request.POST.get('act_expense_approved', 'No')
            expense_paid = request.POST.get('act_expense_paid', 'No')
            
            # Validate required fields
            if not expense_date or not expense_description or not expense_amount or not expense_prop:
                messages.error(request, 'All fields are required.')
                return redirect('act_expense_add')
            
            # Create and save the expense record
            expense = act_expense(
                act_expense_date=expense_date,
                act_expense_description=expense_description,
                act_expense_amount=float(expense_amount),
                act_expense_approved=expense_approved,
                act_expense_paid=expense_paid,
                prop_id=expense_prop
            )
            expense.save()
            
            # Check if user is not a superuser and send email
            if not request.user.is_superuser:
                email_sent = send_expense_approval_email_with_link(expense_description, expense_amount)
                if email_sent:
                    messages.success(request, 'Expense added successfully and approval email sent!')
                else:
                    messages.warning(request, 'Expense added successfully but failed to send approval email.')
            else:
                messages.success(request, 'Expense added successfully!')
            
            return redirect('act_expense_all')
            
        except ValueError as e:
            messages.error(request, 'Please enter a valid amount.')
            return redirect('act_expense_add')
        except Exception as e:
            messages.error(request, f'An error occurred: {str(e)}')
            return redirect('act_expense_add')
    
    return redirect('act_expense_add')

### PETTY CASH ###
@login_required
def petty_cash(request):
	presults = petty.objects.all().order_by('petty_cash_date')
	pvalues = petty.objects.values()
	balance = 0
	for x in pvalues:
		if x['petty_cash_dr_cr'] == "DR":
			balance = balance + x['petty_cash_amount']
		elif x['petty_cash_dr_cr'] == "CR":
			balance = balance - x['petty_cash_amount']
	return render (request, "petty_cash.html", {"petty":presults, "balance":balance})

@login_required
def petty_cash_commit(request):
	if request.method == "POST":
		form = PettyForm(request.POST or None)
		print(form)
		if form.is_valid():
			form.save()
			messages.success(request, "Transaction Added Successfully")
	presults = petty.objects.all().order_by('petty_cash_date')
	pvalues = petty.objects.values()
	balance = 0
	for x in pvalues:
		if x['petty_cash_dr_cr'] == "DR":
			balance = balance + x['petty_cash_amount']
		elif x['petty_cash_dr_cr'] == "CR":
			balance = balance - x['petty_cash_amount']
	return render (request, "petty_cash.html", {"petty":presults, "balance":balance})

@login_required
def petty_cash_add(request):
	presults = petty.objects.all().order_by('petty_cash_date')
	return render(request, "petty_cash_add.html", {"petty":presults})


### ISSUES - FRIDAY STATUS REPORT ###
@login_required
def fsr(request):
    # Get filter parameters
    prop_output = request.POST.get('propname', '').strip()
    country_output = request.POST.get('propcountry', '').strip()
    status_output = request.POST.get('issuestatus', '').strip()
    search_query = request.POST.get('search', '').strip()
    
    # Start with all objects
    results = props.objects.all().order_by('prop_country', 'prop_name')
    isresults = issues.objects.all().order_by('issues_date_logged', 'issues_status')
    idresults = issues_details.objects.all().order_by('issues_details_date', 'issues_details_id')
    
    # Apply filters to properties based on country
    if country_output and country_output != 'All':
        results = results.filter(prop_country=country_output)
    
    # Apply filters to properties based on property name
    if prop_output and prop_output != 'All':
        results = results.filter(prop_name=prop_output)
    
    # Apply filters to issues based on status
    if status_output and status_output != 'All':
        isresults = isresults.filter(issues_status=status_output)
    
    # Apply search filter to issues (search in heading and description)
    if search_query:
        isresults = isresults.filter(
            Q(issues_heading__icontains=search_query) | 
            Q(issues_description__icontains=search_query)
        )
    
    # Get the property IDs from filtered results to ensure issues match filtered properties
    if country_output and country_output != 'All':
        property_ids = results.values_list('prop_id', flat=True)
        isresults = isresults.filter(prop_id__in=property_ids)
    
    if prop_output and prop_output != 'All':
        property_ids = results.values_list('prop_id', flat=True)
        isresults = isresults.filter(prop_id__in=property_ids)
    
    # Pass search query to template for displaying in search input
    context = {
        "props": results, 
        "issues": isresults, 
        "issues_details": idresults,
        "search_query": search_query,
        "selected_country": country_output,
        "selected_property": prop_output,
        "selected_status": status_output,
    }
    
    return render(request, "fsr.html", context)

@login_required
def fsr_add(request):
	results = props.objects.all().order_by('prop_country','prop_name')
	isresults = issues.objects.all().order_by('issues_date_logged','issues_status')
	idresults = issues_details.objects.all().order_by('issues_details_date','issues_details_id')
	log_date = date.today()
	return render(request, "fsr_add.html", {"props":results, "issues":isresults, "issues_details":idresults, "log_date":log_date})

@login_required
def fsr_commit(request):
    if request.method == "POST":
        form = IssuesForm(request.POST or None)
        if form.is_valid():
            form.save()
            messages.success(request, "Issue Added Successfully")
    temp_results = issues.objects.all().order_by('-issues_id')
    is_id = temp_results[0].issues_id
    return redirect(reverse("fsr_details", args=[is_id]) + "?from=fsr_add&origin=fsr")

@login_required
def fsr_details(request, issues_id):
    isresults = issues.objects.filter(pk=issues_id)
    results = props.objects.all().order_by('prop_country','prop_name')
    idresults = issues_details.objects.all().order_by('issues_details_date','issues_details_id').reverse()
    
    # Get the HTTP_REFERER if it exists
    referrer = request.META.get('HTTP_REFERER', '')
    
    # Determine the clean redirect URL
    if 'fsr_details' in referrer:
        # If coming from another details page, go back to main FSR
        redirect_url = reverse('fsr')
    elif 'status_report' in referrer:
        # If coming from status report, go back there
        redirect_url = reverse('friday_status_report')
    else:
        # Default to the main FSR page
        redirect_url = reverse('fsr')
    
    context = {
        "props": results,
        "issues": isresults,
        "issues_details": idresults,
        "redirect_url": redirect_url,
    }
    
    return render(request, "fsr_details.html", context)

@login_required
def fsr_commit_status_change(request):
    if request.method == "POST":
        # Get form data
        issues_id = request.POST.get('issues_id')
        new_status = request.POST.get('issues_status')
        next_url = request.POST.get('next', '')
        
        # Get return parameters from hidden fields
        from_param = request.POST.get('from', 'fsr')
        property_id = request.POST.get('property_id')
        box_type = request.POST.get('box_type')
        
        # Update the issue
        issue = issues.objects.get(pk=issues_id)
        issue.issues_status = new_status
        if new_status == "Resolved":
            issue.issues_resolution_date = date.today()
        issue.save()
        
        # Handle property_detail navigation
        if from_param == 'property_detail' and property_id and box_type:
            # Redirect back to the same fsr_details page with property_detail parameters
            redirect_url = reverse('fsr_details', args=[issues_id])
            redirect_url += f"?from=property_detail&property_id={property_id}&box_type={box_type}"
            return redirect(redirect_url)
        
        # Handle other cases
        elif from_param == 'fsr':
            return redirect(reverse('fsr') + "?refresh=true")
        elif from_param == 'status_report':
            return redirect(reverse('friday_status_report') + "?refresh=true")
        else:
            # Fallback - try to use the next_url if available
            if next_url:
                return redirect(next_url)
            else:
                return redirect(reverse('fsr') + "?refresh=true")

@login_required
def fsr_comment_add(request, issues_id):
    if request.method == 'POST':
        # Get comment text from form
        comment_text = request.POST.get('issues_details_comment', '').strip()
        
        # Validate comment exists
        if not comment_text:
            messages.error(request, "Comment cannot be empty")
            return redirect(reverse('fsr_details', args=[issues_id]) + f"?from={request.GET.get('from', '')}&referrer={request.GET.get('referrer', '')}")
        
        # Get user info if authenticated
        user_initials = ''
        if request.user.is_authenticated:
            user_initials = f"{request.user.first_name[:1]}{request.user.last_name[:1]}"
        
        # Create the comment
        issues_details.objects.create(
            issues_details_comment=comment_text,
            issues_details_user=user_initials,
            issues_details_date=date.today(),
            issues_id=issues_id
        )
        
        # Determine where to redirect back to
        redirect_url = request.POST.get('next', '')
        if not redirect_url:
            # Reconstruct the original URL with parameters
            from_param = request.GET.get('from', '')
            referrer = request.GET.get('referrer', '')
            if from_param and referrer:
                redirect_url = reverse('fsr_details', args=[issues_id]) + f"?from={from_param}&referrer={referrer}"
            else:
                redirect_url = reverse('fsr_details', args=[issues_id])
        
        messages.success(request, "Comment added successfully")
        return redirect(redirect_url)
    
    # If not POST, redirect to details page
    return redirect(reverse('fsr_details', args=[issues_id]))

def get_fsr_context_data(request):
    status_groups = []
    # Use your actual model name 'issues' (lowercase as defined)
    statuses = issues.objects.values_list('issues_status', flat=True).distinct()
    
    # Define the desired order for statuses
    status_order = ['Resolved', 'Unresolved', 'Issue']
    
    # Sort statuses according to the defined order
    # First get statuses that match our order, then any others that might exist
    ordered_statuses = []
    for preferred_status in status_order:
        if preferred_status in statuses:
            ordered_statuses.append(preferred_status)
    
    # Add any other statuses that weren't in our predefined order
    for status in statuses:
        if status not in ordered_statuses:
            ordered_statuses.append(status)
    
    for status in ordered_statuses:
        property_issues = []
        # Filter using the correct field name
        issues_with_status = issues.objects.filter(issues_status=status)
        # Access related property name via ForeignKey
        properties = issues_with_status.values_list('prop__prop_name', flat=True).distinct()
        
        for prop_name in properties:
            issues_fsr = issues_with_status.filter(prop__prop_name=prop_name)
            issue_data = []
            
            for issue in issues_fsr:
                # Use the correct foreign key field name 'issues' and primary key 'issues_id'
                # CHANGED: Added '-issues_details_date' for descending order
                details = issues_details.objects.filter(issues=issue.issues_id).order_by('-issues_details_date')
                issue_data.append({
                    'issues_id': issue.issues_id,  # Use the actual primary key field name
                    'issues_heading': issue.issues_heading,
                    'issues_description': issue.issues_description,
                    'days_to_resolve': getattr(issue, 'days_to_resolve', None),  # This field doesn't exist in your model
                    'days_open': getattr(issue, 'days_open', None),  # This field doesn't exist in your model
                    'details': details
                })
            
            property_issues.append({
                'prop_name': prop_name,
                'issues': issue_data
            })
        
        status_groups.append({
            'status': status,
            'property_issues': property_issues
        })
    
    return {
        'status_groups': status_groups,
        'today': date.today(),
        'request': request
    }

def fsr_pdf(request):
    context = get_fsr_context_data(request)
    return render_to_pdf('fsr_email.html', context)

def get_fsr_context_data(request):
    """
    Generate context data for Friday Status Report (used by both web view and email)
    Rewritten to use Django ORM instead of raw SQL
    """
    today = date.today()
    
    # Get max_comments parameter for summarized reports
    max_comments = request.GET.get('max_comments', None) if hasattr(request, 'GET') else None
    is_summarized_report = max_comments is not None
    
    if is_summarized_report:
        try:
            max_comments = int(max_comments)
        except (ValueError, TypeError):
            max_comments = None
            is_summarized_report = False
    
    # Get all properties ordered by country and name
    properties = props.objects.all().order_by('prop_country', 'prop_name').values('prop_name')
    
    # Get all issues with their details, using select_related and prefetch_related for optimization
    issues_queryset = issues.objects.select_related('prop').prefetch_related(
        Prefetch(
            'issues_details_set',
            queryset=issues_details.objects.all().order_by('-issues_details_id'),
            to_attr='details_list'
        )
    ).order_by('issues_id')
    
    # Process issues data
    issues_data = []
    for issue_obj in issues_queryset:
        # Build the issue dictionary
        issue_dict = {
            'prop_name': issue_obj.prop.prop_name,
            'issues_id': issue_obj.issues_id,
            'issues_heading': issue_obj.issues_heading,
            'issues_description': issue_obj.issues_description,
            'issues_status': issue_obj.issues_status,
            'issues_date_logged': issue_obj.issues_date_logged,
            'issues_resolution_date': issue_obj.issues_resolution_date,
            'days_to_resolve': None,
            'days_open': None,
            'details': []
        }
        
        # Calculate days metrics based on status
        if issue_dict['issues_date_logged']:
            if issue_dict['issues_status'] == 'Resolved':
                if (issue_dict['issues_resolution_date'] and 
                    issue_dict['issues_resolution_date'] != date(1900, 1, 1)):
                    issue_dict['days_to_resolve'] = (issue_dict['issues_resolution_date'] - issue_dict['issues_date_logged']).days
            else:
                issue_dict['days_open'] = (today - issue_dict['issues_date_logged']).days
        
        # Process details
        details_data = []
        for detail in issue_obj.details_list:
            details_data.append({
                'issues_details_id': detail.issues_details_id,
                'issues_details_comment': detail.issues_details_comment,
                'issues_details_user': detail.issues_details_user,
                'issues_details_date': detail.issues_details_date
            })
        
        # Apply comment limiting for summarized reports
        if is_summarized_report and max_comments and len(details_data) > max_comments:
            total_comments_before_limit = len(details_data)
            issue_dict['details'] = details_data[:max_comments]
            issue_dict['has_more_comments'] = True
            issue_dict['total_comments'] = total_comments_before_limit
        else:
            issue_dict['details'] = details_data
            issue_dict['has_more_comments'] = False
            issue_dict['total_comments'] = len(details_data)
        
        issues_data.append(issue_dict)
    
    # Process data by status and property
    processed_data = {}
    for status in ['Resolved', 'Unresolved', 'Issue']:
        processed_data[status] = {}
        for prop in properties:
            prop_name = prop['prop_name']
            processed_data[status][prop_name] = []

            unique_issues = set()

            for issue in issues_data:
                if (issue['prop_name'] == prop_name and 
                    issue['issues_status'] == status and 
                    (issue['issues_heading'], issue['issues_description']) not in unique_issues):

                    if status == 'Resolved':
                        if (issue['issues_resolution_date'] != date(1900, 1, 1) and 
                            issue['issues_resolution_date'] >= (date.today() - timedelta(days=7))):
                            processed_data[status][prop_name].append(issue)
                            unique_issues.add((issue['issues_heading'], issue['issues_description']))
                    else:
                        processed_data[status][prop_name].append(issue)
                        unique_issues.add((issue['issues_heading'], issue['issues_description']))
    
    context = {
        'today': today,
        'statuses': ['Resolved', 'Unresolved', 'Issue'],
        'properties': properties,
        'is_summarized_report': is_summarized_report,
        'max_comments': max_comments,
        'status_groups': [
            {
                'status': status,
                'property_issues': [
                    {
                        'prop_name': prop['prop_name'],
                        'issues': processed_data[status][prop['prop_name']]
                    }
                    for prop in properties
                    if processed_data[status][prop['prop_name']]
                ]
            }
            for status in ['Resolved', 'Unresolved', 'Issue']
        ]
    }
    
    return context

@login_required
def fsr_notification(request):
    smtp_object = None
    try:
        # Check if there's a max_comments parameter in the session or request
        # This indicates the user wants a summarized report
        max_comments = None
        is_summarized_report = False
        
        # Check for max_comments in various places:
        # 1. Direct GET parameter (if coming from Friday report page)
        # 2. Session storage (if user navigated from a summarized report)
        # 3. HTTP_REFERER analysis (check if previous page had max_comments)
        
        if 'max_comments' in request.GET:
            max_comments = request.GET.get('max_comments')
            is_summarized_report = True
        elif 'last_report_type' in request.session:
            # If we stored the last report type in session
            if request.session['last_report_type'] == 'summarized':
                max_comments = request.session.get('max_comments', '2')
                is_summarized_report = True
        else:
            # Check the HTTP referer to see if it came from a summarized report
            referer = request.META.get('HTTP_REFERER', '')
            if 'max_comments=' in referer:
                # Extract max_comments from referer URL
                import re
                match = re.search(r'max_comments=(\d+)', referer)
                if match:
                    max_comments = match.group(1)
                    is_summarized_report = True
        
        # Validate max_comments
        if is_summarized_report and max_comments:
            try:
                max_comments = int(max_comments)
                if max_comments < 1:
                    max_comments = 2
                    is_summarized_report = False
            except (ValueError, TypeError):
                max_comments = 2
                is_summarized_report = False
        
        # Create a mock request object with the appropriate parameters for context generation
        mock_request = type('MockRequest', (), {})()
        mock_request.user = request.user
        mock_request.session = request.session
        mock_request.META = request.META
        
        if is_summarized_report:
            # Create GET parameters for summarized report
            mock_request.GET = {'max_comments': str(max_comments)}
            report_type_text = f"Summarized Report (Max {max_comments} comments per issue)"
        else:
            # No parameters for detailed report
            mock_request.GET = {}
            report_type_text = "Detailed Report (All comments)"
        
        # Fetch context data for the report with appropriate parameters
        context = get_fsr_context_data(mock_request)
        
        # Add report type information to context for email template
        context['is_summarized_report'] = is_summarized_report
        context['max_comments'] = max_comments if is_summarized_report else None
        context['report_type_text'] = report_type_text
        
        # Render HTML content
        html_content = render_to_string("fsr_email.html", context, request=request)
        text_content = strip_tags(html_content)
        
        # Prepare email with report type in subject
        msg = MIMEMultipart("alternative")
        msg['From'] = "demetrimanias@gmail.com"
        msg['To'] = "demetrimanias@gmail.com"
        
        # Include report type in subject
        if is_summarized_report:
            msg['Subject'] = f"Friday Status Report - Summarized ({max_comments} comments/issue)"
        else:
            msg['Subject'] = "Friday Status Report - Detailed"
        
        # Attach both plain text and HTML
        msg.attach(MIMEText(text_content, 'plain'))
        msg.attach(MIMEText(html_content, 'html'))
        
        # SMTP setup
        smtp_object = smtplib.SMTP('smtp.gmail.com', 587)
        smtp_object.ehlo()
        smtp_object.starttls()
        
        email = "demetrimanias@gmail.com"
        password = os.environ.get('EMAIL_PASSWORD')
        
        smtp_object.login(email, password)
        smtp_object.sendmail(email, "demetrimanias@gmail.com", msg.as_string())
        
        success_message = f"Friday Status Report ({report_type_text}) sent successfully!"
        messages.success(request, success_message)
    
    except smtplib.SMTPAuthenticationError as e:
        logger.error(f"SMTP Authentication Error: {e}")
        messages.error(request, "Failed to send email - Authentication error.")
    except smtplib.SMTPException as e:
        logger.error(f"SMTP Error: {e}")
        messages.error(request, "Failed to send email - SMTP error.")
    except Exception as e:
        logger.error(f"Error sending email: {e}")
        messages.error(request, f"Failed to send email notification: {str(e)}")
    finally:
        if smtp_object:
            try:
                smtp_object.quit()
            except:
                pass
    
    return redirect('fsr')

### REPORTS - DASHBOARD (FROM HOME PAGE) ###
# Add these views to your views.py file
@login_required
def revenue_details_view(request):
    """
    View to show revenue details breakdown for budgeted/fixed revenues
    """
    year = request.GET.get('year', datetime.now().year)  # Just for display
    month = request.GET.get('month')
    line_type = request.GET.get('line_type')
    property_id = request.GET.get('property_id')
    prop = request.GET.get('prop', 'all')
    
    # Get all revenue records (no year filtering needed for budgeted revenues)
    revenues = revenue.objects.all().select_related('prop', 'revenue_line_types', 'revenue_types')
    
    # Filter by line type if specified
    if line_type:
        revenues = revenues.filter(revenue_line_types_id=line_type)
    
    # Filter by property
    if property_id and property_id != 'all':
        revenues = revenues.filter(prop_id=property_id)
    elif prop and prop != 'all':
        revenues = revenues.filter(prop_id=prop)
    
    # Get line type name for header
    line_type_name = "Revenue"
    if line_type:
        try:
            line_type_obj = revenue_line_types.objects.get(revenue_line_types_id=line_type)
            line_type_name = line_type_obj.revenue_line_types_name
        except revenue_line_types.DoesNotExist:
            line_type_name = "Unknown"
    
    # Get month name for subtitle
    month_names = {
        '1': 'January', '2': 'February', '3': 'March', '4': 'April',
        '5': 'May', '6': 'June', '7': 'July', '8': 'August',
        '9': 'September', '10': 'October', '11': 'November', '12': 'December'
    }
    month_name = month_names.get(str(month), "All Months") if month else "All Months"
    
    # Create a list of revenue items with monthly breakdown
    revenue_items = []
    total_amount = 0
    
    for rev in revenues:
        months = ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 
                 'jul', 'aug', 'sep', 'oct', 'nov', 'dec']
        
        for i, month_name_field in enumerate(months, 1):
            month_value = getattr(rev, f'revenue_{month_name_field}', 0)
            
            if month_value and month_value > 0:
                # If specific month is requested, only show that month
                if month and int(month) != i:
                    continue
                
                revenue_items.append({
                    'revenue_id': rev.revenue_id,
                    'property': rev.prop,
                    'amount': float(month_value),
                })
                total_amount += float(month_value)
    
    context = {
        'revenue_items': revenue_items,
        'total_amount': total_amount,
        'selected_year': year,
        'selected_month': month,
        'selected_line_type': line_type,
        'line_type_name': line_type_name,
        'month_name': month_name,
    }
    
    return render(request, 'revenue_details.html', context)

@login_required
def budget_expense_details_view(request):
    """
    View to show budgeted expense details breakdown
    """
    year = request.GET.get('year', datetime.now().year)  # Just for display
    month = request.GET.get('month')
    line_type = request.GET.get('line_type')
    property_id = request.GET.get('property_id')
    prop = request.GET.get('prop', 'all')
    
    # Get all budgeted expense records (no year filtering needed for budgeted expenses)
    expenses = expense.objects.all().select_related('prop', 'expense_line_types', 'expense_types')
    
    # Filter by line type if specified
    if line_type:
        expenses = expenses.filter(expense_line_types_id=line_type)
    
    # Filter by property
    if property_id and property_id != 'all':
        expenses = expenses.filter(prop_id=property_id)
    elif prop and prop != 'all':
        expenses = expenses.filter(prop_id=prop)
    
    # Get line type name for header
    line_type_name = "Budget Expenses"
    if line_type:
        try:
            line_type_obj = expense_line_types.objects.get(expense_line_types_id=line_type)
            line_type_name = line_type_obj.expense_line_types_name
        except expense_line_types.DoesNotExist:
            line_type_name = "Unknown"
    
    # Get month name for subtitle
    month_names = {
        '1': 'January', '2': 'February', '3': 'March', '4': 'April',
        '5': 'May', '6': 'June', '7': 'July', '8': 'August',
        '9': 'September', '10': 'October', '11': 'November', '12': 'December'
    }
    month_name = month_names.get(str(month), "All Months") if month else "All Months"
    
    # Create a list of expense items with monthly breakdown
    expense_items = []
    total_amount = 0
    
    for exp in expenses:
        months = ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 
                 'jul', 'aug', 'sep', 'oct', 'nov', 'dec']
        
        for i, month_field in enumerate(months, 1):
            month_value = getattr(exp, f'expense_{month_field}', 0)
            
            if month_value and month_value > 0:
                # If specific month is requested, only show that month
                if month and int(month) != i:
                    continue
                
                expense_items.append({
                    'expense_id': exp.expense_id,
                    'property': exp.prop,
                    'amount': float(month_value),
                })
                total_amount += float(month_value)
    
    context = {
        'expense_items': expense_items,
        'total_amount': total_amount,
        'selected_year': year,
        'selected_month': month,
        'selected_line_type': line_type,
        'line_type_name': line_type_name,
        'month_name': month_name,
    }
    
    return render(request, 'budget_expense_details.html', context)

@login_required
def total_expense_details_view(request):
    """
    View to show combined actual + budgeted expense details
    """
    year = request.GET.get('year', datetime.now().year)
    month = request.GET.get('month')
    property_id = request.GET.get('property_id')
    prop = request.GET.get('prop', 'all')
    
    # Get actual expenses
    actual_expenses = act_expense.objects.filter(
        act_expense_date__year=year
    ).select_related('prop')
    
    # Get budget expenses
    budget_expenses = expense.objects.filter(
        expense_types__expense_types_name__icontains=str(year)
    ).select_related('prop', 'expense_line_types', 'expense_types')
    
    # Filter by month if specified
    if month:
        actual_expenses = actual_expenses.filter(act_expense_date__month=month)
    
    # Filter by property
    if property_id:
        actual_expenses = actual_expenses.filter(prop_id=property_id)
        budget_expenses = budget_expenses.filter(prop_id=property_id)
    elif prop != 'all':
        actual_expenses = actual_expenses.filter(prop_id=prop)
        budget_expenses = budget_expenses.filter(prop_id=prop)
    
    # Order by date
    actual_expenses = actual_expenses.order_by('-act_expense_date')
    
    # Create budget expense items with monthly breakdown (similar to budget_expense_details_view)
    budget_expense_items = []
    for exp in budget_expenses:
        months = ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 
                 'jul', 'aug', 'sep', 'oct', 'nov', 'dec']
        
        for i, month_name in enumerate(months, 1):
            month_value = getattr(exp, f'expense_{month_name}', 0)
            if month_value and month_value > 0:
                # If specific month is requested, only show that month
                if month and int(month) != i:
                    continue
                    
                budget_expense_items.append({
                    'expense_id': exp.expense_id,
                    'property': exp.prop,
                    'expense_line_type': exp.expense_line_types,
                    'expense_type': exp.expense_types,
                    'month': i,
                    'month_name': month_name.capitalize(),
                    'amount': month_value,
                    'description': f"{exp.expense_line_types.expense_line_types_name} - {month_name.capitalize()} {year}",
                    'type': 'budget'
                })
    
    # Get line types and properties for context
    expense_line_types_list = expense_line_types.objects.all()
    properties = props.objects.all()
    
    context = {
        'actual_expenses': actual_expenses,
        'budget_expense_items': budget_expense_items,
        'expense_line_types': expense_line_types_list,
        'properties': properties,
        'selected_year': year,
        'selected_month': month,
        'selected_property': property_id,
        'prop': prop,
    }
    
    return render(request, 'total_expense_details.html', context)

@login_required
def finance_pl(request):
    # Get all properties with prefetched prop_values to optimize queries
    properties = props.objects.filter(prop_status="Active").prefetch_related('prop_values_set')
    
    # Revenue Section
    revenue_line_types_list = revenue_line_types.objects.all()
    revenues = revenue.objects.all()
    
    # Calculate revenue totals
    revenue_totals = {
        'jan': sum(r.revenue_jan or 0 for r in revenues),
        'feb': sum(r.revenue_feb or 0 for r in revenues),
        'mar': sum(r.revenue_mar or 0 for r in revenues),
        'apr': sum(r.revenue_apr or 0 for r in revenues),
        'may': sum(r.revenue_may or 0 for r in revenues),
        'jun': sum(r.revenue_jun or 0 for r in revenues),
        'jul': sum(r.revenue_jul or 0 for r in revenues),
        'aug': sum(r.revenue_aug or 0 for r in revenues),
        'sep': sum(r.revenue_sep or 0 for r in revenues),
        'oct': sum(r.revenue_oct or 0 for r in revenues),
        'nov': sum(r.revenue_nov or 0 for r in revenues),
        'dec': sum(r.revenue_dec or 0 for r in revenues),
    }
    revenue_totals['year'] = sum(revenue_totals.values())
    
    # Calculate revenue totals by line type for all properties
    revenue_totals_by_line = {'all': {}}
    for lt in revenue_line_types_list:
        line_revenues = revenues.filter(revenue_line_types=lt)
        monthly_totals = {
            'jan': sum(r.revenue_jan or 0 for r in line_revenues),
            'feb': sum(r.revenue_feb or 0 for r in line_revenues),
            'mar': sum(r.revenue_mar or 0 for r in line_revenues),
            'apr': sum(r.revenue_apr or 0 for r in line_revenues),
            'may': sum(r.revenue_may or 0 for r in line_revenues),
            'jun': sum(r.revenue_jun or 0 for r in line_revenues),
            'jul': sum(r.revenue_jul or 0 for r in line_revenues),
            'aug': sum(r.revenue_aug or 0 for r in line_revenues),
            'sep': sum(r.revenue_sep or 0 for r in line_revenues),
            'oct': sum(r.revenue_oct or 0 for r in line_revenues),
            'nov': sum(r.revenue_nov or 0 for r in line_revenues),
            'dec': sum(r.revenue_dec or 0 for r in line_revenues),
        }
        monthly_totals['total'] = sum(monthly_totals.values())
        revenue_totals_by_line['all'][lt.revenue_line_types_id] = monthly_totals
    
    # Calculate property-specific revenue totals
    revenue_prop_totals = {}
    for prop in properties:
        prop_revenues = revenues.filter(prop=prop)
        monthly_totals = {
            'jan': sum(r.revenue_jan or 0 for r in prop_revenues),
            'feb': sum(r.revenue_feb or 0 for r in prop_revenues),
            'mar': sum(r.revenue_mar or 0 for r in prop_revenues),
            'apr': sum(r.revenue_apr or 0 for r in prop_revenues),
            'may': sum(r.revenue_may or 0 for r in prop_revenues),
            'jun': sum(r.revenue_jun or 0 for r in prop_revenues),
            'jul': sum(r.revenue_jul or 0 for r in prop_revenues),
            'aug': sum(r.revenue_aug or 0 for r in prop_revenues),
            'sep': sum(r.revenue_sep or 0 for r in prop_revenues),
            'oct': sum(r.revenue_oct or 0 for r in prop_revenues),
            'nov': sum(r.revenue_nov or 0 for r in prop_revenues),
            'dec': sum(r.revenue_dec or 0 for r in prop_revenues),
        }
        monthly_totals['year'] = sum(monthly_totals.values())
        revenue_prop_totals[prop.prop_id] = monthly_totals
        
        # Add property-specific revenue line type totals
        revenue_totals_by_line[prop.prop_id] = {}
        for lt in revenue_line_types_list:
            prop_line_revenues = prop_revenues.filter(revenue_line_types=lt)
            line_monthly_totals = {
                'jan': sum(r.revenue_jan or 0 for r in prop_line_revenues),
                'feb': sum(r.revenue_feb or 0 for r in prop_line_revenues),
                'mar': sum(r.revenue_mar or 0 for r in prop_line_revenues),
                'apr': sum(r.revenue_apr or 0 for r in prop_line_revenues),
                'may': sum(r.revenue_may or 0 for r in prop_line_revenues),
                'jun': sum(r.revenue_jun or 0 for r in prop_line_revenues),
                'jul': sum(r.revenue_jul or 0 for r in prop_line_revenues),
                'aug': sum(r.revenue_aug or 0 for r in prop_line_revenues),
                'sep': sum(r.revenue_sep or 0 for r in prop_line_revenues),
                'oct': sum(r.revenue_oct or 0 for r in prop_line_revenues),
                'nov': sum(r.revenue_nov or 0 for r in prop_line_revenues),
                'dec': sum(r.revenue_dec or 0 for r in prop_line_revenues),
            }
            line_monthly_totals['total'] = sum(line_monthly_totals.values())
            revenue_totals_by_line[prop.prop_id][lt.revenue_line_types_id] = line_monthly_totals

    # Expense Section
    expense_line_types_list = expense_line_types.objects.all()
    expenses = expense.objects.all()
    
    # Calculate expense totals
    expense_totals = {
        'jan': sum(e.expense_jan or 0 for e in expenses),
        'feb': sum(e.expense_feb or 0 for e in expenses),
        'mar': sum(e.expense_mar or 0 for e in expenses),
        'apr': sum(e.expense_apr or 0 for e in expenses),
        'may': sum(e.expense_may or 0 for e in expenses),
        'jun': sum(e.expense_jun or 0 for e in expenses),
        'jul': sum(e.expense_jul or 0 for e in expenses),
        'aug': sum(e.expense_aug or 0 for e in expenses),
        'sep': sum(e.expense_sep or 0 for e in expenses),
        'oct': sum(e.expense_oct or 0 for e in expenses),
        'nov': sum(e.expense_nov or 0 for e in expenses),
        'dec': sum(e.expense_dec or 0 for e in expenses),
    }
    expense_totals['year'] = sum(expense_totals.values())
    
    # Calculate expense totals by line type for all properties
    expense_totals_by_line = {'all': {}}
    for elt in expense_line_types_list:
        line_expenses = expenses.filter(expense_line_types=elt)
        monthly_totals = {
            'jan': sum(e.expense_jan or 0 for e in line_expenses),
            'feb': sum(e.expense_feb or 0 for e in line_expenses),
            'mar': sum(e.expense_mar or 0 for e in line_expenses),
            'apr': sum(e.expense_apr or 0 for e in line_expenses),
            'may': sum(e.expense_may or 0 for e in line_expenses),
            'jun': sum(e.expense_jun or 0 for e in line_expenses),
            'jul': sum(e.expense_jul or 0 for e in line_expenses),
            'aug': sum(e.expense_aug or 0 for e in line_expenses),
            'sep': sum(e.expense_sep or 0 for e in line_expenses),
            'oct': sum(e.expense_oct or 0 for e in line_expenses),
            'nov': sum(e.expense_nov or 0 for e in line_expenses),
            'dec': sum(e.expense_dec or 0 for e in line_expenses),
        }
        monthly_totals['total'] = sum(monthly_totals.values())
        expense_totals_by_line['all'][elt.expense_line_types_id] = monthly_totals
    
    # Calculate property-specific expense totals
    expense_prop_totals = {}
    for prop in properties:
        prop_expenses = expenses.filter(prop=prop)
        monthly_totals = {
            'jan': sum(e.expense_jan or 0 for e in prop_expenses),
            'feb': sum(e.expense_feb or 0 for e in prop_expenses),
            'mar': sum(e.expense_mar or 0 for e in prop_expenses),
            'apr': sum(e.expense_apr or 0 for e in prop_expenses),
            'may': sum(e.expense_may or 0 for e in prop_expenses),
            'jun': sum(e.expense_jun or 0 for e in prop_expenses),
            'jul': sum(e.expense_jul or 0 for e in prop_expenses),
            'aug': sum(e.expense_aug or 0 for e in prop_expenses),
            'sep': sum(e.expense_sep or 0 for e in prop_expenses),
            'oct': sum(e.expense_oct or 0 for e in prop_expenses),
            'nov': sum(e.expense_nov or 0 for e in prop_expenses),
            'dec': sum(e.expense_dec or 0 for e in prop_expenses),
        }
        monthly_totals['year'] = sum(monthly_totals.values())
        expense_prop_totals[prop.prop_id] = monthly_totals
        
        # Add property-specific expense line type totals
        expense_totals_by_line[prop.prop_id] = {}
        for elt in expense_line_types_list:
            prop_line_expenses = prop_expenses.filter(expense_line_types=elt)
            line_monthly_totals = {
                'jan': sum(e.expense_jan or 0 for e in prop_line_expenses),
                'feb': sum(e.expense_feb or 0 for e in prop_line_expenses),
                'mar': sum(e.expense_mar or 0 for e in prop_line_expenses),
                'apr': sum(e.expense_apr or 0 for e in prop_line_expenses),
                'may': sum(e.expense_may or 0 for e in prop_line_expenses),
                'jun': sum(e.expense_jun or 0 for e in prop_line_expenses),
                'jul': sum(e.expense_jul or 0 for e in prop_line_expenses),
                'aug': sum(e.expense_aug or 0 for e in prop_line_expenses),
                'sep': sum(e.expense_sep or 0 for e in prop_line_expenses),
                'oct': sum(e.expense_oct or 0 for e in prop_line_expenses),
                'nov': sum(e.expense_nov or 0 for e in prop_line_expenses),
                'dec': sum(e.expense_dec or 0 for e in prop_line_expenses),
            }
            line_monthly_totals['total'] = sum(line_monthly_totals.values())
            expense_totals_by_line[prop.prop_id][elt.expense_line_types_id] = line_monthly_totals

    # Calculate Profit (Revenue - Expenses)
    profit_totals = {
        'jan': revenue_totals['jan'] - expense_totals['jan'],
        'feb': revenue_totals['feb'] - expense_totals['feb'],
        'mar': revenue_totals['mar'] - expense_totals['mar'],
        'apr': revenue_totals['apr'] - expense_totals['apr'],
        'may': revenue_totals['may'] - expense_totals['may'],
        'jun': revenue_totals['jun'] - expense_totals['jun'],
        'jul': revenue_totals['jul'] - expense_totals['jul'],
        'aug': revenue_totals['aug'] - expense_totals['aug'],
        'sep': revenue_totals['sep'] - expense_totals['sep'],
        'oct': revenue_totals['oct'] - expense_totals['oct'],
        'nov': revenue_totals['nov'] - expense_totals['nov'],
        'dec': revenue_totals['dec'] - expense_totals['dec'],
        'year': revenue_totals['year'] - expense_totals['year']
    }

    # Prepare property values mapping for easy access in template
    prop_values_map = {prop.prop_id: prop.prop_values_set.first() for prop in properties}
    total_current_value = 0
    for prop in properties:
        prop_values = prop.prop_values_set.first()
        if prop_values and prop_values.prop_values_current_value is not None:
            total_current_value += prop_values.prop_values_current_value

    return render(request, 'finance_pl.html', {
        'properties': properties,
        'revenue_line_types': revenue_line_types_list,
        'revenue_totals': revenue_totals,
        'revenue_totals_by_line': revenue_totals_by_line,
        'revenue_prop_totals': revenue_prop_totals,
        'expense_line_types': expense_line_types_list,
        'expense_totals': expense_totals,
        'expense_totals_by_line': expense_totals_by_line,
        'expense_prop_totals': expense_prop_totals,
        'profit_totals': profit_totals,
        'prop_values_map': prop_values_map,
        'total_current_value': total_current_value,
    })

@login_required
def finance_pl_act(request):
    # Get selected year from request (default to current year)
    selected_year = request.GET.get('year', datetime.now().year)
    active_prop = request.GET.get('prop', 'all')  # Default to 'all' properties

    try:
        selected_year = int(selected_year)
    except (ValueError, TypeError):
        selected_year = now().year
    
    # Ensure only 2024 or 2025 is selectable
    if selected_year not in [2024, 2025]:
        selected_year = now().year
    
    # Get all properties with prefetched prop_values
    properties = props.objects.filter(prop_status="Active").prefetch_related('prop_values_set')
    
    # ========= REVENUE SECTION ========= (unchanged as per requirements)
    revenue_line_types_list = revenue_line_types.objects.all()
    revenues = revenue.objects.all()
    
    # Calculate revenue totals
    revenue_totals = {
        'jan': sum(r.revenue_jan or 0 for r in revenues),
        'feb': sum(r.revenue_feb or 0 for r in revenues),
        'mar': sum(r.revenue_mar or 0 for r in revenues),
        'apr': sum(r.revenue_apr or 0 for r in revenues),
        'may': sum(r.revenue_may or 0 for r in revenues),
        'jun': sum(r.revenue_jun or 0 for r in revenues),
        'jul': sum(r.revenue_jul or 0 for r in revenues),
        'aug': sum(r.revenue_aug or 0 for r in revenues),
        'sep': sum(r.revenue_sep or 0 for r in revenues),
        'oct': sum(r.revenue_oct or 0 for r in revenues),
        'nov': sum(r.revenue_nov or 0 for r in revenues),
        'dec': sum(r.revenue_dec or 0 for r in revenues),
    }
    revenue_totals['year'] = sum(revenue_totals.values())
    
    # Calculate revenue totals by line type for all properties
    revenue_totals_by_line = {'all': {}}
    for lt in revenue_line_types_list:
        line_revenues = revenues.filter(revenue_line_types=lt)
        monthly_totals = {
            'jan': sum(r.revenue_jan or 0 for r in line_revenues),
            'feb': sum(r.revenue_feb or 0 for r in line_revenues),
            'mar': sum(r.revenue_mar or 0 for r in line_revenues),
            'apr': sum(r.revenue_apr or 0 for r in line_revenues),
            'may': sum(r.revenue_may or 0 for r in line_revenues),
            'jun': sum(r.revenue_jun or 0 for r in line_revenues),
            'jul': sum(r.revenue_jul or 0 for r in line_revenues),
            'aug': sum(r.revenue_aug or 0 for r in line_revenues),
            'sep': sum(r.revenue_sep or 0 for r in line_revenues),
            'oct': sum(r.revenue_oct or 0 for r in line_revenues),
            'nov': sum(r.revenue_nov or 0 for r in line_revenues),
            'dec': sum(r.revenue_dec or 0 for r in line_revenues),
        }
        monthly_totals['total'] = sum(monthly_totals.values())
        revenue_totals_by_line['all'][lt.revenue_line_types_id] = monthly_totals
    
    # Calculate property-specific revenue totals
    revenue_prop_totals = {}
    for prop in properties:
        prop_revenues = revenues.filter(prop=prop)
        monthly_totals = {
            'jan': sum(r.revenue_jan or 0 for r in prop_revenues),
            'feb': sum(r.revenue_feb or 0 for r in prop_revenues),
            'mar': sum(r.revenue_mar or 0 for r in prop_revenues),
            'apr': sum(r.revenue_apr or 0 for r in prop_revenues),
            'may': sum(r.revenue_may or 0 for r in prop_revenues),
            'jun': sum(r.revenue_jun or 0 for r in prop_revenues),
            'jul': sum(r.revenue_jul or 0 for r in prop_revenues),
            'aug': sum(r.revenue_aug or 0 for r in prop_revenues),
            'sep': sum(r.revenue_sep or 0 for r in prop_revenues),
            'oct': sum(r.revenue_oct or 0 for r in prop_revenues),
            'nov': sum(r.revenue_nov or 0 for r in prop_revenues),
            'dec': sum(r.revenue_dec or 0 for r in prop_revenues),
        }
        monthly_totals['year'] = sum(monthly_totals.values())
        revenue_prop_totals[prop.prop_id] = monthly_totals
        
        # Add property-specific revenue line type totals
        revenue_totals_by_line[prop.prop_id] = {}
        for lt in revenue_line_types_list:
            prop_line_revenues = prop_revenues.filter(revenue_line_types=lt)
            line_monthly_totals = {
                'jan': sum(r.revenue_jan or 0 for r in prop_line_revenues),
                'feb': sum(r.revenue_feb or 0 for r in prop_line_revenues),
                'mar': sum(r.revenue_mar or 0 for r in prop_line_revenues),
                'apr': sum(r.revenue_apr or 0 for r in prop_line_revenues),
                'may': sum(r.revenue_may or 0 for r in prop_line_revenues),
                'jun': sum(r.revenue_jun or 0 for r in prop_line_revenues),
                'jul': sum(r.revenue_jul or 0 for r in prop_line_revenues),
                'aug': sum(r.revenue_aug or 0 for r in prop_line_revenues),
                'sep': sum(r.revenue_sep or 0 for r in prop_line_revenues),
                'oct': sum(r.revenue_oct or 0 for r in prop_line_revenues),
                'nov': sum(r.revenue_nov or 0 for r in prop_line_revenues),
                'dec': sum(r.revenue_dec or 0 for r in prop_line_revenues),
            }
            line_monthly_totals['total'] = sum(line_monthly_totals.values())
            revenue_totals_by_line[prop.prop_id][lt.revenue_line_types_id] = line_monthly_totals

    # ========= EXPENSE SECTION =========
    expense_line_types_list = expense_line_types.objects.all()
    expenses = expense.objects.all()
    
    # Calculate ACTUAL expenses - FILTERED BY SELECTED YEAR, APPROVED AND PAID
    actual_expenses = act_expense.objects.filter(
        act_expense_date__year=selected_year,
        act_expense_approved="Yes",
        act_expense_paid="Yes"
    )
    
    # Initialize actual expense totals
    actual_expense_totals = {
        'jan': 0, 'feb': 0, 'mar': 0, 'apr': 0, 'may': 0, 'jun': 0,
        'jul': 0, 'aug': 0, 'sep': 0, 'oct': 0, 'nov': 0, 'dec': 0, 'year': 0
    }
    
    # Calculate totals for all properties
    for month in ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 
                 'jul', 'aug', 'sep', 'oct', 'nov', 'dec']:
        month_num = {
            'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
            'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12
        }[month]
        
        monthly_expenses = actual_expenses.filter(
            act_expense_date__month=month_num
        ).aggregate(total=Sum('act_expense_amount'))['total'] or 0
        
        actual_expense_totals[month] = monthly_expenses
    
    actual_expense_totals['year'] = sum(actual_expense_totals.values())
    
    # Calculate property-specific actual expenses
    actual_expense_prop_totals = {}
    for prop in properties:
        prop_totals = {
            'jan': 0, 'feb': 0, 'mar': 0, 'apr': 0, 'may': 0, 'jun': 0,
            'jul': 0, 'aug': 0, 'sep': 0, 'oct': 0, 'nov': 0, 'dec': 0, 'year': 0
        }
        
        for month in ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 
                     'jul', 'aug', 'sep', 'oct', 'nov', 'dec']:
            month_num = {
                'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
                'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12
            }[month]
            
            monthly_expenses = actual_expenses.filter(
                prop=prop,
                act_expense_date__month=month_num
            ).aggregate(total=Sum('act_expense_amount'))['total'] or 0
            
            prop_totals[month] = monthly_expenses
        
        prop_totals['year'] = sum(prop_totals.values())
        actual_expense_prop_totals[prop.prop_id] = prop_totals
    
    # Calculate budgeted expense totals
    expense_totals = {
        'jan': sum(e.expense_jan or 0 for e in expenses),
        'feb': sum(e.expense_feb or 0 for e in expenses),
        'mar': sum(e.expense_mar or 0 for e in expenses),
        'apr': sum(e.expense_apr or 0 for e in expenses),
        'may': sum(e.expense_may or 0 for e in expenses),
        'jun': sum(e.expense_jun or 0 for e in expenses),
        'jul': sum(e.expense_jul or 0 for e in expenses),
        'aug': sum(e.expense_aug or 0 for e in expenses),
        'sep': sum(e.expense_sep or 0 for e in expenses),
        'oct': sum(e.expense_oct or 0 for e in expenses),
        'nov': sum(e.expense_nov or 0 for e in expenses),
        'dec': sum(e.expense_dec or 0 for e in expenses),
    }
    expense_totals['year'] = sum(expense_totals.values())
    
    # Calculate expense totals by line type for all properties
    expense_totals_by_line = {'all': {}}
    for elt in expense_line_types_list:
        line_expenses = expenses.filter(expense_line_types=elt)
        monthly_totals = {
            'jan': sum(e.expense_jan or 0 for e in line_expenses),
            'feb': sum(e.expense_feb or 0 for e in line_expenses),
            'mar': sum(e.expense_mar or 0 for e in line_expenses),
            'apr': sum(e.expense_apr or 0 for e in line_expenses),
            'may': sum(e.expense_may or 0 for e in line_expenses),
            'jun': sum(e.expense_jun or 0 for e in line_expenses),
            'jul': sum(e.expense_jul or 0 for e in line_expenses),
            'aug': sum(e.expense_aug or 0 for e in line_expenses),
            'sep': sum(e.expense_sep or 0 for e in line_expenses),
            'oct': sum(e.expense_oct or 0 for e in line_expenses),
            'nov': sum(e.expense_nov or 0 for e in line_expenses),
            'dec': sum(e.expense_dec or 0 for e in line_expenses),
        }
        monthly_totals['total'] = sum(monthly_totals.values())
        expense_totals_by_line['all'][elt.expense_line_types_id] = monthly_totals
    
    # Calculate property-specific expense totals
    expense_prop_totals = {}
    for prop in properties:
        prop_expenses = expenses.filter(prop=prop)
        monthly_totals = {
            'jan': sum(e.expense_jan or 0 for e in prop_expenses),
            'feb': sum(e.expense_feb or 0 for e in prop_expenses),
            'mar': sum(e.expense_mar or 0 for e in prop_expenses),
            'apr': sum(e.expense_apr or 0 for e in prop_expenses),
            'may': sum(e.expense_may or 0 for e in prop_expenses),
            'jun': sum(e.expense_jun or 0 for e in prop_expenses),
            'jul': sum(e.expense_jul or 0 for e in prop_expenses),
            'aug': sum(e.expense_aug or 0 for e in prop_expenses),
            'sep': sum(e.expense_sep or 0 for e in prop_expenses),
            'oct': sum(e.expense_oct or 0 for e in prop_expenses),
            'nov': sum(e.expense_nov or 0 for e in prop_expenses),
            'dec': sum(e.expense_dec or 0 for e in prop_expenses),
        }
        monthly_totals['year'] = sum(monthly_totals.values())
        expense_prop_totals[prop.prop_id] = monthly_totals
        
        # Add property-specific expense line type totals
        expense_totals_by_line[prop.prop_id] = {}
        for elt in expense_line_types_list:
            prop_line_expenses = prop_expenses.filter(expense_line_types=elt)
            line_monthly_totals = {
                'jan': sum(e.expense_jan or 0 for e in prop_line_expenses),
                'feb': sum(e.expense_feb or 0 for e in prop_line_expenses),
                'mar': sum(e.expense_mar or 0 for e in prop_line_expenses),
                'apr': sum(e.expense_apr or 0 for e in prop_line_expenses),
                'may': sum(e.expense_may or 0 for e in prop_line_expenses),
                'jun': sum(e.expense_jun or 0 for e in prop_line_expenses),
                'jul': sum(e.expense_jul or 0 for e in prop_line_expenses),
                'aug': sum(e.expense_aug or 0 for e in prop_line_expenses),
                'sep': sum(e.expense_sep or 0 for e in prop_line_expenses),
                'oct': sum(e.expense_oct or 0 for e in prop_line_expenses),
                'nov': sum(e.expense_nov or 0 for e in prop_line_expenses),
                'dec': sum(e.expense_dec or 0 for e in prop_line_expenses),
            }
            line_monthly_totals['total'] = sum(line_monthly_totals.values())
            expense_totals_by_line[prop.prop_id][elt.expense_line_types_id] = line_monthly_totals

    # ========= PROFIT CALCULATION =========
    profit_totals = {
        'jan': revenue_totals['jan'] - expense_totals['jan'],
        'feb': revenue_totals['feb'] - expense_totals['feb'],
        'mar': revenue_totals['mar'] - expense_totals['mar'],
        'apr': revenue_totals['apr'] - expense_totals['apr'],
        'may': revenue_totals['may'] - expense_totals['may'],
        'jun': revenue_totals['jun'] - expense_totals['jun'],
        'jul': revenue_totals['jul'] - expense_totals['jul'],
        'aug': revenue_totals['aug'] - expense_totals['aug'],
        'sep': revenue_totals['sep'] - expense_totals['sep'],
        'oct': revenue_totals['oct'] - expense_totals['oct'],
        'nov': revenue_totals['nov'] - expense_totals['nov'],
        'dec': revenue_totals['dec'] - expense_totals['dec'],
        'year': revenue_totals['year'] - expense_totals['year']
    }

    # Prepare property values mapping
    prop_values_map = {prop.prop_id: prop.prop_values_set.first() for prop in properties}
    total_current_value = sum(
        pv.prop_values_current_value 
        for pv in prop_values_map.values() 
        if pv and pv.prop_values_current_value is not None
    )

    return render(request, 'finance_pl_act.html', {
        'properties': properties,
        'revenue_line_types': revenue_line_types_list,
        'revenue_totals': revenue_totals,
        'revenue_totals_by_line': revenue_totals_by_line,
        'revenue_prop_totals': revenue_prop_totals,
        'expense_line_types': expense_line_types_list,
        'expense_totals': expense_totals,
        'expense_totals_by_line': expense_totals_by_line,
        'expense_prop_totals': expense_prop_totals,
        'profit_totals': profit_totals,
        'prop_values_map': prop_values_map,
        'total_current_value': total_current_value,
        'actual_expense_totals': actual_expense_totals,
        'actual_expense_prop_totals': actual_expense_prop_totals,
        'selected_year': selected_year,
        'active_prop': active_prop,
        'available_years': [2024, 2025],
    })

@login_required
def petty_cash_rep(request):
	import petty_cash
	rep_output = request.POST.get('d_e')
	if request.user.is_authenticated:
		email = request.user.email
		fname = request.user.first_name
	petty_cash.petty_cash(rep_output, email, fname)
	messages.success(request, "Report Created Successfully")
	return redirect('home')

@login_required
def lease_agreements(request):
	import print_lease
	prop = request.POST.get('propname')
	rep_output = request.POST.get('d_e')
	if request.user.is_authenticated:
		email = request.user.email
		fname = request.user.first_name
	print_lease.lease_report(prop, rep_output, email, fname)
	messages.success(request, "Report Created Successfully")
	return redirect('home')

@login_required
def title_deeds(request):
	import print_title
	prop = request.POST.get('propname')
	rep_output = request.POST.get('d_e')
	if request.user.is_authenticated:
		email = request.user.email
		fname = request.user.first_name
	print_title.title_report(prop, rep_output, email, fname)
	messages.success(request, "Report Created Successfully")
	return redirect('home')

@login_required
def prop_rep(request):
	import print_prop
	prop = request.POST.get('propname')
	rep_output = request.POST.get('d_e')
	if request.user.is_authenticated:
		email = request.user.email
		fname = request.user.first_name
	print_prop.prop_report(prop, rep_output, email, fname)
	messages.success(request, "Report Created Successfully")
	return redirect('home')

@login_required
def property_report(request, prop_id):
	today = date.today()
	property = get_object_or_404(props.objects.only(
    	'prop_id', 'prop_name', 'prop_address1', 'prop_address2', 'prop_suburb', 
		'prop_city', 'prop_province', 'prop_country', 'prop_pcode',
		'prop_floor_area', 'prop_year_built', 'prop_status',
		'prop_available_for_rent', 'prop_title_deed',
		'prop_title_deed_status', 'prop_electricity', 'prop_water',
		'prop_refuse', 'prop_property_tax', 'prop_sewerage', 'prop_insurance'
	), pk=prop_id)
	context = {
		'today': today,
		'property': property,
	}
	return render(request, 'property_report.html', context)

@login_required
def title_deed_report(request, prop_id):
    property = get_object_or_404(props, pk=prop_id)
    
    if not property.prop_title_deed:
        return JsonResponse({'error': 'No title deed available for this property'}, status=404)
    
    # Return JSON with the file URL and type
    return JsonResponse({
        'file_url': property.prop_title_deed.url,
        'file_name': property.prop_title_deed.name.split('/')[-1],
        'file_type': property.prop_title_deed.name.split('.')[-1].lower()
    })

@login_required
def lease_agreement_report(request, tenant_id):
	today = date.today()
	tenant_obj = get_object_or_404(tenant.objects.only(
		'tenant_id', 'prop_id', 'tenant_type', 'tenant_name', 'tenant_contact_person', 'tenant_contact_number', 
		'tenant_email', 'tenant_deposit', 'tenant_lease_start_date', 'tenant_lease_end_date',
		'tenant_rental_type', 'tenant_renewal', 'tenant_renewal_period',
		'tenant_rent', 'tenant_levies',
		'tenant_payment_terms', 'tenant_current', 'tenant_lease_agreement'
	), pk=tenant_id)
	property = get_object_or_404(props.objects.only(
		'prop_id', 'prop_name', 'prop_address1', 'prop_address2', 'prop_suburb', 
		'prop_city', 'prop_province', 'prop_country', 'prop_pcode',
		'prop_floor_area', 'prop_year_built', 'prop_status',
		'prop_available_for_rent', 'prop_title_deed',
		'prop_title_deed_status', 'prop_electricity', 'prop_water',
		'prop_refuse', 'prop_property_tax', 'prop_sewerage', 'prop_insurance'
	), pk=tenant_obj.prop_id)
	context = {
		'today': today,
		'tenant': tenant_obj,
		'property': property,
	}
	return render(request, 'lease_agreement_report.html', context)

@login_required
def tenant_report(request, tenant_id):
	today = date.today()
	tenant_obj = get_object_or_404(tenant.objects.only(
		'tenant_id', 'prop_id', 'tenant_type', 'tenant_name', 'tenant_contact_person', 'tenant_contact_number', 
		'tenant_email', 'tenant_deposit', 'tenant_lease_start_date', 'tenant_lease_end_date',
		'tenant_rental_type', 'tenant_renewal', 'tenant_renewal_period',
		'tenant_rent', 'tenant_levies',
		'tenant_payment_terms', 'tenant_current', 'tenant_lease_agreement'
	), pk=tenant_id)
	context = {
		'today': today,
		'tenant': tenant_obj,
	}
	return render(request, 'tenant_report.html', context)

@login_required
def supplier_report(request, supplier_id):
	today = date.today()
	supplier_obj = get_object_or_404(supplier.objects.only(
		'supplier_id', 'supplier_contact_person', 'supplier_contact_number', 
		'supplier_email', 'supplier_company_name', 'supplier_role',
		'supplier_country'
	), pk=supplier_id)
	context = {
		'today': today,
		'supplier': supplier_obj,
	}
	return render(request, 'supplier_report.html', context)

@login_required
def tenant_rep(request):
	import print_tenant
	prop = request.POST.get('propname')
	rep_output = request.POST.get('d_e')
	if request.user.is_authenticated:
		email = request.user.email
		fname = request.user.first_name
	print_tenant.tenant_report(prop, rep_output, email, fname)
	messages.success(request, "Report Created Successfully")
	return redirect('home')

@login_required
def suppliers_rep(request):
	import print_supplier
	sup = request.POST.get('supname')
	rep_output = request.POST.get('d_e')
	if request.user.is_authenticated:
		email = request.user.email
		fname = request.user.first_name
	print_supplier.supplier_report(sup, rep_output, email, fname)
	messages.success(request, "Report Created Successfully")
	return redirect('home')

@login_required
def fsr_rep(request):
	import fsr
	rep_type = request.POST.get('d_s')
	rep_output = request.POST.get('d_e')
	rep_date = date.today()
	if request.user.is_authenticated:
		email = request.user.email
		fname = request.user.first_name
	fsr.fsr_report(rep_type, rep_date, rep_output, email, fname)
	messages.success(request, "Report Created Successfully")
	return redirect('home')

@login_required
def friday_status_report(request):
    today = date.today()
    rep_date = today
    
    # Get max_comments parameter for summarized reports
    max_comments = request.GET.get('max_comments', None)
    is_summarized_report = max_comments is not None
    
    # Store report type in session for use by fsr_notification
    if is_summarized_report:
        try:
            max_comments = int(max_comments)
            request.session['last_report_type'] = 'summarized'
            request.session['max_comments'] = max_comments
        except (ValueError, TypeError):
            max_comments = None
            is_summarized_report = False
            request.session['last_report_type'] = 'detailed'
            request.session.pop('max_comments', None)
    else:
        request.session['last_report_type'] = 'detailed'
        request.session.pop('max_comments', None)
    
    # Get all properties ordered by country and name
    properties = props.objects.all().order_by('prop_country', 'prop_name').values('prop_name')
    
    # Get all issues with their details, using select_related and prefetch_related for optimization
    issues_queryset = issues.objects.select_related('prop').prefetch_related(
        Prefetch(
            'issues_details_set',
            queryset=issues_details.objects.all().order_by('-issues_details_id'),
            to_attr='details_list'
        )
    ).order_by('issues_id')
    
    # Process issues data
    issues_data = []
    for issue_obj in issues_queryset:
        # Build the issue dictionary
        issue_dict = {
            'prop_name': issue_obj.prop.prop_name,
            'issues_id': issue_obj.issues_id,
            'issues_heading': issue_obj.issues_heading,
            'issues_description': issue_obj.issues_description,
            'issues_status': issue_obj.issues_status,
            'issues_date_logged': issue_obj.issues_date_logged,
            'issues_resolution_date': issue_obj.issues_resolution_date,
            'days_to_resolve': None,  # For resolved issues
            'days_open': None,       # For unresolved issues
            'details': []
        }
        
        # Calculate days metrics based on status
        if issue_dict['issues_date_logged']:
            if issue_dict['issues_status'] == 'Resolved':
                if (issue_dict['issues_resolution_date'] and 
                    issue_dict['issues_resolution_date'] != date(1900, 1, 1)):
                    issue_dict['days_to_resolve'] = (issue_dict['issues_resolution_date'] - issue_dict['issues_date_logged']).days
            else:  # For Unresolved and Issue status
                issue_dict['days_open'] = (today - issue_dict['issues_date_logged']).days
        
        # Process details
        details_data = []
        for detail in issue_obj.details_list:
            details_data.append({
                'issues_details_id': detail.issues_details_id,
                'issues_details_comment': detail.issues_details_comment,
                'issues_details_user': detail.issues_details_user,
                'issues_details_date': detail.issues_details_date
            })
        
        # Apply comment limiting for summarized reports
        if is_summarized_report and max_comments and len(details_data) > max_comments:
            total_comments_before_limit = len(details_data)
            issue_dict['details'] = details_data[:max_comments]
            issue_dict['has_more_comments'] = True
            issue_dict['total_comments'] = total_comments_before_limit
        else:
            issue_dict['details'] = details_data
            issue_dict['has_more_comments'] = False
            issue_dict['total_comments'] = len(details_data)
        
        issues_data.append(issue_dict)
    
    # Process data by status and property
    processed_data = {}
    cut_off_date = date.today() - timedelta(days=7)
    for status in ['Resolved', 'Unresolved', 'Issue']:
        processed_data[status] = {}
        for prop in properties:
            prop_name = prop['prop_name']
            processed_data[status][prop_name] = []

            # Track unique issues by heading+description
            unique_issues = set()

            for issue in issues_data:
                if (issue['prop_name'] == prop_name and 
                    issue['issues_status'] == status and 
                    (issue['issues_heading'], issue['issues_description']) not in unique_issues):

                    # For Resolved, check cutoff date
                    if status == 'Resolved':
                        if (issue['issues_resolution_date'] != date(1900, 1, 1) and 
                            issue['issues_resolution_date'] >= (date.today() - timedelta(days=7))):
                            processed_data[status][prop_name].append(issue)
                            unique_issues.add((issue['issues_heading'], issue['issues_description']))
                    else:
                        processed_data[status][prop_name].append(issue)
                        unique_issues.add((issue['issues_heading'], issue['issues_description']))
    
    context = {
        'today': today,
        'statuses': ['Resolved', 'Unresolved', 'Issue'],
        'properties': properties,
        'is_summarized_report': is_summarized_report,
        'max_comments': max_comments,
        'status_groups': [
            {
                'status': status,
                'property_issues': [
                    {
                        'prop_name': prop['prop_name'],
                        'issues': processed_data[status][prop['prop_name']]
                    }
                    for prop in properties
                    if processed_data[status][prop['prop_name']]  # Only include if issues exist
                ]
            }
            for status in ['Resolved', 'Unresolved', 'Issue']
        ]
    }
    
    return render(request, 'friday_status_report.html', context)

@login_required
def resolved_issues_report(request):
    # Get dates from GET parameters
    f_date_str = request.GET.get('f_date')
    t_date_str = request.GET.get('t_date')

    # Validate dates
    if not f_date_str or not t_date_str:
        messages.error(request, "Both date ranges are required")
        return redirect('fsr')

    try:
        f_date = parse_date(f_date_str)
        t_date = parse_date(t_date_str)
        
        if not f_date or not t_date:
            raise ValueError("Invalid date format")
            
        if t_date < f_date:
            messages.error(request, "End date cannot be before start date")
            return redirect('fsr')

    except (ValueError, TypeError) as e:
        messages.error(request, f"Invalid date format: {str(e)}")
        return redirect('fsr')

    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    prop.prop_name, 
                    issues.issues_heading, 
                    issues.issues_description, 
                    issues.issues_status,
                    issues_details.issues_details_comment,
                    issues_details.issues_details_user,
                    issues_details.issues_details_date,
                    issues.issues_resolution_date,
                    issues.issues_date_logged
                FROM 
                    prop
                    JOIN issues ON prop.prop_id = issues.prop_id
                    JOIN issues_details ON issues.issues_id = issues_details.issues_id
                WHERE 
                    issues.issues_status = 'Resolved'
                    AND issues.issues_resolution_date BETWEEN %s AND %s
                ORDER BY 
                    prop.prop_name ASC,
                    issues.issues_heading ASC,
                    issues_details.issues_details_date DESC
            """, [f_date_str, t_date_str])

            rows = cursor.fetchall()

        # Helper function to parse dates
        def parse_db_date(date_value):
            if isinstance(date_value, date):
                return date_value
            elif isinstance(date_value, str):
                return datetime.strptime(date_value, '%Y-%m-%d').date()
            elif isinstance(date_value, datetime):
                return date_value.date()
            else:
                raise ValueError(f"Unsupported date format: {type(date_value)}")

        # Structure the data
        properties = defaultdict(lambda: {
            'prop_name': '',
            'issues': defaultdict(list)
        })

        for row in rows:
            prop_name = row[0]
            issue_heading = row[1]
            
            try:
                resolution_date = parse_db_date(row[7])
                date_logged = parse_db_date(row[8])
                days_to_resolve = (resolution_date - date_logged).days
            except Exception as e:
                days_to_resolve = 0  # Default value if date parsing fails

            properties[prop_name]['prop_name'] = prop_name
            properties[prop_name]['issues'][issue_heading].append({
                'issues_description': row[2],
                'comment': row[4],
                'user': row[5],
                'comment_date': row[6],
                'resolution_date': row[7],
                'date_logged': row[8],
                'days_to_resolve': days_to_resolve
            })

        # Convert to list format for template
        properties_list = []
        for prop_name, prop_data in properties.items():
            issues_list = []
            for issue_heading, comments in prop_data['issues'].items():
                issues_list.append({
                    'heading': issue_heading,
                    'description': comments[0]['issues_description'],
                    'issues_date_logged': comments[0]['date_logged'],
                    'issues_resolution_date': comments[0]['resolution_date'],
                    'days_to_resolve': comments[0]['days_to_resolve'],
                    'comments': sorted(comments, key=lambda x: x['comment_date'], reverse=True)[:20]
                })

            properties_list.append({
                'prop_name': prop_name,
                'issues': sorted(issues_list, key=lambda x: x['heading'])
            })

        context = {
            'f_date': f_date_str,
            't_date': t_date_str,
            'properties': sorted(properties_list, key=lambda x: x['prop_name'])
        }

        return render(request, 'resolved_issues_report.html', context)

    except Exception as e:
        messages.error(request, f"Error generating report: {str(e)}")
        return redirect('fsr')

@login_required
def issues_rep(request):
	import issues
	f_d = request.POST.get('from_date')
	f_date = datetime.strptime(f_d, "%Y-%m-%d")
	from_date = f_date.date()
	t_d = request.POST.get('to_date')
	t_date = datetime.strptime(t_d, "%Y-%m-%d")
	to_date = t_date.date()
	rep_output = request.POST.get('d_e')
	rep_date = date.today()
	if request.user.is_authenticated:
		email = request.user.email
		fname = request.user.first_name
	issues.issues_report(from_date, to_date, rep_output, email, fname)
	messages.success(request, "Report Created Successfully")
	return redirect('home')

@login_required
def open_invoices(request):
	import open_invoices
	rep_output = request.POST.get('d_e')
	check = 'No'
	if request.user.is_authenticated:
		email = request.user.email
		fname = request.user.first_name
	open_invoices.open_invoices(rep_output, check, email, fname)
	messages.success(request, "Report Created Successfully")
	return redirect('home')

@login_required
def open_invoices_report(request):
    
    today = date.today()
    properties_with_invoices = []
    
    # Get all current tenants with their property details
    current_tenants = tenant.objects.filter(
        tenant_current='Yes'
    ).select_related('prop').order_by('prop__prop_country', 'prop__prop_name')
    
    # Get all unpaid invoices with tenant details in one query
    unpaid_invoices = invoices.objects.filter(
        invoice_paid='No'
    ).select_related('tenant', 'tenant__prop').order_by('invoice_date')
    
    # Process detailed invoice breakdown
    for tenant_obj in current_tenants:
        tenant_invoices = []
        
        # Get unpaid invoices for this tenant
        tenant_unpaid_invoices = [inv for inv in unpaid_invoices if inv.tenant.tenant_id == tenant_obj.tenant_id]
        
        for invoice_obj in tenant_unpaid_invoices:
            payment_terms = tenant_obj.tenant_payment_terms or 0
            due_date = invoice_obj.invoice_date + timedelta(days=payment_terms)
            days_overdue = (today - due_date).days if today > due_date else 0
            
            tenant_invoices.append({
                'invoice_id': invoice_obj.invoice_id,
                'invoice_date': invoice_obj.invoice_date.strftime('%Y-%m-%d'),
                'due_date': due_date.strftime('%Y-%m-%d'),
                'days_overdue': days_overdue,
                'overdue': days_overdue > 0
            })
        
        # Only include tenants with unpaid invoices
        if tenant_invoices:
            properties_with_invoices.append({
                'prop_name': tenant_obj.prop.prop_name,
                'prop_country': tenant_obj.prop.prop_country,
                'tenant_id': tenant_obj.tenant_id,
                'tenant_name': tenant_obj.tenant_name,
                'tenant_contact_person': tenant_obj.tenant_contact_person,
                'tenant_contact_number': tenant_obj.tenant_contact_number,
                'tenant_email': tenant_obj.tenant_email,
                'tenant_rent': tenant_obj.tenant_rent,
                'tenant_payment_terms': tenant_obj.tenant_payment_terms,
                'invoices': tenant_invoices
            })
    
    # Calculate Debtors Age Analysis
    debtors_age_analysis = []
    totals = {
        'total_outstanding': 0,
        'current_0_30': 0,
        'past_due_31_60': 0,
        'past_due_61_90': 0,
        'past_due_91_plus': 0
    }
    
    for tenant_obj in current_tenants:
        tenant_analysis = {
            'tenant_name': tenant_obj.tenant_name,
            'tenant_id': tenant_obj.tenant_id,  # Add tenant_id here too
            'total_outstanding': 0,
            'current_0_30': 0,
            'past_due_31_60': 0,
            'past_due_61_90': 0,
            'past_due_91_plus': 0
        }
        
        # Get unpaid invoices for this tenant
        tenant_unpaid_invoices = [inv for inv in unpaid_invoices if inv.tenant.tenant_id == tenant_obj.tenant_id]
        
        # Calculate aging for this tenant's invoices
        for invoice_obj in tenant_unpaid_invoices:
            payment_terms = tenant_obj.tenant_payment_terms or 0
            due_date = invoice_obj.invoice_date + timedelta(days=payment_terms)
            days_overdue = (today - due_date).days if today > due_date else 0
            amount = float(tenant_obj.tenant_rent or 0)
            
            tenant_analysis['total_outstanding'] += amount
            
            if days_overdue <= 30:
                # Current (0-30 days - includes not yet due and up to 30 days overdue)
                tenant_analysis['current_0_30'] += amount
            elif 31 <= days_overdue <= 60:
                # Past due 31-60 days
                tenant_analysis['past_due_31_60'] += amount
            elif 61 <= days_overdue <= 90:
                # Past due 61-90 days
                tenant_analysis['past_due_61_90'] += amount
            else:
                # Past due 91+ days
                tenant_analysis['past_due_91_plus'] += amount
        
        # Only include tenants with outstanding invoices
        if tenant_analysis['total_outstanding'] > 0:
            debtors_age_analysis.append(tenant_analysis)
            
            # Add to totals
            totals['total_outstanding'] += tenant_analysis['total_outstanding']
            totals['current_0_30'] += tenant_analysis['current_0_30']
            totals['past_due_31_60'] += tenant_analysis['past_due_31_60']
            totals['past_due_61_90'] += tenant_analysis['past_due_61_90']
            totals['past_due_91_plus'] += tenant_analysis['past_due_91_plus']
    
    # Sort debtors by total outstanding (highest first)
    debtors_age_analysis.sort(key=lambda x: x['total_outstanding'], reverse=True)

    context = {
        'today': today.strftime('%Y-%m-%d'),
        'properties_with_invoices': properties_with_invoices,
        'debtors_age_analysis': debtors_age_analysis,
        'totals': totals
    }
    
    return render(request, 'open_invoices_report.html', context)

@login_required
def lease_renewal_report(request):
    
    today = date.today()
    tenants_for_renewal = []
    vacant_properties = []
    declined_renewals = []
    
    # Get all active tenants with their property details using select_related for efficiency
    active_tenants = tenant.objects.filter(
        tenant_current='Yes'
    ).select_related('prop').order_by('prop__prop_country', 'prop__prop_name')
    
    # Get list of property names that have active tenants
    prop_active_tenant = list(active_tenants.values_list('prop__prop_name', flat=True))
    
    # Get all active properties available for rent
    active_properties = props.objects.filter(
        prop_status='Active',
        prop_available_for_rent='Yes'
    ).order_by('prop_country', 'prop_name')
    
    # Process each active tenant for renewal logic
    for tenant_obj in active_tenants:
        lease_end_date = tenant_obj.tenant_lease_end_date
        renewal_period = tenant_obj.tenant_renewal_period or 30  # Default to 30 days if None
        
        if lease_end_date:  # Make sure lease_end_date exists
            renewal_date = lease_end_date - timedelta(days=renewal_period)
            warning_date = renewal_date - timedelta(days=30)
            renewal_status = tenant_obj.tenant_renewal_status or 'pending'  # Default to pending
            
            if today >= warning_date:
                if renewal_status == 'pending':
                    # Normal renewal case - add to tenants list
                    tenants_for_renewal.append({
                        'prop_name': tenant_obj.prop.prop_name,
                        'prop_country': tenant_obj.prop.prop_country,
                        'tenant_type': tenant_obj.tenant_type,
                        'tenant_name': tenant_obj.tenant_name,
                        'tenant_contact_person': tenant_obj.tenant_contact_person,
                        'tenant_contact_number': tenant_obj.tenant_contact_number,
                        'tenant_email': tenant_obj.tenant_email,
                        'tenant_deposit': tenant_obj.tenant_deposit,
                        'tenant_lease_start_date': tenant_obj.tenant_lease_start_date.strftime('%Y-%m-%d') if tenant_obj.tenant_lease_start_date else '',
                        'tenant_lease_end_date': tenant_obj.tenant_lease_end_date.strftime('%Y-%m-%d') if tenant_obj.tenant_lease_end_date else '',
                        'tenant_rental_type': tenant_obj.tenant_rental_type,
                        'tenant_renewal': tenant_obj.tenant_renewal,
                        'tenant_renewal_period': tenant_obj.tenant_renewal_period,
                        'tenant_rent': tenant_obj.tenant_rent,
                        'tenant_levies': tenant_obj.tenant_levies,
                        'tenant_payment_terms': tenant_obj.tenant_payment_terms,
                        'renewal_date': renewal_date.strftime('%Y-%m-%d'),
                        'needs_renewal': True
                    })
                elif renewal_status == 'declined':
                    # Tenant declined renewal - add to declined_renewals list
                    declined_renewals.append({
                        'prop_name': tenant_obj.prop.prop_name,
                        'tenant_name': tenant_obj.tenant_name,
                        'lease_end_date': tenant_obj.tenant_lease_end_date.strftime('%Y-%m-%d') if tenant_obj.tenant_lease_end_date else '',
                        'message': 'CURRENT TENANT NOT RENEWING LEASE - NEED NEW TENANT'
                    })
                # If renewal_status == 'new_lease_signed', do nothing (exclude from report)
    
    # Find vacant properties (properties without active tenants)
    vacant_properties = []
    for prop in active_properties:
        if prop.prop_name not in prop_active_tenant:
            vacant_properties.append({
                'prop_name': prop.prop_name,
                'prop_country': prop.prop_country
            })
    
    context = {
        'tenants': tenants_for_renewal,
        'vacant_properties': vacant_properties,
        'declined_renewals': declined_renewals,
        'today': today.strftime('%Y-%m-%d')
    }
    return render(request, 'lease_renewal_report.html', context)

@login_required
def lease_renewal(request):
	import lease_renewal
	rep_output = request.POST.get('d_e')
	check = 'No'
	if request.user.is_authenticated:
		email = request.user.email
		fname = request.user.first_name
	lease_renewal.lease_renewal(rep_output, check, email, fname)
	messages.success(request, "Report Created Successfully")
	return redirect('home')


### USER ADMIN AND LOGIN AND LOGOUT ###
def login_user(request):
	if request.method =="POST":
	    username = request.POST["username"]
	    password = request.POST["password"]
	    user = authenticate(request, username=username, password=password)
	    if user is not None:
	        login(request, user)
	        messages.success(request, ('You Have Successfully Logged In.'))
	        return redirect('home')
	    else:
	        messages.success(request, ('Error Logging In - Please Try Again !!'))
	        return redirect('login')
	else:
		return render(request, 'login.html', {})

def logout_user(request):
    logout(request)
    messages.success(request, ('You Have Succefully Logged Out.'))
    return redirect('home')
