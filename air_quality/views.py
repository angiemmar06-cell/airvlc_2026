from django.http import JsonResponse
from .models import Station

# Create your views here.
def stations_geojson(request):
    stations = Station.objects.filter(measurements__isnull=False).distinct().order_by('name')
    data = []
    #measurements_isnull=False --> trae solo las estaciones que tienen mediciones asociadas, evitando estaciones sin datos
    
    for station in stations:
        data.append({
            "name": station.name,
            "lat": station.location.y,
            "lng": station.location.x,
        })
        #station.location.x --> coordenada de longitud (lng) = x
        #station.location.y --> coordenada de latitud (lat) = y
    return JsonResponse(data, safe=False) #devuelve una lista JSON

def measurements_geojson(request):
    measurements = measurement.objects.filter(station__isnull=False).order_by('timestamp')
    data = []
    
    for measurement in measurements:
        data.append({
            "station": measurement.station.name,
            "timestamp": measurement.timestamp,
            "value": measurement.value,
        })

    return JsonResponse(data, safe=False) #devuelve una lista JSON
