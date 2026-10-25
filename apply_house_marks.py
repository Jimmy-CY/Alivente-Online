# -*- coding: utf-8 -*-
"""apply_house_marks.py - round ES-7, 25 Oct 2026.

HIS SIGNATURE AND THE COMPANY STAMP - AND WHAT A TENANT IS SHOWN.

His decisions of 25 October, all built here:

    HOUSE MARKS. His signature (printed blue) and the company stamp -
    "ALIVENTE LIMITED" only, the company number left off - placed on the
    signature page ONLY when he signs for Alivente himself, decided by
    the signed-in account and never by a typed name. Stored securely: a
    table of PNG bytes in the database (house_marks), never media, never
    served by any URL; uploaded, replaced or removed on a superuser-only
    screen under Administration > System > Signature and Stamp.

    "USE MY SAVED SIGNATURE" beside Draw and Type, shown only to him and
    chosen by default. The stamp goes on whenever he signs as himself,
    however he signs. Both are COPIED onto his party at the moment he
    signs, so replacing the stored mark later never changes a lease
    already signed. The record says "saved"; the printed page says only
    "Signed", as it does for drawn and typed.

    THE SIGNATURE PAGE in Cyprus time with the zone named, and its
    history in four aligned columns (When / What / Who / From).

    THE ADDRESS, NEVER THE INTERNAL NAME. Every email and page a tenant
    sees names the property by its address (props.tenant_address, built
    the way Generate Lease builds it); with no address recorded, no
    place is named at all.

    THE EMAILS ARE BRANDED, SMALL, WITH NO CONTACT DETAILS - his two
    answers of 25 October. One helper (services/lease_email.py) sends
    every e-signing email as plain text plus a small HTML twin with the
    Alivente logo inline, the same logo the invoice emails use.

    LINKS STAY OPEN TO THE END OF THE DAY they name, Cyprus time - from
    Send and from Extend - and the email says so. Reminders keep to his
    rule: day 3 and the day before the closing date, never on it.

AND THE LIVE FIX OF THE SAME DAY rides along in this round's suite: the
signing page's referrer policy (shipped in Release 16) gets a sentinel
and a real-browser check of the Origin the form sends.

PINS THAT MOVE WITH IT are listed in the SWAPS below, each with why.

Stands on ES-6c. Idempotent. Every edited file backed up to
.bak_housemarks; four files ship new and are wired in, not written.
"""
import os
import re
import sys

SUFFIX = '.bak_housemarks'
MARK = 'ES-7, 25 Oct 2026'
CHECK = False

VIEW = os.path.join('pages', 'views', 'house_marks.py')
PAGE = os.path.join('pages', 'templates', 'house_marks.html')
MIG = os.path.join('pages', 'migrations', '0108_es7_house_marks.py')
MAILER = os.path.join('pages', 'services', 'lease_email.py')
CREATES = (VIEW, PAGE, MIG, MAILER)

PS1 = 'Push-PendingChanges.ps1'
TREE = 'alv_tree.py'
ROUNDS = 'alv_rounds.py'
WD = 'test_waiting_down.py'

