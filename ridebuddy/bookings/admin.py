from django.contrib import admin
from .models import Booking, Discount

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('id', 'student', 'start_location', 'end_location', 'fare', 'status', 'booking_type', 'scheduled_start', 'created_at')
    list_filter = ('booking_type', 'status', 'created_at')
    search_fields = ('student__user__username', 'start_location', 'end_location')
    readonly_fields = ('created_at', 'updated_at')

@admin.register(Discount)
class DiscountAdmin(admin.ModelAdmin):
    list_display = ('code', 'percentage', 'created_at')
    search_fields = ('code',)
