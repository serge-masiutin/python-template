from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    """Project-owned user model, configured before the first migration."""
