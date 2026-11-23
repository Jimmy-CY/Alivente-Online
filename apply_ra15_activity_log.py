# -*- coding: utf-8 -*-
"""apply_ra15_activity_log.py - round RA15, 23 Nov 2026.

RELEASE RA15 - WHO USED ALIVENTE, HOW AND WHEN.

    Demetri, 23 Nov: "I want the sign-ins information. I want the
    changes to the business records. I also want the Pages visited and
    time spent. For the personal, I want to be able to see which
    modules/areas are used the most ... I don't want access to the
    information they are saving in the Personal side." - "Keep the log
    of 12 months. Add the notice line. Email after 5 wrong passwords in
    a row. Be able to view by calendar month, or by the last 30 days, or
    for the past 12 months".

    - pages/activity.py (new) and three records (migration pages 0121):
      ActivityHit (a page opened; in Personal the module only, never the
      page), SignIn (signed in or out, wrong passwords: device, IP),
      RecordChange (a business record added, changed or deleted: by
      whom, each field old and new; account and ID numbers, signatures
      and passwords only "changed").
    - pages.activity.ActivityMiddleware, last in MIDDLEWARE; the sign-in
      signals and the watched records wired in pages/apps.py.
    - The menus' own modules: Property Operations, Financial Management,
      Administration (Functional, System), Personal (usage only,
      including CRS Reporting).
    - User Administration > Activity (superusers): Usage, Pages and time,
      Changes, Sign-ins - a calendar month, the last 30 days or the last
      12 months, by person.
    - The new page joins the tree-wide counts: test_bar_height 295,
      test_help_label 135 labels and 48 Help controls, test_house_title
      129, test_js_buttons 129/155 pages and 706/704 hits,
      test_recipe_tones and test_recipe_side_b 129 of 155,
      test_tree_roots 156, test_subtree_tones 164 and 138,
      test_pair_contrast 758 rules; test_planner 19 queries (one more on
      every page: the visit).
    - The 5th wrong password in a row: one email (key_health.recipient).
    - The watched records' receivers are named functions, never a
      functools.partial: test_project_rollup reads each receiver row and
      calls anything without a __name__ as a weak reference (it stopped
      the first RA15 push).
    - Changes and Sign-ins filter on a time range, not at__date: on MySQL
      with USE_TZ that needs the server's time-zone tables, and without
      them it matched nothing (the second RA15 push).
    - Kept 12 months, deleted once a day - by the key watcher every 15
      minutes (pages/key_health.py), never inside a page.
    - The notice under the sign-in box and in Help.
    - Migration pages 0121: run python manage.py migrate locally first.

The suite, the modules, the template and the migration ship beside this
patcher. Stands on RA14. Idempotent. Edits backed up to .bak_ra15.
"""
import os
import sys

SUFFIX = '.bak_ra15'
MARK = 'RA15, 23 Nov 2026'
CHECK = False
PS1 = 'Push-PendingChanges.ps1'
CREATES = (
    'test_ra15_activity_log.py',
    'pages/activity.py',
    'pages/views_activity.py',
    'pages/templates/user_activity.html',
    'pages/migrations/0121_activity_log.py',
)

