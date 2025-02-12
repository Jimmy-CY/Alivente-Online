from django.contrib import admin
from .models import props, petty, tenant, invoices, issues, issues_details, supplier

# Register your models here.
admin.site.register(props)
admin.site.register(petty)
admin.site.register(tenant)
admin.site.register(invoices)
admin.site.register(issues)
admin.site.register(issues_details)
admin.site.register(supplier)