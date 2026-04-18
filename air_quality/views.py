from django.http import JsonResponse
from .models import Measurement, Station

#filtro que solo permite mostrar los contaminantes que se encuentran en la lista ALLOWED_POLLUTANTS, evitando mostrar otros campos que puedan existir en el modelo Measurement pero que no son relevantes para la API. Esto ayuda a mantener la respuesta de la API más limpia y enfocada en los datos de interés.
ALLOWED_POLLUTANTS = ['no2', 'pm10', 'pm2_5', 'o3', 'so2', 'co', 'no', 'nox', 'nh3', 'c7h8', 'c6h6', 'c8h10', 'as_ng_m3', 'ni_ng_m3', 'cd_ng_m3', 'pb_ng_m3', 'b_a_p_ng_m3', 'wind_speed', 'wind_direction', 'max_wind_speed', 'temperature', 'relative_humidity', 'pressure', 'solar_radiation', 'precipitation', 'noise']

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
    #1. Leer los parametros de consulta
    station_name = request.GET.get("station", "").strip() #strip() --> elimina espacios en blanco al inicio y al final del nombre de la estación
    pollutant = request.GET.get("pollutant")
    
    #2. Validaciones
    if not station_name:
        return JsonResponse({"error": "Missing 'station' parameter"}, status=400)
    
    if not pollutant:
        return JsonResponse({"error": "Missing 'pollutant' parameter"}, status=400)
    
    if pollutant not in ALLOWED_POLLUTANTS:
        return JsonResponse({"error": f"Invalid 'pollutant' parameter. Allowed values are: {ALLOWED_POLLUTANTS}"}, status=400)
    
    if not Station.objects.filter(name=station_name).exists():
        return JsonResponse({"error": "Station not found"}, status=404)
    
    #3. Filtrar mediciones
    measurements = Measurement.objects.filter(station__name=station_name).order_by('measured_at')
    
    #construccion de datos para la respuesta JSON
    data = []
    
    for measurement in measurements [:500]:#limita a las primeras 500 mediciones para evitar sobrecargar la respuesta
        value= getattr(measurement, pollutant) #getattr --> obtiene el valor del atributo especificado por el nombre del contaminante
        #saltar los valores nulos o no disponibles
        if value is None:
            continue
        
        data.append({
            "time": measurement.measured_at.isoformat() if measurement.measured_at else None,
            "value": value,
        })
        
    #5. Devolver la respuesta JSON

    return JsonResponse({
        "station": station_name,
        "pollutant": pollutant,
        "count": len(data),
        "data": data
    }) #devuelve una lista JSON
