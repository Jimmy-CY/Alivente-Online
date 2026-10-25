# -*- coding: utf-8 -*-
"""apply_lease_approval.py - round ES-6, 25 Oct 2026.

A SIGNED LEASE IS APPROVED ONTO ITS TENANT, OR DECLINED.

His decision of 23 October, in his words: "I would also like the signed
PDF to then be uploaded onto a tenant for the Lease that it applies to -
HOWEVER, this would require approval, so we need an approval page and a
notification, for this to be approved before it is saved."

His decisions of 25 October: APPROVE REPLACES whatever lease is attached
(one lease per tenant per period, so no superseded-lease history and no
TenantLeaseDocument table); DECLINE IS FINAL (attaching that lease later
means a new envelope).

WHAT THE ROUND DOES

    ONE PAGE PER ENVELOPE - lease-signing/<pk>/ - where the register's
    View icon has pointed since 23 October with nowhere to go. The
    sealed PDF, who signed and from where, the full trail, the tenancy,
    and what is attached to it now. Approve and Decline appear only when
    LeaseSigning.awaiting_approval says there is something to decide.

    APPROVE writes the sealed copy onto tenant.tenant_lease_agreement by
    UO-1's order: the old file let go of before the save, deleted after
    it, and the new bytes removed again if the save raises.

    THE SEALED PDF IS SERVED THROUGH A PERMISSION CHECK, never from a
    media URL and never cached - ES-4's rule for the page images.

    WHERE IT SHOWS: the bell's count, and a strip on Home and on
    Notifications, all reading LeaseSigning.pending_approval() through
    the context processor - one answer, five places.

    THE SIGNED COPY GOES TO ALIVENTE TOO - decision 2 of 23 October,
    which ES-4 had not built: the sender and the house signer, once each.

AND TWO LOOSE ENDS OF ES-5, FOUND BY HIM ON 25 OCTOBER

    The Send screen still said "every 2 days" - the 22 October plan -
    after ES-5 built day 3 and day 6. And "Days to sign" can be 1 to 60,
    while ES-5 measured its reminders against a fixed seven: fourteen
    days would have reminded on days 10 and 13. His two rules, read
    literally: day 3, and the day before it lapses, counted from when
    the links went out or were last extended. Seven days is still day 3
    and day 6.

PINS THAT MOVE WITH IT: ES-4's suite (the signed copy's recipients),
ES-5's suite (the reminder constant), and the four template counts a
new page always moves - test_house_title, test_js_buttons,
test_subtree_tones, test_tree_roots - each by exactly one.

Idempotent. Every edited file backed up to .bak_leaseapprove; three
files ship new and are wired in rather than written.
"""
import os
import re
import sys

SUFFIX = '.bak_leaseapprove'
MARK = 'ES-6, 25 Oct 2026'
CHECK = False

VIEW = os.path.join('pages', 'views', 'lease_signing_approve.py')
PAGE = os.path.join('pages', 'templates', 'lease_signing_detail.html')
MIG = os.path.join('pages', 'migrations', '0107_es6_lease_approval.py')
CREATES = (VIEW, PAGE, MIG)

PS1 = 'Push-PendingChanges.ps1'
TREE = 'alv_tree.py'
ROUNDS = 'alv_rounds.py'
WD = 'test_waiting_down.py'

