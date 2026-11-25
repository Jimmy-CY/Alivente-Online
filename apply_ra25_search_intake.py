# -*- coding: utf-8 -*-
"""apply_ra25_search_intake.py - round RA25, 25 Nov 2026.

RELEASE RA25 - THE SEARCH REPORTS INTO THE APP, AND NO TEMPLATE CARDS.

    - NEW, shipped beside this file:
        acquisitions/api.py - the door Claude's search tasks use: the
          active scenarios (GET api/scenarios/), start a run (POST
          api/runs/), report to it (POST api/runs/<id>/report/). A shared
          key, ACQ_INTAKE_KEY, on Railway and in the search task - never in
          a file or chat. Without it every call answers 503.
        acquisitions/intake.py - what a report does: facts in, the scoring
          engine decides what is added; a price change noted; every link
          gone = Removed; a status you set never changed.
        test_ra25_search_intake.py.
    - urls.py: the three api/ routes. pages/middleware.py: acquisitions/api/
      needs no login (the key is checked by the view); the screens do.
    - firing.py: a start from the app also gives the scenario ids.
    - views.py, scenarios.html, scenario_edit.html: no "Start from a
      template" cards; New scenario opens the wizard, empty.
    - RETIRED: acquisitions/presets.py (moved to presets.py.bak_ra25).
    - pages/help_content/acquisitions.html: how the searches report, the
      key, no template cards.
    - test_ra19_acquisitions_screens.py, test_ra22_rules_wizard.py taught
      the changes (each says RA25).
    - Registers test_ra25_search_intake.py.

Stands on RA24. Idempotent. Edits backed up to .bak_ra25. No migration.
    python apply_ra25_search_intake.py --check    (changes nothing)
    python apply_ra25_search_intake.py
"""

# --- CONSOLE ENCODING ----------------------------------- 16 Sep 2026 --
# This file prints text it read out of the templates, and some of that
# text is not ASCII - projects/project_task_list.html carries a Greek
# heading behind the language switch, and it will not be the last. On
# Windows, Python writes stdout as cp1252 whenever it is not a UTF-8
# console, and cp1252 cannot encode Greek: the print itself raises
# UnicodeEncodeError and the run dies part-way through. A crash blocks a
# push exactly as hard as a failure and says far less about why.
#
# So keep the encoding the console really has - forcing UTF-8 only moves
# the problem to whoever decodes us - and change the ERROR HANDLER, so a
# character the console cannot draw arrives as a question mark instead of
# ending the run. stderr too, because a traceback is a print as well.
# Guarded, because stdout is not always a stream that can be told.
# See test_console_encoding.py.
import sys as _sys
for _stream in (_sys.stdout, _sys.stderr):
    try:
        _stream.reconfigure(errors='replace')
    except Exception:
        pass
# ------------------------------------------------------------------------




import json
import os
import shutil
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
SUFFIX = '.bak_ra25'
SHIPPED = ('acquisitions/api.py',
           'acquisitions/intake.py',
           'test_ra25_search_intake.py')
