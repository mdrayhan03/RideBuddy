from datetime import timedelta
from decimal import Decimal
from django.utils import timezone
from rides.models import Ride, OwnerCommission

class OwnerCommissionService:
    @classmethod
    def create_commission(cls, owner):
        # Determine the date for yesterday
        to_date = timezone.now().date() - timedelta(days=1)
        
        # Get the latest commission for to find the start date
        last_commission = OwnerCommission.objects.filter(owner=owner).order_by('-to_date').first()
        
        if last_commission:
            # If there's a previous commission, start from the day after its to_date
            from_date = last_commission.to_date + timedelta(days=1)
        else:
            # If no commissions exist, start from their very first completed ride
            first_ride = Ride.objects.filter(
                vehicle__student_owner=owner, 
                status='completed',
                dropped_time__isnull=False
            ).order_by('dropped_time').first()
            
            if first_ride:
                from_date = first_ride.dropped_time.date()
            else:
                # No complete rides at all
                return None
                
        # If commissions are already up-to-date, we don't need to do anything
        if from_date > to_date:
            return None
            
        # Fetch all completed rides between from_date and to_date
        completed_rides = Ride.objects.filter(
            vehicle__student_owner=owner,
            status='completed',
            dropped_time__date__gte=from_date,
            dropped_time__date__lte=to_date
        )
        
        # If there are no rides in this time frame, no commission object needed
        if not completed_rides.exists():
            return None
            
        total_fare = Decimal('0.00')
        commission_amount = Decimal('0.00')
        
        # Calculate totals
        for ride in completed_rides:
            total_fare += ride.total_fare
            # Assuming commission_rate is stored as a percentage, e.g., 10.00
            ride_commission = (ride.total_fare * ride.commission_rate) / Decimal('100.00')
            commission_amount += ride_commission
            
        # Create the new OwnerCommission
        commission = OwnerCommission.objects.create(
            owner=owner,
            from_date=from_date,
            to_date=to_date,
            total_ride_fare=total_fare,
            commission_amount=commission_amount
        )
        
        # Assign the rides to the ManyToMany field
        commission.rides.set(completed_rides)
        
        return commission

    @classmethod
    def process_payment(cls, commission, payment_method, payment_id):
        """
        Process payment for a commission.
        """
        if commission.payment_status == 'paid':
            return False, "Commission already paid."
            
        commission.payment_method = payment_method
        commission.payment_id = payment_id
        commission.payment_status = 'paid'
        commission.payment_date = timezone.now().date()
        # commission.is_verified = True
        # commission.verified_at = timezone.now()
        commission.save()
        
        return True, "Payment processed successfully."