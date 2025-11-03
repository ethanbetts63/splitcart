from django.contrib.staticfiles.storage import ManifestStaticFilesStorage

class CachedManifestStaticFilesStorage(ManifestStaticFilesStorage):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.headers['Cache-Control'] = 'max-age=31536000, immutable'
