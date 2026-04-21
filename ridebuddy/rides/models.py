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

    total_fare = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    commission_rate = models.DecimalField(max_digits=5, decimal_places=2, default=10.00)

    def update_total_fare(self):
        from django.db.models import Sum
        total = self.bookings.aggregate(total=Sum('fare'))['total']
        self.total_fare = total or 0.00
        self.save(update_fields=['total_fare'])

    def __str__(self):
        rider_name = self.rider.user.username if self.rider else "No Rider"
        return f"Ride {self.id} by {rider_name}"

class OwnerCommission(models.Model):
    STATUS_CHOICES = [
        ('due', 'Due'),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
    ]

    BKASH = 'bkash'
    NAGAD = 'nagad'
    ROCKET = 'rocket'
    BANK = 'bank'

    PAYMENT_METHOD_CHOICES = [
        (BKASH, 'Bkash'),
        (NAGAD, 'Nagad'),
        (ROCKET, 'Rocket'),
        (BANK, 'Bank Transfer'),
    ]

    PAYMENT_INSTRUCTION_DICT = {
        BKASH: {
            "title": "Pay via bKash Personal",
            "number": "017XXXXXXXX",
            "steps": "Go to 'Send Money' and enter the amount. Include your Username in the reference.",
        },
        NAGAD: {
            "title": "Pay via Nagad",
            "number": "018XXXXXXXX",
            "steps": "Use 'Send Money' option. No extra charge required.",
        },
        ROCKET: {
            "title": "Pay via Rocket",
            "number": "019XXXXXXXX-X",
            "steps": "Use the 'Bill Pay' or 'Send Money' option.",
        },
        BANK: {
            "title": "Bank Transfer Details",
            "account_name": "App Admin Name",
            "account_no": "123456789",
            "bank_name": "City Bank",
            "branch": "Dhaka",
        },
    }

    owner = models.ForeignKey(Student , on_delete=models.CASCADE, related_name='owner_commissions')
    rides = models.ManyToManyField(Ride, related_name='owner_commissions')

    from_date = models.DateField()
    to_date = models.DateField()

    total_ride_fare = models.DecimalField(null=True, blank=True, max_digits=10, decimal_places=2)
    commission_amount = models.DecimalField(null=True, blank=True, max_digits=10, decimal_places=2)

    payment_method = models.CharField(max_length=20, null=True, blank=True, choices=PAYMENT_METHOD_CHOICES)
    payment_status = models.CharField(max_length=20, null=True, blank=True, choices=STATUS_CHOICES, default='due')
    payment_id = models.CharField(max_length=100, null=True, blank=True)

    invoice_date = models.DateTimeField(auto_now_add=True)
    payment_date = models.DateField(null=True, blank=True)

    is_verified = models.BooleanField(default=False)
    verified_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Payment {self.id} by {self.rider.user.username}"

    @property
    def get_instructions(self):
        """Helper to get instructions for the selected payment method."""
        return self.PAYMENT_INSTRUCTION_DICT.get(self.payment_method, {})
