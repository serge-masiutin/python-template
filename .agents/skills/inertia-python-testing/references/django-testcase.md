# Django TestCase Assertions for Inertia

## Setup

Use Django TestCase and the real middleware. Authentication uses force_login;
CSRF-specific scenarios use Client(enforce_csrf_checks=True).

## Assertions

| Contract | Assertion |
|---|---|
| Status | self.assertEqual(response.status_code, 200) |
| Component | self.assertEqual(response.json()["component"], "Home") |
| Safe fields | self.assertEqual(set(user_props), {"id", "username", "admin"}) |
| Redirect | Check status 303 and Location, then GET the destination |
| Missing prop | self.assertNotIn("secret", response.json()["props"]) |

## Example

```python
class WorkspaceTests(TestCase):
    def test_login_page(self):
        response = self.client.get("/login/", HTTP_X_INERTIA="true")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["component"], "Login")
        self.assertIsNone(response.json()["props"]["auth"]["user"])
```

Deferred and partial prop requests use the same X-Inertia headers as the pytest
examples in the parent skill; the protocol does not depend on the test framework.
