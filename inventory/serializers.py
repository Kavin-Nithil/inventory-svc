from rest_framework import serializers
from .models import Inventory, Reservation, Product, Warehouse

class ReserveSerializer(serializers.Serializer):
    product_sku = serializers.CharField(max_length=50)
    warehouse_code = serializers.CharField(max_length=10)
    quantity = serializers.IntegerField(min_value=1)
    order_id = serializers.CharField(max_length=100, required=False, allow_blank=True)
    timeout_minutes = serializers.IntegerField(min_value=1, max_value=1440, required=False)

class ReleaseSerializer(serializers.Serializer):
    reservation_id = serializers.CharField(max_length=100)

class AvailabilitySerializer(serializers.Serializer):
    product_sku = serializers.CharField(max_length=50)
    warehouse_code = serializers.CharField(max_length=10, required=False, allow_blank=True)

class InventoryResponseSerializer(serializers.Serializer):
    product_sku = serializers.CharField()
    warehouse_code = serializers.CharField()
    on_hand = serializers.IntegerField()
    reserved = serializers.IntegerField()
    available = serializers.IntegerField()