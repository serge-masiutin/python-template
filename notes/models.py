from django.conf import settings
from django.db import models
from django.db.models import Q


class Note(models.Model):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notes"
    )
    body = models.CharField(max_length=2000)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-pk"]
        constraints = [models.CheckConstraint(condition=~Q(body=""), name="note_body_not_empty")]
        indexes = [models.Index(fields=["owner", "-created_at", "-id"], name="note_owner_recent")]
