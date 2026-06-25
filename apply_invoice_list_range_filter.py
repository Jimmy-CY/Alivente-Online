# -*- coding: utf-8 -*-
"""
Apply: From/To month-range filter on the Physical Invoices list.

  pages/views/physical_invoices.py  (physical_invoice_list)
    ~ parse ?from= / ?to= (YYYY-MM); default both to the upcoming period (so the
      screen behaves as before until widened); swap if reversed
    ~ filter by an annotated period index (year*12 + month) BETWEEN the bounds,
      so ranges spanning a year boundary work; counts span the whole range
    ~ provisional tenant numbering only for a single-month range (empty otherwise)
    ~ context: from_value / to_value + a range-aware period_label

  pages/views/physical_invoices.py  (imports)
    + F, IntegerField, ExpressionWrapper from django.db.models

  pages/templates/physical_invoice_list.html
    ~ replace the single Month picker with From / To pickers
    ~ auto-submit includes both pickers

Dispenser panel and all other filters unchanged.

Fail-loud: every anchor must appear exactly once or nothing is written.
After running:  python manage.py check

Run from the repo root:  python apply_invoice_list_range_filter.py
"""
import ast
import io
import os
import sys

VIEWS = os.path.join("pages", "views", "physical_invoices.py")
LIST_TPL = os.path.join("pages", "templates", "physical_invoice_list.html")

# ----------------------------------------------------------------- views.py imports
V_IMP_OLD = "from django.db.models import ProtectedError"
V_IMP_NEW = "from django.db.models import ExpressionWrapper, F, IntegerField, ProtectedError"

# ----------------------------------------------------------------- views.py: head block
V_HEAD_OLD = '''    raw = (request.GET.get("period") or "").strip()
    period_first = None
    if raw:
        try:
            y, m = raw.split("-")
            period_first = date(int(y), int(m), 1)
        except (ValueError, TypeError):
            period_first = None
    if period_first is None:
        period_first = _upcoming_period()
    y, m = period_first.year, period_first.month

    base = PhysicalInvoice.objects.filter(period_year=y, period_month=m)
    counts = {
        "draft": base.filter(status=PhysicalInvoice.STATUS_DRAFT).count(),
        "approved": base.filter(status=PhysicalInvoice.STATUS_APPROVED).count(),
        "sent": base.filter(status=PhysicalInvoice.STATUS_SENT).count(),
    }'''
V_HEAD_NEW = '''    def _parse_ym(value):
        value = (value or "").strip()
        if not value:
            return None
        try:
            yy, mm = value.split("-")
            yy, mm = int(yy), int(mm)
            if 1 <= mm <= 12:
                return date(yy, mm, 1)
        except (ValueError, TypeError):
            pass
        return None

    # From / To month range. Default both to the upcoming period (single month),
    # so the screen behaves exactly as before until the range is widened.
    default_first = _upcoming_period()
    from_first = _parse_ym(request.GET.get("from")) or default_first
    to_first = _parse_ym(request.GET.get("to")) or from_first
    if to_first < from_first:
        from_first, to_first = to_first, from_first

    from_idx = from_first.year * 12 + from_first.month
    to_idx = to_first.year * 12 + to_first.month
    single_month = (from_idx == to_idx)
    y, m = from_first.year, from_first.month  # used for single-month provisional numbering

    base = PhysicalInvoice.objects.annotate(
        _pidx=ExpressionWrapper(F("period_year") * 12 + F("period_month"),
                                output_field=IntegerField())
    ).filter(_pidx__gte=from_idx, _pidx__lte=to_idx)
    counts = {
        "draft": base.filter(status=PhysicalInvoice.STATUS_DRAFT).count(),
        "approved": base.filter(status=PhysicalInvoice.STATUS_APPROVED).count(),
        "sent": base.filter(status=PhysicalInvoice.STATUS_SENT).count(),
    }'''

# ----------------------------------------------------------------- views.py: provisional
V_PROV_OLD = '''    provisional = preview_batch_numbers(
        y, m, statuses=(PhysicalInvoice.STATUS_DRAFT, PhysicalInvoice.STATUS_APPROVED))'''
