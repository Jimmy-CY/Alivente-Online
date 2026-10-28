# -*- coding: utf-8 -*-
"""apply_receipt_email.py - round CR-2, 27 Oct 2026.

RELEASE 29 - EMAILING A CASH RECEIPT. His decisions of 27 October, render
approved.

    - A paper-plane in each Receipts row (and Email receipt on Receipt
      Details), greyed without an email address, never live when void.
    - A confirmation pop-up: To, Cc, subject, the PDF, the exact message.
    - TO is the receipt's own address(es); the new "Cash Receipt to Payer"
      card adds any further To and any Cc. No card, the payer alone.
    - "Issued - Sent" once emailed; an edit afterwards puts it back to
      Issued. The history says who it went to.
    - Receipts gets its Help module: issuing, the list, emailing, details.
    - Branded like the e-signing emails, no contact details.

Stands on GS-1. Idempotent. Edits backed up to .bak_receiptemail; ships this
patcher, its suite and MIGRATION 0110 (CashReceipt.sent_to and the new
notification type) - run `python manage.py migrate` before the gate.
"""
import os
import re
import sys

SUFFIX = '.bak_receiptemail'
MARK = 'CR-2, 27 Oct 2026'
CHECK = False
CREATES = (
    'test_receipt_email.py',
    os.path.join('pages', 'migrations', '0110_notification_type_cash_receipt.py'),
)

PS1 = 'Push-PendingChanges.ps1'
TREE = 'alv_tree.py'
ROUNDS = 'alv_rounds.py'
WD = 'test_waiting_down.py'

