import os
import tempfile
from django.test import TestCase
from api.utils.processing_utils.cleanup import cleanup

class TestCleanup(TestCase):

    def setUp(self):
        """Set up a temporary directory and create some fake files."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.file_paths = []
        for i in range(3):
            file_path = os.path.join(self.temp_dir.name, f"test_file_{i}.txt")
            with open(file_path, "w") as f:
                f.write("test content")
            self.file_paths.append(file_path)
        
        # Add a file that will be deleted before cleanup is called
        self.pre_deleted_file = os.path.join(self.temp_dir.name, "pre_deleted.txt")
        with open(self.pre_deleted_file, "w") as f:
            f.write("content")
        os.remove(self.pre_deleted_file) # Delete it immediately

    def tearDown(self):
        """Clean up the temporary directory."""
        self.temp_dir.cleanup()

    def test_cleanup_deletes_all_files(self):
        """Test that cleanup deletes all specified files."""
        for file_path in self.file_paths:
            self.assertTrue(os.path.exists(file_path))
        
        cleanup(self.file_paths)
        
        for file_path in self.file_paths:
            self.assertFalse(os.path.exists(file_path))

    def test_cleanup_handles_empty_list(self):
        """Test that cleanup handles an empty list of file paths without error."""
        cleanup([])
        # No assertions needed, just ensuring no errors are raised

    def test_cleanup_handles_nonexistent_files(self):
        """Test that cleanup handles file paths that do not exist."""
        nonexistent_file = os.path.join(self.temp_dir.name, "nonexistent_file.txt")
        paths_to_cleanup = self.file_paths + [nonexistent_file, self.pre_deleted_file]
        
        cleanup(paths_to_cleanup)
        
        # All original files should be deleted
        for file_path in self.file_paths:
            self.assertFalse(os.path.exists(file_path))
        
        # Nonexistent files should still not exist (no error raised)
        self.assertFalse(os.path.exists(nonexistent_file))
        self.assertFalse(os.path.exists(self.pre_deleted_file))