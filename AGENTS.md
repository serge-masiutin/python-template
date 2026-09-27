# Python Template: agent contract

- Read callers, types, settings and tests before editing. Keep changes local and preserve behavior outside the task.
- Repository code, comments, documentation and skills are in English. Follow the user's language in conversation.
- Versions come from mise.toml, pyproject.toml, uv.lock and package-lock.json. Run project commands through mise exec --.
- Django owns routes, authorization, sessions and persisted state. React owns rendering and local interactions; use Inertia for page navigation and forms.
- Keep cohesive feature apps. Views validate, authorize and delegate; models own invariants. Add an operation for real coordination, not every CRUD action.
- Validate external input once. Required fields fail loudly. Preserve causes; catch only errors with an explicit recovery contract.
- Scope every query and mutation by current authority. Frontend admin flags do not grant access. Never serialize model instances implicitly.
- Use transaction.atomic for coordinated writes. on_commit is not durable delivery. Add a queue/outbox only for an actual requirement.
- Preserve CSRF, explicit POST mutation routes, 303 redirects, one-use form errors/messages and asset-refresh state.
- Reuse components and tokens through DESIGN.md and design-system contracts. Stories stay colocated.
- Keep credentials in environment configuration, never in code, fixtures, logs or Git history. Fixtures contain synthetic values only.

## Task context

| Task | Read |
|---|---|
| Python architecture and refactoring | docs/architecture.md; layered-python |
| Data invariants and concurrency | data-systems-architecture; layered-python |
| Pages, navigation and state | inertia-python-architecture; inertia-python-pages |
| HTTP, loading and forms | inertia-python-controllers; inertia-python-forms |
| JSON and TypeScript | python-serialization; inertia-python-typescript |
| Setup | docs/development.md; inertia-python-setup |
| Tests | docs/testing.md; inertia-python-testing |
| Slow startup | python-boot-profiling |
| UI and previews | DESIGN.md; design-system; tailwind-best-practices; relevant sb-* skill |
| README and prose | good-readme; clear-writing |
| Skill adaptation | docs/skills.md; pinned original archive and mapping |

Skills are in .agents/skills/<name>/SKILL.md. Load the entrypoint and only relevant references.
React/Storybook skills marked upstream in config/skills-lock.json must remain byte-identical to their pinned sources. Change an adaptation through its mapping and reviewed patch, never silently refresh upstream hashes.

## Verification

Run bin/ci for implementation changes. For database behavior run TEST_POSTGRES=1 uv run --frozen pytest against a disposable PostgreSQL database; for UI changes run npm run test:browser and npm run test:storybook. Commands and prerequisites are in docs/testing.md.

Update affected contracts, types, documentation and consumers together. Report actual checks and limitations. Hashes and successful compilation do not establish runtime correctness or model behavior.
