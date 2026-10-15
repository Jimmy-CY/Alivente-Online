# -*- coding: utf-8 -*-
"""apply_pdf_viewer.py - round PV-1, 15 Oct 2026.

THIS APPLICATION ALREADY HAS A DOCUMENT VIEWER. TWO PAGES WROTE THEIR OWN.

Demetri, on the live site: "why in the Invoice Document viewer different
without all the share buttons, etc. Compare this to Actual Expenses."

Because Actual Expenses includes components/pdf_viewer.html and the P&L
does not:

    components/pdf_viewer.html   PDF.js, page nav, zoom, Download always,
                                 Share on mobile via the Web Share API,
                                 image fallback, full-screen on phones
                                 -> 11 pages

    a hand-rolled iframe modal   Download + Close
                                 -> finance_pl_act, asset_detail

AND THE COMPONENT'S OWN HEADER SAYS WHY IT EXISTS: "Works on all browsers
and devices, including Android Chrome which doesn't support inline PDF
embedding natively." Both hand-rolled viewers are iframes. asset_detail
even apologises for itself in its own markup - "If the PDF does not
display, click here to open it in a new tab" - which is that sentence,
written as a user-facing excuse instead of fixed.


WHAT THE SURVEY FOUND THAT THE REQUEST DID NOT                     MEASURED
============================================================================

ONE - THE PHONE FOOTER. Both pages carry a blanket phone rule for modal
footers, and the shared viewer's footer is a modal footer, so both rules
reach it. The component's mobile footer is one row - a wide Share, then a
44px Download and a 44px Close - and the page rules overrule the widths.
Rendered at 390px with the real Bootstrap and jQuery fixtures:

    finance_pl_act   today  share  26px  download 364  close 364  = 754px
                     PV-1   share 260px  download  44  close  44  = 348px

    asset_detail     today  share 321px  download 321  close 321  = 963px
                            (and flex-direction: column-reverse - three
                             full-width buttons stacked)
                     PV-1   share 221px  download  44  close  44  = 309px

A 26px Share button, and 754px of controls on a 390px screen. Including
the component without this would have replaced a viewer that cannot render
a PDF on Android with one whose buttons do not fit on any phone.

    EXCLUDED, NOT OVERRULED. The fix is `:not()` on the PAGE's rule rather
    than a louder counter-rule in the component's favour. A counter-rule is
    a second thing to keep true; an exclusion simply stops the page rule
    reaching a component it was never written for. It also settles the
    specificity question rather than winning it: asset_detail's rule is
    `.modal-fullscreen-mobile .modal-footer .btn`, and the component's own
    dialog CARRIES .modal-fullscreen-mobile, so an override at equal weight
    would have been decided by source order - which is to say, by where the
    include happens to sit.

TWO - THE STACKING, AND A BUG ALREADY ON THE LIVE PAGE. The P&L opens its
viewer from INSIDE the drill-down modal. Measured:

    drill-down open      body modal-open   overflow hidden   scrolls: no
    viewer opened on it  stacks correctly, pdfViewerModal is topmost
    viewer closed        body ""           overflow visible  scrolls: YES

Bootstrap 4 strips modal-open from <body> when the INNER modal closes, so
the page scrolls behind a modal that is still open. That is true of the
hand-rolled viewer today - this round does not introduce it - and the
existing setTimeout scroll-restore is a partial workaround for the same
thing. Three lines on hidden.bs.modal fix it properly; measured after:
modal-open, overflow hidden, scrolls: no.

    AND THE STACKING IS BY DOM ORDER, NOT BY z-index. Both modals compute
    to 1050; the later one in the document wins. finance_pl_act had written
    `#invoiceViewerModal { z-index: 1060; }` to force it, which worked and
    hid the fact. So WHERE THE INCLUDE SITS IS LOAD-BEARING: it replaces
    the old modal in place, which is after the drill-down, and the suite
    pins that order rather than trusting it.

WHAT IS NOT TOUCHED, AND IS NAMED RATHER THAN LEFT INVISIBLE
--------------------------------------------------------------
  asset_detail's photoViewerModal   A different viewer for a different
                                    thing. Out of scope.
  34 pages loading a SECOND jQuery  asset_detail is one of them: base
                                    loads jquery-3.6.0 and so does the
                                    page. A real defect, a different
                                    round, and counted here so the number
                                    exists on the record.

See test_pdf_viewer.py.
"""
import os
import sys

import alv_tree

code_only = alv_tree.code_only

SUFFIX = '.bak_pdfview'
SUITE = 'test_pdf_viewer.py'
PS1 = 'Push-PendingChanges.ps1'
TREE = 'alv_tree.py'
ROUNDS = 'alv_rounds.py'
WD = 'test_waiting_down.py'
CO = 'test_code_only.py'
COMPONENT = 'components/pdf_viewer.html'
CHECK = False

PL = 'finance_pl_act.html'
AD = 'asset_detail.html'

N_PAGES = 2
N_VIEWERS_WAS, N_VIEWERS_NOW = 3, 1     # viewers in the application
N_INCLUDERS_WAS, N_INCLUDERS_NOW = 11, 13
N_DUP_JQUERY = 34                        # named, not fixed

CONVERTED_WAS, CONVERTED_NOW = 78, 79
ALIAS_WAS, ALIAS_NOW = 67, 69
ALIAS_P_WAS, ALIAS_P_NOW = 33, 34
ALIAS_S_WAS, ALIAS_S_NOW = 34, 35

INCLUDE = "{% include 'components/pdf_viewer.html' %}"

