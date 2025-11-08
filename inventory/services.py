import uuid
import pika
import json
import logging
from django.db import transaction
from django.utils import timezone
from django.conf import settings
from datetime import timedelta
from .models import Inventory, Reservation, Product, Warehouse

logger = logging.getLogger(__name__)


class RabbitMQPublisher:
    @staticmethod
    def publish(event_type, data):
        try:
            credentials = pika.PlainCredentials(
                settings.RABBITMQ_USER,
                settings.RABBITMQ_PASSWORD
            )
            connection = pika.BlockingConnection(
                pika.ConnectionParameters(
                    host=settings.RABBITMQ_HOST,
                    port=settings.RABBITMQ_PORT,
                    credentials=credentials
                )
            )
            channel = connection.channel()
            channel.queue_declare(queue=event_type, durable=True)

            message = json.dumps(data)
            channel.basic_publish(
                exchange='',
                routing_key=event_type,
                body=message,
                properties=pika.BasicProperties(delivery_mode=2)
            )
            connection.close()
            logger.info(f"Published {event_type}: {message}")
        except Exception as e:
            logger.error(f"Failed to publish event {event_type}: {str(e)}")


class InventoryService:
    @staticmethod
    @transaction.atomic
    def reserve_inventory(product_sku, warehouse_code, quantity, order_id='', timeout_minutes=None):
        timeout = timeout_minutes or settings.RESERVATION_TIMEOUT_MINUTES

        # Lock inventory row
        inventory = Inventory.objects.select_for_update().select_related(
            'product', 'warehouse'
        ).get(
            product__sku=product_sku,
            warehouse__code=warehouse_code
        )

        available = inventory.on_hand - inventory.reserved
        if available < quantity:
            raise ValueError(f"Insufficient inventory. Available: {available}, Requested: {quantity}")

        # Create reservation
        reservation_id = str(uuid.uuid4())
        expires_at = timezone.now() + timedelta(minutes=timeout)

        reservation = Reservation.objects.create(
            reservation_id=reservation_id,
            inventory=inventory,
            quantity=quantity,
            order_id=order_id,
            expires_at=expires_at,
            status='active'
        )

        # Update reserved count
        inventory.reserved += quantity
        inventory.save()

        # Publish event
        RabbitMQPublisher.publish('inventory.reserved', {
            'reservation_id': reservation_id,
            'product_sku': product_sku,
            'warehouse_code': warehouse_code,
            'quantity': quantity,
            'order_id': order_id,
            'expires_at': expires_at.isoformat()
        })

        # Check low stock
        if inventory.available <= settings.LOW_STOCK_THRESHOLD:
            RabbitMQPublisher.publish('inventory.low_stock', {
                'product_sku': product_sku,
                'warehouse_code': warehouse_code,
                'available': inventory.available,
                'on_hand': inventory.on_hand,
                'reserved': inventory.reserved
            })

        return {
            'reservation_id': reservation_id,
            'expires_at': expires_at.isoformat(),
            'quantity': quantity
        }

    @staticmethod
    @transaction.atomic
    def release_inventory(reservation_id):
        reservation = Reservation.objects.select_for_update().select_related(
            'inventory', 'inventory__product', 'inventory__warehouse'
        ).get(reservation_id=reservation_id)

        if reservation.status != 'active':
            raise ValueError(f"Reservation {reservation_id} is not active (status: {reservation.status})")

        # Lock inventory
        inventory = Inventory.objects.select_for_update().get(id=reservation.inventory.id)

        # Release reservation
        inventory.reserved -= reservation.quantity
        inventory.save()

        reservation.status = 'released'
        reservation.released_at = timezone.now()
        reservation.save()

        # Publish event
        RabbitMQPublisher.publish('inventory.released', {
            'reservation_id': reservation_id,
            'product_sku': inventory.product.sku,
            'warehouse_code': inventory.warehouse.code,
            'quantity': reservation.quantity
        })

        return {
            'reservation_id': reservation_id,
            'released_at': reservation.released_at.isoformat()
        }

    @staticmethod
    def get_availability(product_sku, warehouse_code=None):
        query = Inventory.objects.select_related('product', 'warehouse').filter(
            product__sku=product_sku
        )

        if warehouse_code:
            query = query.filter(warehouse__code=warehouse_code)

        results = []
        for inv in query:
            results.append({
                'product_sku': inv.product.sku,
                'warehouse_code': inv.warehouse.code,
                'on_hand': inv.on_hand,
                'reserved': inv.reserved,
                'available': inv.available
            })

        return results

    @staticmethod
    @transaction.atomic
    def reap_expired_reservations():
        expired = Reservation.objects.select_for_update().filter(
            status='active',
            expires_at__lt=timezone.now()
        ).select_related('inventory', 'inventory__product', 'inventory__warehouse')

        count = 0
        for reservation in expired:
            inventory = Inventory.objects.select_for_update().get(id=reservation.inventory.id)
            inventory.reserved -= reservation.quantity
            inventory.save()

            reservation.status = 'expired'
            reservation.released_at = timezone.now()
            reservation.save()

            RabbitMQPublisher.publish('inventory.released', {
                'reservation_id': reservation.reservation_id,
                'product_sku': inventory.product.sku,
                'warehouse_code': inventory.warehouse.code,
                'quantity': reservation.quantity,
                'reason': 'expired'
            })
            count += 1

        return count
