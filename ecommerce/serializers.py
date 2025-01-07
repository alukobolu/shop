from rest_framework import serializers
from .models import Product, Order, OrderItem, Review

class ProductSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'name', 'price', 'category', 'thumbnail', 'in_stock', 'stock_count']

class ReviewSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField()
    
    class Meta:
        model = Review
        fields = ['user', 'rating', 'comment', 'date']

class ProductDetailSerializer(serializers.ModelSerializer):
    reviews = ReviewSerializer(many=True, read_only=True)
    rating = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = ['id', 'name', 'description', 'price', 'category', 
                 'specifications', 'images', 'stock_count', 'rating', 'reviews']
    
    def get_rating(self, obj):
        reviews = obj.reviews.all()
        if not reviews:
            return 0
        return sum(review.rating for review in reviews) / len(reviews)

class OrderItemSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='product.name', read_only=True)
    
    class Meta:
        model = OrderItem
        fields = ['product_id', 'name', 'quantity', 'price']

class OrderCreateSerializer(serializers.ModelSerializer):
    products = serializers.ListField(child=serializers.DictField())
    
    class Meta:
        model = Order
        fields = ['products']

class OrderStatusSerializer(serializers.ModelSerializer):
    tracking_info = serializers.SerializerMethodField()
    order_details = serializers.SerializerMethodField()
    
    class Meta:
        model = Order
        fields = ['order_id', 'status', 'tracking_info', 'order_details']
    
    def get_tracking_info(self, obj):
        return {
            'carrier': obj.carrier,
            'tracking_number': obj.tracking_number,
            'tracking_url': f'https://tracking.example.com/{obj.tracking_number}',
            'current_location': 'In Transit',  # You would implement actual tracking logic
            'estimated_delivery': obj.estimated_delivery
        }
    
    def get_order_details(self, obj):
        return {
            'products': OrderItemSerializer(obj.items.all(), many=True).data,
            'total_amount': obj.total_amount,
            'shipping_address': obj.shipping_address,
            'order_date': obj.created_at
        }