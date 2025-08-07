from django.apps import AppConfig

# This should be the ONLY AppConfig class in this file.
class BackendConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'backend' # This should be the actual name of your Django app folder

    # Add the ready() method here to import your signals file.
    def ready(self):
        import backend.signals 