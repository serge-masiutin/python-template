# Value Objects

## Contents

- Summary
- When to Use
- When NOT to Use
- Key Principles
- Implementation
- Money Example
- Anti-Patterns
- Performance Note
- Related Mechanisms

## Summary

Value objects encapsulate domain concepts that are defined by their attributes rather than identity. They're immutable, comparable by value, and often created from multiple database columns or JSON stores.

## When to Use

- Domain concepts like Money, Address, Coordinates
- Groups of related attributes that travel together
- Attributes with behavior (formatting, validation, comparison)
- JSON/JSONB column wrappers with validation

## When NOT to Use

- Entities with identity (use models)
- Simple scalar values without behavior

## Key Principles

- **Immutable** — value objects don't change after creation
- **Equality by value** — two objects with same attributes are equal
- **No identity** — no `id` field, not persisted directly
- **Self-contained** — all behavior related to the concept

## Implementation

### Using Data Class

```python
from dataclasses import dataclass

@dataclass(frozen=True, order=True)
class MediaType:
    content_type: str

    def is_video(self):
        return self.content_type.startswith("video/")

    def is_image(self):
        return self.content_type.startswith("image/")

    def is_svg(self):
        return self.content_type in {"image/svg", "image/svg+xml"}

    def is_font(self):
        return self.content_type in {"font/otf", "font/ttf", "font/woff", "font/woff2"}

assert MediaType("image/png").is_image()
```

### Usage in Models

```python
# Only construct this value after validating the upload's actual media type.
media_type = MediaType(upload.content_type)
if media_type.is_video():
    validate_video_limits(upload)
```

### With `composed_of` (Multiple Columns)

```python
@dataclass(frozen=True)
class Address:
    country: str
    city: str
    street: str
    postal_code: str

    def full_address(self):
        return ", ".join((self.street, self.city, self.postal_code, self.country))

address = Address(user.address_country, user.address_city, user.address_street, user.address_postal_code)
```

### With JSON Store

```python
# JSONField has no domain schema. Validate on ingestion, then construct directly.
form = AddressForm(raw_address)
if not form.is_valid():
    raise ValidationError(form.errors)
address = Address(**form.cleaned_data)
user.address = asdict(address)
user.save(update_fields=["address"])
```

### With store_model Gem

```python
class AddressForm(forms.Form):
    country = forms.CharField(max_length=2)
    city = forms.CharField(max_length=100)
    street = forms.CharField(max_length=200)
    postal_code = forms.CharField(max_length=20)
```

## Money Example

```python
from decimal import Decimal, ROUND_HALF_UP

@dataclass(frozen=True)
class Money:
    amount_cents: int
    currency: str

    def __post_init__(self):
        if self.currency not in {"USD", "EUR", "GBP"}:
            raise ValueError("Unsupported currency")

    def __add__(self, other):
        if self.currency != other.currency:
            raise ValueError("Currency mismatch")
        return Money(self.amount_cents + other.amount_cents, self.currency)

    def __mul__(self, multiplier: Decimal):
        cents = (Decimal(self.amount_cents) * multiplier).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
        return Money(int(cents), self.currency)

    def __str__(self):
        return f"{Decimal(self.amount_cents) / 100:.2f} {self.currency}"

assert str(Money(1999, "USD") * Decimal("2")) == "39.98 USD"
```

## Anti-Patterns

### Mutable Value Objects

```python
@dataclass(frozen=True)
class Address:
    city: str
    street: str
```

### Value Objects With Side Effects

```python
@dataclass(frozen=True)
class Coordinates:
    x: Decimal
    y: Decimal

    def distance_to(self, other):
        return ((self.x - other.x) ** 2 + (self.y - other.y) ** 2).sqrt()

# Cache writes belong to an explicit infrastructure caller, never the value.
```

## Performance Note

Use dataclasses for domain values and Django Forms for external input. Choose based on responsibilities; measure Python behavior before making performance claims. The Ruby benchmark in the original source does not transfer to Python.

## Related Mechanisms

| Mechanism | Purpose |
|-----|---------|
| store_model | Django forms for JSON store attributes |
| frozen_record | Query static YAML/JSON like Django ORM |
