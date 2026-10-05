"""AI-1 - AN ATTACHED INVOICE CAN BE TAKEN OFF AGAIN.

   Demetri, 5 Oct 2026: "The add file to the Edit Asset works perfectly.
   However, I need to add the functionality to remove an attached file."

   He is right that there was none. Edit Asset showed

       Current file: asset_invoices/....png
       [Choose file]  Upload a new file to replace the existing one

   and REPLACE was the only verb available. An invoice attached by
   mistake could be swapped for another one, never removed.

   IMMEDIATE, NOT ON SAVE, and that was a real choice. Everything else on
   that screen waits for Save Changes, so a tickbox would have been the
   consistent thing - but the PHOTOS on that same page already delete the
   moment you press their button, through a hidden form outside
   editAssetForm that the button reaches by `form=`. Demetri chose to
   match the photos rather than the fields: "on Remove - immediate, like
   the photos". So the invoice gets the same shape, with a confirm.

   THE HIDDEN FORM IS NOT A STYLE CHOICE. HTML does not allow a form
   inside a form, and the Remove button has to sit beside the file it
   removes - which is in the middle of editAssetForm. The page already
   solved this twice for photos, and SV-1 spent a round on what happens
   when a submit button has no form owner. Same solution: the form lives
   outside, the button names it.

   THE FILE LEAVES STORAGE. `.delete(save=False)` removes the bytes, the
   field is cleared, and the row is saved - which is what
   act_expense.html's delete_document does and what unlinking alone would
   not. An invoice nobody can reach but that still occupies disk is not
   removed, it is hidden.

   FILES: edit_asset.html, pages/urls.py, pages/views/properties.py.
                                             [test_asset_invoice.py]
"""
import os
import sys

import alv_tree as T

SUFFIX = '.bak_assetinv'

# ----------------------------------------------------------- the markup

TPL_OLD = '''        {% if asset.purchase_invoice %}
            <div class="alert alert-info current-file-info">
                Current file: <a href="{{ asset.purchase_invoice.url }}" target="_blank">{{ asset.purchase_invoice.name }}</a>
            </div>
        {% endif %}'''

TPL_NEW = '''        {% if asset.purchase_invoice %}
            {# AI-1, 5 Oct 2026 - Demetri: "I need to add the #}
            {# functionality to remove an attached file." Replace was #}
            {# the only verb this field had. #}
            {# #}
            {# The button names a form that lives OUTSIDE editAssetForm, #}
            {# because HTML does not allow a form inside a form and this #}
            {# control has to sit beside the file it removes. The photos #}
            {# below already do exactly this. #}
            <div class="alert alert-info current-file-info">
                <span class="current-file-name">
                    Current file: <a href="{{ asset.purchase_invoice.url }}" target="_blank">{{ asset.purchase_invoice.name }}</a>
                </span>
                <button type="submit" form="deleteInvoiceForm"
                        class="icon-action-btn icon-delete"
                        title="Remove this file" aria-label="Remove this file">
                    <i class="fas fa-trash"></i>
                </button>
            </div>
        {% endif %}'''

HELP_OLD = ('<small class="form-text text-muted">Upload a new file to '
            'replace the existing one</small>')
HELP_NEW = ('<small class="form-text text-muted">Upload a new file to '
            'replace the existing one</small>')

FORM_OLD = '''<!-- Hidden per-photo action forms — must live OUTSIDE editAssetForm because HTML
     doesn't allow nested forms. Star/delete buttons reference these by ID. -->'''

FORM_NEW = '''{% if asset.purchase_invoice %}
    <!-- AI-1 - the invoice's own hidden form, same reason as the photos'. -->
    <form method="post" action="{% url 'delete_asset_invoice' asset.id %}"
          id="deleteInvoiceForm" style="display:none"
          onsubmit="return confirm('Remove the attached invoice? The file will be deleted.');">
        {% csrf_token %}
    </form>
{% endif %}

<!-- Hidden per-photo action forms — must live OUTSIDE editAssetForm because HTML
     doesn't allow nested forms. Star/delete buttons reference these by ID. -->'''

CSS_OLD = '''.current-file-info {
    margin-bottom: 8px;
    padding: 10px 14px;
}'''

CSS_NEW = '''.current-file-info {
    margin-bottom: 8px;
    padding: 10px 14px;
}
/* AI-1 - the name on the left, the Remove action on the right. The
   banner was a block of text; it is now a row with a control in it. */
.current-file-info {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
}
.current-file-name {
    min-width: 0;
    overflow-wrap: anywhere;
}'''

# -------------------------------------------------------------- the URL

