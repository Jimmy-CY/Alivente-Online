"""
crs.services.xml_builder — Build OECD CRS XML v2.0 from a Submission + ParseResult.

Public surface:
    enumerate_reports(parse_result, fi_residence_country, strategy)
        Returns dict[str, list[_BuildSlice]] — determines which receiving-country
        files to build and which scoped account slices go into each. Pure
        function; no Django dependencies.

    build_all(submission, parse_result) -> dict[str, bytes]
        Top-level entry point. Returns {receiving_country: xml_bytes} —
        exactly one entry for combined_domestic, N entries for
        split_by_residence (or 0 if no reportable accounts).

Per-account fan-out rules (per OECD CRS spec + the in-house compliance brief):
    Individual          → if holder residence reportable, one slice → that RC
    CRS102 organisation → if entity residence reportable, one entity-only slice
                          → that RC (no CPs)
    CRS101 organisation → one slice per reportable CP residence (entity as
                          structural anchor, only CPs matching that RC included).
                          Entity itself NEVER produces a file under CRS101.
    CRS103 organisation → COMBINED CRS103+CRS101 case:
        * if entity residence reportable → entity-only slice
          (AcctHolderType=CRS103, no CPs)
        * PLUS one CP slice per reportable CP residence
          (AcctHolderType=CRS101, anchor + only that RC's CPs)
      So a CRS103 entity in GB with CPs in DE and AT fans out into 3 slices
      (GB entity-only, DE+George, AT+Pete) before the mode-based aggregation.

Reportability rule (uniform across both modes):
    US residents              → never reportable (FATCA, not CRS)
    Domestic (FI's residence) → never reportable (handled outside CRS)
    All other residences      → reportable
    No OECD jurisdictions list is maintained — relies on the user to enter
    sensible tax_residence values at parser stage. Over-inclusion (generating
    a file for a non-CRS jurisdiction) is acceptable; under-inclusion is not.

Mode interaction:
    combined_domestic — fan-out happens identically, but all resulting slices
        collapse to a single key = fi_residence. The output file's
        ReceivingCountry equals TransmittingCountry equals fi_residence.
    split_by_residence — fan-out slices land in different keys based on their
        actual RC. One output file per distinct RC.

Element ordering, child counts, and namespace placement follow the OECD CRS
XML Schema v2.0 (CrsXML_v2.0.xsd + imports). Changes here should be
cross-checked against the schema before landing.

Namespaces (all four schemas use elementFormDefault="qualified"):
    crs (prefixed): urn:oecd:ties:crs:v2 — most elements
    cfc:            urn:oecd:ties:commontypesfatcacrs:v2 — Address children only
    stf:            urn:oecd:ties:crsstf:v5 — DocSpec children only
    ftc:            urn:oecd:ties:fatca:v1 — declared defensively
    xsi:            schemaLocation carrier

Format conventions:
    - Prefixed namespace style throughout (matches Cyprus tax-portal reference)
    - Root carries xsi:schemaLocation
    - AccountNumber status attrs always emitted true/false (never omitted)
    - Monetary amounts always 2 fraction digits (5000.00, not 5000)
    - <Individual> Name carries nameType="OECD202"

Enum mappings (parser/model values → XML schema codes):
    AcctHolderType, MessageTypeIndic, DocTypeIndic, CtrlgPersonType, MessageType
        already match the schema directly — no translation.
    Name nameType:            legal→OECD207, dba→OECD206, alias→OECD203, aka→OECD205
    Address legalAddressType: residentialOrBusiness→OECD301, residential→OECD302,
                              business→OECD303, registeredOffice→OECD304,
                              unspecified→OECD305
    AccountNumber AcctNumberType:
                              IBAN→OECD601, OBAN→OECD602, ISIN→OECD603,
                              OSIN→OECD604, Other→OECD605
    Payment Type:             Dividend→CRS501, Interest→CRS502,
                              GrossProceeds→CRS503, Other→CRS504
"""
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal

from lxml import etree

from crs.services.tokens import resolve_strict