RETIRED = ('acquisitions/presets.py',)
# (file, the text it holds now, what it becomes) - exact, line endings
# included.
EDITS = json.loads('[["Push-PendingChanges.ps1", "    \'test_ra24_acq_flow.py\'\\n", "    \'test_ra24_acq_flow.py\',\\n    # RA25, 25 Nov 2026 - the search reports into the app; no template cards.\\n    \'test_ra25_search_intake.py\'\\n"], ["acquisitions/firing.py", "    return (\\"Alivente Online asks for a search now of %d scenario%s: %s. \\"\\r\\n            \\"Search only these, then report to the app as usual.\\"\\r\\n            % (len(scenarios), \\"\\" if len(scenarios) == 1 else \\"s\\", names))\\r\\n", "    # RA25 - and by id, for the app\'s api/scenarios/?only= (intake.py).\\r\\n    ids = \\",\\".join(str(s.pk) for s in scenarios if getattr(s, \\"pk\\", None))\\r\\n    return (\\"Alivente Online asks for a search now of %d scenario%s: %s%s. \\"\\r\\n            \\"Search only these, then report to the app as usual.\\"\\r\\n            % (len(scenarios), \\"\\" if len(scenarios) == 1 else \\"s\\", names,\\r\\n               \\" (scenario ids %s)\\" % ids if ids else \\"\\"))\\r\\n"], ["acquisitions/templates/acquisitions/scenario_edit.html", "{% if can_edit and not s.pk and not preset %}\\r\\n", "{% if can_edit and not s.pk %}\\r\\n"], ["acquisitions/templates/acquisitions/scenarios.html", "{% if can_edit %}\\r\\n<h3 class=\\"acq-section-h mt-4\\">Start from a template</h3>\\r\\n<div class=\\"acq-grid\\">\\r\\n  {% for key, t in templates.items %}\\r\\n  <a class=\\"alv-card\\" href=\\"{% url \'acquisitions:scenario_new\' %}?template={{ key }}\\" style=\\"text-decoration: none\\">\\r\\n    <div class=\\"alv-card-head\\"><i class=\\"fas {{ t.icon }}\\" aria-hidden=\\"true\\"></i> <span class=\\"alv-card-title\\">{{ t.title }}</span></div>\\r\\n    <div class=\\"alv-card-body acq-muted\\">{{ t.blurb }}</div>\\r\\n  </a>\\r\\n  {% endfor %}\\r\\n</div>\\r\\n{% endif %}\\r\\n", "{# RA25, 25 Nov 2026 - no template cards: New scenario opens the wizard. #}\\r\\n"], ["acquisitions/templates/acquisitions/scenarios.html", "    <div class=\\"alv-empty-hint\\">{% if q or show != \'all\' %}Clear the search or choose All.{% else %}Start one from a template below.{% endif %}</div>\\r\\n", "    <div class=\\"alv-empty-hint\\">{% if q or show != \'all\' %}Clear the search or choose All.{% else %}Press New scenario to build one step by step.{% endif %}</div>\\r\\n"], ["acquisitions/urls.py", "    path(\\"runs/\\", views.runs, name=\\"runs\\"),\\r\\n", "    path(\\"runs/\\", views.runs, name=\\"runs\\"),\\r\\n    # RA25 - the door Claude\'s search tasks use (a key, no login: api.py).\\r\\n    path(\\"api/scenarios/\\", api.scenarios, name=\\"api_scenarios\\"),\\r\\n    path(\\"api/runs/\\", api.run_start, name=\\"api_run_start\\"),\\r\\n    path(\\"api/runs/<int:pk>/report/\\", api.run_report, name=\\"api_run_report\\"),\\r\\n"], ["acquisitions/urls.py", "from . import views\\r\\n", "from . import api, views\\r\\n"], ["acquisitions/views.py", "                 notify=Scenario.NOTIFY_CHOICES, preset=tpl)\\r\\n", "                 notify=Scenario.NOTIFY_CHOICES)\\r\\n"], ["acquisitions/views.py", "        if tpl in presets.TEMPLATES:\\r\\n            t = presets.TEMPLATES[tpl]\\r\\n            scenario.name = t[\\"title\\"]\\r\\n            scenario.property_type = t[\\"property_type\\"]\\r\\n            scenario.deal = t.get(\\"deal\\", \\"buy\\")      # RA22 - Home to rent\\r\\n            rows = presets.criteria_dicts(tpl)\\r\\n            site_ids = set(Website.objects.filter(is_active=True).values_list(\\"pk\\", flat=True))\\r\\n", "        # RA25, 25 Nov 2026 - no templates: a new scenario is built in the\\r\\n        # wizard (Demetri: \\"due to the fact that we have a Wizard, these\\r\\n        # templates are not needed ... We can remove this section\\").\\r\\n"], ["acquisitions/views.py", "    tpl = request.GET.get(\\"template\\")\\r\\n", ""], ["acquisitions/views.py", "                 n_paused=sum(1 for s in everything if not s.is_active),\\r\\n                 templates=presets.TEMPLATES)\\r\\n", "                 n_paused=sum(1 for s in everything if not s.is_active))\\r\\n"], ["acquisitions/views.py", "from . import firing, presets, services as S\\r\\n", "from . import firing, services as S\\r\\n"], ["acquisitions/views.py", "explains how to start one from Claude.\\r\\n", "explains how to start one from Claude.\\r\\n\\r\\nRA25, 25 Nov 2026 - the connector: the search tasks read the scenarios and\\r\\nreport into the app through api.py (a key, no login); intake.py does it.\\r\\n"], ["alv_rounds.py", "    \'.bak_ra24\',\\n", "    \'.bak_ra24\',\\n    # RA25, 25 Nov 2026 - the search reports into the app; no template cards.\\n    \'.bak_ra25\',\\n"], ["pages/help_content/acquisitions.html", "    <p><strong>Search runs</strong> lists every search: where it ran (the cloud or your PC), how long it took, the sites searched, the listings checked and added, and whether it was complete. Choose one to see each site&rsquo;s result, the summary it sent, and any PC search that finished it.</p>\\r\\n", "    <p><strong>Search runs</strong> lists every search: where it ran (the cloud or your PC), how long it took, the sites searched, the listings checked and added, and whether it was complete. Choose one to see each site&rsquo;s result, the summary it sent, and any PC search that finished it.</p>\\r\\n    <p><strong>How the searches report to the app.</strong> Claude&rsquo;s search tasks read your active scenarios from the app &mdash; their areas, websites and rules, and the listings each already tracks &mdash; and send back what they find: each listing&rsquo;s facts as the listing states them, Claude&rsquo;s answers to the rules it checks, and how each website went. <strong>The app does the scoring</strong>: a listing that clearly fails a Must, or leaves more Musts unanswered than the scenario allows, is not added; a price change is recorded and noted; a listing whose every link has gone is marked Removed. A status you set yourself is never changed. Each search appears here as a run, with its summary when it finishes.</p>\\r\\n    <p><strong>Connecting them, once.</strong> The searches use a private key that only Railway and the search task know. Make a long random one (at least 32 characters &mdash; a password manager&rsquo;s generator is ideal) and put it on Railway as <strong>ACQ_INTAKE_KEY</strong>; the search task gets the same key in its own settings. Never paste it in a chat, an email or a file. Until it is set, the app accepts nothing from a search. If you ever change it, change it in both places.</p>\\r\\n"], ["pages/help_content/acquisitions.html", "    <p>A <strong>scenario</strong> is one search: what to look for, which websites to search (<strong>Where to look</strong>), how often, and how listings are scored. <strong>New scenario</strong> starts an empty one, in <strong>Build rules step by step</strong>; the three cards under the list start one from a template (home to renovate, development plot, home to rent). Nothing is saved until you press <strong>Save scenario</strong>.</p>\\r\\n", "    <p>A <strong>scenario</strong> is one search: what to look for, which websites to search (<strong>Where to look</strong>), how often, and how listings are scored. <strong>New scenario</strong> starts an empty one, in <strong>Build rules step by step</strong>, which asks what you are looking for and writes its rules. Nothing is saved until you press <strong>Save scenario</strong>.</p>\\r\\n"], ["pages/middleware.py", "            \'travel/app/\',\\n", "            \'travel/app/\',\\n            # RA25, 25 Nov 2026 - ACQUISITIONS\' SEARCH DOOR. Claude\'s search\\n            # tasks read the scenarios and report listings here, with no\\n            # session - they are machines, not people. The shared key in the\\n            # X-Acq-Key header (ACQ_INTAKE_KEY on Railway) is the credential\\n            # and acquisitions/api.py checks it. Only this one path: every\\n            # screen under acquisitions/ keeps its permission check.\\n            \'acquisitions/api/\',\\n"], ["test_ra19_acquisitions_screens.py", "                scenario_new=\'/acquisitions/scenarios/new/?template=rent\',\\n", "                scenario_new=\'/acquisitions/scenarios/new/\',       # RA25 - no ?template=\\n"], ["test_ra19_acquisitions_screens.py", "NEW = [\'views.py\', \'urls.py\', \'services.py\', \'presets.py\',\\n", "# RA25, 25 Nov 2026 - presets.py (the template cards) is gone: the wizard\\n# builds a new scenario.\\nNEW = [\'views.py\', \'urls.py\', \'services.py\',\\n"], ["test_ra22_rules_wizard.py", "            t = E_.get(\'/acquisitions/scenarios/new/?template=rent\'\\r\\n                       ).content.decode()\\r\\n            ok(\'<option value=\\"rent\\" selected>\' in t and\\r\\n               \'\\"field\\": \\"monthly_rent\\"\' in t and\\r\\n               \'data-wizard-open\' in t,\\r\\n               \'HOME TO RENT opens a new scenario set to Rent, its rules \'\\r\\n               \'ready to change\')\\r\\n", "            # RA25 - no templates: an old ?template=rent link opens an\\r\\n            # empty new scenario in the wizard. Was: set to Rent, its rules\\r\\n            # ready to change.\\r\\n            t = E_.get(\'/acquisitions/scenarios/new/?template=rent\'\\r\\n                       ).content.decode()\\r\\n            ok(\'\\"field\\": \\"monthly_rent\\"\' not in t and\\r\\n               \'data-wizard-open\' in t and \'acqWizard()\' in t,\\r\\n               \'AN OLD TEMPLATE LINK opens an empty new scenario, in the \'\\r\\n               \'wizard\')\\r\\n"], ["test_ra22_rules_wizard.py", "PR = read(J(APP, \'presets.py\'))\\r\\nok(\'\\"rent\\": {\\"title\\": \\"Home to rent\\"\' in PR and \'\\"let\\":\' not in PR and\\r\\n   \'\\"auction\\":\' not in PR,\\r\\n   \'THE TEMPLATES: Home to renovate, Development plot, Home to rent - \'\\r\\n   \'Buy-to-let and Auction & bank-owned gone\')\\r\\n", "# RA25, 25 Nov 2026 - the templates themselves are gone (Demetri: \\"due to\\r\\n# the fact that we have a Wizard, these templates are not needed\\"). Was:\\r\\n# presets.py holds Home to renovate, Development plot and Home to rent.\\r\\nok(not os.path.isfile(J(APP, \'presets.py\')) and\\r\\n   \'Start from a template\' not in read(J(TPL, \'scenarios.html\')),\\r\\n   \'NO TEMPLATES (RA25): Buy-to-let and Auction & bank-owned went in RA22, \'\\r\\n   \'the rest with the wizard\')\\r\\n"], ["test_ra22_rules_wizard.py", "            \\"{% if can_edit and not s.pk and not preset %}\\" in edit,\\r\\n", "            # RA25 - no template to wait for. Was: ... and not preset %}\\r\\n            \\"{% if can_edit and not s.pk %}\\" in edit,\\r\\n"]]')


