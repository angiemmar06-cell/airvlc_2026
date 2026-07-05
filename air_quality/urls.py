from django.urls import path
from .views import measurements_geojson, meta, stations_geojson

urlpatterns = [
    path('stations/', stations_geojson, name='stations_geojson'),
    path('measurements/', measurements_geojson, name='measurements_geojson'),
    path('meta/', meta, name='meta'),
]
