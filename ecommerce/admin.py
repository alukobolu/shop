from django.contrib import admin
from .models import Product, Order, OrderItem, Review

# Basic admin registration
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'category', 'stock_count')
    list_filter = ('category',)
    search_fields = ('name', 'description')

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'status', 'total_amount', 'created_at')
    list_filter = ('status',)
    search_fields = ('user__username',)
    inlines = [OrderItemInline]

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('product', 'user', 'rating', 'date')
    list_filter = ('rating',)
    search_fields = ('product__name', 'user__username')

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'product', 'quantity', 'price')
    search_fields = ('order__id', 'product__name')

"""
# Commented out custom admin code
class StockFilter(admin.SimpleListFilter):
    title = 'stock status'
    parameter_name = 'stock_status'

    def lookups(self, request, model_admin):
        return (
            ('in_stock', 'In Stock'),
            ('out_of_stock', 'Out of Stock'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'in_stock':
            return queryset.filter(stock_count__gt=0)
        if self.value() == 'out_of_stock':
            return queryset.filter(stock_count=0)

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'category', 'stock_count', 'in_stock', 'display_thumbnail', 'total_orders', 'average_rating')
    list_filter = ('category', 'created_at')
    search_fields = ('name', 'description')
    readonly_fields = ('created_at',)
    list_per_page = 20
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'price', 'category')
        }),
        ('Stock Information', {
            'fields': ('stock_count',)
        }),
        ('Media', {
            'fields': ('thumbnail', 'images')
        }),
        ('Additional Information', {
            'fields': ('specifications', 'created_at'),
            'classes': ('collapse',)
        }),
    )

    def display_thumbnail(self, obj):
        if obj.thumbnail:
            return format_html('<img src="{}" width="50" height="50" />', obj.thumbnail)
        return "No image"
    display_thumbnail.short_description = 'Thumbnail'

    def total_orders(self, obj):
        return OrderItem.objects.filter(product=obj).aggregate(Sum('quantity'))['quantity__sum'] or 0
    total_orders.short_description = 'Total Orders'

    def average_rating(self, obj):
        avg = obj.reviews.aggregate(Avg('rating'))['rating__avg']
        return round(avg, 2) if avg else 'No ratings'
    average_rating.short_description = 'Avg Rating'

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    readonly_fields = ('price',)
    extra = 0
    raw_id_fields = ('product',)

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'status', 'total_amount', 'created_at', 'display_items_count')
    list_filter = ('status', 'created_at')
    search_fields = ('user__username', 'user__email', 'tracking_number')
    readonly_fields = ('created_at', 'total_amount')
    inlines = [OrderItemInline]
    list_per_page = 20

    fieldsets = (
        ('Order Information', {
            'fields': ('user', 'status', 'total_amount', 'created_at')
        }),
        ('Shipping Details', {
            'fields': ('shipping_address', 'tracking_number', 'carrier', 'estimated_delivery')
        }),
        ('Payment Information', {
            'fields': ('payment_method_id',),
            'classes': ('collapse',)
        }),
    )

    def display_items_count(self, obj):
        return obj.items.count()
    display_items_count.short_description = 'Number of Items'

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('items', 'user')

    def save_model(self, request, obj, form, change):
        if not change:
            obj.total_amount = sum(item.price * item.quantity for item in obj.items.all())
        super().save_model(request, obj, form, change)

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('product', 'user', 'rating', 'date', 'short_comment')
    list_filter = ('rating', 'date')
    search_fields = ('product__name', 'user__username', 'comment')
    readonly_fields = ('date',)
    raw_id_fields = ('product', 'user')
    list_per_page = 20

    def short_comment(self, obj):
        return obj.comment[:50] + '...' if len(obj.comment) > 50 else obj.comment
    short_comment.short_description = 'Comment'

# Custom admin site configuration
admin.site.site_header = 'E-Commerce Administration'
admin.site.site_title = 'E-Commerce Admin Portal'
admin.site.index_title = 'Welcome to E-Commerce Admin Portal'

# Custom admin dashboard
from django.core.cache import cache
from django.db.models import Sum, Count
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render
from django.utils import timezone
from datetime import timedelta

@staff_member_required
def admin_dashboard(request):
    # Cache the dashboard data for 10 minutes
    cache_key = 'admin_dashboard_data'
    dashboard_data = cache.get(cache_key)

    if not dashboard_data:
        # Calculate statistics
        today = timezone.now()
        thirty_days_ago = today - timedelta(days=30)

        dashboard_data = {
            'total_orders': Order.objects.count(),
            'recent_orders': Order.objects.filter(created_at__gte=thirty_days_ago).count(),
            'total_products': Product.objects.count(),
            'out_of_stock': Product.objects.filter(stock_count=0).count(),
            'total_revenue': Order.objects.filter(status='delivered').aggregate(Sum('total_amount'))['total_amount__sum'] or 0,
            'recent_revenue': Order.objects.filter(
                status='delivered',
                created_at__gte=thirty_days_ago
            ).aggregate(Sum('total_amount'))['total_amount__sum'] or 0,
            'top_products': Product.objects.annotate(
                order_count=Count('orderitem')
            ).order_by('-order_count')[:5],
        }

        cache.set(cache_key, dashboard_data, 600)  # Cache for 10 minutes

    return render(request, 'admin/dashboard.html', dashboard_data)
"""