import os
from django.conf import settings
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = "Count lines of code in all apps of the project"

    def add_arguments(self, parser):
        parser.add_argument('--exclude-migrations', action='store_true', help="Excludes migration files from count")

    def handle(self, *args, **kwargs):
        project_root = settings.BASE_DIR
        total_lines = 0
        exclude_migrations = kwargs['exclude_migrations']

        for root, dirs, files in os.walk(project_root):
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    if exclude_migrations and 'migrations' in root:
                        continue
                    with open(file_path, 'r') as f:
                        lines = f.readlines()
                        total_lines += len(lines)
                        print(f"{file_path}: {len(lines)} lines")
        self.stdout.write(self.style.SUCCESS(f"Total lines of code: {total_lines}"))