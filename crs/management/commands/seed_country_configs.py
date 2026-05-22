"""
Django management command: seed 29 CRS country configurations.

Place this file at:
    crs/management/commands/seed_country_configs.py

You will also need (one-time setup, if the directories don't already exist):
    crs/management/__init__.py             (empty file)
    crs/management/commands/__init__.py    (empty file)

Then run:
    python manage.py seed_country_configs

The command is idempotent — uses update_or_create, so re-running updates
existing rows in place rather than creating duplicates.

All configurations seed with receiving_country_strategy='split_by_residence'
per the operational decision. Cyprus is NOT included — assumed already
configured.

Doc-ref-id and message-ref-id templates are translated from the source
vendor's token vocabulary to this system's tokens:
    [SENDING_COUNTRY_CD]                  → [TRANSMITTING_COUNTRY]
    [SENDING_FI_IN], [REPORTING_FI_IN],
    [SENDER_IN], [SENDING_IN]             → [SENDING_FI_IN]
    [YEAR], [REPORTING_YEAR], [YYYY],
    [ANNO RIFERIMENTO]                    → [YEAR]
    [RECEIVING_COUNTRY],
    [RECEIVING_COUNTRY_CD]                → [RECEIVING_COUNTRY]
Vendor-specific sequence/identifier tokens (e.g. [PROGRESSIVO RECORD],
[RUNNING_NUMBER_REPORT], [MELDESTELLENNUMMER]) are mapped to [UUID]
or [SENDING_FI_IN] as closest equivalents — adjust per-country in admin
afterwards if a particular tax authority needs a specific format.

If your CountryConfiguration model uses different field names than the
ones below, adjust the FIELD_MAP at the top of handle().
"""
from django.core.management.base import BaseCommand
from crs.models import CountryConfiguration


