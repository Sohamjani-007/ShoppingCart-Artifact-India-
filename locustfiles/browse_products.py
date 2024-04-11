from locust import HttpUser, task, between
from random import randint


class WebsiteUser(HttpUser):
    wait_time = between(1, 5)

    @task(2)
    def view_products(self):
        collection_id = randint(2, 6)
        self.client.get(
            f'/shopping_cart/products/?collection_id={collection_id}',
            name='/shopping_cart/products')

    @task(4)
    def view_product(self):
        product_id = randint(1, 1000)
        self.client.get(
            f'/shopping_cart/products/{product_id}',
            name='/shopping_cart/products/:id')

    @task(1)
    def add_to_cart(self):
        product_id = randint(1, 10)
        self.client.post(
            f'/shopping_cart/carts/{self.cart_id}/items/',
            name='/shopping_cart/carts/items',
            json={'product_id': product_id, 'quantity': 1}
        )

    @task
    def say_hello(self):
        self.client.get('/playground/hello/')

    def on_start(self):
        response = self.client.post('/shopping_cart/carts/')
        result = response.json()
        self.cart_id = result['id']