SWAPS = [
    (os.path.join('pages', 'models.py'), [
        (r'''        ('physical_invoice_review', 'Physical Invoices Awaiting Approval'),
        ('physical_invoice_client', 'Physical Invoice to Client'),
        # THE 16TH, added by Section A round A1: who hears about it
        # when somebody asks for a password link. Configurable from
''',
         r'''        ('physical_invoice_review', 'Physical Invoices Awaiting Approval'),
        ('physical_invoice_client', 'Physical Invoice to Client'),
        # CR-2, 27 Oct 2026 - a cash receipt emailed to its payer. The
        # payer's own address is always a To; this card adds any further
        # To and any CC.
        ('cash_receipt_payer', 'Cash Receipt to Payer'),
        # THE 16TH, added by Section A round A1: who hears about it
        # when somebody asks for a password link. Configurable from
'''),
        (r'''
    sent_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True,
''',
         r'''
    sent_at = models.DateTimeField(null=True, blank=True)
    # CR-2, 27 Oct 2026 - WHO THE LAST EMAIL WENT TO, as sent (To and Cc),
    # so the history can say "Emailed to ..." rather than only "Emailed".
    sent_to = models.TextField(blank=True, default='',
        help_text='The addresses the receipt was last emailed to.')
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True,
'''),
        (r'''        return [l.strip() for l in (self.payer_address or '').splitlines()
                if l.strip()]

# ==========================================================================
''',
         r'''        return [l.strip() for l in (self.payer_address or '').splitlines()
                if l.strip()]

    # CR-2, 27 Oct 2026 - EMAILING A RECEIPT.
    @property
    def email_list(self):
        """The payer's addresses - comma or semicolon separated, deduped."""
        out, seen = [], set()
        for part in (self.payer_email or '').replace(';', ',').split(','):
            a = part.strip()
            if a and a.lower() not in seen:
                seen.add(a.lower())
                out.append(a)
        return out

    @property
    def is_sent(self):
        """Emailed, and not edited since - his decision of 27 October: an
        edit after sending puts the receipt back to plain Issued, so it is
        plain that the corrected copy has not gone out yet."""
        if not self.sent_at or self.is_void:
            return False
        return not self.edited_at or self.edited_at <= self.sent_at

# ==========================================================================
'''),
    ]),
    (os.path.join('pages', 'views', 'receipts.py'), [
        (r'''    # list is invisible to the URLconf no matter how correct it is.
    "cash_receipt_detail",
    "render_cash_receipt_pdf",
    "amount_in_words",
''',
         r'''    # list is invisible to the URLconf no matter how correct it is.
    "cash_receipt_detail",
    # CR-2, 27 Oct 2026 - emailing a receipt.
    "cash_receipt_send",
    "render_cash_receipt_pdf",
    "amount_in_words",
'''),
        (r'''        qs = qs.filter(is_void=True)

    rows = []
    for r in qs:
''',
         r'''        qs = qs.filter(is_void=True)

    card = _receipt_card()
    rows = []
    for r in qs:
'''),
        (r'''            'is_edited': bool(r.edited_at),
            'edited_display': r.edited_at.strftime('%Y-%m-%d') if r.edited_at else '',
            'status_pill': 'alv-pill-neutral' if r.is_void else 'alv-pill-good',
            'status_display': 'Void' if r.is_void else 'Issued',
            'has_pdf': bool(r.pdf_file),
            # A PLAIN STRING FOR THE BROWSER TO ADD UP. Written here with
            # %.2f rather than left to a template filter, so no locale and
''',
         r'''            'is_edited': bool(r.edited_at),
            'edited_display': r.edited_at.strftime('%Y-%m-%d') if r.edited_at else '',
            'status_pill': _status(r)[0],
            'status_display': _status(r)[1],
            'status_title': _status(r)[2],
            'has_pdf': bool(r.pdf_file),
            # CR-2, 27 Oct 2026 - what the email button needs: whether it
            # can send at all, and the To / Cc it WOULD use, worked out
            # here once so the pop-up shows exactly what Send will do.
            'can_send': bool(r.email_list) and not r.is_void,
            'send_to': ', '.join(_send_lists(r, card)[0]),
            'send_cc': ', '.join(_send_lists(r, card)[1]),
            'is_printed': r.doc_format == CashReceipt.FORMAT_PRINTED,
            'was_sent': bool(r.sent_at),
            'email_subject': receipt_email_text(r)[0],
            'email_body': receipt_email_text(r)[1],
            'amount_text': '%s %s' % (money_symbol(r.currency),
                                      _money(r.amount)),
            # A PLAIN STRING FOR THE BROWSER TO ADD UP. Written here with
            # %.2f rather than left to a template filter, so no locale and
'''),
        (r'''                      'tone': ''})
    if r.sent_at:
        trail.append({'what': 'Emailed', 'when': r.sent_at,
                      'who': '', 'note': '', 'tone': ''})
    if r.edited_at:
        trail.append({'what': 'Edited', 'when': r.edited_at,
''',
         r'''                      'tone': ''})
    if r.sent_at:
        # CR-2, 27 Oct 2026 - and to whom, now that it is recorded.
        trail.append({'what': 'Emailed', 'when': r.sent_at,
                      'who': '', 'note': ('to %s' % r.sent_to
                                          if r.sent_to else ''),
                      'tone': ''})
    if r.edited_at:
        trail.append({'what': 'Edited', 'when': r.edited_at,
'''),
        (r'''    trail.sort(key=lambda e: e['when'])

    return render(request, 'cash_receipt_detail.html', {
        'r': r,
        'trail': trail,
        # THE SAME TWO THE LIST ROW USES, from the same helper - a
        # second idea about what a void receipt is called is a second
        # thing to keep in agreement.
        'symbol': money_symbol(r.currency),
        'status_pill': 'alv-pill-neutral' if r.is_void else 'alv-pill-good',
        'status_display': 'Void' if r.is_void else 'Issued',
    })


''',
         r'''    trail.sort(key=lambda e: e['when'])

    card = _receipt_card()
    return render(request, 'cash_receipt_detail.html', {
        'r': r,
        'trail': trail,
        # THE SAME TWO THE LIST ROW USES, from the same helper - a
        # second idea about what a void receipt is called is a second
        # thing to keep in agreement.
        # CR-2, 27 Oct 2026 - from _status(), which the list uses too.
        'symbol': money_symbol(r.currency),
        'status_pill': _status(r)[0],
        'status_display': _status(r)[1],
        'can_send': bool(r.email_list) and not r.is_void,
        'send_to': ', '.join(_send_lists(r, card)[0]),
        'send_cc': ', '.join(_send_lists(r, card)[1]),
        'is_printed': r.doc_format == CashReceipt.FORMAT_PRINTED,
        'amount_text': '%s %s' % (money_symbol(r.currency), _money(r.amount)),
        'email_subject': receipt_email_text(r)[0],
        'email_body': receipt_email_text(r)[1],
    })


# ---------------------------------------------------------------- email
# CR-2, 27 Oct 2026 - EMAILING A RECEIPT. His decisions of 27 October:
#
#   - The paper-plane sits in the row beside Duplicate (and on the Receipt
#     Details bar), greyed while the receipt has no email address or is
#     void. A confirmation pop-up shows exactly who it goes to first.
#   - TO is always the receipt's own address(es). The "Cash Receipt to
#     Payer" card in Notification Settings adds any further To and any Cc;
#     with only a Cc set it goes To the payer, Cc the people named.
#   - Once sent the status reads "Issued - Sent". An edit afterwards puts
#     it back to Issued (CashReceipt.is_sent), so it is plain that the
#     corrected copy has not gone out yet. "Send again" is always there.
#   - Printed-format receipts may be emailed too, with a warning.
#   - The email is the e-signing kind: branded, the logo under the
#     sign-off, no contact details.
RECEIPT_CARD = 'cash_receipt_payer'


def _receipt_card():
    """(to, cc) from the Notification Settings card - empty if unset."""
    from pages.email_utils import get_email_recipients
    got = get_email_recipients(RECEIPT_CARD)
    return list(got.get('to') or []), list(got.get('cc') or [])


def _send_lists(r, card):
    """The To and Cc one send would use: the payer first, then the card;
    nobody twice, and nobody on Cc who is already on To."""
    to, seen = [], set()
    for a in list(r.email_list) + list(card[0]):
        if a.lower() not in seen:
            seen.add(a.lower())
            to.append(a)
    cc = []
    for a in card[1]:
        if a.lower() not in seen:
            seen.add(a.lower())
            cc.append(a)
    return to, cc


def _status(r):
    """(pill, words, hover) - one answer for the list and the details."""
    if r.is_void:
        return 'alv-pill-neutral', 'Void', ''
    if r.is_sent:
        return ('alv-pill-info', 'Issued \u00b7 Sent',
                'Emailed %s' % timezone.localtime(r.sent_at).strftime(
                    '%d %b %Y, %H:%M'))
    if r.sent_at:
        return ('alv-pill-good', 'Issued',
                'Edited after it was emailed - the corrected copy has not '
                'been sent')
    return 'alv-pill-good', 'Issued', ''


def receipt_email_text(r):
    """(subject, body) - the words of the email, also shown in the pop-up."""
    subject = 'Receipt %s - Alivente Limited' % r.receipt_number
    body = ('Dear %s,\n\n'
            'Please find attached receipt %s for %s %s, received on %s, '
            'being payment for %s.\n\n'
            'Kind regards,\n\nAlivente Limited'
            % (r.payer_name, r.receipt_number, money_symbol(r.currency),
               _money(r.amount), r.receipt_date.strftime('%d %B %Y'),
               (r.description or '').strip().rstrip('.')))
    return subject, body


@login_required
@permission_required('auth.can_edit_receipts', raise_exception=True)
@require_POST
def cash_receipt_send(request, cash_receipt_id):
    """Email the stored receipt PDF to its payer (and the card's people)."""
    from pages.services.lease_email import BrandedEmail
    r = get_object_or_404(CashReceipt, pk=cash_receipt_id)
    back = (redirect('cash_receipt_detail', cash_receipt_id=r.pk)
            if request.POST.get('next') == 'detail'
            else redirect('cash_receipt_list'))
    if r.is_void:
        messages.error(request, 'Receipt %s is void - it cannot be emailed.'
                       % r.receipt_number)
        return back
    to, cc = _send_lists(r, _receipt_card())
    if not r.email_list:
        messages.error(request, 'Receipt %s has no email address. Edit the '
                       'receipt and add one under Received from.'
                       % r.receipt_number)
        return back
    if not r.pdf_file:
        store_pdf(r)
        r.refresh_from_db()
    r.pdf_file.open('rb')
    try:
        pdf = r.pdf_file.read()
    finally:
        r.pdf_file.close()
    subject, body = receipt_email_text(r)
    msg = BrandedEmail(subject=subject, body=body, to=to, cc=cc)
    msg.attach('%s.pdf' % r.receipt_number, pdf, 'application/pdf')
    try:
        msg.send(fail_silently=False)
    except Exception as e:                                  # noqa: BLE001
        messages.error(request, 'Receipt %s was NOT sent - the mail server '
                       'said: %s' % (r.receipt_number, str(e)[:160]))
        return back
    sent_to = ', '.join(to) + ((' (cc %s)' % ', '.join(cc)) if cc else '')
    CashReceipt.objects.filter(pk=r.pk).update(sent_at=timezone.now(),
                                               sent_to=sent_to)
    messages.success(request, 'Receipt %s emailed to %s.'
                     % (r.receipt_number, sent_to))
    return back


'''),
    ]),
    (os.path.join('pages', 'views', 'notifications.py'), [
        (r'''        'physical_invoice_review',
        'physical_invoice_client',
        'expense_needs_approval',
        'expense_approved',
''',
         r'''        'physical_invoice_review',
        'physical_invoice_client',
        # CR-2, 27 Oct 2026 - its card, or the choice renders nowhere.
        'cash_receipt_payer',
        'expense_needs_approval',
        'expense_approved',
'''),
    ]),
    (os.path.join('pages', 'email_utils.py'), [
        (r'''        # catch-all silently moves this type too.
        'password_reset_requested': {'to': ['demetrimanias@gmail.com'], 'cc': []},
    }

''',
         r'''        # catch-all silently moves this type too.
        'password_reset_requested': {'to': ['demetrimanias@gmail.com'], 'cc': []},
        # CR-2, 27 Oct 2026 - NAMED AS EMPTY, not left to the catch-all:
        # with no card saved a receipt goes to its payer and nobody else.
        # The catch-all would quietly add a To on every receipt sent.
        'cash_receipt_payer': {'to': [], 'cc': []},
    }

'''),
    ]),
    (os.path.join('pages', 'urls.py'), [
        (r'''    path("receipts/<int:cash_receipt_id>/update/", views.cash_receipt_update, name="cash_receipt_update"),
    path("receipts/<int:cash_receipt_id>/pdf/", views.cash_receipt_pdf, name="cash_receipt_pdf"),

    # ============================================================================
''',
         r'''    path("receipts/<int:cash_receipt_id>/update/", views.cash_receipt_update, name="cash_receipt_update"),
    path("receipts/<int:cash_receipt_id>/pdf/", views.cash_receipt_pdf, name="cash_receipt_pdf"),
    # CR-2, 27 Oct 2026 - email the receipt to its payer.
    path("receipts/<int:cash_receipt_id>/send/", views.cash_receipt_send, name="cash_receipt_send"),

    # ============================================================================
'''),
    ]),
    (os.path.join('pages', 'templates', 'cash_receipts.html'), [
        (r'''            <td data-label="Amount" class="num">{{ row.symbol }} {{ row.amount|floatformat:2|intcomma }}</td>
            <td data-label="Status">
              <span class="alv-pill {{ row.status_pill }}">{{ row.status_display }}</span>
            </td>
            <td data-label="Actions" class="desktop-action-cell cell-actions">
''',
         r'''            <td data-label="Amount" class="num">{{ row.symbol }} {{ row.amount|floatformat:2|intcomma }}</td>
            <td data-label="Status">
              <span class="alv-pill {{ row.status_pill }}"{% if row.status_title %} title="{{ row.status_title }}"{% endif %}>{{ row.status_display }}</span>
            </td>
            <td data-label="Actions" class="desktop-action-cell cell-actions">
'''),
        (r'''                  </span>
                {% endif %}
                {% if row.is_void and perms.auth.can_edit_receipts %}
                  <form method="post" action="{% url 'cash_receipt_unvoid' row.pk %}"
''',
         r'''                  </span>
                {% endif %}
                {# CR-2, 27 Oct 2026 - EMAIL IT. Grey until the receipt has an #}
                {# email address; never on a void one. ADVANCE, before Void.  #}
                {% if row.can_send and perms.auth.can_edit_receipts %}
                  <button type="button" class="icon-action-btn icon-send"
                          title="{% if row.was_sent %}Email this receipt again{% else %}Email this receipt{% endif %}"
                          data-url="{% url 'cash_receipt_send' row.pk %}" data-number="{{ row.number }}"
                          data-to="{{ row.send_to }}" data-cc="{{ row.send_cc }}"
                          data-subject="{{ row.email_subject }}" data-body="{{ row.email_body }}"
                          data-printed="{% if row.is_printed %}1{% endif %}" data-sent="{% if row.was_sent %}1{% endif %}"
                          onclick="return openReceiptSend(this, '');">
                    <i class="fas fa-paper-plane"></i>
                  </button>
                {% else %}
                  <span class="icon-action-btn icon-disabled"
                        title="{% if row.is_void %}A void receipt is not emailed{% elif not perms.auth.can_edit_receipts %}No permission to email receipts{% else %}No email address - edit the receipt to add one{% endif %}">
                    <i class="fas fa-paper-plane"></i>
                  </span>
                {% endif %}
                {% if row.is_void and perms.auth.can_edit_receipts %}
                  <form method="post" action="{% url 'cash_receipt_unvoid' row.pk %}"
'''),
        (r'''
            <!-- Mobile-only action bar -->
            <td class="mobile-action-bar cols-4">
              <a href="{% url 'cash_receipt_pdf' row.pk %}"
                 onclick="openPdfViewer('{% url 'cash_receipt_pdf' row.pk %}', 'Receipt {{ row.number|escapejs }} &mdash; {{ row.payer|escapejs }}', '{{ row.number|escapejs }}.pdf'); return false;"
''',
         r'''
            <!-- Mobile-only action bar -->
            <td class="mobile-action-bar cols-5">
              <a href="{% url 'cash_receipt_pdf' row.pk %}"
                 onclick="openPdfViewer('{% url 'cash_receipt_pdf' row.pk %}', 'Receipt {{ row.number|escapejs }} &mdash; {{ row.payer|escapejs }}', '{{ row.number|escapejs }}.pdf'); return false;"
'''),
        (r'''                  <i class="fas fa-copy mobile-action-icon"></i>
                  <span class="mobile-action-label">Duplicate</span>
                </span>
              {% endif %}
''',
         r'''                  <i class="fas fa-copy mobile-action-icon"></i>
                  <span class="mobile-action-label">Duplicate</span>
                </span>
              {% endif %}
              {% if row.can_send and perms.auth.can_edit_receipts %}
                <button type="button" class="mobile-action-btn"
                        data-url="{% url 'cash_receipt_send' row.pk %}" data-number="{{ row.number }}"
                        data-to="{{ row.send_to }}" data-cc="{{ row.send_cc }}"
                        data-subject="{{ row.email_subject }}" data-body="{{ row.email_body }}"
                        data-printed="{% if row.is_printed %}1{% endif %}" data-sent="{% if row.was_sent %}1{% endif %}"
                        onclick="return openReceiptSend(this, '');">
                  <i class="fas fa-paper-plane mobile-action-icon icon-color-view"></i>
                  <span class="mobile-action-label">Email</span>
                </button>
              {% else %}
                <span class="mobile-action-btn mobile-action-disabled">
                  <i class="fas fa-paper-plane mobile-action-icon"></i>
                  <span class="mobile-action-label">Email</span>
                </span>
              {% endif %}
'''),
        (r'''</script>

{% endblock %}
''',
         r'''</script>

{# EMAIL THIS RECEIPT - CR-2, 27 Oct 2026. One pop-up, filled from the #}
{# button that opened it, showing exactly who Send will reach.         #}
<div class="modal fade" id="receiptSendModal" tabindex="-1" role="dialog"
     aria-labelledby="receiptSendTitle" aria-hidden="true" style="display:none;">
  <div class="modal-dialog modal-lg" role="document">
    <div class="modal-content">
      <form method="post" id="rsm-form" action="">
        {% csrf_token %}
        <input type="hidden" name="next" id="rsm-next" value="">
        <div class="modal-header alv-modal-head">
          <h5 class="modal-title" id="receiptSendTitle"><i class="fas fa-paper-plane"></i> Email receipt <span id="rsm-number"></span></h5>
          <button type="button" class="close" data-dismiss="modal" aria-label="Close">
            <span aria-hidden="true">&times;</span>
          </button>
        </div>
        <div class="modal-body rsm-body">
          <div class="rsm-row"><span class="rsm-label">To</span><span class="rsm-value" id="rsm-to"></span></div>
          <div class="rsm-row" id="rsm-cc-row"><span class="rsm-label">Cc</span><span class="rsm-value" id="rsm-cc"></span></div>
          <div class="rsm-row"><span class="rsm-label">Subject</span><span class="rsm-value" id="rsm-subject"></span></div>
          <div class="rsm-row"><span class="rsm-label">Attached</span><span class="rsm-value"><i class="fas fa-file-pdf"></i> <span id="rsm-file"></span></span></div>
          <div class="rsm-message" id="rsm-body"></div>
          <div class="rsm-note" id="rsm-printed"><i class="fas fa-exclamation-triangle"></i> This receipt is in the <strong>Printed</strong> format, with signature and date lines. It will be sent exactly as it is.</div>
          <div class="rsm-note" id="rsm-again"><i class="fas fa-info-circle"></i> This receipt has been emailed before. Send it again?</div>
          <div class="rsm-hint">Who else receives receipts is set in <strong>Administration &rsaquo; Notification Settings &rsaquo; Cash Receipt to Payer</strong>.</div>
        </div>
        <div class="modal-footer">
          <button type="button" class="btn action-secondary" data-dismiss="modal">Cancel</button>
          <button type="submit" class="btn action-primary" id="rsm-send"><i class="fas fa-paper-plane"></i> Send</button>
        </div>
      </form>
    </div>
  </div>
</div>
<style>
/* CR-2, 27 Oct 2026 - the email pop-up. Tokens only. */
.rsm-body { font-size: 14px; }
.rsm-row { display: flex; gap: 12px; padding: 6px 0; border-bottom: 1px solid var(--alv-line); }
.rsm-label { min-width: 70px; font-weight: 600; color: var(--alv-ink); }
.rsm-value { flex: 1 1 auto; min-width: 0; overflow-wrap: anywhere; color: var(--alv-ink-strong); }
.rsm-message { white-space: pre-line; margin: 12px 0; padding: 12px 14px; border: 1px solid var(--alv-line); border-radius: var(--alv-radius-sm, 6px); background: var(--alv-surface); color: var(--alv-ink-strong); }
.rsm-note { margin: 8px 0; padding: 9px 12px; border-left: 4px solid var(--alv-warn); background: var(--alv-warn-soft); color: var(--alv-ink); border-radius: var(--alv-radius-sm, 6px); }
.rsm-hint { margin-top: 10px; font-size: 12.5px; color: var(--alv-ink-soft, var(--alv-ink)); }
</style>
<script>
(function () {
  // Fill the pop-up from the button's data-* and open it. The server
  // decides who is written on those attributes; this only shows them.
  window.openReceiptSend = function (btn, next) {
    var d = btn.dataset, el = function (id) { return document.getElementById(id); };
    el('rsm-form').action = d.url;
    el('rsm-next').value = next || '';
    el('rsm-number').textContent = d.number;
    el('rsm-to').textContent = d.to;
    el('rsm-cc').textContent = d.cc;
    el('rsm-cc-row').style.display = d.cc ? '' : 'none';
    el('rsm-subject').textContent = d.subject;
    el('rsm-file').textContent = d.number + '.pdf';
    el('rsm-body').textContent = d.body;
    el('rsm-printed').style.display = d.printed === '1' ? '' : 'none';
    el('rsm-again').style.display = d.sent === '1' ? '' : 'none';
    el('rsm-send').innerHTML = '<i class="fas fa-paper-plane"></i> ' + (d.sent === '1' ? 'Send again' : 'Send');
    if (window.jQuery) { window.jQuery('#receiptSendModal').modal('show'); }
    return false;
  };
  var f = document.getElementById('rsm-form');
  if (f) {
    f.addEventListener('submit', function () {
      var b = document.getElementById('rsm-send');
      b.disabled = true;
      b.innerHTML = '<i class="fas fa-paper-plane"></i> Sending...';
    });
  }
})();
</script>

{% endblock %}
'''),
    ]),
    (os.path.join('pages', 'templates', 'cash_receipt_detail.html'), [
        (r'''        <i class="fas fa-pencil-alt"></i> Edit
    </a>
    {% endif %}
    <a href="{% url 'cash_receipt_list' %}" class="btn action-back"
''',
         r'''        <i class="fas fa-pencil-alt"></i> Edit
    </a>
    {% endif %}
    {# CR-2, 27 Oct 2026 - email it, through the same pop-up as the list. #}
    {% if perms.auth.can_edit_receipts and not r.is_void %}
    {% if can_send %}
    <button type="button" class="btn action-secondary"
            data-url="{% url 'cash_receipt_send' r.pk %}" data-number="{{ r.receipt_number }}"
            data-to="{{ send_to }}" data-cc="{{ send_cc }}"
            data-subject="{{ email_subject }}" data-body="{{ email_body }}"
            data-printed="{% if is_printed %}1{% endif %}" data-sent="{% if r.sent_at %}1{% endif %}"
            onclick="return openReceiptSend(this, 'detail');">
        <i class="fas fa-paper-plane"></i> {% if r.sent_at %}Email again{% else %}Email receipt{% endif %}
    </button>
    {% else %}
    <span class="btn action-secondary disabled-btn" title="No email address - edit the receipt to add one">
        <i class="fas fa-paper-plane"></i> Email receipt
    </span>
    {% endif %}
    {% endif %}
    <a href="{% url 'cash_receipt_list' %}" class="btn action-back"
'''),
        (r'''}
</style>
{% endblock %}
''',
         r'''}
</style>
{# EMAIL THIS RECEIPT - CR-2, 27 Oct 2026. One pop-up, filled from the #}
{# button that opened it, showing exactly who Send will reach.         #}
<div class="modal fade" id="receiptSendModal" tabindex="-1" role="dialog"
     aria-labelledby="receiptSendTitle" aria-hidden="true" style="display:none;">
  <div class="modal-dialog modal-lg" role="document">
    <div class="modal-content">
      <form method="post" id="rsm-form" action="">
        {% csrf_token %}
        <input type="hidden" name="next" id="rsm-next" value="">
        <div class="modal-header alv-modal-head">
          <h5 class="modal-title" id="receiptSendTitle"><i class="fas fa-paper-plane"></i> Email receipt <span id="rsm-number"></span></h5>
          <button type="button" class="close" data-dismiss="modal" aria-label="Close">
            <span aria-hidden="true">&times;</span>
          </button>
        </div>
        <div class="modal-body rsm-body">
          <div class="rsm-row"><span class="rsm-label">To</span><span class="rsm-value" id="rsm-to"></span></div>
          <div class="rsm-row" id="rsm-cc-row"><span class="rsm-label">Cc</span><span class="rsm-value" id="rsm-cc"></span></div>
          <div class="rsm-row"><span class="rsm-label">Subject</span><span class="rsm-value" id="rsm-subject"></span></div>
          <div class="rsm-row"><span class="rsm-label">Attached</span><span class="rsm-value"><i class="fas fa-file-pdf"></i> <span id="rsm-file"></span></span></div>
          <div class="rsm-message" id="rsm-body"></div>
          <div class="rsm-note" id="rsm-printed"><i class="fas fa-exclamation-triangle"></i> This receipt is in the <strong>Printed</strong> format, with signature and date lines. It will be sent exactly as it is.</div>
          <div class="rsm-note" id="rsm-again"><i class="fas fa-info-circle"></i> This receipt has been emailed before. Send it again?</div>
          <div class="rsm-hint">Who else receives receipts is set in <strong>Administration &rsaquo; Notification Settings &rsaquo; Cash Receipt to Payer</strong>.</div>
        </div>
        <div class="modal-footer">
          <button type="button" class="btn action-secondary" data-dismiss="modal">Cancel</button>
          <button type="submit" class="btn action-primary" id="rsm-send"><i class="fas fa-paper-plane"></i> Send</button>
        </div>
      </form>
    </div>
  </div>
</div>
<style>
/* CR-2, 27 Oct 2026 - the email pop-up. Tokens only. */
.rsm-body { font-size: 14px; }
.rsm-row { display: flex; gap: 12px; padding: 6px 0; border-bottom: 1px solid var(--alv-line); }
.rsm-label { min-width: 70px; font-weight: 600; color: var(--alv-ink); }
.rsm-value { flex: 1 1 auto; min-width: 0; overflow-wrap: anywhere; color: var(--alv-ink-strong); }
.rsm-message { white-space: pre-line; margin: 12px 0; padding: 12px 14px; border: 1px solid var(--alv-line); border-radius: var(--alv-radius-sm, 6px); background: var(--alv-surface); color: var(--alv-ink-strong); }
.rsm-note { margin: 8px 0; padding: 9px 12px; border-left: 4px solid var(--alv-warn); background: var(--alv-warn-soft); color: var(--alv-ink); border-radius: var(--alv-radius-sm, 6px); }
.rsm-hint { margin-top: 10px; font-size: 12.5px; color: var(--alv-ink-soft, var(--alv-ink)); }
</style>
<script>
(function () {
  // Fill the pop-up from the button's data-* and open it. The server
  // decides who is written on those attributes; this only shows them.
  window.openReceiptSend = function (btn, next) {
    var d = btn.dataset, el = function (id) { return document.getElementById(id); };
    el('rsm-form').action = d.url;
    el('rsm-next').value = next || '';
    el('rsm-number').textContent = d.number;
    el('rsm-to').textContent = d.to;
    el('rsm-cc').textContent = d.cc;
    el('rsm-cc-row').style.display = d.cc ? '' : 'none';
    el('rsm-subject').textContent = d.subject;
    el('rsm-file').textContent = d.number + '.pdf';
    el('rsm-body').textContent = d.body;
    el('rsm-printed').style.display = d.printed === '1' ? '' : 'none';
    el('rsm-again').style.display = d.sent === '1' ? '' : 'none';
    el('rsm-send').innerHTML = '<i class="fas fa-paper-plane"></i> ' + (d.sent === '1' ? 'Send again' : 'Send');
    if (window.jQuery) { window.jQuery('#receiptSendModal').modal('show'); }
    return false;
  };
  var f = document.getElementById('rsm-form');
  if (f) {
    f.addEventListener('submit', function () {
      var b = document.getElementById('rsm-send');
      b.disabled = true;
      b.innerHTML = '<i class="fas fa-paper-plane"></i> Sending...';
    });
  }
})();
</script>

{% endblock %}
'''),
    ]),
    (os.path.join('pages', 'templates', 'notification_settings.html'), [
        (r'''            >{{ notification_settings.physical_invoice_client.cc_emails }}</textarea>
            <div class="field-hint">Copied on every client invoice (e.g. your accounts mailbox)</div>
        </div>

''',
         r'''            >{{ notification_settings.physical_invoice_client.cc_emails }}</textarea>
            <div class="field-hint">Copied on every client invoice (e.g. your accounts mailbox)</div>
        </div>

        <button type="submit" class="btn action-primary">
            <i class="fas fa-save"></i> Save
        </button>
    </form>
</div>

<!-- Cash Receipt to Payer - CR-2, 27 Oct 2026 -->
<div class="notification-card form-card">
    <h3 class="form-section-title"><i class="fas fa-envelope-open-text"></i> Cash Receipt to Payer</h3>
    <p class="text-muted">A cash receipt emailed from Receipts. It always goes to the receipt's own email address (Received from &rsaquo; Email); add anyone else who should receive it below.</p>

    <form method="post">
        {% csrf_token %}
        <input type="hidden" name="notification_type" value="cash_receipt_payer">

        <div class="form-group">
            <label><strong>TO: Additional Recipients (optional)</strong></label>
            <textarea
                class="form-control"
                name="to_addresses"
                rows="2"
                placeholder="email1@example.com, email2@example.com"
            >{{ notification_settings.cash_receipt_payer.to_emails }}</textarea>
            <div class="field-hint">Added to the To line beside the payer. Leave blank to send To the payer only.</div>
        </div>

        <div class="form-group">
            <label><strong>CC: Carbon Copy Recipients (optional)</strong></label>
            <textarea
                class="form-control"
                name="cc_addresses"
                rows="2"
                placeholder="email1@example.com, email2@example.com"
            >{{ notification_settings.cash_receipt_payer.cc_emails }}</textarea>
            <div class="field-hint">Copied on every receipt emailed (e.g. your own address, for the record)</div>
        </div>

'''),
    ]),
    (os.path.join('pages', 'templates', 'base.html'), [
        (r'''        .mobile-action-bar.cols-2 { grid-template-columns: repeat(2, 1fr); }
        .mobile-action-bar.cols-4 { grid-template-columns: repeat(4, 1fr); }

    /* A ROW ACTION THAT POSTS IS WRAPPED IN A FORM - 30 Sep 2026.
''',
         r'''        .mobile-action-bar.cols-2 { grid-template-columns: repeat(2, 1fr); }
        .mobile-action-bar.cols-4 { grid-template-columns: repeat(4, 1fr); }
        /* CR-2, 27 Oct 2026 - Receipts: View, Edit, Duplicate, Email, Void. */
        .mobile-action-bar.cols-5 { grid-template-columns: repeat(5, 1fr); }

    /* A ROW ACTION THAT POSTS IS WRAPPED IN A FORM - 30 Sep 2026.
'''),
    ]),
    (os.path.join('test_cash_receipts.py'), [
        (r'''             'cash_receipt_unvoid', 'cash_receipt_pdf',
             # RV-1, 23 Oct 2026 - the record behind the receipt. G2.
             'cash_receipt_detail'}
# Was five. The edit/unvoid round added edit, update and unvoid, so the floor
# moved with the decision - and it names them rather than counting, because a
''',
         r'''             'cash_receipt_unvoid', 'cash_receipt_pdf',
             # RV-1, 23 Oct 2026 - the record behind the receipt. G2.
             'cash_receipt_detail',
             # CR-2, 27 Oct 2026 - email the receipt to its payer.
             'cash_receipt_send'}
# Was five. The edit/unvoid round added edit, update and unvoid, so the floor
# moved with the decision - and it names them rather than counting, because a
'''),
        (r'''check('  and carries the share sheet that reaches WhatsApp on a phone',
      'navigator.share' in read(os.path.join(TPL, 'components', 'pdf_viewer.html')))
check('four actions, so the mobile bar declares four columns',
      'mobile-action-bar cols-4' in LIST_T and 'cols-2' not in LIST_T)
check('  and base defines cols-4', '.mobile-action-bar.cols-4' in css_of(BASE))


''',
         r'''check('  and carries the share sheet that reaches WhatsApp on a phone',
      'navigator.share' in read(os.path.join(TPL, 'components', 'pdf_viewer.html')))
# CR-2, 27 Oct 2026 - FIVE: View, Edit, Duplicate, Email, Void.
check('five actions, so the mobile bar declares five columns',
      'mobile-action-bar cols-5' in LIST_T and 'cols-2' not in LIST_T)
check('  and base defines cols-5', '.mobile-action-bar.cols-5' in css_of(BASE))


'''),
    ]),
    (os.path.join('test_bar_height.py'), [
        (r'''
BAR, ROW, MODAL = 35, 34, 38
N_BAR, N_ROW, N_MODAL = 283, 120, 95   # ES-9, 26 Oct 2026 - the envelope page draws a greyed Approve and attach when no tenancy is free to receive the lease; both arms of the if count.   # (was 282, 120)   # HK-1, 26 Oct 2026 - the paper-plane left Manage Lease Agreements, his decision; both arms of its superuser check counted, so the row figure falls by two.   # (was 282, 122)   # ES-8, 25 Oct 2026 - the Lease Signing register gains a Help secondary in its bar, and a View-signed-lease icon in its row actions.   # (was 281, 121)   # ES-7, 25 Oct 2026 - the Signature and Stamp screen's bar, Back alone.   # (was 280)   # ES-6, 25 Oct 2026 - the envelope page's bar (Approve and attach, Decline, View signed lease, Back). This census does not resolve a branch, so Approve and Decline count even though they only show while an envelope is awaiting approval.   # (was 276)   # ES-3b, 24 Oct 2026 - the Send for Signature screen (Create and sign, Back) and the Send row action on Manage Lease Agreements. This census does not resolve a branch, so both arms of the perms check count - which is why the row figure moved by two and not by one.   # (was 274, 119)   # ES-3a, 23 Oct 2026 - lease_signing_list.html, the envelope register. An ordinary pages/templates page, so it joins every tree-wide count.   # (was 270, 116)   # RV-1, 23 Oct 2026 - the Receipt Details bar: View receipt, Edit and Back. A new PAGE, so three controls join the census without any existing bar changing.   # (was 267)   # TD-2, 16 Oct 2026 - the two disabled twins. A twin is an .icon-action-btn in a table row, so this census counts it exactly as it counts the button it stands in for - which is the whole idea.   # (was 114)   # NV-1d, 16 Oct 2026 - the View button in the desktop strip, which is inside a table.   # (was 113)   # NV-1c, 16 Oct 2026 - the physical invoice disabled mirror, in the desktop strip, which is inside a table.   # (was 112)   # NV-1b, 16 Oct 2026 - the title deeds Actions cell drew two Bootstrap buttons, which this census cannot see. They are icon-delete and icon-upload now, so two controls join the table-row count without a control being added.   # (was 110)   # PJ-1, 15 Oct 2026 - projects_edit carried its Back control twice, behind an if on from_gantt. This census does not resolve a branch, so it counted both arms; one Back control now, and one count.   # (was 268)   # PV-1, 15 Oct 2026 - the four footer buttons of two hand-rolled invoice viewers. The shared component they moved onto was already in this census, so the count falls by exactly the four that went.   # (was 99)   # VC-1, 14 Oct 2026 - property_assets Take Photo is a <label> that had no house class until this round, so this census could not see it. 35px, in a modal, and named in STRAYS below.   # (was 98)   # DB-5, 12 Oct 2026 - the
# dashboard four joined the bar   # (was 265)   # E-10, 11 Oct 2026 - the
# seven buttons this round paired in CRS modals become visible to
# a census that selects the two position tones and not the danger
# tone.   # (was 91)
N_LOOSE, N_LOOSE_H = 92, 11   # LS-1, 27 Oct 2026 - Include finished and Back in the Lease Signing Status report head, at heights the set already held.   # (was 90)   # ES-7b, 25 Oct 2026 - the Delete envelope button in its own card on the envelope page, at a height already in the set.   # (was 89)   # ES-7, 25 Oct 2026 - the two Save buttons on the Signature and Stamp cards, at a height already in the set.   # (was 87)   # ES-3b, 24 Oct 2026 - Choose a different tenant, which sits in a form card rather than in the action bar. N_LOOSE_H does not move: 35px is a height this set already held.   # (was 86)   # LV-1, 16 Oct 2026 - three of the 25 retoned buttons sit in a card or loose on a page. This census selects on a house class, so it could not see them while a LEAVE entry was keeping them Bootstrap-coloured. N_LOOSE_H does not move - all three land on heights the set already held.   # (was 83)   # NV-1c, 16 Oct 2026 - the two comment controls. They were .status-btn, which this census does not select, and they sit in a comment thread rather than a table, so they land in the loose set. 34px was already one of its eleven heights, so N_LOOSE_H does not move.   # (was 81)   # VC-1, 14 Oct 2026 - edit_asset Take Photo at 35px and my_profile Upload Photo at 31px, both <label> file pickers that had no house class until this round. 35 is a height this set did not hold before.   # (was 80 and 10)   # DB-5 - the side column left the
# loose set, and the two heights it invented went with it
# (was 82 and 12)   # E-10 - and the four loose in
''',
         r'''
BAR, ROW, MODAL = 35, 34, 38
N_BAR, N_ROW, N_MODAL = 285, 122, 99   # CR-2, 27 Oct 2026 - emailing a receipt: Email receipt in the Receipt Details bar (both arms of its if), the paper-plane in the Receipts row (live and greyed), and Cancel and Send in the pop-up on both pages.   # (was 283, 120, 95)   # ES-9, 26 Oct 2026 - the envelope page draws a greyed Approve and attach when no tenancy is free to receive the lease; both arms of the if count.   # (was 282, 120)   # HK-1, 26 Oct 2026 - the paper-plane left Manage Lease Agreements, his decision; both arms of its superuser check counted, so the row figure falls by two.   # (was 282, 122)   # ES-8, 25 Oct 2026 - the Lease Signing register gains a Help secondary in its bar, and a View-signed-lease icon in its row actions.   # (was 281, 121)   # ES-7, 25 Oct 2026 - the Signature and Stamp screen's bar, Back alone.   # (was 280)   # ES-6, 25 Oct 2026 - the envelope page's bar (Approve and attach, Decline, View signed lease, Back). This census does not resolve a branch, so Approve and Decline count even though they only show while an envelope is awaiting approval.   # (was 276)   # ES-3b, 24 Oct 2026 - the Send for Signature screen (Create and sign, Back) and the Send row action on Manage Lease Agreements. This census does not resolve a branch, so both arms of the perms check count - which is why the row figure moved by two and not by one.   # (was 274, 119)   # ES-3a, 23 Oct 2026 - lease_signing_list.html, the envelope register. An ordinary pages/templates page, so it joins every tree-wide count.   # (was 270, 116)   # RV-1, 23 Oct 2026 - the Receipt Details bar: View receipt, Edit and Back. A new PAGE, so three controls join the census without any existing bar changing.   # (was 267)   # TD-2, 16 Oct 2026 - the two disabled twins. A twin is an .icon-action-btn in a table row, so this census counts it exactly as it counts the button it stands in for - which is the whole idea.   # (was 114)   # NV-1d, 16 Oct 2026 - the View button in the desktop strip, which is inside a table.   # (was 113)   # NV-1c, 16 Oct 2026 - the physical invoice disabled mirror, in the desktop strip, which is inside a table.   # (was 112)   # NV-1b, 16 Oct 2026 - the title deeds Actions cell drew two Bootstrap buttons, which this census cannot see. They are icon-delete and icon-upload now, so two controls join the table-row count without a control being added.   # (was 110)   # PJ-1, 15 Oct 2026 - projects_edit carried its Back control twice, behind an if on from_gantt. This census does not resolve a branch, so it counted both arms; one Back control now, and one count.   # (was 268)   # PV-1, 15 Oct 2026 - the four footer buttons of two hand-rolled invoice viewers. The shared component they moved onto was already in this census, so the count falls by exactly the four that went.   # (was 99)   # VC-1, 14 Oct 2026 - property_assets Take Photo is a <label> that had no house class until this round, so this census could not see it. 35px, in a modal, and named in STRAYS below.   # (was 98)   # DB-5, 12 Oct 2026 - the
# dashboard four joined the bar   # (was 265)   # E-10, 11 Oct 2026 - the
# seven buttons this round paired in CRS modals become visible to
# a census that selects the two position tones and not the danger
# tone.   # (was 91)
N_LOOSE, N_LOOSE_H = 93, 11   # CR-2, 27 Oct 2026 - the Save on the Cash Receipt to Payer card, at a height the set already held.   # (was 92)   # LS-1, 27 Oct 2026 - Include finished and Back in the Lease Signing Status report head, at heights the set already held.   # (was 90)   # ES-7b, 25 Oct 2026 - the Delete envelope button in its own card on the envelope page, at a height already in the set.   # (was 89)   # ES-7, 25 Oct 2026 - the two Save buttons on the Signature and Stamp cards, at a height already in the set.   # (was 87)   # ES-3b, 24 Oct 2026 - Choose a different tenant, which sits in a form card rather than in the action bar. N_LOOSE_H does not move: 35px is a height this set already held.   # (was 86)   # LV-1, 16 Oct 2026 - three of the 25 retoned buttons sit in a card or loose on a page. This census selects on a house class, so it could not see them while a LEAVE entry was keeping them Bootstrap-coloured. N_LOOSE_H does not move - all three land on heights the set already held.   # (was 83)   # NV-1c, 16 Oct 2026 - the two comment controls. They were .status-btn, which this census does not select, and they sit in a comment thread rather than a table, so they land in the loose set. 34px was already one of its eleven heights, so N_LOOSE_H does not move.   # (was 81)   # VC-1, 14 Oct 2026 - edit_asset Take Photo at 35px and my_profile Upload Photo at 31px, both <label> file pickers that had no house class until this round. 35 is a height this set did not hold before.   # (was 80 and 10)   # DB-5 - the side column left the
# loose set, and the two heights it invented went with it
# (was 82 and 12)   # E-10 - and the four loose in
'''),
    ]),
    (os.path.join('test_drift_root.py'), [
        (r'''                   'crs/submission_list.html')
CRS_N = 8
N_FOOTER_SUBSTRING, N_FOOTER_TOKEN = 89, 88   # CP-2, 21 Oct 2026 - three dialogs leave the planner and two arrive, so one .modal-footer wrapper goes. BOTH matchers fall by the same one, which is what an ordinary wrapper does and is the point of keeping the pair.   # (was 90, 89)   # RD-1 and RD-2, 19 Oct 2026 - the recipe quick-look dialog and the Move dialog each bring one .modal-footer. BOTH matchers rise by the same 2, which is what an ordinary wrapper does.   # (was 88, 87)   # MO-1, 19 Oct 2026 - two more dialogs on the planner - a planned night, and leftovers. Both matchers rise by the same 2, which is what an ordinary wrapper does.   # (was 86, 85)   # MW-1, 19 Oct 2026 - the planner gains three dialogs - copy a week, save a Menu, apply a Menu - and each brings one .modal-footer. Both matchers rise by the same 3, which is what an ordinary wrapper does.   # (was 83, 82)   # RT-1, 18 Oct 2026 - six .modal-footer wrappers went with the four meal-plan screens MN-1 retired, and the planner brought none. BOTH matchers fall by the same six, which is the point of keeping the pair: the wrappers that left were ordinary ones.   # (was 89, 88)   # CC-2, 17 Oct 2026 - the contact detail modal adds one .modal-footer. Both matchers rise by the same one.   # (was 88, 87)   # CC-1, 15 Oct 2026 - the celebration day sheet adds one .modal-footer. Both matchers rise by the same one.   # (was 87, 86)   # PV-1, 15 Oct 2026 - two hand-rolled invoice viewers went, and each took one .modal-footer wrapper with it. Both matchers fall by the same two, which is itself the point: the wrappers that left were ordinary ones.   # (was 89, 88)
GREY = 'rgb(233, 236, 239)'
GREY_INK = 'rgb(138, 151, 157)'
''',
         r'''                   'crs/submission_list.html')
CRS_N = 8
N_FOOTER_SUBSTRING, N_FOOTER_TOKEN = 91, 90   # CR-2, 27 Oct 2026 - the receipt email pop-up brings one .modal-footer to Receipts and one to Receipt Details. Both matchers rise by the same two.   # (was N_FOOTER_SUBSTRING, N_FOOTER_TOKEN = 89, 88)   # CP-2, 21 Oct 2026 - three dialogs leave the planner and two arrive, so one .modal-footer wrapper goes. BOTH matchers fall by the same one, which is what an ordinary wrapper does and is the point of keeping the pair.   # (was 90, 89)   # RD-1 and RD-2, 19 Oct 2026 - the recipe quick-look dialog and the Move dialog each bring one .modal-footer. BOTH matchers rise by the same 2, which is what an ordinary wrapper does.   # (was 88, 87)   # MO-1, 19 Oct 2026 - two more dialogs on the planner - a planned night, and leftovers. Both matchers rise by the same 2, which is what an ordinary wrapper does.   # (was 86, 85)   # MW-1, 19 Oct 2026 - the planner gains three dialogs - copy a week, save a Menu, apply a Menu - and each brings one .modal-footer. Both matchers rise by the same 3, which is what an ordinary wrapper does.   # (was 83, 82)   # RT-1, 18 Oct 2026 - six .modal-footer wrappers went with the four meal-plan screens MN-1 retired, and the planner brought none. BOTH matchers fall by the same six, which is the point of keeping the pair: the wrappers that left were ordinary ones.   # (was 89, 88)   # CC-2, 17 Oct 2026 - the contact detail modal adds one .modal-footer. Both matchers rise by the same one.   # (was 88, 87)   # CC-1, 15 Oct 2026 - the celebration day sheet adds one .modal-footer. Both matchers rise by the same one.   # (was 87, 86)   # PV-1, 15 Oct 2026 - two hand-rolled invoice viewers went, and each took one .modal-footer wrapper with it. Both matchers fall by the same two, which is itself the point: the wrappers that left were ordinary ones.   # (was 89, 88)
GREY = 'rgb(233, 236, 239)'
GREY_INK = 'rgb(138, 151, 157)'
'''),
    ]),
    (os.path.join('test_recipe_side_b.py'), [
        (r'''# weaker, which is why this count is read and not frozen.
N_NAV_RULE_HITS, N_NAV_RULE_PRIMARY = 12, 10   # PP-1, 20 Oct 2026 - the planner leaves the set. The rule needs a bar whose only non-Back item is a link, and the planner bar now holds Print as well as Shopping List.   # (was 13, 11)   # (was 12, 10)
N_COND_LABEL, N_COND_LABEL_PRIMARY = 9, 7

# Buttons the scan cannot see at all: no Bootstrap colour it LISTS, no
''',
         r'''# weaker, which is why this count is read and not frozen.
N_NAV_RULE_HITS, N_NAV_RULE_PRIMARY = 12, 10   # PP-1, 20 Oct 2026 - the planner leaves the set. The rule needs a bar whose only non-Back item is a link, and the planner bar now holds Print as well as Shopping List.   # (was 13, 11)   # (was 12, 10)
N_COND_LABEL, N_COND_LABEL_PRIMARY = 10, 7   # CR-2, 27 Oct 2026 - Email again / Email receipt on Receipt Details, a secondary  # (was 9, 7)

# Buttons the scan cannot see at all: no Bootstrap colour it LISTS, no
'''),
    ]),
    (os.path.join('test_recipe_tones.py'), [
        (r'''# carry action-primary the same way. A count keyed on the exact class
# string undercounts every page that added a hook of its own.
SWEPT_CANCELS, SWEPT_DANGER, SWEPT_PRIMARY = 55, 14, 30   # PV-1, 15 Oct 2026 - two hand-rolled invoice viewers retired, each with a Close and a Download. The danger count is unchanged: neither had a destructive button in it.   # (was 57, 14, 32)
CONVERTED_NOW, WAITING_NOW, CEILING_NOW, ALIAS_NOW = 73, 2, 38, 57

''',
         r'''# carry action-primary the same way. A count keyed on the exact class
# string undercounts every page that added a hook of its own.
SWEPT_CANCELS, SWEPT_DANGER, SWEPT_PRIMARY = 57, 14, 32   # CR-2, 27 Oct 2026 - the receipt email pop-up on Receipts and on Receipt Details: a Cancel and a Send each.   # (was 55, 14, 30)   # PV-1, 15 Oct 2026 - two hand-rolled invoice viewers retired, each with a Close and a Download. The danger count is unchanged: neither had a destructive button in it.   # (was 57, 14, 32)
CONVERTED_NOW, WAITING_NOW, CEILING_NOW, ALIAS_NOW = 73, 2, 38, 57

'''),
    ]),
    (os.path.join('test_admin_behaviour.py'), [
        (r'''
CONVERTED_NOW, ALIAS_NOW = 92, 95
N_CARDS = 14
PHONES = (320, 360, 390, 414)

''',
         r'''
CONVERTED_NOW, ALIAS_NOW = 92, 95
N_CARDS = 15   # CR-2, 27 Oct 2026 - Cash Receipt to Payer  # (was 14)
ADDED_SINCE = 1   # CR-2, 27 Oct 2026 - cards added after this round
PHONES = (320, 360, 390, 414)

'''),
        (r'''tn, tw = titles(B_NOW[NOTIF]), titles(B_WAS[NOTIF])
ok(len(tn) == N_CARDS, 'each one has a heading', len(tn))
ok(not APPLIED or tn == tw,
   'and the MARKUP order is byte-for-byte what it was - the sort happens '
   'in the browser, so card %d sorts too' % (N_CARDS + 1))
''',
         r'''tn, tw = titles(B_NOW[NOTIF]), titles(B_WAS[NOTIF])
ok(len(tn) == N_CARDS, 'each one has a heading', len(tn))
# CR-2, 27 Oct 2026 - the markup is what it was PLUS the one card added
# since, which sorts in the browser like every other.
ok(not APPLIED or [x for x in tn if x.strip() != 'Cash Receipt to Payer'] == tw,
   'and the MARKUP order is byte-for-byte what it was - the sort happens '
   'in the browser, so card %d sorts too' % (N_CARDS + 1))
'''),
        (r'''
            a, b = seen['now'], seen['was']
            ok(a['n'] == b['n'] == N_CARDS,
               'the page draws %d cards, before and after' % N_CARDS,
               (b['n'], a['n']))
            ok(a['collapsible'] == b['collapsible'] == N_CARDS,
               'and every one of them is collapsible, before and after',
               (b['collapsible'], a['collapsible']))
''',
         r'''
            a, b = seen['now'], seen['was']
            # CR-2, 27 Oct 2026 - ONE CARD JOINED SINCE (Cash Receipt to
            # Payer), so the page before this round drew one fewer.
            ok(a['n'] == N_CARDS and b['n'] == N_CARDS - ADDED_SINCE,
               'the page draws %d cards, %d before this round and the one '
               'added since' % (N_CARDS, N_CARDS - ADDED_SINCE),
               (b['n'], a['n']))
            ok(a['collapsible'] == N_CARDS
               and b['collapsible'] == N_CARDS - ADDED_SINCE,
               'and every one of them is collapsible, before and after',
               (b['collapsible'], a['collapsible']))
'''),
        (r'''            else:
                skip('CONTROL: they were not sorted', 'not applied')
            ok(sorted(a['titles']) == sorted(b['titles']),
               'and it is the SAME %d cards, reordered - none lost, none '
               'invented' % N_CARDS)
''',
         r'''            else:
                skip('CONTROL: they were not sorted', 'not applied')
            ok(sorted(x for x in a['titles']
                      if x.strip() != 'Cash Receipt to Payer')
               == sorted(b['titles']),
               'and it is the SAME %d cards, reordered - none lost, none '
               'invented' % N_CARDS)
'''),
    ]),
    (os.path.join('test_pair_contrast.py'), [
        (r'''MARK = 'B-4b, 8 Oct 2026'

EXPECT_PAIRS = 746   # ES-11, 26 Oct 2026 - the yellow signed-leases bar left Home and Notifications, and with it .lsa-strip's fill+ink pair on each page.   # (was 748)   # ES-9, 26 Oct 2026 - Home's Waiting for you icon chip, .ins-ic--wait, sets the warn-soft fill and warn-ink together, a pair base already uses.   # (was 747)   # ES-7, 25 Oct 2026 - two notes set a fill and an ink together: .hm-note on the Signature and Stamp screen and .ls-saved-note on the signing page, both on the accent pair this table already knows.   # (was 745)   # ES-6, 25 Oct 2026 - three more rules in ES-6's pages set a fill and an ink together, measured by this census on the full tree.   # (was 742)   # ES-4, 24 Oct 2026 - eleven in the public signing pages' own stylesheet. A standalone page cannot inherit a surface, so every one it draws sets both halves of the pair itself - which is exactly why this census asks about them.   # (was 731)   # ES-3a, 23 Oct 2026 - the lease signing register: three signer dots mirroring the good, bad and neutral pills, and the waiting-on-you note. Four rules, no new pairings.   # (was 727)   # MN-2, 21 Oct 2026 - the Saved Menus dialog gains the preset row CP-2 built for Copy, and .mn-preset[aria-pressed=true] sets a fill and an ink together exactly as .cp-preset does. One more pair, of tokens this table already knows.   # (was 726)   # RG-2, 21 Oct 2026 - two more rules set a fill and an ink together: the date field, which wears the paper token on the ink one like every other field in the system, and the line explaining the second Print press, which sits on the surface wash.   # (was 724)   # RG-1, 21 Oct 2026 - the printed sheet is drawn again from four layouts, and five more of its rules set a fill and an ink together: the pill in its three states, the today marker and the dimmed cell. Every one is a token pair this table already knows.   # (was 719)   # PP-1, 20 Oct 2026 - the printable plan sets
# both a ground and an ink on six rules. All house pairs off base's
# own tokens, so the AA table below is untouched and the gross count
''',
         r'''MARK = 'B-4b, 8 Oct 2026'

EXPECT_PAIRS = 750   # CR-2, 27 Oct 2026 - the receipt email pop-up, on Receipts and on Receipt Details: the message box and the Printed warning each set a fill and its ink, pairs base already uses.   # (was 746)   # ES-11, 26 Oct 2026 - the yellow signed-leases bar left Home and Notifications, and with it .lsa-strip's fill+ink pair on each page.   # (was 748)   # ES-9, 26 Oct 2026 - Home's Waiting for you icon chip, .ins-ic--wait, sets the warn-soft fill and warn-ink together, a pair base already uses.   # (was 747)   # ES-7, 25 Oct 2026 - two notes set a fill and an ink together: .hm-note on the Signature and Stamp screen and .ls-saved-note on the signing page, both on the accent pair this table already knows.   # (was 745)   # ES-6, 25 Oct 2026 - three more rules in ES-6's pages set a fill and an ink together, measured by this census on the full tree.   # (was 742)   # ES-4, 24 Oct 2026 - eleven in the public signing pages' own stylesheet. A standalone page cannot inherit a surface, so every one it draws sets both halves of the pair itself - which is exactly why this census asks about them.   # (was 731)   # ES-3a, 23 Oct 2026 - the lease signing register: three signer dots mirroring the good, bad and neutral pills, and the waiting-on-you note. Four rules, no new pairings.   # (was 727)   # MN-2, 21 Oct 2026 - the Saved Menus dialog gains the preset row CP-2 built for Copy, and .mn-preset[aria-pressed=true] sets a fill and an ink together exactly as .cp-preset does. One more pair, of tokens this table already knows.   # (was 726)   # RG-2, 21 Oct 2026 - two more rules set a fill and an ink together: the date field, which wears the paper token on the ink one like every other field in the system, and the line explaining the second Print press, which sits on the surface wash.   # (was 724)   # RG-1, 21 Oct 2026 - the printed sheet is drawn again from four layouts, and five more of its rules set a fill and an ink together: the pill in its three states, the today marker and the dimmed cell. Every one is a token pair this table already knows.   # (was 719)   # PP-1, 20 Oct 2026 - the printable plan sets
# both a ground and an ink on six rules. All house pairs off base's
# own tokens, so the AA table below is untouched and the gross count
'''),
    ]),
    (os.path.join('test_auth_flow.py'), [
        (r'''    from pages.models import NotificationRecipient as NR
    codes = [c for c, _ in NR.NOTIFICATION_TYPES]
    ok(TYPE in codes and len(codes) == 16,
       'the model really offers 16 types, with this one among them',
       '%d: %s' % (len(codes), codes[-2:]))
    ok(len(set(codes)) == len(codes), '  and no code appears twice')
    # ONLY the choices list. The first version of this read the whole
    # file and matched ('pages', '0095_none_columns') out of dependencies,
    # then reported the migration as having a type the model did not.
    choice_block = mig[mig.index('choices=['):mig.index('max_length=50')]
    mig_codes = re.findall(r"\('([a-z_]+)', '", choice_block)
''',
         r'''    from pages.models import NotificationRecipient as NR
    codes = [c for c, _ in NR.NOTIFICATION_TYPES]
    # CR-2, 27 Oct 2026 - SEVENTEEN: Cash Receipt to Payer joined.
    ok(TYPE in codes and len(codes) == 17,
       'the model really offers 17 types, with this one among them',
       '%d: %s' % (len(codes), codes[-2:]))
    ok(len(set(codes)) == len(codes), '  and no code appears twice')
    # ONLY the choices list. The first version of this read the whole
    # file and matched ('pages', '0095_none_columns') out of dependencies,
    # then reported the migration as having a type the model did not.
    # CR-2, 27 Oct 2026 - ASKED OF THE NEWEST notification-type
    # migration, which is the one makemigrations compares against;
    # 0096 is still asked above whether it carries this type.
    _mdir = abspath('pages/migrations')
    _newest = sorted(n for n in os.listdir(_mdir)
                     if n.endswith('.py') and 'notification_type' in n)[-1]
    mig = read(os.path.join(_mdir, _newest))
    choice_block = mig[mig.index('choices=['):mig.index('max_length=50')]
    mig_codes = re.findall(r"\('([a-z_]+)', '", choice_block)
'''),
    ]),
    (os.path.join('pages', 'help_content', 'operational.html'), [
        (r'''<!-- ======= END PHYSICAL INVOICES ======= -->

''',
         r'''<!-- ======= END PHYSICAL INVOICES ======= -->

<!-- ======= CASH RECEIPTS - CR-2, 27 Oct 2026 ======= -->
<section data-module-slug="cash_receipts"
         data-module-group="Financial Management"
         data-module-permission="can_access_receipts"
         data-module-name="Receipts"
         data-module-icon="fa-receipt"
         data-module-category="Operational"
         data-module-subtitle="Issue, email, edit and void numbered cash receipts for money received">

  <article data-tab-slug="crOverview"
           data-tab-name="Overview"
           data-tab-icon="fa-info-circle">
    <h6 style="color:#0e7c8b; font-weight:700;"><i class="fas fa-receipt"></i> What is a Receipt?</h6>
    <p>A <strong>Receipt</strong> is the document you give somebody to confirm that Alivente has received their money &mdash; rent, a deposit, or any other payment. Each one carries a <strong>CR-number</strong> (for example <em>CR-00376</em>) that is given out in order and never changes, and the system stores the PDF the moment the receipt is issued.</p>

    <h6 style="color:#0e7c8b; font-weight:700; margin-top:20px;"><i class="fas fa-plus"></i> Issuing a receipt</h6>
    <p>Press <strong>Issue Receipt</strong>. The next number is shown above the list before you start. Fill in:</p>
    <ul>
      <li><strong>The payment</strong> &mdash; date received, amount, method (cash, bank transfer, cheque, card), an optional reference, and what it is <em>being payment for</em>.</li>
      <li><strong>Received from</strong> &mdash; pick a tenant or customer to fill in their details, or type a name. Address, telephone and <strong>email</strong> are optional; the email is what <strong>Email receipt</strong> sends to, so add it if you will email the receipt. Several addresses can be separated with commas.</li>
      <li><strong>Property</strong> &mdash; optional.</li>
    </ul>

    <h6 style="color:#0e7c8b; font-weight:700; margin-top:20px;"><i class="fas fa-file-pdf"></i> Electronic or Printed</h6>
    <div class="card mb-2" style="border-left:4px solid #0e7c8b;">
      <div class="card-body" style="padding:12px 15px;">
        <h6 style="margin:0 0 5px 0;"><strong>Electronic</strong></h6>
        <p class="mb-0" style="font-size:13px;">No signature block; the receipt states that it is valid without one. Meant for emailing or sharing.</p>
      </div>
    </div>
    <div class="card mb-3" style="border-left:4px solid #0e7c8b;">
      <div class="card-body" style="padding:12px 15px;">
        <h6 style="margin:0 0 5px 0;"><strong>Printed</strong></h6>
        <p class="mb-0" style="font-size:13px;">Carries ruled signature and date lines instead, for handing over on paper. It can still be emailed &mdash; you are warned first.</p>
      </div>
    </div>
  </article>

  <article data-tab-slug="crList"
           data-tab-name="The List"
           data-tab-icon="fa-table">
    <h6 style="color:#0e7c8b; font-weight:700;"><i class="fas fa-table"></i> Reading the list</h6>
    <p>Newest first. Columns: <strong>Receipt #</strong> (click it to open the Receipt Details page), <strong>Date</strong>, <strong>Received From</strong>, <strong>Being Payment For</strong>, <strong>Amount</strong> and <strong>Status</strong>. A receipt changed after it was issued is marked <em>EDITED</em> under its number. The total at the bottom counts issued receipts only, one line per currency.</p>

    <h6 style="color:#0e7c8b; font-weight:700; margin-top:20px;"><i class="fas fa-tag"></i> Status</h6>
    <ul>
      <li><strong>Issued</strong> &mdash; a live receipt.</li>
      <li><strong>Issued &middot; Sent</strong> &mdash; emailed, and not changed since. Hover over it to see when.</li>
      <li><strong>Void</strong> &mdash; cancelled. It keeps its number and stays in the list.</li>
    </ul>

    <h6 style="color:#0e7c8b; font-weight:700; margin-top:20px;"><i class="fas fa-hand-pointer"></i> The actions on each row</h6>
    <ul>
      <li><i class="fas fa-file-pdf"></i> <strong>View</strong> &mdash; the stored PDF, in the viewer.</li>
      <li><i class="fas fa-pencil-alt"></i> <strong>Edit</strong> &mdash; change anything but the number. The PDF is re-made and the receipt is marked edited.</li>
      <li><i class="fas fa-copy"></i> <strong>Duplicate</strong> &mdash; a new receipt with the same details, including the email address, ready to adjust and issue.</li>
      <li><i class="fas fa-paper-plane"></i> <strong>Email</strong> &mdash; send it to the payer (see the next tab). Greyed out when the receipt has no email address, and on a void receipt.</li>
      <li><i class="fas fa-ban"></i> <strong>Void</strong> / <i class="fas fa-undo"></i> <strong>Unvoid</strong> &mdash; cancel a receipt, or bring it back. Voiding stamps VOID on its PDF; unvoiding takes the stamp off.</li>
    </ul>

    <h6 style="color:#0e7c8b; font-weight:700; margin-top:20px;"><i class="fas fa-filter"></i> Filtering</h6>
    <p><strong>Filter</strong> narrows the list by date range and status; <strong>Received From</strong> narrows as you type.</p>
  </article>

  <article data-tab-slug="crEmail"
           data-tab-name="Emailing"
           data-tab-icon="fa-paper-plane">
    <h6 style="color:#0e7c8b; font-weight:700;"><i class="fas fa-paper-plane"></i> Emailing a receipt</h6>
    <p>Press the <i class="fas fa-paper-plane"></i> on a row, or <strong>Email receipt</strong> on the Receipt Details page. A pop-up shows exactly what will happen before anything is sent: who it goes <strong>To</strong>, who is <strong>Cc</strong>&rsquo;d, the subject, the attached PDF and the message itself. Press <strong>Send</strong> to send it, or Cancel.</p>

    <h6 style="color:#0e7c8b; font-weight:700; margin-top:20px;"><i class="fas fa-users"></i> Who receives it</h6>
    <div class="card mb-2" style="border-left:4px solid #0e7c8b;">
      <div class="card-body" style="padding:12px 15px;">
        <h6 style="margin:0 0 5px 0;"><strong>To</strong></h6>
        <p class="mb-0" style="font-size:13px;">Always the email address(es) on the receipt (Received from &rsaquo; Email).</p>
      </div>
    </div>
    <div class="card mb-3" style="border-left:4px solid #0e7c8b;">
      <div class="card-body" style="padding:12px 15px;">
        <h6 style="margin:0 0 5px 0;"><strong>Anyone else</strong></h6>
        <p class="mb-0" style="font-size:13px;">Set once in <strong>Administration &rsaquo; Notification Settings &rsaquo; Cash Receipt to Payer</strong>. Addresses in its <em>TO</em> box are added beside the payer; addresses in its <em>CC</em> box are copied. Leave TO blank and fill in CC to send To the payer and copy, say, yourself. With nothing saved there, the receipt goes to the payer alone.</p>
      </div>
    </div>

    <h6 style="color:#0e7c8b; font-weight:700; margin-top:20px;"><i class="fas fa-check-circle"></i> After sending</h6>
    <ul>
      <li>The status reads <strong>Issued &middot; Sent</strong>, and the Receipt Details history says when and to whom it was emailed.</li>
      <li>The button stays &mdash; as <strong>Send again</strong> &mdash; for when a payer says it did not arrive.</li>
      <li><strong>Editing a sent receipt puts it back to Issued</strong>, so it is clear the corrected copy has not gone out. Email it again to send the correction.</li>
    </ul>

    <div class="alert alert-info" style="border-left:4px solid #0e7c8b;">
      <i class="fas fa-info-circle"></i> The email is short and branded &mdash; the Alivente logo under the sign-off &mdash; and carries no contact details. The receipt itself is the attachment.
    </div>
  </article>

  <article data-tab-slug="crDetails"
           data-tab-name="Receipt Details"
           data-tab-icon="fa-search">
    <h6 style="color:#0e7c8b; font-weight:700;"><i class="fas fa-search"></i> The record behind a receipt</h6>
    <p>Click a receipt number to open <strong>Receipt Details</strong>: the payment, the payer&rsquo;s address, telephone and email, the property, and a <strong>history</strong> &mdash; issued, emailed (and to whom), edited, voided (and why) &mdash; oldest first. From here you can view the PDF, edit the receipt or email it.</p>
  </article>

</section>
<!-- ======= END CASH RECEIPTS ======= -->
'''),
    ]),
]