# ---------------------------------------------------------------------------
# finance_pl_act.html
# ---------------------------------------------------------------------------
# THE MODAL GOES, THE INCLUDE TAKES ITS PLACE. In place, deliberately: it
# sits immediately after #expenseDetailsModal, and the stacking is decided
# by document order.
PL_MODAL_WAS = """<!-- Invoice Viewer Modal -->
<div class="modal fade" id="invoiceViewerModal" tabindex="-1" aria-labelledby="invoiceViewerModalLabel" aria-hidden="true" data-backdrop="static">
    <div class="modal-dialog modal-lg">
        <div class="modal-content">
            <div class="modal-header alv-modal-head">
                <h5 class="modal-title" id="invoiceViewerModalLabel">Invoice Document</h5>
                <button type="button" class="close" data-dismiss="modal" aria-label="Close">
                    <span aria-hidden="true">&times;</span>
                </button>
            </div>
            <div class="modal-body" id="invoiceViewerContent" style="height: 75vh; overflow: hidden; padding: 10px;"></div>
            <div class="modal-footer">
                <a id="downloadInvoiceBtn" href="#" target="_blank" class="btn action-primary">Download</a>
                <button type="button" class="btn action-secondary" data-dismiss="modal">Close</button>
            </div>
        </div>
    </div>
</div>"""

PL_MODAL_NOW = """<!-- Invoice Viewer - PV-1, 15 Oct 2026.
     WAS a hand-rolled iframe modal. The application already had a document
     viewer on eleven other pages; this page and asset_detail each wrote
     their own, and the component exists precisely because an iframe cannot
     render a PDF inline on Android Chrome.

     THIS INCLUDE SITS WHERE THAT MODAL SAT, AND THAT MATTERS. The viewer
     opens from inside #expenseDetailsModal. Measured: both modals compute
     to z-index 1050 and the LATER ONE IN THE DOCUMENT wins, so the include
     must stay after the drill-down. The old `#invoiceViewerModal {
     z-index: 1060 }` forced it and hid that. test_pdf_viewer pins the
     order. -->
{% include 'components/pdf_viewer.html' %}"""

PL_CSS_WAS = """#invoiceViewerContent { background-color: var(--alv-surface); border-radius: 4px; }
#invoiceViewerContent iframe {
    width: 100%;
    height: 100%;
    border: none;
    border-radius: 4px;
}
#invoiceViewerContent img {
    max-width: 100%;
    height: auto;
    display: block;
    margin: 0 auto;
}

#expenseDetailsModal { z-index: 1050; }
#invoiceViewerModal { z-index: 1060; }"""

PL_CSS_NOW = """/* PV-1: the #invoiceViewerContent rules and #invoiceViewerModal's
   z-index went with the hand-rolled modal. The shared component brings its
   own, and the stacking is settled by document order - the include sits
   after #expenseDetailsModal. */
#expenseDetailsModal { z-index: 1050; }"""

PL_PHONE_FOOTER_WAS = """    .modal-footer {
        flex-shrink: 0;
        flex-direction: column-reverse;
        gap: 8px;
        padding: 12px 16px;
    }
    .modal-footer .btn {
        width: 100%;
        padding: 12px;
        margin: 0 !important;
        font-size: 15px;
        justify-content: center;
        display: flex;
    }

    #invoiceViewerContent {
        height: 100% !important;
    }"""

PL_PHONE_FOOTER_NOW = """    /* PV-1: EXCLUDED FROM THE SHARED VIEWER, not overruled for it.
       This page's footer rule is written for its own stacked modals. The
       shared viewer's footer is one row - a wide Share, a 44px Download
       and a 44px Close - and these two rules overrule all three widths.
       Rendered at 390px: share 26px, download 364, close 364, which is
       754px of controls on a 390px screen. Excluded: 260 / 44 / 44. */
    .modal-footer:not(.pdf-viewer-footer) {
        flex-shrink: 0;
        flex-direction: column-reverse;
        gap: 8px;
        padding: 12px 16px;
    }
    .modal-footer:not(.pdf-viewer-footer) .btn {
        width: 100%;
        padding: 12px;
        margin: 0 !important;
        font-size: 15px;
        justify-content: center;
        display: flex;
    }"""

PL_JS_WAS = """    function showInvoiceModalLikeExisting(documentUrl, documentName) {
        const invoiceViewer = document.getElementById('invoiceViewerContent');
        const downloadLink = document.getElementById('downloadInvoiceBtn');
        downloadLink.href = documentUrl;
        downloadLink.download = documentName;
        const extension = documentName.split('.').pop().toLowerCase();
        if (extension === 'pdf') {
            invoiceViewer.innerHTML = `
                <iframe src="${documentUrl}#toolbar=0&navpanes=0&scrollbar=0" width="100%" height="100%" style="border: none; display: block;"></iframe>
            `;
        } else if (['jpg', 'jpeg', 'png'].includes(extension)) {
            invoiceViewer.innerHTML = `<img src="${documentUrl}" alt="Invoice" class="img-fluid">`;
        } else {
            invoiceViewer.innerHTML = `
                <div class="text-center">
                    <i class="fas fa-file-alt fa-5x text-muted mb-3"></i>
                    <p>File: <strong>${documentName}</strong></p>
                    <p>Click Download to view.</p>
                </div>
            `;
        }
        $('#invoiceViewerModal').modal('show');
    }"""

