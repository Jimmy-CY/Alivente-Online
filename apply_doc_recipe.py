# -*- coding: utf-8 -*-
"""apply_doc_recipe.py - rounds DC-1 and RC-3, 12 Nov 2026.

RELEASES 71 AND 72, ONE BUNDLE.

    71 DOCUMENTS: health card, residence certificate, car registration,
       MOT, insurance and tax ID; Remind me 9 or 12 months before expiry,
       for slow renewals (the usual six months otherwise).
    72 RECIPES: Cooked it - stars, a note, "last cooked ..."; cook mode -
       one step at a time, screen on, timers; the recipe list stops
       fetching every ingredient for nothing.
    And meal_calendar_backfill names its database first.

New files ship beside this patcher. Stands on Release 70. Idempotent.
Edits backed up to .bak_docrecipe. MIGRATIONS 0117 and 0118.
"""
import os
import sys

SUFFIX = '.bak_docrecipe'
MARK = 'DC-1, 12 Nov 2026'
CHECK = False
PS1 = 'Push-PendingChanges.ps1'
CREATES = (
    'pages/migrations/0117_document_types_remind.py',
    'pages/migrations/0118_recipe_cooks.py',
    'test_doc_recipe.py',
)

SWAPS = [
    (os.path.join('Push-PendingChanges.ps1'), [
        (r'''    @{ File = 'wellness/phases.py'; Text = 'DISCLAIMER = ('; What = 'CY-2/CY-4: the cycle phases are on disk, honestly worded - without them the cycle tracker cannot open' },
    @{ File = 'pages/css_files.py'; Text = 'def stylesheet(request, digest):'; What = 'SP-1: base.html links its stylesheets from here - without it every page loses its styling' },
    @{ File = 'wellness/home.py'; Text = 'def card_lines(g):'; What = 'PT-1: At home today on Wellness Today - without it Today cannot be drawn' },
    @{ File = 'pages/meal_calendar.py'; Text = 'class MealCalendarMiddleware:'; What = 'MS-1: which meal plan a request is about - without it the planner cannot open' },
''',
         r'''    @{ File = 'wellness/phases.py'; Text = 'DISCLAIMER = ('; What = 'CY-2/CY-4: the cycle phases are on disk, honestly worded - without them the cycle tracker cannot open' },
    @{ File = 'pages/css_files.py'; Text = 'def stylesheet(request, digest):'; What = 'SP-1: base.html links its stylesheets from here - without it every page loses its styling' },
    @{ File = 'pages/models.py'; Text = 'class RecipeCook(models.Model):'; What = 'RC-3: Cooked it is on disk - without it a recipe page cannot open' },
    @{ File = 'wellness/home.py'; Text = 'def card_lines(g):'; What = 'PT-1: At home today on Wellness Today - without it Today cannot be drawn' },
    @{ File = 'pages/meal_calendar.py'; Text = 'class MealCalendarMiddleware:'; What = 'MS-1: which meal plan a request is about - without it the planner cannot open' },
'''),
        (r'''    'test_meal_share.py',
    # PT-1, 12 Nov 2026 - Personal Today inside Wellness; log a past workout.
    'test_wellness_twentyfour.py'
)
# NUMBER EVERY SUITE AS IT RUNS - Demetri, 1 Oct 2026: "for every check of
''',
         r'''    'test_meal_share.py',
    # PT-1, 12 Nov 2026 - Personal Today inside Wellness; log a past workout.
    'test_wellness_twentyfour.py',
    # DC-1 + RC-3, 12 Nov 2026 - Releases 71 and 72: documents; Cooked it and cook mode.
    'test_doc_recipe.py'
)
# NUMBER EVERY SUITE AS IT RUNS - Demetri, 1 Oct 2026: "for every check of
'''),
    ]),
    (os.path.join('alv_rounds.py'), [
        (r'''    # PT-1, 12 Nov 2026 - Personal Today inside Wellness; log a past workout.
    '.bak_wellness24',
]

''',
         r'''    # PT-1, 12 Nov 2026 - Personal Today inside Wellness; log a past workout.
    '.bak_wellness24',
    # DC-1 + RC-3, 12 Nov 2026 - Releases 71 and 72.
    '.bak_docrecipe',
]

'''),
    ]),
    (os.path.join('pages', 'help_content', 'administration.html'), [
        (r'''    <h6 style="font-weight:700; color:#2c3e50; margin-bottom:14px; border-bottom:2px solid #0e7c8b; padding-bottom:6px;"><i class="fas fa-star" style="color:#0e7c8b;"></i> Key Features</h6>
    <div style="display:grid; grid-template-columns:1fr 1fr; gap:12px; margin-bottom:24px;">
      <div style="background:#f0fdff; border:1px solid #b2ebf2; border-radius:8px; padding:14px;"><div style="font-weight:600; color:#0e7c8b; margin-bottom:4px;"><i class="fas fa-passport"></i> Multiple Document Types</div><div style="font-size:13px; color:#6c757d;">Store Passports, ID Cards, Driver's Licences, ARC cards, and more &mdash; all in one place.</div></div>
      <div style="background:#f0fdff; border:1px solid #b2ebf2; border-radius:8px; padding:14px;"><div style="font-weight:600; color:#0e7c8b; margin-bottom:4px;"><i class="fas fa-eye"></i> View Documents</div><div style="font-size:13px; color:#6c757d;">View uploaded document scans or PDFs directly in the browser without downloading.</div></div>
      <div style="background:#f0fdff; border:1px solid #b2ebf2; border-radius:8px; padding:14px;"><div style="font-weight:600; color:#0e7c8b; margin-bottom:4px;"><i class="fas fa-exclamation-circle" style="color:#dc3545;"></i> Expiry Alerts</div><div style="font-size:13px; color:#6c757d;">Expiry dates shown in red when a document is expiring within 6 months or has already expired.</div></div>
      <div style="background:#f0fdff; border:1px solid #b2ebf2; border-radius:8px; padding:14px;"><div style="font-weight:600; color:#0e7c8b; margin-bottom:4px;"><i class="fas fa-bell"></i> Email Notifications</div><div style="font-size:13px; color:#6c757d;">Automatic email alerts on the 1st and 15th of every month for documents expiring soon or already expired.</div></div>
      <div style="background:#f0fdff; border:1px solid #b2ebf2; border-radius:8px; padding:14px;"><div style="font-weight:600; color:#0e7c8b; margin-bottom:4px;"><i class="fas fa-filter"></i> Filtering</div><div style="font-size:13px; color:#6c757d;">Filter by holder name, document type, country of issue, and status to quickly find any document.</div></div>
      <div style="background:#f0fdff; border:1px solid #b2ebf2; border-radius:8px; padding:14px;"><div style="font-weight:600; color:#0e7c8b; margin-bottom:4px;"><i class="fas fa-users"></i> Multiple Holders</div><div style="font-size:13px; color:#6c757d;">Manage documents for multiple family members or associates &mdash; all in a single, searchable list.</div></div>
''',
         r'''    <h6 style="font-weight:700; color:#2c3e50; margin-bottom:14px; border-bottom:2px solid #0e7c8b; padding-bottom:6px;"><i class="fas fa-star" style="color:#0e7c8b;"></i> Key Features</h6>
    <div style="display:grid; grid-template-columns:1fr 1fr; gap:12px; margin-bottom:24px;">
      <div style="background:#f0fdff; border:1px solid #b2ebf2; border-radius:8px; padding:14px;"><div style="font-weight:600; color:#0e7c8b; margin-bottom:4px;"><i class="fas fa-passport"></i> Multiple Document Types</div><div style="font-size:13px; color:#6c757d;">Store Passports, IDs, Driver's Licences, health cards, MOT, insurance and more &mdash; all in one place.</div></div>
      <div style="background:#f0fdff; border:1px solid #b2ebf2; border-radius:8px; padding:14px;"><div style="font-weight:600; color:#0e7c8b; margin-bottom:4px;"><i class="fas fa-eye"></i> View Documents</div><div style="font-size:13px; color:#6c757d;">View uploaded document scans or PDFs directly in the browser without downloading.</div></div>
      <div style="background:#f0fdff; border:1px solid #b2ebf2; border-radius:8px; padding:14px;"><div style="font-weight:600; color:#0e7c8b; margin-bottom:4px;"><i class="fas fa-exclamation-circle" style="color:#dc3545;"></i> Expiry Alerts</div><div style="font-size:13px; color:#6c757d;">Expiry dates shown in red when a document is expiring within 6 months or has already expired.</div></div>
      <div style="background:#f0fdff; border:1px solid #b2ebf2; border-radius:8px; padding:14px;"><div style="font-weight:600; color:#0e7c8b; margin-bottom:4px;"><i class="fas fa-bell"></i> Email Notifications</div><div style="font-size:13px; color:#6c757d;">Automatic email alerts on the 1st and 15th of every month for documents expiring within 6 months &mdash; or 9 or 12 months, if you set Remind me.</div></div>
      <div style="background:#f0fdff; border:1px solid #b2ebf2; border-radius:8px; padding:14px;"><div style="font-weight:600; color:#0e7c8b; margin-bottom:4px;"><i class="fas fa-filter"></i> Filtering</div><div style="font-size:13px; color:#6c757d;">Filter by holder name, document type, country of issue, and status to quickly find any document.</div></div>
      <div style="background:#f0fdff; border:1px solid #b2ebf2; border-radius:8px; padding:14px;"><div style="font-weight:600; color:#0e7c8b; margin-bottom:4px;"><i class="fas fa-users"></i> Multiple Holders</div><div style="font-size:13px; color:#6c757d;">Manage documents for multiple family members or associates &mdash; all in a single, searchable list.</div></div>
'''),
        (r'''    <div style="display:flex; flex-direction:column; gap:14px;">
      <div style="background:#f8f9fa; border-radius:8px; padding:14px; border-left:4px solid #0e7c8b;"><div style="font-weight:700; color:#2c3e50; margin-bottom:4px;"><span style="background:#0e7c8b; color:white; border-radius:50%; padding:1px 7px; margin-right:8px; font-size:11px;">1</span> Holder Name</div><div style="font-size:13px; color:#6c757d;">Select the person this document belongs to. Multiple documents can be added per person.</div></div>
      <div style="background:#f8f9fa; border-radius:8px; padding:14px; border-left:4px solid #0e7c8b;"><div style="font-weight:700; color:#2c3e50; margin-bottom:4px;"><span style="background:#0e7c8b; color:white; border-radius:50%; padding:1px 7px; margin-right:8px; font-size:11px;">2</span> Document Type</div><div style="font-size:13px; color:#6c757d;">Select Passport, ID, Driver's License, Visa, or ARC. This determines the badge colour in the list.</div></div>
      <div style="background:#f8f9fa; border-radius:8px; padding:14px; border-left:4px solid #0e7c8b;"><div style="font-weight:700; color:#2c3e50; margin-bottom:4px;"><span style="background:#0e7c8b; color:white; border-radius:50%; padding:1px 7px; margin-right:8px; font-size:11px;">3</span> Document Number</div><div style="font-size:13px; color:#6c757d;">Enter the unique number exactly as it appears on the document.</div></div>
      <div style="background:#f8f9fa; border-radius:8px; padding:14px; border-left:4px solid #0e7c8b;"><div style="font-weight:700; color:#2c3e50; margin-bottom:4px;"><span style="background:#0e7c8b; color:white; border-radius:50%; padding:1px 7px; margin-right:8px; font-size:11px;">4</span> Country of Issue</div><div style="font-size:13px; color:#6c757d;">Select the country that issued the document.</div></div>
''',
         r'''    <div style="display:flex; flex-direction:column; gap:14px;">
      <div style="background:#f8f9fa; border-radius:8px; padding:14px; border-left:4px solid #0e7c8b;"><div style="font-weight:700; color:#2c3e50; margin-bottom:4px;"><span style="background:#0e7c8b; color:white; border-radius:50%; padding:1px 7px; margin-right:8px; font-size:11px;">1</span> Holder Name</div><div style="font-size:13px; color:#6c757d;">Select the person this document belongs to. Multiple documents can be added per person.</div></div>
      <div style="background:#f8f9fa; border-radius:8px; padding:14px; border-left:4px solid #0e7c8b;"><div style="font-weight:700; color:#2c3e50; margin-bottom:4px;"><span style="background:#0e7c8b; color:white; border-radius:50%; padding:1px 7px; margin-right:8px; font-size:11px;">2</span> Document Type</div><div style="font-size:13px; color:#6c757d;">Select Passport, ID, Driver's License, Visa, ARC, Health Card, Residence Certificate, Car Registration, MOT, Insurance or Tax ID. Slow to renew? Set Remind me to 9 or 12 months.</div></div>
      <div style="background:#f8f9fa; border-radius:8px; padding:14px; border-left:4px solid #0e7c8b;"><div style="font-weight:700; color:#2c3e50; margin-bottom:4px;"><span style="background:#0e7c8b; color:white; border-radius:50%; padding:1px 7px; margin-right:8px; font-size:11px;">3</span> Document Number</div><div style="font-size:13px; color:#6c757d;">Enter the unique number exactly as it appears on the document.</div></div>
      <div style="background:#f8f9fa; border-radius:8px; padding:14px; border-left:4px solid #0e7c8b;"><div style="font-weight:700; color:#2c3e50; margin-bottom:4px;"><span style="background:#0e7c8b; color:white; border-radius:50%; padding:1px 7px; margin-right:8px; font-size:11px;">4</span> Country of Issue</div><div style="font-size:13px; color:#6c757d;">Select the country that issued the document.</div></div>
'''),
        (r'''        <div style="font-weight:600; color:#2c3e50; margin-bottom:6px;"><i class="fas fa-print" style="color:#6c757d;"></i> Print Recipe</div>
        <div style="font-size:13px; color:#6c757d;">Sends the recipe to your printer in a clean, formatted layout.</div>
      </div>

''',
         r'''        <div style="font-weight:600; color:#2c3e50; margin-bottom:6px;"><i class="fas fa-print" style="color:#6c757d;"></i> Print Recipe</div>
        <div style="font-size:13px; color:#6c757d;">Sends the recipe to your printer in a clean, formatted layout.</div>
      </div>

      <div style="background:#f8f9fa; border-radius:8px; padding:14px; border-left:4px solid #0e7c8b;">
        <div style="font-weight:600; color:#2c3e50; margin-bottom:6px;"><i class="fas fa-play" style="color:#0e7c8b;"></i> Cook mode</div>
        <div style="font-size:13px; color:#6c757d;">Under Instructions, <strong>Cook mode</strong> shows one step at a time in big text, keeps your screen on, and offers a timer on any step that has minutes. Next and Back move between steps; &times; closes it.</div>
      </div>

      <div style="background:#f8f9fa; border-radius:8px; padding:14px; border-left:4px solid #0e7c8b;">
        <div style="font-weight:600; color:#2c3e50; margin-bottom:6px;"><i class="fas fa-utensils" style="color:#0e7c8b;"></i> Cooked it</div>
        <div style="font-size:13px; color:#6c757d;">At the bottom of a recipe, tap the stars, add a note if you like and press <strong>I cooked it</strong>. The recipe then says when you last made it, how often, and your average rating. It is yours alone &mdash; nobody else sees it.</div>
      </div>

'''),
    ]),
    (os.path.join('pages', 'management', 'commands', 'check_lease_renewal_and_invoices.py'), [
        (r'''            # 2. Status = 'active'
            # 3. Expiry date within 6 months or already expired
            expiring_passports = Passport.objects.filter(
                expiry_date__isnull=False,  # Must have an expiry date
                status='active',             # Must be active status
                expiry_date__lte=six_months_from_now  # Expiring within 6 months or already expired
            ).order_by('expiry_date')

            passport_list = []
            for passport in expiring_passports:
                days_until_expiry = (passport.expiry_date - today).days

''',
         r'''            # 2. Status = 'active'
            # 3. Expiry date within 6 months or already expired
            # DC-1, 12 Nov 2026 - a document may ask to be reminded earlier
            # (9 or 12 months, for slow renewals). Read the widest window,
            # then keep each document only inside its own.
            expiring_passports = Passport.objects.filter(
                expiry_date__isnull=False,  # Must have an expiry date
                status='active',             # Must be active status
                expiry_date__lte=today + timedelta(
                    days=max(Passport.REMIND_DAYS.values()))
            ).order_by('expiry_date')

            passport_list = []
            for passport in expiring_passports:
                window = Passport.REMIND_DAYS.get(passport.remind_months,
                                                  Passport.REMIND_DAYS[None])
                if passport.expiry_date > today + timedelta(days=window):
                    continue
                days_until_expiry = (passport.expiry_date - today).days

'''),
    ]),
    (os.path.join('pages', 'management', 'commands', 'meal_calendar_backfill.py'), [
        (r'''from django.db import transaction

from pages.models import MealCalendar, MealEntry

''',
         r'''from django.db import transaction

from pages.db_banner import print_banner
from pages.models import MealCalendar, MealEntry

'''),
        (r'''
    def handle(self, *args, **opts):
        loose = MealEntry.objects.filter(calendar__isnull=True)
        n = loose.count()
''',
         r'''
    def handle(self, *args, **opts):
        # DC-1, 12 Nov 2026 - say which database before anything else, as
        # every other tool that can run against Live does.
        print_banner(self.stdout.write)
        loose = MealEntry.objects.filter(calendar__isnull=True)
        n = loose.count()
'''),
    ]),
    (os.path.join('pages', 'models.py'), [
        (r'''        ('visa', 'Visa'),
        ('arc', 'Alien Registration Card'),
    ]

    STATUS_CHOICES = [
''',
         r'''        ('visa', 'Visa'),
        ('arc', 'Alien Registration Card'),
        # DC-1, 12 Nov 2026 - Demetri: "We can add these additional
        # document types." Same reminders as a passport.
        ('health', 'Health Card'),
        ('residence', 'Residence Certificate'),
        ('car_reg', 'Car Registration'),
        ('mot', 'MOT'),
        ('insurance', 'Insurance'),
        ('tax_id', 'Tax ID'),
    ]
    # DC-1 - "an earlier reminder for slow renewals as an optional
    # choice". Empty: the usual six months. A Greek passport, say, can be
    # set to nine or twelve months before it expires.
    REMIND_CHOICES = [(9, '9 months before'), (12, '12 months before')]
    REMIND_DAYS = {None: 180, 9: 270, 12: 365}

    STATUS_CHOICES = [
'''),
        (r'''    expiry_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    document_file = models.FileField(upload_to='passports/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
''',
         r'''    expiry_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    remind_months = models.PositiveSmallIntegerField(
        choices=REMIND_CHOICES, null=True, blank=True,
        help_text='Remind earlier than six months before expiry')
    document_file = models.FileField(upload_to='passports/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
'''),
        (r'''    def __str__(self):
        return f"{self.user.username} - {self.recipe.recipe_name}"

class PantryStaple(models.Model):
''',
         r'''    def __str__(self):
        return f"{self.user.username} - {self.recipe.recipe_name}"

class RecipeCook(models.Model):
    """RC-3, 12 Nov 2026 - "Cooked it": one time somebody made a recipe,
    with how it turned out. Private to whoever cooked it, so a recipe can
    say "last cooked 3 weeks ago, 4 stars - needs more lemon"."""
    user = models.ForeignKey(User, on_delete=models.CASCADE,
                             related_name='recipe_cooks')
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE,
                               related_name='cooks')
    cooked_on = models.DateField()
    rating = models.PositiveSmallIntegerField(null=True, blank=True)
    note = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'recipe_cooks'
        ordering = ['-cooked_on', '-created_at']

    def __str__(self):
        return '%s cooked %s on %s' % (self.user, self.recipe_id,
                                       self.cooked_on)


class PantryStaple(models.Model):
'''),
    ]),
    (os.path.join('pages', 'templates', 'passport_management.html'), [
        (r'''<tbody>
    {% for passport in passports %}
    <tr>
        <td data-label="Holder" data-sort-key="holder" data-sort-value="{{ passport.holder_name }}">{{ passport.holder_name }}</td>
        <td data-label="Type" data-sort-key="doc-type" data-sort-value="{{ passport.document_type }}">
''',
         r'''<tbody>
    {% for passport in passports %}
    <tr data-remind-for="{{ passport.id }}" data-remind="{{ passport.remind_months|default_if_none:'' }}">
        <td data-label="Holder" data-sort-key="holder" data-sort-value="{{ passport.holder_name }}">{{ passport.holder_name }}</td>
        <td data-label="Type" data-sort-key="doc-type" data-sort-value="{{ passport.document_type }}">
'''),
        (r'''            <label for="expiry_date"><strong>Expiry Date:</strong></label>
            <input type="date" class="form-control" id="expiry_date" name="expiry_date">
          </div>
          <div class="form-group">
''',
         r'''            <label for="expiry_date"><strong>Expiry Date:</strong></label>
            <input type="date" class="form-control" id="expiry_date" name="expiry_date">
          </div>
          {# DC-1, 12 Nov 2026 - an earlier reminder, for slow renewals. #}
          <div class="form-group">
            <label for="remind_months"><strong>Remind me:</strong></label>
            <select class="form-control" id="remind_months" name="remind_months">
              <option value="">6 months before (usual)</option>
              {% for value, label in remind_choices %}
              <option value="{{ value }}">{{ label }}</option>
              {% endfor %}
            </select>
          </div>
          <div class="form-group">
'''),
        (r'''    document.getElementById('passport_id').value = '';
    document.getElementById('form_action').value = 'add';
    document.getElementById('addEditModalLabel').textContent = 'Add New Passport/ID';
    document.getElementById('submitBtnText').textContent = 'Save';
''',
         r'''    document.getElementById('passport_id').value = '';
    document.getElementById('form_action').value = 'add';
    document.getElementById('remind_months').value = '';
    document.getElementById('addEditModalLabel').textContent = 'Add New Passport/ID';
    document.getElementById('submitBtnText').textContent = 'Save';
'''),
        (r'''    document.getElementById('expiry_date').value = expiryDate;
    document.getElementById('status').value = status;
    document.getElementById('addEditModalLabel').textContent = 'Edit Passport/ID Information';
    document.getElementById('submitBtnText').textContent = 'Update';
''',
         r'''    document.getElementById('expiry_date').value = expiryDate;
    document.getElementById('status').value = status;
    // DC-1 - the earlier reminder, read from the row rather than added to
    // the long argument list every Edit button already carries.
    var remindRow = document.querySelector('[data-remind-for="' + passportId + '"]');
    document.getElementById('remind_months').value = remindRow ? remindRow.getAttribute('data-remind') : '';
    document.getElementById('addEditModalLabel').textContent = 'Edit Passport/ID Information';
    document.getElementById('submitBtnText').textContent = 'Update';
'''),
    ]),
    (os.path.join('pages', 'templates', 'view_recipe.html'), [
        (r'''        border-radius: 12px;
        width: 100%;
    }

''',
         r'''        border-radius: 12px;
        width: 100%;
        box-sizing: border-box; /* DR-1: the padding pushed it 36px past a phone's edge */
    }

'''),
        (r'''}

</style>

''',
         r'''}


/* RC-3, 12 Nov 2026 - Cook mode and Cooked it. */
.cm-open { display: inline-flex; align-items: center; gap: 8px; min-height: 44px; margin: 0 0 12px; padding: 0 18px; border-radius: 22px; border: 1px solid var(--alv-accent); background: none; color: var(--alv-accent-ink); font-weight: 600; cursor: pointer; }
.cm-screen { position: fixed; inset: 0; z-index: 2000; display: flex; flex-direction: column; gap: 20px; padding: 24px 20px calc(24px + env(safe-area-inset-bottom)); background: var(--alv-paper); color: var(--alv-ink); overflow-y: auto; }
.cm-screen[hidden] { display: none; }
body.cm-on { overflow: hidden; }
.cm-top { display: flex; justify-content: space-between; align-items: center; }
.cm-count { font-weight: 600; color: var(--alv-ink-soft); }
.cm-close { width: 48px; height: 48px; border: 0; background: none; font-size: 32px; line-height: 1; color: var(--alv-ink); cursor: pointer; }
.cm-group { font-size: 15px; font-weight: 600; color: var(--alv-accent-ink); min-height: 1em; }
.cm-text { flex: 1; font-size: 26px; line-height: 1.45; }
.cm-timer-btn { width: 100%; min-height: 56px; border-radius: 28px; border: 2px solid var(--alv-accent); background: none; color: var(--alv-accent-ink); font-size: 18px; font-weight: 600; cursor: pointer; }
.cm-timer-btn.is-done { border-color: var(--alv-bad); color: var(--alv-bad-ink); }
.cm-nav { display: flex; gap: 12px; }
.cm-nav button { flex: 1; min-height: 56px; border-radius: 28px; font-size: 18px; font-weight: 600; cursor: pointer; }
.cm-prev { border: 1px solid var(--alv-line); background: none; color: var(--alv-ink); }
.cm-next { border: 0; background: var(--alv-accent); color: var(--alv-on-accent); }
.cm-prev:disabled { opacity: .4; }
.cooked-section { margin-top: 24px; }
.cooked-summary { color: var(--alv-ink-soft); margin: 0 0 12px; }
.cooked-form { display: flex; flex-wrap: wrap; align-items: center; gap: 10px; margin-bottom: 12px; }
.cooked-stars { display: flex; gap: 2px; }
.cooked-star { margin: 0; cursor: pointer; min-width: 36px; min-height: 44px; display: inline-flex; align-items: center; justify-content: center; font-size: 26px; color: var(--alv-line); }
.cooked-star input { position: absolute; opacity: 0; width: 1px; height: 1px; }
.cooked-stars:hover .cooked-star, .cooked-star:has(input:checked), .cooked-star:has(~ .cooked-star input:checked) { color: var(--alv-spice); }
.cooked-stars .cooked-star:hover ~ .cooked-star { color: var(--alv-line); }
.cooked-note { flex: 1 1 220px; width: auto; }
.cooked-date { width: auto; }
.cooked-list { list-style: none; margin: 0; padding: 0; }
.cooked-list li { display: flex; align-items: center; gap: 12px; min-height: 44px; border-top: 1px solid var(--alv-line-soft); }
.cooked-when { min-width: 96px; font-weight: 600; }
.cooked-rate { min-width: 32px; color: var(--alv-spice-ink); }
.cooked-text { flex: 1; color: var(--alv-ink-soft); }
.cooked-del { margin: 0; }
.cooked-x { width: 44px; height: 44px; border: 0; background: none; font-size: 22px; color: var(--alv-ink-soft); cursor: pointer; }
</style>

'''),
        (r'''                <i class="fas fa-tasks"></i> Instructions
            </h2>

            {% regroup instructions by instruction_group as instruction_groups %}
''',
         r'''                <i class="fas fa-tasks"></i> Instructions
            </h2>
            {# RC-3, 12 Nov 2026 - COOK MODE: one step at a time, big text, #}
            {# the screen kept on, and a timer on any step with minutes.    #}
            {% if instructions %}
            <button type="button" class="cm-open" data-cook-open><i class="fas fa-play"></i> Cook mode</button>
            {% endif %}

            {% regroup instructions by instruction_group as instruction_groups %}
'''),
        (r'''
                    {% for instruction in group.list %}
                    <div class="instruction-step">
                        <div class="step-number">{{ instruction.step_number }}</div>
                        <div class="step-content">
''',
         r'''
                    {% for instruction in group.list %}
                    <div class="instruction-step" data-cook-step data-minutes="{{ instruction.time_estimate|default_if_none:'' }}" data-group="{{ group.grouper|default_if_none:'' }}">
                        <div class="step-number">{{ instruction.step_number }}</div>
                        <div class="step-content">
'''),
        (r'''            {% endfor %}
        </div>
    </div>

</div>

<!-- ============================================================
''',
         r'''            {% endfor %}
        </div>

        {# RC-3, 12 Nov 2026 - COOKED IT: your own record of this recipe,  #}
        {# with a rating and a note. Nobody else sees it.                  #}
        <div class="cooked-section" id="cooked" data-cooked>
            <h2 class="recipe-section-title">
                <i class="fas fa-utensils"></i> Cooked it
            </h2>
            {% if last_cook %}
            <p class="cooked-summary" data-cooked-summary>Last cooked {% if last_cook.cooked_on == today %}today{% else %}{{ last_cook.cooked_on|timesince:today }} ago{% endif %}{% if cooks_total > 1 %} &middot; {{ cooks_total }} times{% endif %}{% if cook_avg %} &middot; {{ cook_avg }}&#9733; on average{% endif %}{% if last_cook.note %} &middot; &ldquo;{{ last_cook.note }}&rdquo;{% endif %}</p>
            {% else %}
            <p class="cooked-summary">Not cooked yet. Made it? Record it here - how it turned out helps next time.</p>
            {% endif %}
            <form method="post" action="{% url 'recipe_cooked' recipe.recipe_id %}" class="cooked-form">
                {% csrf_token %}
                <div class="cooked-stars" role="radiogroup" aria-label="How it turned out">
                    {% for n in "12345" %}<label class="cooked-star"><input type="radio" name="rating" value="{{ n }}"><span aria-hidden="true">&#9733;</span><span class="sr-only">{{ n }} star{{ n|pluralize }}</span></label>{% endfor %}
                </div>
                <input type="text" name="note" maxlength="200" class="form-control cooked-note" placeholder="A note - needs more lemon" aria-label="A note">
                <input type="date" name="cooked_on" value="{{ today|date:'Y-m-d' }}" max="{{ today|date:'Y-m-d' }}" class="form-control cooked-date" aria-label="Cooked on">
                <button type="submit" class="btn action-primary">I cooked it</button>
            </form>
            {% if cooks %}
            <ul class="cooked-list">
                {% for c in cooks %}
                <li><span class="cooked-when">{{ c.cooked_on|date:"j M Y" }}</span><span class="cooked-rate">{% if c.rating %}{{ c.rating }}&#9733;{% endif %}</span><span class="cooked-text">{{ c.note }}</span>
                    <form method="post" action="{% url 'recipe_cooked' recipe.recipe_id %}" class="cooked-del">{% csrf_token %}<input type="hidden" name="delete" value="{{ c.pk }}"><button type="submit" class="cooked-x" aria-label="Remove {{ c.cooked_on|date:'j M Y' }}">&times;</button></form></li>
                {% endfor %}
            </ul>
            {% endif %}
        </div>
    </div>

</div>

{# RC-3 - the cook-mode screen, filled from the steps above by script. #}
<div class="cm-screen" data-cook-screen hidden role="dialog" aria-modal="true" aria-label="Cook mode">
    <div class="cm-top"><span class="cm-count" data-cook-count></span><button type="button" class="cm-close" data-cook-close aria-label="Close cook mode">&times;</button></div>
    <div class="cm-group" data-cook-group></div>
    <div class="cm-text" data-cook-text></div>
    <div class="cm-timer" data-cook-timer hidden><button type="button" class="cm-timer-btn" data-cook-timer-btn></button></div>
    <div class="cm-nav"><button type="button" class="cm-prev" data-cook-prev>&larr; Back</button><button type="button" class="cm-next" data-cook-next>Next &rarr;</button></div>
</div>
<script>
(function () {
    var open = document.querySelector('[data-cook-open]');
    var scr = document.querySelector('[data-cook-screen]');
    if (!open || !scr) return;
    var steps = [].slice.call(document.querySelectorAll('[data-cook-step]')).map(function (el) {
        var t = el.querySelector('.step-text');
        return { text: t ? t.textContent.trim() : '', mins: parseInt(el.getAttribute('data-minutes'), 10) || 0, group: el.getAttribute('data-group') || '' };
    });
    var i = 0, lock = null, tick = null, left = 0;
    var $ = function (s) { return scr.querySelector(s); };
    function wake() { if (navigator.wakeLock) navigator.wakeLock.request('screen').then(function (l) { lock = l; }).catch(function () {}); }
    function fmt(s) { var m = Math.floor(s / 60), x = s % 60; return m + ':' + (x < 10 ? '0' : '') + x; }
    function stopTimer() { if (tick) { clearInterval(tick); tick = null; } }
    function draw() {
        var s = steps[i];
        $('[data-cook-count]').textContent = 'Step ' + (i + 1) + ' of ' + steps.length;
        $('[data-cook-group]').textContent = s.group;
        $('[data-cook-text]').textContent = s.text;
        $('[data-cook-prev]').disabled = i === 0;
        $('[data-cook-next]').textContent = i === steps.length - 1 ? 'Done' : 'Next →';
        stopTimer();
        var box = $('[data-cook-timer]'), btn = $('[data-cook-timer-btn]');
        if (s.mins) { box.hidden = false; btn.textContent = 'Start ' + s.mins + ' min timer'; btn.className = 'cm-timer-btn'; }
        else { box.hidden = true; }
    }
    $('[data-cook-timer-btn]').addEventListener('click', function () {
        var btn = this, s = steps[i];
        if (tick) { stopTimer(); btn.textContent = 'Start ' + s.mins + ' min timer'; return; }
        left = s.mins * 60; btn.textContent = fmt(left) + ' - tap to stop'; btn.className = 'cm-timer-btn is-running';
        tick = setInterval(function () {
            left -= 1;
            if (left <= 0) {
                stopTimer(); btn.textContent = 'Time is up'; btn.className = 'cm-timer-btn is-done';
                if (navigator.vibrate) { try { navigator.vibrate([300, 150, 300, 150, 300]); } catch (e) {} }
                try { var a = new (window.AudioContext || window.webkitAudioContext)(), o = a.createOscillator(), g = a.createGain(); o.frequency.value = 880; o.connect(g); g.connect(a.destination); g.gain.value = 0.2; o.start(); o.stop(a.currentTime + 0.8); } catch (e) {}
                return;
            }
            btn.textContent = fmt(left) + ' - tap to stop';
        }, 1000);
    });
    function show() { i = 0; scr.hidden = false; document.body.classList.add('cm-on'); wake(); draw(); }
    function hide() { stopTimer(); scr.hidden = true; document.body.classList.remove('cm-on'); if (lock) { try { lock.release(); } catch (e) {} lock = null; } }
    open.addEventListener('click', show);
    $('[data-cook-close]').addEventListener('click', hide);
    $('[data-cook-prev]').addEventListener('click', function () { if (i > 0) { i -= 1; draw(); } });
    $('[data-cook-next]').addEventListener('click', function () { if (i < steps.length - 1) { i += 1; draw(); } else { hide(); } });
    document.addEventListener('keydown', function (e) {
        if (scr.hidden) return;
        if (e.key === 'Escape') hide();
        else if (e.key === 'ArrowRight') $('[data-cook-next]').click();
        else if (e.key === 'ArrowLeft') $('[data-cook-prev]').click();
    });
    document.addEventListener('visibilitychange', function () { if (!scr.hidden && document.visibilityState === 'visible') wake(); });
})();
</script>

<!-- ============================================================
'''),
    ]),
    (os.path.join('pages', 'urls.py'), [
        (r'''    path('recipe/check-name/', views.recipe_check_name, name='recipe_check_name'),
    path('recipe/<int:recipe_id>/favourite/', views.toggle_recipe_favourite, name='toggle_recipe_favourite'),
    path('recipes/<int:recipe_id>/suggest_modification/', views.suggest_recipe_modification, name='suggest_recipe_modification'),
    # Meal Planning URLs
''',
         r'''    path('recipe/check-name/', views.recipe_check_name, name='recipe_check_name'),
    path('recipe/<int:recipe_id>/favourite/', views.toggle_recipe_favourite, name='toggle_recipe_favourite'),
    # RC-3, 12 Nov 2026 - Cooked it, with a rating and a note.
    path('recipe/<int:recipe_id>/cooked/', views.recipe_cooked, name='recipe_cooked'),
    path('recipes/<int:recipe_id>/suggest_modification/', views.suggest_recipe_modification, name='suggest_recipe_modification'),
    # Meal Planning URLs
'''),
    ]),
    (os.path.join('pages', 'views', 'passports.py'), [
        (r'''@login_required
@permission_required('auth.can_access_passports', raise_exception=True)
def passport_management(request):
    # Guarantee the current user has a workspace before any data operation.
''',
         r'''@login_required
@permission_required('auth.can_access_passports', raise_exception=True)
def _remind(request):
    """DC-1, 12 Nov 2026 - 9 or 12 months, or None for the usual six."""
    try:
        v = int(request.POST.get('remind_months') or 0)
    except ValueError:
        return None
    return v if v in dict(Passport.REMIND_CHOICES) else None


def passport_management(request):
    # Guarantee the current user has a workspace before any data operation.
'''),
        (r'''                    status=status,
                    document_file=document_file,
                )
                messages.success(request, f'Passport/ID for {holder_name} added successfully!')
''',
         r'''                    status=status,
                    document_file=document_file,
                    remind_months=_remind(request),
                )
                messages.success(request, f'Passport/ID for {holder_name} added successfully!')
'''),
        (r'''            passport.expiry_date = request.POST.get('expiry_date') or None
            passport.status = request.POST.get('status')

            # Update file if a new one is uploaded
''',
         r'''            passport.expiry_date = request.POST.get('expiry_date') or None
            passport.status = request.POST.get('status')
            passport.remind_months = _remind(request)

            # Update file if a new one is uploaded
'''),
        (r'''        'holders': holders,
        'doc_types': Passport.DOCUMENT_TYPE_CHOICES,
        'statuses': Passport.STATUS_CHOICES,
        'countries': countries,
''',
         r'''        'holders': holders,
        'doc_types': Passport.DOCUMENT_TYPE_CHOICES,
        'remind_choices': Passport.REMIND_CHOICES,
        'statuses': Passport.STATUS_CHOICES,
        'countries': countries,
'''),
    ]),
    (os.path.join('pages', 'views', 'recipes', 'recipe_crud.py'), [
        (r'''from django.template.loader import get_template
from django.utils.text import slugify
from django.views.decorators.http import require_POST

''',
         r'''from django.template.loader import get_template
from django.utils.text import slugify
from django.utils import timezone
from django.views.decorators.http import require_POST

'''),
        (r'''        'has_next': page_obj.has_next(),
        'next_page': page_obj.next_page_number() if page_obj.has_next() else None,
        'ingredient_categories': IngredientCategory.objects.prefetch_related('ingredient_set').all().order_by('name'),
        'all_recipes_for_book': json.dumps(all_recipes_for_book),
        # Step 3 - nutrition sort
''',
         r'''        'has_next': page_obj.has_next(),
        'next_page': page_obj.next_page_number() if page_obj.has_next() else None,
        # RC-3, 12 Nov 2026 - 'ingredient_categories' went: every ingredient,
        # prefetched on every visit, for a template that never read it.
        'all_recipes_for_book': json.dumps(all_recipes_for_book),
        # Step 3 - nutrition sort
'''),
        (r'''        'show_ai_suggestions': show_ai_suggestions,
    }

    return render(request, 'view_recipe.html', context)
''',
         r'''        'show_ai_suggestions': show_ai_suggestions,
    }
    # RC-3, 12 Nov 2026 - "Cooked it": your own history with this recipe.
    from pages.models import RecipeCook
    cooks = list(RecipeCook.objects.filter(recipe=recipe, user=request.user))
    rated = [c.rating for c in cooks if c.rating]
    context.update({
        'cooks': cooks[:6],
        'cooks_total': len(cooks),
        'last_cook': cooks[0] if cooks else None,
        'cook_avg': (round(sum(rated) / len(rated), 1) if rated else None),
        'today': timezone.localdate(),
    })

    return render(request, 'view_recipe.html', context)
'''),
    ]),
    (os.path.join('pages', 'views', 'recipes', 'recipe_extras.py'), [
        (r'''from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

''',
         r'''from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

'''),
        (r'''

@login_required
@permission_required('auth.can_edit_recipes', raise_exception=True)
@require_POST
def toggle_recipe_favourite(request, recipe_id):
''',
         r'''

@login_required
@permission_required('auth.can_access_recipes', raise_exception=True)
@require_POST
def recipe_cooked(request, recipe_id):
    """RC-3, 12 Nov 2026 - "Cooked it", with a rating and a note. Anyone
    who can open recipes can keep their own record; nobody else sees it."""
    import datetime as _dt
    from django.utils import timezone
    from pages.models import Recipe, RecipeCook
    recipe = get_object_or_404(Recipe, recipe_id=recipe_id)
    if request.POST.get('delete'):
        RecipeCook.objects.filter(pk=request.POST.get('delete'),
                                  user=request.user, recipe=recipe).delete()
        return redirect('%s#cooked' % reverse('view_recipe',
                                              args=[recipe_id]))
    today = timezone.localdate()
    try:
        when = _dt.date.fromisoformat(request.POST.get('cooked_on') or '')
    except ValueError:
        when = today
    when = min(when, today)
    try:
        rating = int(request.POST.get('rating') or 0)
    except ValueError:
        rating = 0
    RecipeCook.objects.create(
        user=request.user, recipe=recipe, cooked_on=when,
        rating=rating if 1 <= rating <= 5 else None,
        note=(request.POST.get('note') or '').strip()[:200])
    messages.success(request, 'Saved - cooked %s.' % (
        'today' if when == today else when.strftime('%d %b')))
    return redirect('%s#cooked' % reverse('view_recipe', args=[recipe_id]))


@login_required
@permission_required('auth.can_edit_recipes', raise_exception=True)
@require_POST
def toggle_recipe_favourite(request, recipe_id):
'''),
    ]),
    (os.path.join('test_pair_contrast.py'), [
        (r'''MARK = 'B-4b, 8 Oct 2026'

EXPECT_PAIRS = 750   # CR-2, 27 Oct 2026 - the receipt email pop-up, on Receipts and on Receipt Details: the message box and the Printed warning each set a fill and its ink, pairs base already uses.   # (was 746)   # ES-11, 26 Oct 2026 - the yellow signed-leases bar left Home and Notifications, and with it .lsa-strip's fill+ink pair on each page.   # (was 748)   # ES-9, 26 Oct 2026 - Home's Waiting for you icon chip, .ins-ic--wait, sets the warn-soft fill and warn-ink together, a pair base already uses.   # (was 747)   # ES-7, 25 Oct 2026 - two notes set a fill and an ink together: .hm-note on the Signature and Stamp screen and .ls-saved-note on the signing page, both on the accent pair this table already knows.   # (was 745)   # ES-6, 25 Oct 2026 - three more rules in ES-6's pages set a fill and an ink together, measured by this census on the full tree.   # (was 742)   # ES-4, 24 Oct 2026 - eleven in the public signing pages' own stylesheet. A standalone page cannot inherit a surface, so every one it draws sets both halves of the pair itself - which is exactly why this census asks about them.   # (was 731)   # ES-3a, 23 Oct 2026 - the lease signing register: three signer dots mirroring the good, bad and neutral pills, and the waiting-on-you note. Four rules, no new pairings.   # (was 727)   # MN-2, 21 Oct 2026 - the Saved Menus dialog gains the preset row CP-2 built for Copy, and .mn-preset[aria-pressed=true] sets a fill and an ink together exactly as .cp-preset does. One more pair, of tokens this table already knows.   # (was 726)   # RG-2, 21 Oct 2026 - two more rules set a fill and an ink together: the date field, which wears the paper token on the ink one like every other field in the system, and the line explaining the second Print press, which sits on the surface wash.   # (was 724)   # RG-1, 21 Oct 2026 - the printed sheet is drawn again from four layouts, and five more of its rules set a fill and an ink together: the pill in its three states, the today marker and the dimmed cell. Every one is a token pair this table already knows.   # (was 719)   # PP-1, 20 Oct 2026 - the printable plan sets
# both a ground and an ink on six rules. All house pairs off base's
# own tokens, so the AA table below is untouched and the gross count
''',
         r'''MARK = 'B-4b, 8 Oct 2026'

EXPECT_PAIRS = 752   # RC-3, 12 Nov 2026 - cook mode on the recipe page: the full-screen step view sets the paper fill and its ink, and its Next button the accent fill and the on-accent ink. Two rules, pairs base already uses.   # (was 750)   # CR-2, 27 Oct 2026 - the receipt email pop-up, on Receipts and on Receipt Details: the message box and the Printed warning each set a fill and its ink, pairs base already uses.   # (was 746)   # ES-11, 26 Oct 2026 - the yellow signed-leases bar left Home and Notifications, and with it .lsa-strip's fill+ink pair on each page.   # (was 748)   # ES-9, 26 Oct 2026 - Home's Waiting for you icon chip, .ins-ic--wait, sets the warn-soft fill and warn-ink together, a pair base already uses.   # (was 747)   # ES-7, 25 Oct 2026 - two notes set a fill and an ink together: .hm-note on the Signature and Stamp screen and .ls-saved-note on the signing page, both on the accent pair this table already knows.   # (was 745)   # ES-6, 25 Oct 2026 - three more rules in ES-6's pages set a fill and an ink together, measured by this census on the full tree.   # (was 742)   # ES-4, 24 Oct 2026 - eleven in the public signing pages' own stylesheet. A standalone page cannot inherit a surface, so every one it draws sets both halves of the pair itself - which is exactly why this census asks about them.   # (was 731)   # ES-3a, 23 Oct 2026 - the lease signing register: three signer dots mirroring the good, bad and neutral pills, and the waiting-on-you note. Four rules, no new pairings.   # (was 727)   # MN-2, 21 Oct 2026 - the Saved Menus dialog gains the preset row CP-2 built for Copy, and .mn-preset[aria-pressed=true] sets a fill and an ink together exactly as .cp-preset does. One more pair, of tokens this table already knows.   # (was 726)   # RG-2, 21 Oct 2026 - two more rules set a fill and an ink together: the date field, which wears the paper token on the ink one like every other field in the system, and the line explaining the second Print press, which sits on the surface wash.   # (was 724)   # RG-1, 21 Oct 2026 - the printed sheet is drawn again from four layouts, and five more of its rules set a fill and an ink together: the pill in its three states, the today marker and the dimmed cell. Every one is a token pair this table already knows.   # (was 719)   # PP-1, 20 Oct 2026 - the printable plan sets
# both a ground and an ink on six rules. All house pairs off base's
# own tokens, so the AA table below is untouched and the gross count
'''),
    ]),
    (os.path.join('test_surface_border.py'), [
        (r'''# the 96 it settled.
N_CONVERT, N_PAGES, N_FALLBACK, N_OTHER = 78, 43, 3, 95   # RG-1, 21 Oct 2026 - N_OTHER 94 -> 95: a leftover pill is filled with the panel wash, which is a BACKGROUND use of the token and so one more of the uses F2a settled and this suite refuses to re-open.
N_GAINED = 85   # PK-1, 30 Oct 2026 - one more: the hairline under each passkey row on My Profile   # (was 84)   # PC-1, 28 Oct 2026 - one more: the property strip above two tenants on Generate's pop-up, a surface with the house line round it   # (was 83)   # VR-1, 21 Oct 2026 - four more: the row hairlines in the cooking schedule readout on view_recipe, which were a hand-mixed 7 per cent black and are the house line token now. Measured at dE 1.75 against what that black actually painted over the panel - under the 2.0 a trained eye can just detect, so nothing on the screen moved.   # (was 79)   # RG-1, 21 Oct 2026 - one more: the frame round the whole sheet. PP-1 drew a frame per week and a rule under each week label; this draws one frame and one weekday row, and the net is a single rule.   # (was 78)   # PP-1, 20 Oct 2026 - the printable plan draws two borders off var(--alv-line): the frame around a week and the rule under its label. Both are borders on a tinted surface, which is what base's own token note says the token is for.   # (was 76)   # DT-1, 16 Oct 2026 - six of the rules this round deletes carried the border token. base draws those borders now, so the count falls by exactly the copies that went.   # (was 82)

passed = failed = skipped = 0
''',
         r'''# the 96 it settled.
N_CONVERT, N_PAGES, N_FALLBACK, N_OTHER = 78, 43, 3, 95   # RG-1, 21 Oct 2026 - N_OTHER 94 -> 95: a leftover pill is filled with the panel wash, which is a BACKGROUND use of the token and so one more of the uses F2a settled and this suite refuses to re-open.
N_GAINED = 86   # DR-1, 12 Nov 2026 - one more: the outline of the Back button in a recipe's Cook mode, the house line round a plain button   # (was 85)   # PK-1, 30 Oct 2026 - one more: the hairline under each passkey row on My Profile   # (was 84)   # PC-1, 28 Oct 2026 - one more: the property strip above two tenants on Generate's pop-up, a surface with the house line round it   # (was 83)   # VR-1, 21 Oct 2026 - four more: the row hairlines in the cooking schedule readout on view_recipe, which were a hand-mixed 7 per cent black and are the house line token now. Measured at dE 1.75 against what that black actually painted over the panel - under the 2.0 a trained eye can just detect, so nothing on the screen moved.   # (was 79)   # RG-1, 21 Oct 2026 - one more: the frame round the whole sheet. PP-1 drew a frame per week and a rule under each week label; this draws one frame and one weekday row, and the net is a single rule.   # (was 78)   # PP-1, 20 Oct 2026 - the printable plan draws two borders off var(--alv-line): the frame around a week and the rule under its label. Both are borders on a tinted surface, which is what base's own token note says the token is for.   # (was 76)   # DT-1, 16 Oct 2026 - six of the rules this round deletes carried the border token. base draws those borders now, so the count falls by exactly the copies that went.   # (was 82)

passed = failed = skipped = 0
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
    raise SystemExit('DC-1 REFUSED: %s' % msg)


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
    if "'test_doc_recipe.py'" in read(pq):
        print('DC-1 already applied.')
        return 0
    if "'test_wellness_twentyfour.py'" not in read(pq):
        refuse('Release 70 is not applied - this round registers after it.')
    for rel in CREATES:
        if not os.path.isfile(os.path.join(root, *rel.split('/'))):
            refuse('%s is missing - it ships with this patcher; copy the '
                   'new wellness files and the suite in first.' % rel)

    for rel, pairs in SWAPS:
        pth = os.path.join(root, rel)
        t = read(pth)
        for i, (was, now) in enumerate(pairs):
            t = swap(t, was, now, '%s (swap %d of %d)'
                     % (rel, i + 1, len(pairs)))
        out[pth] = t

    if CHECK:
        print('DC-1 --check: %d file(s) would change, none written; %d '
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
    print('DC-1 applied - documents: six types, Remind me; recipes: Cooked it, cook mode.')
    print('      MIGRATIONS 0117 and 0118 - run migrate before pushing.')
    print('      %d file(s) written, backed up to %s' % (len(out), SUFFIX))
    print('      %d file(s) ship with it, wired in rather than written'
          % len(CREATES))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
