from django.apps import AppConfig


class BackendConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'backend'

class YourAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'your_app_name' # Make sure this matches your app's name

    def ready(self):
        import your_app_name.signals # Import the signals