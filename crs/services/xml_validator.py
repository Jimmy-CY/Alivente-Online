"""
crs.services.xml_validator — XSD validation against the OECD CRS v2.0 schema.

Public surface:
    validate(xml_bytes) -> XMLValidationResult

Loads the bundled schema from crs/schema/ (lazily, once per process) and
runs lxml's XSD validator against the supplied XML bytes. Returns a
result object with is_valid + per-error details.

The well-formedness check runs first (XML parse). If the document is
malformed, validation short-circuits with a single error tagged
domain_name='XML' — useful for distinguishing "this isn't even valid XML"
from "this is valid XML but breaks the schema."

The schema files must be present at crs/schema/:
    CrsXML_v2.0.xsd            — main schema, lxml resolves the rest as imports
    CommonTypesFatcaCrs_v2.0.xsd
    oecdcrstypes_v5.0.xsd
    isocrstypes_v1.1.xsd
    FatcaTypes_v1.2.xsd        — imported transitively for PoolReport types

If the main schema file is missing, validate() returns a result with one
error tagged domain_name='SETUP' rather than raising — so the caller can
surface the issue in the UI like any other validation failure.
"""
from dataclasses import dataclass, field
from pathlib import Path

from lxml import etree


SCHEMA_DIR  = Path(__file__).resolve().parent.parent / "schema"
MAIN_SCHEMA = SCHEMA_DIR / "CrsXML_v2.0.xsd"


@dataclass
class XMLValidationError:
    line: int
    column: int
    message: str
    domain_name: str   # 'XML' (well-formedness) | 'SCHEMASV' (XSD) | 'SETUP'


@dataclass
class XMLValidationResult:
    is_valid: bool = False
    errors: list = field(default_factory=list)

    @property
    def error_count(self):
        return len(self.errors)


# Cached compiled schema; loaded on first use. Safe to share across threads
# (lxml.etree.XMLSchema is read-only after construction).
_schema_cache = None


def _get_schema():
    """Load + cache the compiled XSD. Raises FileNotFoundError if the
    main schema file isn't on disk; caller catches and surfaces."""
    global _schema_cache
    if _schema_cache is None:
        if not MAIN_SCHEMA.exists():
            raise FileNotFoundError(
                f"OECD CRS schema not found at {MAIN_SCHEMA}. Extract the "
                f"schema ZIP into crs/schema/ — see xml_validator.py docstring "
                f"for the file list."
            )
        _schema_cache = etree.XMLSchema(etree.parse(str(MAIN_SCHEMA)))
    return _schema_cache


def validate(xml_bytes):
    """Validate XML bytes against the OECD CRS v2.0 schema.

    Returns XMLValidationResult; never raises for XML/XSD issues — those go
    into result.errors with appropriate domain_name. Only environment issues
    (missing schema files) produce a 'SETUP' error in the result.
    """
    result = XMLValidationResult(is_valid=False)

    # Stage 1: well-formedness. If the bytes don't parse as XML, no point
    # asking lxml to schema-validate them.
    try:
        doc = etree.fromstring(xml_bytes)
    except etree.XMLSyntaxError as ex:
        result.errors.append(XMLValidationError(
            line=ex.lineno or 0,
            column=ex.offset or 0,
            message=str(ex),
            domain_name="XML",
        ))
        return result

    # Stage 2: load schema. Cached after first call.
    try:
        schema = _get_schema()
    except FileNotFoundError as ex:
        result.errors.append(XMLValidationError(
            line=0, column=0, message=str(ex), domain_name="SETUP",
        ))
        return result

    # Stage 3: validate against schema.
    if schema.validate(doc):
        result.is_valid = True
        return result

    for err in schema.error_log:
        result.errors.append(XMLValidationError(
            line=err.line,
            column=err.column,
            message=err.message,
            domain_name=err.domain_name,
        ))
    return result