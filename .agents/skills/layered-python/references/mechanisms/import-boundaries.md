# Python Import Boundaries

Adaptation of ArchSpec's division of labor, tailored rules, incremental adoption,
exceptions and limits. Preserve architecture reasoning; do not translate the Ruby
DSL into a nonexistent Python API.

## Division of Labor

Use architectural review for responsibility, hidden I/O and specification tests.
Use a deterministic import check for explicitly forbidden dependencies. Neither
static imports nor folder names prove transaction, authorization or runtime behavior.

## Installation and Reference Configuration

For a small project, the standard-library `ast` module can inspect imports. Adopt
`import-linter` only when several stable package contracts justify the dependency;
verify its version and documented configuration first.

A domain package can forbid `django.http`, views, React integration and provider
adapters while permitting `django.db.models` for cohesive ORM models. A Django
model's ORM base is an intentional framework dependency, not proof that the app
needs a repository abstraction.

```python
import ast
from pathlib import Path

def imported_modules(filename):
    tree = ast.parse(Path(filename).read_text(), filename=str(filename))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            yield from (alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            yield "." * node.level + (node.module or "")
```

This extraction example is not a complete checker. Resolve relative imports against
the package, handle package re-exports and match exact module prefixes in the actual
check before claiming enforcement. Never treat a grep result as a complete dependency
graph.

## What Each Rule Enforces

- HTTP views may parse requests and call operations.
- Domain behavior must not import HTTP views, request globals or deliveries.
- Operations own transaction boundaries and explicit adapter calls.
- Framework adapters may depend on domain contracts; domain value objects remain pure.

Keep the repository's feature packages; do not manufacture empty folders for each
conceptual layer. Runtime call direction and import direction are distinct graphs.

## Domain Services and Escape Hatches

QuerySets and query functions are legitimate ORM data-access boundaries. A focused
exception names the exact import, reason and owner. Excluding an entire folder from
a checker removes its protections: restate applicable constraints explicitly. Do not
use exceptions to permit unreviewed reverse dependencies or ambient actor access.

## Tailoring the Config

Inspect imports, call sites, settings loading, framework registries and tests first.
Write a failing fixture for a forbidden edge and a passing fixture for a legitimate
one, including relative imports. Wire the check into the real `bin/ci` only after
those fixtures run. Do not assume a named architecture tool is installed.

## Adopting on an Existing Codebase

Record a precise baseline of existing violations, reject new violations and reduce
the baseline gradually. Avoid broad module ignores. Structural moves and behavior
changes should remain separate when practical.

## Advanced Per-Package Contracts

Prefer feature-owned packages. Add stricter boundaries only when repeated violations
justify them. Validate transitive edges when the rule forbids indirect dependencies;
a direct-import check cannot establish that stronger promise.

## What Static Checks Cannot Check

Dynamic imports, plugin loading, runtime registries, external calls, authorization,
commit timing and concurrency need runtime or contract tests. Architectural judgment
still applies to a file whose imports happen to satisfy the checker.
