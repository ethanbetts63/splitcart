import os
from django.conf import settings
from api.utils.database_updating_utils.from_archive.update_stores_from_archive_file import update_stores_from_archive_file

def update_stores_from_archive(command):
    command.stdout.write(command.style.SQL_FIELD("--- Starting Store Update from Archive ---"))
    archive_path = os.path.join(settings.BASE_DIR, 'api', 'data', 'archive', 'company_data')

    if not os.path.exists(archive_path):
        command.stdout.write(command.style.WARNING('Company data archive directory not found.'))
        return

    for filename in os.listdir(archive_path):
        if not filename.endswith('.json'):
            continue

        file_path = os.path.join(archive_path, filename)
        command.stdout.write(command.style.SQL_FIELD(f"Processing file: {filename}..."))
        
        company_name, stores_processed = update_stores_from_archive_file(file_path)
        
        if company_name:
            command.stdout.write(command.style.SUCCESS(f"  Successfully processed {stores_processed} stores for {company_name}."))
        else:
            command.stderr.write(command.style.ERROR(f"  Failed to process {filename}."))

    command.stdout.write(command.style.SQL_FIELD("--- Store Update from Archive Complete ---"))
