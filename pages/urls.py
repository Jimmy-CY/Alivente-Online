from django.urls import path
from . import views

urlpatterns = [
    # Home
    path('', views.home, name='home'),
    path('month_select/', views.month_select_view, name='month_select'),
 
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


    ]