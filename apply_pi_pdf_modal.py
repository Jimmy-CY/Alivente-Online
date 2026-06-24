# -*- coding: utf-8 -*-
"""
Apply: open the Physical Invoice PDF in the in-system modal (PDF.js viewer)
instead of a new browser tab.

Patches pages/templates/physical_invoice_list.html only:
  - desktop PDF link  : target="_blank"  ->  openPdfViewer(...) modal call
  - mobile  PDF link  : target="_blank"  ->  openPdfViewer(...) modal call
  - includes components/pdf_viewer.html before {% endblock %}

The modal's openPdfViewer(url, title, downloadFilename) decides PDF-vs-image
from the filename extension, so we pass "<PR#>.pdf" as the download filename
(the /pdf/ endpoint URL has no .pdf suffix). Tenant names are escapejs-guarded.

Fail-loud: every anchor must appear exactly once or nothing is written.
Reload the page afterwards (no Django restart needed for a template change).

Run from the repo root:  python apply_pi_pdf_modal.py
"""
import io
import os
import sys

TPL = os.path.join("pages", "templates", "physical_invoice_list.html")

EDITS = [
    # desktop PDF action
    ('''              <a href="{% url 'physical_invoice_pdf' row.pk %}" target="_blank" rel="noopener"
                 class="icon-action-btn icon-view" title="View invoice PDF">
                <i class="fas fa-file-pdf"></i>
              </a>''',
     '''              <a href="{% url 'physical_invoice_pdf' row.pk %}"
                 onclick="openPdfViewer('{% url 'physical_invoice_pdf' row.pk %}', 'Invoice {{ row.number|escapejs }} &mdash; {{ row.tenant|escapejs }}', '{{ row.number|escapejs }}.pdf'); return false;"
                 class="icon-action-btn icon-view" title="View invoice PDF">
                <i class="fas fa-file-pdf"></i>
              </a>'''),

    # mobile PDF action
    ('''              <a href="{% url 'physical_invoice_pdf' row.pk %}" target="_blank" rel="noopener"
                 class="mobile-action-btn">
                <i class="fas fa-file-pdf mobile-action-icon icon-color-view"></i>
                <span class="mobile-action-label">View PDF</span>
              </a>''',
     '''              <a href="{% url 'physical_invoice_pdf' row.pk %}"
                 onclick="openPdfViewer('{% url 'physical_invoice_pdf' row.pk %}', 'Invoice {{ row.number|escapejs }} &mdash; {{ row.tenant|escapejs }}', '{{ row.number|escapejs }}.pdf'); return false;"
                 class="mobile-action-btn">
                <i class="fas fa-file-pdf mobile-action-icon icon-color-view"></i>
                <span class="mobile-action-label">View PDF</span>
              </a>'''),

    # include the shared viewer component
    ('''});
</script>

{% endblock %}''',
     '''});
</script>

{% include 'components/pdf_viewer.html' %}

{% endblock %}'''),
]


def main():
    if not os.path.exists(TPL):
        sys.exit("ABORTED - missing file: %s" % TPL)
    with io.open(TPL, "r", encoding="utf-8") as fh:
        src = fh.read()

    problems = []
    for i, (old, _new) in enumerate(EDITS, 1):
        n = src.count(old)
        if n != 1:
            problems.append("  edit %d: anchor found %d time(s) (expected 1)" % (i, n))
    if problems:
        sys.exit("ABORTED - no changes written:\n" + "\n".join(problems))

    new_src = src
    for old, new in EDITS:
        new_src = new_src.replace(old, new, 1)

    with io.open(TPL + ".prebak", "w", encoding="utf-8", newline="") as fh:
        fh.write(src)
    with io.open(TPL, "w", encoding="utf-8", newline="") as fh:
        fh.write(new_src)
    print("OK: %s (backup %s.prebak)" % (TPL, TPL))
    print("done. reload the Physical Invoices page.")


if __name__ == "__main__":
    main()