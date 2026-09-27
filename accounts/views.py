from django.contrib.auth import login as start_session
from django.contrib.auth import logout as end_session
from django.contrib.auth.forms import AuthenticationForm
from django.views.decorators.http import require_http_methods, require_POST
from inertia import render
from inertia.http import clear_history

from config.http import form_input, invalid_form, redirect_303


@require_http_methods(["GET", "POST"])
def login(request):
    if request.user.is_authenticated:
        return redirect_303("home")
    if request.method == "GET":
        return render(request, "Login")
    form = AuthenticationForm(request, data=form_input(request, fields={"username", "password"}))
    if not form.is_valid():
        return invalid_form(request, form, destination="login")
    start_session(request, form.get_user())
    return redirect_303("home")


@require_POST
def logout(request):
    end_session(request)
    clear_history(request)
    return redirect_303("login")
