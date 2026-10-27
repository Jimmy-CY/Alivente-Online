# -*- coding: utf-8 -*-
"""apply_lease_status.py - round LS-1, 27 Oct 2026.

RELEASE 26 - LEASE SIGNING STATUS, AND THREE BACKLOG FIXES. His decisions
of 27 October.

    - LEASE SIGNING STATUS: a read-only Tenants report of where every lease
      out for signature stands, for anyone who can see Tenants (Stella).
      Lease Signing itself stays superuser only. Ships its view and
      template; routed, exported, offered on Tenants, described in help.
    - fsr_commit opens the issue it saved, and says so when it saved none.
    - The daily job's lease-upload reminder and passport/ID expiry email go
      through _send_email_with_retry; the duplicate recipients lookup goes.

Stands on ES-11. Idempotent. Edits backed up to .bak_leasestatus; ships
this patcher, its suite, and the report's view and template. No migration.
"""
import os
import re
import sys

SUFFIX = '.bak_leasestatus'
MARK = 'LS-1, 27 Oct 2026'
CHECK = False
CREATES = (
    'test_lease_status.py',
    os.path.join('pages', 'views', 'lease_signing_status.py'),
    os.path.join('pages', 'templates', 'tenant_lease_signing_status.html'),
)

PS1 = 'Push-PendingChanges.ps1'
TREE = 'alv_tree.py'
ROUNDS = 'alv_rounds.py'
WD = 'test_waiting_down.py'

