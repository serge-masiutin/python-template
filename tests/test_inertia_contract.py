"""Exercise the concrete loading APIs used in the adapted skills."""

import pytest
from django.test import override_settings
from django.urls import path
from inertia import always, defer, merge, once, optional, render, scroll


def example(request):
    return render(
        request,
        "Example",
        props={
            "summary": {"count": 1},
            "expensive": defer(lambda: {"total": 2}, group="analytics"),
            "export": optional(lambda: ["safe"]),
            "csrfToken": always("test-token"),
            "countries": once(lambda: ["GB"], expires_at=60),
            "messages": merge(lambda: [{"id": "1", "body": "safe"}], match_on="id"),
            "rows": scroll(
                lambda: [{"id": "1"}],
                {
                    "pageName": "page",
                    "currentPage": 1,
                    "previousPage": None,
                    "nextPage": 2,
                },
            ),
        },
    )


urlpatterns = [path("example/", example)]


@pytest.mark.django_db
@override_settings(ROOT_URLCONF=__name__)
def test_loading_contract(client):
    initial = client.get("/example/", HTTP_X_INERTIA="true").json()
    assert initial["component"] == "Example"
    assert initial["deferredProps"] == {"analytics": ["expensive"]}
    assert "expensive" not in initial["props"]
    assert "export" not in initial["props"]
    assert initial["props"]["rows"] == [{"id": "1"}]
    assert initial["scrollProps"]["rows"]["nextPage"] == 2
    partial = client.get(
        "/example/",
        HTTP_X_INERTIA="true",
        HTTP_X_INERTIA_PARTIAL_COMPONENT="Example",
        HTTP_X_INERTIA_PARTIAL_DATA="expensive,export,messages",
    ).json()
    assert set(partial["props"]) == {"expensive", "export", "messages", "csrfToken", "errors"}
    assert partial["props"]["expensive"] == {"total": 2}
    assert partial["props"]["export"] == ["safe"]
    assert partial["mergeProps"] == ["messages"]
    assert partial["matchPropsOn"] == ["messages.id"]
