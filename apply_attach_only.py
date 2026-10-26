# -*- coding: utf-8 -*-
"""apply_attach_only.py - round ES-10, 26 Oct 2026.

RELEASE 24 - START E-SIGNING ATTACHES THE LEASE, ALWAYS. His decision of
26 October: the lease already on a tenant record is never the document to
sign - since ES-9 it is the lease that tenancy has already signed, or
nothing. A lease for signature is a PDF he attaches (or, once unparked,
one Generate makes).

    - Start e-signing draws one document field, required; the "use the
      lease already on this tenant record" choice and its script go.
    - The server refuses a POST that names the stored lease with nothing
      attached, exactly as it refuses an empty upload.
    - Help says so, and how a lease from Generate gets here.
    - Once a PDF is chosen, its name appears with a PDF viewer icon that
      opens that file in the app PDF viewer modal - his follow-up ask,
      to check it is the right one before anything is sent.
    - test_send_lease asks for the refusal instead of the copy; the
      sentinel that guarded the copy now guards its absence, and
      test_sentinels drops the pin that row needed.

Stands on ES-9. Idempotent. Edits backed up to .bak_attachonly; ships this
patcher and its suite. No migration.
"""
import os
import re
import sys

SUFFIX = '.bak_attachonly'
MARK = 'ES-10, 26 Oct 2026'
CHECK = False
CREATES = (
    'test_attach_only.py',
)

PS1 = 'Push-PendingChanges.ps1'
TREE = 'alv_tree.py'
ROUNDS = 'alv_rounds.py'
WD = 'test_waiting_down.py'

