from shopping_cart.permissions import FullDjangoModelPermissions, IsAdminOrReadOnly, ViewCustomerHistoryPermission
from shopping_cart.pagination import DefaultPagination
from django.db.models.aggregates import Count
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.decorators import action, permission_classes
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.mixins import CreateModelMixin, DestroyModelMixin, RetrieveModelMixin, UpdateModelMixin
from rest_framework.permissions import AllowAny, DjangoModelPermissions, DjangoModelPermissionsOrAnonReadOnly, IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, GenericViewSet
from rest_framework import status
from .filters import ProductFilter
from .models import Cart, CartItem, Collection, Customer, Order, OrderItem, Product, ProductImage, Review
from .serializers import AddCartItemSerializer, CartItemSerializer, CartSerializer, CollectionSerializer, CreateOrderSerializer, CustomerSerializer, OrderSerializer, ProductImageSerializer, ProductSerializer, ReviewSerializer, UpdateCartItemSerializer, UpdateOrderSerializer


class ProductViewSet(ModelViewSet):
    """
    # Create a new product
    POST /products/
    {
      "title": "New Product",
      "description": "A new product",
      "unit_price": 10.99,
      "inventory": 100,
      "collection": 1
    }
    # Response: 201 Created

    # Retrieve a product
    GET /products/1/
    # Response: 200 OK
    {
      "id": 1,
      "title": "New Product",
      "description": "A new product",
      "slug": "new-product",
      "inventory": 100,
      "unit_price": "10.99",
      "price_with_tax": "12.09",
      "collection": 1,
      "images": []
    }

    # Update a product
    PUT /products/1/
    {
      "title": "Updated Product",
      "description": "An updated product",
      "unit_price": 12.99,
      "inventory": 50,
      "collection": 2
    }
    # Response: 200 OK

    # Delete a product
    DELETE /products/1/
    # Response: 204 No Content
    """
    queryset = Product.objects.prefetch_related('images').all()
    serializer_class = ProductSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = ProductFilter
    pagination_class = DefaultPagination
    permission_classes = [IsAdminOrReadOnly]
    search_fields = ['title', 'description']
    ordering_fields = ['unit_price', 'last_update']

    def get_serializer_context(self):
        return {'request': self.request}

    def destroy(self, request, *args, **kwargs):
        if OrderItem.objects.filter(product_id=kwargs['pk']).count() > 0:
            return Response({'error': 'Product cannot be deleted because it is associated with an order item.'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

        return super().destroy(request, *args, **kwargs)


class CollectionViewSet(ModelViewSet):
    """
    Summary
    This code defines a CollectionViewSet class that is a subclass of ModelViewSet from the Django REST Framework. It provides CRUD (Create, Retrieve, Update, Delete) operations for the Collection model. The class also includes a custom destroy method to handle the deletion of a collection.
    Example Usage
    # Create a new collection
    POST /collections/
    Request Body:
    {
      "title": "New Collection",
      "featured_product": 1
    }
    Response:
    {
      "id": 1,
      "title": "New Collection",
      "products_count": 0
    }

    # Retrieve a collection
    GET /collections/1/
    Response:
    {
      "id": 1,
      "title": "New Collection",
      "products_count": 0
    }

    # Update a collection
    PUT /collections/1/
    Request Body:
    {
      "title": "Updated Collection",
      "featured_product": 2
    }
    Response:
    {
      "id": 1,
      "title": "Updated Collection",
      "products_count": 0
    }

    # Delete a collection
    DELETE /collections/1/
    Response:
    204 No Content

    """
    queryset = Collection.objects.annotate(
        products_count=Count('products')).all()
    serializer_class = CollectionSerializer
    permission_classes = [IsAdminOrReadOnly]

    def destroy(self, request, *args, **kwargs):
        if Product.objects.filter(collection_id=kwargs['pk']):
            return Response({'error': 'Collection cannot be deleted because it includes one or more products.'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

        return super().destroy(request, *args, **kwargs)


class ReviewViewSet(ModelViewSet):
    """
    Summary
    The ReviewViewSet class is a viewset that handles the CRUD operations for the Review model. It uses the ReviewSerializer to serialize and deserialize the review data.
    Example Usage
    # Create a new review for a specific product
    POST /products/{product_pk}/reviews/
    Request Body:
    {
      "name": "John Doe",
      "description": "This product is amazing!"
    }
    Response:
    {
      "id": 1,
      "date": "2022-01-01",
      "name": "John Doe",
      "description": "This product is amazing!"
    }

    # Retrieve all reviews for a specific product
    GET /products/{product_pk}/reviews/
    Response:
    [
      {
        "id": 1,
        "date": "2022-01-01",
        "name": "John Doe",
        "description": "This product is amazing!"
      },
      {
        "id": 2,
        "date": "2022-01-02",
        "name": "Jane Smith",
        "description": "Great product!"
      }
    ]

    # Retrieve a specific review for a specific product
    GET /products/{product_pk}/reviews/{review_pk}/
    Response:
    {
      "id": 1,
      "date": "2022-01-01",
      "name": "John Doe",
      "description": "This product is amazing!"
    }

    # Update a specific review for a specific product
    PUT /products/{product_pk}/reviews/{review_pk}/
    Request Body:
    {
      "name": "John Smith",
      "description": "This product is awesome!"
    }
    Response:
    {
      "id": 1,
      "date": "2022-01-01",
      "name": "John Smith",
      "description": "This product is awesome!"
    }

    # Delete a specific review for a specific product
    DELETE /products/{product_pk}/reviews/{review_pk}/
    Response:
    HTTP 204 No Content

    """
    serializer_class = ReviewSerializer

    def get_queryset(self):
        return Review.objects.filter(product_id=self.kwargs['product_pk'])

    def get_serializer_context(self):
        return {'product_id': self.kwargs['product_pk']}


class CartViewSet(CreateModelMixin,
                  RetrieveModelMixin,
                  DestroyModelMixin,
                  GenericViewSet):
    """
    Summary
    The CartViewSet class is a viewset that provides CRUD operations for the Cart model. It uses the CreateModelMixin, RetrieveModelMixin, and DestroyModelMixin mixins to handle the corresponding operations. The viewset is associated with the CartSerializer serializer, which defines the serialization and deserialization logic for the Cart model.
    Example Usage
    # Create a new cart
    POST /carts/
    Request Body:
    {
      "items": [
        {
          "product": 1,
          "quantity": 2
        },
        {
          "product": 2,
          "quantity": 3
        }
      ]
    }
    Response Body:
    {
      "id": "e3f4a4e7-0e3d-4e1d-9e6b-7e7e7e7e7e7e",
      "items": [
        {
          "id": 1,
          "product": 1,
          "quantity": 2
        },
        {
          "id": 2,
          "product": 2,
          "quantity": 3
        }
      ],
      "total_price": 15.0
    }

    # Retrieve a cart
    GET /carts/e3f4a4e7-0e3d-4e1d-9e6b-7e7e7e7e7e7e
    Response Body:
    {
      "id": "e3f4a4e7-0e3d-4e1d-9e6b-7e7e7e7e7e7e",
      "items": [
        {
          "id": 1,
          "product": 1,
          "quantity": 2
        },
        {
          "id": 2,
          "product": 2,
          "quantity": 3
        }
      ],
      "total_price": 15.0
    }

    # Delete a cart
    DELETE /carts/e3f4a4e7-0e3d-4e1d-9e6b-7e7e7e7e7e7e

    """
    queryset = Cart.objects.prefetch_related('items__product').all()
    serializer_class = CartSerializer


class CartItemViewSet(ModelViewSet):
    """
    The CartItemViewSet class is a viewset that handles CRUD operations for the CartItem model.
    It determines the appropriate serializer class based on the HTTP method used in the request.
    Example Usage
    # Create a new cart item
    POST /carts/{cart_pk}/items/
    Request Body:
    {
      "product_id": 1,
      "quantity": 2
    }
    Response Body:
    {
      "id": 1,
      "product": {
        "id": 1,Summary
The CustomerViewSet class is a viewset that provides CRUD operations for the Customer model. It includes methods for retrieving customer history and updating the current customer's information.
Example Usage
# Retrieve a list of all customers
GET /customers/

# Retrieve a specific customer
GET /customers/{customer_id}/

# Update the current customer's information
PUT /customers/me/

# Retrieve the current customer's information
GET /customers/me/

# Retrieve the history of a specific customer
GET /customers/{customer_id}/history/
        "name": "Product 1",
        "unit_price": 10.0
      },
      "quantity": 2,
      "total_price": 20.0
    }

    # Update a cart item
    PATCH /carts/{cart_pk}/items/{item_pk}/
    Request Body:
    {
      "quantity": 3
    }
    Response Body:
    {
      "id": 1,
      "product": {
        "id": 1,
        "name": "Product 1",
        "unit_price": 10.0
      },
      "quantity": 3,
      "total_price": 30.0
    }

    # Delete a cart item
    DELETE /carts/{cart_pk}/items/{item_pk}/
    """
    http_method_names = ['get', 'post', 'patch', 'delete']

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return AddCartItemSerializer
        elif self.request.method == 'PATCH':
            return UpdateCartItemSerializer
        return CartItemSerializer

    def get_serializer_context(self):
        return {'cart_id': self.kwargs['cart_pk']}

    def get_queryset(self):
        return CartItem.objects \
            .filter(cart_id=self.kwargs['cart_pk']) \
            .select_related('product')


class CustomerViewSet(ModelViewSet):
    """
    Summary
    The CustomerViewSet class is a viewset that provides CRUD operations for the Customer model. It includes methods for retrieving customer history and updating the current customer's information.
    Example Usage
    # Retrieve a list of all customers
    GET /customers/

    # Retrieve a specific customer
    GET /customers/{customer_id}/

    # Update the current customer's information
    PUT /customers/me/

    # Retrieve the current customer's information
    GET /customers/me/

    # Retrieve the history of a specific customer
    GET /customers/{customer_id}/history/
    """
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    permission_classes = [IsAdminUser]

    @action(detail=True, permission_classes=[ViewCustomerHistoryPermission])
    def history(self, request, pk):
        return Response('ok')

    @action(detail=False, methods=['GET', 'PUT'], permission_classes=[IsAuthenticated])
    def me(self, request):
        customer = Customer.objects.get(
            user_id=request.user.id)
        if request.method == 'GET':
            serializer = CustomerSerializer(customer)
            return Response(serializer.data)
        elif request.method == 'PUT':
            serializer = CustomerSerializer(customer, data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)


class OrderViewSet(ModelViewSet):
    """
    This code defines a OrderViewSet class that is a subclass of ModelViewSet from the Django REST Framework.
    It handles the CRUD operations for the Order model and provides different serializers based on the request method.
    Example Usage
    # Create a new order
    POST /orders/
    {
      "cart_id": "12345678-1234-5678-1234-567812345678"
    }
    # Response:
    {
      "id": 1,
      "customer": 1,
      "placed_at": "2022-01-01T12:00:00Z",
      "payment_status": "P",
      "items": [
        {
          "id": 1,
          "order": 1,
          "product": 1,
          "unit_price": 10.0,
          "quantity": 2
        },
        {
          "id": 2,
          "order": 1,
          "product": 2,
          "unit_price": 5.0,
          "quantity": 3
        }
      ]
    }

    # Update an existing order
    PATCH /orders/1/
    {
      "payment_status": "C"
    }
    # Response:
    {
      "id": 1,
      "customer": 1,
      "placed_at": "2022-01-01T12:00:00Z",
      "payment_status": "C",
      "items": [
        {
          "id": 1,
          "order": 1,
          "product": 1,
          "unit_price": 10.0,
          "quantity": 2
        },
        {
          "id": 2,
          "order": 1,
          "product": 2,
          "unit_price": 5.0,
          "quantity": 3
        }
      ]
    }

    # Delete an existing order
    DELETE /orders/1/
    # Response: 204 No Content
    """
    http_method_names = ['get', 'post', 'patch', 'delete', 'head', 'options']

    def get_permissions(self):
        if self.request.method in ['PATCH', 'DELETE']:
            return [IsAdminUser()]
        return [IsAuthenticated()]

    def create(self, request, *args, **kwargs):
        serializer = CreateOrderSerializer(
            data=request.data,
            context={'user_id': self.request.user.id})
        serializer.is_valid(raise_exception=True)
        order = serializer.save()
        serializer = OrderSerializer(order)
        return Response(serializer.data)

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CreateOrderSerializer
        elif self.request.method == 'PATCH':
            return UpdateOrderSerializer
        return OrderSerializer

    def get_queryset(self):
        user = self.request.user

        if user.is_staff:
            return Order.objects.all()

        customer_id = Customer.objects.only(
            'id').get(user_id=user.id)
        return Order.objects.filter(customer_id=customer_id)


class ProductImageViewSet(ModelViewSet):
    """
    The ProductImageViewSet class is a viewset that handles the CRUD operations for the ProductImage model. It uses the ProductImageSerializer serializer to serialize and deserialize the data.
    Example Usage
    # Create a new product image
    POST /products/{product_pk}/images/
    Request Body:
    {
      "image": "image.jpg"
    }
    Response:
    {
      "id": 1,
      "image": "image.jpg"
    }

    # Retrieve all product images for a specific product
    GET /products/{product_pk}/images/
    Response:
    [
      {
        "id": 1,
        "image": "image1.jpg"
      },
      {
        "id": 2,
        "image": "image2.jpg"
      }
    ]

    # Retrieve a specific product image
    GET /products/{product_pk}/images/{image_pk}/
    Response:
    {
      "id": 1,
      "image": "image.jpg"
    }

    # Update a specific product image
    PUT /products/{product_pk}/images/{image_pk}/
    Request Body:
    {
      "image": "new_image.jpg"
    }
    Response:
    {
      "id": 1,
      "image": "new_image.jpg"
    }

    # Delete a specific product image
    DELETE /products/{product_pk}/images/{image_pk}/
    Response:
    HTTP 204 No Content
    """
    serializer_class = ProductImageSerializer

    def get_serializer_context(self):
        return {'product_id': self.kwargs['product_pk']}

    def get_queryset(self):
        return ProductImage.objects.filter(product_id=self.kwargs['product_pk'])