SWAPS = [
    (os.path.join('Push-PendingChanges.ps1'), [
        (r'''    'test_ra13_trip_tabs.py',
    # RA14, 22 Nov 2026 - the phone's trip tabs open again.
    'test_ra14_trip_tabs_tap.py'
)
# NUMBER EVERY SUITE AS IT RUNS - Demetri, 1 Oct 2026: "for every check of
''',
         r'''    'test_ra13_trip_tabs.py',
    # RA14, 22 Nov 2026 - the phone's trip tabs open again.
    'test_ra14_trip_tabs_tap.py',
    # RA15, 23 Nov 2026 - the activity log.
    'test_ra15_activity_log.py'
)
# NUMBER EVERY SUITE AS IT RUNS - Demetri, 1 Oct 2026: "for every check of
'''),
    ]),
    (os.path.join('alv_rounds.py'), [
        (r'''    # RA14, 22 Nov 2026 - the phone's trip tabs open again.
    '.bak_ra14',
]

''',
         r'''    # RA14, 22 Nov 2026 - the phone's trip tabs open again.
    '.bak_ra14',
    # RA15, 23 Nov 2026 - the activity log.
    '.bak_ra15',
]

'''),
    ]),
    (os.path.join('mysite', 'settings.py'), [
        (r'''    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

''',
         r'''    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    # RA15, 23 Nov 2026 - the activity log (pages/activity.py): who is
    # asking, for the change log, and each page shown. Last, so a page
    # refused or redirected above is not counted as a visit.
    "pages.activity.ActivityMiddleware",
]

'''),
    ]),
    (os.path.join('pages', 'apps.py'), [
        (r'''        except Exception:  # never stops the app starting
            pass


''',
         r'''        except Exception:  # never stops the app starting
            pass
        # RA15, 23 Nov 2026 - the activity log (pages/activity.py): sign-ins,
        # wrong passwords and changes to business records.
        try:
            from pages import activity
            activity.connect()
        except Exception:  # never stops the app starting
            pass


'''),
    ]),
    (os.path.join('pages', 'help_content', 'administration.html'), [
        (r'''  </article>

</section>
<!-- ======= END USER ADMINISTRATION ======= -->
''',
         r'''  </article>

  <!-- RA15, 23 Nov 2026 - the activity log -->
  <article data-tab-slug="ua-activity"
           data-tab-name="Activity"
           data-tab-icon="fa-history">
    <h5 style="color:#0e7c8b; font-weight:700;"><i class="fas fa-history"></i> Activity &mdash; who used Alivente, how and when</h5>
    <p><strong>Activity</strong> (the button at the top of User Administration) is for superusers only. Pick <strong>a calendar month</strong>, <strong>the last 30 days</strong> or <strong>the last 12 months</strong>, and a person.</p>
    <ul>
      <li><strong>Usage</strong> &mdash; how much each module is used, by each person: visits, with the time spent underneath, grouped as the menus are (Property Operations, Financial Management, Administration, Personal). Darker is more; a dash is not used at all. Click an area to fold it.</li>
      <li><strong>Pages and time</strong> &mdash; each sitting: when, how long and which modules; for Property Operations, Financial Management and Administration the pages themselves too. A visit lasts until the next page, at most 30 minutes; the last page of a sitting counts a minute.</li>
      <li><strong>Changes</strong> &mdash; every business record added, changed or deleted (properties, tenants, suppliers, issues, projects, invoices, receipts, expenses, petty cash, financials, leases, signing, company details, workspaces, users): by whom, and each field&rsquo;s old and new value. Account and ID numbers, signatures and passwords show only that they changed.</li>
      <li><strong>Sign-ins</strong> &mdash; signed in, signed out and wrong passwords, with the device and IP address. <strong>Five wrong passwords in a row</strong> for one sign-in send you an email.</li>
    </ul>
    <div class="alert alert-info" style="border-left:4px solid #0e7c8b;">
      <i class="fas fa-user-shield"></i> <strong>Personal stays private.</strong> For Passports / Documents, Travel, Recipes, Celebrations, Wellness, Household Members and CRS Reporting only the module and the time are kept &mdash; never the pages or anything saved. Everyone is told on the sign-in page: <em>Sign-ins, use of each area and changes to business records are logged. What you save in Personal is never recorded.</em> Everything is deleted after 12 months.
    </div>
  </article>

</section>
<!-- ======= END USER ADMINISTRATION ======= -->
'''),
    ]),
    (os.path.join('pages', 'models.py'), [
        (r'''    def __str__(self):
        return '%s: %s' % (self.service, 'ok' if self.ok else self.problem)
''',
         r'''    def __str__(self):
        return '%s: %s' % (self.service, 'ok' if self.ok else self.problem)


# RA15, 23 Nov 2026 - who used Alivente, how and when (pages/activity.py).
# Demetri: "I want the sign-ins information. I want the changes to the
# business records. I also want the Pages visited and time spent. For the
# personal, I want to be able to see which modules/areas are used the most
# ... I don't want access to the information they are saving in the
# Personal side." Superusers only; kept 12 months.
class ActivityHit(models.Model):
    """A page opened. path is blank in Personal: the module only."""
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE,
                             related_name='+')
    at = models.DateTimeField()
    day = models.DateField(db_index=True)
    module = models.CharField(max_length=20, blank=True)
    path = models.CharField(max_length=200, blank=True)

    class Meta:
        db_table = 'activity_hit'
        indexes = [models.Index(fields=['user', 'at'])]

    def __str__(self):
        return '%s %s' % (self.at, self.module)


class SignIn(models.Model):
    KINDS = [('in', 'Signed in'), ('out', 'Signed out'),
             ('failed', 'Wrong password')]
    at = models.DateTimeField(db_index=True)
    user = models.ForeignKey('auth.User', on_delete=models.SET_NULL,
                             null=True, blank=True, related_name='+')
    username = models.CharField(max_length=150, blank=True)
    kind = models.CharField(max_length=8, choices=KINDS)
    ip = models.CharField(max_length=45, blank=True)
    device = models.CharField(max_length=60, blank=True)

    class Meta:
        db_table = 'activity_sign_in'
        ordering = ['-at']

    def __str__(self):
        return '%s %s %s' % (self.at, self.username, self.kind)


class RecordChange(models.Model):
    """A business record added, changed or deleted. changes: [[field,
    old, new], ...] - blank old and new for a secret field."""
    ACTIONS = [('added', 'Added'), ('changed', 'Changed'),
               ('deleted', 'Deleted')]
    at = models.DateTimeField(db_index=True)
    user = models.ForeignKey('auth.User', on_delete=models.SET_NULL,
                             null=True, blank=True, related_name='+')
    module = models.CharField(max_length=20, blank=True)
    what = models.CharField(max_length=40, blank=True)
    object_id = models.CharField(max_length=40, blank=True)
    name = models.CharField(max_length=200, blank=True)
    action = models.CharField(max_length=8, choices=ACTIONS)
    changes = models.JSONField(default=list, blank=True)

    class Meta:
        db_table = 'activity_change'
        ordering = ['-at']

    def __str__(self):
        return '%s %s %s' % (self.at, self.action, self.name)
'''),
    ]),
    (os.path.join('pages', 'templates', 'login.html'), [
        (r'''        <span class="login-help-note">New account and never set one? Same link.</span>
    </p>
</form>
</div>
''',
         r'''        <span class="login-help-note">New account and never set one? Same link.</span>
    </p>
    {# RA15, 23 Nov 2026 - the activity log, said to everyone who signs in (Demetri: "Add the notice line"). #}
    <p class="login-help-note" data-activity-notice>Sign-ins, use of each area and changes to business records are logged. What you save in Personal is never recorded.</p>
</form>
</div>
'''),
    ]),
    (os.path.join('pages', 'templates', 'user_administration.html'), [
        (r'''            <i class="fas fa-layer-group"></i> Workspaces
        </a>
        <button type="button" class="btn action-secondary" data-toggle="modal" data-target="#user_administrationHelpModal">
            <i class="fas fa-question-circle"></i> Help
''',
         r'''            <i class="fas fa-layer-group"></i> Workspaces
        </a>
        {% if request.user.is_superuser %}{# RA15, 23 Nov 2026 - who used Alivente, how and when. #}<a href="{% url 'user_activity' %}" class="btn action-secondary" data-activity-link>
            <i class="fas fa-history"></i> Activity
        </a>{% endif %}
        <button type="button" class="btn action-secondary" data-toggle="modal" data-target="#user_administrationHelpModal">
            <i class="fas fa-question-circle"></i> Help
'''),
        (r'''                    <i class="fas fa-layer-group"></i> Workspaces
                </a>
                <button type="button" class="action-more-item" role="menuitem"
                        data-toggle="modal" data-target="#user_administrationHelpModal">
''',
         r'''                    <i class="fas fa-layer-group"></i> Workspaces
                </a>
                {% if request.user.is_superuser %}<a href="{% url 'user_activity' %}" class="action-more-item" role="menuitem">
                    <i class="fas fa-history"></i> Activity
                </a>{% endif %}
                <button type="button" class="action-more-item" role="menuitem"
                        data-toggle="modal" data-target="#user_administrationHelpModal">
'''),
    ]),
    (os.path.join('pages', 'urls.py'), [
        (r'''from django.urls import path
from . import views
from . import css_files
from .views_setup import setup_permissions
''',
         r'''from django.urls import path
from . import views
from . import views_activity  # RA15, 23 Nov 2026 - the activity log
from . import css_files
from .views_setup import setup_permissions
'''),
        (r'''    path('user-administration/', views.user_administration, name='user_administration'),
    path('user-administration/add/', views.user_add, name='user_add'),
    path('user-administration/<int:user_id>/edit/', views.user_edit, name='user_edit'),
    path('user-administration/<int:user_id>/permissions/', views.user_permissions, name='user_permissions'),
''',
         r'''    path('user-administration/', views.user_administration, name='user_administration'),
    path('user-administration/add/', views.user_add, name='user_add'),
    # RA15, 23 Nov 2026 - who used Alivente, how and when (superusers).
    path('user-administration/activity/', views_activity.user_activity,
         name='user_activity'),
    path('user-administration/<int:user_id>/edit/', views.user_edit, name='user_edit'),
    path('user-administration/<int:user_id>/permissions/', views.user_permissions, name='user_permissions'),
'''),
    ]),
    (os.path.join('test_bar_height.py'), [
        (r'''
BAR, ROW, MODAL = 35, 34, 38
N_BAR, N_ROW, N_MODAL = 292, 122, 103   # CX-1, 29 Oct 2026 - Help joins the Task List and Gantt Chart bars.   # (N_BAR was 290)   # GL-3, 29 Oct 2026 - the Greek Details pop-up, Cancel and Done, on Tenant Edit and Tenant Add.   # (N_MODAL was 99)   # GE-1, 28 Oct 2026 - Generate gains Send for e-signing beside Download Word, and the envelope page a Word version button.   # (N_BAR was 288)   # GL-1, 28 Oct 2026 - the Company Details screen's bar, Save and Back.   # (N_BAR was 286)   # HK-4, 28 Oct 2026 - Help on the Project Details bar, his finding   # (N_BAR was 285)   # CR-2, 27 Oct 2026 - emailing a receipt: Email receipt in the Receipt Details bar (both arms of its if), the paper-plane in the Receipts row (live and greyed), and Cancel and Send in the pop-up on both pages.   # (was 283, 120, 95)   # ES-9, 26 Oct 2026 - the envelope page draws a greyed Approve and attach when no tenancy is free to receive the lease; both arms of the if count.   # (was 282, 120)   # HK-1, 26 Oct 2026 - the paper-plane left Manage Lease Agreements, his decision; both arms of its superuser check counted, so the row figure falls by two.   # (was 282, 122)   # ES-8, 25 Oct 2026 - the Lease Signing register gains a Help secondary in its bar, and a View-signed-lease icon in its row actions.   # (was 281, 121)   # ES-7, 25 Oct 2026 - the Signature and Stamp screen's bar, Back alone.   # (was 280)   # ES-6, 25 Oct 2026 - the envelope page's bar (Approve and attach, Decline, View signed lease, Back). This census does not resolve a branch, so Approve and Decline count even though they only show while an envelope is awaiting approval.   # (was 276)   # ES-3b, 24 Oct 2026 - the Send for Signature screen (Create and sign, Back) and the Send row action on Manage Lease Agreements. This census does not resolve a branch, so both arms of the perms check count - which is why the row figure moved by two and not by one.   # (was 274, 119)   # ES-3a, 23 Oct 2026 - lease_signing_list.html, the envelope register. An ordinary pages/templates page, so it joins every tree-wide count.   # (was 270, 116)   # RV-1, 23 Oct 2026 - the Receipt Details bar: View receipt, Edit and Back. A new PAGE, so three controls join the census without any existing bar changing.   # (was 267)   # TD-2, 16 Oct 2026 - the two disabled twins. A twin is an .icon-action-btn in a table row, so this census counts it exactly as it counts the button it stands in for - which is the whole idea.   # (was 114)   # NV-1d, 16 Oct 2026 - the View button in the desktop strip, which is inside a table.   # (was 113)   # NV-1c, 16 Oct 2026 - the physical invoice disabled mirror, in the desktop strip, which is inside a table.   # (was 112)   # NV-1b, 16 Oct 2026 - the title deeds Actions cell drew two Bootstrap buttons, which this census cannot see. They are icon-delete and icon-upload now, so two controls join the table-row count without a control being added.   # (was 110)   # PJ-1, 15 Oct 2026 - projects_edit carried its Back control twice, behind an if on from_gantt. This census does not resolve a branch, so it counted both arms; one Back control now, and one count.   # (was 268)   # PV-1, 15 Oct 2026 - the four footer buttons of two hand-rolled invoice viewers. The shared component they moved onto was already in this census, so the count falls by exactly the four that went.   # (was 99)   # VC-1, 14 Oct 2026 - property_assets Take Photo is a <label> that had no house class until this round, so this census could not see it. 35px, in a modal, and named in STRAYS below.   # (was 98)   # DB-5, 12 Oct 2026 - the
# dashboard four joined the bar   # (was 265)   # E-10, 11 Oct 2026 - the
# seven buttons this round paired in CRS modals become visible to
''',
         r'''
BAR, ROW, MODAL = 35, 34, 38
N_BAR, N_ROW, N_MODAL = 295, 122, 103   # RA15, 23 Nov 2026 - Activity joins the User Administration bar, and the new Activity page's bar has Help and Back.   # (N_BAR was 292)   # CX-1, 29 Oct 2026 - Help joins the Task List and Gantt Chart bars.   # (N_BAR was 290)   # GL-3, 29 Oct 2026 - the Greek Details pop-up, Cancel and Done, on Tenant Edit and Tenant Add.   # (N_MODAL was 99)   # GE-1, 28 Oct 2026 - Generate gains Send for e-signing beside Download Word, and the envelope page a Word version button.   # (N_BAR was 288)   # GL-1, 28 Oct 2026 - the Company Details screen's bar, Save and Back.   # (N_BAR was 286)   # HK-4, 28 Oct 2026 - Help on the Project Details bar, his finding   # (N_BAR was 285)   # CR-2, 27 Oct 2026 - emailing a receipt: Email receipt in the Receipt Details bar (both arms of its if), the paper-plane in the Receipts row (live and greyed), and Cancel and Send in the pop-up on both pages.   # (was 283, 120, 95)   # ES-9, 26 Oct 2026 - the envelope page draws a greyed Approve and attach when no tenancy is free to receive the lease; both arms of the if count.   # (was 282, 120)   # HK-1, 26 Oct 2026 - the paper-plane left Manage Lease Agreements, his decision; both arms of its superuser check counted, so the row figure falls by two.   # (was 282, 122)   # ES-8, 25 Oct 2026 - the Lease Signing register gains a Help secondary in its bar, and a View-signed-lease icon in its row actions.   # (was 281, 121)   # ES-7, 25 Oct 2026 - the Signature and Stamp screen's bar, Back alone.   # (was 280)   # ES-6, 25 Oct 2026 - the envelope page's bar (Approve and attach, Decline, View signed lease, Back). This census does not resolve a branch, so Approve and Decline count even though they only show while an envelope is awaiting approval.   # (was 276)   # ES-3b, 24 Oct 2026 - the Send for Signature screen (Create and sign, Back) and the Send row action on Manage Lease Agreements. This census does not resolve a branch, so both arms of the perms check count - which is why the row figure moved by two and not by one.   # (was 274, 119)   # ES-3a, 23 Oct 2026 - lease_signing_list.html, the envelope register. An ordinary pages/templates page, so it joins every tree-wide count.   # (was 270, 116)   # RV-1, 23 Oct 2026 - the Receipt Details bar: View receipt, Edit and Back. A new PAGE, so three controls join the census without any existing bar changing.   # (was 267)   # TD-2, 16 Oct 2026 - the two disabled twins. A twin is an .icon-action-btn in a table row, so this census counts it exactly as it counts the button it stands in for - which is the whole idea.   # (was 114)   # NV-1d, 16 Oct 2026 - the View button in the desktop strip, which is inside a table.   # (was 113)   # NV-1c, 16 Oct 2026 - the physical invoice disabled mirror, in the desktop strip, which is inside a table.   # (was 112)   # NV-1b, 16 Oct 2026 - the title deeds Actions cell drew two Bootstrap buttons, which this census cannot see. They are icon-delete and icon-upload now, so two controls join the table-row count without a control being added.   # (was 110)   # PJ-1, 15 Oct 2026 - projects_edit carried its Back control twice, behind an if on from_gantt. This census does not resolve a branch, so it counted both arms; one Back control now, and one count.   # (was 268)   # PV-1, 15 Oct 2026 - the four footer buttons of two hand-rolled invoice viewers. The shared component they moved onto was already in this census, so the count falls by exactly the four that went.   # (was 99)   # VC-1, 14 Oct 2026 - property_assets Take Photo is a <label> that had no house class until this round, so this census could not see it. 35px, in a modal, and named in STRAYS below.   # (was 98)   # DB-5, 12 Oct 2026 - the
# dashboard four joined the bar   # (was 265)   # E-10, 11 Oct 2026 - the
# seven buttons this round paired in CRS modals become visible to
'''),
    ]),
    (os.path.join('test_help_label.py'), [
        (r'''        '<span class="action-back-label"> Help</span>')
BARE = '<i class="fas fa-question-circle"></i> Help'
LABELS_TOTAL = 134   # CG-1, 13 Nov 2026 - celebration_gifts.html, the My gifts page, an ordinary pages/templates page with a Back.   # (was 133)   # GL-1, 28 Oct 2026 - company_details.html, the Company Details screen, an ordinary pages/templates page that joins every tree-wide count. A house Back, so one more label.   # (was 132)   # ES-7, 25 Oct 2026 - house_marks.html, the Signature and Stamp screen, an ordinary pages/templates page that joins every tree-wide count. A house Back, so one more label.   # (was 131)   # ES-6, 25 Oct 2026 - lease_signing_detail.html, the envelope page. A new PAGE with a house Back, so the tree-wide count moves by exactly one.   # (was 130)   # ES-3b, 24 Oct 2026 - the Send for Signature screen. A new PAGE with a house Back, which carries the label span base hides on a phone, so the tree-wide count moves by exactly one.   # (was 129)   # ES-3a, 23 Oct 2026 - lease_signing_list.html, the envelope register. An ordinary pages/templates page, so it joins every tree-wide count.   # (was 128)   # RV-1, 23 Oct 2026 - the Receipt Details Back. A new PAGE, and a house Back carries the label span base hides on a phone, so the tree-wide count moves by exactly one.   # (was 127)   # PP-1, 20 Oct 2026 - the printable plan's Back. It wore .action-secondary in the first draft and five suites objected; wearing the house class means carrying the house label span, which base hides on a phone so the control becomes a square icon.   # (was 126)   # RT-1, 18 Oct 2026 - three Back labels went with the four meal-plan screens MN-1 retired, and the planner brought none   # (was 129)   # PJ-1, 15 Oct 2026 - the same duplicate Back, counted by its label span. The check below it compares the backup and so falls by one with it.   # (was 130)   # DB-5, 12 Oct 2026 - the dashboard Back gains the house label   # (was 129)   # AFTER this round. 130 before - the Help one.
HELP_TOTAL = 47   # CX-1, 29 Oct 2026 - Task List and Gantt Chart gain Help, bare text like their siblings   # (was 45)   # HK-4, 28 Oct 2026 - Project Details gains Help, his finding; bare text like its siblings   # (was 44)   # ES-8, 25 Oct 2026 - the Lease Signing register gains its own Help, his request; a bare-text Help secondary like its siblings.   # (was 43)   # RT-1, 18 Oct 2026 - three of MH-1 five Help buttons went with the screens they sat on. The guide is unchanged and still reached from the planner and the shopping list.   # (was 46)   # MH-1, 18 Oct 2026 - the five meal-plan screens, which had no Help control at all   # (was 41)   # DB-5, 12 Oct 2026 - and a Help secondary joins the bar   # (was 40)
# The shape 77 pages carried before D7 removed every one of them.
UNSCOPED = '.action-back-label { display: none; }'
''',
         r'''        '<span class="action-back-label"> Help</span>')
BARE = '<i class="fas fa-question-circle"></i> Help'
LABELS_TOTAL = 135   # RA15, 23 Nov 2026 - user_activity.html, the Activity page, an ordinary pages/templates page that joins every tree-wide count: a Back.   # (was 134)   # CG-1, 13 Nov 2026 - celebration_gifts.html, the My gifts page, an ordinary pages/templates page with a Back.   # (was 133)   # GL-1, 28 Oct 2026 - company_details.html, the Company Details screen, an ordinary pages/templates page that joins every tree-wide count. A house Back, so one more label.   # (was 132)   # ES-7, 25 Oct 2026 - house_marks.html, the Signature and Stamp screen, an ordinary pages/templates page that joins every tree-wide count. A house Back, so one more label.   # (was 131)   # ES-6, 25 Oct 2026 - lease_signing_detail.html, the envelope page. A new PAGE with a house Back, so the tree-wide count moves by exactly one.   # (was 130)   # ES-3b, 24 Oct 2026 - the Send for Signature screen. A new PAGE with a house Back, which carries the label span base hides on a phone, so the tree-wide count moves by exactly one.   # (was 129)   # ES-3a, 23 Oct 2026 - lease_signing_list.html, the envelope register. An ordinary pages/templates page, so it joins every tree-wide count.   # (was 128)   # RV-1, 23 Oct 2026 - the Receipt Details Back. A new PAGE, and a house Back carries the label span base hides on a phone, so the tree-wide count moves by exactly one.   # (was 127)   # PP-1, 20 Oct 2026 - the printable plan's Back. It wore .action-secondary in the first draft and five suites objected; wearing the house class means carrying the house label span, which base hides on a phone so the control becomes a square icon.   # (was 126)   # RT-1, 18 Oct 2026 - three Back labels went with the four meal-plan screens MN-1 retired, and the planner brought none   # (was 129)   # PJ-1, 15 Oct 2026 - the same duplicate Back, counted by its label span. The check below it compares the backup and so falls by one with it.   # (was 130)   # DB-5, 12 Oct 2026 - the dashboard Back gains the house label   # (was 129)   # AFTER this round. 130 before - the Help one.
HELP_TOTAL = 48   # RA15, 23 Nov 2026 - user_activity.html, the Activity page, an ordinary pages/templates page that joins every tree-wide count: Help, bare text like its siblings.   # (was 47)   # CX-1, 29 Oct 2026 - Task List and Gantt Chart gain Help, bare text like their siblings   # (was 45)   # HK-4, 28 Oct 2026 - Project Details gains Help, his finding; bare text like its siblings   # (was 44)   # ES-8, 25 Oct 2026 - the Lease Signing register gains its own Help, his request; a bare-text Help secondary like its siblings.   # (was 43)   # RT-1, 18 Oct 2026 - three of MH-1 five Help buttons went with the screens they sat on. The guide is unchanged and still reached from the planner and the shopping list.   # (was 46)   # MH-1, 18 Oct 2026 - the five meal-plan screens, which had no Help control at all   # (was 41)   # DB-5, 12 Oct 2026 - and a Help secondary joins the bar   # (was 40)
# The shape 77 pages carried before D7 removed every one of them.
UNSCOPED = '.action-back-label { display: none; }'
'''),
    ]),
    (os.path.join('test_house_title.py'), [
        (r'''# keeping the two honest" had been disagreeing for three days. Both
# say 122 now.
ok(len(wearers) == 128,   # CG-1, 13 Nov 2026 - celebration_gifts.html, the My gifts page with the Christmas list, an ordinary pages/templates page that joins every tree-wide count. Wears the house title pair.   # (was 127)   # GL-1, 28 Oct 2026 - company_details.html, the Company Details screen, an ordinary pages/templates page that joins every tree-wide count. Wears the house title pair.   # (was 126)   # ES-7, 25 Oct 2026 - house_marks.html, the Signature and Stamp screen, an ordinary pages/templates page that joins every tree-wide count. Wears the house title pair.   # (was 125)   # ES-6, 25 Oct 2026 - lease_signing_detail.html, the envelope page, an ordinary pages/templates page that joins every tree-wide count. Wears the house title pair.   # (was 124)   # ES-3b, 24 Oct 2026 - lease_signing_create.html, the Send for Signature screen, wears the house title pair.   # (was 123)   # ES-3a, 23 Oct 2026 - lease_signing_list.html wears the house title pair.   # (was 122)
   '122 templates now wear the class, which is the number base\'s note '
   'states', len(wearers))
''',
         r'''# keeping the two honest" had been disagreeing for three days. Both
# say 122 now.
ok(len(wearers) == 129,   # RA15, 23 Nov 2026 - user_activity.html, the Activity page, an ordinary pages/templates page that joins every tree-wide count. Wears the house title pair.   # (was 128)   # CG-1, 13 Nov 2026 - celebration_gifts.html, the My gifts page with the Christmas list, an ordinary pages/templates page that joins every tree-wide count. Wears the house title pair.   # (was 127)   # GL-1, 28 Oct 2026 - company_details.html, the Company Details screen, an ordinary pages/templates page that joins every tree-wide count. Wears the house title pair.   # (was 126)   # ES-7, 25 Oct 2026 - house_marks.html, the Signature and Stamp screen, an ordinary pages/templates page that joins every tree-wide count. Wears the house title pair.   # (was 125)   # ES-6, 25 Oct 2026 - lease_signing_detail.html, the envelope page, an ordinary pages/templates page that joins every tree-wide count. Wears the house title pair.   # (was 124)   # ES-3b, 24 Oct 2026 - lease_signing_create.html, the Send for Signature screen, wears the house title pair.   # (was 123)   # ES-3a, 23 Oct 2026 - lease_signing_list.html wears the house title pair.   # (was 122)
   '122 templates now wear the class, which is the number base\'s note '
   'states', len(wearers))
'''),
    ]),
    (os.path.join('test_js_buttons.py'), [
        (r'''# SCOPE does not move - 117 was and is the narrow half, and the pages
# the flag hides are still the recipe and meal-plan side.
CENSUS_NARROW, CENSUS_WIDE = 128, 154   # CG-1, 13 Nov 2026 - celebration_gifts.html, the My gifts page. It joins the application count only, measured: the narrow sweep scope stays 128.   # (was 128, 153)   # GL-1, 28 Oct 2026 - company_details.html, the Company Details screen, an ordinary pages/templates page that joins every tree-wide count.   # (was 127, 152)   # LS-1, 27 Oct 2026 - tenant_lease_signing_status.html, the Lease Signing Status report, an ordinary pages/templates page that joins every tree-wide count.   # (was 126, 151)   # ES-7, 25 Oct 2026 - house_marks.html, the Signature and Stamp screen, an ordinary pages/templates page that joins every tree-wide count.   # (was 125, 150)   # ES-6, 25 Oct 2026 - lease_signing_detail.html, the envelope page, an ordinary pages/templates page that joins every tree-wide count.   # (was 124, 149)   # ES-3b, 24 Oct 2026 - the Send for Signature screen, an ordinary page that joins both halves.   # (was 123, 148)   # ES-4, 24 Oct 2026 - the four public signing templates. They are ordinary pages/templates files, so they join both halves - but they contribute ZERO scanner hits, measured: their controls wear .ls-btn, a class of their own, because the pages cannot extend base and so cannot use the house one.   # (was 119, 144)   # ES-3a, 23 Oct 2026 - lease_signing_list.html, the envelope register. An ordinary pages/templates page, so it joins every tree-wide count.   # (was 118, 143)   # RV-1, 23 Oct 2026 - cash_receipt_detail.html. BOTH halves move: unlike meal_plan_print this is an ordinary pages/templates page, so it joins the sweep scope as well as the application count.   # (was 117, 142)   # PP-1, 20 Oct 2026 - meal_plan_print.html. The narrow half does not move: the sweep scope is the 117 pages it has always been.   # (WIDE was 141)   # RD-1, 19 Oct 2026 - the
# quick-look pair. (wide was 139, and 142 before MN-1 retired four
# meal-plan screens.)
HITS_LOOSE, HITS_TIGHT = 704, 702   # CG-1, 13 Nov 2026 - the My gifts page: Shopping list to me, Back, and a Remove and a Save on each Christmas row, measured by this census; both matchers rise by the same five.   # (was 699, 697)   # GL-1, 28 Oct 2026 - Save and Back on the Company Details screen; both matchers rise by the same two.   # (was 697, 695)   # LS-1, 27 Oct 2026 - Include finished / Open only and Back on the Lease Signing Status report, measured by this census; both matchers rise by the same three.   # (was 694, 692)   # ES-7, 25 Oct 2026 - three more house .btn controls on the Signature and Stamp screen, measured by this census. Both matchers rise by the same three.   # (was 691, 689)   # ES-6, 25 Oct 2026 - the envelope page's bar: Approve and attach, Decline, View signed lease and Back. Both matchers rise by the same four.   # (was 687, 685)   # ES-3b, 24 Oct 2026 - Create and sign, Back, and Choose a different tenant. Both matchers rise by the same three. MEASURED PER ROUND rather than split by eye: ES-4 ships four templates in the same bundle and its share is zero, because its buttons are not house .btn ones.   # (was 684, 682)   # ES-3a, 23 Oct 2026 - lease_signing_list.html, the envelope register. An ordinary pages/templates page, so it joins every tree-wide count.   # (was 680, 678)   # RV-1, 23 Oct 2026 - the Receipt Details bar: View receipt, Edit and Back. Both matchers rise by the same three.   # (was 677, 675)   # PP-1, 20 Oct 2026 - the printable plan's two bar controls, Print and Back. Both matchers rise by the same two.   # (was 675, 673)   # RD-1, 19 Oct 2026 - one scanner
# hit per new template, and BOTH matchers rise by the same two.
# (was 673, 671)   # RT-1, 18 Oct 2026 - thirty-three scanner hits went with the four retired screens, and both matchers fall by the same thirty-three.   # (was 706, 704)
''',
         r'''# SCOPE does not move - 117 was and is the narrow half, and the pages
# the flag hides are still the recipe and meal-plan side.
CENSUS_NARROW, CENSUS_WIDE = 129, 155   # RA15, 23 Nov 2026 - user_activity.html, the Activity page, an ordinary pages/templates page that joins every tree-wide count; both halves move.   # (was 128, 154)   # CG-1, 13 Nov 2026 - celebration_gifts.html, the My gifts page. It joins the application count only, measured: the narrow sweep scope stays 128.   # (was 128, 153)   # GL-1, 28 Oct 2026 - company_details.html, the Company Details screen, an ordinary pages/templates page that joins every tree-wide count.   # (was 127, 152)   # LS-1, 27 Oct 2026 - tenant_lease_signing_status.html, the Lease Signing Status report, an ordinary pages/templates page that joins every tree-wide count.   # (was 126, 151)   # ES-7, 25 Oct 2026 - house_marks.html, the Signature and Stamp screen, an ordinary pages/templates page that joins every tree-wide count.   # (was 125, 150)   # ES-6, 25 Oct 2026 - lease_signing_detail.html, the envelope page, an ordinary pages/templates page that joins every tree-wide count.   # (was 124, 149)   # ES-3b, 24 Oct 2026 - the Send for Signature screen, an ordinary page that joins both halves.   # (was 123, 148)   # ES-4, 24 Oct 2026 - the four public signing templates. They are ordinary pages/templates files, so they join both halves - but they contribute ZERO scanner hits, measured: their controls wear .ls-btn, a class of their own, because the pages cannot extend base and so cannot use the house one.   # (was 119, 144)   # ES-3a, 23 Oct 2026 - lease_signing_list.html, the envelope register. An ordinary pages/templates page, so it joins every tree-wide count.   # (was 118, 143)   # RV-1, 23 Oct 2026 - cash_receipt_detail.html. BOTH halves move: unlike meal_plan_print this is an ordinary pages/templates page, so it joins the sweep scope as well as the application count.   # (was 117, 142)   # PP-1, 20 Oct 2026 - meal_plan_print.html. The narrow half does not move: the sweep scope is the 117 pages it has always been.   # (WIDE was 141)   # RD-1, 19 Oct 2026 - the
# quick-look pair. (wide was 139, and 142 before MN-1 retired four
# meal-plan screens.)
HITS_LOOSE, HITS_TIGHT = 706, 704   # RA15, 23 Nov 2026 - the Activity page's bar, Help and Back, measured by this census; both matchers rise by the same two.   # (was 704, 702)   # CG-1, 13 Nov 2026 - the My gifts page: Shopping list to me, Back, and a Remove and a Save on each Christmas row, measured by this census; both matchers rise by the same five.   # (was 699, 697)   # GL-1, 28 Oct 2026 - Save and Back on the Company Details screen; both matchers rise by the same two.   # (was 697, 695)   # LS-1, 27 Oct 2026 - Include finished / Open only and Back on the Lease Signing Status report, measured by this census; both matchers rise by the same three.   # (was 694, 692)   # ES-7, 25 Oct 2026 - three more house .btn controls on the Signature and Stamp screen, measured by this census. Both matchers rise by the same three.   # (was 691, 689)   # ES-6, 25 Oct 2026 - the envelope page's bar: Approve and attach, Decline, View signed lease and Back. Both matchers rise by the same four.   # (was 687, 685)   # ES-3b, 24 Oct 2026 - Create and sign, Back, and Choose a different tenant. Both matchers rise by the same three. MEASURED PER ROUND rather than split by eye: ES-4 ships four templates in the same bundle and its share is zero, because its buttons are not house .btn ones.   # (was 684, 682)   # ES-3a, 23 Oct 2026 - lease_signing_list.html, the envelope register. An ordinary pages/templates page, so it joins every tree-wide count.   # (was 680, 678)   # RV-1, 23 Oct 2026 - the Receipt Details bar: View receipt, Edit and Back. Both matchers rise by the same three.   # (was 677, 675)   # PP-1, 20 Oct 2026 - the printable plan's two bar controls, Print and Back. Both matchers rise by the same two.   # (was 675, 673)   # RD-1, 19 Oct 2026 - one scanner
# hit per new template, and BOTH matchers rise by the same two.
# (was 673, 671)   # RT-1, 18 Oct 2026 - thirty-three scanner hits went with the four retired screens, and both matchers fall by the same thirty-three.   # (was 706, 704)
'''),
    ]),
    (os.path.join('test_recipe_tones.py'), [
        (r'''# GL-1, 28 Oct 2026 - 128 of 153: company_details.html joins both halves.
# CG-1, 13 Nov 2026 - celebration_gifts.html, the My gifts page with the Christmas list, it joins the page count only, measured - the narrow half stays 128. (was 128 of 153)
ok(len(sb.templates(False)) == 128 and len(sb.templates(True)) == 154,
   '  which is %d of %d' % (128, 154),
   '%d of %d' % (len(sb.templates(False)), len(sb.templates(True))))

''',
         r'''# GL-1, 28 Oct 2026 - 128 of 153: company_details.html joins both halves.
# CG-1, 13 Nov 2026 - celebration_gifts.html, the My gifts page with the Christmas list, it joins the page count only, measured - the narrow half stays 128. (was 128 of 153)
# RA15, 23 Nov 2026 - user_activity.html, the Activity page, joins both
# counts (was 128 of 154).
ok(len(sb.templates(False)) == 129 and len(sb.templates(True)) == 155,
   '  which is %d of %d' % (129, 155),
   '%d of %d' % (len(sb.templates(False)), len(sb.templates(True))))

'''),
    ]),
    (os.path.join('test_recipe_side_b.py'), [
        (r'''N_EDITS, N_PAGES = 31, 13
N_DRIFT, N_DECIDED = 18, 13
GATE_WAS, GATE_NOW = 128, 154   # CG-1, 13 Nov 2026 - celebration_gifts.html, the My gifts page. It joins the application count only, measured: the narrow sweep scope stays 128.   # (was 128, 153)   # GL-1, 28 Oct 2026 - company_details.html, the Company Details screen, an ordinary pages/templates page that joins every tree-wide count.   # (was 127, 152)   # LS-1, 27 Oct 2026 - tenant_lease_signing_status.html, the Lease Signing Status report, an ordinary pages/templates page that joins every tree-wide count.   # (was 126, 151)   # ES-7, 25 Oct 2026 - house_marks.html, the Signature and Stamp screen, an ordinary pages/templates page that joins every tree-wide count.   # (was 125, 150)   # ES-6, 25 Oct 2026 - lease_signing_detail.html, the envelope page, an ordinary page that joins every tree-wide count.   # (was 124, 149)   # ES-3b, 24 Oct 2026 - the Send for Signature screen, an ordinary page that joins every tree-wide count.   # (was 123, 148)   # ES-4, 24 Oct 2026 - the four public signing templates. They are ordinary pages/templates files, so they join every tree-wide count; they cannot extend base, which is why they are standalone.   # (was 119, 144)   # ES-3a, 23 Oct 2026 - lease_signing_list.html, the envelope register. An ordinary pages/templates page, so it joins every tree-wide count.   # (was 118, 143)   # RV-1, 23 Oct 2026 - cash_receipt_detail.html. The same pair as test_js_buttons and test_recipe_tones: an ordinary pages/templates page joins the sweep scope and the page count alike.   # (was 117, 142)   # PP-1, 20 Oct 2026 - meal_plan_print.html. (GATE_NOW was 141)   # RD-1, 19 Oct 2026 - the quick-look
# pair. (GATE_NOW was 139)   # RT-1, 18 Oct 2026 - the wide census is four meal-plan screens smaller and one planner larger. The narrow half does not move.   # (GATE_NOW was 142)

''',
         r'''N_EDITS, N_PAGES = 31, 13
N_DRIFT, N_DECIDED = 18, 13
GATE_WAS, GATE_NOW = 129, 155   # RA15, 23 Nov 2026 - user_activity.html, the Activity page, an ordinary pages/templates page: both halves move.   # (was 128, 154)   # CG-1, 13 Nov 2026 - celebration_gifts.html, the My gifts page. It joins the application count only, measured: the narrow sweep scope stays 128.   # (was 128, 153)   # GL-1, 28 Oct 2026 - company_details.html, the Company Details screen, an ordinary pages/templates page that joins every tree-wide count.   # (was 127, 152)   # LS-1, 27 Oct 2026 - tenant_lease_signing_status.html, the Lease Signing Status report, an ordinary pages/templates page that joins every tree-wide count.   # (was 126, 151)   # ES-7, 25 Oct 2026 - house_marks.html, the Signature and Stamp screen, an ordinary pages/templates page that joins every tree-wide count.   # (was 125, 150)   # ES-6, 25 Oct 2026 - lease_signing_detail.html, the envelope page, an ordinary page that joins every tree-wide count.   # (was 124, 149)   # ES-3b, 24 Oct 2026 - the Send for Signature screen, an ordinary page that joins every tree-wide count.   # (was 123, 148)   # ES-4, 24 Oct 2026 - the four public signing templates. They are ordinary pages/templates files, so they join every tree-wide count; they cannot extend base, which is why they are standalone.   # (was 119, 144)   # ES-3a, 23 Oct 2026 - lease_signing_list.html, the envelope register. An ordinary pages/templates page, so it joins every tree-wide count.   # (was 118, 143)   # RV-1, 23 Oct 2026 - cash_receipt_detail.html. The same pair as test_js_buttons and test_recipe_tones: an ordinary pages/templates page joins the sweep scope and the page count alike.   # (was 117, 142)   # PP-1, 20 Oct 2026 - meal_plan_print.html. (GATE_NOW was 141)   # RD-1, 19 Oct 2026 - the quick-look
# pair. (GATE_NOW was 139)   # RT-1, 18 Oct 2026 - the wide census is four meal-plan screens smaller and one planner larger. The narrow half does not move.   # (GATE_NOW was 142)

'''),
    ]),
    (os.path.join('test_tree_roots.py'), [
        (r'''# 143 since 6 Oct: Section E round E-2b added access_denied.html,
# the 403 page, which until then lived in an f-string.
MAIN_N = 155   # CG-1, 13 Nov 2026 - celebration_gifts.html, the My gifts page with the Christmas list, an ordinary pages/templates page that joins every tree-wide count.   # (was 154)   # GL-1, 28 Oct 2026 - company_details.html, the Company Details screen, an ordinary pages/templates page that joins every tree-wide count.   # (was 153)   # LS-1, 27 Oct 2026 - tenant_lease_signing_status.html, the Lease Signing Status report, an ordinary pages/templates page that joins every tree-wide count.   # (was 152)   # ES-7, 25 Oct 2026 - house_marks.html, the Signature and Stamp screen, an ordinary pages/templates page that joins every tree-wide count.   # (was 151)   # ES-6, 25 Oct 2026 - lease_signing_detail.html, the envelope page, an ordinary pages/templates page that joins every tree-wide count.   # (was 150)   # ES-3b, 24 Oct 2026 - the Send for Signature screen, an ordinary page that joins every tree-wide count.   # (was 149)   # ES-4, 24 Oct 2026 - the four public signing templates. They are ordinary pages/templates files, so they join every tree-wide count; they cannot extend base, which is why they are standalone.   # (was 145)   # ES-3a, 23 Oct 2026 - lease_signing_list.html, the envelope register. An ordinary pages/templates page, so it joins every tree-wide count.   # (was 144)   # RV-1, 23 Oct 2026 - cash_receipt_detail.html. This is the shape of the tree, which is what this file is for.   # (was 143)   # PP-1, 20 Oct 2026 - the printable meal plan is a
               # new page: 142 + 1. (was 142)   # RD-1, 19 Oct 2026 - the quick-look dialog adds two:
               # the partial and its shell. (was 140)   # RT-1, 18 Oct 2026 - MN-1 retired four meal-plan screens and the planner replaced them: 143 - 4 + 1. This is the shape of the tree, which is what this file is for.   # (was 143)
''',
         r'''# 143 since 6 Oct: Section E round E-2b added access_denied.html,
# the 403 page, which until then lived in an f-string.
MAIN_N = 156   # RA15, 23 Nov 2026 - user_activity.html, the Activity page, an ordinary pages/templates page that joins every tree-wide count.   # (was 155)   # CG-1, 13 Nov 2026 - celebration_gifts.html, the My gifts page with the Christmas list, an ordinary pages/templates page that joins every tree-wide count.   # (was 154)   # GL-1, 28 Oct 2026 - company_details.html, the Company Details screen, an ordinary pages/templates page that joins every tree-wide count.   # (was 153)   # LS-1, 27 Oct 2026 - tenant_lease_signing_status.html, the Lease Signing Status report, an ordinary pages/templates page that joins every tree-wide count.   # (was 152)   # ES-7, 25 Oct 2026 - house_marks.html, the Signature and Stamp screen, an ordinary pages/templates page that joins every tree-wide count.   # (was 151)   # ES-6, 25 Oct 2026 - lease_signing_detail.html, the envelope page, an ordinary pages/templates page that joins every tree-wide count.   # (was 150)   # ES-3b, 24 Oct 2026 - the Send for Signature screen, an ordinary page that joins every tree-wide count.   # (was 149)   # ES-4, 24 Oct 2026 - the four public signing templates. They are ordinary pages/templates files, so they join every tree-wide count; they cannot extend base, which is why they are standalone.   # (was 145)   # ES-3a, 23 Oct 2026 - lease_signing_list.html, the envelope register. An ordinary pages/templates page, so it joins every tree-wide count.   # (was 144)   # RV-1, 23 Oct 2026 - cash_receipt_detail.html. This is the shape of the tree, which is what this file is for.   # (was 143)   # PP-1, 20 Oct 2026 - the printable meal plan is a
               # new page: 142 + 1. (was 142)   # RD-1, 19 Oct 2026 - the quick-look dialog adds two:
               # the partial and its shell. (was 140)   # RT-1, 18 Oct 2026 - MN-1 retired four meal-plan screens and the planner replaced them: 143 - 4 + 1. This is the shape of the tree, which is what this file is for.   # (was 143)
'''),
    ]),
    (os.path.join('test_subtree_tones.py'), [
        (r'''# GL-1, 28 Oct 2026 - company_details.html, the Company Details screen, an ordinary pages/templates page that joins every tree-wide count.
# CG-1, 13 Nov 2026 - celebration_gifts.html, the My gifts page with the Christmas list, an ordinary pages/templates page that joins every tree-wide count. (was 162 and 136)
ok(len(tree) == 163, 'a WALK finds 163 templates', len(tree))
ok(len(top) == 137, '  a flat listing finds 137 - 120 was what H7 '
   'counted, 122 after MN-1, and RD-1 adds the quick-look pair',
   len(top))
''',
         r'''# GL-1, 28 Oct 2026 - company_details.html, the Company Details screen, an ordinary pages/templates page that joins every tree-wide count.
# CG-1, 13 Nov 2026 - celebration_gifts.html, the My gifts page with the Christmas list, an ordinary pages/templates page that joins every tree-wide count. (was 162 and 136)
# RA15, 23 Nov 2026 - user_activity.html, the Activity page, joins both
# counts (was 163 and 137).
ok(len(tree) == 164, 'a WALK finds 164 templates', len(tree))
ok(len(top) == 138, '  a flat listing finds 138 - 120 was what H7 '
   'counted, 122 after MN-1, and RD-1 adds the quick-look pair',
   len(top))
'''),
    ]),
    (os.path.join('pages', 'key_health.py'), [
        (r'''            except Exception:                           # noqa: BLE001
                logger.exception('travel ideas catch-up')
            finally:
                close_old_connections()
''',
         r'''            except Exception:                           # noqa: BLE001
                logger.exception('travel ideas catch-up')
            try:            # RA15 - the activity log keeps 12 months
                from pages import activity
                activity.purge()
            except Exception:                           # noqa: BLE001
                logger.exception('activity purge')
            finally:
                close_old_connections()
'''),
    ]),
    (os.path.join('test_planner.py'), [
        (r'''    # the people the Share dialog offers (one query, however many).
    # None of them grows with the meals - the check above proves that.
    ok(q_big <= 18, '  and that number is under 18', q_big)

    head('8f. the shopping list shops a range')
''',
         r'''    # the people the Share dialog offers (one query, however many).
    # None of them grows with the meals - the check above proves that.
    # RA15, 23 Nov 2026 - nineteen. One more on every page: the activity
    # log writes the visit (pages/activity.py). Fixed, never per meal.
    ok(q_big <= 19, '  and that number is under 19', q_big)

    head('8f. the shopping list shops a range')
'''),
    ]),
    (os.path.join('test_pair_contrast.py'), [
        (r'''MARK = 'B-4b, 8 Oct 2026'

EXPECT_PAIRS = 752   # RC-3, 12 Nov 2026 - cook mode on the recipe page: the full-screen step view sets the paper fill and its ink, and its Next button the accent fill and the on-accent ink. Two rules, pairs base already uses.   # (was 750)   # CR-2, 27 Oct 2026 - the receipt email pop-up, on Receipts and on Receipt Details: the message box and the Printed warning each set a fill and its ink, pairs base already uses.   # (was 746)   # ES-11, 26 Oct 2026 - the yellow signed-leases bar left Home and Notifications, and with it .lsa-strip's fill+ink pair on each page.   # (was 748)   # ES-9, 26 Oct 2026 - Home's Waiting for you icon chip, .ins-ic--wait, sets the warn-soft fill and warn-ink together, a pair base already uses.   # (was 747)   # ES-7, 25 Oct 2026 - two notes set a fill and an ink together: .hm-note on the Signature and Stamp screen and .ls-saved-note on the signing page, both on the accent pair this table already knows.   # (was 745)   # ES-6, 25 Oct 2026 - three more rules in ES-6's pages set a fill and an ink together, measured by this census on the full tree.   # (was 742)   # ES-4, 24 Oct 2026 - eleven in the public signing pages' own stylesheet. A standalone page cannot inherit a surface, so every one it draws sets both halves of the pair itself - which is exactly why this census asks about them.   # (was 731)   # ES-3a, 23 Oct 2026 - the lease signing register: three signer dots mirroring the good, bad and neutral pills, and the waiting-on-you note. Four rules, no new pairings.   # (was 727)   # MN-2, 21 Oct 2026 - the Saved Menus dialog gains the preset row CP-2 built for Copy, and .mn-preset[aria-pressed=true] sets a fill and an ink together exactly as .cp-preset does. One more pair, of tokens this table already knows.   # (was 726)   # RG-2, 21 Oct 2026 - two more rules set a fill and an ink together: the date field, which wears the paper token on the ink one like every other field in the system, and the line explaining the second Print press, which sits on the surface wash.   # (was 724)   # RG-1, 21 Oct 2026 - the printed sheet is drawn again from four layouts, and five more of its rules set a fill and an ink together: the pill in its three states, the today marker and the dimmed cell. Every one is a token pair this table already knows.   # (was 719)   # PP-1, 20 Oct 2026 - the printable plan sets
# both a ground and an ink on six rules. All house pairs off base's
# own tokens, so the AA table below is untouched and the gross count
''',
         r'''MARK = 'B-4b, 8 Oct 2026'

EXPECT_PAIRS = 758   # RA15, 23 Nov 2026 - user_activity.html, the Activity page: its tabs, the usage grid's four shades and its pill each set a fill and an ink, all AA.   # (was 752)   # RC-3, 12 Nov 2026 - cook mode on the recipe page: the full-screen step view sets the paper fill and its ink, and its Next button the accent fill and the on-accent ink. Two rules, pairs base already uses.   # (was 750)   # CR-2, 27 Oct 2026 - the receipt email pop-up, on Receipts and on Receipt Details: the message box and the Printed warning each set a fill and its ink, pairs base already uses.   # (was 746)   # ES-11, 26 Oct 2026 - the yellow signed-leases bar left Home and Notifications, and with it .lsa-strip's fill+ink pair on each page.   # (was 748)   # ES-9, 26 Oct 2026 - Home's Waiting for you icon chip, .ins-ic--wait, sets the warn-soft fill and warn-ink together, a pair base already uses.   # (was 747)   # ES-7, 25 Oct 2026 - two notes set a fill and an ink together: .hm-note on the Signature and Stamp screen and .ls-saved-note on the signing page, both on the accent pair this table already knows.   # (was 745)   # ES-6, 25 Oct 2026 - three more rules in ES-6's pages set a fill and an ink together, measured by this census on the full tree.   # (was 742)   # ES-4, 24 Oct 2026 - eleven in the public signing pages' own stylesheet. A standalone page cannot inherit a surface, so every one it draws sets both halves of the pair itself - which is exactly why this census asks about them.   # (was 731)   # ES-3a, 23 Oct 2026 - the lease signing register: three signer dots mirroring the good, bad and neutral pills, and the waiting-on-you note. Four rules, no new pairings.   # (was 727)   # MN-2, 21 Oct 2026 - the Saved Menus dialog gains the preset row CP-2 built for Copy, and .mn-preset[aria-pressed=true] sets a fill and an ink together exactly as .cp-preset does. One more pair, of tokens this table already knows.   # (was 726)   # RG-2, 21 Oct 2026 - two more rules set a fill and an ink together: the date field, which wears the paper token on the ink one like every other field in the system, and the line explaining the second Print press, which sits on the surface wash.   # (was 724)   # RG-1, 21 Oct 2026 - the printed sheet is drawn again from four layouts, and five more of its rules set a fill and an ink together: the pill in its three states, the today marker and the dimmed cell. Every one is a token pair this table already knows.   # (was 719)   # PP-1, 20 Oct 2026 - the printable plan sets
# both a ground and an ink on six rules. All house pairs off base's
# own tokens, so the AA table below is untouched and the gross count
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
    raise SystemExit('RA15 REFUSED: %s' % msg)


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
    if "'test_ra15_activity_log.py'" in read(pq):
        print('RA15 already applied.')
        return 0
    if "'test_ra14_trip_tabs_tap.py'" not in read(pq):
        refuse('RA14 (apply_ra14_trip_tabs_tap.py) is not applied - this round registers after it.')
    for rel in CREATES:
        if not os.path.isfile(os.path.join(root, *rel.split('/'))):
            refuse('%s is missing - it ships with this patcher; copy the '
                   'new files and the suite in first.' % rel)

    for rel, pairs in SWAPS:
        pth = os.path.join(root, rel)
        t = read(pth)
        for i, (was, now) in enumerate(pairs):
            t = swap(t, was, now, '%s (swap %d of %d)'
                     % (rel, i + 1, len(pairs)))
        out[pth] = t

    if CHECK:
        print('RA15 --check: %d file(s) would change, none written; %d '
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
    print('RA15 applied - the activity log. Run: python manage.py migrate')
    print('      %d file(s) written, backed up to %s' % (len(out), SUFFIX))
    print('      %d file(s) ship with it, wired in rather than written'
          % len(CREATES))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