COUNTRY_CONFIGS = [
    dict(country_code="AT", country_name="Austria", default_currency="EUR",
         tin_regex=r"[0-9]{9}",
         max_file_size_mb=-1, max_accounts_per_file=4000,
         fi_doc_ref_id_template="AT_[YEAR]_[SENDING_FI_IN]_[UUID]_[RECEIVING_COUNTRY]",
         account_doc_ref_id_template="AT_[YEAR]_[SENDING_FI_IN]_[UUID]_[RECEIVING_COUNTRY]",
         message_ref_id_template="[SENDING_FI_IN][TRANSMITTING_COUNTRY][YEAR][UUID]"),

    dict(country_code="BM", country_name="Bermuda", default_currency="USD",
         tin_regex=r"[a-zA-Z0-9]*",
         max_file_size_mb=-1, max_accounts_per_file=-1,
         fi_doc_ref_id_template="BM[UUID]",
         account_doc_ref_id_template="BM[UUID]",
         message_ref_id_template="[TRANSMITTING_COUNTRY][YEAR][RECEIVING_COUNTRY][UUID]"),

    dict(country_code="VG", country_name="British Virgin Islands", default_currency="USD",
         tin_regex=r"[a-zA-Z0-9]*",
         max_file_size_mb=-1, max_accounts_per_file=-1,
         fi_doc_ref_id_template="[TRANSMITTING_COUNTRY][SENDING_FI_IN][UUID]",
         account_doc_ref_id_template="[TRANSMITTING_COUNTRY][SENDING_FI_IN][UUID]",
         message_ref_id_template="[TRANSMITTING_COUNTRY][YEAR][RECEIVING_COUNTRY][UUID]"),

    dict(country_code="CA", country_name="Canada", default_currency="CAD",
         tin_regex=r"[a-zA-Z0-9]*",
         max_file_size_mb=150, max_accounts_per_file=-1,
         fi_doc_ref_id_template="CA-[YEAR]-[SENDING_FI_IN]-FI-[UUID]",
         account_doc_ref_id_template="CA-[YEAR]-[SENDING_FI_IN]-SL-[UUID]",
         message_ref_id_template="[TRANSMITTING_COUNTRY][YEAR][RECEIVING_COUNTRY][UUID]"),

    dict(country_code="KY", country_name="Cayman Islands", default_currency="USD",
         tin_regex=r"[a-zA-Z0-9]*",
         max_file_size_mb=-1, max_accounts_per_file=-1,
         fi_doc_ref_id_template="KY[YEAR][RECEIVING_COUNTRY][SENDING_FI_IN][UUID]",
         account_doc_ref_id_template="[TRANSMITTING_COUNTRY][UUID]",
         message_ref_id_template="[SENDING_FI_IN][UUID]"),

    dict(country_code="CL", country_name="Chile", default_currency="USD",
         tin_regex=r"[a-zA-Z0-9]*",
         max_file_size_mb=-1, max_accounts_per_file=-1,
         fi_doc_ref_id_template="CL[YEAR]CLF[SENDING_FI_IN]-[UUID]",
         account_doc_ref_id_template="CL[YEAR]CLA[SENDING_FI_IN]-[UUID]",
         message_ref_id_template="CL[YEAR]CLM[SENDING_FI_IN]-[UUID]"),

    dict(country_code="CN", country_name="China", default_currency="CNY",
         tin_regex=r"[a-zA-Z0-9]*",
         max_file_size_mb=-1, max_accounts_per_file=-1,
         fi_doc_ref_id_template="CN[YEAR][SENDING_FI_IN][UUID]",
         account_doc_ref_id_template="CN[YEAR][SENDING_FI_IN][UUID]",
         message_ref_id_template="[TRANSMITTING_COUNTRY][YEAR][RECEIVING_COUNTRY][UUID]"),

    dict(country_code="CK", country_name="Cook Islands", default_currency="NZD",
         # FATCA_GIIN format: 6 alphanum.5 alphanum.2 alpha.3 digit
         tin_regex=r"[A-Z0-9]{6}\.[A-Z0-9]{5}\.[A-Z]{2}\.[0-9]{3}",
         max_file_size_mb=-1, max_accounts_per_file=-1,
         fi_doc_ref_id_template="[TRANSMITTING_COUNTRY][SENDING_FI_IN][UUID]",
         account_doc_ref_id_template="[TRANSMITTING_COUNTRY][SENDING_FI_IN][UUID]",
         message_ref_id_template="[TRANSMITTING_COUNTRY][YEAR][RECEIVING_COUNTRY][UUID]"),

    dict(country_code="CR", country_name="Costa Rica", default_currency="CRC",
         tin_regex=r"[a-zA-Z0-9]*",
         max_file_size_mb=-1, max_accounts_per_file=-1,
         fi_doc_ref_id_template="CR[YEAR][RECEIVING_COUNTRY][SENDING_FI_IN].[UUID].[UUID]",
         account_doc_ref_id_template="CR[YEAR][RECEIVING_COUNTRY][SENDING_FI_IN].[UUID].[UUID]",
         message_ref_id_template="CR[YEAR][RECEIVING_COUNTRY][SENDING_FI_IN].[UUID]"),

    dict(country_code="FI", country_name="Finland", default_currency="EUR",
         tin_regex=r"[0-9]{7}-[0-9]{1}",
         max_file_size_mb=-1, max_accounts_per_file=-1,
         fi_doc_ref_id_template="[SENDING_FI_IN].[UUID]-[UUID]",
         account_doc_ref_id_template="[SENDING_FI_IN].[UUID]-[UUID]",
         message_ref_id_template="[SENDING_FI_IN]-[YEAR]-[UUID]"),

    dict(country_code="FR", country_name="France", default_currency="EUR",
         tin_regex=r"[0-3][0-9]{12}",
         max_file_size_mb=-1, max_accounts_per_file=-1,
         fi_doc_ref_id_template="IF_[YEAR]_[SENDING_FI_IN]_[UUID]",
         account_doc_ref_id_template="IF_[YEAR]_[SENDING_FI_IN]_[UUID]",
         message_ref_id_template="IF_[YEAR]_[SENDING_FI_IN]_[UUID]"),

    dict(country_code="DE", country_name="Germany", default_currency="EUR",
         tin_regex=r"[a-zA-Z0-9/]*",
         max_file_size_mb=20, max_accounts_per_file=4000,
         fi_doc_ref_id_template="DE[YEAR][SENDING_FI_IN]FI[UUID]",
         account_doc_ref_id_template="DE[YEAR][SENDING_FI_IN]AR[UUID]",
         message_ref_id_template="DE[YEAR]DE[UUID]"),

    dict(country_code="GG", country_name="Guernsey", default_currency="GBP",
         tin_regex=r"[A-Z0-9]{6}\.[A-Z0-9]{5}\.[A-Z]{2}\.[0-9]{3}",
         max_file_size_mb=-1, max_accounts_per_file=-1,
         fi_doc_ref_id_template="[TRANSMITTING_COUNTRY][SENDING_FI_IN][UUID]",
         account_doc_ref_id_template="[TRANSMITTING_COUNTRY][SENDING_FI_IN][UUID]",
         message_ref_id_template="[TRANSMITTING_COUNTRY][YEAR][RECEIVING_COUNTRY][UUID]"),

    dict(country_code="IE", country_name="Ireland", default_currency="GBP",
         tin_regex=r"[a-zA-Z0-9]*",
         max_file_size_mb=-1, max_accounts_per_file=-1,
         fi_doc_ref_id_template="[YEAR][SENDING_FI_IN]FI[UUID]",
         account_doc_ref_id_template="[YEAR][SENDING_FI_IN]AR[UUID]",
         message_ref_id_template="[YEAR][SENDING_FI_IN]MS[UUID]"),

    dict(country_code="IM", country_name="Isle of Man", default_currency="EUR",
         tin_regex=r"[a-zA-Z0-9]*",
         max_file_size_mb=-1, max_accounts_per_file=-1,
         fi_doc_ref_id_template="[SENDING_FI_IN].[UUID]",
         account_doc_ref_id_template="[SENDING_FI_IN].[UUID]",
         message_ref_id_template="[TRANSMITTING_COUNTRY][YEAR][RECEIVING_COUNTRY][UUID]"),

    dict(country_code="IL", country_name="Israel", default_currency="ILS",
         tin_regex=r"[0-9]{9}",
         max_file_size_mb=-1, max_accounts_per_file=-1,
         fi_doc_ref_id_template="IL[YEAR][RECEIVING_COUNTRY].[SENDING_FI_IN].[UUID].CRS.[UUID]",
         account_doc_ref_id_template="IL[YEAR][RECEIVING_COUNTRY].[SENDING_FI_IN].[UUID].CRS.[UUID]",
         message_ref_id_template="IL[YEAR].[SENDING_FI_IN].[UUID].CRS"),

    dict(country_code="IT", country_name="Italy", default_currency="EUR",
         tin_regex=r"[0-9]{11}",
         max_file_size_mb=-1, max_accounts_per_file=-1,
         fi_doc_ref_id_template="IT[YEAR][SENDING_FI_IN]FI[UUID]",
         account_doc_ref_id_template="IT[YEAR][SENDING_FI_IN]AR[UUID]",
         message_ref_id_template="IT[YEAR][SENDING_FI_IN][UUID]"),

    dict(country_code="JP", country_name="Japan", default_currency="JPY",
         tin_regex=r"[a-zA-Z0-9]*",
         max_file_size_mb=-1, max_accounts_per_file=-1,
         fi_doc_ref_id_template="[TRANSMITTING_COUNTRY][SENDING_FI_IN][UUID]",
         account_doc_ref_id_template="[TRANSMITTING_COUNTRY][SENDING_FI_IN][UUID]",
         message_ref_id_template="[TRANSMITTING_COUNTRY][YEAR][RECEIVING_COUNTRY][UUID]"),

    dict(country_code="JE", country_name="Jersey", default_currency="GBP",
         tin_regex=r"[a-zA-Z0-9]*",
         max_file_size_mb=-1, max_accounts_per_file=-1,
         fi_doc_ref_id_template="[TRANSMITTING_COUNTRY][YEAR][RECEIVING_COUNTRY][UUID]",
         account_doc_ref_id_template="[TRANSMITTING_COUNTRY][YEAR][RECEIVING_COUNTRY][UUID]",
         message_ref_id_template="[TRANSMITTING_COUNTRY][YEAR][RECEIVING_COUNTRY][UUID]"),

    dict(country_code="LI", country_name="Liechtenstein", default_currency="CHF",
         tin_regex=r"[0-9]{7}",
         max_file_size_mb=-1, max_accounts_per_file=-1,
         fi_doc_ref_id_template="LI[YEAR][RECEIVING_COUNTRY].[SENDING_FI_IN].[UUID]",
         account_doc_ref_id_template="LI[YEAR][RECEIVING_COUNTRY].[SENDING_FI_IN].[UUID]",
         message_ref_id_template="LI[YEAR][RECEIVING_COUNTRY].[SENDING_FI_IN].[UUID]"),

    dict(country_code="LU", country_name="Luxembourg", default_currency="EUR",
         tin_regex=r"[a-zA-Z0-9]*",
         max_file_size_mb=-1, max_accounts_per_file=-1,
         fi_doc_ref_id_template="LU[YEAR][RECEIVING_COUNTRY]_AR_[SENDING_FI_IN]_[UUID]",
         account_doc_ref_id_template="LU[YEAR][RECEIVING_COUNTRY]_AR_[SENDING_FI_IN]_[UUID]",
         message_ref_id_template="LU[YEAR]LU_HC_[SENDING_FI_IN]_[UUID]"),

    dict(country_code="MY", country_name="Malaysia", default_currency="MYR",
         tin_regex=r"[0-9]{8}",
         max_file_size_mb=-1, max_accounts_per_file=-1,
         fi_doc_ref_id_template="MY[SENDING_FI_IN][YEAR]F[UUID]",
         account_doc_ref_id_template="MY[SENDING_FI_IN][YEAR]A[UUID]",
         message_ref_id_template="MY[SENDING_FI_IN][YEAR][UUID]"),

    dict(country_code="MT", country_name="Malta", default_currency="EUR",
         tin_regex=r"[a-zA-Z0-9]*",
         max_file_size_mb=-1, max_accounts_per_file=-1,
         fi_doc_ref_id_template="MT[YEAR][SENDING_FI_IN]FI[UUID][RECEIVING_COUNTRY]",
         account_doc_ref_id_template="MT[YEAR][SENDING_FI_IN]AR[UUID][RECEIVING_COUNTRY]",
         message_ref_id_template="MT[YEAR][RECEIVING_COUNTRY][SENDING_FI_IN][UUID]"),

    # Mauritius — source screenshot had blank Default Currency and Default
    # Country Code. Using MU / MUR (Mauritian rupee) as conventional defaults.
    dict(country_code="MU", country_name="Mauritius", default_currency="MUR",
         tin_regex=r"[a-zA-Z0-9]*",
         max_file_size_mb=-1, max_accounts_per_file=-1,
         fi_doc_ref_id_template="[TRANSMITTING_COUNTRY][YEAR][RECEIVING_COUNTRY][UUID]",
         account_doc_ref_id_template="[TRANSMITTING_COUNTRY][YEAR][RECEIVING_COUNTRY][UUID]",
         message_ref_id_template="[TRANSMITTING_COUNTRY][YEAR][RECEIVING_COUNTRY][UUID]"),

    dict(country_code="SM", country_name="San Marino", default_currency="EUR",
         tin_regex=r"[a-zA-Z0-9]*",
         max_file_size_mb=-1, max_accounts_per_file=-1,
         fi_doc_ref_id_template="SM_[YEAR]_[SENDING_FI_IN]_FI_[UUID]_SM",
         account_doc_ref_id_template="SM_[YEAR]_[SENDING_FI_IN]_AR_[UUID]_SM",
         message_ref_id_template="SM_[YEAR]_[CURRENT_DATE]_[SENDING_FI_IN]"),

    dict(country_code="SC", country_name="Seychelles", default_currency="SCR",
         tin_regex=r"[a-zA-Z0-9]*",
         max_file_size_mb=-1, max_accounts_per_file=-1,
         fi_doc_ref_id_template="[TRANSMITTING_COUNTRY][YEAR][RECEIVING_COUNTRY][UUID]",
         account_doc_ref_id_template="[TRANSMITTING_COUNTRY][YEAR][RECEIVING_COUNTRY][UUID]",
         message_ref_id_template="[TRANSMITTING_COUNTRY][YEAR][RECEIVING_COUNTRY][UUID]",
         # Seychelles uses a custom filename pattern with RC already embedded:
         output_filename_template="SC_[SENDING_FI_IN]_[UUID]_[RECEIVING_COUNTRY].xml"),

    dict(country_code="CH", country_name="Switzerland", default_currency="CHF",
         tin_regex=r"[0-9]{3}\.[0-9]{4}\.[0-9]{4}",
         max_file_size_mb=-1, max_accounts_per_file=-1,
         fi_doc_ref_id_template="CH[YEAR]CH[UUID]",
         account_doc_ref_id_template="CH[YEAR]CH[UUID]",
         message_ref_id_template="CH[YEAR]CH[UUID]"),

    dict(country_code="UY", country_name="Uruguay", default_currency="UYU",
         tin_regex=r"[a-zA-Z0-9]*",
         max_file_size_mb=-1, max_accounts_per_file=-1,
         fi_doc_ref_id_template="UY.[SENDING_FI_IN].[UUID]",
         account_doc_ref_id_template="UY.[SENDING_FI_IN].[UUID]",
         message_ref_id_template="UY[YEAR][RECEIVING_COUNTRY].[SENDING_FI_IN].[UUID]"),

    dict(country_code="VU", country_name="Vanuatu", default_currency="USD",
         tin_regex=r"[a-zA-Z0-9]*",
         max_file_size_mb=-1, max_accounts_per_file=-1,
         fi_doc_ref_id_template="VU[YEAR][SENDING_FI_IN][UUID]",
         account_doc_ref_id_template="VU[YEAR][SENDING_FI_IN][UUID]",
         message_ref_id_template="VU[YEAR][SENDING_FI_IN][UUID]"),
]