# ---------------------------------------------------------------------------
# Namespaces
# ---------------------------------------------------------------------------
NS_CRS = "urn:oecd:ties:crs:v2"
NS_CFC = "urn:oecd:ties:commontypesfatcacrs:v2"
NS_STF = "urn:oecd:ties:crsstf:v5"
NS_ISO = "urn:oecd:ties:isocrstypes:v1"
NS_FTC = "urn:oecd:ties:fatca:v1"
NS_XSI = "http://www.w3.org/2001/XMLSchema-instance"

NSMAP = {
    "ftc": NS_FTC,
    "stf": NS_STF,
    "cfc": NS_CFC,
    "crs": NS_CRS,
    "xsi": NS_XSI,
}

SCHEMA_LOCATION = "urn:oecd:ties:crs:v2 CrsXML_v2.0.xsd"

_CRS = "{%s}" % NS_CRS
_CFC = "{%s}" % NS_CFC
_STF = "{%s}" % NS_STF
_XSI = "{%s}" % NS_XSI


# ---------------------------------------------------------------------------
# Enum maps
# ---------------------------------------------------------------------------
_NAMETYPE_MAP = {
    "legal": "OECD207",
    "dba":   "OECD206",
    "alias": "OECD203",
    "aka":   "OECD205",
}

_ADDRTYPE_MAP = {
    "residentialOrBusiness": "OECD301",
    "residential":           "OECD302",
    "business":              "OECD303",
    "registeredOffice":      "OECD304",
    "unspecified":           "OECD305",
}

_ACCTNUM_TYPE_MAP = {
    "IBAN":  "OECD601",
    "OBAN":  "OECD602",
    "ISIN":  "OECD603",
    "OSIN":  "OECD604",
    "Other": "OECD605",
}

_PAYMENT_TYPE_MAP = {
    "Dividend":      "CRS501",
    "Interest":      "CRS502",
    "GrossProceeds": "CRS503",
    "Other":         "CRS504",
}


# ---------------------------------------------------------------------------
# Slice dataclass — what enumerate_reports produces; what the builder consumes
# ---------------------------------------------------------------------------
@dataclass
class _BuildSlice:
    """One scoped slice of an account, destined for exactly one XML file.

    The slice carries the original account (for everything OTHER than CPs)
    plus an explicit list of which CPs to include and which AcctHolderType
    to emit. This lets us handle the CRS103 fan-out where a single
    ParsedAccount produces multiple slices with different scopes and
    different reported holder types.

    For Individual slices, cps_to_include and holder_type_override are unused
    (the builder takes the Individual code path which knows neither concept).
    """
    account: object                       # parser.ParsedAccount
    cps_to_include: list = field(default_factory=list)
    holder_type_override: str = ""        # CRS101 / CRS102 / CRS103 / "" for Individual


# ---------------------------------------------------------------------------
# Reportability — the policy gate at the heart of fan-out
# ---------------------------------------------------------------------------
def _is_reportable(person_residence_country, fi_residence_country):
    """Per current policy:
        - blank residence → not reportable (no destination)
        - USA            → not reportable (FATCA covers US persons)
        - domestic       → not reportable (handled outside CRS)
        - everything else → reportable
    No OECD list lookup — relies on parser-validated residence codes."""
    if not person_residence_country:
        return False
    if person_residence_country == "US":
        return False
    if person_residence_country == fi_residence_country:
        return False
    return True


