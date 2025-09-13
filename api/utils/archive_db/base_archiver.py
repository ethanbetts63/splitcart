import os
import datetime
import shutil

class BaseArchiver:
    def __init__(self):
        self.date_stamp = datetime.datetime.now().strftime("%Y-%m-%d")
        self.base_output_dir = self._get_base_output_dir()
        self.archive_dir = os.path.join(self.base_output_dir, self.date_stamp)

    def _get_base_output_dir(self):
        # This can be overridden by subclasses if needed
        return os.path.join('api', 'data', 'archive', 'db_backups')

    def _ensure_directory_exists(self):
        if os.path.exists(self.archive_dir):
            shutil.rmtree(self.archive_dir)
        os.makedirs(self.archive_dir)
        print(f"Created archive directory: {self.archive_dir}")

    def archive(self):
        raise NotImplementedError("Subclasses must implement the archive() method.")

    def run(self):
        self._ensure_directory_exists()
        self.archive()