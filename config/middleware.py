"""Shared browser contracts and one-use response state."""

from django.conf import settings
from django.middleware.csrf import get_token
from django.utils.cache import patch_vary_headers
from inertia import always, location, share


def shared_props(get_response):
    def middleware(request):
        if (
            request.method == "GET"
            and "X-Inertia" in request.headers
            and request.headers.get("X-Inertia-Version", settings.INERTIA_VERSION)
            != settings.INERTIA_VERSION
        ):
            # Refresh before rendering can consume session errors, messages or history flags.
            response = location(request.build_absolute_uri())
            patch_vary_headers(response, ("X-Inertia",))
        else:
            user = request.user
            share(
                request,
                auth={
                    "user": {"id": str(user.pk), "username": user.username, "admin": user.is_staff}
                    if user.is_authenticated
                    else None
                },
                csrfToken=always(lambda: get_token(request)),
                errors=always(lambda: request.session.pop("form_errors", {})),
            )
            response = get_response(request)
        response["Cache-Control"] = "private, no-store"
        return response

    return middleware
