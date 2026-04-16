from django.contrib import admin
from .models import Station, Measurement


@admin.register(Station)
class StationAdmin(admin.ModelAdmin):
    list_display = ("name", "location")
    search_fields = ("name",)


@admin.register(Measurement)
class MeasurementAdmin(admin.ModelAdmin):
    list_display = ("station", "measured_at", "no2", "pm10", "pm2_5", "o3")
    list_filter = ("station", "measured_at")
    search_fields = ("station__name",)
    date_hierarchy = "measured_at"
