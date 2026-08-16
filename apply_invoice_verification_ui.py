#!/usr/bin/env python3
"""
apply_invoice_verification_ui.py
================================

Front-end half of the Invoice Verification feature. Patches
pages/templates/act_expense.html:

  1. Verdict badge on the expenses list  - the existing green document icon
     becomes status-coloured, so a month can be triaged at a glance.
  2. Verdict banner in the Invoice Document tab.
  3. Mobile camera capture - "Take Photo" / "Choose File" on touch devices,
     with client-side downscaling so phone photos clear the 5MB server cap.
  4. .heic / .heif accepted (iPhone captures).

Idempotent; backs up to act_expense.html.bak_invverify_ui. Preserves the
file's CRLF line endings. Run from the project root AFTER
apply_invoice_verification.py:

    python apply_invoice_verification_ui.py [--check]
"""

import os
import shutil
import sys

CHECK = '--check' in sys.argv
ROOT = os.path.dirname(os.path.abspath(__file__))
TARGET = os.path.join(ROOT, 'pages', 'templates', 'act_expense.html')
SENTINEL = 'EXPENSE_VERIFY'

OLD_ACCEPT = 'accept=".pdf,.jpg,.jpeg,.png,.xlsx,.xls,.doc,.docx"'
NEW_ACCEPT = 'accept=".pdf,.jpg,.jpeg,.png,.heic,.heif,.xlsx,.xls,.doc,.docx"'

OLD_INPUT = ('<input type="file" class="form-control-file" name="act_expense_document" '
             + NEW_ACCEPT + ' required>')
NEW_INPUT = OLD_INPUT + '\n                        ${captureButtons()}'

# --- 1. list icon -----------------------------------------------------------
OLD_ICON = """            {% if expense.act_expense_document %}
                <i class="fas fa-file-alt"
                   style="cursor: pointer; color: #28a745; margin-left: 8px;"
                   onclick="viewInvoiceQuick('{{ expense.act_expense_document.url }}', '{{ expense.act_expense_document.name }}')"
                   title="Click to view invoice"></i>
            {% endif %}"""

NEW_ICON = """            {% if expense.act_expense_document %}
                {% with badge=expense.verify_badge %}
                <i class="fas {{ badge.1 }} verify-icon verify-{{ badge.0 }}"
                   style="cursor: pointer; margin-left: 8px;"
                   onclick="viewInvoiceQuick('{{ expense.act_expense_document.url }}', '{{ expense.act_expense_document.name }}')"
                   title="{{ badge.2 }} - click to view invoice"></i>
                {% endwith %}
            {% endif %}"""

# --- 2. verdict data map + banner + camera ---------------------------------
OLD_MODAL_FN = 'function openManageModal(expenseId, date, property, description, amount, approved, paid, documentUrl, documentName, isSuperuser, canEditExpenses) {'

