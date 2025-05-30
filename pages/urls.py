from django.conf import settings
from django.conf.urls.static import static
from django.urls import path
from . import views

urlpatterns = [
    # Home
    path('', views.home, name='home'),
 
    #
    # User Admin
    path('login/', views.login_user, name='login'),
    path('logout/', views.logout_user, name='logout'),
    path('admin_apms/', views.admin_apms, name='admin_apms'),
    path('admin_clear/', views.admin_clear, name='admin_clear'),
    path('admin_unpaid/', views.admin_unpaid, name='admin_unpaid'),
    path('admin_renewals/', views.admin_renewals, name='admin_renewals'),
    path('admin_invoices/', views.admin_invoices, name='admin_invoices'),
    path('tenant/', views.tenant_page, name='tenant'),
    path('upload_title_deed/', views.upload_title_deed, name='upload_title_deed'),
#    path('upload_lease_agreement/', views.upload_lease_agreement, name='upload_lease_agreement'),
#    path('lease_agreement_report/<int:tenant_id>/', views.lease_agreement_report, name='lease_agreement_report'),
#    path('serve_lease/<str:filename>/', views.serve_lease, name='serve_lease'),
    path('lease/<int:tenant_id>/', views.lease_agreement_report, name='lease_agreement_report'),
    path('lease/<str:filename>/view/', views.serve_lease, name='serve_lease'),
    path('upload_lease_agreement/', views.upload_lease_agreement, name='upload_lease_agreement'),

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
    path('title_deed_report/<int:prop_id>', views.title_deed_report, name='title_deed_report'),
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

    #
    # Tenants
    path('tenant_add/', views.tenant_add, name='tenant_add'),
    path('tenant_edit/<tenant_id>', views.tenant_edit, name='tenant_edit'),
    path('tenant_edit_commit/<tenant_id>', views.tenant_edit_commit, name='tenant_edit_commit'),
    path('tenant_commit/', views.tenant_commit, name='tenant_commit'),
    
    #
    #Properties
    path('properties/', views.properties_page, name='properties'),
    path('properties_add/', views.properties_add, name='properties_add'),
    path('properties_edit/<prop_id>', views.properties_edit, name='properties_edit'),
    path('properties_commit/', views.properties_commit, name='properties_commit'),
    path('properties_edit_commit/<prop_id>', views.properties_edit_commit, name='properties_edit_commit'),
    
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
    
    #
    # Friday Status Report Capture
    path('fsr/', views.fsr, name='fsr'),
    path('fsr_add/', views.fsr_add, name='fsr_add'),
    path('fsr_commit/', views.fsr_commit, name='fsr_commit'),
    path('fsr_details/<issues_id>', views.fsr_details, name='fsr_details'),
    path('fsr_commit_status_change/', views.fsr_commit_status_change, name='fsr_commit_status_change'),
    path('fsr_comment_add/<issues_id>', views.fsr_comment_add, name='fsr_comment_add'),


    ] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)