from scraping.management.commands.base_upload_command import BaseUploadCommand

class Command(BaseUploadCommand):
    help = 'Compresses and uploads product .jsonl files to the server.'

    @property
    def outbox_path_name(self) -> str:
        return 'product_outbox'

    @property
    def archive_path_name(self) -> str:
        return 'temp_jsonl_product_storage'

    @property
    def upload_url_path(self) -> str:
        return '/api/upload/products/'
