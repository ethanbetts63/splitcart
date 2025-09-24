from django.apps import apps

class ModelLister:
    def __init__(self, app_labels_to_exclude=None):
        self.app_labels_to_exclude = app_labels_to_exclude or []

    def get_all_models(self):
        """Returns a list of all installed models, excluding specified apps."""
        all_models = []
        for app_config in apps.get_app_configs():
            if app_config.label in self.app_labels_to_exclude:
                continue
            all_models.extend(app_config.get_models())
        return all_models