PL_JS_NOW = """    // PV-1, 15 Oct 2026 - the component decides how a document is shown.
    // The extension sniffing, the iframe, the image branch and the
    // cannot-preview branch all lived here AND in asset_detail AND in the
    // component, three copies of one decision. The component's is the one
    // that handles a PDF on Android.
    function showInvoiceModalLikeExisting(documentUrl, documentName) {
        if (typeof openPdfViewer !== 'function') {
            window.open(documentUrl, '_blank');
            return;
        }
        openPdfViewer(documentUrl,
                      'Expense Invoice \\u2014 ' + documentName,
                      documentName);
    }"""

PL_HIDE_WAS = """    $('#invoiceViewerModal').on('hidden.bs.modal', function() {
        setTimeout(function() {
            $('#expenseDetailsModal .modal-body').scrollTop(firstModalScrollTop);
        }, 100);
    });"""

PL_HIDE_NOW = """    // PV-1: AND THE DRILL-DOWN STAYS A MODAL WHEN THE VIEWER CLOSES.
    // Bootstrap 4 strips modal-open from <body> when the INNER modal of a
    // stacked pair closes, so the page behind scrolls while a modal is
    // still open. Measured before: body "", overflow visible, page
    // scrolls. After: modal-open, overflow hidden, does not. This is not
    // new in this round - the hand-rolled viewer had it too, and the
    // scroll restore below is a partial workaround for the same thing.
    $('#pdfViewerModal').on('hidden.bs.modal', function() {
        if ($('.modal.show, .modal.in').length) {
            $('body').addClass('modal-open');
        }
        setTimeout(function() {
            $('#expenseDetailsModal .modal-body').scrollTop(firstModalScrollTop);
        }, 100);
    });"""

# ---------------------------------------------------------------------------
# asset_detail.html
# ---------------------------------------------------------------------------
AD_MODAL_WAS = """<div class="modal fade" id="invoiceViewerModal" tabindex="-1" role="dialog">
    <div class="modal-dialog modal-lg modal-fullscreen-mobile" role="document">
        <div class="modal-content">
            <div class="modal-header alv-modal-head">
                <h5 class="modal-title">Invoice / Receipt</h5>
                <button type="button" class="close" data-dismiss="modal">
                    <span>&times;</span>
                </button>
            </div>
            <div class="modal-body" id="invoiceViewerContent">
            </div>
            <div class="modal-footer">
                <a id="invoiceDownloadLink" href="#" class="btn action-primary" target="_blank">
                    <i class="fas fa-download"></i> Download
                </a>
                <button type="button" class="btn action-secondary" data-dismiss="modal">Close</button>
            </div>
        </div>
    </div>
</div>"""

AD_MODAL_NOW = """<!-- Invoice Viewer - PV-1, 15 Oct 2026. Was a hand-rolled iframe modal
     whose own markup apologised for it: "If the PDF does not display,
     click here to open it in a new tab." That sentence is the Android
     inline-PDF problem, written as an excuse rather than fixed, and it is
     the reason components/pdf_viewer.html exists. -->
{% include 'components/pdf_viewer.html' %}"""

AD_CSS_WAS = """    /* Invoice viewer modal — iframe goes 70vh */
    #invoiceViewerModal .modal-fullscreen-mobile iframe {
        height: 70vh !important;
    }
    #invoiceViewerModal .modal-fullscreen-mobile img {
        max-height: 70vh !important;
    }
"""

AD_CSS_NOW = """    /* PV-1: the #invoiceViewerModal iframe and img rules went with the
       hand-rolled modal. The shared component sizes its own body. */
"""

AD_PHONE_PAD_WAS = """    .modal-fullscreen-mobile .modal-header,
    .modal-fullscreen-mobile .modal-footer {
        padding: 12px 14px;
    }"""

AD_PHONE_PAD_NOW = """    .modal-fullscreen-mobile .modal-header,
    .modal-fullscreen-mobile:not(.pdf-viewer-modal-dialog) .modal-footer {
        padding: 12px 14px;
    }"""

AD_PHONE_FOOTER_WAS = """    /* Modal footer — stack buttons full-width with primary on top */
    .modal-fullscreen-mobile .modal-footer {
        flex-direction: column-reverse;
        gap: 8px;
        align-items: stretch;
    }
    .modal-fullscreen-mobile .modal-footer .btn {
        width: 100%;
        margin: 0 !important;
        padding: 12px;
    }"""

AD_PHONE_FOOTER_NOW = """    /* Modal footer — stack buttons full-width with primary on top.
       PV-1: EXCLUDED FROM THE SHARED VIEWER. Its dialog also carries
       .modal-fullscreen-mobile, so an override at equal weight would have
       been decided by where the include happens to sit. Rendered at 390px
       unexcluded: column-reverse, three 321px buttons stacked, 963px of
       controls. Excluded: one row, 221 / 44 / 44. */
    .modal-fullscreen-mobile:not(.pdf-viewer-modal-dialog) .modal-footer {
        flex-direction: column-reverse;
        gap: 8px;
        align-items: stretch;
    }
    .modal-fullscreen-mobile:not(.pdf-viewer-modal-dialog) .modal-footer .btn {
        width: 100%;
        margin: 0 !important;
        padding: 12px;
    }"""