NEW_MODAL_FN = '''// ---------------------------------------------------------------------
// Invoice verification: verdict per expense, rendered once by Django so the
// modal needs no extra round-trip and openManageModal keeps its signature.
// ---------------------------------------------------------------------
window.EXPENSE_VERIFY = {
{% for expense in expenses %}{% if expense.act_expense_document %}  "{{ expense.act_expense_id }}": {
    "status": "{{ expense.act_expense_verify_status|default_if_none:''|escapejs }}",
    "notes": "{{ expense.act_expense_verify_notes|default_if_none:''|escapejs }}",
    "total": "{{ expense.act_expense_verify_total|default_if_none:''|escapejs }}",
    "supplier": "{{ expense.act_expense_verify_supplier|default_if_none:''|escapejs }}",
    "number": "{{ expense.act_expense_verify_number|default_if_none:''|escapejs }}",
    "invoiceDate": "{{ expense.act_expense_verify_date|date:'Y-m-d'|default_if_none:''|escapejs }}"
  },
{% endif %}{% endfor %}};

// Verdict banner shown above the document card in the Invoice tab.
function verifyBanner(expenseId) {
    const v = (window.EXPENSE_VERIFY || {})[String(expenseId)];
    if (!v || !v.status) { return ''; }

    const styles = {
        verified:    ['success', 'fa-check-circle',         'Invoice verified'],
        mismatch:    ['danger',  'fa-exclamation-triangle', 'Invoice does not match the approved amount'],
        unverified:  ['secondary', 'fa-question-circle',    'Not checked automatically'],
        not_invoice: ['secondary', 'fa-file',               'Not an invoice'],
        split:       ['info',      'fa-object-group',       'One invoice covering several expenses']
    };
    const s = styles[v.status];
    if (!s) { return ''; }

    const detail = [];
    if (v.total)       { detail.push('<strong>Invoice total:</strong> \\u20ac' + v.total); }
    if (v.supplier)    { detail.push('<strong>Supplier:</strong> ' + v.supplier); }
    if (v.number)      { detail.push('<strong>Invoice no:</strong> ' + v.number); }
    if (v.invoiceDate) { detail.push('<strong>Invoice date:</strong> ' + v.invoiceDate); }

    const notes = (v.notes || '').split('\\n').filter(Boolean)
        .map(n => '<div class="verify-note">' + n + '</div>').join('');

    return `
        <div class="alert alert-${s[0]} verify-banner">
            <div class="verify-banner-head"><i class="fas ${s[1]}"></i> <strong>${s[2]}</strong></div>
            ${notes}
            ${detail.length ? '<div class="verify-meta">' + detail.join(' &nbsp;|&nbsp; ') + '</div>' : ''}
            ${v.status === 'mismatch' ? '<div class="verify-action">The amount can only be changed after the expense is un-approved.</div>' : ''}
        </div>
    `;
}

// ---------------------------------------------------------------------
// Mobile capture. Two buttons rather than one input with `capture`: a bare
// capture attribute FORCES the camera on mobile and removes access to the
// photo library and files, which would break attaching an emailed PDF.
// One input, swapped attribute - so no duplicate field names.
// ---------------------------------------------------------------------
function isTouchDevice() {
    return window.matchMedia && window.matchMedia('(pointer: coarse)').matches
           && ('capture' in document.createElement('input'));
}

function captureButtons() {
    if (!isTouchDevice()) { return ''; }
    return `
        <div class="capture-row">
            <button type="button" class="btn btn-primary btn-sm" onclick="pickWith(this, true)">
                <i class="fas fa-camera"></i> Take Photo
            </button>
            <button type="button" class="btn btn-outline-secondary btn-sm" onclick="pickWith(this, false)">
                <i class="fas fa-paperclip"></i> Choose File
            </button>
            <div class="capture-name text-muted small"></div>
        </div>
    `;
}

function pickWith(btn, useCamera) {
    const form = btn.closest('form');
    const input = form.querySelector('input[type=file]');
    if (!input) { return; }
    if (useCamera) { input.setAttribute('capture', 'environment'); }
    else { input.removeAttribute('capture'); }
    input.click();
}

// Show the chosen filename, since the native input is hidden on touch devices.
document.addEventListener('change', function (e) {
    if (!e.target || e.target.type !== 'file') { return; }
    const row = e.target.closest('form') && e.target.closest('form').querySelector('.capture-name');
    if (row) { row.textContent = e.target.files.length ? e.target.files[0].name : ''; }
});

// Phone photos are routinely 3-12MB and the server rejects anything over 5MB.
// Downscale in the browser before submitting: long edge 1600px, JPEG q0.8,
// which lands around 300KB and stays comfortably legible for extraction.
const MAX_EDGE = 1600, JPEG_QUALITY = 0.8, RESIZE_ABOVE = 1.5 * 1024 * 1024;

function maybeDownscale(input) {
    return new Promise(function (resolve) {
        const file = input.files && input.files[0];
        if (!file || !file.type.startsWith('image/') || file.size <= RESIZE_ABOVE) {
            return resolve(false);
        }
        const reader = new FileReader();
        reader.onload = function () {
            const img = new Image();
            img.onload = function () {
                const scale = Math.min(1, MAX_EDGE / Math.max(img.width, img.height));
                const canvas = document.createElement('canvas');
                canvas.width = Math.round(img.width * scale);
                canvas.height = Math.round(img.height * scale);
                canvas.getContext('2d').drawImage(img, 0, 0, canvas.width, canvas.height);
                canvas.toBlob(function (blob) {
                    if (!blob) { return resolve(false); }
                    try {
                        const name = (file.name.replace(/\\.[^.]+$/, '') || 'photo') + '.jpg';
                        const dt = new DataTransfer();
                        dt.items.add(new File([blob], name, { type: 'image/jpeg' }));
                        input.files = dt.files;
                        resolve(true);
                    } catch (err) { resolve(false); }
                }, 'image/jpeg', JPEG_QUALITY);
            };
            img.onerror = function () { resolve(false); };
            img.src = reader.result;
        };
        reader.onerror = function () { resolve(false); };
        reader.readAsDataURL(file);
    });
}

// Intercept submit once per form, downscale, then let it through.
document.addEventListener('submit', function (e) {
    const form = e.target;
    if (!form || !form.enctype || form.enctype.indexOf('multipart') === -1) { return; }
    if (form.dataset.resized === '1') { form.dataset.resized = ''; return; }
    const input = form.querySelector('input[type=file]');
    if (!input || !input.files || !input.files.length) { return; }
    e.preventDefault();
    maybeDownscale(input).then(function () {
        form.dataset.resized = '1';
        if (typeof form.requestSubmit === 'function') { form.requestSubmit(); }
        else { form.submit(); }
    });
}, true);

''' + OLD_MODAL_FN

