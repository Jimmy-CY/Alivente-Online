#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""The P&L drill-down can open an invoice again - by reading data, not colour.

THE REPORT. On the P&L in Actuals mode, clicking a figure opens "Actual Expense
Details" and the invoice icons in it do nothing.

WHAT IS ACTUALLY THERE. The modal already fetches the expenses table, injects
it, and calls `setupInvoiceIconHandlers()`. That handler is wrong twice over:

    $(document).off('click', '.fa-file-alt').on('click', '.fa-file-alt', ...
        var isGreen = color === 'rgb(40, 167, 69)' || color === 'rgb(0, 128, 0)'
                   || color === 'green' || $icon.hasClass('text-success')
                   || ($icon.attr('style') || '').includes('color: #28a745');
        if (isGreen) { ... open it ... }

  1. THE SELECTOR MATCHES NOTHING. `verify_badge` emits fa-check-circle,
     fa-exclamation-triangle, fa-question-circle, fa-file or fa-file-invoice.
     Never fa-file-alt - that glyph belongs to the report drill table. So no
     click on an invoice icon in this modal has ever been caught.

  2. IT DECIDES BY COLOUR. Three of the four tests name Bootstrap's #28a745.
     Even with the selector fixed, the icon moving onto the house --alv-good
     token would break it again - which the Manage Expense round has just
     done. A colour is a rendering of data, never a substitute for reading it.

THE FIX IS SMALLER THAN WHAT IT REPLACES. The injected rows already carry
`onclick="viewInvoiceQuick(url, name)"` - a function that lives on the Expenses
page and not on this one, which is why the original tried to intercept the
click and re-parse the attribute out of the DOM. Give the name a meaning here
instead: the same document, opened in this page's own viewer. The inline
handler then simply works, and no colour is consulted.

A delegated handler stays for any icon that carries the document in data
attributes rather than an onclick, guarded so an icon with both does not open
twice.

Also fixed on the way past: the download name was the stored PATH
(`invoices/2026/x.pdf`), not the file name.

Run from the repo root.  --check plans without writing.
"""
import os, re, sys, shutil

ROOT   = os.path.dirname(os.path.abspath(__file__))
TPL    = os.path.join(ROOT, 'pages', 'templates')
PAGE   = os.path.join(TPL, 'finance_pl_act.html')
CHECK  = '--check' in sys.argv
SUFFIX = '.bak_plinvoice'

OLD = """    function setupInvoiceIconHandlers() {
        $(document).off('click', '.fa-file-alt').on('click', '.fa-file-alt', function(e) {
            var $icon = $(this);
            var color = $icon.css('color');
            var isGreen = color === 'rgb(40, 167, 69)' || color === 'rgb(0, 128, 0)' || color === 'green' ||
                         $icon.hasClass('text-success') ||
                         ($icon.attr('style') && $icon.attr('style').includes('color: #28a745'));
            if (isGreen) {
                e.preventDefault();
                e.stopPropagation();
                firstModalScrollTop = $('#expenseDetailsModal .modal-body').scrollTop();
                var onclickAttr = $icon.attr('onclick');
                if (onclickAttr) {
                    var matches = onclickAttr.match(/viewInvoiceQuick\\('([^']+)',\\s*'([^']+)'\\)/);
                    if (matches && matches.length >= 2) {
                        showInvoiceModalLikeExisting(matches[1], matches[2] || 'invoice.pdf');
                        return;
                    }
                }
                var documentUrl = $icon.data('invoice-url') || $icon.data('url');
                var documentName = $icon.data('filename') || 'invoice.pdf';
                if (documentUrl) {
                    showInvoiceModalLikeExisting(documentUrl, documentName);
                } else {
                    alert('Invoice file not found.');
                }
            }
        });
    }"""

NEW = """    // The rows injected into this modal come from the Expenses page and carry
    // inline onclick="viewInvoiceQuick(url, name)" - a function that lives on
    // THAT page and not on this one, so the click threw and nothing opened.
    //
    // Give the name a meaning here rather than intercepting the click and
    // re-parsing the attribute out of the DOM, which is what this used to do:
    //
    //   $(document).on('click', '.fa-file-alt', ...)
    //       var isGreen = color === 'rgb(40, 167, 69)' || ... '#28a745' ...
    //       if (isGreen) { open it }
    //
    // wrong twice. The selector named a glyph verify_badge never emits - it
    // renders fa-check-circle, fa-exclamation-triangle, fa-question-circle,
    // fa-file or fa-file-invoice - so no click was ever caught. And it decided
    // whether an icon was an invoice by COMPARING ITS COLOUR to Bootstrap
    // green, which is reading a rendering of data instead of the data.
    window.viewInvoiceQuick = function (documentUrl, documentName) {
        if (!documentUrl) { return; }
        firstModalScrollTop = $('#expenseDetailsModal .modal-body').scrollTop();
        // The stored value is a PATH; the viewer wants a file name to offer as
        // the download.
        var name = String(documentName || '').split('/').pop() || 'invoice.pdf';
        showInvoiceModalLikeExisting(documentUrl, name);
    };

    function setupInvoiceIconHandlers() {
        // For any invoice icon that carries its document in data attributes
        // rather than an onclick. Guarded on the onclick so an icon with both
        // does not open the viewer twice.
        $(document).off('click', '.verify-icon').on('click', '.verify-icon', function(e) {
            var $icon = $(this);
            if ($icon.attr('onclick')) { return; }
            var documentUrl = $icon.data('invoice-url') || $icon.data('url');
            if (!documentUrl) { return; }
            e.preventDefault();
            e.stopPropagation();
            window.viewInvoiceQuick(documentUrl, $icon.data('filename') || 'invoice.pdf');
        });
    }"""


def read(p):
    with open(p, encoding='utf-8') as f:
        return f.read()


def main():
    src = read(PAGE)

    if 'window.viewInvoiceQuick' in src:
        print('  P&L invoice icons          already fixed')
        print('\n  0 file(s) changed')
        return

    n = src.count(OLD)
    if n != 1:
        sys.exit('! setupInvoiceIconHandlers did not match as expected '
                 '(%d occurrence(s)) - it may already have been edited' % n)
    out = src.replace(OLD, NEW, 1)

    bad = []
    _js = '\n'.join(re.findall(r'<script[^>]*>(.*?)</script>', out, re.S))
    # Comments stripped before anything is searched: the note above explains
    # what was removed and names every string it names.
    _code = re.sub(r'//[^\n]*', '', re.sub(r'/\*.*?\*/', '', _js, flags=re.S))
    for gone in ('rgb(40, 167, 69)', '#28a745', 'isGreen'):
        if gone in _code:
            bad.append('%s survives in live script code' % gone)
    # fa-file-alt as a SELECTOR is the fault. The same glyph is also the
    # placeholder this page draws for a file that is neither a PDF nor an
    # image, which is a perfectly good use - asking whether the string is in
    # the file at all reported that legitimate one.
    if re.search('\\.fa-file-alt[\'\"]', _code):
        bad.append('fa-file-alt is still used as a selector')
    for want in ('window.viewInvoiceQuick', "off('click', '.verify-icon')",
                 'showInvoiceModalLikeExisting'):
        if want not in _code:
            bad.append('expected and missing: %s' % want)
    if _code.count('window.viewInvoiceQuick') < 2:
        bad.append('the shim is defined but never used')
    if 'firstModalScrollTop' not in _code:
        bad.append('the scroll position is no longer remembered')
    for blk in re.findall(r'<script[^>]*>(.*?)</script>', out, re.S):
        b = re.sub(r'//[^\n]*', '', re.sub(r'/\*.*?\*/', '', blk, flags=re.S))
        if b.count('{') != b.count('}'):
            bad.append('a script block no longer balances its braces')
            break
    # This page's div counts do NOT balance and never did: it builds markup
    # inside JavaScript template literals, so opens and closes land in
    # different places. An absolute count means nothing here. What must hold
    # is that THIS EDIT changed neither number.
    for tag in ('div', 'script'):
        before = (len(re.findall(r'<%s\b' % tag, src)),
                  len(re.findall(r'</%s\s*>' % tag, src)))
        after = (len(re.findall(r'<%s\b' % tag, out)),
                 len(re.findall(r'</%s\s*>' % tag, out)))
        if before != after:
            bad.append('the edit changed the %s tag counts %s -> %s'
                       % (tag, before, after))
    if bad:
        sys.exit('! P&L invoice self-check FAILED, nothing written:\n   - %s'
                 % '\n   - '.join(bad))

    print('  finance_pl_act.html         the drill-down opens an invoice again')
    print('     by reading the document off the icon, not its colour')

    if not CHECK:
        b = PAGE + SUFFIX
        if not os.path.exists(b):
            shutil.copy2(PAGE, b)
        with open(PAGE, 'w', encoding='utf-8') as f:
            f.write(out)

    print('\n  1 file(s) %s' % ('would change' if CHECK else 'changed'))


if __name__ == '__main__':
    main()
