from django.db import models
from django.utils import timezone
from datetime import timedelta


class Warehouse(models.Model):
    code = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=100)
    location = models.CharField(max_length=200, blank=True)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'warehouses'

    def __str__(self):
        return f"{self.code} - {self.name}"


class Product(models.Model):
    sku = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'products'

    def __str__(self):
        return f"{self.sku} - {self.name}"


class Inventory(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='inventories')
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name='inventories')
    on_hand = models.IntegerField(default=0)
    reserved = models.IntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'inventory'
        unique_together = [['product', 'warehouse']]
        indexes = [
            models.Index(fields=['product', 'warehouse']),
            models.Index(fields=['updated_at']),
        ]

    @property
    def available(self):
        return max(0, self.on_hand - self.reserved)

    def __str__(self):
        return f"{self.product.sku} @ {self.warehouse.code}: {self.available} avail"


class Reservation(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('released', 'Released'),
        ('expired', 'Expired'),
    ]

    reservation_id = models.CharField(max_length=100, unique=True, db_index=True)
    inventory = models.ForeignKey(Inventory, on_delete=models.CASCADE, related_name='reservations')
    quantity = models.IntegerField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    order_id = models.CharField(max_length=100, blank=True)
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    released_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'reservations'
        indexes = [
            models.Index(fields=['status', 'expires_at']),
            models.Index(fields=['reservation_id']),
        ]

    def is_expired(self):
        return timezone.now() > self.expires_at and self.status == 'active'

    def __str__(self):
        return f"Reservation {self.reservation_id}: {self.quantity} units"