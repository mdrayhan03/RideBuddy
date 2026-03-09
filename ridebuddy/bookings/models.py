from django.db import models
from accounts.models import Student

# Create your models here.

# Booking
class Booking(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='bookings')
    start_location = models.CharField(max_length=255)
    end_location = models.CharField(max_length=255)
    start_latlon = models.JSONField(null=True, blank=True)
    end_latlon = models.JSONField(null=True, blank=True)
    waypoints = models.JSONField(null=True, blank=True)
    preference = models.JSONField(null=True, blank=True)
    fare = models.DecimalField(max_digits=10, decimal_places=2)
    distance = models.FloatField(null=True, blank=True)
    RIDE_TYPE_CHOICES = [
        ('car', 'Car'),
        ('bike', 'Bike'),
    ]
    ride_type = models.CharField(max_length=20, choices=RIDE_TYPE_CHOICES, default='car')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Scheduling fields
    TYPE_CHOICES = [
        ('instant', 'Instant'),
        ('schedule', 'Schedule'),
    ]
    booking_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='instant')
    scheduled_start = models.DateTimeField(null=True, blank=True)
    waiting_threshold = models.PositiveIntegerField(default=15) # Minutes
    
    pickup = models.JSONField(null=True, blank=True)
    dropoff = models.JSONField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Booking {self.id} for {self.student.user.username}"

# Discount
class Discount(models.Model):
    code = models.CharField(max_length=50, unique=True)
    description = models.TextField()
    percentage = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.code} ({self.percentage}%)"