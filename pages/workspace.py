"""
Workspace tenancy infrastructure for Personal-module data.

Used by Passports, Celebrations, and Recipes. The rest of Alivente Online
(CRS, Property Operations, Financial Management, Administration) does not
use this layer.

Three pieces:
  - WorkspaceManager: a model Manager subclass that adds .for_user(user)
    and .for_workspace(ws) query shortcuts. Attach to any tenanted model.
  - WorkspaceMiddleware: resolves request.workspace from the logged-in
    user's profile on every request. Does NOT auto-create — the workspace
    must already exist or request.workspace is None.
  - ensure_workspace(user): explicit auto-create helper. Call from a view
    when you know the user is about to need a workspace (e.g. on the first
    write to a Personal module). Idempotent — safe to call repeatedly.
"""

from django.db import models
from django.core.exceptions import ObjectDoesNotExist


# ===========================================================================
# Manager
# ===========================================================================
class WorkspaceManager(models.Manager):
    """Manager for models that carry a workspace ForeignKey.

    Usage in a tenanted model:

        from pages.workspace import WorkspaceManager

        class Passport(models.Model):
            workspace = models.ForeignKey('pages.Workspace', ...)
            # ... other fields ...
            objects = WorkspaceManager()

    Then in views:

        passports = Passport.objects.for_user(request.user)

    Returns an empty queryset (not an error) when the user has no
    workspace, so callers don't need defensive checks.
    """

    def for_user(self, user):
        """Filter to rows in the user's workspace; empty queryset if none."""
        if not getattr(user, 'is_authenticated', False):
            return self.none()
        workspace = _user_workspace(user)
        if workspace is None:
            return self.none()
        return self.filter(workspace=workspace)

    def for_workspace(self, workspace):
        """Filter to rows in a specific workspace (admin/internal use)."""
        return self.filter(workspace=workspace)


def _user_workspace(user):
    """Internal: return the user's workspace or None, swallowing all the
    AttributeError / ObjectDoesNotExist possibilities along the way."""
    try:
        profile = user.profile
    except (AttributeError, ObjectDoesNotExist):
        return None
    return getattr(profile, 'workspace', None)


# ===========================================================================
# Middleware
# ===========================================================================
class WorkspaceMiddleware:
    """Attach request.workspace to every request based on the logged-in
    user's profile. Anonymous users and users with no workspace get
    request.workspace = None.

    Does NOT auto-create a workspace — that's done explicitly via
    ensure_workspace() from views that need it. Auto-create on every
    request would create empty workspaces for every authenticated user
    regardless of whether they ever touch a Personal module.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.workspace = None
        if getattr(request, 'user', None) and request.user.is_authenticated:
            request.workspace = _user_workspace(request.user)
        return self.get_response(request)


# ===========================================================================
# Auto-create helper
# ===========================================================================
def ensure_workspace(user):
    """Return the user's workspace, creating a default one if they have none.

    Call this from views on the first write action a user attempts in a
    Personal module — e.g. when they try to create their first passport.
    Idempotent: safe to call on every request if you want.

    The auto-created workspace is owned by the user and named after their
    username. They can rename it later via the workspace settings UI
    (Phase 4 of the rollout — until then, only superusers can rename via
    Django admin).
    """
    # Avoid circular imports — UserProfile and Workspace both live in
    # pages.models which imports nothing from here.
    from pages.models import UserProfile, Workspace

    profile, _ = UserProfile.objects.get_or_create(user=user)
    if profile.workspace_id is not None:
        return profile.workspace

    workspace = Workspace.objects.create(
        name=f"{user.username}'s Workspace",
        owner=user,
    )
    profile.workspace = workspace
    profile.save(update_fields=['workspace', 'updated_at'])
    return workspace