AD_JS_WAS = """// View invoice in modal
function viewInvoice(url, filename) {
    const content = document.getElementById('invoiceViewerContent');
    const downloadLink = document.getElementById('invoiceDownloadLink');
    const ext = filename.split('.').pop().toLowerCase();

    downloadLink.href = url;

    if (ext === 'pdf') {
        content.innerHTML = `
            <iframe src="${url}#toolbar=0&navpanes=0&scrollbar=1"
                    width="100%" height="500px" style="border: none;">
            </iframe>
            <p class="text-center mt-2">
                <small>If the PDF does not display, <a href="${url}" target="_blank">click here to open it in a new tab</a></small>
            </p>`;
    } else if (['jpg', 'jpeg', 'png'].includes(ext)) {
        content.innerHTML = `<img src="${url}" alt="Invoice" class="img-fluid mx-auto d-block" style="max-height: 70vh;">`;
    } else {
        content.innerHTML = `
            <div class="text-center">
                <i class="fas fa-file fa-5x text-muted mb-3"></i>
                <p>This file type cannot be previewed.</p>
                <a href="${url}" target="_blank" class="btn action-primary">Open File</a>
            </div>`;
    }

    $('#invoiceViewerModal').modal('show');
}"""

AD_JS_NOW = """// View invoice in modal - PV-1, 15 Oct 2026.
// The three branches below (pdf / image / anything else) were the third
// copy of a decision the shared component already makes, and the only
// copy that told the user to open the file in another tab when the
// iframe failed. The component renders the PDF instead.
function viewInvoice(url, filename) {
    if (typeof openPdfViewer !== 'function') {
        window.open(url, '_blank');
        return;
    }
    const name = String(filename || '').split('/').pop() || 'invoice.pdf';
    openPdfViewer(url, 'Invoice / Receipt \\u2014 ' + name, name);
}"""

# ---------------------------------------------------------------------------
# the registers
# ---------------------------------------------------------------------------
TREE_WAS = """    'test_verb_colours.py',
]"""
TREE_NOW = """    'test_verb_colours.py',
    # PV-1, 15 Oct 2026 - two hand-rolled invoice viewers retired onto the
    # component eleven other pages already share. Demetri asked why the
    # P&L viewer had no Share button; the answer was that it was a second
    # implementation. Wide from birth.
    'test_pdf_viewer.py',
]"""

ROUNDS_WAS = """    '.bak_verbs',
]"""
ROUNDS_NOW = """    '.bak_verbs',
    # PV-1, 15 Oct 2026 - finance_pl_act and asset_detail include
    # components/pdf_viewer.html, and each page's blanket phone footer
    # rule is excluded from it rather than overruled.
    '.bak_pdfview',
]"""

SUITE_WAS = """    'test_verb_colours.py'
)"""
SUITE_NOW = """    'test_verb_colours.py',
    'test_pdf_viewer.py'
)"""

CLAIMS_ANCHOR = """    @{ File = 'alv_rowactions.py'; Text = 'VERNACULAR'; What = 'four controls no drift census could see are registered by verb' },"""

CLAIMS = """    @{ File = 'alv_rowactions.py'; Text = 'VERNACULAR'; What = 'four controls no drift census could see are registered by verb' },
    # ------------------------------------------------- PV-1, 15 Oct 2026
    # Demetri asked why the P&L's invoice viewer has no Share button. It
    # was a second implementation of a component eleven pages share.
    @{ File = 'pages\\templates\\finance_pl_act.html'; Text = "include 'components/pdf_viewer.html'"; What = 'the P&L drops its own invoice viewer for the one eleven pages share' },
    @{ File = 'pages\\templates\\asset_detail.html'; Text = "include 'components/pdf_viewer.html'"; What = 'and so does asset_detail, whose markup apologised for its iframe' },
    @{ File = 'pages\\templates\\finance_pl_act.html'; Text = ':not(.pdf-viewer-footer)'; What = 'the page phone footer rule stops reaching a component it never knew about' },
    @{ File = 'pages\\templates\\asset_detail.html'; Text = ':not(.pdf-viewer-modal-dialog)'; What = 'and 963px of buttons stop being laid out on a 390px screen' },"""


# ---------------------------------------------------------------------------
# THE TWO SUITES THIS ROUND MOVES
# ---------------------------------------------------------------------------
# RC-2 wrote the rule when it re-pointed test_amber: "A pinned COUNT moves
# when a later round owns part of it. A pinned DECISION does not move
# because a later round finds it inconvenient." Both of these are the first
# kind, and both are owed an update rather than a silence.
BH = 'test_bar_height.py'
BR = 'test_button_reach.py'
DR = 'test_drift_root.py'
DB = 'test_div_balance.py'
RT = 'test_recipe_tones.py'

# RS-1a's swept-side census. Two Close buttons and two Download primaries
# went with the viewers; the Cancels fall 57 -> 55 and the primaries
# 32 -> 30. The destructive count does not move, which is itself worth
# seeing: neither retired viewer had a Delete in it.
RT_WAS = 'SWEPT_CANCELS, SWEPT_DANGER, SWEPT_PRIMARY = 57, 14, 32'
RT_NOW = ('SWEPT_CANCELS, SWEPT_DANGER, SWEPT_PRIMARY = 55, 14, 30'
          '   # PV-1, 15 Oct 2026 - two hand-rolled invoice viewers'
          ' retired, each with a Close and a Download. The danger count'
          ' is unchanged: neither had a destructive button in it.'
          '   # (was 57, 14, 32)')

PI = 'test_pl_invoice.py'

# PL-1's suite is the one this round moves MOST, and none of it is a count.
# It builds a stub fixture, lifts the page's own functions out of the
# template and runs them against a real click. The claims it makes are all
# still right - the viewer opens, the download offers a file NAME and not a
# stored path, every glyph verify_badge can emit opens it - but the page no
# longer opens a modal itself. It hands the document to the component.
#
# SO THE CLAIMS ARE RE-POINTED AT THE HANDOFF, which is the page's actual
# contract now, and one of them changes shape rather than value: "in an
# iframe, because it is a PDF" was true and is now false BY DESIGN. PDF.js
# draws to a canvas precisely so that a PDF renders where an iframe cannot.
#
# THE LEGACY STUB STAYS. Section 4 is a historical control that re-runs an
# earlier round's handler against that round's markup; it needs the old ids
# or it reproduces a third state that never existed. The fixture carries
# both eras because it tests both.
PI_STUB_WAS = """window.firstModalScrollTop = 0;"""