# ---------------------------------------------------------------------------
# Slice enumeration — pure function, no Django/IO
# ---------------------------------------------------------------------------
def enumerate_reports(parse_result, fi_residence_country, strategy):
    """Build the per-receiving-country slice map for a parse result.

    Returns dict[str, list[_BuildSlice]] keyed by receiving-country code.
    Empty dict if no accounts are reportable (e.g. workbook contains only
    US and domestic holders).

    strategy must be one of 'combined_domestic' or 'split_by_residence'.
    """
    if strategy not in ("combined_domestic", "split_by_residence"):
        raise ValueError(
            f"Unknown receiving_country_strategy: {strategy!r}. "
            f"Expected 'combined_domestic' or 'split_by_residence'."
        )

    reports = defaultdict(list)

    def emit(actual_rc, slice_):
        """Place a slice in the appropriate output bucket per the strategy.
        combined_domestic collapses all slices to the FI's residence;
        split_by_residence keeps them keyed by their actual RC."""
        key = fi_residence_country if strategy == "combined_domestic" else actual_rc
        reports[key].append(slice_)

    for acct in parse_result.accounts:
        if acct.sheet == "Individual":
            if _is_reportable(acct.tax_residence, fi_residence_country):
                emit(acct.tax_residence, _BuildSlice(account=acct))

        elif acct.sheet == "Organisation":
            holder_type = acct.holder_type

            if holder_type == "CRS102":
                # Entity is the reportable person; no CPs in the report.
                if _is_reportable(acct.tax_residence, fi_residence_country):
                    emit(acct.tax_residence, _BuildSlice(
                        account=acct,
                        cps_to_include=[],
                        holder_type_override="CRS102",
                    ))

            elif holder_type == "CRS101":
                # Entity is a Passive NFE, not itself reportable. CPs ARE.
                # One slice per reportable CP residence, grouping CPs by RC
                # so multiple CPs from the same country share a slice.
                cps_by_rc = defaultdict(list)
                for cp in acct.controlling_persons:
                    if _is_reportable(cp.tax_residence, fi_residence_country):
                        cps_by_rc[cp.tax_residence].append(cp)
                for rc, cps in cps_by_rc.items():
                    emit(rc, _BuildSlice(
                        account=acct,
                        cps_to_include=cps,
                        holder_type_override="CRS101",
                    ))

            elif holder_type == "CRS103":
                # Combined CRS103+CRS101 fan-out: the same account can
                # produce up to (1 + N) slices — one CRS103 entity-only
                # slice if the entity is reportable, plus one CRS101 slice
                # per reportable CP residence.
                if _is_reportable(acct.tax_residence, fi_residence_country):
                    emit(acct.tax_residence, _BuildSlice(
                        account=acct,
                        cps_to_include=[],
                        holder_type_override="CRS103",
                    ))
                cps_by_rc = defaultdict(list)
                for cp in acct.controlling_persons:
                    if _is_reportable(cp.tax_residence, fi_residence_country):
                        cps_by_rc[cp.tax_residence].append(cp)
                for rc, cps in cps_by_rc.items():
                    emit(rc, _BuildSlice(
                        account=acct,
                        cps_to_include=cps,
                        holder_type_override="CRS101",
                    ))
            # Unknown holder_type: ignore. Parser-level validation already
            # caught these as invalid, so we shouldn't see them here.

    # In combined_domestic mode, every emit() above collapsed its slice into
    # one bucket keyed on fi_residence_country. That can leave multiple slices
    # in the bucket for the same (account, AcctHolderType) — one per CP
    # residence — because the per-RC grouping above was done before the
    # collapse. Merge them now so the file shows ONE AccountReport per
    # reportable role per account, with all reportable CPs grouped together.
    # This matches conventional combined-domestic layout and avoids
    # duplicate-looking AccountReports with the same AccountNumber.
    # Split mode keeps per-RC granularity because each slice lands in its
    # own bucket — no merge needed.
    if strategy == "combined_domestic":
        for rc in reports:
            merged = {}
            for slice_ in reports[rc]:
                key = (id(slice_.account), slice_.holder_type_override)
                if key in merged:
                    merged[key].cps_to_include.extend(slice_.cps_to_include)
                else:
                    merged[key] = _BuildSlice(
                        account=slice_.account,
                        cps_to_include=list(slice_.cps_to_include),
                        holder_type_override=slice_.holder_type_override,
                    )
            reports[rc] = list(merged.values())

    return dict(reports)


# ---------------------------------------------------------------------------
# Public top-level: build all files for a submission
# ---------------------------------------------------------------------------
def build_all(submission, parse_result):
    """Build all per-RC XML files for a submission.

    Returns dict[str, bytes] keyed by receiving-country code. Empty dict if
    the parse result yields no reportable accounts (caller should treat that
    as an error condition and surface to the user).

    Raises ValueError if parse_result is not valid — caller must check
    parse_result.is_valid before calling.
    """
    if not parse_result.is_valid:
        raise ValueError(
            f"Cannot build XML — ParseResult has {len(parse_result.errors)} "
            f"unresolved errors. Fix and re-parse first."
        )

    fi_residence = submission.reporting_fi.res_country_code
    strategy     = submission.country_config.receiving_country_strategy
    slices_by_rc = enumerate_reports(parse_result, fi_residence, strategy)

    return {
        rc: _build_xml_doc(submission, slices, rc)
        for rc, slices in slices_by_rc.items()
    }

