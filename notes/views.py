from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_GET, require_POST
from inertia import render

from config.http import form_input, invalid_form, redirect_303

from .forms import NoteForm
from .models import Note


@login_required
@require_GET
def home(request):
    return render(
        request,
        "Home",
        props={
            "notes": lambda: [
                {"id": str(note.pk), "body": note.body}
                for note in Note.objects.filter(owner=request.user)[:50]
            ],
        },
    )


@login_required
@require_POST
def create(request):
    form = NoteForm(form_input(request, fields={"body"}))
    if not form.is_valid():
        return invalid_form(request, form, destination="home")
    note = form.save(commit=False)
    note.owner = request.user
    note.save()
    messages.success(request, "Note added")
    return redirect_303("home")


@login_required
@require_POST
def delete(request, note_id):
    note = get_object_or_404(Note, pk=note_id, owner=request.user)
    note.delete()
    messages.success(request, "Note deleted")
    return redirect_303("home")
