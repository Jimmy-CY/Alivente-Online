# Property Acquisitions – step 1 (foundation)

A new Django app for Alivente Online: configurable search **scenarios**, the
**properties** they find, price history, search-run logs and market
snapshots, plus a deterministic **scoring engine**.

This step has no screens yet. You can use everything in the Django admin
straight away. The screens from the mockup come in step 2, and the Claude
connector (API) in step 3.

## What's in the folder

| File | What it does |
|---|---|
| `models.py` | Scenario, Criterion, Property, ListingSource, PriceObservation, ScenarioMatch, Viewing, SearchRun, SiteResult, MarketSnapshot, Area, Website |
| `scoring.py` | The rules engine: Must / Preferred / Scoring, ramps and bands, unknowns, the score cap, Must groups |
| `signals.py` | Re-scores automatically when a property's facts or a scenario's criteria change |
| `admin.py` | Full admin: scenarios with an inline criteria editor, properties with sources, prices and matches |
| `management/commands/seed_acquisitions.py` | Creates your 10 areas, 20 websites and the two scenarios (apartment, plot) |
| `management/commands/import_listings_csv.py` | Imports the old Claude Sheet's Listings tab |
| `tests.py` | 8 tests for the scoring rules |

## Install

1. Copy the `acquisitions` folder into your project, next to your other apps.
2. In `settings.py`, add it to `INSTALLED_APPS`:
   ```python
   "acquisitions.apps.AcquisitionsConfig",
   ```
   Optional: `ACQUISITIONS_VAT_RATE = "0.19"` (that's the default).
3. Create the tables:
   ```
   python manage.py makemigrations acquisitions
   python manage.py migrate
   ```
4. Set up areas, websites and both scenarios:
   ```
   python manage.py seed_acquisitions
   ```
5. Import your current listings. Open the Claude Sheet, go to the Listings tab, and download it as CSV. Then run:
   ```
   python manage.py import_listings_csv listings.csv --scenario apartment-to-renovate-nicosia
   ```
6. Check everything:
   ```
   python manage.py test acquisitions
   ```

On Railway, steps 3–5 run the same way. The commands are safe to run twice.

## How the rules work

- **Facts and scores are kept separately.** A Property holds what the
  listing says, and a ScenarioMatch holds how well it fits one scenario. Edit
  a criterion in the admin and every match is re-scored at once, with no new
  search needed.
- **Unknown is never "no".** A blank fact (None) counts as *unknown*.
  - An unknown Must caps the score (60 by default).
  - More than 3 unknown Musts makes the listing *not addable*.
  - Musts that share a `group` count once. For example, bathrooms + guest WC +
    en-suite count as one, as they did in the sheet.
  - An internal area given only as a total is unknown for the Must, but is
    still used for the "area fit" points.
- **Scoring curves.** A ramp uses `full_from` / `full_to` with `zero_below`
  / `zero_above`, and gives full points inside the window, falling to 0 at
  the zero points. Bands use `score_bands`, for example year built: full
  points from 1995, half for 1985–94.
- **Plain-words rules.** Use field "Plain-words rule" with operator
  "judged". Claude answers it per listing in `ScenarioMatch.judgements`.
- **Your decisions stand.** A status you set (Shortlisted / Rejected) is
  never changed by a search or a re-score. The engine only auto-rejects a
  clear Must failure on listings you haven't decided on.

## Plot scenario

The Musts are the ones you've stated: Engomi or Archangelos, 500–1,000 m²,
≤ €350k and ≤ €500/m². The Preferred and Scoring rows (40 points on € per
buildable m², road frontage, title deed, plot size fit) are my suggested
starting point. Change them in the admin.

## Hooking into your permissions

Register the module in your 12-module `can_access` / `can_edit` setup the
same way as the others. The views in step 2 will use your existing
decorators.
