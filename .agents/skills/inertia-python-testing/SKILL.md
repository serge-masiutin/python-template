---
name: inertia-python-testing
description: Test Django Inertia pages with pytest-django and Django Client. Verify components, safe props, redirects, one-use errors and messages, deferred and partial props, ownership, CSRF and asset versioning.
---

# Inertia Django Testing

Testing patterns for Django Client and pytest-django.

For each view verify component, authorized props, sensitive field allowlists,
mutation status, redirect destination, one-use messages/errors and loading rules.
After a 303, request Location before inspecting page props. Use
Client(enforce_csrf_checks=True) for mutation security tests; ordinary test clients
skip CSRF. Test guest, owner and foreign-owner access.

## Setup

```python
# pyproject.toml already configures DJANGO_SETTINGS_MODULE for pytest-django.
@pytest.mark.django_db
def test_home(client, user):
    client.force_login(user)
    response = client.get("/", HTTP_X_INERTIA="true")
    assert response.status_code == 200
    assert response.json()["component"] == "Home"
```

## Response Assertions

Use ordinary pytest assertions on response.status_code, headers and response.json().
There are no Ruby matchers in inertia-django. Assert exact security-sensitive
allowlists; assert selected fields for unrelated extensible page metadata.

## pytest Examples

```python
page = response.json()
assert page["component"] == "Home"
assert set(page["props"]["auth"]["user"]) == {"id", "username", "admin"}
assert "password" not in page["props"]["auth"]["user"]
```

```python
response = client.post("/notes/", {"body": "A note"})
assert response.status_code == 303
page = client.get(response["Location"], HTTP_X_INERTIA="true").json()
assert page["flash"]["messages"][0]["level"] == "success"

response = client.post("/notes/", {"body": ""})
assert response.status_code == 303
page = client.get(response["Location"], HTTP_X_INERTIA="true").json()
assert "body" in page["props"]["errors"]
assert client.get("/", HTTP_X_INERTIA="true").json()["props"]["errors"] == {}
```

### Test Shared Props

Shared props from share(request, ...) appear in page["props"].

```python
client.force_login(user)
page = client.get("/", HTTP_X_INERTIA="true").json()
assert page["props"]["auth"]["user"]["id"] == str(user.pk)
```

```python
page = client.get("/login/", HTTP_X_INERTIA="true").json()
assert page["props"]["auth"]["user"] is None
```

### Test Deferred Props

```python
page = client.get("/dashboard/", HTTP_X_INERTIA="true").json()
assert page["deferredProps"]["default"] == ["analytics"]
assert "analytics" not in page["props"]
```

### Partial Reload Helpers

```python
response = client.get("/", HTTP_X_INERTIA="true",
    HTTP_X_INERTIA_PARTIAL_COMPONENT="Home", HTTP_X_INERTIA_PARTIAL_DATA="notes")
props = response.json()["props"]
assert "notes" in props
assert "auth" not in props
assert "csrfToken" in props  # always prop
# Deferred props use the same partial reload headers with the deferred keys.
```

### Test External Redirects (location)

```python
response = client.post("/checkout/", HTTP_X_INERTIA="true")
assert response.status_code == 409
assert response["X-Inertia-Location"] == expected_provider_url
```

### Avoid False Confidence

- Do not mock away the real Inertia middleware in request tests.
- Do not inspect errors or messages on the redirect itself.
- Deferred values are absent on initial load; request their keys separately.
- Exercise CSRF and production database constraints as application integration contracts.
- Pair partial reload tests with foreign-owner tests; data selection is not authorization.
- Test form errors surviving an asset-version 409, then clearing after a successful GET.

### Direct Response Access

```python
page = response.json()
component = page["component"]
props = page["props"]
flash = page["flash"]
# Read deferredProps only for responses whose contract declares deferred props.
```

## Related Skills
- **Controller patterns** → `inertia-python-controllers` (prop types, flash, PRG)
- **Form flows** → `inertia-python-forms` (submission, validation)
- **Deferred/shared props** → `inertia-python-pages` (Deferred, usePage)

## References

Read [Django TestCase equivalents](references/django-testcase.md) when working in
a project that uses unittest-style assertions.


