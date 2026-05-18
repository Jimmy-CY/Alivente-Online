"""
Projects views for Alivente Online.

Extracted from pages/views/main.py as part of the modular split. One of
the larger sections: 17 view functions, a Google Translate helper, and
2 translation stubs.

Covers:
  - Project CRUD (projects_list, projects_add, projects_edit,
    projects_delete, projects_detail).
  - Task and subtask CRUD (project_tasks_*, project_subtasks_add).
  - Gantt chart rendering (project_gantt).
  - AJAX endpoints (ajax_update_project_status,
    ajax_update_task_status, ajax_duplicate_project, ajax_delete_task,
    project_task_list, get_project_assignees).
  - Translation utilities - both the temporarily-disabled persistent
    translation stubs (ensure_project_translations, get_translated_text)
    and the on-demand Google Translate AJAX endpoint (translate_text +
    translate_to_greek_service helper).

Known latent issues (preserved verbatim - only manifest when the
disabled persistent-translation path is re-enabled with language='greek'):
  - get_translated_text stub signature takes 2 args but project_task_list
    calls it with 3.
  - ensure_project_translations stub parameter is named 'request' but it
    is called with a project in project_task_list (harmless while the
    body is a no-op; matters once implemented).
"""

import json
import logging
from datetime import datetime, timedelta
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import F, Prefetch, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods, require_POST

from ..models import Project, ProjectDocument, ProjectTask, props

logger = logging.getLogger(__name__)


# --------------------------------------------------------------------------- #
# Translation service stubs (translation temporarily disabled)
# --------------------------------------------------------------------------- #
# from ..translation_service import ensure_project_translations, get_translated_text

def ensure_project_translations(request):
    pass


def get_translated_text(text, target_language='en'):
    return text


@login_required
@permission_required('auth.can_access_projects', raise_exception=True)
def projects_list(request):
    """Display list of projects with filtering and handle modal-based deletion"""

    # Handle POST request for modal-based deletion
    if request.method == 'POST' and 'delete_project_id' in request.POST:
        if not request.user.has_perm('auth.can_edit_projects'):
            messages.error(request, "You don't have permission to delete projects.")
            return redirect('projects')

        project_id = request.POST.get('delete_project_id')
        # Use select_related and prefetch_related for deletion
        project = get_object_or_404(
            Project.objects.select_related('prop').prefetch_related('projecttask_set', 'project_documents'),
            project_id=project_id
        )

        try:
            with transaction.atomic():
                logger.info(f"User {request.user.username} deleting project via modal: {project.project_name}")

                # Use prefetched data for counts (no additional queries)
                all_tasks = list(project.projecttask_set.all())
                main_task_count = sum(1 for task in all_tasks if task.parent_task is None)
                subtask_count = sum(1 for task in all_tasks if task.parent_task is not None)
                document_count = len(list(project.project_documents.all())) if hasattr(project, 'project_documents') else 0
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

    # Initialize filter variables from GET parameters FIRST
    search_query = request.GET.get('search', '').strip()
    selected_property = request.GET.get('property', '')
    selected_status = request.GET.get('status', '')

    # Build the base queryset WITHOUT prefetching unnecessary data
    # Only prefetch what's absolutely needed for the list view
    projects_queryset = Project.objects.select_related('prop')

    # Apply filters BEFORE any prefetching to reduce the dataset
    if search_query:
        projects_queryset = projects_queryset.filter(
            Q(project_name__icontains=search_query) |
            Q(project_description__icontains=search_query)
        )

    if selected_property:
        try:
            property_id = int(selected_property)
            projects_queryset = projects_queryset.filter(prop_id=property_id)
        except (ValueError, TypeError):
            selected_property = ""

    if selected_status:
        valid_statuses = [choice[0] for choice in Project.PROJECT_STATUS_CHOICES]
        if selected_status in valid_statuses:
            projects_queryset = projects_queryset.filter(project_status=selected_status)
        else:
            selected_status = ""

    # Apply ordering AFTER filtering
    projects_queryset = projects_queryset.order_by(F('project_start_date').desc(nulls_last=True))

    # REQUIRED: Template calls calculated methods that need task data
    # The template uses: get_calculated_status, get_progress_percentage,
    # get_calculated_start_date, get_calculated_expected_completion
    # Use comprehensive prefetching to load ALL related task data in minimal queries
    projects_queryset = projects_queryset.prefetch_related(
        Prefetch('projecttask_set',
            queryset=ProjectTask.objects.select_related().prefetch_related('subtasks')
        )
    )

    # If template only shows basic project info (name, description, dates, status),
    # then DON'T prefetch tasks at all

    # Single query for all properties (only if dropdown is used)
    properties = props.objects.only('prop_id', 'prop_name').order_by('prop_name')

    # Pagination with filter preservation
    paginator = Paginator(projects_queryset, 25)
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
@permission_required('auth.can_edit_projects', raise_exception=True)
def projects_add(request):
    """Add new project"""
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
            project = Project(
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
        'status_choices': Project.PROJECT_STATUS_CHOICES,
    }

    return render(request, 'projects/projects_add.html', context)


