from django.contrib import admin
from .models import props, petty, tenant, invoices, issues, issues_details, supplier, prop_values, revenue_types, revenue_line_types, revenue, expense_types, expense_line_types, expense, act_expense

# Register your models here.
admin.site.register(props)
admin.site.register(petty)
admin.site.register(tenant)
admin.site.register(invoices)
admin.site.register(issues)
admin.site.register(issues_details)
admin.site.register(supplier)
admin.site.register(prop_values)
admin.site.register(revenue_types)
admin.site.register(revenue_line_types)
admin.site.register(revenue)
admin.site.register(expense_types)
admin.site.register(expense_line_types)
admin.site.register(expense)
admin.site.register(act_expense)
