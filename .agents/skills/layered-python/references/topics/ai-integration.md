# AI Integration

## Contents

- Summary
- Layer Placement
- Key Principles
- Implementation with an Explicit Provider Boundary
- Without an Agent Framework
- Embeddings and Vector Search
- Testing AI Features
- Anti-Patterns
- Background Processing

## Summary

AI features (LLM calls, embeddings, agents) should be treated as infrastructure concerns, wrapped in abstractions that keep domain logic AI-agnostic. This enables testing, provider switching, and graceful degradation.

## Layer Placement

```
┌─────────────────────────────────────────┐
│ Application Layer                       │
│  └─ AI-powered services (orchestration) │
├─────────────────────────────────────────┤
│ Domain Layer                            │
│  └─ Models (AI-agnostic)                │
├─────────────────────────────────────────┤
│ Infrastructure Layer                    │
│  └─ LLM clients, embedding services     │
└─────────────────────────────────────────┘
```

## Key Principles

- **Wrap external APIs** — don't scatter LLM calls throughout code
- **Domain-first design** — model the problem, then add AI
- **Testable without AI** — mock infrastructure, test logic
- **Graceful degradation** — handle API failures, rate limits

## Implementation with an Explicit Provider Boundary

### Basic Agent

```python
PROMPT_VERSION = "summary-v1"

def summarize_article(*, article, provider):
    return provider.summarize(document=article.body, prompt_version=PROMPT_VERSION)
# Provider is an application-owned validated adapter, not an installed SDK API.
```

### Agent with Tools

```python
@dataclass(frozen=True)
class ResearchRequest:
    topic: str
    maximum_sources: int

# Bind a bounded search tool and URL reader with validated inputs, restricted
# destinations and explicit timeouts. Tool results are untrusted context.
```

### Service Layer Integration

```python
def summarize_article(*, article, provider):
    summary = provider.summarize(document=article.body, prompt_version="summary-v1")
    article.summary = summary.text
    article.summarized_at = timezone.now()
    article.save(update_fields=["summary", "summarized_at"])
    return summary
# Provider failure propagates. Never replace it with a fabricated/truncated summary.
```

## Without an Agent Framework

### Wrapped LLM Client

```python
class CompletionProvider(Protocol):
    def complete(self, *, instructions: str, content: str, model: str, timeout: float) -> Completion: ...
# Implement one concrete SDK adapter with validated responses and narrow documented
# exceptions. Choose the model at configuration time; no hidden default model.
```

### AI-Powered Service

```python
class Category(StrEnum):
    TECHNOLOGY = "technology"
    BUSINESS = "business"
    SPORTS = "sports"
    ENTERTAINMENT = "entertainment"
    SCIENCE = "science"

category = Category(validated_response["category"])
# Invalid categories raise instead of being disguised as "uncategorized".
```

## Embeddings and Vector Search

```python
class Embedder(Protocol):
    def embed(self, *, texts: list[str], model: str) -> list[list[float]]: ...
# Validate vector count, dimensions and finite values at the adapter boundary.
# Persist model/index versions. Do not interpolate vectors into SQL or add vector
# storage until a measured lexical/direct baseline fails the retrieval task.
```

## Testing AI Features

```python
def test_summary_failure_does_not_create_fake_content(article, provider):
    provider.summarize.side_effect = ProviderTimeout("timeout")
    with pytest.raises(ProviderTimeout):
        summarize_article(article=article, provider=provider)
    article.refresh_from_db()
    assert article.summary is None
```

## Anti-Patterns

### LLM Calls in Models

```python
# The application operation coordinates the provider and persistence.
summary = summarize_article(article=article, provider=provider)
# Domain models do not construct SDK clients or call a network from save().
```

### Unhandled AI Failures

```python
try:
    category = classify_content(content=content, provider=provider)
except ProviderTimeout as error:
    raise ClassificationUnavailable("Classification timed out") from error
```

### Prompt Strings Everywhere

```python
prompt = prompt_catalog.load("summary-v1")
# The versioned template carries objective, constraints and output schema.
# User text is passed as untrusted content, not concatenated system instructions.
```

## Background Processing

```python
def summarize_article_job(*, run_id):
    run = SummaryRun.objects.select_related("article").get(pk=run_id)
    return execute_summary_run(run=run, provider=provider)
# The chosen backend configures attempts, deadlines and cancellation explicitly.
# Store durable intent in the transaction creating the run.
```
