from django.contrib import admin
from .models import Ride

@admin.register(Ride)
class RideAdmin(admin.ModelAdmin):
    list_display = ('id', 'rider', 'vehicle', 'status', 'scheduled_start', 'created_at')
    list_filter = ('status', 'scheduled_start', 'created_at')
    search_fields = ('rider__user__username', 'vehicle__vehicle_plate_no')
    filter_horizontal = ('bookings',)
    readonly_fields = ('created_at', 'updated_at')
