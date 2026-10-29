# -*- coding: utf-8 -*-
"""apply_celebration_help.py - round CX-1, 29 Oct 2026.

RELEASE 40 - CELEBRATION EMAILS RETRY, AND HELP ON TASK LIST AND GANTT.

    - send_celebration_notification sends each recipient through
      _send_email_with_retry instead of one SMTP connection of its own with
      no retry; one failure no longer stops the rest.
    - project_task_list.html and project_gantt.html get Help (bar and phone
      More menu) opening the Projects guide on its Views tab.

Stands on VS-1. Idempotent. Edits backed up to .bak_celebhelp; ships this
patcher and its suite. No migration.
"""
import os
import re
import sys

SUFFIX = '.bak_celebhelp'
MARK = 'CX-1, 29 Oct 2026'
CHECK = False
CREATES = (
    'test_celebration_help.py',
)

PS1 = 'Push-PendingChanges.ps1'
TREE = 'alv_tree.py'
ROUNDS = 'alv_rounds.py'
WD = 'test_waiting_down.py'

SWAPS = [
    (os.path.join('pages', 'management', 'commands', 'check_lease_renewal_and_invoices.py'), [
        (r'''
    def send_celebration_notification(self, celebrations_by_recipient):
        """Send email notification for today's celebrations - personalized per recipient"""
        smtp_object = None

        if not celebrations_by_recipient:
''',
         r'''
    def send_celebration_notification(self, celebrations_by_recipient):
        """Send email notification for today's celebrations - personalized per recipient

        CX-1, 29 Oct 2026 - THROUGH _send_email_with_retry, like every other
        email this job sends. It opened one SMTP connection of its own with
        no retry, so a mail-server hiccup at 06:00 UTC lost every
        celebration email for the day while the others tried again. Each
        recipient is now sent - and retried - on their own, and one failure
        no longer stops the rest.
        """

        if not celebrations_by_recipient:
'''),
        (r'''            self.stdout.write('=== SENDING CELEBRATION NOTIFICATIONS ===')

            # Get email settings from environment variables
            email_host = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
            email_port = int(os.environ.get('EMAIL_PORT', 465))
            email_user = os.environ.get('EMAIL_USER', 'demetrimanias@gmail.com')
            email_password = os.environ.get('EMAIL_PASSWORD')
            email_use_ssl = os.environ.get('EMAIL_USE_SSL', 'True').lower() == 'true'
            email_use_tls = os.environ.get('EMAIL_USE_TLS', 'False').lower() == 'true'

            if not email_password:
                self.stdout.write('❌ EMAIL_PASSWORD environment variable not set')
                return False

            # SMTP setup (reuse connection for all emails)
            if email_use_ssl:
                smtp_object = smtplib.SMTP_SSL(email_host, email_port, timeout=60)
            else:
                smtp_object = smtplib.SMTP(email_host, email_port, timeout=60)
                smtp_object.ehlo()
                if email_use_tls:
                    smtp_object.starttls()

            smtp_object.login(email_user, email_password)

            today = date.today()
''',
         r'''            self.stdout.write('=== SENDING CELEBRATION NOTIFICATIONS ===')

            # The sender; connection, login and retries are
            # _send_email_with_retry's (CX-1).
            email_user = os.environ.get('EMAIL_USER', 'demetrimanias@gmail.com')
            sent, failed = 0, []

            today = date.today()
'''),
        (r'''                msg.attach(part2)

                # Send email to this recipient
                text = msg.as_string()
                smtp_object.sendmail(email_user, [recipient_email], text)

                self.stdout.write(f'✅ Celebration email sent to {recipient_email}')

            logger.info(f'Celebration notifications sent to {len(celebrations_by_recipient)} recipient(s)')
            return True

        except smtplib.SMTPAuthenticationError as e:
            error_msg = f"SMTP Authentication Error: {e}"
            logger.error(error_msg)
            self.stdout.write(f'❌ {error_msg}')
            return False
        except smtplib.SMTPException as e:
            error_msg = f"SMTP Error: {e}"
            logger.error(error_msg)
            self.stdout.write(f'❌ {error_msg}')
            return False
        except Exception as e:
            error_msg = f"Error sending celebration notification email: {e}"
            logger.error(error_msg, exc_info=True)
            self.stdout.write(f'❌ {error_msg}')
            return False
        finally:
            if smtp_object:
                try:
                    smtp_object.quit()
                except Exception:
                    pass

    def send_issue_comments_notification(self, comments, report_date):
''',
         r'''                msg.attach(part2)

                # Send email to this recipient - with retries (CX-1)
                if self._send_email_with_retry(
                        msg, email_user, [recipient_email],
                        label='Celebration email to %s' % recipient_email):
                    sent += 1
                else:
                    failed.append(recipient_email)

            logger.info(f'Celebration notifications sent to {sent} recipient(s)')
            if failed:
                self.stdout.write(
                    '❌ Celebration email failed for: %s' % ', '.join(failed))
                return False
            return True

        except Exception as e:
            error_msg = f"Error sending celebration notification email: {e}"
            logger.error(error_msg, exc_info=True)
            self.stdout.write(f'❌ {error_msg}')
            return False

    def send_issue_comments_notification(self, comments, report_date):
'''),
    ]),
    (os.path.join('pages', 'templates', 'projects', 'project_task_list.html'), [
        (r'''{% extends 'base.html' %}
{% load static %}

{% block title %}
''',
         r'''{% extends 'base.html' %}
{% load static %}
{% load help_modal_tags %}

{% block title %}
'''),
        (r'''    </button>

    <!-- Mobile: More menu (hidden on desktop) -->
    <div class="action-more-wrapper" data-menu>
''',
         r'''    </button>

    {# CX-1, 29 Oct 2026 - Help, as on Projects and Project Detail. #}
    <button type="button" class="btn action-secondary" data-toggle="modal" data-target="#projectsHelpModal" data-help-views>
      <i class="fas fa-question-circle"></i> {% if language == 'greek' %}Βοήθεια{% else %}Help{% endif %}
    </button>

    <!-- Mobile: More menu (hidden on desktop) -->
    <div class="action-more-wrapper" data-menu>
'''),
        (r'''        <button type="button" class="action-more-item" id="exportBtnMobile" role="menuitem">
          <i class="fas fa-file-excel"></i> {% if language == 'greek' %}Εξαγωγή Excel{% else %}Export Excel{% endif %}
        </button>
      </div>
''',
         r'''        <button type="button" class="action-more-item" id="exportBtnMobile" role="menuitem">
          <i class="fas fa-file-excel"></i> {% if language == 'greek' %}Εξαγωγή Excel{% else %}Export Excel{% endif %}
        </button>
        <button type="button" class="action-more-item" data-toggle="modal" data-target="#projectsHelpModal" data-help-views role="menuitem">
          <i class="fas fa-question-circle"></i> {% if language == 'greek' %}Βοήθεια{% else %}Help{% endif %}
        </button>
      </div>
'''),
        (r'''</script>

{% endblock %}

''',
         r'''</script>

<script>
// CX-1, 29 Oct 2026 - Help opens the Projects guide on its Views tab,
// which is the one about this page.
document.querySelectorAll('[data-help-views]').forEach(function (b) {
  b.addEventListener('click', function () {
    if (window.jQuery) { jQuery('#projects__prjReports-tab').tab('show'); }
  });
});
</script>
{% render_help_modal "projects" %}
{% endblock %}

'''),
    ]),
    (os.path.join('pages', 'templates', 'projects', 'project_gantt.html'), [
        (r'''{% extends 'base.html' %}
{% load static %}

{% block title %}
''',
         r'''{% extends 'base.html' %}
{% load static %}
{% load help_modal_tags %}

{% block title %}
'''),
        (r'''      <i class="fas fa-print"></i> Print
    </button>
    <a href="{% url 'projects_detail' project.project_id %}" class="btn action-back" title="Back to Project">
      <i class="fas fa-arrow-left"></i>
''',
         r'''      <i class="fas fa-print"></i> Print
    </button>
    {# CX-1, 29 Oct 2026 - Help, as on Projects and Project Detail. #}
    <button type="button" class="btn action-secondary" data-toggle="modal" data-target="#projectsHelpModal" data-help-views>
      <i class="fas fa-question-circle"></i> Help
    </button>
    <!-- Mobile: More menu (hidden on desktop) -->
    <div class="action-more-wrapper" data-menu>
      <button type="button" class="btn action-more-btn" id="actionMoreBtn" data-menu-toggle aria-label="More actions" aria-expanded="false">
        <i class="fas fa-ellipsis-v"></i>
      </button>
      <div class="action-more-menu" id="actionMoreMenu" data-menu-panel role="menu" hidden>
        <button type="button" class="action-more-item" data-toggle="modal" data-target="#projectsHelpModal" data-help-views role="menuitem">
          <i class="fas fa-question-circle"></i> Help
        </button>
      </div>
    </div>
    <a href="{% url 'projects_detail' project.project_id %}" class="btn action-back" title="Back to Project">
      <i class="fas fa-arrow-left"></i>
'''),
        (r'''</script>

{% endblock %}

''',
         r'''</script>

<script>
// CX-1, 29 Oct 2026 - Help opens the Projects guide on its Views tab,
// which is the one about this page.
document.querySelectorAll('[data-help-views]').forEach(function (b) {
  b.addEventListener('click', function () {
    if (window.jQuery) { jQuery('#projects__prjReports-tab').tab('show'); }
  });
});
</script>
{% render_help_modal "projects" %}
{% endblock %}

'''),
    ]),
    (os.path.join('test_bar_height.py'), [
        (r'''
BAR, ROW, MODAL = 35, 34, 38
N_BAR, N_ROW, N_MODAL = 290, 122, 103   # GL-3, 29 Oct 2026 - the Greek Details pop-up, Cancel and Done, on Tenant Edit and Tenant Add.   # (N_MODAL was 99)   # GE-1, 28 Oct 2026 - Generate gains Send for e-signing beside Download Word, and the envelope page a Word version button.   # (N_BAR was 288)   # GL-1, 28 Oct 2026 - the Company Details screen's bar, Save and Back.   # (N_BAR was 286)   # HK-4, 28 Oct 2026 - Help on the Project Details bar, his finding   # (N_BAR was 285)   # CR-2, 27 Oct 2026 - emailing a receipt: Email receipt in the Receipt Details bar (both arms of its if), the paper-plane in the Receipts row (live and greyed), and Cancel and Send in the pop-up on both pages.   # (was 283, 120, 95)   # ES-9, 26 Oct 2026 - the envelope page draws a greyed Approve and attach when no tenancy is free to receive the lease; both arms of the if count.   # (was 282, 120)   # HK-1, 26 Oct 2026 - the paper-plane left Manage Lease Agreements, his decision; both arms of its superuser check counted, so the row figure falls by two.   # (was 282, 122)   # ES-8, 25 Oct 2026 - the Lease Signing register gains a Help secondary in its bar, and a View-signed-lease icon in its row actions.   # (was 281, 121)   # ES-7, 25 Oct 2026 - the Signature and Stamp screen's bar, Back alone.   # (was 280)   # ES-6, 25 Oct 2026 - the envelope page's bar (Approve and attach, Decline, View signed lease, Back). This census does not resolve a branch, so Approve and Decline count even though they only show while an envelope is awaiting approval.   # (was 276)   # ES-3b, 24 Oct 2026 - the Send for Signature screen (Create and sign, Back) and the Send row action on Manage Lease Agreements. This census does not resolve a branch, so both arms of the perms check count - which is why the row figure moved by two and not by one.   # (was 274, 119)   # ES-3a, 23 Oct 2026 - lease_signing_list.html, the envelope register. An ordinary pages/templates page, so it joins every tree-wide count.   # (was 270, 116)   # RV-1, 23 Oct 2026 - the Receipt Details bar: View receipt, Edit and Back. A new PAGE, so three controls join the census without any existing bar changing.   # (was 267)   # TD-2, 16 Oct 2026 - the two disabled twins. A twin is an .icon-action-btn in a table row, so this census counts it exactly as it counts the button it stands in for - which is the whole idea.   # (was 114)   # NV-1d, 16 Oct 2026 - the View button in the desktop strip, which is inside a table.   # (was 113)   # NV-1c, 16 Oct 2026 - the physical invoice disabled mirror, in the desktop strip, which is inside a table.   # (was 112)   # NV-1b, 16 Oct 2026 - the title deeds Actions cell drew two Bootstrap buttons, which this census cannot see. They are icon-delete and icon-upload now, so two controls join the table-row count without a control being added.   # (was 110)   # PJ-1, 15 Oct 2026 - projects_edit carried its Back control twice, behind an if on from_gantt. This census does not resolve a branch, so it counted both arms; one Back control now, and one count.   # (was 268)   # PV-1, 15 Oct 2026 - the four footer buttons of two hand-rolled invoice viewers. The shared component they moved onto was already in this census, so the count falls by exactly the four that went.   # (was 99)   # VC-1, 14 Oct 2026 - property_assets Take Photo is a <label> that had no house class until this round, so this census could not see it. 35px, in a modal, and named in STRAYS below.   # (was 98)   # DB-5, 12 Oct 2026 - the
# dashboard four joined the bar   # (was 265)   # E-10, 11 Oct 2026 - the
# seven buttons this round paired in CRS modals become visible to
''',
         r'''
BAR, ROW, MODAL = 35, 34, 38
N_BAR, N_ROW, N_MODAL = 292, 122, 103   # CX-1, 29 Oct 2026 - Help joins the Task List and Gantt Chart bars.   # (N_BAR was 290)   # GL-3, 29 Oct 2026 - the Greek Details pop-up, Cancel and Done, on Tenant Edit and Tenant Add.   # (N_MODAL was 99)   # GE-1, 28 Oct 2026 - Generate gains Send for e-signing beside Download Word, and the envelope page a Word version button.   # (N_BAR was 288)   # GL-1, 28 Oct 2026 - the Company Details screen's bar, Save and Back.   # (N_BAR was 286)   # HK-4, 28 Oct 2026 - Help on the Project Details bar, his finding   # (N_BAR was 285)   # CR-2, 27 Oct 2026 - emailing a receipt: Email receipt in the Receipt Details bar (both arms of its if), the paper-plane in the Receipts row (live and greyed), and Cancel and Send in the pop-up on both pages.   # (was 283, 120, 95)   # ES-9, 26 Oct 2026 - the envelope page draws a greyed Approve and attach when no tenancy is free to receive the lease; both arms of the if count.   # (was 282, 120)   # HK-1, 26 Oct 2026 - the paper-plane left Manage Lease Agreements, his decision; both arms of its superuser check counted, so the row figure falls by two.   # (was 282, 122)   # ES-8, 25 Oct 2026 - the Lease Signing register gains a Help secondary in its bar, and a View-signed-lease icon in its row actions.   # (was 281, 121)   # ES-7, 25 Oct 2026 - the Signature and Stamp screen's bar, Back alone.   # (was 280)   # ES-6, 25 Oct 2026 - the envelope page's bar (Approve and attach, Decline, View signed lease, Back). This census does not resolve a branch, so Approve and Decline count even though they only show while an envelope is awaiting approval.   # (was 276)   # ES-3b, 24 Oct 2026 - the Send for Signature screen (Create and sign, Back) and the Send row action on Manage Lease Agreements. This census does not resolve a branch, so both arms of the perms check count - which is why the row figure moved by two and not by one.   # (was 274, 119)   # ES-3a, 23 Oct 2026 - lease_signing_list.html, the envelope register. An ordinary pages/templates page, so it joins every tree-wide count.   # (was 270, 116)   # RV-1, 23 Oct 2026 - the Receipt Details bar: View receipt, Edit and Back. A new PAGE, so three controls join the census without any existing bar changing.   # (was 267)   # TD-2, 16 Oct 2026 - the two disabled twins. A twin is an .icon-action-btn in a table row, so this census counts it exactly as it counts the button it stands in for - which is the whole idea.   # (was 114)   # NV-1d, 16 Oct 2026 - the View button in the desktop strip, which is inside a table.   # (was 113)   # NV-1c, 16 Oct 2026 - the physical invoice disabled mirror, in the desktop strip, which is inside a table.   # (was 112)   # NV-1b, 16 Oct 2026 - the title deeds Actions cell drew two Bootstrap buttons, which this census cannot see. They are icon-delete and icon-upload now, so two controls join the table-row count without a control being added.   # (was 110)   # PJ-1, 15 Oct 2026 - projects_edit carried its Back control twice, behind an if on from_gantt. This census does not resolve a branch, so it counted both arms; one Back control now, and one count.   # (was 268)   # PV-1, 15 Oct 2026 - the four footer buttons of two hand-rolled invoice viewers. The shared component they moved onto was already in this census, so the count falls by exactly the four that went.   # (was 99)   # VC-1, 14 Oct 2026 - property_assets Take Photo is a <label> that had no house class until this round, so this census could not see it. 35px, in a modal, and named in STRAYS below.   # (was 98)   # DB-5, 12 Oct 2026 - the
# dashboard four joined the bar   # (was 265)   # E-10, 11 Oct 2026 - the
# seven buttons this round paired in CRS modals become visible to
'''),
    ]),
    (os.path.join('test_help_label.py'), [
        (r'''BARE = '<i class="fas fa-question-circle"></i> Help'
LABELS_TOTAL = 133   # GL-1, 28 Oct 2026 - company_details.html, the Company Details screen, an ordinary pages/templates page that joins every tree-wide count. A house Back, so one more label.   # (was 132)   # ES-7, 25 Oct 2026 - house_marks.html, the Signature and Stamp screen, an ordinary pages/templates page that joins every tree-wide count. A house Back, so one more label.   # (was 131)   # ES-6, 25 Oct 2026 - lease_signing_detail.html, the envelope page. A new PAGE with a house Back, so the tree-wide count moves by exactly one.   # (was 130)   # ES-3b, 24 Oct 2026 - the Send for Signature screen. A new PAGE with a house Back, which carries the label span base hides on a phone, so the tree-wide count moves by exactly one.   # (was 129)   # ES-3a, 23 Oct 2026 - lease_signing_list.html, the envelope register. An ordinary pages/templates page, so it joins every tree-wide count.   # (was 128)   # RV-1, 23 Oct 2026 - the Receipt Details Back. A new PAGE, and a house Back carries the label span base hides on a phone, so the tree-wide count moves by exactly one.   # (was 127)   # PP-1, 20 Oct 2026 - the printable plan's Back. It wore .action-secondary in the first draft and five suites objected; wearing the house class means carrying the house label span, which base hides on a phone so the control becomes a square icon.   # (was 126)   # RT-1, 18 Oct 2026 - three Back labels went with the four meal-plan screens MN-1 retired, and the planner brought none   # (was 129)   # PJ-1, 15 Oct 2026 - the same duplicate Back, counted by its label span. The check below it compares the backup and so falls by one with it.   # (was 130)   # DB-5, 12 Oct 2026 - the dashboard Back gains the house label   # (was 129)   # AFTER this round. 130 before - the Help one.
HELP_TOTAL = 45   # HK-4, 28 Oct 2026 - Project Details gains Help, his finding; bare text like its siblings   # (was 44)   # ES-8, 25 Oct 2026 - the Lease Signing register gains its own Help, his request; a bare-text Help secondary like its siblings.   # (was 43)   # RT-1, 18 Oct 2026 - three of MH-1 five Help buttons went with the screens they sat on. The guide is unchanged and still reached from the planner and the shopping list.   # (was 46)   # MH-1, 18 Oct 2026 - the five meal-plan screens, which had no Help control at all   # (was 41)   # DB-5, 12 Oct 2026 - and a Help secondary joins the bar   # (was 40)
# The shape 77 pages carried before D7 removed every one of them.
UNSCOPED = '.action-back-label { display: none; }'
''',
         r'''BARE = '<i class="fas fa-question-circle"></i> Help'
LABELS_TOTAL = 133   # GL-1, 28 Oct 2026 - company_details.html, the Company Details screen, an ordinary pages/templates page that joins every tree-wide count. A house Back, so one more label.   # (was 132)   # ES-7, 25 Oct 2026 - house_marks.html, the Signature and Stamp screen, an ordinary pages/templates page that joins every tree-wide count. A house Back, so one more label.   # (was 131)   # ES-6, 25 Oct 2026 - lease_signing_detail.html, the envelope page. A new PAGE with a house Back, so the tree-wide count moves by exactly one.   # (was 130)   # ES-3b, 24 Oct 2026 - the Send for Signature screen. A new PAGE with a house Back, which carries the label span base hides on a phone, so the tree-wide count moves by exactly one.   # (was 129)   # ES-3a, 23 Oct 2026 - lease_signing_list.html, the envelope register. An ordinary pages/templates page, so it joins every tree-wide count.   # (was 128)   # RV-1, 23 Oct 2026 - the Receipt Details Back. A new PAGE, and a house Back carries the label span base hides on a phone, so the tree-wide count moves by exactly one.   # (was 127)   # PP-1, 20 Oct 2026 - the printable plan's Back. It wore .action-secondary in the first draft and five suites objected; wearing the house class means carrying the house label span, which base hides on a phone so the control becomes a square icon.   # (was 126)   # RT-1, 18 Oct 2026 - three Back labels went with the four meal-plan screens MN-1 retired, and the planner brought none   # (was 129)   # PJ-1, 15 Oct 2026 - the same duplicate Back, counted by its label span. The check below it compares the backup and so falls by one with it.   # (was 130)   # DB-5, 12 Oct 2026 - the dashboard Back gains the house label   # (was 129)   # AFTER this round. 130 before - the Help one.
HELP_TOTAL = 47   # CX-1, 29 Oct 2026 - Task List and Gantt Chart gain Help, bare text like their siblings   # (was 45)   # HK-4, 28 Oct 2026 - Project Details gains Help, his finding; bare text like its siblings   # (was 44)   # ES-8, 25 Oct 2026 - the Lease Signing register gains its own Help, his request; a bare-text Help secondary like its siblings.   # (was 43)   # RT-1, 18 Oct 2026 - three of MH-1 five Help buttons went with the screens they sat on. The guide is unchanged and still reached from the planner and the shopping list.   # (was 46)   # MH-1, 18 Oct 2026 - the five meal-plan screens, which had no Help control at all   # (was 41)   # DB-5, 12 Oct 2026 - and a Help secondary joins the bar   # (was 40)
# The shape 77 pages carried before D7 removed every one of them.
UNSCOPED = '.action-back-label { display: none; }'
'''),
    ]),
    (os.path.join('test_last_menus.py'), [
        (r'''

ok(len(pages) == 32, '32 pages carry a More menu', len(pages))
off = [rel for rel, p in pages
       if not all(a in markup(today(p)) for a in ATTRS)]
''',
         r'''

# CX-1, 29 Oct 2026 - 32 -> 33: the Gantt Chart gains a More menu (Help).
ok(len(pages) == 33, '33 pages carry a More menu', len(pages))
off = [rel for rel, p in pages
       if not all(a in markup(today(p)) for a in ATTRS)]
'''),
    ]),
    (os.path.join('test_more_menu.py'), [
        (r'''# page the tree serves. Section 3 measures the round from the
# backups and nobody should read any of these as its size.
ok(len(pages) == 32, '32 pages carry the More menu in markup', len(pages))
ok(len(TOUCHED) == 27, '  27 of them are this round\'s, from its backups',
   len(TOUCHED))
''',
         r'''# page the tree serves. Section 3 measures the round from the
# backups and nobody should read any of these as its size.
# CX-1, 29 Oct 2026 - 32 -> 33: the Gantt Chart gains a More menu (Help).
ok(len(pages) == 33, '33 pages carry the More menu in markup', len(pages))
ok(len(TOUCHED) == 27, '  27 of them are this round\'s, from its backups',
   len(TOUCHED))
'''),
        (r'''ok(len(mine) == 26, '  so 26 of this round\'s pages are still in the tree',
   len(mine))
ok(LATER == ['meal_planner.html'],
   '  and 1 page was put on the binder by a LATER round - %s, MW-1, '
   '19 Oct 2026' % (LATER[0] if LATER else 'none'), LATER)
ok(len(DEFERRED) == 3, '  3 keep a hand-inlined handler, on purpose')
ok(len(ALREADY) == 2, '  2 were already on the binder before it started')
''',
         r'''ok(len(mine) == 26, '  so 26 of this round\'s pages are still in the tree',
   len(mine))
ok(LATER == ['meal_planner.html', 'projects/project_gantt.html'],
   '  and 2 pages were put on the binder by LATER rounds - the planner '
   '(MW-1, 19 Oct 2026) and the Gantt Chart (CX-1, 29 Oct 2026)', LATER)
ok(len(DEFERRED) == 3, '  3 keep a hand-inlined handler, on purpose')
ok(len(ALREADY) == 2, '  2 were already on the binder before it started')
'''),
    ]),
    (os.path.join('test_meal_week.py'), [
        (r'''wearing = [p for p in T.templates(include_base=False)
           if 'actionMoreBtn' in T.code_only(read(p))]
ok(len(wearing) == 32,
   '32 pages in both roots carry base\'s More menu', len(wearing))
ok(os.path.join('pages', 'templates', 'meal_planner.html')
   in '\n'.join(wearing), '  and the planner is one of them')
''',
         r'''wearing = [p for p in T.templates(include_base=False)
           if 'actionMoreBtn' in T.code_only(read(p))]
# CX-1, 29 Oct 2026 - 32 -> 33: the Gantt Chart gains a More menu.
ok(len(wearing) == 33,
   '33 pages in both roots carry base\'s More menu', len(wearing))
ok(os.path.join('pages', 'templates', 'meal_planner.html')
   in '\n'.join(wearing), '  and the planner is one of them')
'''),
        (r'''for suite, label in ((MM, 'test_more_menu.py'), (LM, 'test_last_menus.py')):
    body = read(suite)
    ok('== 32' in body and MARK in body,
       '%s reads 32, and says which round moved it' % label)
    ok('== 31' not in body, '  with no 31 left in it')
# AND THE REPAIR, WHICH IS THE PART THAT MATTERS. Each suite now reads
''',
         r'''for suite, label in ((MM, 'test_more_menu.py'), (LM, 'test_last_menus.py')):
    body = read(suite)
    # CX-1, 29 Oct 2026 - both now read 33 (the Gantt Chart's menu).
    ok('== 33' in body and MARK in body,
       '%s reads 33, and says which round moved it' % label)
    ok('== 31' not in body, '  with no 31 left in it')
# AND THE REPAIR, WHICH IS THE PART THAT MATTERS. Each suite now reads
'''),
        (r'''ok('mine = [(n, p) for n, p in pages if n in TOUCHED]' in mm_body,
   '  and not by subtracting two lists from today\'s census')
ok("LATER == ['meal_planner.html']" in mm_body,
   '  and NAMES the page a later round put on the binder')
ok('def today(p):' in lm_body,
   'test_last_menus reads its present-tense census in the present tense')
''',
         r'''ok('mine = [(n, p) for n, p in pages if n in TOUCHED]' in mm_body,
   '  and not by subtracting two lists from today\'s census')
# CX-1, 29 Oct 2026 - and now the Gantt Chart beside it.
ok("LATER == ['meal_planner.html', 'projects/project_gantt.html']" in mm_body,
   '  and NAMES the pages later rounds put on the binder')
ok('def today(p):' in lm_body,
   'test_last_menus reads its present-tense census in the present tense')
'''),
    ]),
    (os.path.join('test_recipe_side_b.py'), [
        (r'''# weaker, which is why this count is read and not frozen.
N_NAV_RULE_HITS, N_NAV_RULE_PRIMARY = 12, 10   # PP-1, 20 Oct 2026 - the planner leaves the set. The rule needs a bar whose only non-Back item is a link, and the planner bar now holds Print as well as Shopping List.   # (was 13, 11)   # (was 12, 10)
N_COND_LABEL, N_COND_LABEL_PRIMARY = 10, 7   # CR-2, 27 Oct 2026 - Email again / Email receipt on Receipt Details, a secondary  # (was 9, 7)

# Buttons the scan cannot see at all: no Bootstrap colour it LISTS, no
''',
         r'''# weaker, which is why this count is read and not frozen.
N_NAV_RULE_HITS, N_NAV_RULE_PRIMARY = 12, 10   # PP-1, 20 Oct 2026 - the planner leaves the set. The rule needs a bar whose only non-Back item is a link, and the planner bar now holds Print as well as Shopping List.   # (was 13, 11)   # (was 12, 10)
N_COND_LABEL, N_COND_LABEL_PRIMARY = 11, 7   # CX-1, 29 Oct 2026 - Help on the Task List, which reads Greek or English like its neighbours, a secondary   # (was 10, 7)   # CR-2, 27 Oct 2026 - Email again / Email receipt on Receipt Details, a secondary  # (was 9, 7)

# Buttons the scan cannot see at all: no Bootstrap colour it LISTS, no
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
    raise SystemExit('CX-1 REFUSED: %s' % msg)


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
    if "'test_celebration_help.py'" in read(pq):
        print('CX-1 already applied.')
        return 0

    sys.path.insert(0, root)
    import alv_tree as T

    if "'test_vendor_sort.py'" not in read(pq):
        refuse('VS-1 is not applied - this round registers after it.')
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
    q = swap(q, """    'test_vendor_sort.py'
)""", """    'test_vendor_sort.py',
    # CX-1, 29 Oct 2026 - celebrations retry; Help on Task List and Gantt.
    'test_celebration_help.py'
)""", '%s (the suites)' % PS1)
    q = swap(
        q,
        """    @{ File = 'pages/models.py'; Text = 'def _fh_unchanged(';""",
        """    @{ File = 'pages/management/commands/check_lease_renewal_and_invoices.py'; Text = 'Celebration email to %s'; What = 'CX-1: the celebrations email retries like the others - without it one mail-server hiccup loses every celebration email for the day' },
    @{ File = 'pages/models.py'; Text = 'def _fh_unchanged(';""",
        '%s (the sentinels)' % PS1)
    out[pq] = q

    ptr = os.path.join(root, TREE)
    out[ptr] = swap(out.get(ptr, read(ptr)), """    'test_vendor_sort.py',
]""", """    'test_vendor_sort.py',
    # CX-1, 29 Oct 2026 - celebrations retry; Help on Task List and Gantt.
    'test_celebration_help.py',
]""", '%s (CONVERTED)' % TREE)

    pd = os.path.join(root, ROUNDS)
    out[pd] = swap(out.get(pd, read(pd)), """    '.bak_vendorsort',
]""", """    '.bak_vendorsort',
    # CX-1, 29 Oct 2026 - celebrations retry; Help on Task List and Gantt.
    '.bak_celebhelp',
]""", '%s (ROUNDS)' % ROUNDS)

    pw = os.path.join(root, WD)
    w = out.get(pw, read(pw))
    n = re.search(r'CONVERTED_N = (\d+)', w)
    if not n:
        refuse('%s: CONVERTED_N is not there' % WD)
    out[pw] = swap(w, 'CONVERTED_N = %s' % n.group(1),
                   'CONVERTED_N = %d   # CX-1, 29 Oct 2026 - this round '
                   'own suite   # (was %s)'
                   % (int(n.group(1)) + 1, n.group(1)),
                   '%s (CONVERTED_N)' % WD)

    # ---------------------------------------------------------- THE GATES
    c = out[os.path.join(root, 'pages', 'management', 'commands',
                         'check_lease_renewal_and_invoices.py')]
    if "label='Celebration email to %s'" not in c:
        refuse('the celebrations email does not go through the retry.')

    if CHECK:
        print('CX-1 --check: %d file(s) would change, none written; %d '
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
    print('CX-1 applied - the celebrations email retries; Help on Task '
          'List and Gantt.')
    print('      No migration.')
    print('      %d file(s) written, backed up to %s' % (len(out), SUFFIX))
    print('      %d file(s) ship with it, wired in rather than written'
          % len(CREATES))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
