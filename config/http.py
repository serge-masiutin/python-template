"""The browser form boundary and Post/Redirect/Get responses."""

import json

from django.core.exceptions import SuspiciousOperation
from django.http import HttpResponse
from django.urls import reverse


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise SuspiciousOperation("Repeated JSON form field")
        result[key] = value
    return result


def form_input(request, *, fields):
    allowed = set(fields) | {"csrfmiddlewaretoken"}
    if request.content_type == "application/json":
        try:
            payload = json.loads(request.body, object_pairs_hook=unique_object)
        except (json.JSONDecodeError, UnicodeDecodeError) as error:
            raise SuspiciousOperation("Malformed JSON form") from error
        if not isinstance(payload, dict) or any(
            not isinstance(value, str) for value in payload.values()
        ):
            raise SuspiciousOperation("Expected an object of string form values")
        if set(payload) - allowed:
            raise SuspiciousOperation("Unexpected form field")
        return payload
    if request.content_type not in {"application/x-www-form-urlencoded", "multipart/form-data"}:
        raise SuspiciousOperation("Expected JSON or browser form data")
    if set(request.POST) - allowed or any(
        len(request.POST.getlist(key)) != 1 for key in request.POST
    ):
        raise SuspiciousOperation("Unexpected or repeated form field")
    return request.POST


def redirect_303(name, **kwargs):
    return HttpResponse(status=303, headers={"Location": reverse(name, kwargs=kwargs)})


def invalid_form(request, form, *, destination):
    request.session["form_errors"] = {name: str(errors[0]) for name, errors in form.errors.items()}
    return redirect_303(destination)