SWAPS = [
    (os.path.join('pages', 'urls.py'), [
        (r'''    path('tenant_lease_agreement/', views.tenant_lease_agreement, name='tenant_lease_agreement'),
    path('lease-timeline/', views.lease_timeline_view, name='lease_timeline'),
    path('tenant-payment-days/', views.tenant_payment_days_view,
         name='tenant_payment_days'),
''',
         r'''    path('tenant_lease_agreement/', views.tenant_lease_agreement, name='tenant_lease_agreement'),
    path('lease-timeline/', views.lease_timeline_view, name='lease_timeline'),
    # LS-1, 27 Oct 2026 - the read-only Lease Signing Status report.
    path('tenant-lease-signing/', views.lease_signing_status,
         name='lease_signing_status'),
    path('tenant-payment-days/', views.tenant_payment_days_view,
         name='tenant_payment_days'),
'''),
    ]),
    (os.path.join('pages', 'views', '__init__.py'), [
        (r'''# URLconf no matter how correct it is - RV-1 learned that on 23 Oct.
from .lease_signing import *  # noqa: F401, F403
# ES-4, 24 Oct 2026 - the signing page itself. Same note as above: a
# view missing from __all__ does not exist to the URLconf.
''',
         r'''# URLconf no matter how correct it is - RV-1 learned that on 23 Oct.
from .lease_signing import *  # noqa: F401, F403
from .lease_signing_status import *  # noqa: F401, F403  LS-1, 27 Oct 2026
# ES-4, 24 Oct 2026 - the signing page itself. Same note as above: a
# view missing from __all__ does not exist to the URLconf.
'''),
    ]),
    (os.path.join('pages', 'templates', 'tenant.html'), [
        (r'''          <a href="{% url 'tenant_payment_days' %}" class="ui-menu-item" role="menuitem">
            <i class="fas fa-stopwatch"></i> Payment Behaviour
          </a>
        </div>
      </div>

''',
         r'''          <a href="{% url 'tenant_payment_days' %}" class="ui-menu-item" role="menuitem">
            <i class="fas fa-stopwatch"></i> Payment Behaviour
          </a>
          {# LS-1, 27 Oct 2026 - the read-only Lease Signing Status report. #}
          <a href="{% url 'lease_signing_status' %}" class="ui-menu-item" role="menuitem">
            <i class="fas fa-file-signature"></i> Lease Signing Status
          </a>
        </div>
      </div>

'''),
        (r'''          <a href="{% url 'tenant_payment_days' %}" class="action-more-item" role="menuitem">
            <i class="fas fa-stopwatch"></i> Payment Behaviour
          </a>
        </div>
''',
         r'''          <a href="{% url 'tenant_payment_days' %}" class="action-more-item" role="menuitem">
            <i class="fas fa-stopwatch"></i> Payment Behaviour
          </a>
          <a href="{% url 'lease_signing_status' %}" class="action-more-item" role="menuitem">
            <i class="fas fa-file-signature"></i> Lease Signing Status
          </a>
        </div>
'''),
    ]),
    (os.path.join('pages', 'help_content', 'operational.html'), [
        (r'''      <li><strong>View</strong> a full Tenant Details Report as a print-friendly summary</li>
      <li><strong>View</strong> the scanned lease agreement PDF inline in a popup</li>
      <li><strong>Jump</strong> to related screens: Lease Timeline, Open Invoices, Lease Renewals, Payment Behaviour</li>
    </ul>

''',
         r'''      <li><strong>View</strong> a full Tenant Details Report as a print-friendly summary</li>
      <li><strong>View</strong> the scanned lease agreement PDF inline in a popup</li>
      <li><strong>Jump</strong> to related screens: Lease Timeline, Open Invoices, Lease Renewals, Payment Behaviour, Lease Signing Status</li>
    </ul>

'''),
        (r'''
        <p class="mb-0" style="font-size:13px; margin-top:8px;"><!-- ES-11, 26 Oct 2026 --><em>Include non-active tenants</em> widens the list to tenancies that are not active &mdash; ended ones, and ones that have not started yet. It will do little until a current lease ends, since a tenancy finishing before August contributes nothing.</p>
      </div>
    </div>
''',
         r'''
        <p class="mb-0" style="font-size:13px; margin-top:8px;"><!-- ES-11, 26 Oct 2026 --><em>Include non-active tenants</em> widens the list to tenancies that are not active &mdash; ended ones, and ones that have not started yet. It will do little until a current lease ends, since a tenancy finishing before August contributes nothing.</p>
      </div>
    </div>
    <!-- LS-1, 27 Oct 2026 - the read-only Lease Signing Status report. -->
    <div class="card mb-3" style="border-left:4px solid #0e7c8b;">
      <div class="card-body">
        <h6 style="color:#0e7c8b;"><i class="fas fa-file-signature"></i> <strong>Lease Signing Status</strong> <small class="text-muted">(top-right button)</small></h6>
        <p class="mb-1">Where every lease out for e-signing stands, in plain words &mdash; for anyone who can see Tenants. It is read only: it does not open the envelopes, show the documents, or act on them; Lease Signing itself stays with the superuser.</p>
        <ul class="mb-0" style="font-size:13px;">
          <li><strong>The four boxes</strong> &mdash; with tenants to sign &middot; waiting for Alivente (to sign first, or to approve) &middot; declined or lapsed &middot; completed this month.</li>
          <li><strong>Each row</strong> &mdash; tenant, property and lease period; where it stands, with the date it was sent and the last reminder; who still has to sign; when the link expires.</li>
          <li><strong>Include finished</strong> adds the completed and cancelled ones; by default you see what is still open, and anything declined or lapsed.</li>
          <li>Reminders go out automatically on day 3 and the day before the link lapses. A tenant's question about an envelope &mdash; a lost email, a lapsed link, a change to the lease &mdash; goes to Demetri.</li>
        </ul>
      </div>
    </div>
'''),
    ]),
    (os.path.join('pages', 'views', 'issues.py'), [
        (r'''@permission_required('auth.can_edit_issues', raise_exception=True)
def fsr_commit(request):
    if request.method == "POST":
        form = IssuesForm(request.POST or None)
        if form.is_valid():
            form.save()
            messages.success(request, "Issue Added Successfully")
    temp_results = issues.objects.all().order_by('-issues_id')
    latest_issue = temp_results.first()
    if latest_issue is None:
        messages.error(request, "No issue could be found to display.")
        return redirect("fsr")
    is_id = latest_issue.issues_id
    return redirect(reverse("fsr_details", args=[is_id]) + "?from=fsr_add&origin=fsr")


''',
         r'''@permission_required('auth.can_edit_issues', raise_exception=True)
def fsr_commit(request):
    # LS-1, 27 Oct 2026 (backlog) - THE ISSUE THIS REQUEST SAVED, not the newest one
    # in the table: two people adding at once were each sent to whichever
    # row landed last. And a form that did not validate used to be
    # dropped without a word and land on somebody else's issue; it now
    # says so and goes back to the form.
    if request.method != "POST":
        return redirect("fsr_add")
    form = IssuesForm(request.POST)
    if not form.is_valid():
        problems = '; '.join(
            '%s: %s' % (k, ' '.join(v)) for k, v in form.errors.items())
        messages.error(request, "The issue was not saved - %s" % problems)
        return redirect("fsr_add")
    saved = form.save()
    messages.success(request, "Issue Added Successfully")
    return redirect(reverse("fsr_details", args=[saved.pk])
                    + "?from=fsr_add&origin=fsr")


'''),
    ]),
    (os.path.join('pages', 'management', 'commands', 'check_lease_renewal_and_invoices.py'), [
        (r'''                return False

            # Create message
            # Get recipients with TO/CC split
            recipients = get_email_recipients('new_lease_upload')

            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = email_user
''',
         r'''                return False

            # Create message. LS-1, 27 Oct 2026 (backlog) - the recipients are the
            # ones read above; the second lookup that stood here asked the
            # same question twice.
            msg = MIMEMultipart('alternative')
            msg['From'] = email_user
'''),
        (r'''            msg.attach(part2)

            # SMTP setup
            if email_use_ssl:
                smtp_object = smtplib.SMTP_SSL(email_host, email_port, timeout=60)
            else:
                smtp_object = smtplib.SMTP(email_host, email_port, timeout=60)
                smtp_object.ehlo()
                if email_use_tls:
                    smtp_object.starttls()

            smtp_object.login(email_user, email_password)

            # Send email
            text = msg.as_string()
            smtp_object.sendmail(email_user, recipients['all'], text)

            self.stdout.write('✅ New lease upload reminder email sent successfully!')
            logger.info('New lease upload reminder email sent successfully')
            return True

        except smtplib.SMTPAuthenticationError as e:
''',
         r'''            msg.attach(part2)

            # LS-1, 27 Oct 2026 (backlog) - THROUGH THE ONE SENDER, so a slow or
            # dropped SMTP connection is retried with backoff like the main
            # notification, instead of losing the day's reminder.
            return self._send_email_with_retry(
                msg, email_user, recipients['all'],
                label='New lease upload reminder')

        except smtplib.SMTPAuthenticationError as e:
'''),
        (r'''            msg.attach(MIMEText(html_body, 'html', 'utf-8'))

            if email_use_ssl:
                smtp_object = smtplib.SMTP_SSL(email_host, email_port, timeout=60)
            else:
                smtp_object = smtplib.SMTP(email_host, email_port, timeout=60)
                smtp_object.ehlo()
                if email_use_tls:
                    smtp_object.starttls()

            smtp_object.login(email_user, email_password)
            smtp_object.sendmail(email_user, recipients['all'], msg.as_string())

            self.stdout.write(f'    ✅ Sent to workspace "{workspace.name}"')
            logger.info(f'Passport expiry email sent for workspace {workspace.name}')
            return True

        except smtplib.SMTPAuthenticationError as e:
''',
         r'''            msg.attach(MIMEText(html_body, 'html', 'utf-8'))

            # LS-1, 27 Oct 2026 (backlog) - through the one sender, with its retry.
            return self._send_email_with_retry(
                msg, email_user, recipients['all'],
                label='Passport expiry email (%s)' % workspace.name)

        except smtplib.SMTPAuthenticationError as e:
'''),
    ]),
    (os.path.join('test_bar_height.py'), [
        (r'''# a census that selects the two position tones and not the danger
# tone.   # (was 91)
N_LOOSE, N_LOOSE_H = 90, 11   # ES-7b, 25 Oct 2026 - the Delete envelope button in its own card on the envelope page, at a height already in the set.   # (was 89)   # ES-7, 25 Oct 2026 - the two Save buttons on the Signature and Stamp cards, at a height already in the set.   # (was 87)   # ES-3b, 24 Oct 2026 - Choose a different tenant, which sits in a form card rather than in the action bar. N_LOOSE_H does not move: 35px is a height this set already held.   # (was 86)   # LV-1, 16 Oct 2026 - three of the 25 retoned buttons sit in a card or loose on a page. This census selects on a house class, so it could not see them while a LEAVE entry was keeping them Bootstrap-coloured. N_LOOSE_H does not move - all three land on heights the set already held.   # (was 83)   # NV-1c, 16 Oct 2026 - the two comment controls. They were .status-btn, which this census does not select, and they sit in a comment thread rather than a table, so they land in the loose set. 34px was already one of its eleven heights, so N_LOOSE_H does not move.   # (was 81)   # VC-1, 14 Oct 2026 - edit_asset Take Photo at 35px and my_profile Upload Photo at 31px, both <label> file pickers that had no house class until this round. 35 is a height this set did not hold before.   # (was 80 and 10)   # DB-5 - the side column left the
# loose set, and the two heights it invented went with it
# (was 82 and 12)   # E-10 - and the four loose in
''',
         r'''# a census that selects the two position tones and not the danger
# tone.   # (was 91)
N_LOOSE, N_LOOSE_H = 92, 11   # LS-1, 27 Oct 2026 - Include finished and Back in the Lease Signing Status report head, at heights the set already held.   # (was 90)   # ES-7b, 25 Oct 2026 - the Delete envelope button in its own card on the envelope page, at a height already in the set.   # (was 89)   # ES-7, 25 Oct 2026 - the two Save buttons on the Signature and Stamp cards, at a height already in the set.   # (was 87)   # ES-3b, 24 Oct 2026 - Choose a different tenant, which sits in a form card rather than in the action bar. N_LOOSE_H does not move: 35px is a height this set already held.   # (was 86)   # LV-1, 16 Oct 2026 - three of the 25 retoned buttons sit in a card or loose on a page. This census selects on a house class, so it could not see them while a LEAVE entry was keeping them Bootstrap-coloured. N_LOOSE_H does not move - all three land on heights the set already held.   # (was 83)   # NV-1c, 16 Oct 2026 - the two comment controls. They were .status-btn, which this census does not select, and they sit in a comment thread rather than a table, so they land in the loose set. 34px was already one of its eleven heights, so N_LOOSE_H does not move.   # (was 81)   # VC-1, 14 Oct 2026 - edit_asset Take Photo at 35px and my_profile Upload Photo at 31px, both <label> file pickers that had no house class until this round. 35 is a height this set did not hold before.   # (was 80 and 10)   # DB-5 - the side column left the
# loose set, and the two heights it invented went with it
# (was 82 and 12)   # E-10 - and the four loose in
'''),
    ]),
    (os.path.join('test_js_buttons.py'), [
        (r'''# SCOPE does not move - 117 was and is the narrow half, and the pages
# the flag hides are still the recipe and meal-plan side.
CENSUS_NARROW, CENSUS_WIDE = 126, 151   # ES-7, 25 Oct 2026 - house_marks.html, the Signature and Stamp screen, an ordinary pages/templates page that joins every tree-wide count.   # (was 125, 150)   # ES-6, 25 Oct 2026 - lease_signing_detail.html, the envelope page, an ordinary pages/templates page that joins every tree-wide count.   # (was 124, 149)   # ES-3b, 24 Oct 2026 - the Send for Signature screen, an ordinary page that joins both halves.   # (was 123, 148)   # ES-4, 24 Oct 2026 - the four public signing templates. They are ordinary pages/templates files, so they join both halves - but they contribute ZERO scanner hits, measured: their controls wear .ls-btn, a class of their own, because the pages cannot extend base and so cannot use the house one.   # (was 119, 144)   # ES-3a, 23 Oct 2026 - lease_signing_list.html, the envelope register. An ordinary pages/templates page, so it joins every tree-wide count.   # (was 118, 143)   # RV-1, 23 Oct 2026 - cash_receipt_detail.html. BOTH halves move: unlike meal_plan_print this is an ordinary pages/templates page, so it joins the sweep scope as well as the application count.   # (was 117, 142)   # PP-1, 20 Oct 2026 - meal_plan_print.html. The narrow half does not move: the sweep scope is the 117 pages it has always been.   # (WIDE was 141)   # RD-1, 19 Oct 2026 - the
# quick-look pair. (wide was 139, and 142 before MN-1 retired four
# meal-plan screens.)
HITS_LOOSE, HITS_TIGHT = 694, 692   # ES-7, 25 Oct 2026 - three more house .btn controls on the Signature and Stamp screen, measured by this census. Both matchers rise by the same three.   # (was 691, 689)   # ES-6, 25 Oct 2026 - the envelope page's bar: Approve and attach, Decline, View signed lease and Back. Both matchers rise by the same four.   # (was 687, 685)   # ES-3b, 24 Oct 2026 - Create and sign, Back, and Choose a different tenant. Both matchers rise by the same three. MEASURED PER ROUND rather than split by eye: ES-4 ships four templates in the same bundle and its share is zero, because its buttons are not house .btn ones.   # (was 684, 682)   # ES-3a, 23 Oct 2026 - lease_signing_list.html, the envelope register. An ordinary pages/templates page, so it joins every tree-wide count.   # (was 680, 678)   # RV-1, 23 Oct 2026 - the Receipt Details bar: View receipt, Edit and Back. Both matchers rise by the same three.   # (was 677, 675)   # PP-1, 20 Oct 2026 - the printable plan's two bar controls, Print and Back. Both matchers rise by the same two.   # (was 675, 673)   # RD-1, 19 Oct 2026 - one scanner
# hit per new template, and BOTH matchers rise by the same two.
# (was 673, 671)   # RT-1, 18 Oct 2026 - thirty-three scanner hits went with the four retired screens, and both matchers fall by the same thirty-three.   # (was 706, 704)
''',
         r'''# SCOPE does not move - 117 was and is the narrow half, and the pages
# the flag hides are still the recipe and meal-plan side.
CENSUS_NARROW, CENSUS_WIDE = 127, 152   # LS-1, 27 Oct 2026 - tenant_lease_signing_status.html, the Lease Signing Status report, an ordinary pages/templates page that joins every tree-wide count.   # (was 126, 151)   # ES-7, 25 Oct 2026 - house_marks.html, the Signature and Stamp screen, an ordinary pages/templates page that joins every tree-wide count.   # (was 125, 150)   # ES-6, 25 Oct 2026 - lease_signing_detail.html, the envelope page, an ordinary pages/templates page that joins every tree-wide count.   # (was 124, 149)   # ES-3b, 24 Oct 2026 - the Send for Signature screen, an ordinary page that joins both halves.   # (was 123, 148)   # ES-4, 24 Oct 2026 - the four public signing templates. They are ordinary pages/templates files, so they join both halves - but they contribute ZERO scanner hits, measured: their controls wear .ls-btn, a class of their own, because the pages cannot extend base and so cannot use the house one.   # (was 119, 144)   # ES-3a, 23 Oct 2026 - lease_signing_list.html, the envelope register. An ordinary pages/templates page, so it joins every tree-wide count.   # (was 118, 143)   # RV-1, 23 Oct 2026 - cash_receipt_detail.html. BOTH halves move: unlike meal_plan_print this is an ordinary pages/templates page, so it joins the sweep scope as well as the application count.   # (was 117, 142)   # PP-1, 20 Oct 2026 - meal_plan_print.html. The narrow half does not move: the sweep scope is the 117 pages it has always been.   # (WIDE was 141)   # RD-1, 19 Oct 2026 - the
# quick-look pair. (wide was 139, and 142 before MN-1 retired four
# meal-plan screens.)
HITS_LOOSE, HITS_TIGHT = 697, 695   # LS-1, 27 Oct 2026 - Include finished / Open only and Back on the Lease Signing Status report, measured by this census; both matchers rise by the same three.   # (was 694, 692)   # ES-7, 25 Oct 2026 - three more house .btn controls on the Signature and Stamp screen, measured by this census. Both matchers rise by the same three.   # (was 691, 689)   # ES-6, 25 Oct 2026 - the envelope page's bar: Approve and attach, Decline, View signed lease and Back. Both matchers rise by the same four.   # (was 687, 685)   # ES-3b, 24 Oct 2026 - Create and sign, Back, and Choose a different tenant. Both matchers rise by the same three. MEASURED PER ROUND rather than split by eye: ES-4 ships four templates in the same bundle and its share is zero, because its buttons are not house .btn ones.   # (was 684, 682)   # ES-3a, 23 Oct 2026 - lease_signing_list.html, the envelope register. An ordinary pages/templates page, so it joins every tree-wide count.   # (was 680, 678)   # RV-1, 23 Oct 2026 - the Receipt Details bar: View receipt, Edit and Back. Both matchers rise by the same three.   # (was 677, 675)   # PP-1, 20 Oct 2026 - the printable plan's two bar controls, Print and Back. Both matchers rise by the same two.   # (was 675, 673)   # RD-1, 19 Oct 2026 - one scanner
# hit per new template, and BOTH matchers rise by the same two.
# (was 673, 671)   # RT-1, 18 Oct 2026 - thirty-three scanner hits went with the four retired screens, and both matchers fall by the same thirty-three.   # (was 706, 704)
'''),
    ]),
    (os.path.join('test_recipe_side_b.py'), [
        (r'''N_EDITS, N_PAGES = 31, 13
N_DRIFT, N_DECIDED = 18, 13
GATE_WAS, GATE_NOW = 126, 151   # ES-7, 25 Oct 2026 - house_marks.html, the Signature and Stamp screen, an ordinary pages/templates page that joins every tree-wide count.   # (was 125, 150)   # ES-6, 25 Oct 2026 - lease_signing_detail.html, the envelope page, an ordinary page that joins every tree-wide count.   # (was 124, 149)   # ES-3b, 24 Oct 2026 - the Send for Signature screen, an ordinary page that joins every tree-wide count.   # (was 123, 148)   # ES-4, 24 Oct 2026 - the four public signing templates. They are ordinary pages/templates files, so they join every tree-wide count; they cannot extend base, which is why they are standalone.   # (was 119, 144)   # ES-3a, 23 Oct 2026 - lease_signing_list.html, the envelope register. An ordinary pages/templates page, so it joins every tree-wide count.   # (was 118, 143)   # RV-1, 23 Oct 2026 - cash_receipt_detail.html. The same pair as test_js_buttons and test_recipe_tones: an ordinary pages/templates page joins the sweep scope and the page count alike.   # (was 117, 142)   # PP-1, 20 Oct 2026 - meal_plan_print.html. (GATE_NOW was 141)   # RD-1, 19 Oct 2026 - the quick-look
# pair. (GATE_NOW was 139)   # RT-1, 18 Oct 2026 - the wide census is four meal-plan screens smaller and one planner larger. The narrow half does not move.   # (GATE_NOW was 142)

''',
         r'''N_EDITS, N_PAGES = 31, 13
N_DRIFT, N_DECIDED = 18, 13
GATE_WAS, GATE_NOW = 127, 152   # LS-1, 27 Oct 2026 - tenant_lease_signing_status.html, the Lease Signing Status report, an ordinary pages/templates page that joins every tree-wide count.   # (was 126, 151)   # ES-7, 25 Oct 2026 - house_marks.html, the Signature and Stamp screen, an ordinary pages/templates page that joins every tree-wide count.   # (was 125, 150)   # ES-6, 25 Oct 2026 - lease_signing_detail.html, the envelope page, an ordinary page that joins every tree-wide count.   # (was 124, 149)   # ES-3b, 24 Oct 2026 - the Send for Signature screen, an ordinary page that joins every tree-wide count.   # (was 123, 148)   # ES-4, 24 Oct 2026 - the four public signing templates. They are ordinary pages/templates files, so they join every tree-wide count; they cannot extend base, which is why they are standalone.   # (was 119, 144)   # ES-3a, 23 Oct 2026 - lease_signing_list.html, the envelope register. An ordinary pages/templates page, so it joins every tree-wide count.   # (was 118, 143)   # RV-1, 23 Oct 2026 - cash_receipt_detail.html. The same pair as test_js_buttons and test_recipe_tones: an ordinary pages/templates page joins the sweep scope and the page count alike.   # (was 117, 142)   # PP-1, 20 Oct 2026 - meal_plan_print.html. (GATE_NOW was 141)   # RD-1, 19 Oct 2026 - the quick-look
# pair. (GATE_NOW was 139)   # RT-1, 18 Oct 2026 - the wide census is four meal-plan screens smaller and one planner larger. The narrow half does not move.   # (GATE_NOW was 142)

'''),
    ]),
    (os.path.join('test_recipe_tones.py'), [
        (r'''# ES-7, 25 Oct 2026 - the Signature and Stamp screen joins both. (was 125, 150)
# ES-6, 25 Oct 2026 - the envelope page joins both counts. (was 124, 149)
ok(len(sb.templates(False)) == 126 and len(sb.templates(True)) == 151,
   '  which is %d of %d' % (126, 151),
   '%d of %d' % (len(sb.templates(False)), len(sb.templates(True))))

''',
         r'''# ES-7, 25 Oct 2026 - the Signature and Stamp screen joins both. (was 125, 150)
# ES-6, 25 Oct 2026 - the envelope page joins both counts. (was 124, 149)
# LS-1, 27 Oct 2026 - tenant_lease_signing_status.html, the Lease Signing Status report, an ordinary pages/templates page that joins every tree-wide count.
ok(len(sb.templates(False)) == 127 and len(sb.templates(True)) == 152,
   '  which is %d of %d' % (127, 152),
   '%d of %d' % (len(sb.templates(False)), len(sb.templates(True))))

'''),
    ]),
    (os.path.join('test_subtree_tones.py'), [
        (r'''# ES-6, 25 Oct 2026 - lease_signing_detail.html, the envelope page, an ordinary pages/templates page that joins every tree-wide count.
# ES-7, 25 Oct 2026 - house_marks.html, the Signature and Stamp screen, an ordinary pages/templates page that joins every tree-wide count.
ok(len(tree) == 160, 'a WALK finds 160 templates', len(tree))
ok(len(top) == 134, '  a flat listing finds 134 - 120 was what H7 '
   'counted, 122 after MN-1, and RD-1 adds the quick-look pair',
   len(top))
''',
         r'''# ES-6, 25 Oct 2026 - lease_signing_detail.html, the envelope page, an ordinary pages/templates page that joins every tree-wide count.
# ES-7, 25 Oct 2026 - house_marks.html, the Signature and Stamp screen, an ordinary pages/templates page that joins every tree-wide count.
# LS-1, 27 Oct 2026 - tenant_lease_signing_status.html, the Lease Signing Status report, an ordinary pages/templates page that joins every tree-wide count.
ok(len(tree) == 161, 'a WALK finds 161 templates', len(tree))
ok(len(top) == 135, '  a flat listing finds 135 - 120 was what H7 '
   'counted, 122 after MN-1, and RD-1 adds the quick-look pair',
   len(top))
'''),
    ]),
    (os.path.join('test_tree_roots.py'), [
        (r'''# 143 since 6 Oct: Section E round E-2b added access_denied.html,
# the 403 page, which until then lived in an f-string.
MAIN_N = 152   # ES-7, 25 Oct 2026 - house_marks.html, the Signature and Stamp screen, an ordinary pages/templates page that joins every tree-wide count.   # (was 151)   # ES-6, 25 Oct 2026 - lease_signing_detail.html, the envelope page, an ordinary pages/templates page that joins every tree-wide count.   # (was 150)   # ES-3b, 24 Oct 2026 - the Send for Signature screen, an ordinary page that joins every tree-wide count.   # (was 149)   # ES-4, 24 Oct 2026 - the four public signing templates. They are ordinary pages/templates files, so they join every tree-wide count; they cannot extend base, which is why they are standalone.   # (was 145)   # ES-3a, 23 Oct 2026 - lease_signing_list.html, the envelope register. An ordinary pages/templates page, so it joins every tree-wide count.   # (was 144)   # RV-1, 23 Oct 2026 - cash_receipt_detail.html. This is the shape of the tree, which is what this file is for.   # (was 143)   # PP-1, 20 Oct 2026 - the printable meal plan is a
               # new page: 142 + 1. (was 142)   # RD-1, 19 Oct 2026 - the quick-look dialog adds two:
               # the partial and its shell. (was 140)   # RT-1, 18 Oct 2026 - MN-1 retired four meal-plan screens and the planner replaced them: 143 - 4 + 1. This is the shape of the tree, which is what this file is for.   # (was 143)
''',
         r'''# 143 since 6 Oct: Section E round E-2b added access_denied.html,
# the 403 page, which until then lived in an f-string.
MAIN_N = 153   # LS-1, 27 Oct 2026 - tenant_lease_signing_status.html, the Lease Signing Status report, an ordinary pages/templates page that joins every tree-wide count.   # (was 152)   # ES-7, 25 Oct 2026 - house_marks.html, the Signature and Stamp screen, an ordinary pages/templates page that joins every tree-wide count.   # (was 151)   # ES-6, 25 Oct 2026 - lease_signing_detail.html, the envelope page, an ordinary pages/templates page that joins every tree-wide count.   # (was 150)   # ES-3b, 24 Oct 2026 - the Send for Signature screen, an ordinary page that joins every tree-wide count.   # (was 149)   # ES-4, 24 Oct 2026 - the four public signing templates. They are ordinary pages/templates files, so they join every tree-wide count; they cannot extend base, which is why they are standalone.   # (was 145)   # ES-3a, 23 Oct 2026 - lease_signing_list.html, the envelope register. An ordinary pages/templates page, so it joins every tree-wide count.   # (was 144)   # RV-1, 23 Oct 2026 - cash_receipt_detail.html. This is the shape of the tree, which is what this file is for.   # (was 143)   # PP-1, 20 Oct 2026 - the printable meal plan is a
               # new page: 142 + 1. (was 142)   # RD-1, 19 Oct 2026 - the quick-look dialog adds two:
               # the partial and its shell. (was 140)   # RT-1, 18 Oct 2026 - MN-1 retired four meal-plan screens and the planner replaced them: 143 - 4 + 1. This is the shape of the tree, which is what this file is for.   # (was 143)
'''),
    ]),
    (os.path.join('test_heading_standard.py'), [
        (r'''    'map_view.html',                         # the map page
    'tenant_payment_days.html',    # tenant payment behaviour
    # ES-4, 24 Oct 2026 - THE PUBLIC SIGNING PAGES, and this is not
    # a debt like the rest of this set. The house heading standard is
''',
         r'''    'map_view.html',                         # the map page
    'tenant_payment_days.html',    # tenant payment behaviour
    # LS-1, 27 Oct 2026 - Lease Signing Status wears the same report head
    # as Payment Behaviour (.alv-report-title), so it sits beside it.
    'tenant_lease_signing_status.html',
    # ES-4, 24 Oct 2026 - THE PUBLIC SIGNING PAGES, and this is not
    # a debt like the rest of this set. The house heading standard is
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
    raise SystemExit('LS-1 REFUSED: %s' % msg)


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
    if "'test_lease_status.py'" in read(pq):
        print('LS-1 already applied.')
        return 0

    sys.path.insert(0, root)
    import alv_tree as T

    if "'test_strip_gone.py'" not in read(pq):
        refuse('ES-11 is not applied - this round registers after it.')
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
    q = swap(q, """    'test_strip_gone.py'
)""", """    'test_strip_gone.py',
    # LS-1, 27 Oct 2026 - Lease Signing Status, and three backlog fixes.
    'test_lease_status.py'
)""", '%s (the suites)' % PS1)
    q = swap(
        q,
        """    @{ File = 'pages/templates/home.html'; Text = 'lsa-strip'; Absent = $true; Code = $true;""",
        """    @{ File = 'pages/views/lease_signing_status.py'; Text = "@permission_required('auth.can_access_tenants'"; What = 'LS-1: Lease Signing Status is a Tenants report, behind the Tenants permission - without it the read-only summary is either open to everybody or closed to the person it was built for' },
    @{ File = 'pages/templates/home.html'; Text = 'lsa-strip'; Absent = $true; Code = $true;""",
        '%s (the sentinels)' % PS1)
    out[pq] = q

    ptr = os.path.join(root, TREE)
    out[ptr] = swap(out.get(ptr, read(ptr)), """    'test_strip_gone.py',
]""", """    'test_strip_gone.py',
    # LS-1, 27 Oct 2026 - Lease Signing Status, and three backlog fixes.
    'test_lease_status.py',
]""", '%s (CONVERTED)' % TREE)

    pd = os.path.join(root, ROUNDS)
    out[pd] = swap(out.get(pd, read(pd)), """    '.bak_stripgone',
]""", """    '.bak_stripgone',
    # LS-1, 27 Oct 2026 - Lease Signing Status, and three backlog fixes.
    '.bak_leasestatus',
]""", '%s (ROUNDS)' % ROUNDS)

    pw = os.path.join(root, WD)
    w = out.get(pw, read(pw))
    n = re.search(r'CONVERTED_N = (\d+)', w)
    if not n:
        refuse('%s: CONVERTED_N is not there' % WD)
    out[pw] = swap(w, 'CONVERTED_N = %s' % n.group(1),
                   'CONVERTED_N = %d   # LS-1, 27 Oct 2026 - this round '
                   'own suite   # (was %s)'
                   % (int(n.group(1)) + 1, n.group(1)),
                   '%s (CONVERTED_N)' % WD)

    # ---------------------------------------------------------- THE GATES
    vw = read(os.path.join(root, 'pages', 'views', 'lease_signing_status.py'))
    if "@permission_required('auth.can_access_tenants'" not in vw:
        refuse('the report is not behind the Tenants permission.')
    iss = out[os.path.join(root, 'pages', 'views', 'issues.py')]
    if 'saved = form.save()' not in iss:
        refuse('fsr_commit does not open the issue it saved.')

    if CHECK:
        print('LS-1 --check: %d file(s) would change, none written; %d '
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
    print('LS-1 applied - Lease Signing Status on Tenants; fsr_commit opens '
          'the issue it saved; two daily emails retry.')
    print('      %d file(s) written, backed up to %s' % (len(out), SUFFIX))
    print('      %d file(s) ship with it, wired in rather than written'
          % len(CREATES))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
