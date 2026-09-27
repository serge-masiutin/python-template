"""Prepare only the isolated browser-test database and synthetic accounts."""

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main():
    os.environ["DJANGO_SETTINGS_MODULE"] = "config.settings_browser"
    (ROOT / "tmp").mkdir(exist_ok=True)
    import django

    django.setup()
    from django.core.management import call_command

    from accounts.models import User

    call_command("migrate", verbosity=0)
    call_command("collectstatic", interactive=False, verbosity=0)
    for username, is_staff in [("browser-member", False), ("browser-admin", True)]:
        user, _ = User.objects.get_or_create(username=username)
        user.set_password("browser-test-password")
        user.is_staff = is_staff
        user.is_superuser = is_staff
        user.save()
        user.notes.all().delete()


if __name__ == "__main__":
    main()
