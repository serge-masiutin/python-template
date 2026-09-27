# Python AI Provider Boundary

Adaptation of Active Agent's agent, tool, prompt, structured-output and background
integration guidance. Preserve the separation of transport, orchestration and
provider I/O. No AI SDK or worker is installed by this starter.

## Installation and Configuration

Inspect `pyproject.toml` and the task before choosing a provider SDK. Pin a supported
version; verify its real method signatures. Keep model, timeout, maximum tool calls,
queue, retry policy and API credentials explicit in validated configuration.

## Basic Usage

### Define Agent

A domain-named application function accepts validated input and a provider boundary.
A Python `Protocol` is useful only where callers need a stable replaceable contract.
Do not reproduce an `ApplicationAgent` inheritance tree or hide network calls in
constructors and properties.

```python
from dataclasses import dataclass
from typing import Protocol

@dataclass(frozen=True)
class Summary:
    text: str

class Summarizer(Protocol):
    def summarize(self, *, document: str, prompt_version: str) -> Summary: ...

def summarize_document(*, document, provider: Summarizer):
    return provider.summarize(document=document.text, prompt_version="summary-v1")
```

These are application-owned interfaces, not claims about an installed provider API.
The adapter must validate the provider response before constructing `Summary`.

## Agents with Tools

Each tool has a bounded input/output schema and one responsibility. Retrieve data
under the current actor/tenant scope. Tool results are untrusted data, not authority.
Check authorization again at mutations; a model's proposed tool call is not consent.
Bound iteration, payload sizes and external effects. Start with one call before a
loop or multi-agent routing.

## System Prompts

Store versioned prompt templates near the feature, with objective, inputs,
constraints, tool policy, output schema and stop conditions. Pass document text as
untrusted context. Keep instructions out of concatenated user content.

## Structured Output

Use provider-supported structured output when available; validate it at the adapter
boundary. `TypedDict` and dataclasses alone do not validate external JSON. Reject
missing required fields and unexpected enum values instead of inventing defaults.

## Service Integration and Background Processing

The operation coordinates authorized inputs, persisted run state and a provider
call. Workers receive record IDs and re-load current execution scope. If enqueueing
must survive a crash, commit run state and durable job intent together. `on_commit`
avoids early execution but does not make a separate broker publish atomic.

## Testing

Use deterministic provider-boundary fakes for transport/error tests and representative
feature evaluations for semantic quality. Include malformed output, ambiguous input,
long context, injected instructions, forbidden tool access and provider timeout.
Record prompt/model versions and evaluation inputs without logging private documents.

## Error Handling

Catch only documented SDK exceptions where you can add context or recover. Preserve
causes. Distinguish failed, cancelled and unknown outcomes. Never retry a potentially
completed external mutation merely because a timeout occurred.