@login_required
@permission_required('auth.can_edit_projects', raise_exception=True)
def projects_edit(request, project_id):
    """Edit existing project - enhanced to handle Gantt chart returns"""
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

        # Add Greek translation fields
        project.project_name_greek = request.POST.get('project_name_greek', '').strip()
        project.project_description_greek = request.POST.get('project_description_greek', '').strip()

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
@permission_required('auth.can_edit_projects', raise_exception=True)
def projects_delete(request, project_id):
    """Delete project with enhanced cascade deletion and warnings"""

    # Single query with prefetching for counts
    project = get_object_or_404(
        Project.objects.select_related('prop').prefetch_related(
            'projecttask_set', 'project_documents'
        ),
        project_id=project_id
    )

    if request.method == 'POST':
        try:
            with transaction.atomic():
                logger.info(f"User {request.user.username} attempting to delete project: {project.project_name} (ID: {project_id})")

                # Use prefetched data for counts (no additional queries)
                all_tasks = list(project.projecttask_set.all())
                main_task_count = sum(1 for task in all_tasks if task.parent_task is None)
                subtask_count = sum(1 for task in all_tasks if task.parent_task is not None)
                total_task_count = len(all_tasks)
                document_count = len(list(project.project_documents.all())) if hasattr(project, 'project_documents') else 0

                project_name = project.project_name

                # Delete the project (this will cascade to delete all related tasks and subtasks)
                project.delete()

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
            logger.error(f"Error deleting project {project_id}: {str(e)}")
            messages.error(
                request,
                f"An error occurred while deleting the project '{project.project_name}'. Please try again or contact support."
            )
            return render(request, 'projects/projects_delete.html', {'project': project})

        return redirect('projects')

    # Use prefetched data for confirmation page (no additional queries)
    all_tasks = list(project.projecttask_set.all())
    main_tasks = [task for task in all_tasks if task.parent_task is None]
    subtasks = [task for task in all_tasks if task.parent_task is not None]
    documents = list(project.project_documents.all()) if hasattr(project, 'project_documents') else []

    context = {
        'project': project,
        'main_task_count': len(main_tasks),
        'subtask_count': len(subtasks),
        'document_count': len(documents),
        'main_tasks': main_tasks[:5],  # Show first 5 main tasks as examples
        'subtasks': subtasks[:10],     # Show first 10 subtasks as examples
        'documents': documents[:5],    # Show first 5 documents as examples
    }

    return render(request, 'projects/projects_delete.html', context)


