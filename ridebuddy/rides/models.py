from django.db import models
from accounts.models import Rider, Vehicle, Student
from bookings.models import Booking

# Create your models here.

# Ride
class Ride(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('started', 'Started'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]    
    rider = models.ForeignKey(Rider, on_delete=models.CASCADE, related_name='rides', blank=True, null=True)
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='rides', blank=True, null=True)
    bookings = models.ManyToManyField(Booking, related_name='rides')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    
    # Scheduling fields
    scheduled_start = models.DateTimeField(null=True, blank=True)
    waiting_threshold = models.PositiveIntegerField(default=15)
    
    created_by = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='created_rides', blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    start_time = models.DateTimeField(null=True, blank=True)
    dropped_time = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        rider_name = self.rider.user.username if self.rider else "No Rider"
        return f"Ride {self.id} by {rider_name}"