PI_STUB_NOW = """window.firstModalScrollTop = 0;

// PV-1, 15 Oct 2026 - the component, stubbed. The page under test no
// longer builds a viewer; it calls openPdfViewer(url, title, filename).
// Recording the call is how this suite now asks whether the document was
// handed over, and WITH WHAT - which is a stronger question than the
// innerHTML of a div the page used to fill in itself.
window.__pdf = null;
window.openPdfViewer = function (url, title, filename) {
  window.__pdf = {url: url, title: title, filename: filename};
  $('#pdfViewerModal').modal('show');
};"""

PI_ROW_WAS = """            '<div id="invoiceViewerModal"><div id="invoiceViewerContent"></div>'
            '<a id="downloadInvoiceBtn"></a></div>' % (glyph, tone, url, name))"""

PI_ROW_NOW = """            # BOTH ERAS. The first three ids are what the page built
            # for itself before PV-1 and are kept for section 4, which
            # re-runs the old handler and needs the old markup.
            # #pdfViewerModal is the shared component's.
            '<div id="invoiceViewerModal"><div id="invoiceViewerContent"></div>'
            '<a id="downloadInvoiceBtn"></a></div>'
            '<div id="pdfViewerModal"></div>' % (glyph, tone, url, name))"""

PI_PROBE_WAS = """PROBE = \"\"\"() => ({
  viewer: document.getElementById('invoiceViewerContent').innerHTML,
  href: document.getElementById('downloadInvoiceBtn').getAttribute('href'),
  download: document.getElementById('downloadInvoiceBtn').getAttribute('download'),
  stub: window.__stub,
  errors: window.__errors})\"\"\""""

PI_PROBE_NOW = """PROBE = \"\"\"() => ({
  viewer: document.getElementById('invoiceViewerContent').innerHTML,
  href: document.getElementById('downloadInvoiceBtn').getAttribute('href'),
  download: document.getElementById('downloadInvoiceBtn').getAttribute('download'),
  pdf: window.__pdf,
  stub: window.__stub,
  errors: window.__errors})\"\"\""""

PI_CHECKS_WAS = """    check('THE VIEWER IS SHOWING THE DOCUMENT',
          '/media/invoices/2026/ATOM_304156.pdf' in (r['viewer'] or ''),
          (r['viewer'] or '')[:70])
    check('  in an iframe, because it is a PDF', '<iframe' in (r['viewer'] or ''))
    check('  and the modal was actually opened',
          any('invoiceViewerModal' in s for s in r['stub']['modalShown']),
          str(r['stub']['modalShown']))"""

PI_CHECKS_NOW = """    # PV-1, 15 Oct 2026 - THE SAME CLAIMS, ASKED OF THE HANDOFF.
    check('THE VIEWER IS SHOWING THE DOCUMENT',
          bool(r['pdf']) and r['pdf']['url']
          == '/media/invoices/2026/ATOM_304156.pdf', str(r['pdf']))
    # WAS: "in an iframe, because it is a PDF". That was true and is now
    # false BY DESIGN - PDF.js draws to a canvas precisely so a PDF
    # renders where an iframe cannot, which is why the component exists.
    check('  on the shared viewer, which draws a PDF rather than handing '
          'it to the browser',
          'pdfjsLib' in COMPONENT_SRC and 'pdfViewerCanvas' in COMPONENT_SRC)
    check('  and the viewer was actually opened',
          any('pdfViewerModal' in s for s in r['stub']['modalShown']),
          str(r['stub']['modalShown']))"""

PI_DL_WAS = """    check('the download offers the FILE NAME, not the stored path',
          r['download'] == 'ATOM_304156.pdf', str(r['download']))
    check('  and points at the document', r['href'] and r['href'].endswith('.pdf'),
          str(r['href']))"""

PI_DL_NOW = """    # THE SAME CLAIM, AND A BETTER TEST OF IT. This used to read the
    # download attribute off a link the page wrote. It now reads the third
    # argument the page HANDS the component - the page's actual
    # responsibility - and a stored path arriving here would fail just as
    # loudly.
    check('the download offers the FILE NAME, not the stored path',
          bool(r['pdf']) and r['pdf']['filename'] == 'ATOM_304156.pdf',
          str(r['pdf']))
    check('  and points at the document',
          bool(r['pdf']) and r['pdf']['url'].endswith('.pdf'),
          str(r['pdf']))"""

PI_GLYPH_WAS = """        check('  %-24s opens too' % glyph,
              '/media/x.pdf' in (r['viewer'] or ''), (r['viewer'] or '')[:40])"""

PI_GLYPH_NOW = """        check('  %-24s opens too' % glyph,
              bool(r['pdf']) and r['pdf']['url'] == '/media/x.pdf',
              str(r['pdf']))"""

PI_GLYPH5X_WAS = """check('  but the glyph survives as the not-a-PDF placeholder, which was always '
      'a fair use of it', 'fa-file-alt fa-5x' in JS)"""