SWAPS = [
    (os.path.join('pages', 'views', 'lease_signing_create.py'), [
        (r'''    tenancy.

THE DOCUMENT: UPLOAD ONE, OR USE THE ONE ALREADY ON THE RECORD. His
decision of 24 October. Re-uploading a file the system already holds
is work for no reason, and the second copy is a second thing that can
drift from the first.

    AND IT IS COPIED, NOT POINTED AT. tenant_lease_agreement can be
    replaced or deleted from Manage Lease Agreements; an envelope
    that merely referenced it would have the document change under a
    signature. ES-2 hashes what was signed precisely so that cannot
    happen quietly, and this is the other half of it.

PDF ONLY, and not because of taste. ES-2 rasterises the original so
''',
         r'''    tenancy.

THE DOCUMENT IS ATTACHED, ALWAYS. ES-10, 26 Oct 2026, his decision,
reversing the 24 October one that offered the lease already on the
tenant record. Since ES-9 a lease is never overwritten, so the file on
a record is either the lease that tenancy already signed or nothing -
and sending a signed lease out to be signed again is never what he
means. A lease for signature is a PDF he attaches (or, once it is
unparked, one Generate makes).

    THE UPLOAD IS STILL A FILE OF THE ENVELOPE'S OWN. Nothing here
    points at tenant_lease_agreement, so Manage Lease Agreements can
    replace or delete that file without changing what was signed.

PDF ONLY, and not because of taste. ES-2 rasterises the original so
'''),
        (r'''from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.files.base import ContentFile
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
''',
         r'''from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
'''),
        (r'''

def _stored_pdf(ten):
    """The lease already on the record, when it is one we can use."""
    f = getattr(ten, 'tenant_lease_agreement', None)
    if not f:
        return None
    name = getattr(f, 'name', '') or ''
    if os.path.splitext(name)[1].lower() != '.pdf':
        return None
    return f


def _prefill(ten, user):
    """Who this envelope would go to, read off the record.
''',
         r'''

def _prefill(ten, user):
    """Who this envelope would go to, read off the record.
'''),
        (r'''            return redirect('lease_signing_create')

        # ---- THE DOCUMENT
        use_stored = request.POST.get('document') == 'stored'
        stored = _stored_pdf(chosen)
        uploaded = request.FILES.get('lease_pdf')

        if use_stored:
            if stored is None:
                messages.error(
                    request, 'There is no PDF lease on this tenant record '
                             'to use. Attach one instead.')
                return redirect(request.get_full_path())
            source_name = os.path.basename(stored.name)
        else:
            if not uploaded:
                messages.error(request,
                               'Attach the lease agreement as a PDF.')
                return redirect(request.get_full_path())
            if os.path.splitext(uploaded.name)[1].lower() not in ALLOWED:
                messages.error(
                    request, 'The lease must be a PDF. The signing page '
                             'shows the document itself, and an image has '
                             'no pages to show.')
                return redirect(request.get_full_path())
            if uploaded.size > MAX_BYTES:
                messages.error(request, 'That file is over 15MB.')
                return redirect(request.get_full_path())
            source_name = uploaded.name

        # ---- THE SIGNERS
''',
         r'''            return redirect('lease_signing_create')

        # ---- THE DOCUMENT - ATTACHED, ALWAYS. ES-10, 26 Oct 2026.
        # The lease on the tenant record is never offered: since ES-9
        # it is either the one this tenancy already signed or nothing.
        # A hand-made POST naming it gets the same answer as an empty
        # upload.
        uploaded = request.FILES.get('lease_pdf')
        if not uploaded:
            messages.error(request,
                           'Attach the lease agreement as a PDF.')
            return redirect(request.get_full_path())
        if os.path.splitext(uploaded.name)[1].lower() not in ALLOWED:
            messages.error(
                request, 'The lease must be a PDF. The signing page '
                         'shows the document itself, and an image has '
                         'no pages to show.')
            return redirect(request.get_full_path())
        if uploaded.size > MAX_BYTES:
            messages.error(request, 'That file is over 15MB.')
            return redirect(request.get_full_path())

        # ---- THE SIGNERS
'''),
        (r'''                expires_at=LeaseSigning.closing_moment(days))

            if use_stored:
                # COPIED, NOT POINTED AT. The file on the tenant record
                # can be replaced or deleted from Manage Lease
                # Agreements, and a document that changed under a
                # signature is the one thing ES-2's hash exists to
                # make impossible.
                stored.open('rb')
                try:
                    env.original_pdf.save(source_name,
                                          ContentFile(stored.read()),
                                          save=True)
                finally:
                    stored.close()
            else:
                env.original_pdf.save(uploaded.name, uploaded, save=True)

            # THE PAGES, NOW. ES-4 shows these and asks page_count how
''',
         r'''                expires_at=LeaseSigning.closing_moment(days))

            env.original_pdf.save(uploaded.name, uploaded, save=True)

            # THE PAGES, NOW. ES-4 shows these and asks page_count how
'''),
        (r'''                detail='%d signer(s), %s, expires in %d day(s)'
                       % (1 + len(signers),
                          'stored lease' if use_stored else 'uploaded',
                          days),
                ip=(request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0]
''',
         r'''                detail='%d signer(s), %s, expires in %d day(s)'
                       % (1 + len(signers),
                          'uploaded',
                          days),
                ip=(request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0]
'''),
        (r'''        'min_expiry': MIN_EXPIRY_DAYS,
        'max_expiry': MAX_EXPIRY_DAYS,
        'stored_pdf': _stored_pdf(chosen) if chosen else None,
        # THE FILENAME, NOT THE STORAGE KEY. Django has no basename
        # filter and a template `cut` on one folder name left
        # `e_agreements/tenant_1_mr-dorian-...` on screen - a path
        # chopped mid-word, which tells the reader nothing and reads
        # like a bug. The view knows how to take a basename.
        'stored_name': (os.path.basename(_stored_pdf(chosen).name)
                        if chosen and _stored_pdf(chosen) else ''),
        # A WARNING, NOT A REFUSAL. A renewal arrives with no lease
        # because duplicate_tenant clears the field, so an envelope on
''',
         r'''        'min_expiry': MIN_EXPIRY_DAYS,
        'max_expiry': MAX_EXPIRY_DAYS,
        # A WARNING, NOT A REFUSAL. A renewal arrives with no lease
        # because duplicate_tenant clears the field, so an envelope on
'''),
    ]),
    (os.path.join('pages', 'templates', 'lease_signing_create.html'), [
        (r'''    <h3 class="form-section-title"><i class="fas fa-file-contract"></i> The document</h3>

    {# TWO WAYS IN, AND THE STORED ONE IS OFFERED FIRST WHEN IT      #}
    {# EXISTS - his decision of 24 October. Re-uploading a file the  #}
    {# system already holds is work for no reason.                   #}
    <div class="form-row">
        <div class="col-md-12">
          <div class="form-group">
            {% if stored_pdf %}
            <label class="alv-choice">
              <input type="radio" name="document" value="stored" checked
                     onchange="lsDoc()">
              {# THE FILENAME THE VIEW TOOK, not the storage key. A   #}
              {# template `cut` on one folder name left a path chopped #}
              {# mid-word on screen the first time this rendered.      #}
              <span>Use the lease already on this tenant record
                &mdash; <code>{{ stored_name }}</code></span>
            </label>
            {% endif %}
            <label class="alv-choice">
              <input type="radio" name="document" value="upload"
                     {% if not stored_pdf %}checked{% endif %}
                     onchange="lsDoc()">
              <span>Attach a different PDF</span>
            </label>
          </div>
        </div>
    </div>

    <div class="form-row" id="ls-upload-row"
         {% if stored_pdf %}style="display: none;"{% endif %}>
        <div class="col-md-8">
          <div class="form-group">
            <label for="lease_pdf"><strong>Lease agreement</strong>
              <span class="alv-req">*</span></label>
            <input type="file" class="form-control" id="lease_pdf"
                   name="lease_pdf" accept="application/pdf,.pdf">
            {# PDF ONLY, AND THE REASON IS SAID RATHER THAN ENFORCED #}
            {# IN SILENCE. ES-2 rasterises the original so the       #}
''',
         r'''    <h3 class="form-section-title"><i class="fas fa-file-contract"></i> The document</h3>

    {# ONE WAY IN - ES-10, 26 Oct 2026, his decision. The lease on   #}
    {# the tenant record is never offered: since ES-9 it is the one  #}
    {# that tenancy already signed, or nothing. A lease for          #}
    {# signature is attached here (Generate joins when unparked).    #}
    <div class="form-row" id="ls-upload-row">
        <div class="col-md-8">
          <div class="form-group">
            <label for="lease_pdf"><strong>Lease agreement</strong>
              <span class="alv-req">*</span></label>
            <input type="file" class="form-control" id="lease_pdf"
                   name="lease_pdf" accept="application/pdf,.pdf" required>
            {# PDF ONLY, AND THE REASON IS SAID RATHER THAN ENFORCED #}
            {# IN SILENCE. ES-2 rasterises the original so the       #}
'''),
        (r'''              itself, page by page.
            </small>
          </div>
        </div>
''',
         r'''              itself, page by page.
            </small>
            {# LOOK BEFORE YOU SEND - ES-10, 26 Oct 2026, his ask. Once  #}
            {# a PDF is chosen, its name and a viewer icon appear; the   #}
            {# icon opens THAT file, from this browser, in the app's own #}
            {# PDF viewer modal (his ask: like the rest of the viewers) -#}
            {# nothing is uploaded until Create and sign.                #}
            <div id="ls-pdf-picked" class="ls-pdf-picked" style="display: none;">
              <a href="#" id="ls-pdf-view" class="icon-action-btn icon-pdf"
                 title="View the attached PDF"
                 aria-label="View the attached PDF"><i class="fas fa-file-pdf"></i></a>
              <span id="ls-pdf-name"></span>
            </div>
          </div>
        </div>
'''),
        (r'''<script>
(function () {
  // THE UPLOAD BOX FOLLOWS THE CHOICE, and the SERVER decides which
  // one it read - this only keeps the screen honest while you look
  // at it. Same rule as T2-2's reveal: '' and not 'block', so the
  // stylesheet keeps deciding.
  window.lsDoc = function () {
    var row = document.getElementById('ls-upload-row');
    if (!row) return;
    var pick = document.querySelector('input[name="document"]:checked');
    var upload = (!pick || pick.value !== 'stored');
    row.style.display = upload ? '' : 'none';
    // REQUIRED FOLLOWS THE REVEAL - T2-6's rule for the contact
    // person, in the other direction. The label carries a star, and a
    // star has to mean a `required` somebody can satisfy; a hidden
    // required field refuses the form with nothing on screen to
    // explain where. test_required_promise is what holds the two
    // together.
    // AND WRITTEN SO THE INSTRUMENT CAN SEE IT. A star on a label is
    // a promise, and test_required_promise sorts every starred label
    // in the tree into one of five mechanisms; `el.required = upload`
    // through a local variable is none of them, so the promise read
    // as unkept. The id sits next to the assignment and the value is
    // a literal, which is the shape that census recognises.
    if (upload) { document.getElementById('lease_pdf').required = true; }
    else { document.getElementById('lease_pdf').required = false; }
  };
  lsDoc();

  // ONE SUBMIT. Rendering the pages of a long lease takes a moment,
''',
         r'''<script>
(function () {
  // THE ATTACHED PDF, VIEWABLE BEFORE IT IS SENT - ES-10, 26 Oct 2026.
  // A blob URL of the chosen file, shown in components/pdf_viewer.html
  // like every other PDF in the app: the browser reads it from memory,
  // so the check costs no upload. The old URL is released on every
  // change so a second choice never shows the first file.
  var pdfIn = document.getElementById('lease_pdf');
  var picked = document.getElementById('ls-pdf-picked');
  var viewA = document.getElementById('ls-pdf-view');
  var nameEl = document.getElementById('ls-pdf-name');
  var blobUrl = null;
  if (pdfIn && picked && viewA && nameEl) {
    pdfIn.addEventListener('change', function () {
      if (blobUrl) { URL.revokeObjectURL(blobUrl); blobUrl = null; }
      var f = pdfIn.files && pdfIn.files[0];
      if (f && /\.pdf$/i.test(f.name)) {
        blobUrl = URL.createObjectURL(f);
        nameEl.textContent = f.name;
        picked.style.display = '';
      } else {
        nameEl.textContent = '';
        picked.style.display = 'none';
      }
    });
    viewA.addEventListener('click', function (ev) {
      ev.preventDefault();
      var f = pdfIn.files && pdfIn.files[0];
      if (blobUrl && f && typeof window.openPdfViewer === 'function') {
        window.openPdfViewer(blobUrl, 'Attached lease', f.name);
      }
    });
  }

  // ONE SUBMIT. Rendering the pages of a long lease takes a moment,
'''),
        (r'''</script>

{% endblock %}
''',
         r'''</script>

{# ES-10, 26 Oct 2026 - the app's PDF viewer, for the attached lease. #}
{% include 'components/pdf_viewer.html' %}

<style>
/* ES-10, 26 Oct 2026 - the attached PDF, with its viewer icon. */
.ls-pdf-picked {
    display: flex; align-items: center; gap: 10px;
    margin-top: 10px; overflow-wrap: anywhere;
}
</style>

{% endblock %}
'''),
    ]),
    (os.path.join('pages', 'help_content', 'administration.html'), [
        (r'''    <ul style="line-height:1.8;">
      <li><strong>Tenant</strong> &mdash; the tenancy the lease is for. If it already has an envelope open you are warned: starting another does not cancel the first.</li>
      <li><strong>The document</strong> &mdash; use the lease already on the tenant record, or attach a different PDF (PDF only, up to 15MB). The file is <em>copied</em> onto the envelope, so replacing the tenant&rsquo;s lease later cannot change what was signed.</li>
      <li><strong>Signing for Alivente</strong> &mdash; leave it as yourself and you sign on the next screen. Name somebody else and they are emailed a link instead.</li>
      <li><strong>Tenants</strong> &mdash; filled in from the tenant record; at most two, with two different email addresses so the record can tell who signed. A second signer appears only when the tenancy has a second tenant.</li>
''',
         r'''    <ul style="line-height:1.8;">
      <li><strong>Tenant</strong> &mdash; the tenancy the lease is for. If it already has an envelope open you are warned: starting another does not cancel the first.</li>
      <!-- ES-10, 26 Oct 2026 - the document is always attached. -->
      <li><strong>The document</strong> &mdash; attach the lease to be signed as a PDF (PDF only, up to 15MB). The lease already on the tenant record is never offered: it is the one that tenancy has already signed. A lease made in <strong>Generate</strong> downloads as a Word file &mdash; check it, save it as a PDF, and attach that. The file belongs to the envelope, so anything done on Manage Lease Agreements later cannot change what was signed.</li>
      <li><strong>Signing for Alivente</strong> &mdash; leave it as yourself and you sign on the next screen. Name somebody else and they are emailed a link instead.</li>
      <li><strong>Tenants</strong> &mdash; filled in from the tenant record; at most two, with two different email addresses so the record can tell who signed. A second signer appears only when the tenancy has a second tenant.</li>
'''),
    ]),
    (os.path.join('test_send_lease.py'), [
        (r'''does not.

SECTION 5 IS THE DOCUMENT, AND THE CLAIM IS THAT IT IS COPIED. A
stored lease that was merely REFERENCED could be replaced or deleted
from Manage Lease Agreements afterwards, and the document would
change under a signature. The suite deletes the original out from
under the envelope and requires the envelope to still have its own.

SECTION 6 ASKS THE INSTRUMENT where the new row action goes.
''',
         r'''does not.

SECTION 5 IS THE DOCUMENT. Until ES-10 (26 Oct 2026) it proved that
the lease already on the tenant record was COPIED onto the envelope.
His decision that day removed that choice - since ES-9 the file on a
record is the lease that tenancy already signed, or nothing - so the
section now proves the opposite door is shut: a tenancy WITH a lease
on its record and a POST that names it, with nothing attached, makes
no envelope. test_attach_only.py is that round's own suite.

SECTION 6 ASKS THE INSTRUMENT where the new row action goes.
'''),
        (r'''        '  and reading the first address through tenant_emails':
            'tenant_emails' in code,
        'the lease already on the record can be used':
            'tenant_lease_agreement' in code and 'stored' in mk,
        '  and is COPIED onto the envelope, never referenced':
            'ContentFile(stored.read())' in code,
        'the pages are rendered when the envelope is made':
            'render_pages' in code,
''',
         r'''        '  and reading the first address through tenant_emails':
            'tenant_emails' in code,
        # ES-10, 26 Oct 2026 - THE LEASE ALREADY ON THE RECORD IS NO
        # LONGER OFFERED, his decision. Its two claims went with it;
        # test_attach_only.py asserts the absence.
        'the pages are rendered when the envelope is made':
            'render_pages' in code,
'''),
        (r'''               'a tenancy with one person offers one signer, not a blank '
               'second one pretending to be somebody')
            ok('already on this tenant record' in body,
               '  and the lease already on the record is offered')

            # ---- (d) THE REFUSALS
''',
         r'''               'a tenancy with one person offers one signer, not a blank '
               'second one pretending to be somebody')
            # ES-10, 26 Oct 2026 - and the lease on the record is NOT
            # offered, whatever is there.
            ok('already on this tenant record' not in body,
               '  and the lease already on the record is not offered - '
               'a lease for signature is always attached (ES-10)')

            # ---- (d) THE REFUSALS
'''),
        (r'''
            # ==========================================================
            head('5. THE STORED LEASE IS COPIED, NOT REFERENCED')
            # ==========================================================
            #
            # A reference would let Manage Lease Agreements replace or
            # delete the document AFTER it had been signed, and a lease
            # that changed under a signature is the one thing ES-2's
            # hash exists to make impossible.
            alone2 = M.tenant.objects.create(
                prop=a_prop(9), tenant_type='Individual',
''',
         r'''
            # ==========================================================
            head('5. THE LEASE ON THE RECORD IS NEVER THE DOCUMENT')
            # ==========================================================
            #
            # ES-10, 26 Oct 2026. Until today this section proved the
            # stored lease was COPIED onto the envelope. That choice is
            # gone: a record's lease is the one already signed, and a
            # hand-made POST that names it gets the empty-upload answer.
            alone2 = M.tenant.objects.create(
                prop=a_prop(9), tenant_type='Individual',
'''),
        (r'''            alone2.tenant_lease_agreement.save(
                'spiropoulou.pdf', ContentFile(a_pdf(3)), save=True)
            stored_name = alone2.tenant_lease_agreement.name

            r = c.post('/lease-signing/new/?tenant=%d' % alone2.pk, {
                'tenant_id': alone2.pk, 'document': 'stored',
''',
         r'''            alone2.tenant_lease_agreement.save(
                'spiropoulou.pdf', ContentFile(a_pdf(3)), save=True)
            r = c.post('/lease-signing/new/?tenant=%d' % alone2.pk, {
                'tenant_id': alone2.pk, 'document': 'stored',
'''),
        (r'''                'signer_1_email': 'anastasia@example.com',
                'expiry_days': '7'})
            env2 = M.LeaseSigning.objects.filter(tenant=alone2).first()
            ok(env2 is not None,
               'the lease already on the record makes an envelope with '
               'no upload at all', r.status_code)
            if env2 is not None:
                ok(env2.page_count == 3,
                   '  and it is really that document, three pages of it',
                   env2.page_count)
                ok(env2.original_pdf.name != stored_name,
                   '  stored under its OWN name, not the record one',
                   env2.original_pdf.name)

                # NOW TAKE THE ORIGINAL AWAY.
                alone2.tenant_lease_agreement.delete(save=True)
                env2.refresh_from_db()
                env2.original_pdf.open('rb')
                try:
                    kept = env2.original_pdf.read()
                finally:
                    env2.original_pdf.close()
                ok(kept[:4] == b'%PDF',
                   '  and DELETING the lease off the tenant record leaves '
                   'the envelope intact - which a reference would not '
                   'have done, and a signature over a vanished document '
                   'is the failure ES-2 hash exists to prevent')

            raise Rollback
''',
         r'''                'signer_1_email': 'anastasia@example.com',
                'expiry_days': '7'})
            ok(r.status_code == 302 and not M.LeaseSigning.objects.filter(
                   tenant=alone2).exists(),
               'a POST naming the lease already on the record, with '
               'nothing attached, makes NO envelope - it comes back to '
               'the form (ES-10)', r.status_code)
            ok(bool(alone2.tenant_lease_agreement),
               '  and the lease on the record is untouched')

            raise Rollback
'''),
        (r'''gate = read(GATE)
ok("'%s'" % ME in gate, '  and on the push gate suite list')
ok('ContentFile(stored.read())' in gate,
   '  with a sentinel that would notice the stored lease becoming a '
   'reference')
ok('from .lease_signing_sign import _invite' in gate,
   '  and one that would notice a second spelling of mint-and-send')
''',
         r'''gate = read(GATE)
ok("'%s'" % ME in gate, '  and on the push gate suite list')
# ES-10, 26 Oct 2026 - the stored-lease copy went with the choice; the
# row that guarded it now guards its absence.
ok("request.POST.get('document') == 'stored'" in gate,
   '  with a sentinel that would notice the stored lease coming back')
ok('from .lease_signing_sign import _invite' in gate,
   '  and one that would notice a second spelling of mint-and-send')
'''),
    ]),
    (os.path.join('test_sentinels.py'), [
        (r'''        'lease_signing_create.py WITH it on 24 Oct, and ES-6 is the '
        'first round since to back that file up',
    'ContentFile(stored.read())':
        'a stored lease is COPIED onto the envelope - ES-3b created '
        'lease_signing_create.py WITH it, and ES-6 is the first round '
        'since to back that file up',
    # THE THIRTEENTH TO FIFTEENTH, 25 OCT 2026 - REVEALED, NOT BROKEN,
    # and the same story as the twelfth.
''',
         r'''        'lease_signing_create.py WITH it on 24 Oct, and ES-6 is the '
        'first round since to back that file up',
    # (THE SEVENTEENTH - the COPY of a stored lease - WENT WITH THE
    # CODE, ES-10, 26 Oct 2026: Start e-signing no longer offers the
    # lease on the record, and its row now asks for the ABSENCE of that
    # choice, which every earlier version had, so it is not blind.)
    # THE THIRTEENTH TO FIFTEENTH, 25 OCT 2026 - REVEALED, NOT BROKEN,
    # and the same story as the twelfth.
'''),
    ]),
    (os.path.join('test_required_promise.py'), [
        (r'''EXPECT = {
    # T2-8, 25 Oct 2026 - 184 -> 188, the four email stars above.
    '1 static required': 188,
    # ES-3b, 24 Oct 2026 - 7 -> 8. The lease upload on the Send for
    # Signature screen, the fifth of that screen's five stars. The
    # script writes it through getElementById with a literal on the
    # right, which is the one script shape this census recognises.
    '2 required set in script': 8,
    '3 stopped by a submit guard': 9,
    '4 cannot be empty': 2,
''',
         r'''EXPECT = {
    # T2-8, 25 Oct 2026 - 184 -> 188, the four email stars above.
    # ES-10, 26 Oct 2026 - 188 -> 189: the lease upload on Start
    # e-signing moved here from row 2. With no stored lease to choose
    # instead, the field is always shown and `required` sits in the
    # markup.
    '1 static required': 189,
    # ES-3b, 24 Oct 2026 - 7 -> 8. The lease upload on the Send for
    # Signature screen, the fifth of that screen's five stars. The
    # script writes it through getElementById with a literal on the
    # right, which is the one script shape this census recognises.
    # ES-10, 26 Oct 2026 - 8 -> 7: that upload is static now (row 1).
    '2 required set in script': 7,
    '3 stopped by a submit guard': 9,
    '4 cannot be empty': 2,
'''),
    ]),
    (os.path.join('test_second_signer.py'), [
        (r'''         'the note under the signers says which case this is'),
        ("'from .lease_signing_sign import _invite':" in sent
         and "'ContentFile(stored.read())':" in sent,
         'ES-3b\'s two sentinels on lease_signing_create.py are pinned, '
         'revealed by ES-6\'s first backup of that file'),
''',
         r'''         'the note under the signers says which case this is'),
        ("'from .lease_signing_sign import _invite':" in sent
         # ES-10, 26 Oct 2026 - the second pin went with the code it
         # pinned; its retirement note stands in its place.
         and ("'ContentFile(stored.read())':" in sent
              or 'THE SEVENTEENTH - the COPY of a stored lease - WENT'
                 in src[SENT]),
         'ES-3b\'s two sentinels on lease_signing_create.py are pinned, '
         'revealed by ES-6\'s first backup of that file'),
'''),
    ]),
    (os.path.join('alv_rowactions.py'), [
        (r'''               'it, beside the ingredient it removes. VC-1, and the same '
               'ruling as edit_asset.',
    },
}
''',
         r'''               'it, beside the ingredient it removes. VC-1, and the same '
               'ruling as edit_asset.',
    },
    # ES-10, 26 Oct 2026 - the sixth of this shape, by his ask: once a
    # lease PDF is chosen on Start e-signing, a viewer icon appears
    # beside its file name and opens THAT file in the PDF viewer modal.
    'lease_signing_create.html': {
        'count': 1,
        'classes': ('icon-pdf',),
        'since': '.bak_attachonly',
        'why': 'View the attached PDF - one control beside the name of the '
               'file just chosen, opening it in the PDF viewer before it is '
               'sent. ES-10, his ask.',
    },
}
'''),
    ]),
    (os.path.join('test_row_exempt.py'), [
        (r'''# The same argument took the placeholder card off
# test_pair_contrast's WCAG exemption in this round.
ok(total == 2, 'it names %d control(s) on %d page(s)'
   % (total, len(RA.NAMED)), total)
for pg, e in sorted(RA.NAMED.items()):
''',
         r'''# The same argument took the placeholder card off
# test_pair_contrast's WCAG exemption in this round.
# ES-10, 26 Oct 2026 - TWO BECAME THREE: the viewer icon beside the
# attached lease on Start e-signing, named by his ask.
ok(total == 3, 'it names %d control(s) on %d page(s)'
   % (total, len(RA.NAMED)), total)
for pg, e in sorted(RA.NAMED.items()):
'''),
        (r'''# RT-1, 18 Oct 2026 - TWO ON TWO. The report walks the live tree, as a
# report should, so the line it prints followed the register down.
ok('NAMED, NOT IN A WRAPPER - 2 button(s) on 2 page(s)' in out,
   'the report names both', out[-500:])
for pg, e in sorted(RA.NAMED.items()):
    ok(pg in out, '  %s appears in it' % pg)
''',
         r'''# RT-1, 18 Oct 2026 - TWO ON TWO. The report walks the live tree, as a
# report should, so the line it prints followed the register down.
# ES-10, 26 Oct 2026 - THREE ON THREE, the viewer icon on Start
# e-signing joining.
ok('NAMED, NOT IN A WRAPPER - 3 button(s) on 3 page(s)' in out,
   'the report names all three', out[-500:])
for pg, e in sorted(RA.NAMED.items()):
    ok(pg in out, '  %s appears in it' % pg)
'''),
    ]),
    (os.path.join('test_row_wrap.py'), [
        (r'''# down, and the arithmetic has to be written down beside it, or the next
# person cannot tell a decision from a regression.
LOOSE_NOW = 2   # RT-1, 18 Oct 2026 - create_meal_plan's one loose trashcan went with the page. The report walks the live tree, as a report should.   # (was 3)   # MD-1, 18 Oct 2026 - E33 collapsed create_meal_plan's three copies of the recipe row into one recipeRowHtml(), so three loose trashcans became one. The first count in this register to go DOWN.   # (was 5)   # VC-1, 14 Oct 2026 - a FOURTH term, and the same kind as AI-1's: pantry_staples' Remove, one control inside the chip that names the staple it removes. It reached this census from the BUTTON one, because btn-link was not on Show-ButtonDrift's colour list and nothing here could see it.   # (was 4)
# AND RA-5 ADDED A THIRD TERM, which is a decision and not a wrap: all
# four are now registered in alv_rowactions.NAMED as single controls
''',
         r'''# down, and the arithmetic has to be written down beside it, or the next
# person cannot tell a decision from a regression.
LOOSE_NOW = 3   # ES-10, 26 Oct 2026 - the viewer icon beside the attached lease on Start e-signing, named in alv_rowactions.NAMED by his ask.   # (was 2)   # RT-1, 18 Oct 2026 - create_meal_plan's one loose trashcan went with the page. The report walks the live tree, as a report should.   # (was 3)   # MD-1, 18 Oct 2026 - E33 collapsed create_meal_plan's three copies of the recipe row into one recipeRowHtml(), so three loose trashcans became one. The first count in this register to go DOWN.   # (was 5)   # VC-1, 14 Oct 2026 - a FOURTH term, and the same kind as AI-1's: pantry_staples' Remove, one control inside the chip that names the staple it removes. It reached this census from the BUTTON one, because btn-link was not on Show-ButtonDrift's colour list and nothing here could see it.   # (was 4)
# AND RA-5 ADDED A THIRD TERM, which is a decision and not a wrap: all
# four are now registered in alv_rowactions.NAMED as single controls
'''),
    ]),
    (os.path.join('test_vocabulary.py'), [
        (r'''# retired the page, and an exemption for a control nobody can reach is
# a line nobody can check. This counts the register as it stands.
ok(len(ra.NAMED) == 2
   and sum(v['count'] for v in ra.NAMED.values()) == 2,
   '  which makes two such controls on two pages',
   {k: v['count'] for k, v in ra.NAMED.items()})
ok(ra.FAMILY.get('edit') < ra.FAMILY.get('delete'),
''',
         r'''# retired the page, and an exemption for a control nobody can reach is
# a line nobody can check. This counts the register as it stands.
# ES-10, 26 Oct 2026 - THREE AND THREE: the viewer icon beside the
# attached lease on Start e-signing, named by his ask.
ok(len(ra.NAMED) == 3
   and sum(v['count'] for v in ra.NAMED.values()) == 3,
   '  which makes three such controls on three pages',
   {k: v['count'] for k, v in ra.NAMED.items()})
ok(ra.FAMILY.get('edit') < ra.FAMILY.get('delete'),
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
    raise SystemExit('ES-10 REFUSED: %s' % msg)


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
    if "'test_attach_only.py'" in read(pq):
        print('ES-10 already applied.')
        return 0

    sys.path.insert(0, root)
    import alv_tree as T

    if "'test_never_overwrite.py'" not in read(pq):
        refuse('ES-9 is not applied - this round registers after it.')
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
    q = swap(q, """    'test_never_overwrite.py'
)""", """    'test_never_overwrite.py',
    # ES-10, 26 Oct 2026 - Start e-signing attaches the lease, always.
    'test_attach_only.py'
)""", '%s (the suites)' % PS1)
    # THE ES-3b ROW GUARDED THE COPY OF A STORED LEASE; it now guards the
    # absence of that choice.
    q = swap(
        q,
        """    @{ File = 'pages/views/lease_signing_create.py'; Text = 'ContentFile(stored.read())'; What = 'ES-3b: the lease already on the tenant record is COPIED onto the envelope, never referenced - that file can be replaced or deleted from Manage Lease Agreements, and a document that changed under a signature is the one thing ES-2 hash exists to make impossible' },""",
        """    @{ File = 'pages/views/lease_signing_create.py'; Text = "request.POST.get('document') == 'stored'"; Absent = $true; Code = $true; What = 'ES-10: Start e-signing never uses the lease already on the tenant record - since ES-9 that is the lease the tenancy already signed, and offering it would send a signed lease out to be signed again' },""",
        '%s (the sentinels)' % PS1)
    out[pq] = q

    ptr = os.path.join(root, TREE)
    out[ptr] = swap(out.get(ptr, read(ptr)), """    'test_never_overwrite.py',
]""", """    'test_never_overwrite.py',
    # ES-10, 26 Oct 2026 - Start e-signing attaches the lease, always.
    'test_attach_only.py',
]""", '%s (CONVERTED)' % TREE)

    pd = os.path.join(root, ROUNDS)
    out[pd] = swap(out.get(pd, read(pd)), """    '.bak_neveroverwrite',
]""", """    '.bak_neveroverwrite',
    # ES-10, 26 Oct 2026 - Start e-signing attaches the lease, always.
    '.bak_attachonly',
]""", '%s (ROUNDS)' % ROUNDS)

    pw = os.path.join(root, WD)
    w = out.get(pw, read(pw))
    n = re.search(r'CONVERTED_N = (\d+)', w)
    if not n:
        refuse('%s: CONVERTED_N is not there' % WD)
    out[pw] = swap(w, 'CONVERTED_N = %s' % n.group(1),
                   'CONVERTED_N = %d   # ES-10, 26 Oct 2026 - this round '
                   'own suite   # (was %s)'
                   % (int(n.group(1)) + 1, n.group(1)),
                   '%s (CONVERTED_N)' % WD)

    # ---------------------------------------------------------- THE GATES
    cv = out[os.path.join(root, 'pages', 'views', 'lease_signing_create.py')]
    if "== 'stored'" in cv or '_stored_pdf' in cv:
        refuse('Start e-signing still reads the lease on the tenant record.')
    ct = out[os.path.join(root, 'pages', 'templates',
                          'lease_signing_create.html')]
    if 'value="stored"' in ct:
        refuse('Start e-signing still offers the lease on the tenant record.')

    if CHECK:
        print('ES-10 --check: %d file(s) would change, none written; %d '
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
    print('ES-10 applied - Start e-signing attaches the lease, always; the '
          'lease on the tenant record is never offered.')
    print('      %d file(s) written, backed up to %s' % (len(out), SUFFIX))
    print('      %d file(s) ship with it, wired in rather than written'
          % len(CREATES))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
