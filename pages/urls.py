from django.conf import settings
from django.conf.urls.static import static
from django.urls import path
from . import views
from .views_setup import setup_permissions


urlpatterns = [
    # Home
    path('', views.home, name='home'),

    #
    # User Admin
    path('login/', views.login_user, name='login'),
    path('logout/', views.logout_user, name='logout'),
    path('admin_apms/', views.admin_apms, name='admin_apms'),
    path('personal/', views.personal_page, name='personal_page'),
    path('admin_clear/', views.admin_clear, name='admin_clear'),
    path('admin_unpaid/', views.admin_unpaid, name='admin_unpaid'),
    path('admin_renewals/', views.admin_renewals, name='admin_renewals'),
    path('admin_invoices/', views.admin_invoices, name='admin_invoices'),
    path('upload_title_deed/', views.upload_title_deed, name='upload_title_deed'),
#    path('upload_lease_agreement/', views.upload_lease_agreement, name='upload_lease_agreement'),
#    path('lease_agreement_report/<int:tenant_id>/', views.lease_agreement_report, name='lease_agreement_report'),
#    path('serve_lease/<str:filename>/', views.serve_lease, name='serve_lease'),
    path('lease/<int:tenant_id>/', views.lease_agreement_report, name='lease_agreement_report'),
    path('lease/<str:filename>/view/', views.serve_lease, name='serve_lease'),
    path('upload_lease_agreement/', views.upload_lease_agreement, name='upload_lease_agreement'),
    path('setup-permissions/', setup_permissions, name='setup_permissions'),  # Now properly imported
    path('user-administration/', views.user_administration, name='user_administration'),
    path('user-administration/add/', views.user_add, name='user_add'),
    path('user-administration/<int:user_id>/edit/', views.user_edit, name='user_edit'),
    path('user-administration/<int:user_id>/permissions/', views.user_permissions, name='user_permissions'),
    path('user-administration/<int:user_id>/delete/', views.user_delete, name='user_delete'),
    path('my-profile/', views.my_profile, name='my_profile'),

    #
    #Reports - Dashboard
    path('title_deeds/', views.title_deeds, name='title_deeds'),
    path('prop_rep/', views.prop_rep, name='prop_rep'),
    path('tenant_rep/', views.tenant_rep, name='tenant_rep'),
    path('suppliers_rep/', views.suppliers_rep, name='suppliers_rep'),
    path('fsr_rep/', views.fsr_rep, name='fsr_rep'),
    path('petty_cash_rep/', views.petty_cash_rep, name='petty_cash_rep'),
    path('open_invoices/', views.open_invoices, name='open_invoices'),
    path('lease_renewal/', views.lease_renewal, name='lease_renewal'),
    path('lease_agreements/', views.lease_agreements, name='lease_agreements'),
    path('issues_rep/', views.issues_rep, name='issues_rep'),
    path('property/<int:prop_id>/title-deed/', views.title_deed_report, name='title_deed_report'),
#    path('lease_agreement_report/<int:tenant_id>', views.lease_agreement_report, name='lease_agreement_report'),
    path('property_report/<int:prop_id>', views.property_report, name='property_report'),
    path('supplier_report/<int:supplier_id>', views.supplier_report, name='supplier_report'),
    path('tenant_report/<int:tenant_id>', views.tenant_report, name='tenant_report'),
    path('lease_renewal_report/', views.lease_renewal_report, name='lease_renewal_report'),
    path('open_invoices_report/', views.open_invoices_report, name='open_invoices_report'),
    path('friday_status_report/', views.friday_status_report, name='friday_status_report'),
    path('resolved_issues_report/', views.resolved_issues_report, name='resolved_issues_report'),
    path('finance_pl/', views.finance_pl, name='finance_pl'),
    path('finance_pl_act/', views.finance_pl_act, name='finance_pl_act'),
    # Property Dashboard
    path('property_management_dashboard/', views.property_management_dashboard, name='property_management_dashboard'),
    path('property_detail/<int:property_id>/<str:box_type>/', views.property_detail, name='property_detail'),
    path('property/<int:property_id>/profit-loss/', views.dashboard_pl, name='dashboard_pl'),    
    # Occupancy Trends
    path('occupancy-trends/', views.occupancy_trends_view, name='occupancy_trends'),
    path('vacancy-management/', views.vacancy_management_view, name='vacancy_management'),

    #
    # Cash Flow
    path("forecast/", views.cashflow_forecast, name="cashflow_forecast"),
    #
    # Notifications
    path('notifications/', views.notifications_dashboard, name='notifications_dashboard'),
    #
    # Projects
    # Projects URLs
    path('projects/', views.projects_list, name='projects'),
    path('projects/add/', views.projects_add, name='projects_add'),
    path('projects/edit/<int:project_id>/', views.projects_edit, name='projects_edit'),
    path('projects/delete/<int:project_id>/', views.projects_delete, name='projects_delete'),
    path('projects/detail/<int:project_id>/', views.projects_detail, name='projects_detail'),
    path('projects/<int:project_id>/gantt/', views.project_gantt, name='project_gantt'),
    # Project Tasks URLs
    path('projects/<int:project_id>/tasks/add/', views.project_tasks_add, name='project_tasks_add'),
    path('projects/<int:project_id>/tasks/edit/<int:task_id>/', views.project_tasks_edit, name='project_tasks_edit'),
    path('projects/<int:project_id>/tasks/delete/<int:task_id>/', views.project_tasks_delete, name='project_tasks_delete'),
    # Project Subtasks URLs
    path('projects/<int:project_id>/tasks/<int:parent_task_id>/subtasks/add/', views.project_subtasks_add, name='project_subtasks_add'),
    # AJAX URLs for dynamic updates
    path('ajax/projects/update-status/', views.ajax_update_project_status, name='ajax_update_project_status'),
    path('ajax/tasks/update-status/', views.ajax_update_task_status, name='ajax_update_task_status'),
    path('projects/ajax/duplicate/', views.ajax_duplicate_project, name='ajax_duplicate_project'),    
    path('projects/<int:project_id>/assignees/', views.get_project_assignees, name='project_assignees'),
    path('projects/<int:project_id>/task-list/', views.project_task_list, name='project_task_list'),
    path('translate/', views.translate_text, name='translate_text'),
    path('projects/<int:project_id>/assignees/', views.get_project_assignees, name='get_project_assignees'),
    path('projects/ajax/delete-task/', views.ajax_delete_task, name='ajax_delete_task'),

    #
    # Finance
    path('finance/', views.finance, name='finance'),
    path('finance_valuations/', views.finance_valuations, name='finance_valuations'),
    path('finance_valuations_add/', views.finance_valuations_add, name='finance_valuations_add'),
    path('finance_valuations_commit/', views.finance_valuations_commit, name='finance_valuations_commit'),
    path('finance_valuations_edit/<int:prop_values_id>/', views.finance_valuations_edit, name='finance_valuations_edit'),
    path('finance_valuations_edit_commit/<int:prop_values_id>/', views.finance_valuations_edit_commit, name='finance_valuations_edit_commit'),
    path('finance_revenue/', views.finance_revenue, name='finance_revenue'),
    path('finance_revenue_add/', views.finance_revenue_add, name='finance_revenue_add'),
    path('finance_revenue_commit/', views.finance_revenue_commit, name='finance_revenue_commit'),
    path('finance_revenue_edit/<int:revenue_id>', views.finance_revenue_edit, name='finance_revenue_edit'),
    path('finance_revenue_edit_commit/<int:revenue_id>', views.finance_revenue_edit_commit, name='finance_revenue_edit_commit'),
    path('finance_expense/', views.finance_expense, name='finance_expense'),
    path('finance_expense_add/', views.finance_expense_add, name='finance_expense_add'),
    path('finance_expense_commit/', views.finance_expense_commit, name='finance_expense_commit'),
    path('finance_expense_edit/<int:expense_id>', views.finance_expense_edit, name='finance_expense_edit'),
    path('finance_expense_edit_commit/<int:expense_id>', views.finance_expense_edit_commit, name='finance_expense_edit_commit'),
    path('finance_revenue_types/', views.finance_revenue_types, name='finance_revenue_types'),
    path('finance_expense_types/', views.finance_expense_types, name='finance_expense_types'),
    path('finance_revenue_line_types/', views.finance_revenue_line_types, name='finance_revenue_line_types'),
    path('finance_expense_line_types/', views.finance_expense_line_types, name='finance_expense_line_types'),
    path('finance_revenue_line_types_add/', views.finance_revenue_line_types_add, name='finance_revenue_line_types_add'),
    path('finance_revenue_line_types_commit/', views.finance_revenue_line_types_commit, name='finance_revenue_line_types_commit'),
    path('finance_expense_line_types_add/', views.finance_expense_line_types_add, name='finance_expense_line_types_add'),
    path('finance_expense_line_types_commit/', views.finance_expense_line_types_commit, name='finance_expense_line_types_commit'),
    path('finance_expense_line_types_edit/<expense_line_types_id>', views.finance_expense_line_types_edit, name='finance_expense_line_types_edit'),
    path('finance_expense_line_types_edit_commit/<int:expense_line_types_id>', views.finance_expense_line_types_edit_commit, name='finance_expense_line_types_edit_commit'),
    path('finance/expense-line-types/check-expenses/<int:expense_line_type_id>/', views.check_expenses_for_line_type, name='check_expenses_for_line_type'),
    path('finance/expense-line-types/delete/<int:expense_line_type_id>/', views.delete_expense_line_type, name='delete_expense_line_type'),
    path('finance_revenue_line_types_edit/<revenue_line_types_id>', views.finance_revenue_line_types_edit, name='finance_revenue_line_types_edit'),
    path('finance_revenue_line_types_edit_commit/<int:revenue_line_types_id>', views.finance_revenue_line_types_edit_commit, name='finance_revenue_line_types_edit_commit'),
    path('finance_revenue_types_add/', views.finance_revenue_types_add, name='finance_revenue_types_add'),
    path('finance_revenue_types_commit/', views.finance_revenue_types_commit, name='finance_revenue_types_commit'),
    path('finance_expense_types_add/', views.finance_expense_types_add, name='finance_expense_types_add'),
    path('finance_expense_types_commit/', views.finance_expense_types_commit, name='finance_expense_types_commit'),
    path('finance_revenue_types_edit/<revenue_types_id>', views.finance_revenue_types_edit, name='finance_revenue_types_edit'),
    path('finance_revenue_types_edit_commit/<int:revenue_types_id>', views.finance_revenue_types_edit_commit, name='finance_revenue_types_edit_commit'),
    path('finance_expense_types_edit/<expense_types_id>', views.finance_expense_types_edit, name='finance_expense_types_edit'),
    path('finance_expense_types_edit_commit/<int:expense_types_id>', views.finance_expense_types_edit_commit, name='finance_expense_types_edit_commit'),
    path('revenue-details/', views.revenue_details_view, name='revenue_details_view'),
    path('budget-expense-details/', views.budget_expense_details_view, name='budget_expense_details_view'),
    path('total-expense-details/', views.total_expense_details_view, name='total_expense_details_view'),
    path('financial-indicators/', views.financial_indicators_view, name='financial_indicators'),
    path('finance/expense-line-types/preview-prorata-change/<int:expense_line_types_id>/',
         views.preview_prorata_amount_change,
         name='preview_prorata_amount_change'),
    path('finance/expense-line-types/edit-and-recalc/<int:expense_line_types_id>/',
         views.finance_expense_line_types_edit_and_recalc_commit,
         name='finance_expense_line_types_edit_and_recalc_commit'),
    path('finance/valuations/preview-change/<int:prop_values_id>/',
         views.preview_valuation_change,
         name='preview_valuation_change'),
    path('finance/valuations/edit-and-recalc/<int:prop_values_id>/',
         views.finance_valuations_edit_and_recalc_commit,
         name='finance_valuations_edit_and_recalc_commit'),
    
    #
    # Lease Agreement Generation
    path('generate-lease-agreement/', views.generate_lease_agreement_view, name='generate_lease_agreement'),
    path('get-property-tenant-data/', views.get_property_tenant_data, name='get_property_tenant_data'),

    #
    # Tenants
    path('tenant/', views.tenant_page, name='tenant'),
    path('tenant_add/', views.tenant_add, name='tenant_add'),
    path('tenant_edit/<tenant_id>', views.tenant_edit, name='tenant_edit'),
    path('tenant_edit_commit/<tenant_id>', views.tenant_edit_commit, name='tenant_edit_commit'),
    path('tenant_commit/', views.tenant_commit, name='tenant_commit'),
    path('tenant_lease_agreement/', views.tenant_lease_agreement, name='tenant_lease_agreement'),
    path('lease-timeline/', views.lease_timeline_view, name='lease_timeline'),
    path('tenant/duplicate/<int:tenant_id>/', views.duplicate_tenant_view, name='duplicate_tenant'),
    path('tenant/delete/<int:tenant_id>/', views.delete_tenant_view, name='delete_tenant'),

    #
    #Properties
    path('properties/', views.properties_page, name='properties'),
    path('properties_add/', views.properties_add, name='properties_add'),
    path('properties_edit/<prop_id>', views.properties_edit, name='properties_edit'),
    path('properties_commit/', views.properties_commit, name='properties_commit'),
    path('properties_edit_commit/<prop_id>', views.properties_edit_commit, name='properties_edit_commit'),
    path('properties_title_deed/', views.properties_title_deed, name='properties_title_deed'),
    path('properties/map/', views.properties_map_view, name='properties_map_view'),
    
    #
    # Petty Cash
    path('petty_cash/', views.petty_cash, name='petty_cash'),
    path('petty_cash_add/', views.petty_cash_add, name='petty_cash_add'),
    path('petty_cash_commit/', views.petty_cash_commit, name='petty_cash_commit'),

    #
    # Actual Expenses
    path('act_expense_all/', views.act_expense_all, name='act_expense_all'),
    path('act_expense_view/', views.act_expense_view, name='act_expense_view'),
    path('act_expense_add/', views.act_expense_add, name='act_expense_add'),
    path('act_expense_commit/', views.act_expense_commit, name='act_expense_commit'),
    path('act_expense_edit/<expense_id>', views.act_expense_edit, name='act_expense_edit'),
    path('act_expense_edit_commit/<expense_id>', views.act_expense_edit_commit, name='act_expense_edit_commit'),
    path('mark_approved/<expense_id>', views.mark_approved, name='mark_approved'),
    path('mark_paid/<expense_id>', views.mark_paid, name='mark_paid'),
    path('mark_deleted/<expense_id>', views.mark_deleted, name='mark_deleted'),
    path('act_expense_manage_document/', views.act_expense_manage_document, name='act_expense_manage_document'),
    path('get-expense-invoice/<str:expense_id>/', views.get_expense_invoice, name='get_expense_invoice'), 
    
    #
    # Invoices
    path('invoices/', views.invoices_page, name='invoices'),
    path('invoices_commit/<invoice_id>', views.invoices_commit, name='invoices_commit'),
    
    #
    # Suppliers
    path('suppliers/', views.suppliers, name='suppliers'),
    path('suppliers_add/', views.suppliers_add, name='suppliers_add'),
    path('suppliers_edit/<supplier_id>', views.suppliers_edit, name='suppliers_edit'),
    path('suppliers_commit/', views.suppliers_commit, name='suppliers_commit'),
    path('suppliers_edit_commit/<supplier_id>', views.suppliers_edit_commit, name='suppliers_edit_commit'),
    path('suppliers/delete/<int:supplier_id>/', views.suppliers_delete, name='suppliers_delete'),
    
    #
    # Friday Status Report Capture
    path('fsr/', views.fsr, name='fsr'),
    path('fsr_add/', views.fsr_add, name='fsr_add'),
    path('fsr_commit/', views.fsr_commit, name='fsr_commit'),
    path('fsr_details/<issues_id>', views.fsr_details, name='fsr_details'),
    path('fsr_commit_status_change/', views.fsr_commit_status_change, name='fsr_commit_status_change'),
    path('fsr_comment_add/<issues_id>', views.fsr_comment_add, name='fsr_comment_add'),
    path('fsr_notification/', views.fsr_notification, name='fsr_notification'),
    path('fsr/pdf/', views.fsr_pdf, name='fsr_pdf'),
    path('issues/delete/<int:issue_id>/', views.delete_issue, name='delete_issue'),
    path('comments-report/', views.comments_report, name='comments_report'),
    path('delete-comment/<int:comment_id>/', views.delete_comment, name='delete_comment'),
    path('issue-details/<int:issue_id>/', views.get_issue_details, name='get_issue_details'),

    #
    # Passports
    path('passport-management/', views.passport_management, name='passport_management'),

    #
    # Recipe Management URLs
    path('recipe_management/', views.recipe_management, name='recipe_management'),
    path('recipes/duplicate/<int:recipe_id>/', views.duplicate_recipe, name='duplicate_recipe'),
    path('view_recipe/<int:recipe_id>/', views.view_recipe, name='view_recipe'),
    path('create_recipe/', views.create_recipe, name='create_recipe'),
    path('recipe/<int:recipe_id>/edit/', views.edit_recipe, name='edit_recipe'),
    path('spell-check-instructions/', views.spell_check_instructions, name='spell_check_instructions'),
    path('ajax/add_recipe_course/', views.add_recipe_course, name='add_recipe_course'),
    path('ajax/add_recipe_category/', views.add_recipe_category, name='add_recipe_category'),
    path('ajax/add_recipe_ingredient/', views.add_recipe_ingredient, name='add_recipe_ingredient'),
    path('add-recipe-protein/', views.add_recipe_protein, name='add_recipe_protein'),
    path('import_recipe/', views.import_recipe, name='import_recipe'),
    path('preview_imported_recipe/<str:temp_id>/', views.preview_imported_recipe, name='preview_imported_recipe'),
    path('ajax/add_measurement/', views.add_measurement_ajax, name='add_measurement_ajax'),
    path('ajax/add_ingredient/', views.add_ingredient_ajax, name='add_ingredient_ajax'),
    path('ajax/add_preparation/', views.add_preparation_ajax, name='add_preparation_ajax'),
    path('recipe/send_shopping_list/', views.send_shopping_list, name='send_shopping_list'),
    path('recipe/generate_shopping_list/', views.generate_recipe_shopping_list, name='generate_recipe_shopping_list'),
    path('recipe/manage-document/', views.recipe_manage_document, name='recipe_manage_document'),
    path('recipe/book-detail/<int:recipe_id>/', views.recipe_book_detail, name='recipe_book_detail'),
    path('recipe/check-name/', views.recipe_check_name, name='recipe_check_name'),
    path('recipe/<int:recipe_id>/favourite/', views.toggle_recipe_favourite, name='toggle_recipe_favourite'),
    # Meal Planning URLs
    path('meal_plans/', views.meal_plans, name='meal_plans'),
    path('meal_plans/create/', views.create_meal_plan, name='create_meal_plan'),
    path('meal_plans/<int:meal_plan_id>/', views.view_meal_plan, name='view_meal_plan'),
    path('meal_plans/<int:meal_plan_id>/edit/', views.edit_meal_plan, name='edit_meal_plan'),
    path('meal_plans/<int:meal_plan_id>/duplicate/', views.duplicate_meal_plan, name='duplicate_meal_plan'),
    path('meal_plans/<int:meal_plan_id>/delete/', views.delete_meal_plan, name='delete_meal_plan'),
    path('meal_plans/<int:meal_plan_id>/shopping_list/', views.meal_plan_shopping_list, name='meal_plan_shopping_list'),
    path('meal_plans/send_shopping_list/', views.send_meal_plan_shopping_list, name='send_meal_plan_shopping_list'),
    path('meal_plans/calendar/', views.meal_plan_calendar, name='meal_plan_calendar'),
    path('meal_plans/add_recipe_to_day/', views.add_recipe_to_meal_plan_day, name='add_recipe_to_meal_plan_day'),
    path('meal_plans/remove_recipe/', views.remove_recipe_from_meal_plan, name='remove_recipe_from_meal_plan'),
    path('recipes/find-matching/', views.find_matching_recipes, name='find_matching_recipes'),
    path('save_unit_conversion/', views.save_unit_conversion, name='save_unit_conversion'),
    # Unit Conversion Management
    path('unit_conversions/', views.unit_conversions_management, name='unit_conversions_management'),
    path('unit_conversions/add/', views.add_conversion, name='add_conversion'),
    path('add_unit_conversion_manual/', views.add_unit_conversion_manual, name='add_unit_conversion_manual'),
    path('edit_unit_conversion/', views.edit_unit_conversion, name='edit_unit_conversion'),
    path('delete_unit_conversion/', views.delete_unit_conversion, name='delete_unit_conversion'),
    # Ingredient Base Unit Management
    path('ingredient_base_units/', views.ingredient_base_units_management, name='ingredient_base_units_management'),
    path('update_ingredient_base_unit/', views.update_ingredient_base_unit, name='update_ingredient_base_unit'),
    path('check-ingredient-usage/', views.check_ingredient_usage, name='check_ingredient_usage'),
    path('delete-ingredient/', views.delete_ingredient, name='delete_ingredient'),
    path('update-ingredient-full/', views.update_ingredient_full, name='update_ingredient_full'),
    path('categories-management/', views.categories_management, name='categories_management'),
    path('add-category/', views.add_category, name='add_category'),
    path('update-category/', views.update_category, name='update_category'),
    path('check-category-usage/', views.check_category_usage, name='check_category_usage'),
    path('delete-category/', views.delete_category, name='delete_category'),
    path('measurement-units-management/', views.measurement_units_management, name='measurement_units_management'),
    path('add-measurement-unit/', views.add_measurement_unit, name='add_measurement_unit'),
    path('update-measurement-unit/', views.update_measurement_unit, name='update_measurement_unit'),
    path('check-unit-usage/', views.check_unit_usage, name='check_unit_usage'),
    path('delete-measurement-unit/', views.delete_measurement_unit, name='delete_measurement_unit'),

    # Celebration Management
    path('celebrations/', views.celebration_dashboard, name='celebration_dashboard'),
    path('celebrations/contacts/', views.celebration_management, name='celebration_management'),
    path('celebrations/calendar/', views.celebration_calendar, name='celebration_calendar'),
    path('celebrations/import/', views.import_celebrations, name='import_celebrations'),

    path('notifications/settings/', views.notification_settings, name='notification_settings'),
    path('notifications/personal/', views.personal_notification_settings, name='personal_notification_settings'),
    path('celebrations/event/<int:event_id>/update-notifications/', views.update_event_notifications, name='update_event_notifications'),

    # Asset Management URLs
    path('properties/<int:prop_id>/assets/', views.property_assets, name='property_assets'),
    path('properties/<int:prop_id>/assets/add/', views.add_asset, name='add_asset'),
    path('assets/<int:asset_id>/', views.asset_detail, name='asset_detail'),
    path('assets/<int:asset_id>/edit/', views.edit_asset, name='edit_asset'),
    path('assets/<int:asset_id>/delete/', views.delete_asset, name='delete_asset'),

    # Maintenance URLs
    path('assets/<int:asset_id>/maintenance/add/', views.add_maintenance, name='add_maintenance'),
    path('maintenance/<int:maintenance_id>/delete/', views.delete_maintenance, name='delete_maintenance'),
    path('maintenance/<int:maintenance_id>/edit/', views.edit_maintenance, name='edit_maintenance'),

    # AJAX URLs
    path('ajax/category/<int:category_id>/subcategories/', views.get_subcategories, name='get_subcategories'),
    path('ajax/category/add/', views.add_category_ajax, name='add_category_ajax'),
    path('ajax/subcategory/add/', views.add_subcategory_ajax, name='add_subcategory_ajax'),
    path('ajax/supplier/add/', views.add_supplier_ajax, name='add_supplier_ajax'),

]