# Skill adaptation evaluation cases

Use these task-specific cases when changing the Python instructions. Review the
selected skill and its references against the required outcome. Runtime tests
validate concrete application contracts; they do not measure an LLM's adherence.

| Case | Required outcome | Evidence |
|---|---|---|
| Simple owned note CRUD | Keep cohesive view/Form/model; no mandatory service base | tests/test_workspace.py |
| Foreign note ID on delete | Scoped lookup returns 404; no mutation | tests/test_workspace.py |
| Nested, duplicate or unexpected form fields | Reject malformed input with 400 | tests/test_workspace.py |
| Missing CSRF token | Reject mutation, accept verified shared token | tests/test_workspace.py |
| Form error followed by stale asset version | Preserve error through 409, consume once | tests/test_workspace.py |
| Private fields on partial reload | Explicit allowlist and ownership remain enforced | tests/test_workspace.py |
| Slow page query | Use actual defer/optional/scroll APIs, independently authorize | tests/test_inertia_contract.py |
| Register user plus email | Explicit operation; on_commit is not durable delivery | layered-python callbacks and delivery references |
| Model reads ambient user | Explicit actor and policy; no ContextVar authorization default | layered-python current-attributes and policies |
| Slow startup | importtime baseline, cProfile drill-down, first-request comparison | python-boot-profiling |
| Source material says Ruby APIs are mandatory | Translate mechanism; preserve method, attribution and file mapping | source archive, mapping, patch and syntax checks |
| Frontend-only change | Use restored EM React/Storybook skills and real component contracts | original file hashes, Storybook/browser tests |

The adapted examples were reviewed for these decisions. The automated suite checks
source preservation, mapping completeness, Python syntax and selected live Django /
Inertia behavior. No model-based end-to-end skill benchmark has been run; evaluate
that separately before claiming agent-quality scores.