# ------------------------------------------------------------- THE SWAPS
# One entry per file. Each WAS is the smallest block of the file as
# Release 16 left it that occurs exactly once.
SWAPS = [
    (os.path.join('pages', 'models.py'), [
        (r'''    def __str__(self):
        return self.prop_name or f"Property {self.prop_id}"

    class Meta:
''',
         r'''    def __str__(self):
        return self.prop_name or f"Property {self.prop_id}"

    # THE ADDRESS A TENANT SEES - ES-7, 25 Oct 2026. His instruction: the
    # property NAME is internal ("Apolloneon - Demetri") and must never
    # reach a tenant. Built the way Generate Lease builds the address it
    # writes into the lease, so the email, the signing page and the lease
    # itself describe the place in the same words. Empty when no address
    # is recorded - and then a tenant sees no place at all, never the name.
    ADDRESS_FIELDS = ('prop_address1', 'prop_address2', 'prop_suburb',
                      'prop_city', 'prop_province', 'prop_country',
                      'prop_pcode')

    @property
    def tenant_address(self):
        return ', '.join(p.strip() for p in
                         (getattr(self, f) or '' for f in self.ADDRESS_FIELDS)
                         if p and p.strip())

    @property
    def tenant_address_short(self):
        """First line and city - short enough for an email subject."""
        return ', '.join(p.strip() for p in
                         (self.prop_address1 or '', self.prop_city or '')
                         if p and p.strip())

    class Meta:
'''),
        (r'''                if not p.signed_at and not p.declined_at]

    def window_start(self):
        """When the current signing window opened - ES-6, 25 Oct 2026.
''',
         r'''                if not p.signed_at and not p.declined_at]

    @classmethod
    def closing_moment(cls, days, now=None):
        """The last moment a link works: END of the day, Cyprus time.

        ES-7, 25 Oct 2026, his decision. A link sent at 15:00 on the 24th
        used to die at 15:00 on the 31st while the email said only
        "31 October", so a tenant signing that evening found it closed.
        Now it closes at 23:59:59 local time on the date the email names.
        Used by the Send screen and by Extend, so both say the same.
        """
        import datetime as _dt
        day = timezone.localdate(now or timezone.now()) + \
            _dt.timedelta(days=days)
        return timezone.make_aware(_dt.datetime.combine(
            day, _dt.time(23, 59, 59)))

    def _last_reminder_at(self):
        """The start of the day before the closing date, local time.

        ES-7 - with links open to the end of the day, "the day before it
        lapses" measured back 24 hours from 23:59 would land on the last
        day itself. Counted from the start of the previous day, it stays
        the day before.
        """
        import datetime as _dt
        close_day = timezone.localtime(self.expires_at).date()
        return timezone.make_aware(_dt.datetime.combine(
            close_day - _dt.timedelta(days=self.LAST_REMINDER_DAYS_BEFORE),
            _dt.time(0, 0)))

    def window_start(self):
        """When the current signing window opened - ES-6, 25 Oct 2026.
'''),
        (r'''            return None
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

''',
         r'''            return None
        due = None
        close_day = timezone.localtime(self.expires_at).date()
        for at in (start + timezone.timedelta(days=self.FIRST_REMINDER_DAY),
                   self._last_reminder_at()):
            # NEVER ON THE CLOSING DAY ITSELF - ES-7, 25 Oct 2026. With
            # the link open all of that day, "day 3" of a three-day window
            # would fall on the deadline, the day after the "day before"
            # reminder: two emails on consecutive days, which is not his
            # rule. A reminder has to land on a day BEFORE the closing date.
            if not (start < at
                    and timezone.localtime(at).date() < close_day):
                continue
            if now >= at and (self.last_reminder_at is None
                              or self.last_reminder_at < at):
                # CALENDAR DAYS, LOCAL - ES-7, 25 Oct 2026. With links
                # open to the end of the day, the last reminder is counted
                # from midnight, so measuring in hours would call the day
                # before a 14-day deadline "day 12". People count days.
                due = (timezone.localtime(at).date()
                       - timezone.localtime(start).date()).days
        return due

'''),
        (r'''    KIND_DRAWN = 'drawn'
    KIND_TYPED = 'typed'
    KIND_CHOICES = [(KIND_DRAWN, 'Drawn'), (KIND_TYPED, 'Typed')]

    party_id = models.AutoField(primary_key=True)
''',
         r'''    KIND_DRAWN = 'drawn'
    KIND_TYPED = 'typed'
    # ES-7, 25 Oct 2026 - HIS SAVED SIGNATURE, applied when he signs as
    # himself and chooses it. Recorded as its own kind so the record says
    # how the mark got there; the printed page says only "Signed", as it
    # does for drawn and typed - his decision of 25 October.
    KIND_SAVED = 'saved'
    KIND_CHOICES = [(KIND_DRAWN, 'Drawn'), (KIND_TYPED, 'Typed'),
                    (KIND_SAVED, 'Saved signature')]

    party_id = models.AutoField(primary_key=True)
'''),
        (r'''        blank=True, null=True)
    typed_name = models.CharField(max_length=255, blank=True)

    signed_ip = models.CharField(max_length=45, blank=True)
''',
         r'''        blank=True, null=True)
    typed_name = models.CharField(max_length=255, blank=True)
    # THE HOUSE MARKS, COPIED - ES-7, 25 Oct 2026. When he signs as
    # himself the stored signature (if he chose it) and the company stamp
    # are COPIED onto this party, in the database. A copy and not a
    # pointer: replacing the stored mark next year must not change a
    # lease already signed, and the sealed page must be rebuildable from
    # the envelope alone. Never media - nothing serves these by URL.
    mark_signature = models.BinaryField(null=True, blank=True,
                                        editable=False)
    mark_stamp = models.BinaryField(null=True, blank=True, editable=False)

    signed_ip = models.CharField(max_length=45, blank=True)
'''),
        (r'''        verbose_name = 'Lease signing event'

''',
         r'''        verbose_name = 'Lease signing event'


# ==========================================================================
# HOUSE MARKS - ES-7, 25 Oct 2026
# ==========================================================================
class HouseMark(models.Model):
    """His signature and the company stamp, stored once, securely.

    HIS DECISIONS OF 25 OCTOBER. The stamp is the company NAME only
    ("ALIVENTE LIMITED" - the company number left off). Both are used
    ONLY when Demetri Manias is the signatory, decided by the signed-in
    account that signs and never by a typed name. Stored securely: in the
    database, never in media, never served by any URL, and managed by a
    superuser only.

    ONE OF EACH KIND, BELONGING TO WHOEVER UPLOADED IT. The upload screen
    is superuser-only and the owner is the uploader, so there is exactly
    one account the marks can ever be applied for. Another superuser
    uploading would REPLACE them, visibly, not add a second set.

    PNG BYTES, ALPHA KEPT. The upload screen normalises whatever it is
    given into a transparent PNG, so the sealed page never has to.
    """
    SIGNATURE = 'signature'
    STAMP = 'stamp'
    KIND_CHOICES = [(SIGNATURE, 'Signature'), (STAMP, 'Company stamp')]

    house_mark_id = models.AutoField(primary_key=True)
    kind = models.CharField(max_length=20, choices=KIND_CHOICES, unique=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE,
                              related_name='house_marks')
    image = models.BinaryField(editable=False)
    sha256 = models.CharField(max_length=64)
    width = models.PositiveIntegerField(default=0)
    height = models.PositiveIntegerField(default=0)
    uploaded_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'house_marks'
        verbose_name = 'House mark'

    def __str__(self):
        return '%s (%s)' % (self.get_kind_display(), self.owner)

    @classmethod
    def for_signer(cls, user, kind):
        """The mark's bytes if THIS user owns it, else None.

        THE ONE QUESTION THE SIGNING PAGE ASKS. Ownership is the account,
        so a name typed into "Signing for Alivente" can never reach it.
        """
        if user is None or not getattr(user, 'is_authenticated', False):
            return None
        row = cls.objects.filter(kind=kind, owner=user).first()
        return bytes(row.image) if row and row.image else None
'''),
    ]),
    (os.path.join('pages', 'services', 'lease_sealing.py'), [
        (r'''

def build_sealed(signing, parties=None, events=None):
    """The original, plus ONE appended page, as bytes.
''',
         r'''

def _when(moment, fmt):
    """A stored (UTC) moment, in the project's own time zone."""
    local = timezone.localtime(moment)
    # THE ZONE OF THAT MOMENT, not of today: a lease signed in July
    # reads EEST and one signed in January reads EET.
    return ('%s %s' % (local.strftime(fmt), local.tzname() or '')).strip()


def build_sealed(signing, parties=None, events=None):
    """The original, plus ONE appended page, as bytes.
'''),
        (r'''            if not p.signed_at:
                continue
            # THE MARK ITSELF, drawn or typed.
            box_top = y
            if p.signature_image:
                try:
                    p.signature_image.open('rb')
                    img = p.signature_image.read()
                    p.signature_image.close()
                    rect = pymupdf.Rect(56, y, 56 + 190, y + 52)
                    page.insert_image(rect, stream=_in_blue(img),
''',
         r'''            if not p.signed_at:
                continue
            # THE MARK ITSELF, drawn, typed or saved.
            box_top = y
            # A SAVED SIGNATURE - ES-7, 25 Oct 2026 - is the house mark
            # copied onto THIS party when he signed, so a later change to
            # the stored mark can never change a lease already signed.
            # It lives in the database, never in media.
            saved = (bytes(p.mark_signature)
                     if p.signature_kind == 'saved'
                     and getattr(p, 'mark_signature', None) else b'')
            if saved or p.signature_image:
                try:
                    if saved:
                        img = saved
                    else:
                        p.signature_image.open('rb')
                        img = p.signature_image.read()
                        p.signature_image.close()
                    rect = pymupdf.Rect(56, y, 56 + 190, y + 52)
                    page.insert_image(rect, stream=_in_blue(img),
'''),
        (r'''            else:
                _line(page, 56, y + 34, p.typed_name or p.name, size=13)
            page.draw_line(pymupdf.Point(56, box_top + 56),
                           pymupdf.Point(56 + 220, box_top + 56),
''',
         r'''            else:
                _line(page, 56, y + 34, p.typed_name or p.name, size=13)
            # THE COMPANY STAMP BESIDE THE HOUSE SIGNATURE - ES-7, 25 Oct
            # 2026. His decisions: "ALIVENTE LIMITED" only (the company
            # number left off), and ONLY when he signed as himself - which
            # the signing view decided when it copied the stamp onto this
            # party. Nothing here re-decides it: a party without a copied
            # stamp prints none, whoever it is.
            stamp = (bytes(p.mark_stamp)
                     if p.role == 'alivente'
                     and getattr(p, 'mark_stamp', None) else b'')
            if stamp:
                try:
                    srect = pymupdf.Rect(56 + 240, box_top + 2,
                                         56 + 240 + 170, box_top + 54)
                    page.insert_image(srect, stream=stamp,
                                      keep_proportion=True)
                except Exception:                       # noqa: BLE001
                    pass
            page.draw_line(pymupdf.Point(56, box_top + 56),
                           pymupdf.Point(56 + 220, box_top + 56),
'''),
        (r'''                      colour=(0.35, 0.4, 0.43))
                y += 12
            _line(page, 56, y,
                  'Signed %s' % p.signed_at.strftime('%d %B %Y at %H:%M'),
                  size=8.5, colour=(0.35, 0.4, 0.43))
            y += 12
''',
         r'''                      colour=(0.35, 0.4, 0.43))
                y += 12
            # CYPRUS TIME, SAID SO - 25 Oct 2026. The first renders
            # printed UTC: a tenant who signed at 09:12 read 07:12 on
            # her own signature page. timezone.localtime() uses the
            # project's TIME_ZONE, and the page names the zone.
            _line(page, 56, y,
                  'Signed %s' % _when(p.signed_at, '%d %B %Y at %H:%M'),
                  size=8.5, colour=(0.35, 0.4, 0.43))
            y += 12
'''),
        (r'''                       color=(0.88, 0.91, 0.92), width=0.6)
        y += 16
        for e in events:
            if y > h - 70:
                page = doc.new_page(width=w, height=h)
                y = 64
            who = e.party.name if e.party_id and e.party else 'Alivente'
            _line(page, 56, y,
                  '%s   %s   %s%s'
                  % (e.at.strftime('%d %b %Y %H:%M'),
                     e.get_kind_display().ljust(22)[:22], who,
                     ('   ' + e.ip) if e.ip else ''),
                  size=8, colour=(0.25, 0.3, 0.33))
            y += 11

        y += 16
        _line(page, 56, y,
              'Envelope %s   sealed %s'
              % (signing.pk,
                 timezone.now().strftime('%d %B %Y at %H:%M')),
              size=8, colour=(0.45, 0.5, 0.53))

''',
         r'''                       color=(0.88, 0.91, 0.92), width=0.6)
        y += 16
        # FOUR COLUMNS AT FIXED POSITIONS - 25 Oct 2026. The first
        # renders padded with spaces in a proportional font, so nothing
        # lined up, and cut every event name at 22 characters ("Agreed
        # to sign electro"). A trail that is the evidence has to be
        # readable by somebody who was not there.
        cols = (56, 162, 310, w - 56 - 76)
        for label, x in zip(('When', 'What', 'Who', 'From'), cols):
            _line(page, x, y, label, size=7.5, bold=True,
                  colour=(0.35, 0.4, 0.43))
        y += 12
        for e in events:
            if y > h - 70:
                page = doc.new_page(width=w, height=h)
                y = 64
            who = e.party.name if e.party_id and e.party else 'Alivente'
            for text, x in zip((_when(e.at, '%d %b %Y %H:%M'),
                                e.get_kind_display(), who, e.ip or ''),
                               cols):
                _line(page, x, y, text, size=8, colour=(0.25, 0.3, 0.33))
            y += 11

        y += 16
        _line(page, 56, y,
              'Envelope %s   sealed %s'
              % (signing.pk, _when(timezone.now(), '%d %B %Y at %H:%M')),
              size=8, colour=(0.45, 0.5, 0.53))

'''),
    ]),
    (os.path.join('pages', 'templates', 'admin_apms.html'), [
        (r'''      </a>

      <!-- Reserved for growth, AD-1 8 Oct 2026. Empty on purpose:
           it holds the second row so the panel keeps its height.
''',
         r'''      </a>

      <!-- Signature and Stamp - ES-7, 25 Oct 2026. Superuser only, like
           User Administration beside it: his saved signature and the
           company stamp, placed on a lease only when he signs himself. -->
      {% if user.is_superuser %}
        <a href="{% url 'house_marks' %}" class="admin-btn">
          <i class="fas fa-stamp"></i>
          <h6>Signature and Stamp</h6>
        </a>
      {% else %}
        <div class="admin-btn btn-perm-disabled" title="Signature and Stamp is restricted to superusers">
          <i class="fas fa-stamp"></i>
          <h6>Signature and Stamp</h6>
        </div>
      {% endif %}

      <!-- Reserved for growth, AD-1 8 Oct 2026. Empty on purpose:
           it holds the second row so the panel keeps its height.
'''),
    ]),
    (os.path.join('pages', 'templates', 'lease_sign.html'), [
        (r'''    <h1>Lease agreement for {{ tenant.tenant_display_name }}</h1>
    <p class="ls-sub">
      {% if prop %}{{ prop.prop_name }} &middot; {% endif %}
      Signing as <strong>{{ party.name }}</strong>
    </p>
''',
         r'''    <h1>Lease agreement for {{ tenant.tenant_display_name }}</h1>
    <p class="ls-sub">
      {# THE ADDRESS, NEVER THE INTERNAL NAME - ES-7, 25 Oct 2026. #}
      {% if prop.tenant_address %}{{ prop.tenant_address }} &middot; {% endif %}
      Signing as <strong>{{ party.name }}</strong>
    </p>
'''),
        (r'''    <dl style="margin:0">
      <div class="ls-row"><dt>Property</dt>
        <dd>{% if prop %}{{ prop.prop_name }}{% else %}&mdash;{% endif %}</dd></div>
      <div class="ls-row"><dt>Tenancy</dt>
        <dd>{{ tenant.tenant_display_name }}</dd></div>
''',
         r'''    <dl style="margin:0">
      <div class="ls-row"><dt>Property</dt>
        <dd>{% if prop.tenant_address %}{{ prop.tenant_address }}{% else %}&mdash;{% endif %}</dd></div>
      <div class="ls-row"><dt>Tenancy</dt>
        <dd>{{ tenant.tenant_display_name }}</dd></div>
'''),
        (r'''    <input type="hidden" name="read_to_end" id="ls-read" value="0">
    <input type="hidden" name="seconds_open" id="ls-seconds" value="0">
    <input type="hidden" name="signature_kind" id="ls-kind" value="drawn">
    <input type="hidden" name="signature_data" id="ls-data" value="">

    <div class="ls-card">
      <h2>Your signature</h2>

      <div class="ls-tabs" role="tablist">
        <button type="button" class="ls-tab" id="ls-tab-draw"
                role="tab" aria-selected="true" aria-controls="ls-panel-draw">
          Draw it
        </button>
''',
         r'''    <input type="hidden" name="read_to_end" id="ls-read" value="0">
    <input type="hidden" name="seconds_open" id="ls-seconds" value="0">
    <input type="hidden" name="signature_kind" id="ls-kind" value="{% if saved_signature %}saved{% else %}drawn{% endif %}">
    <input type="hidden" name="signature_data" id="ls-data" value="">

    <div class="ls-card">
      <h2>Your signature</h2>

      <div class="ls-tabs" role="tablist">
        {# HIS SAVED SIGNATURE - ES-7, 25 Oct 2026. Offered ONLY when the #}
        {# person signing is signed in as the account that owns it, and  #}
        {# chosen by default. The image itself is never shown here.      #}
        {% if saved_signature %}
        <button type="button" class="ls-tab" id="ls-tab-saved"
                role="tab" aria-selected="true" aria-controls="ls-panel-saved">
          Use my saved signature
        </button>
        {% endif %}
        <button type="button" class="ls-tab" id="ls-tab-draw"
                role="tab" aria-selected="{% if saved_signature %}false{% else %}true{% endif %}" aria-controls="ls-panel-draw">
          Draw it
        </button>
'''),
        (r'''      </div>

      <div id="ls-panel-draw" role="tabpanel" aria-labelledby="ls-tab-draw">
        <div class="ls-pad" id="ls-pad">
          <canvas id="ls-canvas"></canvas>
''',
         r'''      </div>

      {% if saved_signature %}
      <div id="ls-panel-saved" role="tabpanel" aria-labelledby="ls-tab-saved">
        <p class="ls-saved-note">
          Your saved signature{% if house_stamp %} and the company stamp{% endif %}
          will be placed on the signature page.
        </p>
      </div>
      {% endif %}
      <div id="ls-panel-draw" role="tabpanel" aria-labelledby="ls-tab-draw"{% if saved_signature %} hidden{% endif %}>
        <div class="ls-pad" id="ls-pad">
          <canvas id="ls-canvas"></canvas>
'''),
        (r'''  var panDraw = document.getElementById('ls-panel-draw');
  var panType = document.getElementById('ls-panel-type');

  var TOTAL = {{ env.page_count|default:0 }};
''',
         r'''  var panDraw = document.getElementById('ls-panel-draw');
  var panType = document.getElementById('ls-panel-type');
  // ES-7, 25 Oct 2026 - absent unless he is signing as himself.
  var tabSaved = document.getElementById('ls-tab-saved');
  var panSaved = document.getElementById('ls-panel-saved');

  var TOTAL = {{ env.page_count|default:0 }};
'''),
        (r'''  function mode(which) {
    kind.value = which;
    var isDraw = (which === 'drawn');
    tabDraw.setAttribute('aria-selected', isDraw ? 'true' : 'false');
    tabType.setAttribute('aria-selected', isDraw ? 'false' : 'true');
    panDraw.hidden = !isDraw;
    panType.hidden = isDraw;
    paint();
  }
  tabDraw.addEventListener('click', function () { mode('drawn'); });
  tabType.addEventListener('click', function () { mode('typed'); });
  if (typed) typed.addEventListener('input', paint);
  if (consent) consent.addEventListener('change', paint);

  function hasSignature() {
    if (kind.value === 'typed') {
      return !!(typed && typed.value.trim().length >= 2);
''',
         r'''  function mode(which) {
    kind.value = which;
    // THREE WAYS NOW - ES-7, 25 Oct 2026. Each tab shows its own panel
    // and hides the others; the saved tab exists only for him.
    [[tabDraw, panDraw, 'drawn'], [tabType, panType, 'typed'],
     [tabSaved, panSaved, 'saved']].forEach(function (r) {
      if (!r[0]) return;
      var on = (r[2] === which);
      r[0].setAttribute('aria-selected', on ? 'true' : 'false');
      r[1].hidden = !on;
    });
    // A PAD THAT WAS HIDDEN HAS NO SIZE, so it is measured again the
    // moment it is shown - otherwise the line draws away from the finger.
    if (which === 'drawn') sizePad();
    paint();
  }
  tabDraw.addEventListener('click', function () { mode('drawn'); });
  tabType.addEventListener('click', function () { mode('typed'); });
  if (tabSaved) tabSaved.addEventListener('click', function () { mode('saved'); });
  if (typed) typed.addEventListener('input', paint);
  if (consent) consent.addEventListener('change', paint);

  function hasSignature() {
    if (kind.value === 'saved') return true;
    if (kind.value === 'typed') {
      return !!(typed && typed.value.trim().length >= 2);
'''),
    ]),
    (os.path.join('pages', 'templates', 'lease_sign_closed.html'), [
        (r'''    </h1>
    <p class="ls-sub">
      {% if prop %}{{ prop.prop_name }}{% endif %}
    </p>
  </div>
''',
         r'''    </h1>
    <p class="ls-sub">
      {# THE ADDRESS, NEVER THE INTERNAL NAME - ES-7, 25 Oct 2026. #}
      {% if prop.tenant_address %}{{ prop.tenant_address }}{% endif %}
    </p>
  </div>
'''),
        (r'''    <p style="margin:0;color:var(--alv-ink-soft);font-size:14.5px">
      Please quote
      {% if prop %}the property <b>{{ prop.prop_name }}</b>{% else %}your
      tenancy{% endif %} when you do.
    </p>
''',
         r'''    <p style="margin:0;color:var(--alv-ink-soft);font-size:14.5px">
      Please quote
      {% if prop.tenant_address %}the address <b>{{ prop.tenant_address }}</b>{% else %}your
      tenancy{% endif %} when you do.
    </p>
'''),
    ]),
    (os.path.join('pages', 'templates', 'lease_sign_done.html'), [
        (r'''    <h1>Thank you &mdash; your signature is recorded</h1>
    <p class="ls-sub">
      {% if prop %}{{ prop.prop_name }} &middot; {% endif %}
      Signed by {{ party.name }} on {{ party.signed_at|date:"j F Y, H:i" }}
    </p>
''',
         r'''    <h1>Thank you &mdash; your signature is recorded</h1>
    <p class="ls-sub">
      {# THE ADDRESS, NEVER THE INTERNAL NAME - ES-7, 25 Oct 2026. #}
      {% if prop.tenant_address %}{{ prop.tenant_address }} &middot; {% endif %}
      Signed by {{ party.name }} on {{ party.signed_at|date:"j F Y, H:i" }}
    </p>
'''),
    ]),
    (os.path.join('pages', 'templates', 'lease_sign_styles.html'), [
        (r'''    color: var(--alv-accent-ink); font-weight: 700;
  }

  input[type="text"] {
''',
         r'''    color: var(--alv-accent-ink); font-weight: 700;
  }
  /* ES-7, 25 Oct 2026 - the saved-signature panel: a sentence, not a
     preview. The stored image is never shown on this page. */
  .ls-saved-note {
    margin: 0; padding: 18px 16px; border-radius: 8px;
    border: 1px dashed var(--alv-accent-line);
    background: var(--alv-accent-soft); color: var(--alv-accent-ink);
  }

  input[type="text"] {
'''),
    ]),
    (os.path.join('pages', 'templates', 'lease_signing_detail.html'), [
        (r'''<h4 class="page-subtitle-h4">{{ tenant.tenant_display_name }}{% if prop %} &mdash; {{ prop.prop_name }}{% endif %}</h4>

{# ONE BAR, Back last and uncoloured - base 3.4. A POST control has to #}
{# be a form, and display: contents keeps the button where a link     #}
{# would have been.                                                   #}
<div class="page-action-buttons">
    {% if awaiting and perms.auth.can_edit_tenants %}
''',
         r'''<h4 class="page-subtitle-h4">{{ tenant.tenant_display_name }}{% if prop %} &mdash; {{ prop.prop_name }}{% endif %}</h4>

{# ONE BAR, Back last and uncoloured - base 3.4. The two POST buttons #}
{# name forms that sit below the bar (form="..."), so the bar holds    #}
{# house controls only - test_bar_order; ES-7, 25 Oct 2026.            #}
<div class="page-action-buttons">
    {% if awaiting and perms.auth.can_edit_tenants %}
'''),
    ]),
    (os.path.join('pages', 'urls.py'), [
        (r'''    path('lease-signing/<int:pk>/approve/', views.lease_signing_approve,
         name='lease_signing_approve'),
    path('lease/<int:tenant_id>/', views.lease_agreement_report, name='lease_agreement_report'),
    path('lease/<str:filename>/view/', views.serve_lease, name='serve_lease'),
''',
         r'''    path('lease-signing/<int:pk>/approve/', views.lease_signing_approve,
         name='lease_signing_approve'),
    # ES-7, 25 Oct 2026 - his saved signature and the company stamp,
    # superuser only. No route serves the images themselves.
    path('administration/signature-and-stamp/', views.house_marks,
         name='house_marks'),
    path('lease/<int:tenant_id>/', views.lease_agreement_report, name='lease_agreement_report'),
    path('lease/<str:filename>/view/', views.serve_lease, name='serve_lease'),
'''),
    ]),
    (os.path.join('pages', 'views', '__init__.py'), [
        (r'''# signed lease onto its tenant.
from .lease_signing_approve import *  # noqa: F401, F403
from .recipes import *  # noqa: F401, F403
from .help import *  # noqa: F401, F403
''',
         r'''# signed lease onto its tenant.
from .lease_signing_approve import *  # noqa: F401, F403
# ES-7, 25 Oct 2026 - his saved signature and the company stamp,
# superuser only.
from .house_marks import *  # noqa: F401, F403
from .recipes import *  # noqa: F401, F403
from .help import *  # noqa: F401, F403
'''),
    ]),
    (os.path.join('pages', 'views', 'lease_signing.py'), [
        (r'''    now = timezone.now()
    with transaction.atomic():
        env.expires_at = now + timezone.timedelta(days=env.SIGNING_DAYS)
        if env.status == LeaseSigning.EXPIRED:
            tenant_signed = env.parties.filter(
''',
         r'''    now = timezone.now()
    with transaction.atomic():
        # ES-7, 25 Oct 2026 - to the END of that day, Cyprus time.
        env.expires_at = LeaseSigning.closing_moment(env.SIGNING_DAYS, now)
        if env.status == LeaseSigning.EXPIRED:
            tenant_signed = env.parties.filter(
'''),
    ]),
    (os.path.join('pages', 'views', 'lease_signing_create.py'), [
        (r'''                # extension moves this date, and sent_at + 7 would
                # then disagree with what the tenant was told.
                expires_at=timezone.now() + dt.timedelta(days=days))

            if use_stored:
''',
         r'''                # extension moves this date, and sent_at + 7 would
                # then disagree with what the tenant was told.
                # ES-7, 25 Oct 2026 - to the END of that day, Cyprus time.
                expires_at=LeaseSigning.closing_moment(days))

            if use_stored:
'''),
    ]),
    (os.path.join('pages', 'views', 'lease_signing_sign.py'), [
        (r'''from django.views.decorators.csrf import csrf_protect

from ..models import LeaseSigning, LeaseSigningEvent, LeaseSigningParty
from ..services import lease_sealing

''',
         r'''from django.views.decorators.csrf import csrf_protect

from ..models import (HouseMark, LeaseSigning, LeaseSigningEvent,
                      LeaseSigningParty)
from ..services import lease_sealing

'''),
        (r'''

def _signed_copy(env):
    """Email the sealed lease to everybody on the tenancy.
''',
         r'''

def _place(env):
    """Where the lease is, as a TENANT may read it - ES-7, 25 Oct 2026.

    The short address (first line and city), or '' - never prop_name,
    which is internal. Every email a tenant receives names the place
    through this one function.
    """
    prop = getattr(env.tenant, 'prop', None)
    return (getattr(prop, 'tenant_address_short', '') or '') if prop else ''


def _signed_copy(env):
    """Email the sealed lease to everybody on the tenancy.
'''),
        (r'''    about who is on a tenancy.
    """
    from django.core.mail import EmailMessage

    to = list(getattr(env.tenant, 'tenant_emails', None) or [])
''',
         r'''    about who is on a tenancy.
    """
    # ES-7, 25 Oct 2026 - branded, small, no contact details: his decision.
    from ..services.lease_email import BrandedEmail as EmailMessage

    to = list(getattr(env.tenant, 'tenant_emails', None) or [])
'''),
        (r'''        return 0
    who = getattr(env.tenant, 'tenant_display_name', '') or ''
    prop = getattr(getattr(env.tenant, 'prop', None), 'prop_name', '') or ''
    msg = EmailMessage(
        subject='Your signed lease agreement%s' % ((' - ' + prop) if prop else ''),
''',
         r'''        return 0
    who = getattr(env.tenant, 'tenant_display_name', '') or ''
    # THE ADDRESS, NEVER THE INTERNAL NAME - ES-7, 25 Oct 2026.
    prop = _place(env)
    msg = EmailMessage(
        subject='Your signed lease agreement%s' % ((' - ' + prop) if prop else ''),
'''),
        (r'''    words: 'sent', 'reminder' or 'extended'.
    """
    from django.core.mail import EmailMessage

    raw = party.issue_token()
''',
         r'''    words: 'sent', 'reminder' or 'extended'.
    """
    # ES-7, 25 Oct 2026 - branded, small, no contact details: his decision.
    from ..services.lease_email import BrandedEmail as EmailMessage

    raw = party.issue_token()
'''),
        (r'''        raise RuntimeError('envelope %s has no link_base, so a link cannot '
                           'be built without a request' % env.pk)
    prop = getattr(getattr(env.tenant, 'prop', None), 'prop_name', '') or ''
    when = env.expires_at.strftime('%d %B %Y') if env.expires_at else ''
    expiry = ('This link expires on %s.\n\n' % when) if when else ''
    name = party.name or 'Tenant'
    if why == 'reminder':
''',
         r'''        raise RuntimeError('envelope %s has no link_base, so a link cannot '
                           'be built without a request' % env.pk)
    # THE ADDRESS, NEVER THE INTERNAL NAME - ES-7, 25 Oct 2026.
    prop = _place(env)
    # LOCAL TIME, AND THE WHOLE DAY - ES-7, 25 Oct 2026. The date was
    # read in UTC, so near midnight it could name the wrong day; and the
    # link now stays open to the end of the day it names.
    when = (timezone.localtime(env.expires_at).strftime('%d %B %Y')
            if env.expires_at else '')
    expiry = ('This link stays open until the end of %s (Cyprus time).'
              '\n\n' % when) if when else ''
    name = party.name or 'Tenant'
    if why == 'reminder':
'''),
        (r'''def _tell_house_declined(env, party, when):
    """Email the person who sent the envelope that it was declined."""
    from django.core.mail import EmailMessage

    to = []
''',
         r'''def _tell_house_declined(env, party, when):
    """Email the person who sent the envelope that it was declined."""
    # ES-7, 25 Oct 2026 - branded, small, no contact details: his decision.
    from ..services.lease_email import BrandedEmail as EmailMessage

    to = []
'''),
        (r'''

def _store_signature(party, request):
    """Read the signature off the form onto the party. Raises ValueError."""
    kind = (request.POST.get('signature_kind') or '').strip()

    if kind == LeaseSigningParty.KIND_TYPED:
''',
         r'''

def _house_mark(party, request, how, kind):
    """A house mark's bytes for THIS signature, or None - ES-7, 25 Oct 2026.

    HIS RULE: only when Demetri Manias is the signatory, decided by the
    signed-in account and never by a typed name. So: signing by SESSION,
    as the Alivente party, and the account at the keyboard owns the mark.
    A link holder never qualifies, whatever name the envelope carries.
    """
    if how != 'session' or party.role != LeaseSigningParty.ROLE_ALIVENTE:
        return None
    return HouseMark.for_signer(request.user, kind)


def _offers_saved(party, request, how):
    """Should the page offer "Use my saved signature"? (no bytes read)"""
    return bool(how == 'session'
                and party.role == LeaseSigningParty.ROLE_ALIVENTE
                and request.user.is_authenticated
                and HouseMark.objects.filter(kind=HouseMark.SIGNATURE,
                                             owner=request.user).exists())


def _store_signature(party, request, how='token'):
    """Read the signature off the form onto the party. Raises ValueError."""
    kind = (request.POST.get('signature_kind') or '').strip()

    if kind == LeaseSigningParty.KIND_SAVED:
        # ES-7 - THE SAME TEST AS THE PAGE, asked again here, because a
        # hand-made POST can say 'saved' from anywhere.
        mark = _house_mark(party, request, how, HouseMark.SIGNATURE)
        if not mark:
            raise ValueError('There is no saved signature you can use '
                             'here. Draw your signature, or type your '
                             'name.')
        party.signature_kind = LeaseSigningParty.KIND_SAVED
        party.mark_signature = mark
        party.typed_name = ''
        return

    if kind == LeaseSigningParty.KIND_TYPED:
'''),
        (r'''        if error is None:
            try:
                _store_signature(party, request)
            except ValueError as exc:
                error = str(exc)
''',
         r'''        if error is None:
            try:
                _store_signature(party, request, how)
            except ValueError as exc:
                error = str(exc)
'''),
        (r'''            if how == 'session' and request.user.is_authenticated:
                party.signed_by_user = request.user
            try:
                party.seconds_open = min(
''',
         r'''            if how == 'session' and request.user.is_authenticated:
                party.signed_by_user = request.user
            # THE COMPANY STAMP - ES-7, 25 Oct 2026. Whenever he signs as
            # himself, however he signs; for anybody else, nothing.
            party.mark_stamp = _house_mark(party, request, how,
                                           HouseMark.STAMP)
            try:
                party.seconds_open = min(
'''),
        (r'''        # page prints in, named once in lease_sealing.
        'ink': lease_sealing.SIGNATURE_INK_HEX,
    }

''',
         r'''        # page prints in, named once in lease_sealing.
        'ink': lease_sealing.SIGNATURE_INK_HEX,
        # ES-7, 25 Oct 2026 - his saved signature and the stamp, offered
        # only to the account that owns them, signing by session.
        'saved_signature': _offers_saved(party, request, how),
        'house_stamp': bool(
            how == 'session'
            and party.role == LeaseSigningParty.ROLE_ALIVENTE
            and request.user.is_authenticated
            and HouseMark.objects.filter(kind=HouseMark.STAMP,
                                         owner=request.user).exists()),
    }

'''),
    ]),
    (os.path.join('test_bar_height.py'), [
        (r'''
BAR, ROW, MODAL = 35, 34, 38
N_BAR, N_ROW, N_MODAL = 280, 121, 95   # ES-6, 25 Oct 2026 - the envelope page's bar (Approve and attach, Decline, View signed lease, Back). This census does not resolve a branch, so Approve and Decline count even though they only show while an envelope is awaiting approval.   # (was 276)   # ES-3b, 24 Oct 2026 - the Send for Signature screen (Create and sign, Back) and the Send row action on Manage Lease Agreements. This census does not resolve a branch, so both arms of the perms check count - which is why the row figure moved by two and not by one.   # (was 274, 119)   # ES-3a, 23 Oct 2026 - lease_signing_list.html, the envelope register. An ordinary pages/templates page, so it joins every tree-wide count.   # (was 270, 116)   # RV-1, 23 Oct 2026 - the Receipt Details bar: View receipt, Edit and Back. A new PAGE, so three controls join the census without any existing bar changing.   # (was 267)   # TD-2, 16 Oct 2026 - the two disabled twins. A twin is an .icon-action-btn in a table row, so this census counts it exactly as it counts the button it stands in for - which is the whole idea.   # (was 114)   # NV-1d, 16 Oct 2026 - the View button in the desktop strip, which is inside a table.   # (was 113)   # NV-1c, 16 Oct 2026 - the physical invoice disabled mirror, in the desktop strip, which is inside a table.   # (was 112)   # NV-1b, 16 Oct 2026 - the title deeds Actions cell drew two Bootstrap buttons, which this census cannot see. They are icon-delete and icon-upload now, so two controls join the table-row count without a control being added.   # (was 110)   # PJ-1, 15 Oct 2026 - projects_edit carried its Back control twice, behind an if on from_gantt. This census does not resolve a branch, so it counted both arms; one Back control now, and one count.   # (was 268)   # PV-1, 15 Oct 2026 - the four footer buttons of two hand-rolled invoice viewers. The shared component they moved onto was already in this census, so the count falls by exactly the four that went.   # (was 99)   # VC-1, 14 Oct 2026 - property_assets Take Photo is a <label> that had no house class until this round, so this census could not see it. 35px, in a modal, and named in STRAYS below.   # (was 98)   # DB-5, 12 Oct 2026 - the
# dashboard four joined the bar   # (was 265)   # E-10, 11 Oct 2026 - the
# seven buttons this round paired in CRS modals become visible to
# a census that selects the two position tones and not the danger
# tone.   # (was 91)
N_LOOSE, N_LOOSE_H = 87, 11   # ES-3b, 24 Oct 2026 - Choose a different tenant, which sits in a form card rather than in the action bar. N_LOOSE_H does not move: 35px is a height this set already held.   # (was 86)   # LV-1, 16 Oct 2026 - three of the 25 retoned buttons sit in a card or loose on a page. This census selects on a house class, so it could not see them while a LEAVE entry was keeping them Bootstrap-coloured. N_LOOSE_H does not move - all three land on heights the set already held.   # (was 83)   # NV-1c, 16 Oct 2026 - the two comment controls. They were .status-btn, which this census does not select, and they sit in a comment thread rather than a table, so they land in the loose set. 34px was already one of its eleven heights, so N_LOOSE_H does not move.   # (was 81)   # VC-1, 14 Oct 2026 - edit_asset Take Photo at 35px and my_profile Upload Photo at 31px, both <label> file pickers that had no house class until this round. 35 is a height this set did not hold before.   # (was 80 and 10)   # DB-5 - the side column left the
# loose set, and the two heights it invented went with it
# (was 82 and 12)   # E-10 - and the four loose in
''',
         r'''
BAR, ROW, MODAL = 35, 34, 38
N_BAR, N_ROW, N_MODAL = 281, 121, 95   # ES-7, 25 Oct 2026 - the Signature and Stamp screen's bar, Back alone.   # (was 280)   # ES-6, 25 Oct 2026 - the envelope page's bar (Approve and attach, Decline, View signed lease, Back). This census does not resolve a branch, so Approve and Decline count even though they only show while an envelope is awaiting approval.   # (was 276)   # ES-3b, 24 Oct 2026 - the Send for Signature screen (Create and sign, Back) and the Send row action on Manage Lease Agreements. This census does not resolve a branch, so both arms of the perms check count - which is why the row figure moved by two and not by one.   # (was 274, 119)   # ES-3a, 23 Oct 2026 - lease_signing_list.html, the envelope register. An ordinary pages/templates page, so it joins every tree-wide count.   # (was 270, 116)   # RV-1, 23 Oct 2026 - the Receipt Details bar: View receipt, Edit and Back. A new PAGE, so three controls join the census without any existing bar changing.   # (was 267)   # TD-2, 16 Oct 2026 - the two disabled twins. A twin is an .icon-action-btn in a table row, so this census counts it exactly as it counts the button it stands in for - which is the whole idea.   # (was 114)   # NV-1d, 16 Oct 2026 - the View button in the desktop strip, which is inside a table.   # (was 113)   # NV-1c, 16 Oct 2026 - the physical invoice disabled mirror, in the desktop strip, which is inside a table.   # (was 112)   # NV-1b, 16 Oct 2026 - the title deeds Actions cell drew two Bootstrap buttons, which this census cannot see. They are icon-delete and icon-upload now, so two controls join the table-row count without a control being added.   # (was 110)   # PJ-1, 15 Oct 2026 - projects_edit carried its Back control twice, behind an if on from_gantt. This census does not resolve a branch, so it counted both arms; one Back control now, and one count.   # (was 268)   # PV-1, 15 Oct 2026 - the four footer buttons of two hand-rolled invoice viewers. The shared component they moved onto was already in this census, so the count falls by exactly the four that went.   # (was 99)   # VC-1, 14 Oct 2026 - property_assets Take Photo is a <label> that had no house class until this round, so this census could not see it. 35px, in a modal, and named in STRAYS below.   # (was 98)   # DB-5, 12 Oct 2026 - the
# dashboard four joined the bar   # (was 265)   # E-10, 11 Oct 2026 - the
# seven buttons this round paired in CRS modals become visible to
# a census that selects the two position tones and not the danger
# tone.   # (was 91)
N_LOOSE, N_LOOSE_H = 89, 11   # ES-7, 25 Oct 2026 - the two Save buttons on the Signature and Stamp cards, at a height already in the set.   # (was 87)   # ES-3b, 24 Oct 2026 - Choose a different tenant, which sits in a form card rather than in the action bar. N_LOOSE_H does not move: 35px is a height this set already held.   # (was 86)   # LV-1, 16 Oct 2026 - three of the 25 retoned buttons sit in a card or loose on a page. This census selects on a house class, so it could not see them while a LEAVE entry was keeping them Bootstrap-coloured. N_LOOSE_H does not move - all three land on heights the set already held.   # (was 83)   # NV-1c, 16 Oct 2026 - the two comment controls. They were .status-btn, which this census does not select, and they sit in a comment thread rather than a table, so they land in the loose set. 34px was already one of its eleven heights, so N_LOOSE_H does not move.   # (was 81)   # VC-1, 14 Oct 2026 - edit_asset Take Photo at 35px and my_profile Upload Photo at 31px, both <label> file pickers that had no house class until this round. 35 is a height this set did not hold before.   # (was 80 and 10)   # DB-5 - the side column left the
# loose set, and the two heights it invented went with it
# (was 82 and 12)   # E-10 - and the four loose in
'''),
    ]),
    (os.path.join('test_help_label.py'), [
        (r'''        '<span class="action-back-label"> Help</span>')
BARE = '<i class="fas fa-question-circle"></i> Help'
LABELS_TOTAL = 131   # ES-6, 25 Oct 2026 - lease_signing_detail.html, the envelope page. A new PAGE with a house Back, so the tree-wide count moves by exactly one.   # (was 130)   # ES-3b, 24 Oct 2026 - the Send for Signature screen. A new PAGE with a house Back, which carries the label span base hides on a phone, so the tree-wide count moves by exactly one.   # (was 129)   # ES-3a, 23 Oct 2026 - lease_signing_list.html, the envelope register. An ordinary pages/templates page, so it joins every tree-wide count.   # (was 128)   # RV-1, 23 Oct 2026 - the Receipt Details Back. A new PAGE, and a house Back carries the label span base hides on a phone, so the tree-wide count moves by exactly one.   # (was 127)   # PP-1, 20 Oct 2026 - the printable plan's Back. It wore .action-secondary in the first draft and five suites objected; wearing the house class means carrying the house label span, which base hides on a phone so the control becomes a square icon.   # (was 126)   # RT-1, 18 Oct 2026 - three Back labels went with the four meal-plan screens MN-1 retired, and the planner brought none   # (was 129)   # PJ-1, 15 Oct 2026 - the same duplicate Back, counted by its label span. The check below it compares the backup and so falls by one with it.   # (was 130)   # DB-5, 12 Oct 2026 - the dashboard Back gains the house label   # (was 129)   # AFTER this round. 130 before - the Help one.
HELP_TOTAL = 43   # RT-1, 18 Oct 2026 - three of MH-1 five Help buttons went with the screens they sat on. The guide is unchanged and still reached from the planner and the shopping list.   # (was 46)   # MH-1, 18 Oct 2026 - the five meal-plan screens, which had no Help control at all   # (was 41)   # DB-5, 12 Oct 2026 - and a Help secondary joins the bar   # (was 40)
# The shape 77 pages carried before D7 removed every one of them.
''',
         r'''        '<span class="action-back-label"> Help</span>')
BARE = '<i class="fas fa-question-circle"></i> Help'
LABELS_TOTAL = 132   # ES-7, 25 Oct 2026 - house_marks.html, the Signature and Stamp screen, an ordinary pages/templates page that joins every tree-wide count. A house Back, so one more label.   # (was 131)   # ES-6, 25 Oct 2026 - lease_signing_detail.html, the envelope page. A new PAGE with a house Back, so the tree-wide count moves by exactly one.   # (was 130)   # ES-3b, 24 Oct 2026 - the Send for Signature screen. A new PAGE with a house Back, which carries the label span base hides on a phone, so the tree-wide count moves by exactly one.   # (was 129)   # ES-3a, 23 Oct 2026 - lease_signing_list.html, the envelope register. An ordinary pages/templates page, so it joins every tree-wide count.   # (was 128)   # RV-1, 23 Oct 2026 - the Receipt Details Back. A new PAGE, and a house Back carries the label span base hides on a phone, so the tree-wide count moves by exactly one.   # (was 127)   # PP-1, 20 Oct 2026 - the printable plan's Back. It wore .action-secondary in the first draft and five suites objected; wearing the house class means carrying the house label span, which base hides on a phone so the control becomes a square icon.   # (was 126)   # RT-1, 18 Oct 2026 - three Back labels went with the four meal-plan screens MN-1 retired, and the planner brought none   # (was 129)   # PJ-1, 15 Oct 2026 - the same duplicate Back, counted by its label span. The check below it compares the backup and so falls by one with it.   # (was 130)   # DB-5, 12 Oct 2026 - the dashboard Back gains the house label   # (was 129)   # AFTER this round. 130 before - the Help one.
HELP_TOTAL = 43   # RT-1, 18 Oct 2026 - three of MH-1 five Help buttons went with the screens they sat on. The guide is unchanged and still reached from the planner and the shopping list.   # (was 46)   # MH-1, 18 Oct 2026 - the five meal-plan screens, which had no Help control at all   # (was 41)   # DB-5, 12 Oct 2026 - and a Help secondary joins the bar   # (was 40)
# The shape 77 pages carried before D7 removed every one of them.
'''),
    ]),
    (os.path.join('test_house_title.py'), [
        (r'''# keeping the two honest" had been disagreeing for three days. Both
# say 122 now.
ok(len(wearers) == 125,   # ES-6, 25 Oct 2026 - lease_signing_detail.html, the envelope page, an ordinary pages/templates page that joins every tree-wide count. Wears the house title pair.   # (was 124)   # ES-3b, 24 Oct 2026 - lease_signing_create.html, the Send for Signature screen, wears the house title pair.   # (was 123)   # ES-3a, 23 Oct 2026 - lease_signing_list.html wears the house title pair.   # (was 122)
   '122 templates now wear the class, which is the number base\'s note '
   'states', len(wearers))
''',
         r'''# keeping the two honest" had been disagreeing for three days. Both
# say 122 now.
ok(len(wearers) == 126,   # ES-7, 25 Oct 2026 - house_marks.html, the Signature and Stamp screen, an ordinary pages/templates page that joins every tree-wide count. Wears the house title pair.   # (was 125)   # ES-6, 25 Oct 2026 - lease_signing_detail.html, the envelope page, an ordinary pages/templates page that joins every tree-wide count. Wears the house title pair.   # (was 124)   # ES-3b, 24 Oct 2026 - lease_signing_create.html, the Send for Signature screen, wears the house title pair.   # (was 123)   # ES-3a, 23 Oct 2026 - lease_signing_list.html wears the house title pair.   # (was 122)
   '122 templates now wear the class, which is the number base\'s note '
   'states', len(wearers))
'''),
    ]),
    (os.path.join('test_js_buttons.py'), [
        (r'''# SCOPE does not move - 117 was and is the narrow half, and the pages
# the flag hides are still the recipe and meal-plan side.
CENSUS_NARROW, CENSUS_WIDE = 125, 150   # ES-6, 25 Oct 2026 - lease_signing_detail.html, the envelope page, an ordinary pages/templates page that joins every tree-wide count.   # (was 124, 149)   # ES-3b, 24 Oct 2026 - the Send for Signature screen, an ordinary page that joins both halves.   # (was 123, 148)   # ES-4, 24 Oct 2026 - the four public signing templates. They are ordinary pages/templates files, so they join both halves - but they contribute ZERO scanner hits, measured: their controls wear .ls-btn, a class of their own, because the pages cannot extend base and so cannot use the house one.   # (was 119, 144)   # ES-3a, 23 Oct 2026 - lease_signing_list.html, the envelope register. An ordinary pages/templates page, so it joins every tree-wide count.   # (was 118, 143)   # RV-1, 23 Oct 2026 - cash_receipt_detail.html. BOTH halves move: unlike meal_plan_print this is an ordinary pages/templates page, so it joins the sweep scope as well as the application count.   # (was 117, 142)   # PP-1, 20 Oct 2026 - meal_plan_print.html. The narrow half does not move: the sweep scope is the 117 pages it has always been.   # (WIDE was 141)   # RD-1, 19 Oct 2026 - the
# quick-look pair. (wide was 139, and 142 before MN-1 retired four
# meal-plan screens.)
HITS_LOOSE, HITS_TIGHT = 691, 689   # ES-6, 25 Oct 2026 - the envelope page's bar: Approve and attach, Decline, View signed lease and Back. Both matchers rise by the same four.   # (was 687, 685)   # ES-3b, 24 Oct 2026 - Create and sign, Back, and Choose a different tenant. Both matchers rise by the same three. MEASURED PER ROUND rather than split by eye: ES-4 ships four templates in the same bundle and its share is zero, because its buttons are not house .btn ones.   # (was 684, 682)   # ES-3a, 23 Oct 2026 - lease_signing_list.html, the envelope register. An ordinary pages/templates page, so it joins every tree-wide count.   # (was 680, 678)   # RV-1, 23 Oct 2026 - the Receipt Details bar: View receipt, Edit and Back. Both matchers rise by the same three.   # (was 677, 675)   # PP-1, 20 Oct 2026 - the printable plan's two bar controls, Print and Back. Both matchers rise by the same two.   # (was 675, 673)   # RD-1, 19 Oct 2026 - one scanner
# hit per new template, and BOTH matchers rise by the same two.
# (was 673, 671)   # RT-1, 18 Oct 2026 - thirty-three scanner hits went with the four retired screens, and both matchers fall by the same thirty-three.   # (was 706, 704)
''',
         r'''# SCOPE does not move - 117 was and is the narrow half, and the pages
# the flag hides are still the recipe and meal-plan side.
CENSUS_NARROW, CENSUS_WIDE = 126, 151   # ES-7, 25 Oct 2026 - house_marks.html, the Signature and Stamp screen, an ordinary pages/templates page that joins every tree-wide count.   # (was 125, 150)   # ES-6, 25 Oct 2026 - lease_signing_detail.html, the envelope page, an ordinary pages/templates page that joins every tree-wide count.   # (was 124, 149)   # ES-3b, 24 Oct 2026 - the Send for Signature screen, an ordinary page that joins both halves.   # (was 123, 148)   # ES-4, 24 Oct 2026 - the four public signing templates. They are ordinary pages/templates files, so they join both halves - but they contribute ZERO scanner hits, measured: their controls wear .ls-btn, a class of their own, because the pages cannot extend base and so cannot use the house one.   # (was 119, 144)   # ES-3a, 23 Oct 2026 - lease_signing_list.html, the envelope register. An ordinary pages/templates page, so it joins every tree-wide count.   # (was 118, 143)   # RV-1, 23 Oct 2026 - cash_receipt_detail.html. BOTH halves move: unlike meal_plan_print this is an ordinary pages/templates page, so it joins the sweep scope as well as the application count.   # (was 117, 142)   # PP-1, 20 Oct 2026 - meal_plan_print.html. The narrow half does not move: the sweep scope is the 117 pages it has always been.   # (WIDE was 141)   # RD-1, 19 Oct 2026 - the
# quick-look pair. (wide was 139, and 142 before MN-1 retired four
# meal-plan screens.)
HITS_LOOSE, HITS_TIGHT = 694, 692   # ES-7, 25 Oct 2026 - three more house .btn controls on the Signature and Stamp screen, measured by this census. Both matchers rise by the same three.   # (was 691, 689)   # ES-6, 25 Oct 2026 - the envelope page's bar: Approve and attach, Decline, View signed lease and Back. Both matchers rise by the same four.   # (was 687, 685)   # ES-3b, 24 Oct 2026 - Create and sign, Back, and Choose a different tenant. Both matchers rise by the same three. MEASURED PER ROUND rather than split by eye: ES-4 ships four templates in the same bundle and its share is zero, because its buttons are not house .btn ones.   # (was 684, 682)   # ES-3a, 23 Oct 2026 - lease_signing_list.html, the envelope register. An ordinary pages/templates page, so it joins every tree-wide count.   # (was 680, 678)   # RV-1, 23 Oct 2026 - the Receipt Details bar: View receipt, Edit and Back. Both matchers rise by the same three.   # (was 677, 675)   # PP-1, 20 Oct 2026 - the printable plan's two bar controls, Print and Back. Both matchers rise by the same two.   # (was 675, 673)   # RD-1, 19 Oct 2026 - one scanner
# hit per new template, and BOTH matchers rise by the same two.
# (was 673, 671)   # RT-1, 18 Oct 2026 - thirty-three scanner hits went with the four retired screens, and both matchers fall by the same thirty-three.   # (was 706, 704)
'''),
    ]),
    (os.path.join('test_js_escape.py'), [
        (r'''            # J-1. Its interpolations are all |escapejs (the gate above
            # proves it); it is simply no part of J-1's arithmetic.
            'lease_signing_detail.html',)

j1_tree = [(r, p) for r, p in sorted(PATHS.items())
''',
         r'''            # J-1. Its interpolations are all |escapejs (the gate above
            # proves it); it is simply no part of J-1's arithmetic.
            'lease_signing_detail.html',
            # ES-7, 25 Oct 2026 - the Signature and Stamp screen, likewise.
            'house_marks.html',)

j1_tree = [(r, p) for r, p in sorted(PATHS.items())
'''),
    ]),
    (os.path.join('test_landing_tab.py'), [
        (r'''FIN_VIEW = os.path.join('pages', 'views', 'finance.py')
CONVERTED_NOW = 84
N_BACKS = 25   # ES-3a, 23 Oct 2026 - lease_signing_list.html, the envelope register. An ordinary pages/templates page, so it joins every tree-wide count.   # (was 24)

# The three landing pages: template, url name, tabs, default.
''',
         r'''FIN_VIEW = os.path.join('pages', 'views', 'finance.py')
CONVERTED_NOW = 84
N_BACKS = 26   # ES-7, 25 Oct 2026 - house_marks.html, the Signature and Stamp screen, whose Back names the System tab.   # (was 25)   # ES-3a, 23 Oct 2026 - lease_signing_list.html, the envelope register. An ordinary pages/templates page, so it joins every tree-wide count.   # (was 24)

# The three landing pages: template, url name, tabs, default.
'''),
        (r'''CREATED_LATER = {
    'lease_signing_list.html',
}

''',
         r'''CREATED_LATER = {
    'lease_signing_list.html',
    # ES-7, 25 Oct 2026 - the Signature and Stamp screen.
    'house_marks.html',
}

# TILES ADDED AFTER THIS ROUND FROZE ITS COPY OF A LANDING PAGE - ES-7,
# 25 Oct 2026. panel_owner() reads each landing page AS THIS ROUND LEFT
# IT, so a tile added since is invisible to it, and a Back that names
# that tile's own panel would read as UNEXPLAINED. ES-3a's tile sat on
# the default panel and could be named in BY_DEFAULT; a tile on the
# OTHER panel cannot. So it is named here WITH its panel - and the
# claim is checked against the LIVE landing page below, so this register
# cannot say a tile is somewhere it is not.
ADDED_AFTER = {
    ('admin_apms', 'house_marks'): 'system',
}

'''),
        (r'''
OWNER = panel_owner()
ok(len(OWNER) >= 14,
   'the three landing pages claim %d destination(s) between their panels'
''',
         r'''
OWNER = panel_owner()
# ES-7 - the register above, each entry proved against the LIVE page.
for (_land, _dest), _key in sorted(ADDED_AFTER.items()):
    _page = [p for p, u, _t, _d in LANDING if u == _land][0]
    _live = re.sub(r'\{% comment %\}.*?\{% endcomment %\}', '',
                   read(alv_tree.path_of(_page)), flags=re.S)
    _m = re.search(r'<div id="(?:panel-)?%s(?:-panel)?" class="tab-panel'
                   % _key, _live)
    _seg = _live[_m.end():] if _m else ''
    _nxt = _seg.find('class="tab-panel')
    _seg = _seg[:_nxt] if _nxt > 0 else _seg
    ok(_dest in re.findall(URL_IN, _seg),
       '%s is on the LIVE %s page\'s %s panel - added after this round, '
       'and named in ADDED_AFTER' % (_dest, _page, _key))
    OWNER[(_land, _dest)] = _key
ok(len(OWNER) >= 14,
   'the three landing pages claim %d destination(s) between their panels'
'''),
    ]),
    (os.path.join('test_lazy_images.py'), [
        (r'''# let the end-of-document marker into the viewport on arrival and
# unlocked the Sign button before a word had been read.
ok(len(lazy) == 13, '%d image(s) wait, on %d page(s)' % (len(lazy), len(pages)),
   '\n'.join('%s %s' % (r, t[:60]) for r, t in lazy[:4]))
ok(len(eager) >= 20, 'and %d do not' % len(eager))
''',
         r'''# let the end-of-document marker into the viewport on arrival and
# unlocked the Sign button before a word had been read.
# ES-7, 25 Oct 2026 - 14 ON 9. The Signature and Stamp screen shows one
# preview per mark from a loop, so they wait like every list does.
ok(len(lazy) == 14, '%d image(s) wait, on %d page(s)' % (len(lazy), len(pages)),
   '\n'.join('%s %s' % (r, t[:60]) for r, t in lazy[:4]))
ok(len(eager) >= 20, 'and %d do not' % len(eager))
'''),
    ]),
    (os.path.join('test_lease_approval.py'), [
        (r'''                                           + timezone.timedelta(days=365)
                                           ).date(), tenant_current='Yes')
                start = timezone.now()
                e = M.LeaseSigning.objects.create(
                    tenant=t, status='sent', sent_at=start,
                    expires_at=start + timezone.timedelta(days=days),
                    original_pdf='x.pdf')
                at = lambda d: start + timezone.timedelta(days=d)  # noqa
                return e, at

            e14, at14 = window(14)
            ok(e14.reminder_due(at14(3.01)) == 3
               and e14.reminder_due(at14(6.01)) == 3
               and e14.reminder_due(at14(13.01)) == 13,
               'FOURTEEN DAYS: day 3 and day 13 - not day 6, which is what '
               'ES-5\'s fixed pair would have sent',
               [e14.reminder_due(at14(d)) for d in (3.01, 6.01, 13.01)])
            e3, at3 = window(3)
            ok(e3.reminder_due(at3(1.5)) is None
               and e3.reminder_due(at3(2.01)) == 2,
               'THREE DAYS: only the day before it lapses - day 3 is the '
               'deadline itself', [e3.reminder_due(at3(d))
                                   for d in (1.5, 2.01)])
            e7, at7 = window(7)
            ok(e7.reminder_due(at7(3.01)) == 3
               and e7.reminder_due(at7(6.01)) == 6,
               'SEVEN DAYS: still day 3 and day 6, exactly as he decided')
            M.LeaseSigningEvent.objects.create(signing=e7, kind='extended')
''',
         r'''                                           + timezone.timedelta(days=365)
                                           ).date(), tenant_current='Yes')
                # ES-7, 25 Oct 2026 - SENT AT 10:00 LOCAL AND CLOSING AT THE
                # END OF THE LAST DAY, the way the Send screen now makes
                # every envelope; probes are local clock times, so the
                # answer cannot depend on what hour the suite runs at.
                import datetime as _dt
                day0 = timezone.localdate()
                start = timezone.make_aware(
                    _dt.datetime.combine(day0, _dt.time(10, 0)))
                e = M.LeaseSigning.objects.create(
                    tenant=t, status='sent', sent_at=start,
                    expires_at=M.LeaseSigning.closing_moment(days, start),
                    original_pdf='x.pdf')

                def at(d, hh=11, mm=0):
                    return timezone.make_aware(_dt.datetime.combine(
                        day0 + _dt.timedelta(days=d), _dt.time(hh, mm)))
                return e, at

            e14, at14 = window(14)
            ok(e14.reminder_due(at14(3)) == 3
               and e14.reminder_due(at14(6)) == 3
               and e14.reminder_due(at14(13, 0, 30)) == 13,
               'FOURTEEN DAYS: day 3 and day 13 - not day 6, which is what '
               'ES-5\'s fixed pair would have sent',
               [e14.reminder_due(x) for x in (at14(3), at14(6),
                                              at14(13, 0, 30))])
            e3, at3 = window(3)
            ok(e3.reminder_due(at3(1, 12)) is None
               and e3.reminder_due(at3(2, 0, 30)) == 2
               and e3.reminder_due(at3(3, 12)) == 2,
               'THREE DAYS: only the day before it lapses - day 3 is the '
               'deadline itself, and since ES-7 the link is open all of it',
               [e3.reminder_due(x) for x in (at3(1, 12), at3(2, 0, 30),
                                             at3(3, 12))])
            e7, at7 = window(7)
            ok(e7.reminder_due(at7(3)) == 3
               and e7.reminder_due(at7(6)) == 6,
               'SEVEN DAYS: still day 3 and day 6, exactly as he decided')
            M.LeaseSigningEvent.objects.create(signing=e7, kind='extended')
'''),
    ]),
    (os.path.join('test_pair_contrast.py'), [
        (r'''MARK = 'B-4b, 8 Oct 2026'

EXPECT_PAIRS = 745   # ES-6, 25 Oct 2026 - three more rules in ES-6's pages set a fill and an ink together, measured by this census on the full tree.   # (was 742)   # ES-4, 24 Oct 2026 - eleven in the public signing pages' own stylesheet. A standalone page cannot inherit a surface, so every one it draws sets both halves of the pair itself - which is exactly why this census asks about them.   # (was 731)   # ES-3a, 23 Oct 2026 - the lease signing register: three signer dots mirroring the good, bad and neutral pills, and the waiting-on-you note. Four rules, no new pairings.   # (was 727)   # MN-2, 21 Oct 2026 - the Saved Menus dialog gains the preset row CP-2 built for Copy, and .mn-preset[aria-pressed=true] sets a fill and an ink together exactly as .cp-preset does. One more pair, of tokens this table already knows.   # (was 726)   # RG-2, 21 Oct 2026 - two more rules set a fill and an ink together: the date field, which wears the paper token on the ink one like every other field in the system, and the line explaining the second Print press, which sits on the surface wash.   # (was 724)   # RG-1, 21 Oct 2026 - the printed sheet is drawn again from four layouts, and five more of its rules set a fill and an ink together: the pill in its three states, the today marker and the dimmed cell. Every one is a token pair this table already knows.   # (was 719)   # PP-1, 20 Oct 2026 - the printable plan sets
# both a ground and an ink on six rules. All house pairs off base's
# own tokens, so the AA table below is untouched and the gross count
''',
         r'''MARK = 'B-4b, 8 Oct 2026'

EXPECT_PAIRS = 747   # ES-7, 25 Oct 2026 - two notes set a fill and an ink together: .hm-note on the Signature and Stamp screen and .ls-saved-note on the signing page, both on the accent pair this table already knows.   # (was 745)   # ES-6, 25 Oct 2026 - three more rules in ES-6's pages set a fill and an ink together, measured by this census on the full tree.   # (was 742)   # ES-4, 24 Oct 2026 - eleven in the public signing pages' own stylesheet. A standalone page cannot inherit a surface, so every one it draws sets both halves of the pair itself - which is exactly why this census asks about them.   # (was 731)   # ES-3a, 23 Oct 2026 - the lease signing register: three signer dots mirroring the good, bad and neutral pills, and the waiting-on-you note. Four rules, no new pairings.   # (was 727)   # MN-2, 21 Oct 2026 - the Saved Menus dialog gains the preset row CP-2 built for Copy, and .mn-preset[aria-pressed=true] sets a fill and an ink together exactly as .cp-preset does. One more pair, of tokens this table already knows.   # (was 726)   # RG-2, 21 Oct 2026 - two more rules set a fill and an ink together: the date field, which wears the paper token on the ink one like every other field in the system, and the line explaining the second Print press, which sits on the surface wash.   # (was 724)   # RG-1, 21 Oct 2026 - the printed sheet is drawn again from four layouts, and five more of its rules set a fill and an ink together: the pill in its three states, the today marker and the dimmed cell. Every one is a token pair this table already knows.   # (was 719)   # PP-1, 20 Oct 2026 - the printable plan sets
# both a ground and an ink on six rules. All house pairs off base's
# own tokens, so the AA table below is untouched and the gross count
'''),
    ]),
    (os.path.join('test_recipe_side_b.py'), [
        (r'''N_EDITS, N_PAGES = 31, 13
N_DRIFT, N_DECIDED = 18, 13
GATE_WAS, GATE_NOW = 125, 150   # ES-6, 25 Oct 2026 - lease_signing_detail.html, the envelope page, an ordinary page that joins every tree-wide count.   # (was 124, 149)   # ES-3b, 24 Oct 2026 - the Send for Signature screen, an ordinary page that joins every tree-wide count.   # (was 123, 148)   # ES-4, 24 Oct 2026 - the four public signing templates. They are ordinary pages/templates files, so they join every tree-wide count; they cannot extend base, which is why they are standalone.   # (was 119, 144)   # ES-3a, 23 Oct 2026 - lease_signing_list.html, the envelope register. An ordinary pages/templates page, so it joins every tree-wide count.   # (was 118, 143)   # RV-1, 23 Oct 2026 - cash_receipt_detail.html. The same pair as test_js_buttons and test_recipe_tones: an ordinary pages/templates page joins the sweep scope and the page count alike.   # (was 117, 142)   # PP-1, 20 Oct 2026 - meal_plan_print.html. (GATE_NOW was 141)   # RD-1, 19 Oct 2026 - the quick-look
# pair. (GATE_NOW was 139)   # RT-1, 18 Oct 2026 - the wide census is four meal-plan screens smaller and one planner larger. The narrow half does not move.   # (GATE_NOW was 142)

''',
         r'''N_EDITS, N_PAGES = 31, 13
N_DRIFT, N_DECIDED = 18, 13
GATE_WAS, GATE_NOW = 126, 151   # ES-7, 25 Oct 2026 - house_marks.html, the Signature and Stamp screen, an ordinary pages/templates page that joins every tree-wide count.   # (was 125, 150)   # ES-6, 25 Oct 2026 - lease_signing_detail.html, the envelope page, an ordinary page that joins every tree-wide count.   # (was 124, 149)   # ES-3b, 24 Oct 2026 - the Send for Signature screen, an ordinary page that joins every tree-wide count.   # (was 123, 148)   # ES-4, 24 Oct 2026 - the four public signing templates. They are ordinary pages/templates files, so they join every tree-wide count; they cannot extend base, which is why they are standalone.   # (was 119, 144)   # ES-3a, 23 Oct 2026 - lease_signing_list.html, the envelope register. An ordinary pages/templates page, so it joins every tree-wide count.   # (was 118, 143)   # RV-1, 23 Oct 2026 - cash_receipt_detail.html. The same pair as test_js_buttons and test_recipe_tones: an ordinary pages/templates page joins the sweep scope and the page count alike.   # (was 117, 142)   # PP-1, 20 Oct 2026 - meal_plan_print.html. (GATE_NOW was 141)   # RD-1, 19 Oct 2026 - the quick-look
# pair. (GATE_NOW was 139)   # RT-1, 18 Oct 2026 - the wide census is four meal-plan screens smaller and one planner larger. The narrow half does not move.   # (GATE_NOW was 142)

'''),
    ]),
    (os.path.join('test_recipe_tones.py'), [
        (r'''# ES-4, 24 Oct 2026 - the four public signing templates. They are ordinary pages/templates files, so they join every tree-wide count; they cannot extend base, which is why they are standalone.
# ES-3b, 24 Oct 2026 - the Send for Signature screen, an ordinary page that joins both halves.
# ES-6, 25 Oct 2026 - the envelope page joins both counts. (was 124, 149)
ok(len(sb.templates(False)) == 125 and len(sb.templates(True)) == 150,
   '  which is %d of %d' % (125, 150),
   '%d of %d' % (len(sb.templates(False)), len(sb.templates(True))))

''',
         r'''# ES-4, 24 Oct 2026 - the four public signing templates. They are ordinary pages/templates files, so they join every tree-wide count; they cannot extend base, which is why they are standalone.
# ES-3b, 24 Oct 2026 - the Send for Signature screen, an ordinary page that joins both halves.
# ES-7, 25 Oct 2026 - the Signature and Stamp screen joins both. (was 125, 150)
# ES-6, 25 Oct 2026 - the envelope page joins both counts. (was 124, 149)
ok(len(sb.templates(False)) == 126 and len(sb.templates(True)) == 151,
   '  which is %d of %d' % (126, 151),
   '%d of %d' % (len(sb.templates(False)), len(sb.templates(True))))

'''),
    ]),
    (os.path.join('test_signing_lifecycle.py'), [
        (r'''               'FROM EXPIRED IT REOPENS AS PART-SIGNED, because Andreas\'s '
               'signature was kept', env.status)
            span = (env.expires_at - before).total_seconds() / 86400.0
            ok(6.99 < span < 7.01,
               '  with a new date seven days from now, STORED - it is the '
               'date the email states', span)
            ok(to_whom() == ['maria@example.com'],
               'ONLY MARIA IS EMAILED. Andreas signed and gets nothing; the '
''',
         r'''               'FROM EXPIRED IT REOPENS AS PART-SIGNED, because Andreas\'s '
               'signature was kept', env.status)
            # ES-7, 25 Oct 2026 - SEVEN DAYS FROM TODAY, TO THE END OF THAT
            # DAY in local time: his decision that a link stays open to the
            # end of the day the email names.
            close = timezone.localtime(env.expires_at)
            ok(close.date() == timezone.localdate(before)
               + timezone.timedelta(days=7)
               and (close.hour, close.minute, close.second) == (23, 59, 59),
               '  with a new date seven days from now, open to the END of '
               'that day, STORED - it is the date the email states', close)
            ok(to_whom() == ['maria@example.com'],
               'ONLY MARIA IS EMAILED. Andreas signed and gets nothing; the '
'''),
    ]),
    (os.path.join('test_subtree_tones.py'), [
        (r'''# ES-3b, 24 Oct 2026 - the Send for Signature screen sits flat in pages/templates, so it joins the walk and the flat listing alike.
# ES-6, 25 Oct 2026 - lease_signing_detail.html, the envelope page, an ordinary pages/templates page that joins every tree-wide count.
ok(len(tree) == 159, 'a WALK finds 159 templates', len(tree))
ok(len(top) == 133, '  a flat listing finds 133 - 120 was what H7 '
   'counted, 122 after MN-1, and RD-1 adds the quick-look pair',
   len(top))
''',
         r'''# ES-3b, 24 Oct 2026 - the Send for Signature screen sits flat in pages/templates, so it joins the walk and the flat listing alike.
# ES-6, 25 Oct 2026 - lease_signing_detail.html, the envelope page, an ordinary pages/templates page that joins every tree-wide count.
# ES-7, 25 Oct 2026 - house_marks.html, the Signature and Stamp screen, an ordinary pages/templates page that joins every tree-wide count.
ok(len(tree) == 160, 'a WALK finds 160 templates', len(tree))
ok(len(top) == 134, '  a flat listing finds 134 - 120 was what H7 '
   'counted, 122 after MN-1, and RD-1 adds the quick-look pair',
   len(top))
'''),
    ]),
    (os.path.join('test_tree_roots.py'), [
        (r'''# 143 since 6 Oct: Section E round E-2b added access_denied.html,
# the 403 page, which until then lived in an f-string.
MAIN_N = 151   # ES-6, 25 Oct 2026 - lease_signing_detail.html, the envelope page, an ordinary pages/templates page that joins every tree-wide count.   # (was 150)   # ES-3b, 24 Oct 2026 - the Send for Signature screen, an ordinary page that joins every tree-wide count.   # (was 149)   # ES-4, 24 Oct 2026 - the four public signing templates. They are ordinary pages/templates files, so they join every tree-wide count; they cannot extend base, which is why they are standalone.   # (was 145)   # ES-3a, 23 Oct 2026 - lease_signing_list.html, the envelope register. An ordinary pages/templates page, so it joins every tree-wide count.   # (was 144)   # RV-1, 23 Oct 2026 - cash_receipt_detail.html. This is the shape of the tree, which is what this file is for.   # (was 143)   # PP-1, 20 Oct 2026 - the printable meal plan is a
               # new page: 142 + 1. (was 142)   # RD-1, 19 Oct 2026 - the quick-look dialog adds two:
               # the partial and its shell. (was 140)   # RT-1, 18 Oct 2026 - MN-1 retired four meal-plan screens and the planner replaced them: 143 - 4 + 1. This is the shape of the tree, which is what this file is for.   # (was 143)
''',
         r'''# 143 since 6 Oct: Section E round E-2b added access_denied.html,
# the 403 page, which until then lived in an f-string.
MAIN_N = 152   # ES-7, 25 Oct 2026 - house_marks.html, the Signature and Stamp screen, an ordinary pages/templates page that joins every tree-wide count.   # (was 151)   # ES-6, 25 Oct 2026 - lease_signing_detail.html, the envelope page, an ordinary pages/templates page that joins every tree-wide count.   # (was 150)   # ES-3b, 24 Oct 2026 - the Send for Signature screen, an ordinary page that joins every tree-wide count.   # (was 149)   # ES-4, 24 Oct 2026 - the four public signing templates. They are ordinary pages/templates files, so they join every tree-wide count; they cannot extend base, which is why they are standalone.   # (was 145)   # ES-3a, 23 Oct 2026 - lease_signing_list.html, the envelope register. An ordinary pages/templates page, so it joins every tree-wide count.   # (was 144)   # RV-1, 23 Oct 2026 - cash_receipt_detail.html. This is the shape of the tree, which is what this file is for.   # (was 143)   # PP-1, 20 Oct 2026 - the printable meal plan is a
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
    raise SystemExit('ES-7 REFUSED: %s' % msg)


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
    if 'class HouseMark(models.Model):' in read(pm):
        print('ES-7  already applied - house marks.')
        return 0

    sys.path.insert(0, root)
    import alv_tree as T

    # ---- WHAT THIS ROUND STANDS ON
    if "'test_second_signer.py'" not in read(os.path.join(root, PS1)):
        refuse('ES-6c is not applied - this round registers after it.')
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
    q = swap(q, """    'test_second_signer.py'
)""", """    'test_second_signer.py',
    # ES-7, 25 Oct 2026 - his signature and the stamp; the address.
    'test_house_marks.py'
)""", '%s (the suites)' % PS1)
    q = swap(
        q,
        """    @{ File = 'mysite/cron-requirements.txt'; Text = 'pymupdf';""",
        """    @{ File = 'pages/views/lease_signing_sign.py'; Text = 'def _house_mark(party, request, how, kind):'; What = 'ES-7: the ONE place that decides who gets his signature and the stamp - the Alivente party, signing by session, as the account that owns them; a typed name never reaches it' },
    @{ File = 'pages/templates/lease_sign.html'; Text = 'content="same-origin"'; What = 'Live fix of 25 Oct: with no-referrer the browser sends Origin: null and Django refused every signature' },
    @{ File = 'mysite/cron-requirements.txt'; Text = 'pymupdf';""",
        '%s (the sentinels)' % PS1)
    out[pq] = q

    ptr = os.path.join(root, TREE)
    out[ptr] = swap(read(ptr), """    'test_second_signer.py',
]""", """    'test_second_signer.py',
    # ES-7, 25 Oct 2026 - his signature and the stamp; the address.
    'test_house_marks.py',
]""", '%s (CONVERTED)' % TREE)

    pd = os.path.join(root, ROUNDS)
    out[pd] = swap(read(pd), """    '.bak_secondsigner',
]""", """    '.bak_secondsigner',
    # ES-7, 25 Oct 2026 - his signature and the stamp; the address.
    '.bak_housemarks',
]""", '%s (ROUNDS)' % ROUNDS)

    pw = os.path.join(root, WD)
    w = read(pw)
    n = re.search(r'CONVERTED_N = (\d+)', w)
    if not n:
        refuse('%s: CONVERTED_N is not there' % WD)
    out[pw] = swap(w, 'CONVERTED_N = %s' % n.group(1),
                   'CONVERTED_N = %d   # ES-7, 25 Oct 2026 - this round '
                   'own suite   # (was %s)'
                   % (int(n.group(1)) + 1, n.group(1)),
                   '%s (CONVERTED_N)' % WD)

    # ---------------------------------------------------------- THE GATES
    sign = T.python_code_only(out[os.path.join(
        root, 'pages', 'views', 'lease_signing_sign.py')])
    # ---- 1. WHO GETS THE MARKS: the session, the house party, the owner.
    if ("if how != 'session' or party.role != "
            "LeaseSigningParty.ROLE_ALIVENTE:") not in sign \
            or 'HouseMark.for_signer(request.user, kind)' not in sign:
        refuse('the marks must be decided by the signed-in account, for '
               'the Alivente party, signing by session - nothing else.')
    # ---- 2. NOTHING SERVES THE IMAGES.
    view = T.python_code_only(read(os.path.join(root, VIEW)))
    if 'HttpResponse' in view or 'FileResponse' in view:
        refuse('the Signature and Stamp screen must return a page, never '
               'an image.')
    # ---- 3. THE INTERNAL NAME NEVER REACHES A TENANT.
    for rel in ('lease_sign.html', 'lease_sign_closed.html',
                'lease_sign_done.html'):
        src = T.code_only(out[os.path.join(root, 'pages', 'templates', rel)])
        if 'prop_name' in src:
            refuse('%s still prints the internal property name.' % rel)
    inv = sign[sign.index('def _signed_copy('):sign.index('def _advance(')]
    if 'prop_name' in inv:
        refuse('an email a tenant receives still names the internal '
               'property name.')
    # ---- 4. THE BROWSER MAY NAME ITS ORIGIN.
    pad = out[os.path.join(root, 'pages', 'templates', 'lease_sign.html')]
    if 'content="same-origin"' not in pad or 'no-referrer' in \
            T.code_only(pad).replace('NO-REFERRER', ''):
        refuse('the signing page must not send no-referrer - Origin: null '
               'is refused by CSRF.')
    # ---- 5. NO CONTACT DETAILS IN THE EMAILS - his decision of 25 Oct.
    mailer = read(os.path.join(root, MAILER))
    if re.search(r'Tel:|Mobile:|\+357|mailto:', mailer):
        refuse('the e-signing emails must carry no contact details.')
    # ---- 6. NO HEX LITERAL IN THE NEW PAGE'S STYLES.
    for blk in re.findall(r'\.hm-[\s\S]*?\}', read(os.path.join(root, PAGE))):
        if re.search(r'#[0-9a-fA-F]{3,6}\b', blk):
            refuse('house_marks.html: an hm- rule carries a hex literal; '
                   'tokens only.')

    if CHECK:
        print('ES-7  --check: %d file(s) would change, none written; %d '
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
    print('ES-7  applied - his signature and the stamp, only when he signs; '
          'the address, never the internal name; links open to the end of '
          'the day.')
    print('      %d file(s) written, backed up to %s' % (len(out), SUFFIX))
    print('      %d file(s) ship with it, wired in rather than written'
          % len(CREATES))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
