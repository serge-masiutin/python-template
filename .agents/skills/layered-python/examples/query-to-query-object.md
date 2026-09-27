# Extract Query Logic to Query Object

Pull a long Django ORM chain out of a controller into a composable query object.

## Before

```python
# Before: authorized_orders and filters have already been validated at the boundary.
def sales(request):
    filters = SalesFilter(request.GET)
    if not filters.is_valid():
        return HttpResponseBadRequest("Invalid filters")
    orders = authorized_orders(request.user).filter(
        status="completed", created_at__range=(filters.cleaned_data["start"], filters.cleaned_data["end"])
    )
    if filters.cleaned_data["region"]:
        orders = orders.filter(customer__region=filters.cleaned_data["region"])
    rows = orders.annotate(day=TruncDate("created_at")).values("day").annotate(
        order_count=Count("pk", distinct=True), revenue=Sum(F("items__quantity") * F("items__price"))
    ).order_by("-day")
    return render(request, "Sales", props={"rows": list(rows)})
```

## After

```python
from dataclasses import dataclass
from django.db.models import Count, F, Sum
from django.db.models.functions import TruncDate


@dataclass(frozen=True)
class SalesReportQuery:
    orders: QuerySet

    def by_date_range(self, start, end):
        return SalesReportQuery(self.orders.filter(created_at__range=(start, end)))

    def by_region(self, region):
        return SalesReportQuery(self.orders.filter(customer__region=region)) if region else self

    def daily_summary(self):
        return self.orders.annotate(day=TruncDate("created_at")).values("day").annotate(
            order_count=Count("pk", distinct=True),
            revenue=Sum(F("items__quantity") * F("items__price")),
        ).order_by("-day")


query = SalesReportQuery(authorized_orders(actor).filter(status="completed"))
rows = query.by_date_range(start, end).by_region(region).daily_summary()
```

The query starts from an authorized scope. Define timezone, date inclusivity,
decimal representation and pagination in the response contract.
