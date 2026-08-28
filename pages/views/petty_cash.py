"""
Petty cash views.

Extracted from the legacy pages/views/main.py during the modular views
split. Covers the simple cash-ledger pages and the report generator.

Functions
---------
- petty_cash        : Ledger list with running balance.
- petty_cash_commit : POST adds a transaction (PettyForm), then
                      re-renders the ledger.
- petty_cash_add    : Renders the add-transaction page.
- petty_cash_rep    : Generates/e-mails the petty-cash report via the
                      project-root petty_cash.py helper, then redirects
                      home.

Auth tiers
----------
read tier -> auth.can_access_petty_cash   (petty_cash, petty_cash_rep)
edit tier -> auth.can_edit_petty_cash     (petty_cash_commit, petty_cash_add)
"""

from datetime import date
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import redirect, render

from ..forms import PettyForm
from ..models import petty


# Stands in for a missing date when the ledger is sorted; see the foot of
# _petty_ledger. Never displayed - the row still shows its own blank date.
_EPOCH = date.min


def _petty_ledger():
    """The ledger rows, newest first, and the balance they add up to.

    ONE QUERY. The view used to run two - `petty.objects.all()` for the rows
    and `petty.objects.values()` for the balance - and loop the second in
    Python. Two reads of the same table for one page, and a balance that could
    in principle disagree with the rows beside it. It cannot now: the figure
    is summed from the rows being drawn.

    NEWEST FIRST, decided here. The view ordered ascending and the template
    then re-sorted with `dictsortreversed` twice; one of those was always
    doing nothing. A list has one order and the view is where it belongs.

    `DR` is money in, `CR` is money out - the model's own convention, kept.
    """
    rows, balance = [], Decimal('0')
    for r in petty.objects.all():
        amount = r.petty_cash_amount or Decimal('0')
        income = (r.petty_cash_dr_cr == 'DR')
        balance += amount if income else -amount
        rows.append({
            'pk': r.petty_cash_id,
            'date': r.petty_cash_date,
            'description': r.petty_cash_description,
            'amount': amount,
            'is_income': income,
            # Income and Expense are CATEGORIES, not states. base's tag tones
            # are named for the colour precisely because they carry no
            # meaning, so nothing downstream reads good or bad into them -
            # unlike the pill scale, where a colour is a judgement.
            'tag': 'alv-tag-moss' if income else 'alv-tag-clay',
            'label': 'Income' if income else 'Expense',
        })
    # `petty_cash_date` is NULLABLE, and a None cannot be compared with a
    # date - the sort would raise. The old page had the same hole in a worse
    # place: `dictsortreversed` swallows the TypeError and returns an empty
    # string, so ONE undated row emptied the whole table. Undated rows sort
    # to the bottom here and the ledger still draws.
    rows.sort(key=lambda r: (r['date'] is not None, r['date'] or _EPOCH,
                             r['pk']), reverse=True)
    return rows, balance


@login_required
@permission_required('auth.can_access_petty_cash', raise_exception=True)
def petty_cash(request):
    rows, balance = _petty_ledger()
    return render(request, "petty_cash.html", {
        "rows": rows,
        "balance": balance,
        # The template must not have to decide what a negative balance means,
        # and `{% if balance < 0 %}` is not something a Django template can
        # say cleanly anyway.
        "is_overdrawn": balance < 0,
        "balance_display": abs(balance),
    })


@login_required
@permission_required('auth.can_edit_petty_cash', raise_exception=True)
def petty_cash_commit(request):
    if request.method == "POST":
        form = PettyForm(request.POST or None)
        if form.is_valid():
            form.save()
            messages.success(request, "Transaction Added Successfully")
    rows, balance = _petty_ledger()
    return render(request, "petty_cash.html", {
        "rows": rows,
        "balance": balance,
        # The template must not have to decide what a negative balance means,
        # and `{% if balance < 0 %}` is not something a Django template can
        # say cleanly anyway.
        "is_overdrawn": balance < 0,
        "balance_display": abs(balance),
    })


@login_required
@permission_required('auth.can_edit_petty_cash', raise_exception=True)
def petty_cash_add(request):
    presults = petty.objects.all().order_by('petty_cash_date')
    return render(request, "petty_cash_add.html", {"petty": presults})


@login_required
@permission_required('auth.can_access_petty_cash', raise_exception=True)
def petty_cash_rep(request):
    # Deliberate inline import (do NOT hoist): this resolves to the
    # project-root petty_cash.py reporting helper, NOT this views module.
    # Python's absolute import finds it via sys.path (the project root),
    # so the name stays unambiguous even though this file is also named
    # petty_cash.py. Kept inline to make that resolution explicit and local.
    import petty_cash
    rep_output = request.POST.get('d_e')
    # @login_required guarantees an authenticated user here, so email/fname
    # are always available (the former `if request.user.is_authenticated`
    # guard was always true and left these statically unbound-looking).
    email = request.user.email
    fname = request.user.first_name
    petty_cash.petty_cash(rep_output, email, fname)
    messages.success(request, "Report Created Successfully")
    return redirect('home')