import subprocess
import os
from .base_archiver import BaseArchiver
from .model_lister import ModelLister

class DatabaseArchiver(BaseArchiver):
    def __init__(self):
        super().__init__()
        # Exclude Django's internal apps and others that don't need backing up
        apps_to_exclude = ['admin', 'auth', 'contenttypes', 'sessions', 'messages', 'staticfiles']
        self.model_lister = ModelLister(app_labels_to_exclude=apps_to_exclude)

    def archive(self):
        """Archives each model to a separate JSON file using dumpdata."""
        print("Starting database archive...")
        models_to_archive = self.model_lister.get_all_models()

        if not models_to_archive:
            print("No models found to archive.")
            return

        for model in models_to_archive:
            app_label = model._meta.app_label
            model_name = model._meta.model_name
            
            output_filename = f"{app_label}.{model_name}.json"
            output_filepath = os.path.join(self.archive_dir, output_filename)
            
            self.command.stdout.write(f"  - Archiving {app_label}.{model_name}...")

            python_executable = os.path.abspath(os.path.join('venv', 'Scripts', 'python.exe'))
            command = [
                python_executable, 'manage.py', 'dumpdata',
                f'{app_label}.{model_name}',
                '--output', output_filepath,
                '--indent', '2'
            ]

            env = os.environ.copy()
            env['PYTHONIOENCODING'] = 'utf-8'

            try:
                subprocess.run(command, check=True, capture_output=True, text=True, env=env, encoding='utf-8', errors='replace')
            except subprocess.CalledProcessError as e:
                self.command.stderr.write(self.command.style.ERROR(f"    Failed to archive {app_label}.{model_name}.\n    Error: {e.stderr}"))

        self.command.stdout.write(self.command.style.SUCCESS("\nDatabase archive complete."))
        self.command.stdout.write(f"Files saved in: {self.archive_dir}")
