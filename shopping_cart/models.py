from django.contrib import admin
from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from uuid import uuid4

from shopping_cart.validators import validate_file_size


class Promotion(models.Model):
    """
    The Promotion class is a Django model that represents a promotion for a product.
    It has fields for the description of the promotion and the discount amount.
    Example Usage
    promotion = Promotion(description='Summer Sale', discount=0.2)
    promotion.save()
    The main functionality of the Promotion class is to store information about a promotion, including its description and discount amount.
    """
    description = models.CharField(max_length=255)
    discount = models.FloatField()


class Collection(models.Model):
    """
    title: A character field that stores the title of the collection.
    featured_product: A foreign key field that references the Product model and stores the featured product for the collection.
    """
    title = models.CharField(max_length=255)
    featured_product = models.ForeignKey(
        'Product', on_delete=models.SET_NULL, null=True, related_name='+', blank=True)

    def __str__(self) -> str:
        return self.title

    class Meta:
        ordering = ['title']


class Product(models.Model):
    """
    title: A character field that stores the title of the product.
    slug: A slug field that stores a URL-friendly version of the title.
    description: A text field that stores the description of the product.
    unit_price: A decimal field that stores the unit price of the product.
    inventory: An integer field that stores the inventory count of the product.
    last_update: A datetime field that stores the last update time of the product.
    collection: A foreign key field that references the Collection model and stores the collection to which the product belongs.
    promotions: A many-to-many field that references the Promotion model and stores the promotions associated with the product.
    """
    title = models.CharField(max_length=255)
    slug = models.SlugField()
    description = models.TextField(null=True, blank=True)
    unit_price = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        validators=[MinValueValidator(1)])
    inventory = models.IntegerField(validators=[MinValueValidator(0)])
    last_update = models.DateTimeField(auto_now=True)
    collection = models.ForeignKey(
        Collection, on_delete=models.PROTECT, related_name='products')
    promotions = models.ManyToManyField(Promotion, blank=True)

    def __str__(self) -> str:
        return self.title

    class Meta:
        ordering = ['title']


class ProductImage(models.Model):
    """
    product: A foreign key field that references the Product model and stores the product to which the image belongs.
    image: An ImageField that stores the image file. The image file is uploaded to the 'shopping_cart/images' directory and is validated using the validate_file_size function
    """
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(
        upload_to='shopping_cart/images',
        validators=[validate_file_size])


class Customer(models.Model):
    """
    phone: CharField for storing the customer's phone number.
    birth_date: DateField for storing the customer's birth date.
    membership: CharField for storing the customer's membership level.
    user: OneToOneField for associating the customer with a user from the User model.
    """
    MEMBERSHIP_BRONZE = 'B'
    MEMBERSHIP_SILVER = 'S'
    MEMBERSHIP_GOLD = 'G'

    MEMBERSHIP_CHOICES = [
        (MEMBERSHIP_BRONZE, 'Bronze'),
        (MEMBERSHIP_SILVER, 'Silver'),
        (MEMBERSHIP_GOLD, 'Gold'),
    ]
    phone = models.CharField(max_length=255)
    birth_date = models.DateField(null=True, blank=True)
    membership = models.CharField(
        max_length=1, choices=MEMBERSHIP_CHOICES, default=MEMBERSHIP_BRONZE)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.user.first_name} {self.user.last_name}'

    @admin.display(ordering='user__first_name')
    def first_name(self):
        return self.user.first_name

    @admin.display(ordering='user__last_name')
    def last_name(self):
        return self.user.last_name

    class Meta:
        ordering = ['user__first_name', 'user__last_name']
        permissions = [
            ('view_history', 'Can view history')
        ]


class Order(models.Model):
    """
    placed_at: DateTimeField that stores the date and time the order was placed. It is automatically set to the current date and time when the order is created.
    payment_status: CharField that stores the payment status of the order. It has choices for 'Pending', 'Complete', and 'Failed', with a default value of 'Pending'.
    customer: ForeignKey to the Customer model, representing the customer who placed the order. The on_delete parameter is set to PROTECT, which means the order cannot be deleted if the associated customer is deleted.
    """
    PAYMENT_STATUS_PENDING = 'P'
    PAYMENT_STATUS_COMPLETE = 'C'
    PAYMENT_STATUS_FAILED = 'F'
    PAYMENT_STATUS_CHOICES = [
        (PAYMENT_STATUS_PENDING, 'Pending'),
        (PAYMENT_STATUS_COMPLETE, 'Complete'),
        (PAYMENT_STATUS_FAILED, 'Failed')
    ]

    placed_at = models.DateTimeField(auto_now_add=True)
    payment_status = models.CharField(
        max_length=1, choices=PAYMENT_STATUS_CHOICES, default=PAYMENT_STATUS_PENDING)
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT)

    class Meta:
        permissions = [
            ('cancel_order', 'Can cancel order')
        ]


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order, on_delete=models.PROTECT, related_name='items')
    product = models.ForeignKey(
        Product, on_delete=models.PROTECT, related_name='orderitems')
    quantity = models.PositiveSmallIntegerField()
    unit_price = models.DecimalField(max_digits=6, decimal_places=2)


class Address(models.Model):
    """
    order: ForeignKey to the Order model, representing the order to which the item belongs.
    product: ForeignKey to the Product model, representing the product associated with the item.
    quantity: PositiveSmallIntegerField that stores the quantity of the item.
    unit_price: DecimalField that stores the unit price of the item.
    """
    street = models.CharField(max_length=255)
    city = models.CharField(max_length=255)
    customer = models.ForeignKey(
        Customer, on_delete=models.CASCADE)


class Cart(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4)
    created_at = models.DateTimeField(auto_now_add=True)


class CartItem(models.Model):
    """
    id: A UUID field that serves as the primary key for the cart. It is automatically generated using the uuid4 function from the uuid module.
    created_at: A DateTimeField that stores the timestamp when the cart was created. It is automatically set to the current datetime when a new cart is created.
    """
    cart = models.ForeignKey(
        Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1)]
    )

    class Meta:
        unique_together = [['cart', 'product']]


class Review(models.Model):
    """
    product: A foreign key field that references the Product model and stores the product being reviewed.
    name: A character field that stores the name of the reviewer.
    description: A text field that stores the description of the review.
    date: A date field that stores the date the review was created.
    """
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name='reviews')
    name = models.CharField(max_length=255)
    description = models.TextField()
    date = models.DateField(auto_now_add=True)
