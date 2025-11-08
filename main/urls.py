"""
URL configuration for main project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path
from inventory.views import ReserveView, ReleaseView, AvailabilityView, HealthView

urlpatterns = [
    path('v1/inventory/reserve', ReserveView.as_view()),
    path('v1/inventory/release', ReleaseView.as_view()),
    path('v1/inventory/availability', AvailabilityView.as_view()),
    path('health', HealthView.as_view()),
]