@login_required
@permission_required('auth.can_access_projects', raise_exception=True)
def projects_detail(request, project_id):
    """Display project details with tasks and subtasks"""
    # Single query with comprehensive prefetching
    project = get_object_or_404(
        Project.objects.select_related('prop').prefetch_related(
            Prefetch('projecttask_set',
                queryset=ProjectTask.objects.filter(parent_task__isnull=True).prefetch_related(
                    Prefetch('subtasks', queryset=ProjectTask.objects.all())
                ).order_by('task_start_date', 'task_id')
            )
        ),
        project_id=project_id
    )

    # Use prefetched data (no additional queries)
    main_tasks = list(project.projecttask_set.all())  # These are already filtered and ordered

    context = {
        'project': project,
        'main_tasks': main_tasks,
        'task_status_choices': ProjectTask.TASK_STATUS_CHOICES,
        'task_priority_choices': ProjectTask.TASK_PRIORITY_CHOICES,
    }

    return render(request, 'projects/projects_detail.html', context)


@login_required
@permission_required('auth.can_edit_projects', raise_exception=True)
def project_tasks_add(request, project_id):
    """Add new task to project"""
    project = get_object_or_404(Project, project_id=project_id)

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
            task = ProjectTask(
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
        'task_status_choices': ProjectTask.TASK_STATUS_CHOICES,
        'task_priority_choices': ProjectTask.TASK_PRIORITY_CHOICES,
    }

    return render(request, 'projects/project_tasks_add.html', context)


@login_required
@permission_required('auth.can_edit_projects', raise_exception=True)
def project_tasks_edit(request, project_id, task_id):
    """
    Edit a project task or subtask with support for Greek language fields
    """
    project = get_object_or_404(Project, project_id=project_id)
    task = get_object_or_404(ProjectTask, task_id=task_id, project=project)

    # Check if coming from Gantt chart
    from_gantt = request.GET.get('from_gantt', False)

    if request.method == 'POST':
        try:
            # Update basic task fields (always editable)
            task.task_name = request.POST.get('task_name', '').strip()
            task.task_description = request.POST.get('task_description', '').strip()

            # Update Greek fields
            task.task_name_greek = request.POST.get('task_name_greek', '').strip()
            task.task_description_greek = request.POST.get('task_description_greek', '').strip()

            # Update priority (always editable)
            task.task_priority = request.POST.get('task_priority')

            # Handle different logic for main tasks vs subtasks
            if task.parent_task:  # This is a subtask - most fields are editable
                # Status is editable for subtasks
                task.task_status = request.POST.get('task_status')

                # Dates are editable for subtasks
                start_date = request.POST.get('task_start_date')
                if start_date:
                    task.task_start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
                else:
                    task.task_start_date = None

                expected_date = request.POST.get('task_expected_completion_date')
                if expected_date:
                    task.task_expected_completion_date = datetime.strptime(expected_date, '%Y-%m-%d').date()
                else:
                    task.task_expected_completion_date = None

                # Handle actual completion date (only for subtasks when status is Completed)
                actual_date = request.POST.get('task_actual_completion_date')
                if actual_date:
                    task.task_actual_completion_date = datetime.strptime(actual_date, '%Y-%m-%d').date()
                else:
                    task.task_actual_completion_date = None

                # Costs are editable for subtasks
                budgeted_cost = request.POST.get('task_budgeted_cost')
                if budgeted_cost:
                    task.task_budgeted_cost = Decimal(budgeted_cost)
                else:
                    task.task_budgeted_cost = Decimal('0.00')

                actual_cost = request.POST.get('task_actual_cost')
                if actual_cost:
                    task.task_actual_cost = Decimal(actual_cost)
                else:
                    task.task_actual_cost = Decimal('0.00')

                # Progress percentage is editable for subtasks
                progress = request.POST.get('task_progress_percentage')
                if progress:
                    task.task_progress_percentage = int(progress)
                else:
                    task.task_progress_percentage = 0

                # Assigned to is editable for subtasks
                task.task_assigned_to = request.POST.get('task_assigned_to', '').strip()

            else:  # This is a main task - most fields are auto-calculated
                # For main tasks, only basic info and priority are directly editable
                # Status, dates, and costs are calculated from subtasks
                # The model's calculation methods will handle the auto-calculation
                pass

            # Validate the task before saving
            task.full_clean()

            # Save the task
            task.save()

            # Success message
            if task.parent_task:
                messages.success(request, f'Subtask "{task.task_name}" updated successfully!')
            else:
                messages.success(request, f'Main task "{task.task_name}" updated successfully!')

            # Redirect based on where we came from
            if from_gantt:
                return redirect('project_gantt', project_id=project.project_id)
            else:
                return redirect('projects_detail', project_id=project.project_id)

        except ValidationError as e:
            # Handle Django model validation errors
            error_messages = []
            if hasattr(e, 'error_dict'):
                for field, errors in e.error_dict.items():
                    field_name = field.replace('_', ' ').title()
                    for error in errors:
                        error_messages.append(f"{field_name}: {error}")
            else:
                error_messages = e.messages if hasattr(e, 'messages') else [str(e)]

            for error_msg in error_messages:
                messages.error(request, error_msg)

        except ValueError as e:
            # Handle value conversion errors (dates, decimals, etc.)
            if 'time data' in str(e):
                messages.error(request, 'Invalid date format. Please use the date picker.')
            elif 'invalid literal' in str(e):
                messages.error(request, 'Invalid number format. Please enter valid numbers for costs and percentages.')
            else:
                messages.error(request, f'Invalid data: {str(e)}')

        except Exception as e:
            # Handle any other unexpected errors
            messages.error(request, f'Error updating task: {str(e)}')

    # Prepare context for the template
    context = {
        'project': project,
        'task': task,
        'task_status_choices': ProjectTask.TASK_STATUS_CHOICES,
        'task_priority_choices': ProjectTask.TASK_PRIORITY_CHOICES,
        'from_gantt': from_gantt,
    }

    return render(request, 'projects/project_tasks_edit.html', context)


