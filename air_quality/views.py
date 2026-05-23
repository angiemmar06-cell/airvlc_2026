from django.db.models import Avg, Count, Max, Min
from django.db.models.functions import Trunc
from django.http import JsonResponse
from django.utils.dateparse import parse_date

from .models import Measurement, Station


# Lista blanca: solo estos campos pueden consultarse desde la API.
ALLOWED_POLLUTANTS = [
    'no2', 'pm10', 'pm2_5', 'o3', 'so2', 'co',
    'no', 'nox', 'nh3', 'c7h8', 'c6h6', 'c8h10',
    'as_ng_m3', 'ni_ng_m3', 'cd_ng_m3', 'pb_ng_m3', 'b_a_p_ng_m3',
    'wind_speed', 'wind_direction', 'max_wind_speed',
    'temperature', 'relative_humidity', 'pressure',
    'solar_radiation', 'precipitation', 'noise',
]

# Unidades de cada variable, devueltas en la respuesta para que el frontend las muestre.
POLLUTANT_UNITS = {
    'no2': 'µg/m³', 'pm10': 'µg/m³', 'pm2_5': 'µg/m³', 'o3': 'µg/m³',
    'so2': 'µg/m³', 'co': 'mg/m³',
    'no': 'µg/m³', 'nox': 'µg/m³', 'nh3': 'µg/m³',
    'c7h8': 'µg/m³', 'c6h6': 'µg/m³', 'c8h10': 'µg/m³',
    'as_ng_m3': 'ng/m³', 'ni_ng_m3': 'ng/m³', 'cd_ng_m3': 'ng/m³',
    'pb_ng_m3': 'ng/m³', 'b_a_p_ng_m3': 'ng/m³',
    'wind_speed': 'm/s', 'wind_direction': '°', 'max_wind_speed': 'm/s',
    'temperature': '°C', 'relative_humidity': '%', 'pressure': 'hPa',
    'solar_radiation': 'W/m²', 'precipitation': 'mm', 'noise': 'dB',
}

VALID_AGGREGATES = {'hourly', 'daily', 'monthly'}
DEFAULT_LIMIT = 5000
MAX_LIMIT = 5000


def stations_geojson(request):
    stations = Station.objects.filter(measurements__isnull=False).distinct().order_by('name')
    data = [
        {
            "name": station.name,
            "lat": station.location.y,
            "lng": station.location.x,
        }
        for station in stations
    ]
    return JsonResponse(data, safe=False)


def measurements_geojson(request):
    # 1. Parámetros
    station_name = request.GET.get("station", "").strip()
    pollutant = request.GET.get("pollutant", "").strip().lower()
    aggregate = request.GET.get("aggregate", "hourly").strip().lower()
    start_date_str = request.GET.get("start_date")
    end_date_str = request.GET.get("end_date")
    limit_str = request.GET.get("limit")

    # 2. Validaciones obligatorias
    if not station_name:
        return JsonResponse({"error": "Missing 'station' parameter"}, status=400)

    if not pollutant:
        return JsonResponse({"error": "Missing 'pollutant' parameter"}, status=400)

    if pollutant not in ALLOWED_POLLUTANTS:
        return JsonResponse(
            {"error": f"Invalid 'pollutant'. Allowed: {ALLOWED_POLLUTANTS}"},
            status=400,
        )

    if aggregate not in VALID_AGGREGATES:
        return JsonResponse(
            {"error": f"Invalid 'aggregate'. Allowed: {sorted(VALID_AGGREGATES)}"},
            status=400,
        )

    if not Station.objects.filter(name=station_name).exists():
        return JsonResponse({"error": "Station not found"}, status=404)

    # 3. Fechas opcionales (YYYY-MM-DD).
    # parse_date devuelve None para formato inválido (p. ej. "abc") pero lanza ValueError
    # cuando el formato es correcto y el valor no existe (mes 13, día 32). Capturamos ambos.
    try:
        start_date = parse_date(start_date_str) if start_date_str else None
    except ValueError:
        start_date = None

    try:
        end_date = parse_date(end_date_str) if end_date_str else None
    except ValueError:
        end_date = None

    if start_date_str and not start_date:
        return JsonResponse({"error": "Invalid 'start_date'. Use YYYY-MM-DD with a valid date"}, status=400)

    if end_date_str and not end_date:
        return JsonResponse({"error": "Invalid 'end_date'. Use YYYY-MM-DD with a valid date"}, status=400)

    if start_date and end_date and start_date > end_date:
        return JsonResponse({"error": "'start_date' must be <= 'end_date'"}, status=400)

    # 4. Límite configurable con tope duro
    if limit_str:
        try:
            limit = int(limit_str)
            if limit < 1:
                raise ValueError
        except ValueError:
            return JsonResponse({"error": "Invalid 'limit'. Must be a positive integer"}, status=400)
        limit = min(limit, MAX_LIMIT)
    else:
        limit = DEFAULT_LIMIT

    # 5. Query base. Excluimos nulos del contaminante: así no inflan los stats ni la cuenta.
    qs = Measurement.objects.filter(
        station__name=station_name,
        **{f"{pollutant}__isnull": False},
    )
    if start_date:
        qs = qs.filter(measured_at__date__gte=start_date)
    if end_date:
        qs = qs.filter(measured_at__date__lte=end_date)

    # 6. Stats sobre el conjunto crudo filtrado (antes de agregar), reflejan la distribución real.
    stats = qs.aggregate(
        mean=Avg(pollutant),
        min=Min(pollutant),
        max=Max(pollutant),
        count=Count(pollutant),
    )

    # 7. Serie temporal según el modo de agregación
    if aggregate == "hourly":
        rows = qs.order_by("measured_at").values_list("measured_at", pollutant)[:limit]
        data = [{"time": t.isoformat(), "value": v} for t, v in rows]
    else:
        trunc_kind = "day" if aggregate == "daily" else "month"
        aggregated = (
            qs.annotate(period=Trunc("measured_at", trunc_kind))
            .values("period")
            .annotate(value=Avg(pollutant))
            .order_by("period")[:limit]
        )
        data = [
            {
                "time": (
                    row["period"].date().isoformat()
                    if trunc_kind == "day"
                    else row["period"].strftime("%Y-%m")
                ),
                "value": row["value"],
            }
            for row in aggregated
        ]

    return JsonResponse({
        "station": station_name,
        "pollutant": pollutant,
        "unit": POLLUTANT_UNITS.get(pollutant),
        "aggregate": aggregate,
        "start_date": start_date.isoformat() if start_date else None,
        "end_date": end_date.isoformat() if end_date else None,
        "limit": limit,
        "stats": stats,
        "count": len(data),
        "data": data,
    })