OLD_LAUNCHER = '${launcherCard(documentName)}'
NEW_LAUNCHER = '${verifyBanner(expenseId)}${launcherCard(documentName)}'

# --- 3. styles --------------------------------------------------------------
OLD_STYLE_ANCHOR = "{% block content %}\n\n<style>"
NEW_STYLE = """{% block content %}

<style>
/* ---- Invoice verification ---------------------------------------- */
.verify-icon.verify-success   { color: #28a745; }
.verify-icon.verify-danger    { color: #dc3545; }
.verify-icon.verify-secondary { color: #6c757d; }
.verify-icon.verify-info      { color: #17a2b8; }
.verify-banner { text-align: left; font-size: 0.9rem; margin-bottom: 12px; }
.verify-banner-head { margin-bottom: 6px; }
.verify-note { margin-top: 2px; }
.verify-meta { margin-top: 8px; font-size: 0.82rem; opacity: 0.9; }
.verify-action { margin-top: 8px; font-style: italic; font-size: 0.82rem; }
.capture-row { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; margin-top: 8px; }
.capture-name { width: 100%; word-break: break-all; }
/* On touch devices the two buttons replace the native picker. */
@media (pointer: coarse) {
    .form-group input[type="file"][name="act_expense_document"] {
        position: absolute; width: 1px; height: 1px;
        opacity: 0; overflow: hidden; z-index: -1;
    }
}
"""


def sniff(path):
    with open(path, 'rb') as fh:
        raw = fh.read()
    enc = 'utf-8-sig' if raw.startswith(b'\xef\xbb\xbf') else 'utf-8'
    return enc, ('\r\n' if b'\r\n' in raw else '\n')


def main():
    if not os.path.exists(TARGET):
        print('! pages/templates/act_expense.html not found')
        return 1

    enc, nl = sniff(TARGET)
    with open(TARGET, encoding=enc, newline='') as fh:
        src = fh.read().replace('\r\n', '\n')

    if SENTINEL in src:
        print('= act_expense.html already patched - nothing to do')
        return 0

    steps = [
        ('list icon', OLD_ICON, NEW_ICON, 1),
        ('modal helpers', OLD_MODAL_FN, NEW_MODAL_FN, 1),
        ('verdict banner', OLD_LAUNCHER, NEW_LAUNCHER, 2),
        ('styles', OLD_STYLE_ANCHOR, NEW_STYLE, 1),
        ('accept heic', OLD_ACCEPT, NEW_ACCEPT, 3),
    ]
    for name, old, _new, expected in steps:
        found = src.count(old)
        if found != expected:
            print('! anchor "%s" found %d times, expected %d - aborting, nothing written'
                  % (name, found, expected))
            return 1

    for name, old, new, expected in steps:
        src = src.replace(old, new) if expected > 1 else src.replace(old, new, 1)

    # capture buttons after each of the three (now-updated) file inputs
    n_inputs = src.count(OLD_INPUT)
    if n_inputs != 3:
        print('! file input anchor found %d times, expected 3 - aborting' % n_inputs)
        return 1
    src = src.replace(OLD_INPUT, NEW_INPUT)

    if CHECK:
        print('= check only: all 6 anchors matched, %d bytes would be written' % len(src))
        return 0

    bak = TARGET + '.bak_invverify_ui'
    if not os.path.exists(bak):
        shutil.copy2(TARGET, bak)
    out = src.replace('\n', nl) if nl == '\r\n' else src
    with open(TARGET, 'w', encoding=enc, newline='') as fh:
        fh.write(out)

    print('+ act_expense.html patched (backup: %s)' % os.path.basename(bak))
    print('  - status-coloured document icon on the list')
    print('  - verdict banner in the Invoice Document tab')
    print('  - Take Photo / Choose File on touch devices + client-side downscale')
    print('  - .heic / .heif accepted')
    return 0


if __name__ == '__main__':
    sys.exit(main())
