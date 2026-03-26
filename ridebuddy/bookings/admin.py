from django.contrib import admin
from django.urls import path
from django.template.response import TemplateResponse
from .models import Booking, Discount

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('id', 'student', 'start_location', 'end_location', 'fare', 'status', 'booking_type', 'scheduled_start', 'created_at')
    list_filter = ('booking_type', 'status', 'created_at')
    search_fields = ('student__user__username', 'start_location', 'end_location')
    readonly_fields = ('created_at', 'updated_at')

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                '<path:object_id>/admin-booking-view/',
                self.admin_site.admin_view(self.admin_booking_view),
                name='admin_booking_view',
            ),
        ]
        return custom_urls + urls

    def admin_booking_view(self, request, object_id):
        # Ensure the user has at least view permission for this model
        if not self.has_view_or_change_permission(request):
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied
            
        booking = self.get_object(request, object_id)
        is_security_officer = request.user.groups.filter(name__iexact='security officer').exists()
        
        context = dict(
            self.admin_site.each_context(request),
            title="Booking Map",
            booking=booking,
            object_id=object_id,
            is_security_officer=is_security_officer,
        )
        return TemplateResponse(request, "admin/bookings/booking/admin_booking.html", context)

@admin.register(Discount)
class DiscountAdmin(admin.ModelAdmin):
    list_display = ('code', 'percentage', 'created_at')
    search_fields = ('code',)
