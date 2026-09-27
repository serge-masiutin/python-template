# Agent skills

The catalog contains 32 project-local skills. React, Storybook and general Evil
Martians payloads are restored byte-for-byte from the official catalog snapshot.
Local framework-independent skills are preserved from rails-template. Python
adaptations keep their original file mapping and a complete textual patch.
These are bundled repository instructions, not a separately hosted skill marketplace.

## Catalog

| Skill | Origin / treatment |
|---|---|
| [design-system](../.agents/skills/design-system/SKILL.md) | Original EM payload |
| [llms-visibility](../.agents/skills/llms-visibility/SKILL.md) | Original EM payload |
| [intent-log](../.agents/skills/intent-log/SKILL.md) | Original EM payload |
| [sb-audit](../.agents/skills/sb-audit/SKILL.md) | Original EM payload |
| [sb-explore](../.agents/skills/sb-explore/SKILL.md) | Original EM payload |
| [sb-figma](../.agents/skills/sb-figma/SKILL.md) | Original EM payload |
| [sb-flows](../.agents/skills/sb-flows/SKILL.md) | Original EM payload |
| [sb-health](../.agents/skills/sb-health/SKILL.md) | Original EM payload |
| [sb-hub](../.agents/skills/sb-hub/SKILL.md) | Original EM payload |
| [sb-inventory](../.agents/skills/sb-inventory/SKILL.md) | Original EM payload |
| [sb-setup](../.agents/skills/sb-setup/SKILL.md) | Original EM payload |
| [sb-ship](../.agents/skills/sb-ship/SKILL.md) | Original EM payload |
| [sb-stories](../.agents/skills/sb-stories/SKILL.md) | Original EM payload |
| [sb-wrappers](../.agents/skills/sb-wrappers/SKILL.md) | Original EM payload |
| [good-readme](../.agents/skills/good-readme/SKILL.md) | Original EM payload |
| [inertia-python-architecture](../.agents/skills/inertia-python-architecture/SKILL.md) | Python adaptation |
| [inertia-python-setup](../.agents/skills/inertia-python-setup/SKILL.md) | Python adaptation |
| [inertia-python-controllers](../.agents/skills/inertia-python-controllers/SKILL.md) | Python adaptation |
| [inertia-python-forms](../.agents/skills/inertia-python-forms/SKILL.md) | Python adaptation |
| [inertia-python-pages](../.agents/skills/inertia-python-pages/SKILL.md) | Python adaptation |
| [inertia-python-typescript](../.agents/skills/inertia-python-typescript/SKILL.md) | Python adaptation |
| [inertia-python-testing](../.agents/skills/inertia-python-testing/SKILL.md) | Python adaptation |
| [shadcn-inertia](../.agents/skills/shadcn-inertia/SKILL.md) | Python adaptation |
| [skills-visibility](../.agents/skills/skills-visibility/SKILL.md) | Original EM payload |
| [secure-npm-package](../.agents/skills/secure-npm-package/SKILL.md) | Original EM payload |
| [tailwind-best-practices](../.agents/skills/tailwind-best-practices/SKILL.md) | Original EM payload |
| [layered-python](../.agents/skills/layered-python/SKILL.md) | Python adaptation |
| [python-serialization](../.agents/skills/python-serialization/SKILL.md) | Python adaptation |
| [python-boot-profiling](../.agents/skills/python-boot-profiling/SKILL.md) | Python adaptation |
| [clear-writing](../.agents/skills/clear-writing/SKILL.md) | Preserved Rails-template skill |
| [data-systems-architecture](../.agents/skills/data-systems-architecture/SKILL.md) | Preserved Rails-template skill |
| [book-to-skill](../.agents/skills/book-to-skill/SKILL.md) | Preserved Rails-template skill |

## Source of truth

[skills-lock.json](../config/skills-lock.json) pins rails-template commit
bc536d2f596d8f73daf2d59968221bf7315b5c94, EM URLs and digests, file hashes,
original archives and explicit old-to-new path mappings. The local upstream catalog
snapshot is [em-catalog.json](../config/em-catalog.json).

layered-python starts from all 57 files of the original layered-rails skill.
The four-layer model, extraction signals, specification-test method, 13 patterns,
eight examples and audit/refactoring workflows remain. Ruby snippets and mechanism
references are adapted to Django Forms, ORM, explicit operations/policies, dataclasses,
React, Python logging and native profiling. Ten gem references map to Python
mechanism files. The archive plus patch makes every changed paragraph reviewable.
Python has no mandatory service base, implicit actor context or Ruby DSL equivalent.

The Rails-specific serialization and boot-profiling skills retain their workflows
with explicit Python DTOs and importtime/cProfile. Inertia skills retain frontend
patterns while server contracts use inertia-django; frontend alternatives for Vue
and Svelte remain reference material. They do not imply those adapters are installed.

## Updating

1. Read the existing source, mapping, consumers and tests.
2. For an upstream update, download the actual official payload and verify its digest
   before replacing files. Review the payload; a hash does not establish trust.
3. For an adaptation, preserve the pinned original archive and update mapped targets.
   Explicitly record a path rename in mapping; never silently remove source coverage.
4. Run `uv run --frozen python scripts/update-skill-lock.py` after reviewing changes.
   This regenerates patches and local adaptation hashes, never upstream baselines.
5. Run bin/ci and the affected application/skill contract cases.

See [skill evaluation cases](skill-evals.md). Structural checks and concrete API
contract tests are automated; an autonomous agent evaluation is a separate activity
and is not represented by file hashes or compilation.