def build_nil(submission):
    """Build a single OECD CRS703 nil return for a submission.

    A nil return declares the FI has done its due-diligence checks and has no
    reportable accounts. Per the OECD CRS XML User Guide: MessageTypeIndic =
    CRS703, a present CrsBody + ReportingFI, and an empty ReportingGroup (no
    AccountReport). Always one file, addressed to the FI's own residence
    (ReceivingCountry == TransmittingCountry == FI residence). No parse_result
    — there is nothing to ingest.

    Returns {fi_residence: xml_bytes}, mirroring build_all's shape so the view
    can treat both paths uniformly.
    """
    fi_residence = submission.reporting_fi.res_country_code
    xml = _build_xml_doc(
        submission, [], fi_residence,
        message_type_indic_override="CRS703",
        append_rc_suffix=False,
    )
    return {fi_residence: xml}


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------
def _ce(parent, qname, text):
    """SubElement + text shortcut. qname must already be Clark-notation."""
    e = etree.SubElement(parent, qname)
    if text is not None:
        e.text = str(text)
    return e


def _format_amount(amount):
    """Monetary values rendered with exactly 2 fraction digits."""
    if amount is None:
        return ""
    if not isinstance(amount, Decimal):
        amount = Decimal(str(amount))
    return format(amount.quantize(Decimal("0.01")), "f")


# ---------------------------------------------------------------------------
# Internal: build one XML file from a list of slices
# ---------------------------------------------------------------------------
def _build_xml_doc(submission, slices, receiving_country,
                   message_type_indic_override=None, append_rc_suffix=True):
    """Build a single CRS XML file containing the supplied slices.
    receiving_country is what goes in MessageSpec; TC always = FI residence.
    message_type_indic_override forces MessageTypeIndic — nil returns pass
    CRS703 regardless of submission.message_type."""
    now = datetime.now(timezone.utc)

    root = etree.Element(_CRS + "CRS_OECD", nsmap=NSMAP)
    root.set(_XSI + "schemaLocation", SCHEMA_LOCATION)
    root.set("version", str(submission.country_config.oecd_version))

    _build_message_spec(root, submission, receiving_country, now,
                        message_type_indic_override=message_type_indic_override,
                        append_rc_suffix=append_rc_suffix)
    _build_crs_body(root, submission, slices)

    return etree.tostring(
        root, pretty_print=True, xml_declaration=True, encoding="UTF-8"
    )


# ---------------------------------------------------------------------------
# MessageSpec — RC now comes from the per-file context, not submission directly
# ---------------------------------------------------------------------------
def _build_message_spec(parent, submission, receiving_country, now,
                        message_type_indic_override=None, append_rc_suffix=True):
    spec = etree.SubElement(parent, _CRS + "MessageSpec")

    _ce(spec, _CRS + "SendingCompanyIN",    submission.sending_company_in)
    _ce(spec, _CRS + "TransmittingCountry", submission.transmitting_country)
    _ce(spec, _CRS + "ReceivingCountry",    receiving_country)
    _ce(spec, _CRS + "MessageType",         "CRS")

    if submission.warning:
        _ce(spec, _CRS + "Warning", submission.warning)

    if submission.reporting_fi.contact:
        _ce(spec, _CRS + "Contact", submission.reporting_fi.contact)

    # MessageRefId per OECD spec must be unique in time AND space. For split
    # files the same base submission produces N files, so we append the RC
    # to disambiguate. A nil return is a single file with no disambiguation
    # need, and the accepted Cyprus format carries no suffix — so the nil
    # path passes append_rc_suffix=False and emits the bare minted id.
    if append_rc_suffix:
        ref_id = f"{submission.message_ref_id}_{receiving_country}"
    else:
        ref_id = submission.message_ref_id
    _ce(spec, _CRS + "MessageRefId", ref_id)

    indic = message_type_indic_override or submission.message_type
    _ce(spec, _CRS + "MessageTypeIndic", indic)

    if submission.corr_message_ref_id:
        _ce(spec, _CRS + "CorrMessageRefId", submission.corr_message_ref_id)

    _ce(spec, _CRS + "ReportingPeriod",
        submission.reporting_period.strftime("%Y-%m-%d"))
    _ce(spec, _CRS + "Timestamp",
        now.strftime("%Y-%m-%dT%H:%M:%S"))


