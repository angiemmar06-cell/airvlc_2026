from django.contrib.gis.db import models


class Station(models.Model):
    name = models.CharField(max_length=100, unique=True)
    location = models.PointField(srid=4326)

    class Meta:
        verbose_name = "Station"
        verbose_name_plural = "Stations"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Measurement(models.Model):
    station = models.ForeignKey(
        Station,
        on_delete=models.CASCADE,
        related_name="measurements"
    )
    date = models.DateField()

    # Main pollutants
    no2 = models.FloatField(null=True, blank=True)
    pm10 = models.FloatField(null=True, blank=True)
    pm2_5 = models.FloatField(null=True, blank=True)
    o3 = models.FloatField(null=True, blank=True)
    so2 = models.FloatField(null=True, blank=True)
    co = models.FloatField(null=True, blank=True)

    # Additional pollutants
    no = models.FloatField(null=True, blank=True)
    nox = models.FloatField(null=True, blank=True)
    nh3 = models.FloatField(null=True, blank=True)
    c7h8 = models.FloatField(null=True, blank=True)
    c6h6 = models.FloatField(null=True, blank=True)
    c8h10 = models.FloatField(null=True, blank=True)

    as_ng_m3 = models.FloatField(null=True, blank=True)
    ni_ng_m3 = models.FloatField(null=True, blank=True)
    cd_ng_m3 = models.FloatField(null=True, blank=True)
    pb_ng_m3 = models.FloatField(null=True, blank=True)
    b_a_p_ng_m3 = models.FloatField(null=True, blank=True)

    # Weather and related variables
    wind_speed = models.FloatField(null=True, blank=True)
    wind_direction = models.FloatField(null=True, blank=True)
    max_wind_speed = models.FloatField(null=True, blank=True)

    temperature = models.FloatField(null=True, blank=True)
    relative_humidity = models.FloatField(null=True, blank=True)
    pressure = models.FloatField(null=True, blank=True)
    solar_radiation = models.FloatField(null=True, blank=True)
    precipitation = models.FloatField(null=True, blank=True)
    noise = models.FloatField(null=True, blank=True)

    # Dataset metadata
    source_created_date = models.DateField(null=True, blank=True)
    source_removed_date = models.DateField(null=True, blank=True)

    class Meta:
        verbose_name = "Measurement"
        verbose_name_plural = "Measurements"
        ordering = ["-date", "station__name"]
        constraints = [
            models.UniqueConstraint(
                fields=["station", "date"],
                name="unique_station_date_measurement"
            )
        ]

    def __str__(self):
        return f"{self.station.name} - {self.date}"
