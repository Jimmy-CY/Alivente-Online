# -*- coding: utf-8 -*-
"""apply_ra19_acquisitions_screens.py - round RA19, 23 Nov 2026.

RELEASE RA19 - PROPERTY ACQUISITIONS, STEP 2: THE ELEVEN SCREENS.

    The pages Demetri approved in the mockups, inside the house standard,
    with a tab bar in place of the mockups' second side menu (Demetri, 23
    Nov: "Great. Get started").

    - acquisitions/ gains views.py, urls.py, services.py, presets.py, its
      template tags, and fourteen templates: Overview, Scenarios, the
      scenario editor with a live preview, a scenario's results (and the
      plot version, in EUR per buildable m2), a property (scorecard, price
      history, questions for the agent, the market, notes and viewings,
      an A4 offer-brief PDF), Price watch, Market snapshot, Auctions &
      off-market and Search runs. Phone bars use the house More menu.
    - acquisitions/models.py: a decision carries a few words of why
      (ScenarioMatch.decision_note); the watch rules are kept
      (WatchSettings). Migration 0002 ships beside this patcher.
    - mysite/urls.py: /acquisitions/.
    - pages/templates/base.html: Acquisitions under Property Operations,
      after Projects, in the sidebar and the menu; the group shows for
      someone with only Acquisitions.
    - mysite/settings.py: mysql.W003 silenced, with the reason beside it.
    - alv_tree.py: the app's templates are in the house tree checks.
    - Help: pages/help_content/acquisitions.html - one Help for the module.
    - House suites, re-pinned where a tree-wide count meets fourteen new
      templates in a third root (each pin says RA19 and what it was):
      bar_height, colour_neutrals/tail/tokens, css_standalone,
      important_base, lease_sign, drift_root, crs_detail_rest, help_label,
      house_title, save_and_cancel, req_marker, radius_token,
      subtree_tones, colour_census, recipe_side_b, recipe_tones,
      heading_prefix, heading_standard, pair_contrast, tree_roots,
      label_weight (moved to the live censuses in test_retired).
      test_panel_title learns that a shared style partial is worn by the
      pages that include it.

Stands on RA18. Idempotent. Edits backed up to .bak_ra19.
MIGRATION: run  python manage.py migrate  before pushing.
"""
import os
import sys

SUFFIX = '.bak_ra19'
MARK = 'RA19, 23 Nov 2026'
CHECK = False
PS1 = 'Push-PendingChanges.ps1'
CREATES = (
    'acquisitions/migrations/0002_decision_note_watch_settings.py',
    'acquisitions/presets.py',
    'acquisitions/services.py',
    'acquisitions/templates/acquisitions/_run_modal.html',
    'acquisitions/templates/acquisitions/_style.html',
    'acquisitions/templates/acquisitions/_tabs.html',
    'acquisitions/templates/acquisitions/auctions.html',
    'acquisitions/templates/acquisitions/market.html',
    'acquisitions/templates/acquisitions/offer_brief.html',
    'acquisitions/templates/acquisitions/overview.html',
    'acquisitions/templates/acquisitions/plot_results.html',
    'acquisitions/templates/acquisitions/price_watch.html',
    'acquisitions/templates/acquisitions/property.html',
    'acquisitions/templates/acquisitions/runs.html',
    'acquisitions/templates/acquisitions/scenario_edit.html',
    'acquisitions/templates/acquisitions/scenario_results.html',
    'acquisitions/templates/acquisitions/scenarios.html',
    'acquisitions/templatetags/__init__.py',
    'acquisitions/templatetags/acq.py',
    'acquisitions/urls.py',
    'acquisitions/views.py',
    'pages/help_content/acquisitions.html',
    'test_ra19_acquisitions_screens.py',
)

