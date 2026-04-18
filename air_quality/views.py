from django.http import JsonResponse
from .models import Measurement, Station

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
    measurements = Measurement.objects.filter(station__isnull=False).order_by('measured_at')
    data = []
    
    for measurement in measurements [:1000]: #limita a las primeras 1000 mediciones para evitar sobrecargar la respuesta
        data.append({
            "station": measurement.station.name,
            "measured_at": measurement.measured_at.isoformat() if measurement.measured_at else None, #para convertir la fecha a formato ISO 8601, que es un formato estándar para fechas en JSON
            "no2": measurement.no2,
            "pm10": measurement.pm10,
            "pm2_5": measurement.pm25,
            "o3": measurement.o3,
            "so2": measurement.so2,
            "co": measurement.co,
            "no": measurement.no            
        })

    return JsonResponse(data, safe=False) #devuelve una lista JSON
