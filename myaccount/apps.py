from django.apps import AppConfig


class MyAccountConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'myaccount'

    def ready(self):

        import myaccount.signals

