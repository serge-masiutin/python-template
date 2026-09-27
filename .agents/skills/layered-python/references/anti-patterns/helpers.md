# Helper Anti-Patterns

Helpers doing work that belongs in templates or components.

## HTML Construction in Helpers

**Problem:** Helpers building HTML programmatically instead of providing logic for templates.

```python
# Bad: a backend helper owns React's markup and presentation structure.
def message_html(message):
    return format_html('<div id="message-{}" class="message">{}</div>', message.pk, message.body)
```

**Issues:**
- HTML structure hidden in Python code, harder to read and modify
- No template preview, harder to collaborate with designers
- Logic and markup tightly coupled
- Testing requires rendering, not unit testable
- Misses React component benefits (sidecar assets, previews, slots)

**Signal:** Heavy use of `tag.div`, `tag.button`, `tag.span` or complex `content_tag` chains.

**Fix:** Extract to React component with template.

```python
def message_props(message):
    return {"id": str(message.pk), "body": message.body, "emojiOnly": message.is_emoji_only()}
```

```tsx
function Message({ message, children }: { message: MessageProps; children: React.ReactNode }) {
  return <article id={`message-${message.id}`} className={message.emojiOnly ? "message-emoji" : "message"}>
    <p>{message.body}</p>{children}
  </article>;
}
```

**Rule of thumb:** If a helper method has more than 2-3 `tag.*` calls or builds nested HTML structure, extract to React component.