@login_required
@permission_required('auth.can_edit_projects', raise_exception=True)
@require_http_methods(["POST"])
def translate_text(request):
    """
    Translate text using Google Translate API
    """
    try:
        data = json.loads(request.body)
        text = data.get('text', '').strip()
        target_language = data.get('target_language', 'greek')
        source_language = data.get('source_language', 'english')

        if not text:
            return JsonResponse({'success': False, 'error': 'No text provided'})

        # Use Google Translate service
        if target_language == 'greek':
            translated_text = translate_to_greek_service(text)
        else:
            translated_text = text

        return JsonResponse({
            'success': True,
            'translated_text': translated_text,
            'source_language': source_language,
            'target_language': target_language
        })

    except Exception as e:
        print(f"Translation view error: {e}")
        return JsonResponse({'success': False, 'error': str(e)})


def translate_to_greek_service(text):
    """
    Use Google Translate API to translate English text to Greek
    """
    try:
        # Lazy import: googletrans is an optional dependency; any failure
        # (including ImportError) falls back to returning the original text.
        from googletrans import Translator

        # Initialize Google Translator
        translator = Translator()

        # Translate from English to Greek
        result = translator.translate(text, dest='el', src='en')

        return result.text

    except Exception as e:
        print(f"Google Translation service error: {e}")
        return text  # Return original text if translation fails


@login_required
@permission_required('auth.can_edit_projects', raise_exception=True)
def project_tasks_delete(request, project_id, task_id):
    """Delete task"""
    project = get_object_or_404(Project, project_id=project_id)
    task = get_object_or_404(ProjectTask, task_id=task_id, project=project)
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
@permission_required('auth.can_edit_projects', raise_exception=True)
def project_subtasks_add(request, project_id, parent_task_id):
    """Add subtask to a main task"""
    project = get_object_or_404(Project, project_id=project_id)
    parent_task = get_object_or_404(ProjectTask, task_id=parent_task_id, project=project)

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
            subtask = ProjectTask(
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
        'task_status_choices': ProjectTask.TASK_STATUS_CHOICES,
        'task_priority_choices': ProjectTask.TASK_PRIORITY_CHOICES,
    }

    return render(request, 'projects/project_subtasks_add.html', context)