V_PROV_NEW = '''    if single_month:
        provisional = preview_batch_numbers(
            y, m, statuses=(PhysicalInvoice.STATUS_DRAFT, PhysicalInvoice.STATUS_APPROVED))
    else:
        provisional = {}'''

# ----------------------------------------------------------------- views.py: context
V_CTX_OLD = '''        "period_value": f"{y:04d}-{m:02d}",
        "period_label": period_first.strftime("%B %Y"),'''
V_CTX_NEW = '''        "from_value": f"{from_first.year:04d}-{from_first.month:02d}",
        "to_value": f"{to_first.year:04d}-{to_first.month:02d}",
        "period_label": (from_first.strftime("%B %Y") if single_month
                         else from_first.strftime("%B %Y") + " \\u2013 " + to_first.strftime("%B %Y")),'''

# ----------------------------------------------------------------- template: From/To pickers
T_MONTH_OLD = '''          <div class="filter-group">
            <label class="filter-label"><i class="fas fa-calendar-alt"></i> Month</label>
            <input type="month" name="period" value="{{ period_value }}"
                   class="form-control filter-input" id="periodInput">
          </div>'''
T_MONTH_NEW = '''          <div class="filter-group">
            <label class="filter-label"><i class="fas fa-calendar-alt"></i> From</label>
            <input type="month" name="from" value="{{ from_value }}"
                   class="form-control filter-input" id="fromInput">
          </div>
          <div class="filter-group">
            <label class="filter-label"><i class="fas fa-calendar-alt"></i> To</label>
            <input type="month" name="to" value="{{ to_value }}"
                   class="form-control filter-input" id="toInput">
          </div>'''

# ----------------------------------------------------------------- template: auto-submit JS
T_JS_OLD = "['periodInput', 'statusSelect', 'typeSelect'].forEach(function (id) {"
T_JS_NEW = "['fromInput', 'toInput', 'statusSelect', 'typeSelect'].forEach(function (id) {"


T_GRID_OLD = '.filter-grid { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 20px; align-items: end; }'
T_GRID_NEW = '.filter-grid { display: grid; grid-template-columns: 1fr 1fr 1fr 1fr; gap: 20px; align-items: end; }'


def _load(path):
    if not os.path.exists(path):
        return None
    with io.open(path, "r", encoding="utf-8") as fh:
        return fh.read()


def main():
    targets = {
        VIEWS: [(V_IMP_OLD, V_IMP_NEW), (V_HEAD_OLD, V_HEAD_NEW),
                (V_PROV_OLD, V_PROV_NEW), (V_CTX_OLD, V_CTX_NEW)],
        LIST_TPL: [(T_MONTH_OLD, T_MONTH_NEW), (T_JS_OLD, T_JS_NEW),
                   (T_GRID_OLD, T_GRID_NEW)],
    }

    srcs, problems = {}, []
    for path, edits in targets.items():
        src = _load(path)
        if src is None:
            problems.append("  MISSING FILE: %s" % path)
            continue
        srcs[path] = src
        for i, (old, _new) in enumerate(edits, 1):
            n = src.count(old)
            if n != 1:
                problems.append("  %s edit %d: anchor found %d time(s) (expected 1)" % (path, i, n))
    if problems:
        sys.exit("ABORTED - no changes written:\n" + "\n".join(problems))

    results = []
    for path, edits in targets.items():
        new_src = srcs[path]
        for old, new in edits:
            new_src = new_src.replace(old, new, 1)
        if path.endswith(".py"):
            try:
                ast.parse(new_src)
            except SyntaxError as e:
                sys.exit("ABORTED - %s does not parse: %s" % (path, e))
        results.append((path, srcs[path], new_src))

    for path, src, new_src in results:
        with io.open(path + ".prebak", "w", encoding="utf-8", newline="") as fh:
            fh.write(src)
        with io.open(path, "w", encoding="utf-8", newline="") as fh:
            fh.write(new_src)
        print("OK: %s (backup %s.prebak)" % (path, path))

    print("done. next: python manage.py check")


if __name__ == "__main__":
    main()