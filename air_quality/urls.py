from django.urls import path
from .views import stations_geojson

urlpatterns = [
    path('stations/', stations_geojson, name='stations_geojson'),
]