# ------------------------------------------------------------- THE SWAPS
# One entry per file. Each WAS is the smallest block of the file as
# ES-5 left it that occurs exactly once.
SWAPS = [
    (os.path.join('pages', 'models.py'), [
        (r'''    # on day 6; day 1/3/6 is three emails in a week.
    SIGNING_DAYS = 7
    REMINDER_DAYS = (3, 6)

    lease_signing_id = models.AutoField(primary_key=True)
''',
         r'''    # on day 6; day 1/3/6 is three emails in a week.
    SIGNING_DAYS = 7
    # ES-6, 25 Oct 2026 - DAY 3, AND THE DAY BEFORE IT LAPSES. ES-5 wrote
    # (3, 6) against a seven-day window, but the Send screen lets the
    # window be anything from 1 to 60 days, and with fourteen days the
    # fixed pair landed on days 10 and 13. His two rules, read literally:
    # one nudge on day 3, one the day before it lapses. For the usual
    # seven days those ARE day 3 and day 6.
    FIRST_REMINDER_DAY = 3
    LAST_REMINDER_DAYS_BEFORE = 1
    REMINDER_RULE = ('Day 3, and the day before the link lapses, to '
                     'whoever has not signed')

    lease_signing_id = models.AutoField(primary_key=True)
'''),
        (r'''    link_base = models.CharField(max_length=200, blank=True)

    class Meta:
        db_table = 'lease_signings'
''',
         r'''    link_base = models.CharField(max_length=200, blank=True)

    # THE APPROVAL - ES-6, 25 Oct 2026. His decision of 23 October: a
    # signed lease is NOT written onto the tenant by the tenant's own
    # action on a page nobody at Alivente is watching. A completed
    # envelope waits here until somebody approves it (the sealed copy
    # becomes the tenant's lease) or declines it (nothing is written).
    #
    # TWO PAIRS AND NOT A STATUS. `status` says what happened to the
    # SIGNING; these say what happened to the RESULT. A completed
    # envelope stays completed whichever way the approval goes, and the
    # register can still ask "was it signed" separately from "was it
    # attached".
    #
    # DECLINE IS FINAL - his decision of 25 October. A declined approval
    # never reappears; attaching that lease means a new envelope.
    approved_at = models.DateTimeField(null=True, blank=True)
    approved_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='lease_signings_approved')
    approval_declined_at = models.DateTimeField(null=True, blank=True)
    approval_declined_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='lease_signings_approval_declined')

    class Meta:
        db_table = 'lease_signings'
'''),
        (r'''        return bool(self.expires_at and timezone.now() > self.expires_at)

    def outstanding(self):
        """The parties who have not signed and have not declined.
''',
         r'''        return bool(self.expires_at and timezone.now() > self.expires_at)

    @property
    def awaiting_approval(self):
        """Signed by everybody, and nobody has yet approved or declined it.

        ES-6, 25 Oct 2026. THE ONE ANSWER, asked by the register, the
        approval page, the bell and the two dashboards - five places
        that must never disagree about whether there is work waiting.
        """
        return (self.status == self.COMPLETED and bool(self.sealed_pdf)
                and self.approved_at is None
                and self.approval_declined_at is None)

    @classmethod
    def pending_approval(cls):
        """The same question as awaiting_approval, asked of the table."""
        return (cls.objects.filter(status=cls.COMPLETED,
                                   approved_at__isnull=True,
                                   approval_declined_at__isnull=True)
                .exclude(sealed_pdf='').exclude(sealed_pdf__isnull=True))

    def outstanding(self):
        """The parties who have not signed and have not declined.
'''),
        (r'''                if not p.signed_at and not p.declined_at]

    def reminder_due(self, now=None):
        """The reminder day that has come and not been sent, or None.

        ES-5, 25 Oct 2026. MEASURED FROM THE WINDOW, NOT FROM sent_at:
        an extension moves expires_at, and the reminders follow it.
        AT MOST ONE A RUN, and a cron that was down across both days
        sends one email rather than two in the same minute.
        """
        if not (self.is_open and self.expires_at):
            return None
        now = now or timezone.now()
        if now >= self.expires_at:
            return None
        start = self.expires_at - timezone.timedelta(days=self.SIGNING_DAYS)
        due = None
        for day in self.REMINDER_DAYS:
            at = start + timezone.timedelta(days=day)
            if now >= at and (self.last_reminder_at is None
                              or self.last_reminder_at < at):
                due = day
        return due

''',
         r'''                if not p.signed_at and not p.declined_at]

    def window_start(self):
        """When the current signing window opened - ES-6, 25 Oct 2026.

        THE LATER OF THE FIRST SEND AND THE LAST EXTENSION. The window
        opens when the links go out (the house signature sends them), and
        an extension opens a new one; a reminder counts from there, not
        from when the envelope was created.
        """
        start = self.sent_at
        if self.pk:
            ext = (self.events.filter(kind='extended')
                   .order_by('-at').values_list('at', flat=True).first())
            if ext and (start is None or ext > start):
                start = ext
        return start

    def reminder_due(self, now=None):
        """The reminder day that has come and not been sent, or None.

        ES-5, 25 Oct 2026; ES-6 made it follow any window length. Day 3
        of the window, and the day before it lapses - each only if it
        falls INSIDE the window. AT MOST ONE A RUN, and a cron that was
        down across both sends one email rather than two in a minute.
        Returns the day number counted from the window's start.
        """
        if not (self.is_open and self.expires_at):
            return None
        now = now or timezone.now()
        if now >= self.expires_at:
            return None
        start = self.window_start()
        if start is None:
            return None
        due = None
        for at in (start + timezone.timedelta(days=self.FIRST_REMINDER_DAY),
                   self.expires_at - timezone.timedelta(
                       days=self.LAST_REMINDER_DAYS_BEFORE)):
            if not (start < at < self.expires_at):
                continue
            if now >= at and (self.last_reminder_at is None
                              or self.last_reminder_at < at):
                due = int(round((at - start).total_seconds() / 86400.0))
        return due

'''),
        (r'''        # per outstanding party; this row is the decision itself.
        ('extended', 'Extended'),
    ]

''',
         r'''        # per outstanding party; this row is the decision itself.
        ('extended', 'Extended'),
        # ES-6, 25 Oct 2026 - what happened to the RESULT. `rejected`
        # and not `declined`, because `declined` already means a TENANT
        # refused to sign, and one word for two acts is a trail nobody
        # can read.
        ('approved', 'Approved onto the tenant'),
        ('rejected', 'Approval declined'),
    ]

'''),
    ]),
    (os.path.join('pages', 'views', 'lease_signing_sign.py'), [
        (r'''
    to = list(getattr(env.tenant, 'tenant_emails', None) or [])
    if not to:
        return 0
''',
         r'''
    to = list(getattr(env.tenant, 'tenant_emails', None) or [])
    # AND TO ALIVENTE - ES-6, 25 Oct 2026, his decision of 23 October:
    # "the signed copy is emailed to Demetri as well as to each tenant
    # who signed". The person who sent the envelope and the house
    # signer, once each, after the tenants.
    house = env.parties.filter(role=LeaseSigningParty.ROLE_ALIVENTE).first()
    for extra in ((getattr(env.created_by, 'email', '') or '')
                  if env.created_by_id else '',
                  (house.email if house else '') or ''):
        extra = extra.strip()
        if extra and extra.lower() not in [t.lower() for t in to]:
            to.append(extra)
    if not to:
        return 0
'''),
    ]),
    (os.path.join('pages', 'views', 'lease_signing.py'), [
        (r'''            # than only in a notification that can be missed. ES-6
            # builds the page it points at.
            'awaiting_approval': (env.status == LeaseSigning.COMPLETED
                                  and not env.tenant.tenant_lease_agreement),
            # ES-5 - from the view's own tuples, never re-decided in the
            # template.
''',
         r'''            # than only in a notification that can be missed. ES-6
            # builds the page it points at.
            # ES-6, 25 Oct 2026 - THE MODEL'S ONE ANSWER. ES-3a guessed
            # from whether the tenant had any lease attached, which was
            # wrong both ways once a lease could be approved over an
            # existing one or declined.
            'awaiting_approval': env.awaiting_approval,
            # ES-5 - from the view's own tuples, never re-decided in the
            # template.
'''),
    ]),
    (os.path.join('pages', 'views', 'lease_signing_create.py'), [
        (r'''# disagree with the date the tenant was told in writing.
#
# THE REMINDER CADENCE IS A CONSTANT. Every two days, for everybody.
# An earlier draft offered it as a per-envelope choice and there is no
# column to put the answer in: adding one would make a view round into
# a model round with a migration, to configure something nobody has
# asked to vary. ES-5 reads this number.
DEFAULT_EXPIRY_DAYS = 7
REMIND_EVERY_DAYS = 2
MIN_EXPIRY_DAYS = 1
MAX_EXPIRY_DAYS = 60
''',
         r'''# disagree with the date the tenant was told in writing.
#
# THE REMINDERS ARE NOT CHOSEN HERE. ES-5 sends them - day 3, and the
# day before the link lapses (day 3 and day 6 of the usual seven), to
# whoever has not signed. ES-6, 25 Oct 2026: this screen said "every 2
# days", the 22 October plan, after ES-5 had built something else; it
# now describes what actually happens, in the model's own words.
DEFAULT_EXPIRY_DAYS = 7
MIN_EXPIRY_DAYS = 1
MAX_EXPIRY_DAYS = 60
'''),
        (r'''        'tenants': tenants,
        'default_expiry': DEFAULT_EXPIRY_DAYS,
        'remind_every': REMIND_EVERY_DAYS,
        'max_tenant_signers': MAX_TENANT_SIGNERS,
        'min_expiry': MIN_EXPIRY_DAYS,
''',
         r'''        'tenants': tenants,
        'default_expiry': DEFAULT_EXPIRY_DAYS,
        'reminder_rule': LeaseSigning.REMINDER_RULE,
        'max_tenant_signers': MAX_TENANT_SIGNERS,
        'min_expiry': MIN_EXPIRY_DAYS,
'''),
    ]),
    (os.path.join('pages', 'templates', 'lease_signing_create.html'), [
        (r'''        <div class="col-md-8">
          <div class="form-group">
            <label for="ls-remind"><strong>Reminders</strong></label>
            <input type="text" id="ls-remind" class="form-control" readonly
                   value="Every {{ remind_every }} days until they sign">
          </div>
        </div>
''',
         r'''        <div class="col-md-8">
          <div class="form-group">
            {# ES-6, 25 Oct 2026 - THE MODEL'S OWN SENTENCE. This said   #}
            {# "every 2 days" after ES-5 had built day 3 and day 6.     #}
            <label for="ls-remind"><strong>Reminders</strong></label>
            <input type="text" id="ls-remind" class="form-control" readonly
                   value="{{ reminder_rule }}">
          </div>
        </div>
'''),
    ]),
    (os.path.join('pages', 'views', '__init__.py'), [
        (r'''# cycle that fails at startup rather than at the first request.
from .lease_signing_create import *  # noqa: F401, F403
from .recipes import *  # noqa: F401, F403
from .help import *  # noqa: F401, F403
''',
         r'''# cycle that fails at startup rather than at the first request.
from .lease_signing_create import *  # noqa: F401, F403
# ES-6, 25 Oct 2026 - one envelope in full, and the approval of a
# signed lease onto its tenant.
from .lease_signing_approve import *  # noqa: F401, F403
from .recipes import *  # noqa: F401, F403
from .help import *  # noqa: F401, F403
'''),
    ]),
    (os.path.join('pages', 'urls.py'), [
        (r'''    path('lease-signing/<int:pk>/cancel/', views.lease_signing_cancel,
         name='lease_signing_cancel'),
    path('lease/<int:tenant_id>/', views.lease_agreement_report, name='lease_agreement_report'),
    path('lease/<str:filename>/view/', views.serve_lease, name='serve_lease'),
''',
         r'''    path('lease-signing/<int:pk>/cancel/', views.lease_signing_cancel,
         name='lease_signing_cancel'),
    # ES-6, 25 Oct 2026 - ONE ENVELOPE IN FULL, where the register's
    # View icon has pointed since 23 October with nowhere to go; the
    # sealed PDF behind a permission check; and the approval itself,
    # POST only, behind the tenants EDIT permission.
    path('lease-signing/<int:pk>/', views.lease_signing_detail,
         name='lease_signing_detail'),
    path('lease-signing/<int:pk>/signed.pdf', views.lease_signing_sealed,
         name='lease_signing_sealed'),
    path('lease-signing/<int:pk>/approve/', views.lease_signing_approve,
         name='lease_signing_approve'),
    path('lease/<int:tenant_id>/', views.lease_agreement_report, name='lease_agreement_report'),
    path('lease/<str:filename>/view/', views.serve_lease, name='serve_lease'),
'''),
    ]),
    (os.path.join('pages', 'templates', 'lease_signing_list.html'), [
        (r'''{# the page this points at; until then it is a count, not a link.     #}
{% if waiting_on_me %}
<div class="ls-note">
    <i class="fas fa-circle-exclamation"></i>
    {{ waiting_on_me }} signed agreement{{ waiting_on_me|pluralize }}
    waiting to be approved onto the tenant record.
</div>
{% endif %}
''',
         r'''{# the page this points at; until then it is a count, not a link.     #}
{% if waiting_on_me %}
{# ES-6, 25 Oct 2026 - and now each one is a link: the row's View     #}
{# icon and the "awaiting approval" note both open the envelope page, #}
{# where Approve and Decline are.                                     #}
<div class="ls-note">
    <i class="fas fa-circle-exclamation"></i>
    {{ waiting_on_me }} signed agreement{{ waiting_on_me|pluralize }}
    waiting to be approved onto the tenant record &mdash; open
    {% if waiting_on_me == 1 %}it{% else %}each one{% endif %} from the
    <b>awaiting approval</b> link on its row.
</div>
{% endif %}
'''),
        (r'''                <td data-label="Expires">
                    {% if r.awaiting_approval %}
                        <span class="ls-attn">awaiting approval</span>
                    {% elif r.env.expires_at %}
                        {{ r.env.expires_at|date:"j M Y" }}
''',
         r'''                <td data-label="Expires">
                    {% if r.awaiting_approval %}
                        <a href="{% url 'lease_signing_detail' r.env.pk %}" class="ls-attn alv-ref-link">awaiting approval</a>
                    {% elif r.env.expires_at %}
                        {{ r.env.expires_at|date:"j M Y" }}
'''),
        (r'''                <td class="desktop-action-cell cell-actions">
                    <div class="row-actions">
                        <span class="icon-action-btn icon-view" title="View this envelope">
                            <i class="fas fa-eye"></i>
                        </span>
                        {# EXTEND AND CANCEL - ES-5, 25 Oct 2026. Drawn on 23  #}
                        {# October as icons that did nothing; now they POST.   #}
''',
         r'''                <td class="desktop-action-cell cell-actions">
                    <div class="row-actions">
                        {# ES-6 - the View icon goes somewhere at last. #}
                        <a href="{% url 'lease_signing_detail' r.env.pk %}" class="icon-action-btn icon-view" title="View this envelope">
                            <i class="fas fa-eye"></i>
                        </a>
                        {# EXTEND AND CANCEL - ES-5, 25 Oct 2026. Drawn on 23  #}
                        {# October as icons that did nothing; now they POST.   #}
'''),
        (r'''                {# THE PHONE ACTIONS. Hidden on desktop by base. #}
                <td class="mobile-action-bar cols-2">
                    <span class="mobile-action-btn">
                        <i class="fas fa-eye mobile-action-icon icon-color-view"></i>
                        <span class="mobile-action-label">View</span>
                    </span>
                    {% if perms.auth.can_edit_tenants and r.can_extend %}
                    {# ES-5 - the phone's Resend becomes the same Extend. #}
''',
         r'''                {# THE PHONE ACTIONS. Hidden on desktop by base. #}
                <td class="mobile-action-bar cols-2">
                    <a href="{% url 'lease_signing_detail' r.env.pk %}" class="mobile-action-btn">
                        <i class="fas fa-eye mobile-action-icon icon-color-view"></i>
                        <span class="mobile-action-label">View</span>
                    </a>
                    {% if perms.auth.can_edit_tenants and r.can_extend %}
                    {# ES-5 - the phone's Resend becomes the same Extend. #}
'''),
    ]),
    (os.path.join('pages', 'templates', 'home.html'), [
        (r'''
  <div class="home-shell">

  {% if insights %}
''',
         r'''
  <div class="home-shell">

  {# SIGNED LEASES WAITING FOR APPROVAL - ES-6, 25 Oct 2026. His decision #}
  {# of 23 October: the approval appears here AND on Notifications.        #}
  {# WRITTEN INTO BOTH PAGES, not included: an include would be a new #}
  {# standalone template, and a dozen censuses count those. The two  #}
  {# copies read ONE count - the context processor's, from the       #}
  {# model's pending_approval() - so they cannot disagree on numbers. #}
  {% if lease_approvals_waiting %}
  <a href="{% url 'lease_signing_list' %}" class="lsa-strip" role="status">
      <i class="fas fa-file-signature"></i>
      <span><b>{{ lease_approvals_waiting }} signed lease{{ lease_approvals_waiting|pluralize }}</b>
      waiting for your approval</span>
      <span class="lsa-go">Review <i class="fas fa-arrow-right"></i></span>
  </a>
  <style>
  /* ES-6 - lsa-* and tokens only: no hex literal reaches a page. */
  .lsa-strip {
      display: flex;
      align-items: center;
      gap: 10px;
      background: var(--alv-warn-soft);
      border: 1px solid var(--alv-warn-line);
      border-left: 4px solid var(--alv-warn);
      border-radius: var(--alv-radius-sm, 6px);
      padding: 11px 14px;
      margin: 0 0 16px;
      color: var(--alv-ink);
      text-decoration: none;
  }
  .lsa-strip:hover { text-decoration: none; color: var(--alv-ink-strong); }
  .lsa-go { margin-left: auto; font-weight: 600; white-space: nowrap; }
  </style>
  {% endif %}

  {% if insights %}
'''),
    ]),
    (os.path.join('pages', 'templates', 'notifications.html'), [
        (r'''        </a>
    </div>

    <!-- Loading Indicator -->
''',
         r'''        </a>
    </div>

    {# SIGNED LEASES WAITING FOR APPROVAL - ES-6, 25 Oct 2026. His decision #}
    {# of 23 October: the approval appears here AND on the Home dashboard.        #}
    {# WRITTEN INTO BOTH PAGES, not included: an include would be a new #}
    {# standalone template, and a dozen censuses count those. The two  #}
    {# copies read ONE count - the context processor's, from the       #}
    {# model's pending_approval() - so they cannot disagree on numbers. #}
    {% if lease_approvals_waiting %}
    <a href="{% url 'lease_signing_list' %}" class="lsa-strip" role="status">
        <i class="fas fa-file-signature"></i>
        <span><b>{{ lease_approvals_waiting }} signed lease{{ lease_approvals_waiting|pluralize }}</b>
        waiting for your approval</span>
        <span class="lsa-go">Review <i class="fas fa-arrow-right"></i></span>
    </a>
    <style>
    /* ES-6 - lsa-* and tokens only: no hex literal reaches a page. */
    .lsa-strip {
        display: flex;
        align-items: center;
        gap: 10px;
        background: var(--alv-warn-soft);
        border: 1px solid var(--alv-warn-line);
        border-left: 4px solid var(--alv-warn);
        border-radius: var(--alv-radius-sm, 6px);
        padding: 11px 14px;
        margin: 0 0 16px;
        color: var(--alv-ink);
        text-decoration: none;
    }
    .lsa-strip:hover { text-decoration: none; color: var(--alv-ink-strong); }
    .lsa-go { margin-left: auto; font-weight: 600; white-space: nowrap; }
    </style>
    {% endif %}

    <!-- Loading Indicator -->
'''),
    ]),
    (os.path.join('mysite', 'context_processors.py'), [
        (r'''    """
    if not request.user.is_authenticated:
        return {'notification_count': 0}
    
    try:
        # Get the notification data
''',
         r'''    """
    if not request.user.is_authenticated:
        return {'notification_count': 0, 'lease_approvals_waiting': 0}

    # SIGNED LEASES WAITING FOR APPROVAL - ES-6, 25 Oct 2026. His
    # decision of 23 October: the approval appears in Notifications and
    # on the Home dashboard. Counted with the ORM on its own, OUTSIDE the
    # raw-SQL block below, so a MySQL hiccup there cannot hide work that
    # is waiting, and only for somebody who can see tenants at all.
    approvals = 0
    try:
        if request.user.has_perm('auth.can_access_tenants'):
            from pages.models import LeaseSigning
            approvals = LeaseSigning.pending_approval().count()
    except Exception:
        approvals = 0

    try:
        # Get the notification data
'''),
        (r'''            notification_data.get('expensesWaitingPayment', 0)
        )
        return {'notification_count': total_count}
    except Exception as e:
        # Log the error if needed
        return {'notification_count': 0}

def get_notification_summary():
''',
         r'''            notification_data.get('expensesWaitingPayment', 0)
        )
        return {'notification_count': total_count + approvals,
                'lease_approvals_waiting': approvals}
    except Exception as e:
        # Log the error if needed
        return {'notification_count': approvals,
                'lease_approvals_waiting': approvals}

def get_notification_summary():
'''),
    ]),
    (os.path.join('test_lease_sign.py'), [
        (r'''            if mail.outbox:
                m = mail.outbox[0]
                ok(sorted(m.to) == ['antoine.madelbos@example.com',
                                    'dorian.tirouard@example.com'],
                   '  to every address on the tenancy, which T2-5 made '
                   'one expression on the model', sorted(m.to))
                ok(len(m.attachments) == 1
                   and m.attachments[0][0].endswith('.pdf'),
''',
         r'''            if mail.outbox:
                m = mail.outbox[0]
                # ES-6, 25 Oct 2026 - AND TO ALIVENTE. Decision 2 of 23
                # October: the signed copy goes to each tenant who signed
                # AND to Demetri. The tenancy's addresses first, then the
                # house signer, once.
                ok(sorted(m.to) == ['antoine.madelbos@example.com',
                                    'dorian.tirouard@example.com',
                                    'signer@example.com'],
                   '  to every address on the tenancy, which T2-5 made '
                   'one expression on the model - and to the house signer',
                   sorted(m.to))
                ok(len(m.attachments) == 1
                   and m.attachments[0][0].endswith('.pdf'),
'''),
    ]),
    (os.path.join('test_signing_lifecycle.py'), [
        (r'''        ("('extended', 'Extended')" in py[MODELS],
         'and the trail can say it was EXTENDED'),
        ('REMINDER_DAYS = (3, 6)' in py[MODELS],
         'reminders are day 3 and day 6, written once on the model'),
        ('def outstanding(self)' in py[MODELS]
         and 'def reminder_due(self' in py[MODELS],
''',
         r'''        ("('extended', 'Extended')" in py[MODELS],
         'and the trail can say it was EXTENDED'),
        # ES-6, 25 Oct 2026 - day 3 and the day before it lapses, which
        # for the usual seven days IS day 3 and day 6; the fixed pair
        # broke on any other window the Send screen allows.
        ('FIRST_REMINDER_DAY = 3' in py[MODELS]
         and 'LAST_REMINDER_DAYS_BEFORE = 1' in py[MODELS],
         'reminders are day 3 and the day before it lapses, written once '
         'on the model'),
        ('def outstanding(self)' in py[MODELS]
         and 'def reminder_due(self' in py[MODELS],
'''),
    ]),
    (os.path.join('test_house_title.py'), [
        (r'''# keeping the two honest" had been disagreeing for three days. Both
# say 122 now.
ok(len(wearers) == 124,   # ES-3b, 24 Oct 2026 - lease_signing_create.html, the Send for Signature screen, wears the house title pair.   # (was 123)   # ES-3a, 23 Oct 2026 - lease_signing_list.html wears the house title pair.   # (was 122)
   '122 templates now wear the class, which is the number base\'s note '
   'states', len(wearers))
''',
         r'''# keeping the two honest" had been disagreeing for three days. Both
# say 122 now.
ok(len(wearers) == 125,   # ES-6, 25 Oct 2026 - lease_signing_detail.html, the envelope page, an ordinary pages/templates page that joins every tree-wide count. Wears the house title pair.   # (was 124)   # ES-3b, 24 Oct 2026 - lease_signing_create.html, the Send for Signature screen, wears the house title pair.   # (was 123)   # ES-3a, 23 Oct 2026 - lease_signing_list.html wears the house title pair.   # (was 122)
   '122 templates now wear the class, which is the number base\'s note '
   'states', len(wearers))
'''),
    ]),
    (os.path.join('test_js_buttons.py'), [
        (r'''# SCOPE does not move - 117 was and is the narrow half, and the pages
# the flag hides are still the recipe and meal-plan side.
CENSUS_NARROW, CENSUS_WIDE = 124, 149   # ES-3b, 24 Oct 2026 - the Send for Signature screen, an ordinary page that joins both halves.   # (was 123, 148)   # ES-4, 24 Oct 2026 - the four public signing templates. They are ordinary pages/templates files, so they join both halves - but they contribute ZERO scanner hits, measured: their controls wear .ls-btn, a class of their own, because the pages cannot extend base and so cannot use the house one.   # (was 119, 144)   # ES-3a, 23 Oct 2026 - lease_signing_list.html, the envelope register. An ordinary pages/templates page, so it joins every tree-wide count.   # (was 118, 143)   # RV-1, 23 Oct 2026 - cash_receipt_detail.html. BOTH halves move: unlike meal_plan_print this is an ordinary pages/templates page, so it joins the sweep scope as well as the application count.   # (was 117, 142)   # PP-1, 20 Oct 2026 - meal_plan_print.html. The narrow half does not move: the sweep scope is the 117 pages it has always been.   # (WIDE was 141)   # RD-1, 19 Oct 2026 - the
# quick-look pair. (wide was 139, and 142 before MN-1 retired four
# meal-plan screens.)
''',
         r'''# SCOPE does not move - 117 was and is the narrow half, and the pages
# the flag hides are still the recipe and meal-plan side.
CENSUS_NARROW, CENSUS_WIDE = 125, 150   # ES-6, 25 Oct 2026 - lease_signing_detail.html, the envelope page, an ordinary pages/templates page that joins every tree-wide count.   # (was 124, 149)   # ES-3b, 24 Oct 2026 - the Send for Signature screen, an ordinary page that joins both halves.   # (was 123, 148)   # ES-4, 24 Oct 2026 - the four public signing templates. They are ordinary pages/templates files, so they join both halves - but they contribute ZERO scanner hits, measured: their controls wear .ls-btn, a class of their own, because the pages cannot extend base and so cannot use the house one.   # (was 119, 144)   # ES-3a, 23 Oct 2026 - lease_signing_list.html, the envelope register. An ordinary pages/templates page, so it joins every tree-wide count.   # (was 118, 143)   # RV-1, 23 Oct 2026 - cash_receipt_detail.html. BOTH halves move: unlike meal_plan_print this is an ordinary pages/templates page, so it joins the sweep scope as well as the application count.   # (was 117, 142)   # PP-1, 20 Oct 2026 - meal_plan_print.html. The narrow half does not move: the sweep scope is the 117 pages it has always been.   # (WIDE was 141)   # RD-1, 19 Oct 2026 - the
# quick-look pair. (wide was 139, and 142 before MN-1 retired four
# meal-plan screens.)
'''),
    ]),
    (os.path.join('test_subtree_tones.py'), [
        (r'''# ES-4, 24 Oct 2026 - the four public signing templates. They are ordinary pages/templates files, so they join every tree-wide count; they cannot extend base, which is why they are standalone.
# ES-3b, 24 Oct 2026 - the Send for Signature screen sits flat in pages/templates, so it joins the walk and the flat listing alike.
ok(len(tree) == 158, 'a WALK finds 158 templates', len(tree))
ok(len(top) == 132, '  a flat listing finds 132 - 120 was what H7 '
   'counted, 122 after MN-1, and RD-1 adds the quick-look pair',
   len(top))
''',
         r'''# ES-4, 24 Oct 2026 - the four public signing templates. They are ordinary pages/templates files, so they join every tree-wide count; they cannot extend base, which is why they are standalone.
# ES-3b, 24 Oct 2026 - the Send for Signature screen sits flat in pages/templates, so it joins the walk and the flat listing alike.
# ES-6, 25 Oct 2026 - lease_signing_detail.html, the envelope page, an ordinary pages/templates page that joins every tree-wide count.
ok(len(tree) == 159, 'a WALK finds 159 templates', len(tree))
ok(len(top) == 133, '  a flat listing finds 133 - 120 was what H7 '
   'counted, 122 after MN-1, and RD-1 adds the quick-look pair',
   len(top))
'''),
    ]),
    (os.path.join('test_tree_roots.py'), [
        (r'''# 143 since 6 Oct: Section E round E-2b added access_denied.html,
# the 403 page, which until then lived in an f-string.
MAIN_N = 150   # ES-3b, 24 Oct 2026 - the Send for Signature screen, an ordinary page that joins every tree-wide count.   # (was 149)   # ES-4, 24 Oct 2026 - the four public signing templates. They are ordinary pages/templates files, so they join every tree-wide count; they cannot extend base, which is why they are standalone.   # (was 145)   # ES-3a, 23 Oct 2026 - lease_signing_list.html, the envelope register. An ordinary pages/templates page, so it joins every tree-wide count.   # (was 144)   # RV-1, 23 Oct 2026 - cash_receipt_detail.html. This is the shape of the tree, which is what this file is for.   # (was 143)   # PP-1, 20 Oct 2026 - the printable meal plan is a
               # new page: 142 + 1. (was 142)   # RD-1, 19 Oct 2026 - the quick-look dialog adds two:
               # the partial and its shell. (was 140)   # RT-1, 18 Oct 2026 - MN-1 retired four meal-plan screens and the planner replaced them: 143 - 4 + 1. This is the shape of the tree, which is what this file is for.   # (was 143)
''',
         r'''# 143 since 6 Oct: Section E round E-2b added access_denied.html,
# the 403 page, which until then lived in an f-string.
MAIN_N = 151   # ES-6, 25 Oct 2026 - lease_signing_detail.html, the envelope page, an ordinary pages/templates page that joins every tree-wide count.   # (was 150)   # ES-3b, 24 Oct 2026 - the Send for Signature screen, an ordinary page that joins every tree-wide count.   # (was 149)   # ES-4, 24 Oct 2026 - the four public signing templates. They are ordinary pages/templates files, so they join every tree-wide count; they cannot extend base, which is why they are standalone.   # (was 145)   # ES-3a, 23 Oct 2026 - lease_signing_list.html, the envelope register. An ordinary pages/templates page, so it joins every tree-wide count.   # (was 144)   # RV-1, 23 Oct 2026 - cash_receipt_detail.html. This is the shape of the tree, which is what this file is for.   # (was 143)   # PP-1, 20 Oct 2026 - the printable meal plan is a
               # new page: 142 + 1. (was 142)   # RD-1, 19 Oct 2026 - the quick-look dialog adds two:
               # the partial and its shell. (was 140)   # RT-1, 18 Oct 2026 - MN-1 retired four meal-plan screens and the planner replaced them: 143 - 4 + 1. This is the shape of the tree, which is what this file is for.   # (was 143)
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
    raise SystemExit('ES-6 REFUSED: %s' % msg)


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

    pm = os.path.join(root, 'pages', 'models.py')
    if MARK in read(pm):
        print('ES-6  already applied - the approval page.')
        return 0

    sys.path.insert(0, root)
    import alv_tree as T

    # ---- WHAT THIS ROUND STANDS ON
    if "'test_signing_lifecycle.py'" not in read(os.path.join(root, PS1)) \
            or 'def outstanding(self):' not in read(pm):
        refuse('ES-5 is not applied - this round registers after it and '
               'rewrites its reminder rule.')
    for rel in CREATES:
        if not os.path.isfile(os.path.join(root, rel)):
            refuse('%s is not on disk. It is what this round IS - the '
                   'patcher wires it in, it does not write it.' % rel)

    # ---- THE MIGRATION FOLLOWS THE ONE IMMEDIATELY BEFORE IT
    migdir = os.path.join(root, 'pages', 'migrations')
    names = sorted(f[:-3] for f in os.listdir(migdir)
                   if re.match(r'^\d{4}_.*\.py$', f))
    deps = {}
    for nm in names:
        deps[nm] = re.findall(r'\("pages",\s*"(\d{4}_[^"]+)"\)|'
                              r"\('pages',\s*'(\d{4}_[^']+)'\)",
                              read(os.path.join(migdir, nm + '.py')))
    mine = os.path.basename(MIG)[:-3]
    used = set()
    for nm, ds in deps.items():
        for pair in ds:
            used.add(pair[0] or pair[1])
    leaves = [nm for nm in names if nm not in used]
    if leaves != [mine]:
        refuse('the migration graph should end at %s alone; its leaves '
               'are %r' % (mine, leaves))
    prev = [p[0] or p[1] for p in deps[mine]]
    if prev != [names[names.index(mine) - 1]]:
        refuse('%s should depend on the migration immediately before it, '
               'not %r' % (mine, prev))

    # ---- THE SWAPS
    for rel, pairs in SWAPS:
        pth = os.path.join(root, rel)
        t = read(pth)
        for i, (was, now) in enumerate(pairs):
            t = swap(t, was, now, '%s (swap %d of %d)'
                     % (rel, i + 1, len(pairs)))
        out[pth] = t

    # ---- REGISTRATION
    pq = os.path.join(root, PS1)
    q = read(pq)
    q = swap(q, """    'test_signing_lifecycle.py'
)""", """    'test_signing_lifecycle.py',
    # ES-6, 25 Oct 2026 - a signed lease is approved onto its tenant.
    'test_lease_approval.py'
)""", '%s (the suites)' % PS1)
    q = swap(
        q,
        """    @{ File = 'mysite/cron-requirements.txt'; Text = 'pymupdf';""",
        """    @{ File = 'pages/models.py'; Text = 'def awaiting_approval(self):'; What = 'ES-6: ONE answer to is this signed lease waiting for approval - the register, the envelope page, the bell and both dashboards ask it, and five screens deciding for themselves is how they come to disagree about whether there is work waiting' },
    @{ File = 'pages/views/lease_signing_approve.py'; Text = "released = [let_go_of_file(ten, 'tenant_lease_agreement')]"; What = 'ES-6: approving a signed lease lets go of the old one BEFORE the save and deletes it AFTER - UO-1 order on the second door into this field; the other order is how a failed save destroys a lease' },
    @{ File = 'mysite/cron-requirements.txt'; Text = 'pymupdf';""",
        '%s (the sentinels)' % PS1)
    out[pq] = q

    ptr = os.path.join(root, TREE)
    out[ptr] = swap(read(ptr), """    'test_signing_lifecycle.py',
]""", """    'test_signing_lifecycle.py',
    # ES-6, 25 Oct 2026 - a signed lease is approved onto its tenant.
    'test_lease_approval.py',
]""", '%s (CONVERTED)' % TREE)

    pd = os.path.join(root, ROUNDS)
    out[pd] = swap(read(pd), """    '.bak_signlife',
]""", """    '.bak_signlife',
    # ES-6, 25 Oct 2026 - a signed lease is approved onto its tenant.
    '.bak_leaseapprove',
]""", '%s (ROUNDS)' % ROUNDS)

    pw = os.path.join(root, WD)
    w = read(pw)
    n = re.search(r'CONVERTED_N = (\d+)', w)
    if not n:
        refuse('%s: CONVERTED_N is not there' % WD)
    out[pw] = swap(w, 'CONVERTED_N = %s' % n.group(1),
                   'CONVERTED_N = %d   # ES-6, 25 Oct 2026 - this round '
                   'own suite   # (was %s)'
                   % (int(n.group(1)) + 1, n.group(1)),
                   '%s (CONVERTED_N)' % WD)

    # ---------------------------------------------------------- THE GATES
    view = T.python_code_only(read(os.path.join(root, VIEW)))

    # ---- 1. UO-1's ORDER ON THE SECOND DOOR INTO THIS FIELD.
    a = view.find("let_go_of_file(ten, 'tenant_lease_agreement')")
    s_ = view.find('ten.save()')
    d_ = view.find("delete_unheld(tenant, released")
    if not (0 <= a < s_ < d_):
        refuse('the approval must let go of the old lease, save, and only '
               'then delete it - UO-1, 23 October. Any other order is how a '
               'failed save destroys a signed lease.')
    if 'default_storage.delete(written)' not in view:
        refuse('a failed save must remove the new bytes it wrote, or every '
               'failure leaves an orphan on the volume.')

    # ---- 2. ONCE ONLY, WHICHEVER WAY.
    if 'if not env.awaiting_approval:' not in view:
        refuse('the approval view does not refuse an envelope that is not '
               'waiting - a second press would attach twice or reverse a '
               'recorded decision, and decline is FINAL.')

    # ---- 3. ONE ANSWER, FIVE PLACES.
    ctx = T.python_code_only(out[os.path.join(root, 'mysite',
                                              'context_processors.py')])
    if 'pending_approval().count()' not in ctx:
        refuse('the bell does not ask LeaseSigning.pending_approval().')

    # ---- 4. NO HEX LITERAL REACHES A PAGE.
    for rel in (PAGE, os.path.join('pages', 'templates', 'home.html'),
                os.path.join('pages', 'templates', 'notifications.html')):
        src = out.get(os.path.join(root, rel)) or read(os.path.join(root, rel))
        for blk in re.findall(r'\.(?:lsd|lsa)-[\s\S]*?\}', src):
            if re.search(r'#[0-9a-fA-F]{3,6}\b', blk):
                refuse('%s: an lsd-/lsa- rule carries a hex literal; tokens '
                       'only.' % rel)

    if CHECK:
        print('ES-6  --check: %d file(s) would change, none written; %d '
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
    print('ES-6  applied - a signed lease is approved onto its tenant, or '
          'declined; the bell and both dashboards show what is waiting.')
    print('      %d file(s) written, backed up to %s' % (len(out), SUFFIX))
    print('      %d file(s) ship with it, wired in rather than written'
          % len(CREATES))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
