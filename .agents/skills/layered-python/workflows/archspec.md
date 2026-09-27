# Import Boundary Checks

Adapt the source architecture-lint workflow to Python imports. Use the
[mechanism reference](../references/mechanisms/import-boundaries.md).

## 1. Check Availability

Inspect pyproject.toml, lockfile, tests and CI for an existing architecture checker.
Use its installed version and documentation. This starter has no import-linter
dependency. Do not invoke the Ruby archspec command or install a checker solely
to satisfy the source workflow.

## 2. Inspect the Codebase

Discover feature packages, views, models, operations and integration adapters.
Identify actual forbidden edges: domain code importing HTTP views, model code
importing delivery entrypoints, or application code importing React presentation.
Preserve existing exceptions and inspect their consumers before changing them.

## 3. Generate Tailored Rules

Use the existing checker, or a small test for a concrete forbidden import.
Python AST import enumeration alone is not a complete dependency graph: account
for relative imports, re-exports, package initialization and dynamic imports.
Add a fixture that violates each rule so a checker that never fails cannot pass.
Never require base classes, folders or suffixes that the project does not use.

## 4. Run and Classify Failures

Run the actual configured command. Distinguish real dependency violations from
misclassified packages and intentionally allowed infrastructure imports. Fix the
classification or code; do not weaken a rule merely to make CI green.

If existing debt needs a baseline, list exact edges with their reason and owner.
New violations must still fail. Never refresh a baseline to absorb new debt.

## 5. Integrate into CI

Add the verified command to bin/ci and its workflow. Exercise one deliberate
violation locally, revert the fixture, and verify a passing clean run.

## 6. Report

Report rules, exclusions, coverage limits and actual command results. State when
dynamic imports or framework callbacks remain outside static analysis.