@login_required
@permission_required('auth.can_access_projects', raise_exception=True)
def project_gantt(request, project_id):
    """Display Gantt chart for project with tasks and subtasks"""
    # Single query with comprehensive prefetching
    project = get_object_or_404(
        Project.objects.select_related('prop').prefetch_related(
            Prefetch('projecttask_set',
                queryset=ProjectTask.objects.filter(parent_task__isnull=True).prefetch_related(
                    Prefetch('subtasks',
                        queryset=ProjectTask.objects.filter(
                            task_start_date__isnull=False,
                            task_expected_completion_date__isnull=False
                        ).order_by('task_start_date', 'task_id')
                    )
                ).order_by('task_start_date', 'task_id')
            )
        ),
        project_id=project_id
    )

    # Check if returning from edit page
    from_edit = request.GET.get('from_edit', False)
    if from_edit:
        messages.success(request, "Changes saved successfully. Gantt chart has been refreshed.")

    # Use prefetched data (no additional queries)
    main_tasks = list(project.projecttask_set.all())

    # Build Gantt data structure using prefetched data
    gantt_data = []

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

    # Add main tasks and their subtasks using prefetched data
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
                'progress': task.get_subtask_progress() / 100 if task.subtasks.all() else (1.0 if task.get_calculated_status() == 'Completed' else 0.0),
                'type': 'task',
                'status': task.get_calculated_status(),
                'budgeted_cost': float(task.get_calculated_budgeted_cost() or 0),
                'actual_cost': float(task.get_calculated_actual_cost() or 0),
                'assigned_to': task.task_assigned_to or '',
                'parent': f'project_{project.project_id}' if project_start and project_end else None,
                'open': True,
                'calculated_progress_percentage': round(task.get_subtask_progress(), 1)
            }
            gantt_data.append(task_item)

            # Add subtasks for this main task using prefetched data
            subtasks = list(task.subtasks.all())  # Already filtered in prefetch

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
                        'parent': f'task_{task.task_id}',
                        'priority': subtask.task_priority,
                        'progress_percentage': subtask.task_progress_percentage or 0
                    }
                    gantt_data.append(subtask_item)

    # If no tasks have dates, create a placeholder message
    if not gantt_data:
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
@permission_required('auth.can_edit_projects', raise_exception=True)
@require_POST
def ajax_update_project_status(request):
    """AJAX view to update project status"""
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


@login_required
@permission_required('auth.can_edit_projects', raise_exception=True)
@require_POST
def ajax_update_task_status(request):
    """AJAX view to update task status"""
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