PI_GLYPH5X_NOW = """# PV-1, 15 Oct 2026 - THE PLACEHOLDER MOVED, IT DID NOT GO.
# This page used to draw its own "cannot preview this" panel, a
# fa-file-alt fa-5x with a Download prompt. The shared component has that
# job now and does it better: an image gets shown rather than refused, and
# what cannot be shown at all gets an error state with a Download Instead
# button, which this page never offered. So the claim is asked of the
# component - the glyph survives, one layer over.
check('  but the not-a-PDF placeholder survives, in the component',
      'pdfViewerImageWrap' in COMPONENT_SRC
      and 'pdfViewerErrorDownload' in COMPONENT_SRC)"""

PI_SRC_WAS = """OLDJS = uncomment_js(scripts_of(OLD))"""

PI_SRC_NOW = """OLDJS = uncomment_js(scripts_of(OLD))

# PV-1, 15 Oct 2026 - the component's source, read once. Two claims below
# moved into it rather than out of existence: the viewer no longer renders
# an iframe because PDF.js draws to a canvas, and the not-a-PDF
# placeholder this page used to draw is the component's now. A suite that
# only asserted those ABSENCES would be asserting nothing; these assert
# what took their place.
_COMP = os.path.join(os.getcwd(), 'pages', 'templates', 'components',
                     'pdf_viewer.html')
COMPONENT_SRC = read(_COMP) if os.path.isfile(_COMP) else ''"""

IB = 'test_important_base.py'
MH = 'test_modal_heads.py'

# Three !important declarations went with the two viewers: asset_detail's
# iframe height and img max-height, and finance_pl_act's phone-only
# #invoiceViewerContent height. All three sized a body the component now
# sizes itself.
IB_TREE_WAS, IB_TREE_NOW = 858, 855

# And two .alv-modal-head headers, one per viewer. The component's own
# header already wore the class and was already counted, so the fall is
# exactly the two that left.
# SWAPPED, NOT BUMPED. bump() appends its note to the matched text, and
# this anchor ends MID-LINE - the note ran into the format string that
# follows it on the same line and commented it out, so the suite raised
# TypeError instead of reporting. A counter that is not alone on its line
# takes a whole-line swap.
MH_WAS = """ok(total == 53 and not bad, '%d header(s) on %d business template(s) carry '"""

# AND THE RENDERED COUNT, which is the same 53 asked a second way: the
# first section counts headers that carry the class, this one RENDERS
# them and counts the looks. Two headers left, so both fall to 51, and a
# round that fixed only one of them would have left the suite claiming
# a number it had just disproved.
MH2_WAS = """        ok(sum(now_looks.values()) == 53 and not off,"""

MH2_NOW = """        # PV-1, 15 Oct 2026 - 53 until the two hand-rolled invoice
        # viewers went. Same two headers as section 2 above, counted
        # here by what they RENDER rather than by the class they carry.
        ok(sum(now_looks.values()) == 51 and not off,"""

MH_NOW = """# PV-1, 15 Oct 2026 - 53 until this round, which retired two
# hand-rolled invoice viewers and their .alv-modal-head headers with
# them. components/pdf_viewer.html wears the class too and was already
# counted here, so the fall is exactly the two that left.
ok(total == 51 and not bad, '%d header(s) on %d business template(s) carry '"""

DR_WAS = 'N_FOOTER_SUBSTRING, N_FOOTER_TOKEN = 89, 88'
DR_NOW = ('N_FOOTER_SUBSTRING, N_FOOTER_TOKEN = 87, 86'
          '   # PV-1, 15 Oct 2026 - two hand-rolled invoice viewers went,'
          ' and each took one .modal-footer wrapper with it. Both matchers'
          ' fall by the same two, which is itself the point: the wrappers'
          ' that left were ordinary ones.   # (was 89, 88)')

# AND ONE THAT IS NOT A COUNT AT ALL. test_div_balance builds a bare
# template Engine with NO DIRS and renders each page's content block from
# a string. It stubs url, static, csrf_token and load - everything that
# needs a whole project - but not {% include %}, because until this round
# no page it renders had one. The first include in its CASES raised
# TemplateDoesNotExist and took the suite down with a traceback.
#
# GIVING IT THE TEMPLATE DIRECTORY IS THE FIX, NOT STUBBING THE INCLUDE.
# An engine that cannot resolve an include renders something the browser
# never sees, and this suite exists to count divs in what the browser
# sees. With dirs set, the component's markup is in the fixture and its
# balance is counted too.
DB_WAS = """    ENGINE = Engine(libraries={
        'humanize': 'django.contrib.humanize.templatetags.humanize'})"""

DB_NOW = """    # PV-1, 15 Oct 2026 - dirs, so {% include %} resolves.
    # ROOT is the template directory. Without it this engine renders a
    # page's content block with every include missing, which is not the
    # markup a browser receives - and from 15 Oct two of this suite's own
    # CASES include components/pdf_viewer.html, so it raised
    # TemplateDoesNotExist rather than reporting anything at all.
    ENGINE = Engine(dirs=[ROOT], libraries={
        'humanize': 'django.contrib.humanize.templatetags.humanize'})"""

BH_MODAL_WAS, BH_MODAL_NOW = 99, 95     # four footer buttons retired

BR_WAS = """check('asset_detail: Download is the primary of its dialog',
      'id="invoiceDownloadLink" href="#" class="btn action-primary"'
      in read('asset_detail.html'))"""

BR_NOW = """# PV-1, 15 Oct 2026 - RE-POINTED, NOT RETIRED.
# This pinned the exact markup of asset_detail's own Download link. That
# control is gone: the page now includes components/pdf_viewer.html, and
# the Download lives there. The CLAIM is unchanged - Download is still the
# primary of that dialog - so it is asked of the component, and of the page
# including it, rather than deleted because the markup moved.
check('asset_detail: Download is the primary of its dialog',
      "class=\\"btn action-primary pdf-action-download\\""
      in read('components/pdf_viewer.html')
      and "include 'components/pdf_viewer.html'"
      in read('asset_detail.html'))"""


