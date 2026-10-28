"""Alivente's own details, stored once - GL-1, 28 Oct 2026.

Every lease names the landlord. Before this round the Generate pop-up
prefilled the company registration number as HE123456 - a placeholder - and
the Greek template carried his passport number and its dates as literal text.
His figures of 28 October now live in one row (CompanyDetails), edited here
by a superuser, and the pop-up and the templates read them.

SUPERUSER ONLY, like Signature and Stamp beside it on Administration ->
System: a lease is a legal document and this is what it says about the
company.
"""
from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import redirect, render

from ..models import CompanyDetails

__all__ = [
    # __init__.py re-exports with `import *`, which obeys __all__ - RV-1's
    # lesson: a view missing from this list does not exist to the URLconf.
    'company_details',
]


class CompanyDetailsForm(forms.ModelForm):
    class Meta:
        model = CompanyDetails
        fields = ['company_name', 'registration_number', 'contact_person',
                  'phone', 'email', 'address', 'passport_number',
                  'passport_issued', 'passport_expires']

    def clean(self):
        data = super().clean()
        a, b = data.get('passport_issued'), data.get('passport_expires')
        if a and b and b <= a:
            self.add_error('passport_expires',
                           'The expiry date must come after the issue date.')
        return data


@login_required
@user_passes_test(lambda u: u.is_superuser)
def company_details(request):
    row = CompanyDetails.current()
    if request.method == 'POST':
        form = CompanyDetailsForm(request.POST, instance=row)
        if form.is_valid():
            saved = form.save(commit=False)
            saved.updated_by = request.user
            saved.save()
            messages.success(request, 'Company details saved. New leases '
                                      'use them from now on.')
            return redirect('company_details')
    else:
        form = CompanyDetailsForm(instance=row)
    return render(request, 'company_details.html', {
        'form': form, 'row': row,
        'expires_soon': row.passport_expires_soon(),
    })
