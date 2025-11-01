from data_management.utils.archive_db.database_archiver import DatabaseArchiver

class ArchiveGenerator:
    def __init__(self, command):
        self.command = command

    def run(self):
        archiver = DatabaseArchiver()
        archiver.command = self.command
        archiver.run()
