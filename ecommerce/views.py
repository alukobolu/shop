from rest_framework import viewsets, status, filters
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from .models import Product, Order, OrderItem
from .serializers import (
    ProductSummarySerializer, ProductDetailSerializer,
    OrderCreateSerializer, OrderStatusSerializer
)
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from django.shortcuts import render
from django.db import models
from django.db.models import Sum, Count
from django.views.decorators.http import require_http_methods
from django.urls import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import redirect

class ProductPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'limit'
    max_page_size = 100

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    pagination_class = ProductPagination
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['name', 'price', 'created_at']
    ordering = ['-created_at']  # Default ordering
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ProductDetailSerializer
        return ProductSummarySerializer
    
    def list(self, request):
        queryset = self.get_queryset()
        category = request.query_params.get('category')
        search = request.query_params.get('search')
        
        if category:
            queryset = queryset.filter(category=category)
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | Q(description__icontains=search)
            )
            
        # Apply ordering
        ordering = request.query_params.get('ordering', '-created_at')
        if ordering:
            queryset = queryset.order_by(ordering)
            
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    def retrieve(self, request, pk=None):
        try:
            product = self.get_object()
            serializer = self.get_serializer(product)
            return Response(serializer.data)
        except Product.DoesNotExist:
            return Response(
                {'error': 'Product not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=False, methods=['get'])
    def search(self, request):
        query = request.query_params.get('q', '')
        category = request.query_params.get('category')
        min_price = request.query_params.get('min_price')
        max_price = request.query_params.get('max_price')
        
        queryset = self.get_queryset()
        
        if query:
            queryset = queryset.filter(
                Q(name__icontains=query) |
                Q(description__icontains=query) |
                Q(category__icontains=query) |
                Q(specifications__icontains=query)
            )
        
        if category:
            queryset = queryset.filter(category=category)
            
        if min_price:
            queryset = queryset.filter(price__gte=float(min_price))
            
        if max_price:
            queryset = queryset.filter(price__lte=float(max_price))
            
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
            
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def bulk_create(self, request):
        products_data = request.data
        if not isinstance(products_data, list):
            return Response(
                {'error': 'Expected a list of products'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        created_products = []
        try:
            for product_data in products_data:
                serializer = ProductDetailSerializer(data=product_data)
                serializer.is_valid(raise_exception=True)
                product = serializer.save()
                created_products.append(product)

            return Response(
                ProductSummarySerializer(created_products, many=True).data,
                status=status.HTTP_201_CREATED
            )
        except Exception as e:
            # Rollback any created products if there's an error
            for product in created_products:
                product.delete()
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

class OrderViewSet(viewsets.ModelViewSet):
    permission_classes = []
    
    def get_serializer_class(self):
        if self.action == 'create':
            return OrderCreateSerializer
        return OrderStatusSerializer
    
    def get_queryset(self):
        user_id = self.request.query_params.get('user_id')
        queryset = Order.objects.all()
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        return queryset
    
    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = get_object_or_404(User, id=1)
        
        try:
            order = Order.objects.create(
                user=user 
            )
            if request.data.get('shipping_address'):
                order.shipping_address = request.data.get('shipping_address')
                order.save()
            
            total_amount = 0
            products_data = serializer.validated_data.get('products', [])
            
            if not products_data:
                order.delete()
                return Response(
                    {'error': 'At least one product is required'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            for item in products_data:
                product = get_object_or_404(Product, id=item['product_id'])
                quantity = item['quantity']
                
                if product.stock_count < quantity:
                    order.delete()
                    return Response(
                        {
                            'error': f'Insufficient stock for product {product.name}. '
                                    f'Available: {product.stock_count}'
                        }, 
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                price = product.price * quantity
                total_amount += price
                
                OrderItem.objects.create(
                    order=order,
                    product=product,
                    quantity=quantity,
                    price=price
                )
                
                product.stock_count -= quantity
                product.save()
            
            order.total_amount = total_amount
            order.save()
            
            return Response({
                'order_id': order.id,
                'status': order.status,
                "response": "Make Payment at https://shop-production-b7d8.up.railway.app/api/order/" + str(order.id)
                # 'estimated_delivery': order.estimated_delivery,
                # 'tracking_number': order.tracking_number
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            if 'order' in locals():
                order.delete()
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )
    
    def retrieve(self, request, pk=None):
        try:
            order = self.get_object()
            serializer = self.get_serializer(order)
            return Response(serializer.data)
        except Order.DoesNotExist:
            return Response(
                {'error': 'Order not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )

def dashboard_view(request):
    total_orders = Order.objects.count()
    recent_orders = Order.objects.filter(created_at__gte='2023-09-01').count()  # Example date
    total_products = Product.objects.count()
    out_of_stock = Product.objects.filter(stock_count=0).count()
    total_revenue = Order.objects.aggregate(total=Sum('total_amount'))['total'] or 0
    recent_revenue = Order.objects.filter(created_at__gte='2023-09-01').aggregate(total=Sum('total_amount'))['total'] or 0
    
    # Fetch the most recent orders
    recent_orders_list = Order.objects.order_by('-created_at')[:5]  # Adjust the number as needed

    context = {
        'total_orders': total_orders,
        'recent_orders': recent_orders,
        'total_products': total_products,
        'out_of_stock': out_of_stock,
        'total_revenue': total_revenue,
        'recent_revenue': recent_revenue,
        'recent_orders_list': recent_orders_list,  # Pass the recent orders to the context
    }
    
    return render(request, 'admin/dashboard.html', context)

@require_http_methods(["GET", "POST"])
def single_order_view(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    if request.method == "POST":
        # Handle payment logic here
        return redirect('dashboard')  # Redirect to a success page after payment

    context = {
        'order': order,
        'payment_link': f"http://127.0.0.1:8001/pay/{order_id}"  # Example payment link
    }
    return render(request, 'admin/single_order.html', context)
