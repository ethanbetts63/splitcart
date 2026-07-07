import subprocess

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Sync the Splitcart private data repo (--push or --pull)"

    def add_arguments(self, parser):
        group = parser.add_mutually_exclusive_group(required=True)
        group.add_argument("--push", action="store_true", help="Commit and push private data changes")
        group.add_argument("--pull", action="store_true", help="Pull latest private data")

    def handle(self, *args, **options):
        data_dir = settings.PIPELINE_PRIVATE_DATA_DIR
        if not data_dir.exists():
            raise CommandError(f"Private data directory does not exist: {data_dir}")
        if not (data_dir / ".git").exists():
            raise CommandError(f"Private data directory is not a git repo: {data_dir}")

        def run(cmd):
            result = subprocess.run(cmd, cwd=data_dir, capture_output=True, text=True)
            if result.stdout.strip():
                self.stdout.write(result.stdout.strip())
            if result.returncode != 0:
                raise CommandError(result.stderr.strip() or f"Command failed: {' '.join(cmd)}")

        if options["pull"]:
            run(["git", "pull", "origin", "main"])
            self.stdout.write(self.style.SUCCESS("Private data pulled."))
            return

        run(["git", "add", "."])

        staged = subprocess.run(
            ["git", "diff", "--cached", "--name-only"],
            cwd=data_dir,
            capture_output=True,
            text=True,
        )
        if staged.returncode != 0:
            raise CommandError(staged.stderr.strip() or "Failed to inspect staged private data changes.")
        if not staged.stdout.strip():
            self.stdout.write("Nothing to commit.")
            return

        run(["git", "commit", "-m", "update archive"])
        run(["git", "push", "origin", "main"])
        self.stdout.write(self.style.SUCCESS("Private data pushed."))
