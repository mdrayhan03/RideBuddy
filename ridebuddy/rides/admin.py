from django.contrib import admin
from django.urls import path
from django.template.response import TemplateResponse
from .models import Ride

@admin.register(Ride)
class RideAdmin(admin.ModelAdmin):
    list_display = ('id', 'rider', 'vehicle', 'status', 'scheduled_start', 'created_at')
    list_filter = ('status', 'scheduled_start', 'created_at')
    search_fields = ('rider__user__username', 'vehicle__vehicle_plate_no')
    filter_horizontal = ('bookings',)
    readonly_fields = ('created_at', 'updated_at')

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                '<path:object_id>/admin-ride-view/',
                self.admin_site.admin_view(self.admin_ride_view),
                name='admin_ride_view',
            ),
        ]
        return custom_urls + urls

    def admin_ride_view(self, request, object_id):
        ride = self.get_object(request, object_id)
        context = dict(
            self.admin_site.each_context(request),
            title="Live Ride Map",
            ride=ride,
            object_id=object_id,
        )
        return TemplateResponse(request, "admin/rides/ride/admin_ride.html", context)
