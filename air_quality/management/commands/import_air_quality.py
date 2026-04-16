import requests
from datetime import datetime

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from air_quality.models import Station, Measurement


API_URL = "https://opendata.vlci.valencia.es/api/3/action/datastore_search"
RESOURCE_ID = "93438700-3338-4dbf-a8ff-1c6dca337cd9"


class Command(BaseCommand):
    help = "Import air quality data in batches from València CKAN API"

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, default=100, help="Records per batch")
        parser.add_argument("--offset", type=int, default=0, help="Initial offset")
        parser.add_argument("--max-batches", type=int, default=1, help="Number of batches to fetch")

    def handle(self, *args, **options):
        limit = options["limit"]
        offset = options["offset"]
        max_batches = options["max_batches"]

        total_imported = 0
        total_skipped = 0

        for batch in range(max_batches):
            current_offset = offset + batch * limit

            self.stdout.write(
                self.style.NOTICE(f"Batch {batch+1}/{max_batches} | offset={current_offset}")
            )

            params = {
                "resource_id": RESOURCE_ID,
                "limit": limit,
                "offset": current_offset,
            }

            response = requests.get(
                API_URL,
                params=params,
                timeout=30,
                headers={"Accept": "application/json"},
            )
            response.raise_for_status()

            data = response.json()

            if not data.get("success"):
                self.stdout.write(self.style.ERROR("API returned success=False"))
                break

            records = data.get("result", {}).get("records", [])

            if not records:
                self.stdout.write(self.style.WARNING("No more records found. Stopping."))
                break

            imported_count = 0
            skipped_count = 0

            with transaction.atomic():
                for record in records:
                    station_name = record.get("Estacion")
                    fecha_str = record.get("Fecha")
                    hora_str = record.get("Hora")

                    if not station_name or not fecha_str:
                        skipped_count += 1
                        continue

                    try:
                        station = Station.objects.get(name=station_name)
                    except Station.DoesNotExist:
                        skipped_count += 1
                        continue

                    measured_at = self.combine_datetime(fecha_str, hora_str)
                    if not measured_at:
                        skipped_count += 1
                        continue

                    Measurement.objects.update_or_create(
                        station=station,
                        measured_at=measured_at,
                        defaults={
                            "no2": self.to_float(record.get("NO2")),
                            "pm10": self.to_float(record.get("PM10")),
                            "pm2_5": self.to_float(record.get("PM2.5")),
                            "o3": self.to_float(record.get("O3")),
                            "so2": self.to_float(record.get("SO2")),
                            "co": self.to_float(record.get("CO")),
                            "no": self.to_float(record.get("NO")),
                            "nox": self.to_float(record.get("NOx")),
                            "nh3": self.to_float(record.get("NH3")),
                            "c7h8": self.to_float(record.get("C7H8")),
                            "c6h6": self.to_float(record.get("C6H6")),
                            "c8h10": self.to_float(record.get("C8H10")),
                            "wind_speed": self.to_float(record.get("Velocidad del viento")),
                            "wind_direction": self.to_float(record.get("Direccion del viento")),
                            "max_wind_speed": self.to_float(record.get("Velocidad maxima del viento")),
                            "temperature": self.to_float(record.get("Temperatura")),
                            "relative_humidity": self.to_float(record.get("Humedad relativa")),
                            "pressure": self.to_float(record.get("Presion")),
                            "solar_radiation": self.to_float(record.get("Radiacion")),
                            "precipitation": self.to_float(record.get("Precipitacion")),
                            "noise": self.to_float(record.get("Ruido")),
                        }
                    )

                    imported_count += 1

            total_imported += imported_count
            total_skipped += skipped_count

            self.stdout.write(
                self.style.SUCCESS(
                    f"Batch done → imported: {imported_count}, skipped: {skipped_count}"
                )
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"\nTOTAL → imported: {total_imported}, skipped: {total_skipped}"
            )
        )

    def to_float(self, value):
        if value in (None, "", "null"):
            return None
        try:
            return float(value)
        except:
            return None

    def combine_datetime(self, fecha_value, hora_value):
        if not fecha_value:
            return None

        try:
            date_part = fecha_value.split("T")[0]
            time_part = hora_value if hora_value else "00:00:00"

            dt = datetime.strptime(f"{date_part} {time_part}", "%Y-%m-%d %H:%M:%S")

            if timezone.is_naive(dt):
                dt = timezone.make_aware(dt, timezone.get_current_timezone())

            return dt

        except:
            return None
