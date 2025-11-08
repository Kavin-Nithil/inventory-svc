from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import ObjectDoesNotExist
from .serializers import (
    ReserveSerializer, ReleaseSerializer,
    AvailabilitySerializer, InventoryResponseSerializer
)
from .services import InventoryService


class ReserveView(APIView):
    def post(self, request):
        serializer = ReserveSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            result = InventoryService.reserve_inventory(**serializer.validated_data)
            return Response(result, status=status.HTTP_201_CREATED)
        except ObjectDoesNotExist:
            return Response(
                {'error': 'Product or warehouse not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response(
                {'error': 'Internal server error'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ReleaseView(APIView):
    def post(self, request):
        serializer = ReleaseSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            result = InventoryService.release_inventory(
                serializer.validated_data['reservation_id']
            )
            return Response(result, status=status.HTTP_200_OK)
        except ObjectDoesNotExist:
            return Response(
                {'error': 'Reservation not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response(
                {'error': 'Internal server error'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class AvailabilityView(APIView):
    def get(self, request):
        serializer = AvailabilitySerializer(data=request.query_params)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            results = InventoryService.get_availability(**serializer.validated_data)
            return Response(results, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {'error': 'Internal server error'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class HealthView(APIView):
    def get(self, request):
        return Response({'status': 'healthy'}, status=status.HTTP_200_OK)