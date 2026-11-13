# -*- coding: utf-8 -*-
"""apply_gifts.py - rounds BV-1 and CG-1, 13 Nov 2026.

RELEASES 74 AND 75, ONE BUNDLE.

    R74 (BV-1): Recipe management sends the recipe book's recipes only
    when the book is opened (?book=1), not on every visit.
    R75 (CG-1): gifts - private, on my own celebrations, never lost; My
    gifts; the Christmas list (plan, then buy; planned against spent; the
    shopping list to me on WhatsApp); a greeting by Claude, in WhatsApp.

New files ship beside this patcher. Stands on Release 73.
Idempotent. Edits backed up to .bak_gifts.
MIGRATION 0119 - run python manage.py migrate before pushing.
"""
import os
import sys

SUFFIX = '.bak_gifts'
MARK = 'CG-1, 13 Nov 2026'
CHECK = False
PS1 = 'Push-PendingChanges.ps1'
CREATES = (
    'pages/views/celebration_gifts.py',
    'pages/migrations/0119_celebration_gifts.py',
    'pages/templates/celebration_gifts.html',
    'test_gifts.py',
)

SWAPS = [
    (os.path.join('Push-PendingChanges.ps1'), [
        (r'''    @{ File = 'wellness/views_recipe.py'; Text = 'def recipe(request, recipe_id):'; What = 'PT-2: a recipe from Today opens inside Wellness - without it the card links to nothing' },
    @{ File = 'pages/passport_holder.py'; Text = 'def member_for(workspace_id, holder_name):'; What = 'PT-2: a document is matched to its holder - without it no document can be added or saved' },
    @{ File = 'pages/meal_calendar.py'; Text = 'class MealCalendarMiddleware:'; What = 'MS-1: which meal plan a request is about - without it the planner cannot open' },
    @{ File = 'wellness/crypto.py'; Text = 'def seal_bytes('; What = 'WL-19: the lock for progress photos is on disk - without it no photo can be saved or shown' },
''',
         r'''    @{ File = 'wellness/views_recipe.py'; Text = 'def recipe(request, recipe_id):'; What = 'PT-2: a recipe from Today opens inside Wellness - without it the card links to nothing' },
    @{ File = 'pages/passport_holder.py'; Text = 'def member_for(workspace_id, holder_name):'; What = 'PT-2: a document is matched to its holder - without it no document can be added or saved' },
    @{ File = 'pages/models.py'; Text = 'class Gift(models.Model):'; What = 'CG-1: gifts - without it migration 0119 has no model and Celebrations cannot open' },
    @{ File = 'pages/views/celebration_gifts.py'; Text = 'def my_gifts(request):'; What = 'CG-1: My gifts and the Christmas list - without it the Celebrations links go nowhere' },
    @{ File = 'pages/meal_calendar.py'; Text = 'class MealCalendarMiddleware:'; What = 'MS-1: which meal plan a request is about - without it the planner cannot open' },
    @{ File = 'wellness/crypto.py'; Text = 'def seal_bytes('; What = 'WL-19: the lock for progress photos is on disk - without it no photo can be saved or shown' },
'''),
        (r'''    'test_doc_recipe.py',
    # PT-2, 12 Nov 2026 - Release 73: At home today is one card; a recipe opens in Wellness.
    'test_wellness_twentyfive.py'
)
# NUMBER EVERY SUITE AS IT RUNS - Demetri, 1 Oct 2026: "for every check of
''',
         r'''    'test_doc_recipe.py',
    # PT-2, 12 Nov 2026 - Release 73: At home today is one card; a recipe opens in Wellness.
    'test_wellness_twentyfive.py',
    # BV-1 + CG-1, 13 Nov 2026 - Releases 74 and 75: the recipe book on demand; gifts.
    'test_gifts.py'
)
# NUMBER EVERY SUITE AS IT RUNS - Demetri, 1 Oct 2026: "for every check of
'''),
    ]),
    (os.path.join('wellness', 'views.py'), [
        (r'''        wanted = set(request.POST.getlist('module'))
        MOD.save(profile, wanted)
        cy_on = CY.is_on(request.user)
        if 'cycle' in wanted and not cy_on:
''',
         r'''        wanted = set(request.POST.getlist('module'))
        MOD.save(profile, wanted)
        # PT-3, 13 Nov 2026 - At home today is one of Your sections now
        # (Demetri, 07:00: "like any other module"), each person's own.
        profile.refresh_from_db(fields=['prefs'])
        hp = dict(profile.prefs or {})
        hp['home_off'] = not request.POST.get('home')
        profile.prefs = hp
        profile.save(update_fields=['prefs', 'updated_at'])
        cy_on = CY.is_on(request.user)
        if 'cycle' in wanted and not cy_on:
'''),
        (r'''        # WL-15 - sounds and vibration are on unless turned off here.
        prefs['sounds_off'] = not request.POST.get('sounds')
        # PT-1 - "At home today" on Today, on unless turned off here.
        prefs['home_off'] = not request.POST.get('home')
        # WL-4b - the evening and weigh-in reminder times, or none.
        for k in ('remind_checkin', 'remind_weigh'):
''',
         r'''        # WL-15 - sounds and vibration are on unless turned off here.
        prefs['sounds_off'] = not request.POST.get('sounds')
        # WL-4b - the evening and weigh-in reminder times, or none.
        for k in ('remind_checkin', 'remind_weigh'):
'''),
        (r'''        'off_name': MOD.name_of(off_key) if off_key in MOD.KEYS else '',
        'sections_open': bool(request.GET.get('s') or off_key),
        'on_names': ', '.join(n for k, n, _l in MOD.MODULES if k in on),
        'weekly': bool(prefs.get('weekly_email')),
        'claude_line': not prefs.get('line_off'),
''',
         r'''        'off_name': MOD.name_of(off_key) if off_key in MOD.KEYS else '',
        'sections_open': bool(request.GET.get('s') or off_key),
        'on_names': ', '.join([n for k, n, _l in MOD.MODULES if k in on]
                              + ([] if prefs.get('home_off')
                                 else ['At home today'])),
        'weekly': bool(prefs.get('weekly_email')),
        'claude_line': not prefs.get('line_off'),
'''),
    ]),
    (os.path.join('wellness', 'templates', 'wellness', 'settings.html'), [
        (r'''    {% if m.key == 'cycle' %}{% comment %} CY-3, 31 Oct 2026 - Demetri, 21:06: the cycle tracker only here, not twice. {% endcomment %}<a class="w-small" href="{% url 'wellness:cycle' %}" style="color:var(--w-sage-deep);min-height:44px;display:inline-flex;align-items:center;margin-top:-6px">{% if m.on %}Open the cycle tracker ›{% else %}What is the cycle tracker? ›{% endif %}</a>{% endif %}
    {% endfor %}
    <button type="submit" class="w-btn full" style="margin-top:8px">Save my sections</button>
  </form>
''',
         r'''    {% if m.key == 'cycle' %}{% comment %} CY-3, 31 Oct 2026 - Demetri, 21:06: the cycle tracker only here, not twice. {% endcomment %}<a class="w-small" href="{% url 'wellness:cycle' %}" style="color:var(--w-sage-deep);min-height:44px;display:inline-flex;align-items:center;margin-top:-6px">{% if m.on %}Open the cycle tracker ›{% else %}What is the cycle tracker? ›{% endif %}</a>{% endif %}
    {% endfor %}
    {# PT-3, 13 Nov 2026 - At home today, switched like any other section, each person's own. #}
    <label class="w-toggle" style="align-items:flex-start;padding:6px 0"><span style="display:flex;flex-direction:column;gap:2px"><span>At home today</span><span class="w-small w-quiet">Who celebrates today, today's meals and your documents due for renewal, at the top of Today.</span></span><input type="checkbox" name="home" value="1"{% if home_on %} checked{% endif %} style="margin-top:2px" data-home-switch></label>
    <button type="submit" class="w-btn full" style="margin-top:8px">Save my sections</button>
  </form>
'''),
        (r'''  <h2 class="w-h2">Sounds and vibration</h2>
  <label style="display:flex;align-items:flex-start;gap:10px;min-height:44px;font-size:15px"><input type="checkbox" name="sounds" value="1"{% if sounds %} checked{% endif %} style="width:22px;height:22px;margin-top:1px;accent-color:var(--w-sage-deep)" data-fx-switch> <span>A soft sound and a short vibration when you tick a habit, earn a badge or finish your day<br><span class="w-small w-quiet">Quiet, and at media volume. Vibration works on Android phones. If your phone is set to reduce motion, the animations become a simple fade.</span></span></label>
  {# PT-1, 12 Nov 2026 - the rest of Alivente, on Today. #}
  <h2 class="w-h2">At home today</h2>
  <label style="display:flex;align-items:flex-start;gap:10px;min-height:44px;font-size:15px"><input type="checkbox" name="home" value="1"{% if home_on %} checked{% endif %} style="width:22px;height:22px;margin-top:1px;accent-color:var(--w-sage-deep)" data-home-switch> <span>Show my celebrations, today's meals and my documents on Today<br><span class="w-small w-quiet">A card at the top, only when there is something to say: who celebrates today, today's meals and your documents due for renewal.</span></span></label>
  {# WL-4c - the line from Claude under the daily quote. #}
  <h2 class="w-h2">The daily quote</h2>
''',
         r'''  <h2 class="w-h2">Sounds and vibration</h2>
  <label style="display:flex;align-items:flex-start;gap:10px;min-height:44px;font-size:15px"><input type="checkbox" name="sounds" value="1"{% if sounds %} checked{% endif %} style="width:22px;height:22px;margin-top:1px;accent-color:var(--w-sage-deep)" data-fx-switch> <span>A soft sound and a short vibration when you tick a habit, earn a badge or finish your day<br><span class="w-small w-quiet">Quiet, and at media volume. Vibration works on Android phones. If your phone is set to reduce motion, the animations become a simple fade.</span></span></label>
  {# WL-4c - the line from Claude under the daily quote. #}
  <h2 class="w-h2">The daily quote</h2>
'''),
    ]),
    (os.path.join('wellness', 'help.py'), [
        (r'''            'Download your data: everything as spreadsheets, your photos if '
            'you like.',
            'At home today: the card on Today with today\'s celebrations, '
            'meals and your documents. Turn it on or off.',
        ],
        'signs': [],
''',
         r'''            'Download your data: everything as spreadsheets, your photos if '
            'you like.',
            'Your sections also switches At home today, the card at the '
            'top of Today, on or off.',
        ],
        'signs': [],
'''),
    ]),
    (os.path.join('wellness', 'guide.py'), [
        (r'''          'or the nine or twelve chosen under Remind me. Tap a recipe to '
          'open it here, with Cook mode. The card only appears when there '
          'is something to say. Turn it off under the cog, At home today.'},
    {'q': 'Set up: log a workout you already did',
     'a': 'For a run this morning, or a session yesterday you forgot to '
''',
         r'''          'or the nine or twelve chosen under Remind me. Tap a recipe to '
          'open it here, with Cook mode. The card only appears when there '
          'is something to say. Turn it off under the cog, Your sections.'},
    {'q': 'Set up: log a workout you already did',
     'a': 'For a run this morning, or a session yesterday you forgot to '
'''),
    ]),
    (os.path.join('test_wellness_twentyfour.py'), [
        (r'''v = read(J(APP, 'views.py'))
ok("if (profile.prefs or {}).get('home_off'):" in v and
   "prefs['home_off'] = not request.POST.get('home')" in v and
   'except Exception:  # noqa: BLE001 - Today must always open' in v,
   '  it can be turned off in Settings, and a fault there never stops Today')
''',
         r'''v = read(J(APP, 'views.py'))
ok("if (profile.prefs or {}).get('home_off'):" in v and
   # PT-3, 13 Nov 2026 - the switch moved into Your sections.
   "hp['home_off'] = not request.POST.get('home')" in v and
   'except Exception:  # noqa: BLE001 - Today must always open' in v,
   '  it can be turned off in Settings, and a fault there never stops Today')
'''),
    ]),
    (os.path.join('test_house_title.py'), [
        (r'''# keeping the two honest" had been disagreeing for three days. Both
# say 122 now.
ok(len(wearers) == 127,   # GL-1, 28 Oct 2026 - company_details.html, the Company Details screen, an ordinary pages/templates page that joins every tree-wide count. Wears the house title pair.   # (was 126)   # ES-7, 25 Oct 2026 - house_marks.html, the Signature and Stamp screen, an ordinary pages/templates page that joins every tree-wide count. Wears the house title pair.   # (was 125)   # ES-6, 25 Oct 2026 - lease_signing_detail.html, the envelope page, an ordinary pages/templates page that joins every tree-wide count. Wears the house title pair.   # (was 124)   # ES-3b, 24 Oct 2026 - lease_signing_create.html, the Send for Signature screen, wears the house title pair.   # (was 123)   # ES-3a, 23 Oct 2026 - lease_signing_list.html wears the house title pair.   # (was 122)
   '122 templates now wear the class, which is the number base\'s note '
   'states', len(wearers))
''',
         r'''# keeping the two honest" had been disagreeing for three days. Both
# say 122 now.
ok(len(wearers) == 128,   # CG-1, 13 Nov 2026 - celebration_gifts.html, the My gifts page with the Christmas list, an ordinary pages/templates page that joins every tree-wide count. Wears the house title pair.   # (was 127)   # GL-1, 28 Oct 2026 - company_details.html, the Company Details screen, an ordinary pages/templates page that joins every tree-wide count. Wears the house title pair.   # (was 126)   # ES-7, 25 Oct 2026 - house_marks.html, the Signature and Stamp screen, an ordinary pages/templates page that joins every tree-wide count. Wears the house title pair.   # (was 125)   # ES-6, 25 Oct 2026 - lease_signing_detail.html, the envelope page, an ordinary pages/templates page that joins every tree-wide count. Wears the house title pair.   # (was 124)   # ES-3b, 24 Oct 2026 - lease_signing_create.html, the Send for Signature screen, wears the house title pair.   # (was 123)   # ES-3a, 23 Oct 2026 - lease_signing_list.html wears the house title pair.   # (was 122)
   '122 templates now wear the class, which is the number base\'s note '
   'states', len(wearers))
'''),
    ]),
    (os.path.join('test_js_buttons.py'), [
        (r'''# SCOPE does not move - 117 was and is the narrow half, and the pages
# the flag hides are still the recipe and meal-plan side.
CENSUS_NARROW, CENSUS_WIDE = 128, 153   # GL-1, 28 Oct 2026 - company_details.html, the Company Details screen, an ordinary pages/templates page that joins every tree-wide count.   # (was 127, 152)   # LS-1, 27 Oct 2026 - tenant_lease_signing_status.html, the Lease Signing Status report, an ordinary pages/templates page that joins every tree-wide count.   # (was 126, 151)   # ES-7, 25 Oct 2026 - house_marks.html, the Signature and Stamp screen, an ordinary pages/templates page that joins every tree-wide count.   # (was 125, 150)   # ES-6, 25 Oct 2026 - lease_signing_detail.html, the envelope page, an ordinary pages/templates page that joins every tree-wide count.   # (was 124, 149)   # ES-3b, 24 Oct 2026 - the Send for Signature screen, an ordinary page that joins both halves.   # (was 123, 148)   # ES-4, 24 Oct 2026 - the four public signing templates. They are ordinary pages/templates files, so they join both halves - but they contribute ZERO scanner hits, measured: their controls wear .ls-btn, a class of their own, because the pages cannot extend base and so cannot use the house one.   # (was 119, 144)   # ES-3a, 23 Oct 2026 - lease_signing_list.html, the envelope register. An ordinary pages/templates page, so it joins every tree-wide count.   # (was 118, 143)   # RV-1, 23 Oct 2026 - cash_receipt_detail.html. BOTH halves move: unlike meal_plan_print this is an ordinary pages/templates page, so it joins the sweep scope as well as the application count.   # (was 117, 142)   # PP-1, 20 Oct 2026 - meal_plan_print.html. The narrow half does not move: the sweep scope is the 117 pages it has always been.   # (WIDE was 141)   # RD-1, 19 Oct 2026 - the
# quick-look pair. (wide was 139, and 142 before MN-1 retired four
# meal-plan screens.)
HITS_LOOSE, HITS_TIGHT = 699, 697   # GL-1, 28 Oct 2026 - Save and Back on the Company Details screen; both matchers rise by the same two.   # (was 697, 695)   # LS-1, 27 Oct 2026 - Include finished / Open only and Back on the Lease Signing Status report, measured by this census; both matchers rise by the same three.   # (was 694, 692)   # ES-7, 25 Oct 2026 - three more house .btn controls on the Signature and Stamp screen, measured by this census. Both matchers rise by the same three.   # (was 691, 689)   # ES-6, 25 Oct 2026 - the envelope page's bar: Approve and attach, Decline, View signed lease and Back. Both matchers rise by the same four.   # (was 687, 685)   # ES-3b, 24 Oct 2026 - Create and sign, Back, and Choose a different tenant. Both matchers rise by the same three. MEASURED PER ROUND rather than split by eye: ES-4 ships four templates in the same bundle and its share is zero, because its buttons are not house .btn ones.   # (was 684, 682)   # ES-3a, 23 Oct 2026 - lease_signing_list.html, the envelope register. An ordinary pages/templates page, so it joins every tree-wide count.   # (was 680, 678)   # RV-1, 23 Oct 2026 - the Receipt Details bar: View receipt, Edit and Back. Both matchers rise by the same three.   # (was 677, 675)   # PP-1, 20 Oct 2026 - the printable plan's two bar controls, Print and Back. Both matchers rise by the same two.   # (was 675, 673)   # RD-1, 19 Oct 2026 - one scanner
# hit per new template, and BOTH matchers rise by the same two.
# (was 673, 671)   # RT-1, 18 Oct 2026 - thirty-three scanner hits went with the four retired screens, and both matchers fall by the same thirty-three.   # (was 706, 704)
''',
         r'''# SCOPE does not move - 117 was and is the narrow half, and the pages
# the flag hides are still the recipe and meal-plan side.
CENSUS_NARROW, CENSUS_WIDE = 128, 154   # CG-1, 13 Nov 2026 - celebration_gifts.html, the My gifts page. It joins the application count only, measured: the narrow sweep scope stays 128.   # (was 128, 153)   # GL-1, 28 Oct 2026 - company_details.html, the Company Details screen, an ordinary pages/templates page that joins every tree-wide count.   # (was 127, 152)   # LS-1, 27 Oct 2026 - tenant_lease_signing_status.html, the Lease Signing Status report, an ordinary pages/templates page that joins every tree-wide count.   # (was 126, 151)   # ES-7, 25 Oct 2026 - house_marks.html, the Signature and Stamp screen, an ordinary pages/templates page that joins every tree-wide count.   # (was 125, 150)   # ES-6, 25 Oct 2026 - lease_signing_detail.html, the envelope page, an ordinary pages/templates page that joins every tree-wide count.   # (was 124, 149)   # ES-3b, 24 Oct 2026 - the Send for Signature screen, an ordinary page that joins both halves.   # (was 123, 148)   # ES-4, 24 Oct 2026 - the four public signing templates. They are ordinary pages/templates files, so they join both halves - but they contribute ZERO scanner hits, measured: their controls wear .ls-btn, a class of their own, because the pages cannot extend base and so cannot use the house one.   # (was 119, 144)   # ES-3a, 23 Oct 2026 - lease_signing_list.html, the envelope register. An ordinary pages/templates page, so it joins every tree-wide count.   # (was 118, 143)   # RV-1, 23 Oct 2026 - cash_receipt_detail.html. BOTH halves move: unlike meal_plan_print this is an ordinary pages/templates page, so it joins the sweep scope as well as the application count.   # (was 117, 142)   # PP-1, 20 Oct 2026 - meal_plan_print.html. The narrow half does not move: the sweep scope is the 117 pages it has always been.   # (WIDE was 141)   # RD-1, 19 Oct 2026 - the
# quick-look pair. (wide was 139, and 142 before MN-1 retired four
# meal-plan screens.)
HITS_LOOSE, HITS_TIGHT = 704, 702   # CG-1, 13 Nov 2026 - the My gifts page: Shopping list to me, Back, and a Remove and a Save on each Christmas row, measured by this census; both matchers rise by the same five.   # (was 699, 697)   # GL-1, 28 Oct 2026 - Save and Back on the Company Details screen; both matchers rise by the same two.   # (was 697, 695)   # LS-1, 27 Oct 2026 - Include finished / Open only and Back on the Lease Signing Status report, measured by this census; both matchers rise by the same three.   # (was 694, 692)   # ES-7, 25 Oct 2026 - three more house .btn controls on the Signature and Stamp screen, measured by this census. Both matchers rise by the same three.   # (was 691, 689)   # ES-6, 25 Oct 2026 - the envelope page's bar: Approve and attach, Decline, View signed lease and Back. Both matchers rise by the same four.   # (was 687, 685)   # ES-3b, 24 Oct 2026 - Create and sign, Back, and Choose a different tenant. Both matchers rise by the same three. MEASURED PER ROUND rather than split by eye: ES-4 ships four templates in the same bundle and its share is zero, because its buttons are not house .btn ones.   # (was 684, 682)   # ES-3a, 23 Oct 2026 - lease_signing_list.html, the envelope register. An ordinary pages/templates page, so it joins every tree-wide count.   # (was 680, 678)   # RV-1, 23 Oct 2026 - the Receipt Details bar: View receipt, Edit and Back. Both matchers rise by the same three.   # (was 677, 675)   # PP-1, 20 Oct 2026 - the printable plan's two bar controls, Print and Back. Both matchers rise by the same two.   # (was 675, 673)   # RD-1, 19 Oct 2026 - one scanner
# hit per new template, and BOTH matchers rise by the same two.
# (was 673, 671)   # RT-1, 18 Oct 2026 - thirty-three scanner hits went with the four retired screens, and both matchers fall by the same thirty-three.   # (was 706, 704)
'''),
    ]),
    (os.path.join('test_recipe_side_b.py'), [
        (r'''N_EDITS, N_PAGES = 31, 13
N_DRIFT, N_DECIDED = 18, 13
GATE_WAS, GATE_NOW = 128, 153   # GL-1, 28 Oct 2026 - company_details.html, the Company Details screen, an ordinary pages/templates page that joins every tree-wide count.   # (was 127, 152)   # LS-1, 27 Oct 2026 - tenant_lease_signing_status.html, the Lease Signing Status report, an ordinary pages/templates page that joins every tree-wide count.   # (was 126, 151)   # ES-7, 25 Oct 2026 - house_marks.html, the Signature and Stamp screen, an ordinary pages/templates page that joins every tree-wide count.   # (was 125, 150)   # ES-6, 25 Oct 2026 - lease_signing_detail.html, the envelope page, an ordinary page that joins every tree-wide count.   # (was 124, 149)   # ES-3b, 24 Oct 2026 - the Send for Signature screen, an ordinary page that joins every tree-wide count.   # (was 123, 148)   # ES-4, 24 Oct 2026 - the four public signing templates. They are ordinary pages/templates files, so they join every tree-wide count; they cannot extend base, which is why they are standalone.   # (was 119, 144)   # ES-3a, 23 Oct 2026 - lease_signing_list.html, the envelope register. An ordinary pages/templates page, so it joins every tree-wide count.   # (was 118, 143)   # RV-1, 23 Oct 2026 - cash_receipt_detail.html. The same pair as test_js_buttons and test_recipe_tones: an ordinary pages/templates page joins the sweep scope and the page count alike.   # (was 117, 142)   # PP-1, 20 Oct 2026 - meal_plan_print.html. (GATE_NOW was 141)   # RD-1, 19 Oct 2026 - the quick-look
# pair. (GATE_NOW was 139)   # RT-1, 18 Oct 2026 - the wide census is four meal-plan screens smaller and one planner larger. The narrow half does not move.   # (GATE_NOW was 142)

''',
         r'''N_EDITS, N_PAGES = 31, 13
N_DRIFT, N_DECIDED = 18, 13
GATE_WAS, GATE_NOW = 128, 154   # CG-1, 13 Nov 2026 - celebration_gifts.html, the My gifts page. It joins the application count only, measured: the narrow sweep scope stays 128.   # (was 128, 153)   # GL-1, 28 Oct 2026 - company_details.html, the Company Details screen, an ordinary pages/templates page that joins every tree-wide count.   # (was 127, 152)   # LS-1, 27 Oct 2026 - tenant_lease_signing_status.html, the Lease Signing Status report, an ordinary pages/templates page that joins every tree-wide count.   # (was 126, 151)   # ES-7, 25 Oct 2026 - house_marks.html, the Signature and Stamp screen, an ordinary pages/templates page that joins every tree-wide count.   # (was 125, 150)   # ES-6, 25 Oct 2026 - lease_signing_detail.html, the envelope page, an ordinary page that joins every tree-wide count.   # (was 124, 149)   # ES-3b, 24 Oct 2026 - the Send for Signature screen, an ordinary page that joins every tree-wide count.   # (was 123, 148)   # ES-4, 24 Oct 2026 - the four public signing templates. They are ordinary pages/templates files, so they join every tree-wide count; they cannot extend base, which is why they are standalone.   # (was 119, 144)   # ES-3a, 23 Oct 2026 - lease_signing_list.html, the envelope register. An ordinary pages/templates page, so it joins every tree-wide count.   # (was 118, 143)   # RV-1, 23 Oct 2026 - cash_receipt_detail.html. The same pair as test_js_buttons and test_recipe_tones: an ordinary pages/templates page joins the sweep scope and the page count alike.   # (was 117, 142)   # PP-1, 20 Oct 2026 - meal_plan_print.html. (GATE_NOW was 141)   # RD-1, 19 Oct 2026 - the quick-look
# pair. (GATE_NOW was 139)   # RT-1, 18 Oct 2026 - the wide census is four meal-plan screens smaller and one planner larger. The narrow half does not move.   # (GATE_NOW was 142)

'''),
        (r'''# shipped decisions instead of ten. The refusal gets stronger, not
# weaker, which is why this count is read and not frozen.
N_NAV_RULE_HITS, N_NAV_RULE_PRIMARY = 12, 10   # PP-1, 20 Oct 2026 - the planner leaves the set. The rule needs a bar whose only non-Back item is a link, and the planner bar now holds Print as well as Shopping List.   # (was 13, 11)   # (was 12, 10)
N_COND_LABEL, N_COND_LABEL_PRIMARY = 11, 7   # CX-1, 29 Oct 2026 - Help on the Task List, which reads Greek or English like its neighbours, a secondary   # (was 10, 7)   # CR-2, 27 Oct 2026 - Email again / Email receipt on Receipt Details, a secondary  # (was 9, 7)

''',
         r'''# shipped decisions instead of ten. The refusal gets stronger, not
# weaker, which is why this count is read and not frozen.
N_NAV_RULE_HITS, N_NAV_RULE_PRIMARY = 13, 11   # CG-1, 13 Nov 2026 - the My gifts bar on the Christmas tab: its only non-Back item is a link, Shopping list to me, and it ships as .action-primary.   # (was 12, 10)   # PP-1, 20 Oct 2026 - the planner leaves the set. The rule needs a bar whose only non-Back item is a link, and the planner bar now holds Print as well as Shopping List.   # (was 13, 11)   # (was 12, 10)
N_COND_LABEL, N_COND_LABEL_PRIMARY = 11, 7   # CX-1, 29 Oct 2026 - Help on the Task List, which reads Greek or English like its neighbours, a secondary   # (was 10, 7)   # CR-2, 27 Oct 2026 - Email again / Email receipt on Receipt Details, a secondary  # (was 9, 7)

'''),
    ]),
    (os.path.join('test_recipe_tones.py'), [
        (r'''# LS-1, 27 Oct 2026 - tenant_lease_signing_status.html, the Lease Signing Status report, an ordinary pages/templates page that joins every tree-wide count.
# GL-1, 28 Oct 2026 - 128 of 153: company_details.html joins both halves.
ok(len(sb.templates(False)) == 128 and len(sb.templates(True)) == 153,
   '  which is %d of %d' % (128, 153),
   '%d of %d' % (len(sb.templates(False)), len(sb.templates(True))))

''',
         r'''# LS-1, 27 Oct 2026 - tenant_lease_signing_status.html, the Lease Signing Status report, an ordinary pages/templates page that joins every tree-wide count.
# GL-1, 28 Oct 2026 - 128 of 153: company_details.html joins both halves.
# CG-1, 13 Nov 2026 - celebration_gifts.html, the My gifts page with the Christmas list, it joins the page count only, measured - the narrow half stays 128. (was 128 of 153)
ok(len(sb.templates(False)) == 128 and len(sb.templates(True)) == 154,
   '  which is %d of %d' % (128, 154),
   '%d of %d' % (len(sb.templates(False)), len(sb.templates(True))))

'''),
    ]),
    (os.path.join('test_subtree_tones.py'), [
        (r'''# LS-1, 27 Oct 2026 - tenant_lease_signing_status.html, the Lease Signing Status report, an ordinary pages/templates page that joins every tree-wide count.
# GL-1, 28 Oct 2026 - company_details.html, the Company Details screen, an ordinary pages/templates page that joins every tree-wide count.
ok(len(tree) == 162, 'a WALK finds 162 templates', len(tree))
ok(len(top) == 136, '  a flat listing finds 136 - 120 was what H7 '
   'counted, 122 after MN-1, and RD-1 adds the quick-look pair',
   len(top))
''',
         r'''# LS-1, 27 Oct 2026 - tenant_lease_signing_status.html, the Lease Signing Status report, an ordinary pages/templates page that joins every tree-wide count.
# GL-1, 28 Oct 2026 - company_details.html, the Company Details screen, an ordinary pages/templates page that joins every tree-wide count.
# CG-1, 13 Nov 2026 - celebration_gifts.html, the My gifts page with the Christmas list, an ordinary pages/templates page that joins every tree-wide count. (was 162 and 136)
ok(len(tree) == 163, 'a WALK finds 163 templates', len(tree))
ok(len(top) == 137, '  a flat listing finds 137 - 120 was what H7 '
   'counted, 122 after MN-1, and RD-1 adds the quick-look pair',
   len(top))
'''),
    ]),
    (os.path.join('test_tree_roots.py'), [
        (r'''# 143 since 6 Oct: Section E round E-2b added access_denied.html,
# the 403 page, which until then lived in an f-string.
MAIN_N = 154   # GL-1, 28 Oct 2026 - company_details.html, the Company Details screen, an ordinary pages/templates page that joins every tree-wide count.   # (was 153)   # LS-1, 27 Oct 2026 - tenant_lease_signing_status.html, the Lease Signing Status report, an ordinary pages/templates page that joins every tree-wide count.   # (was 152)   # ES-7, 25 Oct 2026 - house_marks.html, the Signature and Stamp screen, an ordinary pages/templates page that joins every tree-wide count.   # (was 151)   # ES-6, 25 Oct 2026 - lease_signing_detail.html, the envelope page, an ordinary pages/templates page that joins every tree-wide count.   # (was 150)   # ES-3b, 24 Oct 2026 - the Send for Signature screen, an ordinary page that joins every tree-wide count.   # (was 149)   # ES-4, 24 Oct 2026 - the four public signing templates. They are ordinary pages/templates files, so they join every tree-wide count; they cannot extend base, which is why they are standalone.   # (was 145)   # ES-3a, 23 Oct 2026 - lease_signing_list.html, the envelope register. An ordinary pages/templates page, so it joins every tree-wide count.   # (was 144)   # RV-1, 23 Oct 2026 - cash_receipt_detail.html. This is the shape of the tree, which is what this file is for.   # (was 143)   # PP-1, 20 Oct 2026 - the printable meal plan is a
               # new page: 142 + 1. (was 142)   # RD-1, 19 Oct 2026 - the quick-look dialog adds two:
               # the partial and its shell. (was 140)   # RT-1, 18 Oct 2026 - MN-1 retired four meal-plan screens and the planner replaced them: 143 - 4 + 1. This is the shape of the tree, which is what this file is for.   # (was 143)
''',
         r'''# 143 since 6 Oct: Section E round E-2b added access_denied.html,
# the 403 page, which until then lived in an f-string.
MAIN_N = 155   # CG-1, 13 Nov 2026 - celebration_gifts.html, the My gifts page with the Christmas list, an ordinary pages/templates page that joins every tree-wide count.   # (was 154)   # GL-1, 28 Oct 2026 - company_details.html, the Company Details screen, an ordinary pages/templates page that joins every tree-wide count.   # (was 153)   # LS-1, 27 Oct 2026 - tenant_lease_signing_status.html, the Lease Signing Status report, an ordinary pages/templates page that joins every tree-wide count.   # (was 152)   # ES-7, 25 Oct 2026 - house_marks.html, the Signature and Stamp screen, an ordinary pages/templates page that joins every tree-wide count.   # (was 151)   # ES-6, 25 Oct 2026 - lease_signing_detail.html, the envelope page, an ordinary pages/templates page that joins every tree-wide count.   # (was 150)   # ES-3b, 24 Oct 2026 - the Send for Signature screen, an ordinary page that joins every tree-wide count.   # (was 149)   # ES-4, 24 Oct 2026 - the four public signing templates. They are ordinary pages/templates files, so they join every tree-wide count; they cannot extend base, which is why they are standalone.   # (was 145)   # ES-3a, 23 Oct 2026 - lease_signing_list.html, the envelope register. An ordinary pages/templates page, so it joins every tree-wide count.   # (was 144)   # RV-1, 23 Oct 2026 - cash_receipt_detail.html. This is the shape of the tree, which is what this file is for.   # (was 143)   # PP-1, 20 Oct 2026 - the printable meal plan is a
               # new page: 142 + 1. (was 142)   # RD-1, 19 Oct 2026 - the quick-look dialog adds two:
               # the partial and its shell. (was 140)   # RT-1, 18 Oct 2026 - MN-1 retired four meal-plan screens and the planner replaced them: 143 - 4 + 1. This is the shape of the tree, which is what this file is for.   # (was 143)
'''),
    ]),
    (os.path.join('test_help_label.py'), [
        (r'''        '<span class="action-back-label"> Help</span>')
BARE = '<i class="fas fa-question-circle"></i> Help'
LABELS_TOTAL = 133   # GL-1, 28 Oct 2026 - company_details.html, the Company Details screen, an ordinary pages/templates page that joins every tree-wide count. A house Back, so one more label.   # (was 132)   # ES-7, 25 Oct 2026 - house_marks.html, the Signature and Stamp screen, an ordinary pages/templates page that joins every tree-wide count. A house Back, so one more label.   # (was 131)   # ES-6, 25 Oct 2026 - lease_signing_detail.html, the envelope page. A new PAGE with a house Back, so the tree-wide count moves by exactly one.   # (was 130)   # ES-3b, 24 Oct 2026 - the Send for Signature screen. A new PAGE with a house Back, which carries the label span base hides on a phone, so the tree-wide count moves by exactly one.   # (was 129)   # ES-3a, 23 Oct 2026 - lease_signing_list.html, the envelope register. An ordinary pages/templates page, so it joins every tree-wide count.   # (was 128)   # RV-1, 23 Oct 2026 - the Receipt Details Back. A new PAGE, and a house Back carries the label span base hides on a phone, so the tree-wide count moves by exactly one.   # (was 127)   # PP-1, 20 Oct 2026 - the printable plan's Back. It wore .action-secondary in the first draft and five suites objected; wearing the house class means carrying the house label span, which base hides on a phone so the control becomes a square icon.   # (was 126)   # RT-1, 18 Oct 2026 - three Back labels went with the four meal-plan screens MN-1 retired, and the planner brought none   # (was 129)   # PJ-1, 15 Oct 2026 - the same duplicate Back, counted by its label span. The check below it compares the backup and so falls by one with it.   # (was 130)   # DB-5, 12 Oct 2026 - the dashboard Back gains the house label   # (was 129)   # AFTER this round. 130 before - the Help one.
HELP_TOTAL = 47   # CX-1, 29 Oct 2026 - Task List and Gantt Chart gain Help, bare text like their siblings   # (was 45)   # HK-4, 28 Oct 2026 - Project Details gains Help, his finding; bare text like its siblings   # (was 44)   # ES-8, 25 Oct 2026 - the Lease Signing register gains its own Help, his request; a bare-text Help secondary like its siblings.   # (was 43)   # RT-1, 18 Oct 2026 - three of MH-1 five Help buttons went with the screens they sat on. The guide is unchanged and still reached from the planner and the shopping list.   # (was 46)   # MH-1, 18 Oct 2026 - the five meal-plan screens, which had no Help control at all   # (was 41)   # DB-5, 12 Oct 2026 - and a Help secondary joins the bar   # (was 40)
# The shape 77 pages carried before D7 removed every one of them.
''',
         r'''        '<span class="action-back-label"> Help</span>')
BARE = '<i class="fas fa-question-circle"></i> Help'
LABELS_TOTAL = 134   # CG-1, 13 Nov 2026 - celebration_gifts.html, the My gifts page, an ordinary pages/templates page with a Back.   # (was 133)   # GL-1, 28 Oct 2026 - company_details.html, the Company Details screen, an ordinary pages/templates page that joins every tree-wide count. A house Back, so one more label.   # (was 132)   # ES-7, 25 Oct 2026 - house_marks.html, the Signature and Stamp screen, an ordinary pages/templates page that joins every tree-wide count. A house Back, so one more label.   # (was 131)   # ES-6, 25 Oct 2026 - lease_signing_detail.html, the envelope page. A new PAGE with a house Back, so the tree-wide count moves by exactly one.   # (was 130)   # ES-3b, 24 Oct 2026 - the Send for Signature screen. A new PAGE with a house Back, which carries the label span base hides on a phone, so the tree-wide count moves by exactly one.   # (was 129)   # ES-3a, 23 Oct 2026 - lease_signing_list.html, the envelope register. An ordinary pages/templates page, so it joins every tree-wide count.   # (was 128)   # RV-1, 23 Oct 2026 - the Receipt Details Back. A new PAGE, and a house Back carries the label span base hides on a phone, so the tree-wide count moves by exactly one.   # (was 127)   # PP-1, 20 Oct 2026 - the printable plan's Back. It wore .action-secondary in the first draft and five suites objected; wearing the house class means carrying the house label span, which base hides on a phone so the control becomes a square icon.   # (was 126)   # RT-1, 18 Oct 2026 - three Back labels went with the four meal-plan screens MN-1 retired, and the planner brought none   # (was 129)   # PJ-1, 15 Oct 2026 - the same duplicate Back, counted by its label span. The check below it compares the backup and so falls by one with it.   # (was 130)   # DB-5, 12 Oct 2026 - the dashboard Back gains the house label   # (was 129)   # AFTER this round. 130 before - the Help one.
HELP_TOTAL = 47   # CX-1, 29 Oct 2026 - Task List and Gantt Chart gain Help, bare text like their siblings   # (was 45)   # HK-4, 28 Oct 2026 - Project Details gains Help, his finding; bare text like its siblings   # (was 44)   # ES-8, 25 Oct 2026 - the Lease Signing register gains its own Help, his request; a bare-text Help secondary like its siblings.   # (was 43)   # RT-1, 18 Oct 2026 - three of MH-1 five Help buttons went with the screens they sat on. The guide is unchanged and still reached from the planner and the shopping list.   # (was 46)   # MH-1, 18 Oct 2026 - the five meal-plan screens, which had no Help control at all   # (was 41)   # DB-5, 12 Oct 2026 - and a Help secondary joins the bar   # (was 40)
# The shape 77 pages carried before D7 removed every one of them.
'''),
    ]),
    (os.path.join('test_ai_models.py'), [
        (r'''    # verification, changeable through WELLNESS_LINE_MODEL.
    'wellness/daily_line.py': 'the line under the Wellness daily quote',
}

''',
         r'''    # verification, changeable through WELLNESS_LINE_MODEL.
    'wellness/daily_line.py': 'the line under the Wellness daily quote',
    # CG-1, 13 Nov 2026 - the seventh: a short birthday or name-day greeting
    # for one of your own celebrations, opened in WhatsApp. The same small
    # model as the daily line, changeable through GREETING_MODEL.
    'pages/views/celebration_gifts.py': 'the celebration greeting',
}

'''),
    ]),
    (os.path.join('alv_rounds.py'), [
        (r'''    # PT-2, 12 Nov 2026 - Release 73: the Today card, a recipe in Wellness.
    '.bak_todaycard',
]

''',
         r'''    # PT-2, 12 Nov 2026 - Release 73: the Today card, a recipe in Wellness.
    '.bak_todaycard',
    # BV-1 + CG-1, 13 Nov 2026 - Releases 74 and 75: the book on demand; gifts.
    '.bak_gifts',
]

'''),
    ]),
    (os.path.join('pages', 'views', 'recipes', 'recipe_crud.py'), [
        (r'''    authors = [{'value': v, 'name': n} for v, n in Recipe.AUTHOR_CHOICES]

    # Serialize filtered recipes for book view (use already-filtered queryset)
    all_recipes_for_book = []
    for r in recipes:
        nutrition_values = None
        if nutrition_sort:
            cache = getattr(r, 'nutrition_cache', None)
            if cache:
                nutrition_values = {
                    'calories': float(cache.calories_per_100g) if cache.calories_per_100g is not None else None,
                    'protein':  float(cache.protein_per_100g)  if cache.protein_per_100g  is not None else None,
                    'carbs':    float(cache.carbs_per_100g)    if cache.carbs_per_100g    is not None else None,
                    'fat':      float(cache.fat_per_100g)      if cache.fat_per_100g      is not None else None,
                }
        all_recipes_for_book.append({
            'recipe_id': r.recipe_id,
            'recipe_name': r.recipe_name,
            'recipe_image': r.photo_url,
            'prep_time': r.prep_time,
            'cook_time': r.cook_time,
            'servings': r.servings,
            'difficulty_level': r.difficulty_level,
            'is_vegetarian': r.is_vegetarian,
            'author': r.author,
            'courses': [c.name for c in r.courses.all()],
            'categories': [c.name for c in r.categories.all()],
            'proteins': [p.name for p in r.proteins.all()],
            'nutrition_values': nutrition_values,
        })

    context = {
''',
         r'''    authors = [{'value': v, 'name': n} for v, n in Recipe.AUTHOR_CHOICES]

    # BV-1, 13 Nov 2026 - the book's recipes, only when the book asks.
    # Every visit used to build all ~290 (135 KB of the page's 876 KB,
    # measured on Live 12 Nov) for a view most visits never open, and
    # evaluating them ran the whole filtered list through its prefetches.
    # The book now fetches this same address with ?book=1 - same filters,
    # same order - when it is first opened.
    if request.GET.get('book') == '1':
        return JsonResponse(_book_rows(recipes, nutrition_sort), safe=False)

    context = {
'''),
        (r'''        # RC-3, 12 Nov 2026 - 'ingredient_categories' went: every ingredient,
        # prefetched on every visit, for a template that never read it.
        'all_recipes_for_book': json.dumps(all_recipes_for_book),
        # Step 3 - nutrition sort
        'nutrition_sort': nutrition_sort,
''',
         r'''        # RC-3, 12 Nov 2026 - 'ingredient_categories' went: every ingredient,
        # prefetched on every visit, for a template that never read it.
        # Step 3 - nutrition sort
        'nutrition_sort': nutrition_sort,
'''),
        (r'''        'cooking_calculation': cooking_calc,
    }

    return render(request, 'preview_imported_recipe.html', context)''',
         r'''        'cooking_calculation': cooking_calc,
    }

    return render(request, 'preview_imported_recipe.html', context)


def _book_rows(recipes, nutrition_sort):
    """BV-1 - the recipe book's rows: the filtered recipes, as the book
    has always read them (moved here unchanged from recipe_management)."""
    all_recipes_for_book = []
    for r in recipes:
        nutrition_values = None
        if nutrition_sort:
            cache = getattr(r, 'nutrition_cache', None)
            if cache:
                nutrition_values = {
                    'calories': float(cache.calories_per_100g) if cache.calories_per_100g is not None else None,
                    'protein':  float(cache.protein_per_100g)  if cache.protein_per_100g  is not None else None,
                    'carbs':    float(cache.carbs_per_100g)    if cache.carbs_per_100g    is not None else None,
                    'fat':      float(cache.fat_per_100g)      if cache.fat_per_100g      is not None else None,
                }
        all_recipes_for_book.append({
            'recipe_id': r.recipe_id,
            'recipe_name': r.recipe_name,
            'recipe_image': r.photo_url,
            'prep_time': r.prep_time,
            'cook_time': r.cook_time,
            'servings': r.servings,
            'difficulty_level': r.difficulty_level,
            'is_vegetarian': r.is_vegetarian,
            'author': r.author,
            'courses': [c.name for c in r.courses.all()],
            'categories': [c.name for c in r.categories.all()],
            'proteins': [p.name for p in r.proteins.all()],
            'nutrition_values': nutrition_values,
        })
    return all_recipes_for_book
'''),
    ]),
    (os.path.join('pages', 'views', '__init__.py'), [
        (r'''from .passports import *  # noqa: F401, F403
from .celebrations import *  # noqa: F401, F403
from .users import *  # noqa: F401, F403
from .administration import *  # noqa: F401, F403
''',
         r'''from .passports import *  # noqa: F401, F403
from .celebrations import *  # noqa: F401, F403
from .celebration_gifts import *  # noqa: F401, F403  CG-1
from .users import *  # noqa: F401, F403
from .administration import *  # noqa: F401, F403
'''),
    ]),
    (os.path.join('pages', 'views', 'celebrations.py'), [
        (r'''from django.views.decorators.http import require_POST

from ..models import CelebrationEvent, Contact, HouseholdMember
from pages.workspace import ensure_workspace

''',
         r'''from django.views.decorators.http import require_POST

from ..models import CelebrationEvent, Contact, Gift, HouseholdMember
from pages.workspace import ensure_workspace

'''),
        (r'''                contact = Contact.objects.for_user(request.user).get(id=contact_id)
                name = contact.name
                contact.delete()
                messages.success(request, f'Contact "{name}" deleted successfully!')
            except Contact.DoesNotExist:
                messages.error(request, 'Contact not found.')
''',
         r'''                contact = Contact.objects.for_user(request.user).get(id=contact_id)
                name = contact.name
                # CG-1, 13 Nov 2026 - gifts survive the contact (SET_NULL,
                # name kept). The one deleting is told now; anyone else
                # with gifts for this person is told on their next visit.
                kept = Gift.objects.filter(owner=request.user, contact=contact)
                n_kept = kept.count()
                kept.update(orphan_told=True)
                contact.delete()
                messages.success(request, f'Contact "{name}" deleted successfully!'
                                 + (f' Your {n_kept} gift record'
                                    f'{"" if n_kept == 1 else "s"} for them '
                                    f'{"is" if n_kept == 1 else "are"} kept in My gifts.'
                                    if n_kept else ''))
            except Contact.DoesNotExist:
                messages.error(request, 'Contact not found.')
'''),
        (r'''    all_events.sort(key=lambda x: x['days_until'])

    return render(request, 'celebration_management.html', {
        'contacts': contacts,
        'upcoming_events': all_events[:10],  # Top 10 upcoming
''',
         r'''    all_events.sort(key=lambda x: x['days_until'])

    # CG-1, 13 Nov 2026 - gifts, on "my own" celebrations only: the
    # contacts with an event this person is relevant to. Private - only
    # their own gift rows are read.
    from . import celebration_gifts as CG
    CG.tell_orphans(request)
    my_members = CG.my_member_ids(request.user)
    my_contacts = set()
    for contact in contacts:
        for event in contact.celebration_events.all():
            event.is_mine = bool(event.relevant_member_ids & my_members)
            if event.is_mine:
                my_contacts.add(contact.id)
    gifts = CG.gifts_by_contact(request.user, my_contacts)
    for contact in contacts:
        contact.is_mine = contact.id in my_contacts
        contact.gift_count = len(gifts.get(contact.id, []))

    return render(request, 'celebration_management.html', {
        # Written out as JSON here rather than with json_script, so the
        # element ids are in the template where the page's scripts read
        # them (test_req_marker reads the template, not the page).
        'gift_json': CG.as_json(gifts),
        'members_json': CG.as_json(sorted(my_members)),
        'gift_counts': {cid: len(rows) for cid, rows in gifts.items()},
        'gift_occasions': Gift.OCCASION_CHOICES,
        'this_year': today.year,
        'contacts': contacts,
        'upcoming_events': all_events[:10],  # Top 10 upcoming
'''),
    ]),
    (os.path.join('pages', 'templates', 'recipe_management.html'), [
        (r'''
// ==================== BOOK VIEW ====================
const BOOK_RECIPES = {{ all_recipes_for_book|safe }};
let bookCurrentSpread = 0;
let bookMode = 'grid';
''',
         r'''
// ==================== BOOK VIEW ====================
// BV-1, 13 Nov 2026 - fetched when the book is first opened, not sent with
// every visit (135 KB of the page, measured on Live). Same address, same
// filters, ?book=1.
let BOOK_RECIPES = [];
let bookLoading = null;
function loadBookRecipes() {
    if (!bookLoading) {
        const q = new URLSearchParams(window.location.search);
        q.set('book', '1');
        bookLoading = fetch(window.location.pathname + '?' + q.toString(),
                            {credentials: 'same-origin'})
            .then(r => r.ok ? r.json() : [])
            .then(d => { BOOK_RECIPES = Array.isArray(d) ? d : []; })
            .catch(() => { bookLoading = null; });
    }
    return bookLoading;
}
let bookCurrentSpread = 0;
let bookMode = 'grid';
'''),
        (r'''        if (btn) btn.classList.toggle('active', n === bookRecipesPerPage);
    });
    renderBookSpread();
}

''',
         r'''        if (btn) btn.classList.toggle('active', n === bookRecipesPerPage);
    });
    loadBookRecipes().then(renderBookSpread);
}

'''),
    ]),
    (os.path.join('pages', 'templates', 'celebration_dashboard.html'), [
        (r'''        <i class="fas fa-calendar-alt"></i> View Events
    </a>
    <button type="button" class="btn action-secondary" data-toggle="modal" data-target="#celebration_dashboardHelpModal" title="Help">
            <i class="fas fa-question-circle"></i> Help
''',
         r'''        <i class="fas fa-calendar-alt"></i> View Events
    </a>
    {# CG-1, 13 Nov 2026 - My gifts and the Christmas list. #}
    <a href="{% url 'celebration_gifts' %}" class="btn action-secondary">
        <i class="fas fa-gift"></i> My gifts
    </a>
    <button type="button" class="btn action-secondary" data-toggle="modal" data-target="#celebration_dashboardHelpModal" title="Help">
            <i class="fas fa-question-circle"></i> Help
'''),
        (r'''                <a href="{% url 'celebration_calendar' %}" class="action-more-item" role="menuitem">
                    <i class="fas fa-calendar-alt"></i> View Events
                </a>
                <button type="button" class="action-more-item" role="menuitem"
''',
         r'''                <a href="{% url 'celebration_calendar' %}" class="action-more-item" role="menuitem">
                    <i class="fas fa-calendar-alt"></i> View Events
                </a>
                <a href="{% url 'celebration_gifts' %}" class="action-more-item" role="menuitem">
                    <i class="fas fa-gift"></i> My gifts
                </a>
                <button type="button" class="action-more-item" role="menuitem"
'''),
    ]),
    (os.path.join('pages', 'templates', 'celebration_management.html'), [
        (r'''    #clearAllBtn { flex: 0 0 auto; }
}
</style>

''',
         r'''    #clearAllBtn { flex: 0 0 auto; }
}

/* CG-1, 13 Nov 2026 - Gifts and Greeting: small outline buttons, a list,
   and the pop-up's own button row (not a modal-footer). */
.gift-btn {
    text-decoration: none;
    display: inline-flex; align-items: center; gap: 6px; min-height: 36px;
    margin-top: 8px; padding: 4px 12px; border-radius: 18px;
    border: 1px solid currentColor; font-size: 0.9rem; cursor: pointer;
    color: var(--alv-accent);
}
button.gift-btn { background: transparent; }
.greet-btn { margin-top: 0; margin-left: 8px; }
.gift-count { font-weight: 700; }
.gift-list { list-style: none; padding: 0; margin: 0 0 12px; }
.gift-list li { display: flex; gap: 10px; align-items: center; padding: 8px 0; border-top: 1px solid currentColor; border-top-color: rgba(127,127,127,.25); }
.gift-list li:first-child { border-top: 0; }
.gift-list .gift-when { min-width: 88px; font-weight: 600; font-size: 0.9rem; }
.gift-list .gift-what { flex: 1; }
.gift-list .gift-idea { font-style: italic; }
.gift-list .gift-row-btn { border: 0; padding: 6px 8px; min-height: 36px; cursor: pointer; color: var(--alv-ink-soft); }
.gift-list button.gift-row-btn { background: transparent; }
.gift-kind { display: flex; gap: 20px; margin-bottom: 10px; }
.gift-actions { display: flex; gap: 10px; justify-content: flex-end; flex-wrap: wrap; margin-top: 8px; }
</style>

'''),
        (r'''        {% endif %}

        <button class="btn action-secondary" id="viewToggleBtn" onclick="toggleView()">
            <i class="fas fa-th-large"></i> Compact View
''',
         r'''        {% endif %}

        {# CG-1, 13 Nov 2026 - My gifts and the Christmas list. #}
        <a href="{% url 'celebration_gifts' %}" class="btn action-secondary">
            <i class="fas fa-gift"></i> My gifts
        </a>

        <button class="btn action-secondary" id="viewToggleBtn" onclick="toggleView()">
            <i class="fas fa-th-large"></i> Compact View
'''),
        (r'''                </button>
                {% endif %}
                <button type="button" class="action-more-item" role="menuitem" id="viewToggleMoreItem" onclick="toggleView()">
                    <i class="fas fa-th-large"></i> Compact View
''',
         r'''                </button>
                {% endif %}
                <a href="{% url 'celebration_gifts' %}" class="action-more-item" role="menuitem">
                    <i class="fas fa-gift"></i> My gifts
                </a>
                <button type="button" class="action-more-item" role="menuitem" id="viewToggleMoreItem" onclick="toggleView()">
                    <i class="fas fa-th-large"></i> Compact View
'''),
        (r'''                    </div>
                    {% endif %}
                </div>
                <!-- Desktop contact actions (hidden on mobile via CSS) -->
''',
         r'''                    </div>
                    {% endif %}
                    {# CG-1 - gifts, private, on my own celebrations only. #}
                    {% if contact.is_mine %}
                    <button type="button" class="gift-btn" id="gifts-{{ contact.id }}" data-gift-open="{{ contact.id }}" data-gift-name="{{ contact.name }}">
                        <i class="fas fa-gift"></i> Gifts{% if contact.gift_count %} <span class="gift-count">{{ contact.gift_count }}</span>{% endif %}
                    </button>
                    {% endif %}
                </div>
                <!-- Desktop contact actions (hidden on mobile via CSS) -->
'''),
        (r'''                                {% elif event.get_years %}
                                    ({{ event.get_years }} years)
                                {% endif %}
                            </div>
''',
         r'''                                {% elif event.get_years %}
                                    ({{ event.get_years }} years)
                                {% endif %}
                                {% if event.is_mine %}
                                {# A link, not a button: the contact pop-up copies this row and drives its buttons by position. #}
                                <a href="#" role="button" class="gift-btn greet-btn" data-greet="{{ event.id }}" data-greet-name="{{ contact.name }}" data-greet-what="{{ event.get_event_type_display }}">
                                    <i class="fab fa-whatsapp"></i> Greeting
                                </a>
                                {% endif %}
                            </div>
'''),
        (r'''                        <i class="fas fa-exclamation-triangle fa-3x text-danger mb-3"></i>
                        <h5>Delete contact "<span id="delete_contact_name"></span>"?</h5>
                        <p class="text-muted">This will also delete all events for this contact. This action cannot be undone.</p>
                    </div>
''',
         r'''                        <i class="fas fa-exclamation-triangle fa-3x text-danger mb-3"></i>
                        <h5>Delete contact "<span id="delete_contact_name"></span>"?</h5>
                        <p class="text-muted small" data-gift-kept>Any gifts you recorded for them are kept in My gifts.</p>
                        <p class="text-muted">This will also delete all events for this contact. This action cannot be undone.</p>
                    </div>
'''),
        (r'''                    <button type="submit" class="btn action-secondary action-danger">Delete Event</button>
                </div>
            </form>
        </div>
    </div>
</div>
''',
         r'''                    <button type="submit" class="btn action-secondary action-danger">Delete Event</button>
                </div>
            </form>
        </div>
    </div>
</div>

{% comment %} CG-1, 13 Nov 2026 - the gift pop-up, the "you have gifts for them" warning, and the greeting. Private: filled from this person's own gift rows only. {% endcomment %}
<div class="modal fade" id="giftModal" tabindex="-1" role="dialog" aria-labelledby="giftModalTitle">
    <div class="modal-dialog modal-fullscreen-mobile" role="document">
        <div class="modal-content">
            <div class="modal-header alv-modal-head">
                <h5 class="modal-title" id="giftModalTitle">Gifts</h5>
                <button type="button" class="close" data-dismiss="modal" aria-label="Close"><span>&times;</span></button>
            </div>
            <div class="modal-body">
                <p class="text-muted small mb-2">Only you can see these.</p>
                <ul class="gift-list" id="giftList"></ul>
                <form method="post" action="{% url 'celebration_gift_save' %}" class="gift-form" id="giftForm">
                    {% csrf_token %}
                    <input type="hidden" name="action" value="add">
                    <input type="hidden" name="contact_id" id="gift_contact_id">
                    <input type="hidden" name="next" id="gift_next">
                    <div class="gift-kind" role="radiogroup" aria-label="Given or an idea">
                        <label><input type="radio" name="kind" value="given" checked> Given</label>
                        <label><input type="radio" name="kind" value="idea"> An idea</label>
                    </div>
                    <div class="form-group">
                        <label for="gift_what"><strong>What</strong></label>
                        <input type="text" class="form-control" id="gift_what" name="what" maxlength="200" required>
                    </div>
                    <div class="form-row">
                        <div class="col-6 form-group">
                            <label for="gift_occasion"><strong>Occasion</strong></label>
                            <select class="form-control" id="gift_occasion" name="occasion">
                                {% for v, n in gift_occasions %}<option value="{{ v }}">{{ n }}</option>{% endfor %}
                            </select>
                        </div>
                        <div class="col-3 form-group">
                            <label for="gift_year"><strong>Year</strong></label>
                            <input type="number" class="form-control" id="gift_year" name="year" value="{{ this_year }}" min="1950" max="{{ this_year|add:5 }}">
                        </div>
                        <div class="col-3 form-group">
                            <label for="gift_amount"><strong id="gift_amount_label">Cost</strong></label>
                            <input type="text" class="form-control" id="gift_amount" name="amount" inputmode="decimal" placeholder="€">
                        </div>
                    </div>
                    <div class="gift-actions">
                        <button type="button" class="btn action-secondary" data-dismiss="modal">Close</button>
                        <button type="submit" class="btn action-primary"><i class="fas fa-plus"></i> Add</button>
                    </div>
                </form>
                <form method="post" action="{% url 'celebration_gift_save' %}" id="giftRowForm" hidden>
                    {% csrf_token %}
                    <input type="hidden" name="action" id="gift_row_action">
                    <input type="hidden" name="gift_id" id="gift_row_id">
                    <input type="hidden" name="what" id="gift_row_what">
                    <input type="hidden" name="amount" id="gift_row_amount">
                    <input type="hidden" name="next" id="gift_row_next">
                </form>
            </div>
        </div>
    </div>
</div>

<div class="modal fade" id="giftKeepModal" tabindex="-1" role="dialog" aria-labelledby="giftKeepTitle">
    <div class="modal-dialog modal-fullscreen-mobile" role="document">
        <div class="modal-content">
            <div class="modal-header alv-modal-head">
                <h5 class="modal-title" id="giftKeepTitle">You have gifts recorded</h5>
                <button type="button" class="close" data-dismiss="modal" aria-label="Close"><span>&times;</span></button>
            </div>
            <div class="modal-body">
                <p id="giftKeepText"></p>
                <p class="text-muted small">They are kept, and stay in My gifts. The Gifts button just won't show on this contact while none of their celebrations are yours.</p>
                <div class="gift-actions">
                    <button type="button" class="btn action-secondary" data-gift-keep="cancel">Keep me on</button>
                    <button type="button" class="btn action-primary" data-gift-keep="go">Take me off</button>
                </div>
            </div>
        </div>
    </div>
</div>

<div class="modal fade" id="greetingModal" tabindex="-1" role="dialog" aria-labelledby="greetingTitle">
    <div class="modal-dialog modal-fullscreen-mobile" role="document">
        <div class="modal-content">
            <div class="modal-header alv-modal-head">
                <h5 class="modal-title" id="greetingTitle">Greeting</h5>
                <button type="button" class="close" data-dismiss="modal" aria-label="Close"><span>&times;</span></button>
            </div>
            <div class="modal-body">
                <div class="form-group">
                    <label for="greeting_language"><strong>Language</strong></label>
                    <select class="form-control" id="greeting_language">
                        <option value="English">English</option>
                        <option value="Greek">Greek</option>
                    </select>
                </div>
                <div class="form-group">
                    <label for="greeting_text"><strong>Message</strong></label>
                    <small class="text-muted d-block mb-1">Written by Claude - change anything.</small>
                    <textarea class="form-control" id="greeting_text" rows="5" maxlength="600"></textarea>
                    <small class="text-muted" id="greeting_status" aria-live="polite"></small>
                </div>
                <div class="gift-actions">
                    <button type="button" class="btn action-secondary" id="greeting_again"><i class="fas fa-redo"></i> Write another</button>
                    <a class="btn action-primary" id="greeting_send" href="#" target="_blank" rel="noopener"><i class="fab fa-whatsapp"></i> Open in WhatsApp</a>
                </div>
            </div>
        </div>
    </div>
</div>
'''),
        (r'''</script>

{% endblock %}''',
         r'''</script>


<script type="application/json" id="gift-data">{{ gift_json }}</script>
<script type="application/json" id="my-member-ids">{{ members_json }}</script>
<script>
/* CG-1, 13 Nov 2026 - gifts (private: this page only ever holds the
   signed-in person's own rows), the warning before taking yourself off a
   contact's last celebration while gifts are recorded for them, and the
   greeting written by Claude and opened in WhatsApp. */
(function () {
    var gd = document.getElementById('gift-data');
    var md = document.getElementById('my-member-ids');
    var GIFTS = gd ? JSON.parse(gd.textContent || '{}') : {};
    var MINE = md ? JSON.parse(md.textContent || '[]') : [];
    var here = window.location.pathname;

    function el(tag, cls, text) {
        var e = document.createElement(tag);
        if (cls) e.className = cls;
        if (text != null) e.textContent = text;
        return e;
    }
    function rowPost(action, id, what, amount, cid) {
        document.getElementById('gift_row_action').value = action;
        document.getElementById('gift_row_id').value = id;
        document.getElementById('gift_row_what').value = what || '';
        document.getElementById('gift_row_amount').value = amount || '';
        document.getElementById('gift_row_next').value = here + '?gifts=' + cid + '#gifts-' + cid;
        document.getElementById('giftRowForm').submit();
    }
    function openGifts(cid, name) {
        document.getElementById('giftModalTitle').textContent = 'Gifts for ' + name;
        document.getElementById('gift_contact_id').value = cid;
        document.getElementById('gift_next').value = here + '?gifts=' + cid + '#gifts-' + cid;
        var list = document.getElementById('giftList');
        list.textContent = '';
        var rows = GIFTS[cid] || [];
        if (!rows.length) list.appendChild(el('li', 'text-muted', 'Nothing recorded yet.'));
        rows.forEach(function (g) {
            var li = el('li');
            li.appendChild(el('span', 'gift-when', g.year + ' ' + g.occasion));
            var w = el('span', 'gift-what' + (g.given ? '' : ' gift-idea'),
                       (g.given ? g.what : 'Idea: ' + g.idea) +
                       (g.given && g.cost ? ' - €' + g.cost.replace(/\.00$/, '') : '') +
                       (!g.given && g.budget ? ' - about €' + g.budget.replace(/\.00$/, '') : ''));
            li.appendChild(w);
            if (!g.given) {
                var given = el('button', 'gift-row-btn', 'Given');
                given.type = 'button';
                given.title = 'Mark this idea as given';
                given.addEventListener('click', function () {
                    var cost = window.prompt('What did it cost? (leave empty if you would rather not say)', g.budget || '');
                    if (cost === null) return;
                    rowPost('given', g.id, g.idea, cost, cid);
                });
                li.appendChild(given);
            }
            var del = el('button', 'gift-row-btn', '\u00d7');
            del.type = 'button';
            del.title = 'Remove';
            del.setAttribute('aria-label', 'Remove ' + (g.what || 'this'));
            del.addEventListener('click', function () { rowPost('delete', g.id, '', '', cid); });
            li.appendChild(del);
            list.appendChild(li);
        });
        $('#giftModal').modal('show');
    }
    document.addEventListener('click', function (e) {
        var b = e.target.closest('[data-gift-open]');
        if (b) openGifts(b.getAttribute('data-gift-open'), b.getAttribute('data-gift-name'));
    });
    document.querySelectorAll('input[name="kind"]').forEach(function (r) {
        r.addEventListener('change', function () {
            document.getElementById('gift_amount_label').textContent =
                this.value === 'idea' ? 'Budget' : 'Cost';
        });
    });
    // Back from saving: open the same pop-up again.
    var again = new URLSearchParams(window.location.search).get('gifts');
    if (again) {
        var btn = document.querySelector('[data-gift-open="' + again + '"]');
        if (btn) openGifts(again, btn.getAttribute('data-gift-name'));
    }

    // THE WARNING. Taking yourself off the last of someone's celebrations
    // hides their Gifts button; the gifts themselves are never touched.
    if (typeof window.updateNotification === 'function') {
        var original = window.updateNotification;
        var pending = null;
        window.updateNotification = function (cb) {
            var mine = MINE.indexOf(parseInt(cb.dataset.memberId, 10)) !== -1;
            var card = cb.closest('.contact-card');
            var gb = card && card.querySelector('[data-gift-open]');
            var cid = gb ? gb.getAttribute('data-gift-open') : null;
            var rows = cid ? (GIFTS[cid] || []) : [];
            if (cb.checked || !mine || !rows.length) return original(cb);
            var stillMine = Array.prototype.some.call(
                card.querySelectorAll('input.notify-checkbox'), function (x) {
                    return x !== cb && x.checked &&
                        MINE.indexOf(parseInt(x.dataset.memberId, 10)) !== -1;
                });
            if (stillMine) return original(cb);
            var given = rows.filter(function (g) { return g.given; }).length;
            var ideas = rows.length - given;
            var name = card.querySelector('.contact-name').textContent;
            document.getElementById('giftKeepText').textContent =
                'You have ' + given + ' gift' + (given === 1 ? '' : 's') + ' and ' +
                ideas + ' idea' + (ideas === 1 ? '' : 's') + ' recorded for ' + name + '.';
            pending = cb;
            $('#giftKeepModal').modal('show');
        };
        document.addEventListener('click', function (e) {
            var b = e.target.closest('[data-gift-keep]');
            if (!b || !pending) return;
            var cb = pending;
            pending = null;
            $('#giftKeepModal').modal('hide');
            if (b.getAttribute('data-gift-keep') === 'go') original(cb);
            else cb.checked = true;
        });
        if (window.jQuery) $('#giftKeepModal').on('hidden.bs.modal', function () {
            if (pending) { pending.checked = true; pending = null; }
        });
    }

    // THE GREETING - Claude writes it; WhatsApp sends it.
    var greetId = null, greetNumber = '';
    function sendLink() {
        var t = document.getElementById('greeting_text').value;
        document.getElementById('greeting_send').href =
            'https://wa.me/' + greetNumber + '?text=' + encodeURIComponent(t);
    }
    function writeGreeting() {
        var status = document.getElementById('greeting_status');
        status.textContent = 'Claude is writing...';
        var body = new FormData();
        body.append('language', document.getElementById('greeting_language').value);
        body.append('csrfmiddlewaretoken', document.querySelector('[name=csrfmiddlewaretoken]').value);
        fetch('/celebrations/event/' + greetId + '/greeting/', {method: 'POST', body: body, credentials: 'same-origin'})
            .then(function (r) { return r.json(); })
            .then(function (d) {
                if (d.text) {
                    document.getElementById('greeting_text').value = d.text;
                    greetNumber = d.number || '';
                    status.textContent = greetNumber ? '' : 'No phone number on this contact - WhatsApp will ask who to send it to.';
                } else {
                    status.textContent = d.error || 'Could not write one just now.';
                }
                sendLink();
            })
            .catch(function () { status.textContent = 'Could not reach Claude just now.'; });
    }
    document.addEventListener('click', function (e) {
        var b = e.target.closest('[data-greet]');
        if (!b) return;
        e.preventDefault();
        greetId = b.getAttribute('data-greet');
        document.getElementById('greetingTitle').textContent =
            b.getAttribute('data-greet-what') + ' greeting for ' + b.getAttribute('data-greet-name');
        document.getElementById('greeting_text').value = '';
        $('#greetingModal').modal('show');
        writeGreeting();
    });
    document.getElementById('greeting_again').addEventListener('click', writeGreeting);
    document.getElementById('greeting_language').addEventListener('change', writeGreeting);
    document.getElementById('greeting_text').addEventListener('input', sendLink);
})();
</script>

{% endblock %}'''),
    ]),
    (os.path.join('pages', 'help_content', 'administration.html'), [
        (r'''    <div style="background:#fff3cd; border:1px solid #ffc107; border-radius:8px; padding:14px; font-size:13px; color:#856404;">
      <i class="fas fa-info-circle"></i> <strong>Note:</strong> Event dates are annual &mdash; only the day and month matter. The year is ignored so events repeat every year automatically.
    </div>
  </article>
''',
         r'''    <div style="background:#fff3cd; border:1px solid #ffc107; border-radius:8px; padding:14px; font-size:13px; color:#856404;">
      <i class="fas fa-info-circle"></i> <strong>Note:</strong> Event dates are annual &mdash; only the day and month matter. The year is ignored so events repeat every year automatically.
    </div>
  </article>

  <!-- CG-1, 13 Nov 2026 - gifts, My gifts, the Christmas list and greetings. -->
  <article data-tab-slug="cel-gifts"
           data-tab-name="Gifts"
           data-tab-icon="fa-gift">
    <h6 style="font-weight:700; color:#2c3e50; margin-bottom:16px; border-bottom:2px solid #667eea; padding-bottom:6px;"><i class="fas fa-gift" style="color:#667eea;"></i> Gifts, the Christmas List and Greetings</h6>
    <p style="font-size:14px; color:#6c757d; margin-bottom:16px;"><strong>Private.</strong> Gifts you record are seen by you and nobody else. The <strong>Gifts</strong> button shows on a contact when one of their celebrations is yours &mdash; you are ticked under &ldquo;Relevant to&rdquo;.</p>
    <p style="font-size:13px; color:#6c757d; margin-bottom:12px;"><strong>Gifts</strong> on a contact: record something you gave (with the cost, if you want) or an idea for later (with a budget). An idea has a <strong>Given</strong> button for when you buy it.</p>
    <p style="font-size:13px; color:#6c757d; margin-bottom:12px;"><strong>My gifts</strong> (from the Celebrations pages): everything you have given, year by year with the year&rsquo;s total, and your ideas still to use.</p>
    <p style="font-size:13px; color:#6c757d; margin-bottom:12px;"><strong>Christmas list</strong> (a tab in My gifts): pick the year, tick the people and add them. For each, write <strong>the plan</strong> (an idea and a budget), then when you buy, <strong>what you bought</strong> and its cost &mdash; it can be something else entirely; the plan is kept. Tick <strong>Bought</strong>. The totals show planned against spent. <strong>Shopping list to me</strong> opens WhatsApp with everyone still to buy for &mdash; choose your own chat and send.</p>
    <p style="font-size:13px; color:#6c757d; margin-bottom:12px;"><strong>Greeting</strong> on one of your celebrations: Claude writes a short message in English or Greek. Change anything, then <strong>Open in WhatsApp</strong> &mdash; it goes to the contact&rsquo;s phone number, or WhatsApp asks who to send it to.</p>
    <div style="background:#fff3cd; border:1px solid #ffc107; border-radius:8px; padding:14px; font-size:13px; color:#856404;">
      <i class="fas fa-info-circle"></i> <strong>Never lost:</strong> taking yourself off someone&rsquo;s last celebration warns you first, and deleting a contact keeps your gifts for them, with the name, in My gifts.
    </div>
  </article>
'''),
    ]),
    (os.path.join('pages', 'models.py'), [
        (r'''        return emails

class EventNotification(models.Model):
    """Track which notifications have been sent"""
''',
         r'''        return emails

class Gift(models.Model):
    """CG-1, 13 Nov 2026 - a present given, an idea for one, or a line on the
    Christmas list. Demetri, 12 Nov: "Gifts must be private to the person
    capturing them. We don't need shared gifts."

    PRIVATE: every read is filtered by owner; nobody else ever sees a row.
    NEVER LOST: it hangs on the contact, not the event, and the contact may
    go (SET_NULL) - contact_name keeps who it was for, and the owner is
    told once (orphan_told) on their next visit to Celebrations.
    PLAN AND PURCHASE ARE SEPARATE (Demetri, 12 Nov: "If I decided to plan
    one thing and then buy a completely different gift, that should be OK
    as well"): idea and budget are the plan; gift and cost are what was
    bought. An idea is a row not yet given.
    """
    OCCASION_CHOICES = [
        ('birthday', 'Birthday'),
        ('nameday', 'Name day'),
        ('anniversary', 'Anniversary'),
        ('christmas', 'Christmas'),
        ('other', 'Other'),
    ]
    owner = models.ForeignKey(User, on_delete=models.CASCADE,
                              related_name='gifts')
    contact = models.ForeignKey(Contact, on_delete=models.SET_NULL,
                                null=True, blank=True, related_name='gifts')
    contact_name = models.CharField(max_length=200)
    year = models.PositiveIntegerField()
    occasion = models.CharField(max_length=20, choices=OCCASION_CHOICES,
                                default='birthday')
    idea = models.CharField(max_length=200, blank=True)
    budget = models.DecimalField(max_digits=9, decimal_places=2, null=True,
                                 blank=True)
    gift = models.CharField(max_length=200, blank=True)
    cost = models.DecimalField(max_digits=9, decimal_places=2, null=True,
                               blank=True)
    given = models.BooleanField(default=False)
    note = models.CharField(max_length=200, blank=True)
    orphan_told = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'celebration_gifts'
        ordering = ['-year', 'contact_name', 'id']

    def __str__(self):
        return '%s, %s %s' % (self.contact_name, self.get_occasion_display(),
                              self.year)

    @property
    def who(self):
        return self.contact.name if self.contact_id else self.contact_name

    @property
    def what(self):
        """What it is: the gift bought, else the plan."""
        return self.gift or self.idea


class EventNotification(models.Model):
    """Track which notifications have been sent"""
'''),
    ]),
    (os.path.join('pages', 'urls.py'), [
        (r'''    path('celebrations/calendar/', views.celebration_calendar, name='celebration_calendar'),
    path('celebrations/import/', views.import_celebrations, name='import_celebrations'),
    path('celebrations/event/<int:event_id>/update-notifications/', views.update_event_notifications, name='update_event_notifications'),

''',
         r'''    path('celebrations/calendar/', views.celebration_calendar, name='celebration_calendar'),
    path('celebrations/import/', views.import_celebrations, name='import_celebrations'),
    # CG-1, 13 Nov 2026 - gifts, My gifts and the Christmas list, greetings.
    path('celebrations/gifts/', views.my_gifts, name='celebration_gifts'),
    path('celebrations/gifts/save/', views.celebration_gift_save, name='celebration_gift_save'),
    path('celebrations/event/<int:event_id>/greeting/', views.celebration_greeting, name='celebration_greeting'),
    path('celebrations/event/<int:event_id>/update-notifications/', views.update_event_notifications, name='update_event_notifications'),

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
    raise SystemExit('CG-1 REFUSED: %s' % msg)


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
    if "'test_gifts.py'" in read(pq):
        print('CG-1 already applied.')
        return 0
    if "'test_wellness_twentyfive.py'" not in read(pq):
        refuse('Release 73 is not applied - this round registers after it.')
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
        print('CG-1 --check: %d file(s) would change, none written; %d '
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
    print('CG-1 applied - the recipe book on demand; gifts, My gifts, the Christmas list.')
    print('      MIGRATION 0119 - run migrate before pushing.')
    print('      %d file(s) written, backed up to %s' % (len(out), SUFFIX))
    print('      %d file(s) ship with it, wired in rather than written'
          % len(CREATES))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