def read(p):
    with open(p, encoding='utf-8', newline='') as f:
        return f.read()


def write(p, t):
    with open(p, 'w', encoding='utf-8', newline='') as f:
        f.write(t)


def backup(p):
    b = p + SUFFIX
    if not os.path.exists(b) and not CHECK:
        write(b, read(p))


def refuse(msg):
    raise SystemExit('PV-1 REFUSED: %s' % msg)


def fit(text, lit):
    """A multi-line anchor written LF here, converted to whatever THIS file
    mostly uses. finance_pl_act is CRLF and asset_detail is not, so an
    anchor written one way refuses on one half of the round."""
    if '\n' not in lit:
        return lit
    crlf = text.count('\r\n')
    lf = text.count('\n') - crlf
    body = lit.replace('\r\n', '\n')
    return body.replace('\n', '\r\n') if crlf > lf else body


def once(text, lit, where):
    got = text.count(fit(text, lit))
    if got != 1:
        refuse('%s: the anchor appears %d time(s), expected exactly 1 - %r'
               % (where, got, lit[:72]))


def swap(text, was, now, where):
    once(text, was, where)
    return text.replace(fit(text, was), fit(text, now), 1)


def bump(text, lit, was, now, note, where):
    old = lit % was
    once(text, old, where)
    return text.replace(old, '%s   # %s   # (was %d)'
                        % (lit % now, note, was), 1)


EDITS = {
    PL: [(PL_MODAL_WAS, PL_MODAL_NOW, 'the hand-rolled modal'),
         (PL_CSS_WAS, PL_CSS_NOW, 'its CSS and the forced z-index'),
         (PL_PHONE_FOOTER_WAS, PL_PHONE_FOOTER_NOW, 'the phone footer rule'),
         (PL_JS_WAS, PL_JS_NOW, 'the opener'),
         (PL_HIDE_WAS, PL_HIDE_NOW, 'the close handler')],
    AD: [(AD_MODAL_WAS, AD_MODAL_NOW, 'the hand-rolled modal'),
         (AD_CSS_WAS, AD_CSS_NOW, 'its phone CSS'),
         (AD_PHONE_PAD_WAS, AD_PHONE_PAD_NOW, 'the phone footer padding'),
         (AD_PHONE_FOOTER_WAS, AD_PHONE_FOOTER_NOW, 'the phone footer rule'),
         (AD_JS_WAS, AD_JS_NOW, 'the opener')],
}