SWAPS = [
    (os.path.join('Push-PendingChanges.ps1'), [
        (r'''    'test_ra17_send_standard_month.py',
    # RA18, 23 Nov 2026 - Property Acquisitions, step 1: the foundation.
    'test_ra18_acquisitions.py'
)
# NUMBER EVERY SUITE AS IT RUNS - Demetri, 1 Oct 2026: "for every check of
''',
         r'''    'test_ra17_send_standard_month.py',
    # RA18, 23 Nov 2026 - Property Acquisitions, step 1: the foundation.
    'test_ra18_acquisitions.py',
    # RA19, 23 Nov 2026 - Property Acquisitions, step 2: the eleven screens.
    'test_ra19_acquisitions_screens.py'
)
# NUMBER EVERY SUITE AS IT RUNS - Demetri, 1 Oct 2026: "for every check of
'''),
    ]),
    (os.path.join('acquisitions', 'models.py'), [
        (r'''    # Yours
    your_comments = models.TextField(blank=True)

    date_found = models.DateField(default=timezone.localdate)
''',
         r'''    # Yours
    your_comments = models.TextField(blank=True)
    # RA19, 23 Nov 2026 - why you shortlisted or rejected it, in a few
    # words ("separate kitchen"). Shown beside the status everywhere.
    decision_note = models.CharField(max_length=200, blank=True)

    date_found = models.DateField(default=timezone.localdate)
'''),
        (r'''        return f"{self.property} in {self.scenario}"

    def set_status_by_user(self, status):
        self.status = status
        self.status_set_by_user = status in self.USER_STATUSES
        self.save(update_fields=["status", "status_set_by_user"])


''',
         r'''        return f"{self.property} in {self.scenario}"

    def set_status_by_user(self, status, note=None):
        self.status = status
        self.status_set_by_user = status in self.USER_STATUSES
        fields = ["status", "status_set_by_user"]
        if note is not None:
            self.decision_note = note[:200]
            fields.append("decision_note")
        self.save(update_fields=fields)


'''),
        (r'''            fields=["week_start", "area", "property_type", "size_band"],
            name="acq_one_snapshot_per_week_area_type_band")]
''',
         r'''            fields=["week_start", "area", "property_type", "size_band"],
            name="acq_one_snapshot_per_week_area_type_band")]


# --------------------------------------------------------------------------
# Price watch rules - RA19, 23 Nov 2026
# --------------------------------------------------------------------------
class WatchSettings(models.Model):
    """ONE ROW: what the daily price watch re-checks and when it alerts.

    The Price watch screen edits it; Claude's price-watch task reads it
    (step 5). get() makes the row on first use, so nothing has to seed it.
    """
    SCOPE_CHOICES = [("shortlisted", "Shortlisted listings only"),
                     ("shortlisted_active", "Shortlisted and active")]
    DROP_CHOICES = [("any", "Any amount"), ("3", "At least 3%"), ("5", "At least 5%")]

    scope = models.CharField(max_length=20, choices=SCOPE_CHOICES, default="shortlisted_active")
    drop_alert = models.CharField(max_length=5, choices=DROP_CHOICES, default="any")
    alert_disappears = models.BooleanField(default=True)
    alert_rejected_passes = models.BooleanField(default=True)
    run_time = models.TimeField(default="07:05")

    class Meta:
        verbose_name = "price watch settings"
        verbose_name_plural = "price watch settings"

    def __str__(self):
        return "Price watch settings"

    @classmethod
    def get(cls):
        obj = cls.objects.order_by("pk").first()
        return obj or cls.objects.create()
'''),
    ]),
    (os.path.join('alv_rounds.py'), [
        (r'''    # RA18, 23 Nov 2026 - Property Acquisitions, step 1: the foundation.
    '.bak_ra18',
]

''',
         r'''    # RA18, 23 Nov 2026 - Property Acquisitions, step 1: the foundation.
    '.bak_ra18',
    # RA19, 23 Nov 2026 - Property Acquisitions, step 2: the eleven screens.
    '.bak_ra19',
]

'''),
    ]),
    (os.path.join('alv_tree.py'), [
        (r'''    (('crs', 'templates'),
     'the CRS reporting app, mounted at /crs/ by mysite/urls.py'),
]

''',
         r'''    (('crs', 'templates'),
     'the CRS reporting app, mounted at /crs/ by mysite/urls.py'),
    # RA19, 23 Nov 2026 - inside the house standard, like CRS.
    (('acquisitions', 'templates'),
     'the Property Acquisitions app, mounted at /acquisitions/ by '
     'mysite/urls.py'),
]

'''),
    ]),
    (os.path.join('mysite', 'settings.py'), [
        (r'''    }
})
"""''',
         r'''    }
})
"""

# RA19, 23 Nov 2026 - ONE SYSTEM-CHECK WARNING SWITCHED OFF, ON PURPOSE.
# mysql.W003 says MySQL "may not allow" a unique text column longer than
# 255 characters. acquisitions.ListingSource.url is 500 and unique: a
# listing link can be long, and one link must never be stored twice.
# MySQL 8 (InnoDB, DYNAMIC rows, utf8mb4) indexes up to 3,072 bytes and
# 500 x 4 is 2,000, so the index can exist - RA18's migrate created it
# on Demetri's machine without complaint. Only this warning is silenced.
SILENCED_SYSTEM_CHECKS = ["mysql.W003"]
'''),
    ]),
    (os.path.join('mysite', 'urls.py'), [
        (r'''    path('', include('pages.urls')),
    path("crs/", include("crs.urls")),
    # WL-1, 30 Oct 2026 - Wellness. wellness/app/ (the installable-app
    # shell) answers without a login; everything else needs one.
''',
         r'''    path('', include('pages.urls')),
    path("crs/", include("crs.urls")),
    # RA19, 23 Nov 2026 - Property Acquisitions, under Property Operations.
    path("acquisitions/", include("acquisitions.urls")),
    # WL-1, 30 Oct 2026 - Wellness. wellness/app/ (the installable-app
    # shell) answers without a login; everything else needs one.
'''),
    ]),
    (os.path.join('pages', 'templates', 'base.html'), [
        (r'''    <div class="sidebar-nav">

      {% if user.is_superuser or perms.auth.can_access_properties or perms.auth.can_access_tenants or perms.auth.can_access_suppliers or perms.auth.can_access_issues or perms.auth.can_access_projects or perms.auth.can_access_dashboard %}
      <div class="sidebar-section-header" onclick="toggleSection('propSection', this)">
          <i class="fas fa-building section-icon"></i>
''',
         r'''    <div class="sidebar-nav">

      {% if user.is_superuser or perms.auth.can_access_properties or perms.auth.can_access_tenants or perms.auth.can_access_suppliers or perms.auth.can_access_issues or perms.auth.can_access_projects or perms.auth.can_access_acquisitions or perms.auth.can_access_dashboard %}
      <div class="sidebar-section-header" onclick="toggleSection('propSection', this)">
          <i class="fas fa-building section-icon"></i>
'''),
        (r'''          <a href="{% url 'projects' %}" class="sidebar-link {% if request.resolver_match.url_name == 'projects' %}active{% endif %}" data-tooltip="Projects">
              <i class="fas fa-project-diagram"></i><span class="link-text">Projects</span>
          </a>
          {% endif %}
''',
         r'''          <a href="{% url 'projects' %}" class="sidebar-link {% if request.resolver_match.url_name == 'projects' %}active{% endif %}" data-tooltip="Projects">
              <i class="fas fa-project-diagram"></i><span class="link-text">Projects</span>
          </a>
          {% endif %}
          {# RA19, 23 Nov 2026 - Property Acquisitions, after Projects. #}
          {% if user.is_superuser or perms.auth.can_access_acquisitions %}
          <a href="{% url 'acquisitions:overview' %}" class="sidebar-link {% if request.resolver_match.app_name == 'acquisitions' %}active{% endif %}" data-tooltip="Acquisitions">
              <i class="fas fa-search-location"></i><span class="link-text">Acquisitions</span>
          </a>
          {% endif %}
'''),
        (r'''        <ul class="navbar-nav mr-auto">
          {% if user.is_authenticated %}
            {% if user.is_superuser or perms.auth.can_access_properties or perms.auth.can_access_tenants or perms.auth.can_access_suppliers or perms.auth.can_access_issues or perms.auth.can_access_projects or perms.auth.can_access_dashboard %}
            <li class="nav-item dropdown">
              <a class="nav-link dropdown-toggle" href="#" id="propertyDropdown" role="button" data-toggle="dropdown">Property Operations</a>
''',
         r'''        <ul class="navbar-nav mr-auto">
          {% if user.is_authenticated %}
            {% if user.is_superuser or perms.auth.can_access_properties or perms.auth.can_access_tenants or perms.auth.can_access_suppliers or perms.auth.can_access_issues or perms.auth.can_access_projects or perms.auth.can_access_acquisitions or perms.auth.can_access_dashboard %}
            <li class="nav-item dropdown">
              <a class="nav-link dropdown-toggle" href="#" id="propertyDropdown" role="button" data-toggle="dropdown">Property Operations</a>
'''),
        (r'''                {% if user.is_superuser or perms.auth.can_access_suppliers %}<a class="dropdown-item" href="{% url 'suppliers' %}">Suppliers</a>{% endif %}
                {% if user.is_superuser or perms.auth.can_access_issues %}<a class="dropdown-item" href="{% url 'fsr' %}">Issues</a>{% endif %}
                {% if user.is_superuser or perms.auth.can_access_projects or perms.auth.can_access_dashboard %}<div class="dropdown-divider"></div>{% endif %}
                {% if user.is_superuser or perms.auth.can_access_projects %}<a class="dropdown-item" href="{% url 'projects' %}">Projects</a>{% endif %}
                {% if user.is_superuser or perms.auth.can_access_dashboard %}<a class="dropdown-item" href="{% url 'property_management_dashboard' %}">Dashboard</a>{% endif %}
              </div>
''',
         r'''                {% if user.is_superuser or perms.auth.can_access_suppliers %}<a class="dropdown-item" href="{% url 'suppliers' %}">Suppliers</a>{% endif %}
                {% if user.is_superuser or perms.auth.can_access_issues %}<a class="dropdown-item" href="{% url 'fsr' %}">Issues</a>{% endif %}
                {% if user.is_superuser or perms.auth.can_access_projects or perms.auth.can_access_acquisitions or perms.auth.can_access_dashboard %}<div class="dropdown-divider"></div>{% endif %}
                {% if user.is_superuser or perms.auth.can_access_projects %}<a class="dropdown-item" href="{% url 'projects' %}">Projects</a>{% endif %}
                {% if user.is_superuser or perms.auth.can_access_acquisitions %}<a class="dropdown-item" href="{% url 'acquisitions:overview' %}">Acquisitions</a>{% endif %}
                {% if user.is_superuser or perms.auth.can_access_dashboard %}<a class="dropdown-item" href="{% url 'property_management_dashboard' %}">Dashboard</a>{% endif %}
              </div>
'''),
    ]),
    (os.path.join('test_bar_height.py'), [
        (r'''
BAR, ROW, MODAL = 35, 34, 38
N_BAR, N_ROW, N_MODAL = 295, 122, 103   # RA15, 23 Nov 2026 - Activity joins the User Administration bar, and the new Activity page's bar has Help and Back.   # (N_BAR was 292)   # CX-1, 29 Oct 2026 - Help joins the Task List and Gantt Chart bars.   # (N_BAR was 290)   # GL-3, 29 Oct 2026 - the Greek Details pop-up, Cancel and Done, on Tenant Edit and Tenant Add.   # (N_MODAL was 99)   # GE-1, 28 Oct 2026 - Generate gains Send for e-signing beside Download Word, and the envelope page a Word version button.   # (N_BAR was 288)   # GL-1, 28 Oct 2026 - the Company Details screen's bar, Save and Back.   # (N_BAR was 286)   # HK-4, 28 Oct 2026 - Help on the Project Details bar, his finding   # (N_BAR was 285)   # CR-2, 27 Oct 2026 - emailing a receipt: Email receipt in the Receipt Details bar (both arms of its if), the paper-plane in the Receipts row (live and greyed), and Cancel and Send in the pop-up on both pages.   # (was 283, 120, 95)   # ES-9, 26 Oct 2026 - the envelope page draws a greyed Approve and attach when no tenancy is free to receive the lease; both arms of the if count.   # (was 282, 120)   # HK-1, 26 Oct 2026 - the paper-plane left Manage Lease Agreements, his decision; both arms of its superuser check counted, so the row figure falls by two.   # (was 282, 122)   # ES-8, 25 Oct 2026 - the Lease Signing register gains a Help secondary in its bar, and a View-signed-lease icon in its row actions.   # (was 281, 121)   # ES-7, 25 Oct 2026 - the Signature and Stamp screen's bar, Back alone.   # (was 280)   # ES-6, 25 Oct 2026 - the envelope page's bar (Approve and attach, Decline, View signed lease, Back). This census does not resolve a branch, so Approve and Decline count even though they only show while an envelope is awaiting approval.   # (was 276)   # ES-3b, 24 Oct 2026 - the Send for Signature screen (Create and sign, Back) and the Send row action on Manage Lease Agreements. This census does not resolve a branch, so both arms of the perms check count - which is why the row figure moved by two and not by one.   # (was 274, 119)   # ES-3a, 23 Oct 2026 - lease_signing_list.html, the envelope register. An ordinary pages/templates page, so it joins every tree-wide count.   # (was 270, 116)   # RV-1, 23 Oct 2026 - the Receipt Details bar: View receipt, Edit and Back. A new PAGE, so three controls join the census without any existing bar changing.   # (was 267)   # TD-2, 16 Oct 2026 - the two disabled twins. A twin is an .icon-action-btn in a table row, so this census counts it exactly as it counts the button it stands in for - which is the whole idea.   # (was 114)   # NV-1d, 16 Oct 2026 - the View button in the desktop strip, which is inside a table.   # (was 113)   # NV-1c, 16 Oct 2026 - the physical invoice disabled mirror, in the desktop strip, which is inside a table.   # (was 112)   # NV-1b, 16 Oct 2026 - the title deeds Actions cell drew two Bootstrap buttons, which this census cannot see. They are icon-delete and icon-upload now, so two controls join the table-row count without a control being added.   # (was 110)   # PJ-1, 15 Oct 2026 - projects_edit carried its Back control twice, behind an if on from_gantt. This census does not resolve a branch, so it counted both arms; one Back control now, and one count.   # (was 268)   # PV-1, 15 Oct 2026 - the four footer buttons of two hand-rolled invoice viewers. The shared component they moved onto was already in this census, so the count falls by exactly the four that went.   # (was 99)   # VC-1, 14 Oct 2026 - property_assets Take Photo is a <label> that had no house class until this round, so this census could not see it. 35px, in a modal, and named in STRAYS below.   # (was 98)   # DB-5, 12 Oct 2026 - the
# dashboard four joined the bar   # (was 265)   # E-10, 11 Oct 2026 - the
# seven buttons this round paired in CRS modals become visible to
# a census that selects the two position tones and not the danger
# tone.   # (was 91)
N_LOOSE, N_LOOSE_H = 95, 11   # GE-1, 28 Oct 2026 - Read it before sending and Word version on the Send screen's generated-lease card, at heights the set already held.   # (was 93)   # CR-2, 27 Oct 2026 - the Save on the Cash Receipt to Payer card, at a height the set already held.   # (was 92)   # LS-1, 27 Oct 2026 - Include finished and Back in the Lease Signing Status report head, at heights the set already held.   # (was 90)   # ES-7b, 25 Oct 2026 - the Delete envelope button in its own card on the envelope page, at a height already in the set.   # (was 89)   # ES-7, 25 Oct 2026 - the two Save buttons on the Signature and Stamp cards, at a height already in the set.   # (was 87)   # ES-3b, 24 Oct 2026 - Choose a different tenant, which sits in a form card rather than in the action bar. N_LOOSE_H does not move: 35px is a height this set already held.   # (was 86)   # LV-1, 16 Oct 2026 - three of the 25 retoned buttons sit in a card or loose on a page. This census selects on a house class, so it could not see them while a LEAVE entry was keeping them Bootstrap-coloured. N_LOOSE_H does not move - all three land on heights the set already held.   # (was 83)   # NV-1c, 16 Oct 2026 - the two comment controls. They were .status-btn, which this census does not select, and they sit in a comment thread rather than a table, so they land in the loose set. 34px was already one of its eleven heights, so N_LOOSE_H does not move.   # (was 81)   # VC-1, 14 Oct 2026 - edit_asset Take Photo at 35px and my_profile Upload Photo at 31px, both <label> file pickers that had no house class until this round. 35 is a height this set did not hold before.   # (was 80 and 10)   # DB-5 - the side column left the
# loose set, and the two heights it invented went with it
# (was 82 and 12)   # E-10 - and the four loose in
''',
         r'''
BAR, ROW, MODAL = 35, 34, 38
N_BAR, N_ROW, N_MODAL = 331, 126, 109   # RA19, 23 Nov 2026 - the Acquisitions screens join the census: their bars, their table-row actions and their pop-ups' buttons, every one at the height its place already held (no new stray).   # (was 295, 122, 103)   # RA15, 23 Nov 2026 - Activity joins the User Administration bar, and the new Activity page's bar has Help and Back.   # (N_BAR was 292)   # CX-1, 29 Oct 2026 - Help joins the Task List and Gantt Chart bars.   # (N_BAR was 290)   # GL-3, 29 Oct 2026 - the Greek Details pop-up, Cancel and Done, on Tenant Edit and Tenant Add.   # (N_MODAL was 99)   # GE-1, 28 Oct 2026 - Generate gains Send for e-signing beside Download Word, and the envelope page a Word version button.   # (N_BAR was 288)   # GL-1, 28 Oct 2026 - the Company Details screen's bar, Save and Back.   # (N_BAR was 286)   # HK-4, 28 Oct 2026 - Help on the Project Details bar, his finding   # (N_BAR was 285)   # CR-2, 27 Oct 2026 - emailing a receipt: Email receipt in the Receipt Details bar (both arms of its if), the paper-plane in the Receipts row (live and greyed), and Cancel and Send in the pop-up on both pages.   # (was 283, 120, 95)   # ES-9, 26 Oct 2026 - the envelope page draws a greyed Approve and attach when no tenancy is free to receive the lease; both arms of the if count.   # (was 282, 120)   # HK-1, 26 Oct 2026 - the paper-plane left Manage Lease Agreements, his decision; both arms of its superuser check counted, so the row figure falls by two.   # (was 282, 122)   # ES-8, 25 Oct 2026 - the Lease Signing register gains a Help secondary in its bar, and a View-signed-lease icon in its row actions.   # (was 281, 121)   # ES-7, 25 Oct 2026 - the Signature and Stamp screen's bar, Back alone.   # (was 280)   # ES-6, 25 Oct 2026 - the envelope page's bar (Approve and attach, Decline, View signed lease, Back). This census does not resolve a branch, so Approve and Decline count even though they only show while an envelope is awaiting approval.   # (was 276)   # ES-3b, 24 Oct 2026 - the Send for Signature screen (Create and sign, Back) and the Send row action on Manage Lease Agreements. This census does not resolve a branch, so both arms of the perms check count - which is why the row figure moved by two and not by one.   # (was 274, 119)   # ES-3a, 23 Oct 2026 - lease_signing_list.html, the envelope register. An ordinary pages/templates page, so it joins every tree-wide count.   # (was 270, 116)   # RV-1, 23 Oct 2026 - the Receipt Details bar: View receipt, Edit and Back. A new PAGE, so three controls join the census without any existing bar changing.   # (was 267)   # TD-2, 16 Oct 2026 - the two disabled twins. A twin is an .icon-action-btn in a table row, so this census counts it exactly as it counts the button it stands in for - which is the whole idea.   # (was 114)   # NV-1d, 16 Oct 2026 - the View button in the desktop strip, which is inside a table.   # (was 113)   # NV-1c, 16 Oct 2026 - the physical invoice disabled mirror, in the desktop strip, which is inside a table.   # (was 112)   # NV-1b, 16 Oct 2026 - the title deeds Actions cell drew two Bootstrap buttons, which this census cannot see. They are icon-delete and icon-upload now, so two controls join the table-row count without a control being added.   # (was 110)   # PJ-1, 15 Oct 2026 - projects_edit carried its Back control twice, behind an if on from_gantt. This census does not resolve a branch, so it counted both arms; one Back control now, and one count.   # (was 268)   # PV-1, 15 Oct 2026 - the four footer buttons of two hand-rolled invoice viewers. The shared component they moved onto was already in this census, so the count falls by exactly the four that went.   # (was 99)   # VC-1, 14 Oct 2026 - property_assets Take Photo is a <label> that had no house class until this round, so this census could not see it. 35px, in a modal, and named in STRAYS below.   # (was 98)   # DB-5, 12 Oct 2026 - the
# dashboard four joined the bar   # (was 265)   # E-10, 11 Oct 2026 - the
# seven buttons this round paired in CRS modals become visible to
# a census that selects the two position tones and not the danger
# tone.   # (was 91)
N_LOOSE, N_LOOSE_H = 103, 11   # RA19, 23 Nov 2026 - the controls in the Acquisitions cards, Clear my decision among them, at heights the set already held (N_LOOSE_H does not move).   # (was 95)   # GE-1, 28 Oct 2026 - Read it before sending and Word version on the Send screen's generated-lease card, at heights the set already held.   # (was 93)   # CR-2, 27 Oct 2026 - the Save on the Cash Receipt to Payer card, at a height the set already held.   # (was 92)   # LS-1, 27 Oct 2026 - Include finished and Back in the Lease Signing Status report head, at heights the set already held.   # (was 90)   # ES-7b, 25 Oct 2026 - the Delete envelope button in its own card on the envelope page, at a height already in the set.   # (was 89)   # ES-7, 25 Oct 2026 - the two Save buttons on the Signature and Stamp cards, at a height already in the set.   # (was 87)   # ES-3b, 24 Oct 2026 - Choose a different tenant, which sits in a form card rather than in the action bar. N_LOOSE_H does not move: 35px is a height this set already held.   # (was 86)   # LV-1, 16 Oct 2026 - three of the 25 retoned buttons sit in a card or loose on a page. This census selects on a house class, so it could not see them while a LEAVE entry was keeping them Bootstrap-coloured. N_LOOSE_H does not move - all three land on heights the set already held.   # (was 83)   # NV-1c, 16 Oct 2026 - the two comment controls. They were .status-btn, which this census does not select, and they sit in a comment thread rather than a table, so they land in the loose set. 34px was already one of its eleven heights, so N_LOOSE_H does not move.   # (was 81)   # VC-1, 14 Oct 2026 - edit_asset Take Photo at 35px and my_profile Upload Photo at 31px, both <label> file pickers that had no house class until this round. 35 is a height this set did not hold before.   # (was 80 and 10)   # DB-5 - the side column left the
# loose set, and the two heights it invented went with it
# (was 82 and 12)   # E-10 - and the four loose in
'''),
    ]),
    (os.path.join('test_colour_neutrals.py'), [
        (r'''# turned up the other four one at a time, which is the register
# working: a count nobody checks is a count that drifts.
ok(len(STAND) == 18, '%d standalone template(s)' % len(STAND))
bad = [s for s in sorted(STAND) if os.path.exists(BYNAME[s] + SUFFIX)]
ok(not bad,
''',
         r'''# turned up the other four one at a time, which is the register
# working: a count nobody checks is a count that drifts.
# RA19, 23 Nov 2026 - 22 (was 18): the Acquisitions offer-brief PDF and its three
# partials (_style, _tabs, _run_modal), fragments included into pages that
# already extend base. test_ra19_acquisitions_screens.py checks the three
# partials use house tokens only, since the colour censuses skip them.
ok(len(STAND) == 22, '%d standalone template(s)' % len(STAND))
bad = [s for s in sorted(STAND) if os.path.exists(BYNAME[s] + SUFFIX)]
ok(not bad,
'''),
    ]),
    (os.path.join('test_colour_tail.py'), [
        (r'''# turned up the other four one at a time, which is the register
# working: a count nobody checks is a count that drifts.
ok(len(STAND) == 18, '%d standalone template(s)' % len(STAND))
bad = [s for s in sorted(STAND) if os.path.exists(BYNAME[s] + SUFFIX)]
ok(not bad,
''',
         r'''# turned up the other four one at a time, which is the register
# working: a count nobody checks is a count that drifts.
# RA19, 23 Nov 2026 - 22 (was 18): the Acquisitions offer-brief PDF and its three
# partials (_style, _tabs, _run_modal), fragments included into pages that
# already extend base. test_ra19_acquisitions_screens.py checks the three
# partials use house tokens only, since the colour censuses skip them.
ok(len(STAND) == 22, '%d standalone template(s)' % len(STAND))
bad = [s for s in sorted(STAND) if os.path.exists(BYNAME[s] + SUFFIX)]
ok(not bad,
'''),
    ]),
    (os.path.join('test_colour_tokens.py'), [
        (r'''# turned up the other four one at a time, which is the register
# working: a count nobody checks is a count that drifts.
ok(len(STAND) == 18, '%d standalone template(s)' % len(STAND), sorted(STAND))
BYNAME = {alv_tree.rel(q).replace(os.sep, '/'): q
          for q in alv_tree.templates()}
''',
         r'''# turned up the other four one at a time, which is the register
# working: a count nobody checks is a count that drifts.
# RA19, 23 Nov 2026 - 22 (was 18): the Acquisitions offer-brief PDF and its three
# partials (_style, _tabs, _run_modal), fragments included into pages that
# already extend base. test_ra19_acquisitions_screens.py checks the three
# partials use house tokens only, since the colour censuses skip them.
ok(len(STAND) == 22, '%d standalone template(s)' % len(STAND), sorted(STAND))
BYNAME = {alv_tree.rel(q).replace(os.sep, '/'): q
          for q in alv_tree.templates()}
'''),
    ]),
    (os.path.join('test_css_standalone.py'), [
        (r'''# test_cssrules_outside and test_dead_weight. test_lease_sign.py takes
# the job instead and compares each token value against base.html.
ok(len(sa) == 18, 'it names %d template(s)' % len(sa), sa)
for s in sa:
    print('      %s' % s)
''',
         r'''# test_cssrules_outside and test_dead_weight. test_lease_sign.py takes
# the job instead and compares each token value against base.html.
# RA19, 23 Nov 2026 - 22 (was 18): the Acquisitions offer-brief PDF and its three
# partials (_style, _tabs, _run_modal), fragments included into pages that
# already extend base. test_ra19_acquisitions_screens.py checks the three
# partials use house tokens only, since the colour censuses skip them.
ok(len(sa) == 22, 'it names %d template(s)' % len(sa), sa)
for s in sa:
    print('      %s' % s)
'''),
    ]),
    (os.path.join('test_important_base.py'), [
        (r'''# turned up the other four one at a time, which is the register
# working: a count nobody checks is a count that drifts.
ok(len(stand) == 18, '  eighteen templates are standalone',
   sorted(stand))

''',
         r'''# turned up the other four one at a time, which is the register
# working: a count nobody checks is a count that drifts.
# RA19, 23 Nov 2026 - 22 (was 18): the Acquisitions offer-brief PDF and its three
# partials (_style, _tabs, _run_modal), fragments included into pages that
# already extend base. test_ra19_acquisitions_screens.py checks the three
# partials use house tokens only, since the colour censuses skip them.
ok(len(stand) == 22, '  twenty-two templates are standalone',
   sorted(stand))

'''),
    ]),
    (os.path.join('test_lease_sign.py'), [
        (r'''
sa = T.standalone()
ok(len(sa) == 18,
   'alv_tree counts 18 standalone templates, the four of them included',
   len(sa))
for p in (SIGN, DONE, CLOSED, STYLES):
''',
         r'''
sa = T.standalone()
# RA19, 23 Nov 2026 - 22 (was 18): the Acquisitions offer-brief PDF and its three
# partials (_style, _tabs, _run_modal), fragments included into pages that
# already extend base. test_ra19_acquisitions_screens.py checks the three
# partials use house tokens only, since the colour censuses skip them.
ok(len(sa) == 22,
   'alv_tree counts 22 standalone templates, the four of them included',
   len(sa))
for p in (SIGN, DONE, CLOSED, STYLES):
'''),
    ]),
    (os.path.join('test_drift_root.py'), [
        (r'''                   'crs/submission_list.html')
CRS_N = 8
N_FOOTER_SUBSTRING, N_FOOTER_TOKEN = 94, 93   # RA16, 23 Nov 2026 - the planner's Send dialog brings one .modal-footer. Both matchers rise by the same one.   # (was 93, 92)   # GL-3, 29 Oct 2026 - the Greek Details pop-up brings one .modal-footer to Tenant Edit and one to Tenant Add. Both matchers rise by the same two.   # (was 91, 90)   # CR-2, 27 Oct 2026 - the receipt email pop-up brings one .modal-footer to Receipts and one to Receipt Details. Both matchers rise by the same two.   # (was N_FOOTER_SUBSTRING, N_FOOTER_TOKEN = 89, 88)   # CP-2, 21 Oct 2026 - three dialogs leave the planner and two arrive, so one .modal-footer wrapper goes. BOTH matchers fall by the same one, which is what an ordinary wrapper does and is the point of keeping the pair.   # (was 90, 89)   # RD-1 and RD-2, 19 Oct 2026 - the recipe quick-look dialog and the Move dialog each bring one .modal-footer. BOTH matchers rise by the same 2, which is what an ordinary wrapper does.   # (was 88, 87)   # MO-1, 19 Oct 2026 - two more dialogs on the planner - a planned night, and leftovers. Both matchers rise by the same 2, which is what an ordinary wrapper does.   # (was 86, 85)   # MW-1, 19 Oct 2026 - the planner gains three dialogs - copy a week, save a Menu, apply a Menu - and each brings one .modal-footer. Both matchers rise by the same 3, which is what an ordinary wrapper does.   # (was 83, 82)   # RT-1, 18 Oct 2026 - six .modal-footer wrappers went with the four meal-plan screens MN-1 retired, and the planner brought none. BOTH matchers fall by the same six, which is the point of keeping the pair: the wrappers that left were ordinary ones.   # (was 89, 88)   # CC-2, 17 Oct 2026 - the contact detail modal adds one .modal-footer. Both matchers rise by the same one.   # (was 88, 87)   # CC-1, 15 Oct 2026 - the celebration day sheet adds one .modal-footer. Both matchers rise by the same one.   # (was 87, 86)   # PV-1, 15 Oct 2026 - two hand-rolled invoice viewers went, and each took one .modal-footer wrapper with it. Both matchers fall by the same two, which is itself the point: the wrappers that left were ordinary ones.   # (was 89, 88)
GREY = 'rgb(233, 236, 239)'
GREY_INK = 'rgb(138, 151, 157)'
''',
         r'''                   'crs/submission_list.html')
CRS_N = 8
N_FOOTER_SUBSTRING, N_FOOTER_TOKEN = 98, 97   # RA19, 23 Nov 2026 - the Acquisitions pop-ups (Run search, Shortlist/Reject, Log a viewing, the rule editor) bring one .modal-footer each. Both matchers rise by the same four.   # (was 94, 93)   # RA16, 23 Nov 2026 - the planner's Send dialog brings one .modal-footer. Both matchers rise by the same one.   # (was 93, 92)   # GL-3, 29 Oct 2026 - the Greek Details pop-up brings one .modal-footer to Tenant Edit and one to Tenant Add. Both matchers rise by the same two.   # (was 91, 90)   # CR-2, 27 Oct 2026 - the receipt email pop-up brings one .modal-footer to Receipts and one to Receipt Details. Both matchers rise by the same two.   # (was N_FOOTER_SUBSTRING, N_FOOTER_TOKEN = 89, 88)   # CP-2, 21 Oct 2026 - three dialogs leave the planner and two arrive, so one .modal-footer wrapper goes. BOTH matchers fall by the same one, which is what an ordinary wrapper does and is the point of keeping the pair.   # (was 90, 89)   # RD-1 and RD-2, 19 Oct 2026 - the recipe quick-look dialog and the Move dialog each bring one .modal-footer. BOTH matchers rise by the same 2, which is what an ordinary wrapper does.   # (was 88, 87)   # MO-1, 19 Oct 2026 - two more dialogs on the planner - a planned night, and leftovers. Both matchers rise by the same 2, which is what an ordinary wrapper does.   # (was 86, 85)   # MW-1, 19 Oct 2026 - the planner gains three dialogs - copy a week, save a Menu, apply a Menu - and each brings one .modal-footer. Both matchers rise by the same 3, which is what an ordinary wrapper does.   # (was 83, 82)   # RT-1, 18 Oct 2026 - six .modal-footer wrappers went with the four meal-plan screens MN-1 retired, and the planner brought none. BOTH matchers fall by the same six, which is the point of keeping the pair: the wrappers that left were ordinary ones.   # (was 89, 88)   # CC-2, 17 Oct 2026 - the contact detail modal adds one .modal-footer. Both matchers rise by the same one.   # (was 88, 87)   # CC-1, 15 Oct 2026 - the celebration day sheet adds one .modal-footer. Both matchers rise by the same one.   # (was 87, 86)   # PV-1, 15 Oct 2026 - two hand-rolled invoice viewers went, and each took one .modal-footer wrapper with it. Both matchers fall by the same two, which is itself the point: the wrappers that left were ordinary ones.   # (was 89, 88)
GREY = 'rgb(233, 236, 239)'
GREY_INK = 'rgb(138, 151, 157)'
'''),
        (r'''for n in RELEASED:
    check('  %s is still here' % n, os.path.isfile(os.path.join(ROOT, n)))
check('  and the CRS root really is a second template root',
      len(alv_tree.roots()) == 2, '%d root(s)' % len(alv_tree.roots()))
crs = [alv_tree.rel(p) for p in alv_tree.templates()
       if alv_tree.rel(p).startswith('crs/')]
''',
         r'''for n in RELEASED:
    check('  %s is still here' % n, os.path.isfile(os.path.join(ROOT, n)))
# RA19, 23 Nov 2026 - three roots (was 2): Acquisitions keeps its templates
# in acquisitions/templates, as CRS does. CRS is still one of them.
check('  and the CRS root really is a template root of its own',
      len(alv_tree.roots()) == 3 and any(
          os.sep + 'crs' + os.sep in r + os.sep for r in alv_tree.roots()), '%d root(s)' % len(alv_tree.roots()))
crs = [alv_tree.rel(p) for p in alv_tree.templates()
       if alv_tree.rel(p).startswith('crs/')]
'''),
    ]),
    (os.path.join('test_crs_detail_rest.py'), [
        (r'''
# THE THING THAT STARTED IT.
ok(len(alv_tree.roots()) == 2,
   'CONTROL: and the module is still in the second root, which is where '
   'no gate could see it eleven rounds ago',
   [os.path.basename(os.path.dirname(r)) + '/' + os.path.basename(r)
''',
         r'''
# THE THING THAT STARTED IT.
# RA19, 23 Nov 2026 - three roots (was 2): Acquisitions has its own, as CRS does.
ok(len(alv_tree.roots()) == 3,
   'CONTROL: and the module is still in a root of its own, which is where '
   'no gate could see it eleven rounds ago',
   [os.path.basename(os.path.dirname(r)) + '/' + os.path.basename(r)
'''),
    ]),
    (os.path.join('test_help_label.py'), [
        (r'''        '<span class="action-back-label"> Help</span>')
BARE = '<i class="fas fa-question-circle"></i> Help'
LABELS_TOTAL = 135   # RA15, 23 Nov 2026 - user_activity.html, the Activity page, an ordinary pages/templates page that joins every tree-wide count: a Back.   # (was 134)   # CG-1, 13 Nov 2026 - celebration_gifts.html, the My gifts page, an ordinary pages/templates page with a Back.   # (was 133)   # GL-1, 28 Oct 2026 - company_details.html, the Company Details screen, an ordinary pages/templates page that joins every tree-wide count. A house Back, so one more label.   # (was 132)   # ES-7, 25 Oct 2026 - house_marks.html, the Signature and Stamp screen, an ordinary pages/templates page that joins every tree-wide count. A house Back, so one more label.   # (was 131)   # ES-6, 25 Oct 2026 - lease_signing_detail.html, the envelope page. A new PAGE with a house Back, so the tree-wide count moves by exactly one.   # (was 130)   # ES-3b, 24 Oct 2026 - the Send for Signature screen. A new PAGE with a house Back, which carries the label span base hides on a phone, so the tree-wide count moves by exactly one.   # (was 129)   # ES-3a, 23 Oct 2026 - lease_signing_list.html, the envelope register. An ordinary pages/templates page, so it joins every tree-wide count.   # (was 128)   # RV-1, 23 Oct 2026 - the Receipt Details Back. A new PAGE, and a house Back carries the label span base hides on a phone, so the tree-wide count moves by exactly one.   # (was 127)   # PP-1, 20 Oct 2026 - the printable plan's Back. It wore .action-secondary in the first draft and five suites objected; wearing the house class means carrying the house label span, which base hides on a phone so the control becomes a square icon.   # (was 126)   # RT-1, 18 Oct 2026 - three Back labels went with the four meal-plan screens MN-1 retired, and the planner brought none   # (was 129)   # PJ-1, 15 Oct 2026 - the same duplicate Back, counted by its label span. The check below it compares the backup and so falls by one with it.   # (was 130)   # DB-5, 12 Oct 2026 - the dashboard Back gains the house label   # (was 129)   # AFTER this round. 130 before - the Help one.
HELP_TOTAL = 48   # RA15, 23 Nov 2026 - user_activity.html, the Activity page, an ordinary pages/templates page that joins every tree-wide count: Help, bare text like its siblings.   # (was 47)   # CX-1, 29 Oct 2026 - Task List and Gantt Chart gain Help, bare text like their siblings   # (was 45)   # HK-4, 28 Oct 2026 - Project Details gains Help, his finding; bare text like its siblings   # (was 44)   # ES-8, 25 Oct 2026 - the Lease Signing register gains its own Help, his request; a bare-text Help secondary like its siblings.   # (was 43)   # RT-1, 18 Oct 2026 - three of MH-1 five Help buttons went with the screens they sat on. The guide is unchanged and still reached from the planner and the shopping list.   # (was 46)   # MH-1, 18 Oct 2026 - the five meal-plan screens, which had no Help control at all   # (was 41)   # DB-5, 12 Oct 2026 - and a Help secondary joins the bar   # (was 40)
# The shape 77 pages carried before D7 removed every one of them.
UNSCOPED = '.action-back-label { display: none; }'
''',
         r'''        '<span class="action-back-label"> Help</span>')
BARE = '<i class="fas fa-question-circle"></i> Help'
LABELS_TOTAL = 144   # RA19, 23 Nov 2026 - the Acquisitions screens, in a template root of their own that every tree-wide count walks: a Back on nine of them (the Overview is the module's top and has none).   # (was 135)   # RA15, 23 Nov 2026 - user_activity.html, the Activity page, an ordinary pages/templates page that joins every tree-wide count: a Back.   # (was 134)   # CG-1, 13 Nov 2026 - celebration_gifts.html, the My gifts page, an ordinary pages/templates page with a Back.   # (was 133)   # GL-1, 28 Oct 2026 - company_details.html, the Company Details screen, an ordinary pages/templates page that joins every tree-wide count. A house Back, so one more label.   # (was 132)   # ES-7, 25 Oct 2026 - house_marks.html, the Signature and Stamp screen, an ordinary pages/templates page that joins every tree-wide count. A house Back, so one more label.   # (was 131)   # ES-6, 25 Oct 2026 - lease_signing_detail.html, the envelope page. A new PAGE with a house Back, so the tree-wide count moves by exactly one.   # (was 130)   # ES-3b, 24 Oct 2026 - the Send for Signature screen. A new PAGE with a house Back, which carries the label span base hides on a phone, so the tree-wide count moves by exactly one.   # (was 129)   # ES-3a, 23 Oct 2026 - lease_signing_list.html, the envelope register. An ordinary pages/templates page, so it joins every tree-wide count.   # (was 128)   # RV-1, 23 Oct 2026 - the Receipt Details Back. A new PAGE, and a house Back carries the label span base hides on a phone, so the tree-wide count moves by exactly one.   # (was 127)   # PP-1, 20 Oct 2026 - the printable plan's Back. It wore .action-secondary in the first draft and five suites objected; wearing the house class means carrying the house label span, which base hides on a phone so the control becomes a square icon.   # (was 126)   # RT-1, 18 Oct 2026 - three Back labels went with the four meal-plan screens MN-1 retired, and the planner brought none   # (was 129)   # PJ-1, 15 Oct 2026 - the same duplicate Back, counted by its label span. The check below it compares the backup and so falls by one with it.   # (was 130)   # DB-5, 12 Oct 2026 - the dashboard Back gains the house label   # (was 129)   # AFTER this round. 130 before - the Help one.
HELP_TOTAL = 58   # RA19, 23 Nov 2026 - the ten Acquisitions screens, each with Help, bare text like its siblings (the More menu's copy is not counted).   # (was 48)   # RA15, 23 Nov 2026 - user_activity.html, the Activity page, an ordinary pages/templates page that joins every tree-wide count: Help, bare text like its siblings.   # (was 47)   # CX-1, 29 Oct 2026 - Task List and Gantt Chart gain Help, bare text like their siblings   # (was 45)   # HK-4, 28 Oct 2026 - Project Details gains Help, his finding; bare text like its siblings   # (was 44)   # ES-8, 25 Oct 2026 - the Lease Signing register gains its own Help, his request; a bare-text Help secondary like its siblings.   # (was 43)   # RT-1, 18 Oct 2026 - three of MH-1 five Help buttons went with the screens they sat on. The guide is unchanged and still reached from the planner and the shopping list.   # (was 46)   # MH-1, 18 Oct 2026 - the five meal-plan screens, which had no Help control at all   # (was 41)   # DB-5, 12 Oct 2026 - and a Help secondary joins the bar   # (was 40)
# The shape 77 pages carried before D7 removed every one of them.
UNSCOPED = '.action-back-label { display: none; }'
'''),
    ]),
    (os.path.join('test_house_title.py'), [
        (r'''# keeping the two honest" had been disagreeing for three days. Both
# say 122 now.
ok(len(wearers) == 129,   # RA15, 23 Nov 2026 - user_activity.html, the Activity page, an ordinary pages/templates page that joins every tree-wide count. Wears the house title pair.   # (was 128)   # CG-1, 13 Nov 2026 - celebration_gifts.html, the My gifts page with the Christmas list, an ordinary pages/templates page that joins every tree-wide count. Wears the house title pair.   # (was 127)   # GL-1, 28 Oct 2026 - company_details.html, the Company Details screen, an ordinary pages/templates page that joins every tree-wide count. Wears the house title pair.   # (was 126)   # ES-7, 25 Oct 2026 - house_marks.html, the Signature and Stamp screen, an ordinary pages/templates page that joins every tree-wide count. Wears the house title pair.   # (was 125)   # ES-6, 25 Oct 2026 - lease_signing_detail.html, the envelope page, an ordinary pages/templates page that joins every tree-wide count. Wears the house title pair.   # (was 124)   # ES-3b, 24 Oct 2026 - lease_signing_create.html, the Send for Signature screen, wears the house title pair.   # (was 123)   # ES-3a, 23 Oct 2026 - lease_signing_list.html wears the house title pair.   # (was 122)
   '122 templates now wear the class, which is the number base\'s note '
   'states', len(wearers))
''',
         r'''# keeping the two honest" had been disagreeing for three days. Both
# say 122 now.
ok(len(wearers) == 139,   # RA19, 23 Nov 2026 - the ten Acquisitions screens, in a template root of their own that every tree-wide count walks. Each wears the house title.   # (was 129)   # RA15, 23 Nov 2026 - user_activity.html, the Activity page, an ordinary pages/templates page that joins every tree-wide count. Wears the house title pair.   # (was 128)   # CG-1, 13 Nov 2026 - celebration_gifts.html, the My gifts page with the Christmas list, an ordinary pages/templates page that joins every tree-wide count. Wears the house title pair.   # (was 127)   # GL-1, 28 Oct 2026 - company_details.html, the Company Details screen, an ordinary pages/templates page that joins every tree-wide count. Wears the house title pair.   # (was 126)   # ES-7, 25 Oct 2026 - house_marks.html, the Signature and Stamp screen, an ordinary pages/templates page that joins every tree-wide count. Wears the house title pair.   # (was 125)   # ES-6, 25 Oct 2026 - lease_signing_detail.html, the envelope page, an ordinary pages/templates page that joins every tree-wide count. Wears the house title pair.   # (was 124)   # ES-3b, 24 Oct 2026 - lease_signing_create.html, the Send for Signature screen, wears the house title pair.   # (was 123)   # ES-3a, 23 Oct 2026 - lease_signing_list.html wears the house title pair.   # (was 122)
   '122 templates now wear the class, which is the number base\'s note '
   'states', len(wearers))
'''),
    ]),
    (os.path.join('test_save_and_cancel.py'), [
        (r'''    # inside a .modal-footer.
    'user_edit.html': 'it dismisses a dialog',
}

''',
         r'''    # inside a .modal-footer.
    'user_edit.html': 'it dismisses a dialog',
    # RA19, 23 Nov 2026 - the Acquisitions scenario editor. Its Cancel
    # closes the rule editor pop-up (data-dismiss="modal" in a
    # .modal-footer); the screen itself has only Save and Back.
    'scenario_edit.html': 'it dismisses a dialog',
}

'''),
    ]),
    (os.path.join('test_req_marker.py'), [
        (r'''        '#alv-owned-from is emitted by Django\'s json_script filter at '
        'render time, and the read is inside a try/catch',
}
suspects = []
''',
         r'''        '#alv-owned-from is emitted by Django\'s json_script filter at '
        'render time, and the read is inside a try/catch',
    # RA19, 23 Nov 2026 - the same data island again: the Acquisitions
    # scenario editor's rules arrive by json_script, read inside a try.
    'acquisitions/scenario_edit.html':
        '#acqRowsData is emitted by Django\'s json_script filter at '
        'render time, and the read is inside a try/catch',
}
suspects = []
'''),
    ]),
    (os.path.join('test_radius_token.py'), [
        (r'''# standalone check above asks whether a page DECLARES the token rather
# than naming pages that may not use it.
N_ADDED = 3
N_TOTAL = N_RADIUS + N_PRE - N_RETIRED + N_ADDED
N_STYLE, N_ATTR, N_SCRIPT = 158, 4, 9   # ES-4, 24 Oct 2026 - three in the public signing pages' own stylesheet. They DECLARE the token as well as using it, which is why the standalone check above now asks whether a page declares it rather than naming pages.   # (was 156, 4, 9)   # PP-1, 20 Oct 2026 - the printable plan's .pp-week   # (was 155, 4, 9)   # RT-1, 18 Oct 2026 - one <style> rule and two style attributes went with the retired screens   # (was 156, 6, 9)
N_CHIP, N_CHIP_PAGES = 5, 4

''',
         r'''# standalone check above asks whether a page DECLARES the token rather
# than naming pages that may not use it.
# RA19, 23 Nov 2026 - AND ONE MORE: the Acquisitions module's shared
# stylesheet (acquisitions/_style.html) rounds its cards with the house
# token. A page that extends base, so the token resolves.
N_ADDED = 4
N_TOTAL = N_RADIUS + N_PRE - N_RETIRED + N_ADDED
N_STYLE, N_ATTR, N_SCRIPT = 159, 4, 9   # RA19, 23 Nov 2026 - one in the Acquisitions stylesheet's <style>.   # (was 158, 4, 9)   # ES-4, 24 Oct 2026 - three in the public signing pages' own stylesheet. They DECLARE the token as well as using it, which is why the standalone check above now asks whether a page declares it rather than naming pages.   # (was 156, 4, 9)   # PP-1, 20 Oct 2026 - the printable plan's .pp-week   # (was 155, 4, 9)   # RT-1, 18 Oct 2026 - one <style> rule and two style attributes went with the retired screens   # (was 156, 6, 9)
N_CHIP, N_CHIP_PAGES = 5, 4

'''),
    ]),
    (os.path.join('test_subtree_tones.py'), [
        (r'''# RA15, 23 Nov 2026 - user_activity.html, the Activity page, joins both
# counts (was 163 and 137).
ok(len(tree) == 164, 'a WALK finds 164 templates', len(tree))
ok(len(top) == 138, '  a flat listing finds 138 - 120 was what H7 '
   'counted, 122 after MN-1, and RD-1 adds the quick-look pair',
   len(top))
ok(len(sub) == 26, '  so 26 live in subdirectories and H7 never saw them',
   len(sub))
folders = sorted({rel.split('/')[0] for rel, _ in sub})
ok(len(folders) == 7, '  across %d folders: %s' % (len(folders),
                                                   ', '.join(folders)),
   folders)
''',
         r'''# RA15, 23 Nov 2026 - user_activity.html, the Activity page, joins both
# counts (was 163 and 137).
# RA19, 23 Nov 2026 - the Acquisitions templates, 14 of them in a root of
# their own, all in its acquisitions/ folder (was 164, 26 and 7 folders).
ok(len(tree) == 178, 'a WALK finds 178 templates', len(tree))
ok(len(top) == 138, '  a flat listing finds 138 - 120 was what H7 '
   'counted, 122 after MN-1, and RD-1 adds the quick-look pair',
   len(top))
ok(len(sub) == 40, '  so 40 live in subdirectories and H7 never saw them',
   len(sub))
folders = sorted({rel.split('/')[0] for rel, _ in sub})
ok(len(folders) == 8, '  across %d folders: %s' % (len(folders),
                                                   ', '.join(folders)),
   folders)
'''),
    ]),
    (os.path.join('test_colour_census.py'), [
        (r'''
CEILING = {
    'act_expense.html': 26,
    'admin_apms.html': 1,
''',
         r'''
CEILING = {
    # RA19, 23 Nov 2026 - the Acquisitions offer brief: a PDF body handed to
    # xhtml2pdf, standalone like recipe_pdf, so it cannot read a token and
    # carries its colours itself.
    'acquisitions/offer_brief.html': 11,
    'act_expense.html': 26,
    'admin_apms.html': 1,
'''),
    ]),
    (os.path.join('test_recipe_side_b.py'), [
        (r'''# shipped decisions instead of ten. The refusal gets stronger, not
# weaker, which is why this count is read and not frozen.
N_NAV_RULE_HITS, N_NAV_RULE_PRIMARY = 13, 11   # CG-1, 13 Nov 2026 - the My gifts bar on the Christmas tab: its only non-Back item is a link, Shopping list to me, and it ships as .action-primary.   # (was 12, 10)   # PP-1, 20 Oct 2026 - the planner leaves the set. The rule needs a bar whose only non-Back item is a link, and the planner bar now holds Print as well as Shopping List.   # (was 13, 11)   # (was 12, 10)
N_COND_LABEL, N_COND_LABEL_PRIMARY = 11, 7   # CX-1, 29 Oct 2026 - Help on the Task List, which reads Greek or English like its neighbours, a secondary   # (was 10, 7)   # CR-2, 27 Oct 2026 - Email again / Email receipt on Receipt Details, a secondary  # (was 9, 7)

# Buttons the scan cannot see at all: no Bootstrap colour it LISTS, no
''',
         r'''# shipped decisions instead of ten. The refusal gets stronger, not
# weaker, which is why this count is read and not frozen.
N_NAV_RULE_HITS, N_NAV_RULE_PRIMARY = 14, 12   # RA19, 23 Nov 2026 - the Acquisitions Scenarios bar: its only non-Back, non-Help item is a link, New scenario, and it ships as .action-primary.   # (was 13, 11)   # CG-1, 13 Nov 2026 - the My gifts bar on the Christmas tab: its only non-Back item is a link, Shopping list to me, and it ships as .action-primary.   # (was 12, 10)   # PP-1, 20 Oct 2026 - the planner leaves the set. The rule needs a bar whose only non-Back item is a link, and the planner bar now holds Print as well as Shopping List.   # (was 13, 11)   # (was 12, 10)
N_COND_LABEL, N_COND_LABEL_PRIMARY = 12, 7   # RA19, 23 Nov 2026 - Pause / Resume on an Acquisitions scenario, which reads one or the other by the scenario's state, a secondary.   # (was 11, 7)   # CX-1, 29 Oct 2026 - Help on the Task List, which reads Greek or English like its neighbours, a secondary   # (was 10, 7)   # CR-2, 27 Oct 2026 - Email again / Email receipt on Receipt Details, a secondary  # (was 9, 7)

# Buttons the scan cannot see at all: no Bootstrap colour it LISTS, no
'''),
    ]),
    (os.path.join('test_recipe_tones.py'), [
        (r'''# carry action-primary the same way. A count keyed on the exact class
# string undercounts every page that added a hook of its own.
SWEPT_CANCELS, SWEPT_DANGER, SWEPT_PRIMARY = 59, 14, 34   # GL-3, 29 Oct 2026 - the Greek Details pop-up on Tenant Edit and on Tenant Add: a Cancel and a Done each.   # (was 57, 14, 32)   # CR-2, 27 Oct 2026 - the receipt email pop-up on Receipts and on Receipt Details: a Cancel and a Send each.   # (was 55, 14, 30)   # PV-1, 15 Oct 2026 - two hand-rolled invoice viewers retired, each with a Close and a Download. The danger count is unchanged: neither had a destructive button in it.   # (was 57, 14, 32)
CONVERTED_NOW, WAITING_NOW, CEILING_NOW, ALIAS_NOW = 73, 2, 38, 57

''',
         r'''# carry action-primary the same way. A count keyed on the exact class
# string undercounts every page that added a hook of its own.
SWEPT_CANCELS, SWEPT_DANGER, SWEPT_PRIMARY = 63, 14, 37   # RA19, 23 Nov 2026 - the Acquisitions pop-ups: a dismiss button in each of the four (Close on Run search, Cancel on the rest), and a primary in three - Save the decision, Log the viewing, Save the rule.   # (was 59, 14, 34)   # GL-3, 29 Oct 2026 - the Greek Details pop-up on Tenant Edit and on Tenant Add: a Cancel and a Done each.   # (was 57, 14, 32)   # CR-2, 27 Oct 2026 - the receipt email pop-up on Receipts and on Receipt Details: a Cancel and a Send each.   # (was 55, 14, 30)   # PV-1, 15 Oct 2026 - two hand-rolled invoice viewers retired, each with a Close and a Download. The danger count is unchanged: neither had a destructive button in it.   # (was 57, 14, 32)
CONVERTED_NOW, WAITING_NOW, CEILING_NOW, ALIAS_NOW = 73, 2, 38, 57

'''),
    ]),
    (os.path.join('test_panel_title.py'), [
        (r'''

mine, debt = [], []
for rel, src in ALL:
    used = classes_used(src)
    pres = interpolated_prefixes(src)
    scripts = ' '.join(re.findall(r'<script[^>]*>(.*?)</script>', src, re.S))
    jsnames, jspres = script_names(src)
    for name, sels in sorted(classes_styled(src).items()):
        if name in used or name in classes_used(BASE_SRC):
''',
         r'''

# A SHARED STYLE PARTIAL IS WORN BY THE PAGES THAT INCLUDE IT - RA19,
# 23 Nov 2026. This scan judges each file alone, so a partial that is
# only a <style> block - acquisitions/_style.html, included by every
# Acquisitions page - wears none of its own classes and every rule in it
# read as an orphan: 49 of them, all worn. So a partial also counts what
# its includers wear: their markup, their script-built names, their
# interpolated prefixes. A class no includer wears is still an orphan.
INCLUDE = re.compile(r'\{%\s*include\s+["\']([^"\']+)["\']')
WORN_BY, PRES_BY, JS_BY = {}, {}, {}
for _rel, _src in ALL:
    for _inc in INCLUDE.findall(_src):
        WORN_BY.setdefault(_inc, set()).update(classes_used(_src))
        PRES_BY.setdefault(_inc, []).extend(interpolated_prefixes(_src))
        _n, _p = script_names(_src)
        JS_BY.setdefault(_inc, [set(), []])
        JS_BY[_inc][0].update(_n)
        JS_BY[_inc][1].extend(_p)
        JS_BY[_inc].append(' '.join(re.findall(
            r'<script[^>]*>(.*?)</script>', _src, re.S)))

mine, debt = [], []
for rel, src in ALL:
    key = rel.replace(os.sep, '/')
    used = classes_used(src) | WORN_BY.get(key, set())
    pres = interpolated_prefixes(src) + PRES_BY.get(key, [])
    scripts = ' '.join([' '.join(re.findall(r'<script[^>]*>(.*?)</script>',
                                            src, re.S))]
                       + JS_BY.get(key, [None, None])[2:])
    jsnames, jspres = script_names(src)
    if key in JS_BY:
        jsnames = set(jsnames) | JS_BY[key][0]
        jspres = list(jspres) + JS_BY[key][1]
    for name, sels in sorted(classes_styled(src).items()):
        if name in used or name in classes_used(BASE_SRC):
'''),
    ]),
    (os.path.join('test_heading_prefix.py'), [
        (r'''# this one is really about - "do not inherit the tab" is a statement
# about where the title comes from, not a complaint.
check('  the standalone set is small and known', len(_alone) <= 16,
      '%d' % len(_alone))

''',
         r'''# this one is really about - "do not inherit the tab" is a statement
# about where the title comes from, not a complaint.
# RA19, 23 Nov 2026 - 16 -> 20. Acquisitions adds four: its offer-brief
# PDF body, which never reaches a browser tab, and three partials
# included into pages that do extend base and so inherit its tab.
check('  the standalone set is small and known', len(_alone) <= 20,
      '%d' % len(_alone))

'''),
    ]),
    (os.path.join('test_heading_standard.py'), [
        (r'''    'map_view.html',                         # the map page
    'tenant_payment_days.html',    # tenant payment behaviour
    # LS-1, 27 Oct 2026 - Lease Signing Status wears the same report head
    # as Payment Behaviour (.alv-report-title), so it sits beside it.
''',
         r'''    'map_view.html',                         # the map page
    'tenant_payment_days.html',    # tenant payment behaviour
    # RA19, 23 Nov 2026 - the Acquisitions offer brief is a PDF body handed
    # to xhtml2pdf: it heads a sheet of paper, not a screen, so the screen
    # heading standard does not reach it.
    'acquisitions/offer_brief.html',
    # LS-1, 27 Oct 2026 - Lease Signing Status wears the same report head
    # as Payment Behaviour (.alv-report-title), so it sits beside it.
'''),
    ]),
    (os.path.join('test_pair_contrast.py'), [
        (r'''MARK = 'B-4b, 8 Oct 2026'

EXPECT_PAIRS = 761   # RA16, 23 Nov 2026 - meal_planner.html: the picker's eye, the Undo strip after a dropped meal and the Send dialog's preview each set a fill and an ink, all AA.   # (was 758)   # RA15, 23 Nov 2026 - user_activity.html, the Activity page: its tabs, the usage grid's four shades and its pill each set a fill and an ink, all AA.   # (was 752)   # RC-3, 12 Nov 2026 - cook mode on the recipe page: the full-screen step view sets the paper fill and its ink, and its Next button the accent fill and the on-accent ink. Two rules, pairs base already uses.   # (was 750)   # CR-2, 27 Oct 2026 - the receipt email pop-up, on Receipts and on Receipt Details: the message box and the Printed warning each set a fill and its ink, pairs base already uses.   # (was 746)   # ES-11, 26 Oct 2026 - the yellow signed-leases bar left Home and Notifications, and with it .lsa-strip's fill+ink pair on each page.   # (was 748)   # ES-9, 26 Oct 2026 - Home's Waiting for you icon chip, .ins-ic--wait, sets the warn-soft fill and warn-ink together, a pair base already uses.   # (was 747)   # ES-7, 25 Oct 2026 - two notes set a fill and an ink together: .hm-note on the Signature and Stamp screen and .ls-saved-note on the signing page, both on the accent pair this table already knows.   # (was 745)   # ES-6, 25 Oct 2026 - three more rules in ES-6's pages set a fill and an ink together, measured by this census on the full tree.   # (was 742)   # ES-4, 24 Oct 2026 - eleven in the public signing pages' own stylesheet. A standalone page cannot inherit a surface, so every one it draws sets both halves of the pair itself - which is exactly why this census asks about them.   # (was 731)   # ES-3a, 23 Oct 2026 - the lease signing register: three signer dots mirroring the good, bad and neutral pills, and the waiting-on-you note. Four rules, no new pairings.   # (was 727)   # MN-2, 21 Oct 2026 - the Saved Menus dialog gains the preset row CP-2 built for Copy, and .mn-preset[aria-pressed=true] sets a fill and an ink together exactly as .cp-preset does. One more pair, of tokens this table already knows.   # (was 726)   # RG-2, 21 Oct 2026 - two more rules set a fill and an ink together: the date field, which wears the paper token on the ink one like every other field in the system, and the line explaining the second Print press, which sits on the surface wash.   # (was 724)   # RG-1, 21 Oct 2026 - the printed sheet is drawn again from four layouts, and five more of its rules set a fill and an ink together: the pill in its three states, the today marker and the dimmed cell. Every one is a token pair this table already knows.   # (was 719)   # PP-1, 20 Oct 2026 - the printable plan sets
# both a ground and an ink on six rules. All house pairs off base's
# own tokens, so the AA table below is untouched and the gross count
''',
         r'''MARK = 'B-4b, 8 Oct 2026'

EXPECT_PAIRS = 770   # RA19, 23 Nov 2026 - the Acquisitions stylesheet: nine rules set a fill and an ink together, every pair on house tokens and none below AA (the table of named pairs is unchanged).   # (was 761)   # RA16, 23 Nov 2026 - meal_planner.html: the picker's eye, the Undo strip after a dropped meal and the Send dialog's preview each set a fill and an ink, all AA.   # (was 758)   # RA15, 23 Nov 2026 - user_activity.html, the Activity page: its tabs, the usage grid's four shades and its pill each set a fill and an ink, all AA.   # (was 752)   # RC-3, 12 Nov 2026 - cook mode on the recipe page: the full-screen step view sets the paper fill and its ink, and its Next button the accent fill and the on-accent ink. Two rules, pairs base already uses.   # (was 750)   # CR-2, 27 Oct 2026 - the receipt email pop-up, on Receipts and on Receipt Details: the message box and the Printed warning each set a fill and its ink, pairs base already uses.   # (was 746)   # ES-11, 26 Oct 2026 - the yellow signed-leases bar left Home and Notifications, and with it .lsa-strip's fill+ink pair on each page.   # (was 748)   # ES-9, 26 Oct 2026 - Home's Waiting for you icon chip, .ins-ic--wait, sets the warn-soft fill and warn-ink together, a pair base already uses.   # (was 747)   # ES-7, 25 Oct 2026 - two notes set a fill and an ink together: .hm-note on the Signature and Stamp screen and .ls-saved-note on the signing page, both on the accent pair this table already knows.   # (was 745)   # ES-6, 25 Oct 2026 - three more rules in ES-6's pages set a fill and an ink together, measured by this census on the full tree.   # (was 742)   # ES-4, 24 Oct 2026 - eleven in the public signing pages' own stylesheet. A standalone page cannot inherit a surface, so every one it draws sets both halves of the pair itself - which is exactly why this census asks about them.   # (was 731)   # ES-3a, 23 Oct 2026 - the lease signing register: three signer dots mirroring the good, bad and neutral pills, and the waiting-on-you note. Four rules, no new pairings.   # (was 727)   # MN-2, 21 Oct 2026 - the Saved Menus dialog gains the preset row CP-2 built for Copy, and .mn-preset[aria-pressed=true] sets a fill and an ink together exactly as .cp-preset does. One more pair, of tokens this table already knows.   # (was 726)   # RG-2, 21 Oct 2026 - two more rules set a fill and an ink together: the date field, which wears the paper token on the ink one like every other field in the system, and the line explaining the second Print press, which sits on the surface wash.   # (was 724)   # RG-1, 21 Oct 2026 - the printed sheet is drawn again from four layouts, and five more of its rules set a fill and an ink together: the pill in its three states, the today marker and the dimmed cell. Every one is a token pair this table already knows.   # (was 719)   # PP-1, 20 Oct 2026 - the printable plan sets
# both a ground and an ink on six rules. All house pairs off base's
# own tokens, so the AA table below is untouched and the gross count
'''),
    ]),
    (os.path.join('test_tree_roots.py'), [
        (r'''               # the partial and its shell. (was 140)   # RT-1, 18 Oct 2026 - MN-1 retired four meal-plan screens and the planner replaced them: 143 - 4 + 1. This is the shape of the tree, which is what this file is for.   # (was 143)
CRS_N = 8
TOTAL_N = MAIN_N + CRS_N

CRS_PAGES = [
''',
         r'''               # the partial and its shell. (was 140)   # RT-1, 18 Oct 2026 - MN-1 retired four meal-plan screens and the planner replaced them: 143 - 4 + 1. This is the shape of the tree, which is what this file is for.   # (was 143)
CRS_N = 8
# RA19, 23 Nov 2026 - A THIRD ROOT: acquisitions/templates, the Property
# Acquisitions app, kept beside its code the way CRS is. Fourteen
# templates, every basename distinct from the other two roots.
ACQ_N = 14
TOTAL_N = MAIN_N + CRS_N + ACQ_N

CRS_PAGES = [
'''),
        (r'''# ==========================================================================
rts = alv_tree.roots()
ok(len(rts) == 2, 'alv_tree knows 2 roots', [alv_tree.rel(r) or r for r in rts])
for parts, why in alv_tree.TEMPLATE_ROOTS:
    p = os.path.join(ROOT, *parts)
''',
         r'''# ==========================================================================
rts = alv_tree.roots()
ok(len(rts) == 3, 'alv_tree knows 3 roots', [alv_tree.rel(r) or r for r in rts])
for parts, why in alv_tree.TEMPLATE_ROOTS:
    p = os.path.join(ROOT, *parts)
'''),
    ]),
    (os.path.join('test_label_weight.py'), [
        (r'''N_PART = 2                 # of those, the ones with a hint after the name
N_RULES = 22               # whole .form-group label rules removed
N_HINT = 69                # labels that bold only part of themselves
N_HINT_WAS = 67            # ... 67 before this round added two

CRS_PAGES = ('crs/country_form.html', 'crs/fi_form.html',
''',
         r'''N_PART = 2                 # of those, the ones with a hint after the name
N_RULES = 22               # whole .form-group label rules removed
# RA19, 23 Nov 2026 - SIX MORE OF THE SHAPE, on new Acquisitions pages: Purpose,
# Values, Bands instead, The rule in plain words, Group, and Why in a few
# words - each a bold name and a plain hint. A new page has no backup of
# this round, so it counts on both sides (was 69 and 67).
N_HINT = 75                # labels that bold only part of themselves
N_HINT_WAS = 73            # ... 73 before this round added two

CRS_PAGES = ('crs/country_form.html', 'crs/fi_form.html',
'''),
    ]),
    (os.path.join('test_retired.py'), [
        (r'''    # censuses.
    'test_dr2_values.py',
    'test_entry_sections.py', 'test_js_escape.py', 'test_label_weight.py',
    'test_meal_plan_buttons.py', 'test_more_css.py',
    'test_page_title.py',
    'test_recipe_spice.py', 'test_retone.py',
    'test_user_slash.py', 'test_zoom_guards.py',
)
MOVED = (
    # PX-2, 21 Oct 2026 - moved out of KEPT, where RT-1 filed it.
    # PX-1 measured the library on 13 October and its numbers were a
''',
         r'''    # censuses.
    'test_dr2_values.py',
    'test_entry_sections.py', 'test_js_escape.py',
    'test_meal_plan_buttons.py', 'test_more_css.py',
    'test_page_title.py',
    'test_recipe_spice.py', 'test_retone.py',
    'test_user_slash.py', 'test_zoom_guards.py',
)
MOVED = (
    # RA19, 23 Nov 2026 - moved out of KEPT. Its hint-label count sums
    # alv_tree.templates(), the tree as it stands, so a new page with a
    # bold name and a plain hint moves it - six on the Acquisitions
    # screens. A census of today's tree, like the colour suites below.
    'test_label_weight.py',
    # PX-2, 21 Oct 2026 - moved out of KEPT, where RT-1 filed it.
    # PX-1 measured the library on 13 October and its numbers were a
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
    raise SystemExit('RA19 REFUSED: %s' % msg)


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
    if "'test_ra19_acquisitions_screens.py'" in read(pq):
        print('RA19 already applied.')
        return 0
    if "'test_ra18_acquisitions.py'" not in read(pq):
        refuse('RA18 (apply_ra18_acquisitions.py) is not applied - this round registers after it.')
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
        print('RA19 --check: %d file(s) would change, none written; %d '
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
    print('RA19 applied - Property Acquisitions, step 2: the screens. Now run: python manage.py migrate')
    print('      %d file(s) written, backed up to %s' % (len(out), SUFFIX))
    print('      %d file(s) ship with it, wired in rather than written'
          % len(CREATES))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