class Command(BaseCommand):
    help = "Seed 29 CountryConfiguration rows in split-by-residence mode."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be created/updated without writing to DB.",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]

        # Defaults applied to every row, can be overridden per-country in
        # the COUNTRY_CONFIGS dict if any country needs something different.
        common_defaults = {
            "oecd_version":                  "2.0",
            "receiving_country_strategy":    "split_by_residence",
            "output_filename_template":      "[SENDING_FI_IN]_[CURRENT_DATE].xml",
        }

        created_count = 0
        updated_count = 0

        valid_fields = {
            f.name for f in CountryConfiguration._meta.get_fields()
            if hasattr(f, "attname")  # filters out reverse relations
        }

        for cfg in COUNTRY_CONFIGS:
            country_code = cfg["country_code"]
            defaults = {**common_defaults, **cfg}
            defaults.pop("country_code", None)
            # Silently drop any keys not in the model schema (e.g. vendor-specific
            # fields like max_file_size_mb that this system doesn't model).
            defaults = {k: v for k, v in defaults.items() if k in valid_fields}

            if dry_run:
                exists = CountryConfiguration.objects.filter(country_code=country_code).exists()
                action = "UPDATE" if exists else "CREATE"
                self.stdout.write(f"  [{action}] {country_code} — {cfg['country_name']}")
                continue

            obj, created = CountryConfiguration.objects.update_or_create(
                country_code=country_code,
                defaults=defaults,
            )
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(
                    f"  CREATED  {country_code} — {cfg['country_name']}"
                ))
            else:
                updated_count += 1
                self.stdout.write(
                    f"  updated  {country_code} — {cfg['country_name']}"
                )

        if dry_run:
            self.stdout.write(self.style.WARNING(
                f"\nDry run — {len(COUNTRY_CONFIGS)} configurations would be processed."
            ))
        else:
            self.stdout.write(self.style.SUCCESS(
                f"\nDone. {created_count} created, {updated_count} updated."
            ))