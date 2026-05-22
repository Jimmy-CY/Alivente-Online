"""
crs.services.tokens — Template token resolver for CRS reference IDs and filenames.

Templates use [TOKEN] placeholders that get replaced at resolution time with
values from a context dict and dynamically computed values (timestamps, UUIDs).

Supported tokens:
    [SENDING_FI_IN]  — the FI's IN used as SendingCompanyIN (from context)
    [YEAR]           — the reporting year as a 4-digit string (from context)
    [YYYYMMDDHHMM]   — current UTC timestamp, e.g. "202605211015"
    [CURRENT_DATE]   — current UTC date as YYYYMMDD, e.g. "20260521"
    [UUID]           — a fresh 12-char hex UUID slice (unique per resolution)

Each call to resolve() that hits a dynamic token ([YYYYMMDDHHMM], [CURRENT_DATE],
[UUID]) generates a fresh value, so calling resolve() twice on the same template
will not produce identical strings if those tokens are present.

Unknown tokens are left in place by resolve(); use resolve_strict() to raise
ValueError if any token can't be substituted.

Functions:
    resolve(template, context)        — Returns the resolved string.
    resolve_strict(template, context) — Like resolve, but raises if any token remains.
"""
import re
import uuid
from datetime import datetime, timezone


_TOKEN_RE = re.compile(r"\[([A-Z_]+)\]")


def _now():
    """Return current UTC datetime. Pulled out for test patching."""
    return datetime.now(timezone.utc)


def _dynamic_values():
    """Compute the dynamic tokens that change on every call."""
    now = _now()
    return {
        "YYYYMMDDHHMM": now.strftime("%Y%m%d%H%M"),
        "CURRENT_DATE": now.strftime("%Y%m%d"),
        "UUID":         uuid.uuid4().hex[:12].upper(),
    }


def resolve(template, context):
    """Resolve [TOKEN] placeholders in template using context + dynamic values."""
    values = {**_dynamic_values(), **{k: str(v) for k, v in context.items()}}

    def _sub(match):
        token = match.group(1)
        return values.get(token, match.group(0))

    return _TOKEN_RE.sub(_sub, template)


def resolve_strict(template, context):
    """Like resolve(), but raises ValueError if any [TOKEN] remains unresolved."""
    resolved = resolve(template, context)
    leftover = _TOKEN_RE.findall(resolved)
    if leftover:
        raise ValueError(
            f"Unresolved tokens in template: {', '.join(sorted(set(leftover)))}"
        )
    return resolved