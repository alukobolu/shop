from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator

class Product(models.Model):
    CATEGORY_CHOICES = [
        ('food', 'Food'),
        ('arts_crafts', 'Arts'),
        ('automotive', 'Automotive'),
        ('baby', 'Baby'),
        ('beauty', 'Beauty'),
        ('books', 'Books'),
        ('computers', 'Computers'),
        ('electronics', 'Electronics'),
        ('fashion', "Men & Women Fashion"),
        ('health', 'Health'),
        ('home_kitchen', 'Kitchen'),
        ('industrial', 'Industrial'),
        ('kids_fashion', "Kids Fashion"),
        ('movies_tv', 'Movies'),
        ('music', 'Music'),
        ('office', 'Office'),
        ('pet_supplies', 'Pet'),
        ('sports_outdoors', 'Outdoors'),
        ('tools_home', 'Tools'),
        ('toys_games', 'Toys'),
        ('video_games', 'Games'),
        ('clothing', 'Clothing'),
        ('home', 'Home'),
        ('sports', 'Sports'),
        ('sneakers', 'Sneakers'),
    ]
    
    name = models.CharField(max_length=200)
    description = models.TextField(null=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, null=True, blank=True)
    thumbnail = models.URLField(null=True, blank=True)
    stock_count = models.IntegerField(default=0)
    specifications = models.JSONField(default=dict, null=True, blank=True)
    images = models.JSONField(default=list, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def in_stock(self):
        return self.stock_count > 0

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['-created_at']

class Review(models.Model):
    product = models.ForeignKey(Product, related_name='reviews', on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    comment = models.TextField(null=True, blank=True)
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Review for {self.product.name} by {self.user.username}"

class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='pending'
    )
    total_amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True
    )
    shipping_address = models.JSONField(null=True, blank=True)
    payment_method_id = models.CharField(max_length=100, null=True, blank=True)
    tracking_number = models.CharField(max_length=100, null=True, blank=True)
    carrier = models.CharField(max_length=100, null=True, blank=True)
    estimated_delivery = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Order {self.id} by {self.user.username if self.user else 'Unknown'}"

class OrderItem(models.Model):
    order = models.ForeignKey(
        Order, 
        related_name='items', 
        on_delete=models.CASCADE
    )
    product = models.ForeignKey(
        Product, 
        on_delete=models.SET_NULL, 
        null=True
    )
    quantity = models.IntegerField(
        validators=[MinValueValidator(1)],
        default=1
    )
    price = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.quantity}x {self.product.name if self.product else 'Unknown Product'}"

    class Meta:
        ordering = ['-created_at']
