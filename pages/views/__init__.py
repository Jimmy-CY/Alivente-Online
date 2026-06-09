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
from .recipes import *  # noqa: F401, F403
from .help import *  # noqa: F401, F403
from .household import *