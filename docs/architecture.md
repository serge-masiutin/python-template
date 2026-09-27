# Architecture

Django views own HTTP parsing, authentication, authorization and explicit response
composition. Forms validate input; models own data invariants; QuerySets own simple
queries. Add an application operation when a use case coordinates multiple records
or external effects. Avoid a mandatory service class or repository for ordinary CRUD.

## Request and browser contract

| Route | Method | Contract |
|---|---|---|
| / | GET | Authenticated Home, latest 50 owned notes |
| /login/ | GET, POST | Login page or AuthenticationForm submission |
| /logout/ | POST | End session, clear encrypted history, redirect |
| /notes/ | POST | Validate body, attach server-selected owner |
| /notes/<id>/delete/ | POST | Delete only an owned note; otherwise 404 |
| /admin/ | Django admin | Staff gate and Django model permissions |
| /health/ | GET | DB SELECT 1; 200 only when ready |

Mutations require CSRF and return 303 on success or validation errors. Malformed
JSON, unexpected keys and repeated fields return 400. Django Form errors are
one-use field strings; __all__ is the non-field key. The shared middleware preserves
errors, messages and history flags before an asset-version 409 can consume them.

Shared props are auth.user (nullable), csrfToken and errors. Django messages appear
in page.flash.messages. User and note IDs are strings. INERTIA_JSON_ENCODER uses
DjangoJSONEncoder to reject accidental ORM model serialization; DTOs list fields.
All page responses have private, no-store caching. Partial selection does not grant
access; every deferred/partial request must authorize before querying.

## Persistence and side effects

PostgreSQL is the deployed database; SQLite is only a fast test boundary. Notes have
an owner FK, a non-empty body constraint and a recent-owner index. Django sessions
live in the database. Staff visibility in React is only presentation; Django admin
rechecks current permissions. Database credentials belong to environment config.

Use transaction.atomic for coordinated writes. transaction.on_commit runs after a
successful commit but is not durable delivery; use an explicit outbox/queue only
when an actual external effect requires it. No worker or AI SDK is installed.

## Frontend

web/src/app.tsx resolves explicit Login/Home component names. React owns local UI;
Django owns URLs, sessions and data. Inertia Form/router use the shared X-CSRFToken
header. Do not enable a second automatic injector for that same header.
Native anchors enter Django admin because it is outside the Inertia app.
