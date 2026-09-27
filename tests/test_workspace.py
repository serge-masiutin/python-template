import json

import pytest
from django.test import Client
from django.urls import reverse

from accounts.models import User
from notes.models import Note

pytestmark = pytest.mark.django_db


@pytest.fixture
def user():
    return User.objects.create_user(username="alice", password="strong-test-password")


@pytest.fixture
def signed_in(client, user):
    client.force_login(user)
    return client


def page(client, path="/", **headers):
    response = client.get(path, HTTP_X_INERTIA="true", **headers)
    assert response.status_code == 200
    return response.json()


def test_requires_login(client):
    assert client.get("/").status_code == 302


def test_login_and_logout(client, user):
    response = client.post("/login/", {"username": "alice", "password": "strong-test-password"})
    assert response.status_code == 303
    assert page(client)["component"] == "Home"
    response = client.post("/logout/")
    assert response.status_code == 303
    assert page(client, "/login/")["clearHistory"] is True
    assert client.get("/").status_code == 302


def test_login_errors_are_consumed_once(client):
    response = client.post("/login/", {"username": "absent", "password": "wrong"})
    assert response.status_code == 303
    assert "__all__" in page(client, "/login/")["props"]["errors"]
    assert page(client, "/login/")["props"]["errors"] == {}


def test_notes_are_owned_and_serialized(signed_in, user):
    other = User.objects.create_user(username="bob")
    Note.objects.create(owner=other, body="private")
    note = Note.objects.create(owner=user, body="mine")
    props = page(signed_in)["props"]
    assert props["notes"] == [{"id": str(note.pk), "body": "mine"}]
    assert set(props["auth"]["user"]) == {"id", "username", "admin"}
    assert "password" not in json.dumps(props)


def test_create_and_delete_note(signed_in, user):
    response = signed_in.post("/notes/", {"body": "new"}, content_type="application/json")
    assert response.status_code == 303
    note = Note.objects.get(owner=user)
    response = signed_in.post(reverse("note-delete", args=[note.pk]))
    assert response.status_code == 303
    assert not Note.objects.exists()


def test_cannot_delete_another_users_note(signed_in):
    other = User.objects.create_user(username="bob")
    note = Note.objects.create(owner=other, body="private")
    assert signed_in.post(reverse("note-delete", args=[note.pk])).status_code == 404
    assert Note.objects.filter(pk=note.pk).exists()


@pytest.mark.parametrize("body", ["", " " * 20, "x" * 2001])
def test_invalid_note_redirects_to_field_errors(signed_in, body):
    response = signed_in.post("/notes/", {"body": body})
    assert response.status_code == 303
    assert "body" in page(signed_in)["props"]["errors"]
    assert not Note.objects.exists()


@pytest.mark.parametrize(
    "payload", [[], {"body": {"nested": "invalid"}}, {"body": "x", "owner": "2"}]
)
def test_rejects_malformed_contract(signed_in, payload):
    assert signed_in.post("/notes/", payload, content_type="application/json").status_code == 400
    assert not Note.objects.exists()


def test_rejects_duplicate_fields(signed_in):
    assert (
        signed_in.post(
            "/notes/", "body=a&body=b", content_type="application/x-www-form-urlencoded"
        ).status_code
        == 400
    )


def test_mutations_require_csrf(user):
    client = Client(enforce_csrf_checks=True)
    client.force_login(user)
    assert client.post("/notes/", {"body": "x"}).status_code == 403
    response = client.get("/", HTTP_X_INERTIA="true")
    token = response.json()["props"]["csrfToken"]
    assert client.post("/notes/", {"body": "x"}, HTTP_X_CSRFTOKEN=token).status_code == 303


def test_partial_reload_includes_csrf_and_errors(signed_in):
    props = page(
        signed_in, HTTP_X_INERTIA_PARTIAL_COMPONENT="Home", HTTP_X_INERTIA_PARTIAL_DATA="notes"
    )["props"]
    assert set(props) == {"notes", "csrfToken", "errors"}


def test_regular_user_cannot_enter_admin(signed_in):
    assert signed_in.get("/admin/").status_code == 302


def test_page_cache_and_version_contract(signed_in):
    response = signed_in.get("/", HTTP_X_INERTIA="true")
    assert response["Cache-Control"] == "private, no-store"
    assert "X-Inertia" in response["Vary"]
    stale = signed_in.get("/", HTTP_X_INERTIA="true", HTTP_X_INERTIA_VERSION="old")
    assert stale.status_code == 409


def test_errors_survive_asset_refresh(client):
    client.post("/login/", {"username": "missing", "password": "wrong"})
    response = client.get("/login/", HTTP_X_INERTIA="true", HTTP_X_INERTIA_VERSION="old")
    assert response.status_code == 409
    assert response["Cache-Control"] == "private, no-store"
    assert "__all__" in page(client, "/login/")["props"]["errors"]
    assert page(client, "/login/")["props"]["errors"] == {}


def test_messages_survive_asset_refresh(signed_in):
    signed_in.post("/notes/", {"body": "message"})
    assert (
        signed_in.get("/", HTTP_X_INERTIA="true", HTTP_X_INERTIA_VERSION="old").status_code == 409
    )
    assert page(signed_in)["flash"]["messages"] == [{"level": "success", "message": "Note added"}]
    assert "flash" not in page(signed_in)


def test_rejects_duplicate_json_fields(signed_in):
    response = signed_in.post("/notes/", '{"body":"a","body":"b"}', content_type="application/json")
    assert response.status_code == 400
    assert not Note.objects.exists()


def test_notes_are_bounded(signed_in, user):
    Note.objects.bulk_create([Note(owner=user, body=f"note {number}") for number in range(55)])
    assert len(page(signed_in)["props"]["notes"]) == 50
