from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import ProductViewSet, OrderViewSet, dashboard_view, single_order_view

# Option 1: Using Router (Recommended)
router = DefaultRouter()
router.register(r'products', ProductViewSet, basename='product')
router.register(r'orders', OrderViewSet, basename='order')

urlpatterns = [
    path('admin/dashboard/', dashboard_view, name='dashboard'),
    path('order/<int:order_id>/', single_order_view, name='single_order'),
] + router.urls

# Option 2: Manual URL mapping
"""
urlpatterns = [
    path('api/products/', ProductViewSet.as_view({
        'get': 'list',
        'post': 'create'
    }), name='product-list'),
    
    path('api/products/<int:pk>/', ProductViewSet.as_view({
        'get': 'retrieve',
        'put': 'update',
        'patch': 'partial_update',
        'delete': 'destroy'
    }), name='product-detail'),
    
    path('api/orders/', OrderViewSet.as_view({
        'get': 'list',
        'post': 'create'
    }), name='order-list'),
    
    path('api/orders/<int:pk>/', OrderViewSet.as_view({
        'get': 'retrieve'
    }), name='order-detail'),
    
    path('api/products/bulk_create/', ProductViewSet.as_view({
        'post': 'bulk_create'
    }), name='product-bulk-create'),
]
""" 