from django.contrib import admin
from django.db import connection
from django.http import JsonResponse
from django.urls import path
from django.views.decorators.http import require_GET

from accounts import views as accounts
from notes import views as notes


@require_GET
def health(request):
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1")
        cursor.fetchone()
    return JsonResponse({"status": "ok"})


urlpatterns = [
    path("", notes.home, name="home"),
    path("login/", accounts.login, name="login"),
    path("logout/", accounts.logout, name="logout"),
    path("notes/", notes.create, name="note-create"),
    path("notes/<int:note_id>/delete/", notes.delete, name="note-delete"),
    path("admin/", admin.site.urls),
    path("health/", health, name="health"),
]
