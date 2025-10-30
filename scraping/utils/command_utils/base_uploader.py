from django.conf import settings

class BaseUploader:
    def __init__(self, command, dev=False):
        self.command = command
        self.dev = dev

    def get_server_url(self):
        if self.dev:
            return 'http://127.0.0.1:8000'
        
        try:
            server_url = settings.API_SERVER_URL
            if not server_url:
                self.command.stderr.write(self.command.style.ERROR("API_SERVER_URL is not configured in settings or .env file."))
                return None
            return server_url
        except AttributeError:
            self.command.stderr.write(self.command.style.ERROR("API_SERVER_URL must be configured in settings or .env file."))
            return None

    def get_api_key(self):
        try:
            api_key = settings.API_SECRET_KEY
            if not api_key:
                self.command.stderr.write(self.command.style.ERROR("API_SECRET_KEY is not configured in settings or .env file."))
                return None
            return api_key
        except AttributeError:
            self.command.stderr.write(self.command.style.ERROR("API_SECRET_KEY must be configured in settings or .env file."))
            return None
