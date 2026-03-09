from django.contrib import admin
from .models import RiderReview, PassengerReview, VehicleReview

@admin.register(RiderReview)
class RiderReviewAdmin(admin.ModelAdmin):
    list_display = ('id', 'reviewer', 'rider', 'ride', 'rating', 'status', 'created_at')
    list_filter = ('rating', 'status', 'created_at')
    search_fields = ('reviewer__student__user__username', 'rider__user__username')

@admin.register(PassengerReview)
class PassengerReviewAdmin(admin.ModelAdmin):
    list_display = ('id', 'reviewer', 'whom_reviewed', 'ride', 'rating', 'status', 'created_at')
    list_filter = ('rating', 'status', 'created_at')
    search_fields = ('reviewer__student__user__username', 'whom_reviewed__student__user__username')

@admin.register(VehicleReview)
class VehicleReviewAdmin(admin.ModelAdmin):
    list_display = ('id', 'reviewer', 'vehicle', 'ride', 'rating', 'status', 'created_at')
    list_filter = ('rating', 'status', 'created_at')
    search_fields = ('reviewer__student__user__username', 'vehicle__vehicle_plate_no')