# ---------------------------------------------------------------------------
# CrsBody — now iterates slices
# ---------------------------------------------------------------------------
def _build_crs_body(parent, submission, slices):
    body = etree.SubElement(parent, _CRS + "CrsBody")

    _build_reporting_fi(body, submission)

    group = etree.SubElement(body, _CRS + "ReportingGroup")
    for slice_ in slices:
        _build_account_report(group, slice_, submission)


def _build_reporting_fi(parent, submission):
    fi = submission.reporting_fi
    cc = submission.country_config

    fi_elem = etree.SubElement(parent, _CRS + "ReportingFI")

    _ce(fi_elem, _CRS + "ResCountryCode", fi.res_country_code)

    for fin in fi.ins.all():
        in_elem = _ce(fi_elem, _CRS + "IN", fin.in_value)
        if fin.issued_by:
            in_elem.set("issuedBy", fin.issued_by)
        if fin.in_type:
            in_elem.set("INType", fin.in_type)

    name = _ce(fi_elem, _CRS + "Name", fi.name)
    if fi.name_type in _NAMETYPE_MAP:
        name.set("nameType", _NAMETYPE_MAP[fi.name_type])

    _build_address(fi_elem, fi.address_country_code, fi.address_free, fi.address_type)

    fi_doc_ref = resolve_strict(
        cc.fi_doc_ref_id_template,
        {"SENDING_FI_IN": submission.sending_company_in, "YEAR": submission.year},
    )
    _build_doc_spec(fi_elem, submission.document_type, fi_doc_ref)


def _build_account_report(parent, slice_, submission):
    """Build one AccountReport from a slice. Slice carries the original
    account for everything OTHER than CPs and AcctHolderType, both of which
    come from the slice's per-file scope."""
    acct = slice_.account
    cc   = submission.country_config

    report = etree.SubElement(parent, _CRS + "AccountReport")

    acct_doc_ref = resolve_strict(
        cc.account_doc_ref_id_template,
        {"SENDING_FI_IN": submission.sending_company_in, "YEAR": submission.year},
    )
    _build_doc_spec(report, submission.document_type, acct_doc_ref)

    acct_num = _ce(report, _CRS + "AccountNumber", acct.account_number)
    if acct.account_number_type in _ACCTNUM_TYPE_MAP:
        acct_num.set("AcctNumberType", _ACCTNUM_TYPE_MAP[acct.account_number_type])
    acct_num.set("ClosedAccount",       "true" if acct.is_closed       else "false")
    acct_num.set("UndocumentedAccount", "true" if acct.is_undocumented else "false")
    acct_num.set("DormantAccount",      "true" if acct.is_dormant      else "false")

    holder = etree.SubElement(report, _CRS + "AccountHolder")
    if acct.sheet == "Individual":
        ind = etree.SubElement(holder, _CRS + "Individual")
        _build_person_party(
            ind,
            res_country=acct.tax_residence,
            tin=acct.tin, tin_issued_by=acct.tin_issued_by,
            first_name=acct.holder_first_name,
            last_name=acct.holder_last_name,
            address_country=acct.address_country,
            address_free=acct.address_free,
            birth_date=acct.holder_birth_date,
        )
    else:
        org = etree.SubElement(holder, _CRS + "Organisation")
        _build_organisation_party_body(
            org,
            res_country=acct.tax_residence,
            in_value=acct.tin, in_issued_by=acct.tin_issued_by,
            in_type=acct.in_type,
            name=acct.holder_name, name_type="legal",
            address_country=acct.address_country,
            address_free=acct.address_free,
        )
        # AcctHolderType from the slice — for CRS103 entity-only it's CRS103,
        # for derived-from-CRS103 CP slices it's CRS101.
        _ce(holder, _CRS + "AcctHolderType", slice_.holder_type_override)

    # ControllingPersons — from the slice, not the account directly. This is
    # the per-file scoping mechanism: a CRS101 slice for AT only includes the
    # AT CP, not the DE CP that also belongs to this account.
    for cp in slice_.cps_to_include:
        cp_elem = etree.SubElement(report, _CRS + "ControllingPerson")
        ind = etree.SubElement(cp_elem, _CRS + "Individual")
        _build_person_party(
            ind,
            res_country=cp.tax_residence,
            tin=cp.tin, tin_issued_by=cp.tin_issued_by,
            first_name=cp.first_name, last_name=cp.last_name,
            address_country=cp.address_country, address_free=cp.address_free,
            birth_date=cp.birth_date,
        )
        if cp.cp_type:
            _ce(cp_elem, _CRS + "CtrlgPersonType", cp.cp_type)

    balance = _ce(report, _CRS + "AccountBalance", _format_amount(acct.balance))
    balance.set("currCode", acct.balance_currency)

    for payment in acct.payments:
        p_elem = etree.SubElement(report, _CRS + "Payment")
        _ce(p_elem, _CRS + "Type", _PAYMENT_TYPE_MAP[payment.type])
        amnt = _ce(p_elem, _CRS + "PaymentAmnt", _format_amount(payment.amount))
        amnt.set("currCode", payment.currency)


