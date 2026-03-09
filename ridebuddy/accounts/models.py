import os
from django.db import models
from django.contrib.auth.models import AbstractUser

def user_profile_pic_path(instance, filename):
    ext = filename.split('.')[-1]
    return f"profile_pics/{instance.username}_profile.{ext}"

def student_id_pic_path(instance, filename):
    ext = filename.split('.')[-1]
    return f"student_ids/{instance.user.username}_id_card.{ext}"

def rider_license_pic_path(instance, filename):
    ext = filename.split('.')[-1]
    return f"licenses/{instance.user.username}_license.{ext}"

def tax_token_pic_path(instance, filename):
    ext = filename.split('.')[-1]
    return f"tax_tokens/{instance.vehicle_plate_no}_tax_token.{ext}"

# User(abstractuser)
class User(AbstractUser):
    phone_no = models.CharField(max_length=15, blank=True, null=True)
    emergency_contact = models.CharField(max_length=15, blank=True, null=True)
    profile_picture = models.ImageField(upload_to=user_profile_pic_path, blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    is_student = models.BooleanField(default=False)
    is_rider = models.BooleanField(default=False)

    def __str__(self):
        return self.username

# Community
class Community(models.Model):
    name = models.CharField(max_length=100)
    short_name = models.CharField(max_length=10)

    def __str__(self):
        return self.name

# Vehicle
class Vehicle(models.Model):
    VEHICLE_TYPES = [
        ('car', 'Car'),
        ('bike', 'Bike'),
    ]
    vehicle_type = models.CharField(max_length=20, choices=VEHICLE_TYPES)
    vehicle_model = models.CharField(max_length=100)
    vehicle_plate_no = models.CharField(max_length=20, unique=True)
    capacity = models.PositiveIntegerField()
    tax_token_picture = models.ImageField(upload_to=tax_token_pic_path, blank=True, null=True)
    ac_available = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.vehicle_model} ({self.vehicle_plate_no})"

# Student
class Student(models.Model):
    DRIVER_TYPES = [
        ('self_drive', 'Self Drive'),
        ('has_driver', 'Has Driver'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_profile')
    id_no = models.CharField(max_length=50)
    community = models.ForeignKey(Community, on_delete=models.SET_NULL, null=True, related_name='students')
    alternative_email = models.EmailField(blank=True, null=True)
    id_picture = models.ImageField(upload_to=student_id_pic_path, blank=True, null=True)
    has_vehicle = models.BooleanField(default=False)
    vehicle = models.OneToOneField(Vehicle, on_delete=models.SET_NULL, null=True, blank=True, related_name='student_owner')
    driver_type = models.CharField(max_length=20, choices=DRIVER_TYPES, blank=True, null=True)
    
    def __str__(self):
        return f"Student: {self.user.username}"

# Rider
class Rider(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='rider_profile')
    employer_student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='hired_riders')
    license_no = models.CharField(max_length=50, unique=True)
    license_picture = models.ImageField(upload_to=rider_license_pic_path, blank=True, null=True)
    vehicle = models.OneToOneField(Vehicle, on_delete=models.SET_NULL, null=True, blank=True, related_name='rider_driver')

    def __str__(self):
        return f"Rider: {self.user.username}"

# UserLocation
class UserLocation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='locations')
    latitude = models.FloatField()
    longitude = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Location: {self.user.username} ({self.latitude}, {self.longitude})"

class OTP(models.Model):
    OTP_TYPES = [
        ('login', 'Login'),
        ('signup', 'Signup'),
        ('forgot_password', 'Forgot Password'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='otps')
    code = models.CharField(max_length=6)
    otp_type = models.CharField(max_length=20, choices=OTP_TYPES, default='signup')
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)

    def __str__(self):
        return f"OTP for {self.user.username}: {self.code}"