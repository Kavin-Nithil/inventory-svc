#!/bin/sh
echo "Waiting for RabbitMQ..."
until nc -z rabbitmq 5672; do
  sleep 2
done
echo "RabbitMQ is up!"
exec "$@"