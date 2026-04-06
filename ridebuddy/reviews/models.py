from django.db import models
from rides.models import Ride
from bookings.models import Booking
from accounts.models import Student, Rider, Vehicle, User

# Create your models here.

REVIEW_STATUS_CHOICES = [
    ('pending', 'Pending'),
    ('done', 'Done'),
    ('cancel', 'Cancel'),
]

# Rider Review (Student reviewing the Rider)
class RiderReview(models.Model):
    reviewer = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='given_rider_reviews', null=True, blank=True)
    rider = models.ForeignKey(Rider, on_delete=models.CASCADE, related_name='rider_reviews')
    ride = models.ForeignKey(Ride, on_delete=models.CASCADE, related_name='rider_reviews')
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)], null=True, blank=True)
    review = models.TextField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=REVIEW_STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        reviewer_name = self.reviewer.student.user.username if self.reviewer else "Anonymous"
        return f"Rider Review {self.id} by {reviewer_name} for {self.rider.user.username} - {self.rating}*"

# Passenger Review (One booking context reviewing another, e.g., Rider/Manager context for a passenger)
class PassengerReview(models.Model):
    reviewer = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='given_passenger_reviews', null=True, blank=True)
    whom_reviewed = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='passenger_reviews', null=True, blank=True)
    ride = models.ForeignKey(Ride, on_delete=models.CASCADE, related_name='passenger_reviews')
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)], null=True, blank=True)
    review = models.TextField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=REVIEW_STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        reviewer_name = self.reviewer.student.user.username if self.reviewer else "Anonymous"
        reviewed_name = self.whom_reviewed.student.user.username if self.whom_reviewed else "Unknown"
        return f"Passenger Review {self.id} by {reviewer_name} for {reviewed_name} - {self.rating}*"

# Vehicle Review (Student reviewing the Vehicle)
class VehicleReview(models.Model):
    reviewer = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='given_vehicle_reviews', null=True, blank=True)
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='vehicle_reviews')
    ride = models.ForeignKey(Ride, on_delete=models.CASCADE, related_name='vehicle_reviews')
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)], null=True, blank=True)
    review = models.TextField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=REVIEW_STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        reviewer_name = self.reviewer.student.user.username if self.reviewer else "Anonymous"
        return f"Vehicle Review {self.id} by {reviewer_name} for {self.vehicle.vehicle_plate_no} - {self.rating}*"

# Platform Review (User reviewing the RideBuddy platform)
class PlatformReview(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='platform_reviews')
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)], null=True, blank=True)
    review = models.TextField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=REVIEW_STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Platform Review {self.id} by {self.user.username} - {self.rating}*"

# Student Review (Rider reviewing the Student/Passenger)
class StudentReview(models.Model):
    reviewer = models.ForeignKey(Rider, on_delete=models.CASCADE, related_name='given_student_reviews')
    student_booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='received_rider_reviews')
    ride = models.ForeignKey(Ride, on_delete=models.CASCADE, related_name='student_reviews')
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)], null=True, blank=True)
    review = models.TextField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=REVIEW_STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Student Review {self.id} by {self.reviewer.user.username} for {self.student_booking.student.user.username} - {self.rating}*"