def main(argv):
    global CHECK
    CHECK = '--check' in argv
    root = os.path.dirname(os.path.abspath(__file__))

    # ---------------------------------------------------------------- 0
    # ALREADY APPLIED COMES FIRST, and it is asked of the TREE: if neither
    # page still declares a viewer of its own, the markup half is done.
    live = 0
    for page in (PL, AD):
        s = read(alv_tree.path_of(page))
        live += s.count('id="invoiceViewerModal"')
    if not live:
        print('PV-1  already applied - neither page declares a viewer of '
              'its own.')
        return 0

    # ---------------------------------------------------------------- 1
    # THE COMPONENT HAS TO EXIST BEFORE ANYTHING INCLUDES IT.
    comp = os.path.join(root, 'pages', 'templates', 'components',
                        'pdf_viewer.html')
    if not os.path.isfile(comp):
        refuse('%s is not on disk - this round includes it twice' % COMPONENT)
    if 'window.openPdfViewer' not in read(comp):
        refuse('%s does not define openPdfViewer' % COMPONENT)

    out = {}
    for page, edits in EDITS.items():
        p = alv_tree.path_of(page)
        s = read(p)
        for was, now, what in edits:
            s = swap(s, was, now, '%s (%s)' % (page, what))
        out[p] = s

    # ---------------------------------------------------------------- 2
    # GATES. Each one is a thing the survey measured, asserted rather than
    # assumed, and each refuses the whole round rather than writing half.
    for page in (PL, AD):
        s = out[alv_tree.path_of(page)]
        if s.count(INCLUDE) != 1:
            refuse('%s: expected exactly 1 include of the component, got %d'
                   % (page, s.count(INCLUDE)))
        if 'invoiceViewerModal' in code_only(s):
            refuse('%s: the old viewer is still referenced in code' % page)
        if 'invoiceViewerContent' in code_only(s):
            refuse('%s: the old viewer body is still referenced' % page)

    # THE INCLUDE MUST SIT AFTER THE DRILL-DOWN. Measured: both modals are
    # z-index 1050 and document order decides which is on top. This is the
    # one gate that would let a silent, phone-only regression through.
    s = out[alv_tree.path_of(PL)]
    if s.index(INCLUDE) < s.index('id="expenseDetailsModal"'):
        refuse('%s: the include sits BEFORE #expenseDetailsModal - the '
               'viewer would open underneath it' % PL)

    # ---------------------------------------------------------------- 3
    # the two suites this round moves, each with its owner named
    p = os.path.join(root, BH)
    out[p] = bump(read(p), 'N_BAR, N_ROW, N_MODAL = 268, 110, %d',
                  BH_MODAL_WAS, BH_MODAL_NOW,
                  'PV-1, 15 Oct 2026 - the four footer buttons of two '
                  'hand-rolled invoice viewers. The shared component they '
                  'moved onto was already in this census, so the count '
                  'falls by exactly the four that went.',
                  '%s (the modal census)' % BH)

    p = os.path.join(root, BR)
    s = read(p)
    if 'pdf-action-download' in s:
        refuse('%s already asks the component' % BR)
    out[p] = swap(s, BR_WAS, BR_NOW, '%s (the asset_detail Download)' % BR)

    p = os.path.join(root, DR)
    out[p] = swap(read(p), DR_WAS, DR_NOW, '%s (the footer wrappers)' % DR)

    p = os.path.join(root, DB)
    s = read(p)
    if 'Engine(dirs=' in s:
        refuse('%s already gives its engine a template directory' % DB)
    out[p] = swap(s, DB_WAS, DB_NOW, '%s (the template engine)' % DB)

    p = os.path.join(root, IB)
    out[p] = bump(read(p), 'IMP_TREE = %d', IB_TREE_WAS, IB_TREE_NOW,
                  'PV-1, 15 Oct 2026 - three !important declarations went '
                  'with the two hand-rolled viewers: an iframe height, an '
                  'img max-height and a phone-only body height. The '
                  'component sizes its own body.',
                  '%s (the tree count)' % IB)

    p = os.path.join(root, RT)
    out[p] = swap(read(p), RT_WAS, RT_NOW, '%s (the swept-side census)' % RT)

    p = os.path.join(root, PI)
    s = read(p)
    if 'window.__pdf' in s:
        refuse('%s already asks the handoff' % PI)
    for was, now, what in ((PI_STUB_WAS, PI_STUB_NOW, 'the component stub'),
                           (PI_ROW_WAS, PI_ROW_NOW, 'the fixture row'),
                           (PI_PROBE_WAS, PI_PROBE_NOW, 'the probe'),
                           (PI_SRC_WAS, PI_SRC_NOW, 'the component source'),
                           (PI_CHECKS_WAS, PI_CHECKS_NOW, 'section 3'),
                           (PI_DL_WAS, PI_DL_NOW, 'the download claim'),
                           (PI_GLYPH_WAS, PI_GLYPH_NOW, 'the glyph sweep'),
                           (PI_GLYPH5X_WAS, PI_GLYPH5X_NOW,
                            'the not-a-PDF placeholder')):
        s = swap(s, was, now, '%s (%s)' % (PI, what))
    out[p] = s

    p = os.path.join(root, MH)
    s = read(p)
    s = swap(s, MH_WAS, MH_NOW, '%s (the header count)' % MH)
    s = swap(s, MH2_WAS, MH2_NOW, '%s (the rendered look count)' % MH)
    out[p] = s

    # ---------------------------------------------------------------- 4
    # the registers and the two counters these rounds keep by hand
    p = os.path.join(root, PS1)
    s = read(p)
    if 'test_pdf_viewer.py' in s:
        refuse('%s already lists this round' % PS1)
    s = swap(s, SUITE_WAS, SUITE_NOW, '%s (the suite list)' % PS1)
    s = swap(s, CLAIMS_ANCHOR, CLAIMS, '%s (the claims)' % PS1)
    out[p] = s

    p = os.path.join(root, TREE)
    out[p] = swap(read(p), TREE_WAS, TREE_NOW, '%s (CONVERTED)' % TREE)

    p = os.path.join(root, ROUNDS)
    out[p] = swap(read(p), ROUNDS_WAS, ROUNDS_NOW, '%s (ROUNDS)' % ROUNDS)

    p = os.path.join(root, WD)
    out[p] = bump(read(p), 'CONVERTED_N = %d', CONVERTED_WAS, CONVERTED_NOW,
                  'PV-1, 15 Oct 2026 - this round own suite. Two '
                  'hand-rolled invoice viewers onto the shared component, '
                  'after Demetri asked why the P&L one had no Share '
                  'button.',
                  '%s (the converted count)' % WD)

    p = os.path.join(root, CO)
    s = read(p)
    s = bump(s, 'ok(len(aliased) == %d,', ALIAS_WAS, ALIAS_NOW,
             'PV-1, 15 Oct 2026 - this round own patcher and suite',
             '%s (the alias count)' % CO)
    s = swap(s, "'%%d file(s) alias it - %d patchers and %d suites'"
             % (ALIAS_P_WAS, ALIAS_S_WAS),
             "'%%d file(s) alias it - %d patchers and %d suites'"
             % (ALIAS_P_NOW, ALIAS_S_NOW),
             '%s (the alias split)' % CO)
    out[p] = s

    # ---------------------------------------------------------------- 5
    if CHECK:
        print('PV-1 --check  %d file(s) would change' % len(out))
        for q in sorted(out):
            print('   %s' % os.path.relpath(q, root))
        return 0

    for q, t in sorted(out.items()):
        backup(q)
        write(q, t)

    print('PV-1 applied.')
    print('   %d page(s) drop a hand-rolled viewer for the shared component'
          % N_PAGES)
    print('   %d viewer(s) in the application, down from %d'
          % (N_VIEWERS_NOW, N_VIEWERS_WAS))
    print('   %d page(s) now include it, up from %d'
          % (N_INCLUDERS_NOW, N_INCLUDERS_WAS))
    print('   each page phone footer rule is EXCLUDED from it, not')
    print('         overruled - 754px and 963px of controls on a 390px')
    print('         screen become 348px and 309px')
    print('   the drill-down keeps modal-open when the viewer closes')
    print('   %d page(s) still load a second jQuery - named, not this '
          'round' % N_DUP_JQUERY)
    print('   %d file(s) written, backups end %s' % (len(out), SUFFIX))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