def read(p):
    with open(p, encoding='utf-8', newline='') as f:
        return f.read()


def write_file(p, t):
    with open(p, 'w', encoding='utf-8', newline='') as f:
        f.write(t)


def backup(p):
    b = p + SUFFIX
    if not os.path.exists(b) and not CHECK:
        write_file(b, read(p))


def refuse(msg):
    raise SystemExit('CR-2 REFUSED: %s' % msg)


def fit(text, lit):
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


def swap(text, old, new, where):
    once(text, old, where)
    return text.replace(fit(text, old), fit(text, new))


def main(argv):
    global CHECK
    CHECK = '--check' in argv
    root = os.path.dirname(os.path.abspath(__file__))
    out = {}

    pq = os.path.join(root, PS1)
    if "'test_receipt_email.py'" in read(pq):
        print('CR-2 already applied.')
        return 0

    sys.path.insert(0, root)
    import alv_tree as T

    if "'test_gate_speed_two.py'" not in read(pq):
        refuse('GS-1 is not applied - this round registers after it.')
    for rel in CREATES:
        if not os.path.isfile(os.path.join(root, rel)):
            refuse('%s is missing - it ships with this patcher; copy it in '
                   'first.' % rel)

    # ---- THE SWAPS
    for rel, pairs in SWAPS:
        pth = os.path.join(root, rel)
        t = read(pth)
        for i, (was, now) in enumerate(pairs):
            t = swap(t, was, now, '%s (swap %d of %d)'
                     % (rel, i + 1, len(pairs)))
        out[pth] = t

    # ---- REGISTRATION
    q = out.get(pq, read(pq))
    q = swap(q, """    'test_gate_speed_two.py'
)""", """    'test_gate_speed_two.py',
    # CR-2, 27 Oct 2026 - emailing a cash receipt.
    'test_receipt_email.py'
)""", '%s (the suites)' % PS1)
    q = swap(
        q,
        """    @{ File = 'test_crs_print.py'; Text = 'subprocess.run([sys.executable, GUARD]';""",
        """    @{ File = 'pages/views/receipts.py'; Text = 'def cash_receipt_send('; What = 'CR-2: a cash receipt can be emailed to its payer - without the view the paper-plane posts to nothing' },
    @{ File = 'test_crs_print.py'; Text = 'subprocess.run([sys.executable, GUARD]';""",
        '%s (the sentinels)' % PS1)
    out[pq] = q

    ptr = os.path.join(root, TREE)
    out[ptr] = swap(out.get(ptr, read(ptr)), """    'test_gate_speed_two.py',
]""", """    'test_gate_speed_two.py',
    # CR-2, 27 Oct 2026 - emailing a cash receipt.
    'test_receipt_email.py',
]""", '%s (CONVERTED)' % TREE)

    pd = os.path.join(root, ROUNDS)
    out[pd] = swap(out.get(pd, read(pd)), """    '.bak_gatespeed2',
]""", """    '.bak_gatespeed2',
    # CR-2, 27 Oct 2026 - emailing a cash receipt.
    '.bak_receiptemail',
]""", '%s (ROUNDS)' % ROUNDS)

    pw = os.path.join(root, WD)
    w = out.get(pw, read(pw))
    n = re.search(r'CONVERTED_N = (\d+)', w)
    if not n:
        refuse('%s: CONVERTED_N is not there' % WD)
    out[pw] = swap(w, 'CONVERTED_N = %s' % n.group(1),
                   'CONVERTED_N = %d   # CR-2, 27 Oct 2026 - this round '
                   'own suite   # (was %s)'
                   % (int(n.group(1)) + 1, n.group(1)),
                   '%s (CONVERTED_N)' % WD)

    # ---------------------------------------------------------- THE GATES
    if 'def cash_receipt_send(' not in out[
            os.path.join(root, 'pages', 'views', 'receipts.py')]:
        refuse('the send view did not land.')
    if "'cash_receipt_payer': {'to': [], 'cc': []}" not in out[
            os.path.join(root, 'pages', 'email_utils.py')]:
        refuse('with no card saved, receipts must go to the payer alone.')

    if CHECK:
        print('CR-2 --check: %d file(s) would change, none written; %d '
              'ship with it.' % (len(out), len(CREATES)))
        for k in sorted(out):
            print('        %s' % os.path.relpath(k, root))
        return 0

    for k, val in sorted(out.items()):
        backup(k)
        write_file(k, val)
    for k in sorted(out):
        if read(k) != out[k]:
            refuse('%s was not written' % os.path.relpath(k, root))
    print('CR-2 applied - cash receipts can be emailed; Cash Receipt to '
          'Payer card on Notification Settings. Run manage.py migrate (0110).')
    print('      %d file(s) written, backed up to %s' % (len(out), SUFFIX))
    print('      %d file(s) ship with it, wired in rather than written'
          % len(CREATES))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
