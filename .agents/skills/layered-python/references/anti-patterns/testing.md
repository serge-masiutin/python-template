# Testing Anti-Patterns

Tests that verify the wrong layer's responsibilities.

## Testing Wrong Layer

**Problem:** Controller tests verify business logic.

```python
def test_vip_discount(client, vip_customer):
    client.force_login(vip_customer)
    client.post("/orders/", {"product": "book"})
    assert Order.objects.latest("pk").total == Decimal("90.00")
```

**Fix:** Test business logic in model specs.

```python
def test_order_applies_vip_discount(vip_customer, line_items):
    order = Order(customer=vip_customer)
    order.calculate_total(items=line_items)
    assert order.total == Decimal("90.00")


@pytest.mark.django_db
def test_create_order_redirects(client, customer):
    client.force_login(customer)
    response = client.post("/orders/", {"product": "book"})
    assert response.status_code == 303
    assert response["Location"].startswith("/orders/")
```
