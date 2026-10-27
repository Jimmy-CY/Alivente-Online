"""
pages.views package aggregator.

This app's URL configuration (pages/urls.py) does `from . import views`
and references view callables as `views.<name>`. The views were split out
of a single large module into focused submodules; to keep that flat
`views.<name>` namespace working for the URLconf, every submodule is
re-exported here with a wildcard import.

The `# noqa: F401, F403` markers are intentional: these wildcard
re-exports exist solely so each view resolves as `pages.views.<name>`
for the URLconf - they are not accidental unused imports.

Import order here is organisational, not load-bearing: each submodule is
imported on first reference, and the submodules satisfy their own
cross-module needs via explicit relative imports (e.g. finance imports
from properties/dashboard). No submodule imports from this package's
former `main.py`.

Historical note: a `main.py` shim previously sat at the top of this list
and additionally re-exported a large block of library imports. Every view
now lives in a dedicated module (recipes in the `recipes` sub-package),
so `main.py` was retired and its redundant `from .main import *` removed.
"""

from .properties import *  # noqa: F401, F403
from .dashboard import *  # noqa: F401, F403
from .wcim import *  # noqa: F401, F403
from .finance import *  # noqa: F401, F403
from .petty_cash import *  # noqa: F401, F403
from .suppliers import *  # noqa: F401, F403
from .invoices import *  # noqa: F401, F403
from .receipts import *  # noqa: F401, F403
from .passports import *  # noqa: F401, F403
from .celebrations import *  # noqa: F401, F403
from .users import *  # noqa: F401, F403
from .administration import *  # noqa: F401, F403
from .notifications import *  # noqa: F401, F403
from .projects import *  # noqa: F401, F403
from .issues import *  # noqa: F401, F403
from .expenses import *  # noqa: F401, F403
from .tenants import *  # noqa: F401, F403
from .auth import *  # noqa: F401, F403
from .home import *  # noqa: F401, F403
from .notifications_dashboard import *  # noqa: F401, F403
from .lease_template import *  # noqa: F401, F403
# ES-3a, 23 Oct 2026 - the lease signing register. `import *` obeys
# __all__, so a view missing from that list does not exist to the
# URLconf no matter how correct it is - RV-1 learned that on 23 Oct.
from .lease_signing import *  # noqa: F401, F403
from .lease_signing_status import *  # noqa: F401, F403  LS-1, 27 Oct 2026
# ES-4, 24 Oct 2026 - the signing page itself. Same note as above: a
# view missing from __all__ does not exist to the URLconf.
from .lease_signing_sign import *  # noqa: F401, F403
# ES-3b, 24 Oct 2026 - the send screen. AFTER lease_signing_sign,
# because it imports _invite from it; the other order is an import
# cycle that fails at startup rather than at the first request.
from .lease_signing_create import *  # noqa: F401, F403
# ES-6, 25 Oct 2026 - one envelope in full, and the approval of a
# signed lease onto its tenant.
from .lease_signing_approve import *  # noqa: F401, F403
# ES-7, 25 Oct 2026 - his saved signature and the company stamp,
# superuser only.
from .house_marks import *  # noqa: F401, F403
from .recipes import *  # noqa: F401, F403
from .help import *  # noqa: F401, F403
from .household import *
from .physical_invoices import *