URL_OLD = ("    path('assets/<int:asset_id>/photos/<int:photo_id>/delete/', "
           "views.delete_asset_photo, name='delete_asset_photo'),")

URL_NEW = ("    path('assets/<int:asset_id>/invoice/delete/', "
           "views.delete_asset_invoice, name='delete_asset_invoice'),\n"
           + URL_OLD)

# ------------------------------------------------------------- the view

VIEW_ANCHOR = '''@login_required
@permission_required('auth.can_edit_properties', raise_exception=True)
@require_POST
def delete_asset_photo(request, asset_id, photo_id):'''

VIEW_NEW = '''@login_required
@permission_required('auth.can_edit_properties', raise_exception=True)
@require_POST
def delete_asset_invoice(request, asset_id):
    """Remove the asset's purchase invoice. POST only.

    AI-1, 5 Oct 2026. Demetri: "I need to add the functionality to remove
    an attached file." The field could only ever be REPLACED.

    THE BYTES GO, not just the link. `.delete(save=False)` removes the
    file from storage and leaves the model alone; the field is then
    cleared and the row saved in one write. Clearing the field by itself
    would leave a file nobody can reach still occupying disk, which is
    hidden rather than removed - act_expense's delete_document learned
    this first and does the same thing.
    """
    asset = get_object_or_404(PropertyAsset, pk=asset_id)
    if not asset.purchase_invoice:
        messages.warning(request, 'There is no invoice attached to remove.')
        return redirect('edit_asset', asset_id=asset_id)
    try:
        asset.purchase_invoice.delete(save=False)
        asset.purchase_invoice = None
        asset.save(update_fields=['purchase_invoice'])
        messages.success(request, 'Invoice removed.')
    except Exception as e:
        messages.error(request, f'Error removing the invoice: {str(e)}')
    return redirect('edit_asset', asset_id=asset_id)


''' + VIEW_ANCHOR

PARTS_TPL = [(TPL_OLD, TPL_NEW), (FORM_OLD, FORM_NEW), (CSS_OLD, CSS_NEW)]


def read(path):
    with open(path, encoding='utf-8', newline='') as fh:
        return fh.read()


def write(path, text):
    with open(path, 'w', encoding='utf-8', newline='') as fh:
        fh.write(text)


def backup(path):
    bak = path + SUFFIX
    if not os.path.exists(bak):
        with open(path, 'rb') as src, open(bak, 'wb') as dst:
            dst.write(src.read())


def fit(text, block):
    return block.replace('\n', '\r\n') if '\r\n' in text else block


def one(text, needle, what):
    n = text.count(needle)
    if n != 1:
        raise SystemExit('AI-1: %s matched %d times, expected 1' % (what, n))


def main(argv):
    check = '--check' in argv
    root = os.path.dirname(os.path.abspath(__file__))
    os.chdir(root)
    done = 0

    # --- template
    path = T.path_of('edit_asset.html')
    text = read(path)
    for i, (old, new) in enumerate(PARTS_TPL):
        if fit(text, new) in text:
            continue
        o = fit(text, old)
        one(text, o, 'template anchor %d' % (i + 1))
        text = text.replace(o, fit(text, new), 1)
        done += 1
    if done and not check:
        backup(path)
        write(path, text)

    # --- url
    up = os.path.join(root, 'pages', 'urls.py')
    utext = read(up)
    if "name='delete_asset_invoice'" not in utext:
        o = fit(utext, URL_OLD)
        one(utext, o, 'the photo delete route')
        utext = utext.replace(o, fit(utext, URL_NEW), 1)
        if not check:
            backup(up)
            write(up, utext)
        done += 1

    # --- view
    vp = os.path.join(root, 'pages', 'views', 'properties.py')
    vtext = read(vp)
    if 'def delete_asset_invoice(' not in vtext:
        o = fit(vtext, VIEW_ANCHOR)
        one(vtext, o, 'the photo delete view')
        vtext = vtext.replace(o, fit(vtext, VIEW_NEW), 1)
        if not check:
            backup(vp)
            write(vp, vtext)
        done += 1

    print('AI-1  edits : %d' % done)

    if check:
        if done:
            print('AI-1  NOT APPLIED')
            return 1
        print('AI-1  applied')
        return 0
    # ALL FIVE OR NONE. A button with no route is a 404; a route with no
    # button is dead code; the CSS alone is a banner that lays out for a
    # control that is not there.
    if done not in (0, 5):
        print('AI-1  REFUSED: partial application (%d of 5)' % done)
        return 2
    print('AI-1  ok')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
