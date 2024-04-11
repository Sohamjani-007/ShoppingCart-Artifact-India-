from django.apps import AppConfig


class StoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'shopping_cart'

    def ready(self) -> None:
        import shopping_cart.signals.handlers