@login_required
@permission_required('auth.can_edit_projects', raise_exception=True)
@require_POST
def ajax_duplicate_project(request):
    """
    AJAX view to duplicate a project with all its tasks and subtasks,
    adjusting all dates based on the new project start date and handling budget copy options
    """
    try:
        # Parse JSON data
        data = json.loads(request.body)
        project_id = data.get('project_id')
        new_project_name = data.get('new_project_name', '').strip()
        new_project_description = data.get('new_project_description', '').strip()
        new_project_start_date_str = data.get('new_project_start_date', '').strip()
        budget_copy_option = data.get('budget_copy_option', 'budgeted')
        clear_greek_translations = data.get('clear_greek_translations', False)

        # Validate required fields
        if not project_id or not new_project_name or not new_project_description or not new_project_start_date_str:
            return JsonResponse({
                'success': False,
                'message': 'Project ID, new project name, description, and start date are required'
            })

        # Validate budget copy option
        if budget_copy_option not in ['budgeted', 'actual']:
            budget_copy_option = 'budgeted'

        # Parse the new start date
        try:
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

        # Get the original project with comprehensive prefetching
        try:
            original_project = Project.objects.select_related('prop').prefetch_related(
                Prefetch('projecttask_set',
                    queryset=ProjectTask.objects.select_related().prefetch_related('subtasks')
                ),
                'project_documents'
            ).get(project_id=project_id)
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
                new_project_total_budgeted_cost = original_project.get_calculated_actual_cost()

            # Create new project
            new_project = Project.objects.create(
                project_name=new_project_name,
                project_description=new_project_description,
                prop=original_project.prop,
                project_start_date=new_project_start_date,
                project_expected_completion_date=new_project_expected_completion,
                project_status='Pending',
                project_actual_completion_date=None,
                project_total_budgeted_cost=new_project_total_budgeted_cost,
                project_total_actual_cost=Decimal('0.00'),
                project_name_greek=None if clear_greek_translations else getattr(original_project, 'project_name_greek', None),
                project_description_greek=None if clear_greek_translations else getattr(original_project, 'project_description_greek', None),
            )

            # Get all tasks using prefetched data
            all_original_tasks = list(original_project.projecttask_set.all())
            main_tasks = [task for task in all_original_tasks if task.parent_task_id is None]

            # Prepare bulk data for main tasks
            main_tasks_to_create = []
            task_id_mapping = {}  # Map old task ID to new task index

            # First pass: Prepare main tasks for bulk creation
            for original_task in main_tasks:
                new_task_start_date = adjust_date(original_task.task_start_date, date_offset)
                new_task_expected_completion = adjust_date(original_task.task_expected_completion_date, date_offset)
                new_task_budgeted_cost = get_cost_for_budget(original_task, budget_copy_option)

                new_task = ProjectTask(
                    project=new_project,
                    task_name=original_task.task_name,
                    task_description=original_task.task_description,
                    task_start_date=new_task_start_date,
                    task_expected_completion_date=new_task_expected_completion,
                    task_budgeted_cost=new_task_budgeted_cost,
                    task_actual_cost=Decimal('0.00'),
                    task_priority=original_task.task_priority,
                    task_status='Pending',
                    task_actual_completion_date=None,
                    task_assigned_to=original_task.task_assigned_to,
                    parent_task=None,
                    task_progress_percentage=0,
                    task_name_greek=getattr(original_task, 'task_name_greek', None),
                    task_description_greek=getattr(original_task, 'task_description_greek', None),
                )
                main_tasks_to_create.append(new_task)
                # Store mapping for later subtask creation
                task_id_mapping[original_task.task_id] = len(main_tasks_to_create) - 1

            # Bulk create main tasks
            created_main_tasks = ProjectTask.objects.bulk_create(main_tasks_to_create)

            # IMPORTANT: After bulk_create, we need to fetch the tasks with their IDs
            # because bulk_create doesn't populate the ID field on the returned objects
            created_main_tasks_with_ids = list(
                ProjectTask.objects.filter(
                    project=new_project,
                    parent_task__isnull=True
                ).order_by('task_id')
            )

            # Create mapping from original task ID to new task object (with ID)
            task_object_mapping = {}
            for i, original_task in enumerate(main_tasks):
                if i < len(created_main_tasks_with_ids):
                    task_object_mapping[original_task.task_id] = created_main_tasks_with_ids[i]

            # Prepare bulk data for subtasks
            subtasks_to_create = []

            # Get all subtasks using prefetched data and group by parent
            for original_main_task in main_tasks:
                # Use prefetched subtasks
                subtasks = list(original_main_task.subtasks.all())

                if original_main_task.task_id in task_object_mapping:
                    new_main_task = task_object_mapping[original_main_task.task_id]

                    for original_subtask in subtasks:
                        new_subtask_start_date = adjust_date(original_subtask.task_start_date, date_offset)
                        new_subtask_expected_completion = adjust_date(original_subtask.task_expected_completion_date, date_offset)
                        new_subtask_budgeted_cost = get_cost_for_budget(original_subtask, budget_copy_option)

                        new_subtask = ProjectTask(
                            project=new_project,
                            task_name=original_subtask.task_name,
                            task_description=original_subtask.task_description,
                            task_start_date=new_subtask_start_date,
                            task_expected_completion_date=new_subtask_expected_completion,
                            task_budgeted_cost=new_subtask_budgeted_cost,
                            task_actual_cost=Decimal('0.00'),
                            task_priority=original_subtask.task_priority,
                            task_status='Pending',
                            task_actual_completion_date=None,
                            task_assigned_to=original_subtask.task_assigned_to,
                            parent_task=new_main_task,
                            task_progress_percentage=0,
                            task_name_greek=getattr(original_subtask, 'task_name_greek', None),
                            task_description_greek=getattr(original_subtask, 'task_description_greek', None),
                        )
                        subtasks_to_create.append(new_subtask)

            # Bulk create subtasks
            if subtasks_to_create:
                ProjectTask.objects.bulk_create(subtasks_to_create)

            # Copy project documents using prefetched data
            documents_to_create = []
            try:
                original_documents = list(original_project.project_documents.all())
                for original_doc in original_documents:
                    new_document = ProjectDocument(
                        project=new_project,
                        task=None,
                        document_name=f"Copy of {original_doc.document_name}" if original_doc.document_name else None,
                        document_description=original_doc.document_description,
                        document_file=original_doc.document_file,
                        document_uploaded_by=request.user.username,
                    )
                    documents_to_create.append(new_document)

                # Bulk create documents
                if documents_to_create:
                    ProjectDocument.objects.bulk_create(documents_to_create)

            except Exception as doc_error:
                # Silent fail for document copying
                pass

        # Build success message
        budget_message = ""
        if budget_copy_option == 'actual':
            budget_message = " with actual costs copied as budgeted costs"
        else:
            budget_message = " with budgeted costs copied"

        translation_message = ""
        if clear_greek_translations:
            translation_message = " and Greek translations cleared for project name and description"

        success_message = f'Project "{new_project_name}" created successfully{budget_message}{translation_message}'
        if date_offset is not None:
            success_message += f' and all dates adjusted by {date_offset} days'

        return JsonResponse({
            'success': True,
            'message': success_message,
            'new_project_id': new_project.project_id,
            'date_offset': date_offset,
            'budget_copy_option': budget_copy_option,
            'greek_translations_cleared': clear_greek_translations
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
@permission_required('auth.can_access_projects', raise_exception=True)
def project_task_list(request, project_id):
    """Display task list for a specific project and assignee"""
    # Single query with comprehensive prefetching
    project = get_object_or_404(
        Project.objects.select_related('prop').prefetch_related(
            Prefetch('projecttask_set',
                queryset=ProjectTask.objects.filter(parent_task__isnull=True).prefetch_related(
                    'subtasks'
                ).order_by('task_start_date', 'task_id')
            )
        ),
        project_id=project_id
    )

    # Get parameters
    assigned_to = request.GET.get('assigned_to', '')
    language = request.GET.get('language', 'english')

    # Ensure Greek translations if language is Greek
    if language == 'greek':
        ensure_project_translations(project)

    # Use prefetched data
    main_tasks = list(project.projecttask_set.all())

    # Filter in Python using prefetched data instead of additional queries
    if assigned_to:
        filtered_main_tasks = []
        for task in main_tasks:
            task_matches = task.task_assigned_to == assigned_to
            subtask_matches = any(subtask.task_assigned_to == assigned_to for subtask in task.subtasks.all())
            if task_matches or subtask_matches:
                filtered_main_tasks.append(task)
        main_tasks = filtered_main_tasks

    # Build task list with hierarchy using prefetched data
    task_list = []
    total_tasks = 0
    completed_tasks = 0
    pending_tasks = 0

    # Add project as root item
    project_start_date = project.get_calculated_start_date()
    project_end_date = project.get_calculated_expected_completion()
    project_is_overdue = (
        project_end_date and
        project_end_date < timezone.now().date() and
        project.get_calculated_status() != 'Completed'
    )

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
        'start_date': project_start_date,
        'end_date': project_end_date,
        'priority': None,
        'indent_level': 0,
        'is_overdue': project_is_overdue,
        'project_obj': project
    }
    task_list.append(project_item)

    # Process main tasks and subtasks using prefetched data
    for main_task in main_tasks:
        # For main tasks, use calculated dates
        task_start_date = main_task.get_calculated_start_date()
        task_end_date = main_task.get_calculated_expected_completion()
        task_is_overdue = (
            task_end_date and
            task_end_date < timezone.now().date() and
            main_task.get_calculated_status() != 'Completed'
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
            'status': main_task.get_calculated_status(),
            'start_date': task_start_date,
            'end_date': task_end_date,
            'priority': main_task.task_priority,
            'indent_level': 1,
            'is_overdue': task_is_overdue,
            'task_obj': main_task
        }
        task_list.append(main_task_item)

        # Add subtasks using prefetched data
        subtasks = list(main_task.subtasks.all())
        if assigned_to:
            subtasks = [subtask for subtask in subtasks if subtask.task_assigned_to == assigned_to]

        # Sort subtasks by start date and task_id
        subtasks.sort(key=lambda x: (x.task_start_date or timezone.now().date(), x.task_id))

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
                'is_overdue': is_overdue,
                'task_obj': subtask
            }
            task_list.append(subtask_item)

            # ONLY count subtasks in totals
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
@permission_required('auth.can_edit_projects', raise_exception=True)
@require_POST
def ajax_delete_task(request):
    """
    AJAX view to delete a task or subtask
    """
    try:
        data = json.loads(request.body)
        task_id = data.get('task_id')
        task_type = data.get('task_type')  # 'task' or 'subtask'

        if not task_id:
            return JsonResponse({
                'success': False,
                'message': 'Task ID is required'
            })

        try:
            task_id = int(task_id)
        except (ValueError, TypeError):
            return JsonResponse({
                'success': False,
                'message': f'Invalid task ID: {task_id}'
            })

        # Get the task to delete
        try:
            task_to_delete = ProjectTask.objects.get(task_id=task_id)
        except ProjectTask.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': f'Task with ID {task_id} was not found'
            })

        # Use transaction to ensure all-or-nothing deletion
        with transaction.atomic():
            if task_type == 'task':
                # Delete main task and all its subtasks
                subtasks = ProjectTask.objects.filter(parent_task=task_to_delete)
                subtask_count = subtasks.count()

                # Delete subtasks first
                subtasks.delete()

                # Delete the main task
                task_name = task_to_delete.task_name
                task_to_delete.delete()

                message = f'Task "{task_name}" and {subtask_count} subtask(s) deleted successfully'

            elif task_type == 'subtask':
                # Delete only the subtask
                task_name = task_to_delete.task_name
                task_to_delete.delete()

                message = f'Subtask "{task_name}" deleted successfully'

            else:
                return JsonResponse({
                    'success': False,
                    'message': 'Invalid task type. Must be "task" or "subtask"'
                })

        return JsonResponse({
            'success': True,
            'message': message
        })

    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Invalid JSON data'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'An error occurred while deleting: {str(e)}'
        })


@login_required
@permission_required('auth.can_access_projects', raise_exception=True)
def get_project_assignees(request, project_id):
    """AJAX endpoint to get all assignees for a project"""
    # Single query with prefetching
    project = get_object_or_404(
        Project.objects.prefetch_related('projecttask_set'),
        project_id=project_id
    )

    # Use prefetched data to get assignees
    assignees = set()

    for task in project.projecttask_set.all():
        if task.task_assigned_to and task.task_assigned_to.strip():
            assignees.add(task.task_assigned_to.strip())

    # Convert to sorted list
    assignees_list = sorted(list(assignees))

    return JsonResponse({
        'success': True,
        'assignees': assignees_list,
        'project_name': project.project_name
    })