def refuse(msg):
    raise SystemExit('RA25 REFUSED: %s' % msg)


def load(rel):
    with open(os.path.join(ROOT, rel), 'rb') as f:
        raw = f.read()
    return raw.decode('utf-8-sig'), raw[:3] == b'\xef\xbb\xbf'


def main():
    check = '--check' in sys.argv[1:]
    ps1, _ = load('Push-PendingChanges.ps1')
    if "'test_ra25_search_intake.py'" in ps1:
        print('RA25 already applied.')
        return 0
    if "'test_ra24_acq_flow.py'" not in ps1:
        refuse('RA24 (apply_ra24_acq_flow.py) is not applied - '
               'this round registers after it.')
    for rel in SHIPPED:
        if not os.path.isfile(os.path.join(ROOT, *rel.split('/'))):
            refuse('%s is not in place - it ships with this patcher; copy it '
                   'in first.' % rel)
    # A file's edits are made one after another on the same text, in the
    # order listed; every anchor must be found exactly once when its turn
    # comes, or nothing at all is written.
    texts, order = {}, []
    for rel, old, new in EDITS:
        if rel not in texts:
            texts[rel] = list(load(rel))
            order.append(rel)
        text = texts[rel][0]
        if text.count(old) != 1:
            refuse('%s: the anchor is found %d time(s), not once'
                   % (rel, text.count(old)))
        texts[rel][0] = text.replace(old, new)
    plan = [(rel, texts[rel][0], texts[rel][1]) for rel in order]
    for rel, text, bom in plan:
        if check:
            print('RA25 --check: %s would change' % rel)
            continue
        p = os.path.join(ROOT, rel)
        if not os.path.exists(p + SUFFIX):
            shutil.copy2(p, p + SUFFIX)
        with open(p, 'wb') as f:
            f.write((b'\xef\xbb\xbf' if bom else b'') + text.encode('utf-8'))
        print('  changed %s' % rel)
    for rel in RETIRED:
        p = os.path.join(ROOT, *rel.split('/'))
        if not os.path.isfile(p):
            continue
        if check:
            print('RA25 --check: %s would be moved to %s' % (rel, SUFFIX))
            continue
        if os.path.exists(p + SUFFIX):
            os.remove(p)
        else:
            os.rename(p, p + SUFFIX)
        print('  retired %s (kept as %s)' % (rel, SUFFIX))
    if not check:
        print('RA25 applied - the search reports into the app; no template cards. No migration.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
