from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from shopping_cart.models import Customer

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_customer_for_new_user(sender, **kwargs):
  """
  This code defines a signal receiver function named create_customer_for_new_user that is triggered
  whenever a new user is saved in the Django authentication system.
  The function creates a new Customer object associated with the newly created user
  """
  if kwargs['created']:
    Customer.objects.create(user=kwargs['instance'])