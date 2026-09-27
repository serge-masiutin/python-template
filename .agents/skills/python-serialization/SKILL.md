---
name: python-serialization
description: Serialize explicit JSON boundaries in Django and Inertia without leaking model data; keep entity, page, shared, loading, and consumer type contracts separate. Use for Inertia props and independent JSON APIs.
---

# Python Serialization

Keep reusable entity shapes, page-specific responses, shared data, loading policy,
and consumer types separate. Django renders Inertia pages with explicit props. Use explicit Python DTOs at
JSON boundaries and keep independent APIs separate.

## Setup: Establish Whether Serialization Is Needed

Inspect the consumer, authorization scope, schema, content limits and existing DTOs.
Inertia pages use explicit render(request, component, props=...). Reuse a small
entity serializer only when its shape is shared. Django admin remains ordinary HTML.
The starter does not include the Rails trace viewer or native client; do not invent
those contracts or expose raw provider payloads as a replacement.

## Entity Shape

Use a named small serializer/value object when the shape is reused. List fields rather
than passing a model to an implicit JSON encoder. Pass context explicitly where needed;
serialization should not query, mutate, send notifications, or consult hidden global state.

```python
def project_summary(project):
    return {"id": str(project.pk), "name": project.name,
            "updated_at": project.updated_at.isoformat()}
```

This is an illustrative feature object, not an existing starter feature. Confirm ID
representation and timestamp precision with the consumer contract. Use select_related/prefetch_related
in the query layer if the shape needs them; test collection growth for N+1.

## Page-Specific Response

Compose only the entities and metadata a real JSON consumer needs. Keep pagination,
filters, totals, and domain records distinct. Authorize and scope before serializing.
Don't let a serializer choose the actor's accessible collection implicitly.

```python
@login_required
def index(request):
    projects = projects_visible_to(request.user).order_by("pk")[:50]
    return render(request, "Projects/Index", props={
        "projects": [project_summary(project) for project in projects],
    })
```

The example demonstrates a bounded shape, not a complete pagination API. A production
collection contract must define navigation/cursors and limits appropriate to the feature.
For independent APIs, return JsonResponse with the API’s explicit schema.

## Shared Data

Share only the layout’s public contract. The starter provides auth, csrfToken and
errors; Django messages appear separately in page.flash.messages. Do not expose
password hashes, session identifiers, arbitrary settings or entire user models.
The CSRF token is an intentional browser contract, not a session credential.

## Explicit Rendering and Naming

There is no implicit resource lookup or instance-variable serialization. Use
inertia.render(request, component, props=...) or JsonResponse explicitly. Keep
INERTIA_JSON_ENCODER set to DjangoJSONEncoder: the adapter’s default encoder can
serialize arbitrary models. A DTO must not query, mutate or infer authorization.

## Types and Schema

Read inertia-python-typescript. Define IDs, nullability, omitted fields, enums,
timestamp format and order. Update web/src/types.ts with the producer and tests.
TypeScript annotations do not validate independent network JSON at runtime.
No type generator is installed. If added, pin its inputs, command and consumers.

## Loading Options

Read [loading-options.md](references/loading-options.md) for the complete mapping of
regular, optional, deferred/grouped, once/expiry, merge/deep-merge, always, and scroll
options. Loading belongs to the request/job/UI boundary, not a side effect of serializing
an attribute. Use actual inertia helpers at the view boundary; do not add loading behavior to DTO fields.

## Troubleshooting

| Symptom | Cause to investigate | Resolution |
| --- | --- | --- |
| Unexpected/private fields | Unrestricted model JSON or merged SDK payload | Restore explicit allowlist and negative access tests |
| Collection is slow | Serializer queries per item | Preload at query boundary, verify N+1 |
| Consumer missing field | Producer/consumer schema drift | Update both and test version compatibility |
| Null silently becomes empty | Undocumented default/optional chaining | Define optionality and reject malformed required input |
| “Resource not found” expectation | Copied implicit resource convention | Use explicit Django render call |
| Types never generated | Generator not installed/configured | Use actual contract; don't claim a nonexistent task |
| Stale or unauthorized cached JSON | Missing access/version scope | Recheck authorization and correct cache boundary |

## Gate

Verify exact allowlist where sensitive, access for guest/owner/foreign/admin as applicable,
malformed external input, collection size/query behavior, consumer parsing/compilation,
and backward compatibility for published consumers. Never include real secrets,
user documents, prompt bodies, or raw traces in fixtures.
