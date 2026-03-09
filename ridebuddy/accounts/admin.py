from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Community, Vehicle, Student, Rider, UserLocation, OTP

class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'phone_no', 'is_student', 'is_rider', 'is_verified', 'is_active')
    fieldsets = UserAdmin.fieldsets + (
        ('Additional Info', {'fields': ('phone_no', 'emergency_contact', 'profile_picture', 'is_verified', 'is_student', 'is_rider')}),
    )

@admin.register(Community)
class CommunityAdmin(admin.ModelAdmin):
    list_display = ('name', 'short_name')
    search_fields = ('name', 'short_name')

@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ('vehicle_model', 'vehicle_plate_no', 'vehicle_type', 'capacity')
    list_filter = ('vehicle_type',)
    search_fields = ('vehicle_model', 'vehicle_plate_no')

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('user', 'id_no', 'community', 'has_vehicle')
    list_filter = ('community', 'has_vehicle')
    search_fields = ('id_no', 'user__username', 'user__first_name')

@admin.register(Rider)
class RiderAdmin(admin.ModelAdmin):
    list_display = ('user', 'license_no', 'employer_student')
    search_fields = ('license_no', 'user__username')

@admin.register(UserLocation)
class UserLocationAdmin(admin.ModelAdmin):
    list_display = ('user', 'latitude', 'longitude', 'updated_at')
    list_filter = ('updated_at',)

@admin.register(OTP)
class OTPAdmin(admin.ModelAdmin):
    list_display = ('user', 'code', 'created_at', 'is_used')
    list_filter = ('is_used', 'created_at')
    search_fields = ('user__username', 'code')

admin.site.register(User, CustomUserAdmin)
