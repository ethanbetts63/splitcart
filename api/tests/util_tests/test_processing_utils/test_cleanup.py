import os
import tempfile
from django.test import TestCase
from api.utils.processing_utils.cleanup import cleanup

class TestCleanup(TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.file_paths = []
        for i in range(3):
            file_path = os.path.join(self.temp_dir.name, f"test_file_{i}.txt")
            with open(file_path, "w") as f:
                f.write("test")
            self.file_paths.append(file_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_cleanup_deletes_files(self):
        self.assertTrue(os.path.exists(self.file_paths[0]))
        cleanup(self.file_paths)
        self.assertFalse(os.path.exists(self.file_paths[0]))

    def test_cleanup_handles_empty_list(self):
        cleanup([])