# ---------------------------------------------------------------------------
# Reusable subtree builders (unchanged from the previous version)
# ---------------------------------------------------------------------------
def _build_person_party(parent, *, res_country, tin, tin_issued_by,
                        first_name, last_name, address_country, address_free,
                        birth_date):
    _ce(parent, _CRS + "ResCountryCode", res_country)

    tin_elem = _ce(parent, _CRS + "TIN", tin)
    if tin_issued_by:
        tin_elem.set("issuedBy", tin_issued_by)

    name = etree.SubElement(parent, _CRS + "Name")
    name.set("nameType", "OECD202")
    _ce(name, _CRS + "FirstName", first_name)
    _ce(name, _CRS + "LastName",  last_name)

    _build_address(parent, address_country, address_free)

    if birth_date:
        bi = etree.SubElement(parent, _CRS + "BirthInfo")
        _ce(bi, _CRS + "BirthDate", str(birth_date))


def _build_organisation_party_body(parent, *, res_country, in_value, in_issued_by,
                                   in_type, name, name_type,
                                   address_country, address_free):
    _ce(parent, _CRS + "ResCountryCode", res_country)

    in_elem = _ce(parent, _CRS + "IN", in_value)
    if in_issued_by:
        in_elem.set("issuedBy", in_issued_by)
    if in_type:
        in_elem.set("INType", in_type)

    name_elem = _ce(parent, _CRS + "Name", name)
    if name_type in _NAMETYPE_MAP:
        name_elem.set("nameType", _NAMETYPE_MAP[name_type])

    _build_address(parent, address_country, address_free)


def _build_address(parent, country_code, address_free, address_type=None):
    addr = etree.SubElement(parent, _CRS + "Address")
    if address_type and address_type in _ADDRTYPE_MAP:
        addr.set("legalAddressType", _ADDRTYPE_MAP[address_type])
    _ce(addr, _CFC + "CountryCode", country_code)
    _ce(addr, _CFC + "AddressFree", address_free)


def _build_doc_spec(parent, doc_type_indic, doc_ref_id, corr_msg_ref_id=None,
                    corr_doc_ref_id=None):
    ds = etree.SubElement(parent, _CRS + "DocSpec")
    _ce(ds, _STF + "DocTypeIndic", doc_type_indic)
    _ce(ds, _STF + "DocRefId",     doc_ref_id)
    if corr_msg_ref_id:
        _ce(ds, _STF + "CorrMessageRefId", corr_msg_ref_id)
    if corr_doc_ref_id:
        _ce(ds, _STF + "CorrDocRefId", corr_doc_ref_id)